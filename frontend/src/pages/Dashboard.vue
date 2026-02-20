<template>
  <div>
    <h2 class="mb-4">System Dashboard</h2>

    <div class="row g-3">

      <StatusCard
        title="Active Model Version"
        :value="status.active_model_version"
      />

      <StatusCard
        title="Model Loaded"
        :value="status.model_loaded ? 'Yes' : 'No'"
        :badge="status.model_loaded ? 'success' : 'danger'"
      />

      <StatusCard
        title="Drift Flag"
        :value="metrics.drift_flag ? 'Detected' : 'No Drift'"
        :badge="metrics.drift_flag ? 'danger' : 'success'"
      />

      <StatusCard
        title="Freeze Flag"
        :value="metrics.freeze_flag ? 'Frozen' : 'Active'"
        :badge="metrics.freeze_flag ? 'warning' : 'success'"
      />

      <StatusCard
        title="Latency p95 (ms)"
        :value="metrics.latency_p95_ms ?? '—'"
      />

      <StatusCard
        title="Predictions Count"
        :value="metrics.predictions_count"
      />

      <StatusCard
        title="Errors Count"
        :value="metrics.errors_count"
        :badge="metrics.errors_count > 0 ? 'danger' : 'success'"
      />

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getStatus, getMetrics } from '../services/api'
import StatusCard from '../components/StatusCard.vue'

interface SystemStatus {
  status: string
  model_loaded: boolean
  active_model_version: string
  errors: string[]
  warnings: string[]
}

interface SystemMetrics {
  drift_flag: boolean
  freeze_flag: boolean
  latency_p95_ms: number | null
  predictions_count: number
  errors_count: number
}

const status = ref<Partial<SystemStatus>>({})

const metrics = ref<SystemMetrics>({
  drift_flag: false,
  freeze_flag: false,
  latency_p95_ms: null,
  predictions_count: 0,
  errors_count: 0
})

async function loadDashboard() {
  try {
    const [statusResp, metricsResp] = await Promise.all([
      getStatus(),
      getMetrics()
    ])

    status.value = statusResp.data
    metrics.value = metricsResp.data
  } catch (error) {
    console.error('Dashboard load failed', error)
  }
}

onMounted(() => {
  loadDashboard()

  // автообновление каждые 10 секунд
  setInterval(loadDashboard, 10000)
})
</script>