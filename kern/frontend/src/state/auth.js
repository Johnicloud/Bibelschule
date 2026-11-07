// Angemeldet-Status, geräteweit über alle Komponenten hinweg sichtbar. loggedIn: null = noch unbekannt
// (erste Prüfung läuft), true/false danach. http.js setzt loggedIn=false, sobald irgendein Aufruf 401 bekommt
// (z. B. Sitzung abgelaufen) – so springt die Oberfläche überall zuverlässig zum Login zurück.
import { ref } from 'vue'

export const loggedIn = ref(null)
export const username = ref('')
export const isAdmin = ref(false)
export const vorname = ref('')
export const nachname = ref('')
export const gemeinde = ref('')
// Ein Admin hat das Passwort zurückgesetzt: die Oberfläche zeigt dann erst die Pflicht-Seite "Neues Passwort
// wählen" (PasswortAendernView.vue), bevor sie den Rest der App freigibt.
export const mussPasswortAendern = ref(false)
// Hinweistext auf der Anmeldeseite nach automatischer Abmeldung (wie bei der Finanzapp: "Du wurdest nach X
// Minuten ohne Benutzung abgemeldet."), gesetzt von App.vue beim Inaktivitäts-Logout, geleert beim nächsten
// erfolgreichen Anmelden.
export const abmeldeHinweis = ref('')
