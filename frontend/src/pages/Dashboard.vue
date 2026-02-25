<template>
  <div>
    <h2 class="mb-4">System Dashboard</h2>

    <div class="row g-3">

      <StatusCard
        title="Active Model Version"
        :value="overview.runtime.version ?? '—'"
      />

      <StatusCard
        title="Model Loaded"
        :value="overview.runtime.model_loaded ? 'Yes' : 'No'"
        :badge="overview.runtime.model_loaded ? 'success' : 'danger'"
      />

      <StatusCard
        title="Drift Flag"
        :value="overview.runtime.drift_flag ? 'Detected' : 'No Drift'"
        :badge="overview.runtime.drift_flag ? 'danger' : 'success'"
      />

      <StatusCard
        title="Freeze Flag"
        :value="overview.runtime.freeze_flag ? 'Frozen' : 'Active'"
        :badge="overview.runtime.freeze_flag ? 'warning' : 'success'"
      />

      <StatusCard
        title="Latency p95 (ms)"
        :value="overview.telemetry.latency_p95_ms ?? '—'"
      />

      <StatusCard
        title="Predictions Count"
        :value="overview.telemetry.predictions_count"
      />

      <StatusCard
        title="Errors Count"
        :value="overview.telemetry.errors_count"
        :badge="overview.telemetry.errors_count > 0 ? 'danger' : 'success'"
      />

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import StatusCard from '../components/StatusCard.vue'

interface OverviewResponse {
  timestamp: string
  runtime: {
    ml_model_id: string | null
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

async function loadDashboard() {
  try {
    const response = await axios.get('/api/v1/system/overview')
    overview.value = response.data
  } catch (error) {
    console.error('Dashboard load failed', error)
  }
}

onMounted(() => {
  loadDashboard()
  setInterval(loadDashboard, 10000)
})
</script>