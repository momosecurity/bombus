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
    <Footer class="layout-footer-center">
        <Row type="flex" justify="center">
            <Col span="8">
                <div>
                    <h6 class="n-footer-link-group-name">合规法案</h6>
                    <a class="n-footer-link" href="https://baike.baidu.com/item/SOX404/134662">SOX404法案</a>
                    <a class="n-footer-link" href="http://www.gov.cn/gzdt/2007-07/24/content_694380.htm">信息安全等级保护管理办法</a>
                </div>
            </Col>
            <Col span="8">
                <div>
                    <h6 class="n-footer-link-group-name">安全开源</h6>
                    <a class="n-footer-link" href="https://github.com/momosecurity/aswan">Aswan风控策略引擎</a>
                    <a class="n-footer-link" href="https://github.com/momosecurity/rhizobia_J">JAVA安全SDK及编码规范</a>
                    <a class="n-footer-link" href="https://github.com/momosecurity/rhizobia_P">PHP安全SDK及编码规范</a>
                    <a class="n-footer-link" href="https://github.com/momosecurity/">GitHub</a>
                </div>
            </Col>
        </Row>

        <span class="home-footer" style="float: right"><span style="letter-spacing: 1px;">&copy;2020</span> 陌陌安全</span>
    </Footer>
</template>

<script>
    export default {
        name: "HomeFooter"
    }
</script>

<style scoped>
    .home-footer {
        font-size: 13px;
        font-weight: bold;
        letter-spacing: 2px;
    }
    .layout-footer-center {
        padding-top: 24px;
        color: #616161;
        height: 228px;
        width: 100%;
    }
    .n-footer-link {
        color: #616161;
        width: fit-content;
        display: block;
        font-size: 12px;
        padding-top: 8px;
        padding-bottom: 8px;
    }

    .n-footer-link:hover {
        cursor: pointer;
        text-decoration: underline;
    }
    .n-footer-link-group-name {
        font-size: 15px;
        font-weight: bold;
    }
</style>
