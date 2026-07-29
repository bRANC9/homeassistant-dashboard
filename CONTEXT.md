# Home Assistant Dashboard — Session Context

## Projekt cél
Moduláris, Git-vezérelt Home Assistant dashboard (Helios) TrueNAS-on futó HA példányhoz. Automatikus deploy GitHub webhook → Docker container segítségével. Minden logika template szenzorokban, a nézetek csak megjelenítés.

## Fontos szabályok
- Minden módosítás után: `git add -A && git commit -m "..." && git push`
- Mielőtt bármit pusholsz, validáld YAML-el: `python -c "import yaml; yaml.safe_load(open('file.yaml'))"`
- A webhook container induláskor automatikusan deploy-ol (entrypoint.sh). Kézi deploy: `docker exec ha-dashboard-webhook bash /deploy/deploy.sh`
- Dashboard filozófia: **nincs logika a nézetekben** — minden Jinja2 a template szenzorokban (`deploy/templates/templates.yaml`)
- `sections` view típus: **nincs `horizontal-stack`**, `max_columns` ≥ legnagyobb `grid_options.columns`
- `decluttering-card` `variables` formátuma: lista, nem map (`- key: value`)
- `browser_mod.popup` helyes szintaxis: `service: browser_mod.popup`, `content:` (nem `card:`)

## Repo struktúra
```
dashboard/
  dashboard.yaml          — fő dashboard (decluttering_templates, views include)
  templates/
    decluttering.yaml     — decluttering template-k (sensor_chip, entity_chip, docker_tile, stb.)
  views/
    home.yaml             — Home: status chips, Power Flow, EV, Pool/Weather, climate, fények
    energy.yaml           — Energy: ApexCharts, PV forecast
    ev.yaml               — EV: IONIQ 5, wallbox, smart charging
    pool.yaml             — Pool: pump, hőmérséklet, timer, időjárás
    basement.yaml         — Basement: WoL, szerver szoba
    basement_terrace.yaml — Terasz: világítás, szenzorok
    homelab.yaml          — Homelab: rendszer állapot, TrueNAS Docker tile-ok, Zigbee2MQTT
  cards/
    deployment_version.yaml — build verzió (__HELIOS_BUILD__ placeholder)
  themes/
    helios.yaml           — Mushroom theme
deploy/
  Dockerfile              — almir/webhook + bash/curl/git/python3/pyyaml
  docker-compose.yml      — container konfig, HA config mount, user: root
  entrypoint.sh           — startup: deploy.sh futtatása, majd webhook server indítás
  deploy.sh               — git pull → validate → copy → HA reload + notification
  validate.sh             — YAML validáció HA tag-ekkel
  hooks.json              — webhook trigger: X-GitHub-Event: push
  setup.sh                — első beállítás
  templates/
    templates.yaml        — template szenzorok (TrueNAS app status, EV colors, pool, stb.)
.github/workflows/
  docker-build.yml        — CI: build + push to GHCR, majd webhook notify
docs/
  entity-inventory.md     — entitás lista domain-enként
```

## Dashboard views
| View | Path | Leírás |
|------|------|--------|
| Home | `/home` | Napi áttekintés, climate, fények |
| Energy | `/energy` | PV, hálózat, akku, fogyasztás |
| EV | `/ev` | IONIQ 5, töltés, timezone |
| Pool | `/pool` | Medence szivattyú, hőmérséklet, időjárás |
| Basement | `/basement` | Iroda, szerver szoba |
| Basement Terrace | `/basement-terrace` | Terasz |
| Homelab | `/homelab` | TrueNAS, Z2M, rendszer |

## MCP eszközök
- **Home Assistant MCP** — dashboard kezelés, entitások, szolgáltatások, konfig
  - Használat: `remote-server_*` eszközök
- **TrueNAS MCP** — TrueNAS kezelés (pools, apps, datasets, shares)
  - Használat: `truenas_*` eszközök

## Végpontok
- **HA (belső)**: `http://192.168.1.250:8123`
- **HA (külső, Pangolin)**: `https://home.kerekmuvek.hu`
- **TrueNAS Web UI**: `https://192.168.1.250:444` vagy `http://192.168.1.250:88`
- **TrueNAS API (REST)**: `http://192.168.1.250:88/api/v2.0/` (HTTP, self-signed cert miatt)
  - ApiKey: **(TrueNAS UI-ban nézd meg / regeneráld!)**
- **Webhook deploy URL**: `https://ha-dash-deploy.kerekmuvek.hu/hooks/ha-dashboard-deploy`
- **GitHub repo**: `https://github.com/bRANC9/homeassistant-dashboard` (public)
- **GHCR image**: `ghcr.io/branc9/homeassistant-dashboard/ha-dashboard-webhook:latest`

## TrueNAS / Infra
- TrueNAS 25.10.4 (Goldeye), Intel i7-7700K, 32GB RAM
- Pools: `backup` (3.7TB), `docker` (232GB SSD), `storage` (93TB HDD, 90% teljes ⚠️)
- Docker apps: 17 fut, 3 stop (cod4x, minecraft, nodered)
- Watchtower fut (automatikus container update)
- Docker container név konvenció: `ix-{app_name}-{service_name}`
- TrueNAS API app control: `POST /app/start`, `POST /app/stop` (nincs `/app/restart`)
- HA container: `https://home.kerekmuvek.hu` (külső URL a docker-compose-ban)

## HACS custom card-ok (telepítve)
decluttering-card, mushroom-card, bubble-card, mini-graph-card, apexcharts-card, auto-entities, button-card, card-mod, layout-card

## Integrációk (telepítve)
browser_mod, TrueNAS CE (HACS), template szenzorok, rest_command

## Notify entitások
- `notify.sm_s921b` — telefon
- `notify.desktop_nia5fgv` — desktop
- `notify.franci` — Franci
- `notify.galaxy_watch6_classic_xseb` — óra

## Jelenlegi állapot
- HA verzió: 2026.7.4
- Utolsó commit (pusholva): 037b513
- Utolsó deploy-olt commit: c628fb1 (webhook nem deploy-olta a legújabb commit-okat — kézi deploy kell: `docker exec ha-dashboard-webhook bash /deploy/deploy.sh`)
- HA deprecated REST API warning — 38 hívás/24h; JSON-RPC 2.0 WebSocket-re kell váltani 26.04 előtt

## Build verzió
- A `deployment_version.yaml` card a Homelab view-ban mutatja a deploy-olt commit hash-t
- Minden push után a deploy script (`deploy.sh`) a `__HELIOS_BUILD__` helyére teszi a rövid commit hash-t
- A deploy után a Homelab view alján látszik: "Helios Dashboard — {hash}"

## Ismert hibák / TODO
1. **Deploy mechanism issues** — webhook 200-at ad de nem frissül; valószínűleg Docker volume git pull probléma; repo publikus, de `git config --global safe.directory` kellhet
2. **HA scripts needed** — restart script (stop → delay → start) a TrueNAS API-n keresztül, mivel nincs `/app/restart` endpoint
3. **HA REST API deprecated** — deploy.sh átírása JSON-RPC 2.0 WebSocket-re 26.04 előtt
4. **Docker socket** — csak monitoringra (`command_line` sensor), control TrueNAS API-n keresztül
5. **`horizontal-stack` a popup tartalomban** — a Fények popup `vertical-stack` → `horizontal-stack`-et használ, ami popup-on belül OK, de sections view-ban nem
