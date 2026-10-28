import { createCall } from './http'

// Ausgehender Adapter: Skripte-Dienst (über den Kern: /api/skripte). Hier nur, was andere Ansichten brauchen:
// die Dateien eines Fachs und die daraus lesbaren Karten (Fragenliste oder Druckbogen).
export function createSkripteApi(base = '/api/skripte') {
  const call = createCall(base)
  return {
    list: (subjectId) => call('GET', `/skripte?subject_id=${encodeURIComponent(subjectId)}`),
    karten: (skriptId) => call('GET', `/skripte/${skriptId}/karten`),
  }
}
