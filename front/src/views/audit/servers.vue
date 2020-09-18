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
                    <Input type="text" v-model="formFilter.server_name" :placeholder="descMap.server_name"></Input>
                </FormItem>
                <FormItem prop="kind" v-if="!fromTask">
                    <Select v-model="formFilter.server_kind" :placeholder="descMap.server_kind" filterable>
                        <Option v-for="item in serverKind" :value="item.name" :key="item.name">{{ item.desc }}</Option>
                    </Select>
                </FormItem>
                <FormItem prop="type" v-if="!fromTask">
                    <Input type="text" v-model="formFilter.server_type" :placeholder="descMap.server_type"></Input>
                </FormItem>
                <FormItem prop="audit_sys" v-if="!fromTask">
                    <Select v-model="formFilter.audit_sys" :placeholder="descMap.audit_sys" filterable>
                        <Option v-for="item in sysList" :value="item.id" :key="item.id">{{ item.sys_name }}</Option>
                    </Select>
                </FormItem>

                <FormItem>
                    <Button type="primary" icon="md-search" @click="filterRecord('formFilter')">查询</Button>
                    <Button type="primary" icon="md-refresh" @click="resetQuery('formFilter')">重置</Button>
                </FormItem>

            </Form>
        </div>

        <!--数据记录表格-->
        <Table border :columns="tableColumns" :data="tableData" size="small">
            <template slot-scope="{ row }" slot="domains">
                <pre><p v-for="uri in row.domains" :key="uri">{{ uri }}</p></pre>
            </template>

            <template slot-scope="{ row }" slot="action">
                <Button type="error" size="small"
                    :to="{name: 'databases-mysql-table', params: {cluster_id: row.cluster_id}}">删除
                </Button>
            </template>

            <div slot="footer" class="f-local-footer">总计 {{ recordTotal }} 条, 本页 {{ tableData.length }} 条
            </div>
        </Table>

        <!--分页-->
        <div class="f-local-page">
            <Page :current="currentPage" :total="recordTotal" :page-size="pageSize" @on-change="changePage" show-elevator />
        </div>

        <!--数据记录更新表单-->
        <Modal v-model="formModal" title="变更" footer-hide>
            <Form ref="formData" :model="formData" :rules="formRule" :label-width="120">
                <FormItem label="ID" prop="id" v-show="false">
                    <Input type="text" v-model="formData.id" readonly disabled></Input>
                </FormItem>

                <FormItem v-for="(value, name) in showColumns" :key="name" :prop="name" :label="value">
                    <Input type="text" v-model="formData[name]" :placeholder="showColumns[name]"></Input>
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
        name: 'AuditServer',
        data() {
            return {
                descMap: {},
                showColumns: [],
                userSearchResult: [],
                sysList: [],
                serverKind: [],
                userLoading: false,
                fromTask: false,

                // 数据总记录数据
                recordTotal: 0,
                // 当前页号
                currentPage: 1,
                pageSize: 10,

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
                    const record = this.tableData[index]
                    this.formData = {...record}
                } else {
                    this.formData = {}
                }
                this.formModal = true
            },

            // 删除数据记录
            removeRecord(index) {
                const url = `/api/audit/audit_server/${this.tableData[index].id}/`
                requestAPI(url, {}, 'delete').then(resp => {
                    this.loadTableData()
                    this.$Message.success(`删除 ${this.tableData[index].desc} 成功`)
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
            getSysList() {
                const url = `/api/audit/sys/`
                requestAPI(url, {}, 'get').then(resp => {
                    this.sysList = resp.data.results;
                })
            },
            // 重置
            resetQuery() {
                this.formFilter = {}
                this.loadTableData()
            },
            // getServerKind() {
            //     const url = `/api/audit/server_kind/`
            //     requestAPI(url, {}, 'get').then(resp => {
            //         this.serverKind = resp.data.results;
            //     })
            // },
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
                if (this.$route.params.from){
                    this.fromTask = true
                }
                if (this.$route.params.audit_sys){
                    this.formFilter.audit_sys = this.$route.params.audit_sys
                }
                if (this.$route.params.server_kind){
                    this.formFilter.server_kind = this.$route.params.server_kind
                }
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
                requestAPI('/api/audit/server/', params).then(resp => {
                    this.tableData = resp.data.results
                    this.recordTotal = resp.data.count
                    this.descMap = resp.data.desc_map
                    this.showColumns = resp.data.show_columns
                    this.serverKind = resp.data.server_kind
                    this.sysList = resp.data.sys_list
                    // this.formFilter = {}
                    this.tableColumns = []
                    this.userLoading = false
                    this.userSearchResult = []
                    // this.sysList = []
                    this.tableColumns.push({
                        title: '#',
                        type: 'index',
                        width: 70,
                        indexMethod: (row) => {
                            return (row._index + 1) + (this.pageSize * this.currentPage) - this.pageSize;
                        }
                    })
                    const primaryKey = resp.data.clickable_key
                    const primaryKeyDesc = this.showColumns[primaryKey]
                    // this.tableColumns.push(this.renderTablePrimaryKey(primaryKey, primaryKeyDesc))
                    for (const key in this.showColumns) {
                        if (key === primaryKey) { continue }
                        let column = {
                            'title': this.showColumns[key],
                            'key': key
                        }
                        this.tableColumns.push(column)
                    }
                    // for (const key in this.descMap) {
                    //     this.formFilter[key] = ''
                    // }
                    // this.tableColumns.push({
                    //     title: '操作',
                    //     slot: 'action',
                    //     width: 100
                    // })

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
            // this.getServerKind();
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
