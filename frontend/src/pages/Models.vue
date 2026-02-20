<template>
  <div>
    <h2 class="mb-4">Model Registry</h2>

    <ModelTable
      :models="models"
      @activate="handleActivate"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getModels, activateModel } from '../services/api'
import ModelTable from '../components/ModelTable.vue'

interface ModelItem {
  ml_model_id: string
  version: string
  active: boolean
  created_at: string
}

const models = ref<ModelItem[]>([])

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

onMounted(loadModels)
</script>