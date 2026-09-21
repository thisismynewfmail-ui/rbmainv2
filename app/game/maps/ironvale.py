"""Blackout Relay -- "Ironvale Relay": a dusk-lit capture-the-flag valley.

Layout, west to east (the map is an exact mirror of itself about x = 0)::

        RED BASE          MIDFIELD           THE RELAY           MIDFIELD          BLUE BASE
    +-------------+   +--------------+   +-------------+   +--------------+   +-------------+
    | keep / flag |   | bunker (N)   |   | muster (N)  |   | bunker (N)   |   | flag / keep |
    | courtyard   |---| road+freight |---| atrium+core |---| road+freight |---|   courtyard |
    | rear yard   |   | bunker (S)   |   | muster (S)  |   | bunker (S)   |   |   rear yard |
    +-------------+   +--------------+   +-------------+   +--------------+   +-------------+
            \\____________________ the undercroft tunnels ____________________/

Three things drive the design:

* **The Relay is the spawn building.**  Both teams deploy from muster halls
  bolted onto its west and east faces, so everybody walks out of the middle
  of the map towards their own end.  The atrium between the halls is the
  shortest route across, which makes the centre the busiest room on the map.
* **Every base has three ways in.**  The gate off the main road, a sally port
  on each flank, and a postern at the back reached by the alley that runs
  outside the compound wall.  A flag can never be walled off behind one
  chokepoint.
* **The tunnels are the flag runner's road home.**  A hatch behind each keep
  drops into a corridor that runs the length of the map to the undercroft
  beneath the Relay, with spurs surfacing inside all four bunkers.  It is not
  a short cut -- it is the same distance, out of the light.

Geometry rules this file keeps to, so that nothing clips, z-fights or traps
a player:

* One ground plane.  The terrain top is y = 0 everywhere; every floor above
  it is a 2-unit pad (``PAD``), which is inside the client's 2.1 step height,
  so no pad edge is ever an invisible wall.  Relief is *added* (berms,
  freight, platforms), never dug out of the ground.
* Everything underground lives below y = ``TERRAIN_BOTTOM``, and the only
  places a player crosses that layer are the eight stair shafts and the four
  drains.  Every one of them is punched out of the terrain, the pad above it
  and the rock ceiling below it by the same rectangle (``shaft_holes``), so
  a hole and the stairs inside it can never drift apart.
* Solids abut, they do not overlap.  Two faces that share a plane always
  point away from each other, so back-face culling hides them both.
  ``tools/mapcheck.py`` re-checks that claim over the whole map.
"""
from __future__ import annotations

import math
import random
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .builder import MapBuilder

# --------------------------------------------------------------- palette
GRASS = "#3f7a4a"
GRASS_DARK = "#35663e"
GRASS_LIGHT = "#4c8c55"
DIRT = "#6b5a45"
SAND = "#b9a888"
ASPHALT = "#4e545b"
ASPHALT_LINE = "#c9cdd2"
CONCRETE = "#9aa0a6"
CONCRETE_DARK = "#787f86"
CONCRETE_LIGHT = "#b6bcc1"
STEEL = "#6f767d"
STEEL_DARK = "#4a5057"
RUST = "#8a5a3a"
WOOD = "#7a5335"
WOOD_DARK = "#543923"
ROCK = "#7d8288"
ROCK_DARK = "#666b71"
GLASS = "#9fd8e8"
LAMP = "#ffe2a8"
WATER = "#2f6f8f"

RED = "#c4281c"
RED_DARK = "#8c1c15"
RED_NEON = "#ff6a54"
BLUE = "#0d69ac"
BLUE_DARK = "#0a3c69"
BLUE_NEON = "#63c0ff"

TEAM_COLOUR = {"red": RED, "blue": BLUE}
TEAM_DARK = {"red": RED_DARK, "blue": BLUE_DARK}
TEAM_NEON = {"red": RED_NEON, "blue": BLUE_NEON}

# ------------------------------------------------------------ elevations
PAD = 2.0                  # every building floor sits one step above ground
TERRAIN_TOP = 0.0
TERRAIN_BOTTOM = -4.0
TUNNEL_CEIL = TERRAIN_BOTTOM      # the terrain slab is the tunnel roof
TUNNEL_FLOOR = -18.0
TUNNEL_BASE = -22.0
KILL_Y = -40.0

# --------------------------------------------------------------- extents
# The valley is 904 x 400 units.  The long axis is mostly midfield: a base
# gate is 196 units from the edge of the Relay's plinth, which is what makes
# a flag run a journey rather than a dash between two buildings.
MAP_X = 466.0              # terrain half-width along the long axis
MAP_Z = 214.0
WALL_T = 14.0              # perimeter wall thickness
PLAY_X = MAP_X - WALL_T    # 452: inner face of the end walls
PLAY_Z = MAP_Z - WALL_T    # 200

# ------------------------------------------------------------- the relay
RELAY_X = 58.0             # outer face of the main block
RELAY_Z = 54.0
RELAY_WALL = 5.0
RELAY_IN_X = RELAY_X - RELAY_WALL      # 53
RELAY_IN_Z = RELAY_Z - RELAY_WALL      # 49
RELAY_TOP = 28.0           # top of the walls / underside of the roof
RELAY_ROOF = 30.0
PLINTH_X = 116.0
PLINTH_Z = 84.0
MEZZ_Y = 15.5              # mezzanine walking surface
MEZZ_IN_Z = 37.0           # inner edge of the north/south balconies
ANNEX_OUT = 102.0          # outer face of a muster hall
ANNEX_Z = (20.0, 52.0)     # near/far edge of the north hall (south mirrors)
ANNEX_DOOR = (28.0, 44.0)  # doorway span, shared by both of a hall's doors
ANNEX_TOP = 18.0
ANNEX_ROOF = 19.5

# --------------------------------------------------------------- the base
BASE_FRONT = 312.0         # outer face of the front wall
BASE_WALL_T = 6.0
BASE_BACK = 452.0          # inner face of the end wall (= PLAY_X)
BASE_Z = 140.0             # inner face of the side walls
BASE_TOP = 24.0            # top of the compound wall / rampart floor
RAMPART_W = 24.0
KEEP_FRONT = 357.0
KEEP_BACK = 421.0
KEEP_Z = 46.0
KEEP_WALL = 4.0
KEEP_TOP = 18.0
KEEP_ROOF = 20.0
GALLERY_Y = 12.5           # walking surface of the keep's inner balcony
FLAG_X = 384.0             # the pedestal, a touch in front of the keep's centre
FLAG_Y = 6.2

# ------------------------------------------------------------- the field
# Three bands of cover between the plinth and a compound gate, each with a
# job: freight to break the first 80 units of road, the Cutting to give the
# middle of the midfield a piece of high ground worth taking, and the depots
# to give the last approach to a gate somewhere to fight from.
FREIGHT_X = 152.0          # centre of a freight yard
FREIGHT_Z = 60.0
CUTTING_X = (196.0, 232.0)  # the revetment across the midfield
CUTTING_TOP = 12.0
CUTTING_GAP = 27.0         # the road's way through it, either side of z = 0
CUTTING_END = 84.0         # where each wing stops, short of the bunkers
BUNKER_X = (208.0, 268.0)  # forward outposts: the lockdown spawns
BUNKER_Z = (94.0, 148.0)
BUNKER_TOP = 13.0
BUNKER_ROOF = 15.0
DEPOT_X = (264.0, 312.0)   # pump house (south) and fuel depot (north)
DEPOT_Z = (34.0, 84.0)
DEPOT_TOP = 14.0
DEPOT_ROOF = 16.0
ROAD_Z = 19.0
ALLEY_Z = 174.0            # centre of the lane outside the compound wall

# ------------------------------------------------------------ the tunnels
TUN_MAIN_Z = (-32.0, -8.0)         # the long corridor, 24 wide
TUN_SPUR_X = (228.0, 248.0)        # the north/south spur, 20 wide
TUN_SPUR_Z = 108.0                 # where the spur meets its stair
TUN_SPUR_TOP = 134.0               # ...and where that stair surfaces
UNDER_X = 86.0
UNDER_Z = 78.0
CISTERN_X = (262.0, 322.0)         # the flooded hall half way along
CISTERN_Z = (-40.0, 78.0)
HATCH_X = (421.0, 453.0)           # the chamber under each keep's rear yard
HATCH_Z = (-36.0, 12.0)
HATCH_STAIR_X = (429.0, 445.0)
HATCH_STAIR_Z = (-20.0, 6.0)
RELAY_STAIR_X = (32.0, 52.0)
RELAY_STAIR_Z = (-30.0, -4.0)
BUNKER_STAIR_X = (230.0, 246.0)
PUMP_STAIR_X = (276.0, 294.0)      # cistern up into the pump house
PUMP_STAIR_Z = (44.0, 70.0)
DRAIN_X = (43.0, 57.0)
DRAIN_Z = (59.0, 73.0)

STEP_MAX = 2.0             # the client steps up to 2.1; stay inside it


# =========================================================== small helpers
def rect(x0: float, x1: float, z0: float, z1: float) -> Tuple[float, float, float, float]:
    """A rectangle in the ground plane, always lowest-coordinate first."""
    return (min(x0, x1), max(x0, x1), min(z0, z1), max(z0, z1))


def carve(area: Tuple[float, float, float, float],
          holes: Sequence[Tuple[float, float, float, float]]
          ) -> List[Tuple[float, float, float, float]]:
    """Cover ``area`` with rectangles that avoid every hole.

    The sweep splits the area into bands at each hole edge along z, walks each
    band left to right skipping the holes that cross it, and then glues bands
    back together where they happen to share an x range.  The result tiles the
    area exactly: no gaps to fall through and no two pieces overlapping, which
    is what keeps the ground free of z-fighting.
    """
    x0, x1, z0, z1 = area
    cuts = sorted({z0, z1} | {v for h in holes for v in (h[2], h[3])
                              if z0 < v < z1})
    pieces: List[Tuple[float, float, float, float]] = []
    for za, zb in zip(cuts, cuts[1:]):
        crossing = sorted((h for h in holes
                           if h[2] < zb - 1e-6 and h[3] > za + 1e-6
                           and h[1] > x0 + 1e-6 and h[0] < x1 - 1e-6),
                          key=lambda h: h[0])
        cursor = x0
        for hole in crossing:
            start = max(x0, hole[0])
            if start - cursor > 1e-6:
                pieces.append((cursor, start, za, zb))
            cursor = max(cursor, min(x1, hole[1]))
        if x1 - cursor > 1e-6:
            pieces.append((cursor, x1, za, zb))
    merged: List[Tuple[float, float, float, float]] = []
    for piece in sorted(pieces, key=lambda p: (p[0], p[1], p[2])):
        if merged:
            last = merged[-1]
            if abs(last[0] - piece[0]) < 1e-6 and abs(last[1] - piece[1]) < 1e-6 \
                    and abs(last[3] - piece[2]) < 1e-6:
                merged[-1] = (last[0], last[1], last[2], piece[3])
                continue
        merged.append(piece)
    return merged


def slab(b: MapBuilder, area: Tuple[float, float, float, float], top: float,
         thickness: float, colour: str, **kw) -> Dict[str, Any]:
    """One floor plate, given as a rectangle and the height of its surface."""
    x0, x1, z0, z1 = area
    return b.box([(x0 + x1) / 2.0, top - thickness / 2.0, (z0 + z1) / 2.0],
                 [x1 - x0, thickness, z1 - z0], colour, **kw)


def plate(b: MapBuilder, areas: Sequence[Tuple[float, float, float, float]],
          top: float, thickness: float, colour: str, **kw) -> None:
    for area in areas:
        slab(b, area, top, thickness, colour, **kw)


def wall(b: MapBuilder, axis: str, at: float, thickness: float,
         lo: float, hi: float, y0: float, y1: float, colour: str,
         gaps: Sequence[Tuple[float, float, float]] = (), **kw) -> None:
    """A straight wall with doorways cut into it.

    ``axis`` is the axis the wall *runs along*: "z" puts it at x = ``at``,
    "x" puts it at z = ``at``.  Every gap is ``(start, end, head)`` -- where
    the opening begins and ends along the wall, and the height its lintel
    starts at.  A ``head`` at or above ``y1`` leaves the opening full height.
    """
    def piece(a: float, c: float, ya: float, yb: float) -> None:
        if c - a < 1e-6 or yb - ya < 1e-6:
            return
        if axis == "z":
            b.box([at, (ya + yb) / 2.0, (a + c) / 2.0],
                  [thickness, yb - ya, c - a], colour, **kw)
        else:
            b.box([(a + c) / 2.0, (ya + yb) / 2.0, at],
                  [c - a, yb - ya, thickness], colour, **kw)

    cursor = lo
    for start, end, head in sorted(gaps, key=lambda g: g[0]):
        # Clip the opening to the wall.  A caller that hands the same list of
        # doorways to several pieces of one long wall would otherwise have
        # the pieces that do not contain a doorway build themselves all the
        # way out to where it starts -- straight through whatever is there.
        start = max(lo, min(hi, start))
        end = max(lo, min(hi, end))
        if end - start < 1e-6:
            continue
        piece(cursor, start, y0, y1)
        piece(start, end, min(head, y1), y1)
        cursor = max(cursor, end)
    piece(cursor, hi, y0, y1)



def room_walls(b: MapBuilder, area: Tuple[float, float, float, float],
               thickness: float, y0: float, y1: float, colour: str,
               doors: Optional[Dict[str, Sequence[Tuple[float, float, float]]]] = None,
               sides: Sequence[str] = ("x-", "x+", "z-", "z+"), **kw) -> None:
    """Four walls inside ``area`` that meet at the corners without overlapping.

    The two walls facing along x run the full depth and the two facing along
    z are inset to fit between them, which is the whole trick: overlapping
    corners put two identical faces on the same plane, and a depth buffer
    cannot choose between them.  ``doors`` maps a side ("x-", "x+", "z-",
    "z+") to the openings in it, each ``(start, end, head)``.
    """
    x0, x1, z0, z1 = area
    doors = doors or {}
    if "x-" in sides:
        wall(b, "z", x0 + thickness / 2.0, thickness, z0, z1, y0, y1, colour,
             gaps=doors.get("x-", ()), **kw)
    if "x+" in sides:
        wall(b, "z", x1 - thickness / 2.0, thickness, z0, z1, y0, y1, colour,
             gaps=doors.get("x+", ()), **kw)
    if "z-" in sides:
        wall(b, "x", z0 + thickness / 2.0, thickness, x0 + thickness,
             x1 - thickness, y0, y1, colour, gaps=doors.get("z-", ()), **kw)
    if "z+" in sides:
        wall(b, "x", z1 - thickness / 2.0, thickness, x0 + thickness,
             x1 - thickness, y0, y1, colour, gaps=doors.get("z+", ()), **kw)


def flight(b: MapBuilder, axis: str, near: float, far: float,
           lo: float, hi: float, y_near: float, y_far: float,
           colour: str, fill: Optional[float] = None,
           rise: float = STEP_MAX, **kw) -> None:
    """A straight staircase whose two ends land exactly on the floors it joins.

    It travels along ``axis`` from ``near`` to ``far`` (either end may be the
    higher one) and is ``lo``..``hi`` wide across.  The last tread finishes
    flush with ``far`` at ``y_far`` and the first step up from ``near`` is one
    rise, so a flight can always be butted straight against a slab without
    overlapping it.  Treads are solid down to ``fill`` so there is no hollow
    underneath to fall into or see through.
    """
    drop = abs(y_far - y_near)
    steps = max(1, int(math.ceil(drop / rise - 1e-6)))
    dy = (y_far - y_near) / steps
    run = (far - near) / steps
    base = fill if fill is not None else min(y_near, y_far) - 6.0
    for i in range(steps):
        a, c = near + run * i, near + run * (i + 1)
        top = y_near + dy * (i + 1)
        if axis == "x":
            b.box([(a + c) / 2.0, (base + top) / 2.0, (lo + hi) / 2.0],
                  [abs(c - a), top - base, hi - lo], colour, **kw)
        else:
            b.box([(lo + hi) / 2.0, (base + top) / 2.0, (a + c) / 2.0],
                  [hi - lo, top - base, abs(c - a)], colour, **kw)


def crenels(b: MapBuilder, axis: str, at: float, lo: float, hi: float,
            y: float, colour: str, every: float = 9.0, size: float = 4.5,
            height: float = 3.0, thickness: float = 3.0) -> None:
    """Decorative merlons along a parapet -- never solid, never in the way."""
    count = max(2, int((hi - lo) / every))
    step = (hi - lo) / count
    for i in range(count):
        centre = lo + step * (i + 0.5)
        if axis == "z":
            b.box([at, y + height / 2.0, centre], [thickness, height, size],
                  colour, collide=False)
        else:
            b.box([centre, y + height / 2.0, at], [size, height, thickness],
                  colour, collide=False)


def strip_light(b: MapBuilder, x: float, z: float, y: float, length: float,
                axis: str = "x", colour: str = LAMP, width: float = 1.6) -> None:
    """A ceiling tube.  Neon is self-lit, so these carry the interiors."""
    size = [length, 0.5, width] if axis == "x" else [width, 0.5, length]
    b.box([x, y, z], size, colour, material="neon", collide=False)


def floodlight(b: MapBuilder, x: float, z: float, y: float = 0.0,
               height: float = 26.0, colour: str = LAMP) -> None:
    b.cyl([x, y + height / 2.0, z], [2.2, height, 2.2], STEEL_DARK,
          material="metal")
    b.box([x, y + height + 1.4, z], [7.0, 2.8, 5.0], STEEL, collide=False,
          material="metal")
    b.box([x, y + height + 0.2, z], [5.6, 1.0, 3.8], colour, material="neon",
          collide=False)


def hazard_rim(b: MapBuilder, area: Tuple[float, float, float, float],
               y: float) -> None:
    """A striped lip around an open shaft, so nobody walks into one blind."""
    x0, x1, z0, z1 = area
    for at, axis in ((x0 - 1.0, "z"), (x1 + 1.0, "z")):
        b.box([at, y + 0.45, (z0 + z1) / 2.0], [2.0, 0.9, z1 - z0 + 4.0],
              "#f2b01e", collide=False, decal="hazard")
    for at in (z0 - 1.0, z1 + 1.0):
        b.box([(x0 + x1) / 2.0, y + 0.45, at], [x1 - x0, 0.9, 2.0],
              "#f2b01e", collide=False, decal="hazard")




def shaft_lamp(b: MapBuilder, area: Tuple[float, float, float, float]) -> None:
    """Light a stair shaft from its rim rather than from thin air.

    A strip hung down the middle of an open shaft is a strip floating over a
    staircase when anybody looks into it from above.  These sit recessed
    under the lip of the hole, so the stairs are lit and there is nothing
    to see hanging in the gap.
    """
    x0, x1, z0, z1 = area
    for at in (x0 + 0.7, x1 - 0.7):
        b.box([at, TERRAIN_BOTTOM + 0.7, (z0 + z1) / 2.0],
              [1.0, 0.8, (z1 - z0) - 4.0], "#9fe8ff", material="neon",
              collide=False)


def deploy_pad(b: MapBuilder, x: float, z: float, y: float, colour: str,
               size: float = 7.0) -> None:
    """A spawn pad, painted on the floor rather than lit up.

    A glowing plate under your feet is the brightest thing on screen at the
    exact moment you most need to read the room, and nobody has to *find* a
    spawn point.  Paint says the same thing and then gets out of the way.
    """
    b.box([x, y + 0.12, z], [size, 0.24, size], "#6e757c", collide=False)
    half = size / 2.0
    for offset in (-half + 0.4, half - 0.4):
        b.box([x + offset, y + 0.28, z], [0.8, 0.2, size], colour,
              collide=False)
        b.box([x, y + 0.28, z + offset], [size - 1.6, 0.2, 0.8], colour,
              collide=False)


def face_sign(b: MapBuilder, x: float, y: float, z: float, w: float, h: float,
              decal: str, facing: str, colour: str = "#f2f3f3") -> None:
    """A flat sign whose printed face looks along +X, -X, +Z or -Z.

    Decals are painted on a part's own +Z face, so a sign that has to face
    along X is the same box given a quarter turn -- which the collision
    builders already understand, and which these never need anyway.
    """
    turn = {"z+": 0.0, "z-": math.pi, "x+": math.pi / 2.0,
            "x-": -math.pi / 2.0}[facing]
    b.box([x, y, z], [w, h, 0.7], colour, r=[0, turn, 0], collide=False,
          decal=decal)


# ============================================================== the relay
def _muster_hall(b: MapBuilder, team: str, sx: int, sz: int) -> List[Dict[str, Any]]:
    """One of the four spawn halls bolted onto the Relay's west and east faces.

    ``sx`` picks the side (-1 red / +1 blue) and ``sz`` the end (-1 north /
    +1 south).  Each team gets both ends, so a full server spreads over two
    doors instead of stacking behind one, and every hall has two ways out:
    straight onto your own half through the outer door, and inwards to the
    atrium through the wall it shares with the Relay.
    """
    colour = TEAM_COLOUR[team]
    dark = TEAM_DARK[team]
    neon = TEAM_NEON[team]
    inward = -sx                       # +1 points from the hall to the centre
    out_x = sx * ANNEX_OUT             # outer face
    in_x = sx * RELAY_X                # shared face with the Relay
    skin_x = out_x + inward * 5.0      # inner surface of the outer wall
    zlo = min(sz * ANNEX_Z[0], sz * ANNEX_Z[1])
    zhi = max(sz * ANNEX_Z[0], sz * ANNEX_Z[1])
    dlo = min(sz * ANNEX_DOOR[0], sz * ANNEX_DOOR[1])
    dhi = max(sz * ANNEX_DOOR[0], sz * ANNEX_DOOR[1])
    head = PAD + 12.0

    # Team colour on the outside, pale concrete on the inside.  From the
    # field a red or blue hall is the landmark that tells you whose half you
    # are on; from a deploy pad a wall of saturated team colour a body-length
    # from your face is the only thing you can see, every single life.  So
    # the colour is a one-unit skin and the structure behind it is concrete.
    for at, out in ((zlo, -1.0), (zhi, 1.0)):
        wall(b, "x", at + out * 0.5, 1.0, min(out_x, in_x), max(out_x, in_x),
             PAD, ANNEX_TOP, colour)
        wall(b, "x", at + out * -3.0, 4.0, min(out_x, in_x), max(out_x, in_x),
             PAD, ANNEX_TOP, CONCRETE_LIGHT)
    wall(b, "z", out_x + inward * 0.5, 1.0, zlo + 5.0, zhi - 5.0,
         PAD, ANNEX_TOP, colour, gaps=[(dlo, dhi, head)])
    wall(b, "z", out_x + inward * 3.0, 4.0, zlo + 5.0, zhi - 5.0,
         PAD, ANNEX_TOP, CONCRETE_LIGHT, gaps=[(dlo, dhi, head)])

    # roof with a shallow eave, and a parapet along the outer edge so the
    # rooftop route cannot dump you off the back by accident
    slab(b, rect(out_x, in_x, zlo - 2.0, zhi + 2.0), ANNEX_ROOF,
         ANNEX_ROOF - ANNEX_TOP, dark, studs=True)
    wall(b, "z", out_x + inward * 1.2, 2.4, zlo - 2.0, zhi + 2.0,
         ANNEX_ROOF, ANNEX_ROOF + 2.6, dark)
    # A band of colour under the eaves -- and nothing across the doorway.
    # There used to be a full-height panel here; it did not collide, so it
    # was a wall you walked through on the way out of your own spawn.
    for lo, hi in ((zlo + 1.0, dlo - 1.0), (dhi + 1.0, zhi - 1.0)):
        if hi - lo < 1.0:
            continue
        b.box([out_x - inward * 0.4, ANNEX_TOP - 1.8, (lo + hi) / 2.0],
              [0.8, 1.2, hi - lo], neon, material="neon", collide=False)

    # lit inside, with the team's colours over the door you walk out of
    for sz_off in (-1, 1):
        strip_light(b, (skin_x + in_x) / 2.0,
                    (zlo + zhi) / 2.0 + sz_off * 7.0, ANNEX_TOP - 1.6,
                    abs(in_x - skin_x) - 6.0, "x")
        b.box([(skin_x + in_x) / 2.0, PAD + 9.0,
               (zlo + zhi) / 2.0 + sz_off * ((zhi - zlo) / 2.0 - 5.4)],
              [abs(in_x - skin_x) - 4.0, 1.0, 0.8], colour, collide=False)
    face_sign(b, skin_x + inward * 0.5, PAD + 13.75, (dlo + dhi) / 2.0,
              12.0, 3.4, "sign_%s" % team, "x+" if inward > 0 else "x-")

    # wall racks and a floor stripe: kit the room out without putting a
    # single solid where somebody is about to spawn
    for at in (zlo + 6.0, zhi - 6.0):     # either side of the back door
        b.box([in_x + inward * 0.8, PAD + 7.0, at], [1.2, 5.0, 6.0], STEEL,
              collide=False, material="metal")
    b.box([(skin_x + in_x) / 2.0, PAD + 0.12, (zlo + zhi) / 2.0],
          [abs(in_x - skin_x) - 6.0, 0.24, 3.0], dark, collide=False)
    # cover for the moment you step outside, set beside the doorway rather
    # than across it
    b.box([out_x - inward * 6.0, PAD + 2.4, zlo + 3.0], [9.0, 4.8, 9.0],
          dark, studs=True)
    b.box([out_x - inward * 6.0, PAD + 2.0, zhi - 3.0], [9.0, 4.0, 9.0],
          CONCRETE_DARK, studs=True)

    # The way through to the atrium is a door, not a missing wall: the
    # Relay's own shell is filled back in across this bay and a 12-wide
    # opening cut through it, so the room you spawn in has four sides and
    # the back way out is somewhere a defender can actually stand.
    wall(b, "z", sx * (RELAY_X - RELAY_WALL / 2.0), RELAY_WALL, dlo, dhi,
         PAD, PAD + 12.0, CONCRETE_LIGHT,
         gaps=[(dlo + 2.0, dhi - 2.0, PAD + 9.0)])
    for at in (dlo + 2.0, dhi - 2.0):
        b.box([in_x + inward * 1.0, PAD + 4.5, at], [1.4, 9.0, 0.8], colour,
              collide=False)
    b.box([in_x + inward * 1.0, PAD + 9.4, (dlo + dhi) / 2.0],
          [1.4, 0.8, dhi - dlo - 4.0], colour, collide=False)

    # the deploy pads -- six per hall, facing out of the outer door
    yaw = sx * math.pi / 2.0
    spawns = []
    for i in range(6):
        px = skin_x + inward * (8.0 + (i % 3) * 12.0)
        pz = zlo + 10.0 + (i // 3) * ((zhi - zlo) - 20.0)
        deploy_pad(b, px, pz, PAD, colour)
        b.spawn(team, px, PAD + 1.0, pz, yaw)
        spawns.append({"p": [round(px, 2), round(PAD + 1.0, 2), round(pz, 2)],
                       "yaw": round(yaw, 3)})
    return spawns


def _relay(b: MapBuilder, holes: Sequence[Tuple[float, float, float, float]]) -> None:
    """The building in the middle of the map: muster halls, atrium, mast."""
    roof_gap = (-42.0, -28.0, RELAY_ROOF)      # where the roof stair arrives

    # ---------------------------------------------------------- the plinth
    plate(b, carve(rect(-PLINTH_X, PLINTH_X, -PLINTH_Z, PLINTH_Z), holes),
          PAD, PAD, CONCRETE, studs=True)
    for sx in (-1, 1):
        b.box([sx * (RELAY_X + PLINTH_X) / 2.0, PAD + 0.15, 0.0],
              [PLINTH_X - RELAY_X, 0.3, ROAD_Z * 2.0], CONCRETE_DARK,
              collide=False)

    # ------------------------------------------------------------- shell
    side_doors = [(-16.0, 16.0, 18.0),
                  (-ANNEX_DOOR[1], -ANNEX_DOOR[0], PAD + 12.0),
                  (ANNEX_DOOR[0], ANNEX_DOOR[1], PAD + 12.0)]
    end_doors = [(-40.0, -24.0, 15.0), (24.0, 40.0, 15.0)]
    room_walls(b, rect(-RELAY_X, RELAY_X, -RELAY_Z, RELAY_Z), RELAY_WALL,
               PAD, RELAY_TOP, CONCRETE_LIGHT,
               doors={"x-": side_doors, "x+": side_doors,
                      "z-": end_doors, "z+": end_doors})

    # roof, with an oculus over the core: the mast climbs out through it and
    # anyone up top can drop straight back into the middle of the fight
    oculus = rect(-13.0, 13.0, -13.0, 13.0)
    plate(b, carve(rect(-RELAY_X, RELAY_X, -RELAY_Z, RELAY_Z), [oculus]),
          RELAY_ROOF, RELAY_ROOF - RELAY_TOP, CONCRETE_DARK, studs=True)
    hazard_rim(b, oculus, RELAY_ROOF)
    room_walls(b, rect(-RELAY_X, RELAY_X, -RELAY_Z, RELAY_Z), 3.0,
               RELAY_ROOF, RELAY_ROOF + 3.4, CONCRETE,
               doors={"x-": [roof_gap], "x+": [roof_gap]})
    for sx in (-1, 1):
        crenels(b, "z", sx * (RELAY_X - 1.5), -RELAY_Z + 4, RELAY_Z - 4,
                RELAY_ROOF + 3.4, CONCRETE_LIGHT, every=11.0, thickness=2.4)
    for sz in (-1, 1):
        crenels(b, "x", sz * (RELAY_Z - 1.5), -RELAY_X + 7, RELAY_X - 7,
                RELAY_ROOF + 3.4, CONCRETE_LIGHT, every=11.0, thickness=2.4)

    # ------------------------------------------------------------- atrium
    for sx in (-1, 1):
        for sz in (-1, 1):
            b.box([sx * 41.0, (PAD + MEZZ_Y - 1.5) / 2.0, sz * 41.0],
                  [6.0, MEZZ_Y - 1.5 - PAD, 6.0], CONCRETE_DARK)
    b.box([0, PAD + 1.0, 0], [44, 2.0, 44], CONCRETE_DARK, studs=True)
    b.box([0, PAD + 3.0, 0], [28, 2.0, 28], CONCRETE_LIGHT, studs=True)
    b.cyl([0, PAD + 4.6, 0], [18, 1.2, 18], "#f5c518", collide=False,
          material="neon")
    # the mast: solid while it is inside the building, scenery above the roof
    b.cyl([0, (PAD + 4.0 + RELAY_ROOF) / 2.0, 0],
          [7.0, RELAY_ROOF - PAD - 4.0, 7.0], STEEL, material="metal")
    b.cyl([0, RELAY_ROOF + 13.0, 0], [4.4, 26.0, 4.4], STEEL_DARK,
          material="metal", collide=False)
    for i in range(3):
        b.box([0, RELAY_ROOF + 4.0 + i * 9.0, 0],
              [15.0 - i * 3.0, 0.8, 15.0 - i * 3.0], STEEL, collide=False,
              material="metal")
    b.cone([0, RELAY_ROOF + 29.0, 0], [17.0, 7.0, 17.0], CONCRETE_LIGHT,
           collide=False)
    b.sphere([0, RELAY_ROOF + 34.0, 0], [3.4, 3.4, 3.4], "#ff7a3d",
             material="neon", collide=False)

    # cover on the atrium floor: a hall this size with nothing in it is a
    # shooting gallery.  Everything here sits clear of the stairwells, the
    # dais and the columns, so the middle stays a room you fight through
    # rather than an obstacle course
    for sx in (-1, 1):
        for sz in (-1, 1):
            b.box([sx * 12.0, PAD + 3.0, sz * 34.0], [10.0, 6.0, 10.0], WOOD,
                  studs=True)
        b.box([sx * 47.0, PAD + 4.0, 15.0], [6.0, 8.0, 14.0], STEEL,
              material="metal")
        # each team's colours carried round the inside of its own doorway
        for sz in (-1, 1):
            b.box([sx * (RELAY_IN_X - 0.4), PAD + 10.0,
                   sz * (ANNEX_DOOR[0] + ANNEX_DOOR[1]) / 2.0],
                  [0.8, 1.4, ANNEX_DOOR[1] - ANNEX_DOOR[0]],
                  TEAM_NEON["red" if sx < 0 else "blue"], material="neon",
                  collide=False)
    for sz in (-1, 1):
        b.box([0, PAD + 2.0, sz * 42.0], [26.0, 4.0, 5.0], CONCRETE_DARK,
              studs=True)

    # mezzanine: two balconies looking at each other across the oculus
    for sz in (-1, 1):
        far = sz * RELAY_IN_Z
        near = sz * MEZZ_IN_Z
        slab(b, rect(-41.0, 41.0, min(near, far), max(near, far)), MEZZ_Y,
             1.5, CONCRETE_DARK, studs=True)
        b.box([0, MEZZ_Y + 1.6, near - sz * 0.5], [82.0, 3.2, 1.0], STEEL,
              collide=False, material="metal")
        for sx in (-1, 1):
            flight(b, "z", sz * 19.0, near, sx * 30.0 - 5.0, sx * 30.0 + 5.0,
                   PAD, MEZZ_Y, CONCRETE, fill=PAD, rise=1.95)
        strip_light(b, 0, sz * 43.0, RELAY_TOP - 2.0, 70.0, "x")
    strip_light(b, 0, 0, RELAY_TOP - 3.4, 88.0, "z")

    # ----------------------------------------- stairs down to the undercroft
    for sx in (-1, 1):
        area = rect(sx * RELAY_STAIR_X[0], sx * RELAY_STAIR_X[1],
                    RELAY_STAIR_Z[0], RELAY_STAIR_Z[1])
        flight(b, "z", area[3], area[2], area[0], area[1], PAD, TUNNEL_FLOOR,
               CONCRETE_DARK, fill=TUNNEL_FLOOR)
        b.box([(area[0] + area[1]) / 2.0, PAD + 0.45, area[3] + 2.4],
              [area[1] - area[0], 0.9, 2.0], "#f2b01e", collide=False,
              decal="hazard")
        shaft_lamp(b, area)

    # ------------------------------------------------- the four muster halls
    for team, sx in (("red", -1), ("blue", 1)):
        pads: List[Dict[str, Any]] = []
        for sz in (-1, 1):
            pads.extend(_muster_hall(b, team, sx, sz))
        b.marker("muster_%s" % team, pads)

    # plinth -> north annex roof -> Relay roof, in two flights
    for sx in (-1, 1):
        flight(b, "z", -PLINTH_Z + 4.0, -(ANNEX_Z[1] + 2.0),
               sx * 86.0 - 6.0, sx * 86.0 + 6.0, PAD, ANNEX_ROOF,
               CONCRETE_DARK, fill=PAD, rise=1.95)
        flight(b, "x", sx * 76.0, sx * RELAY_X, -40.0, -30.0,
               ANNEX_ROOF, RELAY_ROOF, CONCRETE_DARK, fill=ANNEX_ROOF,
               rise=1.95)

    # ---------------------------------------------------------- the drains
    # one-way ways down into the tunnels, out on the flanks of the plinth
    for sx in (-1, 1):
        for sz in (-1, 1):
            area = rect(sx * DRAIN_X[0], sx * DRAIN_X[1],
                        sz * DRAIN_Z[0], sz * DRAIN_Z[1])
            hazard_rim(b, area, PAD)

    # floodlights round the plinth, banners either side of each main door
    for sx in (-1, 1):
        for sz in (-1, 1):
            floodlight(b, sx * 100.0, sz * 68.0, PAD, 24.0)
            face_sign(b, sx * (RELAY_X + 0.4), PAD + 13.0, sz * 22.0,
                      12.0, 14.0, "banner_%s" % ("red" if sx < 0 else "blue"),
                      "x-" if sx < 0 else "x+",
                      RED_DARK if sx < 0 else BLUE_DARK)


# =============================================================== the bases
def _base(b: MapBuilder, team: str, sx: int,
          holes: Sequence[Tuple[float, float, float, float]]) -> None:
    """One team's compound: rampart, courtyard, keep, rear yard, hatch house.

    Everything here is written as a *magnitude* along x and multiplied by
    ``sx``, so the red compound at -x and the blue one at +x are the same
    building to the last unit.  Three ways in, by design: the gate off the
    road, a sally port on each flank, and the postern at the back that the
    outside lane leads to.
    """
    colour = TEAM_COLOUR[team]
    dark = TEAM_DARK[team]
    neon = TEAM_NEON[team]

    def xs(a: float, c: float) -> Tuple[float, float]:
        return (min(sx * a, sx * c), max(sx * a, sx * c))

    front_out, front_in = BASE_FRONT, BASE_FRONT + BASE_WALL_T
    side_in, side_out = BASE_Z, BASE_Z + BASE_WALL_T
    keep_in, keep_far = KEEP_FRONT + KEEP_WALL, KEEP_BACK - KEEP_WALL
    gallery_step = keep_in + 25.0        # where the stair up to it lands
    gallery_back = keep_far - 12.0       # inner edge of the back leg
    yard0, yard1 = KEEP_BACK + 4.0, BASE_BACK - 3.0   # the rear yard's shed
    postern = (KEEP_BACK + 6.0, KEEP_BACK + 20.0)

    # --------------------------------------------------------------- apron
    plate(b, carve(rect(sx * front_out, sx * BASE_BACK, -side_out, side_out),
                   holes), PAD, PAD, CONCRETE, studs=True)
    # a darker concrete lane from the gate to the keep door
    b.box([sx * (front_in + KEEP_FRONT) / 2.0, PAD + 0.15, 0],
          [KEEP_FRONT - front_in, 0.3, 46.0], CONCRETE_DARK, collide=False)

    # ---------------------------------------------------- the compound wall
    wall(b, "z", sx * (front_out + BASE_WALL_T / 2.0), BASE_WALL_T,
         -side_out, side_out, PAD, BASE_TOP, CONCRETE,
         gaps=[(-22.0, 22.0, 16.0), (-106.0, -86.0, 13.0), (86.0, 106.0, 13.0)])
    for sz in (-1, 1):
        lo, hi = xs(front_in, BASE_BACK)
        wall(b, "x", sz * (side_in + BASE_WALL_T / 2.0), BASE_WALL_T, lo, hi,
             PAD, BASE_TOP, CONCRETE,
             gaps=[xs(*postern) + (13.0,)])              # the rear postern

    # rampart walk over the front wall, carried on columns over the courtyard
    walk = xs(front_out, front_out + RAMPART_W)
    slab(b, (walk[0], walk[1], -side_out, side_out), BASE_TOP + 1.5, 1.5,
         CONCRETE_DARK, studs=True)
    for i in range(9):
        z = -side_in + 2.0 + i * (side_in * 2.0 - 4.0) / 8.0
        b.box([sx * (front_out + RAMPART_W - 3.0), (PAD + BASE_TOP) / 2.0, z],
              [4.0, BASE_TOP - PAD, 4.0], CONCRETE_DARK)
    wall(b, "z", sx * (front_out + 1.5), 3.0, -side_out, side_out,
         BASE_TOP + 1.5, BASE_TOP + 5.0, CONCRETE_LIGHT)
    crenels(b, "z", sx * (front_out + 1.5), -side_in, side_in,
            BASE_TOP + 5.0, CONCRETE, every=12.0, thickness=2.4)
    b.box([sx * (front_out + RAMPART_W - 0.5), BASE_TOP + 3.0, 0],
          [1.0, 3.0, side_out * 2.0], STEEL, collide=False, material="metal")
    for sz in (-1, 1):
        stair = xs(front_out + RAMPART_W, front_out + RAMPART_W + 12.0)
        flight(b, "z", sz * 78.0, sz * 48.0, stair[0], stair[1],
               PAD, BASE_TOP + 1.5, CONCRETE_DARK, fill=PAD)

    # ---------------------------------------------------------- the keep
    keep_z_in = KEEP_Z - KEEP_WALL                                   # 42
    wall(b, "z", sx * (KEEP_FRONT + KEEP_WALL / 2.0), KEEP_WALL,
         -KEEP_Z, KEEP_Z, PAD, KEEP_TOP, CONCRETE_LIGHT,
         gaps=[(-13.0, 13.0, 12.0)])
    wall(b, "z", sx * (KEEP_BACK - KEEP_WALL / 2.0), KEEP_WALL,
         -KEEP_Z, KEEP_Z, PAD, KEEP_TOP, CONCRETE_LIGHT,
         gaps=[(-10.0, 10.0, 11.0)])
    for sz in (-1, 1):
        lo, hi = xs(KEEP_FRONT + KEEP_WALL, KEEP_BACK - KEEP_WALL)
        wall(b, "x", sz * (KEEP_Z - KEEP_WALL / 2.0), KEEP_WALL, lo, hi,
             PAD, KEEP_TOP, CONCRETE_LIGHT,
             gaps=[xs(FLAG_X - 7.0, FLAG_X + 9.0) + (11.0,)])
    slab(b, rect(sx * KEEP_FRONT, sx * KEEP_BACK, -KEEP_Z, KEEP_Z),
         KEEP_ROOF, KEEP_ROOF - KEEP_TOP, dark, studs=True)

    # the flag pedestal, sat a little in front of centre so it reads from
    # the doorway the moment an attacker steps through it
    b.box([sx * FLAG_X, PAD + 1.0, 0], [26, 2.0, 26], CONCRETE_DARK, studs=True)
    b.box([sx * FLAG_X, PAD + 3.0, 0], [16, 2.0, 16], colour, studs=True)
    b.cyl([sx * FLAG_X, PAD + 4.3, 0], [12, 0.6, 12], neon, material="neon",
          collide=False)

    # inner gallery: a U of balcony that looks down on the pedestal
    for sz in (-1, 1):
        leg = xs(gallery_step, gallery_back)
        slab(b, (leg[0], leg[1], min(sz * 30.0, sz * keep_z_in),
                 max(sz * 30.0, sz * keep_z_in)), GALLERY_Y, 1.5,
             CONCRETE_DARK, studs=True)
        stair = xs(keep_in, gallery_step)
        flight(b, "x", stair[1] if sx < 0 else stair[0],
               stair[0] if sx < 0 else stair[1],
               min(sz * 32.0, sz * 40.0), max(sz * 32.0, sz * 40.0),
               PAD, GALLERY_Y, CONCRETE, fill=PAD)
        b.box([sx * (gallery_step + gallery_back) / 2.0, GALLERY_Y + 1.6,
               sz * 30.5], [gallery_back - gallery_step, 3.2, 1.0],
              STEEL, collide=False, material="metal")
    back_leg = xs(gallery_back, keep_far)
    slab(b, (back_leg[0], back_leg[1], -keep_z_in, keep_z_in), GALLERY_Y, 1.5,
         CONCRETE_DARK, studs=True)
    b.box([sx * (gallery_back - 0.5), GALLERY_Y + 1.6, 0],
          [1.0, 3.2, 60.0], STEEL,
          collide=False, material="metal")

    # keep lighting and the team's colours inside the flag room
    strip_light(b, sx * (keep_in + 14.0), 0, KEEP_TOP - 1.8, 56.0, "z")
    strip_light(b, sx * (keep_far - 14.0), 0, KEEP_TOP - 1.8, 56.0, "z")
    for sz in (-1, 1):
        b.box([sx * FLAG_X, KEEP_TOP - 1.0, sz * 22.0], [30.0, 1.0, 0.8],
              neon, material="neon", collide=False)

    # outside stairs onto the keep roof, one on each flank
    for sz in (-1, 1):
        stair = xs(keep_far - 10.0, keep_far + 2.0)
        flight(b, "z", sz * 70.0, sz * KEEP_Z, stair[0], stair[1],
               PAD, KEEP_ROOF, CONCRETE_DARK, fill=PAD)
    for sz in (-1, 1):
        wall(b, "x", sz * (KEEP_Z - 1.5), 3.0, *xs(KEEP_FRONT, KEEP_BACK),
             y0=KEEP_ROOF, y1=KEEP_ROOF + 3.4, colour=CONCRETE,
             gaps=[xs(keep_far - 10.0, keep_far + 2.0) + (KEEP_ROOF,)])
    for at in (KEEP_FRONT + 1.5, KEEP_BACK - 1.5):
        wall(b, "z", sx * at, 3.0, -KEEP_Z + 3, KEEP_Z - 3,
             KEEP_ROOF, KEEP_ROOF + 3.4, CONCRETE)
    crenels(b, "z", sx * (KEEP_FRONT + 1.5), -KEEP_Z + 6, KEEP_Z - 6,
            KEEP_ROOF + 3.4, CONCRETE_LIGHT, every=10.0, thickness=2.4)
    # the banner mast: the landmark you navigate a flag run by
    b.cyl([sx * FLAG_X, KEEP_ROOF + 13.0, 0], [1.6, 26.0, 1.6], STEEL_DARK,
          material="metal", collide=False)
    face_sign(b, sx * FLAG_X, KEEP_ROOF + 20.0, 6.5, 12.0, 14.0,
              "banner_%s" % team, "z+", colour)
    b.sphere([sx * FLAG_X, KEEP_ROOF + 27.0, 0], [3.0, 3.0, 3.0], neon,
             material="neon", collide=False)

    # ------------------------------------------------------- the rear yard
    inward_side = "x+" if sx < 0 else "x-"
    room_walls(b, rect(sx * yard0, sx * yard1, -34.0, 34.0), 3.0, PAD, 13.0,
               CONCRETE, doors={inward_side: [(12.0, 28.0, 11.0)]})
    slab(b, rect(sx * yard0, sx * yard1, -34.0, 34.0), 14.5, 1.5,
         CONCRETE_DARK, studs=True)
    strip_light(b, sx * (yard0 + yard1) / 2.0, 18.0, 11.4, 20.0, "x",
                "#9fe8ff")
    face_sign(b, sx * (yard0 + 0.5), PAD + 8.0, -26.0, 14.0, 6.0, "hazard",
              "x+" if sx < 0 else "x-", "#f2b01e")

    area = rect(sx * HATCH_STAIR_X[0], sx * HATCH_STAIR_X[1],
                HATCH_STAIR_Z[0], HATCH_STAIR_Z[1])
    flight(b, "z", area[3], area[2], area[0], area[1], PAD, TUNNEL_FLOOR,
           CONCRETE_DARK, fill=TUNNEL_FLOOR)
    shaft_lamp(b, area)

    # a resupply shed to break the yard up, plus crates in the courtyard
    room_walls(b, rect(sx * (yard0 + 0.5), sx * (yard1 - 0.5), 62.0, 96.0),
               3.0, PAD, 12.0, colour,
               doors={inward_side: [(70.0, 86.0, 10.0)]})
    slab(b, rect(sx * yard0, sx * yard1, 62.0, 96.0), 13.5, 1.5, dark,
         studs=True)
    b.box([sx * (yard0 + yard1) / 2.0, PAD + 6.0, 79.0], [16.0, 1.4, 20.0],
          LAMP, material="neon", collide=False)

    rng = random.Random(0x51E6E + sx)
    for _ in range(9):
        cx = rng.uniform(front_in + 8.0, KEEP_FRONT - 8.0)
        cz = rng.uniform(-side_in + 10.0, side_in - 10.0)
        if abs(cz) < 26.0 and cx < front_in + 24.0:
            continue                       # keep the gate lane walkable
        size = rng.uniform(6.0, 9.0)
        b.box([sx * cx, PAD + size / 2.0, cz], [size, size, size],
              rng.choice([WOOD, STEEL, dark]), studs=True)
    for sz in (-1, 1):
        b.box([sx * (front_in + 16.0), PAD + 4.0, sz * 46.0],
              [10.0, 8.0, 26.0], CONCRETE_DARK, studs=True)
        floodlight(b, sx * (front_in + 30.0), sz * 100.0, PAD, 22.0)
        floodlight(b, sx * (yard0 + 6.0), sz * 126.0, PAD, 20.0)

    b.marker("flag_%s" % team, {"p": [sx * FLAG_X, FLAG_Y, 0.0], "team": team})
    b.marker("base_%s" % team, {"p": [sx * FLAG_X, FLAG_Y, 0.0],
                                "radius": 16.0})


# ============================================================== the field
def _bunker(b: MapBuilder, sx: int, sz: int,
            holes: Sequence[Tuple[float, float, float, float]]
            ) -> List[Dict[str, Any]]:
    """A forward outpost: concrete box, firing slits, roof, tunnel shaft.

    These are the four points the whole midfield turns on.  Each one is a
    hard place to shoot into, has a climbable roof for anyone patient enough
    to take the outside ramp, and hides a stair down onto the spur tunnel --
    so holding a bunker is holding a door into the map's underside.
    """
    x0, x1 = BUNKER_X                       # 124 .. 176, measured from centre
    z0, z1 = BUNKER_Z                       # 88 .. 134
    inner_x, outer_x = sx * x0, sx * x1
    near_z, far_z = sz * z0, sz * z1

    def zs(a: float, c: float) -> Tuple[float, float]:
        return (min(sz * a, sz * c), max(sz * a, sz * c))

    def xsp(a: float, c: float) -> Tuple[float, float]:
        return (min(sx * a, sx * c), max(sx * a, sx * c))

    plate(b, carve(rect(inner_x, outer_x, near_z, far_z), holes), PAD, PAD,
          CONCRETE_DARK, studs=True)

    # the two walls facing the fight get a doorway; the two facing away get a
    # firing slit instead, so the inside is defensible without being a box
    # you can only be shot in
    area = rect(inner_x, outer_x, near_z, far_z)
    inner_side = "x+" if sx < 0 else "x-"
    outer_side = "x-" if sx < 0 else "x+"
    near_side = "z+" if sz < 0 else "z-"
    far_side = "z-" if sz < 0 else "z+"
    room_walls(b, area, 4.0, PAD, BUNKER_TOP, CONCRETE,
               sides=(inner_side, near_side),
               doors={inner_side: [zs(96.0, 112.0) + (10.0,)],
                      near_side: [xsp(146.0, 162.0) + (10.0,)]})
    for band in ((PAD, 7.0), (10.0, BUNKER_TOP)):
        room_walls(b, area, 4.0, band[0], band[1], CONCRETE,
                   sides=(outer_side, far_side))
    slab(b, area, BUNKER_ROOF, BUNKER_ROOF - BUNKER_TOP, CONCRETE_LIGHT,
         studs=True)

    # outside ramp onto the roof, landing flush with its inner edge
    ramp = zs(116.0, 128.0)
    flight(b, "x", sx * (x0 - 24.0), inner_x, ramp[0], ramp[1],
           TERRAIN_TOP, BUNKER_ROOF, CONCRETE_DARK, fill=TERRAIN_TOP)
    # roof parapet, open only where the ramp arrives
    room_walls(b, area, 3.0, BUNKER_ROOF, BUNKER_ROOF + 3.2, CONCRETE,
               doors={inner_side: [ramp + (BUNKER_ROOF,)]})
    crenels(b, "x", sz * (z1 - 1.5), *xsp(x0 + 8, x1 - 8),
            y=BUNKER_ROOF + 3.2, colour=CONCRETE_LIGHT, every=10.0,
            thickness=2.4)

    # the stair down to the spur, and the light that gives it away
    area = rect(sx * BUNKER_STAIR_X[0], sx * BUNKER_STAIR_X[1],
                *zs(TUN_SPUR_Z, TUN_SPUR_TOP))
    flight(b, "z", sz * TUN_SPUR_TOP, sz * TUN_SPUR_Z, area[0], area[1],
           PAD, TUNNEL_FLOOR, CONCRETE_DARK, fill=TUNNEL_FLOOR)
    shaft_lamp(b, area)
    strip_light(b, sx * (x0 + x1) / 2.0, sz * (z0 + 8.0), BUNKER_TOP - 1.6,
                40.0, "x")
    b.box([sx * (BUNKER_STAIR_X[0] + BUNKER_STAIR_X[1]) / 2.0, PAD + 0.45,
           sz * (TUN_SPUR_Z - 2.5)], [20.0, 0.9, 2.0], "#f2b01e",
          collide=False, decal="hazard")

    # crates inside, so the doorway is not a straight line through the room
    b.box([sx * (x0 + 34.0), PAD + 3.0, sz * (z0 + 8.0)], [8.0, 6.0, 8.0],
          WOOD, studs=True)

    yaw = sx * math.pi / 2.0
    spawns = []
    for i in range(4):
        px = sx * (x0 + 12.0 + (i % 2) * 40.0)
        pz = sz * (z0 + 12.0 + (i // 2) * 30.0)
        deploy_pad(b, px, pz, PAD, "#9fe8ff", 6.5)
        spawns.append({"p": [round(px, 2), round(PAD + 1.0, 2), round(pz, 2)],
                       "yaw": round(yaw, 3)})
    return spawns


def _containers(b: MapBuilder, sx: int, sz: int, rng: random.Random) -> None:
    """A freight stack either side of the road: hard cover you can climb.

    The two low boxes carry a third, and a wooden crate beside them is the
    step up -- six units onto the crate, six onto the stack, eight onto the
    top -- so the high ground is earned with jumps rather than handed over.
    """
    palette = [RUST, "#3f6f5a", "#7a6a3a", STEEL_DARK, "#8a3a32"]
    cx, cz = sx * FREIGHT_X, sz * FREIGHT_Z
    long_x = (34.0, 12.0, 13.0)
    long_z = (13.0, 12.0, 34.0)
    for ox, oz, oy, size in ((0.0, -13.0, 0.0, long_x),
                             (0.0, 0.0, 0.0, long_x),
                             (26.0, 3.0, 0.0, long_z),
                             (-26.0, 3.0, 0.0, long_z)):
        b.box([cx + ox, oy + size[1] / 2.0, cz + oz], list(size),
              rng.choice(palette), material="metal")
    b.box([cx, 16.0, cz - 6.5], [34.0, 8.0, 13.0], rng.choice(palette),
          material="metal")
    b.box([cx, 3.0, cz + 13.0], [10.0, 6.0, 10.0], WOOD, studs=True)


def _berm(b: MapBuilder, cx: float, cz: float, w: float, d: float,
          tiers: int = 4) -> None:
    """A terraced earthwork: relief you can always walk up, never jump-stuck."""
    for i in range(tiers):
        inset = i * 5.0
        b.box([cx, 1.0 + i * 2.0, cz], [w - inset * 2.0, 2.0, d - inset * 2.0],
              GRASS_DARK if i % 2 else GRASS_LIGHT, studs=True,
              material="grass")


def _outpost_tower(b: MapBuilder, sx: int, sz: int) -> None:
    """The blockhouse in the lane outside each compound wall."""
    x0, x1 = 330.0, 374.0
    z0, z1 = 152.0, 184.0

    def xsp(a: float, c: float) -> Tuple[float, float]:
        return (min(sx * a, sx * c), max(sx * a, sx * c))

    def zs(a: float, c: float) -> Tuple[float, float]:
        return (min(sz * a, sz * c), max(sz * a, sz * c))

    slab(b, rect(sx * x0, sx * x1, sz * z0, sz * z1), PAD, PAD, CONCRETE_DARK,
         studs=True)
    area = rect(sx * x0, sx * x1, sz * z0, sz * z1)
    inner_side = "x+" if sx < 0 else "x-"
    outer_side = "x-" if sx < 0 else "x+"
    room_walls(b, area, 4.0, PAD, 14.0, CONCRETE,
               doors={inner_side: [zs(z0 + 6.0, z0 + 20.0) + (10.0,)]})
    slab(b, area, 16.0, 2.0, CONCRETE_LIGHT, studs=True)
    ramp = zs(z0 + 22.0, z0 + 34.0)
    flight(b, "x", sx * (x1 + 26.0), sx * x1, ramp[0], ramp[1],
           TERRAIN_TOP, 16.0, CONCRETE_DARK, fill=TERRAIN_TOP)
    room_walls(b, area, 3.0, 16.0, 19.2, CONCRETE,
               doors={outer_side: [ramp + (16.0,)]})
    strip_light(b, sx * (x0 + x1) / 2.0, sz * (z0 + z1) / 2.0, 12.4,
                26.0, "x")
    # a lattice mast for the skyline -- scenery, never in the way
    mast = (sx * (x0 + x1) / 2.0, sz * (z0 + z1) / 2.0)
    b.cyl([mast[0], 34.0, mast[1]], [2.4, 34.0, 2.4], STEEL_DARK,
          collide=False, material="metal")
    for i in range(4):
        b.box([mast[0], 24.0 + i * 7.0, mast[1]],
              [9.0 - i * 1.4, 0.7, 9.0 - i * 1.4], STEEL, collide=False,
              material="metal")
    b.sphere([mast[0], 52.0, mast[1]], [2.4, 2.4, 2.4], "#ff7a3d",
             material="neon", collide=False)



def _cutting(b: MapBuilder, sx: int) -> None:
    """The revetment across the middle of one half of the midfield.

    A 196-unit run of open field between the plinth and a compound gate is a
    shooting gallery, so it gets a spine: a concrete bank twelve high with a
    single cut through it for the road.  Whoever holds the bank shoots down
    onto the gap; whoever wants the gap either takes the bank by one of its
    four ramps, goes round the ends, or goes under it.  It is the piece that
    turns the new distance into a fight rather than a walk.
    """
    x0, x1 = sx * CUTTING_X[0], sx * CUTTING_X[1]
    lo, hi = min(x0, x1), max(x0, x1)
    mid = (lo + hi) / 2.0

    for sz in (-1, 1):
        near, far = sz * CUTTING_GAP, sz * CUTTING_END
        z0, z1 = min(near, far), max(near, far)
        slab(b, (lo, hi, z0, z1), CUTTING_TOP, CUTTING_TOP, CONCRETE_DARK,
             studs=True)
        # a parapet on the face that looks back at the Relay, so the bank is
        # cover from one side and exposed from the other
        wall(b, "z", lo + 1.5, 3.0, z0, z1, CUTTING_TOP, CUTTING_TOP + 3.4,
             CONCRETE)
        crenels(b, "z", lo + 1.5, z0 + 6, z1 - 6, CUTTING_TOP + 3.4,
                CONCRETE_LIGHT, every=12.0, thickness=2.4)
        # Two ramps onto each wing: one climbed from the road end on the
        # Relay side, one from the flank end on the compound side.  Neither
        # team gets the bank for free and neither is locked out of it.
        # Written against the faces themselves rather than against whichever
        # of them happens to be the smaller x, so the red bank and the blue
        # bank are climbed from the same two places.
        for face, out, span in ((CUTTING_X[0], -1.0, (28.0, 40.0)),
                                (CUTTING_X[1], 1.0, (68.0, 80.0))):
            a, c = sz * span[0], sz * span[1]
            flight(b, "x", sx * (face + out * 26.0), sx * face,
                   min(a, c), max(a, c), TERRAIN_TOP, CUTTING_TOP,
                   CONCRETE_DARK, fill=TERRAIN_TOP)
        # the gap's edge is lit, because walking off a twelve-unit drop in
        # the dark is not an interesting way to lose a flag
        b.box([mid, CUTTING_TOP + 0.3, near - sz * 1.2],
              [hi - lo, 0.6, 2.4], "#f2b01e", collide=False, decal="hazard")
        floodlight(b, mid, near + sz * 9.0, TERRAIN_TOP, 22.0)
        # a pillbox on the shoulder of the cut, covering the road through it
        room_walls(b, rect(lo + 4.0, hi - 4.0, near + sz * 8.0,
                           near + sz * 34.0), 4.0, CUTTING_TOP,
                   CUTTING_TOP + 10.0, CONCRETE,
                   doors={("z+" if sz < 0 else "z-"): [(min(mid - 7, mid + 7),
                                                        max(mid - 7, mid + 7),
                                                        CUTTING_TOP + 8.0)]})
        slab(b, rect(lo + 4.0, hi - 4.0, near + sz * 8.0, near + sz * 34.0),
             CUTTING_TOP + 11.5, 1.5, CONCRETE_LIGHT, studs=True)
        strip_light(b, mid, near + sz * 21.0, CUTTING_TOP + 8.6, 22.0, "x")

    # the cut itself: kerbs either side of the road where it passes through
    for sz in (-1, 1):
        b.box([mid, 1.6, sz * (CUTTING_GAP + 1.5)], [hi - lo, 3.2, 3.0],
              CONCRETE, studs=True)


def _depot(b: MapBuilder, sx: int, sz: int, rng: random.Random,
           holes: Sequence[Tuple[float, float, float, float]]) -> None:
    """The last cover before a compound gate.

    South of the road it is a pump house -- a solid two-storey box with a
    roof you can fight from; north of it, an open-sided fuel depot whose
    tanks you can shelter behind but not on top of.  One of each per side,
    so the two approaches to a gate read differently and play differently.
    """
    x0, x1 = DEPOT_X
    z0, z1 = DEPOT_Z
    area = rect(sx * x0, sx * x1, sz * z0, sz * z1)
    inner = "x+" if sx < 0 else "x-"
    outer = "x-" if sx < 0 else "x+"
    near = "z+" if sz < 0 else "z-"

    def zs(a: float, c: float) -> Tuple[float, float]:
        return (min(sz * a, sz * c), max(sz * a, sz * c))

    def xsp(a: float, c: float) -> Tuple[float, float]:
        return (min(sx * a, sx * c), max(sx * a, sx * c))

    plate(b, carve(area, holes), PAD, PAD, CONCRETE_DARK, studs=True)
    if sz > 0:
        # ---- pump house: walls, a door on each of the two useful sides,
        # and an outside stair to a roof that overlooks the gate road
        room_walls(b, area, 4.0, PAD, DEPOT_TOP, CONCRETE_LIGHT,
                   doors={inner: [zs(z0 + 10.0, z0 + 26.0) + (11.0,)],
                          near: [xsp(x0 + 16.0, x1 - 16.0) + (11.0,)]})
        slab(b, area, DEPOT_ROOF, DEPOT_ROOF - DEPOT_TOP, CONCRETE, studs=True)
        stair = zs(z1 - 18.0, z1 - 4.0)
        flight(b, "x", sx * (x1 + 24.0), sx * x1, stair[0], stair[1],
               TERRAIN_TOP, DEPOT_ROOF, CONCRETE_DARK, fill=TERRAIN_TOP)
        room_walls(b, area, 3.0, DEPOT_ROOF, DEPOT_ROOF + 3.2, CONCRETE,
                   doors={outer: [stair + (DEPOT_ROOF,)]})
        strip_light(b, sx * (x0 + x1) / 2.0, sz * (z0 + z1) / 2.0,
                    DEPOT_TOP - 1.6, 42.0, "x")
        # the pumps themselves, and the hatch down into the cistern
        for i in range(2):
            b.cyl([sx * (x0 + 12.0 + i * 16.0), PAD + 4.0, sz * (z1 - 8.0)],
                  [9.0, 8.0, 9.0], STEEL, material="metal")
        b.box([sx * (PUMP_STAIR_X[0] + PUMP_STAIR_X[1]) / 2.0, PAD + 0.45,
               sz * (PUMP_STAIR_Z[0] - 2.5)], [20.0, 0.9, 2.0], "#f2b01e",
              collide=False, decal="hazard")
    else:
        # ---- fuel depot: a canopy on legs over four tanks.  No walls, so
        # it is cover you can shoot through the gaps of rather than a room
        for i in range(4):
            cx = sx * (x0 + 10.0 + i * 12.0)
            b.cyl([cx, PAD + 7.0, sz * (z0 + 18.0)], [11.0, 14.0, 11.0],
                  rng.choice([RUST, "#7a6a3a", STEEL_DARK]), material="metal")
            b.cyl([cx, PAD + 14.6, sz * (z0 + 18.0)], [4.0, 1.2, 4.0],
                  STEEL_DARK,
                  material="metal", collide=False)
        for i in range(4):
            b.box([sx * (x0 + 6.0 + i * 13.0), PAD + 8.0, sz * (z1 - 8.0)],
                  [3.0, 16.0, 3.0], STEEL_DARK, material="metal")
        slab(b, rect(sx * (x0 + 2.0), sx * (x1 - 2.0), sz * (z0 + 4.0),
                     sz * (z1 - 2.0)), DEPOT_TOP + 3.0, 1.6, STEEL,
             studs=False, material="metal")
        for i in range(3):
            b.box([sx * (x0 + x1) / 2.0, DEPOT_TOP + 1.4,
                   sz * (z0 + 10.0 + i * 16.0)], [x1 - x0 - 10.0, 0.6, 2.0],
                  LAMP, material="neon", collide=False)
        # low bunded wall round the tanks: waist-high cover, vaultable
        for at in (sz * (z0 + 2.0), sz * (z1 - 2.0)):
            wall(b, "x", at, 3.0, *xsp(x0 + 2.0, x1 - 2.0), y0=PAD,
                 y1=PAD + 5.0, colour=CONCRETE)
        wall(b, "z", sx * (x1 - 1.5), 3.0, *zs(z0 + 3.5, z1 - 3.5), y0=PAD,
             y1=PAD + 5.0, colour=CONCRETE)


def _treeline(b: MapBuilder, x0: float, z0: float, x1: float, z1: float,
              count: int, rng: random.Random, scale: float = 1.2) -> None:
    """A row of trees, planted to block a sight line rather than to decorate.

    Scattered trees are noise; a line of them across a lane is a wall you can
    shoot through the gaps of, which is the useful kind of cover.
    """
    for i in range(count):
        t = i / float(max(1, count - 1))
        x = x0 + (x1 - x0) * t + rng.uniform(-5.0, 5.0)
        z = z0 + (z1 - z0) * t + rng.uniform(-5.0, 5.0)
        if i % 3 == 2:
            b.tree(x, z, 0.0, scale * rng.uniform(0.85, 1.15), WOOD, "#2f6b42")
        else:
            b.pine(x, z, 0.0, scale * rng.uniform(0.9, 1.25), WOOD_DARK,
                   "#2a5f3c")


def _field(b: MapBuilder, holes: Sequence[Tuple[float, float, float, float]],
           rng: random.Random) -> Dict[str, List[Dict[str, Any]]]:
    """Everything between a compound wall and the Relay plinth."""
    outposts: Dict[str, List[Dict[str, Any]]] = {"red": [], "blue": []}

    # the road, and the two dirt tracks that flank it
    for sx in (-1, 1):
        lo, hi = sorted((sx * PLINTH_X, sx * BASE_FRONT))
        b.box([(lo + hi) / 2.0, 0.15, 0], [hi - lo, 0.3, ROAD_Z * 2.0],
              ASPHALT, collide=False)
        for sz in (-1, 1):
            b.box([(lo + hi) / 2.0, 0.12, sz * 121.0], [hi - lo, 0.24, 18.0],
                  DIRT, collide=False)
        for i in range(14):
            mark = lo + (hi - lo) * (i + 0.5) / 14.0
            b.box([mark, 0.32, 0], [9.0, 0.16, 1.8], ASPHALT_LINE,
                  collide=False)
    # the lane that runs outside each compound wall, front to back
    for sz in (-1, 1):
        b.box([0, 0.12, sz * ALLEY_Z], [MAP_X * 2 - WALL_T * 2, 0.24, 16.0],
              DIRT, collide=False)

    for sx in (-1, 1):
        team = "red" if sx < 0 else "blue"
        _cutting(b, sx)
        for sz in (-1, 1):
            outposts[team].extend(_bunker(b, sx, sz, holes))
            _containers(b, sx, sz, rng)
            _outpost_tower(b, sx, sz)
            _depot(b, sx, sz, rng, holes)
            _berm(b, sx * 150.0, sz * 178.0, 64.0, 22.0, 2)

            # Band one: sandbag nests stepping out from the plinth, so the
            # first eighty units of road are not a straight line of sight
            # from the Relay door to the Cutting.
            for i in range(3):
                b.box([sx * (128.0 + i * 16.0), 3.0, sz * (24.0 + i * 3.0)],
                      [16.0, 6.0, 5.0], SAND, studs=True)
            # staggered blast walls on the freight-yard flank
            for i in range(2):
                b.box([sx * (138.0 + i * 38.0), 3.5, sz * 88.0],
                      [24.0, 7.0, 4.0], CONCRETE_DARK, studs=True)
            # Band three: cover on the last run at the gate, offset from the
            # road so it breaks the lane without blocking it.
            for i in range(3):
                b.box([sx * (268.0 + i * 16.0), 3.0, sz * (26.0 + i * 5.0)],
                      [12.0, 6.0, 12.0], rng.choice([WOOD, CONCRETE_DARK]),
                      studs=True)
            # tree lines: one across the outer lane where it passes the
            # Cutting, one screening the bunker's open flank
            _treeline(b, sx * 190.0, sz * 160.0, sx * 246.0, sz * 196.0, 7, rng)
            _treeline(b, sx * 276.0, sz * 118.0, sx * 320.0, sz * 160.0, 6, rng)
            _treeline(b, sx * 124.0, sz * 118.0, sx * 176.0, sz * 152.0, 6, rng)

        # floodlights down the road: one pair per band, so the run from the
        # gate to the Relay is lit the whole way at dusk
        for x in (130.0, 178.0, 252.0, 296.0):
            floodlight(b, sx * x, -ROAD_Z - 8.0, 0.0, 24.0)
            floodlight(b, sx * x, ROAD_Z + 8.0, 0.0, 24.0)

    # scenery -- none of it in the way, all of it collidable only where it
    # reads as cover (trunks and rocks yes, canopies no)
    keep_out = [rect(-PLINTH_X - 6, PLINTH_X + 6, -PLINTH_Z - 6, PLINTH_Z + 6)]
    for sx in (-1, 1):
        keep_out.append(rect(sx * (BASE_FRONT - 6), sx * BASE_BACK,
                             -BASE_Z - 10, BASE_Z + 10))
        keep_out.append(rect(sx * (CUTTING_X[0] - 28), sx * (CUTTING_X[1] + 28),
                             -PLAY_Z, PLAY_Z))
        for sz in (-1, 1):
            keep_out.append(rect(sx * (BUNKER_X[0] - 30), sx * BUNKER_X[1],
                                 sz * (BUNKER_Z[0] - 6), sz * BUNKER_Z[1]))
            keep_out.append(rect(sx * (DEPOT_X[0] - 26), sx * (DEPOT_X[1] + 26),
                                 sz * (DEPOT_Z[0] - 8), sz * (DEPOT_Z[1] + 8)))
            keep_out.append(rect(sx * 118.0, sx * 200.0, sz * 24.0, sz * 96.0))
            keep_out.append(rect(sx * 200.0, sx * 290.0, sz * 148.0,
                                 sz * 190.0))

    def clear(x: float, z: float) -> bool:
        if abs(z) < ROAD_Z + 8.0:
            return False
        return not any(r[0] - 8 < x < r[1] + 8 and r[2] - 8 < z < r[3] + 8
                       for r in keep_out)

    placed = 0
    attempts = 0
    while placed < 86 and attempts < 1600:
        attempts += 1
        x = rng.uniform(-PLAY_X + 12, PLAY_X - 12)
        z = rng.uniform(-PLAY_Z + 12, PLAY_Z - 12)
        if not clear(x, z):
            continue
        roll = rng.random()
        if roll < 0.42:
            b.pine(x, z, 0.0, rng.uniform(0.9, 1.7), WOOD_DARK, "#2a5f3c")
        elif roll < 0.74:
            b.tree(x, z, 0.0, rng.uniform(0.9, 1.5), WOOD, "#2f6b42")
        else:
            b.rock(x, z, 0.0, rng.uniform(0.9, 2.1), ROCK)
        placed += 1

    # scuff marks, but only where there is actually paving to scuff: the two
    # compound aprons and the Relay plinth.  Each patch gets its own depth as
    # well as its own height, so two that overlap cannot share a surface
    paved = [rect(-PLINTH_X, -ANNEX_OUT, -PLINTH_Z, PLINTH_Z),
             rect(ANNEX_OUT, PLINTH_X, -PLINTH_Z, PLINTH_Z)]
    for side in (-1, 1):
        paved.append(rect(side * BASE_FRONT, side * BASE_BACK, -BASE_Z, BASE_Z))
    for i in range(26):
        area = paved[i % len(paved)]
        w, d = rng.uniform(16, 40), rng.uniform(14, 34)
        x = rng.uniform(area[0] + w / 2 + 4.0, area[1] - w / 2 - 4.0)
        z = rng.uniform(area[2] + d / 2 + 4.0, area[3] - d / 2 - 4.0)
        if any(h[0] < x + w / 2 and h[1] > x - w / 2 and
               h[2] < z + d / 2 and h[3] > z - d / 2 for h in holes):
            continue
        top = PAD + 0.10 + i * 0.004
        bottom = PAD - 0.3 - i * 0.004
        b.box([x, (top + bottom) / 2.0, z], [w, top - bottom, d],
              CONCRETE_DARK if i % 2 else "#8b9198", collide=False)

    # darker grass patches so the open ground is not a flat green sheet
    # every patch gets its own paper-thin height, so two that happen to
    # overlap can never end up fighting for the same pixels
    laid = 0
    tries = 0
    while laid < 58 and tries < 600:
        tries += 1
        x = rng.uniform(-PLAY_X, PLAY_X)
        z = rng.uniform(-PLAY_Z, PLAY_Z)
        w, d = rng.uniform(22, 58), rng.uniform(22, 58)
        if any(h[0] < x + w / 2 and h[1] > x - w / 2 and
               h[2] < z + d / 2 and h[3] > z - d / 2 for h in holes):
            continue                      # never hang a patch over a shaft
        top = 0.10 + laid * 0.004
        b.box([x, (top - 0.4) / 2.0, z], [w, top + 0.4, d],
              GRASS_DARK if laid % 2 else GRASS_LIGHT, collide=False)
        laid += 1
    # shallow standing water in the corners of the outer lanes
    for sx in (-1, 1):
        for sz in (-1, 1):
            b.water(sx * 356.0, sz * 186.0, 84.0, 18.0, 0.35, WATER)
    return outposts


# ============================================================= the tunnels
def _tunnels(b: MapBuilder, holes: Sequence[Tuple[float, float, float, float]]
             ) -> None:
    """The undercroft and the two corridors that feed it.

    Nothing down here ever meets the terrain slab: the void stops at
    ``TUNNEL_CEIL`` and the ground starts there, so the only way between the
    two worlds is one of the six stair shafts -- which is exactly what makes
    a tunnel worth watching.
    """
    main_lo, main_hi = TUN_MAIN_Z
    spur_lo, spur_hi = TUN_SPUR_X

    def ceiling(area: Tuple[float, float, float, float]) -> None:
        """Rock overhead, not the underside of a field.

        The terrain slab would otherwise be the tunnel roof, and it is grass
        all the way through -- which from below reads as standing under a
        lawn.  This is the same rectangle a shaft's hole is cut from, so the
        stairwells stay open.
        """
        plate(b, carve(area, holes), TUNNEL_CEIL, 1.2, ROCK_DARK)

    # ------------------------------------------------------- the undercroft
    slab(b, rect(-UNDER_X, UNDER_X, -UNDER_Z, UNDER_Z), TUNNEL_FLOOR,
         TUNNEL_FLOOR - TUNNEL_BASE, CONCRETE_DARK, studs=True)
    ceiling(rect(-UNDER_X, UNDER_X, -UNDER_Z, UNDER_Z))
    for sz in (-1, 1):
        wall(b, "x", sz * (UNDER_Z + 1.5), 3.0, -UNDER_X - 3.0, UNDER_X + 3.0,
             TUNNEL_FLOOR, TUNNEL_CEIL, ROCK_DARK)
    for sx in (-1, 1):
        wall(b, "z", sx * (UNDER_X + 1.5), 3.0, -UNDER_Z, UNDER_Z,
             TUNNEL_FLOOR, TUNNEL_CEIL, ROCK_DARK,
             gaps=[(main_lo, main_hi, TUNNEL_CEIL)])
        for sz in (-1, 1):
            b.box([sx * 62.0, (TUNNEL_FLOOR + TUNNEL_CEIL) / 2.0, sz * 26.0],
                  [5.0, TUNNEL_CEIL - TUNNEL_FLOOR, 5.0], CONCRETE_DARK)
    # These run down the hall well clear of the stair wells and the drains.
    # A tube that crosses an open shaft is a tube hanging in mid-air when you
    # look down it from the atrium.
    for sz in (-1, 1):
        strip_light(b, 0, sz * 56.0, TUNNEL_CEIL - 1.4, 150.0, "x", "#9fe8ff")
    b.box([0, TUNNEL_FLOOR + 0.3, 0], [40.0, 0.6, 40.0], "#f5c518",
          collide=False, material="neon")

    for sx in (-1, 1):
        def xs(a: float, c: float) -> Tuple[float, float]:
            return (min(sx * a, sx * c), max(sx * a, sx * c))

        cis_lo, cis_hi = CISTERN_X
        cis_z0, cis_z1 = CISTERN_Z

        # ------------------------------------------------ the main corridor
        # It runs the whole new length of the valley in three pieces: hall to
        # cistern, the cistern itself, and cistern to hatch.  Splitting it
        # there is what keeps the cistern's floor and the corridor's from
        # both claiming the same surface.
        for lo, hi in ((UNDER_X, cis_lo), (cis_hi, HATCH_X[0])):
            slab(b, rect(sx * lo, sx * hi, main_lo, main_hi), TUNNEL_FLOOR,
                 TUNNEL_FLOOR - TUNNEL_BASE, CONCRETE_DARK, studs=True)
            ceiling(rect(sx * lo, sx * hi, main_lo, main_hi))
            for at in (main_lo - 1.5, main_hi + 1.5):
                wall(b, "x", at, 3.0, *xs(lo + 3.0, hi - 3.0),
                     y0=TUNNEL_FLOOR, y1=TUNNEL_CEIL, colour=ROCK_DARK,
                     gaps=[xs(spur_lo - 3.0, spur_hi + 3.0) + (TUNNEL_CEIL,)])
        for i in range(11):
            strip_light(b, sx * (104.0 + i * 30.0), (main_lo + main_hi) / 2.0,
                        TUNNEL_CEIL - 1.4, 26.0, "x", "#9fe8ff")
        for i in range(8):
            x = sx * (106.0 + i * 38.0)
            if abs(x) > cis_lo - 8.0 and abs(x) < cis_hi + 8.0:
                continue
            b.box([x, TUNNEL_FLOOR + 2.5, main_lo + 3.0], [5.0, 5.0, 5.0],
                  WOOD, studs=True)

        # ------------------------------------------------------- the spur
        for lo, hi in ((-(TUN_SPUR_TOP + 2.0), main_lo),
                       (main_hi, TUN_SPUR_TOP + 2.0)):
            slab(b, rect(sx * spur_lo, sx * spur_hi, lo, hi), TUNNEL_FLOOR,
                 TUNNEL_FLOOR - TUNNEL_BASE, CONCRETE_DARK, studs=True)
            ceiling(rect(sx * spur_lo, sx * spur_hi, lo, hi))
        for at in (spur_lo - 1.5, spur_hi + 1.5):
            wall(b, "z", sx * at, 3.0, -(TUN_SPUR_TOP + 5.0),
                 TUN_SPUR_TOP + 5.0, TUNNEL_FLOOR, TUNNEL_CEIL, ROCK_DARK,
                 gaps=[(main_lo - 3.0, main_hi + 3.0, TUNNEL_CEIL)])
        for sz in (-1, 1):
            wall(b, "x", sz * (TUN_SPUR_TOP + 3.5), 3.0, *xs(spur_lo, spur_hi),
                 y0=TUNNEL_FLOOR, y1=TUNNEL_CEIL, colour=ROCK_DARK)
            for i in range(4):
                strip_light(b, sx * (spur_lo + spur_hi) / 2.0,
                            sz * (42.0 + i * 22.0), TUNNEL_CEIL - 1.4, 22.0,
                            "z", "#9fe8ff")

        # ----------------------------------------------------- the cistern
        # A flooded hall half way along each corridor, with its own way up
        # into the pump house on the surface.  It is the reason the tunnel
        # is worth the extra distance: a third door onto the map, and a room
        # big enough to be worth fighting over on the way past.
        slab(b, rect(sx * cis_lo, sx * cis_hi, cis_z0, cis_z1), TUNNEL_FLOOR,
             TUNNEL_FLOOR - TUNNEL_BASE, CONCRETE_DARK, studs=True)
        ceiling(rect(sx * cis_lo, sx * cis_hi, cis_z0, cis_z1))
        for at, gap in ((cis_lo - 1.5, True), (cis_hi + 1.5, True)):
            wall(b, "z", sx * at, 3.0, cis_z0, cis_z1, TUNNEL_FLOOR,
                 TUNNEL_CEIL, ROCK_DARK,
                 gaps=[(main_lo, main_hi, TUNNEL_CEIL)] if gap else [])
        for at in (cis_z0 - 1.5, cis_z1 + 1.5):
            wall(b, "x", at, 3.0, *xs(cis_lo - 3.0, cis_hi + 3.0),
                 y0=TUNNEL_FLOOR, y1=TUNNEL_CEIL, colour=ROCK_DARK)
        for i in range(3):
            for sz in (-1, 1):
                b.box([sx * (cis_lo + 14.0 + i * 16.0),
                       (TUNNEL_FLOOR + TUNNEL_CEIL) / 2.0,
                       (cis_z0 + cis_z1) / 2.0 + sz * 32.0],
                      [5.0, TUNNEL_CEIL - TUNNEL_FLOOR, 5.0], CONCRETE_DARK)
        # standing water in the middle, with a dry walkway round the edge
        b.water(sx * (cis_lo + cis_hi) / 2.0, (cis_z0 + cis_z1) / 2.0,
                (cis_hi - cis_lo) - 22.0, (cis_z1 - cis_z0) - 26.0,
                TUNNEL_FLOOR + 0.6, WATER)
        for i in range(5):
            strip_light(b, sx * (cis_lo + cis_hi) / 2.0,
                        cis_z0 + 12.0 + i * 24.0, TUNNEL_CEIL - 1.4, 40.0,
                        "x", "#9fe8ff")
        for i in range(2):
            b.box([sx * (cis_lo + 8.0), TUNNEL_FLOOR + 3.0,
                   cis_z0 + 10.0 + i * 12.0], [8.0, 6.0, 8.0], WOOD,
                  studs=True)
        # the stair up into the pump house
        shaft = rect(sx * PUMP_STAIR_X[0], sx * PUMP_STAIR_X[1],
                     PUMP_STAIR_Z[0], PUMP_STAIR_Z[1])
        flight(b, "z", shaft[2], shaft[3], shaft[0], shaft[1], TUNNEL_FLOOR,
               PAD, CONCRETE_DARK, fill=TUNNEL_FLOOR)
        shaft_lamp(b, shaft)

        # --------------------------------------------- the hatch chamber
        h0, h1 = HATCH_X
        hz0, hz1 = HATCH_Z
        slab(b, rect(sx * h0, sx * h1, hz0, hz1), TUNNEL_FLOOR,
             TUNNEL_FLOOR - TUNNEL_BASE, CONCRETE_DARK, studs=True)
        ceiling(rect(sx * h0, sx * h1, hz0, hz1))
        wall(b, "z", sx * (h0 - 1.5), 3.0, hz0, hz1, TUNNEL_FLOOR, TUNNEL_CEIL,
             ROCK_DARK, gaps=[(main_lo, main_hi, TUNNEL_CEIL)])
        wall(b, "z", sx * (h1 + 1.5), 3.0, hz0, hz1, TUNNEL_FLOOR, TUNNEL_CEIL,
             ROCK_DARK)
        for at in (hz0 - 1.5, hz1 + 1.5):
            wall(b, "x", at, 3.0, *xs(h0 - 3.0, h1 + 3.0), y0=TUNNEL_FLOOR,
                 y1=TUNNEL_CEIL, colour=ROCK_DARK)
        strip_light(b, sx * (h0 + h1) / 2.0, -30.0, TUNNEL_CEIL - 1.4, 24.0,
                    "x", "#9fe8ff")
        b.box([sx * (h0 + h1) / 2.0, TUNNEL_FLOOR + 3.0, -31.0],
              [10.0, 6.0, 6.0], WOOD, studs=True)

# ================================================================== build
def shaft_holes() -> List[Tuple[float, float, float, float]]:
    """Every rectangle that has to be missing from the ground and the pads.

    One list, used by the terrain, the Relay plinth, both compound aprons and
    all four bunker floors, so a shaft and the hole it needs can never drift
    apart no matter which of them is edited.
    """
    holes: List[Tuple[float, float, float, float]] = []
    for sx in (-1, 1):
        holes.append(rect(sx * HATCH_STAIR_X[0], sx * HATCH_STAIR_X[1],
                          HATCH_STAIR_Z[0], HATCH_STAIR_Z[1]))
        holes.append(rect(sx * RELAY_STAIR_X[0], sx * RELAY_STAIR_X[1],
                          RELAY_STAIR_Z[0], RELAY_STAIR_Z[1]))
        for sz in (-1, 1):
            holes.append(rect(sx * DRAIN_X[0], sx * DRAIN_X[1],
                              sz * DRAIN_Z[0], sz * DRAIN_Z[1]))
            holes.append(rect(sx * BUNKER_STAIR_X[0], sx * BUNKER_STAIR_X[1],
                              sz * TUN_SPUR_Z, sz * TUN_SPUR_TOP))
        holes.append(rect(sx * PUMP_STAIR_X[0], sx * PUMP_STAIR_X[1],
                          PUMP_STAIR_Z[0], PUMP_STAIR_Z[1]))
    return holes


def build() -> Dict[str, Any]:
    b = MapBuilder(
        "Ironvale Relay",
        sky={"top": "#22406f", "horizon": "#9b86a0",
             "sun": [0.2, 0.62, 0.76], "clouds": 0.5, "tint": "#ffc89a"},
        ambient="#6b7d95", fog=880.0, ground=GRASS)
    rng = random.Random(20260920)
    holes = shaft_holes()

    # ------------------------------------------------------------ terrain
    plate(b, carve(rect(-MAP_X, MAP_X, -MAP_Z, MAP_Z), holes), TERRAIN_TOP,
          TERRAIN_TOP - TERRAIN_BOTTOM, GRASS, studs=True, material="grass")
    for sx in (-1, 1):
        wall(b, "z", sx * (PLAY_X + WALL_T / 2.0), WALL_T, -MAP_Z, MAP_Z,
             TERRAIN_TOP, 40.0, ROCK)
    for sz in (-1, 1):
        wall(b, "x", sz * (PLAY_Z + WALL_T / 2.0), WALL_T, -PLAY_X, PLAY_X,
             TERRAIN_TOP, 40.0, ROCK)
    # a ragged rock skyline on top of the boundary, so the edge of the world
    # reads as a valley rim rather than as a wall
    for sx in (-1, 1):
        for i in range(13):
            z = -MAP_Z + 18.0 + i * (MAP_Z * 2.0 - 36.0) / 12.0
            h = rng.uniform(16.0, 42.0)
            b.box([sx * (PLAY_X + WALL_T / 2.0 + rng.uniform(-3, 3)),
                   40.0 + h / 2.0, z], [WALL_T + 6.0, h, 34.0], ROCK_DARK,
                  collide=False)
    for sz in (-1, 1):
        for i in range(25):
            x = -PLAY_X + 16.0 + i * (PLAY_X * 2.0 - 32.0) / 24.0
            h = rng.uniform(14.0, 38.0)
            b.box([x, 40.0 + h / 2.0,
                   sz * (PLAY_Z + WALL_T / 2.0 + rng.uniform(-3, 3))],
                  [36.0, h, WALL_T + 6.0], ROCK_DARK, collide=False)

    # -------------------------------------------------------------- build
    _relay(b, holes)
    _base(b, "red", -1, holes)
    _base(b, "blue", 1, holes)
    outposts = _field(b, holes, rng)
    _tunnels(b, holes)

    for team, pads in outposts.items():
        b.marker("outpost_%s" % team, pads)
    b.marker("mode", "ctf")
    b.marker("captures_to_win", 5)
    b.marker("relay", {"radius": PLINTH_X, "name": "The Relay"})
    b.kill_y = KILL_Y
    return b.to_dict()
