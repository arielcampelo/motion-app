import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useWorkoutStore } from '../../store/workout'
import { useUserStore } from '../../store/user'
import { audioService } from '../../utils/audio'

const router = useRouter()
const store = useWorkoutStore()

const session = ref(store.activeSession)

if (!session.value) {
  router.push('/modality/malabarismo')
}

// Transform exercises with sets into individual blocks for the session
const sessionBlocks = ref([])

if (session.value) {
  session.value.exercises.forEach((ex, exIndex) => {
    for (let i = 0; i < ex.sets; i++) {
      sessionBlocks.value.push({
        id: `${ex.id}-${i}`,
        originalId: ex.id,
        name: ex.name,
        type: ex.type,
        target: ex.target,
        setNumber: i + 1,
        totalSets: ex.sets,
        state: 'idle', // idle, countdown, running, pending_confirmation, done
        countdown: 3, // prep time
        timeLeft: ex.target,
        order: sessionBlocks.value.length
      })
    }
  })
}

// Drag and drop logic
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
let timerInterval = null

const getRestDuration = () => {
  const level = userStore.user.level
  if (level === 'Avançado') return 15 // Juggling needs less rest
  if (level === 'Intermediário') return 25
  return 40
}

const toggleExpand = (id) => {
  if (expandedId.value === id) {
    expandedId.value = null
  } else {
    expandedId.value = id
  }
}

const startBlock = (index) => {
  if (isResting.value) stopRest()
  currentBlockIndex.value = index
  const block = sessionBlocks.value[index]
  expandedId.value = block.id
  isPaused.value = false

  if (block.type === 'tempo') {
    block.state = 'countdown'
    block.countdown = 3
    audioService.speak(`Preparar para ${block.name}`)
    
    const countInterval = setInterval(() => {
      if (!isPaused.value) {
        audioService.playCountdown(block.countdown)
        block.countdown--
        if (block.countdown <= 0) {
          clearInterval(countInterval)
          block.state = 'running'
          audioService.playStart()
          startMainTimer(block)
        }
      }
    }, 1000)
  } else {
    block.state = 'running'
    audioService.playStart()
  }
}

const startMainTimer = (block) => {
  timerInterval = setInterval(() => {
    block.timeLeft--
    if (block.timeLeft <= 0) {
      clearInterval(timerInterval)
      block.state = 'pending_confirmation'
    }
  }, 1000)
}

const completeBlock = (block) => {
  if (timerInterval) clearInterval(timerInterval)
  block.state = 'done'
  
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
  audioService.speak(`Concluído. Recuperação de ${restTimeLeft.value} segundos. Próximo: ${nextBlock.name}`)
  
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

const formatTime = (seconds) => {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

onUnmounted(() => {
  if (timerInterval) clearInterval(timerInterval)
})

const finishSession = () => {
  store.addWorkout({
    name: session.value.name,
    modalityId: 'malabarismo',
    details: {
      blocks: sessionBlocks.value,
      completed: sessionBlocks.value.filter(b => b.state === 'done').length
    }
  })
  audioService.speak('Sessão finalizada! Ótimo treino!')
  store.activeSession = null
  router.push('/modality/malabarismo')
}
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
        <span class="rest-title">Recuperação</span>
        <div class="rest-timer">{{ restTimeLeft }}s</div>
        <p>Próximo: {{ sessionBlocks[currentBlockIndex]?.name }}</p>
        <button class="btn-outline" @click="restTimeLeft = 0">Pular</button>
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
          'is-running': block.state === 'running' || block.state === 'countdown'
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
            <span class="block-meta">Série {{ block.setNumber }}/{{ block.totalSets }} • {{ block.type === 'tempo' ? formatTime(block.target) : `${block.target} catches` }}</span>
          </div>
          <div class="block-status">
            <span v-if="block.state === 'done'">✅</span>
            <span v-else-if="block.state !== 'idle'">⏳</span>
          </div>
        </div>

        <div v-if="expandedId === block.id && block.state !== 'done'" class="block-actions animate-fade-in">
          
          <div v-if="isPaused" class="pause-notice">
            <p>Sessão Pausada</p>
            <button class="btn-primary" @click="togglePause">Retomar</button>
          </div>

          <div v-else-if="block.state === 'idle'" class="action-center">
            <button class="btn-action start-btn" @click="startBlock(index)">▶ Iniciar</button>
          </div>

          <div v-else-if="block.state === 'countdown'" class="action-center">
            <div class="countdown-text">Começando em...</div>
            <div class="big-number">{{ block.countdown }}</div>
          </div>

          <div v-else-if="block.state === 'running'" class="action-center">
            <div v-if="block.type === 'tempo'">
              <div class="big-number timer">{{ formatTime(block.timeLeft) }}</div>
            </div>
            <div v-else>
              <div class="countdown-text">Contagem Iniciada</div>
              <p class="model-hint">O modelo de visão computacional registrará os catches (Em breve)</p>
            </div>
            <button class="btn-action complete-btn" @click="completeBlock(block)">✓ Concluir</button>
          </div>

          <div v-else-if="block.state === 'pending_confirmation'" class="action-center">
            <div class="countdown-text text-accent">Tempo Esgotado!</div>
            <button class="btn-action complete-btn" @click="completeBlock(block)">✓ Confirmar Conclusão</button>
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
  border-color: rgba(139, 92, 246, 0.5);
  box-shadow: var(--shadow-md);
}

.floating-block.is-expanded {
  box-shadow: 0 10px 30px rgba(0,0,0,0.5);
  transform: scale(1.02);
  border-color: #8b5cf6;
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

.btn-action {
  padding: 12px 32px;
  border-radius: var(--radius-full);
  font-size: 1.1rem;
  font-weight: 600;
  color: white;
}

.start-btn {
  background: #8b5cf6;
  box-shadow: 0 4px 15px rgba(139, 92, 246, 0.4);
}

.complete-btn {
  background: #10b981;
  box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4);
}

.countdown-text {
  font-size: 1.2rem;
  color: var(--text-secondary);
}

.text-accent {
  color: #f59e0b;
  font-weight: bold;
}

.big-number {
  font-size: 4rem;
  font-weight: 800;
  font-family: var(--font-heading);
  line-height: 1;
  color: var(--text-primary);
}

.timer {
  font-variant-numeric: tabular-nums;
}

.model-hint {
  font-size: 0.85rem;
  color: var(--text-tertiary);
  font-style: italic;
  margin-bottom: 1rem;
}

/* Reusing shared session styles */
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
  border-color: #8b5cf6;
}

.rest-title {
  text-transform: uppercase;
  letter-spacing: 0.1em;
  font-size: 0.9rem;
  color: #8b5cf6;
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
