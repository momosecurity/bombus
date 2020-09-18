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

from bombus import views
from core.drfmongo.routers import DRFMongoRouter

router = DRFMongoRouter()
router.register(r'audit_log', views.AuditLogViewSet)
router.register(r'feature', views.FeatureViewSet)
router.register(r'record-history', views.OperationLogViewSet)
router.register(r'settings', views.SettingConfViewSet)
router.register(r'app-compliance', views.AppComplianceViewSet)
router.register(r'compliance-detail', views.ComplianceDetailViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('check_health/', views.HealthCheck.as_view(), name='check_health'),
    path('search_user/', views.UserSearch.as_view(), name='search_user')
]
