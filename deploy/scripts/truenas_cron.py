import json
import sys

from truenas_ws import TrueNASWS, load_credentials, rest_call


def main():
    api_key, auth_header = load_credentials()

    try:
        ws = TrueNASWS(api_key=api_key)
        jobs = ws.call("cronjob.query")
        ws_failed = False
    except Exception:
        ws = None
        jobs = rest_call("cronjob.query", auth_header=auth_header) or []
        ws_failed = True

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
        try:
            if ws is not None:
                result = ws.call("cronjob.run", [jid])
            else:
                result = rest_call("cronjob.run", [jid], auth_header=auth_header)
            print(json.dumps({
                "status": "triggered",
                "job": match.get("description") or match.get("command"),
                "result": result,
            }))
        except Exception as e:
            print(json.dumps({"error": str(e)}))
            sys.exit(1)
    else:
        print(json.dumps({"usage": "list | run <name>"}))

    if ws is not None:
        ws.close()
    sys.exit(0 if not ws_failed else 0)


if __name__ == "__main__":
    main()
