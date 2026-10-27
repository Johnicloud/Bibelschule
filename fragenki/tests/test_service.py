import pytest
from app.application.ports import BibelQuelle, TextKI
from app.application.services import FragenKiService
from app.domain.errors import InvalidInput


class FakeBibel(BibelQuelle):
    def __init__(self, text="Im Anfang schuf Gott Himmel und Erde."): self.text = text
    def kapitel(self, buch_kurz, kapitel): return self.text


class BrokenBibel(BibelQuelle):
    def kapitel(self, buch_kurz, kapitel): raise ConnectionError("nicht erreichbar")


class FakeKI(TextKI):
    def __init__(self, antwort): self.antwort = antwort
    def frage(self, prompt): return self.antwort


class BrokenKI(TextKI):
    def frage(self, prompt): raise ConnectionError("nicht erreichbar")


def test_generieren_parses_json_vorschlaege():
    antwort = '[{"frage": "Was schuf Gott zuerst?"}, {"frage": "Was bedeutet das heute?"}]'
    svc = FragenKiService(FakeBibel(), FakeKI(antwort))
    ergebnis = svc.generieren("1Mo", 1)
    assert ergebnis["vorschlaege"] == [
        {"frage": "Was schuf Gott zuerst?"},
        {"frage": "Was bedeutet das heute?"},
    ]
    assert ergebnis["rohtext_ki"] == antwort


def test_generieren_akzeptiert_auch_reine_string_liste():
    """Ollama hält sich nicht immer an die angefragte Objektform – reine Strings sind auch brauchbar."""
    antwort = '["Was schuf Gott zuerst?", "Wer sprach die Worte?"]'
    svc = FragenKiService(FakeBibel(), FakeKI(antwort))
    ergebnis = svc.generieren("1Mo", 1)
    assert ergebnis["vorschlaege"] == [{"frage": "Was schuf Gott zuerst?"}, {"frage": "Wer sprach die Worte?"}]


def test_generieren_ignores_surrounding_text_around_the_json_array():
    """Ollama hält sich nicht immer ans reine JSON (z. B. „Hier sind die Fragen: [...]“)."""
    antwort = 'Hier sind die Fragen:\n[{"frage": "Wer ist gemeint?"}]\nViel Erfolg!'
    svc = FragenKiService(FakeBibel(), FakeKI(antwort))
    ergebnis = svc.generieren("1Mo", 1)
    assert ergebnis["vorschlaege"] == [{"frage": "Wer ist gemeint?"}]


def test_generieren_falls_back_to_empty_list_when_answer_has_no_json():
    """Kein gültiges JSON: leere Vorschlagsliste, aber die rohe Antwort bleibt sichtbar (nur ein Vorschlag, kein Automatismus)."""
    antwort = "Das Kapitel handelt von der Schöpfung."
    svc = FragenKiService(FakeBibel(), FakeKI(antwort))
    ergebnis = svc.generieren("1Mo", 1)
    assert ergebnis["vorschlaege"] == []
    assert ergebnis["rohtext_ki"] == antwort


def test_generieren_skips_entries_without_frage():
    antwort = '[{"frage": ""}, {"anderes": "x"}, {"frage": "Echte Frage"}]'
    svc = FragenKiService(FakeBibel(), FakeKI(antwort))
    ergebnis = svc.generieren("1Mo", 1)
    assert ergebnis["vorschlaege"] == [{"frage": "Echte Frage"}]


def test_generieren_ohne_ki_schlaegt_fehl():
    svc = FragenKiService(FakeBibel(), ki=None)
    with pytest.raises(InvalidInput):
        svc.generieren("1Mo", 1)


def test_generieren_ohne_verstext_schlaegt_fehl():
    svc = FragenKiService(FakeBibel(text="  "), FakeKI("[]"))
    with pytest.raises(InvalidInput):
        svc.generieren("1Mo", 1)


def test_generieren_meldet_nicht_erreichbare_ki_als_invalid_input():
    svc = FragenKiService(FakeBibel(), BrokenKI())
    with pytest.raises(InvalidInput):
        svc.generieren("1Mo", 1)


def test_generieren_meldet_nicht_erreichbaren_bibel_dienst_als_invalid_input():
    svc = FragenKiService(BrokenBibel(), FakeKI("[]"))
    with pytest.raises(InvalidInput):
        svc.generieren("1Mo", 1)
