// Ausgehender Adapter: Register-Dienst (über den Kern: /api/register).
import { createCall } from './http'

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
    deleteEntry: (id) => call('DELETE', `/entries/${id}`),
    // Link zum Herunterladen (CSV oder Text) eines Registers, mit derselben Sortierung wie die Anzeige
    exportUrl: (registerId, { sort = 'name', format = 'csv' } = {}) =>
      base + '/export' + query({ register_id: registerId, sort, format }),
  }
}
