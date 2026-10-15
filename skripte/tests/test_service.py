import pytest
from app.application.ports import DateiSpeicher, PdfText, SkriptRepository
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


class FakePdfText(PdfText):
    """Tut so, als stünde in jeder PDF-Datei genau ihr Inhalt als Text (kein echtes PDF-Parsing nötig)."""
    def text(self, pdf):
        return pdf.decode("utf-8")


@pytest.fixture
def svc():
    return SkriptService(InMemoryRepo(), InMemoryDateien(), FakePdfText())


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


def test_suche_findet_treffer_in_pdf_dateien(svc):
    svc.upload("fach-1", "a.pdf", "application/pdf", b"Hier geht es um die Gnade Gottes.")
    svc.upload("fach-1", "b.pdf", "application/pdf", b"Nichts Passendes hier drin.")
    treffer = svc.suche("Gnade")
    assert len(treffer) == 1 and treffer[0]["dateiname"] == "a.pdf" and "Gnade" in treffer[0]["ausschnitt"]


def test_suche_ist_case_insensitive(svc):
    svc.upload("fach-1", "a.pdf", "application/pdf", b"Grosse Gnade")
    assert len(svc.suche("GNADE")) == 1


def test_suche_ignoriert_dateien_ohne_pdf_content_type(svc):
    svc.upload("fach-1", "bild.png", "image/png", b"Gnade")
    assert svc.suche("Gnade") == []


def test_suche_kann_auf_ein_fach_eingeschraenkt_werden(svc):
    svc.upload("fach-1", "a.pdf", "application/pdf", b"Gnade")
    svc.upload("fach-2", "b.pdf", "application/pdf", b"Gnade")
    assert len(svc.suche("Gnade", "fach-1")) == 1


def test_suche_rejects_zu_kurzen_text(svc):
    with pytest.raises(InvalidInput):
        svc.suche("a")


def test_suche_without_pdf_text_wiring_returns_empty():
    svc = SkriptService(InMemoryRepo(), InMemoryDateien())   # kein PdfText
    svc.upload("fach-1", "a.pdf", "application/pdf", b"Gnade")
    assert svc.suche("Gnade") == []


def test_subject_status_counts_skripte(svc):
    assert svc.subject_status("fach-1") == {"count": 0}
    svc.upload("fach-1", "a.pdf", "application/pdf", b"1")
    assert svc.subject_status("fach-1") == {"count": 1}
