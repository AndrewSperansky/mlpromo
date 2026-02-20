<template>
  <div class="col-md-3">
    <div class="card p-3 shadow-sm">
      <h6 class="text-muted">{{ title }}</h6>

      <div v-if="badge" class="mt-2">
        <span :class="'badge bg-' + badge">
          {{ value }}
        </span>
      </div>

      <div v-else class="fs-5 fw-bold mt-2">
        {{ value ?? '—' }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  value?: string | number
  badge?: string
}>()
</script>