import pytest
from app.application.ports import PdfText, TextKI
from app.application.services import AufgabenLeseService
from app.domain.errors import InvalidInput


class FakePdfText(PdfText):
    def __init__(self, text="Klausur am 01.03.2027, 50 %."): self.text = text
    def text_auslesen(self, pdf): return self.text


class FakeKI(TextKI):
    def __init__(self, antwort): self.antwort = antwort
    def frage(self, prompt): return self.antwort


class BrokenKI(TextKI):
    def frage(self, prompt): raise ConnectionError("nicht erreichbar")


def test_lesen_parses_json_vorschlaege():
    antwort = '[{"titel": "Klausur", "frist": "2027-03-01", "gewichtung": 50}, {"titel": "Lesen"}]'
    svc = AufgabenLeseService(FakePdfText(), FakeKI(antwort))
    ergebnis = svc.lesen(b"irgendein-pdf")
    assert ergebnis["vorschlaege"] == [
        {"titel": "Klausur", "frist": "2027-03-01", "gewichtung": 50},
        {"titel": "Lesen", "frist": None, "gewichtung": None},
    ]
    assert ergebnis["rohtext_ki"] == antwort


def test_lesen_ignores_surrounding_text_around_the_json_array():
    """Ollama hält sich nicht immer ans reine JSON (z. B. „Hier ist die Liste: [...]“)."""
    antwort = 'Hier ist die Liste:\n[{"titel": "Anwesenheit"}]\nViel Erfolg!'
    svc = AufgabenLeseService(FakePdfText(), FakeKI(antwort))
    ergebnis = svc.lesen(b"irgendein-pdf")
    assert ergebnis["vorschlaege"] == [{"titel": "Anwesenheit", "frist": None, "gewichtung": None}]


def test_lesen_falls_back_to_empty_list_when_answer_has_no_json():
    """Kein gültiges JSON: leere Vorschlagsliste, aber die rohe Antwort bleibt sichtbar (nur ein Vorschlag, kein Automatismus)."""
    antwort = "Das Formular enthält eine Klausur und eine Lesepflicht."
    svc = AufgabenLeseService(FakePdfText(), FakeKI(antwort))
    ergebnis = svc.lesen(b"irgendein-pdf")
    assert ergebnis["vorschlaege"] == []
    assert ergebnis["rohtext_ki"] == antwort


def test_lesen_skips_entries_without_titel():
    antwort = '[{"titel": ""}, {"frist": "2027-01-01"}, {"titel": "Echte Aufgabe"}]'
    svc = AufgabenLeseService(FakePdfText(), FakeKI(antwort))
    ergebnis = svc.lesen(b"irgendein-pdf")
    assert ergebnis["vorschlaege"] == [{"titel": "Echte Aufgabe", "frist": None, "gewichtung": None}]


def test_lesen_ohne_ki_schlaegt_fehl():
    svc = AufgabenLeseService(FakePdfText(), ki=None)
    with pytest.raises(InvalidInput):
        svc.lesen(b"irgendein-pdf")


def test_lesen_ohne_text_schlaegt_fehl():
    svc = AufgabenLeseService(FakePdfText(text="  "), FakeKI("[]"))
    with pytest.raises(InvalidInput):
        svc.lesen(b"irgendein-pdf")


def test_lesen_meldet_nicht_erreichbare_ki_als_invalid_input():
    svc = AufgabenLeseService(FakePdfText(), BrokenKI())
    with pytest.raises(InvalidInput):
        svc.lesen(b"irgendein-pdf")
