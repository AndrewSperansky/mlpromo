// frontend\src\services\api.ts

import axios from 'axios'

const api = axios.create({
    baseURL: '/api/v1',
    timeout: 5000
})

// Добавляем интерцепторы для логирования ВСЕХ запросов и ответов
api.interceptors.request.use(request => {
    console.log('🚀 Request:', {
        method: request.method?.toUpperCase(),
        url: request.url,
        baseURL: request.baseURL,
        fullURL: `${request.baseURL}${request.url}`,
        params: request.params,
        data: request.data
    })
    return request
})

api.interceptors.response.use(
    response => {
        console.log('✅ Response OK:', {
            status: response.status,
            url: response.config.url,
            data: response.data
        })
        return response
    },
    error => {
        console.error('❌ Response Error:', {
            status: error.response?.status,
            statusText: error.response?.statusText,
            url: error.config?.url,
            method: error.config?.method?.toUpperCase(),
            data: error.response?.data,
            headers: error.response?.headers
        })
        return Promise.reject(error)
    }
)

// ============================
// TYPES
// ============================

export interface Dataset {
    dataset_version_id: string
    created_at: string
    row_count: number
}

export interface ModelItem {
    ml_model_id: string
    version: string
    active: boolean
    created_at: string
}

// ============================
// TRAIN MODEL TYPES
// ============================

export interface TrainModelParams {
    dataset_version_id?: string      // опционально, нужно если train_on_all = false
    train_on_all?: boolean            // новый параметр
    promote?: boolean                 // опционально
}

// ============================
// SYSTEM HEALTH
// ============================ 

export const getHealth = () => api.get('/system/health')

// ============================
// SYSTEM STATUS
// ============================ 

export const getStatus = () => api.get('/system/status')

// ============================
// SYSTEM METRICS
// ============================ 

export const getMetrics = () => api.get('/system/metrics')

// ============================
// MODELS LIST
// ============================ 

export const getModels = () =>
    api.get<ModelItem[]>('/ml/models')

// ============================
// MODEL ACTIVATE
// ============================ 

export const activateModel = (modelId: string) =>
    api.post(`/ml/models/${modelId}/activate`)

// ============================
// MODEL UPLOAD
// ============================ 

export const uploadModel = (formData: FormData) =>
    api.post('/ml/models/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    })

// ============================
// MODEL EVALUATE
// ============================ 

export const evaluateModel = (id: string) =>
    api.post(`/ml/models/evaluate/${id}`)

// ============================
// MODEL ROLLBACK
// ============================ 

export const rollbackModel = (id: string) =>
    api.post(`/ml/models/rollback/${id}`)

// ============================
// LINEAGE
// ============================ 

export const getLineage = () =>
    api.get('/ml/models/lineage')

// ============================
// PREDICT BATCH
// ============================ 

export const predictBatch = (rows: any[]) =>
    api.post('/ml/predict', { data: rows })

// ============================
// AUDIT
// ============================ 

export const getAuditPage = (page: number, modelId: string) =>
    api.get('/ml/audit', {
        params: { page, model_id: modelId }
    })

// ============================
// MODEL TRAIN (ОБНОВЛЕНО!)
// ============================    

export const trainModel = (data: TrainModelParams) =>
    api.post('/ml/train', data)

// ============================
// DATASETS
// ============================

export const fetchDatasets = () => {
    console.log('📊 Fetching datasets...')
    return api.get<Dataset[]>('/ml/datasets')
}

export const fetchDatasetModels = (datasetId: string) => {
    console.log('📊 Fetching models for dataset:', datasetId)
    return api.get(`/ml/datasets/${datasetId}/models`)
}

export const deleteDataset = (datasetId: string) => {
    console.log('🗑️ deleteDataset called with:', {
        datasetId,
        type: typeof datasetId,
        value: datasetId,
        isEmpty: !datasetId
    })

    if (!datasetId) {
        console.error('❌ Cannot delete: datasetId is undefined or empty')
        return Promise.reject(new Error('datasetId is required'))
    }

    const url = `/ml/datasets/${String(datasetId)}`
    console.log('🗑️ DELETE URL:', url)

    return api.delete(url)
}

// ============================
// MODEL DETAILS
// ============================

export const fetchModelDetails = (modelId: number) =>
    api.get(`/models/${modelId}`)

export const fetchModelMetrics = (modelId: number) =>
    api.get(`/models/${modelId}/metrics`)

export const promoteModel = (modelId: number) =>
    api.post(`/models/${modelId}/promote`)

export const deactivateModel = (modelId: number) =>
    api.post(`/models/${modelId}/deactivate`)

export default api