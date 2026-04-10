<!-- frontend/src/pages/Register.vue -->

<template>
  <div class="register-container">
    <div class="card shadow-sm" style="width: 450px;">
      <div class="card-header bg-primary text-white text-center">
        <h4 class="mb-0">Регистрация</h4>
      </div>
      <div class="card-body">
        <div v-if="error" class="alert alert-danger">{{ error }}</div>
        <div v-if="success" class="alert alert-success">
          <i class="bi bi-check-circle-fill me-2"></i>
          {{ successMessage }}
        </div>
        
        <div class="mb-3">
          <label class="form-label">Email *</label>
          <input type="email" class="form-control" v-model="email" :class="{ 'is-invalid': emailError }">
          <div class="invalid-feedback">{{ emailError }}</div>
        </div>
        
        <div class="mb-3">
          <label class="form-label">Имя пользователя (опционально)</label>
          <input type="text" class="form-control" v-model="username">
          <div class="form-text">Если не указать, будет сгенерировано из email</div>
        </div>
        
        <div class="mb-3">
          <label class="form-label">Полное имя (опционально)</label>
          <input type="text" class="form-control" v-model="fullName">
        </div>
        
        <div class="mb-3">
          <label class="form-label">Пароль *</label>
          <input type="password" class="form-control" v-model="password" :class="{ 'is-invalid': passwordError }">
          <div class="invalid-feedback">{{ passwordError }}</div>
        </div>
        
        <div class="mb-3">
          <label class="form-label">Подтверждение пароля *</label>
          <input type="password" class="form-control" v-model="confirmPassword" :class="{ 'is-invalid': confirmPasswordError }">
          <div class="invalid-feedback">Пароли не совпадают</div>
        </div>
        
        <button class="btn btn-primary w-100" @click="handleRegister" :disabled="loading">
          <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
          {{ loading ? 'Регистрация...' : 'Зарегистрироваться' }}
        </button>
        
        <div class="text-center mt-3">
          <router-link to="/login">Уже есть аккаунт? Войти</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()

const email = ref('')
const username = ref('')
const fullName = ref('')
const password = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const error = ref('')
const success = ref(false)
const successMessage = ref('')

const emailError = computed(() => {
  if (!email.value) return 'Email обязателен'
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(email.value)) return 'Неверный формат email'
  return ''
})

const passwordError = computed(() => {
  if (!password.value) return 'Пароль обязателен'
  if (password.value.length < 7) return 'Пароль должен быть не менее 7 символов'
  return ''
})

const confirmPasswordError = computed(() => {
  if (password.value !== confirmPassword.value) return 'Пароли не совпадают'
  return ''
})

const isValid = computed(() => {
  return !emailError.value && !passwordError.value && !confirmPasswordError.value
})

async function handleRegister() {
  if (!isValid.value) return
  
  loading.value = true
  error.value = ''
  success.value = false
  
  const result = await authStore.register({
    email: email.value,
    username: username.value || undefined,
    password: password.value,
    full_name: fullName.value || undefined
  })
  
  if (result.success) {
    successMessage.value = '✓ Регистрация успешна! Допуск будет предоставлен после проверки Администратором.'
    success.value = true
    // Очищаем форму
    email.value = ''
    username.value = ''
    fullName.value = ''
    password.value = ''
    confirmPassword.value = ''
  } else {
    error.value = result.error || 'Ошибка регистрации'
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