// frontend\src\stores\auth.ts

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../services/api'

interface User {
  id: number
  username: string
  email: string
  role: string
  full_name: string
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

  async function login(username: string, password: string) {
    loading.value = true
    try {
      const response = await api.post('/auth/login', { username, password })
      setToken(response.data.access_token)
      user.value = response.data.user
      return { success: true }
    } catch (error: any) {
      return { success: false, error: error.response?.data?.detail || 'Login failed' }
    } finally {
      loading.value = false
    }
  }

  async function register(data: any) {
    loading.value = true
    try {
      await api.post('/auth/register', data)
      return { success: true }
    } catch (error: any) {
      return { success: false, error: error.response?.data?.detail || 'Registration failed' }
    } finally {
      loading.value = false
    }
  }

  async function logout() {
    await api.post('/auth/logout')
    setToken(null)
    user.value = null
  }

  async function fetchMe() {
    if (!token.value) return
    try {
      const response = await api.get('/auth/me')
      user.value = response.data
    } catch {
      setToken(null)
      user.value = null
    }
  }

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
    setToken
  }
})