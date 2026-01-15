import Vue from 'vue'
import VueRouter from 'vue-router'
import ChatArea from '../components/ChatArea.vue'
import ModelSquare from '../views/ModelSquare.vue'
import AppsView from '../views/AppsView.vue'
import AppDetailView from '../views/AppDetailView.vue'
import ModelDebugView from '../views/ModelDebugView.vue'
import VoiceCallView from '../views/VoiceCallView.vue'

Vue.use(VueRouter)

const routes = [
    {
        path: '/',
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
