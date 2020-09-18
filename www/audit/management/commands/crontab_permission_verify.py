# -*- coding:utf-8 -*-
"""
每天运行, 检测当前所有审计范围内的权限矩阵、角色离职情况等
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

from audit.models import AuditSysModel
from audit.rule_handler import (JobTransferHandler, LongTimeNoUseHandler,
                                PermissionMatrixHandler, ResignUserHandler)

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def get_audit_sys(self):
        """
        获取审计范围
        """
        audit_sys_list = AuditSysModel.objects.all()
        return audit_sys_list

    def handle(self, *args, **options):
        audit_sys_list = self.get_audit_sys()
        for audit_sys in audit_sys_list:
            logger.info(f'[CRONTAB PERMISSION VERIFY] begin to verify perm of {audit_sys.sys_name}')
            logger.info('###### 权限矩阵校验 STRAT... ######')
            PermissionMatrixHandler(audit_sys.id).validate_sys()
            logger.info('###### 离职信息校验 STRAT... ######')
            ResignUserHandler(audit_sys.id).validate_sys()
            logger.info('###### 长时间未使用 STRAT... ######')
            LongTimeNoUseHandler(audit_sys.id).validate_sys()
            logger.info(f'[CRONTAB PERMISSION VERIFY] perm verified of {audit_sys.sys_name} finished !!!')
