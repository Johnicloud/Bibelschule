import { createCall } from './http'
import { loggedIn } from '../state/auth'

// Ausgehender Adapter: Karteikarten-Dienst (über den Kern: /api/karteikarten).
export function createHttpApi(base = '/api') {
  const call = createCall(base)
  return {
    listDecks: () => call('GET', '/decks'),
    createDeck: (name) => call('POST', '/decks', { name }),
    getDeck: (id) => call('GET', `/decks/${id}`),
    deleteDeck: (id) => call('DELETE', `/decks/${id}`),
    allCards: () => call('GET', '/cards'),
    addCard: (id, card) => call('POST', `/decks/${id}/cards`, card),
    deleteCard: (id, cardId) => call('DELETE', `/decks/${id}/cards/${cardId}`),
    dueCards: (id) => call('GET', id ? `/decks/${id}/study` : '/study'),
    review: (id, cardId, correct) => call('POST', `/decks/${id}/cards/${cardId}/review`, { correct }),
    // Antwort ist eine PDF-Datei, kein JSON – darum ein eigener Aufruf statt createCall (siehe pdfcreatorApi.js).
    druckbogen: async (id, format = 'a7') => {
      const res = await fetch(`${base}/decks/${id}/druckbogen?format=${format}`)
      if (res.status === 401) loggedIn.value = false
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(typeof err.detail === 'string' ? err.detail : 'Etwas ist schiefgelaufen.')
      }
      return res.blob()
    },
  }
}
