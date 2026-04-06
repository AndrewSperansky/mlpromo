<!-- frontend/src/pages/Predict.vue -->

<template>
  <div>
    <h2 class="mb-4">Predictions Test Page</h2>

    <!-- Переключатель режимов -->
    <div class="btn-group mb-3" role="group">
      <button type="button" class="btn" :class="inputMode === 'manual' ? 'btn-primary' : 'btn-outline-secondary'"
        @click="inputMode = 'manual'">
        <i class="bi bi-pencil-square me-1"></i> Manual Input
      </button>
      <button type="button" class="btn" :class="inputMode === 'csv' ? 'btn-primary' : 'btn-outline-secondary'"
        @click="inputMode = 'csv'">
        <i class="bi bi-file-earmark-spreadsheet me-1"></i> CSV Upload
      </button>
    </div>

    <!-- ==================== РУЧНОЙ ВВОД ==================== -->
    <div v-if="inputMode === 'manual'">
      <!-- Кнопка Add Row над таблицей -->
      <div class="mb-3 d-flex justify-content-end">
        <button class="btn btn-success" @click="openAddForm">
          <i class="bi bi-plus-lg me-2"></i>Add Row
        </button>
      </div>

      <!-- Таблица на всю ширину экрана -->
      <div class="full-width-table">
        <div class="card mb-4">
          <div class="card-header bg-secondary text-white">
            <i class="bi bi-table me-2"></i>Input Data
          </div>
          <div class="card-body p-0">
            <div class="table-responsive" style="overflow-x: auto;">
              <table class="table table-sm table-bordered mb-0" style="min-width: 1400px; width: 100%;">
                <thead class="table-dark sticky-top">
                  <tr>
                    <th style="width: 40px">#</th>
                    <th>Promo ID</th>
                    <th>Week</th>
                    <th>Month</th>
                    <th>SKU</th>
                    <th>Category</th>
                    <th>Regular Price</th>
                    <th>Promo Price</th>
                    <th>Store ID</th>
                    <th>Region</th>
                    <th>Store Location Type</th>
                    <th>Format Assortment</th>
                    <th>Adv Carrier</th>
                    <th>Adv Material</th>
                    <th>Promo Mechanics</th>
                    <th>Marketing Type</th>
                    <th>Baseline</th>
                    <th style="width: 200px">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, idx) in manualRows" :key="idx">
                    <td class="text-center">{{ idx + 1 }}</td>
                    <td>{{ row.promo_id || 'Empty' }}</td>
                    <td>{{ row.week || 'Empty' }}</td>
                    <td>{{ row.month || 'Empty' }}</td>
                    <td>{{ row.sku || 'Empty' }}</td>
                    <td>{{ row.category || 'Empty' }}</td>
                    <td>{{ row.regular_price || 'Empty' }}</td>
                    <td>{{ row.promo_price || 'Empty' }}</td>
                    <td>{{ row.store_id || 'Empty' }}</td>
                    <td>{{ row.region || 'Empty' }}</td>
                    <td>{{ row.store_location_type || 'Empty' }}</td>
                    <td>{{ row.format_assortment || 'Empty' }}</td>
                    <td>{{ row.adv_carrier || 'Empty' }}</td>
                    <td>{{ row.adv_material || 'Empty' }}</td>
                    <td>{{ row.promo_mechanics || 'Empty' }}</td>
                    <td>{{ row.marketing_type || 'Empty' }}</td>
                    <td>{{ row.baseline || 'Empty' }}</td>
                    <td class="text-center">

                      <button class="btn btn-primary btn-sm me-1" @click="openEditForm(idx)" title="Edit">
                        <i class="bi bi-pencil"></i> Edit
                      </button>
                      <button class="btn btn-danger btn-sm" @click="removeRow(idx)" title="Delete">
                        <i class="bi bi-trash3"></i> Delete
                      </button>

                    </td>
                  </tr>
                </tbody>
                <tbody v-if="manualRows.length === 0">
                  <tr>
                    <td colspan="18" class="text-center text-muted py-4">No data. Click "Add Row" to add items.</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>



    <!-- ==================== CSV ЗАГРУЗКА ==================== -->
    <div v-if="inputMode === 'csv'">
      <div class="input-group mb-3">
        <label class="btn btn-primary" for="csvUpload">
          <i class="bi bi-cloud-upload me-2"></i>Load CSV
          <input type="file" id="csvUpload" class="d-none" accept=".csv" @change="handleCSVUpload" />
        </label>

        <div class="form-control bg-light d-flex align-items-center justify-content-between">
          <span>
            <i v-if="csvRows.length === 0" class="bi bi-file-earmark text-muted me-2"></i>
            <i v-else class="bi bi-check-circle-fill text-success me-2"></i>
            <span :class="{ 'text-success': csvRows.length > 0 }">
              {{ csvStatusText }}
            </span>
          </span>
          <span v-if="csvRows.length > 0" class="badge bg-success rounded-pill">
            {{ csvRows.length }} rows
          </span>
        </div>

        <button class="btn btn-success" type="button" :disabled="csvRows.length === 0 || loading"
          @click="runCSVPrediction">
          <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
          <i v-else class="bi bi-play-fill me-2"></i>
          {{ loading ? 'Predicting...' : 'Run' }}
        </button>
      </div>
    </div>

    <!-- ==================== Кнопка Run Prediction (для ручного режима) ==================== -->
    <div v-if="inputMode === 'manual'" class="d-flex justify-content-end mb-4">
      <button class="btn btn-primary btn-lg" @click="runManualPrediction"
        :disabled="loading || manualRows.length === 0">
        <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
        <i v-else class="bi bi-play-fill me-2"></i>
        {{ loading ? 'Predicting...' : 'Run Prediction' }}
      </button>
    </div>

    <!-- ==================== РЕЗУЛЬТАТЫ ==================== -->
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
            <i class="bi bi-table me-2"></i>Детализация результатов
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
                  <td class="text-info fw-bold">{{ item.k_uplift.toFixed(3) }}x</td>
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
          <li v-for="item in topShap" :key="item.feature"
            class="list-group-item d-flex justify-content-between align-items-center">
            {{ item.feature }}
            <span class="badge bg-primary rounded-pill">{{ item.value.toFixed(4) }}</span>
          </li>
        </ul>
      </div>
    </div>
  </div>

  <!-- Модальное окно для добавления/редактирования -->
  <ManualPredictForm v-if="showModal" :row="editingRow" :index="editingIndex" @close="closeModal" @save="saveRow" />
</template>

<script setup lang="ts">
import { ref, nextTick, computed } from 'vue'
import { predictBatch } from '../services/api'
import Chart from 'chart.js/auto'
import ManualPredictForm from '../components/ManualPredictForm.vue'

interface RowData {
  promo_id: string
  week: number
  month: number
  sku: string
  category: string
  regular_price: number
  promo_price: number
  store_id: string
  region: string
  store_location_type: string
  format_assortment: string
  adv_carrier: string
  adv_material: string
  promo_mechanics: string
  marketing_type: string
  baseline?: number
}

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

// Режим ввода
const inputMode = ref<'manual' | 'csv'>('manual')

// Ручной ввод
const manualRows = ref<RowData[]>([])
const showModal = ref(false)
const editingIndex = ref<number | null>(null)
const editingRow = ref<RowData | null>(null)

// CSV ввод
const csvRows = ref<CsvRow[]>([])

// Общие результаты
const predictions = ref<PredictionResult[]>([])
const loading = ref(false)
const chartRef = ref<HTMLCanvasElement | null>(null)
let chartInstance: Chart | null = null
const topShap = ref<{ feature: string; value: number }[]>([])

const csvStatusText = computed(() => {
  if (csvRows.value.length === 0) return 'No data loaded'
  return `Ready to predict (${csvRows.value.length} samples)`
})

// ==================== РУЧНОЙ ВВОД ====================
function openAddForm() {
  editingIndex.value = null
  editingRow.value = null
  showModal.value = true
}

function openEditForm(index: number) {
  editingIndex.value = index
  editingRow.value = { ...manualRows.value[index] } as RowData
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  editingIndex.value = null
  editingRow.value = null
}

function saveRow(row: RowData) {
  if (editingIndex.value !== null) {
    manualRows.value[editingIndex.value] = row
  } else {
    manualRows.value.push(row)
  }
  closeModal()
}

function removeRow(index: number) {
  manualRows.value.splice(index, 1)
}

async function runManualPrediction() {
  if (manualRows.value.length === 0) {
    alert('No data to predict')
    return
  }

  loading.value = true

  const requests = manualRows.value.map(row => ({
    promo_id: row.promo_id,
    week: row.week,
    month: row.month,
    sku: row.sku,
    category: row.category,
    regular_price: row.regular_price,
    promo_price: row.promo_price,
    store_id: row.store_id,
    region: row.region,
    store_location_type: row.store_location_type,
    format_assortment: row.format_assortment,
    adv_carrier: row.adv_carrier,
    adv_material: row.adv_material,
    promo_mechanics: row.promo_mechanics,
    marketing_type: row.marketing_type,
    analog_sku: [],
    baseline: row.baseline
  }))

  try {
    const response = await predictBatch(requests)
    const results = response.data.predictions || response.data

    predictions.value = results.map((p: any) => ({
      k_uplift: p.k_uplift,
      baseline: p.baseline,
      prediction_absolute: p.prediction_absolute,
      uplift_percent: p.uplift_percent,
      store_id: p.store_id,
      promo_price: p.promo_price
    }))

    if (results[0]?.shap_values?.length) {
      const shapArray = results[0].shap_values
      const shapObj: Record<string, number> = {}
      shapArray.forEach((s: any) => {
        shapObj[s.feature] = Math.abs(s.effect)
      })
      topShap.value = Object.entries(shapObj)
        .map(([feature, value]) => ({ feature, value }))
        .sort((a, b) => b.value - a.value)
        .slice(0, 5)
    }

    await nextTick()
    renderChart()

  } catch (error: any) {
    console.error('Prediction error:', error)
    alert(`Prediction failed: ${error.response?.data?.detail || error.message}`)
  } finally {
    loading.value = false
  }
}

// ==================== CSV ФУНКЦИИ ====================
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

  csvRows.value = lines
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

  console.log("📦 parsed rows", csvRows.value)
}

async function runCSVPrediction() {
  if (csvRows.value.length === 0) {
    alert('No data to predict')
    return
  }

  loading.value = true
  predictions.value = []
  topShap.value = []

  try {
    for (const row of csvRows.value) {
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
      const results = response.data.predictions || response.data
      
      // 🔥 ПРАВИЛЬНАЯ ОБРАБОТКА: берём первый элемент из массива predictions
      const data = results[0] || {}
      
      console.log('🔍 Processed data:', data)

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

      if (data.shap_values && topShap.value.length === 0) {
        const shapArray = data.shap_values
        const shapObj: Record<string, number> = {}
        shapArray.forEach((s: any) => {
          shapObj[s.feature] = Math.abs(s.effect)
        })
        topShap.value = Object.entries(shapObj)
          .map(([feature, value]) => ({ feature, value }))
          .sort((a, b) => b.value - a.value)
          .slice(0, 5)
      }
    }

    console.log('🔍 FINAL predictions.value:', predictions.value)
    
    if (predictions.value.length > 0) {
      await nextTick()
      renderChart()
    }

  } catch (error) {
    console.error("Prediction error:", error)
  } finally {
    loading.value = false
  }
}

// ==================== ГРАФИК ====================
function renderChart() {
  const canvas = chartRef.value
  if (!canvas) return
  if (chartInstance) chartInstance.destroy()
  if (predictions.value.length === 0) return

  chartInstance = new Chart(canvas, {
    type: 'bar',
    data: {
      labels: predictions.value.map((_, i) => i + 1),
      datasets: [
        {
          label: 'Базовые продажи (без промо)',
          data: predictions.value.map(p => p.baseline),
          backgroundColor: 'rgba(255, 99, 132, 0.9)',
          borderColor: 'rgba(255, 99, 132, 1)',
          borderWidth: 1
        },
        {
          label: 'Дополнительные продажи (промо эффект)',
          data: predictions.value.map(p => Math.max(0, p.prediction_absolute - p.baseline)),
          backgroundColor: 'rgba(54, 162, 235, 0.8)',
          borderColor: 'rgba(54, 162, 235, 1)',
          borderWidth: 1
        }
      ]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { position: 'top' },
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
        y: { stacked: true, beginAtZero: true, title: { display: true, text: 'Количество продаж (шт)' } },
        x: { stacked: true, title: { display: true, text: 'Сценарий' } }
      }
    }
  })
}
</script>

<style scoped>
.sticky-top {
  position: sticky;
  top: 0;
  z-index: 10;
}

::placeholder {
  color: #e4e2e2 !important;
  opacity: 1 !important;
}

:-ms-input-placeholder {
  color: #e4e2e2 !important;
}

::-ms-input-placeholder {
  color: #e4e2e2 !important;
}

.table-wrapper {
  overflow-x: auto;
  width: 100%;
}

/* Кнопки не схлопываются */
.btn-sm {
  padding: 0.375rem 0.75rem;
  font-size: 0.875rem;
  white-space: nowrap;
}

.btn-sm i {
  margin-right: 4px;
}

/* Таблица на всю ширину экрана */
.full-width-table {
  position: relative;
  left: 50%;
  right: 50%;
  margin-left: -50vw;
  margin-right: -50vw;
  width: 100vw;
}

/* Убираем скругления у карточки для полной ширины */
.full-width-table .card {
  border-radius: 0;
  margin-left: 0;
  margin-right: 0;
}

/* Если нужно убрать горизонтальный скролл у body */
body {
  overflow-x: hidden;
}


.text-success {
  color: #198754 !important;
  font-weight: bold;
}

.text-danger {
  color: #dc3545 !important;
  font-weight: bold;
}

.text-info {
  color: #0dcaf0 !important;
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