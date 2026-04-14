<!-- frontend/src/pages/Lineage.vue -->

<template>
  <div>
    <h2 class="mb-4">Model Lineage</h2>
    
    <!-- Статистика -->
    <div class="row g-3 mb-4">
      <div class="col-md-4">
        <div class="card bg-primary text-white">
          <div class="card-body">
            <h6 class="card-title">Total Events</h6>
            <h2 class="mb-0">{{ events.length }}</h2>
          </div>
        </div>
      </div>
      <div class="col-md-4">
        <div class="card bg-success text-white">
          <div class="card-body">
            <h6 class="card-title">Promoted</h6>
            <h2 class="mb-0">{{ getEventCount('promoted') }}</h2>
          </div>
        </div>
      </div>
      <div class="col-md-4">
        <div class="card bg-info text-white">
          <div class="card-body">
            <h6 class="card-title">Trained</h6>
            <h2 class="mb-0">{{ getEventCount('trained') }}</h2>
          </div>
        </div>
      </div>
    </div>

    <!-- Таблица -->
    <div class="card shadow-sm">
      <div class="card-header bg-secondary text-white">
        <i class="bi bi-diagram-3 me-2"></i>
        Lineage Events
      </div>
      <div class="card-body p-0">
        <div class="table-responsive">
          <table class="table table-striped table-hover mb-0">
            <thead class="table-dark">
              <tr>
                <th style="width: 160px">Time</th>
                <th style="width: 100px">Event</th>
                <th style="width: 80px">Model ID</th>
                <th style="width: 100px">RMSE</th>
                <th style="width: 80px">Rows</th>
                <th style="width: 100px">Previous Model</th>
                <th>Reason</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="e in events" :key="e.timestamp">
                <td class="small">{{ formatDate(e.timestamp) }}</td>
                <td>
                  <span :class="getEventBadgeClass(e.event_type)" class="badge">
                    <i :class="getEventIcon(e.event_type)" class="me-1"></i>
                    {{ formatEventType(e.event_type) }}
                  </span>
                </td>
                <td><strong>{{ e.model_id }}</strong></td>
                <td>
                  <span v-if="e.metadata?.rmse" class="text-primary">
                    {{ e.metadata.rmse.toFixed(4) }}
                  </span>
                  <span v-else class="text-muted">—</span>
                </td>
                <td>
                  <span v-if="e.metadata?.rows_used" class="text-muted">
                    {{ e.metadata.rows_used }}
                  </span>
                  <span v-else class="text-muted">—</span>
                </td>
                <td>
                  <span v-if="e.metadata?.previous_model_id" class="text-warning">
                    {{ e.metadata.previous_model_id }}
                  </span>
                  <span v-else class="text-muted">—</span>
                </td>
                <td class="small text-muted">
                  {{ e.reason || '—' }}
                </td>
              </tr>
            </tbody>
            <tbody v-if="events.length === 0">
              <tr>
                <td colspan="7" class="text-center text-muted py-4">
                  <i class="bi bi-diagram-3 fs-1"></i>
                  <p class="mt-2">No lineage events yet</p>
                  <small>Train or promote a model to see lineage</small>
                </td>
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
import { getLineage } from '../services/api'

interface LineageEvent {
  timestamp: string
  event_type: string
  model_id: string
  reason?: string
  metadata?: {
    rmse?: number
    rows_used?: number
    previous_model_id?: string
    decision?: any
  }
}

const events = ref<LineageEvent[]>([])

function formatDate(dateStr: string) {
  const date = new Date(dateStr)
  return date.toLocaleString('ru-RU')
}

function getEventBadgeClass(eventType: string): string {
  switch (eventType) {
    case 'promoted':
      return 'bg-success'
    case 'trained':
      return 'bg-primary'
    case 'upload':
      return 'bg-info'
    case 'rollback':
      return 'bg-warning text-dark'
    default:
      return 'bg-secondary'
  }
}

function getEventIcon(eventType: string): string {
  switch (eventType) {
    case 'promoted':
      return 'bi bi-star-fill'
    case 'trained':
      return 'bi bi-arrow-repeat'
    case 'upload':
      return 'bi bi-cloud-upload'
    case 'rollback':
      return 'bi bi-arrow-counterclockwise'
    default:
      return 'bi bi-circle'
  }
}

function formatEventType(eventType: string): string {
  const types: Record<string, string> = {
    'promoted': 'Promoted',
    'trained': 'Trained',
    'upload': 'Uploaded',
    'rollback': 'Rollback'
  }
  return types[eventType] || eventType.charAt(0).toUpperCase() + eventType.slice(1)
}

function getEventCount(eventType: string): number {
  return events.value.filter(e => e.event_type === eventType).length
}

onMounted(async () => {
  try {
    const res = await getLineage()
    events.value = res.data.reverse()
    console.log('📊 Lineage events loaded:', events.value.length)
  } catch (error) {
    console.error('Failed to load lineage:', error)
  }
})
</script>

<style scoped>
.badge {
  padding: 6px 10px;
  font-size: 12px;
  font-weight: 500;
}

.bg-success {
  background-color: #198754 !important;
}

.bg-primary {
  background-color: #0d6efd !important;
}

.bg-info {
  background-color: #0dcaf0 !important;
  color: #000 !important;
}

.bg-warning {
  background-color: #ffc107 !important;
  color: #000 !important;
}

.table-responsive {
  overflow-x: auto;
}

th, td {
  vertical-align: middle;
}
</style>