// Anwendungsschicht: Skripte (nur Lesen für andere Ansichten, z. B. Orientierungsfragen aus einer Datei).
export function createSkripteService(api) {
  return {
    // Dateien eines Fachs, aus denen sich Fragen lesen lassen (PDF, Word, Pages, Text, Bild …)
    dateienMitFragen: async (subjectId) => (await api.list(subjectId)).filter((s) => s.kann_fragen),
    dateien: (subjectId) => api.list(subjectId),
    seitenGesamt: async (skriptId) => (await api.qualitaet(skriptId)).seiten_gesamt,
    karten: (skriptId) => api.karten(skriptId),
  }
}
