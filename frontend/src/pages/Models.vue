<!-- frontend/src/pages/Models.vue -->

<template>
  <div>
    <div class="mb-4">
      <h2>Model Registry</h2>

      <div class="d-flex mt-4 gap-2 align-items-center">
        <button class="btn btn-primary" :disabled="training" @click="showTrainModal = true">
          {{ training ? 'Training...' : 'Train Model' }}
        </button>

        <input type="file" ref="fileInput" accept=".zip" class="d-none" @change="handleFileSelect" />
        <button class="btn btn-success" :disabled="uploading" @click="triggerFileInput">
          {{ uploading ? 'Uploading...' : 'Upload Model' }}
        </button>

        <button class="btn btn-info" @click="showCompareModal = true">
          Compare Models
        </button>
      </div>
    </div>

    <div v-if="uploadResult" class="alert alert-info">
      <strong>Result:</strong>
      <pre class="mb-0">{{ uploadResult }}</pre>
    </div>

    <ModelTable 
      class="mt-4" 
      :models="models" 
      @activate="openActivateModal" 
      @deactivate="openDeactivateModal"
      @rollback="handleRollback" 
      @evaluate="handleEvaluate" 
      @row-click="goToModel" 
      @delete="openDeleteModal" 
    />

    <button class="btn btn-sm btn-outline-info" @click="showHistoryModal = true">
      Show Activation History
    </button>

    <!-- Модальные окна -->
    <TrainModal 
      :show="showTrainModal" 
      :training="training"
      @close="showTrainModal = false" 
      @confirm="handleTrain" 
    />

    <ActivateModal 
      :show="showActivateModal" 
      :modelId="selectedModelForActivation"
      @close="showActivateModal = false" 
      @confirm="confirmActivate" 
    />

    <DeactivateModal 
      :show="showDeactivateModal" 
      :modelId="selectedModelForDeactivation"
      @close="showDeactivateModal = false" 
      @confirm="confirmDeactivate" 
    />

    <DeleteModal 
      :show="showDeleteModal" 
      :modelId="modelToDelete"
      @close="showDeleteModal = false" 
      @confirm="confirmDelete" 
    />

    <ModelDetailsModal :modelId="selectedModelId" @closed="selectedModelId = null" />

    <CompareModelsModal 
      :show="showCompareModal" 
      :models="models" 
      @close="showCompareModal = false" 
    />

    <ActivationHistoryModal 
      :show="showHistoryModal" 
      @close="showHistoryModal = false" 
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  getModels,
  activateModel,
  deactivateModel,
  uploadModel,
  evaluateModel,
  rollbackModel,
  trainModel,
  deleteModel,
  type ModelItem,
} from '../services/api'
import ModelTable from '../components/ModelTable.vue'
import ModelDetailsModal from "@/components/ModelDetailsModal.vue"
import CompareModelsModal from '../components/CompareModelsModal.vue'
import ActivationHistoryModal from '../components/ActivationHistoryModal.vue'
import TrainModal from '../components/TrainModal.vue'
import ActivateModal from '../components/ActivateModal.vue'
import DeactivateModal from '../components/DeactivateModal.vue'
import DeleteModal from '../components/DeleteModal.vue'

const models = ref<ModelItem[]>([])
const fileInput = ref<HTMLInputElement | null>(null)

const uploading = ref(false)
const training = ref(false)
const uploadResult = ref<any>(null)
const selectedModelId = ref<number | null>(null)

const showTrainModal = ref(false)
const showActivateModal = ref(false)
const showDeactivateModal = ref(false)
const showDeleteModal = ref(false)
const showCompareModal = ref(false)
const showHistoryModal = ref(false)

const selectedModelForActivation = ref<string>('')
const selectedModelForDeactivation = ref<string>('')
const modelToDelete = ref<number | null>(null)

async function loadModels() {
  const response = await getModels()
  models.value = response.data.map((m: any) => ({
    ml_model_id: m.id,
    version: m.version,
    active: m.is_active,
    created_at: m.trained_at || m.created_at
  }))
}

function goToModel(id: number) {
  selectedModelId.value = id
}

async function handleTrain() {
  try {
    training.value = true
    const response = await trainModel({ promote: false })
    uploadResult.value = response.data
    await loadModels()
    showTrainModal.value = false
  } finally {
    training.value = false
  }
}

function openActivateModal(modelId: number) {
  selectedModelForActivation.value = modelId.toString()
  showActivateModal.value = true
}

function openDeactivateModal(modelId: number) {
  selectedModelForDeactivation.value = modelId.toString()
  showDeactivateModal.value = true
}

async function confirmActivate() {
  await activateModel(selectedModelForActivation.value)
  showActivateModal.value = false
  await loadModels()
}

async function confirmDeactivate() {
  await deactivateModel(Number(selectedModelForDeactivation.value))
  showDeactivateModal.value = false
  await loadModels()
}

async function handleEvaluate(modelId: number) {
  const response = await evaluateModel(modelId.toString())
  uploadResult.value = response.data
}

async function handleRollback() {
  try {
    await rollbackModel()
    await loadModels()
  } catch (error) {
    console.error('Rollback failed:', error)
    alert('Rollback failed. Not enough history?')
  }
}

function openDeleteModal(modelId: number) {
  modelToDelete.value = modelId
  showDeleteModal.value = true
}

async function confirmDelete() {
  if (!modelToDelete.value) return
  try {
    await deleteModel(modelToDelete.value)
    await loadModels()
    showDeleteModal.value = false
    modelToDelete.value = null
  } catch (error) {
    console.error('Failed to delete model:', error)
  }
}

function triggerFileInput() {
  fileInput.value?.click()
}

async function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  const formData = new FormData()
  formData.append('file', file)

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

onMounted(() => {
  loadModels()
})
</script>