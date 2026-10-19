#!/bin/sh
# Legt einen neuen Dienst aus der Vorlage an und trägt ihn in docker-compose.override.yml ein.
#   ./neuer-dienst.sh vokabeln "Vokabeln"
# Danach: docker compose up --build -d   (der Dienst meldet sich selbst beim Kern an und erscheint in der Oberfläche)
set -e
cd "$(dirname "$0")"
name="$1"
label="${2:-$1}"

case "$name" in
  ""|[!a-z]*|*[!a-z0-9-]*) echo "Name: Kleinbuchstaben, Ziffern und Bindestrich, beginnt mit einem Buchstaben (z. B. vokabeln)."; exit 1;;
esac
case "$name" in
  subjects|services|sync|overview|registry|health|docs|redoc|kern|frontend) echo "Der Name \"$name\" ist vergeben."; exit 1;;
esac
case "$label" in
  *"|"*|*"&"*|*"\\"*) echo "Der Anzeigename darf | & \\ nicht enthalten."; exit 1;;
esac
[ -e "$name" ] && { echo "Den Ordner \"$name\" gibt es schon."; exit 1; }

cp -R dienst-vorlage "$name"
find "$name" -name __pycache__ -type d -prune -exec rm -rf {} +
find "$name" -type f \( -name '*.py' -o -name '*.html' -o -name '*.txt' -o -name Dockerfile \) \
  -exec sed -i.bak "s|__NAME__|$name|g; s|__LABEL__|$label|g" {} +
find "$name" -name '*.bak' -type f -delete

[ -f docker-compose.override.yml ] || printf 'services:\n' > docker-compose.override.yml
block_file=$(mktemp)
trap 'rm -f "$block_file"' EXIT
cat > "$block_file" <<EOF
  $name:
    build: ./$name
    environment:
      KERN_URL: http://kern:8000
      SERVICE_URL: http://$name:8000
    volumes:
      - ./data/$name:/app/data
    restart: unless-stopped
EOF
# Direkt nach "services:" einfügen, nicht ans Dateiende anhängen – sonst landet der neue Dienst unter einem
# späteren Top-Level-Schlüssel wie "networks:" (falsch eingerückt, kaputtes YAML). Der Block kommt über eine
# Datei statt über -v: macOS' awk ("one true awk") bricht bei -v mit einem mehrzeiligen String ab
# ("newline in string"), eine Datei mit getline liest dagegen auf jedem awk portabel.
awk -v bf="$block_file" '{print} /^services:/ && !done {while ((getline line < bf) > 0) print line; close(bf); done=1}' \
  docker-compose.override.yml > docker-compose.override.yml.tmp
mv docker-compose.override.yml.tmp docker-compose.override.yml

echo "Dienst \"$label\" liegt in ./$name und ist in docker-compose.override.yml eingetragen."
echo "Starten: docker compose up --build -d"
