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
                    <Button type="success" icon="md-add-circle" @click="showForm()">新增</Button>
                </FormItem>
            </Form>
        </div>

        <!--数据记录表格-->
        <Table border :columns="tableColumns" :data="tableData" size="small">
            <template slot-scope="{ row, index }" slot="action">
                <Button type="error" size="small" @click="removeRecord(index)">删除</Button>
            </template>
            <template slot-scope="{ row, index }" slot="perm">
                <Button type="primary" size="small" @click="showPerm(index)">权限设置</Button>
            </template>
            <template slot-scope="{ row, index }" slot="pass">
                <Button type="primary" size="small" @click="showPass(index)">重置密码</Button>
            </template>

            <div slot="footer" class="f-local-footer">总计 {{ recordTotal }} 条, 本页 {{ tableData.length }} 条
            </div>
        </Table>

        <!--分页-->
        <div class="f-local-page">
            <Page :current="currentPage" :total="recordTotal" :page-size="10" @on-change="changePage" show-elevator />
        </div>

        <!--查看及更新表单-->
        <Modal v-model="formModal" title="新增" footer-hide width="700px" :mask-closable="false">
            <Form ref="formData" :model="formData" :rules="formRule" :label-width="120">
                <FormItem label="ID" prop="id" v-show="false">
                    <Input type="text" v-model="formData.id" readonly disabled></Input>
                </FormItem>

                <FormItem label="名称" prop="name">
                    <Input type="text" v-model="formData.name"></Input>
                </FormItem>
                <FormItem label="邮箱" prop="desc">
                    <Input cols="70" v-model="formData.email"></Input>
                </FormItem>
                <FormItem>
                    <Button type="primary" icon="md-arrow-up" @click="addRecord('formData')">提交</Button>
                </FormItem>

            </Form>
        </Modal>
        <Modal v-model="permFormModal" title="权限" footer-hide width="700px" :mask-closable="false">
            <Form ref="permFormData" :model="permFormData" :label-width="120">
                <FormItem label="ID" prop="id" v-show="false">
                    <Input type="text" v-model="permFormData.id" readonly disabled></Input>
                </FormItem>
                <FormItem label="权限列表">
                    <Select  v-model="permFormData.perms" filterable multiple>
                        <Option v-for="(item, idx) in permList" :value="item.key" :key="item.key">{{ item.name }}</Option>
                    </Select>
                </FormItem>
                <FormItem>
                    <Button type="primary" icon="md-arrow-up" @click="updateRecord('permFormData')">提交</Button>
                </FormItem>

            </Form>
        </Modal>
        <Modal v-model="passFormModal" title="更新密码" footer-hide width="700px" :mask-closable="false">
            <Form ref="passFormData" :model="passFormData" :rules="passRules" :label-width="120">
                <FormItem label="ID" prop="id" v-show="false">
                    <Input type="text" v-model="passFormData.id" readonly disabled></Input>
                </FormItem>
                <FormItem label="更新密码" prop="password">
                    <Input type="text" v-model="passFormData.password"></Input>
                </FormItem>
                <FormItem>
                    <Button type="primary" icon="md-arrow-up" @click="updatePass('passFormData')">提交</Button>
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
        name: 'RuleAtom',
        data() {
            return {
                descMap: {},
                showColumns: [],
                // 规则启用状态定义
                ruleStatusList: [],
                ruleAtomTemplates: [],
                regexRuleList: [],

                // 数据总记录数据
                recordTotal: 0,
                // 当前页号
                currentPage: 1,

                // 表格数据
                tableColumns: [],
                tableData: [],
                permList: [],

                // 数据过滤表单
                formFilter: {},
                formFilterRule: {},
                configurable: false,

                // 数据更新表单
                formModal: false,
                formData: {},
                formRule: {},
                formUrisRow: 5,
                // 权限变更表单
                permFormModal: false,
                permFormData: {},
                passFormModal: false,
                passFormData: {},
                passRules: {
                    password: [
                        { required: true, message: '密码不能为空', trigger: 'blur' },
                    ]
                  },
            }
        },
        methods: {
            // 弹出数据变更表单
            showForm(index) {
                this.$refs['formData'].resetFields()
                if (index !== undefined) {
                    const url = `/api/sso/user/${this.tableData[index].id}/`
                    requestAPI(url, {}, 'get').then(resp => {
                        this.formData = resp.data
                    })
                } else {
                    this.formData = {}
                }
                this.formModal = true
            },
            showPerm(index) {
                this.permFormData = {
                    'id': this.tableData[index].id,
                    'perms': this.tableData[index].perms
                }
                this.permFormModal = true
            },
            showPass(index) {
                this.passFormData = {
                    'id': this.tableData[index].id,
                    'password': ''
                }
                this.passFormModal = true
            },
            // 删除数据记录
            removeRecord(index) {
                const url = `/api/sso/user/${this.tableData[index].id}/`
                requestAPI(url, {}, 'delete').then(resp => {
                    this.loadTableData()
                    this.$Message.success(`删除 ${this.tableData[index].username} 成功`)
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
                this.loadTableData()
            },
            // 更新密码
            updatePass(name) {
                this.$refs[name].validate((valid) => {
                    if (!valid) {
                        this.$Message.error('输入有误！请检查')
                    } else {
                        let form = this.passFormData
                        console.log(form)
                        let postData = {...form}
                        const url = `/api/sso/user/${form.id}/`
                        requestAPI(url, {}, 'patch', postData).then(resp => {
                            this.$Message.success('更新成功')
                            this.loadTableData()
                        })
                        this.passFormModal = false
                    }
                })
            },
            // 新增
            addRecord(name) {
                this.$refs[name].validate((valid) => {
                    if (!valid) {
                        this.$Message.error('输入有误！请检查')
                    } else {

                        let form = this.formData
                        let postData = {...form}

                        if (form.id) {
                            const url = `/api/sso/user/${form.id}/`
                            requestAPI(url, {}, 'patch', postData).then(resp => {
                                this.$Message.success('更新成功')
                                this.loadTableData()
                            })
                        } else {
                            requestAPI('/api/sso/user/', {}, 'post', postData).then(resp => {
                                this.$Message.success('添加成功')
                                this.loadTableData()
                            })
                        }
                        this.formModal = false
                    }
                })
            },
            // 表单更新
            updateRecord(name) {
                this.$refs[name].validate((valid) => {
                    if (!valid) {
                        this.$Message.error('输入有误！请检查')
                    } else {

                        let form = this.permFormData
                        let postData = {...form}

                        if (form.id) {
                            const url = `/api/sso/user/${form.id}/`
                            requestAPI(url, {}, 'patch', postData).then(resp => {
                                this.$Message.success('更新成功')
                                this.loadTableData()
                            })
                        } else {
                            requestAPI('/api/sso/user/', {}, 'post', postData).then(resp => {
                                this.$Message.success('添加成功')
                                this.loadTableData()
                            })
                        }
                        this.permFormModal = false
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
                        ...this.formFilter
                    }
                }
                requestAPI('/api/sso/user/', params).then(resp => {
                    this.tableData = resp.data.results
                    this.recordTotal = resp.data.count
                    this.descMap = resp.data.desc_map
                    this.showColumns = resp.data.show_columns
                    this.formRule = resp.data.form_rule
                    this.permList = resp.data.perm_keys
                    this.tableColumns = []
                    this.formData = {}
                    this.permFormData = {}
                    this.passFormData = {}

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
                        width: 120,
                        align: 'center'
                    })
                    this.tableColumns.push({
                        title: '权限',
                        slot: 'perm',
                        width: 120,
                        align: 'center'
                    })
                    this.tableColumns.push({
                        title: '密码',
                        slot: 'pass',
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
        watch: {
            'formModal' (val) {
                if(!val){
                    this.formData = {}
                }
            },
            'permFormModal' (val) {
                if(!val){
                    this.permFormData = {}
                }
            },
            'passFormModal' (val) {
                if(!val){
                    this.passFormData = {}
                }
            },
            deep:true
        },
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
