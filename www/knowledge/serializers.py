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
from knowledge.models import (RequireModel, TagModel, TagTypeModel,
                              TagTypePropertyModel)


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
