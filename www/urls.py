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

from django.urls import include, path

urlpatterns = [
    path('api/sso/', include(('ssologin.urls', 'ssologin'), namespace='ssologin')),
    path('api/', include(('bombus.urls', 'bombus'), namespace='bombus')),
    path('api/audit/', include(('audit.urls', 'audit'), namespace='audit')),
    path('api/knowledge/', include(('knowledge.urls', 'knowledge'), namespace='knowledge')),
    path('file/', include(('static.urls', 'static'), namespace='static')),
]
