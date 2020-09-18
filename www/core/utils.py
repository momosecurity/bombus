# coding: utf-8

#  Copyright (C) 2020  momosecurity
#
#  This file is part of Bombus.
#
#  Bombus is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Bombus is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with Bombus.  If not, see <https://www.gnu.org/licenses/>.

import logging
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class OrderedDescEnum(Enum):
    """
    带描述可以排序的枚举

    注意: 下标从0开始

    Usage:
    >>> class Colors(OrderedDescEnum):
    ...    BLUE = 'blue color'
    ...    YELLOW = 'yellow color'
    >>> Colors.BLUE.value
    'blue color'
    >>> sorted([Colors.YELLOW, Colors.BLUE])
    [<Colors.BLUE: 0>, <Colors.YELLOW: 1>]

    """

    def __new__(cls, *args, **kwargs):
        value = len(cls.__members__)
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

    def __init__(self, desc: str):
        self.desc = desc

    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self.value >= other.value
        return NotImplemented

    def __gt__(self, other):
        if self.__class__ is other.__class__:
            return self.value > other.value
        return NotImplemented

    def __le__(self, other):
        if self.__class__ is other.__class__:
            return self.value <= other.value
        return NotImplemented

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented

    @classmethod
    def choices(cls):
        return [item.upper() for item in tuple(cls.__members__)]

    @classmethod
    def items(cls):
        return tuple((item.name, item.desc) for item in cls)

    @classmethod
    def to_seq(cls):
        return [{'name': item.name, 'desc': item.desc} for item in cls]


CEnum = OrderedDescEnum


def get_email_prefix(email):
    if not email:
        return email
    return email.replace('@ca.com', '')


def time2str(time_obj, format='%Y-%m-%d %H:%M'):
    return datetime.strftime(time_obj, format)


def utc2local(dt):
    return dt + timedelta(hours=8)


def date2datetime(date):
    return datetime.combine(date, datetime.min.time())


def split_large_collection(collection, size):
    if not isinstance(collection, (list, tuple)):
        collection = list(collection)

    for i in range(0, len(collection), size):
        yield collection[i:i + size]
