import { ref, computed, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useWorkoutStore } from '../../store/workout'
import { useUserStore } from '../../store/user'
import AICamera from '../../components/AICamera.vue'
import { audioService } from '../../utils/audio'

const router = useRouter()
const store = useWorkoutStore()

const session = ref(store.activeSession)

if (!session.value) {
  router.push('/modality/calistenia')
}

// Transform exercises with sets into individual blocks
const sessionBlocks = ref([])

if (session.value) {
  session.value.exercises.forEach((ex) => {
    for (let i = 0; i < ex.sets; i++) {
      sessionBlocks.value.push({
        id: `${ex.id}-${i}`,
        originalId: ex.id,
        name: ex.name,
        area: ex.area,
        reps: ex.reps,
        weight: ex.weight,
        setNumber: i + 1,
        totalSets: ex.sets,
        state: 'idle', // idle, running, done
      })
    }
  })
}

// Drag and drop
const draggedItem = ref(null)
const onDragStart = (index) => { draggedItem.value = index }
const onDragOver = (e) => { e.preventDefault() }
const onDrop = (index) => {
  const item = sessionBlocks.value.splice(draggedItem.value, 1)[0]
  sessionBlocks.value.splice(index, 0, item)
  draggedItem.value = null
}

const userStore = useUserStore()
const currentBlockIndex = ref(0)
const isPaused = ref(false)
const isResting = ref(false)
const restTimeLeft = ref(0)
let restInterval = null

const expandedId = ref(null)
const useAICamera = ref(false)
const aiMode = ref('pushup')

// Rest duration based on user level
const getRestDuration = () => {
  const level = userStore.user.level
  if (level === 'Avançado') return 30
  if (level === 'Intermediário') return 45
  return 60
}

const toggleExpand = (id) => {
  if (expandedId.value === id) {
    expandedId.value = null
    useAICamera.value = false
  } else {
    expandedId.value = id
    useAICamera.value = false
  }
}

const startBlock = (index) => {
  if (isResting.value) stopRest()
  currentBlockIndex.value = index
  const block = sessionBlocks.value[index]
  block.state = 'running'
  expandedId.value = block.id
  useAICamera.value = false
  isPaused.value = false
  
  audioService.playStart()
}

const completeBlock = (block) => {
  block.state = 'done'
  useAICamera.value = false
  isPaused.value = false
  
  const nextIndex = sessionBlocks.value.findIndex((b, idx) => b.state === 'idle' && idx > sessionBlocks.value.indexOf(block))
  
  if (nextIndex !== -1) {
    startRest(nextIndex)
  } else {
    expandedId.value = null
  }
}

const startRest = (nextIndex) => {
  isResting.value = true
  restTimeLeft.value = getRestDuration()
  currentBlockIndex.value = nextIndex
  
  const nextBlock = sessionBlocks.value[nextIndex]
  audioService.speak(`Série concluída. Descanso de ${restTimeLeft.value} segundos. Próximo exercício: ${nextBlock.name}`)
  
  restInterval = setInterval(() => {
    if (!isPaused.value) {
      restTimeLeft.value--
      
      if (restTimeLeft.value > 0 && restTimeLeft.value <= 3) {
        audioService.playCountdown(restTimeLeft.value)
      }

      if (restTimeLeft.value <= 0) {
        stopRest()
        startBlock(nextIndex)
      }
    }
  }, 1000)
}

const stopRest = () => {
  isResting.value = false
  if (restInterval) clearInterval(restInterval)
  restInterval = null
}

const togglePause = () => {
  isPaused.value = !isPaused.value
}

const enableAICamera = (mode) => {
  aiMode.value = mode
  useAICamera.value = true
}

const onAiCountUpdated = (count) => {
  // Option: show count progressing, but AICamera already shows it
}

const finishSession = () => {
  // calculate total reps/sets for history
  const totalReps = sessionBlocks.value
    .filter(b => b.state === 'done')
    .reduce((acc, b) => acc + Number(b.reps), 0);
  
  const completedBlocks = sessionBlocks.value.filter(b => b.state === 'done');

  store.addWorkout({
    name: session.value.name,
    modalityId: 'calistenia',
    details: {
      totalSets: completedBlocks.length,
      totalReps: totalReps,
      blocks: completedBlocks
    }
  })
  audioService.speak('Treino finalizado! Parabéns pelo esforço!')
  store.activeSession = null
  router.push('/modality/calistenia')
}

onUnmounted(() => {
  stopRest()
})
</script>

<template>
  <div v-if="session" class="container animate-fade-in">
    <header class="section-header">
      <div class="header-main">
        <h2>{{ session.name }}</h2>
        <div class="session-controls">
          <button v-if="expandedId" class="btn-icon-round" :class="{ 'is-paused': isPaused }" @click="togglePause">
            {{ isPaused ? '▶' : '⏸' }}
          </button>
        </div>
      </div>
      <button class="btn-primary finish-btn" @click="finishSession">Finalizar Treino</button>
    </header>

    <div v-if="isResting" class="rest-overlay animate-fade-in">
      <div class="rest-content glass-panel">
        <span class="rest-title">Descanso Ativo</span>
        <div class="rest-timer">{{ restTimeLeft }}s</div>
        <p>Próximo: {{ sessionBlocks[currentBlockIndex]?.name }}</p>
        <button class="btn-outline" @click="restTimeLeft = 0">Pular Descanso</button>
      </div>
    </div>

    <div class="blocks-container">
      <div 
        v-for="(block, index) in sessionBlocks" 
        :key="block.id"
        class="floating-block"
        :class="{ 
          'is-expanded': expandedId === block.id,
          'is-done': block.state === 'done',
          'is-running': block.state === 'running'
        }"
        draggable="true"
        @dragstart="onDragStart(index)"
        @dragover="onDragOver"
        @drop="onDrop(index)"
      >
        <div class="block-header" @click="toggleExpand(block.id)">
          <div class="block-drag-handle">⋮⋮</div>
          <div class="block-info">
            <h3>{{ block.name }}</h3>
            <span class="block-meta">Série {{ block.setNumber }}/{{ block.totalSets }} • {{ block.reps }} reps {{ block.weight > 0 ? `+${block.weight}kg` : '' }}</span>
          </div>
          <div class="block-status">
            <span v-if="block.state === 'done'">✅</span>
            <span v-else-if="block.state === 'running'">⏳</span>
          </div>
        </div>

        <div v-if="expandedId === block.id && block.state !== 'done'" class="block-actions animate-fade-in">
          <div v-if="isPaused" class="pause-notice">
            <p>Treino Pausado</p>
            <button class="btn-primary" @click="togglePause">Retomar</button>
          </div>
          
          <div v-else-if="block.state === 'idle'" class="action-center">
            <button class="btn-action start-btn" @click="startBlock(index)">▶ Iniciar Série</button>
          </div>

          <div v-else-if="block.state === 'running'" class="action-center">
            
            <template v-if="!useAICamera">
              <div class="running-info">
                <div class="big-number">{{ block.reps }}</div>
                <div class="countdown-text">repetições</div>
              </div>
              
              <div class="buttons-row">
                <button class="btn-action complete-btn" @click="completeBlock(block)">✓ Concluir Manualmente</button>
                <button v-if="block.name.toLowerCase().includes('flexão') || block.name.toLowerCase().includes('push')" class="btn-action ai-btn" @click="enableAICamera('pushup')">🤖 Contar Flexões</button>
                <button v-if="block.name.toLowerCase().includes('polichinelo') || block.name.toLowerCase().includes('jack')" class="btn-action ai-btn" @click="enableAICamera('jumping_jack')">🤖 Contar Polichinelos</button>
              </div>
            </template>

            <template v-else>
              <div class="camera-container">
                <AICamera 
                  :active="!isPaused" 
                  :targetCount="block.reps" 
                  :mode="aiMode"
                  @completed="completeBlock(block)"
                />
              </div>
              <button class="btn-cancel" @click="useAICamera = false">Cancelar Câmera</button>
            </template>

          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  gap: 1rem;
}

.header-main {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.btn-icon-round {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: rgba(255,255,255,0.05);
  border: 1px solid var(--border-light);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  color: white;
}

.btn-icon-round.is-paused {
  background: var(--accent-primary);
  border-color: var(--accent-primary);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(139, 92, 246, 0.4); }
  70% { box-shadow: 0 0 0 10px rgba(139, 92, 246, 0); }
  100% { box-shadow: 0 0 0 0 rgba(139, 92, 246, 0); }
}

.finish-btn {
  background: #10b981;
  box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4);
}

.blocks-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.floating-block {
  background: var(--bg-surface-elevated);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-light);
  transition: all var(--transition-normal);
  overflow: hidden;
}

.floating-block:hover {
  border-color: rgba(16, 185, 129, 0.5);
  box-shadow: var(--shadow-md);
}

.floating-block.is-expanded {
  box-shadow: 0 10px 30px rgba(0,0,0,0.5);
  transform: scale(1.02);
  border-color: #10b981;
  z-index: 10;
  position: relative;
}

.floating-block.is-done {
  opacity: 0.6;
  border-color: rgba(16, 185, 129, 0.3);
}

.floating-block.is-running {
  border-color: #f59e0b;
  box-shadow: 0 0 20px rgba(245, 158, 11, 0.2);
}

.block-header {
  display: flex;
  align-items: center;
  padding: 1.5rem;
  cursor: pointer;
}

.block-drag-handle {
  color: var(--text-tertiary);
  font-size: 1.2rem;
  margin-right: 1rem;
  cursor: grab;
}

.block-info h3 {
  font-size: 1.1rem;
  margin-bottom: 0.2rem;
}

.block-meta {
  font-size: 0.85rem;
  color: var(--text-tertiary);
}

.block-status {
  margin-left: auto;
  font-size: 1.2rem;
}

.block-actions {
  padding: 0 1.5rem 1.5rem 1.5rem;
  border-top: 1px solid var(--border-subtle);
  margin-top: 0.5rem;
  padding-top: 1.5rem;
}

.action-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.running-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 1rem;
}

.btn-action {
  padding: 12px 32px;
  border-radius: var(--radius-full);
  font-size: 1.1rem;
  font-weight: 600;
  color: white;
}

.start-btn {
  background: #f59e0b;
  box-shadow: 0 4px 15px rgba(245, 158, 11, 0.4);
}

.complete-btn {
  background: #10b981;
  box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4);
}

.countdown-text {
  font-size: 1.2rem;
  color: var(--text-secondary);
}

.big-number {
  font-size: 4rem;
  font-weight: 800;
  font-family: var(--font-heading);
  line-height: 1;
  color: var(--text-primary);
}

.buttons-row {
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
  width: 100%;
}

.camera-container {
  width: 100%;
  margin-bottom: 1rem;
}

.ai-btn {
  background: #6366f1;
  box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
}

.btn-cancel {
  background: transparent;
  color: var(--text-secondary);
  border: none;
  font-size: 0.9rem;
  padding: 8px;
  cursor: pointer;
  margin-top: 0.5rem;
  text-decoration: underline;
}

.rest-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 17, 21, 0.9);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  backdrop-filter: blur(8px);
}

.rest-content {
  max-width: 400px;
  width: 100%;
  padding: 3rem;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
  border-color: var(--accent-secondary);
}

.rest-title {
  text-transform: uppercase;
  letter-spacing: 0.1em;
  font-size: 0.9rem;
  color: var(--accent-secondary);
  font-weight: 700;
}

.rest-timer {
  font-size: 5rem;
  font-weight: 800;
  font-family: var(--font-heading);
  line-height: 1;
}

.pause-notice {
  text-align: center;
  padding: 2rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.pause-notice p {
  font-size: 1.2rem;
  color: var(--text-secondary);
}
</style>
