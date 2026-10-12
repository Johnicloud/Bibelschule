from datetime import date

from app.domain.forecast import forecast, worst_status
from app.domain.models import ReadingEntry, ReadingTask

TODAY = date(2026, 10, 12)


def task(total=100, passes=1, deadline=None, entries=()):
    return ReadingTask(subject_id="f", title="Buch", unit="Seiten", total=total, passes=passes,
                       deadline=deadline, entries=[ReadingEntry(day=d, amount=a) for d, a in entries])


def test_not_started_shows_needed_pace():
    f = forecast(task(deadline=date(2026, 10, 22)), TODAY)
    assert f.status == "not_started" and f.needed_per_day == 10 and f.projected_finish is None


def test_on_track_with_projection():
    # 40 Seiten in 4 Tagen = 10/Tag, Rest 60 -> 6 Tage -> 18.10., Frist 25.10.
    entries = [(date(2026, 10, 9), 10), (date(2026, 10, 10), 10), (date(2026, 10, 11), 10), (TODAY, 10)]
    f = forecast(task(deadline=date(2026, 10, 25), entries=entries), TODAY)
    assert f.pace_per_day == 10 and f.projected_finish == date(2026, 10, 18)
    assert f.status == "on_track"


def test_tight_when_pace_barely_enough():
    entries = [(TODAY, 10)]  # 10/Tag, Rest 90 -> 9 Tage; Frist in 9 Tagen, Bedarf 10/Tag
    f = forecast(task(deadline=date(2026, 10, 21), entries=entries), TODAY)
    assert f.projected_finish == date(2026, 10, 21) and f.status == "tight"


def test_behind_when_pace_too_slow():
    f = forecast(task(deadline=date(2026, 10, 20), entries=[(TODAY, 5)]), TODAY)
    assert f.status == "behind"


def test_old_entries_give_zero_pace_and_behind():
    f = forecast(task(deadline=date(2026, 12, 1), entries=[(date(2026, 8, 1), 5)]), TODAY)
    assert f.pace_per_day == 0 and f.projected_finish is None and f.status == "behind"


def test_overdue_done_and_open():
    assert forecast(task(deadline=date(2026, 10, 1), entries=[(TODAY, 5)]), TODAY).status == "overdue"
    assert forecast(task(entries=[(TODAY, 100)]), TODAY).status == "done"
    assert forecast(task(entries=[(TODAY, 5)]), TODAY).status == "open"


def test_deadline_today_needs_everything_today():
    f = forecast(task(deadline=TODAY, entries=[(TODAY, 10)]), TODAY)
    assert f.needed_per_day == 90 and f.status == "behind"


def test_passes_multiply_target():
    f = forecast(task(total=50, passes=2, entries=[(TODAY, 25)]), TODAY)
    assert f.target == 100 and f.percent == 25


def test_worst_status():
    assert worst_status(["done", "tight", "on_track"]) == "tight"
    assert worst_status([]) is None
