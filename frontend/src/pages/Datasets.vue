<!-- frontend\src\pages\Datasets.vue -->

<template>
    <div class="datasets-page">
        <h1>Datasets</h1>

        <!-- Upload block -->
        <div class="upload-card">
            <input type="file" accept=".csv" @change="handleFileSelect" ref="fileInput" />

            <button :disabled="uploading || !selectedFile" @click="uploadDataset">
                {{ uploading ? "Uploading..." : "Upload Dataset" }}
            </button>

            <span v-if="error" class="error">{{ error }}</span>
        </div>

        <!-- Table -->
        <table v-if="datasets.length">
            <thead>
                <tr>
                    <th>Version</th>
                    <th>Created</th>
                    <th>Rows</th>
                </tr>
            </thead>
            <tbody>
                <tr v-for="ds in datasets" :key="ds.dataset_version_id">
                    <td>{{ ds.dataset_version_id }}</td>
                    <td>{{ formatDate(ds.created_at) }}</td>
                    <td>{{ ds.rows_count }}</td>
                </tr>
            </tbody>
        </table>

        <p v-else class="empty">No datasets uploaded yet</p>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue"
import axios from "axios"

interface Dataset {
    dataset_version_id: string
    created_at: string
    rows_count: number
}

const datasets = ref<Dataset[]>([])
const uploading = ref(false)
const error = ref<string | null>(null)
const selectedFile = ref<File | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)

const API_BASE = "http://localhost:8000/api/v1/ml"

async function loadDatasets() {
    try {
        const res = await axios.get(`${API_BASE}/datasets`)
        datasets.value = res.data
    } catch (err: any) {
        error.value = "Failed to load datasets"
    }
}

function handleFileSelect(event: Event) {
    const target = event.target as HTMLInputElement
    const file = target.files?.[0]

    if (!file) return

    selectedFile.value = file
    error.value = null
}

async function uploadDataset() {
    if (!selectedFile.value) return

    const formData = new FormData()
    formData.append("file", selectedFile.value)

    try {
        uploading.value = true
        error.value = null

        await axios.post(`${API_BASE}/dataset/upload`, formData, {
            headers: { "Content-Type": "multipart/form-data" },
        })

        await loadDatasets()

        selectedFile.value = null
        if (fileInput.value) fileInput.value.value = ""

    } catch (err: any) {
        error.value =
            err.response?.data?.detail || "Dataset upload failed"
    } finally {
        uploading.value = false
    }
}

function formatDate(date: string) {
    return new Date(date).toLocaleString()
}

onMounted(loadDatasets)
</script>

<style scoped>
.datasets-page {
    padding: 20px;
}

.upload-card {
    margin-bottom: 20px;
    display: flex;
    gap: 10px;
    align-items: center;
}

button {
    padding: 6px 12px;
    cursor: pointer;
}

button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
}

.error {
    color: red;
}

.empty {
    opacity: 0.6;
}
</style>