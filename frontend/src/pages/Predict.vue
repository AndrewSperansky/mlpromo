<!-- frontend/src/pages/Predict.vue -->

<template>
  <div>

    <h2 class="mb-4">Predictions Test Page</h2>

    <div class="mb-3">
      <input type="file" accept=".csv" @change="handleCSVUpload" />
    </div>

    <button class="btn btn-primary mb-3" :disabled="!rows.length || loading" @click="runBatchPredict">
      {{ loading ? 'Predicting...' : 'Run Batch Predict' }}
    </button>

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
import { ref, nextTick } from 'vue'
import { predictBatch } from '../services/api'
import Chart from 'chart.js/auto'

interface CsvRow {
  [key: string]: number
}

const rows = ref<CsvRow[]>([])
const predictions = ref<number[]>([])
const loading = ref(false)
const chartRef = ref<HTMLCanvasElement | null>(null)
let chartInstance: Chart | null = null
const topShap = ref<{ feature: string; value: number }[]>([])


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
      const obj: CsvRow = {}

      headers.forEach((header, index) => {

        const raw = values[index] ?? '0'
        const parsed = Number(raw.trim())

        obj[header] = isNaN(parsed) ? 0 : parsed
      })

      return obj
    })
}


// =========================
// BATCH PREDICT
// =========================

async function runBatchPredict() {

  loading.value = true

  try {

    const response = await predictBatch(rows.value)

    predictions.value = response.data?.predictions ?? []

    const shapArray = response.data?.shap_values
    if (Array.isArray(shapArray) && shapArray.length > 0) {
      computeTopShap(shapArray[0])
    }

    await nextTick()
    renderChart()

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