<!-- frontend/src/components/ModelDetailsModal.vue -->

<template>
  <div class="modal fade show" style="display:block" tabindex="-1" v-if="modelId">
    <div class="modal-dialog modal-lg">
      <div class="modal-content">

        <!-- ===== HEADER ===== -->
        <div class="modal-header">
          <h5 class="modal-title">
            <i class="bi bi-cpu me-2"></i>
            Model Details
          </h5>
          <button class="btn-close" @click="$emit('closed')"></button>
        </div>

        <!-- ===== BODY ===== -->
        <div class="modal-body">

          <!-- Loading -->
          <div v-if="loading" class="text-center py-4">
            <div class="spinner-border text-primary"></div>
            <p class="mt-2 text-muted">Loading model details...</p>
          </div>

          <!-- Model Info -->
          <div v-else-if="model">
            <!-- Основная информация -->
            <div class="row mb-4">
              <div class="col-md-4">
                <div class="info-label">Model Name</div>
                <div class="info-value">{{ model.name || '—' }}</div>
              </div>
              <div class="col-md-4">
                <div class="info-label">Version</div>
                <div class="info-value">{{ model.version || '—' }}</div>
              </div>
              <div class="col-md-4">
                <div class="info-label">Algorithm</div>
                <div class="info-value">
                  <span class="badge" :class="getAlgorithmClass(model.algorithm)">
                    {{ getAlgorithmLabel(model.algorithm) }}
                  </span>
                </div>
              </div>
            </div>

            <div class="row mb-4">
              <div class="col-md-4">
                <div class="info-label">Model Type</div>
                <div class="info-value">{{ model.model_type || '—' }}</div>
              </div>
              <div class="col-md-4">
                <div class="info-label">Target</div>
                <div class="info-value">{{ model.target || '—' }}</div>
              </div>
              <div class="col-md-4">
                <div class="info-label">Status</div>
                <div class="info-value">
                  <span class="badge" :class="model.is_active ? 'bg-success' : 'bg-secondary'">
                    {{ model.is_active ? '✅ Active' : 'Inactive' }}
                  </span>
                </div>
              </div>
            </div>

            <div class="row mb-4">
              <div class="col-md-4">
                <div class="info-label">Trained Rows</div>
                <div class="info-value">{{ model.trained_rows_count?.toLocaleString() || '—' }}</div>
              </div>
              <div class="col-md-4">
                <div class="info-label">Features Count</div>
                <div class="info-value">{{ model.features?.length || '—' }}</div>
              </div>
              <div class="col-md-4">
                <div class="info-label">Trained At</div>
                <div class="info-value">{{ formatDate(model.trained_at || model.created_at || null) }}</div>
              </div>
            </div>

            <!-- Метрики (красиво) -->
            <h6 class="mt-4 mb-3">
              <i class="bi bi-bar-chart-steps me-2"></i>
              Metrics
            </h6>

            <div class="metrics-grid">
              <!-- RMSE -->
              <div class="metric-card" v-if="metrics?.rmse !== undefined">
                <div class="metric-label">RMSE</div>
                <div class="metric-value">{{ metrics.rmse.toFixed(6) }}</div>
                <div class="metric-badge" :class="metrics.rmse < 1 ? 'bg-success' : 'bg-warning'">
                  {{ metrics.rmse < 1 ? '✅ Excellent' : '⚠️ Moderate' }}
                </div>
              </div>

              <!-- Validation RMSE -->
              <div class="metric-card" v-if="metrics?.val_rmse !== undefined">
                <div class="metric-label">Validation RMSE</div>
                <div class="metric-value">{{ metrics.val_rmse.toFixed(6) }}</div>
                <div class="metric-badge bg-info">Hold-out</div>
              </div>

              <!-- Train RMSE -->
              <div class="metric-card" v-if="metrics?.train_rmse !== undefined">
                <div class="metric-label">Train RMSE</div>
                <div class="metric-value">{{ metrics.train_rmse.toFixed(6) }}</div>
                <div class="metric-badge bg-secondary">Reference</div>
              </div>

              <!-- Coverage -->
              <div class="metric-card" v-if="metrics?.coverage !== undefined">
                <div class="metric-label">Coverage</div>
                <div class="metric-value">{{ (metrics.coverage * 100).toFixed(2) }}%</div>
                <div class="metric-badge" :class="getCoverageClass(metrics.coverage)">
                  {{ getCoverageLabel(metrics.coverage) }}
                </div>
              </div>

              <!-- Uplift -->
              <div class="metric-card" v-if="metrics?.uplift !== undefined">
                <div class="metric-label">Uplift</div>
                <div class="metric-value">{{ metrics.uplift.toFixed(4) }}x</div>
                <div class="metric-badge" :class="metrics.uplift > 1 ? 'bg-success' : 'bg-secondary'">
                  {{ metrics.uplift > 1 ? '📈 Positive' : '📉 Neutral' }}
                </div>
              </div>

              <!-- Accuracy@ε -->
              <div class="metric-card" v-if="metrics?.accuracy_eps !== undefined">
                <div class="metric-label">Accuracy@ε (5%)</div>
                <div class="metric-value">{{ (metrics.accuracy_eps * 100).toFixed(2) }}%</div>
                <div class="metric-badge" :class="metrics.accuracy_eps > 0.95 ? 'bg-success' : 'bg-warning'">
                  {{ metrics.accuracy_eps > 0.95 ? '✅ High' : '⚠️ Moderate' }}
                </div>
              </div>

              <!-- Best Iteration -->
              <div class="metric-card" v-if="metrics?.best_iteration !== undefined">
                <div class="metric-label">Best Iteration</div>
                <div class="metric-value">{{ metrics.best_iteration }}</div>
                <div class="metric-badge bg-secondary">Early stopping</div>
              </div>

              <!-- Total Iterations -->
              <div class="metric-card" v-if="metrics?.total_iterations !== undefined">
                <div class="metric-label">Total Iterations</div>
                <div class="metric-value">{{ metrics.total_iterations }}</div>
                <div class="metric-badge bg-secondary">Completed</div>
              </div>

              <!-- Sample Size -->
              <div class="metric-card" v-if="metrics?.sample_size !== undefined">
                <div class="metric-label">Sample Size</div>
                <div class="metric-value">{{ metrics.sample_size.toLocaleString() }}</div>
                <div class="metric-badge bg-secondary">Records</div>
              </div>

              <!-- Train/Val/Test sizes -->
              <div class="metric-card" v-if="metrics?.train_size !== undefined">
                <div class="metric-label">Train / Val / Test</div>
                <div class="metric-value small">
                  {{ metrics.train_size?.toLocaleString() }} / 
                  {{ metrics.validation_size?.toLocaleString() }} / 
                  {{ metrics.test_size?.toLocaleString() }}
                </div>
                <div class="metric-badge bg-secondary">Split</div>
              </div>
            </div>

            <!-- Confidence Interval (RMSE CI) -->
            <div v-if="metrics?.rmse_ci" class="mt-4">
              <h6 class="mb-2">
                <i class="bi bi-bounding-box-circles me-2"></i>
                RMSE Confidence Interval (95%)
              </h6>
              <div class="ci-display">
                <span class="ci-value">{{ metrics.rmse_ci.rmse?.toFixed(6) }}</span>
                <span class="ci-range">
                  [{{ metrics.rmse_ci.lower?.toFixed(6) }} — {{ metrics.rmse_ci.upper?.toFixed(6) }}]
                </span>
                <span class="ci-margin text-muted">
                  ±{{ metrics.rmse_ci.margin?.toFixed(6) }}
                </span>
              </div>
            </div>

            <!-- Conformal Prediction -->
            <div v-if="metrics?.conformal" class="mt-4">
              <h6 class="mb-2">
                <i class="bi bi-sigma me-2"></i>
                Conformal Prediction
              </h6>
              <div class="row g-2">
                <div class="col-md-4">
                  <div class="info-label">Alpha (α)</div>
                  <div class="info-value">{{ metrics.conformal.alpha || '—' }}</div>
                </div>
                <div class="col-md-4">
                  <div class="info-label">Q-hat (q̂)</div>
                  <div class="info-value">{{ metrics.conformal.q_hat?.toFixed(6) || '—' }}</div>
                </div>
                <div class="col-md-4">
                  <div class="info-label">Interval Width</div>
                  <div class="info-value">{{ metrics.conformal.interval_width?.toFixed(6) || '—' }}</div>
                </div>
              </div>
            </div>

            <!-- Features -->
            <div v-if="model.features?.length" class="mt-4">
              <h6 class="mb-2">
                <i class="bi bi-list-ul me-2"></i>
                Features ({{ model.features.length }})
              </h6>
              <div class="features-list">
                <span v-for="f in model.features" :key="f" class="feature-tag">
                  {{ f }}
                </span>
              </div>
            </div>

            <!-- Statistical Comparison -->
            <div v-if="metrics?.statistical_comparison" class="mt-4">
              <h6 class="mb-2">
                <i class="bi bi-graph-up-arrow me-2"></i>
                Statistical Comparison
              </h6>
              <div class="alert alert-info small">
                <p class="mb-1"><strong>Test:</strong> {{ metrics.statistical_comparison.test_used || '—' }}</p>
                <p class="mb-0"><strong>Current Model:</strong> ID {{ metrics.statistical_comparison.current_model_id }} (v{{ metrics.statistical_comparison.current_model_version }})</p>
              </div>
            </div>

          </div>

          <!-- No model -->
          <div v-else class="text-center py-4 text-muted">
            <i class="bi bi-cpu fs-1"></i>
            <p class="mt-2">Model not found</p>
          </div>

        </div>

        <!-- ===== FOOTER ===== -->
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="$emit('closed')">
            <i class="bi bi-x-lg me-1"></i>
            Close
          </button>
        </div>

      </div>
    </div>
  </div>

  <!-- Backdrop -->
  <div class="modal-backdrop fade show" v-if="modelId"></div>
</template>

<script setup lang="ts">
import { ref, watch } from "vue"
import {
    fetchModelDetails,
    fetchModelMetrics,
} from "@/services/api"
import type { Model } from "@/types"

const props = defineProps<{
    modelId: number | null
}>()

const emit = defineEmits(["closed", "updated"])

const model = ref<Model | null>(null)
const metrics = ref<Record<string, any> | null>(null)
const loading = ref(false)

// ===== Форматирование =====
function formatDate(dateStr: string | null) {
    if (!dateStr) return '—'
    const date = new Date(dateStr)
    return date.toLocaleString('ru-RU', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    })
}

function getAlgorithmClass(algorithm: string | undefined): string {
    if (!algorithm) return 'bg-secondary'
    if (algorithm.startsWith('pytorch')) return 'bg-info text-dark'
    if (algorithm === 'catboost') return 'bg-primary'
    return 'bg-secondary'
}

function getAlgorithmLabel(algorithm: string | undefined): string {
    if (!algorithm) return 'Unknown'
    if (algorithm === 'catboost') return 'CatBoost'
    if (algorithm === 'pytorch_lstm') return 'LSTM'
    if (algorithm === 'pytorch_lstm_with_embeddings') return 'LSTM (Embeddings)'
    return algorithm
}

function getCoverageClass(coverage: number): string {
    if (coverage >= 0.94 && coverage <= 0.96) return 'bg-success'
    if (coverage >= 0.92) return 'bg-warning'
    return 'bg-danger'
}

function getCoverageLabel(coverage: number): string {
    if (coverage >= 0.94 && coverage <= 0.96) return '✅ Calibrated'
    if (coverage >= 0.92) return '⚠️ Slightly off'
    return '❌ Poor calibration'
}

// ===== Загрузка данных =====
watch(
    () => props.modelId,
    async (id) => {
        if (!id) return

        loading.value = true
        try {
            model.value = await fetchModelDetails(id)
            const metricsResponse = await fetchModelMetrics(id)
            metrics.value = metricsResponse.data?.metrics || null
        } catch (error) {
            console.error('Failed to load model details:', error)
        } finally {
            loading.value = false
        }
    },
    { immediate: true }
)
</script>

<style scoped>
.modal-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.4);
    z-index: 1040;
}

.info-label {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    color: #6c757d;
    letter-spacing: 0.5px;
}

.info-value {
    font-size: 15px;
    font-weight: 500;
    padding: 2px 0 8px 0;
}

.metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: 12px;
}

.metric-card {
    background: #f8f9fa;
    border-radius: 8px;
    padding: 12px 14px;
    border: 1px solid #e9ecef;
    transition: all 0.2s;
}

.metric-card:hover {
    border-color: #0d6efd;
    box-shadow: 0 2px 8px rgba(13, 110, 253, 0.1);
}

.metric-label {
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    color: #6c757d;
    letter-spacing: 0.3px;
    margin-bottom: 2px;
}

.metric-value {
    font-size: 18px;
    font-weight: 700;
    color: #212529;
}

.metric-badge {
    font-size: 9px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 10px;
    display: inline-block;
    margin-top: 4px;
    color: white;
}

.bg-success {
    background-color: #198754 !important;
}

.bg-warning {
    background-color: #ffc107 !important;
    color: #000 !important;
}

.bg-danger {
    background-color: #dc3545 !important;
}

.bg-info {
    background-color: #0dcaf0 !important;
    color: #000 !important;
}

.bg-secondary {
    background-color: #6c757d !important;
}

.bg-primary {
    background-color: #0d6efd !important;
}

/* CI Display */
.ci-display {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 10px 16px;
    background: #f8f9fa;
    border-radius: 8px;
    border: 1px solid #e9ecef;
    flex-wrap: wrap;
}

.ci-value {
    font-size: 18px;
    font-weight: 700;
    color: #212529;
}

.ci-range {
    font-size: 15px;
    font-weight: 500;
    color: #0d6efd;
}

.ci-margin {
    font-size: 13px;
}

/* Features */
.features-list {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    padding: 8px 0;
}

.feature-tag {
    background: #e9ecef;
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 500;
    color: #495057;
    border: 1px solid #dee2e6;
}

.feature-tag:hover {
    background: #0d6efd;
    color: white;
    border-color: #0d6efd;
}

/* Badge */
.badge {
    font-size: 13px;
    padding: 4px 12px;
}
</style>