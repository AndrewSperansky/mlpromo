<!-- frontend\src\pages\Datasets.vue -->

<script setup lang="ts">
import { onMounted, ref } from "vue"
import { useRouter } from "vue-router"
import { fetchDatasets } from "@/services/api"
import type { Dataset } from "@/types"

const datasets = ref<Dataset[]>([])
const router = useRouter()

onMounted(async () => {
    datasets.value = await fetchDatasets()
})

function openDataset(id: string) {
    router.push(`/datasets/${id}`)
}
</script>

<template>
    <div>
        <h2>Datasets</h2>
        <table>
            <thead>
                <tr>
                    <th>Version</th>
                    <th>Created</th>
                    <th>Rows</th>
                </tr>
            </thead>
            <tbody>
                <tr v-for="d in datasets" :key="d.id" @click="openDataset(d.id)">
                    <td>{{ d.id }}</td>
                    <td>{{ d.created_at }}</td>
                    <td>{{ d.rows_count }}</td>
                </tr>
            </tbody>
        </table>
    </div>
</template>