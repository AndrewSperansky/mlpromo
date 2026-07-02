<!-- frontend/src/components/LSTMTrainingChart.vue -->
 
<template>
  <div class="card shadow-sm border-0">
    <div class="card-header bg-white d-flex justify-content-between align-items-center">
      <div>
        <i class="bi bi-graph-up me-2 text-primary"></i>
        <strong>{{ title }}</strong>
        <span class="badge bg-secondary ms-2">{{ modelType }}</span>
      </div>
      <span v-if="bestValLoss !== null" class="badge bg-success">
        Best: {{ bestValLoss.toFixed(6) }}
      </span>
    </div>
    <div class="card-body">
      <div v-if="loading" class="text-center py-4">
        <div class="spinner-border text-primary"></div>
        <p class="mt-2 text-muted">Loading training metrics...</p>
      </div>
      
      <div v-else-if="data.train_loss?.length" class="chart-container">
        <canvas ref="chartRef" height="120"></canvas>
        <div class="mt-3 d-flex justify-content-between small text-muted">
          <span>Epochs: {{ data.total_epochs || data.train_loss.length }}</span>
          <span v-if="data.best_val_loss !== null">
            Best Val Loss: {{ data.best_val_loss.toFixed(6) }}
          </span>
          <span v-else>No validation data</span>
        </div>
      </div>
      
      <div v-else class="text-center py-4 text-muted">
        <i class="bi bi-bar-chart fs-1"></i>
        <p class="mt-2">{{ message || 'No training data available' }}</p>
        <p class="small">{{ hint || 'Train LSTM model first' }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'  // ← добавлен computed!
import Chart from 'chart.js/auto'

interface TrainingData {
  iterations: number[]
  train_loss: number[]
  val_loss: number[]
  best_epoch: number | null
  best_val_loss: number | null
  total_epochs: number
  message?: string
  error?: string
}

const props = defineProps<{
  data: TrainingData
  title?: string
  modelType?: string
  message?: string
  hint?: string
  loading?: boolean
}>()

const chartRef = ref<HTMLCanvasElement | null>(null)
let chartInstance: Chart | null = null

const bestValLoss = computed(() => props.data?.best_val_loss ?? null)  // ← теперь computed работает!

function render() {
  const canvas = chartRef.value
  if (!canvas) return
  
  if (!props.data?.train_loss?.length) {
    if (chartInstance) {
      chartInstance.destroy()
      chartInstance = null
    }
    return
  }
  
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  
  if (chartInstance) {
    chartInstance.destroy()
    chartInstance = null
  }
  
  const labels = props.data.iterations || props.data.train_loss.map((_, i) => i + 1)
  const hasValidation = props.data.val_loss?.length > 0
  
  const datasets: any[] = [  // ← явно указываем any[]
    {
      label: 'Train Loss',
      data: props.data.train_loss,
      borderColor: 'rgb(54, 162, 235)',
      backgroundColor: 'rgba(54, 162, 235, 0.1)',
      fill: true,
      tension: 0.3,
      pointRadius: 0,
    }
  ]
  
  if (hasValidation) {
    datasets.push({
      label: 'Validation Loss',
      data: props.data.val_loss,
      borderColor: 'rgb(255, 99, 132)',
      backgroundColor: 'rgba(255, 99, 132, 0.1)',
      fill: true,
      tension: 0.3,
      pointRadius: 0,
      borderDash: [5, 5],  // ← теперь не ругается, т.к. массив any[]
    })
  }
  
  chartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets,
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        tooltip: {
          callbacks: {
            label: (context: any) => {
              const value = context.raw
              return `${context.dataset.label}: ${value.toFixed(6)}`
            }
          }
        },
        legend: {
          position: 'top',
        }
      },
      scales: {
        y: {
          title: { display: true, text: 'Loss' },
          beginAtZero: true,
        },
        x: {
          title: { display: true, text: 'Epoch' },
        }
      }
    }
  })
}

watch(() => props.data, async () => {
  await nextTick()
  render()
}, { deep: true, immediate: true })

onMounted(() => {
  nextTick(() => render())
})

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.destroy()
    chartInstance = null
  }
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
.chart-container {
  position: relative;
}
</style>