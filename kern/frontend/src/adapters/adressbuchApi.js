// Ausgehender Adapter: Adressbuch-Dienst (über den Kern: /api/adressbuch).
import { createCall } from './http'

export function createAdressbuchApi(base = '/api/adressbuch') {
  const call = createCall(base)
  return {
    dozenten: () => call('GET', '/dozenten'),
    assign: (dozentId, subjectId) => call('POST', `/dozenten/${dozentId}/faecher/${subjectId}`),
  }
}
