import json, os, ssl, urllib.request
ctx = ssl._create_unverified_context()

api_header = ""
try:
    with open("/config/secrets.yaml") as f:
        for line in f:
            if line.strip().startswith("truenas_api_header"):
                api_header = line.split(":", 1)[1].strip().strip('"').strip("'")
except Exception:
    pass

def api_get(path):
    if not api_header:
        return None
    req = urllib.request.Request(
        "http://192.168.1.250:88" + path,
        headers={"Authorization": api_header}
    )
    try:
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            return json.loads(resp.read())
    except Exception:
        return None

def query_docker_hub(image):
    if not image:
        return None
    if "/" not in image:
        image = "library/" + image
    url = "https://hub.docker.com/v2/repositories/" + image + "/tags/?page_size=30&ordering=last_updated"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "HeliosDashboard/1.0"})
        with urllib.request.urlopen(req, timeout=5, context=ctx) as resp:
            data = json.loads(resp.read())
        skip = ("latest", "beta", "alpha", "rc", "nightly", "edge", "dev", "test")
        for tag in data.get("results", []):
            name = tag.get("name", "")
            if len(name) > 30:
                continue
            low = name.lower()
            if any(s in low for s in skip):
                continue
            if "sha-" in low:
                continue
            return name
    except Exception:
        pass
    return None

def extract_image_from_config(cfg):
    if not cfg:
        return None
    for key in ("image", "docker_image", "container_image"):
        val = cfg.get(key)
        if val and isinstance(val, str):
            return val
    images = cfg.get("images")
    if isinstance(images, list) and images:
        first = images[0]
        if isinstance(first, dict):
            return first.get("image") or first.get("repository")
        if isinstance(first, str):
            return first
    return None

apps = api_get("/api/v2.0/app") or []

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
    docker_image = extract_image_from_config(a.get("config"))
    if not docker_image:
        docker_image = a.get("image")
    entry["docker_image"] = docker_image or ""
    entry["docker_hub_version"] = ""
    entry["docker_hub_url"] = ""
    is_custom = a.get("custom_app", False)
    has_native_update = bool(entry.get("latest_version"))
    if is_custom and not has_native_update:
        if not docker_image:
            detail = api_get("/api/v2.0/app/" + str(a.get("id", "")))
            if detail:
                docker_image = extract_image_from_config(detail.get("config"))
                if not docker_image:
                    docker_image = detail.get("image")
        if docker_image:
            entry["docker_image"] = docker_image
            hub_ver = query_docker_hub(docker_image)
            if hub_ver:
                entry["docker_hub_version"] = hub_ver
                normalized = docker_image if "/" in docker_image else "library/" + docker_image
                entry["docker_hub_url"] = "https://hub.docker.com/r/" + normalized + "/tags"
    result[aid] = entry

alerts_raw = api_get("/api/v2.0/alert") or []
alerts = []
for al in alerts_raw:
    if al.get("dismissed"):
        continue
    alerts.append({
        "level": al.get("level", "INFO"),
        "title": al.get("source") or al.get("klass", ""),
        "message": (al.get("formatted") or al.get("text") or "")[:200],
    })

print(json.dumps({"apps": result, "alerts": alerts}))
