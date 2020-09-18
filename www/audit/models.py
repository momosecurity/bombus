# -*- coding: utf-8 -*-

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
import re
from collections import defaultdict

from django.conf import settings
from mongoengine import (BooleanField, DateField, DateTimeField, DictField,
                         Document, ListField, ReferenceField, StringField)
from mongoengine.queryset import DoesNotExist

from bombus.libs.enums import (AuditPeriodEnum, MessageBoardEnum,
                               OnOfflineStatusEnum, ReviewTypeEnum,
                               RuleTypeEnum, ServerKindEnum, TaskStatusEnum)
from bombus.services.user_service import UserService
from core.util import time_util
from core.util.time_util import time2str
from core.utils import get_email_prefix

logger = logging.getLogger(__name__)


class LastUpdateBaseModel(Document):
    """
    记录更新人, 更新时间
    """
    last_update = DateTimeField(required=True, verbose_name='更新时间')
    last_update_person = StringField(required=True, verbose_name='最后更新人')
    meta = {
        'abstract': True
    }

    @property
    def last_update_person_render(self):
        if self.last_update_person:
            return (UserService.get_user_by_email(self.last_update_person) or {}).get('name')
        return ''

    @property
    def last_update_render(self):
        if self.last_update:
            return time2str(self.last_update)
        return None


class AuditSysModel(LastUpdateBaseModel):
    """
    审阅系统范围定义
    """
    sys_name = StringField(required=True, verbose_name='业务线', unique=True)
    sys_id = StringField(required=True, verbose_name='业务线id', unique=True)
    dept_name = StringField(required=False, verbose_name='部门名称', null=True)
    db_dept_tip = StringField(required=False, verbose_name='数据库部门映射提示', null=True)
    online_ticket_dept_id = StringField(required=False, verbose_name='上线单部门', null=True)
    deploy_ticket_dept = StringField(required=False, verbose_name='部署单部门', null=True)
    # 以下人员以英文逗号分割, 存储accountid
    leader = StringField(required=False, verbose_name='负责人', null=True)
    sa_auditor = StringField(required=False, verbose_name='操作系统账号审阅人', null=True)
    dba_auditor = StringField(required=False, verbose_name='数据库系统账号审阅人', null=True)
    sys_db_auditor = StringField(required=False, verbose_name='运维审阅人', null=True)
    app_auditor = StringField(required=False, verbose_name='应用系统账号审阅人', null=True)
    ticket_auditor = StringField(required=False, verbose_name='工单审阅人', null=True)
    meta = {
        'collection': 'audit_sys',
        'verbose_name': '业务线审阅人'
    }

    @classmethod
    def get_sys_id_by_online_ticket_dept(cls, dept_id):
        return cls.objects.filter(online_ticket_dept_id=dept_id).distinct('sys_id')

    @classmethod
    def get_sys_id_by_deploy_ticket_dept(cls, dept_id):
        return cls.objects.filter(deploy_ticket_dept=dept_id).distinct('sys_id')

    @classmethod
    def server_kind_auditors(cls, id):
        try:
            instance = cls.objects.get(id=id)
            return {
                ServerKindEnum.APP.name: cls.get_multi_user(instance.app_auditor),
                ServerKindEnum.SYS_DB.name: cls.get_multi_user(instance.sys_db_auditor),
                ServerKindEnum.TICKET.name: cls.get_multi_user(instance.ticket_auditor),
            }
        except Exception as e:
            return {}

    @classmethod
    def get_fmt_db_dept_tip(cls, id) -> list:
        try:
            instance = cls.objects.get(id=id)
            tip = instance.db_dept_tip or ''
            return list(filter(None, tip.split(';')))
        except:
            return []

    @classmethod
    def get_sys_by_user_on_auditor(cls, user):
        """
        根据用户邮箱, 获取其担任审阅人的业务线
        """
        accountid = user
        if not str(accountid).isdigit():
            email = str(accountid)
            user = UserService.get_user_by_email(email) or {}
            accountid = user.get('accountid') or None
        if not accountid:
            return []
        target_sys = []
        sys_list = cls.objects.all()
        for sys in sys_list:
            auditors = filter(None, [sys.leader, sys.sys_db_auditor, sys.app_auditor, sys.ticket_auditor])
            if accountid in cls.split_auditor(';'.join(auditors)):
                target_sys.append(sys)
        return target_sys

    @classmethod
    def get_list(cls):
        result = []
        query_result = cls.objects.all()
        for qry in query_result:
            tmp = {}
            tmp['id'] = str(qry.id)
            tmp['sys_name'] = str(qry.sys_name)
            result.append(tmp)
        return result

    @classmethod
    def is_auditor(cls, sys_id, review_type, accountid):
        try:
            if not accountid:
                return False
            instance = cls.objects.get(id=sys_id)
            auditor = ''

            if ReviewTypeEnum[review_type] == ReviewTypeEnum.APP:
                auditor = instance.app_auditor
            elif ReviewTypeEnum[review_type] == ReviewTypeEnum.SYS_DB:
                auditor = instance.sys_db_auditor
            elif ReviewTypeEnum[review_type] == ReviewTypeEnum.TICKET:
                auditor = instance.ticket_auditor
            return accountid in cls.split_auditor(auditor)
        except:
            return False

    @staticmethod
    def split_auditor(auditors):
        if not auditors:
            return []
        return list([x.strip() for x in filter(None, re.split('[,;，；\s]', auditors))])

    @classmethod
    def visible_scope_by_person(cls, audit_sys, user):
        """
        用户对于该业务线可见的审阅内容
        """
        all_scopes = [
            ReviewTypeEnum.APP.name,
            ReviewTypeEnum.SYS_DB.name,
            ReviewTypeEnum.TICKET.name
        ]

        if not str(user).isdigit():
            user = get_email_prefix(user)
            user_info = UserService.get_user_by_email(user)
            user = (user_info or {}).get('accountid')
        if not user:
            return all_scopes

        perm_scopes = []
        try:
            instance = cls.objects.get(id=audit_sys)
            sys_db_auditor = cls.split_auditor(instance.sys_db_auditor)
            app_auditor = cls.split_auditor(instance.app_auditor)
            ticket_auditor = cls.split_auditor(instance.ticket_auditor)
            if user in app_auditor:
                perm_scopes.append(ReviewTypeEnum.APP.name)
            if user in sys_db_auditor:
                perm_scopes.append(ReviewTypeEnum.SYS_DB.name)
            if user in ticket_auditor:
                perm_scopes.append(ReviewTypeEnum.TICKET.name)
            return perm_scopes or all_scopes
        except:
            return all_scopes

    @property
    def audit_scope(self):
        return 'SOX'

    @classmethod
    def get_multi_user(cls, auditors: str):
        if not auditors:
            return '-'
        user_names = []
        error_ids = []
        id_list = cls.split_auditor(auditors)
        batch_user_info = UserService.batch_get_user_by_accountid(id_list)
        for accountid in id_list:
            name = (batch_user_info.get(accountid) or {}).get('name')
            if name:
                user_names.append(name)
            else:
                error_ids.append(accountid)
        return ','.join(user_names + error_ids) or '-'

    @property
    def leader_render(self):
        return self.get_multi_user(self.leader)

    @property
    def sa_auditor_render(self):
        return self.get_multi_user(self.sa_auditor)

    @property
    def dba_auditor_render(self):
        return self.get_multi_user(self.dba_auditor)

    @property
    def app_auditor_render(self):
        return self.get_multi_user(self.app_auditor)

    @property
    def sys_db_auditor_render(self):
        return self.get_multi_user(self.sys_db_auditor)

    @property
    def ticket_auditor_render(self):
        return self.get_multi_user(self.ticket_auditor)

    @property
    def all_auditors(self) -> list:
        auditors = ','.join(filter(None, [self.app_auditor, self.sys_db_auditor]))
        return list(set(self.split_auditor(auditors)))

    @property
    def list_ticket_auditors(self) -> list:
        return self.split_auditor(self.ticket_auditor)


class SysProjectModel(Document):
    sys_id = StringField(required=True, verbose_name='业务线id')
    project = StringField(required=True, verbose_name='项目名称')
    appkey = StringField(required=True, verbose_name='appkey')
    created_date = DateField(required=True, verbose_name='创建时间')
    update_date = DateField(required=True, verbose_name='更新时间')
    meta = {
        'collection': 'sys_project',
        'verbose_name': '业务线项目列表',
        'indexes': [
            'update_date',
            'sys_id',
            {'fields': ('sys_id', 'project'), 'unique': True},
        ]
    }

    @classmethod
    def get_project_by_sys_ids(cls, sys_ids):
        return cls.objects.filter(sys_id__in=sys_ids).distinct('project')

    @classmethod
    def get_appkey_by_sys_id(cls, sys_id):
        return cls.objects.filter(sys_id=sys_id).distinct('appkey')


class AuditServerModel(Document):
    """ 审计资产 """
    server_name = StringField(required=True, verbose_name='主机名')
    server_kind = StringField(required=True, verbose_name='类别', choices=ServerKindEnum.choices(),
                              default=ServerKindEnum.APP)
    server_type = StringField(required=True, verbose_name='类型')
    audit_sys = ReferenceField(AuditSysModel, required=True, verbose_name='业务线')
    bg_alias = StringField(required=False, verbose_name='应用别名')
    meta = {
        'collection': 'audit_server',
        'verbose_name': '审计资产',
        'indexes': [
            'server_name',
            {'fields': ('server_name', 'audit_sys', 'server_kind'), 'unique': True},
        ],
    }

    @property
    def leader_name(self):
        return self.audit_sys.leader_render

    @property
    def audit_scope(self):
        return self.audit_sys.audit_scope

    @property
    def audit_sys_name(self):
        return self.audit_sys.sys_name

    @property
    def server_kind_name(self):
        return ServerKindEnum[self.server_kind].desc

    @property
    def auditor_name(self):
        auditor = None
        if self.server_kind == ServerKindEnum.SA.name or self.server_kind == ServerKindEnum.DBA.name:
            auditor = self.audit_sys.sys_db_auditor_render
        elif self.server_kind == ServerKindEnum.APP.name:
            auditor = self.audit_sys.app_auditor_render
        return auditor

    @classmethod
    def get_server_name_list(cls, audit_sys, server_kind):
        if not server_kind == ServerKindEnum.APP.name:
            return list(cls.objects.filter(
                audit_sys=audit_sys, server_kind=server_kind)
                        .distinct('server_name'))
        else:
            bg_names = []
            bg_alias_list = list(cls.objects.filter(
                audit_sys=audit_sys, server_kind=ServerKindEnum.APP.name)
                                 .distinct('bg_alias'))
            for bg_alias in bg_alias_list:
                bg_names.extend(bg_alias.split(','))
            return list(filter(None, bg_names))

    @classmethod
    def get_assets(cls, audit_sys, server_kind=None):
        """
        获取资产
        """
        query_params = {
            'audit_sys': audit_sys
        }
        if server_kind is not None:
            query_params['server_kind'] = server_kind
        assets = cls.objects.filter(**query_params).all()
        return assets


class ServerInfo(Document):
    server_name = StringField(required=True, verbose_name='主机名')
    root_user = StringField(required=True, verbose_name='root用户')
    record_date = DateField(required=True, verbose_name='统计日期')
    create_dt = DateTimeField(required=False, verbose_name='创建日期', null=True)
    risk_tag = BooleanField(required=False, verbose_name='是否有风险', default=False)
    risk_sys = ListField(ReferenceField(AuditSysModel), verbose_name='有风险业务线', default=[])
    dept_name = StringField(required=False, verbose_name='部门名称', null=True)
    meta = {
        'verbose_name': '主机root账号',
        "auto_create_index": True,
        "index_background": True,
        'indexes': [
            'server_name',
            'root_user',
            'create_dt',
            'record_date',
            'dept_name',
            {'fields': ('server_name', 'root_user', 'record_date'), 'unique': True},
        ]
    }


class RegexPatternModel(LastUpdateBaseModel):
    """
    正则规则
    """
    name = StringField(required=True, verbose_name='名称')
    regex = StringField(required=True, verbose_name='正则规则', unique=True)
    desc = StringField(required=True, verbose_name='描述说明')
    meta = {
        'collection': 'regex_rule',
        'verbose_name': '正则规则'
    }


class RuleAtomModel(LastUpdateBaseModel):
    """
    策略原子
    """
    name = StringField(required=True, verbose_name='名称')
    status = StringField(required=True, verbose_name='状态', choices=OnOfflineStatusEnum.choices(),
                         default=OnOfflineStatusEnum.ONLINE)
    rule_type = StringField(required=True, verbose_name='策略类型', choices=RuleTypeEnum.choices(),
                            default=RuleTypeEnum.PERM)
    desc = StringField(required=True, verbose_name='描述')
    regex_pattern = ListField(ReferenceField(RegexPatternModel), required=False, verbose_name='正则规则', null=True)
    meta = {
        'collection': 'rule_atom',
        'verbose_name': '策略原子'
    }

    @property
    def status_render(self):
        return OnOfflineStatusEnum[self.status].desc

    @classmethod
    def get_name_by_id(cls, id):
        try:
            instance = cls.objects.get(id=id)
            return instance.name
        except Exception as e:
            return ''

    @classmethod
    def get_regex_pattern_by_id(cls, id):
        try:
            instance = cls.objects.get(id=id)
            if instance.rule_type == RuleTypeEnum.REGEX.name:
                return instance.regex_pattern
            return []
        except:
            return []


class RuleGroupModel(LastUpdateBaseModel):
    """
    策略组
    """
    name = StringField(required=True, verbose_name='名称')
    atoms = ListField(ReferenceField(RuleAtomModel), required=True, verbose_name='策略原子')
    audit_period = StringField(required=True, verbose_name='审阅周期', choices=AuditPeriodEnum.choices(),
                               default=AuditPeriodEnum.QUARTER)
    status = StringField(required=True, verbose_name='状态', choices=OnOfflineStatusEnum.choices(),
                         default=OnOfflineStatusEnum.ONLINE)
    meta = {
        'collection': 'rule_group',
        'verbose_name': '策略组'
    }

    @property
    def status_render(self):
        return OnOfflineStatusEnum[self.status].desc

    @property
    def audit_period_render(self):
        return AuditPeriodEnum[self.audit_period].desc

    @classmethod
    def get_list(cls):
        result = []
        query_result = cls.objects.all()
        for qry in query_result:
            tmp = {}
            tmp['id'] = str(qry.id)
            tmp['name'] = str(qry.name)
            result.append(tmp)
        return result


class NonNormalUserModel(LastUpdateBaseModel):
    """
    非标准用户
    """
    name = StringField(required=True, verbose_name='用户标识')
    audit_sys = ReferenceField(AuditSysModel, required=True, verbose_name='所属业务线')
    server_kind = StringField(required=True, verbose_name='系统类型', choices=ServerKindEnum.choices(),
                              default=ServerKindEnum.APP)
    user = StringField(required=True, verbose_name='对应用户')  # accountid
    user_email = StringField(required=True, verbose_name='用户邮箱前缀')
    user_name = StringField(required=True, verbose_name='用户名称')
    dept = StringField(required=True, verbose_name='所属部门')
    deleted = BooleanField(required=True, verbose_name='是否删除', default=False)
    meta = {
        'collection': 'non_normal_user',
        'verbose_name': '非标准用户',
        'indexes': [
            'name',
            'user',
            'user_email'
        ]
    }

    def delete(self, **kwargs):
        self.deleted = True
        self.save()

    @classmethod
    def get_name_by_users(cls, audit_sys, users: list):
        if not list:
            return []
        names = list(cls.objects.filter(
            audit_sys=audit_sys, user__in=users, deleted=False
        ).values_list('name').distinct('name'))
        return names

    @property
    def user_render(self):
        return self.user_name + '(' + self.user + ')'

    @property
    def server_kind_render(self):
        return ServerKindEnum[self.server_kind].desc

    @property
    def audit_sys_render(self):
        return self.audit_sys.sys_name

    @classmethod
    def get_nonnormal_name_by_accountids(cls, audit_sys, accountids):
        """
        获取业务线下id对应的非标准用户名
        """
        ret_res = defaultdict(set)
        queryset = cls.objects.filter(audit_sys=audit_sys, user__in=accountids, deleted=False).all()
        for qs in queryset:
            ret_res[qs.user].add(qs.name)
        return ret_res

    @classmethod
    def get_normal_user(cls, name, audit_sys, server_kind):
        normal_user_column = 'user' if server_kind == ServerKindEnum.APP.name else 'user_email'
        user_tag = cls.objects.filter(name=name,
                                      audit_sys=audit_sys,
                                      server_kind=server_kind,
                                      deleted=False).values_list(normal_user_column).first()
        return user_tag or name

    @classmethod
    def get_user_map(cls, user_tags: list, audit_sys, server_kind, reverse=False) -> dict:
        """
        根据非标准用户名, 获取对应用户信息; reverse为True则反向查找
        备注:
            app:  account_id->normal_account_id
            sa/db: email->normal_email
        """
        ori_user_column = 'name'
        normal_user_column = 'user' if server_kind == ServerKindEnum.APP.name else 'user_email'
        ret_res = defaultdict(set)
        filter_params = {
            'audit_sys': audit_sys,
            'server_kind': server_kind,
            'deleted': False,
        }
        if not reverse:
            filter_params['name__in'] = user_tags
            query_res = cls.objects.filter(**filter_params).values_list(ori_user_column, normal_user_column)
        else:
            filter_params[f'{normal_user_column}__in'] = user_tags
            query_res = cls.objects.filter(**filter_params).values_list(normal_user_column, ori_user_column)
        for query_key, map_key in query_res:
            ret_res[query_key].add(map_key)
        return ret_res


class BashCommandModel(Document):
    """
    操作系统命令
    """
    source_id = StringField(required=True, verbose_name='原始id', unique=True)
    server_name = StringField(required=True, verbose_name='服务器名称')
    server_ip = StringField(required=True, verbose_name='服务器ip')
    user_name = StringField(required=True, verbose_name='用户名称')
    client_ip = StringField(required=True, verbose_name='客户端ip')
    time = StringField(required=True, verbose_name='操作时间')
    bash_command = StringField(required=True, verbose_name='操作命令')
    hit_patterns = ListField(ReferenceField(RegexPatternModel), verbose_name='正则规则', required=False, null=True)
    ### 抽样时添加
    hit_rule_atoms = ListField(ReferenceField(RuleAtomModel), verbose_name='命中策略原子', required=False, null=True)
    risk_tag = BooleanField(required=False, verbose_name='是否有风险', default=False)
    meta = {
        'collection': 'bash_command',
        'verbose_name': '系统命令',
        'indexes': [
            'server_name',
            'time',
            'user_name'
        ]
    }


class TaskManagerModel(LastUpdateBaseModel):
    """
    任务计划管理
    """
    name = StringField(required=True, verbose_name='任务名称')
    desc = StringField(required=True, verbose_name='任务描述')
    sys = ReferenceField(AuditSysModel, required=True, verbose_name='业务线')
    rule_group = ReferenceField(RuleGroupModel, required=True, verbose_name='策略组')
    follow_up_person = StringField(required=True, verbose_name='跟进人')
    status = StringField(required=True, verbose_name='状态', choices=OnOfflineStatusEnum.choices(),
                         default=OnOfflineStatusEnum.ONLINE)
    meta = {
        'collection': 'task_manager',
        'verbose_name': '任务配置'
    }

    @classmethod
    def get_atoms_by_sys(cls, sys_id):
        queryset = cls.objects.filter(sys=sys_id, status=OnOfflineStatusEnum.ONLINE.name)
        total_atoms = set()
        for qs in queryset:
            rule_group = qs.rule_group
            if rule_group.status == OnOfflineStatusEnum.ONLINE.name:
                atoms = rule_group.atoms
                total_atoms |= set((atoms or []))
        return [at for at in total_atoms if at.status == OnOfflineStatusEnum.ONLINE.name]

    @classmethod
    def get_managers_by_sys(cls, sys_list):
        result = []
        queryset = cls.objects.filter(sys__in=sys_list).all()
        for qs in queryset:
            result.append(str(qs.id))
        return result

    @classmethod
    def get_list(cls):
        result = []
        query_result = cls.objects.all()
        for qry in query_result:
            tmp = {'id': str(qry.id), 'name': str(qry.name)}
            result.append(tmp)
        return result

    @property
    def period_render(self):
        return self.rule_group.audit_period_render

    @property
    def follow_up_person_render(self):
        return UserService.get_user_name(self.follow_up_person) or '-'

    @property
    def sys_render(self):
        return self.sys.sys_name

    @property
    def rule_group_render(self):
        try:
            return self.rule_group.name
        except:
            return ''

    @property
    def status_render(self):
        return OnOfflineStatusEnum[self.status].desc

    @property
    def cur_period_render(self):
        last_task = AuditTaskModel.objects. \
            filter(task_manager=self.id) \
            .order_by('-created_time').first()
        return last_task and last_task.period or '无'


class AuditTaskModel(Document):
    """
    具体执行的任务对象
    """
    created_time = DateTimeField(required=True, verbose_name='创建时间')
    period = StringField(required=True, verbose_name='所属周期')
    status = StringField(required=True, verbose_name='任务状态', choices=TaskStatusEnum.choices(),
                         default=TaskStatusEnum.NOT_STARTED)
    task_manager = ReferenceField(TaskManagerModel, verbose_name='任务所属', required=True)
    log_sampled = BooleanField(required=False, verbose_name='是否日志抽样', default=False)
    # 审阅报告页展示用生成时间
    start_time = DateTimeField(required=False, verbose_name='启动时间', null=True)
    finished_time = DateTimeField(required=False, verbose_name='完成时间', null=True)
    meta = {
        'collection': 'audit_task',
        'verbose_name': '审计任务'
    }

    @classmethod
    def rule_type_is_configed(cls, task_id, rule_type):
        try:
            task_obj = cls.objects.get(id=task_id)
        except:
            return False
        manager = task_obj.task_manager
        rule_group = manager.rule_group
        if rule_group.status != OnOfflineStatusEnum.ONLINE.name:
            return False

        atoms = rule_group.atoms
        for at in atoms:
            if at.status == OnOfflineStatusEnum.ONLINE.name and at.rule_type == rule_type:
                return True
        return False

    def get_atoms_by_sys(cls, sys_id):
        queryset = cls.objects.filter(sys=sys_id, status=OnOfflineStatusEnum.ONLINE.name)
        total_atoms = set()
        for qs in queryset:
            rule_group = qs.rule_group
            if rule_group.status == OnOfflineStatusEnum.ONLINE.name:
                atoms = rule_group.atoms
                total_atoms |= set((atoms or []))
        return [at for at in total_atoms if at.status == OnOfflineStatusEnum.ONLINE.name]

    @property
    def review_page_url(self):
        return f'{settings.HTTPS_HOST}report/newreview/{self.id}'

    @classmethod
    def get_title_by_id(cls, id):
        try:
            instance = cls.objects.get(id=id)
            return instance.title
        except DoesNotExist as e:
            return ''
        except Exception as e:
            logger.exception(f'get task error by id({str(id)})')
            return ''

    @classmethod
    def get_active_task_by_sys(cls, sys):
        manager_list = TaskManagerModel.get_managers_by_sys([sys])
        return cls.objects.filter(task_manager__in=manager_list,
                                  status__ne=TaskStatusEnum.FINISHED.name).all()

    @staticmethod
    def pause_tip():
        tip = '该任务已被暂停, 详请咨询'
        names = []
        target_user = '合规同事'
        for accountid in settings.AUDIT_USERS:
            ums_info = UserService.query_accountid(accountid)
            name = (ums_info or {}).get('name')
            if name:
                names.append(name)
        if names:
            target_user = '、'.join(names)
        return f'{tip}{target_user}'

    @property
    def audit_sys_id(self):
        return str(self.task_manager.sys.id)

    @property
    def created_time_render(self):
        return time2str(self.created_time)

    @property
    def task_manager_render(self):
        return self.task_manager.name

    @property
    def status_render(self):
        if self.status != TaskStatusEnum.UNDER_REVIEW.name:
            return TaskStatusEnum[self.status].desc

        res = NewReviewCommentModel.get_review_status(self.id)
        reviewed = []
        unreviewed = []
        for k, v in res.items():
            if v:
                reviewed.append(k)
            else:
                unreviewed.append(k)
        reviewed_str = unreviewed_str = ''
        reviewed_desc = [ReviewTypeEnum[rr].desc for rr in reviewed]
        if reviewed_desc:
            reviewed_str = '、'.join(reviewed_desc) + '已审阅'
        unreviewed_desc = [ReviewTypeEnum[rr].desc for rr in unreviewed]
        if unreviewed_desc:
            unreviewed_str = '、'.join(unreviewed_desc) + '未审阅'
        return ';'.join(filter(None, [reviewed_str, unreviewed_str]))

    @property
    def title(self):
        return f'{self.task_manager.sys.sys_name}{self.period}审阅报告'

    @property
    def audit_period(self):
        return self.task_manager.rule_group.audit_period

    @property
    def start_time_render(self):
        aim_time = self.start_time
        if not aim_time:
            aim_time = datetime.datetime.today() - datetime.timedelta(days=1)
        aim_time = max(aim_time, self.created_time)
        return time2str(aim_time, fmt='%Y-%m-%d')

    @classmethod
    def get_base_info(cls, id):
        try:
            result = {}
            instance = cls.objects.get(id=id)
            result['id'] = str(instance.id)
            result['created_time'] = instance.start_time_render
            result['period'] = instance.period
            result['name'] = instance.title
            result['status'] = instance.status
            result['is_pause'] = instance.status == TaskStatusEnum.PAUSE.name
            result['audit_sys_id'] = str(instance.task_manager.sys.id)
            result['audit_sys_name'] = instance.task_manager.sys.sys_name
            result['audit_period'] = instance.task_manager.rule_group.audit_period
            result['cnf_sys_id'] = instance.task_manager.sys.sys_id
            result['is_finished'] = instance.status == TaskStatusEnum.FINISHED.name
            result['finished_time'] = instance.finished_time
            return result
        except Exception as e:
            return {}

    @classmethod
    def get_rule_atom(cls, id):
        try:
            instance = cls.objects.get(id=id)
            atoms = instance.task_manager.rule_group.atoms
            result_atoms = []
            for atom in atoms:
                if atom.status == OnOfflineStatusEnum.ONLINE.name:
                    result_atoms.append(atom)
            return result_atoms
        except:
            return []

    @classmethod
    def get_regex_rules(cls, id):
        rules = []
        atoms = cls.get_rule_atom(id)
        for atom in atoms:
            regex_pattern = RuleAtomModel.get_regex_pattern_by_id(atom.id)
            rules.extend(regex_pattern)
        return list(set(rules))

    @classmethod
    def get_review_progress(cls, task_id):
        """
        获取审计任务审阅进度
        """
        task_instance = cls.objects.get(id=task_id)
        task_id = task_instance.id
        # 日志、权限审阅进度
        query_list = list(ReviewCommentModel._get_collection().aggregate([
            {'$match': {'task': task_id}},
            {'$group': {'_id': '$server_kind', 'types': {'$addToSet': '$review_type'}}}
        ]))
        result = {}
        for r in query_list:
            result[r['_id']] = sorted(r['types'])
        # 上线单审阅进度
        audit_sys = task_instance.task_manager.sys
        period = task_instance.period
        online_dept_id = audit_sys.online_ticket_dept_id
        deploy_ticket_dept = audit_sys.deploy_ticket_dept
        online_type = 'online'
        deploy_type = 'deploy'
        online_review = ReviewCommentModel.objects.filter(period=period, dept=online_dept_id,
                                                          server_kind=ServerKindEnum.TICKET.name,
                                                          review_type=online_type)
        deploy_review = ReviewCommentModel.objects.filter(period=period, dept=deploy_ticket_dept,
                                                          server_kind=ServerKindEnum.TICKET.name,
                                                          review_type=deploy_type)
        ticket_reviewed_types = []
        if bool(online_review):
            ticket_reviewed_types.append(online_type)
        if bool(deploy_review):
            ticket_reviewed_types.append(deploy_type)
        result[ServerKindEnum.TICKET.name] = ticket_reviewed_types

        return result


class BgAccessLogModel(Document):
    """应用后台日志"""
    bg_name = StringField(max_length=20, required=True, verbose_name='后台名称')
    user = StringField(required=True, verbose_name='请求人')
    access_dt = DateTimeField(required=True, verbose_name='请求时间')
    host = StringField(required=True, verbose_name='域名')
    url = StringField(required=True, verbose_name='请求路径')
    method = StringField(max_length=6, required=True, choices=('GET', 'POST', 'PUT', 'DELETE'), verbose_name='请求方法')
    params = DictField(verbose_name='请求参数')
    ip = StringField(max_length=15, required=True, verbose_name='请求IP')
    ua = StringField(required=True, verbose_name='请求UA')
    user_normal = BooleanField(required=False, verbose_name='是否为标准accountid', default=False)
    op_module = StringField(required=False, verbose_name='所属功能模块')
    risk_tag = BooleanField(required=False, verbose_name='是否有风险', default=False)
    meta = {
        'indexes': [
            'user', 'access_dt', 'bg_name'
        ]
    }

    @property
    def access_dt_render(self):
        return time2str(self.access_dt)

    @property
    def user_render(self):
        try:
            ums_info = UserService.query_accountid(self.user)
            return (ums_info or {}).get('name') or self.user
        except:
            return self.user


class UserRoleModifyLogModel(Document):
    bg_name = StringField(max_length=20, required=True, verbose_name='后台名称')
    user = StringField(max_length=9, required=True, verbose_name='请求人')
    modify_dt = DateTimeField(required=True, verbose_name='请求时间')
    modify_type = StringField(max_length=6, required=True, choices=('add', 'delete'), verbose_name='变更类型')
    role = StringField(required=False, verbose_name='角色名称', null=True)
    op_user = StringField(max_length=9, required=True, verbose_name='操作者')
    op_ip = StringField(max_length=15, required=False, verbose_name='操作者IP')
    op_ua = StringField(required=False, verbose_name='操作者UA')


class RolePermissionModifyLogModel(Document):
    bg_name = StringField(max_length=20, required=True, verbose_name='后台名称')
    role = StringField(required=True, verbose_name='角色名称')
    modify_dt = DateTimeField(required=True, verbose_name='变更时间')
    modify_type = StringField(max_length=6, required=True, choices=('add', 'delete', 'create'), verbose_name='变更类型')
    permission = StringField(verbose_name='权限名称')
    op_user = StringField(max_length=9, required=True, verbose_name='操作者')
    op_ip = StringField(max_length=15, required=True, verbose_name='操作者IP')
    op_ua = StringField(required=True, verbose_name='操作者UA')


class UserRoleDataModel(Document):
    bg_name = StringField(required=True, verbose_name='后台名称')
    role = StringField(required=True, verbose_name='角色名称')
    user = StringField(required=True, verbose_name='用户')
    record_date = DateField(required=True, verbose_name='统计日期')
    create_dt = DateTimeField(required=False, verbose_name='创建时间')
    risk_tag = BooleanField(required=False, verbose_name='是否有风险', default=False)
    risk_sys = ListField(ReferenceField(AuditSysModel), default=[], verbose_name='有风险业务线')
    dept_name = StringField(required=False, verbose_name='部门名称', null=True)
    meta = {
        'verbose_name': '应用后台账号',
        "auto_create_index": True,
        "index_background": True,
        "indexes": [
            'bg_name',
            'record_date',
            'create_dt',
            'dept_name',
        ]
    }


class UserSupplementInfo(Document):
    accountid = StringField(required=True, verbose_name='accountid', unique=True)
    name = StringField(required=True, verbose_name='姓名')
    email = StringField(required=True, verbose_name='邮箱')
    create_time = DateTimeField(required=True, verbose_name='创建时间')
    update_time = DateTimeField(required=True, verbose_name='更新时间')
    meta = {
        'collection': 'user_supplement_info',
        'verbose_name': '补充用户信息'
    }

    @classmethod
    def user_info(cls):
        result = {}
        queryset = cls.objects.values_list('accountid', 'name')
        for item in queryset:
            accountid, name = item
            result[accountid] = {'name': name, 'accountid': accountid}
        return result


class DbUserRoleModel(Document):
    """
    数据库用户角色信息
    """
    user = StringField(required=True, verbose_name='用户')  # 邮箱前缀
    role = StringField(required=True, verbose_name='角色名称', null=True)
    db_node = StringField(required=False, verbose_name='db_node', null=True)
    server_name = StringField(required=False, verbose_name='机器名称')
    db_name = StringField(required=False, verbose_name='数据库名称', null=True)
    record_date = DateField(required=True, verbose_name='统计日期')
    create_dt = DateTimeField(required=False, verbose_name='创建日期', null=True)
    risk_tag = BooleanField(required=False, verbose_name='是否有风险', default=False)
    risk_sys = ListField(ReferenceField(AuditSysModel), verbose_name='有风险业务线', default=[])
    dept_name = StringField(required=False, verbose_name='部门名称', null=True)
    meta = {
        'collection': 'db_user_role',
        'verbose_name': '数据库用户信息',
        "auto_create_index": True,
        "index_background": True,
        'indexes': [
            'user',
            'record_date',
            'db_node',
            'server_name',
            'create_dt',
            'dept_name'
        ]
    }


class RolePermissionData(Document):
    bg_name = StringField(max_length=20, required=True, verbose_name='后台名称')
    role = StringField(required=True, verbose_name='角色名称')
    permission = StringField(verbose_name='权限key')
    record_date = DateField(required=True, verbose_name='统计日期')
    create_dt = DateTimeField(required=False, verbose_name='创建时间')


class EmployeePositionChangeDataModel(Document):
    employee_id = StringField(max_length=10, required=True, verbose_name='工号')
    accountid = StringField(required=True, verbose_name='用户id')
    name = StringField(required=True, verbose_name='姓名')
    title_before = StringField(required=True, verbose_name='变更前职位')
    title_after = StringField(required=True, verbose_name='变更后职位')
    department_before = StringField(required=True, verbose_name='变更前部门')
    department_after = StringField(required=True, verbose_name='变更后部门')
    modify_dt = DateTimeField(required=True, verbose_name='变更时间')
    action = StringField(required=False, verbose_name='变更类型')

    @classmethod
    def get_accountid_by_time_range(cls, start_time, end_time):
        return list(cls.objects.filter(
            modify_dt__lt=end_time,
            modify_dt__gte=start_time
        ).values_list('accountid').distinct('accountid'))


class UserAccountDataModel(Document):
    bg_name = StringField(max_length=20, required=True, verbose_name='后台名称')
    user_id = StringField(required=True, verbose_name='用户ID')
    accountid = StringField(required=True, verbose_name='accountid')
    create_date = DateField(required=True, verbose_name='创建日期')
    update_date = DateField(required=True, verbose_name='更新日期')
    meta = {
        'verbose_name': '自用user与accountid映射关系表',
        'indexes': [
            {'fields': ('bg_name', 'user_id'), 'unique': True}
        ]
    }

    @classmethod
    def get_accountid_by_user(cls, bg_name, user_id):
        if not user_id:
            return None
        accountid = cls.objects.filter(
            bg_name=bg_name, user_id=str(user_id)
        ).values_list('accountid').first()
        return accountid

    @classmethod
    def get_user_map(cls, bg_name):
        result = {}
        if not bg_name:
            return result
        queryset = cls.objects.filter(bg_name=bg_name).values_list('user_id', 'accountid')
        for item in queryset:
            user, accountid = item
            result[user] = accountid
        return result


class ReviewCommentModel(Document):
    """
    审阅意见
    """
    task = ReferenceField(AuditTaskModel, verbose_name='审阅任务', required=False, null=True)
    dept = StringField(required=False, verbose_name='部门', null=True)
    period = StringField(required=False, verbose_name='周期', null=True)  # dept 和 period配合使用, 用于存储上线单部分数据
    user = StringField(required=True, verbose_name='审阅人')
    server_kind = StringField(required=True, verbose_name='审阅页类型', choices=ServerKindEnum.choices(),
                              default=ServerKindEnum.APP)
    review_type = StringField(required=True, verbose_name='数据类型', choices=('perm', 'log', 'online', 'deploy'))
    created_time = DateTimeField(required=True, verbose_name='审阅时间')
    content = StringField(required=True, verbose_name='审阅内容')
    record_id = StringField(required=False, verbose_name='单记录标识')
    record_desc = StringField(required=False, verbose_name='单记录描述')
    meta = {
        'collection': 'review_comment',
        'verbose_name': '审阅意见',
        "auto_create_index": True,
        "index_background": True,
        "indexes": [
            ('task', 'server_kind', 'review_type', 'user', 'record_id')
        ]
    }

    @classmethod
    def get_review_content(cls, server_kind, review_type, record_ids, task=None, dept=None, period=None):
        result = {}
        queryset = cls.objects.filter(
            server_kind=server_kind,
            review_type=review_type,
            record_id__in=record_ids,
        )
        if task:
            queryset = queryset.filter(task=task)
        else:
            queryset = queryset.filter(dept=dept, period=period)
        for qs in queryset:
            result[qs.record_id] = qs.content
        return result

    @classmethod
    def get_reviewed_record_ids(cls, task, server_kind, review_type):
        record_ids = list(cls.objects.filter(task=task,
                                             server_kind=server_kind,
                                             review_type=review_type).distinct('record_id'))
        return record_ids

    @classmethod
    def has_reviewed(cls, filter_params):
        exists = cls.objects.filter(**filter_params).first()
        return bool(exists)

    @property
    def user_render(self):
        return UserService.get_user_name(self.user)

    @property
    def created_time_render(self):
        return time2str(self.created_time)


class TaskMessageBoardModel(Document):
    """
    留言板
    """
    task = ReferenceField(AuditTaskModel, verbose_name='审阅任务', required=False)
    dept = StringField(required=False, verbose_name='部门', null=True)
    period = StringField(required=False, verbose_name='周期', null=True)  # dept 和 period配合使用, 用于存储上线单部分数据
    user = StringField(required=True, verbose_name='留言用户')
    server_kind = StringField(required=True, verbose_name='审阅页类型', choices=ServerKindEnum.choices(),
                              default=ServerKindEnum.APP)
    review_type = StringField(required=True, verbose_name='数据类型', choices=('perm', 'log', 'online', 'deploy'))
    created_time = DateTimeField(required=True, verbose_name='创建时间')
    content = StringField(required=True, verbose_name='留言内容')
    meta = {
        'collection': 'task_message_board',
        'verbose_name': '留言板',
        'indexes': [
            ('task', 'server_kind', 'review_type')
        ]
    }

    @property
    def user_render(self):
        return UserService.get_user_name(self.user)

    @property
    def created_time_render(self):
        return time2str(self.created_time)


class RiskUserModel(Document):
    """
    用户异常原因, 用来存储权限相容矩阵、离职用户异常原因等
    """
    audit_sys = ReferenceField(AuditSysModel, required=True, verbose_name='业务线')
    user = StringField(required=True, verbose_name='用户accountid')
    record_date = DateField(required=True, verbose_name='记录日期')
    matrix_risk = StringField(required=False, null=True, verbose_name='权限兼容矩阵异常说明')
    staff_risk = StringField(required=False, null=True, verbose_name='是否离职异常')
    no_use_risk = StringField(required=False, null=True, verbose_name='长期未使用异常')
    last_remind = DateTimeField(required=False, verbose_name='上次提示时间')
    meta = {
        'collection': 'risk_user',
        'verbose_name': '业务异常用户',
        'indexes': [
            'audit_sys',
            'user',
            {'fields': ('audit_sys', 'user', 'record_date'), 'unique': True},
        ]
    }

    @classmethod
    def get_risk_users(cls, audit_sys, date):
        risk_users = list(cls.objects.filter(
            audit_sys=audit_sys,
            record_date=date
        ).values_list('user').distinct('user'))
        return risk_users

    @property
    def risk_reason(self):
        risk_list = filter(None, [self.matrix_risk, self.staff_risk])
        return ';'.join(risk_list)

    @classmethod
    def update_risk_user(cls, user, audit_sys, risk_params: dict):
        """
        更新用户异常信息, 一天更新一次
        """
        risk_day = time_util.yesterday()
        if not risk_params or not any(risk_params.values()):
            return
        try:
            instance = cls.objects.get(user=user, audit_sys=audit_sys, record_date=risk_day)
            instance.update(**risk_params)
            instance.save()
        except Exception as e:
            risk_user = {}
            risk_user['user'] = user
            risk_user['audit_sys'] = audit_sys
            risk_user['record_date'] = risk_day
            risk_user.update(risk_params)
            cls(**risk_user).save()

    @classmethod
    def update_no_risk_users(cls, users, audit_sys):
        try:
            cls.objects.filter(audit_sys=audit_sys, user__in=users).delete()
        except:
            pass


class JobTransferRiskModel(Document):
    """
    转岗风险结果集记录
    """
    task = ReferenceField(AuditTaskModel, verbose_name='关联任务', required=True)
    accountid = ListField(required=False, verbose_name='accountid列表', null=True)
    email = ListField(required=False, verbose_name='邮箱前缀列表', null=True)
    created_time = DateTimeField(required=True, verbose_name='创建时间')
    update_time = DateTimeField(required=True, verbose_name='更新时间')
    meta = {
        'collection': 'job_transfer_risk',
        'verbose_name': '转岗风险',
        'indexes': [
            'task'
        ]
    }

    @classmethod
    def get_user_by_task(cls, task):
        result = {
            'accountids': [],
            'emails': []
        }
        try:
            instance = cls.objects.get(task=task)
            result['accountids'] = instance.accountid
            result['emails'] = instance.email
        except:
            return result

    @classmethod
    def save_risk(cls, task, accountids, emails):
        now = datetime.datetime.now()
        try:
            instance = cls.objects.get(task=task)
            instance.accountid = accountids
            instance.email = emails
            instance.update_time = now
            instance.save()
        except:
            cls(task=task,
                accountid=accountids,
                email=emails,
                created_time=now,
                update_time=now
                ).save()


class MysqlLogModel(Document):
    """
    数据库日志
    """
    source_id = StringField(required=True, verbose_name='原始id', unique=True)
    server_name = StringField(required=False, verbose_name='服务器名称', null=True)
    db_node = StringField(required=False, verbose_name='数据库域名', null=True)
    db_name = StringField(required=True, verbose_name='数据库名称')
    user = StringField(required=True, verbose_name='用户名称')
    sqltext = StringField(required=True, verbose_name='执行sql')
    cmd_source = StringField(required=False, server_name='命令来源')
    time = StringField(required=True, verbose_name='操作时间')
    hit_patterns = ListField(ReferenceField(RegexPatternModel), verbose_name='正则规则', required=False)
    ### 抽样时添加
    hit_rule_atoms = ListField(ReferenceField(RuleAtomModel), verbose_name='命中策略原子', required=False)
    risk_tag = BooleanField(required=False, verbose_name='是否有风险', default=False)
    meta = {
        'collection': 'mysql_log',
        'verbose_name': '数据库日志',
        'indexes': [
            'server_name',
            'db_node',
            'user',
            'time'
        ]
    }

    @property
    def user_render(self):
        user_id = str(self.user)
        try:
            if user_id.isdigit():
                account_id = user_id
                user_info = UserService.query_accountid(account_id)
            else:
                user_info = UserService.get_user_by_email(user_id)
            return (user_info or {}).get('name')
        except Exception as e:
            return user_id


class LogSampleModel(Document):
    """
    日志抽样结果
    """
    task = ReferenceField(AuditTaskModel, required=True, verbose_name='对应任务')
    server_kind = StringField(required=True, verbose_name='日志类型', choices=ServerKindEnum.choices(),
                              default=ServerKindEnum.APP)
    final_sample = ListField(required=False, verbose_name='最终样品', null=True)
    created_time = DateTimeField(required=True, verbose_name='创建时间')
    meta = {
        'verbose_name': '日志抽样结果',
        'collection': 'log_sample',
        'indexes': [
            ('task', 'server_kind')
        ]
    }

    @classmethod
    def save_log(cls, task_id, server_kind, final_sample):
        try:
            instance = cls.objects.get(task=task_id, server_kind=server_kind)
            instance.delete()
        except:
            pass
        now = datetime.datetime.now()
        LogSampleModel(task=task_id,
                       server_kind=server_kind,
                       final_sample=final_sample,
                       created_time=now).save()


class OnlineTicketModel(Document):
    """
    上线单
    """
    ticket_id = StringField(required=True, verbose_name='上线单id', unique=True)
    ticket_type = StringField(required=True, verbose_name='类型')
    commit_id = StringField(required=True, verbose_name='commit_id')
    submit_time = DateTimeField(required=True, verbose_name='提交时间')
    project = StringField(required=True, verbose_name='项目')
    change_detail = StringField(required=True, verbose_name='变更内容')
    influence = StringField(required=True, verbose_name='影响范围')
    submitter = ListField(required=True, verbose_name='提单人员', null=True)
    developer = ListField(required=False, verbose_name='开发人员')
    demander = ListField(required=False, verbose_name='需求方', null=True)
    tester = ListField(required=False, verbose_name='测试人员')
    reviewer = ListField(required=False, verbose_name='reviewer')
    header = ListField(required=False, verbose_name='负责人')
    director = ListField(required=False, verbose_name='主管/总监')
    deployer = ListField(required=False, verbose_name='部署人员')
    cur_step = StringField(required=True, verbose_name='当前状态')
    status = StringField(required=True, verbose_name='状态')
    dept_id = StringField(required=True, verbose_name='所属组')
    meta = {
        'collection': 'online_ticket',
        'verbose_name': '上线单',
        'indexes': [
            'ticket_id', 'submit_time', 'project', 'developer', 'deployer', 'dept_id'
        ]
    }

    @staticmethod
    def gen_ticket_url(ticket_id):
        return f'https://www.example.com/ticket_link/{ticket_id}'

    @property
    def ticket_id_render(self):
        ticket_url = self.gen_ticket_url(self.ticket_id)
        return f'<a href="{ticket_url}" target="_blank">{self.ticket_id}</a>'

    @property
    def submit_time_render(self):
        return time2str(self.submit_time)

    @staticmethod
    def pick_names(users):
        return ';'.join([x['name'] for x in users if 'name' in x])

    @property
    def developer_render(self):
        return self.pick_names(self.developer)

    @property
    def demander_render(self):
        return self.pick_names(self.demander)

    @property
    def tester_render(self):
        return self.pick_names(self.tester)

    @property
    def reviewer_render(self):
        return self.pick_names(self.reviewer)

    @property
    def header_render(self):
        return self.pick_names(self.header)

    @property
    def director_render(self):
        return self.pick_names(self.director)

    @property
    def deployer_render(self):
        return self.pick_names(self.deployer)

    @property
    def submitter_render(self):
        return self.pick_names(self.submitter)


class DeployTicketModel(Document):
    """
    部署行为记录,
    """
    source_id = StringField(required=True, verbose_name='来源ID', unique=True)
    commit_id = StringField(required=True, verbose_name='commit_id')
    deployer = StringField(required=True, verbose_name='部署人')
    project = StringField(required=True, verbose_name='项目')
    desc = StringField(required=True, verbose_name='部署说明')
    reason = StringField(required=True, verbose_name='部署原因')
    deploy_time = DateTimeField(required=True, verbose_name='部署时间')
    dept = StringField(required=True, verbose_name='部门')
    risk = BooleanField(required=False, verbose_name='是否有风险')
    risk_reason = StringField(required=False, verbose_name='风险原因', null=True)
    ticket_id = StringField(required=False, verbose_name='上线单', null=True)
    appkey = StringField(required=False, verbose_name='appkey', null=True)
    wos_url = StringField(required=False, verbose_name='工单关闭链接', null=True)
    meta = {
        'collection': 'deploy_ticket',
        'verbose_name': '部署行为记录',
        'indexes': [
            'commit_id', 'deployer', 'project', 'deploy_time', 'dept'
        ]
    }

    @property
    def deploy_time_render(self):
        return time2str(self.deploy_time)

    @staticmethod
    def gen_ticket_url(ticket_id):
        return f'https://www.example.com/ticket_link/{ticket_id}'

    @property
    def ticket_id_render(self):
        if self.ticket_id:
            ticket_url = self.gen_ticket_url(self.ticket_id)
            return f'<a href="{ticket_url}" target="_blank">{self.ticket_id}</a>'
        elif self.wos_url:
            show_id = self.wos_url.split('/')[-1]
            return f'<a href="{self.wos_url}" target="_blank">{show_id}</a>'
        return '-'


class NewReviewCommentModel(Document):
    """
    新审阅意见
    """
    task = ReferenceField(AuditTaskModel, verbose_name='审阅任务', required=False, null=True)
    dept = StringField(required=False, verbose_name='部门', null=True)
    period = StringField(required=False, verbose_name='周期', null=True)  # dept 和 period配合使用, 用于存储上线单部分数据
    user = StringField(required=True, verbose_name='审阅人')
    review_type = StringField(required=True, verbose_name='审阅类型', choices=ReviewTypeEnum.choices(),
                               default=ReviewTypeEnum.APP)
    created_time = DateTimeField(required=True, verbose_name='审阅时间')
    content = StringField(required=True, verbose_name='审阅内容')
    single_id = StringField(required=False, verbose_name='单记录标识')
    single_desc = StringField(required=False, verbose_name='单记录描述')
    meta = {
        'collection': 'new_review_comment',
        'verbose_name': '审阅意见',
        "auto_create_index": True,
        "index_background": True,
        "indexes": [
            ('task', 'review_type', 'created_time', 'user', 'single_id')
        ]
    }

    @classmethod
    def expand_task_info(cls, task_id, review_type):
        task_obj = AuditTaskModel.objects.get(id=task_id)
        if review_type not in [
            ReviewTypeEnum.TICKET.name,
            ReviewTypeEnum.ONLINE_TICKET.name,
            ReviewTypeEnum.DEPLOY_TICKET.name
        ]:
            return {'task': task_obj.id, 'review_type': review_type}
        else:
            result = {'review_type': review_type, 'period': task_obj.period}
            if review_type == ReviewTypeEnum.DEPLOY_TICKET.name:
                result['dept'] = task_obj.task_manager.sys.deploy_ticket_dept
            else:
                result['dept'] = task_obj.task_manager.sys.online_ticket_dept_id
            return result

    @classmethod
    def get_single_review_content(cls, task_id, review_type, single_ids):
        """
        获取个人审阅意见
        """
        if not single_ids:
            return {}
        result = {}
        task_filter = cls.expand_task_info(task_id, review_type)
        task_filter['single_id__in'] = single_ids
        queryset = cls.objects.filter(**task_filter)
        for qs in queryset:
            qs_data = qs._data
            single_id = qs.single_id
            result[single_id] = qs_data['content']
        return result

    @classmethod
    def get_review_status(cls, task_id):
        """
        获取task的审阅状态
        """
        task_obj = AuditTaskModel.objects.get(id=task_id)
        whole_review_types = [
            ReviewTypeEnum.APP.name,
            ReviewTypeEnum.SYS_DB.name,
            ReviewTypeEnum.TICKET.name
        ]
        review_types1 = cls.objects.filter(task=task_obj.id, single_id=None,
                                           review_type__in=whole_review_types).distinct('review_type')
        dept = task_obj.task_manager.sys.online_ticket_dept_id
        period = task_obj.period
        review_types2 = cls.objects.filter(dept=dept, period=period, single_id=None,
                                           review_type__in=whole_review_types).values_list('review_type')
        review_types = list(review_types1) + list(review_types2)

        reviewed_status = {}
        for rt in whole_review_types:
            reviewed_status[rt] = False
            if rt in review_types:
                reviewed_status[rt] = True
        return reviewed_status

    @classmethod
    def get_reviewed_single_ids(cls, task, review_type):
        single_ids = list(cls.objects.filter(task=task,
                                             review_type=review_type).distinct('single_id'))
        single_ids = list(filter(None, single_ids))
        return single_ids

    @classmethod
    def has_reviewed(cls, task, user, review_type):
        """
        判定是否完成审阅
        """
        if review_type not in [
            ReviewTypeEnum.APP.name,
            ReviewTypeEnum.SYS_DB.name,
            ReviewTypeEnum.TICKET.name
        ]:
            raise Exception(f'invalid params review_type({review_type})')
        expand_filter = cls.expand_task_info(task, review_type)
        expand_filter['user'] = user
        expand_filter['single_id'] = None
        exists = cls.objects.filter(**expand_filter).first()
        return bool(exists)

    @property
    def user_render(self):
        return UserService.get_user_name(self.user)

    @property
    def created_time_render(self):
        return time2str(self.created_time)

    @classmethod
    def can_review(cls, user_email, task, review_type):
        """
        判断能否审阅, 是否是审阅人及是否已经完成审阅
        """
        user_info = UserService.get_user_by_email(user_email)
        accountid = user_info.get('accountid')
        if not accountid:
            return False, '请重新登录'
        task_obj = AuditTaskModel.objects.get(id=task)
        if not task_obj:
            return False, '信息不存在'
        audit_sys_id = task_obj.task_manager.sys.id
        review_groups = [
            [ReviewTypeEnum.APP.name, ReviewTypeEnum.APP_LOG.name],
            [ReviewTypeEnum.SYS_DB.name, ReviewTypeEnum.SYS_DB_LOG.name],
            [ReviewTypeEnum.TICKET.name, ReviewTypeEnum.ONLINE_TICKET.name, ReviewTypeEnum.DEPLOY_TICKET.name]
        ]
        review_type_kind = None
        for rg in review_groups:
            if review_type in rg:
                review_type_kind = rg[0]
        if not review_type_kind:
            return False, '审阅类型错误'
        if not AuditSysModel.is_auditor(audit_sys_id, review_type_kind, accountid):
            return False, '非该类型审阅人'
        if cls.has_reviewed(task, user_email, review_type_kind):
            return False, '审阅人该审阅已完成'
        return True, None


class NewMessageBoardModel(Document):
    """
    新留言板
    """
    task = ReferenceField(AuditTaskModel, verbose_name='审阅任务', required=False)
    dept = StringField(required=False, verbose_name='部门', null=True)
    period = StringField(required=False, verbose_name='周期', null=True)
    user = StringField(required=True, verbose_name='留言用户')
    review_type = StringField(required=True, verbose_name='审阅类型', choices=MessageBoardEnum.choices(),
                               default=MessageBoardEnum.APP.name)
    created_time = DateTimeField(required=True, verbose_name='创建时间')
    content = StringField(required=True, verbose_name='留言内容')
    meta = {
        'collection': 'new_task_message_board',
        'verbose_name': '留言板',
        "auto_create_index": True,
        "index_background": True,
        'indexes': [
            'created_time',
            'task',
            'review_type',
            'created_time',
            {'fields': ('dept', 'period')}
        ]
    }

    @property
    def user_render(self):
        return UserService.get_user_name(self.user)

    @property
    def created_time_render(self):
        return time2str(self.created_time)


class TicketApproveModel(Document):
    environment = StringField(required=True, verbose_name='环境')
    release = StringField(required=True, verbose_name='发布系统')
    project = ListField(required=True, verbose_name='项目名称')
    reason = StringField(required=True, verbose_name='关闭原因')
    time_long = StringField(required=True, verbose_name='关闭时间规格')
    submitter = DictField(required=True, verbose_name='关闭人信息')
    reviewer = ListField(required=True, verbose_name='审批人')
    start_time = DateTimeField(required=True, verbose_name='开始时间')
    end_time = DateTimeField(required=True, verbose_name='结束时间')
    wos_url = StringField(required=True, verbose_name='工单url')

    meta = {
        'collection': 'ticket_approve',
        'verbose_name': '工单审批关闭-记录',
        "auto_create_index": True,
        "index_background": True,
        'indexes': [
            'start_time',
            'end_time',
            'project'
        ]
    }
