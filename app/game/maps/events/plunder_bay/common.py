"""The pieces Plunder Bay's islands are built from.

Every island is played the same way round (app/game/worlds/plunder_bay.py):
the Scarlet Corsairs' ship is moored off its west end and the Azure
Buccaneers' off its east, each alongside a pier, with the treasure between.
This module builds what every island has -- the seabed and the sea over it,
the two ships with their holds and their cannons, the piers -- and what most
of them are dressed with: rocks, palms, huts, barrels and crates, torches,
campfires and rope bridges.

:class:`Isle` wraps an area with the marks the rules and the bots need:

``dig``     where X marks the spot (a few are live in any haul);
``loot``    where loose treasure turns up (``what``: any, bar or gem);
``idol``    the cursed idol's altar;
``hold``    each crew's hold hatch (``team``, ``r``): carry treasure in;
``cannon``  each crew's deck cannons (``team``, ``yaw`` they face);

and each place adds its own (``sunken`` for the tide, ``tentacle`` for the
kraken, ``patrol`` and ``barracks`` for the redcoats, ``rain`` for the
eruption).

Everything a body can reach is solid and stands on something; the sea is a
sheet of glass over the seabed, waded through -- slowly.
"""
from __future__ import annotations

import math
import random
from typing import Dict, List, Optional, Sequence, Tuple

from ..kit import ArenaArea, Surfaces, building, flight, gable, ground, rect, slab, threshold

Rect = Tuple[float, float, float, float]

HALF = (170.0, 120.0)
SEA_TOP = -1.0              # high water
SEABED = -3.0               # the bottom: waist-deep at high water
DECK = 5.0                  # a ship's main deck
QUARTER = 12.0              # its quarterdeck, over the captain's cabin
FORE = 9.0                  # its forecastle
PIER = 1.6                  # a pier's planking
SHIP_X = 146.0              # each ship's keel: west (red) and east (blue)
SHORE_X = 112.0             # where each end of the island meets the sea

SAND = "#e8d49c"
SAND_WET = "#d4bc84"
SAND_DARK = "#b89c64"
SEA = "#1f6e9e"
ROCK = "#8c867a"
ROCK_DARK = "#6c675e"
ROCK_LIGHT = "#a8a294"
HULL = "#5a3a22"
HULL_DARK = "#3e2816"
DECKING = "#a8805a"
PLANK = "#8a6a44"
TIMBER = "#6a4a2e"
TRIM = "#c8a040"
ROPE = "#c8a878"
CANVAS = "#ece4cc"
THATCH = "#c8a85a"
IRON = "#3a3a40"

CREWS = {
    "red": {"stripe": "#c8302a", "sail": "#b8282a", "trim": "#e8b830",
            "name": "THE SCARLET QUEEN", "glow": "#ff6a5a"},
    "blue": {"stripe": "#2a6ab8", "sail": "#2a5aa8", "trim": "#e8d8a8",
             "name": "THE BLUE MARLIN", "glow": "#6ab8ff"},
}


class Isle:
    """One island under construction: the area, its ground covers, and the
    marks the rules and the bots read."""

    def __init__(self, b: ArenaArea, rng: random.Random):
        self.b = b
        self.rng = rng
        self.s = Surfaces(b)
        self.digs = 0
        self.loots = 0
        self.trails: List[Rect] = []

    def top(self, x: float, z: float, below: float = 3.0) -> float:
        """The height of whatever is underfoot at (x, z) -- turf, a sand
        cover, a path -- so a prop stands on it rather than in it."""
        return self.b.surface(x, z, below)

    # ---------------------------------------------------------------- marks
    def dig(self, x: float, y: Optional[float], z: float, name: str) -> None:
        """Where X marks the spot: a chest is buried here when it is live."""
        y = self.top(x, z) if y is None else y
        self.b.mark("dig", x, y, z, i=self.digs, name=name)
        self.digs += 1

    def loot(self, x: float, y: Optional[float], z: float, kind: str = "any",
             name: str = "") -> None:
        """Where loose treasure turns up (``kind``: any, bar or gem)."""
        y = self.top(x, z, 40.0) if y is None else y
        self.b.mark("loot", x, y, z, what=kind, i=self.loots, name=name)
        self.loots += 1

    def idol(self, x: float, y: float, z: float, colour: str = ROCK_LIGHT) -> None:
        """The cursed idol's altar: a stone block with a gold-rimmed top and
        two braziers, the idol rising on it when its time comes."""
        b = self.b
        b.box([x, y + 1.6, z], [5.0, 3.2, 5.0], colour)
        b.box([x, y + 3.35, z], [5.6, 0.3, 5.6], TRIM, material="metal")
        b.box([x, y + 0.3, z], [6.4, 0.6, 6.4], ROCK_DARK)
        for dx in (-4.4, 4.4):
            b.cyl([x + dx, y + 1.4, z], [1.4, 2.8, 1.4], ROCK_DARK)
            b.cyl([x + dx, y + 3.0, z], [1.8, 0.4, 1.8], IRON, material="metal")
            b.cone([x + dx, y + 3.9, z], [1.2, 1.4, 1.2], "#ffb03a", material="neon",
                   collide=False)
        b.mark("idol", x, y + 3.5, z)

    # ---------------------------------------------------------- the ground
    def land(self, colour: str, holes: Sequence[Rect] = (), soil: str = "#6a5a40") -> None:
        """The island's turf over soil at y 0, out to under the boundary,
        with the sea (and anything else lower) left open in ``holes``."""
        ground(self.b, colour, soil=soil, material="", holes=holes)

    def seabed(self, area: Rect, top: float = SEABED, colour: str = SAND_WET,
               water: bool = True) -> None:
        """A stretch of seabed, solid underfoot, and the sea over it."""
        x0, x1, z0, z1 = area
        slab(self.b, area, top, 3.0, colour)
        if water and top < SEA_TOP:
            self.water(area, top)

    def water(self, area: Rect, bottom: float, top: float = SEA_TOP, colour: str = SEA,
              alpha: float = 0.55) -> None:
        x0, x1, z0, z1 = area
        self.b.box([(x0 + x1) / 2.0, (bottom + top) / 2.0, (z0 + z1) / 2.0],
                   [x1 - x0, top - bottom, z1 - z0], colour, material="glass", alpha=alpha,
                   collide=False)

    def shelf(self, area: Rect, side: str, steps: Sequence[float] = (-1.0, -2.0),
              width: float = 4.0, colour: str = SAND) -> None:
        """A beach going down into the sea on ``side`` of ``area`` (the
        land): strips of sand a step lower each, from the turf to the
        seabed.  The strips lie on the seabed slab, inside the sea hole."""
        x0, x1, z0, z1 = area
        for k, top in enumerate(steps):
            a, c = k * width, (k + 1) * width
            if side == "x-":
                r = (x0 - c, x0 - a, z0, z1)
            elif side == "x+":
                r = (x1 + a, x1 + c, z0, z1)
            elif side == "z-":
                r = (x0, x1, z0 - c, z0 - a)
            else:
                r = (x0, x1, z1 + a, z1 + c)
            self.b.box([(r[0] + r[1]) / 2.0, (SEABED + top) / 2.0, (r[2] + r[3]) / 2.0],
                       [r[1] - r[0], top - SEABED, r[3] - r[2]],
                       SAND if k == 0 else SAND_WET)

    def trail(self, points: Sequence[Tuple[float, float]], width: float = 5.0,
              top: float = 0.08, colour: str = "#c8b07a") -> None:
        """A path laid on the turf along a line of straight legs, each a
        strip ``width`` wide (where two legs meet the second is cut round
        the first, so nothing overlaps)."""
        h = width / 2.0
        for (ax, az), (bx, bz) in zip(points, points[1:]):
            x0, x1 = sorted((ax, bx))
            z0, z1 = sorted((az, bz))
            r = rect(x0 - h, x1 + h, z0 - h, z1 + h)
            self.s.lay(r, top, colour)
            self.trails.append(r)

    def clear(self, x: float, z: float, r: float = 3.0) -> bool:
        """Is (x, z) at least ``r`` from every trail -- somewhere to put a
        palm or a bush?"""
        return not any(t[0] - r < x < t[1] + r and t[2] - r < z < t[3] + r for t in self.trails)

    def cliffs(self, along: str, a0: float, a1: float, back: float, front: float,
               height: float, colours: Sequence[str], base: float = 0.0,
               green: str = "#3f7a34", vines: bool = True, step: float = 12.0,
               recess: float = 3.0, solid_top: bool = False) -> List[Tuple[float, float, float]]:
        """A wall of cliff running along ``along`` ("x" or "z") from ``a0``
        to ``a1``, its foot at ``front`` and its back at ``back``: segments
        of rock of different heights, each set back a little from the line
        (never forward of it), a stratum stepped back on top, jungle on top
        of that, and vines down the face out of reach.  Returns each
        segment's (start, end, face)."""
        b = self.b
        rng = self.rng
        sign = 1.0 if front > back else -1.0
        faces: List[Tuple[float, float, float]] = []
        n = max(1, int(round((a1 - a0) / step)))
        for k in range(n):
            u0 = a0 + k * (a1 - a0) / n
            u1 = u0 + (a1 - a0) / n
            h = height * rng.uniform(0.82, 1.12)
            face = front - sign * rng.uniform(0.0, recess)
            faces.append((u0, u1, face))
            colour = colours[k % len(colours)]
            inset = rng.uniform(2.0, 5.0)
            top2 = rng.uniform(3.0, 8.0)

            def put(c0: float, c1: float, w0: float, w1: float, y0: float, y1: float, col: str,
                    **kw) -> Dict:
                ca, cb = sorted((c0, c1))
                wa, wb = sorted((w0, w1))
                if along == "x":
                    return b.box([(ca + cb) / 2.0, (y0 + y1) / 2.0, (wa + wb) / 2.0],
                                 [cb - ca, y1 - y0, wb - wa], col, **kw)
                return b.box([(wa + wb) / 2.0, (y0 + y1) / 2.0, (ca + cb) / 2.0],
                             [wb - wa, y1 - y0, cb - ca], col, **kw)

            put(u0, u1, back, face, base, base + h, colour)
            put(u0 + 0.4, u1 - 0.4, back, face - sign * inset, base + h, base + h + top2,
                colours[(k + 1) % len(colours)], collide=solid_top)
            put(u0 + 1.0, u1 - 1.0, back, face - sign * (inset + 1.0), base + h + top2,
                base + h + top2 + 1.0, green, collide=False)
            if vines and h > 12.0:
                for f in (0.3, 0.72):
                    c = u0 + (u1 - u0) * f + rng.uniform(-1.0, 1.0)
                    low = base + rng.uniform(7.0, 11.0)
                    put(c - 0.5, c + 0.5, face, face + sign * 0.3, low, base + h, green,
                        collide=False)
        return faces

    # ------------------------------------------------------------- dressing
    def rock(self, x: float, z: float, w: float, d: float, h: float,
             y: Optional[float] = None, colour: str = ROCK, cap: str = "") -> float:
        """A rock: a big block with smaller ones shouldered against it and a
        lump on top, all solid -- a rock you could walk through is worse
        than no rock.  Returns the height of its main top."""
        b = self.b
        rng = self.rng
        y = self.top(x, z) if y is None else y
        b.box([x, y + h / 2.0, z], [w, h, d], colour)
        top = y + h
        b.box([x + rng.uniform(-w * 0.15, w * 0.15), top + h * 0.12, z + rng.uniform(-d * 0.15, d * 0.15)],
              [w * 0.62, h * 0.24, d * 0.58], cap or colour)
        for side in (-1, 1):
            hh = h * rng.uniform(0.45, 0.7)
            b.box([x + side * (w / 2.0 + w * 0.12), y + hh / 2.0, z + rng.uniform(-d * 0.2, d * 0.2)],
                  [w * 0.24, hh, d * 0.6], ROCK_DARK if side < 0 else colour)
        return top

    def palm(self, x: float, z: float, y: Optional[float] = None, h: float = 14.0) -> None:
        """A palm: one straight trunk, solid -- not a stack of rings you
        could climb like a ladder -- banded, a crown of fronds and coconuts
        high out of reach."""
        b = self.b
        rng = self.rng
        y = self.top(x, z) if y is None else y
        b.cyl([x, y + h / 2.0, z], [1.2, h, 1.2], "#7a5a38")
        for k in range(2, int(h // 2.0)):
            b.cyl([x, y + k * 2.0, z], [1.3, 0.24, 1.3], "#6a4a2c", collide=False)
        top = y + h
        b.sphere([x, top + 0.3, z], [1.8, 1.4, 1.8], "#6a5a2a", collide=False)
        for a in range(6):
            ang = a * math.pi / 3.0 + rng.uniform(-0.2, 0.2)
            b.sphere([x + math.cos(ang) * 3.4, top + 0.1, z + math.sin(ang) * 3.4],
                     [6.2 if a % 2 else 5.4, 0.9, 2.2], "#3a8a3a", collide=False,
                     r=[0.0, -ang, 0.0])
        for a in range(3):
            ang = a * 2.1 + 0.5
            b.sphere([x + math.cos(ang) * 0.9, top - 0.6, z + math.sin(ang) * 0.9],
                     [0.7, 0.7, 0.7], "#5a3a1a", collide=False)

    def bush(self, x: float, z: float, y: Optional[float] = None, size: float = 3.0,
             colour: str = "#3a7a3a") -> None:
        """A low clump of jungle: solid (you go round it, not through)."""
        b = self.b
        y = self.top(x, z) if y is None else y
        b.sphere([x, y + size * 0.4, z], [size, size * 0.9, size], colour)
        b.sphere([x + size * 0.35, y + size * 0.3, z - size * 0.2], [size * 0.7, size * 0.6, size * 0.7],
                 "#2e6a32")

    def fern(self, x: float, z: float, y: Optional[float] = None,
             colour: str = "#4a8a3a") -> None:
        """Fronds flat on the ground, nothing to walk through."""
        b = self.b
        y = self.top(x, z) if y is None else y
        for k in range(5):
            a = k * math.tau / 5.0 + self.rng.uniform(-0.2, 0.2)
            b.box([x + math.cos(a) * 1.3, y + 0.06, z + math.sin(a) * 1.3], [2.6, 0.12, 0.9],
                  colour, collide=False, r=[0.0, -a, 0.0])

    def barrel(self, x: float, z: float, y: Optional[float] = None,
               colour: str = "#7a5232") -> None:
        b = self.b
        y = self.top(x, z) if y is None else y
        b.cyl([x, y + 1.6, z], [2.6, 3.2, 2.6], colour)
        for hy in (0.6, 2.6):
            b.cyl([x, y + hy, z], [2.7, 0.3, 2.7], IRON, material="metal", collide=False)

    def crates(self, x: float, z: float, y: Optional[float] = None, n: int = 3) -> None:
        b = self.b
        y = self.top(x, z) if y is None else y
        spots = [(0.0, 0.0), (3.4, 0.4), (0.2, 3.4), (3.8, 3.8)]
        for k in range(min(n, len(spots))):
            dx, dz = spots[k]
            size = 3.0 if k % 2 else 2.6
            b.box([x + dx, y + size / 2.0, z + dz], [size, size, size], "#a07a52", decal="planks")
        if n > 2:
            b.box([x + 0.2, y + 2.6 + 1.1, z + 0.1], [2.2, 2.2, 2.2], "#b88a5a", decal="planks")

    def torch(self, x: float, z: float, y: Optional[float] = None, h: float = 6.0) -> None:
        """A torch on a pole: the pole is solid, the flame sits on its cup."""
        b = self.b
        y = self.top(x, z) if y is None else y
        # all of it solid: whatever could be stood on has nothing over it
        b.cyl([x, y + h / 2.0, z], [0.6, h, 0.6], TIMBER)
        b.cyl([x, y + h + 0.3, z], [1.0, 0.6, 1.0], IRON, material="metal")
        b.cone([x, y + h + 1.2, z], [0.8, 1.2, 0.8], "#ffb03a", material="neon")

    def campfire(self, x: float, z: float, y: Optional[float] = None) -> None:
        b = self.b
        y = self.top(x, z) if y is None else y
        for k in range(8):
            a = k * math.tau / 8.0
            b.cyl([x + math.cos(a) * 2.2, y + 0.4, z + math.sin(a) * 2.2], [1.0, 0.8, 1.0], ROCK_DARK)
        b.cyl([x, y + 0.1, z], [3.4, 0.2, 3.4], "#2a2420", collide=False)
        for a in (0.4, 1.9):
            b.cyl([x, y + 0.5, z], [0.5, 3.0, 0.5], TIMBER, collide=False, r=[math.pi / 2.0, a, 0.0])
        b.cone([x, y + 1.4, z], [1.8, 2.2, 1.8], "#ff8a2a", material="neon", collide=False)
        b.cone([x + 0.3, y + 1.1, z - 0.2], [1.0, 1.4, 1.0], "#ffd04a", material="neon", collide=False)
        # the spit over it, on two forked posts
        for dx in (-2.8, 2.8):
            b.cyl([x + dx, y + 1.6, z], [0.4, 3.2, 0.4], TIMBER)
        b.cyl([x, y + 3.0, z], [0.3, 5.6, 0.3], TIMBER, collide=False, r=[0.0, 0.0, math.pi / 2.0])

    def hut(self, area: Rect, door: str, y: float = 0.0, colour: str = "#a8845a",
            roof: str = THATCH, height: float = 8.0) -> Tuple[float, float]:
        """A beach hut of timber with a thatched, stepped roof and a door on
        ``door``; returns the doorway's centre."""
        x0, x1, z0, z1 = area
        cx, cz = (x0 + x1) / 2.0, (z0 + z1) / 2.0
        along = cx if door in ("z-", "z+") else cz
        span = (along - 2.6, along + 2.6)
        building(self.b, area, y, height, colour, t=0.8, roof_colour=roof, roof_t=0.6,
                 floor_colour=PLANK, doors={door: [(span[0], span[1], y + 7.0)]},
                 lights="#ffcf8a", studs_roof=False)
        gable(self.b, area, y + height + 0.6, roof, "x" if x1 - x0 >= z1 - z0 else "z",
              tiers=3, rise=1.2, overhang=0.8)
        threshold(self.b, area, door, span, t=0.8, y0=y)
        return (cx, z1) if door == "z+" else (cx, z0) if door == "z-" else \
            (x1, cz) if door == "x+" else (x0, cz)

    def rope_bridge(self, x0: float, x1: float, z: float, y: float, width: float = 6.0,
                    bed: float = SEABED) -> None:
        """A plank bridge along x, on posts down to ``bed`` at each end, with
        rope rails strung between the posts (the posts keep you on it)."""
        b = self.b
        length = x1 - x0
        n = max(2, int(length // 2.0))
        for k in range(n):
            px = x0 + (k + 0.5) * length / n
            b.box([px, y - 0.2, z], [length / n - 0.25, 0.4, width],
                  PLANK if k % 2 else "#9a7a52")
        # a beam under each edge, which is what the planks lie on
        for dz in (-width / 2.0 + 0.4, width / 2.0 - 0.4):
            b.box([(x0 + x1) / 2.0, y - 0.65, z + dz], [length, 0.5, 0.8], TIMBER)
        for px in (x0 + 0.5, x1 - 0.5):
            for dz in (-width / 2.0 - 0.4, width / 2.0 + 0.4):
                b.cyl([px, (bed + y + 3.6) / 2.0, z + dz], [0.8, y + 3.6 - bed, 0.8], TIMBER)
        # the rope rail, at the posts' tops: over the head of anybody standing
        # on the ground beside the bridge's ends
        for dz in (-width / 2.0 - 0.4, width / 2.0 + 0.4):
            b.box([(x0 + x1) / 2.0, y + 3.3, z + dz], [length - 1.0, 0.24, 0.24], ROPE,
                  collide=False)

    def flag(self, x: float, z: float, y: Optional[float], colour: str, h: float = 12.0,
             skull: bool = True) -> None:
        """A flag on a pole: a Jolly Roger, or a plain one in ``colour``."""
        b = self.b
        y = self.top(x, z) if y is None else y
        b.cyl([x, y + h / 2.0, z], [0.5, h, 0.5], TIMBER)
        b.box([x + 2.3, y + h - 1.7, z], [4.2, 3.0, 0.16], colour, collide=False)
        if skull:
            b.sphere([x + 2.3, y + h - 1.4, z], [1.1, 1.1, 0.24], "#f0ece0", collide=False)
            for a in (0.7, -0.7):
                b.box([x + 2.3, y + h - 2.5, z], [1.9, 0.26, 0.2], "#f0ece0", collide=False,
                      r=[0.0, 0.0, a])


# ================================================================== ships
def galleon(isle: Isle, team: str, sz: float = 0.0) -> Dict[str, float]:
    """A crew's galleon, moored along z off its end of the island with its
    pier alongside, built in the ship's own frame and turned to face in:
    ``u`` runs across the ship towards the island, ``v`` along the keel
    from the stern (v -) to the bow (v +).

    The main deck has the hold hatch in the middle (the ``hold`` mark:
    carry treasure in) and two gangplanks down to the pier; the quarterdeck
    over the stern has the wheel and the captain's cabin under it, the
    forecastle the bow; a cannon on each looks out over the beach.  Three
    masts carry the crew's sails and a Jolly Roger."""
    b = isle.b
    crew = CREWS[team]
    side = -1.0 if team == "red" else 1.0
    sx = side * SHIP_X
    inward = -side

    def X(u: float) -> float:
        return sx + inward * u

    def box(u0: float, u1: float, v0: float, v1: float, y0: float, y1: float, colour: str,
            **kw) -> None:
        xa, xb = sorted((X(u0), X(u1)))
        b.box([(xa + xb) / 2.0, (y0 + y1) / 2.0, sz + (v0 + v1) / 2.0],
              [xb - xa, y1 - y0, v1 - v0], colour, **kw)

    def cyl(u: float, v: float, y0: float, y1: float, d: float, colour: str, **kw) -> None:
        b.cyl([X(u), (y0 + y1) / 2.0, sz + v], [d, y1 - y0, d], colour, **kw)

    # ---- the hull: below the main deck, tapering at the bow
    box(-8.0, 8.0, -28.0, 26.0, SEABED, DECK, HULL)
    box(-5.0, 5.0, 26.0, 32.0, SEABED, FORE, HULL)
    box(-2.5, 2.5, 32.0, 35.0, SEABED + 2.0, FORE, HULL)
    # the stripe along the side in the crew's colour, and the waterline
    for sgn in (-1.0, 1.0):
        u0, u1 = (8.0, 8.2) if sgn > 0 else (-8.2, -8.0)
        box(u0, u1, -28.0, 26.0, 2.6, 3.8, crew["stripe"])
        box(u0, u1, -28.0, 26.0, -0.4, 0.2, HULL_DARK)

    # ---- the captain's cabin under the quarterdeck
    box(-8.0, -6.4, -28.0, -14.0, DECK, QUARTER - 1.0, HULL)
    box(6.4, 8.0, -28.0, -14.0, DECK, QUARTER - 1.0, HULL)
    box(-6.4, 6.4, -28.0, -26.6, DECK, QUARTER - 1.0, HULL)
    # the front wall, a door in its middle and a window each side
    front = [(-6.4, -4.4, DECK, QUARTER - 1.0), (-4.4, -3.4, DECK, DECK + 2.4),
             (-4.4, -3.4, DECK + 5.4, QUARTER - 1.0), (-3.4, -2.0, DECK, QUARTER - 1.0),
             (-2.0, 2.0, DECK + 7.0, QUARTER - 1.0), (2.0, 3.4, DECK, QUARTER - 1.0),
             (3.4, 4.4, DECK, DECK + 2.4), (3.4, 4.4, DECK + 5.4, QUARTER - 1.0),
             (4.4, 6.4, DECK, QUARTER - 1.0)]
    for u0, u1, y0, y1 in front:
        box(u0, u1, -15.0, -14.0, y0, y1, HULL_DARK)
    for u0 in (-4.4, 3.4):
        box(u0, u0 + 1.0, -14.7, -14.3, DECK + 2.4, DECK + 5.4, "#cfe0e8", material="glass",
            alpha=0.45)
    # the quarterdeck over it
    box(-8.0, 8.0, -28.0, -14.0, QUARTER - 1.0, QUARTER, DECKING)
    # inside: the chart table, the captain's chair, a sea chest, a lamp
    box(-2.6, 2.6, -22.0, -19.0, DECK, DECK + 3.0, TIMBER)
    chart = b.box([X(0.0), DECK + 3.03, sz - 20.5], [4.8, 0.06, 2.6], "#e8dcb8", collide=False,
                  decal="pb_map")
    chart["dw"] = 1
    box(-1.2, 1.2, -24.6, -23.4, DECK, DECK + 2.0, HULL_DARK)
    box(-1.2, 1.2, -25.6, -24.6, DECK, DECK + 4.4, HULL_DARK)
    box(3.0, 5.6, -26.4, -24.0, DECK, DECK + 2.2, "#7a4a28")
    box(2.9, 5.7, -26.5, -23.9, DECK + 2.2, DECK + 2.6, TRIM, material="metal")
    box(-0.5, 0.5, -20.9, -20.1, QUARTER - 1.6, QUARTER - 1.0, IRON, material="metal", collide=False)
    box(-0.4, 0.4, -20.8, -20.2, QUARTER - 2.6, QUARTER - 1.6, "#ffcf7a", material="neon",
        collide=False)
    # the stern windows, lit from inside, and the ship's name under them
    for k in range(4):
        u = -5.0 + k * 3.3
        box(u - 1.0, u + 1.0, -28.2, -28.0, DECK + 2.4, DECK + 5.0, "#ffd890", material="neon",
            collide=False)
    box(-6.0, 6.0, -28.25, -28.0, DECK - 1.6, DECK - 0.2, crew["stripe"], collide=False,
        decal="t~%s~%s~#f4e8c8~8.57" % (crew["name"], crew["stripe"]))
    # the rails round the quarterdeck, open where the stairs come up
    box(-8.0, -7.2, -28.0, -14.0, QUARTER, QUARTER + 1.8, HULL_DARK)
    box(7.2, 8.0, -28.0, -14.0, QUARTER, QUARTER + 1.8, HULL_DARK)
    box(-7.2, 7.2, -28.0, -27.2, QUARTER, QUARTER + 1.8, HULL_DARK)
    box(-4.4, 4.4, -14.8, -14.0, QUARTER, QUARTER + 1.8, HULL_DARK)
    # the wheel and the binnacle
    box(-0.6, 0.6, -18.2, -17.0, QUARTER, QUARTER + 2.4, TIMBER)
    b.cyl([X(0.0), QUARTER + 3.2, sz - 17.6], [2.8, 0.3, 2.8], "#7a4a28", collide=False,
          r=[math.pi / 2.0, 0.0, 0.0])
    for k in range(4):
        b.box([X(0.0), QUARTER + 3.2, sz - 17.6], [0.18, 3.6, 0.18], "#5a3a20", collide=False,
              r=[0.0, 0.0, k * math.pi / 4.0])
    # the stairs up to the quarterdeck, one each side of the cabin door
    for lo, hi in ((-7.2, -4.4), (4.4, 7.2)):
        xa, xb = sorted((X(lo), X(hi)))
        flight(b, "z", sz - 6.0, sz - 14.0, xa, xb, DECK, QUARTER, TIMBER, fill=DECK)
    # lanterns at the stern corners
    for u in (-7.6, 7.6):
        box(u - 0.4, u + 0.4, -28.4, -27.6, QUARTER + 1.8, QUARTER + 2.2, IRON, material="metal",
            collide=False)
        box(u - 0.3, u + 0.3, -28.3, -27.7, QUARTER + 2.2, QUARTER + 3.3, "#ffcf7a",
            material="neon", collide=False)

    # ---- the main deck: rails, the hold, the gangplank openings
    planks = [(-5.0, -1.0), (8.0, 12.0)]           # where the gangplanks come aboard
    cursor = -14.0
    for v0, v1 in planks:
        box(7.2, 8.0, cursor, v0, DECK, DECK + 2.2, HULL_DARK)
        cursor = v1
    box(7.2, 8.0, cursor, 16.0, DECK, DECK + 2.2, HULL_DARK)
    box(-8.0, -7.2, -14.0, 16.0, DECK, DECK + 2.2, HULL_DARK)
    for v in (-10.0, -6.0, 0.0, 4.0, 13.0):
        box(-8.2, -7.0, v - 0.3, v + 0.3, DECK + 2.2, DECK + 2.5, TRIM, collide=False)
    # the hold hatch: a grating in a low coaming, and the crew's glow on it
    grating = b.box([X(0.0), DECK + 0.05, sz - 2.0], [7.0, 0.1, 7.0], "#4a3220", collide=False,
                    decal="pb_grate")
    grating["dw"] = 1
    for u0, u1, v0, v1 in ((-4.1, -3.5, -6.1, 2.1), (3.5, 4.1, -6.1, 2.1),
                           (-3.5, 3.5, -6.1, -5.5), (-3.5, 3.5, 1.5, 2.1)):
        box(u0, u1, v0, v1, DECK, DECK + 0.5, TIMBER)
    b.cyl([X(0.0), DECK + 0.13, sz - 2.0], [6.2, 0.06, 6.2], crew["glow"], material="neon",
          alpha=0.45, collide=False)
    b.mark("hold", X(0.0), DECK, sz - 2.0, team=team, r=4.2)
    # coils of rope, a capstan, barrels lashed to the rail
    b.cyl([X(-4.0), DECK + 1.2, sz + 9.5], [2.4, 2.4, 2.4], TIMBER)
    b.cyl([X(-4.0), DECK + 2.6, sz + 9.5], [3.0, 0.4, 3.0], HULL_DARK)
    for u, v in ((-5.6, -3.0), (-5.6, 14.0), (5.6, 14.0)):
        isle.barrel(X(u), sz + v, DECK)
    b.cyl([X(5.6), DECK + 0.2, sz + 3.0], [2.4, 0.4, 2.4], ROPE, collide=False)

    # ---- the forecastle
    box(-8.0, 8.0, 16.0, 26.0, DECK, FORE, HULL)
    box(-8.0, -7.2, 16.8, 25.2, FORE, FORE + 1.8, HULL_DARK)
    box(7.2, 8.0, 16.8, 25.2, FORE, FORE + 1.8, HULL_DARK)
    box(-8.0, -2.5, 16.0, 16.8, FORE, FORE + 1.8, HULL_DARK)
    box(2.5, 8.0, 16.0, 16.8, FORE, FORE + 1.8, HULL_DARK)
    box(-5.0, -4.2, 26.0, 32.0, FORE, FORE + 1.8, HULL_DARK)
    box(4.2, 5.0, 26.0, 32.0, FORE, FORE + 1.8, HULL_DARK)
    box(-8.0, -5.0, 25.2, 26.0, FORE, FORE + 1.8, HULL_DARK)
    box(5.0, 8.0, 25.2, 26.0, FORE, FORE + 1.8, HULL_DARK)
    box(-2.5, 2.5, 34.2, 35.0, FORE, FORE + 1.8, HULL_DARK)
    box(-4.2, -2.5, 31.2, 32.0, FORE, FORE + 1.8, HULL_DARK)
    box(2.5, 4.2, 31.2, 32.0, FORE, FORE + 1.8, HULL_DARK)
    box(-2.5, -1.7, 32.0, 34.2, FORE, FORE + 1.8, HULL_DARK)
    box(1.7, 2.5, 32.0, 34.2, FORE, FORE + 1.8, HULL_DARK)
    xa, xb = sorted((X(-2.5), X(2.5)))
    flight(b, "z", sz + 11.0, sz + 16.0, xa, xb, DECK, FORE, TIMBER, fill=DECK)
    # the bowsprit and the figurehead
    b.cyl([X(0.0), FORE + 3.6, sz + 40.0], [1.0, 13.0, 1.0], TIMBER, collide=False,
          r=[1.15, 0.0, 0.0])
    b.sphere([X(0.0), FORE - 1.2, sz + 35.6], [1.6, 2.2, 1.6], TRIM, collide=False)

    # ---- the masts, yards and sails
    # (the lowest sail on each mast clears the head of anybody standing on
    # the rail under it)
    for v, base, height, yards in ((-21.0, QUARTER, 26.0, (15.0, 22.0)),
                                   (7.0, DECK, 38.0, (15.0, 24.0, 32.0)),
                                   (21.0, FORE, 30.0, (15.0, 23.0))):
        cyl(0.0, v, base, base + height, 1.6, TIMBER)
        for k, yy in enumerate(yards):
            span = 18.0 - k * 3.0
            b.cyl([X(0.0), base + yy, sz + v], [0.6, span, 0.6], TIMBER, collide=False,
                  r=[0.0, 0.0, math.pi / 2.0])
            drop = 7.0 - k * 1.2
            # the sail hangs off the truss just forward of the mast
            b.box([X(0.0), base + yy - 0.3 - drop / 2.0, sz + v + 0.95],
                  [span - 1.6, drop, 0.3], crew["sail"], collide=False)
            b.box([X(0.0), base + yy - 0.3 - drop / 2.0, sz + v + 1.14],
                  [span * 0.32, drop * 0.86, 0.08], "#f4ecd8", collide=False)
            # and the yard is held to the mast by its truss
            b.box([X(0.0), base + yy, sz + v + 0.55], [1.0, 0.8, 0.5], IRON, material="metal",
                  collide=False)
        if v == 7.0:
            # the crow's nest and the Jolly Roger at the masthead
            b.cyl([X(0.0), base + 35.0, sz + v], [4.2, 1.2, 4.2], TIMBER, collide=False)
            b.cyl([X(0.0), base + height + 2.0, sz + v], [0.3, 4.0, 0.3], TIMBER, collide=False)
            b.box([X(0.0) + inward * 2.1, base + height + 2.8, sz + v], [4.0, 2.6, 0.14],
                  "#141414", collide=False)
            b.sphere([X(0.0) + inward * 2.1, base + height + 3.1, sz + v], [1.0, 1.0, 0.24],
                     "#f0ece0", collide=False)
            for a in (0.7, -0.7):
                b.box([X(0.0) + inward * 2.1, base + height + 2.2, sz + v], [1.8, 0.24, 0.2],
                      "#f0ece0", collide=False, r=[0.0, 0.0, a])
    # the shrouds: ropes from the masts down to the rails
    for v, base, height in ((7.0, DECK, 38.0), (21.0, FORE, 30.0)):
        for sgn in (-1.0, 1.0):
            top_u, top_y = 0.0, base + height * 0.72
            foot_u, foot_y = sgn * 7.6, base + (2.2 if base == DECK else 1.8)
            du, dy = top_u - foot_u, top_y - foot_y
            length = math.hypot(du, dy)
            ang = math.atan2(du * inward, dy)
            b.box([X((top_u + foot_u) / 2.0), (top_y + foot_y) / 2.0, sz + v - 1.2],
                  [0.18, length, 0.18], ROPE, collide=False, r=[0.0, 0.0, -ang])

    # ---- the cannons, one on the quarterdeck and one on the forecastle
    for v, deck in ((-23.5, QUARTER), (21.5, FORE)):
        box(3.2, 6.0, v - 1.4, v + 1.4, deck, deck + 1.4, "#5a3a22")
        box(4.0, 5.2, v - 0.8, v + 0.8, deck + 1.4, deck + 1.8, "#4a2e1a")
        for dv in (-1.55, 1.55):
            b.cyl([X(4.6), deck + 0.6, sz + v + dv], [1.2, 0.3, 1.2], IRON, material="metal",
                  collide=False, r=[math.pi / 2.0, 0.0, 0.0])
        b.cyl([X(6.4), deck + 2.4, sz + v], [1.2, 4.6, 1.2], IRON, material="metal",
              collide=False, r=[0.0, 0.0, math.pi / 2.0])
        b.cyl([X(8.7), deck + 2.4, sz + v], [1.5, 0.5, 1.5], IRON, material="metal",
              collide=False, r=[0.0, 0.0, math.pi / 2.0])
        b.sphere([X(1.8), deck + 0.5, sz + v + 2.2], [1.0, 1.0, 1.0], IRON, material="metal",
                 collide=False)
        b.mark("cannon", X(4.6), deck, sz + v, team=team,
               yaw=round(math.atan2(inward, 0.0), 3))

    # ---- the pier alongside and the two walkways to the island
    pier_u = (8.0, 14.0)
    box(pier_u[0], pier_u[1], -18.0, 18.0, PIER - 0.6, PIER, PLANK)
    for v in (-17.0, -9.0, 0.0, 9.0, 17.0):
        for u in (8.8, 13.2):
            cyl(u, v, SEABED, PIER - 0.6, 1.0, TIMBER)
    for v0, v1 in planks:
        xa, xb = sorted((X(13.5), X(8.0)))
        flight(b, "x", X(13.5), X(8.0), sz + v0, sz + v1, PIER, DECK, TIMBER, fill=PIER)
    # bollards and a coil of rope on the pier, the mooring lines to the ship
    for v in (-15.0, 15.0):
        cyl(13.0, v, PIER, PIER + 1.6, 1.2, IRON, material="metal")
    walk = (14.0, SHIP_X - SHORE_X)
    for v0, v1 in ((-18.0, -12.0), (12.0, 18.0)):
        box(walk[0], walk[1], v0, v1, PIER - 0.6, PIER, PLANK)
        for u in (20.0, 27.0):
            for v in (v0 + 0.8, v1 - 0.8):
                cyl(u, v, SEABED, PIER - 0.6, 1.0, TIMBER)
        # posts along the outer edge of each walkway with a rope between
        edge = v0 + 0.3 if v0 < 0 else v1 - 0.3
        for u in (16.0, 24.0, 31.0):
            cyl(u, edge, PIER, PIER + 2.8, 0.6, TIMBER)
        b.box([X((16.0 + 31.0) / 2.0), PIER + 2.4, sz + edge], [15.0, 0.22, 0.22], ROPE)

    # ---- spawns: on the main deck, between the stairs and forward of the
    # hold, with room round each
    for u, v in ((-1.2, -11.0), (1.2, -11.0), (-1.2, -8.4), (1.2, -8.4), (3.8, 4.6),
                 (-3.8, 4.6)):
        b.team_spawn(team, X(u), DECK, sz + v, yaw=round(math.atan2(inward, 0.0), 3))
    return {"x": sx, "z": sz, "inward": inward}
