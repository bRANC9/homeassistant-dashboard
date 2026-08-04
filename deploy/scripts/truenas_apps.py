import json
import os
import re
import ssl
import time
import urllib.request

from truenas_ws import TrueNASWS, load_credentials, rest_call

ssl_ctx = ssl._create_unverified_context()

# ── Docker Hub rate-limit cache ─────────────────────────────
# File-based cache with TTL so the 30s command_line sensor does not hammer
# hub.docker.com on every scan (anonymous API is rate limited).
CACHE_FILE = os.environ.get("DOCKER_HUB_CACHE", "/tmp/truenas_dockerhub_cache.json")
CACHE_TTL = 24 * 3600          # 24h
MAX_QUERIES_PER_SCAN = 12       # cap fresh lookups per sensor scan

_hub_cache = {}
_hub_fresh_queries = 0


def _load_cache():
    global _hub_cache
    try:
        with open(CACHE_FILE) as f:
            _hub_cache = json.load(f)
    except Exception:
        _hub_cache = {}


def _save_cache():
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(_hub_cache, f)
    except Exception:
        pass


def query_docker_hub_cached(image):
    """Return latest stable tag from cache (TTL) or a fresh Docker Hub query."""
    global _hub_cache, _hub_fresh_queries
    if not image:
        return None
    entry = _hub_cache.get(image)
    now = time.time()
    if entry and (now - entry.get("ts", 0)) < CACHE_TTL:
        return entry.get("version") or None
    if _hub_fresh_queries >= MAX_QUERIES_PER_SCAN:
        return (entry.get("version") or None) if entry else None
    version = _query_docker_hub(image)
    _hub_cache[image] = {"version": version, "ts": now}
    _hub_fresh_queries += 1
    if len(_hub_cache) > 500:
        _hub_cache = dict(list(_hub_cache.items())[-250:])
    _save_cache()
    return version


def _query_docker_hub(image):
    if "/" not in image:
        image = "library/" + image
    url = "https://hub.docker.com/v2/repositories/" + image + "/tags/?page_size=100&ordering=last_updated"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "HeliosDashboard/1.0"})
        with urllib.request.urlopen(req, timeout=5, context=ssl_ctx) as resp:
            data = json.loads(resp.read())
        skip = ("latest", "beta", "alpha", "rc", "nightly", "edge", "dev", "test",
                "unstable", "stable", "openssl", "armhf", "amd64", "aarch64",
                "preview", "canary", "snapshot", "head", "master", "main", "develop")
        for tag in data.get("results", []):
            name = tag.get("name", "")
            low = name.lower()
            if any(s in low for s in skip):
                continue
            if "sha-" in low:
                continue
            if not re.match(r'^v?\d+\.\d+', low):
                continue
            return name
    except Exception:
        pass
    return None


KNOWN_IMAGES = {
    "adguard_home": "adguard/adguardhome",
    "jackett": "jackett/jackett",
    "immich": "immichapp/immich",
    "frigate": "blakeblackshear/frigate",
    "pangolin": "fosrl/pangolin",
    "seerr": "fallenbagel/jellyseerr",
    "sonarr": "linuxserver/sonarr",
    "radarr": "linuxserver/radarr",
    "transmission": "linuxserver/transmission",
    "jellyfin": "jellyfin/jellyfin",
    "grafana": "grafana/grafana",
    "netdata": "netdata/netdata",
    "mosquitto": "eclipse-mosquitto",
    "esphome": "esphome/esphome",
    "watchtower": "containrrr/watchtower",
    "azure_agent": "oznu/cloudflare-ddns",
    "homeassistant": "home-assistant/home-assistant",
    "zigbee2mqtt": "koenkk/zigbee2mqtt",
}


def extract_image_from_config(cfg):
    if not cfg:
        return None
    for key in ("image", "docker_image", "container_image", "repo", "repository"):
        val = cfg.get(key)
        if val and isinstance(val, str):
            return val
    for list_key in ("images", "docker_images", "containers"):
        images = cfg.get(list_key)
        if isinstance(images, list) and images:
            first = images[0]
            if isinstance(first, dict):
                return first.get("image") or first.get("repository") or first.get("repo")
            if isinstance(first, str):
                return first
    return None


def find_docker_image(app_name, app_data, ws):
    img = extract_image_from_config(app_data.get("config"))
    if img:
        return img
    img = app_data.get("image")
    if img:
        return img
    if ws is not None:
        try:
            detail = ws.call("app.get_instance", [app_data.get("id", app_name)])
            if detail:
                img = extract_image_from_config(detail.get("config"))
                if img:
                    return img
                img = detail.get("image")
                if img:
                    return img
        except Exception:
            pass
    clean = app_name.replace("-", "_")
    if clean in KNOWN_IMAGES:
        return KNOWN_IMAGES[clean]
    return None


def main():
    _load_cache()
    api_key, auth_header = load_credentials()

    ws = None
    try:
        ws = TrueNASWS(api_key=api_key)
        apps = ws.call("app.query")
        alerts_raw = ws.call("alert.list")
    except Exception:
        if ws is not None:
            ws.close()
            ws = None
        apps = rest_call("app.query", auth_header=auth_header) or []
        alerts_raw = rest_call("alert.list", auth_header=auth_header) or []

    result = {}
    for a in apps:
        aid = a["id"].replace("-", "_")
        entry = {k: a.get(k) for k in [
            "name", "id", "state", "upgrade_available", "latest_version",
            "image_updates_available", "custom_app", "migrated",
            "human_version", "version"
        ]}
        aw = a.get("active_workloads") or {}
        if isinstance(aw, dict):
            entry["containers"] = aw.get("containers", 0)
            ports = []
            for p in aw.get("used_ports", []):
                for hp in p.get("host_ports", []):
                    if hp.get("host_port"):
                        ports.append(hp["host_port"])
            entry["ports"] = ports[:3]
        else:
            entry["containers"] = aw
            entry["ports"] = []
        portals = a.get("portals") or {}
        entry["portal_url"] = ""
        if isinstance(portals, dict):
            for v in portals.values():
                if v:
                    entry["portal_url"] = v
                    break
        elif isinstance(portals, list) and portals:
            entry["portal_url"] = portals[0]
        notes = a.get("notes", "")
        entry["notes"] = notes[:200] if notes else ""
        is_custom = a.get("custom_app", False)
        has_native_update = bool(entry.get("latest_version"))
        entry["docker_hub_version"] = ""
        entry["docker_hub_url"] = ""
        if is_custom and not has_native_update:
            docker_image = find_docker_image(a.get("name", aid), a, ws)
            if docker_image:
                entry["docker_image"] = docker_image
                hub_ver = query_docker_hub_cached(docker_image)
                if hub_ver:
                    entry["docker_hub_version"] = hub_ver
                    normalized = docker_image if "/" in docker_image else "library/" + docker_image
                    entry["docker_hub_url"] = "https://hub.docker.com/r/" + normalized + "/tags"
        result[aid] = entry

    alerts = []
    for al in alerts_raw:
        if al.get("dismissed"):
            continue
        alerts.append({
            "level": al.get("level", "INFO"),
            "title": al.get("source") or al.get("klass", ""),
            "message": (al.get("formatted") or al.get("text") or "")[:200],
        })

    if ws is not None:
        ws.close()

    print(json.dumps({"apps": result, "alerts": alerts}))


if __name__ == "__main__":
    main()
