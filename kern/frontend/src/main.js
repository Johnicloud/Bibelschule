// Kompositionswurzel der UI: Adapter -> Anwendungsschicht -> Komponenten
import { createApp } from 'vue'
import App from './App.vue'
import './style.css'
import { createAdressbuchApi } from './adapters/adressbuchApi'
import { createAufgabenleserApi } from './adapters/aufgabenleserApi'
import { createAuthApi } from './adapters/authApi'
import { createBibelApi } from './adapters/bibelApi'
import { createBibliothekApi } from './adapters/bibliothekApi'
import { createFragenkiApi } from './adapters/fragenkiApi'
import { createHttpApi } from './adapters/httpApi'
import { createKernApi } from './adapters/kernApi'
import { createNotizenApi } from './adapters/notizenApi'
import { createPdfcreatorApi } from './adapters/pdfcreatorApi'
import { createPredigtenApi } from './adapters/predigtenApi'
import { createReadingApi } from './adapters/readingApi'
import { createRegisterApi } from './adapters/registerApi'
import { createSchnelllesenApi } from './adapters/schnelllesenApi'
import { createAdressbuchService } from './application/adressbuchService'
import { createAufgabenLeseService } from './application/aufgabenLeseService'
import { createAuthService } from './application/authService'
import { createBibelService } from './application/bibelService'
import { createBibliothekService } from './application/bibliothekService'
import { createFlashcardService } from './application/flashcardService'
<<<<<<< HEAD
import { createNotizenService } from './application/notizenService'
=======
import { createFragenkiService } from './application/fragenkiService'
>>>>>>> origin/claude/fragenki-724ef6
import { createPdfcreatorService } from './application/pdfcreatorService'
import { createPredigtenService } from './application/predigtenService'
import { createSubjectService } from './application/subjectService'
import { createReadingService } from './application/readingService'
import { createRegisterService } from './application/registerService'
import { createSchnelllesenService } from './application/schnelllesenService'

createApp(App)
  .provide('auth', createAuthService(createAuthApi('/api')))
  .provide('subjects', createSubjectService(createKernApi('/api')))
  .provide('service', createFlashcardService(createHttpApi('/api/karteikarten')))
  .provide('reading', createReadingService(createReadingApi('/api/lesenachweis')))
  .provide('register', createRegisterService(createRegisterApi('/api/register')))
  .provide('adressbuch', createAdressbuchService(createAdressbuchApi('/api/adressbuch')))
  .provide('aufgabenleser', createAufgabenLeseService(createAufgabenleserApi('/api/aufgabenleser')))
  .provide('pdfcreator', createPdfcreatorService(createPdfcreatorApi('/api/pdfcreator')))
  .provide('bibel', createBibelService(createBibelApi('/api/bibel')))
  .provide('bibliothek', createBibliothekService(createBibliothekApi('/api/bibliothek')))
  .provide('schnelllesen', createSchnelllesenService(createSchnelllesenApi('/api/schnelllesen')))
<<<<<<< HEAD
  .provide('predigten', createPredigtenService(createPredigtenApi('/api/predigten')))

  .provide('notizen', createNotizenService(createNotizenApi('/api/notizen')))
=======
  .provide('fragenki', createFragenkiService(createFragenkiApi('/api/fragenki')))
>>>>>>> origin/claude/fragenki-724ef6
  .mount('#app')
