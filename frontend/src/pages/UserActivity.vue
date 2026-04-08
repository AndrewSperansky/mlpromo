<!-- frontend/src/pages/UserActivity.vue -->
<template>
  <div>
    <h2 class="mb-4">User Activity Log</h2>
    
    <!-- Filters -->
    <div class="card mb-4">
      <div class="card-body">
        <div class="row g-3">
          <div class="col-md-3">
            <label class="form-label">User</label>
            <select v-model="filters.userId" class="form-select" @change="loadActivities">
              <option :value="null">All Users</option>
              <option v-for="user in users" :key="user.id" :value="user.id">
                {{ user.username }} ({{ user.role }})
              </option>
            </select>
          </div>
          <div class="col-md-3">
            <label class="form-label">Action</label>
            <select v-model="filters.action" class="form-select" @change="loadActivities">
              <option :value="null">All Actions</option>
              <option value="login">Login</option>
              <option value="logout">Logout</option>
              <option value="predict">Predict</option>
              <option value="train">Train Model</option>
              <option value="activate">Activate Model</option>
              <option value="upload">Upload Dataset</option>
            </select>
          </div>
          <div class="col-md-3">
            <label class="form-label">Date From</label>
            <input type="date" v-model="filters.dateFrom" class="form-control" @change="loadActivities">
          </div>
          <div class="col-md-3">
            <label class="form-label">Date To</label>
            <input type="date" v-model="filters.dateTo" class="form-control" @change="loadActivities">
          </div>
        </div>
        <div class="row mt-3">
          <div class="col-md-12">
            <button class="btn btn-primary me-2" @click="loadActivities">
              <i class="bi bi-search me-1"></i> Apply Filters
            </button>
            <button class="btn btn-secondary" @click="resetFilters">
              <i class="bi bi-arrow-repeat me-1"></i> Reset
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Statistics -->
    <div class="row g-3 mb-4">
      <div class="col-md-3">
        <div class="card bg-primary text-white">
          <div class="card-body">
            <h6 class="card-title">Total Activities</h6>
            <h2 class="mb-0">{{ activities.length }}</h2>
          </div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="card bg-success text-white">
          <div class="card-body">
            <h6 class="card-title">Predictions</h6>
            <h2 class="mb-0">{{ getActionCount('predict') }}</h2>
          </div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="card bg-warning text-dark">
          <div class="card-body">
            <h6 class="card-title">Trainings</h6>
            <h2 class="mb-0">{{ getActionCount('train') }}</h2>
          </div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="card bg-info text-white">
          <div class="card-body">
            <h6 class="card-title">Logins</h6>
            <h2 class="mb-0">{{ getActionCount('login') }}</h2>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Activities Table -->
    <div class="card shadow-sm">
      <div class="card-header bg-secondary text-white d-flex justify-content-between align-items-center">
        <span><i class="bi bi-clock-history me-2"></i>Activity Log</span>
        <button class="btn btn-sm btn-light" @click="loadActivities" :disabled="loading">
          <i class="bi bi-arrow-repeat"></i> Refresh
        </button>
      </div>
      <div class="card-body p-0">
        <div v-if="loading" class="text-center py-4">
          <div class="spinner-border text-primary"></div>
        </div>
        <div v-else-if="activities.length === 0" class="text-center py-4 text-muted">
          No activities found
        </div>
        <div v-else class="table-responsive">
          <table class="table table-striped table-hover mb-0">
            <thead class="table-dark">
              <tr>
                <th>Time</th>
                <th>User</th>
                <th>Action</th>
                <th>Resource</th>
                <th>Details</th>
                <th>IP Address</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="activity in activities" :key="activity.id">
                <td class="small">{{ formatDateTime(activity.created_at) }}</td>
                <td>
                  <span :class="getRoleBadgeClass(activity.user_role)">
                    {{ activity.username }}
                  </span>
                </td>
                <td>
                  <span :class="getActionBadgeClass(activity.action)">
                    {{ activity.action }}
                  </span>
                </td>
                <td class="small">{{ activity.resource || '-' }}</td>
                <td class="small">{{ activity.details || '-' }}</td>
                <td class="small">{{ activity.ip_address || '-' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '../services/api'

interface Activity {
  id: number
  user_id: number
  username: string
  user_role: string
  action: string
  resource: string | null
  details: string | null
  ip_address: string | null
  created_at: string
}

interface User {
  id: number
  username: string
  role: string
}

const activities = ref<Activity[]>([])
const users = ref<User[]>([])
const loading = ref(false)

const filters = ref({
  userId: null as number | null,
  action: null as string | null,
  dateFrom: '',
  dateTo: ''
})

function getActionBadgeClass(action: string): string {
  switch (action) {
    case 'login': return 'badge bg-success'
    case 'logout': return 'badge bg-secondary'
    case 'predict': return 'badge bg-primary'
    case 'train': return 'badge bg-warning'
    case 'activate': return 'badge bg-danger'
    case 'upload': return 'badge bg-info'
    default: return 'badge bg-secondary'
  }
}

function getRoleBadgeClass(role: string): string {
  switch (role) {
    case 'admin': return 'badge bg-danger'
    case 'ml_engineer': return 'badge bg-primary'
    case 'analyst': return 'badge bg-info'
    default: return 'badge bg-secondary'
  }
}

function formatDateTime(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleString('ru-RU')
}

function getActionCount(action: string): number {
  return activities.value.filter(a => a.action === action).length
}

async function loadUsers() {
  try {
    const response = await api.get('/auth/users')
    users.value = response.data
  } catch (error) {
    console.error('Failed to load users:', error)
  }
}

async function loadActivities() {
  loading.value = true
  try {
    const params: any = {}
    if (filters.value.userId) params.user_id = filters.value.userId
    if (filters.value.action) params.action = filters.value.action
    if (filters.value.dateFrom) params.date_from = filters.value.dateFrom
    if (filters.value.dateTo) params.date_to = filters.value.dateTo
    
    const response = await api.get('/auth/activities', { params })
    activities.value = response.data
  } catch (error) {
    console.error('Failed to load activities:', error)
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  filters.value = {
    userId: null,
    action: null,
    dateFrom: '',
    dateTo: ''
  }
  loadActivities()
}

onMounted(() => {
  loadUsers()
  loadActivities()
})
</script>

<style scoped>
.badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}

.table-responsive {
  overflow-x: auto;
}
</style>