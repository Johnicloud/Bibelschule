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
