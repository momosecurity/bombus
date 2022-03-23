"""
注意: 执行前会清除数据, 只用于初始化
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

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from audit.models import (AuditServerModel, AuditSysModel, AuditTaskModel,
                          BashCommandModel, BgAccessLogModel, DbUserRoleModel,
                          DeployTicketModel, EmployeePositionChangeDataModel,
                          MysqlLogModel, OnlineTicketModel, RegexPatternModel,
                          RuleAtomModel, RuleGroupModel, ServerInfo,
                          SysProjectModel, TaskManagerModel,
                          TicketApproveModel, UserRoleDataModel)
from bombus.libs.enums import (AuditPeriodEnum, OnOfflineStatusEnum,
                               RuleTypeEnum, ServerKindEnum)
from bombus.models import AppComplianceModel, FeatureModel, AppStandingBookModel, AppTodoModel, \
    ProjectStandingBookModel, ProjectTodoModel
from bombus.services.user_model import Employee
from core.util import time_util
from knowledge.models import (RequireModel, TagModel, TagTypeModel,
                              TagTypePropertyModel, PolicyTraceModel, SupervisionModel)
from ssologin.models import PermissionKeyModel


class Command(BaseCommand):

    regex_pattern_info = [
        {'regex': 'sudo|create user', 'desc': '样例'}
    ]
    audit_sys_list = [
        {
            'sys_id': 'ca',
            'name': '合规后台',
            'bg_alias': 'ca_bg',
            'db_dept_tip': '合规',
            'online_ticket_dept_id': 'dept_id_1',
            'deploy_ticket_dept': 'dept_id_1',
            'app_auditor': '10002',
            'sys_db_auditor': '10002',
            'ticket_auditor': '10002',
        }
    ]
    constant_server = [
        {
            'sys_id': 'ca',
            'server_kind': ServerKindEnum.SA.name,
            'servers': ['ca.server1.com', 'ca.server2.com'],
            'server_type': 'linux'
        },
        {
            'sys_id': 'ca',
            'server_kind': ServerKindEnum.DBA.name,
            'servers': ['ca.mysql1.com', 'ca.mysql2.com'],
            'server_type': 'mysql'
        },
    ]
    perm_keys = [
        {'key':'ca_asset:read', 'name': '资产列表读', 'desc': '查看资产列表'},
        {'key':'ca_conf:read', 'name': '配置读', 'desc': '查看策略配置'},
        {'key':'ca_conf:write', 'name': '配置写', 'desc': '更新策略配置'},
        {'key':'ca_log:read', 'name': '审计日志读', 'desc': '查看审计日志'},
        {'key':'ca_review:read', 'name': '审阅报告读', 'desc': '查看审阅报告'},
        {'key':'ca_review:write', 'name': '审阅报告写', 'desc': '回复审阅意见'},
        {'key':'ca_task:read', 'name': '任务列表读', 'desc': '查看任务列表'},
        {'key':'ca_task:write', 'name': '任务列表写', 'desc': '更新任务列表'},
        {'key': 'ca_knowledge:read', 'name': '知识库读', 'desc': '查看知识库'},
        {'key': 'ca_knowledge:write', 'name': '知识库写', 'desc': '更新知识库'},
    ]
    employee_list = [
        {'employee_id': '10000', 'employee_name': 'admin', 'email': 'admin'},
        {'employee_id': '10002', 'employee_name': 'auditor', 'email': 'auditor'},
        {'employee_id': '40001', 'employee_name': '40001', 'email': '40001a'},
        {'employee_id': '40002', 'employee_name': '40002', 'email': '40002a'},
        {'employee_id': '40003', 'employee_name': '40003', 'email': '40003a'},
        {'employee_id': '40004', 'employee_name': '40004', 'email': '40004a'},
        {'employee_id': '40005', 'employee_name': '40005', 'email': '40005a'},
        {'employee_id': '40006', 'employee_name': '40006', 'email': '40006a'},
        {'employee_id': '40007', 'employee_name': '40007', 'email': '40007a'},
        {'employee_id': '40008', 'employee_name': '40008', 'email': '40008a'},
        {'employee_id': '40009', 'employee_name': '40009', 'email': '40009a', 'status': False},
        {'employee_id': '40010', 'employee_name': '40010', 'email': '40010a'},
    ]
    bg_user_role = [
        {'user': '40001', 'role': '管理员'},
        {'user': '40002', 'role': '管理员'},
        {'user': '40003', 'role': '管理员'},
        {'user': '40004', 'role': '列表查看'},
        {'user': '40005', 'role': '列表查看'},
        {'user': '40006', 'role': '列表查看'},
        {'user': '40007', 'role': '更新配置'},
        {'user': '40008', 'role': '更新配置'},
        {'user': '40009', 'role': '更新配置'},
        {'user': '40010', 'role': '更新配置'},
        {'user': '40001', 'role': '更新配置'},
    ]
    db_user_role = [
        # user对应email
        {'user': '40001a', 'role': '数据库管理员', 'server_name': 'ca.mysql1.com'},
        {'user': '40002a', 'role': '数据库管理员', 'server_name': 'ca.mysql1.com'},
        {'user': '40003a', 'role': '查询权限', 'server_name': 'ca.mysql1.com'},
        {'user': '40004a', 'role': '查询权限', 'server_name': 'ca.mysql2.com'},
        {'user': '40005a', 'role': '查询权限', 'server_name': 'ca.mysql2.com'},
        {'user': '40006a', 'role': '查询权限', 'server_name': 'ca.mysql2.com'},
        {'user': '40007a', 'role': '查询权限', 'server_name': 'ca.mysql2.com'},
    ]
    sys_root_user = [
        # root_user对应email
        {'root_user': '40008a', 'server_name': 'ca.server1.com'},
        {'root_user': '40008a', 'server_name': 'ca.server2.com'},
        {'root_user': '40003a', 'server_name': 'ca.server1.com'},
        {'root_user': '40004a', 'server_name': 'ca.server2.com'},
    ]
    bg_log_list = [
        {'user': '40001', 'url': '/'},
        {'user': '40001', 'url': '/?a=b'},
        {'user': '40001', 'url': '/?c=d'},
        {'user': '40002', 'url': '/'},
        {'user': '40003', 'url': '/test'},
        {'user': '40004', 'url': '/test1', 'access_dt': time_util.time_delta(time_util.today(), days=50)}
    ]
    bash_command_list = [
        {'source_id': '1', 'user_name': '40003a', 'bash_command': 'sudo1'},
        {'source_id': '2', 'user_name': '40003a', 'bash_command': 'sudo pip'},
        {'source_id': '3', 'user_name': '40004a', 'bash_command': 'sudo pip'}
    ]
    mysql_log_list = [
        {'source_id': 'a', 'user': '40001a', 'sqltext': 'create user'},
        {'source_id': 'b', 'user': '40007a', 'sqltext': 'create user'},
        {'source_id': 'c', 'user': '40007a', 'sqltext': 'create user abc'}
    ]

    last_update_person = 'admin'

    def init_admin_user(self):
        User.objects.create_superuser(username='admin', password='admin', email='admin@ca.com')
        User.objects.create_user(username='auditor', password='auditor', email='auditor@ca.com')

    def init_audit_sys(self):
        AuditSysModel.objects.delete()
        AuditServerModel.objects.delete()
        for sys_info in self.audit_sys_list:
            name = sys_info.pop('name', None)
            bg_alias = sys_info.pop('bg_alias', None)
            sys = AuditSysModel(**sys_info,
                                sys_name=name,
                                last_update=self.now,
                                last_update_person=self.last_update_person).save()
            AuditServerModel(server_name=name,
                             server_kind=ServerKindEnum.APP.name,
                             server_type='应用',
                             audit_sys=sys.id,
                             bg_alias=bg_alias).save()
        for server_cnf in self.constant_server:
            sys_id = server_cnf['sys_id']
            sys_instance = AuditSysModel.objects.get(sys_id=sys_id)
            server_kind = server_cnf['server_kind']
            name_list = server_cnf['servers']
            server_type = server_cnf['server_type']
            for name in name_list:
                AuditServerModel(server_name=name,
                                 server_kind=server_kind,
                                 server_type=server_type,
                                 audit_sys=sys_instance).save()

    def init_regex_rule(self):
        RegexPatternModel.objects().delete()
        for regex_pattern in self.regex_pattern_info:
            regex_pattern['name'] = regex_pattern['desc']
            RegexPatternModel(last_update=self.now, last_update_person=self.last_update_person, **regex_pattern).save()

    def init_rule_atom(self):
        RuleAtomModel.objects.delete()
        all_regex = RegexPatternModel.objects().all()

        # 正则策略原子
        RuleAtomModel(
            last_update=self.now,
            last_update_person=self.last_update_person,
            name='写操作检测',
            status=OnOfflineStatusEnum.ONLINE.name,
            rule_type=RuleTypeEnum.REGEX.name,
            desc='写操作检测样例',
            regex_pattern=all_regex
        ).save()
        # 权限矩阵原子
        RuleAtomModel(
            last_update=self.now,
            last_update_person=self.last_update_person,
            name='权限矩阵判定',
            status=OnOfflineStatusEnum.ONLINE.name,
            rule_type=RuleTypeEnum.PERM.name,
            desc='权限矩阵原子'
        ).save()
        # 长期未使用策略原子
        RuleAtomModel(
            last_update=self.now,
            last_update_person=self.last_update_person,
            name='长期未访问判定原子',
            status=OnOfflineStatusEnum.ONLINE.name,
            rule_type=RuleTypeEnum.NO_USE.name,
            desc='对45天之内没有过日志操作的员工进行标识'
        ).save()
        # 转岗策略原子
        RuleAtomModel(
            last_update=self.now,
            last_update_person=self.last_update_person,
            name='转岗判定原子',
            status=OnOfflineStatusEnum.ONLINE.name,
            rule_type=RuleTypeEnum.JOB_TRANS.name,
            desc='针对转岗员工权限保留的情况'
        ).save()

    def init_rule_group(self):
        RuleGroupModel.objects.delete()
        all_rule_atoms = RuleAtomModel.objects.all()
        RuleGroupModel(
            last_update=self.now,
            last_update_person=self.last_update_person,
            name='策略组',
            status=OnOfflineStatusEnum.ONLINE.name,
            atoms=all_rule_atoms,
            audit_period=AuditPeriodEnum.QUARTER.name
        ).save()

    def init_perm_key(self):
        PermissionKeyModel.objects.delete()
        for item in self.perm_keys:
            PermissionKeyModel(**item).save()

    def init_task_config(self):
        audit_sys = AuditSysModel.objects.first()
        rule_group = RuleGroupModel.objects.first()
        TaskManagerModel.objects.delete()
        AuditTaskModel.objects.delete()
        TaskManagerModel(
            last_update=self.now,
            last_update_person=self.last_update_person,
            name='任务配置',
            desc='配置任务, 按期生成新的任务实例',
            sys=audit_sys,
            rule_group=rule_group,
            follow_up_person=self.last_update_person,
            status=OnOfflineStatusEnum.ONLINE.name
        ).save()

    def init_mock_employee_info(self):
        Employee.objects.delete()
        for ei in self.employee_list:
            ei['dept_name'] = 'CA部门'
            if 'status' not in ei:
                ei['status'] = True
            Employee(**ei).save()

    def init_job_transfor_data(self):
        data = {
            "employee_id": "111111",
            "accountid": "40010",
            "name": "40010",
            "title_before": "开发工程师",
            "title_after": "测试工程师",
            "department_before": "部门1",
            "department_after": "部门2",
            "modify_dt": self.yesterday,
            "action": "huibao"
        }
        EmployeePositionChangeDataModel(**data).save()

    def init_mock_task_data(self):
        now = datetime.datetime.now()
        yesterday = now.date() - datetime.timedelta(days=1)
        UserRoleDataModel.objects.delete()
        for bg_user in self.bg_user_role:
            bg_user['bg_name'] = 'ca_bg'
            bg_user['record_date'] = yesterday
            bg_user['create_dt'] = now
            UserRoleDataModel(**bg_user).save()
        DbUserRoleModel.objects.delete()
        for db_role in self.db_user_role:
            db_role['record_date'] = yesterday
            DbUserRoleModel(**db_role).save()
        ServerInfo.objects.delete()
        for root_user in self.sys_root_user:
            root_user['record_date'] = yesterday
            ServerInfo(**root_user).save()

        log_day = time_util.yesterday()
        constant_bg_log = {
            'host': 'ca.bg.com',
            'bg_name': 'ca_bg',
            'params': {'a': 'b'},
            'method': 'POST',
            'ip': '1.1.1.1',
            'ua': 'ua test',
            'access_dt': log_day,
        }
        all_regex = RegexPatternModel.objects().all()
        constant_sys_log = {
            'server_name': 'ca.server1.com',
            'server_ip': '1.1.1.1',
            'client_ip': '127.0.0.1',
            'time': datetime.datetime.strftime(log_day, '%Y-%m-%d %H:%M:%S'),
            'hit_patterns': all_regex
        }
        constant_mysql_log = {
            'server_name': 'ca.mysql1.com',
            'db_node': None,
            'db_name': 'ca',
            'cmd_source': 'demo',
            'time': datetime.datetime.strftime(log_day, '%Y-%m-%d %H:%M:%S'),
            'hit_patterns': all_regex,
        }
        BgAccessLogModel.objects.delete()
        BashCommandModel.objects.delete()
        MysqlLogModel.objects.delete()
        for bg_log in self.bg_log_list:
            tmp_info = {}
            tmp_info.update(constant_bg_log)
            tmp_info.update(bg_log)
            BgAccessLogModel(**tmp_info).save()
        for sys_log in self.bash_command_list:
            sys_log.update(constant_sys_log)
            BashCommandModel(**sys_log).save()
        for mysql_log in self.mysql_log_list:
            mysql_log.update(constant_mysql_log)
            MysqlLogModel(**mysql_log).save()

    def init_knowledge_data(self):
        RequireModel.objects.delete()
        TagModel.objects.delete()
        TagTypePropertyModel.objects.delete()
        TagTypeModel.objects.delete()
        tag_type = TagTypeModel(
            name='依据法规',
            desc='合规依据的法律法规等',
            select_type='MULTI',
            required='TRUE',
            opt_show='TRUE',
            statistic_show='TRUE'
        ).save()
        ttp1 = TagTypePropertyModel(
            name='强制性法规',
            desc='强制',
            tag_type=tag_type
        ).save()
        ttp2 = TagTypePropertyModel(
            name='法规草案',
            desc='样例',
            tag_type=tag_type
        ).save()
        tag1 = TagModel(
            name='违规收集个人信息',
            desc='根据《**》法案...',
            status='ONLINE',
            tag_type=tag_type,
            tag_type_property=ttp1
        ).save()
        RequireModel(
            content='样例: 根据**法规.....',
            source='法规第123条: 明确规定...',
            tags=[tag1]
        ).save()

    def init_app_compliance(self):
        AppComplianceModel.objects.delete()
        AppComplianceModel(
            name='app名称',
            app_status='已投放',
            dept='所属部门',
            startup_subject='开办主体',
            principal='负责人',
            remarks='后续观察',
            version='1.0.1'
        ).save()

    def init_feature_data(self):
        FeatureModel.objects.delete()
        FeatureModel(
            title='待办项1',
            desc="为满足**目标, 需对**进行整改",
            demander="内审部",
            priority="HIGH",
            status="UN_STARTED",
            expect_deadline=self.now,
            implementer="研发",
            submitter=['admin']
        ).save()

    def init_ticket_data(self):
        online_ticket = {
            "ticket_id": "ticket_id1",
            "ticket_type": "功能开发",
            "commit_id": "1220622111111111111111111111111111",
            "submit_time": time_util.yesterday(),
            "project": "project1",
            "change_detail": "功能开发",
            "influence": "新增功能",
            "developer": [
                {
                    "name": "40001",
                    "email": "40001a"
                }
            ],
            "submitter": [
                {
                    "name": "40001",
                    "email": "40001a"
                }
            ],
            "tester": [],
            "reviewer": [
                {
                    "name": "40002",
                    "email": "40002a"
                }
            ],
            "cur_step": "准备上线",
            "status": "ready",
            "dept_id": "dept_id_1"
        }
        deploy_ticket = {
            "source_id": "source_dt_1",
            "deploy_time": self.yesterday,
            "deployer": "40005a",
            "project": "project1",
            "dept": "dept_id_1",
            "commit_id": "1220622",
            "desc": "功能部署",
            "reason": "功能部署",
            "risk": True,
            "ticket_id": "ticket_id1",
            "risk_reason": "流程不规范",
            "appkey": "appkey0"
        }
        ticket_approve_data = {
            "wos_url": "https://www.example.com/ticket_approve_link/12345",
            'start_time': time_util.time_delta(self.yesterday, days=1),
            "end_time": time_util.time_delta(self.yesterday, forward='later', days=1),
            "environment": "2",
            "project": ["project1"],
            "reason": "测试",
            "release": "123123",
            "submitter": {
                "name": "40007",
                "id": '40007'
            },
            'reviewer': [{
                'name': '40008',
                'id': '40008'
            }],
            "time_long": '5',
        }
        sys_project_data = {
            "sys_id": "ca",
            "project": "project1",
            "appkey": "appkey0",
            "created_date": self.now,
            "update_date": self.now
        }
        OnlineTicketModel.objects.delete()
        DeployTicketModel.objects.delete()
        SysProjectModel.objects.delete()
        TicketApproveModel.objects.delete()
        OnlineTicketModel(**online_ticket).save()
        DeployTicketModel(**deploy_ticket).save()
        SysProjectModel(**sys_project_data).save()
        TicketApproveModel(**ticket_approve_data).save()

    def init_standing_book_data(self):
        """ 管理台账数据 """
        AppStandingBookModel.objects.delete()
        AppTodoModel.objects.delete()
        ProjectStandingBookModel.objects.delete()
        ProjectTodoModel.objects.delete()
        app_standing_book_data = {
            'app': '产品',
            'app_version': '1.0.0',
            'occur_time': datetime.datetime.now(),
            'kind': '类型1',
            'remark': '备注'
        }
        app_obj = AppStandingBookModel(**app_standing_book_data).save()
        app_todo_data = {
            'app': app_obj,
            'question': '问题描述',
            'handle_status': '处理状态: 待办',
            'handle_person': '处理人',
            'schedule': '整改排期计划'
        }
        AppTodoModel(**app_todo_data).save()

        project_standing_book_data = {
            'project': '项目1',
            'handle_person': '处理人2',
            'remark': '备注'
        }
        pro_obj = ProjectStandingBookModel(**project_standing_book_data).save()
        project_todo_data = {
            'project': pro_obj,
            'detail': '具体事项',
            'time_point': '时间线排期'
        }
        ProjectTodoModel(**project_todo_data).save()

    def init_policy_trace_data(self):
        """ 政策解读数据 """
        PolicyTraceModel.objects.delete()
        data = {
            'title': '政策法规',
            'title_url': '',
            'pub_time': self.now,
            'organ': '发文机构',
            'kind': '类型',
            'interpretation': '政策解读1231',
            'inter_url': ''
        }
        PolicyTraceModel(**data).save()

    def init_supervision_data(self):
        """ 监管动态数据 """
        SupervisionModel.objects.delete()
        data = {
            'title': 'this is title',
            'pub_time': self.now,
            'organ': '机构1',
            'kind': '类型',
            'concern': '关注重点123',
            'source_link': ''
        }
        SupervisionModel(**data).save()

    def handle(self, *args, **options):
        self.now = datetime.datetime.now()
        self.yesterday = time_util.yesterday()
        self.init_admin_user()
        self.init_audit_sys()
        self.init_regex_rule()
        self.init_rule_atom()
        self.init_rule_group()
        self.init_task_config()
        self.init_perm_key()
        self.init_job_transfor_data()
        self.init_mock_task_data()
        self.init_mock_employee_info()
        self.init_app_compliance()
        self.init_knowledge_data()
        self.init_feature_data()
        self.init_ticket_data()
        self.init_standing_book_data()
        self.init_policy_trace_data()
        self.init_supervision_data()

