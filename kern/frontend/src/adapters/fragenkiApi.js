// Ausgehender Adapter: Fragen-KI-Dienst (über den Kern: /api/fragenki).
import { createCall } from './http'

export function createFragenkiApi(base = '/api/fragenki') {
  const call = createCall(base)
  return {
    buecher: () => call('GET', '/buecher'),
    generieren: (buch, kapitel) => call('POST', '/generieren', { buch, kapitel: Number(kapitel) }),
  }
}
