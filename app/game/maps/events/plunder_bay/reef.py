"""The Coral Reef: an atoll of sandy islets round a lagoon, joined by
boardwalks over the shallows, with a great wreck run aground in the middle.

Layout (north is -z; the Scarlet Corsairs' ship off the west key, the
Azure Buccaneers' off the east)::

    z -114              LIGHTHOUSE ROCK (the lighthouse, the keeper's cottage)
    z  -78        NW key ====== boardwalk ====== NE key
                    ||                              ||
   SCARLET  DRIFTWOOD KEY   ~~~ the basin: THE LEVIATHAN ~~~   COCONUT KEY  BLUE
    QUEEN   (stilt hut)          (wrecked, broken in two)      (stilt hut)  MARLIN
                    ||                              ||
    z   78        SW key ====== boardwalk ====== SE key
    z  114                  CLAM FLATS (giant clams, the fishing shack)

Everything between the keys is water: knee-deep over the shallows (slow
going) and chest-deep in the basin round the wreck (slower).  The boardwalks
are the quick way round; the wreck is reached by wading the basin, or by
the broken boardwalks out from the north rock and the clam flats, and is
climbed through the break amidships, where it snapped in two.

The twist is the kraken (``extra["twist"] = "kraken"``): it rises in the
basin under the wreck, its tentacles coming up at the ``tentacle`` marks to
slam whoever is near -- and knock whatever they are carrying out of their
hands.
"""
from __future__ import annotations

import math
import random
from typing import Tuple

from ..calamity_coast.town import lookout_tower, skirt
from ..kit import ArenaArea, backdrop, flight, slab
from ...ironvale import carve
from .common import (HULL, HULL_DARK, IRON, PLANK, ROCK, ROCK_DARK, ROCK_LIGHT, SAND, SAND_WET,
                     SEA, SEA_TOP, SHIP_X, SHORE_X, TIMBER, TRIM, Isle, galleon)

HALF = (170.0, 120.0)
SKY = {"top": "#2a8ad8", "horizon": "#bff0f0", "sun": [0.3, 0.75, 0.25], "clouds": 0.4,
       "tint": "#f0fff8"}
AMBIENT = "#b8c8cc"
GROUND = "#e6d8a4"
FOG = 900.0

SHALLOW = -2.4              # the reef flat: knee-deep at high water
BASIN = -5.0                # the lagoon's basin round the wreck: chest-deep
RING = -3.7                 # the step down into the basin
ISLE = 0.4                  # a key's sand
BEACH = -1.0                # the strip of beach round every key
WALK = 1.0                  # the boardwalks
LAGOON = "#2ab8b8"
CORAL = ["#ff6a8a", "#ff9a3a", "#9a5ad8", "#ffd04a", "#3ac8b8", "#f05a5a"]
BASIN_R = (-40.0, 40.0, -44.0, 44.0)

KEYS = {
    "west": (-SHORE_X, -76.0, -34.0, 34.0),
    "east": (76.0, SHORE_X, -34.0, 34.0),
    "north": (-28.0, 28.0, -114.0, -84.0),
    "south": (-28.0, 28.0, 84.0, 114.0),
    "nw": (-84.0, -56.0, -90.0, -66.0),
    "ne": (56.0, 84.0, -90.0, -66.0),
    "sw": (-84.0, -56.0, 66.0, 90.0),
    "se": (56.0, 84.0, 66.0, 90.0),
}
# boardwalks: (x0, x1, z0, z1), each running from one key's edge to the next
WALKS = [
    (-82.0, -77.0, -66.0, -34.0), (77.0, 82.0, -66.0, -34.0),
    (-82.0, -77.0, 34.0, 66.0), (77.0, 82.0, 34.0, 66.0),
    (-56.0, -28.0, -88.0, -83.0), (28.0, 56.0, -88.0, -83.0),
    (-56.0, -28.0, 83.0, 88.0), (28.0, 56.0, 83.0, 88.0),
]
# and the two broken ones out towards the wreck
SPURS = [(-2.5, 2.5, -84.0, -48.0), (-2.5, 2.5, 48.0, 84.0)]
STILT = 5.0                 # a stilt hut's floor


# ================================================================ the sea
def _sea(isle: Isle) -> None:
    b = isle.b
    hx, hz = HALF
    m = b.margin
    whole = (-hx - m, hx + m, -hz - m, hz + m)
    for x0, x1, z0, z1 in carve(whole, [BASIN_R]):
        slab(b, (x0, x1, z0, z1), SHALLOW, 3.0, SAND_WET)
    slab(b, BASIN_R, BASIN, 3.0, "#c8b884")
    # the step down into the basin, round its edge
    x0, x1, z0, z1 = BASIN_R
    w = 4.0
    for xa, xb in ((x0, x0 + w), (x1 - w, x1)):
        b.box([(xa + xb) / 2.0, (BASIN + RING) / 2.0, 0.0], [w, RING - BASIN, z1 - z0], SAND_WET)
    for za, zb in ((z0, z0 + w), (z1 - w, z1)):
        b.box([0.0, (BASIN + RING) / 2.0, (za + zb) / 2.0], [x1 - x0 - 2 * w, RING - BASIN, w],
              SAND_WET)
    # the water over all of it, and the open sea beyond the reef's edge
    b.box([0.0, (BASIN + SEA_TOP) / 2.0, 0.0], [2 * hx, SEA_TOP - BASIN, 2 * hz], LAGOON,
          material="glass", alpha=0.5, collide=False)
    for xa, xb, za, zb in ((-hx - m - 300.0, -hx - m, -hz - m - 300.0, hz + m + 300.0),
                           (hx + m, hx + m + 300.0, -hz - m - 300.0, hz + m + 300.0),
                           (-hx - m, hx + m, hz + m, hz + m + 300.0),
                           (-hx - m, hx + m, -hz - m - 300.0, -hz - m)):
        b.box([(xa + xb) / 2.0, (SHALLOW - 6.0 + SEA_TOP) / 2.0, (za + zb) / 2.0],
              [xb - xa, SEA_TOP - SHALLOW + 6.0, zb - za], SEA, material="glass", alpha=0.6,
              collide=False)


def _edges(isle: Isle) -> None:
    """The reef's crest all the way round: a wall of rock the surf breaks
    on, too tall to climb out over."""
    b = isle.b
    rng = isle.rng
    hx, hz = HALF
    m = b.margin
    top = 5.0
    for sgn in (-1.0, 1.0):
        b.box([sgn * (hx + m / 2.0), (SHALLOW + top) / 2.0, 0.0], [m, top - SHALLOW, 2 * (hz + m)],
              ROCK)
        b.box([0.0, (SHALLOW + top) / 2.0, sgn * (hz + m / 2.0)], [2 * hx, top - SHALLOW, m], ROCK)
    for k in range(22):
        z = -hz - m + (k + 0.5) * 2 * (hz + m) / 22.0
        for sgn in (-1.0, 1.0):
            b.box([sgn * (hx + m / 2.0) + rng.uniform(-1.0, 1.0), top + 1.0 + (k % 3) * 0.5, z],
                  [m - 2.0 - (k % 2) * 0.6, 2.0 + (k % 3), 2 * (hz + m) / 22.0 - 2.0],
                  ROCK_LIGHT if k % 2 else ROCK)
    for k in range(18):
        x = -hx + (k + 0.5) * 2 * hx / 18.0
        for sgn in (-1.0, 1.0):
            b.box([x, top + 1.0 + (k % 3) * 0.5, sgn * (hz + m / 2.0) + rng.uniform(-1.0, 1.0)],
                  [2 * hx / 18.0 - 2.0, 2.0 + (k % 3), m - 2.0 - (k % 2) * 0.6],
                  ROCK if k % 2 else ROCK_LIGHT)
    skirt(b, hx, hz, "#c8b884", top=SHALLOW - 3.05)
    backdrop(b, "hills", -4.0, rng, sides=("z-", "z+"), colours=["#3f8a4a", "#4a9a54", "#3a7a42"],
             depth=180.0)


# ================================================================ the keys
def _key(isle: Isle, area: Tuple[float, float, float, float], colour: str = SAND) -> None:
    """A key: a block of sand standing out of the reef flat, with a strip
    of beach a step down all round it."""
    b = isle.b
    x0, x1, z0, z1 = area
    b.box([(x0 + x1) / 2.0, (SHALLOW + ISLE) / 2.0, (z0 + z1) / 2.0],
          [x1 - x0, ISLE - SHALLOW, z1 - z0], colour)
    w = 3.0
    for xa, xb in ((x0 - w, x0), (x1, x1 + w)):
        b.box([(xa + xb) / 2.0, (SHALLOW + BEACH) / 2.0, (z0 + z1) / 2.0],
              [w, BEACH - SHALLOW, z1 - z0 + 2 * w], SAND_WET)
    for za, zb in ((z0 - w, z0), (z1, z1 + w)):
        b.box([(x0 + x1) / 2.0, (SHALLOW + BEACH) / 2.0, (za + zb) / 2.0],
              [x1 - x0, BEACH - SHALLOW, w], SAND_WET)


def _walk(isle: Isle, area, broken: float = 0.0) -> None:
    """A boardwalk on posts over the flat; ``broken`` leaves its last
    stretch (at the high-z or low-z end, by sign) as a few planks."""
    b = isle.b
    x0, x1, z0, z1 = area
    along_x = (x1 - x0) > (z1 - z0)
    length = (x1 - x0) if along_x else (z1 - z0)
    stop = length - abs(broken)
    n = max(2, int(stop // 3.0))
    for k in range(n):
        a = k * stop / n
        c = a + stop / n - 0.2
        if broken < 0:
            a, c = length - c, length - a
        if along_x:
            b.box([x0 + (a + c) / 2.0, WALK - 0.2, (z0 + z1) / 2.0], [c - a, 0.4, z1 - z0],
                  PLANK if k % 2 else "#9a7a52")
        else:
            b.box([(x0 + x1) / 2.0, WALK - 0.2, z0 + (a + c) / 2.0], [x1 - x0, 0.4, c - a],
                  PLANK if k % 2 else "#9a7a52")
    # the bearers the planks lie on, and posts down to the flat
    span = (0.0, stop) if broken >= 0 else (length - stop, length)
    for side in (0.6, -0.6):
        if along_x:
            zc = z0 + 0.6 if side > 0 else z1 - 0.6
            b.box([x0 + (span[0] + span[1]) / 2.0, WALK - 0.65, zc], [span[1] - span[0], 0.5, 0.8],
                  TIMBER)
        else:
            xc = x0 + 0.6 if side > 0 else x1 - 0.6
            b.box([xc, WALK - 0.65, z0 + (span[0] + span[1]) / 2.0], [0.8, 0.5, span[1] - span[0]],
                  TIMBER)
    k = 0
    u = span[0] + 3.0
    while u < span[1] - 1.0:
        for side in (0, 1):
            if along_x:
                px, pz = x0 + u, (z0 + 0.6) if side == 0 else (z1 - 0.6)
            else:
                px, pz = (x0 + 0.6) if side == 0 else (x1 - 0.6), z0 + u
            b.cyl([px, (SHALLOW + WALK - 0.9) / 2.0, pz], [0.8, WALK - 0.9 - SHALLOW, 0.8], TIMBER)
            if k % 2 == 0:
                # a stub of post standing up at the edge to keep you on
                b.cyl([px, WALK + 0.8, pz], [0.6, 1.6, 0.6], TIMBER)
        u += 8.0
        k += 1
    if broken:
        # the planks that are left, out over the water where it gave way
        end = length - abs(broken) if broken > 0 else abs(broken)
        for k in range(3):
            u = end + (k + 0.5) * abs(broken) / 4.0 if broken > 0 else end - (k + 0.5) * abs(broken) / 4.0
            if along_x:
                b.box([x0 + u, SHALLOW + 0.1 + k * 0.05, (z0 + z1) / 2.0 + (k - 1) * 1.2],
                      [1.8, 0.2, 3.6], "#7a5a3a", collide=False, r=[0.0, 0.3 * (k - 1), 0.0])
            else:
                b.box([(x0 + x1) / 2.0 + (k - 1) * 1.2, SHALLOW + 0.1 + k * 0.05, z0 + u],
                      [3.6, 0.2, 1.8], "#7a5a3a", collide=False, r=[0.0, 0.3 * (k - 1), 0.0])


def _stilt_hut(isle: Isle, x: float, z: float, sgn: float, colour: str) -> None:
    """A hut up on stilts, a ladder-stair up to its porch, nets and floats
    hanging under it."""
    b = isle.b
    x0, x1 = sorted((x - 7.0, x + 7.0))
    area = (x0, x1, z - 6.0, z + 6.0)
    # the stilts and the platform the hut stands on (with a porch in front)
    for px in (x0 + 0.6, x1 - 0.6):
        for pz in (z - 5.4, z + 5.4, z + 9.4):
            b.cyl([px, (ISLE + STILT - 0.6) / 2.0, pz], [1.0, STILT - 0.6 - ISLE, 1.0], TIMBER)
    slab(b, (x0, x1, z - 6.0, z + 10.0), STILT, 0.6, PLANK)
    isle.hut(area, "z+", y=STILT, colour=colour, height=7.0)
    flight(b, "z", z + 18.0, z + 10.0, x - 2.2, x + 2.2, ISLE, STILT, TIMBER, fill=ISLE)
    # a rail round the porch, open where the stair arrives
    for xa, xb in ((x0, x - 2.2), (x + 2.2, x1)):
        b.box([(xa + xb) / 2.0, STILT + 1.0, z + 9.7], [xb - xa, 2.0, 0.6], TIMBER)
    for xs in (x0 + 0.3, x1 - 0.3):
        b.box([xs, STILT + 1.0, z + 8.0], [0.6, 2.0, 3.4], TIMBER)
    # floats hanging under it, a net
    for k in range(3):
        b.sphere([x0 + 3.0 + k * 4.0, STILT - 1.2, z - 2.0], [1.0, 1.0, 1.0],
                 ("#e85a3a", "#f4f0e8", "#3a8ae8")[k], collide=False)
        b.box([x0 + 3.0 + k * 4.0, STILT - 0.65, z - 2.0], [0.1, 0.5, 0.1], "#c8b890",
              collide=False)


def _clam(isle: Isle, x: float, z: float, y: float, s: float = 1.0, open_: bool = True) -> None:
    """A giant clam, half sunk in the sand, its shell agape on a pearl."""
    b = isle.b
    b.sphere([x, y + 0.6 * s, z], [5.0 * s, 2.4 * s, 4.0 * s], "#8a6ab8")
    b.sphere([x, y + 1.1 * s, z], [4.2 * s, 0.8 * s, 3.2 * s], "#f0c8d8", collide=False)
    if open_:
        b.sphere([x, y + 2.4 * s, z - 1.0 * s], [4.8 * s, 1.0 * s, 3.6 * s], "#7a5aa8",
                 collide=False, r=[-0.7, 0.0, 0.0])
    b.sphere([x, y + 1.6 * s, z + 0.3 * s], [1.0 * s, 1.0 * s, 1.0 * s], "#fff8f0",
             material="neon", collide=False)


def _coral(isle: Isle, x: float, z: float, y: float, n: int = 5) -> None:
    """A clump of coral on the flat: solid, so you wade round it."""
    b = isle.b
    rng = isle.rng
    for k in range(n):
        cx, cz = x + rng.uniform(-3.0, 3.0), z + rng.uniform(-3.0, 3.0)
        colour = rng.choice(CORAL)
        size = rng.uniform(1.0, 2.2)
        if k % 3 == 0:
            b.cone([cx, y + size * 0.9, cz], [size, size * 1.8, size], colour)
        elif k % 3 == 1:
            b.sphere([cx, y + size * 0.35, cz], [size * 1.4, size * 0.9, size * 1.4], colour)
        else:
            b.cyl([cx, y + size * 0.6, cz], [size * 0.6, size * 1.2, size * 0.6], colour)
            b.sphere([cx, y + size * 1.3, cz], [size * 1.1, size * 0.5, size * 1.1], colour)


def _keys(isle: Isle) -> None:
    b = isle.b
    rng = isle.rng
    for name, area in KEYS.items():
        _key(isle, area)
    for area in WALKS:
        _walk(isle, area)
    _walk(isle, SPURS[0], broken=10.0)
    _walk(isle, SPURS[1], broken=-10.0)
    # the west and east keys: a stilt hut, palms, fish racks, crates, a
    # beached boat, two X's
    for sgn in (-1.0, 1.0):
        def X(x: float, sgn: float = sgn) -> float:
            return sgn * x
        west = sgn < 0
        _stilt_hut(isle, X(94.0), -18.0, sgn, "#a8845a" if west else "#9a7a52")
        for x, z in ((104.0, -30.0), (88.0, 4.0), (106.0, 10.0), (84.0, 26.0), (100.0, 30.0),
                     (80.0, -28.0)):
            isle.palm(X(x), z, ISLE, rng.uniform(12.0, 17.0))
        # the fish racks: two posts with a pole across, fish hung off it
        for z in (12.0, 20.0):
            for dx in (-3.0, 3.0):
                b.cyl([X(96.0) + dx, ISLE + 2.0, z], [0.5, 4.0, 0.5], TIMBER)
            b.box([X(96.0), ISLE + 3.8, z], [6.0, 0.3, 0.3], TIMBER, collide=False)
            for k in range(4):
                b.box([X(96.0) - 2.0 + k * 1.3, ISLE + 3.0, z], [0.5, 1.4, 0.2], "#8a9aa8",
                      collide=False)
        isle.crates(X(84.0) - (3.8 if not west else 0.0), -12.0, ISLE, n=3)
        isle.barrel(X(80.0), 8.0, ISLE)
        isle.barrel(X(80.0), 11.0, ISLE)
        b.box([X(108.0), ISLE + 0.85, 22.0], [4.4, 1.7, 9.0], "#8a5a34")
        b.box([X(108.0), ISLE + 1.75, 22.0], [3.2, 0.1, 7.6], "#3a2a1a", collide=False)
        isle.torch(X(110.0), -24.0, ISLE)
        isle.torch(X(110.0), 24.0, ISLE)
        isle.flag(X(80.0), -32.0, ISLE, "#141414")
        isle.dig(X(102.0), ISLE, -4.0, "under the palms" if west else "the coconut grove")
        isle.dig(X(84.0), ISLE, 16.0, "behind the fish racks" if west else "by the racks")
        isle.loot(X(94.0), STILT + 0.4, -18.0, "any", "the stilt hut")
        isle.loot(X(88.0), ISLE, -30.0, "any", "the key")
        _coral(isle, X(66.0), -10.0, SHALLOW)
        _coral(isle, X(64.0), 18.0, SHALLOW, 4)
    # the corner keys: palms, a rock, a crate pile, an X or loot each
    for name, (x0, x1, z0, z1) in KEYS.items():
        if name not in ("nw", "ne", "sw", "se"):
            continue
        cx, cz = (x0 + x1) / 2.0, (z0 + z1) / 2.0
        sx = -1.0 if cx < 0 else 1.0
        sz = -1.0 if cz < 0 else 1.0
        isle.palm(cx + sx * 6.0, cz - sz * 4.0, ISLE, rng.uniform(12.0, 16.0))
        isle.palm(cx - sx * 5.0, cz + sz * 6.0, ISLE, rng.uniform(11.0, 15.0))
        isle.rock(cx + sx * 7.0, cz + sz * 5.0, 5.0, 4.0, 2.6, ISLE)
        isle.torch(cx - sx * 8.0, cz - sz * 7.0, ISLE)
        if sz < 0:
            isle.dig(cx - sx * 2.0, ISLE, cz, "the %s key" % ("north-west" if sx < 0 else "north-east"))
        else:
            isle.dig(cx - sx * 2.0, ISLE, cz, "the %s key" % ("south-west" if sx < 0 else "south-east"))
        isle.loot(cx + sx * 2.0, ISLE, cz + sz * 8.0, "any", "the little key")
        _coral(isle, cx, cz - sz * 22.0, SHALLOW)
    # the boardwalks' far ends carry a pouch or two
    isle.loot(-80.0, WALK, -50.0, "any", "the west boardwalk")
    isle.loot(80.0, WALK, 50.0, "any", "the east boardwalk")
    isle.loot(-42.0, WALK, 86.0, "any", "the south boardwalk")
    isle.loot(42.0, WALK, -86.0, "any", "the north boardwalk")


def _north(isle: Isle) -> None:
    """Lighthouse Rock: the lighthouse on its outcrop, the keeper's
    cottage, rocks round the shore."""
    b = isle.b
    rng = isle.rng
    x0, x1, z0, z1 = KEYS["north"]
    # the outcrop the lighthouse stands on, steps up its south face
    b.box([0.0, ISLE + 1.5, -104.0], [24.0, 3.0, 16.0], ROCK)
    flight(b, "z", -90.0, -96.0, -3.0, 3.0, ISLE, ISLE + 3.0, ROCK_DARK, fill=ISLE)
    top = lookout_tower(b, 0.0, -104.0, ISLE + 3.0, 26.0, "#f4f0e8", "#8a8478", core=8.0,
                        width=4.0, cap="#3a3a3a", start="z+", lantern="#fff4c0",
                        bands=["#f4f0e8", "#c8302a"])
    # the keeper's cottage beside it
    isle.hut((14.0, 26.0, -110.0, -100.0), "z+", ISLE, colour="#e8e0d0", roof="#4a5a6a",
             height=7.0)
    for x in (-24.0, -18.0, 20.0):
        isle.rock(x, -88.0 + rng.uniform(-2.0, 2.0), rng.uniform(4.0, 6.0), 4.0, rng.uniform(2.0, 3.0),
                  ISLE)
    isle.palm(-20.0, -100.0, ISLE, 14.0)
    isle.dig(-10.0, ISLE, -92.0, "the foot of the lighthouse")
    isle.loot(3.0, top, -104.0 - 6.4, "bar", "the lighthouse gallery")
    isle.loot(20.0, ISLE + 0.4, -105.0, "any", "the keeper's cottage")
    b.landmark(0.0, -104.0, "the lighthouse")


def _south(isle: Isle) -> None:
    """Clam Flats: giant clams on the sand, the fishing shack, nets."""
    b = isle.b
    rng = isle.rng
    for x, z, s in ((-16.0, 96.0, 1.0), (14.0, 98.0, 1.1), (-4.0, 108.0, 0.9), (20.0, 108.0, 0.8)):
        _clam(isle, x, z, ISLE, s)
        isle.loot(x, ISLE + 1.4 * s, z + 0.3 * s, "gem", "a giant clam")
    isle.hut((-26.0, -14.0, 102.0, 112.0), "z-", ISLE, colour="#b89a6a", roof="#8a6a3a",
             height=7.0)
    for k in range(3):
        b.cyl([6.0 + k * 4.0, ISLE + 2.0, 88.0], [0.5, 4.0, 0.5], TIMBER)
    net = b.box([10.0, ISLE + 3.0, 88.0], [8.4, 2.4, 0.2], "#c8c0a8", decal="netting")
    net["dw"] = 1
    for x in (-24.0, 24.0):
        isle.palm(x, 90.0, ISLE, rng.uniform(13.0, 17.0))
    isle.torch(-8.0, 88.0, ISLE)
    isle.dig(4.0, ISLE, 100.0, "the clam flats")
    b.landmark(0.0, 100.0, "the clam flats")
    # clams out on the flat too, under water
    for x, z in ((-34.0, 62.0), (34.0, -62.0)):
        _clam(isle, x, z, SHALLOW, 0.8)
        isle.loot(x, SHALLOW + 1.1, z + 0.24, "gem", "a clam on the reef")


# ================================================================ the wreck
def _wreck(isle: Isle) -> None:
    """The Leviathan: a man-of-war run aground in the basin and broken in
    two.  Its aft half is hollow -- the hold, reached through the break --
    and stairs in the break climb to both decks."""
    b = isle.b
    deck = 5.0
    hold = -1.4
    # ---- the fore half, solid to its deck, the forecastle on its bow
    b.box([0.0, (BASIN + deck) / 2.0, 13.0], [18.0, deck - BASIN, 18.0], HULL)
    b.box([0.0, (BASIN + deck) / 2.0, 24.5], [12.0, deck - BASIN, 5.0], HULL)
    b.box([0.0, (BASIN + deck) / 2.0, 28.5], [6.0, deck - BASIN, 3.0], HULL_DARK)
    b.box([0.0, (deck + 8.0) / 2.0, 19.0], [18.0, 3.0, 6.0], HULL)
    b.box([0.0, (deck + 8.0) / 2.0, 24.5], [12.0, 3.0, 5.0], HULL)
    b.box([0.0, (deck + 8.0) / 2.0, 28.5], [6.0, 3.0, 3.0], HULL)
    flight(b, "z", 11.0, 16.0, -2.0, 2.0, deck, 8.0, TIMBER, fill=deck)
    # ---- the aft half: the hull's sides and stern round the hold, the
    # deck over it
    for sgn in (-1.0, 1.0):
        b.box([sgn * 8.2, (BASIN + deck - 0.6) / 2.0, -18.0], [1.6, deck - 0.6 - BASIN, 24.0], HULL)
    b.box([0.0, (BASIN + deck - 0.6) / 2.0, -29.2], [14.8, deck - 0.6 - BASIN, 1.6], HULL)
    b.box([0.0, (BASIN + hold) / 2.0, -17.2], [14.8, hold - BASIN, 22.4], HULL_DARK)
    b.box([0.0, deck - 0.3, -18.0], [18.0, 0.6, 24.0], "#8a6a48")
    # the quarterdeck on the stern, stairs up to it
    b.box([0.0, (deck + 9.0) / 2.0, -25.0], [18.0, 4.0, 10.0], HULL)
    flight(b, "z", -14.0, -20.0, -2.0, 2.0, deck, 9.0, TIMBER, fill=deck)
    # ---- the break amidships: smashed down to the hold's floor, the sides
    # stove in to stumps, rubble piled up out of the basin into it
    b.box([0.0, (BASIN + hold) / 2.0, -1.0], [18.0, hold - BASIN, 10.0], HULL_DARK)
    for sgn in (-1.0, 1.0):
        for za, zb in ((-6.0, -4.0), (2.0, 4.0)):
            b.box([sgn * 8.2, (hold + 0.8) / 2.0, (za + zb) / 2.0], [1.6, 0.8 - hold, zb - za], HULL)
        b.box([sgn * 10.5, BASIN + 0.9, -1.0], [3.0, 1.8, 6.0], ROCK_DARK)
        b.box([sgn * 12.4, BASIN + 0.45, -1.0], [0.8, 0.9, 4.0], ROCK_DARK)
    # stairs in the break: up to the fore deck on one side, the aft on the other
    flight(b, "z", -4.0, 4.0, 3.0, 7.0, hold, deck, TIMBER, fill=hold)
    flight(b, "z", 2.0, -6.0, -7.0, -3.0, hold, deck, TIMBER, fill=hold)
    # ---- rails round the decks, open where the stairs arrive
    for sgn in (-1.0, 1.0):
        b.box([sgn * 8.6, deck + 1.0, 10.0], [0.8, 2.0, 12.0], HULL_DARK)
        b.box([sgn * 8.6, deck + 1.0, -13.0], [0.8, 2.0, 14.0], HULL_DARK)
        b.box([sgn * 8.6, 9.0 + 1.0, -25.0], [0.8, 2.0, 10.0], HULL_DARK)
        b.box([sgn * 8.6, 8.0 + 1.0, 19.0], [0.8, 2.0, 6.0], HULL_DARK)
    b.box([0.0, 9.0 + 1.0, -29.6], [16.4, 2.0, 0.8], HULL_DARK)
    # her paint: a stripe down each side, gun ports along the aft half,
    # gilt on the rails
    for sgn in (-1.0, 1.0):
        for z0, z1 in ((-30.0, -6.0), (4.0, 22.0)):
            b.box([sgn * 9.075, 1.6, (z0 + z1) / 2.0], [0.15, 0.8, z1 - z0], "#c8a040")
        for z in (-26.0, -22.0, -18.0, -14.0, -10.0):
            b.box([sgn * 9.06, 3.2, z], [0.12, 1.2, 1.4], "#141210")
        for z0, z1 in ((4.0, 16.0), (-20.0, -6.0)):
            b.box([sgn * 8.6, deck + 2.04, (z0 + z1) / 2.0], [0.9, 0.08, z1 - z0], TRIM,
                  material="metal", collide=False)
    # ---- inside the hold: cannons along the sides, barrels, gold, lamps on
    # the walls (there is no room to hang one over anybody's head)
    for z in (-24.0, -18.0, -12.0):
        for sgn in (-1.0, 1.0):
            b.box([sgn * 5.6, hold + 0.6, z], [2.4, 1.2, 2.6], "#5a3a22")
            b.cyl([sgn * 6.6, hold + 1.8, z], [1.0, 2.4, 1.0], IRON, material="metal",
                  collide=False, r=[0.0, 0.0, math.pi / 2.0])
    # (the gold and the barrels against the stern: the aisle between the
    # guns stays a body's width all the way back)
    for x in (-6.1, 6.1):
        isle.barrel(x, -27.1, hold)
    b.sphere([0.0, hold + 0.6, -26.6], [4.4, 1.4, 2.6], "#e8b830", material="metal")
    for z in (-21.0, -15.0, -9.0):
        for sgn in (-1.0, 1.0):
            b.box([sgn * 7.1, hold + 3.4, z], [0.6, 0.4, 0.8], IRON, material="metal")
            b.box([sgn * 7.1, hold + 4.1, z], [0.5, 1.0, 0.5], "#ffcf7a", material="neon")
    # ---- the masts: one standing amidships of the fore half with rags of
    # sail, the mizzen a stump, the main mast fallen across the break
    b.cyl([0.0, deck + 16.0, 10.0], [1.6, 32.0, 1.6], TIMBER)
    for k, yy in enumerate((14.0, 24.0)):
        b.cyl([0.0, deck + yy, 10.0], [0.6, 16.0 - k * 3.0, 0.6], TIMBER, collide=False,
              r=[0.0, 0.0, math.pi / 2.0])
        b.box([-2.0 + k * 1.5, deck + yy - 3.4, 10.75], [9.0 - k * 2.0, 5.6, 0.3], "#c8c0a8",
              collide=False)
    b.cyl([0.0, 9.0 + 3.5, -24.0], [1.4, 7.0, 1.4], TIMBER)
    b.cone([0.0, 9.0 + 7.6, -24.0], [1.4, 1.2, 1.4], "#5a4a32")
    # a yard that came down with it, lying on the bottom by the bow
    b.cyl([16.0, BASIN + 0.5, 18.0], [1.0, 14.0, 1.0], TIMBER, collide=False,
          r=[0.0, 0.4, math.pi / 2.0])
    # the figurehead and the name on the stern
    b.sphere([0.0, deck + 1.0, 30.6], [1.8, 3.0, 1.6], "#5a9a8a", collide=False)
    b.box([0.0, deck - 1.4, -30.1], [12.0, 1.4, 0.2], "#2a3a4a", collide=False,
          decal="t~THE LEVIATHAN~#2a3a4a~#e8d8a8~8.57")
    # barnacles and weed up its sides
    for z in (-20.0, -8.0, 6.0, 18.0):
        for sgn in (-1.0, 1.0):
            b.box([sgn * 9.06, BASIN + 2.0, z], [0.12, 3.0, 4.0], "#3a6a4a")
    # the idol's altar on the forecastle, gold where the hold's lamps shine
    isle.idol(0.0, 8.0, 22.0)
    # marks: loot in the hold and on the decks
    isle.loot(-3.0, hold, -22.0, "gem", "the Leviathan's hold")
    isle.loot(3.0, hold, -16.0, "bar", "the Leviathan's hold")
    isle.loot(0.0, hold, -10.0, "any", "the Leviathan's hold")
    isle.loot(5.0, 9.0, -25.0, "any", "the Leviathan's quarterdeck")
    isle.dig(0.0, hold, -1.0, "the break in the Leviathan")
    # the kraken comes up round it
    for x, z in ((-18.0, -24.0), (18.0, -24.0), (-18.0, 20.0), (18.0, 20.0), (0.0, -38.0),
                 (0.0, 38.0)):
        b.mark("tentacle", x, BASIN, z)
    b.landmark(0.0, 0.0, "the Leviathan")


# ================================================================ meta
def _meta(isle: Isle) -> None:
    b = isle.b
    for x, z, name in ((-94.0, 0.0, "Driftwood Key"), (94.0, 0.0, "Coconut Key"),
                       (-70.0, -78.0, "the north-west key"), (70.0, -78.0, "the north-east key"),
                       (-70.0, 78.0, "the south-west key"), (70.0, 78.0, "the south-east key"),
                       (-SHIP_X, 0.0, "the Scarlet Queen"), (SHIP_X, 0.0, "the Blue Marlin")):
        b.landmark(x, z, name)
    b.camera(0.0, 50.0, 100.0, 0.0, 0.0, 0.0)
    b.camera(-140.0, 40.0, -90.0, -40.0, 0.0, 0.0)
    b.camera(140.0, 40.0, 90.0, 40.0, 0.0, 0.0)
    b.camera(24.0, 16.0, -6.0, 0.0, 2.0, -16.0)
    b.extra.update({"twist": "kraken", "water": SEA_TOP, "kraken_every": [55.0, 75.0],
                    "kraken_for": 30.0, "warn": 5.0})


def build(b: ArenaArea) -> None:
    rng = random.Random(7172)
    isle = Isle(b, rng)
    _sea(isle)
    _edges(isle)
    _keys(isle)
    _north(isle)
    _south(isle)
    _wreck(isle)
    galleon(isle, "red", 0.0)
    galleon(isle, "blue", 0.0)
    _meta(isle)
