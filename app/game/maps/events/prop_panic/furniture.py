"""The fixed furniture of Prop Panic's places: beds, counters, shelving,
sofas, display cases -- everything that is *not* a disguise, drawn in the
same local frame as the props (standing on the floor at the origin, front
to +z) and built with :func:`catalogue.stamp`, so any piece can be turned a
quarter at a time to face whichever way the room wants.

Every piece is solid where a body could meet it, and its tops are real
surfaces: a hider can climb onto a counter and sit among the jars.  The
tops a hider can use are given back by the ``*_top`` constants so the
areas can set props on them.
"""
from __future__ import annotations

from typing import List

from .catalogue import (B, BLACK, BRASS, C, CREAM, GOLD, IRON, K, LEAF, MARBLE, R, S,
                        SILVER, STONE, WHITE, WOOD, WOOD_DARK, WOOD_LIGHT, Part)

COUNTER_TOP = 3.2
TABLE_TOP = 3.0
SHELF_GAP = 3.4


def rug(w: float, d: float, colour: str, decal: str = "", border: str = "") -> List[Part]:
    """A rug flat on the floor (paint, as far as feet are concerned)."""
    parts = [B(0.0, 0.0, 0.0, w, 0.05, d, colour, dec=decal, ghost=True, wrap=bool(decal))]
    if border:
        parts.append(B(0.0, 0.05, 0.0, w - 0.6, 0.02, d - 0.6, border, ghost=True))
    return parts


def bed(colour: str, w: float = 7.0, d: float = 10.0, sheet: str = WHITE,
        frame: str = WOOD) -> List[Part]:
    """A bed, its head against the wall behind it (-z)."""
    hd = d / 2.0
    return [
        B(0.0, 0.0, 0.0, w, 1.4, d - 0.6, frame),
        B(0.0, 0.0, -hd + 0.3, w + 0.4, 4.6, 0.6, frame),
        B(0.0, 0.0, hd - 0.25, w + 0.2, 2.2, 0.5, frame),
        B(0.0, 1.4, -0.25, w - 0.4, 1.0, d - 1.2, sheet),
        R(-w / 4.0, 2.4, -hd + 1.6, w / 2.0 - 0.6, 0.7, 1.6, WHITE),
        R(w / 4.0, 2.4, -hd + 1.6, w / 2.0 - 0.6, 0.7, 1.6, WHITE),
        B(0.0, 2.4, 0.8, w - 0.2, 0.36, d - 4.4, colour, dec="xm_quilt"),
    ]


def wardrobe(colour: str = WOOD, w: float = 6.0, h: float = 9.0, d: float = 3.0) -> List[Part]:
    return [
        B(0.0, 0.0, 0.0, w, h, d, colour),
        B(-w / 4.0, 0.6, d / 2.0, w / 2.0 - 0.3, h - 1.4, 0.06, WOOD_LIGHT),
        B(w / 4.0, 0.6, d / 2.0, w / 2.0 - 0.3, h - 1.4, 0.06, WOOD_LIGHT),
        B(-0.4, h / 2.0, d / 2.0 + 0.06, 0.2, 0.9, 0.12, BRASS),
        B(0.4, h / 2.0, d / 2.0 + 0.06, 0.2, 0.9, 0.12, BRASS),
        B(0.0, h, 0.0, w + 0.4, 0.4, d + 0.3, WOOD_DARK),
    ]


def dresser(colour: str = WOOD, w: float = 6.0, d: float = 2.6, h: float = 3.4) -> List[Part]:
    """A chest of drawers: its top (``h`` + 0.2) is a shelf for small props."""
    parts = [B(0.0, 0.0, 0.0, w, h, d, colour)]
    for k in range(3):
        y = 0.3 + k * (h - 0.4) / 3.0
        parts.append(B(0.0, y, d / 2.0, w - 0.6, (h - 0.4) / 3.0 - 0.2, 0.06, WOOD_LIGHT))
        parts.append(B(0.0, y + (h - 0.4) / 6.0 - 0.1, d / 2.0 + 0.06, 0.8, 0.2, 0.1, BRASS))
    parts.append(B(0.0, h, 0.0, w + 0.2, 0.2, d + 0.2, WOOD_DARK))
    return parts


def counter(w: float, d: float = 3.6, body: str = "#e8e2d4", top: str = "#6a5a4a",
            doors: str = "#c8d8c0") -> List[Part]:
    """A run of kitchen cupboards, the worktop at COUNTER_TOP."""
    parts = [B(0.0, 0.0, -0.1, w, COUNTER_TOP - 0.3, d - 0.2, body),
             B(0.0, COUNTER_TOP - 0.3, 0.0, w, 0.3, d, top)]
    n = max(1, int(w // 3.0))
    for k in range(n):
        x = -w / 2.0 + (k + 0.5) * w / n
        parts.append(B(x, 0.3, d / 2.0 - 0.1, w / n - 0.3, COUNTER_TOP - 0.9, 0.06, doors))
        parts.append(B(x + w / n / 2.0 - 0.5, 1.9, d / 2.0 - 0.04, 0.16, 0.6, 0.1, SILVER))
    return parts


def stove(w: float = 4.0, d: float = 3.6) -> List[Part]:
    return [
        B(0.0, 0.0, -0.1, w, COUNTER_TOP - 0.2, d - 0.2, "#c8402a"),
        B(0.0, COUNTER_TOP - 0.2, 0.0, w, 0.2, d, BLACK),
        B(0.0, 0.5, d / 2.0 - 0.1, w - 0.8, 1.6, 0.06, "#3a3a3a", m="glass"),
        B(0.0, 2.3, d / 2.0 - 0.06, w - 0.8, 0.14, 0.14, SILVER),
        C(-0.9, COUNTER_TOP, -0.6, 1.2, 0.08, 1.2, "#3a3a3a"),
        C(0.9, COUNTER_TOP, -0.6, 1.2, 0.08, 1.2, "#3a3a3a"),
        C(-0.9, COUNTER_TOP, 0.8, 1.0, 0.08, 1.0, "#3a3a3a"),
        C(0.9, COUNTER_TOP, 0.8, 1.0, 0.08, 1.0, "#3a3a3a"),
        B(0.0, COUNTER_TOP, -d / 2.0 + 0.3, w, 1.6, 0.6, "#c8402a"),
    ]


def fridge(colour: str = "#e8f0f0", w: float = 3.8, d: float = 3.4, h: float = 8.0) -> List[Part]:
    return [
        B(0.0, 0.0, 0.0, w, h, d, colour, m="metal"),
        B(0.0, 0.2, d / 2.0, w - 0.3, h * 0.6 - 0.3, 0.06, colour, m="metal"),
        B(0.0, h * 0.6, d / 2.0, w - 0.3, h * 0.4 - 0.2, 0.06, colour, m="metal"),
        B(w / 2.0 - 0.6, h * 0.35, d / 2.0 + 0.06, 0.2, 1.6, 0.12, SILVER),
        B(w / 2.0 - 0.6, h * 0.7, d / 2.0 + 0.06, 0.2, 1.0, 0.12, SILVER),
    ]


def sink_unit(w: float = 5.0, d: float = 3.6) -> List[Part]:
    parts = counter(w, d)
    parts += [
        B(0.0, COUNTER_TOP, -0.2, 2.6, 0.06, 2.0, SILVER, m="metal"),
        C(0.0, COUNTER_TOP, -d / 2.0 + 0.5, 0.3, 1.6, 0.3, SILVER, m="metal"),
        B(0.0, COUNTER_TOP + 1.3, -d / 2.0 + 0.95, 0.24, 0.24, 1.0, SILVER, m="metal"),
    ]
    return parts


def table(w: float, d: float, top: str = WOOD, legs: str = WOOD_DARK,
          cloth: str = "", h: float = TABLE_TOP) -> List[Part]:
    """A table, its top at ``h``; the floor under it is open (a mug can
    hide there)."""
    parts = [B(0.0, h - 0.3, 0.0, w, 0.3, d, top)]
    for sx in (-1, 1):
        for sz in (-1, 1):
            parts.append(B(sx * (w / 2.0 - 0.6), 0.0, sz * (d / 2.0 - 0.6), 0.5, h - 0.3, 0.5, legs))
    if cloth:
        parts.append(B(0.0, h, 0.0, w - 0.6, 0.04, d - 0.6, cloth, dec="xm_gingham", ghost=True,
                       wrap=True))
    return parts


def sofa(colour: str, w: float = 9.0, d: float = 3.6) -> List[Part]:
    return [
        B(0.0, 0.0, 0.1, w, 1.4, d - 0.2, colour),
        R(-w / 4.0 + 0.2, 1.4, 0.35, w / 2.0 - 1.2, 0.7, d - 1.3, colour),
        R(w / 4.0 - 0.2, 1.4, 0.35, w / 2.0 - 1.2, 0.7, d - 1.3, colour),
        B(-w / 2.0 + 0.45, 1.4, 0.1, 0.9, 1.4, d - 0.2, colour),
        B(w / 2.0 - 0.45, 1.4, 0.1, 0.9, 1.4, d - 0.2, colour),
        R(0.0, 1.4, -d / 2.0 + 0.5, w - 1.8, 2.6, 0.8, colour),
    ]


def bookcase(w: float = 6.0, h: float = 9.0, d: float = 2.0, colour: str = WOOD_DARK,
             seed: int = 0) -> List[Part]:
    """Shelves full of books (the books are part of it: you cannot be one)."""
    books = ["#7a2a2a", "#2a4a6a", "#2a6a3a", "#c8a040", "#6a3a6a", "#3a3a3a", "#a85a2a"]
    parts = [B(0.0, 0.0, -0.1, w, h, d - 0.2, colour),
             B(0.0, h, 0.0, w + 0.3, 0.3, d + 0.1, colour)]
    shelves = int((h - 0.6) // 2.6)
    for k in range(shelves):
        y = 0.4 + k * 2.6
        x = -w / 2.0 + 0.4
        n = 0
        while x < w / 2.0 - 0.9:
            bw = 0.45 + ((seed + k * 7 + n * 3) % 4) * 0.12
            bh = 1.6 + ((seed + k * 5 + n * 11) % 5) * 0.15
            parts.append(B(x + bw / 2.0, y, d / 2.0 - 0.12, bw - 0.04, bh, 0.2,
                           books[(seed + k * 3 + n) % len(books)]))
            x += bw
            n += 1
    return parts


def shelf_unit(w: float, levels: int, d: float = 2.4, colour: str = "#d8dcdf",
               gap: float = SHELF_GAP, metal: bool = True) -> List[Part]:
    """Open shelving: uprights and ``levels`` shelves, the first at the
    floor.  Shelf ``k``'s top is at ``0.3 + k * gap`` (see shelf_tops)."""
    m = "metal" if metal else ""
    parts = []
    for sx in (-1, 1):
        parts.append(B(sx * (w / 2.0 - 0.15), 0.0, 0.0, 0.3, levels * gap + 0.4, d, colour, m=m))
    for k in range(levels):
        parts.append(B(0.0, k * gap, 0.0, w - 0.6, 0.3, d, colour, m=m))
    parts.append(B(0.0, levels * gap, 0.0, w - 0.6, 0.3, d, colour, m=m))
    parts.append(B(0.0, 0.3, -d / 2.0 + 0.15, w - 0.6, levels * gap - 0.3, 0.2, colour, m=m))
    return parts


def shelf_tops(levels: int, gap: float = SHELF_GAP) -> List[float]:
    return [0.3 + k * gap for k in range(levels)] + [levels * gap + 0.3]


def fireplace(w: float = 8.0, h: float = 7.0, d: float = 2.4) -> List[Part]:
    """A brick fireplace against the wall behind it, a fire in the grate."""
    return [
        B(-w / 2.0 + 0.9, 0.0, 0.0, 1.8, h - 1.0, d, "#9a4f3a", dec="bricks"),
        B(w / 2.0 - 0.9, 0.0, 0.0, 1.8, h - 1.0, d, "#9a4f3a", dec="bricks"),
        B(0.0, h - 2.6, 0.0, w - 3.6, 1.6, d, "#9a4f3a", dec="bricks"),
        B(0.0, 0.0, -0.6, w - 3.6, h - 2.6, d - 1.2, "#2a1e1a"),
        B(0.0, h - 1.0, 0.1, w + 1.0, 0.5, d + 0.6, WOOD_DARK),
        B(0.0, 0.0, 0.0, w - 3.6, 0.5, d, "#5a5a5a"),
        B(-0.5, 0.5, -0.1, 1.6, 0.4, 0.6, WOOD),
        B(0.4, 0.5, 0.1, 1.4, 0.4, 0.5, WOOD_LIGHT),
        K(0.0, 0.9, 0.0, 1.6, 1.8, 0.8, "#ff8a2a", m="neon", ghost=True),
        K(0.4, 0.9, -0.1, 0.9, 1.2, 0.6, "#ffd23a", m="neon", ghost=True),
    ]


def bathtub(w: float = 4.4, d: float = 9.0) -> List[Part]:
    return [
        B(0.0, 0.0, 0.0, w, 1.4, d, WHITE),
        B(0.0, 1.4, -d / 2.0 + 0.3, w, 1.3, 0.6, WHITE),
        B(0.0, 1.4, d / 2.0 - 0.3, w, 1.3, 0.6, WHITE),
        B(-w / 2.0 + 0.3, 1.4, 0.0, 0.6, 1.3, d - 1.2, WHITE),
        B(w / 2.0 - 0.3, 1.4, 0.0, 0.6, 1.3, d - 1.2, WHITE),
        B(0.0, 1.4, 0.0, w - 1.2, 0.8, d - 1.2, "#9ad0e8", m="glass"),
        C(0.0, 2.7, -d / 2.0 + 0.3, 0.3, 1.2, 0.3, SILVER, m="metal"),
    ]


def toilet() -> List[Part]:
    return [
        B(0.0, 0.0, 0.2, 1.4, 1.6, 2.0, WHITE),
        B(0.0, 1.6, 0.35, 1.6, 0.2, 2.2, WHITE),
        B(0.0, 0.0, -1.1, 2.0, 3.6, 0.8, WHITE),
        B(0.0, 3.6, -1.1, 2.2, 0.2, 1.0, WHITE),
    ]


def basin() -> List[Part]:
    return [
        C(0.0, 0.0, 0.0, 0.9, 2.6, 0.9, WHITE),
        B(0.0, 2.6, 0.1, 2.6, 0.6, 2.0, WHITE),
        B(0.0, 3.2, -0.7, 0.3, 0.6, 0.3, SILVER, m="metal"),
    ]


def painting(w: float, h: float, decal: str, frame: str = GOLD) -> List[Part]:
    """A framed picture flat against the wall behind it (its back at z=0)."""
    return [B(0.0, 0.0, 0.2, w + 0.6, h + 0.6, 0.4, frame),
            B(0.0, 0.3, 0.42, w, h, 0.04, WHITE, dec=decal)]


def pendant(drop: float = 3.0, shade: str = CREAM, lamp: str = "#ffe2a8") -> List[Part]:
    """A ceiling lamp hanging ``drop`` below the ceiling, drawn with the
    ceiling at y = 0 (stamp it at the ceiling's underside)."""
    return [
        C(0.0, -drop + 1.2, 0.0, 0.12, drop - 1.2, 0.12, BLACK, ghost=True),
        K(0.0, -drop, 0.0, 2.4, 1.2, 2.4, shade, ghost=True),
        S(0.0, -drop - 0.3, 0.0, 0.8, 0.6, 0.8, lamp, m="neon", ghost=True),
    ]


def display_case(w: float = 5.0, d: float = 3.0, h: float = 3.2) -> List[Part]:
    """A plinth with a glass case on it (what is inside is on show, not a
    hiding place)."""
    return [
        B(0.0, 0.0, 0.0, w, h, d, "#2a2a30"),
        B(0.0, h, 0.0, w - 0.2, 0.06, d - 0.2, "#d8d0c0"),
        B(0.0, h, d / 2.0 - 0.04, w - 0.4, 2.6, 0.08, "#cfe8ff", m="glass", a=0.35),
        B(0.0, h, -d / 2.0 + 0.04, w - 0.4, 2.6, 0.08, "#cfe8ff", m="glass", a=0.35),
        B(0.0, h + 2.6, 0.0, w, 0.2, d, "#2a2a30"),
        B(-w / 2.0 + 0.1, h, 0.0, 0.2, 2.6, d, "#cfe8ff", m="glass", a=0.35),
        B(w / 2.0 - 0.1, h, 0.0, 0.2, 2.6, d, "#cfe8ff", m="glass", a=0.35),
    ]


def plinth(w: float = 3.0, h: float = 2.0, colour: str = MARBLE) -> List[Part]:
    return [B(0.0, 0.0, 0.0, w, h, w, colour), B(0.0, h, 0.0, w + 0.3, 0.2, w + 0.3, STONE)]


def hedge(w: float, h: float, d: float, colour: str = LEAF) -> List[Part]:
    return [R(0.0, 0.0, 0.0, w, h, d, colour)]


def raised_bed(w: float, d: float, plants: str = "#4a8a3a", soil: str = "#4a3424",
               wood: str = WOOD) -> List[Part]:
    """A planter box with something growing in it; its rim is a step."""
    parts = [B(0.0, 0.0, 0.0, w, 1.6, d, wood),
             B(0.0, 1.6, 0.0, w - 0.6, 0.06, d - 0.6, soil)]
    n = max(1, int(w // 2.2))
    for k in range(n):
        x = -w / 2.0 + (k + 0.5) * w / n
        parts.append(S(x, 1.5, -d / 4.0, 1.6, 1.4, 1.6, plants))
        parts.append(S(x + 0.4, 1.5, d / 4.0, 1.4, 1.2, 1.4, plants))
    return parts


def lamp_stand(h: float = 9.0, colour: str = IRON) -> List[Part]:
    """A garden or street lamp on a post."""
    return [C(0.0, 0.0, 0.0, 0.8, h, 0.8, colour, m="metal"),
            B(0.0, h, 0.0, 1.6, 0.3, 1.6, colour, m="metal"),
            B(0.0, h + 0.3, 0.0, 1.2, 1.4, 1.2, "#ffe2a8", m="neon", ghost=True),
            K(0.0, h + 1.7, 0.0, 2.2, 0.9, 2.2, colour, m="metal")]


def bench(w: float = 6.0, wood: str = WOOD_LIGHT, iron: str = IRON) -> List[Part]:
    return [
        B(-w / 2.0 + 0.4, 0.0, 0.0, 0.3, 1.6, 2.0, iron),
        B(w / 2.0 - 0.4, 0.0, 0.0, 0.3, 1.6, 2.0, iron),
        B(0.0, 1.6, 0.0, w, 0.3, 2.0, wood),
        B(0.0, 1.9, -0.8, w, 1.8, 0.3, wood),
    ]


def till_counter(w: float = 6.0, d: float = 3.0) -> List[Part]:
    """A checkout: a belt, a scanner and a bagging shelf."""
    return [
        B(0.0, 0.0, 0.0, w, 2.8, d, "#3a4a5a"),
        B(0.0, 2.8, 0.0, w, 0.2, d, "#2a2a2a", dec="vinyl"),
        B(w / 2.0 - 1.0, 3.0, 0.0, 1.4, 0.6, 1.4, SILVER, m="metal"),
        C(w / 2.0 - 1.0, 3.6, -0.9, 0.3, 3.0, 0.3, SILVER, m="metal"),
    ]
