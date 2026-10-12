// Kartentypen mit Farbe; Klassen stehen ausgeschrieben da, damit Tailwind sie findet.
export const KINDS = {
  classic: {
    label: 'Umdrehen',
    hint: 'Frage und Antwort, du bewertest dich selbst',
    badge: 'bg-teal-100 text-teal-800 dark:bg-teal-500/15 dark:text-teal-300',
  },
  choice: {
    label: 'Multiple Choice',
    hint: 'Vier Antworten, eine ist richtig',
    badge: 'bg-violet-100 text-violet-800 dark:bg-violet-500/15 dark:text-violet-300',
  },
  truefalse: {
    label: 'Richtig/Falsch',
    hint: 'Eine Aussage, die stimmt oder nicht',
    badge: 'bg-sky-100 text-sky-800 dark:bg-sky-500/15 dark:text-sky-300',
  },
}
