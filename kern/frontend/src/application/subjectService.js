// Anwendungsschicht: Fächer und Übersicht. Kennt nur den "api"-Port, nicht HTTP.
const zahlOderNull = (v) => (v === '' || v == null ? null : Number(v))

function aufgabeFelder(f) {
  return {
    titel: (f.titel || '').trim(), art: f.art || 'allgemein', frist: f.frist || null, gewichtung: zahlOderNull(f.gewichtung),
    zaehlt: f.zaehlt !== false, notiz: (f.notiz || '').trim(), soll: zahlOderNull(f.soll), ist: zahlOderNull(f.ist),
    einheit: (f.einheit || '').trim(),
  }
}

export function createSubjectService(api) {
  return {
    list: () => api.listSubjects(),
    get: (id) => api.getSubject(id),
    create: (name, aufgaben = [], se = null) =>
      api.createSubject(name.trim(), aufgaben.map((t) => t.trim()).filter(Boolean), se === '' || se == null ? null : Number(se)),
    rename: (id, name) => api.renameSubject(id, name.trim()),
    setSe: (id, se) => api.setSe(id, se === '' || se == null ? null : Number(se)),
    setNote: (id, note) => api.setNote(id, note === '' || note == null ? null : Number(note)),
    noten: () => api.noten(),
    remove: (id) => api.deleteSubject(id),
    addAufgabe: (id, titel, frist, gewichtung) => api.addAufgabe(id, titel.trim(), frist, gewichtung),
    // Standard für alle Arten: dieselbe Aufbereitung beim Anlegen und Bearbeiten (leer = entfernen)
    createAufgabe: (id, felder) => api.createAufgabe(id, aufgabeFelder(felder)),
    updateAufgabe: (id, aufgabeId, felder) => api.updateAufgabe(id, aufgabeId, aufgabeFelder(felder)),
    setAufgabeErledigt: (id, aufgabeId, erledigt) => api.setAufgabeErledigt(id, aufgabeId, erledigt),
    removeAufgabe: (id, aufgabeId) => api.deleteAufgabe(id, aufgabeId),
    setAufgabePensum: (id, aufgabeId, pensumId) => api.setAufgabePensum(id, aufgabeId, pensumId),
    setAktiveDienste: (id, dienste) => api.setAktiveDienste(id, dienste),
    services: () => api.services(),
    overview: () => api.overview(),
    overviewOf: (id) => api.subjectOverview(id), // Stand und Gesamtfortschritt eines Fachs
    sync: () => api.sync(),
  }
}
