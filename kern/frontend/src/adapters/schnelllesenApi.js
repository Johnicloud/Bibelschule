// Ausgehender Adapter: Schnelllesen-Dienst (über den Kern: /api/schnelllesen).
import { createCall } from './http'

export function createSchnelllesenApi(base = '/api/schnelllesen') {
  const call = createCall(base)
  return {
    buecher: () => call('GET', '/buecher'),
    liste: () => call('GET', '/einheiten'),
    get: (id) => call('GET', `/einheiten/${id}`),
    starten: (buch, kapitel) => call('POST', '/einheiten', { buch, kapitel: Number(kapitel) }),
    durchgangAbschliessen: (id, sekunden) => call('POST', `/einheiten/${id}/durchgaenge`, { sekunden }),
    loeschen: (id) => call('DELETE', `/einheiten/${id}`),
  }
}
