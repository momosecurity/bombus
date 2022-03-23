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

from django.conf import settings

from core.lru import lru_cache_function
from core.utils import split_large_collection

from .user_model import Employee


class UserService(object):

    EMAIL_SUFFIX = settings.EMAIL_SUFFIX
    BATCH_SIZE = 10

    @classmethod
    @lru_cache_function(max_size=5000)
    def _query(cls, method, params):
        try:
            result = Employee._query(method, params)
        except Exception as e:
            import traceback
            result = {}
        return result

    query_service = _query

    @classmethod
    def _validate_email(cls, email):
        return str(email).strip().replace(' ', '').replace(cls.EMAIL_SUFFIX, '')

    get_email_prefix = _validate_email

    @classmethod
    def get_user_by_accountid(cls, accountid, status=None):
        """
        根据id获取用户, 默认查询全部, status: True->在职; False-离职; None->全部
        """
        result = cls.query_service('search-by-accountids', {'ids': str(accountid), 'status': status})
        return result and result[0] or {}

    @classmethod
    def query_accountid(cls, accountid):
        return cls.get_user_by_accountid(accountid, status=True)

    @classmethod
    def batch_get_user_by_accountid(cls, accountids: list) -> dict:
        result = {}
        accountids = list(filter(None, map(str, accountids)))
        if not accountids:
            return result

        accountids.sort()
        for mid in accountids:
            result[mid] = {}

        for ids in split_large_collection(accountids, cls.BATCH_SIZE):
            ids_str = ','.join(ids)
            resp = cls.query_service('search-by-accountids', {'ids': ids_str})
            for r in resp:
                result[r['accountid']] = r
        return result

    @classmethod
    def batch_get_user_by_email(cls, emails: list) -> dict:
        result = {}
        emails = list(filter(None, map(str, emails)))
        if not emails:
            return result

        emails.sort()
        for em in emails:
            result[em] = {}
        for ems in split_large_collection(emails, cls.BATCH_SIZE):
            ems_str = ','.join(ems)
            resp = cls.query_service('search-by-accountids', {'emails': ems_str})
            for r in resp:
                email = cls.get_email_prefix(r['email'])
                result[email] = r
        return result

    @classmethod
    def batch_id_to_email(cls, accountids: list, clear_email=True) -> dict:
        """
        批量id转为邮箱
        """
        result = {}
        id2info = cls.batch_get_user_by_accountid(accountids)
        for _id, info in id2info.items():
            email = ''
            if info:
                email = info['email']
                if clear_email:
                    email = cls.get_email_prefix(email)
            result[str(_id)] = email
        return result

    @classmethod
    def get_user_by_email(cls, email):
        """
        根据邮箱获取用户信息(离职人员也能查到)
        """
        email = cls._validate_email(email)
        result = cls.batch_get_user_by_email([email])
        return result.get(email) or {}

    @classmethod
    def search_user(cls, email):
        """关键字查询用户"""
        name = cls.get_email_prefix(email)
        result = cls.query_service('search-user', {'keyword': name})
        return result['users']

    @classmethod
    def get_user_name(cls, email):
        if not email:
            return ''
        try:
            user = cls.get_user_by_email(email)
            if not user:
                return ''
            return user['name']
        except:
            return ''

    @classmethod
    def is_staff(cls, accountid, default=False) -> bool:
        """是否为内部员工"""
        if not accountid:
            return default
        result = cls.query_service('is-staff', {'id': str(accountid)})
        return bool(result and result.get('is_staff'))


if __name__ == '__main__':
    principal = UserService.get_user_by_accountid('123')
    print(principal)
