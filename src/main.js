import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import './style.css'
import App from './App.vue'

window.addEventListener('error', (event) => {
  console.error('Global Error:', event.error || event.message)
})
window.addEventListener('unhandledrejection', (event) => {
  console.error('Unhandled Rejection:', event.reason)
})

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

app.mount('#app')
