from dataclasses import dataclass, fields, field
from enum import Enum
from typing import Union
import datetime

WUBOOK_DATE_TEMPLATE = "%d/%m/%Y"


def parse_wubook_date(s):
    return datetime.datetime.strptime(s, WUBOOK_DATE_TEMPLATE)


def dateformat(date):
    if type(date) == str:
        return date
    # template = WUBOOK_DATE_TEMMPLATE + " %H:%M"
    if type(date) == datetime.date:
        date = datetime.datetime.combine(date, datetime.time())
    template = WUBOOK_DATE_TEMPLATE
    return date.strftime(template)


class WubookData:

    def set_object(self, object_server):
        self.object_server = object_server
        return self


@dataclass
class WuBookRoom(WubookData):
    name: str
    id: int
    occupancy: int
    men: int
    children: int
    shortname: int
    subroom: int
    board: str
    price: float
    availability: int
    woodoo: int
    rtype: int
    rtype_name: str
    boards: str
    anchorate: int
    dec_avail: int
    min_price: int
    max_price: int

    def __init__(self, **kwargs):
        field_names = {field.name for field in fields(self)}
        for key, value in kwargs.items():
            if key in field_names:
                setattr(self, key, value)


class WuBookStatus(Enum):
    confirmed = 1
    waiting_approval = 2
    refused = 3
    accepted = 4
    cancelled = 5
    cancelled_with_penalty = 6


class WuBookDevice(Enum):
    Not_Detectable = -1
    Unknown_device = 0
    Mobile_phone = 1
    Tablet_computer = 2
    Personal_computer = 3
    iPhone = 4
    iPad = 5
    Android_device = 6
    BlackBerry = 7
    iPod = 8


@dataclass
class WuBookBooking(WubookData):
    """
    https://tdocs.wubook.net/wired/fetch.html

reservation_code

The reservation ID (and at the same time creation timestamp= reservation date)

status

Reservation Status (see below: status)

channel_reservation_code

If originated by an OTA, it contains the OTA ID of this reservation (0 otherwise)

id_channel

If originated by an OTA, that’s the channel type (booking, expedia, …, check get_channels_info())

id_woodoo

If originated by an OTA, that’s the ID of the connected WooDoo Channel

fount

If originated by a Fount Site, it contains the Fount site ID (trivago, tripadv and so on, see fountfield)

modified_reservations

If the reservation is modified, this field is not null (see below: modified_reservations)

was_modified

If was_modified= 1, then status= 5 and you have a modification (see below: modified_reservations)

amount

The reservation amount

currency

The currency code. Three digits (EUR, USD, ..)

booked_rate

Deprecated (see booked_rooms): booked pricing plan: -1= Unknown, 0= Wb Parity or id of the plan

orig_amount

Original Reservation Amount (amount can be modified from the extranet)

amount_reason

If Amount is modified, this field contains the related comment

date_received

Deprecated (see date_received_time)

date_received_time

Reservation Date

date_arrival

Arrival

date_departure

Departure

arrival_hour

boards

Information about boards: WooDoo Online Reception only (see below: boards)

tboard

Information about total amount of all boards (see below: tboard)

status_reason

Eventually, this field contains a reason for the current reservation status

men

Number of adults (when not defined, equal to -1)

children

Number of children

sessionSeed

The eventual sessionSeed tag assigned during the opening of the WooDoo Online Reception

origin_company_name

The origin parameter that can be sent in the new_reservation function

customer_city

customer_country

customer_mail

customer_name

customer_surname

customer_notes

customer_phone

customer_address

customer_language

customer_language_iso

A string following the ISO 639-1 Standard for languages (https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes)

customer_zip

rooms

A string contatining booked rooms IDs, comma separated

roomnight

Roomnights (almost useless)

addons_list

Info about addons (for OTA reservations and WooDoo Online Reception add-ons)

room_opportunities

Number of room addons in the addons_list (WooDoo Online Reception only)

opportunities

Number of generic addons in the addons_list (WooDoo Online Reception only)

dayprices

Per day, per room prices

special_offer

Info about an eventual special offer: name and discount (WooDoo Online Reception only)

rooms_occupancies

Info about the occupancy of each booked room (it can be empty, see below : rooms_occupancies)

discount

Information about an eventual discount (see below: discount)

mandatory_costs

An optional array of Mandatory Costs (only for direct reservations)

payment_gateway_fee

The amount paid by the customer online (as deposit, WooDoo Online Reception only)

forced_price

If true (1), dayprices should be ignored (used for youbook and aliens reservations for example)

booked_rooms

Optional and detailed info about each room/rate with a day granularity (see below: booked_rooms)

ancillary

If you fetch with ancillary= 1 (see below: ancillary)

device

Device used to books (see below: device)

deleted_at

Deprecated (see deleted_at_time)

deleted_at_time

Info about eventual reservation deletion (see below: deleted)

deleted_advance

deleted_from

channel_data

Standarized info for all channels, like split reservations (see below: channel_data)

city_tax

City tax value calculated following the rule set on WooDoo, not included in the amount (WooDoo Online Reception only)


    """
    id_channel: int
    reservation_code: int
    amount: float
    orig_amount: float
    city_tax: float
    amount_reason: str
    id_woodoo: str
    channel_reservation_code: str
    sessionSeed: str
    origin_company_name: str
    fount: str
    status: WuBookStatus
    modified_reservations: list
    was_modified: int
    status_reason: str
    date_received: str
    date_received_time: str
    date_arrival: datetime.datetime
    date_departure: datetime.datetime
    arrival_hour: str
    payment_gateway_fee: str
    men: int
    children: int
    customer_city: str
    customer_country: str
    customer_mail: str
    customer_name: str
    customer_surname: str
    customer_notes: str
    customer_phone: str
    customer_address: str
    customer_zip: str
    customer_language: int
    customer_language_iso: str
    roomnight: int
    rooms: int  # вообще тут уместно STR или список, потому что может быть серия номеров, но не в этой задаче
    room_opportunities: int
    opportunities: int
    cc_info: int
    booked_rate: int
    addons_list: list
    special_offer: str
    device: WuBookDevice
    booked_rooms: dict  # тут какая-то дичь
    channel_data: dict
    rooms_occupancies: list
    boards: dict
    tboard: float
    currency: str
    dayprices: dict[str, list[float]]
    deleted_at: str = None
    deleted_at_time: str = None
    deleted_from: str = None
    deleted_advance: str = None
    discount: dict[str, Union[int, str]] = None

    @property
    def id(self):
        return self.reservation_code

    def __init__(self, **kwargs):
        field_names = {field.name for field in fields(self)}
        for key in field_names:
            setattr(self, key, None)
        for key, value in kwargs.items():
            if key in field_names:
                if key in {'date_arrival', 'date_departure'}:
                    value = parse_wubook_date(value)
                elif key == 'rooms':
                    value = value.split(',')
                    value = int(value[0])
                setattr(self, key, value)

    def cancel(self, reason='Синхронизация c BNOVO', send_voucher=0):
        return self.object_server.cancel_reservation(
            self.reservation_code,
            reason, send_voucher
        )

    def confirm(self, reason='Синхронизация c BNOVO', send_voucher=0):
        return self.object_server.confirm_reservation(
            self.reservation_code,
            reason, send_voucher
        )

    def reconfirm(self, reason='Синхронизация c BNOVO', send_voucher=0):
        return self.object_server.reconfirm_reservation(
            self.reservation_code,
            reason, send_voucher
        )

    def update(self):
        if not self.dayprices:
            all_data = self.object_server.booking(self.reservation_code)
            self.__dict__.update(all_data.__dict__)
        return self

    def __str__(self) -> str:
        keys = ["id", "date_arrival", "date_departure", "customer_name",
                "customer_surname", "customer_phone", "customer_mail"]
        values = []
        for key in keys:
            value = getattr(self, key, "")
            if isinstance(value, datetime.datetime):
                value = value.strftime("%d/%m/%Y")
            values.append(str(value))

        return ", ".join(f"{key}: {value}" for key, value in zip(keys, values))


@dataclass
class WuBookGuests:
    men: int = 1
    children: int = 0


@dataclass
class WuBookCustomer:
    lname: str = ''
    fname: str = ''
    email: str = 'no@mail.ru'
    city: str = ''
    phone: str = ''
    street: str = ''
    country: str = 'RU'
    arrival_hour: str = ''
    notes: str = ''


WUBOOK_CANCELLED_STATES = {3, 5, 6}
