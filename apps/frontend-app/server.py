from __future__ import annotations

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class SpaRequestHandler(SimpleHTTPRequestHandler):
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".html": "text/html; charset=utf-8",
        ".js": "application/javascript; charset=utf-8",
        ".css": "text/css; charset=utf-8",
    }

    def do_GET(self):
        requested = self.path.split("?", 1)[0]
        local_path = Path(self.directory, requested.lstrip("/"))
        if requested != "/" and not local_path.exists():
            self.path = "/index.html"
        super().do_GET()


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", 3010), SpaRequestHandler)
    server.serve_forever()
