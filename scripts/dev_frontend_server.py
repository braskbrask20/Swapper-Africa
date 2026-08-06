"""Local dev server for the frontend that disables browser caching.

We're actively iterating on the JS/CSS/HTML in this repo; the plain
`python3 -m http.server` lets browsers (Safari in particular) hold onto stale
copies of individual files, which produces confusing "Can't find variable"
style errors when one cached file references something a newer file added.
This serves the same static files but tells the browser never to cache them.

Usage: python3 scripts/dev_frontend_server.py [port]  (defaults to 5500)
"""
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer


class NoCacheHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Pragma", "no-cache")
        super().end_headers()


def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5500
    server = ThreadingHTTPServer(("0.0.0.0", port), NoCacheHandler)
    print(f"Serving the frontend with caching disabled at http://0.0.0.0:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
