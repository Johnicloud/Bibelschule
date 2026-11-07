// Ausgehender Adapter: Glossar-Dienst (über den Kern: /api/glossar).
import { createCall } from './http'

export function createGlossarApi(base = '/api/glossar') {
  const call = createCall(base)
  return {
    eintraege: () => call('GET', '/eintraege'),
    add: (eintrag) => call('POST', '/eintraege', eintrag),
    update: (id, eintrag) => call('PUT', `/eintraege/${id}`, eintrag),
    remove: (id) => call('DELETE', `/eintraege/${id}`),
  }
}
