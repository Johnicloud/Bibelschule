"""Ausgehender Adapter: speichert alles in einer JSON-Datei (atomar, mit täglicher Sicherung).

Wichtig für die Daten: neue Felder immer mit .get(..., Standardwert) lesen, alte Felder nie umbenennen oder
löschen, ohne die Datei zu migrieren. So bleiben vorhandene Daten beim Erweitern des Dienstes erhalten."""
import json
import threading
from pathlib import Path

from app.adapters.outbound.storage import atomic_write_text, daily_backup
from app.application.ports import ItemRepository
from app.domain.models import Item


class JsonItemRepository(ItemRepository):
    def __init__(self, path: Path):
        self.path = Path(path)
        self._lock = threading.Lock()

    def _read(self) -> dict[str, Item]:
        if not self.path.exists():
            return {}
        return {d["id"]: Item(id=d["id"], subject_id=d["subject_id"], text=d["text"])
                for d in json.loads(self.path.read_text("utf-8"))}

    def _write(self, items: dict[str, Item]) -> None:
        daily_backup(self.path)
        atomic_write_text(self.path, json.dumps(
            [{"id": i.id, "subject_id": i.subject_id, "text": i.text} for i in items.values()],
            ensure_ascii=False, indent=2))

    def list(self, subject_id: str | None = None) -> list[Item]:
        with self._lock:
            return [i for i in self._read().values() if subject_id is None or i.subject_id == subject_id]

    def get(self, item_id: str) -> Item | None:
        with self._lock:
            return self._read().get(item_id)

    def save(self, item: Item) -> None:
        with self._lock:
            items = self._read()
            items[item.id] = item
            self._write(items)

    def delete(self, item_id: str) -> None:
        with self._lock:
            items = self._read()
            items.pop(item_id, None)
            self._write(items)

    def delete_subject(self, subject_id: str) -> None:
        with self._lock:
            self._write({k: i for k, i in self._read().items() if i.subject_id != subject_id})
