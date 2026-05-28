<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useWorkoutStore } from '../../store/workout'

const router = useRouter()
const route = useRoute()
const store = useWorkoutStore()

const modalityId = computed(() => route.params.id)
const modalityName = computed(() => store.modalities.find(m => m.id === modalityId.value)?.name || 'Calistenia')

const sessionName = ref(`Sessão de ${modalityName.value}`)
const sessionRestTime = ref(60) // Tempo de descanso em segundos
const exercises = ref([
  { id: Date.now(), area: 'superior', name: 'Flexão', customName: '', sets: 3, reps: 10 }
])

const availableTricks = computed(() => store.exercises.calistenia || { superior: [], core: [], inferior: [] })

const addExercise = () => {
  exercises.value.push({
    id: Date.now(),
    area: 'superior',
    name: 'Flexão',
    customName: '',
    sets: 3,
    reps: 10
  })
}

const getOntologyInfo = (name) => {
  return store.calisthenicsOntology[name] || null
}

const getExerciseUnitLabel = (name) => {
  const info = getOntologyInfo(name)
  return info && info.unit === 'seconds' ? 'Segundos' : 'Reps'
}

const capitalize = (str) => {
  if (!str) return ''
  return str.charAt(0).toUpperCase() + str.slice(1)
}

const isRequirementMet = (req, currentExercises) => {
  return currentExercises.some(ex => ex.name === req)
}

const hasMissingRequirements = (name, currentExercises) => {
  const info = getOntologyInfo(name)
  if (!info || !info.requirements || info.requirements.length === 0) return false
  return info.requirements.some(req => !isRequirementMet(req, currentExercises))
}

const onExerciseChange = (ex) => {
  const info = getOntologyInfo(ex.name)
  if (info) {
    if (info.unit === 'seconds' && ex.reps <= 15) {
      ex.reps = 30
    } else if (info.unit === 'reps' && ex.reps >= 20) {
      ex.reps = 10
    }
  }
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
    restTime: sessionRestTime.value,
    modalityId: 'calistenia',
    exercises: finalExercises
  }
  router.push(`/modality/calistenia/session/${sessionId}`)
}

const goBack = () => router.push(`/modality/calistenia`)
const saveAsTemplate = () => {
  store.saveTemplate({
    name: sessionName.value,
    restTime: sessionRestTime.value,
    modalityId: 'calistenia',
    exercises: JSON.parse(JSON.stringify(exercises.value))
  })
  alert('Sessão salva com sucesso para uso futuro!')
}

const loadTemplate = (templateId) => {
  const tpl = store.savedTemplates.find(t => t.id === templateId)
  if (tpl) {
    sessionName.value = tpl.name
    sessionRestTime.value = tpl.restTime || 60
    exercises.value = JSON.parse(JSON.stringify(tpl.exercises))
  }
}

const applyOverload = (ex, progInfo) => {
  ex.reps = progInfo.recommended_next_reps
  ex.sets = progInfo.recommended_next_sets
}

const replaceWithAdvancedExercise = (index, nextExerciseName) => {
  const info = getOntologyInfo(nextExerciseName)
  if (info) {
    exercises.value[index].name = nextExerciseName
    exercises.value[index].area = info.area.toLowerCase()
    onExerciseChange(exercises.value[index])
  }
}

const getExerciseUnitText = (name) => {
  const info = getOntologyInfo(name)
  if (info) {
    return info.unit === 'seconds' ? 'segundos' : 'reps'
  }
  return 'reps'
}

const quickAddExercise = (name, area) => {
  const info = getOntologyInfo(name)
  const isIsometric = info && info.type === 'isometric'
  exercises.value.push({
    id: Date.now() + Math.random(),
    area: area.toLowerCase(),
    name: name,
    sets: 3,
    reps: isIsometric ? 30 : 10
  })
}

const myTemplates = computed(() => store.savedTemplates.filter(t => t.modalityId === 'calistenia'))

// --- ONTOLOGY PYTHON BACKEND INTEGRATION ---
const analysisResult = ref(null)

const analyzeWorkoutSession = async () => {
  if (store.ontologyStatus !== 'online') {
    analysisResult.value = null
    return
  }
  
  try {
    const payload = {
      exercises: exercises.value.map(ex => ({
        name: ex.name === 'outro' ? ex.customName || 'Exercício Livre' : ex.name,
        sets: Number(ex.sets),
        reps: Number(ex.reps),
        area: ex.area
      }))
    }
    const response = await fetch('http://localhost:8085/api/analyze-workout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    if (response.ok) {
      analysisResult.value = await response.json()
    }
  } catch (err) {
    console.error('Erro ao analisar treino:', err)
  }
}

const getPushPullRatio = (patterns) => {
  const push = patterns['Empurrar'] || 0
  const pull = patterns['Puxar'] || 0
  if (push === 0 && pull === 0) return 50
  return (push / (push + pull)) * 100
}

watch(exercises, () => {
  analyzeWorkoutSession()
}, { deep: true })

onMounted(() => {
  store.loadOntology().then(() => {
    analyzeWorkoutSession()
    
    // Prefill exercise if passed in query params
    if (route.query.prefill) {
      const prefillEx = decodeURIComponent(route.query.prefill)
      const ontologyInfo = store.calisthenicsOntology[prefillEx]
      if (ontologyInfo) {
        const isIsometric = ontologyInfo.type === 'isometric'
        exercises.value = [
          {
            id: Date.now(),
            area: ontologyInfo.area.toLowerCase(),
            name: prefillEx,
            customName: '',
            sets: 3,
            reps: isIsometric ? 30 : 10
          }
        ]
        
        // Auto apply overload if history exists
        store.evaluateUser().then((evalData) => {
          if (evalData && evalData.exercise_progressions[prefillEx]) {
            const progInfo = evalData.exercise_progressions[prefillEx]
            if (progInfo.max_reps_completed > 0) {
              exercises.value[0].reps = progInfo.recommended_next_reps
              exercises.value[0].sets = progInfo.recommended_next_sets
            }
          }
        })
      }
    }
  })
  store.evaluateUser()
})
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

    <!-- Painel de Análise Semântica (Ontologia) -->
    <div v-if="store.ontologyStatus === 'online' && analysisResult" class="analysis-panel glass-panel animate-fade-in">
      <div class="analysis-header">
        <h4>🧠 Análise Semântica da Ontologia (Python SPARQL)</h4>
        <span class="status-indicator online">Online</span>
      </div>
      
      <div class="analysis-grid">
        <!-- Balanço de Volume por Área -->
        <div class="analysis-card">
          <h5>Distribuição por Padrão de Movimento</h5>
          <div class="pattern-badges">
            <span v-for="(count, pat) in analysisResult.patterns" :key="pat" class="badge-pattern">
              {{ pat }}: {{ count }}
            </span>
          </div>
          <!-- Barra de Progresso Push vs Pull -->
          <div v-if="analysisResult.patterns['Empurrar'] || analysisResult.patterns['Puxar']" class="balance-bar-container">
            <div class="balance-bar-labels">
              <span>Empurrar ({{ analysisResult.patterns['Empurrar'] || 0 }})</span>
              <span>Puxar ({{ analysisResult.patterns['Puxar'] || 0 }})</span>
            </div>
            <div class="balance-bar">
              <div 
                class="bar-fill push" 
                :style="{ width: getPushPullRatio(analysisResult.patterns) + '%' }"
              ></div>
              <div class="bar-fill pull"></div>
            </div>
          </div>
        </div>

        <!-- Divisão de Dificuldade -->
        <div class="analysis-card">
          <h5>Níveis da Sessão</h5>
          <div class="level-bars">
            <div v-for="(count, lvl) in analysisResult.levels" :key="lvl" class="level-bar-item">
              <span class="level-name">{{ lvl }}</span>
              <span class="level-count">{{ count }} ex.</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Alertas & Avisos da Ontologia -->
      <div class="analysis-alerts" v-if="analysisResult.warnings.length > 0 || analysisResult.recommendations.length > 0">
        <div v-if="analysisResult.warnings.length > 0" class="alerts-section">
          <h5>Avisos de Alinhamento:</h5>
          <ul>
            <li v-for="warn in analysisResult.warnings" :key="warn" class="warn-item">
              ⚠️ {{ warn }}
            </li>
          </ul>
        </div>
        <div v-if="analysisResult.recommendations.length > 0" class="recommendations-section" style="margin-top: 0.75rem;">
          <h5>Sugestões de Progressão:</h5>
          <ul>
            <li v-for="rec in analysisResult.recommendations" :key="rec" class="rec-item">
              💡 {{ rec }}
            </li>
          </ul>
        </div>
      </div>
      
      <div v-else class="analysis-success">
        <span class="success-icon">✓</span>
        <p>Treino equilibrado e estruturado de acordo com as regras de progressão da ontologia!</p>
      </div>
    </div>

    <div class="form-container glass-panel">
      <!-- Painel de Nível do Usuário (Ontologia) -->
      <div v-if="store.userEvaluation" class="user-level-panel animate-fade-in">
        <h4 class="user-level-title">🧠 Seu Nível e Recomendações de Range</h4>
        <div class="user-level-grid">
          <div v-for="(data, area) in store.userEvaluation.area_levels" :key="area" class="user-level-card">
            <div class="card-area">{{ area }}</div>
            <div class="card-level" :class="data.level.toLowerCase()">{{ data.level }}</div>
            <div class="card-count">{{ data.completed_count }} dominados</div>
            <!-- Exercícios Recomendados (Range) -->
            <div v-if="data.unlocked_next.length > 0" class="card-unlocked">
              <span class="unlocked-label">Pode tentar:</span>
              <div class="unlocked-chips">
                <span 
                  v-for="ex in data.unlocked_next" 
                  :key="ex" 
                  class="chip-unlocked" 
                  @click="quickAddExercise(ex, area)"
                  title="Adicionar ao treino"
                >
                  + {{ ex }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="form-group">
        <label>Nome do Treino</label>
        <input v-model="sessionName" type="text" class="input-field" />
      </div>

      <div class="form-group" style="margin-top: 1rem;">
        <label>Tempo de Descanso entre as Séries (segundos)</label>
        <input v-model="sessionRestTime" type="number" min="0" class="input-field" />
      </div>

      <div class="divider"></div>
      <h3>Exercícios Planejados</h3>
      
      <div class="exercises-list">
        <div class="exercise-card glass-panel" v-for="(ex, index) in exercises" :key="ex.id">
          <div class="exercise-row">
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
              <select v-model="ex.name" class="input-field select-field" @change="onExerciseChange(ex)">
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
              <label>{{ getExerciseUnitLabel(ex.name) }}</label>
              <input v-model="ex.reps" type="number" min="1" class="input-field" />
            </div>

            <button @click="removeExercise(index)" class="btn-icon delete-btn">×</button>
          </div>

          <!-- Painel da Ontologia / Sugestões -->
          <div v-if="getOntologyInfo(ex.name) && ex.area !== 'outro' && ex.name !== 'outro'" class="ontology-panel animate-fade-in">
            <div class="ontology-header">
              <div class="ontology-badges">
                <span class="badge-level" :class="getOntologyInfo(ex.name).level">
                  {{ getOntologyInfo(ex.name).level }}
                </span>
                <span class="badge-type">
                  {{ getOntologyInfo(ex.name).type === 'isometric' ? 'Isométrico' : 'Dinâmico' }}
                </span>
              </div>
            </div>
            
            <p class="ontology-desc">{{ getOntologyInfo(ex.name).description }}</p>
            
            <!-- Relação de Requerimento -->
            <div v-if="getOntologyInfo(ex.name).requirements.length > 0" class="ontology-requirements">
              <span class="req-title">Requisitos recomendados:</span>
              <span 
                v-for="req in getOntologyInfo(ex.name).requirements" 
                :key="req" 
                class="badge-req"
                :class="{ 'is-missing': !isRequirementMet(req, exercises) }"
              >
                {{ req }} {{ isRequirementMet(req, exercises) ? '✓' : '⚠️' }}
              </span>
              <p v-if="hasMissingRequirements(ex.name, exercises)" class="req-warning">
                ⚠️ Dica: Adicione os exercícios de requisito marcados com ⚠️ na sua rotina para evoluir com segurança.
              </p>
            </div>

            <!-- Painel de Sobrecarga Progressiva Semântica -->
            <div v-if="store.userEvaluation && store.userEvaluation.exercise_progressions[ex.name]" class="overload-section animate-fade-in">
              <div v-if="store.userEvaluation.exercise_progressions[ex.name].max_reps_completed > 0" class="overload-box">
                <span class="overload-title">⚡ Sobrecarga Progressiva (Histórico)</span>
                <div class="overload-details">
                  <p class="overload-text">
                    Seu recorde: <strong>{{ store.userEvaluation.exercise_progressions[ex.name].max_reps_completed }} {{ getExerciseUnitText(ex.name) }}</strong>. 
                    Meta sugerida: <strong>{{ store.userEvaluation.exercise_progressions[ex.name].recommended_next_sets }} x {{ store.userEvaluation.exercise_progressions[ex.name].recommended_next_reps }} {{ getExerciseUnitText(ex.name) }}</strong>.
                  </p>
                  <button 
                    v-if="Number(ex.reps) !== store.userEvaluation.exercise_progressions[ex.name].recommended_next_reps || Number(ex.sets) !== store.userEvaluation.exercise_progressions[ex.name].recommended_next_sets"
                    @click="applyOverload(ex, store.userEvaluation.exercise_progressions[ex.name])" 
                    class="btn-overload-apply animate-pulse"
                  >
                    Aplicar Carga
                  </button>
                  <span v-else class="badge-overload-applied">✓ Carga Aplicada</span>
                </div>
                
                <div v-if="store.userEvaluation.exercise_progressions[ex.name].progression_status === 'progredir_exercicio' && store.userEvaluation.exercise_progressions[ex.name].next_exercise_suggestion" class="overload-evolution">
                  <span>🚀 <strong>Pronto para evoluir!</strong> Sugerimos avançar para <strong>{{ store.userEvaluation.exercise_progressions[ex.name].next_exercise_suggestion }}</strong>.</span>
                  <button @click="replaceWithAdvancedExercise(index, store.userEvaluation.exercise_progressions[ex.name].next_exercise_suggestion)" class="btn-overload-swap">
                    Substituir Exercício
                  </button>
                </div>
              </div>
            </div>

            <!-- Sistema de Sugestão -->
            <div class="ontology-suggestion">
              <span class="sug-icon">💡</span>
              <p class="sug-text">{{ getOntologyInfo(ex.name).suggestion }}</p>
            </div>
          </div>
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

.exercise-card {
  background: rgba(255, 255, 255, 0.01);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-subtle);
  overflow: hidden;
  transition: all var(--transition-normal);
}
.exercise-card:hover {
  border-color: rgba(16, 185, 129, 0.2);
  background: rgba(255, 255, 255, 0.02);
}

.exercise-row {
  display: grid;
  grid-template-columns: 1fr 1.5fr 0.8fr 0.8fr 40px;
  gap: 1rem;
  align-items: flex-end;
  padding: 1.5rem;
}

@media (max-width: 768px) {
  .exercise-row {
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
  }
  
  .exercise-row .form-group:nth-child(2) {
    grid-column: span 2;
  }
  
  .delete-btn {
    grid-column: 2;
    justify-self: end;
  }
}

/* Estilos do Painel de Ontologia */
.ontology-panel {
  padding: 0 1.5rem 1.5rem 1.5rem;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  background: rgba(0, 0, 0, 0.1);
  font-size: 0.9rem;
}

.ontology-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1rem;
  margin-bottom: 0.5rem;
}

.ontology-badges {
  display: flex;
  gap: 0.5rem;
}

.badge-level, .badge-type {
  padding: 3px 8px;
  border-radius: var(--radius-full);
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.badge-level.iniciante {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
  border: 1px solid rgba(16, 185, 129, 0.2);
}

.badge-level.intermediario {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
  border: 1px solid rgba(245, 158, 11, 0.2);
}

.badge-level.avancado {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
  border: 1px solid rgba(239, 68, 68, 0.2);
}

.badge-type {
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-secondary);
  border: 1px solid var(--border-light);
}

.ontology-desc {
  color: var(--text-secondary);
  margin-top: 0.5rem;
  margin-bottom: 0.75rem;
  line-height: 1.4;
}

.ontology-requirements {
  margin-top: 0.75rem;
  padding: 0.75rem;
  background: rgba(0, 0, 0, 0.15);
  border-radius: var(--radius-sm);
  border: 1px solid rgba(255, 255, 255, 0.03);
}

.req-title {
  font-weight: 600;
  margin-right: 0.5rem;
  color: var(--text-secondary);
  font-size: 0.85rem;
}

.badge-req {
  display: inline-block;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
  font-size: 0.8rem;
  margin-right: 0.4rem;
  font-weight: 500;
  border: 1px solid rgba(16, 185, 129, 0.2);
}

.badge-req.is-missing {
  background: rgba(245, 158, 11, 0.05);
  color: #f59e0b;
  border: 1px solid rgba(245, 158, 11, 0.2);
}

.req-warning {
  color: #f59e0b;
  font-size: 0.8rem;
  margin-top: 0.5rem;
  margin-bottom: 0;
}

.ontology-suggestion {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.75rem;
  padding: 0.75rem;
  background: rgba(16, 185, 129, 0.05);
  border-left: 3px solid #10b981;
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
}

.sug-icon {
  font-size: 1rem;
}

.sug-text {
  margin: 0;
  font-size: 0.85rem;
  color: var(--text-primary);
  line-height: 1.4;
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

/* Estilos do Painel de Análise Semântica */
.analysis-panel {
  padding: 1.5rem;
  margin-bottom: 2rem;
  border-color: rgba(139, 92, 246, 0.2);
  background: rgba(139, 92, 246, 0.02);
}

.analysis-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.2rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  padding-bottom: 0.6rem;
}

.analysis-header h4 {
  font-size: 1.1rem;
  color: var(--text-primary);
  font-weight: 600;
}

.status-indicator {
  font-size: 0.75rem;
  padding: 2px 8px;
  border-radius: var(--radius-full);
  font-weight: 600;
  text-transform: uppercase;
}

.status-indicator.online {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
  border: 1px solid rgba(16, 185, 129, 0.2);
}

.analysis-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  margin-bottom: 1.2rem;
}

@media (max-width: 768px) {
  .analysis-grid {
    grid-template-columns: 1fr;
  }
}

.analysis-card {
  background: rgba(0, 0, 0, 0.2);
  padding: 1rem;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-subtle);
}

.analysis-card h5 {
  font-size: 0.9rem;
  margin-bottom: 0.75rem;
  color: var(--text-secondary);
  font-weight: 600;
}

.pattern-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.badge-pattern {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border-light);
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.8rem;
  color: var(--text-primary);
}

.balance-bar-container {
  margin-top: 1rem;
}

.balance-bar-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: var(--text-tertiary);
  margin-bottom: 0.25rem;
}

.balance-bar {
  display: flex;
  height: 8px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.bar-fill.push {
  background: #3b82f6; /* Blue for push */
}

.bar-fill.pull {
  flex-grow: 1;
  background: #f59e0b; /* Orange for pull */
}

.level-bars {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.level-bar-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.85rem;
}

.level-name {
  color: var(--text-secondary);
}

.level-count {
  font-weight: 600;
  color: var(--text-primary);
}

.analysis-alerts {
  background: rgba(0, 0, 0, 0.15);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-subtle);
  padding: 1rem;
}

.alerts-section h5, .recommendations-section h5 {
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin-bottom: 0.5rem;
  font-weight: 600;
}

.alerts-section ul, .recommendations-section ul {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  padding-left: 0;
}

.warn-item {
  color: #f59e0b;
  font-size: 0.85rem;
  line-height: 1.4;
}

.rec-item {
  color: #a78bfa;
  font-size: 0.85rem;
  line-height: 1.4;
}

.analysis-success {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  background: rgba(16, 185, 129, 0.05);
  border: 1px solid rgba(16, 185, 129, 0.1);
  padding: 0.75rem 1rem;
  border-radius: var(--radius-sm);
}

.success-icon {
  background: #10b981;
  color: white;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 0.75rem;
}

.analysis-success p {
  margin: 0;
  font-size: 0.85rem;
  color: #10b981;
}

/* User Level Panel */
.user-level-panel {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  padding: 1.25rem;
  margin-bottom: 2rem;
}

.user-level-title {
  font-size: 1rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 1rem;
  border-left: 3px solid #8b5cf6;
  padding-left: 0.5rem;
}

.user-level-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 1rem;
}

.user-level-card {
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: var(--radius-sm);
  padding: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.card-area {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  color: var(--text-tertiary);
  letter-spacing: 0.05em;
}

.card-level {
  font-size: 0.95rem;
  font-weight: 700;
  text-transform: capitalize;
}
.card-level.iniciante { color: #10b981; }
.card-level.intermediário, .card-level.intermediario { color: #f59e0b; }
.card-level.avanço, .card-level.avancado { color: #ef4444; }

.card-count {
  font-size: 0.75rem;
  color: var(--text-secondary);
  margin-bottom: 0.5rem;
}

.card-unlocked {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  padding-top: 0.5rem;
  margin-top: auto;
}

.unlocked-label {
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  color: var(--text-tertiary);
}

.unlocked-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
}

.chip-unlocked {
  background: rgba(139, 92, 246, 0.08);
  border: 1px solid rgba(139, 92, 246, 0.2);
  color: #a78bfa;
  font-size: 0.7rem;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
  cursor: pointer;
  transition: all var(--transition-fast);
  white-space: nowrap;
}

.chip-unlocked:hover {
  background: rgba(139, 92, 246, 0.2);
  transform: translateY(-1px);
  color: white;
}

/* Progressive Overload Box */
.overload-section {
  margin: 1rem 0;
}

.overload-box {
  background: rgba(16, 185, 129, 0.02);
  border-left: 3px solid #10b981;
  border: 1px solid rgba(16, 185, 129, 0.1);
  border-left-width: 3px;
  border-radius: var(--radius-sm);
  padding: 0.85rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.overload-title {
  font-size: 0.75rem;
  font-weight: 700;
  color: #10b981;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.overload-details {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.overload-text {
  margin: 0;
  font-size: 0.8rem;
  color: var(--text-secondary);
  line-height: 1.4;
}

.btn-overload-apply {
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.3);
  color: #10b981;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 700;
  cursor: pointer;
  transition: all var(--transition-fast);
  white-space: nowrap;
}

.btn-overload-apply:hover {
  background: #10b981;
  color: white;
  transform: scale(1.05);
}

.badge-overload-applied {
  background: rgba(16, 185, 129, 0.08);
  color: #10b981;
  border: 1px solid rgba(16, 185, 129, 0.15);
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 700;
  white-space: nowrap;
}

.overload-evolution {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  border-top: 1px solid rgba(255, 255, 255, 0.04);
  padding-top: 0.5rem;
  margin-top: 0.25rem;
  font-size: 0.75rem;
  color: var(--text-primary);
}

.btn-overload-swap {
  background: rgba(139, 92, 246, 0.1);
  border: 1px solid rgba(139, 92, 246, 0.3);
  color: #a78bfa;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 700;
  cursor: pointer;
  align-self: flex-start;
  transition: all var(--transition-fast);
}

.btn-overload-swap:hover {
  background: #8b5cf6;
  color: white;
}
</style>
