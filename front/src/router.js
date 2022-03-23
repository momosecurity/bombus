/*
 * Copyright (C) 2020  momosecurity
 *
 * This file is part of Bombus.
 *
 * Bombus is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Lesser General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * Bombus is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public License
 * along with Bombus.  If not, see <https://www.gnu.org/licenses/>.
 */

import HomeIndex from './views/index.vue'
import HomeIndex2 from './views/index2.vue'

const routers = [
    {
        name: 'home',
        path: '/',
        meta: {
            title: '首页',
            icon: 'md-home'
        },
        component: HomeIndex,
    },
    {
        name: 'login',
        path: '/login',
        meta: {
            title: '登录页面',
            icon: 'md-home',
            hideInMenu: true,
        },
        component: (resolve) => require(['./views/login/login.vue'], resolve),
        children: []
    },
    {
        name: 'user',
        path: '/user',
        meta: {
            title: '用户管理',
            icon: 'md-home',
            perm: 'admin',
        },
        component: HomeIndex,
        children: [
            {
                path: 'permkey',
                name: 'permkey',
                meta: {
                    title: '权限列表',
                    icon: 'md-contact'
                },
                component: (resolve) => require(['./views/user/permkey.vue'], resolve)
            },
            {
                path: 'userlist',
                name: 'userlist',
                meta: {
                    title: '用户列表',
                    icon: 'md-contact'
                },
                component: (resolve) => require(['./views/user/userlist.vue'], resolve)
            }
        ]
    },
    {
        path: '/errorpage',
        meta: {
            title: '错误页面',
            icon: 'md-contact',
            hideInMenu: true,
        },
        component: HomeIndex,
        children: [
            {
                path: 'error403',
                name: 'error403',
                meta: {
                    title: '403页面',
                    icon: 'md-contact'
                },
                component: (resolve) => require(['./views/error-pages/403.vue'], resolve)
            },
        ]
    },
    {
        path: '/knowledge',
        meta: { title: "知识库", icon: 'md-book'},
        component: HomeIndex,
        children: [
            {
                path: 'tag-type',
                name: 'tag-type',
                meta: {
                    title: '知识坐标系设置',
                    icon: 'md-contact',
                    perm: 'ca_knowledge:read',
                    hideInMenu: true,
                },
                component: (resolve) => require(['./views/knowledge/tag-type.vue'], resolve),
            },
            {
                path: 'tag-type-property',
                name: 'tag-type-property',
                meta: {
                    title: '类型属性',
                    icon: 'md-contact',
                    hideInMenu: true,
                    perm: 'ca_knowledge:read'
                },
                component: (resolve) => require(['./views/knowledge/tag-type-property.vue'], resolve)
            },
            {
                path: 'tag',
                name: 'tag',
                meta: {
                    title: '知识刻度值管理',
                    icon: 'md-contact',
                    hideInMenu: true,
                    perm: 'ca_knowledge:read',
                },
                component: (resolve) => require(['./views/knowledge/tag.vue'], resolve)
            },
            {
                path: 'require',
                name: 'require',
                meta: {
                    title: '知识库管理',
                    icon: 'md-contact',
                    perm: 'ca_knowledge:read',
                },
                component: (resolve) => require(['./views/knowledge/require.vue'], resolve)
            },
            {
                path: 'overlook',
                name: 'overlook',
                meta: {
                    title: '知识地图',
                    icon: 'md-contact',
                },
                component: (resolve) => require(['./views/knowledge/overlook.vue'], resolve)
            },
            {
                path: 'supervision',
                name: 'supervision',
                meta: {
                    title: '监管动态',
                },
                component: (resolve) => require(['./views/knowledge/supervision.vue'], resolve)
            },
            {
                path: 'policy-trace',
                name: 'policy-trace',
                meta: {
                    title: '政策解读',
                },
                component: (resolve) => require(['./views/knowledge/policy-trace.vue'], resolve)
            },
        ]
    },
    {
        path: '/audit',
        meta: {
            title: '资产清单',
            icon: 'md-apps'
        },
        component: HomeIndex,
        children: [
            {
                path: 'server',
                name: 'server',
                meta: {
                    title: '清单列表',
                    icon: 'md-contact'
                },
                component: (resolve) => require(['./views/audit/servers.vue'], resolve)
            }
        ]
    },
    {
        path: '/rule',
        meta: {
            title: '策略配置',
            icon: 'md-cube'
        },
        component: HomeIndex,
        children: [
            {
                path: 'rulegroup',
                meta: {
                    title: '策略组',
                    icon: 'md-contact'
                },
                component: (resolve) => require(['./views/rule/rulegroup.vue'], resolve)
            },
            {
                path: 'ruleatom',
                meta: {
                    title: '策略原子',
                    icon: 'md-contact'
                },
                component: (resolve) => require(['./views/rule/ruleatom.vue'], resolve)
            },
             {
                path: 'regexrule',
                meta: {
                    title: '正则规则配置',
                    icon: 'md-contact'
                },
                component: (resolve) => require(['./views/rule/regexrule.vue'], resolve)
            },
            {
                path: 'userconfig',
                meta: {
                    title: '非标准用户管理',
                    icon: 'md-contact'
                },
                component: (resolve) => require(['./views/rule/nonnormaluser.vue'], resolve)
            },
            {
                path: 'auditorconfig',
                meta: {
                    title: '审阅人管理',
                    icon: 'md-contact'
                },
                component: (resolve) => require(['./views/rule/auditorconfig.vue'], resolve)
            },
            {
                path: 'operationlog/:id',
                name: 'operationlog',
                meta: {
                    title: '变更历史',
                    icon: 'md-contact',
                    hideInMenu: true
                },
                component: (resolve) => require(['./views/rule/operationlog.vue'], resolve)
            },
        ]
    },
    {
        path: '/task',
        meta: {
            title: '任务',
            icon: 'md-stats'
        },
        component: HomeIndex,
        children: [
            {
                path: 'taskmanager',
                meta: {
                    title: '任务配置',
                    icon: 'md-contact'
                },
                component: (resolve) => require(['./views/task/taskmanager.vue'], resolve)
            },
            {
                path: 'tasklist',
                name: 'tasklist',
                meta: {
                    title: '任务列表',
                    icon: 'md-contact',
                    // hideInMenu: true
                },
                component: (resolve) => require(['./views/task/tasklist.vue'], resolve)
            },
            {
                path: 'onlineticket',
                name: 'onlineticket',
                meta: {
                    title: '上线单',
                    icon: 'md-contact',
                    hideInMenu: true
                },
                component: (resolve) => require(['./views/task/onlineticket.vue'], resolve)
            },
            {
                path: 'deployticket',
                name: 'deployticket',
                meta: {
                    title: '部署单',
                    icon: 'md-contact',
                    hideInMenu: true
                },
                component: (resolve) => require(['./views/task/deployticket.vue'], resolve)
            },
            {
                path: 'sysdblog',
                name: 'sysdblog',
                meta: {
                    title: '操作系统数据库日志',
                    icon: 'md-contact',
                    hideInMenu: true
                },
                component: (resolve) => require(['./views/task/sysdblog.vue'], resolve)
            },
            {
                path: 'applog',
                name: 'applog',
                meta: {
                    title: '应用系统日志',
                    icon: 'md-contact',
                    hideInMenu: true
                },
                component: (resolve) => require(['./views/task/applog.vue'], resolve)
            },
            {
                path: 'bashcommand/:id',
                name: 'bashcommand',
                meta: {
                    title: '操作日志详情页',
                    icon: 'md-contact',
                    hideInMenu: true
                },
                component: (resolve) => require(['./views/task/bashcommand.vue'], resolve)
            },
            {
                path: 'bgaccesslog/:id',
                name: 'bgaccesslog',
                meta: {
                    title: '应用日志详情页',
                    icon: 'md-contact',
                    hideInMenu: true
                },
                component: (resolve) => require(['./views/task/bgaccesslog.vue'], resolve)
            },
            {
                path: 'mysqllog',
                name: 'mysqllog',
                meta: {
                    title: '数据库日志详情页',
                    icon: 'md-contact',
                    hideInMenu: true
                },
                component: (resolve) => require(['./views/task/mysqllog.vue'], resolve)
            },
        ]
    },
    {
        path: '/report',
        meta: {
            title: '任务',
            icon: 'md-stats',
            hideInMenu: true
        },
        component: HomeIndex2,
        children: [
            {
                path: 'newreview/:id',
                name: 'newreview',
                meta: {
                    title: '审阅报告',
                    icon: 'md-contact'
                },
                component: (resolve) => require(['./views/task/newreviewpage.vue'], resolve)
            },
        ]
    },
    {
        path: '/compliance',
        meta: {
            title: 'APP隐私合规',
            icon: 'md-briefcase'
        },
        component: HomeIndex,
        children: [
            {
                path: 'app-compliance',
                name: 'app-compliance',
                meta: {
                    title: '公司APP现状',
                    icon: 'md-contact'
                },
                component: (resolve) => require(['./views/workbench/app-compliance.vue'], resolve)
            },
            {
                path: 'compliance-detail/:id',
                name: 'compliance-detail',
                meta: {
                    title: '评估发现',
                    icon: 'md-contact',
                    hideInMenu: true
                },
                component: (resolve) => require(['./views/workbench/compliance-detail.vue'], resolve)
            },
            {
                path: 'standing-book',
                name: 'standing-book',
                meta: {
                    title: 'APP管理台账',
                    icon: 'md-contact'
                },
                component: (resolve) => require(['./views/workbench/app-standing-book.vue'], resolve)
            },
            {
                path: 'app-todo/:id',
                name: 'app-todo',
                meta: {
                    title: 'APP台账待办',
                    icon: 'md-contact',
                    hideInMenu: true
                },
                component: (resolve) => require(['./views/workbench/app-todo.vue'], resolve)
            },
            {
                path: 'project-standing-book',
                name: 'project-standing-book',
                meta: {
                    title: '专项管理台账',
                    icon: 'md-contact'
                },
                component: (resolve) => require(['./views/workbench/project-standing-book.vue'], resolve)
            },
            {
                path: 'project-todo/:id',
                name: 'project-todo',
                meta: {
                    title: '专项台账待办',
                    icon: 'md-contact',
                    hideInMenu: true
                },
                component: (resolve) => require(['./views/workbench/project-todo.vue'], resolve)
            },
        ]
    },
    {
        path: '/workbench',
        meta: {
            title: '工作台',
            icon: 'md-desktop'
        },
        component: HomeIndex,
        children: [
            {
                path: 'feature',
                meta: {
                    title: '待办跟踪',
                    icon: 'md-contact'
                },
                component: (resolve) => require(['./views/workbench/feature.vue'], resolve)
            },
            {
                path: 'settings',
                meta: {
                    title: '动态参数配置',
                    icon: 'md-contact'
                },
                component: (resolve) => require(['./views/workbench/settings.vue'], resolve)
            }
        ]
    },
    {
        path: '/logs',
        meta: {
            title: '操作日志',
            icon: 'md-paper'
        },
        component: HomeIndex,
        children: [
            {
                path: 'generallog',
                meta: {
                    title: '审计日志',
                    icon: 'md-contact'
                },
                component: (resolve) => require(['./views/logs/generallog.vue'], resolve)
            }
        ]
    }
];
export default routers;
