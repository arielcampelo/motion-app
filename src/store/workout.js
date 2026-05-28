import { defineStore } from 'pinia'
import jugglingTricks from '../data/juggling_tricks.json'
import calisthenicsOntology from '../data/calisthenics_ontology.json'

export const useWorkoutStore = defineStore('workout', {
  state: () => {
    const savedWorkouts = localStorage.getItem('motion-workouts')
    return {
      workouts: savedWorkouts ? JSON.parse(savedWorkouts) : [],
      activeSession: null,
      calisthenicsOntology: calisthenicsOntology,
      ontologyStatus: 'unknown', // 'unknown' | 'online' | 'fallback'
      modalities: [
        { id: 'calistenia', name: 'Calistenia', icon: '🤸‍♂️', color: '#10b981', desc: 'Séries, repetições e peso corporal' },
        { id: 'malabarismo', name: 'Malabarismo', icon: '🤹', color: '#8b5cf6', desc: 'Bolas, claves e truques' },
        { id: 'natacao', name: 'Natação', icon: '🏊‍♂️', color: '#3b82f6', desc: 'Distância, tempo e estilos', comingSoon: true }
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
      savedTemplates: savedWorkouts ? (JSON.parse(localStorage.getItem('motion-templates')) || []) : [],
      userEvaluation: null
    }
  },
  actions: {
    async loadOntology() {
      try {
        const response = await fetch('http://localhost:8085/api/exercises')
        if (response.ok) {
          this.calisthenicsOntology = await response.json()
          this.ontologyStatus = 'online'
          console.log('Ontologia carregada com sucesso do backend Python!')
        } else {
          this.ontologyStatus = 'fallback'
        }
      } catch (err) {
        console.warn('Backend Python indisponível. Usando ontologia estática como fallback.')
        this.ontologyStatus = 'fallback'
      }
    },
    async evaluateUser() {
      try {
        const response = await fetch('http://localhost:8085/api/evaluate-user', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ history: this.workouts })
        })
        if (response.ok) {
          this.userEvaluation = await response.json()
          console.log('Avaliação de progresso do usuário carregada do backend!')
          return this.userEvaluation
        }
      } catch (err) {
        console.warn('Erro ao obter avaliação do usuário no backend:', err)
      }
      return null
    },
    addWorkout(workout) {
      workout.id = Date.now()
      workout.date = new Date().toISOString()
      this.workouts.unshift(workout)
      localStorage.setItem('motion-workouts', JSON.stringify(this.workouts))
      // Atualiza avaliação de progresso após adicionar novo treino
      this.evaluateUser()
    },
    saveTemplate(template) {
      template.id = Date.now()
      this.savedTemplates.push(template)
      localStorage.setItem('motion-templates', JSON.stringify(this.savedTemplates))
    }
  }
})
