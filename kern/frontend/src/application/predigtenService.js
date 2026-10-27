// Anwendungsschicht: Predigten. Kennt nur den "api"-Port, nicht HTTP.
// `stellenText` kommt aus der Oberfläche als ein Textfeld (eine Bibelstelle je Zeile oder durch Komma
// getrennt, z. B. "Joh 3,16\nRöm 8,28") – der Dienst selbst erwartet eine Liste freier Bibelstellen-Texte.
export function stellenAusText(stellenText) {
  return (stellenText || '')
    .split(/[\n,]/)
    .map((s) => s.trim())
    .filter(Boolean)
}

export function stellenZuText(stellen) {
  return (stellen || []).join(', ')
}

function predigtBody(predigt) {
  return {
    titel: predigt.titel.trim(),
    datum: predigt.datum || null,
    prediger: predigt.prediger || null,
    notiz: predigt.notiz || null,
    stellen: stellenAusText(predigt.stellenText),
  }
}

export function createPredigtenService(api) {
  return {
    predigten: () => api.predigten(),
    add: (predigt) => api.add(predigtBody(predigt)),
    update: (id, predigt) => api.update(id, predigtBody(predigt)),
    remove: (id) => api.remove(id),
    dateiHochladen: (id, datei) => api.dateiHochladen(id, datei),
    dateiUrl: (id) => api.dateiUrl(id),
  }
}
