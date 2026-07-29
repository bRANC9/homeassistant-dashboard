import json, os, sys, urllib.request

try:
    import yaml
    with open("/config/secrets.yaml") as f:
        secrets = yaml.safe_load(f)
except Exception as e:
    print(json.dumps({"error": f"secrets error: {e}"}))
    sys.exit(1)

api_header = secrets.get("truenas_api_header", "")
if not api_header:
    print(json.dumps({"error": "truenas_api_header not found"}))
    sys.exit(1)

req = urllib.request.Request(
    "http://192.168.1.250:88/api/v2.0/app",
    headers={"Authorization": api_header}
)
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        apps = json.loads(resp.read())
except Exception as e:
    print(json.dumps({"error": f"API failed: {e}"}))
    sys.exit(1)

result = {}
for a in apps:
    aid = a["id"].replace("-", "_")
    result[aid] = a.get("state", "UNKNOWN")
    result[aid + "_containers"] = a.get("active_containers", 0)
    result[aid + "_update_avail"] = a.get("upgrade_available", False)
print(json.dumps(result))
