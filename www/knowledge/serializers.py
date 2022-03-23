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

from bombus.libs.baseserializer import BaseDocumentSerializer
from core.util.time_util import utc2local
from knowledge.models import (RequireModel, TagModel, TagTypeModel,
                              TagTypePropertyModel, SupervisionModel, PolicyTraceModel)


class TagTypeSerializer(BaseDocumentSerializer):
    class Meta:
        model = TagTypeModel
        fields = '__all__'


class TagTypePropertySerializer(BaseDocumentSerializer):
    class Meta:
        model = TagTypePropertyModel
        fields = '__all__'


class TagSerializer(BaseDocumentSerializer):
    class Meta:
        model = TagModel
        fields = '__all__'


class RequireSerializer(BaseDocumentSerializer):
    class Meta:
        model = RequireModel
        fields = '__all__'

    def extra_to_representation(self, instance):
        result = {}
        if instance is None:
            return result
        expand_tags = TagModel.taglist2map(instance.tags)
        result.update(**expand_tags)
        return result


class SupervisionSerializer(BaseDocumentSerializer):
    class Meta:
        model = SupervisionModel
        fields = '__all__'

    def time_convert(self, validated_data):
        if validated_data.get('pub_time'):
            validated_data['pub_time'] = utc2local(validated_data['pub_time'])

    def create(self, validated_data):
        self.time_convert(validated_data)
        instance = super().create(validated_data)
        return instance

    def update(self, instance, validated_data):
        self.time_convert(validated_data)
        super().update(instance, validated_data)
        return instance


class PolicyTraceSerializer(BaseDocumentSerializer):
    class Meta:
        model = PolicyTraceModel
        fields = '__all__'

    def time_convert(self, validated_data):
        if validated_data.get('pub_time'):
            validated_data['pub_time'] = utc2local(validated_data['pub_time'])

    def create(self, validated_data):
        self.time_convert(validated_data)
        instance = super().create(validated_data)
        return instance

    def update(self, instance, validated_data):
        self.time_convert(validated_data)
        super().update(instance, validated_data)
        return instance
