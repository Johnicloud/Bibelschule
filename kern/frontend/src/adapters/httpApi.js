import { createCall } from './http'

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
  }
}
