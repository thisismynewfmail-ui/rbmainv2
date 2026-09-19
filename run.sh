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
#   ./run.sh                                 HTTP on :80, and a nudge about TLS
#   ./run.sh --domain example.com            HTTPS on :443 with your Let's
#                                            Encrypt certificate, :80 redirects
#   ./run.sh --self-signed                   HTTPS with a throwaway certificate
#   ./run.sh --no-https                      plain HTTP only, as before
#   ./run.sh --port 8972 --no-https          unprivileged, no sudo needed
#   ./run.sh --reset                         wipe the database and re-seed
#   ./run.sh --no-games                      website only
#
# Getting a certificate for a domain (Porkbun or anywhere else -- the
# registrar does not matter, only that the A record points here and port 80
# reaches this machine):
#
#   1. Point the domain's A record at this machine's public address.
#   2. Start the site so port 80 answers:   ./run.sh --domain example.com
#   3. In another shell, ask for the certificate. The server answers the
#      challenge itself, so leave it running:
#        sudo certbot certonly --webroot -w data/acme -d example.com
#   4. Restart:                             ./run.sh --domain example.com
#
# Renewal needs nothing from you as long as port 80 stays open: certbot's
# timer writes into data/acme and the server serves it. Restart afterwards to
# pick the new certificate up (certbot's --deploy-hook is the usual place).
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
STAY_ROOT=0
HAS_USER=0
HAS_INTERVAL=0
DOMAIN="${BLOCKHAVEN_DOMAIN:-}"
ARGS=()
while [ $# -gt 0 ]; do
  case "$1" in
    --port) HTTP_PORT="${2:-}"; ARGS+=("$1" "${2:-}"); shift 2 ;;
    --port=*) HTTP_PORT="${1#*=}"; ARGS+=("$1"); shift ;;
    --https-port) HTTPS_PORT="${2:-}"; ARGS+=("$1" "${2:-}"); shift 2 ;;
    --https-port=*) HTTPS_PORT="${1#*=}"; ARGS+=("$1"); shift ;;
    --domain) DOMAIN="${2:-}"; ARGS+=("$1" "${2:-}"); shift 2 ;;
    --domain=*) DOMAIN="${1#*=}"; ARGS+=("$1"); shift ;;
    --no-https) WANT_TLS=0; ARGS+=("$1"); shift ;;
    --user|--user=*) HAS_USER=1; ARGS+=("$1"); shift ;;
    # Ours, not main.py's: keep the server running as root after it binds.
    --stay-root) STAY_ROOT=1; shift ;;
    --status-interval|--status-interval=*) HAS_INTERVAL=1; ARGS+=("$1"); shift ;;
    *) ARGS+=("$1"); shift ;;
  esac
done

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
