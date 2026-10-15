"""Anwendungsfälle. Kennen nur Domäne und Ports."""
from app.application.ports import DateiSpeicher, IndexRepository, PdfText, VersRepository, VerseExtractor
from app.domain.bible import BOOKS, find_book, parse_ref
from app.domain.errors import InvalidInput, NotFound
from app.domain.models import Bibelindex, Buchseite, Vers


class BibelService:
    def __init__(self, index_repo: IndexRepository, dateien: DateiSpeicher, text: PdfText,
                 verse_repo: VersRepository | None = None, extractor: VerseExtractor | None = None):
        self.index_repo = index_repo
        self.dateien = dateien
        self.text = text
        self.verse_repo = verse_repo
        self.extractor = extractor

    def index(self) -> Bibelindex:
        gespeichert = self.index_repo.get()
        if gespeichert is None:
            return Bibelindex(buchseiten=[Buchseite(buch_index=i) for i in range(len(BOOKS))])
        # Fehlende Bücher ergänzen (z. B. nach Erweiterung der Buchliste) – nie welche verlieren.
        vorhanden = {b.buch_index for b in gespeichert.buchseiten}
        gespeichert.buchseiten += [Buchseite(buch_index=i) for i in range(len(BOOKS)) if i not in vorhanden]
        return gespeichert

    def hochladen(self, dateiname: str, inhalt: bytes) -> Bibelindex:
        """Speichert die Datei und erkennt die Buch-Seiten (einige Sekunden). Das Herauslesen der Verse selbst
        dauert bei einer ganzen Bibel 1-2 Minuten – zu lang für eine Antwort auf diesen Aufruf (Proxy-Timeouts).
        Der Adapter (api.py) stößt `verse_im_hintergrund_einlesen` darum separat an, nicht blockierend."""
        if not inhalt:
            raise InvalidInput("Die Datei ist leer.")
        erkannt = self.text.buchseiten_erkennen(inhalt)
        index = Bibelindex(
            buchseiten=[Buchseite(buch_index=i, seite=erkannt.get(i), erkannt=i in erkannt) for i in range(len(BOOKS))],
            dateiname=dateiname)
        self.index_repo.save(index)
        self.dateien.speichere(inhalt)
        return index

    def verse_im_hintergrund_einlesen(self) -> None:
        """Liest die Verse aus der zuletzt hochgeladenen Datei heraus und speichert sie. Für den Hintergrund-
        Thread gedacht (siehe `hochladen`) – läuft über die gespeicherte Datei und den gespeicherten Index,
        nicht über frisch hochgeladene Bytes, damit der Aufrufer nichts durchreichen muss."""
        if self.extractor is None or self.verse_repo is None:
            return
        inhalt = self.dateien.lies()
        if inhalt is None:
            return
        self.verse_repo.ersetze_alle(self._alle_verse_lesen(inhalt, self.index()))

    def _alle_verse_lesen(self, inhalt: bytes, index: Bibelindex) -> list[Vers]:
        """Baut das ganze Bibel-Gerüst mit Versen – nur für Bücher, deren Startseite bekannt ist (siehe
        `buchseiten_erkennen`); ohne Seite kein Buchbereich, also kein Versuch. Vorschlag zum Prüfen und
        Nachbessern, siehe verse_extractor.py."""
        verse: list[Vers] = []
        for buchseite in sorted(index.buchseiten, key=lambda b: b.buch_index):
            if buchseite.seite is None:
                continue
            bis = self._naechste_startseite(index, buchseite.buch_index)
            ende = (bis - 1) if bis is not None else None
            for kapitel, vers_nr, vers_text in self.extractor.buch_verse(inhalt, buchseite.seite, ende):
                verse.append(Vers(buch_index=buchseite.buch_index, kapitel=kapitel, vers=vers_nr, text=vers_text))
        return verse

    def seite_setzen(self, buch_index: int, seite: int | None) -> Bibelindex:
        if not 0 <= buch_index < len(BOOKS):
            raise InvalidInput("Dieses Buch kenne ich nicht.")
        if seite is not None and seite < 1:
            raise InvalidInput("Die Seite beginnt bei 1.")
        idx = self.index()
        bestehend = idx.seite_von(buch_index)
        bestehend.seite, bestehend.erkannt = seite, False
        self.index_repo.save(idx)
        return idx

    def datei(self) -> bytes | None:
        return self.dateien.lies()

    def hat_verse(self) -> bool:
        return self.verse_repo.hat_verse() if self.verse_repo else False

    def stelle(self, text: str) -> dict:
        """Löst eine Bibelstelle (z. B. 'Joh 3,16') zur Seite im hinterlegten PDF auf. Kapitel 1 eines Buches
        liegt genau auf dessen Startseite (`genau`); alle anderen Kapitel sind proportional zwischen dieser
        und der Startseite des nächsten Buches verteilt – nah dran, aber kein Versprechen auf die exakte
        Seite (siehe Entscheidungen)."""
        ref = parse_ref(text)
        buch = BOOKS[ref.book]
        idx = self.index()
        start = idx.seite_von(ref.book)
        if start is None or start.seite is None:
            raise NotFound(f"Für {buch.name} ist noch keine Seite hinterlegt.")
        seite = start.seite
        genau = ref.chapter == 1
        if not genau:
            naechste = self._naechste_startseite(idx, ref.book)
            if naechste is not None and buch.chapters > 1:
                anteil = (ref.chapter - 1) / buch.chapters
                seite = start.seite + round(anteil * (naechste - start.seite))
        return {"buch": buch.short, "name": buch.name, "kapitel": ref.chapter, "seite": seite, "genau": genau}

    def kapitel(self, buch_kurz: str, kapitel: int) -> dict:
        """Der Verstext eines Kapitels, falls schon herausgelesen (siehe `hochladen`)."""
        buch = find_book(buch_kurz)
        if buch is None:
            raise InvalidInput(f"Das Bibelbuch „{buch_kurz}“ kenne ich nicht.")
        if not 1 <= kapitel <= buch.chapters:
            raise InvalidInput(f"{buch.name} hat nur {buch.chapters} Kapitel.")
        verse = self.verse_repo.kapitel(buch.index, kapitel) if self.verse_repo else []
        return {"buch": buch.short, "name": buch.name, "kapitel": kapitel, "kapitel_gesamt": buch.chapters,
                "verse": [{"vers": v.vers, "text": v.text} for v in verse]}

    def _naechste_startseite(self, idx: Bibelindex, buch_index: int) -> int | None:
        for i in range(buch_index + 1, len(BOOKS)):
            b = idx.seite_von(i)
            if b and b.seite is not None:
                return b.seite
        return None
