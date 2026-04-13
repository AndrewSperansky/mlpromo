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
            <h6 class="card-title">Retrains</h6>
            <h2 class="mb-0">{{ getEventCount('retrain') + getEventCount('trained') }}</h2>
          </div>
        </div>
      </div>
    </div>

    <!-- Таблица с улучшенным отображением -->
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
                <th style="width: 180px">Time</th>
                <th style="width: 120px">Event</th>
                <th>Model ID</th>
                <th>Details</th>
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
                <td>
                  <strong>{{ e.model_id }}</strong>
                </td>
                <td class="small text-muted">
                  <span v-if="e.metadata?.decision" class="text-info">
                    Decision: {{ e.metadata.decision.decision || e.metadata.decision }}
                  </span>
                  <span v-else-if="e.metadata?.reason" class="text-warning">
                    {{ e.metadata.reason }}
                  </span>
                  <span v-else>—</span>
                </td>
              </tr>
            </tbody>
            <tbody v-if="events.length === 0">
              <tr>
                <td colspan="4" class="text-center text-muted py-4">
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
  metadata?: any
}

const events = ref<LineageEvent[]>([])

function formatDate(dateStr: string) {
  const date = new Date(dateStr)
  return date.toLocaleString('ru-RU')
}

function getEventBadgeClass(eventType: string): string {
  switch (eventType) {
    case 'promoted':
    case 'approve':
      return 'bg-success'
    case 'retrain':
    case 'trained':
      return 'bg-primary'
    case 'rejected':
    case 'reject':
      return 'bg-danger'
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
    case 'approve':
      return 'bi bi-check-circle'
    case 'retrain':
    case 'trained':
      return 'bi bi-arrow-repeat'
    case 'rejected':
    case 'reject':
      return 'bi bi-x-circle'
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
    'approve': 'Approved',
    'retrain': 'Retrain',
    'trained': 'Trained',
    'rejected': 'Rejected',
    'reject': 'Rejected',
    'upload': 'Uploaded',
    'rollback': 'Rollback',
    'evaluate': 'Evaluated'
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

.bg-danger {
  background-color: #dc3545 !important;
}

.bg-warning {
  background-color: #ffc107 !important;
  color: #000 !important;
}

.bg-info {
  background-color: #0dcaf0 !important;
  color: #000 !important;
}

.bg-secondary {
  background-color: #6c757d !important;
}

.table-responsive {
  overflow-x: auto;
}
</style>