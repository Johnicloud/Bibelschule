// Anwendungsschicht: Register. Mehrere Stellen dürfen mit Semikolon oder Zeilenumbruch getrennt sein,
// der Dienst zerlegt und prüft sie.

// Koordinaten kommen von Hand aus einem einzigen Textfeld „Breite, Länge“ (keine Geocoding-API verdrahtet).
export function parseKoordinaten(text) {
  const t = (text || '').trim()
  if (!t) return { lat: null, lon: null }
  const teile = t.split(/[,;]\s*|\s+/).filter(Boolean).map(Number)
  if (teile.length !== 2 || teile.some(Number.isNaN)) {
    throw new Error('Koordinaten als „Breite, Länge“ angeben, z. B. 52.52, 13.405.')
  }
  const [lat, lon] = teile
  return { lat, lon }
}

export function formatKoordinaten(e) {
  return e.lat == null ? '' : `${e.lat}, ${e.lon}`
}

// Link zu OpenStreetMap statt eines eingebetteten <iframe> (Datenschutz/CSP: kein Drittanbieter-Dokument
// im eigenen Origin). Der Kachel-Ausschnitt daneben ist nur ein einzelnes Bild, kein interaktives Embed.
export function kartenLink(lat, lon) {
  return `https://www.openstreetmap.org/?mlat=${lat}&mlon=${lon}#map=15/${lat}/${lon}`
}

export function kartenKachelUrl(lat, lon, zoom = 14) {
  const n = 2 ** zoom
  const x = Math.floor(((lon + 180) / 360) * n)
  const latRad = (lat * Math.PI) / 180
  const y = Math.floor(((1 - Math.log(Math.tan(latRad) + 1 / Math.cos(latRad)) / Math.PI) / 2) * n)
  return `https://tile.openstreetmap.org/${zoom}/${x}/${y}.png`
}

export function createRegisterService(api) {
  return {
    registers: (subjectId) => api.registers(subjectId),
    create: (subjectId, name) => api.createRegister(subjectId, name.trim()),
    rename: (id, name) => api.renameRegister(id, name.trim()),
    remove: (id) => api.deleteRegister(id),
    entries: (registerId, sort) => api.entries(registerId, sort),
    passages: (registerId) => api.passages(registerId),
    add: (registerId, e) => {
      const { lat, lon } = parseKoordinaten(e.koordinaten)
      return api.addEntry({ register_id: registerId, name: e.name.trim(), refs: [e.refs], lat, lon })
    },
    removeEntry: (id) => api.deleteEntry(id),
    setLocation: (id, text) => {
      const { lat, lon } = parseKoordinaten(text)
      return api.setLocation(id, lat, lon)
    },
    async exportieren(registerId, opts, dateiname) {
      const blob = await api.exportieren(registerId, opts)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = dateiname
      a.click()
      URL.revokeObjectURL(url)
    },
  }
}
