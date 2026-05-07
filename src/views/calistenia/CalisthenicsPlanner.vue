<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useWorkoutStore } from '../../store/workout'

const router = useRouter()
const route = useRoute()
const store = useWorkoutStore()

const modalityId = computed(() => route.params.id)
const modalityName = computed(() => store.modalities.find(m => m.id === modalityId.value)?.name || 'Calistenia')

const sessionName = ref(`Sessão de ${modalityName.value}`)
const exercises = ref([
  { id: Date.now(), area: 'superior', name: 'Flexão', customName: '', sets: 3, reps: 10, weight: 0 }
])

const availableTricks = computed(() => store.exercises.calistenia || { superior: [], core: [], inferior: [] })

const addExercise = () => {
  exercises.value.push({
    id: Date.now(),
    area: 'superior',
    name: 'Flexão',
    customName: '',
    sets: 3,
    reps: 10,
    weight: 0
  })
}

const removeExercise = (index) => {
  exercises.value.splice(index, 1)
}

const startSession = () => {
  const sessionId = Date.now().toString()
  
  const finalExercises = exercises.value.map(ex => ({
    ...ex,
    name: ex.name === 'outro' ? ex.customName || 'Exercício Livre' : ex.name
  }))

  store.activeSession = {
    id: sessionId,
    name: sessionName.value,
    modalityId: 'calistenia',
    exercises: finalExercises
  }
  router.push(`/modality/calistenia/session/${sessionId}`)
}

const goBack = () => router.push(`/modality/calistenia`)
const saveAsTemplate = () => {
  store.saveTemplate({
    name: sessionName.value,
    modalityId: 'calistenia',
    exercises: JSON.parse(JSON.stringify(exercises.value))
  })
  alert('Sessão salva com sucesso para uso futuro!')
}

const loadTemplate = (templateId) => {
  const tpl = store.savedTemplates.find(t => t.id === templateId)
  if (tpl) {
    sessionName.value = tpl.name
    exercises.value = JSON.parse(JSON.stringify(tpl.exercises))
  }
}

const myTemplates = computed(() => store.savedTemplates.filter(t => t.modalityId === 'calistenia'))
</script>

<template>
  <div class="container animate-fade-in">
    <button @click="goBack" class="btn-back">← Voltar</button>

    <header class="section-header">
      <h2>Planejar: {{ modalityName }}</h2>
      <div class="header-actions">
        <button class="btn-outline" @click="saveAsTemplate">Salvar Sessão Padrão</button>
        <button class="btn-primary custom-btn" @click="startSession">Iniciar Sessão Agora</button>
      </div>
    </header>

    <div v-if="myTemplates.length > 0" class="templates-section">
      <label>Carregar Treino Salvo:</label>
      <select class="input-field template-select" @change="e => loadTemplate(Number(e.target.value))">
        <option value="">-- Escolha um treino --</option>
        <option v-for="tpl in myTemplates" :key="tpl.id" :value="tpl.id">{{ tpl.name }}</option>
      </select>
    </div>

    <div class="form-container glass-panel">
      <div class="form-group">
        <label>Nome do Treino</label>
        <input v-model="sessionName" type="text" class="input-field" />
      </div>

      <div class="divider"></div>
      <h3>Exercícios Planejados</h3>
      
      <div class="exercises-list">
        <div v-for="(ex, index) in exercises" :key="ex.id" class="exercise-row">
          <div class="form-group">
            <label>Área</label>
            <select v-model="ex.area" class="input-field select-field">
              <option value="superior">Superior</option>
              <option value="core">Core</option>
              <option value="inferior">Inferior</option>
              <option value="cardio">Cardio</option>
              <option value="outro">Outro</option>
            </select>
          </div>

          <div class="form-group" v-if="ex.area !== 'outro'">
            <label>Exercício</label>
            <select v-model="ex.name" class="input-field select-field">
              <option v-for="trick in availableTricks[ex.area]" :key="trick" :value="trick">{{ trick }}</option>
              <option value="outro">Outro (Digitar)</option>
            </select>
          </div>

          <div class="form-group" v-if="ex.area === 'outro' || ex.name === 'outro'">
            <label>Nome do Exercício</label>
            <input v-model="ex.customName" type="text" class="input-field" placeholder="Ex: Alongamento" />
          </div>
          
          <div class="form-group">
            <label>Séries</label>
            <input v-model="ex.sets" type="number" min="1" class="input-field" />
          </div>
          
          <div class="form-group">
            <label>Reps</label>
            <input v-model="ex.reps" type="number" min="1" class="input-field" />
          </div>

          <div class="form-group">
            <label>Peso (kg)</label>
            <input v-model="ex.weight" type="number" min="0" class="input-field" />
          </div>

          <button @click="removeExercise(index)" class="btn-icon delete-btn">×</button>
        </div>
      </div>

      <button @click="addExercise" class="btn-outline">+ Adicionar Exercício</button>
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

.header-actions {
  display: flex;
  gap: 1rem;
}

.templates-section {
  margin-bottom: 2rem;
  background: rgba(255,255,255,0.02);
  padding: 1.5rem;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-light);
}

.template-select {
  margin-top: 0.5rem;
}

.custom-btn {
  background: #10b981;
  box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4);
}
.custom-btn:hover {
  box-shadow: 0 6px 20px rgba(16, 185, 129, 0.6);
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
  border-color: #10b981;
}

.select-field {
  appearance: none;
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
  grid-template-columns: 1fr 1.5fr 0.8fr 0.8fr 0.8fr 40px;
  gap: 1rem;
  align-items: flex-end;
  background: rgba(255,255,255,0.02);
  padding: 1rem;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-subtle);
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
  color: #10b981;
  font-weight: 500;
  transition: all var(--transition-fast);
}
.btn-outline:hover {
  background: rgba(16, 185, 129, 0.05);
  border-style: solid;
}
</style>
