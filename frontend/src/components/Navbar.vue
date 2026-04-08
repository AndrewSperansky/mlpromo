<!-- frontend\src\components\Navbar.vue -->

<template>
  <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
    <div class="container-fluid">
      <span class="navbar-brand fw-bold">
        Promo ML | User: {{ authStore.user?.username || 'Guest' }}
      </span>

      <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
        <span class="navbar-toggler-icon"></span>
      </button>

      <div class="collapse navbar-collapse" id="navbarNav">
        <ul class="navbar-nav ms-auto">

          <li class="nav-item">
            <router-link class="nav-link" to="/dashboard">
              Dashboard
            </router-link>
          </li>

          <li class="nav-item">
            <router-link class="nav-link" to="/models">
              Models
            </router-link>
          </li>

          <li class="nav-item">
            <router-link class="nav-link" to="/datasets">
              Datasets
            </router-link>
          </li>

          <li class="nav-item">
            <router-link class="nav-link" to="/runtime">
              Runtime
            </router-link>
          </li>

          <li class="nav-item">
            <router-link class="nav-link" to="/predict">
              Predict
            </router-link>
          </li>

          <li class="nav-item">
            <router-link class="nav-link" to="/audit">
              Audit
            </router-link>
          </li>

          <li class="nav-item">
            <a :href="grafanaUrl" target="_blank" class="nav-link">
              Grafana
            </a>
          </li>

          <li v-if="authStore.isAdmin" class="nav-item">
            <router-link class="nav-link" to="/users">Users</router-link>
          </li>

          <li v-if="authStore.isAdmin" class="nav-item">
            <router-link class="nav-link" to="/activity">Activity</router-link>
          </li>

        </ul>

        <ul class="navbar-nav">
          <li class="nav-item dropdown">
            <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown">
              <i class="bi bi-person-circle me-1"></i>
              {{ authStore.user?.username || 'User' }}
            </a>
            <ul class="dropdown-menu dropdown-menu-end">
              <li><span class="dropdown-item-text text-muted">Role: {{ authStore.user?.role }}</span></li>
              <li>
                <hr class="dropdown-divider">
              </li>
              <li><a class="dropdown-item text-danger" href="#" @click="logout">Logout</a></li>
            </ul>
          </li>
        </ul>

      </div>
    </div>
  </nav>
</template>


<script setup lang="ts">

import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const grafanaUrl = import.meta.env.VITE_GRAFANA_URL || 'http://192.168.18.73:3000'

async function logout() {
  await authStore.logout()
  router.push('/login')
}

</script>
