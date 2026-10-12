# Karteikarten

Fächer anlegen, darin Karteikarten erstellen und mit dem Leitner-System lernen.
Backend: Python (FastAPI) · Frontend: Vue 3 + Tailwind (Vite) · Aufbau: hexagonale Architektur.

## Funktionen

- Startseite mit Zahlen, allen Fächern und allen Karten (Suche, Filter nach Fach, Typ, fällig)
- Drei Kartentypen: Umdrehen, Multiple Choice (4 Antworten), Richtig/Falsch
- Fälligkeit: richtig beantwortete Karten kommen nach 1, 2, 4, 8, 16 Tagen wieder, falsche sofort
  (in der Lernrunde werden sie am Ende nochmal gestellt)
- Hell/Dunkel-Umschalter (merkt sich die Wahl, folgt sonst dem System)

## Mit Docker (z. B. auf dem MacBook)

    docker compose up --build

Dann http://localhost:8080 öffnen. Die Karten liegen in `./data/decks.json`.
Im Hintergrund: `docker compose up -d --build`, beenden: `docker compose down`.

## Schnittstelle zu einem übergeordneten Service

- Eingehend: die REST-API unter `/api` mit interaktiver Doku auf http://localhost:8080/api/docs
  (Schema: `/api/openapi.json`). Ein anderer Service kann Fächer und Karten anlegen, fällige Karten holen
  und Antworten melden.
- Ausgehend: setze `EXTERNAL_SERVICE_URL` (und optional `EXTERNAL_SERVICE_TOKEN`), zum Beispiel in einer
  `.env` neben der `docker-compose.yml` (Vorlage: `.env.example`). Dann bekommt diese URL jedes Ereignis
  per POST als JSON: `deck.created`, `deck.deleted`, `card.created`, `card.deleted`, `card.reviewed`.

      {"event": "card.reviewed", "occurred_at": "...", "data": {"deck_id": "...", "correct": true, "box": 2}}

## Ohne Docker (Entwicklung)

    cd backend && python -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt && uvicorn app.main:app --reload     # Port 8000, Tests: pytest
    cd frontend && npm install && npm run dev                            # Port 5173

## Hexagonale Struktur

    backend/app/
      domain/        Card, Deck, Kartentypen, Lernregeln (kein Framework, kein Speicher)
      application/   Anwendungsfälle (FlashcardService) + Ports DeckRepository, EventPublisher
      adapters/
        inbound/     HTTP-API (FastAPI)
        outbound/    JsonDeckRepository, WebhookPublisher / NullPublisher
      main.py        Kompositionswurzel

    frontend/src/
      domain/        Kartentypen, Fälligkeitstexte
      application/   flashcardService.js
      adapters/      httpApi.js
      components/    ui/ (Header, Badges, Statistik) und cards/ (FlashCard, ChoiceCard, CardForm, CardItem)
      views/         Start, Fächer, Fach, Lernen

Abhängigkeiten zeigen nach innen. Eine andere Datenbank oder ein anderer externer Service
ist nur ein neuer Outbound-Adapter.
