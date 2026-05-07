<script setup>
import { ref, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useWorkoutStore } from '../../store/workout'
import AICamera from '../../components/AICamera.vue'

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

const expandedId = ref(null)
const useAICamera = ref(false)
const aiMode = ref('pushup')

const toggleExpand = (id) => {
  if (expandedId.value === id) {
    expandedId.value = null
    useAICamera.value = false
  } else {
    expandedId.value = id
    useAICamera.value = false
  }
}

const startBlock = (block) => {
  block.state = 'running'
  useAICamera.value = false
}

const completeBlock = (block) => {
  block.state = 'done'
  expandedId.value = null
  useAICamera.value = false
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
  store.activeSession = null
  router.push('/modality/calistenia')
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
          <div v-if="block.state === 'idle'" class="action-center">
            <button class="btn-action start-btn" @click="startBlock(block)">▶ Iniciar Série</button>
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
                  :active="true" 
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
</style>
