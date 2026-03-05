<!-- frontend\src\pages\DatasetDetails.vue -->

<script setup lang="ts">
import { onMounted, ref } from "vue"
import { useRoute } from "vue-router"
import { fetchDatasetModels } from "@/services/api"
import type { Model } from "@/types"

const route = useRoute()
const models = ref<Model[]>([])

onMounted(async () => {
  const res = await fetchDatasetModels(route.params.id as string)
  models.value = res.data
})

</script>

<template>
  <div>
    <h2>Models trained on dataset {{ route.params.id }}</h2>

    <table>
      <thead>
        <tr>
          <th>Name</th>
          <th>Version</th>
          <th>Rows</th>
          <th>Active</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="m in models" :key="m.id">
          <td>{{ m.name }}</td>
          <td>{{ m.version }}</td>
          <td>{{ m.trained_rows_count }}</td>
          <td>{{ m.is_active ? "Yes" : "No" }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>