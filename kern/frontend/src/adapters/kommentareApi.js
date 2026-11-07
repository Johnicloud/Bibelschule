// Ausgehender Adapter: Kommentare-Dienst (über den Kern: /api/kommentare).
import { createCall } from './http'

export function createKommentareApi(base = '/api/kommentare') {
  const call = createCall(base)
  return {
    quellen: () => call('GET', '/quellen'),
    quelleAnlegen: (quelle) => call('POST', '/quellen', quelle),
    quelleLoeschen: (id) => call('DELETE', `/quellen/${id}`),
    eintraegeZuQuelle: (quelleId) => call('GET', `/quellen/${quelleId}/eintraege`),
    zuStelle: (buch, kapitel, vers) =>
      call('GET', `/eintraege?buch=${encodeURIComponent(buch)}&kapitel=${kapitel}&vers=${vers}`),
    eintragAnlegen: (eintrag) => call('POST', '/eintraege', eintrag),
    eintragLoeschen: (id) => call('DELETE', `/eintraege/${id}`),
  }
}
