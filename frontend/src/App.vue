<!-- frontend/src/App.vue -->

<template>
  <div>
    <Navbar v-if="showNavbar" />
    <div :class="showNavbar ? 'container mt-4' : ''">
      <router-view />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from './stores/auth'
import Navbar from './components/Navbar.vue'

const route = useRoute()
const authStore = useAuthStore()

const showNavbar = computed(() => {
  return authStore.isAuthenticated && route.meta.requiresAuth === true
})
</script>