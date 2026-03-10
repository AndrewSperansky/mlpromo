<!-- frontend/src/pages/Predict.vue -->

<template>
  <div>

    <h2 class="mb-4">Predictions Test Page</h2>

    <div class="input-group mb-3">
      <!-- Левая кнопка (зеленая) -->
      <label class="btn btn-primary" for="csvUpload">
        <i class="bi bi-cloud-upload me-2"></i>Load CSV
        <input type="file" id="csvUpload" class="d-none" accept=".csv" @change="handleCSVUpload" />
      </label>

      <!-- Отображение статуса (вместо input) -->
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

      <!-- Правая кнопка (зеленая) -->
      <button class="btn btn-success" type="button" :disabled="!rows.length || loading" @click="runBatchPredict">
        <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
        <i v-else class="bi bi-play-fill me-2"></i>
        {{ loading ? 'Predicting...' : 'Run' }}
      </button>
    </div>

    <div v-if="predictions.length" class="mb-4">
      <canvas ref="chartRef"></canvas>
    </div>

    <div v-if="topShap.length">
      <h5>Top 5 SHAP Features</h5>
      <ul>
        <li v-for="item in topShap" :key="item.feature">
          {{ item.feature }} : {{ item.value.toFixed(4) }}
        </li>
      </ul>
    </div>

  </div>
</template>

<script setup lang="ts">

import { predictBatch } from '../services/api'
import Chart from 'chart.js/auto'
import { ref, nextTick, computed } from 'vue'  // ← ВАЖНО: добавили computed

interface CsvRow {
  [key: string]: number
}

const rows = ref<CsvRow[]>([])
const predictions = ref<number[]>([])
const loading = ref(false)
const chartRef = ref<HTMLCanvasElement | null>(null)
let chartInstance: Chart | null = null
const topShap = ref<{ feature: string; value: number }[]>([])

const statusText = computed(() => {
  if (!rows.value.length) return 'No data loaded'
  return `Ready to predict (${rows.value.length} samples)`
})

const distributionChartRef = ref<HTMLCanvasElement | null>(null)
const shapChartRef = ref<HTMLCanvasElement | null>(null)
const heatmapChartRef = ref<HTMLCanvasElement | null>(null)

let distributionChart: Chart | null = null
let shapChart: Chart | null = null
let heatmapChart: Chart | null = null


// =========================
// SAFE CSV UPLOAD
// =========================

function handleCSVUpload(event: Event) {

  const input = event.target as HTMLInputElement | null
  if (!input) return

  const files = input.files
  if (!files || files.length === 0) return

  const file = files.item(0)
  if (!file) return   // ← ВАЖНО для strict TS

  const reader = new FileReader()

  reader.onload = () => {
    const result = reader.result
    if (typeof result !== 'string') return
    parseCSV(result)
  }

  reader.readAsText(file)
}


// =========================
// CSV PARSER (STRICT SAFE)
// =========================

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

        // convert only numeric fields
        if (header === "price" || header === "discount") {

          const num = Number(raw)
          obj[header] = isNaN(num) ? 0 : num

        } else {
          obj[header] = raw
        }
      })

      return obj
    })

  console.log("📦 parsed rows", rows.value)

}


// =========================
// BATCH PREDICT
// =========================

async function runBatchPredict() {
  loading.value = true

  try {
    predictions.value = []
    topShap.value = []

    // Проходим по каждой строке и отправляем отдельный запрос
    for (const row of rows.value) {

      // Добавляем недостающие поля со значениями по умолчанию
      const payload = {
        promo_code: String(row.promo_code),
        sku: String(row.sku),
        prediction_date: String(row.prediction_date),
        price: Number(row.price),
        discount: Number(row.discount),

        // ОБЯЗАТЕЛЬНЫЕ ПОЛЯ, КОТОРЫХ НЕТ В CSV
        avg_sales_7d: 100,  // значение по умолчанию
        avg_discount_7d: 5, // значение по умолчанию
        promo_days_left: 7, // значение по умолчанию
      }

      console.log("📤 sending payload", payload)

      // Отправляем ОДИН объект, не массив!
      const response = await predictBatch(payload)

      const prediction = response.data?.prediction
      if (prediction !== undefined) {
        predictions.value.push(prediction)
      }

      // SHAP для первой строки (или для всех, если нужно)
      if (response.data?.shap_values && topShap.value.length === 0) {
        const shapArray = response.data.shap_values
        const shapObj: Record<string, number> = {}
        shapArray.forEach((s: any) => {
          shapObj[s.feature] = s.effect
        })
        computeTopShap(shapObj)
      }
    }

    await nextTick()
    renderChart()
    renderDistributionChart()
    renderShapChart()
    renderHeatmap()

  } catch (error) {
    console.error("Prediction error:", error)
  } finally {
    loading.value = false
  }
}


// =========================
// CHART
// =========================

function renderChart() {

  const canvas = chartRef.value
  if (!canvas) return

  if (chartInstance) {
    chartInstance.destroy()
  }

  chartInstance = new Chart(canvas, {
    type: 'line',
    data: {
      labels: predictions.value.map((_, i) => i + 1),
      datasets: [{
        label: 'Predictions',
        data: predictions.value
      }]
    }
  })
}

function renderDistributionChart() {

  const canvas = distributionChartRef.value
  if (!canvas) return

  if (distributionChart) {
    distributionChart.destroy()
  }

  distributionChart = new Chart(canvas, {

    type: 'bar',

    data: {

      labels: predictions.value.map((_, i) => `S${i + 1}`),

      datasets: [{
        label: 'Prediction distribution',
        data: predictions.value
      }]

    }

  })
}


function renderShapChart() {

  const canvas = shapChartRef.value
  if (!canvas) return

  if (shapChart) {
    shapChart.destroy()
  }

  shapChart = new Chart(canvas, {

    type: 'bar',

    data: {

      labels: topShap.value.map(s => s.feature),

      datasets: [{
        label: 'SHAP impact',
        data: topShap.value.map(s => s.value)
      }]

    },

    options: {
      indexAxis: 'y'
    }

  })
}

function renderHeatmap() {

  const canvas = heatmapChartRef.value
  if (!canvas) return

  if (heatmapChart) {
    heatmapChart.destroy()
  }

  heatmapChart = new Chart(canvas, {

    type: 'bar',

    data: {

      labels: topShap.value.map(v => v.feature),

      datasets: [{
        label: 'Feature strength',
        data: topShap.value.map(v => v.value)
      }]

    },

    options: {

      plugins: {
        legend: { display: false }
      }

    }

  })
}

// =========================
// SHAP TOP 5
// =========================

function computeTopShap(shapObj: Record<string, number>) {

  const sorted = Object.entries(shapObj)
    .map(([feature, value]) => ({
      feature,
      value: Math.abs(Number(value))
    }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 5)

  topShap.value = sorted
}

</script>

<style scoped>
.border-success.border-dashed {
  border-style: dashed !important;
  transition: all 0.3s ease;
}

.border-success.border-dashed:hover {
  background-color: rgba(25, 135, 84, 0.15) !important;
  cursor: pointer;
}

.btn-outline-success:hover i {
  transform: scale(1.1);
  transition: transform 0.2s ease;
}
</style>