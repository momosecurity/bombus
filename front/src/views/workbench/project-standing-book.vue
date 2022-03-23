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
                    <Input type="text" v-model="formFilter.project" :placeholder="descMap.project"></Input>
                </FormItem>
                <FormItem prop="startup_subject">
                    <Input type="text" v-model="formFilter.handle_person" :placeholder="descMap.handle_person"></Input>
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
            <template slot-scope="{ row, index }" slot="route">
                <Button type="primary" size="small" @click="routeDetail(index)">详情</Button>
            </template>
            <template slot-scope="{ row, index }" slot="action">
                <Button type="primary" size="small" @click="showForm(index)">更新</Button>
            </template>

            <div slot="footer" class="f-local-footer">总计 {{ recordTotal }} 条, 本页 {{ tableData.length }} 条
            </div>
        </Table>

        <!--分页-->
        <div class="f-local-page">
            <Page :current="currentPage" :total="recordTotal" :page-size="10" @on-change="changePage" show-elevator />
        </div>

        <!--查看及更新表单-->
        <Modal v-model="formModal" title="更新/查看" footer-hide width="700px" :mask-closable="false">
            <Form ref="formData" :model="formData" :rules="formRule" :label-width="120">
                <FormItem label="ID" prop="id" v-show="false">
                    <Input type="text" v-model="formData.id" readonly disabled></Input>
                </FormItem>

                <FormItem :label="descMap.project" prop="project">
                    <Input type="text" v-model="formData.project"></Input>
                </FormItem>
                <FormItem :label="descMap.handle_person" prop="handle_person">
                    <Input type="text" v-model="formData.handle_person"></Input>
                </FormItem>
                <FormItem :label="descMap.remark" prop="remark">
                  <Input type="textarea" v-model="formData.remark"></Input>
                </FormItem>
                <FormItem>
                    <Button type="primary" icon="md-arrow-up" @click="updateRecord('formData')">提交</Button>
                </FormItem>

            </Form>
        </Modal>

        <Modal v-model="urlDetailModal" :title="urlTitle">
            <List border v-if="urlDetail && urlDetail.length > 0">
                <ListItem v-for="item in urlDetail">
                    <a :href="item.url" :download="item.name">{{item.name}}</a>
                </ListItem>
            </List>
        </Modal>
    </div>
</template>

<script>
    import {
        requestAPI
    } from '../../api'
    export default {
        name: 'ProStandingBook',
        data() {
            return {
                url: '/api/project-standing-book/',
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
                configurable: false,

                // url详情表单
                urlDetailModal: false,
                urlDetail: [],
                urlTitle: '',
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
            // 查看变更历史
            showLog(index) {
                this.$router.push({
                    name: 'operationlog',
                    params: {
                        id: this.tableData[index].id,
                    }
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
                let params = {}
                if (page) {
                    params = {
                        ...this.formFilter,
                        ...{
                            page: page,
                        }
                    }
                } else {
                    params = {
                        ...this.formFilter,
                        page: this.currentPage
                    }
                }
                requestAPI(this.url, params).then(resp => {
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
                            'key': key
                        }
                        this.tableColumns.push(column)
                    }
                    this.tableColumns.push({
                        title: '详情',
                        slot: 'route',
                        width: 80,
                        align: 'center'
                    }),
                    this.tableColumns.push({
                        title: '操作',
                        slot: 'action',
                        width: 80,
                        align: 'center',
                    })
                })
            },
            // 分页 - 更新页面
            changePage(pageNum) {
                this.currentPage = pageNum
                this.loadTableData(pageNum)
            },
            renderDetailButton(key, title){
                return {
                    'title': title,
                    'key': key,
                    'align': 'center',
                    'width': 90,
                    render: (h, params) => {
                        return h('Button',
                            {
                                props: {type: 'primary', size: 'small'},
                                on: {click: () => {this.showUrlDetail(params.index, key)}}
                            }, '详情')
                    }
                }
            },
            showUrlDetail(index, key){
                this.urlDetailModal = true
                let recordData = this.tableData[index]
                this.urlDetail = recordData[key]
                this.urlTitle = this.descMap[key]
            },
            // 查看评估发现
            routeDetail(index) {
                this.$router.push({
                    name: 'project-todo',
                    params: {
                        id: this.tableData[index].id,
                    }
                })
                // let route = this.$router.resolve({
                //     name: 'app-todo',
                //     params: {
                //         id: this.tableData[index].id,
                //     }
                // })
                // window.open(route.href, '_blank')
            },
        },
        created() {
            this.loadTableData();
        },
    }
</script>

<style scoped>
    .demo-upload-list {
        display: inline-block;
        width: 60px;
        height: 60px;
        text-align: center;
        line-height: 60px;
        border: 1px solid transparent;
        border-radius: 4px;
        overflow: hidden;
        background: #fff;
        position: relative;
        box-shadow: 0 1px 1px rgba(0, 0, 0, .2);
        margin-right: 4px;
    }

    .demo-upload-list img {
        width: 100%;
        height: 100%;
    }

    .demo-upload-list-cover {
        display: none;
        position: absolute;
        top: 0;
        bottom: 0;
        left: 0;
        right: 0;
        background: rgba(0, 0, 0, .6);
    }

    .demo-upload-list:hover .demo-upload-list-cover {
        display: block;
    }

    .demo-upload-list-cover i {
        color: #fff;
        font-size: 20px;
        cursor: pointer;
        margin: 0 2px;
    }

    .ivu-icon {
        line-height: 58px;
    }

    .span-click {
        cursor: pointer;  /*鼠标悬停变小手*/
        text-decoration:underline;
        &:hover {
            color: blue;
            background: #c2f0f0;
         }
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

</style>
