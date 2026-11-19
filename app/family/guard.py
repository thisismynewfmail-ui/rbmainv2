"""Enforcement: the hooks the rest of the site calls for child accounts.

Every function here starts with one in-memory lookup (``directory.get``) and
returns at once for any account that is not a child, so the hooks can sit on
the busiest paths -- every message, friend request, comment, purchase and
game join -- without costing players or bots anything.

Two rules hold throughout:

* **Refusals never give a child away.**  Somebody whose message to a child is
  stopped is told it "couldn't be delivered", never why: nothing a stranger
  can see says "this is a child account" or "this account has a parent".
  Only the child (in kid-friendly words) and their own parent learn more.
* **Bots never reach a child in private.**  The synthetic players can share
  a round with a child and talk in the round's public chat (through Safe
  Chat), but they never send a child a friend request, a message or a
  profile comment, and a child cannot open a private line to one.
"""
from __future__ import annotations

import time
from typing import Any, Dict, Optional, Tuple

from .. import db
from . import children, controls as rules, shield

GENERIC_MESSAGE = "That message couldn't be delivered."
GENERIC_FRIEND = "That player isn't taking friend requests right now."
GENERIC_COMMENT = "Comments on this profile are closed."

CHANNEL_LABELS = {
    "message": "a private message",
    "comment": "a profile comment",
    "profile": "their profile's About Me",
    "game": "in-game chat",
}


class Refused(Exception):
    """An action a child's rules do not allow; the text is shown as is."""


def child(uid: Any) -> Optional[Dict[str, Any]]:
    return children.directory.get(uid)


def is_child(uid: Any) -> bool:
    return children.directory.get(uid) is not None


def _is_bot(uid: Any) -> bool:
    try:
        from ..bots import director
        running = director.running()
        if running is not None:
            return bool(running.is_bot(int(uid)))
    except Exception:
        pass
    row = db.query_one("SELECT is_bot FROM users WHERE id=?", (int(uid),))
    return bool(row and row["is_bot"])


def _name(uid: Any) -> str:
    return str(db.scalar("SELECT username FROM users WHERE id=?", (int(uid),), "someone"))


def _friends(a: int, b: int) -> bool:
    from ..social import friends
    return friends.are_friends(int(a), int(b))


# ------------------------------------------------------------------ alerts

def alert(uid: int, kind: str, severity: str, channel: str, title: str,
          detail: str = "", excerpt: str = "", other_name: str = "",
          world_id: str = "") -> None:
    """Tell a child's parent something.  Repeats of the same thing inside a
    couple of minutes are folded into the first, and a child cannot flood
    their parent's dashboard (sixty an hour at most)."""
    now = int(time.time())
    try:
        dup = db.query_one(
            "SELECT 1 FROM family_alerts WHERE user_id=? AND kind=? AND excerpt=?"
            " AND other_name=? AND created_at>?",
            (uid, kind, excerpt[:240], other_name[:40], now - 120))
        if dup:
            return
        recent = int(db.scalar("SELECT COUNT(*) FROM family_alerts WHERE user_id=?"
                               " AND created_at>?", (uid, now - 3600)))
        if recent >= 60:
            return
        db.execute(
            "INSERT INTO family_alerts(user_id, kind, severity, channel, title,"
            " detail, excerpt, other_name, world_id, created_at)"
            " VALUES(?,?,?,?,?,?,?,?,?,?)",
            (uid, kind[:30], severity[:10], channel[:20], title[:120],
             detail[:400], excerpt[:240], other_name[:40], world_id[:40], now))
    except Exception:
        pass


def _first(info: Dict[str, Any]) -> str:
    return info.get("first_name") or "Your child"


def _where(channel: str, world_id: str = "") -> str:
    if channel == "game" and world_id:
        from ..models import worlds
        world = worlds.get_any(world_id)
        return "in-game chat in %s" % (world["name"] if world else world_id)
    return CHANNEL_LABELS.get(channel, channel)


def record_outgoing(uid: int, info: Dict[str, Any], verdict: shield.Verdict,
                    channel: str, text: str, other_name: str = "",
                    world_id: str = "") -> None:
    """The child wrote something Safe Chat stopped or flagged."""
    where = _where(channel, world_id)
    to = (" to %s" % other_name) if other_name else ""
    if verdict.blocked:
        alert(uid, "blocked_out", verdict.severity, channel,
              "Safe Chat stopped a message",
              "%s tried to share %s in %s%s. It wasn't sent."
              % (_first(info), verdict.describe(), where, to),
              shield.excerpt(text), other_name, world_id)
    elif "wellbeing" in verdict.categories:
        alert(uid, "wellbeing", "warn", channel, "A message worth a gentle check-in",
              "%s wrote something in %s%s that can be a sign of feeling low. It may "
              "be nothing -- but it might be a good moment to check in."
              % (_first(info), where, to), shield.excerpt(text), other_name, world_id)
    elif "age" in verdict.categories and channel != "game":
        alert(uid, "age_question", "info", channel, "Asked somebody's age",
              "%s asked about age in %s%s." % (_first(info), where, to),
              shield.excerpt(text), other_name, world_id)


def record_incoming(uid: int, info: Dict[str, Any], verdict: shield.Verdict,
                    channel: str, text: str, other_name: str,
                    world_id: str = "") -> None:
    """Somebody tried to send the child something Safe Chat stopped."""
    if not verdict.blocked:
        if "age" in verdict.categories and channel != "game":
            alert(uid, "age_asked", "info", channel, "Somebody asked their age",
                  "%s asked %s their age in %s." % (other_name, _first(info),
                                                     _where(channel, world_id)),
                  shield.excerpt(text), other_name, world_id)
        return
    alert(uid, "blocked_in", verdict.severity, channel,
          "Safe Chat blocked something sent to %s" % _first(info),
          "%s tried to send %s %s in %s. %s never saw it."
          % (other_name or "Somebody", _first(info), verdict.describe(),
             _where(channel, world_id), _first(info)),
          shield.excerpt(text), other_name, world_id)


# ----------------------------------------------------------------- sign-in

def login_block(user: Dict[str, Any]) -> Optional[str]:
    info = child(user.get("id"))
    if info and info["paused"]:
        return "Your account is paused right now. Ask your grown-up!"
    return None


def session_ok(user: Dict[str, Any]) -> bool:
    info = child(user.get("id"))
    return not (info and info["paused"])


# ----------------------------------------------------------------- messages

def _shown(subject: str, body: str) -> str:
    """A message as the parent's alert quotes it: the subject only when one
    was written (the site fills in "(no subject)" otherwise)."""
    subject = (subject or "").strip()
    if not subject or (subject.startswith("(") and subject.endswith(")")):
        return body
    return "%s \u2014 %s" % (subject, body)


def filter_message(sender_id: int, recipient: Dict[str, Any], subject: str,
                   body: str) -> Tuple[str, str]:
    """Check a private message; returns the (possibly blanked) subject and
    body, or raises :class:`Refused`."""
    rid = int(recipient["id"])
    sender = child(sender_id)
    target = child(rid)
    if sender is None and target is None:
        return subject, body
    if sender is not None:
        if recipient.get("is_bot") or _is_bot(rid):
            raise Refused(GENERIC_MESSAGE)
        mode = sender["controls"]["messages"]
        if mode == "off":
            raise Refused("Messages are switched off on your account.")
        if mode == "friends" and not _friends(sender_id, rid):
            raise Refused("You can only send messages to your friends.")
        verdict = shield.scan(subject + "\n" + body, author_is_child=True)
        if verdict.flagged:
            record_outgoing(sender_id, sender, verdict, "message",
                            _shown(subject, body), recipient["username"])
        if verdict.blocked:
            raise Refused(shield.kid_notice(verdict))
        if verdict.action == "mask":
            subject = shield.scan(subject).masked or subject
            body = shield.scan(body).masked or body
    if target is not None:
        if _is_bot(sender_id):
            raise Refused(GENERIC_MESSAGE)
        mode = target["controls"]["messages"]
        if mode == "off" or (mode == "friends" and not _friends(sender_id, rid)):
            raise Refused(GENERIC_MESSAGE)
        if sender is None:
            verdict = shield.scan(subject + "\n" + body, author_is_child=False)
            if verdict.flagged:
                record_incoming(rid, target, verdict, "message", _shown(subject, body),
                                _name(sender_id))
            if verdict.blocked:
                raise Refused(GENERIC_MESSAGE)
            if verdict.action == "mask":
                subject = shield.scan(subject, author_is_child=False).masked or subject
                body = shield.scan(body, author_is_child=False).masked or body
    return subject, body


# ------------------------------------------------------------------ friends

def queue_approval(child_id: int, other_id: int, direction: str) -> None:
    now = int(time.time())
    db.execute(
        "INSERT INTO family_approvals(child_id, other_id, direction, status, created_at)"
        " VALUES(?,?,?,'waiting',?)"
        " ON CONFLICT(child_id, other_id) DO UPDATE SET direction=excluded.direction,"
        " status='waiting', created_at=excluded.created_at, decided_at=0",
        (child_id, other_id, direction, now))


def waiting_approval(child_id: int, other_id: int) -> bool:
    return db.query_one("SELECT 1 FROM family_approvals WHERE child_id=? AND"
                        " other_id=? AND status='waiting'", (child_id, other_id)) is not None


def on_friend_request(from_id: int, to_id: int) -> Optional[str]:
    """Before a friend request is written.  Returns a state to report instead
    of writing it ("awaiting_parent"), None to carry on, or raises."""
    asker = child(from_id)
    if asker is not None and children.approving(from_id):
        asker = None
    asked = child(to_id)
    if asked is not None and children.approving(to_id):
        asked = None
    if asker is None and asked is None:
        return None
    if asker is not None:
        if _is_bot(to_id):
            raise Refused(GENERIC_FRIEND)
        mode = asker["controls"]["friends"]
        if mode == "off":
            raise Refused("Adding new friends is switched off on your account.")
        if mode == "approve":
            from ..social import friends
            rel = friends.relationship(from_id, to_id)
            if rel and rel["status"] == "accepted":
                return "friends"
            if rel and rel["status"] == "pending":
                if int(rel["requester_id"]) == to_id:
                    queue_approval(from_id, to_id, "in")
                    return "awaiting_parent"
                return "pending_out"
            if asked is not None and asked["controls"]["friends"] == "off":
                raise Refused(GENERIC_FRIEND)
            queue_approval(from_id, to_id, "out")
            return "awaiting_parent"
    if asked is not None:
        if _is_bot(from_id):
            raise Refused(GENERIC_FRIEND)
        if asked["controls"]["friends"] == "off":
            raise Refused(GENERIC_FRIEND)
    return None


def on_friend_accept(user_id: int, other_id: int) -> Optional[str]:
    """Before ``user_id`` accepts ``other_id``'s request."""
    info = child(user_id)
    if info is None or children.approving(user_id):
        return None
    if _is_bot(other_id):
        raise Refused(GENERIC_FRIEND)
    mode = info["controls"]["friends"]
    if mode == "off":
        raise Refused("Adding new friends is switched off on your account.")
    if mode == "approve":
        queue_approval(user_id, other_id, "in")
        return "awaiting_parent"
    return None


def waiting_for(child_id: int) -> list:
    """The friendships this child is waiting on a grown-up for (their own
    friends page shows them)."""
    if not is_child(child_id):
        return []
    return db.rows_to_dicts(db.query(
        "SELECT a.id, a.direction, a.created_at, u.username FROM family_approvals a"
        " JOIN users u ON u.id=a.other_id WHERE a.child_id=? AND a.status='waiting'"
        " ORDER BY a.id DESC LIMIT 20", (child_id,)))


# ----------------------------------------------------------------- comments

def filter_wall_comment(profile_id: int, author_id: int, body: str) -> str:
    """Check a profile comment; returns the (possibly blanked) body."""
    author = child(author_id)
    owner = child(profile_id) if profile_id != author_id else None
    if author is None and owner is None:
        return body
    if author is not None:
        if profile_id != author_id and _is_bot(profile_id):
            raise Refused(GENERIC_COMMENT)
        verdict = shield.scan(body, author_is_child=True)
        if verdict.flagged:
            record_outgoing(author_id, author, verdict, "comment", body,
                            _name(profile_id) if profile_id != author_id else "")
        if verdict.blocked:
            raise Refused(shield.kid_notice(verdict))
        if verdict.action == "mask":
            body = verdict.masked or body
    if owner is not None:
        if _is_bot(author_id):
            raise Refused(GENERIC_COMMENT)
        mode = owner["controls"]["wall"]
        if mode == "off" or (mode == "friends" and not _friends(profile_id, author_id)):
            raise Refused(GENERIC_COMMENT)
        if author is None:
            verdict = shield.scan(body, author_is_child=False)
            if verdict.flagged:
                record_incoming(profile_id, owner, verdict, "comment", body,
                                _name(author_id))
            if verdict.blocked:
                raise Refused(GENERIC_COMMENT)
            if verdict.action == "mask":
                body = verdict.masked or body
    return body


# ------------------------------------------------------------------ profile

_STRICTNESS = {"public": 0, "friends": 1, "private": 2}


def clamp_privacy(user_id: int, settings: Dict[str, str]) -> Dict[str, str]:
    """A child can make their profile more private than their parent's
    rules, never less."""
    info = child(user_id)
    if info is None:
        return settings
    c = info["controls"]
    caps = {
        "friends_list": "friends",
        "wall": {"off": "private", "friends": "friends", "anyone": "public"}[c["wall"]],
        "online": "private" if c["presence"] == "nobody" else "friends",
        "server": "private" if c["presence"] == "nobody" else "friends",
    }
    out = dict(settings)
    for key, cap in caps.items():
        if _STRICTNESS.get(out.get(key, "public"), 0) < _STRICTNESS[cap]:
            out[key] = cap
    return out


def scrub_profile(user_id: int, blurb: str, location: str) -> Tuple[str, str]:
    """A child's About Me never carries contact details, and a child has
    no location line at all."""
    info = child(user_id)
    if info is None:
        return blurb, location
    verdict = shield.scan(blurb or "", author_is_child=True)
    if verdict.flagged:
        record_outgoing(user_id, info, verdict, "profile", blurb or "")
    if verdict.blocked:
        masked = verdict.masked
        blurb = masked if masked and masked != (blurb or "").strip() else ""
    elif verdict.action == "mask":
        blurb = verdict.masked
    return blurb, ""


def may_change_password(user_id: int) -> bool:
    return not is_child(user_id)


# --------------------------------------------------------------------- play

def check_join(uid: int, world_id: str) -> Optional[str]:
    """Why this child may not start a round of ``world_id`` now, or None."""
    info = child(uid)
    if info is None:
        return None
    from . import activity
    reason, _kind = activity.play_block(info, world_id)
    return reason


def ticket_flags(uid: int) -> Optional[Dict[str, Any]]:
    """What the game host needs to know about a child: their chat setting.
    Rides in the signed join ticket, so it cannot be forged."""
    info = child(uid)
    if info is None:
        return None
    return {"chat": info["controls"]["chat"]}


def on_game_report(world_id: str, uid: int, report: Dict[str, Any]) -> None:
    """A game host's word that Safe Chat acted on a child's in-game chat."""
    info = child(uid)
    if info is None:
        return
    event = str(report.get("event", ""))
    categories = tuple(c for c in (report.get("categories") or [])
                       if isinstance(c, str) and c in shield.CATEGORIES)
    if not categories:
        return
    action = max((shield.CATEGORIES[c][0] for c in categories),
                 key=shield.ACTION_RANK.__getitem__)
    severity = max((shield.CATEGORIES[c][1] for c in categories),
                   key=shield.SEVERITY_RANK.__getitem__)
    verdict = shield.Verdict(action, severity, categories, "")
    excerpt = str(report.get("excerpt", ""))[:240]
    other = str(report.get("other", ""))[:40]
    if event == "said":
        record_outgoing(uid, info, verdict, "game", excerpt, "", world_id)
    elif event == "heard":
        record_incoming(uid, info, verdict, "game", excerpt, other, world_id)


# ----------------------------------------------------------------- spending

def check_spend(uid: int, item_id: str = "") -> Optional[str]:
    info = child(uid)
    if info is None:
        return None
    c = info["controls"]
    if item_id:
        from ..models import catalog
        item = catalog.get(item_id)
        if item and item.get("slot") in ("crate", "key") and not c["crates"]:
            return "Crates are switched off on your account."
    if not c["spending"]:
        return "Spending Noogets is switched off on your account."
    return None


def check_crates(uid: int, buying: bool = False) -> Optional[str]:
    info = child(uid)
    if info is None:
        return None
    if not info["controls"]["crates"]:
        return "Crates are switched off on your account."
    if buying and not info["controls"]["spending"]:
        return "Spending Noogets is switched off on your account."
    return None


# --------------------------------------------------------------------- bots

def bot_may_contact(uid: Any) -> bool:
    """False for a child account: bots never reach a child in private."""
    return not is_child(uid)


# ------------------------------------------------------------ the chrome

def banner(user: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """The child's own play-time strip at the top of every page."""
    if not user:
        return None
    info = child(user.get("id"))
    if info is None:
        return None
    from . import activity
    return activity.today_summary(info)
