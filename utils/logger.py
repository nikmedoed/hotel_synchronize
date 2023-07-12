import logging

import requests

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)


class TelegramHandler(logging.Handler):

    def __init__(self, token, chat_ids):
        super().__init__()
        self.token = token
        self.chat_ids = chat_ids

        self.level_emojis = {
            'INFO': '✨',
            'WARNING': '⚠️',
            'ERROR': '❌'
        }

    def emit(self, record):
        message = self.format(record)
        level = record.levelname
        emoji = self.level_emojis.get(level, '👀')
        self.send_message(emoji + ' ' + message)

    def handle(self, record):
        if record.levelno >= logging.INFO:
            super().handle(record)

    def send_message(self, message):
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"

        for i in self.chat_ids:
            try:
                params = {
                    "chat_id": i,
                    "text": message
                }
                response = requests.post(url, json=params)
                if response.status_code != 200:
                    raise ValueError(f"Failed to send Telegram message {response.json()}")
            except Exception as e:
                print(f"ERROR = Bot: {e}, id: {i}, mess: {message}")
