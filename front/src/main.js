/*
 * Copyright (C) 2020  momosecurity
 *
 * This file is part of Bombus.
 *
 * Bombus is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Lesser General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * Bombus is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public License
 * along with Bombus.  If not, see <https://www.gnu.org/licenses/>.
 */

import Vue from 'vue';
import ViewUI from 'view-design';
import VueClipboard from 'vue-clipboard2';
import VueRouter from 'vue-router';
import 'view-design/dist/styles/iview.css';

import Routers from './router';
import Util from './libs/util';
import App from './app.vue';
import {loginAuthenticate} from './api'


Vue.use(VueClipboard);
Vue.use(VueRouter);
Vue.use(ViewUI);

// 路由配置
const RouterConfig = {
    mode: 'history',
    routes: Routers
};
const router = new VueRouter(RouterConfig);

router.beforeEach((to, from, next) => {
    ViewUI.LoadingBar.start();
    Util.title(to.meta.title);

    let username = sessionStorage.getItem('username')
    if (username) {
        return next();
    }
    if (to.path === '/login'){
        next();
    }else {
        loginAuthenticate(to.path).then(resp => {
            if (resp.data.status === 200) {
                console.log('aaa:', resp.data.payload['is_super'])
                sessionStorage.setItem('username', resp.data.payload['username'])
                sessionStorage.setItem('perms', resp.data.payload['perms'])
                sessionStorage.setItem('is_super', resp.data.payload['is_superuser'])
                next();
            }
        })
    }
});

router.afterEach((to, from, next) => {
    ViewUI.LoadingBar.finish();
    window.scrollTo(0, 0);
});

new Vue({
    el: '#app',
    router: router,
    render: h => h(App)
});
