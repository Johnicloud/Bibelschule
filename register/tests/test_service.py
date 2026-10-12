import pytest
from app.application.ports import EventPublisher, RegisterRepository
from app.application.services import RegisterService
from app.domain.errors import InvalidInput, NotFound


class InMemoryRepo(RegisterRepository):
    def __init__(self): self.d = {}
    def list(self, subject_id=None): return [e for e in self.d.values() if subject_id in (None, e.subject_id)]
    def get(self, i): return self.d.get(i)
    def save(self, e): self.d[e.id] = e
    def delete(self, i): self.d.pop(i, None)
    def delete_subject(self, s): self.d = {i: e for i, e in self.d.items() if e.subject_id != s}


class FakeEvents(EventPublisher):
    def __init__(self): self.sent = []
    def publish(self, event, payload): self.sent.append(event)


@pytest.fixture
def events():
    return FakeEvents()


@pytest.fixture
def svc(events):
    return RegisterService(InMemoryRepo(), events)


def texts(entry):
    return [r.format() for r in entry.refs]


def test_add_entry_sorts_refs_in_bible_order(svc):
    e = svc.add_entry("f", "person", "Abraham", ["Hebr 11,8", "1Mo 12,1-3; 1. Mose 22"])
    assert texts(e) == ["1Mo 12,1-3", "1Mo 22", "Hebr 11,8"]


def test_same_name_merges_without_duplicates(svc, events):
    svc.add_entry("f", "person", "Abraham", ["1Mo 12,1"])
    e = svc.add_entry("f", "person", " abraham ", ["1Mo 12,1", "1Mo 15,6"], note="Vater des Glaubens")
    assert texts(e) == ["1Mo 12,1", "1Mo 15,6"] and e.name == "Abraham" and e.note == "Vater des Glaubens"
    assert len(svc.list_entries("f")) == 1
    assert events.sent == ["register.entry_added", "register.entry_updated"]


def test_person_and_place_with_same_name_stay_separate(svc):
    svc.add_entry("f", "person", "Silo", ["Ri 21,19"])
    svc.add_entry("f", "place", "Silo", ["Jos 18,1"])
    assert len(svc.list_entries("f")) == 2


def test_bad_ref_saves_nothing(svc):
    with pytest.raises(InvalidInput):
        svc.add_entry("f", "person", "Mose", ["2Mo 3,1", "Quatsch 4"])
    assert svc.list_entries() == []
    with pytest.raises(InvalidInput):
        svc.add_entry("f", "person", "Mose", [])
    with pytest.raises(InvalidInput):
        svc.add_entry("f", "tier", "Löwe", ["Dan 6"])
    with pytest.raises(InvalidInput):
        svc.add_entry("f", "person", " ", ["Dan 6"])


def test_sorted_by_name_and_by_bible_order(svc):
    svc.add_entry("f", "place", "Ägypten", ["2Mo 1,1"])
    svc.add_entry("f", "person", "Zacharias", ["Lk 1,5"])
    svc.add_entry("f", "person", "Abraham", ["1Mo 12,1"])
    svc.add_entry("f", "place", "Bethlehem", ["Mi 5,1", "Mt 2,1"])
    assert [e.name for e in svc.list_entries("f")] == ["Abraham", "Ägypten", "Bethlehem", "Zacharias"]
    assert [e.name for e in svc.list_entries("f", sort="bibel")] == ["Abraham", "Ägypten", "Bethlehem", "Zacharias"]
    assert [e.name for e in svc.list_entries("f", kind="place", sort="name")] == ["Ägypten", "Bethlehem"]
    with pytest.raises(InvalidInput):
        svc.list_entries(sort="farbe")


def test_by_passage_groups_names_per_verse(svc):
    svc.add_entry("f", "person", "Abraham", ["1Mo 12,1", "Joh 8,56"])
    svc.add_entry("f", "place", "Haran", ["1Mo 12,4", "1Mo 12,1"])
    result = svc.by_passage("f")
    assert [(r.format(), [e.name for e in es]) for r, es in result] == [
        ("1Mo 12,1", ["Abraham", "Haran"]), ("1Mo 12,4", ["Haran"]), ("Joh 8,56", ["Abraham"])]


def test_delete_status_and_subject_hooks(svc):
    a = svc.add_entry("f", "person", "Abraham", ["1Mo 12,1", "1Mo 15,6"])
    svc.add_entry("f", "place", "Ur", ["1Mo 11,28"])
    svc.add_entry("anderes", "person", "Paulus", ["Apg 9"])
    assert svc.subject_status("f") == {"persons": 1, "places": 1, "refs": 3}
    svc.delete_entry(a.id)
    with pytest.raises(NotFound):
        svc.delete_entry(a.id)
    svc.discard_subject("f")
    assert [e.name for e in svc.list_entries()] == ["Paulus"]
