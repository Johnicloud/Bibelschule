"""Anwendungsfälle. Kennen nur Domäne und Ports."""
from datetime import date
from typing import Callable

from app.application.ports import EventPublisher, ReadingRepository
from app.domain.errors import InvalidInput, NotFound
from app.domain.forecast import STATUS_ORDER, Forecast, forecast, worst_status
from app.domain.models import UNITS, ReadingEntry, ReadingTask

MAX_PASSES = 20


def _clean(text: str, what: str) -> str:
    text = (text or "").strip()
    if not text:
        raise InvalidInput(f"{what} darf nicht leer sein.")
    return text


class ReadingService:
    def __init__(self, repo: ReadingRepository, events: EventPublisher | None = None,
                 today: Callable[[], date] = date.today):
        self.repo = repo
        self.events = events
        self.today = today

    def _emit(self, event: str, payload: dict) -> None:
        if self.events:
            self.events.publish(event, payload)

    def _task(self, task_id: str) -> ReadingTask:
        task = self.repo.get(task_id)
        if task is None:
            raise NotFound("Lesepensum nicht gefunden.")
        return task

    # Pensen
    def add_task(self, subject_id: str, title: str, unit: str, total: int, passes: int = 1,
                 start: date | None = None, deadline: date | None = None) -> ReadingTask:
        if unit not in UNITS:
            raise InvalidInput("Die Einheit ist Seiten oder Kapitel.")
        if not isinstance(total, int) or total < 1:
            raise InvalidInput(f"Der Umfang muss mindestens 1 sein ({unit}).")
        if not isinstance(passes, int) or not 1 <= passes <= MAX_PASSES:
            raise InvalidInput(f"Die Zahl der Durchgänge liegt zwischen 1 und {MAX_PASSES}.")
        if start and deadline and start >= deadline:
            raise InvalidInput("Der Starttermin muss vor der Frist liegen.")
        task = ReadingTask(subject_id=_clean(subject_id, "Das Fach"), title=_clean(title, "Der Titel"),
                           unit=unit, total=total, passes=passes, start=start, deadline=deadline)
        self.repo.save(task)
        self._emit("reading.task_created", {"subject_id": task.subject_id, "task_id": task.id})
        return task

    def list_tasks(self, subject_id: str | None = None) -> list[ReadingTask]:
        tasks = self.repo.list(subject_id)
        return sorted(tasks, key=lambda t: (t.deadline is None, t.deadline or date.max, t.title.lower()))

    def get_task(self, task_id: str) -> ReadingTask:
        return self._task(task_id)

    def delete_task(self, task_id: str) -> None:
        task = self._task(task_id)
        self.repo.delete(task_id)
        self._emit("reading.task_deleted", {"subject_id": task.subject_id, "task_id": task.id})

    # Leseprotokoll
    def log_reading(self, task_id: str, amount: int, day: date | None = None, note: str = "") -> ReadingTask:
        task = self._task(task_id)
        day = day or self.today()
        if not isinstance(amount, int) or amount < 1:
            raise InvalidInput(f"Gib an, wie viel du gelesen hast (mindestens 1, in {task.unit}).")
        if day > self.today():
            raise InvalidInput("Das Datum liegt in der Zukunft.")
        task.entries.append(ReadingEntry(day=day, amount=amount, note=(note or "").strip()))
        self.repo.save(task)
        self._emit("reading.logged", {"subject_id": task.subject_id, "task_id": task.id,
                                      "amount": amount, "done": task.done, "target": task.target})
        return task

    def delete_entry(self, task_id: str, entry_id: str) -> ReadingTask:
        task = self._task(task_id)
        entry = task.get_entry(entry_id)
        if entry is None:
            raise NotFound("Eintrag nicht gefunden.")
        task.entries.remove(entry)
        self.repo.save(task)
        return task

    # Prognose
    def forecast_for(self, task: ReadingTask) -> Forecast:
        return forecast(task, self.today())

    # Fach-Hooks
    def discard_subject(self, subject_id: str) -> None:
        self.repo.delete_subject(subject_id)

    def subject_status(self, subject_id: str) -> dict:
        tasks = self.repo.list(subject_id)
        forecasts = [(t, self.forecast_for(t)) for t in tasks]
        # Jedes Pensum zählt gleich viel (Seiten und Kapitel lassen sich nicht addieren): Mittel der Prozentwerte.
        percent = round(sum(f.percent for _, f in forecasts) / len(forecasts), 1) if forecasts else 0.0
        open_tasks = [(t, f) for t, f in forecasts if f.status != "done"]
        urgent = min(open_tasks, key=lambda tf: (STATUS_ORDER.index(tf[1].status), tf[0].deadline or date.max), default=None)
        open_deadlines = [t.deadline for t, f in open_tasks if t.deadline]
        return {"task_count": len(tasks),
                "done_count": len(tasks) - len(open_tasks),
                "percent": percent,
                "progress": int(percent + 0.5) if forecasts else None,   # Gesamtfortschritt des Kerns (0 bis 100)
                "status": worst_status([f.status for _, f in forecasts]),
                "urgent_title": urgent[0].title if urgent else None,     # dringendstes offenes Pensum
                "next_deadline": min(open_deadlines).isoformat() if open_deadlines else None}
