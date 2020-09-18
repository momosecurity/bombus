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
        <Card>
            <Row v-for="row in Math.ceil(Statistic.length/4)" v-if="Statistic.length >= 4">
                <Col :span="24/4" v-for="(item, idx) in Statistic.slice((row-1)*4, row*4)">
                    <span style="font-size: 18px"> <b>{{item.desc}}</b> </span> <span style="font-size: 20px; color: #3c78d8">{{item.count}} </span>
                </Col>
            </Row>
            <Row v-else>
                <Col :span="24/Statistic.length" v-for="(item, idx) in Statistic">
                    <span style="font-size: 18px"> <b>{{item.desc}}</b> </span> <span style="font-size: 20px; color: #3c78d8;">{{item.count}} </span>
                </Col>
            </Row>
        </Card>


        <Card>
             <div style="margin-left: 17px">
                <Form class="f-local-form" ref="formFilter" :model="formFilter" style="width: 400px">

                    <FormItem label="搜索:">
                        <Row>
                        <Col span="10">
                            <Input type="text" v-model="formFilter.content" placeholder="关键字"></Input>
                        </Col>
                        <Col span="4" offset="1">
                            <Button type="primary" icon="md-search" @click="filterRecord('formFilter')">查询</Button>
                        </Col>
                        <Col span="4" offset="2">
                            <Button type="primary" icon="md-settings" @click="ColumnShowConf">显示筛选</Button>
                        </Col>
                        </Row>
                    </FormItem>
                </Form>
            </div>
<!--            <hr style="border:1px dashed #000; height:1px">-->
            <Card>
                <div class="box">
                    <Row style="padding-top: 5px" type="flex" justify="start" v-for="(type,index) in TagTypeList"
                         :key="type.id"
                         v-if="typeFilterShow(type)">
                    <Col span="2"><b>{{type.name}}</b>:</Col>
                    <Col span="22">
                      <a href="#"
                        v-for="(tag,idx) in [{'id': type.id + '_all', 'name': '全部'}].concat(TypeTagMap[type.id])"
                        :key="tag.id"
                        @click="select(tag.id, type.id)"
                        :class="[SelectedTag.indexOf(tag.id)!==-1? 'tag-active': 'text-filter']">
                          <span><b>{{tag.name}}</b></span>
                      </a>

                    </Col>
                  </Row>
                </div>
            </Card>
        </Card>


        <!--数据记录表格-->
        <div style="width: auto; overflow: scroll">
        <Table border :columns="tableColumns" :data="tableData" size="small">
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
                  transfer
            />
        </div>

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
                typePrefix: 'type_',
                showColumnName: 'kn:overlook-show-columns',
                descMap: {},
                showColumns: {},
                selectColumns: [],
                defaultShowColumns: [],
                columnModal: false,
                columnWidth: 200,
                // 规则启用状态定义
                TagTypeList: [],
                TypeTagMap: {},
                TagTypePropertyList: [],
                TypePropertyMap: {},
                PropertyShow: false,
                StatusList: [],
                Statistic: [],
                SelectedTag: [],

                // 数据总记录数据
                recordTotal: 0,
                // 当前页号
                currentPage: 1,
                pageSize: 30,
                pageSizeOpt: [10,20,30,40,50],

                // 表格数据
                tableColumns: [],
                tableData: [],

                // 数据过滤表单
                formFilter: {},
                formFilterRule: {},
                configurable: false,

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
                        this.formData = resp.data
                    })
                } else {
                    this.formData = {}
                }
                this.formModal = true
            },
            // 过滤器是否展示
            typeFilterShow(type){
                if(type.opt_show==='TRUE' && this.TypeTagMap[type.id] && this.TypeTagMap[type.id].length !== 0){
                    return true
                }else{
                    return false
                }
            },
            // 取消该类型的选中状态
            cancelTypeTagSelect(type){
                let tags = this.TypeTagMap[type]
                for(const tag of tags){
                    let idx = this.SelectedTag.indexOf(tag.id)
                    if(idx !== -1){
                        this.SelectedTag.splice(idx, 1)
                    }
                }
            },

            // 取消类型全部的选择
            cancelTypeAllSelect(type){
                let tagId = type + '_all'
                let idx = this.SelectedTag.indexOf(tagId)
                if(idx !== -1){
                    this.SelectedTag.splice(idx, 1)
                }
            },
            // 选中状态
            select(tagId, typeId){
                if(tagId.endsWith('_all')){
                    let typeAll = tagId.slice(0, -4)
                    this.cancelTypeTagSelect(typeAll)
                }
                else{
                    this.cancelTypeAllSelect(typeId)
                }
                let idx = this.SelectedTag.indexOf(tagId)
                if(idx === -1){
                    this.SelectedTag.push(tagId)
                }else{
                    this.SelectedTag.splice(idx, 1)
                }
                this.filterRecord('formFilter')
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
            // 获取选中的过滤标签
            clearTag(){
                let clearTags = []
                for(const tag of this.SelectedTag){
                    if(!tag.endsWith('_all')){
                        clearTags.push(tag)
                    }
                }
                // 一定不能加空格
                return clearTags.join(',')
            },
            // 加载表格数据
            loadTableData(page) {
                let params = {}
                if (page) {
                    params = {
                        ...this.formFilter,
                        ...{
                            tags: this.clearTag()
                        },
                        ...{
                            page: page,
                            page_size: this.pageSize,
                        }
                    }
                } else {
                    params = {
                        ...this.formFilter,
                        ...{
                            tags: this.clearTag()
                        },
                        ...{
                            page: this.currentPage,
                            page_size: this.pageSize,
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
                    this.StatusList = resp.data.status_list
                    this.Statistic = resp.data.statistic
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
                    for (const key in SelShowColumns) {
                        let column = {
                            'title': SelShowColumns[key],
                            'key': key,
                            'type': 'html',
                            'width': this.columnWidth,
                            'resizable': true,
                        }
                        if(key==='content'){
                            column = this.renderBreakContent(key, SelShowColumns[key])
                        }
                        if (key.startsWith('type_')){
                            column = this.renderToolTip(key, SelShowColumns[key])
                        }
                        this.tableColumns.push(column)
                    }
                })
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
                let contentList = content.split('\n')
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

                let simpleContent = simpleContentList.join('\n')
                if(simpleContent === content){
                    simpleContent = ''
                }
                return simpleContent
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
            ColumnShowConf(){
                this.columnModal = true
            },
            concatShowColumnName(columnName){
                return columnName + '_simple'
            },
            renderBreakContent(key, title){
                return {
                    'title': title,
                    'key': key,
                    'resizable': true,
                    // 'width': 400,
                    render: (h, params) => {
                        let content = params.row[key]
                        return h('pre', content)
                    }
                }
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
            showAll(index, key){
                let record = this.tableData[index]
                this.$set(record, this.concatShowColumnName(key), '')
                this.$set(this.tableData, index, record)
            },
            saveColumns() {
                let SelShowColumns = {}
                localStorage.setItem(this.showColumnName, this.selectColumns)
                if(!this.selectColumns || this.selectColumns.length === 0){
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
                for (const key in SelShowColumns) {
                    let column = {
                        'title': SelShowColumns[key],
                        'key': key,
                        'type': 'html',
                        // 'width': this.columnWidth,
                        'resizable': true
                    }
                    if (key === 'content') {
                        column = this.renderBreakContent(key, SelShowColumns[key])
                    }
                    if (key.startsWith('type_')){
                        column = this.renderToolTip(key, SelShowColumns[key])
                    }
                    this.tableColumns.push(column)
                }
            }
        },
        created() {
            this.loadTableData();
        }
    }
</script>
<style>
    .auto-column-size-table table {
      table-layout: auto;
    }
    .auto-column-size-table table colgroup col {
      display: none;
    }
</style>
<style scoped>
    .filter-more {
        width: 90%;
        margin: 0 auto;
        border: 1px solid #e8f4fd;
        /*padding: 25px 15px;*/
    }
    .selectbox-leave-active,
    .selectbox-enter-active {
      transition: all 1s ease;
    }
    .selectbox-leave-active,
    .selectbox-enter {
        height: 0px !important;
    }
    .selectbox-leave,
    .selectbox-enter-active {
        height: 150px;
    }
    .box {
        /*height: 150px;*/
        overflow: hidden;
    }
    .tag-item {
        display: inline-block;
        padding: 10px 20px;
        background-color: #666;
        margin-left: 20px;
        color: #fff;
        border-radius: 10px;
    }
    .text-filter {
          display: inline-block;
          color: #335EEB;
          padding: 2px 6px;
          span {
            display: inline-block;
            text-align: center;
            &:hover {
              border-radius: 40px;
              color: #000000;
              animation-fill-mode: forwards;
            }
        }
    }
    .tag-active {
          background-color: #d0cdff;
          border-radius: 20px;
          padding: 2px 6px;
          color: #335EEB;
          &:hover {
              background-color: #F9FBFD;
          }
    }
    .text-select {
      display: inline-block;
      padding: 0px 5px;
      border: 1px solid #268edb;
      border-radius: 40px;
      color: #268edb;
      font-size: 14px;
      margin-right: 20px;
      i {
        display: inline-block;
        height: 100%;
        font-size: 15px;
        padding: 0px 5px;
      }
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

    /*.f-local-form {*/
    /*    padding: 10px 0;*/
    /*}*/

    .f-local-option-item {
        padding: 3px;
    }

    .f-tab {
        font-weight: bold;
    }
</style>
