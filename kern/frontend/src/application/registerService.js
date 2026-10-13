// Anwendungsschicht: Register. Mehrere Stellen dürfen mit Semikolon oder Zeilenumbruch getrennt sein,
// der Dienst zerlegt und prüft sie.
export function createRegisterService(api) {
  return {
    registers: (subjectId) => api.registers(subjectId),
    create: (subjectId, name) => api.createRegister(subjectId, name.trim()),
    rename: (id, name) => api.renameRegister(id, name.trim()),
    remove: (id) => api.deleteRegister(id),
    entries: (registerId, sort) => api.entries(registerId, sort),
    passages: (registerId) => api.passages(registerId),
    add: (registerId, e) => api.addEntry({ register_id: registerId, name: e.name.trim(), refs: [e.refs] }),
    removeEntry: (id) => api.deleteEntry(id),
    exportUrl: (registerId, opts) => api.exportUrl(registerId, opts),
  }
}
