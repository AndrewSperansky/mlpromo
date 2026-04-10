<!-- frontend/src/pages/Models.vue -->

<template>
  <div>
    <div class="mb-4">
      <h2>Model Registry</h2>

      <div class="d-flex mt-4 gap-2 align-items-center">
        <!-- TRAIN BUTTON -->
        <button class="btn btn-primary" :disabled="training" @click="openTrainModal">
          {{ training ? 'Training...' : 'Train Model' }}
        </button>

        <!-- UPLOAD MODEL BUTTON -->
        <input type="file" ref="fileInput" accept=".zip" class="d-none" @change="handleFileSelect" />
        <button class="btn btn-success" :disabled="uploading" @click="triggerFileInput">
          {{ uploading ? 'Uploading...' : 'Upload Model' }}
        </button>

        <!-- COMPARE MODELS BUTTON -->
        <button class="btn btn-info" @click="openCompareModal">
          Compare Models
        </button>

        <!-- FORCE RETRAIN CHECK BUTTON -->
        <button class="btn btn-outline-secondary" @click="forceRetrainCheck" :disabled="checking">
          <span v-if="checking" class="spinner-border spinner-border-sm me-1"></span>
          <i v-else class="bi bi-search me-1"></i>
          {{ checking ? 'Checking...' : 'Force Check' }}
        </button>
      </div>
    </div>

    <!-- Force Check Result -->
    <div v-if="checkResult" class="alert mb-3" :class="checkResult.needed ? 'alert-warning' : 'alert-info'">
      <div class="d-flex justify-content-between align-items-center">
        <div>
          <i :class="checkResult.needed ? 'bi bi-exclamation-triangle-fill' : 'bi bi-check-circle-fill'" class="me-2"></i>
          <strong>{{ checkResult.needed ? 'Retrain Recommended' : 'Model is Up to Date' }}</strong>
          <p class="mb-0 small mt-1">{{ checkResult.reason || 'No retrain needed at this time' }}</p>
        </div>
        <div v-if="checkResult.new_data_count !== undefined" class="text-end">
          <span class="badge bg-secondary">{{ checkResult.new_data_count }} new rows</span>
        </div>
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

    <button class="btn btn-sm btn-outline-info mt-3" @click="showHistoryModal = true">
      Show Activation History
    </button>

    <!-- Train Modal -->
    <TrainModal 
      :show="showTrainModal" 
      :training="training"
      @close="showTrainModal = false" 
      @confirm="handleTrain" 
    />

    <!-- Training Result Card -->
    <TrainingResultCard 
      v-if="trainingCompleted && trainingResult" 
      :trainingResult="trainingResult"
      @activated="handleTrainingActivated"
      @dismissed="handleTrainingDismissed"
    />

    <!-- Activate Modal -->
    <ActivateModal 
      :show="showActivateModal" 
      :modelId="selectedModelForActivation"
      @close="showActivateModal = false" 
      @confirm="confirmActivate" 
    />

    <!-- Deactivate Modal -->
    <DeactivateModal 
      :show="showDeactivateModal" 
      :modelId="selectedModelForDeactivation"
      @close="showDeactivateModal = false" 
      @confirm="confirmDeactivate" 
    />

    <!-- Delete Modal -->
    <DeleteModal 
      :show="showDeleteModal" 
      :modelId="modelToDelete"
      @close="showDeleteModal = false" 
      @confirm="confirmDelete" 
    />

    <!-- Model Details Modal -->
    <ModelDetailsModal :modelId="selectedModelId" @closed="selectedModelId = null" />

    <!-- Compare Models Modal -->
    <CompareModelsModal 
      :show="showCompareModal" 
      :models="models" 
      @close="showCompareModal = false" 
    />

    <!-- Activation History Modal -->
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
import api from '../services/api'
import ModelTable from '../components/ModelTable.vue'
import ModelDetailsModal from "@/components/ModelDetailsModal.vue"
import CompareModelsModal from '../components/CompareModelsModal.vue'
import ActivationHistoryModal from '../components/ActivationHistoryModal.vue'
import TrainModal from '../components/TrainModal.vue'
import TrainingResultCard from '../components/TrainingResultCard.vue'
import ActivateModal from '../components/ActivateModal.vue'
import DeactivateModal from '../components/DeactivateModal.vue'
import DeleteModal from '../components/DeleteModal.vue'


const compareModelA = ref<number | null>(null)
const compareModelB = ref<number | null>(null)


const models = ref<ModelItem[]>([])
const fileInput = ref<HTMLInputElement | null>(null)

const uploading = ref(false)
const training = ref(false)
const checking = ref(false)
const uploadResult = ref<any>(null)
const selectedModelId = ref<number | null>(null)
const checkResult = ref<any>(null)

// Training state
const showTrainModal = ref(false)
const trainingCompleted = ref(false)
const trainingResult = ref<any>(null)

// Modals
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

function openTrainModal() {
  showTrainModal.value = true
}


function openCompareModal() {
  const activeModel = models.value.find(m => m.active)
  const lastModel = models.value[models.value.length - 1]
  if (activeModel) compareModelA.value = activeModel.ml_model_id
  if (lastModel) compareModelB.value = lastModel.ml_model_id
  showCompareModal.value = true
}

async function handleTrain() {
  training.value = true
  showTrainModal.value = false
  
  try {
    const response = await trainModel({ promote: false })
    trainingResult.value = response.data
    trainingCompleted.value = true
    await loadModels()
  } catch (error) {
    console.error('Training failed:', error)
    alert('Training failed. Check server logs.')
    trainingCompleted.value = false
  } finally {
    training.value = false
  }
}

function handleTrainingActivated() {
  trainingCompleted.value = false
  trainingResult.value = null
  loadModels()
}

function handleTrainingDismissed() {
  trainingCompleted.value = false
  trainingResult.value = null
}

async function forceRetrainCheck() {
  checking.value = true
  checkResult.value = null
  try {
    const response = await api.post('/system/force-retrain')
    checkResult.value = response.data
    // Скрываем результат через 10 секунд
    setTimeout(() => {
      checkResult.value = null
    }, 10000)
  } catch (error) {
    console.error('Force check failed:', error)
    alert('Force check failed')
  } finally {
    checking.value = false
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

async function confirmActivate(force: boolean = false) {
  try {
    await activateModel(Number(selectedModelForActivation.value), force)
    showActivateModal.value = false
    await loadModels()
  } catch (error: any) {
    const detail = error.response?.data?.detail || error.message
    alert(`❌ Activation failed: ${detail}`)
  }
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