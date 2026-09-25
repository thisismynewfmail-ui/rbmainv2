"""Account creation, authentication, sessions and presence."""
from __future__ import annotations

import json
import re
import time
from typing import Any, Dict, List, Optional

from .. import config, db, security
from . import catalog


class AuthError(Exception):
    pass


def _now() -> int:
    return int(time.time())


def get_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    return db.row_to_dict(db.query_one("SELECT * FROM users WHERE id=?", (user_id,)))


def get_by_username(username: str) -> Optional[Dict[str, Any]]:
    if not username:
        return None
    return db.row_to_dict(db.query_one(
        "SELECT * FROM users WHERE username_lower=?", (username.strip().lower(),)))


def exists(username: str) -> bool:
    return get_by_username(username) is not None


def create_user(username: str, password: str, is_admin: bool = False,
                credits: Optional[int] = None,
                blurb: str = "") -> Dict[str, Any]:
    username = (username or "").strip()
    if not security.valid_username(username):
        raise AuthError(
            "Usernames must be %d-%d characters, letters, numbers and underscores only."
            % (config.USERNAME_MIN, config.USERNAME_MAX))
    if not (config.PASSWORD_MIN <= len(password or "") <= config.PASSWORD_MAX):
        raise AuthError("Passwords must be at least %d characters."
                        % config.PASSWORD_MIN)
    if exists(username):
        raise AuthError("That username is already taken.")

    now = _now()
    start_credits = config.STARTING_CREDITS if credits is None else int(credits)
    with db.transaction() as conn:
        cur = conn.execute(
            "INSERT INTO users(username, username_lower, password_hash, created_at,"
            " last_seen, last_login, credits, is_admin, blurb)"
            " VALUES(?,?,?,?,?,?,?,?,?)",
            (username, username.lower(), security.hash_password(password), now,
             now, now, start_credits, 1 if is_admin else 0,
             security.clean_text(blurb, 400)))
        user_id = int(cur.lastrowid)
        conn.execute(
            "INSERT INTO credit_ledger(user_id, delta, balance_after, reason,"
            " actor_id, created_at) VALUES(?,?,?,?,?,?)",
            (user_id, start_credits, start_credits, "Welcome bonus", None, now))
        conn.execute(
            "INSERT INTO avatars(user_id, colors, equipped, hotbar, body_type,"
            " updated_at) VALUES(?,?,?,?,?,?)",
            (user_id, _json(catalog.DEFAULT_COLORS), _json({}), _json([]),
             catalog.DEFAULT_BODY_TYPE, now))
    # Starter kit is granted through the normal inventory path so every item a
    # player owns exists as a real inventory row.
    from . import inventory, avatars
    for item_id in catalog.STARTER_ITEMS:
        inventory.grant(user_id, item_id, source="starter", allow_unusual=False)
    avatars.apply_defaults(user_id)
    db.audit(user_id, "account.create", username)
    from .. import console
    console.note("new account: %s" % username)
    return get_by_id(user_id)  # type: ignore[return-value]


def _json(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"))


def authenticate(username: str, password: str) -> Dict[str, Any]:
    user = get_by_username(username)
    if not user or not security.verify_password(password, user["password_hash"]):
        raise AuthError("Incorrect username or password.")
    if user["is_banned"]:
        raise AuthError("This account has been suspended.")
    db.execute("UPDATE users SET last_login=?, last_seen=? WHERE id=?",
               (_now(), _now(), user["id"]))
    from .. import console
    console.note("%s signed in" % user["username"])
    return user


def change_password(user_id: int, old_password: str, new_password: str) -> None:
    user = get_by_id(user_id)
    if not user:
        raise AuthError("No such account.")
    if not security.verify_password(old_password, user["password_hash"]):
        raise AuthError("Your current password is not correct.")
    if not (config.PASSWORD_MIN <= len(new_password or "") <= config.PASSWORD_MAX):
        raise AuthError("New password is too short.")
    db.execute("UPDATE users SET password_hash=? WHERE id=?",
               (security.hash_password(new_password), user_id))
    db.execute("DELETE FROM sessions WHERE user_id=?", (user_id,))
    db.audit(user_id, "account.password_change", user["username"])


# ------------------------------------------------------------------ sessions

def start_session(user_id: int, user_agent: str = "", ip: str = "") -> Dict[str, str]:
    token = security.new_token(32)
    csrf = security.new_token(24)
    now = _now()
    db.execute("INSERT INTO sessions(token,user_id,csrf,created_at,expires_at,"
               "user_agent,ip) VALUES(?,?,?,?,?,?,?)",
               (token, user_id, csrf, now, now + config.SESSION_TTL,
                (user_agent or "")[:200], (ip or "")[:64]))
    return {"token": token, "csrf": csrf}


def get_session(token: str) -> Optional[Dict[str, Any]]:
    if not token:
        return None
    row = db.query_one(
        "SELECT s.token, s.user_id, s.csrf, s.expires_at, s.spotlight_seen"
        " FROM sessions s WHERE s.token=?", (token,))
    if not row:
        return None
    if row["expires_at"] < _now():
        db.execute("DELETE FROM sessions WHERE token=?", (token,))
        return None
    return dict(row)


def end_session(token: str) -> None:
    if token:
        db.execute("DELETE FROM sessions WHERE token=?", (token,))


def claim_spotlight(token: str) -> bool:
    """True exactly once per sign-in, for the weekly spotlight banner.

    The flag lives on the session row rather than the account, so it survives
    a reload (the banner does not come back on every page) and is gone the
    moment the player signs out and back in -- a new session, a new greeting.
    The UPDATE is conditional, so two tabs racing each other still only get
    one claim between them.
    """
    if not token:
        return False
    cur = db.execute("UPDATE sessions SET spotlight_seen=1 WHERE token=?"
                     " AND spotlight_seen=0", (token,))
    return bool(cur.rowcount)


def touch(user_id: int) -> None:
    db.execute("UPDATE users SET last_seen=? WHERE id=?", (_now(), user_id))


def purge_expired_sessions() -> None:
    db.execute("DELETE FROM sessions WHERE expires_at < ?", (_now(),))


# ------------------------------------------------------------------ presence
ONLINE_WINDOW = 180


def _bots():
    """The running bot director, or None.

    A bot's presence lives in the director's memory rather than in its
    ``last_seen`` column: a hundred thousand bots touching a column every
    couple of minutes would be the busiest thing the database ever did.
    The column is written when a bot logs in and when it logs out, which is
    exactly what "last seen" means for somebody who is not online.
    """
    try:
        from ..bots import director
    except Exception:
        return None
    return director.running()


def is_online(user: Dict[str, Any]) -> bool:
    if user.get("is_bot"):
        director = _bots()
        if director is not None:
            return director.bot_online(int(user["id"]))
    return (_now() - int(user.get("last_seen") or 0)) < ONLINE_WINDOW


def live_seen(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Give online bots a fresh last-seen, the way an active person has."""
    director = _bots()
    if director is None:
        return rows
    now = _now()
    for row in rows:
        if row.get("is_bot") and director.bot_online(int(row["id"])):
            row["last_seen"] = max(int(row.get("last_seen") or 0),
                                   now - (int(row["id"]) * 37) % 90)
    return rows


def presence_label(user: Dict[str, Any]) -> str:
    from ..game import registry
    playing = registry.player_world(int(user["id"]))
    if playing:
        return "Playing %s" % playing
    return "Online" if is_online(user) else "Offline"


# ------------------------------------------------------------------- profile

def update_profile(user_id: int, blurb: str, location: str) -> None:
    db.execute("UPDATE users SET blurb=?, location=? WHERE id=?",
               (security.clean_text(blurb, 400), security.clean_text(location, 60, False),
                user_id))


def search(term: str, limit: int = 40,
           order: str = "joined") -> List[Dict[str, Any]]:
    """Player lookup.

    ``order`` is "joined" (newest accounts first, which is what the People
    browser shows) or "seen" (most recently active first, used by the admin
    dashboard where recency is the useful sort).
    """
    column = "created_at" if order == "joined" else "last_seen"
    term = (term or "").strip().lower()
    if term:
        rows = db.query(
            "SELECT * FROM users WHERE username_lower LIKE ?"
            " ORDER BY %s DESC, id DESC LIMIT ?" % column,
            ("%" + term.replace("%", "") + "%", limit))
    else:
        rows = db.query("SELECT * FROM users ORDER BY %s DESC, id DESC"
                        " LIMIT ?" % column, (limit,))
    return live_seen(db.rows_to_dicts(rows))


def suggest(term: str, limit: int = 8,
            exclude_id: int = 0) -> List[Dict[str, Any]]:
    """Type-ahead for the "To" box: prefix matches first, then substrings."""
    term = (term or "").strip().lower().replace("%", "")
    if not term:
        return []
    rows = db.query(
        "SELECT id, username, last_seen, is_bot FROM users"
        " WHERE username_lower LIKE ? AND id<>?"
        " ORDER BY (username_lower LIKE ?) DESC, last_seen DESC LIMIT ?",
        ("%" + term + "%", exclude_id, term + "%", limit))
    out = live_seen(db.rows_to_dicts(rows))
    for row in out:
        row.pop("is_bot", None)
    return out


def recent(limit: int = 12) -> List[Dict[str, Any]]:
    return live_seen(db.rows_to_dicts(db.query(
        "SELECT * FROM users ORDER BY created_at DESC LIMIT ?", (limit,))))


def online_users(limit: int = 30) -> List[Dict[str, Any]]:
    """Who is online: people first (most recently active), then bots."""
    cutoff = _now() - ONLINE_WINDOW
    people = db.rows_to_dicts(db.query(
        "SELECT * FROM users WHERE last_seen > ? AND is_bot=0"
        " ORDER BY last_seen DESC LIMIT ?", (cutoff, limit)))
    director = _bots()
    if director is None or len(people) >= limit:
        return people[:limit]
    ids = director.online_sample(limit - len(people))
    if not ids:
        return people
    marks = ",".join("?" * len(ids))
    bots = live_seen(db.rows_to_dicts(db.query(
        "SELECT * FROM users WHERE id IN (%s)" % marks, ids)))
    order = {uid: index for index, uid in enumerate(ids)}
    bots.sort(key=lambda row: order.get(int(row["id"]), 0))
    merged = people + bots
    merged.sort(key=lambda row: -int(row.get("last_seen") or 0))
    return merged[:limit]


def online_count() -> int:
    """People online plus bots online, without listing any of them."""
    cutoff = _now() - ONLINE_WINDOW
    people = int(db.scalar("SELECT COUNT(*) FROM users WHERE last_seen > ?"
                           " AND is_bot=0", (cutoff,)))
    director = _bots()
    return people + (director.online if director is not None else 0)


def count_users() -> int:
    return int(db.scalar("SELECT COUNT(*) FROM users"))


def public(user: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Strip everything that must never leave the server.

    ``is_bot`` never leaves either: to everybody but an administrator a bot
    is just another player.
    """
    if not user:
        return None
    return {
        "id": user["id"],
        "username": user["username"],
        "blurb": user.get("blurb", ""),
        "location": user.get("location", ""),
        "created_at": user.get("created_at", 0),
        "last_seen": user.get("last_seen", 0),
        "is_admin": bool(user.get("is_admin")),
        "place_visits": user.get("place_visits", 0),
    }


# -------------------------------------------------------------- preferences
THEMES = ("auto", "light", "dark")

# Who may see a given part of a profile.  "friends" means accepted friends
# only; "private" means nobody but the owner (and administrators).
VISIBILITIES = ("public", "friends", "private")

PRIVACY_FIELDS = {
    "friends_list": "public",
    "stats": "public",
    "inventory": "public",
    "server": "friends",
    "wall": "public",
    "online": "public",
}

PRIVACY_LABELS = [
    ("friends_list", "Who can see my friends list"),
    ("inventory", "Who can see my inventory"),
    ("stats", "Who can see my deaths and K/D"),
    ("server", "Who can see the server I am playing on"),
    ("online", "Who can see when I am online"),
    ("wall", "Who can leave comments on my profile"),
]

MAX_PINNED = 3


# Small per-account interface switches.  They live in one JSON blob so a new
# switch is a key here rather than another column and another migration.
PREF_DEFAULTS: Dict[str, Any] = {
    "messenger": True,       # the floating message bubble, on by default
}


def prefs_of(user: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    merged = dict(PREF_DEFAULTS)
    raw = (user or {}).get("prefs") or "{}"
    try:
        stored = json.loads(raw)
    except (TypeError, ValueError):
        stored = {}
    if isinstance(stored, dict):
        for key, value in stored.items():
            if key in PREF_DEFAULTS:
                merged[key] = bool(value) if isinstance(
                    PREF_DEFAULTS[key], bool) else value
    return merged


def set_prefs(user_id: int, values: Dict[str, Any]) -> Dict[str, Any]:
    merged = prefs_of(get_by_id(user_id))
    for key, value in (values or {}).items():
        if key in PREF_DEFAULTS:
            merged[key] = bool(value) if isinstance(
                PREF_DEFAULTS[key], bool) else value
    db.execute("UPDATE users SET prefs=? WHERE id=?", (_json(merged), user_id))
    return merged


# --------------------------------------------------------------- controls
# Key bindings and aim settings follow the player between machines, so they
# are stored on the account rather than in one browser's localStorage.  The
# rest of the in-game settings (render scale, view distance, volume) stay
# per-device, because they describe the machine rather than the player.
#
# This list mirrors DEFAULT_BINDS in static/js/game/settings.js: it is the
# whitelist a posted set is checked against, so an action that is not a real
# one never reaches the database.
CONTROL_ACTIONS = (
    "forward", "back", "left", "right", "jump", "sprint", "crouch",
    "reload", "interact", "camera", "chat", "teamchat", "scoreboard", "map",
    "slot1", "slot2", "slot3", "slot4", "slot5",
)

# KeyboardEvent.code is always alphanumeric -- KeyW, Digit1, ShiftLeft,
# Space, Tab, ArrowUp, NumpadEnter -- so anything else is not a key.
_KEYCODE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]{0,23}$")

# Ranges are the ones the sliders offer; a hand-rolled POST is clamped to the
# same window rather than trusted.
CONTROL_NUMBERS = {
    "sensitivity": (0.02, 0.6, 0.24),
    "fov": (60.0, 110.0, 82.0),
}
CONTROL_FLAGS = {"invertY": False, "rawMouse": True}


def controls_of(user: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """This account's stored bindings and aim settings.

    Only what the player actually changed is stored, so the client keeps
    ownership of the defaults: an empty ``binds`` here means "use yours".
    """
    raw = (user or {}).get("controls") or "{}"
    try:
        stored = json.loads(raw)
    except (TypeError, ValueError):
        stored = {}
    if not isinstance(stored, dict):
        stored = {}
    out: Dict[str, Any] = {"binds": {}}
    binds = stored.get("binds")
    if isinstance(binds, dict):
        for action, code in binds.items():
            if action not in CONTROL_ACTIONS or not isinstance(code, str):
                continue
            # "" means the player deliberately left this action unbound, and
            # that has to survive the trip or the default comes back.
            if code == "" or _KEYCODE_RE.match(code):
                out["binds"][action] = code
    for key, (low, high, _default) in CONTROL_NUMBERS.items():
        value = stored.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            out[key] = round(min(high, max(low, float(value))), 4)
    for key in CONTROL_FLAGS:
        if key in stored:
            out[key] = bool(stored[key])
    return out


def set_controls(user_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
    """Replace this account's controls with a validated copy of ``data``."""
    clean = controls_of({"controls": _json(data if isinstance(data, dict) else {})})
    db.execute("UPDATE users SET controls=? WHERE id=?", (_json(clean), user_id))
    return clean


def theme_of(user: Optional[Dict[str, Any]]) -> str:
    value = (user or {}).get("theme") or "auto"
    return value if value in THEMES else "auto"


def set_theme(user_id: int, theme: str) -> str:
    theme = (theme or "").lower()
    if theme not in THEMES:
        theme = "auto"
    db.execute("UPDATE users SET theme=? WHERE id=?", (theme, user_id))
    return theme


def privacy_of(user: Optional[Dict[str, Any]]) -> Dict[str, str]:
    """Merged privacy settings; unknown or missing keys fall back to default."""
    settings = dict(PRIVACY_FIELDS)
    raw = (user or {}).get("privacy") or "{}"
    try:
        stored = json.loads(raw)
    except (TypeError, ValueError):
        stored = {}
    if isinstance(stored, dict):
        for key, value in stored.items():
            if key in settings and value in VISIBILITIES:
                settings[key] = value
    return settings


def set_privacy(user_id: int, settings: Dict[str, Any]) -> Dict[str, str]:
    merged = privacy_of(get_by_id(user_id))
    for key, value in (settings or {}).items():
        if key in PRIVACY_FIELDS and value in VISIBILITIES:
            merged[key] = value
    db.execute("UPDATE users SET privacy=? WHERE id=?", (_json(merged), user_id))
    return merged


def can_view(owner: Dict[str, Any], field: str, viewer_id: int,
             viewer_is_admin: bool = False) -> bool:
    """Apply one privacy field for a given viewer."""
    owner_id = int(owner["id"])
    if viewer_id == owner_id or viewer_is_admin:
        return True
    level = privacy_of(owner).get(field, "public")
    if level == "public":
        return True
    if level == "private":
        return False
    if not viewer_id:
        return False
    from ..social import friends as friends_model
    return friends_model.are_friends(owner_id, viewer_id)


def pinned_of(user: Optional[Dict[str, Any]]) -> List[int]:
    raw = (user or {}).get("pinned") or "[]"
    try:
        stored = json.loads(raw)
    except (TypeError, ValueError):
        return []
    if not isinstance(stored, list):
        return []
    out = []
    for value in stored:
        try:
            inv_id = int(value)
        except (TypeError, ValueError):
            continue
        if inv_id > 0 and inv_id not in out:
            out.append(inv_id)
    return out[:MAX_PINNED]


def set_pinned(user_id: int, inv_ids: List[Any]) -> List[int]:
    """Pin up to three owned inventory rows to the top of the profile."""
    from . import inventory
    clean: List[int] = []
    for value in (inv_ids or []):
        try:
            inv_id = int(value)
        except (TypeError, ValueError):
            continue
        if inv_id <= 0 or inv_id in clean:
            continue
        if inventory.get_row(user_id, inv_id) is None:
            continue
        clean.append(inv_id)
        if len(clean) >= MAX_PINNED:
            break
    db.execute("UPDATE users SET pinned=? WHERE id=?", (_json(clean), user_id))
    return clean
