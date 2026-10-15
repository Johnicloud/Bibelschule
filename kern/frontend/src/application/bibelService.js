// Anwendungsschicht: Bibel. Kennt nur den "api"-Port, nicht HTTP.
export function createBibelService(api) {
  return {
    index: () => api.index(),
    seiteSetzen: (buchIndex, seite) => api.seiteSetzen(buchIndex, seite === '' || seite == null ? null : Number(seite)),
    hochladen: (datei) => api.hochladen(datei),
    stelle: (text) => api.stelle(text),
    kapitel: (buch, nummer) => api.kapitel(buch, nummer),
    dateiUrl: (seite) => api.dateiUrl(seite),
  }
}
