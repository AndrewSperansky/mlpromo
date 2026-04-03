<!-- frontend\src\components\TrainingResultCard.vue -->

<template>
  <div class="card mb-4 border-primary shadow-sm">
    <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
      <div>
        <i class="bi bi-check-circle-fill me-2"></i>
        <strong>Training Completed — Review Results</strong>
      </div>
      <span class="badge bg-light text-dark">
        {{ formatDate(trainingResult.trained_at) }}
      </span>
    </div>
    <div class="card-body">
      <!-- Metrics Comparison -->
      <h6 class="mb-3">
        <i class="bi bi-graph-up me-2"></i>Metrics Comparison
      </h6>
      <table class="table table-sm table-bordered" style="width: auto;">
        <thead class="table-secondary">
          <tr>
            <th>Metric</th>
            <th>Current Model</th>
            <th></th>
            <th>New Model</th>
            <th>Change</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(value, metric) in trainingResult.comparison.metrics_diff" :key="metric">
            <td class="fw-bold">{{ metric.toUpperCase() }}</td>
            <td class="text-muted">{{ formatMetric(trainingResult.comparison.current_metrics[metric]) }}</td>
            <td>→</td>
            <td class="fw-bold">{{ formatMetric(trainingResult.comparison.candidate_metrics[metric]) }}</td>
            <td :class="value >= 0 ? 'text-success' : 'text-danger'">
              {{ value >= 0 ? '+' : '' }}{{ value.toFixed(6) }}
              <span v-if="metric === 'rmse' && value >= 0" class="ms-1">✅</span>
              <span v-else-if="metric === 'rmse' && value < 0" class="ms-1">⚠️</span>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Recommendation -->
      <div class="alert" :class="trainingResult.comparison.is_better ? 'alert-success' : 'alert-warning'">
        <i v-if="trainingResult.comparison.is_better" class="bi bi-check-circle-fill me-2"></i>
        <i v-else class="bi bi-exclamation-triangle-fill me-2"></i>
        <strong>
          {{ trainingResult.comparison.is_better ? 'Metrics improved!' : 'Metrics did not improve' }}
        </strong>
        <span v-if="trainingResult.comparison.is_better">
          RMSE improved by {{ trainingResult.comparison.improvement_percent }}%
        </span>
        <span v-else>
          New model RMSE is {{ Math.abs(trainingResult.comparison.improvement_percent) }}% worse.
        </span>
        <br>
        <small>Review metrics above before activating.</small>
      </div>

      <!-- Actions -->
      <div class="mt-3 d-flex gap-2">
        <button class="btn btn-success" @click="activate" :disabled="activating">
          <span v-if="activating" class="spinner-border spinner-border-sm me-2"></span>
          <i v-else class="bi bi-check-lg me-2"></i>
          {{ activating ? 'Activating...' : 'Activate Model' }}
        </button>
        <button class="btn btn-outline-secondary" @click="dismiss" :disabled="activating">
          <i class="bi bi-x-lg me-2"></i>
          Dismiss
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import api from '../services/api'

interface TrainingResult {
  comparison: {
    current_model_id: number
    candidate_model_id: number
    current_metrics: Record<string, number>
    candidate_metrics: Record<string, number>
    metrics_diff: Record<string, number>
    is_better: boolean
    improvement_percent: number
  }
  candidate_model_id: number
  trained_at: string
}

const props = defineProps<{
  trainingResult: TrainingResult
}>()

const emit = defineEmits(['activated', 'dismissed'])
const activating = ref(false)

function formatMetric(value: number | undefined) {
  if (value === undefined) return '—'
  return value.toFixed(6)
}

function formatDate(dateStr: string) {
  if (!dateStr) return '—'
  const date = new Date(dateStr)
  return date.toLocaleString('ru-RU')
}

async function activate() {
  activating.value = true
  try {
    await api.post(`/ml/models/${props.trainingResult.candidate_model_id}/activate`)
    await api.post('/system/clear-training-result')
    emit('activated')
  } catch (error) {
    console.error('Activation failed:', error)
    alert('Failed to activate model')
  } finally {
    activating.value = false
  }
}

async function dismiss() {
  try {
    await api.post('/system/clear-training-result')
    emit('dismissed')
  } catch (error) {
    console.error('Failed to dismiss:', error)
  }
}
</script>

<style scoped>
.text-success {
  color: #198754 !important;
  font-weight: bold;
}
.text-danger {
  color: #dc3545 !important;
  font-weight: bold;
}
</style>