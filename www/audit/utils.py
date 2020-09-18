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

import ipaddress
import json
import logging
import os
import socket
import time
from datetime import datetime

from core import get_redis_client

logger = logging.getLogger(__name__)

_left_dt = datetime.strptime('2011-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')
_right_dt = datetime.strptime('2030-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')


def check_timestamp(field, value, error):
    try:
        assert _left_dt < datetime.fromtimestamp(value) < _right_dt
    except Exception:
        error(field, "invalid")


def check_ip(field, value, error):
    if value == '':
        return
    try:
        ipaddress.ip_address(value)
    except Exception:
        error(field, "invalid")


def check_date_str(field, value, error):
    try:
        datetime.strptime(value, '%Y-%m-%d')
    except Exception:
        error(field, 'invalid format')


accountid_rule = dict(type='string', required=True, regex=r'^[1-9]\d{4,14}$')
normal_account_rule = dict(type='string', minlength=1, required=True)
timestamp_rule = dict(type='integer', required=True, check_with=check_timestamp)
ip_rule = dict(type='string', required=True, check_with=check_ip)

data_type_schema_map = {
    'BgAccessLog': {
        'bg_name': dict(type='string', required=True),
        'user': normal_account_rule,
        'op_ts': timestamp_rule,
        'host': dict(type='string', required=True),
        'url': dict(type='string', required=True),
        'method': dict(type='string', allowed=['GET', 'POST', 'PUT', 'DELETE'], required=True,
                       coerce=lambda x: x.upper()),
        'params': dict(type='string', required=True),
        'ip': ip_rule,
        'ua': dict(type='string', required=True),
        'op_module': dict(type='string', required=False),
    },
    'UserRoleModifyLog': {
        'bg_name': dict(type='string', required=True),
        'user': normal_account_rule,
        'modify_ts': timestamp_rule,
        'modify_type': dict(type='string', allowed=['add', 'delete'], required=True),
        'role': dict(type='string', required=True),
        'op_user': normal_account_rule,
        'op_ip': ip_rule,
        'op_ua': dict(type='string', required=True)
    },
    'RolePermissionModifyLog': {
        'bg_name': dict(type='string', required=True),
        'role': dict(type='string', required=True),
        'modify_ts': timestamp_rule,
        'modify_type': dict(type='string', allowed=['add', 'create', 'delete'], required=True),
        'permission': dict(type='string', required=True),
        'op_user': normal_account_rule,
        'op_ip': ip_rule,
        'op_ua': dict(type='string', required=True)
    },
    'UserRoleData': {
        'bg_name': dict(type='string', required=True),
        'role': dict(type='string', required=True),
        'user_details': {
            'type': 'list',
            'required': True,
            'minlength': 1,
            'schema': {
                'type': 'dict',
                'schema': {
                    'user': normal_account_rule,
                    'create_ts': dict(type='integer', required=False, check_with=check_timestamp)
                }
            }
        },
        'date': dict(type='string', required=True, check_with=check_date_str)
    },
    'RolePermissionData': {
        'bg_name': dict(type='string', required=True),
        'role': dict(type='string', required=True),
        'permission_details': {
            'type': 'list',
            'minlength': 1,
            'schema': {
                'type': 'dict',
                'schema': {
                    'perm_name': dict(type='string', required=True),
                    'create_ts': dict(type='integer', required=False, check_with=check_timestamp)
                }
            }
        },
        'date': dict(type='string', required=True, check_with=check_date_str)
    },
    'UserAccountData': {
        'bg_name': dict(type='string', required=True),
        'user_id': normal_account_rule,
        'accountid': accountid_rule,
        'date': dict(type='string', required=True, check_with=check_date_str)
    },
    'EmployeePositionChangeData': {
        'EMPLID': normal_account_rule,
        'HPS_ACCOUNT_ID': accountid_rule,
        'NAME': normal_account_rule,
        'HPS_TITLE_BEF': normal_account_rule,
        'HPS_TITLE_AFT': normal_account_rule,
        'HPS_DPNM_BEF': normal_account_rule,
        'HPS_DPNM_AFT': normal_account_rule,
        'MODIFT_TS': timestamp_rule,
        'ACTION': dict(type='string', required=False)
    }
}


def get_data_check_schema(data_type):
    try:
        return data_type_schema_map[data_type]
    except KeyError:
        return None


def build_private_queue_name(business_type: str) -> str:
    """
        构造一个本进程持有的私有名称
    :param business_type: 业务名称
    :return:
    """
    hostname = socket.gethostname()
    special_key = os.environ.get('SPECIAL_KEY') or os.getpid()
    assert special_key, 'NEED SPECIAL_KEY ENV'
    return '{}|{}|{}'.format(business_type, hostname.replace('.', '_'), special_key)


class RedisDataProvider(object):
    business_type = 'third_bg_log'
    redis_name = 'audit_redis'
    origin_queue_name = 'bombus:business_bg:log:list'

    def __init__(self):
        super(RedisDataProvider, self).__init__()
        self.conn = get_redis_client(self.redis_name)
        self.private_queue_name = None

    def get_log(self):
        if not self.private_queue_name:
            self.private_queue_name = build_private_queue_name(self.business_type)
        conn = self.conn
        while True:
            log_str = conn.lindex(self.private_queue_name, -1)

            if not log_str:
                log_str = conn.rpoplpush(self.origin_queue_name,
                                         self.private_queue_name)

            if log_str:
                return log_str
            else:
                time.sleep(0.1)

    def ack(self):
        self.conn.lpop(self.private_queue_name)

    def write(self, data):
        try:
            data = json.dumps(data, separators=(',', ':'))
            self.conn.rpush(self.origin_queue_name, data)
            return True
        except Exception:
            logger.exception(f'persistence {data} error')
            return False

    def batch_write(self, datas):
        try:
            datas = [json.dumps(data, separators=(',', ':')) for data in datas]
            self.conn.rpush(self.origin_queue_name, *datas)
            return True
        except Exception:
            logger.exception(f'persistence {datas} error')
            return False
