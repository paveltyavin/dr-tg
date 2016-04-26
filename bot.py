from telepot import Bot
import settings
import re

from models import Parser, freq_dict

CORD_RE = '([35]\d[\.,]\d+)'
LINK_RE = re.compile(r'/link', flags=re.I)
CODE_RE = re.compile(r'\b\d*[dд]\d*[rр]\d*(?<=\w\w\w)\b|\b\d*[rр]\d*[dд]\d*(?<=\w\w\w)\b', flags=re.I)


class ManulaBot(Bot):
    freq = 28  # Частота рации

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser = Parser()

    def on_link(self, chat_id, text):
        self.sendMessage(chat_id, 'Ссылка')

    def on_cord(self, chat_id, text):
        cord_list = re.findall(CORD_RE, text)
        if len(cord_list) == 2:
            self.sendLocation(chat_id, *cord_list)

    def on_code(self, chat_id, text):
        code_list = re.findall(CODE_RE, text)

        for code in code_list:
            take_message = self.parser.take_code(code)
            message = "{} : {}".format(code, take_message)

            if 'Принят код' in take_message:
                # Если код принят, то парсим движок на принятые коды.
                parse_result = self.parser.parse()
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
            self.freq = int(text.replace('/freq', ''))
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

    def on_auth(self, chat_id, text):
        try:
            login, password = map(
                lambda x: x.strip(),
                filter(
                    bool,
                    text.replace('/auth', '').split(' ')
                )
            )
        except ValueError:
            return
        self.parser.auth(login, password)
        self.sendMessage(chat_id, 'Авторизация установлена. Логин = {}'.format(login))

    def on_chat_message(self, msg):
        text = msg['text']
        chat_id = msg['chat'].get('id')

        # Отвечает не собеседнику, а в определенный чат, если в settings этот чат задан явно.
        if hasattr(settings, 'CHAT_ID'):
            chat_id = settings.CHAT_ID

        if re.match(CORD_RE, text):
            return self.on_cord(chat_id, text)

        if re.match(LINK_RE, text):
            return self.on_link(chat_id, text)

        if re.match(r'^/freq', text):
            return self.on_freq(chat_id, text)

        if re.match(CODE_RE, text):
            return self.on_code(chat_id, text)

        if re.match(r'^/auth', text):
            return self.on_auth(chat_id, text)


if __name__ == '__main__':
    bot = ManulaBot(settings.TOKEN)
    bot.message_loop(run_forever=True)
