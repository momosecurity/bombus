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

from mongoengine import BooleanField, Document, StringField
from mongoengine.queryset import DoesNotExist
from mongoengine.queryset.visitor import Q


class Employee(Document):
    employee_id = StringField(required=True, verbose_name='员工id', unique=True)
    employee_name = StringField(required=True, verbose_name='员工姓名')
    email = StringField(required=True, verbose_name='邮箱')
    dept_name = StringField(required=True, verbose_name='部门信息')
    status = BooleanField(required=True, verbose_name='在职状态', default=True)
    meta = {
        'collection': 'employee_info',
        'verbose_name': '员工信息表',
        'indexes': [
            'employee_id',
            'email',
            'employee_name',
        ]
    }

    def to_dict(self):
        return {
            'id': self.employee_id,
            'accountid': self.employee_id,
            'name': self.employee_name,
            'email': self.email,
            'dept_name': self.dept_name,
        }

    @classmethod
    def get_users(cls, ids:str='', emails:str='', status=None) -> list:
        """
        根据员工id查询
        params ids: 用户id列表
        params status: 在值状态, default all
        """
        result = []
        id_list = list(filter(None, [x.strip() for x in ids.split(',')]))
        email_list = list(filter(None, [x.strip() for x in emails.split(',')]))
        if not id_list and not emails:
            return result

        if id_list:
            queryset = cls.objects.filter(employee_id__in=id_list)
        else:
            queryset = cls.objects.filter(email__in=email_list)
        if status is not None:
            queryset = queryset.filter(status=status)
        for item in queryset.limit(10):
            result.append(item.to_dict())
        return result

    @classmethod
    def search_user(cls, keyword):
        result = []
        if not keyword:
            return result

        name_filter = Q(employee_name__contains=keyword)
        email_filter = Q(email__contains=keyword)
        queryset = cls.objects.filter(name_filter | email_filter).limit(10)
        for item in queryset:
            result.append(item.to_dict())
        return {'users': result}

    @classmethod
    def staff_status(cls, id):
        try:
            is_staff = bool(cls.objects.get(employee_id=str(id), status=True))
        except DoesNotExist as e:
            is_staff = False
        except Exception as e:
            is_staff = False
        return {'is_staff': is_staff}

    @classmethod
    def _query(cls, method, params):
        method_map = {
            'search-by-accountids': cls.get_users,
            'is-staff': cls.staff_status,
            'search-user': cls.search_user
        }
        func = method_map.get(method)
        if not func:
            raise Exception(f'unmatched query method: {method}')
        return func(**params)
