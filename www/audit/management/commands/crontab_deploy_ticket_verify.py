# -*- coding:utf-8 -*-

"""
定时任务: 每天检查前一天的部署单, 是否存在风险
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

from audit.handlers.ticket_handler import DeployTicketHandler
from audit.models import DeployTicketModel
from core.util import time_util

logger = logging.getLogger(__name__)


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
        start_time = time_util.yesterday()
        end_time = time_util.today()
        depts = list(DeployTicketModel.objects.distinct('dept'))
        if options['start_time']:
            start_time = datetime.datetime.strptime(options['start_time'], '%Y-%m-%d')
        if options['end_time']:
            end_time = datetime.datetime.strptime(options['end_time'], '%Y-%m-%d')
        for dept in depts:
            logger.info(f'[TICKET_VERIFY] begin verify deploy ticket for [{dept}]')
            DeployTicketHandler.verify_dept_tickets(dept, start_time, end_time)
            logger.info(f'[TICKET_VERIFY] verify deploy ticket for [{dept}] finished')
