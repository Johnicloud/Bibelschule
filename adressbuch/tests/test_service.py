import pytest
from app.application.ports import DozentRepository
from app.application.services import DozentService
from app.domain.errors import InvalidInput, NotFound


class InMemoryRepo(DozentRepository):
    def __init__(self): self.d = {}
    def list(self): return list(self.d.values())
    def get(self, i): return self.d.get(i)
    def save(self, dozent): self.d[dozent.id] = dozent
    def delete(self, i): self.d.pop(i, None)


@pytest.fixture
def svc():
    return DozentService(InMemoryRepo())


def test_add_dozent_requires_a_name(svc):
    with pytest.raises(InvalidInput):
        svc.add_dozent("  ")


def test_add_and_list_sorted_by_name(svc):
    svc.add_dozent("Viktor Löwen")
    svc.add_dozent("Andreas Neufeld", email="andreas.neufeld@eben-ezer.tel")
    assert [d.name for d in svc.list_dozenten()] == ["Andreas Neufeld", "Viktor Löwen"]


def test_update_and_delete(svc):
    d = svc.add_dozent("Sergi Panin", telefon="0123")
    updated = svc.update_dozent(d.id, "Sergi Panin", "sergi@example.com", "0456", "kennt Pneumatologie")
    assert updated.email == "sergi@example.com" and updated.telefon == "0456"
    svc.delete_dozent(d.id)
    assert svc.list_dozenten() == []
    with pytest.raises(NotFound):
        svc.delete_dozent(d.id)


def test_assign_and_unassign_subjects(svc):
    d = svc.add_dozent("Andreas Löwen")
    svc.assign(d.id, "fach-1")
    svc.assign(d.id, "fach-1")  # doppelt zuordnen ändert nichts
    svc.assign(d.id, "fach-2")
    assert sorted(svc._dozent(d.id).faecher) == ["fach-1", "fach-2"]
    assert [x.id for x in svc.for_subject("fach-1")] == [d.id]

    svc.unassign(d.id, "fach-1")
    assert svc._dozent(d.id).faecher == ["fach-2"]
    assert svc.for_subject("fach-1") == []


def test_discard_subject_removes_assignment_but_keeps_dozent(svc):
    d = svc.add_dozent("Viktor Razlaw")
    svc.assign(d.id, "fach-1")
    svc.assign(d.id, "fach-2")
    svc.discard_subject("fach-1")
    assert svc._dozent(d.id).faecher == ["fach-2"]
    assert svc.list_dozenten() == [svc._dozent(d.id)]  # Dozent bleibt erhalten


def test_subject_status_counts_assigned_dozenten(svc):
    d1, d2 = svc.add_dozent("Eins"), svc.add_dozent("Zwei")
    svc.assign(d1.id, "fach-1")
    assert svc.subject_status("fach-1") == {"count": 1}
    svc.assign(d2.id, "fach-1")
    assert svc.subject_status("fach-1") == {"count": 2}
