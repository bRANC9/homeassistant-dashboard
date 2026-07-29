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
        "human_version", "version",
        "active_workloads", "portals"
    ]}
    # truncate notes to 200 chars to avoid attribute size issues
    notes = a.get("notes", "")
    entry["notes"] = notes[:200] if notes else ""
    result[aid] = entry
print(json.dumps({"apps": result}))
