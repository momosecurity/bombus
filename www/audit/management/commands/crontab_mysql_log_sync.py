# -*- coding:utf-8 -*-
"""
同步数据库日志数据, 并进行正则规则匹配
"""


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
import logging

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class BlockEvent:
    pass


class MysqlLogSync(object):

    def __init__(self, start_time, end_time):
        pass

    def sync(self):
        pass


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            '--start_time',
            dest='start_time',
            default=None,
            help="start_time eg: 2020-10-19")
        parser.add_argument(
            '--end_time',
            dest='end_time',
            default=None,
            help="end_time eg: 2020-10-20")

    def handle(self, *args, **options):
        start_time = end_time = None
        if options['start_time']:
            start_time = datetime.datetime.strptime(options['start_time'], '%Y-%m-%d')
        if options['end_time']:
            end_time = datetime.datetime.strptime(options['end_time'], '%Y-%m-%d')
        if start_time and end_time and start_time >= end_time:
            raise Exception('start_time must be earlier than end_time, please check !')

        MysqlLogSync(start_time, end_time).sync()
