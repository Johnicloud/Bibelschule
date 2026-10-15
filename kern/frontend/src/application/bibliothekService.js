// Anwendungsschicht: Bibliothek. Kennt nur den "api"-Port, nicht HTTP.
function buchBody(buch) {
  return {
    titel: buch.titel.trim(),
    autor: buch.autor || null,
    verlag: buch.verlag || null,
    jahr: buch.jahr === '' || buch.jahr == null ? null : Number(buch.jahr),
    isbn: buch.isbn || null,
    standort: buch.standort || null,
    notiz: buch.notiz || null,
  }
}

export function createBibliothekService(api) {
  return {
    buecher: () => api.buecher(),
    suche: (text) => api.suche(text),
    add: (buch) => api.add(buchBody(buch)),
    update: (id, buch) => api.update(id, buchBody(buch)),
    remove: (id) => api.remove(id),
    ausleihen: (id, an) => api.ausleihen(id, an.trim()),
    zurueckgeben: (id) => api.zurueckgeben(id),
    assign: (buchId, subjectId) => api.assign(buchId, subjectId),
    unassign: (buchId, subjectId) => api.unassign(buchId, subjectId),
    dateiHochladen: (id, datei) => api.dateiHochladen(id, datei),
    textErkennen: (id) => api.textErkennen(id),
    dateiUrl: (id) => api.dateiUrl(id),
    textDateiUrl: (id) => api.textDateiUrl(id),
  }
}
