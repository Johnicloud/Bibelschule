# Bibelschule

Studienplaner für viele Fächer. Eine Obersoftware (der **Kern**) verwaltet die Fächer, kleine **Dienste**
liefern ihre Funktionen dazu. Jedes Fach bekommt automatisch Karteikarten, Lesenachweis und Register.

| Ordner | Aufgabe |
|---|---|
| `kern/backend` | Fächer anlegen/umbenennen/löschen, Dienstverzeichnis, Statusübersicht, leitet `/api/<dienst>/…` weiter |
| `kern/frontend` | Die Oberfläche (Vue 3 + Tailwind, Hell/Dunkel) |
| `karteikarten` | Karteikarten: Umdrehen, Multiple Choice, Richtig/Falsch, Leitner-System |
| `lesenachweis` | Lesepensen mit Leseprotokoll, Durchgängen, Frist und **Prognose** |
| `register` | beliebig viele Register pro Fach (Namen, Orte, …) mit Bibelstellen, sortiert nach Alphabet, Bibelreihenfolge oder Stelle, exportierbar |
| `dienst-vorlage` | Vorlage für neue Dienste, benutzt von `./neuer-dienst.sh` |

## Start

    docker compose up --build

Dann http://localhost:8080 öffnen. Im Hintergrund: `docker compose up -d --build`, beenden: `docker compose down`.

## Deine Daten

- Alles liegt in `./data/` und überlebt Neustarts, Neubauen und Updates (`docker compose down` löscht nichts).
  Die Karteikarten bleiben wie in der alten App in `./data/decks.json`, der Rest in `./data/kern`, `./data/lesenachweis`,
  `./data/register` und `./data/<neuer dienst>`.
- Geschrieben wird atomar (erst Nebendatei, dann ersetzen), ein Absturz mitten im Speichern zerstört die Datei nicht.
- Vor dem ersten Speichern eines Tages kopiert jeder Dienst seine Datei nach `backups/` neben der Datei
  (Stand vom Vortag, die letzten 14 Tage bleiben). Zurückspielen = Datei aus `backups/` an die Stelle der Datei kopieren.
- Karten, die schon in `decks.json` liegen, werden beim Start als Fächer übernommen (gleiche ID, die Karten hängen dran).
- Wer einen Dienst erweitert, liest neue Felder mit Standardwert und benennt alte nie ohne Migration um (siehe `CLAUDE.md`).
- Das Löschen eines Fachs löscht seine Daten in allen Diensten. Wer eine Sicherung braucht, kopiert vorher `./data`.

## Neuen Dienst hinzufügen (nur der Dienst, sonst nichts)

    ./neuer-dienst.sh vokabeln "Vokabeln"
    docker compose up --build -d

Das Skript kopiert `dienst-vorlage/` nach `./vokabeln` und trägt den Dienst in `docker-compose.override.yml` ein
(wird von `docker compose` automatisch dazugelesen). Beim Start meldet sich der Dienst selbst beim Kern an, bekommt
alle Fächer und erscheint ohne Änderung an Kern oder Oberfläche:

- als **Reiter in jedem Fach**, wenn sein Manifest eine eigene Seite meldet (`"panel": "ui"`, die Seite `/api/ui` liefert er selbst),
- als **Kachel auf der Startseite** mit den Kennzahlen aus seinem Manifest (`"status"`),
- mit seiner API unter `/api/<name>/…`.

Die Vorlage ist ein kleines, lauffähiges Beispiel (Einträge pro Fach); ersetze `domain`, `application` und die
Seite `ui.html` durch deine Fachlogik. Einen bestehenden Dienst erweiterst du in seinem Ordner, der Rest merkt es
über das Manifest. Eingebaute Dienste (Karteikarten, Lesenachweis, Register) haben eine fest eingebaute Oberfläche.

## Lesenachweis: so rechnet die Prognose

- Ziel = Umfang × Durchgänge (z. B. 200 Seiten, 2 Durchgänge = 400 Seiten).
- Tempo = Durchschnitt der letzten 14 Tage (in den ersten Tagen nur über die Tage seit dem ersten Eintrag).
- Voraussichtlich fertig = heute + Rest ÷ Tempo. Nötig pro Tag = Rest ÷ Tage bis zur Frist.
- Status: *Im Plan*, *Knapp* (Tempo unter 115 % des Bedarfs), *Im Rückstand*, *Frist überschritten*,
  *Noch nicht begonnen*, *Ohne Frist*, *Fertig*.

## Register: Bibelstellen

Erkannt werden Kurzformen und ausgeschriebene Namen: `Joh 3,16`, `1. Mose 12,1-3`, `Ps 23`, `Mt 5-7`,
`Röm 8,28-9,5`, `1Kor 13,4f`, `Jud 5` (Bücher mit einem Kapitel). Mehrere Stellen trennst du mit Semikolon oder
Zeilenumbruch. 66 Bücher in evangelischer Reihenfolge, ohne Apokryphen. Gibt es den Namen im Register schon, kommen
die Stellen dazu. Es gibt keine Notizen.

**Mehrere Register:** Im Reiter Register stehen alle Register des Fachs nebeneinander (mit der Zahl ihrer Einträge).
Ein Klick springt hin, darunter trägst du sofort ein (Name, Stellen, Enter). „+ Neues Register“ legt ein weiteres an,
beliebig viele pro Fach. Umbenennen und Löschen stehen über dem Eintragsformular. Einträge aus der Zeit mit den
zwei festen Listen landen beim Start automatisch in den Registern „Namen“ und „Orte“.

**Export:** im Reiter Register die Knöpfe „Export CSV“ (Semikolon, öffnet in deutschem Excel mit Umlauten) und
„Export Text“. Exportiert wird das gewählte Register in der gewählten Sortierung. API: `GET /api/register/export?register_id=…&sort=name|bibel|stellen&format=csv|txt`.

## Fortschritt

**Lesestatus des Fachs:** oben im Reiter Lesenachweis. Prozent gelesen (jedes Pensum zählt gleich viel), fertige Pensen,
das dringendste offene Pensum und die nächste Frist.

**Gesamtfortschritt:** oben auf der Fachseite und auf der Startseite. Mittel aus allen Diensten, die einen Fortschritt melden:
Lesen (Prozent gelesen) und Karteikarten (Anteil „sicher gelernt“, Lernstufe 4 oder höher). Das Register zeigt nur Zahlen.
Ein neuer Dienst zählt mit, sobald sein Status ein `progress` (0 bis 100) enthält. API: `GET /api/subjects/{id}/overview`.

## Wie ein Dienst sich einhängt

Jeder Dienst ist ein eigener Ordner mit eigenem Dockerfile, eigenen Daten und einer REST-API unter `/api`
(interaktive Doku: `/api/docs`). Dazu erfüllt er diesen kleinen Vertrag, den der Kern aufruft:

    GET    /api/health                     lebt der Dienst?
    PUT    /api/subjects/{id}   {"name"}   Fach anlegen/umbenennen (Fach-ID kommt vom Kern)
    DELETE /api/subjects/{id}              alle Daten dieses Fachs löschen
    GET    /api/subjects/{id}/status       Kennzahlen des Fachs für die Startseite (JSON)
    GET    /api/manifest                   Steckbrief: name, label, panel (Seite für den Reiter oder null), status-Felder
    GET    /api/subjects                   (optional) vorhandene Fächer, die der Kern übernehmen darf

Neuer Dienst: siehe oben. Dienste teilen nur die Fach-ID, keine Datenbank. Ist ein Dienst beim Anlegen eines Fachs nicht
erreichbar, bleibt das Fach gespeichert; der Kern gleicht beim Start und bei „Dienste abgleichen“ (Startseite,
`POST /api/sync`) nach.

Optional meldet jeder Dienst Ereignisse (`card.reviewed`, `reading.logged`, `register.entry_added` …) per POST an
`EXTERNAL_SERVICE_URL` (siehe `.env.example`).

## Entwicklung ohne Docker

Jeder Dienst (auch `dienst-vorlage`): `cd <dienst> && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`,
Tests mit `pytest`, Start mit `uvicorn app.main:app --reload --port <port>`. Der Kern braucht
`SERVICES=karteikarten=http://localhost:8001,lesenachweis=http://localhost:8002,register=http://localhost:8003`
und läuft auf Port 8000. Oberfläche: `cd kern/frontend && npm install && npm run dev` (Port 5173).

## Hexagonale Struktur (jeder Dienst gleich)

    app/
      domain/        reine Regeln, kein Framework, kein Speicher
      application/   Anwendungsfälle + Ports (Repository, EventPublisher, im Kern ServiceGateway)
      adapters/
        inbound/     HTTP-API (FastAPI)
        outbound/    JSON-Datei, Webhook, im Kern HTTP zu den Diensten
      main.py        Kompositionswurzel

Abhängigkeiten zeigen nach innen. Eine andere Datenbank ist nur ein neuer Outbound-Adapter.
