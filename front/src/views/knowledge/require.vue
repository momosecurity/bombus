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
                    <Input type="text" v-model="formFilter.content" :placeholder="descMap.content"></Input>
                </FormItem>
                <FormItem v-for="(Type, idx) in TagTypeList">
                    <Select v-model="formFilter['type_' + Type.id]" filterable :placeholder="Type.name">
                        <Option v-for="(tag, idx) in TypeTagMap[Type.id]" :value="tag.id" :key="tag.id">{{ tag.name }}</Option>
                    </Select>
                </FormItem>
                <FormItem>
                    <Button type="primary" icon="md-search" @click="filterRecord('formFilter')">查询</Button>
                    <Button type="primary" icon="md-refresh" @click="resetQuery('formFilter')">重置</Button>
                    <Button type="success" icon="md-add-circle" @click="showForm()">新增</Button>
                    <Button type="info" icon="md-settings" @click="routeType">知识坐标系设置</Button>
                    <Button type="info" icon="md-settings" @click="routeTag">知识刻度值管理</Button>
                    <Button type="info" icon="md-settings" @click="ColumnShowConf">显示筛选</Button>
                </FormItem>
            </Form>
        </div>

        <!--数据记录表格-->
        <div style="width: auto; overflow: scroll">
        <Table border :row-class-name="rowClassName" :columns="tableColumns" :data="tableData" size="small">
            <template slot-scope="{ row, index }" slot="action">
                <Button type="primary" size="small" @click="showForm(index)">更新</Button>
                <Button type="primary" size="small" @click="showLog(index)">变更历史</Button>
            </template>

            <div slot="footer" class="f-local-footer">总计 {{ recordTotal }} 条, 本页 {{ tableData.length }} 条
            </div>
        </Table>
        </div>

        <!--分页-->
        <div class="f-local-page">
            <Page :current="currentPage" :total="recordTotal" :page-size-opts="pageSizeOpt"
                  :page-size="pageSize" @on-change="changePage"
                  @on-page-size-change="changePageSize"
                  show-elevator
                  show-sizer
            />
        </div>

        <!--查看及更新表单-->
        <Modal v-model="formModal" title="更新/查看" footer-hide :mask-closable="false">
            <Form ref="formData" :model="formData" :rules="formRule" :label-width="120"  :disabled="histModal">
                <FormItem label="ID" prop="id" v-show="false">
                    <Input type="text" v-model="formData.id" readonly disabled></Input>
                </FormItem>

                <FormItem :label="descMap.content" prop="content">
                    <Input type="textarea" v-model="formData.content"></Input>
                </FormItem>
                <FormItem :label="descMap.source" prop="source">
                    <Input type="text" v-model="formData.source"></Input>
                </FormItem>
                <FormItem v-for="(item, idx) in TagTypeList" :label="item.name" :prop="typePrefix + item.id">
                    <Select v-model="formData[typePrefix + item.id]" filterable :multiple="item.select_type == 'MULTI'">
                        <Option v-for="(tag, idx) in TypeTagMap[item.id]" :value="tag.id" :key="tag.id">{{ tag.name }}</Option>
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
        <!-- 列展示 -->
        <Modal v-model="columnModal" title="列展示" @on-ok="saveColumns">
            <CheckboxGroup v-model="selectColumns">
                <Checkbox v-for="(v, k) in showColumns" :label='k' :key="k">{{v}}</Checkbox>
            </CheckboxGroup>
        </Modal>
    </div>
</template>

<script>
    import {
        requestAPI
    } from '../../api'
    export default {
        name: 'Require',
        data() {
            return {
                url: '/api/knowledge/require/',
                histUrl: '/api/record-history/',
                typePrefix: 'type_',
                descMap: {},
                showColumnName: 'kn:require-show-columns',
                showColumns: {},
                selectColumns: [],
                defaultShowColumns: [],
                columnModal: false,
                columnWidth: 200,
                // 规则启用状态定义
                TagTypeList: [],
                TypeTagMap: {},
                TagTypeMap: {},
                TagTypePropertyList: [],
                TypePropertyMap: {},
                PropertyShow: false,
                StatusList: [],

                // 数据总记录数据
                recordTotal: 0,
                // 当前页号
                currentPage: 1,
                pageSize: 10,
                pageSizeOpt: [10, 20, 30, 40, 50],

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
                formData: {},
                formModal: false,
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
                        this.formData = this.fmtDetailData(resp.data)
                    })
                } else {
                    this.formData = {}
                }
                this.formModal = true
            },
            // 类型管理
            routeType() {
                this.$router.push({
                    name: 'tag-type'
                })
            },
            // 标签管理
            routeTag() {
                this.$router.push({
                    name: 'tag'
                })
            },
            // 格式化详情数据
            fmtDetailData(detailData){
                let formData = {}
                for(const key in detailData){
                    if(!key.startsWith('type_')){
                        formData[key] = detailData[key]
                    }
                }
                this.splitTags(formData)
                return formData
            },
            rowClassName (row, index) {
                if(row.lack_required){
                    return 'lack-require-tip-row';
                }
                return '';
            },
            // 保存前格式化
            preSave(formData){
                let fmtData = {}
                let tags = []
                for(const key in formData){
                    if(!key.startsWith('type_')){
                        fmtData[key] = formData[key]
                    }else{
                        let typeTags = formData[key]
                        if(typeTags.constructor===Array){
                            tags = tags.concat(typeTags)
                        }else{
                            tags.push(typeTags)
                        }
                    }
                }
                fmtData['tags'] = tags
                return fmtData
            },
            // fmtFilter
            fmtFilter(filterData){
                let filterResult = {}
                let tags = []
                for(const key in filterData){
                    if(!key.startsWith('type_')){
                        filterResult[key] = filterData[key]
                    }else{
                        let typeTags = filterData[key]
                        if(typeTags.constructor===Array){
                            tags = tags.concat(typeTags)
                        }else{
                            tags.push(typeTags)
                        }
                    }
                }
                filterResult['tags'] = tags.join(',')
                return filterResult
            },
            // 拆分标签
            splitTags(formData){
                let tags = formData['tags']
                for(const tagId of tags){
                    let tagType = this.TagTypeMap[tagId]
                    let typeName = 'type_' + tagType
                    if(!formData[typeName]){
                        formData[typeName] = [tagId]
                    }else{
                        formData[typeName].push(tagId)
                    }
                }
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
                    this.formData = this.fmtDetailData(JSON.parse(resp.data.content))
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
                        let form = this.preSave(this.formData)
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
            // 生成标签到类型映射
            genTagTypeMap(){
                let result = {}
                for(const type in this.TypeTagMap){
                    for(const tag of this.TypeTagMap[type]){
                        result[tag.id] = type
                    }
                }
                this.TagTypeMap = result
            },
            // 加载表格数据
            loadTableData(page) {
                let params = {}
                if (page) {
                    params = {
                        ...this.fmtFilter(this.formFilter),
                        ...{
                            page: page,
                            page_size: this.pageSize
                        }
                    }
                } else {
                    params = {
                        ...this.fmtFilter(this.formFilter),
                        ...{
                            page: this.currentPage,
                            page_size: this.pageSize
                        }
                    }
                }
                requestAPI(this.url, params).then(resp => {
                    this.tableData = resp.data.results
                    this.addShowColumn(this.tableData)
                    this.recordTotal = resp.data.count
                    this.descMap = resp.data.desc_map
                    this.showColumns = resp.data.show_columns
                    this.formRule = resp.data.form_rule
                    this.expandColumns = resp.data.tag_type_list
                    this.tableColumns = []
                    this.TagTypeList = resp.data.tag_type_list
                    this.TypePropertyMap = resp.data.type_property_map
                    this.TypeTagMap = resp.data.type_tag_map
                    this.genTagTypeMap()
                    this.StatusList = resp.data.status_list
                    this.histModal = false
                    this.formModal = false
                    this.defaultShowColumns = resp.data.default_columns
                    if(this.selectColumns.length === 0){
                        this.selectColumns = localStorage.getItem(this.showColumnName)
                        if(this.selectColumns && this.selectColumns.length !== 0){
                            this.selectColumns = this.selectColumns.split(',')
                        }else{
                            this.selectColumns = this.defaultShowColumns
                        }
                    }
                    let SelShowColumns = {}
                    for(const k of this.selectColumns){
                        SelShowColumns[k] = this.showColumns[k]
                    }
                    this.tableColumns.push({
                        title: '#',
                        type: 'index',
                        width: 55
                    })
                    let sourceColumn = {}
                    for (const key in SelShowColumns) {
                        let column = {
                            'title': SelShowColumns[key],
                            'key': key,
                            'type': 'html',
                            // 'width': this.columnWidth,
                            'resizable': true
                        }
                        if(key==='content'){
                            column = this.renderBreakContent(key, SelShowColumns[key])
                        }
                        if (key.startsWith('type_')){
                            column = this.renderToolTip(key, SelShowColumns[key])
                        }
                        if(key==='source'){
                            sourceColumn = column
                        }else{
                            this.tableColumns.push(column)
                        }
                    }
                    if(JSON.stringify(sourceColumn) !== '{}'){
                        this.tableColumns.push(sourceColumn)
                    }
                    this.tableColumns.push({
                        title: '操作',
                        slot: 'action',
                        width: 160,
                    })
                })
            },
            // 在类型变化时, 清空属性值
            PropertyIsValid(){
                for (const curPro of this.TagTypePropertyList){
                    if(curPro.id === this.formData.tag_type_property){
                        return true
                    }
                }
                return false
            },
            // 分页 - 更新页面
            changePage(pageNum) {
                this.currentPage = pageNum
                this.loadTableData(pageNum)
            },
            changePageSize(pageSize){
                this.pageSize = pageSize
                this.currentPage = 1
                this.loadTableData()
            },
            saveColumns() {
                let SelShowColumns = {}
                localStorage.setItem(this.showColumnName, this.selectColumns)
                if (!this.selectColumns || this.selectColumns.length === 0) {
                    this.selectColumns = this.defaultShowColumns
                }
                for (const k of this.selectColumns) {
                    SelShowColumns[k] = this.showColumns[k]
                }
                this.tableColumns = []
                this.tableColumns.push({
                    title: '#',
                    type: 'index',
                    width: 55
                })
                let sourceColumn = {}
                for (const key in SelShowColumns) {
                    let column = {
                        'title': SelShowColumns[key],
                        'key': key,
                        'type': 'html',
                        // 'width': this.columnWidth,
                        'resizable': true,
                    }
                    if (key === 'content') {
                        column = this.renderBreakContent(key, SelShowColumns[key])
                    }
                    if (key.startsWith('type_')){
                        column = this.renderToolTip(key, SelShowColumns[key])
                    }
                    if (key === 'source') {
                        sourceColumn = column
                    } else {
                        this.tableColumns.push(column)
                    }
                }
            if (JSON.stringify(sourceColumn) !== '{}') {
                this.tableColumns.push(sourceColumn)
            }
            this.tableColumns.push({
                title: '操作',
                slot: 'action',
                width: 160,
            })

            },
            concatShowColumnName(columnName){
                return columnName + '_simple'
            },
            // 装饰返回值, 添加外显精简字段
            addShowColumn(tableData){
                for(let record of tableData){
                    for(const key in record){
                        let showColumnName = this.concatShowColumnName(key)
                        if(key.startsWith('type_')){
                            record[showColumnName] = this.pickShow(record[key])
                        }
                    }
                }
            },
            // 抽取content内容
            pickShow(content){
                if(!content || content.length === 0){
                    return content
                }
                let simpleContentList = []
                let showLength = 50
                let regex = /<[^>]+>/g
                let contentList = content.split(',\n')
                for(const item of contentList){
                    let result = item.replace(regex, '')
                    if(result!=null){
                        simpleContentList = simpleContentList.concat(item.trim())
                        showLength -= result.length
                        if(showLength <= 0){
                            break
                        }
                    }
                }
                let simpleContent = simpleContentList.join(',\n')
                if(simpleContent === content){
                    simpleContent = ''
                }
                return simpleContent
            },
            renderToolTip(key, title) {
                let sKey = this.concatShowColumnName(key)
                return {
                    title: title,
                    key: sKey,
                    'resizable': true,
                    // 'width': this.columnWidth,
                    render: (h, params) => {
                        let tip = '\n·········'
                        let content = params.row[sKey];
                        if(!content){
                            content = params.row[key]
                            tip = ''
                        }
                        if(!content){content = ''}
                        let renderArray = [
                            h('span', {
                                domProps: {
                                    innerHTML: '<pre>' + content + '</pre>'
                                }
                            }, content)
                        ]
                        if(tip){
                            renderArray.push(
                                h('a', {
                                    style: {
                                        marginLeft: '7px',
                                        marginTop: '0px',
                                    },
                                    on: {
                                        click: () => {
                                            this.showAll(params.index, key)
                                        }
                                    },
                                }, tip)
                            )
                        }
                        return h('div', renderArray)
                    }
                }
            },
            renderBreakContent(key, title){
                return {
                    title: title,
                    key: key,
                    resizable: true,
                    // 'width': 400,
                    render: (h, params) => {
                        let content = params.row[key]
                        return h('pre', content)
                    }
                }
            },
            showAll(index, key){
                let record = this.tableData[index]
                this.$set(record, this.concatShowColumnName(key), '')
                this.$set(this.tableData, index, record)
            },
            ColumnShowConf(){
                this.columnModal = true
            },
        },
        created() {
            this.loadTableData();
        }
    }
</script>

<style>
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

    .ivu-table .lack-require-tip-row td{
        background-color: #e5fdff;
        /*color: #fff;*/
    }

    .f-tab {
        font-weight: bold;
    }
</style>
