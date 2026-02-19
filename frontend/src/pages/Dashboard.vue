<template>
  <div>
    <h2 class="mb-4">System Dashboard</h2>

    <div class="row g-3">

      <div class="col-md-3">
        <div class="card p-3">
          <h6>Status</h6>
          <p class="mb-0">
            <span
              class="badge"
              :class="health.status === 'ok' ? 'bg-success' : 'bg-danger'"
            >
              {{ health.status || 'loading...' }}
            </span>
          </p>
        </div>
      </div>

      <div class="col-md-3">
        <div class="card p-3">
          <h6>Environment</h6>
          <p class="mb-0">{{ health.environment }}</p>
        </div>
      </div>

      <div class="col-md-3">
        <div class="card p-3">
          <h6>Version</h6>
          <p class="mb-0">{{ health.version }}</p>
        </div>
      </div>

      <div class="col-md-3">
        <div class="card p-3">
          <h6>Service</h6>
          <p class="mb-0">{{ health.service }}</p>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'

interface HealthResponse {
  status: string
  service: string
  environment: string
  version: string
}

const health = ref<Partial<HealthResponse>>({})

onMounted(async () => {
  try {
    const response = await axios.get('/api/v1/system/health')
    health.value = response.data
  } catch (error) {
    health.value = { status: 'error' }
  }
})
</script>
