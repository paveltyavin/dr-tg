import unittest
from views import sector_text, KoImg


class KoTextTestCase(unittest.TestCase):
    def test(self):
        sector_text({
            'name': 'Основные коды',
            'code_list': [
                {'metka': 1, 'ko': '1', 'taken': False},
                {'metka': 2, 'ko': '1+', 'taken': True},
                {'metka': 3, 'ko': '2', 'taken': False},
                {'metka': 4, 'ko': '3+', 'taken': False},
                {'metka': 5, 'ko': '2+', 'taken': True},
                {'metka': 6, 'ko': '1', 'taken': True},
                {'metka': 7, 'ko': '1', 'taken': True},
                {'metka': 8, 'ko': '1', 'taken': False},
                {'metka': 9, 'ko': '1+', 'taken': True},
                {'metka': 10, 'ko': '2', 'taken': False},
                {'metka': 11, 'ko': '3+', 'taken': False},
                {'metka': 12, 'ko': '2+', 'taken': True},
                {'metka': 13, 'ko': '1', 'taken': True},
                {'metka': 14, 'ko': '1', 'taken': True},
            ]
        })
