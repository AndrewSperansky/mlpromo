<!-- frontend/src/pages/Dashboard.vue -->

<template>
  <div>
    <h2 class="mb-4">System Dashboard</h2>

    <!-- ===== CARDS ЗДОРОВЬЯ КОНТЕЙНЕРОВ ===== -->
    <div class="row g-3 mb-4">
      <div v-for="(container, name) in containers" :key="name" class="col-md-3 col-lg-2">
        <div class="card h-100 border-0 shadow-sm" :class="getContainerCardClass(container)">
          <div class="card-body p-3">
            <div class="d-flex justify-content-between align-items-start">
              <div class="overflow-hidden">
                <h6 class="text-muted mb-1 small text-truncate" :title="name">
                  {{ formatContainerName(name) }}
                </h6>
                <h5 class="mb-0">
                  <span :class="getContainerStatusClass(container)">
                    {{ getContainerStatusText(container) }}
                  </span>
                </h5>
              </div>
              <div class="rounded-circle p-2" :class="getContainerBgClass(container)">
                <i :class="getContainerIcon(container)" class="fs-5 text-white"></i>
              </div>
            </div>
            <small class="text-muted mt-2 d-block">
              {{ getContainerUptime(container) }}
            </small>
          </div>
        </div>
      </div>

      <div class="col-md-3 col-lg-2">
        <div class="card h-100 border-0 shadow-sm" :class="healthBorderClass">
          <div class="card-body">
            <div class="d-flex justify-content-between align-items-start">
              <div class="overflow-hidden">
                <h6 class="text-muted mb-1">SYSTEM HEALTH</h6>
                <h5 class="mb-0">
                  <span :class="healthStatusClass">{{ healthStatus }}</span>
                </h5>
              </div>
              <div class="rounded-circle p-2" :class="healthBgClass">
                <i :class="healthIconClass" class="fs-5 text-white"></i>
              </div>
            </div>
            <small class="text-muted mt-2 d-block">Last check: {{ formatTime(containersTimestamp) }}</small>
          </div>
        </div>
      </div>
    </div>

    <!-- Остальные карточки здоровья системы -->
    <div class="row g-3 mb-4">
      <!-- Model Status -->
      <div class="col-md-4">
        <div class="card h-100 border-0 shadow-sm">
          <div class="card-body">
            <div class="d-flex justify-content-between align-items-start">
              <div>
                <h6 class="text-muted mb-1">Model Status</h6>
                <h3 class="mb-0">
                  <span :class="overview.runtime.model_loaded ? 'text-success' : 'text-danger'">
                    {{ overview.runtime.model_loaded ? 'Loaded' : 'Not Loaded' }}
                  </span>
                </h3>
                <small class="text-muted">Version: {{ overview.runtime.version || '—' }}</small>
              </div>
              <div class="rounded-circle p-2" :class="overview.runtime.model_loaded ? 'bg-success' : 'bg-danger'">
                <i class="bi bi-cpu fs-4 text-white"></i>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Drift Status -->
      <div class="col-md-4">
        <div class="card h-100 border-0 shadow-sm">
          <div class="card-body">
            <div class="d-flex justify-content-between align-items-start">
              <div>
                <h6 class="text-muted mb-1">Drift Detection</h6>
                <h3 class="mb-0">
                  <span :class="overview.runtime.drift_flag ? 'text-warning' : 'text-success'">
                    {{ overview.runtime.drift_flag ? 'Drift Detected' : 'Stable' }}
                  </span>
                </h3>
                <small class="text-muted">SHAP & Data drift monitoring</small>
              </div>
              <div class="rounded-circle p-2" :class="overview.runtime.drift_flag ? 'bg-warning' : 'bg-success'">
                <i class="bi bi-graph-up fs-4 text-white"></i>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Freeze Status -->
      <div class="col-md-4">
        <div class="card h-100 border-0 shadow-sm">
          <div class="card-body">
            <div class="d-flex justify-content-between align-items-start">
              <div>
                <h6 class="text-muted mb-1">Promotions</h6>
                <h3 class="mb-0">
                  <span :class="overview.runtime.freeze_flag ? 'text-warning' : 'text-success'">
                    {{ overview.runtime.freeze_flag ? 'Frozen' : 'Active' }}
                  </span>
                </h3>
                <small class="text-muted">Auto-promotion is {{ overview.runtime.freeze_flag ? 'disabled' : 'enabled' }}</small>
              </div>
              <div class="rounded-circle p-2" :class="overview.runtime.freeze_flag ? 'bg-warning' : 'bg-success'">
                <i class="bi bi-rocket-takeoff fs-4 text-white"></i>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Drift & Coverage Chart -->
    <DriftCoverageChart />

    <!-- ===== TRAINING CURVE CHARTS ===== -->
    <div class="row g-3 mb-4">
      <div class="col-md-12">
        <div class="card border-0 shadow-sm">
          <div class="card-header bg-white border-0">
            <h6 class="mb-0">
              <i class="bi bi-graph-up me-2"></i>Training RMSE
            </h6>
          </div>
          <div class="card-body">
            <canvas id="trainChart" ref="trainChartRef" height="120"></canvas>
          </div>
        </div>
      </div>

      <div class="col-md-12 mt-4">
        <div class="card border-0 shadow-sm">
          <div class="card-header bg-white border-0">
            <h6 class="mb-0">
              <i class="bi bi-graph-down me-2"></i>Validation RMSE
            </h6>
          </div>
          <div class="card-body">
            <canvas id="valChart" ref="valChartRef" height="120"></canvas>
          </div>
        </div>
      </div>
    </div>

    <!-- Best iteration info -->
    <div v-if="trainingData?.best_iteration" class="text-muted small mb-4">
      <i class="bi bi-info-circle me-1"></i>
      Best iteration: {{ trainingData.best_iteration }} (Best RMSE: {{ trainingData.best_val_rmse?.toFixed(6) }})
    </div>

    <!-- ===== LSTM TRAINING CHART ===== -->

    <div class="row mt-4">
      <div class="col-md-12">
        <LSTMTrainingChart
          :data="lstmTrainingData"
          title="LSTM Training"
          model-type="LSTM"
          :loading="lstmTrainingData.loading"
          :hint="lstmTrainingData.message || 'Train LSTM model to see learning curve'"
        />
      </div>
    </div>


    <!-- ===== PERFORMANCE CARDS ===== -->
    <div class="row g-3 mb-4">
      <div class="col-md-4">
        <div class="card h-100 border-0 shadow-sm">
          <div class="card-body">
            <h6 class="text-muted mb-2"><i class="bi bi-stopwatch me-1"></i> Latency P95</h6>
            <h2 class="mb-0">{{ overview.telemetry.latency_p95_ms?.toFixed(0) ?? '—' }} <small class="fs-6 text-muted">ms</small></h2>
            <small class="text-muted">Last 100 predictions</small>
          </div>
        </div>
      </div>
      <div class="col-md-4">
        <div class="card h-100 border-0 shadow-sm">
          <div class="card-body">
            <h6 class="text-muted mb-2"><i class="bi bi-bar-chart-steps me-1"></i> Total Predictions</h6>
            <h2 class="mb-0">{{ overview.telemetry.predictions_count || 0 }}</h2>
            <small class="text-muted">Since last restart</small>
          </div>
        </div>
      </div>
      <div class="col-md-4">
        <div class="card h-100 border-0 shadow-sm">
          <div class="card-body">
            <h6 class="text-muted mb-2"><i class="bi bi-exclamation-triangle me-1"></i> Errors</h6>
            <h2 class="mb-0" :class="(overview.telemetry.errors_count || 0) > 0 ? 'text-danger' : ''">
              {{ overview.telemetry.errors_count || 0 }}
            </h2>
            <small class="text-muted">Failed predictions</small>
          </div>
        </div>
      </div>
    </div>

    <!-- ===== ALERTS SECTION ===== -->
    <div v-if="overview.errors.length || overview.warnings.length" class="row g-3 mb-4">
      <div v-if="overview.errors.length" class="col-md-6">
        <div class="card border-danger shadow-sm">
          <div class="card-header bg-danger text-white">
            <i class="bi bi-x-circle-fill me-2"></i> Errors
          </div>
          <div class="card-body">
            <ul class="mb-0">
              <li v-for="(err, idx) in overview.errors" :key="idx">{{ err }}</li>
            </ul>
          </div>
        </div>
      </div>
      <div v-if="overview.warnings.length" class="col-md-6">
        <div class="card border-warning shadow-sm">
          <div class="card-header bg-warning text-dark">
            <i class="bi bi-exclamation-triangle-fill me-2"></i> Warnings
          </div>
          <div class="card-body">
            <ul class="mb-0">
              <li v-for="(warn, idx) in overview.warnings" :key="idx">{{ warn }}</li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <!-- ===== FOOTER ===== -->
    <div class="text-muted text-end mt-3 small">
      Last updated: {{ formatDate(overview.timestamp) }}
    </div>
  </div>
</template>

<script setup lang="ts">
import Chart from 'chart.js/auto'
import { ref, onMounted, onUnmounted, computed, nextTick } from 'vue'
import axios from 'axios'
import { getContainersStatus } from '../services/api'
import DriftCoverageChart from '../components/DriftCoverageChart.vue'
import LSTMTrainingChart from '../components/LSTMTrainingChart.vue'
import { getLSTMTrainingMetrics } from '../services/api'

interface OverviewResponse {
  timestamp: string
  runtime: {
    ml_model_id: string | number | null
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

interface ContainerInfo {
  status: string
  state: string
  health: string
  running: boolean
  healthy: boolean
  started_at: string
  image: string
}

const overview = ref<OverviewResponse>({
  timestamp: '',
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
    errors_count: 0
  },
  errors: [],
  warnings: []
})


const defaultContainer = {
  status: 'running',
  healthy: true,
  state: 'running',
  health: 'healthy',
  running: true,
  started_at: '',
  image: ''
}

const containerNames = [
  'promo_ml_backend',
  'promo_ml_frontend',
  'promo_nginx',
  'promo_redis',
  'promo_redis_exporter',
  'promo_postgres',
  'promo_postgres_exporter',
  'promo_promtail',
  'promo_prometheus',
  'promo_grafana',
  'promo_loki'
]

const containers = ref<Record<string, ContainerInfo>>(
  Object.fromEntries(containerNames.map(name => [name, { ...defaultContainer }]))
)
const containersTimestamp = ref('')
const trainChartRef = ref<HTMLCanvasElement | null>(null)
const valChartRef = ref<HTMLCanvasElement | null>(null)
let trainChartInstance: any = null
let valChartInstance: any = null

const trainingData = ref<{
  iterations: number[];
  train_rmse: number[];
  val_rmse: number[];
  best_iteration: number;
  best_val_rmse: number;
  message?: string;
  error?: string;
} | null>(null)

let intervalId: number | null = null

// Computed для Health Status
const healthStatus = computed(() => {
  const hasErrors = overview.value.errors.length > 0
  const modelLoaded = overview.value.runtime.model_loaded
  const driftDetected = overview.value.runtime.drift_flag

  if (hasErrors) return 'Degraded'
  if (!modelLoaded) return 'Warning'
  if (driftDetected) return 'Attention'
  return 'Healthy'
})

const healthStatusClass = computed(() => {
  const status = healthStatus.value
  if (status === 'Healthy') return 'text-success'
  if (status === 'Warning') return 'text-warning'
  if (status === 'Attention') return 'text-info'
  return 'text-danger'
})

const healthBgClass = computed(() => {
  const status = healthStatus.value
  if (status === 'Healthy') return 'bg-success'
  if (status === 'Warning') return 'bg-warning'
  if (status === 'Attention') return 'bg-info'
  return 'bg-danger'
})

const healthBorderClass = computed(() => {
  const status = healthStatus.value
  if (status === 'Healthy') return 'border-success'
  if (status === 'Warning') return 'border-warning'
  if (status === 'Attention') return 'border-info'
  return 'bg-danger'
})

const healthIconClass = computed(() => {
  const status = healthStatus.value
  if (status === 'Healthy') return 'bi bi-check-lg'
  if (status === 'Warning') return 'bi bi-exclamation-triangle'
  if (status === 'Attention') return 'bi bi-eye'
  return 'bi bi-x-lg'
})

const lstmTrainingData = ref({
  iterations: [],
  train_loss: [],
  val_loss: [],
  best_epoch: null,
  best_val_loss: null,
  total_epochs: 0,
  loading: false,
  message: 'No LSTM training data yet',
})

//  ========================================================
//              ФУНКЦИИ (МЕТОДЫ)
//  ========================================================

// Методы для карточек контейнеров
function formatContainerName(name: string): string {
  return name.replace('promo_', '').replace(/_/g, ' ').toUpperCase()
}

function getContainerStatusText(container: ContainerInfo): string {
  if (container.healthy) return 'Healthy'
  if (container.running && container.health === 'starting') return 'Starting'
  if (container.running) return 'Running'
  if (container.status === 'exited') return 'Stopped'
  if (container.status === 'paused') return 'Paused'
  return container.status
}

function getContainerStatusClass(container: ContainerInfo): string {
  if (container.healthy) return 'text-success'
  if (container.running && container.health === 'starting') return 'text-warning'
  if (container.running) return 'text-primary'
  if (container.status === 'exited') return 'text-danger'
  return 'text-secondary'
}

function getContainerCardClass(container: ContainerInfo): string {
  if (container.healthy) return 'border-success'
  if (container.running && container.health === 'starting') return 'border-warning'
  if (container.running) return 'border-primary'
  if (container.status === 'exited') return 'border-danger'
  return 'border-secondary'
}

function getContainerBgClass(container: ContainerInfo): string {
  if (container.healthy) return 'bg-success'
  if (container.running && container.health === 'starting') return 'bg-warning'
  if (container.running) return 'bg-primary'
  if (container.status === 'exited') return 'bg-danger'
  return 'bg-secondary'
}

function getContainerIcon(container: ContainerInfo): string {
  if (container.healthy) return 'bi bi-check-lg'
  if (container.running && container.health === 'starting') return 'bi bi-hourglass-split'
  if (container.running) return 'bi bi-play-fill'
  if (container.status === 'exited') return 'bi bi-stop-fill'
  return 'bi bi-question-lg'
}

function getContainerUptime(container: ContainerInfo): string {
  if (!container.running || !container.started_at) return 'Starting...'
  const startTime = new Date(container.started_at)
  const now = new Date()
  const diffMs = now.getTime() - startTime.getTime()
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffMinutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60))

  if (diffHours > 0) {
    return `Up ${diffHours}h ${diffMinutes}m`
  }
  return `Up ${diffMinutes}m`
}

async function loadDashboard() {
  try {
    const response = await axios.get('/api/v1/system/overview')
    overview.value = response.data
  } catch (error) {
    console.error('Dashboard load failed', error)
  }
}

async function loadContainersStatus() {
  try {
    const response = await getContainersStatus()
    if (response.data.success) {
      // Обновляем существующие контейнеры, сохраняя структуру
      //containers.value = response.data.containers
      containers.value = { ...containers.value, ...response.data.containers }
      containersTimestamp.value = response.data.timestamp
    } else {
      console.error('Failed to load containers:', response.data.error)
    }
  } catch (error) {
    console.error('Containers status load failed', error)
  }
}

function formatDate(dateStr: string) {
  if (!dateStr) return '—'
  const date = new Date(dateStr)
  return date.toLocaleString('ru-RU')
}

function formatTime(dateStr: string) {
  if (!dateStr) return '—'
  const date = new Date(dateStr)
  return date.toLocaleTimeString('ru-RU')
}

async function loadTrainingMetrics() {
  try {
    const response = await axios.get('/api/v1/ml/training/metrics')
    trainingData.value = response.data

    if (trainingData.value && trainingData.value.iterations?.length > 0) {
      await nextTick()
      renderTrainingCharts()
    }
  } catch (error) {
    console.error('Failed to load training metrics:', error)
  }
}

function renderTrainingCharts() {
  if (!trainingData.value) return

  // Train Chart
  if (trainChartRef.value) {
    if (trainChartInstance) trainChartInstance.destroy()

    const ctx = trainChartRef.value.getContext('2d')
    if (ctx) {
      trainChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
          labels: trainingData.value.iterations,
          datasets: [{
            label: 'Training RMSE',
            data: trainingData.value.train_rmse,
            borderColor: 'rgb(54, 162, 235)',
            backgroundColor: 'rgba(54, 162, 235, 0.1)',
            fill: true,
            tension: 0.4
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: true,
          plugins: {
            tooltip: {
              callbacks: {
                label: (context: any) => `RMSE: ${context.raw.toFixed(6)}`
              }
            }
          },
          scales: {
            y: {
              title: { display: true, text: 'RMSE' }
            },
            x: {
              title: { display: true, text: 'Iteration' }
            }
          }
        }
      })
    }
  }

  // Validation Chart
  if (valChartRef.value) {
    if (valChartInstance) valChartInstance.destroy()

    const ctx = valChartRef.value.getContext('2d')
    if (ctx) {
      valChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
          labels: trainingData.value.iterations,
          datasets: [{
            label: 'Validation RMSE',
            data: trainingData.value.val_rmse,
            borderColor: 'rgb(75, 192, 192)',
            backgroundColor: 'rgba(75, 192, 192, 0.1)',
            fill: true,
            tension: 0.4
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: true,
          plugins: {
            tooltip: {
              callbacks: {
                label: (context: any) => `RMSE: ${context.raw.toFixed(6)}`
              }
            }
          },
          scales: {
            y: {
              title: { display: true, text: 'RMSE' }
            },
            x: {
              title: { display: true, text: 'Iteration' }
            }
          }
        }
      })
    }
  }
}

async function loadLSTMTrainingMetrics() {
  lstmTrainingData.value.loading = true
  try {
    const response = await getLSTMTrainingMetrics()
    lstmTrainingData.value = {
      ...response.data,
      loading: false,
      message: response.data.message || '',
    }
  } catch (error) {
    console.error('Failed to load LSTM training metrics:', error)
    lstmTrainingData.value.loading = false
    lstmTrainingData.value.message = 'Failed to load metrics'
  }
}


onMounted(() => {
  loadDashboard()
  loadContainersStatus()
  loadTrainingMetrics()
  loadLSTMTrainingMetrics()
  intervalId = setInterval(() => {
    loadDashboard()
    loadContainersStatus()
  }, 10000) as unknown as number
})

onUnmounted(() => {
  if (intervalId) {
    clearInterval(intervalId)
  }
})
</script>

<style scoped>
.card {
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15) !important;
}

.bg-success {
  background-color: #198754 !important;
}

.bg-warning {
  background-color: #ffc107 !important;
}

.bg-danger {
  background-color: #dc3545 !important;
}

.bg-info {
  background-color: #0dcaf0 !important;
}

.bg-primary {
  background-color: #0d6efd !important;
}

.bg-secondary {
  background-color: #6c757d !important;
}

.text-success {
  color: #198754 !important;
}

.text-warning {
  color: #ffc107 !important;
}

.text-danger {
  color: #dc3545 !important;
}

.text-info {
  color: #0dcaf0 !important;
}

.text-primary {
  color: #0d6efd !important;
}

.border-success {
  border: 1px solid #198754 !important;
}

.border-warning {
  border: 1px solid #ffc107 !important;
}

.border-danger {
  border: 1px solid #dc3545 !important;
}

.border-primary {
  border: 1px solid #0d6efd !important;
}

.text-truncate {
  max-width: 120px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>