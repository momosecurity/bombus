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

from audit import caviews, views
from core.drfmongo.routers import DRFMongoRouter

audit_router = DRFMongoRouter()

audit_router.register(r'server', views.AuditServerViewSet)
audit_router.register(r'sys', views.AuditSysViewSet)
audit_router.register(r'regex_rule', views.RegexPatternViewSet)
audit_router.register(r'rule_atom', views.RuleAtomViewSet)
audit_router.register(r'rule_group', views.RuleGroupViewSet)
audit_router.register(r'non_normal_user', views.NonNormalUserViewSet)
audit_router.register(r'task_manager', views.TaskManagerViewSet)
audit_router.register(r'task', views.AuditTaskViewSet)
audit_router.register(r'operation_log', views.OperationLogViewSet)
audit_router.register(r'bash_command', views.BashCommandViewSet)
audit_router.register(r'bg_access_log', views.BgAccessLogViewSet)
audit_router.register(r'review_comment', views.ReviewCommentViewSet)
audit_router.register(r'message_board', views.TaskMessageBoardViewSet)
audit_router.register(r'mysql_log', views.MysqlLogViewSet)
audit_router.register(r'online_ticket', views.OnlineTicketViewSet)
audit_router.register(r'new_review_comment', views.NewReviewCommentViewSet)
audit_router.register(r'new_message_board', views.NewMessageBoardViewSet)

urlpatterns = [
    path('', include(audit_router.urls)),
    path('common_data/', views.CommonDataReport.as_view(), name='common_log'),
    path('app_user_review/', caviews.AppUserReviewView.as_view(), name='app_user_review'),
    path('sys_user_review/', caviews.SysUserReviewView.as_view(), name='sys_user_review'),
    path('db_user_review/', caviews.DbUserReviewView.as_view(), name='db_user_review'),
    path('sys_log_review/', caviews.SysLogReviewView.as_view(), name='sys_log_review'),
    path('app_log_review/', caviews.AppLogReviewView.as_view(), name='app_log_review'),
    path('db_log_review/', caviews.DbLogReviewView.as_view(), name='db_log_review'),
    path('user_servers/', caviews.ServerListView.as_view(), name='user_servers'),
    path('deploy_ticket/', views.DeployTicketView.as_view(), name='ticket_deploy'),
    path('perm_apply/', caviews.PermApplyView.as_view(), name='perm_apply'),
    path('ticket_list/', caviews.TicketReview.as_view(), name='ticket_review'),
    path('sys_db/', caviews.SysDbReview.as_view(), name='sys_db'),
    path('app_user/', caviews.AppUserReview.as_view(), name='app_user'),
    path('sys_db_log/', caviews.SysDbLogReview.as_view(), name='sys_db_log'),
    path('app_log/', caviews.AppLogReview.as_view(), name='app_log'),
]
