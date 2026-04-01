// frontend\src\types.ts

export interface Dataset {
    id: string
    created_at: string
    rows_count: number
}

export interface Model {
    id: number
    name: string
    version: string
    algorithm?: string
    model_type?: string
    target?: string
    trained_rows_count: number
    is_active: boolean
    trained_at?: string
    metrics?: Record<string, any>
    features?: string[]
}