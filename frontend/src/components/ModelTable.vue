 <!-- frontend\src\components\ModelTable.vue -->


<template>
  <div class="card p-3 shadow-sm">
    <table class="table table-striped">
      <thead>
        <tr>
          <th>Model ID</th>
          <th>Version</th>
          <th>Status</th>
          <th>Created At</th>
          <th>Action</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="model in models" :key="model.ml_model_id">
          <td>{{ model.ml_model_id }}</td>
          <td>{{ model.version }}</td>

          <td>
            <span
              class="badge"
              :class="model.active ? 'bg-success' : 'bg-secondary'"
            >
              {{ model.active ? 'Active' : 'Inactive' }}
            </span>
          </td>

          <td>{{ model.created_at }}</td>

          <td>
            <button
              class="btn btn-sm btn-outline-primary"
              :disabled="model.active"
              @click="$emit('activate', model.ml_model_id)"
            >
              Activate
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  models: Array<{
    ml_model_id: string
    version: string
    active: boolean
    created_at: string
  }>
}>()

defineEmits(['activate'])
</script>