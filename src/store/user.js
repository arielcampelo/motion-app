import { defineStore } from 'pinia'

export const useUserStore = defineStore('user', {
  state: () => {
    let user = {
      name: '',
      level: 'Iniciante',
      goal: '',
      avatar: '👤'
    }
    
    try {
      const savedUser = localStorage.getItem('motion-user')
      if (savedUser && savedUser !== 'undefined') {
        user = { ...user, ...JSON.parse(savedUser) }
      }
    } catch (e) {
      console.warn('Erro ao carregar usuário do localStorage:', e)
    }

    return { user }
  },
  actions: {
    setUser(userData) {
      this.user = { ...this.user, ...userData }
      localStorage.setItem('motion-user', JSON.stringify(this.user))
    }
  }
})
