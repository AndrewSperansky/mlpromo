<!-- frontend/src/components/TrainModal.vue -->

<template>
  <div v-if="show" class="modal-backdrop" @click.self="$emit('close')">
    <div class="modal-box">
      <h5>Confirm Training</h5>
      <p>Train model on the entire dataset?</p>
      <p class="text-muted small">Model will be trained on all available data</p>


      <div class="mt-3">
        <div class="form-check">
          <input class="form-check-input" type="checkbox" v-model="force" id="forceCheck">
          <label class="form-check-label" for="forceCheck">
            Force training (ignore metrics check)
          </label>
        </div>
      </div>

      <div class="mt-3 d-flex justify-content-end gap-2">
        <button class="btn btn-secondary" @click="$emit('close')">Cancel</button>
        <button class="btn btn-primary" :disabled="training" @click="$emit('confirm')">
          {{ training ? 'Training...' : 'Confirm' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const force = ref(false)
defineExpose({ force })

defineProps<{
  show: boolean
  training: boolean
}>()

defineEmits(['close', 'confirm'])
</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1050;
}

.modal-box {
  background: white;
  padding: 24px;
  border-radius: 8px;
  width: 400px;
}
</style>