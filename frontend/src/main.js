// Kompositionswurzel der UI: Adapter -> Service -> Komponenten
import { createApp } from 'vue'
import App from './App.vue'
import './style.css'
import { createHttpApi } from './adapters/httpApi'
import { createFlashcardService } from './application/flashcardService'

createApp(App)
  .provide('service', createFlashcardService(createHttpApi('/api')))
  .mount('#app')
