from utils.loadenv import bnovo_client, wubook_clients, bnovo_pms_client, DEBUG_RUNNING
from service.wubook import WuBookRoom, WuBookBooking
from service.bnovo import BnovoPMSBooking
import datetime
from itertools import chain
from typing import Union
import logging
from time import sleep

from utils.bnovo_to_wubook import update_wubook_copy, bnovo_to_wubook_new_record
from utils.database import BNOVO_TAG, WUBOOK_TAG
from utils.updates import split_dict, make_updates
from utils.wubook_to_bnovo import update_bnovo_copy, wubook_to_bnovo_new_record


def get_rooms_comparison():
    # составляем словари переназначений комнат
    wubook_rooms = chain(*[c.rooms() for c in wubook_clients])
    bnovo_rooms = bnovo_client.get_roomtypes()

    if DEBUG_RUNNING:
        bnovo_rooms = {k: v for k, v in bnovo_rooms.items() if 'Тестовая' in v['name']}
        wubook_rooms = [room for room in wubook_rooms if 'Тестовая' in room.name]

    tempdict: dict[str, WuBookRoom] = {room.name: room for room in wubook_rooms}
    roomid_bnovo_to_wubook = {}
    roomid_wubook_to_binovo = {}

    for key, room in bnovo_rooms.items():
        wroom = tempdict.get(room['name'])
        if not wroom:
            logging.warning(f'No room in wubook {room["name"]}')
        else:
            roomid_bnovo_to_wubook[room['id']] = wroom
            roomid_bnovo_to_wubook[room['name']] = wroom
            roomid_wubook_to_binovo[wroom.id] = room
    return roomid_bnovo_to_wubook, roomid_wubook_to_binovo


def synchroiteration(roomid_bnovo_to_wubook, roomid_wubook_to_binovo):
    # Собираем брони для обработки, остальные пропустятся
    now = datetime.datetime.now()
    bnovo_bookings: dict[Union[int, str], BnovoPMSBooking] = {
        i.get_id_number(): i for i in bnovo_pms_client.get_bookings(
            departure_from=datetime.datetime.now().date()
        ) if i.departure >= now}
    # Проблемы вубук:
    # - ограничение в 120 записей
    # - кривые фильтры, нет фильтров по выезду
    # Поэтому запросить все актуальные записи непросто,
    # из биново будем стучать по базе, а в вубук плясать от изменений
    wubook_bookings: dict[int, WuBookBooking] = {i.reservation_code: i for i in chain(*[
        c.bookings(
            dfrom=datetime.datetime.now().date() - datetime.timedelta(days=10)
        ) + c.new_bookings()
        for c in wubook_clients])}

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
        room = roomid_wubook_to_binovo.get(book.rooms)
        wubook_to_bnovo_new_record(room, book)

    for book_id, book in bnovo_bookings.items():
        wub_room = roomid_bnovo_to_wubook.get(book.initial_room_type_name)
        bnovo_to_wubook_new_record(wub_room, book)


if __name__ == "__main__":
    # Получаем сопоставления. Для каких номеров нет сопоставлений, пропустим
    roomid_bnovo_to_wubook, roomid_wubook_to_binovo = get_rooms_comparison()

    while 1:
        logging.debug("New iteration start")
        if not DEBUG_RUNNING:
            try:
                synchroiteration(roomid_bnovo_to_wubook, roomid_wubook_to_binovo)
            except Exception as e:
                mes = str(e)
                if "More than 288" in mes:
                    logging.error(f"Синхронизация не получилась, спим 6 мин {mes}")
                    sleep(300)
                else:
                    logging.error(f"Непредвиденная ошибка синхронизации {mes}\n{e.with_traceback()}")
            sleep(180)
        else:
            synchroiteration(roomid_bnovo_to_wubook, roomid_wubook_to_binovo)
            sleep(30)
