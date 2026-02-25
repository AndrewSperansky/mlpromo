 <!-- frontend\src\pages\Models.vue -->

<template>
  <div>
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
          @click="triggerFileInput"
        >
          Upload Model
        </button>
      </div>
    </div>

    <ModelTable
      :models="models"
      @activate="handleActivate"
    />
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

async function loadModels() {
  try {
    const response = await getModels()
    models.value = response.data
  } catch (error) {
    console.error('Failed to load models', error)
  }
}

async function handleActivate(modelId: string) {
  try {
    await activateModel(modelId)
    await loadModels()
  } catch (error) {
    console.error('Activation failed', error)
  }
}

function triggerFileInput() {
  fileInput.value?.click()
}

async function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement

  if (!target.files || target.files.length === 0) {
    return
  }

  const file = target.files.item(0)

  if (!file) {
    return
  }

  const formData = new FormData()
  formData.append('file', file)

  try {
    await uploadModel(formData)
    await loadModels()
  } catch (error) {
    console.error('Upload failed', error)
  } finally {
    target.value = ''
  }
}

onMounted(loadModels)
</script>