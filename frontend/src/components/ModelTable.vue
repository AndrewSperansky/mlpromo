<!-- frontend/src/components/ModelTable.vue -->

<template>
  <table class="table table-bordered table-striped table-hover">
    <thead class="table-dark">
      <tr>
        <th>Model ID</th>
        <th>Algorithm</th>
        <th>Version</th>
        <th>Status</th>
        <th>Metric</th>
        <th>Created At</th>
        <th>Actions</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="model in models" :key="model.ml_model_id" @click="$emit('row-click', model.ml_model_id)"
        style="cursor: pointer;">
        <td>{{ model.ml_model_id }}</td>
        <td>
          <span :class="getAlgorithmBadgeClass(model.algorithm)">
            {{ getAlgorithmLabel(model.algorithm) }}
          </span>
        </td>
        <td>{{ model.version }}</td>
        <td>
          <span class="badge" :class="model.active ? 'bg-success' : 'bg-secondary'">
            {{ model.active ? 'Active' : 'Inactive' }}
          </span>
        </td>
        <td @click.stop>
          <span v-if="model.algorithm === 'catboost'">
            RMSE: {{ model.metrics?.rmse?.toFixed(4) || '—' }}
          </span>
          <span v-else-if="model.algorithm && model.algorithm.startsWith('pytorch')">
            Val Loss: {{ model.metrics?.val_loss?.toFixed(2) || '—' }}
          </span>
          <span v-else>—</span>
        </td>
        <td>{{ formatDate(model.created_at) }}</td>
        <td @click.stop>
          <button 
            v-if="!model.active"
            class="btn btn-sm btn-outline-primary me-2" 
            @click="$emit('activate', model.ml_model_id)"
          >
            Activate
          </button>
          
          <button 
            v-if="model.active"
            class="btn btn-sm btn-outline-warning me-2" 
            @click="$emit('deactivate', model.ml_model_id)"
          >
            Deactivate
          </button>

          <button class="btn btn-sm btn-outline-info me-2" @click="$emit('evaluate', model.ml_model_id)">
            Evaluate
          </button>

          <button class="btn btn-sm btn-outline-secondary me-2" @click="$emit('rollback', model.ml_model_id)">
            Rollback
          </button>

          <button class="btn btn-sm btn-outline-danger" @click="$emit('delete', model.ml_model_id)">
            Delete
          </button>
        </td>
       </tr>
    </tbody>
  </table>
</template>

<script setup lang="ts">
export interface ModelItem {
  ml_model_id: number
  version: string
  active: boolean
  created_at: string
  algorithm?: string
  metrics?: {
    rmse?: number
    val_loss?: number
    [key: string]: any
  }
}

defineProps<{
  models: ModelItem[]
}>()

defineEmits<{
  (e: 'activate', id: number): void
  (e: 'deactivate', id: number): void
  (e: 'rollback', id: number): void
  (e: 'evaluate', id: number): void
  (e: 'row-click', id: number): void
  (e: 'delete', id: number): void
}>()

function formatDate(dateStr: string) {
  if (!dateStr) return '-'
  try {
    const date = new Date(dateStr)
    if (isNaN(date.getTime())) return '-'
    return date.toLocaleString('ru-RU', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch (e) {
    return '-'
  }
}

function getAlgorithmBadgeClass(algorithm: string | undefined): string {
  if (algorithm && algorithm.startsWith('pytorch')) {
    return 'badge bg-info text-dark'
  }
  return 'badge bg-secondary'
}

function getAlgorithmLabel(algorithm: string | undefined): string {
  if (algorithm === 'catboost') return 'CatBoost'
  if (algorithm === 'pytorch_lstm') return 'LSTM'
  if (algorithm === 'pytorch_lstm_with_embeddings') return 'LSTM (Embs)'
  return algorithm || 'CatBoost'
}
</script>