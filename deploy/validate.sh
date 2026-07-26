#!/bin/bash
set -euo pipefail

# ──────────────────────────────────────────────────────────────
# validate.sh — YAML szintaktikai ellenőrzés
# ──────────────────────────────────────────────────────────────

REPO_DIR="${1:-.}"
DASHBOARD_DIR="$REPO_DIR/dashboard"
ERRORS=0

echo "Validating YAML files in $DASHBOARD_DIR ..."

# Python YAML parser HA-specifikus tag-ekkel
validate_yaml() {
    local file="$1"
    python3 -c "
import yaml, sys

class HALoader(yaml.SafeLoader):
    pass

def ha_include(loader, node):
    return None

def ha_include_dir(loader, node):
    return None

HALoader.add_constructor('!include', ha_include)
HALoader.add_constructor('!include_dir_list', ha_include_dir)
HALoader.add_constructor('!include_dir_named', ha_include_dir)
HALoader.add_constructor('!include_dir_merge_list', ha_include_dir)
HALoader.add_constructor('!include_dir_merge_named', ha_include_dir)

try:
    with open('$file', 'r', encoding='utf-8') as f:
        yaml.load(f, Loader=HALoader)
    print(f'  OK: $file')
except yaml.YAMLError as e:
    print(f'  ERROR: $file')
    print(f'  {e}', file=sys.stderr)
    sys.exit(1)
" 2>&1
}

# Dashboard fő fájl
if [ -f "$DASHBOARD_DIR/dashboard.yaml" ]; then
    validate_yaml "$DASHBOARD_DIR/dashboard.yaml" || ERRORS=$((ERRORS + 1))
else
    echo "  WARNING: dashboard.yaml not found"
    ERRORS=$((ERRORS + 1))
fi

# View fájlok
for view in "$DASHBOARD_DIR/views/"*.yaml; do
    if [ -f "$view" ]; then
        validate_yaml "$view" || ERRORS=$((ERRORS + 1))
    fi
done

# Custom card-ok
for card in "$DASHBOARD_DIR/cards/"*.yaml; do
    if [ -f "$card" ]; then
        validate_yaml "$card" || ERRORS=$((ERRORS + 1))
    fi
done

# Theme-ek
for theme in "$DASHBOARD_DIR/themes/"*.yaml; do
    if [ -f "$theme" ]; then
        validate_yaml "$theme" || ERRORS=$((ERRORS + 1))
    fi
done

if [ $ERRORS -gt 0 ]; then
    echo ""
    echo "Validation FAILED: $ERRORS error(s) found."
    exit 1
else
    echo ""
    echo "All YAML files valid."
    exit 0
fi
