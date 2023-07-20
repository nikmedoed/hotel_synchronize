import os
from dotenv import load_dotenv
from service.bnovo import BnovoAPI
from service.wubook import WuBook
from service.bnovoPMS import BnovoPMSapi
from utils.logger import TelegramHandler
import logging

load_dotenv()


def keys_to_dict(keys, prefix=""):
    d = {}
    for k in keys:
        key = f'{prefix}{k}'.upper()
        res = os.getenv(key)
        if not res:
            raise Exception(f"Не указан параметр окружения {key}")
        d[k] = res
    return d


RESERVATIONSTEPS_USER = keys_to_dict(("username", "password", "account_id"), 'bnovo_')
PMS_USER = keys_to_dict(("username", "password"), 'bnovo_pms_')
WUBOOK_USER = keys_to_dict(("token", "lcodes"), 'wubook_')

WUBOOK_USERS = []
for code in WUBOOK_USER['lcodes'].split(','):
    d = {**WUBOOK_USER, 'lcode': code}
    del d['lcodes']
    WUBOOK_USERS.append(d)

bnovo_client = BnovoAPI(**RESERVATIONSTEPS_USER)
wubook_clients = [WuBook(**wu) for wu in WUBOOK_USERS]
bnovo_pms_client = BnovoPMSapi(**PMS_USER)
DEBUG_RUNNING = os.getenv('DEBUG_RUNNING')== 'True'

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_IDS = os.getenv('CHAT_IDS').split(',')

telegram_handler = TelegramHandler(token=TELEGRAM_BOT_TOKEN, chat_ids=CHAT_IDS)
logging.root.addHandler(telegram_handler)
