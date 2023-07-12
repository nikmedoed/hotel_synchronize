from utils.loadenv import bnovo_client
from tqdm import tqdm

# Это копирует комнаты + виртуальные номера в биново

NEW_ROOMS = [
    # '№18 ГКС "Лазурный берег"',
    # '№17 ГКС "Жаркая Мексика"',
    # '№16 ГКС "Лагуна Колорадо"',
    # '№15 ГКС "Ниагара"',
    # '№14 ГКС "Пряный Марракеш"',
    # '№13 ГКС "Замки Луары"',
    # '№12 ГКС "Индия"'
]

KEYS_TO_COPY = [
    "name",
    "adults",
    "price",
    "parent_id",
    "children",
    "enabled",
    "enabled_ota",
    "description",
    "accommodation_type",
    "name_ru",
    "name_en",
    "name_de",
    "name_zh",
    "name_es",
    "name_fr",
    "name_ja",
    "name_it",
    "name_ko",
    "name_pl",
    "name_fi",
    "name_lt",
    "description_ru",
    "description_en",
    "description_de",
    "description_zh",
    "description_es",
    "description_fr",
    "description_ja",
    "description_it",
    "description_ko",
    "description_pl",
    "description_fi",
    "description_lt"
]

TARGET_NAME = '№4 ГКЛ "Северное сияние"'

bnovo_rooms = bnovo_client.get_roomtypes()

to_copy = [x for k, x in bnovo_rooms.items() if x['name'].startswith(TARGET_NAME)]

categories = []
for room in to_copy:
    parent = room['parent_id']
    if parent:
        categories.append(room)
    else:
        par = room

for name in NEW_ROOMS:
    parent = {i: par[i] for i in KEYS_TO_COPY}
    parent['name'] =parent['name'].replace(TARGET_NAME, name)
    res = bnovo_client.create_room(parent)
    parent_id =res["roomtype_id"]
    for ch in tqdm(categories):
        child ={i: ch[i] for i in KEYS_TO_COPY}
        child['name'] =child['name'].replace(TARGET_NAME, name)
        child['parent_id'] = parent_id
        res = bnovo_client.create_room(child)
