"""The parental controls: what they are, their defaults, and their limits.

A child's controls are one JSON object on their ``family_children`` row.
Everything that reads or writes it goes through :func:`clean`, so a
hand-rolled request can only ever store values the dashboard itself offers,
and a key added here later simply takes its default on every existing child.

    weekday_minutes   play per school day (Mon-Fri), None for no limit
    weekend_minutes   play per Saturday / Sunday, None for no limit
    quiet             whether quiet hours apply at all
    quiet_start/_end  "HH:MM" in the family's time zone; may wrap midnight
    worlds_blocked    world ids the child may not join
    chat              in-game chat: "safe" (Safe Chat) or "off"
    messages          private messages: "friends", "off" or "anyone"
    friends           new friends: "approve" (each one needs the parent's
                      OK), "open" or "off"
    wall              profile comments: "friends", "off" or "anyone"
    presence          who sees them online / in a world: "friends", "nobody"
    spending          may spend Noogets in the market
    crates            may buy and open crates (loot boxes)
"""
from __future__ import annotations

import datetime as _dt
import re
from typing import Any, Dict, List, Optional

# What a parent reads about each world, and how intense it is.  New worlds
# fall back to "action" with their own tagline until somebody writes them a
# line here.
INTENSITY = {
    "gentle": {"label": "Gentle", "blurb": "Silly, light-hearted fun"},
    "action": {"label": "Action", "blurb": "Cartoon blasters and team battles"},
    "intense": {"label": "Intense", "blurb": "Spooky or suspenseful themes"},
}

WORLD_GUIDE: Dict[str, Dict[str, str]] = {
    "sky_sprint": {
        "intensity": "gentle", "kind": "Obstacle-course race",
        "note": "Two teams race through floating obstacle courses in the sky. "
                "The only 'weapon' is a bonk glove that bumps rivals off the course."},
    "prop_panic": {
        "intensity": "gentle", "kind": "Hide and seek",
        "note": "Hiders turn into furniture and toys; seekers hunt for the props "
                "that aren't what they seem. Sneaky, silly and full of giggles."},
    "rail_rivals": {
        "intensity": "action", "kind": "Team race",
        "note": "Two railroad companies push ore carts toward the finish, with "
                "brake levers, coal boosts and blocky blasters at the crossing."},
    "plunder_bay": {
        "intensity": "action", "kind": "Pirate treasure hunt",
        "note": "Two pirate crews race to haul gold into their own ship \u2014 "
                "digging up chests, firing cannons and raiding each other."},
    "blackout_relay": {
        "intensity": "action", "kind": "Capture the flag",
        "note": "A team shooter at dusk: grab the other team's flag and bring it "
                "home. Blocky cartoon weapons, respawns every few seconds."},
    "last_light": {
        "intensity": "intense", "kind": "Zombie survival",
        "note": "Players team up against waves of cartoon zombies in dark, "
                "spooky places. Co-operative, but it can be scary for younger kids."},
    "whodunit": {
        "intensity": "intense", "kind": "Murder mystery",
        "note": "Secret roles: one player is secretly the culprit, one is the "
                "detective, everyone else gathers clues. Suspense and mystery themes."},
}

MINUTE_CHOICES = [15, 30, 45, 60, 90, 120, 180, 240]
MAX_MINUTES = 16 * 60

CHOICES = {
    "chat": ["safe", "off"],
    "messages": ["friends", "off", "anyone"],
    "friends": ["approve", "open", "off"],
    "wall": ["friends", "off", "anyone"],
    "presence": ["friends", "nobody"],
}

LABELS = {
    "chat": {"safe": "Safe Chat", "off": "Chat off"},
    "messages": {"friends": "Friends only", "off": "Off", "anyone": "Anyone"},
    "friends": {"approve": "I approve each one", "open": "They choose",
                "off": "No new friends"},
    "wall": {"friends": "Friends only", "off": "Off", "anyone": "Anyone"},
    "presence": {"friends": "Friends only", "nobody": "Nobody"},
}

HELP = {
    "chat": "Safe Chat blocks phone numbers, emails, addresses, links and invites "
            "to other apps \u2014 in both directions \u2014 and blanks out strong language.",
    "messages": "Who can send private messages. Safe Chat checks every one.",
    "friends": "With approval on, new friends wait for your OK on this dashboard.",
    "wall": "Who can leave comments on their profile.",
    "presence": "Who can see when they're online and which world they're in.",
    "spending": "Noogets are play money \u2014 nothing on the site costs real money.",
    "crates": "Crates are random-reward boxes (like loot boxes). You decide.",
}

_HHMM = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)$")


def age_from_year(birth_year: int, now: Optional[_dt.date] = None) -> Optional[int]:
    if not birth_year:
        return None
    today = now or _dt.date.today()
    age = today.year - int(birth_year)
    return age if 0 < age < 25 else None


def defaults(age: Optional[int] = None) -> Dict[str, Any]:
    """Where a new child's rules start, for a child of ``age`` (None:
    unknown).  No daily limits, quiet hours off and they choose their own
    friends -- the parent switches on whatever they want, in the wizard or
    later.  The quiet-hours times are ready for when they do (earlier for
    younger children); Safe Chat, friends-only messages, gentler worlds for
    under 10s and no crates under 13 hold from the start."""
    young = age is not None and age < 10
    teen = age is not None and age >= 13
    intense = [w for w, g in WORLD_GUIDE.items() if g["intensity"] == "intense"]
    return {
        "weekday_minutes": None,
        "weekend_minutes": None,
        "quiet": False,
        "quiet_start": "20:00" if young else ("22:00" if teen else "21:00"),
        "quiet_end": "07:00",
        "worlds_blocked": intense if young else [],
        "chat": "safe",
        "messages": "friends",
        "friends": "open",
        "wall": "friends",
        "presence": "friends",
        "spending": True,
        "crates": teen,
    }


def _minutes(value: Any, fallback: Optional[int]) -> Optional[int]:
    if value is None or value == "" or value == "none" or value == "unlimited":
        return None
    try:
        minutes = int(float(value))
    except (TypeError, ValueError):
        return fallback
    return max(0, min(MAX_MINUTES, minutes))


def _hhmm(value: Any, fallback: str) -> str:
    match = _HHMM.match(str(value or "").strip())
    if not match:
        return fallback
    return "%02d:%02d" % (int(match.group(1)), int(match.group(2)))


def _flag(value: Any, fallback: bool) -> bool:
    if isinstance(value, bool):
        return value
    if value in (1, "1", "true", "on", "yes"):
        return True
    if value in (0, "0", "false", "off", "no"):
        return False
    return fallback


def clean(raw: Any, base: Optional[Dict[str, Any]] = None,
          known_worlds: Optional[List[str]] = None) -> Dict[str, Any]:
    """A complete, valid controls object: ``raw`` laid over ``base`` (the
    current controls, or the defaults), every value checked."""
    current = dict(base or defaults())
    for key, value in defaults().items():
        current.setdefault(key, value)
    data = raw if isinstance(raw, dict) else {}
    out: Dict[str, Any] = {}
    for key in ("weekday_minutes", "weekend_minutes"):
        out[key] = (_minutes(data[key], current[key]) if key in data
                    else _minutes(current[key], None))
    out["quiet"] = _flag(data.get("quiet", current["quiet"]), True)
    out["quiet_start"] = _hhmm(data.get("quiet_start", current["quiet_start"]), "21:00")
    out["quiet_end"] = _hhmm(data.get("quiet_end", current["quiet_end"]), "07:00")
    blocked = data.get("worlds_blocked", current.get("worlds_blocked") or [])
    if not isinstance(blocked, list):
        blocked = []
    known = set(known_worlds) if known_worlds is not None else None
    seen: List[str] = []
    for world_id in blocked:
        world_id = str(world_id)[:40]
        if world_id in seen or not re.match(r"^[a-z0-9_]+$", world_id):
            continue
        if known is not None and world_id not in known:
            continue
        seen.append(world_id)
    out["worlds_blocked"] = seen
    for key, options in CHOICES.items():
        value = str(data.get(key, current.get(key)) or "")
        out[key] = value if value in options else options[0]
    out["spending"] = _flag(data.get("spending", current["spending"]), True)
    out["crates"] = _flag(data.get("crates", current["crates"]), False)
    return out


# ------------------------------------------------------------------- time

def is_weekend(day: _dt.date) -> bool:
    return day.weekday() >= 5


def limit_minutes(controls: Dict[str, Any], day: _dt.date) -> Optional[int]:
    key = "weekend_minutes" if is_weekend(day) else "weekday_minutes"
    return controls.get(key)


def _to_minutes(hhmm: str) -> int:
    hours, minutes = hhmm.split(":")
    return int(hours) * 60 + int(minutes)


def in_quiet_hours(controls: Dict[str, Any], local: _dt.datetime) -> bool:
    if not controls.get("quiet"):
        return False
    start = _to_minutes(controls.get("quiet_start") or "21:00")
    end = _to_minutes(controls.get("quiet_end") or "07:00")
    now = local.hour * 60 + local.minute
    if start == end:
        return False
    if start < end:
        return start <= now < end
    return now >= start or now < end          # wraps midnight


def quiet_ends_label(controls: Dict[str, Any]) -> str:
    return clock_label(controls.get("quiet_end") or "07:00")


def clock_label(hhmm: str) -> str:
    """``21:30`` -> ``9:30 pm``."""
    try:
        hours, minutes = (int(x) for x in hhmm.split(":"))
    except (ValueError, AttributeError):
        return hhmm
    suffix = "am" if hours < 12 else "pm"
    shown = hours % 12 or 12
    return ("%d %s" % (shown, suffix)) if minutes == 0 else ("%d:%02d %s" % (shown, minutes, suffix))


def minutes_label(minutes: Optional[int]) -> str:
    if minutes is None:
        return "No limit"
    if minutes == 0:
        return "No games"
    if minutes < 60:
        return "%d min" % minutes
    hours, rest = divmod(minutes, 60)
    return ("%d hr" % hours) if not rest else ("%d hr %d min" % (hours, rest))


def world_guide(world: Dict[str, Any]) -> Dict[str, Any]:
    guide = dict(WORLD_GUIDE.get(world["id"]) or {})
    guide.setdefault("intensity", "action")
    guide.setdefault("kind", world.get("genre", "Game"))
    guide.setdefault("note", world.get("tagline", ""))
    level = INTENSITY.get(guide["intensity"], INTENSITY["action"])
    guide["intensity_label"] = level["label"]
    guide["intensity_blurb"] = level["blurb"]
    return guide
