"""Eingehender Adapter: HTTP-API (FastAPI) ruft die Anwendungsfälle auf.
Interaktive Doku: /api/docs  ·  Schema: /api/openapi.json (auch für übergeordnete Services nutzbar)."""
from typing import Literal

from fastapi import APIRouter, FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.application.services import FlashcardService, Pair
from app.domain.errors import InvalidInput, NotFound
from app.domain.models import Deck


class DeckIn(BaseModel):
    name: str


class CardIn(BaseModel):
    kind: Literal["classic", "choice", "truefalse"] = "classic"
    front: str
    back: str = ""
    options: list[str] = Field(default_factory=list)
    correct_index: int | None = None


class SubjectIn(BaseModel):
    name: str


class ReviewIn(BaseModel):
    correct: bool


def card_out(pair: Pair) -> dict:
    deck, c = pair
    return {"id": c.id, "deck_id": deck.id, "deck_name": deck.name, "kind": c.kind,
            "front": c.front, "back": c.back, "options": c.options,
            "correct_index": c.correct_index, "box": c.box,
            "due": c.due.isoformat(), "is_due": c.is_due()}


def deck_out(d: Deck, with_cards: bool = False) -> dict:
    out = {"id": d.id, "name": d.name, "card_count": len(d.cards), "due_count": len(d.due_cards())}
    if with_cards:
        out["cards"] = [card_out((d, c)) for c in d.cards]
    return out


def create_app(service: FlashcardService) -> FastAPI:
    app = FastAPI(title="Karteikarten", docs_url="/api/docs", openapi_url="/api/openapi.json")
    api = APIRouter(prefix="/api")

    @app.exception_handler(NotFound)
    async def _not_found(_, e):
        return JSONResponse({"detail": str(e)}, status_code=404)

    @app.exception_handler(InvalidInput)
    async def _invalid(_, e):
        return JSONResponse({"detail": str(e)}, status_code=422)

    @api.get("/health")
    def health():
        return {"status": "ok"}

    @api.get("/decks")
    def list_decks():
        return [deck_out(d) for d in service.list_decks()]

    @api.post("/decks", status_code=201)
    def create_deck(body: DeckIn):
        return deck_out(service.create_deck(body.name))

    @api.get("/decks/{deck_id}")
    def get_deck(deck_id: str):
        return deck_out(service.get_deck(deck_id), with_cards=True)

    @api.delete("/decks/{deck_id}", status_code=204)
    def delete_deck(deck_id: str):
        service.delete_deck(deck_id)

    @api.get("/cards")
    def all_cards():
        return [card_out(p) for p in service.all_cards()]

    @api.post("/decks/{deck_id}/cards", status_code=201)
    def add_card(deck_id: str, body: CardIn):
        return card_out(service.add_card(deck_id, body.kind, body.front, body.back,
                                         body.options, body.correct_index))

    @api.delete("/decks/{deck_id}/cards/{card_id}", status_code=204)
    def delete_card(deck_id: str, card_id: str):
        service.delete_card(deck_id, card_id)

    @api.get("/study")
    def study_all():
        return [card_out(p) for p in service.due_cards()]

    @api.get("/decks/{deck_id}/study")
    def study_deck(deck_id: str):
        return [card_out(p) for p in service.due_cards(deck_id)]

    @api.post("/decks/{deck_id}/cards/{card_id}/review")
    def review(deck_id: str, card_id: str, body: ReviewIn):
        return card_out(service.review_card(deck_id, card_id, body.correct))

    @api.get("/manifest")
    def manifest():
        """Steckbrief für den Kern: so zeigt die Oberfläche diesen Dienst an."""
        return {"name": "karteikarten", "label": "Karteikarten", "panel": None,
                "status": [{"key": "due_count", "label": "fällig"}, {"key": "card_count", "label": "Karten"}]}

    # Fach-Hooks: so hängt sich dieser Dienst an die zentrale Fächerverwaltung des Kerns.
    @api.get("/subjects")
    def list_subjects():
        """Bestehende Fächer dieses Dienstes. Der Kern übernimmt unbekannte als Fächer (so gehen alte Karten nicht verloren)."""
        return [{"id": d.id, "name": d.name} for d in service.list_decks()]

    @api.put("/subjects/{subject_id}", status_code=204)
    def put_subject(subject_id: str, body: SubjectIn):
        service.ensure_deck(subject_id, body.name)

    @api.delete("/subjects/{subject_id}", status_code=204)
    def delete_subject(subject_id: str):
        service.discard_deck(subject_id)

    @api.get("/subjects/{subject_id}/status")
    def subject_status(subject_id: str):
        return service.deck_status(subject_id)

    app.include_router(api)
    return app
