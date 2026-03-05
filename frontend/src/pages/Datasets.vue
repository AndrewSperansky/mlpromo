<!-- frontend\src\pages\Datasets.vue -->

<template>
  <div class="container-fluid mt-4">
    <h2 class="mb-4">Datasets</h2>

    <div class="card mb-4">
      <div class="card-body">
        <div class="row g-2 align-items-center">

          <div class="col-auto">
            <input type="file" class="form-control" accept=".csv" @change="handleFileSelect" />
          </div>

          <div class="col-auto">
            <button class="btn btn-primary" @click="uploadDataset" :disabled="!selectedFile || uploading">
              <span v-if="uploading" class="spinner-border spinner-border-sm"></span>
              Upload Dataset
            </button>
          </div>

        </div>
      </div>
    </div>

    <div v-if="error" class="alert alert-danger">
      {{ error }}
    </div>

    <div class="card">
      <div class="card-body p-0">

        <table class="table table-striped table-hover table-bordered mb-0">
          <thead class="table-dark">
            <tr>
              <th style="width:40%">Dataset Version</th>
              <th style="width:25%">Created</th>
              <th style="width:15%">Rows</th>
              <th style="width:20%">Actions</th>
            </tr>
          </thead>

          <tbody>

            <tr v-for="ds in datasets" :key="ds.dataset_version_id">
              <td>
                <a href="#" @click.prevent="openDataset(ds.dataset_version_id)" class="dataset-link">
                  {{ ds.dataset_version_id }}
                </a>
              </td>
              <td>{{ formatDate(ds.created_at) }}</td>
              <td>{{ ds.row_count }}</td>

              <td>
                <button class="btn btn-danger btn-sm" @click="handleDelete(ds.dataset_version_id)">
                  Delete
                </button>
              </td>

            </tr>

            <tr v-if="datasets.length === 0">
              <td colspan="4" class="text-center text-muted p-4">
                No datasets uploaded yet
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
import { useRouter } from "vue-router"
import api, { fetchDatasets, deleteDataset } from "../services/api"

interface Dataset {
  dataset_version_id: string
  created_at: string
  row_count: number
}

const router = useRouter()
const datasets = ref<Dataset[]>([])
const selectedFile = ref<File | null>(null)
const uploading = ref(false)
const error = ref("")


function openDataset(id: string) {
  router.push(`/datasets/${id}`)
}

function formatDate(date: string) {
  return new Date(date).toLocaleString()
}

function handleFileSelect(event: Event) {
  const input = event.target as HTMLInputElement
  if (!input.files || input.files.length === 0) {
    selectedFile.value = null
    return
  }
  selectedFile.value = input.files.item(0)
}

async function loadDatasets() {
  try {
    console.log('Loading datasets...')
    const res = await fetchDatasets()
    console.log('Fetch datasets response:', res)

    // Проверяем структуру ответа
    const data = res.data || res
    console.log('Datasets data:', data)

    if (!Array.isArray(data)) {
      console.error('Data is not an array:', data)
      datasets.value = []
      return
    }

    datasets.value = data.map((ds: any) => ({
      dataset_version_id: ds.dataset_version_id || ds.id,
      created_at: ds.created_at,
      row_count: ds.row_count
    }))

    console.log('Processed datasets:', datasets.value)
  } catch (e) {
    console.error('Load datasets error:', e)
    error.value = "Failed to load datasets"
  }
}

async function uploadDataset() {
  if (!selectedFile.value) return
  uploading.value = true
  error.value = ""

  const formData = new FormData()
  formData.append("file", selectedFile.value)

  try {
    console.log('Uploading file:', selectedFile.value.name)
    await api.post("/ml/dataset/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" }
    })
    selectedFile.value = null
    await loadDatasets()
  } catch (e) {
    console.error('Upload error:', e)
    error.value = "Dataset upload failed"
  } finally {
    uploading.value = false
  }
}

async function handleDelete(id: string) {
  console.log('🗑️ handleDelete called with id:', id, 'type:', typeof id)

  if (!id) {
    console.error('❌ handleDelete: id is undefined or empty')
    error.value = "Cannot delete: invalid dataset ID"
    return
  }

  if (!confirm("Delete this dataset?")) return

  try {
    console.log('Calling deleteDataset with id:', id)
    const result = await deleteDataset(id)
    console.log('Delete result:', result)
    await loadDatasets()
  } catch (e: any) {
    console.error('❌ Delete error:', e)
    console.error('Error response:', e.response?.data)
    error.value = e.response?.data?.detail || "Delete failed"
  }
}

onMounted(loadDatasets)
</script>


<style>
.dataset-link {
  text-decoration: none;
  font-weight: 500;
  color: #0d6efd;
  cursor: pointer;
}

.dataset-link:hover {
  text-decoration: underline;
}
</style>