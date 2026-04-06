<!-- frontend/src/components/ActivationHistoryModal.vue -->

<template>
  <div v-if="show" class="modal-backdrop" @click.self="$emit('close')">
    <div class="modal-box" style="width: 600px;">
      <h5>Model Activation History</h5>

      <table class="table table-sm">
        <thead>
          <tr><th>Time</th><th>Model ID</th><th>Activated By</th></tr>
        </thead>
        <tbody>
          <tr v-for="entry in history" :key="entry.id">
            <td>{{ formatDate(entry.activated_at) }}</td>
            <td>{{ entry.model_id }}</td>
            <td>{{ entry.activated_by }}</td>
          </tr>
          <tr v-if="history.length === 0">
            <td colspan="3" class="text-center">No history yet</td>
          </tr>
        </tbody>
      </table>

      <div class="d-flex justify-content-end mt-3">
        <button class="btn btn-secondary" @click="$emit('close')">Close</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { getActivationHistory } from '../services/api'

interface HistoryEntry {
  id: number
  model_id: number
  activated_at: string
  activated_by: string
}

const props = defineProps<{ show: boolean }>()
const emit = defineEmits(['close'])

const history = ref<HistoryEntry[]>([])

function formatDate(dateStr: string) {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('ru-RU')
}

async function loadHistory() {
  const response = await getActivationHistory()
  history.value = response.data
}

watch(() => props.show, async (newVal) => {
  if (newVal) {
    await loadHistory()
  }
})
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
}
</style>