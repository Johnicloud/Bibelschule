// Ausgehender Adapter: Fächer, Dienstverzeichnis und Übersicht des Kerns.
import { createCall } from './http'

export function createKernApi(base = '/api') {
  const call = createCall(base)
  return {
    listSubjects: () => call('GET', '/subjects'),
    getSubject: (id) => call('GET', `/subjects/${id}`),
    createSubject: (name, aufgaben = [], se = null) => call('POST', '/subjects', { name, aufgaben, se }),
    renameSubject: (id, name) => call('PUT', `/subjects/${id}`, { name }),
    setSe: (id, se) => call('PUT', `/subjects/${id}/se`, { se }),
    deleteSubject: (id) => call('DELETE', `/subjects/${id}`),
    addAufgabe: (id, titel, frist, gewichtung) =>
      call('POST', `/subjects/${id}/aufgaben`, { titel, frist: frist || null, gewichtung: gewichtung === '' || gewichtung == null ? null : Number(gewichtung) }),
    setAufgabeErledigt: (id, aufgabeId, erledigt) => call('PUT', `/subjects/${id}/aufgaben/${aufgabeId}`, { erledigt }),
    deleteAufgabe: (id, aufgabeId) => call('DELETE', `/subjects/${id}/aufgaben/${aufgabeId}`),
    services: () => call('GET', '/services'),
    overview: () => call('GET', '/overview'),
    subjectOverview: (id) => call('GET', `/subjects/${id}/overview`),
    sync: () => call('POST', '/sync'),
  }
}
