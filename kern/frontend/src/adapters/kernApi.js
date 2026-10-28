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
    setNote: (id, note) => call('PUT', `/subjects/${id}/note`, { note }),
    noten: () => call('GET', '/noten'),
    deleteSubject: (id) => call('DELETE', `/subjects/${id}`),
    addAufgabe: (id, titel, frist, gewichtung) =>
      call('POST', `/subjects/${id}/aufgaben`, { titel, frist: frist || null, gewichtung: gewichtung === '' || gewichtung == null ? null : Number(gewichtung) }),
    createAufgabe: (id, felder) => call('POST', `/subjects/${id}/aufgaben`, felder),
    updateAufgabe: (id, aufgabeId, felder) => call('PATCH', `/subjects/${id}/aufgaben/${aufgabeId}`, felder),
    setAufgabeErledigt: (id, aufgabeId, erledigt) => call('PUT', `/subjects/${id}/aufgaben/${aufgabeId}`, { erledigt }),
    deleteAufgabe: (id, aufgabeId) => call('DELETE', `/subjects/${id}/aufgaben/${aufgabeId}`),
    setAufgabePensum: (id, aufgabeId, pensumId) => call('PUT', `/subjects/${id}/aufgaben/${aufgabeId}/pensum`, { pensum_id: pensumId }),
    setAktiveDienste: (id, dienste) => call('PUT', `/subjects/${id}/dienste`, { dienste }),
    services: () => call('GET', '/services'),
    overview: () => call('GET', '/overview'),
    subjectOverview: (id) => call('GET', `/subjects/${id}/overview`),
    sync: () => call('POST', '/sync'),
  }
}
