"""Per-player notifications: a badge earned, a crate dropped.

Anything that happens to a player while they are not looking at it is
written here once.  The site picks unseen ones up on the poll it already
makes (``/api/social/counts``), shows each as a toast, and marks it seen; a
game host shows a badge the moment it is earned and the site then has nothing
left to say about it.
"""
from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional

from .. import db

# Keep a player's history short: these are toasts, not an inbox.
KEEP = 60


def push(user_id: int, kind: str, title: str, body: str = "",
         data: Optional[Dict[str, Any]] = None) -> int:
    now = int(time.time())
    cur = db.execute(
        "INSERT INTO notifications(user_id,kind,title,body,data,created_at)"
        " VALUES(?,?,?,?,?,?)",
        (int(user_id), kind[:24], title[:120], body[:300],
         json.dumps(data or {}, separators=(",", ":")), now))
    note_id = int(cur.lastrowid)
    # trim the tail now and then rather than on every write
    if note_id % 25 == 0:
        db.execute(
            "DELETE FROM notifications WHERE user_id=? AND id NOT IN"
            " (SELECT id FROM notifications WHERE user_id=? ORDER BY id DESC LIMIT ?)",
            (int(user_id), int(user_id), KEEP))
    return note_id


def _row(row) -> Dict[str, Any]:
    try:
        data = json.loads(row["data"] or "{}")
    except ValueError:
        data = {}
    return {"id": int(row["id"]), "kind": row["kind"], "title": row["title"],
            "body": row["body"], "data": data, "at": int(row["created_at"]),
            "seen": bool(row["seen_at"])}


def unseen(user_id: int, limit: int = 6) -> List[Dict[str, Any]]:
    return [_row(r) for r in db.query(
        "SELECT * FROM notifications WHERE user_id=? AND seen_at=0"
        " ORDER BY id ASC LIMIT ?", (int(user_id), int(limit)))]


def recent(user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
    return [_row(r) for r in db.query(
        "SELECT * FROM notifications WHERE user_id=? ORDER BY id DESC LIMIT ?",
        (int(user_id), int(limit)))]


def mark_seen(user_id: int, ids: List[int]) -> int:
    clean = [int(i) for i in ids if str(i).isdigit()][:50]
    if not clean:
        return 0
    marks = ",".join("?" * len(clean))
    return db.execute(
        "UPDATE notifications SET seen_at=? WHERE user_id=? AND seen_at=0"
        " AND id IN (%s)" % marks,
        [int(time.time()), int(user_id)] + clean).rowcount


def mark_kind_seen(user_id: int, kind: str, key: str, value: Any) -> None:
    """Mark notes of ``kind`` whose data[key] == value as seen (a badge the
    game already announced in the round needs no second toast on the site)."""
    for row in db.query(
            "SELECT id, data FROM notifications WHERE user_id=? AND kind=?"
            " AND seen_at=0", (int(user_id), kind)):
        try:
            if json.loads(row["data"] or "{}").get(key) == value:
                db.execute("UPDATE notifications SET seen_at=? WHERE id=?",
                           (int(time.time()), int(row["id"])))
        except ValueError:
            continue
