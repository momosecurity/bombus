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
    <div :style="bg" class="container">
        <div class="header">
            <div class="center">
                <h2 style="font-size:30px;
                           letter-spacing: 1px;
                           margin-top: 30px;
                           margin-bottom: 30px;"
                    v-if="!isPause" v-text="pageTitle"></h2>
                <h2 style="color:#FF0000;
                           font-size:30px;
                           letter-spacing: 1px;
                           margin-top: 30px;
                           margin-bottom: 30px;"
                    v-if="isPause">{{pageTitle}}(已暂停)</h2>
            </div>

            <div class="time">
                <p>
                    生成时间: {{genDate}}
                    <span style="color:#FF0000;float: right" v-if="isPause">{{pauseTip}}</span>
                </p>
            </div>

            <div class="banner">
                <Row type="flex" align="middle">
                    <Col span="1"><Avatar icon="md-bookmarks" class="report-icon" size="large"/></Col>
                    <Col>
                        <p class="banner-title">审阅规则</p>
                        请根据
                        <span v-if="currentReviewType == 'TICKET'">
                            <a href="#">《上线流程规范》</a>
                        </span>
                        <span v-else>
                            <a href="#">《账号安全管理细则》</a>
                        </span>
                        审阅制度执行情况。
                    </Col>
                </Row>
                <Row type="flex" align="middle">
                    <Col span="1"><Avatar icon="md-list-box" class="report-icon" size="large"/></Col>
                    <Col span="12">
                        <p class="banner-title">{{currentReviewTypeName}}审阅</p>
                        <div>
                            审阅人: <span style="color: #2d8cf0">{{currentAuditors}}</span>
                        </div>
                    </Col>
                    <Col>
                        <Form ref="permFormData" :model="permFormData" inline
                              style="margin-top: 30px; display:inline-block;">
                            <span style="line-height:35px;
                                         font-weight: 500;
                                         font-size: 15px;
                                         padding-right: 10px;">审阅人代授权
                                <Tooltip :content="permApplyContent" max-width="200">
                                    <span style="font-size: 5px; line-height: 5px">❓</span>
                                </Tooltip>
                            </span>

                            <FormItem prop="user">
                                <Select v-model="permFormData.user" placeholder="审阅人" filterable remote
                                        :remote-method="userSearch"
                                        :loading="userLoading"
                                >
                                    <Option v-for="(option, index) in userSearchResult" :value="option.accountid"
                                            :key="index">{{option.name}}
                                    </Option>
                                </Select>
                            </FormItem>
                            <FormItem>
                                <Button type="primary" @click="applyPerm('permFormData')">申请</Button>
                            </FormItem>
                        </Form>

                    </Col>
                </Row>
                <Row type="flex" align="middle" style="margin-top: 20px">
                    <Col span="10" push="1">
                        <Select v-model="formFilter.dept_name"
                                placeholder="部门"
                                style="float: left; width: 50%"
                                filterable :transfer="true">
                            <Option v-for="(item, idx) in deptNames" :value="item" :key="item">{{ item }}</Option>
                        </Select>
                        <Button type="primary" style="display: inline-block; margin-left: 10px"
                                @click="filterTable()">查询</Button>
                        <Button v-show="currentReviewType!=='TICKET'" type="primary" icon="md-settings" style="display: inline-block; margin-left: 8px"
                                @click="showSelectRoles">角色筛选</Button>

                    </Col>
                    <Col push="8">
                        <Switch v-model="formFilter.is_reviewed" @on-change="filterTable" />
                        <span style="line-height:35px;
                                     font-weight: bold;
                                     padding-left: 10px;"
                        >过滤已填写意见</span>
                    </Col>
                </Row>
            </div>
        </div>

        <div class="body">
            <Table border style="word-break: break-all; word-wrap: break-word" :row-class-name="rowClassName" :columns="currentTableColumn" :data="currentTableData" size="small" height="500">
                <template slot-scope="{ row, index }" slot="online_ticket">
                    <Button type="primary" size="small" @click="onlineTicket(index)" :disabled="!(row.projects && row.projects.length > 0)">详情</Button>
                </template>
                <template slot-scope="{ row, index }" slot="deploy_ticket">
                    <Button type="primary" size="small" @click="deployTicket(index)" :disabled="row.risk_deploy_count===0">详情</Button>
                </template>
                <template slot-scope="{ row, index }" slot="log_detail">
                    <Button type="primary" size="small" @click="logDetail(index)"
                            :disabled="!row.has_logs"
                    >详情</Button>
                </template>
                <template slot-scope="{ row, index }" slot="review_host_list">
                    <Button type="primary" size="small" @click="showAuditServerForm(index)">详情</Button>
                </template>
            </Table>
        </div>

        <div class="footer">
            <Row style="padding: 3px">
                <Avatar icon="ios-create" class="report-icon" size="large"/>
                <span class="banner-title" style="margin-left: 5px; font-weight: bold">审阅意见</span>
                <span style="float: right">
                    <span style="font-weight: bold">总计</span>:
                    <span style="font-weight: bold">{{currentUserCount}}</span> 个用户
                </span>
            </Row>
            <Row>
                <Col span="14" style="padding-left: 53px; padding-top: 10px;">
                    <h4 style="color: dodgerblue">针对个人审阅意见:</h4>
                    <List v-if="singleReviewList && singleReviewList.length > 0" size="small"
                          style="max-height: 300px; overflow-y: scroll">
                        <ListItem v-for="item in singleReviewList">
                            <span>{{item.user_render}}针对{{item.single_desc}}<span @click="routeDetail(item)" :class="{'clickable': getClick(item.review_type)}">{{showSingleId(item)}}</span>的审阅意见: {{item.content}}({{item.created_time_render}})</span>
                        </ListItem>
                    </List>
                    <span v-else>{{emptyReviewTip}}</span>

                    <br/><br/>

                    <h4 style="color: dodgerblue">整体审阅意见:</h4>
                    <List style="max-height: 300px; overflow-y: scroll">
                        <ListItem v-for="item in wholeReivewList">
                            {{fmtReviewComment(item)}}
                        </ListItem>
                    </List>
                </Col>
                <Col span="9" offset="1">
                    <p>整体审阅意见:
                        <span style="font-weight: bold; color: red" v-if="currentCanReview">
                            为确认全部内容已审阅, 请补充整体审阅意见。
                        </span>
                    </p>
                    <Input type="textarea" v-model="wholeReviewContent" :rows="6" :disabled="!currentCanReview"></Input>
                    <Button style="float: right; margin-top: 5px"
                            type="primary"
                            :disabled="!Boolean(wholeReviewContent.length)"
                            @click="saveReview">提交
                    </Button>
                </Col>
            </Row>

            <Row style="margin-top: 50px">
                <Avatar icon="md-text" class="report-icon" size="large"/>
                <span class="banner-title" style="margin-left: 5px; font-weight: bold">留言板</span>
                <div style="padding-left: 53px; padding-top: 10px; max-height: 300px; overflow-y: scroll">
                    <List>
                        <ListItem v-for="item in messageBoardList">
                            {{fmtMessageContent(item)}}
                        </ListItem>
                    </List>
                    <Button :disabled="!Boolean(messageContent.length)"
                            type="primary"
                            style="display: inline-block; margin-left: 5px"
                            @click="saveMessage">提交
                    </Button>
                    <Input v-model="messageContent" style="float: left; width: 40%; margin-bottom: 100px"></Input>
                </div>
            </Row>

        </div>
        <div id="nav">
            <Card title="快速导航" style="width:170px;">
                <CellGroup @on-click="routeBack">
                    <Cell title="返回" style="font-weight: bold;"/>
                </CellGroup>
                <CellGroup v-for="item in indexList" v-if="showTypes.indexOf(item.key)!==-1" @on-click="checkOutType(item.key)">
                    <Cell :title="item.name"
                          :name="item.key"
                          :class="{'reviewed': reviewedTypes.indexOf(item.key)!==-1}"
                          :selected="item.key===currentReviewType"/>
                </CellGroup>
                <CellGroup>
                    <Cell :title="getProgress()"/>
                </CellGroup>
            </Card>
        </div>
        <Modal v-model="reviewFormModal" title="审阅" @on-ok="commitRecordReview">
            <Input type="textarea" v-model="recordReviewContent"></Input>
        </Modal>

        <Modal v-model="serverContentModal" title="资产详情">
            <div>
                <h4>统计:</h4>
                <pre>{{ServerStaticCount}}</pre>
                <Button type="default" size="small" @click="copyText">复制</Button>
            </div>
            <br>
            <div>
                <h4>列表:</h4>
                <pre>{{ServerPermDetail}}</pre>
            </div>
        </Modal>

        <Modal v-model="showRoleSelectModal" title="角色/权限" @on-ok="filterTable" width="400">
            <div style="max-height: 400px; overflow-y: scroll">
            <Checkbox
            :indeterminate="indeterminate"
            :value="checkAll"
            @click.prevent.native="handleCheckAll">全选</Checkbox>
            <CheckboxGroup v-model="SelectedRoles" @on-change="checkAllRoleChange">
                <div v-for="k in allRoles">
                <Checkbox :label='k' :key="k" :class="{'selectBox': SelectedRoles.indexOf(k) !== -1}"></Checkbox>
                </div>
            </CheckboxGroup>
            </div>
        </Modal>
    </div>
</template>

<script>
    import {requestAPI} from "../../api";

    export default {
        name: "ReviewPage",
        data() {
            return {
                bg: {
                    backgroundImage: "url(" + require("../../images/background.png") + ")",
                    backgroundRepeat: "repeat-y",
                    backgroundSize: "cover",
                    paddingLeft: "30px",
                    paddingRight: "30px",
                    paddingBottom: "30px",
                    // marginTop: "5px",
                    // opacity: 0.7
                },
                pageTitle: '审阅报告',
                currentReviewType: '',
                currentReviewTypeName: '应用系统',
                currentAuditors: '',
                deptNames: [],
                currentTableColumn: [],
                currentTableData: [],
                currentUserCount: 0,
                emptyReviewTip: '数据由上方表格填写内容同步，若您针对具体个人没有审阅意见，仅填写整体审阅意见即可。',
                reviewStatus: {},
                reviewedTypes: [],
                unReviewedTypes: [],
                emptyContent: '未匹配到记录（或数据未接入），如有疑问请联系安全组',
                genDate: '',
                auditSys: '',
                auditSysId: '',
                taskId: '5e4e2a88c554e817dc661148',
                pauseTip: '任务已暂停, 详请咨询合规同事',
                // 审阅意见 & 留言板数据
                singleReviewList: [],
                wholeReivewList: [],
                messageBoardList: [],
                // 单记录审阅参数
                curEditReviewRecord: null,
                curEditServerKind: null,
                curEditReviewType: null,
                recordReviewModal: false,
                recordReviewContent: '',
                reviewIndex: -1,
                reviewFormModal: false,
                // 整体审阅
                wholeReviewContent: '',
                currentCanReview: true,
                // 留言板
                messageContent: '',

                // 文案部分
                riskDeployerContent: '如果异常部署人为空，则该用户在审阅周期内不存在异常部署。',
                projectContent: '如果负责项目为空，则该用户仅负责部署，不参与上线审批。',
                permApplyContent: '若需增加人员协同审阅，可进行代授权，后续审阅均会通知该审阅人。',
                logDescContent: '  1）查看日志中的变更类命令/动作是否经过合理授权。\n' +
                    '  2）若日志中包含导出敏感数据的命令/动作，应审计用户行为是否合理。\n' +
                    '  3）应用日志格式为系统开发同事自主定义，安全组接入时根据变更类关键字筛选出结果，需审阅人根据日志自行甄别操作内容是否存在风险。若存在可读性差的问题，建议与技术负责人沟通提升日志可读性。\n' +
                    '  4）操作日志无法点击查看详情，指该审阅周期内没有发生写操作，数据为空。',
                riskReasonContent: '' +
                    '1)职责分离：同一系统，除数据库管理员可根据工作需要兼具操作系统管理员权限外，同一员工不得同时兼任开发、应用系统管理员、操作系统管理员、数据库管理员中的两种（含） 以上角色；\n' +
                    '2)具有管理职责的角色所含人员是否经过合理授权；\n' +
                    '3)权限包含的人员是否满足岗位职责要求，是否存在转岗、离职等情况；\n' +
                    '4)默认生产环境操作系统仅运维工程师可具备永久 ROOT 权限; \n' +
                    '5)可以接触到公司敏感数据、用户数据的权限，所授权员工是否合理；\n' +
                    '6)可以接触到公司敏感数据、用户数据的权限，权限分配是否符合最小授权原则。',
                reviewColumnContent: '针对具体用户或日志的审阅意见，此内容为选填。',
                riskDeployContent: '1）未授权变更：指没有找到对应的上线单，即没有经过上线变更审批流程，执行了部署操作。\n' +
                    '2）工单审批异常：指上线单的流程状态为已撤销，或负责人未审批就提前部署。\n' +
                    '3）操作不规范：已完成部署操作，但申请人未结束上线单流程。\n' +
                    '4）发布系统工单关闭已审批授权：指项目已通过负责人和SRE的评估，变更操作不影响审计范围内系统相关服务，在特定期限内关闭了上线单与部署单关联的验证功能，可以不通过上线单的审批就进行部署操作。',
                serverContentModal: false,
                ServerStaticCount: {},
                ServerPermDetail: {},
                showDbPerm: true,
                serverKind: [],
                permServerKind: '',
                permFormData: {},
                permFormRule: {
                    user: [
                        { required: true, message: '待授权审阅人不能为空', trigger: 'blur' }
                    ],
                    server_kind: [
                        { required: true, message: '审阅权限类型不能为空', trigger: 'blur' },
                    ]
                },
                userLoading: false,
                userSearchResult: [],
                formFilter: {},
                reviewTypeName: {
                    'APP': '应用系统',
                    'SYS_DB': '操作系统/数据库',
                    'TICKET': '工单'
                },
                indexList: [
                    {
                        key: 'APP',
                        name: '应用系统'
                    },
                    {
                        key: 'SYS_DB',
                        name: '操作系统/数据库'
                    },
                    {
                        key: 'TICKET',
                        name: '工单'
                    }
                ],
                showTypes: [],
                typeUrlMap: {
                    'APP': '/api/audit/app_user/',
                    'SYS_DB': '/api/audit/sys_db/',
                    'TICKET': '/api/audit/ticket_list/'
                },
                messageForm: {
                    content: '',
                },
                reviewForm: {
                    content: '',
                },
                isPause: false,
                showKind: [],
                showRoleSelectModal: false,
                SelectedRoles: null,
                allRoles: [],
                indeterminate: false,
                checkAll: true,

            }
        },
        methods: {
            // 加载基础信息
            loadBaseInfo(){
                this.taskId = this.$route.params.id
                let initReviewType = this.$route.params.review_type
                const url = `/api/audit/task/${this.taskId}/`
                requestAPI(url, {}, 'get').then(resp => {
                    this.pageTitle = resp.data.base_info.name
                    this.genDate = resp.data.base_info.created_time
                    this.auditSys = resp.data.base_info.audit_sys_name
                    this.auditSysId = resp.data.base_info.audit_sys_id
                    this.isPause = resp.data.base_info.is_pause
                    this.pauseTip = resp.data.pause_tip
                    this.auditors = resp.data.auditors
                    this.serverKind = resp.data.server_kind
                    this.reviewStatus = resp.data.review_status
                    this.showTypes = resp.data.visible_scope
                    this.fmtReviewedType()
                    if(initReviewType){
                        this.checkOutType(initReviewType)
                    }else {
                        this.autoCheckoutType()
                    }
                })
            },
            // 获取格式化的类
            fmtReviewedType(){
                let reviewedType = []
                let unReviewedType = []
                for(const k in this.reviewStatus){
                    if(this.reviewStatus[k]){
                        reviewedType.push(k)
                    }else{
                        unReviewedType.push(k)
                    }
                }
                this.reviewedTypes = reviewedType
                this.unReviewedTypes = unReviewedType
            },
            // 加载当前数据
            autoCheckoutType(){
                let loadReviewType = this.showTypes[0]
                for(const reviewType in this.reviewStatus){
                    if(!this.reviewStatus[reviewType] && this.showTypes.indexOf(reviewType) !== -1){
                        loadReviewType = reviewType
                        break
                    }
                }
                this.currentReviewType = loadReviewType
                this.loadCurrentData()
            },
            loadCurrentData(){
                this.currentReviewTypeName = this.reviewTypeName[this.currentReviewType]
                this.currentAuditors = this.auditors[this.currentReviewType]
                this.loadTypeData()
                this.loadReviewData()
                this.loadMessageBoardData()
            },
            // 加载审阅数据
            loadReviewData(){
                let url = '/api/audit/new_review_comment/'
                let params = {
                    task: this.taskId,
                    review_type: this.currentReviewType,
                    page_size: 10000
                }
                requestAPI(url, params).then(resp => {
                    this.singleReviewList = resp.data.single_reviews
                    this.wholeReivewList = resp.data.whole_reviews
                    this.currentCanReview = resp.data.can_review
                })
            },
            // 加载留言板数据
            loadMessageBoardData(){
                let url = '/api/audit/new_message_board/'
                let params = {
                    task: this.taskId,
                    review_type: this.currentReviewType,
                    page_size: 10000,
                }
                requestAPI(url, params).then(resp => {
                    this.messageBoardList = resp.data.results
                })
            },
            fmtMessageContent(item){
                let user = item.user_render
                let timeStr = item.created_time_render

                let content = item.content
                let showContent = user + ':'
                showContent += content
                showContent += '  (' + timeStr + ')'
                return showContent
            },
            fmtReviewComment(item){
                let reviewer = item.user_render
                let timeStr = item.created_time_render
                let singleDesc = item.single_desc
                let content = item.content
                let showContent = reviewer
                if(singleDesc && singleDesc.length > 0){
                    showContent += '针对' + singleDesc
                }
                showContent += '的审阅意见: '
                showContent += content
                showContent += '  (' + timeStr + ')'
                return showContent
            },
            routeDetail(item){
                let singleId = item.single_id
                if(item.review_type === 'ONLINE_TICKET'){
                    this.routeOnlineTicket(singleId)
                }else if(item.review_type === 'DEPLOY_TICKET'){
                    this.routeDeployTicket(singleId)
                }else if(item.review_type === 'SYS_DB_LOG'){
                    this.routeSysDbLog(singleId)
                }else if(item.review_type === 'APP_LOG'){
                    this.routeAppLog(singleId)
                }
            },
            routeOnlineTicket(ticketId){
                let route = this.$router.resolve({
                    path: '/task/onlineticket',
                    query: {
                        task_id: this.taskId,
                        ticket_id: ticketId,
                    }
                })
                window.open(route.href, '_blank')
            },
            routeDeployTicket(singleId){
                let route = this.$router.resolve({
                    path: '/task/deployticket',
                    query: {
                        task_id: this.taskId,
                        commit_id: singleId,
                    }
                })
                window.open(route.href, '_blank')
            },
            routeSysDbLog(singleId){
                let route = this.$router.resolve({
                    path: '/task/sysdblog',
                    query: {
                        task_id: this.taskId,
                        log_id: singleId,
                    }
                })
                window.open(route.href, '_blank')
            },
            routeAppLog(singleId){
                let route = this.$router.resolve({
                    path: '/task/applog',
                    query: {
                        task_id: this.taskId,
                        log_id: singleId,
                    }
                })
                window.open(route.href, '_blank')
            },
            //
            showSingleId(item){
                if(this.getClick(item.review_type)){
                    let singleId = item.single_id
                    if(singleId.length > 10) {
                        singleId = singleId.slice(0, 10)
                    }
                    return `(${singleId})`
                }else{
                    return ''
                }
            },
            // 判定是否可以点击
            getClick(review_type){
                if(review_type === 'APP_LOG' || review_type ==='ONLINE_TICKET' || review_type === 'DEPLOY_TICKET' || review_type === 'SYS_DB_LOG'){
                    return true
                }
                return false
            },
            // 单人审阅的跳转链接
            fmtReviewLink(item){
                let linkContent = ''
                if(item.review_type === 'ONLINE_TICKET'){
                    let ticket_id = item.single_id
                    linkContent = `<span @click="routeOnlineTicket(` + ticket_id + `)">(${ticket_id})</span>`
                }else if(item.review_type === "DEPLOY_TICKET"){
                    let commit_id = item.single_id
                    linkContent = `<span @click="routeDeployTicket(` + commit_id + `)">(${commit_id})</span>`
                }else if(item.review_type === "APP_LOG" || item.review_type === 'SYS_DB_LOG'){
                    let log_id = item.single_id
                    linkContent = `<span @click="routeDeployTicket(` + log_id + `)">(${log_id})</span>`
                }
                let result = item.single_desc + linkContent
                // console.log(result)
                return result
            },
            getTicketColumns(){
                return[
                    {
                        title: '#',
                        type: 'index',
                        width: 75
                    },
                    {
                        key: 'email',
                        title: '用户标识',
                    },
                    {
                        key: 'name',
                        title: '用户',
                    },
                    {
                        key: 'dept_name',
                        title: '所属部门',
                    },
                    {
                        key: 'projects',
                        title: '负责项目',
                        renderHeader: (h, params) => {
                            return h('div', [
                                        h('span', {
                                            domProps: {
                                                innerHTML: '负责项目'
                                            }
                                        }),
                                        h('Tooltip', {
                                            props: {
                                                size: 'small',
                                                placement: 'bottom',
                                                transfer: true,
                                            }
                                        }, [
                                            '❓',
                                            h('div', {
                                                slot: 'content',
                                                style: {
                                                    whiteSpace: 'pre-wrap',
                                                    wordBreak: 'break-all'
                                                },
                                            }, this.projectContent)
                                        ])
                                    ])
                        }
                    },
                    {
                        title: '上线单详情',
                        slot: 'online_ticket',
                    },
                    {
                        key: 'deployers',
                        title: '异常部署人',
                        renderHeader: (h, params) => {
                            return h('div', [
                                        h('span', {
                                            domProps: {
                                                innerHTML: '异常部署人'
                                            }
                                        }),
                                        h('Tooltip', {
                                            props: {
                                                size: 'small',
                                                placement: 'bottom',
                                                transfer: true,
                                            }
                                        }, [
                                            '❓',
                                            h('div', {
                                                slot: 'content',
                                                style: {
                                                    whiteSpace: 'pre-wrap',
                                                    wordBreak: 'break-all'
                                                },
                                            }, this.riskDeployerContent)
                                        ])
                                    ])
                        }
                    },
                    {
                        key: 'risk_deploy_count',
                        title: '异常部署次数',
                    },
                    {
                        title: '异常部署详情',
                        slot: 'deploy_ticket',
                        renderHeader: (h, params) => {
                            return h('div', [
                                        h('span', {
                                            domProps: {
                                                innerHTML: '异常部署详情'
                                            }
                                        }),
                                        h('Tooltip', {
                                            props: {
                                                size: 'small',
                                                placement: 'bottom',
                                                transfer: true,
                                            }
                                        }, [
                                            '❓',
                                            h('div', {
                                                slot: 'content',
                                                style: {
                                                    whiteSpace: 'pre-wrap',
                                                    wordBreak: 'break-all'
                                                },
                                            }, this.riskDeployContent)
                                        ])
                                    ])
                        }
                    },
                    {
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
                        },
                        renderHeader: (h, params) => {
                            return h('div', [
                                        h('span', {
                                            domProps: {
                                                innerHTML: '审阅意见'
                                            }
                                        }),
                                        h('Tooltip', {
                                            props: {
                                                size: 'small',
                                                placement: 'bottom',
                                                transfer: true,
                                            }
                                        }, [
                                            '❓',
                                            h('div', {
                                                slot: 'content',
                                                style: {
                                                    whiteSpace: 'pre-wrap',
                                                    wordBreak: 'break-all'
                                                },
                                            }, this.reviewColumnContent)
                                        ])
                                    ])
                        }
                    }
                ]
            },
            getSysDbColumn(){
                return [
                    {
                        title: '#',
                        type: 'index',
                        width: 70
                    },
                    {
                        key: 'origin_name',
                        title: '用户标识'
                    }, {
                        key: 'name',
                        title: '用户'
                    }, {
                        key: 'dept_name',
                        title: '所属部门'
                    }, {
                        key: 'roles',
                        title: '角色/权限'
                    }, {
                        slot: 'review_host_list',
                        title: "资产信息",
                        align: "center",
                        width: 100
                    },
                    {
                        key: 'risk_reason',
                        title: '异常原因',
                        renderHeader: (h, params) => {
                            return h('div', [
                                        h('span', {
                                            domProps: {
                                                innerHTML: '异常原因'
                                            }
                                        }),
                                        h('Tooltip', {
                                            props: {
                                                // content: this.riskReasonContent,
                                                trigger: 'hover',
                                                size: 'small',
                                                placement: 'bottom',
                                                transfer: true,
                                            }
                                        }, [
                                            '❓',
                                            h('div', {
                                                slot: 'content',
                                                style: {
                                                    whiteSpace: 'pre-wrap',
                                                    wordBreak: 'break-all'
                                                },
                                            }, this.riskReasonContent)
                                        ])

                                    ])
                        }
                    }, {
                        slot: 'log_detail',
                        title: '操作日志',
                        renderHeader: (h, params) => {
                            return h('div', [
                                        h('span', {
                                            domProps: {
                                                innerHTML: '操作日志'
                                            }
                                        }),
                                        h('Tooltip', {
                                            props: {
                                                size: 'small',
                                                placement: 'bottom',
                                                transfer: true,
                                            }
                                        }, [
                                            '❓',
                                            h('div', {
                                                slot: 'content',
                                                style: {
                                                    whiteSpace: 'pre-wrap',
                                                    wordBreak: 'break-all'
                                                },
                                            }, this.logDescContent)
                                        ])

                                    ])
                        }
                    }, {
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
                        },
                        renderHeader: (h, params) => {
                            return h('div', [
                                        h('span', {
                                            domProps: {
                                                innerHTML: '审阅意见'
                                            }
                                        }),
                                        h('Tooltip', {
                                            props: {
                                                size: 'small',
                                                placement: 'bottom',
                                                transfer: true,
                                            }
                                        }, [
                                            '❓',
                                            h('div', {
                                                slot: 'content',
                                                style: {
                                                    whiteSpace: 'pre-wrap',
                                                    wordBreak: 'break-all'
                                                },
                                            }, this.reviewColumnContent)
                                        ])
                                    ])
                        }
                    },
                ]
            },
            getAppColumn(){
                return [
                    {
                        title: '#',
                        type: 'index',
                        width: 70
                    },
                    {
                        key: 'origin_name',
                        title: '用户标识'
                    }, {
                        key: 'name',
                        title: '用户'
                    }, {
                        key: 'dept_name',
                        title: '所属部门'
                    }, {
                        key: 'roles',
                        title: '角色/权限'
                    },
                    {
                        key: 'risk_reason',
                        title: '异常原因',
                        renderHeader: (h, params) => {
                            return h('div', [
                                        h('span', {
                                            domProps: {
                                                innerHTML: '异常原因'
                                            }
                                        }),
                                        h('Tooltip', {
                                            props: {
                                                // content: this.riskReasonContent,
                                                trigger: 'hover',
                                                size: 'small',
                                                placement: 'bottom',
                                                transfer: true,
                                            }
                                        }, [
                                            '❓',
                                            h('div', {
                                                slot: 'content',
                                                style: {
                                                    whiteSpace: 'pre-wrap',
                                                    wordBreak: 'break-all'
                                                },
                                            }, this.riskReasonContent)
                                        ])

                                    ])
                        }
                    }, {
                        slot: 'log_detail',
                        title: '操作日志',
                        renderHeader: (h, params) => {
                            return h('div', [
                                        h('span', {
                                            domProps: {
                                                innerHTML: '操作日志'
                                            }
                                        }),
                                        h('Tooltip', {
                                            props: {
                                                size: 'small',
                                                placement: 'bottom',
                                                transfer: true,
                                            }
                                        }, [
                                            '❓',
                                            h('div', {
                                                slot: 'content',
                                                style: {
                                                    whiteSpace: 'pre-wrap',
                                                    wordBreak: 'break-all'
                                                },
                                            }, this.logDescContent)
                                        ])

                                    ])
                        }
                    }, {
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
                        },
                        renderHeader: (h, params) => {
                            return h('div', [
                                        h('span', {
                                            domProps: {
                                                innerHTML: '审阅意见'
                                            }
                                        }),
                                        h('Tooltip', {
                                            props: {
                                                size: 'small',
                                                placement: 'bottom',
                                                transfer: true,
                                            }
                                        }, [
                                            '❓',
                                            h('div', {
                                                slot: 'content',
                                                style: {
                                                    whiteSpace: 'pre-wrap',
                                                    wordBreak: 'break-all'
                                                },
                                            }, this.reviewColumnContent)
                                        ])
                                    ])
                        }
                    },
                ]
            },
            showSelectRoles(){
                this.showRoleSelectModal = true
            },
            filterTable(){
                this.loadTypeData()
            },
            // 加载类型数据
            loadTypeData(){
                let url = this.typeUrlMap[this.currentReviewType]
                let role = ''
                if(this.SelectedRoles && this.SelectedRoles.length !== this.allRoles.length){
                    role = this.SelectedRoles.join(',')
                }
                let params = {
                    task_id: this.taskId,
                    role: role,
                    ...this.formFilter
                }
                requestAPI(url, params).then(resp => {
                    this.currentTableColumn = this.getTypeColumn()
                    this.currentTableData = resp.data.results
                    this.currentUserCount = resp.data.user_count
                    this.deptNames = resp.data.dept_names
                    this.allRoles = resp.data.all_roles
                    if(this.SelectedRoles == null){
                        this.SelectedRoles = this.allRoles
                    }
                })
            },
            getTypeColumn() {
                if(this.currentReviewType === 'TICKET'){
                    return this.getTicketColumns()
                }else if(this.currentReviewType === 'APP'){
                    return this.getAppColumn()
                }else{
                    return this.getSysDbColumn()
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
            // 上线单列表
            onlineTicket(index){
                this.$router.push({
                    path: '/task/onlineticket',
                    query: {
                        task_id: this.taskId,
                        user: this.currentTableData[index].email,
                    }
                })
            },
            deployTicket(index){
                this.$router.push({
                    path: '/task/deployticket',
                    query: {
                        task_id: this.taskId,
                        user: this.currentTableData[index].email,
                        role: this.currentTableData[index].role,
                        name: this.currentTableData[index].name,
                        // name: this.tableData[index].id,
                    }
                })
            },
            editRecordReview(index) {
                this.reviewIndex = index
                this.reviewFormModal = true
            },
            // 提交留言
            saveMessage(){
                let postData = {
                    task: this.taskId,
                    review_type: this.currentReviewType,
                    content: this.messageContent,
                }
                requestAPI('/api/audit/new_message_board/', {}, 'post', postData).then(resp => {
                    this.$Message.success('保存成功')
                    this.messageContent = ''
                    this.loadMessageBoardData()
                })
            },
            // 提交整体审阅意见
            saveReview(){
                let postData = {
                    task: this.taskId,
                    review_type: this.currentReviewType,
                    content: this.wholeReviewContent,
                }
                requestAPI('/api/audit/new_review_comment/', {}, 'post', postData).then(resp => {
                    this.$Message.success('保存成功')
                    this.wholeReviewContent = ''
                    this.loadBaseInfo()
                })
            },
            // 提交单记录审阅意见
            commitRecordReview(){
                let recordInfo = this.pickRecordInfo()
                let postData = {
                    task: this.taskId,
                    review_type: this.currentReviewType,
                    content: this.recordReviewContent,
                    ...recordInfo
                }
                requestAPI('/api/audit/new_review_comment/', {}, 'post', postData).then(resp => {
                    this.$Message.success('保存成功')
                    this.recordReviewContent = ''
                    this.loadTypeData()
                    this.loadReviewData()
                })
            },
            // 抽取审阅信息
            pickRecordInfo(){
                let single_id = ''
                let curReviewData = this.currentTableData[this.reviewIndex]
                if(this.currentReviewType === 'TICKET'){
                    single_id = curReviewData.email
                }else{
                    single_id = curReviewData.origin_name
                }
                let user = curReviewData.name
                if(!user || user.length === 0){
                    user = single_id
                }
                let single_desc = '用户【' + user + '】'
                return {
                    'single_id': single_id,
                    'single_desc': single_desc
                }
            },
            // 查看日志详情
            logDetail(index){
                let pathName = ''
                if(this.currentReviewType === 'APP'){
                    pathName = '/task/applog'
                }
                else{
                    pathName = '/task/sysdblog'
                }
                this.$router.push({
                    path: pathName,
                    query: {
                        task_id: this.taskId,
                        user: this.currentTableData[index].origin_name,
                        name: this.currentTableData[index].name,
                    }
                })
            },
            // 切换审阅类型
            checkOutType(targetType){
                if(this.showTypes.indexOf(targetType) !== -1){
                    this.SelectedRoles = null
                    this.checkAll = true
                    this.indeterminate = false
                    this.currentReviewType = targetType
                    this.loadCurrentData()
                }else{
                    this.autoCheckoutType()
                }
            },
            // 整体审阅进度
            getProgress(){
                let reviewed = 0
                let unreviewed = 0
                if(!this.showTypes){
                    return '计算中'
                }
                for(const k in this.reviewStatus){
                    if(this.showTypes.indexOf(k) != -1){
                        if (this.reviewStatus[k]) {
                            reviewed += 1
                        } else {
                            unreviewed += 1
                        }
                    }
                }
                let total = reviewed + unreviewed
                let progress = '整体进度: '
                if(total !== 0){
                    progress += Math.trunc((reviewed/total * 100)) + '%'
                }else{
                    progress += '100%'
                }

                return progress
            },
            applyPerm(name) {
                let form = this.permFormData
                let postData = {
                    ...form,
                    server_kind: this.currentReviewType,
                    task_id: this.taskId
                }
                requestAPI('/api/audit/perm_apply/', {}, 'post', postData).then(resp => {
                    this.$Message.success('申请成功, 已通知合规人员')
                })

            },
            rowClassName (row, index) {
                if(row.risk_reason && row.risk_reason.length > 0){
                    if(row.risk_level === 1){
                        return 'demo-table-error1-row';
                    }else if(row.risk_level === 2){
                        return 'demo-table-error2-row';
                    }else if(row.risk_level === 3 || row.risk_level === 4){
                        return 'demo-table-error3-row';
                    }
                }
                return '';
            },
            // 返回任务列表页面
            routeBack(){
                this.$router.push({
                    name: 'tasklist',
                })
            },
            // 查看主机列表
            showAuditServerForm(index){
                let user = this.currentTableData[index].origin_name
                let params = {}
                params.user = user
                params.server_kind = 'SYS_DB'
                params.task_id = this.taskId
                requestAPI('/api/audit/user_servers/', params).then(resp=>{
                    let result = resp.data.results
                    this.ServerStaticCount = this.fmtServerCount(resp.data.statis_result)
                    this.ServerPermDetail = this.fmtServerPerm(result)
                    this.showDbPerm = resp.data.has_search_perm
                    this.serverContentModal = true
                })
            },
            fmtServerCount(serverCounts){
                let fmtContentList = []
                for(const perm in serverCounts){
                    let serverCount = serverCounts[perm]
                    let joinContent = '具备' + perm + '权限的主机数量: ' + serverCount
                    fmtContentList.push(joinContent)
                }
                return fmtContentList.join('\n')
            },
            fmtServerPerm(serverPerms){
                let fmtContentList = []
                for(const server in serverPerms){
                    let permContent = serverPerms[server]
                    let joinContent = server + ' (' + permContent + ')'
                    fmtContentList.push(joinContent)
                }
                return fmtContentList.join('\n')
            },
            concatKindType(serverKind, reviewType){
                let lowerCaseServerKind = ''
                if(serverKind==='APP'){
                    lowerCaseServerKind = 'app'
                }
                else if(serverKind==="SA"){
                    lowerCaseServerKind = 'sys'
                }
                else if(serverKind==="DBA"){
                    lowerCaseServerKind = 'db'
                }else if(serverKind==='TICKET'){
                    lowerCaseServerKind = 'ticket'
                }
                return lowerCaseServerKind + '_' + reviewType
            },
            copyText() {
                var vm = this
                this.$copyText(this.ServerPermDetail).then(function (e) {
                    vm.$Message.success('复制成功')
                }, function (e) {
                    vm.$Message.error('复制失败, 请手动操作')
                })
            },
            handleCheckAll() {
                if (this.indeterminate) {
                    this.checkAll = false;
                } else {
                    this.checkAll = !this.checkAll;
                }
                this.indeterminate = false;

                if (this.checkAll) {
                    this.SelectedRoles = this.allRoles;
                } else {
                    this.SelectedRoles = [];
                }
            },
            checkAllRoleChange (data) {
                if (data.length === this.allRoles.length) {
                    this.indeterminate = false;
                    this.checkAll = true;
                } else if (data.length > 0) {
                    this.indeterminate = true;
                    this.checkAll = false;
                } else {
                    this.indeterminate = false;
                    this.checkAll = false;
                }
            }
        },
        created() {
            this.loadBaseInfo();
        },
    }
</script>

<style scoped>
    .container {
        min-height:100%;
        margin:0;
        padding:0;
        position:relative;
    }

    .body {
        margin-top: 30px;
        flex: 1 1 auto;
        background-color: blue;
        min-height: 500px;
    }
    .header{
        /*height: 230px;*/
        flex: 0 0 auto;
        margin: 0px 5px;
      /*opacity: 0.1;*/
    }
    .footer {
        margin-top: 30px;
        bottom: 0;
        padding-bottom: 10px;
        /*flex: 0 0 auto;*/
        /*margin: 5px;*/
        /*opacity: 0.5;*/
    }
    .center {
        padding-top: 10px;
        text-align: center;
    }

    .banner-title{
        font-weight:bold;
        font-size: 15px;
    }

    .banner{
        padding-left: 5px;
    }

    .reviewed{
        background-color: #DDDDDD;
    }

    .time{
        padding-left: 5px;
        margin-bottom: 25px;
        font-weight: 800;
    }

    #nav {
        position: fixed;
        top: 1em;
        right: 1em;
        opacity: 0.8;
    }

    .clickable {
        color:blue;
        cursor: pointer;  /*鼠标悬停变小手*/
        text-decoration:underline;
    }

    .right {
        text-align: right;
    }
    .f-dashboard-item {
        padding-right: 30px;
    }
    .empty-content{
        text-align: center;
        display: block;
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

    .goto-span {
        color:blue;
        cursor: pointer;  /*鼠标悬停变小手*/
        text-decoration:underline;
    }

    .textarea-inherit {
        width: 60%;
        height: 70px;
        overflow: auto;
        word-break: break-all; //解决兼容问题
    }
    .textarea-message {
        width: 80%;
        overflow: auto;
        word-break: break-all; //解决兼容问题
    }

    .report-icon {
        background: cornflowerblue;
    }

    .selectBox {
        color: blue;

    }

    .help-icon {
        /*background: white;*/
        size: 5px;
        color: red;
    }

</style>

<style>
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


    .ivu-cell-title {
        font-size: 12px;
    }
    .ivu-table .demo-table-info-row td{
        background-color: #2db7f5;
        color: #fff;
    }
    .ivu-table .demo-table-error1-row td{
        background-color: #ff4e00;
        color: #fff;
    }

    .ivu-table .demo-table-error2-row td{
        background-color: #ff9106;
        color: #fff;
    }

    .ivu-table .demo-table-error3-row td{
        background-color: #a4aacc;
        color: #fff;
    }

    body {
        height: 100%;
        color: black !important;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
        font-family: "Avenir", Tahoma, Arial, PingFang SC, Lantinghei SC, Microsoft Yahei, Hiragino Sans GB, Microsoft Sans Serif, WenQuanYi Micro Hei, Helvetica, sans-serif !important;
    }

    body::-webkit-scrollbar {
        width: 0;
    }
</style>
