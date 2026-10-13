#!/bin/sh
# Legt ein Konto an (nur für eingeladene Personen, keine Selbstregistrierung über die Oberfläche):
#   ./neues-konto.sh "Johannes Löwen" "passwort123"
# Alle Konten sehen dieselben Fächer (gemeinsames Lernen) – das Konto regelt nur den Zugang.
set -e
cd "$(dirname "$0")"
if [ -z "$1" ] || [ -z "$2" ]; then
  echo "Nutzung: ./neues-konto.sh \"Benutzername\" \"Passwort (mind. 8 Zeichen)\""
  exit 1
fi
docker compose exec kern python -m app.create_account "$1" "$2"
