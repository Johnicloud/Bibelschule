"""Anwendungsfälle. Kennen nur Domäne und Ports."""
from app.application.ports import DeckRepository, EventPublisher, PrintRenderer
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


def _set_fuer_karte(deck: Deck, set_name: str | None) -> str:
    """Name des Sets, in das eine Karte kommt: ein vorhandenes (Schreibweise egal) oder der neue Name, leer = kein Set."""
    name = (set_name or "").strip()
    return deck.finde_set(name) or name


class FlashcardService:
    def __init__(self, decks: DeckRepository, events: EventPublisher | None = None,
                 printer: PrintRenderer | None = None):
        self.decks = decks
        self.events = events
        self.printer = printer

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

    def ensure_deck(self, deck_id: str, name: str) -> Deck:
        """Fach-Hook der Bibelschule: legt das Fach mit der Fach-ID des Kerns an oder benennt es um."""
        name = _clean(name, "Der Name")
        deck = self.decks.get(deck_id)
        if deck is None:
            deck = Deck(id=deck_id, name=name)
            self.decks.save(deck)
            self._emit("deck.created", {"deck_id": deck.id, "name": deck.name})
        elif deck.name != name:
            deck.name = name
            self.decks.save(deck)
        return deck

    def discard_deck(self, deck_id: str) -> None:
        """Fach-Hook: löscht das Fach, falls es existiert (mehrfach aufrufbar)."""
        if self.decks.get(deck_id) is not None:
            self.delete_deck(deck_id)

    def deck_status(self, deck_id: str) -> dict:
        deck = self.decks.get(deck_id)
        cards = deck.cards if deck else []
        return {"card_count": len(cards),
                "due_count": len(deck.due_cards()) if deck else 0,
                "mastered": sum(1 for c in cards if c.box >= 4),
                # je Set: Karten und sicher gelernte – der Kern braucht das für Aufgaben, die an ein Set geknüpft sind
                "sets": [{"name": n, "card_count": sum(1 for c in cards if c.set_name == n),
                          "mastered": sum(1 for c in cards if c.set_name == n and c.box >= 4)}
                         for n in (deck.set_namen() if deck else [])],
                # Fortschritt dieses Fachs in Prozent: Anteil der Karten auf Lernstufe 4 oder höher ("sicher gelernt")
                "progress": int(100 * sum(1 for c in cards if c.box >= 4) / len(cards) + 0.5) if cards else None}

    def get_deck(self, deck_id: str) -> Deck:
        return self._deck(deck_id)

    def delete_deck(self, deck_id: str) -> None:
        deck = self._deck(deck_id)
        self.decks.delete(deck_id)
        self._emit("deck.deleted", {"deck_id": deck.id, "name": deck.name})

    # Karteikarten
    def add_card(self, deck_id: str, kind: str, front: str, back: str = "",
                 options: list[str] | None = None, correct_index: int | None = None, set_name: str = "") -> Pair:
        deck = self._deck(deck_id)
        card = build_card(kind, front, back, options or [], correct_index)
        card.set_name = _set_fuer_karte(deck, set_name)
        deck.cards.append(card)
        self.decks.save(deck)
        self._emit("card.created", {"deck_id": deck.id, "card_id": card.id, "kind": card.kind})
        return deck, card

    def update_card(self, deck_id: str, card_id: str, kind: str, front: str, back: str = "",
                    options: list[str] | None = None, correct_index: int | None = None,
                    set_name: str | None = None) -> Pair:
        """Inhalt einer Karte ändern. Lernstufe und Fälligkeit bleiben (Bearbeiten ist kein Lernerfolg).
        `set_name=None` lässt das Set unverändert, ein leerer Text nimmt die Karte aus dem Set."""
        deck = self._deck(deck_id)
        card = deck.get_card(card_id)
        if card is None:
            raise NotFound("Karteikarte nicht gefunden.")
        neu = build_card(kind, front, back, options or [], correct_index)     # prüft wie beim Anlegen
        card.kind, card.front, card.back = neu.kind, neu.front, neu.back
        card.options, card.correct_index = neu.options, neu.correct_index
        if set_name is not None:
            card.set_name = _set_fuer_karte(deck, set_name)
        self.decks.save(deck)
        self._emit("card.updated", {"deck_id": deck.id, "card_id": card.id, "kind": card.kind})
        return deck, card

    # Sets: eine Ebene unter dem Fach (Fach > Set > Karten)
    def create_set(self, deck_id: str, name: str) -> Deck:
        deck = self._deck(deck_id)
        name = _clean(name, "Der Name des Sets")
        if deck.finde_set(name):
            raise InvalidInput("Ein Set mit diesem Namen gibt es schon.")
        deck.sets.append(name)
        self.decks.save(deck)
        self._emit("set.created", {"deck_id": deck.id, "name": name})
        return deck

    def rename_set(self, deck_id: str, name: str, neu: str) -> Deck:
        deck = self._deck(deck_id)
        alt = deck.finde_set(name)
        if alt is None:
            raise NotFound("Set nicht gefunden.")
        neu = _clean(neu, "Der Name des Sets")
        vorhanden = deck.finde_set(neu)
        if vorhanden is not None and vorhanden != alt:
            raise InvalidInput("Ein Set mit diesem Namen gibt es schon.")
        deck.sets = [neu if n == alt else n for n in deck.sets]      # Reihenfolge bleibt
        for c in deck.cards:
            if c.set_name == alt:
                c.set_name = neu
        self.decks.save(deck)
        self._emit("set.renamed", {"deck_id": deck.id, "name": alt, "neu": neu})
        return deck

    def delete_set(self, deck_id: str, name: str, mit_karten: bool = False) -> Deck:
        deck = self._deck(deck_id)
        alt = deck.finde_set(name)
        if alt is None:
            raise NotFound("Set nicht gefunden.")
        deck.sets = [n for n in deck.sets if n != alt]
        if mit_karten:
            deck.cards = [c for c in deck.cards if c.set_name != alt]
        else:
            for c in deck.cards:
                if c.set_name == alt:
                    c.set_name = ""
        self.decks.save(deck)
        self._emit("set.deleted", {"deck_id": deck.id, "name": alt, "mit_karten": mit_karten})
        return deck

    def delete_card(self, deck_id: str, card_id: str) -> None:
        deck = self._deck(deck_id)
        card = deck.get_card(card_id)
        if card is None:
            raise NotFound("Karteikarte nicht gefunden.")
        deck.cards.remove(card)
        self.decks.save(deck)
        self._emit("card.deleted", {"deck_id": deck.id, "card_id": card.id})

    def druckbogen(self, deck_id: str, format: str = "a7") -> bytes:
        deck = self._deck(deck_id)
        if not deck.cards:
            raise InvalidInput("Dieses Fach hat keine Karten zum Drucken.")
        if self.printer is None:
            raise InvalidInput("Drucken ist gerade nicht verfügbar.")
        if format not in ("a7", "a8"):
            raise InvalidInput("Format muss a7 oder a8 sein.")
        return self.printer.druckbogen(deck.cards, format)

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
