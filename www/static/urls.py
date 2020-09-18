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

import re

from django.conf import settings
from django.urls import path, re_path
from django.views.decorators.csrf import csrf_exempt

from static import views

urlpatterns = [
    path(r'upload/', csrf_exempt(views.FileUpload.as_view()), name='upload'),
    re_path(r'^%s(?P<path>.*)$' % settings.STATIC_FILE_PREFIX,
            csrf_exempt(views.FileDownload.as_view()), name='static_file'),
]
