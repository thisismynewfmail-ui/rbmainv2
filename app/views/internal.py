"""Internal endpoints used by the game host processes.

Requests are authenticated with an HMAC over the raw body using the server
secret, and are only accepted from the loopback interface.
"""
from __future__ import annotations

import json
import time
from typing import Any, Dict

from .. import config, db, security
from ..game import registry as game_registry
from ..http import router as R
from ..http.router import Request
from ..models import worlds
from .base import router

_visit_guard: Dict[str, float] = {}


@router.get("/.well-known/acme-challenge/<token>")
def acme_challenge(req: Request, token: str = ""):
    """Answer Let's Encrypt's HTTP-01 challenge.

    certbot's webroot plugin writes the response into
    ``data/acme/.well-known/acme-challenge/<token>`` and the CA then asks for
    it over PLAIN HTTP on port 80 -- it will not follow a redirect to HTTPS
    for this, and at first issue there is no certificate to redirect to
    anyway.  So the plain listener serves this path itself instead of
    redirecting it, and this route is what it serves.

    Nothing here is secret: the token is a random name the CA just handed out
    and the body is a value only that CA can check.  The path is still pinned
    to the webroot, because a token is attacker-supplied text.
    """
    name = str(token or "")
    # A challenge token is url-safe base64; anything else is somebody
    # fishing, and refusing the lot is cheaper than reasoning about it.
    if not name or len(name) > 128 or not all(
            c.isalnum() or c in "-_" for c in name):
        return R.error(404, "No such challenge.")
    path = config.ACME_WEBROOT / ".well-known" / "acme-challenge" / name
    try:
        body = path.read_bytes()
    except OSError:
        return R.error(404, "No such challenge.")
    return R.Response(body, 200, "text/plain").no_cache()


@router.post("/internal/heartbeat")
def heartbeat(req: Request):
    if req.remote_addr not in ("127.0.0.1", "::1", "localhost"):
        return R.json_response({"ok": False}, 403)
    if not security.check_service_signature(
            req.body, req.headers.get("x-service-signature", "")):
        return R.json_response({"ok": False, "error": "bad signature"}, 403)
    try:
        payload = json.loads(req.body.decode("utf-8"))
    except Exception:
        return R.json_response({"ok": False, "error": "bad json"}, 400)
    world_id = str(payload.get("world", ""))
    if worlds.get(world_id) is None:
        return R.json_response({"ok": False, "error": "unknown world"}, 400)
    before = game_registry.raw(world_id) or {}
    previous = _humans(before)
    game_registry.heartbeat(world_id, payload)
    players = int(payload.get("players", 0))
    humans = _humans(payload)
    status = game_registry.world_status(world_id)
    if status["players"]:
        worlds.note_peak(world_id, int(status["players"]))
    if humans != previous:
        from .. import console
        world = worlds.get(world_id)
        console.note("%s: %d player%s (%+d)"
                     % (world["name"] if world else world_id, humans,
                        "" if humans == 1 else "s", humans - previous))
    for report in payload.get("reports", []) or []:
        try:
            _apply_report(world_id, report)
        except Exception:
            if config.DEBUG:
                import traceback
                traceback.print_exc()
    reply: Dict[str, Any] = {"ok": True, "at": int(time.time())}
    # the bot director answers too: bots arriving and leaving live rounds,
    # rounds that have gone to sleep, and the settings the host plays with
    from ..bots import director as bot_director
    director = bot_director.running()
    if director is not None:
        try:
            reply.update(director.on_heartbeat(world_id, payload))
            from ..bots import config as bot_config
            if int(payload.get("cfg_v", -1)) != bot_config.version():
                reply["cfg"] = bot_config.ingame_section()
        except Exception:
            import traceback
            traceback.print_exc()
    return R.json_response(reply)


def _humans(payload: Dict[str, Any]) -> int:
    total = 0
    for inst in payload.get("instances", []) or []:
        total += int(inst.get("count", 0)) - int(inst.get("bots", 0) or 0)
    return total


def _apply_report(world_id: str, report: Dict[str, Any]) -> None:
    kind = str(report.get("kind", ""))
    user_id = int(report.get("user_id", 0) or 0)
    if user_id <= 0:
        return
    if kind == "visit":
        key = "%s:%d" % (world_id, user_id)
        last = _visit_guard.get(key, 0.0)
        if time.time() - last < 25:
            return
        _visit_guard[key] = time.time()
        worlds.record_visit(world_id, user_id, int(report.get("seconds", 30)))
        db.execute("UPDATE users SET last_seen=? WHERE id=?",
                   (int(time.time()), user_id))
    elif kind == "stats":
        worlds.add_game_stats(
            user_id, world_id,
            kills=int(report.get("kills", 0)),
            deaths=int(report.get("deaths", 0)),
            playtime=int(report.get("playtime", 0)),
            score=int(report.get("score", 0)))
        db.execute("UPDATE users SET last_seen=? WHERE id=?",
                   (int(time.time()), user_id))
    elif kind == "round":
        worlds.add_game_stats(user_id, world_id, rounds=1,
                              wins=1 if report.get("won") else 0)
