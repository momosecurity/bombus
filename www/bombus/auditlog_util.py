"""
审计日志可读转化
"""

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

import json

from django.utils.functional import cached_property
from mongoengine.fields import ListField, ReferenceField

from audit.models import (AuditServerModel, AuditSysModel, AuditTaskModel,
                          BashCommandModel, BgAccessLogModel,
                          DeployTicketModel, MysqlLogModel,
                          NewMessageBoardModel, NewReviewCommentModel,
                          NonNormalUserModel, OnlineTicketModel,
                          RegexPatternModel, ReviewCommentModel, RuleAtomModel,
                          RuleGroupModel, TaskManagerModel,
                          TaskMessageBoardModel)
from bombus.libs.enums import CEnum, ServerKindEnum
from bombus.models import (AppComplianceModel, ComplianceDetailModel,
                           FeatureModel, OperationLogModel,
                           ProjectAuditLogEntry, SettingConfModel)
from knowledge.models import (RequireModel, TagModel, TagTypeModel,
                              TagTypePropertyModel)

AUDIT_PREFIX = 'audit'
SSO_PREFIX = 'sso'
KNOW_PREFIX = 'knowledge'
PREFIXS = [AUDIT_PREFIX, SSO_PREFIX, KNOW_PREFIX]
VIEW_MODEL_MAP = {
    # 审计
    f'{AUDIT_PREFIX}/server': AuditServerModel,
    f'{AUDIT_PREFIX}/sys': AuditSysModel,
    f'{AUDIT_PREFIX}/regex_rule': RegexPatternModel,
    f'{AUDIT_PREFIX}/rule_atom': RuleAtomModel,
    f'{AUDIT_PREFIX}/rule_group': RuleGroupModel,
    f'{AUDIT_PREFIX}/non_normal_user': NonNormalUserModel,
    f'{AUDIT_PREFIX}/task_manager': TaskManagerModel,
    f'{AUDIT_PREFIX}/task': AuditTaskModel,
    f'{AUDIT_PREFIX}/bash_command': BashCommandModel,
    f'{AUDIT_PREFIX}/review_comment': ReviewCommentModel,
    f'{AUDIT_PREFIX}/message_board': TaskMessageBoardModel,
    f'{AUDIT_PREFIX}/mysql_log': MysqlLogModel,
    f'{AUDIT_PREFIX}/bg_access_log': BgAccessLogModel,
    f'{AUDIT_PREFIX}/online_ticket': OnlineTicketModel,
    f'{AUDIT_PREFIX}/deploy_ticket': DeployTicketModel,
    f'{AUDIT_PREFIX}/new_review_comment': NewReviewCommentModel,
    f'{AUDIT_PREFIX}/new_message_board': NewMessageBoardModel,
    '/audit_log': ProjectAuditLogEntry,
    '/feature': FeatureModel,
    '/record-history': OperationLogModel,
    '/app-compliance': AppComplianceModel,
    '/compliance-detail': ComplianceDetailModel,
    '/settings': SettingConfModel,
    # 知识库
    f'{KNOW_PREFIX}/tag-type': TagTypeModel,
    f'{KNOW_PREFIX}/tag-type-property': TagTypePropertyModel,
    f'{KNOW_PREFIX}/tag': TagModel,
    f'{KNOW_PREFIX}/require': RequireModel,
}


VIEW_MAP = {
    '/search_user': {
        'name': '用户搜索',
        'fields': {'email': '搜索词'}
    },
    f'{SSO_PREFIX}/login': {
        'name': '登录',
    },
    f'{SSO_PREFIX}/user': {
        'name': '用户列表',
        'fields': {'name': '名称', 'email': '邮箱', 'password': '密码'}
    },
    f'{SSO_PREFIX}/perm_key': {
        'name': '权限列表',
        'fields': {'name': '名称', 'key': '权限key'}
    },
    f'{SSO_PREFIX}/logout': {
        'name': '退出登录',
    },
    f'{SSO_PREFIX}/authenticate': {
        'name': '登录验证',
        'fields': {'fromUrl': '上游路径'}
    },
    f'{SSO_PREFIX}/callback': {
        'name': '登录系统',
        'fields': {'accountid': '用户id'}
    },
    f'{AUDIT_PREFIX}/db_user_review': {
        'name': '数据库账号清单',
        'fields': {'task_id': '任务'},
        'value_render': {'task_id': AuditTaskModel.get_title_by_id}
    },
    f'{AUDIT_PREFIX}/db_log_review': {
        'name': '数据库日志清单',
        'fields': {'task_id': '任务'},
        'value_render': {'task_id': AuditTaskModel.get_title_by_id}
    },
    f'{AUDIT_PREFIX}/app_user_review': {
        'name': '应用系统账号清单',
        'fields': {'task_id': '任务'},
        'value_render': {'task_id': AuditTaskModel.get_title_by_id}
    },
    f'{AUDIT_PREFIX}/app_log_review': {
        'name': '应用系统日志清单',
        'fields': {'task_id': '任务'},
        'value_render': {'task_id': AuditTaskModel.get_title_by_id}
    },
    f'{AUDIT_PREFIX}/sys_user_review': {
        'name': '操作系统账号清单',
        'fields': {'task_id': '任务'},
        'value_render': {'task_id': AuditTaskModel.get_title_by_id}
    },
    f'{AUDIT_PREFIX}/sys_log_review': {
        'name': '操作系统日志清单',
        'fields': {'task_id': '任务'},
        'value_render': {'task_id': AuditTaskModel.get_title_by_id}
    },
    f'{AUDIT_PREFIX}/perm_apply': {
        'name': '代审阅人权限申请',
        'fields': {'task_id': '任务', 'user': '用户id', 'server_kind': '权限类型'},
        'value_render': {'task_id': AuditTaskModel.get_title_by_id, 'server_kind': lambda x: ServerKindEnum[x].desc}
    },
    f'{AUDIT_PREFIX}/ticket_list': {
        'name': '工单审阅',
        'fields': {'task_id': '任务'},
        'value_render': {'task_id': AuditTaskModel.get_title_by_id}
    },
    f'{AUDIT_PREFIX}/sys_db': {
        'name': '操作系统/数据库审阅',
        'fields': {'task_id': '任务'},
        'value_render': {'task_id': AuditTaskModel.get_title_by_id}
    },
    f'{AUDIT_PREFIX}/app_user': {
        'name': '应用系统审阅',
        'fields': {'task_id': '任务'},
        'value_render': {'task_id': AuditTaskModel.get_title_by_id}
    },
    f'{AUDIT_PREFIX}/sys_db_log': {
        'name': '操作系统/数据库日志查看',
        'fields': {'task_id': '任务', 'user': '用户'},
        'value_render': {'task_id': AuditTaskModel.get_title_by_id}
    },
    f'{AUDIT_PREFIX}/app_log': {
        'name': '应用系统日志查看',
        'fields': {'task_id': '任务', 'user': '用户id'},
        'value_render': {'task_id': AuditTaskModel.get_title_by_id}
    },


}


class DataWrap:
    def __init__(self, data):
        self.data = data

    @property
    def operation_name(self):
        return self.data['name']

    @cached_property
    def fields(self):
        return list((self.data.get('fields') or {}).keys())

    def get_name_by_id(self, id):
        return self.data['name']

    def get_filed_name(self, field):
        fields = self.data.get('fields') or {}
        return fields.get(field) or field

    def get_value_name(self, field, v):
        value_render_func = (self.data.get('value_render') or {}).get(field)
        if not value_render_func:
            return v
        else:
            return value_render_func(v)

    def kv_render(self, k, v):
        k_render = self.get_filed_name(k)
        v_render = self.get_value_name(k, v)
        return f'{k_render}:{v_render}'


class ModelWrap:

    NAME_COLUMNS = ['name', 'sys_name', 'title',  'desc', 'content', 'rectification_category']

    def __init__(self, model):
        self.model = model
        self.meta = self.model._meta

    @property
    def operation_name(self):
        return self.meta.get('verbose_name') or self.meta.get('collection')

    def get_name_by_id(self, id):
        try:
            instance = self.model.objects.get(id=id)
            for name in self.NAME_COLUMNS:
                instance_name = getattr(instance, name, '')
                if instance_name:
                    return instance_name
            return id
        except:
            return id

    @cached_property
    def fields(self):
        return self.model._fields

    def get_field_name(self, field):
        verbose_name = getattr(getattr(self.model, field), 'verbose_name', None)
        return verbose_name

    def check_special(self, k, v):
        """
        需要特殊处理的键值对
        """
        if self.model == OperationLogModel and k == 'table_id':
            try:
                v = self.model.objects.filter(**{k: v}).order_by('-operate_time')[0]
                return f'对象: {v.table_name}-{v.name}'
            except:
                return None
        elif self.model == RequireModel and k == 'tags':
            if isinstance(v, str):
                fmt_v = v.split(',')
                return self.kv_render(k, fmt_v)
        return None

    def kv_render(self, k, v):
        if k not in self.fields:
            return ''
        if k in ['id', 'last_update', 'last_update_person']:
            return ''

        special_result = self.check_special(k, v)
        if special_result:
            return special_result

        v_render = str(v)
        column = getattr(self.model, k)
        k_render = getattr(column, 'verbose_name', k)
        choices = getattr(column, 'choices')
        if choices:
            default = getattr(column, 'default')
            if default:
                if isinstance(default, CEnum):
                    v_render = type(default)[v].desc
        if isinstance(column, ListField):
            if v:
                v_render_result = []
                field = column.field
                if isinstance(field, ReferenceField):
                    document_type_obj = field.document_type_obj
                    for v_item in v:
                        v_item_render = ModelWrap(document_type_obj).get_name_by_id(v_item)
                        v_render_result.append(v_item_render)
                v_render = ';'.join(v_render_result)
        if isinstance(column, ReferenceField):
            if v:
                v_render = ModelWrap(column.document_type_obj).get_name_by_id(v)
        return f'{k_render}:{v_render}'


class ReadableLog:

    URL_PREFIX = '/api/'
    INHERIT_FIELDS = ['req_user', 'req_time_render', 'resp_content']
    KEY_NAME_MAP = {
        'page': '页码',
        'page_size': '页容量',
        'req_time_left': '早于时间点',
        'req_time_right': '晚于时间点'
    }

    def __init__(self, item):
        self.data = item

    def split_path(self, path):
        """
        拆分请求路径, 返回路径名称, id_field
        """
        id_query = ''
        clear_path = path.replace(self.URL_PREFIX, '')
        app_prefix, _, source_path = clear_path.partition('/')
        if app_prefix not in PREFIXS:
            source_path = clear_path
            app_prefix = ''
        path_name, _, id_params = source_path.partition('/')
        if id_params:
            id_query, _, query_params = id_params.partition('/')
        return f'{app_prefix}/{path_name}', id_query

    def kv_render(self, key, value, handler):
        if key in self.KEY_NAME_MAP:
            key_render = self.KEY_NAME_MAP[key]
            value_render = value
            return f'{key_render}: {value_render}'
        else:
            return handler.kv_render(key, value)

    def fmt_params(self, params, handler):
        fmt_prm_list = []
        for k, v in params.items():
            kv_desc = self.kv_render(k, v, handler)
            if kv_desc:
                fmt_prm_list.append(kv_desc)
        return '; '.join(fmt_prm_list) or '无'

    def fmt(self):
        item = self.data
        path_name, id_query = self.split_path(item['req_path'])
        handler = None
        if path_name in VIEW_MODEL_MAP:
            model = VIEW_MODEL_MAP[path_name]
            handler = ModelWrap(model)
        elif path_name in VIEW_MAP:
            data = VIEW_MAP[path_name]
            handler = DataWrap(data)
        if not handler:
            return item

        fmt_item = {}
        for _field in self.INHERIT_FIELDS:
            fmt_item[_field] = item[_field]
        fmt_item['operation_on'] = handler.operation_name

        req_method = item['req_method']
        fmt_func_name = f'_fmt_{req_method.lower()}'
        fmt_func = getattr(self, fmt_func_name, None)
        if fmt_func and callable(fmt_func):
            func_res = fmt_func(item, id_query, handler)
            if func_res:
                fmt_item.update(func_res)
        return fmt_item

    def _fmt_get(self, item, id_query, handler):
        result = {}
        action = '查看列表'
        query_params = json.loads(item['req_params'] or '{}')
        if id_query:
            instance_name = handler.get_name_by_id(id_query)
            action = f'查看详情【{instance_name}】'
        else:
            if 'page' not in query_params:
                query_params['page'] = 1
            if 'page_size' not in query_params:
                query_params['page_size'] = 10
        result['action'] = action
        result['content'] = self.fmt_params(query_params, handler)
        return result

    _fmt_options = _fmt_get

    def _fmt_post(self, item, id_query, handler):
        result = {}
        action = '新增'
        result['action'] = action
        req_body = json.loads(item['req_body'] or '{}')
        result['content'] = self.fmt_params(req_body, handler)
        return result

    def _fmt_patch(self, item, id_query, handler):
        result = {}
        action = '更新'
        instance_name = handler.get_name_by_id(id_query)
        req_body = json.loads(item['req_body'] or '{}')
        result['action'] = f'{action}【{instance_name}】'
        result['content'] = self.fmt_params(req_body, handler)
        return result

    def _fmt_delete(self, item, id_query, handler):
        result = {}
        action = '删除'
        instance_name = handler.get_name_by_id(id_query)
        result['action'] = f'{action}【{instance_name}】'
        result['content'] = ''
        return result
