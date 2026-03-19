<template>
    <iframe
        :src="grafanaUrl"
        width="100%"
        height="900px"
        style="border:none;"
    >
    </iframe>
</template>

<script setup lang="ts">
const grafanaUrl = import.meta.env.VITE_GRAFANA_URL || 'http://localhost:3000'
</script>