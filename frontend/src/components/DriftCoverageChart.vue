<!-- frontend/src/components/DriftCoverageChart.vue -->

<template>
  <div class="card shadow-sm border-0 mt-4">
    <div class="card-header bg-white d-flex justify-content-between align-items-center">
      <strong><i class="bi bi-graph-up me-2"></i>Drift & Coverage (Real-time)</strong>
      <span class="badge" :class="driftStatusClass">
        Drift: {{ (currentDrift * 100).toFixed(1) }}%
      </span>
    </div>
    <div class="card-body">
      <canvas ref="chartRef" height="100"></canvas>
      
      <div class="mt-3 small">
        <div class="d-flex justify-content-between">
          <div>
            <i class="bi bi-circle-fill text-danger me-1"></i> Drift Score
            <span class="text-muted ms-2">(0 = stable, 1 = high drift)</span>
          </div>
          <div>
            <i class="bi bi-circle-fill text-success me-1"></i> Coverage
            <span class="text-muted ms-2">(target: 95%)</span>
          </div>
        </div>
        <div class="mt-2" v-if="currentCoverage">
          <i class="bi bi-info-circle-fill me-1"></i>
          Current coverage: <strong :class="coverageStatusClass">{{ (currentCoverage * 100).toFixed(1) }}%</strong>
          <span v-if="currentCoverage < 0.92" class="text-warning ms-2">⚠️ Below target (95%)</span>
          <span v-else-if="currentCoverage > 0.98" class="text-success ms-2">✅ Good calibration</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import Chart from 'chart.js/auto'

const chartRef = ref<HTMLCanvasElement | null>(null)
let chart: Chart | null = null
let intervalId: number | null = null

const currentDrift = ref(0)
const currentCoverage = ref(0)

const driftStatusClass = computed(() => {
  if (currentDrift.value < 0.1) return 'bg-success'
  if (currentDrift.value < 0.3) return 'bg-warning'
  return 'bg-danger'
})

const coverageStatusClass = computed(() => {
  if (currentCoverage.value >= 0.94 && currentCoverage.value <= 0.96) return 'text-success'
  if (currentCoverage.value >= 0.92) return 'text-warning'
  return 'text-danger'
})

async function loadData() {
  try {
    const res = await axios.get('/api/v1/ml/monitoring/drift')
    currentDrift.value = res.data.current_drift || 0
    currentCoverage.value = res.data.current_coverage || 0
    return res.data.points || []
  } catch (error) {
    console.error('Failed to load drift data:', error)
    return []
  }
}

async function render() {
  const data = await loadData()
  
  if (!chartRef.value) return
  if (chart) chart.destroy()
  
  const ctx = chartRef.value.getContext('2d')
  if (!ctx) return
  
  if (data.length === 0) {
    // Показываем сообщение о недостатке данных
    chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: ['No data yet'],
        datasets: [
          { label: 'Drift', data: [0], borderColor: 'red' },
          { label: 'Coverage', data: [0], borderColor: 'green' }
        ]
      },
      options: {
        plugins: {
          tooltip: { callbacks: { label: () => 'No drift data available' } }
        }
      }
    })
    return
  }
  
  const labels = data.map((d: any) => {
    const date = new Date(d.time)
    return date.toLocaleTimeString()
  })
  const drift = data.map((d: any) => d.drift)
  const coverage = data.map((d: any) => d.coverage)
  
  chart = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: 'Drift Score',
          data: drift,
          borderColor: 'rgb(220, 53, 69)',
          backgroundColor: 'rgba(220, 53, 69, 0.1)',
          tension: 0.3,
          fill: true
        },
        {
          label: 'Coverage',
          data: coverage,
          borderColor: 'rgb(40, 167, 69)',
          backgroundColor: 'rgba(40, 167, 69, 0.1)',
          tension: 0.3,
          fill: true
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        tooltip: {
          callbacks: {
            label: (context: any) => {
              const value = context.raw
              if (context.dataset.label === 'Coverage') {
                return `Coverage: ${(value * 100).toFixed(1)}%`
              }
              return `${context.dataset.label}: ${value.toFixed(3)}`
            }
          }
        }
      },
      scales: {
        y: {
          title: { display: true, text: 'Score' },
          min: 0,
          max: 1
        },
        x: {
          title: { display: true, text: 'Time' }
        }
      }
    }
  })
}

onMounted(() => {
  render()
  intervalId = setInterval(() => {
    render()
  }, 30000) as unknown as number
})

onUnmounted(() => {
  if (intervalId) clearInterval(intervalId)
  if (chart) chart.destroy()
})
</script>

<style scoped>
.card {
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15) !important;
}
</style>