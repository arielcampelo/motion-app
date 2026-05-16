<script setup>
import { ref, computed, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useWorkoutStore } from '../../store/workout'
import { audioService } from '../../utils/audio'

const router = useRouter()
const store = useWorkoutStore()

const session = ref(store.activeSession)
if (!session.value) router.push('/modality/escalada')

// Build blocks from planned exercises
const blocks = ref(
  (session.value?.exercises || []).map(ex => ({
    ...ex,
    id: ex.id || Date.now() + Math.random(),
    topsHit: 0,
    attemptsUsed: 0,
    state: 'idle' // idle | done
  }))
)

const totalTops = computed(() => blocks.value.reduce((a, b) => a + b.topsHit, 0))
const maxGrade = computed(() => {
  const done = blocks.value.filter(b => b.topsHit > 0)
  return done.length ? done[done.length - 1].grade : '--'
})

const addTop = (block) => {
  if (block.topsHit < block.tops) {
    block.topsHit++
    audioService.beep(1200, 300)
    if (block.topsHit >= block.tops) block.state = 'done'
  }
}

const addAttempt = (block) => {
  block.attemptsUsed++
}

const markSkipped = (block) => {
  block.state = 'done'
}

// Add a quick ad-hoc route during the session
const showAddRoute = ref(false)
const newRoute = ref({ type: 'Boulder', grade: 'V1', tops: 1 })
const addAdHocRoute = () => {
  blocks.value.push({
    id: Date.now(),
    type: newRoute.value.type,
    grade: newRoute.value.grade,
    tops: newRoute.value.tops,
    attempts: 5,
    topsHit: 0,
    attemptsUsed: 0,
    state: 'idle'
  })
  showAddRoute.value = false
  newRoute.value = { type: 'Boulder', grade: 'V1', tops: 1 }
}

const finishSession = () => {
  const doneBlocks = blocks.value.filter(b => b.topsHit > 0 || b.attemptsUsed > 0)
  const tops = doneBlocks.reduce((a, b) => a + b.topsHit, 0)
  const grades = doneBlocks.filter(b => b.topsHit > 0).map(b => b.grade)
  const maxG = grades.length ? grades[grades.length - 1] : '--'

  store.addWorkout({
    name: session.value.name,
    modalityId: 'escalada',
    details: {
      tops,
      maxGrade: maxG,
      blocks: doneBlocks
    }
  })

  audioService.speak('Sessão finalizada! Bom trabalho!')
  store.activeSession = null
  router.push('/modality/escalada')
}

const typeEmoji = (type) => ({ Boulder: '🪨', 'Top Rope': '🧗', Guiada: '📌', 'Campus Board': '🏋️' }[type] || '🧗')
</script>

<template>
  <div v-if="session" class="container animate-fade-in">

    <!-- Header -->
    <header class="climb-header">
      <div>
        <h2>{{ session.name }}</h2>
        <p class="header-meta">⛰️ {{ totalTops }} tops · Max: {{ maxGrade }}</p>
      </div>
      <button class="btn-primary finish-btn" @click="finishSession">Finalizar</button>
    </header>

    <!-- Route blocks -->
    <div class="blocks-list">
      <div
        v-for="block in blocks"
        :key="block.id"
        class="route-card glass-panel"
        :class="{ 'is-done': block.state === 'done' }"
      >
        <div class="route-header">
          <span class="route-emoji">{{ typeEmoji(block.type) }}</span>
          <div class="route-info">
            <h3>{{ block.type }} <span class="grade-badge">{{ block.grade }}</span></h3>
            <p class="route-meta">Alvo: {{ block.tops }} top{{ block.tops > 1 ? 's' : '' }}</p>
          </div>
          <span v-if="block.state === 'done'" class="done-check">✅</span>
        </div>

        <div v-if="block.state !== 'done'" class="route-actions">
          <div class="counters">
            <div class="counter-box">
              <div class="counter-val">{{ block.topsHit }}</div>
              <div class="counter-lbl">tops</div>
            </div>
            <div class="counter-sep">/</div>
            <div class="counter-box dim">
              <div class="counter-val">{{ block.attemptsUsed }}</div>
              <div class="counter-lbl">tent.</div>
            </div>
          </div>

          <div class="action-btns">
            <button class="btn-top" @click="addTop(block)">🏆 Top!</button>
            <button class="btn-attempt" @click="addAttempt(block)">💪 Tentativa</button>
            <button class="btn-skip" @click="markSkipped(block)">Pular →</button>
          </div>
        </div>

        <div v-else class="done-summary">
          <span>{{ block.topsHit }} tops</span>
          <span>{{ block.attemptsUsed }} tentativas</span>
        </div>
      </div>
    </div>

    <!-- Add ad-hoc route -->
    <div v-if="showAddRoute" class="add-route-form glass-panel">
      <h3>+ Nova Via</h3>
      <div class="form-row">
        <div class="form-group">
          <label>Tipo</label>
          <select v-model="newRoute.type" class="input-field">
            <option>Boulder</option>
            <option>Top Rope</option>
            <option>Guiada</option>
          </select>
        </div>
        <div class="form-group">
          <label>Grau</label>
          <input v-model="newRoute.grade" type="text" class="input-field" placeholder="V3" />
        </div>
        <div class="form-group">
          <label>Tops</label>
          <input v-model.number="newRoute.tops" type="number" min="1" class="input-field" />
        </div>
      </div>
      <div class="form-actions">
        <button class="btn-outline cancel-btn" @click="showAddRoute = false">Cancelar</button>
        <button class="btn-primary amber-btn" @click="addAdHocRoute">Adicionar</button>
      </div>
    </div>

    <button v-else class="btn-outline add-btn" @click="showAddRoute = true">
      + Adicionar Via Avulsa
    </button>

  </div>
</template>

<style scoped>
.climb-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
  gap: 1rem;
  flex-wrap: wrap;
}
.climb-header h2 { font-size: 1.4rem; margin-bottom: 0.2rem; }
.header-meta { font-size: 0.9rem; color: var(--text-secondary); }

.finish-btn {
  background: #f59e0b;
  box-shadow: 0 4px 15px rgba(245,158,11,0.4);
}

/* Blocks */
.blocks-list { display: flex; flex-direction: column; gap: 1rem; margin-bottom: 1.5rem; }

.route-card { padding: 1.5rem; transition: all 0.3s; }
.route-card.is-done { opacity: 0.6; }

.route-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.2rem;
}
.route-emoji { font-size: 1.8rem; }
.route-info { flex: 1; }
.route-info h3 { font-size: 1rem; display: flex; align-items: center; gap: 0.5rem; }
.grade-badge {
  background: rgba(245,158,11,0.15);
  border: 1px solid rgba(245,158,11,0.3);
  border-radius: 99px;
  padding: 2px 10px;
  font-size: 0.85rem;
  color: #fbbf24;
  font-weight: 700;
}
.route-meta { font-size: 0.82rem; color: var(--text-tertiary); margin-top: 2px; }
.done-check { font-size: 1.3rem; }

/* Actions */
.route-actions { display: flex; flex-direction: column; gap: 1rem; }

.counters {
  display: flex;
  align-items: center;
  gap: 1rem;
  justify-content: center;
}
.counter-box { text-align: center; }
.counter-val { font-size: 2.5rem; font-weight: 800; font-family: var(--font-heading); line-height: 1; }
.counter-lbl { font-size: 0.75rem; color: var(--text-tertiary); margin-top: 2px; }
.counter-box.dim .counter-val { color: var(--text-tertiary); font-size: 1.8rem; }
.counter-sep { font-size: 1.5rem; color: var(--text-tertiary); }

.action-btns { display: flex; gap: 0.8rem; justify-content: center; flex-wrap: wrap; }

.btn-top {
  background: #f59e0b;
  box-shadow: 0 4px 12px rgba(245,158,11,0.4);
  padding: 10px 24px;
  border-radius: var(--radius-full);
  font-weight: 700;
  color: white;
  cursor: pointer;
  border: none;
  font-size: 1rem;
  transition: all 0.2s;
}
.btn-top:hover { box-shadow: 0 6px 18px rgba(245,158,11,0.6); transform: scale(1.02); }

.btn-attempt {
  background: rgba(255,255,255,0.07);
  border: 1px solid var(--border-light);
  padding: 10px 20px;
  border-radius: var(--radius-full);
  font-weight: 600;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 0.95rem;
  transition: all 0.2s;
}
.btn-attempt:hover { background: rgba(255,255,255,0.12); }

.btn-skip {
  background: transparent;
  border: none;
  color: var(--text-tertiary);
  font-size: 0.85rem;
  cursor: pointer;
  padding: 8px 12px;
  text-decoration: underline;
}

/* Done summary */
.done-summary {
  display: flex;
  gap: 1rem;
  font-size: 0.85rem;
  color: #fbbf24;
  font-weight: 500;
}

/* Add route form */
.add-route-form {
  padding: 1.5rem;
  margin-bottom: 1rem;
}
.add-route-form h3 { margin-bottom: 1rem; font-size: 1rem; }

.form-row {
  display: grid;
  grid-template-columns: 1.5fr 1fr 0.8fr;
  gap: 1rem;
  margin-bottom: 1rem;
}
@media (max-width: 600px) {
  .form-row { grid-template-columns: 1fr 1fr; }
}
.form-group { display: flex; flex-direction: column; gap: 0.4rem; }
label { font-size: 0.82rem; color: var(--text-secondary); }
.input-field {
  background: rgba(0,0,0,0.2);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  padding: 8px 12px;
  color: var(--text-primary);
  font-size: 0.9rem;
}
.form-actions { display: flex; gap: 0.8rem; justify-content: flex-end; }

.amber-btn {
  background: #f59e0b;
  box-shadow: 0 4px 12px rgba(245,158,11,0.35);
}
.cancel-btn { color: var(--text-tertiary); }

.add-btn {
  width: 100%;
  padding: 12px;
  border: 1px dashed var(--border-light);
  border-radius: var(--radius-sm);
  color: #f59e0b;
  font-weight: 500;
  transition: all 0.2s;
}
.add-btn:hover { background: rgba(245,158,11,0.05); border-style: solid; }
</style>
