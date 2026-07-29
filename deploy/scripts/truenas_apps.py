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
    result[aid] = {
        "state": a.get("state", "UNKNOWN"),
        "containers": a.get("active_containers", 0),
        "update_avail": a.get("upgrade_available", False),
    }
print(json.dumps({"apps": result}))
