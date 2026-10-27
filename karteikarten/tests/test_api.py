from app.adapters.inbound.api import create_app
from app.application.services import FlashcardService
from fastapi.testclient import TestClient
from tests.test_service import InMemoryRepo


def test_karte_bearbeiten_ueber_die_api_set_nur_bei_angabe_aendern():
    service = FlashcardService(InMemoryRepo())
    deck = service.create_deck("Apg")
    _, card = service.add_card(deck.id, "classic", "Alt?", "Alt", set_name="Set A")
    client = TestClient(create_app(service))
    url = f"/api/decks/{deck.id}/cards/{card.id}"

    antwort = client.put(url, json={"kind": "classic", "front": "Neu?", "back": "Neu"})   # ohne set_name: bleibt
    assert antwort.status_code == 200
    assert (antwort.json()["front"], antwort.json()["set_name"]) == ("Neu?", "Set A")

    antwort = client.put(url, json={"kind": "classic", "front": "Neu?", "back": "Neu", "set_name": ""})   # leer: raus aus dem Set
    assert antwort.json()["set_name"] == ""

    assert client.put(url, json={"kind": "classic", "front": " ", "back": "x"}).status_code == 422
    assert client.put(f"/api/decks/{deck.id}/cards/unbekannt", json={"kind": "classic", "front": "a", "back": "b"}).status_code == 404


def test_sets_ueber_die_api():
    service = FlashcardService(InMemoryRepo())
    deck = service.create_deck("Apg")
    client = TestClient(create_app(service))
    assert client.post(f"/api/decks/{deck.id}/sets", json={"name": "Fragen / 1"}).status_code == 201
    service.add_card(deck.id, "classic", "F?", "A", set_name="Fragen / 1")
    sets = client.get(f"/api/decks/{deck.id}").json()["sets"]
    assert sets == [{"name": "Fragen / 1", "card_count": 1, "due_count": 1}]
    assert client.post(f"/api/decks/{deck.id}/sets", json={"name": "fragen / 1"}).status_code == 422
    antwort = client.put(f"/api/decks/{deck.id}/sets", json={"name": "Fragen / 1", "neu": "Lektion 1"})
    assert [s["name"] for s in antwort.json()["sets"]] == ["Lektion 1"]
    antwort = client.delete(f"/api/decks/{deck.id}/sets", params={"name": "Lektion 1"})
    assert antwort.json()["sets"] == [] and antwort.json()["card_count"] == 1       # Karten bleiben
    assert client.delete(f"/api/decks/{deck.id}/sets", params={"name": "Lektion 1"}).status_code == 404
