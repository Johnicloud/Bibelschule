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

- [fertig] Dienst `vorlesen`: liest Text oder ein PDF vor (lokale KI-Stimme, kein Cloud-Dienst, kein API-Key,
  kostenlos – auf Wunsch so). Vertonung über Piper (https://github.com/rhasspy/piper), das deutsche Stimmmodell
  „Thorsten“ (mittlere Qualität, CC0/MIT) liegt dem Image bei (`Dockerfile` lädt es beim Bauen von Hugging Face),
  läuft komplett offline im eigenen Container – anders als `pdfcreator`/`aufgabenleser`/`bibliothek` also kein
  `OLLAMA_URL`/`networks: [default, ki]` nötig. `PiperTextToSpeech` ruft `piper` als eigenen Prozess auf (nicht
  über die Python-Bibliothek, deren Schnittstelle sich schon geändert hat – die Kommandozeile ist stabil).
  Fachübergreifend wie `pdfcreator`/`aufgabenleser` (kein `panel`, keine eigenen Fach-Daten, zustandslos – kein
  `./data`-Volume –, nur die drei Pflicht-Endpunkte). Zwei Endpunkte: `POST /api/text` (reiner Text) und
  `POST /api/pdf` (PDF-Datei, Text per `pypdf` wie beim `aufgabenleser`-Dienst herausgelesen), beide geben WAV
  zurück. Höchstens 20 000 Zeichen je Durchlauf (längere Texte brauchen auf der CPU sehr lange).
  Zwei Zugänge in der Oberfläche: ein globaler Reiter „Vorlesen“ (`VorlesenView.vue`, freier Text einfügen,
  Audio spielt automatisch) und ein „Vorlesen“-Knopf je Datei im Skripte-Reiter (`skripte/.../ui.html`) – holt
  die Datei über die schon vorhandene `/datei`-Vorschau-URL und schickt sie an `vorlesen` weiter, rein im
  Browser, ohne dass ein Dienst einen anderen Dienst serverseitig aufruft (es gibt dafür noch kein Vorbild im
  Projekt; der Kern leitet nur Oberfläche-zu-Dienst weiter, nie Dienst-zu-Dienst, siehe Entscheidungen). Aufruf
  eines fremden Diensts aus der eigenen `ui.html` darum bewusst mit absolutem Pfad (`/api/vorlesen/pdf`), nicht
  relativ (relativ träfe sonst den eigenen Dienst, siehe Entscheidungen zum relativen Aufruf).
  Nebenbei `neuer-dienst.sh` repariert: trug neue Dienste bisher ans Ende von `docker-compose.override.yml`
  an, landete nach dem ersten Ollama-Dienst (der einen `networks:`-Block anhängt) fälschlich dort statt bei
  den übrigen Diensten (ist `bibel` und beim Anlegen von `vorlesen` selbst genau so passiert, von Hand
  korrigiert) – fügt jetzt direkt nach der `services:`-Zeile ein.

## Fach-Vertrag (jeder Dienst)
`GET /api/health` · `PUT /api/subjects/{id}` {name} · `DELETE /api/subjects/{id}` · `GET /api/subjects/{id}/status` (darf `progress` 0 bis 100 oder null enthalten) ·
`GET /api/manifest` {name,label,panel,status:[{key,label}]} · optional `GET /api/subjects` (vorhandene Fächer, der Kern übernimmt sie).
Der Kern ruft ihn auf; die Fach-ID ist das Einzige, was Dienste teilen.

## Später
Skript und Fragen mit Ollama einlesen (Aufgabenblatt selbst
macht das schon der `aufgabenleser`-Dienst; Ollama läuft direkt auf dem Mac, Container erreichen es über
host.docker.internal:11434; Ergebnisse immer nur Vorschlag, siehe Entscheidungen) ·
Priorisierung (Eisenhower: dringend/wichtig) als eigener Dienst für Aufgaben ·
Kalender-Dienst (Aufgabe, Soll, Ist) · Bulk-Import der 50 Fächer aus dem Studienablaufplan (SE, Dozent, Semester;
noch nicht gemacht, Foto kann Lesefehler enthalten – Kontrollliste nötig) · evtl. Fristen-Erinnerung über alle
Fächer, Volltextsuche, Notizen/Logbuch.

## Entscheidungen
- Der Kern ist der einzige Eingang der Oberfläche; er reicht Aufrufe an die Dienste weiter.
- Kein Dienst ruft einen anderen Dienst direkt auf (kein Vorbild dafür im Projekt, auch `vorlesen` tut das nicht):
  braucht ein Dienst Daten eines anderen (z. B. `vorlesen` die Datei von `skripte`), holt die Oberfläche sie beim
  einen Dienst und reicht sie an den anderen weiter – reine Browser-Orchestrierung, wie schon die
  Dozentenzuordnung beim Fach-Anlegen. Jeder Dienst bleibt dadurch unabhängig erreichbar/austauschbar.
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
