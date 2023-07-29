import datetime
import logging

from utils.loadenv import bnovo_client, DEBUG_RUNNING
from utils.database import WUBOOK_TAG, synchrobase, key, BNOVO_TAG
from utils.bnovo_to_wubook import update_wubook_copy
from service.bnovo_types import BnovoRoomTypeServices, BnovoRoomTypes, \
    bnovo_date_format, bnovo_dates, BnovoNewBooking, BnovoPMSBooking, BnovoStatuses
from service.wubook_types import WuBookBooking, WUBOOK_CANCELLED_STATES

# 1 - Новое, 2 - Отменено, 3 - Заселен, 4 - Выехал, 5 - Проверено, 6 - На рассмотрении
STATUS_WUBOOK_TO_BNOVO = {
    1: 5,
    2: 1,
    3: 2,
    4: 5,
    5: 2,
    6: 2,
}


def wubook_to_bnovo(book: WuBookBooking, rooms: dict[str, dict]):
    # book.arrival_hour не куда указать /
    # А оно ещё и не всегда, иногда просто --
    # Если час заезда меньше, чем 15:00 - в биново ответ на ранний заезд 1
    if book.status in WUBOOK_CANCELLED_STATES:
        # 1: confirmed
        # 2: waiting for approval (WooDoo Online Reception only)
        # 3: refused (WooDoo Online Reception only)
        # 4: accepted (WooDoo Online Reception only)
        # 5: cancelled
        # 6: (probably not used anymore): cancelled with penalty
        return
    if not rooms:
        return
    for k, ro in rooms.items():
        if not ro:
            if not DEBUG_RUNNING:
                logging.warning(f"Нет комнаты wub_id '{k}' "
                                f"в словаре сопоставлений (в Bnovo), пропускаем")
            return
    arrival = book.date_arrival
    departure = book.date_departure
    if departure.date() <= datetime.date.today():
        return
    if arrival < datetime.datetime.now():
        arrival = datetime.datetime.now()
    date_diff = (departure - arrival).days
    if date_diff == 0:
        return
    book_id = book.reservation_code

    # Сервисы будут привязаны к одной комнате и размазаны на несколько дней
    addons_info = []
    services = []
    bnovo_addons = bnovo_client.addons
    for add in book.addons_list:
        name = add['name']
        price = add['price']
        per = add['perday']
        quant = add['number']
        addon = bnovo_addons.get(name)
        text = f"- {quant} {name}, сум {price}, ежедневно: {'Да' if per else 'Нет'}"
        if not addon:
            logging.warning(f"Не найдено сопоставление для дополнительной услуги {name}")
            text += " - нет сопоставления"
        else:
            ldp = date_diff
            if per:
                dayprice = price / ldp
                day_prices = {date: {"count": quant, "price": dayprice} for date in bnovo_dates(arrival, 1, ldp + 1)}
            else:
                ldp = min(quant, ldp)
                if addon['max_quantity_enabled']:
                    ldp = min(addon['max_quantity'], ldp)
                dayprice = price / ldp
                day_prices = {date: {"count": 1, "price": dayprice} for date in bnovo_dates(arrival, ldp)}
            services.append(BnovoRoomTypeServices(
                i=addon['id'],
                c=quant,
                total_amount=price,
                day_prices=day_prices
            ))
        addons_info.append(text)
    addons_info = '\n'.join(addons_info)
    if addons_info:
        addons_info = f"\n\nДополнительные услуги:\n{addons_info}"

    room_types = {}
    for wubook_room_id, dayprices in book.dayprices.items():
        dayprices = dayprices[-date_diff:]
        room_id = rooms[wubook_room_id]['id']

        room_types[room_id] = BnovoRoomTypes(
            count=1,
            prices={bnovo_date_format(arrival + datetime.timedelta(days=n)): i for n, i in
                    enumerate(dayprices)},
            room_type_services=[{"services": []}]  # количество services == count
        )
    room_types[next(iter(room_types))].room_type_services[0]["services"] = services

    extra = ""
    new = BnovoNewBooking(
        plan_id=153650,  # 157122, # Это id тарифа, решили использовать основной
        warranty_type='other',
        guarantee_sum=book.payment_gateway_fee or 0,
        arrival=bnovo_date_format(arrival),
        departure=bnovo_date_format(departure),
        name=book.customer_name,
        surname=book.customer_surname,
        email=book.customer_mail,
        phone=book.customer_phone,
        lang=book.customer_language_iso,
        comment=(f"{WUBOOK_TAG}: {book_id}\n"
                 f"Заезд в {book.arrival_hour}\n"
                 f"Комментарий гостя:\n{book.customer_notes}"
                 f"{addons_info}"),
        room_types=room_types,
        extra=extra
    )
    new_bookings = bnovo_client.add_booking(new)
    rnames = [room.get('name') for room in rooms.values()]
    logging.info(
        f"WuBook to Bnovo new copy: {book_id} -> {[n.number for n in new_bookings]} "
        f"– rooms: {rnames}, {book.customer_surname} {book.customer_name} "
        f"arr {book.date_arrival}")
    return new_bookings


def update_bnovo_copy(bnovo: BnovoPMSBooking, original: WuBookBooking, rooms_bnovo_to_wub: dict):
    try:
        if original.status in WUBOOK_CANCELLED_STATES and bnovo.status_id != 2:
            # Статус мог изменитьcя на отменено и всё,
            # его переносим в копию, остальное переносим из копии
            # будет создана вторая запись
            # Могли измениться даты, Мог измениться номер,
            # Во всех случаях старое бронирование отменяется
            # Создаётся новое бронирование
            bnovo.change_status(BnovoStatuses.cancelled)
            logging.info(f"wubook {original.reservation_code} -> bnovo {bnovo.id} cancelled")
        else:
            update_wubook_copy(original, bnovo, rooms_bnovo_to_wub)
    except Exception as e:
        logging.error(f"wubook {original.reservation_code} -> bnovo {bnovo.id} synchronize error: {e}")


def wubook_to_bnovo_new_record(rooms: dict[str, dict], book: WuBookBooking):
    book_id = book.reservation_code
    try:
        new_bookings = wubook_to_bnovo(book, rooms)
        if new_bookings:
            for n in new_bookings:
                # В базу сохраняем "обратную связь" через ID, чтобы находить оригинал
                synchrobase.set(key(BNOVO_TAG, n.number), book_id)
    except Exception as e:
        err = e.args[0].get('errors')
        if err and type(err) == list:
            rnames = [room.get('name') for room in rooms.values()]
            if err[0].get('type') == 'isAvailable':
                book.cancel(reason="Извините, даты уже заняты", send_voucher=1)
                logging.warning(f"wubook {book_id} cancelled :: "
                                f"в биново заняты даты {book.date_arrival} {book.date_departure} "
                                f"rooms: {rnames}")
            mes = err[0].get('message')
            if mes:
                e = f"{mes}, wubook: {book}, rooms: {rnames}"
        logging.error(f"Ошибка бронирования bnovo :: {WUBOOK_TAG}: {book_id}, err: {e}")
