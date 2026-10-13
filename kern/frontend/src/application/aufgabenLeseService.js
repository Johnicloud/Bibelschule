// Anwendungsschicht: Aufgabenblatt (PDF) einlesen lassen. Kennt nur den "api"-Port, nicht HTTP/FormData.
export function createAufgabenLeseService(api) {
  return {
    lesen: (datei) => api.lesen(datei),
  }
}
