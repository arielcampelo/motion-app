<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useWorkoutStore } from '../store/workout'

const route = useRoute()
const router = useRouter()
const store = useWorkoutStore()

const modalityId = computed(() => route.params.id)
const modality = computed(() => store.modalities.find(m => m.id === modalityId.value))

const workouts = computed(() => 
  store.workouts.filter(w => w.modalityId === modalityId.value)
)

const goBack = () => router.push('/')
const handlePrimaryAction = () => {
  const planners = ['malabarismo', 'calistenia', 'escalada', 'natacao']
  if (planners.includes(modalityId.value)) {
    router.push(`/modality/${modalityId.value}/planner`)
  } else {
    router.push(`/modality/${modalityId.value}/new`)
  }
}
</script>

<template>
  <div v-if="modality" class="container animate-fade-in">
    <button @click="goBack" class="btn-back">← Voltar para Modalidades</button>
    
    <header class="modality-header" :style="{ '--mod-color': modality.color }">
      <div class="mod-title-area">
        <span class="mod-icon">{{ modality.icon }}</span>
        <div>
          <h1>{{ modality.name }}</h1>
          <p class="subtitle">{{ modality.desc }}</p>
        </div>
      </div>
      <button class="btn-primary custom-bg" @click="handlePrimaryAction">
        {{ ['malabarismo', 'calistenia', 'escalada', 'natacao'].includes(modalityId) ? '📅 Planejar Sessão' : '+ Registrar Treino' }}
      </button>
    </header>

    <section class="workouts-history">
      <h2>Histórico Recente</h2>
      
      <div v-if="workouts.length === 0" class="empty-state glass-panel">
        <div class="empty-icon">📝</div>
        <h3>Nenhum treino registrado</h3>
        <p>Você ainda não registrou nenhum treino de {{ modality.name }}.</p>
      </div>
      
      <div v-else class="workout-list">
        <div v-for="workout in workouts" :key="workout.id" class="history-card glass-panel">
          <div class="card-header">
            <h3>{{ workout.name }}</h3>
            <span class="date">{{ new Date(workout.date).toLocaleDateString() }}</span>
          </div>
          <div class="card-body">
            <!-- Render custom metrics based on modality -->
            <div v-if="modalityId === 'calistenia'" class="metrics">
              <span class="tag">{{ workout.details.totalSets }} séries</span>
              <span class="tag">{{ workout.details.totalReps }} reps</span>
            </div>
            <div v-else-if="modalityId === 'malabarismo'" class="metrics">
              <span class="tag" v-if="workout.details.blocks">{{ workout.details.completed }}/{{ workout.details.blocks.length }} blocos</span>
              <span class="tag" v-else>{{ workout.details.duration }} min</span>
            </div>
            <div v-else-if="modalityId === 'escalada'" class="metrics">
              <span class="tag">{{ workout.details.tops }} tops</span>
              <span class="tag">Max: V{{ workout.details.maxGrade }}</span>
            </div>
            <div v-else-if="modalityId === 'natacao'" class="metrics">
              <span class="tag">{{ workout.details.distance }}m</span>
              <span class="tag">{{ workout.details.time }} min</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.btn-back {
  color: var(--text-tertiary);
  margin-bottom: 1rem;
  font-size: 0.9rem;
  font-weight: 500;
}

.btn-back:hover {
  color: var(--text-primary);
}

.modality-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 3rem;
  padding-bottom: 2rem;
  border-bottom: 1px solid var(--border-light);
  gap: 1rem;
  flex-wrap: wrap;
}

.mod-title-area {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.mod-icon {
  font-size: 4rem;
  filter: drop-shadow(0 0 20px rgba(255,255,255,0.1));
}

.custom-bg {
  background: var(--mod-color);
  box-shadow: 0 4px 15px var(--mod-color);
  opacity: 0.9;
}
.custom-bg:hover {
  opacity: 1;
  box-shadow: 0 6px 20px var(--mod-color);
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

.empty-state p {
  color: var(--text-tertiary);
}

.workout-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.history-card {
  padding: 1.5rem;
}

.card-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.date {
  color: var(--text-tertiary);
  font-size: 0.9rem;
}

.metrics {
  display: flex;
  gap: 1rem;
}

.tag {
  background: rgba(255,255,255,0.05);
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--text-secondary);
}
</style>
