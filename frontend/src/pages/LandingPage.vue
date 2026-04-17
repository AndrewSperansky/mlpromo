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
          Интеллектуальная платформа для прогнозирования эффективности промо-акций
        </p>
        <p class="mb-4">
          Прогнозирование прироста продаж, анализ эффективности промо-акций<br>
          и бизнес-аналитика на основе машинного обучения<br>

        </p>
        <div class="d-flex gap-3 justify-content-center">
          <button class="btn btn-primary btn-lg" @click="goToLogin">
            <i class="bi bi-box-arrow-in-right me-2"></i>
            Войти
          </button>
          <button class="btn btn-outline-light btn-lg" @click="goToRegister">
            <i class="bi bi-person-plus me-2"></i>
            Зарегистрироваться
          </button>
        </div>
        <div class="mt-4 text-center">
          <a href="/docs" target="_blank" class="text-white text-decoration-none opacity-75">
            <i class="bi bi-file-text me-1"></i>
            API Docs (Swagger UI)
          </a>
        </div>
      </div>
    </div>

    <!-- Features Section -->
    <div class="features-section">
      <div class="container">
        <h2 class="text-center mb-5">Ключевые возможности</h2>
        <div class="row g-4">
          <div class="col-md-4">
            <div class="feature-card text-center  h-100">
              <div class="feature-icon">
                <i class="bi bi-cpu"></i>
              </div>
              <h4>ML Прогнозы</h4>
              <p>Прогнозирование прироста продаж с помощью CatBoost, доверительные интервалы и SHAP объяснения</p>
            </div>
          </div>
          <div class="col-md-4">
            <div class="feature-card text-center  h-100">
              <div class="feature-icon">
                <i class="bi bi-bar-chart-steps"></i>
              </div>
              <h4>Статистическая валидация</h4>
              <p>Доверительные интервалы, p-value и тестирование статистической значимости моделей</p>
            </div>
          </div>
          <div class="col-md-4">
            <div class="feature-card text-center  h-100">
              <div class="feature-icon">
                <i class="bi bi-shield-check"></i>
              </div>
              <h4>Human-in-the-Loop</h4>
              <p>Ручное утверждение моделей с визуальным сравнением метрик перед активацией</p>
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
              <div class="stat-number">{{ stats.total_trainings || '???' }}</div>
              <div class="stat-label">Обучений</div>
            </div>
          </div>
          <div class="col-md-3">
            <div class="stat-card">
              <div class="stat-number">{{ stats.total_predictions }}</div>
              <div class="stat-label">Предсказаний</div>
            </div>
          </div>
          <div class="col-md-3">
            <div class="stat-card">
              <div class="stat-number">{{ stats.total_rows }}</div>
              <div class="stat-label">Строк в датасете</div>
            </div>
          </div>
          <div class="col-md-3">
            <div class="stat-card">
              <div class="stat-number">{{ stats.total_models }}</div>
              <div class="stat-label">Версий моделей</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <footer class="footer">
      <div class="container text-center">
        <p>&copy; 2026 АПХ Мираторг. Все права защищены.</p>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()

const stats = ref({
  total_models: 0,
  total_predictions: 0,
  total_trainings: 0,
  total_rows: 0
})

async function loadStats() {
  try {
    console.log('🟢 Loading stats...')
    const response = await axios.get('/api/v1/system/landing-stats')
    console.log('🟢 Stats response:', response.data)
    stats.value = response.data
  } catch (error) {
    console.error('🔴 Failed to load landing stats:', error)
  }
}

onMounted(() => {
  console.log('🟢 LandingPage mounted')
  loadStats()
})

const goToLogin = () => {
  router.push('/login')
}

const goToRegister = () => {
  router.push('/register')
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
  background: rgba(255, 255, 255, 0.2);
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

.btn-outline-light {
  padding: 12px 40px;
  font-size: 18px;
  transition: transform 0.3s;
}

.btn-outline-light:hover {
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
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.feature-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
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