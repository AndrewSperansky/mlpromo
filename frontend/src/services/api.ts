// frontend\src\services\api.ts

import axios from 'axios'

const api = axios.create({
    baseURL: '/api/v1',
    timeout: 5000
})

// ============================
// TYPES
// ============================

export interface Dataset {
    dataset_version_id: string
    created_at: string
    rows_count: number
}

export interface ModelItem {
    ml_model_id: string
    version: string
    active: boolean
    created_at: string
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

// export const getModels = () => api.get('/ml/models')      //  native fetch 

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
// VODEL EVALUATE
// ============================ 

export const evaluateModel = (id: string) =>
    api.post(`/ml/models/evaluate/${id}`)

// ============================
// MODEL ROLLBACK
// ============================ 

export const rollbackModel = (id: string) =>
    api.post(`/ml/models/rollback/${id}`)

// ============================
// LEANAGE
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
// MODEL TRAIN
// ============================    

export const trainModel = (data: { dataset_version_id: string }) =>
    api.post('/ml/train', data)


// ============================
// DATASETS
// ============================

export const fetchDatasets = () =>
    api.get<Dataset[]>('/ml/datasets')


export async function fetchDatasetModels(datasetId: string) {
    return fetch(`api/v1/ml/datasets/${datasetId}/models`).then(r => r.json());
}



// ============================
// MODEL DETAILS
// ============================

export async function fetchModelDetails(modelId: number) {
    return fetch(`/api/v1/models/${modelId}`).then(r => r.json());
}

export async function fetchModelMetrics(modelId: number) {
    return fetch(`/api/v1/models/${modelId}/metrics`).then(r => r.json());
}

export async function promoteModel(modelId: number) {
    return fetch(`/api/v1/models/${modelId}/promote`, {
        method: "POST",
    }).then(r => r.json());
}

export async function deactivateModel(modelId: number) {
    return fetch(`/api/v1/models/${modelId}/deactivate`, {
        method: "POST",
    }).then(r => r.json());
}


export default api

