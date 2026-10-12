import pytest
from app.application.ports import ServiceGateway, SubjectRepository
from app.application.services import SubjectService
from app.domain.errors import InvalidInput, NotFound


class InMemoryRepo(SubjectRepository):
    def __init__(self): self.d = {}
    def list(self): return list(self.d.values())
    def get(self, i): return self.d.get(i)
    def save(self, s): self.d[s.id] = s
    def delete(self, i): self.d.pop(i, None)


class FakeGateway(ServiceGateway):
    """Zwei Dienste im Speicher; 'down' simuliert einen ausgefallenen Dienst."""
    def __init__(self, names=("karteikarten", "register")):
        self._names, self.down, self.known, self.deleted = list(names), set(), {n: {} for n in names}, []

    def names(self): return self._names
    def online(self, s): return s not in self.down

    def put_subject(self, s, i, name):
        if s in self.down: return False
        self.known[s][i] = name
        return True

    def delete_subject(self, s, i):
        if s in self.down: return False
        self.known[s].pop(i, None)
        self.deleted.append((s, i))
        return True

    def status(self, s, i): return {"n": len(self.known[s])} if i in self.known[s] else {"n": 0}
    def forward(self, service, method, path, query, body, content_type): return 200, b"{}", "application/json"


@pytest.fixture
def gw():
    return FakeGateway()


@pytest.fixture
def svc(gw):
    return SubjectService(InMemoryRepo(), gw)


def test_create_subject_reaches_all_services(svc, gw):
    subject, synced = svc.create_subject("  Dogmatik ")
    assert subject.name == "Dogmatik" and synced == {"karteikarten": True, "register": True}
    assert all(known[subject.id] == "Dogmatik" for known in gw.known.values())


def test_names_must_be_unique_and_not_empty(svc):
    svc.create_subject("Dogmatik")
    with pytest.raises(InvalidInput):
        svc.create_subject("dogmatik")
    with pytest.raises(InvalidInput):
        svc.create_subject("  ")


def test_rename_and_delete(svc, gw):
    subject, _ = svc.create_subject("Dogmatik")
    other, _ = svc.create_subject("Ethik")
    with pytest.raises(InvalidInput):
        svc.rename_subject(other.id, "Dogmatik")
    renamed, _ = svc.rename_subject(subject.id, "Dogmatik I")
    assert gw.known["register"][subject.id] == "Dogmatik I"
    assert svc.delete_subject(subject.id) == {"karteikarten": True, "register": True}
    assert [s.name for s in svc.list_subjects()] == ["Ethik"]
    with pytest.raises(NotFound):
        svc.delete_subject(subject.id)


def test_subject_is_kept_when_a_service_is_down_and_sync_repairs_it(svc, gw):
    gw.down.add("register")
    subject, synced = svc.create_subject("Dogmatik")
    assert synced == {"karteikarten": True, "register": False}
    assert svc.sync() == {"karteikarten": True, "register": False}
    gw.down.clear()
    assert svc.sync() == {"karteikarten": True, "register": True}
    assert gw.known["register"][subject.id] == "Dogmatik"


def test_overview_skips_offline_services(svc, gw):
    subject, _ = svc.create_subject("Dogmatik")
    gw.down.add("register")
    o = svc.overview()
    assert o["services"] == [{"name": "karteikarten", "online": True}, {"name": "register", "online": False}]
    assert o["subjects"] == [{"id": subject.id, "name": "Dogmatik",
                              "status": {"karteikarten": {"n": 1}, "register": None}}]


def test_forward_only_known_services(svc):
    assert svc.forward("register", "GET", "entries", "", b"", None)[0] == 200
    with pytest.raises(NotFound):
        svc.forward("gibtesnicht", "GET", "x", "", b"", None)


def test_subjects_sorted_by_name(svc):
    for n in ("Zeitgeschichte", "ägyptisch", "Bibelkunde"):
        svc.create_subject(n)
    assert [s.name for s in svc.list_subjects()] == ["ägyptisch", "Bibelkunde", "Zeitgeschichte"]
