// Anwendungsschicht: Skripte (nur für die globale Suche, siehe adapters/skripteApi.js). Kennt nur den
// "api"-Port, nicht HTTP.
export function createSkripteService(api) {
  return {
    suche: (text, subjectId) => api.suche(text, subjectId),
    dateiUrl: (id) => api.dateiUrl(id),
  }
}
