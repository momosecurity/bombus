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

from braces.views import JSONResponseMixin
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseRedirect, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.viewsets import ModelViewSet

from bombus.libs.baseview import GetViewSet, UpdateViewSet
from ssologin.serializers import PermissionKeySerializer, UserSerializer


class SSOLoginAuthenticateView(JSONResponseMixin, View):
    @method_decorator(ensure_csrf_cookie)
    def get(self, request, **kwargs):
        user = request.user
        if not user.is_authenticated:
            login_page = f'{settings.LOGIN_PAGE}'
            return self.render_json_response({
                'status': 401,
                'message': 'UNAUTHORIZED',
                'payload': {'login_url': login_page}
            }, status=401)
        else:
            user_perms = list(user.user_permissions.all().values_list('codename', flat=True))
            is_super = user.is_superuser
            return self.render_json_response({
                'status': 200,
                'message': 'Authenticated',
                'payload': {
                    'username': user.username,
                    'email': user.email,
                    'perms': user_perms,
                    'is_superuser': is_super
                }
            })


class SSOLoginView(View):
    """
    登录view
    """
    @method_decorator(ensure_csrf_cookie)
    def post(self, request, *args, **kwargs):
        post_params = json.loads(request.body or '{}') or {}
        username = post_params.get('username')
        password = post_params.get('password')
        if not all([username, password]):
            return JsonResponse(data={'message': '用户名密码不能为空', 'error': 1})
        user = authenticate(request, username=username, password=password)
        if not user:
            return JsonResponse(data={'message': '用户名或密码错误', 'error': 1})
        login(request, user)
        resp = JsonResponse(data={'message': '登录成功', 'error': 0})
        return resp


class SSOLogoutStatusView(JSONResponseMixin, View):
    def get(self, request):
        logout(request)
        login_page = f'{settings.LOGIN_PAGE}'
        resp = HttpResponseRedirect(login_page)
        return resp


class PermKeyViewSet(GetViewSet, UpdateViewSet):
    """
    审计范围
    """
    serializer_class = PermissionKeySerializer
    queryset = serializer_class.Meta.model.objects()
    show_column_keys = ['name', 'key', 'desc']
    filter_fields = {
        'name': 'contains',
        'key': 'contains'
    }

    def get_queryset(self):
        query = self.build_filter_params(self.request.query_params)
        return self.serializer_class.Meta.model.objects(**query)


class UserViewSet(ModelViewSet):
    serializer_class = UserSerializer
    queryset = serializer_class.Meta.model.objects.all()
    show_columns = {
        'username': '用户名',
        'email': '邮箱',
    }

    def list(self, request, *args, **kwargs):
        resp = {}
        page_size = request.query_params.get('page_size') or 10
        page_num = request.query_params.get('page', 1)
        offset = page_num * page_size
        queryset = User.objects.all()
        resp['count'] = queryset.count()
        resp['show_columns'] = self.show_columns
        resp['perm_keys'] = PermissionKeySerializer.Meta.model.get_list()
        user_list = []
        for item in queryset[offset - page_size: offset]:
            info = {
                'id': item.id, 'username': item.username,
                'email': item.email,
                'perms': [x.codename for x in item.user_permissions.all()]
            }
            user_list.append(info)
        resp['results'] = user_list
        return JsonResponse(data=resp)

    def create(self, request, *args, **kwargs):
        username = request.data['name']
        email = request.data['email']
        try:
            User.objects.create_user(username=username, email=email)
            return JsonResponse(data={'message': '添加成功', 'error': 0})
        except:
            return JsonResponse(data={'message': '添加失败', 'error': 1})

    def update(self, request, *args, **kwargs):
        content_type = ContentType.objects.get(app_label='auth', model='permission')
        id = request.data['id']
        user = User.objects.get(id=id)
        if 'perms' in request.data:
            perms = request.data['perms']
            new_perms = []
            for perm in perms:
                user_perm, _ = Permission.objects.get_or_create(
                    name=perm, codename=perm,
                    content_type=content_type
                )
                new_perms.append(user_perm)
            user.user_permissions.set(new_perms)
        if 'password' in request.data:
            user.set_password(request.data['password'])
        user.save()
        return JsonResponse(data={'message': '保存成功'})
