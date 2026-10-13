// Ausgehender Adapter: Lesenachweis-Dienst (über den Kern: /api/lesenachweis).
import { createCall } from './http'

export function createReadingApi(base = '/api/lesenachweis') {
  const call = createCall(base)
  return {
    status: (subjectId) => call('GET', `/subjects/${subjectId}/status`),
    tasks: (subjectId) => call('GET', `/tasks?subject_id=${encodeURIComponent(subjectId)}`),
    addTask: (task) => call('POST', '/tasks', task),
    deleteTask: (id) => call('DELETE', `/tasks/${id}`),
    log: (id, entry) => call('POST', `/tasks/${id}/entries`, entry),
    deleteEntry: (id, entryId) => call('DELETE', `/tasks/${id}/entries/${entryId}`),
  }
}
