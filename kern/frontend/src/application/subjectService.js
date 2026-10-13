// Anwendungsschicht: Fächer und Übersicht. Kennt nur den "api"-Port, nicht HTTP.
export function createSubjectService(api) {
  return {
    list: () => api.listSubjects(),
    get: (id) => api.getSubject(id),
    create: (name, aufgaben = [], se = null) =>
      api.createSubject(name.trim(), aufgaben.map((t) => t.trim()).filter(Boolean), se === '' || se == null ? null : Number(se)),
    rename: (id, name) => api.renameSubject(id, name.trim()),
    setSe: (id, se) => api.setSe(id, se === '' || se == null ? null : Number(se)),
    remove: (id) => api.deleteSubject(id),
    addAufgabe: (id, titel, frist, gewichtung) => api.addAufgabe(id, titel.trim(), frist, gewichtung),
    setAufgabeErledigt: (id, aufgabeId, erledigt) => api.setAufgabeErledigt(id, aufgabeId, erledigt),
    removeAufgabe: (id, aufgabeId) => api.deleteAufgabe(id, aufgabeId),
    services: () => api.services(),
    overview: () => api.overview(),
    overviewOf: (id) => api.subjectOverview(id), // Stand und Gesamtfortschritt eines Fachs
    sync: () => api.sync(),
  }
}
