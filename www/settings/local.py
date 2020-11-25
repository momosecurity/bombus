# -*- coding: utf-8 -*-

"""

There’s nothing stopping you from creating your own settings,
for your own Django apps. Just follow these guidelines:

- Setting names must be all uppercase.
- Don’t reinvent an already-existing setting.
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

import os

from settings.base import *

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': f'{CURRENT_DIR}/../ca.sqlite3',
    }
}


###############
# BASIC STUFF #
###############
DEBUG = True
ALLOWED_HOSTS = ["*"]
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False

# access domain
DOMAIN = '127.0.0.1'
HTTPS_HOST = f'http://{DOMAIN}:60010/'
LOGIN_PAGE = f'{HTTPS_HOST}login'


##################
# MONGO SETTINGS #
##################
MONGODB_CONF = {
    'ca': {
        'default_db': 'ca_local',
        'conf': {
            'host': ['127.0.0.1:27017', ],
            'maxPoolSize': 20,
            'maxIdleTimeMS': 60 * 1000,
            'waitQueueTimeoutMS': 500,
            'socketTimeoutMS': 5 * 1000,
            'alias': 'default'
        }
    }
}


##################
# REDIS SETTINGS #
##################
REDIS_CONF = {
    'audit_redis': {"host": "127.0.0.1", "port": 6379},
    'ums_cache_ca': {'host': '127.0.0.1', 'port': 6379},
    'task_has_log': {'host': '127.0.0.1', 'port': 6379},
}
