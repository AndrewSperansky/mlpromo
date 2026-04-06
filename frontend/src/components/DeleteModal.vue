<!-- frontend/src/components/DeleteModal.vue -->

<template>
  <div v-if="show" class="modal-backdrop" @click.self="$emit('close')">
    <div class="modal-box">
      <h5 class="text-danger">Confirm Deletion</h5>
      <p>Are you sure you want to delete model:</p>
      <strong>ID: {{ modelId }}</strong>
      <p class="text-warning mt-2">⚠️ This action cannot be undone!</p>

      <div class="mt-3 d-flex justify-content-end gap-2">
        <button class="btn btn-secondary" @click="$emit('close')">Cancel</button>
        <button class="btn btn-danger" @click="$emit('confirm')">Delete Permanently</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  show: boolean
  modelId: number | null
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