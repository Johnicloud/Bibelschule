// Ausgehender Adapter: Skripte-Dienst (über den Kern: /api/skripte). Die eigentliche Verwaltung läuft über
// das UI-Kit des Dienstes selbst (iframe, siehe skripte/app/adapters/inbound/ui.html) – dieser Adapter deckt
// nur, was die globale Oberfläche direkt braucht: die Volltextsuche und der Datei-Link für ihre Treffer.
import { createCall } from './http'

export function createSkripteApi(base = '/api/skripte') {
  const call = createCall(base)
  return {
    suche: (text, subjectId) =>
      call('GET', `/suche?text=${encodeURIComponent(text)}${subjectId ? `&subject_id=${encodeURIComponent(subjectId)}` : ''}`),
    dateiUrl: (id) => `${base}/skripte/${id}/datei`,
  }
}
