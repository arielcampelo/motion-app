import { defineStore } from 'pinia'
import jugglingTricks from '../data/juggling_tricks.json'

export const useWorkoutStore = defineStore('workout', {
  state: () => {
    const savedWorkouts = localStorage.getItem('motion-workouts')
    return {
      workouts: savedWorkouts ? JSON.parse(savedWorkouts) : [],
      activeSession: null,
      modalities: [
        { id: 'calistenia', name: 'Calistenia', icon: '🤸‍♂️', color: '#10b981', desc: 'Séries, repetições e peso corporal' },
        { id: 'malabarismo', name: 'Malabarismo', icon: '🤹', color: '#8b5cf6', desc: 'Bolas, claves e truques' },
        { id: 'escalada', name: 'Escalada', icon: '🧗', color: '#f59e0b', desc: 'Graus (V-scale), tops e tentativas' },
        { id: 'natacao', name: 'Natação', icon: '🏊‍♂️', color: '#3b82f6', desc: 'Distância, tempo e estilos' }
      ],
      exercises: {
        'malabarismo': { bolas: jugglingTricks.bolas, claves: jugglingTricks.claves },
        'calistenia': {
          superior: ['Flexão', 'Flexão Inclinada', 'Barra Fixa', 'Barra (Pendurado)', 'Barra Australiana', 'Suporte nas Argolas', 'Muscle Up', 'Dips', 'Front Lever', 'Planche'],
          core: ['L-Sit', 'Prancha', 'Dragon Flag', 'Hollow Body', 'Abdominal Infra'],
          inferior: ['Agachamento (Squat)', 'Pistol Squat', 'Bulgarian Split Squat', 'Nordic Curl'],
          cardio: ['Polichinelo', 'Burpee', 'Montanha Alpinista']
        },
        'escalada': ['Boulder', 'Top Rope', 'Guiada', 'Campus Board'],
        'natacao': ['Crawl (Livre)', 'Costas', 'Peito', 'Borboleta']
      },
      savedTemplates: savedWorkouts ? (JSON.parse(localStorage.getItem('motion-templates')) || []) : []
    }
  },
  actions: {
    addWorkout(workout) {
      workout.id = Date.now()
      workout.date = new Date().toISOString()
      this.workouts.unshift(workout)
      localStorage.setItem('motion-workouts', JSON.stringify(this.workouts))
    },
    saveTemplate(template) {
      template.id = Date.now()
      this.savedTemplates.push(template)
      localStorage.setItem('motion-templates', JSON.stringify(this.savedTemplates))
    }
  }
})
