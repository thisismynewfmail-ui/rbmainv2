"""The Bots Zone: the admin dashboard's control room for synthetic players.

Everything the Bots Zone shows or changes goes through here, behind the same
``admin_required`` guard as the rest of the dashboard.  Settings are validated
by the schema in :mod:`app.bots.config`; creation and deletion run as
background jobs whose progress the page polls; per-bot actions go through the
director so a bot is never left half in a world.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List

from .. import db
from ..bots import config as bot_config
from ..bots import director as bot_director
from ..bots import factory, llm, names, personas, storage
from ..http.router import Request
from ..models import worlds
from .base import admin_required, api_error, api_ok, router


def _director():
    return bot_director.running() or bot_director.get()


@router.get("/api/admin/bots/overview")
@admin_required
def overview(req: Request):
    director = _director()
    stats = director.stats() if director.loaded else {"loaded": False, "total": 0}
    client = llm.client()
    return api_ok(
        stats=stats,
        population=factory.population(),
        job=factory.job_status(),
        llm=client.snapshot(),
        chatter=director.chatter.snapshot() if director.chatter else {},
        gamechat=director.gamechat.snapshot() if director.gamechat else {},
        curve=director.curve_preview(),
        worlds=[{"id": w["id"], "name": w["name"]} for w in worlds.all_worlds()],
        running=bot_director.running() is not None,
        at=int(time.time()))


@router.get("/api/admin/bots/rounds")
@admin_required
def rounds(req: Request):
    director = _director()
    return api_ok(rounds=director.rounds() if director.loaded else {})


FEED_LIMIT = 40


def _feed_rows(kind: str) -> List[Dict[str, Any]]:
    """The latest social activity involving bots, straight from the tables.

    Every query walks its table newest-first by primary key and stops at the
    limit, so it costs the same with ten bots or two hundred thousand.
    """
    out: List[Dict[str, Any]] = []
    if kind == "friends":
        for r in db.query(
                "SELECT f.status, f.created_at, f.updated_at, a.id AS a_id, a.username AS a,"
                " a.is_bot AS a_bot, b.id AS b_id, b.username AS b, b.is_bot AS b_bot"
                " FROM friendships f JOIN users a ON a.id=f.requester_id"
                " JOIN users b ON b.id = CASE WHEN f.requester_id=f.user_low"
                " THEN f.user_high ELSE f.user_low END"
                " WHERE a.is_bot=1 OR b.is_bot=1 ORDER BY f.id DESC LIMIT ?", (FEED_LIMIT,)):
            out.append({"kind": "friends" if r["status"] == "accepted" else "request",
                        "at": int(r["updated_at"] or r["created_at"]),
                        "who": r["a"], "who_id": r["a_id"], "who_bot": bool(r["a_bot"]),
                        "to": r["b"], "to_id": r["b_id"], "to_bot": bool(r["b_bot"]),
                        "text": ""})
    elif kind == "chatter":
        for r in db.query(
                "SELECT c.body, c.created_at, a.id AS a_id, a.username AS a, a.is_bot AS a_bot,"
                " p.id AS p_id, p.username AS p, p.is_bot AS p_bot"
                " FROM profile_comments c JOIN users a ON a.id=c.author_id"
                " JOIN users p ON p.id=c.profile_id"
                " WHERE a.is_bot=1 OR p.is_bot=1 ORDER BY c.id DESC LIMIT ?", (FEED_LIMIT,)):
            out.append({"kind": "comment", "at": int(r["created_at"]),
                        "who": r["a"], "who_id": r["a_id"], "who_bot": bool(r["a_bot"]),
                        "to": r["p"], "to_id": r["p_id"], "to_bot": bool(r["p_bot"]),
                        "text": r["body"]})
        for r in db.query(
                "SELECT p.body, p.created_at, p.likes, u.id AS a_id, u.username AS a"
                " FROM posts p JOIN users u ON u.id=p.user_id"
                " WHERE u.is_bot=1 ORDER BY p.id DESC LIMIT ?", (FEED_LIMIT // 3,)):
            out.append({"kind": "post", "at": int(r["created_at"]),
                        "who": r["a"], "who_id": r["a_id"], "who_bot": True,
                        "to": "", "to_id": 0, "to_bot": False,
                        "text": r["body"], "likes": int(r["likes"] or 0)})
    elif kind == "messages":
        for r in db.query(
                "SELECT m.body, m.created_at, s.id AS a_id, s.username AS a, s.is_bot AS a_bot,"
                " t.id AS b_id, t.username AS b, t.is_bot AS b_bot"
                " FROM messages m JOIN users s ON s.id=m.sender_id"
                " JOIN users t ON t.id=m.recipient_id"
                " WHERE s.is_bot=1 OR t.is_bot=1 ORDER BY m.id DESC LIMIT ?", (FEED_LIMIT,)):
            out.append({"kind": "dm", "at": int(r["created_at"]),
                        "who": r["a"], "who_id": r["a_id"], "who_bot": bool(r["a_bot"]),
                        "to": r["b"], "to_id": r["b_id"], "to_bot": bool(r["b_bot"]),
                        "text": r["body"]})
    out.sort(key=lambda e: -e["at"])
    return out[:FEED_LIMIT]


@router.get("/api/admin/bots/feed")
@admin_required
def feed(req: Request):
    kind = req.query.get("kind") or "chatter"
    if kind not in ("friends", "chatter", "messages"):
        return api_error("Unknown feed.")
    return api_ok(rows=_feed_rows(kind), kind=kind)


@router.get("/api/admin/bots/schema")
@admin_required
def schema(req: Request):
    director = _director()
    return api_ok(schema=bot_config.schema(), values=bot_config.public_values(),
                  version=bot_config.version(),
                  tag_counts=director.tag_counts() if director.loaded else {},
                  tags=[{"id": t["id"], "label": t["label"], "group": t["group"],
                         "prompt": t["prompt"]} for t in personas.all_tags()],
                  groups=[{"id": g, "exclusive": ex, "core": core, "max": most}
                          for g, ex, core, most in personas.GROUPS])


@router.post("/api/admin/bots/config")
@admin_required
def save_config(req: Request):
    data = req.data()
    changes = data.get("changes") if isinstance(data.get("changes"), dict) else {}
    if not changes:
        return api_error("Nothing to save.")
    applied = bot_config.save(changes)
    db.audit(int(req.user["id"]), "bots.config", "",
             {k: ("(hidden)" if k == "llm.api_key" else v) for k, v in applied.items()})
    if any(k.startswith("llm.") for k in applied):
        import threading
        threading.Thread(target=lambda: llm.client().probe(True), daemon=True).start()
    return api_ok(applied=list(applied), values=bot_config.public_values(),
                  version=bot_config.version())


@router.post("/api/admin/bots/reset")
@admin_required
def reset_section(req: Request):
    section = str(req.data().get("section", ""))
    if section not in {s for s, _l, _b in bot_config.SECTIONS}:
        return api_error("No such section.")
    bot_config.reset(section)
    db.audit(int(req.user["id"]), "bots.config.reset", section)
    return api_ok(values=bot_config.public_values())


# ------------------------------------------------------------------ table
def _rows(ids: List[int]) -> List[Dict[str, Any]]:
    if not ids:
        return []
    marks = ",".join("?" * len(ids))
    rows = db.rows_to_dicts(db.query(
        "SELECT u.id, u.username, u.created_at, u.last_seen, u.blurb, u.credits,"
        " u.is_banned, b.tags,"
        " (SELECT COUNT(*) FROM profile_comments c WHERE c.author_id=u.id) AS comments,"
        " (SELECT body FROM profile_comments c WHERE c.author_id=u.id"
        "   ORDER BY c.id DESC LIMIT 1) AS last_comment,"
        " (SELECT created_at FROM profile_comments c WHERE c.author_id=u.id"
        "   ORDER BY c.id DESC LIMIT 1) AS last_comment_at,"
        " (SELECT COALESCE(SUM(kills),0) FROM game_stats g WHERE g.user_id=u.id) AS kills,"
        " (SELECT COALESCE(SUM(deaths),0) FROM game_stats g WHERE g.user_id=u.id) AS deaths"
        " FROM users u JOIN bot_profiles b ON b.user_id=u.id WHERE u.id IN (%s)" % marks,
        ids))
    order = {uid: index for index, uid in enumerate(ids)}
    rows.sort(key=lambda r: order.get(int(r["id"]), 0))
    director = _director()
    names_by_world = {w["id"]: w["name"] for w in worlds.all_worlds()}
    out = []
    for row in rows:
        presence = director.presence(int(row["id"])) if director.loaded else {}
        tags = personas.parse_tags(row["tags"])
        out.append({
            "id": int(row["id"]), "name": row["username"],
            "tags": [{"id": t, "label": (personas.tag_info(t) or {}).get("label", t),
                      "group": (personas.tag_info(t) or {}).get("group", "")} for t in tags],
            "state": presence.get("state", "offline"),
            "world": names_by_world.get(presence.get("world", ""), ""),
            "world_id": presence.get("world", ""),
            "instance": presence.get("instance", 0),
            "live": presence.get("live", False),
            "since": presence.get("since", 0), "next_at": presence.get("next_at", 0),
            "friends": presence.get("friends", 0),
            "friend_target": presence.get("friend_target", 0),
            "comments": int(row["comments"] or 0),
            "last_comment": row["last_comment"] or "",
            "last_comment_at": int(row["last_comment_at"] or 0),
            "kills": int(row["kills"] or 0), "deaths": int(row["deaths"] or 0),
            "joined": int(row["created_at"] or 0),
            "last_seen": int(row["last_seen"] or 0),
            "credits": int(row["credits"] or 0),
            "banned": bool(row["is_banned"]),
        })
    return out


@router.get("/api/admin/bots/list")
@admin_required
def bot_list(req: Request):
    q = (req.query.get("q") or "").strip().lower().replace("%", "")
    state = req.query.get("state") or ""
    world = req.query.get("world") or ""
    tag = (req.query.get("tag") or "").strip()
    sort = req.query.get("sort") or "recent"
    try:
        page = max(0, int(req.query.get("page") or 0))
        size = max(5, min(200, int(req.query.get("size") or 40)))
    except ValueError:
        page, size = 0, 40
    director = _director()
    if state or world:
        # presence lives in the director's memory: filter there, then read
        # the page's rows from the database
        total, ids = director.select(state, world, 0, 1 << 30)
        if q or tag:
            matched: List[int] = []
            for start in range(0, len(ids), 800):
                chunk = ids[start:start + 800]
                marks = ",".join("?" * len(chunk))
                sql = ("SELECT u.id FROM users u JOIN bot_profiles b ON b.user_id=u.id"
                       " WHERE u.id IN (%s)" % marks)
                params: List[Any] = list(chunk)
                if q:
                    sql += " AND u.username_lower LIKE ?"
                    params.append("%" + q + "%")
                if tag:
                    sql += " AND (',' || b.tags || ',') LIKE ?"
                    params.append("%," + tag + ",%")
                keep = {int(r["id"]) for r in db.query(sql, params)}
                matched.extend(u for u in chunk if u in keep)
            ids = matched
        total = len(ids)
        page_ids = ids[page * size:(page + 1) * size]
    else:
        where = ["u.is_bot=1"]
        params = []
        if q:
            where.append("u.username_lower LIKE ?")
            params.append("%" + q + "%")
        if tag:
            where.append("(',' || b.tags || ',') LIKE ?")
            params.append("%," + tag + ",%")
        order = {"name": "u.username_lower ASC", "joined": "u.created_at DESC",
                 "seen": "u.last_seen DESC", "recent": "u.id DESC"}.get(sort, "u.id DESC")
        clause = " AND ".join(where)
        total = int(db.scalar("SELECT COUNT(*) FROM users u JOIN bot_profiles b"
                              " ON b.user_id=u.id WHERE " + clause, params))
        page_ids = [int(r["id"]) for r in db.query(
            "SELECT u.id FROM users u JOIN bot_profiles b ON b.user_id=u.id WHERE "
            + clause + " ORDER BY " + order + " LIMIT ? OFFSET ?",
            params + [size, page * size])]
    return api_ok(rows=_rows(page_ids), total=total, page=page, size=size)


@router.get("/api/admin/bots/detail")
@admin_required
def bot_detail(req: Request):
    try:
        uid = int(req.query.get("id") or 0)
    except ValueError:
        return api_error("Bad id.")
    row = db.row_to_dict(db.query_one(
        "SELECT u.*, b.tags, b.traits, b.generator, b.created_at AS generated_at"
        " FROM users u JOIN bot_profiles b ON b.user_id=u.id WHERE u.id=?", (uid,)))
    if row is None:
        return api_error("No such bot.", 404)
    director = _director()
    tags = personas.parse_tags(row["tags"])
    traits = personas.unpack_traits(row["traits"])
    friends = db.rows_to_dicts(db.query(
        "SELECT u.id, u.username, u.is_bot FROM friendships f"
        " JOIN users u ON u.id = CASE WHEN f.user_low=? THEN f.user_high ELSE f.user_low END"
        " WHERE f.status='accepted' AND (f.user_low=? OR f.user_high=?) LIMIT 40",
        (uid, uid, uid)))
    written = db.rows_to_dicts(db.query(
        "SELECT c.id, c.body, c.created_at, p.username AS wall FROM profile_comments c"
        " JOIN users p ON p.id=c.profile_id WHERE c.author_id=? ORDER BY c.id DESC LIMIT 12",
        (uid,)))
    wall = db.rows_to_dicts(db.query(
        "SELECT c.id, c.body, c.created_at, a.username AS author, a.is_bot"
        " FROM profile_comments c JOIN users a ON a.id=c.author_id"
        " WHERE c.profile_id=? ORDER BY c.id DESC LIMIT 12", (uid,)))
    posts = db.rows_to_dicts(db.query(
        "SELECT id, body, created_at, likes FROM posts WHERE user_id=?"
        " ORDER BY id DESC LIMIT 8", (uid,)))
    stats = worlds.player_stats(uid)
    pending = director.chatter.pending_for(uid) if director.chatter else {}
    shared = []
    for friend in friends:
        j = director.index_of(int(friend["id"])) if director.loaded else -1
        i = director.index_of(uid) if director.loaded else -1
        friend["shared"] = personas.shared(director.masks[i], director.masks[j]) \
            if i >= 0 and j >= 0 else None
        shared.append(friend)
    return api_ok(
        bot={"id": uid, "name": row["username"], "blurb": row["blurb"],
             "location": row["location"], "joined": row["created_at"],
             "last_seen": row["last_seen"], "credits": row["credits"],
             "visits": row["place_visits"], "banned": bool(row["is_banned"]),
             "generator": row["generator"], "generated_at": row["generated_at"],
             "folder": str(storage.folder(uid, row["username"]))},
        tags=[{"id": t, "label": (personas.tag_info(t) or {}).get("label", t),
               "group": (personas.tag_info(t) or {}).get("group", ""),
               "prompt": (personas.tag_info(t) or {}).get("prompt", "")} for t in tags],
        traits=traits, style=personas.style_notes(traits),
        presence=director.presence(uid) if director.loaded else {},
        friends=shared, written=written, wall=wall, posts=posts, stats=stats,
        pending=pending, logs=storage.list_logs(uid, row["username"]))


@router.get("/api/admin/bots/log")
@admin_required
def bot_log(req: Request):
    try:
        uid = int(req.query.get("id") or 0)
    except ValueError:
        return api_error("Bad id.")
    name = str(req.query.get("name") or "")
    row = db.query_one("SELECT username FROM users WHERE id=? AND is_bot=1", (uid,))
    if row is None:
        return api_error("No such bot.", 404)
    known = {entry["name"] for entry in storage.list_logs(uid, row["username"])}
    if name not in known:
        return api_error("No such log.", 404)
    return api_ok(name=name, entries=storage.tail(uid, row["username"], name, 300))


@router.post("/api/admin/bots/create")
@admin_required
def create(req: Request):
    try:
        count = int(req.data().get("count") or 0)
    except (TypeError, ValueError):
        return api_error("How many?")
    if count <= 0:
        return api_error("Enter how many bots to create.")
    ok, message = factory.start_create(count)
    if not ok:
        return api_error(message)
    db.audit(int(req.user["id"]), "bots.create.start", "", {"count": count})
    return api_ok(message=message, job=factory.job_status())


@router.post("/api/admin/bots/delete")
@admin_required
def delete(req: Request):
    data = req.data()
    if data.get("all"):
        if str(data.get("confirm", "")).strip().upper() != "DELETE ALL BOTS":
            return api_error("Type DELETE ALL BOTS to confirm.")
        ok, message = factory.start_delete(None)
    else:
        ids = [int(v) for v in (data.get("ids") or []) if str(v).isdigit()]
        if not ids:
            return api_error("No bots selected.")
        ok, message = factory.start_delete(ids)
    if not ok:
        return api_error(message)
    db.audit(int(req.user["id"]), "bots.delete.start", "",
             {"all": bool(data.get("all")), "count": len(data.get("ids") or [])})
    return api_ok(message=message, job=factory.job_status())


@router.post("/api/admin/bots/cancel")
@admin_required
def cancel(req: Request):
    return api_ok(cancelled=factory.cancel())


@router.post("/api/admin/bots/action")
@admin_required
def action(req: Request):
    data = req.data()
    try:
        uid = int(data.get("id") or 0)
    except (TypeError, ValueError):
        return api_error("Bad id.")
    verb = str(data.get("action", ""))
    if verb not in ("online", "offline", "leave", "join"):
        return api_error("Unknown action.")
    result = _director().force(uid, verb, str(data.get("world", "")))
    db.audit(int(req.user["id"]), "bots.action", str(uid), {"action": verb,
                                                            "result": result})
    return api_ok(result=result, presence=_director().presence(uid))


@router.post("/api/admin/bots/llm/probe")
@admin_required
def probe(req: Request):
    info = llm.client().probe(force=True)
    return api_ok(llm=llm.client().snapshot(), reachable=bool(info.get("reachable")))


@router.get("/api/admin/bots/llm/template")
@admin_required
def template(req: Request):
    return api_ok(template=llm.client().template_text(),
                  source=llm.client().info.get("template_source", ""))


@router.post("/api/admin/bots/llm/test")
@admin_required
def llm_test(req: Request):
    data = req.data()
    prompt = str(data.get("prompt") or "").strip()[:2000]
    system = str(data.get("system") or "").strip()[:4000]
    if not prompt:
        return api_error("Write a test prompt.")
    messages = ([{"role": "system", "content": system}] if system else []) + \
        [{"role": "user", "content": prompt}]
    started = time.time()
    try:
        result = llm.client().complete(messages, int(data.get("max_tokens") or 120),
                                       timeout=float(bot_config.get("llm.timeout_seconds") or 90))
    except Exception as exc:
        return api_error("The model did not answer: %s" % exc)
    return api_ok(text=llm.clean_output(result.get("text", "")), raw=result.get("text", ""),
                  ms=int((time.time() - started) * 1000), mode=result.get("mode"),
                  prompt_tokens=result.get("prompt_tokens"),
                  completion_tokens=result.get("completion_tokens"))


@router.get("/api/admin/bots/names/preview")
@admin_required
def names_preview(req: Request):
    import random
    rng = random.Random()
    return api_ok(names=names.generate_unique(rng, set(), 24))
