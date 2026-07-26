#!/bin/bash
set -euo pipefail

# ──────────────────────────────────────────────────────────────
# setup.sh — Első beállítás
# ──────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"
ENV_EXAMPLE="$SCRIPT_DIR/.env.example"

echo "╔══════════════════════════════════════════════════╗"
echo "║  Helios Dashboard — Deployment Setup            ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

if [ -f "$ENV_FILE" ]; then
    echo ".env file already exists."
    read -p "Overwrite? (y/N): " OVERWRITE
    if [ "$OVERWRITE" != "y" ] && [ "$OVERWRITE" != "Y" ]; then
        echo "Keeping existing .env"
        exit 0
    fi
fi

cp "$ENV_EXAMPLE" "$ENV_FILE"

SECRET=$(openssl rand -hex 32 2>/dev/null || python3 -c "import secrets; print(secrets.token_hex(32))")
sed -i "s|CHANGE_ME_TO_A_RANDOM_SECRET|$SECRET|" "$ENV_FILE" 2>/dev/null || \
sed -i '' "s|CHANGE_ME_TO_A_RANDOM_SECRET|$SECRET|" "$ENV_FILE" 2>/dev/null || true

echo "Generated webhook secret: $SECRET"
echo ""
echo "=== Next steps ==="
echo ""
echo "1. Szerkeszd a .env fájlt:"
echo "   - HA_CONFIG_PATH: HA config könyvtár a TrueNAS-on"
echo "   - HA_TOKEN: HA long-lived access token"
echo "   - HA_URL: HA API elérhetősége"
echo ""
echo "2. HA configuration.yaml-ban add hozzá:"
echo ""
echo "   lovelace:"
echo "     dashboards:"
echo "       helios:"
echo "         mode: yaml"
echo "         title: Helios"
echo "         icon: mdi:view-dashboard"
echo "         show_in_sidebar: true"
echo "         filename: www/helios-dashboard/dashboard.yaml"
echo ""
echo "3. GitHub webhook beállítás:"
echo "   - Payload URL: http://TRUENAS_IP:9000/hooks/ha-dashboard-deploy"
echo "   - Content type: application/json"
echo "   - Secret: $SECRET"
echo "   - Events: Just the push event"
echo "   - Branch: main"
echo ""
echo "4. TrueNAS-on indítsd el:"
echo "   cd deploy && docker compose up -d"
echo ""
