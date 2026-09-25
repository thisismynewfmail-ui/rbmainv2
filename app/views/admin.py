"""The admin dashboard at /admin-dashboard.

Any signed-in player who is not an administrator is silently redirected to the
home page, and every mutation goes through exactly the same server side code
paths a normal player's actions would use (economy.adjust, inventory.grant,
...), so the dashboard can never create state the game cannot.
"""
from __future__ import annotations

import os
import time
from typing import Any, Dict, List

from .. import config, db
from ..game import registry as game_registry
from ..http import router as R
from ..http.router import Request
from ..models import avatars, catalog, economy, inventory, users, worlds
from ..social import comments, feed, posts
from .base import admin_required, api_error, api_ok, render, router

SUPERVISOR = None  # set by main.py so the dashboard can show host processes


def set_supervisor(supervisor) -> None:
    global SUPERVISOR
    SUPERVISOR = supervisor


def _live_payload() -> Dict[str, Any]:
    world_rows = []
    for world in worlds.all_worlds():
        status = game_registry.world_status(world["id"])
        stats = worlds.stats(world["id"])
        world_rows.append({
            "id": world["id"], "name": world["name"],
            "players": status["players"], "instances": status["instances"],
            "humans": status.get("humans", status["players"]),
            "bots": status.get("bots", 0),
            "live_instances": status.get("live_instances", status["instances"]),
            "capacity": world["max_players"], "online": status["online"],
            "visits": stats["visits"], "rating": stats["rating"],
            "tick_ms": status.get("tick_ms", 0),
            "instance_list": status.get("instance_list", []),
        })
    snapshot = feed.stats_snapshot()
    money = economy.totals()
    return {
        "at": int(time.time()),
        "worlds": world_rows,
        "site": snapshot,
        "money": money,
        "online_users": users.online_count(),
        "in_game": game_registry.total_players(),
        "hosts": SUPERVISOR.status() if SUPERVISOR else [],
        # NOTE: not called "items" -- that name collides with dict.items in templates
        "item_stats": inventory.global_stats(),
    }


@router.get("/admin-dashboard")
@admin_required
def dashboard(req: Request):
    term = req.query.get("q", "")
    return render(req, "admin.html",
                  live=_live_payload(),
                  user_rows=users.search(term, 40, order="seen"),
                  term=term,
                  audit=db.rows_to_dicts(db.query(
                      "SELECT a.*, u.username FROM audit_log a"
                      " LEFT JOIN users u ON u.id=a.actor_id"
                      " ORDER BY a.id DESC LIMIT 40")),
                  ledger=db.rows_to_dicts(db.query(
                      "SELECT l.*, u.username FROM credit_ledger l"
                      " JOIN users u ON u.id=l.user_id"
                      " ORDER BY l.id DESC LIMIT 25")),
                  catalogue=catalog.ALL_ITEMS,
                  effects=catalog.UNUSUAL_EFFECTS,
                  server={
                      "pid": os.getpid(),
                      "port": config.HTTP_PORT,
                      "python": "%d.%d" % (os.sys.version_info[:2]),
                      "db": str(config.DB_PATH),
                  })


# ------------------------------------------------------------- social graph
NETWORK_LIMIT = 220


def _degrees() -> Dict[int, int]:
    """Accepted-friendship count per account.

    A whole-table aggregate: instant on a small site, and with a large bot
    population the friendships table runs to millions of rows, so it is
    remembered for a while rather than recounted on every refresh of the map.
    """
    def compute() -> Dict[int, int]:
        out: Dict[int, int] = {}
        for row in db.query(
                "SELECT uid, COUNT(*) AS n FROM (SELECT user_low AS uid FROM friendships"
                " WHERE status='accepted' UNION ALL SELECT user_high FROM friendships"
                " WHERE status='accepted') GROUP BY uid"):
            out[int(row["uid"])] = int(row["n"])
        return out
    total = users.count_users()
    return db.cached("admin.degrees", 2.5 if total < 5000 else 45.0, compute)


def _network_payload() -> Dict[str, Any]:
    """Nodes and edges for the animated connection map.

    Everything is derived from the same tables the site itself reads, so the
    graph is a view of live state rather than a second copy of it.  The node
    list is capped -- real people first, then the busiest accounts -- so a
    platform carrying a hundred thousand bots still renders something a
    browser can draw at sixty frames a second, and only the edges between the
    accounts on the map are read.
    """
    degree = _degrees()
    people = db.rows_to_dicts(db.query(
        "SELECT id, username, created_at, last_seen, is_admin, is_banned, is_bot"
        " FROM users WHERE is_bot=0"))
    people.sort(key=lambda u: (-degree.get(int(u["id"]), 0),
                               -int(u["created_at"] or 0)))
    people = people[:NETWORK_LIMIT]
    room = NETWORK_LIMIT - len(people)
    if room > 0:
        bot_ids = [uid for uid, _n in sorted(
            ((uid, n) for uid, n in degree.items()), key=lambda p: -p[1])]
        if bot_ids:
            human_ids = {int(u["id"]) for u in people}
            wanted = [uid for uid in bot_ids if uid not in human_ids][:room * 2]
            for start in range(0, len(wanted), 400):
                chunk = wanted[start:start + 400]
                marks = ",".join("?" * len(chunk))
                people += db.rows_to_dicts(db.query(
                    "SELECT id, username, created_at, last_seen, is_admin, is_banned,"
                    " is_bot FROM users WHERE is_bot=1 AND id IN (%s)" % marks, chunk))
            people.sort(key=lambda u: (u["is_bot"], -degree.get(int(u["id"]), 0)))
            people = people[:NETWORK_LIMIT]
        if len(people) < NETWORK_LIMIT:
            have = {int(u["id"]) for u in people}
            for row in db.rows_to_dicts(db.query(
                    "SELECT id, username, created_at, last_seen, is_admin, is_banned,"
                    " is_bot FROM users WHERE is_bot=1 ORDER BY id DESC LIMIT ?",
                    (NETWORK_LIMIT,))):
                if int(row["id"]) not in have and len(people) < NETWORK_LIMIT:
                    people.append(row)
    keep = {int(u["id"]) for u in people}
    users.live_seen(people)

    in_game = {}
    from ..bots import director as bot_director
    director = bot_director.running()
    for world in worlds.all_worlds():
        for player in game_registry.players_in(world["id"], 400):
            in_game[int(player.get("user_id", 0))] = world["name"]
    names_by_world = {w["id"]: w["name"] for w in worlds.all_worlds()}

    nodes = []
    for row in people:
        uid = int(row["id"])
        playing = in_game.get(uid, "")
        if not playing and row["is_bot"] and director is not None:
            playing = names_by_world.get(director.bot_world(uid) or "", "")
        nodes.append({
            "id": uid,
            "name": row["username"],
            "degree": degree.get(uid, 0),
            "admin": bool(row["is_admin"]),
            "banned": bool(row["is_banned"]),
            "bot": bool(row["is_bot"]),
            "online": users.is_online(row),
            "playing": playing,
            "joined": int(row["created_at"] or 0),
            "last_seen": int(row["last_seen"] or 0),
        })

    ids = sorted(keep)
    edges = []
    friend_rows: List[Dict[str, Any]] = []
    follow_rows: List[Dict[str, Any]] = []
    if ids:
        marks = ",".join("?" * len(ids))
        friend_rows = db.rows_to_dicts(db.query(
            "SELECT user_low, user_high, status FROM friendships WHERE user_low IN (%s)"
            " AND user_high IN (%s)" % (marks, marks), ids + ids))
        follow_rows = db.rows_to_dicts(db.query(
            "SELECT follower_id, followee_id FROM follows WHERE follower_id IN (%s)"
            " AND followee_id IN (%s)" % (marks, marks), ids + ids))
    for row in friend_rows:
        edges.append({"a": int(row["user_low"]), "b": int(row["user_high"]),
                      "kind": "friend" if row["status"] == "accepted" else "pending"})
    seen = {(e["a"], e["b"]) for e in edges}
    for row in follow_rows:
        a, b = int(row["follower_id"]), int(row["followee_id"])
        pair = (a, b) if a < b else (b, a)
        if pair in seen:
            continue
        seen.add(pair)
        edges.append({"a": a, "b": b, "kind": "follow"})

    isolated = sum(1 for n in nodes if not n["degree"])
    return {
        "at": int(time.time()),
        "nodes": nodes,
        "edges": edges,
        "truncated": max(0, users.count_users() - len(nodes)),
        "summary": {
            "people": len(nodes),
            "bots": sum(1 for n in nodes if n["bot"]),
            "friendships": sum(1 for e in edges if e["kind"] == "friend"),
            "pending": sum(1 for e in edges if e["kind"] == "pending"),
            "follows": sum(1 for e in edges if e["kind"] == "follow"),
            "isolated": isolated,
            "online": sum(1 for n in nodes if n["online"]),
            "playing": sum(1 for n in nodes if n["playing"]),
        },
    }


@router.get("/api/admin/live")
@admin_required
def live(req: Request):
    return api_ok(**_live_payload())


@router.get("/api/admin/network")
@admin_required
def network(req: Request):
    return api_ok(**_network_payload())


@router.get("/api/admin/user")
@admin_required
def admin_user(req: Request):
    target = users.get_by_username(req.query.get("username", ""))
    if target is None:
        return api_error("No such player.", 404)
    uid = int(target["id"])
    public = users.public(target)
    public["is_bot"] = bool(target.get("is_bot"))
    return api_ok(user=public,
                  credits=economy.balance(uid),
                  inventory=inventory.list_for_user(uid),
                  ledger=economy.history(uid, 20),
                  avatar=avatars.descriptor(uid, target["username"]),
                  stats=worlds.player_stats(uid))


@router.post("/api/admin/credits")
@admin_required
def admin_credits(req: Request):
    data = req.data()
    target = users.get_by_username(str(data.get("username", "")))
    if target is None:
        return api_error("No such player.")
    mode = str(data.get("mode", "add"))
    try:
        amount = int(data.get("amount", 0))
    except (TypeError, ValueError):
        return api_error("Amount must be a whole number.")
    reason = str(data.get("reason", "")).strip()[:100] or "Admin adjustment"
    actor = int(req.user["id"])
    uid = int(target["id"])
    try:
        if mode == "set":
            balance = economy.set_balance(uid, amount, "Admin set: %s" % reason,
                                          actor)
        else:
            balance = economy.adjust(uid, amount, "Admin: %s" % reason, actor,
                                     allow_negative=True)
    except economy.EconomyError as exc:
        return api_error(str(exc))
    db.audit(actor, "admin.credits", target["username"],
             {"mode": mode, "amount": amount, "balance": balance,
              "reason": reason})
    return api_ok(balance=balance, username=target["username"])


@router.post("/api/admin/grant")
@admin_required
def admin_grant(req: Request):
    data = req.data()
    target = users.get_by_username(str(data.get("username", "")))
    if target is None:
        return api_error("No such player.")
    item_id = str(data.get("item_id", ""))
    if catalog.get(item_id) is None:
        return api_error("Unknown item.")
    tier = str(data.get("tier", "normal"))
    effect = str(data.get("effect", "")) or None
    if tier not in catalog.TIERS:
        return api_error("Unknown tier.")
    if tier == "unusual" and catalog.get(item_id)["slot"] != "hat":
        return api_error("Only hats can be Unusual.")
    row = inventory.grant(int(target["id"]), item_id, source="admin",
                          allow_unusual=False, force_tier=tier,
                          force_effect=effect)
    db.audit(int(req.user["id"]), "admin.grant", target["username"], row)
    return api_ok(item=row)


@router.post("/api/admin/revoke")
@admin_required
def admin_revoke(req: Request):
    data = req.data()
    target = users.get_by_username(str(data.get("username", "")))
    if target is None:
        return api_error("No such player.")
    try:
        inv_id = int(data.get("inv_id", 0))
    except (TypeError, ValueError):
        return api_error("Bad item.")
    row = inventory.get_row(int(target["id"]), inv_id)
    if row is None:
        return api_error("They do not own that.")
    db.execute("DELETE FROM inventory WHERE id=?", (inv_id,))
    avatars.unequip_missing(int(target["id"]))
    db.audit(int(req.user["id"]), "admin.revoke", target["username"],
             {"inv_id": inv_id, "item": row["item_id"]})
    return api_ok()


@router.post("/api/admin/ban")
@admin_required
def admin_ban(req: Request):
    data = req.data()
    target = users.get_by_username(str(data.get("username", "")))
    if target is None:
        return api_error("No such player.")
    if bool(target["is_admin"]):
        return api_error("Administrators cannot be suspended.")
    state = 0 if int(target["is_banned"]) else 1
    db.execute("UPDATE users SET is_banned=? WHERE id=?", (state, target["id"]))
    if state:
        db.execute("DELETE FROM sessions WHERE user_id=?", (target["id"],))
    db.audit(int(req.user["id"]), "admin.ban", target["username"],
             {"banned": bool(state)})
    return api_ok(banned=bool(state))


@router.post("/api/admin/announce")
@admin_required
def admin_announce(req: Request):
    text = str(req.data().get("text", "")).strip()[:200]
    if not text:
        return api_error("Nothing to announce.")
    db.set_meta("announcement", text)
    db.set_meta("announcement_at", str(int(time.time())))
    db.audit(int(req.user["id"]), "admin.announce", "", text)
    return api_ok(text=text)


@router.post("/api/admin/moderate")
@admin_required
def admin_moderate(req: Request):
    data = req.data()
    kind = str(data.get("kind", ""))
    try:
        target_id = int(data.get("id", 0))
    except (TypeError, ValueError):
        return api_error("Bad id.")
    actor = int(req.user["id"])
    if kind == "post":
        posts.delete(target_id, actor, True)
    elif kind == "profile_comment":
        comments.delete_profile_comment(target_id, actor, True)
    elif kind == "post_comment":
        comments.delete_post_comment(target_id, actor, True)
    else:
        return api_error("Unknown target.")
    db.audit(actor, "admin.moderate", kind, {"id": target_id})
    return api_ok()
