import datetime
import logging
from typing import Union

from utils.loadenv import DEBUG_RUNNING
from utils.database import BNOVO_TAG, WUBOOK_TAG, synchrobase, key, wubook_multiroom_feedback
from service.bnovo_types import BnovoPMSBooking
from service.wubook_types import WuBookRoom, WuBookCustomer, WuBookGuests, \
    WuBookBooking, WUBOOK_CANCELLED_STATES

# waiting for approval reservation (status=2) or a confirmed one (status=1)
STATUS_BNOVO_TO_WUBOOK = {
    1: 2,
    2: 2,
    3: 1,
    4: 1,
    5: 1,
    6: 2
}


def bnovo_to_wubook(book: BnovoPMSBooking, wub_room: WuBookRoom):
    if not wub_room:
        if not DEBUG_RUNNING:
            logging.warning(f"Нет комнаты '{book.initial_room_type_name}' "
                            f"в словаре сопоставлений (в WuBook), пропускаем")
        return
    if book.status_id in {2, 4}:
        return
    departue = book.departure
    if departue.date() <= datetime.date.today():
        return
    book_id = book.id
    arrival = book.arrival
    if arrival < datetime.datetime.now():
        arrival = datetime.datetime.now()
    os = wub_room.object_server
    new_booking = os.new_reservation(
        dfrom=arrival,
        dto=departue,
        rooms={
            wub_room.id: [1, 'nb'],
        },
        customer=WuBookCustomer(
            lname=book.surname,
            fname=book.name,
            email=book.email or 'bnovo_no_return@mail.ru',
            phone=book.phone,
            arrival_hour=arrival.strftime("%H:%M"),
            notes=f"{BNOVO_TAG}: {book_id}\n"
                  f"{book.link_id}\n"
                  f"adults: {book.extra['adults']}, "
                  f"children: {book.extra['children']}"
        ),
        guests=WuBookGuests(book.extra['adults'], book.extra['children']),
        status=STATUS_BNOVO_TO_WUBOOK.get(int(book.status_id), 1)
    )
    logging.info(f"Bnovo to WuBook new copy: {book_id} -> {new_booking} "
                 f"– room: {wub_room.name} :: {book.surname} {book.name} "
                 f"– arrival: {book.arrival}")
    return new_booking


def update_wubook_copy(wubook: WuBookBooking, original: BnovoPMSBooking,
                       rooms_origin_to_copy: dict[Union[int, str], WuBookRoom]):
    # При изменении бронирования вубук его статус становится 5 (отменено).
    # Поле modified_reservations становится равным rcode,
    # was_modified становится равным 1.
    # Т.е. создаются новые записи для изменения.
    rcode = wubook.reservation_code
    try:
        room = rooms_origin_to_copy.get(original.initial_room_type_name)
        if wubook.date_departure and wubook.date_departure < datetime.datetime.now():
            return

        wubook_rooms = wubook.dayprices and {room for room in wubook.dayprices}

        if original.arrival and wubook.date_arrival and (
                (
                        original.arrival.date() >= datetime.datetime.now().date()
                        and
                        original.arrival.date() != wubook.date_arrival.date()
                )
                or
                original.departure.date() != wubook.date_departure.date()
                or
                (room and str(room.id) not in wubook_rooms)
                # т.к. к одной брони вубука может относиться несколько биново,
                # надо проверять по всем номерам, но если поменялась один номер из серии,
                # придётся пересоздавать бронь вубук заново и для других броней биново
        ):
            if wubook.status not in WUBOOK_CANCELLED_STATES:
                wubook.cancel(reason='bnovo data update')
                kk = key(WUBOOK_TAG, rcode)
                if synchrobase.exists(kk):
                    synchrobase.rem(kk)
                if len(wubook_rooms) > 1:
                    wubook_multiroom_feedback.delete(wubook.id)
                logging.info(f"bnovo {original.id} changed wubook {rcode} cancelled")
            if original.status_id != 2:
                bnovo_to_wubook_new_record(room, original)
        elif original.status_id in {3, 4, 5}:
            if wubook.status == 2:
                try:
                    wubook.confirm(reason='bnovo synchronize')
                    logging.info(f"wubook {rcode} confirmed")
                except Exception as e:
                    logging.info(f"wubook {rcode} may already confirmed, err: {e}")
            elif wubook.status in WUBOOK_CANCELLED_STATES:
                wubook.reconfirm(reason='bnovo synchronize')
                logging.info(f"wubook {rcode} reconfirmed")
        elif original.status_id == 2 and wubook.status in {1, 2, 4}:
            wubook.cancel(reason='bnovo synchronize')
            if len(wubook_rooms) > 1:
                wubook_multiroom_feedback.delete(wubook.id)
            logging.info(f"wubook {rcode} cancelled")
    except Exception as e:
        logging.error(f"bnovo {original.id} to wubook {rcode} synchronize error: {e}")


def bnovo_to_wubook_new_record(wub_room: WuBookRoom, book: BnovoPMSBooking):
    try:
        new_booking = bnovo_to_wubook(book, wub_room)
        if new_booking:
            synchrobase.set(key(WUBOOK_TAG, new_booking), book.id_number)
    except Exception as e:
        logging.error(f"Ошибка бронирования wubook :: {BNOVO_TAG}: {book.id}, err: {e}")
