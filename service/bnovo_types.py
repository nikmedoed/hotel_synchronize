from dataclasses import dataclass, asdict, field, fields
from enum import Enum
from typing import Union
import datetime


def bnovo_date_format(date):
    try:
        return date.strftime("%Y-%m-%d")
    except:
        return date


def bnovo_dates(date, a, b=None):
    if not b:
        a, b = 0, a
    for n in range(a, b):
        yield bnovo_date_format(date + datetime.timedelta(days=n))


def parse_bnovo_date(date_string):
    return datetime.datetime.strptime(date_string.split('+')[0], '%Y-%m-%d %H:%M:%S')


class RequestType(Enum):
    POST = 'post'
    DELETE = 'delete'
    GET = 'get'
    FORM = 'form'


@dataclass
class BnovoBooking:
    ota_id: int
    link_id: str
    status_id: int
    roomtype_id: int
    plan_id: int
    parent_room_type_id: int
    number: str
    arrival: datetime.datetime
    departure: datetime.datetime
    name: str
    surname: str
    email: str
    phone: str
    adults: int
    amount: int
    prices: dict[str, int]
    services: dict[str, dict[str, Union[int, str]]]
    extra: dict[str, str]
    extra_array: dict[str, str]
    online_warranty_deadline_date: datetime.datetime
    create_date: datetime.datetime
    update_date: datetime.datetime
    id: int = None
    ota_booking_id: int = None
    account_id: int = None
    comment: str = ""
    birth_date: str = None
    cancellation_fine: str = None
    lang: str = "ru"
    children: int = 0
    booking_guarantee_auto_booking_cancel: int = 0
    promo_code: str = None
    is_fetched: int = 0
    paid: int = 0
    payment_key: str = None
    modified_from: str = None
    modified_to: str = None

    def __init__(self, **kwargs):
        field_names = {field.name for field in fields(self)}
        for key, value in kwargs.items():
            if key in field_names:
                if key in {'arrival', 'departure'}:
                    value = parse_bnovo_date(value)
                setattr(self, key, value)


@dataclass
class BnovoBookingExtra:
    """
Represents an extra booking information

    Board:	Описание питания, предусмотренного по бронированию. Текст неограниченной длины.

    Rates:	Распределение стоимости бронирования по дням или периодам.

    Guests_List:	Список гостей

    Guests_Number:	Кол-во гостей

    Guests_Smoking:	Курящие ли гости

    Guests_Requests:	Пожелания или запросы от гостей

    Loyalty_flags:	Массив маркеров, которые участвуют в программе лояльности, например, Genius в booking.com, членство в ассоциациях Expedia и т.д.

    Loyalty_loyalty_id:	Идентификатор программы лояльности, использованной при бронировании

    Ota_info_Hotel_id:	Идентификатор аккаунта в OTA. Используется в рассылках PMS систем, например в случае, когда пришло бронирование, модификация или отмена по несопоставленному тарифу.

    Ota_info_Rate_name:	Название тарифа в OTA. Используется в рассылках PMS систем, например в случае, когда пришло бронирование, модификация или отмена по несопоставленному тарифу.
    """
    Board: str = None
    Rates: list[str] = None
    Guests_List: list[str] = None
    Guests_Number: int = None
    Guests_Smoking: bool = None
    Guests_Requests: list[str] = None
    Loyalty_flags: list[str] = None
    Loyalty_loyalty_id: str = None
    Ota_info_Hotel_id: str = None
    Ota_info_Rate_name: str = None


@dataclass
class BnovoFiscal:
    """
Информация о содержимом чека при создании бронирования

    name: Название элемента корзины. Должно быть пустым в запросе. При печати чека будет подставлено “<номер бронирования>: Проживание”.

    room_type_id: Идентификатор бронируемой категории номеров.

    quantity_value: Кол-во для данного элемента корзины для указания в чеке (кол-во бронируемых номеров).

    quantity_measure: Единица измерения для указания в чеке по данному элементу корзины. Должно быть “усл.” для проживания.

    price: Стоимость данного элемента корзины (стоимость проживания за весь период в одном номере данной категории).

    tax: Идентификатор НДС. Подробнее в разделе “Контроллер юридических лиц”.

    tax_system: Идентификатор системы налогообложения. Подробнее в разделе “Контроллер юридических лиц”. Может быть значением из списка: 0, 1, 2, 3, 4, 5

    payment_subject_type: Идентификатор признака предмета расчета. Подробнее в разделе “Контроллер юридических лиц”.

    payment_method_type: Идентификатор признака способа расчета. Подробнее в разделе “Контроллер юридических лиц”. Может быть значением из списка: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13

    item_code: Идентификатор элемента корзины (порядковый номер в чеке).
    """
    room_type_id: int
    quantity_value: int
    price: float
    tax: int
    tax_system: int
    payment_subject_type: int
    payment_method_type: int
    item_code: int
    name: str = ""
    quantity_measure: str = "усл."


@dataclass
class BnovoRoomTypeServices:
    """
Дополнительные услуги для каждого номера по каждой дате. Количество должно совпадать, а содержимое может быть пустым.
Используется в виде списка словарей с ключом "services". Пример:
{ "services":[ { "i":1, "c":1, "total_amount":1678, "day_prices":{ "2019-01-29":{ "count":1, "price":1678 } } } ] }, { "services":[ { "i":1, "c":1, "total_amount":1678, "day_prices":{ "2019-01-29":{ "count":1, "price":1678 } } } ] }

    i: Идентификатор доп. услуги.

    c: Кол-во доп. услуг.

    total_amount: Общая стоимость доп. услуг в номере.

    day_prices: Массив цен доп. услуг по дням. Ключ - дата в формате Y-m-d (строка), внутри массив с ключами count и price. Значение ключа count - целое число, значение ключа price - float.
    """
    i: int = None
    c: int = None
    total_amount: float = 0
    day_prices: dict[str, dict[str, int]] = field(default_factory=dict)


@dataclass
class BnovoRoomTypes:
    """
Описание бронируемых комнат

    count: Кол-во бронируемых номеров.

    prices: Массив цен по дням за проживание. Ключ - дата в формате Y-m-d (строка), значение - float.

    room_type_services: Массив с дополнительными услугами для каждого номера, учитывая параметр count. Если count передан 2, то в массиве должно быть два элемента. Если доп. услуг в бронировании нет, то нужно передавать пустой массив для каждого номера, учитывая параметр count

    promo_code: Массив цен с примененным промокодом. В формате: {"new_prices": {Дата в формате Y-m-d: цена (float)}}
    """
    count: int
    prices: dict[str, int]
    room_type_services: list[dict[str, list[BnovoRoomTypeServices]]]
    promo_code: dict[str, dict[str, int]] = None


@dataclass
class BnovoNewBooking:
    """
Описание броней

    plan_id  Идентификатор тарифа, по которому совершается бронирование.

    warranty_type: Тип предоплаты за бронирование. Может быть значением из списка: no - нет онлайн оплаты, onlinepay - онлайн оплата через шлюз оплаты, other - другой тип оплаты.

    guarantee_sum: Сумма предоплаты за бронирование. Используется только вместе с warranty_type = onlinepay. При указании этого параметра, если настроен шлюз оплат, гость будет перенаправлен на онлайн-оплату бронирования. Если шлюз не настроен или вернул ответ, содержащий ошибку, бронирование будет создано, отелю будет отправлено Email уведомление о том, что попытка взять предоплату завершилась ошибкой.

    arrival: Дата заезда. Тип - строка в формате Y-m-d.

    departure: Дата выезда. Тип - строка в формате Y-m-d.

    name: Имя гостя. Строка длиной до 255 символов.

    surname: Фамилия гостя. Строка длиной до 255 символов.

    email: Email гостя. Строка длиной до 255 символов. Должна содержать корректный Email адрес.

    phone: Телефон гостя. Строка длиной до 255 символов.

    lang: Язык гостя для уведомлений. Может быть значением из списка: ru, en, de, es, fi, fr, it, ja, ko, lt, lv, pl, ro, zh

    comment: Комментарий гостя. Текст неограниченной длины.

    promo_code_name: Промокод. Необходимо, чтобы в элементе массива room_types было указано поле promo_code (содержание поля - см. в описании элеметнтов в room_types).

    room_types: Массив, содержащий информацию о бронируемых категориях номеров.

    fiscal_items: Элементы корзины заказа для печати чека. Указывается совместно с параметром guarantee_sum. Поддерживается только оплата проживания.

    extra: Поле для записи дополнительной информации о бронировании. Cтрока в формате JSON неограниченной длины.
    """
    plan_id: int
    arrival: datetime.datetime
    departure: datetime.datetime
    name: str
    surname: str
    email: str
    phone: str
    room_types: dict[str, BnovoRoomTypes]
    fiscal_items: list[BnovoFiscal] = None
    extra: str = ""  # BnovoBookingExtra = None
    warranty_type: str = "no"
    guarantee_sum: float = 0
    lang: str = "ru"
    comment: str = ""
    promo_code_name: str = None

    def __init__(self, **kwargs):
        field_names = {field.name for field in fields(self)}
        for key, value in kwargs.items():
            if key in field_names:
                setattr(self, key, value)


class BnovoStatuses(Enum):
    new = 1
    cancelled = 2
    inhouse = 3
    exited = 4
    checked = 5
    looks = 6


class BnovoPMSobject:
    def set_server(self, server):
        self.server = server
        return self


@dataclass
class BnovoPMSBooking(BnovoPMSobject):
    """
    
agency_commission: Комиссия агентства

agency_id: ID агентства 

agency_name: Название агентства

agency_not_pay_services_commission: Платится ли агентству комиссия с продажи доп. услуг

arrival: Дата и время заезда 2021-07-14 14:00:00+03'

create_date: Дата создания 2021-07-10 14:17:48'

current_room: Название номера

customer_id: ID заказчика 17080222'

departure: Дата и время выезда 2021-07-15 12:00:00+03'

early_check_in: Ранний заезд

email: Эл. почта гостя

extra: Дополнительные данные по бронированию {"adults": 0, "children": 0}

hotel: Информация об отеле

hotel_id: ID отеля 6360'

id: ID бронирования 27412345'

initial_room_type_name: Название категории номера Standard Twin

late_check_out: Поздний выезд

link_id: Код группы бронирований 4AB5C-100721

name: Имя заказчика Иван

float: Код бронирования в Bnovo PMS 4AB5C-100721

payments_total: Сумма платежей 0.00'

phone: Телефон заказчика +7 (902) 345-67-89

plan_name: Название тарифного плана Невозвратный

prices_rooms_total: Стоимость проживания 2500.00'

prices_services_total: Стоимость доп. услуг 800.00'

provided_total: Стоимость оказанных услуг 0.00'

source_icon: Имя файла иконки источника (полный путь https://online.bnovo.ru/public/images/sources/{имя_файла}) channels_bnovobook.png

source_id: ID источника 2'

source_name: Название источника Модуль бронирования

status_id: ID статуса бронирования<br/> 1 - Новое, 2 - Отменено, 3 - Заселен, 4 - Выехал, 5 - Проверено, 6 - На рассмотрении 1'

status_name: Название статуса бронирования<br/> Новое, Отменено, Заселен, Выехал, Проверено, На рассмотрении Новое

supplier_id: ID контрагента

supplier_name: Название контрагента

surname: Фамилия заказчика Иванов

unread: Прочитана бронь или нет

    """
    arrival: datetime.datetime
    create_date: datetime.datetime
    departure: datetime.datetime
    status_id: str
    status_name: str
    agency_commission: float = None
    agency_id: str = None
    agency_name: str = None
    agency_not_pay_services_commission: bool = None
    current_room: str = None
    customer_id: str = None
    early_check_in: bool = None
    email: str = None
    extra: dict[str, int] = None
    hotel: dict = None
    hotel_id: str = None
    id: str = None
    initial_room_type_name: str = None
    late_check_out: bool = None
    link_id: str = None
    name: str = None
    float: str = None
    payments_total: str = None
    phone: str = None
    plan_name: str = None
    prices_rooms_total: str = None
    prices_services_total: str = None
    provided_total: str = None
    source_icon: str = None
    source_id: str = None
    source_name: str = None
    supplier_id: str = None
    supplier_name: str = None
    surname: str = None
    unread: str = None

    @property
    def id_number(self):
        # От возвращаемого ID зависит групировка бронирований.
        # Т.е. мы не смогли заводить брони серией, то считаем,
        # что брони из вубука заводятся отдельными записями.
        # У нас есть только номер модуля (групповой брони),
        # поэтому там где его нет, считаем по обычному id,
        # аналогично, если в группе более одной записи, не смотрим на этот номер.
        # Наши группы с одной записью.
        if self.extra:
            i = self.extra.get('bnovobook_group_main_booking_number')
            group = self.extra.get('pms_group_booking_numbers')
            if i and group and len(group) == 1:
                return i
        return self.id

    def __init__(self, **kwargs):
        field_names = {field.name for field in fields(self)}
        for key, value in kwargs.items():
            if key in field_names:
                if key in {'arrival', 'departure'}:
                    value = parse_bnovo_date(value)
                if key == 'status_id':
                    value = int(value)
                setattr(self, key, value)

    def change_status(self, status: Union[BnovoStatuses, int]):
        return self.server.change_booking_status(
            booking_id=self.id,
            booking_number=self.link_id,
            new_status_id=status.value if type(status) == BnovoStatuses else status
        )

    def __str__(self) -> str:
        keys = ["id", "arrival", "departure", "name",
                "surname", "phone", "email"]
        values = []
        for key in keys:
            value = getattr(self, key, "")
            if isinstance(value, datetime.datetime):
                value = value.strftime("%d/%m/%Y")
            values.append(str(value))

        return ", ".join(f"{key}: {value}" for key, value in zip(keys, values))
