import { createRouter, createWebHistory } from 'vue-router'

import Dashboard from '../pages/Dashboard.vue'
import Models from '../pages/Models.vue'
import Audit from '../pages/Audit.vue'
import Predict from '../pages/Predict.vue'

const routes = [
    {
        path: '/',
        name: 'Dashboard',
        component: Dashboard
    },
    {
        path: '/models',
        name: 'Models',
        component: Models
    },
    {
        path: '/audit',
        name: 'Audit',
        component: Audit
    },
    {
        path: '/predict',
        name: 'Predict',
        component: Predict
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

export default router
