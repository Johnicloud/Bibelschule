// Ausgehender Adapter: Register-Dienst (über den Kern: /api/register).
import { createCall } from './http'

export function createRegisterApi(base = '/api/register') {
  const call = createCall(base)
  const query = (subjectId, params) =>
    '?' + new URLSearchParams({ subject_id: subjectId, ...params }).toString()
  return {
    entries: (subjectId, { kind = '', sort = 'name' } = {}) =>
      call('GET', '/entries' + query(subjectId, { sort, ...(kind ? { kind } : {}) })),
    passages: (subjectId, kind = '') => call('GET', '/passages' + query(subjectId, kind ? { kind } : {})),
    addEntry: (entry) => call('POST', '/entries', entry),
    deleteEntry: (id) => call('DELETE', `/entries/${id}`),
  }
}
