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
- Erweitern heißt: einen Dienst hinzufügen oder einen Dienst ändern, nie den Kern oder die Oberfläche anfassen müssen.
  Neue Dienste kommen aus `dienst-vorlage` (`./neuer-dienst.sh name "Anzeigename"`), melden sich selbst beim Kern an und
  erscheinen über ihr Manifest (Reiter per `panel`, Kachel per `status`).
- Daten bleiben erhalten: neue Felder mit `.get(..., Standard)` lesen, alte Felder nie ohne Migration umbenennen oder
  löschen, Speichern nur über `storage.py` (atomar + tägliche Sicherung in `backups/`).
- Backend: Python + FastAPI. Frontend: Vue 3 + Tailwind (Hell/Dunkel), spricht nur mit dem Kern (`/api`). Start: `docker compose up --build`.

## Stand
- [fertig] Karteikarten-Dienst (Fächer, Karten: Umdrehen, Multiple Choice, Richtig/Falsch, Fälligkeit, Webhook, Fach-Hooks)
- [fertig] Kern: zentrale Fächerverwaltung, Dienstverzeichnis (`SERVICES`), Weiterleitung `/api/<dienst>/…`, Statusübersicht, Abgleich
- [fertig] Lesenachweis-Dienst mit Prognose (Seiten/Kapitel, Durchgänge, Frist, Tempo der letzten 14 Tage)
- [fertig] Register-Dienst (Namen und Orte mit Bibelstellen, alphabetisch / Bibelreihenfolge / nach Stelle, Export CSV/Text, keine Notizen)
- [fertig] Plug-in-Mechanismus: Selbstanmeldung `POST /api/registry`, Manifest, Reiter/Kachel automatisch, `dienst-vorlage`, `neuer-dienst.sh`
- [fertig] Datensicherheit: atomares Schreiben, tägliche Sicherung, Übernahme vorhandener Karten als Fächer
- [fertig] Oberfläche: Start (Status je Fach), Fächer, Fach mit Reitern Karteikarten/Lesenachweis/Register, Alle Karten, Lernen
- [ungeprüft] Docker-Build, Oberfläche im Browser und die FastAPI-Schicht der Dienste wurden noch nicht ausgeführt
  (bisher nur Tests der Domäne und Anwendung, Syntaxprüfung). Erster Schritt beim Weiterarbeiten: `docker compose up --build` und alles durchklicken.

## Fach-Vertrag (jeder Dienst)
`GET /api/health` · `PUT /api/subjects/{id}` {name} · `DELETE /api/subjects/{id}` · `GET /api/subjects/{id}/status` ·
`GET /api/manifest` {name,label,panel,status:[{key,label}]} · optional `GET /api/subjects` (vorhandene Fächer, der Kern übernimmt sie).
Der Kern ruft ihn auf; die Fach-ID ist das Einzige, was Dienste teilen.

## Später
Lesenachweis als PDF ausfüllen (Vorlage nötig) · Aufgabenblatt, Skript und Fragen mit Ollama einlesen (Ollama läuft
direkt auf dem Mac, Container erreichen es über host.docker.internal:11434) ·
Auswendiglern-Modus.

## Entscheidungen
- Der Kern ist der einzige Eingang der Oberfläche; er reicht Aufrufe an die Dienste weiter.
- Tempo für die Prognose: Durchschnitt der letzten 14 Tage. „Knapp“ = Tempo unter 115 % des Bedarfs.
- Bibelbücher: 66, evangelische Reihenfolge, Kurznamen nach Lutherbibel; Bücher mit einem Kapitel (Obd, Phlm, 2Joh, 3Joh, Jud): „Jud 5“ = Vers 5.
- Löscht der Kern ein Fach, während ein Dienst offline ist, bleibt dessen Datenrest liegen und wird beim nächsten Abgleich als Fach zurückgeholt (lieber nichts verlieren).
- Fachnamen führt nur der Kern; Lesenachweis und Register kennen nur die Fach-ID.
- Leitner-Stufen: 0, 1, 2, 4, 8, 16 Tage. Falsche Karten sind sofort wieder fällig.
- Ergebnisse der KI sind immer nur Vorschläge, die der Nutzer prüft.
