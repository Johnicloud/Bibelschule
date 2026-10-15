"""Domäne: wo im hinterlegten Bibel-PDF ein Buch beginnt.

Nur Buch-genau gespeichert (66 Einträge), nicht Kapitel-genau (1189 Kapitel wären von Hand kaum zu pflegen).
Die Seite eines Kapitels wird daraus errechnet: gleichmäßig zwischen der Startseite dieses Buches und der
des nächsten verteilt, nach Kapitelanteil (`Buch.chapters`) – nicht exakt, aber nah dran, siehe Entscheidungen."""
from dataclasses import dataclass, field


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


@dataclass
class Vers:
    """Ein einzelner Bibelvers, automatisch aus der hochgeladenen PDF herausgelesen (siehe verse_extractor.py).
    Kein Anspruch auf Perfektion: der erste (unnummerierte) Vers eines Kapitels landet beim Herauslesen manchmal
    am Ende des letzten Verses des vorigen Kapitels (siehe dortiger Modul-Docstring) – ein „Gerüst zum Prüfen
    und Nachbessern“, keine fertige, redaktionell geprüfte Bibelausgabe."""
    buch_index: int
    kapitel: int
    vers: int
    text: str
