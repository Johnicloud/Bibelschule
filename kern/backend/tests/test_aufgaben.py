"""Aufgaben-Standard: jede Aufgabe hat eine Art, ist bearbeitbar und zählt (mit Gewichtung) zum Gesamtfortschritt – oder ist
„nur zum Lernen“. Alte Aufgaben ohne die neuen Felder bleiben gültig."""
import json

import pytest
from app.adapters.outbound.json_repository import JsonSubjectRepository
from app.application.services import SubjectService
from app.domain.errors import InvalidInput, NotFound
from tests.test_service import FakeGateway, InMemoryRepo


@pytest.fixture
def svc():
    return SubjectService(InMemoryRepo(), FakeGateway())


def fach(svc):
    return svc.create_subject("Apostelgeschichte")[0]


def test_neue_aufgabe_ist_allgemein_zaehlt_und_hat_die_standardfelder(svc):
    a = svc.add_aufgabe(fach(svc).id, "Lesen").aufgaben[0]
    assert (a.art, a.zaehlt, a.notiz, a.soll, a.ist, a.einheit) == ("allgemein", True, "", None, None, "")


def test_aufgabe_mit_art_und_umfang_anlegen(svc):
    s = svc.add_aufgabe(fach(svc).id, "Register Orte", "2026-12-01", 30, art="ausarbeitung", soll=40, ist=10, einheit="Einträge")
    a = s.aufgaben[0]
    assert (a.art, a.frist, a.gewichtung, a.soll, a.ist, a.einheit) == ("ausarbeitung", "2026-12-01", 30, 40, 10, "Einträge")
    assert a.fortschritt() == 25
    with pytest.raises(InvalidInput):
        svc.add_aufgabe(s.id, "X", art="gibt-es-nicht")


def test_aufgabe_bearbeiten_aendert_nur_die_genannten_felder(svc):
    s = fach(svc)
    a = svc.add_aufgabe(s.id, "Klausur", "2026-12-10", 50, art="klausur").aufgaben[0]
    s = svc.update_aufgabe(s.id, a.id, titel=" Klausur Apg ", frist="2026-12-12", notiz="Raum 3")
    a = s.aufgaben[0]
    assert (a.titel, a.frist, a.notiz, a.gewichtung, a.art, a.zaehlt) == ("Klausur Apg", "2026-12-12", "Raum 3", 50, "klausur", True)
    s = svc.update_aufgabe(s.id, a.id, frist="", gewichtung=None, zaehlt=False)
    a = s.aufgaben[0]
    assert (a.frist, a.gewichtung, a.zaehlt) == (None, None, False)          # leer = entfernt


def test_aufgabe_bearbeiten_prueft_die_eingaben(svc):
    s = fach(svc)
    a = svc.add_aufgabe(s.id, "Referat").aufgaben[0]
    for falsch in ({"titel": "  "}, {"art": "unbekannt"}, {"gewichtung": 0}, {"gewichtung": 101}, {"soll": -1}, {"ist": -2}, {"unbekannt": 1}):
        with pytest.raises(InvalidInput):
            svc.update_aufgabe(s.id, a.id, **falsch)
    assert svc.update_aufgabe(s.id, a.id).aufgaben[0].titel == "Referat"     # nichts geändert
    with pytest.raises(NotFound):
        svc.update_aufgabe(s.id, "gibt-es-nicht", titel="x")


def test_gesamtfortschritt_zaehlt_teilfortschritt_gewichtet_und_laesst_lernaufgaben_weg(svc):
    s = fach(svc)
    svc.add_aufgabe(s.id, "Klausur", gewichtung=50, art="klausur")
    s = svc.add_aufgabe(s.id, "Ausarbeitung", gewichtung=50, art="ausarbeitung", soll=10, ist=4)
    teil, status = svc._aufgaben_part(s)
    assert teil["progress"] == 20 and status == {"count": 2, "done": 0}          # 0 % Klausur, 40 % Ausarbeitung, je zur Hälfte
    s = svc.add_aufgabe(s.id, "Zum Üben", art="allgemein", zaehlt=False)
    assert svc._aufgaben_part(s)[0]["progress"] == 20                              # „nur zum Lernen“ zählt nicht mit


def test_ohne_gewichtung_zaehlt_jede_aufgabe_gleich_und_ohne_zaehlende_gibt_es_keinen_fortschritt(svc):
    s = fach(svc)
    s = svc.add_aufgabe(s.id, "A", zaehlt=True)
    s = svc.add_aufgabe(s.id, "B")
    svc.set_aufgabe_erledigt(s.id, s.aufgaben[0].id, True)
    assert svc._aufgaben_part(s)[0]["progress"] == 50
    for a in s.aufgaben:
        svc.update_aufgabe(s.id, a.id, zaehlt=False)
    assert svc._aufgaben_part(s)[0]["progress"] is None


def test_klausur_offen_erkennt_die_art_auch_ohne_das_wort_im_titel(svc):
    s = fach(svc)
    s = svc.add_aufgabe(s.id, "Abschlussprüfung", art="klausur")
    s = svc.add_aufgabe(s.id, "Lesen")
    svc.set_aufgabe_erledigt(s.id, s.aufgaben[1].id, True)
    assert svc._fach_status(s, 50) == "klausur_offen"


def test_alte_aufgaben_ohne_neue_felder_werden_gelesen_und_neue_gespeichert(tmp_path):
    pfad = tmp_path / "subjects.json"
    pfad.write_text(json.dumps([{"id": "f1", "name": "Alt", "aufgaben": [{"id": "a1", "titel": "Alte Aufgabe", "erledigt": True}]}]))
    repo = JsonSubjectRepository(pfad)
    a = repo.get("f1").aufgaben[0]
    assert (a.art, a.zaehlt, a.notiz, a.soll, a.ist, a.einheit, a.erledigt) == ("allgemein", True, "", None, None, "", True)
    svc = SubjectService(repo, FakeGateway())
    svc.add_aufgabe("f1", "Neu", art="ausarbeitung", soll=5, ist=1, einheit="Seiten", zaehlt=False)
    n = JsonSubjectRepository(pfad).get("f1").aufgaben[1]
    assert (n.art, n.soll, n.ist, n.einheit, n.zaehlt) == ("ausarbeitung", 5, 1, "Seiten", False)


def test_orientierungsfragen_haengen_an_einem_set_und_ihr_fortschritt_kommt_von_den_karten(svc):
    s = fach(svc)
    s = svc.add_aufgabe(s.id, "Orientierungsfragen Kap. 1", gewichtung=40, art="fragen", set_name=" Fragen Kap. 1 ")
    a = s.aufgaben[0]
    assert (a.art, a.set_name) == ("fragen", "Fragen Kap. 1")
    s = svc.add_aufgabe(s.id, "Klausur", gewichtung=60, art="klausur")
    teil, _ = svc._aufgaben_part(s, {a.id: 50})                  # 10 von 20 Karten sicher gelernt
    assert teil["progress"] == 20                                  # 40 % Gewicht x 50 % Fortschritt
    assert svc._aufgaben_part(s)[0]["progress"] == 0               # ohne Angaben vom Karteikarten-Dienst: noch nichts gelernt
    svc.update_aufgabe(s.id, a.id, set_name="")
    assert s.aufgaben[0].set_name == ""


def test_fach_fortschritt_nimmt_den_set_stand_aus_dem_karteikarten_status(svc):
    s = fach(svc)
    a = svc.add_aufgabe(s.id, "Fragen", art="fragen", set_name="Fragen 1").aufgaben[0]
    status = {"karteikarten": {"card_count": 4, "mastered": 3, "sets": [{"name": "Fragen 1", "card_count": 4, "mastered": 3}]}, "register": None}
    zeile = svc._row(s, status, [])
    teil = next(p for p in zeile["parts"] if p["service"] == "aufgaben")
    assert teil["progress"] == 75


def test_aufgabe_mit_verknuepftem_pensum_nimmt_den_lesestand_fuer_den_fortschritt(svc):
    s = fach(svc)
    s = svc.add_aufgabe(s.id, "Lesen der Pflichtlektüre", art="lesen_pflicht", gewichtung=50)
    a = s.aufgaben[0]
    svc.set_aufgabe_pensum(s.id, a.id, "pensum-1")
    status = {"lesenachweis": {"pensen": [{"id": "pensum-1", "percent": 40}, {"id": "anderes", "percent": 90}]}}
    teil = next(p for p in svc._row(s, status, [])["parts"] if p["service"] == "aufgaben")
    assert teil["progress"] == 40
    assert svc._row(s, {}, [])["parts"][0]["progress"] == 0         # Lesedienst nicht erreichbar: noch nichts gelesen


def test_formular_der_pflichtlektuere_wird_gespeichert_und_geprueft(svc):
    s = fach(svc)
    a = svc.add_aufgabe(s.id, "Pflichtlektüre", art="lesen_pflicht", formular="standard").aufgaben[0]
    assert a.formular == "standard"
    s = svc.update_aufgabe(s.id, a.id, formular="angefragt")
    assert s.aufgaben[0].formular == "angefragt"
    s = svc.update_aufgabe(s.id, a.id, formular="skript:abc123")
    assert s.aufgaben[0].formular == "skript:abc123"
    s = svc.update_aufgabe(s.id, a.id, formular="")
    assert s.aufgaben[0].formular == ""
    with pytest.raises(InvalidInput):
        svc.update_aufgabe(s.id, a.id, formular="irgendwas")


def test_lese_aufgabe_kann_beim_anlegen_ein_pensum_verknuepfen(svc):
    s = svc.add_aufgabe(fach(svc).id, "Skript lesen", art="lesen_skript", pensum_id="pensum-9")
    assert s.aufgaben[0].pensum_id == "pensum-9"


def test_jede_aufgabe_kann_nachtraeglich_an_ein_set_geknuepft_werden(svc):
    s = fach(svc)
    a = svc.add_aufgabe(s.id, "Beantwortung der Orientierungsfragen").aufgaben[0]       # „allgemein“, ohne Set angelegt
    s = svc.update_aufgabe(s.id, a.id, set_name="Fragen Kap. 1")
    status = {"karteikarten": {"sets": [{"name": "Fragen Kap. 1", "card_count": 10, "mastered": 3}]}}
    teil = next(p for p in svc._row(s, status, [])["parts"] if p["service"] == "aufgaben")
    assert teil["progress"] == 30
