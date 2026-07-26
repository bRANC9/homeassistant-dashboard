# Home Assistant Dashboard

A modular, Git-managed Home Assistant dashboard for daily control of energy, EV, pool, basement, and homelab systems.

## Views

| View | Path | Description |
|------|------|-------------|
| Home | `/home` | Daily overview and control centre |
| Energy | `/energy` | PV, grid, battery, and consumption charts |
| EV | `/ev` | IONIQ 5 status, charging controls, scheduling |
| Pool | `/pool` | Pump control, temperature, lighting |
| Basement | `/basement` | Office, server room, sensors |
| Basement Terrace | `/basement-terrace` | Terrace lighting and future devices |
| Homelab | `/homelab` | TrueNAS, Zigbee2MQTT, system health |

## Custom Cards Required

Install via HACS before activating this dashboard:

- Mushroom Cards
- Bubble Card
- ApexCharts Card
- Mini Graph Card
- Auto Entities
- Button Card
- Card Mod
- Layout Card

## Setup

1. Copy `dashboard/dashboard.yaml` to your HA config directory
2. Register the dashboard in `configuration.yaml` (see deployment docs)
3. Copy view files to the appropriate location
4. Restart Home Assistant or reload the dashboard

### Theme

Helios uses a small local Mushroom theme to make status icons easier to read. Ensure that
`configuration.yaml` loads the Home Assistant `themes` directory:

```yaml
frontend:
  themes: !include_dir_merge_named themes
```

The deployment copies `dashboard/themes/helios.yaml` to `<HA_CONFIG_PATH>/themes/helios.yaml`.

The Homelab view also displays the short Git commit hash of the deployed dashboard build.

## Deployment

Automatikus deploy webhook-al: a webhook container a TrueNAS-on fut és mount-olva van a HA config könyvtár.

```
GitHub push → webhook container (TrueNAS-on) → git pull → validate
    → copy fájlok (közvetlen mount) → HA reload
```

### Docker image

A GitHub Actions automatikusan buildeli és publikálja a webhook containert a GitHub Container Registry-ben (`ghcr.io`). TrueNAS-on csak le kell húzni:

```bash
docker pull ghcr.io/branc9/homeassistant-dashboard/ha-dashboard-webhook:latest
```

### Gyors beállítás

```bash
cd deploy
bash setup.sh       # Generál webhook secret + .env
# Szerkeszd a .env fájlt (HA_CONFIG_PATH, HA_TOKEN)
docker compose up -d
```

### .env beállítás

| Változó | Leírás |
|---------|--------|
| `WEBHOOK_SECRET` | GitHub webhook HMAC titkos kulcs |
| `HA_CONFIG_PATH` | HA config könyvtár a TrueNAS-on (pl. `/mnt/pool/homeassistant/config`) |
| `HA_TOKEN` | HA long-lived access token |
| `HA_URL` | HA API elérhetősége (pl. `http://localhost:8123`) |

### GitHub Webhook

1. Repo → Settings → Webhooks → Add webhook
2. Payload URL: `http://TRUENAS_IP:9000/hooks/ha-dashboard-deploy`
3. Content type: `application/json`
4. Secret: a setup.sh által generált érték
5. Events: Just the push event
6. Branch: `main`

### HA configuration.yaml (a TrueNAS-on)

```yaml
lovelace:
  dashboards:
    helios-dashboard:
      mode: yaml
      title: Helios
      icon: mdi:view-dashboard
      show_in_sidebar: true
      filename: www/helios-dashboard/dashboard.yaml
```

### Fájlok

| Fájl | Cél |
|------|-----|
| `deploy/Dockerfile` | Webhook container image build |
| `deploy/docker-compose.yml` | Webhook container (HA config mount-olva) |
| `deploy/hooks.json` | Webhook szabályok + HMAC validáció |
| `deploy/deploy.sh` | Git pull → validate → copy → HA reload |
| `deploy/validate.sh` | YAML szintaktikai ellenőrzés |
| `deploy/setup.sh` | Első beállítás, secret generálás |
| `.github/workflows/docker-build.yml` | CI: Docker image build + push to GHCR |
