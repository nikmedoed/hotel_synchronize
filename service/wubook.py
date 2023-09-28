import xmlrpc.client
from .wubook_types import *
import datetime
from dataclasses import asdict
import inspect
from utils.cache import Cache
import socket

socket.setdefaulttimeout(30)
cache = Cache(1800)


class WuBook:
    server = xmlrpc.client.Server('https://wired.wubook.net/xrws/', allow_none=True)

    def __init__(self, token, lcode):
        self.token = token
        self.lcode = lcode

    def __response_procc(self, response, cls=None):
        res, response = response

        with open('wubook_req_log.txt', 'a', encoding='utf8') as f:
            current_frame = inspect.currentframe()
            caller_function = current_frame.f_back.f_code.co_name
            f.write(f"{datetime.datetime.now()}\t{self.lcode}\t{res}\t{caller_function}\n")

        if res == 0:
            if type(response) == str:
                return response
            if cls:
                if type(response) == list:
                    return [cls(**r).set_object(self) for r in response]
                return cls(**response.set_object(self))
            return response
        else:
            raise Exception(f"{res}:: {response}")

    @property
    def __get_auth(self):
        return self.token, self.lcode

    def rooms(self) -> list[WuBookRoom]:
        response = self.server.fetch_rooms(*self.__get_auth)
        return self.__response_procc(response, WuBookRoom)

    def room(self, rid, ancillary=0) -> WuBookRoom:
        response = self.server.fetch_single_room(*self.__get_auth, rid, ancillary)
        return self.__response_procc(response, WuBookRoom)

    def remove_room(self, rid):
        response = self.server.del_room(*self.__get_auth, rid)
        return self.__response_procc(response)

    def booking(self, rcode, ancillary=False):
        key = f"{self.lcode}:{rcode}"
        item = cache.get(key)
        if not item:
            response = self.server.fetch_booking(*self.__get_auth, rcode, ancillary)
            item = self.__response_procc(response, WuBookBooking)
            cache.set(key, item)
        return item

    def new_bookings(self, ancillary=0, mark=1):
        response = self.server.fetch_new_bookings(*self.__get_auth, ancillary, mark)
        return self.__response_procc(response, WuBookBooking)

    def bookings(self, dfrom: datetime.date = '', dto: datetime.date = '', oncreated=0, ancillary=0):
        """
        вернуть список бронирований по фильтрам

        :param dfrom: от этой даты
        :param dto: до этой
        :param oncreated: по созданию (1) или по заезду (0)
        :param ancillary: доп ерунда
        """
        if dfrom:
            dfrom = dateformat(dfrom)
        if dto:
            dto = dateformat(dto)
        response = self.server.fetch_bookings(*self.__get_auth, dfrom, dto, oncreated, ancillary)
        return self.__response_procc(response, WuBookBooking)

    def bookings_codes(self, dfrom: datetime.date, dto: datetime.date, oncreated=0):
        """
        вернуть список бронирований по фильтрам

        :param dfrom: от этой даты
        :param dto: до этой
        :param oncreated: по созданию (1) или по заезду (0)
        :param ancillary: доп ерунда
        """
        dfrom = dateformat(dfrom)
        dto = dateformat(dto)
        response = self.server.fetch_bookings_codes(*self.__get_auth, dfrom, dto, oncreated)
        return self.__response_procc(response)

    def cancel_reservation(self, rcode, reason='Синхронизация c BNOVO', send_voucher=0):
        response = self.server.cancel_reservation(*self.__get_auth, rcode, reason, send_voucher)
        return self.__response_procc(response)

    def confirm_reservation(self, rcode, reason='Синхронизация c BNOVO', send_voucher=0):
        response = self.server.confirm_reservation(*self.__get_auth, rcode, reason, send_voucher)
        return self.__response_procc(response)

    def reconfirm_reservation(self, rcode, reason='Синхронизация c BNOVO', send_voucher=0):
        response = self.server.reconfirm_reservation(*self.__get_auth, rcode, reason, send_voucher)
        return self.__response_procc(response)

    def new_reservation(self,
                        dfrom: datetime.date,
                        dto: datetime.date,
                        rooms: list,
                        customer: WuBookCustomer,
                        amount=1,
                        origin='xml', ccard=0,
                        ancillary=0, guests: WuBookGuests = 1,
                        ignore_restrs=1,
                        ignore_avail=1,
                        status=2):
        if dfrom:
            dfrom = dateformat(dfrom)
        if dto:
            dto = dateformat(dto)
        rooms = {str(i): [1, 'nb'] for i in rooms}
        response = self.server.new_reservation(*self.__get_auth, dfrom,
                                               dto, rooms,
                                               {key: value for key, value in asdict(customer).items() if value},
                                               amount,
                                               origin, ccard, ancillary,
                                               asdict(guests),
                                               ignore_restrs, ignore_avail, status)
        return self.__response_procc(response)

    def new_room(self,
                 name,
                 beds,
                 defprice,
                 shortname,
                 defboard='nb',
                 boards: dict = {},
                 rtype=4,
                 min_price='',
                 max_price='',
                 names: dict = '',
                 descriptions: dict = '',
                 woodoo=0,
                 avail=1
                 ):
        """

        :param name:
        :param beds:the occupancy of the rooms (children included)
        :param defprice:
        :param shortname:maximum 4 chars. For the same property, use different shortnames for different rooms
        :param defboard:it can be bb (breakfast), fb (full board), hb (half board), nb (no board) and ai (all inclusive)
        :param boards:optional and only useful for the Online Reception (booking engine). Details follow.
        :param rtype:type of the product (1: Room; 2: Apartment; 3: Bed; 4: Unit; 5: Bungalow; 6: Tent; 7: Villa; 8: Chalet; 9: RV park)
        :param min_price: the minimun price for this room (If passed, must be greater to or equal to 5. Otherwise defalt values is 0)
        :param max_price:the maximun price for this room (If passed, must be greater to or equal to 5. Otherwise defalt values is 0)
        :param names: used to provide a name of the room for each language (booking engine). KV struct, like: {‘en’: ‘Double’, ‘it’: ‘Doppia’}
        :param descriptions:as names
        :param woodoo:if 1, this room will be WooDoo only
        :param avail: ???
        """
        response = self.server.new_room(
            *self.__get_auth, woodoo, name, beds,
            defprice, avail, shortname, defboard,
            names, descriptions,
            boards, rtype,
            # min_price, max_price
        )
        return self.__response_procc(response)

    def new_virtual_room(self,
                         rid,
                         name,
                         beds,
                         defprice,
                         shortname,
                         children,
                         defboard='nb',
                         boards: dict = {},
                         min_price='',
                         max_price='',
                         names: dict = '',
                         descriptions: dict = '',
                         woodoo=0,
                         dec_avail=1
                         ):

        """

        :param name:
        :param beds:the occupancy of the rooms (children included)
        :param defprice:
        :param shortname:maximum 4 chars. For the same property, use different shortnames for different rooms
        :param defboard:it can be bb (breakfast), fb (full board), hb (half board), nb (no board) and ai (all inclusive)
        :param boards:optional and only useful for the Online Reception (booking engine). Details follow.
        :param rtype:type of the product (1: Room; 2: Apartment; 3: Bed; 4: Unit; 5: Bungalow; 6: Tent; 7: Villa; 8: Chalet; 9: RV park)
        :param min_price: the minimun price for this room (If passed, must be greater to or equal to 5. Otherwise defalt values is 0)
        :param max_price:the maximun price for this room (If passed, must be greater to or equal to 5. Otherwise defalt values is 0)
        :param names: used to provide a name of the room for each language (booking engine). KV struct, like: {‘en’: ‘Double’, ‘it’: ‘Doppia’}
        :param descriptions:as names
        :param woodoo:if 1, this room will be WooDoo only
        :param avail: ???
        """

        response = self.server.new_virtual_room(
            *self.__get_auth, rid, woodoo, name, beds, children,
            defprice, shortname, defboard,
            names, descriptions,
            # boards, dec_avail, min_price, max_price
        )
        return self.__response_procc(response)
