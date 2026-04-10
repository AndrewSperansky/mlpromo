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
          и бизнес-аналитика на основе машинного обучения
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
      </div>
    </div>

    <!-- Features Section -->
    <div class="features-section">
      <div class="container">
        <h2 class="text-center mb-5">Ключевые возможности</h2>
        <div class="row g-4">
          <div class="col-md-4">
            <div class="feature-card text-center">
              <div class="feature-icon">
                <i class="bi bi-cpu"></i>
              </div>
              <h4>ML Прогнозы</h4>
              <p>Прогнозирование прироста продаж с помощью CatBoost, доверительные интервалы и SHAP объяснения</p>
            </div>
          </div>
          <div class="col-md-4">
            <div class="feature-card text-center">
              <div class="feature-icon">
                <i class="bi bi-bar-chart-steps"></i>
              </div>
              <h4>Статистическая валидация</h4>
              <p>Доверительные интервалы, p-value и тестирование статистической значимости моделей</p>
            </div>
          </div>
          <div class="col-md-4">
            <div class="feature-card text-center">
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
              <div class="stat-number">1174</div>
              <div class="stat-label">Строк для обучения</div>
            </div>
          </div>
          <div class="col-md-3">
            <div class="stat-card">
              <div class="stat-number">95%</div>
              <div class="stat-label">Доверительный интервал</div>
            </div>
          </div>
          <div class="col-md-3">
            <div class="stat-card">
              <div class="stat-number">10+</div>
              <div class="stat-label">Версий моделей</div>
            </div>
          </div>
          <div class="col-md-3">
            <div class="stat-card">
              <div class="stat-number">24/7</div>
              <div class="stat-label">Мониторинг</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <footer class="footer">
      <div class="container text-center">
        <p>&copy; 2026 Promo ML. Все права защищены.</p>
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