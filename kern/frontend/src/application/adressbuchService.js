// Anwendungsschicht: Adressbuch. Kennt nur den "api"-Port, nicht HTTP.
export function createAdressbuchService(api) {
  return {
    dozenten: () => api.dozenten(),
    add: (dozent) => api.add({ name: dozent.name.trim(), email: dozent.email || null, telefon: dozent.telefon || null, adresse: dozent.adresse || null, notiz: dozent.notiz || null }),
    update: (id, dozent) => api.update(id, { name: dozent.name.trim(), email: dozent.email || null, telefon: dozent.telefon || null, adresse: dozent.adresse || null, notiz: dozent.notiz || null }),
    remove: (id) => api.remove(id),
    assign: (dozentId, subjectId) => api.assign(dozentId, subjectId),
    unassign: (dozentId, subjectId) => api.unassign(dozentId, subjectId),
  }
}
