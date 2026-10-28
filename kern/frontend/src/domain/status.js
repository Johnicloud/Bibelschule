// Anzeige-Regeln: Namen der Dienste, Lesestatus, Datum, Prognosetext.
export const SERVICE_LABELS = {
  karteikarten: 'Karteikarten',
  lesenachweis: 'Lesenachweis',
  register: 'Register',
}

// Dienste mit eigener, eingebauter Oberfläche. Jeder andere Dienst erscheint über sein Manifest von selbst.
export const NATIVE_SERVICES = ['karteikarten', 'lesenachweis', 'register']

// Fest (immer Reiter, nie abschaltbar): aufgaben (Kern) und lesenachweis. Optional (nur Reiter/Kachel in der
// Übersicht, wenn im Fach eingeblendet, siehe subject.aktive_dienste): Register/Karteikarten/Bibelverse/Skripte.
// Adressbuch erscheint bewusst nirgends in der Fach-Übersicht (Dozenten-Zuordnung läuft übers Bearbeiten-Formular
// und den globalen Adressbuch-Reiter).
export const OPTIONAL_SERVICES = ['karteikarten', 'register', 'bibelverse', 'skripte']

// Symbol je Reiter innerhalb eines Fachs (SubjectView.vue und die Übersicht darin, SubjectOverview.vue) –
// an einer Stelle, damit beide dieselben Symbole zeigen. Name ohne Eintrag hier fällt auf 'baustein' zurück.
export const TAB_ICONS = {
  uebersicht: 'uebersicht', aufgaben: 'aufgaben', karteikarten: 'karten', lesenachweis: 'lesenachweis',
  register: 'register', adressbuch: 'adressbuch', bibelverse: 'bibelverse', skripte: 'skripte',
}

export const READING_STATUS = {
  overdue: { label: 'Frist überschritten', tone: 'rose' },
  behind: { label: 'Im Rückstand', tone: 'rose' },
  tight: { label: 'Knapp', tone: 'amber' },
  not_started: { label: 'Noch nicht begonnen', tone: 'slate' },
  open: { label: 'Ohne Frist', tone: 'slate' },
  on_track: { label: 'Im Plan', tone: 'teal' },
  done: { label: 'Fertig', tone: 'teal' },
}

// Fünf Stufen des Fachs, vom Kern automatisch aus Fortschritt und Aufgaben hergeleitet (kein eigenes Pflegen).
export const FACH_STATUS = {
  angelegt: { label: 'Angelegt', tone: 'slate' },
  begonnen: { label: 'Begonnen', tone: 'amber' },
  in_arbeit: { label: 'In Arbeit', tone: 'sky' },
  klausur_offen: { label: 'Nur Klausur fehlt', tone: 'violet' },
  abgeschlossen: { label: 'Abgeschlossen', tone: 'teal' },
}

export const TONE_CLASSES = {
  rose: 'bg-rose-100 text-rose-800 dark:bg-rose-500/15 dark:text-rose-300',
  amber: 'bg-amber-100 text-amber-800 dark:bg-amber-500/15 dark:text-amber-300',
  teal: 'bg-teal-100 text-teal-800 dark:bg-teal-500/15 dark:text-teal-300',
  slate: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
  sky: 'bg-sky-100 text-sky-800 dark:bg-sky-500/15 dark:text-sky-300',
  violet: 'bg-violet-100 text-violet-800 dark:bg-violet-500/15 dark:text-violet-300',
}

export const BAR_CLASSES = {
  rose: 'bg-rose-500',
  amber: 'bg-amber-500',
  teal: 'bg-teal-500',
  slate: 'bg-slate-400',
  sky: 'bg-sky-500',
  violet: 'bg-violet-500',
}

export function formatDate(iso) {
  if (!iso) return ''
  return new Date(`${iso}T00:00:00`).toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

export function num(n) {
  return Number(n).toLocaleString('de-DE', { maximumFractionDigits: 1 })
}

// Ein Satz zur Prognose eines Lesepensums (task = Antwort des Lesenachweis-Dienstes).
export function forecastText(task) {
  const f = task.forecast
  const per = (n) => `${num(n)} ${task.unit} pro Tag`
  const deadline = formatDate(task.deadline)
  switch (f.status) {
    case 'done':
      return 'Geschafft, alles gelesen.'
    case 'overdue': {
      const days = -f.days_left
      return `Die Frist ist seit ${days} ${days === 1 ? 'Tag' : 'Tagen'} vorbei. Es fehlen noch ${num(f.remaining)} ${task.unit}.`
    }
    case 'not_started':
      return f.needed_per_day
        ? `Noch nichts gelesen. Bis ${deadline} sind ${per(f.needed_per_day)} nötig.`
        : 'Noch nichts gelesen.'
    case 'open':
      return f.projected_finish
        ? `Ohne Frist. Bei ${per(f.pace_per_day)} bist du am ${formatDate(f.projected_finish)} fertig.`
        : 'Ohne Frist. In den letzten 14 Tagen wurde nichts gelesen.'
    case 'behind':
      return f.projected_finish
        ? `Zurzeit ${per(f.pace_per_day)}, nötig sind ${per(f.needed_per_day)}. Bei diesem Tempo wirst du erst am ${formatDate(f.projected_finish)} fertig (Frist ${deadline}).`
        : `In den letzten 14 Tagen wurde nichts gelesen. Bis ${deadline} sind ${per(f.needed_per_day)} nötig.`
    default: // on_track, tight
      return `Bei ${per(f.pace_per_day)} bist du am ${formatDate(f.projected_finish)} fertig (Frist ${deadline}). Nötig sind ${per(f.needed_per_day)}.`
  }
}

// Arten einer Aufgabe (Standard für alle): Beschriftung, Symbol und wie die Frist heißt. Die Art bestimmt, welche Felder
// das Formular zeigt (`umfang` = Soll/Ist/Einheit, z. B. Seiten einer Ausarbeitung). Weitere Arten kommen hier dazu.
export const AUFGABEN_ARTEN = {
  allgemein: { label: 'Aufgabe', icon: 'aufgaben', frist: 'Frist', hinweis: 'Eine einfache Aufgabe zum Abhaken.' },
  klausur: { label: 'Klausur', icon: 'kalender', frist: 'Termin', hinweis: 'Mit Termin; zeigt „Nur Klausur fehlt“, wenn nur sie offen ist.' },
  ausarbeitung: { label: 'Ausarbeitung', icon: 'stift', frist: 'Abgabe', umfang: true, hinweis: 'Texte verfassen, Register schreiben … mit Umfang und Stand.' },
}
export const artInfo = (art) => AUFGABEN_ARTEN[art] || AUFGABEN_ARTEN.allgemein

// „in 12 Tagen“ / „heute“ / „seit 3 Tagen vorbei“ – für Termine und Abgaben
export function tageBisText(iso, heute = new Date()) {
  if (!iso) return ''
  const tage = Math.round((new Date(`${iso}T00:00:00`) - new Date(heute.getFullYear(), heute.getMonth(), heute.getDate())) / 86400000)
  if (tage === 0) return 'heute'
  if (tage === 1) return 'morgen'
  return tage > 0 ? `in ${tage} Tagen` : `seit ${-tage} ${tage === -1 ? 'Tag' : 'Tagen'} vorbei`
}
