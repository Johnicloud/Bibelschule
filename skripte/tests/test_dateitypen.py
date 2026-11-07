import io
import zipfile

import pytest
from app.adapters.inbound.api import create_app
from app.adapters.outbound.datei_leser import DateiLeserAdapter
from app.application.services import SkriptService
from app.domain.dateitypen import art, kann_fragen, media_type
from app.domain.errors import InvalidInput
from fastapi.testclient import TestClient
from tests.test_service import InMemoryDateien, InMemoryRepo


class FakeBilder:
    def zu_jpeg(self, inhalt): return b"JPEG:" + inhalt


@pytest.fixture
def svc():
    return SkriptService(InMemoryRepo(), InMemoryDateien(), DateiLeserAdapter(), None, FakeBilder())


def test_art_nach_endung():
    assert [art(n) for n in ["a.PDF", "a.docx", "a.md", "a.pptx", "a.heic", "a.mp3", "a.MOV", "a.doc", "a.xyz", "ohne"]] == \
        ["pdf", "docx", "text", "ansichtstext", "sonst", "audio", "video", "doc", "sonst", "sonst"]
    assert kann_fragen("a.pptx") and kann_fragen("a.md") and not kann_fragen("a.mp3") and not kann_fragen("a.doc")


def test_media_type_nach_endung_vor_dem_gespeicherten():
    assert media_type("a.md", "application/octet-stream") == "text/plain; charset=utf-8"
    assert media_type("a.m4a", None) == "audio/mp4"
    assert media_type("a.xyz", "application/x-foo") == "application/x-foo"


def test_heic_wird_beim_hochladen_zu_jpg(svc):
    s = svc.upload("f", "IMG_0001.HEIC", "image/heic", b"rohdaten")
    assert (s.dateiname, s.content_type) == ("IMG_0001.jpg", "image/jpeg")
    assert svc.datei(s.id)[1] == b"JPEG:rohdaten"
    with pytest.raises(InvalidInput):
        SkriptService(InMemoryRepo(), InMemoryDateien()).upload("f", "x.heic", None, b"x")


def test_text_und_markdown_fragen(svc):
    t = svc.upload("f", "Fragen.txt", None, "1. Wer war Petrus?\n2. Wo lebte Paulus?\n".encode("utf-8"))
    assert svc.fragen(t.id) == ["Wer war Petrus?", "Wo lebte Paulus?"]
    m = svc.upload("f", "Fragen.md", None, "# Fragen\n- Wer war Petrus?\n- Wo lebte Paulus?\n".encode("utf-8"))
    assert svc.fragen(m.id) == ["Fragen", "Wer war Petrus?", "Wo lebte Paulus?"]
    alt = svc.upload("f", "Alt.txt", None, "Wer schrieb Lk?\nWas ist Gnade für Jünger?".encode("latin-1"))
    assert svc.fragen(alt.id)[1] == "Was ist Gnade für Jünger?"          # kein UTF-8: als Latin-1 gelesen


def _zip(dateien):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, inhalt in dateien.items():
            z.writestr(name, inhalt)
    return buf.getvalue()


def test_odt_und_pptx_text(svc):
    odt = _zip({"content.xml": '<office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
                               'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"><office:body><office:text>'
                               '<text:h>Überschrift</text:h><text:p>Wer war <text:span>Petrus</text:span>?</text:p>'
                               '</office:text></office:body></office:document-content>'})
    s = svc.upload("f", "A.odt", None, odt)
    assert svc.fragen(s.id) == ["Überschrift", "Wer war Petrus?"]
    folie = lambda *t: ('<p:sld xmlns:p="x" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><p:cSld>'
                        + "".join(f"<a:p><a:r><a:t>{x}</a:t></a:r></a:p>" for x in t) + "</p:cSld></p:sld>")
    pptx = _zip({"ppt/slides/slide2.xml": folie("Zweite Folie"), "ppt/slides/slide1.xml": folie("Titel", "Punkt")})
    p = svc.upload("f", "A.pptx", None, pptx)
    assert svc.ansichtstext(p.id) == "── Folie 1 ──\nTitel\nPunkt\n\n── Folie 2 ──\nZweite Folie"


def test_spulen_liefert_nur_das_angefragte_stueck_mit_206(svc):
    s = svc.upload("f", "Aufnahme.mp3", None, bytes(range(100)))
    client = TestClient(create_app(svc))
    url = f"/api/skripte/{s.id}/datei"
    r = client.get(url, headers={"Range": "bytes=10-19"})
    assert (r.status_code, r.content, r.headers["content-range"]) == (206, bytes(range(10, 20)), "bytes 10-19/100")
    assert r.headers["accept-ranges"] == "bytes" and r.headers["content-type"] == "audio/mpeg"
    assert client.get(url, headers={"Range": "bytes=90-"}).content == bytes(range(90, 100))
    assert client.get(url, headers={"Range": "bytes=-5"}).content == bytes(range(95, 100))
    assert client.get(url).status_code == 200 and len(client.get(url).content) == 100   # ohne Range wie bisher
    assert client.get(url, headers={"Range": "bytes=500-"}).status_code == 422


def test_ansichtstext_route(svc):
    s = svc.upload("f", "Notiz.txt", None, "Hallo\nWelt".encode())
    r = TestClient(create_app(svc)).get(f"/api/skripte/{s.id}/text")
    assert r.status_code == 200 and "Hallo" in r.text
