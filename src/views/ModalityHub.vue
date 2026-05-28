<script setup>
import { ref, computed, onMounted } from 'vue'
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

const startFreeJuggling = () => {
  const sessionId = Date.now().toString()
  store.activeSession = {
    id: sessionId,
    name: 'Treino Livre de Malabarismo',
    modalityId: 'malabarismo',
    exercises: [
      { id: Date.now(), name: 'Treino Livre', instrument: 'bolas', type: 'livre', target: 0, sets: 1 }
    ]
  }
  router.push(`/modality/malabarismo/session/${sessionId}`)
}

// --- TAB STATE ---
const activeTab = ref('history') // 'history' | 'progression'

// --- ONTOLOGY PROGRESSION TREE STATE ---
const progressionTree = ref({ nodes: [], edges: [] })
const selectedNode = ref(null)

const completedExercises = computed(() => {
  const completed = new Set()
  workouts.value.forEach(w => {
    if (w.details && w.details.blocks) {
      w.details.blocks.forEach(b => {
        completed.add(b.name)
      })
    }
  })
  return completed
})

const getPrerequisites = (nodeId) => {
  return progressionTree.value.edges
    .filter(e => e.target === nodeId)
    .map(e => e.source)
}

const getUnlocks = (nodeId) => {
  return progressionTree.value.edges
    .filter(e => e.source === nodeId)
    .map(e => e.target)
}

const getNodeStatus = (node) => {
  if (completedExercises.value.has(node.id)) {
    return 'completed'
  }
  const prereqs = getPrerequisites(node.id)
  if (prereqs.length === 0) {
    return 'unlocked'
  }
  const allMet = prereqs.every(req => completedExercises.value.has(req))
  return allMet ? 'unlocked' : 'locked'
}

const trainingPlans = ref([])

const fetchTrainingPlans = async () => {
  try {
    const response = await fetch('http://localhost:8085/api/training-plans')
    if (response.ok) {
      trainingPlans.value = await response.json()
    }
  } catch (err) {
    console.error('Erro ao buscar planos de treino:', err)
  }
}

const fetchProgressionTree = async () => {
  try {
    const response = await fetch('http://localhost:8085/api/progression-tree')
    if (response.ok) {
      progressionTree.value = await response.json()
      if (progressionTree.value.nodes.length > 0) {
        selectedNode.value = progressionTree.value.nodes[0]
      }
    }
  } catch (err) {
    console.error('Erro ao buscar progression tree:', err)
  }
}

// Group nodes by category
const groupedNodes = computed(() => {
  const groups = {
    'Superior': { 'Iniciante': [], 'Intermediário': [], 'Avançado': [] },
    'Core': { 'Iniciante': [], 'Intermediário': [], 'Avançado': [] },
    'Inferior': { 'Iniciante': [], 'Intermediário': [], 'Avançado': [] },
    'Cardio': { 'Iniciante': [], 'Intermediário': [], 'Avançado': [] }
  }

  progressionTree.value.nodes.forEach(node => {
    // Ensure clean casing/accents matching
    let area = node.area
    if (area === 'superior') area = 'Superior'
    if (area === 'core') area = 'Core'
    if (area === 'inferior') area = 'Inferior'
    if (area === 'cardio') area = 'Cardio'

    let lvl = node.level
    if (lvl === 'iniciante') lvl = 'Iniciante'
    if (lvl === 'intermediario') lvl = 'Intermediário'
    if (lvl === 'avancado') lvl = 'Avançado'

    if (groups[area] && groups[area][lvl]) {
      groups[area][lvl].push({
        ...node,
        status: getNodeStatus(node)
      })
    }
  })

  return groups
})

const openPlannerWithExercise = (name) => {
  router.push(`/modality/calistenia/planner?prefill=${encodeURIComponent(name)}`)
}

onMounted(() => {
  store.loadOntology().then(() => {
    if (store.ontologyStatus === 'online') {
      fetchProgressionTree()
      fetchTrainingPlans()
    }
  })
})
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
      <div class="header-actions">
        <button v-if="modalityId === 'malabarismo'" class="btn-outline free-btn" @click="startFreeJuggling">
          📹 Câmera Livre
        </button>
        <button class="btn-primary custom-bg" @click="handlePrimaryAction">
          {{ ['malabarismo', 'calistenia', 'escalada', 'natacao'].includes(modalityId) ? '📅 Planejar Sessão' : '+ Registrar Treino' }}
        </button>
      </div>
    </header>

    <!-- Tabs Navigation (only for Calistenia for now) -->
    <div v-if="modalityId === 'calistenia' && store.ontologyStatus === 'online'" class="tabs-nav glass-panel animate-fade-in">
      <button 
        class="tab-btn" 
        :class="{ 'is-active': activeTab === 'history' }" 
        @click="activeTab = 'history'"
      >
        📝 Histórico de Treinos
      </button>
      <button 
        class="tab-btn" 
        :class="{ 'is-active': activeTab === 'progression' }" 
        @click="activeTab = 'progression'"
      >
        🌳 Árvore de Progressão (Ontologia)
      </button>
      <button 
        class="tab-btn" 
        :class="{ 'is-active': activeTab === 'plans' }" 
        @click="activeTab = 'plans'"
      >
        📈 Planos Semânticos (Milestones)
      </button>
    </div>

    <section v-if="activeTab === 'history'" class="workouts-history">
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

    <!-- Mapa de Progressão Calistênica -->
    <section v-else-if="activeTab === 'progression' && modalityId === 'calistenia'" class="progression-section">
      <div class="progression-layout">
        
        <!-- Árvore de Habilidades / RPG Game style -->
        <div class="skill-tree-container">
          <div v-for="(levels, area) in groupedNodes" :key="area" class="area-block glass-panel">
            <h3 class="area-title">{{ area }}</h3>
            
            <div class="tree-columns">
              <!-- Nível Iniciante -->
              <div class="tree-column">
                <span class="column-level iniciante">Iniciante</span>
                <div class="nodes-list">
                  <div 
                    v-for="node in levels['Iniciante']" 
                    :key="node.id" 
                    class="node-card" 
                    :class="[node.status, { 'is-selected': selectedNode && selectedNode.id === node.id }]"
                    @click="selectedNode = node"
                  >
                    <span class="node-indicator"></span>
                    <span class="node-name">{{ node.name }}</span>
                  </div>
                </div>
              </div>

              <!-- Nível Intermediário -->
              <div class="tree-column">
                <span class="column-level intermediario">Intermediário</span>
                <div class="nodes-list">
                  <div 
                    v-for="node in levels['Intermediário']" 
                    :key="node.id" 
                    class="node-card" 
                    :class="[node.status, { 'is-selected': selectedNode && selectedNode.id === node.id }]"
                    @click="selectedNode = node"
                  >
                    <span class="node-indicator"></span>
                    <span class="node-name">{{ node.name }}</span>
                  </div>
                </div>
              </div>

              <!-- Nível Avançado -->
              <div class="tree-column">
                <span class="column-level avancado">Avançado</span>
                <div class="nodes-list">
                  <div 
                    v-for="node in levels['Avançado']" 
                    :key="node.id" 
                    class="node-card" 
                    :class="[node.status, { 'is-selected': selectedNode && selectedNode.id === node.id }]"
                    @click="selectedNode = node"
                  >
                    <span class="node-indicator"></span>
                    <span class="node-name">{{ node.name }}</span>
                  </div>
                </div>
              </div>

            </div>
          </div>
        </div>

        <!-- Painel Lateral de Detalhes -->
        <div class="details-panel-container">
          <div v-if="selectedNode" class="node-details-card glass-panel animate-fade-in">
            <div class="details-header">
              <h3>{{ selectedNode.name }}</h3>
              <span class="badge-status" :class="selectedNode.status">
                {{ selectedNode.status === 'completed' ? '✓ Dominado' : selectedNode.status === 'unlocked' ? '🔓 Disponível' : '🔒 Bloqueado' }}
              </span>
            </div>
            
            <p class="details-desc">{{ store.calisthenicsOntology[selectedNode.name]?.description || 'Sem descrição na ontologia.' }}</p>
            
            <div class="details-meta-grid">
              <div class="meta-item">
                <span class="meta-label">Tipo:</span>
                <span class="meta-value">{{ selectedNode.type === 'isometric' ? 'Isométrico' : 'Dinâmico' }}</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">Nível:</span>
                <span class="meta-value badge-level-text" :class="selectedNode.level.toLowerCase()">{{ selectedNode.level }}</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">Foco:</span>
                <span class="meta-value">{{ selectedNode.pattern }}</span>
              </div>
            </div>

            <!-- Requisitos -->
            <div class="details-section-info" v-if="getPrerequisites(selectedNode.id).length > 0">
              <span class="details-subtitle">Requisitos Recomendados:</span>
              <div class="badge-row">
                <span 
                  v-for="req in getPrerequisites(selectedNode.id)" 
                  :key="req" 
                  class="badge-req-item"
                  :class="{ 'is-completed': completedExercises.has(req) }"
                >
                  {{ req }} {{ completedExercises.has(req) ? '✓' : '⚠️' }}
                </span>
              </div>
            </div>

            <!-- Desbloqueia -->
            <div class="details-section-info" v-if="getUnlocks(selectedNode.id).length > 0">
              <span class="details-subtitle">Próximas Progressões:</span>
              <div class="badge-row">
                <span 
                  v-for="unl in getUnlocks(selectedNode.id)" 
                  :key="unl" 
                  class="badge-unl-item"
                >
                  {{ unl }}
                </span>
              </div>
            </div>

            <!-- Dica de Treinamento -->
            <div class="details-suggestion" v-if="store.calisthenicsOntology[selectedNode.name]?.suggestion">
              <span class="suggestion-icon">💡</span>
              <p>{{ store.calisthenicsOntology[selectedNode.name]?.suggestion }}</p>
            </div>

            <!-- Abrir Plano de Treino -->
            <div class="details-action-row" style="margin-top: 1.5rem;">
              <button 
                @click="openPlannerWithExercise(selectedNode.name)" 
                class="btn-primary start-plan-btn"
                :class="{ 'advanced-glow': selectedNode.level.toLowerCase() === 'avançado' || selectedNode.level.toLowerCase() === 'avancado' }"
                style="width: 100%; display: flex; align-items: center; justify-content: center; gap: 0.5rem; padding: 12px;"
              >
                <span>{{ selectedNode.level.toLowerCase() === 'avançado' || selectedNode.level.toLowerCase() === 'avancado' ? '🔥 Criar Plano Avançado' : '📅 Criar Plano de Treino' }}</span>
              </button>
            </div>
          </div>
        </div>

      </div>
    </section>

    <!-- Seção de Planos de Treino (Milestones e Progressões) -->
    <section v-else-if="activeTab === 'plans' && modalityId === 'calistenia'" class="plans-section animate-fade-in">
      <h2>Planos de Treino Estruturados (Ontologia)</h2>
      <p class="section-desc" style="color: var(--text-secondary); margin-bottom: 2rem;">
        Esses planos são gerados dinamicamente a partir das regras e relações de milestones descritas na ontologia.
      </p>

      <div v-if="trainingPlans.length === 0" class="empty-state glass-panel">
        <div class="empty-icon">📈</div>
        <h3>Nenhum plano estruturado encontrado</h3>
        <p>Não há planos de treino cadastrados na ontologia para esta modalidade.</p>
      </div>

      <div v-else class="plans-grid">
        <div v-for="plan in trainingPlans" :key="plan.id" class="plan-card glass-panel" style="padding: 2rem; margin-bottom: 2rem;">
          <div class="plan-header" style="margin-bottom: 1.5rem; border-bottom: 1px solid var(--border-light); padding-bottom: 1rem;">
            <h3 style="font-size: 1.6rem; color: var(--accent-primary); margin-bottom: 0.5rem;">{{ plan.name }}</h3>
            <p style="color: var(--text-secondary); font-size: 0.95rem;">{{ plan.description }}</p>
          </div>

          <div class="milestones-timeline" style="display: flex; flex-direction: column; gap: 2rem;">
            <div v-for="(milestone, idx) in plan.milestones" :key="milestone.id" class="milestone-block" style="position: relative; padding-left: 2.5rem;">
              <!-- Linha vertical conectando os marcos da timeline -->
              <div v-if="idx < plan.milestones.length - 1" class="timeline-line" style="position: absolute; left: 11px; top: 28px; bottom: -20px; width: 2px; background: var(--border-light);"></div>
              
              <!-- Timeline circle indicator -->
              <div class="timeline-indicator" style="position: absolute; left: 0; top: 4px; width: 24px; height: 24px; border-radius: 50%; background: var(--bg-surface-elevated); border: 2px solid var(--accent-primary); display: flex; align-items: center; justify-content: center; font-size: 0.75rem; font-weight: bold; color: var(--text-primary);">
                {{ idx + 1 }}
              </div>
              
              <h4 style="font-size: 1.25rem; font-weight: 700; margin-bottom: 0.75rem; color: white;">
                {{ milestone.name }}
              </h4>

              <!-- Sessions for this milestone -->
              <div class="sessions-container" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1rem; margin-top: 1rem;">
                <div v-for="session in milestone.sessions" :key="session.id" class="session-card" style="background: rgba(255, 255, 255, 0.02); border: 1px solid var(--border-light); border-radius: var(--radius-md); padding: 1.25rem; display: flex; flex-direction: column; justify-content: space-between; gap: 1rem;">
                  <div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                      <span class="session-type-badge" :style="{ background: session.type === 'Força' ? 'rgba(239, 68, 68, 0.1)' : 'rgba(16, 185, 129, 0.1)', color: session.type === 'Força' ? '#ef4444' : '#10b981', border: session.type === 'Força' ? '1px solid rgba(239, 68, 68, 0.2)' : '1px solid rgba(16, 185, 129, 0.2)', padding: '2px 8px', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 'bold' }">
                        {{ session.type }}
                      </span>
                      <span style="font-size: 0.8rem; color: var(--text-tertiary);">Semana {{ session.week }}</span>
                    </div>

                    <h5 style="font-size: 1.05rem; margin-bottom: 0.5rem; color: white;">{{ session.name }}</h5>
                    <p style="font-size: 0.85rem; color: var(--text-secondary); line-height: 1.4;">
                      <strong>Exercício Foco:</strong> <span style="color: var(--accent-primary-hover)">{{ session.exercise }}</span>
                    </p>
                    <p style="font-size: 0.85rem; color: var(--text-tertiary); line-height: 1.4; margin-top: 0.5rem;">
                      <strong>Progressão:</strong> {{ session.progression }}
                    </p>
                  </div>

                  <button 
                    @click="openPlannerWithExercise(session.exercise)" 
                    class="btn-primary" 
                    style="width: 100%; padding: 10px 12px; font-size: 0.85rem; display: flex; align-items: center; justify-content: center; gap: 0.5rem; border-radius: var(--radius-sm);"
                  >
                    <span>⚡ Abrir Sessão de Treino</span>
                  </button>
                </div>
              </div>
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

.header-actions {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.free-btn {
  border-color: rgba(255, 255, 255, 0.2);
  color: white;
}

.free-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: white;
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

/* Tabs Navigation */
.tabs-nav {
  display: flex;
  gap: 1rem;
  padding: 8px;
  margin-bottom: 2rem;
  background: rgba(255, 255, 255, 0.02);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-light);
}

.tab-btn {
  flex: 1;
  padding: 12px;
  border-radius: var(--radius-sm);
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text-secondary);
  transition: all var(--transition-fast);
}

.tab-btn:hover {
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.02);
}

.tab-btn.is-active {
  color: #10b981;
  background: rgba(16, 185, 129, 0.08);
  box-shadow: inset 0 0 10px rgba(16, 185, 129, 0.05);
}

/* Progression Layout */
.progression-layout {
  display: grid;
  grid-template-columns: 2.2fr 1fr;
  gap: 2rem;
  align-items: start;
}

@media (max-width: 1024px) {
  .progression-layout {
    grid-template-columns: 1fr;
  }
}

.area-block {
  margin-bottom: 2rem;
  padding: 1.5rem;
  background: rgba(255, 255, 255, 0.01);
  border: 1px solid rgba(255, 255, 255, 0.03);
}

.area-title {
  font-size: 1.25rem;
  color: var(--text-primary);
  margin-bottom: 1.5rem;
  border-left: 4px solid #10b981;
  padding-left: 0.75rem;
}

.tree-columns {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 1.5rem;
}

@media (max-width: 768px) {
  .tree-columns {
    grid-template-columns: 1fr;
    gap: 2rem;
  }
}

.tree-column {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.column-level {
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  margin-bottom: 0.5rem;
}

.column-level.iniciante { color: #10b981; }
.column-level.intermediario { color: #f59e0b; }
.column-level.avancado { color: #ef4444; }

.nodes-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.node-card {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 12px;
  background: rgba(0, 0, 0, 0.25);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
  position: relative;
}

.node-card:hover {
  transform: translateY(-2px);
  border-color: rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.03);
}

.node-card.is-selected {
  border-color: #10b981 !important;
  background: rgba(16, 185, 129, 0.05);
  box-shadow: 0 0 12px rgba(16, 185, 129, 0.15);
}

.node-indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.node-card.completed .node-indicator {
  background: #10b981;
  box-shadow: 0 0 8px #10b981;
}

.node-card.unlocked .node-indicator {
  background: #f59e0b;
  box-shadow: 0 0 8px #f59e0b;
}

.node-card.locked .node-indicator {
  background: var(--text-tertiary);
}

.node-card.locked {
  opacity: 0.6;
}

.node-name {
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Details Panel */
.details-panel-container {
  position: sticky;
  top: 2rem;
}

.node-details-card {
  padding: 1.5rem;
  background: rgba(139, 92, 246, 0.02);
  border-color: rgba(139, 92, 246, 0.15);
  box-shadow: var(--shadow-lg);
}

.details-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  padding-bottom: 0.75rem;
}

.details-header h3 {
  font-size: 1.25rem;
  color: var(--text-primary);
}

.badge-status {
  padding: 3px 10px;
  border-radius: var(--radius-full);
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
}

.badge-status.completed {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
  border: 1px solid rgba(16, 185, 129, 0.2);
}

.badge-status.unlocked {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
  border: 1px solid rgba(245, 158, 11, 0.2);
}

.badge-status.locked {
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-secondary);
  border: 1px solid var(--border-light);
}

.details-desc {
  font-size: 0.9rem;
  color: var(--text-secondary);
  line-height: 1.5;
  margin-bottom: 1.25rem;
}

.details-meta-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  background: rgba(0, 0, 0, 0.15);
  padding: 1rem;
  border-radius: var(--radius-sm);
  margin-bottom: 1.25rem;
  border: 1px solid rgba(255, 255, 255, 0.03);
}

.meta-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.meta-label {
  font-size: 0.75rem;
  color: var(--text-tertiary);
  font-weight: 500;
}

.meta-value {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-primary);
}

.badge-level-text {
  text-transform: capitalize;
}
.badge-level-text.iniciante { color: #10b981; }
.badge-level-text.intermediário { color: #f59e0b; }
.badge-level-text.avanço, .badge-level-text.avancado { color: #ef4444; }

.details-section-info {
  margin-bottom: 1.25rem;
}

.details-subtitle {
  display: block;
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--text-secondary);
  margin-bottom: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 0.02em;
}

.badge-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.badge-req-item, .badge-unl-item {
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--border-light);
  color: var(--text-secondary);
}

.badge-req-item.is-completed {
  background: rgba(16, 185, 129, 0.08);
  border-color: rgba(16, 185, 129, 0.2);
  color: #10b981;
}

.badge-unl-item {
  background: rgba(139, 92, 246, 0.05);
  border-color: rgba(139, 92, 246, 0.2);
  color: #a78bfa;
}

.details-suggestion {
  display: flex;
  gap: 0.5rem;
  margin-top: 1rem;
  padding: 1rem;
  background: rgba(16, 185, 129, 0.03);
  border-left: 3px solid #10b981;
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
}

.suggestion-icon {
  font-size: 1rem;
}

.details-suggestion p {
  margin: 0;
  font-size: 0.8rem;
  color: var(--text-primary);
  line-height: 1.4;
}

.start-plan-btn {
  font-weight: 700;
  letter-spacing: 0.02em;
  transition: all var(--transition-normal);
}

.advanced-glow {
  background: linear-gradient(135deg, #ef4444 0%, #d946ef 100%) !important;
  box-shadow: 0 0 15px rgba(239, 68, 68, 0.35) !important;
}

.advanced-glow:hover {
  box-shadow: 0 0 25px rgba(239, 68, 68, 0.6) !important;
  transform: translateY(-2px);
}
</style>
