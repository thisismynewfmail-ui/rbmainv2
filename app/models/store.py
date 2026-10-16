"""The Crate Vault's shop floor: how /market groups what crates.py and
market.py already know.  No writes, no prices of its own.

The page is built from a handful of read-only views over the catalogue:

``console``    the Event Console -- the live event's crate (or the Classic
               crate when nothing is on), the player's loadout for it and the
               one button they need next
``wings``      the Crate Hall: one wing per holiday, one shelf per year, plus
               the Classic wing; every shelf carries its own loot drawer,
               plates and server-rendered odds
``ring``       the Key Ring: one row per series, so crates.js can always find
               the row it is updating
``spotlight``  the Inspect Bench's picks
``side_odds``  the Odds Board

Templates read these through AttrDict, which answers dict methods before
keys -- so no field here is called items, keys, values, get, pop, update,
copy, clear or setdefault, and a ``held`` count is always read as
``held['keys']`` / ``held['crates']``.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from . import catalog, crates, holidays

# under three days left, the console and the shelves call it
LAST_CALL = 72 * 3600
# a calendar year, near enough, for guessing when a holiday comes round again
YEAR = 365 * 86400 + 21600
GRADE_ORDER = ("mythic", "legendary", "rare", "uncommon", "common")
_GRADE_RANK = {g: i for i, g in enumerate(GRADE_ORDER)}

HOLIDAY_META = {h["id"]: h for h in holidays.HOLIDAYS}
SHORT = {"newyear": "NEW YEAR", "stpatricks": "ST. PAT'S", "easter": "EASTER",
         "july4": "JULY 4TH", "halloween": "HALLOWEEN", "christmas": "CHRISTMAS"}
CLASSIC = {"id": "classic", "name": "Classic", "icon": "star",
           "blurb": "The Blockhaven Hat Crate. On the shelf since opening day, every day."}
SPOT_TOPUP = ("hat_halo", "hat_crown", "hat_lantern", "hat_hexed_witch")
_STATE_ORDER = {"live": 0, "upcoming": 1, "past": 2, "always": 0}


# ------------------------------------------------------------------ helpers
def ink(hex_colour: str) -> str:
    """The text colour that reads on a background of ``hex_colour``."""
    text = (hex_colour or "#000000").lstrip("#")
    if len(text) == 3:
        text = "".join(c * 2 for c in text)
    try:
        rgb = [int(text[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    except ValueError:
        return "#ffffff"

    def lin(c: float) -> float:
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    lum = 0.2126 * lin(rgb[0]) + 0.7152 * lin(rgb[1]) + 0.0722 * lin(rgb[2])
    return "#140800" if lum > 0.36 else "#ffffff"


def series_now(sid: str, now: int) -> Dict[str, Any]:
    """public_series, with its state worked out at ``now`` (public_series
    reads the real clock)."""
    raw = crates.SERIES[sid]
    st = crates.series_state(raw, now)
    return dict(crates.public_series(raw), state=st, live=st in ("always", "live"),
                active=st != "upcoming")


def _price(item_id: str) -> int:
    return int((catalog.get(item_id) or {}).get("price", 0))


def kits(sid: str) -> List[Dict[str, Any]]:
    """Every bundle a series sells, cheapest first, with what it is worth."""
    out = []
    for o in crates.OFFERS:
        if o["series"] != sid:
            continue
        n_crates = sum(int(n) for i, n in o["contents"].items()
                       if (catalog.get(i) or {}).get("slot") == "crate")
        n_keys = sum(int(n) for i, n in o["contents"].items()
                     if (catalog.get(i) or {}).get("slot") == "key")
        value = sum(_price(i) * int(n) for i, n in o["contents"].items())
        out.append(dict(o, value=value, n_crates=n_crates, n_keys=n_keys,
                        short="PAIR" if (n_crates, n_keys) == (1, 1)
                        else "%d-PACK" % max(n_crates, n_keys),
                        saving=value - int(o["price"])))
    out.sort(key=lambda k: (int(k["price"]), k["id"]))
    return out


def classic_feature() -> Dict[str, Any]:
    """event_feature's shape, for the Blockhaven Hat Crate."""
    raw = crates.SERIES["classic"]
    loot = sorted(raw["loot"], key=lambda i: (_GRADE_RANK.get(crates.grade_of(raw, i), 9),
                                              (catalog.get(i) or {}).get("name", i)))
    effects = [catalog.UNUSUAL_EFFECTS[e]["name"] for e in raw["effects"][:2]
               if e in catalog.UNUSUAL_EFFECTS]
    return {"series": crates.public_series(raw), "loot": loot, "effects": effects,
            "hero_effect": raw["effects"][0] if raw["effects"] else "",
            "glow": raw["colors"].get("glow", "#ffffff")}


def _edition_label(event_id: str) -> Dict[str, str]:
    event = crates.EVENTS.get(event_id or "")
    if not event:
        return {"ed_label": "", "ed_short": ""}
    meta = HOLIDAY_META.get(event["holiday"], {})
    return {"ed_label": "%s %d" % (meta.get("name", event["name"]), event["year"]),
            "ed_short": "%s ’%02d" % (SHORT.get(event["holiday"], event["holiday"].upper()),
                                            event["year"] % 100)}


def decorate(cards: List[Dict[str, Any]], now: int) -> List[Dict[str, Any]]:
    """Tag the aisle cards with their event's age and a collection label."""
    for card in cards:
        card["state"] = crates.event_state(card.get("event", ""), now)
        card.update(_edition_label(card.get("event", "")))
    return cards


def _need(held: Dict[str, int]) -> str:
    c, k = int(held.get("crates", 0)), int(held.get("keys", 0))
    if c and k:
        return "open"
    if c:
        return "key"
    if k:
        return "crate"
    return "buy"


def _held(stash: Dict[str, Any], sid: str) -> Dict[str, int]:
    got = stash.get(sid) or {}
    return {"crates": int(got.get("crates", 0)), "keys": int(got.get("keys", 0))}


# ------------------------------------------------------------- the console
def console(now: int, events: List[Dict[str, Any]], stash: Dict[str, Any]) -> Dict[str, Any]:
    """The Event Console: the live event's crate, or the Classic one."""
    ev = events[0] if events else None
    sid = ev["series"] if ev else "classic"
    raw = crates.SERIES[sid]
    series = series_now(sid, now)
    holiday = ev["holiday"] if ev else ""
    meta = HOLIDAY_META.get(holiday) if holiday else None
    colors = dict(raw["colors"])
    feature = (crates.event_feature(ev["id"]) if ev else None) or classic_feature()
    chase = [{"id": i, "color": crates.GRADES[crates.grade_of(raw, i)]["color"]}
             for i in feature["loot"][:21]]
    sold = kits(sid)
    pair = next((k for k in sold if (k["n_crates"], k["n_keys"]) == (1, 1)), None)
    others = [k for k in sold if k is not pair]
    multi = max(others, key=lambda k: (k["n_crates"], -int(k["price"]))) if others else None
    held = _held(stash, sid)
    seconds_left = int(ev.get("seconds_left", 0)) if ev else 0
    upcoming = crates.upcoming_events(now)
    nxt = None
    if upcoming:
        up = upcoming[0]
        nxt = {"id": up["id"], "name": up["name"], "title": up["title"],
               "icon": HOLIDAY_META.get(up["holiday"], CLASSIC)["icon"],
               "days": max(1, -(-int(up["seconds_until"]) // 86400))}
    return {
        "sid": sid, "series": series, "event": ev,
        "holiday": holiday,
        "holiday_name": meta["name"] if meta else CLASSIC["name"],
        "icon": meta["icon"] if meta else CLASSIC["icon"],
        "ordinal": holidays.ordinal(int(ev.get("edition", 1))) if ev else "",
        "year": int(ev["year"]) if ev else 0,
        "colors": colors, "ink": ink(colors.get("accent", "#f2c230")),
        "feature": feature, "chase": chase,
        "pair": pair, "multi": multi,
        "held": held, "need": _need(held),
        "ready": min(held["crates"], held["keys"]),
        "seconds_left": seconds_left,
        "days_left": seconds_left // 86400,
        "last_call": bool(ev and 0 < seconds_left < LAST_CALL),
        "next": nxt,
    }


# ------------------------------------------------------------- the hall
def _piece(item: Dict[str, Any], owned: Dict[str, int]) -> Dict[str, Any]:
    grade = item.get("grade") or "common"
    return {"id": item["id"], "name": item["name"], "slot": item["slot"],
            "slot_label": item.get("slot_label")
            or catalog.SLOT_LABELS.get(item["slot"], item["slot"]),
            "grade": grade, "grade_label": crates.GRADES[grade]["label"],
            "color": crates.GRADES[grade]["color"], "price": int(item.get("price", 0)),
            "buy": bool(item.get("buyable")), "hat": item["slot"] == "hat",
            "owned": int(owned.get(item["id"], 0))}


def _sort_pieces(pieces: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(pieces, key=lambda p: (_GRADE_RANK.get(p["grade"], 9), not p["buy"],
                                         p["name"]))


def _opens_on(starts: int) -> str:
    tm = time.gmtime(int(starts))
    return "%s %d" % (time.strftime("%b", tm), tm.tm_mday)


def shelf(ed: Dict[str, Any], now: int, owned: Dict[str, int],
          stash: Dict[str, Any]) -> Dict[str, Any]:
    """One year's crate on its shelf."""
    sid = ed["id"]
    raw = crates.SERIES[sid]
    st = crates.series_state(raw, now)
    out = {k: v for k, v in ed.items() if k not in ("items", "theme_def")}
    out.update(state=st, live=st in ("always", "live"), active=st != "upcoming")
    upcoming = st == "upcoming"
    pieces = [] if upcoming else _sort_pieces([_piece(it, owned) for it in ed.get("items", [])])
    meta = HOLIDAY_META.get(raw.get("holiday", ""), CLASSIC)
    ends = int(raw.get("ends") or 0)
    left = max(0, ends - now) if ends else 0
    out.update(
        pieces=pieces,
        kits=[] if upcoming else kits(sid),
        odds=[] if upcoming else crates.contents(sid)["grades"],
        on_shelf=sum(1 for p in pieces if p["buy"]),
        collected=sum(1 for p in pieces if p["owned"]),
        held=_held(stash, sid),
        days_left=left // 86400 if st == "live" else 0,
        last_call=st == "live" and 0 < left < LAST_CALL,
        days_until=max(1, -(-(int(raw.get("starts", 0)) - now) // 86400)) if upcoming else 0,
        opens_on=_opens_on(raw.get("starts", 0)) if upcoming else "",
        holiday_name=meta["name"],
        ink=ink(raw["colors"].get("accent", "#f2c230")),
        label=("%s %s · %d" % (ed.get("ordinal", ""), meta["name"], int(ed.get("year", 0)))
               if raw.get("event") else "Always on"),
    )
    return out


def _classic_shelf(now: int, owned: Dict[str, int], stash: Dict[str, Any]) -> Dict[str, Any]:
    raw = crates.SERIES["classic"]
    items = []
    for item_id in raw["loot"]:
        item = catalog.get(item_id)
        if not item:
            continue
        items.append({"id": item_id, "name": item["name"], "slot": item["slot"],
                      "grade": crates.grade_of(raw, item_id),
                      "price": int(item.get("price", 0)),
                      "buyable": crates.for_sale(item, now)})
    ed = dict(series_now("classic", now), items=items, title="Blockhaven Classic",
              blurb=CLASSIC["blurb"], ordinal="")
    return shelf(ed, now, owned, stash)


def wings(now: int, owned: Dict[str, int], stash: Dict[str, Any]) -> List[Dict[str, Any]]:
    """The Crate Hall: a wing per holiday (live first, then Classic, then
    the rest in the order they come round), a shelf per year."""
    live_order = {e["holiday"]: n for n, e in enumerate(crates.active_events(now))}
    out = []
    for holiday in crates.collections(now):
        shelves = [shelf(ed, now, owned, stash) for ed in holiday["editions"]]
        if not shelves:
            continue
        shelves.sort(key=lambda s: (_STATE_ORDER.get(s["state"], 3), -int(s.get("starts", 0))))
        done = [s for s in shelves if s["state"] != "upcoming"]
        soon = [s for s in shelves if s["state"] == "upcoming"]
        years = sorted(int(s.get("year", 0)) for s in (done or soon))
        span = ("%d–%d" % (years[0], years[-1]) if years[0] != years[-1]
                else str(years[0]))
        if soon:
            next_start = min(int(s["starts"]) for s in soon)
        else:
            next_start = max(int(s.get("starts", 0)) for s in shelves)
            while next_start <= now:
                next_start += YEAR
        out.append({
            "id": holiday["id"], "name": holiday["name"], "icon": holiday["icon"],
            "blurb": holiday["blurb"], "shelves": shelves,
            "live": any(s["state"] == "live" for s in shelves),
            "soon": bool(soon), "count": len(done), "span": span,
            "accent": shelves[0]["colors"]["accent"],
            "owned_n": sum(s["collected"] for s in done),
            "total_n": sum(len(s["pieces"]) for s in done),
            "next_start": next_start, "selected": False,
        })
    classic_shelf = _classic_shelf(now, owned, stash)
    classic = dict(CLASSIC, shelves=[classic_shelf], live=False, soon=False, count=1,
                   span="Always on", accent=classic_shelf["colors"]["accent"],
                   owned_n=classic_shelf["collected"], total_n=len(classic_shelf["pieces"]),
                   next_start=0, selected=False)
    lit = sorted([w for w in out if w["live"]], key=lambda w: live_order.get(w["id"], 99))
    rest = sorted([w for w in out if not w["live"]], key=lambda w: w["next_start"])
    ordered = lit + [classic] + rest
    if ordered:
        ordered[0]["selected"] = True
    return ordered


# --------------------------------------------------------------- the ring
def ring(series: List[Dict[str, Any]], stash: Dict[str, Any], live_sid: str) -> List[Dict[str, Any]]:
    """The Key Ring: a row for every series, live and Classic pinned."""
    rows = []
    for s in series:
        held = _held(stash, s["id"])
        rows.append(dict(s, held=held, pinned=s["id"] in (live_sid, "classic"),
                         empty=not held["crates"] and not held["keys"],
                         ready=held["crates"] > 0 and held["keys"] > 0,
                         need_key=held["crates"] > held["keys"],
                         need_crate=held["keys"] > held["crates"],
                         sellable=s.get("state") != "upcoming"))
    rows.sort(key=lambda r: (0 if r["id"] == live_sid and live_sid != "classic"
                             else 1 if r["id"] == "classic" else 2,
                             -int(r.get("starts", 0)), r["id"]))
    return rows


# ---------------------------------------------------------- the bench
def _pick(item_id: str, crate: str) -> Optional[Dict[str, Any]]:
    item = catalog.get(item_id)
    if not item or crate not in crates.SERIES:
        return None
    return {"id": item_id, "name": item["name"], "rarity": item.get("rarity", "common"),
            "description": item.get("description", ""), "crate": crate,
            "fx": " ".join(crates.SERIES[crate]["effects"][:8])}


def spotlight(cn: Dict[str, Any]) -> List[Dict[str, Any]]:
    """The Inspect Bench: the console crate's best hats, topped up with a
    few famous ones."""
    sid = cn["sid"]
    hats = [i for i in cn["feature"]["loot"] if (catalog.get(i) or {}).get("slot") == "hat"]
    picks: List[Dict[str, Any]] = []
    for item_id in hats[:6 if sid == "classic" else 4]:
        pick = _pick(item_id, sid)
        if pick:
            picks.append(pick)
    for item_id in SPOT_TOPUP:
        if len(picks) >= 6:
            break
        if any(p["id"] == item_id for p in picks):
            continue
        pick = _pick(item_id, crates.ITEM_SERIES.get(item_id, "classic"))
        if pick:
            picks.append(pick)
    return picks


def side_odds(cn: Dict[str, Any], now: int) -> List[Dict[str, Any]]:
    """The Odds Board: the console crate's grades, and the Classic crate's."""
    return [{"series": series_now(s, now), "grades": crates.contents(s)["grades"]}
            for s in dict.fromkeys([cn["sid"], "classic"])]
