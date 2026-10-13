// Ausgehender Adapter: Adressbuch-Dienst (über den Kern: /api/adressbuch).
import { createCall } from './http'

export function createAdressbuchApi(base = '/api/adressbuch') {
  const call = createCall(base)
  return {
    dozenten: () => call('GET', '/dozenten'),
    add: (dozent) => call('POST', '/dozenten', dozent),
    update: (id, dozent) => call('PUT', `/dozenten/${id}`, dozent),
    remove: (id) => call('DELETE', `/dozenten/${id}`),
    assign: (dozentId, subjectId) => call('POST', `/dozenten/${dozentId}/faecher/${subjectId}`),
    unassign: (dozentId, subjectId) => call('DELETE', `/dozenten/${dozentId}/faecher/${subjectId}`),
  }
}
