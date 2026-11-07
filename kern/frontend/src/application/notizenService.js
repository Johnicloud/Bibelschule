// Anwendungsschicht: Notizen. Kennt nur den "api"-Port, nicht HTTP.
export function createNotizenService(api) {
  return {
    liste: (stelle) => api.liste(stelle),
    anlegen: (stelle, text) => api.anlegen(stelle, text),
    loeschen: (id) => api.loeschen(id),
  }
}
