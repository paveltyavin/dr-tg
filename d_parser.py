from grab.base import Grab
import re


class Parser(object):
    red_span_re = re.compile('<span style="color:red">([123]\+?|N)</span>')

    def __init__(self):
        self.g = Grab()

    def get_html(self):
        """
        Идет на сайт дозора, парсит страницу и записывает ее в аттрибут html
        TODO: Здесь должна быть работа с объектом self.g
        """
        pass

    def get_sector_list(self):
        """
        Возвращает списки КО, в виде словаря, в котором ключ - название группы КО, значение - список КО.
        Пример:
        [{'name': 'Первый сектор', 'ko': ['1+', '1', '3']},{'name': 'Второй сектор','ko' = ['1', '2']}]

        В обычном уровне (без секторов)
        [{'name': 'Основные коды','ko': ['1+', '1', '3']}]
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
