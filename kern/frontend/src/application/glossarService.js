// Anwendungsschicht: Glossar. Kennt nur den "api"-Port, nicht HTTP.
export function createGlossarService(api) {
  return {
    eintraege: () => api.eintraege(),
    add: (eintrag) => api.add(eintrag),
    update: (id, eintrag) => api.update(id, eintrag),
    remove: (id) => api.remove(id),
  }
}
