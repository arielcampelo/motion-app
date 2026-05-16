<script setup>
import { ref, computed, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useWorkoutStore } from '../../store/workout'
import { audioService } from '../../utils/audio'
import SwimmingAICamera from '../../components/SwimmingAICamera.vue'

const router = useRouter()
const store = useWorkoutStore()

// ── AI Camera ──────────────────────────────────────────────────────────────────
const useCamera = ref(false)
const cameraLaneLength = ref(25)

const onDistanceUpdated = (dist) => {
  // keep camera distance in sync for display only
}
const onLapCompleted = ({ lap, distance }) => {
  // Audio feedback when camera detects a lap
  audioService.speak(`Comprimento ${lap}. ${distance} metros.`)
}

const session = ref(store.activeSession)

if (!session.value) {
  router.push('/modality/natacao')
}

// Build session blocks: expand reps into individual laps
const sessionBlocks = ref([])

if (session.value) {
  session.value.exercises.forEach((ex) => {
    for (let i = 0; i < ex.reps; i++) {
      sessionBlocks.value.push({
        id: `${ex.id}-${i}`,
        originalId: ex.id,
        style: ex.style,
        distance: Number(ex.distance),
        lapNumber: i + 1,
        totalLaps: ex.reps,
        rest: Number(ex.rest),
        state: 'idle', // idle | running | done
        elapsedSeconds: 0,
        pace: null // seconds per 100m, calculated after completion
      })
    }
  })
}

// ── Computed totals ──────────────────────────────────────────────────────────
const totalDistancePlanned = computed(() =>
  sessionBlocks.value.reduce((acc, b) => acc + b.distance, 0)
)
const totalDistanceDone = computed(() =>
  sessionBlocks.value
    .filter(b => b.state === 'done')
    .reduce((acc, b) => acc + b.distance, 0)
)
const progressPercent = computed(() =>
  totalDistancePlanned.value > 0
    ? Math.round((totalDistanceDone.value / totalDistancePlanned.value) * 100)
    : 0
)

// ── Active lap state ─────────────────────────────────────────────────────────
const currentBlockIndex = ref(0)
const isPaused = ref(false)
const isResting = ref(false)
const restTimeLeft = ref(0)
let restInterval = null

const expandedId = ref(null)

// Per-lap stopwatch
const lapSeconds = ref(0)
let lapInterval = null

const lapDisplay = computed(() => {
  const m = Math.floor(lapSeconds.value / 60).toString().padStart(2, '0')
  const s = (lapSeconds.value % 60).toString().padStart(2, '0')
  return `${m}:${s}`
})

const startLapTimer = () => {
  lapSeconds.value = 0
  lapInterval = setInterval(() => {
    if (!isPaused.value) lapSeconds.value++
  }, 1000)
}

const stopLapTimer = () => {
  if (lapInterval) clearInterval(lapInterval)
  lapInterval = null
}

// ── Block control ────────────────────────────────────────────────────────────
const startBlock = (index) => {
  if (isResting.value) stopRest()
  currentBlockIndex.value = index
  const block = sessionBlocks.value[index]
  block.state = 'running'
  expandedId.value = block.id
  isPaused.value = false
  stopLapTimer()
  startLapTimer()
  audioService.playStart()
}

const completeBlock = (block) => {
  stopLapTimer()
  block.state = 'done'
  block.elapsedSeconds = lapSeconds.value
  // pace = s / (distance / 100)
  block.pace = block.distance > 0
    ? Math.round(lapSeconds.value / (block.distance / 100))
    : null
  isPaused.value = false

  const nextIndex = sessionBlocks.value.findIndex(
    (b, idx) => b.state === 'idle' && idx > sessionBlocks.value.indexOf(block)
  )

  if (nextIndex !== -1) {
    startRest(nextIndex, block.rest)
  } else {
    expandedId.value = null
  }
}

const startRest = (nextIndex, restSeconds) => {
  if (!restSeconds || restSeconds <= 0) {
    startBlock(nextIndex)
    return
  }
  isResting.value = true
  restTimeLeft.value = restSeconds
  currentBlockIndex.value = nextIndex

  const nextBlock = sessionBlocks.value[nextIndex]
  audioService.speak(
    `Série concluída. Descanse ${restSeconds} segundos. Próxima: ${nextBlock.distance} metros de ${nextBlock.style}.`
  )

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

const toggleExpand = (id) => {
  expandedId.value = expandedId.value === id ? null : id
}

// ── Finish ───────────────────────────────────────────────────────────────────
const finishSession = () => {
  stopRest()
  stopLapTimer()

  const doneLaps = sessionBlocks.value.filter(b => b.state === 'done')
  const totalDistance = doneLaps.reduce((acc, b) => acc + b.distance, 0)
  const totalTime = doneLaps.reduce((acc, b) => acc + b.elapsedSeconds, 0)

  store.addWorkout({
    name: session.value.name,
    modalityId: 'natacao',
    details: {
      distance: totalDistance,
      time: Math.round(totalTime / 60),
      laps: doneLaps.length,
      blocks: doneLaps
    }
  })

  audioService.speak('Treino finalizado! Parabéns pela sessão!')
  store.activeSession = null
  router.push('/modality/natacao')
}

// ── Helpers ──────────────────────────────────────────────────────────────────
const formatPace = (seconds) => {
  if (!seconds) return '--'
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${s.toString().padStart(2, '0')}/100m`
}

const styleEmoji = (style) => {
  const map = {
    'Crawl (Livre)': '🏊',
    'Costas': '🏊‍♀️',
    'Peito': '🐸',
    'Borboleta': '🦋'
  }
  return map[style] || '🏊'
}

onUnmounted(() => {
  stopRest()
  stopLapTimer()
})
</script>

<template>
  <div v-if="session" class="swim-container animate-fade-in">

    <!-- Header -->
    <header class="swim-header">
      <div class="header-left">
        <h2>{{ session.name }}</h2>
        <div class="header-meta">
          <span class="pool-icon">🏊‍♂️</span>
          <span class="dist-label">{{ totalDistanceDone }}m / {{ totalDistancePlanned }}m</span>
        </div>
      </div>
      <div class="header-right">
        <button
          v-if="expandedId"
          class="btn-icon-round"
          :class="{ 'is-paused': isPaused }"
          @click="togglePause"
        >
          {{ isPaused ? '▶' : '⏸' }}
        </button>
        <button class="btn-primary finish-btn" @click="finishSession">Finalizar</button>
      </div>
    </header>

    <!-- Progress bar -->
    <div class="progress-bar-wrap">
      <div class="progress-bar-track">
        <div class="progress-bar-fill" :style="{ width: progressPercent + '%' }"></div>
      </div>
      <span class="progress-label">{{ progressPercent }}% concluído</span>
    </div>

    <!-- Rest overlay -->
    <div v-if="isResting" class="rest-overlay animate-fade-in">
      <div class="rest-content glass-panel">
        <span class="rest-title">💤 Descanso</span>
        <div class="rest-timer">{{ restTimeLeft }}s</div>
        <p class="rest-next">
          Próximo: {{ sessionBlocks[currentBlockIndex]?.distance }}m de
          {{ sessionBlocks[currentBlockIndex]?.style }}
        </p>
        <button class="btn-outline skip-btn" @click="restTimeLeft = 0">Pular Descanso</button>
      </div>
    </div>

    <!-- Lap blocks -->
    <div class="blocks-container">
      <div
        v-for="(block, index) in sessionBlocks"
        :key="block.id"
        class="lap-block"
        :class="{
          'is-expanded': expandedId === block.id,
          'is-done': block.state === 'done',
          'is-running': block.state === 'running'
        }"
      >
        <!-- Block header -->
        <div class="block-header" @click="toggleExpand(block.id)">
          <span class="style-emoji">{{ styleEmoji(block.style) }}</span>
          <div class="block-info">
            <h3>{{ block.style }}</h3>
            <span class="block-meta">
              Série {{ block.lapNumber }}/{{ block.totalLaps }} •
              {{ block.distance }}m
              <template v-if="block.state === 'done'">
                • ⏱ {{ formatPace(block.pace) }}
              </template>
            </span>
          </div>
          <div class="block-status">
            <span v-if="block.state === 'done'" class="status-done">✅</span>
            <span v-else-if="block.state === 'running'" class="status-running">⏳</span>
            <span v-else class="status-idle">○</span>
          </div>
        </div>

        <!-- Block expanded body -->
        <div v-if="expandedId === block.id && block.state !== 'done'" class="block-body animate-fade-in">

          <!-- Paused notice -->
          <div v-if="isPaused" class="pause-notice">
            <p>Treino Pausado</p>
            <button class="btn-primary" @click="togglePause">▶ Retomar</button>
          </div>

          <!-- Idle: start -->
          <div v-else-if="block.state === 'idle'" class="action-center">
            <div class="distance-chip">{{ block.distance }}m</div>
            <div class="style-chip">{{ block.style }}</div>
            <button class="btn-action start-btn" @click="startBlock(index)">
              ▶ Iniciar Série
            </button>
          </div>

          <!-- Running: stopwatch -->
          <div v-else-if="block.state === 'running'" class="action-center">

            <!-- AI Camera panel -->
            <div v-if="useCamera" class="camera-panel">
              <SwimmingAICamera
                :active="!isPaused"
                :lane-length="cameraLaneLength"
                @distance-updated="onDistanceUpdated"
                @lap-completed="onLapCompleted"
                @close="useCamera = false"
              />
            </div>

            <template v-else>
              <div class="swim-stopwatch">
                <div class="stopwatch-display">{{ lapDisplay }}</div>
                <div class="stopwatch-label">{{ block.distance }}m · {{ block.style }}</div>
              </div>
              <div class="wave-loader">
                <span></span><span></span><span></span><span></span><span></span>
              </div>
            </template>

            <div class="buttons-row">
              <button class="btn-action complete-btn" @click="completeBlock(block)">
                ✓ Concluir Série
              </button>
              <button v-if="!useCamera" class="btn-action cam-btn" @click="useCamera = true">
                📹 Contar com Câmera
              </button>
            </div>
          </div>

        </div>

        <!-- Done block summary -->
        <div v-if="block.state === 'done'" class="done-summary">
          <span>⏱ {{ Math.floor(block.elapsedSeconds / 60) }}m {{ block.elapsedSeconds % 60 }}s</span>
          <span>{{ formatPace(block.pace) }}</span>
        </div>

      </div>
    </div>

  </div>
</template>

<style scoped>
.swim-container {
  max-width: 700px;
  margin: 0 auto;
  padding: 1.5rem 1rem 4rem;
}

/* ── Header ── */
.swim-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.5rem;
  gap: 1rem;
  flex-wrap: wrap;
}

.header-left h2 {
  font-size: 1.4rem;
  margin-bottom: 0.3rem;
}

.header-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.pool-icon { font-size: 1.1rem; }

.header-right {
  display: flex;
  align-items: center;
  gap: 0.8rem;
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
  cursor: pointer;
  transition: all 0.2s;
}
.btn-icon-round:hover { background: rgba(255,255,255,0.1); }
.btn-icon-round.is-paused {
  background: #3b82f6;
  border-color: #3b82f6;
  animation: pulse-blue 2s infinite;
}

@keyframes pulse-blue {
  0%   { box-shadow: 0 0 0 0 rgba(59,130,246,0.5); }
  70%  { box-shadow: 0 0 0 10px rgba(59,130,246,0); }
  100% { box-shadow: 0 0 0 0 rgba(59,130,246,0); }
}

.finish-btn {
  background: #3b82f6;
  box-shadow: 0 4px 15px rgba(59,130,246,0.4);
}

/* ── Progress bar ── */
.progress-bar-wrap {
  margin-bottom: 2rem;
}
.progress-bar-track {
  height: 6px;
  background: rgba(255,255,255,0.07);
  border-radius: 99px;
  overflow: hidden;
  margin-bottom: 0.4rem;
}
.progress-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #60a5fa);
  border-radius: 99px;
  transition: width 0.6s ease;
}
.progress-label {
  font-size: 0.8rem;
  color: var(--text-tertiary);
}

/* ── Rest overlay ── */
.rest-overlay {
  position: fixed;
  inset: 0;
  background: rgba(10, 12, 20, 0.92);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  backdrop-filter: blur(10px);
}

.rest-content {
  max-width: 380px;
  width: 100%;
  padding: 3rem 2rem;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.2rem;
  border-color: #3b82f6;
  box-shadow: 0 0 40px rgba(59,130,246,0.2);
}

.rest-title {
  text-transform: uppercase;
  letter-spacing: 0.1em;
  font-size: 0.85rem;
  color: #60a5fa;
  font-weight: 700;
}

.rest-timer {
  font-size: 5.5rem;
  font-weight: 800;
  font-family: var(--font-heading);
  line-height: 1;
  color: #93c5fd;
}

.rest-next {
  color: var(--text-secondary);
  font-size: 0.95rem;
}

.skip-btn {
  border-color: rgba(59,130,246,0.4);
  color: #60a5fa;
  padding: 8px 24px;
  border-radius: var(--radius-full);
}
.skip-btn:hover { background: rgba(59,130,246,0.1); }

/* ── Lap blocks ── */
.blocks-container {
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
}

.lap-block {
  background: var(--bg-surface-elevated);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-light);
  overflow: hidden;
  transition: all 0.3s ease;
}

.lap-block:hover { border-color: rgba(59,130,246,0.4); }
.lap-block.is-running {
  border-color: #3b82f6;
  box-shadow: 0 0 20px rgba(59,130,246,0.2);
}
.lap-block.is-expanded {
  box-shadow: 0 10px 30px rgba(0,0,0,0.5);
  transform: scale(1.01);
  z-index: 10;
  position: relative;
}
.lap-block.is-done {
  opacity: 0.65;
  border-color: rgba(59,130,246,0.25);
}

.block-header {
  display: flex;
  align-items: center;
  padding: 1.2rem 1.5rem;
  cursor: pointer;
  gap: 1rem;
}

.style-emoji { font-size: 1.6rem; }

.block-info { flex: 1; }
.block-info h3 { font-size: 1rem; margin-bottom: 0.15rem; }
.block-meta { font-size: 0.82rem; color: var(--text-tertiary); }

.block-status { font-size: 1.1rem; }
.status-idle { color: var(--text-tertiary); font-size: 0.9rem; }
.status-running { animation: spin 2s linear infinite; display: inline-block; }

@keyframes spin {
  0%   { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* ── Done summary pill ── */
.done-summary {
  padding: 0.4rem 1.5rem 1rem;
  display: flex;
  gap: 1.2rem;
  font-size: 0.82rem;
  color: #60a5fa;
  font-weight: 500;
}

/* ── Block body ── */
.block-body {
  padding: 0 1.5rem 1.5rem;
  border-top: 1px solid var(--border-subtle);
  padding-top: 1.5rem;
}

.action-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.2rem;
}

.distance-chip,
.style-chip {
  background: rgba(59,130,246,0.1);
  border: 1px solid rgba(59,130,246,0.25);
  border-radius: 99px;
  padding: 6px 20px;
  font-size: 1rem;
  color: #93c5fd;
  font-weight: 600;
}

.btn-action {
  padding: 12px 36px;
  border-radius: var(--radius-full);
  font-size: 1.05rem;
  font-weight: 600;
  color: white;
  cursor: pointer;
  border: none;
  transition: all 0.2s;
}

.start-btn {
  background: #f59e0b;
  box-shadow: 0 4px 15px rgba(245,158,11,0.4);
}
.start-btn:hover { box-shadow: 0 6px 20px rgba(245,158,11,0.6); }

.complete-btn {
  background: #3b82f6;
  box-shadow: 0 4px 15px rgba(59,130,246,0.4);
}
.complete-btn:hover { box-shadow: 0 6px 20px rgba(59,130,246,0.6); }

/* ── Stopwatch ── */
.swim-stopwatch {
  text-align: center;
}

.stopwatch-display {
  font-size: 4rem;
  font-weight: 800;
  font-family: var(--font-heading);
  line-height: 1;
  color: #93c5fd;
  letter-spacing: 0.05em;
}

.stopwatch-label {
  font-size: 0.9rem;
  color: var(--text-secondary);
  margin-top: 0.4rem;
}

/* ── Wave animation ── */
.wave-loader {
  display: flex;
  align-items: flex-end;
  gap: 5px;
  height: 32px;
}

.wave-loader span {
  display: block;
  width: 8px;
  border-radius: 4px;
  background: linear-gradient(180deg, #3b82f6, #1d4ed8);
  animation: wave 1.2s ease-in-out infinite;
}

.wave-loader span:nth-child(1) { animation-delay: 0s; }
.wave-loader span:nth-child(2) { animation-delay: 0.15s; }
.wave-loader span:nth-child(3) { animation-delay: 0.3s; }
.wave-loader span:nth-child(4) { animation-delay: 0.45s; }
.wave-loader span:nth-child(5) { animation-delay: 0.6s; }

@keyframes wave {
  0%, 100% { height: 8px; opacity: 0.5; }
  50%       { height: 32px; opacity: 1; }
}

/* ── Pause notice ── */
.pause-notice {
  text-align: center;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}
.pause-notice p {
  font-size: 1.1rem;
  color: var(--text-secondary);
}

/* ── Camera panel ── */
.camera-panel {
  width: 100%;
}

.buttons-row {
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
  width: 100%;
  align-items: center;
}

.cam-btn {
  background: #6366f1;
  box-shadow: 0 4px 15px rgba(99,102,241,0.4);
  font-size: 0.9rem;
  padding: 10px 28px;
}
.cam-btn:hover { box-shadow: 0 6px 20px rgba(99,102,241,0.6); }
</style>
