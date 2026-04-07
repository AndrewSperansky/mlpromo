<!-- frontend/src/components/ManualPredictForm.vue -->

<template>
  <div class="modal-backdrop" @click.self="$emit('close')">
    <div class="modal-box">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h3>{{ isEdit ? 'Edit Row' : 'Add New Row' }}</h3>
        <button class="btn-close" @click="$emit('close')"></button>
      </div>

      <div class="form-container">
        <div class="row">
          <div class="col-md-6 mb-3">
            <label class="form-label fw-bold">Promo ID <span class="text-danger">*</span></label>
            <input v-model="formData.promo_id" class="form-control"
              :class="{ 'is-invalid': !formData.promo_id && touched }" placeholder="" />
          </div>
          <div class="col-md-3 mb-3">
            <label class="form-label fw-bold">Week <span class="text-danger">*</span></label>
            <input v-model.number="formData.week" type="number" class="form-control"
              :class="{ 'is-invalid': !formData.week && touched }" placeholder="" />
          </div>
          <div class="col-md-3 mb-3">
            <label class="form-label fw-bold">Month <span class="text-danger">*</span></label>
            <input v-model.number="formData.month" type="number" class="form-control"
              :class="{ 'is-invalid': !formData.month && touched }" placeholder="" />
          </div>
        </div>

        <!-- ... остальные поля формы (без изменений) ... -->

      </div>

      <div class="d-flex justify-content-end gap-2 mt-3 pt-3 border-top">
        <button class="btn btn-secondary" @click="$emit('close')">Cancel</button>
        <button class="btn btn-primary" @click="save" :disabled="!isValid">
          {{ isEdit ? 'Update' : 'Add' }}
        </button>
      </div>

      <!-- ===== Prediction Interval Display ===== -->
      <div v-if="showInterval && interval" class="mt-3 pt-3 border-top">
        <div class="alert" :class="intervalAlertClass">
          <div class="d-flex justify-content-between align-items-center">
            <div>
              <strong>Prediction Interval (95%):</strong>
              <span class="ms-2">
                [{{ interval.lower[0]?.toFixed(2) ?? '?' }} — {{ interval.upper[0]?.toFixed(2) ?? '?' }}]
              </span>
            </div>
            <span :class="uncertaintyBadgeClass" class="badge">
              {{ uncertaintyLabel }}
            </span>
          </div>
          <div class="progress mt-2" style="height: 6px;">
            <div class="progress-bar" :class="uncertaintyBarClass" :style="{ width: uncertaintyWidth + '%' }"></div>
          </div>
          <small class="text-muted mt-1 d-block">
            Width: {{ intervalWidth.toFixed(2) }} |
            Lower bound: {{ interval.lower[0]?.toFixed(2) ?? '?' }} |
            Upper bound: {{ interval.upper[0]?.toFixed(2) ?? '?' }}
          </small>
        </div>
      </div>
    </div>
  </div>
</template>

// ManualPredictForm.vue

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { predictWithInterval } from '../services/api'

interface ManualRow {
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

// Расширенный тип для эмита
interface ManualRowWithPrediction extends ManualRow {
  prediction?: number
  interval?: { lower: number[]; upper: number[] }
  has_interval?: boolean
}

const props = defineProps<{
  row?: ManualRow | null
  index?: number | null
}>()

// ✅ defineEmits НА ВЕРХНЕМ УРОВНЕ
const emit = defineEmits<{
  (e: 'close'): void
  (e: 'save', row: ManualRowWithPrediction): void
}>()

const touched = ref(false)
const isEdit = computed(() => props.index !== null && props.row !== null)

// ===== STATE =====
const interval = ref<{ lower: number[]; upper: number[] } | null>(null)
const showInterval = ref(false)

const formData = ref<ManualRow>({
  promo_id: '',
  week: 0,
  month: 0,
  sku: '',
  category: '',
  regular_price: 0,
  promo_price: 0,
  store_id: '',
  region: '',
  store_location_type: '',
  format_assortment: 'na',
  adv_carrier: 'ЖЦ',
  adv_material: 'na',
  promo_mechanics: 'na',
  marketing_type: 'Скидка по карте!',
  baseline: 1
})

watch(() => props.row, (newRow) => {
  if (newRow) {
    formData.value = { ...newRow }
    interval.value = null
    showInterval.value = false
  }
}, { immediate: true })

const isValid = computed(() => {
  return !!(formData.value.promo_id && 
    formData.value.sku && 
    formData.value.store_id && 
    formData.value.regular_price && 
    formData.value.promo_price)
})

// ===== COMPUTED для интервала =====
const intervalWidth = computed(() => {
  if (!interval.value) return 0
  const lower = interval.value.lower[0] ?? 0
  const upper = interval.value.upper[0] ?? 0
  return upper - lower
})

const uncertaintyLabel = computed(() => {
  const width = intervalWidth.value
  if (width < 10) return 'LOW'
  if (width < 30) return 'MEDIUM'
  return 'HIGH'
})

const uncertaintyBadgeClass = computed(() => {
  const width = intervalWidth.value
  if (width < 10) return 'bg-success'
  if (width < 30) return 'bg-warning'
  return 'bg-danger'
})

const uncertaintyBarClass = computed(() => {
  const width = intervalWidth.value
  if (width < 10) return 'bg-success'
  if (width < 30) return 'bg-warning'
  return 'bg-danger'
})

const uncertaintyWidth = computed(() => {
  const width = intervalWidth.value
  return Math.min(100, (width / 50) * 100)
})

const intervalAlertClass = computed(() => {
  const width = intervalWidth.value
  if (width < 10) return 'alert-success'
  if (width < 30) return 'alert-warning'
  return 'alert-danger'
})

// ===== METHODS =====
function closeModal() {
  interval.value = null
  showInterval.value = false
  emit('close')
}

async function save() {
  touched.value = true
  if (!isValid.value) return

  const rowToSave = {
    ...formData.value,
    format_assortment: formData.value.format_assortment || 'na',
    adv_carrier: formData.value.adv_carrier || 'ЖЦ',
    adv_material: formData.value.adv_material || 'na',
    promo_mechanics: formData.value.promo_mechanics || 'na',
    marketing_type: formData.value.marketing_type || 'Скидка по карте!',
  }

  try {
    const result = await predictWithInterval(rowToSave)

    // Сохраняем интервал для отображения
    if (result.interval && result.has_interval) {
      interval.value = result.interval
      showInterval.value = true
    } else {
      interval.value = null
      showInterval.value = false
    }

    // ✅ Эмитим результат с предсказанием (используем emit из верхнего уровня)
    emit('save', {
      ...rowToSave,
      prediction: result.prediction,
      interval: result.interval,
      has_interval: result.has_interval
    })

    closeModal()
  } catch (error) {
    console.error('Prediction failed:', error)
    alert('Failed to get prediction')
  }
}
</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1050;
}

.modal-box {
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
  width: 90%;
  max-width: 800px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

.form-container {
  flex: 1;
  overflow-y: auto;
  padding-right: 8px;
}

.btn-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
}

.is-invalid {
  border-color: #dc3545;
  background-color: #fff3f3;
}

.text-danger {
  color: #dc3545;
}

/* Interval styles */
.progress {
  background-color: #e9ecef;
  border-radius: 3px;
}

.progress-bar {
  transition: width 0.3s ease;
}

.alert {
  padding: 12px;
  border-radius: 8px;
}

.alert-success {
  background-color: #d1e7dd;
  border-color: #badbcc;
  color: #0f5132;
}

.alert-warning {
  background-color: #fff3cd;
  border-color: #ffecb5;
  color: #856404;
}

.alert-danger {
  background-color: #f8d7da;
  border-color: #f5c2c7;
  color: #842029;
}

.bg-success {
  background-color: #198754 !important;
}

.bg-warning {
  background-color: #ffc107 !important;
  color: #000 !important;
}

.bg-danger {
  background-color: #dc3545 !important;
}
</style>