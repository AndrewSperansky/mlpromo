<!-- frontend/src/pages/Models.vue -->

<template>
  <div>

    <!-- ===== HEADER ===== -->
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h2>Model Registry</h2>

      <div class="d-flex gap-2">

        <!-- Train Button -->
        <button class="btn btn-primary" :disabled="training" @click="handleTrain">
          {{ training ? 'Training...' : 'Train Model' }}
        </button>

        <!-- Upload -->
        <input type="file" ref="fileInput" accept=".zip" class="d-none" @change="handleFileSelect" />

        <button class="btn btn-success" :disabled="uploading" @click="triggerFileInput">
          {{ uploading ? 'Uploading...' : 'Upload Model' }}
        </button>

      </div>
    </div>

    <!-- ===== Result Card (Upload / Evaluate / Train) ===== -->
    <div v-if="uploadResult" class="alert alert-info">

      <strong>Model ID:</strong> {{ uploadResult.model_id }}

      <!-- Metrics -->
      <div v-if="uploadResult.metrics" class="mt-2">
        <strong>Metrics:</strong>
        <ul class="mb-1">
          <li v-for="(value, key) in uploadResult.metrics" :key="key">
            {{ key }}: {{ Number(value).toFixed(4) }}
          </li>
        </ul>
      </div>

      <!-- Promotion Decision -->
      <div v-if="uploadResult.promotion_decision" class="mt-2">
        <strong>Decision:</strong>
        <span class="badge ms-2" :class="decisionClass(uploadResult.promotion_decision.decision)">
          {{ uploadResult.promotion_decision.decision }}
        </span>

        <div class="small text-muted mt-1">
          {{ uploadResult.promotion_decision.reason }}
        </div>
      </div>

    </div>

    <!-- ===== TABLE ===== -->
    <ModelTable :models="models" @activate="handleActivate" @rollback="handleRollback" @evaluate="handleEvaluate" />

    <!-- ===== TOASTS ===== -->
    <div class="toast-container position-fixed bottom-0 end-0 p-3" style="z-index: 1055">
      <div class="toast show align-items-center text-bg-success border-0" v-if="toast.success">
        <div class="d-flex">
          <div class="toast-body">
            {{ toast.success }}
          </div>
          <button class="btn-close btn-close-white me-2 m-auto" @click="toast.success = ''"></button>
        </div>
      </div>

      <div class="toast show align-items-center text-bg-danger border-0" v-if="toast.error">
        <div class="d-flex">
          <div class="toast-body">
            {{ toast.error }}
          </div>
          <button class="btn-close btn-close-white me-2 m-auto" @click="toast.error = ''"></button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  getModels,
  activateModel,
  uploadModel,
  evaluateModel,
  rollbackModel,
  trainModel
} from '../services/api'
import ModelTable from '../components/ModelTable.vue'

interface ModelItem {
  ml_model_id: string
  version: string
  active: boolean
  created_at: string
}

const models = ref<ModelItem[]>([])
const fileInput = ref<HTMLInputElement | null>(null)

const uploading = ref(false)
const training = ref(false)

const uploadResult = ref<any>(null)

const toast = ref({
  success: '',
  error: ''
})

function decisionClass(decision: string) {
  if (decision === 'approve') return 'bg-success'
  if (decision === 'reject') return 'bg-danger'
  if (decision === 'manual_review') return 'bg-warning text-dark'
  if (decision === 'frozen') return 'bg-secondary'
  return 'bg-light text-dark'
}

async function loadModels() {
  const response = await getModels()
  models.value = response.data
}

async function handleTrain() {
  try {
    training.value = true

    const response = await trainModel()

    uploadResult.value = response.data

    toast.value.success = 'Training completed successfully'

    await loadModels()

  } catch (error: any) {
    toast.value.error =
      error?.response?.data?.detail || 'Training failed'
  } finally {
    training.value = false
  }
}

async function handleActivate(modelId: string) {
  try {
    await activateModel(modelId)
    toast.value.success = 'Model activated successfully'
    await loadModels()
  } catch {
    toast.value.error = 'Activation failed'
  }
}

async function handleEvaluate(modelId: string) {
  try {
    const response = await evaluateModel(modelId)
    uploadResult.value = response.data
    toast.value.success = 'Model evaluated successfully'
  } catch {
    toast.value.error = 'Evaluation failed'
  }
}

async function handleRollback(modelId: string) {
  try {
    await rollbackModel(modelId)
    toast.value.success = `Rolled back to ${modelId}`
    await loadModels()
  } catch {
    toast.value.error = 'Rollback failed'
  }
}

function triggerFileInput() {
  fileInput.value?.click()
}

async function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement
  if (!target.files || target.files.length === 0) return

  const file = target.files.item(0)
  if (!file) return

  const formData = new FormData()
  formData.append('file', file)

  try {
    uploading.value = true

    const response = await uploadModel(formData)
    uploadResult.value = response.data

    toast.value.success = 'Model uploaded successfully'

    await loadModels()

  } catch (error: any) {
    toast.value.error =
      error?.response?.data?.detail || 'Upload failed'
  } finally {
    uploading.value = false
    target.value = ''
  }
}

onMounted(loadModels)
</script>