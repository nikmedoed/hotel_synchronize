from utils.actual_bookings import get_actual_wubook_bookings
from service.wubook_types import WUBOOK_CANCELLED_STATES
from tqdm import tqdm

wubook_bookings = get_actual_wubook_bookings()

for w in tqdm(wubook_bookings.values()):
    if w.status not in WUBOOK_CANCELLED_STATES:
        try:
            w.cancel(reason="Сброс состояния")
            # print(w.reservation_code, w.object_server.lcode )
        except Exception as e:
            print(w.reservation_code, e)
