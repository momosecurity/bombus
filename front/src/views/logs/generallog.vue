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
<!--                <FormItem prop="req_method">-->
<!--                    <Input type="text" v-model="formFilter.req_method" :placeholder="descMap.req_method"></Input>-->
<!--                </FormItem>-->
<!--                <FormItem prop="req_path">-->
<!--                    <Input type="text" v-model="formFilter.req_path" :placeholder="descMap.req_path"></Input>-->
<!--                </FormItem>-->
                <FormItem prop="req_user">
                    <Input type="text" v-model="formFilter.req_user" :placeholder="descMap.req_user"></Input>
                </FormItem>
                <FormItem prop="req_time">
                    <DatePicker ref="leftTime" type="datetime" @on-change="getLeftTime" format="yyyy-MM-dd HH:mm" placeholder="请求开始时间"></DatePicker>
                </FormItem>
                <FormItem prop="req_time">
                    <DatePicker ref="rightTime" type="datetime" @on-change="getRightTime" format="yyyy-MM-dd HH:mm" placeholder="请求截止时间"></DatePicker>
                </FormItem>

                <FormItem>
                    <Button type="primary" icon="md-search" @click="filterRecord('formFilter')">查询</Button>
                    <Button type="primary" icon="md-refresh" @click="resetQuery('formFilter')">重置</Button>
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
            <Page :current="currentPage" :total="recordTotal" :page-size="pageSize" @on-change="changePage" show-elevator />
        </div>

        <!--数据记录更新表单-->
<!--        <Modal v-model="jsonRespContentFormModal" title="详情" footer-hide width="700px">-->
<!--&lt;!&ndash;            <span v-text="formData.resp_content"></span>&ndash;&gt;-->
<!--            <json-viewer :value="JSON.parse(formData.resp_content)"></json-viewer>-->
<!--        </Modal>-->
<!--        <Modal v-model="textRespContentFormModal" title="详情" footer-hide width="700px">-->
<!--            <span v-text="formData.resp_content"></span>-->
<!--        </Modal>-->
        <Modal v-model="respContentFormModal" title="响应体" footer-hide width="700px">
            <textarea disabled cols="90" rows="20" v-model="formData.resp_content"></textarea>
        </Modal>

    </div>
</template>

<script>
    import {
        requestAPI
    } from '../../api'
    import JsonViewer from 'vue-json-viewer'
    export default {
        name: 'GeneralLog',
        components: {
            JsonViewer
        },
        data() {
            return {
                descMap: {},
                showColumns: [],

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
                respContentFormModal: false,
                jsonRespContentFormModal: false,
                textRespContentFormModal: false,
                formData: {
                    resp_content: "{}",
                },
                formRule: {},
                formUrisRow: 5,
                pageSize: 30
            }
        },
        methods: {
            // 删除数据记录
            removeRecord(index) {
                const url = `/api/audit_log/${this.tableData[index].id}/`
                requestAPI(url, {}, 'delete').then(resp => {
                    this.loadTableData()
                    this.$Message.success(`删除 ${this.tableData[index].desc} 成功`)
                })
            },
            getLeftTime: function(time_str, time_type) {
                this.formFilter.req_time_left = time_str
            },
            getRightTime: function(time_str, time_type) {
                this.formFilter.req_time_right = time_str
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
                this.$refs.leftTime.handleClear()
                this.$refs.rightTime.handleClear()
                this.loadTableData()
            },
            // 加载表格数据
            loadTableData(page) {
                let params = {}
                if (page) {
                    params = {
                        ...this.formFilter,
                        ...{
                            page: this.currentPage,
                            page_size: this.pageSize
                        }
                    }
                } else {
                    params = {
                        ...this.formFilter,
                        ...{
                            page_size: this.pageSize
                        }
                    }
                }
                requestAPI('/api/audit_log/', params).then(resp => {
                    this.tableData = resp.data.results
                    this.recordTotal = resp.data.count
                    this.descMap = resp.data.desc_map
                    this.showColumns = resp.data.show_columns
                    this.serverKind = resp.data.server_kind
                    // this.formFilter = {}
                    this.tableColumns = []
                    this.userLoading = false
                    this.userSearchResult = []
                    // this.sysList = []
                    this.tableColumns.push({
                        title: '#',
                        type: 'index',
                        width: 55
                    })
                    for (const key in this.showColumns) {
                        if (key === 'resp_content'){
                            this.tableColumns.push(this.renderRespContent(key, this.showColumns[key]))
                        }
                        else if (key === 'req_user_agent' || key === 'req_body' || key === 'resp_content_type') {
                            this.tableColumns.push(this.renderToolTip(key, this.showColumns[key]))
                        }
                        else {
                            let column = {
                                'title': this.showColumns[key],
                                'key': key
                            }
                            this.tableColumns.push(column)
                        }

                    }
                    // this.tableColumns.push({
                    //     title: '查看',
                    //     slot: 'action',
                    //     width: 150,
                    //     align: 'center'
                    // })
                })
            },

            // 分页 - 更新页面
            changePage(pageNum) {
                this.currentPage = pageNum
                this.loadTableData(pageNum)
            },
            // 渲染返回数据
            renderRespContent(key, title) {
                return {
                    title: title,
                    key: key,
                    render: (h, params) => {
                        let content = params.row[key];
                        if (content != null && content.length != 0){
                            if (content.length > 10) { content = content.slice(0,10) + '...'}
                            return h('div', [
                                h('a', {
                                    on: {
                                        click: () => {
                                            this.showRespContent(params.index)
                                        }
                                    }
                                }, content)
                            ]);
                        }
                        else{
                            return h('span', '空')
                        }
                    }
                }
            },
            renderToolTip(key, title) {
                return {
                    title: title,
                    key: key,
                    render: (h, params) => {
                        let content = params.row[key];
                        if (content != null){
                            if (content.length > 10) { content = content.slice(0,15) + '...'}
                        }
                        return h('Tooltip', {
                            props: { placement: 'left' }
                        }, [
                            content,
                            h('span', { slot: 'content', style: { whiteSpace: 'normal', wordBreak: 'break-all' } },params.row[key])
                        ])
                    }
                }
            },
            showRespContent(index) {
                // this.$refs['formData'].resetFields()
                if (index !== undefined) {
                    const record = this.tableData[index]
                    this.formData = {...record}
                } else {
                    this.formData = {}
                }
                this.respContentFormModal = true
                // if (this.isJSON(this.formData.resp_content)) {
                //     this.jsonRespContentFormModal = true
                // } else {
                //     this.textRespContentFormModal = true
                // }
            },
            isJSON(str) {
                if (typeof str == 'string') {
                    try {
                        var obj=JSON.parse(str);
                        if (typeof obj == 'object' && obj ){
                            return true;
                        } else {
                            return false;
                        }
                    } catch(e) {
                        console.log('error：'+str+'!!!'+e);
                        return false;
                    }
                }
                console.log('It is not a string!')
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
