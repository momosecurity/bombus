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

import logging
from collections import defaultdict

from mongoengine import Document, ListField, ReferenceField, StringField
from bombus.libs.enums import BooleanEnum, OnOfflineStatusEnum, SelectTypeEnum

logger = logging.getLogger(__name__)


class TagTypeModel(Document):
    """ 标签类型 """
    name = StringField(required=True, verbose_name='坐标系名称')
    desc = StringField(required=True, verbose_name='描述')
    select_type = StringField(required=True, verbose_name='选择类型',
                              choices=SelectTypeEnum.choices(), default=SelectTypeEnum.SINGLE)
    required = StringField(required=True, verbose_name='是否必填',
                           choices=BooleanEnum.choices(), default=BooleanEnum.TRUE)
    opt_show = StringField(required=True, verbose_name='地图显示筛选',
                           choices=BooleanEnum.choices(), default=BooleanEnum.TRUE)
    statistic_show = StringField(required=True, verbose_name='地图统计总数',
                                 choices=BooleanEnum.choices(), default=BooleanEnum.TRUE, null=True)
    column_show = StringField(required=False, verbose_name='列默认展示',
                              choices=BooleanEnum.choices(), default=BooleanEnum.TRUE, null=True)
    meta = {
        'collection': 'tag_type',
        'verbose_name': '标签类型',
        'indexes': [
            'name'
        ],
    }

    @classmethod
    def statistic_types(cls):
        result = []
        queryset = cls.objects.filter(statistic_show=BooleanEnum.TRUE.name).all()
        for qs in queryset:
            item_data = qs._data
            item_data['id'] = str(item_data['id'])
            result.append(item_data)
        return result

    @classmethod
    def required_types(cls):
        result = []
        queryset = cls.objects.filter(required=BooleanEnum.TRUE.name).all()
        for qs in queryset:
            item_data = qs._data
            item_data['id'] = str(item_data['id'])
            result.append(item_data)
        return result

    @classmethod
    def items(cls):
        queryset = cls.objects.all()
        infos = [qs._data for qs in queryset]
        for item in infos:
            item['id'] = str(item['id'])
        return infos

    @property
    def opt_show_render(self):
        return BooleanEnum[self.opt_show].desc

    @property
    def required_render(self):
        return BooleanEnum[self.required].desc

    @property
    def select_type_render(self):
        return SelectTypeEnum[self.select_type].desc

    @property
    def column_show_render(self):
        value = self.column_show
        if value is None:
            value = BooleanEnum.TRUE.name
        return BooleanEnum[value].desc


class TagTypePropertyModel(Document):
    """
    标签类型属性
    """
    meta = {
        'collection': 'tag_type_property',
        'verbose_name': '标签类型属性',
    }

    name = StringField(required=True, verbose_name='属性名称')
    desc = StringField(required=True, verbose_name='描述')
    tag_type = ReferenceField(TagTypeModel, required=True, verbose_name='所属坐标系')

    @property
    def tag_type_render(self):
        try:
            return self.tag_type.name
        except:
            return self.tag_type or ''

    @classmethod
    def type_property_map(cls):
        result = defaultdict(list)
        for item in cls.objects.all():
            type_id = str(item.tag_type.id)
            result[type_id].append({'id': str(item.id), 'name':item.name})
        return result


class TagModel(Document):
    """
    标签
    """
    meta = {
        'collection': 'tag',
        'verbose_name': '标签',
    }

    name = StringField(required=True, verbose_name='名称')
    desc = StringField(required=True, verbose_name='描述')
    ref_link = StringField(required=False, verbose_name='参考链接', null=True)
    status = StringField(required=True, verbose_name='状态',
                         choices=OnOfflineStatusEnum.choices(), default=OnOfflineStatusEnum.ONLINE)
    tag_type = ReferenceField(TagTypeModel, required=True, verbose_name='所属坐标系')
    tag_type_property = ReferenceField(TagTypePropertyModel, verbose_name='属性', required=False, null=True)

    @classmethod
    def type_count(cls):
        result = []
        queryset = cls.objects.filter(status=OnOfflineStatusEnum.ONLINE.name)
        statistic_types = TagTypeModel.statistic_types()
        for st in statistic_types:
            type_name = st['name']
            count = queryset.filter(tag_type=st['id']).count()
            result.append({'desc': type_name, 'count': count})
        return result

    @classmethod
    def offline_required_tags(cls):
        """
        禁用状态的必选标签
        """
        required_types = TagTypeModel.required_types()
        type_ids = [x['id'] for x in required_types]
        tag_ids = list(cls.objects.filter(status=OnOfflineStatusEnum.OFFLINE.name,
                                          tag_type__in=type_ids).values_list('id'))
        return tag_ids

    @classmethod
    def taglist2map(cls, tags):
        if tags and isinstance(tags[0], str):
            tags = cls.objects.filter(id__in=tags)
        result = defaultdict(list)
        for tag in tags:
            type_id = str(tag.tag_type.id)
            result[f'type_{type_id}'].append({
                'id': str(tag.id),
                'name': tag.name,
                'ref_link': tag.ref_link,
                'status': tag.status
            })
        return result

    @classmethod
    def taglist2map_render(cls, tags):
        result = defaultdict(list)
        queryset = cls.objects.filter(id__in=tags).all()
        for qs in queryset:
            type_id = str(qs.tag_type.id)
            result[type_id].append(qs.name)
        return {k: ';'.join(v) for k, v in result.items()}

    @classmethod
    def type_tag_map(cls):
        result = defaultdict(list)
        queryset = cls.objects.filter(status=OnOfflineStatusEnum.ONLINE.name).all()
        for qs in queryset:
            type_id = str(qs.tag_type.id)
            result[type_id].append({'id': str(qs.id), 'name': qs.name})
        return result

    @property
    def tag_type_render(self):
        try:
            return self.tag_type.name
        except:
            return self.tag_type or ''

    @property
    def tag_type_property_render(self):
        try:
            return self.tag_type_property.name
        except:
            return self.tag_type_property or ''

    @property
    def status_render(self):
        return OnOfflineStatusEnum[self.status].desc


class RequireModel(Document):
    """
    管理要求
    """
    meta = {
        'collection': 'require',
        'verbose_name': '管理要求'
    }
    content = StringField(required=True, verbose_name='管理要求')
    source = StringField(required=False, verbose_name='出处', null=True)
    tags = ListField(ReferenceField(TagModel), required=False, verbose_name='标签')

    @property
    def tags_render(self):
        result = defaultdict(list)
        if self.tags:
            for item in self.tags:
                type_id = str(item.tag_type.id)
                result[type_id].append({'id': str(item.id), 'name': item.name})
        return result

    @classmethod
    def describe(cls):
        result = {}
        offline_required_tags = TagModel.offline_required_tags()
        queryset = cls.objects.filter(tags__not__in=offline_required_tags)
        result['total_count'] = queryset.count()
        return result
