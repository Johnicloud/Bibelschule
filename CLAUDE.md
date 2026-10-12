# Bibelschule: Projektnotizen

Diese Datei ist das Gedächtnis des Projekts. Wer an dem Code weiterarbeitet (Mensch oder Claude),
liest sie zuerst und aktualisiert sie nach jeder größeren Änderung.

## Ziel
Studienplaner für viele Fächer mit gleichem Aufbau (Aufgabenblatt, Lesenachweis, Karteikarten).
Obersoftware "Bibelschule" mit kleinen Services, die ihre Dienste an die große Software übergeben.
Sprache der Oberfläche und der Texte: Deutsch.

## Regeln
- Hexagonal: `domain` kennt nichts, `application` kennt nur Domäne und Ports, Adapter kennen die Anwendung.
- Jeder Dienst ist ein eigener Ordner mit eigenem Dockerfile, eigenen Daten und eigener API unter `/api`.
- Dienste teilen nur die Fach-ID, keine Datenbank.
- Ereignisse an andere Dienste laufen über den Port `EventPublisher`.
- Neue Funktion = zuerst Anwendungsfall und Test, dann Adapter, dann Oberfläche.
- Backend: Python + FastAPI. Frontend: Vue 3 + Tailwind (Hell/Dunkel). Start: `docker compose up --build`.

## Stand
- [fertig] Karteikarten-Dienst (Fächer, Karten: Umdrehen, Multiple Choice, Richtig/Falsch, Fälligkeit, Startseite, Webhook)
- [offen] Kern "Bibelschule": zentrale Fächerverwaltung, Dienstverzeichnis; Karteikarten hängen sich per Fach-ID ein
- [offen] Lesenachweis-Dienst mit Prognose (Seiten und Kapitel, Durchgänge, Frist)
- [offen] Register-Dienst (Namen und Orte mit Bibelstellen, sortiert nach Name und Bibelreihenfolge)

## Später
Lesenachweis als PDF ausfüllen · Aufgabenblatt, Skript und Fragen mit Ollama einlesen (Ollama läuft
direkt auf dem Mac, Container erreichen es über host.docker.internal:11434) · Status-Dashboard ·
Auswendiglern-Modus.

## Entscheidungen
- Leitner-Stufen: 0, 1, 2, 4, 8, 16 Tage. Falsche Karten sind sofort wieder fällig.
- Ergebnisse der KI sind immer nur Vorschläge, die der Nutzer prüft.
