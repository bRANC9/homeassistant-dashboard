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

# ── 1. Git pull ──────────────────────────────────────────────
log "Pulling latest changes..."
cd "$REPO_DIR"
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
mkdir -p "$DASHBOARD_DST/themes"

cp "$DASHBOARD_SRC/dashboard.yaml" "$DASHBOARD_DST/"

for view in "$DASHBOARD_SRC/views/"*.yaml; do
    [ -f "$view" ] && cp "$view" "$DASHBOARD_DST/views/"
done

for card in "$DASHBOARD_SRC/cards/"*.yaml; do
    [ -f "$card" ] && cp "$card" "$DASHBOARD_DST/cards/"
done

for theme in "$DASHBOARD_SRC/themes/"*.yaml; do
    [ -f "$theme" ] && cp "$theme" "$DASHBOARD_DST/themes/"
done

log "Dashboard files copied."

# ── 4. Dashboard regisztráció ───────────────────────────────
REG_FILE="$HA_CONFIG/ui-lovelace-helios.yaml"
if [ ! -f "$REG_FILE" ]; then
    log "Creating dashboard registration file..."
    cat > "$REG_FILE" << 'EOF'
views:
  - !include www/helios-dashboard/dashboard.yaml
EOF
    log "Created $REG_FILE"
fi

# ── 5. HA reload ────────────────────────────────────────────
log "Reloading Home Assistant dashboard..."
if [ -n "${HA_TOKEN:-}" ]; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST \
        -H "Authorization: Bearer $HA_TOKEN" \
        -H "Content-Type: application/json" \
        "${HA_URL}/api/services/lovelace/reload" 2>/dev/null || echo "000")

    if [ "$HTTP_CODE" = "200" ]; then
        log "HA dashboard reloaded successfully."
    else
        log "WARNING: HA reload returned HTTP $HTTP_CODE"
    fi

    # Notification
    curl -s -X POST \
        -H "Authorization: Bearer $HA_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"message\": \"Dashboard deployed: $COMMIT\", \"title\": \"Helios Deploy\", \"data\": {\"channel\": \"ha-dashboard\"}}" \
        "${HA_URL}/api/services/mobile_app/send_notification" > /dev/null 2>&1 || true
    log "Notification sent."
else
    log "WARNING: HA_TOKEN not set, skipping HA refresh."
    log "Manual: HA → Developer Tools → Services → lovelace.reload"
fi

log "=== Deploy completed ==="
