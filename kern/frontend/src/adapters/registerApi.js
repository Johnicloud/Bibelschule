// Ausgehender Adapter: Register-Dienst (über den Kern: /api/register).
import { createCall } from './http'
import { loggedIn } from '../state/auth'

export function createRegisterApi(base = '/api/register') {
  const call = createCall(base)
  const query = (params) => '?' + new URLSearchParams(params).toString()
  return {
    registers: (subjectId) => call('GET', '/registers' + query({ subject_id: subjectId })),
    createRegister: (subjectId, name) => call('POST', '/registers', { subject_id: subjectId, name }),
    renameRegister: (id, name) => call('PUT', `/registers/${id}`, { name }),
    deleteRegister: (id) => call('DELETE', `/registers/${id}`),
    entries: (registerId, sort = 'name') => call('GET', '/entries' + query({ register_id: registerId, sort })),
    passages: (registerId) => call('GET', '/passages' + query({ register_id: registerId })),
    addEntry: (entry) => call('POST', '/entries', entry),
    updateEntry: (id, entry) => call('PUT', `/entries/${id}`, entry),
    deleteEntry: (id) => call('DELETE', `/entries/${id}`),
    setLocation: (id, lat, lon) => call('PUT', `/entries/${id}/location`, { lat, lon }),
    // Export (CSV oder Text) eines Registers, mit derselben Sortierung wie die Anzeige. Als Blob statt als
    // einfacher <a href>-Link, damit eine abgelaufene Sitzung nicht als kaputte Datei heruntergeladen wird,
    // sondern wie jeder andere Aufruf zur Anmeldeseite zurückführt.
    exportieren: async (registerId, { sort = 'name', format = 'csv' } = {}) => {
      const res = await fetch(`${base}/export` + query({ register_id: registerId, sort, format }))
      if (res.status === 401) loggedIn.value = false
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(typeof err.detail === 'string' ? err.detail : 'Etwas ist schiefgelaufen.')
      }
      return res.blob()
    },
  }
}
