#!/bin/bash
set -euo pipefail

# ── Startup deploy ──
# Watchtower frissítés után azonnal lehúzza a legfrissebb verziót
echo "[startup] Running initial deploy..."
bash /deploy/deploy.sh || echo "[startup] WARNING: Initial deploy failed, continuing anyway..."

# ── Start webhook server ──
echo "[startup] Starting webhook server..."
exec webhook -hooks /etc/webhook/hooks.json -verbose
