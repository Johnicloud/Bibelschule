import pytest
from app.application.ports import DateiSpeicher, SkriptRepository
from app.application.services import MAX_BYTES, SkriptService
from app.domain.errors import InvalidInput, NotFound


class InMemoryRepo(SkriptRepository):
    def __init__(self): self.d = {}
    def list(self, subject_id=None): return [s for s in self.d.values() if subject_id is None or s.subject_id == subject_id]
    def get(self, i): return self.d.get(i)
    def save(self, s): self.d[s.id] = s
    def delete(self, i): self.d.pop(i, None)
    def delete_subject(self, subject_id):
        weg = [s for s in self.d.values() if s.subject_id == subject_id]
        for s in weg: self.d.pop(s.id, None)
        return weg


class InMemoryDateien(DateiSpeicher):
    def __init__(self): self.d = {}
    def speichere(self, i, inhalt): self.d[i] = inhalt
    def lies(self, i): return self.d.get(i)
    def loesche(self, i): self.d.pop(i, None)
    def vorhanden(self, i): return i in self.d
    def groesse(self, i): return len(self.d[i]) if i in self.d else None
    def lies_bereich(self, i, start, ende): return self.d[i][start:ende + 1]


@pytest.fixture
def svc():
    return SkriptService(InMemoryRepo(), InMemoryDateien())


def test_upload_requires_a_filename(svc):
    with pytest.raises(InvalidInput):
        svc.upload("fach-1", "  ", "application/pdf", b"xyz")


def test_upload_rejects_too_large_files(svc):
    with pytest.raises(InvalidInput):
        svc.upload("fach-1", "riesig.pdf", "application/pdf", b"x" * (MAX_BYTES + 1))


def test_upload_list_and_download(svc):
    s = svc.upload("fach-1", "Skript.pdf", "application/pdf", b"%PDF-1.4...")
    assert s.groesse == len(b"%PDF-1.4...") and s.subject_id == "fach-1"
    assert [x.dateiname for x in svc.list_skripte("fach-1")] == ["Skript.pdf"]
    geholt, inhalt = svc.datei(s.id)
    assert geholt.id == s.id and inhalt == b"%PDF-1.4..."


def test_delete_removes_metadata_and_content(svc):
    s = svc.upload("fach-1", "a.pdf", "application/pdf", b"123")
    svc.delete(s.id)
    assert svc.list_skripte("fach-1") == []
    with pytest.raises(NotFound):
        svc.datei(s.id)


def test_discard_subject_removes_all_its_skripte(svc):
    svc.upload("fach-1", "a.pdf", "application/pdf", b"1")
    svc.upload("fach-1", "b.pdf", "application/pdf", b"2")
    svc.upload("fach-2", "c.pdf", "application/pdf", b"3")
    svc.discard_subject("fach-1")
    assert svc.list_skripte("fach-1") == []
    assert len(svc.list_skripte("fach-2")) == 1


def test_subject_status_counts_skripte(svc):
    assert svc.subject_status("fach-1") == {"count": 0}
    svc.upload("fach-1", "a.pdf", "application/pdf", b"1")
    assert svc.subject_status("fach-1") == {"count": 1}
