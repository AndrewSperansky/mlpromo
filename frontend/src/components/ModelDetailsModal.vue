<!-- frontend\src\components\ModelDetailsModal.vue -->

<script setup lang="ts">
import { ref, watch } from "vue"
import {
    fetchModelDetails,
    fetchModelMetrics,
    promoteModel,
    deactivateModel,
} from "@/services/api"
import type { Model } from "@/types"

const props = defineProps<{
    modelId: number | null
}>()

const emit = defineEmits(["closed", "updated"])

const model = ref<Model | null>(null)
const metrics = ref<Record<string, any> | null>(null)
const loading = ref(false)

watch(
    () => props.modelId,
    async (id) => {
        if (!id) return

        loading.value = true
        model.value = await fetchModelDetails(id)

        const metricsResponse = await fetchModelMetrics(id)
        metrics.value = metricsResponse.data

        loading.value = false
    }
)

async function promote() {
    if (!model.value) return
    await promoteModel(model.value.id)
    model.value.is_active = true
    emit("updated")
}

async function deactivate() {
    if (!model.value) return
    await deactivateModel(model.value.id)
    model.value.is_active = false
    emit("updated")
}
</script>

<template>
    <div class="modal fade show" style="display:block" tabindex="-1" v-if="modelId">
        <div class="modal-dialog modal-lg">
            <div class="modal-content">

                <!-- HEADER -->

                <div class="modal-header">
                    <h5 class="modal-title">Model Details</h5>

                    <button class="btn-close" @click="$emit('closed')"></button>
                </div>

                <!-- BODY -->

                <div class="modal-body">

                    <div v-if="loading">
                        Loading model...
                    </div>

                    <div v-else-if="model">

                        <div class="row mb-3">
                            <div class="col-md-6">
                                <b>Name:</b> {{ model.name }}
                            </div>

                            <div class="col-md-6">
                                <b>Version:</b> {{ model.version }}
                            </div>
                        </div>

                        <div class="row mb-3">
                            <div class="col-md-6">
                                <b>Dataset:</b> {{ model.dataset_version_id }}
                            </div>

                            <div class="col-md-6">
                                <b>Rows:</b> {{ model.trained_rows_count }}
                            </div>
                        </div>

                        <div class="mb-3">
                            <b>Status:</b>

                            <span class="badge" :class="model.is_active ? 'bg-success' : 'bg-secondary'">
                                {{ model.is_active ? "Active" : "Inactive" }}
                            </span>
                        </div>

                        <!-- METRICS -->

                        <h6>Metrics</h6>

                        <table v-if="metrics" class="table table-sm table-bordered">
                            <tbody>
                                <tr v-for="(value, key) in metrics" :key="key">
                                    <td>{{ key }}</td>
                                    <td>{{ value }}</td>
                                </tr>
                            </tbody>
                        </table>

                    </div>
                </div>

                <!-- FOOTER -->

                <div class="modal-footer">

                    <button class="btn btn-success" @click="promote" v-if="model && !model.is_active">
                        Promote
                    </button>

                    <button class="btn btn-warning" @click="deactivate" v-if="model && model.is_active">
                        Deactivate
                    </button>

                    <button class="btn btn-secondary" @click="$emit('closed')">
                        Close
                    </button>

                </div>

            </div>
        </div>
    </div>

    <!-- BACKDROP -->

    <div class="modal-backdrop fade show" v-if="modelId"></div>
</template>