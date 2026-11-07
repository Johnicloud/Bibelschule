# Bibelschule auf Proxmox betreiben

Die App ist ein Docker-Compose-Stack, braucht also nichts Proxmox-Spezifisches: eine Linux-VM mit Docker genügt.
**Nicht auf einer echten Proxmox-Installation ausprobiert** – die Schritte sind aus der Compose-Datei abgeleitet.

## 1. VM
Debian 12 / Ubuntu 24.04, 2 Kerne, **8 GB RAM** (die Texterkennung gescannter Skripte braucht Arbeitsspeicher; unter 6 GB
wird sie vom System beendet), 40 GB Platte (Skripte, Audio und Video werden schnell groß). Autostart der VM: „Start at boot“.

```bash
curl -fsSL https://get.docker.com | sh
git clone <dein-repo> bibelschule && cd bibelschule
docker network create ki        # wird von docker-compose.override.yml erwartet (auch ohne Ollama)
cp .env.example .env            # OLLAMA_URL anpassen oder leer lassen (KI-Funktionen sind dann aus)
docker compose up -d --build
./neues-konto.sh "DeinName" "DeinPasswort"
```
Danach läuft die App unter `http://<vm-ip>:8170` (nur im Heimnetz verwenden).

## 2. HTTPS von außen (Caddy)
1. `deploy/proxmox/Caddyfile`: `bibelschule.example.de` durch die eigene Adresse ersetzen (DNS zeigt auf die VM,
   Router leitet 80 und 443 an die VM).
2. Start mit dem Zusatz (schließt Port 8170 nach außen, Caddy übernimmt):
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.override.yml -f deploy/proxmox/docker-compose.proxmox.yml up -d --build
   ```
3. Nur Heimnetz ohne eigene Adresse: im Caddyfile die Domain durch `bibelschule.lan` und eine Zeile `tls internal` ersetzen;
   der Browser fragt einmal nach dem Zertifikat.

Statt Caddy geht auch WireGuard/Tailscale (dann gar kein Port nach außen) – meist die sicherere Wahl.

## 3. Sichern
Alles liegt in `./data` (Fächer, Karten, Skripte samt Textfassungen). Proxmox-Sicherung der VM **oder** `rsync -a ./data
/sicherung/`. Die Dienste legen zusätzlich täglich Kopien der Angaben in `backups/` ab (nicht der Dateien selbst).

## 4. Wichtig
- Anmeldung ist Pflicht, `/api/registry` ist absichtlich offen (nur intern im Docker-Netz) – deshalb nie einzelne Dienste
  veröffentlichen, nur Caddy (443).
- Sitzungen liegen im Speicher: nach einem Neustart des Kerns muss man sich neu anmelden.
- Upload-Grenze: 200 MB je Datei (Dienst und nginx), im Caddyfile 250 MB.
- Docker-Speicher: bei Docker Desktop (Mac) ggf. in den Einstellungen auf 8 GB erhöhen, auf einer Linux-VM gilt der RAM der VM.
