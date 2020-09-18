# -*- coding:utf-8 -*-

"""
self-defined serializer
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

from rest_framework_mongoengine.serializers import DocumentSerializer


class BaseDocumentSerializer(DocumentSerializer):
    """ 自定义 """
    def to_representation(self, instance):
        """
        数据外显 下发额外字段
        下发规则:
            1. 如果model下包含了对应的field_render属性, 则下发时, 会同样将field_reader字段及属性值下发
        """
        ret = super().to_representation(instance)
        extra_data = self.extra_to_representation(instance)
        return dict(ret, **extra_data)

    def extra_to_representation(self, instance):
        """
        渲染额外的展示信息
        """
        result = {}
        if instance is None:
            return result
        for _f in self.Meta.model._fields:
            field_render = _f + '_render'
            if field_render in instance:
                result[field_render] = getattr(instance, field_render)

        return result
