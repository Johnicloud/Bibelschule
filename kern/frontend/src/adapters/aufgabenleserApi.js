// Ausgehender Adapter: liest ein Aufgabenblatt (PDF) und liefert Aufgaben-Vorschläge (nur Vorschläge, siehe
// Projektnotizen). Eigener Aufruf statt des gemeinsamen `call` aus http.js, weil hier eine Datei (multipart)
// statt JSON geschickt wird.
import { loggedIn } from '../state/auth'

export function createAufgabenleserApi(base = '/api/aufgabenleser') {
  return {
    async lesen(datei) {
      const form = new FormData()
      form.append('datei', datei)
      const res = await fetch(`${base}/lesen`, { method: 'POST', body: form })
      if (res.status === 401) loggedIn.value = false
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(typeof err.detail === 'string' ? err.detail : 'Etwas ist schiefgelaufen.')
      }
      return res.json()
    },
  }
}
