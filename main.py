from service.wubook import WuBookRoom
from itertools import chain
import logging
from time import sleep

from utils.bnovo_to_wubook import update_wubook_copy, bnovo_to_wubook_new_record
from utils.database import BNOVO_TAG, WUBOOK_TAG
from utils.updates import split_dict, make_updates
from utils.wubook_to_bnovo import update_bnovo_copy, wubook_to_bnovo_new_record
from utils.actual_bookings import get_actual_wubook_bookings, get_actual_bnovo_bookings, count_wubook_cancelled, \
    count_bnovo_cancelled
from utils.loadenv import bnovo_client, wubook_clients, DEBUG_RUNNING


def get_rooms_comparison():
    # составляем словари переназначений комнат
    wubook_rooms = chain(*[c.rooms() for c in wubook_clients])
    bnovo_rooms = bnovo_client.get_roomtypes()

    # if DEBUG_RUNNING:
    #     bnovo_rooms = {k: v for k, v in bnovo_rooms.items() if 'Тестовая' in v['name']}
    #     wubook_rooms = [room for room in wubook_rooms if 'Тестовая' in room.name]

    tempdict: dict[str, WuBookRoom] = {room.name: room for room in wubook_rooms}
    roomid_bnovo_to_wubook = {}
    roomid_wubook_to_binovo = {}

    for key, room in bnovo_rooms.items():
        wroom = tempdict.get(room['name'])
        if not wroom:
            logging.warning(f'No room in wubook {room["name"]}')
        else:
            roomid_bnovo_to_wubook[room['id']] = wroom
            roomid_bnovo_to_wubook[str(room['id'])] = wroom
            roomid_bnovo_to_wubook[room['name']] = wroom
            roomid_wubook_to_binovo[wroom.id] = room
            roomid_wubook_to_binovo[str(wroom.id)] = room
    return roomid_bnovo_to_wubook, roomid_wubook_to_binovo


def synchroiteration(roomid_bnovo_to_wubook, roomid_wubook_to_binovo):
    # Собираем брони для обработки, остальные пропустятся
    bnovo_bookings = get_actual_bnovo_bookings()
    logging.info(f"bnovo collected {len(bnovo_bookings)} booking, "
                 f"is cancelled {count_bnovo_cancelled(bnovo_bookings.values())}")
    wubook_bookings = get_actual_wubook_bookings()
    logging.info(f"wubook collected {len(wubook_bookings)} booking, "
                 f"is cancelled {count_wubook_cancelled(wubook_bookings.values())}")

    # Step 1: Делим записи на те, что помечены в базе (по ключу есть ид оригинала) и оригинальные
    wubook_bookings_from_bnovo = split_dict(wubook_bookings, WUBOOK_TAG)
    bnovo_bookings_from_wubook = split_dict(bnovo_bookings, BNOVO_TAG)

    # Step 2: Обновляем дубликаты, убираем из списка оригиналы, что были в дубликатах
    # Считаем, что информация в биново актуальнее
    make_updates(wubook_bookings_from_bnovo, bnovo_bookings, WUBOOK_TAG, update_wubook_copy, roomid_bnovo_to_wubook)
    make_updates(bnovo_bookings_from_wubook, wubook_bookings, BNOVO_TAG, update_bnovo_copy, roomid_bnovo_to_wubook)
    # После у нас останутся новые записи, которые нужно продублировать в системах

    # Step 3: Создаём новые записи из остатков
    for book_id, book in wubook_bookings.items():
        rooms = book.dayprices and {room: roomid_wubook_to_binovo.get(room) for room in book.dayprices}
        wubook_to_bnovo_new_record(rooms, book)

    for book_id, book in bnovo_bookings.items():
        wub_room = roomid_bnovo_to_wubook.get(book.initial_room_type_name)
        bnovo_to_wubook_new_record(wub_room, book)


def safe_execution(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except Exception as e:
        mes = str(e)
        sleep_time = 0
        if "More than 288" in mes:
            sleep_time = 300
        if "in the last 3600 seconds" in mes:
            sleep_time = 3300
        if "More than 240" in mes:
            sleep_time = 600
        if sleep_time:
            logging.error(
                f"Ошибка выполнения функции {func.__name__}, ограничения вубук. Спим {sleep_time / 60:.1f} мин {mes}")
            sleep(sleep_time)
        else:
            logging.error(f"Непредвиденная ошибка в функции {func.__name__}: {mes}")
            try:
                logging.error(e.with_traceback())
            except:
                print("Не получилось вывести traceback")
        return None


if __name__ == "__main__":
    SLEEP_TIME = 240
    # Получаем сопоставления. Для каких номеров нет сопоставлений, пропустим
    rooms = None
    while not rooms:
        rooms = safe_execution(get_rooms_comparison)
    roomid_bnovo_to_wubook, roomid_wubook_to_binovo = rooms
    while 1:
        logging.info("New synchroiteration start")
        if not DEBUG_RUNNING:
            result = safe_execution(synchroiteration, roomid_bnovo_to_wubook, roomid_wubook_to_binovo)
            logging.info(f"iteration end, sleep {SLEEP_TIME} sec")
            sleep(SLEEP_TIME)
        else:
            synchroiteration(roomid_bnovo_to_wubook, roomid_wubook_to_binovo)
            sleep(30)
