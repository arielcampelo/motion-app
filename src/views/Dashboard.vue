<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useWorkoutStore } from '../store/workout'

const store = useWorkoutStore()
const router = useRouter()

const modalities = computed(() => store.modalities)

const navigateToModality = (id) => {
  router.push(`/modality/${id}`)
}
</script>

<template>
  <div class="container animate-fade-in">
    <header class="dashboard-header">
      <div class="logo-text">
        <span class="motion-text">Motion</span>
      </div>
      <button class="btn-stats glass-panel" @click="router.push('/statistics')">
        <span class="icon">📊</span>
        <span>Estatísticas</span>
      </button>
    </header>

    <section class="modalities-section">
      <div class="modality-grid">
        <div 
          v-for="mod in modalities" 
          :key="mod.id" 
          class="modality-card glass-panel"
          @click="navigateToModality(mod.id)"
          :style="{ '--mod-color': mod.color }"
        >
          <div class="mod-icon-wrapper">
            <span class="mod-icon">{{ mod.icon }}</span>
          </div>
          <div class="mod-info">
            <h3>{{ mod.name }}</h3>
            <p>{{ mod.desc }}</p>
          </div>
          <div class="mod-arrow">→</div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 3rem;
  margin-top: 2rem;
}

.btn-stats {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 20px;
  font-weight: 600;
  color: var(--text-primary);
  border: 1px solid var(--border-light);
  transition: all var(--transition-normal);
}

.btn-stats:hover {
  background: rgba(255, 255, 255, 0.05);
  transform: translateY(-2px);
  border-color: var(--accent-primary);
}

@media (max-width: 600px) {
  .dashboard-header {
    flex-direction: column;
    gap: 1.5rem;
  }
  .btn-stats {
    width: 100%;
    justify-content: center;
  }
}

.motion-text {
  font-size: 2.5rem;
  font-weight: 800;
  font-family: var(--font-heading);
  background: var(--accent-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  letter-spacing: -0.04em;
}

.modality-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 1.5rem;
}

@media (max-width: 600px) {
  .greeting {
    font-size: 2.2rem;
  }
  .modality-grid {
    grid-template-columns: 1fr;
  }
  .modality-card {
    padding: 1.25rem;
  }
}

.modality-card {
  display: flex;
  align-items: center;
  padding: 1.5rem;
  cursor: pointer;
  transition: all var(--transition-normal);
  position: relative;
  overflow: hidden;
}

.modality-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: radial-gradient(circle at top right, var(--mod-color) 0%, transparent 70%);
  opacity: 0.05;
  transition: opacity var(--transition-normal);
}

.modality-card:hover {
  transform: translateY(-5px);
  box-shadow: var(--shadow-lg);
  border-color: rgba(255, 255, 255, 0.15);
}

.modality-card:hover::before {
  opacity: 0.15;
}

.mod-icon-wrapper {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  background: rgba(255,255,255,0.05);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  margin-right: 1.5rem;
  border: 1px solid rgba(255,255,255,0.05);
  box-shadow: 0 4px 10px rgba(0,0,0,0.2);
}

.mod-info {
  flex: 1;
}

.mod-info h3 {
  font-size: 1.3rem;
  margin-bottom: 0.25rem;
  color: var(--text-primary);
}

.mod-info p {
  font-size: 0.9rem;
  color: var(--text-tertiary);
}

.mod-arrow {
  font-size: 1.5rem;
  color: var(--text-tertiary);
  opacity: 0;
  transform: translateX(-10px);
  transition: all var(--transition-normal);
}

.modality-card:hover .mod-arrow {
  opacity: 1;
  transform: translateX(0);
  color: var(--mod-color);
}
</style>
