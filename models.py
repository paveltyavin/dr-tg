from urllib.parse import urlencode, urljoin

import dataset
from grab.base import Grab
import re
import settings

from decorators import throttle

host = 'http://classic.dzzzr.ru/moscow/'
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
})))

red_span_re = re.compile('<span style="color:red">([123]\+?|N)</span>')


class Parser(object):
    current_level = None

    def __init__(self):
        self.g = Grab()
        self.db = dataset.connect(settings.DATASET)

        self.table_code = self.db['code']
        self.table_sector = self.db['sector']
        self.table_tip = self.db['tip']
        self.table_cookies = self.db['cookies']

        for cookie_dict in self.db['cookies']:
            del cookie_dict['id']
            try:
                self.g.cookies.set(**cookie_dict)
            except ValueError:
                pass

    def fetch(self):
        """Загружает страницу движка"""
        self.g.go(drive_url)

    def auth(self, login='', password=''):
        """Авторизация на сайте дозора"""
        self.table_cookies.delete()

        self.g.go(start_url)
        self.g.doc.set_input('login', login)
        self.g.doc.set_input('password', password)
        self.g.doc.submit()
        cookie_list = self.g.cookies.get_dict()

        for cookie_dict in cookie_list:
            self.table_cookies.insert(cookie_dict)

    @throttle(seconds=2)
    def take_code(self, code):
        """Пробивка кода. Возвращает сообщение движка"""
        code = code.lower()
        code = code.replace('д', 'd')
        code = code.replace('р', 'r')

        self.g.go(drive_url)
        self.g.doc.set_input('cod', code)
        self.g.doc.submit()
        message = self.g.doc.select('//div[@class="sysmsg"]//b').text()
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
        div = self.g.doc.select('//div[@class="zad"][1]')[0]
        sector_list_str = div.html()
        level_number_str = div.node().getprevious().text
        level_number_str = level_number_str.replace('Задание', '')
        current_level = int(level_number_str.strip())
        if self.current_level != current_level:
            self.current_level = current_level
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
        self.table_tip.delete()

        div_list = self.g.doc.select('//div[@class="title"]')
        div = next((div for div in div_list if 'Подсказка l:' in div.html()), None)
        if div is None:
            return result
        tip_node = div.node().getnext()
        tip_text = tip_node.text_content()
        old_tip = self.table_tip.find_one(index=1)
        self.table_tip.upsert({
            'text': tip_text,
            'index': 1,  # номер подсказки
        }, ['index'])
        if old_tip is None:
            result['tip_list'].append({
                'text': tip_text,
                'index': 1,
            })
        return result


freq_dict = {x: "{:.3f}".format(433.075 + x * 0.025) for x in range(1, 70)}

HELP_TEXT = '''
/freq - частота рации. Для настройки канала напишите, например, "/freq 27"
/link - ссылка в движочек. Для настройки используйте команду "/link <ссылка>"
/auth - логин, под которым авторизован бот. "/auth <логин> <пароль>" - авторизация на сайте дозора. Используйте это команду в личке с ботом.
/type - актуальная настройку "ввода кодов". Можно отключить так: "/type off" или включить "/type on"
'''
