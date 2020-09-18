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

from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

from bombus.libs.exception import FastResponse


class FastResponseMiddleware(MiddlewareMixin):

    def process_exception(self, request, exception):

        if isinstance(exception, FastResponse):
            error_info = {'error': exception.error_msg}
            json_resp = JsonResponse(error_info, status=exception.status_code)
            json_resp.content_type = 'application/json'
            return json_resp

        return None
