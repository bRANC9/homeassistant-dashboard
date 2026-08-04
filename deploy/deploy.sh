#!/bin/bash
set -euo pipefail

# ──────────────────────────────────────────────────────────────
# deploy.sh — Git pull + validate + copy + HA reload
# Közvetlen mount-al működik (nem kell SSH)
# ──────────────────────────────────────────────────────────────

REPO_DIR="${DEPLOY_REPO_DIR:-/deploy/repo}"
HA_CONFIG="${HA_CONFIG_PATH:-/ha-config}"
DASHBOARD_SRC="$REPO_DIR/dashboard"
DASHBOARD_DST="$HA_CONFIG/www/helios-dashboard"
LOG_FILE="${DEPLOY_LOG:-/deploy/deploy.log}"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

log "=== Deploy started ==="
log "Event: ${WEBHOOK_REF:-push}"

# ── 0. Webhook HMAC verification ─────────────────────────────
# Ha a WEBHOOK_SECRET be van állítva (setup.sh generálja), a GitHub
# X-Hub-Signature-256 fejlécet ellenőrizzük a nyers payload alapján.
# A webhook a PAYLOAD és X_HUB_SIGNATURE_256 env-eket adja át (hooks.json).
if [ -n "${WEBHOOK_SECRET:-}" ]; then
    log "Verifying webhook signature..."
    if ! python3 -c "import hashlib, hmac, os, sys; \
sig=os.environ.get('X_HUB_SIGNATURE_256', ''); \
payload=os.environ.get('PAYLOAD', ''); \
expected='sha256=' + hmac.new(os.environ.get('WEBHOOK_SECRET', '').encode(), payload.encode(), hashlib.sha256).hexdigest(); \
sys.exit(0 if hmac.compare_digest(sig, expected) else 1)"; then
        log "ERROR: Webhook signature mismatch — aborting deploy."
        exit 1
    fi
    log "Webhook signature OK."
else
    log "WARNING: WEBHOOK_SECRET not set, skipping signature check."
fi

# ── 1. Git pull ──────────────────────────────────────────────
cd "$REPO_DIR"

# Git safe directory beállítás (Docker volume ownership miatt)
git config --global --add safe.directory "$REPO_DIR"

# Első futáskor clone-oljuk a repot
if [ ! -d ".git" ]; then
    log "First run — cloning repository..."
    git clone https://github.com/bRANC9/homeassistant-dashboard.git .
fi

log "Pulling latest changes..."
git fetch origin main 2>&1 | tee -a "$LOG_FILE"
git reset --hard origin/main 2>&1 | tee -a "$LOG_FILE"
git clean -fd 2>&1 | tee -a "$LOG_FILE"
COMMIT=$(git rev-parse --short HEAD)
log "HEAD: $COMMIT"

# ── 2. Validate YAML ────────────────────────────────────────
log "Validating YAML files..."
bash /deploy/validate.sh "$REPO_DIR"
if [ $? -ne 0 ]; then
    log "ERROR: YAML validation failed! Aborting deploy."
    exit 1
fi
log "YAML validation passed."

# ── 3. Copy dashboard files ─────────────────────────────────
log "Copying dashboard to $DASHBOARD_DST ..."
mkdir -p "$DASHBOARD_DST/views"
mkdir -p "$DASHBOARD_DST/cards"
mkdir -p "$DASHBOARD_DST/templates"
mkdir -p "$DASHBOARD_DST/command_line"
mkdir -p "$DASHBOARD_DST/scripts"
mkdir -p "$HA_CONFIG/themes"
mkdir -p "$HA_CONFIG/templates"

cp "$DASHBOARD_SRC/dashboard.yaml" "$DASHBOARD_DST/"

for view in "$DASHBOARD_SRC/views/"*.yaml; do
    [ -f "$view" ] && cp "$view" "$DASHBOARD_DST/views/"
done

for card in "$DASHBOARD_SRC/cards/"*.yaml; do
    [ -f "$card" ] && cp "$card" "$DASHBOARD_DST/cards/"
done

for template in "$DASHBOARD_SRC/templates/"*.yaml; do
    [ -f "$template" ] && cp "$template" "$DASHBOARD_DST/templates/"
done

for cmdline in "$DASHBOARD_SRC/command_line/"*.yaml; do
    [ -f "$cmdline" ] && cp "$cmdline" "$DASHBOARD_DST/command_line/"
done

for script in "$REPO_DIR/deploy/scripts/"*.py; do
    [ -f "$script" ] && cp "$script" "$DASHBOARD_DST/scripts/"
done

for tpl in "$REPO_DIR/deploy/templates/"*.yaml; do
    [ -f "$tpl" ] && cp "$tpl" "$HA_CONFIG/templates/"
done

# Replace the source placeholder only in the deployed copy. This keeps the
# repository deterministic while the Homelab view shows the running build.
grep -rl "__HELIOS_BUILD__" "$DASHBOARD_DST" 2>/dev/null | while read -r f; do
    sed -i "s/__HELIOS_BUILD__/${COMMIT}/g" "$f"
done

for theme in "$DASHBOARD_SRC/themes/"*.yaml; do
    [ -f "$theme" ] && cp "$theme" "$HA_CONFIG/themes/"
done

log "Dashboard files copied."

# Megjegyzés: a configuration.yaml-ban a dashboard key-nek kötőjelesnek kell lennie:
# lovelace:
#   dashboards:
#     helios-dashboard:  <-- kötőjel kötelező!
#       mode: yaml
#       title: Helios
#       icon: mdi:view-dashboard
#       show_in_sidebar: true
#       filename: www/helios-dashboard/dashboard.yaml

# ── 4. HA notifications (optional) ────────────────────────────
log "Notifying HA..."
if [ -n "${HA_TOKEN:-}" ]; then
    for TARGET in sm_s921b desktop_nia5fgv; do
        CODE=$(curl -s -o /dev/null -w "%{http_code}" \
            -X POST \
            -H "Authorization: Bearer $HA_TOKEN" \
            -H "Content-Type: application/json" \
            -d "{\"message\": \"Dashboard deployed: $COMMIT\", \"title\": \"Helios Deploy\"}" \
            "${HA_URL}/api/services/notify/${TARGET}" 2>/dev/null || echo "000")
        log "notify.${TARGET}: HTTP $CODE"
    done
else
    log "HA_TOKEN not set, skipping notifications."
    log "NOTE: YAML dashboard auto-reloads on browser refresh (HA 2026+)."
fi

log "=== Deploy completed ==="
