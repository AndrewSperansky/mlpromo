// frontend\src\services\api.ts

import axios from 'axios'

const api = axios.create({
    baseURL: '/api/v1',
    timeout: 5000
})

export const getHealth = () => api.get('/system/health')
export const getStatus = () => api.get('/system/status')
export const getMetrics = () => api.get('/system/metrics')

export const getModels = () => api.get('/ml/models')

export const activateModel = (modelId: string) =>
    api.post(`/ml/models/${modelId}/activate`)

export const uploadModel = (formData: FormData) =>
    api.post('/ml/models/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    })

export const evaluateModel = (id: string) =>
    api.post(`/api/v1/ml/models/evaluate/${id}`)

export const rollbackModel = (id: string) =>
    api.post(`/api/v1/ml/models/rollback/${id}`)

export const getLineage = () =>
    api.get('/api/v1/ml/models/lineage')

export const predictBatch = (rows: any[]) =>
    api.post('/api/v1/ml/predict', { data: rows })

export const getAuditPage = (page: number, modelId: string) =>
    api.get('/api/v1/ml/audit', {
        params: { page, model_id: modelId }
    })


export default api

