<!-- frontend/src/pages/Datasets.vue -->

<template>
  <div class="container-fluid mt-4">
    <h2 class="mb-4">Dataset Management</h2>

    <!-- Статистика датасета -->
    <div class="row mb-4">
      <div class="col-md-4">
        <div class="card bg-primary text-white h-100">
          <div class="card-body d-flex flex-column">
            <h5 class="card-title">Total Rows</h5>
            <h2 class="display-4 mt-auto mb-0">{{ stats.total_rows || 0 }}</h2>
          </div>
        </div>
      </div>
      <div class="col-md-4">
        <div class="card bg-success text-white h-100">
          <div class="card-body d-flex flex-column">
            <h5 class="card-title">Last Upload</h5>
            <h6 class="mt-auto mb-1">{{ formatDate(stats.last_updated) || '—' }}</h6>
            <small class="mt-0">{{ stats.last_upload_records || 0 }} rows added</small>
          </div>
        </div>
      </div>
      <div class="col-md-4">
        <div class="card bg-info text-white h-100">
          <div class="card-body d-flex flex-column">
            <h5 class="card-title">Total Uploads</h5>
            <h2 class="display-4 mt-auto mb-0">{{ stats.total_uploads || 0 }}</h2>
          </div>
        </div>
      </div>
    </div>

    <!-- Загрузка нового файла -->
    <div class="card mb-4">
      <div class="card-body">
        <div class="d-flex gap-2">
          <div class="flex-grow-1">
            <input type="file" class="form-control" accept=".csv" @change="handleFileSelect" />
          </div>
          <div class="flex-shrink-0">
            <button class="btn btn-primary" @click="uploadDataset" :disabled="!selectedFile || uploading">
              <span v-if="uploading" class="spinner-border spinner-border-sm"></span>
              Upload & Append
            </button>
          </div>
        </div>
        <small class="text-muted mt-2 d-block">
          New data will be appended to the existing dataset. After upload, retrain the model.
        </small>
      </div>
    </div>

    <div v-if="error" class="alert alert-danger">
      {{ error }}
    </div>

    <!-- История загрузок -->
    <div class="card">
      <div class="card-header">
        <h5 class="mb-0">Upload History</h5>
      </div>
      <div class="card-body p-0">
        <table class="table table-striped table-hover mb-0">
          <thead class="table-dark">
            <tr>
              <th>Batch ID</th>
              <th>Uploaded At</th>
              <th>Records Added</th>
              <th>Total After</th>
              <th>Duration (ms)</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="upload in stats.upload_history" :key="upload.id">
              <td><code>{{ upload.batch_id.slice(0, 8) }}...</code></td>
              <td>{{ formatDate(upload.uploaded_at) }}</td>
              <td class="text-success fw-bold">{{ upload.records_added }}</td>
              <td>{{ upload.total_records_after }}</td>
              <td>{{ upload.duration_ms }}</td>
              <td>
                <span :class="upload.status === 'success' ? 'badge bg-success' : 'badge bg-danger'">
                  {{ upload.status }}
                </span>
              </td>
            </tr>
            <tr v-if="!stats.upload_history?.length">
              <td colspan="6" class="text-center text-muted p-4">
                No uploads yet
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue"
import api from "../services/api"

interface UploadHistory {
  id: number
  batch_id: string
  uploaded_at: string
  records_added: number
  total_records_after: number
  status: string
  error_message: string | null
  duration_ms: number
}

interface DatasetStats {
  total_rows: number
  last_updated: string | null
  last_upload_records: number
  total_uploads: number
  upload_history: UploadHistory[]
}

const stats = ref<DatasetStats>({
  total_rows: 0,
  last_updated: null,
  last_upload_records: 0,
  total_uploads: 0,
  upload_history: []
})
const selectedFile = ref<File | null>(null)
const uploading = ref(false)
const error = ref("")

function formatDate(dateStr: string | null) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString()
}

function handleFileSelect(event: Event) {
  const input = event.target as HTMLInputElement
  if (!input.files || input.files.length === 0) {
    selectedFile.value = null
    return
  }
  selectedFile.value = input.files.item(0)
}

async function loadStats() {
  try {
    const response = await api.get('/ml/dataset/stats')
    stats.value = response.data
  } catch (e) {
    console.error('Failed to load stats:', e)
    error.value = "Failed to load dataset statistics"
  }
}

async function uploadDataset() {
  if (!selectedFile.value) return
  uploading.value = true
  error.value = ""

  const formData = new FormData()
  formData.append("file", selectedFile.value)

  try {
    const response = await api.post("/ml/dataset/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" }
    })
    
    console.log('Upload response:', response.data)
    await loadStats()
    selectedFile.value = null
    
    // Сбрасываем input
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    if (input) input.value = ''
    
  } catch (e: any) {
    console.error('Upload error:', e)
    error.value = e.response?.data?.detail || "Dataset upload failed"
  } finally {
    uploading.value = false
  }
}

onMounted(() => {
  loadStats()
})
</script>