<!-- frontend/src/pages/Predict.vue -->

<template>
  <div>
    <h2 class="mb-4">Predictions Test Page</h2>

    <div class="input-group mb-3">
      <!-- Кнопки управления -->
      <button class="btn btn-primary" @click="showManualForm = true">
        <i class="bi bi-pencil-square me-2"></i>Manual Input
      </button>
      <label class="btn btn-primary" for="csvUpload">
        <i class="bi bi-cloud-upload me-2"></i>Load CSV
        <input type="file" id="csvUpload" class="d-none" accept=".csv" @change="handleCSVUpload" />
      </label>

      <div class="form-control bg-light d-flex align-items-center justify-content-between">
        <span>
          <i v-if="!rows.length" class="bi bi-file-earmark text-muted me-2"></i>
          <i v-else class="bi bi-check-circle-fill text-success me-2"></i>
          <span :class="{ 'text-success': rows.length }">
            {{ statusText }}
          </span>
        </span>
        <span v-if="rows.length" class="badge bg-success rounded-pill">
          {{ rows.length }} rows
        </span>
      </div>

      <button class="btn btn-success" type="button" :disabled="!rows.length || loading" @click="runBatchPredict">
        <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
        <i v-else class="bi bi-play-fill me-2"></i>
        {{ loading ? 'Predicting...' : 'Run' }}
      </button>
    </div>

    <!-- Карточка с результатами -->
    <div v-if="predictions.length" class="row mb-4">
      <div class="col-md-12">
        <div class="card shadow-sm">
          <div class="card-header bg-primary text-white">
            <i class="bi bi-graph-up me-2"></i>Прогноз продаж
          </div>
          <div class="card-body">
            <canvas ref="chartRef"></canvas>
          </div>
        </div>
      </div>
      
      <div class="col-md-12 mt-4">
        <div class="card shadow-sm">
          <div class="card-header bg-info text-white">
            <i class="bi bi-table me-2"></i>Детализация
          </div>
          <div class="card-body p-0">
            <table class="table table-striped table-hover mb-0">
              <thead class="table-dark">
                 <tr>
                  <th>#</th>
                  <th>Промо-цена</th>
                  <th>k_uplift</th>
                  <th>Прогноз (шт)</th>
                  <th>Baseline</th>
                  <th>Прирост</th>
                 </tr>
              </thead>
              <tbody>
                <tr v-for="(item, idx) in predictions" :key="idx">
                  <td class="fw-bold">{{ idx + 1 }}</td>
                  <td class="fw-bold text-primary">{{ item.promo_price.toFixed(2) }} ₽</td>
                  <td class="text-primary fw-bold">{{ item.k_uplift.toFixed(3) }}x</td>
                  <td class="text-success fw-bold">{{ item.prediction_absolute.toFixed(2) }}</td>
                  <td class="text-secondary">{{ item.baseline.toFixed(2) }}</td>
                  <td :class="item.uplift_percent >= 0 ? 'text-success' : 'text-danger'">
                    {{ item.uplift_percent >= 0 ? '+' : '' }}{{ item.uplift_percent.toFixed(1) }}%
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- SHAP Features -->
    <div v-if="topShap.length" class="card shadow-sm mt-4">
      <div class="card-header bg-secondary text-white">
        <i class="bi bi-bar-chart-steps me-2"></i>Top 5 Influencing Features (SHAP)
      </div>
      <div class="card-body">
        <ul class="list-group">
          <li v-for="item in topShap" :key="item.feature" class="list-group-item d-flex justify-content-between align-items-center">
            {{ item.feature }}
            <span class="badge bg-primary rounded-pill">{{ item.value.toFixed(4) }}</span>
          </li>
        </ul>
      </div>
    </div>

  </div>
  <!-- Модальное окно для ручного ввода -->
  <ManualPredictModal 
    v-if="showManualForm" 
    :predictions="predictions"
    @close="showManualForm = false"
    @predict="handleManualPredict"
  />

</template>

<script setup lang="ts">
import { ref, nextTick, computed } from 'vue'
import { predictBatch } from '../services/api'
import Chart from 'chart.js/auto'
import ManualPredictModal from '../components/ManualPredictModal.vue'

interface CsvRow {
  [key: string]: any
}

interface PredictionResult {
  k_uplift: number
  baseline: number
  prediction_absolute: number
  uplift_percent: number
  store_id?: string  
  promo_price: number
}

const rows = ref<CsvRow[]>([])
const predictions = ref<PredictionResult[]>([])
const loading = ref(false)
const chartRef = ref<HTMLCanvasElement | null>(null)
let chartInstance: Chart | null = null
const topShap = ref<{ feature: string; value: number }[]>([])
const showManualForm = ref(false)

const statusText = computed(() => {
  if (!rows.value.length) return 'No data loaded'
  return `Ready to predict (${rows.value.length} samples)`
})

function handleManualPredict(newPredictions: any[]) {
  predictions.value = newPredictions.map((p: any) => ({
    k_uplift: p.k_uplift,
    baseline: p.baseline,
    prediction_absolute: p.prediction_absolute,
    uplift_percent: p.uplift_percent,
    store_id: p.store_id,
    promo_price: p.promo_price
  }))
  
  nextTick(() => {
    renderChart()
  })
}


function handleCSVUpload(event: Event) {
  const input = event.target as HTMLInputElement | null
  if (!input) return

  const files = input.files
  if (!files || files.length === 0) return

  const file = files.item(0)
  if (!file) return

  const reader = new FileReader()
  reader.onload = () => {
    const result = reader.result
    if (typeof result !== 'string') return
    parseCSV(result)
  }
  reader.readAsText(file)
}

function parseCSV(text: string) {
  const trimmed = text.trim()
  if (!trimmed) return

  const lines = trimmed.split('\n')
  if (lines.length < 2) return

  const headerLine = lines[0]
  if (!headerLine) return

  const headers = headerLine.split(',').map(h => h.trim())

  rows.value = lines
    .slice(1)
    .filter(line => line.trim().length > 0)
    .map(line => {
      const values = line.split(',')
      const obj: any = {}
      headers.forEach((header, index) => {
        const raw = (values[index] ?? '').trim()
        const num = Number(raw)
        obj[header] = isNaN(num) ? raw : num
      })
      return obj
    })

  console.log("📦 parsed rows", rows.value)
}

async function runBatchPredict() {
  loading.value = true
  predictions.value = []
  topShap.value = []

  try {
    for (const row of rows.value) {
      const payload = {
        promo_id: String(row.promo_id || row.PromoID || ''),
        week: Number(row.week || 1),
        month: Number(row.month || 1),
        sku: String(row.sku || row.SKU || ''),
        category: String(row.category || ''),
        regular_price: Number(row.regular_price || 0),
        promo_price: Number(row.promo_price || 0),
        store_id: String(row.store_id || row.StoreID || ''),
        region: String(row.region || ''),
        store_location_type: String(row.store_location_type || ''),
        format_assortment: String(row.format_assortment || ''),
        adv_carrier: String(row.adv_carrier || ''),
        adv_material: String(row.adv_material || ''),
        promo_mechanics: String(row.promo_mechanics || ''),
        marketing_type: String(row.marketing_type || ''),
        analog_sku: row.analog_sku ? JSON.parse(row.analog_sku) : [],
        baseline: row.baseline ? Number(row.baseline) : undefined
      }

      const response = await predictBatch([payload])

      const data = response.data
      
      if (data.k_uplift !== undefined) {
        predictions.value.push({
          k_uplift: data.k_uplift,
          baseline: data.baseline,
          prediction_absolute: data.prediction_absolute,
          uplift_percent: data.uplift_percent,
          store_id: payload.store_id,  
          promo_price: payload.promo_price
        })
      }

      // SHAP для первой строки
      if (data.shap_values && topShap.value.length === 0) {
        const shapArray = data.shap_values
        const shapObj: Record<string, number> = {}
        shapArray.forEach((s: any) => {
          shapObj[s.feature] = Math.abs(s.effect)
        })
        const sorted = Object.entries(shapObj)
          .map(([feature, value]) => ({ feature, value }))
          .sort((a, b) => b.value - a.value)
          .slice(0, 5)
        topShap.value = sorted
      }
    }

    await nextTick()
    renderChart()

  } catch (error) {
    console.error("Prediction error:", error)
  } finally {
    loading.value = false
  }
}

function renderChart() {
  const canvas = chartRef.value
  if (!canvas) return

  if (chartInstance) {
    chartInstance.destroy()
  }

  if (predictions.value.length === 0) return

  const firstPrediction = predictions.value[0]
  if (!firstPrediction) return

  chartInstance = new Chart(canvas, {
    type: 'bar',
    data: {
      labels: predictions.value.map((p, i) => {
        // 🔥 безопасная проверка
        const storeId = p.store_id || `Строка ${i + 1}`
        return `${storeId}\nбаза: ${p.baseline.toFixed(0)}`
      }),
      datasets: [
        {
          label: 'Базовые продажи (без промо)',
          data: predictions.value.map(p => p.baseline),
          backgroundColor: 'rgba(255, 99, 132, 0.9)',
          borderColor: 'rgba(255, 99, 132, 1)',
          borderWidth: 1,
          borderRadius: 4
        },
        {
          label: 'Дополнительные продажи (промо эффект)',
          data: predictions.value.map(p => Math.max(0, p.prediction_absolute - p.baseline)),
          backgroundColor: 'rgba(54, 162, 235, 0.8)',
          borderColor: 'rgba(54, 162, 235, 1)',
          borderWidth: 1,
          borderRadius: 4
        }
      ]
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          position: 'top',
        },
        tooltip: {
          callbacks: {
            label: (context: any) => {
              if (context.dataset.label === 'Базовые продажи (без промо)') {
                return `${context.dataset.label}: ${context.raw.toFixed(2)} шт`
              }
              const baseline = predictions.value[context.dataIndex]?.baseline || 0
              const total = baseline + context.raw
              return `${context.dataset.label}: ${context.raw.toFixed(2)} шт (всего: ${total.toFixed(2)})`
            }
          }
        }
      },
      scales: {
        y: {
          title: {
            display: true,
            text: 'Количество продаж (шт)'
          },
          stacked: true,
          beginAtZero: true
        },
        x: {
          title: {
            display: true,
            text: 'Магазин / Сценарий'
          },
          stacked: true
        }
      }
    }
  })
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
.text-primary {
  color: #0d6efd !important;
  font-weight: bold;
}
.text-secondary {
  color: #6c757d !important;
}
</style>