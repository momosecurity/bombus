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

import logging
import smtplib
from email.mime.text import MIMEText
from functools import wraps

from bombus.services.user_service import UserService

logger = logging.getLogger(__name__)


def no_exception(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as err:
            logger.exception(f'EmailMessage Error! {err!r}')
    return wrapper


class EmailMessage:
    SENDER = 'example-user@example.com'
    PASSWORD = 'example-password'
    MAIL_HOST = 'smtp.example.com'
    SUB = '自动化推送提醒'

    @classmethod
    def batch_send_to_persons(cls, text, to_list):
        emails = UserService.batch_id_to_email(to_list, clear_email=False)
        cls.send_mail(emails, cls.SUB, text)

    @classmethod
    def send_mail(cls, to_list, sub, content):
        """发送邮件提示"""
        msg = MIMEText(content, _subtype='plain')
        msg['Subject'] = sub
        msg['From'] = cls.SENDER
        msg['To'] = ";".join(to_list)
        try:
            s = smtplib.SMTP()
            s.connect(cls.MAIL_HOST)
            s.login(cls.SENDER, cls.PASSWORD)
            s.sendmail(cls.SENDER, to_list, msg.as_string())
            s.close()
            return True
        except Exception as e:
            logger.exception('send email error ')
            return False
