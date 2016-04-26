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
        self.bot.sendMessage = Mock(return_value={})
        self.bot.parser = self.parser

    def tearDown(self):
        """Очищаем таблицы после прохождения каждого теста"""
        self.parser.table_tip.delete()
        self.parser.table_code.delete()
        self.parser.table_sector.delete()

    def set_html(self, filename):
        filepath = os.path.join(os.path.dirname(__file__), filename)
        with codecs.open(filepath, encoding='cp1251') as f:
            html = f.read()
            html_bytes = bytes(html, encoding='cp1251')
            self.parser.g.setup_document(html_bytes)

    def test_code_fail(self):
        self.parser.take_code = Mock(return_value='Код не принят')
        self.bot.on_chat_message({
            'text': 'dr4',
            'chat': {'id': None},
        })
        self.bot.sendMessage.assert_called_once_with(None, 'dr4 : Код не принят')

    def test_code_success_multiple_metka(self):
        self.set_html('pages/19/1.html')
        self.parser.parse()
        self.set_html('pages/19/3.html')

        self.parser.take_code = Mock(return_value='Принят код')

        self.bot.on_chat_message({
            'text': 'dr4',
            'chat': {'id': None},
        })
        self.bot.sendMessage.assert_called_once_with(None, 'dr4 : Принят код . Метка: 8 или 11')

    def test_code_success_one_metka(self):
        self.set_html('pages/19/1.html')
        self.parser.parse()
        self.set_html('pages/19/2.html')

        self.parser.take_code = Mock(return_value='Принят код')

        self.bot.on_chat_message({
            'text': 'dr4',
            'chat': {'id': None},
        })
        self.bot.sendMessage.assert_called_once_with(None, 'dr4 : Принят код . Метка: 8')
