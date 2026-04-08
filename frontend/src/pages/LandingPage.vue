<!-- frontend/src/pages/LandingPage.vue -->
<template>
  <div class="landing-container">
    <!-- Hero Section -->
    <div class="hero-section text-center">
      <div class="container">
        <div class="hero-icon mb-4">
          <i class="bi bi-graph-up"></i>
        </div>
        <h1 class="display-3 fw-bold mb-3">Promo ML</h1>
        <p class="lead mb-4">
          Intelligent promotion effectiveness prediction platform
        </p>
        <p class="mb-4">
          Machine learning models for sales uplift prediction,<br>
          promotion effectiveness analysis, and business intelligence
        </p>
        <button class="btn btn-primary btn-lg" @click="goToLogin">
          <i class="bi bi-box-arrow-in-right me-2"></i>
          Login to Dashboard
        </button>
      </div>
    </div>

    <!-- Features Section -->
    <div class="features-section">
      <div class="container">
        <h2 class="text-center mb-5">Key Features</h2>
        <div class="row g-4">
          <div class="col-md-4">
            <div class="feature-card text-center">
              <div class="feature-icon">
                <i class="bi bi-cpu"></i>
              </div>
              <h4>ML Predictions</h4>
              <p>Sales uplift prediction with CatBoost models, confidence intervals, and SHAP explanations</p>
            </div>
          </div>
          <div class="col-md-4">
            <div class="feature-card text-center">
              <div class="feature-icon">
                <i class="bi bi-bar-chart-steps"></i>
              </div>
              <h4>Statistical Validation</h4>
              <p>Confidence intervals, p-values, and statistical significance testing for model comparison</p>
            </div>
          </div>
          <div class="col-md-4">
            <div class="feature-card text-center">
              <div class="feature-icon">
                <i class="bi bi-shield-check"></i>
              </div>
              <h4>Human-in-the-Loop</h4>
              <p>Manual approval workflow for model promotion with metric comparison</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Stats Section -->
    <div class="stats-section">
      <div class="container">
        <div class="row text-center">
          <div class="col-md-3">
            <div class="stat-card">
              <div class="stat-number">1174</div>
              <div class="stat-label">Training Rows</div>
            </div>
          </div>
          <div class="col-md-3">
            <div class="stat-card">
              <div class="stat-number">95%</div>
              <div class="stat-label">Confidence Interval</div>
            </div>
          </div>
          <div class="col-md-3">
            <div class="stat-card">
              <div class="stat-number">10+</div>
              <div class="stat-label">Model Versions</div>
            </div>
          </div>
          <div class="col-md-3">
            <div class="stat-card">
              <div class="stat-number">24/7</div>
              <div class="stat-label">Monitoring</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <footer class="footer">
      <div class="container text-center">
        <p>&copy; 2026 Promo ML. All rights reserved.</p>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const goToLogin = () => {
  router.push('/login')
}
</script>

<style scoped>
.landing-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.hero-section {
  padding: 100px 20px 80px;
  color: white;
}

.hero-icon {
  font-size: 80px;
}

.hero-icon i {
  background: rgba(255,255,255,0.2);
  padding: 30px;
  border-radius: 50%;
}

.hero-section h1 {
  font-size: 56px;
  font-weight: 700;
}

.hero-section .lead {
  font-size: 20px;
  opacity: 0.9;
}

.btn-primary {
  background: #ff6b6b;
  border: none;
  padding: 12px 40px;
  font-size: 18px;
  transition: transform 0.3s;
}

.btn-primary:hover {
  background: #ff5252;
  transform: translateY(-2px);
}

.features-section {
  background: white;
  padding: 80px 20px;
}

.feature-card {
  padding: 30px;
  border-radius: 12px;
  transition: all 0.3s;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

.feature-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 20px rgba(0,0,0,0.15);
}

.feature-icon {
  font-size: 48px;
  color: #667eea;
  margin-bottom: 20px;
}

.stats-section {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 60px 20px;
  color: white;
}

.stat-card {
  padding: 20px;
}

.stat-number {
  font-size: 48px;
  font-weight: 700;
  margin-bottom: 10px;
}

.stat-label {
  font-size: 16px;
  opacity: 0.9;
}

.footer {
  background: #2d3748;
  color: #a0aec0;
  padding: 30px 20px;
}

@media (max-width: 768px) {
  .hero-section h1 {
    font-size: 36px;
  }
  
  .hero-section {
    padding: 60px 20px;
  }
  
  .feature-card {
    margin-bottom: 20px;
  }
}
</style>