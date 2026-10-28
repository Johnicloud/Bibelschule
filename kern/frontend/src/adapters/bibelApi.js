// Ausgehender Adapter: Bibel-Dienst (über den Kern: /api/bibel). Hochladen ist multipart (Datei), /stelle und
// /kapitel sind einfache GETs – eigener Aufruf statt des gemeinsamen `call` aus http.js wegen des Uploads.
import { createCall } from './http'
import { loggedIn } from '../state/auth'

export function createBibelApi(base = '/api/bibel') {
  const call = createCall(base)
  return {
    index: () => call('GET', '/index'),
    seiteSetzen: (buchIndex, seite) => call('PUT', `/buecher/${buchIndex}`, { seite }),
    stelle: (text) => call('GET', `/stelle?text=${encodeURIComponent(text)}`),
    nachschlagen: (text) => call('GET', `/nachschlagen?text=${encodeURIComponent(text)}`),
    kapitel: (buch, nummer) => call('GET', `/kapitel?buch=${encodeURIComponent(buch)}&nummer=${nummer}`),
    suche: (wort) => call('GET', `/suche?wort=${encodeURIComponent(wort)}`),
    dateiUrl: (seite) => `${base}/datei${seite ? `#page=${seite}` : ''}`,
    async hochladen(datei) {
      const form = new FormData()
      form.append('name', datei.name)
      form.append('datei', datei)
      const res = await fetch(`${base}/hochladen`, { method: 'POST', body: form })
      if (res.status === 401) loggedIn.value = false
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(typeof err.detail === 'string' ? err.detail : 'Etwas ist schiefgelaufen.')
      }
      return res.json()
    },
  }
}
