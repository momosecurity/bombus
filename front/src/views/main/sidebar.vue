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
    <div class="home-sidebar">

        <Menu :theme="theme" width="auto" :open-names="[openNames]" accordion :active-name="path">
            <div v-for="(route, index) in routes" :key="index">

                <Submenu v-if="route.children" :name="route.path"
                         v-show="menuShow(route)">
                    <template slot="title">
                        <Icon :type="route.meta.icon" />
                        <span style="font-weight: bold;">{{ route.meta.title }}</span>
                    </template>
                    <MenuItem v-for="child in route.children"
                              v-show="menuShow(child)"
                              :name="route.path + '/' + child.path"
                              :to="route.path + '/' + child.path"
                              :key="child.meta.title"
                              class="f-second-title">
                        {{ child.meta.title }}
                    </MenuItem>
                </Submenu>

                <MenuItem v-else :name="route.path" :to="route.path" style="font-weight: bold;">
                    <Icon :type="route.meta.icon" />
                    {{ route.meta.title }}
                </MenuItem>
            </div>
        </Menu>
    </div>
</template>

<script>
    export default {
        name: 'HomeSidebar',
        data () {
            return {
                theme: 'light',
                path: this.$route.path,
                openNames: this.$route.matched[0].path,
                perms: sessionStorage.getItem('perms').split(','),
                isSuper: sessionStorage.getItem('is_super') === 'true'
            }
        },
        methods: {
            menuShow(route){
                if(route.meta.hideInMenu){
                    return false
                }
                if(!route.meta.perm || this.isSuper){
                    return true
                }
                if(this.perms.includes(route.meta.perm)){
                    return true
                }
                return false
            }
        },
        computed: {
            routes: function () {
                const routes = []
                for (const i in this.$router.options.routes) {
                    if (!this.$router.options.routes.hasOwnProperty(i)){
                        continue
                    }
                    const route = this.$router.options.routes[i]
                    if(route.hasOwnProperty('meta')) {
                        routes.push(route);
                    }
                }
                return routes;
            }
        }
    }
</script>

<style scoped>
    .home-sidebar {
        padding-top: 15px;
        padding-bottom: 200px;
    }
    .f-second-title {
        font-size: 13px;
    }
</style>
