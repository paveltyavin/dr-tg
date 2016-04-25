import unittest
from views import code_text, KoImg


class KoTextTestCase(unittest.TestCase):
    def test(self):
        result = code_text([
            {'ko': '1', 'taken': False},
            {'ko': '1+', 'taken': True},
            {'ko': '2', 'taken': False},
            {'ko': '3+', 'taken': False},
            {'ko': '2+', 'taken': True},
            {'ko': '1', 'taken': True},
            {'ko': '1', 'taken': True},
            {'ko': '1', 'taken': False},
            {'ko': '1+', 'taken': True},
            {'ko': '2', 'taken': False},
            {'ko': '3+', 'taken': False},
            {'ko': '2+', 'taken': True},
            {'ko': '1', 'taken': True},
            {'ko': '1', 'taken': True},
        ])
        # print(result)


class KoImgTestCase(unittest.TestCase):
    def test(self):
        KoImg(['1', '2', '3'])
