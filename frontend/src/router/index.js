import Vue from 'vue'
import VueRouter from 'vue-router'
import ChatArea from '../components/ChatArea.vue'
import AppsView from '../views/AppsView.vue'
import AppDetailView from '../views/AppDetailView.vue'

Vue.use(VueRouter)

const routes = [
    {
        path: '/',
        name: 'Home',
        component: ChatArea
    },
    {
        path: '/apps',
        name: 'Apps',
        component: AppsView
    },
    {
        path: '/apps/:id',
        name: 'AppDetail',
        component: AppDetailView
    }
]

const router = new VueRouter({
    mode: 'history',
    base: process.env.BASE_URL,
    routes
})

export default router
