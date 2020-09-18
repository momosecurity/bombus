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

import json
import logging
import re
from datetime import datetime

from django.conf import settings
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.utils.deprecation import MiddlewareMixin

from bombus.libs.exception import FastResponse
from bombus.models import ProjectAuditLogEntry

logger = logging.getLogger(__name__)


class ProjectAuditLogMiddleware:
    """审计日志中间件"""

    AUDIT_LOG_PATH = reverse_lazy('bombus:audit_log-list')
    LOGOUT_PATH = reverse_lazy('ssologin:logout')
    URI_WHITH_LIST = [
        reverse_lazy('bombus:check_health'),
        reverse_lazy('audit:common_log'),
        reverse_lazy('static:upload')
    ]
    RE_URI_WHITE_LIST = [
        '^/%s(?P<path>.*)$' % settings.STATIC_FILE_API_PREFIX
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        extra_params = {}
        path = request.path
        if path == self.LOGOUT_PATH:
            extra_params['req_user'] = request.user

        request.body_copy = request.body
        response = self.get_response(request)
        try:
            if path in self.URI_WHITH_LIST:
                return response
            for re_path in self.RE_URI_WHITE_LIST:
                if re.match(re_path, path):
                    return response
            self.save_log(request, response, **extra_params)
        except Exception:
            logger.exception(
                f'Failed record access log entry: '
                f'user: {request.user}, '
                f'path: {request.path}, '
                f'method: {request.method}, '
                f'status_code: {response.status_code}, '
                f'headers: {request.headers}, '
                f'content: {response.content}'
            )
        return response

    @classmethod
    def save_log(cls, request, response, **kwargs):
        """持久化审计日志"""

        path = request.path
        if path == cls.AUDIT_LOG_PATH:
            return

        user = request.user
        if 'req_user' in kwargs:
            user = kwargs['req_user']
        if not user.is_authenticated:
            req_user = 'AnonymousUser'
        else:
            req_user = f'{user.username}({user.email})'

        response_content = '{}'
        try:
            response_content = response.content.decode()
        except Exception as e:
            pass
        log_entry = ProjectAuditLogEntry(
            req_time=datetime.now(),
            req_user=req_user,
            req_path=request.path,
            req_method=request.method,
            req_ip=request.headers.get('X-Real-Ip') or request.META.get('REMOTE_ADDR'),
            req_user_agent=request.headers['User-Agent'],
            req_params=json.dumps(request.GET.dict()),
            req_body=request.body_copy.decode(),
            resp_status_code=response.status_code,
            resp_content_type=response.get('Content-Type') or '',
            resp_content=response_content,
        )
        log_entry.save()


class FastResponseMiddleware(MiddlewareMixin):

    def process_exception(self, request, exception):

        if isinstance(exception, FastResponse):
            error_info = {'error': exception.error_msg}
            json_resp = JsonResponse(error_info, status=exception.status_code)
            json_resp.content_type = 'application/json'
            return json_resp

        return None
