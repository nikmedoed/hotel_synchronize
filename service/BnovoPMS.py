import requests
import datetime
import inspect

from .bnovo_types import *


def date_format(date: datetime.date):
    if not date or type(date) != datetime.date:
        return date
    return date.strftime("%d.%m.%Y")


def body_update(dictionary, key, value):
    if value:
        dictionary[key] = value
    return dictionary

# Можно добиться, чтобы список параметров сохранялся в классе при инициализации
# и получить body для функции было проще и быстрее, но лень
# Или в декоратор это превратить и параметры при создании обсчитывать
def get_body(func,loc):
    parameters = set(inspect.signature(func).parameters)- {'self'}
    body = {name: value for name, value in loc.items() if name in parameters}
    return body


class BnovoPMSapi:
    _BASE = 'https://online.bnovo.ru'
    _TOKEN_REJECT_TIME = datetime.timedelta(minutes=59)
    _session = None
    _refresh_time = None

    _username = ""
    _password = ""

    def __init__(self, username, password):
        self._username = username
        self._password = password
        self._session = requests.session()
        self._session.headers['Accept'] = 'application/json'

    def auth(self):
        params = {
            "username": self._username,
            "password": self._password
        }
        res = self._session.post(f"{self._BASE}/", json=params).json()
        err = res.get('flash_error')
        if err:
            raise Exception(err)
        return res

    def _request(self, endpoint: str, params: dict,
                 rtype: RequestType = RequestType.GET, key=None
                 ) -> dict:
        if not self._refresh_time or datetime.datetime.now() - self._refresh_time > self._TOKEN_REJECT_TIME:
            self.auth()
        self._refresh_time = datetime.datetime.now()

        url = f"{self._BASE}{endpoint}"
        if rtype == RequestType.POST:
            response = self._session.post(url, json=params)
        elif rtype == RequestType.DELETE:
            response = self._session.delete(url, json=params)
        elif rtype == RequestType.FORM:
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'x-requested-with': 'XMLHttpRequest'
            }
            response = self._session.post(url, data=params, headers=headers)
            # Нормально бы обработать, но пока нужно только для смены статуса, а там пустота
            return response.text
        else:
            response = self._session.get(url, params=params)
        response = response.json()
        if key:
            re = response.get(key)
            if re == None:
                raise ValueError(response)
            response = re
        return response

    def get_bookings(self,
                     create_from: datetime.date = None,
                     create_to: datetime.date = None,
                     arrival_from: datetime.date = None,
                     arrival_to: datetime.date = None,
                     departure_from: datetime.date = None,
                     departure_to: datetime.date = None,
                     cancellation_from: datetime.date = None,
                     cancellation_to: datetime.date = None,
                     advanced_search: int = 2,
                     name: str = None,
                     surname: str = None,
                     phone: str = None,
                     email: str = None,
                     sources: list[str] = None,
                     status_ids: list[int] = None,
                     discount_reason_ids: list[int] = None,
                     cancel_reason_ids: list[int] = None,
                     tags_ids: list[int] = None,
                     marketing_option_ids: list[int] = None,
                     roomtypes: str = None,
                     c: int = 100,
                     page: int = 1,
                     order_by: str = "arrival_date.asc"
                     ) -> list[BnovoPMSBooking]:
        """
    Метод API позволяет получить бронирования по различным фильтрам.
        
        :param create_from: Начало периода дат создания бронирования (d.m.Y)
        :param create_to: Конец периода дат создания бронирования (d.m.Y)
        :param arrival_from: Начало периода дат заезда (d.m.Y)
        :param arrival_to: Конец периода дат заезда (d.m.Y)
        :param departure_from: Начало периода дат выезда (d.m.Y)
        :param departure_to: Конец периода дат выезда (d.m.Y)
        :param cancellation_from: Начало периода дат отмены (d.m.Y)
        :param cancellation_to: Конец периода дат отмены (d.m.Y)
        :param advanced_search *: Версия расширенного поиска (1 - старая, 2 - новая)
        :param name: Имя заказчика или гостя
        :param surname: Фамилия заказчика или гостя
        :param phone: Номер телефона заказчика или гостя
        :param email: Эл. почта заказчика или гостя
        :param sources: Источники бронирования через запятую. source_0 - Прямое, source_{id} - ID канала, agency_{id} - ID агентства, supplier_{id} - ID компании"
        :param status_ids: ID статусов бронирования через запятую:  1 - Новое, 2 - Отменено, 3 - Заселен, 4 - Выехал, 5 - Проверено, 6 - На рассмотрении"
        :param discount_reason_ids: ID причин скидки
        :param cancel_reason_ids: ID причин отмены
        :param tags_ids: ID тегов гостей
        :param marketing_option_ids: ID значений маркетинговых полей "Откуда вы о нас узнали" и "Способ бронирования"
        :param roomtypes: ID категорий номеров
        :param c: Кол-во элементов на странице (по-умолчанию 10, максимум 100)
        :param page: Текущая страница
        :param order_by: Поле для сортировки и порядок: create_date.asc - По дате создания по возрастанию (сначала идут старые брони) create_date.desc - По дате создания по убыванию (сначала идут новые брони) arrival_date.asc - По дате заезда по возрастанию arrival_date.desc - По дате заезда по убыванию departure_date.asc - По дате выезда по возрастанию departure_date.desc - По дате выезда по убыванию
        """
        body =get_body(self.get_bookings, locals())
        POINT = "/dashboard"

        for i in set(body.keys()):
            v = body[i]
            if not v:
                del body[i]
            elif type(v) == datetime.date:
                body[i] = date_format(v)
        result = []
        while body['page']:
            response = self._request(POINT, body)
            body['page'] = response['pages'].get('next_page')
            re = response.get('bookings')
            if re == None:
                raise ValueError(response)
            result.extend(re)
        return [BnovoPMSBooking(**b).set_server(self) for b in result]



    def get_rooms(self, with_rooms=0):
        body =get_body(self.get_rooms, locals())
        POINT = "/roomTypes/get"
        response = self._request(POINT, body)
        return response

    def change_booking_status(self,
                              booking_id,
                              booking_number,
                              new_status_id,
                              cancel_reason_id=0,
                              concierge_checkout=0,
                              is_checkin=0
                              ):
        body =get_body(self.change_booking_status, locals())
        POINT = "/booking/change_booking_status"
        response = self._request(POINT, body, rtype=RequestType.FORM)
        return response
