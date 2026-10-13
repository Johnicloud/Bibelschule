// Anwendungsschicht: Adressbuch. Kennt nur den "api"-Port, nicht HTTP.
export function createAdressbuchService(api) {
  return {
    dozenten: () => api.dozenten(),
    assign: (dozentId, subjectId) => api.assign(dozentId, subjectId),
  }
}
