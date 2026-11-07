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
    updateCard: (id, cardId, card) => api.updateCard(id, cardId, {
      ...card,
      front: card.front.trim(),
      back: (card.back || '').trim(),
      options: (card.options || []).map((o) => o.trim()),
    }),
    createSet: (id, name) => api.createSet(id, name.trim()),
    renameSet: (id, name, neu) => api.renameSet(id, name, neu.trim()),
    deleteSet: (id, name, mitKarten = false) => api.deleteSet(id, name, mitKarten),
    deleteCard: (id, cardId) => api.deleteCard(id, cardId),
    startSession: (deckId) => api.dueCards(deckId), // deckId leer = alle Fächer
    answer: (deckId, cardId, correct) => api.review(deckId, cardId, correct),
    async drucken(deckId, deckName, fenster, format = 'a7') {
      const blob = await api.druckbogen(deckId, format)
      pdfZeigen(fenster, blob, `Karteikarten ${deckName}.pdf`)
    },
  }
}
