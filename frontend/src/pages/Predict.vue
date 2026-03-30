<!-- frontend\src\pages\Predict.vue -->


<template>
  <div>
    <h2 class="mb-4">Predictions Test Page</h2>

    <div class="input-group mb-3">
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
            <i class="bi bi-table me-2"></i>Детализация прогнозов
          </div>
          <div class="card-body p-0">
            <table class="table table-striped table-hover mb-0">
              <thead class="table-dark">
                <tr>
                  <th>#</th>
                  <th>Прогноз (шт)</th>
                  <th>Дата</th>
                  <th>SKU</th>
                  <th>Промо-код</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, idx) in tableData" :key="idx">
                  <td class="fw-bold">{{ item.index }}</td>
                  <td class="text-primary fw-bold">{{ item.prediction }}</td>
                  <td>{{ item.date }}</td>
                  <td>{{ item.sku }}</td>
                  <td>{{ item.promoCode }}</td>
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
</template>

<script setup lang="ts">
import { ref, nextTick, computed } from 'vue'
import { predictBatch } from '../services/api'
import Chart from 'chart.js/auto'

interface CsvRow {
  [key: string]: any
}

const rows = ref<CsvRow[]>([])
const predictions = ref<{ value: number; date: string; sku: string; promoCode: string }[]>([])
const loading = ref(false)
const chartRef = ref<HTMLCanvasElement | null>(null)
let chartInstance: Chart | null = null
const topShap = ref<{ feature: string; value: number }[]>([])

const statusText = computed(() => {
  if (!rows.value.length) return 'No data loaded'
  return `Ready to predict (${rows.value.length} samples)`
})

const tableData = computed(() => {
  return predictions.value.map((pred, idx) => ({
    index: idx + 1,
    prediction: pred.value.toFixed(2),
    date: pred.date,
    sku: pred.sku,
    promoCode: pred.promoCode
  }))
})

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
        promo_code: String(row.promo_code || row.PromoID || 'TEST'),
        sku: String(row.sku || row.SKU || 'SKU'),
        prediction_date: String(row.prediction_date || row.Date || new Date().toISOString().split('T')[0]),
        features: {
          RegularPrice: Number(row.RegularPrice || 0),
          PromoPrice: Number(row.PromoPrice || 0),
          VolumeRegular: Number(row.VolumeRegular || 0),
          HistoricalSalesPromo: Number(row.HistoricalSalesPromo || 0),
          SalesQty_PrevModel: Number(row.SalesQty_PrevModel || 0),
          TurnoverBefore: Number(row.TurnoverBefore || 0),
          TurnoverPromo: Number(row.TurnoverPromo || 0),
          IsNewSKU: Number(row.IsNewSKU || 0),
          IsAnalogSKU: Number(row.IsAnalogSKU || 0)
        }
      }

      const response = await predictBatch(payload)
      const data = response.data
      
      if (data.prediction !== undefined) {
        predictions.value.push({
          value: data.prediction,
          date: payload.prediction_date,
          sku: payload.sku,
          promoCode: payload.promo_code
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

  chartInstance = new Chart(canvas, {
    type: 'bar',
    data: {
      labels: predictions.value.map((_, i) => i + 1),
      datasets: [
        {
          label: 'Прогноз продаж (шт)',
          data: predictions.value.map(p => p.value),
          backgroundColor: 'rgba(54, 162, 235, 0.7)',
          borderColor: 'rgba(54, 162, 235, 1)',
          borderWidth: 1
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
              return `${context.dataset.label}: ${context.raw.toFixed(2)} шт`
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
          beginAtZero: true
        },
        x: {
          title: {
            display: true,
            text: 'Номер строки'
          }
        }
      }
    }
  })
}
</script>

<style scoped>
.card {
  margin-bottom: 1rem;
}
</style>