"""
状态变更时, 相关处理
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

from django.conf import settings
from django.utils.functional import cached_property

from audit.models import (AuditTaskModel, NewReviewCommentModel,
                          ReviewCommentModel, TaskMessageBoardModel)
from audit.rule_handler import PeriodProxyHandler
from bombus.libs.enums import PushEventEnum, TaskStatusEnum
from bombus.libs.exception import FastResponse
from bombus.services.message import EmailMessage


class PushMaterial(object):
    """
    push物料定义
    """

    EVENT_CONTENT_FMT = {
        PushEventEnum.STARTED: '您好，合规审阅已开始，请登录 {report_url} 进行审阅',
        PushEventEnum.TIC_STARTED: '您好，合规审阅(上线工单)已开始，请登录 {report_url} 进行审阅',
        PushEventEnum.REVIEWED: '{title}已审阅，请登录 {report_url} 确认',
    }

    event_func_map = {
        PushEventEnum.STARTED: 'format_review_push_info',
        PushEventEnum.REVIEWED: 'format_audit_push_info'
    }

    def __init__(self, event_type, task_instance):
        self.event_type = event_type
        self.task_instance = task_instance

    def get_audit_users(self):
        """
        获取合规人员
        """
        return settings.AUDIT_USERS

    @cached_property
    def task_url(self):
        return self.task_instance.review_page_url

    def get_auditors(self):
        return self.task_instance.task_manager.sys.all_auditors

    def get_ticket_auditors(self):
        return self.task_instance.task_manager.sys.list_ticket_auditors

    def ticket_is_pushed(self):
        """
        判断工单通知是否已经推送过
        """
        audit_sys = self.task_instance.task_manager.sys
        dept_id = audit_sys.online_ticket_dept_id
        active_tasks = AuditTaskModel.objects.filter(
            id__ne=self.task_instance.id,
            period=self.task_instance.period,
            status__not__in=[TaskStatusEnum.NOT_STARTED.name, TaskStatusEnum.PAUSE.name]
        )
        for task in active_tasks:
            if task.task_manager.sys.online_ticket_dept_id == dept_id:
                return True
        return False

    def format_review_push_info(self):
        push_list = []
        url = self.task_url
        auditor_list = self.get_auditors()
        content = self.EVENT_CONTENT_FMT[PushEventEnum.STARTED].format(report_url=url)
        normal_push_info = {
            'push_users': auditor_list,
            'push_content': content
        }
        push_list.append(normal_push_info)
        ticket_auditors = self.get_ticket_auditors()
        if set(ticket_auditors) - set(auditor_list):
            if not self.ticket_is_pushed():
                ticket_push_info = {
                    'push_users': set(ticket_auditors) - set(auditor_list),
                    'push_content': self.EVENT_CONTENT_FMT[PushEventEnum.TIC_STARTED].format(report_url=url)
                }
                push_list.append(ticket_push_info)
        return push_list

    def format_audit_push_info(self):
        url = self.task_url
        title = self.task_instance.title
        users = self.get_audit_users()
        content = self.EVENT_CONTENT_FMT[PushEventEnum.REVIEWED].format(title=title, report_url=url)
        return [{
            'push_users': users,
            'push_content': content
        }]

    def push_info(self) -> list:
        """
        推送人及内容
        """
        result = []
        func_name = self.event_func_map.get(self.event_type) or ''
        if func_name:
            func = getattr(self, func_name)
            if func and callable(func):
                result = func()
        return result


class StatusPush(object):
    """
    状态推送
    """
    EVENT_TYPE_PATTERN = {
        (TaskStatusEnum.NOT_STARTED, TaskStatusEnum.STARTED): PushEventEnum.STARTED,
        (TaskStatusEnum.UNDER_REVIEW, TaskStatusEnum.NOT_AUDITED): PushEventEnum.REVIEWED
    }

    def __init__(self, task_instance, status_tuple):
        self.status_tuple = status_tuple
        self.task_instance = task_instance

    def push(self):
        """
        根据状态变更发送推送
        """
        if not self.event_type:
            return
        self._send_push(self.event_type)

    __call__ = push

    @cached_property
    def event_type(self):
        """
        根据状态变更 推送事件类型
        """
        old_status = self.status_tuple[0]
        new_status = self.status_tuple[1]
        if old_status == new_status:
            return

        event_type = self.EVENT_TYPE_PATTERN.get((old_status, new_status)) or None
        return event_type

    def _send_push(self, et):
        """
        根据material发送推送
        """
        push_material = PushMaterial(et, self.task_instance)
        push_info = push_material.push_info()
        if push_info:
            for push_params in push_info:
                push_content = push_params['push_content']
                push_users = push_params['push_users']
                if push_content and push_users:
                    EmailMessage.batch_send_to_persons(push_content, push_users)


class StatusChange:
    """
    状态变更
    """
    def __init__(self, task_instance, status_tuple: tuple):
        self.task_instance = task_instance
        self.status_tuple = status_tuple
        self.old_status, self.new_status = status_tuple

    def push(self):
        """
        推送
        """
        StatusPush(self.task_instance, self.status_tuple).push()

    def trigger(self):
        """
        触发操作
        """
        if self.new_status == TaskStatusEnum.PAUSE and self.old_status != TaskStatusEnum.PAUSE:
            self.pause()
        elif self.new_status == TaskStatusEnum.NOT_STARTED and self.old_status == TaskStatusEnum.PAUSE:
            self.recovery()
        elif self.new_status == TaskStatusEnum.STARTED and self.old_status == TaskStatusEnum.NOT_STARTED:
            self.start()
        elif self.new_status == TaskStatusEnum.FINISHED:
            self.finish()
        self.push()

    def get_task_period_time(self):
        return PeriodProxyHandler.time_range(self.task_instance.audit_period, self.task_instance.created_time)

    def validate(self):
        if self.new_status == TaskStatusEnum.NOT_STARTED and self.old_status == TaskStatusEnum.PAUSE:
            # 恢复
            return
        if (self.new_status.value < self.old_status.value) or \
                (self.old_status == TaskStatusEnum.NOT_STARTED and self.new_status == TaskStatusEnum.FINISHED) or \
                (self.old_status == TaskStatusEnum.FINISHED and self.new_status == TaskStatusEnum.PAUSE):
            raise FastResponse('状态变更非法: %s->%s' % (self.old_status.desc, self.new_status.desc))

        if not settings.DEBUG:
            if self.new_status == TaskStatusEnum.STARTED:
                _, period_end_time = self.get_task_period_time()
                if datetime.datetime.now() < period_end_time:
                    raise FastResponse('周期尚未结束, 任务不可以开始噢~')

    def pause(self):
        pass

    def start(self):
        self.task_instance.start_time = datetime.datetime.now()
        self.task_instance.save()

    def finish(self):
        self.task_instance.finished_time = datetime.datetime.now()
        self.task_instance.save()

    def recovery(self):
        ReviewCommentModel.objects.filter(task=self.task_instance).delete()
        TaskMessageBoardModel.objects.filter(task=self.task_instance).delete()

    @classmethod
    def check_review_status(cls, task_id):
        """
        检测审阅状态, 如果各部分都有审阅意见, 则
            UNDER_REVIEW->NOT_AUDITED
        否则:
            STARTED -> UNDER_REVIEW
        """
        if not task_id:
            return

        reviewed_status = NewReviewCommentModel.get_review_status(task_id)
        review_finished = True
        begin_reviewed = False
        for k, v in reviewed_status.items():
            if not v:
                review_finished = False
                break
            else:
                begin_reviewed = True

        status = TaskStatusEnum.STARTED.name
        if begin_reviewed:
            status = TaskStatusEnum.UNDER_REVIEW.name
        if review_finished:
            status = TaskStatusEnum.NOT_AUDITED.name
        try:
            instance = AuditTaskModel.objects.get(id=task_id)
            instance.status = status
            instance.save()
            if status == TaskStatusEnum.NOT_AUDITED.name:
                cls(instance, (TaskStatusEnum.UNDER_REVIEW, TaskStatusEnum.NOT_AUDITED)).push()
        except:
            pass
