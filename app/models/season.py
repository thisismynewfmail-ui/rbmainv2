"""The seasonal site skin: which holiday dresses the site chrome right now.

The market already knows about events (app/models/crates.py: EVENTS, with a
start and an end each).  This module answers a narrower question for the page
header -- *is a holiday with a site skin running today, and what does its
event chip say?* -- and it answers it from the real calendar on every render:

* by date only.  BLOCKHAVEN_EVENTS=all keeps every event on sale for
  development, but it must not paint the site orange in June, so it is not
  consulted here.  crates.active_events() and event_state() are untouched.
* keyed on ``holiday``, never on the event id, so every year's Halloween
  (halloween_2022 .. halloween) wears the same skin and the store can grow to
  thirty-odd series without this file changing.
* a holiday without an entry in SKINS (Christmas, for now) leaves the site
  exactly as it is.

Environment:
    BLOCKHAVEN_SEASON=off|0|none|no|false   turn the skin off
    BLOCKHAVEN_SEASON=halloween             preview the newest Halloween event
                                            when no skinned event is live
"""
from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional, Tuple

SKINS: Dict[str, Dict[str, str]] = {
    "halloween": {"theme_light": "#ff9f2e", "theme_dark": "#24110a",
                  "critters": "Halloween critters"},
}

# Pages that keep the colours and the chip but run nothing: the world pages
# (their 3D previews), the sign-in forms, the editors and the admin desk.
QUIET_PREFIXES = ("/worlds/", "/login", "/register", "/avatar", "/profile-editor",
                  "/admin", "/messages/")
# The market's event hero has its own moon and bats; the header calms down
# there so the store stays the one animated focal point.
CALM_PATHS = ("/market",)
# Where the event chip leads.  The store hero sells the event crate and key.
EVENT_HREF = "/market"
OFF_WORDS = ("off", "0", "none", "no", "false")

DAY = 86400
HOUR = 3600


def left_labels(left: int, forced: bool = False) -> Tuple[str, str, str]:
    """(long, compact, short) countdown labels for the event chip.

    static/js/ui/season.js mirrors this function exactly, so the chip keeps
    counting in a tab that stays open.
    """
    if forced:
        return ("PREVIEW", "PREVIEW", "PREVIEW")
    left = max(0, int(left))
    if left > 3 * DAY:
        days, hours = left // DAY, (left % DAY) // HOUR
        text = "%dd %dh" % (days, hours)
        return (text, text, "%dd" % days)
    if left > DAY:
        days, hours = left // DAY, (left % DAY) // HOUR
        text = "%dd %dh" % (days, hours)
        return ("LAST 3 DAYS · " + text, text, "%dd" % days)
    hours, minutes = left // HOUR, (left % HOUR) // 60
    text = "%dh %dm" % (hours, minutes)
    return ("ENDS IN " + text, text, ("%dh" % hours) if hours else ("%dm" % minutes))


def _pick(now: int, override: str) -> Tuple[Optional[Dict[str, Any]], bool]:
    from . import crates
    live = [e for e in crates.EVENTS.values()
            if e.get("holiday") in SKINS and e.get("starts") and e.get("ends")
            and e["starts"] <= now < e["ends"]]
    if live:
        # two skinned events overlapping: the one that started last wins
        return max(live, key=lambda e: e["starts"]), False
    if override in SKINS:
        pool = [e for e in crates.EVENTS.values() if e.get("holiday") == override]
        if pool:
            return max(pool, key=lambda e: e["starts"]), True
    return None, False


def current(now: Optional[int] = None, path: str = "") -> Optional[Dict[str, Any]]:
    """The skin for this request, or None.  Never cached: it is a handful of
    comparisons, and a cached answer is how a skin outstays its event."""
    env = os.environ.get("BLOCKHAVEN_SEASON", "").strip().lower()
    if env and env in OFF_WORDS:
        return None
    now = int(now if now is not None else time.time())
    ev, forced = _pick(now, env)
    if ev is None:
        return None
    from . import crates
    series = crates.SERIES.get(ev.get("series", "")) or {}
    pub = crates.public_series(series) if series else {}
    skin = SKINS[ev["holiday"]]
    ends = 0 if forced else int(ev["ends"])
    left = max(0, ends - now) if ends else 0
    long_, compact, short = left_labels(left, forced)
    path = path or ""
    out: Dict[str, Any] = {
        "holiday": ev["holiday"], "event_id": ev["id"], "name": ev["name"],
        "title": ev.get("title") or ev["name"],
        "crate_name": series.get("name") or pub.get("crate_name", ""),
        "key_name": pub.get("key_name", ""),
        "crate_price": pub.get("crate_price", 0), "key_price": pub.get("key_price", 0),
        "href": EVENT_HREF, "starts": int(ev["starts"]), "ends": ends, "now": now,
        "days_left": left // DAY, "left_long": long_, "left_compact": compact,
        "left_short": short, "theme_light": skin["theme_light"],
        "theme_dark": skin["theme_dark"], "critters": skin["critters"],
        "forced": forced, "lite": path.startswith(QUIET_PREFIXES),
        "calm": path in CALM_PATHS,
    }
    out["client"] = {k: out[k] for k in ("holiday", "event_id", "name", "crate_name", "href",
                                         "ends", "now", "forced", "lite", "calm",
                                         "days_left")}
    return out
