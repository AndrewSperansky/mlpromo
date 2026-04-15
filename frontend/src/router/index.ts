import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
/* import Dashboard from '../pages/Dashboard.vue'
import Models from '../pages/Models.vue'
import Audit from '../pages/Audit.vue'
import Predict from '../pages/Predict.vue'
import RuntimeAdmin from "../pages/RuntimeAdmin.vue" */
import Lineage from '../pages/Lineage.vue'



const routes = [
    { path: '/', component: () => import('../pages/LandingPage.vue'), meta: { public: true, requiresAuth: false } },
    { path: '/dashboard', component: () => import('../pages/Dashboard.vue'), meta: { requiresAuth: true } },
    { path: '/login', component: () => import('../pages/Login.vue'), meta: { public: true, requiresAuth: false } },
    { path: '/register', component: () => import('../pages/Register.vue'), meta: { public: true, requiresAuth: false } },
    { path: '/models', component: () => import('../pages/Models.vue'), meta: { requiresAuth: true, roles: ['admin', 'ml_engineer'] } },
    { path: '/audit', component: () => import('../pages/Audit.vue'), meta: { requiresAuth: true, roles: ['admin', 'analyst', 'ml_engineer'] } },
    { path: '/predict', component: () => import('../pages/Predict.vue'), meta: { requiresAuth: true, roles: ['admin', 'analyst', 'ml_engineer'] } },
    { path: '/runtime', component: () => import('../pages/RuntimeAdmin.vue'), meta: { requiresAuth: true, roles: ['admin', 'ml_engineer'] } },
    { path: '/datasets', component: () => import('../pages/Datasets.vue'), meta: { requiresAuth: true, roles: ['admin', 'ml_engineer'] } },
    { path: '/users', component: () => import('../pages/Users.vue'), meta: { requiresAuth: true, roles: ['admin'] } },
    { path: '/activity', component: () => import('../pages/UserActivity.vue'), meta: { requiresAuth: true, roles: ['admin'] } },
    { path: '/lineage', name: 'Lineage', component: Lineage,  meta: { requiresAuth: true, roles: ['admin', 'analyst', 'ml_engineer'] } },
]

const router = createRouter({
    history: createWebHistory(),
    routes
})



router.beforeEach(async (to, _from, next) => {
  const authStore = useAuthStore()
  
  // 🔥 Если токен есть, но пользователь не загружен — восстанавливаем сессию
  if (authStore.token && !authStore.user) {
    await authStore.fetchMe()
  }
  
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
    return
  }
  
  // 🔥 Проверка roles (массив)
    if (to.meta.roles && Array.isArray(to.meta.roles)) {
        const userRole = authStore.user?.role
        if (!userRole || !to.meta.roles.includes(userRole)) {
            next('/dashboard')
            return
        }
    }
  
  if (to.path === '/login' && authStore.isAuthenticated) {
    next('/dashboard')
    return
  }
  
  next()
})


export default router
