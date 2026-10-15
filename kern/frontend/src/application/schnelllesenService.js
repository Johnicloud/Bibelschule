// Anwendungsschicht: Schnelllesen. Kennt nur den "api"-Port, nicht HTTP.
export function createSchnelllesenService(api) {
  return {
    buecher: () => api.buecher(),
    liste: () => api.liste(),
    get: (id) => api.get(id),
    starten: (buch, kapitel) => api.starten(buch, kapitel),
    durchgangAbschliessen: (id, sekunden) => api.durchgangAbschliessen(id, sekunden),
    loeschen: (id) => api.loeschen(id),
  }
}
