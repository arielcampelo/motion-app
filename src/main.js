import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import './style.css'
import App from './App.vue'

window.addEventListener('error', (event) => {
  document.body.innerHTML += `<div style="position:fixed;top:0;left:0;background:red;color:white;z-index:9999;padding:20px;">${event.error ? event.error.stack : event.message}</div>`;
});
window.addEventListener('unhandledrejection', (event) => {
  document.body.innerHTML += `<div style="position:fixed;top:0;left:0;background:red;color:white;z-index:9999;padding:20px;">${event.reason}</div>`;
});

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

app.mount('#app')
