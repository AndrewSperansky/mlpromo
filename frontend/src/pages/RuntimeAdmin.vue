<!-- frontend/src/pages/RuntimeAdmin.vue -->

<template>
  <div>
    <!-- Заголовок с кнопкой Refresh -->
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h2>Runtime Administration</h2>
      <button class="btn btn-primary" @click="refreshAll" :disabled="loading">
        <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
        <i v-else class="bi bi-arrow-repeat me-2"></i>
        {{ loading ? 'Refreshing...' : 'Refresh' }}
      </button>
    </div>

    <!-- ========================================================= -->
    <!-- ========== RETRAIN RECOMMENDATION CARD (НОВЫЙ) ========= -->
    <!-- ========================================================= -->
    <div v-if="retrainRecommendation.recommended" class="card mb-4 border-warning shadow-sm">
      <div class="card-header bg-warning text-dark d-flex justify-content-between align-items-center">
        <div>
          <i class="bi bi-exclamation-triangle-fill me-2"></i>
          <strong>Retrain Recommendation</strong>
        </div>
        <span class="badge bg-dark" :class="priorityBadgeClass">
          {{ priorityText }}
        </span>
      </div>
      <div class="card-body">
        <div class="row align-items-center">
          <div class="col-md-8">
            <p class="mb-2 fs-5">
              <i class="bi bi-info-circle-fill me-2 text-primary"></i>
              {{ retrainRecommendation.reason }}
            </p>
            <p v-if="retrainRecommendation.recommended_at" class="text-muted small mb-0">
              <i class="bi bi-clock me-1"></i>
              Recommended at: {{ formatDate(retrainRecommendation.recommended_at) }}
            </p>
            
            <!-- Candidate Metrics (если есть) -->
            <div v-if="retrainRecommendation.candidate_metrics" class="mt-3">
              <strong class="text-primary">
                <i class="bi bi-graph-up me-1"></i>Candidate Model Metrics:
              </strong>
              <table class="table table-sm table-bordered mt-2" style="width: auto; background-color: #f8f9fa;">
                <tbody>
                  <tr v-for="(value, key) in retrainRecommendation.candidate_metrics" :key="key">
                    <td class="fw-bold">{{ key }}</td>
                    <td>{{ typeof value === 'number' ? value.toFixed(6) : value }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
          
          <div class="col-md-4 text-end">
            <button 
              class="btn btn-success me-2 px-4" 
              @click="approveRetrain" 
              :disabled="retrainActionLoading"
            >
              <span v-if="retrainActionLoading" class="spinner-border spinner-border-sm me-2"></span>
              <i v-else class="bi bi-check-lg me-2"></i>
              {{ retrainActionLoading ? 'Training...' : 'Approve & Train' }}
            </button>
            <button 
              class="btn btn-outline-secondary" 
              @click="dismissRetrain" 
              :disabled="retrainActionLoading"
            >
              <i class="bi bi-x-lg me-1"></i>
              Dismiss
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ===== Operational Overview ===== -->
    <div class="row g-3 mb-4">
      <!-- Model ID и Version на половинках -->
      <div class="col-md-6">
        <div class="input-group">
          <span class="input-group-text status-label bg-secondary text-light">Model ID</span>
          <input type="text" class="form-control" :value="overview.runtime.ml_model_id ?? '—'" readonly />
        </div>
      </div>

      <div class="col-md-6">
        <div class="input-group">
          <span class="input-group-text status-label bg-secondary text-light">Version</span>
          <input type="text" class="form-control" :value="overview.runtime.version ?? '—'" readonly />
        </div>
      </div>

      <!-- Остальные статусы по 3 колонки -->
      <div class="col-md-3">
        <div class="input-group">
          <span class="input-group-text status-label bg-secondary text-light">Model Loaded</span>
          <input type="text" class="form-control" :value="overview.runtime.model_loaded ? 'Yes' : 'No'"
            :class="overview.runtime.model_loaded ? 'text-success fw-bold' : 'text-danger fw-bold'" readonly />
        </div>
      </div>

      <div class="col-md-3">
        <div class="input-group">
          <span class="input-group-text status-label bg-secondary text-light">Freeze Flag</span>
          <input type="text" class="form-control" :value="overview.runtime.freeze_flag ? 'Frozen' : 'Active'"
            :class="overview.runtime.freeze_flag ? 'text-warning fw-bold' : 'text-success fw-bold'" readonly />
        </div>
      </div>

      <div class="col-md-3">
        <div class="input-group">
          <span class="input-group-text status-label bg-secondary text-light">Drift Flag</span>
          <input type="text" class="form-control" :value="overview.runtime.drift_flag ? 'Drift Detected' : 'No Drift'"
            :class="overview.runtime.drift_flag ? 'text-danger fw-bold' : 'text-success fw-bold'" readonly />
        </div>
      </div>

      <div class="col-md-3">
        <div class="input-group">
          <span class="input-group-text status-label bg-secondary text-light">Retrain Requested</span>
          <input type="text" class="form-control" :value="overview.runtime.retrain_requested ? 'Yes' : 'No'"
            :class="overview.runtime.retrain_requested ? 'text-primary fw-bold' : 'text-secondary fw-bold'" readonly />
        </div>
      </div>
    </div>

    <!-- ===== Controls ===== -->
    <div class="row g-3 mb-4">
      <div class="col-md-3">
        <button class="btn btn-warning w-100" @click="freeze" :disabled="loading">
          Freeze
        </button>
      </div>

      <div class="col-md-3">
        <button class="btn btn-success w-100" @click="unfreeze" :disabled="loading">
          Unfreeze
        </button>
      </div>

      <div class="col-md-3">
        <button class="btn btn-danger w-100" @click="clearDrift" :disabled="loading">
          Clear Drift
        </button>
      </div>

      <div class="col-md-3">
        <button class="btn btn-primary w-100" @click="forceRetrain" :disabled="loading">
          <i class="bi bi-rocket-takeoff me-1"></i>
          Force Retrain Check
        </button>
      </div>
    </div>

    <!-- ===== Telemetry Section ===== -->
    <div class="card shadow-sm mb-4">
      <div class="card-header bg-primary text-white">
        Telemetry
      </div>
      <div class="card-body">
        <div class="row g-3">
          <div class="col-md-4">
            <div class="input-group">
              <span class="input-group-text status-label">Latency P95 (ms)</span>
              <input type="text" class="form-control" :value="overview.telemetry.latency_p95_ms?.toFixed(2) ?? '—'"
                readonly />
            </div>
          </div>
          <div class="col-md-4">
            <div class="input-group">
              <span class="input-group-text status-label">Predictions Count</span>
              <input type="text" class="form-control" :value="overview.telemetry.predictions_count" readonly />
            </div>
          </div>
          <div class="col-md-4">
            <div class="input-group">
              <span class="input-group-text status-label">Errors Count</span>
              <input type="text" class="form-control" :value="overview.telemetry.errors_count"
                :class="overview.telemetry.errors_count > 0 ? 'text-danger fw-bold' : ''" readonly />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ===== Errors & Warnings ===== -->
    <div v-if="overview.errors.length" class="alert alert-danger">
      <h5>Errors</h5>
      <ul class="mb-0">
        <li v-for="(err, idx) in overview.errors" :key="idx">{{ err }}</li>
      </ul>
    </div>

    <div v-if="overview.warnings.length" class="alert alert-warning">
      <h5>Warnings</h5>
      <ul class="mb-0">
        <li v-for="(warn, idx) in overview.warnings" :key="idx">{{ warn }}</li>
      </ul>
    </div>

    <!-- ===== Debug Sections ===== -->
    <div class="row">
      <!-- Overview Debug -->
      <div class="col-md-6">
        <div class="card shadow-sm">
          <div class="card-header d-flex justify-content-between align-items-center bg-secondary text-white">
            <span>Debug Overview</span>
            <button class="btn btn-sm btn-outline-light" @click="showOverviewDebug = !showOverviewDebug">
              {{ showOverviewDebug ? 'Hide' : 'Show' }}
            </button>
          </div>
          <div v-if="showOverviewDebug" class="card-body">
            <pre class="bg-light p-3 small">{{ overview }}</pre>
          </div>
        </div>
      </div>

      <!-- Runtime State Debug -->
      <div class="col-md-6">
        <div class="card shadow-sm">
          <div class="card-header d-flex justify-content-between align-items-center bg-info text-white">
            <span>Debug Runtime State</span>
            <button class="btn btn-sm btn-outline-light" @click="showRuntimeDebug = !showRuntimeDebug">
              {{ showRuntimeDebug ? 'Hide' : 'Show' }}
            </button>
          </div>
          <div v-if="showRuntimeDebug" class="card-body">
            <pre class="bg-light p-3 small">{{ runtimeState }}</pre>
          </div>
        </div>
      </div>
    </div>

    <!-- Timestamp -->
    <div v-if="overview.timestamp" class="text-muted text-end mt-3 small">
      Last updated: {{ formatDate(overview.timestamp) }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from "vue"
import api from "../services/api"

// ===== Types =====
interface OverviewResponse {
  timestamp: string
  runtime: {
    ml_model_id: number | string | null
    version: string | null
    model_loaded: boolean
    freeze_flag: boolean
    drift_flag: boolean
    retrain_requested?: boolean
  }
  telemetry: {
    latency_p95_ms: number | null
    predictions_count: number
    errors_count: number
  }
  errors: string[]
  warnings: string[]
}

interface RuntimeStateResponse {
  status: string
  model_loaded: boolean
  version: string | null
  errors: string[]
  warnings: string[]
  last_drift_flag: boolean
  last_latency_p95: number | null
  last_decision: any
  last_decision_timestamp: string | null
  retrain_requested: boolean
  ml_model_id: number | string
  checked: boolean
  contract: any
  model_path?: string
  feature_order?: string[]
}

interface RetrainRecommendation {
  recommended: boolean
  reason: string | null
  candidate_metrics: Record<string, any> | null
  candidate_id: number | null
  candidate_version: string | null
  recommended_at: string | null
}

// ===== State =====
const overview = ref<OverviewResponse>({
  timestamp: "",
  runtime: {
    ml_model_id: null,
    version: null,
    model_loaded: false,
    freeze_flag: false,
    drift_flag: false,
    retrain_requested: false,
  },
  telemetry: {
    latency_p95_ms: null,
    predictions_count: 0,
    errors_count: 0,
  },
  errors: [],
  warnings: [],
})

const runtimeState = ref<RuntimeStateResponse | null>(null)
const retrainRecommendation = ref<RetrainRecommendation>({
  recommended: false,
  reason: null,
  candidate_metrics: null,
  candidate_id: null,
  candidate_version: null,
  recommended_at: null,
})

const showOverviewDebug = ref(false)
const showRuntimeDebug = ref(false)
const loading = ref(false)
const retrainActionLoading = ref(false)

// ===== Computed =====
const priorityText = computed(() => {
  if (!retrainRecommendation.value.recommended) return ''
  const reason = retrainRecommendation.value.reason || ''
  if (reason.includes('📊') || reason.includes('initial')) return 'High Priority'
  if (reason.includes('⏰')) return 'Medium Priority'
  return 'Info'
})

const priorityBadgeClass = computed(() => {
  if (!retrainRecommendation.value.recommended) return ''
  const reason = retrainRecommendation.value.reason || ''
  if (reason.includes('📊') || reason.includes('initial')) return 'bg-danger'
  if (reason.includes('⏰')) return 'bg-warning'
  return 'bg-info'
})

// ===== Methods =====
async function loadOverview() {
  try {
    const res = await api.get("/system/overview")
    overview.value = res.data
    console.log("📊 Overview loaded:", overview.value)
  } catch (error) {
    console.error("Failed to load overview:", error)
  }
}

async function loadRuntimeState() {
  try {
    const res = await api.get("/system/runtime-state")
    runtimeState.value = res.data
    console.log("🔄 Runtime state loaded:", runtimeState.value)
  } catch (error) {
    console.error("Failed to load runtime state:", error)
  }
}

async function loadRetrainRecommendation() {
  try {
    const res = await api.get("/system/retrain-recommendation")
    retrainRecommendation.value = res.data
    console.log("📢 Retrain recommendation:", retrainRecommendation.value)
  } catch (error) {
    console.error("Failed to load retrain recommendation:", error)
  }
}

async function refreshAll() {
  loading.value = true
  try {
    await Promise.all([
      loadOverview(),
      loadRuntimeState(),
      loadRetrainRecommendation()
    ])
    console.log("✅ All data refreshed")
  } catch (error) {
    console.error("Refresh failed:", error)
  } finally {
    setTimeout(() => {
      loading.value = false
    }, 300)
  }
}

async function freeze() {
  try {
    await api.post("/system/freeze")
    await refreshAll()
  } catch (error) {
    console.error("Freeze failed:", error)
  }
}

async function unfreeze() {
  try {
    await api.post("/system/unfreeze")
    await refreshAll()
  } catch (error) {
    console.error("Unfreeze failed:", error)
  }
}

async function clearDrift() {
  try {
    await api.post("/system/clear-drift")
    await refreshAll()
  } catch (error) {
    console.error("Clear drift failed:", error)
  }
}

async function forceRetrain() {
  try {
    await api.post("/system/force-retrain")
    await refreshAll()
  } catch (error) {
    console.error("Force retrain failed:", error)
  }
}

async function approveRetrain() {
  retrainActionLoading.value = true
  try {
    const response = await api.post("/system/retrain-approve")
    console.log("Retrain approved:", response.data)
    
    // Сбросить рекомендацию на UI
    retrainRecommendation.value.recommended = false
    
    // Показать уведомление
    alert("✅ Training started! New model will be promoted upon completion.")
    
    // Перезагрузить всё через несколько секунд
    setTimeout(() => {
      refreshAll()
    }, 3000)
    
  } catch (error: any) {
    console.error("Failed to approve retrain:", error)
    alert(`❌ Failed to start retraining: ${error.response?.data?.message || error.message}`)
  } finally {
    retrainActionLoading.value = false
  }
}

async function dismissRetrain() {
  retrainActionLoading.value = true
  try {
    const response = await api.post("/system/retrain-dismiss")
    console.log("Retrain dismissed:", response.data)
    
    // Сбросить рекомендацию на UI
    retrainRecommendation.value.recommended = false
    
  } catch (error) {
    console.error("Failed to dismiss retrain:", error)
  } finally {
    retrainActionLoading.value = false
  }
}

function formatDate(dateStr: string) {
  if (!dateStr) return '—'
  const date = new Date(dateStr)
  return date.toLocaleString('ru-RU')
}

// ===== Lifecycle =====
onMounted(() => {
  refreshAll()
  // Автообновление каждые 30 секунд
  setInterval(() => {
    refreshAll()
  }, 30000)
})
</script>

<style scoped>
.status-label {
  min-width: 140px;
  background-color: #f8f9fa;
  font-weight: 500;
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

.text-primary {
  color: #0d6efd !important;
}

.text-secondary {
  color: #6c757d !important;
}

.fw-bold {
  font-weight: 700 !important;
}

.form-control:read-only {
  background-color: #fff;
  opacity: 1;
}

.input-group-text {
  justify-content: center;
}

.card.border-warning {
  border-width: 2px;
}

.bg-warning {
  background-color: #ffc107 !important;
}
</style>