<!-- frontend/src/pages/Models.vue -->

<template>
  <div>
    <!-- ===== HEADER ===== -->
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h2>Model Registry</h2>

      <div class="d-flex gap-2">
        <button class="btn btn-primary" :disabled="training" @click="handleTrain">
          {{ training ? 'Training...' : 'Train Model' }}
        </button>

        <input type="file" ref="fileInput" accept=".zip" class="d-none" @change="handleFileSelect" />

        <button class="btn btn-success" :disabled="uploading" @click="triggerFileInput">
          {{ uploading ? 'Uploading...' : 'Upload Model' }}
        </button>
      </div>
    </div>

    <!-- ===== RESULT CARD ===== -->
    <div v-if="uploadResult" class="alert alert-info">
      <strong>Model ID:</strong> {{ uploadResult.model_id }}
    </div>

    <!-- ===== TABLE ===== -->
    <ModelTable :models="models" @activate="handleActivate" @rollback="handleRollback" @evaluate="handleEvaluate"
      @row-click="goToModel" />

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  getModels,
  activateModel,
  uploadModel,
  evaluateModel,
  rollbackModel,
  trainModel
} from '../services/api'
import ModelTable from '../components/ModelTable.vue'

const router = useRouter()

function goToModel(id: string) {
  router.push(`/models/${id}`)
}

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

async function loadModels() {
  const response = await getModels()
  models.value = response.data
}

async function handleTrain() {
  try {
    training.value = true
    const response = await trainModel()
    uploadResult.value = response.data
    await loadModels()
  } finally {
    training.value = false
  }
}

async function handleActivate(modelId: string) {
  await activateModel(modelId)
  await loadModels()
}

async function handleEvaluate(modelId: string) {
  const response = await evaluateModel(modelId)
  uploadResult.value = response.data
}

async function handleRollback(modelId: string) {
  await rollbackModel(modelId)
  await loadModels()
}

function triggerFileInput() {
  fileInput.value?.click()
}

async function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]  // используем optional chaining

  if (!file) return  // проверка на существование

  const formData = new FormData()
  formData.append('file', file)  // TypeScript теперь знает, что file - это File

  try {
    uploading.value = true
    const response = await uploadModel(formData)
    uploadResult.value = response.data
    await loadModels()
  } finally {
    uploading.value = false
    target.value = ''
  }
}

onMounted(loadModels)
</script>