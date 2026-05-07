<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useWorkoutStore } from '../../store/workout'

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

const expandedId = ref(null)
let timerInterval = null

const toggleExpand = (id) => {
  if (expandedId.value === id) {
    expandedId.value = null
  } else {
    expandedId.value = id
  }
}

const startBlock = (block) => {
  if (block.type === 'tempo') {
    block.state = 'countdown'
    block.countdown = 3
    
    const countInterval = setInterval(() => {
      block.countdown--
      if (block.countdown <= 0) {
        clearInterval(countInterval)
        block.state = 'running'
        startMainTimer(block)
      }
    }, 1000)
  } else {
    block.state = 'running'
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
  expandedId.value = null
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
  store.activeSession = null
  router.push('/modality/malabarismo')
}
</script>

<template>
  <div v-if="session" class="container animate-fade-in">
    <header class="section-header">
      <h2>{{ session.name }}</h2>
      <button class="btn-primary finish-btn" @click="finishSession">Finalizar Treino</button>
    </header>

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
          
          <div v-if="block.state === 'idle'" class="action-center">
            <button class="btn-action start-btn" @click="startBlock(block)">▶ Iniciar</button>
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
</style>
