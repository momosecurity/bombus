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

import os
import pathlib

###############
# BASIC STUFF #
###############
DEBUG = False
ALLOWED_HOSTS = ["*"]
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECRET_KEY = '===REPLACE_WITH_YOUR_SECRET_KEY==='


LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_L10N = True
USE_TZ = False

WSGI_APPLICATION = 'wsgi.application'
ROOT_URLCONF = 'urls'
STATIC_URL = '/static/'
PROJECT_DIR = pathlib.Path(__file__).parent
EMAIL_SUFFIX = '@ca.com'


###########
# SESSION #
###########
SESSION_COOKIE_AGE = 86400 * 7


INSTALLED_APPS = (
    # Django contrib
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party
    'rest_framework',
    'audit',
    'bombus',
    'ssologin',
    'static'
)


MIDDLEWARE = MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'ssologin.middleware.PermissionAuthenticateMiddleware',
    'bombus.middleware.ProjectAuditLogMiddleware',
    'audit.middleware.FastResponseMiddleware',
)


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
)


#########################
# DJANGO REST FRAMEWORK #
#########################
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'core.drfmongo.pagination.LargeQuerySetPagination',
    'PAGE_SIZE': 10
}


##################
# REDIS_SETTINGS #
##################
REDIS_CONN_DEFAULT_CONF = {
    "max_connections": 20,
    "socket_timeout": 1,
    "decode_responses": True,
}


#################
# TIME SETTINGS #
#################
DATETIME_FMT001 = '%Y-%m-%d %H:%M:%S'
DATETIME_FMT002 = '%Y-%m-%dT%H:%M:%S+08:00'
DATETIME_FMT003 = '%Y-%m-%dT%H:%M:%S'
DATE_FMT001 = '%Y%m%d'
DATE_FMT002 = '%Y-%m-%d'


###########
# LOGGING #
###########
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname:1.1s} {asctime} {module}:{lineno}] {message}',
            'style': '{',
        },
        'simple': {
            'format': '[{levelname} {asctime}] {message}',
            'style': '{',
        },
        'django.server': {
            '()': 'django.utils.log.ServerFormatter',
            'format': '[{server_time}] {message}',
            'style': '{',
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'django.server': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'django.server',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'django.server': {
            'handlers': ['django.server'],
            'level': 'INFO',
            'propagate': False,
        },
        **{
            app: {
                'handlers': ['console'],
                'level': 'DEBUG',
                'propagate': False,
            } for app in ('services', 'core', '__main__') + INSTALLED_APPS
        }
    },
}


################
# FILE STORAGE #
################
FILE_DIR = pathlib.Path('.')
DATA_DIR = pathlib.Path('.')

STATIC_FILE_PREFIX = 'ca_static/'
STATIC_FILE_API_PREFIX = f'file/{STATIC_FILE_PREFIX}'

#############
# PERM CONF #
#############
CA_ASSET = 'ca_asset'
CA_CONF = 'ca_conf'
CA_TASK = 'ca_task'
CA_REVIEW = 'ca_review'
CA_LOG = 'ca_log'
CA_BENCH = 'ca_workbench'
CA_KNDGE = 'ca_knowledge'
CA_UNIFY = 'ca_unify'


#####################
# BUSINESS SETTINGS #
#####################
DBA = ['40001a', '40002a']

ADMIN_USERS = []
AUDIT_USERS = ['40002', '40002']

# 服务账号
SERVICE_ACCOUNT = []

BG_ADMIN_ROLE_MAP = {
    'ca_bg': '管理员'
}
