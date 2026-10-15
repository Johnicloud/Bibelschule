import pytest
from app.application.ports import BildExtraktor, BuchRepository, DateiSpeicher, OcrKI, TextLeser, TextPdfBauer
from app.application.services import BibliothekService
from app.domain.errors import InvalidInput, NotFound


class InMemoryRepo(BuchRepository):
    def __init__(self): self.d = {}
    def list(self): return list(self.d.values())
    def get(self, i): return self.d.get(i)
    def save(self, buch): self.d[buch.id] = buch
    def delete(self, i): self.d.pop(i, None)


class InMemoryDateien(DateiSpeicher):
    def __init__(self): self._original, self._text = {}, {}
    def speichere_original(self, buch_id, inhalt): self._original[buch_id] = inhalt
    def original(self, buch_id): return self._original.get(buch_id)
    def speichere_text(self, buch_id, inhalt): self._text[buch_id] = inhalt
    def text_pdf(self, buch_id): return self._text.get(buch_id)
    def loesche(self, buch_id): self._original.pop(buch_id, None); self._text.pop(buch_id, None)


class FakeBilder(BildExtraktor):
    """Tut so, als hätte die PDF genau zwei Seiten-Bilder."""
    def seiten_bilder(self, pdf): return [b"seite-1-bild", b"seite-2-bild"]


class FakeOcr(OcrKI):
    def __init__(self): self.gesehen = []
    def seite_lesen(self, bild):
        self.gesehen.append(bild)
        return f"Text von {bild.decode()}"


class FakeTextPdfBauer(TextPdfBauer):
    def baue(self, original_pdf, text_je_seite):
        return b"TEXT-PDF:" + "|".join(text_je_seite).encode()


class FakeTextLeser(TextLeser):
    """Tut so, als stünde in der Text-PDF genau ihr eigener Inhalt als Text (kein echtes PDF-Parsing nötig)."""
    def text(self, pdf):
        return pdf.decode()


@pytest.fixture
def svc():
    return BibliothekService(InMemoryRepo(), InMemoryDateien(), FakeBilder(), FakeOcr(), FakeTextPdfBauer(),
                             FakeTextLeser())


def test_add_buch_requires_a_title(svc):
    with pytest.raises(InvalidInput):
        svc.add_buch("  ")


def test_add_and_list_sorted_by_title(svc):
    svc.add_buch("Systematische Theologie")
    svc.add_buch("Dogmatik", autor="Berkhof", jahr=1932)
    assert [b.titel for b in svc.list_buecher()] == ["Dogmatik", "Systematische Theologie"]
    assert svc.list_buecher()[0].autor == "Berkhof" and svc.list_buecher()[0].jahr == 1932


def test_update_and_delete(svc):
    b = svc.add_buch("Altes Buch")
    updated = svc.update_buch(b.id, "Neuer Titel", "Autor", "Verlag", 2020, "123-456", "Regal 3", "Notiz")
    assert updated.titel == "Neuer Titel" and updated.standort == "Regal 3"
    svc.delete_buch(b.id)
    assert svc.list_buecher() == []
    with pytest.raises(NotFound):
        svc.delete_buch(b.id)


def test_ausleihen_und_zurueckgeben(svc):
    b = svc.add_buch("Kommentar zu Römer")
    assert b.ausgeliehen_an is None
    b = svc.ausleihen(b.id, "Johannes")
    assert b.ausgeliehen_an == "Johannes"
    b = svc.zurueckgeben(b.id)
    assert b.ausgeliehen_an is None


def test_ausleihen_requires_a_name(svc):
    b = svc.add_buch("Buch")
    with pytest.raises(InvalidInput):
        svc.ausleihen(b.id, "  ")


def test_assign_and_unassign_subjects(svc):
    b = svc.add_buch("Hermeneutik")
    svc.assign(b.id, "fach-1")
    svc.assign(b.id, "fach-1")   # doppelt zuordnen ändert nichts
    svc.assign(b.id, "fach-2")
    assert sorted(svc._buch(b.id).faecher) == ["fach-1", "fach-2"]
    assert [x.id for x in svc.for_subject("fach-1")] == [b.id]

    svc.unassign(b.id, "fach-1")
    assert svc._buch(b.id).faecher == ["fach-2"]
    assert svc.for_subject("fach-1") == []


def test_discard_subject_removes_assignment_but_keeps_buch(svc):
    b = svc.add_buch("Kirchengeschichte")
    svc.assign(b.id, "fach-1")
    svc.assign(b.id, "fach-2")
    svc.discard_subject("fach-1")
    assert svc._buch(b.id).faecher == ["fach-2"]
    assert svc.list_buecher() == [svc._buch(b.id)]   # Buch bleibt erhalten


def test_subject_status_counts_assigned_buecher(svc):
    b1, b2 = svc.add_buch("Eins"), svc.add_buch("Zwei")
    svc.assign(b1.id, "fach-1")
    assert svc.subject_status("fach-1") == {"count": 1}
    svc.assign(b2.id, "fach-1")
    assert svc.subject_status("fach-1") == {"count": 2}


def test_datei_hochladen_speichert_und_markiert_das_buch(svc):
    b = svc.add_buch("Gescanntes Buch")
    assert b.hat_datei is False
    b = svc.datei_hochladen(b.id, b"%PDF-fake")
    assert b.hat_datei is True and b.text_erkannt is False
    assert svc.original_datei(b.id) == b"%PDF-fake"


def test_datei_hochladen_rejects_empty_file(svc):
    b = svc.add_buch("Buch")
    with pytest.raises(InvalidInput):
        svc.datei_hochladen(b.id, b"")


def test_text_erkennen_liest_jede_seite_und_baut_eine_text_pdf(svc):
    b = svc.add_buch("Gescanntes Buch")
    svc.datei_hochladen(b.id, b"%PDF-fake")
    svc.text_erkennen(b.id)
    text_pdf = svc.text_datei(b.id)
    assert text_pdf == b"TEXT-PDF:Text von seite-1-bild|Text von seite-2-bild"
    assert svc._buch(b.id).text_erkannt is True


def test_text_erkennen_without_wiring_does_nothing():
    svc = BibliothekService(InMemoryRepo())   # keine Datei-Ablage/KI verdrahtet
    b = svc.add_buch("Buch")
    svc.text_erkennen(b.id)   # darf nicht knallen
    assert svc.text_datei(b.id) is None


def test_text_erkennen_without_uploaded_file_does_nothing(svc):
    b = svc.add_buch("Buch ohne Datei")
    svc.text_erkennen(b.id)
    assert svc.text_datei(b.id) is None


def test_suche_findet_treffer_nur_in_buechern_mit_text_erkennung(svc):
    b1 = svc.add_buch("Mit Text")
    svc.datei_hochladen(b1.id, b"%PDF-fake")
    svc.dateien.speichere_text(b1.id, b"Hier geht es um die Gnade Gottes.")
    svc.repo.get(b1.id).text_erkannt = True
    b2 = svc.add_buch("Ohne Erkennung")
    svc.datei_hochladen(b2.id, b"%PDF-fake")
    treffer = svc.suche("Gnade")
    assert len(treffer) == 1 and treffer[0]["titel"] == "Mit Text" and "Gnade" in treffer[0]["ausschnitt"]


def test_suche_ist_case_insensitive(svc):
    b = svc.add_buch("Buch")
    svc.datei_hochladen(b.id, b"%PDF-fake")
    svc.dateien.speichere_text(b.id, b"Grosse Gnade")
    svc.repo.get(b.id).text_erkannt = True
    assert len(svc.suche("GNADE")) == 1


def test_suche_rejects_zu_kurzen_text(svc):
    with pytest.raises(InvalidInput):
        svc.suche("a")


def test_suche_without_wiring_returns_empty():
    svc = BibliothekService(InMemoryRepo())   # keine Datei-Ablage/kein TextLeser
    svc.add_buch("Buch")
    assert svc.suche("Gnade") == []
