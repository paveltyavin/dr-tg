import os
import codecs
import settings

from unittest import TestCase
from unittest.mock import Mock

from bot import ManulaBot
from models import Parser


class BotTestCase(TestCase):
    def setUp(self):
        self.parser = Parser()
        if hasattr(settings, 'CHAT_ID'):
            del settings.CHAT_ID
        self.bot = ManulaBot(None)
        self.bot.sendMessage = Mock()
        self.bot.parser = self.parser
        self.bot.parser.fetch = Mock()

    def tearDown(self):
        """Очищаем таблицы после прохождения каждого теста"""
        self.parser.table_tip.delete()
        self.parser.table_code.delete()
        self.parser.table_sector.delete()

    def set_html(self, filename):
        """Это метод устанавливает "текущую" страницу дозорного дижка"""
        filepath = os.path.join(os.path.dirname(__file__), filename)
        with codecs.open(filepath, encoding='cp1251') as f:
            html = f.read()
            html_bytes = bytes(html, encoding='cp1251')
            self.parser.g.setup_document(html_bytes)

    def test_code_fail(self):
        """
        Вызываем пробитие кода (dr4).
        Если код неверный, то бот должен послать об этом сообщение в чат
        """
        self.parser.take_code = Mock(return_value='Код не принят')
        self.bot.on_chat_message({'chat': {'id': None}, 'text': 'dr4'})
        self.bot.sendMessage.assert_called_once_with(None, 'dr4 : Код не принят')

    def test_code_success_one_metka(self):
        """
        Вызываем пробитие кода (dr4),
        предварительно настроив движок так, что он ответит "Принят код".
        Бот должен послать в чат сообщение о принятие кода и номере метки
        """
        self.set_html('pages/code_1.html')
        self.parser.parse()
        self.parser.take_code = Mock(return_value='Принят код')
        self.set_html('pages/code_2.html')

        self.bot.on_chat_message({'chat': {'id': None}, 'text': 'dr4'})
        self.bot.sendMessage.assert_called_once_with(None, 'dr4 : Принят код . Метка: 8')

    def test_code_success_multiple_metka(self):
        """то же, что в методе test_code_success_one_metka, только несколько возможных меток"""
        self.set_html('pages/code_1.html')
        self.parser.parse()
        self.parser.take_code = Mock(return_value='Принят код')
        self.set_html('pages/code_3.html')

        self.bot.on_chat_message({'chat': {'id': None}, 'text': 'dr4'})
        self.bot.sendMessage.assert_called_once_with(None, 'dr4 : Принят код . Метка: 8 или 11')

    def test_freq(self):
        """Тест сообщения на запрос частоты"""
        self.bot.on_chat_message({'chat': {'id': None}, 'text': '/freq'})
        self.bot.sendMessage.assert_called_once_with(None, 'Основная частота: 433.775 ||| Канал Midland: 28')

    def test_new_level(self):
        """Если наступает новый уровень, то бот должен послать об этом сообщение в канал"""
        self.set_html('pages/tip_1.html')
        self.parser.parse()
        self.set_html('pages/code_1.html')
        self.bot.handle_loop()
        self.bot.sendMessage.assert_called_once_with(None, 'Новый уровень.')

    def test_new_tip(self):
        """Если возникает новая подсказка, то бот должен послать об этом сообщение в канал"""
        self.set_html('pages/tip_1.html')
        self.parser.parse()
        self.set_html('pages/tip_2.html')
        self.bot.handle_loop()
        self.bot.sendMessage.assert_called_once_with(None, 'Подсказка: Ответ на спойлер: пустырь')

    def test_new_code(self):
        """
        Если какой-то появился новый код судя по движку,
        то бот должен послать табличку об этом в канал"""
        self.set_html('pages/code_1.html')
        self.parser.parse()
        self.set_html('pages/code_2.html')
        self.bot.handle_loop()
        self.bot.sendMessage.assert_called_once_with(
            None,
            'основные коды\n'
            '```\n'
            ' 1 3   V    11 1+       \n'
            ' 2 2   V    12 1   V    \n'
            ' 3 3   V    13 1+  V    \n'
            ' 4 2   V    14 1   V    \n'
            ' 5 2   V    \n'
            ' 6 1   V    \n'
            ' 7 1   V    \n'
            ' 8 2   V    \n'
            ' 9 1   V    \n'
            '10 1+       \n'
            '```',
        )
