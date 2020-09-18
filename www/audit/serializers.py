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

from audit.models import (AuditServerModel, AuditSysModel, AuditTaskModel,
                          BashCommandModel, BgAccessLogModel,
                          DeployTicketModel, MysqlLogModel,
                          NewMessageBoardModel, NewReviewCommentModel,
                          NonNormalUserModel, OnlineTicketModel,
                          RegexPatternModel, ReviewCommentModel, RuleAtomModel,
                          RuleGroupModel, TaskManagerModel,
                          TaskMessageBoardModel, UserRoleDataModel)
from audit.statuschange import StatusChange
from bombus.libs.baseserializer import BaseDocumentSerializer
from bombus.libs.enums import TaskStatusEnum


class AuditSysSerializer(BaseDocumentSerializer):
    class Meta:
        model = AuditSysModel
        fields = '__all__'


class AuditServerSerializer(BaseDocumentSerializer):
    class Meta:
        model = AuditServerModel
        fields = '__all__'

    def extra_to_representation(self, instance):
        """
        渲染额外的展示信息;   eg:  dept_id:1 => dept_name: 技术部门
        """
        result = {}
        if instance is None:
            return result

        result['leader_name'] = instance.leader_name
        result['audit_scope'] = instance.audit_scope
        result['audit_sys_name'] = instance.audit_sys_name
        result['server_kind_name'] = instance.server_kind_name
        result['auditor_name'] = instance.auditor_name
        return result


class RegexPatternSerializer(BaseDocumentSerializer):
    """
    正则匹配
    """
    class Meta:
        model = RegexPatternModel
        fields = '__all__'


class RuleAtomSerializer(BaseDocumentSerializer):
    """
    策略原子
    """
    class Meta:
        model = RuleAtomModel
        fields = '__all__'


class RuleGroupSerializer(BaseDocumentSerializer):
    """
    策略组
    """
    class Meta:
        model = RuleGroupModel
        fields = '__all__'


class NonNormalUserSerializer(BaseDocumentSerializer):
    """
    非标准用户
    """
    class Meta:
        model = NonNormalUserModel
        fields = '__all__'


class TaskManagerSerializer(BaseDocumentSerializer):
    """
    任务计划
    """
    class Meta:
        model = TaskManagerModel
        fields = '__all__'

    def extra_to_representation(self, instance):
        """
        渲染额外的展示信息;
        """
        result = super().extra_to_representation(instance)
        if instance is None:
            return result

        result['period_render'] = instance.period_render
        result['cur_period_render'] = instance.cur_period_render
        return result


class AuditTaskSerializer(BaseDocumentSerializer):
    """
    审计任务
    """
    class Meta:
        model = AuditTaskModel
        fields = '__all__'

    def extra_to_representation(self, instance):
        """
        渲染额外的展示信息;
        """
        result = super().extra_to_representation(instance)
        if instance is None:
            return result

        result['audit_sys'] = instance.audit_sys_id
        return result

    def update(self, instance, validated_data):
        old_task_status = TaskStatusEnum[instance.status]
        new_task_status = TaskStatusEnum[validated_data['status']]
        status_tuple = (old_task_status, new_task_status)
        status_push = StatusChange(instance, status_tuple)
        status_push.validate()
        instance = super().update(instance, validated_data)
        status_push.trigger()
        return instance


class ReviewCommentSerializer(BaseDocumentSerializer):
    class Meta:
        model = ReviewCommentModel
        fields = '__all__'


class NewReviewCommentSerializer(BaseDocumentSerializer):
    class Meta:
        model = NewReviewCommentModel
        fields = '__all__'


class TaskMessageBoardSerializer(BaseDocumentSerializer):
    class Meta:
        model = TaskMessageBoardModel
        fields = '__all__'


class NewMessageBoardSerializer(BaseDocumentSerializer):
    class Meta:
        model = NewMessageBoardModel
        fields = '__all__'


class UserRoleDataSerializer(BaseDocumentSerializer):
    """
    用户角色数据
    """
    class Meta:
        model = UserRoleDataModel
        fields = '__all__'


class BashCommandSerializer(BaseDocumentSerializer):
    """
    操作系统日志
    """
    class Meta:
        model = BashCommandModel
        fields = '__all__'


class BgAccessLogSerializer(BaseDocumentSerializer):
    """
    应用系统日志
    """
    class Meta:
        model = BgAccessLogModel
        fields = '__all__'


class MysqlLogSerializer(BaseDocumentSerializer):
    """
    数据库日志
    """
    class Meta:
        model = MysqlLogModel
        fields = '__all__'


class OnlineTicketSerializer(BaseDocumentSerializer):
    """
    上线单
    """
    class Meta:
        model = OnlineTicketModel
        fields = '__all__'


class DeployTicketSerializer(BaseDocumentSerializer):
    """
    部署单
    """
    class Meta:
        model = DeployTicketModel
        fields = '__all__'
