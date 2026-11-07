// Anwendungsschicht: Fragen-KI. Kennt nur den "api"-Port, nicht HTTP.
export function createFragenkiService(api) {
  return {
    buecher: () => api.buecher(),
    generieren: (buch, kapitel) => api.generieren(buch, kapitel),
  }
}
