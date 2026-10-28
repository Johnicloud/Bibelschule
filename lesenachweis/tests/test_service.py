from datetime import date

import pytest
from app.application.ports import EventPublisher, ReadingRepository
from app.application.services import ReadingService
from app.domain.errors import InvalidInput, NotFound

TODAY = date(2026, 10, 12)


class InMemoryRepo(ReadingRepository):
    def __init__(self): self.d = {}
    def list(self, subject_id=None): return [t for t in self.d.values() if subject_id in (None, t.subject_id)]
    def get(self, i): return self.d.get(i)
    def save(self, t): self.d[t.id] = t
    def delete(self, i): self.d.pop(i, None)
    def delete_subject(self, s): self.d = {i: t for i, t in self.d.items() if t.subject_id != s}


class FakeEvents(EventPublisher):
    def __init__(self): self.sent = []
    def publish(self, event, payload): self.sent.append(event)


@pytest.fixture
def events():
    return FakeEvents()


@pytest.fixture
def svc(events):
    return ReadingService(InMemoryRepo(), events, today=lambda: TODAY)


def test_add_task_validates(svc):
    with pytest.raises(InvalidInput):
        svc.add_task("f", " ", "Seiten", 10)
    with pytest.raises(InvalidInput):
        svc.add_task("f", "Buch", "Minuten", 10)
    with pytest.raises(InvalidInput):
        svc.add_task("f", "Buch", "Seiten", 0)
    with pytest.raises(InvalidInput):
        svc.add_task("f", "Buch", "Seiten", 10, passes=0)


def test_log_reading_and_forecast(svc, events):
    t = svc.add_task("f", "Dogmatik", "Seiten", 200, deadline=date(2026, 11, 12))
    svc.log_reading(t.id, 20)
    svc.log_reading(t.id, 10, day=date(2026, 10, 11), note=" Kapitel 1 ")
    t = svc.get_task(t.id)
    assert t.done == 30 and t.entries[1].note == "Kapitel 1"
    assert svc.forecast_for(t).remaining == 170
    assert events.sent == ["reading.task_created", "reading.logged", "reading.logged"]


def test_log_rejects_bad_input(svc):
    t = svc.add_task("f", "Buch", "Kapitel", 10)
    with pytest.raises(InvalidInput):
        svc.log_reading(t.id, 0)
    with pytest.raises(InvalidInput):
        svc.log_reading(t.id, 1, day=date(2026, 10, 13))
    with pytest.raises(NotFound):
        svc.log_reading("gibt-es-nicht", 1)


def test_delete_entry_and_task(svc):
    t = svc.add_task("f", "Buch", "Seiten", 10)
    entry = svc.log_reading(t.id, 3).entries[0]
    assert svc.delete_entry(t.id, entry.id).done == 0
    with pytest.raises(NotFound):
        svc.delete_entry(t.id, entry.id)
    svc.delete_task(t.id)
    assert svc.list_tasks() == []


def test_add_task_with_buecher_sums_their_pages_as_total(svc):
    t = svc.add_task("f", "Pflicht-Lektüre", "Seiten", total=None, buecher=[
        {"title": "Die Apostelgeschichte", "total": 200},
        {"title": "Wuppertaler Studienbibel", "total": 250},
        {"title": "Edition C", "total": 150},
    ])
    assert t.total == 600 and [b.title for b in t.buecher] == \
        ["Die Apostelgeschichte", "Wuppertaler Studienbibel", "Edition C"]
    assert svc.forecast_for(t).target == 600


def test_add_task_rejects_empty_buch_title_or_bad_total(svc):
    with pytest.raises(InvalidInput):
        svc.add_task("f", "Lektüre", "Seiten", None, buecher=[{"title": " ", "total": 100}])
    with pytest.raises(InvalidInput):
        svc.add_task("f", "Lektüre", "Seiten", None, buecher=[{"title": "Buch", "total": 0}])
    with pytest.raises(InvalidInput):
        svc.add_task("f", "Lektüre", "Seiten", None, buecher=[])


def test_update_task_changes_fields_without_touching_entries(svc):
    t = svc.add_task("f", "Buch", "Seiten", 100, deadline=date(2026, 11, 1))
    svc.log_reading(t.id, 10)
    updated = svc.update_task(t.id, "Neuer Titel", "Kapitel", 50, passes=2, deadline=date(2026, 12, 1))
    assert updated.title == "Neuer Titel" and updated.unit == "Kapitel" and updated.total == 50
    assert updated.passes == 2 and updated.deadline == date(2026, 12, 1) and updated.done == 10
    with pytest.raises(InvalidInput):
        svc.update_task(t.id, " ", "Seiten", 10)
    with pytest.raises(NotFound):
        svc.update_task("gibt-es-nicht", "Buch", "Seiten", 10)


def test_update_task_can_switch_to_buecher(svc):
    t = svc.add_task("f", "Lektüre", "Seiten", 100)
    updated = svc.update_task(t.id, "Lektüre", "Seiten", None, buecher=[
        {"title": "Buch A", "total": 60}, {"title": "Buch B", "total": 40},
    ])
    assert updated.total == 100 and [b.title for b in updated.buecher] == ["Buch A", "Buch B"]


def test_log_reading_can_reference_a_buch(svc):
    t = svc.add_task("f", "Lektüre", "Seiten", None, buecher=[
        {"title": "Buch A", "total": 60}, {"title": "Buch B", "total": 40},
    ])
    buch_a, buch_b = t.buecher
    svc.log_reading(t.id, 20, buch_id=buch_a.id)
    svc.log_reading(t.id, 10, buch_id=buch_a.id)
    svc.log_reading(t.id, 15, buch_id=buch_b.id)
    t = svc.get_task(t.id)
    assert t.buch_done(buch_a.id) == 30 and t.buch_done(buch_b.id) == 15
    assert t.done == 45
    with pytest.raises(InvalidInput):
        svc.log_reading(t.id, 5, buch_id="gibt-es-nicht")


def test_log_reading_tracks_each_durchlauf_separately(svc):
    """Mehrere Durchgänge: im ersten Durchgang auf Seite 5 stehen, gleichzeitig im zweiten auf Seite 7 –
    jeder Durchgang hat seinen eigenen Stand (wie bei Büchern), nicht nur eine gemeinsame Summe."""
    t = svc.add_task("f", "Apostelgeschichte", "Seiten", 10, passes=3)
    svc.log_reading(t.id, 5, durchlauf=1)
    svc.log_reading(t.id, 7, durchlauf=2)
    t = svc.get_task(t.id)
    assert t.durchlauf_done(1) == 5 and t.durchlauf_done(2) == 7 and t.durchlauf_done(3) == 0
    assert t.done == 12   # Gesamtfortschritt bleibt die Summe über alle Durchgänge

    with pytest.raises(InvalidInput):
        svc.log_reading(t.id, 1, durchlauf=0)
    with pytest.raises(InvalidInput):
        svc.log_reading(t.id, 1, durchlauf=4)   # nur 3 Durchgänge vereinbart


def test_log_reading_without_durchlauf_defaults_to_the_first(svc):
    t = svc.add_task("f", "Buch", "Seiten", 10, passes=2)
    svc.log_reading(t.id, 3)
    t = svc.get_task(t.id)
    assert t.durchlauf_done(1) == 3 and t.entries[0].durchlauf == 1


def test_aktiver_durchlauf_is_the_first_unfinished_one(svc):
    t = svc.add_task("f", "Buch", "Seiten", 10, passes=3)
    assert t.aktiver_durchlauf() == 1
    svc.log_reading(t.id, 10, durchlauf=1)   # Durchgang 1 fertig
    t = svc.get_task(t.id)
    assert t.aktiver_durchlauf() == 2
    svc.log_reading(t.id, 10, durchlauf=2)
    svc.log_reading(t.id, 10, durchlauf=3)   # alle fertig
    t = svc.get_task(t.id)
    assert t.aktiver_durchlauf() == 3   # bleibt beim letzten, kein Durchgang 4


def test_tasks_sorted_by_deadline(svc):
    svc.add_task("f", "Später", "Seiten", 10, deadline=date(2026, 12, 1))
    svc.add_task("f", "Ohne", "Seiten", 10)
    svc.add_task("f", "Bald", "Seiten", 10, deadline=date(2026, 10, 20))
    assert [t.title for t in svc.list_tasks("f")] == ["Bald", "Später", "Ohne"]


def test_subject_status_and_hooks(svc):
    a = svc.add_task("f", "A", "Seiten", 100, deadline=date(2026, 10, 20))
    svc.add_task("f", "B", "Seiten", 100)
    svc.add_task("anderes", "C", "Seiten", 10)
    svc.log_reading(a.id, 50)
    s = svc.subject_status("f")
    assert s["task_count"] == 2 and s["percent"] == 25.0
    assert s["status"] == "not_started" and s["next_deadline"] == "2026-10-20"
    assert s["done_count"] == 0 and s["progress"] == 25 and s["urgent_title"] == "B"
    assert svc.subject_status("leer") == {"task_count": 0, "done_count": 0, "percent": 0.0, "progress": None,
                                          "status": None, "urgent_title": None, "next_deadline": None, "pensen": []}
    svc.discard_subject("f")
    assert [t.title for t in svc.list_tasks()] == ["C"]


def test_subject_progress_counts_every_task_equally(svc):
    gross = svc.add_task("g", "Dickes Buch", "Seiten", 600)
    klein = svc.add_task("g", "Apostelgeschichte", "Kapitel", 28, passes=4)
    svc.log_reading(gross.id, 600)                       # 100 %
    svc.log_reading(klein.id, 28)                        # 25 % von 4 Durchgängen
    s = svc.subject_status("g")
    assert s["percent"] == 62.5 and s["progress"] == 63 and s["done_count"] == 1
    assert s["urgent_title"] == "Apostelgeschichte"


def test_status_nennt_den_stand_jedes_pensums_fuer_verknuepfte_aufgaben(svc):
    a = svc.add_task("f", "Pflichtlektüre", "Seiten", 200)
    b = svc.add_task("f", "Apostelgeschichte", "Kapitel", 28, passes=2)
    svc.log_reading(a.id, 50)
    svc.log_reading(b.id, 28)
    pensen = {p["id"]: p["percent"] for p in svc.subject_status("f")["pensen"]}
    assert pensen == {a.id: 25, b.id: 50}                       # ganze Prozent, 28 von 56 Kapiteln
