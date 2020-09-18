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
import json
import logging

from mongoengine import (BooleanField, DateTimeField, DictField, Document,
                         IntField, ListField, ReferenceField, StringField)
from mongoengine.queryset import DoesNotExist

from bombus.libs.enums import PriorityEnum, ProcessStatusEnum
from bombus.services.user_service import UserService
from core.util.time_util import time2str

logger = logging.getLogger(__name__)


class BaseModel(Document):
    """
    记录更新人, 更新时间
    """
    created_time = DateTimeField(required=False, verbose_name='创建时间', default=datetime.datetime.now())
    updated_time = DateTimeField(required=False, verbose_name='更新时间', default=datetime.datetime.now())
    deleted = BooleanField(required=False, verbose_name='是否删除', default=False)
    meta = {
        'abstract': True
    }

    @property
    def updated_time_render(self):
        if self.updated_time:
            return time2str(self.updated_time)
        return None

    def delete(self, **kwargs):
        try:
            self.deleted = True
            self.save()
        except Exception as e:
            logger.exception('delete error')


class ProjectAuditLogEntry(Document):
    req_time = DateTimeField(verbose_name='请求时间')
    req_user = StringField(verbose_name='请求用户')
    req_path = StringField(verbose_name='请求路径')
    req_method = StringField(verbose_name='请求方法')
    req_ip = StringField(verbose_name='请求IP')
    req_user_agent = StringField(verbose_name='请求UA')
    req_params = StringField(verbose_name='请求query_string')
    req_body = StringField(verbose_name='请求body')

    resp_status_code = IntField(verbose_name='响应码')
    resp_content_type = StringField(verbose_name='响应类型')
    resp_content = StringField(verbose_name='响应内容')

    meta = {
        'collection': 'project_audit_log_entry',
        'verbose_name': '合规平台审计日志',
        "indexes": [
            'req_time',
            'req_user',
            'req_path'
        ]
    }
    @property
    def req_time_render(self):
        return time2str(self.req_time)


class OperationLogModel(Document):
    """
    操作日志
    """
    name = StringField(required=False, verbose_name='名称')
    table_name = StringField(required=True, verbose_name='表名')
    table_id = StringField(required=True, verbose_name='操作id')
    content = StringField(required=True, verbose_name='快照')
    operate_type = StringField(required=True, verbose_name='操作类型')
    operate_time = DateTimeField(required=True, verbose_name='操作时间')
    operator = StringField(required=True, verbose_name='操作人')
    meta = {
        'collection': 'operation_log',
        'verbose_name': '操作日志',
        'orderding': ['-operate_time']
    }

    @property
    def operate_time_render(self):
        return time2str(self.operate_time)


class FeatureModel(BaseModel):
    """
    待办跟踪
    """
    title = StringField(required=True, verbose_name='标题', max_length=50, min_length=2)
    desc = StringField(required=True, verbose_name='需求描述', min_length=2)
    demander = StringField(required=True, verbose_name='需求方', min_length=2)
    priority = StringField(required=True, verbose_name='优先级', choices=PriorityEnum.choices(),
                           default=PriorityEnum.LOW)
    status = StringField(required=True, verbose_name='需求状态', choices=ProcessStatusEnum.choices(),
                         default=ProcessStatusEnum.UN_STARTED)
    expect_deadline = DateTimeField(required=True, verbose_name='预计完成时间')
    actual_deadline = DateTimeField(required=False, verbose_name='实际完成时间', null=True)
    submitter = ListField(required=True, verbose_name='提交人')
    implementer = StringField(required=True, verbose_name='执行人')
    meta = {
        'collection': 'feature',
        'verbose_name': '待办项跟踪',
        'indexes': [
            'submitter',
            'implementer',
            'updated_time',
            'created_time',
        ]
    }

    @property
    def status_render(self):
        return ProcessStatusEnum[self.status].desc

    @property
    def priority_render(self):
        return PriorityEnum[self.priority].desc

    @property
    def expect_deadline_render(self):
        return time2str(self.expect_deadline)

    @property
    def actual_deadline_render(self):
        if self.actual_deadline:
            return time2str(self.actual_deadline)
        return '-'

    @property
    def submitter_render(self):
        if not self.submitter:
            return '-'
        user_info = UserService.batch_get_user_by_email(self.submitter)
        names = []
        for email in self.submitter:
            name = (user_info.get(email) or {}).get('name')
            if name:
                names.append(name)
        return '，'.join(names) or '-'


class SettingConfModel(Document):
    """
    后台配置参数
    """
    meta = {
        'collection': 'setting_conf',
        'verbose_name': '后台配置参数',
        "auto_create_index": True,
        "index_background": True
    }
    conf_key = StringField(verbose_name='参数key', required=True, unique=True)
    desc = StringField(verbose_name='参数说明', required=True)
    content = StringField(verbose_name='参数值', required=False, null=True)

    @classmethod
    def get_conf_content(cls, conf_key):
        try:
            return cls.objects.get(conf_key=conf_key).content
        except DoesNotExist as e:
            return None
        except Exception as e:
            logger.exception(f'get setting by conf_key[{conf_key}] error')
            return None

    @classmethod
    def get_fmt_cnf(cls, conf_key, loads=True):
        """
        获取格式化的数据
        """
        content = cls.get_conf_content(conf_key)
        if content and loads:
            try:
                content = json.loads(content)
            except:
                logger.exception(f'loads {content} error for {conf_key}')
        return content


class AppComplianceModel(BaseModel):
    """
    APP隐私合规
    """
    meta = {
        'collection': 'app_compliance',
        'verbose_name': 'app隐私合规',
        'indexes': [
            'name'
        ]
    }
    name = StringField(required=True, verbose_name='app名称')
    app_status = StringField(required=False, verbose_name='app状态', null=True)
    version = StringField(required=False, verbose_name='当前版本', null=True)
    dept = StringField(required=True, verbose_name='所属部门')
    startup_subject = StringField(required=False, verbose_name='开办主体', null=True)
    principal = StringField(required=False, verbose_name='负责人', null=True)
    risk_assessment_report_url = ListField(DictField(), required=False, null=True, verbose_name='风险评估报告')
    security_commitment_url = ListField(DictField(), required=False, null=True, verbose_name='安全承诺书')
    remarks = StringField(required=False, verbose_name='备注', null=True)


class ComplianceDetailModel(BaseModel):
    meta = {
        'collection': 'compliance_detail',
        'verbose_name': '评估发现',
        'indexes': [
            'rectification_time'
        ]
    }
    app = ReferenceField(AppComplianceModel, required=True, verbose_name='APP主体')
    rectification_category = StringField(required=True, verbose_name='整改类型')
    promotion_dept = StringField(required=True, verbose_name='推进部门')
    status_description = StringField(required=False, verbose_name='现状说明', null=True)
    evaluation_basis = StringField(required=False, verbose_name='评估依据', null=True)
    rectification_program = StringField(required=False, verbose_name='整改方案', null=True)
    rectification_time = DateTimeField(required=True, verbose_name='整改时间', null=True)
    status = StringField(required=True, verbose_name='整改状态')

    @property
    def app_render(self):
        try:
            return self.app.name
        except:
            return self.app

    @property
    def rectification_time_render(self):
        if self.rectification_time:
            return time2str(self.rectification_time)
        return '-'
