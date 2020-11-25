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

from settings.local import *

# access domain
HTTPS_HOST = 'http://127.0.0.1:60010/'


##################
# MONGO SETTINGS #
##################
MONGODB_CONF = {
    'ca': {
        'default_db': 'ca_local',
        'conf': {
            'host': ['db_mongo:27017', ],
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
    'audit_redis': {"host": "db_redis", "port": 6379},
    'ums_cache_ca': {'host': 'db_redis', 'port': 6379},
    'task_has_log': {'host': 'db_redis', 'port': 6379},
}
