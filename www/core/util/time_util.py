# -*- coding:utf-8 -*-

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

import datetime

from dateutil.relativedelta import relativedelta

DT_FMT_001 = '%Y-%m-%d %H:%M:%S'
DT_FMT_002 = '%Y%m%d'
DT_FMT_003 = '%Y-%m-%d'
DT_FMT_004 = '%Y-%m-%dT%H:%M:%S+08:00'


def time2str(time=None, fmt=DT_FMT_001):
    if not time:
        time = datetime.datetime.now()
    return datetime.datetime.strftime(time, fmt)


def str2time(time_sr, fmt=DT_FMT_001):
    return datetime.datetime.strptime(time_sr, fmt)


def dt2stamp(dt: (datetime.date, datetime.datetime), wrapper=None):
    assert isinstance(dt, datetime.date), 'wrong dt type, only accept (datetime.date | datetime.datetime)'

    if type(dt) is datetime.date:
        dt = datetime.datetime.strptime(str(dt), DT_FMT_003)
    ts = dt.timestamp()
    if wrapper and callable(wrapper):
        ts = wrapper(ts)
    return ts


def today():
    today_date = datetime.date.today()
    return datetime.datetime.combine(today_date, datetime.time.min)


def yesterday():
    return today() - datetime.timedelta(days=1)


def date2datetime(date):
    return datetime.datetime.combine(date, datetime.datetime.min.time())


def time_delta(base_time=None, forward='ago', **kwargs):
    """
    时间点
    params base_time: 时间基点
    params forward: ago | later
    """
    base_time = base_time or datetime.datetime.now()
    if forward == 'ago':
        return base_time - relativedelta(**kwargs)
    return base_time + relativedelta(**kwargs)


def local2utc(local_time):
    return local_time - datetime.timedelta(hours=8)


def utc2local(utc_time):
    return utc_time + datetime.timedelta(hours=8)


def get_extra_time(dt, step=0, rounding_level="m"):
    """
    取整分钟、小时、天的时间
    """
    if not dt:
        return dt

    td = None
    ret_dt = dt
    if rounding_level == "d":
        td = datetime.timedelta(days=-step,
                                seconds=dt.second,
                                microseconds=dt.microsecond,
                                milliseconds=0,
                                minutes=dt.minute, hours=dt.hour, weeks=0)
    elif rounding_level == "h":
        td = datetime.timedelta(days=0,
                                seconds=dt.second,
                                microseconds=dt.microsecond,
                                milliseconds=0,
                                minutes=dt.minute, hours=-step, weeks=0)
    elif rounding_level == "m":
        td = datetime.timedelta(days=0,
                                seconds=dt.second,
                                microseconds=dt.microsecond,
                                milliseconds=0,
                                minutes=-step, hours=0, weeks=0)
    elif rounding_level == "s":
        td = datetime.timedelta(days=0,
                                seconds=-step,
                                microseconds=dt.microsecond,
                                milliseconds=0, minutes=0, hours=0, weeks=0)

    if td:
        ret_dt = dt - td
    return ret_dt
