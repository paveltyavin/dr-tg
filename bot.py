from telepot import Bot
import settings
import re
import time

from models import Parser, freq_dict, HELP_TEXT
from views import sector_text, KoImg

CORD_RE = '([35]\d[\.,]\d+)'
STANDARD_CODE_PATTERN = '\d*[dдrрDДRР]\d*[dдrрDДRР]\d*'


# STANDARD_CODE_PATTERN = '(?:([1-9]+))?(?:([dд])|[rр])(?:([1-9]+))?(?(2)[rр]|[dд])(?(1)[1-9]*|(?(3)[1-9]*|[1-9]+))'
# STANDARD_CODE_PATTERN = '\b\d*[dд]\d*[rр]\d*(?<=\w\w\w)\b|\b\d*[rр]\d*[dд]\d*(?<=\w\w\w)\b'


class ManulaBot(Bot):
    freq = 28  # Частота рации
    parse = False  # Режим парсинга движка
    type = False  # Режим ввода кодов

    routes = (
        (CORD_RE, 'on_cord'),
        (r'^/link', 'on_link'),
        (r'^/test_ko_img', 'on_test_ko_img'),
        (r'^/test_error', 'on_test_error'),
        (r'^/freq', 'on_freq'),
        (r'^/help', 'on_help'),
        (r'^/type', 'on_type'),
        (r'^/parse', 'on_parse'),
        (r'^/cookie', 'on_cookie'),
        (r'^/pin', 'on_pin'),
        (r'^/pattern', 'on_pattern'),
        (r'^/status', 'on_status'),
    )

    def set_data(self, key, value):
        setattr(self, key, value)
        self.parser.table_bot.upsert({
            'token': settings.TOKEN,
            key: value
        }, ['token'])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser = Parser()

        self.parser.table_bot.upsert({'token': settings.TOKEN}, ['token'])
        data = self.parser.table_bot.find_one(**{'token': settings.TOKEN})
        for key in [
            'freq',
            'type',
            'parse',
        ]:
            value = data.get(key)
            if value is not None:
                setattr(self, key, value)

        cookie = data.get('cookie')
        if cookie:
            self.parser.set_cookie(cookie)

        pin = data.get('pin')
        if pin:
            self.parser.set_pin(pin)

        code_pattern = data.get('code_pattern')
        if code_pattern:
            self.code_pattern = code_pattern
        else:
            self.code_pattern = STANDARD_CODE_PATTERN

    def on_help(self, chat_id, text):
        self.sendMessage(chat_id, HELP_TEXT)

    def on_type(self, chat_id, text):
        if 'on' in text:
            self.set_data('type', True)
        elif 'off' in text:
            self.set_data('type', False)
        self.sendMessage(chat_id, "Режим ввода кодов: {}".format("Включен" if self.type else "Выключен"))

    def on_parse(self, chat_id, text):
        if 'on' in text:
            self.set_data('parse', True)
        elif 'off' in text:
            self.set_data('parse', False)
        self.sendMessage(chat_id, "Режим парсинга движка: {}".format("Включен" if self.parse else "Выключен"))

    def on_cookie(self, chat_id, text):
        for cookie in re.findall('(\w{24})', text):
            self.parser.set_cookie(cookie)
            self.set_data('cookie', cookie)
            self.sendMessage(chat_id, "Кука установлена")

    def on_test_ko_img(self, chat_id, text):
        self.send_ko_img(chat_id)

    def on_test_error(self, chat_id, text):
        raise Exception

    def on_pin(self, chat_id, text):
        text = text.replace('/pin', '').strip()
        if text:
            self.parser.set_pin(text)
            self.set_data('pin', text)
            self.sendMessage(chat_id, "Пин установлен")
        else:
            data = self.parser.table_bot.find_one(**{'token': settings.TOKEN})
            pin = data.get('pin')
            if pin:
                self.sendMessage(chat_id, "Пин для игры: {}".format(pin))
            else:
                self.sendMessage(chat_id, "Пин отсутствует")

    def on_pattern(self, chat_id, text):
        text = text.replace('/pattern', '').strip()
        if 'standar' in text:
            text = STANDARD_CODE_PATTERN

        if text:
            try:
                re.compile(text)
            except re.error:
                self.sendMessage(chat_id, "Шаблон кода не установлен")

            self.set_data('code_pattern', text)
            self.sendMessage(chat_id, "Шаблон кода установлен: {}".format(text))
        else:
            self.sendMessage(chat_id, "Шаблон кода: {}".format(self.code_pattern))

    def on_link(self, chat_id, text):
        data = self.parser.table_bot.find_one(**{'token': settings.TOKEN})
        pin = data.get('pin')
        if pin:
            self.sendMessage(chat_id, "Пин для игры: {}".format(pin))

    def on_cord(self, chat_id, text):
        cord_list = re.findall(CORD_RE, text)
        if len(cord_list) == 2:
            self.sendLocation(chat_id, *cord_list)

    def on_code(self, chat_id, text):
        code_list = re.findall(self.code_pattern, text, flags=re.I)

        for code in code_list:
            if len(code) < 3:
                return
            take_message = self.parser.take_code(code)
            if not take_message:
                continue
            message = "{} : {}".format(code, take_message)

            if False and 'принят' in take_message.lower() and 'код не принят' not in take_message.lower():
                # Если код принят, то парсим движок на принятые коды.
                parse_result = self.parser.parse(update_db=False)
                metka_list = []
                sector_list = parse_result['sector_list']
                for sector in sector_list:
                    for code in sector['code_list']:
                        metka_list.append(code['metka'])
                if metka_list:
                    message = "{} . Метка: {}".format(message, " или ".join(list(map(str, metka_list))))
            self.sendMessage(chat_id, message)

    def on_freq(self, chat_id, text):
        try:
            self.set_data('freq', int(text.replace('/freq', '')))
        except ValueError:
            pass
        freq_result = freq_dict.get(self.freq)
        if freq_result is None:
            self.sendMessage(chat_id, 'Используйте команду "/freq <число>" , где <число> - номер канала midland от 1 до 60.')
        else:
            self.sendMessage(chat_id, 'Основная частота: {} ||| Канал Midland: {}'.format(
                freq_result,
                str(self.freq),
            ))

    def on_status(self, chat_id, text):
        self.parser.fetch()
        body = self.parser.g.doc.body.decode('cp1251')
        connected = 'лог игры' in body.lower()
        if connected:
            self.sendMessage(chat_id, 'Движок подключен')
        else:
            self.sendMessage(chat_id, 'Проблемы с подключением к движку')

    def on_chat_message(self, msg):
        text = msg.get('text')
        if text is None:
            return
        chat_id = msg['chat'].get('id')

        # Отвечает не собеседнику, а в определенный чат, если в settings этот чат задан явно.
        if hasattr(settings, 'CHAT_ID'):
            if chat_id and chat_id != settings.CHAT_ID:
                return
            else:
                chat_id = settings.CHAT_ID

        for pattern, method_str in self.routes:
            method = getattr(self, method_str, None)
            if method is not None and re.search(pattern, text):
                method(chat_id, text)

        if self.type and 2 < len(text) < 100 and re.search(self.code_pattern, text, flags=re.I):
            self.on_code(chat_id, text.strip().lower())

    def send_ko(self, channel_id):
        for sector in self.parser.table_sector.all():
            sector['code_list'] = list(self.parser.table_code.find(sector_id=sector['id']))
            self.sendMessage(channel_id, sector_text(sector), parse_mode='Markdown')

    def send_ko_img(self, channel_id):
        for sector in self.parser.table_sector.all():
            ko_list = list(self.parser.table_code.find(sector_id=sector['id']))
            ko_img = KoImg(ko_list=ko_list)
            self.sendPhoto(channel_id, ('ko.png', ko_img.content))

    def handle_loop(self):
        if not self.parse:
            return
        channel_id = getattr(settings, 'CHANNEL_ID', None)
        if channel_id is None:
            return

        self.parser.fetch()
        parse_result = self.parser.parse()

        if parse_result['new_level']:
            self.sendMessage(channel_id, 'Новый уровень')
            self.send_ko(channel_id)
            # self.send_ko_img(channel_id)

        for tip in parse_result['tip_list']:
            self.sendMessage(channel_id, "Подсказка: {}".format(tip['text']))

        if parse_result['new_code']:
            self.send_ko(channel_id)

        if parse_result['new_spoiler']:
            self.sendMessage(channel_id, 'Открыт спойлер')


if __name__ == '__main__':
    bot = ManulaBot(settings.TOKEN)
    bot.message_loop()
    while 1:
        bot.handle_loop()
        time.sleep(getattr(settings, 'SLEEP_SECONDS', 30))
