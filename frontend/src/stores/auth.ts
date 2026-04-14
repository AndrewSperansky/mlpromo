// frontend/src/stores/auth.ts

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../services/api'

interface User {
  id: number
  username: string
  email: string
  role: string
  full_name: string
  is_active: boolean
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('token'))
  const loading = ref(false)

  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isMLEngineer = computed(() => ['admin', 'ml_engineer'].includes(user.value?.role || ''))

  function setToken(newToken: string | null) {
    token.value = newToken
    if (newToken) {
      localStorage.setItem('token', newToken)
      api.defaults.headers.common['Authorization'] = `Bearer ${newToken}`
    } else {
      localStorage.removeItem('token')
      delete api.defaults.headers.common['Authorization']
    }
  }

  async function login(email: string, password: string) {
    loading.value = true
    try {
      const response = await api.post('/auth/login', { email, password })
      setToken(response.data.access_token)
      user.value = response.data.user
      return { success: true }
    } catch (error: any) {
      return { success: false, error: error.response?.data?.detail || 'Ошибка входа' }
    } finally {
      loading.value = false
    }
  }

  async function register(data: any) {
    loading.value = true
    try {
      const response = await api.post('/auth/register', data)
      return { success: true, message: response.data.message }
    } catch (error: any) {
      return { success: false, error: error.response?.data?.detail || 'Ошибка регистрации' }
    } finally {
      loading.value = false
    }
  }

  async function logout() {
    try {
      await api.post('/auth/logout')
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      setToken(null)
      user.value = null
    }
  }
  // ==========================================
  // 🔥 ВОССТАНОВЛЕНИЕ СЕССИИ ПРИ ЗАГРУЗКЕ
  // ==========================================

  async function fetchMe() {
    if (!token.value) return
    try {
      const response = await api.get('/auth/me')
      user.value = response.data
      return true
    } catch (error) {
      console.error('Session restore failed:', error)
      setToken(null)
      user.value = null
      return false
    }
  }

  // =============================================
  // 🔥 ИНИЦИАЛИЗАЦИЯ — проверяем токен при старте
  // =============================================
  
  const init = async () => {
    if (token.value) {
      api.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
      await fetchMe()
    }
  }

  // Запускаем инициализацию
  init()

  return {
    user,
    token,
    loading,
    isAuthenticated,
    isAdmin,
    isMLEngineer,
    login,
    register,
    logout,
    fetchMe,
    setToken,
    init
  }
})