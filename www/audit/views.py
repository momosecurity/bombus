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
import json
import logging

from cerberus import Validator
from django.conf import settings
from django.http import JsonResponse
from django.views import View
from mongoengine.queryset.visitor import Q
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from _collections import defaultdict
from audit.handlers.ticket_handler import OnlineTicketHandler
from audit.models import (AuditTaskModel, DeployTicketModel,
                          LogSampleModel, NewReviewCommentModel,
                          OnlineTicketModel, ReviewCommentModel,
                          SysProjectModel)
from audit.permissions import APIAuthentication, CommonDataAPIPermission
from audit.rule_handler import PeriodProxyHandler, ProxyHandler
from audit.serializers import (AuditServerSerializer, AuditSysSerializer,
                               AuditTaskSerializer, BashCommandSerializer,
                               BgAccessLogSerializer, DeployTicketSerializer,
                               MysqlLogSerializer, NewMessageBoardSerializer,
                               NewReviewCommentSerializer,
                               NonNormalUserSerializer, OnlineTicketSerializer,
                               RegexPatternSerializer, ReviewCommentSerializer,
                               RuleAtomSerializer, RuleGroupSerializer,
                               TaskManagerSerializer,
                               TaskMessageBoardSerializer)
from audit.statuschange import StatusChange
from audit.utils import RedisDataProvider, get_data_check_schema
from bombus.libs import permission_required
from bombus.libs.baseview import GetViewSet, UpdateViewSet
from bombus.libs.enums import (AuditPeriodEnum, OnOfflineStatusEnum,
                               ReviewTypeEnum, ServerKindEnum, TaskStatusEnum)
from bombus.libs.exception import FastResponse
from bombus.serializers import OperationLogSerializer
from bombus.services.user_service import UserService
from core.util import time_util
from core.utils import get_email_prefix

logger = logging.getLogger(__name__)


class BaseViewSet(GetViewSet, UpdateViewSet):
    """
    基础ViewSet
    """

    def record_log(self, action, request, serializer):
        """
        记录操作日志
        """
        log_data = {'operator': get_email_prefix(request.user.email),
                    'operate_time': datetime.datetime.now(),
                    'operate_type': action}

        clean_content = {}
        content = serializer.data

        model_fields = serializer.Meta.model._fields
        model_meta = serializer.Meta.model._meta
        for mf in model_fields:
            clean_content[mf] = content.get(mf) or ''

        id_field = model_meta['id_field']
        log_data['table_name'] = model_meta.get('verbose_name') or model_meta['collection']
        log_data['table_id'] = str(content[id_field])
        log_data['name'] = clean_content.get('name', log_data['table_id'])
        log_data['content'] = json.dumps(clean_content, ensure_ascii=False)

        log_serializer = OperationLogSerializer(data=log_data)
        log_serializer.is_valid(raise_exception=True)
        log_serializer.save()


@permission_required(settings.CA_CONF)
class AuditSysViewSet(BaseViewSet):
    """
    审计范围
    """
    serializer_class = AuditSysSerializer
    queryset = serializer_class.Meta.model.objects()
    show_column_keys = ['sys_name', 'leader', 'sys_db_auditor', 'app_auditor', 'ticket_auditor']
    filter_fields = {
        'sys_name': 'contains'
    }

    def get_queryset(self):
        query = self.build_filter_params(self.request.query_params)
        return self.serializer_class.Meta.model.objects(**query)


@permission_required(settings.CA_ASSET)
class AuditServerViewSet(ModelViewSet):
    """ 审计资产 """

    serializer_class = AuditServerSerializer
    filter_fields = {
        # column:     search_pattern
        'server_name': 'contains',
        'server_kind': '',
        'server_type': 'contains',
        'audit_sys': ''
    }
    show_columns = {
        # code_name       : show_name
        'server_name': '名称',
        'server_kind_name': '类别',
        'server_type': '类型',
        'audit_sys_name': '所属业务线',
        'audit_scope': '审计范围',
        'leader_name': '负责人',
        'auditor_name': '审阅人'
    }

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        model = self.serializer_class.Meta.model
        response.data['desc_map'] = {
            column_name: getattr(getattr(model, column_name), 'verbose_name')
            for column_name in self.filter_fields.keys()
        }
        response.data['show_columns'] = self.show_columns
        response.data['server_kind'] = [x for x in ServerKindEnum.to_seq() if x['name'] not in
                                        [ServerKindEnum.TICKET.name, ServerKindEnum.SYS_DB.name]]
        response.data['sys_list'] = AuditSysSerializer.Meta.model.get_list()
        return response

    def get_queryset(self):
        query = self.build_filter_params(self.request.query_params)
        return self.serializer_class.Meta.model.objects(**query)

    def build_filter_params(self, params):
        query_params = {}
        for column_name, match_pattern in self.filter_fields.items():
            query_key = column_name if not match_pattern else '__'.join([column_name, match_pattern])
            query_params[query_key] = params.get(column_name)

        for key, value in list(query_params.items()):
            if not value:
                del query_params[key]
        return query_params


@permission_required(settings.CA_CONF)
class RuleAtomViewSet(BaseViewSet):
    """
    策略原子
    """
    serializer_class = RuleAtomSerializer
    queryset = serializer_class.Meta.model.objects()
    show_column_keys = ['name', 'status', 'last_update', 'last_update_person']
    form_rule_keys = ['name', 'status', 'desc', 'rule_type']
    filter_fields = {
        'name': 'contains',
        'status': ''
    }

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data['rule_status'] = OnOfflineStatusEnum.to_seq()

        rule_atom_templates = []
        for enum_choice, handler in ProxyHandler.handle_mapping.items():
            name = enum_choice.name
            desc = enum_choice.desc
            configurable = getattr(handler, 'configurable', False)
            rule_atom_templates.append({'name': name, 'desc': desc, 'configurable': configurable})
        response.data['rule_atom_templates'] = rule_atom_templates

        return response

    def get_queryset(self):
        query = self.build_filter_params(self.request.query_params)
        return self.serializer_class.Meta.model.objects(**query)


@permission_required(settings.CA_CONF)
class RuleGroupViewSet(BaseViewSet):
    """
    策略组
    """
    serializer_class = RuleGroupSerializer
    queryset = serializer_class.Meta.model.objects()
    show_column_keys = ['name', 'audit_period', 'status', 'last_update', 'last_update_person']
    form_rule_keys = ['name', 'status', 'audit_period', 'atoms']
    filter_fields = {
        # column:     search_pattern
        'name': 'contains',
        'status': ''
    }

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data['rule_status'] = OnOfflineStatusEnum.to_seq()
        response.data['audit_period'] = AuditPeriodEnum.to_seq()
        return response

    def get_queryset(self):
        query = self.build_filter_params(self.request.query_params)
        return self.serializer_class.Meta.model.objects(**query)


class OperationLogViewSet(BaseViewSet):
    """
    操作日志查询
    """
    serializer_class = OperationLogSerializer
    show_column_keys = ['table_name', 'name', 'operate_type', 'operate_time', 'operator']

    filter_fields = {
        'table_id': ''
    }

    def get_queryset(self):
        query = self.build_filter_params(self.request.query_params)
        return self.serializer_class.Meta.model.objects(**query).order_by('-operate_time')


@permission_required(settings.CA_CONF)
class RegexPatternViewSet(BaseViewSet):
    """
    正则策略
    """
    serializer_class = RegexPatternSerializer
    queryset = serializer_class.Meta.model.objects()
    show_column_keys = ['name', 'regex', 'desc', 'last_update', 'last_update_person']
    form_rule_keys = ['name', 'regex', 'desc']
    filter_fields = {
        'name': 'contains',
        'regex': 'contains'
    }

    def get_queryset(self):
        query = self.build_filter_params(self.request.query_params)
        return self.serializer_class.Meta.model.objects(**query)


@permission_required(settings.CA_CONF)
class NonNormalUserViewSet(BaseViewSet):
    """
    非标准用户
    """
    serializer_class = NonNormalUserSerializer
    show_column_keys = ['name', 'audit_sys', 'server_kind', 'user', 'dept']
    form_rule_keys = ['name', 'server_kind', 'audit_sys', 'user']
    filter_fields = {
        # column:     search_pattern
        'name': 'contains',
        'server_kind': '',
        'audit_sys': '',
        'user': '',
        'dept': 'contains'
    }

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        model = self.serializer_class.Meta.model
        response.data['server_kind_list'] = ServerKindEnum.to_seq()
        response.data['sys_list'] = AuditSysSerializer.Meta.model.get_list()
        return response

    def _get_auto_data(self, request, *args, **kwargs):
        """
        填充自动变更的非表单数据, 如表单有对应字段, 以填充的为准
        """
        auto_data = super()._get_auto_data(request, *args, **kwargs)
        _fields = self.serializer_class.Meta.model._fields
        if 'user' in _fields:
            user_info = UserService.query_accountid(request.data.get('user')) or {}
            auto_data['user_email'] = (user_info.get('email') or '').replace(settings.EMAIL_SUFFIX, '')
            auto_data['user_name'] = user_info.get('name')
            auto_data['dept'] = user_info.get('dept_name')
            auto_data['deleted'] = False
        return auto_data

    def get_queryset(self):
        query = self.build_filter_params(self.request.query_params)
        query['deleted'] = False
        return self.serializer_class.Meta.model.objects(**query)


@permission_required(settings.CA_CONF)
class TaskManagerViewSet(BaseViewSet):
    """
    任务配置管理
    """
    serializer_class = TaskManagerSerializer
    show_column_keys = ['name', 'sys', 'rule_group', 'period', 'cur_period', 'follow_up_person', 'status']
    form_rule_keys = ['name', 'desc', 'rule_group', 'follow_up_person', 'status', 'sys']
    filter_fields = {
        'name': 'contains',
        'sys': '',
        'rule_group': '',
        'status': ''
    }
    extra_show_columns = {
        'period': '执行周期',
        'cur_period': '当前周期'
    }

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data['status_list'] = OnOfflineStatusEnum.to_seq()
        response.data['rule_group_list'] = RuleGroupSerializer.Meta.model.get_list()
        response.data['sys_list'] = AuditSysSerializer.Meta.model.get_list()
        return response

    def get_queryset(self):
        query = self.build_filter_params(self.request.query_params)
        return self.serializer_class.Meta.model.objects(**query)


@permission_required(settings.CA_TASK)
class AuditTaskViewSet(BaseViewSet):
    """
    任务列表
    """
    serializer_class = AuditTaskSerializer
    queryset = serializer_class.Meta.model.objects()
    show_column_keys = ['task_manager', 'created_time', 'period', 'status']

    filter_fields = {
        'task_manager': '',
        'period': 'contains',
        'status': ''
    }

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data['task_status_list'] = TaskStatusEnum.to_seq()
        response.data['task_manager_list'] = TaskManagerSerializer.Meta.model.get_list()
        return response

    def retrieve(self, request, *args, **kwargs):
        try:
            resp = super().retrieve(request, *args, **kwargs)
            resp.data['base_info'] = base_info = AuditTaskSerializer.Meta.model.get_base_info(resp.data['id'])
            sys_id = base_info['audit_sys_id']
            resp.data['visible_scope'] = AuditSysSerializer.Meta.model.visible_scope_by_person(sys_id, request.user.email)
            resp.data['pause_tip'] = AuditTaskSerializer.Meta.model.pause_tip()
            resp.data['auditors'] = AuditSysSerializer.Meta.model.server_kind_auditors(sys_id)
            resp.data['server_kind'] = ServerKindEnum.to_seq()
            resp.data['review_status'] = NewReviewCommentModel.get_review_status(resp.data['id'])
            return resp
        except Exception as e:
            raise FastResponse('抱歉, 无权限查看该数据')

    def get_queryset(self):
        query = self.build_filter_params(self.request.query_params)
        email = get_email_prefix(self.request.user.email)
        sys_on_auditor = AuditSysSerializer.Meta.model.get_sys_by_user_on_auditor(email)
        if sys_on_auditor:
            task_managers = TaskManagerSerializer.Meta.model.get_managers_by_sys(sys_on_auditor)
            query['task_manager__in'] = task_managers
            query['status__not__in'] = [TaskStatusEnum.NOT_STARTED.name, TaskStatusEnum.PAUSE.name]
        return self.serializer_class.Meta.model.objects(**query).order_by('-created_time')


class CommonDataReport(APIView):
    permission_classes = [CommonDataAPIPermission]
    authentication_classes = [APIAuthentication]

    def post(self, request, **kwargs):
        data = self.handle(request.data)
        return JsonResponse(data)

    def handle(self, origin_data):
        data_type = origin_data.get('data_type')
        datas = origin_data.get('data')
        if not datas or not data_type or not isinstance(datas, list):
            return {
                "message": "invalid params",
                "result": False
            }

        schema = get_data_check_schema(data_type)
        if schema is None:
            return {
                "message": f"invalid data_type {data_type}",
                "result": False
            }
        v = Validator(schema)
        result_datas = []
        for data in datas:
            v.validate(data)
            errors = v.errors
            if errors:
                return {
                    "message": errors,
                    "result": False
                }

            tmp = {
                'data_type': data_type,
                'source': 'http',
                'data': v.document
            }
            result_datas.append(tmp)
        if RedisDataProvider().batch_write(result_datas):
            return {
                "message": 'OK',
                "result": True
            }
        else:
            return {
                "message": 'persistence error',
                "result": False
            }


@permission_required(settings.CA_REVIEW)
class SampleLogViewSet(BaseViewSet):

    def sample_filter(self):
        sample_ids = LogSampleModel.objects. \
            filter(task=self.request.GET.get('task_id'), server_kind=self.sample_server_kind). \
            values_list('final_sample').first()
        if sample_ids:
            return {'id__in': sample_ids}
        else:
            return None


class BashCommandViewSet(SampleLogViewSet):
    """
    操作日志命令详情页
    """
    serializer_class = BashCommandSerializer
    show_column_keys = ['server_name', 'server_ip', 'client_ip', 'time', 'server_ip', 'bash_command']

    filter_fields = {
        'hit_rule_atoms': 'in',
        'user_name': '',
    }
    sample_server_kind = ServerKindEnum.SA.name

    def get_queryset(self):
        query = self.build_filter_params(self.request.query_params)
        sample_filter = self.sample_filter()
        if sample_filter:
            query.update(sample_filter)
        return self.serializer_class.Meta.model.objects(**query).order_by('-time')


class BgAccessLogViewSet(SampleLogViewSet):
    """
    应用操作日志详情页
    """
    serializer_class = BgAccessLogSerializer
    show_column_keys = ['url', 'access_dt', 'op_module',  'params', 'user', 'ip']
    filter_fields = {
        'user': '',
    }
    sample_server_kind = ServerKindEnum.APP.name

    def get_queryset(self):
        task_id = self.request.query_params.get('task_id')

        query = self.build_filter_params(self.request.query_params)
        sample_filter = self.sample_filter()
        if sample_filter:
            query.update(sample_filter)
        return self.serializer_class.Meta.model.objects(**query).order_by('-access_dt')


class MysqlLogViewSet(SampleLogViewSet):
    """
    数据库日志详情页
    """
    sample_server_kind = ServerKindEnum.DBA.name
    serializer_class = MysqlLogSerializer
    show_column_keys = ['server_name', 'db_node', 'db_name',  'sqltext', 'user', 'time']

    filter_fields = {
        'hit_rule_atoms': 'in',
        'user': '',
    }

    def get_queryset(self):
        query = self.build_filter_params(self.request.query_params)
        sample_filter = self.sample_filter()
        if sample_filter:
            query.update(sample_filter)
        return self.serializer_class.Meta.model.objects(**query).order_by('-time')


# FIXME: 这个类中很不少 Unresolved attribute reference
class TicketMixin:
    """
    上下单信息
    """
    SERVER_KIND = ServerKindEnum.TICKET.name

    def expand_task_info(self, task_id, review_type):
        """
        扩展任务信息, 上线单的审阅根据部门来, 需要将任务转化为部门 + 审阅周期
        """
        if review_type not in [
            ReviewTypeEnum.TICKET.name,
            ReviewTypeEnum.ONLINE_TICKET.name,
            ReviewTypeEnum.DEPLOY_TICKET.name
        ]:
            return {'task': task_id}

        task_instance = AuditTaskModel.objects.get(id=task_id)
        period = task_instance.period
        if review_type == ReviewTypeEnum.DEPLOY_TICKET.name:
            dept_tag = task_instance.task_manager.sys.deploy_ticket_dept
        else:
            dept_tag = task_instance.task_manager.sys.online_ticket_dept_id
        return {
            'dept': dept_tag,
            'period': period
        }

    def render_time(self, start_time, end_time):
        return {
            f'{self.TIME_COLUMN}__lt': end_time,
            f'{self.TIME_COLUMN}__gte': start_time,
        }

    def time_filter(self, base_info):
        target_date = time_util.get_extra_time(base_info['finished_time'], step=-1, rounding_level='d')
        if not target_date:
            target_date = time_util.yesterday()
        right_time = time_util.time_delta(target_date, forward='later', days=1)

        instance = AuditTaskSerializer.Meta.model.objects.get(id=base_info['id'])
        created_time = instance.created_time
        audit_period = base_info['audit_period']
        left_time, _ = PeriodProxyHandler.time_range(audit_period, created_time)
        result = self.render_time(left_time, right_time)
        return result

    def gen_default_filter(self, task_id):
        """
        处理部门及时间过滤条件
        """
        result = {}
        task_info = AuditTaskSerializer.Meta.model.get_base_info(task_id)
        if task_info:
            audit_sys = AuditSysSerializer.Meta.model.objects.get(id=task_info['audit_sys_id'])
            result[self.DEPT_COLUMN] = getattr(audit_sys, self.SYS_DEPT_KEY)
            time_filter = self.time_filter(task_info)
            result.update(time_filter)
        return result

    def get_review_content(self, record_ids):
        expand_info = self.expand_task_info(self.task_id, review_type=self.REVIEW_TYPE)
        result = ReviewCommentModel.get_review_content(server_kind=self.SERVER_KIND,
                                                       review_type=self.REVIEW_TYPE,
                                                       record_ids=record_ids,
                                                       **expand_info)
        return result


@permission_required(settings.CA_REVIEW)
class ReviewCommentViewSet(BaseViewSet, TicketMixin):
    """
    审阅意见
    """
    serializer_class = ReviewCommentSerializer
    filter_fields = {
        'task': '',
        'server_kind': '',
        'review_type': ''
    }
    show_column_keys = ['user', 'created_time', 'content']

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data['can_review'] = self.can_review(request)
        return response

    def can_review(self, request):
        email = get_email_prefix(request.user.email)
        accountid = UserService.get_user_by_email(email)['accountid']
        get_prms = request.query_params
        task_id = get_prms['task']
        server_kind = get_prms['server_kind']
        review_type = get_prms['review_type']
        task_info = AuditTaskSerializer.Meta.model.get_base_info(task_id)
        sys_id = task_info['audit_sys_id']
        is_auditor = AuditSysSerializer.Meta.model.is_auditor(sys_id, server_kind, accountid)
        if not is_auditor:
            return False
        has_reviewed_params = {
            'task': task_id,
            'user': email,
            'server_kind': server_kind,
            'review_type': review_type
        }
        if ServerKindEnum[server_kind] == ServerKindEnum.TICKET:
            task_id = has_reviewed_params.pop('task', None)
            expand_info = self.expand_task_info(task_id, review_type)
            has_reviewed_params.update(expand_info)
        has_reviewed = self.serializer_class.Meta.model.has_reviewed(has_reviewed_params)
        return not bool(has_reviewed)

    def _get_auto_data(self, request, *args, **kwargs):
        """
        填充自动变更的非表单数据, 如表单有对应字段, 以填充的为准
        """
        auto_data = {}
        _fields = self.serializer_class.Meta.model._fields
        if 'created_time' in _fields:
            auto_data['created_time'] = datetime.datetime.now()
        if 'user' in _fields:
            auto_data['user'] = get_email_prefix(request.user.email)
        return auto_data

    def get_queryset(self):
        query = self.build_filter_params(self.request.query_params)
        if ServerKindEnum[query['server_kind']] == ServerKindEnum.TICKET:
            task = query.pop('task', None)
            dept_info = self.expand_task_info(task, query['review_type'])
            query.update(dept_info)
        return self.serializer_class.Meta.model.objects(**query).order_by('created_time')

    def purge_data(self, ready_data):
        if ServerKindEnum[ready_data['server_kind']] == ServerKindEnum.TICKET:
            task = ready_data.pop('task', None)
            expand_info = self.expand_task_info(task, ready_data['review_type'])
            ready_data.update(expand_info)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        StatusChange.check_review_status(request.data.get('task'))
        return response


class TaskMessageBoardViewSet(BaseViewSet, TicketMixin):
    """
    留言板
    """
    serializer_class = TaskMessageBoardSerializer
    filter_fields = {
        'task': '',
        'server_kind': '',
        'review_type': ''
    }
    show_column_keys = ['user', 'created_time', 'content']

    def purge_data(self, ready_data):
        if ServerKindEnum[ready_data['server_kind']] == ServerKindEnum.TICKET:
            task = ready_data.pop('task', None)
            expand_info = self.expand_task_info(task, ready_data['review_type'])
            ready_data.update(expand_info)

    def _get_auto_data(self, request, *args, **kwargs):
        """
        填充自动变更的非表单数据, 如表单有对应字段, 以填充的为准
        """
        auto_data = {}
        _fields = self.serializer_class.Meta.model._fields
        if 'created_time' in _fields:
            auto_data['created_time'] = datetime.datetime.now()
        if 'user' in _fields:
            auto_data['user'] = get_email_prefix(request.user.email)
        return auto_data

    def get_queryset(self):
        query = self.build_filter_params(self.request.query_params)
        if ServerKindEnum[query['server_kind']] == ServerKindEnum.TICKET:
            task = query.pop('task', None)
            dept_info = self.expand_task_info(task, query['review_type'])
            query.update(dept_info)
        return self.serializer_class.Meta.model.objects(**query)


@permission_required(settings.CA_REVIEW)
class OnlineTicketViewSet(BaseViewSet, TicketMixin):
    """
    上线单
    """
    serializer_class = OnlineTicketSerializer
    filter_fields = {
        'task_id': '',
        'ticket_type': '',
        'user': '',
        'ticket_id': ''
    }
    show_column_keys = serializer_class.Meta.model._fields
    exclude_column_keys = ['id', 'status', 'dept_id']
    default_show_columns = [
        'ticket_id_render', 'submit_time_render', 'project',
        'ticket_type', 'change_detail', 'developer_render'
    ]
    TIME_COLUMN = 'submit_time'
    DEPT_COLUMN = 'dept_id'
    SYS_DEPT_KEY = 'online_ticket_dept_id'
    ticket_types = ['功能上线', '技术修复', '运维操作', '紧急上线']
    REVIEW_TYPE = ReviewTypeEnum.ONLINE_TICKET.name

    def fill_review_content(self, result):
        single_ids = [r['ticket_id'] for r in result]
        review_content = NewReviewCommentModel.get_single_review_content(self.task_id, self.REVIEW_TYPE, single_ids)
        for item in result:
            record_id = item['ticket_id']
            content = review_content.get(record_id) or ''
            item['review_content'] = content

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data['ticket_types'] = self.ticket_types
        response.data['default_columns'] = self.default_show_columns
        results = response.data['results']
        self.fill_review_content(results)
        response.data['results'] = results
        return response

    def get_ticket_id_filter(self, task_id):
        """ 通过部署单限定条件 获取ticketId范围 """
        deploy_filter = DeployTicketView().gen_default_filter(task_id)
        queryset = DeployTicketModel.objects.filter(**deploy_filter)
        # appkey范围过滤
        base_info = AuditTaskModel.get_base_info(task_id)
        sys_id = base_info['cnf_sys_id']
        appkeys = SysProjectModel.get_appkey_by_sys_id(sys_id)
        if appkeys:
            queryset = queryset.filter(appkey__in=appkeys)
        ticket_ids = list(queryset.distinct('ticket_id'))
        ticket_ids = list(filter(None, ticket_ids))
        return ticket_ids

    def get_queryset(self):
        query = self.build_filter_params(self.request.query_params)
        query['status__in'] = ['ready', 'done']
        if 'task_id' in query:
            self.task_id = query.pop('task_id')
            ticket_range = self.get_ticket_id_filter(self.task_id)
            query['ticket_id__in'] = ticket_range
        if 'user' in query:
            user = query.pop('user')
            query['submitter__email'] = user
        return self.serializer_class.Meta.model.objects(**query).order_by('project')


@permission_required(settings.CA_REVIEW)
class DeployTicketView(View, TicketMixin):
    """
    部署单信息
    """
    serializer_class = DeployTicketSerializer
    TIME_COLUMN = 'deploy_time'
    DEPT_COLUMN = 'dept'
    SYS_DEPT_KEY = 'deploy_ticket_dept'
    REVIEW_TYPE = ReviewTypeEnum.DEPLOY_TICKET.name

    def get_show_columns(self):
        return {
            'project': '项目',
            'commit_id': '提交id',
            'deploy_time': '部署时间',
            'reason': '原因',
            'deployer': '部署人',
            'risk_reason': '异常原因',
            'ticket_id_render': '上线单',
        }

    def render_time(self, start_time, end_time):
        return {
            f'{self.TIME_COLUMN}__lt': end_time,
            f'{self.TIME_COLUMN}__gte': start_time,
        }

    def get_online_ticket_ids(self, submitter):
        ticket_ids = OnlineTicketViewSet().get_ticket_id_filter(self.task_id)
        params = {
            'ticket_id__in': ticket_ids,
            'submitter__email': submitter,
        }
        return OnlineTicketModel.objects.filter(**params).distinct('ticket_id')

    def get(self, request, *args, **kwargs):
        get_prms = request.GET
        resp_data = {}
        resp_data['show_columns'] = self.get_show_columns()
        resp_data['results'] = []
        resp_data['count'] = 0

        page = int(get_prms.get('page') or 1)
        page_size = int(get_prms.get('page_size') or 10)
        offset = (page - 1) * page_size

        self.task_id = task_id = get_prms.get('task_id')
        self.base_info = AuditTaskSerializer.Meta.model.get_base_info(task_id)
        default_filter = self.gen_default_filter(task_id)
        if not default_filter:
            return JsonResponse(data=resp_data)

        sys_id = self.base_info['cnf_sys_id']
        appkeys = SysProjectModel.get_appkey_by_sys_id(sys_id)
        if appkeys:
            default_filter['appkey__in'] = appkeys

        deploy_list = []
        default_filter['risk'] = True
        user = get_prms.get('user')
        role = get_prms.get('role')
        commit_id = get_prms.get('commit_id')
        if user:
            roles = [x.strip() for x in (role or '').split(',')]
            if 'submitter' in roles:
                ticket_ids = self.get_online_ticket_ids(submitter=user)
                deploy_list.extend(list(DeployTicketModel.objects.filter(**default_filter, ticket_id__in=ticket_ids)))
            if 'deployer' in roles:
                deploy_list.extend(list(DeployTicketModel.objects.filter(
                    **default_filter, deployer=user, ticket_id__in=[None, ''])
                ))
        if commit_id:
            deploy_list.extend(list(DeployTicketModel.objects.filter(**default_filter, commit_id=commit_id)))

        results = self.merge_list(deploy_list)
        resp_data['count'] = len(results)
        result = self.format_result(results[offset: offset+page_size])
        self.fill_review_content(result)
        resp_data['results'] = result
        return JsonResponse(data=resp_data)

    def fill_review_content(self, result):
        record_ids = [r['commit_id'] for r in result]
        review_content = NewReviewCommentModel.get_single_review_content(self.task_id, self.REVIEW_TYPE, record_ids)
        for item in result:
            record_id = item['commit_id']
            content = review_content.get(record_id) or ''
            item['review_content'] = content

    def show_url_link(self, ticket_id, wos_url):
        if ticket_id:
            ticket_url = OnlineTicketHandler.gen_ticket_url(ticket_id)
            return f'<a href="{ticket_url}" target="_blank">{ticket_id}</a>'
        elif wos_url:
            show_id = wos_url.split('/')[-1]
            return f'<a href="{wos_url}" target="_blank">{show_id}</a>'
        return '-'

    def merge_list(self, deploy_list):
        """
        聚合列表, 获取结果
        """
        result = defaultdict(dict)
        for item in deploy_list:
            commit_id = item.commit_id
            commit_data = result[commit_id]
            commit_data['commit_id'] = commit_id
            commit_data['ticket_id'] = item.ticket_id
            commit_data['wos_url'] = item.wos_url
            commit_data['project'] = item.project
            commit_data.setdefault('reasons', set()).add(item.reason)
            commit_data.setdefault('deployers', set()).add(item.deployer)
            commit_data.setdefault('risk_reason', set()).add(item.risk_reason)
            commit_data.setdefault('deploy_times', []).append(item.deploy_time)
        ori_list = list(result.values())
        ori_list.sort(key=lambda x: x['project'])
        return ori_list

    def format_result(self, results):
        fmt_rs = []
        all_emails = []
        for res in results:
            all_emails.extend(list(res['deployers']))
        email2user = UserService.batch_get_user_by_email(all_emails)
        email2name = {k: v.get('name', ) for k, v in email2user.items()}
        for item in results:
            ticket_fmt = {}
            try:
                ticket_fmt['commit_id'] = item['commit_id']
                ticket_id = item['ticket_id']
                wos_url = item['wos_url']

                ticket_fmt['ticket_id_render'] = self.show_url_link(ticket_id, wos_url)
                ticket_fmt['project'] = item['project']
                ticket_fmt['reason'] = ';'.join(item['reasons'])
                ticket_fmt['deployer'] = '; '.join([email2name.get(x) for x in item['deployers']])
                ticket_fmt['deploy_time'] = ';  '.join([time_util.time2str(t) for t in sorted(item['deploy_times'])])
                ticket_fmt['risk_reason'] = ';  '.join(filter(None, item['risk_reason']))
                fmt_rs.append(ticket_fmt)
            except Exception as e:
                logger.exception('format user_info error for ur_info(%s)' % (ticket_fmt))
        return fmt_rs


@permission_required(settings.CA_REVIEW)
class NewReviewCommentViewSet(BaseViewSet, TicketMixin):
    """
    审阅意见
    """
    serializer_class = NewReviewCommentSerializer
    filter_fields = {
        'task': '',
        'review_type': ''
    }
    show_column_keys = ['user', 'created_time', 'content']

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data['can_review'] = self.can_review(request)
        results = response.data['results']
        single_reviews = list(filter(lambda x: x['single_id'], results))
        whole_reviews = list(filter(lambda x: not x['single_id'], results))
        response.data['single_reviews'] = single_reviews
        response.data['whole_reviews'] = whole_reviews
        return response

    def can_review(self, request):
        email = get_email_prefix(request.user.email)
        get_prms = request.query_params
        task_id = get_prms['task']
        review_type = get_prms['review_type']
        can_review, _ = self.serializer_class.Meta.model.can_review(email, task_id, review_type)
        return can_review

    def _get_auto_data(self, request, *args, **kwargs):
        """
        填充自动变更的非表单数据, 如表单有对应字段, 以填充的为准
        """
        auto_data = {}
        _fields = self.serializer_class.Meta.model._fields
        if 'created_time' in _fields:
            auto_data['created_time'] = datetime.datetime.now()
        if 'user' in _fields:
            auto_data['user'] = get_email_prefix(request.user.email)
        return auto_data

    def expand_review_type(self, review_type):
        type_list_map = {
            ReviewTypeEnum.TICKET.name: [
                ReviewTypeEnum.TICKET.name,
                ReviewTypeEnum.ONLINE_TICKET.name,
            ],
            ReviewTypeEnum.APP.name: [
                ReviewTypeEnum.APP.name,
                ReviewTypeEnum.APP_LOG.name,
            ],
            ReviewTypeEnum.SYS_DB.name: [
                ReviewTypeEnum.SYS_DB.name,
                ReviewTypeEnum.SYS_DB_LOG.name,
            ]
        }
        return type_list_map.get(review_type)

    def get_queryset(self):
        query = self.build_filter_params(self.request.query_params)
        or_filter_params = {}
        # 这里的review_type代表整体审阅的类型, 所以日志及上线单部署单类型不会传入
        if ReviewTypeEnum[query['review_type']] == ReviewTypeEnum.TICKET:
            task = query.pop('task', None)
            dept_info = self.expand_task_info(task, query['review_type'])
            query.update(dept_info)
            or_filter_params = self.expand_task_info(task, ReviewTypeEnum.DEPLOY_TICKET.name)
        origin_review_type = query.pop('review_type')
        review_type_params = {'review_type__in': self.expand_review_type(origin_review_type)}
        query_filter = Q(**query, **review_type_params)
        if or_filter_params:
            query_filter |= Q(**or_filter_params)
        return self.serializer_class.Meta.model.objects(query_filter).order_by('created_time')

    def purge_data(self, ready_data):
        task = ready_data.pop('task', None)
        expand_info = self.expand_task_info(task, ready_data['review_type'])
        ready_data.update(expand_info)

    def create(self, request, *args, **kwargs):
        user_email = get_email_prefix(request.user.email)
        _can, reason = NewReviewCommentModel.can_review(
            user_email, request.data.get('task'), request.data.get('review_type')
        )
        if not _can:
            raise FastResponse(reason)
        response = super().create(request, *args, **kwargs)
        if not request.data.get('single_id'):
            # 只有整体审阅会触发push
            StatusChange.check_review_status(request.data.get('task'))
        return response


class NewMessageBoardViewSet(BaseViewSet, TicketMixin):
    """
    留言板
    """
    serializer_class = NewMessageBoardSerializer
    filter_fields = {
        'task': '',
        'review_type': ''
    }
    show_column_keys = ['user', 'created_time', 'content']

    def purge_data(self, ready_data):
        if ReviewTypeEnum[ready_data['review_type']] == ReviewTypeEnum.TICKET:
            task = ready_data.pop('task', None)
            expand_info = self.expand_task_info(task, ready_data['review_type'])
            ready_data.update(expand_info)

    def _get_auto_data(self, request, *args, **kwargs):
        """
        填充自动变更的非表单数据, 如表单有对应字段, 以填充的为准
        """
        auto_data = {}
        _fields = self.serializer_class.Meta.model._fields
        if 'created_time' in _fields:
            auto_data['created_time'] = datetime.datetime.now()
        if 'user' in _fields:
            auto_data['user'] = get_email_prefix(request.user.email)
        return auto_data

    def get_queryset(self):
        query = self.build_filter_params(self.request.query_params)
        if ReviewTypeEnum[query['review_type']] == ReviewTypeEnum.TICKET:
            task = query.pop('task', None)
            dept_info = self.expand_task_info(task, query['review_type'])
            query.update(dept_info)
        return self.serializer_class.Meta.model.objects(**query)
