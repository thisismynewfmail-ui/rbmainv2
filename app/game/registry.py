"""Live game-host registry (web-server side).

Game hosts are separate processes.  They push a heartbeat into the web server
every couple of seconds describing their instances; the world browser, the
profile presence badge and the admin dashboard all read from this cache.
"""
from __future__ import annotations

import threading
import time
from typing import Any, Dict, List, Optional, Tuple

from ..db import AttrDict

_lock = threading.RLock()
_hosts: Dict[str, Dict[str, Any]] = {}       # world_id -> heartbeat payload
_backends: Dict[str, Tuple[str, int]] = {}   # world_id -> (host, port)
STALE_AFTER = 20.0


def register_backend(world_id: str, host: str, port: int) -> None:
    with _lock:
        _backends[world_id] = (host, port)


def backend_for(world_id: str) -> Optional[Tuple[str, int]]:
    with _lock:
        return _backends.get(world_id)


def all_backends() -> Dict[str, Tuple[str, int]]:
    with _lock:
        return dict(_backends)


def heartbeat(world_id: str, payload: Dict[str, Any]) -> None:
    payload = dict(payload)
    payload["received_at"] = time.time()
    with _lock:
        _hosts[world_id] = payload


def raw(world_id: str) -> Optional[Dict[str, Any]]:
    with _lock:
        data = _hosts.get(world_id)
    if not data:
        return None
    if time.time() - data.get("received_at", 0) > STALE_AFTER:
        return None
    return data


def _director():
    try:
        from ..bots import director
    except Exception:
        return None
    return director.running()


# Instance rows shown on a page.  A world carrying a few thousand bots has a
# few hundred instances; the browser lists the busiest, not all of them.
LIST_LIMIT = 40


def world_status(world_id: str) -> Dict[str, Any]:
    """Players, instances and the instance list for one world.

    Two sources, one answer: the live instances the world's game host
    reports, and the sleeping ones the bot director keeps (instances whose
    only occupants are bots, which cost nothing until somebody joins them).
    Both are instances as far as anybody browsing can tell, which is the
    point.
    """
    data = raw(world_id)
    if not data:
        return AttrDict({"online": False, "players": 0, "instances": 0,
                         "instance_list": [], "humans": 0, "bots": 0,
                         "live_instances": 0, "sleeping_instances": 0})
    live = [dict(i) for i in data.get("instances", [])]
    live_players = int(data.get("players", 0))
    live_bots = 0
    for entry in live:
        bots = int(entry.get("bots", 0) or 0)
        entry.setdefault("bots", bots)
        entry["humans"] = int(entry.get("count", 0)) - bots
        live_bots += bots
    # an idle live instance with nobody in it is scaffolding, not a server
    # anybody is playing on -- but keep one so the list is never empty of
    # somewhere to go
    shown = [e for e in live if e.get("count")] or live[:1]
    sleeping_players = 0
    sleeping_count = 0
    sleeping: List[Dict[str, Any]] = []
    director = _director()
    if director is not None:
        view = director.world_view(world_id)
        sleeping_players = int(view.get("players", 0))
        sleeping_count = int(view.get("instances", 0))
        sleeping = list(view.get("list", []))
    listing = shown + sleeping
    listing.sort(key=lambda e: (-int(e.get("count", 0)), int(e.get("id", 0))))
    total_instances = len(shown) + sleeping_count
    return AttrDict({
        "online": True,
        "players": live_players + sleeping_players,
        "instances": total_instances,
        "instance_list": listing[:LIST_LIMIT],
        "instances_hidden": max(0, total_instances - min(LIST_LIMIT, len(listing))),
        "humans": live_players - live_bots,
        "bots": live_bots + sleeping_players,
        "live_instances": len(live),
        "sleeping_instances": sleeping_count,
        "uptime": data.get("uptime", 0),
        "tick_ms": data.get("tick_ms", 0),
        "nav": data.get("nav") or {},
    })


def all_status() -> Dict[str, Dict[str, Any]]:
    from ..models import worlds
    return {w["id"]: world_status(w["id"]) for w in worlds.WORLDS}


def total_players() -> int:
    return sum(s["players"] for s in all_status().values())


def player_world(user_id: int) -> Optional[str]:
    from ..models import worlds
    director = _director()
    if director is not None and director.is_bot(user_id):
        world_id = director.bot_world(user_id)
        if not world_id or not raw(world_id):
            return None
        world = worlds.get(world_id)
        return world["name"] if world else world_id
    for world_id in list(_hosts.keys()):
        data = raw(world_id)
        if not data:
            continue
        for inst in data.get("instances", []):
            for player in inst.get("players", []):
                if int(player.get("user_id", 0)) == int(user_id):
                    world = worlds.get(world_id)
                    return world["name"] if world else world_id
    return None


def players_in(world_id: str, limit: int = 0) -> List[Dict[str, Any]]:
    """Everybody in a world: live instances first, then sleeping ones.

    ``limit`` caps the list (a world with hundreds of players does not need
    all of them on one page); live players always come first.
    """
    data = raw(world_id)
    if not data:
        return []
    out: List[Dict[str, Any]] = []
    for inst in data.get("instances", []):
        for player in inst.get("players", []):
            entry = dict(player)
            entry["instance"] = inst.get("id")
            out.append(entry)
    director = _director()
    if director is not None and (not limit or len(out) < limit):
        room = (limit - len(out)) if limit else 400
        extra = director.dormant_players(world_id, room)
        if extra:
            from .. import db
            ids = [int(e["user_id"]) for e in extra]
            names = {}
            for start in range(0, len(ids), 400):
                chunk = ids[start:start + 400]
                marks = ",".join("?" * len(chunk))
                for row in db.query("SELECT id, username FROM users WHERE id IN (%s)"
                                    % marks, chunk):
                    names[int(row["id"])] = row["username"]
            for entry in extra:
                name = names.get(int(entry["user_id"]))
                if name:
                    entry["name"] = name
                    out.append(entry)
    return out[:limit] if limit else out


def human_place(user_id: int) -> Optional[Tuple[str, int]]:
    """(world, instance) a real player is in right now, if any."""
    for world_id in list(_hosts.keys()):
        data = raw(world_id)
        if not data:
            continue
        for inst in data.get("instances", []):
            for player in inst.get("players", []):
                if int(player.get("user_id", 0)) == int(user_id) and not player.get("bot"):
                    return world_id, int(inst.get("id", 0))
    return None


def control(world_id: str, message: Dict[str, Any],
            timeout: float = 3.0) -> Optional[Dict[str, Any]]:
    """One signed request to a world's game host (wake an instance, a line
    of bot chat).  None when the host is down or does not answer."""
    import http.client
    import json

    from .. import security

    backend = backend_for(world_id)
    if backend is None:
        return None
    body = json.dumps(message).encode()
    conn = None
    try:
        conn = http.client.HTTPConnection(backend[0], backend[1], timeout=timeout)
        conn.request("POST", "/control", body, {
            "Content-Type": "application/json",
            "X-Service-Signature": security.service_signature(body),
        })
        response = conn.getresponse()
        return json.loads(response.read().decode("utf-8") or "{}")
    except Exception:
        return None
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


def drop_user_everywhere(user_id: int, reason: str = "",
                         timeout: float = 1.5) -> int:
    """Pull one account out of every running world, now.

    Hosts are separate processes, so this is a short signed POST to each
    host's own port -- the same HMAC the heartbeat uses.  It is synchronous on
    purpose: ``/api/game/join`` calls it *before* it mints a ticket, so by the
    time the browser opens its socket the player's older session has already
    been disconnected rather than being told about it two seconds later.
    Hosts that are down or slow are skipped; the host the new connection lands
    on enforces the same rule again locally, so nothing is lost if one of
    these calls does not land.
    """
    import http.client
    import json

    from .. import security

    if int(user_id or 0) <= 0:
        return 0
    body = json.dumps({"action": "drop", "user_id": int(user_id),
                       "reason": reason}).encode()
    signature = security.service_signature(body)
    dropped = 0
    for world_id, (host, port) in all_backends().items():
        conn = None
        try:
            conn = http.client.HTTPConnection(host, port, timeout=timeout)
            conn.request("POST", "/control", body, {
                "Content-Type": "application/json",
                "X-Service-Signature": signature,
            })
            response = conn.getresponse()
            payload = json.loads(response.read().decode("utf-8") or "{}")
            dropped += int(payload.get("dropped", 0) or 0)
        except Exception:
            continue
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass
    return dropped


def online_player_ids() -> List[int]:
    ids = []
    for world_id in list(_hosts.keys()):
        for player in players_in(world_id):
            ids.append(int(player.get("user_id", 0)))
    return ids
