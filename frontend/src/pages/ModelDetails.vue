<!-- frontend\src\pages\ModelDetails.vue -->


<script setup lang="ts">
import { onMounted, ref } from "vue"
import { useRoute } from "vue-router"
import {
    fetchModelDetails,
    fetchModelMetrics,
    promoteModel,
    deactivateModel,
} from "@/services/api"
import type { Model } from "@/types"

const route = useRoute()

const model = ref<Model | null>(null)
const metrics = ref<Record<string, any> | null>(null)

onMounted(async () => {
    const id = Number(route.params.id)
    model.value = await fetchModelDetails(id)
    metrics.value = await fetchModelMetrics(id)
})

async function promote() {
    if (!model.value) return
    await promoteModel(Number(route.params.id))
    model.value.is_active = true
}

async function deactivate() {
    if (!model.value) return
    await deactivateModel(Number(route.params.id))
    model.value.is_active = false
}
</script>

<template>
    <div v-if="model">
        <h2>Model Details</h2>

        <p><b>Name:</b> {{ model.name }}</p>
        <p><b>Version:</b> {{ model.version }}</p>
        <p><b>Dataset:</b> {{ model.dataset_version_id }}</p>
        <p><b>Rows:</b> {{ model.trained_rows_count }}</p>
        <p><b>Status:</b> {{ model.is_active ? "Active" : "Inactive" }}</p>

        <button @click="promote">Promote</button>
        <button @click="deactivate">Deactivate</button>

        <h3>Metrics</h3>
        <pre>{{ metrics }}</pre>
    </div>
</template>
