<!-- frontend/src/components/ManualPredictModal.vue -->
 <!-- ГОРИЗОНТАЛЬНАЯ ФОРМА-ТАБЛИЦА В МОДАЛЬНОМ ОКНЕ -->

<template>
  <div class="modal-backdrop" @click.self="$emit('close')">
    <div class="modal-box">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h3>Manual Batch Prediction</h3>
        <button class="btn-close" @click="$emit('close')"></button>
      </div>
      
      <div class="mb-3">
        <button class="btn btn-sm btn-success" @click="addRow">
          <i class="bi bi-plus-lg"></i> Add Row
        </button>
      </div>
      
      <div class="table-responsive" style="max-height: 60vh; overflow-y: auto;">
        <table class="table table-sm table-bordered">
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
              <th style="width: 50px"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, idx) in rows" :key="idx">
              <td class="text-center">{{ idx + 1 }}</td>
              <td><input v-model="row.promo_id" class="form-control form-control-sm" placeholder="промо-12-2025" /></td>
              <td><input v-model.number="row.week" type="number" class="form-control form-control-sm" placeholder="26" /></td>
              <td><input v-model.number="row.month" type="number" class="form-control form-control-sm" placeholder="6" /></td>
              <td><input v-model="row.sku" class="form-control form-control-sm" placeholder="РН235555" /></td>
              <td><input v-model="row.category" class="form-control form-control-sm" placeholder="Охлажденка" /></td>
              <td><input v-model.number="row.regular_price" type="number" step="0.01" class="form-control form-control-sm" placeholder="269.99" /></td>
              <td><input v-model.number="row.promo_price" type="number" step="0.01" class="form-control form-control-sm" placeholder="209.99" /></td>
              <td><input v-model="row.store_id" class="form-control form-control-sm" placeholder="МГЗ №461" /></td>
              <td><input v-model="row.region" class="form-control form-control-sm" placeholder="МСК" /></td>
              <td><input v-model="row.store_location_type" class="form-control form-control-sm" placeholder="Трассовый" /></td>
              <td><input v-model="row.format_assortment" class="form-control form-control-sm" placeholder="na" /></td>
              <td><input v-model="row.adv_carrier" class="form-control form-control-sm" placeholder="ЖЦ" /></td>
              <td><input v-model="row.adv_material" class="form-control form-control-sm" placeholder="na" /></td>
              <td><input v-model="row.promo_mechanics" class="form-control form-control-sm" placeholder="na" /></td>
              <td><input v-model="row.marketing_type" class="form-control form-control-sm" placeholder="Скидка по карте!" /></td>
              <td><input v-model.number="row.baseline" type="number" step="0.01" class="form-control form-control-sm" placeholder="100" /></td>
              <td class="text-center">
                <button class="btn btn-sm btn-outline-danger" @click="removeRow(idx)">
                  <i class="bi bi-trash3"></i>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <div class="d-flex justify-content-end gap-2 mt-3 pt-3 border-top">
        <button class="btn btn-secondary" @click="$emit('close')">Cancel</button>
        <button class="btn btn-primary" @click="runPrediction" :disabled="loading">
          <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
          {{ loading ? 'Predicting...' : 'Run Prediction' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { predictBatch } from '../services/api'

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

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'predict', predictions: any[]): void
}>()

const rows = ref<ManualRow[]>([getEmptyRow()])
const loading = ref(false)

function getEmptyRow(): ManualRow {
  return {
    promo_id: 'промо-3-2026',
    week: 26,
    month: 6,
    sku: 'РН235555',
    category: 'Охлажденка',
    regular_price: 269,
    promo_price: 149,
    store_id: 'МГЗ №461',
    region: 'МСК',
    store_location_type: 'Трассовый',
    format_assortment: 'na',
    adv_carrier: 'na',
    adv_material: 'na',
    promo_mechanics: 'na',
    marketing_type: 'Скидка по карте!',
    baseline: undefined
  }
}

function addRow() {
  rows.value.push(getEmptyRow())
}

function removeRow(index: number) {
  rows.value.splice(index, 1)
}

async function runPrediction() {
  loading.value = true
  
  // Фильтруем только заполненные строки (с promo_id)
  const validRows = rows.value.filter(row => row.promo_id && row.sku)
  
  if (validRows.length === 0) {
    alert('Please fill at least one row with promo_id and sku')
    loading.value = false
    return
  }
  
  const requests = validRows.map(row => ({
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

  // 🔥 ПОДРОБНОЕ ЛОГИРОВАНИЕ
  console.log('📤 Sending batch request with', requests.length, 'items')
  console.log('📤 First request:', JSON.stringify(requests[0], null, 2))
  
  try {
    const response = await predictBatch(requests)
    const predictions = response.data.predictions || response.data
    emit('predict', predictions)
    emit('close')
  } catch (error: any) {
    console.error('Batch prediction error:', error)
    const detail = error.response?.data?.detail
    if (typeof detail === 'object') {
      alert(`Prediction failed: ${detail.message || JSON.stringify(detail)}`)
    } else {
      alert(`Prediction failed: ${detail || error.message}`)
    }
  } finally {
    loading.value = false
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
  max-width: 1400px;
  max-height: 90vh;
  overflow-y: auto;
}

.sticky-top {
  position: sticky;
  top: 0;
  z-index: 10;
}

.btn-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
}

.table-responsive {
  overflow-x: auto;
}

.form-control-sm {
  font-size: 0.875rem;
  padding: 0.25rem 0.5rem;
}
</style>