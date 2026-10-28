<script setup>
// Eine Stelle für alle Symbole der Oberfläche (Lucide-ähnliche Strichzeichnungen, wie auch die Finanzapp sie nutzt,
// dort aber ohne zentrale Datei – hier gebündelt, damit neue Symbole nicht in jeder Komponente neu gezeichnet werden).
const props = defineProps({ name: { type: String, required: true } })

const PATHS = {
  faecher: 'M12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83zM2 12a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 12M2 17a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 17',
  karten: 'M2 7a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V7zM14 7.5l4.4-1.6a2 2 0 0 1 2.6 1.2l2.7 9.4a2 2 0 0 1-1.2 2.6L18 20.5',
  adressbuch: 'M16 11a4 4 0 1 0-8 0 4 4 0 0 0 8 0zM4 21v-1a6 6 0 0 1 6-6h4a6 6 0 0 1 6 6v1',
  lernen: 'M13 2 3 14h7l-1 8 10-12h-7l1-8z',
  aufgaben: 'M9 11l2 2 4-4M5 5h14v14H5V5z',
  lesenachweis: 'M3 5a2 2 0 0 1 2-2h6v18H5a2 2 0 0 1-2-2V5zM21 5a2 2 0 0 0-2-2h-6v18h6a2 2 0 0 0 2-2V5z',
  register: 'M4 4h16v4H4V4zM4 11h16v2H4v-2zM4 16h10v2H4v-2z',
  bibelverse: 'M19 21 12 16 5 21V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z',
  uebersicht: 'M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM13 13h7v7h-7z',
  skripte: 'M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zM14 2v6h6M8 13h8M8 17h8',
  baustein: 'M12 2l3 2v4l3-2 3 2v6l-3 2v4l-3-2-3 2v-4l-3-2V6l3-2z',
  stift: 'M4 20h4L19.5 8.5a2.1 2.1 0 0 0-3-3L5 17v3zM13.5 6.5l3 3',
  plus: 'M12 5v14M5 12h14',
  chevron: 'M6 9l6 6 6-6',
  zurueck: 'M19 12H5M12 19l-7-7 7-7',
  vor: 'M5 12h14M12 5l7 7-7 7',
  haken: 'M20 6 9 17l-5-5',
  kalender: 'M8 2v4M16 2v4M3 10h18M5 4h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z',
  noten: 'M4 20h3v-6H4v6zM10.5 20h3V9h-3v11zM17 20h3V4h-3v16z',
  buch: 'M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H19a1 1 0 0 1 1 1v18a1 1 0 0 1-1 1H6.5a1 1 0 0 1 0-5H20M12.5 6v8M9.5 9h6',
  bibliothek: 'M3 21h18M4 21V5a1 1 0 0 1 1-1h3a1 1 0 0 1 1 1v16M10 21V9a1 1 0 0 1 1-1h3a1 1 0 0 1 1 1v12M16 21V7a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v14',
  x: 'M6 6l12 12M18 6 6 18',
  stoppuhr: 'M10 2h4M12 14 15 11M12 6a8 8 0 1 0 0 16 8 8 0 0 0 0-16z',
  predigten: 'M11 6a13 13 0 0 0 8.4-2.8A1 1 0 0 1 21 4v12a1 1 0 0 1-1.6.8A13 13 0 0 0 11 14H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2zM6 14a12 12 0 0 0 2.4 7.2 2 2 0 0 0 3.2-2.4A8 8 0 0 1 10 14M8 6v8',
  notizen: 'M21 9a2.4 2.4 0 0 0-.706-1.706l-3.588-3.588A2.4 2.4 0 0 0 15 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2zM15 3v5a1 1 0 0 0 1 1h5',
  funken: 'M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0zM20 3v4M22 5h-4M4 17v2M5 18H3',
  tempo: 'M12 14l4-4M3.34 19a10 10 0 1 1 17.32 0',
  mehr: 'M5 12h.01M12 12h.01M19 12h.01',
  verknuepfen: 'M10 13a5 5 0 0 0 7.5.5l3-3a5 5 0 0 0-7-7l-1.7 1.7M14 11a5 5 0 0 0-7.5-.5l-3 3a5 5 0 0 0 7 7l1.7-1.7',
  papierkorb: 'M3 6h18M8 6V4a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v2M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6M10 11v6M14 11v6',
  glossar: 'M3 20h5.5a8 8 0 1 1 7 0H21',
}

const path = () => PATHS[props.name] || PATHS.baustein
</script>

<template>
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
    <path :d="path()" />
  </svg>
</template>
