import io

import pytest
from app.adapters.inbound.api import create_app
from app.adapters.outbound.datei_leser import DateiLeserAdapter
from app.application.services import SkriptService
from app.domain.errors import InvalidInput
from app.domain.qualitaet import seitenqualitaet
from app.domain.suche import finde, suchwoerter
from fastapi.testclient import TestClient
from tests.test_service import InMemoryDateien, InMemoryRepo

GUTER_TEXT = ("Die Apostelgeschichte beschreibt die Entstehung der ersten Gemeinde in Jerusalem und die Ausbreitung des "
              "Evangeliums bis an die Enden der Erde durch die Apostel und ihre Mitarbeiter.")


def test_qualitaet_gut_schlecht_und_zu_wenig_text():
    assert seitenqualitaet(GUTER_TEXT) >= 95
    muell = "Bl aidr Hoockt en Teru l ur iNBeBaINE xkqzrt ppgfsd ~~^^ ### |||| qwrtz Eee iNBeBaINE bcdfgh"
    assert seitenqualitaet(muell + " " + muell) < 60
    assert seitenqualitaet("Titelseite") is None


def test_suche_alle_woerter_teilwoerter_trennung_und_ausschnitt():
    fund = finde("Die Apostel-\ngeschichte beschreibt die Gemeinden in Jerusalem.", suchwoerter("GEMEINDE jerusalem"))
    assert fund.ausschnitt == "Die Apostelgeschichte beschreibt die Gemeinden in Jerusalem."
    assert fund.ausschnitt[fund.von:fund.bis] == "Gemeinde"
    assert finde("Nur Jerusalem", suchwoerter("gemeinde jerusalem")) is None            # beide Wörter müssen vorkommen
    assert finde("irgendwas", []) is None


def _pdf(seiten):
    from reportlab.pdfgen import canvas
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    for text in seiten:
        y = 780
        for zeile in text.split("\n"):
            c.drawString(40, y, zeile); y -= 16
        c.showPage()
    c.save()
    return buf.getvalue()


@pytest.fixture
def svc():
    return SkriptService(InMemoryRepo(), InMemoryDateien(), DateiLeserAdapter())


def test_suche_ueber_alle_skripte_mit_seitenzahl(svc):
    svc.upload("f", "Skript.pdf", None, _pdf(["Einleitung zur Apostelgeschichte " * 3, "Die Gemeinde in Jerusalem wächst. " * 3]))
    svc.upload("f", "Notizen.txt", None, "Die Gemeinde in Antiochia".encode())
    svc.upload("anderes-fach", "Fremd.txt", None, "Gemeinde".encode())
    erg = svc.suche("f", "gemeinde")
    assert sorted((t["dateiname"], t["seite"]) for t in erg["treffer"]) == [("Notizen.txt", None), ("Skript.pdf", 2)]
    assert erg["ohne_text"] == []
    with pytest.raises(InvalidInput):
        svc.suche("f", "   ")


def test_gemerkte_seiten_werden_wiederverwendet_und_bei_neuer_fassung_ersetzt(svc):
    class Zaehler(DateiLeserAdapter):
        n = 0
        def seiten(self, dateiname, inhalt):
            Zaehler.n += 1
            return super().seiten(dateiname, inhalt)
    s2 = SkriptService(svc.repo, svc.dateien, Zaehler())
    s = s2.upload("f", "A.txt", None, b"Gnade und Friede")
    s2.suche("f", "gnade"); s2.suche("f", "friede")
    assert Zaehler.n == 1                                             # beim zweiten Suchen aus dem Gemerkten
    s2.dateien.speichere(s.id, b"Etwas ganz anderes")                  # Quelle geändert (Größe anders)
    assert s2.suche("f", "gnade")["treffer"] == [] and Zaehler.n == 2


def test_gescanntes_pdf_ohne_text_wird_gemeldet_und_nach_erkennung_gefunden(svc):
    class Ocr:
        def erkennen(self, pdf): return _pdf(["Die Gemeinde in Jerusalem"])
    svc2 = SkriptService(svc.repo, svc.dateien, DateiLeserAdapter(), Ocr())
    leer = _pdf([""])                                                  # eine Seite ohne Text = wie ein Scan
    s = svc2.upload("f", "Scan.pdf", None, leer)
    erg = svc2.suche("f", "gemeinde")
    assert erg["treffer"] == [] and erg["ohne_text"] == ["Scan.pdf"]
    svc2.text_erkennen_starten(s.id, im_hintergrund=False)
    erg = svc2.suche("f", "gemeinde")
    assert [t["seite"] for t in erg["treffer"]] == [1] and erg["ohne_text"] == []


def test_qualitaet_und_suche_ueber_die_api(svc):
    s = svc.upload("f", "Skript.pdf", None, _pdf([GUTER_TEXT.replace(". ", ".\n")]))
    client = TestClient(create_app(svc))
    q = client.get(f"/api/skripte/{s.id}/qualitaet").json()
    assert q["seiten_gesamt"] == 1 and q["durchschnitt"] >= 95 and q["unsicher"] == []
    assert client.get("/api/skripte/suche", params={"subject_id": "f", "q": "Jerusalem"}).json()["treffer"][0]["seite"] == 1
    assert client.get("/api/skripte/suche", params={"subject_id": "f", "q": " "}).status_code == 422
