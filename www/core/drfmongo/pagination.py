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

import inspect

from django.core.paginator import Paginator as DjangoPaginator
from django.utils.functional import cached_property
from django.utils.inspect import method_has_no_args
from mongoengine.queryset.queryset import QuerySet as MongoQuerySet
from rest_framework.pagination import PageNumberPagination


class CustomDjangoPaginator(DjangoPaginator):
    @cached_property
    def count(self):
        cnt = getattr(self.object_list, 'count', None)
        if callable(cnt) and not inspect.isbuiltin(cnt) and (
                method_has_no_args(cnt) or isinstance(self.object_list, MongoQuerySet)):
            return cnt()
        return len(self.object_list)


class LargeQuerySetPagination(PageNumberPagination):
    page_size_query_param = 'page_size'
    django_paginator_class = CustomDjangoPaginator
