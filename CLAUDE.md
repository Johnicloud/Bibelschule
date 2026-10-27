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
- [fertig] Tagesziel-Hinweis im Lesenachweis: Banner „Heute noch nicht gelesen – Ziel: X“ (aus `needed_per_day`,
  sonst `plan_per_day`), solange heute noch kein Eintrag für das Pensum da ist. Reine Anzeige, kein neuer Datensatz.
- [fertig] Lesepensum aus mehreren Büchern: optionale `buecher`-Liste (Titel + eigener Umfang je Buch), `total`
  wird dann automatisch als Summe gesetzt (wie „Pflicht-Lektüre 600 Seiten“ aus mehreren Titeln im Aufgabenblatt).
  Ohne Bücherliste bleibt der einfache einzelne Umfang wie bisher.
- [fertig] Login: Konten per Skript (`./neues-konto.sh "Name" "Passwort"`) oder, einmal angemeldet, über die
  Oberfläche (Profilseite „Konto“, Klick auf den eigenen Namen) – keine Selbstregistrierung ohne Anmeldung.
  Alle Konten sehen dieselben Fächer (gemeinsames Lernen) – das Konto regelt nur den Zugang, keine Datentrennung,
  kein Dienst musste dafür geändert werden. Sitzung über httpOnly-Cookie, Passwort als PBKDF2-Hash (stdlib,
  keine neue Abhängigkeit). Der Kern prüft bei jedem `/api/…`-Aufruf außer `/api/health`, `/api/registry`
  (Selbstanmeldung der Dienste, interner Docker-Verkehr) und `/api/login`; schützt damit automatisch auch jeden
  weitergereichten Dienst, da die Oberfläche nur über den Kern spricht. Sitzungen liegen nur im Speicher
  (Neustart des Kerns meldet alle ab) – bewusst so, keine Sitzungsdatei, die man stehlen könnte.
  Eigenes Passwort ändern: `PUT /api/me/password` (altes + neues Passwort), Profilseite.
- [fertig] Fach bearbeiten (nicht nur bei der Anlage): auf der Fachseite „Bearbeiten“ öffnet ein Formular mit
  Name, SE/Credits (synchron wie beim Anlegen) und Dozenten (Mehrfachauswahl, gleicht beim Speichern per
  Zuordnen/Entfernen mit dem Adressbuch ab). Ersetzt die alten einzelnen `prompt()`-Dialoge für Umbenennen/SE.
  Dozentenauswahl steht jetzt auch beim Anlegen direkt neben SE/Credits, nicht mehr darunter.
- [fertig] Admin-Konten: `is_admin`-Feld am Konto. Nur Admins dürfen `/api/accounts` (Liste, Anlegen) nutzen,
  sonst 403. `./neues-konto.sh` legt immer Admins an (wer Shell-Zugriff auf den Container hat, hat ohnehin
  vollen Zugriff); weitere, auch nicht-Admin-Konten legt ein Admin über die Oberfläche an. Bestehendes
  erstes Konto wurde einmalig von Hand in `accounts.json` auf `is_admin: true` gesetzt (keine Migration nötig,
  neue Konten tragen das Feld von Anfang an; alte ohne das Feld gelten als `false`, siehe `.get(..., False)`).
- [fertig] Automatische Abmeldung nach Inaktivität (wie bei einer Finanz-App), zweistufig:
  Server (`MemorySessionStore`, `IDLE_TIMEOUT = 15 min`): jede Sitzung hat ein gleitendes Zeitfenster – jeder
  erfolgreiche Aufruf schiebt die Frist weiter, ohne Aufruf länger als 15 Minuten gilt sie als abgelaufen.
  Frontend (`App.vue`): eigener 15-Minuten-Inaktivitätstimer (Maus/Tastatur/Touch/Scroll setzt ihn zurück)
  meldet zusätzlich sofort lokal ab, ohne auf einen fehlgeschlagenen Serveraufruf warten zu müssen.
- [fertig] Oberfläche im Finanzapp-Stil: ein rundes Benutzer-Symbol (Personen-Silhouette, `AccountMenu.vue`)
  oben rechts bündelt Hell/Dunkel, „Konto“ (Profilseite) und „Abmelden“ statt einzelner Knöpfe nebeneinander.
  Navigation: „Start“ ist kein eigener Reiter mehr (nur noch per Logo-Klick erreichbar), „Adressbuch“ ist jetzt
  ein globaler Reiter (`AdressbuchView.vue`: alle Dozenten anlegen/löschen, unabhängig vom Fach; Zuordnung zu
  einem Fach bleibt Sache des jeweiligen Fachs). Passwort-Formulare verlangen das neue Passwort zweimal.

- [fertig] PDF-Vorlagen-Dienst (`pdfcreator`): füllt PDF-Formulare serverseitig aus (reportlab-Overlay + pypdf-Merge,
  keine KI nötig für das Ausfüllen selbst). Mitgeliefert: „Lesenachweis Pflichtlektüre“ (BEE-Formular) mit von Hand
  vermessenen Feldpositionen (`domain/standard_vorlage.py`), Platz für 6 Bücher (Titel+Seiten je Zeile).
  Fachübergreifend (kein `panel`, keine Fach-Daten) – trotzdem mit den drei Pflicht-Endpunkten des Fach-Vertrags,
  damit der Kern beim Abgleich keine Ausnahme braucht.
  Neue Vorlage hochladen (`POST /api/vorlagen`, multipart): bekommt noch keine Feldpositionen (die trägt man von
  Hand in `vorlagen.json` ein), aber einen KI-Vorschlag von Ollama, welche Angaben im Formular vorkommen – reiner
  Lesetext zur Orientierung, keine automatische Positionierung (siehe Entscheidungen: Ergebnisse der KI sind
  Vorschläge). Ollama läuft nicht in diesem Compose-Stack, sondern lokal auf dem Mac; Adresse über `OLLAMA_URL`
  (Default `http://host.docker.internal:11434`, siehe `.env.example`), 180 Sekunden Zeitlimit (lokale Modelle
  brauchen länger als eine Cloud-API). Ohne `OLLAMA_URL` oder bei Netzwerkfehler gibt es einfach keinen Vorschlag
  (`NullTextKI` bzw. abgefangener Fehler), der Upload selbst schlägt nie deswegen fehl.

- [fertig] Bibelverse ausgearbeitet: Vers bearbeiten (`PUT /api/verse/{id}`, ändert Bibelstelle/Text/Zuordnung
  Fach↔allgemein, lässt Lernstufe und Fälligkeit unangetastet – Bearbeiten ist kein Lernerfolg). Oberfläche zeigt
  jetzt je Vers die Leitner-Stufe („neu“, „Stufe n (x Tage)“, „sicher gelernt“ ab Stufe 4) und das Fälligkeitsdatum,
  dazu oben im Fach-Reiter einen Fortschritts-Satz „X von Y Versen dieses Fachs sicher gelernt“.

- [fertig] Oberfläche im Design der Finanzapp (`/Users/admin/finanzapp`, Vorbild begutachtet: `main.css`,
  `knoepfe.css`, `seiten.css`, `AppRoot.vue`/`HaushaltsbuchNavigation.vue`): Farben als CSS-Variablen
  (`--color-primary`, `-primary-darker`, `-theme`, `-theme-inv`, `-backdrop`, `-highlight`, `-link`, `-error`,
  `-success`) in `style.css`, per `.dark`-Klasse umgeschaltet (nicht `prefers-color-scheme`) – `useTheme.js`
  schaltet weiter nur die Klasse, der Rest folgt automatisch. `tailwind.config.js` bindet sie als Farben ein
  (`bg-primary`, `text-theme-inv`, …), nur Bibelschule bleibt beim Teal-Markenton statt dem Blau der Finanzapp.
  `.panel`/`.btn`/`.input` in `style.css` sind jetzt zentral über diese Tokens definiert (wie `seiten-karte`/
  `schaltflaeche` dort): Knöpfe heben beim Hover leicht ab (`hover:-translate-y-0.5`) statt nur die Farbe zu
  wechseln, Primär-Knopf mit farbigem Schatten. `AppHeader.vue`: Kopfleiste in Primärfarbe (wie `.app-header`
  dort) statt neutralem Grau, Navigation als Pillen-Leiste (aktiver Reiter = weiße Pille), „Start“-Logo links.
  `AccountMenu.vue` entsprechend angepasst (weißes Icon auf der farbigen Leiste). Nur die gemeinsamen
  Bausteine wurden umgestellt, nicht jede Seite einzeln nachgezogen – Status-Badges u. Ä. mit eigenen Farben
  (rose/amber/violet) blieben unverändert, das UI-Kit der Plugin-Dienste (`/ui-kit.css`) ebenfalls (eigenes,
  bewusst minimales System, siehe oben). Tailwind v3 (nicht v4 wie bei der Finanzapp): keine `@theme`-Direktive,
  Variablen normal in `:root`/`.dark` definiert und über `theme.extend.colors` eingebunden; Opacity-Modifier auf
  diesen Custom-Properties (`text-theme-inv/70`) schlagen in v3 fehl, stattdessen eine `opacity-*`-Utility nehmen.

- [fertig] Fach-Status (5 Stufen): `angelegt` · `begonnen` · `in_arbeit` · `klausur_offen` („Nur Klausur fehlt“) ·
  `abgeschlossen`. Automatisch aus dem Gesamtfortschritt hergeleitet (`SubjectService._fach_status`, Kern),
  keine eigene Pflege nötig. Sonderfall: ist nur noch eine Aufgabe offen, deren Titel „Klausur“ enthält, zeigt
  das Fach `klausur_offen` statt der reinen Prozent-Stufe. Der Schlüssel kommt als `stufe` in `/overview` und
  `/subjects/{id}/overview` mit; Anzeige/Label/Farbe stehen im Frontend (`domain/status.js`, `FACH_STATUS`),
  wie beim Lesestatus des Lesenachweis-Dienstes.
- [fertig] Dienst `aufgabenleser`: liest ein hochgeladenes Aufgabenblatt (PDF, `POST /api/lesen`) und lässt
  Ollama daraus eine Liste von Aufgaben vorschlagen (`titel`, `frist`, `gewichtung`) – reiner Lesetext-zu-JSON-
  Vorschlag, legt nie selbst etwas an (siehe Entscheidungen: Ergebnisse der KI sind immer nur Vorschläge).
  Fachübergreifend wie `pdfcreator` (kein `panel`, keine eigenen Fach-Daten, nur die drei Pflicht-Endpunkte).
  PDF-Text über `pypdf` (wie bei `pdfcreator`), gleicher `OLLAMA_URL`/`OLLAMA_MODEL`-Mechanismus. Ohne
  `OLLAMA_URL` liefert `/api/lesen` 422 (anders als bei `pdfcreator`: hier ist die KI der ganze Zweck des
  Diensts, kein optionaler Zusatz). Oberfläche: im Fach-Reiter „Aufgaben“ lädt man die PDF hoch, bekommt eine
  Liste mit Kontrollkästchen (alle vorausgewählt), wählt ab/zu und legt die ausgewählten per Klick als echte
  Aufgaben über die bestehende Aufgaben-API des Kerns an; die rohe KI-Antwort bleibt in einem Klapptext
  sichtbar, auch wenn sich daraus kein gültiges JSON gewinnen ließ. `pdfcreator` bleibt für den umgekehrten Weg
  (Vorlage ausfüllen/exportieren) zuständig – zwei getrennte Dienste für Lesen und Schreiben von PDFs.

- [fertig] Oberfläche weiter an die Finanzapp angeglichen und mit durchgängigen Symbolen versehen:
  - Aktiver Reiter hatte bisher einen weißen Hintergrund auf der farbigen Kopfleiste (kaum lesbar). Die Reiter
    stehen jetzt in `AppNav.vue`, einer eigenen Pillen-Leiste unterhalb der Kopfleiste (wie Übersicht/Planung bei
    der Finanzapp auf dem Desktop), aktiver Reiter mit `bg-primary text-white`. `AppHeader.vue` zeigt nur noch
    Logo und Benutzer-Symbol.
  - Alle Symbole zentral in `components/ui/AppIcon.vue` (ein `name`, ein Satz Strichpfade) statt verstreuter
    Inline-SVGs – neue Symbole kommen nur noch dort hinzu.
  - Hell/Dunkel als Kippschalter (`ThemeSwitch.vue`, Sonne/Mond im Knopf) im Benutzermenü statt Textzeile, wie
    `ThemeToggle.vue` der Finanzapp.
  - „Lernen“ ist kein eigener Reiter mehr, sondern ein Schnellzugriff unten rechts (`StudyFab.vue`, rund, fest),
    wie die Schnellerfassung der Finanzapp.
  - Dienste-Übersicht (online/offline, „Dienste abgleichen“) zog von der Startseite in die Konto-Seite
    (`ProfileView.vue`, Abschnitt „Dienste“) – dort, wo auch die Benutzerverwaltung ist.
  - Fach-Kacheln auf der Startseite zeigen nur noch Name, Status-Badge (siehe unten) und Gesamtfortschritt;
    das Aufschlüsseln nach Dienst gehört in die Reiter der Fach-Seite (dafür sind sie da), nicht in die Kachel.
    Eine „+ Neues Fach“-Kachel öffnet das Anlage-Formular inline, genau wie „Neuen Benutzer anlegen“ auf der
    Konto-Seite ein Formular öffnet – das Formular selbst (`SubjectCreateForm.vue`) ist jetzt eine gemeinsame
    Komponente für Startseite und Fächer-Seite, keine doppelte Logik mehr.
  - Fach umbenennen/bearbeiten hat jetzt ein Stift-Symbol statt eines Text-Knopfes (Fächer-Liste und Fach-Kopf).
  - Dozenten-Auswahl (beim Fach anlegen und beim Fach bearbeiten) ist ein Dropdown (`DozentenAuswahl.vue`,
    Knopf mit Auswahl-Text, Häkchen-Liste darunter) statt einer offenen Checkbox-Reihe.
  - Reiter innerhalb eines Fachs (`SubjectView.vue`) zeigen jetzt auch Symbole, aktive Markierung über
    `border-primary text-primary` (Token-Farbe) statt hartem `teal-600`.

- [fertig] Lesenachweis weiter ausgearbeitet: Leseeintrag ohne Notiz-Feld (Angabe war unnötig, Backend-Feld
  `note` bleibt für alte Daten erhalten, wird nur nicht mehr befüllt). „Neues Lesepensum“ steht jetzt hinter
  einem Knopf („+ Neues Pensum“) statt dauerhaft offen zu sein. Pensum bearbeiten (`PUT /api/lesenachweis/
  tasks/{id}`, `ReadingService.update_task`): Stift-Symbol wie beim Fach öffnet ein Formular mit denselben
  Feldern wie beim Anlegen (Titel, Umfang/Einheit oder Bücherliste, Durchgänge, Start, Frist); Leseprotokoll
  bleibt beim Bearbeiten unangetastet.

- [fertig] Anfangsbuchstaben-Modus bei Bibelverse: Prüfung läuft jetzt bei jedem Tastendruck (kein „Prüfen“-Knopf
  mehr). Erster falscher Buchstabe -> sofort als falsch bewertet (`POST .../review {correct:false}`, einmalig),
  Verstext zur Kontrolle gezeigt, Eingabe geleert zum Wiederholen; erst wenn der Vers danach richtig getippt
  wird, geht es automatisch zum nächsten fälligen Vers weiter (ohne erneute Bewertung). Vollständig richtig beim
  ersten Versuch -> sofort als richtig bewertet, kurze Bestätigung, automatisch weiter. Vorher musste man extra
  auf „Prüfen“ und danach auf „Weiter“ klicken.

- [fertig] Lesenachweis weiter ausgearbeitet:
  - Pensen-Kacheln im Fach-Reiter jetzt wie die Fächer-Kacheln der Startseite angeordnet: zweispaltiges Grid,
    „+ Neues Pensum“ als eigene Kachel am Ende, Anlege-/Export-Formular als Panel oberhalb statt dauerhaft offen.
  - Buchbezogene Seiten: bei Pensen aus mehreren Büchern lässt sich jeder Leseeintrag einem Buch zuordnen
    (`buch_id` an `ReadingEntry`, `ReadingTask.buch_done()`). Eintragsformular zeigt dann eine Buchauswahl,
    die Büchliste je Pensum zeigt „gelesen/gesamt“ pro Buch.
  - PDF-Export über den bestehenden `pdfcreator`-Dienst (Vorlage „Lesenachweis Pflichtlektüre“): Knopf „Als PDF
    exportieren“ sowohl je einzelnem Pensum (dessen eigene Bücher) als auch für das ganze Fach (alle Bücher aller
    Pensen zusammen, max. 6 Zeilen wie die Vorlage). Fragt nur Name/Gemeinde ab, Fach kommt vom Fach selbst. Reine
    Frontend-Orchestrierung (`pdfcreatorService.js` ruft `/api/pdfcreator/vorlagen/{id}/fuellen` auf, liefert ein
    PDF-Blob statt JSON – eigener Adapter ohne den gemeinsamen `createCall`, siehe `adapters/http.js`).

- [fertig] Ollama-Aufgabenvorschläge erkennen Lesepensen: ein Vorschlag mit Mengenangabe im Titel (z. B.
  „Pflicht-Lektüre 600 Seiten“, Muster `/(\d+)\s*(seiten|kapitel)/i`) wird im Aufgaben-Reiter als eigene Gruppe
  „Lesepensen“ angezeigt (von den echten „Aufgaben“ getrennt) und beim Übernehmen automatisch als Lesenachweis-
  Pensum angelegt (`reading.add(...)`) statt als Aufgabe. Reine Heuristik im Frontend (`AufgabenPanel.vue`) – der
  `aufgabenleser`-Dienst selbst kennt den Lesenachweis nicht und bleibt bei reinen Titel/Frist/Gewichtung-Vorschlägen.

- [fertig] Register-Export reparierte: Die Knöpfe „Export CSV“/„Export Text“ im Register-Reiter waren schon da,
  liefen aber als einfache `<a href download>`-Links – bei abgelaufener Sitzung lud der Browser dadurch die
  JSON-Fehlermeldung (`{"detail":"Bitte anmelden."}`) als vermeintliche CSV-Datei herunter, ohne dass das auffiel.
  Jetzt wie der PDF-Export über `pdfcreator` (Vorbild `pdfcreatorService.js`): `registerApi.exportieren()` holt die
  Datei per `fetch` als Blob, bei 401 greift dieselbe Weiche wie bei jedem anderen Aufruf (`loggedIn.value = false`,
  zurück zur Anmeldeseite) statt einer kaputten Datei; echte Fehler zeigt eine Zeile unter den Export-Knöpfen.

- [fertig] Eigenes Profil: `Account` (Kern) hat jetzt `vorname`/`nachname`/`gemeinde` (optional, `None`-Default,
  wie bei `is_admin` ohne Migration – alte Konten lesen einfach `None`). `PUT /api/me` (`AuthService.update_profile`)
  speichert sie, `GET /api/me` und `POST /api/login` liefern sie mit. Konto-Seite hat dafür einen neuen Abschnitt
  „Profil“ oberhalb von „Passwort ändern“. Zweck: der Lesenachweis-PDF-Export (`ReadingPanel.vue`/`TaskCard.vue`)
  füllt Name und Gemeinde jetzt aus diesen Profilwerten vor (`state/auth.js`: `vorname`/`nachname`/`gemeinde`,
  gesetzt beim Login und bei `/me`), bleibt aber ein normales, überschreibbares Eingabefeld – kein Pflichtfeld,
  kein Zwang zum Pflegen des Profils. Nebenbei behoben: `authService.createAccount(...)` nahm das dritte Argument
  (`is_admin`) entgegen, reichte es aber nie an die API weiter – das Admin-Kästchen beim Benutzer-Anlegen wirkte
  dadurch nie.
- [fertig] Lesenachweis-PDF-Export füllt jetzt die TATSÄCHLICH gelesene Menge je Buch/Pensum (`b.done` bzw.
  `forecast.done`, aus dem bereits vorhandenen `buch_done()`/`Forecast.done` der Lesenachweis-Domäne), nicht mehr
  den geplanten/maximalen Umfang (`b.total`/`t.total`). Reiner Frontend-Fix (`ReadingPanel.vue`, `TaskCard.vue`),
  die Backend-Daten dafür gab es schon.

- [fertig] Adressbuch: Adresse jetzt in getrennten Feldern statt einer Freitextzeile – `strasse`/`plz`/`ort` am
  `Dozent` (Kern-Regel „alte Felder nie ohne Migration umbenennen/löschen“: das alte `adresse`-Feld bleibt für
  bestehende Daten erhalten, neue Dozenten füllen nur noch die drei neuen Felder). Anzeige bevorzugt die neuen
  Felder, fällt für ältere Dozenten auf `adresse` zurück (`anschrift()` in `AdressbuchView.vue`).
  Dozent-anlegen-Formular ist jetzt wie bei Fächern/Pensen hinter einem Knopf („+ Neuer Dozent“), dazu eine
  „+“-Kachel am Ende der Liste.
- [fertig] „Neuer Eintrag“-Formulare vereinheitlicht: Aufgaben (`AufgabenPanel.vue`) und Karteikarten
  (`DeckPanel.vue`) öffnen ihr Anlege-Formular jetzt ebenfalls über einen Knopf („+ Neue Aufgabe“/„+ Neue Karte“)
  statt es dauerhaft zu zeigen, wie bei Fächern/Pensen/Dozenten. Ausnahme bewusst: das Eintragsformular im
  Register (`RegisterPanel.vue`) bleibt dauerhaft offen – dort ist das Absicht (siehe Register-Eintrag oben,
  „Fokus bleibt im Namensfeld“), ein Knopf würde das schnelle Nacheinander-Eintragen nur erschweren.

- [fertig] Neue Symbole für Adressbuch (schon vorhanden, nur noch nicht verdrahtet), Bibelverse (Lesezeichen)
  und Skripte (Dokument) in `AppIcon.vue`. Navigation jetzt überall reine Symbole ohne Text, Name per
  `title`/`aria-label` (Tooltip beim Hovern, weiterhin per Tastatur/Screenreader erreichbar): die globale
  Pillen-Leiste (`AppNav.vue`) und die Reiter innerhalb eines Fachs (`SubjectView.vue`, `TAB_ICONS` um
  `adressbuch`/`bibelverse`/`skripte` ergänzt, vorher fielen die drei auf das Baustein-Symbol zurück).

- [fertig] Fach-Kopf aufgeräumt: `ProgressPanel.vue` zeigt nur noch die Gesamtfortschritt-Zahl mit Balken,
  nicht mehr dauerhaft die Aufschlüsselung je Dienst darunter (war zu viel auf einmal direkt unter dem Titel).
  Die Aufschlüsselung gibt es jetzt als eigener, erster Reiter „Übersicht“ (`SubjectOverview.vue`, Raster-Symbol):
  je Dienst eine klickbare Kachel mit Fortschritt/Kurztext, ein Klick springt in den jeweiligen Reiter
  (`@go` → `update:tab`). Alle Stellen, die ein Fach öffnen, springen jetzt auf `uebersicht` statt `aufgaben`
  (`App.vue`, `HomeView.vue`, `SubjectsView.vue` über `App.vue`). `TAB_ICONS` zog dafür von `SubjectView.vue`
  nach `domain/status.js` (eine Stelle für beide Komponenten, die Reiter-Symbole brauchen).

- [fertig] Lesenachweis-Pensum-Kachel (`TaskCard.vue`) minimalisiert: auf einen Blick nur noch Titel, Status-
  Badge, Frist und – falls heute noch nichts gelesen – das Tagesziel als eine Zahl, dazu ein schlichter
  Fortschrittsbalken ohne Text. Der ausführliche Prognose-Satz („Zurzeit X Seiten pro Tag, nötig sind Y …“) und
  die Start/Plan-Angaben in der Kopfzeile fielen weg. Bücher-Aufschlüsselung, Eintragen-Formular, Leseprotokoll
  und die Knöpfe (PDF-Export/Löschen) blieben wie gewohnt sichtbar, auf expliziten Wunsch so entschieden
  (Auswahl per Nachfrage, nicht geraten).
- [fertig] Fach-Kopf weiter überarbeitet: Name, Status-Badge, SE/Credits und Gesamtfortschritt (samt Balken)
  stehen jetzt in einer gemeinsamen Kachel (`ProgressPanel.vue` hat keinen eigenen Kachel-Rahmen mehr, lebt in
  der Kachel von `SubjectView.vue`). „Zurück zu den Fächern“ ist kein Text-Knopf mehr auf der Seite, sondern ein
  Pfeil-Symbol neben dem „Bibelschule“-Logo in der Kopfleiste (`AppHeader.vue`, neue Props `zurueck`/`@back`,
  nur sichtbar während man in einem Fach ist). Die Reiter-Leiste darunter ist jetzt so breit wie die Kachel
  darüber (Pillen-Leiste wie `AppNav.vue`, Reiter teilen sich die Breite gleichmäßig auf, `flex-1`) statt eines
  schmalen Unterstrich-Streifens, Symbole entsprechend größer (`h-6 w-6` statt `h-5 w-5`).

- [fertig] Optionale Dienste und Übersicht aus Aufgaben: `Subject.aktive_dienste` (Kern) listet, welche der
  optionalen Dienste (Register/Karteikarten/Bibelverse/Skripte, siehe `OPTIONAL_SERVICES` in `domain/status.js`)
  für ein Fach eingeblendet sind – ohne Eintrag dort gibt es weder einen Reiter noch eine Kachel dafür. Aufgaben
  und Lesenachweis sind fest, immer da. `PUT /api/subjects/{id}/dienste` setzt die Liste; die Übersicht
  (`SubjectOverview.vue`) zeigt für inaktive optionale Dienste eine „+ hinzufügen“-Kachel, die den Dienst
  freischaltet und sofort dorthin springt. Adressbuch erscheint hier absichtlich nie.
  Die Übersicht besteht jetzt in erster Linie aus den Aufgaben (dem Umfang des Fachs) als Kacheln: ein
  „Erledigt“/„Offen“-Feld, oder – ist die Aufgabe mit einem Lesenachweis-Pensum verknüpft (neues Feld
  `Aufgabe.pensum_id`, in `AufgabenPanel.vue` je Aufgabe per Dropdown wählbar) – der echte Lesestatus
  („Im Rückstand“ usw.) dieses Pensums statt eines einfachen Häkchens. `PUT /api/subjects/{id}/aufgaben/
  {aufgabe_id}/pensum` setzt/löst die Verknüpfung.
- [fertig] Fach-Kopf weiter minimalisiert: Titel größer, SE/Credits und der Status-Chip sind weg, nur noch ein
  schlichter Farbbalken (Farbe nach Fach-Status, Breite nach Gesamtfortschritt) – auf ausdrückliche Nachfrage so
  entschieden, nicht geraten. Die Reiter-Leiste zeigt entsprechend nur noch Übersicht/Aufgaben/Lesenachweis plus
  die aktivierten optionalen Dienste, auch hier mit größeren Symbolen; die obere App-Navigation (`AppNav.vue`)
  bekam ebenfalls größere Symbole.
- [fertig] Register-Export (CSV/Text) lässt die Register-Spalte weg, wenn ein einzelnes, schon gefiltertes
  Register exportiert wird (wie es die Oberfläche immer tut) – vorher stand in jeder Zeile derselbe Register-
  Name noch einmal. Nur beim (bisher nicht über die Oberfläche erreichbaren) Export über alle Register eines
  Fachs hinweg bleibt die Spalte zur Unterscheidung nötig (`entries_table(..., mit_register=register_id is None)`).

- [fertig] Fach-Kopf: Status-Chip und Prozentzahl stehen jetzt doch wieder neben dem Titel (nur der Farbbalken
  allein war zu wenig), SE/Credits bleiben aber weg. Aufgaben-Erledigt ist jetzt ein runder Haken-Knopf
  (`AppIcon name="haken"`, gefüllt/teal wenn erledigt, nur Umriss wenn offen) statt einer schlichten Checkbox.
  „PDF auswählen“ (Aufgabenblatt einlesen) steht als Knopf direkt neben „+ Neue Aufgabe“ im Kopf von „Umfang
  dieses Fachs“, die frühere eigene Einleitungsbox mit Erklärungstext fiel weg.
- [fertig] Workflow-Wechsel (auf Wunsch): Änderungen an diesem Projekt laufen ab jetzt über einen eigenen
  Branch + Pull Request + Review, nicht mehr direkt auf `main`. `gh` (GitHub-CLI) wurde dafür installiert.

- [fertig] Pensum-Kachel (`TaskCard.vue`) weiter ausgearbeitet: Eintragen-Formular zeigt den Buchnamen jetzt
  komplett (statt abgeschnitten), Seiten-Feld dafür schmaler, Datum nur noch ein Kalender-Symbol (öffnet den
  nativen Datumswähler über `showPicker()`), Eintragen ein Haken-Symbol statt Textknopf. Kopf zeigt nur noch
  Status (Frist fiel weg). Die reine „aus: Buch (x/y), …“-Textzeile ist jetzt je Buch eine eigene, schlichte
  Statusleiste mit Seitenzahl darüber; Einträge ohne Buch-Zuordnung (z. B. aus der Zeit vor einer Aufteilung in
  mehrere Bücher) laufen nicht mehr spurlos in den Gesamtfortschritt ein, sondern erscheinen sichtbar als „Ohne
  Buch zugeordnet“ mit ihrer Menge.

- [fertig] Bug behoben: `buch_id` eines Leseeintrags ging beim Speichern verloren (`JsonReadingRepository._to_dict`/
  `_from_dict` kannten das Feld nicht, obwohl Domäne/API es längst hatten) – ein Eintrag landete nach dem
  nächsten Laden immer bei „ohne Buch zugeordnet“, egal welches Buch beim Eintragen gewählt wurde. Dazu als
  Absicherung in `TaskCard.vue`: die Buch-Auswahl hat keine stille Vorauswahl mehr („Buch wählen“ als
  Pflicht-Option), Eintragen ohne gewähltes Buch wird jetzt abgelehnt statt stillschweigend ohne Zuordnung
  gespeichert zu werden. Neuer Regressionstest `lesenachweis/tests/test_json_repository.py` (Speichern + Laden
  mit `buch_id`, bisher gab es keinen Test fürs Repository selbst, nur mit einem In-Memory-Fake).

- [fertig] Lesenachweis: mehrere Durchgänge (passes > 1) jetzt mit je eigenem Stand, wie bei Büchern – im ersten
  Durchgang auf Seite 5 stehen und gleichzeitig im zweiten auf Seite 7 ist jetzt möglich. `ReadingEntry.durchlauf`
  (1-basiert, Default 1) hält fest, zu welchem Durchgang ein Eintrag gehört; `ReadingTask.durchlauf_done(n)` und
  `aktiver_durchlauf()` (der erste noch nicht abgeschlossene) in der Domäne. API liefert je Pensum eine
  `durchlaeufe`-Liste (`{nummer, done, total, abgeschlossen, aktiv}`). Oberfläche (`TaskCard.vue`): abgeschlossene
  Durchgänge nur als Zahl oben zusammengefasst („2 von 4 Durchgängen abgeschlossen“), nur der gerade laufende
  bekommt eine eigene Statusleiste, künftige (noch nicht erreichte) Durchgänge erscheinen gar nicht erst.
  Eintragen-Formular bekommt bei passes > 1 ein Durchgang-Dropdown (anders als beim Buch bewusst mit einer
  Vorauswahl – dem aus echten Daten berechneten aktiven Durchgang, kein Zufallswert).

- [fertig] Karteikarten doppelseitig drucken: `GET /api/karteikarten/decks/{id}/druckbogen` baut aus den Karten
  eines Fachs eine neue PDF-Seite mit reportlab (eigener Port `PrintRenderer`/Adapter `ReportlabPrintRenderer`,
  kein Overlay wie bei `pdfcreator` – hier wird von Grund auf gezeichnet). Raster 2×4 Karten je Bogen, je zwei
  PDF-Seiten im Wechsel (erst alle Vorderseiten des Bogens, dann alle Rückseiten) – beim doppelseitigen Drucken
  liegen so aufeinanderfolgende Seiten direkt richtig. Rückseite ist je Zeile spaltenverkehrt gezeichnet (passt
  zu „Wenden an der langen Kante“, der üblichen Standardeinstellung – bei „kurzer Kante“ zur Probe erst mit
  wenigen Karten drucken). `card.back` ist für alle Kartentypen schon der richtige Antworttext (bei Multiple
  Choice/Richtig-Falsch die richtige Antwort, nicht die Optionenliste), daher keine Sonderfälle im Renderer nötig.
  Dünne gestrichelte Schnittlinien je Karte. Oberfläche: Knopf „Als PDF drucken“ im Fach-Reiter Karteikarten,
  wie der PDF-Export beim Lesenachweis als Browser-Download (`flashcardService.drucken()`, eigener Fetch-Aufruf
  für die Binärdatei statt des gemeinsamen `createCall`, siehe `httpApi.js`).

- [fertig] Benutzerverwaltung wie bei der Finanzapp (`/Users/admin/finanzapp`, Vorbild begutachtet): auf der
  Konto-Seite ist das Admin-Recht jetzt eine Checkbox je Benutzer (statt nur beim Anlegen setzbar und danach
  ein reiner Anzeige-Chip) – `PUT /api/accounts/{username}/admin`, `AuthService.set_is_admin`. Der letzte Admin
  kann sich sein Admin-Recht nicht selbst nehmen (serverseitig erzwungen, wie bei der Finanzapp). Dazu „Passwort
  neu setzen“ je Benutzer: `POST /api/accounts/{username}/reset-password` erzeugt ein zufälliges temporäres
  Passwort, meldet das Konto überall ab (`SessionStore.delete_for_account`, neue Pflichtmethode am Port) und
  setzt `Account.muss_passwort_aendern`. Das temporäre Passwort steht einmalig in der Oberfläche (nicht
  geloggt) – der Admin kennt nie das endgültige Passwort, das sich der Benutzer selbst setzt. Beim nächsten
  Anmelden zeigt die Oberfläche statt der App erst `PasswortAendernPflichtView.vue` (temporäres Passwort als
  „bisheriges“ + neues zweimal, nutzt denselben `PUT /api/me/password`-Weg wie die normale Passwort-Änderung,
  die dabei das Flag löscht).
  Zusätzlich wie bei der Finanzapp: nach automatischer Abmeldung durch Inaktivität zeigt die Anmeldeseite jetzt
  einen Hinweis („Du wurdest nach 15 Minuten ohne Benutzung abgemeldet.“) statt kommentarlos zum leeren
  Login-Formular zurückzuspringen (`state/auth.js` `abmeldeHinweis`, gesetzt in `App.vue` `idleLogout()`,
  geleert beim nächsten erfolgreichen Login). Finanzapp selbst hat weder einen Vorab-Countdown/Warn-Dialog vor
  der automatischen Abmeldung noch einen Bestätigungsdialog beim manuellen Abmelden – beides bewusst nicht
  nachgebaut, das „Abmelden wie bei der Finanzapp“ bezog sich recherchiert auf genau diesen Hinweistext.

- [fertig] Noten: `note` (deutsche Notenskala 1,0 bis 5,0, optional) ist ein Feld am Fach im Kern (wie `se`,
  dieselbe Begründung: gehört zum Fach selbst, kein eigener Dienst nötig). Eintragbar im Fach-Bearbeiten-Formular
  (neben SE/Credits) und direkt im neuen globalen Reiter „Noten“ (`NotenView.vue`, Stift-Symbol je Fach-Kachel).
  Allgemeine Auswertung `GET /api/noten` (`SubjectService.notenuebersicht`): Durchschnitt über alle benoteten
  Fächer, gewichtet nach SE (Fach ohne SE zählt wie eine SE – dieselbe Regel wie bei der Aufgaben-Gewichtung:
  vorhandene Gewichte zählen mehr, fehlende wie ein normaler Anteil). „Noten“ steht in `RESERVED`, kein Dienst
  darf sich so nennen.

- [fertig] Neuer Dienst `bibel`: eine Bibel als PDF hinterlegen, auf die Bibelstellen in der ganzen App
  verweisen können – ein Klick führt direkt zur passenden Seite. Fachübergreifend wie `pdfcreator`/
  `aufgabenleser` (kein `panel`, kein Fach-Bezug), eigene Oberfläche `BibelView.vue` als globaler Reiter
  „Bibel“ im Kern-Frontend (nicht als iframe-`ui.html`, weil Upload + Seiten-Tabelle mehr Interaktion
  brauchen, als das UI-Kit der Dienst-Vorlage hergibt).
  - **Seiten-Erkennung** (`pdf_text.py`, `PypdfText.buchseiten_erkennen`): beim Hochladen zweistufig automatisch
    erkannt, auf welcher PDF-Seite jedes der 66 Bücher beginnt. 1) Jede Seite trägt in ihrer Kopfzeile die
    gedruckte Seitenzahl (z. B. „183“ oder bei einer Doppelseite „482 483“) – daraus eine Zuordnung gedruckte
    Seitenzahl → PDF-Seite; fehlt sie (Buch-Titelseiten zeigen oft keine eigene Seitenzahl), wird auf die
    nächstgelegene bekannte Seitenzahl hochgerechnet (höchstens 5 Seiten Abstand). 2) Ein „Inhaltsverzeichnis
    und Abkürzungen der Bücher des Alten/Neuen Testaments“ listet je Buch Name, Kurzname und gedruckte
    Seitenzahl – daraus mit Schritt 1 die PDF-Seite je Buch. Gegen die echte Schlachter-2000-PDF des Nutzers
    geprüft: alle 66 Bücher korrekt gefunden. Nur ein Vorschlag (wie die KI-Ergebnisse bei `pdfcreator`/
    `aufgabenleser`, siehe Entscheidungen) – von Hand korrigierbar über `PUT /api/bibel/buecher/{index}`,
    in `BibelView.vue` je Buch ein Stift-Symbol wie bei Fach/Pensum/Dozent.
  - **Verstext** (`verse_extractor.py`, `PypdfVerseExtractor`): liest zusätzlich den eigentlichen Bibeltext
    heraus, Buch für Buch innerhalb seines erkannten Seitenbereichs. Reine Textbereinigung, keine KI: Seitenzahl-
    Kopfzeilen, Fußnotenzeilen („a (1,26) hebr. …“) und Querverweiszeilen („Ps 104,2; Jos 45,7; 2Kor 4,6“)
    werden herausgefiltert (Letzteres über `find_book` – eine Zeile, die nur aus Buch+Zahl-Häppchen besteht,
    ist kein echter Verstext), Ligaturen (ﬂ, ﬁ, …) und Trennungen am Zeilenumbruch repariert. Versgrenzen
    erkennt man an der Zahl, die jeden Vers einleitet (Zeilenanfang oder nach Satzzeichen + 1-2 Leerzeichen
    mitten in der Zeile); ein unplausibler Zahlensprung (> 15, z. B. „782 Jahre“ in einem Stammbaum-Kapitel,
    wo auf das großgeschriebene deutsche Nomen ein falscher Treffer folgen könnte) zählt nicht als Versgrenze.
    **Bekannte Lücke:** Vers 1 eines Kapitels steht im Druck nie mit eigener Zahl da; am Kapitelwechsel gibt es
    dafür keine im Text sichtbare Markierung (Zwischenüberschriften lassen sich ohne Schriftart-Information aus
    der PDF nicht zuverlässig erkennen) – der unnummerierte Vers 1 jedes Kapitels (außer dem ersten eines
    Buches) hängt darum am Ende des letzten Verses des vorigen Kapitels, statt eine eigene Zeile zu sein.
    Gegen die echte Datei geprüft: Johannes korrekt in 21 Kapitel zerlegt, Joh 3,16 wortgenau extrahiert,
    insgesamt rund 25 000 von etwa 31 000 Versen gefunden (~82 %) – ein „Gerüst zum Prüfen und Nachbessern“,
    wie vom Nutzer so gewünscht, keine redaktionell geprüfte Ausgabe.
  - **Kapitel-Seite, wenn Vers 1 nicht bekannt ist**: Kapitel 1 eines Buches liegt genau auf dessen Startseite;
    andere Kapitel sind proportional zwischen dieser und der Startseite des nächsten Buches verteilt (nach
    Kapitelanteil, `Buch.chapters` – eine fest hinterlegte, bekannte Zahl je Buch) – nah dran, aber nicht exakt.
  - **Geschwindigkeit**: Das Herauslesen der Verse einer ganzen Bibel (hier 1396 Seiten) dauert 1-2 Minuten,
    zu lang für eine Antwort auf `POST /api/bibel/hochladen` (Proxy-Timeouts). Die Seiten-Erkennung selbst
    läuft darum im Thread-Pool (dauert nur Sekunden, blockiert aber sonst den ganzen Dienst, auch
    `/api/health`, wie der Ollama-Aufruf bei `pdfcreator`), das Herauslesen der Verse läuft zusätzlich als
    eigener, nicht abgewarteter Hintergrund-Thread – die Antwort auf das Hochladen kommt sofort mit den
    erkannten Buch-Seiten, `hat_verse` in der Antwort zeigt, ob die Verse schon fertig sind.
  - **Verknüpfung im Register**: Die Bibelstellen-Chips im Register-Reiter (`RegisterPanel.vue`) sind jetzt
    Knöpfe statt reiner Anzeige – ein Klick löst `GET /api/bibel/stelle?text=…` auf und öffnet
    `/api/bibel/datei#page=N` in einem neuen Tab (PDF-Fragment, vom Browser nativ unterstützt).

- [fertig] Bibel als Grundlage für Verknüpfungen bis auf Wortebene (auf Wunsch vorbereitet, noch ohne eigene
  Oberfläche dafür): jeder Vers hat jetzt eine stabile, kanonische Adresse (`domain/bible.py`, `Stelle.format()`,
  z. B. `Joh.3.16`; mit Wort `Joh.3.16.5` = 5. Wort dieses Verses) – `Vers.id` trägt sie, `parse_stelle()`
  liest sie wieder ein (anders als `parse_ref()`, das freien Text wie „Joh 3,16-18“ für die Seitensuche
  versteht, erwartet `parse_stelle()` immer genau diese Punkt-Schreibweise, nie einen Bereich: eine Stelle,
  an die man etwas anknüpft, ist immer genau eine Stelle).
  - `GET /api/bibel/wort?stelle=Joh.3.16.5` löst ein einzelnes Wort auf (samt dem ganzen Vers als Zusammenhang).
    Wörter werden nicht gespeichert, sondern bei Bedarf aus `Vers.text` zerlegt (`domain/models.py`, `woerter()`
    – an Leerraum, Satzzeichen bleiben am Wort), damit sich die Zahl nicht ändert, wenn man dieselbe Datei
    erneut hochlädt.
  - Neuer genereller **Verweis**-Mechanismus (`domain/models.py`, `Verweis`; `VerweisRepository`): ein Verweis
    hat `stelle` (die kanonische Adresse), `art` (freier Text, keine feste Liste – „register-eintrag“, „notiz“,
    „frage“, „wortstudie“, was auch künftig dazukommt), `referenz` (eine ID/Kurzbeschreibung des verweisenden
    Dings – der `bibel`-Dienst kennt die anderen Dienste nicht, siehe Regeln) und optional `titel`.
    `POST /api/bibel/verweise`, `GET /api/bibel/verweise?stelle=…` (Rückwärtssuche: was zeigt hierher?),
    `DELETE /api/bibel/verweise/{id}`. Bewusst noch nicht ans Register oder sonst wohin angeschlossen (reine
    Vorbereitung) – das Register verlinkt weiterhin nur zur Seite, nicht als `Verweis`-Eintrag.
  - 38 Bibel-Dienst-Tests grün (15 neue: `Stelle`-Format/Parsing, `woerter()`/`Vers.wort()`, `wort()`- und
    `verweis_*`-Anwendungsfälle). Gegen die echte Schlachter-PDF nachgerechnet: `Joh.3.16.5` löst korrekt zu
    „Gott“ auf.

- [fertig] Bibel lesen (die Bibel als Grundlage, nicht nur als PDF-Seitenlink): neuer Anwendungsfall
  `BibelService.nachschlagen(text)` (`application/services.py`) löst eine frei eingegebene Stelle wie
  „Joh 3,16“ über `parse_ref` + das schon vorhandene `kapitel()` auf und liefert das GANZE Kapitel mit
  Verstext dazu `markiert` – der angefragte Vers zum Hervorheben, `None` bei einer reinen Kapitelangabe
  („Ps 23“). Dafür kennt `BibleRef` (`domain/bible.py`) jetzt auch den ersten genannten Vers; nebenbei einen
  bis dahin unbemerkten Fehler behoben: bei den `SINGLE_CHAPTER`-Büchern (Obd, Phlm, 2Joh, 3Joh, Jud) wurde
  die einzige Zahl („Jud 5“ = Vers 5) zwar richtig als Kapitel 1 erkannt, der Vers selbst aber verworfen.
  Route `GET /api/bibel/nachschlagen`. Zeigt bewusst den Text selbst, nie eine PDF-Seite – `stelle()`/
  `GET /api/bibel/stelle` bleiben unverändert für den Seiten-Link aus dem Register.
  Oberfläche (`BibelView.vue`, Abschnitt „Lesen“, nur sichtbar sobald Verse eingelesen sind): Eingabefeld für
  eine Bibelstelle (ruft `nachschlagen`) und ein Buch-Dropdown zum Durchlesen ab Kapitel 1 (ruft `kapitel`,
  ohne Markierung); das gefundene Kapitel steht direkt auf der Seite in eigener, gut lesbarer Typografie
  (Serifenschrift, große Zeilenhöhe, Verszahlen als kleine hochgestellte Ziffern, der nachgeschlagene Vers
  farblich hervorgehoben) – kein PDF-Embed. Pfeile links/rechts blättern Kapitel für Kapitel innerhalb des
  gewählten Buchs (am Buchanfang/-ende deaktiviert).

- [fertig] Neuer Dienst `bibliothek`: eigener Bücherbestand (Bücherkatalog), unabhängig vom Fach – Titel,
  Autor, Verlag, Jahr, ISBN, Standort, Notiz; beliebig vielen Fächern zuordenbar (wie Dozenten im Adressbuch:
  eigene Zuordnungsliste je Buch, löscht der Kern ein Fach, bleibt das Buch). Ausleihe: `ausleihen_an`/
  `ausleihen`/`zurueckgeben` (wer ein Buch hat, einfacher Name statt eigenem Konto). Fachübergreifend wie
  `pdfcreator`/`aufgabenleser` (kein `panel`, eigene Oberfläche `BibliothekView.vue` als globaler Reiter).
  - **Gescannte Bücher per KI durchsuchbar machen**: Original-PDF hochladen (`POST /api/bibliothek/buecher/{id}/datei`,
    multipart, über `FileSystemDateiSpeicher`/`storage.py` wie bei `skripte`), dann „Text erkennen“ (`POST
    .../text-erkennen`) – liest je Seite das größte eingebettete Bild heraus (`PypdfBildExtraktor`), schickt es
    an ein Ollama-Vision-Modell (`OllamaOcrKI`, eigener `OLLAMA_VISION_MODEL`, Default `llama3.2-vision` – ein
    reines Textmodell wie bei `pdfcreator`/`aufgabenleser` versteht keine Bilder), und legt den erkannten Text
    als unsichtbare Textebene über die Original-Seite (`ReportlabTextPdfBauer`, `reportlab` `beginText()` +
    `setTextRenderMode(3)`, dann mit `pypdf` zusammengeführt) – Original bleibt optisch unverändert, die neue
    Text-PDF (`GET .../text-datei`) ist durchsuchbar/kopierbar. Wie bei der Bibel-Verse-Erkennung läuft das
    Erkennen (ein KI-Aufruf je Seite, dauert bei einem ganzen Buch mehrere Minuten) als eigener, nicht
    abgewarteter Hintergrund-Thread (`threading.Thread(daemon=True)`), die Antwort auf das Auslösen kommt sofort
    (202); kein Live-Fortschritt in der Oberfläche, man lädt nach ein paar Minuten neu. Ohne `OLLAMA_URL` bleibt
    es bei `NullOcrKI` (Fehlermeldung bei Aufruf) – wie bei `pdfcreator` ist das Hochladen selbst davon unberührt.
  - 17 Dienst-Tests grün (Service mit In-Memory-Fakes + Adapter-Tests gegen echte, synthetisch erzeugte PDFs
    mit eingebetteten Bildern – bestätigen u. a., dass die unsichtbare Textebene mit `pypdf.extract_text()`
    tatsächlich auffindbar ist).

- [fertig] Neuer Dienst `schnelllesen`: Speedreading-Training nach der tatsächlichen 3-2-1-Methode. Runde 1:
  3 Minuten frei im ganzen Kapitel lesen, danach auf das letzte gelesene Wort klicken ("wie weit bin ich
  gekommen") – dieser Abschnitt (`Einheit.segment_woerter`, Wortzahl bis dahin) ist ab Runde 2 der GANZE
  Text: Runde 2 (2 Minuten) und Runde 3 (1 Minute) zeigen nur noch genau diesen, schon bekannten Abschnitt,
  man liest ihn also zweimal erneut, in immer weniger Zeit (`Einheit.text_fuer_runde(runde)`). Fachübergreifend
  wie `bibel` (kein `panel`, eigene Oberfläche `SchnelllesenView.vue` als globaler Reiter, Symbol `stoppuhr`).
  Eigene, gekürzte Kopie von `domain/bible.py` (nur Buch + Kapitelzahl, siehe Entscheidungen) – Buch/Kapitel-
  Auswahl kommt darüber aus dem Dienst selbst (`GET /api/buecher`). Holt sich den Verstext eines Kapitels
  direkt vom Bibel-Dienst (`HttpBibelQuelle`, `BIBEL_URL`, Default `http://bibel:8000`) – ein direkter
  Dienst-zu-Dienst-Aufruf im Docker-Netz wie bei `pdfcreator`/`aufgabenleser` zu Ollama, nicht über den Kern
  (der Login verlangt). `Durchgang.woerter` hält je Runde die für `wpm` (Wörter pro Minute) maßgebliche
  Wortzahl (Runde 1: wie weit gekommen, ab Runde 2: die Länge des Abschnitts) – wird aus der gespeicherten
  Wortzahl berechnet, nicht erneut vom Bibel-Dienst nachgefragt, bleibt also auch stabil, falls sich dessen
  Text später ändert. Die Oberfläche misst die Zeit selbst (Timer im Browser, kein serverseitiger Countdown):
  Runde 1 stoppt automatisch nach 3 Minuten und zeigt den Text dann klickbar Wort für Wort; ab Runde 2 bleibt
  das „Fertig“ dem Lesenden überlassen, auch über das Ziel hinaus (zeigt dann rot an). Verlauf vergangener
  Einheiten mit Lösch-Knopf unterhalb des laufenden Trainings.
  `neuer-dienst.sh` nebenbei repariert: es hängte den neuen Dienst immer ans Dateiende von
  `docker-compose.override.yml` an, was bei einem bestehenden `networks:`-Schlüssel am Dateiende (wie bei `ki`
  durch `pdfcreator`/`aufgabenleser`/`bibliothek`) den neuen Dienst fälschlich dort einhängte (kaputtes YAML) –
  fügt jetzt direkt nach `services:` ein.

<<<<<<< HEAD
- [fertig] PDFs direkt im Browser drucken UND herunterladen (statt nur erzwungenem Download): gemeinsame
  Funktion `kern/frontend/src/application/pdf.js` (`fensterOeffnen`/`pdfZeigen`) – öffnet die PDF-Datei in
  einem neuen Reiter, wo der Browser seine eigene PDF-Ansicht mit Drucken- und Herunterladen-Knopf mitbringt,
  statt sie wie bisher sofort als Datei zu speichern. Das Fenster muss schon offen sein, BEVOR die Datei beim
  Server abgeholt wird (`fensterOeffnen()` synchron im Klick-Handler, bevor das `await` der eigentlichen
  PDF-Erzeugung läuft) – sonst blocken Safari und manche Pop-up-Blocker das Fenster, weil die „Nutzeraktion“ mit
  der ersten asynchronen Anfrage als verbraucht gilt. Blockt der Browser trotzdem, lädt `pdfZeigen` ersatzweise
  herunter (nichts geht verloren). Eingesetzt bei Karteikarten-Druckbogen (`DeckPanel.vue`) und beim
  Lesenachweis-PDF-Export (`TaskCard.vue`, `ReadingPanel.vue`).
  Dabei auch den bisher nur lokal (nicht committeten) Karteikarten-Druckbogen fertiggestellt: eigener
  `PrintRenderer`-Port, `ReportlabPrintRenderer` zeichnet 2×4-Raster je Bogen, Vorder-/Rückseiten im Wechsel
  (Rückseite spaltenverkehrt je Zeile, passt zu „Wenden an der langen Kante“), `GET /api/karteikarten/decks/
  {id}/druckbogen`.

- [fertig] Der Karteikarten-Druckbogen (siehe oben) lag auf einem eigenen Branch (`pdf-drucken-im-browser`),
  der nie in diesen Arbeitsbranch gemergt wurde – im Code fehlte die Funktion deshalb komplett, obwohl diese
  Datei sie schon als fertig führte. Nachträglich per `git cherry-pick` nachgeholt. Dabei auf Wunsch gleich auf
  A7 umgestellt: `CELL_W`/`CELL_H` in `print_renderer.py` sind jetzt exakt 105 x 74 mm (A7 quer) statt aus der
  A4-Seite mit 28pt Rand berechnet – 2 Spalten x 105 mm treffen die A4-Breite (210 mm) genau, 4 Zeilen x 74 mm
  die A4-Höhe (297 mm) fast genau, die Karten füllen das Blatt also randlos („platt voll“, auf Wunsch).
- [fertig] Druckbogen weiter ausgearbeitet: Format wählbar, A7 (2x4, 8 Karten je Bogen) oder A8 (4x4, 16
  Karten je Bogen). `FORMATE`-Dict in `print_renderer.py`, `ReportlabPrintRenderer.druckbogen(cards, format)`,
  durchgereicht über `FlashcardService.druckbogen` und `GET .../druckbogen?format=a7|a8`. Dropdown neben
  „Als PDF drucken“ in `DeckPanel.vue`. Dazu jede Karte oben links mit laufender Nummer (auf Vorder- UND
  Rückseite dieselbe, hilft beim Zuschneiden/Sortieren) und größere Schrift (`FONT_SIZE` 11 auf 13, auf Wunsch
  „dürfen ruhig mehr Zeilenumbrüche haben“ – kein automatisches Verkleinern bei langem Text, wächst einfach
  in die Höhe).
- [fertig] A8 druckt jetzt auch quer (auf Wunsch, „immer quer drucken“): Zelle 74 x 52 mm (statt 52 x 74 mm
  hochkant), dafür die ganze Seite quer gedreht (`landscape(A4)`, 297 x 210 mm) statt der bisherigen A4-Seite
  hochkant – 4 Spalten x 74 mm treffen die (jetzt breitere) Seite fast genau, 4 Zeilen x 52 mm die (jetzt
  niedrigere) Höhe fast genau, weiterhin 16 Karten je Bogen. Ohne die gedrehte Seite blieben bei quer-Zellen
  mehrere Zentimeter Papier ungenutzt. `FORMATE[format]["page"]` hält jetzt die Seitengröße pro Format,
  `canvas.Canvas(..., pagesize=...)` nutzt sie statt der festen `A4`-Konstante.
- [fertig] Register-Eintrag bearbeiten: bisher gab es nur Anlegen (ergänzt Stellen bei gleichem Namen) und
  Löschen, keine Möglichkeit, Name oder Stellen eines bestehenden Eintrags zu ändern, ohne ihn zu löschen und
  neu anzulegen. Neuer Anwendungsfall `RegisterService.update_entry` (ersetzt Name und Stellen vollständig,
  anders als `add_entry`, das nur ergänzt), Route `PUT /api/register/entries/{id}`. Name muss weiterhin im
  Register eindeutig sein (der bearbeitete Eintrag selbst zählt dabei nicht mit). Oberfläche
  (`RegisterPanel.vue`): „Bearbeiten“-Knopf neben „Löschen“ öffnet ein Inline-Formular an derselben Stelle
  (Name + Bibelstellen, wie beim Anlegen), „Speichern“/„Abbrechen“.

- [fertig] Arbeitspaket B – Konkordanz & Stichwortsuche (Erweiterung Bibel-Dienst): `GET /api/bibel/suche?wort=…`
  durchsucht den schon eingelesenen Verstext aller Bücher/Kapitel (Teilstring, Groß/Klein egal) und liefert
  Fundstellen (kanonische Stelle, Buch, Kapitel/Vers, dazu `kontextsatz` – der Satz aus dem Verstext, der das
  Suchwort enthält, einfache Trennung an Punkt/Ausrufe-/Fragezeichen statt echter Sprachanalyse). Auf 200
  Treffer begrenzt (`BibelService.suche(wort, limit=200)`), keine Volltextsuch-Engine nötig. Dafür neuer Port
  `VersRepository.alle()` (alle Verse, sortiert nach Buch/Kapitel/Vers) – Grundlage auch für Paket D.
  Oberfläche (`BibelView.vue`, Abschnitt „Konkordanz“ unterhalb von „Lesen“): Suchfeld, Trefferliste mit
  Kontextsatz, Klick springt ins gelesene Kapitel (bestehende `kapitel()`-Anzeige, Treffer-Vers statt einer
  nachgeschlagenen Stelle hervorgehoben).

- [fertig] Arbeitspaket C umgesetzt: Koordinaten je Register-Eintrag (`RegisterEntry.lat`/`lon`, optional,
  `.get(..., None)` – alte Daten ohne diese Felder bleiben gültig). Von Hand eingetragen, keine Geocoding-API
  verdrahtet: ein Textfeld „Breite, Länge“ im Eintragsformular (`parseKoordinaten` im Frontend zerlegt es),
  genauso beim nachträglichen Ändern (neuer Endpunkt `PUT /api/register/entries/{id}/location`,
  `RegisterService.set_location`, rührt Name/Stellen nicht an). `add_entry` setzt Koordinaten nur, wenn
  angegeben – beim bloßen Ergänzen weiterer Stellen zum selben Namen bleiben vorhandene Koordinaten unangetastet.
  Kartenausschnitt in `RegisterPanel.vue`: ein einzelnes statisches OpenStreetMap-Kachelbild (eigene Berechnung
  der Kachel-Nummer aus Breite/Länge, kein zusätzliches Paket) plus Link zum vollen Kartenausschnitt auf
  openstreetmap.org – bewusst kein `<iframe>` (Datenschutz/CSP: kein fremdes Dokument im eigenen Origin).

- [fertig] Neuer Dienst `predigten`: Predigt-/Schreibarchiv (Arbeitspaket E), nach dem Vorbild von `bibliothek`
  (Datei-Upload über `storage.py`/`FileSystemDateiSpeicher`) für den Upload-Teil, aber fachübergreifend wie
  `bibel`/`schnelllesen` (kein `panel`, keine Fach-Zuordnung, die drei Pflicht-Endpunkte des Fach-Vertrags sind
  reine No-ops). Ein Eintrag hat Titel, optionales Datum/Prediger/Notiz, optional eine hochgeladene Datei (PDF,
  genau eine je Predigt – anders als bei `bibliothek` kein Original/Text-Paar, siehe Texterkennung unten) und
  beliebig viele Bibelstellen.
  - **Verweis beim Bibel-Dienst**: eine frei eingegebene Stelle ("Joh 3,16", auch nur "Ps 23" – zeigt dann auf
    deren ersten Vers, ein Verweis braucht immer genau eine Stelle, siehe Entscheidungen) wird über die eigene
    Kopie von `domain/bible.py` (wie bei `bibel`/`register`/`schnelllesen`) in die kanonische Adresse
    übersetzt und direkt beim Bibel-Dienst angemeldet (`POST /api/verweise`, `art="predigt"`,
    `referenz=<predigt-id>`, `HttpBibelVerweise` in `app/adapters/outbound/bibel_client.py`, `BIBEL_URL` – nach
    dem Vorbild von `schnelllesen`s `HttpBibelQuelle` für den direkten Dienst-zu-Dienst-Aufruf im Docker-Netz).
    Die zurückgegebene Verweis-ID merkt sich die Predigt (`Predigt.verweis_ids`, Stelle -> ID), um beim
    Bearbeiten (gestrichene Stelle) oder Löschen der Predigt den zugehörigen Verweis gezielt wieder zu
    entfernen (`DELETE /api/verweise/{id}` beim Bibel-Dienst). Ist der Bibel-Dienst nicht erreichbar, bricht
    das weder das Anlegen noch das Bearbeiten/Löschen der Predigt ab (Fehler wird nur geloggt) – wie der
    Ollama-Aufruf bei `pdfcreator` ist der Verweis eine Zusatzleistung, kein Pflichtteil.
  - **Bewusst ausgelassen**: Texterkennung (OCR) für gescannte Predigten, wie sie `bibliothek` hat
    (Ollama-Vision-Modell + unsichtbare Textebene) – würde den Rahmen des ersten Durchgangs sprengen, kann bei
    Bedarf nach demselben Muster nachgerüstet werden (`BildExtraktor`/`OcrKI`/`TextPdfBauer`-Ports kopieren).
    Darum auch nur eine Datei je Predigt (kein Original/Text-Paar wie bei `bibliothek`).
  - Oberfläche: neuer globaler Reiter „Predigten“ (`PredigtenView.vue`, Symbol `predigten`, angelehnt an
    `BibliothekView.vue`), Liste mit Anlegen-Formular hinter einem Knopf (wie bei Dozenten/Pensen), Bibelstellen
    als Freitext-Feld (eine je Zeile oder durch Komma getrennt, `predigtenService.js`
    `stellenAusText`/`stellenZuText`), Datei-Upload wie bei `bibliothek`.
  - Nebenbei repariert: `neuer-dienst.sh` schlug auf diesem Mac fehl (`awk -v` mit einem mehrzeiligen Wert –
    "newline in string", ein BSD-awk-Problem, GNU-awk kennt es nicht). Der Einbau des neuen Dienst-Blocks in
    `docker-compose.override.yml` läuft jetzt über eine Block-Datei + `sed … r …` statt `awk -v`, portabel auf
    beiden Plattformen.

- [fertig] Arbeitspaket A umgesetzt – neuer Dienst `notizen`: eigene Gedanken an einer Bibelstelle. Ein
  `Kommentar` hat `stelle` (kanonische Adresse wie „Joh.3.16“), `text`, `erstellt` und `verweis_id`. Beim
  Anlegen meldet der Dienst sich direkt beim Bibel-Dienst als `Verweis` an (`POST /api/verweise`, `art=
  "kommentar"`, `referenz=<kommentar-id>`, `BIBEL_URL`, wie `schnelllesen` → `HttpBibelQuelle`): prüft dort
  zugleich die Stelle (`parse_stelle`) und liefert bei einer unbekannten Stelle 422 – dieser Fehler wird
  durchgereicht, der Kommentar bleibt dann ungespeichert. Ist der Bibel-Dienst nicht erreichbar, wird der
  Kommentar trotzdem gespeichert, nur `verweis_id` bleibt `None` (`NullBibelVerweise`, wie `NullBibelQuelle`
  bei `schnelllesen`). Löschen eines Kommentars löst auch den Verweis wieder auf. Fachübergreifend wie
  `bibel`/`schnelllesen` (kein `panel`, keine Fach-Daten, nur die drei Pflicht-Endpunkte als No-ops).
  Oberfläche: neuer globaler Reiter „Notizen“ (`NotizenView.vue`, analog `SchnelllesenView.vue`) – Bibelstelle
  frei eintippen (`bibel.nachschlagen(text)` löst sie auf, die kanonische Adresse baut das Frontend selbst aus
  `buch`/`kapitel`/`markiert` zusammen, kein eigener Stellen-Parser im Frontend nötig), Kommentar schreiben,
  Liste bisheriger Kommentare zu dieser Stelle.
=======
- [fertig] Neuer Dienst `fragenki` (Arbeitspaket D): schlägt zu einem gewählten Bibelkapitel 3-5
  Verständnisfragen vor (Ollama, wie `aufgabenleser`/`pdfcreator`: `OLLAMA_URL`/`OLLAMA_MODEL`, 180 Sekunden
  Zeitlimit, ohne `OLLAMA_URL` liefert `/api/generieren` 422, da die KI hier der ganze Zweck ist). Holt sich
  den Verstext des Kapitels direkt vom Bibel-Dienst (`BIBEL_URL`, wie `schnelllesen` → `HttpBibelQuelle`,
  eigene eingebettete Kopie von `domain/bible.py`). Ergebnis ist IMMER nur ein Vorschlag (siehe Entscheidungen):
  die KI liefert sicher nur die Frage, keine zuverlässige Antwort dazu – die rohe KI-Antwort bleibt in einem
  Klapptext sichtbar, auch ohne gültiges JSON. Fachübergreifend wie `aufgabenleser`/`schnelllesen` (kein
  `panel`, nur die drei Pflicht-Endpunkte als No-ops). Oberfläche: neuer globaler Reiter „Fragen und KI“
  (`FragenKiView.vue`) – Buch/Kapitel wählen, Fragen generieren, je Vorschlag ein Kontrollkästchen und ein
  Antwortfeld (die Antwort trägt der Nutzer selbst ein), dann Fach wählen und die ausgewählten Fragen als
  Karteikarten anlegen (Frontend-Orchestrierung über die bestehende Karteikarten-API des Kerns, Deck-ID =
  Fach-ID, wie `AufgabenPanel.vue` es für Aufgaben/Lesepensen macht).
  Nebenbei behoben: `neuer-dienst.sh` schlug auf macOS fehl (`awk: newline in string`) – das installierte
  BSD-awk ("one true awk") bricht bei `-v` mit einem mehrzeiligen String ab, anders als gawk. Der Dienst-Block
  kommt jetzt über eine Temp-Datei (`getline … < bf`) statt über `-v block="$block"` ins Skript, das läuft auf
  beiden awk-Varianten.
>>>>>>> origin/claude/fragenki-724ef6

## Fach-Vertrag (jeder Dienst)
`GET /api/health` · `PUT /api/subjects/{id}` {name} · `DELETE /api/subjects/{id}` · `GET /api/subjects/{id}/status` (darf `progress` 0 bis 100 oder null enthalten) ·
`GET /api/manifest` {name,label,panel,status:[{key,label}]} · optional `GET /api/subjects` (vorhandene Fächer, der Kern übernimmt sie).
Der Kern ruft ihn auf; die Fach-ID ist das Einzige, was Dienste teilen.

## Später
Aus der Bibelstudium-Mindmap (siehe Artefakt, von Claude am 2026-10-19 aus einer Skizze gebaut) abgeleitete
Arbeitspakete. Jedes ist ein eigener Dienst oder eine klar abgegrenzte Erweiterung eines bestehenden – damit
auf einem eigenen Branch/Worktree unabhängig von den anderen bearbeitbar, mehrere parallel in getrennten
Chats/Sitzungen. Bibel ist dabei schon jetzt die Grundlage für alles (siehe Entscheidungen: „Bibel als
Grundlage“) – kein Paket muss darauf warten, dass das erst gebaut wird.

- **A – Kommentare & Verbindungen** (neuer Dienst `notizen`, nutzt den vorbereiteten Verweis-Mechanismus des
  Bibel-Dienstes): eigene Gedanken an einer Bibelstelle; jeder Kommentar legt einen Verweis (`art="kommentar"`)
  im Bibel-Dienst an, „was verweist hierher?“ zeigt dann Register-Einträge und Kommentare zusammen.

- **A – Kommentare & Verbindungen** [fertig, siehe Stand] (neuer Dienst `notizen`, nutzt den vorbereiteten
  Verweis-Mechanismus des Bibel-Dienstes): eigene Gedanken an einer Bibelstelle; jeder Kommentar legt einen
  Verweis (`art="kommentar"`) im Bibel-Dienst an. Offen für später: „was verweist hierher?“ zeigt noch keine
  Register-Einträge und Kommentare zusammen an einer Stelle (der Bibel-Dienst kennt den Verweis schon, nur
  keine Oberfläche dafür).
- **B – Konkordanz & Stichwortsuche** (Erweiterung Bibel-Dienst): `GET /api/bibel/suche?wort=…` durchsucht
  den schon eingelesenen Verstext aller Bücher, liefert Fundstellen – Grundlage auch für Paket D.
- **C – Orte mit Landkarte** (Erweiterung Register-Dienst): Koordinaten je Ortseintrag (von Hand oder
  Geocoding-Vorschlag), Kartenansicht im Register-Reiter.

- **B – Konkordanz & Stichwortsuche** (Erweiterung Bibel-Dienst): `GET /api/bibel/suche?wort=…` durchsucht
  den schon eingelesenen Verstext aller Bücher, liefert Fundstellen – Grundlage auch für Paket D.
- **D – Fragen & KI** (neuer Dienst `fragenki`, wie `aufgabenleser`: Ollama liefert nur einen Vorschlag):
  Fragen zu einem Kapitel generieren, als Karteikarte übernehmbar; Lernstand-Statistik separat (fachübergreifend).
- **E – Predigt-/Schreibarchiv** (neuer Dienst `predigten`, wie `bibliothek`: Upload + Texterkennung):
  Predigten/eigene Texte hochladen, optional mit Verweis auf die behandelte Bibelstelle (Mechanismus wie A).
- **F – Griechisches Glossar** (neuer Dienst `glossar`, fachübergreifend wie `bibel`, nutzt denselben
  Verweis-Mechanismus wie A): ein Eintrag hält griechisches Wort, Transliteration und Erklärung; beliebig
  viele Bibelstellen je Wort, jede legt einen Verweis (`art="glossar"`) beim Bibel-Dienst an. Oberfläche:
  neuer globaler Reiter „Glossar“, alphabetische Liste mit Suchfeld, Bibelstellen als anklickbare Chips
  (wie im Register). Kein eigener griechischer Grundtext nötig (das wäre ein viel größerer, vager Brocken –
  eine eigene Textquelle parallel zum deutschen Vers einzubinden) – diese kleinere, konkrete Form schlägt das.
- **G – Gliederung & Spickzettel, wissenschaftliche Zitierhilfe** (Erweiterung des `notizen`-Diensts aus A):
  strukturierte Gliederungspunkte statt freier Kommentare, Export mit Quellenangabe. Baut auf A auf.
- **H – Automatische Fortschritt-Vorschläge** (Kern-Erweiterung, Ausnahme „Aufgaben liegen im Kern“ gilt
  weiter): baut auf D auf, braucht also die KI-Anbindung zuerst.

A, B, D, E, F sind voneinander unabhängig und direkt startbar (C ist fertig, siehe Stand).
G hängt an A, H an D.

Ältere, von der Mindmap unabhängige Ideen: Priorisierung (Eisenhower: dringend/wichtig) als eigener Dienst für
Aufgaben · Kalender-Dienst (Aufgabe, Soll, Ist) · Bulk-Import der 50 Fächer aus dem Studienablaufplan (SE,
Dozent, Semester; Foto kann Lesefehler enthalten – Kontrollliste nötig) · Fristen-Erinnerung über alle Fächer.

## Entscheidungen
- **Bibel als Grundlage** (auf Wunsch festgehalten): der Bibel-Dienst ist die einzige Quelle für Bibeltext.
  Ein Dienst, der Verstext braucht, holt ihn über die öffentliche API des Bibel-Diensts (direkter
  Dienst-zu-Dienst-Aufruf im Docker-Netz, `BIBEL_URL`, wie bei `schnelllesen` → `HttpBibelQuelle`), legt sich
  nie eine eigene Kopie des Textes an. Zeigt ein Dienst auf eine einzelne Bibelstelle (ein Kommentar, ein
  Register-Eintrag, eine Predigt), meldet er das als `Verweis` beim Bibel-Dienst an (`POST /api/bibel/verweise`,
  siehe dessen generischer Verweis-Mechanismus) – so bleibt „was verweist hierher?“ an einer Stelle beantwortbar,
  über alle Dienste hinweg. Nur die Buchliste/der Parser (`domain/bible.py`) bleibt pro Dienst eine eigene
  Kopie (siehe unten), der Text selbst nie.
- Der Kern ist der einzige Eingang der Oberfläche; er reicht Aufrufe an die Dienste weiter.
- Tempo für die Prognose: Durchschnitt der letzten 14 Tage. „Knapp“ = Tempo unter 115 % des Bedarfs.
- Bibelbücher: 66, evangelische Reihenfolge, Kurznamen nach Lutherbibel; Bücher mit einem Kapitel (Obd, Phlm, 2Joh, 3Joh, Jud): „Jud 5“ = Vers 5.
  Jeder Dienst, der Bibelstellen kennt (Register, `bibel`), hat eine eigene Kopie der Buchliste/des Parsers (`domain/bible.py`) –
  Dienste teilen keinen Code, nur die Fach-ID (siehe Regeln); Kurznamen und Reihenfolge bewusst überall identisch gehalten.
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
- `/api/registry` (Selbstanmeldung der Dienste) bleibt bewusst ohne Login erreichbar, da Dienste den Kern intern
  über `http://kern:8000` ansprechen (nicht über die Oberfläche) und keine eigenen Zugangsdaten haben. War schon vor
  dem Login offen erreichbar; das Risiko ändert sich durch den Login nicht, nur die eigentlichen Daten sind jetzt
  geschützt. Wer die App ins offene Internet stellt, sollte das wissen.
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
- Gleiche Falle wie bei `list(...)`, aber auf Instanz-Ebene statt Klasse: ein Attribut `self.original = {}` in
  `__init__` überschreibt in derselben Klasse stillschweigend eine Methode `def original(self, ...)` für diese
  Instanz (`TypeError: 'dict' object is not callable` beim nächsten Aufruf) – passiert leicht in Test-Fakes, die
  Port-Methodennamen als naheliegende Attributnamen wiederverwenden. Abhilfe: Attribut anders nennen (z. B.
  `self._original`), nie denselben Namen wie eine Methode der Klasse.
