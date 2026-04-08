<!-- frontend/src/pages/Users.vue -->
<template>
    <div>
        <h2 class="mb-4">User Management</h2>

        <!-- Statistics -->
        <div class="row g-3 mb-4">
            <div class="col-md-4">
                <div class="card bg-primary text-white">
                    <div class="card-body">
                        <h6 class="card-title">Total Users</h6>
                        <h2 class="mb-0">{{ users.length }}</h2>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card bg-success text-white">
                    <div class="card-body">
                        <h6 class="card-title">Active Users</h6>
                        <h2 class="mb-0">{{ activeUsersCount }}</h2>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card bg-info text-white">
                    <div class="card-body">
                        <h6 class="card-title">Admins</h6>
                        <h2 class="mb-0">{{ adminCount }}</h2>
                    </div>
                </div>
            </div>
        </div>

        <!-- User Table -->
        <div class="card shadow-sm">
            <div class="card-header bg-secondary text-white d-flex justify-content-between align-items-center">
                <span><i class="bi bi-people me-2"></i>Users</span>
                <button class="btn btn-sm btn-light" @click="loadUsers" :disabled="loading">
                    <i class="bi bi-arrow-repeat"></i> Refresh
                </button>
            </div>
            <div class="card-body p-0">
                <div v-if="loading" class="text-center py-4">
                    <div class="spinner-border text-primary"></div>
                </div>
                <div v-else-if="users.length === 0" class="text-center py-4 text-muted">
                    No users found
                </div>
                <table v-else class="table table-striped table-hover mb-0">
                    <thead class="table-dark">
                        <tr>
                            <th>ID</th>
                            <th>Username</th>
                            <th>Email</th>
                            <th>Full Name</th>
                            <th>Role</th>
                            <th>Status</th>
                            <th>Active</th>
                            <th>Last Login</th>
                            <th style="width: 100px">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="user in users" :key="user.id">
                            <td>{{ user.id }}</td>
                            <td>{{ user.username }}</td>
                            <td>{{ user.email }}</td>
                            <td>{{ user.full_name || '-' }}</td>
                            <td>
                                <span :class="getRoleBadgeClass(user.role)">
                                    {{ user.role }}
                                </span>
                            </td>
                            <td>
                                <span :class="user.is_active ? 'badge bg-success' : 'badge bg-danger'">
                                    {{ user.is_active ? 'Active' : 'Blocked' }}
                                </span>
                            </td>
                            <td>
                                <div class="form-check">
                                    <input class="form-check-input" type="checkbox" :checked="user.is_active"
                                        @change="toggleUserStatus(user)" :disabled="user.id === authStore.user?.id"
                                        style="width: 20px; height: 20px; cursor: pointer;">
                                </div>
                            </td>

                            <td class="small">
                                {{ formatDate(user.last_login_at) }}
                            </td>

                            <td>
                                <div class="btn-group" role="group">
                                    <button class="btn btn-sm btn-primary" @click="editUser(user)" title="Edit"
                                        style="padding: 4px 8px;">
                                        <i class="bi bi-pencil"></i>
                                    </button>
                                    <button v-if="user.id !== authStore.user?.id" class="btn btn-sm btn-danger"
                                        @click="deleteUser(user)" title="Delete" style="padding: 4px 8px;">
                                        <i class="bi bi-trash3"></i>
                                    </button>
                                </div>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Edit User Modal -->
        <div v-if="showEditModal && editingUser" class="modal-backdrop" @click.self="showEditModal = false">
            <div class="modal-box" style="width: 450px;">
                <h5>Edit User</h5>
                <hr>

                <div class="mb-3">
                    <label class="form-label">Username</label>
                    <input type="text" class="form-control" v-model="editingUser.username" disabled>
                </div>

                <div class="mb-3">
                    <label class="form-label">Email</label>
                    <input type="email" class="form-control" v-model="editingUser.email">
                </div>

                <div class="mb-3">
                    <label class="form-label">Full Name</label>
                    <input type="text" class="form-control" v-model="editingUser.full_name">
                </div>

                <div class="mb-3">
                    <label class="form-label">Role</label>
                    <select class="form-select" v-model="editingUser.role">
                        <option value="viewer">Viewer</option>
                        <option value="analyst">Analyst</option>
                        <option value="ml_engineer">ML Engineer</option>
                        <option value="admin">Admin</option>
                    </select>
                </div>

                <div class="d-flex justify-content-end gap-2 mt-3">
                    <button class="btn btn-secondary" @click="showEditModal = false">Cancel</button>
                    <button class="btn btn-primary" @click="saveUser" :disabled="saving">
                        <span v-if="saving" class="spinner-border spinner-border-sm me-2"></span>
                        Save Changes
                    </button>
                </div>
            </div>
        </div>

        <!-- Delete Confirmation Modal -->
        <div v-if="showDeleteModal" class="modal-backdrop" @click.self="showDeleteModal = false">
            <div class="modal-box">
                <h5 class="text-danger">Confirm Delete</h5>
                <p>Are you sure you want to delete user:</p>
                <strong>{{ userToDelete?.username }}</strong>
                <p class="text-warning mt-2">⚠️ This action cannot be undone!</p>

                <div class="mt-3 d-flex justify-content-end gap-2">
                    <button class="btn btn-secondary" @click="showDeleteModal = false">Cancel</button>
                    <button class="btn btn-danger" @click="confirmDelete" :disabled="deleting">
                        <span v-if="deleting" class="spinner-border spinner-border-sm me-2"></span>
                        Delete Permanently
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import api from '../services/api'

interface User {
    id: number
    username: string
    email: string
    full_name: string | null
    role: string
    is_active: boolean
    last_login_at: string | null
}

const authStore = useAuthStore()
const users = ref<User[]>([])
const loading = ref(false)
const showDeleteModal = ref(false)
const userToDelete = ref<User | null>(null)
const deleting = ref(false)
const showEditModal = ref(false)
const editingUser = ref<User | null>(null)
const saving = ref(false)

const activeUsersCount = computed(() => users.value.filter(u => u.is_active).length)
const adminCount = computed(() => users.value.filter(u => u.role === 'admin').length)

function getRoleBadgeClass(role: string): string {
    switch (role) {
        case 'admin': return 'badge bg-danger'
        case 'ml_engineer': return 'badge bg-primary'
        case 'analyst': return 'badge bg-info'
        default: return 'badge bg-secondary'
    }
}

function formatDate(dateStr: string | null): string {
    if (!dateStr) return '-'
    const date = new Date(dateStr)
    return date.toLocaleString('ru-RU')
}

async function loadUsers() {
    loading.value = true
    try {
        const response = await api.get('/auth/users')
        users.value = response.data
    } catch (error) {
        console.error('Failed to load users:', error)
    } finally {
        loading.value = false
    }
}

async function toggleUserStatus(user: User) {
    const action = user.is_active ? 'block' : 'unblock'
    try {
        await api.post(`/auth/users/${user.id}/${action}`)
        user.is_active = !user.is_active
    } catch (error) {
        console.error(`Failed to ${action} user:`, error)
    }
}

function deleteUser(user: User) {
    userToDelete.value = user
    showDeleteModal.value = true
}

async function confirmDelete() {
    if (!userToDelete.value) return  // ← уже есть, но TS не понимает

    deleting.value = true
    try {
        await api.delete(`/auth/users/${userToDelete.value.id}`)
        // Добавляем проверку перед фильтрацией
        if (userToDelete.value) {
            users.value = users.value.filter(u => u.id !== userToDelete.value!.id)
        }
        showDeleteModal.value = false
        userToDelete.value = null
    } catch (error) {
        console.error('Failed to delete user:', error)
    } finally {
        deleting.value = false
    }
}


async function editUser(user: User) {
  editingUser.value = { ...user }
  showEditModal.value = true
}

async function saveUser() {
  if (!editingUser.value) return
  
  saving.value = true
  try {
    await api.put(`/auth/users/${editingUser.value.id}`, {
      email: editingUser.value.email,
      full_name: editingUser.value.full_name,
      role: editingUser.value.role
    })
    
    // Обновляем локальный список
    const index = users.value.findIndex(u => u.id === editingUser.value!.id)
    if (index !== -1) {
      users.value[index] = { ...users.value[index], ...editingUser.value }
    }
    
    showEditModal.value = false
    editingUser.value = null
  } catch (error) {
    console.error('Failed to update user:', error)
    alert('Failed to update user')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
    loadUsers()
})
</script>

<style scoped>
.modal-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.4);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1050;
}

.modal-box {
    background: white;
    padding: 24px;
    border-radius: 8px;
    width: 400px;
    max-width: 90vw;
}

.badge {
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
}

.form-check-input {
    cursor: pointer;
}

.btn-group .btn {
    padding: 4px 8px;
    font-size: 12px;
    line-height: 1.5;
}

.btn-group .btn i {
    font-size: 14px;
}

.btn-sm {
    padding: 4px 8px !important;
    font-size: 12px !important;
}
</style>