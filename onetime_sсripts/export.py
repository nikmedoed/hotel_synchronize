import pandas as pd
from utils.loadenv import bnovo_client, wubook_clients, bnovo_pms_client
import datetime
from itertools import chain
from dataclasses import asdict
from utils.actual_bookings import get_actual_wubook_bookings, get_actual_bnovo_bookings

bnovo_rooms = bnovo_client.get_roomtypes()
bnovo_rooms = [v for k, v in bnovo_rooms.items()]
df = pd.DataFrame(bnovo_rooms)
df.to_excel('bnovo_rooms.xlsx')

bnovo_addons = bnovo_client.get_addons()
df = pd.DataFrame(bnovo_addons)
df.to_excel('bnovo_addons.xlsx')

bnovo_bookings = get_actual_bnovo_bookings().values()
df = pd.DataFrame(bnovo_bookings)
df.to_excel('bnovo_bookings.xlsx')

date = datetime.datetime.now().date() + datetime.timedelta(days=30)
wubook_bookings = get_actual_wubook_bookings()
df = pd.DataFrame([asdict(w) for w in wubook_bookings.values()])
df.to_excel('wubook_bookings.xlsx')

bnovo_plans = bnovo_client.get_plans()
pd.DataFrame(bnovo_plans).to_excel('bnovo_plans.xlsx')

bnovo_bookings = bnovo_client.get_bookings(
    arrival_from=datetime.datetime.now().date() - datetime.timedelta(days=10)
)
df = pd.DataFrame(bnovo_bookings)
df.to_excel('bnovo_module_bookings.xlsx')

wubook_rooms = chain(*[c.rooms() for c in wubook_clients])
df = pd.DataFrame(wubook_rooms)
df.to_excel('wubook_rooms.xlsx')
