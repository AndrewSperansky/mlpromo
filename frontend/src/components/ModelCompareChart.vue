<!-- frontend/src/components/ModelCompareChart.vue -->

<template>
  <div class="card shadow-sm border-0 mt-4">
    <div class="card-header bg-white">
      <strong>Model Comparison (RMSE + Confidence Interval)</strong>
    </div>
    <div class="card-body">
      <canvas ref="chartRef" height="100"></canvas>
      
      <div class="mt-3 small" :class="ciOverlap ? 'text-warning' : 'text-success'">
        <i :class="ciOverlap ? 'bi bi-exclamation-triangle-fill' : 'bi bi-check-circle-fill'" class="me-1"></i>
        <span v-if="ciOverlap">
          ⚠️ Confidence intervals overlap → no statistically significant improvement
        </span>
        <span v-else>
          ✅ Confidence intervals do not overlap → improvement is statistically significant
        </span>
      </div>
      
      <div class="mt-2 small text-muted">
        <i class="bi bi-info-circle-fill me-1"></i>
        Current model: RMSE = {{ currentRMSE?.toFixed(6) }} 
        <span v-if="currentCI">(CI: {{ currentCI.lower?.toFixed(6) }} – {{ currentCI.upper?.toFixed(6) }})</span>
        <br>
        Candidate model: RMSE = {{ candidateRMSE?.toFixed(6) }}
        <span v-if="candidateCI">(CI: {{ candidateCI.lower?.toFixed(6) }} – {{ candidateCI.upper?.toFixed(6) }})</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import Chart from 'chart.js/auto'

const props = defineProps<{
  comparison: any
}>()

const chartRef = ref<HTMLCanvasElement | null>(null)
let chart: Chart | null = null

const currentRMSE = computed(() => props.comparison?.current_metrics?.rmse)
const candidateRMSE = computed(() => props.comparison?.candidate_metrics?.rmse)
const currentCI = computed(() => props.comparison?.current_metrics?.rmse_ci)
const candidateCI = computed(() => props.comparison?.candidate_metrics?.rmse_ci)

const ciOverlap = computed(() => {
  const c1 = currentCI.value
  const c2 = candidateCI.value
  
  if (!c1 || !c2) return false
  
  // Проверяем пересечение интервалов
  return !(c2.upper < c1.lower || c2.lower > c1.upper)
})

function render() {
  if (!chartRef.value) return
  
  if (chart) chart.destroy()
  
  const ctx = chartRef.value.getContext('2d')
  if (!ctx) return
  
  const labels = ['Current Model', 'Candidate Model']
  
  const rmseData = [currentRMSE.value, candidateRMSE.value]
  const ciLowerData = [currentCI.value?.lower, candidateCI.value?.lower]
  const ciUpperData = [currentCI.value?.upper, candidateCI.value?.upper]
  
  chart = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: 'RMSE',
          data: rmseData,
          borderColor: 'rgb(54, 162, 235)',
          backgroundColor: 'rgba(54, 162, 235, 0.1)',
          borderWidth: 2,
          pointRadius: 6,
          pointBackgroundColor: 'rgb(54, 162, 235)',
          tension: 0.1
        },
        {
          label: 'CI Lower Bound',
          data: ciLowerData,
          borderColor: 'rgba(255, 99, 132, 0.5)',
          borderDash: [5, 5],
          borderWidth: 1,
          pointRadius: 0,
          fill: false
        },
        {
          label: 'CI Upper Bound',
          data: ciUpperData,
          borderColor: 'rgba(255, 99, 132, 0.5)',
          borderDash: [5, 5],
          borderWidth: 1,
          pointRadius: 0,
          fill: false
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
              if (value === undefined || value === null) return ''
              if (context.dataset.label === 'RMSE') {
                return `RMSE: ${value.toFixed(6)}`
              }
              return `${context.dataset.label}: ${value.toFixed(6)}`
            }
          }
        },
        legend: {
          position: 'bottom'
        }
      },
      scales: {
        y: {
          title: {
            display: true,
            text: 'RMSE'
          },
          beginAtZero: false
        }
      }
    }
  })
}

watch(() => props.comparison, async (newVal) => {
  console.log('🔍 ModelCompareChart received comparison:', newVal)
  await nextTick()
  if (newVal) {
    render()
  }
}, { immediate: true, deep: true })

// 🔥 Дополнительно: перерисовка при монтировании, если данные уже есть
onMounted(() => {
  if (props.comparison && (props.comparison.current_metrics || props.comparison.candidate_metrics)) {
    render()
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
</style>