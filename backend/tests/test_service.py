import pytest
from app.application.ports import DeckRepository, EventPublisher
from app.application.services import FlashcardService
from app.domain.errors import InvalidInput, NotFound


class InMemoryRepo(DeckRepository):
    def __init__(self): self.d = {}
    def list(self): return list(self.d.values())
    def get(self, i): return self.d.get(i)
    def save(self, deck): self.d[deck.id] = deck
    def delete(self, i): self.d.pop(i, None)


class FakeEvents(EventPublisher):
    def __init__(self): self.sent = []
    def publish(self, event, payload): self.sent.append(event)


@pytest.fixture
def events():
    return FakeEvents()


@pytest.fixture
def svc(events):
    return FlashcardService(InMemoryRepo(), events)


def test_classic_flow(svc):
    deck = svc.create_deck("Biologie")
    _, card = svc.add_card(deck.id, "classic", "Zellkern", "Enthält die DNA")
    assert [c.id for _, c in svc.due_cards(deck.id)] == [card.id]


def test_choice_card(svc):
    deck = svc.create_deck("Bio")
    _, card = svc.add_card(deck.id, "choice", "2+2?", options=["3", "4", "5", "6"], correct_index=1)
    assert card.back == "4"
    with pytest.raises(InvalidInput):
        svc.add_card(deck.id, "choice", "x", options=["a", "b", "c"], correct_index=0)


def test_truefalse_card(svc):
    deck = svc.create_deck("Bio")
    _, card = svc.add_card(deck.id, "truefalse", "Wasser kocht bei 100 °C", correct_index=0)
    assert card.options == ["Richtig", "Falsch"] and card.back == "Richtig"


def test_review_and_due(svc):
    deck = svc.create_deck("Bio")
    _, card = svc.add_card(deck.id, "classic", "a", "b")
    svc.review_card(deck.id, card.id, True)
    assert svc.due_cards(deck.id) == []
    _, again = svc.review_card(deck.id, card.id, False)
    assert again.box == 0


def test_all_cards_and_events(svc, events):
    a, b = svc.create_deck("A"), svc.create_deck("B")
    svc.add_card(a.id, "classic", "1", "1")
    svc.add_card(b.id, "classic", "2", "2")
    assert len(svc.all_cards()) == 2 and len(svc.due_cards()) == 2
    assert events.sent.count("card.created") == 2


def test_validation(svc):
    with pytest.raises(InvalidInput):
        svc.create_deck("  ")
    with pytest.raises(NotFound):
        svc.get_deck("x")
