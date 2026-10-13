from datetime import timedelta

import pytest
from app.application.ports import VersRepository
from app.application.services import VersService
from app.domain.errors import InvalidInput, NotFound
from app.domain.models import utcnow


class InMemoryRepo(VersRepository):
    def __init__(self): self.d = {}
    def list(self): return list(self.d.values())
    def get(self, i): return self.d.get(i)
    def save(self, v): self.d[v.id] = v
    def delete(self, i): self.d.pop(i, None)
    def delete_subject(self, subject_id):
        for i in [v.id for v in self.d.values() if v.subject_id == subject_id]:
            self.d.pop(i, None)


@pytest.fixture
def svc():
    return VersService(InMemoryRepo())


def test_add_requires_referenz_and_text(svc):
    with pytest.raises(InvalidInput):
        svc.add_vers("", "Denn also hat Gott die Welt geliebt...")
    with pytest.raises(InvalidInput):
        svc.add_vers("Joh 3,16", "  ")


def test_new_vers_is_due_immediately(svc):
    v = svc.add_vers("Joh 3,16", "Denn also hat Gott die Welt geliebt...", subject_id="fach-1")
    assert v.box == 0 and v.is_due()


def test_review_correct_advances_box_and_pushes_due_date(svc):
    v = svc.add_vers("Joh 3,16", "Text", subject_id="fach-1")
    v = svc.review(v.id, True)
    assert v.box == 1 and v.due > utcnow() + timedelta(hours=1)


def test_review_wrong_resets_box_and_is_due_again(svc):
    v = svc.add_vers("Joh 3,16", "Text", subject_id="fach-1")
    v = svc.review(v.id, True)
    v = svc.review(v.id, False)
    assert v.box == 0 and v.is_due()
    with pytest.raises(NotFound):
        svc.review("gibt-es-nicht", True)


def test_list_verse_filters_by_subject_or_allgemein(svc):
    svc.add_vers("Joh 3,16", "a", subject_id="fach-1")
    svc.add_vers("Ps 23,1", "b", subject_id=None)
    svc.add_vers("Röm 8,28", "c", subject_id="fach-2")
    assert [v.referenz for v in svc.list_verse(subject_id="fach-1")] == ["Joh 3,16"]
    assert [v.referenz for v in svc.list_verse(allgemein=True)] == ["Ps 23,1"]
    assert len(svc.list_verse()) == 3


def test_due_verse_combines_fach_and_allgemein(svc):
    eigener = svc.add_vers("Joh 3,16", "a", subject_id="fach-1")
    allgemeiner = svc.add_vers("Ps 23,1", "b", subject_id=None)
    svc.add_vers("Röm 8,28", "c", subject_id="fach-2")  # anderes Fach: zählt hier nicht mit
    svc.review(eigener.id, True)  # nicht mehr fällig
    faellig = {v.id for v in svc.due_verse("fach-1")}
    assert faellig == {allgemeiner.id}


def test_discard_subject_removes_its_own_verse_but_not_allgemein(svc):
    svc.add_vers("Joh 3,16", "a", subject_id="fach-1")
    svc.add_vers("Ps 23,1", "b", subject_id=None)
    svc.discard_subject("fach-1")
    assert svc.list_verse(subject_id="fach-1") == []
    assert len(svc.list_verse(allgemein=True)) == 1


def test_update_vers_changes_referenz_text_and_zuordnung(svc):
    v = svc.add_vers("Joh 3,16", "alter Text", subject_id="fach-1")
    updated = svc.update_vers(v.id, "Joh 3,17", "neuer Text", subject_id=None)
    assert updated.referenz == "Joh 3,17" and updated.text == "neuer Text" and updated.subject_id is None
    assert updated.box == 0   # Bearbeiten ändert nichts am Lernfortschritt


def test_update_vers_keeps_box_and_due(svc):
    v = svc.add_vers("Joh 3,16", "Text", subject_id="fach-1")
    v = svc.review(v.id, True)
    updated = svc.update_vers(v.id, "Joh 3,16", "korrigierter Text")
    assert updated.box == 1 and updated.due == v.due


def test_update_vers_requires_referenz_and_text(svc):
    v = svc.add_vers("Joh 3,16", "Text")
    with pytest.raises(InvalidInput):
        svc.update_vers(v.id, " ", "Text")
    with pytest.raises(NotFound):
        svc.update_vers("gibt-es-nicht", "Joh 3,16", "Text")


def test_subject_status_counts_and_progress(svc):
    assert svc.subject_status("fach-1") == {"count": 0, "faellig": 0, "progress": None}
    v1 = svc.add_vers("Joh 3,16", "a", subject_id="fach-1")
    svc.add_vers("Röm 8,28", "b", subject_id="fach-1")
    for _ in range(4):
        v1 = svc.review(v1.id, True)
    status = svc.subject_status("fach-1")
    assert status["count"] == 2 and status["progress"] == 50  # 1 von 2 auf Stufe 4+
