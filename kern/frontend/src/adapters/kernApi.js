// Ausgehender Adapter: Fächer, Dienstverzeichnis und Übersicht des Kerns.
import { createCall } from './http'

export function createKernApi(base = '/api') {
  const call = createCall(base)
  return {
    listSubjects: () => call('GET', '/subjects'),
    getSubject: (id) => call('GET', `/subjects/${id}`),
    createSubject: (name) => call('POST', '/subjects', { name }),
    renameSubject: (id, name) => call('PUT', `/subjects/${id}`, { name }),
    deleteSubject: (id) => call('DELETE', `/subjects/${id}`),
    services: () => call('GET', '/services'),
    overview: () => call('GET', '/overview'),
    subjectOverview: (id) => call('GET', `/subjects/${id}/overview`),
    sync: () => call('POST', '/sync'),
  }
}
