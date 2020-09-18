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

<!--                <FormItem>-->
<!--                    <Button type="primary" icon="md-search" @click="filterRecord('formFilter')">查询</Button>-->
<!--                </FormItem>-->

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
        <Modal v-model="formModal" title="详情" footer-hide width="700px">
<!--            <span v-text="formData.content"></span>-->
            <json-viewer :value="JSON.parse(formData.content)"></json-viewer>
        </Modal>

    </div>
</template>

<script>
    import {
        requestAPI
    } from '../../api'
    import JsonViewer from 'vue-json-viewer'
    export default {
        name: 'bashCommand',
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
                formModal: false,
                formData: {
                    content: "{}",
                },
                formRule: {},
                formUrisRow: 5
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

            // 删除数据记录
            removeRecord(index) {
                const url = `/api/audit/bash_command/${this.tableData[index].id}/`
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
            // 加载表格数据
            loadTableData(page) {
                let params = {}
                if (page) {
                    params = {
                        task_id: this.$route.params.task_id,
                        user: this.$route.params.user,
                        ...{
                            page: this.currentPage
                        }
                    }
                } else {
                    params = {
                        task_id: this.$route.params.task_id,
                        user: this.$route.params.user,
                    }
                }
                requestAPI('/api/audit/bg_access_log/', params).then(resp => {
                    this.tableData = resp.data.results
                    this.recordTotal = resp.data.count
                    this.descMap = resp.data.desc_map
                    this.showColumns = resp.data.show_columns
                    this.serverKind = resp.data.server_kind
                    this.formFilter = {}
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
                        if (key === 'params') {
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
