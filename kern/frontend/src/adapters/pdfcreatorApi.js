// Ausgehender Adapter: PDF-Vorlagen-Dienst (über den Kern: /api/pdfcreator). Antwort ist eine PDF-Datei,
// kein JSON – darum ein eigener Aufruf statt des gemeinsamen createCall (siehe adapters/http.js).
import { loggedIn } from '../state/auth'

export function createPdfcreatorApi(base = '/api/pdfcreator') {
  return {
    fuellen: async (vorlageId, body) => {
      const res = await fetch(`${base}/vorlagen/${vorlageId}/fuellen`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (res.status === 401) loggedIn.value = false
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(typeof err.detail === 'string' ? err.detail : 'Etwas ist schiefgelaufen.')
      }
      return res.blob()
    },
  }
}
