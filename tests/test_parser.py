import os
import unittest
import codecs

from d_parser import Parser


class ParserTestCase(unittest.TestCase):
    def setUp(self):
        self.parser = Parser()

    def set_html(self, filename):
        filepath = os.path.join(os.path.dirname(__file__), filename)
        with codecs.open(filepath, encoding='cp1251') as f:
            html = f.read()
            html_bytes = bytes(html, encoding='cp1251')
            self.parser.g.setup_document(html_bytes)

    def test_get_sector_list(self):
        self.set_html('pages/1.html')

        sector_list = self.parser.get_sector_list()
        self.assertListEqual([{
            'name': 'основные коды',
            'code_list': [{
                'ko': '1',
                'taken': False
            }, {
                'ko': '1+',
                'taken': False
            }],
        }], sector_list)

    def test_get_tips_list(self):
        self.set_html('pages/stub/18tip1.html')

        tips_list = self.parser.get_tips_list()
        self.assertListEqual('Ответ на спойлер: пустырь', tips_list)
