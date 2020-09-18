"""
    主机信息 -> root用户列表
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

import logging

from django.core.management import BaseCommand

from bombus.libs.enums import ServerKindEnum

logger = logging.getLogger(__name__)


def sync_service_user(server_kind):
    pass


class Command(BaseCommand):

    def handle(self, *args, **options):
        logger.info('sync root user begin')
        sync_service_user(ServerKindEnum.SA.name)
        sync_service_user(ServerKindEnum.DBA.name)
        logger.info('sync root user finish')
