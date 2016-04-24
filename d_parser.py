from grab.base import Grab
import re


class Parser(object):
    red_span_re = re.compile('<span style="color:red">([123]\+?|N)</span>')
    state = {}  # Состояние дозорного движка. Пример состояния - в файле d_parser_state_example.py

    def __init__(self):
        self.g = Grab()

    def fetch(self):
        """
        Идет на сайт дозора, парсит страницу и обновляет текущее состояние
        """
        self.state = self.get_state()

    def get_state(self):
        return {
            'game': self.get_game(),
            'level': self.get_level(),
        }

    def get_level(self):
        return {
            'codes_left': 0,
            'sector_list': self.get_sector_list(),
        }

    def get_game(self):
        return {
            'current_level': 0,
        }

    def get_sector_list(self):
        div_list = self.g.doc.select('//div[@class="zad"]')
        div_html = next((div.html() for div in div_list if '<strong>Коды сложности</strong>' in div.html()), None)
        if div_html is None:
            return []
        ko_part = div_html.split('<strong>Коды сложности</strong><br> ')[1]
        ko_part = ko_part.replace('null', 'N').replace('<br></div>', '').replace('\n', '').replace('\r', '')
        result = []
        for sector in ko_part.split('<br>'):
            sector_name, sector_code_str = sector.split(': ')
            code_list = []
            for item in sector_code_str.split(', '):
                code_list.append({
                    'ko': item,
                    'taken': False,
                })
            result.append({
                'name': sector_name,
                'code_list': code_list,
            })
        return result

    def get_tips_list(self):
        div_list = self.g.doc.select('//div[@class="title"]')
        div_html = next((div for div in div_list if 'Подсказка l:' in div.html()), None)
        if div_html is None:
            return []
        tip_text = div_html.node().getnext().text_content()
        return [tip_text]
