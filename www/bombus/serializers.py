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

import datetime

from bombus.libs.baseserializer import BaseDocumentSerializer
from bombus.libs.enums import ProcessStatusEnum
from bombus.models import (AppComplianceModel, ComplianceDetailModel,
                           FeatureModel, OperationLogModel,
                           ProjectAuditLogEntry, SettingConfModel, ProjectTodoModel, ProjectStandingBookModel,
                           AppTodoModel, AppStandingBookModel)
from core.utils import utc2local


class ProjectAuditLogEntrySerializer(BaseDocumentSerializer):
    class Meta:
        model = ProjectAuditLogEntry
        fields = '__all__'


class OperationLogSerializer(BaseDocumentSerializer):
    """
    操作日志
    """
    class Meta:
        model = OperationLogModel
        fields = '__all__'


class FeatureSerializer(BaseDocumentSerializer):
    """
    审计任务
    """
    class Meta:
        model = FeatureModel
        fields = '__all__'

    def time_convert(self, validated_data):
        validated_data['expect_deadline'] = utc2local(validated_data['expect_deadline'])

    def create(self, validated_data):
        self.time_convert(validated_data)
        validated_data['created_time'] = datetime.datetime.now()
        validated_data['updated_time'] = datetime.datetime.now()
        validated_data['status'] = ProcessStatusEnum.UN_STARTED.name
        validated_data['submitter'] = validated_data['submitter']
        instance = super().create(validated_data)
        return instance

    def update(self, instance, validated_data):
        self.time_convert(validated_data)
        validated_data['updated_time'] = datetime.datetime.now()
        if ProcessStatusEnum[validated_data['status']] == ProcessStatusEnum.FINISHED:
            validated_data['actual_deadline'] = instance.actual_deadline or datetime.datetime.now()
        # 提交人逻辑
        origin_submitter = instance.submitter
        cur_submitter = validated_data['submitter']
        new_submitter = origin_submitter
        if not set(cur_submitter) <= set(origin_submitter):
            check_keys = ['title', 'desc', 'demander', 'priority', 'expect_deadline']
            changed = False
            for ck in check_keys:
                old_value = getattr(instance, ck, None)
                new_value = validated_data.get(ck, None)
                if old_value != new_value:
                    changed = True
                    break
            if changed:
                new_submitter.extend(cur_submitter)
        validated_data['submitter'] = new_submitter

        instance = super().update(instance, validated_data)
        return instance


class SettingConfSerializer(BaseDocumentSerializer):
    """
    后台配置项
    """
    class Meta:
        model = SettingConfModel
        fields = '__all__'


class AppComplianceSerializer(BaseDocumentSerializer):
    """
    app隐私合规
    """
    class Meta:
        model = AppComplianceModel
        fields = '__all__'

    def create(self, validated_data):
        validated_data['created_time'] = datetime.datetime.now()
        validated_data['updated_time'] = datetime.datetime.now()
        instance = super().create(validated_data)
        return instance


class ComplianceDetailSerializer(BaseDocumentSerializer):
    """
    评估发现
    """
    class Meta:
        model = ComplianceDetailModel
        fields = '__all__'

    def time_convert(self, validated_data):
        if validated_data.get('rectification_time'):
            validated_data['rectification_time'] = utc2local(validated_data['rectification_time'])

    def create(self, validated_data):
        self.time_convert(validated_data)
        validated_data['created_time'] = datetime.datetime.now()
        validated_data['updated_time'] = datetime.datetime.now()
        instance = super().create(validated_data)
        return instance

    def update(self, instance, validated_data):
        self.time_convert(validated_data)
        validated_data['updated_time'] = datetime.datetime.now()
        super().update(instance, validated_data)
        return instance


class AppStandingBookSerializer(BaseDocumentSerializer):
    """
    app隐私合规
    """
    class Meta:
        model = AppStandingBookModel
        fields = '__all__'

    def time_convert(self, validated_data):
        if validated_data.get('occur_time'):
            validated_data['occur_time'] = utc2local(validated_data['occur_time'])

    def create(self, validated_data):
        self.time_convert(validated_data)
        validated_data['created_time'] = datetime.datetime.now()
        validated_data['updated_time'] = datetime.datetime.now()
        instance = super().create(validated_data)
        return instance

    def update(self, instance, validated_data):
        self.time_convert(validated_data)
        validated_data['updated_time'] = datetime.datetime.now()
        super().update(instance, validated_data)
        return instance


class AppTodoSerializer(BaseDocumentSerializer):
    """
    评估发现
    """
    class Meta:
        model = AppTodoModel
        fields = '__all__'

    def create(self, validated_data):
        validated_data['created_time'] = datetime.datetime.now()
        validated_data['updated_time'] = datetime.datetime.now()
        instance = super().create(validated_data)
        return instance

    def update(self, instance, validated_data):
        validated_data['updated_time'] = datetime.datetime.now()
        super().update(instance, validated_data)
        return instance


class ProjectStandingBookSerializer(BaseDocumentSerializer):
    """
    专项管理台账
    """
    class Meta:
        model = ProjectStandingBookModel
        fields = '__all__'

    def create(self, validated_data):
        validated_data['created_time'] = datetime.datetime.now()
        validated_data['updated_time'] = datetime.datetime.now()
        instance = super().create(validated_data)
        return instance

    def update(self, instance, validated_data):
        validated_data['updated_time'] = datetime.datetime.now()
        super().update(instance, validated_data)
        return instance


class ProjectTodoSerializer(BaseDocumentSerializer):
    """
    评估发现
    """
    class Meta:
        model = ProjectTodoModel
        fields = '__all__'

    def create(self, validated_data):
        validated_data['created_time'] = datetime.datetime.now()
        validated_data['updated_time'] = datetime.datetime.now()
        instance = super().create(validated_data)
        return instance

    def update(self, instance, validated_data):
        validated_data['updated_time'] = datetime.datetime.now()
        super().update(instance, validated_data)
        return instance

