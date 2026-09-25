"""Site-wide activity feed assembled from the other social modules."""
from __future__ import annotations

import time
from typing import Any, Dict, List

from .. import db


def recent_activity(limit: int = 18) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    for row in db.query(
            "SELECT p.id, p.body, p.created_at, u.username FROM posts p"
            " JOIN users u ON u.id=p.user_id WHERE p.hidden=0"
            " ORDER BY p.id DESC LIMIT ?", (limit,)):
        events.append({"kind": "post", "username": row["username"],
                       "text": row["body"], "at": row["created_at"],
                       "link": "/profile/%s" % row["username"]})
    seen_finds = set()
    # Only finds worth reading about reach the feed: an Unusual pull, or an
    # uncommon-or-better item.  Routine purchases are left out of it.
    for row in db.query(
            "SELECT i.acquired_at, i.tier, u.username, i.item_id FROM inventory i"
            " JOIN users u ON u.id=i.user_id WHERE i.source='market'"
            " ORDER BY i.id DESC LIMIT ?", (limit * 6,)):
        from ..models import catalog, inventory
        item = catalog.get(row["item_id"])
        if not item:
            continue
        unusual = row["tier"] == "unusual"
        if not unusual and item.get("rarity", "common") not in inventory.NOTABLE_RARITIES:
            continue
        key = (row["username"], item["id"])
        if key in seen_finds:
            continue
        seen_finds.add(key)
        events.append({
            "kind": "unusual" if unusual else "find",
            "username": row["username"],
            "text": ("pulled an UNUSUAL %s!" % item["name"] if unusual
                     else "picked up the %s %s"
                          % (item.get("rarity", "common"), item["name"])),
            "at": row["acquired_at"],
            "link": "/market?q=%s" % item["name"].replace(" ", "+")})
    for row in db.query(
            "SELECT f.updated_at, a.username AS ua, b.username AS ub"
            " FROM friendships f JOIN users a ON a.id=f.user_low"
            " JOIN users b ON b.id=f.user_high WHERE f.status='accepted'"
            " ORDER BY f.updated_at DESC LIMIT ?", (limit,)):
        events.append({"kind": "friend", "username": row["ua"],
                       "text": "is now friends with %s" % row["ub"],
                       "at": row["updated_at"],
                       "link": "/profile/%s" % row["ub"]})
    # World visits are still recorded -- they are what the visit counters and
    # the world stats are built from -- but they are not news.  "X played
    # Capture The Flag" arrives every thirty seconds somebody is in a round,
    # which is enough to push everything anyone would actually want to read
    # off the bottom of the feed.
    events.sort(key=lambda e: e["at"], reverse=True)
    return events[:limit]


def stats_snapshot() -> Dict[str, int]:
    return dict(db.cached("feed.stats", 10.0, _stats_snapshot))


def _stats_snapshot() -> Dict[str, int]:
    now = int(time.time())
    day = now - 86400
    return {
        "users": int(db.scalar("SELECT COUNT(*) FROM users")),
        "new_users_today": int(db.scalar(
            "SELECT COUNT(*) FROM users WHERE created_at > ?", (day,))),
        "posts": int(db.scalar("SELECT COUNT(*) FROM posts")),
        "messages": int(db.scalar("SELECT COUNT(*) FROM messages")),
        "friendships": int(db.scalar(
            "SELECT COUNT(*) FROM friendships WHERE status='accepted'")),
        "items_owned": int(db.scalar("SELECT COUNT(*) FROM inventory")),
        "unusuals": int(db.scalar(
            "SELECT COUNT(*) FROM inventory WHERE tier='unusual'")),
        "visits": int(db.scalar("SELECT COALESCE(SUM(visits),0) FROM world_stats")),
    }
