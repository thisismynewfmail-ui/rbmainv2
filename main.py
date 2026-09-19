#!/usr/bin/env python3
"""BLOCKHAVEN -- a block-world game platform.

Starts the website (profiles, avatar editor, market, world browser) on
port 8972 and supervises one game-host process per world.  Every game world is
served from a sub-page of that same port, e.g. http://<your-ip>:8972/burger_tycoon

Usage::

    python3 main.py                # normal start
    python3 main.py --port 9000    # different port
    python3 main.py --no-games     # website only (no game hosts)
    python3 main.py --reset        # wipe the database and re-seed
"""
from __future__ import annotations

import argparse
import os
import signal
import socket
import ssl
import sys
import threading
import time

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

from app import config  # noqa: E402


def local_ip() -> str:
    try:
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        probe.settimeout(0.4)
        probe.connect(("10.255.255.255", 1))
        address = probe.getsockname()[0]
        probe.close()
        return address
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"


def _bind_hint(port: int) -> str:
    """Why a bind failed, in the words of the thing that can fix it."""
    if port < 1024 and os.geteuid() != 0:
        return ("       Ports below 1024 need root: run it with sudo, or\n"
                "       grant the binary the capability once:\n"
                "         sudo setcap 'cap_net_bind_service=+ep' "
                "$(readlink -f $(which python3))")
    return ("       Something else is already on that port. Find it with\n"
            "         sudo ss -lptn 'sport = :%d'" % port)


def _drop_privileges(user: str) -> bool:
    """Become ``user`` now that the privileged ports are bound.

    Everything after this -- the database, the game hosts it spawns, anything
    a request touches -- runs as an ordinary account, so a bug in the server
    is not a bug with root behind it.  The data directory is handed over with
    it: the database, the session secret and the ACME webroot all have to stay
    writable, and a root-owned file left in there would fail a long way from
    the cause.
    """
    if os.geteuid() != 0:
        print("[main] --user only applies when started as root; staying as is.")
        return True
    try:
        import grp
        import pwd
        entry = pwd.getpwnam(user)
    except KeyError:
        print("[main] no such user: %s" % user)
        return False
    try:
        for path in (config.DATA_DIR,):
            os.chown(path, entry.pw_uid, entry.pw_gid)
            for root, dirs, files in os.walk(path):
                for name in dirs + files:
                    os.chown(os.path.join(root, name), entry.pw_uid, entry.pw_gid)
        os.setgroups(
            [g.gr_gid for g in grp.getgrall() if user in g.gr_mem] or [entry.pw_gid])
        os.setgid(entry.pw_gid)
        os.setuid(entry.pw_uid)
        os.environ["HOME"] = entry.pw_dir
    except OSError as exc:
        print("[main] could not drop to %s -- %s" % (user, exc))
        return False
    print("[main] dropped privileges to %s (uid %d)" % (user, entry.pw_uid))
    return True


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Run the BLOCKHAVEN platform")
    parser.add_argument("--port", type=int, default=config.HTTP_PORT,
                        help="plain HTTP port (default 80; redirects to "
                             "HTTPS when a certificate is in use)")
    parser.add_argument("--https-port", type=int, default=config.HTTPS_PORT,
                        help="TLS port (default 443)")
    parser.add_argument("--host", default=config.HTTP_HOST)
    parser.add_argument("--domain", default=config.DOMAIN,
                        help="the name this is served as, e.g. example.com. "
                             "Optional: when a certificate is found it "
                             "names the site itself. A certbot certificate "
                             "is looked for under "
                             "/etc/letsencrypt/live/<domain>/.")
    parser.add_argument("--cert", default=config.TLS_CERT,
                        help="certificate chain (PEM)")
    parser.add_argument("--key", default=config.TLS_KEY,
                        help="private key (PEM)")
    parser.add_argument("--cert-dir", default="",
                        help="where a certificate downloaded from a "
                             "registrar or host lives (default: certs/ in "
                             "this directory, which is searched anyway)")
    parser.add_argument("--tls-check", action="store_true",
                        help="say which certificate would be used and what "
                             "is wrong with the others, then exit without "
                             "binding anything")
    parser.add_argument("--self-signed", action="store_true",
                        help="make and use a self-signed certificate: for "
                             "local work only, every browser will warn")
    parser.add_argument("--no-https", action="store_true",
                        help="serve plain HTTP only")
    parser.add_argument("--hsts", type=int, nargs="?", const=15552180, default=0,
                        metavar="SECONDS",
                        help="send Strict-Transport-Security once TLS is "
                             "known good (default 180 days). A browser that "
                             "has seen it refuses plain HTTP until it "
                             "expires, so turn it on deliberately.")
    parser.add_argument("--user", default="",
                        help="drop to this user once the privileged ports "
                             "are bound (e.g. --user $SUDO_USER)")
    parser.add_argument("--no-games", action="store_true",
                        help="serve the website without starting game hosts")
    parser.add_argument("--reset", action="store_true",
                        help="delete the database and start fresh")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--status-interval", type=float, default=4.0,
                        help="seconds between terminal status blocks "
                             "(0 turns the live read-out off)")
    args = parser.parse_args(argv)

    if args.debug:
        config.DEBUG = True
        os.environ["BLOCKHAVEN_DEBUG"] = "1"
    config.HTTP_PORT = args.port
    config.HTTPS_PORT = args.https_port
    config.DOMAIN = args.domain

    if args.cert_dir:
        os.environ["BLOCKHAVEN_CERT_DIR"] = args.cert_dir

    if args.tls_check:
        from app.http import tls as tls_support
        usable, text = tls_support.report(args.domain, args.cert, args.key,
                                          args.cert_dir)
        print(text)
        return 0 if usable else 1

    if args.reset and config.DB_PATH.exists():
        for suffix in ("", "-wal", "-shm"):
            path = str(config.DB_PATH) + suffix
            if os.path.exists(path):
                os.remove(path)
        print("[main] database reset")

    from app import bootstrap, webapp
    from app.http import server as http_server
    from app.http import tls as tls_support

    # ---------------------------------------------------------------- TLS
    # Resolved before anything binds, because whether there is a certificate
    # decides what the plain port is for: serving the site, or redirecting to
    # the encrypted one.
    tls_context = None
    tls_info = None
    if not args.no_https:
        try:
            tls_info = tls_support.locate(args.domain, args.cert, args.key,
                                          allow_self_signed=args.self_signed,
                                          cert_dir=args.cert_dir)
        except tls_support.TLSError as exc:
            print("[main] %s" % exc)
            return 1
        if tls_info:
            # A certificate names the site it belongs to, so --domain is a
            # convenience rather than a requirement: without it the redirect
            # target would be this machine's IP address, which no certificate
            # covers -- exactly the "Not secure" this is here to avoid.
            if not args.domain and tls_info.get("domain"):
                args.domain = tls_info["domain"]
                config.DOMAIN = args.domain
                print("[main] serving as %s (read from the certificate)"
                      % args.domain)
            try:
                tls_context = http_server.tls_context(tls_info["cert"],
                                                      tls_info["key"])
            except (OSError, ssl.SSLError) as exc:
                print("[main] could not load the certificate %s -- %s"
                      % (tls_info["cert"], exc))
                return 1
            config.TLS_CERT = tls_info["cert"]
            config.TLS_KEY = tls_info["key"]
            config.TLS_ACTIVE = True
            config.HSTS_SECONDS = int(args.hsts or 0)
            for warning in (tls_info.get("warnings") or "").split("; "):
                if warning:
                    print("[main] certificate note: %s" % warning)
        else:
            def _indent(text: str) -> str:
                return "\n".join("       " + line
                                 for line in text.splitlines())

            print("[main] no certificate yet, so this is plain HTTP for now.")
            print("       Already have one from your registrar or host?")
            print(_indent(tls_support.bundle_hint()))
            print("       Or have Let's Encrypt issue one here:")
            print(_indent(tls_support.certbot_hint(args.domain)))
            print("       (--tls-check says what was looked at and why it "
                  "was passed over; --self-signed is for local work, and "
                  "--no-https stops the asking)")

    config.ACME_WEBROOT.mkdir(parents=True, exist_ok=True)
    (config.ACME_WEBROOT / ".well-known" / "acme-challenge").mkdir(
        parents=True, exist_ok=True)

    # ------------------------------------------------------------ listeners
    # Bound while still privileged, because 80 and 443 need that; everything
    # after this point can run as an ordinary user.
    redirect_to = ""
    if tls_context is not None:
        redirect_to = "https://%s" % (args.domain or local_ip())
        if args.https_port != 443:
            redirect_to += ":%d" % args.https_port

    servers = []
    try:
        plain = http_server.serve(None, args.host, args.port,
                                  redirect_to=redirect_to)
        servers.append(("http", args.port, plain))
    except OSError as exc:
        print("[main] could not bind %s:%d -- %s" % (args.host, args.port, exc))
        print(_bind_hint(args.port))
        return 1
    secure = None
    if tls_context is not None:
        try:
            secure = http_server.serve(None, args.host, args.https_port,
                                       ssl_context=tls_context)
            servers.append(("https", args.https_port, secure))
        except OSError as exc:
            print("[main] could not bind %s:%d -- %s"
                  % (args.host, args.https_port, exc))
            print(_bind_hint(args.https_port))
            plain.server_close()
            return 1

    if args.user:
        if not _drop_privileges(args.user):
            for _n, _p, srv in servers:
                srv.server_close()
            return 1

    bootstrap.seed()

    supervisor = None
    if not args.no_games:
        from app.game.supervisor import Supervisor
        from app.views import admin as admin_views
        # The hosts report in over plain HTTP on the loopback, which is why
        # /internal is the one path the redirector still answers.
        supervisor = Supervisor(args.port)
        supervisor.start()
        admin_views.set_supervisor(supervisor)

    application = webapp.create_app()
    for _name, _port, srv in servers:
        srv.attach(application)
    server = secure or plain

    address = local_ip()
    from app import console
    from app.models import worlds as world_registry

    public_port = args.https_port if tls_context is not None else args.port
    dashboard = console.Dashboard(application, public_port, address,
                                  supervisor=supervisor,
                                  interval=max(2.0, args.status_interval or 4.0),
                                  scheme="https" if tls_context else "http",
                                  domain=args.domain)
    print(dashboard.intro(world_registry.all_worlds(),
                          (config.ADMIN_USERNAME, config.ADMIN_PASSWORD),
                          not args.no_games), flush=True)
    if tls_context is not None:
        info = tls_info or {}
        dashboard.note("HTTPS on port %d -- certificate %s"
                       % (args.https_port, info.get("source", "?")))
        if info.get("covers"):
            dashboard.note("certificate covers %s" % info["covers"])
        details = tls_support.describe(info.get("cert", ""))
        if details.get("days_left"):
            dashboard.note("certificate expires %s (%s days)"
                           % (details.get("expires", "?"), details["days_left"]))
        if info.get("chain_note"):
            dashboard.note("chain: %s" % info["chain_note"])
        for warning in (info.get("warnings") or "").split("; "):
            if warning:
                dashboard.note(warning)
        if info.get("source") == "self-signed":
            dashboard.note("self-signed: browsers will warn. Fine for a LAN, "
                           "not for the public site.")
        dashboard.note("port %d redirects to %s" % (args.port, redirect_to))
    else:
        dashboard.note("web server listening on port %d (plain HTTP)"
                       % args.port)
    if supervisor is not None:
        dashboard.note("supervising %d game host%s"
                       % (len(world_registry.all_worlds()),
                          "" if len(world_registry.all_worlds()) == 1 else "s"))
    if args.status_interval and args.status_interval > 0:
        dashboard.start()

    stopping = threading.Event()

    def shutdown(signum=None, frame=None):
        if stopping.is_set():
            return
        stopping.set()
        dashboard.stop()
        print("\n[main] shutting down...", flush=True)
        for _name, _port, srv in servers:
            threading.Thread(target=srv.shutdown, daemon=True).start()
        if supervisor:
            supervisor.stop()

    signal.signal(signal.SIGINT, shutdown)
    try:
        signal.signal(signal.SIGTERM, shutdown)
    except (AttributeError, ValueError):
        pass

    # Every listener but the last gets its own thread; the last runs on this
    # one, so Ctrl-C still lands where it always did.
    for _name, _port, srv in servers[:-1]:
        threading.Thread(target=srv.serve_forever, kwargs={"poll_interval": 0.5},
                         daemon=True).start()
    try:
        servers[-1][2].serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        shutdown()
    finally:
        if not stopping.is_set():
            shutdown()
        for _name, _port, srv in servers:
            srv.server_close()
    print(console.dim("  served %s requests over %s"
                      % (f"{getattr(application, 'request_count', 0):,}",
                         console.human_time(time.time() - dashboard.started))))
    print("[main] bye.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
