from utils.loadenv import bnovo_client, wubook_clients
from tqdm import tqdm
from itertools import chain

# !!! clean wubook rooms
# for wc in wubook_clients:
#     for room in wc.rooms():
#         print("Пробую удалить", room.name, end='\t :: ')
#         try:
#             print('Результат удаления', wc.remove_room(room.id))
#         except:
#             print('Не вышло')

wubook_dict = {i.lcode: i for i in wubook_clients}
wubook_rooms = chain(*[c.rooms() for c in wubook_dict.values()])

rooms_names = {w.name: w.id for w in wubook_rooms}

# В данном случае надо было разбить номера по объектам из-за лимита 80 номеров
with open('id-object_list', 'r') as f:
    rooms_to_object = dict([r.split() for r in f.read().split('\n')])

r = {}

bnovo_rooms = bnovo_client.get_roomtypes()

# это корректно для списка в момент написания. Если родители будут не первыми,
# то нужно правильно обработать детей до появления родителя
for key, room in bnovo_rooms.items():
    parent = room['parent_id']
    room['code'] = key
    if parent:
        r[parent]['virtual'].append(room)
    else:
        room['virtual'] = []
        r[room['id']] = room

# История с созданием уникальных кодов до 4 символов
count = 0

# в вубуке есть реальные комнаты и их вариации (реальные), подготовим данные и отправим.
# коробке имя это странная штука - 4х значный уникальный код, можно буквы.
for key, room in r.items():
    to_object = rooms_to_object.get(str(room['id']))
    if not to_object:
        print("no object match for", room['id'], room['name'])
        continue
    wubook_client = wubook_dict.get(to_object)
    if not wubook_client:
        print("no wubook client for object id", to_object)
        continue

    count += 1
    parent_id = rooms_names.get(room['name'])
    if not parent_id:
        print("creates", room['name'])
        body = {
            'name': room['name'],
            'beds': room['adults'],
            'defprice': room['price'],
            'shortname': f"{count:02}00",
            'names': {'ru': room['name_ru']},
            'descriptions': {'ru': room['description_ru']}
        }
        parent_id = wubook_client.new_room(**body)
    c2 = 0
    created = 0
    err_count = 0
    exists = 0
    errorrs = set()
    for child in tqdm(room['virtual'], desc = room['name']):
        c2 += 1
        ch_id = rooms_names.get(child['name'])
        if ch_id:
            exists += 1
        else:
            while 1:
                try:
                    cbody = {
                        'rid': parent_id,
                        'name': child['name'],
                        'beds': child['adults'] + child['children'],
                        'defprice': child['price'],
                        'shortname': f"{count:02}{c2:02}",
                        'names': {'ru': child['name_ru']},
                        'children': child['children'],
                        'descriptions': {'ru': child['description_ru']}
                    }
                    wubook_client.new_virtual_room(**cbody)
                    created += 1
                    break
                except Exception as err:
                    err = str(err)
                    if 'Shortname has to be unique. This shortname is already used' in err:
                        c2 += 1
                    else:
                        err_count += 1
                        errorrs.add(err)
                        break
    if created or err_count:
        print(f"Subrooms created: {created}/{len(room['virtual'])-exists},\texists:{exists},\terrors: {err_count}\tfor {room['name']}")
    if errorrs:
        print("Errors:\n", "\n".join(errorrs))
