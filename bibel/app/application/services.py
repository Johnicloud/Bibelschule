"""Anwendungsfälle. Kennen nur Domäne und Ports."""
from app.application.ports import (DateiSpeicher, IndexRepository, PdfText, VersRepository, VerseExtractor,
                                   VerweisRepository)
from app.domain.bible import BOOKS, Stelle, find_book, parse_ref, parse_stelle
from app.domain.errors import InvalidInput, NotFound
from app.domain.models import Bibelindex, Buchseite, Vers, Verweis


class BibelService:
    def __init__(self, index_repo: IndexRepository, dateien: DateiSpeicher, text: PdfText,
                 verse_repo: VersRepository | None = None, extractor: VerseExtractor | None = None,
                 verweis_repo: VerweisRepository | None = None):
        self.index_repo = index_repo
        self.dateien = dateien
        self.text = text
        self.verse_repo = verse_repo
        self.extractor = extractor
        self.verweis_repo = verweis_repo

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
                stelle_id = Stelle(buchseite.buch_index, kapitel, vers_nr).format()
                verse.append(Vers(buch_index=buchseite.buch_index, kapitel=kapitel, vers=vers_nr, text=vers_text,
                                  id=stelle_id))
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

    def nachschlagen(self, text: str) -> dict:
        """Löst eine frei eingegebene Bibelstelle ('Joh 3,16') zum Lesen auf: das ganze Kapitel mit Verstext
        (siehe `kapitel`), dazu `markiert` – der angefragte Vers zum Hervorheben in der Oberfläche, None wenn
        nur das Kapitel genannt wurde. Zeigt den Text selbst, keine PDF-Seite (siehe `stelle`, das weiterhin
        für den Seiten-Link aus dem Register gebraucht wird)."""
        ref = parse_ref(text)
        ergebnis = self.kapitel(BOOKS[ref.book].short, ref.chapter)
        ergebnis["markiert"] = ref.verse
        return ergebnis

    def kapitel(self, buch_kurz: str, kapitel: int) -> dict:
        """Der Verstext eines Kapitels, falls schon herausgelesen (siehe `hochladen`)."""
        buch = find_book(buch_kurz)
        if buch is None:
            raise InvalidInput(f"Das Bibelbuch „{buch_kurz}“ kenne ich nicht.")
        if not 1 <= kapitel <= buch.chapters:
            raise InvalidInput(f"{buch.name} hat nur {buch.chapters} Kapitel.")
        verse = self.verse_repo.kapitel(buch.index, kapitel) if self.verse_repo else []
        return {"buch": buch.short, "name": buch.name, "kapitel": kapitel, "kapitel_gesamt": buch.chapters,
                "verse": [{"id": v.id, "vers": v.vers, "text": v.text} for v in verse]}

    MAX_TREFFER = 100

    def suche(self, text: str) -> list[dict]:
        """Volltextsuche über alle herausgelesenen Verse: findet jeden Vers, dessen Text `text` enthält
        (Groß/Kleinschreibung egal), sortiert in Bibelreihenfolge. Keine Bibelstelle wie bei `stelle` – hier
        wird nach Inhalt gesucht, nicht nach Fundort."""
        text = (text or "").strip()
        if len(text) < 2:
            raise InvalidInput("Bitte mindestens 2 Zeichen eingeben.")
        if self.verse_repo is None:
            return []
        treffer = sorted(self.verse_repo.suche(text), key=lambda v: (v.buch_index, v.kapitel, v.vers))
        return [{"id": v.id, "buch": BOOKS[v.buch_index].short, "name": BOOKS[v.buch_index].name,
                 "kapitel": v.kapitel, "vers": v.vers, "text": v.text} for v in treffer[:self.MAX_TREFFER]]

    def wort(self, stelle_text: str) -> dict:
        """Löst eine Wort-genaue Stelle ('Joh.3.16.5') zum einzelnen Wort auf, samt dem ganzen Vers als
        Zusammenhang. Ohne Wort-Teil ('Joh.3.16') ist das Ergebnis derselbe Vers, nur ohne `wort`."""
        stelle = parse_stelle(stelle_text)
        if self.verse_repo is None:
            raise NotFound("Es sind noch keine Verse eingelesen.")
        vers = self.verse_repo.vers(stelle.book, stelle.chapter, stelle.verse)
        if vers is None:
            raise NotFound(f"Für {stelle.format()} ist noch kein Vers eingelesen.")
        wort_text = None
        if stelle.word is not None:
            wort_text = vers.wort(stelle.word)
            if wort_text is None:
                raise InvalidInput(f"{vers.id} hat nur {len(vers.woerter())} Wörter.")
        return {"stelle": stelle.format(), "vers_id": vers.id, "vers_text": vers.text, "wort": wort_text}

    # Verweise: irgendetwas in der App zeigt auf eine Bibelstelle (Vers oder Wort) – der generische
    # Anknüpfungspunkt, siehe domain/models.py.
    def verweis_anlegen(self, stelle_text: str, art: str, referenz: str, titel: str | None) -> Verweis:
        if self.verweis_repo is None:
            raise InvalidInput("Verweise sind gerade nicht verfügbar.")
        stelle = parse_stelle(stelle_text)   # wirft InvalidInput, wenn die Stelle nicht stimmt
        if not (art or "").strip():
            raise InvalidInput("Die Art des Verweises darf nicht leer sein.")
        if not (referenz or "").strip():
            raise InvalidInput("Die Referenz darf nicht leer sein.")
        verweis = Verweis(stelle=stelle.format(), art=art.strip(), referenz=referenz.strip(),
                          titel=(titel or "").strip() or None)
        self.verweis_repo.speichere(verweis)
        return verweis

    def verweise_zu(self, stelle_text: str) -> list[Verweis]:
        if self.verweis_repo is None:
            return []
        stelle = parse_stelle(stelle_text)
        return self.verweis_repo.zu_stelle(stelle.format())

    def verweis_loeschen(self, verweis_id: str) -> None:
        if self.verweis_repo is not None:
            self.verweis_repo.loesche(verweis_id)

    def _naechste_startseite(self, idx: Bibelindex, buch_index: int) -> int | None:
        for i in range(buch_index + 1, len(BOOKS)):
            b = idx.seite_von(i)
            if b and b.seite is not None:
                return b.seite
        return None
