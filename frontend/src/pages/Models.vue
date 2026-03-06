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
      <div class="d-flex mt-4 gap-2">

        <!-- DATASET SELECT -->
        <select v-model="selectedDataset" class="form-select w-auto">
          <option disabled value="">Select Dataset</option>
          <option v-for="d in datasets" :key="d.dataset_version_id" :value="d.dataset_version_id">
            {{ d.dataset_version_id }}
          </option>
        </select>

        <!-- TRAIN -->
        <button class="btn btn-primary" :disabled="training || !selectedDataset" @click="openTrainModal">
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
    @evaluate="handleEvaluate" @row-click="goToModel" />

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
  trainModel,
  fetchDatasets
} from '../services/api'

import ModelTable, { type ModelItem } from '../components/ModelTable.vue'

const router = useRouter()

function goToModel(id: string) {
  router.push(`/models/${id}`)
}

// Убираем локальное объявление ModelItem
/* interface ModelItem {
  ml_model_id: string
  version: string
  active: boolean
  created_at: string
} */

interface DatasetItem {
  dataset_version_id: string
}

const models = ref<ModelItem[]>([])    // используем импортированный тип
const datasets = ref<DatasetItem[]>([])
const selectedDataset = ref<string>('')

const fileInput = ref<HTMLInputElement | null>(null)

const uploading = ref(false)
const training = ref(false)

const uploadResult = ref<any>(null)

const showTrainModal = ref(false)
const showActivateModal = ref(false)
const selectedModelForActivation = ref<string>('')

async function loadModels() {
  const response = await getModels()
  models.value = response.data
}

async function loadDatasets() {
  const response = await fetchDatasets()

  // 🔥 Трансформируем данные: id → dataset_version_id
  datasets.value = response.data.map((item: any) => ({
    dataset_version_id: item.id  // ← переименовываем поле
  }))

  console.log('Трансформированные datasets:', datasets.value)
}

function openTrainModal() {
  if (!selectedDataset.value) return
  showTrainModal.value = true
}

async function handleTrain() {
  try {
    training.value = true

    const response = await trainModel({
      dataset_version_id: selectedDataset.value
    })

    uploadResult.value = response.data

    await loadModels()

  } finally {
    training.value = false
    showTrainModal.value = false
  }
}

function openActivateModal(modelId: string) {
  selectedModelForActivation.value = modelId
  showActivateModal.value = true
}

async function confirmActivate() {
  await activateModel(selectedModelForActivation.value)
  showActivateModal.value = false
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