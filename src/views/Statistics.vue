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

// Current Streak calculation
const currentStreak = computed(() => {
  if (workouts.value.length === 0) return 0
  
  const dates = Array.from(new Set(workouts.value.map(w => new Date(w.date).toDateString())))
    .map(d => new Date(d))
    .sort((a, b) => b - a)

  let streak = 0
  let today = new Date()
  today.setHours(0,0,0,0)
  
  let checkDate = new Date(today)
  
  // Se o último treino não foi hoje nem ontem, a streak quebrou
  const lastWorkout = dates[0]
  lastWorkout.setHours(0,0,0,0)
  const diff = (today - lastWorkout) / (1000 * 60 * 60 * 24)
  
  if (diff > 1) return 0

  for (const date of dates) {
    date.setHours(0,0,0,0)
    if (date.getTime() === checkDate.getTime()) {
      streak++
      checkDate.setDate(checkDate.getDate() - 1)
    } else if (date.getTime() < checkDate.getTime()) {
      break
    }
  }
  return streak
})

// Consistency Index (Active days in last 30 days)
const consistencyIndex = computed(() => {
  if (workouts.value.length === 0) return 0
  const thirtyDaysAgo = new Date()
  thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30)
  
  const activeDaysLastMonth = new Set(
    workouts.value
      .filter(w => new Date(w.date) >= thirtyDaysAgo)
      .map(w => new Date(w.date).toDateString())
  ).size
  
  return Math.round((activeDaysLastMonth / 30) * 100)
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

const favoriteModality = computed(() => {
  const sorted = Object.values(modalityStats.value).sort((a, b) => b.count - a.count)
  return sorted[0]?.count > 0 ? sorted[0] : null
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
      count,
      fullDate: d.toLocaleDateString('pt-BR', { day: 'numeric', month: 'short' })
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
    <button @click="goBack" class="btn-back">← Voltar para o início</button>

    <header class="section-header">
      <div class="header-content">
        <h1>Dashboard de Performance</h1>
        <p class="subtitle">Onde a matemática encontra o movimento</p>
      </div>
      <div v-if="currentStreak > 0" class="streak-badge glass-panel animate-bounce-in">
        <span class="streak-fire">🔥</span>
        <div class="streak-info">
          <span class="streak-count">{{ currentStreak }}</span>
          <span class="streak-label">DIAS SEGUIDOS</span>
        </div>
      </div>
    </header>

    <div v-if="workouts.length === 0" class="empty-state glass-panel">
      <div class="empty-icon">📈</div>
      <h3>Nenhum movimento registrado</h3>
      <p>A matemática precisa de dados para gerar insights. Comece seu primeiro treino hoje!</p>
      <button class="btn-primary" @click="goBack" style="margin-top: 1.5rem;">Explorar Modalidades</button>
    </div>

    <template v-else>
      <!-- Quick Stats -->
      <div class="stats-overview">
        <div class="stat-card glass-panel">
          <div class="stat-header">
            <span class="stat-label">Total de Sessões</span>
            <span class="stat-icon-mini">📊</span>
          </div>
          <span class="stat-value text-gradient">{{ totalSessions }}</span>
        </div>
        <div class="stat-card glass-panel highlight">
          <div class="stat-header">
            <span class="stat-label">Índice de Consistência</span>
            <span class="stat-icon-mini">🎯</span>
          </div>
          <div class="stat-value-group">
            <span class="stat-value text-gradient">{{ consistencyIndex }}%</span>
            <span class="stat-sublabel">nos últimos 30 dias</span>
          </div>
        </div>
        <div class="stat-card glass-panel">
          <div class="stat-header">
            <span class="stat-label">Modalidade Favorita</span>
            <span class="stat-icon-mini">⭐</span>
          </div>
          <div v-if="favoriteModality" class="fav-mod">
            <span class="stat-value small">{{ favoriteModality.name }}</span>
            <span class="stat-icon">{{ favoriteModality.icon }}</span>
          </div>
        </div>
      </div>

      <!-- Activity Charts -->
      <div class="charts-grid">
        <!-- Weekly Chart -->
        <div class="chart-container glass-panel">
          <div class="chart-header">
            <h3>Atividade Semanal</h3>
            <span class="chart-legend">Volume de treinos / dia</span>
          </div>
          <div class="bar-chart">
            <div v-for="day in weeklyActivity" :key="day.label" class="bar-group">
              <div class="bar-wrapper">
                <div 
                  class="bar" 
                  :style="{ height: `${(day.count / maxDayCount) * 100}%` }"
                  :class="{ 'has-data': day.count > 0 }"
                >
                  <div class="bar-tooltip" v-if="day.count > 0">
                    <span class="tip-val">{{ day.count }} treinos</span>
                    <span class="tip-date">{{ day.fullDate }}</span>
                  </div>
                </div>
              </div>
              <span class="bar-label">{{ day.label }}</span>
            </div>
          </div>
        </div>

        <!-- Modality Distribution -->
        <div class="chart-container glass-panel">
          <div class="chart-header">
            <h3>Distribuição</h3>
            <span class="chart-legend">Treinos por categoria</span>
          </div>
          <div class="modality-list">
            <div v-for="stat in modalityStats" :key="stat.name" class="modality-stat-row">
              <div class="mod-info">
                <span class="mod-icon">{{ stat.icon }}</span>
                <span class="mod-name">{{ stat.name }}</span>
                <span class="mod-percentage" v-if="totalSessions > 0">
                  {{ Math.round((stat.count / totalSessions) * 100) }}%
                </span>
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

      <!-- Motivation Card -->
      <div class="motivation-banner glass-panel">
        <div class="motivation-content">
          <span class="quote-icon">"</span>
          <p class="quote-text">A persistência é o que transforma a média em maestria. Você está a apenas um treino da sua melhor versão.</p>
          <span class="quote-author">— Motion Intelligence</span>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.btn-back {
  background: none;
  border: none;
  color: var(--text-tertiary);
  margin-bottom: 1.5rem;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: color 0.3s;
  padding: 0;
}

.btn-back:hover {
  color: var(--text-primary);
}

.section-header {
  margin-bottom: 2.5rem;
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 1.5rem;
}

.subtitle {
  color: var(--text-secondary);
  font-size: 1.1rem;
}

.streak-badge {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem 1.25rem;
  background: rgba(255, 107, 0, 0.1) !important;
  border: 1px solid rgba(255, 107, 0, 0.2) !important;
}

.streak-fire {
  font-size: 2rem;
  filter: drop-shadow(0 0 8px rgba(255, 107, 0, 0.5));
}

.streak-info {
  display: flex;
  flex-direction: column;
}

.streak-count {
  font-size: 1.5rem;
  font-weight: 800;
  color: #ff6b00;
  line-height: 1;
}

.streak-label {
  font-size: 0.65rem;
  font-weight: 700;
  color: #ff6b00;
  letter-spacing: 0.1em;
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
  gap: 0.75rem;
  position: relative;
  overflow: hidden;
}

.stat-card.highlight {
  border: 1px solid rgba(139, 92, 246, 0.3);
}

.stat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-label {
  font-size: 0.75rem;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-weight: 700;
}

.stat-icon-mini {
  opacity: 0.4;
  font-size: 1.1rem;
}

.stat-value {
  font-size: 2.8rem;
  font-weight: 800;
  font-family: var(--font-heading);
  line-height: 1;
}

.stat-value.small {
  font-size: 1.5rem;
  margin-top: 0.5rem;
}

.stat-value-group {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.stat-sublabel {
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

.fav-mod {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.charts-grid {
  display: grid;
  grid-template-columns: 1.6fr 1fr;
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.chart-container {
  padding: 1.75rem;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.chart-header h3 {
  font-size: 1.1rem;
  margin: 0;
  color: var(--text-primary);
}

.chart-legend {
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

/* Bar Chart */
.bar-chart {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  height: 200px;
  padding-top: 1rem;
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
  width: 32px;
  background: rgba(255,255,255,0.02);
  border-radius: 12px;
  display: flex;
  align-items: flex-end;
  position: relative;
}

.bar {
  width: 100%;
  background: rgba(255,255,255,0.05);
  border-radius: 12px;
  transition: all 0.8s cubic-bezier(0.34, 1.56, 0.64, 1);
  min-height: 6px;
  position: relative;
}

.bar.has-data {
  background: var(--accent-gradient);
  box-shadow: 0 4px 15px rgba(139, 92, 246, 0.2);
}

.bar:hover .bar-tooltip {
  opacity: 1;
  transform: translateX(-50%) translateY(-10px);
}

.bar-tooltip {
  position: absolute;
  top: -3.5rem;
  left: 50%;
  transform: translateX(-50%) translateY(0);
  background: var(--bg-surface-elevated);
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 0.7rem;
  white-space: nowrap;
  border: 1px solid var(--border-light);
  box-shadow: 0 10px 25px rgba(0,0,0,0.3);
  opacity: 0;
  pointer-events: none;
  transition: all 0.3s;
  z-index: 10;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.tip-val {
  font-weight: 800;
  color: var(--text-primary);
}

.tip-date {
  font-size: 0.6rem;
  color: var(--text-tertiary);
}

.bar-label {
  font-size: 0.7rem;
  color: var(--text-tertiary);
  font-weight: 600;
}

/* Modality List */
.modality-list {
  display: flex;
  flex-direction: column;
  gap: 1.4rem;
}

.modality-stat-row {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.mod-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
}

.mod-name {
  font-weight: 600;
  flex: 1;
}

.mod-percentage {
  font-size: 0.7rem;
  color: var(--text-tertiary);
  font-weight: 500;
}

.progress-container {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.progress-bg {
  flex: 1;
  height: 10px;
  background: rgba(255,255,255,0.03);
  border-radius: 5px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 5px;
  transition: width 1s cubic-bezier(0.22, 1, 0.36, 1);
  box-shadow: 0 0 10px rgba(0,0,0,0.2);
}

.mod-count {
  font-weight: 800;
  font-size: 0.9rem;
  min-width: 25px;
  text-align: right;
  color: var(--text-primary);
}

/* Motivation Banner */
.motivation-banner {
  padding: 2.5rem;
  text-align: center;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.05), rgba(16, 185, 129, 0.05)) !important;
}

.motivation-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.quote-icon {
  font-size: 3rem;
  line-height: 1;
  color: var(--text-tertiary);
  opacity: 0.3;
  font-family: serif;
}

.quote-text {
  font-size: 1.1rem;
  font-style: italic;
  color: var(--text-secondary);
  max-width: 600px;
  line-height: 1.6;
}

.quote-author {
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

/* Empty State */
.empty-state {
  padding: 5rem 2rem;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.25rem;
}

.empty-icon {
  font-size: 4rem;
  opacity: 0.3;
}

.empty-state h3 {
  font-size: 1.5rem;
  margin: 0;
}

.empty-state p {
  color: var(--text-secondary);
  max-width: 300px;
}

@media (max-width: 1024px) {
  .charts-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .stats-overview {
    grid-template-columns: 1fr;
  }
  
  .section-header {
    flex-direction: column;
    align-items: flex-start;
  }
}

/* Animations */
@keyframes bounce-in {
  0% { transform: scale(0.8); opacity: 0; }
  70% { transform: scale(1.05); }
  100% { transform: scale(1); opacity: 1; }
}

.animate-bounce-in {
  animation: bounce-in 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
}
</style>

