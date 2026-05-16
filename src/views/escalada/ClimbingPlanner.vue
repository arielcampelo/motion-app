<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useWorkoutStore } from '../../store/workout'

const router = useRouter()
const route = useRoute()
const store = useWorkoutStore()

const modalityId = computed(() => route.params.id)
const modality = computed(() => store.modalities.find(m => m.id === 'escalada'))

const sessionName = ref(`Sessão de Escalada`)
const exercises = ref([
  { id: Date.now(), type: 'Boulder', grade: 'V1', tops: 1, attempts: 1 }
])

const availableTypes = computed(() => store.exercises.escalada || ['Boulder', 'Top Rope', 'Guiada'])

const addExercise = () => {
  exercises.value.push({
    id: Date.now(),
    type: 'Boulder',
    grade: 'V1',
    tops: 1,
    attempts: 1
  })
}

const removeExercise = (index) => {
  exercises.value.splice(index, 1)
}

const startSession = () => {
  const sessionId = Date.now().toString()
  store.activeSession = {
    id: sessionId,
    name: sessionName.value,
    modalityId: 'escalada',
    exercises: [...exercises.value]
  }
  router.push(`/modality/escalada/session/${sessionId}`)
}

const goBack = () => router.push(`/modality/escalada`)
</script>

<template>
  <div class="container animate-fade-in">
    <button @click="goBack" class="btn-back">← Voltar</button>

    <header class="section-header">
      <h2>Planejar: {{ modality?.name }}</h2>
      <button class="btn-primary custom-btn" @click="startSession">Iniciar Sessão</button>
    </header>

    <div class="form-container glass-panel">
      <div class="form-group">
        <label>Nome do Treino</label>
        <input v-model="sessionName" type="text" class="input-field" />
      </div>

      <div class="divider"></div>
      <h3>Vias / Boulders Planejados</h3>
      
      <div class="exercises-list">
        <div v-for="(ex, index) in exercises" :key="ex.id" class="exercise-row">
          <div class="form-group">
            <label>Tipo</label>
            <select v-model="ex.type" class="input-field select-field">
              <option v-for="type in availableTypes" :key="type" :value="type">{{ type }}</option>
            </select>
          </div>

          <div class="form-group">
            <label>Grau</label>
            <input v-model="ex.grade" type="text" class="input-field" placeholder="Ex: V3 ou 6a" />
          </div>
          
          <div class="form-group">
            <label>Tops Alvo</label>
            <input v-model="ex.tops" type="number" min="1" class="input-field" />
          </div>

          <div class="form-group">
            <label>Tentativas Max</label>
            <input v-model="ex.attempts" type="number" min="1" class="input-field" />
          </div>

          <button @click="removeExercise(index)" class="btn-icon delete-btn">×</button>
        </div>
      </div>

      <button @click="addExercise" class="btn-outline">+ Adicionar Objetivo</button>
    </div>
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

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.custom-btn {
  background: #f59e0b;
  box-shadow: 0 4px 15px rgba(245, 158, 11, 0.4);
}

.form-container {
  padding: 2rem;
}

.form-group {
  margin-bottom: 0;
  display: flex;
  flex-direction: column;
}

label {
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.input-field {
  width: 100%;
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  padding: 10px 14px;
  color: var(--text-primary);
  font-family: var(--font-body);
  font-size: 0.95rem;
}
.input-field:focus {
  outline: none;
  border-color: #f59e0b;
}

.divider {
  height: 1px;
  background: var(--border-light);
  margin: 2rem 0;
}

h3 {
  margin-bottom: 1.5rem;
  font-size: 1.2rem;
}

.exercises-list {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}

.exercise-row {
  display: grid;
  grid-template-columns: 1fr 1fr 0.8fr 0.8fr 40px;
  gap: 1rem;
  align-items: flex-end;
  background: rgba(255,255,255,0.02);
  padding: 1.5rem;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-subtle);
}

@media (max-width: 768px) {
  .exercise-row {
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
  }
}

.btn-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  color: var(--text-tertiary);
  border-radius: var(--radius-sm);
  margin-bottom: 2px;
}
.btn-icon:hover {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

.btn-outline {
  width: 100%;
  padding: 12px;
  border: 1px dashed var(--border-light);
  border-radius: var(--radius-sm);
  color: #f59e0b;
  font-weight: 500;
  transition: all var(--transition-fast);
}
.btn-outline:hover {
  background: rgba(245, 158, 11, 0.05);
  border-style: solid;
}
</style>
