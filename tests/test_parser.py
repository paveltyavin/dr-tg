import os
import unittest
import codecs

from d_parser import Parser


class ParserTestCase(unittest.TestCase):
    def setUp(self):
        self.parser = Parser()

    def set_html(self, filename):
        with codecs.open(os.path.abspath(filename), encoding='cp1251') as f:
            html = f.read()
            html_bytes = bytes(html, encoding='cp1251')
            self.parser.g.setup_document(html_bytes)

    def test_get_sector_list(self):
        self.set_html('./pages/6.htm')

        sector_list = self.parser.get_sector_list()
        self.assertListEqual([{
            'name': 'основные коды',
            'ko_list': ['1', '1+'],
        }], sector_list)
