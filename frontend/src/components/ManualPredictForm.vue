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
            <label class="form-label fw-bold">Promo ID </label>
            <input v-model="formData.promo_id" class="form-control" placeholder="" />
          </div>
          <div class="col-md-3 mb-3">
            <label class="form-label fw-bold">Week <span class="text-danger">*</span></label>
            <input v-model.number="formData.week" type="number" class="form-control" :class="{ 'is-invalid': !formData.week && touched }" placeholder="" />
          </div>
          <div class="col-md-3 mb-3">
            <label class="form-label fw-bold">Month <span class="text-danger">*</span></label>
            <input v-model.number="formData.month" type="number" class="form-control" :class="{ 'is-invalid': !formData.month && touched }" placeholder="" />
          </div>
        </div>
        
        <div class="row">
          <div class="col-md-6 mb-3">
            <label class="form-label fw-bold">SKU <span class="text-danger">*</span></label>
            <input v-model="formData.sku" class="form-control" :class="{ 'is-invalid': !formData.sku && touched }" placeholder="" />
          </div>
          <div class="col-md-6 mb-3">
            <label class="form-label fw-bold">Category <span class="text-danger">*</span></label>
            <input v-model="formData.category" class="form-control" :class="{ 'is-invalid': !formData.category && touched }" placeholder="" />
          </div>
        </div>
        
        <div class="row">
          <div class="col-md-6 mb-3">
            <label class="form-label fw-bold">Regular Price <span class="text-danger">*</span></label>
            <input v-model.number="formData.regular_price" type="number" step="0.01" class="form-control" :class="{ 'is-invalid': !formData.regular_price && touched }" placeholder="" />
          </div>
          <div class="col-md-6 mb-3">
            <label class="form-label fw-bold">Promo Price <span class="text-danger">*</span></label>
            <input v-model.number="formData.promo_price" type="number" step="0.01" class="form-control" :class="{ 'is-invalid': !formData.promo_price && touched }" placeholder="" />
          </div>
        </div>
        
        <div class="row">
          <div class="col-md-6 mb-3">
            <label class="form-label fw-bold">Store ID <span class="text-danger">*</span></label>
            <input v-model="formData.store_id" class="form-control" :class="{ 'is-invalid': !formData.store_id && touched }" placeholder="" />
          </div>

          <div class="col-md-3 mb-3">
            <label class="form-label fw-bold">Region <span class="text-danger">*</span></label>
            <input v-model="formData.region" class="form-control" :class="{ 'is-invalid': !formData.region && touched }" placeholder="" />
          </div>

          <div class="col-md-3 mb-3">
            <label class="form-label fw-bold">Store Location Type <span class="text-danger">*</span></label>
            <input v-model="formData.store_location_type" class="form-control" :class="{ 'is-invalid': !formData.store_location_type && touched }" placeholder="" />
          </div>
        </div>
        
      
        <div class="row">
          <div class="col-md-6 mb-3">
            <label class="form-label fw-bold">Promo Mechanics</label>
            <input v-model="formData.promo_mechanics" class="form-control" placeholder="" />
          </div>

          <div class="col-md-3 mb-3">
            <label class="form-label fw-bold">Adv Carrier</label>
            <input v-model="formData.adv_carrier" class="form-control" placeholder="" />
          </div>

          <div class="col-md-3 mb-3">
            <label class="form-label fw-bold">Adv Material</label>
            <input v-model="formData.adv_material" class="form-control" placeholder="" />
          </div>
        </div>
        
        <div class="row">
          <div class="col-md-6 mb-3">
            <label class="form-label fw-bold">Format Assortment <span class="text-danger">*</span></label>
            <input v-model="formData.format_assortment" class="form-control" :class="{ 'is-invalid': !formData.format_assortment && touched }" placeholder="" />
          </div>

          <div class="col-md-6 mb-3">
            <label class="form-label fw-bold">Marketing Type <span class="text-danger">*</span></label>
            <input v-model="formData.marketing_type" class="form-control" :class="{ 'is-invalid': !formData.format_assortment && touched }" placeholder="" />
          </div>
        </div>
        
        <div class="row">
          <div class="col-md-6 mb-3">
            <label class="form-label fw-bold">Baseline (optional)</label>
            <input v-model.number="formData.baseline" type="number" step="0.01" class="form-control" placeholder="" />
          </div>
        </div>
      </div>
      
      <div class="d-flex justify-content-end gap-2 mt-3 pt-3 border-top">
        <button class="btn btn-secondary" @click="$emit('close')">Cancel</button>
        <button class="btn btn-primary" @click="save" :disabled="!isValid">
          {{ isEdit ? 'Update' : 'Add' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'

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

const props = defineProps<{
  row?: ManualRow | null
  index?: number | null
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'save', row: ManualRow): void
}>()

const touched = ref(false)
const isEdit = computed(() => props.index !== null && props.row !== null)

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
  }
}, { immediate: true })

const isValid = computed(() => {
  return !!(formData.value.promo_id && 
    formData.value.sku && 
    formData.value.store_id && 
    formData.value.regular_price && 
    formData.value.promo_price)
})

function save() {
  touched.value = true
  if (!isValid.value) return
  // Базовые поля из формы (без дефолтов)
  const rowToSave = {
    ...formData.value,
    // Переопределяем только те поля, где нужны дефолты если 0 или пусто
    format_assortment: formData.value.format_assortment || 'na',
    adv_carrier: formData.value.adv_carrier || 'ЖЦ',
    adv_material: formData.value.adv_material || 'na',
    promo_mechanics: formData.value.promo_mechanics || 'na',
    marketing_type: formData.value.marketing_type || 'Скидка по карте!',
  }
  emit('save', rowToSave)
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
</style>