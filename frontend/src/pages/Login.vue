<!-- frontend/src/pages/Login.vue -->
<template>
  <div class="login-container">
    <div class="card shadow-sm" style="width: 400px;">
      <div class="card-header bg-primary text-white text-center">
        <h4 class="mb-0">Promo ML Login</h4>
      </div>
      <div class="card-body">
        <div v-if="error" class="alert alert-danger">{{ error }}</div>
        
        <div class="mb-3">
          <label class="form-label">Username</label>
          <input 
            type="text" 
            class="form-control" 
            v-model="username" 
            @keyup.enter="handleLogin"
            autofocus
          >
        </div>
        
        <div class="mb-3">
          <label class="form-label">Password</label>
          <input 
            type="password" 
            class="form-control" 
            v-model="password" 
            @keyup.enter="handleLogin"
          >
        </div>
        
        <button 
          class="btn btn-primary w-100" 
          @click="handleLogin" 
          :disabled="loading"
        >
          <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
          {{ loading ? 'Logging in...' : 'Login' }}
        </button>
        
        <div class="text-center mt-3">
          <router-link to="/register">Don't have an account? Register</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function handleLogin() {
  if (!username.value || !password.value) {
    error.value = 'Please enter username and password'
    return
  }
  
  loading.value = true
  error.value = ''
  
  const result = await authStore.login(username.value, password.value)
  
  if (result.success) {
    router.push('/dashboard')
  } else {
    error.value = result.error || 'Login failed'
  }
  
  loading.value = false
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 80vh;
}
</style>