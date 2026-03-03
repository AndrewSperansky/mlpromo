<!-- frontend/src/components/ModelTable.vue -->

<template>
  <table class="table table-bordered">
    <thead>
      <tr>
        <th>Model ID</th>
        <th>Version</th>
        <th>Status</th>
        <th>Created At</th>
        <th>Actions</th>
      </tr>
    </thead>

    <tbody>
      <tr v-for="model in models" :key="model.ml_model_id" @click="$emit('row-click', model.ml_model_id)"
        style="cursor: pointer;">
        <td>{{ model.ml_model_id }}</td>
        <td>{{ model.version }}</td>
        <td>
          <span class="badge" :class="model.active ? 'bg-success' : 'bg-secondary'">
            {{ model.active ? 'Active' : 'Inactive' }}
          </span>
        </td>
        <td>{{ model.created_at }}</td>

        <td>
          <!-- ВАЖНО: stop propagation -->
          <button class="btn btn-sm btn-outline-primary me-2" @click.stop="$emit('activate', model.ml_model_id)">
            Activate
          </button>

          <button class="btn btn-sm btn-outline-info me-2" @click.stop="$emit('evaluate', model.ml_model_id)">
            Evaluate
          </button>

          <button class="btn btn-sm btn-outline-warning" @click.stop="$emit('rollback', model.ml_model_id)">
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

defineEmits<{
  (e: 'activate', id: string): void
  (e: 'rollback', id: string): void
  (e: 'evaluate', id: string): void
  (e: 'row-click', id: string): void
}>()
</script>