<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useWorkoutStore } from '../store/workout'

const store = useWorkoutStore()
const router = useRouter()

const workouts = computed(() => store.workouts)

// General stats
const totalSessions = computed(() => workouts.value.length)
const totalDays = computed(() => {
  if (workouts.value.length === 0) return 0
  const dates = workouts.value.map(w => new Date(w.date).toDateString())
  return new Set(dates).size
})

// Stats per modality
const modalityStats = computed(() => {
  const stats = {}
  store.modalities.forEach(m => {
    const modWorkouts = workouts.value.filter(w => w.modalityId === m.id)
    stats[m.id] = {
      count: modWorkouts.length,
      name: m.name,
      color: m.color,
      icon: m.icon
    }
  })
  return stats
})

const maxModCount = computed(() => {
  const counts = Object.values(modalityStats.value).map(s => s.count)
  return Math.max(...counts, 1)
})

// Weekly activity (Last 7 days)
const weeklyActivity = computed(() => {
  const days = []
  for (let i = 6; i >= 0; i--) {
    const d = new Date()
    d.setDate(d.getDate() - i)
    const dateStr = d.toDateString()
    const count = workouts.value.filter(w => new Date(w.date).toDateString() === dateStr).length
    days.push({
      label: d.toLocaleDateString('pt-BR', { weekday: 'short' }),
      count
    })
  }
  return days
})

const maxDayCount = computed(() => {
  const counts = weeklyActivity.value.map(d => d.count)
  return Math.max(...counts, 1)
})

const goBack = () => router.push('/')
</script>

<template>
  <div class="container animate-fade-in">
    <button @click="goBack" class="btn-back">← Voltar</button>

    <header class="section-header">
      <h1>Minhas Estatísticas</h1>
      <p class="subtitle">Acompanhe seu progresso e consistência</p>
    </header>

    <div v-if="workouts.length === 0" class="empty-state glass-panel">
      <div class="empty-icon">📈</div>
      <h3>Sem dados suficientes</h3>
      <p>Registre alguns treinos para ver suas estatísticas detalhadas.</p>
      <button class="btn-primary" @click="goBack" style="margin-top: 1rem;">Começar Treino</button>
    </div>

    <template v-else>
      <!-- Quick Stats -->
      <div class="stats-overview">
        <div class="stat-card glass-panel">
          <span class="stat-label">Total de Sessões</span>
          <span class="stat-value text-gradient">{{ totalSessions }}</span>
        </div>
        <div class="stat-card glass-panel">
          <span class="stat-label">Dias Ativos</span>
          <span class="stat-value text-gradient">{{ totalDays }}</span>
        </div>
        <div class="stat-card glass-panel">
          <span class="stat-label">Média Semanal</span>
          <span class="stat-value text-gradient">{{ (totalSessions / 4).toFixed(1) }}</span>
        </div>
      </div>

      <!-- Activity Charts -->
      <div class="charts-grid">
        <!-- Weekly Chart -->
        <div class="chart-container glass-panel">
          <h3>Atividade Semanal</h3>
          <div class="bar-chart">
            <div v-for="day in weeklyActivity" :key="day.label" class="bar-group">
              <div class="bar-wrapper">
                <div 
                  class="bar" 
                  :style="{ height: `${(day.count / maxDayCount) * 100}%` }"
                  :class="{ 'has-data': day.count > 0 }"
                >
                  <span class="bar-tooltip" v-if="day.count > 0">{{ day.count }}</span>
                </div>
              </div>
              <span class="bar-label">{{ day.label }}</span>
            </div>
          </div>
        </div>

        <!-- Modality Distribution -->
        <div class="chart-container glass-panel">
          <h3>Distribuição por Modalidade</h3>
          <div class="modality-list">
            <div v-for="stat in modalityStats" :key="stat.name" class="modality-stat-row">
              <div class="mod-info">
                <span class="mod-icon">{{ stat.icon }}</span>
                <span class="mod-name">{{ stat.name }}</span>
              </div>
              <div class="progress-container">
                <div class="progress-bg">
                  <div 
                    class="progress-fill" 
                    :style="{ width: `${(stat.count / totalSessions) * 100}%`, background: stat.color }"
                  ></div>
                </div>
                <span class="mod-count">{{ stat.count }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.btn-back {
  color: var(--text-tertiary);
  margin-bottom: 1rem;
  font-size: 0.9rem;
  font-weight: 500;
}

.section-header {
  margin-bottom: 2.5rem;
}

.subtitle {
  color: var(--text-secondary);
}

.text-gradient {
  background: var(--accent-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.stats-overview {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem;
  margin-bottom: 2.5rem;
}

.stat-card {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.stat-label {
  font-size: 0.85rem;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 600;
}

.stat-value {
  font-size: 2.5rem;
  font-weight: 800;
  font-family: var(--font-heading);
}

.charts-grid {
  display: grid;
  grid-template-columns: 1.5fr 1fr;
  gap: 1.5rem;
}

.chart-container {
  padding: 1.5rem;
}

.chart-container h3 {
  font-size: 1.1rem;
  margin-bottom: 2rem;
  color: var(--text-primary);
}

/* Bar Chart */
.bar-chart {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  height: 200px;
  padding-top: 2rem;
}

.bar-group {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  flex: 1;
}

.bar-wrapper {
  flex: 1;
  width: 30px;
  background: rgba(255,255,255,0.03);
  border-radius: var(--radius-full);
  display: flex;
  align-items: flex-end;
  position: relative;
}

.bar {
  width: 100%;
  background: var(--text-tertiary);
  border-radius: var(--radius-full);
  transition: all 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
  min-height: 4px;
}

.bar.has-data {
  background: var(--accent-gradient);
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);
}

.bar-tooltip {
  position: absolute;
  top: -2.5rem;
  left: 50%;
  transform: translateX(-50%);
  background: var(--bg-surface-elevated);
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: bold;
  border: 1px solid var(--border-light);
}

.bar-label {
  font-size: 0.75rem;
  color: var(--text-tertiary);
  text-transform: uppercase;
}

/* Modality List */
.modality-list {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.modality-stat-row {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.mod-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
}

.progress-container {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.progress-bg {
  flex: 1;
  height: 8px;
  background: rgba(255,255,255,0.05);
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.8s ease-out;
}

.mod-count {
  font-weight: 700;
  font-size: 0.9rem;
  min-width: 20px;
  text-align: right;
}

.empty-state {
  padding: 4rem 2rem;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.empty-icon {
  font-size: 3rem;
  opacity: 0.5;
}

@media (max-width: 900px) {
  .charts-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 600px) {
  .stats-overview {
    grid-template-columns: 1fr;
  }
}
</style>
