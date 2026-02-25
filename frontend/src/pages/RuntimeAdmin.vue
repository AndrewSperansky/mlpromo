<template>
  <div>
    <h2 class="mb-4">Runtime Administration</h2>

    <!-- ===== Operational Overview ===== -->
    <div class="row g-3 mb-4">

      <StatusCard
        title="Model ID"
        :value="overview.runtime.ml_model_id ?? '—'"
      />

      <StatusCard
        title="Version"
        :value="overview.runtime.version ?? '—'"
      />

      <StatusCard
        title="Model Loaded"
        :value="overview.runtime.model_loaded ? 'Yes' : 'No'"
        :badge="overview.runtime.model_loaded ? 'success' : 'danger'"
      />

      <StatusCard
        title="Freeze Flag"
        :value="overview.runtime.freeze_flag ? 'Frozen' : 'Active'"
        :badge="overview.runtime.freeze_flag ? 'warning' : 'success'"
      />

      <StatusCard
        title="Drift Flag"
        :value="overview.runtime.drift_flag ? 'Drift Detected' : 'No Drift'"
        :badge="overview.runtime.drift_flag ? 'danger' : 'success'"
      />

      <StatusCard
        title="Retrain Requested"
        :value="overview.runtime.retrain_requested ? 'Yes' : 'No'"
        :badge="overview.runtime.retrain_requested ? 'primary' : 'secondary'"
      />

    </div>

    <!-- ===== Controls ===== -->
    <div class="row g-3 mb-4">

      <div class="col-md-3">
        <button class="btn btn-warning w-100" @click="freeze">
          Freeze
        </button>
      </div>

      <div class="col-md-3">
        <button class="btn btn-success w-100" @click="unfreeze">
          Unfreeze
        </button>
      </div>

      <div class="col-md-3">
        <button class="btn btn-danger w-100" @click="clearDrift">
          Clear Drift
        </button>
      </div>

      <div class="col-md-3">
        <button class="btn btn-primary w-100" @click="forceRetrain">
          Force Retrain
        </button>
      </div>

    </div>

    <!-- ===== Debug Section ===== -->
    <div class="card shadow-sm">
      <div class="card-header d-flex justify-content-between align-items-center">
        <span>Debug Runtime State</span>
        <button class="btn btn-sm btn-outline-secondary" @click="toggleDebug">
          {{ showDebug ? 'Hide' : 'Show' }}
        </button>
      </div>

      <div v-if="showDebug" class="card-body">
        <pre class="bg-light p-3 small">
{{ overview }}
        </pre>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue"
import api from "../services/api"
import StatusCard from "../components/StatusCard.vue"

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

const showDebug = ref(false)

async function loadOverview() {
  const res = await api.get("/system/overview")
  overview.value = res.data
}

async function freeze() {
  await api.post("/system/freeze")
  await loadOverview()
}

async function unfreeze() {
  await api.post("/system/unfreeze")
  await loadOverview()
}

async function clearDrift() {
  await api.post("/system/clear-drift")
  await loadOverview()
}

async function forceRetrain() {
  await api.post("/system/force-retrain")
  await loadOverview()
}

function toggleDebug() {
  showDebug.value = !showDebug.value
}

onMounted(loadOverview)
</script>