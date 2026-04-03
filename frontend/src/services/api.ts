// frontend\src\services\api.ts

import axios from 'axios'
import type { Model } from "@/types"

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

// Тип для датасета (соответствует API)
export interface Dataset {
    id: string
    created_at: string
    row_count: number
    target_column: string
    status: string
    comment: string | null
}

// Тип для параметров обучения 
export interface TrainModelParams {
    promote?: boolean
}

// Тип для модели
export interface ModelItem {
    ml_model_id: number
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

/* export const rollbackModel = (id: string) =>
    api.post(`/ml/models/rollback/${id}`) */

export const rollbackModel = () =>
    api.post('/ml/models/rollback')


// ============================
// MODEL TRAIN
// ============================ 


export const trainModel = async (data: TrainModelParams) => {
    console.log('🚀 Starting model training...', data)

    try {
        const response = await api.post('/ml/train', data, {
            timeout: 300000  // 5 минут
        })

        console.log('✅ Training completed:', response.data)
        return response

    } catch (error: unknown) {
        // Проверяем тип ошибки
        if (error && typeof error === 'object' && 'code' in error && error.code === 'ECONNABORTED') {
            console.error('❌ Training timeout - operation took too long')
            throw new Error('Training timeout. The model training is taking longer than expected. Please try again or check server logs.')
        }

        if (error instanceof Error) {
            console.error('❌ Training failed:', error.message)
        } else {
            console.error('❌ Training failed with unknown error:', error)
        }

        throw error
    }
}

// ========================================
// MODEL TRAIN DIRECT On The Runtime Page
// ========================================

export const trainModelDirect = async (promote: boolean = false) => {
    console.log('🚀 Starting direct model training...', { promote })
    
    try {
        const response = await api.post('/ml/train', { promote }, {
            timeout: 300000  // 5 минут
        })
        
        console.log('✅ Training completed:', response.data)
        return response
        
    } catch (error: unknown) {
        if (error && typeof error === 'object' && 'code' in error && error.code === 'ECONNABORTED') {
            console.error('❌ Training timeout')
            throw new Error('Training timeout. The model training is taking longer than expected.')
        }
        
        if (error instanceof Error) {
            console.error('❌ Training failed:', error.message)
        }
        
        throw error
    }
}


// ============================
// MODEL DELETE
// ============================ 

export const deleteModel = (modelId: number) => {
    console.log(`🗑️ Deleting model ${modelId}`);
    return api.delete(`/ml/models/${modelId}`);
}


// ============================
// MODELS COMPARE
// ============================ 

export const compareModels = (modelA: number, modelB: number) =>
    api.get('/ml/models/compare', {
        params: { model_a: modelA, model_b: modelB }
    })


// ============================
// MODEL DETAILS
// ============================

export const fetchModelDetails = async (modelId: number): Promise<Model> => {
    const response = await api.get(`/ml/models/${modelId}`)
    return response.data
}

export const fetchModelMetrics = (modelId: number) =>
    api.get(`/ml/models/${modelId}/metrics`)

export const promoteModel = (modelId: number) =>
    api.post(`/ml/models/${modelId}/promote`)

export const deactivateModel = (modelId: number) =>
    api.post(`/ml/models/${modelId}/deactivate`)

export default api


// ============================
// MODELS LINEAGE
// ============================ 

export const getLineage = () =>
    api.get('/ml/models/lineage')

// ============================
// MODELS Activation History
// ============================ 


export const getActivationHistory = (limit: number = 10) =>
    api.get(`/ml/models/activation-history?limit=${limit}`)


// ============================
// PREDICT 
// ============================ 

// Для одиночного прогноза
export const predict = (payload: any) =>
    api.post('/ml/predict', payload)  

// Для batch прогноза — отправляем массив в эндпоинт /predict/batch
export const predictBatch = (requests: any[]) => {
  console.log('📤 Sending batch request with', requests.length, 'items')
  return api.post('/ml/predict/batch', { requests })
}

// ============================
// AUDIT
// ============================ 

export function getAuditPage(page: number, modelId?: string) {

    const params: any = { page }

    if (modelId && modelId.trim() !== "") {
        params.model_id = modelId
    }

    console.log('📊 Audit request:', { page, modelId, params })

    return api.get("/ml/audit", { params })
}


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

// ============================
// DATASET DELETE
// ============================

export const deleteDataset = (datasetId: string, force: boolean = false) => {
    console.log('🗑️ deleteDataset called with:', {
        datasetId,
        force,
        type: typeof datasetId
    });

    if (!datasetId) {
        console.error('❌ Cannot delete: datasetId is undefined or empty');
        return Promise.reject(new Error('datasetId is required'));
    }

    const url = `/ml/datasets/${String(datasetId)}${force ? '?force=true' : ''}`;
    console.log('🗑️ DELETE URL:', url);

    return api.delete(url);
};