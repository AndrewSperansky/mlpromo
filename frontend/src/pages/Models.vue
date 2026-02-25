 <!-- frontend\src\pages\Models.vue -->

<template>
  <div>

    <!-- ===== HEADER ===== -->
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h2>Model Registry</h2>

      <div>
        <input
          type="file"
          ref="fileInput"
          accept=".zip"
          class="d-none"
          @change="handleFileSelect"
        />

        <button
          class="btn btn-success"
          :disabled="uploading"
          @click="triggerFileInput"
        >
          {{ uploading ? 'Uploading...' : 'Upload Model' }}
        </button>
      </div>
    </div>

    <!-- ===== Upload Result Card ===== -->
    <div
      v-if="uploadResult"
      class="alert alert-info"
    >
      <strong>Upload Status:</strong> {{ uploadResult.status }} <br />
      <strong>Model ID:</strong> {{ uploadResult.model_id }}
    </div>

    <!-- ===== TABLE ===== -->
    <ModelTable
      :models="models"
      @activate="handleActivate"
      @rollback="handleRollback"
    />

    <!-- ===== TOASTS ===== -->
    <div
      class="toast-container position-fixed bottom-0 end-0 p-3"
      style="z-index: 1055"
    >
      <div
        class="toast show align-items-center text-bg-success border-0"
        v-if="toast.success"
      >
        <div class="d-flex">
          <div class="toast-body">
            {{ toast.success }}
          </div>
          <button class="btn-close btn-close-white me-2 m-auto"
            @click="toast.success = ''"></button>
        </div>
      </div>

      <div
        class="toast show align-items-center text-bg-danger border-0"
        v-if="toast.error"
      >
        <div class="d-flex">
          <div class="toast-body">
            {{ toast.error }}
          </div>
          <button class="btn-close btn-close-white me-2 m-auto"
            @click="toast.error = ''"></button>
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
  uploadModel
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
const uploadResult = ref<any>(null)

const toast = ref({
  success: '',
  error: ''
})

async function loadModels() {
  const response = await getModels()
  models.value = response.data
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

async function handleRollback() {
  toast.value.error = 'Rollback endpoint not implemented yet'
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