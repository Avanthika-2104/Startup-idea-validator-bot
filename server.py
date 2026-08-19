"""Minimal dependency-free JSON web server used by the project UI."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable


MAX_REQUEST_BYTES = 1_000_000


def serve(
    generator: Callable[[dict[str, Any]], dict[str, Any]],
    *,
    title: str,
    base_dir: Path,
    host: str,
    port: int,
) -> None:
    """Serve the browser UI and generation endpoint."""

    index_file = base_dir / "static" / "index.html"

    class Handler(BaseHTTPRequestHandler):
        def send_bytes(self, status: int, payload: bytes, content_type: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.end_headers()
            self.wfile.write(payload)

        def send_json(self, status: int, value: dict[str, Any]) -> None:
            payload = json.dumps(value, ensure_ascii=False).encode("utf-8")
            self.send_bytes(status, payload, "application/json; charset=utf-8")

        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/":
                self.send_bytes(200, index_file.read_bytes(), "text/html; charset=utf-8")
                return
            if self.path == "/health":
                self.send_json(200, {"status": "ok", "app": title})
                return
            self.send_json(404, {"error": "Not found"})

        def do_POST(self) -> None:  # noqa: N802
            if self.path != "/api/generate":
                self.send_json(404, {"error": "Not found"})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length <= 0 or length > MAX_REQUEST_BYTES:
                    raise ValueError("Request body is missing or too large.")
                payload = json.loads(self.rfile.read(length))
                if not isinstance(payload, dict):
                    raise ValueError("Request body must be a JSON object.")
                self.send_json(200, {"result": generator(payload)})
            except (ValueError, json.JSONDecodeError) as exc:
                self.send_json(400, {"error": str(exc)})
            except RuntimeError as exc:
                self.send_json(502, {"error": str(exc)})
            except Exception:
                self.send_json(500, {"error": "Unexpected server error."})

        def log_message(self, format: str, *args: object) -> None:
            return

    server = ThreadingHTTPServer((host, port), Handler)
    print(f"{title} running at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
