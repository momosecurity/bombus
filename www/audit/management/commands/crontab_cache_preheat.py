# -*- coding:utf-8 -*-

"""
缓存预热
缓存:
    1. 审计任务 用户预加载  python manage.py crontab_cache_preheat --c 2       --- gevent并发2, 默认5个
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

from gevent import monkey; monkey.patch_socket()

import logging

from django.core.management.base import BaseCommand
from gevent import pool

from audit.caviews import AppUserReview, SysDbReview
from audit.models import AuditTaskModel
from bombus.libs.enums import TaskStatusEnum

logger = logging.getLogger(__name__)


class MockRequest:
    def __init__(self, task_id):
        self.task_id = str(task_id)

    @property
    def GET(self):
        return {'task_id': self.task_id}


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            '--c',
            dest='concurrency',
            default=None,
            help="concurrency count")

    def request_app_user(self, task_id):
        """ 模拟请求APP user """
        mock_req = MockRequest(task_id)
        AppUserReview().get(mock_req)

    def request_sys_db_user(self, task_id):
        """ 模拟请求SYS_DB user """
        mock_req = MockRequest(task_id)
        SysDbReview().get(mock_req)

    def log_preheat(self, task):
        title = task.title
        logger.info(f'{title} 用户日志预热开始...')
        self.request_app_user(task.id)
        self.request_sys_db_user(task.id)
        logger.info(f'{title} 用户日志预热结束...')

    def user_request_preheat(self):
        """ 用户请求预热 """
        logger.info("[TASK LOG] cache preheat start...")
        un_finished_tasks = AuditTaskModel.objects.filter(status__ne=TaskStatusEnum.FINISHED.name)
        gevent_pool = pool.Pool(size=self.concurrency_count)

        for task in un_finished_tasks:
            gevent_pool.spawn(self.log_preheat, task)

        gevent_pool.join(raise_error=True)
        logger.info("[TASK LOG] cache preheat finished")

    def handle(self, *args, **options):
        self.concurrency_count = int(options['concurrency'] or 5)
        self.user_request_preheat()
