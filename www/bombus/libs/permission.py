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

from django.contrib.auth.models import Permission

VIEW_PERMISSION_ATTR = 'permission_keys'


def permission_required(*perm_keys: str):
    """装饰器: 为class或function设置权限key属性"""

    def wrapper(klass_or_func):
        setattr(klass_or_func, VIEW_PERMISSION_ATTR, set(perm_keys))
        return klass_or_func

    return wrapper


def get_view_perms(view) -> set:
    try:
        return getattr(view, VIEW_PERMISSION_ATTR)
    except AttributeError:
        pass

    # FOR rest_framework viewset
    try:
        return getattr(view.cls, VIEW_PERMISSION_ATTR)
    except AttributeError:
        pass

    return set()


def has_perm(request, view) -> bool:
    """判断该次请求是否有权限"""

    if request.user.is_superuser:
        return True

    method = request.method
    if method.lower() == 'get':
        action = 'read'
    else:
        action = 'write'

    required_perms = get_view_perms(view)
    for perm in required_perms:
        perm = f'{perm}:{action}'
        try:
            request.user.user_permissions.get(codename=perm)
        except Permission.DoesNotExist:
            return False

    return True
