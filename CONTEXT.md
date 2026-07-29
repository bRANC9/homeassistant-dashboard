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
  command_line/
    truenas_apps.yaml     — REST sensor config (TrueNAS app állapotok lekérése)
deploy/
  Dockerfile              — almir/webhook + bash/curl/git/python3/pyyaml
  docker-compose.yml      — container konfig, HA config mount, user: root
  entrypoint.sh           — startup: deploy.sh futtatása, majd webhook server indítás
  deploy.sh               — git pull → validate → copy → HA reload + notification
  validate.sh             — YAML validáció HA tag-ekkel
  hooks.json              — webhook trigger: X-GitHub-Event: push
  setup.sh                — első beállítás
  scripts/
    truenas_apps.py       — Python script: TrueNAS API → JSON (app state, containers)
  templates/
    templates.yaml        — template szenzorok (EV colors, pool, Z2M, TrueNAS update)
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
  - REST sensor használja app állapot lekérésre: `command_line` → `deploy/scripts/truenas_apps.py`
  - API key `secrets.yaml`-ban: `truenas_api_header: "Bearer <key>"`
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
- **App control HA-ból: `truenas_ce.app_start` / `truenas_ce.app_stop`** (TrueNAS CE integration, target: `binary_sensor.truenas_apps_<name>`)
- **App restart**: `script.truenas_app_restart` (stop → 5s delay → start)
- `truenas_ce.system_refresh` — azonnali állapotfrissítés
- **App state lekérés**: `command_line` sensor + `deploy/scripts/truenas_apps.py` (Python script, API key a secrets.yaml-ból)
  - `sensor.truenas_apps_state` — JSON attribútumokban: `<app_name>` → RUNNING/STOPPED/DEPLOYING/CRASHED, `<app_name>_containers`, `<app_name>_update_avail`
  - scan_interval: 30s
- `docker_tile` template: state/color-t a `[[app_name]]`-ből számolja (`state_attr` a REST sensor attribútumaiból)
- Per-app color template szenzorok **eltávolítva** — a `docker_tile` template inline számolja a színt
- HA container: `https://home.kerekmuvek.hu` (külső URL a docker-compose-ban)

## TrueNAS Control (saját HACS integration)
- **Repo (WS-only, TrueNAS 26+)**: `https://github.com/bRANC9/ha-truenas-control`
- **Helyi másolat**: `G:\PycharmProjects\ha-truenas-control`
- **Domain**: `truenas_ws` — WebSocket JSON-RPC 2.0, nincs REST
- **Port**: 9443 (TrueNAS 26 default API port)
- **Entitások**:
  - `sensor.truenas_ws_version` — TrueNAS verzió
  - `sensor.truenas_ws_cpu_usage` — CPU %
  - `sensor.truenas_ws_memory_usage` — Memória %
  - `sensor.truenas_ws_pool_<name>_usage` — Pool használat %
  - `sensor.truenas_ws_pool_<name>_available` — Pool szabad hely
  - `sensor.truenas_ws_disk_<name>_temperature` — Diszk hőmérséklet
  - `sensor.truenas_ws_app_<name>_version` — App verzió
  - `binary_sensor.truenas_ws_app_<name>` — App fut?
  - `binary_sensor.truenas_ws_pool_<name>_healthy` — Pool egészséges?
  - `binary_sensor.truenas_ws_service_<name>` — Service fut?
  - `switch.truenas_ws_app_<name>` — App start/stop
- **Service**: `truenas_ws.restart_app` (stop → delay → start)
- Teendő: renderelés után add hozzá HACS-hez custom repo-ként

## TrueNAS Apps Manager (régi, REST alapú)
- **Repo**: `https://github.com/bRANC9/ha-truenas-apps` (külön repo, v0.3.0-ig)
- Dual transport (WS+REST), de deprecated — TrueNAS 26-hoz a fenti kell
- Eltávolítandó HA-ból amint a `truenas_ws` működik

## HACS custom card-ok (telepítve)
decluttering-card, mushroom-card, bubble-card, mini-graph-card, apexcharts-card, auto-entities, button-card, card-mod, layout-card

## Integrációk (telepítve)
browser_mod, TrueNAS CE (HACS), template szenzorok, rest_command (már nem használjuk — TrueNAS CE app_start/app_stop váltotta ki)

## Notify entitások
- `notify.sm_s921b` — telefon
- `notify.desktop_nia5fgv` — desktop
- `notify.franci` — Franci
- `notify.galaxy_watch6_classic_xseb` — óra

## Jelenlegi állapot
- HA verzió: 2026.7.4
- Utolsó commit (pusholva): 037b513 → bővítve REST sensor + restart script
- Utolsó deploy-olt commit: c628fb1 (webhook nem deploy-olta a legújabb commit-okat — kézi deploy kell: `docker exec ha-dashboard-webhook bash /deploy/deploy.sh`)
- REST sensor (`sensor.truenas_apps_state`) folyamatosan lekéri a TrueNAS app állapotokat (30 másodpercenként)
- `script.truenas_app_restart` létrehozva HA-ban
- HA deprecated REST API warning — 38 hívás/24h; JSON-RPC 2.0 WebSocket-re kell váltani 26.04 előtt

## Mit csináltunk eddig (session history condensed)
- Teljes dashboard struktúra kialakítva (7 view, decluttering template-k, deploy pipeline)
- TrueNAS CE integration telepítve → app control `truenas_ce.app_start/stop`
- `command_line` REST sensor létrehozva TrueNAS API-hoz (real app states: RUNNING, DEPLOYING, STOPPED, CRASHED)
- `docker_tile` template frissítve: Restart gomb, Activity szekció, inline state/color számolás
- Régi per-app binary_sensor alapú color szenzorok eltávolítva
- `script.truenas_app_restart` létrehozva HA-ban (stop → delay → start)
- API key `secrets.yaml`-ban (user által beállítva TrueNAS-on)

## Build verzió
- A `deployment_version.yaml` card a Homelab view-ban mutatja a deploy-olt commit hash-t
- Minden push után a deploy script (`deploy.sh`) a `__HELIOS_BUILD__` helyére teszi a rövid commit hash-t
- A deploy után a Homelab view alján látszik: "Helios Dashboard — {hash}"

## Ismert hibák / TODO
1. ~~**Deploy mechanism issues** — webhook 200-at ad de nem frissül; repo újra publikálva, safe.directory fix~~ (javítva)
2. ~~**HA scripts needed** — restart script (stop → delay → start) a TrueNAS API-n keresztül~~ → **megoldva**: `script.truenas_app_restart`
3. **HA REST API deprecated** — deploy.sh átírása JSON-RPC 2.0 WebSocket-re 26.04 előtt
4. **rest_command-ok eltávolítása a TrueNAS configuration.yaml-ből** — már nem használt, de a régi API key-es bejegyzések ott vannak
5. ~~**`horizontal-stack` a popup tartalomban**~~ (nem releváns)
6. **`secrets.yaml`-ban `truenas_api_header` beállítva** — user által TrueNAS-on (nem commit-olva)
7. **`command_line: !include www/helios-dashboard/command_line/truenas_apps.yaml` hozzáadása a configuration.yaml-hez** — user által TrueNAS-on
8. **Old `rest_command` API kulcs eltávolítása** — user feladata TrueNAS-on
