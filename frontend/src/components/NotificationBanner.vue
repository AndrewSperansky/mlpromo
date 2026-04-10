<!-- frontend/src/components/NotificationBanner.vue -->

<template>
  <div v-if="visible" class="alert" :class="alertClass" role="alert">
    <div class="d-flex justify-content-between align-items-start">
      <div class="flex-grow-1">
        <div v-if="title" class="fw-bold mb-1">{{ title }}</div>
        <div>{{ message }}</div>
        <div v-if="details" class="small mt-1 text-muted">{{ details }}</div>
      </div>
      <button type="button" class="btn-close" @click="close" aria-label="Close"></button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps<{
  type: 'success' | 'danger' | 'warning' | 'info'
  title?: string
  message: string
  details?: string
  autoClose?: number  // milliseconds
}>()

const emit = defineEmits(['close'])

const visible = ref(true)

const alertClass = computed(() => {
  switch (props.type) {
    case 'success': return 'alert-success'
    case 'danger': return 'alert-danger'
    case 'warning': return 'alert-warning'
    default: return 'alert-info'
  }
})

function close() {
  visible.value = false
  emit('close')
}

// Автоматическое закрытие
if (props.autoClose) {
  setTimeout(() => {
    if (visible.value) close()
  }, props.autoClose)
}
</script>