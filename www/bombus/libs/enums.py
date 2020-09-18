# -*- coding:utf-8 -*-

"""
定义业务枚举变量
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

from core import CEnum


class ServerKindEnum(CEnum):
    """
    资产类别
    """
    SA = '操作系统'
    DBA = '数据库'
    APP = '应用系统'
    TICKET = '工单'
    # 审阅人合并
    SYS_DB = '操作系统/数据库'


class OnOfflineStatusEnum(CEnum):
    """
    启用状态开关
    """
    ONLINE = '启用'
    OFFLINE = '停用'


class RuleTypeEnum(CEnum):
    """
    策略原子类型
    """
    PERM = '权限矩阵'
    REGEX = '正则匹配'
    NO_USE = '长期未使用'
    JOB_TRANS = '转岗异动'


class AuditPeriodEnum(CEnum):
    """
    审阅周期
    """
    QUARTER = '每季度'
    HALFYEAR = '半年'
    MONTH = '每月'


class TaskStatusEnum(CEnum):
    NOT_STARTED = '待启动'
    STARTED = '已启动'
    UNDER_REVIEW = '审阅中'
    NOT_AUDITED = '待审核'
    FINISHED = '已完成'
    PAUSE = '暂停'


class PushEventEnum(CEnum):
    STARTED = '启动事件'
    REVIEWED = '已审阅事件'
    TIC_STARTED = '工单启动事件'


class PriorityEnum(CEnum):
    """
    优先级状态
    """
    HIGH = '高'
    MIDDLE = '中'
    LOW = '低'


class ProcessStatusEnum(CEnum):
    """
    进行状态
    """
    UN_STARTED = '待完成'
    IN_PROCESS = '进行中'
    FINISHED = '已完成'


class SelectTypeEnum(CEnum):
    """
    选择类型
    """
    SINGLE = '单选'
    MULTI = '多选'


class BooleanEnum(CEnum):
    """
    是否状态枚举
    """
    TRUE = '是'
    FALSE = '否'


class ReviewTypeEnum(CEnum):
    """
    审阅意见类型
    """
    APP = '应用'
    SYS_DB = '数据库/操作系统'
    TICKET = '工单'
    APP_LOG = '应用日志'
    SYS_DB_LOG = '数据库/操作系统日志'
    ONLINE_TICKET = '上线单'
    DEPLOY_TICKET = '部署单'


class MessageBoardEnum(CEnum):
    """
    审阅意见类型
    """
    APP = '应用'
    SYS_DB = '数据库/操作系统'
    TICKET = '工单'
