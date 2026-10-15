// Ausgehender Adapter: Bibliothek-Dienst (über den Kern: /api/bibliothek). Datei-Upload ist multipart, die
// Downloads liefern PDF statt JSON – eigene Aufrufe statt des gemeinsamen `call` aus http.js.
import { createCall } from './http'
import { loggedIn } from '../state/auth'

export function createBibliothekApi(base = '/api/bibliothek') {
  const call = createCall(base)
  return {
    buecher: () => call('GET', '/buecher'),
    add: (buch) => call('POST', '/buecher', buch),
    update: (id, buch) => call('PUT', `/buecher/${id}`, buch),
    remove: (id) => call('DELETE', `/buecher/${id}`),
    ausleihen: (id, an) => call('POST', `/buecher/${id}/ausleihen`, { an }),
    zurueckgeben: (id) => call('POST', `/buecher/${id}/zurueckgeben`),
    assign: (buchId, subjectId) => call('POST', `/buecher/${buchId}/faecher/${subjectId}`),
    unassign: (buchId, subjectId) => call('DELETE', `/buecher/${buchId}/faecher/${subjectId}`),
    textErkennen: (id) => call('POST', `/buecher/${id}/text-erkennen`),
    dateiUrl: (id) => `${base}/buecher/${id}/datei`,
    textDateiUrl: (id) => `${base}/buecher/${id}/text-datei`,
    async dateiHochladen(id, datei) {
      const form = new FormData()
      form.append('datei', datei)
      const res = await fetch(`${base}/buecher/${id}/datei`, { method: 'POST', body: form })
      if (res.status === 401) loggedIn.value = false
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(typeof err.detail === 'string' ? err.detail : 'Etwas ist schiefgelaufen.')
      }
      return res.json()
    },
  }
}
