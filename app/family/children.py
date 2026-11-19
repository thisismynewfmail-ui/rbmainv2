"""Child accounts: made by a parent, played by a child, watched over by both.

A child account is an ordinary ``users`` row -- the child plays, dresses up
and makes friends like anybody -- plus a ``family_children`` row linking it to
the parent who made it.  Every function here that touches a child takes the
parent's id and checks the link first, so a parent can only ever see or
change their own children.

``directory`` is the in-memory index of every child account and its rules.
It is what the enforcement hooks (guard.py) read on every message, friend
request, purchase and game join, so for the overwhelming majority of
accounts -- players and bots -- a check costs one dictionary lookup.
"""
from __future__ import annotations

import json
import re
import threading
import time
from typing import Any, Dict, List, Optional

from .. import config, db, security
from . import accounts, controls as rules, shield


class ChildError(Exception):
    def __init__(self, message: str, field: str = ""):
        super().__init__(message)
        self.field = field


CHILD_PASSWORD_MIN = 6
NAME_RE = re.compile(r"^[^\d<>@#$%^&*=+{}\[\]|\\/]{1,30}$")


def _now() -> int:
    return int(time.time())


# ---------------------------------------------------------------- directory

class Directory:
    """Every child account, its parent's clock and its controls, in memory.

    Reloaded whenever a family write invalidates it, and every TTL seconds
    regardless, so a change made by another thread (or a database edited by
    hand) is never more than a few seconds behind.
    """

    TTL = 20.0

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._kids: Dict[int, Dict[str, Any]] = {}
        self._at = 0.0

    def invalidate(self) -> None:
        with self._lock:
            self._at = 0.0

    def _fresh(self) -> Dict[int, Dict[str, Any]]:
        if time.time() - self._at < self.TTL:
            return self._kids
        with self._lock:
            if time.time() - self._at < self.TTL:
                return self._kids
            kids: Dict[int, Dict[str, Any]] = {}
            try:
                rows = db.query(
                    "SELECT c.user_id, c.parent_id, c.controls, c.paused,"
                    " c.first_name, c.birth_year, p.timezone, p.tz_offset"
                    " FROM family_children c"
                    " JOIN family_parents p ON p.id=c.parent_id")
            except Exception:
                rows = []
            for row in rows:
                try:
                    stored = json.loads(row["controls"] or "{}")
                except (TypeError, ValueError):
                    stored = {}
                age = rules.age_from_year(int(row["birth_year"] or 0))
                kids[int(row["user_id"])] = {
                    "uid": int(row["user_id"]),
                    "parent_id": int(row["parent_id"]),
                    "controls": rules.clean(stored, rules.defaults(age)),
                    "paused": bool(row["paused"]),
                    "first_name": row["first_name"],
                    "age": age,
                    "tz": accounts.tzinfo_for(row["timezone"], row["tz_offset"]),
                }
            self._kids = kids
            self._at = time.time()
            return kids

    def get(self, uid: Any) -> Optional[Dict[str, Any]]:
        try:
            return self._fresh().get(int(uid))
        except (TypeError, ValueError):
            return None

    def is_child(self, uid: Any) -> bool:
        return self.get(uid) is not None

    def ids(self) -> frozenset:
        return frozenset(self._fresh().keys())


directory = Directory()


# --------------------------------------------------------------- creating

def count_for(parent_id: int) -> int:
    return int(db.scalar("SELECT COUNT(*) FROM family_children WHERE parent_id=?",
                         (parent_id,)))


def check_username(username: str) -> Optional[str]:
    name = (username or "").strip()
    if not security.valid_username(name):
        return ("Usernames are %d-%d letters, numbers or underscores."
                % (config.USERNAME_MIN, config.USERNAME_MAX))
    if shield._phone_spans(name) or re.search(r"\d{7,}", name):
        return "That looks like a phone number -- pick something else."
    if accounts.name_taken(name):
        return "That username is taken -- try adding a word or a number."
    return None


def _clean_first_name(value: str) -> str:
    name = security.clean_text(value, 30, allow_newlines=False)
    if not name or not NAME_RE.match(name):
        raise ChildError("Add your child's first name (just for you -- it's "
                         "never shown to anyone else).", "first_name")
    return name


def _clean_birth_year(value: Any) -> int:
    if value in (None, "", 0, "0"):
        return 0
    try:
        year = int(value)
    except (TypeError, ValueError):
        raise ChildError("Pick their birth year.", "birth_year")
    this_year = time.gmtime().tm_year
    if not this_year - 18 <= year <= this_year - 3:
        raise ChildError("Pick a birth year between %d and %d."
                         % (this_year - 18, this_year - 3), "birth_year")
    return year


def create(parent: Dict[str, Any], first_name: str, birth_year: Any,
           username: str, password: str, look: Optional[Dict[str, Any]] = None,
           controls: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    from ..models import avatars, users
    parent_id = int(parent["id"])
    if count_for(parent_id) >= config.FAMILY_MAX_CHILDREN:
        raise ChildError("A family can have up to %d child accounts."
                         % config.FAMILY_MAX_CHILDREN)
    first = _clean_first_name(first_name)
    year = _clean_birth_year(birth_year)
    username = (username or "").strip()
    problem = check_username(username)
    if problem:
        raise ChildError(problem, "username")
    if not (CHILD_PASSWORD_MIN <= len(password or "") <= config.PASSWORD_MAX):
        raise ChildError("Their password needs at least %d characters."
                         % CHILD_PASSWORD_MIN, "password")
    if password.lower() == username.lower():
        raise ChildError("Their password can't be the same as their username.",
                         "password")
    age = rules.age_from_year(year)
    chosen = rules.clean(controls or {}, rules.defaults(age),
                         known_worlds=_world_ids())
    try:
        user = users.create_user(username, password)
    except users.AuthError as exc:
        raise ChildError(str(exc), "username")
    uid = int(user["id"])
    try:
        slots = {int(r["slot"]) for r in db.query(
            "SELECT slot FROM family_children WHERE parent_id=?", (parent_id,))}
        slot = next(i for i in range(1, config.FAMILY_MAX_CHILDREN + 2)
                    if i not in slots)
        now = _now()
        db.execute(
            "INSERT INTO family_children(user_id, parent_id, first_name, birth_year,"
            " slot, controls, paused, created_at, updated_at)"
            " VALUES(?,?,?,?,?,?,0,?,?)",
            (uid, parent_id, first, year, slot,
             json.dumps(chosen, separators=(",", ":")), now, now))
    except Exception:
        db.execute("DELETE FROM users WHERE id=?", (uid,))
        raise
    directory.invalidate()
    # Safer profile defaults than a self-registered player gets; the clamp in
    # guard.clamp_privacy keeps the child from loosening past the parent's
    # rules later.
    users.set_privacy(uid, {"friends_list": "friends", "server": "friends",
                            "online": "friends", "wall": "friends"})
    _apply_look(uid, look or {})
    accounts.set_setup_state(parent_id, "done")
    db.audit(None, "family.child_create", username)
    return get(parent_id, uid)  # type: ignore[return-value]


def _apply_look(uid: int, look: Dict[str, Any]) -> None:
    from ..models import avatars, catalog
    body = str(look.get("body_type") or "")
    if body in catalog.BODY_TYPES:
        try:
            avatars.set_body_type(uid, body)
        except Exception:
            pass
    colors = look.get("colors") if isinstance(look.get("colors"), dict) else {}
    allowed = {entry["hex"].lower() for entry in catalog.BODY_PALETTE}
    clean = {part: str(value).lower() for part, value in colors.items()
             if part in catalog.BODY_PARTS and str(value).lower() in allowed}
    if clean:
        try:
            avatars.set_colors(uid, clean)
        except Exception:
            pass


def _world_ids() -> List[str]:
    from ..models import worlds
    return [w["id"] for w in worlds.all_worlds()]


# ---------------------------------------------------------------- reading

_COLUMNS = ("c.user_id, c.parent_id, c.first_name, c.birth_year, c.slot,"
            " c.controls, c.paused, c.created_at AS linked_at, c.updated_at,"
            " u.username, u.created_at, u.last_seen, u.last_login, u.credits,"
            " u.place_visits, u.is_banned")


def _shape(row: Any) -> Dict[str, Any]:
    data = dict(row)
    try:
        stored = json.loads(data.get("controls") or "{}")
    except (TypeError, ValueError):
        stored = {}
    age = rules.age_from_year(int(data.get("birth_year") or 0))
    data["age"] = age
    data["controls"] = rules.clean(stored, rules.defaults(age))
    data["paused"] = bool(data.get("paused"))
    data["id"] = int(data["user_id"])
    return db.AttrDict(data)


def list_for(parent_id: int) -> List[Dict[str, Any]]:
    rows = db.query("SELECT %s FROM family_children c JOIN users u ON u.id=c.user_id"
                    " WHERE c.parent_id=? ORDER BY c.slot, c.created_at" % _COLUMNS,
                    (parent_id,))
    return [_shape(r) for r in rows]


def get(parent_id: int, key: Any) -> Optional[Dict[str, Any]]:
    """One of this parent's children, by user id or username; None for
    anybody else's child or any other account at all."""
    if isinstance(key, int) or (isinstance(key, str) and key.isdigit()):
        row = db.query_one("SELECT %s FROM family_children c JOIN users u ON"
                           " u.id=c.user_id WHERE c.user_id=? AND c.parent_id=?"
                           % _COLUMNS, (int(key), parent_id))
    else:
        row = db.query_one("SELECT %s FROM family_children c JOIN users u ON"
                           " u.id=c.user_id WHERE u.username_lower=? AND c.parent_id=?"
                           % _COLUMNS, (str(key or "").strip().lower(), parent_id))
    return _shape(row) if row else None


def parent_of(uid: int) -> Optional[Dict[str, Any]]:
    row = db.query_one("SELECT parent_id FROM family_children WHERE user_id=?", (uid,))
    return accounts.get(int(row["parent_id"])) if row else None


# --------------------------------------------------------------- managing

def _require(parent_id: int, uid: int) -> Dict[str, Any]:
    child = get(parent_id, int(uid))
    if child is None:
        raise ChildError("That isn't one of your children's accounts.")
    return child


def set_controls(parent_id: int, uid: int, raw: Dict[str, Any]) -> Dict[str, Any]:
    from ..models import users
    child = _require(parent_id, uid)
    chosen = rules.clean(raw, child["controls"], known_worlds=_world_ids())
    db.execute("UPDATE family_children SET controls=?, updated_at=? WHERE user_id=?",
               (json.dumps(chosen, separators=(",", ":")), _now(), uid))
    directory.invalidate()
    # the profile privacy follows the new rules at once
    users.set_privacy(uid, {})
    db.audit(None, "family.controls", child["username"])
    return chosen


def update_details(parent_id: int, uid: int, first_name: str,
                   birth_year: Any) -> Dict[str, Any]:
    _require(parent_id, uid)
    first = _clean_first_name(first_name)
    year = _clean_birth_year(birth_year)
    db.execute("UPDATE family_children SET first_name=?, birth_year=?, updated_at=?"
               " WHERE user_id=?", (first, year, _now(), uid))
    directory.invalidate()
    return _require(parent_id, uid)


def set_paused(parent_id: int, uid: int, paused: bool) -> bool:
    child = _require(parent_id, uid)
    db.execute("UPDATE family_children SET paused=?, updated_at=? WHERE user_id=?",
               (1 if paused else 0, _now(), uid))
    directory.invalidate()
    if paused:
        sign_out_everywhere(parent_id, uid, "Your account is paused for now. "
                                            "Ask your grown-up!")
    db.audit(None, "family.pause" if paused else "family.resume", child["username"])
    return bool(paused)


def reset_password(parent_id: int, uid: int, password: str) -> None:
    child = _require(parent_id, uid)
    if not (CHILD_PASSWORD_MIN <= len(password or "") <= config.PASSWORD_MAX):
        raise ChildError("Use at least %d characters." % CHILD_PASSWORD_MIN, "password")
    if password.lower() == child["username"].lower():
        raise ChildError("The password can't be the same as the username.", "password")
    db.execute("UPDATE users SET password_hash=? WHERE id=?",
               (security.hash_password(password), uid))
    db.execute("DELETE FROM sessions WHERE user_id=?", (uid,))
    db.audit(None, "family.child_password", child["username"])


def sign_out_everywhere(parent_id: int, uid: int, reason: str = "") -> None:
    _require(parent_id, uid)
    db.execute("DELETE FROM sessions WHERE user_id=?", (uid,))
    try:
        from ..game import registry as game_registry
        threading.Thread(target=game_registry.drop_user_everywhere,
                         args=(uid, reason or "Your grown-up signed you out."),
                         daemon=True).start()
    except Exception:
        pass


def delete(parent_id: int, uid: int) -> None:
    child = _require(parent_id, uid)
    db.execute("DELETE FROM sessions WHERE user_id=?", (uid,))
    db.execute("DELETE FROM users WHERE id=?", (uid,))
    directory.invalidate()
    db.audit(None, "family.child_delete", child["username"])


def remove_friend(parent_id: int, uid: int, other_name: str) -> None:
    from ..models import users
    from ..social import friends
    _require(parent_id, uid)
    other = users.get_by_username(other_name)
    if other is None:
        raise ChildError("No such player.")
    friends.remove(uid, int(other["id"]))
    db.execute("UPDATE family_approvals SET status='declined', decided_at=?"
               " WHERE child_id=? AND other_id=?", (_now(), uid, int(other["id"])))


def decide_approval(parent_id: int, uid: int, approval_id: int,
                    approve: bool) -> str:
    """The parent's answer to a friendship waiting on them."""
    from ..social import friends
    _require(parent_id, uid)
    row = db.query_one("SELECT * FROM family_approvals WHERE id=? AND child_id=?",
                       (int(approval_id), uid))
    if row is None or row["status"] != "waiting":
        raise ChildError("That request has already been answered.")
    other = int(row["other_id"])
    now = _now()
    if not approve:
        if row["direction"] == "in":
            friends.decline(uid, other)
        db.execute("UPDATE family_approvals SET status='declined', decided_at=?"
                   " WHERE id=?", (now, row["id"]))
        return "declined"
    db.execute("UPDATE family_approvals SET status='approved', decided_at=?"
               " WHERE id=?", (now, row["id"]))
    rel = friends.relationship(uid, other)
    state = "approved"
    with _approving(uid):
        try:
            if row["direction"] == "in":
                if rel and rel["status"] == "pending" and int(rel["requester_id"]) == other:
                    friends.accept(uid, other)
                    state = "friends"
                elif rel and rel["status"] == "accepted":
                    state = "friends"
                else:
                    state = "expired"
            else:
                if rel is None:
                    friends.request(uid, other)
                    state = "requested"
                elif rel["status"] == "pending" and int(rel["requester_id"]) == other:
                    friends.accept(uid, other)
                    state = "friends"
                elif rel["status"] == "accepted":
                    state = "friends"
                else:
                    state = "requested"
        except friends.FriendError as exc:
            raise ChildError(str(exc))
    return state


# A parent's OK is the approval, so while it is being carried out the
# approval hooks stand aside for that child (and only on this thread).
_approval_local = threading.local()


class _approving:
    def __init__(self, uid: int):
        self.uid = uid

    def __enter__(self):
        held = getattr(_approval_local, "uids", set())
        held = set(held)
        held.add(self.uid)
        _approval_local.uids = held
        return self

    def __exit__(self, *exc):
        held = set(getattr(_approval_local, "uids", set()))
        held.discard(self.uid)
        _approval_local.uids = held
        return False


def approving(uid: int) -> bool:
    return uid in getattr(_approval_local, "uids", set())


def sign_in_here(parent_id: int, uid: int, user_agent: str, ip: str) -> Dict[str, str]:
    """A player session for the child, started by their parent on this
    device (the "Sign them in on this computer" button)."""
    from ..models import users
    child = _require(parent_id, uid)
    if child["paused"]:
        raise ChildError("Their account is paused -- resume it first.")
    if child.get("is_banned"):
        raise ChildError("This account has been suspended.")
    session = users.start_session(uid, user_agent, ip)
    db.execute("UPDATE users SET last_login=?, last_seen=? WHERE id=?",
               (_now(), _now(), uid))
    db.audit(uid, "auth.login", child["username"], {"ip": ip, "by": "family"})
    return session
