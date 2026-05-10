import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '../store/user'
import Dashboard from '../views/Dashboard.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/onboarding',
      name: 'onboarding',
      component: () => import('../views/Onboarding.vue')
    },
    {
      path: '/',
      name: 'dashboard',
      component: Dashboard
    },
    {
      path: '/statistics',
      name: 'statistics',
      component: () => import('../views/Statistics.vue')
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
      path: '/modality/escalada/planner',
      name: 'escalada-planner',
      component: () => import('../views/escalada/ClimbingPlanner.vue')
    },
    {
      path: '/modality/natacao/planner',
      name: 'natacao-planner',
      component: () => import('../views/natacao/SwimmingPlanner.vue')
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

router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  const hasUser = !!userStore.user.name

  if (to.name !== 'onboarding' && !hasUser) {
    next({ name: 'onboarding' })
  } else if (to.name === 'onboarding' && hasUser) {
    next({ name: 'dashboard' })
  } else {
    next()
  }
})

export default router
