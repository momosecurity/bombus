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

import redis
from django.conf import settings

##############
# REDIS POOL #
##############

conn_pool = {}


def get_conn_pool():
    if not conn_pool:
        for k, v in settings.REDIS_CONF.items():
            v.update(settings.REDIS_CONN_DEFAULT_CONF.copy())
            conn_pool[k] = redis.StrictRedis(**v)
    return conn_pool


def get_redis_client(name) -> redis.StrictRedis:
    return get_conn_pool()[name]


class _RedisProxy:
    """redis proxy add prefix automatically."""

    # add methods those are need to be hacked here
    _hacked_methods = [
        'set', 'get', 'setex', 'hget', 'hset', 'smembers',
        'sadd', 'incr', 'delete', 'exists', 'mget', 'mset',
        'sismember', 'expire',
    ]
    own_attrs = ['_client', '__prefix']

    def __getattribute__(self, name):
        if name in _RedisProxy.own_attrs:
            return object.__getattribute__(self, name)
        try:
            attr = getattr(self._client, name)
        except AttributeError:
            return object.__getattribute__(self, name)

        if name in _RedisProxy._hacked_methods:
            def newfunc(k, *args, **kwargs):
                prefix = self.__prefix
                k = prefix + ':' + k
                result = attr(k, *args, **kwargs)
                return result
            return newfunc

        return attr

    def __init__(self, prefix):
        self._client = redis.StrictRedis(**settings.REDIS_CONF[prefix])
        self.__prefix = prefix

    @classmethod
    def get_client(cls, prefix=''):
        return cls(prefix)

    def __repr__(self):
        return f'<cache_proxy: {self.__prefix}>'


_redis_proxy = _RedisProxy.get_client

# 缓存实例定义
ums_cache = _redis_proxy('ums_cache_ca')
has_log_cache = _redis_proxy('task_has_log')
