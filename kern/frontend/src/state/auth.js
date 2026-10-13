// Angemeldet-Status, geräteweit über alle Komponenten hinweg sichtbar. loggedIn: null = noch unbekannt
// (erste Prüfung läuft), true/false danach. http.js setzt loggedIn=false, sobald irgendein Aufruf 401 bekommt
// (z. B. Sitzung abgelaufen) – so springt die Oberfläche überall zuverlässig zum Login zurück.
import { ref } from 'vue'

export const loggedIn = ref(null)
export const username = ref('')
export const isAdmin = ref(false)
