import pandas as pd
from utils.loadenv import bnovo_client, wubook_clients, bnovo_pms_client
from service.wubook import WuBookBooking
import datetime
from itertools import chain
from dataclasses import asdict

bnovo_rooms = bnovo_client.get_roomtypes()
bnovo_rooms =[ v for k, v in bnovo_rooms.items()]
df = pd.DataFrame(bnovo_rooms)
df.T.to_excel('bnovo_rooms.xlsx')

bnovo_addons = bnovo_client.get_addons()
df = pd.DataFrame(bnovo_addons)
df.to_excel('bnovo_addons.xlsx')

bnovo_bookings = bnovo_pms_client.get_bookings(
    departure_from=datetime.datetime.now().date()
)
df = pd.DataFrame(bnovo_bookings)
df.to_excel('bnovo_bookings.xlsx')


date = datetime.datetime.now().date() + datetime.timedelta(days=30)
wubook_bookings: dict[int, WuBookBooking] = {i.reservation_code: i for i in chain(*[
    c.bookings(
        dto=date
    ) + c.new_bookings(mark=0)
    for c in wubook_clients])}
df = pd.DataFrame([asdict(w) for w in wubook_bookings.values()])
df.to_excel('wubook_bookings.xlsx')

bnovo_plans = bnovo_client.get_plans()
pd.DataFrame(bnovo_plans).to_excel('bnovo_plans.xlsx')

bnovo_bookings = bnovo_client.get_bookings(
    arrival_from=datetime.datetime.now().date() - datetime.timedelta(days=10)
)
df = pd.DataFrame(bnovo_bookings)
df.to_excel('bnovo_module_bookings.xlsx')
