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
    <div class="layout">
        <Layout>
            <Layout>
                <Layout class="home-layout">
                    <Content class="home-content">
                        <router-view/>
                    </Content>
                </Layout>
            </Layout>
        </Layout>
    </div>
</template>


<script>
    import HomeSidebar from "./main/sidebar"
    import HomeHeader from "./main/header"
    import HomeFooter from "./main/footer"
    import HomeBreadcrumb from "./main/breadcrumb"
    import Watermark from '../libs/watermark'
    export default {
        name: 'HomeIndex2',
        components: {
            HomeSidebar,
            HomeHeader,
            HomeFooter,
            HomeBreadcrumb
        },
        mounted: function () {
            let username = sessionStorage.getItem('username')
            // Watermark.set(username)
        }
    }
</script>


<style scoped>
    .layout{
        background: #f5f7f9;
        position: relative;
        overflow: hidden;
        /*letter-spacing: 1px;*/
    }
    .home-content {
        /*margin-top: 15px;*/
        /*padding: 20px;*/
        min-height: 530px;
        background: #fff;
    }
    .home-layout {
        /*margin-top: 20px;*/
        /*padding: 0 14px 0 14px;*/
    }
</style>
