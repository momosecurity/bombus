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
            <Form class="f-local-form" ref="formFilter" :model="formFilter" inline>
                <FormItem>
                    <Input type="text" v-model="formFilter.name" :placeholder="descMap.name"></Input>
                </FormItem>
                <FormItem>
                    <Input type="text" v-model="formFilter.desc" :placeholder="descMap.desc"></Input>
                </FormItem>
                <FormItem>
                    <Select v-model="formFilter.tag_type" filterable :placeholder="descMap.tag_type">
                        <Option v-for="(item, idx) in TagTypeList" :value="item.id" :key="item.id">{{ item.name }}</Option>
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
            <template slot-scope="{ row, index }" slot="action">
                <Button type="primary" size="small" @click="showForm(index)">更新</Button>
                <Button type="primary" size="small" @click="showLog(index)">变更历史</Button>
            </template>

            <div slot="footer" class="f-local-footer">总计 {{ recordTotal }} 条, 本页 {{ tableData.length }} 条
            </div>
        </Table>

        <!--分页-->
        <div class="f-local-page">
            <Page :current="currentPage" :total="recordTotal" :page-size="10" @on-change="changePage" show-elevator />
        </div>

        <!--查看及更新表单-->
        <Modal v-model="formModal" title="更新/查看" footer-hide :mask-closable="false">
            <Form ref="formData" :model="formData" :rules="formRule" :label-width="120" :disabled="histModal">
                <FormItem label="ID" prop="id" v-show="false">
                    <Input type="text" v-model="formData.id" readonly disabled></Input>
                </FormItem>

                <FormItem :label="descMap.name" prop="name">
                    <Input type="text" v-model="formData.name"></Input>
                </FormItem>
                <FormItem :label="descMap.desc" prop="desc">
                    <Input type="textarea" v-model="formData.desc"></Input>
                </FormItem>
                <FormItem :label="descMap.tag_type" prop="tag_type">
                    <Select v-model="formData.tag_type" filterable>
                        <Option v-for="(item, idx) in TagTypeList" :value="item.id" :key="item.id">{{ item.name }}</Option>
                    </Select>
                </FormItem>

                <FormItem v-show="!histModal">
                    <Button type="primary" icon="md-arrow-up" @click="updateRecord('formData')">提交</Button>
                </FormItem>

            </Form>
        </Modal>

        <!-- 历史记录表单 -->
        <Modal v-model="histModal" title="变更记录" footer-hide :mask-closable="false">
            <Table border :columns="histTableColumns" :data="histTableData" size="small">

                <template slot-scope="{ row, index }" slot="hist-action">
                    <Button type="primary" size="small" @click="showHistDetail(index)">查看</Button>
                    <Button type="primary" size="small" @click="recovery(index)">恢复</Button>
                </template>

            </Table>
        </Modal>
    </div>
</template>

<script>
    import {
        requestAPI
    } from '../../api'
    export default {
        name: 'TagTypeProperty',
        data() {
            return {
                url: '/api/knowledge/tag-type-property/',
                histUrl: '/api/record-history/',
                descMap: {},
                showColumns: [],
                // 规则启用状态定义
                TagTypeList: [],
                TagTypePropertyList: [],
                TypePropertyMap: {},
                PropertyShow: false,

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
                configurable: false,

                // 变更历史
                histModal: false,
                histTableColumns: [],
                histTableData: [],

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
                    const url = `${this.url}${this.tableData[index].id}/`
                    requestAPI(url, {}, 'get').then(resp => {
                        this.formData = resp.data
                    })
                } else {
                    this.formData = {}
                }
                this.formModal = true
            },
            // 恢复
            recovery(index){
                const url = `${this.histUrl}${this.histTableData[index].id}`
                requestAPI(url, {}, 'get').then(resp => {
                    let postData = JSON.parse(resp.data.content)
                    const url = `${this.url}${postData.id}/`
                    requestAPI(url, {}, 'patch', postData).then(resp => {
                        this.$Message.success('更新成功')
                        this.loadTableData()
                    })
                })
            },
            // 查看变更记录详情
            showHistDetail(index){
                this.$refs['formData'].resetFields()
                const url = `${this.histUrl}${this.histTableData[index].id}`
                requestAPI(url, {}, 'get').then(resp => {
                    this.formData = JSON.parse(resp.data.content)
                })
                this.formModal = true
            },
            // 查看变更历史
            showLog(index) {
                // 开始新页面
                this.loadHistData(index)
            },
            loadHistData(index){
                let params = {
                    'table_id': this.tableData[index].id,
                    'page_size': 30,
                }
                requestAPI(this.histUrl, params, 'get').then(resp => {
                    this.histTableData = resp.data.results
                    let histShowColumns = resp.data.show_columns
                    this.histTableColumns = []

                    this.histTableColumns.push({
                        title: '#',
                        type: 'index',
                        width: 55
                    })
                    for (const key in histShowColumns) {
                        let column = {
                            'title': histShowColumns[key],
                            'key': key
                        }
                        this.histTableColumns.push(column)
                    }
                    this.histTableColumns.push({
                        title: '操作',
                        slot: 'hist-action',
                        width: 130,
                        // align: 'center'
                    })
                    this.histModal = true
                })
            },
            // 删除数据记录
            removeRecord(index) {
                const url = `${this.url}${this.tableData[index].id}/`
                requestAPI(url, {}, 'delete').then(resp => {
                    this.loadTableData()
                    this.$Message.success(`删除 ${this.tableData[index].desc} 成功`)
                })
            },
            // 数据过滤
            filterRecord(name) {
                this.currentPage = 1
                this.loadTableData()
                this.$Message.success('查询成功!')
            },
            // 重置
            resetQuery() {
                this.formFilter = {}
                this.currentPage = 1
                this.loadTableData()
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
                            const url = `${this.url}${form.id}/`
                            requestAPI(url, {}, 'patch', postData).then(resp => {
                                this.$Message.success('更新成功')
                                this.loadTableData()
                            })
                        } else {
                            requestAPI(this.url, {}, 'post', postData).then(resp => {
                                this.$Message.success('添加成功')
                                this.loadTableData()
                            })
                        }
                        this.formModal = false
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
                            page: page
                        }
                    }
                } else {
                    params = {
                        ...this.formFilter,
                        ...{
                            page: this.currentPage,
                        }
                    }
                }
                requestAPI(this.url, params).then(resp => {
                    this.tableData = resp.data.results
                    this.recordTotal = resp.data.count
                    this.descMap = resp.data.desc_map
                    this.showColumns = resp.data.show_columns
                    this.formRule = resp.data.form_rule
                    this.tableColumns = []
                    this.TagTypeList = resp.data.tag_type_list
                    this.histModal = false
                    this.formModal = false
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
                        width: 160,
                        // align: 'center'
                    })
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
