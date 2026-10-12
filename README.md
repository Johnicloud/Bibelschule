# Bibelschule

Studienplaner für viele Fächer. Eine Obersoftware (der **Kern**) verwaltet die Fächer, kleine **Dienste**
liefern ihre Funktionen dazu. Jedes Fach bekommt automatisch Karteikarten, Lesenachweis und Register.

| Ordner | Aufgabe |
|---|---|
| `kern/backend` | Fächer anlegen/umbenennen/löschen, Dienstverzeichnis, Statusübersicht, leitet `/api/<dienst>/…` weiter |
| `kern/frontend` | Die Oberfläche (Vue 3 + Tailwind, Hell/Dunkel) |
| `karteikarten` | Karteikarten: Umdrehen, Multiple Choice, Richtig/Falsch, Leitner-System |
| `lesenachweis` | Lesepensen mit Leseprotokoll, Durchgängen, Frist und **Prognose** |
| `register` | Namen und Orte mit Bibelstellen, sortiert nach Alphabet, Bibelreihenfolge oder Stelle |

## Start

    docker compose up --build

Dann http://localhost:8080 öffnen. Die Daten liegen in `./data/<dienst>/` und bleiben beim Neustart erhalten.
Im Hintergrund: `docker compose up -d --build`, beenden: `docker compose down`.

**Alte Karteikarten-App:** Karten aus einer früheren `decks.json` tauchen in der Bibelschule nicht automatisch
unter einem Fach auf, denn Fächer kommen jetzt vom Kern. Ein Import ist noch offen.

## Lesenachweis: so rechnet die Prognose

- Ziel = Umfang × Durchgänge (z. B. 200 Seiten, 2 Durchgänge = 400 Seiten).
- Tempo = Durchschnitt der letzten 14 Tage (in den ersten Tagen nur über die Tage seit dem ersten Eintrag).
- Voraussichtlich fertig = heute + Rest ÷ Tempo. Nötig pro Tag = Rest ÷ Tage bis zur Frist.
- Status: *Im Plan*, *Knapp* (Tempo unter 115 % des Bedarfs), *Im Rückstand*, *Frist überschritten*,
  *Noch nicht begonnen*, *Ohne Frist*, *Fertig*.

## Register: Bibelstellen

Erkannt werden Kurzformen und ausgeschriebene Namen: `Joh 3,16`, `1. Mose 12,1-3`, `Ps 23`, `Mt 5-7`,
`Röm 8,28-9,5`, `1Kor 13,4f`, `Jud 5` (Bücher mit einem Kapitel). Mehrere Stellen trennst du mit Semikolon oder
Zeilenumbruch. 66 Bücher in evangelischer Reihenfolge, ohne Apokryphen. Gibt es den Namen im Fach schon, kommen
die Stellen dazu.

## Wie ein Dienst sich einhängt

Jeder Dienst ist ein eigener Ordner mit eigenem Dockerfile, eigenen Daten und einer REST-API unter `/api`
(interaktive Doku: `/api/docs`). Dazu erfüllt er diesen kleinen Vertrag, den der Kern aufruft:

    GET    /api/health                     lebt der Dienst?
    PUT    /api/subjects/{id}   {"name"}   Fach anlegen/umbenennen (Fach-ID kommt vom Kern)
    DELETE /api/subjects/{id}              alle Daten dieses Fachs löschen
    GET    /api/subjects/{id}/status       Kennzahlen des Fachs für die Startseite (JSON)

Neuer Dienst: Ordner anlegen, in `docker-compose.yml` einen Service hinzufügen und in `SERVICES` des Kerns
eintragen (`name=http://name:8000`). Die Oberfläche erreicht ihn dann unter `/api/name/…`. Dienste teilen nur die
Fach-ID, keine Datenbank. Ist ein Dienst beim Anlegen eines Fachs nicht erreichbar, bleibt das Fach gespeichert;
der Kern gleicht beim Start und bei „Dienste abgleichen“ (Startseite, `POST /api/sync`) nach.

Optional meldet jeder Dienst Ereignisse (`card.reviewed`, `reading.logged`, `register.entry_added` …) per POST an
`EXTERNAL_SERVICE_URL` (siehe `.env.example`).

## Entwicklung ohne Docker

Jeder Dienst: `cd <dienst> && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`,
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
