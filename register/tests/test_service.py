import pytest
from app.application.ports import EventPublisher, RegisterRepository
from app.application.services import RegisterService
from app.domain.errors import InvalidInput, NotFound


class InMemoryRepo(RegisterRepository):
    def __init__(self): self.d, self.r = {}, {}
    def list(self, subject_id=None): return [e for e in self.d.values() if subject_id in (None, e.subject_id)]
    def get(self, i): return self.d.get(i)
    def save(self, e): self.d[e.id] = e
    def delete(self, i): self.d.pop(i, None)
    def list_registers(self, subject_id=None): return [r for r in self.r.values() if subject_id in (None, r.subject_id)]
    def get_register(self, i): return self.r.get(i)
    def save_register(self, r): self.r[r.id] = r
    def delete_register(self, i):
        self.d = {k: e for k, e in self.d.items() if e.register_id != i}
        self.r.pop(i, None)
    def delete_subject(self, s):
        self.d = {i: e for i, e in self.d.items() if e.subject_id != s}
        self.r = {i: r for i, r in self.r.items() if r.subject_id != s}


class FakeEvents(EventPublisher):
    def __init__(self): self.sent = []
    def publish(self, event, payload): self.sent.append(event)


@pytest.fixture
def events():
    return FakeEvents()


@pytest.fixture
def svc(events):
    return RegisterService(InMemoryRepo(), events)


@pytest.fixture
def namen(svc):
    return svc.create_register("f", "Namen")


@pytest.fixture
def orte(svc):
    return svc.create_register("f", "Orte")


def texts(entry):
    return [r.format() for r in entry.refs]


def test_any_number_of_registers_in_order_with_counts(svc, namen, orte):
    svc.create_register("f", "Völker")
    svc.create_register("anderes", "Namen")
    svc.add_entry(namen.id, "Abraham", ["1Mo 12,1"])
    assert [(r.name, n) for r, n in svc.list_registers("f")] == [("Namen", 1), ("Orte", 0), ("Völker", 0)]


def test_register_names_are_unique_per_subject(svc, namen, events):
    with pytest.raises(InvalidInput):
        svc.create_register("f", " namen ")
    with pytest.raises(InvalidInput):
        svc.create_register("f", " ")
    svc.create_register("anderes", "Namen")           # in einem anderen Fach erlaubt
    assert events.sent.count("register.created") == 2


def test_rename_and_delete_register_with_entries(svc, namen, orte):
    svc.add_entry(namen.id, "Abraham", ["1Mo 12,1"])
    svc.add_entry(orte.id, "Ur", ["1Mo 11,28"])
    assert svc.rename_register(namen.id, "Personen").name == "Personen"
    with pytest.raises(InvalidInput):
        svc.rename_register(namen.id, "Orte")
    svc.delete_register(namen.id)
    assert [e.name for e in svc.list_entries("f")] == ["Ur"]
    with pytest.raises(NotFound):
        svc.delete_register(namen.id)


def test_add_entry_sorts_refs_in_bible_order(svc, namen):
    e = svc.add_entry(namen.id, "Abraham", ["Hebr 11,8", "1Mo 12,1-3; 1. Mose 22"])
    assert texts(e) == ["1Mo 12,1-3", "1Mo 22", "Hebr 11,8"]


def test_same_name_merges_within_a_register_only(svc, namen, orte, events):
    svc.add_entry(namen.id, "Abraham", ["1Mo 12,1"])
    e = svc.add_entry(namen.id, "Abraham", ["1Mo 12,1", "1Mo 15,6"])   # gleicher Name (Groß/Klein egal)
    svc.add_entry(namen.id, " abraham ", ["Joh 8,56"])
    assert texts(svc.list_entries(register_id=namen.id)[0]) == ["1Mo 12,1", "1Mo 15,6", "Joh 8,56"] and e.name == "Abraham"
    svc.add_entry(orte.id, "Silo", ["Jos 18,1"])
    svc.add_entry(namen.id, "Silo", ["Ri 21,19"])                       # gleicher Name in anderem Register bleibt getrennt
    assert len(svc.list_entries("f")) == 3
    assert events.sent.count("register.entry_added") == 3


def test_bad_input_saves_nothing(svc, namen):
    with pytest.raises(InvalidInput):
        svc.add_entry(namen.id, "Mose", ["2Mo 3,1", "Quatsch 4"])
    assert svc.list_entries() == []
    with pytest.raises(InvalidInput):
        svc.add_entry(namen.id, "Mose", [])
    with pytest.raises(InvalidInput):
        svc.add_entry(namen.id, " ", ["Dan 6"])
    with pytest.raises(NotFound):
        svc.add_entry("gibt-es-nicht", "Mose", ["2Mo 3,1"])


def test_sorted_by_name_and_by_bible_order(svc, namen, orte):
    svc.add_entry(orte.id, "Ägypten", ["2Mo 1,1"])
    svc.add_entry(namen.id, "Zacharias", ["Lk 1,5"])
    svc.add_entry(namen.id, "Abraham", ["1Mo 12,1"])
    svc.add_entry(orte.id, "Bethlehem", ["Mi 5,1", "Mt 2,1"])
    assert [e.name for e in svc.list_entries("f")] == ["Abraham", "Ägypten", "Bethlehem", "Zacharias"]
    assert [e.name for e in svc.list_entries("f", sort="bibel")] == ["Abraham", "Ägypten", "Bethlehem", "Zacharias"]
    assert [e.name for e in svc.list_entries(register_id=orte.id)] == ["Ägypten", "Bethlehem"]
    with pytest.raises(InvalidInput):
        svc.list_entries(sort="farbe")


def test_by_passage_groups_entries_per_verse(svc, namen, orte):
    svc.add_entry(namen.id, "Abraham", ["1Mo 12,1", "Joh 8,56"])
    svc.add_entry(orte.id, "Haran", ["1Mo 12,4", "1Mo 12,1"])
    result = svc.by_passage("f")
    assert [(r.format(), [e.name for e in es]) for r, es in result] == [
        ("1Mo 12,1", ["Abraham", "Haran"]), ("1Mo 12,4", ["Haran"]), ("Joh 8,56", ["Abraham"])]
    assert [r.format() for r, _ in svc.by_passage(register_id=orte.id)] == ["1Mo 12,1", "1Mo 12,4"]


def test_delete_status_and_subject_hooks(svc, namen, orte):
    a = svc.add_entry(namen.id, "Abraham", ["1Mo 12,1", "1Mo 15,6"])
    svc.add_entry(orte.id, "Ur", ["1Mo 11,28"])
    paulus = svc.create_register("anderes", "Namen")
    svc.add_entry(paulus.id, "Paulus", ["Apg 9"])
    assert svc.subject_status("f") == {"registers": 2, "entries": 2, "refs": 3}
    assert svc.subject_status("leer") == {"registers": 0, "entries": 0, "refs": 0}
    svc.delete_entry(a.id)
    with pytest.raises(NotFound):
        svc.delete_entry(a.id)
    svc.discard_subject("f")
    assert [e.name for e in svc.list_entries()] == ["Paulus"] and svc.list_registers("f") == []


def test_entry_coordinates_are_optional_and_preserved_when_merging(svc, orte):
    e = svc.add_entry(orte.id, "Ur", ["1Mo 11,28"])
    assert (e.lat, e.lon) == (None, None)

    e = svc.add_entry(orte.id, "Ur", ["1Mo 15,7"], lat=30.9608, lon=46.1025)   # Stellen dazu + Koordinaten gesetzt
    assert (e.lat, e.lon) == (30.9608, 46.1025)

    e = svc.add_entry(orte.id, "Ur", ["Neh 9,7"])   # ohne Angabe bleiben vorhandene Koordinaten unangetastet
    assert (e.lat, e.lon) == (30.9608, 46.1025)


def test_entry_coordinates_must_come_together_and_in_range(svc, orte):
    with pytest.raises(InvalidInput):
        svc.add_entry(orte.id, "Ur", ["1Mo 11,28"], lat=30.9608)
    with pytest.raises(InvalidInput):
        svc.add_entry(orte.id, "Ur", ["1Mo 11,28"], lat=300, lon=46.1025)


def test_set_location_updates_or_clears_without_touching_refs(svc, orte):
    e = svc.add_entry(orte.id, "Ur", ["1Mo 11,28"])
    svc.set_location(e.id, 30.9608, 46.1025)
    assert texts(svc.repo.get(e.id)) == ["1Mo 11,28"]
    assert (svc.repo.get(e.id).lat, svc.repo.get(e.id).lon) == (30.9608, 46.1025)

    svc.set_location(e.id, None, None)
    assert (svc.repo.get(e.id).lat, svc.repo.get(e.id).lon) == (None, None)

    with pytest.raises(NotFound):
        svc.set_location("gibt-es-nicht", 1, 1)


def test_migrate_legacy_moves_old_names_and_places_into_registers(svc):
    from app.domain.models import RegisterEntry
    for kind, name in [("person", "Abraham"), ("place", "Ur"), ("person", "Sara"), ("", "Rätsel")]:
        svc.repo.save(RegisterEntry(subject_id="f", register_id="", name=name, legacy_kind=kind))
    assert svc.migrate_legacy() == 4
    assert svc.migrate_legacy() == 0                                   # zweites Mal tut nichts
    regs = {r.name: n for r, n in svc.list_registers("f")}
    assert regs == {"Namen": 3, "Orte": 1}
