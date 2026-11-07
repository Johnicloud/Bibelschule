import json

from app.adapters.outbound.json_repository import JsonRegisterRepository
from app.application.services import RegisterService

OLD = [  # so sah register.json aus, als es nur Namen und Orte gab
    {"id": "e1", "subject_id": "f", "kind": "person", "name": "Abraham",
     "refs": [{"book": 0, "chapter": 12, "verse": 1, "chapter_end": None, "verse_end": None}]},
    {"id": "e2", "subject_id": "f", "kind": "place", "name": "Ur", "refs": []},
]


def test_old_data_file_is_taken_over_without_loss(tmp_path):
    path = tmp_path / "register.json"
    path.write_text(json.dumps(OLD), "utf-8")
    svc = RegisterService(JsonRegisterRepository(path))
    assert svc.migrate_legacy() == 2

    fresh = RegisterService(JsonRegisterRepository(path))              # neu laden: alles ist da und zugeordnet
    assert {r.name: n for r, n in fresh.list_registers("f")} == {"Namen": 1, "Orte": 1}
    assert [e.name for e in fresh.list_entries("f")] == ["Abraham", "Ur"]
    assert fresh.migrate_legacy() == 0
    saved = json.loads(path.read_text("utf-8"))
    assert all(e["register_id"] for e in saved) and {e["kind"] for e in saved} == {"person", "place"}


def test_delete_register_removes_its_entries_on_disk(tmp_path):
    svc = RegisterService(JsonRegisterRepository(tmp_path / "register.json"))
    a, b = svc.create_register("f", "A"), svc.create_register("f", "B")
    svc.add_entry(a.id, "Eins", ["Apg 1"])
    svc.add_entry(b.id, "Zwei", ["Apg 2"])
    svc.delete_register(a.id)
    again = RegisterService(JsonRegisterRepository(tmp_path / "register.json"))
    assert [(r.name, n) for r, n in again.list_registers("f")] == [("B", 1)]


def test_coordinates_survive_reload(tmp_path):
    path = tmp_path / "register.json"
    svc = RegisterService(JsonRegisterRepository(path))
    orte = svc.create_register("f", "Orte")
    e = svc.add_entry(orte.id, "Ur", ["1Mo 11,28"], lat=30.9608, lon=46.1025)

    again = RegisterService(JsonRegisterRepository(path))
    reloaded = again.repo.get(e.id)
    assert (reloaded.lat, reloaded.lon) == (30.9608, 46.1025)
