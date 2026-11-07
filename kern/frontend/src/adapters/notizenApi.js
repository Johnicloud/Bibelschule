// Ausgehender Adapter: Notizen-Dienst (über den Kern: /api/notizen).
import { createCall } from './http'

export function createNotizenApi(base = '/api/notizen') {
  const call = createCall(base)
  return {
    liste: (stelle) => call('GET', `/kommentare?stelle=${encodeURIComponent(stelle)}`),
    anlegen: (stelle, text) => call('POST', '/kommentare', { stelle, text }),
    loeschen: (id) => call('DELETE', `/kommentare/${id}`),
  }
}
