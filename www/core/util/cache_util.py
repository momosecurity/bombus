# -*- coding:utf-8 -*-

"""
缓存装饰器, 用来装饰函数方法等
"""
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

import functools
import pickle
import random

from core.util.hash_util import md5


class CacheWrap(object):

    def __init__(self, cache_serve, pre_fix='', expire=3600, time_range=600, time_cache_key=None):
        assert expire > 0, 'expire must be bigger than 0'
        assert isinstance(pre_fix, str), 'pre_fix only accept string value'

        self.cache_serve = cache_serve
        self.pre_fix = pre_fix
        self.expire = expire
        self.time_range = time_range
        self.miss = 0
        self.hits = 0
        self.time_cache_key=time_cache_key

    @property
    def random_expire(self):
        expire = self.expire
        if self.time_range:
            expire += random.randint(0, self.time_range)
        return expire

    def _set_cache(self, key, value):
        value = pickle.dumps(value)
        self.cache_serve.setex(key, self.random_expire, value)

    def _get_cache(self, key):
        _get = False
        value = self.cache_serve.get(key)
        if value:
            try:
                value = pickle.loads(value)
                _get = True
            except:
                pass

        if _get:
            self.hits += 1
        else:
            self.miss += 1
        self.upload_hit()
        return _get, value

    def upload_hit(self):
        """
        upload the miss/hit to cal the Statistics
        """
        pass

    def _get_cache_key(self, args, kwargs):
        time_key = ''
        if self.time_cache_key:
            if callable(self.time_cache_key):
                time_key = self.time_cache_key()
            else:
                time_key = self.time_cache_key

        t_args = repr(args)
        t_kwargs = repr(kwargs)
        md5_str = md5(f'{t_args}:{t_kwargs}')
        return f'{time_key}:{self.pre_fix}:{md5_str}'

    def __call__(self, func):
        @functools.wraps(func)
        def wrapped_func(*args, **kwargs):
            key = self._get_cache_key(args, kwargs)
            _get, value = self._get_cache(key)
            if _get:
                return value
            value = func(*args, **kwargs)
            self._set_cache(key, value)
            return value

        return wrapped_func
