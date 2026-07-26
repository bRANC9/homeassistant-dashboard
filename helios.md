# Project Helios — Home Assistant Dashboard Migration Handoff

**Purpose:** continue the Home Assistant dashboard migration in Codex Work Mode from the current conversation state.

## Objective

Build a new, modular, Git-managed Home Assistant dashboard beside the existing dashboard. The new dashboard should be a polished, responsive daily control centre for energy, EV, pool, basement, basement terrace and homelab monitoring—without breaking the current working dashboard.

The final project should be deployable from GitHub through a self-hosted webhook container on the user's TrueNAS/homelab environment. Start with dashboard files only; do not migrate the entire Home Assistant configuration unless explicitly requested later.

## Repository

- GitHub repository: `https://github.com/bRANC9/homeassistant-dashboard.git`
- Expected default branch: `main`
- The repository was reported as empty when last inspected in the prior conversation.
- Desired workflow: make changes on feature branches, then open a draft PR to `main`.

Before making changes in Work Mode:

1. Clone/open the repository locally.
2. Check `git status`, remotes, default branch and existing files.
3. Do **not** assume the repository is still empty.

## Source files already uploaded in the prior chat

The user previously attached Home Assistant storage/configuration files. Their contents are not present in this handoff, so obtain them again from the user or locate them in the active workspace before generating entity-specific YAML.

Reported filenames:

- `lovelace.lovelace` — believed to contain the primary dashboard
- `lovelace_dashboards` — dashboard registry/list
- `lovelace_resources` — Lovelace/HACS resources
- `lovelace` — a separate “Pool Control” dashboard
- `lovelace.map` — map dashboard configuration

Likely source location for a Storage Mode dashboard: `/config/.storage/`. These files are Home Assistant internal JSON-style storage files; preserve them as read-only source material and do not edit them in place.

Also request or inspect, where available:

- `configuration.yaml` (especially `lovelace:` and dashboard registration)
- existing themes, `www/`, custom templates and any dashboard YAML files
- a current screenshot of the dashboard on desktop and mobile
- the actual entity IDs for every retained card/integration

## Confirmed platform state

- Current dashboard uses **Storage Mode** and includes a Sections-based layout.
- The existing Sunsynk Power Flow card is important and should be retained with its current entity mappings and configuration.
- `show_daily: true` must remain enabled in the power-flow configuration.
- The user installed `layout-card` and reported installing most recommended dashboard additions.

## Expected installed custom cards/integrations

Treat this list as user-reported; verify exact resource URLs and card types from `lovelace_resources` before using them.

- Mushroom
- layout-card
- card-mod
- ApexCharts Card
- Auto-Entities
- Bubble Card
- Bubble Card Tools
- Button Card
- Mini Graph Card
- likely Decluttering Card and Browser Mod

Do not require Bar Card. It was not found and is explicitly unnecessary.

## Design and architecture decisions

### Migration strategy

- Preserve the existing Storage Mode dashboard as a safe fallback.
- Create a **new YAML-mode dashboard** for the redesigned UI.
- Keep the dashboard project separate from the full Home Assistant configuration at first, so secrets and unrelated automations are not committed.
- Convert/recreate only the relevant presentation layer from the storage dashboard after entity IDs have been confirmed.

### Dashboard views

Planned views:

1. **Home** — daily overview/control centre
2. **Energy** — charts and energy analysis
3. **EV** — Hyundai/Ioniq and charging controls/status
4. **Pool** — pool controls, temperature, pump/runtime, lighting
5. **Basement** — office/server/sensors/controls
6. **Basement Terrace** — initially a light; designed for future devices
7. **Homelab** — TrueNAS, containers, HA, network and service health
8. Optional **Settings** — shortcuts/secondary controls

### Visual system

- Mobile-first, responsive layout with `layout-card`; desktop should use available width cleanly.
- Use Mushroom for standard controls/status, Bubble Card selectively for high-value summary panels, ApexCharts for analytical graphs, and Auto-Entities for dynamic lists/alerts.
- Avoid excessive horizontal stacks and legacy Glance cards.
- Prefer function/room-oriented labels over raw entity names.
- Keep cards spacious and scannable; do not place every available sensor on Home.

Suggested semantic colors:

| Domain | Color |
| --- | --- |
| Solar | Yellow |
| Battery | Green |
| Grid | Blue |
| EV | Purple |
| Pool | Orange |
| Alerts | Red |
| Homelab | Neutral |

### Reusable components

Build reusable YAML components/templates where they genuinely reduce duplication:

- status chips
- room temperature/humidity card
- light/device control card
- climate card
- summary device card (EV, pool, battery, homelab service)
- alert/dynamic entity list

Use Home Assistant-compatible YAML inclusion patterns. Do not over-engineer templates before the actual source entities are known.

## Home view requirements

The first real milestone is a usable Home view. Planned content, in rough order:

1. Header chips: solar power, house load, battery SOC, EV SOC, pool temperature, outdoor/indoor temperature.
2. Existing Sunsynk Power Flow card, retained with `show_daily: true`.
3. EV summary: SOC, range, connected/charging, charge power, optional target SOC and estimated ready time.
4. Pool summary: water temperature, pump state, runtime/remaining runtime, lighting.
5. Weather and PV forecast.
6. Quick lights, including the basement-terrace light.
7. Climate controls replacing old Glance cards.
8. House temperature/humidity overview.
9. Alerts/system health: unavailable devices, low batteries, critical service/inverter status.
10. Optional quick automation controls: solar mode, smart charging, pool auto, night mode—only when real entities are supplied.

Specific agreed change: combine terrace temperature and humidity into one `mini-graph-card` with a secondary Y-axis when those entities are known.

## Other view requirements

### Energy

- Move detailed history/analysis out of Home.
- Use ApexCharts for PV, grid import/export, battery charge/discharge, house load, EV and pool; add boiler/climate only if measured entities exist.
- Provide 24-hour, 7-day and 30-day perspectives where recorder statistics support them.

### Basement Terrace

- Begin with the existing light.
- Provide intentional placeholders or a scalable section for future outlets, WLED, camera, speaker, motion, temperature/humidity, heater and fan.
- Do not create controls for nonexistent entities.

### Homelab

- Surface only integrations/entities actually present: TrueNAS, Docker, Home Assistant, Frigate, Jellyfin, backups, internet, MQTT and Zigbee were discussed as candidates.

## Deployment objective (later phase)

Desired path:

```text
GitHub push → GitHub webhook → self-hosted webhook container → validation → local checkout update → Home Assistant refresh/reload
```

The user prefers a webhook-based model over GitHub Actions SSH deployment, to avoid granting GitHub SSH access to the homelab.

Suggested implementation candidate: `adnanh/webhook` container with:

- a dedicated endpoint for this dashboard repository
- a shared secret/signature validation appropriate for GitHub webhook events
- branch filtering: deploy only `main`
- a deploy script that validates before replacing the live files
- logs and a non-destructive failure path

Important deployment caveats to validate during implementation:

- GitHub must be able to reach the webhook endpoint. This needs a secure public ingress/reverse proxy, VPN/tunnel, or a different trigger mechanism; do not expose an unauthenticated webhook port.
- Home Assistant YAML dashboards need an explicit registration/mount in `configuration.yaml` or the relevant dashboard configuration. The repository alone cannot make the dashboard appear.
- Resource reload, dashboard/config reload, and browser refresh behavior differ. Confirm the smallest safe refresh action against the user's Home Assistant version and deployment before automating it.
- Never use `git reset --hard` against a directory containing user-edited live config unless that directory is explicitly a disposable deployment checkout and its target is verified.
- Keep HA API tokens and webhook secrets outside Git (`.env`, secret store, or Home Assistant secrets).

## Proposed repository layout

Start simple and adapt after checking the source dashboard and HA include support:

```text
homeassistant-dashboard/
├── README.md
├── .gitignore
├── dashboard/
│   ├── dashboard.yaml
│   ├── views/
│   │   ├── home.yaml
│   │   ├── energy.yaml
│   │   ├── ev.yaml
│   │   ├── pool.yaml
│   │   ├── basement.yaml
│   │   ├── basement_terrace.yaml
│   │   └── homelab.yaml
│   ├── cards/
│   ├── templates/
│   ├── themes/
│   └── images/
├── deploy/
│   ├── docker-compose.yml
│   ├── hooks.json
│   └── deploy.sh
├── scripts/
│   ├── lint.sh
│   └── validate.sh
├── docs/
│   ├── entity-inventory.md
│   └── deployment.md
└── .github/
    └── workflows/
```

Do not promise that every directory will be used; create files only when they have a clear responsibility.

## Immediate implementation sequence in Codex Work Mode

1. Open/clone the repository locally and inspect its state.
2. Locate or ask the user to reattach the five Storage Mode files and `configuration.yaml`.
3. Parse `lovelace.lovelace` and produce an entity/card inventory; identify custom-card dependencies and the exact Sunsynk Power Flow block.
4. Ask only for any entity mappings not discoverable from the files (notably forecast, EV target/ready-time, homelab status and future terrace devices).
5. Create an initial project branch and baseline structure with a clear README, `.gitignore` and migration notes.
6. Implement the YAML dashboard registration/integration plan without changing the old dashboard.
7. Create the Home view first, using verified entity IDs and the preserved Sunsynk card configuration.
8. Validate YAML and custom-card availability; have the user test in HA with desktop/mobile screenshots.
9. Add Energy, EV, Pool, Basement, Basement Terrace and Homelab views iteratively.
10. Only after the dashboard renders correctly, implement and test the webhook deployment path in a staging/check-out location.

## Guardrails

- Do not invent entity IDs or controls that may accidentally point to the wrong device.
- Do not edit `.storage` files directly.
- Do not remove the existing dashboard until the new YAML dashboard has been tested and accepted.
- Do not commit `.storage` files, API tokens, webhook secrets, `.env` files, SSH keys, passwords or a full HA config containing secrets.
- Do not expose a webhook endpoint without authentication and ingress restrictions.
- Preserve `show_daily: true` in the Sunsynk Power Flow card.

## Success criteria

- New dashboard is available alongside the old one.
- Home view is usable on desktop and phone and retains accurate live values.
- No existing automations/integrations are broken.
- Dashboard configuration is readable, modular enough to maintain, and tracked in Git.
- Deploy mechanism is documented and only automated once validated safely.

