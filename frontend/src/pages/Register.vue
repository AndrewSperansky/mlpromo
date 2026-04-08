<!-- frontend/src/pages/Register.vue -->
<template>
  <div class="register-container">
    <div class="card shadow-sm" style="width: 450px;">
      <div class="card-header bg-primary text-white text-center">
        <h4 class="mb-0">Create Account</h4>
      </div>
      <div class="card-body">
        <div v-if="error" class="alert alert-danger">{{ error }}</div>
        <div v-if="success" class="alert alert-success">Registration successful! Please login.</div>
        
        <div class="mb-3">
          <label class="form-label">Username *</label>
          <input type="text" class="form-control" v-model="username" :class="{ 'is-invalid': usernameError }">
          <div class="invalid-feedback">{{ usernameError }}</div>
        </div>
        
        <div class="mb-3">
          <label class="form-label">Email *</label>
          <input type="email" class="form-control" v-model="email" :class="{ 'is-invalid': emailError }">
          <div class="invalid-feedback">{{ emailError }}</div>
        </div>
        
        <div class="mb-3">
          <label class="form-label">Full Name</label>
          <input type="text" class="form-control" v-model="fullName">
        </div>
        
        <div class="mb-3">
          <label class="form-label">Password *</label>
          <input type="password" class="form-control" v-model="password" :class="{ 'is-invalid': passwordError }">
          <div class="invalid-feedback">{{ passwordError }}</div>
        </div>
        
        <div class="mb-3">
          <label class="form-label">Confirm Password *</label>
          <input type="password" class="form-control" v-model="confirmPassword" :class="{ 'is-invalid': confirmPasswordError }">
          <div class="invalid-feedback">Passwords do not match</div>
        </div>
        
        <button class="btn btn-primary w-100" @click="handleRegister" :disabled="loading">
          <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
          {{ loading ? 'Registering...' : 'Register' }}
        </button>
        
        <div class="text-center mt-3">
          <router-link to="/login">Already have an account? Login</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const email = ref('')
const fullName = ref('')
const password = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const error = ref('')
const success = ref(false)

const usernameError = computed(() => {
  if (!username.value) return 'Username is required'
  if (username.value.length < 3) return 'Username must be at least 3 characters'
  return ''
})

const emailError = computed(() => {
  if (!email.value) return 'Email is required'
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(email.value)) return 'Invalid email format'
  return ''
})

const passwordError = computed(() => {
  if (!password.value) return 'Password is required'
  if (password.value.length < 4) return 'Password must be at least 4 characters'
  return ''
})

const confirmPasswordError = computed(() => {
  if (password.value !== confirmPassword.value) return 'Passwords do not match'
  return ''
})

const isValid = computed(() => {
  return !usernameError.value && !emailError.value && !passwordError.value && !confirmPasswordError.value
})

async function handleRegister() {
  if (!isValid.value) return
  
  loading.value = true
  error.value = ''
  success.value = false
  
  const result = await authStore.register({
    username: username.value,
    email: email.value,
    password: password.value,
    full_name: fullName.value
  })
  
  if (result.success) {
    success.value = true
    setTimeout(() => {
      router.push('/login')
    }, 2000)
  } else {
    error.value = result.error || 'Registration failed'
  }
  
  loading.value = false
}
</script>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 80vh;
}
</style>