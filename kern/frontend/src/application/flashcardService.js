// Anwendungsschicht der UI: kennt nur den "api"-Port (ein Objekt mit diesen Methoden), nicht HTTP.
import { pdfZeigen } from './pdf'

export function createFlashcardService(api) {
  return {
    listDecks: () => api.listDecks(),
    createDeck: (name) => api.createDeck(name.trim()),
    openDeck: (id) => api.getDeck(id),
    deleteDeck: (id) => api.deleteDeck(id),
    allCards: () => api.allCards(),
    addCard: (id, card) => api.addCard(id, {
      ...card,
      front: card.front.trim(),
      back: (card.back || '').trim(),
      options: (card.options || []).map((o) => o.trim()),
    }),
    deleteCard: (id, cardId) => api.deleteCard(id, cardId),
    startSession: (deckId) => api.dueCards(deckId), // deckId leer = alle Fächer
    answer: (deckId, cardId, correct) => api.review(deckId, cardId, correct),
    async drucken(deckId, deckName, fenster, format = 'a7') {
      const blob = await api.druckbogen(deckId, format)
      pdfZeigen(fenster, blob, `Karteikarten ${deckName}.pdf`)
    },
  }
}
