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

import logging
import re
from collections import defaultdict

from audit.models import (DeployTicketModel, OnlineTicketModel,
                          TicketApproveModel)

logger = logging.getLogger(__name__)


class OnlineTicketHandler:
    """
    上线单处理
    """

    URL_FMT = 'http://www.your_ticket_url.com/link/{ticket_id}'

    @classmethod
    def gen_ticket_url(cls, ticket_id):
        return cls.URL_FMT.format(ticket_id=ticket_id)

    @classmethod
    def split_commitid(cls, commit_id):
        if not commit_id:
            return []
        return list(filter(None, re.split('[,;，；\s]', commit_id)))

    @classmethod
    def hit_commitid(cls, commit_id, ot_commitid):
        """
        判断commit是否能匹配该上线单
        """
        ot_commitids = cls.split_commitid(ot_commitid)
        for ot_cid in ot_commitids:
            if ot_cid.startswith(commit_id):
                return True
        return False


class DeployTicketHandler:

    COMMIT_ID_LENGTH = 7

    def __init__(self, deploy_ticket_id):
        self.id = deploy_ticket_id

    @classmethod
    def get_online_ticket(cls, commit_id):
        ots = OnlineTicketModel.objects.filter(commit_id__contains=commit_id)
        hit_online_ticket = None
        for ot in ots:
            if OnlineTicketHandler.hit_commitid(commit_id, ot.commit_id):
                hit_online_ticket = ot
                break
        return hit_online_ticket

    @property
    def data(self):
        try:
            instance = DeployTicketModel.objects.get(id=self.id)
            data = instance._data
            return data
        except:
            return {}

    @classmethod
    def approve_ticket_close(cls, commit_id):
        """ 判断对应的部署单 是否关闭工单审批 """
        queryset = DeployTicketModel.objects.filter(commit_id=commit_id)
        time_lines = []
        projects = set()
        for qs in queryset:
            time_lines.append(qs.deploy_time)
            projects.add(qs.project)
        time_lines.sort()

        record = TicketApproveModel.objects.filter(project__in=projects,
                                                   start_time__lte=time_lines[0],
                                                   end_time__gte=time_lines[0]).order_by('start_time').first()
        if record:
            return record.wos_url
        return None

    @classmethod
    def verify_dept_tickets(cls, dept, start_time, end_time):
        queryset = DeployTicketModel.objects.filter(
            dept=dept,
            deploy_time__gte=start_time,
            deploy_time__lt=end_time
        )
        cmid_info = defaultdict(dict)
        for qs in queryset:
            cm_id = qs.commit_id[:cls.COMMIT_ID_LENGTH]
            info = cmid_info[cm_id]
            info['ori_commit_id'] = qs.commit_id
        for commit_id, _info in cmid_info.items():
            ori_commit_id = _info['ori_commit_id']
            verify_result = cls.get_verify_result_by_commitid(commit_id)
            if verify_result['risk'] is True and verify_result['risk_reason'] == '未授权变更':
                wos_url = cls.approve_ticket_close(ori_commit_id)
                if wos_url:
                    verify_result['wos_url'] = wos_url
                    verify_result['risk_reason'] = '发布系统工单关闭已审批授权'
            cls.batch_update(ori_commit_id, verify_result)

    @classmethod
    def batch_update(cls, commit_id, result):
        DeployTicketModel.objects.filter(commit_id=commit_id).update(**result, multi=True)

    @classmethod
    def get_verify_result_by_commitid(cls, commit_id):
        online_ticket = cls.get_online_ticket(commit_id)
        risk_info = cls.get_risk_from_ticket(online_ticket)
        return risk_info

    @classmethod
    def get_risk_from_ticket(cls, ticket_obj):
        result = {
            'risk': False,
            'risk_reason': '',
            'ticket_id': ''
        }

        if not ticket_obj:
            result['risk'] = True
            result['risk_reason'] = '未授权变更'
        else:
            result['ticket_id'] = ticket_obj.ticket_id
            if ticket_obj.status not in ['ready', 'done']:
                result['risk'] = True
                result['risk_reason'] = '工单审批异常'
            elif ticket_obj.status == 'ready':
                result['risk'] = True
                result['risk_reason'] = '操作不规范'
        return result
