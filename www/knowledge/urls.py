# -*- coding:utf-8 -*-

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

from core.drfmongo.routers import DRFMongoRouter
from knowledge import viewsets

router = DRFMongoRouter()

router.register(r'tag-type', viewsets.TagTypeViewSet)
router.register(r'tag-type-property', viewsets.TagTypePropertyViewSet)
router.register(r'tag', viewsets.TagViewSet)
router.register(r'require', viewsets.RequireViewSet)


urlpatterns = [
    path('', include(router.urls)),
]
