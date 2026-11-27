"""The admin dashboard's Instances tab: every game world, and every round
being played in one -- the live ones on its game host and the sleeping ones
the bot director keeps -- with a way for the admin to join any of them.

Admin only, and nowhere else on the site: these routes sit behind the same
``admin_required`` guard as the rest of the dashboard, and the "pin" that
seats the admin in exactly the round chosen is honoured for admins alone
(app/views/worlds_view.py, app/game/host.py).
"""
from __future__ import annotations

from typing import Any, Dict, List

from .. import db
from ..game import registry as game_registry
from ..http.router import Request
from ..models import worlds
from .base import admin_required, api_error, api_ok, router


def _director():
    try:
        from ..bots import director
        return director.running() or director.get()
    except Exception:
        return None


@router.get("/api/admin/instances/worlds")
@admin_required
def instance_worlds(req: Request):
    rows: List[Dict[str, Any]] = []
    for world in worlds.all_worlds():
        status = game_registry.world_status(world["id"])
        rows.append({"id": world["id"], "name": world["name"], "online": bool(status["online"]),
                     "players": int(status["players"]), "humans": int(status.get("humans", 0)),
                     "bots": int(status.get("bots", 0)),
                     "live": int(status.get("live_instances", 0)),
                     "asleep": int(status.get("sleeping_instances", 0)),
                     "max": int(world.get("max_players", 0) or 0),
                     "mode": str(world.get("mode", "") or world.get("engine", "") or "")})
    return api_ok(worlds=rows)


def _live_rounds(world_id: str) -> List[Dict[str, Any]]:
    data = game_registry.raw(world_id) or {}
    out: List[Dict[str, Any]] = []
    for entry in data.get("instances", []):
        players = list(entry.get("players") or [])
        best = max(players, key=lambda p: int(p.get("score", 0) or 0), default=None)
        bots = int(entry.get("bots", 0) or 0)
        count = int(entry.get("count", 0) or 0)
        out.append({"id": int(entry.get("id", 0) or 0), "state": "live", "count": count,
                    "bots": bots, "humans": count - bots, "max": int(entry.get("max", 0) or 0),
                    "round": int(entry.get("round", 1) or 1), "phase": str(entry.get("phase", "") or ""),
                    "summary": str(entry.get("summary", "") or ""),
                    "age": int(float(entry.get("uptime", 0) or 0)),
                    "wave": int(entry.get("wave", 0) or 0),
                    "top": int(best.get("score", 0) or 0) if best else 0,
                    "top_name": str(best.get("name", "")) if best else "",
                    "players": [{"name": str(p.get("name", "")), "score": int(p.get("score", 0) or 0),
                                 "kills": int(p.get("kills", 0) or 0), "team": str(p.get("team", "") or ""),
                                 "bot": bool(p.get("bot"))}
                                for p in sorted(players, key=lambda p: -int(p.get("score", 0) or 0))]})
    return out


@router.get("/api/admin/instances")
@admin_required
def instances(req: Request):
    world_id = str(req.query.get("world") or "")
    world = worlds.get(world_id)
    if world is None:
        return api_error("Unknown world.", 404)
    rows = _live_rounds(world_id)
    director = _director()
    if director is not None and getattr(director, "loaded", False):
        asleep = director.sleeping_rounds(world_id)
        uids = sorted({r["top_uid"] for r in asleep if r.get("top_uid")})
        names: Dict[int, str] = {}
        for start in range(0, len(uids), 500):
            chunk = uids[start:start + 500]
            marks = ",".join("?" * len(chunk))
            for row in db.query("SELECT id, username FROM users WHERE id IN (%s)" % marks, chunk):
                names[int(row["id"])] = row["username"]
        for r in asleep:
            r["top_name"] = names.get(int(r.pop("top_uid", 0) or 0), "")
            r["players"] = []
        rows += asleep
    status = game_registry.world_status(world_id)
    return api_ok(world={"id": world_id, "name": world["name"], "online": bool(status["online"]),
                         "max": int(world.get("max_players", 0) or 0)},
                  instances=rows)
