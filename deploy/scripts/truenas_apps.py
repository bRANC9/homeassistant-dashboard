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

apps = []
if api_header:
    req = urllib.request.Request(
        "http://192.168.1.250:88/api/v2.0/app",
        headers={"Authorization": api_header}
    )
    try:
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            apps = json.loads(resp.read())
    except Exception:
        pass

result = {}
for a in apps:
    aid = a["id"].replace("-", "_")
    entry = {k: a.get(k) for k in [
        "name", "id", "state", "upgrade_available", "latest_version",
        "image_updates_available", "custom_app", "migrated",
        "human_version", "version"
    ]}
    # active_workloads returns a dict, extract container count and ports
    aw = a.get("active_workloads", {}) or {}
    if isinstance(aw, dict):
        entry["containers"] = aw.get("containers", 0)
        ports = []
        for p in aw.get("used_ports", []):
            for hp in p.get("host_ports", []):
                if hp.get("host_port"):
                    ports.append(hp["host_port"])
        entry["ports"] = ports[:3]  # max 3 ports
    else:
        entry["containers"] = aw
        entry["ports"] = []
    # extract first portal URL
    portals = a.get("portals", {}) or {}
    entry["portal_url"] = ""
    if isinstance(portals, dict):
        for v in portals.values():
            if v:
                entry["portal_url"] = v
                break
    elif isinstance(portals, list) and portals:
        entry["portal_url"] = portals[0]
    # truncate notes to 200 chars to avoid attribute size issues
    notes = a.get("notes", "")
    entry["notes"] = notes[:200] if notes else ""
    result[aid] = entry
print(json.dumps({"apps": result}))
