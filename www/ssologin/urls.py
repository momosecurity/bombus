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

from core.drfmongo.routers import DRFMongoRouter
from ssologin import views

sso_router = DRFMongoRouter()
sso_router.register(r'perm_key', views.PermKeyViewSet)
sso_router.register(r'user', views.UserViewSet)

urlpatterns = [
    path('', include(sso_router.urls)),
    path('authenticate/', views.SSOLoginAuthenticateView.as_view(), name='authenticate'),
    path('login/', views.SSOLoginView.as_view(), name='login'),
    path('logout/', views.SSOLogoutStatusView.as_view(), name='logout'),
]
