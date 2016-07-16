from datetime import datetime
import os
from urllib.parse import urlencode, urljoin

import dataset
from grab.base import Grab
import re
import settings

from decorators import throttle

host = 'http://classic.dzzzr.ru/'
start_url = urljoin(host, 'moscow/')
drive_url = urljoin(host, 'moscow/go/?{}'.format(urlencode({
    'nostat': 'on',
    'notext': '',
    'notags': '',
    'refresh': '30',
    'log': '',
    'legend': '',
    'bonus': 'on',
    'kladMap': '',
    'mes': '',
})))

red_span_re = re.compile('<span style="color:red">([123]\+?|N)</span>')


class Parser(object):
    def __init__(self):
        self.g = Grab()
        self.g.setup(timeout=100)
        self.db = dataset.connect(settings.DATASET)

        self.table_code = self.db['code']
        self.table_sector = self.db['sector']
        self.table_tip = self.db['tip']
        self.table_cookies = self.db['cookies']
        self.table_bot = self.db['bot']

        for cookie_dict in self.db['cookies']:
            del cookie_dict['id']
            try:
                self.g.cookies.set(**cookie_dict)
            except ValueError:
                pass

    def set_cookie(self, cookie):
        self.g.cookies.set(
            name='dozorSiteSession',
            value=cookie,
            domain='.dzzzr.ru',
            path='/',
        )

    def set_pin(self, userpwd):
        self.g.setup(userpwd=userpwd)

    def fetch(self):
        """Загружает страницу движка"""
        self.g.go(drive_url)
        n = datetime.utcnow()
        dir_1 = "./log/{}".format(n.strftime("%H"))
        dir_2 = "{}/{}".format(dir_1, n.strftime("%H_%M"))
        filepath = "{}/log_{}.html".format(dir_2, n.strftime("%H_%M_%S"))
        if not os.path.exists('./log'):
            os.makedirs('./log')
        if not os.path.exists(dir_1):
            os.makedirs(dir_1)
        if not os.path.exists(dir_2):
            os.makedirs(dir_2)
        with open(filepath, mode='w+') as f:
            html = self.g.doc.body.decode('cp1251')
            # f.write(html)

    @throttle(seconds=2)
    def take_code(self, code):
        """Пробивка кода. Возвращает сообщение движка"""
        code = code.lower()
        code = code.replace('д', 'd')
        code = code.replace('р', 'r')

        self.g.go(drive_url)
        if not self.g.doc.select('.//*[@name="cod"]').exists():
            return ""

        self.g.doc.set_input('cod', code)
        self.g.doc.submit()

        if not self.g.doc.select('//div[@class="sysmsg"]//b').exists():
            return ""
        message = self.g.doc.select('//div[@class="sysmsg"]//b').html()
        message = message.replace('<b>', '').replace('</b>', '')
        return message

    def parse(self):
        result = {}
        result.update(self._parse_level())
        result.update(self._parse_tip())
        return result

    def _parse_level(self):
        """
        Парсит страницу дозорного движка. Возвращает словарь с инфой об обновлении.
        Подробнее, что такое инфа обновления - в комментариях ниже
        """
        result = {
            'new_level': False,  # Новый уровень?
            'new_code': False,  # Новый пробитый код?
            'sector_list': [],  # Инфо о взятых кодах
        }
        try:
            div = self.g.doc.select('//div[@class="zad"][1]')[0]
        except IndexError:
            return result
        sector_list_str = div.html()
        level_number_str = div.node().getprevious().text
        level_number_str = level_number_str.replace('Задание', '')
        level = int(level_number_str.strip())

        bot_data = self.table_bot.find_one(**{'token': settings.TOKEN})

        if bot_data.get('level') != level:
            self.table_bot.upsert({
                'token': settings.TOKEN,
                'level': level,
            }, ['token'])

            self.table_sector.delete()
            self.table_code.delete()
            self.table_tip.delete()
            result['new_level'] = True

        sector_list_str = sector_list_str.split('<strong>Коды сложности</strong><br> ')[1]
        sector_list_str = sector_list_str.split('<br></div>')[0]
        sector_list_str = sector_list_str.replace('null', 'N')
        for sector_index, sector_str in enumerate(sector_list_str.split('<br> ')):
            sector_name, sector_code_str = sector_str.split(': ')
            sector = {
                'id': sector_index + 1,
                'name': sector_name,
                'code_list': [],
            }
            for metka_index, item in enumerate(sector_code_str.split(', ')):
                taken = bool(red_span_re.match(item))
                ko = red_span_re.findall(item)[0] if taken else item

                old_code = self.table_code.find_one(**{
                    'sector_id': sector_index + 1,
                    'metka': metka_index + 1,
                })
                filters = {
                    'ko': ko,
                    'taken': taken,
                    'metka': metka_index + 1,
                    'sector_id': sector_index + 1,
                }
                if old_code is None:
                    self.table_code.insert(filters)
                elif old_code['taken'] != taken:
                    self.table_code.update(filters, ['sector_id', 'metka'])
                    if 'бонусные коды' not in sector['name']:
                        result['new_code'] = True
                    sector['code_list'].append(filters)

            result['sector_list'].append(sector)
            self.table_sector.upsert({
                'id': sector_index + 1,
                'name': sector_name,
            }, ['id'])
        return result

    def _parse_tip(self):
        """
        Парсит текст подсказок. Возвращает объект обновления
        """
        result = {
            'tip_list': [],  # Новые подсказки.
        }

        div_list = self.g.doc.select('//div[@class="title"]')

        for div in div_list:
            for tip_title, tip_index in (
                ('Подсказка l:', 1),
                ('Подсказка 2:', 2),
            ):
                if tip_title in div.html():
                    tip_node = div.node().getnext()
                    tip_text = tip_node.text_content()
                    if 'не предусмотрена' in tip_text.lower():
                        continue
                    old_tip = self.table_tip.find_one(index=tip_index)
                    self.table_tip.upsert({
                        'text': tip_text,
                        'index': tip_index,  # номер подсказки
                    }, ['index'])
                    if old_tip is None:
                        result['tip_list'].append({
                            'text': tip_text,
                            'index': tip_index,
                        })
        return result


freq_dict = {x: "{:.3f}".format(433.075 + x * 0.025) for x in range(1, 70)}

HELP_TEXT = '''
/parse - парсить ли движок дозора. Можно отключить так: "/parse off" или включить "/parse on".
/cookie - устанавливает авторизационную куку dozorSiteSession. Использовать так: "/cookie KTerByfGopF5dSgFjkl07x8v"
/status - проверка статуса подключения к движку.
/pin - устанавливает пин для доступа в игру. Использовать так: "/pin moscow_capitan:123456"
/type - актуальная настройку "ввода кодов". Можно отключить так: "/type off" или включить "/type on".
'''

ADD_HELP_TEXT = """
/freq - частота рации. Для настройки канала напишите, например, "/freq 27"
/pattern - регулярное выражение для поиска кода. Чтобы установить стандартное выражение используйте команду "/pattern standard"
Коды ищутся по регулярному выражению, изменяемому через настройку /pattern
/link - ссылка в движочек. Для настройки используйте команду "/link <ссылка>"
"""
