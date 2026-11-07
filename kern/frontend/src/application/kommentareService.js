// Anwendungsschicht: Kommentare. Kennt nur den "api"-Port, nicht HTTP.
export function createKommentareService(api) {
  return {
    quellen: () => api.quellen(),
    quelleAnlegen: (quelle) => api.quelleAnlegen(quelle),
    quelleLoeschen: (id) => api.quelleLoeschen(id),
    eintraegeZuQuelle: (quelleId) => api.eintraegeZuQuelle(quelleId),
    zuStelle: (buch, kapitel, vers) => api.zuStelle(buch, kapitel, vers),
    eintragAnlegen: (eintrag) => api.eintragAnlegen(eintrag),
    eintragLoeschen: (id) => api.eintragLoeschen(id),
  }
}
