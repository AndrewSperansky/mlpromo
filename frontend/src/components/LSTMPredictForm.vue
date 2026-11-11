<!-- frontend/src/components/LSTMPredictForm.vue -->

<template>
  <div class="card shadow-sm">
    <div class="card-header bg-info text-white">
      <i class="bi bi-cpu me-2"></i>
      <strong>LSTM Sales Prediction</strong>
      <span class="badge bg-light text-dark ms-2">PyTorch</span>
    </div>
    <div class="card-body">
      <div class="row g-3">
        <div class="col-md-4">
          <label class="form-label fw-bold">SKU <span class="text-danger">*</span></label>
          <input 
            type="text" 
            class="form-control" 
            v-model="sku" 
            placeholder="РН112367"
            :class="{ 'is-invalid': errors.sku }"
          >
          <div class="invalid-feedback" v-if="errors.sku">{{ errors.sku }}</div>
        </div>
        
        <div class="col-md-3">
          <label class="form-label fw-bold">Days Ahead</label>
          <input 
            type="number" 
            class="form-control" 
            v-model.number="daysAhead" 
            min="1" 
            max="30"
          >
          <small class="text-muted">1-30 дней</small>
        </div>
        
        <div class="col-md-3">
          <label class="form-label fw-bold">Store ID</label>
          <input 
            type="text" 
            class="form-control" 
            v-model="storeId" 
            placeholder="00-000072"
          >
          <small class="text-muted">Опционально</small>
        </div>
        
        <div class="col-md-2 d-flex align-items-end">
          <button 
            class="btn btn-info w-100" 
            @click="runPrediction" 
            :disabled="loading || !sku"
          >
            <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
            <i v-else class="bi bi-graph-up me-2"></i>
            {{ loading ? 'Predicting...' : 'Predict' }}
          </button>
        </div>
      </div>
      
      <!-- Результаты прогноза -->
      <div v-if="result" class="mt-4">
        <div class="alert alert-success">
          <div class="d-flex justify-content-between align-items-center">
            <div>
              <strong>Model ID:</strong> {{ result.model_id }}
              <span class="mx-2">|</span>
              <strong>SKU:</strong> {{ result.sku }}
              <span class="mx-2">|</span>
              <strong>Days:</strong> {{ result.days_ahead }}
            </div>
            <span class="badge bg-success">LSTM</span>
          </div>
        </div>
        
        <div class="table-responsive">
          <table class="table table-sm table-bordered table-hover">
            <thead class="table-dark">
              <tr>
                <th>#</th>
                <th>Date</th>
                <th>Predicted Sales (шт)</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(pred, idx) in result.predictions" :key="idx">
                <td class="text-center">{{ idx + 1 }}</td>
                <td>{{ formatDate(pred.date) }}</td>
                <td class="fw-bold text-primary">{{ pred.predicted_sales.toFixed(2) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        
        <!-- Простой график -->
        <canvas ref="chartRef" height="80" class="mt-3"></canvas>
      </div>
      
      <div v-if="error" class="alert alert-danger mt-3">
        <i class="bi bi-exclamation-triangle-fill me-2"></i>
        {{ error }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { predictLSTM, type LSTMPredictResponse } from '../services/api'
import Chart from 'chart.js/auto'

const sku = ref('')
const daysAhead = ref(7)
const storeId = ref('')
const loading = ref(false)
const result = ref<LSTMPredictResponse | null>(null)
const error = ref('')
const chartRef = ref<HTMLCanvasElement | null>(null)
let chartInstance: Chart | null = null

const errors = ref({ sku: '' })

function formatDate(dateStr: string) {
  const date = new Date(dateStr)
  return date.toLocaleDateString('ru-RU')
}

async function runPrediction() {
  // Валидация
  if (!sku.value.trim()) {
    errors.value.sku = 'SKU is required'
    return
  }
  errors.value.sku = ''
  
  loading.value = true
  error.value = ''
  result.value = null
  
  try {
    const response = await predictLSTM({
      sku: sku.value.trim(),
      days_ahead: daysAhead.value,
      store_id: storeId.value.trim() || undefined
    })
    result.value = response.data
    
    // Рендерим график
    await renderChart()
    
  } catch (err: any) {
    console.error('LSTM prediction failed:', err)
    error.value = err.response?.data?.detail || 'Prediction failed. Check if LSTM model is active.'
  } finally {
    loading.value = false
  }
}

async function renderChart() {
  if (!chartRef.value || !result.value) return
  
  if (chartInstance) chartInstance.destroy()
  
  const ctx = chartRef.value.getContext('2d')
  if (!ctx) return
  
  const labels = result.value.predictions.map(p => formatDate(p.date))
  const data = result.value.predictions.map(p => p.predicted_sales)
  
  chartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'Predicted Sales (шт)',
        data,
        borderColor: 'rgb(13, 202, 240)',
        backgroundColor: 'rgba(13, 202, 240, 0.1)',
        fill: true,
        tension: 0.3
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        tooltip: {
          callbacks: {
            label: (context: any) => `Продажи: ${context.raw.toFixed(2)} шт`
          }
        }
      }
    }
  })
}
</script>

<style scoped>
.card {
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15) !important;
}
.is-invalid {
  border-color: #dc3545;
}
</style>