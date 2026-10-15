import pytest
from app.application.ports import DateiSpeicher, IndexRepository, PdfText, VersRepository, VerseExtractor
from app.application.services import BibelService
from app.domain.bible import BOOKS, find_book
from app.domain.errors import InvalidInput, NotFound
from app.domain.models import Bibelindex


class InMemoryIndexRepo(IndexRepository):
    def __init__(self): self.d = None
    def get(self): return self.d
    def save(self, index): self.d = index


class InMemoryVersRepo(VersRepository):
    def __init__(self): self.verse = []
    def ersetze_alle(self, verse): self.verse = verse
    def kapitel(self, buch_index, kapitel):
        return sorted((v for v in self.verse if v.buch_index == buch_index and v.kapitel == kapitel),
                     key=lambda v: v.vers)
    def hat_verse(self): return bool(self.verse)


class InMemoryDateien(DateiSpeicher):
    def __init__(self): self.inhalt = None
    def speichere(self, inhalt): self.inhalt = inhalt
    def lies(self): return self.inhalt


class FakeText(PdfText):
    """Tut so, als hätte sie Genesis auf Seite 1 und Johannes auf Seite 500 gefunden."""
    def buchseiten_erkennen(self, pdf):
        return {find_book("1Mo").index: 1, find_book("Joh").index: 500}


class FakeExtractor(VerseExtractor):
    """Liefert für 1. Mose immer zwei feste Verse, egal welche Seiten übergeben werden."""
    def buch_verse(self, pdf, von_seite, bis_seite):
        return [(1, 1, "Im Anfang schuf Gott die Himmel und die Erde."), (1, 2, "Die Erde aber war wüst und leer.")]


@pytest.fixture
def svc():
    return BibelService(InMemoryIndexRepo(), InMemoryDateien(), FakeText(), InMemoryVersRepo(), FakeExtractor())


def test_hochladen_speichert_datei_und_erkannte_seiten(svc):
    index = svc.hochladen("meine-bibel.pdf", b"%PDF-fake")
    assert index.dateiname == "meine-bibel.pdf"
    assert len(index.buchseiten) == len(BOOKS)
    gen = index.seite_von(find_book("1Mo").index)
    assert gen.seite == 1 and gen.erkannt is True
    jud = index.seite_von(find_book("Jud").index)
    assert jud.seite is None and jud.erkannt is False
    assert svc.datei() == b"%PDF-fake"


def test_hochladen_rejects_empty_file(svc):
    with pytest.raises(InvalidInput):
        svc.hochladen("leer.pdf", b"")


def test_seite_setzen_overrides_and_clears_erkannt_flag(svc):
    svc.hochladen("b.pdf", b"x")
    index = svc.seite_setzen(find_book("1Mo").index, 7)
    gen = index.seite_von(find_book("1Mo").index)
    assert gen.seite == 7 and gen.erkannt is False   # von Hand überschrieben, nicht mehr "erkannt"


def test_seite_setzen_validates(svc):
    with pytest.raises(InvalidInput):
        svc.seite_setzen(999, 1)
    with pytest.raises(InvalidInput):
        svc.seite_setzen(find_book("1Mo").index, 0)


def test_stelle_chapter_one_is_exact(svc):
    svc.hochladen("b.pdf", b"x")
    ergebnis = svc.stelle("1. Mose 1,1")
    assert ergebnis == {"buch": "1Mo", "name": "1. Mose", "kapitel": 1, "seite": 1, "genau": True}


def test_stelle_other_chapters_are_interpolated_between_this_and_the_next_known_book(svc):
    svc.hochladen("b.pdf", b"x")
    # 1Mo hat 50 Kapitel, Seite 1 bis (näheste bekannte Seite danach) 500 = Johannes.
    ergebnis = svc.stelle("1Mo 25")   # Kapitel 25 von 50 -> etwa die Mitte
    assert ergebnis["genau"] is False
    assert 1 < ergebnis["seite"] < 500


def test_stelle_raises_when_book_has_no_page_yet(svc):
    svc.hochladen("b.pdf", b"x")
    with pytest.raises(NotFound):
        svc.stelle("2Mo 1")   # 2. Mose wurde von FakeText nicht erkannt


def test_index_without_upload_lists_all_books_empty():
    svc = BibelService(InMemoryIndexRepo(), InMemoryDateien(), FakeText())
    index = svc.index()
    assert len(index.buchseiten) == len(BOOKS)
    assert all(b.seite is None for b in index.buchseiten)


def test_hochladen_allein_liest_noch_keine_verse(svc):
    """Verse einlesen ist bewusst ein eigener Schritt (verse_im_hintergrund_einlesen), nicht Teil von
    hochladen() selbst – das dauert bei einer ganzen Bibel 1-2 Minuten, zu lang für eine Antwort."""
    svc.hochladen("b.pdf", b"x")
    assert svc.kapitel("1Mo", 1)["verse"] == []
    assert svc.hat_verse() is False


def test_verse_im_hintergrund_einlesen_extracts_verses_for_recognized_books(svc):
    svc.hochladen("b.pdf", b"x")
    svc.verse_im_hintergrund_einlesen()
    ergebnis = svc.kapitel("1Mo", 1)
    assert ergebnis["buch"] == "1Mo" and ergebnis["kapitel_gesamt"] == 50
    assert [v["text"] for v in ergebnis["verse"]] == [
        "Im Anfang schuf Gott die Himmel und die Erde.", "Die Erde aber war wüst und leer."]
    assert svc.hat_verse() is True


def test_verse_im_hintergrund_einlesen_without_wiring_does_nothing():
    svc = BibelService(InMemoryIndexRepo(), InMemoryDateien(), FakeText())   # kein verse_repo/extractor
    svc.hochladen("b.pdf", b"x")
    svc.verse_im_hintergrund_einlesen()   # darf nicht knallen
    assert svc.hat_verse() is False


def test_kapitel_validates_book_and_chapter_number(svc):
    with pytest.raises(InvalidInput):
        svc.kapitel("Xyz", 1)
    with pytest.raises(InvalidInput):
        svc.kapitel("Jud", 2)   # Judas hat nur 1 Kapitel


def test_kapitel_is_empty_before_any_upload():
    svc = BibelService(InMemoryIndexRepo(), InMemoryDateien(), FakeText(), InMemoryVersRepo(), FakeExtractor())
    assert svc.kapitel("1Mo", 1)["verse"] == []


def test_hochladen_without_extractor_wiring_skips_verses_silently():
    svc = BibelService(InMemoryIndexRepo(), InMemoryDateien(), FakeText())   # kein verse_repo/extractor
    index = svc.hochladen("b.pdf", b"x")
    assert index.dateiname == "b.pdf"   # Seiten-Erkennung funktioniert weiterhin ohne Verse
