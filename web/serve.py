"""Serve the web client on http://localhost:3000 with its configuration taken from web/.env.

The browser can't read .env, so this server exposes the values as /config.js.
Allowlist: only index.html and config.js are served; everything else (.env included) is a 404.

Usage:
    cp .env.example .env   # then fill in the values
    python serve.py
"""

import json
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HOST, PORT = "127.0.0.1", 3000
REQUIRED_KEYS = ("AWS_REGION", "COGNITO_CLIENT_ID", "API_URL")
PAGE_PATHS = {"/", "/index.html"}


def load_env(path: Path) -> dict[str, str]:
    """Parse KEY=VALUE lines, ignoring blank lines and comments."""
    values = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self) -> None:
        # Compare the raw path (still URL-encoded) against an allowlist: %2Eenv or ../ never match.
        path = self.path.split("?", 1)[0]
        if path in PAGE_PATHS:
            self.path = "/index.html"
            super().do_GET()
        elif path == "/config.js":
            self._send_config()
        else:
            self.send_error(404)

    def do_HEAD(self) -> None:
        self.send_error(405)

    def _send_config(self) -> None:
        env_file = ROOT / ".env"
        if not env_file.exists():
            self.send_error(500, "web/.env not found: copy .env.example to .env")
            return
        env = load_env(env_file)
        missing = [k for k in REQUIRED_KEYS if not env.get(k)]
        if missing:
            self.send_error(500, f"Missing values in web/.env: {', '.join(missing)}")
            return

        config = {"region": env["AWS_REGION"], "clientId": env["COGNITO_CLIENT_ID"], "apiUrl": env["API_URL"].rstrip("/")}
        body = f"window.APP_CONFIG = {json.dumps(config)};\n".encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/javascript; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), partial(Handler, directory=str(ROOT)))
    print(f"Serving the web client on http://localhost:{PORT} (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
