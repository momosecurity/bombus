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

import logging

from django.conf import settings
from django.http import JsonResponse
from django.urls import reverse_lazy

from bombus.libs.permission import has_perm

logger = logging.getLogger(__name__)


class PermissionAuthenticateMiddleware:
    # 白名单URI 无需授权即可访问
    URI_WHITE_LIST = {
        reverse_lazy('ssologin:login'),
        reverse_lazy('ssologin:logout'),
        reverse_lazy('ssologin:authenticate'),
        reverse_lazy('bombus:check_health'),
        reverse_lazy('audit:common_log')
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    @classmethod
    def log_permission_denied(cls, request):
        """记录鉴权失败信息"""
        user = request.user
        if user.is_anonymous:
            email = 'null'
            fullname = 'AnonymousUser'
        else:
            email = user.email
            fullname = user.username

        msg = (f'Assess denied! '
               f'user: {fullname}, '
               f'email: {email}, '
               f'path: {request.path}, '
               f'client_ip: {request.META.get("REMOTE_ADDR")}, '
               f'user_agent: {request.META.get("HTTP_USER_AGENT")}')
        logger.warning(msg)

    @classmethod
    def resp_json(cls, status, message, **kwargs):
        json_data = {'status': status, 'message': message, 'payload': kwargs}
        return JsonResponse(json_data, status=status)

    @classmethod
    def process_view(cls, request, view, *args):

        # 测试环境无权限控制(暂不生效)
        if settings.DEBUG:
            return None

        # 无需登录的URL直接通过
        path = request.path
        if path in cls.URI_WHITE_LIST:
            return None

        # 检查登录状态
        user = request.user
        if not user.is_authenticated:
            return cls.resp_json(status=401,
                                 message='UNAUTHORIZED',
                                 login_url=f'{settings.LOGIN_URL}')

        # 检查权限状态
        if not has_perm(request, view):
            cls.log_permission_denied(request)
            return cls.resp_json(status=403,
                                 message='FORBIDDEN',
                                 req_method=request.method,
                                 error='抱歉，无权进行此操作。')

        return None

    @classmethod
    def process_exception(cls, request, exception):
        user = request.user
        if user.is_anonymous:
            trigger_user = 'AnonymousUser'
        else:
            trigger_user = user.email
        msg = (f'View Exception!\n'
               f'Trigger Uri: {request.path}\n'
               f'Trigger Method: {request.method}\n'
               f'Trigger User: {trigger_user}\n'
               f'client_ip: {request.META.get("REMOTE_ADDR")}\n'
               f'user_agent: {request.META.get("HTTP_USER_AGENT")}\n'
               f'Exception: {exception!r}{exception}')
        logger.exception(msg)
        return None
