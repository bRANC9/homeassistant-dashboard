"""Minimal TrueNAS WebSocket (legacy DDP) JSON-RPC client — stdlib only.

Replaces the deprecated REST API (removed in TrueNAS 26.04) with the native
WebSocket transport at wss://<host>:444/websocket. Fallback to REST is kept so
the scripts still work if the WS endpoint is unreachable.

Usage:
    from truenas_ws import load_credentials, call
    key, header = load_credentials()
    apps = call("app.query", api_key=key, auth_header=header)
"""

import base64
import json
import os
import socket
import ssl
import struct
import urllib.request

DEFAULT_HOST = "192.168.1.250"
DEFAULT_WS_PORT = 444
DEFAULT_WS_PATH = "/websocket"
DEFAULT_REST_BASE = "http://192.168.1.250:88/api/v2.0"

# Per-TrueNAS env override (compose/k8s friendly), else defaults above.
HOST = os.environ.get("TRUENAS_HOST", DEFAULT_HOST)
WS_PORT = int(os.environ.get("TRUENAS_WS_PORT", str(DEFAULT_WS_PORT)))
WS_PATH = os.environ.get("TRUENAS_WS_PATH", DEFAULT_WS_PATH)
REST_BASE = os.environ.get("TRUENAS_REST_BASE", DEFAULT_REST_BASE).rstrip("/")


class WSError(Exception):
    """Raised on any WebSocket transport or protocol failure."""


class WSClosed(WSError):
    pass


def load_credentials():
    """Read truenas_api_header from /config/secrets.yaml.

    The TRUENAS_API_KEY / TRUENAS_API_HEADER env vars (if set) take precedence,
    which makes the scripts testable outside the HA container.

    Returns (api_key, auth_header). api_key is the bare key (Bearer prefix
    stripped), auth_header is the full value used for REST Authorization.
    """
    api_header = os.environ.get("TRUENAS_API_HEADER", "") or ""
    if not api_header:
        try:
            with open("/config/secrets.yaml") as f:
                for line in f:
                    if line.strip().startswith("truenas_api_header"):
                        api_header = line.split(":", 1)[1].strip().strip('"').strip("'")
                        break
        except Exception:
            pass
    key = api_header
    if key.lower().startswith("bearer "):
        key = key[7:].strip()
    if not key:
        key = os.environ.get("TRUENAS_API_KEY", "")
    return key, api_header


class TrueNASWS:
    """Connection to the TrueNAS middleware WebSocket endpoint."""

    def __init__(self, host=HOST, port=WS_PORT, path=WS_PATH, api_key="", timeout=10):
        self.host = host
        self.port = port
        self.path = path
        self.api_key = api_key
        self.timeout = timeout
        self._sock = None
        self._msg_id = 0

    # ---- low level I/O ----

    def _recv_exact(self, n):
        buf = b""
        while len(buf) < n:
            chunk = self._sock.recv(n - len(buf))
            if not chunk:
                raise WSClosed("connection closed")
            buf += chunk
        return buf

    def _ws_send_frame(self, payload):
        if isinstance(payload, str):
            payload = payload.encode()
        mask = os.urandom(4)
        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        length = len(payload)
        hdr = bytearray([0x81])  # FIN + text
        if length < 126:
            hdr.append(0x80 | length)
        elif length < 65536:
            hdr.append(0x80 | 126)
            hdr += struct.pack(">H", length)
        else:
            hdr.append(0x80 | 127)
            hdr += struct.pack(">Q", length)
        self._sock.sendall(bytes(hdr) + mask + masked)

    def _ws_send_raw(self, opcode, payload=b""):
        mask = os.urandom(4)
        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        length = len(payload)
        hdr = bytearray([0x80 | opcode])
        if length < 126:
            hdr.append(0x80 | length)
        elif length < 65536:
            hdr.append(0x80 | 126)
            hdr += struct.pack(">H", length)
        else:
            hdr.append(0x80 | 127)
            hdr += struct.pack(">Q", length)
        self._sock.sendall(bytes(hdr) + mask + masked)

    def _ws_recv_message(self):
        """Read one complete text message, handling ping/pong and fragments."""
        fragments = []
        while True:
            hdr = self._recv_exact(2)
            fin = hdr[0] & 0x80
            opcode = hdr[0] & 0x0F
            length = hdr[1] & 0x7F
            if length == 126:
                length = struct.unpack(">H", self._recv_exact(2))[0]
            elif length == 127:
                length = struct.unpack(">Q", self._recv_exact(8))[0]
            mask = self._recv_exact(4) if (hdr[1] & 0x80) else None
            data = self._recv_exact(length)
            if mask:
                data = bytes(b ^ mask[i % 4] for i, b in enumerate(data))
            if opcode == 0x9:  # ping -> pong
                self._ws_send_raw(0xA, data)
                continue
            if opcode == 0x8:  # close
                raise WSClosed("server closed connection")
            if opcode in (0x1, 0x2):  # text / binary start
                fragments = [data]
                if fin:
                    return b"".join(fragments)
            elif opcode == 0x0:  # continuation
                fragments.append(data)
                if fin:
                    return b"".join(fragments)

    # ---- protocol ----

    def _connect(self):
        raw = socket.create_connection((self.host, self.port), timeout=self.timeout)
        try:
            ctx = ssl._create_unverified_context()
            self._sock = ctx.wrap_socket(raw, server_hostname=self.host)
        except Exception:
            raw.close()
            raise
        self._handshake()

    def _handshake(self):
        key = base64.b64encode(os.urandom(16)).decode()
        req = (
            f"GET {self.path} HTTP/1.1\r\n"
            f"Host: {self.host}:{self.port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n"
            "Sec-WebSocket-Protocol: truenas_api_v2\r\n"
            "\r\n"
        )
        self._sock.sendall(req.encode())
        resp = b""
        while b"\r\n\r\n" not in resp:
            chunk = self._sock.recv(4096)
            if not chunk:
                raise WSClosed("connection closed during handshake")
            resp += chunk
        status = resp.split(b"\r\n", 1)[0]
        if b" 101 " not in status:
            raise WSError(f"handshake failed: {status.decode(errors='replace')}")

    def _send(self, payload):
        if not self.api_key:
            raise WSError("no API key configured")
        self._ws_send_frame(payload)

    def _call(self, method, params=None):
        """Send a method call and wait for the matching result."""
        self._msg_id += 1
        msg_id = self._msg_id
        self._send(json.dumps({
            "id": msg_id,
            "msg": "method",
            "method": method,
            "params": params or [],
        }))
        while True:
            try:
                data = self._ws_recv_message()
            except socket.timeout:
                raise WSError(f"timeout waiting for {method}")
            try:
                resp = json.loads(data)
            except json.JSONDecodeError:
                continue
            if resp.get("id") != msg_id:
                continue  # ignore notifications / unrelated frames
            if resp.get("msg") == "error" or "error" in resp:
                err = resp.get("error", {})
                raise WSError(f"{method}: {err.get('errname', '')} {err.get('reason', err)}")
            return resp.get("result")

    def call(self, method, params=None):
        if self._sock is None:
            self._connect()
            # DDP connect + auth handshake
            self._send(json.dumps({"msg": "connect", "version": "1", "support": ["1"]}))
            self._ws_recv_message()
            ok = self._call("auth.login_with_api_key", [self.api_key])
            if ok is not True:
                raise WSError(f"auth failed: {ok}")
        return self._call(method, params)

    def close(self):
        if self._sock is not None:
            try:
                self._sock.close()
            except Exception:
                pass
            self._sock = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


# ---- REST fallback (pre-26.04 compatibility) ----

def _rest_target(method, params):
    """Map a WS method name to a REST (method, path, body) triple."""
    if method == "app.query":
        return "GET", "/app", None
    if method == "app.get_instance":
        ident = str(params[0]) if params else ""
        return "GET", f"/app/{ident}", None
    if method == "alert.list":
        return "GET", "/alert", None
    if method == "cronjob.query":
        return "GET", "/cronjob", None
    if method == "cronjob.run":
        ident = str(params[0]) if params else ""
        return "POST", f"/cronjob/{ident}/run", {}
    raise WSError(f"no REST mapping for {method}")


def rest_call(method, params=None, auth_header=""):
    if not auth_header:
        raise WSError("no auth header configured")
    http_method, path, body = _rest_target(method, params)
    req = urllib.request.Request(
        REST_BASE + path,
        headers={"Authorization": auth_header},
        method=http_method,
    )
    if http_method == "POST":
        req.data = json.dumps(body).encode()
        req.add_header("Content-Type", "application/json")
    ctx = ssl._create_unverified_context()
    try:
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            return json.loads(resp.read())
    except Exception as e:
        raise WSError(f"REST {http_method} {path}: {e}")


def call(method, params=None, api_key="", auth_header="", timeout=10):
    """Try WebSocket first, fall back to REST on transport failure."""
    try:
        with TrueNASWS(api_key=api_key, timeout=timeout) as ws:
            return ws.call(method, params)
    except Exception:
        return rest_call(method, params, auth_header=auth_header)
