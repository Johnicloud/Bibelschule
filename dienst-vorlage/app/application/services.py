"""Anwendungsfälle. Kennen nur Domäne und Ports."""
from app.application.ports import EventPublisher, ItemRepository
from app.domain.errors import InvalidInput, NotFound
from app.domain.models import Item


class ItemService:
    def __init__(self, repo: ItemRepository, events: EventPublisher | None = None):
        self.repo = repo
        self.events = events

    def _emit(self, event: str, payload: dict) -> None:
        if self.events:
            self.events.publish(event, payload)

    def add_item(self, subject_id: str, text: str) -> Item:
        text = (text or "").strip()
        if not text:
            raise InvalidInput("Der Eintrag darf nicht leer sein.")
        item = Item(subject_id=subject_id, text=text)
        self.repo.save(item)
        self._emit("__NAME__.item_added", {"subject_id": subject_id, "item_id": item.id})
        return item

    def list_items(self, subject_id: str | None = None) -> list[Item]:
        return self.repo.list(subject_id)

    def delete_item(self, item_id: str) -> None:
        item = self.repo.get(item_id)
        if item is None:
            raise NotFound("Eintrag nicht gefunden.")
        self.repo.delete(item_id)
        self._emit("__NAME__.item_deleted", {"subject_id": item.subject_id, "item_id": item.id})

    # Fach-Hooks
    def discard_subject(self, subject_id: str) -> None:
        self.repo.delete_subject(subject_id)

    def subject_status(self, subject_id: str) -> dict:
        """Kennzahlen für die Startseite. Die Schlüssel stehen im Manifest (api.py), die Oberfläche zeigt sie von selbst.
        Optional: ein Schlüssel "progress" (ganze Zahl 0 bis 100, oder None, wenn es nichts zu messen gibt) zählt
        automatisch in den Gesamtfortschritt des Fachs, den der Kern als Mittel aller Dienste berechnet."""
        return {"count": len(self.repo.list(subject_id))}
