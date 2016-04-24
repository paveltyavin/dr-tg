from grab.base import Grab
import re


class Parser(object):
    red_span_re = re.compile('<span style="color:red">([123]\+?|N)</span>')

    def __init__(self):
        self.g = Grab()

    def fetch(self):
        """
        Идет на сайт дозора, парсит страницу, и обновляет текущее состояние
        """
        pass

    def get_sector_list(self):
        """
        Возвращает списки КО, в виде словаря, в котором ключ - название группы КО, значение - список КО.
        Пример:
        [
            {
                'name': 'Основные коды',
                'code_list': [
                    {
                        'ko':'1+',
                        'taken': False,
                    },
                    {
                        'ko':'1',
                        'taken': True,
                    },
                    {
                        'ko':'3',
                        'taken': True,
                    }
                ]
            },
            {
                'name': 'Бонусные коды',
                'code_list': [
                    {
                        'ko':'2+',
                        'taken': False,
                    },
                    {
                        'ko':'4',
                        'taken': False,
                    }
                ]
            }
        ]
        """
        div_list = self.g.doc.select('//div[@class="zad"]')
        div_html = next((div.html() for div in div_list if '<strong>Коды сложности</strong>' in div.html()), None)
        if div_html is None:
            return []
        ko_part = div_html.split('<strong>Коды сложности</strong><br> ')[1]
        ko_part = ko_part.replace('null', 'N').replace('<br></div>', '').replace('\n', '').replace('\r', '')
        ko_part = self.red_span_re.sub('V', ko_part)
        result = []
        for sector in ko_part.split('<br>'):
            sector_name, sector_code_str = sector.split(': ')
            result.append({
                'name': sector_name,
                'ko_list': sector_code_str.split(', '),
            })
        return result
