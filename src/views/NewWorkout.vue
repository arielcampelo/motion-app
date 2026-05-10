<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useWorkoutStore } from '../store/workout'

const route = useRoute()
const router = useRouter()
const store = useWorkoutStore()

const modalityId = computed(() => route.params.id)
const modality = computed(() => store.modalities.find(m => m.id === modalityId.value))
const exercises = computed(() => store.exercises[modalityId.value] || [])

const workoutName = ref('')
const selectedExercise = ref('')

// Calistenia form
const sets = ref([{ reps: 10, weight: 0 }])
const addSet = () => sets.value.push({ reps: 10, weight: 0 })
const removeSet = (index) => sets.value.length > 1 && sets.value.splice(index, 1)

// Malabarismo form
const jugglingDuration = ref(30)
const maxCatches = ref(0)

// Escalada form
const tops = ref(0)
const maxGrade = ref(1)

// Natação form
const distance = ref(1000)
const swimTime = ref(30)

const saveWorkout = () => {
  let details = {}
  
  if (modalityId.value === 'calistenia') {
    details = {
      totalSets: sets.value.length,
      totalReps: sets.value.reduce((acc, s) => acc + Number(s.reps), 0),
      sets: [...sets.value]
    }
  } else if (modalityId.value === 'malabarismo') {
    details = { duration: jugglingDuration.value, maxCatches: maxCatches.value }
  } else if (modalityId.value === 'escalada') {
    details = { tops: tops.value, maxGrade: maxGrade.value }
  } else if (modalityId.value === 'natacao') {
    details = { distance: distance.value, time: swimTime.value }
  }

  store.addWorkout({
    name: workoutName.value || `Treino de ${modality.value.name}`,
    modalityId: modalityId.value,
    exercise: selectedExercise.value,
    details
  })
  
  router.push(`/modality/${modalityId.value}`)
}

const goBack = () => router.push(`/modality/${modalityId.value}`)
</script>

<template>
  <div v-if="modality" class="container animate-fade-in">
    <button @click="goBack" class="btn-back">← Voltar</button>

    <header class="section-header">
      <div>
        <h2>Novo Treino de {{ modality.name }}</h2>
      </div>
      <button class="btn-primary custom-btn" :style="{ '--mod-color': modality.color }" @click="saveWorkout">Salvar Treino</button>
    </header>

    <div class="form-container glass-panel">
      <div class="form-group">
        <label>Nome do Treino (Opcional)</label>
        <input v-model="workoutName" type="text" placeholder="Ex: Treino Intenso" class="input-field" />
      </div>
      
      <div class="form-group">
        <label>Foco Principal</label>
        <select v-model="selectedExercise" class="input-field select-field">
          <option value="">Selecione o exercício/técnica...</option>
          <option v-for="ex in exercises" :key="ex" :value="ex">{{ ex }}</option>
        </select>
      </div>

      <div class="divider"></div>

      <!-- CALISTENIA -->
      <div v-if="modalityId === 'calistenia'" class="modality-form">
        <div class="sets-header">
          <span>Série</span><span>Reps</span><span>Peso (kg)</span><span></span>
        </div>
        <div v-for="(set, index) in sets" :key="index" class="set-row">
          <div class="set-number">{{ index + 1 }}</div>
          <input v-model="set.reps" type="number" min="1" class="input-field compact" />
          <input v-model="set.weight" type="number" min="0" class="input-field compact" placeholder="Peso extra" />
          <button @click="removeSet(index)" class="btn-icon">×</button>
        </div>
        <button @click="addSet" class="btn-outline" :style="{ '--mod-color': modality.color }">+ Adicionar Série</button>
      </div>

      <!-- MALABARISMO -->
      <div v-else-if="modalityId === 'malabarismo'" class="modality-form">
        <div class="form-row">
          <div class="form-group">
            <label>Duração (Minutos)</label>
            <input v-model="jugglingDuration" type="number" min="1" class="input-field" />
          </div>
          <div class="form-group">
            <label>Max Catches (Recorde do dia)</label>
            <input v-model="maxCatches" type="number" min="0" class="input-field" />
          </div>
        </div>
      </div>

      <!-- ESCALADA -->
      <div v-else-if="modalityId === 'escalada'" class="modality-form">
        <div class="form-row">
          <div class="form-group">
            <label>Tops (Vias completadas)</label>
            <input v-model="tops" type="number" min="0" class="input-field" />
          </div>
          <div class="form-group">
            <label>Maior Grau Alcançado (V)</label>
            <div style="display:flex;align-items:center;gap:10px;">
              <span style="font-size:1.2rem;font-weight:bold;color:var(--text-secondary)">V</span>
              <input v-model="maxGrade" type="number" min="0" class="input-field" />
            </div>
          </div>
        </div>
      </div>

      <!-- NATAÇÃO -->
      <div v-else-if="modalityId === 'natacao'" class="modality-form">
        <div class="form-row">
          <div class="form-group">
            <label>Distância Total (Metros)</label>
            <input v-model="distance" type="number" step="50" min="50" class="input-field" />
          </div>
          <div class="form-group">
            <label>Tempo Total (Minutos)</label>
            <input v-model="swimTime" type="number" min="1" class="input-field" />
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<style>
/* Global fix for container on mobile */
@media (max-width: 600px) {
  .container {
    padding: 1rem !important;
  }
  .form-container {
    padding: 1.25rem !important;
  }
}
</style>

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
  background: var(--mod-color);
  box-shadow: 0 4px 15px var(--mod-color);
  opacity: 0.9;
}
.custom-btn:hover {
  opacity: 1;
  box-shadow: 0 6px 20px var(--mod-color);
}

.form-container {
  padding: 2rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

@media (max-width: 600px) {
  .form-row {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
}

label {
  display: block;
  font-size: 0.9rem;
  color: var(--text-secondary);
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.input-field {
  width: 100%;
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  padding: 12px 16px;
  color: var(--text-primary);
  font-family: var(--font-body);
  font-size: 1rem;
  transition: border-color var(--transition-fast);
}
.input-field:focus {
  outline: none;
  border-color: var(--accent-primary);
}

.select-field {
  appearance: none;
  background-image: url("data:image/svg+xml;charset=US-ASCII,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%22292.4%22%20height%3D%22292.4%22%3E%3Cpath%20fill%3D%22%239ca3af%22%20d%3D%22M287%2069.4a17.6%2017.6%200%200%200-13-5.4H18.4c-5%200-9.3%201.8-12.9%205.4A17.6%2017.6%200%200%200%200%2082.2c0%205%201.8%209.3%205.4%2012.9l128%20127.9c3.6%203.6%207.8%205.4%2012.8%205.4s9.2-1.8%2012.8-5.4L287%2095c3.5-3.5%205.4-7.8%205.4-12.8%200-5-1.9-9.2-5.5-12.8z%22%2F%3E%3C%2Fsvg%3E");
  background-repeat: no-repeat;
  background-position: right 1rem top 50%;
  background-size: 0.65rem auto;
}

.divider {
  height: 1px;
  background: var(--border-light);
  margin: 2rem 0;
}

.modality-form {
  background: rgba(255, 255, 255, 0.02);
  border-radius: var(--radius-md);
  padding: 1.5rem;
  border: 1px solid var(--border-subtle);
}

.sets-header {
  display: grid;
  grid-template-columns: 60px 1fr 1fr 40px;
  gap: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--border-light);
  margin-bottom: 1rem;
  font-size: 0.85rem;
  color: var(--text-tertiary);
  font-weight: 600;
}

.set-row {
  display: grid;
  grid-template-columns: 60px 1fr 1fr 40px;
  gap: 1rem;
  align-items: center;
  margin-bottom: 0.5rem;
}

.set-number {
  background: rgba(255, 255, 255, 0.05);
  width: 32px;
  height: 32px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  color: var(--text-secondary);
}

.compact {
  padding: 8px 12px;
}

.btn-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  color: var(--text-tertiary);
  border-radius: var(--radius-sm);
}
.btn-icon:hover {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

.btn-outline {
  margin-top: 1rem;
  width: 100%;
  padding: 10px;
  border: 1px dashed var(--border-light);
  border-radius: var(--radius-sm);
  color: var(--mod-color, var(--text-secondary));
  font-weight: 500;
  transition: all var(--transition-fast);
}
.btn-outline:hover {
  background: rgba(255,255,255,0.05);
  border-style: solid;
}
</style>
