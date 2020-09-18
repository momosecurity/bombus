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
from urllib.parse import urljoin

from django.conf import settings
from django.http import JsonResponse
from django.views import View

from bombus.libs.exception import FastResponse
from bombus.services.cloud_storage import GetCloudStorage, UploadCloudStorage
from core.util import time_util


class FileUpload(View):
    """
    上传文件
    """
    def post(self, request, *args, **kwargs):
        uploaded_file = request.FILES['file']
        file_name = uploaded_file.name
        upload_cloud = UploadCloudStorage(uploaded_file)
        cloud_uri = upload_cloud.upload()
        if not cloud_uri:
            raise FastResponse('上传失败, 请重试')
        path = f'{settings.STATIC_FILE_API_PREFIX}{cloud_uri}'
        url = urljoin(settings.HTTPS_HOST, path)
        upload_time = time_util.time2str(datetime.datetime.now())
        upload_info = {
            'name': file_name,
            'url': url,
            'location': url,
            'upload_time': upload_time
        }
        return JsonResponse(data=upload_info)


class FileDownload(View):
    """
    下载文件
    """
    def get(self, request, *args, **kwargs):
        path = kwargs.get('path')
        if path:
            return GetCloudStorage().get_result(path)

        raise FastResponse('下载失败, 请重试！')
