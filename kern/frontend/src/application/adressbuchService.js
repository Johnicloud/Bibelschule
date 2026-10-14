// Anwendungsschicht: Adressbuch. Kennt nur den "api"-Port, nicht HTTP.
function dozentBody(dozent) {
  return {
    name: dozent.name.trim(),
    email: dozent.email || null,
    telefon: dozent.telefon || null,
    strasse: dozent.strasse || null,
    plz: dozent.plz || null,
    ort: dozent.ort || null,
    notiz: dozent.notiz || null,
  }
}

export function createAdressbuchService(api) {
  return {
    dozenten: () => api.dozenten(),
    add: (dozent) => api.add(dozentBody(dozent)),
    update: (id, dozent) => api.update(id, dozentBody(dozent)),
    remove: (id) => api.remove(id),
    assign: (dozentId, subjectId) => api.assign(dozentId, subjectId),
    unassign: (dozentId, subjectId) => api.unassign(dozentId, subjectId),
  }
}
