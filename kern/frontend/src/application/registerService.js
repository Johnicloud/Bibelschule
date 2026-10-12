// Anwendungsschicht: Register. Mehrere Stellen dürfen mit Semikolon oder Zeilenumbruch getrennt sein,
// der Dienst zerlegt und prüft sie.
export function createRegisterService(api) {
  return {
    list: (subjectId, opts) => api.entries(subjectId, opts),
    passages: (subjectId, kind) => api.passages(subjectId, kind),
    add: (subjectId, e) => api.addEntry({
      subject_id: subjectId,
      kind: e.kind,
      name: e.name.trim(),
      refs: [e.refs],
      note: (e.note || '').trim(),
    }),
    remove: (id) => api.deleteEntry(id),
  }
}
