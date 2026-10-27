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


def test_druckbogen_needs_cards_and_a_renderer(svc):
    deck = svc.create_deck("Bio")
    with pytest.raises(InvalidInput):
        svc.druckbogen(deck.id)   # keine Karten
    svc.add_card(deck.id, "classic", "a", "b")
    with pytest.raises(InvalidInput):
        svc.druckbogen(deck.id)   # kein Renderer verdrahtet
    with pytest.raises(NotFound):
        svc.druckbogen("unbekannt")


def test_druckbogen_calls_the_renderer_with_the_decks_cards():
    class FakeRenderer:
        def druckbogen(self, cards, format="a7"):
            self.cards, self.format = cards, format
            return b"%PDF-fake"
    renderer = FakeRenderer()
    svc = FlashcardService(InMemoryRepo(), printer=renderer)
    deck = svc.create_deck("Bio")
    svc.add_card(deck.id, "classic", "a", "b")
    assert svc.druckbogen(deck.id) == b"%PDF-fake"
    assert len(renderer.cards) == 1 and renderer.cards[0].front == "a"
    assert renderer.format == "a7"
    svc.druckbogen(deck.id, "a8")
    assert renderer.format == "a8"
    with pytest.raises(InvalidInput):
        svc.druckbogen(deck.id, "a4")


def test_subject_hooks(svc, events):
    deck = svc.ensure_deck("fach1", "Dogmatik")
    assert deck.id == "fach1" and events.sent == ["deck.created"]
    assert svc.ensure_deck("fach1", "Dogmatik II").name == "Dogmatik II"
    assert events.sent == ["deck.created"]  # Umbenennen ist kein neues Fach
    svc.add_card("fach1", "classic", "a", "b")
    assert svc.deck_status("fach1") == {"card_count": 1, "due_count": 1, "mastered": 0, "progress": 0}
    assert svc.deck_status("unbekannt") == {"card_count": 0, "due_count": 0, "mastered": 0, "progress": None}
    svc.discard_deck("fach1")
    svc.discard_deck("fach1")  # zweites Mal tut nichts
    assert svc.list_decks() == []


def test_karte_merkt_sich_ihr_set_auch_nach_dem_speichern(svc, tmp_path):
    from app.adapters.outbound.json_repository import JsonDeckRepository
    deck = svc.create_deck("Apg")
    svc.add_card(deck.id, "classic", "Frage?", "Antwort", set_name="  Fragen Apostelgeschichte ")
    svc.add_card(deck.id, "classic", "Ohne Set?", "Ja")
    assert [c.set_name for c in svc.get_deck(deck.id).cards] == ["Fragen Apostelgeschichte", ""]
    repo = JsonDeckRepository(tmp_path / "decks.json")
    repo.save(svc.get_deck(deck.id))
    assert [c.set_name for c in repo.get(deck.id).cards] == ["Fragen Apostelgeschichte", ""]


def test_karte_bearbeiten_aendert_den_inhalt_aber_nicht_den_lernstand(svc, events):
    deck = svc.create_deck("Apg")
    _, card = svc.add_card(deck.id, "classic", "Alt?", "Alt", set_name="Set A")
    svc.review_card(deck.id, card.id, True)
    stufe, faellig = svc.get_deck(deck.id).cards[0].box, svc.get_deck(deck.id).cards[0].due
    _, neu = svc.update_card(deck.id, card.id, "classic", " Neu? ", " Neu ")
    gespeichert = svc.get_deck(deck.id).cards[0]
    assert (gespeichert.front, gespeichert.back) == ("Neu?", "Neu")
    assert (gespeichert.id, gespeichert.box, gespeichert.due) == (card.id, stufe, faellig)   # Bearbeiten ist kein Lernerfolg
    assert gespeichert.set_name == "Set A"                      # ohne Angabe bleibt das Set
    assert "card.updated" in events.sent


def test_karte_bearbeiten_kann_typ_und_set_wechseln(svc):
    deck = svc.create_deck("Apg")
    _, card = svc.add_card(deck.id, "classic", "Frage?", "Antwort")
    svc.update_card(deck.id, card.id, "choice", "Frage?", "", ["a", "b", "c", "d"], 2, set_name="Neues Set")
    c = svc.get_deck(deck.id).cards[0]
    assert (c.kind, c.back, c.correct_index, c.set_name) == ("choice", "c", 2, "Neues Set")
    svc.update_card(deck.id, card.id, "classic", "Frage?", "Antwort", set_name="")
    assert svc.get_deck(deck.id).cards[0].set_name == ""      # leerer Name nimmt die Karte aus dem Set


def test_karte_bearbeiten_prueft_wie_beim_anlegen(svc):
    deck = svc.create_deck("Apg")
    _, card = svc.add_card(deck.id, "classic", "Frage?", "Antwort")
    with pytest.raises(InvalidInput):
        svc.update_card(deck.id, card.id, "classic", "  ", "x")
    with pytest.raises(InvalidInput):
        svc.update_card(deck.id, card.id, "classic", "Frage?", " ")
    assert svc.get_deck(deck.id).cards[0].front == "Frage?"     # abgelehnte Änderung lässt die Karte unverändert
    with pytest.raises(NotFound):
        svc.update_card(deck.id, "gibts-nicht", "classic", "a", "b")


# ---- Sets: eine Ebene unter dem Fach ----

def test_set_anlegen_ist_auch_ohne_karten_sichtbar_und_eindeutig(svc):
    deck = svc.create_deck("Apg")
    svc.create_set(deck.id, "  Fragen 1 ")
    assert svc.get_deck(deck.id).set_namen() == ["Fragen 1"]
    with pytest.raises(InvalidInput):
        svc.create_set(deck.id, "fragen 1")          # gleicher Name, Groß/Klein egal
    with pytest.raises(InvalidInput):
        svc.create_set(deck.id, "  ")


def test_karte_landet_im_bestehenden_set_auch_bei_anderer_schreibweise(svc):
    deck = svc.create_deck("Apg")
    svc.create_set(deck.id, "Fragen 1")
    _, karte = svc.add_card(deck.id, "classic", "F?", "A", set_name="fragen 1")
    assert karte.set_name == "Fragen 1"
    svc.add_card(deck.id, "classic", "G?", "B", set_name="Nur auf Karte")       # nie angelegt, entsteht durch die Karte
    assert svc.get_deck(deck.id).set_namen() == ["Fragen 1", "Nur auf Karte"]


def test_set_umbenennen_aendert_alle_karten(svc):
    deck = svc.create_deck("Apg")
    svc.create_set(deck.id, "Alt")
    svc.add_card(deck.id, "classic", "F?", "A", set_name="Alt")
    svc.add_card(deck.id, "classic", "G?", "B", set_name="Anderes")
    svc.rename_set(deck.id, "Alt", "Neu")
    d = svc.get_deck(deck.id)
    assert d.set_namen() == ["Neu", "Anderes"]
    assert [c.set_name for c in d.cards] == ["Neu", "Anderes"]
    with pytest.raises(InvalidInput):
        svc.rename_set(deck.id, "Neu", "anderes")        # würde zwei Sets zusammenwerfen
    with pytest.raises(NotFound):
        svc.rename_set(deck.id, "Gibt es nicht", "X")
    svc.rename_set(deck.id, "Neu", "neu")                 # nur die Schreibweise ändern geht


def test_set_loeschen_behaelt_die_karten_oder_loescht_sie_mit(svc):
    deck = svc.create_deck("Apg")
    svc.add_card(deck.id, "classic", "F?", "A", set_name="Weg")
    svc.add_card(deck.id, "classic", "G?", "B", set_name="Weg")
    svc.delete_set(deck.id, "Weg")
    d = svc.get_deck(deck.id)
    assert d.set_namen() == [] and [c.set_name for c in d.cards] == ["", ""]
    svc.add_card(deck.id, "classic", "H?", "C", set_name="Mit")
    svc.delete_set(deck.id, "Mit", mit_karten=True)
    assert [c.front for c in svc.get_deck(deck.id).cards] == ["F?", "G?"]
    with pytest.raises(NotFound):
        svc.delete_set(deck.id, "Mit")


def test_sets_ueberleben_das_speichern(svc, tmp_path):
    from app.adapters.outbound.json_repository import JsonDeckRepository
    deck = svc.create_deck("Apg")
    svc.create_set(deck.id, "Leer")
    repo = JsonDeckRepository(tmp_path / "decks.json")
    repo.save(svc.get_deck(deck.id))
    assert repo.get(deck.id).sets == ["Leer"]
