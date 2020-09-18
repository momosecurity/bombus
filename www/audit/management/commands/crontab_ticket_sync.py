# coding=utf-8
"""
上线单数据同步

python manage.py crontab_ticket_sync --sync                           # 同步前一天数据
python manage.py crontab_ticket_sync --update                         # 更新流程未结束工单
python manage.py crontab_ticket_sync --whole --start_time 2020-05-20  # 同步全量数据

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

import logging

from django.core.management.base import BaseCommand

from bombus.libs.ticket_service import OnlineTicketService, TicketService
from core.util import time_util

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    dept_map = OnlineTicketService.dept_map
    BATCH_SIZE = 5
    time_range = {'months': 6}
    unfinished_status = ['in_progress', 'ready']

    def add_arguments(self, parser):
        parser.add_argument(
            '--sync',
            dest='sync',
            action='store_true',
            default=False,
            help="sync lastday info")
        parser.add_argument(
            '--update',
            dest='update',
            action='store_true',
            default=False,
            help="update ticket status")
        parser.add_argument('--whole',
            dest='whole',
            action='store_true',
            default=False,
            help="sync whole data")
        parser.add_argument(
            '--start_time',
            dest='start_time',
            default=None,
            help="start_time eg: 2020-10-19")

    def handle(self, *args, **options):
        if options['update']:
            self.update_unfinished_data()
        elif options['sync']:
            self.sync_lastest_info()
        elif options['whole']:
            start_date = time_util.str2time(options['start_time'], '%Y-%m-%d')
            self.sync_whole_info(start_date)

    def sync_whole_info(self, start_date):
        pass

    def sync_lastest_info(self):
        pass

    def update_unfinished_data(self):
        pass
