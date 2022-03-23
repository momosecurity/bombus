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
                <FormItem prop="status">
                    <Input type="text" v-model="formFilter.handle_status" :placeholder="descMap.handle_status"></Input>
                </FormItem>

                <FormItem>
                    <Button type="primary" icon="md-search" @click="filterRecord('formFilter')">查询</Button>
                    <Button type="primary" icon="md-refresh" @click="resetQuery('formFilter')">重置</Button>
                    <Button type="success" icon="md-add-circle" @click="showForm()">新增</Button>
                </FormItem>

            </Form>
        </div>

        <!--数据记录表格-->
        <div style="width: auto; overflow: scroll">
        <Table border :columns="tableColumns" :data="tableData" size="small" @on-cell-click="showDetail">

            <template slot-scope="{ row, index }" slot="action">
                <Button :disabled="editable(index)" type="primary" size="small" @click="showForm(index)">更新</Button>
            </template>

            <div slot="footer" class="f-local-footer">总计 {{ recordTotal }} 条, 本页 {{ tableData.length }} 条
            </div>
        </Table>
        </div>

        <!--分页-->
        <div class="f-local-page">
            <Page :current="currentPage" :total="recordTotal" :page-size="10" @on-change="changePage" show-elevator />
        </div>
        <Modal v-model="formDetailModal" title="发现问题">
            <div><pre>{{curQuestionDetail}}</pre></div>
        </Modal>
        <!--数据记录更新表单-->
        <Modal v-model="formModal" title="新增/更新" footer-hide>
            <Form ref="formData" :model="formData" :rules="formRule" :label-width="120">
                <FormItem label="ID" prop="id" v-show="false">
                    <Input type="text" v-model="formData.id" readonly disabled></Input>
                </FormItem>
                <FormItem :label="descMap.question" prop="question">
                    <Input type="textarea" :rows="5" v-model="formData.question"></Input>
                </FormItem>
                <FormItem :label="descMap.handle_status" prop="handle_status">
                    <Input type="text" v-model="formData.handle_status"></Input>
                </FormItem>
                <FormItem :label="descMap.handle_person" prop="handle_person">
                    <Input type="text" v-model="formData.handle_person"></Input>
                </FormItem>
               <FormItem :label="descMap.schedule" prop="schedule">
                    <Input type="text" v-model="formData.schedule"></Input>
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
    import tinymce from 'tinymce'
    import 'tinymce/themes/silver'
    import 'tinymce/icons/default'
    import 'tinymce/plugins/image'
    import 'tinymce/plugins/media'
    import 'tinymce/plugins/table'
    import 'tinymce/plugins/lists'
    import 'tinymce/plugins/wordcount'
    import 'tinymce/plugins/colorpicker'
    import 'tinymce/plugins/textcolor'

    import Editor from '@tinymce/tinymce-vue'
    export default {
        components: {
            Editor
        },
        name: 'AppTodo',
        data() {
            return {
                app_id: '',
                mainUrl: '/api/app-todo/',
                descMap: {},
                showColumns: [],
                userSearchResult: [],
                serverKindList: [],
                userLoading: false,
                sysList: [],
                priorityList: [],
                statusList: [],
                curQuestionDetail: '',

                // tinymce
                // 数据总记录数据
                recordTotal: 0,
                // 当前页号
                currentPage: 1,

                // 表格数据
                tableColumns: [
                    { title: '#', type: 'index', width: 55},
                    { title: '发现问题', key: 'question'},
                    // { title: '发现问题', key: 'question', tooltip: true, className: 'click-detail' },
                    { title: '整改状态', key: 'handle_status'},
                    { title: '对接人', key: 'handle_person'},
                    { title: '整改排期', key: 'schedule'},
                    { title: '操作', slot: 'action', width: 130}
                ],
                tableData: [],

                // 数据过滤表单
                formFilter: {},
                formFilterRule: {},
                // 时间限制提示
                timeWarning: false,
                // 详情展示
                formDetailModal: false,
                // 链接展示
                fullLink: '',
                formLinkModal: false,
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
                    const url = `${this.mainUrl}${this.tableData[index].id}/`
                    requestAPI(url, {}, 'get').then(resp => {
                        this.formData = resp.data
                    })
                } else {
                    this.formData = {}
                }
                this.formModal = true
            },
            // 时间变更
            timeLimit(time, time_type) {
                var curTime = this.getNowFormatDate()
                if(time <= curTime) {
                    this.timeWarning = true
                }else{
                    this.timeWarning = false
                }
            },
            getNowFormatDate() {
                var date = new Date();
                var seperator1 = "-";
                var seperator2 = ":";
                var month = date.getMonth() + 1;
                var strDate = date.getDate();
                if (month >= 1 && month <= 9) {
                    month = "0" + month;
                }
                if (strDate >= 0 && strDate <= 9) {
                    strDate = "0" + strDate;
                }
                var currentdate = date.getFullYear() + seperator1 + month + seperator1 + strDate
                        + " " + date.getHours() + seperator2 + date.getMinutes()
                        + seperator2 + date.getSeconds();
                return currentdate;
            },
            // 开始时间限制
            beginTime(){
                return {
                    disabledDate(date) {
                        let curTime = new Date()
                        return date && date > curTime
                    }
                }
            },
            // 完成
            finish(index) {
                this.$Modal.confirm({
                    title: '提示',
                    content: '完成之后将不可继续编辑, 是否继续?',
                    onOk: () => {
                        this.$refs['formData'].resetFields()
                        const url = `${this.mainUrl}${this.tableData[index].id}/`
                        requestAPI(url, {}, 'get').then(resp => {
                            this.formData = resp.data
                            this.formData['status'] = 'FINISHED'
                            const url = `${this.mainUrl}${this.formData.id}/`
                            requestAPI(url, {}, 'patch', this.formData).then(resp => {
                                this.$Message.success('更新成功')
                                this.loadTableData()
                            })
                        })
                    }
                });
            },
            editable(index) {
                const record = this.tableData[index]
                let status = record['status']
                if (status === 'FINISHED'){
                    return true
                }else{
                    return false
                }
            },

            showDetail(row, column, data, event){
                if(column.key === 'question'){
                    this.formDetailModal = true
                    this.curQuestionDetail = data
                }
            },
            copyText() {
                var vm = this
                this.$copyText(this.fullLink).then(function (e) {
                    vm.$Message.success('复制成功')
                }, function (e) {
                    vm.$Message.error('复制失败, 请手动操作')
                })
            },
            showLink(index){
                // this.$refs['formData'].resetFields()
                const record = this.tableData[index]
                let curData = {...record}
                let url = window.location.origin + window.location.pathname
                let pk = curData['id']
                let fullLink = url + '?pk=' + pk
                this.fullLink = fullLink
                this.formLinkModal = true
            },
            // 表单更新
            updateRecord(name) {
                this.$refs[name].validate((valid) => {
                    if (!valid) {
                        this.$Message.error('输入有误！请检查')
                    } else {
                        let form = this.formData
                        let postData = {...form}
                        postData['app'] = this.app_id
                        if (form.id) {
                            const url = `${this.mainUrl}${form.id}/`
                            requestAPI(url, {}, 'patch', postData).then(resp => {
                                this.$Message.success('更新成功')
                                this.loadTableData()
                            })
                        } else {
                            requestAPI(this.mainUrl, {}, 'post', postData).then(resp => {
                                this.$Message.success('添加成功')
                                this.loadTableData()
                            })
                        }
                        this.formModal = false
                    }
                })
            },
            //
            limitContent(content, length) {
                if (content != null && content.length != 0){
                    if (content.length > length) { content = content.slice(0,length) + '...'}
                }
                return content
            },
            // 删除数据记录
            removeRecord(index) {
                this.$Modal.confirm({
                    title: '提示',
                    content: '确认删除记录【' + this.limitContent(this.tableData[index].title, 10) + '】?',
                    onOk: () => {
                        const url = `${this.mainUrl}${this.tableData[index].id}/`
                        requestAPI(url, {}, 'delete').then(resp => {
                            this.loadTableData()
                            this.$Message.success(`删除 ${this.tableData[index].name} 成功`)
                        })
                    }
                });
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
            // 查看变更历史
            showLog(index) {
                // 开始新页面
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
                let app_id = this.$route.params.id
                this.app_id = this.$route.params.id
                // let queryParams = this.$route.query
                // console.log('queryParams:', queryParams)
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
                if(app_id){
                    params['app'] = app_id
                }
                requestAPI(this.mainUrl, params).then(resp => {
                    this.tableData = resp.data.results
                    this.recordTotal = resp.data.count
                    this.descMap = resp.data.desc_map
                    this.showColumns = resp.data.show_columns
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
        },
        mounted() {
            tinymce.init({});
        },
        watch: {
            'formModal' (val) {
                if(!val){
                    this.timeWarning = false
                }
            },
            deep:true
        },
    }
</script>

<style scoped>
    .auto-column-size-table table {
      table-layout: auto;
    }
    .auto-column-size-table table colgroup col {
      display: none;
    }
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
