"""Read-only loopback preview for an isolated LAST LIGHT mesh workspace.

This is intentionally NOT a remotely exposed founder dashboard: remote access
needs real authentication, permissions and private asset storage first.
"""
from __future__ import annotations

import argparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit


UI = Path(__file__).with_name("dashboard")
EXTENSIONS = {".html", ".css", ".js", ".json", ".png", ".glb", ".blend", ".log"}


def handler_for(data_root: Path):
    source = data_root.resolve()

    class Preview(SimpleHTTPRequestHandler):
        def translate_path(self, path):
            decoded = unquote(urlsplit(path).path)
            if decoded in ("/", "/index.html", "/app.js", "/style.css"):
                target = UI / ("index.html" if decoded == "/" else decoded.lstrip("/"))
            elif decoded == "/manifest.json" or decoded.startswith("/rooms/"):
                target = source / decoded.lstrip("/")
            else:
                return str(source / "__not_served__")
            # Reject URL-encoded traversal and symlinks outside the approved root.
            base = UI if target.is_relative_to(UI) else source
            if not target.resolve().is_relative_to(base.resolve()) or target.suffix not in EXTENSIONS:
                return str(source / "__not_served__")
            return str(target)

        def list_directory(self, path):
            self.send_error(403, "Directory listing disabled")
            return None

        def end_headers(self):
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'")
            self.send_header("X-Frame-Options", "DENY")
            super().end_headers()

    return Preview


def main() -> None:
    parser = argparse.ArgumentParser(description="Private localhost mesh review room")
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    if not (args.data_root / "manifest.json").is_file():
        raise ValueError("missing mesh workspace manifest")
    with ThreadingHTTPServer(("127.0.0.1", args.port), handler_for(args.data_root)) as server:
        print(f"LL_MESH_DASHBOARD http://127.0.0.1:{server.server_port}", flush=True)
        server.serve_forever()


if __name__ == "__main__":
    main()
