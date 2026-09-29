#!/usr/bin/env python3
"""
MHP AI Control – lokaler Kollaborationsserver
=============================================
Startet einen HTTP-Server, der:
  • das Dashboard unter  http://localhost:8080  ausliefert
  • den gemeinsamen Zustand in  data/state.json  speichert
  • die Identität der angemeldeten Person über /.auth/me meldet

Starten:  python3 server.py
Beenden:  Ctrl+C
"""

import getpass
import json
import socket
import urllib.parse
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT       = Path(__file__).parent
STATE_FILE = ROOT / "data" / "state.json"
HTML_FILE  = ROOT / "mhp-ai-control_3.html"
PORT       = 8080


# ---------------------------------------------------------------------------
# Zustandsverwaltung (lesen / schreiben mit Konflikt-Erkennung)
# ---------------------------------------------------------------------------

def read_state():
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"state": {}, "updatedAt": None}


def write_state(new_state, base_updated_at):
    """
    Speichert neuen Zustand. Gibt den neuen updatedAt-Wert zurück,
    oder None bei einem Schreibkonflikt.
    """
    current = read_state()
    # Konflikt: jemand anderes hat seit unserem letzten Lesen geändert
    if (base_updated_at
            and current.get("updatedAt")
            and current["updatedAt"] != base_updated_at):
        return None
    now = datetime.now(timezone.utc).isoformat()
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"state": new_state, "updatedAt": now},
                  f, ensure_ascii=False, indent=2)
    return now


# ---------------------------------------------------------------------------
# HTTP-Handler
# ---------------------------------------------------------------------------

class Handler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):          # einfache Konsolenausgabe
        print(f"  {self.address_string():<15} {fmt % args}")

    # -- Hilfsmethoden -------------------------------------------------------

    def _send_json(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, path: Path):
        content = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", len(content))
        self.end_headers()
        self.wfile.write(content)

    def _path(self):
        return urllib.parse.urlparse(self.path).path

    # -- GET -----------------------------------------------------------------

    def do_GET(self):
        p = self._path()

        if p == "/api/state":
            self._send_json(200, read_state())

        elif p == "/.auth/me":
            # Systembenutzername als Identität – reicht für die Anzeige im Dashboard
            self._send_json(200, {
                "clientPrincipal": {
                    "userDetails": getpass.getuser(),
                    "userRoles": ["authenticated"],
                }
            })

        elif p in ("/", "/index.html"):
            self._send_html(HTML_FILE)

        else:
            self.send_response(404)
            self.end_headers()

    # -- PUT -----------------------------------------------------------------

    def do_PUT(self):
        if self._path() != "/api/state":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length))
        updated_at = write_state(
            body.get("state", {}),
            body.get("baseUpdatedAt"),
        )
        if updated_at is None:
            self._send_json(409, {"error": "conflict"})
        else:
            self._send_json(200, {"updatedAt": updated_at})

    # -- OPTIONS (CORS-Preflight) --------------------------------------------

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, PUT, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


# ---------------------------------------------------------------------------
# Start
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    server = HTTPServer(("", PORT), Handler)
    print(f"\n  MHP AI Control – Kollaborationsserver")
    print(f"  ════════════════════════════════════")
    print(f"  Dashboard:  http://localhost:{PORT}")
    print(f"  Zustand:    {STATE_FILE.relative_to(ROOT)}")
    print(f"  Benutzer:   {getpass.getuser()}")
    print(f"  Beenden:    Ctrl+C\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server beendet.\n")
