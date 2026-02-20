// frontend\src\services\api.ts

import axios from 'axios'

const api = axios.create({
    baseURL: '/api/v1',
    timeout: 5000
})

export const getHealth = () => api.get('/system/health')
export const getStatus = () => api.get('/system/status')
export const getMetrics = () => api.get('/system/metrics')

export default api