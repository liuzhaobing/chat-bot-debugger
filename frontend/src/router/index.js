import Vue from 'vue'
import VueRouter from 'vue-router'
import ChatArea from '../components/chat-completion/ChatArea.vue'
import ModelSquare from '../views/agent/model-square/ModelSquare.vue'
import AppsView from '../views/agent/app-square/AppsView.vue'
import AppDetailView from '../views/agent/app-square/AppDetailView.vue'
import ModelDebugView from '../views/agent/model-square/ModelDebugView.vue'
import VoiceCallView from '../views/agent/dial-agent/VoiceCallView.vue'

Vue.use(VueRouter)

const routes = [
    {
        path: '/models',
        name: 'ModelSquare',
        component: ModelSquare
    },
    {
        path: '/chat',
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

export default router
