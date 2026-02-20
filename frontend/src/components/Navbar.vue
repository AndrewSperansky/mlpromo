<template>
  <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
    <div class="container-fluid">
      <span class="navbar-brand fw-bold">
        Promo ML Admin
      </span>

      <button
        class="navbar-toggler"
        type="button"
        data-bs-toggle="collapse"
        data-bs-target="#navbarNav"
      >
        <span class="navbar-toggler-icon"></span>
      </button>

      <div class="collapse navbar-collapse" id="navbarNav">
        <ul class="navbar-nav ms-auto">

          <li class="nav-item">
            <router-link class="nav-link" to="/">
              Dashboard
            </router-link>
          </li>

          <li class="nav-item">
            <router-link class="nav-link" to="/models">
              Models
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

        </ul>
      </div>
    </div>
  </nav>
</template>

<script setup lang="ts">
</script>
