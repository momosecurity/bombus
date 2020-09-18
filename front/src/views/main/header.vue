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
    <Menu class="home-header" mode="horizontal" theme="dark" active-name="1">
        <div class="layout-logo">
            <router-link to="/">
                <Row type="flex" justify="start">
                    <Col span="12"><img class="home-logo" :src="secLogo"/></Col>
                    <Col span="12"><div class="home-logo-title">合规审计</div></Col>
                </Row>
            </router-link>
        </div>
        <div class="layout-nav">
            <Row type="flex" justify="end">
                <MenuItem name="5">
                    <Dropdown trigger="click">
                        <Icon type="md-contact" />
                         {{username}}
                        <Icon type="ios-arrow-down"></Icon>
                        <DropdownMenu slot="list">
                            <DropdownItem>版本 v1.0.0</DropdownItem>
                            <DropdownItem divided><span @click="logout">退出</span></DropdownItem>
                        </DropdownMenu>
                    </Dropdown>
                </MenuItem>
            </Row>
        </div>
    </Menu>
</template>

<script>
    import secLogo from '../../images/sec-logo.png'
    export default {
        name: "HomeHeader",
        data () {
            return {
                secLogo,
                username: sessionStorage.getItem('username')
            }
        },
        methods: {
            logout() {
                sessionStorage.clear()
                window.location = '/api/sso/logout/'
            }
        }
    }
</script>

<style scoped>
    .layout-logo{
        float: left;
        position: relative;
        top: 10px;
        left: 10px;
    }
    .home-logo {
        height: 55px;
    }
    .layout-nav{
        width: auto;
        margin: 0 auto;
        margin-right: 20px;
    }
    .home-header {
        height: 70px;
        background-size: cover;
        background: #000000;
        /*background: url("../../images/background-grey.jpg") no-repeat 50% 30%;*/
        box-shadow: 0 1px 3px #555;
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
    .ivu-menu-item {
        margin-top: 5px;
    }
</style>
