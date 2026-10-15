// Anwendungsschicht: Text oder eine PDF-Datei vorlesen lassen (lokale KI, siehe Projektnotizen).
export function createVorlesenService(api) {
  return {
    text: (text) => api.text(text.trim()),
    pdf: (datei) => api.pdf(datei),
  }
}
