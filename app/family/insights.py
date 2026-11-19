"""Everything a parent's dashboard shows about one child.

Read-only and per child: each section is a handful of indexed queries over
that one account, so the dashboard costs the same on a site with ten players
as on one with a hundred thousand.  All times are put in the family's own
time zone (the one the parent signed up from), because "played 40 minutes
on Tuesday" has to mean the parent's Tuesday.
"""
from __future__ import annotations

import datetime as _dt
import re
import time
from typing import Any, Dict, List, Optional

from .. import db
from . import activity, children, controls as rules

DAYS_CHART = 14
DAYS_HEAT = 28
DAYS_WORLDS = 30


def _info(child: Dict[str, Any]) -> Dict[str, Any]:
    info = children.directory.get(child["id"])
    if info is None:
        children.directory.invalidate()
        info = children.directory.get(child["id"])
    return info  # type: ignore[return-value]


def _local(info: Dict[str, Any], at: Optional[float] = None) -> _dt.datetime:
    return _dt.datetime.fromtimestamp(time.time() if at is None else at, info["tz"])


def _world_names() -> Dict[str, Dict[str, Any]]:
    from ..models import worlds
    return {w["id"]: w for w in worlds.every_world()}


def _clock(info: Dict[str, Any], at: Any) -> str:
    try:
        local = _local(info, float(at))
    except (TypeError, ValueError, OSError):
        return ""
    return local.strftime("%I:%M %p").lstrip("0").lower()


def _when(info: Dict[str, Any], at: Any) -> str:
    """``Today 4:32 pm`` / ``Yesterday 7:10 pm`` / ``Mon 12 Nov, 9:05 am``."""
    try:
        local = _local(info, float(at))
    except (TypeError, ValueError, OSError):
        return ""
    today = _local(info).date()
    clock = local.strftime("%I:%M %p").lstrip("0").lower()
    if local.date() == today:
        return "Today " + clock
    if local.date() == today - _dt.timedelta(days=1):
        return "Yesterday " + clock
    if (today - local.date()).days < 7:
        return local.strftime("%a ") + clock
    return local.strftime("%a %d %b, ").replace(" 0", " ") + clock


def duration(seconds: Any) -> str:
    try:
        seconds = int(seconds)
    except (TypeError, ValueError):
        return "0m"
    if seconds < 60:
        return "%ds" % max(0, seconds)
    minutes = seconds // 60
    if minutes < 60:
        return "%dm" % minutes
    hours, minutes = divmod(minutes, 60)
    return ("%dh %02dm" % (hours, minutes)) if minutes else ("%dh" % hours)


# ------------------------------------------------------------------ status

def live_status(child: Dict[str, Any]) -> Dict[str, Any]:
    """What the child is doing right now: playing, on the site, or away."""
    from ..game import registry as game_registry
    from ..models import users
    uid = int(child["id"])
    info = _info(child)
    user = users.get_by_id(uid) or {}
    place = game_registry.human_place(uid)
    names = _world_names()
    sess = activity.tracker.live_session(uid)
    out: Dict[str, Any] = {"state": "offline", "label": "Offline", "world": "",
                           "world_name": "", "since": "", "last_seen": "",
                           "last_seen_ago": ""}
    if place:
        world_id = place[0]
        out.update(state="playing", world=world_id,
                   world_name=names.get(world_id, {}).get("name", world_id),
                   label="Playing %s" % names.get(world_id, {}).get("name", world_id))
        if sess and sess.get("world") == world_id:
            out["since"] = duration(time.time() - sess["start"])
    elif users.is_online(user):
        out.update(state="online", label="On the site")
    last = int(user.get("last_seen") or 0)
    if last:
        from ..views.base import ago
        out["last_seen"] = _when(info, last)
        out["last_seen_ago"] = ago(last)
    out["today"] = activity.today_summary(info)
    out["alerts"] = int(db.scalar("SELECT COUNT(*) FROM family_alerts WHERE user_id=?"
                                  " AND seen_at=0 AND severity IN ('warn','high')", (uid,)))
    out["approvals"] = int(db.scalar("SELECT COUNT(*) FROM family_approvals WHERE"
                                     " child_id=? AND status='waiting'", (uid,)))
    out["paused"] = bool(info.get("paused")) if info else False
    return out


# --------------------------------------------------------------- play time

def _playtime_rows(uid: int, since: str) -> List[Dict[str, Any]]:
    rows = [dict(r) for r in db.query(
        "SELECT day, hour, world_id, seconds FROM family_playtime"
        " WHERE user_id=? AND day>=?", (uid, since))]
    with activity.tracker.lock:
        for (u, day, hour, world_id), seconds in activity.tracker.pending.items():
            if u == uid and day >= since and seconds >= 1:
                rows.append({"day": day, "hour": hour, "world_id": world_id,
                             "seconds": int(seconds)})
    return rows


def playtime(child: Dict[str, Any]) -> Dict[str, Any]:
    uid = int(child["id"])
    info = _info(child)
    c = info["controls"]
    today = _local(info).date()
    first = today - _dt.timedelta(days=max(DAYS_CHART, DAYS_HEAT, DAYS_WORLDS) - 1)
    rows = _playtime_rows(uid, first.strftime("%Y-%m-%d"))
    by_day: Dict[str, int] = {}
    for row in rows:
        by_day[row["day"]] = by_day.get(row["day"], 0) + int(row["seconds"])

    chart = []
    for back in range(DAYS_CHART - 1, -1, -1):
        day = today - _dt.timedelta(days=back)
        key = day.strftime("%Y-%m-%d")
        limit = rules.limit_minutes(c, day)
        chart.append({
            "day": key,
            "dow": day.strftime("%a"),
            "label": day.strftime("%a %d").replace(" 0", " "),
            "short": day.strftime("%a")[0],
            "date": day.strftime("%d %b").lstrip("0"),
            "seconds": by_day.get(key, 0),
            "minutes": round(by_day.get(key, 0) / 60.0, 1),
            "limit": None if limit is None else limit,
            "today": back == 0,
            "weekend": rules.is_weekend(day),
        })

    monday = today - _dt.timedelta(days=today.weekday())
    week = sum(v for k, v in by_day.items() if k >= monday.strftime("%Y-%m-%d"))
    last_monday = monday - _dt.timedelta(days=7)
    last_week = sum(v for k, v in by_day.items()
                    if last_monday.strftime("%Y-%m-%d") <= k < monday.strftime("%Y-%m-%d"))
    seven = [today - _dt.timedelta(days=i) for i in range(7)]
    seven_total = sum(by_day.get(d.strftime("%Y-%m-%d"), 0) for d in seven)
    active_days = sum(1 for d in seven if by_day.get(d.strftime("%Y-%m-%d"), 0) > 0)

    worlds_since = (today - _dt.timedelta(days=DAYS_WORLDS - 1)).strftime("%Y-%m-%d")
    per_world: Dict[str, int] = {}
    for row in rows:
        if row["day"] >= worlds_since:
            per_world[row["world_id"]] = per_world.get(row["world_id"], 0) + int(row["seconds"])
    names = _world_names()
    total_worlds = sum(per_world.values()) or 1
    world_rows = []
    for world_id, seconds in sorted(per_world.items(), key=lambda kv: -kv[1]):
        world = names.get(world_id, {})
        guide = rules.world_guide(world) if world else {"intensity": "action",
                                                         "intensity_label": "Action"}
        world_rows.append({
            "id": world_id, "name": world.get("name", world_id),
            "seconds": seconds, "label": duration(seconds),
            "share": round(100.0 * seconds / total_worlds, 1),
            "color": (world.get("colors") or ["#6aa6e8"])[0],
            "intensity": guide["intensity"], "intensity_label": guide["intensity_label"],
        })

    heat_since = (today - _dt.timedelta(days=DAYS_HEAT - 1)).strftime("%Y-%m-%d")
    heat = [[0] * 24 for _ in range(7)]
    for row in rows:
        if row["day"] < heat_since:
            continue
        try:
            dow = _dt.date.fromisoformat(row["day"]).weekday()
        except ValueError:
            continue
        heat[dow][int(row["hour"]) % 24] += int(row["seconds"])
    peak_hour = None
    hour_totals = [sum(heat[d][h] for d in range(7)) for h in range(24)]
    if any(hour_totals):
        peak_hour = max(range(24), key=lambda h: hour_totals[h])

    return {
        "chart": chart,
        "today": activity.today_summary(info),
        "week_seconds": week, "week_label": duration(week),
        "last_week_seconds": last_week, "last_week_label": duration(last_week),
        "week_change": (None if not last_week else
                        round(100.0 * (week - last_week) / last_week)),
        "avg_seconds": seven_total // 7, "avg_label": duration(seven_total // 7),
        "active_days": active_days,
        "worlds": world_rows,
        "heat": heat,
        "heat_max": max(max(r) for r in heat) if heat else 0,
        "peak_hour": peak_hour,
        "peak_label": (rules.clock_label("%02d:00" % peak_hour) if peak_hour is not None
                       else ""),
    }


def sessions(child: Dict[str, Any], limit: int = 30) -> List[Dict[str, Any]]:
    uid = int(child["id"])
    info = _info(child)
    names = _world_names()
    live = activity.tracker.live_session(uid)
    rows = db.rows_to_dicts(db.query(
        "SELECT * FROM family_play_log WHERE user_id=? ORDER BY id DESC LIMIT ?",
        (uid, limit)))
    out = []
    for row in rows:
        is_live = bool(live and live.get("id") == row["id"])
        ended = live["last"] if is_live else row["ended_at"]
        seconds = (ended - live["start"]) if is_live else row["seconds"]
        world = names.get(row["world_id"], {})
        out.append({
            "world": row["world_id"], "world_name": world.get("name", row["world_id"]),
            "color": (world.get("colors") or ["#6aa6e8"])[0],
            "start": _when(info, row["started_at"]),
            "end": _clock(info, ended),
            "duration": duration(seconds), "seconds": int(seconds),
            "live": is_live,
            "ended_by": {"limit": "Daily limit", "quiet": "Quiet hours",
                         "paused": "Paused", "world": "World switched off"}.get(
                             row.get("ended_by") or "", ""),
        })
    return out


# --------------------------------------------------------------- sign-ins

def _device(agent: str) -> str:
    agent = agent or ""
    if not agent:
        return "Unknown device"
    if "iPad" in agent:
        kind = "iPad"
    elif "iPhone" in agent:
        kind = "iPhone"
    elif "Android" in agent:
        kind = "Android tablet" if "Mobile" not in agent else "Android phone"
    elif "CrOS" in agent:
        kind = "Chromebook"
    elif "Macintosh" in agent or "Mac OS" in agent:
        kind = "Mac"
    elif "Windows" in agent:
        kind = "Windows PC"
    elif "Linux" in agent:
        kind = "Linux computer"
    else:
        kind = "Computer"
    if "Edg/" in agent:
        browser = "Edge"
    elif "Firefox/" in agent:
        browser = "Firefox"
    elif "Chrome/" in agent or "CriOS" in agent:
        browser = "Chrome"
    elif "Safari/" in agent:
        browser = "Safari"
    else:
        browser = ""
    return kind + (" · " + browser if browser else "")


def signins(child: Dict[str, Any]) -> Dict[str, Any]:
    uid = int(child["id"])
    info = _info(child)
    active = db.rows_to_dicts(db.query(
        "SELECT created_at, user_agent FROM sessions WHERE user_id=? AND expires_at>?"
        " ORDER BY created_at DESC LIMIT 10", (uid, int(time.time()))))
    history = db.rows_to_dicts(db.query(
        "SELECT created_at, detail FROM audit_log WHERE actor_id=? AND action='auth.login'"
        " ORDER BY id DESC LIMIT 12", (uid,)))
    return {
        "active": [{"device": _device(r["user_agent"]), "when": _when(info, r["created_at"])}
                   for r in active],
        "history": [{"when": _when(info, r["created_at"]),
                     "by_parent": '"by":"family"' in (r["detail"] or "")} for r in history],
    }


# ------------------------------------------------------------------ social

def social(child: Dict[str, Any]) -> Dict[str, Any]:
    from ..models import users
    from ..social import follows, friends
    uid = int(child["id"])
    info = _info(child)
    since = {}
    for row in db.query("SELECT user_low, user_high, updated_at FROM friendships"
                        " WHERE status='accepted' AND (user_low=? OR user_high=?)",
                        (uid, uid)):
        other = row["user_high"] if row["user_low"] == uid else row["user_low"]
        since[int(other)] = int(row["updated_at"])
    msg_counts = {}
    for row in db.query(
            "SELECT CASE WHEN sender_id=? THEN recipient_id ELSE sender_id END AS other,"
            " COUNT(*) AS n FROM messages WHERE sender_id=? OR recipient_id=?"
            " GROUP BY other", (uid, uid, uid)):
        msg_counts[int(row["other"])] = int(row["n"])
    friend_rows = []
    for f in users.live_seen(friends.list_friends(uid, 200)):
        friend_rows.append({
            "username": f["username"], "id": int(f["id"]),
            "online": users.is_online(f),
            "since": _when(info, since.get(int(f["id"]), 0)).split(",")[0]
                     if since.get(int(f["id"])) else "",
            "since_ts": since.get(int(f["id"]), 0),
            "messages": msg_counts.get(int(f["id"]), 0),
        })
    friend_rows.sort(key=lambda r: -r["since_ts"])
    approvals = db.rows_to_dicts(db.query(
        "SELECT a.id, a.other_id, a.direction, a.status, a.created_at, a.decided_at,"
        " u.username, u.created_at AS joined FROM family_approvals a"
        " JOIN users u ON u.id=a.other_id"
        " WHERE a.child_id=? ORDER BY (a.status='waiting') DESC, a.id DESC LIMIT 30",
        (uid,)))
    from ..views.base import ago
    waiting, decided = [], []
    for row in approvals:
        entry = {"id": int(row["id"]), "username": row["username"],
                 "direction": row["direction"], "status": row["status"],
                 "when": _when(info, row["created_at"]),
                 "joined": ago(row["joined"]),
                 "mutual": len(friends.mutual_friends(uid, int(row["other_id"])))}
        (waiting if row["status"] == "waiting" else decided).append(entry)
    incoming = [{"username": r["username"], "when": _when(info, r["requested_at"])}
                for r in friends.incoming_requests(uid)]
    outgoing = [{"username": r["username"], "when": _when(info, r["requested_at"])}
                for r in friends.outgoing_requests(uid)]
    return {"friends": friend_rows, "count": len(friend_rows),
            "waiting": waiting, "decided": decided[:10],
            "incoming": incoming, "outgoing": outgoing,
            "follows": follows.counts(uid)}


def conversations(child: Dict[str, Any]) -> Dict[str, Any]:
    from ..social import messages
    uid = int(child["id"])
    info = _info(child)
    rows = db.rows_to_dicts(db.query(
        "SELECT CASE WHEN m.sender_id=? THEN m.recipient_id ELSE m.sender_id END AS other,"
        " COUNT(*) AS total, SUM(CASE WHEN m.sender_id=? THEN 1 ELSE 0 END) AS sent,"
        " MAX(m.id) AS last_id, MAX(m.created_at) AS last_at"
        " FROM messages m WHERE m.sender_id=? OR m.recipient_id=?"
        " GROUP BY other ORDER BY last_id DESC LIMIT 40", (uid, uid, uid, uid)))
    out = []
    for row in rows:
        last = db.query_one("SELECT body, sender_id FROM messages WHERE id=?",
                            (row["last_id"],))
        name = db.scalar("SELECT username FROM users WHERE id=?", (row["other"],), "")
        if last is None or not name:
            continue
        out.append({
            "username": name, "total": int(row["total"]),
            "sent": int(row["sent"] or 0), "received": int(row["total"]) - int(row["sent"] or 0),
            "when": _when(info, row["last_at"]),
            "preview": messages.preview(last["body"], 80),
            "last_mine": int(last["sender_id"]) == uid,
        })
    today = _local(info).date()
    first = today - _dt.timedelta(days=13)
    start_ts = int(_dt.datetime.combine(first, _dt.time(0), info["tz"]).timestamp())
    daily = {}
    for row in db.query("SELECT created_at, sender_id FROM messages WHERE"
                        " (sender_id=? OR recipient_id=?) AND created_at>=?",
                        (uid, uid, start_ts)):
        key = _local(info, row["created_at"]).strftime("%Y-%m-%d")
        slot = daily.setdefault(key, [0, 0])
        slot[0 if int(row["sender_id"]) == uid else 1] += 1
    days = []
    for back in range(13, -1, -1):
        day = today - _dt.timedelta(days=back)
        key = day.strftime("%Y-%m-%d")
        sent, received = daily.get(key, [0, 0])
        days.append({"day": key, "short": day.strftime("%a")[0], "sent": sent,
                     "received": received, "label": day.strftime("%a %d").replace(" 0", " ")})
    week_start = int(time.time()) - 7 * 86400
    week = int(db.scalar("SELECT COUNT(*) FROM messages WHERE (sender_id=? OR"
                         " recipient_id=?) AND created_at>?", (uid, uid, week_start)))
    return {"threads": out, "daily": days, "week": week,
            "partners": len(out)}


def transcript(child: Dict[str, Any], other_name: str, limit: int = 80) -> Dict[str, Any]:
    """One conversation in full -- for the parent only, read-only (opening it
    here does not mark anything read on the child's side)."""
    from ..models import users
    uid = int(child["id"])
    info = _info(child)
    other = users.get_by_username(other_name)
    if other is None:
        return {"other": other_name, "rows": []}
    rows = db.rows_to_dicts(db.query(
        "SELECT id, sender_id, subject, body, created_at FROM messages"
        " WHERE (sender_id=? AND recipient_id=?) OR (sender_id=? AND recipient_id=?)"
        " ORDER BY id DESC LIMIT ?", (uid, int(other["id"]), int(other["id"]), uid, limit)))
    out = []
    for row in reversed(rows):
        out.append({"mine": int(row["sender_id"]) == uid,
                    "subject": row["subject"] if row["subject"] not in ("(no subject)", "Re: hey") else "",
                    "body": row["body"], "when": _when(info, row["created_at"])})
    return {"other": other["username"], "rows": out}


def wall(child: Dict[str, Any]) -> Dict[str, Any]:
    uid = int(child["id"])
    info = _info(child)
    received = db.rows_to_dicts(db.query(
        "SELECT c.body, c.created_at, u.username FROM profile_comments c"
        " JOIN users u ON u.id=c.author_id WHERE c.profile_id=? AND c.hidden=0"
        " ORDER BY c.id DESC LIMIT 12", (uid,)))
    written = db.rows_to_dicts(db.query(
        "SELECT c.body, c.created_at, u.username FROM profile_comments c"
        " JOIN users u ON u.id=c.profile_id WHERE c.author_id=? AND c.profile_id<>?"
        " ORDER BY c.id DESC LIMIT 12", (uid, uid)))
    shape = lambda r: {"username": r["username"], "body": r["body"],  # noqa: E731
                       "when": _when(info, r["created_at"])}
    return {"received": [shape(r) for r in received],
            "written": [shape(r) for r in written]}


# ------------------------------------------------------------------ safety

SEVERITY_ORDER = {"high": 0, "warn": 1, "info": 2}


def alerts(child: Dict[str, Any], limit: int = 60) -> Dict[str, Any]:
    uid = int(child["id"])
    info = _info(child)
    rows = db.rows_to_dicts(db.query(
        "SELECT * FROM family_alerts WHERE user_id=? ORDER BY id DESC LIMIT ?",
        (uid, limit)))
    out = []
    for row in rows:
        out.append({"id": int(row["id"]), "kind": row["kind"], "severity": row["severity"],
                    "channel": row["channel"], "title": row["title"],
                    "detail": row["detail"], "excerpt": row["excerpt"],
                    "other": row["other_name"], "when": _when(info, row["created_at"]),
                    "unseen": not row["seen_at"]})
    week_ago = int(time.time()) - 7 * 86400
    blocked_week = int(db.scalar("SELECT COUNT(*) FROM family_alerts WHERE user_id=?"
                                 " AND kind IN ('blocked_out','blocked_in') AND created_at>?",
                                 (uid, week_ago)))
    return {"rows": out,
            "unseen": sum(1 for r in out if r["unseen"] and r["severity"] in ("warn", "high")),
            "blocked_week": blocked_week,
            "total": int(db.scalar("SELECT COUNT(*) FROM family_alerts WHERE user_id=?",
                                   (uid,)))}


def mark_alerts_seen(uid: int) -> None:
    db.execute("UPDATE family_alerts SET seen_at=? WHERE user_id=? AND seen_at=0",
               (int(time.time()), uid))


# ---------------------------------------------------------------- spending

def spending(child: Dict[str, Any]) -> Dict[str, Any]:
    from ..models import catalog, economy, inventory
    uid = int(child["id"])
    info = _info(child)
    week_ago = int(time.time()) - 7 * 86400
    spent = int(db.scalar("SELECT COALESCE(-SUM(delta),0) FROM credit_ledger WHERE"
                          " user_id=? AND delta<0 AND created_at>?", (uid, week_ago)))
    earned = int(db.scalar("SELECT COALESCE(SUM(delta),0) FROM credit_ledger WHERE"
                           " user_id=? AND delta>0 AND created_at>?", (uid, week_ago)))
    ledger = [{"delta": int(r["delta"]), "reason": r["reason"],
               "balance": int(r["balance_after"]), "when": _when(info, r["created_at"])}
              for r in economy.history(uid, 20)]
    openings = db.rows_to_dicts(db.query(
        "SELECT item_id, grade, tier, created_at FROM crate_openings WHERE user_id=?"
        " ORDER BY id DESC LIMIT 6", (uid,)))
    crates_opened = int(db.scalar("SELECT COUNT(*) FROM crate_openings WHERE user_id=?",
                                  (uid,)))
    recent_items = []
    for row in inventory.list_for_user(uid)[:10]:
        if row["slot"] in ("crate", "key"):
            continue
        recent_items.append({"name": row["name"], "slot": row["slot_label"],
                             "rarity": row["rarity"], "tier": row["tier"],
                             "item_id": row["item_id"], "source": row["source"],
                             "when": _when(info, row["acquired_at"])})
    return {
        "balance": economy.balance(uid), "spent_week": spent, "earned_week": earned,
        "ledger": ledger, "crates_opened": crates_opened,
        "openings": [{"name": (catalog.get(r["item_id"]) or {}).get("name", r["item_id"]),
                      "grade": r["grade"], "unusual": r["tier"] == "unusual",
                      "when": _when(info, r["created_at"])} for r in openings],
        "items": recent_items[:8],
        "summary": inventory.summary(uid),
    }


# ----------------------------------------------------------- achievements

def achievements(child: Dict[str, Any]) -> Dict[str, Any]:
    from ..models import badges, worlds
    uid = int(child["id"])
    info = _info(child)
    cards = [b for b in badges.collection(uid, with_models=False) if b["earned"]]
    stats = worlds.player_stats(uid)
    names = _world_names()
    per_world = []
    for world_id, row in stats["worlds"].items():
        per_world.append({"name": names.get(world_id, {}).get("name", world_id),
                          "rounds": int(row.get("rounds") or 0),
                          "wins": int(row.get("wins") or 0),
                          "score": int(row.get("score") or 0)})
    per_world.sort(key=lambda r: -r["rounds"])
    return {
        "badges": [{"name": b["name"], "rank": b["rank"], "tier": b["tier_label"],
                    "color": b["color"], "game": b["game_name"],
                    "description": b["description"], "level": b["level"],
                    "when": _when(info, b["awarded_at"]).split(",")[0]} for b in cards[:24]],
        "badge_count": len(cards), "badge_total": len(badges.BADGES),
        "rounds": int(stats["total"]["rounds"]), "wins": int(stats["total"]["wins"]),
        "score": int(stats["total"]["score"]),
        "worlds": per_world,
    }


# ---------------------------------------------------------------- controls

def controls_view(child: Dict[str, Any]) -> Dict[str, Any]:
    from ..models import worlds
    info = _info(child)
    c = info["controls"]
    rows = []
    for world in worlds.all_worlds():
        guide = rules.world_guide(world)
        rows.append({"id": world["id"], "name": world["name"],
                     "kind": guide["kind"], "note": guide["note"],
                     "intensity": guide["intensity"],
                     "intensity_label": guide["intensity_label"],
                     "color": (world.get("colors") or ["#6aa6e8"])[0],
                     "allowed": world["id"] not in c["worlds_blocked"]})
    return {"values": c, "worlds": rows, "minute_choices": rules.MINUTE_CHOICES,
            "labels": rules.LABELS, "help": rules.HELP,
            "intensity": rules.INTENSITY}


# -------------------------------------------------------------- everything

def child_report(child: Dict[str, Any]) -> Dict[str, Any]:
    info = _info(child)
    return {
        "status": live_status(child),
        "play": playtime(child),
        "sessions": sessions(child),
        "signins": signins(child),
        "social": social(child),
        "messages": conversations(child),
        "wall": wall(child),
        "alerts": alerts(child),
        "spending": spending(child),
        "achievements": achievements(child),
        "controls": controls_view(child),
        "joined": _when(info, child["created_at"]).split(",")[0],
        "age": info.get("age"),
    }


def family_overview(parent: Dict[str, Any], kids: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """The hub's card for each child: who, what they're doing, today's time."""
    out = []
    for kid in kids:
        info = _info(kid)
        status = live_status(kid)
        today = status["today"]
        week = playtime(kid)
        out.append({
            "id": kid["id"], "username": kid["username"], "first_name": kid["first_name"],
            "age": info.get("age"), "status": status, "today": today,
            "week_label": week["week_label"], "chart": week["chart"][-7:],
            "friends": int(db.scalar("SELECT COUNT(*) FROM friendships WHERE"
                                     " status='accepted' AND (user_low=? OR user_high=?)",
                                     (kid["id"], kid["id"]))),
            "paused": bool(kid["paused"]),
        })
    return out
