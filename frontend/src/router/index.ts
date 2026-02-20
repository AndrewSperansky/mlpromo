import { createRouter, createWebHistory } from 'vue-router'

import Dashboard from '../pages/Dashboard.vue'
import Models from '../pages/Models.vue'
import Audit from '../pages/Audit.vue'
import Predict from '../pages/Predict.vue'
import RuntimeAdmin from "../pages/RuntimeAdmin.vue"

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
    },
    {
        path: "/runtime",
        component: RuntimeAdmin,
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

export default router
