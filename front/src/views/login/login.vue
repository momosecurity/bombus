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

    <div class="login-container" :style="bgGroundDiv">
    <div id="canvascontainer" ref='can'></div>
    <Menu class="home-header" mode="horizontal" theme="dark" active-name="1">
        <div class="layout-logo">

        <Row type="flex" justify="start">
                    <Col span="12"><img class="home-logo" :src="secLogo"/></Col>
                    <Col span="12"><div class="home-logo-title">合规审计</div></Col>
        </Row>
    </div>
    </Menu>

    <Form ref="loginForm" autoComplete="on" :model="loginForm" :rules="loginRules"  class="card-box login-form">
        <Form-item prop="username">
            <Input type="text" v-model="loginForm.username" placeholder="Username" autoComplete="on">
                <Icon type="ios-person-outline" slot="prepend" ></Icon>
            </Input>
        </Form-item>
        <Form-item prop="password">
            <Input type="password" v-model="loginForm.password" placeholder="Password" @keyup.enter.native="handleLogin">
                <Icon type="ios-locked-outline" slot="prepend"></Icon>
            </Input>
        </Form-item>
        <Form-item>
            <Button type="primary" @click="handleLogin('loginForm')" long>登录</Button>
        </Form-item>
        <span :show="errorTip" style="color:red">{{tipContent}}</span>
    </Form>
    </div>
    </div>
</template>

<script>
    import { requestAPI } from '../../api'
    import secLogo from '../../images/sec-logo.png'
    import loginBg from '../../images/bg.jpg'
    export default {
        name: 'login',
        data() {
            return {
                secLogo,
                loginBg,
                bgGroundDiv: {
                    backgroundImage: 'url(' + require('../../images/bg.jpg') + ')',
                    backgroundSize: "100% 100%",
                },
                loginForm: {
                    username: '',
                    password: ''
                },
                loginRules: {
                    username: [
                        { required: true, message: '用户名不能为空', trigger: 'blur' }
                    ],
                    password: [
                        { required: true, message: '密码不能为空', trigger: 'blur' },
                    ]
                },
                loading: false,
                showDialog: false,
                errorTip: false,
                tipContent: '',
            }
      },
        methods: {
        handleLogin() {
          this.$refs.loginForm.validate(valid => {
            if (valid) {
              this.loading = true;
              let form = this.loginForm
              let postData = {...form}
              requestAPI('/api/sso/login/', {}, 'post', postData).then(resp=>{
                  let res = resp.data
                  if(res.error === 1){
                      this.tipContent = res.message
                      this.errorTip = true
                  }
                  else {
                      this.$Message.success('登录成功')
                      this.$router.push({'path': '/'})
                  }
              })
          }});
        },
      },
        created() {
            let username = sessionStorage.getItem('username')
            if(username && username.length > 0){
                this.$router.push({'path': '/'})
            }
        },
        mounted() {

        }
    }

</script>
<style scoped>
    .login-container a{color:#0078de;}
    #canvascontainer{
        position: absolute;
        top: 0px;
    }
    .layout-logo{
        float: left;
        position: relative;
        top: 10px;
        left: 10px;
    }
    .home-logo {
        height: 55px;
    }
    .home-logo-title {
        color: white;
        font-weight: bold;
        font-size: 16px;
        margin-top: -4px;
        margin-left: 20px;
        letter-spacing: 2px;
    }
    .home-logo-title::before {
        content: "·";
        color: white;
        box-sizing: border-box;
        margin-right: 15px;
    }

</style>

<style>

    .login-container {
        height: 100vh;
        background-color: #2d3a4b;}
        input:-webkit-autofill {
            -webkit-box-shadow: 0 0 0px 1000px #293444 inset !important;
            -webkit-text-fill-color: #fff !important;
        }
        input {
            background: transparent;
            border: 1px solid #2d8cf0;
            -webkit-appearance: none;
            border-radius: 3px;
            padding: 12px 5px 12px 15px;
            color: #eeeeee;
            height: 47px;
        }
        .login-form {
            position: absolute;
            left: 0;
            right: 0;
            width: 400px;
            padding: 35px 35px 15px 35px;
            margin: 120px auto;
        }

</style>