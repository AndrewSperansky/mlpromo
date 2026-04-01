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
      <div class="card-header d-flex justify-content-between align-items-center">
        <h5 class="mb-0">Upload History</h5>
        <button class="btn btn-sm btn-outline-secondary" @click="loadStats" :disabled="loading">
          <i class="bi bi-arrow-repeat"></i> Refresh
        </button>
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
              <th>Actions</th>
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
              <td>
                <button 
                  class="btn btn-sm btn-outline-danger" 
                  @click="confirmDeleteBatch(upload.batch_id)"
                  :disabled="deleting"
                >
                  <i class="bi bi-trash3"></i> Delete
                </button>
              </td>
            </tr>
            <tr v-if="!stats.upload_history?.length">
              <td colspan="7" class="text-center text-muted p-4">
                No uploads yet
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Модальное окно подтверждения удаления -->
    <div v-if="showDeleteModal" class="modal-backdrop" @click.self="showDeleteModal = false">
      <div class="modal-box">
        <h5 class="text-danger">⚠️ Confirm Deletion</h5>
        <p>Are you sure you want to delete this batch?</p>
        <p class="text-muted small">Batch ID: <code>{{ batchToDelete }}</code></p>
        <p class="text-warning small">⚠️ This will delete {{ deleteBatchRecords }} records and cannot be undone!</p>
        
        <div class="mt-3 d-flex justify-content-end gap-2">
          <button class="btn btn-secondary" @click="showDeleteModal = false">
            Cancel
          </button>
          <button class="btn btn-danger" @click="deleteBatch" :disabled="deleting">
            <span v-if="deleting" class="spinner-border spinner-border-sm me-2"></span>
            Delete Permanently
          </button>
        </div>
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
const loading = ref(false)
const deleting = ref(false)
const error = ref("")

// Модальное окно удаления
const showDeleteModal = ref(false)
const batchToDelete = ref<string | null>(null)
const deleteBatchRecords = ref(0)

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
  loading.value = true
  try {
    const response = await api.get('/ml/dataset/stats')
    stats.value = response.data
  } catch (e) {
    console.error('Failed to load stats:', e)
    error.value = "Failed to load dataset statistics"
  } finally {
    loading.value = false
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

function confirmDeleteBatch(batchId: string) {
  // Находим запись, чтобы показать количество записей
  const upload = stats.value.upload_history.find(u => u.batch_id === batchId)
  if (upload) {
    deleteBatchRecords.value = upload.records_added
  }
  batchToDelete.value = batchId
  showDeleteModal.value = true
}

async function deleteBatch() {
  if (!batchToDelete.value) return
  
  deleting.value = true
  
  try {
    const response = await api.delete(`/ml/dataset/batch/${batchToDelete.value}`)
    console.log('Delete response:', response.data)
    
    // Обновляем статистику после удаления
    await loadStats()
    
    showDeleteModal.value = false
    batchToDelete.value = null
    
  } catch (e: any) {
    console.error('Delete error:', e)
    const detail = e.response?.data?.detail
    if (typeof detail === 'object') {
      error.value = detail.message || "Failed to delete batch"
    } else {
      error.value = detail || "Failed to delete batch"
    }
  } finally {
    deleting.value = false
  }
}

onMounted(() => {
  loadStats()
})
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
  width: 450px;
  max-width: 90%;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

.modal-box code {
  background: #f5f5f5;
  padding: 2px 6px;
  border-radius: 4px;
}

.text-danger {
  color: #dc3545 !important;
}

.text-warning {
  color: #ffc107 !important;
}

.bg-success {
  background-color: #198754 !important;
}

.bg-danger {
  background-color: #dc3545 !important;
}
</style>