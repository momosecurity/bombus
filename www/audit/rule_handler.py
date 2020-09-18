# -*- coding:utf-8 -*-

"""
concrete logic of audit_rule
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

import abc
import datetime
import logging
import re

import arrow
from django.conf import settings
from django.utils.functional import cached_property
from mongoengine.queryset.visitor import Q

from audit.models import (AuditServerModel, AuditSysModel, AuditTaskModel,
                          BgAccessLogModel, DbUserRoleModel,
                          EmployeePositionChangeDataModel,
                          JobTransferRiskModel, NonNormalUserModel,
                          RiskUserModel, ServerInfo, TaskManagerModel,
                          UserRoleDataModel)
from bombus.libs.enums import AuditPeriodEnum, RuleTypeEnum, ServerKindEnum
from bombus.libs.exception import FastResponse
from bombus.services.mysql_service import (get_db_name_by_dept,
                                           get_db_node_by_host)
from bombus.services.user_service import UserService
from core.util import time_util
from core.utils import date2datetime, get_email_prefix, split_large_collection

logger = logging.getLogger(__name__)


class BaseHandler:

    def __init__(self, audit_sys):
        self.audit_sys = audit_sys
        self.sys_instance = AuditSysModel.objects.get(id=audit_sys)

    def convert_user_to_id(self, users: list):
        user_account_ids = []
        self.id2user = {}
        for user in users:
            user = str(user)
            accountid = user
            if not user.isdigit():
                ums_info = UserService.get_user_by_email(user) or {}
                accountid = ums_info.get('accountid') or None
                if accountid:
                    self.id2user[accountid] = user
            if accountid:
                user_account_ids.append(accountid)
        return user_account_ids

    def convert_id_to_user(self, accountids: list):
        """
        将统一比较标准转为各自存储的信息, 默认accountids
        """
        users = []
        for accountid in accountids:
            if accountid in self.id2user:
                user = self.id2user.get(accountid)
                if user:
                    users.append(user)
            else:
                users.append(accountid)
        return users

    @cached_property
    def all_server_names(self):
        return AuditServerModel.get_server_name_list(self.audit_sys, self.server_kind)

    @cached_property
    def yesterday_date(self):
        return time_util.yesterday()

    def all_users(self):
        users = self.get_all_users()
        return self.fmt_users(users)

    def admin_users(self):
        users = self.get_admin_users()
        return self.fmt_users(users)

    def fmt_users(self, users):
        normal_users = self.convert_normal_users(users)
        user_account_ids = self.convert_user_to_id(normal_users)
        return [str(x) for x in user_account_ids]

    def convert_normal_users(self, user_names, reverse=False):
        if not user_names:
            return user_names
        user_map = NonNormalUserModel.get_user_map(user_names, self.audit_sys, self.server_kind, reverse=reverse)
        record_normal_users = set()
        for v in user_map.values():
            record_normal_users |= set(v)
        users = list((set(user_names) - set(user_map.keys())) | record_normal_users)
        return users

    def update_risk_tag(self, users, validated):
        cus_users = self.convert_id_to_user(users)
        ori_users = self.convert_normal_users(cus_users, reverse=True)
        self._update_risk_tag(ori_users, validated)

    def _update_risk_tag(self, ori_user, validated):
        pass


class AppPermHandler(BaseHandler):

    server_kind = ServerKindEnum.APP.name
    model = UserRoleDataModel

    def get_admin_role_by_bg(self, bg_name):
        return settings.BG_ADMIN_ROLE_MAP.get(bg_name, ) or ''

    def get_all_users(self):
        return UserRoleDataModel.objects.filter(
            bg_name__in=self.all_server_names,
            record_date=self.yesterday_date
        ).values_list('user').distinct('user')

    def get_admin_users(self):
        users = []
        for bg_name in self.all_server_names:
            admin_role = self.get_admin_role_by_bg(bg_name)
            if admin_role:
                bg_users = UserRoleDataModel.objects.filter(
                    record_date=self.yesterday_date,
                    bg_name=bg_name,
                    role=admin_role).values_list('user')
                users.extend(bg_users)
        return list(set(users))

    def _update_risk_tag(self, users, validated):
        self.model.objects.filter(
            bg_name__in=self.all_server_names,
            user__in=users,
            record_date=self.yesterday_date
        ).update(risk_tag=(not validated), add_to_set__risk_sys=self.sys_instance)


class SysPermHandler(BaseHandler):
    server_kind = ServerKindEnum.SA.name
    model = ServerInfo
    # 自运维主机标签
    SELF_OPERATE_TAG = ['ads-mine']

    def get_all_users(self):
        return ServerInfo.objects.filter(
            server_name__in=self.all_server_names,
            record_date=self.yesterday_date
        ).values_list('root_user').distinct('root_user')

    @cached_property
    def clear_server_names(self):
        clear_server_names = self.all_server_names
        re_pattern = '|'.join(self.SELF_OPERATE_TAG)
        if re_pattern:
            clear_server_names = list(filter(lambda x: not re.search(re_pattern, x), clear_server_names))
        return clear_server_names

    def get_admin_users(self):
        return ServerInfo.objects.filter(
            server_name__in=self.clear_server_names,
            record_date=self.yesterday_date
        ).values_list('root_user').distinct('root_user')

    def _update_risk_tag(self, users, validated):
        self.model.objects.filter(
            server_name__in=self.all_server_names,
            record_date=self.yesterday_date,
            root_user__in=users
        ).update(risk_tag=(not validated), add_to_set__risk_sys=self.sys_instance)


class DbPermHandler(BaseHandler):
    server_kind = ServerKindEnum.DBA.name
    model = DbUserRoleModel

    def db_dept_tip_filter(self):
        tips = AuditSysModel.get_fmt_db_dept_tip(self.audit_sys)
        tip_db_map = get_db_name_by_dept(tips)
        db_names = set()
        for db in tip_db_map.values():
            db_names |= set(db)
        db_names = list(db_names)
        if db_names:
            return Q(**{'db_name__in': db_names}) | Q(**({'db_name': None}))
        else:
            return Q()

    def get_asset_filter(self):
        asset_filter = Q(**{'server_name__in': self.all_server_names})
        db_nodes = get_db_node_by_host(self.all_server_names)
        if db_nodes:
            db_query = Q(**{'db_node__in': db_nodes})
            asset_filter |= db_query
        db_name_filter = self.db_dept_tip_filter()
        asset_filter &= db_name_filter
        return asset_filter

    def get_all_users(self):
        asset_filter = self.get_asset_filter()
        record_date_filter = Q(**{'record_date': self.yesterday_date})
        return self.model.objects.filter(asset_filter & record_date_filter).values_list('user').distinct('user')

    def get_admin_users(self):
        return settings.DBA

    def _update_risk_tag(self, users, validated):
        asset_filter = self.get_asset_filter()
        record_date_filter = Q(**{'record_date': self.yesterday_date})
        user_filter = Q(**{'user__in': users})
        self.model.objects.filter(
            asset_filter & record_date_filter & user_filter
        ).update(risk_tag=(not validated), add_to_set__risk_sys=self.sys_instance)


class AuditRuleHandler(metaclass=abc.ABCMeta):
    """
    审核策略
    """
    @classmethod
    def to_dict(cls):
        return {
            'name': cls.__name__,
            'desc': cls.name,
            'configurable': cls.configurable
        }


class PermRuleHandler(AuditRuleHandler):

    def __init__(self, audit_sys):
        self.audit_sys = audit_sys
        self.app_handler = AppPermHandler(audit_sys)
        self.sys_handler = SysPermHandler(audit_sys)
        self.db_handler = DbPermHandler(audit_sys)

    def get_audit_sys_users(self):
        """
        获取业务线所有用户
        """
        app_users = self.app_handler.all_users()
        sys_users = self.sys_handler.all_users()
        db_users = self.db_handler.all_users()
        return list(set(app_users + sys_users + db_users))

    def callback_risk_tag(self, users, validated):
        # users here mean accountids
        self.app_handler.update_risk_tag(users, validated)
        self.sys_handler.update_risk_tag(users, validated)
        self.db_handler.update_risk_tag(users, validated)


class PermissionMatrixHandler(PermRuleHandler):
    """
    权限矩阵
    """
    name = '权限矩阵'
    configurable = False

    def validate_sys(self):
        """
        验证业务线内权限相容情况
        """
        # 下面的所有user都是accountid
        app_admin_list = self.app_handler.admin_users()
        sa_list = self.sys_handler.admin_users()
        dba_list = self.db_handler.admin_users()
        set_app_list = set(app_admin_list)
        set_sa_list = set(sa_list)
        set_dba_list = set(dba_list)
        all_admin_users = (set_app_list & set_dba_list) | (set_app_list & set_sa_list) | (set_dba_list & set_sa_list)
        for user in all_admin_users:
            self.update_risk_user(user, user in app_admin_list, user in sa_list, user in dba_list)

    def update_risk_user(self, user, is_app_admin, is_sa, is_dba):
        """
        更新用户风险记录
        """
        admin_value = is_app_admin + is_dba + is_sa
        validated = False
        if admin_value <= 1:
            validated = True
        elif admin_value == 2:
            if is_dba == is_sa == 1:
                validated = True

        admin_desc = ''
        if not validated:
            admin_desc = '、'.join(filter(None, [
                (is_app_admin and '应用管理员' or ''),
                (is_sa and '系统管理员' or ''),
                (is_dba and '数据库管理员' or '')]))
            admin_desc = '兼具' + admin_desc
        RiskUserModel.update_risk_user(user, self.audit_sys, {'matrix_risk': admin_desc})
        self.callback_risk_tag([user], validated)


class ResignUserHandler(PermRuleHandler):
    """
    离职用户信息检测
    """
    name = '离职信息检测'
    configurable = False

    def validate_sys(self):
        """
        验证业务线所有人员离职情况
        """
        # 下面的所有user都是accountid
        all_users = self.get_audit_sys_users()
        not_staff_users = []
        for user in all_users:
            is_staff = UserService.is_staff(user)
            if not is_staff:
                not_staff_users.append(user)
        self.update_risk_users(not_staff_users)

    def update_risk_users(self, users):
        self.callback_risk_tag(users, False)
        for user in users:
            RiskUserModel.update_risk_user(user, self.audit_sys, {'staff_risk': '已离职'})


class JobTransferHandler(PermRuleHandler):
    """
    岗位变更信息,
    注: 和权限矩阵和离职信息信息直接绑定到业务线上不同的是, 岗位变更提示与审核周期有关, 所以风险状态要维护到任务上
    """
    name = '岗位变更信息'
    configurable = False

    def validate_sys(self):
        now = datetime.datetime.now()
        all_active_tasks = AuditTaskModel.get_active_task_by_sys(self.audit_sys)
        all_users = self.get_audit_sys_users()
        for task in all_active_tasks:
            created_time = task.created_time
            audit_period = task.audit_period
            start_time, end_time = PeriodProxyHandler.time_range(audit_period, created_time)

            transfer_account_ids = EmployeePositionChangeDataModel.get_accountid_by_time_range(start_time, now)
            task_risk_user_ids = list(set(all_users) & set(transfer_account_ids))
            self.record_task_risk_users(task, task_risk_user_ids)

    def record_task_risk_users(self, task, user_ids):
        """记录风险用户"""
        if not user_ids:
            return
        step = 50
        emails = []
        for _ids in split_large_collection(user_ids, step):
            id2emails = UserService.batch_id_to_email(_ids)
            emails.extend(id2emails.values())
        clear_emails = [get_email_prefix(em) for em in emails]
        nonnormal_user_names = self.get_nonnormal_names(user_ids)
        user_ids += nonnormal_user_names
        clear_emails += nonnormal_user_names
        JobTransferRiskModel.save_risk(task, user_ids, clear_emails)

    def get_nonnormal_names(self, user_ids):
        """
        补充非标准用户信息
        """
        result = set()
        id_names_map = NonNormalUserModel.get_nonnormal_name_by_accountids(self.audit_sys, user_ids)
        for names in id_names_map.values():
            result |= names
        return list(result)


class LongTimeNoUseHandler(AuditRuleHandler):
    configurable = False
    name = '长期未使用'
    days = 45
    risk_reason = '已有45天未操作'
    white_users = []

    def __init__(self, audit_sys):
        self.audit_sys = audit_sys
        self.app_handler = AppPermHandler(audit_sys)
        self.sys_instance = AuditSysModel.objects.get(id=audit_sys)

    def rule_configed(self):
        """ 判断策略原子是否配置 """
        atoms = TaskManagerModel.get_atoms_by_sys(self.audit_sys)
        for atom in atoms:
            if atom.rule_type == RuleTypeEnum.NO_USE.name:
                return True
        return False

    @property
    def server_names(self):
        return AuditServerModel.get_server_name_list(self.audit_sys, ServerKindEnum.APP.name)

    def hit_rule(self, user):
        last_log = BgAccessLogModel.objects.filter(user=user,
                                                    bg_name__in=self.server_names).order_by('-access_dt').first()

        if not last_log:
            return False
        now = time_util.today()
        last_req_time = last_log.access_dt
        no_use_days = (now - last_req_time).days
        return no_use_days >= 45

    def _update_risk_tag(self, users, validated):
        UserRoleDataModel.objects.filter(
            bg_name__in=self.server_names,
            user__in=users,
            record_date=time_util.yesterday()
        ).update(risk_tag=(not validated), add_to_set__risk_sys=self.audit_sys)

    def validate_sys(self):
        if not self.rule_configed():
            return
        app_handler = AppPermHandler(self.audit_sys)
        users = app_handler.get_all_users()
        users = list(set(users) - set(self.white_users))
        risk_users = set()
        for user in users:
            _is_hit = self.hit_rule(user)
            if _is_hit:
                risk_users.add(user)
                RiskUserModel.update_risk_user(user, self.audit_sys, {'no_use_risk': self.risk_reason})

        if risk_users:
            self._update_risk_tag(risk_users, False)


class RegexMatchHandler(AuditRuleHandler):
    """
    正则匹配
    """
    name = '命令正则匹配'
    configurable = True


class RegexPatternHandler:
    """
    正则规则
    """
    def __init__(self, pk, pattern):
        self.pk = pk
        self.pattern = pattern
        self.complile_pattern = re.compile(pattern, re.IGNORECASE)

    def match(self, command):
        return bool(self.complile_pattern.search(command))


class ProxyHandler:

    handle_mapping = {
        RuleTypeEnum.PERM: PermissionMatrixHandler,
        RuleTypeEnum.REGEX: RegexMatchHandler,
        RuleTypeEnum.NO_USE: LongTimeNoUseHandler,
        RuleTypeEnum.JOB_TRANS: JobTransferHandler
    }


# 审核周期handler
class PeriodHandler:
    patterns = []

    def __init__(self, dt=None):
        self.dt = dt or arrow.now()
        if not isinstance(self.dt, arrow.arrow.Arrow):
            self.dt = arrow.arrow.Arrow.fromdatetime(self.dt)
        self.year, self.month, self.day = self.dt.year, self.dt.month, self.dt.day

    def match(self):
        return (self.month, self.day) in self.patterns


class QuarterHandler(PeriodHandler):
    patterns = [(1,1), (4,1), (7,1), (10,1)]

    def tag(self):
        return f'{self.year}年Q{self.convert_month_to_quarter()}'

    def convert_month_to_quarter(self):
        return (self.month + 2)//3

    def time_range(self):
        start_time = self.dt.floor('quarter')
        end_time = self.dt.ceil('quarter')
        return start_time, end_time


class HalfYearHandler(PeriodHandler):
    patterns = [(7,1), (1,1)]

    def tag(self):
        desc = '上' if 1 <= self.month < 7 else '下'
        return f'{self.year}年{desc}'

    def time_range(self):
        if 1 <= self.month < 7:
            start_month = 1
            end_month = 6
        else:
            start_month = 7
            end_month = 12
        start_time = arrow.arrow.Arrow(self.year, start_month, self.day).floor('quarter')
        end_time = arrow.arrow.Arrow(self.year, end_month, self.day).ceil('quarter')
        return start_time, end_time


class MonthHandler(PeriodHandler):
    patterns = [(x,1) for x in range(1,13)]

    def tag(self):
        return f'{self.year}年{self.month}月'

    def time_range(self):
        start_time = self.dt.floor('month')
        end_time = self.dt.ceil('month')
        return start_time, end_time


class PeriodProxyHandler:
    periodHandlerMap = {
        AuditPeriodEnum.QUARTER.name: QuarterHandler,
        AuditPeriodEnum.HALFYEAR.name: HalfYearHandler,
        AuditPeriodEnum.MONTH.name: MonthHandler,
    }

    @classmethod
    def get_handler(cls, period_name, dt=None):
        handler_kls = cls.periodHandlerMap.get(period_name)
        if handler_kls:
            return handler_kls(dt)
        else:
            raise FastResponse(f'错误周期名称: {period_name}')

    @staticmethod
    def convert_arrow_to_datetime(arrow_time):
        fmt_time = arrow_time.datetime
        fmt_time = fmt_time.replace(tzinfo=None)
        return fmt_time

    @classmethod
    def time_range(cls, period_name, dt=None, keep_arrow=False):
        handler = cls.get_handler(period_name, dt)
        start_time, end_time = handler.time_range()
        if not keep_arrow:
            start_time = cls.convert_arrow_to_datetime(start_time)
            end_time = cls.convert_arrow_to_datetime(end_time)
        return start_time, end_time
