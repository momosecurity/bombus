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
    <Breadcrumb v-if="firstItem.path !== ''">
        <BreadcrumbItem to="/">
            <Icon type="md-home"></Icon> 首页
        </BreadcrumbItem>
        <BreadcrumbItem>
            <Icon :type="firstItem.meta.icon"></Icon> {{firstItem.meta.title}}
        </BreadcrumbItem>
        <BreadcrumbItem :to="secondItem.path">
            <Icon type="logo-buffer"></Icon> <span>{{secondItem.meta.title}}</span>
        </BreadcrumbItem>
    </Breadcrumb>
</template>


<script>
    export default {
        name: "HomeBreadcrumb",
        data () {
            return {

            }
        },
        computed: {
            firstItem: function () { return this.$route.matched[0] },
            secondItem: function () { return this.$route }
        }
    }
</script>


<style scoped>
</style>
