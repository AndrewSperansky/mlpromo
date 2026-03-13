<!-- frontend\src\pages\Datasets.vue -->

<template>
  <div class="container-fluid mt-4">
    <h2 class="mb-4">Datasets</h2>

    <div class="card mb-4">
      <div class="card-body">
        <div class="d-flex gap-2">
          <div class="flex-grow-1">
            <input type="file" class="form-control" accept=".csv" @change="handleFileSelect" />
          </div>

          <div class="flex-shrink-0">
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

    <!-- Таблица датасетов -->
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
                <a href="#" @click.prevent="openDatasetDetails(ds.dataset_version_id)" class="dataset-link">
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

  <!-- ===== МОДАЛЬНОЕ ОКНО ДЛЯ ПРОСМОТРА МОДЕЛЕЙ ===== -->
  <div v-if="showModal" class="modal fade show d-block" tabindex="-1">
    <div class="modal-dialog modal-lg">
      <div class="modal-content">

        <div class="modal-header">
          <h5 class="modal-title">
            Models trained on dataset
            <span class="dataset-id">{{ selectedDataset }}</span>
          </h5>

          <button type="button" class="btn-close" @click="showModal = false"></button>
        </div>

        <div class="modal-body">

          <table class="table table-striped">
            <thead>
              <tr>
                <th>Name</th>
                <th>Version</th>
                <th>Rows</th>
                <th>Active</th>
              </tr>
            </thead>

            <tbody>

              <tr v-for="m in datasetModels" :key="m.id">
                <td>{{ m.name }}</td>
                <td>{{ m.version }}</td>
                <td>{{ m.trained_rows_count }}</td>
                <td>{{ m.is_active ? "Yes" : "No" }}</td>
              </tr>

              <tr v-if="datasetModels.length === 0">
                <td colspan="4" class="text-center text-muted">
                  No models trained on this dataset
                </td>
              </tr>

            </tbody>
          </table>

        </div>

      </div>
    </div>
  </div>

  <div v-if="showModal" class="modal-backdrop fade show"></div>

  <!-- ===== МОДАЛЬНОЕ ОКНО ПОДТВЕРЖДЕНИЯ УДАЛЕНИЯ ===== -->
  <div v-if="showDeleteConfirm" class="modal fade show d-block" tabindex="-1">
    <div class="modal-dialog">
      <div class="modal-content">

        <div class="modal-header bg-danger text-white">
          <h5 class="modal-title">
            <i class="bi bi-exclamation-triangle me-2"></i>
            Confirm Deletion
          </h5>
          <button type="button" class="btn-close btn-close-white" @click="showDeleteConfirm = false"></button>
        </div>

        <div class="modal-body">
          <p class="fs-5">{{ deleteConfirmMessage }}</p>
          <p class="text-muted small mb-0">Это действие нельзя отменить. Все связанные модели будут помечены как
            удалённые.</p>
        </div>

        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="showDeleteConfirm = false">
            Cancel
          </button>
          <button type="button" class="btn btn-danger" @click="confirmForceDelete">
            <i class="bi bi-trash3 me-2"></i>
            Delete with models
          </button>
        </div>

      </div>
    </div>
  </div>

  <div v-if="showDeleteConfirm" class="modal-backdrop fade show"></div>

</template>

<script setup lang="ts">
import { ref, onMounted } from "vue"
import { fetchDatasetModels } from "../services/api"
import api, { fetchDatasets, deleteDataset } from "../services/api"

// ===== Types =====
interface Dataset {
  dataset_version_id: string
  created_at: string
  row_count: number
}

// ===== State =====
const selectedDataset = ref<string | null>(null)
const datasetModels = ref<any[]>([])
const showModal = ref(false)

const datasets = ref<Dataset[]>([])
const selectedFile = ref<File | null>(null)
const uploading = ref(false)
const error = ref("")

// ===== Delete confirmation modal =====
const showDeleteConfirm = ref(false)
const deleteConfirmMessage = ref('')
const pendingDeleteId = ref<string | null>(null)

// ===== Methods =====
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

async function handleDelete(datasetId: string) {
  try {
    console.log('🔍 Trying to delete without force:', datasetId);
    await deleteDataset(datasetId, false);
    await loadDatasets();
  } catch (error: any) {
    console.log('🔍 Error caught:', error);

    if (error.response?.status === 409) {
      console.log('🔍 409 Conflict detected');

      const detail = error.response?.data?.detail;
      console.log('🔍 detail:', detail);

      const modelsCount = detail?.total_models || 'несколько';
      console.log('🔍 modelsCount:', modelsCount);

      // Показываем кастомное модальное окно вместо confirm
      pendingDeleteId.value = datasetId;
      deleteConfirmMessage.value =
        `Этот датасет используется ${modelsCount} моделью(ями).`;
      showDeleteConfirm.value = true;

    } else {
      console.error('❌ Delete error:', error);
      alert('Ошибка при удалении датасета');
    }
  }
}

async function confirmForceDelete() {
  if (!pendingDeleteId.value) return;

  try {
    await deleteDataset(pendingDeleteId.value, true);
    await loadDatasets();
    showDeleteConfirm.value = false;
    pendingDeleteId.value = null;
  } catch (forceError) {
    console.error('Force delete failed:', forceError);
    alert('Не удалось удалить датасет даже с force=true');
  }
}

async function openDatasetDetails(id: string) {
  selectedDataset.value = id
  showModal.value = true

  try {
    const res = await fetchDatasetModels(id)
    datasetModels.value = res.data
  } catch (e) {
    console.error("Failed to load models", e)
  }
}

onMounted(loadDatasets)
</script>

<style scoped>
.dataset-link {
  text-decoration: none;
  font-weight: 500;
  color: #0d6efd;
  cursor: pointer;
}

.dataset-link:hover {
  text-decoration: underline;
}

.dataset-id {
  color: #198754;
  font-weight: 600;
}

/* Стили для модальных окон */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 1040;
}

.modal.show {
  display: block;
  z-index: 1050;
}

.modal-dialog {
  z-index: 1060;
}

.bg-danger {
  background-color: #dc3545 !important;
}

.btn-close-white {
  filter: invert(1) grayscale(100%) brightness(200%);
}
</style>