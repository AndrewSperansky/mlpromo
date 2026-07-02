<!-- frontend/src/pages/Models.vue -->

<template>
  <div>
    <div class="mb-4">
      <h2>Model Registry</h2>

      <div class="d-flex mt-4 gap-2 align-items-center">
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

    <!-- Результат обучения  Training Bunner-->
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


    <!-- ================================================================================================== -->
    <!-- =============================  ТАБЛИЦА ModelTable ================================================ -->

    <ModelTable class="mt-4" :models="models" @activate="openActivateModal" @deactivate="openDeactivateModal"
      @rollback="handleRollback" @evaluate="handleEvaluate" @row-click="goToModel" @delete="openDeleteModal" />

    <!-- =============================  ТАБЛИЦА ModelTable ================================================ -->
    <!-- ================================================================================================== -->
    

    <button class="btn btn-sm btn-outline-info" @click="showHistoryModal = true">
      Show Activation History
    </button>


    <!-- ============================================ -->
    <!-- 🔮 LSTM HITL CARDS                           -->
    <!-- ============================================ -->
    <div class="row mt-4 g-4">
      
      <!-- ---------- LSTM CARD ---------- -->
      <div class="col-md-12">
        <div class="card h-100" :class="lstmStatus.lstm?.is_active ? 'border-success border-2' : 'border-secondary'">
          <div class="card-header d-flex justify-content-between align-items-center"
              :class="lstmStatus.lstm?.is_active ? 'bg-success text-white' : 'bg-secondary text-white'">
            <div>
              <i class="bi bi-cpu me-2"></i>
              <strong>LSTM Model</strong>
              <small class="ms-2 opacity-75">(baseline source)</small>
            </div>
            <span class="badge" :class="lstmStatus.lstm?.is_active ? 'bg-light text-success' : 'bg-light text-secondary'">
              {{ lstmStatus.lstm?.is_active ? '✅ Active' : 'Inactive' }}
            </span>
          </div>
          
          <div class="card-body">
            <!-- Есть LSTM модель -->
            <div v-if="lstmStatus.lstm?.exists">
              <div class="row">
                <div class="col-md-6">
                  <p class="mb-1"><strong>ID:</strong> {{ lstmStatus.lstm.id || '—' }}</p>
                  <p class="mb-1"><strong>Version:</strong> {{ lstmStatus.lstm.version || '—' }}</p>
                  <p class="mb-1">
                    <strong>Val Loss:</strong>
                    <span class="text-primary fw-bold">
                      {{ lstmStatus.lstm.metrics?.val_loss?.toFixed(4) || '—' }}
                    </span>
                  </p>
                </div>
                <div class="col-md-6">
                  <p class="mb-1">
                    <strong>Status:</strong>
                    <span :class="lstmStatus.lstm.is_active ? 'text-success fw-bold' : 'text-warning fw-bold'">
                      {{ lstmStatus.lstm.is_active ? 'Active (baseline)' : 'Candidate' }}
                    </span>
                  </p>
                  <p class="mb-1" v-if="lstmStatus.lstm.activated_at">
                    <strong>Activated:</strong> {{ formatDate(lstmStatus.lstm.activated_at) }}
                  </p>
                  <p class="mb-0" v-if="!lstmStatus.lstm.is_active && lstmStatus.lstm.has_candidate">
                    <span class="badge bg-info">Candidate ready for activation</span>
                  </p>
                </div>
              </div>

              <!-- Кнопки управления -->
              <div class="mt-3 d-flex gap-2 flex-wrap">
                <button 
                  v-if="!lstmStatus.lstm.is_active"
                  class="btn btn-success" 
                  @click="openActivateLSTMModal"
                  :disabled="lstmLoading"
                >
                  <span v-if="lstmLoading" class="spinner-border spinner-border-sm me-1"></span>
                  <i v-else class="bi bi-check-lg me-1"></i>
                  Activate LSTM
                </button>
                
                <button 
                  v-if="lstmStatus.lstm.is_active"
                  class="btn btn-warning" 
                  @click="openDeactivateLSTMModal"
                  :disabled="lstmLoading"
                >
                  <span v-if="lstmLoading" class="spinner-border spinner-border-sm me-1"></span>
                  <i v-else class="bi bi-x-lg me-1"></i>
                  Deactivate LSTM
                </button>
                
                <button 
                  class="btn btn-outline-secondary" 
                  @click="refreshLSTMStatus"
                  :disabled="lstmLoading"
                  title="Refresh status"
                >
                  <i class="bi bi-arrow-repeat"></i>
                </button>
              </div>
            </div>

            <!-- Нет LSTM модели -->
            <div v-else>
              <div class="text-center py-3">
                <i class="bi bi-cpu fs-1 text-muted"></i>
                <p class="text-muted mt-2 mb-3">
                  No LSTM model trained yet.
                </p>
                <button 
                  class="btn btn-primary" 
                  @click="openTrainLSTMModal"
                  :disabled="lstmLoading"
                >
                  <i class="bi bi-rocket-takeoff me-1"></i>
                  Train LSTM
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>


    <!-- ============================================ -->
    <!-- LSTM ACTIVATE MODAL                          -->
    <!-- ============================================ -->
    <div v-if="showActivateLSTMModal" class="modal-backdrop" @click.self="showActivateLSTMModal = false">
      <div class="modal-box" style="width: 500px;">
        <h5 class="text-success">
          <i class="bi bi-check-circle-fill me-2"></i>
          Activate LSTM Model
        </h5>
        <p>Are you sure you want to activate LSTM as baseline source?</p>
        
        <div class="alert alert-info mt-2">
          <i class="bi bi-info-circle-fill me-2"></i>
          <strong>LSTM will be used for baseline predictions</strong>
          <ul class="mb-0 mt-1 small">
            <li>Will automatically provide baseline for CatBoost</li>
            <li>Can be deactivated at any time</li>
          </ul>
        </div>

        <div v-if="lstmStatus.lstm" class="mt-2">
          <p class="mb-1"><strong>Model ID:</strong> {{ lstmStatus.lstm.id }}</p>
          <p class="mb-1"><strong>Version:</strong> {{ lstmStatus.lstm.version }}</p>
          <p class="mb-0"><strong>Val Loss:</strong> {{ lstmStatus.lstm.metrics?.val_loss?.toFixed(4) || '—' }}</p>
        </div>

        <div class="mt-3 d-flex justify-content-end gap-2">
          <button class="btn btn-secondary" @click="showActivateLSTMModal = false">Cancel</button>
          <button class="btn btn-success" @click="confirmActivateLSTM" :disabled="lstmLoading">
            <span v-if="lstmLoading" class="spinner-border spinner-border-sm me-1"></span>
            <i v-else class="bi bi-check-lg me-1"></i>
            Activate
          </button>
        </div>
      </div>
    </div>

    <!-- ============================================ -->
    <!-- LSTM DEACTIVATE MODAL                        -->
    <!-- ============================================ -->
    <div v-if="showDeactivateLSTMModal" class="modal-backdrop" @click.self="showDeactivateLSTMModal = false">
      <div class="modal-box" style="width: 500px;">
        <h5 class="text-warning">
          <i class="bi bi-exclamation-triangle-fill me-2"></i>
          Deactivate LSTM Model
        </h5>
        <p>Are you sure you want to deactivate LSTM?</p>
        
        <div class="alert alert-warning mt-2">
          <i class="bi bi-info-circle-fill me-2"></i>
          <strong>CatBoost will be used for baseline</strong>
          <ul class="mb-0 mt-1 small">
            <li>LSTM will no longer provide baseline</li>
            <li>Manual baseline will be used</li>
            <li>Can be reactivated at any time</li>
          </ul>
        </div>

        <div class="mt-3 d-flex justify-content-end gap-2">
          <button class="btn btn-secondary" @click="showDeactivateLSTMModal = false">Cancel</button>
          <button class="btn btn-warning" @click="confirmDeactivateLSTM" :disabled="lstmLoading">
            <span v-if="lstmLoading" class="spinner-border spinner-border-sm me-1"></span>
            <i v-else class="bi bi-x-lg me-1"></i>
            Deactivate
          </button>
        </div>
      </div>
    </div>

    <!-- ============================================ -->
    <!-- LSTM TRAIN MODAL (заглушка)                 -->
    <!-- ============================================ -->
    <div v-if="showTrainLSTMModal" class="modal-backdrop" @click.self="showTrainLSTMModal = false">
      <div class="modal-box" style="width: 550px;">
        <h5>
          <i class="bi bi-rocket-takeoff me-2"></i>
          Train LSTM Model
        </h5>
        <p>Train unified LSTM model on all SKUs.</p>
        
        <div class="alert alert-info mt-2">
          <i class="bi bi-info-circle-fill me-2"></i>
          <strong>Training parameters:</strong>
          <ul class="mb-0 mt-1 small">
            <li>All SKUs unified model</li>
            <li>Embeddings for SKU, store, category</li>
            <li>Will be saved as candidate</li>
          </ul>
        </div>

        <div class="mt-3 d-flex justify-content-end gap-2">
          <button class="btn btn-secondary" @click="showTrainLSTMModal = false">Cancel</button>
          <button class="btn btn-primary" @click="confirmTrainLSTM" :disabled="lstmLoading">
            <span v-if="lstmLoading" class="spinner-border spinner-border-sm me-1"></span>
            <i v-else class="bi bi-play-fill me-1"></i>
            Start Training
          </button>
        </div>
      </div>
    </div>

    
    <!-- Остальные модальные окна... -->
    <ActivateModal :show="showActivateModal" :modelId="selectedModelForActivation" @close="showActivateModal = false"
      @confirm="confirmActivate" />

    <DeactivateModal :show="showDeactivateModal" :modelId="selectedModelForDeactivation"
      @close="showDeactivateModal = false" @confirm="confirmDeactivate" />

    <DeleteModal :show="showDeleteModal" :modelId="modelToDelete" @close="showDeleteModal = false"
      @confirm="confirmDelete" />

    <ModelDetailsModal :modelId="selectedModelId" @closed="selectedModelId = null" />

    <CompareModelsModal :show="showCompareModal" :models="models" @close="showCompareModal = false" />

    <ActivationHistoryModal :show="showHistoryModal" @close="showHistoryModal = false" />
  </div>
</template>

<!-- TS -->

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  getModels,
  getLSTMStatus,
  activateLSTM,
  deactivateLSTM,
  deactivateModel,
  uploadModel,
  evaluateModel,
  rollbackModel,
  trainModel,
  deleteModel,
  type ModelItem,
  type LSTMStatusResponse,
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

const models = ref<ModelItem[]>([])
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

  
// ===== LSTM STATE =====
const lstmStatus = ref<LSTMStatusResponse>({
  lstm: {
    exists: false,
    has_candidate: false,
    id: null,
    version: null,
    metrics: null,
    is_active: false,
    activated_at: null,
  },
  catboost: {
    id: null,
    version: null,
    metrics: null,
    is_active: false,
  }
})
const lstmLoading = ref(false)

// ===== LSTM MODALS =====
const showActivateLSTMModal = ref(false)
const showDeactivateLSTMModal = ref(false)
const showTrainLSTMModal = ref(false)

// ================================
//          FUNCTIONS
// ================================

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
      /* setTimeout(() => {
        trainingResultMessage.value = null
      }, 120000) */
    }
  } catch (error) {
    console.error('Check new data failed:', error)
  } finally {
    checking.value = false
  }
}


/// СРАВНЕНИЕ МОДЕЛЕЙ И РЕНДЕРИНГ БАННЕРА ПОСЛЕ ОБУЧЕНИЯ + График сравнения
async function handleTrain() {
  training.value = true

  try {
    const response = await trainModel({ promote: false })
    console.group("📦 MODELS.VUE")
    console.log("Full response:", response)
    console.log("Response.data:", response.data)
    console.log("Comparison:", response.data?.comparison)
    console.log("Model ID:", response.data?.model_id)
    console.groupEnd()
    uploadResult.value = response.data

    // Получаем comparison из ответа
    const comparison = response.data.comparison
    console.log('🔍 COMPARISON DATA:', JSON.stringify(comparison, null, 2))

    if (comparison) {
      trainingResultComparisonData.value = comparison
      trainingResultComparison.value = true
      console.log('📊 Comparison data saved for chart:', comparison)
    }

    // Получаем model_id из ответа
    const newModelId = response.data.model_id

    if (comparison && newModelId) {
      const rmseOld = comparison.current_metrics?.rmse ?? null
      const rmseNew = comparison.candidate_metrics?.rmse ?? null
      const isBetter = comparison.is_better ?? false
      const improvement = comparison.improvement_percent ?? 0

      if (isBetter) {
        // Метрики улучшились — активируем автоматически
        await api.post(`/ml/models/${newModelId}/activate`)
        trainingResultType.value = 'success'
        trainingResultTitle.value = '✅ Model Auto-Activated'
        trainingResultMessage.value = `New model (ID: ${newModelId}) activated automatically.`
        trainingResultDetails.value = `RMSE: ${rmseOld?.toFixed(6) || '?'} → ${rmseNew?.toFixed(6) || '?'} (improved by ${Math.abs(improvement).toFixed(1)}%)`
      } else {
        // Метрики хуже — не активируем
        trainingResultType.value = 'warning'
        trainingResultTitle.value = '⚠️ Model Trained but Not Activated'
        trainingResultMessage.value = `New model (ID: ${newModelId}) has worse metrics.`
        trainingResultDetails.value = `RMSE: ${rmseOld?.toFixed(6) || '?'} → ${rmseNew?.toFixed(6) || '?'} (worsened by ${Math.abs(improvement).toFixed(1)}%)`
      }
    } else if (!models.value.find(m => m.active) && newModelId) {
      // Первая модель — активируем
      await api.post(`/ml/models/${newModelId}/activate`)
      trainingResultType.value = 'success'
      trainingResultTitle.value = '✅ First Model Activated'
      trainingResultMessage.value = `Model (ID: ${newModelId}) activated as first model.`
      trainingResultDetails.value = `RMSE: ${response.data.metrics?.rmse?.toFixed(6) || 'N/A'}`
    } else {
      // Нет comparison — просто показываем результат
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

// ===== LSTM FUNCTIONS =====
async function refreshLSTMStatus() {
  try {
    const response = await getLSTMStatus()
    lstmStatus.value = response.data
    console.log('🔄 LSTM status refreshed:', lstmStatus.value)
  } catch (error) {
    console.error('Failed to get LSTM status:', error)
  }
}

function openActivateLSTMModal() {
  showActivateLSTMModal.value = true
}

async function confirmActivateLSTM() {
  lstmLoading.value = true
  try {
    await activateLSTM()
    await refreshLSTMStatus()
    showActivateLSTMModal.value = false
    alert('✅ LSTM model activated as baseline source!')
  } catch (error: any) {
    alert('❌ Failed to activate LSTM: ' + (error.response?.data?.detail || error.message))
  } finally {
    lstmLoading.value = false
  }
}

function openDeactivateLSTMModal() {
  showDeactivateLSTMModal.value = true
}

async function confirmDeactivateLSTM() {
  lstmLoading.value = true
  try {
    await deactivateLSTM()
    await refreshLSTMStatus()
    showDeactivateLSTMModal.value = false
    alert('✅ LSTM model deactivated.')
  } catch (error: any) {
    alert('❌ Failed to deactivate LSTM: ' + (error.response?.data?.detail || error.message))
  } finally {
    lstmLoading.value = false
  }
}

function openTrainLSTMModal() {
  showTrainLSTMModal.value = true
}

async function confirmTrainLSTM() {
  lstmLoading.value = true
  try {
    // TODO: Реализовать вызов /ml/torch/train/lstm/unified
    // Пока заглушка
    alert('LSTM training will be implemented soon!')
    showTrainLSTMModal.value = false
  } catch (error) {
    console.error('LSTM training failed:', error)
  } finally {
    lstmLoading.value = false
  }
}

// ===== FORMAT DATE =====
function formatDate(dateStr: string) {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('ru-RU')
}

onMounted(() => {
  refreshLSTMStatus()
  loadModels()
})
</script>