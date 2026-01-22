import Vue from 'vue'
import VueRouter from 'vue-router'
import ChatView from '../views/agent/chat-completion/ChatView.vue'
import ModelSquare from '../views/agent/model-square/ModelSquare.vue'
import AppsView from '../views/agent/app-square/AppsView.vue'
import AppDetailView from '../views/agent/app-square/AppDetailView.vue'
import ModelDebugView from '../views/agent/model-square/ModelDebugView.vue'
import VoiceCallView from '../views/agent/dial-agent/VoiceCallView.vue'

Vue.use(VueRouter)

const routes = [
    {
        path: '/',
        redirect: '/chat'
    },
    {
        path: '/models',
        name: 'ModelSquare',
        component: ModelSquare
    },
    {
        path: '/chat',
        name: 'NewChat',
        component: ChatView
    },
    {
        path: '/chat/:id',
        name: 'Chat',
        component: ChatView,
        props: true
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
    },
    {
        path: '/model-debug',
        name: 'ModelDebug',
        component: ModelDebugView
    },
    {
        path: '/voice-call',
        name: 'VoiceCall',
        component: VoiceCallView
    }
]

const router = new VueRouter({
    mode: 'history',
    base: process.env.BASE_URL,
    routes
})

// 处理重复导航错误
const originalPush = VueRouter.prototype.push
VueRouter.prototype.push = function push(location) {
    return originalPush.call(this, location).catch(err => {
        if (err.name !== 'NavigationDuplicated') {
            throw err
        }
    })
}

const originalReplace = VueRouter.prototype.replace
VueRouter.prototype.replace = function replace(location) {
    return originalReplace.call(this, location).catch(err => {
        if (err.name !== 'NavigationDuplicated') {
            throw err
        }
    })
}

export default router
