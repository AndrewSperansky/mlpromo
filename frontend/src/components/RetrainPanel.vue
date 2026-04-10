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
                        This may take a few minutes. New model will be created but not activated automatically.
                    </p>
                </div>
                <div class="col-md-4 text-end">
                    <div class="d-flex gap-2">
                        <button class="btn btn-outline-secondary btn-sm" @click="forceCheck" :disabled="checking"
                            title="Check if retrain is needed">
                            <span v-if="checking" class="spinner-border spinner-border-sm me-1"></span>
                            <i v-else class="bi bi-search me-1"></i>
                            {{ checking ? 'Checking...' : 'Force Check' }}
                        </button>
                        <button class="btn btn-primary" @click="showTrainModal = true" :disabled="trainingInProgress">
                            <span v-if="trainingInProgress" class="spinner-border spinner-border-sm me-2"></span>
                            <i v-else class="bi bi-rocket-takeoff me-2"></i>
                            {{ trainingInProgress ? 'Training...' : 'Start Training' }}
                        </button>
                    </div>
                </div>
            </div>

            <!-- Force Check Result -->
            <div v-if="checkResult" class="mt-3 alert" :class="checkResult.needed ? 'alert-warning' : 'alert-info'">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <i :class="checkResult.needed ? 'bi bi-exclamation-triangle-fill' : 'bi bi-check-circle-fill'"
                            class="me-2"></i>
                        <strong>{{ checkResult.needed ? 'Retrain Recommended' : 'Model is Up to Date' }}</strong>
                        <p class="mb-0 small mt-1">{{ checkResult.reason || 'No retrain needed at this time' }}</p>
                    </div>
                    <div v-if="checkResult.new_data_count !== undefined" class="text-end">
                        <span class="badge bg-secondary">{{ checkResult.new_data_count }} new rows</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Train Modal -->
        <TrainModal :show="showTrainModal" :training="trainingInProgress" @close="showTrainModal = false"
            @confirm="handleTrain" />

        <!-- Training Result Card -->
        <TrainingResultCard v-if="trainingCompleted && trainingResult" :trainingResult="trainingResult"
            @activated="handleTrainingActivated" @dismissed="handleTrainingDismissed" />
    </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { trainModel } from '../services/api'
import api from '../services/api'
import TrainModal from './TrainModal.vue'
import TrainingResultCard from './TrainingResultCard.vue'

const showTrainModal = ref(false)
const trainingInProgress = ref(false)
const trainingCompleted = ref(false)
const trainingResult = ref<any>(null)
const checking = ref(false)
const checkResult = ref<any>(null)

const emit = defineEmits(['model-trained', 'model-activated'])

async function forceCheck() {
    checking.value = true
    checkResult.value = null
    try {
        const response = await api.post('/system/force-retrain')
        checkResult.value = response.data
    } catch (error) {
        console.error('Force check failed:', error)
    } finally {
        checking.value = false
        // Скрываем результат через 10 секунд
        setTimeout(() => {
            checkResult.value = null
        }, 10000)
    }
}

async function handleTrain() {
    trainingInProgress.value = true
    showTrainModal.value = false

    try {
        const response = await trainModel({ promote: false })
        trainingResult.value = response.data
        trainingCompleted.value = true
        emit('model-trained')
    } catch (error) {
        console.error('Training failed:', error)
        alert('Training failed. Check server logs.')
        trainingCompleted.value = false
    } finally {
        trainingInProgress.value = false
    }
}

function handleTrainingActivated() {
    trainingCompleted.value = false
    trainingResult.value = null
    emit('model-activated')
}

function handleTrainingDismissed() {
    trainingCompleted.value = false
    trainingResult.value = null
}
</script>