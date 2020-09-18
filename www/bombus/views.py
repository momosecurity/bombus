# -*- coding:utf-8 -*-

"""
健康检测
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
from django.http import HttpResponse, JsonResponse
from django.views import View

from bombus.auditlog_util import ReadableLog
from bombus.libs import permission_required
from bombus.libs.baseview import BaseViewSet, GetViewSet
from bombus.libs.enums import PriorityEnum, ProcessStatusEnum
from bombus.libs.exception import FastResponse
from bombus.serializers import (AppComplianceSerializer,
                                ComplianceDetailSerializer, FeatureSerializer,
                                OperationLogSerializer,
                                ProjectAuditLogEntrySerializer,
                                SettingConfSerializer)
from bombus.services.user_service import UserService

logger = logging.getLogger(__name__)


class HealthCheck(View):
    def get(self, request, *args, **kwargs):
        return HttpResponse('ok')


class UserSearch(View):
    """
    用户关键字搜索
    """
    def get(self, request, *args, **kwargs):
        email = request.GET.get('email')
        users = UserService.search_user(email)
        for user in users:
            user['email_prefix'] = user['email'].replace(settings.EMAIL_SUFFIX, '')
        return JsonResponse({'results':users})


@permission_required(settings.CA_LOG)
class AuditLogViewSet(GetViewSet):
    """
    审计日志
    """
    serializer_class = ProjectAuditLogEntrySerializer

    filter_fields = {
        'req_method': '',
        'req_path': 'contains',
        'req_user': 'contains'
    }
    show_columns = {
        # code_name       : show_name
        'req_time_render': '请求时间',
        'req_user': '操作人',
        'operation_on': '操作对象',
        'action': '动作',
        'content': '参数',
        'resp_content': '返回值'
    }

    def convert_readable_result(self, results):
        readable_results = []
        for res in results:
            readable_results.append(ReadableLog(res).fmt())
        return readable_results

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data['show_columns'] = self.show_columns
        response.data['results'] = self.convert_readable_result(response.data['results'])
        return response

    def get_queryset(self):
        query = self.build_filter_params(self.request.query_params)
        time_fmt = '%Y-%m-%d %H:%M'
        req_time_left = self.request.query_params.get('req_time_left')
        req_time_right = self.request.query_params.get('req_time_right')
        if req_time_left:
            query['req_time__gte'] = datetime.datetime.strptime(req_time_left, time_fmt)
        if req_time_right:
            query['req_time__lte'] = datetime.datetime.strptime(req_time_right, time_fmt)
        if self.request.query_params.get('req_method'):
            query.pop('req_method', None)
            query['req_method__contains'] = self.request.query_params['req_method'].upper()

        return self.serializer_class.Meta.model.objects(**query).order_by('-req_time')


class OperationLogViewSet(BaseViewSet):
    """
    操作日志查询
    """
    serializer_class = OperationLogSerializer
    show_column_keys = ['name', 'operate_type', 'operate_time', 'operator']

    filter_fields = {
        'table_id': ''
    }

    def get_queryset(self):
        query = self.build_filter_params(self.request.query_params)
        return self.serializer_class.Meta.model.objects(**query).order_by('-operate_time')


@permission_required(settings.CA_BENCH)
class FeatureViewSet(BaseViewSet):
    """
    待办跟踪
    """
    serializer_class = FeatureSerializer
    queryset = serializer_class.Meta.model.objects()
    show_column_keys = [
        'title', 'demander', 'priority', 'status',
        'expect_deadline', 'actual_deadline', 'submitter', 'implementer']
    form_rule_keys = ['title', 'desc', 'demander', 'status', 'priority', 'expect_deadline', 'implementer']
    clickable_key = 'title'
    filter_fields = {
        'id': '',
        'priority': '',
        'status': '',
    }

    def _get_auto_data(self, request, *args, **kwargs):
        """
        填充自动变更的非表单数据, 如表单有对应字段, 以填充的为准
        """
        auto_data = {}
        _fields = self.serializer_class.Meta.model._fields
        if 'submitter' in _fields:
            auto_data['submitter'] = [UserService.get_email_prefix(request.user.email)]
        return auto_data

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if ProcessStatusEnum[instance.status] == ProcessStatusEnum.FINISHED:
            raise FastResponse('已完成状态不允许删除')
        return super().destroy(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if ProcessStatusEnum[instance.status] == ProcessStatusEnum.FINISHED:
            raise FastResponse('已完成状态不允许更新')
        return super().update(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        implementer_list = list(UserService.batch_get_user_by_accountid(settings.AUDIT_USERS).values())
        for item in implementer_list:
            item['email_prefix'] = UserService.get_email_prefix(item['email'])
            item['name'] = item['name']
        response.data['priority_list'] = PriorityEnum.to_seq()
        response.data['status_list'] = ProcessStatusEnum.to_seq()
        response.data['clickable_key'] = self.clickable_key
        return response

    def get_queryset(self):
        query = self.build_filter_params(self.request.query_params)
        if 'id' in query:
            if len(query['id']) != 24:
                query.pop('id', None)
        query['deleted'] = False
        return self.serializer_class.Meta.model.objects(**query).order_by('-created_time')


@permission_required(settings.CA_BENCH)
class SettingConfViewSet(BaseViewSet):
    """
    后台配置项
    """
    serializer_class = SettingConfSerializer
    show_column_keys = ['conf_key', 'desc']

    filter_fields = {
        'conf_key': 'contains',
    }

    def get_queryset(self):
        query = self.build_filter_params(self.request.query_params)
        return self.serializer_class.Meta.model.objects(**query)


@permission_required(settings.CA_BENCH)
class AppComplianceViewSet(BaseViewSet):
    """
    APP隐私合规
    """
    serializer_class = AppComplianceSerializer
    # show_column_keys = ['']
    filter_fields = {
        'name': 'contains',
        'dept': 'contains',
        'startup_subject': 'contains',
        'app_status': 'contains'
    }
    form_rule_keys = ['name', 'dept']
    show_column_keys = serializer_class.Meta.model._fields
    exclude_column_keys = ['created_time', 'updated_time', 'deleted', 'id']

    def _get_auto_data(self, request, *args, **kwargs):
        """
        填充自动变更的非表单数据, 如表单有对应字段, 以填充的为准
        """
        auto_data = {}
        _fields = self.serializer_class.Meta.model._fields
        if 'updated_time' in _fields:
            auto_data['updated_time'] = datetime.datetime.now()
        return auto_data

    def get_queryset(self):
        query = self.build_filter_params(self.request.query_params)
        return self.serializer_class.Meta.model.objects(**query).filter(deleted=False)


@permission_required(settings.CA_BENCH)
class ComplianceDetailViewSet(BaseViewSet):
    """
    评估发现
    """
    serializer_class = ComplianceDetailSerializer
    filter_fields = {
        'app': '',
        'status': 'contains'
    }
    form_rule_keys = ['rectification_category', 'promotion_dept', 'status', 'rectification_time']
    show_column_keys = serializer_class.Meta.model._fields
    exclude_column_keys = ['created_time', 'updated_time', 'deleted', 'id']

    def _get_auto_data(self, request, *args, **kwargs):
        auto_data = {}
        _fields = self.serializer_class.Meta.model._fields
        if 'updated_time' in _fields:
            auto_data['updated_time'] = datetime.datetime.now()
        return auto_data

    def get_queryset(self):
        query = self.build_filter_params(self.request.query_params)
        return self.serializer_class.Meta.model.objects(**query).filter(deleted=False)
