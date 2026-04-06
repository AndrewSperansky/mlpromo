<!-- frontend/src/components/CompareModelsModal.vue -->

<template>
  <div v-if="show" class="modal-backdrop" @click.self="$emit('close')">
    <div class="modal-box" style="width: 800px;">
      <h5>Compare Models</h5>

      <div class="row mb-3">
        <div class="col">
          <label>Model A</label>
          <select v-model="modelA" class="form-select">
            <option v-for="m in models" :key="m.ml_model_id" :value="m.ml_model_id">
              {{ m.version }} (ID: {{ m.ml_model_id }}) {{ m.active ? '🔥' : '' }}
            </option>
          </select>
        </div>
        <div class="col">
          <label>Model B</label>
          <select v-model="modelB" class="form-select">
            <option v-for="m in models" :key="m.ml_model_id" :value="m.ml_model_id">
              {{ m.version }} (ID: {{ m.ml_model_id }}) {{ m.active ? '🔥' : '' }}
            </option>
          </select>
        </div>
      </div>

      <div class="d-flex justify-content-end mb-3">
        <button class="btn btn-primary" @click="fetchCompare" :disabled="comparing">
          {{ comparing ? 'Comparing...' : 'Compare' }}
        </button>
      </div>

      <div v-if="compareResult" class="mt-3">
        <h6>Metrics</h6>
        <table class="table table-sm">
          <tr v-for="(value, key) in compareResult.diff.metric_diff" :key="key">
            <td><strong>{{ key }}</strong></td>
            <td>{{ compareResult.model_a.metrics[key]?.toFixed(6) }}</td>
            <td>→</td>
            <td>{{ compareResult.model_b.metrics[key]?.toFixed(6) }}</td>
            <td :class="value >= 0 ? 'text-success' : 'text-danger'">
              {{ value >= 0 ? '+' : '' }}{{ value.toFixed(6) }}
            </td>
          </tr>
        </table>

        <!-- Рекомендация -->
        <div class="alert mt-3" :class="recommendationClass">
          <i :class="recommendationIcon" class="me-2"></i>
          <strong>{{ recommendationText }}</strong>
          <div class="mt-1 small">
            <span v-if="compareResult.model_a.is_active" class="badge bg-success me-2">Active</span>
            <span v-if="compareResult.model_b.is_active" class="badge bg-success me-2">Active</span>
            {{ recommendationDetails }}
          </div>
        </div>

        <h6>Features</h6>
        <div class="row">
          <div class="col">
            <strong>Only in A:</strong>
            <ul>
              <li v-for="f in compareResult.diff.features_diff.only_in_a" :key="f">{{ f }}</li>
              <li v-if="!compareResult.diff.features_diff.only_in_a?.length" class="text-muted">—</li>
            </ul>
          </div>
          <div class="col">
            <strong>Only in B:</strong>
            <ul>
              <li v-for="f in compareResult.diff.features_diff.only_in_b" :key="f">{{ f }}</li>
              <li v-if="!compareResult.diff.features_diff.only_in_b?.length" class="text-muted">—</li>
            </ul>
          </div>
          <div class="col">
            <strong>Common Features:</strong>
            <ul>
              <li v-for="f in compareResult.diff.features_diff.common" :key="f">{{ f }}</li>
            </ul>
          </div>
        </div>

        <p><strong>Dataset equal:</strong> {{ compareResult.diff.dataset_equal ? 'Yes' : 'No' }}</p>
      </div>

      <div class="d-flex justify-content-end mt-3 pt-3 border-top">
        <button class="btn btn-secondary" @click="$emit('close')">Close</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { compareModels } from '../services/api'

const props = defineProps<{
  show: boolean
  models: Array<{ ml_model_id: number; version: string; active: boolean }>
}>()

const emit = defineEmits(['close'])

const modelA = ref<number | null>(null)
const modelB = ref<number | null>(null)
const compareResult = ref<any>(null)
const comparing = ref(false)

async function fetchCompare() {
  if (!modelA.value || !modelB.value) {
    console.warn('Both models must be selected')
    return
  }

  comparing.value = true
  compareResult.value = null

  try {
    const response = await compareModels(modelA.value, modelB.value)
    compareResult.value = response.data
  } catch (error) {
    console.error('Compare failed:', error)
    alert('Failed to compare models')
  } finally {
    comparing.value = false
  }
}

// Computed для рекомендации
const recommendationText = computed(() => {
  if (!compareResult.value) return ''
  
  const metricsDiff = compareResult.value.diff?.metric_diff || {}
  let betterModel: 'A' | 'B' | null = null
  
  for (const [metric, diff] of Object.entries(metricsDiff)) {
    const diffNum = diff as number
    if (metric === 'rmse' || metric === 'mae' || metric === 'mape') {
      if (diffNum > 0) betterModel = 'B'
      else if (diffNum < 0) betterModel = 'A'
    } else {
      if (diffNum > 0) betterModel = 'B'
      else if (diffNum < 0) betterModel = 'A'
    }
  }
  
  if (betterModel === 'A') {
    return `✅ Model A (${compareResult.value.model_a.version}) is better!`
  } else if (betterModel === 'B') {
    return `✅ Model B (${compareResult.value.model_b.version}) is better!`
  } else if (compareResult.value.model_a.is_active && !compareResult.value.model_b.is_active) {
    return `ℹ️ Model A is currently active. Consider comparing with newer models.`
  } else if (!compareResult.value.model_a.is_active && compareResult.value.model_b.is_active) {
    return `ℹ️ Model B is currently active. Consider comparing with newer models.`
  }
  
  return `⚖️ Models have similar performance. Review metrics in detail.`
})

const recommendationClass = computed(() => {
  if (!compareResult.value) return 'alert-secondary'
  
  const metricsDiff = compareResult.value.diff?.metric_diff || {}
  let betterModel: 'A' | 'B' | null = null
  
  for (const [metric, diff] of Object.entries(metricsDiff)) {
    const diffNum = diff as number
    if (metric === 'rmse' || metric === 'mae' || metric === 'mape') {
      if (diffNum > 0) betterModel = 'B'
      else if (diffNum < 0) betterModel = 'A'
    } else {
      if (diffNum > 0) betterModel = 'B'
      else if (diffNum < 0) betterModel = 'A'
    }
  }
  
  if (betterModel) return 'alert-success'
  return 'alert-info'
})

const recommendationIcon = computed(() => {
  if (!compareResult.value) return 'bi bi-question-circle'
  
  const metricsDiff = compareResult.value.diff?.metric_diff || {}
  let betterModel: 'A' | 'B' | null = null
  
  for (const [metric, diff] of Object.entries(metricsDiff)) {
    const diffNum = diff as number
    if (metric === 'rmse' || metric === 'mae' || metric === 'mape') {
      if (diffNum > 0) betterModel = 'B'
      else if (diffNum < 0) betterModel = 'A'
    } else {
      if (diffNum > 0) betterModel = 'B'
      else if (diffNum < 0) betterModel = 'A'
    }
  }
  
  if (betterModel) return 'bi bi-star-fill'
  return 'bi bi-info-circle-fill'
})

const recommendationDetails = computed(() => {
  if (!compareResult.value) return ''
  
  const metricsDiff = compareResult.value.diff?.metric_diff || {}
  const details: string[] = []
  
  for (const [metric, diff] of Object.entries(metricsDiff)) {
    const diffNum = diff as number
    
    if (metric === 'rmse') {
      if (diffNum > 0) {
        details.push(`RMSE улучшился на ${diffNum.toFixed(6)}`)
      } else if (diffNum < 0) {
        details.push(`RMSE ухудшился на ${Math.abs(diffNum).toFixed(6)}`)
      }
    } else if (metric === 'mae') {
      if (diffNum > 0) details.push(`MAE улучшился на ${diffNum.toFixed(6)}`)
      else if (diffNum < 0) details.push(`MAE ухудшился на ${Math.abs(diffNum).toFixed(6)}`)
    } else if (metric === 'r2') {
      if (diffNum > 0) details.push(`R² улучшился на ${diffNum.toFixed(6)}`)
      else if (diffNum < 0) details.push(`R² ухудшился на ${Math.abs(diffNum).toFixed(6)}`)
    }
  }
  
  return details.join('; ') || 'No significant differences detected.'
})

</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1050;
}

.modal-box {
  background: white;
  padding: 24px;
  border-radius: 8px;
  max-width: 90vw;
  max-height: 90vh;
  overflow-y: auto;
}

.text-success {
  color: #198754 !important;
}

.text-danger {
  color: #dc3545 !important;
}
</style>