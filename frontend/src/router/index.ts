import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
/* import Dashboard from '../pages/Dashboard.vue'
import Models from '../pages/Models.vue'
import Audit from '../pages/Audit.vue'
import Predict from '../pages/Predict.vue'
import RuntimeAdmin from "../pages/RuntimeAdmin.vue" */

const routes = [
    { path: '/', component: () => import('../pages/LandingPage.vue'), meta: { public: true, requiresAuth: false } },
   { path: '/dashboard', component: () => import('../pages/Dashboard.vue'), meta: { requiresAuth: true } },
    { path: '/login', component: () => import('../pages/Login.vue'), meta: { public: true, requiresAuth: false } },
    { path: '/register', component: () => import('../pages/Register.vue'), meta: { public: true, requiresAuth: false } },
    { path: '/models', component: () => import('../pages/Models.vue'), meta: { requiresAuth: true, role: 'admin' } },
    { path: '/audit', component: () => import('../pages/Audit.vue'), meta: { requiresAuth: true, role: 'admin' } },
    { path: '/predict', component: () => import('../pages/Predict.vue'), meta: { requiresAuth: true, role: 'admin' } },
    { path: '/runtime', component: () => import('../pages/RuntimeAdmin.vue'), meta: { requiresAuth: true, role: 'admin' } },
    { path: '/datasets', component: () => import('../pages/Datasets.vue'), meta: { requiresAuth: true, role: 'admin' } },
    { path: '/users', component: () => import('../pages/Users.vue'), meta: { requiresAuth: true, role: 'admin' } },
    { path: '/activity', component: () => import('../pages/UserActivity.vue'), meta: { requiresAuth: true, role: 'admin' } },
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

router.beforeEach(async (to, _from, next) => {
  const authStore = useAuthStore()
  
  // Ждём инициализации
    if (!authStore.user && authStore.token) {
        await authStore.fetchMe()
    }
    
    if (to.meta.requiresAuth && !authStore.isAuthenticated) {
        next('/login')
        return
    }
  
  if (to.meta.role && authStore.user?.role !== to.meta.role && authStore.user?.role !== 'admin') {
    next('/')
    return
  }
  
  next()
})

export default router
