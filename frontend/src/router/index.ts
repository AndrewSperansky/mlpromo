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
    },
    {
        path: "/datasets",
        name: "Datasets",
        component: () => import("../pages/Datasets.vue"),
    },
    {
        path: "/datasets/:id",
        name: "DatasetDetails",
        component: () => import("../pages/DatasetDetails.vue"),
    },
    {
        path: "/models/:id",
        name: "ModelDetails",
        component: () => import("../pages/ModelDetails.vue"),
    },

]

const router = createRouter({
    history: createWebHistory(),
    routes
})

export default router
