<!-- frontend/src/pages/Models.vue -->

<template>
  <div>
    <!-- ===== HEADER ===== -->
    <div class="mb-4">
      <div class="mb-6">
        <h2>Model Registry</h2>
      </div>

      <!-- ROW 2 -->
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
      </div>
    </div>
  </div>

  <!-- ===== RESULT CARD ===== -->
  <div v-if="uploadResult" class="alert alert-info">
    <strong>Result:</strong>
    <pre class="mb-0">{{ uploadResult }}</pre>
  </div>

  <!-- ===== TABLE ===== -->
  <ModelTable 
    class="mt-4" 
    :models="models" 
    @activate="openActivateModal" 
    @deactivate="handleDeactivate"
    @rollback="handleRollback"
    @evaluate="handleEvaluate" 
    @row-click="goToModel" 
    @delete="openDeleteModal" 
  />

  <button class="btn btn-sm btn-outline-info" @click="showHistory = true">
    Show Activation History
  </button>

  <!-- ===== TRAIN MODAL ===== -->
  <div v-if="showTrainModal" class="modal-backdrop">
    <div class="modal-box">
      <h5>Confirm Training</h5>
      <p>Train model on the entire dataset?</p>
      <p class="text-muted small">Model will be trained on all available data</p>

      <div class="mt-3 d-flex justify-content-end gap-2">
        <button class="btn btn-secondary" @click="showTrainModal = false">
          Cancel
        </button>
        <button class="btn btn-primary" :disabled="training" @click="handleTrain">
          Confirm
        </button>
      </div>
    </div>
  </div>

  <!-- ===== ACTIVATE MODAL ===== -->
  <div v-if="showActivateModal" class="modal-backdrop">
    <div class="modal-box">
      <h5>Activate Model</h5>
      <p>Activate model:</p>
      <strong>{{ selectedModelForActivation }}</strong>

      <div class="mt-3 d-flex justify-content-end gap-2">
        <button class="btn btn-secondary" @click="showActivateModal = false">
          Cancel
        </button>
        <button class="btn btn-success" @click="confirmActivate">
          Activate
        </button>
      </div>
    </div>
  </div>

  <!-- ===== DEACTIVATE MODAL ===== -->
  <div v-if="showDeactivateModal" class="modal-backdrop">
    <div class="modal-box">
      <h5>Deactivate Model</h5>
      <p>Deactivate model:</p>
      <strong>{{ selectedModelForDeactivation }}</strong>
      <p class="text-warning mt-2">⚠️ This model will no longer be used for predictions!</p>

      <div class="mt-3 d-flex justify-content-end gap-2">
        <button class="btn btn-secondary" @click="showDeactivateModal = false">
          Cancel
        </button>
        <button class="btn btn-warning" @click="confirmDeactivate">
          Deactivate
        </button>
      </div>
    </div>
  </div>

  <!-- ===== DELETE MODAL ===== -->
  <div v-if="showDeleteModal" class="modal-backdrop" @click.self="showDeleteModal = false">
    <div class="modal-box">
      <h5 class="text-danger">Confirm Deletion</h5>
      <p>Are you sure you want to delete model:</p>
      <strong>ID: {{ modelToDelete }}</strong>
      <p class="text-warning mt-2">⚠️ This action cannot be undone!</p>

      <div class="mt-3 d-flex justify-content-end gap-2">
        <button class="btn btn-secondary" @click="showDeleteModal = false">
          Cancel
        </button>
        <button class="btn btn-danger" @click="confirmDelete">
          Delete Permanently
        </button>
      </div>
    </div>
  </div>

  <!-- ===== MODEL DETAIL MODAL ===== -->
  <ModelDetailsModal :modelId="selectedModelId" @closed="selectedModelId = null" />

  <!-- модальное окно с историей -->
  <div v-if="showHistory" class="modal-backdrop" @click.self="showHistory = false">
    <div class="modal-box" style="width: 600px;">
      <h5>Model Activation History</h5>

      <table class="table table-sm">
        <thead>
          <tr>
            <th>Time</th>
            <th>Model ID</th>
            <th>Activated By</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="entry in history" :key="entry.id">
            <td>{{ formatDate(entry.activated_at) }}</td>
            <td>{{ entry.model_id }}</td>
            <td>{{ entry.activated_by }}</td>
          </tr>
          <tr v-if="history.length === 0">
            <td colspan="3" class="text-center">No history yet</td>
          </tr>
        </tbody>
      </table>

      <button class="btn btn-secondary" @click="showHistory = false">Close</button>
    </div>
  </div>

  <!-- Модальное окно для сравнения моделей -->
  <div v-if="showCompareModal" class="modal-backdrop" @click.self="showCompareModal = false">
    <div class="modal-box" style="width: 800px;">
      <h5>Compare Models</h5>

      <div class="row mb-3">
        <div class="col">
          <label>Model A</label>
          <select v-model="compareModelA" class="form-select">
            <option v-for="m in models" :key="m.ml_model_id" :value="m.ml_model_id">
              {{ m.version }} (ID: {{ m.ml_model_id }}) {{ m.active ? '🔥' : '' }}
            </option>
          </select>
        </div>
        <div class="col">
          <label>Model B</label>
          <select v-model="compareModelB" class="form-select">
            <option v-for="m in models" :key="m.ml_model_id" :value="m.ml_model_id">
              {{ m.version }} (ID: {{ m.ml_model_id }}) {{ m.active ? '🔥' : '' }}
            </option>
          </select>
        </div>
      </div>

      <div class="d-flex justify-content-end mb-3">
        <button class="btn btn-primary" @click="fetchCompare" :disabled="comparing">
          {{ comparing ? 'Comparing...' : 'Compare' }}
        </button>
      </div>

      <div v-if="compareResult" class="mt-3">
        <h6>Metrics</h6>
        <table class="table table-sm">
          <tr v-for="(value, key) in compareResult.diff.metric_diff" :key="key">
            <td><strong>{{ key }}</strong></td>
            <td>{{ compareResult.model_a.metrics[key]?.toFixed(6) }}</td>
            <td>→</td>
            <td>{{ compareResult.model_b.metrics[key]?.toFixed(6) }}</td>
            <td :class="value >= 0 ? 'text-success' : 'text-danger'">
              {{ value >= 0 ? '+' : '' }}{{ value.toFixed(6) }}
            </td>
          </tr>
        </table>

        <h6>Features</h6>
        <div class="row">
          <div class="col">
            <strong>Only in A:</strong>
            <ul>
              <li v-for="f in compareResult.diff.features_diff.only_in_a" :key="f">{{ f }}</li>
              <li v-if="compareResult.diff.features_diff.only_in_a?.length === 0" class="text-muted">—</li>
            </ul>
          </div>
          <div class="col">
            <strong>Only in B:</strong>
            <ul>
              <li v-for="f in compareResult.diff.features_diff.only_in_b" :key="f">{{ f }}</li>
              <li v-if="compareResult.diff.features_diff.only_in_b?.length === 0" class="text-muted">—</li>
            </ul>
          </div>
          <div class="col">
            <strong>Common Features:</strong>
            <ul>
              <li v-for="f in compareResult.diff.features_diff.common" :key="f">{{ f }}</li>
            </ul>
          </div>
        </div>

        <p><strong>Dataset equal:</strong> {{ compareResult.diff.dataset_equal ? 'Yes' : 'No' }}</p>
      </div>

      <div class="d-flex justify-content-end mt-3 pt-3 border-top">
        <button class="btn btn-secondary" @click="showCompareModal = false">
          Close
        </button>
      </div>
    </div>
  </div>

</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
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
import { getActivationHistory } from '../services/api'
import { compareModels } from '../services/api'


interface ActivationHistoryItem {
  id: number
  model_id: number
  activated_at: string
  activated_by: string
}

const models = ref<ModelItem[]>([])
const fileInput = ref<HTMLInputElement | null>(null)

const uploading = ref(false)
const training = ref(false)

const uploadResult = ref<any>(null)

const selectedModelId = ref<number | null>(null)

const showTrainModal = ref(false)
const showActivateModal = ref(false)
const showDeactivateModal = ref(false)
const selectedModelForActivation = ref<string>('')
const selectedModelForDeactivation = ref<string>('')

// ===== DELETE MODAL =====
const showDeleteModal = ref(false)
const modelToDelete = ref<number | null>(null)

// ===== MODELS ACTIVATION HISTORY MODAL =====
const showHistory = ref(false)
const history = ref<ActivationHistoryItem[]>([])

// ===== MODELS COMPARE MODAL =====
const showCompareModal = ref(false)
const compareModelA = ref<number | null>(null)
const compareModelB = ref<number | null>(null)
const compareResult = ref<any>(null)
const comparing = ref(false)


function formatDate(dateStr: string) {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('ru-RU')
}


function goToModel(id: number) {
  selectedModelId.value = id
}


async function loadModels() {
  const response = await getModels()

  models.value = response.data.map((m: any) => ({
    ml_model_id: m.id,
    version: m.version,
    active: m.is_active,
    created_at: m.trained_at || m.created_at
  }))
}


function openTrainModal() {
  showTrainModal.value = true
}

async function handleTrain() {
  try {
    training.value = true

    const response = await trainModel({ promote: false })
    uploadResult.value = response.data
    await loadModels()

  } finally {
    training.value = false
    showTrainModal.value = false
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

async function handleDeactivate(modelId: number) {
  openDeactivateModal(modelId)
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


async function loadHistory() {
  const response = await getActivationHistory()
  history.value = response.data
}


async function fetchCompare() {
  if (!compareModelA.value || !compareModelB.value) {
    console.warn('Both models must be selected')
    return
  }

  comparing.value = true
  compareResult.value = null

  try {
    const response = await compareModels(compareModelA.value, compareModelB.value)
    compareResult.value = response.data

    console.log('Compare result:', compareResult.value)
    console.log('features_diff:', compareResult.value?.features_diff)
    console.log('diff:', compareResult.value?.diff)

  } catch (error) {
    console.error('Compare failed:', error)
    alert('Failed to compare models')
  } finally {
    comparing.value = false
  }
}

function openCompareModal() {
  showCompareModal.value = true
  const activeModel = models.value.find(m => m.active)
  const lastModel = models.value[models.value.length - 1]
  if (activeModel) compareModelA.value = activeModel.ml_model_id
  if (lastModel) compareModelB.value = lastModel.ml_model_id
}


watch(showHistory, async (newVal) => {
  if (newVal) {
    await loadHistory()
  }
})


onMounted(() => {
  loadModels()
})
</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  justify-content: center;
  align-items: center;
}

.modal-box {
  background: white;
  padding: 24px;
  border-radius: 8px;
  width: 400px;
}

.text-success {
  color: #198754 !important;
}

.text-danger {
  color: #dc3545 !important;
}

.text-warning {
  color: #ffc107 !important;
}
</style>