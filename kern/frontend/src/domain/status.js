// Anzeige-Regeln: Namen der Dienste, Lesestatus, Datum, Prognosetext.
export const SERVICE_LABELS = {
  karteikarten: 'Karteikarten',
  lesenachweis: 'Lesenachweis',
  register: 'Register',
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

export const TONE_CLASSES = {
  rose: 'bg-rose-100 text-rose-800 dark:bg-rose-500/15 dark:text-rose-300',
  amber: 'bg-amber-100 text-amber-800 dark:bg-amber-500/15 dark:text-amber-300',
  teal: 'bg-teal-100 text-teal-800 dark:bg-teal-500/15 dark:text-teal-300',
  slate: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
}

export const BAR_CLASSES = {
  rose: 'bg-rose-500',
  amber: 'bg-amber-500',
  teal: 'bg-teal-500',
  slate: 'bg-slate-400',
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
