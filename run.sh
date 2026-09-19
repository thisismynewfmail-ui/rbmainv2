#!/usr/bin/env bash
# BLOCKHAVEN launcher.
#
# Starts the platform with the live terminal read-out: a status block every
# few seconds showing traffic, accounts, worlds and host processes instead of
# a single banner that goes quiet.
#
# The defaults are the public ones -- port 80 for HTTP and 443 for HTTPS --
# because those are what a browser tries when somebody types a domain. Both
# are privileged ports, so this script re-runs itself under sudo when it has
# to, and then hands the server back to your own account once the sockets are
# open (see --stay-root).
#
#   sudo ./run.sh                            HTTPS on :443 if a certificate is
#                                            installed, :80 redirects to it
#   ./run.sh --tls-check                     which certificate would be used,
#                                            and what is wrong with the rest
#   ./run.sh --domain example.com            name the site explicitly
#   ./run.sh --self-signed                   HTTPS with a throwaway certificate
#   ./run.sh --no-https                      plain HTTP only, as before
#   ./run.sh --port 8972 --no-https          unprivileged, no sudo needed
#   ./run.sh --reset                         wipe the database and re-seed
#   ./run.sh --no-games                      website only
#
# ---------------------------------------------------------------------------
# HTTPS
#
# There are two ways to have a certificate, and the server takes either one
# without being told which:
#
# A. You already have one, from your registrar or your host (Porkbun,
#    Namecheap, cPanel, ZeroSSL -- they all hand out a zip). Install it once:
#
#      python3 tools/install_cert.py ~/Downloads/example.com-ssl-bundle.zip
#      sudo ./run.sh
#
#    The installer unpacks the zip into certs/, works out which file is the
#    certificate and which is the key whatever they were named, puts the chain
#    in the right order, and refuses anything expired or mismatched. After
#    that ./run.sh finds it on its own -- no --domain, no --cert, no --key --
#    and the name the site answers to is read out of the certificate.
#
# B. Let's Encrypt issues one here, over port 80:
#
#      1. Point the domain's A record at this machine's public address.
#      2. Start the site so port 80 answers:   sudo ./run.sh --domain example.com
#      3. In another shell, ask for the certificate. The server answers the
#         challenge itself, so leave it running:
#           sudo certbot certonly --webroot -w data/acme -d example.com
#      4. Restart:                             sudo ./run.sh
#
#    Renewal needs nothing from you as long as port 80 stays open: certbot's
#    timer writes into data/acme and the server serves it. Restart afterwards
#    to pick the new certificate up (certbot's --deploy-hook is the usual
#    place).
#
# If a browser still says "Not secure", ./run.sh --tls-check says why: it
# lists every certificate found, what each covers, when it expires, and the
# reason any of them were passed over.
#
# Environment:
#   BLOCKHAVEN_STATUS_INTERVAL   default refresh in seconds (default 4)
#   BLOCKHAVEN_PORT              default HTTP port (default 80)
#   BLOCKHAVEN_HTTPS_PORT        default TLS port (default 443)
#   BLOCKHAVEN_DOMAIN            default --domain
#   BLOCKHAVEN_TLS_CERT / _KEY   default --cert / --key
#   NO_COLOR                     set to anything to drop the ANSI colours
set -uo pipefail

cd "$(dirname "$0")" || exit 1

PYTHON="${PYTHON:-python3}"
if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "run.sh: $PYTHON is not on PATH -- BLOCKHAVEN needs Python 3.9 or newer." >&2
  exit 1
fi

VERSION="$("$PYTHON" -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null || echo "?")"
if ! "$PYTHON" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 1)'; then
  echo "run.sh: Python $VERSION found, but 3.9 or newer is required." >&2
  exit 1
fi

# ---------------------------------------------------------------- arguments
# Read the few flags this script has to understand itself. Everything is
# passed through to main.py untouched; these are only inspected.
HTTP_PORT="${BLOCKHAVEN_PORT:-80}"
HTTPS_PORT="${BLOCKHAVEN_HTTPS_PORT:-443}"
WANT_TLS=1
TLS_CHECK=0
SELF_SIGNED=0
STAY_ROOT=0
HAS_USER=0
HAS_INTERVAL=0
DOMAIN="${BLOCKHAVEN_DOMAIN:-}"
CERT_DIR="${BLOCKHAVEN_CERT_DIR:-certs}"
ARGS=()
while [ $# -gt 0 ]; do
  case "$1" in
    --port) HTTP_PORT="${2:-}"; ARGS+=("$1" "${2:-}"); shift 2 ;;
    --port=*) HTTP_PORT="${1#*=}"; ARGS+=("$1"); shift ;;
    --https-port) HTTPS_PORT="${2:-}"; ARGS+=("$1" "${2:-}"); shift 2 ;;
    --https-port=*) HTTPS_PORT="${1#*=}"; ARGS+=("$1"); shift ;;
    --domain) DOMAIN="${2:-}"; ARGS+=("$1" "${2:-}"); shift 2 ;;
    --domain=*) DOMAIN="${1#*=}"; ARGS+=("$1"); shift ;;
    --cert-dir) CERT_DIR="${2:-}"; ARGS+=("$1" "${2:-}"); shift 2 ;;
    --cert-dir=*) CERT_DIR="${1#*=}"; ARGS+=("$1"); shift ;;
    --no-https) WANT_TLS=0; ARGS+=("$1"); shift ;;
    --self-signed) SELF_SIGNED=1; ARGS+=("$1"); shift ;;
    # Reads certificates and exits. It binds nothing, so it needs neither
    # root nor the start-up banner -- run it under sudo to have it see a
    # root-owned key as the server will.
    --tls-check) TLS_CHECK=1; ARGS+=("$1"); shift ;;
    --user|--user=*) HAS_USER=1; ARGS+=("$1"); shift ;;
    # Ours, not main.py's: keep the server running as root after it binds.
    --stay-root) STAY_ROOT=1; shift ;;
    --status-interval|--status-interval=*) HAS_INTERVAL=1; ARGS+=("$1"); shift ;;
    *) ARGS+=("$1"); shift ;;
  esac
done

if [ "$TLS_CHECK" -eq 1 ]; then
  exec "$PYTHON" main.py "${ARGS[@]}"
fi

NEEDS_ROOT=0
[ "$HTTP_PORT" -lt 1024 ] 2>/dev/null && NEEDS_ROOT=1
if [ "$WANT_TLS" -eq 1 ] && [ "$HTTPS_PORT" -lt 1024 ] 2>/dev/null; then
  NEEDS_ROOT=1
fi

# ---------------------------------------------------------------- privileges
# Ports below 1024 need root to BIND. They do not need root to serve, so the
# server drops back to the account that called sudo as soon as the sockets
# are open -- a bug in a request handler should not be a bug with root behind
# it. --stay-root or an explicit --user turns that off.
if [ "$NEEDS_ROOT" -eq 1 ] && [ "$(id -u)" -ne 0 ]; then
  if ! command -v sudo >/dev/null 2>&1; then
    echo "run.sh: port $HTTP_PORT needs root and sudo is not installed." >&2
    echo "        Either run this as root, or pick unprivileged ports:" >&2
    echo "          ./run.sh --port 8972 --https-port 8443" >&2
    exit 1
  fi
  echo "run.sh: ports $HTTP_PORT/$HTTPS_PORT need root -- re-running under sudo."
  exec sudo -E "$0" "${ARGS[@]}" ${STAY_ROOT:+--stay-root}
fi

if [ "$(id -u)" -eq 0 ] && [ "$STAY_ROOT" -eq 0 ] && [ "$HAS_USER" -eq 0 ] \
   && [ -n "${SUDO_USER:-}" ] && [ "${SUDO_USER}" != "root" ]; then
  ARGS+=(--user "$SUDO_USER")
fi

INTERVAL="${BLOCKHAVEN_STATUS_INTERVAL:-4}"
if [ "$HAS_INTERVAL" -eq 0 ]; then
  ARGS+=(--status-interval "$INTERVAL")
fi

# ---------------------------------------------------------------- summary
COLS="$(tput cols 2>/dev/null || echo 80)"
printf '%*s\n' "$COLS" '' | tr ' ' '='
echo "  BLOCKHAVEN launcher"
echo "  python      $PYTHON ($VERSION)"
echo "  workdir     $(pwd)"
if [ "$WANT_TLS" -eq 1 ]; then
  echo "  ports       $HTTP_PORT (redirects) and $HTTPS_PORT (HTTPS)"
else
  echo "  ports       $HTTP_PORT (plain HTTP)"
fi
[ -n "$DOMAIN" ] && echo "  domain      $DOMAIN"
if [ "$WANT_TLS" -eq 1 ]; then
  # A glance at the filesystem only -- main.py does the real checking a
  # moment later, and --tls-check explains it in full.
  # -name '*key*' is excluded so the line names the certificate rather than
  # the key sitting beside it; the numbered copies install_cert.py keeps
  # (fullchain.pem.1) do not match '*.pem' and are skipped for free.
  CERT_HIT="$(find "$CERT_DIR" -maxdepth 3 -type f \( -name '*.pem' -o -name '*.crt' -o -name '*.cer' \) ! -name '*key*' 2>/dev/null | head -n 1)"
  ZIP_HIT="$(find "$CERT_DIR" -maxdepth 2 -type f -name '*.zip' 2>/dev/null | head -n 1)"
  if [ "$SELF_SIGNED" -eq 1 ]; then
    echo "  certificate throwaway self-signed -- browsers will warn"
  elif [ -r "$CERT_DIR/fullchain.pem" ]; then
    echo "  certificate $CERT_DIR/fullchain.pem"
  elif [ -n "$CERT_HIT" ]; then
    echo "  certificate $CERT_DIR/  ($(basename "$CERT_HIT"))"
  elif [ -n "${DOMAIN:-}" ] && [ -r "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
    echo "  certificate /etc/letsencrypt/live/$DOMAIN/"
  elif [ -n "$ZIP_HIT" ]; then
    echo "  certificate $(basename "$ZIP_HIT") is still zipped -- install it with"
    echo "              python3 tools/install_cert.py \"$ZIP_HIT\""
  else
    echo "  certificate none found -- the site will be plain HTTP"
    echo "              python3 tools/install_cert.py <your-bundle.zip>"
  fi
fi
if [ "$(id -u)" -eq 0 ] && [ -n "${SUDO_USER:-}" ] && [ "$STAY_ROOT" -eq 0 ]; then
  echo "  privileges  binding as root, then serving as ${SUDO_USER}"
fi
if [ -f data/blockhaven.sqlite3 ]; then
  SIZE="$(du -h data/blockhaven.sqlite3 2>/dev/null | cut -f1)"
  echo "  database    data/blockhaven.sqlite3 (${SIZE:-?})"
else
  echo "  database    will be created and seeded on this run"
fi
printf '%*s\n' "$COLS" '' | tr ' ' '='
echo

exec "$PYTHON" main.py "${ARGS[@]}"
