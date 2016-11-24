import os
import codecs
from unittest.case import skip

import settings

from unittest import TestCase
from unittest.mock import Mock, patch

from bot import DzrBot
from parser import Parser, HELP_TEXT
from views import KoImg


class BotTestCase(TestCase):
    @patch('parser.settings.DATASET', settings.DATASET_TEST)
    def setUp(self):
        self.parser = Parser()
        settings.CHAT_ID = 'CHAT_ID'
        settings.CHANNEL_ID = 'CHANNEL_ID'
        self.bot = DzrBot(None)
        self.bot.type = True
        self.bot.sendMessage = Mock()
        self.bot.parser = self.parser
        self.bot.parser.fetch = Mock()
        self.bot.parse = True
        self.bot.sentry = None

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

    def test_help(self):
        self.bot.on_chat_message({'chat': {'id': None}, 'text': '/help'})
        self.bot.sendMessage.assert_any_call('CHAT_ID', HELP_TEXT)

    def test_code_fail(self):
        """
        Вызываем пробитие кода (dr4).
        Если код неверный, то бот должен послать об этом сообщение в чат
        """
        self.set_html('pages/code_1.html')
        self.parser._parse_message = Mock(return_value={'message': 'код не принят'})
        self.bot.on_chat_message({'chat': {'id': None}, 'text': 'dr4', 'message_id': 321})
        self.bot.sendMessage.assert_any_call('CHAT_ID', 'dr4 : код не принят', reply_to_message_id=321)

    def test_code_empty(self):
        """
        Нестандартный код пишется через слэш
        """
        self.set_html('pages/code_1.html')
        self.parser._parse_message = Mock(return_value={'message': 'код не принят'})
        self.bot.on_chat_message({'chat': {'id': None}, 'text': '/ НЕСТАНДАРТНЫЙКОД1', 'message_id': 321})
        self.bot.sendMessage.assert_any_call('CHAT_ID', 'нестандартныйкод1 : код не принят', reply_to_message_id=321)

    def test_new_level(self):
        """Если наступает новый уровень, то бот должен послать об этом сообщение в канал"""
        self.set_html('pages/tip_1.html')
        self.parser.parse()
        self.set_html('pages/code_1.html')
        self.bot.handle_loop()
        self.bot.sendMessage.assert_any_call('CHANNEL_ID', 'Новый уровень')

    def test_new_tip(self):
        """Если возникает новая подсказка, то бот должен послать об этом сообщение в канал"""
        self.set_html('pages/tip_1.html')
        self.parser.parse()
        self.set_html('pages/tip_2.html')
        self.bot.handle_loop()
        self.bot.sendMessage.assert_any_call('CHANNEL_ID', 'Подсказка: Ответ на спойлер: пустырь')

    def test_new_spoiler(self):
        """Если открывается спойлер, то бот должен послать об этом сообщение в канал"""
        self.set_html('pages/spoiler_1.html')
        self.parser.parse()
        self.set_html('pages/spoiler_2.html')
        self.bot.handle_loop()
        self.bot.sendMessage.assert_any_call('CHANNEL_ID', 'Открыт спойлер')

    def test_new_code(self):
        """
        Если в движке появился новый пробитый код,
        то бот должен послать табличку об этом в канал.
        Обратите внимание на взятый код по 11-й метке.
        """
        self.set_html('pages/code_1.html')
        self.parser.parse()
        self.set_html('pages/code_1.html')
        self.parser.parse()
        self.set_html('pages/code_2.html')
        self.bot.handle_loop()
        self.bot.sendMessage.assert_any_call(
            'CHANNEL_ID',
            ' основные коды\n'
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
            parse_mode='Markdown',
        )

        self.bot.sendMessage.reset_mock()
        self.set_html('pages/code_3.html')
        self.bot.handle_loop()

        self.bot.sendMessage.assert_any_call(
            'CHANNEL_ID',
            ' основные коды\n'
            '```\n'
            ' 1 3   V    11 1+  V    \n'
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
            parse_mode='Markdown',
        )

    def test_type(self):
        self.bot.on_chat_message({'chat': {'id': None}, 'text': '/type'})
        self.bot.sendMessage.assert_any_call('CHAT_ID', 'Режим ввода кодов: Включен')

        self.bot.sendMessage.reset_mock()
        self.bot.on_chat_message({'chat': {'id': None}, 'text': '/type off'})
        self.bot.sendMessage.assert_any_call('CHAT_ID', 'Режим ввода кодов: Выключен')

        self.bot.sendMessage.reset_mock()
        self.bot.on_chat_message({'chat': {'id': None}, 'text': '/type on'})
        self.bot.sendMessage.assert_any_call('CHAT_ID', 'Режим ввода кодов: Включен')


@skip
class BotImgTestCase(TestCase):
    def test_ko_img(self):
        self.bot = DzrBot(settings.TOKEN)
        ko_img = KoImg(ko_list=['1', '2', '3'])
        self.bot.sendPhoto(818051, ('ko.png', ko_img.content))
