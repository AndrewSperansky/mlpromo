<template>
  <div>
    <div class="mb-4">
      <h2>Model Registry</h2>

      <div class="d-flex mt-4 gap-2 align-items-center">
        <!-- ===== ВКЛАДКИ ===== -->
        <div class="btn-group me-auto" role="group">
          <button 
            type="button" 
            class="btn" 
            :class="activeTab === 'catboost' ? 'btn-primary' : 'btn-outline-secondary'"
            @click="activeTab = 'catboost'; loadModels()"
          >
            <i class="bi bi-tree-fill me-1"></i>
            CatBoost
          </button>
          <button 
            type="button" 
            class="btn" 
            :class="activeTab === 'pytorch' ? 'btn-primary' : 'btn-outline-secondary'"
            @click="activeTab = 'pytorch'; loadModels()"
          >
            <i class="bi bi-cpu me-1"></i>
            PyTorch LSTM
          </button>
          <button 
            type="button" 
            class="btn" 
            :class="activeTab === 'all' ? 'btn-primary' : 'btn-outline-secondary'"
            @click="activeTab = 'all'; loadModels()"
          >
            <i class="bi bi-diagram-3 me-1"></i>
            All Models
          </button>
        </div>

        <button class="btn btn-primary" :disabled="training" @click="handleTrain">
          {{ training ? 'Training...' : 'Train Model' }}
        </button>

        <input type="file" ref="fileInput" accept=".zip" class="d-none" @change="handleFileSelect" />
        <button class="btn btn-success" :disabled="uploading" @click="triggerFileInput">
          {{ uploading ? 'Uploading...' : 'Upload Model' }}
        </button>

        <button class="btn btn-info" @click="showCompareModal = true">
          Compare Models
        </button>

        <button class="btn btn-outline-secondary" @click="checkNewData" :disabled="checking">
          <span v-if="checking" class="spinner-border spinner-border-sm me-1"></span>
          <i v-else class="bi bi-search me-1"></i>
          {{ checking ? 'Checking...' : 'Check New Data' }}
        </button>
      </div>
    </div>

    <!-- Новые данные (жёлтая карточка) -->
    <NewDataAlert v-if="showNewDataAlert" :newRowsCount="newRowsCount" :message="newDataMessage"
      @close="showNewDataAlert = false" />

    <!-- Результат обучения -->
    <NotificationBanner v-if="trainingResultMessage" :type="trainingResultType" :title="trainingResultTitle"
      :message="trainingResultMessage" :details="trainingResultDetails" @close="trainingResultMessage = null" />

    <!-- График сравнения моделей -->
    <ModelCompareChart v-if="trainingResultMessage && trainingResultComparison"
      :comparison="trainingResultComparisonData" />

    <!-- Uploaded Model Metrics -->
    <div v-if="uploadResult" class="alert alert-info alert-dismissible fade show" role="alert">
      <strong>Result:</strong>
      <pre class="mb-0">{{ uploadResult }}</pre>
      <button type="button" class="btn-close" @click="uploadResult = null" aria-label="Close"></button>
    </div>

    <!-- ===== ТАБЛИЦА МОДЕЛЕЙ (с фильтром по активной вкладке) ===== -->
    <ModelTable 
      class="mt-4" 
      :models="filteredModels" 
      :activeTab="activeTab"
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
    <ActivateModal :show="showActivateModal" :modelId="selectedModelForActivation" @close="showActivateModal = false"
      @confirm="confirmActivate" />

    <DeactivateModal :show="showDeactivateModal" :modelId="selectedModelForDeactivation"
      @close="showDeactivateModal = false" @confirm="confirmDeactivate" />

    <DeleteModal :show="showDeleteModal" :modelId="modelToDelete" @close="showDeleteModal = false"
      @confirm="confirmDelete" />

    <ModelDetailsModal :modelId="selectedModelId" @closed="selectedModelId = null" />

    <CompareModelsModal :show="showCompareModal" :models="allModels" @close="showCompareModal = false" />

    <ActivationHistoryModal :show="showHistoryModal" @close="showHistoryModal = false" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  getModels,
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
import ActivateModal from '../components/ActivateModal.vue'
import DeactivateModal from '../components/DeactivateModal.vue'
import DeleteModal from '../components/DeleteModal.vue'
import NotificationBanner from '../components/NotificationBanner.vue'
import NewDataAlert from '../components/NewDataAlert.vue'
import ModelCompareChart from '../components/ModelCompareChart.vue'

const activeTab = ref<'catboost' | 'pytorch' | 'all'>('all')
const fileInput = ref<HTMLInputElement | null>(null)

const uploading = ref(false)
const training = ref(false)
const checking = ref(false)
const uploadResult = ref<any>(null)
const selectedModelId = ref<number | null>(null)

// Уведомления
const showNewDataAlert = ref(false)
const newRowsCount = ref(0)
const newDataMessage = ref('')

const trainingResultMessage = ref<string | null>(null)
const trainingResultType = ref<'success' | 'danger' | 'warning' | 'info'>('info')
const trainingResultTitle = ref('')
const trainingResultDetails = ref('')

const showActivateModal = ref(false)
const showDeactivateModal = ref(false)
const showDeleteModal = ref(false)
const showCompareModal = ref(false)
const showHistoryModal = ref(false)

const selectedModelForActivation = ref<string>('')
const selectedModelForDeactivation = ref<string>('')
const modelToDelete = ref<number | null>(null)

const trainingResultComparison = ref(false)
const trainingResultComparisonData = ref<any>(null)

// ===== ВСЕ МОДЕЛИ (без фильтра) =====
const allModels = ref<ModelItem[]>([])

// ===== ОТФИЛЬТРОВАННЫЕ МОДЕЛИ ПО АКТИВНОЙ ВКЛАДКЕ =====
const filteredModels = computed(() => {
  if (activeTab.value === 'catboost') {
    return allModels.value.filter(m => 
      m.algorithm === 'catboost' || !m.algorithm?.startsWith('pytorch')
    )
  }
  if (activeTab.value === 'pytorch') {
    return allModels.value.filter(m => 
      m.algorithm?.startsWith('pytorch_lstm') || m.algorithm === 'pytorch_lstm_with_embeddings'
    )
  }
  return allModels.value
})

async function loadModels() {
  const response = await getModels()
  // Сохраняем все модели
  allModels.value = response.data.map((m: any) => ({
    ml_model_id: m.id,
    version: m.version,
    active: m.is_active,
    created_at: m.trained_at || m.created_at,
    algorithm: m.algorithm || 'catboost',
    sku_code: m.sku_code, 
    metrics: m.metrics
  }))
}

function goToModel(id: number) {
  selectedModelId.value = id
}

async function checkNewData() {
  checking.value = true
  try {
    const response = await api.post('/system/force-retrain')
    if (response.data.needed) {
      newRowsCount.value = response.data.new_data_count || 0
      newDataMessage.value = response.data.reason || 'New data available for training'
      showNewDataAlert.value = true
    } else {
      trainingResultType.value = 'info'
      trainingResultTitle.value = 'No New Data'
      trainingResultMessage.value = 'Dataset is up to date. No retraining needed.'
      trainingResultDetails.value = ''
    }
  } catch (error) {
    console.error('Check new data failed:', error)
  } finally {
    checking.value = false
  }
}

async function handleTrain() {
  training.value = true

  try {
    const response = await trainModel({ promote: false })
    uploadResult.value = response.data

    const comparison = response.data.comparison
    console.log('🔍 COMPARISON DATA:', JSON.stringify(comparison, null, 2))

    if (comparison) {
      trainingResultComparisonData.value = comparison
      trainingResultComparison.value = true
    }

    const newModelId = response.data.model_id

    if (comparison && newModelId) {
      const rmseOld = comparison.current_metrics?.rmse ?? null
      const rmseNew = comparison.candidate_metrics?.rmse ?? null
      const isBetter = comparison.is_better ?? false
      const improvement = comparison.improvement_percent ?? 0

      if (isBetter) {
        await api.post(`/ml/models/${newModelId}/activate`)
        trainingResultType.value = 'success'
        trainingResultTitle.value = '✅ Model Auto-Activated'
        trainingResultMessage.value = `New model (ID: ${newModelId}) activated automatically.`
        trainingResultDetails.value = `RMSE: ${rmseOld?.toFixed(6) || '?'} → ${rmseNew?.toFixed(6) || '?'} (improved by ${Math.abs(improvement).toFixed(1)}%)`
      } else {
        trainingResultType.value = 'warning'
        trainingResultTitle.value = '⚠️ Model Trained but Not Activated'
        trainingResultMessage.value = `New model (ID: ${newModelId}) has worse metrics.`
        trainingResultDetails.value = `RMSE: ${rmseOld?.toFixed(6) || '?'} → ${rmseNew?.toFixed(6) || '?'} (worsened by ${Math.abs(improvement).toFixed(1)}%)`
      }
    } else if (!allModels.value.find(m => m.active) && newModelId) {
      await api.post(`/ml/models/${newModelId}/activate`)
      trainingResultType.value = 'success'
      trainingResultTitle.value = '✅ First Model Activated'
      trainingResultMessage.value = `Model (ID: ${newModelId}) activated as first model.`
      trainingResultDetails.value = `RMSE: ${response.data.metrics?.rmse?.toFixed(6) || 'N/A'}`
    } else {
      trainingResultType.value = 'info'
      trainingResultTitle.value = 'ℹ️ Model Trained'
      trainingResultMessage.value = `New model (ID: ${newModelId}) created.`
      trainingResultDetails.value = 'Check Models table for details'
    }

    await loadModels()

  } catch (error) {
    console.error('Training failed:', error)
    trainingResultType.value = 'danger'
    trainingResultTitle.value = '❌ Training Failed'
    trainingResultMessage.value = 'Model training failed. Check server logs.'
    trainingResultDetails.value = ''
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
  await deactivateModel(Number(selectedModelForActivation.value))
  showActivateModal.value = false
  await loadModels()
  alert('✅ Model activated successfully!')
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