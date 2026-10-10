"""Badges: medals earned by playing, shown on profiles and worn on the chest.

A badge watches one *stat* -- flags captured, players revived, the best wave
cleared -- and has a ladder of thresholds.  Crossing the first one awards it;
every later one levels it up, and each level is a step up in metal and in
ornament (see :func:`model`): Bronze, Silver, Gold, Platinum, Diamond and
Mythic, the way a Strange counter climbs its ranks.

The flow is deliberately one-way and boring:

1. The game (or the market) calls :func:`record` with a stat and an amount.
   Game hosts do it through the heartbeat (``report_badge`` in
   ``app/game/host.py``), so a burst of kills is a single row update.
2. :func:`record` stores the stat, works out every badge watching it, and
   for each one whose level went up writes the award and leaves the player a
   notification.  It returns those level-ups, which the heartbeat hands back
   to the host so the player sees a toast in game as well.

Adding a badge is one entry in ``BADGES`` plus, if it watches a new stat, a
``record`` call where that thing happens.  ``howto_readmes/
badge_creation_and_implimentation_and_ceration.txt`` walks through it.
"""
from __future__ import annotations

import json
import math
import time
from typing import Any, Dict, Iterable, List, Optional

from .. import db
from .modeling import part, place

MAX_SHOWN = 4          # badges on show on a profile

# ----------------------------------------------------------------- the tiers
# One per level.  ``body`` is the plate, ``trim`` the rim and laurels, and
# ``gem`` what is set into it from Platinum up.
TIERS: List[Dict[str, str]] = [
    {"id": "bronze", "label": "Bronze", "body": "#b8743a", "trim": "#8a5226",
     "gem": "#ffb070", "glow": "#ffb070"},
    {"id": "silver", "label": "Silver", "body": "#c9d2da", "trim": "#97a3ae",
     "gem": "#e8f4ff", "glow": "#e8f4ff"},
    {"id": "gold", "label": "Gold", "body": "#f0bd45", "trim": "#c8901c",
     "gem": "#ff5a5a", "glow": "#ffe08a"},
    {"id": "platinum", "label": "Platinum", "body": "#f1eef8", "trim": "#a99bd6",
     "gem": "#56d8ff", "glow": "#d9ccff"},
    {"id": "diamond", "label": "Diamond", "body": "#8fe6ff", "trim": "#f4fdff",
     "gem": "#7fe3ff", "glow": "#7fe3ff"},
    {"id": "mythic", "label": "Mythic", "body": "#2c1440", "trim": "#ffcf4a",
     "gem": "#ff4fd8", "glow": "#ff4fd8"},
]

# --------------------------------------------------------------- the families
# What a badge is built on.  Blackout Relay's are struck on a cog (it is an
# industrial relay station), Last Light's on a heater shield, the market's on
# a star and an event's on a moon.
FAMILIES: Dict[str, Dict[str, str]] = {
    "cog": {"face": "#173a66", "ribbon": "#2d7ff9", "wing": "#9fb4c8",
            "wing_mesh": "wing"},
    "shield": {"face": "#3a140c", "ribbon": "#d0571a", "wing": "#f4efe6",
               "wing_mesh": "wing"},
    "star": {"face": "#2b1450", "ribbon": "#8b3fd6", "wing": "#e9ddff",
             "wing_mesh": "wing"},
    "moon": {"face": "#1a0d26", "ribbon": "#ff8c1a", "wing": "#2a1838",
             "wing_mesh": "bat"},
    # the other holidays (app/models/holidays/): New Year is struck on a clock
    # face, St. Patrick's on a shamrock, Easter on an egg, the Fourth on a
    # star, Christmas on a snowflake
    "clock": {"face": "#0b1433", "ribbon": "#f2c230", "wing": "#fff3b0",
              "wing_mesh": "wing"},
    "clover": {"face": "#0e3a1c", "ribbon": "#2fa84f", "wing": "#d8f5c8",
               "wing_mesh": "wing"},
    "egg": {"face": "#3a2a5a", "ribbon": "#ff9ad8", "wing": "#fff3d8",
            "wing_mesh": "wing"},
    "spangle": {"face": "#0d2a6b", "ribbon": "#c4281c", "wing": "#f2f3f3",
                "wing_mesh": "wing"},
    "flake": {"face": "#0b2a46", "ribbon": "#c4281c", "wing": "#e8f8ff",
              "wing_mesh": "wing"},
}

GAMES = {
    "blackout_relay": "Blackout Relay",
    "last_light": "Last Light",
    "market": "Crates & Market",
    "event": "Events",
}


def _badge(badge_id: str, name: str, game: str, stat: str, thresholds: List[int],
           ranks: List[str], desc: str, emblem: str, family: str, unit: str,
           mode: str = "add", event: str = "") -> Dict[str, Any]:
    assert len(ranks) == len(thresholds), badge_id
    assert thresholds == sorted(thresholds), badge_id
    return {"id": badge_id, "name": name, "game": game, "stat": stat,
            "thresholds": thresholds, "ranks": ranks, "description": desc,
            "emblem": emblem, "family": family, "unit": unit, "mode": mode,
            "event": event}


BADGES_LIST: List[Dict[str, Any]] = [
    # ------------------------------------------------------- Blackout Relay
    _badge("br_flag_runner", "Flag Runner", "blackout_relay", "br_captures",
           [1, 10, 30, 75, 150, 300],
           ["Courier", "Runner", "Breakaway", "Flag Bearer", "Relay Legend",
            "Blackout Phantom"],
           "Counts every enemy flag you carry home in Blackout Relay, and levels "
           "up as the tally climbs.", "em_flag", "cog", "flags captured"),
    _badge("br_homeguard", "Homeguard", "blackout_relay", "br_returns",
           [1, 10, 40, 100, 250, 500],
           ["Picket", "Sentry", "Warden", "Keeper", "Bastion", "Iron Gate"],
           "Earned by touching your team's dropped flag to send it straight home.",
           "em_return", "cog", "flags returned"),
    _badge("br_interceptor", "Interceptor", "blackout_relay", "br_carrier_kills",
           [1, 10, 30, 80, 200, 400],
           ["Spoiler", "Tackler", "Interceptor", "Runner's Bane", "The Wall",
            "Lights Out"],
           "Awarded for stopping enemy flag carriers before they can score.",
           "em_crosshair", "cog", "carriers stopped"),
    _badge("br_frontline", "Relay Frontline", "blackout_relay", "br_kills",
           [25, 150, 500, 1500, 4000, 10000],
           ["Recruit", "Trooper", "Veteran", "Shock Trooper", "Warlord", "Live Wire"],
           "Tracks every opponent you knock out on Ironvale Relay.",
           "em_bolt", "cog", "knockouts"),
    _badge("br_champion", "Relay Champion", "blackout_relay", "br_wins",
           [1, 5, 15, 40, 100, 250],
           ["Contender", "Victor", "Champion", "Conqueror", "Dynasty", "Undisputed"],
           "Won rounds of Blackout Relay with your team.",
           "em_trophy", "cog", "rounds won"),
    _badge("br_bulwark", "Bulwark", "blackout_relay", "br_defends",
           [10, 50, 150, 400, 1000, 2500],
           ["Guard", "Defender", "Rampart", "Fortress", "Citadel", "Unbreakable"],
           "Knocked out attackers who came too close to your own flag.",
           "em_tower", "cog", "defensive knockouts"),
    _badge("br_clutch", "Overtime Clutch", "blackout_relay", "br_clutch",
           [1, 5, 15, 40, 80, 150],
           ["Buzzer Beater", "Clutch", "Ice Cold", "Closer", "Overtime King",
            "Stopped Clock"],
           "Captured a flag while the round was already in overtime.",
           "em_clock", "cog", "overtime captures"),
    _badge("br_sudden_death", "Sudden Death", "blackout_relay", "br_sudden",
           [1, 3, 10],
           ["Decider", "Executioner", "Final Word"],
           "Scored the capture that settled a round in sudden death.",
           "em_hourglass", "cog", "deciding captures"),

    # ----------------------------------------------------------- Last Light
    _badge("ll_holdout", "Last Light Holdout", "last_light", "ll_best_wave",
           [5, 10, 15, 20, 30, 40],
           ["Survivor", "Holdout", "Night Owl", "Dawn Watcher", "Lighthouse",
            "The Last Light"],
           "Shows the highest wave you have cleared in Last Light; survive later "
           "waves to level it.", "em_sunrise", "shield", "best wave", mode="max"),
    _badge("ll_medic", "Field Medic", "last_light", "ll_revives",
           [1, 10, 40, 100, 250, 600],
           ["First Aider", "Medic", "Combat Medic", "Lifeline", "Guardian Angel",
            "Miracle Worker"],
           "Earned by picking downed teammates back up in Last Light.",
           "em_cross", "shield", "revives"),
    _badge("ll_slayer", "Infected Slayer", "last_light", "ll_kills",
           [100, 500, 2000, 6000, 15000, 40000],
           ["Exterminator", "Cleaner", "Reaper", "Purger", "Horde Breaker",
            "Extinction"],
           "Counts every infected you put down in Last Light.",
           "em_hand", "shield", "infected"),
    _badge("ll_hunter", "Special Hunter", "last_light", "ll_specials",
           [5, 30, 100, 300, 800, 2000],
           ["Tracker", "Hunter", "Stalker", "Predator", "Apex", "Nightmare's End"],
           "Took down special infected: Bloaters, Spitters, Bombers and worse.",
           "em_skull", "shield", "specials"),
    _badge("ll_tank_buster", "Tank Buster", "last_light", "ll_tanks",
           [1, 5, 15, 40, 100, 200],
           ["Giant Slayer", "Tank Buster", "Wrecker", "Demolisher", "Titanfall",
            "Colossus Bane"],
           "Helped bring down Tanks with the last blow or a big share of the damage.",
           "em_fist", "shield", "tanks"),
    _badge("ll_bomb_squad", "Bomb Squad", "last_light", "ll_defuses",
           [1, 10, 30, 75, 150, 300],
           ["Defuser", "Technician", "Bomb Squad", "Steady Hand", "Fuse Cutter",
            "Zero Blast"],
           "Defused Bombers with a clean headshot before they could go off.",
           "em_bomb", "shield", "bombers defused"),
    _badge("ll_sharpshooter", "Sharpshooter", "last_light", "ll_headshots",
           [25, 200, 750, 2000, 6000, 15000],
           ["Marksman", "Sharpshooter", "Deadeye", "Sniper", "Hawkeye",
            "One Shot"],
           "Counts headshot kills on the infected.",
           "em_scope", "shield", "headshots"),
    _badge("ll_wavebreaker", "Wave Breaker", "last_light", "ll_waves",
           [5, 25, 100, 300, 750, 1500],
           ["Breakwater", "Seawall", "Wave Breaker", "Tidebreaker", "Stormwall",
            "Unsinkable"],
           "Counts every wave you have been standing at the end of.",
           "em_waves", "shield", "waves survived"),
    _badge("ll_untouchable", "Untouchable", "last_light", "ll_untouched",
           [1, 5, 15, 40, 100, 200],
           ["Unscathed", "Slippery", "Untouchable", "Ghost", "Phantom",
            "Immaculate"],
           "Cleared wave 10 or later without going down once.",
           "em_shield", "shield", "flawless waves"),
    _badge("ll_grand_tour", "Grand Tour", "last_light", "ll_areas",
           [1, 2, 3, 4],
           ["Day Tripper", "Wanderer", "Road Warrior", "Grand Tourist"],
           "Cleared wave 5 in each of Last Light's four areas.",
           "em_compass", "shield", "areas"),

    # ------------------------------------------------------ crates and events
    _badge("mk_unboxer", "Unboxer", "market", "crates_opened",
           [1, 10, 30, 75, 150, 300],
           ["Curious", "Unboxer", "Collector", "Hoarder", "Vault Raider",
            "Crate Lord"],
           "Counts every crate you have unlocked with a key.",
           "em_crate", "star", "crates opened"),
    _badge("mk_lucky_star", "Lucky Star", "market", "unusuals_unboxed",
           [1, 2, 4, 7, 12, 20],
           ["Lucky", "Charmed", "Blessed", "Fortune's Pet", "Jackpot",
            "Born Unusual"],
           "Unboxed an Unusual from a crate, the rarest pull there is.",
           "em_sparkle", "star", "Unusuals unboxed"),
    _badge("ev_harvest_2026", "Hallowed Harvest 2026", "event", "ev_harvest_2026",
           [1, 5, 15, 30, 60, 100],
           ["Trick-or-Treater", "Harvester", "Grave Robber", "Hexed",
            "Pumpkin King", "Lord of Hallows"],
           "Opened Hallowed Harvest crates during the 2026 event, and only then.",
           "em_pumpkin", "moon", "harvest crates", event="halloween"),
]

# One badge for every other event (app/models/holidays/): earned by opening
# its crates while it runs, and only then.
def _event_badges() -> List[Dict[str, Any]]:
    from . import holidays
    out = []
    for ev in holidays.EVENTS:
        if not ev.badge:
            continue
        b = ev.badge
        out.append(_badge(b["id"], b["name"], "event", b["id"], [1, 5, 15, 30, 60, 100],
                          b["ranks"], b["description"], b["emblem"], b["family"],
                          "%s crates" % ev.name, event=ev.id))
    return out


BADGES_LIST.extend(_event_badges())
BADGES: Dict[str, Dict[str, Any]] = {b["id"]: b for b in BADGES_LIST}
BY_STAT: Dict[str, List[Dict[str, Any]]] = {}
for _b in BADGES_LIST:
    BY_STAT.setdefault(_b["stat"], []).append(_b)

# Stats that are not counted directly but worked out from others: the Grand
# Tour is the number of areas with an ``ll_area_<id>`` mark.
DERIVED = {"ll_areas": "ll_area_"}


# ------------------------------------------------------------------ levels
def level_for(badge: Dict[str, Any], value: int) -> int:
    return sum(1 for t in badge["thresholds"] if value >= t)


def tier_of(level: int) -> Dict[str, str]:
    return TIERS[max(0, min(len(TIERS), level) - 1)]


def _now() -> int:
    return int(time.time())


# ------------------------------------------------------------------ record
def record(user_id: int, stat: str, amount: int = 1, mode: str = "add",
           notify: bool = True) -> List[Dict[str, Any]]:
    """Add to (or raise) one of a player's stats; return any level-ups."""
    return record_many(user_id, [(stat, amount, mode)], notify)


def record_many(user_id: int, changes: Iterable[Any],
                notify: bool = True) -> List[Dict[str, Any]]:
    """Several stats at once, in one transaction.

    ``changes`` is ``(stat, amount, mode)`` triples; ``mode`` is ``add`` for
    a running count and ``max`` for a best-ever.  Returns one event per badge
    that was awarded or levelled up, in the order they happened."""
    uid = int(user_id)
    if uid <= 0:
        return []
    now = _now()
    touched: Dict[str, int] = {}
    events: List[Dict[str, Any]] = []
    with db.transaction() as conn:
        if conn.execute("SELECT 1 FROM users WHERE id=?", (uid,)).fetchone() is None:
            return []
        for change in changes:
            stat, amount, mode = (list(change) + [1, "add"])[:3]
            stat = str(stat)[:48]
            try:
                amount = int(amount)
            except (TypeError, ValueError):
                continue
            if amount <= 0 and mode != "max":
                continue
            row = conn.execute("SELECT value FROM badge_stats WHERE user_id=? AND stat=?",
                               (uid, stat)).fetchone()
            old = int(row["value"]) if row else 0
            new = max(old, amount) if mode == "max" else old + amount
            if new == old and row is not None:
                continue
            conn.execute(
                "INSERT INTO badge_stats(user_id,stat,value,updated_at) VALUES(?,?,?,?)"
                " ON CONFLICT(user_id,stat) DO UPDATE SET value=excluded.value,"
                " updated_at=excluded.updated_at", (uid, stat, new, now))
            touched[stat] = new
            for derived, prefix in DERIVED.items():
                if stat.startswith(prefix):
                    # an exact prefix, not LIKE: "_" is a wildcard there, and
                    # "ll_area_%" would count "ll_areas" itself
                    count = int(conn.execute(
                        "SELECT COUNT(*) AS n FROM badge_stats WHERE user_id=?"
                        " AND substr(stat, 1, ?)=? AND value > 0",
                        (uid, len(prefix), prefix)).fetchone()["n"])
                    conn.execute(
                        "INSERT INTO badge_stats(user_id,stat,value,updated_at) VALUES(?,?,?,?)"
                        " ON CONFLICT(user_id,stat) DO UPDATE SET value=excluded.value,"
                        " updated_at=excluded.updated_at", (uid, derived, count, now))
                    touched[derived] = count
        for stat, value in touched.items():
            for badge in BY_STAT.get(stat, []):
                level = level_for(badge, value)
                if level <= 0:
                    continue
                held = conn.execute(
                    "SELECT level FROM badge_awards WHERE user_id=? AND badge_id=?",
                    (uid, badge["id"])).fetchone()
                before = int(held["level"]) if held else 0
                if level <= before:
                    continue
                if held is None:
                    conn.execute(
                        "INSERT INTO badge_awards(user_id,badge_id,level,awarded_at,"
                        "levelled_at) VALUES(?,?,?,?,?)",
                        (uid, badge["id"], level, now, now))
                else:
                    conn.execute(
                        "UPDATE badge_awards SET level=?, levelled_at=? WHERE user_id=?"
                        " AND badge_id=?", (level, now, uid, badge["id"]))
                events.append(_event(badge, level, before, value, uid))
        is_bot = conn.execute("SELECT is_bot FROM users WHERE id=?", (uid,)).fetchone()
    if events and notify and not (is_bot and int(is_bot["is_bot"] or 0)):
        from . import notifications
        for event in events:
            notifications.push(uid, "badge", event["title"], event["body"],
                               {"badge": event["id"], "level": event["level"],
                                "tier": event["tier"], "first": event["first"],
                                "emblem": event["emblem"], "family": event["family"]})
    return events


def _event(badge: Dict[str, Any], level: int, before: int, value: int,
           uid: int) -> Dict[str, Any]:
    tier = tier_of(level)
    rank = badge["ranks"][level - 1]
    first = before == 0
    if first:
        title = "Badge earned: %s!" % badge["name"]
        body = "%s \u2022 %s. Wear it from Edit Avatar or show it off on your profile." % (
            tier["label"], rank)
    else:
        title = "%s levelled up to %s!" % (badge["name"], tier["label"])
        body = "Rank %d: %s (%s %s)." % (level, rank, f"{value:,}", badge["unit"])
    return {"uid": uid, "id": badge["id"], "name": badge["name"], "level": level,
            "tier": tier["id"], "tier_label": tier["label"], "color": tier["body"],
            "glow": tier["glow"], "rank": rank, "emblem": badge["emblem"],
            "family": badge["family"], "first": first, "value": value,
            "title": title, "body": body}


# ------------------------------------------------------------------- reads
def stats_of(user_id: int) -> Dict[str, int]:
    return {row["stat"]: int(row["value"]) for row in db.query(
        "SELECT stat, value FROM badge_stats WHERE user_id=?", (int(user_id),))}


def earned(user_id: int) -> Dict[str, Dict[str, int]]:
    """badge id -> {level, awarded_at, levelled_at} for every badge held."""
    return {row["badge_id"]: {"level": int(row["level"]),
                              "awarded_at": int(row["awarded_at"]),
                              "levelled_at": int(row["levelled_at"])}
            for row in db.query("SELECT * FROM badge_awards WHERE user_id=?",
                                (int(user_id),))
            if row["badge_id"] in BADGES}


def card(badge_id: str, level: int, value: int = 0,
         awarded_at: int = 0, with_model: bool = True) -> Dict[str, Any]:
    """Everything a page needs to draw one badge at one level."""
    badge = BADGES[badge_id]
    shown = max(1, level)
    tier = tier_of(shown)
    levels = len(badge["thresholds"])
    nxt = badge["thresholds"][level] if level < levels else None
    floor = badge["thresholds"][level - 1] if level > 0 else 0
    if nxt is None:
        pct = 100
    else:
        pct = int(max(0, min(100, (value - floor) * 100.0 / max(1, nxt - floor))))
    out = {
        "id": badge_id, "name": badge["name"], "description": badge["description"],
        "game": badge["game"], "game_name": GAMES.get(badge["game"], ""),
        "level": level, "levels": levels, "earned": level > 0,
        "tier": tier["id"], "tier_label": tier["label"], "color": tier["body"],
        "trim": tier["trim"], "glow": tier["glow"],
        "rank": badge["ranks"][shown - 1], "emblem": badge["emblem"],
        "family": badge["family"], "value": value, "unit": badge["unit"],
        "next": nxt, "pct": pct, "awarded_at": awarded_at,
        "thresholds": badge["thresholds"], "ranks": badge["ranks"],
        "event": badge["event"],
    }
    if with_model:
        out["parts"] = model(badge_id, shown)
    return out


def collection(user_id: int, with_models: bool = True) -> List[Dict[str, Any]]:
    """Every badge, held or not, with progress -- the Badge Inventory."""
    held = earned(user_id)
    stats = stats_of(user_id)
    out = []
    for badge in BADGES_LIST:
        got = held.get(badge["id"])
        level = got["level"] if got else 0
        if not got and badge["event"]:
            # an event badge you never earned is not a goal any more once the
            # event is over; while it runs it is the best advert there is
            from . import crates
            if not crates.event_active(badge["event"]):
                continue
        out.append(card(badge["id"], level, stats.get(badge["stat"], 0),
                        got["awarded_at"] if got else 0, with_models))
    out.sort(key=lambda c: (not c["earned"], -c["level"], -c["awarded_at"]))
    return out


def shown_of(user: Any) -> List[str]:
    """The (up to four) badges a player has chosen to show, still held."""
    try:
        raw = json.loads(user["badges_shown"] or "[]")
    except (KeyError, IndexError, TypeError, ValueError):
        raw = []
    held = earned(int(user["id"]))
    out: List[str] = []
    for badge_id in raw if isinstance(raw, list) else []:
        if isinstance(badge_id, str) and badge_id in held and badge_id not in out:
            out.append(badge_id)
    return out[:MAX_SHOWN]


def showcase(user: Any) -> List[Dict[str, Any]]:
    """The profile's badge row: the chosen four, or the best four if none
    have been chosen yet, so a new badge shows up without any setup."""
    held = earned(int(user["id"]))
    stats = stats_of(int(user["id"]))
    chosen = shown_of(user)
    if not chosen:
        best = sorted(held.items(), key=lambda kv: (-kv[1]["level"], -kv[1]["levelled_at"]))
        chosen = [badge_id for badge_id, _ in best[:MAX_SHOWN]]
    return [card(b, held[b]["level"], stats.get(BADGES[b]["stat"], 0),
                 held[b]["awarded_at"]) for b in chosen if b in held]


def set_shown(user_id: int, badge_ids: Iterable[Any]) -> List[str]:
    held = earned(user_id)
    out: List[str] = []
    for badge_id in badge_ids:
        badge_id = str(badge_id or "")
        if badge_id in held and badge_id not in out:
            out.append(badge_id)
    out = out[:MAX_SHOWN]
    db.execute("UPDATE users SET badges_shown=? WHERE id=?",
               (json.dumps(out), int(user_id)))
    return out


def worn_of(user_id: int) -> str:
    row = db.query_one("SELECT badge FROM avatars WHERE user_id=?", (int(user_id),))
    badge_id = (row["badge"] if row else "") or ""
    return badge_id if badge_id in BADGES else ""


def set_worn(user_id: int, badge_id: str) -> str:
    badge_id = str(badge_id or "")
    if badge_id and badge_id not in earned(user_id):
        raise ValueError("You have not earned that badge yet.")
    from . import avatars
    avatars.raw_avatar(int(user_id))       # make sure the row exists
    db.execute("UPDATE avatars SET badge=?, updated_at=? WHERE user_id=?",
               (badge_id, _now(), int(user_id)))
    return badge_id


def worn_payload(user_id: int) -> Optional[Dict[str, Any]]:
    """What an avatar descriptor carries for the badge on its chest."""
    badge_id = worn_of(user_id)
    if not badge_id:
        return None
    held = earned(user_id).get(badge_id)
    if not held:
        return None
    level = held["level"]
    tier = tier_of(level)
    return {"id": badge_id, "name": BADGES[badge_id]["name"], "level": level,
            "tier": tier["id"], "tier_label": tier["label"],
            "rank": BADGES[badge_id]["ranks"][level - 1],
            "parts": model(badge_id, level)}


def holders(badge_id: str) -> int:
    return int(db.scalar("SELECT COUNT(*) FROM badge_awards WHERE badge_id=?",
                         (badge_id,), 0))


# ------------------------------------------------------------------ models
_MODELS: Dict[Any, List[Dict[str, Any]]] = {}
HALF_PI = math.pi / 2


def model(badge_id: str, level: int) -> List[Dict[str, Any]]:
    """The 3D badge, about one unit tall, centred on the origin, facing +Z.

    Every level keeps everything the one below had and adds to it, so the
    ladder reads at a glance from across a room:

    1 Bronze    the plate, its enamel face and the emblem
    2 Silver    a raised rim, riveted
    3 Gold      a laurel wreath round the bottom
    4 Platinum  ribbon tails, and a gem set at the top
    5 Diamond   wings, and gems round the rim
    6 Mythic    an obsidian plate, a crown, and a ring of glowing beads
    """
    key = (badge_id, int(level))
    if key not in _MODELS:
        _MODELS[key] = _build(BADGES[badge_id], max(1, min(len(TIERS), int(level))))
    return [dict(p) for p in _MODELS[key]]


def _build(badge: Dict[str, Any], level: int) -> List[Dict[str, Any]]:
    tier = tier_of(level)
    fam = FAMILIES[badge["family"]]
    body, trim, gem = tier["body"], tier["trim"], tier["gem"]
    mythic = level >= 6
    face = "#120a1c" if mythic else fam["face"]
    parts: List[Dict[str, Any]] = []
    family = badge["family"]

    # --- the plate
    if family == "cog":
        parts.append(place("cog", [0, 0, 0], [1.06, 1.06, 0.9], body, m="metal"))
        face_r = 0.37
        parts.append(place("disc", [0, 0, 0.045], [face_r * 2, face_r * 2, 0.5], face))
    elif family == "shield":
        parts.append(place("shield", [0, 0, 0], [1.02, 1.04, 0.9], body, m="metal"))
        parts.append(place("shield", [0, 0.01, 0.045], [0.80, 0.80, 0.5], face))
        face_r = 0.36
    elif family == "star":
        parts.append(place("star", [0, -0.03, 0], [1.22, 1.22, 0.9], body, m="metal"))
        face_r = 0.30
        parts.append(place("disc", [0, 0, 0.045], [face_r * 2, face_r * 2, 0.5], face))
    elif family == "clock":
        parts.append(place("disc", [0, 0, 0], [1.04, 1.04, 0.85], body, m="metal"))
        face_r = 0.38
        parts.append(place("disc", [0, 0, 0.045], [face_r * 2, face_r * 2, 0.5], face))
        # twelve hour marks round the rim
        for k in range(12):
            a = k * math.tau / 12
            parts.append(part("box", [math.sin(a) * 0.46, math.cos(a) * 0.46, 0.07],
                              [0.03, 0.08, 0.03], trim, r=[0, 0, -a], m="metal"))
        parts.append(part("cyl", [0, 0.58, 0], [0.10, 0.10, 0.10], body, m="metal"))
    elif family == "clover":
        parts.append(place("shamrock", [0, 0.02, 0], [1.16, 1.16, 0.9], body, m="metal"))
        face_r = 0.30
        parts.append(place("disc", [0, 0.06, 0.045], [face_r * 2, face_r * 2, 0.5], face))
    elif family == "egg":
        parts.append(place("egg", [0, -0.62, 0], [0.92, 0.95, 0.42], body, anchor=[0, 0, 0],
                           m="metal"))
        face_r = 0.32
        parts.append(place("disc", [0, -0.02, 0.18], [face_r * 2, face_r * 2.1, 0.5], face))
    elif family == "spangle":
        parts.append(place("star", [0, -0.03, 0], [1.22, 1.22, 0.9], body, m="metal"))
        face_r = 0.30
        parts.append(place("disc", [0, 0, 0.045], [face_r * 2, face_r * 2, 0.5], face))
        for k, c in enumerate(("#c4281c", "#f2f3f3", "#c4281c")):
            parts.append(part("box", [0, 0.20 - k * 0.07, 0.10], [0.62, 0.05, 0.02], c))
    elif family == "flake":
        parts.append(place("snowflake", [0, 0, 0], [1.20, 1.20, 1.4], body, m="metal"))
        face_r = 0.30
        parts.append(place("disc", [0, 0, 0.045], [face_r * 2, face_r * 2, 0.5], face))
    else:  # moon
        parts.append(place("disc", [0, 0, 0], [1.0, 1.0, 0.85], body, m="metal"))
        face_r = 0.39
        parts.append(place("disc", [0, 0, 0.045], [face_r * 2, face_r * 2, 0.5], face))
        # a crescent over the shoulder of the moon, in the trim colour
        parts.append(place("crescent", [0.30, 0.20, 0.07], [0.30, 0.30, 0.4], trim,
                           r=[0, 0, 0.5], m="metal"))

    # --- the emblem, printed on the face
    size = face_r * 1.62
    parts.append(part("box", [0, 0, 0.098], [size, size, 0.01], "#ffffff",
                      a=-1, decal=badge["emblem"]))

    # --- 2 Silver: a raised rim, riveted
    if level >= 2:
        rim = face_r * 2 + 0.10
        parts.append(part("torus", [0, 0, 0.05], [rim, rim, rim], trim,
                          r=[HALF_PI, 0, 0], m="metal"))
        count = 8
        for k in range(count):
            a = (k + 0.5) * math.tau / count
            rr = rim * 0.4
            parts.append(part("sph", [math.sin(a) * rr, math.cos(a) * rr, 0.12],
                              [0.055, 0.055, 0.04], body, m="metal"))

    # --- 3 Gold: laurels round the bottom
    if level >= 3:
        laurel = "#ffcf4a" if mythic else trim
        for side in (1, -1):
            for k in range(6):
                phi = 0.42 + k * 0.30
                rad = 0.60 + (0.03 if k % 2 else -0.02)
                x = math.sin(phi) * rad * side
                y = -math.cos(phi) * rad + 0.02
                rz = (phi - HALF_PI) * side + (0.22 if k % 2 else -0.08) * side
                parts.append(part("leaf", [x, y, 0.0], [0.09, 0.26, 0.05], laurel,
                                  r=[0, 0, rz], m="metal"))
            # the stem ties the two branches at the bottom
        parts.append(part("sph", [0, -0.58, 0.02], [0.10, 0.08, 0.08], laurel, m="metal"))

    # --- 4 Platinum: ribbon tails and a gem at the top
    if level >= 4:
        ribbon = "#ff4fd8" if mythic else fam["ribbon"]
        for side in (1, -1):
            parts.append(part("ribbon", [0.15 * side, -0.70, -0.04], [0.22, 0.44, 0.05],
                              ribbon, r=[0, 0, 0.26 * side]))
        parts.append(place("gem", [0, 0.50, 0.08], [0.16, 0.16, 0.16], gem,
                           r=[HALF_PI, 0, 0], m="glass"))
        parts.append(part("torus", [0, 0.50, 0.06], [0.20, 0.20, 0.20], trim,
                          r=[HALF_PI, 0, 0], m="metal"))

    # --- 5 Diamond: wings and gems round the rim
    if level >= 5:
        mesh = fam["wing_mesh"]
        wing_c = "#ff4fd8" if mythic and mesh == "bat" else fam["wing"]
        if mythic and mesh == "wing":
            wing_c = "#ffe6a0"
        for side in (1, -1):
            if mesh == "wing":
                parts.append(place("wing", [0.40 * side, 0.08, -0.06], 0.66, wing_c,
                                   anchor=[-0.5, 0.0, 0],
                                   r=[0, 0 if side > 0 else math.pi, 0.18]))
                parts.append(place("wing", [0.40 * side, -0.02, -0.09], 0.50, trim,
                                   anchor=[-0.5, 0.0, 0],
                                   r=[0, 0 if side > 0 else math.pi, -0.06], m="metal"))
            else:
                parts.append(place("bat", [0.58 * side, 0.12, -0.06], [0.70, 0.70, 0.8],
                                   wing_c, r=[0, 0, 0.12 * side]))
        for k in range(4):
            a = math.pi / 4 + k * math.pi / 2
            rr = (face_r * 2 + 0.10) * 0.4
            parts.append(place("gem", [math.sin(a) * rr, math.cos(a) * rr, 0.13],
                               [0.09, 0.09, 0.09], gem, r=[HALF_PI, 0, 0], m="glass"))

    # --- 6 Mythic: a crown and a ring of glowing beads
    if mythic:
        top = 0.62 if family != "star" else 0.64
        parts.append(part("rbox", [0, top, 0.0], [0.44, 0.09, 0.10], trim, m="metal"))
        for k, x in enumerate((-0.18, -0.09, 0.0, 0.09, 0.18)):
            tall = 0.20 if k == 2 else (0.15 if k in (1, 3) else 0.12)
            parts.append(part("cone", [x, top + 0.045 + tall / 2, 0.0],
                              [0.07, tall, 0.07], trim, m="metal"))
            parts.append(part("sph", [x, top + 0.05 + tall, 0.0], [0.045, 0.045, 0.045],
                              gem, m="neon"))
        for k in range(18):
            a = k * math.tau / 18
            parts.append(part("sph", [math.sin(a) * 0.74, math.cos(a) * 0.74, -0.10],
                              [0.06, 0.06, 0.06], gem, m="neon"))
    return parts


# --------------------------------------------------------------- pretty JSON
def public_catalogue() -> List[Dict[str, Any]]:
    """Every badge's definition, for the help page and the docs."""
    return [{"id": b["id"], "name": b["name"], "game": b["game"],
             "game_name": GAMES.get(b["game"], ""), "description": b["description"],
             "thresholds": b["thresholds"], "ranks": b["ranks"], "unit": b["unit"],
             "emblem": b["emblem"], "family": b["family"], "event": b["event"]}
            for b in BADGES_LIST]
