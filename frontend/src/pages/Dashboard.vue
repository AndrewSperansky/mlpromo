<!-- frontend\src\pages\Dashboard.vue -->

<template>
  <div>
    <h2 class="mb-4">System Dashboard</h2>

    <!-- ===== Dashboard Cards в одну колонку на всю ширину ===== -->
    <div class="row g-3">

      <!-- Active Model Version -->
      <div class="col-md-12">
        <div class="input-group">
          <span class="input-group-text status-label bg-secondary text-light">Active Model Version</span>
          <input type="text" class="form-control" :value="overview.runtime.version ?? '—'" readonly />
        </div>
      </div>

      <!-- Model Loaded -->
      <div class="col-md-12">
        <div class="input-group">
          <span class="input-group-text status-label bg-secondary text-light">Model Loaded</span>
          <input type="text" class="form-control" :value="overview.runtime.model_loaded ? 'Yes' : 'No'"
            :class="overview.runtime.model_loaded ? 'text-success fw-bold' : 'text-danger fw-bold'" readonly />
        </div>
      </div>

      <!-- Drift Flag -->
      <div class="col-md-12">
        <div class="input-group">
          <span class="input-group-text status-label bg-secondary text-light">Drift Flag</span>
          <input type="text" class="form-control" :value="overview.runtime.drift_flag ? 'Detected' : 'No Drift'"
            :class="overview.runtime.drift_flag ? 'text-danger fw-bold' : 'text-success fw-bold'" readonly />
        </div>
      </div>

      <!-- Freeze Flag -->
      <div class="col-md-12">
        <div class="input-group">
          <span class="input-group-text status-label bg-secondary text-light">Freeze Flag</span>
          <input type="text" class="form-control" :value="overview.runtime.freeze_flag ? 'Frozen' : 'Active'"
            :class="overview.runtime.freeze_flag ? 'text-warning fw-bold' : 'text-success fw-bold'" readonly />
        </div>
      </div>

      <!-- Latency p95 (ms) -->
      <div class="col-md-12">
        <div class="input-group">
          <span class="input-group-text status-label bg-secondary text-light">Latency p95 (ms)</span>
          <input type="text" class="form-control" :value="overview.telemetry.latency_p95_ms?.toFixed(2) ?? '—'"
            readonly />
        </div>
      </div>

      <!-- Predictions Count -->
      <div class="col-md-12">
        <div class="input-group">
          <span class="input-group-text status-label bg-secondary text-light">Predictions Count</span>
          <input type="text" class="form-control" :value="overview.telemetry.predictions_count" readonly />
        </div>
      </div>

      <!-- Errors Count -->
      <div class="col-md-12">
        <div class="input-group">
          <span class="input-group-text status-label bg-secondary text-light">Errors Count</span>
          <input type="text" class="form-control" :value="overview.telemetry.errors_count"
            :class="overview.telemetry.errors_count > 0 ? 'text-danger fw-bold' : ''" readonly />
        </div>
      </div>

    </div>

    <!-- ===== Errors Section ===== -->
    <div v-if="overview.errors.length" class="alert alert-danger mt-4">
      <h5>Errors</h5>
      <ul class="mb-0">
        <li v-for="(err, idx) in overview.errors" :key="idx">{{ err }}</li>
      </ul>
    </div>

    <!-- ===== Warnings Section ===== -->
    <div v-if="overview.warnings.length" class="alert alert-warning mt-4">
      <h5>Warnings</h5>
      <ul class="mb-0">
        <li v-for="(warn, idx) in overview.warnings" :key="idx">{{ warn }}</li>
      </ul>
    </div>

    <!-- ===== Last Updated ===== -->
    <div v-if="overview.timestamp" class="text-muted text-end mt-3 small">
      Last updated: {{ formatDate(overview.timestamp) }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import axios from 'axios'

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

let intervalId: number | null = null

async function loadDashboard() {
  try {
    const response = await axios.get('/api/v1/system/overview')
    overview.value = response.data
    console.log('📊 Dashboard updated:', overview.value)
  } catch (error) {
    console.error('Dashboard load failed', error)
  }
}

function formatDate(dateStr: string) {
  if (!dateStr) return '—'
  const date = new Date(dateStr)
  return date.toLocaleString('ru-RU')
}

onMounted(() => {
  loadDashboard()
  intervalId = setInterval(loadDashboard, 10000) as unknown as number
})

onUnmounted(() => {
  if (intervalId) {
    clearInterval(intervalId)
  }
})
</script>

<style scoped>
.status-label {
  min-width: 180px;
  font-weight: 500;
}

/* Цвета для значений */
.text-success {
  color: #198754 !important;
}

.text-danger {
  color: #dc3545 !important;
}

.text-warning {
  color: #ffc107 !important;
}

/* Жирный текст для выделения */
.fw-bold {
  font-weight: 700 !important;
}

/* Убираем рамку при фокусе для readonly полей */
.form-control:read-only {
  background-color: #fff;
  opacity: 1;
}

/* Выравнивание заголовков */
.input-group-text {
  justify-content: center;
}

/* Стили для алертов */
.alert ul {
  margin-top: 8px;
  padding-left: 20px;
}
</style>