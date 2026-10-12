"""Anwendungsfälle. Kennen nur Domäne und Ports."""
from app.application.ports import DeckRepository, EventPublisher
from app.domain.errors import InvalidInput, NotFound
from app.domain.models import TRUE_FALSE, Card, Deck

Pair = tuple[Deck, Card]


def _clean(text: str, what: str) -> str:
    text = (text or "").strip()
    if not text:
        raise InvalidInput(f"{what} darf nicht leer sein.")
    return text


def build_card(kind: str, front: str, back: str, options: list[str], correct_index: int | None) -> Card:
    front = _clean(front, "Die Frage")
    if kind == "classic":
        return Card(front=front, back=_clean(back, "Die Rückseite"))
    if kind == "choice":
        opts = [(o or "").strip() for o in options or []]
        if len(opts) != 4 or not all(opts):
            raise InvalidInput("Es braucht genau 4 Antworten, keine darf leer sein.")
        if correct_index not in range(4):
            raise InvalidInput("Wähle die richtige Antwort aus.")
        return Card(front=front, back=opts[correct_index], kind=kind, options=opts, correct_index=correct_index)
    if kind == "truefalse":
        if correct_index not in (0, 1):
            raise InvalidInput("Wähle Richtig oder Falsch.")
        return Card(front=front, back=TRUE_FALSE[correct_index], kind=kind,
                    options=list(TRUE_FALSE), correct_index=correct_index)
    raise InvalidInput("Unbekannter Kartentyp.")


class FlashcardService:
    def __init__(self, decks: DeckRepository, events: EventPublisher | None = None):
        self.decks = decks
        self.events = events

    def _emit(self, event: str, payload: dict) -> None:
        if self.events:
            self.events.publish(event, payload)

    def _deck(self, deck_id: str) -> Deck:
        deck = self.decks.get(deck_id)
        if deck is None:
            raise NotFound("Fach nicht gefunden.")
        return deck

    # Fächer
    def list_decks(self) -> list[Deck]:
        return self.decks.list()

    def create_deck(self, name: str) -> Deck:
        deck = Deck(name=_clean(name, "Der Name"))
        self.decks.save(deck)
        self._emit("deck.created", {"deck_id": deck.id, "name": deck.name})
        return deck

    def get_deck(self, deck_id: str) -> Deck:
        return self._deck(deck_id)

    def delete_deck(self, deck_id: str) -> None:
        deck = self._deck(deck_id)
        self.decks.delete(deck_id)
        self._emit("deck.deleted", {"deck_id": deck.id, "name": deck.name})

    # Karteikarten
    def add_card(self, deck_id: str, kind: str, front: str, back: str = "",
                 options: list[str] | None = None, correct_index: int | None = None) -> Pair:
        deck = self._deck(deck_id)
        card = build_card(kind, front, back, options or [], correct_index)
        deck.cards.append(card)
        self.decks.save(deck)
        self._emit("card.created", {"deck_id": deck.id, "card_id": card.id, "kind": card.kind})
        return deck, card

    def delete_card(self, deck_id: str, card_id: str) -> None:
        deck = self._deck(deck_id)
        card = deck.get_card(card_id)
        if card is None:
            raise NotFound("Karteikarte nicht gefunden.")
        deck.cards.remove(card)
        self.decks.save(deck)
        self._emit("card.deleted", {"deck_id": deck.id, "card_id": card.id})

    def all_cards(self) -> list[Pair]:
        pairs = [(d, c) for d in self.decks.list() for c in d.cards]
        return sorted(pairs, key=lambda p: p[1].due)

    # Lernen
    def due_cards(self, deck_id: str | None = None) -> list[Pair]:
        decks = [self._deck(deck_id)] if deck_id else self.decks.list()
        pairs = [(d, c) for d in decks for c in d.due_cards()]
        return sorted(pairs, key=lambda p: p[1].due)

    def review_card(self, deck_id: str, card_id: str, correct: bool) -> Pair:
        deck = self._deck(deck_id)
        card = deck.get_card(card_id)
        if card is None:
            raise NotFound("Karteikarte nicht gefunden.")
        card.review(correct)
        self.decks.save(deck)
        self._emit("card.reviewed", {"deck_id": deck.id, "card_id": card.id, "correct": correct,
                                     "box": card.box, "due": card.due.isoformat()})
        return deck, card
