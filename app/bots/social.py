"""What a bot's social life writes to the database.

Every row here is the same row a person's action would write -- a
``friendships`` row, a ``profile_comments`` row, a ``posts`` row, a
``messages`` row -- so a bot's friends list, wall and inbox are indistinguishable
from anybody else's.  The only thing skipped is the per-account flood
protection (``db.rate_limit``): bots are budgeted centrally by the director,
and leaving a rate-limit bucket behind for every one of a hundred thousand
accounts would be a table full of nothing.

Writes that happen in volume (presence changes, finished game sessions) are
batched into a single transaction each.
"""
from __future__ import annotations

import time
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from .. import db, security
from ..social import comments as comments_model
from ..social import friends as friends_model
from ..social import messages as messages_model
from ..social import posts as posts_model


def _now() -> int:
    return int(time.time())


# ---------------------------------------------------------------- friends
def relationship(a: int, b: int) -> Optional[Dict[str, Any]]:
    return friends_model.relationship(a, b)


def request_friend(from_id: int, to_id: int, max_friends: int = 200) -> str:
    """A bot asks another account to be friends.  Returns the new state."""
    if from_id == to_id:
        return "self"
    existing = friends_model.relationship(from_id, to_id)
    if existing:
        if existing["status"] == "accepted":
            return "friends"
        if int(existing["requester_id"]) != from_id:
            accept(from_id, to_id)
            return "friends"
        return "pending_out"
    if friends_model.count_friends(from_id) >= min(max_friends, friends_model.MAX_FRIENDS):
        return "full"
    low, high = (from_id, to_id) if from_id < to_id else (to_id, from_id)
    now = _now()
    db.execute("INSERT OR IGNORE INTO friendships(user_low,user_high,requester_id,"
               "status,created_at,updated_at) VALUES(?,?,?,'pending',?,?)",
               (low, high, from_id, now, now))
    return "pending_out"


def accept(user_id: int, other_id: int) -> bool:
    rel = friends_model.relationship(user_id, other_id)
    if not rel or rel["status"] != "pending" or int(rel["requester_id"]) == user_id:
        return False
    if friends_model.count_friends(user_id) >= friends_model.MAX_FRIENDS:
        return False
    db.execute("UPDATE friendships SET status='accepted', updated_at=? WHERE id=?",
               (_now(), rel["id"]))
    return True


def decline(user_id: int, other_id: int) -> None:
    friends_model.decline(user_id, other_id)


def pending_batch(after_id: int, limit: int = 400) -> List[Dict[str, Any]]:
    """Pending requests in id order, for the director to deliver."""
    return db.rows_to_dicts(db.query(
        "SELECT id, user_low, user_high, requester_id, created_at FROM friendships"
        " WHERE status='pending' AND id>? ORDER BY id LIMIT ?", (after_id, limit)))


def seed_friendships(pairs: Iterable[Tuple[int, int, int]]) -> int:
    """Accepted friendships that already existed when the bots arrived."""
    rows = []
    for a, b, when in pairs:
        if a == b:
            continue
        low, high = (a, b) if a < b else (b, a)
        rows.append((low, high, a, when, when))
    if not rows:
        return 0
    with db.transaction() as conn:
        conn.executemany(
            "INSERT OR IGNORE INTO friendships(user_low,user_high,requester_id,"
            "status,created_at,updated_at) VALUES(?,?,?,'accepted',?,?)", rows)
    return len(rows)


def friend_counts() -> Dict[int, int]:
    counts: Dict[int, int] = {}
    for row in db.query("SELECT user_low AS u, COUNT(*) AS n FROM friendships"
                        " WHERE status='accepted' GROUP BY user_low"):
        counts[int(row["u"])] = counts.get(int(row["u"]), 0) + int(row["n"])
    for row in db.query("SELECT user_high AS u, COUNT(*) AS n FROM friendships"
                        " WHERE status='accepted' GROUP BY user_high"):
        counts[int(row["u"])] = counts.get(int(row["u"]), 0) + int(row["n"])
    return counts


def friend_ids(uid: int) -> List[int]:
    return friends_model.friend_ids(uid)


def follow(follower: int, followee: int) -> None:
    if follower == followee:
        return
    db.execute("INSERT OR IGNORE INTO follows(follower_id,followee_id,created_at)"
               " VALUES(?,?,?)", (follower, followee, _now()))


# --------------------------------------------------------------- comments
def wall(profile_id: int, limit: int = 14) -> List[Dict[str, Any]]:
    """A profile's newest comments, oldest first, as log entries."""
    rows = db.query(
        "SELECT c.id, c.body, c.created_at, c.author_id, u.username"
        " FROM profile_comments c JOIN users u ON u.id=c.author_id"
        " WHERE c.profile_id=? AND c.hidden=0 ORDER BY c.id DESC LIMIT ?",
        (profile_id, limit))
    return [{"id": int(r["id"]), "who": r["username"], "text": r["body"],
             "at": int(r["created_at"]), "uid": int(r["author_id"])}
            for r in reversed(rows)]


def comment(author: int, profile: int, body: str) -> Optional[int]:
    body = security.clean_text(body, comments_model.MAX_LEN)
    if not body:
        return None
    cur = db.execute(
        "INSERT INTO profile_comments(profile_id,author_id,body,created_at)"
        " VALUES(?,?,?,?)", (profile, author, body, _now()))
    return int(cur.lastrowid)


def wall_open_to(owner: Dict[str, Any], author_id: int) -> bool:
    from ..models import users
    return users.can_view(owner, "wall", author_id, False)


# ------------------------------------------------------------------ posts
def post(author: int, body: str) -> Optional[int]:
    body = security.clean_text(body, posts_model.MAX_LEN)
    if not body:
        return None
    cur = db.execute("INSERT INTO posts(user_id, body, created_at) VALUES(?,?,?)",
                     (author, body, _now()))
    return int(cur.lastrowid)


def recent_posts(author: int, limit: int = 8) -> List[str]:
    return [r["body"] for r in reversed(db.query(
        "SELECT body FROM posts WHERE user_id=? ORDER BY id DESC LIMIT ?",
        (author, limit)))]


def like_something(liker: int, author_ids: Sequence[int]) -> Optional[int]:
    """Like the newest post by one of ``author_ids`` the bot has not liked."""
    if not author_ids:
        return None
    marks = ",".join("?" * len(author_ids))
    row = db.query_one(
        "SELECT p.id FROM posts p WHERE p.user_id IN (%s) AND p.hidden=0"
        " AND p.created_at > ? AND NOT EXISTS (SELECT 1 FROM post_likes l"
        " WHERE l.post_id=p.id AND l.user_id=?) ORDER BY p.id DESC LIMIT 1"
        % marks, tuple(author_ids) + (_now() - 7 * 86400, liker))
    if row is None:
        return None
    try:
        posts_model.toggle_like(int(row["id"]), liker)
    except posts_model.PostError:
        return None
    return int(row["id"])


# --------------------------------------------------------------- messages
def dm(sender: int, recipient_name: str, body: str, subject: str = "") -> Optional[int]:
    body = security.clean_text(body, messages_model.BODY_MAX)
    if not body:
        return None
    from ..models import users
    target = users.get_by_username(recipient_name)
    if target is None:
        return None
    subject = subject or "Re: hey"
    cur = db.execute(
        "INSERT INTO messages(sender_id,recipient_id,subject,body,created_at)"
        " VALUES(?,?,?,?,?)", (sender, int(target["id"]),
                               security.clean_text(subject, messages_model.SUBJECT_MAX, False),
                               body, _now()))
    return int(cur.lastrowid)


def conversation(bot: int, other: int, limit: int = 30) -> List[Dict[str, Any]]:
    return messages_model.conversation(bot, other, limit)


def mark_read(bot: int, other: int) -> None:
    messages_model.mark_thread_read(bot, other)


# ---------------------------------------------------- presence and sessions
def set_last_seen(rows: Sequence[Tuple[int, int]]) -> None:
    """``(when, uid)`` pairs, one transaction."""
    if not rows:
        return
    with db.transaction() as conn:
        conn.executemany("UPDATE users SET last_seen=? WHERE id=?", list(rows))


def write_sessions(rows: Sequence[Dict[str, Any]]) -> None:
    """Finished bot game sessions: stats, visits and visit counters at once."""
    if not rows:
        return
    now = _now()
    stats, visits, per_world, per_user = [], [], {}, {}
    for row in rows:
        stats.append((row["uid"], row["world"], row.get("kills", 0),
                      row.get("deaths", 0), row.get("wins", 0),
                      row.get("rounds", 0), row.get("playtime", 0),
                      row.get("score", 0)))
        if row.get("visit"):
            visits.append((row["world"], row["uid"], row.get("at", now),
                           row.get("playtime", 0)))
            per_world[row["world"]] = per_world.get(row["world"], 0) + 1
            per_user[row["uid"]] = per_user.get(row["uid"], 0) + 1
    with db.transaction() as conn:
        conn.executemany(
            "INSERT INTO game_stats(user_id,world_id,kills,deaths,wins,rounds,"
            "playtime,score) VALUES(?,?,?,?,?,?,?,?)"
            " ON CONFLICT(user_id,world_id) DO UPDATE SET"
            " kills=kills+excluded.kills, deaths=deaths+excluded.deaths,"
            " wins=wins+excluded.wins, rounds=rounds+excluded.rounds,"
            " playtime=playtime+excluded.playtime, score=score+excluded.score",
            stats)
        if visits:
            conn.executemany("INSERT INTO world_visits(world_id,user_id,created_at,"
                             "seconds) VALUES(?,?,?,?)", visits)
        for world, count in per_world.items():
            conn.execute("UPDATE world_stats SET visits=visits+?, updated_at=?"
                         " WHERE world_id=?", (count, now, world))
        if per_user:
            conn.executemany("UPDATE users SET place_visits=place_visits+?"
                             " WHERE id=?", [(n, u) for u, n in per_user.items()])


def prune_bot_visits(keep_days: int = 3) -> int:
    """Old visit rows from bots: the counters keep them, the log need not."""
    cutoff = _now() - keep_days * 86400
    cur = db.execute("DELETE FROM world_visits WHERE created_at < ? AND user_id IN"
                     " (SELECT id FROM users WHERE is_bot=1)", (cutoff,))
    return cur.rowcount or 0
