// Ausgehender Adapter: Vorlesen-Dienst (über den Kern: /api/vorlesen). Antwort ist eine Audio-Datei (WAV),
// kein JSON – darum ein eigener Aufruf statt des gemeinsamen createCall (siehe adapters/http.js), wie beim
// pdfcreator-Dienst.
import { loggedIn } from '../state/auth'

async function alsAudio(res) {
  if (res.status === 401) loggedIn.value = false
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(typeof err.detail === 'string' ? err.detail : 'Etwas ist schiefgelaufen.')
  }
  return res.blob()
}

export function createVorlesenApi(base = '/api/vorlesen') {
  return {
    text: async (text) => alsAudio(await fetch(`${base}/text`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    })),
    // pdf: Blob/File der Datei direkt vom Browser weitergereicht (z. B. aus dem Skripte-Reiter geholt).
    pdf: async (datei) => {
      const formData = new FormData()
      formData.append('datei', datei)
      return alsAudio(await fetch(`${base}/pdf`, { method: 'POST', body: formData }))
    },
  }
}
