<!-- frontend/src/components/ErrorModal.vue -->

<template>
  <div v-if="show" class="modal-backdrop" @click.self="$emit('close')">
    <div class="modal-box">
      <div class="text-center">
        <div class="text-danger mb-3">
          <i class="bi bi-x-circle-fill fs-1"></i>
        </div>
        <h5 class="text-danger">Activation Failed</h5>
        <p class="mt-3">{{ message }}</p>
        <div class="mt-3">
          <button class="btn btn-primary" @click="$emit('close')">OK</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  show: boolean
  message: string
}>()

defineEmits(['close'])
</script>