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
- Backend: Python + FastAPI. Frontend: Vue 3 + Tailwind (Hell/Dunkel), spricht nur mit dem Kern (`/api`). Start: `docker compose up --build` -> http://localhost:8170.

## Stand
- [fertig] Karteikarten-Dienst (Fächer, Karten: Umdrehen, Multiple Choice, Richtig/Falsch, Fälligkeit, Webhook, Fach-Hooks)
- [fertig] Kern: zentrale Fächerverwaltung, Dienstverzeichnis (`SERVICES`), Weiterleitung `/api/<dienst>/…`, Statusübersicht, Abgleich
- [fertig] Lesenachweis-Dienst mit Prognose (Seiten/Kapitel, Durchgänge, Frist, Tempo der letzten 14 Tage)
- [fertig] Register-Dienst: beliebig viele Register pro Fach (z. B. Namen, Orte, Völker), Einträge mit Bibelstellen, alphabetisch / Bibelreihenfolge / nach Stelle,
  Export CSV/Text je Register. Alte Namen/Orte wandern beim Start automatisch in die Register „Namen“ und „Orte“ (`migrate_legacy`).
  Oberfläche: alle Register als Reiter nebeneinander, Klick springt hin, Eintragsformular sofort darunter (Fokus bleibt im Namensfeld)
- [fertig] Lesestatus des Fachs (Kopf des Reiters Lesenachweis) und Gesamtfortschritt je Fach (Kopf der Fachseite und Startseite)
- [fertig] Plug-in-Mechanismus: Selbstanmeldung `POST /api/registry`, Manifest, Reiter/Kachel automatisch, `dienst-vorlage`, `neuer-dienst.sh`
- [fertig] Datensicherheit: atomares Schreiben, tägliche Sicherung, Übernahme vorhandener Karten als Fächer
- [fertig] Oberfläche: Start (Status je Fach), Fächer, Fach mit Reitern Aufgaben/Karteikarten/Lesenachweis/Register, Alle Karten, Lernen
- [fertig] Docker-Build, Oberfläche im Browser und die FastAPI-Schicht der Dienste geprüft (`docker compose up --build`, durchgeklickt).
- [fertig] Aufgaben als Umfang eines Fachs: Teil des Kerns (nicht eigener Dienst), Titel + optionale Frist + erledigt.
  Beim Fach-Anlegen gleich die ersten Aufgaben eintragbar, danach im Reiter „Aufgaben“ verwaltbar (hinzufügen, abhaken, löschen).
  Zählt wie ein Dienst zum Gesamtfortschritt (Anteil erledigter Aufgaben).
- [fertig] Frontend-Standard für neue Dienste: `/ui-kit.css` + `/ui-kit.js` (ausgeliefert vom Kern-Frontend unter `kern/frontend/public/`).
  `dienst-vorlage/app/adapters/inbound/ui.html` bindet beide mit absolutem Pfad ein (funktioniert auch im Reiter-iframe, da alles
  unter einem Origin läuft). So bringt jeder neue Dienst nur noch Inhalt mit, nicht eigenes CSS/JS für Knopf, Eingabefeld, Liste.
- [fertig] SE/Credits am Fach: `se` (Studieneinheiten, altes System) ist ein Feld am Fach im Kern; Credits = se * 1.5
  (neues System) wird live berechnet (`GET /api/subjects/{id}` liefert `se` und `credits`), nicht gespeichert.
  Eintragbar beim Fach-Anlegen und danach per Klick auf die SE-Anzeige im Fach-Kopf.
- [fertig] Adressbuch-Dienst: Dozenten (Name, E-Mail, Telefon, Notiz), beliebig vielen Fächern zuordenbar (eigene
  Zuordnungsliste je Dozent, nicht über die Fach-ID hinaus geteilt). Löscht der Kern ein Fach, verschwindet nur die
  Zuordnung, der Dozent bleibt. „Mail vorbereiten“ öffnet einen mailto-Link (Betreff = Fachname, geholt per
  Browser-Fetch direkt vom Kern) – nichts wird automatisch verschickt.
- [fertig] Skripte-Dienst: Dateien (PDF u. a.) je Fach hochladen (multipart, max. 50 MB), Angaben in `skripte.json`,
  Inhalt in `data/skripte/dateien/<id>` (beides über `storage.py`, der Inhalt ohne tägliche Sicherung). Direkt im
  Reiter lesbar (Inline-iframe-Vorschau über `/datei`, `Content-Disposition: inline`) und herunterladbar.
- [fertig] Bibelverse-Dienst: Verse mit Bibelstelle + Text, `subject_id = null` heißt „allgemein“ (kein Fach).
  Gleiches Leitner-System wie Karteikarten (Stufen/Logik 1:1 übernommen). Lernen im Fach-Reiter zeigt die fälligen
  Verse des Fachs UND die allgemeinen zusammen. Zwei Lernmodi: Aufdecken (wie Karteikarten) und „Anfangsbuchstaben“
  (nur Anfangsbuchstaben jedes Wortes eintippen, sofortiger Abgleich rein im Browser, kein Server-Aufruf nötig).
- [fertig] Adresse-Feld für Dozenten (Adressbuch), nützlich für die Brief-Option im echten Aufgabenblatt.
- [fertig] Dozenten direkt beim Fach-Anlegen auswählbar: die Oberfläche lädt die Dozentenliste vom Adressbuch-Dienst
  und ordnet die gewählten nach dem Anlegen zu (`POST /api/adressbuch/dozenten/{id}/faecher/{subjectId}`). Reine
  Frontend-Orchestrierung über die bestehende `/api/<dienst>/…`-Weiterleitung, der Kern weiß nichts von Dozenten.
- [fertig] Credits direkt am Fach eingebbar: zweites Eingabefeld neben SE im Anlege-Formular, beide halten sich im
  Formular gegenseitig synchron (Credits = SE × 1,5); gespeichert wird weiterhin nur `se` im Kern (eine Quelle der Wahrheit).
- [fertig] Starttermin beim Lesepensum: `start`-Feld (optional). Daraus berechnet die Prognose `plan_per_day`
  (Umfang gleichmäßig von Start bis Frist verteilt) – zusätzlich zu `needed_per_day` (Rest ab heute) und
  `pace_per_day` (bisheriges Tempo). Zeigt von Tag eins an ein sinnvolles Tagesziel, auch bevor gelesen wurde.

## Fach-Vertrag (jeder Dienst)
`GET /api/health` · `PUT /api/subjects/{id}` {name} · `DELETE /api/subjects/{id}` · `GET /api/subjects/{id}/status` (darf `progress` 0 bis 100 oder null enthalten) ·
`GET /api/manifest` {name,label,panel,status:[{key,label}]} · optional `GET /api/subjects` (vorhandene Fächer, der Kern übernimmt sie).
Der Kern ruft ihn auf; die Fach-ID ist das Einzige, was Dienste teilen.

## Später
Lesenachweis als PDF ausfüllen (Vorlage nötig) · Aufgabenblatt, Skript und Fragen mit Ollama einlesen (Ollama läuft
direkt auf dem Mac, Container erreichen es über host.docker.internal:11434; Ergebnisse immer nur Vorschlag, siehe
Entscheidungen) · Priorisierung (Eisenhower: dringend/wichtig) als eigener Dienst für Aufgaben ·
Kalender-Dienst (Aufgabe, Soll, Ist) · Bulk-Import der 50 Fächer aus dem Studienablaufplan (SE, Dozent, Semester;
noch nicht gemacht, Foto kann Lesefehler enthalten – Kontrollliste nötig) · evtl. Fristen-Erinnerung über alle
Fächer, Volltextsuche, Notizen/Logbuch.

## Entscheidungen
- Der Kern ist der einzige Eingang der Oberfläche; er reicht Aufrufe an die Dienste weiter.
- Tempo für die Prognose: Durchschnitt der letzten 14 Tage. „Knapp“ = Tempo unter 115 % des Bedarfs.
- Bibelbücher: 66, evangelische Reihenfolge, Kurznamen nach Lutherbibel; Bücher mit einem Kapitel (Obd, Phlm, 2Joh, 3Joh, Jud): „Jud 5“ = Vers 5.
- Löscht der Kern ein Fach, während ein Dienst offline ist, bleibt dessen Datenrest liegen und wird beim nächsten Abgleich als Fach zurückgeholt (lieber nichts verlieren).
- Fachnamen führt nur der Kern; Lesenachweis und Register kennen nur die Fach-ID.
- Gesamtfortschritt eines Fachs = Mittel der `progress`-Werte aller erreichbaren Dienste, die einen melden (`GET /api/subjects/{id}/overview`, `parts` zeigt die Teile).
  Neue Dienste zählen automatisch mit. Das Register meldet keinen (es hat kein Ziel), zeigt nur Zahlen.
- Lesen: Prozent des Fachs = Mittel der Prozentwerte der Pensen (jedes Pensum gleich viel, Seiten und Kapitel lassen sich nicht addieren).
- Karteikarten: Fortschritt = Anteil der Karten auf Lernstufe 4 oder höher („sicher gelernt“, Wiederholung nach 8 Tagen oder mehr).
- Register: Name im Register eindeutig (Groß/Klein egal), gleicher Name in einem anderen Register bleibt getrennt; gleicher Name im selben Register ergänzt die Stellen.
  Dateien: `register.json` (Einträge, JSON-Feld `kind` bleibt für alte Daten erhalten) und `registers.json` (Register).
- Leitner-Stufen: 0, 1, 2, 4, 8, 16 Tage. Falsche Karten sind sofort wieder fällig.
- Ergebnisse der KI sind immer nur Vorschläge, die der Nutzer prüft.
- Aufgaben (Umfang eines Fachs) liegen bewusst im Kern, nicht in einem eigenen Dienst: sie gehören zum Fach selbst
  (wie der Name), nicht zu einem bestimmten Lernweg. Das Domänenmodell des Kerns wächst dadurch mit; das ist hier
  gewollt, abweichend von der sonstigen Regel „Erweitern = Dienst, nie Kern“.
- Neue Dienste (aus `dienst-vorlage`) binden ihre eigene Oberfläche nicht mehr mit eigenem CSS/JS, sondern über
  `/ui-kit.css` und `/ui-kit.js` vom Kern-Frontend. Absoluter Pfad genügt, weil Oberfläche und alle Dienste hinter
  einem Nginx-Origin liegen (auch im Reiter-iframe). Folgt die Seite nicht dem Hell/Dunkel-Umschalter der App
  (nur `prefers-color-scheme`), weil der iframe ein eigenes Dokument ist.
- Eigene Oberfläche eines Dienstes (`ui.html`) ruft ihre eigene API immer relativ OHNE führenden Schrägstrich auf
  (z. B. `call('GET', 'dozenten')`, nicht `/api/dozenten`), weil die Seite selbst unter `/api/<dienst>/ui` hängt und
  der Kern `/api/<dienst>/<rest>` an den Dienst weiterreicht. Ein führender `/api/...`-Pfad träfe stattdessen den
  Kern direkt (nur für Kern-eigene Routen wie `/api/subjects/{id}` richtig, nie für die eigenen Routen des Dienstes).
- Falle beim Schreiben von Ports/Repositories: eine Methode `list(...)` im selben Klassenkörper VOR einer späteren
  Methode mit Rückgabetyp `list[Etwas]` lässt Python beim Import abstürzen ("'function' object is not subscriptable"),
  weil der Name `list` in der Klasse da schon die Methode meint, nicht mehr den eingebauten Typ. Abhilfe: ganz oben
  `from __future__ import annotations`. Tests, die nur mit einem In-Memory-Repo laufen, decken das nicht auf – erst
  der echte Import (z. B. `app/main.py`, Docker-Start) merkt es.
- Datei-Uploads (FastAPI `UploadFile`) brauchen `python-multipart` in `requirements.txt`, sonst startet der Dienst
  nicht; einfache Formularfelder neben `UploadFile` müssen explizit `= Form(...)` sein, sonst hält FastAPI sie für
  Query-Parameter.
- Der Kern reicht beim Weiterleiten (`/api/<dienst>/...`) nur `content-type` durch, keine weiteren Antwort-Header
  (z. B. `Content-Disposition` geht verloren). Für Dateinamen beim Herunterladen das `download`-Attribut des
  `<a>`-Tags nutzen, nicht auf den Header verlassen.
