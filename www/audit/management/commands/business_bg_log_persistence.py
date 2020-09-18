# -*- coding:utf-8 -*-
"""
    合规数据入库
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

import json
import logging
import time
from datetime import datetime

from django.core.management.base import BaseCommand
from mongoengine.queryset import DoesNotExist

from audit.models import (BgAccessLogModel, EmployeePositionChangeDataModel,
                          RolePermissionData, RolePermissionModifyLogModel,
                          UserAccountDataModel, UserRoleDataModel,
                          UserRoleModifyLogModel)
from audit.utils import RedisDataProvider
from core.util import time_util

logger = logging.getLogger(__name__)


def handle_bg_access_log(data: dict):
    op_ts = data.pop('op_ts')
    data['access_dt'] = datetime.fromtimestamp(op_ts)
    data['params'] = json.loads(data['params'])
    BgAccessLogModel(**data).save()


def handle_user_role_modify_log(data: dict):
    modify_ts = data.pop('modify_ts')
    data['modify_dt'] = datetime.fromtimestamp(modify_ts)
    UserRoleModifyLogModel(**data).save()


def handle_role_permission_modify_log(data: dict):
    modify_ts = data.pop('modify_ts')
    data['modify_dt'] = datetime.fromtimestamp(modify_ts)
    RolePermissionModifyLogModel(**data).save()


def user2accountid(bg_name, user):
    return UserAccountDataModel.get_accountid_by_user(bg_name, user) or None


def get_created_time(bg_name, user):
    """
    获取用户在对应后台的创建时间
    """
    queryset = UserRoleDataModel.objects.filter(user=user, bg_name=bg_name)
    create_dt = queryset.filter(create_dt__ne=None).order_by('create_dt').values_list('create_dt').first()
    if create_dt:
        return create_dt
    record_date = queryset.order_by('record_date').values_list('record_date').first()
    if record_date:
        return time_util.date2datetime(record_date)
    return time_util.today()


def handle_user_role_data(data: dict):
    user_details = data['user_details']
    bg_name = data['bg_name']
    role = data['role']

    record_date = datetime.strptime(data['date'], '%Y-%m-%d').date()

    for detail in user_details:
        user = detail['user']
        create_ts = detail.get('create_ts')
        msg = {
            'bg_name': bg_name,
            'record_date': record_date,
            'role': role,
            'user': user,
        }
        if create_ts:
            msg['create_dt'] = datetime.fromtimestamp(create_ts)
        else:
            msg['create_dt'] = get_created_time(bg_name, user)

        UserRoleDataModel(**msg).save()


def handle_role_permission_data(data: dict):
    permission_details = data['permission_details']
    bg_name = data['bg_name']
    role = data['role']
    record_date = datetime.strptime(data['date'], '%Y-%m-%d').date()

    for detail in permission_details:
        perm_name = detail['perm_name']
        create_ts = detail.get('create_ts')

        msg = {
            'bg_name': bg_name,
            'record_date': record_date,
            'role': role,
            'permission': perm_name,
        }
        if create_ts:
            msg['create_dt'] = datetime.fromtimestamp(create_ts)

        RolePermissionData(**msg).save()


def handle_employee_position_change_data(data: dict):
    name_map = {
        'EMPLID': 'employee_id',
        'HPS_ACCOUNT_ID': 'accountid',
        'NAME': 'name',
        'HPS_TITLE_BEF': 'title_before',
        'HPS_TITLE_AFT': 'title_after',
        'HPS_DPNM_BEF': 'department_before',
        'HPS_DPNM_AFT': 'department_after',
        'ACTION': 'action'
    }
    timestamp = data.pop('MODIFT_TS')
    new_data = {
        'modify_dt': datetime.fromtimestamp(timestamp),
    }
    for old_key, new_key in name_map.items():
        new_data[new_key] = data.get(old_key) or ''
    EmployeePositionChangeDataModel(**new_data).save()


def handle_user_account_data(data: dict):
    data.pop('date', '')
    today = datetime.now().date()
    try:
        instance = UserAccountDataModel.objects.get(bg_name=data['bg_name'], user_id=data['user_id'])
        instance.accountid = data['accountid']
        instance.update_date = today
        instance.save()
    except DoesNotExist as e:
        instance = UserAccountDataModel(**data)
        instance.create_date = today
        instance.update_date = today
        instance.save()
    except Exception as e:
        logger.exception('handle user account error')


class Command(BaseCommand):
    type_model_dict = {
        'BgAccessLog': handle_bg_access_log,
        'UserRoleModifyLog': handle_user_role_modify_log,
        'RolePermissionModifyLog': handle_role_permission_modify_log,
        'UserRoleData': handle_user_role_data,
        'RolePermissionData': handle_role_permission_data,
        'EmployeePositionChangeData': handle_employee_position_change_data,
        'UserAccountData': handle_user_account_data
    }

    def handle(self, *args, **options):
        provider = RedisDataProvider()

        while True:
            try:
                log_str = provider.get_log()
            except Exception:
                logger.exception(f'get {provider.business_type} log fail.')
                time.sleep(0.1)
                continue

            handle_success = False
            err = None
            for _ in range(2):
                try:
                    self.process_log(log_str)
                    handle_success = True
                    break
                except Exception as e:
                    err = e
            if not handle_success:
                logger.exception(f'process log |:{log_str}:| fail', exc_info=err)

            try:
                provider.ack()
            except Exception:
                logger.exception(f'ack {provider.business_type} log |:{log_str}:| fail')

    def process_log(self, log_str, retry_count=2):
        err = None
        for _ in range(retry_count):
            try:
                log_dict = json.loads(log_str)
                data_type = log_dict['data_type']
                data = log_dict['data']

                handle_func = self.type_model_dict.get(data_type)
                handle_func(data)
                return
            except Exception as e:
                err = e
        if err:
            raise err
