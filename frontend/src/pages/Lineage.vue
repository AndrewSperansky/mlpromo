<!-- frontend/src/pages/Lineage.vue -->

<template>
  <div>
    <h2>Model Lineage</h2>

    <table class="table">
      <thead>
        <tr>
          <th>Time</th>
          <th>Event</th>
          <th>Model</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="e in events" :key="e.timestamp">
          <td>{{ e.timestamp }}</td>
          <td>{{ e.event_type }}</td>
          <td>{{ e.model_id }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getLineage } from '../services/api'

const events = ref<any[]>([])

onMounted(async () => {
  const res = await getLineage()
  events.value = res.data.reverse()
})
</script>