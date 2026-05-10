<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../store/user'

const router = useRouter()
const userStore = useUserStore()

const name = ref('')
const level = ref('Iniciante')
const goal = ref('')

const saveProfile = () => {
  if (!name.value) return alert('Por favor, digite seu nome.')
  
  userStore.setUser({
    name: name.value,
    level: level.value,
    goal: goal.value
  })
  
  router.push('/')
}
</script>

<template>
  <div class="container onboarding-container animate-fade-in">
    <div class="onboarding-card glass-panel">
      <header class="onboarding-header">
        <div class="logo-icon-large"></div>
        <h1>Bem-vindo ao Motion</h1>
        <p>Vamos configurar seu perfil de atleta</p>
      </header>

      <form @submit.prevent="saveProfile" class="onboarding-form">
        <div class="form-group">
          <label>Como podemos te chamar?</label>
          <input v-model="name" type="text" placeholder="Seu nome" class="input-field" required />
        </div>

        <div class="form-group">
          <label>Qual seu nível atual?</label>
          <div class="level-selector">
            <button 
              v-for="l in ['Iniciante', 'Intermediário', 'Avançado']" 
              :key="l"
              type="button"
              :class="{ active: level === l }"
              @click="level = l"
            >
              {{ l }}
            </button>
          </div>
        </div>

        <div class="form-group">
          <label>Qual seu objetivo principal?</label>
          <input v-model="goal" type="text" placeholder="Ex: Ganhar força, consistência..." class="input-field" />
        </div>

        <button type="submit" class="btn-primary full-width">Começar Jornada</button>
      </form>
    </div>
  </div>
</template>

<style scoped>
.onboarding-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 80vh;
}

.onboarding-card {
  max-width: 450px;
  width: 100%;
  padding: 3rem;
  text-align: center;
}

.onboarding-header {
  margin-bottom: 2.5rem;
}

.logo-icon-large {
  width: 64px;
  height: 64px;
  background: var(--accent-gradient);
  border-radius: 16px;
  margin: 0 auto 1.5rem;
  box-shadow: 0 10px 25px rgba(139, 92, 246, 0.4);
}

h1 {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

p {
  color: var(--text-secondary);
}

.onboarding-form {
  text-align: left;
}

.form-group {
  margin-bottom: 1.5rem;
}

label {
  display: block;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-tertiary);
  margin-bottom: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.input-field {
  width: 100%;
  background: rgba(255,255,255,0.03);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  padding: 12px 16px;
  color: white;
  font-size: 1rem;
}

.input-field:focus {
  outline: none;
  border-color: var(--accent-primary);
}

.level-selector {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.5rem;
}

.level-selector button {
  padding: 10px 5px;
  background: rgba(255,255,255,0.03);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  font-size: 0.8rem;
  font-weight: 600;
}

.level-selector button.active {
  background: var(--accent-primary);
  border-color: var(--accent-primary);
  color: white;
}

.full-width {
  width: 100%;
  margin-top: 1rem;
}
</style>
