import os
import unittest
import codecs

from models import Parser


class ParserTestCase(unittest.TestCase):
    def setUp(self):
        self.parser = Parser()

    def tearDown(self):
        """Очищаем таблицы после прохождения каждого теста"""
        self.parser.table_tip.delete()
        self.parser.table_code.delete()
        self.parser.table_sector.delete()

    def set_html(self, filename):
        filepath = os.path.join(os.path.dirname(__file__), filename)
        with codecs.open(filepath, encoding='cp1251') as f:
            html = f.read()
            html_bytes = bytes(html, encoding='cp1251')
            self.parser.g.setup_document(html_bytes)

    def test_parse_level_multiple(self):
        """Несколько секторов"""
        self.set_html('pages/10/1.html')
        self.parser.parse()

        self.assertEqual(self.parser.table_sector.count(), 2)

        sector_1 = self.parser.table_sector.find_one()
        self.assertEqual(sector_1['name'], 'бонусные коды')
        code = self.parser.table_code.find_one(metka=1, sector_id=sector_1['id'])
        self.assertEqual(code['ko'], 'N')

    def test_parse_level_one(self):
        """Один сектор, многие коды взяты"""
        self.set_html('pages/18/1.html')
        self.parser.parse()

        self.assertEqual(self.parser.table_sector.count(), 1)
        self.assertEqual(self.parser.table_code.count(), 14)

        code_1 = self.parser.table_code.find_one(metka=1)
        self.assertEqual(code_1['ko'], '3')
        self.assertEqual(code_1['taken'], True)

        code_2 = self.parser.table_code.find_one(metka=2)
        self.assertEqual(code_2['ko'], '2')
        self.assertEqual(code_2['taken'], False)

    def test_parse_sector_take_code(self):
        """Взятие кода по восьмой и одиннадцатой метке."""
        self.set_html('pages/19/1.html')
        self.parser.parse()
        code = self.parser.table_code.find_one(metka=8)
        self.assertEqual(code['taken'], False)

        self.set_html('pages/19/3.html')
        result = self.parser.parse()
        self.assertEqual(result['new_level'], False)  # Нет нового уровня
        code_list = result['sector_list'][0]['code_list']  # Берем взятые коды из первого (единственного) сектора
        self.assertSetEqual({
            code_list[0]['metka'],
            code_list[1]['metka'],
        }, {8, 11})  # Восьмая и одиннадцатая метки взяты

        code = self.parser.table_code.find_one(metka=8)  # Удостоверяемся, что состояние в базе изменилось
        self.assertEqual(code['taken'], True)

    def test_parse_tip(self):
        self.set_html('pages/18/1.html')
        result = self.parser.parse()
        self.assertEqual(len(result['tip_list']), 0)
        self.assertEqual(self.parser.table_tip.count(), 0)  # Подсказок в базе не должно быть

        tip_text = 'Ответ на спойлер: пустырь'
        self.set_html('pages/18/2.html')
        result = self.parser.parse()
        self.assertEqual(result['tip_list'][0]['text'], tip_text)

        self.assertEqual(self.parser.table_tip.count(), 1)  # Должна появится первая подсказка
        tip = self.parser.table_tip.find_one()
        self.assertEqual(tip['text'], tip_text)
