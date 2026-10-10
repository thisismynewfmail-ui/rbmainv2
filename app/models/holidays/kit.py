"""The workbench every event is built on.

An event (``Event``) is one year's occasion -- the 2023 St. Patrick's Day,
the 2024 Christmas -- and everything that came with it: its crate and the
key that opens it, the cosmetics inside, the weapons and the held items, the
Unusual effects only it carries, the opening show's theme and a badge.

Each holiday module (newyear.py, stpatricks.py, easter.py, july4.py,
halloween.py, christmas.py) makes one ``Event`` per year and fills it with
decorated builder functions::

    EV = Event("christmas_2023", "christmas", 2023, "xm23", ...)

    @EV.hat("elf_cap", "Jingle Elf Cap", "Two bells...", "rare")
    def _():
        return [place(...), part(...), ...]

The decorators turn a function that returns a part list into a catalogue
item with an id (``hat_xm23_elf_cap``), a price from its rarity, the event's
id and the hat-hair rule, so a holiday module reads as a list of designs
rather than as bookkeeping.

**Fitting the head.**  Both heads are rounded boxes hanging below the hat
origin (the top centre of the head): the male one 1.46 x 1.28 x 1.40, the
female one 1.34 x 1.27 x 1.34, so anything that clears the male head clears
the female one.  A round shell has to clear the head's CORNERS, not its
faces -- the corners reach ~0.89 from the axis -- which is what ``reach``
and ``dome`` work out.  ``python3`` can't see the result, so every item is
also held to ``node tools/fitcheck.js`` (nothing of the body may show
through it on either build) and looked at with ``node tools/itemsheet.js``.
"""
from __future__ import annotations

import calendar
import math
import time
from typing import Any, Callable, Dict, List, Optional, Sequence

from ..modeling import mirror_x, part, place, ring_of, rotate  # noqa: F401

PI = math.pi
TAU = math.tau

GOLD = "#f2c230"
GOLD_DARK = "#b8860b"
SILVER = "#c9ced6"
IRON = "#3a3d42"
BRASS = "#c9a227"
BONE = "#ece4d0"
WHITE = "#f4f6f8"
SNOW = "#fbfdff"
BLACK = "#16171b"

# Prices by rarity.  Hats only ever come out of crates (the price is what
# they are worth when sold back); everything else from a past event's
# collection can also be bought outright at this price.
PRICE = {"common": 300, "uncommon": 600, "rare": 1100, "legendary": 1900,
         "mythic": 2800}
WEAPON_PRICE = {"uncommon": 1200, "rare": 1600, "legendary": 2000, "mythic": 2400}


def date(text: str) -> int:
    return calendar.timegm(time.strptime(text, "%Y-%m-%d"))


def shade(hex_colour: str, k: float) -> str:
    """The same colour lighter (k > 1) or darker (k < 1)."""
    h = hex_colour.lstrip("#")
    rgb = [int(h[i:i + 2], 16) for i in (0, 2, 4)]
    rgb = [max(0, min(255, int(round(v * k)))) for v in rgb]
    return "#%02x%02x%02x" % tuple(rgb)


def mix(a: str, b: str, t: float) -> str:
    ha, hb = a.lstrip("#"), b.lstrip("#")
    ca = [int(ha[i:i + 2], 16) for i in (0, 2, 4)]
    cb = [int(hb[i:i + 2], 16) for i in (0, 2, 4)]
    return "#%02x%02x%02x" % tuple(int(round(x + (y - x) * t)) for x, y in zip(ca, cb))


# ------------------------------------------------------------ the head
# The male head (the larger one) as the rig draws it: a rounded box whose
# corners have a radius of about 0.285 in every direction.
HEAD_W, HEAD_H, HEAD_D = 1.46, 1.28, 1.40
_BEV = (0.286, 0.274, 0.283)


def reach(y: float) -> float:
    """How far the head reaches from its axis at height ``y`` below the
    top (y is <= 0): the corner of the rounded box, which is what a round
    shell has to clear."""
    inner_x, inner_z = HEAD_W / 2 - _BEV[0], HEAD_D / 2 - _BEV[2]
    top_inner = -_BEV[1]
    bottom_inner = -HEAD_H + _BEV[1]
    if y > top_inner:
        f = math.sqrt(max(0.0, 1 - ((y - top_inner) / _BEV[1]) ** 2))
    elif y < bottom_inner:
        f = math.sqrt(max(0.0, 1 - ((bottom_inner - y) / _BEV[1]) ** 2))
    else:
        f = 1.0
    return math.hypot(inner_x, inner_z) + f * (_BEV[0] + _BEV[2]) / 2


def dome(y0: float, height: float, c: str, aspect: float = 0.97, margin: float = 0.03,
         t: str = "hemi", **kw) -> Dict[str, Any]:
    """A round crown over the head with its base at ``y0``, tall
    ``height``, just wide enough that the head's corners stay inside it at
    every height (``aspect`` makes it a touch shorter front to back)."""
    native_h = {"hemi": 0.5, "capcrown": 0.52, "bell": 1.02}.get(t, 0.5)
    need = 0.0
    steps = 24
    for k in range(steps + 1):
        y = y0 + (min(0.0, y0 + height) - y0) * k / steps
        if y > 0:
            continue
        h = (y - y0) / max(1e-6, height)
        shape = math.sqrt(max(1e-4, 1 - h * h)) if t == "hemi" else 1.0
        if t == "capcrown":
            # straight for a fifth of its height, then the dome
            band = 0.10 / 0.52
            shape = 1.0 if h <= band else math.sqrt(max(1e-4, 1 - ((h - band) / (1 - band)) ** 2))
        need = max(need, (reach(y) + margin) / max(0.2, shape))
    w = need * 2
    if w > 2.02:
        raise ValueError("dome(%s, %s) would be %.2f wide -- too flat to clear the "
                         "head; use cap()" % (y0, height, w))
    return place(t, [0, y0, 0], [w, height / native_h, w * aspect], c, anchor=[0, 0, 0], **kw)


def cap(y0: float, top: float, c: str, grow: float = 0.0, **kw) -> Dict[str, Any]:
    """A skullcap: a rounded box over the crown from ``y0`` (below the top
    of the head) up to ``top``.  It follows the square skull where a round
    ``dome`` that short would have to splay out into a pancake to clear the
    corners -- use it for every low crown, cushion and pad, and put a
    ``band`` or ``ringband`` round its lower edge."""
    return part("rbox", [0, (y0 + top) / 2, 0], [1.60 + grow, top - y0, 1.54 + grow], c, **kw)


def band(y: float, h: float, c: str, grow: float = 0.0, **kw) -> Dict[str, Any]:
    """A band round the head at height ``y``: a rounded box a little bigger
    than the head, which hugs the square skull better than a ring does."""
    return part("rbox", [0, y, 0], [1.58 + grow, h, 1.52 + grow], c, **kw)


def ringband(y: float, h: float, c: str, margin: float = 0.03, **kw) -> Dict[str, Any]:
    """A round band (a washer) whose outer wall clears the head's corners."""
    r = reach(min(0.0, y - h / 2)) + margin
    return place("ring", [0, y - h / 2, 0], [r * 2, h / 0.2, r * 2 * 0.97], c,
                 anchor=[0, 0, 0], **kw)


def straps(c: str, x: float = 0.36, w: float = 0.13, **kw) -> List[Dict[str, Any]]:
    """Two shoulder straps for a back item, lying across the tops of the
    shoulders (the torso's top is 0.99 above the back anchor on the male
    build and 0.95 on the female, so they rest on one and all but touch
    the other) from the pack forward to the collarbone."""
    return [part("rbox", [x * side, 1.025, 0.20], [w, 0.06, 0.72], c, **kw) for side in (1, -1)]


def around(count: int, radius: float, y: float, fn: Callable, start: float = 0.0,
           zscale: float = 1.0) -> List[Dict[str, Any]]:
    """``fn(angle, x, z)`` at points round a circle (angle 0 is the front,
    +Z, turning towards +X); a returned list is flattened."""
    out: List[Dict[str, Any]] = []
    for k in range(count):
        a = start + TAU * k / count
        got = fn(a, math.sin(a) * radius, math.cos(a) * radius * zscale)
        if isinstance(got, list):
            out.extend(got)
        elif got:
            out.append(got)
    return out


def sides(fn: Callable[[int], List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """``fn(side)`` for side in (1, -1), flattened -- for anything that
    comes in a left and a right."""
    return list(fn(1)) + list(fn(-1))


# ------------------------------------------------------------- motifs
def gift_bow(at: Sequence[float], k: float, c: str, knot: Optional[str] = None,
             yaw: float = 0.0, tails: bool = True) -> List[Dict[str, Any]]:
    """A gift bow: four ribbon loops round a knot, and two tails."""
    knot = knot or shade(c, 0.85)
    x, y, z = at
    out = []
    for i, (turn, lift) in enumerate(((0.0, 0.25), (PI, 0.25), (0.6, 0.55), (PI - 0.6, 0.55))):
        out.append(place("bowloop", [x, y, z], [0.62 * k, 0.62 * k, 0.6 * k],
                         c if i < 2 else shade(c, 1.08), anchor=[0, 0, 0],
                         r=[0, yaw + PI / 2, turn + (lift if turn < PI / 2 else -lift)]))
    out.append(part("sph", [x, y + 0.02 * k, z], [0.16 * k, 0.15 * k, 0.16 * k], knot))
    if tails:
        for side in (1, -1):
            out.append(place("ribbon", [x + 0.05 * k * side, y - 0.04 * k, z],
                             [0.13 * k, 0.40 * k, 0.05 * k], c, anchor=[0, 0.5, 0],
                             r=[0.0, yaw, 0.45 * side]))
    return out


def pompom(at: Sequence[float], size: float, c: str = SNOW) -> Dict[str, Any]:
    return part("sph", list(at), [size, size * 0.94, size], c, decal="fur", wrap=True)


def buckle(at: Sequence[float], w: float, h: float, c: str = GOLD,
           r: Optional[Sequence[float]] = None, plate: Optional[str] = None,
           depth: float = 0.05) -> List[Dict[str, Any]]:
    """A square buckle: four bars round a plate (the leprechaun's, a
    pilgrim's, a belt's)."""
    x, y, z = at
    t = min(w, h) * 0.2
    pieces = [
        part("rbox", [0, h / 2 - t / 2, 0], [w, t, depth], c, m="metal"),
        part("rbox", [0, -h / 2 + t / 2, 0], [w, t, depth], c, m="metal"),
        part("rbox", [w / 2 - t / 2, 0, 0], [t, h, depth], c, m="metal"),
        part("rbox", [-w / 2 + t / 2, 0, 0], [t, h, depth], c, m="metal"),
        part("rbox", [0, 0, 0.004], [t * 0.7, h * 0.66, depth * 1.2], shade(c, 0.85), m="metal"),
    ]
    if plate:
        pieces.insert(0, part("box", [0, 0, -depth * 0.3], [w - t, h - t, depth * 0.4], plate))
    out = []
    for p in pieces:
        off = rotate(p["p"], r) if r else p["p"]
        q = dict(p)
        q["p"] = [round(x + off[0], 4), round(y + off[1], 4), round(z + off[2], 4)]
        if r:
            q["r"] = [round(v, 4) for v in r]
        out.append(q)
    return out


def at_frame(parts: List[Dict[str, Any]], at: Sequence[float], r: Optional[Sequence[float]] = None,
             k: float = 1.0) -> List[Dict[str, Any]]:
    """Move a little sub-model (authored round its own origin) into place:
    scaled by ``k``, turned by ``r`` (as a whole: each part's own turn is
    composed with it only for parts with no turn of their own), then moved
    to ``at``."""
    out = []
    for p in parts:
        off = [p["p"][0] * k, p["p"][1] * k, p["p"][2] * k]
        if r:
            off = rotate(off, r)
        q = dict(p)
        q["p"] = [round(at[0] + off[0], 4), round(at[1] + off[1], 4), round(at[2] + off[2], 4)]
        q["s"] = [round(v * k, 4) for v in p["s"]]
        if r and not p.get("r"):
            q["r"] = [round(v, 4) for v in r]
        out.append(q)
    return out


def stripes_on(parts: List[Dict[str, Any]], count: int, c: str, y0: float, y1: float,
               w: float, d: float, h: float = 0.05) -> None:
    """Thin rounded bands round a column, ``count`` of them from y0 to y1."""
    for k in range(count):
        y = y0 + (y1 - y0) * (k + 0.5) / count
        parts.append(part("rbox", [0, y, 0], [w, h, d], c))


# ------------------------------------------------------------ the event
class Event:
    """One year's occasion and everything in it."""

    def __init__(self, event_id: str, holiday: str, year: int, code: str, *,
                 name: str, title: str, blurb: str, tagline: str,
                 starts: str, ends: str, colors: Dict[str, str],
                 crate_price: int = 500, key_price: int = 600,
                 unusual_chance: float = 0.04,
                 grades: Optional[Dict[str, int]] = None,
                 family_effects: Sequence[str] = (),
                 hero_effect: str = "", stencil: str = ""):
        self.id = event_id
        self.holiday = holiday
        self.year = year
        self.code = code
        self.name = name
        self.title = title
        self.blurb = blurb
        self.tagline = tagline
        self.starts = date(starts)
        self.ends = date(ends)
        self.colors = colors
        self.crate_price = crate_price
        self.key_price = key_price
        self.unusual_chance = unusual_chance
        self.grades = grades or {"uncommon": 42, "rare": 36, "legendary": 15, "mythic": 7}
        self.family_effects = list(family_effects)
        self.hero_effect = hero_effect
        self.stencil = stencil
        self.items: List[Dict[str, Any]] = []
        self.crate: Optional[Dict[str, Any]] = None
        self.key: Optional[Dict[str, Any]] = None
        self.effects: Dict[str, Dict[str, Any]] = {}
        self.effect_weights: Dict[str, float] = {}
        self.grade_of: Dict[str, str] = {}
        self.theme: Dict[str, Any] = {}
        self.badge: Optional[Dict[str, Any]] = None
        self.offers: List[Dict[str, Any]] = []
        self._order = 0

    # ---------------------------------------------------------- helpers
    def _id(self, slot: str, key: str) -> str:
        prefix = {"usable": "use"}.get(slot, slot)
        return "%s_%s_%s" % (prefix, self.code, key)

    def _item(self, slot: str, key: str, name: str, desc: str, rarity: str,
              data: Dict[str, Any], price: Optional[int] = None,
              **extra: Any) -> Dict[str, Any]:
        self._order += 1
        item = {"id": self._id(slot, key), "name": name, "slot": slot,
                "price": int(price if price is not None else PRICE.get(rarity, 600)),
                "rarity": rarity, "description": desc,
                "sort_order": 200 + self._order, "event": self.id, "data": data}
        item.update(extra)
        self.items.append(item)
        return item

    # --------------------------------------------------------- wearables
    def hat(self, key: str, name: str, desc: str, rarity: str = "rare",
            hair: str = "flat", **extra: Any):
        """A hat.  ``hair`` is what happens to the hair under it: "flat"
        (pressed down), "hide" (the hat encloses the head) or "show"."""
        def wrap(fn):
            self._item("hat", key, name, desc, rarity,
                       {"parts": fn(), "hair": hair}, **extra)
            return fn
        return wrap

    def back(self, key: str, name: str, desc: str, rarity: str = "rare", **extra: Any):
        def wrap(fn):
            self._item("back", key, name, desc, rarity, {"parts": fn()}, **extra)
            return fn
        return wrap

    def hairdo(self, key: str, name: str, desc: str, rarity: str = "uncommon", **extra: Any):
        """A hair style, authored in head units (see cosmetics.py)."""
        def wrap(fn):
            self._item("hair", key, name, desc, rarity, {"parts": fn()}, **extra)
            return fn
        return wrap

    def face(self, key: str, name: str, desc: str, shapes: List[Dict[str, Any]],
             rarity: str = "uncommon") -> Dict[str, Any]:
        return self._item("face", key, name, desc, rarity, {"shapes": shapes})

    def shirt(self, key: str, name: str, desc: str, data: Dict[str, Any],
              rarity: str = "uncommon") -> Dict[str, Any]:
        return self._item("shirt", key, name, desc, rarity, data)

    def pants(self, key: str, name: str, desc: str, data: Dict[str, Any],
              rarity: str = "uncommon") -> Dict[str, Any]:
        return self._item("pants", key, name, desc, rarity, data)

    def belt(self, key: str, name: str, desc: str, data: Dict[str, Any],
             rarity: str = "uncommon") -> Dict[str, Any]:
        return self._item("belt", key, name, desc, rarity, data)

    # ----------------------------------------------------------- weapons
    def weapon(self, key: str, name: str, desc: str, stats: Dict[str, Any],
               attrs: Sequence[Sequence[str]], rarity: str = "legendary",
               grade: str = "mythic", proj: Optional[Callable] = None,
               deploy: Optional[Callable] = None, minion: Optional[Dict[str, Any]] = None,
               two_handed: Optional[bool] = None):
        """A weapon (or any held item).  ``stats`` drives the game host (see
        app/game/gear.py for every key it reads); ``attrs`` is the card's
        list of what it does, TF2 style: ("+", "..."), ("-", "...") or
        ("=", "...") for the neutral line.  ``proj``/``deploy`` return the
        part lists the client draws for its projectile or what it places;
        ``minion`` describes what it summons."""
        def wrap(fn):
            data: Dict[str, Any] = {"stats": dict(stats), "parts": fn(),
                                    "attrs": [list(a) for a in attrs]}
            if proj is not None:
                data["proj"] = proj()
            if deploy is not None:
                data["deploy"] = deploy()
            if minion is not None:
                data["minion"] = minion
            if two_handed is not None:
                data["two_handed"] = bool(two_handed)
            item = self._item("usable", key, name, desc, rarity, data,
                              price=WEAPON_PRICE.get(rarity, 1800))
            if grade:
                self.grade_of[item["id"]] = grade
            return fn
        return wrap

    def gear(self, key: str, name: str, desc: str, stats: Dict[str, Any],
             attrs: Sequence[Sequence[str]], rarity: str = "rare", grade: str = "",
             deploy: Optional[Callable] = None):
        """A held item that is not a weapon: a snack, a toy, a gadget."""
        stats = dict(stats)
        stats.setdefault("held_item", True)
        return self.weapon(key, name, desc, stats, attrs, rarity=rarity,
                           grade=grade, deploy=deploy)

    # ---------------------------------------------------- crate and key
    def crate_model(self, name: str, desc: str, hinge: Sequence[float],
                    keyhole: Optional[Sequence[float]] = None, rarity: str = "legendary"):
        """The crate.  Its model marks the lid parts ``lid=1``, the lock
        ``lock=1``; ``hinge`` is the point the lid turns about (axis X) and
        ``keyhole`` the point on the lock's face the key's tip enters."""
        def wrap(fn):
            data: Dict[str, Any] = {"parts": fn(), "hinge": list(hinge)}
            if keyhole is not None:
                data["keyhole"] = list(keyhole)
            self.crate = {"id": "crate_" + self.id, "name": name, "slot": "crate",
                          "price": self.crate_price, "rarity": rarity,
                          "sort_order": 10, "series": self.id, "event": self.id,
                          "description": desc, "data": data}
            return fn
        return wrap

    def key_model(self, name: str, desc: str, shoulder: float, rarity: str = "rare"):
        """The key.  It is authored lying along X with its bit towards +X;
        ``shoulder`` is the X where the blade meets the bow -- how far it
        goes into the lock."""
        def wrap(fn):
            self.key = {"id": "key_" + self.id, "name": name, "slot": "key",
                        "price": self.key_price, "rarity": rarity, "sort_order": 9,
                        "opens": [self.id], "event": self.id, "description": desc,
                        "data": {"parts": fn(), "opens": [self.id],
                                 "shoulder": float(shoulder)}}
            return fn
        return wrap

    # ---------------------------------------------------------- the rest
    def effect(self, effect_id: str, weight: float = 3.0, **definition: Any) -> None:
        definition["event"] = self.id
        self.effects[effect_id] = definition
        self.effect_weights[effect_id] = weight

    def opening(self, **theme: Any) -> None:
        """The opening show (static/js/ui/crates.js reads this as the
        series' theme): sky, ambient, burst colours, the pieces that fly out
        of the lid, the effects that seep and linger, the beam colour, and
        ``backdrop`` -- the CSS art family the stage paints behind it."""
        self.theme = theme

    def award(self, name: str, ranks: Sequence[str], desc: str, emblem: str,
              family: str) -> None:
        self.badge = {"id": "ev_" + self.id, "name": name, "ranks": list(ranks),
                      "description": desc, "emblem": emblem, "family": family}

    def bundle(self, key: str, name: str, crates: int, price: int, blurb: str) -> None:
        self.offers.append({"id": "offer_%s_%s" % (self.id, key), "name": name,
                            "series": self.id,
                            "contents": {"crate_" + self.id: crates, "key_" + self.id: crates},
                            "price": price, "blurb": blurb})

    @property
    def loot(self) -> List[str]:
        return [it["id"] for it in self.items]
