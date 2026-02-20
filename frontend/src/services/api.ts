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

export default api

