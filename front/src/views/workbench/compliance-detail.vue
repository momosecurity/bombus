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
                    <Input type="text" v-model="formFilter.status" :placeholder="descMap.status"></Input>
                </FormItem>

                <FormItem>
                    <Button type="primary" icon="md-search" @click="filterRecord('formFilter')">查询</Button>
                    <Button type="success" icon="md-add-circle" @click="showForm()">新增</Button>
                </FormItem>

            </Form>
        </div>

        <!--数据记录表格-->
        <div style="width: auto; overflow: scroll">
        <Table border :columns="tableColumns" :data="tableData" size="small">

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

        <Modal v-model="formLinkModal" title="详情" footer-hide>

            <p>{{fullLink}}</p>
            <Button type="default" size="small" @click="copyText">复制</Button>
        </Modal>
        <Modal v-model="formDetailModal" title="详情">
            <div><pre>{{formData.desc}}</pre></div>
        </Modal>
        <!--数据记录更新表单-->
        <Modal v-model="formModal" title="变更" footer-hide width="70">
            <Form ref="formData" :model="formData" :rules="formRule" :label-width="120">
                <FormItem label="ID" prop="id" v-show="false">
                    <Input type="text" v-model="formData.id" readonly disabled></Input>
                </FormItem>
                <FormItem :label="descMap.rectification_category" prop="rectification_category">
                    <Input type="text" v-model="formData.rectification_category"></Input>
                </FormItem>
                <FormItem :label="descMap.status_description" prop="status_description">
                    <Editor v-if="formModal" id="status_description" v-model="formData.status_description" :init="editorInit"></Editor>
                </FormItem>
                <FormItem :label="descMap.evaluation_basis" prop="evaluation_basis">
                    <Editor v-if="formModal"  id="evaluation_basis" v-model="formData.evaluation_basis" :init="editorInit"></Editor>
                </FormItem>
                <FormItem :label="descMap.rectification_program" prop="rectification_program">
                    <Editor v-if="formModal"  id="rectification_program" v-model="formData.rectification_program" :init="editorInit"></Editor>
                </FormItem>
                <FormItem :label="descMap.promotion_dept" prop="promotion_dept">
                    <Input v-model="formData.promotion_dept"/>
                </FormItem>
                <FormItem :label="descMap.status" prop="status">
                    <Input v-model="formData.status"/>
                </FormItem>
                <FormItem :label="descMap.rectification_time" prop="rectification_time">
                    <DatePicker type="datetime" :value="formData.rectification_time" v-model="formData.rectification_time" style="width: 200px"></DatePicker>
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
        name: 'Feature',
        props:{
            plugins: {
              type: [String, Array],
              default: 'lists image media table wordcount'
            },
            toolbar: {
              type: [String, Array],
              default: 'bold italic forecolor| fontsizeselect | fontselect | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent | lists image media table | removeformat'
            }
        },
        data() {
            return {
                app_id: '',
                mainUrl: '/api/compliance-detail/',
                descMap: {},
                showColumns: [],
                userSearchResult: [],
                serverKindList: [],
                userLoading: false,
                sysList: [],
                priorityList: [],
                statusList: [],

                // tinymce
                editorInit: {
                    language_url: '/static/tinymce/langs/zh_CN.js',
                    language: 'zh_CN',
                    skin_url: '/static/tinymce/skins/ui/oxide',
                    content_css: `/static/tinymce/skins/content/default/content.css`,
                    height: 300,
                    plugins: this.plugins,
                    toolbar: this.toolbar,
                    menubar: false,
                    images_upload_url: '/file/upload/',
                    images_upload_credentials: true,
                    relative_urls : false,
                    remove_script_host : false,
                    fontsize_formats: "8pt 10pt 12pt 14pt 18pt 24pt 36pt",
                },
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
            showDetail(index) {
                this.$refs['formData'].resetFields()
                if (index !== undefined) {
                    const record = this.tableData[index]
                    this.formData = {...record}
                } else {
                    this.formData = {}
                }
                this.formDetailModal = true
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
                        console.log(postData)
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
            renderTablePrimaryKey(key, title) {
                return {
                    title: title,
                    key: key,
                    render: (h, params) => {
                        return h('div', [
                            h('a', {
                                    on: {
                                        click: () => {
                                            this.showDetail(params.index)
                                        }
                                    }
                                },
                                params.row[key]
                            )
                        ]);
                    }
                }
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
                if(app_id){
                    params['app'] = app_id
                }
                requestAPI(this.mainUrl, params).then(resp => {
                    this.tableData = resp.data.results
                    this.recordTotal = resp.data.count
                    this.descMap = resp.data.desc_map
                    this.showColumns = resp.data.show_columns
                    this.formRule = resp.data.form_rule
                    this.tableColumns = []
                    this.tableColumns.push({
                        title: '#',
                        type: 'index',
                        width: 55
                    })
                    for (const key in this.showColumns) {
                        let column = {
                            'title': this.showColumns[key],
                            'key': key,
                            'type': 'html',
                            'width': 'auto',
                            'resizable': true,
                        }
                        this.tableColumns.push(column)
                    }
                    this.tableColumns.push({
                        title: '操作',
                        slot: 'action',
                        width: 120,
                        align: 'center'
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
