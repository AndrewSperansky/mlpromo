<!-- frontend/src/components/ModelTable.vue -->

<template>
  <table class="table table-bordered">
    <thead>
      <tr>
        <th>Model ID</th>
        <th>Version</th>
        <th>Active</th>
        <th>Created At</th>
        <th>Actions</th>
      </tr>
    </thead>

    <tbody>
      <tr v-for="model in models" :key="model.ml_model_id">
        <td>{{ model.ml_model_id }}</td>
        <td>{{ model.version }}</td>
        <td>
          <span v-if="model.active" class="badge bg-success">
            Active
          </span>
        </td>
        <td>{{ model.created_at }}</td>

        <td>

          <button class="btn btn-sm btn-outline-primary me-2" @click="$emit('activate', model.ml_model_id)">
            Activate
          </button>

          <button class="btn btn-sm btn-outline-info me-2" @click="$emit('evaluate', model.ml_model_id)">
            Evaluate
          </button>

          <button class="btn btn-sm btn-outline-warning" @click="$emit('rollback', model.ml_model_id)">
            Rollback
          </button>

        </td>
      </tr>
    </tbody>
  </table>
</template>

<script setup lang="ts">
interface ModelItem {
  ml_model_id: string
  version: string
  active: boolean
  created_at: string
}

defineProps<{
  models: ModelItem[]
}>()

defineEmits(['activate', 'rollback', 'evaluate'])
</script>