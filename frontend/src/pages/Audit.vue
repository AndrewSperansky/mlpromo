<!-- frontend/src/pages/Audit.vue -->

<template>
  <div>

    <h2 class="mb-4">Prediction Audit Viewer</h2>

    <div class="mb-3">
      <input v-model="filterModel" placeholder="Filter by model_id" class="form-control w-25" />
    </div>

    <table class="table table-bordered">
      <thead>
        <tr>
          <th>Request ID</th>
          <th>Model</th>
          <th>Version</th>
          <th>Prediction</th>
          <th>Created</th>
        </tr>
      </thead>

      <tbody>
        <tr v-for="row in results" :key="row.id">
          <td>{{ row.request_id }}</td>
          <td>{{ row.model_id }}</td>
          <td>{{ row.model_version }}</td>
          <td>{{ row.prediction_value }}</td>
          <td>{{ row.created_at }}</td>
        </tr>
      </tbody>
    </table>

    <button class="btn btn-secondary" @click="loadMore">
      Load More
    </button>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { getAuditPage } from '../services/api'

const results = ref<any[]>([])
const page = ref(1)
const filterModel = ref('')

async function loadAudit(reset = false) {
  if (reset) {
    page.value = 1
    results.value = []
  }

  const response = await getAuditPage(page.value, filterModel.value)
  results.value.push(...response.data)
}

function loadMore() {
  page.value++
  loadAudit()
}

watch(filterModel, () => loadAudit(true))

onMounted(() => loadAudit())
</script>