"""Anwendungsfälle. Kennen nur Domäne und Ports."""
from app.application.ports import PdfText, TextToSpeech
from app.domain.errors import InvalidInput

MAX_ZEICHEN = 20_000   # längere Texte brauchen sehr lange zum Vertonen (lokale KI, keine Cloud)


class VorleseService:
    def __init__(self, tts: TextToSpeech, pdf_text: PdfText):
        self.tts = tts
        self.pdf_text = pdf_text

    def text_vorlesen(self, text: str) -> bytes:
        text = (text or "").strip()
        if not text:
            raise InvalidInput("Kein Text zum Vorlesen.")
        if len(text) > MAX_ZEICHEN:
            raise InvalidInput(f"Der Text ist zu lang (höchstens {MAX_ZEICHEN} Zeichen).")
        try:
            return self.tts.sprich(text)
        except Exception as e:   # die lokale Vertonung kann fehlschlagen (z. B. unbekanntes Zeichen, Absturz)
            raise InvalidInput(f"Das Vorlesen ist fehlgeschlagen: {e}") from e

    def pdf_vorlesen(self, pdf: bytes) -> bytes:
        text = self.pdf_text.text_auslesen(pdf)
        if not text.strip():
            raise InvalidInput("Aus der PDF-Datei ließ sich kein Text lesen.")
        return self.text_vorlesen(text)

    # Fach-Hooks: der Dienst kennt kein einzelnes Fach (liest nur vor, speichert nichts).
    def discard_subject(self, subject_id: str) -> None:
        pass

    def subject_status(self, subject_id: str) -> dict:
        return {}
