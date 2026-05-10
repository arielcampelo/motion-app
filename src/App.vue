<script setup>
import { ref, computed, onMounted } from 'vue'
import { RouterView } from 'vue-router'
import { useAIStore } from './store/ai'
import { useUserStore } from './store/user'
import { audioService } from './utils/audio'

const userStore = useUserStore()
const aiStore = useAIStore()
const audioMode = ref(audioService.mode)

const cycleAudioMode = () => {
  const modes = ['all', 'beeps', 'none']
  const currentIndex = modes.indexOf(audioMode.value)
  const nextIndex = (currentIndex + 1) % modes.length
  audioMode.value = modes[nextIndex]
  audioService.setMode(audioMode.value)
}

const audioIcon = computed(() => {
  if (audioMode.value === 'all') return '🔊'
  if (audioMode.value === 'beeps') return '🔔'
  return '🔇'
})

onMounted(() => {
  // Pré-carrega o modelo de IA assim que o app abre
  aiStore.initModel()
})
</script>

<template>
  <div class="app-layout">
    <nav class="navbar glass-panel">
      <div class="nav-content">
        <div class="logo">
          <div class="logo-icon"></div>
          <span>Motion</span>
        </div>
        <div class="nav-links">
          <button class="btn-audio" @click="cycleAudioMode" :title="`Som: ${audioMode}`">
            {{ audioIcon }}
          </button>
          <router-link to="/">Dashboard</router-link>
          <router-link v-if="userStore.user.name" to="/onboarding" class="profile-link">
            👤 {{ userStore.user.name }}
          </router-link>
        </div>
      </div>
    </nav>
    
    <main class="main-content">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.app-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.navbar {
  position: sticky;
  top: 0;
  z-index: 100;
  border-radius: 0;
  border-left: none;
  border-right: none;
  border-top: none;
  background: rgba(26, 29, 36, 0.85);
}

.nav-content {
  max-width: 1000px;
  margin: 0 auto;
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

@media (max-width: 600px) {
  .nav-content {
    padding: 1rem;
  }
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  font-family: var(--font-heading);
  font-weight: 800;
  font-size: 1.5rem;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}

.logo-icon {
  width: 32px;
  height: 32px;
  background: var(--accent-gradient);
  border-radius: 8px;
  position: relative;
  overflow: hidden;
}

.logo-icon::after {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: linear-gradient(to bottom right, rgba(255,255,255,0.4) 0%, transparent 50%);
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 24px;
}

.nav-links a {
  font-weight: 500;
  color: var(--text-secondary);
  transition: color var(--transition-fast);
}

.nav-links a:hover, .nav-links a.router-link-active {
  color: var(--text-primary);
}

.nav-links a.btn-primary {
  color: white;
}

.btn-audio {
  background: none;
  border: none;
  font-size: 1.2rem;
  padding: 8px;
  cursor: pointer;
  filter: grayscale(1);
  transition: filter 0.3s;
}

.btn-audio:hover {
  filter: grayscale(0);
}

.profile-link {
  background: rgba(255, 255, 255, 0.05);
  padding: 6px 12px;
  border-radius: var(--radius-full);
  font-size: 0.85rem;
  border: 1px solid var(--border-light);
}

.main-content {
  flex: 1;
}
</style>
