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

set -x
set -e

PROJECT_NAME=$(basename `pwd`)
# 获取当前目录
project_path=$(dirname $(cd `dirname $0`; pwd))
# 项目目录
PROJECT_DIR=$project_path
# 虚拟环境名称
VIRTUAL_ENV_NAME=$PROJECT_NAME
# 虚拟环境列表目录
ENV_DIR="${PROJECT_DIR}/venv"
# 当前虚拟环境目录
CUR_ENV_DIR="${ENV_DIR}/${VIRTUAL_ENV_NAME}"
# python路径
VIRTUAL_PYTHON_PATH="${CUR_ENV_DIR}/bin/python"
# python版本
PYTHON_VERSION="python3"


# 初始化Python虚拟环境
function install_pyenv() {
    printf "\n\n[+] install py_env\n"
    if [[ -f "${VIRTUAL_PYTHON_PATH}" ]]; then
        echo "${VIRTUAL_PYTHON_PATH} exist!"
    else
        echo "${VIRTUAL_PYTHON_PATH} not exist!"
        ${PYTHON_VERSION} -m venv ${CUR_ENV_DIR}
    fi
}


# 安装python依赖
function install_python_deps() {
    printf "\n\n[+] install python deps\n"
    ${CUR_ENV_DIR}/bin/pip install -r ${PROJECT_DIR}/requirements.txt
}


# django 命令
function run_django_command() {
    printf "\n\n[+] run django command\n"
    ${VIRTUAL_PYTHON_PATH} ${PROJECT_DIR}/www/manage.py migrate
}



function main() {
    install_pyenv
    install_python_deps
    run_django_command
}


# 入口函数
main
