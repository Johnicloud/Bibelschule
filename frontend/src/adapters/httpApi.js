// Ausgehender Adapter: spricht per HTTP mit dem Python-Backend.
export function createHttpApi(base = '/api') {
  async function call(method, path, body) {
    const res = await fetch(base + path, {
      method,
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(typeof err.detail === 'string' ? err.detail : 'Etwas ist schiefgelaufen.')
    }
    return res.status === 204 ? null : res.json()
  }
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
