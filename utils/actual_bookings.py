import datetime
import logging
from itertools import chain
from typing import Union

from service.bnovo_types import BnovoPMSBooking
from service.wubook_types import WuBookBooking, WUBOOK_CANCELLED_STATES
from utils.loadenv import wubook_clients, bnovo_pms_client


def get_actual_wubook_bookings() -> dict[int, WuBookBooking]:
    # Проблемы вубук:
    # - ограничение в 120 записей
    # - кривые фильтры, нет фильтров по выезду
    # Поэтому запросить все актуальные записи непросто,
    # из биново будем стучать по базе, а в вубук плясать от изменений

    now = datetime.datetime.now()
    gap = (now - datetime.timedelta(days=10)).date()
    codes_dto = (now + datetime.timedelta(days=600)).date()
    bookings = {}
    for client in wubook_clients:
        books = {i.reservation_code: i for i in chain(
            client.bookings(dfrom=gap),
            client.new_bookings(),
            # client.bookings(dfrom=now)
        )}
        codes_data = {c['reservation_code']: c for c in client.bookings_codes(dfrom=gap, dto=codes_dto)}
        codes = (set(codes_data.keys()) | set(books.keys()))
        for code in codes:
            item = books.get(code)
            try:
                # дополнительно можно здесь фильтровать по статусу,
                # но так можно скипнуть реальные отмены для дубликатов.
                # или проанализировать возможность создавать фиктивные записи о бронированиях только со статусом.
                # Так можно будет нативно обновлять, не запрашивая данные
                # {'reservation_code': 1689680394, 'status': 5, 'id_channel': 0}
                if not item:
                    item = codes_data.get(code)
                    t = item and item.get('status') in WUBOOK_CANCELLED_STATES
                    item = WuBookBooking(**item) if t else client.booking(code)[0]
            except Exception as e:
                logging.warning(f"wubook: не получилось запросить бронирование {code} "
                                f"будет пропущено в итерации. Ошибка: {e}")
            if item and (not item.date_departure or item.date_departure >= now):
                bookings[code] = item
    return bookings


def count_wubook_cancelled(bookings: [WuBookBooking]):
    return sum([1 for i in bookings if i.status in WUBOOK_CANCELLED_STATES])


def count_bnovo_cancelled(bookings: [BnovoPMSBooking]):
    return sum([1 for i in bookings if i.status_id == 2])


def get_actual_bnovo_bookings() -> dict[Union[int, str], BnovoPMSBooking]:
    now = datetime.datetime.now()
    return {
        i.id_number: i for i in bnovo_pms_client.get_bookings(
            departure_from=now.date()
        ) if i.departure >= now}
