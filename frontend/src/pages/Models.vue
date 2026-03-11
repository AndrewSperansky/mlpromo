<!-- frontend/src/pages/Models.vue -->

<template>
  <div>
    <!-- ===== HEADER ===== -->
    <div class="mb-4">
      <!-- ROW 1 -->
      <div class="mb-6">
        <h2>Model Registry</h2>
      </div>

      <!-- ROW 2 -->
      <div class="d-flex mt-4 gap-2 align-items-center">
        <!-- DATASET SELECT -->
        <select v-model="selectedDataset" class="form-select w-auto">
          <option disabled value="">Select Dataset</option>
          <option v-for="d in datasets" :key="d.id" :value="d.id">
            {{ d.id }}
          </option>
        </select>

        <!-- CHECKBOX TRAIN ON ALL -->
        <div class="form-check">
          <input type="checkbox" class="form-check-input" id="trainAllCheckbox" v-model="trainOnAll"
            :disabled="training">
          <label class="form-check-label" for="trainAllCheckbox">
            Train on all datasets
          </label>
        </div>

        <!-- TRAIN BUTTON -->
        <button class="btn btn-primary" :disabled="training || (!selectedDataset && !trainOnAll)"
          @click="openTrainModal">
          {{ training ? 'Training...' : 'Train Model' }}
        </button>

        <!-- UPLOAD MODEL -->
        <input type="file" ref="fileInput" accept=".zip" class="d-none" @change="handleFileSelect" />
        <button class="btn btn-success" :disabled="uploading" @click="triggerFileInput">
          {{ uploading ? 'Uploading...' : 'Upload Model' }}
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
  <ModelTable class="mt-4" :models="models" @activate="openActivateModal" @rollback="handleRollback"
    @evaluate="handleEvaluate" @row-click="goToModel" @delete="openDeleteModal" />

  <!-- ===== TRAIN MODAL ===== -->
  <div v-if="showTrainModal" class="modal-backdrop">
    <div class="modal-box">
      <h5>Confirm Training</h5>
      <p>Train model using dataset:</p>
      <strong>{{ selectedDataset }}</strong>

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
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
// import { useRouter } from 'vue-router'
import {
  getModels,
  activateModel,
  uploadModel,
  evaluateModel,
  rollbackModel,
  trainModel,
  fetchDatasets,
  deleteModel,
  type ModelItem,
  type TrainModelParams  // ← ИМПОРТИРОВАНО!
} from '../services/api'
import ModelTable from '../components/ModelTable.vue'
import ModelDetailsModal from "@/components/ModelDetailsModal.vue"
import { type Dataset } from '../services/api'


function goToModel(id: number) {
  selectedModelId.value = id
}

const models = ref<ModelItem[]>([])
const datasets = ref<Dataset[]>([])
const selectedDataset = ref<string>('')
const trainOnAll = ref(false)

const fileInput = ref<HTMLInputElement | null>(null)

const uploading = ref(false)
const training = ref(false)

const uploadResult = ref<any>(null)

const selectedModelId = ref<number | null>(null)

const showTrainModal = ref(false)
const showActivateModal = ref(false)
const selectedModelForActivation = ref<string>('')


// ===== DELETE MODAL =====
const showDeleteModal = ref(false)
const modelToDelete = ref<number | null>(null)

async function loadModels() {
  const response = await getModels()
  models.value = response.data
}

async function loadDatasets() {
  const response = await fetchDatasets()
  console.log('📊 Datasets loaded:', response.data)
  datasets.value = response.data
}

function openTrainModal() {
  if (!selectedDataset.value && !trainOnAll.value) return
  showTrainModal.value = true
}

async function handleTrain() {
  try {
    training.value = true

    const params: TrainModelParams = {
      promote: false
    }

    if (trainOnAll.value) {
      params.train_on_all = true
    } else {
      params.dataset_version_id = selectedDataset.value
    }

    const response = await trainModel(params)
    uploadResult.value = response.data
    await loadModels()

  } finally {
    training.value = false
    showTrainModal.value = false
    trainOnAll.value = false
    selectedDataset.value = ''
  }
}

function openActivateModal(modelId: number) {  // ← ИСПРАВЛЕНО: string → number
  selectedModelForActivation.value = modelId.toString()  // ← конвертируем для отображения
  showActivateModal.value = true
}

async function confirmActivate() {
  await activateModel(selectedModelForActivation.value)
  showActivateModal.value = false
  await loadModels()
}

async function handleEvaluate(modelId: number) {
  const response = await evaluateModel(modelId.toString())
  uploadResult.value = response.data
}

async function handleRollback(modelId: number) {
  await rollbackModel(modelId.toString())
  await loadModels()
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
  loadDatasets()
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
</style>