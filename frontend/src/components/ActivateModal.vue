<!-- frontend/src/components/ActivateModal.vue -->

<template>
  <div v-if="show" class="modal-backdrop" @click.self="$emit('close')">
    <div class="modal-box" style="width: 500px;">
      <h5>Activate Model</h5>
      <p>Activate model:</p>
      <strong>{{ modelId }}</strong>

      <!-- Сообщение об ошибке, если активация не удалась -->
      <div v-if="errorMessage" class="alert alert-danger mt-3">
        <i class="bi bi-exclamation-triangle-fill me-2"></i>
        <strong>Cannot activate model:</strong>
        <p class="mb-0 mt-1">{{ errorMessage }}</p>
      </div>

      <!-- Предупреждение и чекбокс для force -->
      <div v-if="errorMessage" class="mt-3">
        <div class="form-check">
          <input 
            class="form-check-input" 
            type="checkbox" 
            v-model="forceActivation" 
            id="forceCheck"
          >
          <label class="form-check-label" for="forceCheck">
            Force activation (ignore metrics check)
          </label>
        </div>
        <small class="text-warning" v-if="forceActivation">
          ⚠️ Warning: Activating a model with worse metrics may degrade prediction quality!
        </small>
      </div>

      <div class="mt-3 d-flex justify-content-end gap-2">
        <button class="btn btn-secondary" @click="$emit('close')">Cancel</button>
        <button 
          class="btn btn-success" 
          @click="confirm"
          :disabled="loading"
        >
          <span v-if="loading" class="spinner-border spinner-border-sm me-1"></span>
          {{ loading ? 'Activating...' : 'Activate' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { activateModel } from '../services/api'

const props = defineProps<{
  show: boolean
  modelId: string
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'activated'): void
}>()

const forceActivation = ref(false)
const loading = ref(false)
const errorMessage = ref('')

// Сбрасываем состояние при открытии модального окна
watch(() => props.show, (newVal) => {
  if (newVal) {
    forceActivation.value = false
    errorMessage.value = ''
  }
})

async function confirm() {
  loading.value = true
  errorMessage.value = ''
  
  try {
    await activateModel(Number(props.modelId), forceActivation.value)
    emit('activated')
    emit('close')
  } catch (error: any) {
    const detail = error.response?.data?.detail || error.message
    
    // Форматируем понятное сообщение
    if (detail.includes('worse rmse')) {
      errorMessage.value = 'This model has worse RMSE than the currently active model.'
    } else if (detail.includes('not found')) {
      errorMessage.value = 'Model file not found. Please retrain the model.'
    } else {
      errorMessage.value = detail
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1050;
}

.modal-box {
  background: white;
  padding: 24px;
  border-radius: 8px;
  width: 500px;
  max-width: 90vw;
}

.form-check {
  padding-left: 1.5rem;
}

.alert-danger {
  background-color: #f8d7da;
  border: 1px solid #f5c2c7;
  color: #842029;
  border-radius: 6px;
  padding: 12px;
}
</style>