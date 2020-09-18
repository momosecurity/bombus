# -*- coding:utf-8 -*-

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

from django.conf import settings
from mongoengine.queryset.visitor import Q

from bombus.libs import permission_required
from bombus.libs.baseview import GetViewSet, UpdateViewSet
from bombus.libs.enums import BooleanEnum, OnOfflineStatusEnum, SelectTypeEnum
from bombus.serializers import OperationLogSerializer
from bombus.services.user_service import UserService
from knowledge.models import (RequireModel, TagModel, TagTypeModel,
                              TagTypePropertyModel)
from knowledge.serializers import (RequireSerializer, TagSerializer,
                                   TagTypePropertySerializer,
                                   TagTypeSerializer)


class HistoryVersionViewSet(UpdateViewSet):
    """
    记录历史变更
    """

    def record_log(self, action, request, serializer):
        """
        记录操作日志
        """
        log_data = {
            'operator': UserService.get_email_prefix(request.user.email),
            'operate_time': datetime.datetime.now(),
            'operate_type': action
        }

        clean_content = {}
        content = serializer.data

        model_fields = serializer.Meta.model._fields
        model_meta = serializer.Meta.model._meta
        for mf in model_fields:
            clean_content[mf] = content.get(mf) or ''

        id_field = model_meta['id_field']
        log_data['table_name'] = model_meta.get('verbose_name') or model_meta['collection']
        log_data['table_id'] = str(content[id_field])
        log_data['name'] = clean_content.get('name') or clean_content.get('content') or log_data['table_id']
        log_data['content'] = json.dumps(clean_content, ensure_ascii=False)

        log_serializer = OperationLogSerializer(data=log_data)
        log_serializer.is_valid(raise_exception=True)
        log_serializer.save()


@permission_required(settings.CA_KNDGE)
class TagTypeViewSet(GetViewSet, HistoryVersionViewSet):
    """
    标签类型
    """
    serializer_class = TagTypeSerializer
    queryset = serializer_class.Meta.model.objects()
    show_column_keys = ['name', 'desc', 'select_type', 'required', 'opt_show', 'column_show']
    form_rule_keys = ['name', 'desc', 'select_type', 'required', 'opt_show', 'statistic_show']
    filter_fields = {
        'name': 'contains',
        'desc': 'contains',
        'opt_show': '',
    }

    def get_queryset(self):
        query = self.build_filter_params(self.request.query_params)
        return self.serializer_class.Meta.model.objects(**query)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data['boolean_list'] = BooleanEnum.to_seq()
        response.data['select_type_list'] = SelectTypeEnum.to_seq()
        return response


@permission_required(settings.CA_KNDGE)
class TagTypePropertyViewSet(GetViewSet, HistoryVersionViewSet):
    """
    标签类型属性
    """
    serializer_class = TagTypePropertySerializer
    queryset = serializer_class.Meta.model.objects()
    show_column_keys = ['name', 'desc', 'tag_type']
    form_rule_keys = ['name', 'tag_type']
    filter_fields = {
        'name': 'contains',
        'tag_type': '',
    }

    def get_queryset(self):
        query = self.build_filter_params(self.request.query_params)
        return self.serializer_class.Meta.model.objects(**query)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data['tag_type_list'] = TagTypeModel.items()
        return response


@permission_required(settings.CA_KNDGE)
class TagViewSet(GetViewSet, HistoryVersionViewSet):
    """
    标签
    """
    serializer_class = TagSerializer
    queryset = serializer_class.Meta.model.objects()
    show_column_keys = ['name', 'tag_type', 'tag_type_property', 'status']
    form_rule_keys = ['name', 'desc', 'tag_type', 'status']
    filter_fields = {
        'name': 'contains',
        'tag_type': '',
    }

    def get_queryset(self):
        query = self.build_filter_params(self.request.query_params)
        return self.serializer_class.Meta.model.objects(**query)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data['tag_type_list'] = TagTypeModel.items()
        response.data['status_list'] = OnOfflineStatusEnum.to_seq()
        response.data['type_property_map'] = TagTypePropertyModel.type_property_map()
        return response


class RequireViewSet(GetViewSet, HistoryVersionViewSet):
    """
    管理要求
    """
    serializer_class = RequireSerializer
    queryset = serializer_class.Meta.model.objects()
    show_column_keys = ['content', 'source']
    form_rule_keys = ['content', 'source']
    TYPE_PREFIX = 'type_'

    def get_queryset(self):
        queryset = self.serializer_class.Meta.model.objects.filter(
            tags__not__in=TagModel.offline_required_tags())
        query = self.build_filter_params(self.request.query_params)
        queryset = queryset.filter(**query)
        # 内容全局搜索
        content = self.request.query_params.get('content')
        if content:
            content_filter = Q(content__contains=content)
            source_filter = Q(source__contains=content)
            matched_tags = TagModel.objects.filter(name__contains=content, status=OnOfflineStatusEnum.ONLINE.name)
            tag_filter = Q(tags__in=matched_tags)
            queryset = queryset.filter(content_filter | source_filter | tag_filter)
        # 标签精确匹配
        query_tags = self.request.query_params.get('tags')
        if query_tags:
            query_tags = query_tags.split(',')
            tag_by_type = TagModel.taglist2map(query_tags)
            for type_tag in tag_by_type.values():
                tag_ids = [x['id'] for x in type_tag]
                queryset = queryset.filter(tags__in=tag_ids)
        return queryset

    def tag_info_render(self, tag_info):
        if OnOfflineStatusEnum[tag_info['status']] == OnOfflineStatusEnum.OFFLINE:
            return
        if not tag_info['ref_link']:
            return tag_info['name']
        else:
            return f"""<a href="{tag_info['ref_link']}">{tag_info['name']}</a>"""

    def default_show_columns(self, type_list):
        """下发默认显示字段"""
        show_types = [f"{self.TYPE_PREFIX}{x['id']}"
                      for x in type_list
                      if x['column_show'] != BooleanEnum.FALSE.name]
        show_columns = ['content'] + show_types
        return show_columns

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        required_types = TagTypeModel.required_types()
        compared_type_ids = {f'{self.TYPE_PREFIX}{x["id"]}'
                             for x in required_types}
        results = response.data['results']
        for item in results:
            for k, v in item.items():
                if k.startswith(self.TYPE_PREFIX):
                    tag_renders = list(filter(None, map(self.tag_info_render, v)))
                    item[k] = '\n'.join(tag_renders)
            item['lack_required'] = bool(compared_type_ids - set(item.keys()))

        response.data['type_tag_map'] = TagModel.type_tag_map()
        response.data['tag_type_list'] = type_list = TagTypeModel.items()
        response.data['status_list'] = OnOfflineStatusEnum.to_seq()
        response.data['type_property_map'] = TagTypePropertyModel.type_property_map()
        response.data['statistic'] = self.get_desc_count()
        response.data['default_columns'] = self.default_show_columns(type_list)
        expand_columns = {f"{self.TYPE_PREFIX}{x['id']}": x['name'] for x in type_list}
        response.data['show_columns'].update(expand_columns)
        for ttype in type_list:
            if BooleanEnum[ttype['required']] == BooleanEnum.TRUE:
                rule = {
                    'required': True,
                    'message': f'{ttype["name"]} 不能为空',
                    'trigger': 'blur'
                }
                if SelectTypeEnum[ttype['select_type']] == SelectTypeEnum.MULTI:
                    rule.update({'type': 'array', 'min': 1})
                response.data['form_rule'][f'{self.TYPE_PREFIX}{ttype["id"]}'] = [rule]
        return response

    def get_desc_count(self):
        """
        获取统计数量
        """
        require_desc = RequireModel.describe()
        result = [{'desc': '知识总数', 'count': require_desc['total_count']}]
        tag_desc = TagModel.type_count()
        result.extend(tag_desc)
        return result
