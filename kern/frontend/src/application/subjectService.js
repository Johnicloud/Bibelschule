// Anwendungsschicht: Fächer und Übersicht. Kennt nur den "api"-Port, nicht HTTP.
export function createSubjectService(api) {
  return {
    list: () => api.listSubjects(),
    get: (id) => api.getSubject(id),
    create: (name) => api.createSubject(name.trim()),
    rename: (id, name) => api.renameSubject(id, name.trim()),
    remove: (id) => api.deleteSubject(id),
    services: () => api.services(),
    overview: () => api.overview(),
    sync: () => api.sync(),
  }
}
