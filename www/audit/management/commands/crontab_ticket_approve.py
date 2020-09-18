# -*- coding:utf-8 -*-
"""
同步工单审批关闭记录

python manage.py crontab_ticket_approve --start_date 20200601
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

from audit.models import TicketApproveModel
from core.util import time_util

logger = logging.getLogger(__name__)


class TicketApproveRecordSync:

    def __init__(self, start_date=None, end_date=None):
        self.end_date = end_date or time_util.today()
        self.start_date = start_date or time_util.time_delta(self.end_date, days=1)

    def sync(self):
        pass


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            '--start_date',
            dest='start_date',
            default=None,
            help="开始日期 eg: 20201019")
        parser.add_argument(
            '--end_date',
            dest='end_date',
            default=None,
            help="结束日期 eg: 20201020")

    def handle(self, *args, **options):
        start_date = end_date = None
        if options['start_date']:
            start_date = datetime.datetime.strptime(options['start_date'], time_util.DT_FMT_002)
        if options['end_date']:
            end_date = datetime.datetime.strptime(options['end_date'], time_util.DT_FMT_002)
        if start_date and end_date and start_date >= end_date:
            raise Exception('start_date must be earlier than end_date, please check !')

        TicketApproveRecordSync(start_date, end_date).sync()
