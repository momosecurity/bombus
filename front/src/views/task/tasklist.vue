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
                <FormItem prop="sys">
                    <Select v-model="formFilter.task_manager" :placeholder="descMap.task_manager" filterable>
                        <Option v-for="item in taskManagerList" :value="item.id" :key="item.id">{{ item.name }}</Option>
                    </Select>
                </FormItem>
                <FormItem prop="status">
                     <Select v-model="formFilter.status" :placeholder="descMap.status" filterable>
                        <Option v-for="(item, idx) in taskStatusList" :value="item.name" :key="item.name">{{ item.desc }}</Option>
                     </Select>
                </FormItem>

                <FormItem>
                    <Button type="primary" icon="md-search" @click="filterRecord('formFilter')">查询</Button>
                    <Button type="primary" icon="md-refresh" @click="resetQuery">重置</Button>
                </FormItem>
            </Form>
        </div>

        <!--数据记录表格-->
        <Table border :columns="tableColumns" :data="tableData" size="small">

            <template slot-scope="{ row, index }" slot="route">
                <Button type="primary" size="small" @click="routeReviewPage(index)">查看</Button>
            </template>
            <template slot-scope="{ row, index }" slot="action">
                <Button type="primary" size="small" @click="showForm(index)">更新</Button>
            </template>

            <div slot="footer" class="f-local-footer">总计 {{ recordTotal }} 条, 本页 {{ tableData.length }} 条
            </div>
        </Table>

        <!--分页-->
        <div class="f-local-page">
            <Page :current="currentPage" :total="recordTotal" :page-size="pageSize" @on-change="changePage" show-elevator />
        </div>

        <!--数据记录更新表单-->
        <Modal v-model="formModal" title="详情" footer-hide width="700px">
            <Form ref="formData" :model="formData" :rules="formRule" :label-width="120">
                <FormItem label="ID" prop="id" v-show="false">
                    <Input type="text" v-model="formData.id" readonly disabled></Input>
                </FormItem>
                <FormItem label="任务所属" prop="task_manager">
                    <Select disabled v-model="formData.task_manager" filterable>
                        <Option v-for="(item, idx) in taskManagerList" :value="item.id" :key="item.id">{{ item.name }}</Option>
                    </Select>
                </FormItem>
                <FormItem label="周期" disabled prop="period">
                    <Input disabled type="text" v-model="formData.period"></Input>
                </FormItem>
                <FormItem label="状态" prop="status">
                    <Select v-model="formData.status" filterable>
                        <Option v-for="(item, idx) in taskStatusList" :value="item.name" :key="item.name">{{ item.desc }}</Option>
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
        name: 'TaskList',
        data() {
            return {
                descMap: {},
                showColumns: [],
                taskManagerList: [],
                taskStatusList: [],
                // 数据总记录数据
                recordTotal: 0,
                // 当前页号
                currentPage: 1,
                pageSize:10,

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
                // this.getTaskManagerList();
                this.$refs['formData'].resetFields()
                if (index !== undefined) {
                    const url = `/api/audit/task/${this.tableData[index].id}/`
                    requestAPI(url, {}, 'get').then(resp => {
                        this.formData = resp.data
                    })
                } else {
                    this.formData = {}
                }
                this.formModal = true
            },
            // 跳转至审阅页面
            routeReviewPage(index) {
                let route = this.$router.resolve({
                    name: 'newreview',
                    params: {
                        id: this.tableData[index].id,
                    }
                })
                window.open(route.href, '_blank')
            },
            routeUserReviewPage(index) {
                this.$router.push({
                    name: 'permreview',
                    params: {
                        id: this.tableData[index].id,
                    }
                })
            },
            routeLogReviewPage(index) {
                this.$router.push({
                    name: 'logreview',
                    params: {
                        id: this.tableData[index].id,
                    }
                })
            },
            // 重置查询条件
            resetQuery() {
                this.formFilter = {}
                this.loadTableData()
            },
            // 删除数据记录
            removeRecord(index) {
                const url = `/api/audit/task/${this.tableData[index].id}/`
                requestAPI(url, {}, 'delete').then(resp => {
                    this.loadTableData()
                    this.$Message.success(`删除 ${this.tableData[index].desc} 成功`)
                })
            },
            // 获取任务配置数据
            getTaskManagerList() {
                const url = `/api/audit/task_manager/`
                requestAPI(url, {}, 'get').then(resp => {
                    this.taskManagerList = resp.data.results;
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
                        ...this.formFilter,
                    }
                }
                requestAPI('/api/audit/task/', params).then(resp => {
                    this.tableData = resp.data.results
                    this.recordTotal = resp.data.count
                    this.descMap = resp.data.desc_map
                    this.showColumns = resp.data.show_columns
                    this.taskStatusList = resp.data.task_status_list
                    this.taskManagerList = resp.data.task_manager_list
                    this.formData = {}
                    // this.formFilter = {}
                    this.tableColumns = []
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
                        title: '审阅页面',
                        slot: 'route',
                        width: 150,
                        align: 'center'
                    })
                    this.tableColumns.push({
                        title: '操作',
                        slot: 'action',
                        width: 150,
                        align: 'center'
                    })
                })
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
                            const url = `/api/audit/task/${form.id}/`
                            requestAPI(url, {}, 'patch', postData).then(resp => {
                                this.$Message.success('更新成功')
                                this.loadTableData()
                            })
                        } else {
                            requestAPI('/api/audit/task/', {}, 'post', postData).then(resp => {
                                this.$Message.success('添加成功')
                                this.loadTableData()
                            })
                        }
                        this.formModal = false
                    }
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
