# -*- coding:utf-8 -*-
"""
自定义异常
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

class FastResponse(Exception):
    """
    抛出异常, 通过中间件捕获, 返回response
    """
    status_code = 599

    def __init__(self, error_msg: str):
        self.error_msg = error_msg

    def __str__(self):
        return self.error_msg
