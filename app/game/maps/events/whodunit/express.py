"""The Midnight Express -- a sleeper train on the mountain line, at night.

The train runs along x, the locomotive at the +x end::

    x -148 ... -136 | -136 ...... -96 | -94 ... -54 | -52 ... -12 | -10 ...... 30 |
      rear platform   OBSERVATION CAR   SLEEPER B     SLEEPER A     LOUNGE CAR
    | 32 ..... 72 | 74 ....... 114 | 116 .. 132 | 134 ......... 176
      DINING CAR    BAGGAGE CAR      the tender   the locomotive (cab, boiler)

Every car has a door in each end, a little off its middle (the side
corridor of the sleepers runs along z 0.8 .. 4.8), and the gangways between
them are short covered passages.  The roofs are walkable: up the stair on
the rear platform, or up the coal in the tender to the cab roof -- but a
roof is no place to be when the train goes into a tunnel.  Off the side of
the train is off the train: the rules take anybody who ends up below the
cars (``fall_y``).

The train stands still in the map; the client streams the mountainside
past it (the poles, the pines, the drifts) and draws the tunnels.
"""
from __future__ import annotations

import random
from typing import List, Tuple

from ..kit import ArenaArea, backdrop, flight, letters, rect, slab, strip_light
from ..prop_panic import furniture as fx
from ..prop_panic.catalogue import B, BLACK, BRASS, C, GOLD, K, R, S, WHITE, WOOD_DARK, place, stamp
from ..prop_panic.rooms import covering, interior, openings, partition
from .common import candelabra, hang, rails, room, stair

HALF = (180.0, 28.0)
SKY = {"top": "#0a1020", "horizon": "#2a3450", "sun": [0.3, 0.6, -0.4],
       "clouds": 0.3, "tint": "#c8d0ff"}
AMBIENT = "#5a6488"
GROUND = "#d8e0ec"
FOG = 600.0

FLOOR, CEIL, ROOF = 8.0, 17.0, 17.6
W, T = 6.0, 0.6
IN = W - T                         # the cars' inside, either side of the middle
DOOR = (0.8, 4.8)                  # the end doors (z)
HEAD = 14.0
SILL, TOP = 11.0, 15.2
PAINT_TRIM = "#c8a040"
BODY = "#3a1a2a"                   # the carriages' livery
BODY_LINE = "#c8a040"

CARS = {
    "observation": (-136.0, -96.0),
    "sleeper_b": (-94.0, -54.0),
    "sleeper_a": (-52.0, -12.0),
    "lounge": (-10.0, 30.0),
    "dining": (32.0, 72.0),
    "baggage": (74.0, 114.0),
}
TENDER = (116.0, 132.0)
CAB = (134.0, 146.0)
BOILER = (146.0, 176.0)
PLATFORM = (-148.0, -136.0)


# ================================================================ the cars
def _windows(x0: float, x1: float, every: float = 6.0, skip: Tuple[float, float] = (0.0, 0.0)
             ) -> List[Tuple[float, float, float, float]]:
    out = []
    x = x0 + 4.0
    while x + 3.4 < x1 - 3.0:
        if not (skip[0] < x + 3.4 and x < skip[1]):
            out.append((x, x + 3.4, SILL, TOP))
        x += every
    return out


def _car(b: ArenaArea, x0: float, x1: float, inside: str, floor: str, decal: str = "",
         side_holes: Tuple[list, list] = (None, None), front: bool = True, back: bool = True) -> None:
    """A carriage: floor, side walls with windows, end walls with their
    doors, roof, the underframe and the bogies, and its paint inside."""
    south = side_holes[0] if side_holes[0] is not None else _windows(x0, x1)
    north = side_holes[1] if side_holes[1] is not None else _windows(x0, x1)
    slab(b, rect(x0, x1, -W, W), FLOOR, 0.6, "#2a2420")
    openings(b, "x", -W + T / 2.0, T, x0, x1, FLOOR, CEIL, BODY, south, glass=True)
    openings(b, "x", W - T / 2.0, T, x0, x1, FLOOR, CEIL, BODY, north, glass=True)
    door = [(DOOR[0], DOOR[1], FLOOR - 1.0, HEAD)]
    openings(b, "z", x0 + T / 2.0, T, -IN, IN, FLOOR, CEIL, BODY, door if back else [])
    openings(b, "z", x1 - T / 2.0, T, -IN, IN, FLOOR, CEIL, BODY, door if front else [])
    # the roof, its lantern ridge, the gold line along the sides
    slab(b, rect(x0 - 0.3, x1 + 0.3, -W - 0.3, W + 0.3), ROOF, ROOF - CEIL, "#34343c")
    slab(b, rect(x0 + 1.0, x1 - 1.0, -3.4, 3.4), ROOF + 0.4, 0.4, "#2a2a30")
    # torpedo ventilators along the ridge (low enough to step over)
    x = x0 + 5.0
    while x < x1 - 4.0:
        b.cyl([x, ROOF + 0.7, 0.0], [1.0, 0.6, 1.0], "#4a4a52", material="metal")
        b.sphere([x, ROOF + 1.0, 0.0], [1.2, 0.5, 1.2], "#4a4a52", material="metal", collide=False)
        x += 8.0
    for z in (-W - 0.06, W + 0.06):
        b.box([(x0 + x1) / 2.0, 9.4, z], [x1 - x0, 0.3, 0.12], BODY_LINE, collide=False)
        b.box([(x0 + x1) / 2.0, 16.2, z], [x1 - x0, 0.3, 0.12], BODY_LINE, collide=False)
    # underframe and bogies on the rails
    b.box([(x0 + x1) / 2.0, 6.6, 0.0], [x1 - x0 - 4.0, 1.6, 8.0], "#1a1a1e")
    for bx in (x0 + 6.0, x1 - 6.0):
        b.box([bx, 5.2, 0.0], [7.0, 1.2, 6.0], "#2a2a2e", material="metal")
        for dx in (-2.2, 2.2):
            for z in (-3.2, 3.2):
                b.cyl([bx + dx, 5.2, z], [2.6, 0.5, 2.6], "#3a3a40", r=[1.5708, 0.0, 0.0],
                      material="metal")
    holes_s = [(a, c, s, t) for a, c, s, t in south]
    holes_n = [(a, c, s, t) for a, c, s, t in north]
    end = [(DOOR[0] - 0.5, DOOR[1] + 0.5, FLOOR - 1.0, HEAD + 0.5)]
    interior(b, (x0 + T, x1 - T, -IN, IN), FLOOR, CEIL, inside,
             {"z-": holes_s, "z+": holes_n, "x-": end if back else [], "x+": end if front else []},
             floor=floor, floor_decal=decal)


def _gangway(b: ArenaArea, x0: float, x1: float) -> None:
    """The covered passage between two cars' end doors."""
    a, c = DOOR[0] - 0.6, DOOR[1] + 0.6
    slab(b, rect(x0, x1, a, c), FLOOR, 0.6, "#2a2420")
    b.box([(x0 + x1) / 2.0, (FLOOR + HEAD) / 2.0, a + 0.3], [x1 - x0, HEAD - FLOOR, 0.6], "#1a1a1e")
    b.box([(x0 + x1) / 2.0, (FLOOR + HEAD) / 2.0, c - 0.3], [x1 - x0, HEAD - FLOOR, 0.6], "#1a1a1e")
    slab(b, rect(x0, x1, a, c), HEAD + 0.6, 0.6, "#1a1a1e")
    covering(b, rect(x0, x1, DOOR[0], DOOR[1]), FLOOR, "#4a3a30")


# ============================================================ the furniture
def _observation(b: ArenaArea) -> None:
    x0, x1 = CARS["observation"]
    tall = [(x, x + 6.0, 9.6, 16.2) for x in range(int(x0) + 3, int(x1) - 8, 8)]
    _car(b, x0, x1, "#e8dcc0", "#5a2a2a", side_holes=(tall, tall))
    y = FLOOR
    for x in (-130.0, -122.0, -114.0, -106.0):
        place(b, "armchair", x, -3.6, y, 2, hide=False)
        place(b, "armchair", x, 3.6, y, 0, hide=False)
    for x in (-126.0, -110.0):
        place(b, "side_table", x, -3.8, y, 0, hide=False)
        place(b, "potted_plant", x, 3.6, y, 0, hide=False)
    stamp(b, fx.bookcase(6.0, 7.6, 1.6, WOOD_DARK, seed=21), x0 + T + 0.9, -2.0, y, 1)
    place(b, "globe", -101.0, -3.6, y, 0, hide=False)
    for x in (-128.0, -116.0, -104.0):
        strip_light(b, x, 0.0, CEIL, 5.0, "x", "#ffe8b8", 1.0)
    # the open rear platform: railings, a lamp, the stair up to the roof
    px0, px1 = PLATFORM
    slab(b, rect(px0, px1, -W, W), FLOOR, 0.6, "#2a2420")
    b.box([(px0 + px1) / 2.0, 6.6, 0.0], [px1 - px0 - 2.0, 1.6, 8.0], "#1a1a1e")
    # the railing: a panel below, a brass rail on posts above, see-through
    # between them but too low a gap for anybody to slip through
    for z in (-W + 0.2, W - 0.2):
        b.box([(px0 + 0.4 + px1) / 2.0, FLOOR + 0.7, z], [px1 - px0 - 0.4, 1.4, 0.4], BODY)
        b.box([(px0 + 0.4 + px1) / 2.0, FLOOR + 3.45, z], [px1 - px0 - 0.4, 0.3, 0.4], BRASS,
              material="metal")
        x = px0 + 1.4
        while x < px1 - 0.5:
            b.box([x, FLOOR + 2.35, z], [0.2, 1.9, 0.2], BRASS, material="metal")
            x += 1.6
    b.box([px0 + 0.2, FLOOR + 0.7, 0.0], [0.4, 1.4, 2 * W], BODY)
    b.box([px0 + 0.2, FLOOR + 3.45, 0.0], [0.4, 0.3, 2 * W], BRASS, material="metal")
    for z in (-4.4, -2.8, -1.2, 1.2, 2.8, 4.4):
        b.box([px0 + 0.2, FLOOR + 2.35, z], [0.2, 1.9, 0.2], BRASS, material="metal")
    # the stair runs up the side away from the car's door, and stops short
    # of the roof's overhang so its top tread meets the roof edge
    flight(b, "x", px0 + 0.4, px1 - 0.35, -5.4, -1.2, FLOOR, ROOF, "#4a3a30", fill=FLOOR)
    b.box([px0 + 1.2, FLOOR + 6.0, 3.6], [0.6, 12.0, 0.6], "#2a2a2a")
    b.box([px0 + 1.2, FLOOR + 12.6, 3.6], [1.2, 1.2, 1.2], "#c82a2a", material="neon")
    # the drumhead on the rail, lit from inside
    b.cyl([px0 - 0.06, FLOOR + 2.0, 0.0], [3.0, 0.12, 3.0], BODY_LINE, r=[0.0, 0.0, 1.5708],
          material="metal", collide=False)
    b.cyl([px0 - 0.16, FLOOR + 2.0, 0.0], [2.4, 0.08, 2.4], "#fff0c8", r=[0.0, 0.0, 1.5708],
          material="neon", collide=False)


def _sleeper(b: ArenaArea, key: str, first: bool) -> None:
    x0, x1 = CARS[key]
    n = 6
    span = (x1 - x0 - 2 * T) / n
    corridor = _windows(x0, x1)
    berths = [(x0 + T + span * k + 1.4, x0 + T + span * k + span - 1.4, SILL, TOP) for k in range(n)]
    _car(b, x0, x1, "#e8dcc0", "#7a2a2a", side_holes=(berths, corridor))
    y = FLOOR
    # the corridor partition with a door into every compartment
    doors = []
    for k in range(n):
        mid = x0 + T + span * (k + 0.5)
        doors.append((mid - 2.2, mid + 2.2, HEAD))
    partition(b, "x", 0.5, x0 + T, x1 - T, FLOOR, CEIL, "#8a5a3a", doors, trim_colour=PAINT_TRIM)
    for k in range(1, n):
        x = x0 + T + span * k
        b.box([x, (FLOOR + CEIL) / 2.0, (-IN + 0.2) / 2.0], [0.6, CEIL - FLOOR, IN + 0.2], "#8a5a3a")
    colours = ["#4a6a8a", "#7a3a4a", "#3a6a4a"] if first else ["#6a6a7a", "#5a5a4a", "#6a4a3a"]
    for k in range(n):
        lo = x0 + T + span * k + (0.3 if k else 0.0)
        hi = x0 + T + span * (k + 1) - (0.3 if k < n - 1 else 0.0)
        mid = (lo + hi) / 2.0
        # the berth along the outer wall, a little table under the window, a case
        stamp(b, [B(0.0, 0.0, 0.0, hi - lo - 0.4, 2.0, 2.6, WOOD_DARK),
                  R(0.0, 2.0, 0.0, hi - lo - 0.6, 0.6, 2.4, colours[k % 3]),
                  R(-(hi - lo) / 2.0 + 1.0, 2.6, 0.0, 1.2, 0.5, 2.0, WHITE)],
              mid, -IN + 1.4, y)
        if first:
            stamp(b, [B(0.0, 6.4, 0.0, hi - lo - 0.4, 0.4, 2.4, WOOD_DARK),
                      R(0.0, 6.8, 0.0, hi - lo - 0.6, 0.5, 2.2, colours[(k + 1) % 3])],
                  mid, -IN + 1.3, y)
        # the luggage on the foot of the bed, out of the way of the door
        place(b, "hatbox" if k % 2 else "treasure_chest", hi - 1.6, -IN + 1.4, y + 2.6, 0,
              hide=False)
        hang(b, [C(0.0, -0.6, 0.0, 0.1, 0.6, 0.1, BLACK, ghost=True),
                 S(0.0, -1.0, 0.0, 0.7, 0.6, 0.7, "#ffe2a8", m="neon", ghost=True)], mid, CEIL, -2.6)
    for k in range(4):
        strip_light(b, x0 + 5.0 + k * (x1 - x0 - 10.0) / 3.0, 3.0, CEIL, 3.0, "x", "#ffe8b8", 0.8)
    stamp(b, fx.rug(x1 - x0 - 2 * T - 0.4, 3.2, "#7a2a2a", border=PAINT_TRIM), (x0 + x1) / 2.0, 2.9,
          y)


def _lounge(b: ArenaArea) -> None:
    x0, x1 = CARS["lounge"]
    _car(b, x0, x1, "#2a4a3a", "#6a4a2a", "planks")
    y = FLOOR
    # the bar at the back end, sofas, the upright piano, a card table
    # (the bar stops short of the back door, which the corridor lines up on)
    stamp(b, fx.counter(4.8, 2.4, "#5a3a24", "#2a1a14", "#6a4a2a"), x0 + T + 1.3, -3.0, y, 1)
    for k, c in enumerate(("#c8a040", "#3a8a5a", "#c84a3a", "#6a8ac8")):
        stamp(b, [C(0.0, 0.0, 0.0, 0.5, 1.4, 0.5, c, m="glass")], x0 + T + 0.7, -4.6 + k * 1.1,
              y + 3.2)
    for x in (-2.0, 12.0):
        stamp(b, fx.sofa("#7a2a3a", 8.0, 3.4), x, -IN + 1.8, y, 0)
    stamp(b, fx.table(4.0, 2.4, WOOD_DARK, WOOD_DARK, h=2.0), 5.0, -1.2, y)
    stamp(b, [B(0.0, 0.0, 0.0, 6.0, 5.0, 2.2, BLACK), B(0.0, 5.0, 0.0, 6.4, 0.3, 2.4, BLACK),
              B(0.0, 2.6, 1.2, 5.0, 0.3, 0.6, WHITE), B(0.0, 0.0, 2.6, 3.0, 1.6, 1.2, WOOD_DARK)],
          22.0, IN - 1.2, y, 2)
    stamp(b, fx.table(3.6, 3.6, "#2a5a3a", WOOD_DARK), 22.0, -2.4, y)
    for dx, q in ((-2.6, 1), (2.6, 3)):
        place(b, "dining_chair", 22.0 + dx, -2.4, y, q, hide=False)
    place(b, "floor_lamp", x1 - T - 1.0, -IN + 1.0, y, 0, hide=False)
    place(b, "potted_plant", x1 - T - 1.2, IN - 1.2, y, 0, hide=False)
    for x in (-2.0, 10.0, 22.0):
        hang(b, [C(0.0, -0.8, 0.0, 0.1, 0.8, 0.1, BLACK, ghost=True),
                 S(0.0, -1.2, 0.0, 2.2, 0.5, 2.2, GOLD, m="metal", ghost=True),
                 S(0.0, -1.5, 0.0, 1.2, 0.5, 1.2, "#ffe2a8", m="neon", ghost=True)], x, CEIL, 0.0)


def _dining(b: ArenaArea) -> None:
    x0, x1 = CARS["dining"]
    _car(b, x0, x1, "#e8dcc0", "#5a2a2a")
    y = FLOOR
    galley = x1 - 9.0
    partition(b, "z", galley, -IN, IN, FLOOR, CEIL, "#8a5a3a", [(DOOR[0], DOOR[1], HEAD)],
              trim_colour=PAINT_TRIM)
    # tables for four by the windows on the south side, two by the north
    for k, x in enumerate((36.5, 44.0, 51.5, 59.0)):
        stamp(b, fx.table(3.6, 3.0, WOOD_DARK, WOOD_DARK, cloth=WHITE), x, -IN + 1.7, y)
        for dx, q in ((-2.4, 1), (2.4, 3)):
            place(b, "dining_chair", x + dx, -IN + 1.7, y, q, hide=False)
        stamp(b, [C(0.0, 0.0, 0.0, 0.5, 1.2, 0.5, BRASS, m="metal"),
                  K(0.0, 1.2, 0.0, 1.2, 0.8, 1.2, "#f2e8c8"),
                  S(0.0, 1.0, 0.0, 0.5, 0.4, 0.5, "#ffe2a8", m="neon", ghost=True)], x, -IN + 1.4, y + 3.0)
    for x in (40.0, 55.0):
        stamp(b, fx.table(3.0, 2.0, WOOD_DARK, WOOD_DARK, cloth=WHITE), x, IN - 1.1, y)
        place(b, "dining_chair", x - 2.2, IN - 1.1, y, 1, hide=False)
        place(b, "dining_chair", x + 2.2, IN - 1.1, y, 3, hide=False)
        stamp(b, candelabra(), x, IN - 1.1, y + 3.0)
    # the galley: the counter and the range along the south wall, so the
    # way through from door to door stays clear; plates on a rack overhead
    stamp(b, fx.counter(4.4, 2.4), galley + 0.5 + 2.2, -IN + 1.3, y, 0)
    stamp(b, fx.stove(3.2, 2.4), x1 - T - 0.1 - 1.6, -IN + 1.3, y, 0)
    place(b, "cheese_wheel", galley + 1.6, -IN + 1.3, y + 3.2, 0, hide=False)
    place(b, "teapot", galley + 3.8, -IN + 1.3, y + 3.2, 0, hide=False)
    b.box([(galley + x1) / 2.0, FLOOR + 6.6, IN - 0.4], [x1 - galley - 2.0, 0.3, 0.8], WOOD_DARK)
    for k in range(6):
        b.cyl([galley + 1.6 + k * 1.1, FLOOR + 7.3, IN - 0.4], [1.0, 0.1, 1.0], WHITE,
              r=[1.5708, 0.0, 0.0], collide=False)
    for x in (38.0, 48.0, 58.0):
        strip_light(b, x, 0.0, CEIL, 5.0, "x", "#fff0c8", 0.8)
    strip_light(b, (galley + x1) / 2.0, 0.0, CEIL, 4.0, "x", "#ffffff", 0.8)


def _baggage(b: ArenaArea) -> None:
    x0, x1 = CARS["baggage"]
    side = [(90.0, 98.0, FLOOR - 1.0, HEAD), (78.0, 81.0, SILL, TOP), (106.0, 109.0, SILL, TOP)]
    _car(b, x0, x1, "#6a5a44", "#5a4a3a", "planks", side_holes=(side, side))
    y = FLOOR
    # the sliding doors stand open: a painted edge at each
    for z in (-IN + 1.0, IN - 1.0):
        b.box([94.0, y + 0.02, z], [8.0, 0.04, 2.0], "#f2b01e", collide=False, decal="hazard")
    # crates, trunks, mail sacks, the safe: mostly along the south side, so
    # there is always a way down the car from one end door to the other
    for x, z, h in ((77.8, -3.6, 2), (81.4, -3.6, 1), (84.0, 3.6, 2), (105.0, 3.6, 1),
                    (108.0, -3.6, 1)):
        for k in range(h):
            stamp(b, [B(0.0, 0.0, 0.0, 3.4, 3.4, 3.4, "#8a6a3a"),
                      B(0.0, 1.5, 1.72, 3.0, 0.4, 0.06, "#5a4a2a")], x, z, y + k * 3.4, k)
    place(b, "treasure_chest", 85.4, -3.8, y, 0, hide=False)
    place(b, "hatbox", 102.6, -3.8, y, 0, hide=False)
    place(b, "birdcage", 104.6, -3.8, y, 0, hide=False)
    for x, z in ((88.2, -3.4), (100.0, -3.4), (101.0, 3.8)):
        stamp(b, [R(0.0, 0.0, 0.0, 2.4, 1.6, 1.8, "#a89a7a")], x, z, y)
    stamp(b, [B(0.0, 0.0, 0.0, 3.0, 4.0, 2.6, "#3a3a3a", m="metal"),
              C(0.0, 2.0, 1.36, 0.9, 0.12, 0.9, "#c8ccd4", m="metal", turn=0)], 111.8, -3.6, y, 0)
    for x in (80.0, 94.0, 106.0):
        hang(b, [C(0.0, -1.0, 0.0, 0.1, 1.0, 0.1, BLACK, ghost=True),
                 S(0.0, -1.4, 0.0, 0.8, 0.8, 0.8, "#ffb35a", m="neon", ghost=True)], x, CEIL, 0.0)


def _tender(b: ArenaArea) -> None:
    """The coal bunker: a walkway along its north side from the baggage car
    to the footplate, the coal heaped in steps along the south side, up to
    the height of the cab roof."""
    x0, x1 = TENDER
    slab(b, rect(x0, x1, -W, W), FLOOR, 0.6, "#1a1a1e")
    b.box([(x0 + x1) / 2.0, 6.6, 0.0], [x1 - x0 - 2.0, 1.6, 8.0], "#1a1a1e")
    # the rear wall (with its door), the low sides of the bunker
    openings(b, "z", x0 + T / 2.0, T, -W, W, FLOOR, CEIL, "#1a1a1e",
             [(DOOR[0], DOOR[1], FLOOR - 1.0, HEAD)])
    for z in (-W + T / 2.0, W - T / 2.0):
        b.box([(x0 + T + x1) / 2.0, FLOOR + 2.0, z], [x1 - x0 - T, 4.0, T], "#1a1a1e")
    # the coal, from a step in from the rear wall up to the front
    flight(b, "x", x0 + T + 1.4, x1, -IN, -0.6, FLOOR, ROOF, "#1a1a1a", fill=FLOOR)
    for x, z, k in ((121.5, -3.6, 1), (124.6, -1.8, 2), (127.7, -4.0, 3)):
        stamp(b, [S(0.0, 0.0, 0.0, 1.6, 0.8, 1.4, "#2a2a2a", ghost=True)], x, z,
              FLOOR + 1.92 * k - 0.3)
    b.box([x0 + T + 0.2, FLOOR + 0.5, -3.0], [0.4, 1.0, 4.8], "#3a3a3e", material="metal")
    covering(b, rect(x0 + T, x1, -0.6, IN), FLOOR, "#2a2a2e")
    slab(b, rect(x1, CAB[0], -W, W), FLOOR, 0.6, "#2a2a2e", material="metal")


def _locomotive(b: ArenaArea) -> None:
    """A streamlined engine of the thirties: the cab, then a deep casing
    over the boiler whose flat top is a ledge you can drop onto from the cab
    roof (and climb back from), the boiler, dome and chimney on top of it,
    and a stepped nose with the headlamp."""
    x0, x1 = CAB
    bx0, bx1 = BOILER
    deck = FLOOR + 5.4                              # the casing's top
    slab(b, rect(x0, bx1, -W, W), FLOOR, 0.6, "#1a1a1e")
    b.box([(x0 + bx1) / 2.0, 6.0, 0.0], [bx1 - x0 - 2.0, 2.8, 8.0], "#1a1a1e")
    # the cab: two sides with windows, open to the tender; its front wall is
    # the backhead, with a window either side of the boiler over the casing
    for z in (-W + T / 2.0, W - T / 2.0):
        openings(b, "x", z, T, x0, x1, FLOOR, CEIL, "#2a3a2a", [(x0 + 3.0, x1 - 3.0, 11.6, 15.4)],
                 glass=True)
    openings(b, "z", x1 - T / 2.0, T, -IN, IN, FLOOR, CEIL, "#2a2a2e",
             [(-5.0, -2.8, deck + 0.6, 16.2), (2.8, 5.0, deck + 0.6, 16.2)], glass=True)
    slab(b, rect(x0 - 0.3, x1 + 0.3, -W - 0.3, W + 0.3), ROOF, ROOF - CEIL, "#2a3a2a")
    face = x1 - T - 0.05
    b.box([face, FLOOR + 3.0, 0.0], [0.1, 2.4, 3.0], "#ff7a1a", material="neon", collide=False)
    for z in (-1.8, -0.6, 0.6, 1.8):
        b.cyl([face, FLOOR + 6.6, z], [1.0, 0.12, 1.0], "#f2f0ea", r=[0.0, 0.0, 1.5708],
              collide=False)
    b.box([face, FLOOR + 5.2, 0.0], [0.1, 0.24, 4.6], BRASS, material="metal", collide=False)
    stamp(b, [B(0.0, 0.0, 0.0, 1.6, 2.0, 1.6, "#3a2a1a"), R(0.0, 2.0, 0.0, 1.6, 0.4, 1.6, "#5a2a2a")],
          x0 + 3.0, -IN + 1.2, FLOOR)
    covering(b, rect(x0, x1 - T, -IN, IN), FLOOR, "#3a3a3e")
    # the casing, and the stepped nose
    nose = bx1 - 6.0
    b.box([(x1 + nose) / 2.0, (FLOOR + deck) / 2.0, 0.0], [nose - x1, deck - FLOOR, 2 * W], "#1e2a22",
          material="metal")
    for k, (a, c, top) in enumerate(((nose, nose + 2.4, deck - 1.2), (nose + 2.4, nose + 4.4, deck - 2.4),
                                     (nose + 4.4, bx1, deck - 3.6))):
        b.box([(a + c) / 2.0, (FLOOR + top) / 2.0, 0.0], [c - a, top - FLOOR, 2 * W - 0.6 * (k + 1)],
              "#1e2a22", material="metal")
    for z in (-W - 0.06, W + 0.06):
        for k, y in enumerate((FLOOR + 1.4, FLOOR + 2.6, FLOOR + 3.8)):
            b.box([(x1 + nose) / 2.0 + 1.0 + k, y, z], [nose - x1 - 2.0 - 2 * k, 0.3, 0.12], BRASS,
                  material="metal", collide=False)
    b.box([bx1 + 0.06, FLOOR + 1.0, 0.0], [0.12, 1.2, 2.4], "#fff4c8", material="neon",
          collide=False)
    b.box([bx1 + 1.0, 6.6, 0.0], [2.0, 2.8, 2 * W - 1.8], "#8a1a1a")
    # the boiler, the dome and the chimney on top of the casing
    b.cyl([(x1 + nose) / 2.0, deck + 2.2, 0.0], [4.4, nose - x1, 4.4], "#2a3a30", r=[0.0, 0.0, 1.5708],
          material="metal")
    for x in (x1 + 6.0, x1 + 14.0):
        b.cyl([x, deck + 2.2, 0.0], [4.6, 0.4, 4.6], BRASS, r=[0.0, 0.0, 1.5708], material="metal",
              collide=False)
    b.sphere([x1 + 10.0, deck + 4.4, 0.0], [2.4, 1.8, 2.4], BRASS, material="metal")
    b.cyl([nose - 3.0, deck + 5.2, 0.0], [2.2, 2.4, 2.2], "#1a1a1e")
    b.cyl([nose - 3.0, deck + 6.6, 0.0], [2.8, 0.6, 2.8], "#1a1a1e")
    # the driving wheels and their rods
    for x in (bx0 + 4.0, bx0 + 11.0, bx0 + 18.0):
        for z in (-W - 0.3, W + 0.3):
            b.cyl([x, 5.4, z], [6.0, 0.6, 6.0], "#8a1a1a", r=[1.5708, 0.0, 0.0])
    # the cylinders ahead of the drivers, and the rods from them to the wheels
    for z in (-W - 0.3, W + 0.3):
        b.box([bx0 + 25.0, 5.9, z], [4.0, 3.0, 1.4], "#1e2a22", material="metal")
    for z in (-W - 0.7, W + 0.7):
        b.box([bx0 + 14.0, 5.4, z + (0.05 if z < 0 else -0.05)], [21.0, 0.4, 0.2], "#c8ccd4",
              material="metal", collide=False)
        for x in (bx0 + 4.0, bx0 + 11.0, bx0 + 18.0):
            b.cyl([x, 5.4, z - (0.1 if z < 0 else -0.1)], [0.8, 0.2, 0.8], "#c8ccd4",
                  r=[1.5708, 0.0, 0.0], material="metal", collide=False)
    letters(b, (x0 + x1) / 2.0, 10.2, W + 0.02, "MIDNIGHT", 1.0, "#2a3a2a", "#c8a040", "z+",
            depth=0.1)
    letters(b, (x0 + x1) / 2.0, 10.2, -W - 0.02, "MIDNIGHT", 1.0, "#2a3a2a", "#c8a040", "z-",
            depth=0.1)


# ============================================================== the scenery
def _scenery(b: ArenaArea, rng: random.Random) -> None:
    hx, hz = HALF
    # the track and its bed along the whole shelf, the shelf itself, the
    # valley far below
    b.box([0.0, 1.5, 0.0], [2 * hx + 120.0, 3.0, 22.0], "#d8e0ec")
    b.box([0.0, 3.2, 0.0], [2 * hx + 120.0, 0.4, 8.0], "#4a4440")
    for z in (-2.4, 2.4):
        b.box([0.0, 3.8, z], [2 * hx + 120.0, 0.6, 0.5], "#6a6e76", material="metal")
    b.box([0.0, -1.0, 40.0], [2 * hx + 240.0, 2.0, 58.0], "#c8d0dc", collide=False)
    b.box([0.0, -1.0, -40.0], [2 * hx + 240.0, 2.0, 58.0], "#c8d0dc", collide=False)
    # the shelf drops away to the valley on the south side
    b.box([0.0, -31.0, -70.0], [2 * hx + 240.0, 62.0, 2.0], "#8a94a4", collide=False)
    b.box([0.0, -62.0, 0.0], [2 * hx + 400.0, 2.0, 600.0], "#b8c4d4", collide=False)
    backdrop(b, "peaks", -60.0, rng, colours=["#5a6478", "#4a5468", "#6a7488"], depth=140.0)


# ======================================================================= meta
def _meta(b: ArenaArea) -> None:
    y = FLOOR
    starts = [(-4.0, 2.4), (8.0, 2.8), (16.0, 3.0), (12.0, 0.6), (36.0, 0.3), (46.0, 0.3),
              (56.0, 0.3), (67.5, 0.0), (-20.0, 3.18), (-34.0, 3.18), (-46.0, 3.18), (-62.0, 3.18),
              (-76.0, 3.18), (-88.0, 3.18), (-118.0, 0.0), (-104.0, 0.0)]
    for x, z in starts:
        b.team_spawn("start", x, y, z, yaw=1.5708 if x < 0 else -1.5708)
    room(b, "the observation car", -116.0, y, 0.0, [(-132.0, 0.0), (-100.0, -0.6), (-118.0, 3.6)])
    room(b, "the rear platform", -141.0, y, 2.4, [(-145.0, 2.0)])
    for key, name in (("sleeper_b", "the first-class sleeper"), ("sleeper_a", "the sleeping car")):
        x0, x1 = CARS[key]
        room(b, name, (x0 + x1) / 2.0, y, 2.9, [(x0 + 4.0, 2.9), (x1 - 4.0, 3.0)])
        span = (x1 - x0 - 2 * T) / 6.0
        for k in (1, 4):
            lo = x0 + T + span * k + 0.3
            b.mark("clue", lo + 1.9, y, -1.2)
            b.mark("roam", lo + 1.9, y, -1.0)
    room(b, "the lounge car", 6.0, y, 2.6, [(-3.0, 3.4), (16.0, 1.0), (27.0, 0.6)])
    room(b, "the dining car", 47.0, y, 1.2, [(35.0, 0.8), (62.0, 3.0), (48.0, -0.6)])
    room(b, "the galley", 67.0, y, 0.0, [(67.0, 0.6)])
    room(b, "the baggage car", 94.0, y, 0.0, [(82.0, -0.2), (104.5, -1.0), (96.0, 3.4)])
    room(b, "the coal tender", 124.0, FLOOR + 6.0, 0.0, [], roam=False)
    room(b, "the locomotive", 140.0, y, 0.0, [(138.0, 2.6)])
    room(b, "the roof", -40.0, ROOF + 0.4, 0.0, [(-77.0, 0.0), (7.0, 0.0), (57.0, 0.0), (99.0, 0.0)],
         roam=False)
    # the ways up to the roof, for the bots: the rear platform's stair, the coal
    stair(b, (PLATFORM[0] + 2.6, y, 1.2), (CARS["observation"][0] + 3.0, ROOF, -4.6))
    stair(b, (TENDER[0] + T + 2.6, y, 1.6), (CAB[0] + 2.0, ROOF, -3.0))
    b.camera(0.0, 40.0, 60.0, 0.0, 10.0, 0.0)
    b.camera(-170.0, 30.0, 30.0, -120.0, 10.0, 0.0)
    b.camera(170.0, 34.0, -30.0, 120.0, 12.0, 0.0)
    b.extra.update({"accent": "#c8a040", "twist": "tunnel", "twist_every": [38.0, 52.0],
                    "twist_for": 7.0, "twist_warn": 3.0, "roof_y": 16.5, "fall_what": "a fall from the train", "fall_y": 6.5,
                    "round_seconds": 180.0, "motion": [-1.0, 0.0], "speed": 38.0,
                    "train": [PLATFORM[0], BOILER[1]]})


def build(b: ArenaArea) -> None:
    rng = random.Random(1934)
    b.void = True
    _scenery(b, rng)
    _observation(b)
    _sleeper(b, "sleeper_b", True)
    _sleeper(b, "sleeper_a", False)
    _lounge(b)
    _dining(b)
    _baggage(b)
    _tender(b)
    _locomotive(b)
    order = ["observation", "sleeper_b", "sleeper_a", "lounge", "dining", "baggage"]
    for a, c in zip(order, order[1:]):
        _gangway(b, CARS[a][1], CARS[c][0])
    _gangway(b, CARS["baggage"][1], TENDER[0])
    _meta(b)
