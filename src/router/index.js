import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: Dashboard
    },
    {
      path: '/modality/malabarismo/planner',
      name: 'malabarismo-planner',
      component: () => import('../views/malabarismo/JugglingPlanner.vue')
    },
    {
      path: '/modality/malabarismo/session/:sessionId',
      name: 'malabarismo-session',
      component: () => import('../views/malabarismo/JugglingActiveSession.vue')
    },
    {
      path: '/modality/calistenia/planner',
      name: 'calistenia-planner',
      component: () => import('../views/calistenia/CalisthenicsPlanner.vue')
    },
    {
      path: '/modality/calistenia/session/:sessionId',
      name: 'calistenia-session',
      component: () => import('../views/calistenia/CalisthenicsActiveSession.vue')
    },
    {
      path: '/modality/:id',
      name: 'modality-hub',
      component: () => import('../views/ModalityHub.vue')
    },
    {
      path: '/modality/:id/new',
      name: 'new-workout',
      component: () => import('../views/NewWorkout.vue')
    }
  ]
})

export default router
