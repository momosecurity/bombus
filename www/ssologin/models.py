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

from mongoengine import Document, StringField


class PermissionKeyModel(Document):
    name = StringField(verbose_name='权限名称')
    key = StringField(verbose_name='权限key', required=True, unique=True)
    desc = StringField(verbose_name='权限描述', required=True)
    meta = {
        'collection': 'permission_key',
        'verbose_name': '权限列表'
    }

    def to_dict(self):
        return {
            'name': self.name,
            'key': self.key,
            'desc': self.desc
        }

    @classmethod
    def get_list(cls):
        result = []
        queryset = cls.objects.all().order_by('key')
        for qs in queryset:
            result.append(qs.to_dict())
        return result
