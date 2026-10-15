import pytest
from app.application.ports import PdfText, TextToSpeech
from app.application.services import MAX_ZEICHEN, VorleseService
from app.domain.errors import InvalidInput


class FakeTts(TextToSpeech):
    def __init__(self, bricht_ab=False): self.bricht_ab = bricht_ab
    def sprich(self, text):
        if self.bricht_ab:
            raise RuntimeError("piper ist abgestürzt")
        return f"audio:{text}".encode()


class FakePdfText(PdfText):
    def __init__(self, text=""): self.text = text
    def text_auslesen(self, pdf): return self.text


@pytest.fixture
def svc():
    return VorleseService(FakeTts(), FakePdfText())


def test_text_vorlesen_gibt_audio_zurueck(svc):
    assert svc.text_vorlesen(" Hallo Welt ") == b"audio:Hallo Welt"


def test_text_vorlesen_lehnt_leeren_text_ab(svc):
    with pytest.raises(InvalidInput):
        svc.text_vorlesen("   ")


def test_text_vorlesen_lehnt_zu_langen_text_ab(svc):
    with pytest.raises(InvalidInput):
        svc.text_vorlesen("x" * (MAX_ZEICHEN + 1))


def test_text_vorlesen_meldet_fehler_der_vertonung_als_invalid_input():
    svc = VorleseService(FakeTts(bricht_ab=True), FakePdfText())
    with pytest.raises(InvalidInput):
        svc.text_vorlesen("Hallo")


def test_pdf_vorlesen_liest_text_aus_und_vertont_ihn():
    svc = VorleseService(FakeTts(), FakePdfText("Aus der PDF gelesen"))
    assert svc.pdf_vorlesen(b"irrelevante-bytes") == b"audio:Aus der PDF gelesen"


def test_pdf_vorlesen_lehnt_pdf_ohne_text_ab():
    svc = VorleseService(FakeTts(), FakePdfText(""))
    with pytest.raises(InvalidInput):
        svc.pdf_vorlesen(b"irrelevante-bytes")


def test_subject_hooks_sind_no_ops(svc):
    assert svc.subject_status("irgendein-fach") == {}
    svc.discard_subject("irgendein-fach")   # darf nicht werfen
