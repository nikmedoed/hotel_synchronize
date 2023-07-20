import requests
import datetime
import json
from .bnovo_types import *
import time
import logging

BNOVO_BASE_URL = "https://api.reservationsteps.ru/v1/api/"
BNOVO_TEST_URL = "https://api.sandbox.reservationsteps.ru/v1/api/"


def body_update(dictionary, key, value):
    if value:
        dictionary[key] = value
    return dictionary


class BnovoAPI:
    _BASE = BNOVO_BASE_URL
    _TOKEN_REJECT_TIME = datetime.timedelta(minutes=59)
    _ADDONS_UPDATE_TIME = datetime.timedelta(hours=12)
    _token = None
    _refresh_time = None

    _account_id = 0
    _username = ""
    _password = ""

    _addons_dict = None
    _addons_update_time = None

    @property
    def __get_token(self):
        return {
            'token': self._token,
            'account_id': self._account_id
        }

    def __init__(self, username, password, account_id, test=False):
        self._username = username
        self._password = password
        self._account_id = account_id
        self._BASE = BNOVO_TEST_URL if test else BNOVO_BASE_URL

    def _setToken(self, token):
        self._token = token
        self._refresh_time = datetime.datetime.now()

    def auth(self):
        params = {
            "username": self._username,
            "password": self._password
        }
        response = requests.post(f"{self._BASE}auth", json=params).json()
        self._setToken(response['token'])

    def _request(self, endpoint: str, params: dict, rtype: RequestType = RequestType.GET, key=None) -> dict:
        if not self._token or datetime.datetime.now() - self._refresh_time > self._TOKEN_REJECT_TIME:
            self.auth()
        params.update(self.__get_token)
        url = f"{self._BASE}{endpoint}"

        if self._refresh_time:
            sleep_time = 1 - (datetime.datetime.now() - self._refresh_time).total_seconds()
            if sleep_time > 0:
                time.sleep(sleep_time)

        for attempt in range(1, 6):
            if rtype == RequestType.POST:
                response = requests.post(url, json=params)
            elif rtype == RequestType.DELETE:
                response = requests.delete(url, json=params)
            else:
                response = requests.get(url, params=params)

            if response.status_code == 429:
                st = 30 * attempt
                logging.warning(f"Bnovo код 429, спим: {st} сек")
                time.sleep(st)
            else:
                response = response.json()
                if key:
                    re = response.get(key)
                    if re == None:
                        raise ValueError(response)
                    response = re
                return response
        raise Exception(f"5 неуспешных попыток запроса, код 429, ограничение на частоту запросов")

    def get_bookings(self,
                     arrival_from: datetime.date = None,
                     arrival_to: datetime.date = None,
                     created_from: datetime.date = None,
                     created_to: datetime.date = None,
                     booking_number: str = None,
                     booking_numbers: list = None,
                     booking_group: str = None,
                     all_accounts: int = 0,
                     not_fetched: int = 0,
                     ) -> list[BnovoBooking]:
        """
Метод API позволяет получить список бронирований.
При запросе списка бронирований можно указать фильтры:
 - по дате заезда - даты начала и конца периода, в который происходит заезд
 - по дате создания бронирования - даты начала и конца периода, в который было создано бронирование
 - по массиву номеров бронирований, по отметке “прочитано”.

        :param arrival_from: Начало периода дат заезда
        :param arrival_to: Конец периода дат заезда
        :param created_from: Начало периода дат создания бронирования
        :param created_to: Конец периода дат создания бронирования
        :param booking_number: Номер бронирования
        :param booking_numbers: Номера бронирований
        :param booking_group: Номер группы
        :param all_accounts: Выбирать бронирования со всех аккаунтов
        :param not_fetched: Если 0, то выбирать бронирования, помеченные как прочитанные
        """
        POINT = "bookings"
        body = {
            "arrival_from": bnovo_date_format(arrival_from),
            "arrival_to": bnovo_date_format(arrival_to),
            "created_from": bnovo_date_format(created_from),
            "created_to": bnovo_date_format(created_to),
            "booking_number": booking_number,
            "booking_numbers": booking_numbers,
            "booking_group": booking_group,
            "all_accounts": all_accounts,
            "not_fetched": not_fetched
        }
        for i in set(body.keys()):
            if not body[i]:
                del body[i]
        response = self._request(POINT, body, key='bookings')
        return [BnovoBooking(**b) for b in response]

    def delete_booking(self, booking_number: str, guest_email: str) -> list[BnovoBooking]:
        """
Метод API позволяет отменить бронирование по его номеру и EMail’у гостя. Возвращает отмененные брони.

        :param booking_number: Номер бронирования, к примеру "X959N_290120"
        :param guest_email: Почта связанная с бронирвоанием
        """
        POINT = "bookings"
        body = {
            "booking_number": booking_number,
            "email": guest_email
        }
        response = self._request(POINT, body, key='deleted_bookings')
        return [BnovoBooking(**b) for b in response]

    def add_booking(self, new_booking: BnovoNewBooking):
        """
Метод API позволяет добавить новое бронирование. В ответ будет возвращен список созданных бронирований и ссылка на их оплату, если передан параметр guarantee_sum. Для печати чеков при онлайн оплате нужно указать параметр fiscal_items. Если бронируется несколько номеров (в том числе одной категории), то создается группа бронирований. Создание бронирования вызывает изменения наличия в модуле бронирования и в менеджере каналов OTA. Есть возможность указать дополнительные услуги для каждого номера в бронировании.

        :param new_booking: описание бронирования
        """
        POINT = "bookings"

        response = self._request(POINT,
                                 {"booking_json": json.dumps(asdict(new_booking))},
                                 key='bookings',
                                 rtype=RequestType.POST
                                 )
        return [BnovoBooking(**b) for b in response]

    def get_roomtypes(self, address_included=0):
        """

        :param address_included: Показать данные местоположения
        """
        POINT = "roomtypes"
        body = {
            'address_included': address_included
        }
        response = self._request(POINT, body, key='roomtypes')
        return response

    def get_plans(self):
        POINT = "plans"
        response = self._request(POINT, {}, key='plans')
        return response

    def get_amenities(self, roomtype_id):
        POINT = "roomtype_amenities"
        response = self._request(POINT, {"roomtype_id": roomtype_id}, key='amenities_data')
        return response

    @property
    def addons(self):
        if self._addons_dict == None or self._addons_update_time - datetime.datetime.now() > self._ADDONS_UPDATE_TIME:
            self.get_addons()
        return self._addons_dict

    def get_addons(self):
        POINT = "additional_services"
        response = self._request(POINT, {}, key='additional_services').values()
        addons = {r['name']: r for r in response}
        for r in response:
            addons[r['id']] = r
            addons[r['name_ru']] = r
        self._addons_dict = addons
        self._addons_update_time = datetime.datetime.now()
        return response

    def create_room(self, body):
        POINT = "roomtypes"
        response = self._request(POINT, body, rtype=RequestType.POST)
        return response
