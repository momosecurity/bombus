# -*- coding:utf-8 -*-
"""
每天运行, 检测当前所有任务配置, 如满足规则, 则生成审计任务
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

from audit.models import AuditTaskModel, TaskManagerModel
from audit.rule_handler import HalfYearHandler, MonthHandler, QuarterHandler
from bombus.libs.enums import (AuditPeriodEnum, OnOfflineStatusEnum,
                               TaskStatusEnum)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    periodHandlerMap = {
        AuditPeriodEnum.QUARTER.name: QuarterHandler,
        AuditPeriodEnum.HALFYEAR.name: HalfYearHandler,
        AuditPeriodEnum.MONTH.name: MonthHandler,
    }

    def get_all_task_config(self):
        task_configs = TaskManagerModel.objects.filter(status=OnOfflineStatusEnum.ONLINE.name).all()
        return task_configs

    def gen_task(self, cnf, handler):
        period = handler.tag()
        try:
            instance = AuditTaskModel.objects.get(
                task_manager=cnf.id,
                period=period
            )
            return instance.id
        except:
            instance = AuditTaskModel(
                created_time=datetime.datetime.now(),
                period=period,
                status=TaskStatusEnum.NOT_STARTED.name,
                task_manager=cnf.id
            )
            instance.save()
            logger.info('[CRONTAB_TASK_GEN] gen new_task[%s-%s]' % (cnf.name, period))
            return instance.id

    def handle(self, *args, **options):
        task_configs = self.get_all_task_config()
        for cnf in task_configs:
            audit_period = cnf.rule_group.audit_period
            handler = self.periodHandlerMap.get(audit_period)()
            self.gen_task(cnf, handler)
