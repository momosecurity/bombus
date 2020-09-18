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
                    <Input type="text" v-model="formFilter.name" :placeholder="descMap.name"></Input>
                </FormItem>
                <FormItem prop="startup_subject">
                    <Input type="text" v-model="formFilter.startup_subject" :placeholder="descMap.startup_subject"></Input>
                </FormItem>
                <FormItem prop="dept">
                    <Input type="text" v-model="formFilter.dept" :placeholder="descMap.dept"></Input>
                </FormItem>
                <FormItem prop="app_status">
                    <Input type="text" v-model="formFilter.app_status" :placeholder="descMap.app_status"></Input>
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

                <FormItem :label="descMap.name" prop="name">
                    <Input type="text" v-model="formData.name"></Input>
                </FormItem>
                <FormItem :label="descMap.startup_subject" prop="startup_subject">
                    <Input type="text" v-model="formData.startup_subject"></Input>
                </FormItem>
                <FormItem :label="descMap.version" prop="version">
                    <Input type="text" v-model="formData.version"></Input>
                </FormItem>
                <FormItem :label="descMap.app_status" prop="app_status">
                    <Input type="text" v-model="formData.app_status"></Input>
                </FormItem>
                <FormItem :label="descMap.dept" prop="dept">
                    <Input type="text" v-model="formData.dept"></Input>
                </FormItem>
                <FormItem :label="descMap.principal" prop="principal">
                    <Input type="text" v-model="formData.principal"></Input>
                </FormItem>
                <FormItem :label="descMap.remarks" prop="remarks">
                    <Input type="text" v-model="formData.remarks"></Input>
                </FormItem>
                <FormItem :label="descMap.risk_assessment_report_url">
                    <Upload
                        ref="upload"
                        :with-credentials="true"
                        :show-upload-list="false"
                        :action="uploadUrl"
                        :on-success="handleSuccess1"
                    >
                        <Button icon="ios-cloud-upload-outline">上传文件</Button>
                    </Upload>
                    <div v-for="(item,idx) in formData.risk_assessment_report_url">
                        {{item.name}}
                        <Icon type="ios-trash-outline" @click="handleRemove1(idx)"></Icon>
                    </div>
                </FormItem>
                <FormItem :label="descMap.security_commitment_url">
                    <Upload
                        ref="upload"
                        :with-credentials="true"
                        :show-upload-list="false"
                        :action="uploadUrl"
                        :on-success="handleSuccess2"
                    >
                        <Button icon="ios-cloud-upload-outline">上传文件</Button>
                    </Upload>
                    <div v-for="(item,idx) in formData.security_commitment_url">
                        {{item.name}}
                        <Icon type="ios-trash-outline" @click="handleRemove2(idx)"></Icon>
                    </div>
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
        name: 'AppCompliance',
        data() {
            return {
                url: '/api/app-compliance/',
                downloadUrl: '/api/download-file/',
                uploadUrl: '/file/upload/',
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
                    this.formData = {
                        'risk_assessment_report_url': [],
                        'security_commitment_url': [],
                    }
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
            getConfigurableByName(val) {
                for (var i = 0; i < this.ruleAtomTemplates.length; i++) {
                    var ruleAtomTemplate = this.ruleAtomTemplates[i];
                    if (ruleAtomTemplate.name == val) {
                        return ruleAtomTemplate.configurable;
                    }
                }
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
                requestAPI(this.url, params).then(resp => {
                    this.tableData = resp.data.results
                    this.recordTotal = resp.data.count
                    this.descMap = resp.data.desc_map
                    this.showColumns = resp.data.show_columns
                    this.formRule = resp.data.form_rule
                    // this.formFilter = {}
                    this.tableColumns = []
                    this.ruleStatusList = resp.data.rule_status
                    this.ruleAtomTemplates = resp.data.rule_atom_templates

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
                        if(key === 'risk_assessment_report_url' || key === 'security_commitment_url'){
                            column = this.renderDetailButton(key, this.showColumns[key])
                        }
                        this.tableColumns.push(column)
                    }
                    this.tableColumns.push({
                        title: '评估发现',
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
            genDownloadUrl(item){
                let _url = ''
                _url = this.downloadUrl + '?path=' + item.url + '&file_name=' + item.name
                return _url
            },
            // 移除文件
            handleRemove1 (index) {
                let fileList = this.formData['risk_assessment_report_url']
                fileList.splice(index, 1)
            },
            handleRemove2 (index) {
                let fileList = this.formData['security_commitment_url']
                fileList.splice(index, 1)
            },
            fmtFileItem(resp){
                let file = {}
                file['name'] = resp.name
                file['url'] = resp.url
                file['upload_time'] = resp.upload_time
                return file
            },
            handleSuccess1 (res, file) {
                let uploadedFile = this.fmtFileItem(res)
                let fileList = this.formData['risk_assessment_report_url']
                if(fileList && fileList.length > 0){
                    fileList.push(uploadedFile)
                }else{
                    this.formData['risk_assessment_report_url'] = [uploadedFile]
                }
            },
            handleSuccess2 (res, file) {
                let uploadedFile = this.fmtFileItem(res)
                let fileList = this.formData['security_commitment_url']
                if(fileList && fileList.length > 0){
                    fileList.push(uploadedFile)
                }else{
                    this.formData['security_commitment_url'] = [uploadedFile]
                }
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
                    name: 'compliance-detail',
                    params: {
                        id: this.tableData[index].id,
                    }
                })
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
