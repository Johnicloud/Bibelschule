// Ausgehender Adapter: Predigten-Dienst (über den Kern: /api/predigten). Datei-Upload ist multipart wie bei
// bibliothekApi.js, eigener Aufruf statt des gemeinsamen `call` aus http.js.
import { createCall } from './http'
import { loggedIn } from '../state/auth'

export function createPredigtenApi(base = '/api/predigten') {
  const call = createCall(base)
  return {
    predigten: () => call('GET', '/predigten'),
    add: (predigt) => call('POST', '/predigten', predigt),
    update: (id, predigt) => call('PUT', `/predigten/${id}`, predigt),
    remove: (id) => call('DELETE', `/predigten/${id}`),
    dateiUrl: (id) => `${base}/predigten/${id}/datei`,
    async dateiHochladen(id, datei) {
      const form = new FormData()
      form.append('datei', datei)
      const res = await fetch(`${base}/predigten/${id}/datei`, { method: 'POST', body: form })
      if (res.status === 401) loggedIn.value = false
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(typeof err.detail === 'string' ? err.detail : 'Etwas ist schiefgelaufen.')
      }
      return res.json()
    },
  }
}
