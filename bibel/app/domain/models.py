"""Domäne: wo im hinterlegten Bibel-PDF ein Buch beginnt, die herausgelesenen Verse, und Verweise, die von
irgendwo in der App auf eine Bibelstelle (bis auf Wortebene) zeigen – die Bibel als Grundlage, an die sich
alles andere anknüpfen lässt (siehe Projektnotizen).

Nur Buch-genau gespeichert (66 Einträge), nicht Kapitel-genau (1189 Kapitel wären von Hand kaum zu pflegen).
Die Seite eines Kapitels wird daraus errechnet: gleichmäßig zwischen der Startseite dieses Buches und der
des nächsten verteilt, nach Kapitelanteil (`Buch.chapters`) – nicht exakt, aber nah dran, siehe Entscheidungen."""
import re
from dataclasses import dataclass, field
from uuid import uuid4


def new_id() -> str:
    return uuid4().hex


@dataclass
class Buchseite:
    """`seite` ist die 1-basierte Seite im PDF, an der dieses Buch beginnt (None = noch nicht bekannt).
    `erkannt` unterscheidet eine automatisch im Inhaltsverzeichnis gefundene Seite von einer von Hand
    eingetragenen – beide sind gleichwertig gültig, `erkannt` ist nur eine Anzeige-Information."""
    buch_index: int
    seite: int | None = None
    erkannt: bool = False


@dataclass
class Bibelindex:
    """Der ganze Bestand: die Datei selbst liegt separat (DateiSpeicher), hier nur die Seitenzuordnung."""
    buchseiten: list[Buchseite] = field(default_factory=list)
    dateiname: str | None = None

    def seite_von(self, buch_index: int) -> Buchseite | None:
        return next((b for b in self.buchseiten if b.buch_index == buch_index), None)


_WORT = re.compile(r"\S+")


def woerter(text: str) -> list[str]:
    """Zerlegt einen Verstext in Wörter (an Leerraum, Satzzeichen bleiben am Wort) – die Grundlage für die
    Wort-genaue Adresse (`Stelle.word`). Einfache, stabile Regel statt echter Sprachanalyse: dieselbe Zahl
    Wörter kommt bei jedem Aufruf heraus, auch nach erneutem Hochladen derselben Datei."""
    return _WORT.findall(text or "")


_SATZTRENNER = re.compile(r"(?<=[.!?])\s+")


def kontextsatz(text: str, suchwort: str) -> str:
    """Der Satz aus `text`, der `suchwort` enthält (Groß/Kleinschreibung egal) – der Zusammenhang für einen
    Konkordanz-Treffer (siehe `BibelService.suche`). Einfache Satztrennung an Punkt/Ausrufe-/Fragezeichen,
    keine echte Sprachanalyse; ohne erkennbare Satzgrenze (oder falls keiner der Sätze passt) der ganze Text."""
    saetze = _SATZTRENNER.split(text or "")
    nadel = suchwort.lower()
    treffer = next((s for s in saetze if nadel in s.lower()), None)
    return (treffer if treffer is not None else (text or "")).strip()


@dataclass
class Vers:
    """Ein einzelner Bibelvers, automatisch aus der hochgeladenen PDF herausgelesen (siehe verse_extractor.py).
    `id` ist die kanonische, stabile Adresse (`Stelle.format()`, z. B. „Joh.3.16“) – darüber verknüpft sich
    alles andere mit diesem Vers (siehe `Verweis`), nicht über die Datenbank-Reihenfolge.
    Kein Anspruch auf Perfektion: der erste (unnummerierte) Vers eines Kapitels landet beim Herauslesen manchmal
    am Ende des letzten Verses des vorigen Kapitels (siehe dortiger Modul-Docstring) – ein „Gerüst zum Prüfen
    und Nachbessern“, keine fertige, redaktionell geprüfte Bibelausgabe."""
    buch_index: int
    kapitel: int
    vers: int
    text: str
    id: str = ""

    def woerter(self) -> list[str]:
        return woerter(self.text)

    def wort(self, index: int) -> str | None:
        w = self.woerter()
        return w[index - 1] if 1 <= index <= len(w) else None


@dataclass
class Verweis:
    """Ein Verweis von irgendwo in der App auf eine Bibelstelle (Vers oder einzelnes Wort) – der generische
    Anknüpfungspunkt: `art` sagt, was für eine Art Verweis es ist (z. B. „register-eintrag“, „notiz“,
    „frage“, „wortstudie“ – offen für alles Künftige, keine feste Liste), `referenz` ist frei (eine ID oder
    Kurzbeschreibung des verweisenden Dings, dieser Dienst kennt die anderen Dienste nicht), `titel` eine
    kurze, für Menschen lesbare Beschriftung."""
    stelle: str   # Stelle.format(), z. B. "Joh.3.16" oder "Joh.3.16.5"
    art: str
    referenz: str
    titel: str | None = None
    id: str = field(default_factory=new_id)
