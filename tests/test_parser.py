import unittest
from codecs import open

from d_parser import Parser


class ParserTestCase(unittest.TestCase):
    def test_get_ko(self):
        parser = Parser()
        with open('./pages/6.htm', encoding='cp1251') as f:
            parser.html = f.read()
        ko_list = parser.get_ko_list()
        self.assertEqual([], ko_list)
