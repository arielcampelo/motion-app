<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useWorkoutStore } from '../../store/workout'

const router = useRouter()
const store = useWorkoutStore()

const modality = computed(() => store.modalities.find(m => m.id === 'natacao'))
const sessionName = ref('Sessão de Natação')

const sets = ref([
  { id: Date.now(), style: 'Crawl (Livre)', distance: 400, reps: 1, rest: 30 }
])

const availableStyles = computed(() =>
  Array.isArray(store.exercises.natacao)
    ? store.exercises.natacao
    : ['Crawl (Livre)', 'Costas', 'Peito', 'Borboleta']
)

const totalDistance = computed(() =>
  sets.value.reduce((acc, s) => acc + Number(s.distance) * Number(s.reps), 0)
)

const addSet = () => {
  sets.value.push({
    id: Date.now(),
    style: 'Crawl (Livre)',
    distance: 100,
    reps: 1,
    rest: 30
  })
}

const removeSet = (index) => {
  sets.value.splice(index, 1)
}

const startSession = () => {
  if (sets.value.length === 0) return
  const sessionId = Date.now().toString()

  store.activeSession = {
    id: sessionId,
    name: sessionName.value,
    modalityId: 'natacao',
    exercises: [...sets.value]
  }
  router.push(`/modality/natacao/session/${sessionId}`)
}

const saveAsTemplate = () => {
  store.saveTemplate({
    name: sessionName.value,
    modalityId: 'natacao',
    exercises: JSON.parse(JSON.stringify(sets.value))
  })
  alert('Sessão salva com sucesso!')
}

const loadTemplate = (templateId) => {
  const tpl = store.savedTemplates.find(t => t.id === templateId)
  if (tpl) {
    sessionName.value = tpl.name
    sets.value = JSON.parse(JSON.stringify(tpl.exercises))
  }
}

const myTemplates = computed(() =>
  store.savedTemplates.filter(t => t.modalityId === 'natacao')
)

const goBack = () => router.push('/modality/natacao')
</script>

<template>
  <div class="container animate-fade-in">
    <button @click="goBack" class="btn-back">← Voltar</button>

    <header class="section-header">
      <div>
        <h2>Planejar: Natação 🏊‍♂️</h2>
        <p class="subtitle-meta">Total: <strong>{{ totalDistance }}m</strong></p>
      </div>
      <div class="header-actions">
        <button class="btn-outline save-tpl-btn" @click="saveAsTemplate">Salvar Sessão</button>
        <button class="btn-primary custom-btn" @click="startSession">Iniciar Agora</button>
      </div>
    </header>

    <!-- Load template -->
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
      <h3>Séries Planejadas</h3>

      <div class="exercises-list">
        <div v-for="(set, index) in sets" :key="set.id" class="exercise-row">
          <div class="form-group">
            <label>Estilo</label>
            <select v-model="set.style" class="input-field select-field">
              <option v-for="style in availableStyles" :key="style" :value="style">{{ style }}</option>
            </select>
          </div>

          <div class="form-group">
            <label>Distância (m)</label>
            <input v-model="set.distance" type="number" step="25" min="25" class="input-field" />
          </div>

          <div class="form-group">
            <label>Repetições</label>
            <input v-model="set.reps" type="number" min="1" class="input-field" />
          </div>

          <div class="form-group">
            <label>Descanso (s)</label>
            <input v-model="set.rest" type="number" min="0" class="input-field" />
          </div>

          <div class="form-group total-col">
            <label>Total</label>
            <span class="total-badge">{{ set.distance * set.reps }}m</span>
          </div>

          <button @click="removeSet(index)" class="btn-icon delete-btn">×</button>
        </div>
      </div>

      <button @click="addSet" class="btn-outline">+ Adicionar Série</button>
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
.btn-back:hover { color: var(--text-primary); }

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
  gap: 1rem;
  flex-wrap: wrap;
}

.subtitle-meta {
  font-size: 0.9rem;
  color: var(--text-secondary);
  margin-top: 0.25rem;
}
.subtitle-meta strong { color: #60a5fa; }

.header-actions {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.custom-btn {
  background: #3b82f6;
  box-shadow: 0 4px 15px rgba(59,130,246,0.4);
}
.custom-btn:hover { box-shadow: 0 6px 20px rgba(59,130,246,0.6); }

.save-tpl-btn {
  border-color: rgba(59,130,246,0.4);
  color: #60a5fa;
}
.save-tpl-btn:hover { background: rgba(59,130,246,0.08); border-style: solid; }

.templates-section {
  margin-bottom: 2rem;
  background: rgba(255,255,255,0.02);
  padding: 1.5rem;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-light);
}
.template-select { margin-top: 0.5rem; }

.form-container { padding: 2rem; }

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
  background: rgba(0,0,0,0.2);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  padding: 10px 14px;
  color: var(--text-primary);
  font-family: var(--font-body);
  font-size: 0.95rem;
}
.input-field:focus {
  outline: none;
  border-color: #3b82f6;
}

.select-field { appearance: none; }

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
  grid-template-columns: 1.3fr 0.8fr 0.7fr 0.7fr 0.7fr 40px;
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
  .total-col { display: none; }
}

.total-badge {
  background: rgba(59,130,246,0.12);
  border: 1px solid rgba(59,130,246,0.25);
  border-radius: 99px;
  padding: 8px 14px;
  font-size: 0.85rem;
  font-weight: 600;
  color: #60a5fa;
  text-align: center;
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
  cursor: pointer;
}
.btn-icon:hover { background: rgba(239,68,68,0.2); color: #ef4444; }

.btn-outline {
  width: 100%;
  padding: 12px;
  border: 1px dashed var(--border-light);
  border-radius: var(--radius-sm);
  color: #3b82f6;
  font-weight: 500;
  transition: all var(--transition-fast);
}
.btn-outline:hover {
  background: rgba(59,130,246,0.05);
  border-style: solid;
}
</style>
