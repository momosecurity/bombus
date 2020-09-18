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
                <FormItem>
                    <Button type="primary" icon="ios-arrow-back" @click="routeBack()">返回审阅页</Button>
                </FormItem>
            </Form>
        </div>
        <!--数据记录表格-->
        <Table border :columns="tableColumns" :data="tableData" size="small">

            <template slot-scope="{ row, index }" slot="action">
                <Button type="primary" size="small" @click="showForm(index)">查看内容</Button>
            </template>

            <div slot="footer" class="f-local-footer">总计 {{ recordTotal }} 条, 本页 {{ tableData.length }} 条
            </div>
        </Table>

        <!--分页-->
        <div class="f-local-page">
            <Page :current="currentPage" :total="recordTotal" :page-size="10" @on-change="changePage" show-elevator />
        </div>

        <!--数据记录更新表单-->
        <Modal v-model="formModal" title="审阅" @on-ok="commitRecordReview">
            <Input type="textarea" v-model="reviewContent"></Input>
        </Modal>

    </div>
</template>

<script>
    import {
        requestAPI
    } from '../../api'
    import JsonViewer from 'vue-json-viewer'
    export default {
        name: 'appLog',
        data() {
            return {
                descMap: {},
                showColumns: [],
                reviewIndex: -1,
                reviewContent: '',
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
                formData: {
                    content: "{}",
                },
                formRule: {},
                formUrisRow: 5,
            }
        },
        methods: {
            // 弹出数据变更表单
            showForm(index) {
                // this.$refs['formData'].resetFields()
                if (index !== undefined) {
                    const record = this.tableData[index]
                    this.formData = {...record}
                } else {
                    this.formData = {}
                }
                this.formModal = true
            },

            // 加载表格数据
            loadTableData(page) {
                let params = {
                    task_id: this.$route.query.task_id,
                    user: this.$route.query.user,
                    log_id: this.$route.query.log_id,
                    page: this.currentPage,
                    page_size: this.pageSize,
                }
                requestAPI('/api/audit/app_log/', params).then(resp => {
                    this.tableData = resp.data.results
                    this.recordTotal = resp.data.count
                    this.showColumns = resp.data.show_columns
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
                        'title': '审阅意见',
                        'key': 'review_content',
                        'align': 'center',
                        render: (h, params) => {
                            let content = params.row['review_content']
                            if(!content || content.length === 0){
                                return h('Button',
                                    {
                                        props: {type: 'primary', size: 'small'},
                                        on: {click: () => {this.editRecordReview(params.index)}}
                                    }, '填写')
                            }else{
                                return h('span', content)
                            }
                        }
                    })

                })
            },
            editRecordReview(index) {
                this.reviewIndex = index
                this.formModal = true
            },
            // 分页 - 更新页面
            changePage(pageNum) {
                this.currentPage = pageNum
                this.loadTableData(pageNum)
            },
            // 生成single审阅信息
            pickRecordInfo(){
                let source_type = this.tableData[this.reviewIndex].type
                let single_id = this.tableData[this.reviewIndex].id
                let user = this.$route.query.name
                let single_desc = '用户【' + user + '】日志'
                return {
                    'single_id': single_id,
                    'single_desc': single_desc
                }
            },
            // 提交审阅意见
            commitRecordReview(){
                let recordInfo = this.pickRecordInfo()
                let postData = {
                    task: this.$route.query.task_id,
                    review_type: 'APP_LOG',
                    content: this.reviewContent,
                    ...recordInfo
                }
                requestAPI('/api/audit/new_review_comment/', {}, 'post', postData).then(resp => {
                    this.$Message.success('保存成功')
                    this.reviewContent = ''
                    this.loadTableData(this.currentPage)
                })
            },
            // 跳转审阅页
            routeBack(){
                this.$router.push({
                    name: 'newreview',
                    params: {
                        id: this.$route.query.task_id,
                        review_type: 'APP'
                    }
                })
            },
            renderToolTip(key, title) {
                return {
                    title: title,
                    key: key,
                    render: (h, params) => {
                        let content = JSON.stringify(params.row[key]);
                        let simpleContent = content;
                        console.log(content)
                        if (content != null){
                            if (content.length > 15) { simpleContent = content.slice(0,15) + '...'}
                        }
                        return h('Tooltip', {
                            props: { placement: 'left' }
                        }, [
                            simpleContent,
                            h('span', { slot: 'content', style: { whiteSpace: 'normal', wordBreak: 'break-all' } }, content)
                        ])
                    }
                }
            },
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
