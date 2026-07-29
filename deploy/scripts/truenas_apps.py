import json, os, urllib.request

# Read API key from secrets.yaml
api_header = ""
try:
    with open("/config/secrets.yaml") as f:
        for line in f:
            if line.strip().startswith("truenas_api_header"):
                api_header = line.split(":", 1)[1].strip().strip('"').strip("'")
except Exception:
    pass

if not api_header:
    print(json.dumps({"error": "no api key"}))
else:
    req = urllib.request.Request(
        "http://192.168.1.250:88/api/v2.0/app",
        headers={"Authorization": api_header}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            apps = json.loads(resp.read())
    except Exception as e:
        print(json.dumps({"error": f"api: {e}"}))
        apps = []

    result = {}
    for a in apps:
        aid = a["id"].replace("-", "_")
        result[aid] = a.get("state", "UNKNOWN")
        result[aid + "_containers"] = a.get("active_containers", 0)
        result[aid + "_update_avail"] = a.get("upgrade_available", False)
    print(json.dumps(result))
