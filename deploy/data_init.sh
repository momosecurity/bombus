#!/usr/bin/env bash

#
# Copyright (C) 2020  momosecurity
#
# This file is part of Bombus.
#
# Bombus is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Bombus is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Bombus.  If not, see <https://www.gnu.org/licenses/>.
#

PROJECT_NAME=$(basename `pwd`)
project_path=$(dirname $(cd `dirname $0`; pwd))
echo $project_path
# 项目目录
base_path=$project_path
# 虚拟环境名称
VIRTUAL_ENV_NAME=$PROJECT_NAME
# 虚拟环境列表目录
ENV_DIR="${base_path}/venv"
# 当前虚拟环境目录
CUR_ENV_DIR="${ENV_DIR}/${VIRTUAL_ENV_NAME}"
# python路径
python_path="${CUR_ENV_DIR}/bin/python"

${python_path} ${base_path}/www/manage.py init_data
${python_path} ${base_path}/www/manage.py crontab_task_gen
${python_path} ${base_path}/www/manage.py crontab_permission_verify
