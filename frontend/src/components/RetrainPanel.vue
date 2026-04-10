<!-- frontend/src/components/RetrainPanel.vue -->

<template>
    <div class="card mb-4">
        <div class="card-header bg-primary text-white">
            <i class="bi bi-robot me-2"></i>
            Model Retraining
        </div>
        <div class="card-body">
            <div class="row align-items-center">
                <div class="col-md-8">
                    <p class="mb-1">
                        <strong>Retrain Model</strong>
                        <span class="text-muted ms-2">
                            <i class="bi bi-info-circle me-1"></i>
                            Train a new model on the entire dataset
                        </span>
                    </p>
                    <p class="text-muted small mb-0">
                        After training, metrics will be compared with the current active model.
                        Better metrics = automatic activation.
                    </p>
                </div>
                <div class="col-md-4 text-end">
                    <button class="btn btn-primary" @click="startTraining" :disabled="trainingInProgress">
                        <span v-if="trainingInProgress" class="spinner-border spinner-border-sm me-2"></span>
                        <i v-else class="bi bi-rocket-takeoff me-2"></i>
                        {{ trainingInProgress ? 'Training...' : 'Start Training' }}
                    </button>
                </div>
            </div>
        </div>

        <!-- Жёлтая карточка - новые данные -->
        <div v-if="showNewDataAlert" class="mx-3 mb-3 alert alert-warning alert-dismissible fade show" role="alert">
            <div class="d-flex justify-content-between align-items-start">
                <div>
                    <strong>📊 New Data Available!</strong>
                    <p class="mb-0 small">{{ newDataMessage }}</p>
                    <span class="small text-muted">{{ newRowsCount }} new rows detected</span>
                </div>
                <button type="button" class="btn-close" @click="showNewDataAlert = false" aria-label="Close"></button>
            </div>
        </div>

        <!-- Результат обучения -->
        <div v-if="uploadResult" class="mx-3 mb-3 alert alert-info alert-dismissible fade show" role="alert">
            <div class="d-flex justify-content-between align-items-start">
                <div>
                    <strong>Result:</strong>
                    <pre class="mb-0 mt-1">{{ uploadResult }}</pre>
                </div>
                <button type="button" class="btn-close" @click="uploadResult = null" aria-label="Close"></button>
            </div>
        </div>

        <!-- Сообщение о результате обучения с таблицей сравнения -->
        <div v-if="trainingResultMessage" class="mx-3 mb-3 alert" :class="trainingResultClass" role="alert">
            <div class="d-flex justify-content-between align-items-start">
                <div class="flex-grow-1">
                    <strong>{{ trainingResultTitle }}</strong>
                    <p class="mb-0 mt-1">{{ trainingResultMessage }}</p>
                    <small v-if="trainingResultDetails" class="text-muted">{{ trainingResultDetails }}</small>

                    <!-- Таблица сравнения -->
                    <div v-if="trainingResultComparison" class="mt-2">
                        <table class="table table-sm table-bordered mt-2" style="width: auto; background: #f8f9fa;">
                            <thead>
                                <tr>
                                    <th>Metric</th>
                                    <th>Current Model</th>
                                    <th>→</th>
                                    <th>New Model</th>
                                    <th>Change</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td class="fw-bold">RMSE</td>
                                    <td>{{ trainingResultCurrentRMSE?.toFixed(6) || '—' }}</td>
                                    <td>→</td>
                                    <td>{{ trainingResultNewRMSE?.toFixed(6) || '—' }}</td>
                                    <td :class="trainingResultIsBetter ? 'text-success' : 'text-danger'">
                                        {{ trainingResultIsBetter ? '✅ Better' : '⚠️ Worse' }}
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
                <button type="button" class="btn-close" @click="closeTrainingResult" aria-label="Close"></button>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import api from '../services/api'
import { trainModel } from '../services/api'

const emit = defineEmits(['model-trained', 'model-activated'])

const trainingInProgress = ref(false)
const checking = ref(false)

// Уведомления
const showNewDataAlert = ref(false)
const newRowsCount = ref(0)
const newDataMessage = ref('')
const uploadResult = ref<any>(null)

const trainingResultMessage = ref<string | null>(null)
const trainingResultTitle = ref('')
const trainingResultDetails = ref('')
const trainingResultClass = ref('alert-info')
const trainingResultCurrentRMSE = ref<number | null>(null)
const trainingResultNewRMSE = ref<number | null>(null)
const trainingResultIsBetter = ref(false)
const trainingResultComparison = ref(false)

function closeTrainingResult() {
    trainingResultMessage.value = null
    trainingResultComparison.value = false
}

async function checkNewData() {
    checking.value = true
    try {
        const response = await api.post('/system/force-retrain')
        if (response.data.needed) {
            newRowsCount.value = response.data.new_data_count || 0
            newDataMessage.value = response.data.reason || 'New data available for training'
            showNewDataAlert.value = true
        }
    } catch (error) {
        console.error('Check new data failed:', error)
    } finally {
        checking.value = false
    }
}

async function startTraining() {
    trainingInProgress.value = true
    showNewDataAlert.value = false
    trainingResultMessage.value = null

    try {
        const response = await trainModel({ promote: false })
        uploadResult.value = response.data

        // Получаем текущую активную модель
        const modelsResponse = await api.get('/ml/models')
        const models = modelsResponse.data
        const activeModel = models.find((m: any) => m.is_active === true)
        const newModelId = response.data.model_id
        const newRMSE = response.data.metrics?.rmse

        trainingResultNewRMSE.value = newRMSE || null

        if (activeModel && newRMSE) {
            const oldRMSE = activeModel.metrics?.rmse
            trainingResultCurrentRMSE.value = oldRMSE || null

            if (oldRMSE !== undefined && newRMSE !== undefined) {
                const isBetter = newRMSE <= oldRMSE
                trainingResultIsBetter.value = isBetter
                trainingResultComparison.value = true

                if (isBetter) {
                    // Метрики улучшились → активируем автоматически
                    await api.post(`/ml/models/${newModelId}/promote`)
                    emit('model-activated')

                    trainingResultClass.value = 'alert-success'
                    trainingResultTitle.value = '✅ Model Auto-Activated'
                    trainingResultMessage.value = `New model (ID: ${newModelId}) has been activated automatically.`
                    trainingResultDetails.value = `RMSE improved: ${oldRMSE.toFixed(6)} → ${newRMSE.toFixed(6)}`
                } else {
                    // Метрики хуже → не активируем
                    trainingResultClass.value = 'alert-warning'
                    trainingResultTitle.value = '⚠️ Model Trained but Not Activated'
                    trainingResultMessage.value = `New model (ID: ${newModelId}) has worse metrics.`
                    trainingResultDetails.value = `RMSE worsened: ${oldRMSE.toFixed(6)} → ${newRMSE.toFixed(6)} (${((newRMSE - oldRMSE) / oldRMSE * 100).toFixed(1)}% worse)`
                }
            } else {
                trainingResultComparison.value = false
                trainingResultClass.value = 'alert-info'
                trainingResultTitle.value = 'ℹ️ Model Trained'
                trainingResultMessage.value = `New model (ID: ${newModelId}) created.`
                trainingResultDetails.value = 'Unable to compare metrics (missing RMSE data)'
            }
        } else if (newModelId) {
            // Нет активной модели → активируем первую
            await api.post(`/ml/models/${newModelId}/activate`)
            emit('model-activated')

            trainingResultComparison.value = false
            trainingResultClass.value = 'alert-success'
            trainingResultTitle.value = '✅ First Model Activated'
            trainingResultMessage.value = `Model (ID: ${newModelId}) has been activated as the first model.`
            trainingResultDetails.value = `RMSE: ${newRMSE?.toFixed(6) || 'N/A'}`
        }

        emit('model-trained')

        setTimeout(() => {
            window.location.reload()
        }, 1500)


    } catch (error) {
        console.error('Training failed:', error)
        trainingResultComparison.value = false
        trainingResultClass.value = 'alert-danger'
        trainingResultTitle.value = '❌ Training Failed'
        trainingResultMessage.value = 'Model training failed. Check server logs.'
        trainingResultDetails.value = ''
    } finally {
        trainingInProgress.value = false
    }
}

// Загружаем проверку новых данных при монтировании
setTimeout(() => {
    checkNewData()
}, 1000)

defineExpose({
    checkNewData
})
</script>