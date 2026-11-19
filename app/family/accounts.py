"""Parent accounts and parent sessions.

A parent account is made in exactly one place -- the onboarding page,
``/parent-signup`` -- and it is a different kind of thing from a player: its
own table, its own password rules (longer), its own sessions and its own
cookie.  Parent and player usernames share one namespace all the same, so a
name can never mean two different accounts and the ordinary sign-in page can
send a parent on to their dashboard without ambiguity.
"""
from __future__ import annotations

import datetime as _dt
import json
import re
import time
from typing import Any, Dict, Optional

from .. import config, db, security

USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{%d,%d}$" % (config.USERNAME_MIN,
                                                     config.USERNAME_MAX))
EMAIL_RE = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,190}\.[A-Za-z]{2,24}$")

# /parent_<name> is the parent's own page, so a name that reads as one of the
# fixed family pages can never be an account.
RESERVED = {
    "signup", "signup_l", "signin", "signout", "login", "logout", "setup",
    "dashboard", "admin", "api", "help", "child", "children", "kid", "kids",
    "account", "settings", "new", "family", "parent", "parents", "guardian",
    "support", "static", "null", "none", "undefined", "root", "system",
}
RELATIONS = {"parent": "Parent", "guardian": "Guardian"}


class ParentError(Exception):
    """A problem with a parent account request; the text is shown as is."""

    def __init__(self, message: str, field: str = ""):
        super().__init__(message)
        self.field = field


def _now() -> int:
    return int(time.time())


# ------------------------------------------------------------------ lookup

def get(parent_id: int) -> Optional[Dict[str, Any]]:
    return db.row_to_dict(db.query_one(
        "SELECT * FROM family_parents WHERE id=?", (int(parent_id),)))


def get_by_username(username: str) -> Optional[Dict[str, Any]]:
    if not username:
        return None
    return db.row_to_dict(db.query_one(
        "SELECT * FROM family_parents WHERE username_lower=?",
        (str(username).strip().lower(),)))


def get_by_email(email: str) -> Optional[Dict[str, Any]]:
    email = (email or "").strip().lower()
    if not email:
        return None
    return db.row_to_dict(db.query_one(
        "SELECT * FROM family_parents WHERE email_lower=?", (email,)))


def name_taken(username: str) -> bool:
    """Taken by anybody: a parent, a player or a bot."""
    low = (username or "").strip().lower()
    if not low:
        return False
    if db.query_one("SELECT 1 FROM family_parents WHERE username_lower=?", (low,)):
        return True
    return db.query_one("SELECT 1 FROM users WHERE username_lower=?", (low,)) is not None


def parent_name_exists(username: str) -> bool:
    """For the player sign-up page: is this name a parent's?"""
    low = (username or "").strip().lower()
    return bool(low) and db.query_one(
        "SELECT 1 FROM family_parents WHERE username_lower=?", (low,)) is not None


def check_username(username: str) -> Optional[str]:
    """The problem with ``username`` as a new parent name, or None."""
    name = (username or "").strip()
    if not USERNAME_RE.match(name):
        return ("Usernames are %d-%d letters, numbers or underscores."
                % (config.USERNAME_MIN, config.USERNAME_MAX))
    if name.lower() in RESERVED:
        return "That name is reserved -- try another."
    if name_taken(name):
        return "That username is taken."
    return None


# --------------------------------------------------------------- creation

def create(username: str, password: str, display_name: str, email: str,
           relation: str = "parent", timezone: str = "", tz_offset: Any = 0,
           source: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    username = (username or "").strip()
    display_name = security.clean_text(display_name, 40, allow_newlines=False)
    email = (email or "").strip()
    if not display_name:
        raise ParentError("Tell us what to call you.", "display_name")
    if not EMAIL_RE.match(email) or len(email) > 254:
        raise ParentError("That email address doesn't look right.", "email")
    problem = check_username(username)
    if problem:
        raise ParentError(problem, "username")
    if not (config.FAMILY_PASSWORD_MIN <= len(password or "") <= config.PASSWORD_MAX):
        raise ParentError("Use at least %d characters for your password."
                          % config.FAMILY_PASSWORD_MIN, "password")
    if (password or "").lower() == username.lower():
        raise ParentError("Your password can't be your username.", "password")
    if get_by_email(email):
        raise ParentError("There's already a family account with that email. "
                          "Sign in instead?", "email")
    relation = relation if relation in RELATIONS else "parent"
    tz = clean_timezone(timezone)
    try:
        offset = max(-14 * 60, min(14 * 60, int(float(tz_offset or 0))))
    except (TypeError, ValueError):
        offset = 0
    now = _now()
    clean_source = {}
    for key, value in (source or {}).items():
        if isinstance(key, str) and re.match(r"^[a-z_]{2,20}$", key) and value:
            clean_source[key] = security.clean_text(value, 120, allow_newlines=False)
    with db.transaction() as conn:
        # checked again inside the write lock: two tabs racing for one name
        if conn.execute("SELECT 1 FROM family_parents WHERE username_lower=?",
                        (username.lower(),)).fetchone() or \
                conn.execute("SELECT 1 FROM users WHERE username_lower=?",
                             (username.lower(),)).fetchone():
            raise ParentError("That username is taken.", "username")
        cur = conn.execute(
            "INSERT INTO family_parents(username, username_lower, password_hash,"
            " display_name, email, email_lower, relation, timezone, tz_offset,"
            " created_at, last_login, last_seen, source)"
            " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (username, username.lower(), security.hash_password(password),
             display_name, email, email.lower(), relation, tz, offset, now, now,
             now, json.dumps(clean_source, separators=(",", ":"))))
        parent_id = int(cur.lastrowid)
    db.audit(None, "family.parent_create", username,
             {"source": clean_source.get("utm_source", "")})
    from .. import console
    where = clean_source.get("utm_source") or clean_source.get("ref") or "direct"
    console.note("new family account: %s (%s)" % (username, where))
    return get(parent_id)  # type: ignore[return-value]


def authenticate(login: str, password: str) -> Dict[str, Any]:
    """Sign in by username or email."""
    login = (login or "").strip()
    parent = get_by_email(login) if "@" in login else get_by_username(login)
    if parent is None or not security.verify_password(password or "",
                                                      parent["password_hash"]):
        raise ParentError("That username or password isn't right.")
    if parent["is_disabled"]:
        raise ParentError("This family account has been switched off.")
    now = _now()
    db.execute("UPDATE family_parents SET last_login=?, last_seen=? WHERE id=?",
               (now, now, parent["id"]))
    return parent


def try_authenticate(login: str, password: str) -> Optional[Dict[str, Any]]:
    try:
        return authenticate(login, password)
    except ParentError:
        return None


# ---------------------------------------------------------------- profile

def update_profile(parent_id: int, display_name: str, email: str,
                   timezone: str = "", relation: str = "") -> Dict[str, Any]:
    parent = get(parent_id)
    if parent is None:
        raise ParentError("No such account.")
    display_name = security.clean_text(display_name, 40, allow_newlines=False)
    email = (email or "").strip()
    if not display_name:
        raise ParentError("Tell us what to call you.", "display_name")
    if not EMAIL_RE.match(email):
        raise ParentError("That email address doesn't look right.", "email")
    other = get_by_email(email)
    if other is not None and int(other["id"]) != int(parent_id):
        raise ParentError("Another family account already uses that email.", "email")
    tz = clean_timezone(timezone) if timezone else parent["timezone"]
    relation = relation if relation in RELATIONS else parent["relation"]
    db.execute("UPDATE family_parents SET display_name=?, email=?, email_lower=?,"
               " timezone=?, relation=? WHERE id=?",
               (display_name, email, email.lower(), tz, relation, parent_id))
    return get(parent_id)  # type: ignore[return-value]


def change_password(parent_id: int, current: str, new: str) -> None:
    parent = get(parent_id)
    if parent is None:
        raise ParentError("No such account.")
    if not security.verify_password(current or "", parent["password_hash"]):
        raise ParentError("Your current password isn't right.", "current")
    if not (config.FAMILY_PASSWORD_MIN <= len(new or "") <= config.PASSWORD_MAX):
        raise ParentError("Use at least %d characters." % config.FAMILY_PASSWORD_MIN, "new")
    db.execute("UPDATE family_parents SET password_hash=? WHERE id=?",
               (security.hash_password(new), parent_id))
    db.audit(None, "family.parent_password", parent["username"])


def set_setup_state(parent_id: int, state: str) -> None:
    if state in ("new", "later", "done"):
        db.execute("UPDATE family_parents SET setup_state=? WHERE id=?",
                   (state, parent_id))


def delete(parent_id: int) -> int:
    """Remove a family: the parent and every child account they made.

    Returns how many child accounts went with it.  The child accounts are
    real player accounts, so they are deleted as players (cascading through
    their inventory, friendships, messages and the rest), not merely
    unlinked -- a child account left behind with nobody watching it is
    exactly what this feature exists to prevent.
    """
    rows = db.query("SELECT user_id FROM family_children WHERE parent_id=?",
                    (parent_id,))
    ids = [int(r["user_id"]) for r in rows]
    with db.transaction() as conn:
        for uid in ids:
            conn.execute("DELETE FROM users WHERE id=?", (uid,))
        conn.execute("DELETE FROM family_parents WHERE id=?", (parent_id,))
    from . import children
    children.directory.invalidate()
    return len(ids)


# ---------------------------------------------------------------- sessions

def start_session(parent_id: int, user_agent: str = "", ip: str = "") -> Dict[str, str]:
    token = security.new_token(32)
    csrf = security.new_token(24)
    now = _now()
    db.execute("INSERT INTO family_sessions(token, parent_id, csrf, created_at,"
               " expires_at, user_agent, ip) VALUES(?,?,?,?,?,?,?)",
               (token, parent_id, csrf, now, now + config.FAMILY_SESSION_TTL,
                (user_agent or "")[:200], (ip or "")[:64]))
    return {"token": token, "csrf": csrf}


def session_for(token: str) -> Optional[Dict[str, Any]]:
    """The session and its parent, or None (expired, unknown, switched off)."""
    if not token or len(token) > 128:
        return None
    row = db.query_one("SELECT * FROM family_sessions WHERE token=?", (token,))
    if row is None:
        return None
    if int(row["expires_at"]) < _now():
        db.execute("DELETE FROM family_sessions WHERE token=?", (token,))
        return None
    parent = get(int(row["parent_id"]))
    if parent is None or parent["is_disabled"]:
        return None
    if _now() - int(parent.get("last_seen") or 0) > 60:
        db.execute("UPDATE family_parents SET last_seen=? WHERE id=?",
                   (_now(), parent["id"]))
    return {"token": token, "csrf": row["csrf"], "parent": parent}


def end_session(token: str) -> None:
    if token:
        db.execute("DELETE FROM family_sessions WHERE token=?", (token,))


def end_all_sessions(parent_id: int, keep: str = "") -> None:
    db.execute("DELETE FROM family_sessions WHERE parent_id=? AND token<>?",
               (parent_id, keep or ""))


def purge_expired() -> None:
    db.execute("DELETE FROM family_sessions WHERE expires_at < ?", (_now(),))


# --------------------------------------------------------------- the clock

def clean_timezone(name: str) -> str:
    """An IANA zone name the system knows, or ''."""
    name = (name or "").strip()
    if not name or len(name) > 64 or not re.match(r"^[A-Za-z0-9_+\-/]+$", name):
        return ""
    try:
        from zoneinfo import ZoneInfo
        ZoneInfo(name)
    except Exception:
        return ""
    return name


_ZONES: Dict[str, Any] = {}


def tzinfo_for(timezone: str, tz_offset: int = 0) -> _dt.tzinfo:
    """The family's zone: the IANA name when this system can resolve it,
    otherwise the fixed UTC offset the browser reported at sign-up."""
    if timezone:
        zone = _ZONES.get(timezone)
        if zone is None:
            try:
                from zoneinfo import ZoneInfo
                zone = ZoneInfo(timezone)
            except Exception:
                zone = False
            _ZONES[timezone] = zone
        if zone:
            return zone
    return _dt.timezone(_dt.timedelta(minutes=int(tz_offset or 0)))


def local_now(parent: Optional[Dict[str, Any]], at: Optional[float] = None) -> _dt.datetime:
    zone = tzinfo_for((parent or {}).get("timezone", ""),
                      (parent or {}).get("tz_offset", 0))
    return _dt.datetime.fromtimestamp(at if at is not None else time.time(), zone)


def greeting(parent: Dict[str, Any]) -> str:
    hour = local_now(parent).hour
    if hour < 5:
        return "Hello"
    if hour < 12:
        return "Good morning"
    if hour < 18:
        return "Good afternoon"
    return "Good evening"
