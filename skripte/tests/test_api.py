from app.adapters.inbound.api import create_app
from app.application.services import SkriptService
from fastapi.testclient import TestClient
from tests.test_service import InMemoryDateien, InMemoryRepo


def test_datei_mit_sonderzeichen_im_namen_liefert_keinen_serverfehler():
    # Dateinamen können Zeichen enthalten, die in HTTP-Kopfzeilen (Latin-1) nicht gehen – das gab früher 500
    service = SkriptService(InMemoryRepo(), InMemoryDateien())
    s = service.upload("f", "Übung – Skript.pdf", "application/pdf", b"%PDF-1.4")
    antwort = TestClient(create_app(service)).get(f"/api/skripte/{s.id}/datei")
    assert antwort.status_code == 200
    assert "filename*=UTF-8''" in antwort.headers["content-disposition"]


def test_ansicht_fuer_neuen_tab_gibt_es_nur_fuer_vorhandene_skripte():
    service = SkriptService(InMemoryRepo(), InMemoryDateien())
    s = service.upload("f", "Fragen.docx", None, b"x")
    client = TestClient(create_app(service))
    assert client.get(f"/api/skripte/{s.id}/ansicht").status_code == 200
    assert client.get("/api/skripte/unbekannt/ansicht").status_code == 404
