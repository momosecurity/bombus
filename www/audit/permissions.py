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

from django.contrib.auth.models import AnonymousUser
from django.utils.translation import gettext_lazy as _
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import IsAuthenticated


class APIPermission(IsAuthenticated):
    ALLOWED_USERS = []

    def has_permission(self, request, view):
        return request.user and request.user.get_username() in self.ALLOWED_USERS


class CommonDataAPIPermission(APIPermission):
    ALLOWED_USERS = ['token-example']


class APIAuthentication(TokenAuthentication):
    VALID_TOKEN_USER_MAP = {
        'secret_key_example': 'token-example',
    }

    def authenticate_credentials(self, key):
        sys_name = self.VALID_TOKEN_USER_MAP.get(key)
        if not sys_name:
            raise AuthenticationFailed(_('Invalid token.'))
        user = AnonymousUser()
        user.username = sys_name
        return user, key
