// Vermittelt zwischen weit entfernten Komponenten, die auf eine Bibelstelle verweisen (Register-Verweise,
// Suchtreffer, …), und dem Bibel-Reiter: statt die rohe PDF zu öffnen, setzt ein Klick diese Stelle und
// App.vue wechselt in den Bibel-Reiter; BibelView.vue liest sie aus und schlägt sie dort nach (nachschlagen).
import { ref } from 'vue'

export const zielBibelstelle = ref(null)
