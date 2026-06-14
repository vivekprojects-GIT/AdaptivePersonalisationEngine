import { createApp } from 'vue'
import './styles/globals.css'
import App from './App.vue'
import router from './router'
import { initThemeMode } from './lib/theme'
import { vReveal } from './lib/reveal'
import { vMagnet } from './lib/magnet'

initThemeMode()
createApp(App).use(router).directive('reveal', vReveal).directive('magnet', vMagnet).mount('#app')
