<!-- frontend/src/components/NewDataAlert.vue -->

<template>
  <NotificationBanner
    v-if="visible"
    type="warning"
    title="📊 New Data Available"
    :message="message"
    :details="`${newRowsCount} new rows detected since last training`"
    @close="handleClose"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import NotificationBanner from './NotificationBanner.vue'

const props = defineProps<{
  newRowsCount: number
  message: string
}>()

const emit = defineEmits(['close'])

const visible = ref(true)

function handleClose() {
  visible.value = false
  emit('close')
}
</script>