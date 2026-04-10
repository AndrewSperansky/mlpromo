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

    <!-- ===== Conformal Prediction Metrics ===== -->
    <div class="row g-3 mb-4" v-if="conformalMetrics.available">
      <div class="col-md-3">
        <div class="card h-100 border-0 shadow-sm"
          style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
          <div class="card-body text-white">
            <h6 class="card-title mb-2">
              <i class="bi bi-sigma me-1"></i>
              Alpha (α)
            </h6>
            <h2 class="mb-2">{{ conformalMetrics.alpha }}</h2>
            <small class="opacity-75">
              <i class="bi bi-info-circle me-1"></i>
              Уровень ошибки (95% доверительный интервал → 0.05)
            </small>
          </div>
        </div>
      </div>

      <div class="col-md-3">
        <div class="card h-100 border-0 shadow-sm"
          style="background: linear-gradient(135deg, #e96443 0%, #904e95 100%);">
          <div class="card-body text-white">
            <h6 class="card-title mb-2">
              <i class="bi bi-calculator me-1"></i>
              Q-hat (q̂)
            </h6>
            <h2 class="mb-2">{{ conformalMetrics.q_hat?.toFixed(6) ?? '—' }}</h2>
            <small class="opacity-75">
              <i class="bi bi-info-circle me-1"></i>
              Квантиль оценок несоответствия (Nonconformity scores)
            </small>
          </div>
        </div>
      </div>

      <div class="col-md-3">
        <div class="card h-100 border-0 shadow-sm"
          style="background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);">
          <div class="card-body text-white">
            <h6 class="card-title mb-2">
              <i class="bi bi-database me-1"></i>
              Calibration Size
            </h6>
            <h2 class="mb-2">{{ conformalMetrics.calibration_size }}</h2>
            <small class="opacity-75">
              <i class="bi bi-info-circle me-1"></i>
              Размер калибровочной выборки (20% от данных)
            </small>
          </div>
        </div>
      </div>

      <div class="col-md-3">
        <div class="card h-100 border-0 shadow-sm"
          style="background: linear-gradient(135deg, #134e5e 0%, #71b280 100%);">
          <div class="card-body text-white">
            <h6 class="card-title mb-2">
              <i class="bi bi-arrows-angle-expand me-1"></i>
              Interval Width
            </h6>
            <h2 class="mb-2">{{ conformalMetrics.interval_width?.toFixed(4) ?? '—' }}</h2>
            <small class="opacity-75">
              <i class="bi bi-info-circle me-1"></i>
              Ширина доверительного интервала (2 × q̂)
            </small>
          </div>
        </div>
      </div>
    </div>

    <!-- Пример интерпретации -->
    <div class="row g-3 mb-4" v-if="conformalMetrics.available && conformalMetrics.q_hat">
      <div class="col-md-12">
        <div class="card border-0 shadow-sm bg-light">
          <div class="card-body">
            <h6 class="mb-2">
              <i class="bi bi-graph-up me-2 text-info"></i>
              Интерпретация
            </h6>
            <p class="mb-1">
              <strong>Доверительный интервал:</strong>
              [k_uplift - q̂, k_uplift + q̂] = k_uplift ± {{ conformalMetrics.q_hat?.toFixed(4) }}
            </p>
            <p class="mb-0 text-muted small">
              <i class="bi bi-lightbulb me-1"></i>
              Пример: при прогнозе k_uplift = 1.76,
              95% доверительный интервал составляет
              [{{ (1.76 - (conformalMetrics.q_hat || 0)).toFixed(4) }},
              {{ (1.76 + (conformalMetrics.q_hat || 0)).toFixed(4) }}]
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- ===== Operational Overview ===== -->
    <div class="row g-3 mb-4">
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
      <div class="col-md-4">
        <button class="btn btn-warning w-100" @click="freeze" :disabled="loading">
          Freeze
        </button>
      </div>

      <div class="col-md-4">
        <button class="btn btn-success w-100" @click="unfreeze" :disabled="loading">
          Unfreeze
        </button>
      </div>

      <div class="col-md-4">
        <button class="btn btn-danger w-100" @click="clearDrift" :disabled="loading">
          Clear Drift
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
import { ref, onMounted, onUnmounted } from "vue"
import api from "../services/api"

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

interface ConformalMetrics {
  available: boolean
  alpha: number
  q_hat: number | null
  calibration_size: number
  interval_width: number | null
}

const conformalMetrics = ref<ConformalMetrics>({
  available: false,
  alpha: 0.05,
  q_hat: null,
  calibration_size: 0,
  interval_width: null
})

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
const showOverviewDebug = ref(false)
const showRuntimeDebug = ref(false)
const loading = ref(false)

let intervalId: number | null = null

async function loadOverview() {
  try {
    const res = await api.get("/system/overview")
    overview.value = res.data
  } catch (error) {
    console.error("Failed to load overview:", error)
  }
}

async function loadRuntimeState() {
  try {
    const res = await api.get("/system/runtime-state")
    runtimeState.value = res.data
  } catch (error) {
    console.error("Failed to load runtime state:", error)
  }
}

async function refreshAll() {
  loading.value = true
  try {
    await Promise.all([
      loadOverview(),
      loadRuntimeState(),
      loadConformalMetrics()
    ])
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

async function loadConformalMetrics() {
  try {
    const res = await api.get("/system/runtime-state")
    const runtime = res.data

    if (runtime.conformal_q_hat || runtime.conformal) {
      const q_hat = runtime.conformal_q_hat || runtime.conformal?.q_hat
      const alpha = runtime.conformal?.alpha || 0.05
      const calibration_size = runtime.conformal?.calibration_size || 0
      const interval_width = runtime.conformal?.interval_width || (q_hat ? q_hat * 2 : null)

      conformalMetrics.value = {
        available: true,
        alpha: alpha,
        q_hat: q_hat,
        calibration_size: calibration_size,
        interval_width: interval_width
      }
    } else {
      conformalMetrics.value.available = false
    }
  } catch (error) {
    console.error("Failed to load conformal metrics:", error)
    conformalMetrics.value.available = false
  }
}

function formatDate(dateStr: string) {
  if (!dateStr) return '—'
  const date = new Date(dateStr)
  return date.toLocaleString('ru-RU')
}

onMounted(() => {
  refreshAll()
  intervalId = setInterval(() => {
    refreshAll()
  }, 30000) as unknown as number
})

onUnmounted(() => {
  if (intervalId) {
    clearInterval(intervalId)
  }
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
</style>