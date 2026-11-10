#!/usr/bin/env python3
"""Expose an allowlisted subset of a loopback-only Nitter instance."""

from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from os import environ
from pathlib import Path
from re import fullmatch
from threading import Lock


LISTEN_HOST = environ.get("LISTEN_HOST", "127.0.0.1")
LISTEN_PORT = int(environ.get("PORT", "8081"))
NITTER_HOST = environ.get("NITTER_HOST", "127.0.0.1")
NITTER_PORT = int(environ.get("NITTER_PORT", "8080"))
ALLOWLIST = Path(environ.get("ALLOWLIST", "allowed-users.txt"))
FEED_REQUEST_LOCK = Lock()
HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}


def allowed_users() -> set[str]:
    try:
        return {
            line.strip().removeprefix("@").lower()
            for line in ALLOWLIST.read_text().splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }
    except FileNotFoundError:
        return set()


class Handler(BaseHTTPRequestHandler):
    server_version = "NitterRssFacade/1.0"

    def do_GET(self) -> None:
        if self.path == "/healthz":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"ok\n")
            return

        path = self.path.split("?", 1)[0]
        profile = fullmatch(r"/([A-Za-z0-9_]{1,15})/rss", path)
        is_media = path.startswith(("/pic/", "/video/"))
        if (profile is None or profile.group(1).lower() not in allowed_users()) and not is_media:
            self.send_error(404)
            return

        if profile is not None:
            with FEED_REQUEST_LOCK:
                self.proxy_request()
        else:
            self.proxy_request()

    def proxy_request(self) -> None:
        upstream = HTTPConnection(NITTER_HOST, NITTER_PORT, timeout=30)
        try:
            upstream.request("GET", self.path, headers={"User-Agent": self.headers.get("User-Agent", "RSS reader")})
            response = upstream.getresponse()
            body = response.read()
            self.send_response(response.status)
            for name, value in response.getheaders():
                if name.lower() not in HOP_BY_HOP_HEADERS and name.lower() != "content-length":
                    self.send_header(name, value)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (ConnectionError, OSError, TimeoutError):
            self.send_error(502, "Nitter backend unavailable")
        finally:
            upstream.close()

    def log_message(self, format: str, *args: object) -> None:
        print(f"{self.address_string()} - {format % args}", flush=True)


if __name__ == "__main__":
    ThreadingHTTPServer((LISTEN_HOST, LISTEN_PORT), Handler).serve_forever()
