<script setup>
import { RouterView } from 'vue-router'
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
          <router-link to="/">Dashboard</router-link>
          <!-- <router-link to="/workout/new" class="btn-primary" style="padding: 8px 16px; font-size: 0.9rem;">+ Novo Treino</router-link> -->
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

.main-content {
  flex: 1;
}
</style>
