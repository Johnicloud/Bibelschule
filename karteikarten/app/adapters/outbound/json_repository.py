"""Ausgehender Adapter: speichert alle Fächer in einer JSON-Datei."""
import json
import threading
from datetime import datetime
from pathlib import Path

from app.application.ports import DeckRepository
from app.adapters.outbound.storage import atomic_write_text, daily_backup
from app.domain.models import Card, Deck


def _to_dict(d: Deck) -> dict:
    return {"id": d.id, "name": d.name, "cards": [
        {"id": c.id, "kind": c.kind, "front": c.front, "back": c.back, "options": c.options,
         "correct_index": c.correct_index, "box": c.box, "due": c.due.isoformat()}
        for c in d.cards]}


def _from_dict(d: dict) -> Deck:
    return Deck(id=d["id"], name=d["name"], cards=[
        Card(id=c["id"], kind=c.get("kind", "classic"), front=c["front"], back=c["back"],
             options=c.get("options", []), correct_index=c.get("correct_index"),
             box=c["box"], due=datetime.fromisoformat(c["due"])) for c in d["cards"]])


class JsonDeckRepository(DeckRepository):
    def __init__(self, path: Path):
        self.path = Path(path)
        self._lock = threading.Lock()

    def _read(self) -> dict[str, Deck]:
        if not self.path.exists():
            return {}
        return {d["id"]: _from_dict(d) for d in json.loads(self.path.read_text("utf-8"))}

    def _write(self, decks: dict[str, Deck]) -> None:
        daily_backup(self.path)
        atomic_write_text(self.path, json.dumps([_to_dict(d) for d in decks.values()], ensure_ascii=False, indent=2))

    def list(self) -> list[Deck]:
        with self._lock:
            return list(self._read().values())

    def get(self, deck_id: str) -> Deck | None:
        with self._lock:
            return self._read().get(deck_id)

    def save(self, deck: Deck) -> None:
        with self._lock:
            decks = self._read()
            decks[deck.id] = deck
            self._write(decks)

    def delete(self, deck_id: str) -> None:
        with self._lock:
            decks = self._read()
            decks.pop(deck_id, None)
            self._write(decks)
