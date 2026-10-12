"""Prognose: reine Rechnung aus Pensum, Protokoll und Datum. Kein Zugriff auf Uhr oder Speicher."""
from dataclasses import dataclass
from datetime import date, timedelta
from math import ceil

from app.domain.models import ReadingTask

WINDOW_DAYS = 14        # so weit zurück zählt das Lesetempo
TIGHT_FACTOR = 1.15     # Tempo unter 115 % des Bedarfs gilt als knapp

# Reihenfolge von schlimm nach gut (für die Gesamtanzeige eines Fachs)
STATUS_ORDER = ["overdue", "behind", "tight", "not_started", "open", "on_track", "done"]


@dataclass(frozen=True)
class Forecast:
    target: int
    done: int
    remaining: int
    percent: float
    days_left: int | None            # bis zur Frist (negativ = überschritten)
    needed_per_day: float | None     # so viel muss ab morgen täglich gelesen werden
    pace_per_day: float | None       # so viel wird zurzeit täglich gelesen
    projected_finish: date | None    # voraussichtlich fertig am (bei gleichbleibendem Tempo, ab morgen)
    status: str                      # done | overdue | not_started | open | behind | tight | on_track


def pace_per_day(task: ReadingTask, today: date) -> float | None:
    """Durchschnitt der letzten 14 Tage; in den ersten Tagen nur über die Tage seit dem ersten Eintrag."""
    if not task.entries:
        return None
    first = min(e.day for e in task.entries)
    span = max(1, min(WINDOW_DAYS, (today - first).days + 1))
    start = today - timedelta(days=span - 1)
    read = sum(e.amount for e in task.entries if start <= e.day <= today)
    return read / span


def forecast(task: ReadingTask, today: date) -> Forecast:
    target, done = task.target, task.done
    remaining = max(target - done, 0)
    percent = min(100.0, done / target * 100) if target else 100.0
    days_left = (task.deadline - today).days if task.deadline else None
    pace = pace_per_day(task, today)

    needed = None
    if days_left is not None and remaining:
        if days_left > 0:
            needed = remaining / days_left
        elif days_left == 0:
            needed = float(remaining)

    projected = None
    if remaining and pace:
        projected = today + timedelta(days=ceil(remaining / pace))

    if remaining == 0:
        status = "done"
    elif days_left is not None and days_left < 0:
        status = "overdue"
    elif not task.entries:
        status = "not_started"
    elif task.deadline is None:
        status = "open"
    elif projected is None or projected > task.deadline:
        status = "behind"
    elif needed is not None and pace < needed * TIGHT_FACTOR:
        status = "tight"
    else:
        status = "on_track"

    return Forecast(target, done, remaining, percent, days_left, needed, pace, projected, status)


def worst_status(statuses: list[str]) -> str | None:
    return min(statuses, key=STATUS_ORDER.index) if statuses else None
