"""
上传下载文件服务
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

import datetime
import os
import uuid
from pathlib import Path

from django.conf import settings
from django.http import StreamingHttpResponse

from bombus.libs.exception import FastResponse


class UploadCloudStorage:
    def __init__(self, file):
        self.file = file

    def upload(self):
        uri = self.gen_uri()
        file_path = settings.DATA_DIR/uri
        with open(file_path, 'wb') as f:
            for chunk in self.file.chunks():
                f.write(chunk)

        return uri

    def gen_uri(self):
        file_ext = os.path.splitext(self.file.name)[-1]
        ts = int(datetime.datetime.now().strftime('%Y%m%d'))
        uid = str(uuid.uuid4()).upper()
        file_tag = f'{uid}_{ts}{file_ext}'
        return file_tag


class GetCloudStorage:
    _DOWNLOAD_ERR = '下载失败, 请重试！'

    @classmethod
    def get_result(cls, path):
        if not path or not isinstance(path, str) or '\x00' in path:
            raise FastResponse(cls._DOWNLOAD_ERR)
        rel = Path(path)
        if rel.is_absolute() or rel.name in ('', '.', '..'):
            raise FastResponse(cls._DOWNLOAD_ERR)
        try:
            base = Path(settings.DATA_DIR).resolve()
            file_path = (base / rel).resolve()
            file_path.relative_to(base)
        except (OSError, ValueError):
            raise FastResponse(cls._DOWNLOAD_ERR) from None
        if not file_path.is_file():
            raise FastResponse(cls._DOWNLOAD_ERR)
        try:
            fp = open(file_path, 'rb')
        except OSError:
            raise FastResponse(cls._DOWNLOAD_ERR) from None
        response = StreamingHttpResponse(fp)
        response['Content-Type'] = 'application/octet-stream'
        return response
