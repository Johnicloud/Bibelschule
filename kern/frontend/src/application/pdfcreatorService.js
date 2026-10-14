// Anwendungsschicht: PDF-Vorlagen. Füllt die mitgelieferte Vorlage „Lesenachweis Pflichtlektüre“ und öffnet sie
// zum Drucken/Herunterladen (siehe pdf.js).
import { pdfZeigen } from './pdf'

const STANDARD_VORLAGE_ID = 'lesenachweis-pflichtlektuere'
const MAX_BUECHER = 6

export function createPdfcreatorService(api) {
  return {
    async lesenachweisExportieren(fach, name, gemeinde, buecher, fenster) {
      const blob = await api.fuellen(STANDARD_VORLAGE_ID, {
        werte: { fach, name: (name || '').trim(), gemeinde: (gemeinde || '').trim() },
        buecher: buecher.slice(0, MAX_BUECHER).map((b) => ({ titel: b.titel, seiten: String(b.seiten) })),
      })
      pdfZeigen(fenster, blob, `Lesenachweis ${fach}.pdf`)
    },
  }
}
