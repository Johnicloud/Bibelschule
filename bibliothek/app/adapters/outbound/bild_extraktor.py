"""Ausgehender Adapter: zerlegt eine PDF in ein Bild je Seite. Ein gescanntes Buch ist praktisch immer genau
das – eine eingebettete Bild-Datei pro Seite –, darum reicht das Auslesen der eingebetteten Bilder (pypdf),
ohne die Seite selbst neu zu rendern (kein Poppler/PyMuPDF als zusätzliche Abhängigkeit nötig)."""
import io

from pypdf import PdfReader

from app.application.ports import BildExtraktor


class PypdfBildExtraktor(BildExtraktor):
    def seiten_bilder(self, pdf: bytes) -> list[bytes]:
        reader = PdfReader(io.BytesIO(pdf))
        bilder = []
        for seite in reader.pages:
            bilder_der_seite = list(seite.images)
            if not bilder_der_seite:
                bilder.append(b"")   # keine Bild-Seite (z. B. schon Text) – nichts zu erkennen
                continue
            # Das größte Bild der Seite ist fast immer die eigentliche Scan-Seite (kleinere sind oft Logos o. ä.).
            groesstes = max(bilder_der_seite, key=lambda b: len(b.data))
            bilder.append(groesstes.data)
        return bilder
