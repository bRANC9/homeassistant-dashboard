import json, os, ssl, sys, urllib.request
ctx = ssl._create_unverified_context()

api_header = ""
try:
    with open("/config/secrets.yaml") as f:
        for line in f:
            if line.strip().startswith("truenas_api_header"):
                api_header = line.split(":", 1)[1].strip().strip('"').strip("'")
except Exception:
    pass

base = "http://192.168.1.250:88/api/v2.0"
req = urllib.request.Request(
    base + "/cronjob",
    headers={"Authorization": api_header}
)
try:
    with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
        jobs = json.loads(resp.read())
except Exception as e:
    print(json.dumps({"error": str(e)}))
    sys.exit(1)

target = sys.argv[1] if len(sys.argv) > 1 else ""

if target == "list":
    out = {}
    for j in jobs:
        desc = j.get("description") or j.get("command", "?")
        out[str(j["id"])] = desc
    print(json.dumps(out))
elif target == "run":
    name = sys.argv[2] if len(sys.argv) > 2 else ""
    match = None
    for j in jobs:
        desc = j.get("description") or j.get("command", "")
        if name.lower() in desc.lower():
            match = j
            break
    if not match:
        print(json.dumps({"error": f"cron job '{name}' not found"}))
        sys.exit(1)
    jid = match["id"]
    run_req = urllib.request.Request(
        base + f"/cronjob/{jid}/run",
        data=b"{}",
        headers={"Authorization": api_header, "Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(run_req, timeout=30, context=ctx) as resp:
            result = json.loads(resp.read())
        print(json.dumps({"status": "triggered", "job": match.get("description") or match.get("command"), "result": result}))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
else:
    print(json.dumps({"usage": "list | run <name>"}))
