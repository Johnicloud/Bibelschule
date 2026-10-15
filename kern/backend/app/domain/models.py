"""Domäne des Kerns: ein Fach mit seinen Aufgaben. Die Fach-ID ist das Einzige, was alle Dienste teilen."""
from dataclasses import dataclass, field
from uuid import uuid4


def new_id() -> str:
    return uuid4().hex


@dataclass
class Aufgabe:
    """Eine Aufgabe umreißt den Umfang eines Fachs (Zeile im Aufgabenblatt der Dozentin).
    gewichtung = anteilige Bewertung in Prozent, wie im Aufgabenblatt (z. B. Klausur 50 %).
    pensum_id: optional, verknüpft die Aufgabe mit einem Pensum des Lesenachweis-Diensts (z. B. „Lesen der
    Pflicht-Lektüre + Lesenachweis“) – die Übersicht zeigt dann dessen echten Lesestatus statt eines Häkchens."""
    titel: str
    frist: str | None = None
    gewichtung: float | None = None
    erledigt: bool = False
    pensum_id: str | None = None
    id: str = field(default_factory=new_id)


@dataclass
class Subject:
    name: str
    id: str = field(default_factory=new_id)
    aufgaben: list[Aufgabe] = field(default_factory=list)
    se: float | None = None   # Studieneinheiten (alt); Credits = se * 1.5 (neues System, wird nicht gespeichert)
    note: float | None = None   # Abschlussnote des Fachs, deutsche Notenskala 1,0 (sehr gut) bis 5,0 (nicht ausreichend)
    # Optionale Dienste (Register/Karteikarten/Bibelverse/Skripte), die für dieses Fach eingeblendet wurden –
    # ohne das hier zu stehen, erscheinen sie weder als Reiter noch als Kachel in der Übersicht (Aufgaben und
    # Lesenachweis sind fest, kein Fach ohne die beiden).
    aktive_dienste: list[str] = field(default_factory=list)


@dataclass
class Account:
    """Ein Konto. Alle Konten sehen dieselben Fächer (gemeinsames Lernen) – das Konto regelt nur den Zugang,
    keine Datentrennung. Konten legt man per Skript an oder, einmal angemeldet, als Admin über die Oberfläche.
    is_admin = darf neue Konten (auch neue Admins) anlegen und die Benutzerliste sehen.
    vorname/nachname/gemeinde sind optional (z. B. für den Lesenachweis-PDF-Export: Name und Gemeinde kommen
    von dort, statt bei jedem Export neu eingetippt zu werden).
    muss_passwort_aendern: ein Admin hat das Passwort zurückgesetzt – das Konto darf sich mit dem neuen
    (temporären) Passwort anmelden, muss aber vor allem anderen ein eigenes neues Passwort wählen. Wird beim
    Zurücksetzen gesetzt und beim nächsten eigenen Passwortwechsel wieder gelöscht."""
    username: str
    password_hash: str
    is_admin: bool = False
    vorname: str | None = None
    nachname: str | None = None
    gemeinde: str | None = None
    muss_passwort_aendern: bool = False
    id: str = field(default_factory=new_id)
