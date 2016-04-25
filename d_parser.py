from urllib.parse import urlencode

import dataset
from grab.base import Grab
import re

start_url = 'http://classic.dzzzr.ru/moscow/'
drive_url = 'http://classic.dzzzr.ru/moscow/go/?{}'.format(urlencode({
    'nostat': 'on',
    'notext': '',
    'notags': '',
    'refresh': '30',
    'log': '',
    'legend': '',
    'bonus': 'on',
    'kladMap': '',
}))


class Parser(object):
    red_span_re = re.compile('<span style="color:red">([123]\+?|N)</span>')
    current_level = None
    current_game = None

    def __init__(self):
        self.g = Grab()
        self.db = dataset.connect('sqlite:///:memory:')
        # self.db = dataset.connect('sqlite:///mydatabase.db')  # Можно использовать файл базы

        self.table_code = self.db['code']
        self.table_sector = self.db['sector']
        self.table_tip = self.db['tip']

    def auth(self, login='', password=''):
        """Авторизация на сайте дозора"""
        self.g.go(start_url)
        self.g.doc.set_input('login', login)
        self.g.doc.set_input('password', password)
        self.g.doc.submit()

    def fetch(self):
        """Идет на сайт дозора, парсит страницу и обновляет текущее состояние"""
        self.g.go(drive_url)
        self.parse_level()
        self.parse_tip()

    def parse_level(self):
        """
        Парсит текст задания. Возвращает словарь с инфой об обновлении.
        Подробнее, что такое инфа обновления - в комментариях ниже
        """
        result = {
            'new_level': False,  # Новый уровень?
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
            result['new_level'] = True

        sector_list_str = sector_list_str.split('<strong>Коды сложности</strong><br> ')[1]
        sector_list_str = sector_list_str.split('<br></div>')[0]
        sector_list_str = sector_list_str.replace('null', 'N')
        for sector_index, sector_str in enumerate(sector_list_str.split('<br> ')):
            sector_name, sector_code_str = sector_str.split(': ')
            sector = {'code_list': []}
            for metka_index, item in enumerate(sector_code_str.split(', ')):
                taken = bool(self.red_span_re.match(item))
                ko = self.red_span_re.findall(item)[0] if taken else item

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
                    sector['code_list'].append(filters)

            result['sector_list'].append(sector)
            self.table_sector.upsert({
                'name': sector_name,
                'id': sector_index + 1,
            }, ['id'])
        return result

    def parse_tip(self):
        """
        Парсит текст подсказок. Возвращает объект обновления
        """
        result = {
            'new_tip': False,  # Есть ли новая подсказка?
        }
        self.table_tip.delete()

        div_list = self.g.doc.select('//div[@class="title"]')
        div = next((div for div in div_list if 'Подсказка l:' in div.html()), None)
        if div is None:
            return result
        tip_text = div.node().getnext().text_content()
        old_tip = self.table_tip.find_one(index=1)
        self.table_tip.upsert({
            'text': tip_text,
            'index': 1,  # номер подсказки
        }, ['index'])
        if old_tip is None:
            result.update({
                'text': tip_text,
                'index': 1,
            })
        return result
