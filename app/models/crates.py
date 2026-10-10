"""Crates, keys and the series they belong to.

Hats no longer come off the market shelf: they come out of crates.  A crate
and the key that opens it are ordinary items -- owned copies with serials, a
price and a model (app/models/cosmetics.py) -- and a *series* ties them
together: which key opens which crate, what is inside, how likely each grade
is, which Unusual effects can come out of it, and when it is on sale.

Adding a crate later is one entry in SERIES plus the crate and key items in
the catalogue -- see reference_images_to_start_with/CRATES_AND_KEYS.md.

Everything that decides an outcome happens here, on the server, inside one
write transaction: the client sends two inventory row ids and gets back what
came out, plus the strip of tiles the opening animation spins through.  The
strip is decoration -- generated after the result is fixed and built around
it -- so nothing the browser does can change what you got.
"""
from __future__ import annotations

import calendar
import os
import random
import time
from typing import Any, Dict, List, Optional

from .. import db
from . import catalog, holidays, inventory, notifications


class CrateError(Exception):
    pass


def _date(text: str) -> int:
    return calendar.timegm(time.strptime(text, "%Y-%m-%d"))


# ---------------------------------------------------------------- grades
# How rare a drop is.  Every crate item is graded by its catalogue rarity;
# the series says how likely each grade is.  Colours are what the reel, the
# contents list and the reveal paint each grade in.
GRADES: Dict[str, Dict[str, Any]] = {
    "common": {"id": "common", "label": "Common", "color": "#9fb0c2", "rank": 0},
    "uncommon": {"id": "uncommon", "label": "Uncommon", "color": "#4fc46e", "rank": 1},
    "rare": {"id": "rare", "label": "Rare", "color": "#3d8bfd", "rank": 2},
    "legendary": {"id": "legendary", "label": "Legendary", "color": "#f2a93b", "rank": 3},
    "mythic": {"id": "mythic", "label": "Mythic", "color": "#ff4d6d", "rank": 4},
}
UNUSUAL_GRADE = {"id": "unusual", "label": "Unusual", "color": "#b26bff", "rank": 5}

CLASSIC_EFFECTS = ["burning", "scorching", "starstruck", "void_mist", "frostbite",
                   "circuitry", "bubbly", "ember_storm", "sunbeam", "toxic_haze",
                   "static_charge"]
HALLOWEEN_EFFECTS = ["phantom_procession", "trick_or_treat", "floating_bones",
                     "flying_skulls", "jack_o_lanterns", "skeletal_mishap", "bat_swarm",
                     "haunted_wisps", "cursed_runes", "spider_descent", "raven_feathers",
                     "candlelight_vigil"]

# --------------------------------------------------------------- series
# Series #1 has been on the shelf since opening day.  Every other series is an
# event's (app/models/holidays/), numbered in the order the events ran.
SERIES: Dict[str, Dict[str, Any]] = {
    "classic": {
        "id": "classic", "number": 1,
        "name": "Blockhaven Hat Crate",
        "crate": "crate_classic", "key": "key_standard",
        "tagline": "Every hat ever made for Blockhaven, in one box.",
        "theme": "classic",          # which opening sequence plays (crates.js)
        "colors": {"accent": "#f2c230", "deep": "#3a2410", "glow": "#ffe9a8"},
        "starts": 0, "ends": 0,      # 0 = always
        "grades": {"common": 55, "uncommon": 30, "rare": 12, "legendary": 3},
        "unusual_chance": 0.02,
        "effects": CLASSIC_EFFECTS,
        "loot": [it["id"] for it in catalog.HATS],
    },
}

EVENTS: Dict[str, Dict[str, Any]] = {}
OFFERS: List[Dict[str, Any]] = [
    {"id": "offer_classic_pair", "name": "Crate + Key", "series": "classic",
     "contents": {"crate_classic": 1, "key_standard": 1}, "price": 950,
     "blurb": "One crate and the key for it. Open it the moment it lands."},
    {"id": "offer_classic_five", "name": "Collector's Five", "series": "classic",
     "contents": {"crate_classic": 5, "key_standard": 5}, "price": 4500,
     "blurb": "Five crates, five keys, five chances at a Halo -- or an Unusual."},
]

for _number, _ev in enumerate(holidays.EVENTS, 2):
    # an event's effects: the ones it brought, then its family's older set
    _effects = list(_ev.effects) + [e for e in _ev.family_effects if e not in _ev.effects]
    if _ev.id == "halloween":
        _effects = HALLOWEEN_EFFECTS
    SERIES[_ev.id] = {
        "id": _ev.id, "number": _number,
        "name": _ev.crate["name"], "crate": _ev.crate["id"], "key": _ev.key["id"],
        "tagline": _ev.tagline, "theme": _ev.id, "theme_def": _ev.theme,
        "event": _ev.id, "holiday": _ev.holiday, "year": _ev.year,
        "colors": _ev.colors, "starts": _ev.starts, "ends": _ev.ends,
        "grades": dict(_ev.grades), "unusual_chance": _ev.unusual_chance,
        "effects": _effects, "effect_weights": dict(_ev.effect_weights),
        "loot": list(_ev.loot), "grade_of": dict(_ev.grade_of),
    }
    EVENTS[_ev.id] = {
        "id": _ev.id, "name": _ev.name, "title": _ev.title, "blurb": _ev.blurb,
        "holiday": _ev.holiday, "year": _ev.year,
        "edition": getattr(_ev, "edition", 1),
        "starts": _ev.starts, "ends": _ev.ends, "colors": _ev.colors,
        # the series the market's event hero sells, and the Unusual effect
        # that curls round its crate on the pedestal
        "series": _ev.id, "hero_effect": _ev.hero_effect,
        "badge": (_ev.badge or {}).get("id", "ev_harvest_2026" if _ev.id == "halloween"
                                       else ""),
    }
    OFFERS.extend(_ev.offers)

OFFERS_BY_ID = {o["id"]: o for o in OFFERS}

# ------------------------------------------------------------- lookups
CRATE_SERIES = {s["crate"]: s for s in SERIES.values()}
KEY_SERIES = {s["key"]: s for s in SERIES.values()}

# Hats only ever come out of a crate, from any series, at any time: they are
# what an Unusual can be.  While an event is on, everything else in its crate
# is crate-only too, apart from its weapons and held items; once it is over,
# its collection sells those cosmetics outright (see ``for_sale``).
HATS_ONLY_IN_CRATES = frozenset(it["id"] for it in catalog.ALL_ITEMS if it["slot"] == "hat")
CRATE_EXCLUSIVE = frozenset(
    list(HATS_ONLY_IN_CRATES)
    + [i for s in SERIES.values() for i in s["loot"]
       if (catalog.get(i) or {}).get("slot") != "usable"])
ITEM_SERIES: Dict[str, str] = {}
for _s in SERIES.values():
    if _s["id"] == "classic":
        continue
    for _i in _s["loot"]:
        ITEM_SERIES.setdefault(_i, _s["id"])


def events_forced() -> bool:
    """BLOCKHAVEN_EVENTS=all keeps every event running (for development)."""
    return os.environ.get("BLOCKHAVEN_EVENTS", "").lower() in ("all", "1", "on")


def event_state(event_id: str, now: Optional[int] = None) -> str:
    """'always' (not an event), 'live', 'past' (its collection is in the
    archive) or 'upcoming' (announced, not on sale yet)."""
    if not event_id:
        return "always"
    event = EVENTS.get(event_id)
    if event is None:
        return "past"
    if events_forced():
        return "live"
    now = int(now if now is not None else time.time())
    if event["starts"] and now < event["starts"]:
        return "upcoming"
    if event["ends"] and now >= event["ends"]:
        return "past"
    return "live"


def event_active(event_id: str, now: Optional[int] = None) -> bool:
    """Is the event running right now (not merely in the archive)?"""
    return event_state(event_id, now) in ("always", "live")


def series_state(series: Dict[str, Any], now: Optional[int] = None) -> str:
    return event_state(series.get("event", ""), now)


def series_active(series: Dict[str, Any], now: Optional[int] = None) -> bool:
    """Can its crate and key be bought?  While its event runs, and from the
    archive once it is over -- never before it starts."""
    return series_state(series, now) != "upcoming"


def series_live(series: Dict[str, Any], now: Optional[int] = None) -> bool:
    return series_state(series, now) in ("always", "live")


def active_events(now: Optional[int] = None) -> List[Dict[str, Any]]:
    """The events running right now, the one that started most recently
    first (with every event forced on, that puts the newest at the front)."""
    now = int(now if now is not None else time.time())
    out = []
    for event in EVENTS.values():
        if event_active(event["id"], now):
            out.append(dict(event, seconds_left=max(0, event["ends"] - now)
                            if event["ends"] else 0))
    if events_forced():
        # forced on for development: the real current event (by date) leads
        out.sort(key=lambda e: (not (e["starts"] <= now < e["ends"]), -e["starts"]))
    else:
        out.sort(key=lambda e: -e["starts"])
    return out


def upcoming_events(now: Optional[int] = None) -> List[Dict[str, Any]]:
    now = int(now if now is not None else time.time())
    return sorted([dict(e, seconds_until=max(0, e["starts"] - now)) for e in EVENTS.values()
                   if event_state(e["id"], now) == "upcoming"], key=lambda e: e["starts"])


def for_sale(item: Dict[str, Any], now: Optional[int] = None) -> bool:
    """Whether the market sells this item right now.

    * hats never: they come out of crates
    * an event's own things only once it has started
    * while the event runs, its crate cosmetics are crate-only (the weapons
      and held items are sold, as they always were)
    * once it is over, its collection sells everything but its hats"""
    if item.get("hidden") or int(item.get("price", 0)) < 0:
        return False
    if item["id"] in HATS_ONLY_IN_CRATES:
        return False
    event = item.get("event", "")
    state = event_state(event, now) if event else "always"
    if state == "upcoming":
        return False
    if item["id"] in CRATE_EXCLUSIVE:
        series = SERIES.get(ITEM_SERIES.get(item["id"], ""))
        return bool(series) and series_state(series, now) == "past"
    return True


def grade_of(series: Dict[str, Any], item_id: str) -> str:
    override = (series.get("grade_of") or {}).get(item_id)
    if override:
        return override
    rarity = (catalog.get(item_id) or {}).get("rarity", "common")
    return rarity if rarity in GRADES else "common"


def key_opens(key_item_id: str, crate_item_id: str) -> bool:
    key = catalog.get(key_item_id) or {}
    crate = CRATE_SERIES.get(crate_item_id)
    return bool(crate) and crate["id"] in (key.get("opens") or [])


def _pool(series: Dict[str, Any]) -> Dict[str, List[str]]:
    pool: Dict[str, List[str]] = {}
    for item_id in series["loot"]:
        if catalog.get(item_id) is None:
            continue
        pool.setdefault(grade_of(series, item_id), []).append(item_id)
    return pool


def contents(series_id: str) -> Dict[str, Any]:
    """What is in a crate and the odds of each thing -- shown in full."""
    series = SERIES.get(series_id)
    if series is None:
        raise CrateError("No such crate.")
    pool = _pool(series)
    weights = {g: w for g, w in series["grades"].items() if pool.get(g)}
    total = float(sum(weights.values())) or 1.0
    items = []
    for grade in sorted(weights, key=lambda g: -GRADES[g]["rank"]):
        share = weights[grade] / total
        for item_id in pool[grade]:
            item = catalog.get(item_id)
            items.append({
                "item_id": item_id, "name": item["name"], "slot": item["slot"],
                "slot_label": catalog.SLOT_LABELS.get(item["slot"], item["slot"]),
                "grade": grade, "grade_label": GRADES[grade]["label"],
                "color": GRADES[grade]["color"],
                "chance": round(100.0 * share / len(pool[grade]), 3),
                "unusual_capable": item["slot"] == "hat",
                "description": item.get("description", ""),
            })
    effects = [{"id": e, "name": catalog.UNUSUAL_EFFECTS[e]["name"]}
               for e in series["effects"] if e in catalog.UNUSUAL_EFFECTS]
    return {
        "series": public_series(series), "items": items,
        "grades": [{"id": g, "label": GRADES[g]["label"], "color": GRADES[g]["color"],
                    "chance": round(100.0 * weights[g] / total, 2)}
                   for g in sorted(weights, key=lambda g: GRADES[g]["rank"])],
        "unusual_chance": round(series["unusual_chance"] * 100.0, 2),
        "effects": effects,
    }


def public_series(series: Dict[str, Any]) -> Dict[str, Any]:
    crate = catalog.get(series["crate"]) or {}
    key = catalog.get(series["key"]) or {}
    event = EVENTS.get(series.get("event", "")) or {}
    state = series_state(series)
    return {
        "id": series["id"], "number": series["number"], "name": series["name"],
        "tagline": series["tagline"], "theme": series["theme"],
        "theme_def": series.get("theme_def") or {},
        "colors": series["colors"], "crate": series["crate"], "key": series["key"],
        "crate_name": crate.get("name", ""), "key_name": key.get("name", ""),
        "crate_price": int(crate.get("price", 0)), "key_price": int(key.get("price", 0)),
        "event": series.get("event", ""), "active": series_active(series),
        "live": state in ("always", "live"), "state": state,
        "holiday": series.get("holiday", ""), "year": series.get("year", 0),
        "edition": event.get("edition", 0), "event_name": event.get("name", ""),
        "starts": series.get("starts", 0), "ends": series.get("ends", 0),
        "unusual_chance": round(series["unusual_chance"] * 100.0, 2),
        "loot_count": len(series["loot"]),
    }


def all_series() -> List[Dict[str, Any]]:
    return [public_series(s) for s in sorted(SERIES.values(), key=lambda s: s["number"])]


def event_feature(event_id: str) -> Optional[Dict[str, Any]]:
    """What the market's event hero shows for an event: its series (crate,
    key, prices), the chase items best first, and the effects it pushes."""
    event = EVENTS.get(event_id)
    series = SERIES.get((event or {}).get("series", ""))
    if event is None or series is None:
        return None
    order = {g: i for i, g in enumerate(("mythic", "legendary", "rare", "uncommon", "common"))}
    loot = sorted(series["loot"], key=lambda i: (order.get(grade_of(series, i), 9),
                                                 (catalog.get(i) or {}).get("slot") != "usable"))
    weights = series.get("effect_weights") or {}
    featured = [e for e in series["effects"] if weights.get(e, 1.0) > 1.0] or series["effects"][:2]
    return {"series": public_series(series), "loot": loot,
            "effects": [catalog.UNUSUAL_EFFECTS[e]["name"] for e in featured
                        if e in catalog.UNUSUAL_EFFECTS],
            "hero_effect": event.get("hero_effect", ""),
            "glow": series["colors"].get("glow", "#ffffff")}


def collections(now: Optional[int] = None) -> List[Dict[str, Any]]:
    """Every holiday's run of events, oldest first, for the market's
    Collections: each year's series, what it held, and what is buyable."""
    now = int(now if now is not None else time.time())
    out = []
    for holiday in holidays.HOLIDAYS:
        editions = []
        for ev in [e for e in holidays.EVENTS if e.holiday == holiday["id"]]:
            series = SERIES[ev.id]
            items = []
            for item_id in series["loot"]:
                item = catalog.get(item_id)
                if not item:
                    continue
                items.append({"id": item_id, "name": item["name"], "slot": item["slot"],
                              "slot_label": catalog.SLOT_LABELS.get(item["slot"], item["slot"]),
                              "rarity": item.get("rarity", "common"),
                              "grade": grade_of(series, item_id),
                              "color": GRADES[grade_of(series, item_id)]["color"],
                              "price": int(item.get("price", 0)),
                              "buyable": for_sale(item, now)})
            editions.append(dict(public_series(series), items=items,
                                 title=ev.title, blurb=ev.blurb,
                                 ordinal=holidays.ordinal(getattr(ev, "edition", 1))))
        out.append(dict(holiday, editions=editions))
    return out


# ------------------------------------------------------------- rolling
def roll(series: Dict[str, Any], rng: Optional[random.Random] = None) -> Dict[str, Any]:
    """One draw from a crate: grade, item, and whether it came out Unusual."""
    rng = rng or random.SystemRandom()
    pool = _pool(series)
    grades = [g for g in series["grades"] if pool.get(g)]
    if not grades:
        raise CrateError("That crate is empty.")
    grade = rng.choices(grades, [series["grades"][g] for g in grades])[0]
    item_id = rng.choice(pool[grade])
    item = catalog.get(item_id)
    tier, effect = "normal", ""
    if item["slot"] == "hat" and rng.random() < series["unusual_chance"]:
        tier = "unusual"
        effects = [e for e in series["effects"] if e in catalog.UNUSUAL_EFFECTS]
        boost = series.get("effect_weights") or {}
        effect = rng.choices(effects, [float(boost.get(e, 1.0)) for e in effects])[0]
    return {"item_id": item_id, "grade": grade, "tier": tier, "effect": effect}


REEL_LENGTH = 56
REEL_WIN = 48


def build_reel(series: Dict[str, Any], winner: Dict[str, Any],
               rng: Optional[random.Random] = None) -> List[Dict[str, Any]]:
    """The strip of tiles the opening animation spins past.

    Mostly ordinary draws, weighted like the real odds so the strip *looks*
    like the crate -- with the near misses a reel is for: something rare
    right before the stop and something better just after it, and now and
    then a mystery Unusual tile flashing past.  The winner sits at REEL_WIN.
    """
    rng = rng or random.Random()
    pool = _pool(series)
    grades = [g for g in series["grades"] if pool.get(g)]
    weights = [series["grades"][g] for g in grades]
    ranked = sorted(grades, key=lambda g: GRADES[g]["rank"])

    def tile(grade: Optional[str] = None) -> Dict[str, Any]:
        g = grade or rng.choices(grades, weights)[0]
        return {"item_id": rng.choice(pool[g]), "grade": g, "tier": "normal"}

    reel = [tile() for _ in range(REEL_LENGTH)]
    # a mystery Unusual or two goes past during the fast part of the spin
    for at in rng.sample(range(8, REEL_WIN - 6), 2):
        if rng.random() < 0.7:
            reel[at] = {"item_id": "", "grade": "unusual", "tier": "unusual",
                        "mystery": True}
    # the tease: the best grade sits one past the winner, a good one just before
    best, good = ranked[-1], ranked[max(0, len(ranked) - 2)]
    reel[REEL_WIN + 1] = tile(best)
    reel[REEL_WIN - 1] = tile(good)
    reel[REEL_WIN - 3] = tile(best) if rng.random() < 0.5 else tile(good)
    reel[REEL_WIN] = {"item_id": winner["item_id"], "grade": winner["grade"],
                      "tier": winner["tier"], "effect": winner.get("effect", ""),
                      "winner": True}
    return reel


def _next_serial(conn, item_id: str) -> int:
    return int(conn.execute("SELECT COALESCE(MAX(serial),0) FROM inventory WHERE item_id=?",
                            (item_id,)).fetchone()[0]) + 1


def open_crate(user_id: int, crate_inv: int, key_inv: int) -> Dict[str, Any]:
    """Use one key on one crate.  Both are spent; one item comes out."""
    now = int(time.time())
    with db.transaction() as conn:
        crate_row = conn.execute("SELECT * FROM inventory WHERE id=? AND user_id=?",
                                 (int(crate_inv), int(user_id))).fetchone()
        key_row = conn.execute("SELECT * FROM inventory WHERE id=? AND user_id=?",
                               (int(key_inv), int(user_id))).fetchone()
        if crate_row is None:
            raise CrateError("You do not have that crate any more.")
        if key_row is None:
            raise CrateError("You do not have that key any more.")
        series = CRATE_SERIES.get(crate_row["item_id"])
        if series is None:
            raise CrateError("That is not a crate.")
        if (catalog.get(key_row["item_id"]) or {}).get("slot") != "key":
            raise CrateError("That is not a key.")
        if not key_opens(key_row["item_id"], crate_row["item_id"]):
            raise CrateError("That key does not fit this crate.")
        won = roll(series)
        conn.execute("DELETE FROM inventory WHERE id IN (?,?) AND user_id=?",
                     (int(crate_inv), int(key_inv), int(user_id)))
        serial = _next_serial(conn, won["item_id"])
        cur = conn.execute(
            "INSERT INTO inventory(user_id,item_id,tier,effect,serial,acquired_at,source)"
            " VALUES(?,?,?,?,?,?,?)",
            (int(user_id), won["item_id"], won["tier"], won["effect"], serial, now,
             "crate:%s" % series["id"]))
        inv_id = int(cur.lastrowid)
        conn.execute(
            "INSERT INTO crate_openings(user_id,series,crate_item,key_item,item_id,inv_id,"
            "grade,tier,effect,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
            (int(user_id), series["id"], crate_row["item_id"], key_row["item_id"],
             won["item_id"], inv_id, won["grade"], won["tier"], won["effect"], now))
        username = conn.execute("SELECT username FROM users WHERE id=?",
                                (int(user_id),)).fetchone()["username"]
    db.audit(user_id, "crate.open", won["item_id"],
             {"series": series["id"], "tier": won["tier"], "effect": won["effect"],
              "inv_id": inv_id})
    item = catalog.get(won["item_id"])
    if won["tier"] == "unusual":
        from .. import console
        console.note("UNUSUAL %s unboxed by %s (%s)"
                     % (item["name"], username,
                        catalog.UNUSUAL_EFFECTS[won["effect"]]["name"]))
    # badges: every crate counts, an Unusual counts twice over, and an event
    # crate opened while its event runs counts towards that year's badge
    from . import badges
    changes = [("crates_opened", 1, "add")]
    if won["tier"] == "unusual":
        changes.append(("unusuals_unboxed", 1, "add"))
    event = EVENTS.get(series.get("event", ""))
    if event and event.get("badge") and event_active(event["id"]):
        changes.append((event["badge"], 1, "add"))
    earned = badges.record_many(user_id, changes)
    decorated = inventory.decorate(inventory.get_row(user_id, inv_id) or {
        "id": inv_id, "item_id": won["item_id"], "tier": won["tier"],
        "effect": won["effect"], "serial": serial, "acquired_at": now,
        "source": "crate"})
    decorated["grade"] = won["grade"]
    decorated["grade_label"] = (UNUSUAL_GRADE if won["tier"] == "unusual"
                                else GRADES[won["grade"]])["label"]
    decorated["grade_color"] = GRADES[won["grade"]]["color"]
    return {
        "item": decorated,
        "series": public_series(series),
        "reel": build_reel(series, won),
        "win_index": REEL_WIN,
        "left": stash_counts(user_id),
        # the two rows the opening used up, so a page can take them off its shelf
        "used": {"crate": int(crate_inv), "key": int(key_inv)},
        "badges": [{k: e[k] for k in ("id", "name", "level", "tier_label", "rank",
                                      "first", "emblem", "color")} for e in earned],
    }


# ------------------------------------------------------------ the stash
def stash(user_id: int) -> Dict[str, Any]:
    """The crates and keys a player holds, grouped by series."""
    rows = db.query(
        "SELECT id, item_id, serial, acquired_at FROM inventory WHERE user_id=?"
        " AND item_id IN (%s) ORDER BY id" % ",".join(
            "?" * (len(CRATE_SERIES) + len(KEY_SERIES))),
        [int(user_id)] + list(CRATE_SERIES) + list(KEY_SERIES))
    out: Dict[str, Any] = {s: {"crates": [], "keys": []} for s in SERIES}
    for row in rows:
        if row["item_id"] in CRATE_SERIES:
            out[CRATE_SERIES[row["item_id"]]["id"]]["crates"].append(int(row["id"]))
        else:
            for series_id in (catalog.get(row["item_id"]) or {}).get("opens") or []:
                if series_id in out:
                    out[series_id]["keys"].append(int(row["id"]))
    return out


def stash_counts(user_id: int) -> Dict[str, Dict[str, int]]:
    return {s: {"crates": len(v["crates"]), "keys": len(v["keys"])}
            for s, v in stash(user_id).items()}


# ------------------------------------------------------------- buying
def _grant_rows(conn, user_id: int, contents: Dict[str, int], source: str,
                now: int) -> List[int]:
    ids = []
    for item_id, count in contents.items():
        for _ in range(int(count)):
            cur = conn.execute(
                "INSERT INTO inventory(user_id,item_id,tier,effect,serial,acquired_at,source)"
                " VALUES(?,?,'normal','',?,?,?)",
                (int(user_id), item_id, _next_serial(conn, item_id), now, source))
            ids.append(int(cur.lastrowid))
    return ids


def _charge(conn, user_id: int, price: int, reason: str, now: int) -> int:
    row = conn.execute("SELECT credits FROM users WHERE id=?", (int(user_id),)).fetchone()
    if row is None:
        raise CrateError("No such account.")
    credits = int(row["credits"])
    if credits < price:
        raise CrateError("You need %s more Noogets for that." % f"{price - credits:,}")
    balance = credits - price
    conn.execute("UPDATE users SET credits=? WHERE id=?", (balance, int(user_id)))
    conn.execute(
        "INSERT INTO credit_ledger(user_id,delta,balance_after,reason,actor_id,created_at)"
        " VALUES(?,?,?,?,?,?)", (int(user_id), -price, balance, reason[:120], None, now))
    return balance


def buy_offer(user_id: int, offer_id: str) -> Dict[str, Any]:
    offer = OFFERS_BY_ID.get(offer_id)
    if offer is None:
        raise CrateError("That bundle is not on offer.")
    series = SERIES[offer["series"]]
    if not series_active(series):
        raise CrateError("That bundle went with the event.")
    now = int(time.time())
    with db.transaction() as conn:
        balance = _charge(conn, user_id, int(offer["price"]), "Bought %s" % offer["name"], now)
        ids = _grant_rows(conn, user_id, offer["contents"], "bundle", now)
    db.audit(user_id, "market.bundle", offer_id, {"price": offer["price"], "rows": ids})
    return {"balance": balance, "offer": offer_id, "granted": ids,
            "stash": stash_counts(user_id)}


def drop(user_id: int, crate_item: str, count: int = 1, with_keys: bool = False,
         actor_id: Optional[int] = None, note: str = "") -> Dict[str, Any]:
    """An administrator drops crates (and optionally keys) on a player."""
    series = CRATE_SERIES.get(crate_item)
    if series is None:
        raise CrateError("No such crate.")
    count = max(1, min(50, int(count or 1)))
    now = int(time.time())
    contents = {crate_item: count}
    if with_keys:
        contents[series["key"]] = count
    with db.transaction() as conn:
        if conn.execute("SELECT 1 FROM users WHERE id=?", (int(user_id),)).fetchone() is None:
            raise CrateError("No such account.")
        ids = _grant_rows(conn, user_id, contents, "drop", now)
    crate = catalog.get(crate_item)
    title = ("%d %ss dropped for you!" % (count, crate["name"]) if count > 1
             else "A %s dropped for you!" % crate["name"])
    body = ("With %s to open %s." % (
        "a key" if count == 1 else "%d keys" % count, "it" if count == 1 else "them")
        if with_keys else "Find it under Crates & Keys in your inventory.")
    if note:
        body = "%s %s" % (note.strip()[:120], body)
    notifications.push(user_id, "crate", title, body,
                       {"item_id": crate_item, "series": series["id"], "count": count,
                        "keys": bool(with_keys)})
    db.audit(actor_id, "admin.drop_crate", str(user_id),
             {"crate": crate_item, "count": count, "keys": bool(with_keys)})
    return {"granted": ids, "series": series["id"], "count": count,
            "keys": bool(with_keys)}


# ------------------------------------------------------------- history
def recent_openings(limit: int = 20, series: str = "") -> List[Dict[str, Any]]:
    sql = ("SELECT o.*, u.username FROM crate_openings o JOIN users u ON u.id=o.user_id")
    args: List[Any] = []
    if series:
        sql += " WHERE o.series=?"
        args.append(series)
    sql += " ORDER BY o.id DESC LIMIT ?"
    args.append(int(limit))
    out = []
    for row in db.query(sql, args):
        item = catalog.get(row["item_id"]) or {"name": row["item_id"], "slot": ""}
        effect = catalog.UNUSUAL_EFFECTS.get(row["effect"] or "")
        grade = UNUSUAL_GRADE if row["tier"] == "unusual" else GRADES.get(
            row["grade"], GRADES["common"])
        out.append({"username": row["username"], "item_id": row["item_id"],
                    "name": item["name"], "grade": row["grade"],
                    "grade_label": grade["label"], "color": grade["color"],
                    "tier": row["tier"], "effect": row["effect"] or "",
                    "effect_name": effect["name"] if effect else "",
                    "series": row["series"], "at": int(row["created_at"])})
    return out


def stats() -> Dict[str, int]:
    return dict(db.cached("crates.stats", 10.0, lambda: {
        "opened": int(db.scalar("SELECT COUNT(*) FROM crate_openings")),
        "unusuals": int(db.scalar(
            "SELECT COUNT(*) FROM crate_openings WHERE tier='unusual'")),
    }))


# --------------------------------------------------------- bots unboxing
def bot_unbox(user_id: int, rng: Optional[random.Random] = None) -> Optional[Dict[str, Any]]:
    """A synthetic player buys a crate and a key and opens them, exactly as
    a person would -- same prices, same odds, same ledger -- so the market's
    drop feed has a crowd in it.  Returns None when it cannot afford it."""
    rng = rng or random.Random()
    # the crowd follows the event: a live series is far likelier than the
    # archive, and nobody can open what is not on sale yet
    choices = [s for s in SERIES.values() if series_active(s)]
    if not choices:
        return None
    weights = [6.0 if series_state(s) == "live" else (2.0 if s["id"] == "classic" else 0.25)
               for s in choices]
    series = rng.choices(choices, weights)[0]
    crate, key = catalog.get(series["crate"]), catalog.get(series["key"])
    price = int(crate["price"]) + int(key["price"])
    now = int(time.time())
    try:
        with db.transaction() as conn:
            _charge(conn, user_id, price, "Bought %s and %s" % (crate["name"], key["name"]),
                    now)
            ids = _grant_rows(conn, user_id, {crate["id"]: 1, key["id"]: 1}, "market", now)
    except CrateError:
        return None
    try:
        return open_crate(user_id, ids[0], ids[1])
    except CrateError:
        return None
