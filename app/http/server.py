"""A threaded HTTP/1.1 server with TLS and websocket reverse-proxy support.

Written directly on top of ``socketserver`` (rather than ``http.server``) so we
keep full control of the socket when a connection is upgraded to a websocket:
game traffic is piped, byte for byte, into the matching game-host process while
the ordinary website keeps being served from the very same port.

TLS is terminated here too, which is what lets the websocket proxy work over
``wss://``: the upgrade arrives already decrypted on the same listener the
pages come from, so the game needs no second port and no second certificate.
The handshake happens in the connection's own thread rather than in the accept
loop, so a slow or hostile client cannot hold up everybody else's connections.

Two listeners run when TLS is on.  The 443 one serves the site.  The 80 one
answers three things and redirects everything else: the ACME challenge (which
has to be plain HTTP by definition), loopback calls to /internal (which is how
the game hosts report in), and HEAD/GET probes that want a redirect.
"""
from __future__ import annotations

import gzip
import mimetypes
import os
import select
import socket
import socketserver
import ssl
import sys
import threading
import time
import traceback
from typing import Callable, Dict, Optional, Tuple

from .. import config
from .router import Request, Response, STATUS_TEXT, error

MAX_HEADER_BYTES = 32 * 1024
MAX_BODY_BYTES = 2 * 1024 * 1024
KEEPALIVE_TIMEOUT = 45
# A handshake is a couple of round trips; anything slower is not a browser.
TLS_HANDSHAKE_TIMEOUT = 12
SERVER_NAME = "BlockhavenHTTP/1.0"

GZIP_TYPES = ("text/", "application/javascript", "application/json",
              "image/svg+xml")

mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("application/json", ".json")
mimetypes.add_type("image/svg+xml", ".svg")


class Application:
    """Holds the dispatch callable plus the websocket backend resolver."""

    def __init__(self, dispatch: Callable[[Request], Response],
                 ws_resolver: Optional[Callable[[str], Optional[Tuple[str, int]]]] = None,
                 static_root: Optional[str] = None):
        self.dispatch = dispatch
        self.ws_resolver = ws_resolver
        self.static_root = static_root or str(config.STATIC_DIR)
        self.started = time.time()
        self.request_count = 0
        self.ws_count = 0
        self._lock = threading.Lock()

    def bump(self, ws: bool = False) -> None:
        with self._lock:
            self.request_count += 1
            if ws:
                self.ws_count += 1


class ConnectionHandler(socketserver.StreamRequestHandler):
    rbufsize = 65536
    wbufsize = 0
    timeout = KEEPALIVE_TIMEOUT
    app: Application = None  # type: ignore[assignment]

    def setup(self) -> None:
        """Terminate TLS before anything reads the socket.

        This runs in the connection's own thread, not the accept loop, so a
        client that opens a socket and then says nothing costs one thread
        instead of blocking every other connection behind it.  A handshake
        that fails raises, which socketserver turns into handle_error and a
        closed socket -- the right answer for a probe or for a browser that
        tried https:// against the plain port.
        """
        ctx = getattr(self.server, "ssl_context", None)
        if ctx is not None:
            self.request.settimeout(TLS_HANDSHAKE_TIMEOUT)
            self.request = ctx.wrap_socket(self.request, server_side=True)
        super().setup()

    # ------------------------------------------------------------------ core
    def handle(self) -> None:
        try:
            self.connection.settimeout(KEEPALIVE_TIMEOUT)
            while True:
                if not self.handle_one():
                    break
        except (socket.timeout, TimeoutError):
            pass
        except (ConnectionResetError, BrokenPipeError):
            pass
        except OSError:
            pass
        except Exception:
            if config.DEBUG:
                traceback.print_exc()

    def handle_one(self) -> bool:
        line = self.rfile.readline(MAX_HEADER_BYTES + 1)
        if not line:
            return False
        try:
            request_line = line.decode("latin-1").rstrip("\r\n")
        except Exception:
            return False
        if not request_line:
            return True
        parts = request_line.split()
        if len(parts) != 3:
            self.send_simple(400, "Bad Request")
            return False
        method, target, version = parts
        headers: Dict[str, str] = {}
        total = len(line)
        while True:
            hline = self.rfile.readline(MAX_HEADER_BYTES + 1)
            if not hline:
                return False
            total += len(hline)
            if total > MAX_HEADER_BYTES:
                self.send_simple(431, "Headers too large")
                return False
            if hline in (b"\r\n", b"\n"):
                break
            try:
                raw = hline.decode("latin-1").rstrip("\r\n")
                name, _, value = raw.partition(":")
                key = name.strip().lower()
                if key:
                    if key in headers:
                        headers[key] += "," + value.strip()
                    else:
                        headers[key] = value.strip()
            except Exception:
                continue

        path, _, raw_query = target.partition("?")
        path = _normalise_path(path)

        # ------------------------------------------------- http -> https
        # Everything on the plain port is a redirect except the two things
        # that cannot be: the ACME challenge, which is plain HTTP by
        # definition, and the game hosts' own reports, which come from this
        # machine and never leave it.
        redirect_to = getattr(self.server, "redirect_to", "")
        if redirect_to and not path.startswith(config.ACME_PREFIX) \
                and not (path.startswith("/internal/")
                         and _is_loopback(self.client_address[0])):
            host = _redirect_host(headers.get("host", ""), redirect_to)
            self.send_redirect(host + target)
            return False

        # ------------------------------------------------ websocket upgrade
        if (headers.get("upgrade", "").lower() == "websocket"
                and self.app.ws_resolver is not None):
            backend = self.app.ws_resolver(path)
            if backend is None:
                self.send_simple(404, "No such realtime endpoint")
                return False
            self.app.bump(ws=True)
            self.proxy_websocket(backend, request_line, headers)
            return False

        body = b""
        length = headers.get("content-length")
        if length:
            try:
                n = int(length)
            except ValueError:
                self.send_simple(400, "Bad Content-Length")
                return False
            if n > MAX_BODY_BYTES:
                self.send_simple(413, "Payload too large")
                return False
            remaining = n
            chunks = []
            while remaining > 0:
                chunk = self.rfile.read(min(remaining, 65536))
                if not chunk:
                    return False
                chunks.append(chunk)
                remaining -= len(chunk)
            body = b"".join(chunks)

        keep_alive = version.upper() != "HTTP/1.0"
        if headers.get("connection", "").lower() == "close":
            keep_alive = False

        req = Request(method, path, raw_query, headers, body,
                      self.client_address[0])
        self.app.bump()
        try:
            resp = self.app.dispatch(req)
        except Exception:
            traceback.print_exc()
            resp = error(500, "Something went wrong on the server.")
        if resp is None:
            resp = error(500, "Handler returned nothing.")

        self.send_response(req, resp, keep_alive)
        return keep_alive

    def send_redirect(self, location: str) -> None:
        """301 to the same path on https, and say so in a body a curl -I or a
        browser with scripting off can still read."""
        body = (b"<!doctype html><meta charset=utf-8>"
                b"<title>Moved</title><p>This site is served over HTTPS: "
                b"<a href=\"" + location.encode("utf-8", "replace") + b"\">"
                + location.encode("utf-8", "replace") + b"</a>")
        head = ("HTTP/1.1 301 Moved Permanently\r\n"
                "Location: %s\r\n"
                "Content-Type: text/html; charset=utf-8\r\n"
                "Content-Length: %d\r\n"
                "Connection: close\r\n"
                "Server: %s\r\n\r\n" % (location, len(body), SERVER_NAME))
        try:
            self.wfile.write(head.encode("latin-1") + body)
        except OSError:
            pass

    # ---------------------------------------------------------------- output
    def send_response(self, req: Request, resp: Response, keep_alive: bool) -> None:
        body = resp.body
        headers = dict(resp.headers)
        ctype = headers.get("Content-Type", "")
        if (len(body) > 900 and any(ctype.startswith(t) for t in GZIP_TYPES)
                and "gzip" in req.headers.get("accept-encoding", "")):
            body = gzip.compress(body, 5)
            headers["Content-Encoding"] = "gzip"
            headers["Vary"] = "Accept-Encoding"
        headers["Content-Length"] = str(len(body))
        headers["Server"] = SERVER_NAME
        headers["Connection"] = "keep-alive" if keep_alive else "close"
        headers.setdefault("X-Content-Type-Options", "nosniff")
        # Opt in only, and only on the encrypted listener: a browser that has
        # seen this refuses plain HTTP for the whole max-age, so sending it
        # from the redirector -- or before a certificate is known good --
        # locks visitors out of a site that has gone back to HTTP.
        if config.HSTS_SECONDS and getattr(self.server, "ssl_context", None):
            headers.setdefault("Strict-Transport-Security",
                               "max-age=%d" % config.HSTS_SECONDS)
        out = ["HTTP/1.1 %d %s" % (resp.status,
                                   STATUS_TEXT.get(resp.status, "OK"))]
        for k, v in headers.items():
            out.append("%s: %s" % (k, v))
        for cookie in resp.cookies:
            out.append("Set-Cookie: %s" % cookie)
        head = ("\r\n".join(out) + "\r\n\r\n").encode("latin-1")
        try:
            self.wfile.write(head)
            if body and req.method != "HEAD":
                self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def send_simple(self, status: int, message: str) -> None:
        body = message.encode()
        try:
            self.wfile.write(
                ("HTTP/1.1 %d %s\r\nContent-Type: text/plain\r\n"
                 "Content-Length: %d\r\nConnection: close\r\n\r\n"
                 % (status, STATUS_TEXT.get(status, "Error"), len(body))
                 ).encode("latin-1") + body)
        except OSError:
            pass

    # ------------------------------------------------------------- ws proxy
    def proxy_websocket(self, backend: Tuple[str, int], request_line: str,
                        headers: Dict[str, str]) -> None:
        """Pipe the upgrade handshake and every following byte to a game host."""
        try:
            upstream = socket.create_connection(backend, timeout=8)
        except OSError:
            self.send_simple(503, "Game server unavailable")
            return
        try:
            upstream.settimeout(None)
            self.connection.settimeout(None)
            rebuilt = [request_line]
            for key, value in headers.items():
                rebuilt.append("%s: %s" % (key, value))
            rebuilt.append("X-Real-IP: %s" % self.client_address[0])
            upstream.sendall(("\r\n".join(rebuilt) + "\r\n\r\n").encode("latin-1"))
            self._pump(upstream)
        finally:
            try:
                upstream.close()
            except OSError:
                pass

    def _pump(self, upstream: socket.socket) -> None:
        """Shuttle bytes both ways until either side hangs up.

        The client -> upstream direction reads through ``self.rfile`` with
        ``read1`` so anything the buffered reader already swallowed while
        parsing the request headers is forwarded rather than lost, and it never
        blocks waiting for data that has not arrived.
        """
        client = self.connection
        stop = threading.Event()

        def client_to_upstream():
            try:
                while not stop.is_set():
                    data = self.rfile.read1(65536)
                    if not data:
                        break
                    upstream.sendall(data)
            except (OSError, ValueError):
                pass
            finally:
                stop.set()
                try:
                    upstream.shutdown(socket.SHUT_WR)
                except OSError:
                    pass

        pump = threading.Thread(target=client_to_upstream, daemon=True,
                                name="ws-up")
        pump.start()
        try:
            while not stop.is_set():
                try:
                    data = upstream.recv(65536)
                except (ConnectionResetError, OSError):
                    break
                if not data:
                    break
                try:
                    client.sendall(data)
                except OSError:
                    break
        finally:
            stop.set()
            try:
                upstream.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                client.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass


def _is_loopback(address: str) -> bool:
    """Is this peer on this machine?  The game hosts are, and nothing else
    that talks to /internal should be."""
    return address in ("127.0.0.1", "::1", "::ffff:127.0.0.1") \
        or address.startswith("127.")


def _redirect_host(host_header: str, fallback: str) -> str:
    """Where a plain request should be sent.

    The Host header decides, so a site reached by several names keeps the one
    the visitor typed -- but it is attacker-controlled, so it is accepted only
    if it looks like a hostname, and the port is dropped (a redirect from :80
    goes to :443, which is implicit).  Anything else falls back to the domain
    the server was started with.
    """
    host = (host_header or "").strip().split(",")[0].strip()
    if host.startswith("["):                     # bracketed IPv6 literal
        name, _, _rest = host.partition("]")
        host = name + "]"
    else:
        host = host.split(":")[0]
    if host and all(c.isalnum() or c in "-._" for c in host) and ".." not in host:
        return "https://" + host
    return fallback


def _normalise_path(path: str) -> str:
    from urllib.parse import unquote
    path = unquote(path)
    if not path.startswith("/"):
        path = "/" + path
    while "//" in path:
        path = path.replace("//", "/")
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/") or "/"
    return path


class ThreadedHTTPServer(socketserver.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True
    request_queue_size = 128

    def __init__(self, addr, handler_cls, app: Optional[Application] = None,
                 ssl_context: Optional[ssl.SSLContext] = None,
                 redirect_to: str = ""):
        self.app = app
        self.handler_cls = handler_cls
        # Handed to the handler, which does the handshake in its own thread.
        self.ssl_context = ssl_context
        # Non-empty on the plain listener when TLS is up: "https://host" with
        # the port already folded in, ready for a Location header.
        self.redirect_to = redirect_to
        if app is not None:
            handler_cls.app = app
        super().__init__(addr, handler_cls)

    def attach(self, app: Application) -> None:
        """Hand the server its application once there is one.

        The listeners are bound before the application is built, because
        binding 80 and 443 needs a privilege the rest of the process has no
        reason to keep -- so the socket exists first and the site that
        answers on it arrives a moment later.
        """
        self.app = app
        self.handler_cls.app = app

    def server_bind(self):
        # Without this a client that hangs up mid-handshake can leave the
        # port in TIME_WAIT and a restart fails to bind for a minute -- on a
        # machine where the whole site is one process, that is the site down.
        if hasattr(socket, "SO_REUSEADDR"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        super().server_bind()

    def handle_error(self, request, client_address):  # noqa: D401
        exc = sys.exc_info()[1]
        if isinstance(exc, (ConnectionResetError, BrokenPipeError,
                            socket.timeout, TimeoutError)):
            return
        # A failed handshake is routine on a public port: a scanner, a
        # browser sent to https:// on the plain port, a probe. Not an error.
        if isinstance(exc, ssl.SSLError):
            return
        if config.DEBUG:
            traceback.print_exc()


def tls_context(cert_file: str, key_file: str) -> ssl.SSLContext:
    """A modern server context: TLS 1.2+, the platform's cipher choice, and
    HTTP/1.1 advertised over ALPN so a browser does not try HTTP/2 against a
    server that only speaks 1.1."""
    ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.load_cert_chain(certfile=cert_file, keyfile=key_file)
    try:
        ctx.set_alpn_protocols(["http/1.1"])
    except NotImplementedError:      # pragma: no cover - very old OpenSSL
        pass
    return ctx


def serve(app: Optional[Application], host: str, port: int,
          ssl_context: Optional[ssl.SSLContext] = None,
          redirect_to: str = "") -> ThreadedHTTPServer:
    return ThreadedHTTPServer((host, port), ConnectionHandler, app,
                              ssl_context=ssl_context, redirect_to=redirect_to)


# ---------------------------------------------------------------- static files
_static_cache: Dict[str, Tuple[float, bytes, str]] = {}
_static_lock = threading.Lock()


def serve_static(root: str, rel_path: str, req: Request) -> Response:
    rel_path = rel_path.lstrip("/")
    if ".." in rel_path or rel_path.startswith("/"):
        return error(403, "Nope.")
    full = os.path.normpath(os.path.join(root, rel_path))
    if not full.startswith(os.path.normpath(root)):
        return error(403, "Nope.")
    try:
        stat = os.stat(full)
    except OSError:
        return error(404, "File not found: %s" % rel_path)
    if not os.path.isfile(full):
        return error(404, "Not a file")
    key = full
    with _static_lock:
        hit = _static_cache.get(key)
    if hit and hit[0] == stat.st_mtime:
        data, ctype = hit[1], hit[2]
    else:
        with open(full, "rb") as fh:
            data = fh.read()
        ctype = mimetypes.guess_type(full)[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype in ("application/javascript",
                                                  "application/json",
                                                  "image/svg+xml"):
            ctype += "; charset=utf-8"
        with _static_lock:
            _static_cache[key] = (stat.st_mtime, data, ctype)
    etag = '"%x-%x"' % (int(stat.st_mtime), stat.st_size)
    if req.headers.get("if-none-match") == etag:
        return Response(b"", 304, ctype, {"ETag": etag})
    # Templates link every asset with a ?v= stamp derived from the file, so a
    # stamped URL can be kept forever: when the file changes the URL changes
    # with it.  A bare URL -- a bookmark, a hand-typed path, an old page still
    # open -- has to revalidate every time, because holding one of those was
    # what let a phone run last week's site.js against today's markup.  The
    # ETag makes revalidation a 304 with no body, so it stays cheap.
    if config.DEBUG:
        cache = "no-store"
    elif req.query.get("v"):
        cache = "public, max-age=31536000, immutable"
    else:
        cache = "no-cache"
    return Response(data, 200, ctype, {
        "ETag": etag,
        "Cache-Control": cache,
    })
