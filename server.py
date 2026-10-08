#!/usr/bin/env python3
"""
MHP AI Control – lokaler Entwicklungsserver
===========================================
Implementiert dieselbe Schnittstelle wie der Produktivbetrieb (GitHub),
damit Änderungen am Dashboard getestet werden können, ohne die echten
Daten zu verändern.

  GET  /            Dashboard (index.html)
  GET  /api/state   { state, updatedAt }
  PUT  /api/state   { state, baseUpdatedAt } → 200 { updatedAt } | 409
  GET  /api/snapshots         [{ id, at, by, label }]
  POST /api/snapshots         { id, at, by, label, state }
  GET  /api/snapshots/<id>    { id, at, by, label, state }
  GET  /.auth/me    Identität (DEV_USER oder Systembenutzer)

Starten:  python3 server.py
          DEV_USER=anna python3 server.py     # als andere Person testen
          PORT=9000 python3 server.py
Daten:    .dev-data/state.json (nicht versioniert)
"""

import getpass
import json
import os
import re
import threading
import urllib.parse
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).parent
STATE_FILE = ROOT / ".dev-data" / "state.json"
SNAPSHOT_DIR = ROOT / ".dev-data" / "snapshots"
SNAPSHOT_ID = re.compile(r"^[0-9A-Za-z-]{1,64}$")
HTML_FILE = ROOT / "index.html"
PORT = int(os.environ.get("PORT", "8080"))
MAX_BODY = 20 * 1024 * 1024

_lock = threading.Lock()


def read_state():
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"state": {}, "updatedAt": None}


def write_state(new_state, base_updated_at):
    """Speichert atomar. Gibt den neuen updatedAt-Wert zurück, None bei Konflikt."""
    with _lock:
        if read_state().get("updatedAt") != base_updated_at:
            return None
        now = datetime.now(timezone.utc).isoformat()
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp = STATE_FILE.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"state": new_state, "updatedAt": now}, f, ensure_ascii=False, indent=2)
        tmp.replace(STATE_FILE)
        return now


def list_snapshots():
    if not SNAPSHOT_DIR.exists():
        return []
    out = []
    for f in SNAPSHOT_DIR.glob("*.json"):
        with open(f, encoding="utf-8") as fh:
            d = json.load(fh)
        out.append({k: d.get(k) for k in ("id", "at", "by", "label")})
    return out


class Handler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        print(f"  {self.address_string():<15} {fmt % args}")

    def _send_json(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _path(self):
        return urllib.parse.urlparse(self.path).path

    def do_GET(self):
        p = self._path()
        if p == "/api/state":
            self._send_json(200, read_state())
        elif p == "/api/snapshots":
            self._send_json(200, list_snapshots())
        elif p.startswith("/api/snapshots/"):
            sid = p.rsplit("/", 1)[1]
            f = SNAPSHOT_DIR / f"{sid}.json"
            if SNAPSHOT_ID.match(sid) and f.exists():
                self._send_json(200, json.loads(f.read_text(encoding="utf-8")))
            else:
                self._send_json(404, {"error": "not found"})
        elif p == "/.auth/me":
            user = os.environ.get("DEV_USER") or getpass.getuser()
            self._send_json(200, {"clientPrincipal": {"userDetails": user, "userRoles": ["authenticated"]}})
        elif p in ("/", "/index.html"):
            content = HTML_FILE.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", len(content))
            self.end_headers()
            self.wfile.write(content)
        else:
            self._send_json(404, {"error": "not found"})

    def _read_body(self):
        """JSON-Body mit dict-Feld "state", sonst None (Antwort ist dann schon gesendet)."""
        length = int(self.headers.get("Content-Length", 0))
        if length > MAX_BODY:
            self._send_json(413, {"error": "payload too large"})
            return None
        try:
            body = json.loads(self.rfile.read(length))
            if not isinstance(body.get("state"), dict):
                raise ValueError
            return body
        except (ValueError, AttributeError):
            self._send_json(400, {"error": "invalid body"})
            return None

    def do_POST(self):
        if self._path() != "/api/snapshots":
            self._send_json(404, {"error": "not found"})
            return
        body = self._read_body()
        if body is None:
            return
        sid = str(body.get("id", ""))
        if not SNAPSHOT_ID.match(sid):
            self._send_json(400, {"error": "invalid id"})
            return
        SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
        (SNAPSHOT_DIR / f"{sid}.json").write_text(json.dumps(body, ensure_ascii=False, indent=2), encoding="utf-8")
        self._send_json(201, {"id": sid})

    def do_PUT(self):
        if self._path() != "/api/state":
            self._send_json(404, {"error": "not found"})
            return
        body = self._read_body()
        if body is None:
            return
        state = body["state"]
        updated_at = write_state(state, body.get("baseUpdatedAt"))
        if updated_at is None:
            self._send_json(409, {"error": "conflict"})
        else:
            self._send_json(200, {"updatedAt": updated_at})


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print("\n  MHP AI Control – lokaler Entwicklungsserver")
    print(f"  Dashboard:  http://localhost:{PORT}")
    print(f"  Daten:      {STATE_FILE.relative_to(ROOT)}")
    print(f"  Benutzer:   {os.environ.get('DEV_USER') or getpass.getuser()}")
    print("  Beenden:    Ctrl+C\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server beendet.\n")
