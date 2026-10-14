// Gemeinsames Verhalten für jeden Dienst, der eine PDF-Datei liefert: zeigt sie in einem neuen Reiter, wo der
// Browser seine eigene PDF-Ansicht mit Drucken- und Herunterladen-Knopf mitbringt (Chrome, Firefox, Safari haben
// das serienmäßig) – ein Klick statt eines erzwungenen Downloads.
//
// Das Fenster muss schon offen sein, BEVOR die PDF-Datei beim Server abgeholt wird (siehe fensterOeffnen unten):
// Safari und mancher Pop-up-Blocker erlauben window.open() nur noch direkt im Klick-Handler, nicht mehr danach,
// wenn dazwischen schon eine asynchrone Anfrage (fetch) gelaufen ist – die "Nutzeraktion" gilt dann als verbraucht.
export function fensterOeffnen() {
  return window.open('', '_blank')
}

export function pdfZeigen(fenster, blob, dateiname) {
  const url = URL.createObjectURL(blob)
  if (fenster && !fenster.closed) {
    fenster.location.href = url
  } else {
    // Pop-up wurde doch blockiert: wenigstens herunterladen, damit die Datei nicht verloren geht.
    const a = document.createElement('a')
    a.href = url
    a.download = dateiname
    a.click()
  }
  // Objekt-URL erst spät freigeben: der Reiter lädt die Datei asynchron.
  setTimeout(() => URL.revokeObjectURL(url), 60_000)
}
