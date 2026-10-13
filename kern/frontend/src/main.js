// Kompositionswurzel der UI: Adapter -> Anwendungsschicht -> Komponenten
import { createApp } from 'vue'
import App from './App.vue'
import './style.css'
import { createAdressbuchApi } from './adapters/adressbuchApi'
import { createAufgabenleserApi } from './adapters/aufgabenleserApi'
import { createAuthApi } from './adapters/authApi'
import { createHttpApi } from './adapters/httpApi'
import { createKernApi } from './adapters/kernApi'
import { createReadingApi } from './adapters/readingApi'
import { createRegisterApi } from './adapters/registerApi'
import { createAdressbuchService } from './application/adressbuchService'
import { createAufgabenLeseService } from './application/aufgabenLeseService'
import { createAuthService } from './application/authService'
import { createFlashcardService } from './application/flashcardService'
import { createSubjectService } from './application/subjectService'
import { createReadingService } from './application/readingService'
import { createRegisterService } from './application/registerService'

createApp(App)
  .provide('auth', createAuthService(createAuthApi('/api')))
  .provide('subjects', createSubjectService(createKernApi('/api')))
  .provide('service', createFlashcardService(createHttpApi('/api/karteikarten')))
  .provide('reading', createReadingService(createReadingApi('/api/lesenachweis')))
  .provide('register', createRegisterService(createRegisterApi('/api/register')))
  .provide('adressbuch', createAdressbuchService(createAdressbuchApi('/api/adressbuch')))
  .provide('aufgabenleser', createAufgabenLeseService(createAufgabenleserApi('/api/aufgabenleser')))
  .mount('#app')
