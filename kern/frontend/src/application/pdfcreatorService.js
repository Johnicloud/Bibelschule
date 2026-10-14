// Anwendungsschicht: PDF-Vorlagen. Füllt die mitgelieferte Vorlage „Lesenachweis Pflichtlektüre“ und löst
// den Browser-Download aus (kein Objekt-URL-Leak: wird nach dem Klick wieder freigegeben).
const STANDARD_VORLAGE_ID = 'lesenachweis-pflichtlektuere'
const MAX_BUECHER = 6

export function createPdfcreatorService(api) {
  return {
    async lesenachweisExportieren(fach, name, gemeinde, buecher) {
      const blob = await api.fuellen(STANDARD_VORLAGE_ID, {
        werte: { fach, name: (name || '').trim(), gemeinde: (gemeinde || '').trim() },
        buecher: buecher.slice(0, MAX_BUECHER).map((b) => ({ titel: b.titel, seiten: String(b.seiten) })),
      })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `Lesenachweis ${fach}.pdf`
      a.click()
      URL.revokeObjectURL(url)
    },
  }
}
