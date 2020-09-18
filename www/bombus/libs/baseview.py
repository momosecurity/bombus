# -*- coding:utf-8 -*-

"""
self-defined BaseViewSet
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

from mongoengine import DateTimeField, ListField
from rest_framework import status
from rest_framework.mixins import (CreateModelMixin, DestroyModelMixin,
                                   UpdateModelMixin)
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ReadOnlyModelViewSet

from core.utils import get_email_prefix


class GetViewSet(ReadOnlyModelViewSet):
    """
    基础ViewSet
    1. 提供表单数据填充: _get_auto_data
    2. 记录操作日志:
    3. show_columns: 下发列表页要展示的字段;
    4. form_rule: 设置更新form的是否必填
    """
    show_column_keys = []
    exclude_column_keys = []
    extra_show_columns = {}
    filter_fields = {}
    form_rule_keys = []

    def get_show_columns(self):
        """
        获取展示的columns数据
        """
        show_columns = {}
        model = self.serializer_class.Meta.model
        for column_key in self.show_column_keys:
            if column_key in self.exclude_column_keys:
                continue
            if column_key in model._fields:
                verbose_name = getattr(getattr(model, column_key), 'verbose_name', None)
            else:
                verbose_name = self.extra_show_columns.get(column_key)
            column_key_render = column_key + '_render'
            show_key = column_key
            if hasattr(model, column_key_render):
                show_key = column_key_render
            show_columns[show_key] = verbose_name
        return show_columns

    def get_form_rule(self):
        """
        获取表达验证规则
        """
        if not self.form_rule_keys:
            return {}

        form_rule = {}
        model = self.serializer_class.Meta.model
        for rule_key in self.form_rule_keys:
            field = getattr(model, rule_key, None)
            if not field:
                continue

            required = getattr(field, 'required')
            if not required:
                continue
            validate_list = []
            verbose_name = getattr(field, 'verbose_name')
            validate_info = {
                'required': True,
                'message': f'{verbose_name} 不能为空',
                'trigger': 'blur'
            }
            if isinstance(field, ListField):
                validate_info.update({'type': 'array', 'min': 1})
            elif isinstance(field, DateTimeField):
                validate_info.update({'type': 'date'})
            validate_list.append(validate_info)
            if getattr(field, 'min_length', None):
                validate_list.append({
                    'type': 'string',
                    'min': field.min_length,
                    'message': f'不能少于{field.min_length}个字符'
                })
            if getattr(field, 'max_length', None):
                validate_list.append({
                    'type': 'string',
                    'max': field.max_length,
                    'message': f'不能超过{field.max_length}个字符'
                })
            form_rule[rule_key] = validate_list

        return form_rule

    def build_filter_params(self, params):
        query_params = {}
        for column_name, match_pattern in self.filter_fields.items():
            query_key = column_name if not match_pattern else '__'.join([column_name, match_pattern])
            query_value = params.get(column_name)
            if query_value:
                if match_pattern == 'in':
                    if not isinstance(query_value, (tuple, list, set)):
                        query_value = [query_value]
                query_params[query_key] = query_value
        return query_params

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        model = self.serializer_class.Meta.model
        response.data['show_columns'] = self.get_show_columns()
        response.data['form_rule'] = self.get_form_rule()
        response.data['desc_map'] = {
            column_name: getattr(getattr(model, column_name), 'verbose_name', None)
            for column_name in model._fields
        }
        return response


class UpdateViewSet(CreateModelMixin,
                   UpdateModelMixin,
                   DestroyModelMixin,
                   GenericViewSet):
    """
    func:
        1. update/create
        2. record log
    """
    def record_log(self, action, request, serializer):
        """
        记录操作日志
        """
        pass

    def purge_data(self, ready_data):
        """
        序列化前做数据处理
        """
        pass

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        auto_data = self._get_auto_data(request, *args, **kwargs) or {}
        ready_data = dict(request.data, **auto_data)
        self.purge_data(ready_data)
        serializer = self.get_serializer(instance, data=ready_data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        self.record_log('update', request, serializer=serializer)
        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        auto_data = self._get_auto_data(request, *args, **kwargs) or {}
        ready_data = dict(request.data, **auto_data)
        self.purge_data(ready_data)
        serializer = self.get_serializer(data=ready_data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        self.record_log('create', request, serializer=serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        self.record_log('delete', request, serializer)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _get_auto_data(self, request, *args, **kwargs):
        """
        填充自动变更的非表单数据, 如表单有对应字段, 以填充的为准
        """
        auto_data = {}
        _fields = self.serializer_class.Meta.model._fields
        if 'last_update' in _fields:
            auto_data['last_update'] = datetime.datetime.now()
        if 'last_update_person' in _fields:
            auto_data['last_update_person'] = get_email_prefix(request.user.email)
        return auto_data


class BaseViewSet(UpdateViewSet, GetViewSet):
    pass
