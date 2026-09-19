"""Global configuration for the BLOCKHAVEN platform.

Everything is intentionally dependency free -- the whole stack runs on the
Python standard library so the project can be dropped onto any machine with
Python 3.9+ and started with ``python3 main.py``.
"""
from __future__ import annotations

import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
STATIC_DIR = BASE_DIR / "static"
TEMPLATE_DIR = BASE_DIR / "templates"

DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "blockhaven.sqlite3"
SECRET_PATH = DATA_DIR / "secret.key"

SITE_NAME = "BLOCKHAVEN"
SITE_TAGLINE = "Build it. Play it. Live it."

# ---------------------------------------------------------------- networking
# The public ports.  80 and 443 are what a browser tries when someone types a
# domain, so those are the defaults; both are privileged, which is why run.sh
# knows how to ask for root.
HTTP_PORT = int(os.environ.get("BLOCKHAVEN_PORT", "80"))
HTTPS_PORT = int(os.environ.get("BLOCKHAVEN_HTTPS_PORT", "443"))
HTTP_HOST = os.environ.get("BLOCKHAVEN_HOST", "0.0.0.0")

# The domain this is served as.  It is what the HTTP listener redirects to
# when a request arrives with no Host header worth trusting, and what the
# certificate is looked up under.
DOMAIN = os.environ.get("BLOCKHAVEN_DOMAIN", "")

# TLS.  Empty means plain HTTP; ``main.py --cert/--key`` or a certificate
# found under /etc/letsencrypt/live/<domain>/ fills them in.
TLS_CERT = os.environ.get("BLOCKHAVEN_TLS_CERT", "")
TLS_KEY = os.environ.get("BLOCKHAVEN_TLS_KEY", "")
# Set once TLS is actually listening, so cookies can be marked Secure and the
# plain listener knows to redirect rather than serve.
TLS_ACTIVE = False
# Opt in only: a browser that has seen this header refuses plain HTTP for the
# whole max-age, which is unpleasant to undo if the certificate lapses.
HSTS_SECONDS = 0

# Where certbot's webroot plugin drops its HTTP-01 challenge files.  The
# challenge has to be answerable over PLAIN HTTP on port 80 even when
# everything else there is a redirect, which is why it is served from the
# server rather than from behind the redirect.
ACME_WEBROOT = DATA_DIR / "acme"
ACME_PREFIX = "/.well-known/acme-challenge/"

# Where a certificate downloaded from a registrar or host is kept.  It is
# searched on every start, so ``./run.sh`` serves HTTPS with no flags at all
# once a bundle has been put there -- see ``tools/install_cert.py``.  The
# directory is in .gitignore: a private key does not belong in a repository.
CERT_DIR = Path(os.environ.get("BLOCKHAVEN_CERT_DIR", "") or (BASE_DIR / "certs"))

# Internal loopback range used by the game host subprocesses.  Nothing outside
# the machine ever talks to these -- the public facing HTTP server reverse
# proxies websocket upgrades into them.
GAME_HOST_PORT_BASE = int(os.environ.get("BLOCKHAVEN_GAME_PORT_BASE", "8990"))
INTERNAL_BIND = "127.0.0.1"

# ---------------------------------------------------------------- economy
STARTING_CREDITS = 2000
UNUSUAL_CHANCE = 0.005  # 0.5% on hat-slot cosmetics only
MAX_CREDITS = 1_000_000_000

# ---------------------------------------------------------------- accounts
ADMIN_USERNAME = "admin_system"
ADMIN_PASSWORD = "passman69"
DEMO_ADMIN_TEST_USERNAME = "admin_test"
DEMO_ADMIN_TEST_PASSWORD = "passman69"

PASSWORD_MIN = 4
PASSWORD_MAX = 128
USERNAME_MIN = 3
USERNAME_MAX = 20

SESSION_COOKIE = "bh_session"
SESSION_TTL = 60 * 60 * 24 * 30  # 30 days

PBKDF2_ROUNDS = 120_000

# ---------------------------------------------------------------- gameplay
VISIT_THRESHOLD_SECONDS = 30  # 30s of playtime == one recorded visit
TICK_RATE = 20                # server simulation / broadcast rate
SHUFFLE_VOTE_SECONDS = 30
SHUFFLE_VOTE_RATIO = 0.80
GAME_TICKET_TTL = 120         # seconds a signed join ticket stays valid

# ---------------------------------------------------------------- misc
DEBUG = os.environ.get("BLOCKHAVEN_DEBUG", "") not in ("", "0", "false")


def load_secret() -> bytes:
    """Persistent server secret used for HMAC signing (sessions, tickets)."""
    if SECRET_PATH.exists():
        raw = SECRET_PATH.read_bytes().strip()
        if len(raw) >= 32:
            return raw
    raw = secrets.token_bytes(48).hex().encode()
    SECRET_PATH.write_bytes(raw)
    try:
        os.chmod(SECRET_PATH, 0o600)
    except OSError:
        pass
    return raw


SECRET = load_secret()
