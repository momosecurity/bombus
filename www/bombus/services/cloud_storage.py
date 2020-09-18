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

from django.conf import settings
from django.http import StreamingHttpResponse


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
    @classmethod
    def get_result(cls, path):
        file_path = settings.DATA_DIR/path
        fp = open(file_path, 'rb')
        response = StreamingHttpResponse(fp)
        response['Content-Type'] = 'application/octet-stream'
        return response
