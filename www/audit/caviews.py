"""
审阅页面view
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

import datetime
import json
import logging
import re
from collections import defaultdict
from functools import partial

from bson.objectid import ObjectId
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.utils.functional import cached_property
from django.views import View

from audit.constant import DEFAULT_TRANS_ACTION, job_transfer_type
from audit.models import (AuditServerModel, AuditSysModel, AuditTaskModel,
                          BashCommandModel, BgAccessLogModel, DbUserRoleModel,
                          DeployTicketModel, EmployeePositionChangeDataModel,
                          LogSampleModel, MysqlLogModel,
                          NewReviewCommentModel, NonNormalUserModel,
                          OnlineTicketModel, ReviewCommentModel, RiskUserModel,
                          RuleAtomModel, ServerInfo, SysProjectModel,
                          UserRoleDataModel, UserSupplementInfo)
from audit.rule_handler import PeriodProxyHandler
from bombus.libs import permission_required
from bombus.libs.enums import ReviewTypeEnum, RuleTypeEnum, ServerKindEnum
from bombus.libs.exception import FastResponse
from bombus.services.message import EmailMessage
from bombus.services.mysql_service import (get_db_name_by_dept,
                                           get_db_node_by_host)
from bombus.services.user_service import UserService
from core.redis_conn import has_log_cache
from core.util import cache_util, time_util
from core.util.time_util import date2datetime, dt2stamp, today

logger = logging.getLogger(__name__)


@permission_required(settings.CA_REVIEW)
class ReviewView(View):
    """
    审阅页
    """
    def get_task_base_info(self, task_id):
        return AuditTaskModel.get_base_info(task_id)

    def service_account_filter(self):
        return {f'{self.user_column}': {'$not': {'$in': settings.SERVICE_ACCOUNT}}}

    def maybe_convert_normal_user(self, user_id):
        return NonNormalUserModel.get_normal_user(user_id, self.audit_sys_id, self.server_kind)

    def get_batch_ums_info(self, users):
        result = {}
        if not users:
            return result

        users = filter(None, map(str, users))
        ids = []
        emails = []
        for user in users:
            if user.isdigit():
                ids.append(user)
            else:
                emails.append(user)
        if emails:
            result.update(UserService.batch_get_user_by_email(emails))
        if ids:
            result.update(UserService.batch_get_user_by_accountid(ids))
        return result

    def get_ums_info(self, user_tag, user_map, ums_info):
        user = user_tag
        if user_map.get(user_tag):
            user = list(user_map[user_tag])[0]
        user_info = ums_info.get(user)
        if user_info:
            dept_name = user_info['dept_name']
            sec_dept_name = '-'.join(dept_name.split('-', 2)[:2])
            user_info['dept_name'] = sec_dept_name
        return user_info or {}

    def get_prepared_info(self, user_tags, server_kind=None):
        user_map = NonNormalUserModel.get_user_map(user_tags,
                                                   self.base_info['audit_sys_id'], server_kind or self.server_kind)
        clear_users = set()
        for v in user_map.values():
            clear_users |= set(v)
        users = list((set(user_tags) - set(user_map.keys())) | clear_users)
        batch_ums_info = self.get_batch_ums_info(users)
        return user_map, batch_ums_info

    def get_time_range(self, base_info):
        created_time = self.task_instance.created_time
        audit_period = base_info['audit_period']
        start_time, end_time = PeriodProxyHandler.time_range(audit_period, created_time)
        return start_time, end_time

    @cached_property
    def risk_info_date(self):
        now = datetime.datetime.now()
        target_date = min(now, self.period_end_time + datetime.timedelta(days=1))
        return date2datetime(target_date.date())

    def fmt_risk_reason(self, accountid, perm_risk_tag, job_risk_tag):
        """
        格式化异常信息
        """
        if not accountid:
            return ''

        risk_reason = []
        if perm_risk_tag:
            risk_user = RiskUserModel.objects.filter(
                audit_sys=self.audit_sys_id, user=accountid, record_date=self.risk_info_date).first()
            if risk_user:
                risk_reason.append(risk_user.risk_reason)
        if job_risk_tag:
            job_transfer = EmployeePositionChangeDataModel.objects.filter(
                modify_dt__lte=self.period_end_time,
                modify_dt__gt=self.period_start_time,
                accountid=accountid
            ).order_by('-modify_dt').first()
            if job_transfer:
                risk_reason.append(f'转岗至{job_transfer.department_after}')
        return ';'.join(risk_reason)

    def sample_filter(self):
        return {}

    def job_transfor_params(self):
        return {
            '$lookup': {
                'from': "job_transfer_risk",
                'localField': f"{self.joint_name}",
                'foreignField': f"{self.job_transfer_hit_column}",
                'as': "risk_users"
            },
        }

    @cached_property
    def yesterday_date(self):
        now = datetime.datetime.now()
        yesterday = now - datetime.timedelta(days=1)
        if yesterday < self.period_start_time:
            return None

        target_dt = yesterday
        if yesterday > self.period_end_time:
            target_dt = self.period_end_time
        return date2datetime(target_dt.date())

    def get_result(self, query_params):
        param_list = self.match_params(query_params) + [self.job_transfor_params()]
        result = list(self.model._get_collection().aggregate(param_list))
        return result

    def fill_fmt_risk_tag(self, result):
        if not result:
            return

        for item in result:
            item['perm_risk_tag'] = True in (item.get('risk_tag') or [])
            item['job_risk_tag'] = self.task_instance.id in [x['task'] for x in item.get('risk_users') or []]

    def get(self, request, *args, **kwargs):
        get_prms = request.GET
        self.task_id = get_prms.get('task_id')
        self.task_instance = AuditTaskModel.objects.get(id=self.task_id)
        self.base_info = base_info = self.get_task_base_info(self.task_id)
        self.period_start_time, self.period_end_time = self.get_time_range(base_info)

        resp_data = {}
        resp_data['show_columns'] = self.get_show_columns()
        resp_data['base_info'] = base_info
        resp_data['dept_names'] = []
        resp_data['results'] = []
        resp_data['count'] = 0
        if not base_info:
            return JsonResponse(data=resp_data)

        self.audit_sys_id = base_info['audit_sys_id']
        page = int(get_prms.get('page') or 1)
        page_size = int(get_prms.get('page_size') or 10)
        offset = (page - 1) * page_size

        query_params = self.format_query_params(base_info)
        sample_filter = self.sample_filter()
        date_filter = self.date_filter()
        page_filter = self.get_page_filter(get_prms)
        if query_params is not None and sample_filter is not None and date_filter is not None:
            resp_data['dept_names'] = self.get_result_dept_names(query_params, date_filter)
            query_params.update(self.service_account_filter())
            query_params.update(sample_filter)
            query_params.update(date_filter)
            query_params.update(page_filter)
            result = self.get_result(query_params)
            self.fill_fmt_risk_tag(result)
            result.sort(key=self.sort_key)
            total_count = len(result)
            result = self.get_prepared_result(result, offset, page_size)
            results = self.format_result(result)
            results.sort(key=lambda x: not bool(x['risk']))
            results = self.get_pagination_result(results, offset, page_size)
            self.fill_review_content(results)
            resp_data['results'] = results
            resp_data['count'] = total_count
        return JsonResponse(data=resp_data)

    def get_review_content(self, record_ids):
        result = ReviewCommentModel.get_review_content(task=self.task_id,
                                                       server_kind=self.server_kind,
                                                       review_type=self.review_type,
                                                       record_ids=record_ids)
        return result

    def fill_review_content(self, result):
        record_ids = [r['origin_name'] for r in result]
        review_content = self.get_review_content(record_ids)
        for item in result:
            record_id = item['origin_name']
            content = review_content.get(record_id) or ''
            item['review'] = content

    def get_page_filter(self, prms):
        """ 页面的过滤参数 """
        return {}

    def get_result_dept_names(self, query_params, date_params):
        return []

    def get_prepared_result(self, result, offset, page_size):
        return result[offset: offset+page_size]

    def get_pagination_result(self, result, offset, page_size):
        return result


class UserReviewView(ReviewView):
    """
    账号审阅页
    """
    joint_name = '_id'      # 与job_transfer_risk联表查询字段
    review_type = 'perm'
    REVIEW_TYPE = ReviewTypeEnum.APP.name

    def get_show_columns(self):
        return {
            'origin_name': '用户标识',
            'name': '用户',
            'dept_name': '所属部门',
            'roles': '角色/权限',
            'risk': '异常原因'
        }

    def date_filter(self):
        if not self.yesterday_date:
            return None
        return {'record_date': self.yesterday_date}

    def match_params(self, query_params):
        """
        查询mongo库, 过滤条件
        """
        return [
            {'$match': query_params},
            {'$group': {
                "_id": f'${self.user_column}',
                'create_dts': {'$addToSet': '$create_dt'},
                'roles': {'$addToSet': '$role'},
                'risk_tag': {'$addToSet': '$risk_tag'},
                'risk_sys': {'$addToSet': '$risk_sys'}
                }
            },
        ]

    def sort_key(self, item):
        perm_risk_tag = item['perm_risk_tag']
        job_risk_tag = item['job_risk_tag']
        create_dts = item.get('create_dts') or []
        create_dt = today()
        if create_dts:
            create_dt = create_dts[0]
        create_ts = dt2stamp(create_dt)
        risk_sys = item.get('risk_sys') or []
        hit_risk_sys = False
        if perm_risk_tag:
            for rs in risk_sys:
                if self.audit_sys_id in map(str, rs):
                    hit_risk_sys = True
                    break
            perm_risk_tag &= hit_risk_sys
        return -perm_risk_tag, -job_risk_tag, -create_ts, item['_id']

    def get_page_filter(self, prms):
        result = {}
        dept_name = prms.get('dept_name')
        if dept_name:
            result['dept_name'] = dept_name
        is_reviewed = prms.get('is_reviewed', None)
        if is_reviewed is not None:
            reviewed_ids = NewReviewCommentModel.get_reviewed_single_ids(self.task_id, self.REVIEW_TYPE)
            op = '$in'
            if is_reviewed == '0':
                op = '$nin'
            result[self.user_column] = {op: reviewed_ids}
        return result

    def get_result_dept_names(self, query_params, date_params):
        filter_params = {}
        filter_params.update(query_params)
        filter_params.update(date_params)
        result = self.model._get_collection().find(filter_params).distinct('dept_name')
        result = list(filter(None, result))
        result.sort()
        return result


class LogReviewView(ReviewView):
    """
    日志审阅页
    """
    joint_name = '_id.user'     # 与job_transfer_risk联表查询字段
    review_type = 'log'

    def get_show_columns(self):
        return {
            'origin_name': '用户标识',
            'rule_atom_name': '日志类型',
            'name': '用户',
            'count': '操作次数',
            'risk': '异常原因'
        }

    def date_filter(self):
        return {}

    def sample_filter(self):
        sample_ids = LogSampleModel.objects.\
            filter(task=self.task_id, server_kind=self.sample_server_kind).\
            values_list('final_sample').first()
        if sample_ids:
            return {'_id': {'$in': sample_ids}}
        else:
            return None

    def match_params(self, query_params):
        """
        查询mongo库, 过滤条件
        """
        return [
            {'$match': query_params},
            {"$unwind": '$hit_rule_atoms'},
            {'$group': {
                '_id': {'hit_rule_atom': '$hit_rule_atoms', 'user': f'${self.user_column}'},
                'count': {'$sum': 1},
                'risk_tag': {'$addToSet': '$risk_tag'}
                }
            },
        ]

    def sort_key(self, item):
        perm_risk_tag = item['perm_risk_tag']
        job_risk_tag = item['job_risk_tag']
        count = item['count']
        return -perm_risk_tag, -job_risk_tag, -count, item['_id']['user']


class AppUserReviewView(UserReviewView):
    """
    应用系统账号审阅页
    """
    server_kind = ServerKindEnum.APP.name
    job_transfer_hit_column = 'accountid'
    user_column = 'user'
    model = UserRoleDataModel

    def get_prepared_result(self, result, offset, page_size):
        return result

    def get_pagination_result(self, result, offset, page_size):
        return result

    def format_query_params(self, base_info):
        audit_sys_id = base_info['audit_sys_id']
        bg_names = AuditServerModel.get_server_name_list(audit_sys_id, self.server_kind)
        if not bg_names:
            return None
        query_params = {'bg_name': {'$in': bg_names}}
        return query_params

    def format_result(self, results):
        user_tags = [user_role['_id'] for user_role in results]
        user_map, batch_ums_info = self.get_prepared_info(user_tags)
        fmt_rs = []
        for user_role in results:
            ur_info = {}
            try:
                accountid = user_role['_id']
                ur_info['accountid'] = accountid
                ums_info = self.get_ums_info(accountid, user_map, batch_ums_info)
                ur_info['origin_name'] = accountid
                ur_info['name'] = ums_info.get('name')
                ur_info['dept_name'] = ums_info.get('dept_name')
                ur_info['roles'] = ';'.join(user_role['roles'])
                ur_info['risk_reason'] = self.fmt_risk_reason(
                    ums_info.get('accountid') or accountid, user_role['perm_risk_tag'], user_role['job_risk_tag']
                )
                fmt_rs.append(ur_info)
            except Exception as e:
                logger.exception('format user_info error for ur_info(%s)' % (ur_info))
        return fmt_rs


class SysUserReviewView(UserReviewView):
    """
    操作系统用户审阅
    """
    server_kind = ServerKindEnum.SA.name
    user_column = 'root_user'
    job_transfer_hit_column = 'email'
    model = ServerInfo

    def format_query_params(self, base_info):
        audit_sys_id = base_info['audit_sys_id']
        server_names = AuditServerModel.get_server_name_list(audit_sys_id, self.server_kind)
        if not server_names:
            return None
        query_params = {'server_name': {'$in': server_names}}
        return query_params

    def format_result(self, results):
        fmt_rs = []
        user_tags = [user_role['_id'] for user_role in results]
        user_map, batch_ums_info = self.get_prepared_info(user_tags)
        for res in results:
            ur_info = {}
            try:
                root_user = res['_id']
                ums_info = self.get_ums_info(root_user, user_map, batch_ums_info)
                ur_info['origin_name'] = root_user
                ur_info['name'] = ums_info.get('name')
                ur_info['dept_name'] = ums_info.get('dept_name')
                ur_info['roles'] = '操作系统管理员'
                ur_info['risk'] = self.fmt_risk_reason(
                    ums_info.get('accountid'), res['perm_risk_tag'], res['job_risk_tag']
                )
                fmt_rs.append(ur_info)
            except Exception as e:
                logger.exception(f'format user_info error for ur_info({ur_info})')
        return fmt_rs


class SysLogReviewView(LogReviewView):
    """
    操作系统日志审阅页面
    """
    sample_server_kind = server_kind = ServerKindEnum.SA.name
    model = BashCommandModel
    job_transfer_hit_column = 'email'
    user_column = 'user_name'

    def get_prepared_result(self, result, offset, page_size):
        return result

    def get_pagination_result(self, result, offset, page_size):
        return result[offset: offset+page_size]

    def format_result(self, results):
        fmt_rs = []
        user_tags = [user_role['_id']['user'] for user_role in results]
        user_map, batch_ums_info = self.get_prepared_info(user_tags)
        for result in results:
            tmp_data = {}
            try:
                uniq_data = result['_id']
                tmp_data['rule_atom_id'] = str(uniq_data['hit_rule_atom'])
                tmp_data['rule_atom_name'] = RuleAtomModel.get_name_by_id(tmp_data['rule_atom_id'])
                tmp_data['origin_name'] = uniq_data['user']
                tmp_data['count'] = result['count']
                ums_info = self.get_ums_info(tmp_data['origin_name'], user_map, batch_ums_info)
                if ums_info:
                    tmp_data['name'] = ums_info.get('name')
                    tmp_data['risk'] = self.fmt_risk_reason(
                        ums_info.get('accountid'), result['perm_risk_tag'], result['job_risk_tag']
                    )
                else:
                    tmp_data['name'] = ''
                    tmp_data['risk'] = '查不到该员工信息'
                fmt_rs.append(tmp_data)
            except Exception as e:
                logger.exception(f'format user_info error for ur_info({tmp_data})')
        return fmt_rs

    def format_query_params(self, base_info):
        audit_sys_id = base_info['audit_sys_id']
        server_names = AuditServerModel.get_server_name_list(audit_sys_id, self.server_kind)
        if not server_names:
            return None
        return {'server_name': {'$in': server_names}}


class AppLogReviewView(LogReviewView):
    """
    应用系统日志审阅页
    """
    sample_server_kind = server_kind = ServerKindEnum.APP.name
    model = BgAccessLogModel
    job_transfer_hit_column = 'accountid'
    user_column = 'user'
    joint_name = '_id'

    @cached_property
    def thirdparty_user_info(self):
        return UserSupplementInfo.user_info()

    def get_prepared_result(self, result, offset, page_size):
        return result

    def get_pagination_result(self, result, offset, page_size):
        return result[offset: offset+page_size]

    def format_result(self, results):
        fmt_rs = []
        user_tags = [user_role['_id'] for user_role in results]
        user_map, batch_ums_info = self.get_prepared_info(user_tags)
        for result in results:
            tmp_data = {}
            try:
                user = result['_id']
                tmp_data['rule_atom_name'] = '写操作'
                tmp_data['origin_name'] = user
                tmp_data['count'] = result['count']
                ums_info = self.get_ums_info(tmp_data['origin_name'], user_map, batch_ums_info)
                if ums_info:
                    tmp_data['name'] = ums_info.get('name')
                    tmp_data['risk'] = self.fmt_risk_reason(
                        ums_info.get('accountid') or user, result['perm_risk_tag'], result['job_risk_tag']
                    )
                else:
                    third_info = self.thirdparty_user_info.get(user)
                    if third_info:
                        tmp_data['name'] = third_info.get('name')
                        tmp_data['risk'] = ''
                    else:
                        tmp_data['name'] = ''
                        tmp_data['risk'] = '查不到该员工信息'
                fmt_rs.append(tmp_data)
            except Exception as e:
                logger.exception(f'format user_info error for ur_info({tmp_data})')
        return fmt_rs

    def match_params(self, query_params):
        """
        查询mongo库, 过滤条件
        """
        return [
            {'$match': query_params},
            {'$group': {
                '_id': f'${self.user_column}',
                'count': {'$sum': 1},
                'risk_tag': {'$addToSet': '$risk_tag'}
                }
            },
        ]

    def sort_key(self, item):
        perm_risk_tag = item['perm_risk_tag']
        job_risk_tag = item['job_risk_tag']
        count = item.get('count')
        return -perm_risk_tag, -job_risk_tag, -count, item['_id']

    def format_query_params(self, base_info):
        return {}


class DbLogReviewView(LogReviewView):
    """
    数据库日志审阅
    """
    sample_server_kind = server_kind = ServerKindEnum.DBA.name
    model = MysqlLogModel
    job_transfer_hit_column = 'email'
    user_column = 'user'

    def format_result(self, results):
        fmt_rs = []
        user_tags = [user_role['_id']['user'] for user_role in results]
        user_map, batch_ums_info = self.get_prepared_info(user_tags)
        for result in results:
            tmp_data = {}
            try:
                uniq_data = result['_id']
                tmp_data['rule_atom_id'] = str(uniq_data['hit_rule_atom'])
                tmp_data['rule_atom_name'] = RuleAtomModel.get_name_by_id(tmp_data['rule_atom_id'])
                tmp_data['origin_name'] = uniq_data['user']
                ums_info = self.get_ums_info(tmp_data['origin_name'], user_map, batch_ums_info)
                tmp_data['name'] = ums_info.get('name')
                tmp_data['count'] = result['count']
                tmp_data['risk'] = self.fmt_risk_reason(
                    ums_info.get('accountid') or uniq_data['user'], result['perm_risk_tag'], result['job_risk_tag']
                )
                fmt_rs.append(tmp_data)
            except Exception as e:
                logger.exception(f'format user_info error for ur_info({tmp_data})')
        return fmt_rs

    def format_query_params(self, base_info):
        return {}


class DbUserReviewView(UserReviewView):
    """
    数据库账号审阅页
    """

    server_kind = ServerKindEnum.DBA.name
    user_column = 'user'
    job_transfer_hit_column = 'email'
    model = DbUserRoleModel

    def format_query_params(self, base_info):
        audit_sys_id = base_info['audit_sys_id']
        server_names = AuditServerModel.get_server_name_list(audit_sys_id, self.server_kind)
        if not server_names:
            return None
        query_params = {'server_name': {'$in': server_names}}

        db_nodes = get_db_node_by_host(server_names)
        if db_nodes:
            node_params = {'db_node': {'$in': db_nodes}}
            query_params = {'$or': [query_params, node_params]}
        tips = AuditSysModel.get_fmt_db_dept_tip(base_info['audit_sys_id'])
        if tips:
            tip_db_map = get_db_name_by_dept(tips)
            db_names = set()
            for db in tip_db_map.values():
                db_names |= set(db)
            db_names = list(db_names)
            if db_names:
                db_params = {'$or': [{'db_name': {'$in': db_names}}, {'db_name': None}]}
                query_params = {'$and': [query_params, db_params]}
        return query_params

    def format_result(self, results):
        fmt_rs = []
        user_tags = [user_role['_id'] for user_role in results]
        user_map, batch_ums_info = self.get_prepared_info(user_tags)
        for res in results:
            ur_info = {}
            try:
                user = res['_id']
                ums_info = self.get_ums_info(user, user_map, batch_ums_info)
                ur_info['origin_name'] = user
                ur_info['name'] = ums_info.get('name')
                ur_info['dept_name'] = ums_info.get('dept_name')
                ur_info['roles'] = ';'.join(res['roles'])
                ur_info['risk'] = self.fmt_risk_reason(
                    ums_info.get('accountid') or user, res['perm_risk_tag'], res['job_risk_tag']
                )
                fmt_rs.append(ur_info)
            except Exception as e:
                logger.exception(f'format user_info error for ur_info({ur_info})')
        return fmt_rs


class PermApplyView(View):
    """
    审阅权限申请
    """
    def post(self, request, *args, **kwargs):
        post_prms = json.loads(request.body)
        server_kind = post_prms.get('server_kind')
        user = post_prms.get('user')
        task_id = post_prms.get('task_id')
        if not all([server_kind, user, task_id]):
            raise FastResponse(f'权限类型及待授权人不能为空')

        base_info = AuditTaskModel.get_base_info(task_id)
        sys_id = base_info['audit_sys_id']
        apply_user = request.user
        apply_user_accountid = UserService.get_user_by_email(apply_user.email).get('accountid') or ''
        if not apply_user_accountid:
            raise FastResponse(f'请登录后再试')
        if not AuditSysModel.is_auditor(sys_id, server_kind, apply_user_accountid):
            raise FastResponse(f'抱歉，您不是该权限类型审阅人，无权进行此操作')
        if AuditSysModel.is_auditor(sys_id, server_kind, user):
            raise FastResponse(f'该申请人已经为审阅人，请刷新页面')

        applyed_user = UserService.get_user_by_accountid(user)
        if not applyed_user:
            raise FastResponse(f'待授权人({user})不存在')
        push_content = f'您好，审阅人（{apply_user.username}）申请增加业务线({base_info["audit_sys_name"]})-' \
                       f'{ServerKindEnum[server_kind].desc}审阅人：{applyed_user.get("name")}({user}），请处理！'
        EmailMessage.batch_send_to_persons(push_content, settings.AUDIT_USERS)
        return JsonResponse(data={})


class NewReviewBaseView(ReviewView):

    @cached_property
    def last_date(self):
        """
        未完成: 显示最新数据  T-1,
        已完成: 显示完成当天看到的数据, 对应T-1
        """
        target_date = None
        if self.base_info['finished_time']:
            target_date = time_util.get_extra_time(self.base_info['finished_time'], step=-1, rounding_level='d')
        if not target_date:
            target_date = time_util.yesterday()
        return target_date

    @property
    def last_date_line(self):
        """ 通过时间范围查询的最后时间点"""
        return time_util.time_delta(self.last_date, forward='later', days=1)

    def init_task_info(self, task_id):
        """ 初始化task信息 """
        self.task_id = task_id
        self.task_instance = AuditTaskModel.objects.get(id=self.task_id)
        self.base_info = base_info = self.get_task_base_info(self.task_id)
        self.period_start_time, self.period_end_time = self.get_time_range(base_info)


# 审阅页优化, 合并上线单部署单, 账号日志
@permission_required(settings.CA_REVIEW)
class TicketReview(NewReviewBaseView):

    REVIEW_TYPE = ReviewTypeEnum.TICKET.name
    show_columns = {
        'email': '用户标识',
        'name': '用户',
        'dept_name': '所属部门',
        'projects': '负责项目',
        'deployers': '部署人',
        'deploy_risk_count': '异常部署次数',
        'review_content': '审阅意见'
    }

    def expand_task_info(self, task_id, review_type):
        """
        扩展任务信息, 上线单的审阅根据部门来, 需要将任务转化为部门 + 审阅周期
        """
        task_instance = AuditTaskModel.objects.get(id=task_id)
        period = task_instance.period
        if review_type == 'online':
            dept_tag = task_instance.task_manager.sys.online_ticket_dept_id
        else:
            dept_tag = task_instance.task_manager.sys.deploy_ticket_dept
        return {
            'dept': dept_tag,
            'period': period
        }

    def pick_data(self, data, columns):
        result = {}
        for col in columns:
            if col in data:
                result[col] = data[col]
        return result

    def get_all_online_ticket(self):
        """
        获取所有的上线单
        """
        dept = self.task_instance.task_manager.sys.deploy_ticket_dept
        queryset = DeployTicketModel.objects.filter(deploy_time__lt=self.last_date_line,
                                                    deploy_time__gt=self.period_start_time,
                                                    dept=dept)
        sys_id = self.base_info['cnf_sys_id']
        appkeys = SysProjectModel.get_appkey_by_sys_id(sys_id)
        if appkeys:
            queryset = queryset.filter(appkey__in=appkeys)
        ticket_ids = list(filter(None, queryset.distinct('ticket_id')))

        queryset = OnlineTicketModel.objects.filter(ticket_id__in=ticket_ids,
                                                    status__in=['ready', 'done'])
        result = {}
        if queryset.count() == 0:
            return result

        keep_columns = ['project', 'submitter']
        for item in queryset:
            item_data = item._data
            ticket_id = item_data['ticket_id']
            result[ticket_id] = self.pick_data(item_data, keep_columns)
        return result

    def get_risk_deploy_ticket(self):
        """
        获取异常部署单
        """
        dept = self.task_instance.task_manager.sys.deploy_ticket_dept
        queryset = DeployTicketModel.objects.filter(risk=True,
                                                    deploy_time__lt=self.last_date_line,
                                                    deploy_time__gt=self.period_start_time,
                                                    dept=dept)
        sys_id = self.base_info['cnf_sys_id']
        appkeys = SysProjectModel.get_appkey_by_sys_id(sys_id)
        if appkeys:
            queryset = queryset.filter(appkey__in=appkeys)

        result = []
        keep_columns = ['ticket_id', 'deployer']
        for item in queryset:
            item_data = item._data
            result.append(self.pick_data(item_data, keep_columns))
        return result

    def merge_ticket(self, online_ticket_data, deploy_list):
        """
        合并上线单部署单
        return:
            online_ticket_dict, unmatch_deploy_list
        """
        unmatched_deploy_list = []
        for deploy_item in deploy_list:
            ticket_id = deploy_item.get('ticket_id')
            if not ticket_id:
                unmatched_deploy_list.append(deploy_item)
                continue
            online_ticket = online_ticket_data.get(ticket_id)
            if online_ticket:
                deployer = deploy_item.get('deployer')
                online_ticket.setdefault('deployers', set()).add(deployer)
                online_ticket['risk_deploy_count'] = (online_ticket.get('risk_deploy_count') or 0) + 1
        return online_ticket_data, unmatched_deploy_list

    def fmt_user_result(self, fmt_online_ticket, unmatched_deploy_list) -> list:
        """
        按照人员信息聚合, 返回结果
        """
        user_result = defaultdict(dict)
        # 上线单数据按照员工聚合
        for tid, tinfo in fmt_online_ticket.items():
            submitter = tinfo['submitter']
            project = tinfo.get('project') or ''
            risk_deploy_count = tinfo.get('risk_deploy_count') or 0
            deployers = tinfo.get('deployers') or set()

            # 将上线单部署单数据写进用户
            user_email = submitter[0]['email']
            user_info = user_result[user_email]
            user_info['email'] = user_email
            user_info.setdefault('role', set()).add('submitter')
            user_info.setdefault('projects', set()).add(project)
            user_info['risk_deploy_count'] = (user_info.get('risk_deploy_count') or 0) + risk_deploy_count
            user_info.setdefault('ticket_ids', []).append(tid)
            user_info['deployers'] = user_info.get('deployers', set()) | deployers
        # 未匹配上线单按员工聚合
        for ud in unmatched_deploy_list:
            deployer = ud['deployer']
            user_info = user_result[deployer]
            user_info['email'] = deployer
            user_info.setdefault('role', set()).add('deployer')
            user_info.setdefault('deployers', set()).add(deployer)
            user_info['risk_deploy_count'] = (user_info.get('risk_deploy_count') or 0) + 1
        user_result = sorted(user_result.values(), key=lambda x: (-(x.get('risk_deploy_count') or 0), x['email']))
        for user in user_result:
            user['role'] = ','.join(list(user['role']))
            user['projects'] = self.drop_duplicate(','.join(list(user.get('projects') or set())))
        return user_result

    def drop_duplicate(self, item_str):
        """
        针对字符串再去重
        """
        item_list = re.split('[,;，；\s]', item_str)
        item_list = filter(None, [x.strip() for x in item_list])
        item_list = sorted(list(set(item_list)))
        return ', '.join(item_list)

    def fill_user_info(self, user_result):
        """
        填充个人部门, 名称, 审阅意见等
        """
        deployers_set = set()
        user_email_set = set()
        for x in user_result:
            user_email_set.add(x['email'])
            deployers_set |= x['deployers']
        emails = list(user_email_set | deployers_set)
        user_map, batch_ums_info = self.get_prepared_info(emails, ServerKindEnum.TICKET.name)
        review_content = NewReviewCommentModel.get_single_review_content(self.task_id, self.REVIEW_TYPE, user_email_set)
        for ur in user_result:
            user_info = self.get_ums_info(ur['email'], user_map, batch_ums_info)
            dept_name = user_info.get('dept_name') or ''
            ur['review_content'] = review_content.get(ur['email'])
            ur['name'] = user_info.get('name')
            ur['dept_name'] = '-'.join(dept_name.split('-', 2)[:2])
            ur['deployers'] = self.convert_email_set_to_names(ur['deployers'], batch_ums_info)
        return user_result

    def convert_email_set_to_names(self, deployers_set, user_infos):
        name_list = []
        for deployer in deployers_set:
            name = ((user_infos.get(deployer) or {}).get('name')) or deployer
            name_list.append(name)
        return ','.join(name_list)

    def filter_result(self, result, get_prms):
        """
        过滤
        """
        dept_name = get_prms.get('dept_name')
        if dept_name:
            result = filter(lambda x: x['dept_name'] == dept_name, result)
        is_reviewed = get_prms.get('is_reviewed', None)
        if is_reviewed is not None:
            if is_reviewed == 'true':
                result = filter(lambda x: not x.get('review_content'), result)
        return list(result)

    def get(self, request):
        get_prms = request.GET
        task_id = get_prms.get('task_id')
        self.init_task_info(task_id)

        resp = {}
        resp['show_columns'] = self.show_columns
        # 获取数据
        online_ticket_data = self.get_all_online_ticket()
        deploy_list = self.get_risk_deploy_ticket()
        fmt_online_ticket, unmatched_deploy_list = self.merge_ticket(online_ticket_data, deploy_list)
        user_result = self.fmt_user_result(fmt_online_ticket, unmatched_deploy_list)
        result = self.fill_user_info(user_result)
        # 根据结果抽取部门信息
        dept_names = sorted(list(filter(None, set([x['dept_name'] for x in result]))))
        resp['dept_names'] = [''] + dept_names
        # 过滤
        result = self.filter_result(result, get_prms)
        resp['user_count'] = len(result)
        resp['results'] = result

        return JsonResponse(data=resp)


log_cache_wrap = cache_util.CacheWrap(has_log_cache,
                                      expire=3600 * 24,
                                      time_range=0,
                                      time_cache_key=partial(time_util.time2str, fmt=time_util.DT_FMT_002))


@permission_required(settings.CA_REVIEW)
class NewUserReview(NewReviewBaseView):

    show_columns = {
        'origin_name': '用户标识',
        'name': '用户',
        'dept_name': '所属部门',
        'roles': '角色/权限',
        'risk_reason': '异常原因',
        'review_content': '审阅意见',
    }

    @cached_property
    def common_filter(self):
        params = {}
        params.update(self.date_filter())
        return params

    def date_filter(self):
        if not self.last_date:
            raise Exception('can not get the date of user !!!')
        return {'record_date': self.last_date}

    def fmt_risk_tags(self, users):
        for user in users:
            if self.base_info['audit_sys_id'] in map(str, user['risk_sys']):
                user['perm_risk_tag'] = user.get('risk_tag') or False
            else:
                user['perm_risk_tag'] = False

    def fmt_result(self, users):
        for user in users:
            user['roles'] = ','.join(sorted(list(user['roles'])))
            user.pop('risk_sys', None)
            user.pop('risk_tag', None)

    def get_transfer_risk_desc(self, accountid):
        reason = ''
        job_transfers = EmployeePositionChangeDataModel.objects.filter(
            modify_dt__lte=self.last_date_line,
            modify_dt__gt=self.period_start_time,
            accountid=accountid
        ).order_by('-modify_dt').all()
        if not job_transfers:
            return reason

        job_transfer_actions = [jt.action for jt in job_transfers]
        valid_reasons = list(job_transfer_type.keys())
        if set(job_transfer_actions) - set(valid_reasons):
            job_transfer_actions.append(DEFAULT_TRANS_ACTION)
        clean_risks = list(set(valid_reasons) & set(job_transfer_actions))
        clean_risks.sort(key=valid_reasons.index)
        hit_risk = clean_risks[0]
        if hit_risk == DEFAULT_TRANS_ACTION:
            hit_job_transfer = job_transfers[0]
            reason = f'转岗至{hit_job_transfer.department_after}'
        else:
            reason = job_transfer_type[hit_risk]
        return reason

    def get_user_risk_reason(self, accountid, perm_risk_tag):
        """
        获取异常原因及异常等级,
        风险排序 权限>转岗>离职
        """
        unrisk_level = 99999
        if not accountid:
            return '', unrisk_level
        reasons = []
        risk_levels = [unrisk_level]
        audit_sys_id = self.base_info['audit_sys_id']
        # 权限及离职异常及长期未使用异常
        if perm_risk_tag:
            risk_user = RiskUserModel.objects.filter(
                audit_sys=audit_sys_id, user=accountid, record_date=self.last_date).first()
            if risk_user:
                if risk_user.matrix_risk:
                    reasons.append(risk_user.matrix_risk)
                    risk_levels.append(1)
                if risk_user.staff_risk:
                    reasons.append(risk_user.staff_risk)
                    risk_levels.append(3)
                if risk_user.no_use_risk and self.NO_USE_RISK_SHOW:
                    reasons.append(risk_user.no_use_risk)
                    risk_levels.append(4)
        # 是否配置了转岗异常策略原子
        if AuditTaskModel.rule_type_is_configed(self.task_id, RuleTypeEnum.JOB_TRANS.name):
            # 转岗异常原因补充
            job_transfer_reason = self.get_transfer_risk_desc(accountid)
            if job_transfer_reason:
                reasons.append(job_transfer_reason)
                risk_levels.append(2)
        return ';'.join(reasons), min(risk_levels)

    def filter_result(self, result, get_prms):
        """
        过滤
        """
        dept_name = get_prms.get('dept_name')
        if dept_name:
            result = filter(lambda x: x['dept_name'] == dept_name, result)
        is_reviewed = get_prms.get('is_reviewed', None)
        if is_reviewed is not None:
            if is_reviewed == 'true':
                result = filter(lambda x: not x.get('review_content'), result)
        return list(result)

    def pick_roles(self, users):
        roles = set()
        for user in users:
            roles |= (user['roles'] or set())
        return sorted(list(roles))

    def role_filter(self, users):
        input_role = self.get_prms.get('role') or ''
        if not input_role:
            return users

        select_roles = set(input_role.split(',') or [])
        filter_users = []
        for user in users:
            roles = user['roles']
            hit_roles = select_roles & set(roles)
            if not hit_roles:
                continue
            user['roles'] = hit_roles
            filter_users.append(user)
        return filter_users

    def get(self, request):
        self.get_prms = get_prms = request.GET
        task_id = get_prms.get('task_id')
        self.init_task_info(task_id)

        resp = {}
        resp['show_columns'] = self.show_columns
        resp['all_roles'] = []
        if not self.date_filter:
            return

        users = self.get_users()
        self.fmt_risk_tags(users)
        self.fill_user_info(users)
        all_roles = self.pick_roles(users)
        users = self.role_filter(users)
        self.fmt_result(users)
        # 根据结果抽取特征
        dept_names = sorted(list(filter(None, set([x['dept_name'] for x in users]))))
        resp['dept_names'] = [''] + dept_names

        # 过滤
        result = self.filter_result(users, get_prms)

        # 最终结果排序
        result.sort(key=lambda x: (x['risk_level'], -dt2stamp(x['create_dt'])))
        resp['user_count'] = len(result)
        resp['results'] = result
        resp['all_roles'] = all_roles
        return JsonResponse(data=resp)

    @staticmethod
    # @log_cache_wrap
    def has_logs(log_type, task_id, origin_name):
        result = True
        if ReviewTypeEnum[log_type] == ReviewTypeEnum.APP:
            result = len(AppLogReview().get_logs(task_id, origin_name)) > 0
        else:
            result = len(SysDbLogReview().get_logs(task_id, origin_name)) > 0
        return result


@permission_required(settings.CA_REVIEW)
class AppUserReview(NewUserReview):
    """
    操作系统用户
    """
    REVIEW_TYPE = ReviewTypeEnum.APP.name
    NO_USE_RISK_SHOW = True

    def fill_user_info(self, users):
        """
        补充用户信息:  部门/姓名/异常原因/审阅意见
        """
        origin_names = [u['origin_name'] for u in users]
        user_map, batch_ums_info = self.get_prepared_info(origin_names, ServerKindEnum.APP.name)
        review_content = NewReviewCommentModel.get_single_review_content(self.task_id, self.REVIEW_TYPE, origin_names)
        for user in users:
            origin_name = user['origin_name']
            ums_info = self.get_ums_info(origin_name, user_map, batch_ums_info)
            user['name'] = ums_info.get('name')
            dept_name = ums_info.get('dept_name') or ''
            user['dept_name'] = '-'.join(dept_name.split('-', 2)[:2])
            user['review_content'] = review_content.get(origin_name)
            risk_reason, risk_level = self.get_user_risk_reason(ums_info.get('accountid'), user['perm_risk_tag'])
            user['risk_reason'] = risk_reason
            user['risk_level'] = risk_level
            user['has_logs'] = self.has_logs(self.REVIEW_TYPE, self.task_id, origin_name)

    def format_query_params(self):
        audit_sys_id = self.base_info['audit_sys_id']
        server_names = AuditServerModel.get_server_name_list(audit_sys_id, ServerKindEnum.APP.name)
        if not server_names:
            return None
        query_params = {'bg_name': {'$in': server_names}}
        return query_params

    def get_users(self):
        asset_filter = self.format_query_params()
        if not asset_filter:
            return []
        asset_filter.update(self.common_filter)
        user_list = list(UserRoleDataModel._get_collection().find(asset_filter))
        user_result = defaultdict(dict)
        for item_u in user_list:
            user_name = item_u['user']
            user_info = user_result[user_name]
            user_info['origin_name'] = user_name
            user_info.setdefault('roles', set()).add(item_u['role'])
            user_info['risk_tag'] = bool(user_info.get('risk_tag') or item_u.get('risk_tag'))
            user_info['risk_sys'] = user_info.get('risk_sys', set()) | set(item_u.get('risk_sys') or [])
            create_dt = item_u.get('create_dt') or item_u.get('record_date')
            if user_info.get('create_dt'):
                user_info['create_dt'] = max(user_info['create_dt'], create_dt)
            else:
                user_info['create_dt'] = create_dt
        user_list = user_result.values()
        return user_list


@permission_required(settings.CA_REVIEW)
class SysDbReview(NewUserReview):
    """
    数据库/操作系统账号合并
    """
    REVIEW_TYPE = ReviewTypeEnum.SYS_DB.name
    NO_USE_RISK_SHOW = False

    def fill_user_info(self, users):
        """
        补充用户信息:  部门/姓名/异常原因/审阅意见
        """
        emails = [u['origin_name'] for u in users]
        user_map, batch_ums_info = self.get_prepared_info(emails, ServerKindEnum.SYS_DB.name)
        review_content = NewReviewCommentModel.get_single_review_content(self.task_id, self.REVIEW_TYPE, emails)
        for user in users:
            origin_name = user['origin_name']
            ums_info = self.get_ums_info(origin_name, user_map, batch_ums_info)
            user['name'] = ums_info.get('name')
            dept_name = ums_info.get('dept_name') or ''
            user['dept_name'] = '-'.join(dept_name.split('-', 2)[:2])
            user['review_content'] = review_content.get(origin_name)
            risk_reason, risk_level = self.get_user_risk_reason(ums_info.get('accountid'), user['perm_risk_tag'])
            user['risk_reason'] = risk_reason
            user['risk_level'] = risk_level
            user['has_logs'] = self.has_logs(self.REVIEW_TYPE, self.task_id, origin_name)

    def get_users(self):
        db_users = self.get_db_users()
        sys_users = self.get_sys_users()
        all_users = {}
        all_users.update(sys_users)
        for name, info in db_users.items():
            if name in all_users:
                user_info = all_users[name]
                user_info['create_dt'] = max(user_info['create_dt'], info['create_dt'])
                user_info['roles'] = user_info['roles'] | info['roles']
                user_info['risk_tag'] = user_info['risk_tag'] | info['risk_tag']
                user_info['risk_sys'] = user_info['risk_sys'] | info['risk_sys']
            else:
                all_users[name] = info
        return list(all_users.values())

    def get_db_users(self):
        asset_filter = self.format_db_query_params()
        if not asset_filter:
            return {}
        asset_filter.update(self.common_filter)
        db_user_infos = list(DbUserRoleModel._get_collection().find(asset_filter))

        user_result = defaultdict(dict)
        for db_user in db_user_infos:
            user_name = db_user['user']
            user_info = user_result[user_name]
            user_info.setdefault('roles', set()).add(db_user['role'])
            user_info['origin_name'] = user_name
            user_info['risk_tag'] = bool(user_info.get('risk_tag') or db_user.get('risk_tag'))
            user_info['risk_sys'] = user_info.get('risk_sys', set()) | set(db_user.get('risk_sys') or [])
            create_dt = db_user.get('create_dt') or db_user.get('record_date')
            if user_info.get('create_dt'):
                user_info['create_dt'] = max(user_info['create_dt'], create_dt)
            else:
                user_info['create_dt'] = create_dt
        return user_result

    def get_sys_users(self):
        asset_filter = self.format_sys_query_params()
        if not asset_filter:
            return {}
        asset_filter.update(self.common_filter)
        sys_user_infos = list(ServerInfo._get_collection().find(asset_filter))
        user_result = defaultdict(dict)
        for sys_user in sys_user_infos:
            user_name = sys_user['root_user']
            user_info = user_result[user_name]
            user_info['origin_name'] = user_name
            user_info['roles'] = {'操作系统管理员'}
            user_info['risk_tag'] = bool(user_info.get('risk_tag') or sys_user.get('risk_tag'))
            user_info['risk_sys'] = user_info.get('risk_sys', set()) | set(sys_user.get('risk_sys') or [])
            create_dt = sys_user.get('create_dt') or sys_user.get('record_date')
            if user_info.get('create_dt'):
                user_info['create_dt'] = max(user_info['create_dt'], create_dt)
            else:
                user_info['create_dt'] = create_dt
        return user_result

    def format_sys_query_params(self):
        audit_sys_id = self.base_info['audit_sys_id']
        server_names = AuditServerModel.get_server_name_list(audit_sys_id, ServerKindEnum.SA.name)
        if not server_names:
            return None
        query_params = {'server_name': {'$in': server_names}}
        return query_params

    def format_db_query_params(self):
        audit_sys_id = self.base_info['audit_sys_id']
        server_names = AuditServerModel.get_server_name_list(audit_sys_id, ServerKindEnum.DBA.name)
        if not server_names:
            return None

        query_params = {'server_name': {'$in': server_names}}
        db_nodes = get_db_node_by_host(server_names)
        if db_nodes:
            node_params = {'db_node': {'$in': db_nodes}}
            query_params = {'$or': [query_params, node_params]}
        tips = AuditSysModel.get_fmt_db_dept_tip(self.base_info['audit_sys_id'])
        if tips:
            tip_db_map = get_db_name_by_dept(tips)
            db_names = set()
            for db in tip_db_map.values():
                db_names |= set(db)
            db_names = list(db_names)
            if db_names:
                db_params = {'$or': [{'db_name': {'$in': db_names}}, {'db_name': None}]}
                query_params = {'$and': [query_params, db_params]}
        return query_params


@permission_required(settings.CA_REVIEW)
class NewLogReview(NewReviewBaseView):

    def get(self, request):
        self.get_prms = get_prms = request.GET
        self.task_id = get_prms.get('task_id')
        self.user = get_prms.get('user')
        self.log_id = get_prms.get('log_id')
        if self.log_id:
            self.log_id = ObjectId(self.log_id)
        # 获取分页信息
        page = int(get_prms.get('page') or 1)
        page_size = int(get_prms.get('page_size') or 10)
        offset = (page - 1) * page_size

        resp = {}
        resp['show_columns'] = self.show_columns
        logs = self.get_logs(self.task_id, self.user, self.log_id)
        resp['count'] = len(logs)
        logs = logs[offset: offset+page_size]
        self.fill_log_info(logs)
        # 最终结果排序
        logs.sort(key=lambda x: x['time'], reverse=True)
        resp['results'] = logs
        return JsonResponse(data=resp)

    def init_task_info(self, task_id):
        """
        实例化全局task信息
        """
        self.task_id = task_id
        self.task_instance = AuditTaskModel.objects.get(id=task_id)
        self.base_info = self.get_task_base_info(task_id)
        self.period_start_time, self.period_end_time = self.get_time_range(self.base_info)

    def fill_log_info(self, logs):
        log_ids = [x['id'] for x in logs]
        review_content = NewReviewCommentModel.get_single_review_content(self.task_id, self.REVIEW_TYPE, log_ids)
        for l in logs:
            l['review_content'] = review_content.get(l['id'])


@permission_required(settings.CA_REVIEW)
class AppLogReview(NewLogReview):
    """
    应用系统日志
    """
    REVIEW_TYPE = ReviewTypeEnum.APP_LOG.name
    show_columns = {
        'host': '域名',
        'url': 'url',
        'params': '参数',
        'time': '执行时间'
    }

    def time_filter(self):
        return {'access_dt__lte': self.last_date_line, 'access_dt__gte': self.period_start_time}

    def rule_filter(self):
        """
        获取匹配规则过滤条件
        """
        return {'method__in': ['PUT', 'POST', 'DELETE'], 'params__not__in': [{}, None]}

    def get_asset_params(self):
        audit_sys_id = self.base_info['audit_sys_id']
        server_names = AuditServerModel.get_server_name_list(audit_sys_id, ServerKindEnum.APP.name)
        asset_column = 'bg_name'
        return {f'{asset_column}__in': server_names}

    def get_logs(self, task_id, user, log_id=None):

        if not user and not log_id:
            return []

        self.init_task_info(task_id)
        model = BgAccessLogModel

        query_prms = {}
        if log_id:
            query_prms = {'id': log_id}
        else:
            query_prms.update(self.time_filter())
            query_prms.update(self.get_asset_params())
            query_prms.update(self.rule_filter())
        if user:
            query_prms['user'] = user

        logs = list(model.objects.filter(**query_prms).order_by('-access_dt'))
        result = []
        for item in logs:
            fmt_log = {}
            fmt_log['id'] = str(item.id)
            fmt_log['user'] = item.user
            fmt_log['time'] = time_util.time2str(item.access_dt)
            fmt_log['url'] = item.url
            fmt_log['host'] = item.host
            fmt_log['params'] = str(item.params)
            fmt_log['type'] = 'app'
            result.append(fmt_log)
        return result


@permission_required(settings.CA_REVIEW)
class SysDbLogReview(NewLogReview):
    """
    操作系统/数据库日志
    """
    REVIEW_TYPE = ReviewTypeEnum.SYS_DB_LOG.name
    show_columns = {
        'server_name': '服务器名称',
        'db_name': '数据库名称',
        'command': '命令',
        'time': '执行时间'
    }

    @cached_property
    def common_filter(self):
        """
        公共参数, 事件区间过滤 & 命中规则过滤
        """
        time_filter = self.time_filter()
        rule_filter = self.rule_filter()
        result = {}
        result.update(time_filter)
        result.update(rule_filter)
        return result

    def time_filter(self):
        start_time_str = time_util.time2str(self.period_start_time)
        end_time_str = time_util.time2str(self.last_date_line)
        return {'time': {'$lte': end_time_str, '$gte': start_time_str}}

    def rule_filter(self):
        """
        获取匹配规则过滤条件
        """
        regex_rules = AuditTaskModel.get_regex_rules(self.task_id)
        if regex_rules:
            return {'hit_patterns': {'$in': [r.id for r in regex_rules]}}
        return {}

    def get_logs(self, task_id, user, log_id=None):
        self.init_task_info(task_id)
        db_logs = self.get_db_logs(task_id, user, log_id)
        sys_logs = self.get_sys_logs(task_id, user, log_id)
        logs = db_logs + sys_logs
        logs.sort(key=lambda x: x['time'], reverse=True)
        return logs

    def get_db_logs(self, task_id, user, log_id):
        """
        查询数据库日志
        """
        if not user and not log_id:
            return []

        query_prms = {}
        if log_id:
            query_prms = {'_id': log_id}
        else:
            query_prms.update(self.common_filter)
            query_prms.update(self.get_db_asset_params())

        if user:
            query_prms['user'] = user

        logs = list(MysqlLogModel._get_collection().find(query_prms))
        result = []
        for item in logs:
            fmt_log = {}
            fmt_log['id'] = str(item['_id'])
            fmt_log['user'] = item['user']
            fmt_log['time'] = item['time']
            fmt_log['db_name'] = item['db_name']
            fmt_log['command'] = item['sqltext']
            fmt_log['server_name'] = item['server_name']
            fmt_log['type'] = 'db'
            result.append(fmt_log)
        return result

    def get_db_asset_params(self):
        audit_sys_id = self.base_info['audit_sys_id']
        server_names = AuditServerModel.get_server_name_list(audit_sys_id, ServerKindEnum.DBA.name)
        if not server_names:
            return {'server_name': {'$in': []}}
        query_params = {'server_name': {'$in': server_names}}

        db_nodes = get_db_node_by_host(server_names)
        if db_nodes:
            node_params = {'db_node': {'$in': db_nodes}}
            query_params = {'$or': [query_params, node_params]}
        tips = AuditSysModel.get_fmt_db_dept_tip(self.base_info['audit_sys_id'])
        if tips:
            tip_db_map = get_db_name_by_dept(tips)
            db_names = set()
            for db in tip_db_map.values():
                db_names |= set(db)
            db_names = list(db_names)
            if db_names:
                db_params = {'$or': [{'db_name': {'$in': db_names}}, {'db_name': None}]}
                query_params = {'$and': [query_params, db_params]}
        return query_params

    def get_sys_asset_params(self):
        audit_sys_id = self.base_info['audit_sys_id']
        server_names = AuditServerModel.get_server_name_list(audit_sys_id, ServerKindEnum.SA.name)
        query_params = {'server_name': {'$in': server_names}}
        return query_params

    def get_sys_logs(self, task_id, user, log_id):
        """
        查询操作系统日志
        """
        if not user and not log_id:
            return []

        query_prms = {}
        if log_id:
            query_prms = {'_id': log_id}
        else:
            query_prms.update(self.common_filter)
            query_prms.update(self.get_sys_asset_params())

        if user:
            query_prms['user_name'] = user
        logs = list(BashCommandModel._get_collection().find(query_prms))
        result = []
        for item in logs:
            fmt_log = {}
            fmt_log['id'] = str(item['_id'])
            fmt_log['user'] = item['user_name']
            fmt_log['time'] = item['time']
            fmt_log['command'] = item['bash_command']
            fmt_log['server_name'] = item['server_name']
            fmt_log['db_name'] = ''
            fmt_log['type'] = 'sys'
            result.append(fmt_log)
        return result


class ServerListView(SysDbLogReview):
    """
    查询用户对应主机列表
    """

    def has_db_search_perm(self, user):
        """ 判断人员有没有数据库查询权限 """
        role_filter = self.get_db_asset_params()
        role_filter['role'] = '查询权限'
        role_filter['user'] = user
        roles = list(DbUserRoleModel._get_collection().find(role_filter).limit(1))
        return bool(roles)

    def get(self, request, *args, **kwargs):
        get_prms = request.GET
        task_id = get_prms.get('task_id')
        user = get_prms.get('user')
        self.init_task_info(task_id)
        base_info = self.get_task_base_info(task_id)
        sys_servers = list(AuditServerModel.objects.
                           filter(audit_sys=base_info.get('audit_sys_id'),
                                  server_kind__in=[ServerKindEnum.SA.name, ServerKindEnum.DBA.name]).
                           values_list('server_name'))
        params = {
            'record_date': self.last_date,
            'server_name__in': sys_servers,
        }

        sys_server_names = ServerInfo.objects.filter(**params, root_user=user).distinct('server_name')
        sys_server_role_map = dict.fromkeys(sys_server_names, {'操作系统管理员'})

        db_server_roles = DbUserRoleModel.objects.filter(**params, user=user).values_list('server_name', 'role')
        db_server_role_map = {}
        for db_server, role in db_server_roles:
            db_server_role_map.setdefault(db_server, set()).add(role)

        server_role_map = {}
        server_role_map.update(sys_server_role_map)
        for db_server, role_set in db_server_role_map.items():
            server_role_map[db_server] = role_set | (server_role_map.get(db_server) or set())

        statis_roles = ['操作系统管理员', '数据库主机操作系统管理员']
        statis_result = dict.fromkeys(statis_roles, 0)
        for _, role_set in server_role_map.items():
            for sr in statis_roles:
                if sr in role_set:
                    statis_result[sr] += 1

        fmt_server_role_map = {}
        for server, role_set in server_role_map.items():
            fmt_server_role_map[server] = ','.join(sorted(list(role_set)))

        result = {
            'results': fmt_server_role_map,
            'statis_result': statis_result,
            'has_search_perm': self.has_db_search_perm(user)
        }
        return JsonResponse(data=result)
