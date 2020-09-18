# -*- coding:utf-8 -*-
"""
每天运行 对不符合权限兼容矩阵的用户发出提醒
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

from django.conf import settings
from django.core.management.base import BaseCommand

from audit.models import AuditSysModel, AuditTaskModel, RiskUserModel
from audit.rule_handler import PeriodProxyHandler
from bombus.services.message import EmailMessage
from bombus.services.user_service import UserService

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def get_audit_sys(self):
        """
        获取审计范围
        """
        audit_sys_list = AuditSysModel.objects.all()
        result = {}
        for audit_sys in audit_sys_list:
            result[str(audit_sys.id)] = str(audit_sys.sys_name)
        return result

    def get_user_name(self, user):
        user_name = user
        try:
            ums_info = UserService.query_accountid(user)
            other_user_name = ums_info.get('name')
            return other_user_name or user_name
        except:
            return user_name

    def format_push_content(self, sys_ids):
        result = []
        queryset = AuditSysModel.objects.filter(id__in=sys_ids)
        for qs in queryset:
            sys_link = self._fmt_sys_link(qs)
            if sys_link:
                result.append(sys_link)
        sys_names = '\n'.join(result)
        if sys_names:
            day = datetime.datetime.now().date()
            content = f'### 请注意 ###\n以下业务线存在权限不相容情况, 请在合规平台中查看详情:\n{sys_names}\n日期:{day}'
            return content
        return ''

    def _fmt_sys_link(self, audit_sys):
        sys_name = audit_sys.sys_name
        tasks = AuditTaskModel.get_active_task_by_sys(audit_sys)
        now = datetime.datetime.now()
        links = []
        for task in tasks:
            created_time = task.created_time
            audit_period = task.audit_period
            start_time, end_time = PeriodProxyHandler.time_range(audit_period, created_time)
            if start_time <= now <= end_time:
                links.append(task.review_page_url)
        if links:
            link_url = ';'.join(links)
            return f"{sys_name}【 {link_url} 】"
        return ''

    def handle(self, *args, **options):

        today = datetime.datetime.now().date()
        risk_sys = RiskUserModel.objects.filter(
            record_date=today,
            matrix_risk__not__in=['', None]
        ).distinct('audit_sys')
        risk_sys_ids = []
        for sys in risk_sys:
            risk_sys_ids.append(sys.id)

        push_info = self.format_push_content(risk_sys_ids)
        push_users = settings.AUDIT_USERS
        if push_info and push_users:
            EmailMessage.batch_send_to_persons(push_info, push_users)
