"""Die mitgelieferte Vorlage „Lesenachweis Pflichtlektüre“ (Bibelseminar Eben-Ezer). Positionen von Hand aus dem
PDF vermessen (pdfplumber, Seite 595 x 842 Punkte, A4). Neue/andere Vorlagen bekommen ihre Felder nicht automatisch
vermessen – dafür gibt es den Ollama-Textvorschlag (siehe TextKI), die Positionen trägt man danach von Hand ein."""
from app.domain.models import MAX_BUECHER, Feld, Vorlage

STANDARD_VORLAGE_ID = "lesenachweis-pflichtlektuere"


def _buch_felder() -> list[Feld]:
    row_top0, row_h = 474.7, 21.36
    page_h = 841.9
    felder = []
    for i in range(MAX_BUECHER):
        top = row_top0 + row_h * i
        y = round(page_h - (top + 14), 1)
        felder.append(Feld(schluessel=f"buch_{i}_titel", seite=0, x=64, y=y, groesse=10))
        felder.append(Feld(schluessel=f"buch_{i}_seiten", seite=0, x=468, y=y, groesse=10))
    return felder


def standard_vorlage() -> Vorlage:
    return Vorlage(
        id=STANDARD_VORLAGE_ID,
        name="Lesenachweis Pflichtlektüre",
        dateiname="lesenachweis_pflichtlektuere.pdf",
        felder=[
            Feld(schluessel="fach", seite=0, x=168, y=555.9),
            Feld(schluessel="name", seite=0, x=168, y=512.9),
            Feld(schluessel="gemeinde", seite=0, x=168, y=483.9),
            *_buch_felder(),
        ],
    )
