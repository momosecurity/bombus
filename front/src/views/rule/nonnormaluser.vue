<!--
  - Copyright (C) 2020  momosecurity
  -
  - This file is part of Bombus.
  -
  - Bombus is free software: you can redistribute it and/or modify
  - it under the terms of the GNU Lesser General Public License as published by
  - the Free Software Foundation, either version 3 of the License, or
  - (at your option) any later version.
  -
  - Bombus is distributed in the hope that it will be useful,
  - but WITHOUT ANY WARRANTY; without even the implied warranty of
  - MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  - GNU Lesser General Public License for more details.
  -
  - You should have received a copy of the GNU Lesser General Public License
  - along with Bombus.  If not, see <https://www.gnu.org/licenses/>.
  -->

<template>
    <div>
        <!--过滤器内联表单-->
        <div slot="header" class="f-local-header">
            <Form class="f-local-form" ref="formFilter" :model="formFilter" :rules="formFilterRule" inline>
                <FormItem prop="name">
                    <Input type="text" v-model="formFilter.name" :placeholder="descMap.name"></Input>
                </FormItem>
                <FormItem prop="audit_sys">
                    <Select v-model="formFilter.audit_sys" :placeholder="descMap.audit_sys" filterable>
                        <Option v-for="item in sysList" :value="item.id" :key="item.id">{{ item.sys_name }}</Option>
                    </Select>
                </FormItem>
                <FormItem prop="server_kind">
                    <Select v-model="formFilter.server_kind" :placeholder="descMap.server_kind" filterable>
                        <Option v-for="item in serverKindList" :value="item.name" :key="item.name">{{ item.desc }}</Option>
                    </Select>
                </FormItem>
                <FormItem prop="dept">
                    <Input type="text" v-model="formFilter.dept" :placeholder="descMap.dept"></Input>
                </FormItem>

                <FormItem prop="user">
                    <Select v-model="formFilter.user" :placeholder="descMap.user" filterable remote :remote-method="userSearch"
                            :loading="userLoading">
                        <Option v-for="(option, index) in userSearchResult" :value="option.accountid" :key="index">{{option.name}}</Option>
                    </Select>
                </FormItem>

                <FormItem>
                    <Button type="primary" icon="md-search" @click="filterRecord('formFilter')">查询</Button>
                    <Button type="primary" icon="md-refresh" @click="resetQuery('formFilter')">重置</Button>
                    <Button type="success" icon="md-add-circle" @click="showForm()">新增</Button>
                </FormItem>

            </Form>
        </div>

        <!--数据记录表格-->
        <Table border :columns="tableColumns" :data="tableData" size="small">
            <template slot-scope="{ row }" slot="domains">
                <pre><p v-for="uri in row.domains" :key="uri">{{ uri }}</p></pre>
            </template>

            <template slot-scope="{ row, index }" slot="action">
                <Button type="primary" size="small" @click="showForm(index)">更新</Button>
<!--                <Button type="primary" size="small" @click="showLog(index)">变更历史</Button>-->
                <Button type="error" size="small" @click="removeRecord(index)">删除</Button>
            </template>

            <div slot="footer" class="f-local-footer">总计 {{ recordTotal }} 条, 本页 {{ tableData.length }} 条
            </div>
        </Table>

        <!--分页-->
        <div class="f-local-page">
            <Page :current="currentPage" :total="recordTotal" :page-size="10" @on-change="changePage" show-elevator />
        </div>

        <!--数据记录更新表单-->
        <Modal v-model="formModal" title="变更" footer-hide>
            <Form ref="formData" :model="formData" :rules="formRule" :label-width="120">
                <FormItem label="ID" prop="id" v-show="false">
                    <Input type="text" v-model="formData.id" readonly disabled></Input>
                </FormItem>

                <FormItem label="用户标识" prop="name">
                    <Input type="text" v-model="formData.name"></Input>
                </FormItem>
                <FormItem label="来源系统" prop="server_kind">
                    <Select v-model="formData.server_kind" filterable>
                        <Option v-for="(item, idx) in serverKindList" :value="item.name" :key="item.name">{{ item.desc }}</Option>
                    </Select>
                </FormItem>
                <FormItem label="所属业务线" prop="audit_sys">
                    <Select v-model="formData.audit_sys" filterable>
                        <Option v-for="(item, idx) in sysList" :value="item.id" :key="item.id">{{ item.sys_name }}</Option>
                    </Select>
                </FormItem>
                <FormItem label="对应用户" prop="user">
                    <Select v-model="formData.user" filterable remote :remote-method="userSearch" :loading="userLoading">
                        <Option v-for="(option, index) in userSearchResult" :value="option.accountid" :key="index">{{option.name}}</Option>
                    </Select>
                </FormItem>

                <FormItem>
                    <Button type="primary" icon="md-arrow-up" @click="updateRecord('formData')">提交</Button>
                </FormItem>
            </Form>
        </Modal>

    </div>
</template>

<script>
    import {
        requestAPI
    } from '../../api'
    export default {
        name: 'NonNormalUser',
        data() {
            return {
                descMap: {},
                showColumns: [],
                userSearchResult: [],
                serverKindList: [],
                userLoading: false,
                sysList: [],

                // 数据总记录数据
                recordTotal: 0,
                // 当前页号
                currentPage: 1,

                // 表格数据
                tableColumns: [],
                tableData: [],

                // 数据过滤表单
                formFilter: {},
                formFilterRule: {},

                // 数据更新表单
                formModal: false,
                formData: {},
                formRule: {},
                formUrisRow: 5
            }
        },
        methods: {
            // 弹出数据变更表单
            showForm(index) {
                this.$refs['formData'].resetFields()
                if (index !== undefined) {
                    const url = `/api/audit/non_normal_user/${this.tableData[index].id}/`
                    requestAPI(url, {}, 'get').then(resp => {
                        this.formData = resp.data
                    })
                } else {
                    this.formData = {}
                }
                this.formModal = true
            },
            // 表单更新
            updateRecord(name) {
                this.$refs[name].validate((valid) => {
                    if (!valid) {
                        this.$Message.error('输入有误！请检查')
                    } else {
                        let form = this.formData
                        let postData = {...form}
                        if (form.id) {
                            const url = `/api/audit/non_normal_user/${form.id}/`
                            requestAPI(url, {}, 'patch', postData).then(resp => {
                                this.$Message.success('更新成功')
                                this.loadTableData()
                            })
                        } else {
                            requestAPI('/api/audit/non_normal_user/', {}, 'post', postData).then(resp => {
                                this.$Message.success('添加成功')
                                this.loadTableData()
                            })
                        }
                        this.formModal = false
                    }
                })
            },
            // 删除数据记录
            removeRecord(index) {
                const url = `/api/audit/non_normal_user/${this.tableData[index].id}/`
                requestAPI(url, {}, 'delete').then(resp => {
                    this.loadTableData()
                    this.$Message.success(`删除 ${this.tableData[index].name} 成功`)
                })
            },
            // 数据过滤
            filterRecord(name) {
                this.currentPage = 1
                this.$refs[name].validate((valid) => {
                    if (valid) {
                        this.loadTableData()
                        this.$Message.success('查询成功!')
                    } else {
                        this.$Message.error('过滤条件错误!');
                    }
                })
            },
            // 重置
            resetQuery() {
                this.formFilter = {}
                this.loadTableData()
            },
            // 查看变更历史
            showLog(index) {
                // 开始新页面
                // const url = `api/audit/operation_log/${this.tableData[index].id}`
                this.$router.push({
                    name: 'operationlog',
                    params: {
                        id: this.tableData[index].id,
                    }
                })
            },
            userSearch(query) {
                if (query !== '') {
                    this.userLoading = true;
                    let params = {};
                    const url = 'api/search_user/';
                    params = {
                        email: query
                    };
                    requestAPI(url, params, 'get').then(resp => {
                        this.userSearchResult = resp.data.results;
                    })
                    this.userLoading = false;
                }
            },
            // 加载表格数据
            loadTableData(page) {
                let params = {}
                if (page) {
                    params = {
                        ...this.formFilter,
                        ...{
                            page: this.currentPage
                        }
                    }
                } else {
                    params = {
                        ...this.formFilter
                    }
                }
                requestAPI('/api/audit/non_normal_user/', params).then(resp => {
                    this.tableData = resp.data.results
                    this.recordTotal = resp.data.count
                    this.descMap = resp.data.desc_map
                    this.showColumns = resp.data.show_columns
                    this.serverKindList = resp.data.server_kind_list
                    // this.formFilter = {}
                    this.formRule = resp.data.form_rule
                    this.sysList = resp.data.sys_list
                    this.tableColumns = []
                    this.userLoading = false
                    this.userSearchResult = []
                    this.tableColumns.push({
                        title: '#',
                        type: 'index',
                        width: 55
                    })
                    for (const key in this.showColumns) {
                        let column = {
                            'title': this.showColumns[key],
                            'key': key
                        }
                        this.tableColumns.push(column)
                    }
                    this.tableColumns.push({
                        title: '操作',
                        slot: 'action',
                        width: 150,
                        align: 'center'
                    })

                })
            },
            // 加载业务线
            getSysList() {
                const url = `/api/audit/sys/`
                requestAPI(url, {}, 'get').then(resp => {
                    this.sysList = resp.data.results;
                })
            },
            // 分页 - 更新页面
            changePage(pageNum) {
                this.currentPage = pageNum
                this.loadTableData(pageNum)
            }
        },
        created() {
            this.loadTableData();
            // this.getSysList();
        }
    }
</script>

<style scoped>
    .f-dashboard-item {
        padding-right: 30px;
    }

    .f-local-page {
        margin: 20px 0 0 0;
    }

    .f-local-footer {
        padding: 0 18px;
        font-weight: bold;
    }

    .f-local-form {
        padding: 10px 0;
    }

    .f-local-option-item {
        padding: 3px;
    }

    .f-tab {
        font-weight: bold;
    }
</style>
