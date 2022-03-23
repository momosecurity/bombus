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
                <FormItem prop="organ">
                    <Input type="text" v-model="formFilter.organ" :placeholder="descMap.organ"></Input>
                </FormItem>
                <FormItem prop="kind">
                    <Input type="text" v-model="formFilter.kind" :placeholder="descMap.kind"></Input>
                </FormItem>
                <FormItem prop="pub_time__gte">
                  <DatePicker type="date" placeholder="起始时间"
                              :value="formFilter.pub_time__gte"
                              @on-change="filterTimeChangeGt"
                              format="yyyy-MM-dd"></DatePicker>
                </FormItem>
                <FormItem prop="pub_time__lte">
                  <DatePicker type="datetime" placeholder="结束时间"
                              :value="formFilter.pub_time__lte"
                              @on-change="filterTimeChangeLt"
                              format="yyyy-MM-dd"></DatePicker>
                </FormItem>

                <FormItem>
                    <Button type="primary" icon="md-search" @click="filterRecord('formFilter')">查询</Button>
                    <Button type="primary" icon="md-refresh" @click="resetQuery('formFilter')">重置</Button>
                    <Button type="success" icon="md-add-circle"
                            @click="showForm()"
                    >新增</Button>
                </FormItem>

            </Form>
        </div>

        <!--数据记录表格-->
        <Table border :columns="tableColumns" :data="tableData" size="small"
               @on-cell-click="showDetail"
        >
            <template slot-scope="{ row }" slot="title">
                <a v-if="row.source_link && row.source_link.trim().length > 0" :href="row.source_link.trim()" target="_blank">{{row.title}}</a>
                <span v-else>{{row.title}}</span>
            </template>
            <template slot-scope="{ row }" slot="pub_time">
                <span>{{row.pub_time.substr(0, 10)}}</span>
            </template>
            <template slot-scope="{ row, index }" slot="action">
                <Button type="primary" size="small" @click="showForm(index)">更新</Button>
                <Button type="primary" size="small" @click="showLink(index)">链接</Button>
            </template>
            <div slot="footer" class="f-local-footer">总计 {{ recordTotal }} 条, 本页 {{ tableData.length }} 条</div>
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
                <FormItem label="标题" prop="title">
                    <Input type="text" v-model="formData.title"></Input>
                </FormItem>
                <FormItem label="类型" prop="kind">
                    <Input type="text" v-model="formData.kind"></Input>
                </FormItem>
                <FormItem label="发文机构" prop="organ">
                    <Input type="text" v-model="formData.organ"></Input>
                </FormItem>
                <FormItem :label="descMap.pub_time" prop="pub_time">
                  <DatePicker type="datetime" :value="formData.pub_time" v-model="formData.pub_time" style="width: 200px"></DatePicker>
                </FormItem>
                <FormItem label="关注重点" prop="concern">
                    <Input type='textarea' :rows="3" v-model="formData.concern"></Input>
                </FormItem>
                <FormItem label="原文链接" prop="source_link">
                    <Input type="text" v-model="formData.source_link"></Input>
                </FormItem>

                <FormItem>
                    <Button type="primary" icon="md-arrow-up" @click="updateRecord('formData')">提交</Button>
                </FormItem>
            </Form>
        </Modal>
        <Modal v-model="showDetailFormModal" title="关注重点" footer-hide>
            <pre>{{curDetailContent}}</pre>
        </Modal>
        <Modal v-model="formLinkModal" title="详情" footer-hide width="550">
            <p>{{fullLink}}</p>
            <Button type="default" size="small" @click="copyText">复制</Button>
        </Modal>

    </div>
</template>

<script>
    import {
        requestAPI
    } from '../../api'
    export default {
        name: 'Supervision',
        data() {
            return {
                url: '/api/knowledge/supervision/',
                perms: sessionStorage.getItem('perms').split(','),
                writePermKey: 'ca_unify:write',
                descMap: {},
                showColumns: [],
                // 数据总记录数据
                recordTotal: 0,
                // 当前页号
                currentPage: 1,

                // 表格数据
                tableColumns: [
                    { title: '#', type: 'index', width: 55},
                    { title: '标题', slot: 'title' },
                    { title: '时间', slot: 'pub_time', width: 130},
                    { title: '发文机构', key: 'organ'},
                    { title: '类型', key: 'kind'},
                    { title: '关注重点', key: 'concern'},
                    // { title: '关注重点', key: 'concern', tooltip: true, className: 'click-detail'},
                    { title: '操作', slot: 'action', width: 130}
                ],
                tableData: [],

                // 数据过滤表单
                formFilter: {},
                formFilterRule: {},

                // 分享链接
                formLinkModal: false,
                fullLink: '',
                // 数据更新表单
                formModal: false,
                formData: {},
                formRule: {},
                showDetailFormModal: false,
                curDetailContent: ''
            }
        },
        methods: {
            // 复制分享链接
            copyText() {
                var vm = this
                this.$copyText(this.fullLink).then(function (e) {
                    vm.$Message.success('复制成功')
                }, function (e) {
                    vm.$Message.error('复制失败, 请手动操作')
                })
            },
            filterTimeChangeGt(value) {
                this.formFilter['pub_time__gte'] = value
            },
            filterTimeChangeLt(value) {
                this.formFilter['pub_time__lte'] = value
            },
            // 链接
            showLink(index){
                const record = this.tableData[index]
                let curData = {...record}
                let url = window.location.origin + window.location.pathname
                let pk = curData['id']
                let fullLink = url + '?pk=' + pk
                this.fullLink = fullLink
                this.formLinkModal = true
            },
            // 展示详情
            showDetail(row, column, data, event){
                if(column.key !== 'concern'){
                    return
                }
                this.showDetailFormModal = true
                this.curDetailContent = data
            },
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
                let query_id = this.$route.query.pk
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
                        page: this.currentPage
                    }
                }
                if (query_id){
                    params['id'] = query_id
                }
                requestAPI(this.url, params).then(resp => {
                    this.tableData = resp.data.results
                    this.recordTotal = resp.data.count
                    this.descMap = resp.data.desc_map
                    this.showColumns = resp.data.show_columns
                    this.serverKindList = resp.data.server_kind_list
                    this.formRule = resp.data.form_rule

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
<style>
    .ivu-table td.click-detail{
        /*background-color: #2db7f5;*/
        color: #fff;
    }
    .ivu-table td.click-detail span{
        color: #2D8CF0;
        cursor: pointer;
    }
</style>

<style scoped>
    pre {
        display: block;
        overflow: auto;
        padding: 5px 10px;
        white-space:pre-wrap; /* css-3 */
        white-space:-moz-pre-wrap; /* Mozilla, since 1999 */
        white-space:-o-pre-wrap; /* Opera 7 */
        word-wrap:break-word; /* Internet Explorer 5.5+ */
        white-space: pre-wrap; /* Firefox */
    }

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
