from grab.base import Grab
import re

class Parser(object):
    def __init__(self):
        self.g = Grab()
        self.red_span_re = re.compile(r'<span style="color:red">([123]\+?|N)</span>')

    def get_html(self):
        """
        Идет на сайт дозора, парсит страницу и записывает ее в аттрибут html
        TODO: Здесь должна быть работа с объектом self.g
        """
        pass

    def get_ko_list(self):
        """
        Возвращает списки КО, в виде словаря, в котором ключ - название группы КО, значение - список КО.
        Пример:
        {'основные коды': ['1+', '1', '3'], 'бонусные коды': ['2', '3', '1']}
        """
        div_list = self.g.doc.select('//div[@class="zad"]')
        for i in div_list:
            if '<strong>Коды сложности</strong>' in i.html():
                div_html = i.html()
        ko_part = div_html.split('<strong>Коды сложности</strong><br> ')[1]
        ko_part = ko_part.replace('null', 'N').replace('<br></div>', '').replace('\n', '').replace('\r', '')
        ko_part = self.red_span_re.sub('V', ko_part)
        code_lists = ko_part.split('<br>')
        code_dict = {}
        for i in code_lists:
            ko_dict = i.split(': ')
            key = ko_dict[0]
            value = ko_dict[1].split(', ')
            item = [key, value]
            code_dict.update([item])
        print(code_dict)
        return code_dict