import { defineStore } from 'pinia'

export const useUserStore = defineStore('user', {
  state: () => {
    const savedUser = localStorage.getItem('motion-user')
    return {
      user: savedUser ? JSON.parse(savedUser) : {
        name: '',
        level: 'Iniciante', // Iniciante, Intermediário, Avançado
        goal: '',
        avatar: '👤'
      }
    }
  },
  actions: {
    setUser(userData) {
      this.user = { ...this.user, ...userData }
      localStorage.setItem('motion-user', JSON.stringify(this.user))
    }
  }
})
