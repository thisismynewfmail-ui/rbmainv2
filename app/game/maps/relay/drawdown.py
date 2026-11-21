"""Drawdown -- a reservoir drained to the bottom in a drought.

Forty years under water, and now Lower Ashby is back: its high street, its
pub, its mill, its two chapels on their hills -- grey with silt, roofs gone,
boats stranded in the lanes.  Both teams muster at the foot of the
reservoir's valve tower, which stands in the middle of the old village;
the flags are in the chapels at either end of the valley.

Layout (red to the west; mirrored about x = 0)::

      z +196  ~~~~~ the old shorelines: six steps of bathtub rings up the bank ~~~~~
      z +110  .................. THE BARN (outpost) ...... a boat in the lane ......
      z  +40  CHAPEL HILL -- HIGH STREET: the Drowned Bell, cottages -- VALVE TOWER
      z   -10 ============== the culvert, under it all, into the valve chamber ======
      z  -55  ~~~~~~~~~~~~ the dry river, under three stone bridges ~~~~~~~~~~~~~~~
      z  -90  .................. THE MILL, cottages ....... PUMP SHED (outpost) .....
      z -196  ~~~~~ the bank again ~~~~~

The culvert is the runner's road: a concrete pipe under the lakebed from a
stair in each chapel's crypt to the valve chamber under the tower.  The
dry river is the low road across the south of the village.
"""
from __future__ import annotations

import math
import random

from . import kit
from .kit import (CONCRETE, CONCRETE_DARK, CONCRETE_LIGHT, STEEL, STEEL_DARK, Half, carve,
                  flight, halves, holed_wall, rect, room_walls, slab, strip_light)

HALF = (320.0, 196.0)
SKY = {"top": "#7e868e", "horizon": "#cfc8b8", "sun": [0.3, 0.6, 0.5],
       "clouds": 0.95, "tint": "#e8e0d0"}
AMBIENT = "#a09a8c"
GROUND = "#8a7a5a"
FOG = 720.0

MUD = "#8a7a5a"
MUD_DARK = "#74664a"
MUD_LIGHT = "#a0906c"
SILT = "#b0a488"
STONE = "#9a968a"
STONE_DARK = "#7e7a70"
STONE_LIGHT = "#b4b0a4"
SLATE = "#4a4e56"
COBBLE = "#86827a"
RUST = "#8a5a3a"
WEED = "#5a6a3a"

TOWER = 13.0                        # the valve tower's half width
ANNEX = (13.0, 41.0, -16.0, 16.0)   # a muster annex (x magnitudes)
ANNEX_ROOF = 13.2
BALCONY = 21.0
CULVERT_Z = (-16.0, -4.0)
CULVERT_FLOOR = -8.0
CULVERT_X = 250.0
WELL_TOWER = (-5.0, 5.0, -4.0, 8.0)         # the stair up from the valve chamber
WELL_CRYPT = (238.0, 250.0)                 # a crypt stair's x span (magnitudes)
RIVER_Z = (-62.0, -48.0)
RIVER_X = 252.0
RIVER_DEPTH = 7.0
CHAPEL = (232.0, 296.0, -18.0, 18.0)
HILL_Y = 6.0
FLAG_X = 270.0


def build(b: kit.RelayArea) -> None:
    rng = random.Random(0xD8A1)
    b.relay("the Valve Tower", 50.0)
    b.intro = ["Drawdown -- the reservoir is dry, and Lower Ashby is back.",
               "Muster at the foot of the valve tower; the flags are in the drowned "
               "chapels on their hills at either end of the valley.",
               "The culvert runs under the lakebed from each chapel's crypt to the "
               "valve chamber under the tower."]
    b.extra.update({"accent": "#d8c89a", "weather": "dust"})
    culvert = rect(-CULVERT_X, CULVERT_X, CULVERT_Z[0], CULVERT_Z[1])
    river = rect(-RIVER_X, RIVER_X, RIVER_Z[0], RIVER_Z[1])
    tower_well = rect(*WELL_TOWER)
    crypts = [h.r(WELL_CRYPT[0], WELL_CRYPT[1], CULVERT_Z[1], CULVERT_Z[1] + 14.0)
              for h in halves(b)]
    kit.ground(b, MUD, soil="#5a4a32", holes=[culvert, river, tower_well] + crypts)
    _culvert(b, culvert, tower_well, crypts)
    _river(b, river)
    _banks(b)
    _tower(b)
    for h in halves(b):
        _hill(b, h, crypts)
        _chapel(b, h)
        _village(b, h)
        _outposts(b, h)
        _lakebed(b, h)
    _bridges(b)
    _street(b)
    _easter_eggs(b)
    _edge(b, rng)
    _landmarks(b)


# ================================================================== culvert
def _culvert(b: kit.RelayArea, culvert, tower_well, crypts) -> None:
    """A concrete pipe under the lakebed: a lid of silt over it, the odd
    lamp, rungs and silt inside, a stair up into the tower and one into each
    chapel's crypt."""
    kit.channel(b, culvert, -CULVERT_FLOOR, "#6a6a62", wall_c="#5a5a54", studs=True,
                openings={"z+": [(tower_well[0], tower_well[1])] +
                          [(w[0], w[1]) for w in crypts]})
    x0, x1, z0, z1 = culvert
    # the lid: the lakebed over the pipe, everywhere nothing else covers it
    covered = [rect(-CULVERT_X - 1.0, -204.0, z0, z1), rect(204.0, CULVERT_X + 1.0, z0, z1)]
    lid = carve(culvert, covered + [tower_well])
    kit.plate(b, lid, 0.0, 0.6, MUD, studs=True)
    # lamps along it, silt drifts on its floor, a grate at each end
    zc = (z0 + z1) / 2.0
    for x in range(-232, 240, 24):
        if abs(x) < 10:
            continue
        ceiling = 0.0 if abs(x) > 204 else -0.6
        strip_light(b, float(x), zc, ceiling, 6.0, "z", "#ffd890" if x % 48 else "#9fe8ff")
    for x in (-160.0, -70.0, 70.0, 160.0):
        b.box([x, CULVERT_FLOOR + 0.5, z0 + 3.0], [12.0, 1.0, 5.0], SILT, studs=True)
    for sx in (-1, 1):
        b.box([sx * (CULVERT_X - 0.6), CULVERT_FLOOR + 3.5, zc], [1.2, 7.0, 12.0], RUST,
              material="metal", alpha=0.7)
    # the valve chamber's stair, up into the tower
    flight(b, "z", tower_well[2], tower_well[3], tower_well[0], tower_well[1], CULVERT_FLOOR,
           0.0, CONCRETE, fill=CULVERT_FLOOR)
    # the crypt stairs, up into each chapel (inside the hill)
    for well in crypts:
        flight(b, "z", well[2], well[3], well[0], well[1], CULVERT_FLOOR, HILL_Y, STONE_DARK,
               fill=CULVERT_FLOOR)


# ==================================================================== river
def _river(b: kit.RelayArea, river) -> None:
    """The river the reservoir drowned, dry again: a cracked bed of silt,
    stones, a rusted shopping trolley, a way down at each end."""
    kit.channel(b, river, RIVER_DEPTH, SILT, wall_c="#5a4a32", studs=True)
    x0, x1, z0, z1 = river
    zc = (z0 + z1) / 2.0
    y = -RIVER_DEPTH
    for k in range(11):
        x = -230.0 + k * 46.0
        b.box([x, y + 0.04, zc + (k % 3 - 1) * 2.0], [1.0, 0.08, z1 - z0 - 3.0], MUD_DARK,
              collide=False)
    for sx in (-1, 1):
        flight(b, "x", sx * (x1 - 24.0), sx * x1, z0, z1, y, 0.0, STONE_DARK, fill=y)
        for x, z, s in ((60.0, -58.0, 1.0), (190.0, -52.0, 1.3), (100.0, -51.0, 0.8)):
            kit.boulder(b, sx * x, z, y, s, STONE)
        # a stone stair down the river's north bank, by each outer bridge
        flight(b, "x", sx * 104.0, sx * 84.0, z1 - 5.0, z1, -1.8, y, STONE, fill=y)


# ==================================================================== banks
def _banks(b: kit.RelayArea) -> None:
    """The reservoir's banks: six steps of old shoreline north and south,
    each ring a different stain."""
    hx, hz = HALF
    colours = [MUD_DARK, "#7a6a4a", MUD, "#9a8a62", MUD_LIGHT, "#a8a080"]
    for sz in (-1, 1):
        tiers = []
        for k in range(6):
            near = 140.0 + k * 9.0
            tiers.append([rect(-hx, hx, min(sz * near, sz * hz), max(sz * near, sz * hz))])
        kit.tier_stack(b, tiers, 0.0, [2.0], colours, studs=True)
    # a jetty that used to reach the water, high and dry on the third ring
    for sx in (-1, 1):
        x = sx * 120.0
        b.box([x, 6.0 + 0.3, 166.0 - 9.0], [6.0, 0.6, 16.0], "#7a5a3a", studs=True)
        for dz in (-6.0, 0.0):
            b.cyl([x - 2.4, 3.0, 154.0 + dz], [0.8, 6.0, 0.8], "#5a3a22")
            b.cyl([x + 2.4, 3.0, 154.0 + dz], [0.8, 6.0, 0.8], "#5a3a22")


# ==================================================================== tower
def _tower(b: kit.RelayArea) -> None:
    """The valve tower: a concrete shaft in the middle of the reservoir, a
    muster annex bolted on each side, a balcony round it at the old top
    water level, and the valve house on top."""
    t = TOWER
    top = 52.0
    room_walls(b, rect(-t, t, -t, t), 3.0, 0.0, 16.0, CONCRETE,
               doors={"x-": [(-6.0, 6.0, 9.0)], "x+": [(-6.0, 6.0, 9.0)],
                      "z+": [(-5.0, 5.0, 9.0)], "z-": [(-5.0, 5.0, 9.0)]})
    slab(b, rect(-t, t, -t, t), 17.4, 1.4, CONCRETE_DARK)
    # the shaft above the base room, solid, with its bands of high water marks
    b.box([0.0, 17.4 + (top - 17.4) / 2.0, 0.0], [2 * t, top - 17.4, 2 * t], CONCRETE_LIGHT)
    for k, y in enumerate((24.0, 30.0, 36.0, 42.0)):
        b.box([0.0, y, 0.0], [2 * t + 0.4, 0.8, 2 * t + 0.4], ["#6a7a6a", "#7a7a6a",
                                                                 "#8a7a6a", "#9a8a72"][k],
              collide=False)
    # the balcony at the old top water level, railed, and the stairs to it
    ring = rect(-t - 6.0, t + 6.0, -t - 6.0, t + 6.0)
    kit.plate(b, carve(ring, [rect(-t, t, -t, t)]), BALCONY, 1.2, CONCRETE_DARK, studs=True)
    room_walls(b, ring, 1.0, BALCONY, BALCONY + 3.0, STEEL,
               doors={"x-": [(8.0, 16.0, BALCONY + 3.0)], "x+": [(8.0, 16.0, BALCONY + 3.0)]},
               material="metal")
    # the valve house on top, and its crane
    b.box([0.0, top + 5.0, 0.0], [20.0, 10.0, 20.0], "#c8c0a8")
    b.box([0.0, top + 10.6, 0.0], [23.0, 1.2, 23.0], SLATE)
    b.box([0.0, top + 18.0, 0.0], [1.6, 14.0, 1.6], RUST, material="metal", collide=False)
    b.box([8.0, top + 24.6, 0.0], [18.0, 1.4, 1.4], RUST, material="metal", collide=False)
    b.box([16.0, top + 20.0, 0.0], [0.3, 8.0, 0.3], "#2a2a2a", collide=False)
    kit.board_letters(b, 0.0, 12.0, t, "ASHBY WATER BOARD", 1.8, CONCRETE, "#3a3e46",
                      solid=False)
    strip_light(b, 0.0, 0.0, 16.0, 18.0, "z", "#ffe2a8")
    # the great valve wheels in the base room, either side of the stair
    for sx in (-1, 1):
        b.cyl([sx * 8.0, 3.0, -8.0], [1.6, 6.0, 1.6], STEEL_DARK, material="metal")
        b.cyl([sx * 8.0, 6.6, -8.0], [6.0, 1.2, 6.0], RUST, material="metal", collide=False)
    kit.hazard_rim(b, rect(*WELL_TOWER), 0.0)
    for h in halves(b):
        x0, x1, z0, z1 = ANNEX
        area = h.r(x0, x1, z0, z1)
        room_walls(b, area, 2.0, 0.0, ANNEX_ROOF - 1.2, "#b0aa98",
                   doors={h.outward: [(-7.0, 7.0, 10.0)]}, sides=(h.outward, "z-", "z+"))
        slab(b, area, ANNEX_ROOF, 1.2, CONCRETE_DARK, studs=True)
        for i in range(3):
            for j in (-1, 1):
                b.muster(h.team, h.x(18.0 + 6.0 * i), 0.0, j * 8.5, h.yaw_out, size=4.6)
        h.sign(x1 - 2.36, 9.4, 0.0, 10.0, 3.0, "sign_%s" % h.team, "x+")
        strip_light(b, h.x(27.0), 0.0, ANNEX_ROOF - 1.2, 26.0, "z", "#ffe2a8")
        # the stair up the annex's north side to its roof, then on up to the balcony
        h.flight_x(x1 + 14.0, x1, z1, z1 + 8.0, 0.0, ANNEX_ROOF, STONE_DARK, fill=0.0)
        h.slab(x1 - 10.0, x1, z1, z1 + 8.0, ANNEX_ROOF, 1.2, CONCRETE_DARK, studs=True)
        h.flight_x(x1 - 10.0, t + 6.0, 8.0, 16.0, ANNEX_ROOF, BALCONY, STONE_DARK,
                   fill=ANNEX_ROOF)
        # cover by the annex door
        h.box(x1 + 6.0, 2.0, -12.0, 6.0, 4.0, 6.0, STONE_DARK, studs=True)
        h.box(x1 + 6.0, 1.6, 12.0, 5.0, 3.2, 5.0, RUST, studs=True)


# ===================================================================== hills
def _hill(b: kit.RelayArea, h: Half, crypts) -> None:
    """The chapel's hill: three steps of drowned turf up to the chapel."""
    cx = 262.0
    tiers = []
    for k in range(3):
        f = 1.0 - k * 0.16
        pieces = []
        for r in kit.ellipse_rects(h.x(cx), 0.0, 62.0 * f, 84.0 * f, band=6.0):
            r = (max(r[0], -HALF[0]), min(r[1], HALF[0]), r[2], r[3])
            pieces.extend(carve(r, crypts))
        tiers.append(pieces)
    kit.tier_stack(b, tiers, 0.0, [2.0], [WEED, MUD_LIGHT, "#6a7a4a"], studs=True)
    # gravestones on the hill's lower step, mossy
    for k in range(10):
        a = k * 0.6 - 3.0
        x, z = cx + math.cos(a) * 44.0, math.sin(a) * 58.0
        if abs(z) < 30.0:
            continue
        h.box(x, 2.0 + 1.6, z, 3.0, 3.2, 1.0, STONE_LIGHT if k % 2 else STONE)


def _chapel(b: kit.RelayArea, h: Half) -> None:
    """A drowned chapel on its hill: the nave roofless, its rafters bare,
    a steeple at the far end, the flag before the altar -- and the crypt
    stair down to the culvert."""
    x0, x1, z0, z1 = CHAPEL
    y = HILL_Y
    top = y + 14.0
    area = h.r(x0, x1, z0, z1)
    holed = {h.inward: [(-6.0, 6.0, y + 10.0)],
             "z-": [(*h.xs(258.0, 268.0), y + 9.0)], "z+": [(*h.xs(258.0, 268.0), y + 9.0)],
             h.outward: [(-5.0, 5.0, y + 8.0)]}
    room_walls(b, area, 3.0, y, top, STONE, doors=holed)
    # windows: arches of light along the nave (holes high in the walls)
    for xx in (244.0, 282.0):
        for z in (z0 + 1.5, z1 - 1.5):
            h.box(xx, y + 9.5, z, 4.0, 5.0, 3.2, "#c8d8e8", collide=False, material="glass",
                  alpha=0.35)
    # the rafters, bare, over the nave
    for xx in range(int(x0) + 6, int(x1), 8):
        h.box(float(xx), top + 0.6, 0.0, 1.2, 1.2, z1 - z0, "#4a3a2a")
    # the steeple at the far end, solid, its bell still up there
    sx0, sx1 = x1, x1 + 14.0
    h.box((sx0 + sx1) / 2.0, y + 17.0, 0.0, sx1 - sx0, 34.0, 14.0, STONE_DARK)
    h.cone((sx0 + sx1) / 2.0, y + 34.0 + 9.0, 0.0, 14.0, 18.0, 14.0, SLATE, collide=False)
    h.box((sx0 + sx1) / 2.0 - 7.06 * 1.0, y + 26.0, 0.0, 0.12, 5.0, 4.0, "#2a2a2a",
          collide=False)
    # the flag before the altar
    top_y = kit.pedestal(b, h.x(FLAG_X), 0.0, y, h.colour, h.neon, base=STONE_DARK)
    b.flag(h.team, h.x(FLAG_X), top_y, 0.0)
    kit.banner_mast(b, h.x(x1 - 6.0), 24.0, y, 26.0, h.team, h.inward)
    # pews, silted up: cover in the chancel
    for xx in (287.0, 291.0):
        for z in (-9.0, 9.0):
            h.box(xx, y + 1.0, z, 2.0, 2.0, 7.0, "#6a5a42", studs=True)
    # the crypt stair: walled round on three sides, open at its head
    wx0, wx1 = WELL_CRYPT
    wz0, wz1 = CULVERT_Z[1], CULVERT_Z[1] + 14.0
    h.box(wx0 - 0.6, y + 1.5, (wz0 + wz1) / 2.0 - 0.6, 1.2, 3.0, wz1 - wz0 + 1.2, STONE_DARK)
    h.box(wx1 + 0.6, y + 1.5, (wz0 + wz1) / 2.0 - 0.6, 1.2, 3.0, wz1 - wz0 + 1.2, STONE_DARK)
    h.box((wx0 + wx1) / 2.0, y + 1.5, wz0 - 0.6, wx1 - wx0, 3.0, 1.2, STONE_DARK)
    name = "ST BRIDE" if h.team == "red" else "ST PETER"
    kit.board_letters(b, h.x(x0), top - 2.5, 0.0, name, 2.0, STONE_LIGHT, "#2a2e36",
                      facing=h.inward, solid=False)


# =================================================================== village
def _cottage(b, h: Half, x0: float, x1: float, z0: float, z1: float, height: float,
             door: str, colour: str = STONE, roof: str = "", windows: bool = True) -> None:
    """A drowned cottage: stone walls, a door, window holes, and its roof
    gone -- or, where ``roof`` is a colour, a stepped slate roof still on."""
    area = h.r(x0, x1, z0, z1)
    zc = (z0 + z1) / 2.0
    xc = (x0 + x1) / 2.0
    doors = {}
    wins = {}
    if door in ("z-", "z+"):
        doors[door] = [(*h.xs(xc - 3.0, xc + 3.0), 7.0)]
    else:
        doors[h.face(door)] = [(zc - 3.0, zc + 3.0, 7.0)]
    if windows:
        for side in ("z-", "z+"):
            if side == door:
                continue
            wins[side] = [(*h.xs(xc - 2.0, xc + 2.0), 3.0, 5.6)]
    kit.building(b, area, 0.0, height, colour, roof=bool(roof), roof_colour=roof or SLATE,
                 doors=doors, windows=wins, lights="", studs_roof=True)
    if roof:
        kit.gable(b, area, height + 1.2, roof, along="x" if (x1 - x0) > (z1 - z0) else "z",
                  tiers=3, rise=1.4)


def _village(b: kit.RelayArea, h: Half) -> None:
    """Lower Ashby on this half: the Drowned Bell, the cottages along the
    high street, the mill by the river, gardens gone to silt."""
    # north side of the high street
    _cottage(b, h, 64.0, 92.0, 54.0, 78.0, 10.0, "z-", STONE, roof="")
    _cottage(b, h, 104.0, 138.0, 56.0, 84.0, 12.0, "z-", "#a89a84", roof=SLATE)
    kit.board_letters(b, h.x(121.0), 9.0, 56.0, "THE BELL", 1.6, "#3a2a1a", "#e8d8a8",
                      facing="z-", solid=False)
    _cottage(b, h, 150.0, 172.0, 54.0, 74.0, 9.0, "x-", STONE_LIGHT, roof="")
    # south of the high street, between it and the tower lane
    _cottage(b, h, 70.0, 96.0, 10.0, 28.0, 9.0, "z+", STONE_DARK, roof="")
    _cottage(b, h, 120.0, 144.0, 8.0, 28.0, 10.0, "z+", "#a89a84", roof=SLATE)
    # across the river: the mill and a cottage
    _cottage(b, h, 60.0, 90.0, -100.0, -72.0, 9.0, "z+", STONE, roof="")
    _cottage(b, h, 104.0, 140.0, -106.0, -74.0, 14.0, "z+", "#9a8a72", roof="")
    # the mill wheel on the river side of the mill, seized
    h.cyl(122.0, 7.0, -73.0, 16.0, 2.0, 16.0, "#5a4a32", collide=False, r=[math.pi / 2.0, 0.0, 0.0])
    h.box(122.0, 7.0, -73.0, 2.0, 2.0, 2.0, RUST, collide=False)
    # garden walls, low, a step to hop
    for x0, x1, z in ((64.0, 92.0, 90.0), (150.0, 178.0, 86.0), (60.0, 90.0, -112.0)):
        h.box((x0 + x1) / 2.0, 1.5, z, x1 - x0, 3.0, 1.6, STONE_DARK, studs=True)
    # a boat aground in a lane, a second on its side
    h.box(180.0, 1.4, 40.0 + 0.0 - 0.0, 18.0, 2.8, 6.0, "#3a6a8a")
    h.box(180.0, 2.9, 40.0, 12.0, 0.2, 4.0, "#7a5a3a", collide=False)
    h.box(196.0, 2.0, -20.0, 6.0, 4.0, 16.0, "#c8c0b0")


# ================================================================= outposts
def _outposts(b: kit.RelayArea, h: Half) -> None:
    """The barn (north) and the pump shed (south): where a team falls back
    to while its flag is out."""
    kit.outpost_room(h, 150.0, 192.0, 92.0, 128.0, 0.0, "#8a6a4a", "#5a3a2a", height=12.0,
                     door_w=12.0, pads=2, lights="#ffd890")
    kit.gable(b, h.r(150.0, 192.0, 92.0, 128.0), 13.2, "#6a3a2a", along="x", tiers=3, rise=1.6)
    kit.outpost_room(h, 150.0, 192.0, -128.0, -92.0, 0.0, CONCRETE, CONCRETE_DARK, height=11.0,
                     door_w=12.0, pads=2)
    h.cyl(186.0, 12.2 + 4.0, -122.0, 2.4, 8.0, 2.4, RUST, material="metal")


# ================================================================== lakebed
def _lakebed(b: kit.RelayArea, h: Half) -> None:
    """The bed between the buildings: plates of cracked mud a step high,
    weed, fish skeletons, rusted things the water kept."""
    for x, z, w, d, hgt in ((48.0, 112.0, 24.0, 16.0, 0.8), (210.0, 120.0, 20.0, 14.0, 1.4),
                            (60.0, -130.0, 22.0, 12.0, 1.0), (206.0, -100.0, 18.0, 16.0, 1.6),
                            (98.0, 108.0, 18.0, 12.0, 1.2), (130.0, -128.0, 16.0, 10.0, 0.6)):
        h.slab(x - w / 2.0, x + w / 2.0, z - d / 2.0, z + d / 2.0, hgt, hgt,
               MUD_LIGHT if hgt > 1.0 else MUD_DARK, studs=True)
    for x, z in ((40.0, 100.0), (186.0, -142.0 + 10.0), (214.0, 60.0)):
        for k in range(4):
            h.sphere(x + k * 1.6, 0.6, z + (k % 2) * 1.2, 2.0, 1.2, 2.0, WEED, collide=False)
    for x, z in ((86.0, 120.0), (200.0, 96.0)):
        h.box(x, 0.12, z, 6.0, 0.2, 0.4, "#e8e0d0", collide=False)
        for k in range(5):
            h.box(x - 2.0 + k * 1.0, 0.16, z, 0.2, 0.2, 2.4 - abs(k - 2) * 0.5, "#e8e0d0",
                  collide=False)
    # a rusted car where a lane was, on its roof
    h.box(214.0, 1.6, -132.0, 11.0, 3.2, 5.0, RUST, material="metal")
    h.box(214.0, 3.6, -132.0, 6.0, 0.8, 4.0, "#5a3a2a", material="metal", collide=False)


def _bridges(b: kit.RelayArea) -> None:
    """Three stone bridges over the dry river: one at the tower, one at each
    end of the village."""
    z0, z1 = RIVER_Z
    for x in (-130.0, 0.0, 130.0):
        slab(b, rect(x - 7.0, x + 7.0, z0 - 4.0, z1 + 4.0), 1.6, 1.6, STONE)
        for dx in (-6.6, 6.6):
            b.box([x + dx, 2.6, (z0 + z1) / 2.0], [0.8, 2.0, z1 - z0 + 8.0], STONE_DARK)
        # the keystone over the middle of the arch, and its lamps
        for dx in (-6.6, 6.6):
            b.box([x + dx, 4.2, (z0 + z1) / 2.0], [1.2, 1.2, 1.2], STONE_LIGHT)


def _street(b: kit.RelayArea) -> None:
    """The high street, cobbled under the silt, from chapel hill to chapel
    hill past the tower, and the tower lane."""
    for sx in (-1, 1):
        b.box([sx * 132.0, 0.03, 40.0], [164.0, 0.06, 12.0], COBBLE, collide=False)
        for x in range(56, 210, 10):
            b.box([sx * float(x), 0.08, 40.0], [0.4, 0.04, 12.0], "#6e6a64", collide=False)
        # a lamp standard, bent, every so often
        for x in (70.0, 140.0, 196.0):
            b.cyl([sx * x, 5.0, 33.0], [0.8, 10.0, 0.8], RUST, material="metal")
            b.box([sx * x, 10.4, 33.0], [1.6, 0.8, 1.6], RUST, material="metal", collide=False)


def _easter_eggs(b: kit.RelayArea) -> None:
    """A red phone box in the square, a NO SWIMMING sign on dry land and a
    diver's helmet in the river bed."""
    b.box([0.0, 4.0, 70.0], [4.0, 8.0, 4.0], "#c42b20")
    b.box([0.0, 8.4, 70.0], [4.4, 0.8, 4.4], "#a0221a")
    b.box([0.0, 6.8, 67.94], [3.0, 0.8, 0.12], "#f2f2f2", collide=False,
          decal=kit.sign_decal("TELEPHONE", "#1b1b1b", "#f2f2f2", 3.0 / 0.8))
    for side in (-1.0, 1.0):
        b.box([side * 2.05, 4.2, 70.0], [0.1, 4.0, 2.6], "#9fd8e8", collide=False,
              material="glass", alpha=0.5)
    b.cyl([0.0, 3.0, 128.0], [0.7, 6.0, 0.7], "#d8d8d8")
    b.box([0.0, 6.6, 128.0], [6.0, 2.4, 0.4], "#f2f2f2",
          decal=kit.sign_decal("NO SWIMMING", "#f2f2f2", "#c42b20", 6.0 / 2.4))
    b.sphere([0.0, -RIVER_DEPTH + 1.6, -55.0], [3.2, 3.2, 3.2], "#b8882a", material="metal",
             collide=False)
    b.cyl([0.0, -RIVER_DEPTH + 1.6, -56.7], [1.6, 0.2, 1.6], "#5a7a8a", collide=False,
          r=[math.pi / 2.0, 0.0, 0.0])


# ===================================================================== edge
def _edge(b: kit.RelayArea, rng: random.Random) -> None:
    """The dam to the north, the hills all round, the reservoir's own
    bathtub ring on the wall."""
    hx, hz, m = HALF[0], HALF[1], b.margin
    room_walls(b, rect(-hx - m, hx + m, -hz - m, hz + m), m, 0.0, 34.0, "#7a6a4a")
    for k, y in enumerate((12.0, 18.0, 24.0)):
        for sx in (-1, 1):
            b.box([sx * (hx + 0.2), y, 0.0], [0.4, 1.2, 2 * hz - 2.0],
                  ["#6a7a6a", "#7a7a6a", "#8a7a6a"][k], collide=False)
    b.box([0.0, 40.0, hz + m + 30.0], [520.0, 80.0, 40.0], CONCRETE_LIGHT, collide=False)
    b.box([0.0, 81.0, hz + m + 30.0], [530.0, 2.0, 44.0], CONCRETE, collide=False)
    for x in (-180.0, -60.0, 60.0, 180.0):
        b.box([x, 60.0, hz + m + 9.8], [8.0, 40.0, 0.4], "#5a6a6a", collide=False)
    kit.backdrop(b, "hills", 30.0, rng, colours=["#6a7a5a", "#5a6a4a", "#7a8a6a"],
                 sides=("x-", "x+", "z-"), depth=60.0)


def _landmarks(b: kit.RelayArea) -> None:
    for x, z, name in ((0, 0, "the valve tower"), (0, 70, "the phone box"),
                       (0, -55, "the tower bridge"), (0, -10, "the culvert")):
        b.landmark(float(x), float(z), name)
    for sx, team in ((-1, "red"), (1, "blue")):
        b.landmark(sx * 262.0, 0.0, "St Bride's" if team == "red" else "St Peter's")
        for x, z, name in ((121, 70, "the Drowned Bell"), (171, 110, "the barn"),
                           (171, -110, "the pump shed"), (122, -90, "the mill"),
                           (130, -55, "the mill bridge")):
            b.landmark(sx * float(x), float(z), "%s (%s side)" % (name, team))
    b.camera(-150.0, 60.0, 160.0, 0.0, 10.0, 0.0)
    b.camera(160.0, 60.0, -160.0, 0.0, 10.0, 0.0)
    b.camera(0.0, 80.0, 180.0, 0.0, 10.0, -20.0)
