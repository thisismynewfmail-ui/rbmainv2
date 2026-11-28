"""Longhorn Stockyards -- a cow town at the end of the cattle trail, the
sun going down gold over the mesas and a herd in every pen.

Layout (north is -z; both tracks run west to east, the cattle trail north
to south east of the middle, bowing west where the lines cross it)::

    z -250 ===== MESAS ============================[ NORTH GAP ]======== MESAS ====
           water tank   BOOT HILL   the church        T  LONGHORN ARCH  THE PENS
           bunkhouse    (the dead tree, the crosses)  R  (the catwalk over the
           (lane a start) ---\\                      A   alley, the chutes, the
    z    0 THE RODEO ARENA    \\==== the diamond ====I== stock cars)   (lane b end)
           (grandstands,       / windpump  coal      L  THE AUCTION BARN
           bucking chutes)    /                      |  MAIN STREET: saloon, bank,
           (lane b start) ---/  the trail camp       |  sheriff, store, church;
    z +250 COTTONWOOD CREEK (the mill, the hide yard) [ SOUTH GAP ]  hotel, livery,
           ===== MESAS ==========================================   smithy (lane a end)

Both companies leave the yards at the west end, climb the west swell and
come down to the diamond, then cross the cattle trail -- the Goodnight line
in the north-east, the Chisholm line in the south-east -- on their way to
the two stations.

The twist (``sweep``, style ``stampede``): every minute or so the herd
breaks out of one of the gaps in the mesas and stampedes down the trail
and out of the other, across both lines.  While it runs both crossings are
shut -- the stock gates swing across the tracks -- and a cart short of the
trail waits; a cart on the trail goes over if its company pushes it, or is
rolled back off.  Anybody on the trail when the herd comes is trampled.
Hold E at a corral gate -- the holding corral beside either crossing, the
stockyard gate by the arch, the drovers' corral on Main Street -- and the
herd breaks now: on their cart, if you time it.
"""
from __future__ import annotations

import math
import random

from ..kit import (WARM, WOOD, WOOD_DARK, WOOD_LIGHT, ArenaArea, backdrop, building, flight, gable,
                   ground, lantern, rect, room_walls, sign_decal, slab, threshold, wall, wall_sign)
from ...lastlight.kit import lamp_post
from . import common, rails
from .land import Land, graded, lay_graded, world_lane
from .rails import beside, clear_of, fillet, lay_track, mirror, storeyed, telegraph
from .scenery import bunting, camp_fire, cook_wagon, grandstand, outcrop, pup_tent, sage, skull

HALF = (400.0, 250.0)
SKY = {"top": "#3a5aa0", "horizon": "#ffb060", "sun": [-0.62, 0.24, 0.42],
       "clouds": 0.4, "tint": "#ffdcaa"}
AMBIENT = "#b8946c"
GROUND = "#b8a060"
FOG = 900.0

PRAIRIE = "#b8a060"
PRAIRIE_GREEN = "#9aa058"
PRAIRIE_DRY = "#cbb474"
DIRT = "#b08458"
DIRT_DARK = "#93694a"
MESA = "#b8603a"
MESA_DARK = "#8a4428"
MESA_PALE = "#d08a5a"
BARN_RED = "#a8321e"
WHITEWASH = "#efe6d4"
PLANK = "#9a7048"
PLANK_DARK = "#6a4a30"
FENCE = "#8a6440"
FENCE_DARK = "#6a4a2e"
HORN = "#efe2c4"
NAVY = "#2f4a6a"
GOLD = "#e8b23a"

ROUTE = fillet([(-372.0, -150.0), (-210.0, -150.0), (0.0, 0.0), (210.0, 150.0), (372.0, 150.0)],
               radius=80.0, step=5.0)
PROFILE = [(0.0, 0.0), (0.13, 0.0), (0.27, 5.0), (0.4, 2.0), (0.5, 1.0), (0.6, 1.0), (0.75, 1.0),
           (0.85, 4.0), (0.94, 0.0), (1.0, 0.0)]
LANE_A, YS = graded(ROUTE, PROFILE)
LANE_B = mirror(LANE_A)
LANES = (LANE_A, LANE_B)
LANE_OF = {"a": LANE_A, "b": LANE_B}

TRAIL_X0, TRAIL_K = 112.0, 0.00045
TRAIL_Y = 1.0                     # the trail's worn floor, a step under the prairie
TRAIL_HALF = 9.0                  # the herd's half-width: nearer the middle than this, trampled
TRAIL_KEEP = 15.0                 # nothing built nearer the middle than this
HERD_SPEED, HERD_LEN = 30.0, 150.0
TRAIL_END = 470.0                 # the trail runs on out of sight beyond the gaps
GAP_W = 15.0                      # half the gaps' width
GAP_H = 22.0


def trail_x(z: float) -> float:
    return TRAIL_X0 + TRAIL_K * z * z


TRAIL = [(trail_x(float(z)), float(z)) for z in range(-int(TRAIL_END), int(TRAIL_END) + 1, 10)]

PENS = (150.0, 300.0, -238.0, -178.0)       # the stockyard pens' block
ALLEY = (-214.0, -202.0)                    # the alley through the middle of it, z
CATWALK_Y = 8.0
SIDING_Z = -168.0
BARN = rect(150.0, 194.0, -28.0, 28.0)      # the auction barn
ARENA = rect(-320.0, -230.0, -32.0, 32.0)   # the rodeo arena's fence
CAMP = (-140.0, 12.0)                       # the trail camp's fire
REMUDA = rect(-196.0, -164.0, -34.0, -6.0)  # the camp's rope corral of horses
BOOT_HILL = (-118.0, -200.0, 7.0, 52.0)     # the knoll: x, z, height, radius
CHURCH = rect(-48.0, -26.0, -232.0, -200.0)
TANK = (-298.0, -186.0)                     # the railroad's water tank
BUNKHOUSE = rect(-262.0, -218.0, -236.0, -214.0)
MILL = (-226.0, 181.0)                      # the grist mill on the creek
HIDES = (-334.0, 210.0)                     # the hide yard
CREEK = [(-410.0, 196.0), (-330.0, 186.0), (-262.0, 202.0), (-206.0, 200.0), (-150.0, 188.0),
         (-94.0, 204.0), (-46.0, 224.0), (-26.0, 262.0)]
CALLS = ((150.5, -220.0, "the stockyard gate"), (150.5, 220.0, "the drovers' corral"),
         (131.4, -63.0, "the north crossing corral"), (131.4, 63.0, "the south crossing corral"))
CORRALS = (rect(136.0, 164.0, -80.0, -46.0), rect(136.0, 164.0, 46.0, 80.0))
WAGONS = (-4.0, 150.0)                      # the emigrants' wagons drawn up in a ring
BRANDING = rect(18.0, 46.0, -190.0, -162.0)  # the branding pen
MANSION = rect(240.0, 280.0, -60.0, -28.0)  # the cattle baron's house on the knoll

DEPOTS = (("a", 0.32, 1.0, "PRAIRIE TANK", 1, BARN_RED),
          ("a", 0.88, 1.0, "SADDLE CREEK", 2, NAVY),
          ("b", 0.32, -1.0, "PRAIRIE TANK SOUTH", 1, NAVY),
          ("b", 0.88, -1.0, "SADDLE CREEK NORTH", 2, BARN_RED))
COAL = ((-336.0, -100.0), (-336.0, 100.0), (-64.0, 0.0), (58.0, 0.0))

KEEP: list = []
BASES: dict = {}
RIGS: dict = {}


def build(b: ArenaArea) -> None:
    rng = random.Random(0x10A6)
    del KEEP[:]
    BASES.clear()
    RIGS.clear()
    for key in ("cattle", "horses", "smoke", "flame", "flags", "vanes", "lights", "pumps"):
        RIGS[key] = []
    b.extra.update({
        "accent": "#ffb24a", "twist": "sweep",
        "lanes": {"a": world_lane(b, LANE_A, YS), "b": world_lane(b, LANE_B, YS)},
        "names": {"a": "the Chisholm line", "b": "the Goodnight line"},
        "sweep": {"style": "stampede", "path": [b.at(x, TRAIL_Y, z) for x, z in TRAIL],
                  "speed": HERD_SPEED, "length": HERD_LEN, "half": TRAIL_HALF,
                  "cross": {lane: round(_cross(path, TRAIL)[1], 2) for lane, path in LANE_OF.items()},
                  "show": [round(_trail_s(-b.half_z - b.margin * 0.7), 2),
                           round(_trail_s(b.half_z + b.margin * 0.7), 2)],
                  "gates": _gate_specs(b)},
    })
    land = _land()
    ground(b, PRAIRIE, soil="#6a5236", holes=[])
    land.build(b, PRAIRIE)
    _edge(b, rng)
    for path in LANES:
        lay_graded(b, path, YS, ballast="#8a7a62")
    common.start_yards(b, ("LONGHORN YARD", "CHISHOLM YARD"), (BARN_RED, NAVY), KEEP, post=PLANK_DARK,
                       sign_bg=HORN, sign_fg="#4a2a1a")
    _gates(b)
    _calls(b)
    _diamond(b)
    _stockyards(b, rng)
    _crossing_corrals(b)
    _barn(b, rng)
    _main_street(b, rng)
    _rodeo(b, rng, land)
    _camp(b, rng, land)
    _boot_hill(b, rng, land)
    _yard_west(b, rng, land)
    _creek(b, rng, land)
    _windpump(b, land)
    _wagons(b, rng)
    _branding(b, rng, land)
    _mansion(b, rng)
    _haystacks(b, rng, land)
    common.termini(b, ("BUFFALO SPRINGS", "STOCKYARD JUNCTION"), (NAVY, BARN_RED), KEEP, house="#c8a070",
                   trim=PLANK_DARK, sign_bg=HORN, sign_fg="#4a2a1a")
    common.place_depots(b, DEPOTS, LANE_OF, BASES, KEEP)
    common.place_levers(b, land, LANE_OF, KEEP)
    common.place_coal(b, COAL, BASES, rng, KEEP)
    _scatter(b, rng, land)
    telegraph(b, LANE_A, -1.0, ground=land.height, skip=_blocked)
    telegraph(b, LANE_B, 1.0, ground=land.height, skip=_blocked)
    _rigs(b, land)
    for x, z, name in ((-345, -150, "the Longhorn yard"), (-345, 150, "the Chisholm yard"),
                       (0, 0, "the diamond"), (trail_x(0.0), 0, "the cattle trail"),
                       (trail_x(-235.0), -235, "the north gap"), (trail_x(235.0), 235, "the south gap"),
                       (150, -208, "the Longhorn Arch"), (225, -208, "the stockyard pens"),
                       (225, -208, "the catwalk"), (255, -168, "the stock cars"),
                       (172, 0, "the auction barn"), (90, 114, "the Golden Steer saloon"),
                       (100, 170, "Main Street"), (156, 157, "the Drovers' Cottage"),
                       (163, 193, "the livery stable"), (163, 228, "the smithy"),
                       (ARENA[0] + 45, 0, "the rodeo arena"), (CAMP[0], CAMP[1], "the trail camp"),
                       (BOOT_HILL[0], BOOT_HILL[1], "Boot Hill"), (-37, -216, "the church"),
                       (TANK[0], TANK[1], "the water tank"), (-240, -225, "the bunkhouse"),
                       (MILL[0], MILL[1], "the mill"), (HIDES[0], HIDES[1], "the hide yard"),
                       (-150, 196, "Cottonwood Creek"), (80, -24, "the windpump"),
                       (345, 150, "Buffalo Springs"), (345, -150, "Stockyard Junction"),
                       (WAGONS[0], WAGONS[1], "the wagon ring"), (32, -176, "the branding pen"),
                       (260, -44, "the cattle baron's house")):
        b.landmark(float(x), float(z), name)
    for x, z, name in CALLS:
        b.landmark(x, z, name)
    b.camera(40.0, 44.0, -40.0, trail_x(-80.0), 2.0, -80.0)
    b.camera(110.0, 50.0, -120.0, 225.0, 6.0, -208.0)
    b.camera(40.0, 40.0, 120.0, 110.0, 6.0, 180.0)
    b.camera(-200.0, 44.0, 70.0, -275.0, 4.0, 0.0)


def _keep(area) -> None:
    KEEP.append(area)


def _blocked(x: float, z: float) -> bool:
    if abs(x - trail_x(z)) < TRAIL_KEEP:
        return True
    return any(k[0] - 2 < x < k[1] + 2 and k[2] - 2 < z < k[3] + 2 for k in KEEP)


def _smooth(k: float) -> float:
    k = max(0.0, min(1.0, k))
    return k * k * (3.0 - 2.0 * k)


def _cross(path, line):
    """(distance along ``path``, distance along ``line``) where they cross."""
    def cum(pts):
        out = [0.0]
        for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
            out.append(out[-1] + math.hypot(x1 - x0, z1 - z0))
        return out
    ca, cb = cum(path), cum(line)
    for i in range(len(path) - 1):
        (p0x, p0z), (p1x, p1z) = path[i], path[i + 1]
        for j in range(len(line) - 1):
            (q0x, q0z), (q1x, q1z) = line[j], line[j + 1]
            rx, rz, sx, sz = p1x - p0x, p1z - p0z, q1x - q0x, q1z - q0z
            den = rx * sz - rz * sx
            if abs(den) < 1e-9:
                continue
            t = ((q0x - p0x) * sz - (q0z - p0z) * sx) / den
            u = ((q0x - p0x) * rz - (q0z - p0z) * rx) / den
            if 0.0 <= t <= 1.0 and 0.0 <= u <= 1.0:
                return ca[i] + t * (ca[i + 1] - ca[i]), cb[j] + u * (cb[j + 1] - cb[j])
    return ca[-1] / 2.0, cb[-1] / 2.0


def _trail_s(z: float) -> float:
    """How far along the trail (from its north end) it reaches ``z``."""
    s = 0.0
    for (x0, z0), (x1, z1) in zip(TRAIL, TRAIL[1:]):
        seg = math.hypot(x1 - x0, z1 - z0)
        if z0 <= z <= z1:
            return s + seg * (z - z0) / (z1 - z0)
        s += seg
    return s


# ==================================================================== land
KNOLLS = ((BOOT_HILL[0], BOOT_HILL[1], BOOT_HILL[2], BOOT_HILL[3]), (-36.0, -150.0, 4.0, 40.0),
          (-262.0, 96.0, 5.0, 42.0), (260.0, -40.0, 5.0, 46.0), (250.0, 60.0, 4.0, 40.0),
          (-110.0, 120.0, 4.0, 36.0), (40.0, 210.0, 5.0, 40.0), (-200.0, -110.0, 5.0, 40.0))


def _land() -> Land:
    """Rolling prairie, sunburnt on the swells and greener in the low
    places, rising to the mesas north and south; Boot Hill and a few
    smaller knolls; the trail a worn swathe of bare dirt a step under the
    grass."""
    hx, hz = HALF
    land = Land(rect(-hx, hx, -hz, hz), cell=10.0, step=1.0)

    def shape(x: float, z: float) -> float:
        swell = 2.6 * math.sin(x / 61.0 + 0.4) * math.cos(z / 47.0) + 1.8 * math.cos(x / 37.0 - z / 53.0)
        edge = 7.0 * _smooth((abs(z) - 180.0) / 70.0)
        hill = 0.0
        for kx, kz, kh, kr in KNOLLS:
            hill += kh * _smooth(1.0 - math.hypot(x - kx, z - kz) / kr)
        h = 3.2 + swell + edge + hill
        off = abs(x - trail_x(z))
        k = _smooth((off - 13.0) / 24.0)
        return max(TRAIL_Y, TRAIL_Y + (h - TRAIL_Y) * k)

    land.add(shape)
    flats = [(rect(-400.0, -312.0, -182.0, -126.0), 0.0, 10.0),    # the Longhorn yard
             (rect(-400.0, -312.0, 126.0, 182.0), 0.0, 10.0),      # the Chisholm yard
             (rect(300.0, 400.0, -200.0, -120.0), 0.0, 10.0),      # the stations
             (rect(300.0, 400.0, 120.0, 200.0), 0.0, 10.0),
             (rect(PENS[0] - 2.0, PENS[1] + 18.0, PENS[2] - 8.0, PENS[3] + 2.0), TRAIL_Y, 8.0),
             (rect(206.0, 300.0, -174.0, -160.0), TRAIL_Y, 6.0),    # the siding
             (rect(BARN[0] - 10.0, BARN[1] + 32.0, BARN[2] - 8.0, BARN[3] + 8.0), TRAIL_Y, 8.0),
             (rect(130.0, 168.0, -84.0, -42.0), TRAIL_Y, 6.0),     # the crossing corrals
             (rect(130.0, 168.0, 42.0, 84.0), TRAIL_Y, 6.0),
             (rect(70.0, 124.0, 96.0, 244.0), TRAIL_Y, 6.0),       # Main Street, the west side
             (rect(136.0, 186.0, 138.0, 244.0), TRAIL_Y, 6.0),     # and the east
             (rect(186.0, 222.0, 166.0, 204.0), TRAIL_Y, 6.0),     # the smithy
             (rect(300.0, 352.0, -250.0, -218.0), TRAIL_Y, 6.0),   # the Livestock Exchange
             (rect(ARENA[0] - 14.0, ARENA[1] + 14.0, ARENA[2] - 24.0, ARENA[3] + 24.0), 2.0, 10.0),
             (rect(CHURCH[0] - 6.0, CHURCH[1] + 6.0, CHURCH[2] - 6.0, CHURCH[3] + 6.0), 4.0, 8.0),
             (rect(BUNKHOUSE[0] - 4.0, BUNKHOUSE[1] + 4.0, BUNKHOUSE[2] - 4.0, BUNKHOUSE[3] + 6.0), 3.0, 8.0),
             (rect(TANK[0] - 28.0, TANK[0] + 8.0, TANK[1] - 8.0, TANK[1] + 9.0), 2.0, 6.0),
             (rect(CAMP[0] - 60.0, CAMP[0] + 24.0, CAMP[1] - 50.0, CAMP[1] + 22.0), 2.0, 10.0),
             (rect(MILL[0] - 18.0, MILL[0] + 18.0, MILL[1] - 12.0, MILL[1] + 11.0), 2.0, 6.0),
             (rect(HIDES[0] - 22.0, HIDES[0] + 22.0, HIDES[1] - 10.0, HIDES[1] + 16.0), 2.0, 6.0),
             (rect(60.0, 98.0, -40.0, 14.0), TRAIL_Y, 6.0),        # the windpump and the coal
             (rect(WAGONS[0] - 34.0, WAGONS[0] + 34.0, WAGONS[1] - 30.0, WAGONS[1] + 34.0), 3.0, 10.0),
             (rect(BRANDING[0] - 8.0, BRANDING[1] + 8.0, BRANDING[2] - 8.0, BRANDING[3] + 8.0), 3.0, 8.0)]
    for area, y, blend in flats:
        land.flatten(area, y, blend)
    mtop = float(round(land.height((MANSION[0] + MANSION[1]) / 2.0, (MANSION[2] + MANSION[3]) / 2.0)))
    land.flatten(rect(MANSION[0] - 10.0, MANSION[1] + 10.0, MANSION[2] - 10.0, MANSION[3] + 14.0), mtop, 10.0)
    BOOT_Y["mansion"] = mtop
    top = float(round(land.height(BOOT_HILL[0], BOOT_HILL[1])))
    land.flatten(rect(BOOT_HILL[0] - 16.0, BOOT_HILL[0] + 16.0, BOOT_HILL[1] - 12.0, BOOT_HILL[1] + 12.0),
                 top, 10.0)
    BOOT_Y["top"] = top
    common.plan_depots(land, DEPOTS, LANE_OF, YS, BASES)
    common.plan_coal(land, COAL, BASES)
    for path in LANES:
        land.pin_path(path, YS, half=7.5, blend=12.0)
    # the creek: its cells cut to the ground, its banks the land either side
    for (x0, z0), (x1, z1) in zip(CREEK, CREEK[1:]):
        n = max(1, int(math.hypot(x1 - x0, z1 - z0) / 4.0))
        for k in range(n + 1):
            x, z = x0 + (x1 - x0) * k / n, z0 + (z1 - z0) * k / n
            land.cut(rect(x - 4.0, x + 4.0, z - 4.0, z + 4.0))

    def paint(x: float, z: float, h: float):
        off = abs(x - trail_x(z))
        if off < 5.0:
            return DIRT_DARK
        if off < 16.0:
            return DIRT
        if ARENA[0] <= x <= ARENA[1] and ARENA[2] <= z <= ARENA[3]:
            return DIRT
        if h >= 9.0:
            return PRAIRIE_DRY
        if h < 2.5:
            return PRAIRIE_GREEN
        return None

    land.colour(paint)
    return land


# ==================================================================== edge
def _edge(b: ArenaArea, rng: random.Random) -> None:
    """Red mesas along the north and south, each split by the trail's gap
    (the herd comes out of the shadow in it); low swells east and west."""
    hx, hz, m = b.half_x, b.half_z, b.margin
    room_walls(b, rect(-hx - m, hx + m, -hz - m, hz + m), m, 0.0, 22.0, "#9a8a58", sides=("x-", "x+"))
    for side in (-1, 1):
        zc = side * (hz + m / 2.0)
        gx = trail_x(side * hz)
        wall(b, "x", zc, m, -hx, hx, 0.0, 44.0, MESA_DARK, gaps=[(gx - GAP_W, gx + GAP_W, GAP_H)])
        # the shadow of the canyon the trail goes up into, a few units in
        b.box([gx, GAP_H / 2.0, side * (hz + m * 0.7)], [GAP_W * 2.0, GAP_H, m * 0.6], "#3a2418")
        b.box([gx, GAP_H + 11.3, zc], [GAP_W * 2.0 + 0.4, 22.6, m + 0.4], MESA)
        # the gap's rock jaws, banded, stepping back
        for e in (-1.0, 1.0):
            for k, (w, h, c) in enumerate(((6.0, 34.0, MESA), (5.0, 26.0, MESA_PALE), (4.0, 18.0, MESA_DARK))):
                px = gx + e * (GAP_W + 2.0 + k * 3.0)
                pz = side * (hz - 3.0 - k * 4.0)
                b.box([px, h / 2.0, pz], [w, h, 6.0 - k], c)
            b.box([gx + e * (GAP_W + 2.5), 36.5, side * (hz - 3.0)], [7.0, 5.0, 7.0], MESA_PALE, collide=False)
        # the ragged crest of the mesas
        for i in range(32):
            x = -hx + (i + 0.5) * (2 * hx) / 32.0
            if abs(x - gx) < GAP_W + 8.0:
                continue
            top = rng.uniform(3.0, 14.0)
            b.box([x, 44.0 + top / 2.0, zc], [2 * hx / 32.0 - 1.0, top, m + 1.0 + (i % 3) * 0.13],
                  rng.choice([MESA, MESA_DARK, MESA_PALE]), collide=False)
        _keep(rect(gx - GAP_W - 16.0, gx + GAP_W + 16.0, side * hz - 20.0, side * hz + 20.0))
    backdrop(b, "hills", 0.0, rng, ["#9a8a58", "#a89860", "#8a7a4a"], sides=("x-", "x+"), depth=200.0)
    backdrop(b, "mesas", 0.0, rng, [MESA_DARK, MESA, "#7a3a24"], sides=("z-", "z+"), depth=140.0)


# ================================================================= the trail
def _lane_cross_d(path) -> float:
    return _cross(path, TRAIL)[0]


def _gate_specs(b: ArenaArea):
    """The stock gates (their arms the client's, swung across the track
    while the herd runs): on each lane, one each side of the trail."""
    out = []
    for lane, path in (("a", LANE_A), ("b", LANE_B)):
        d_x = _lane_cross_d(path)
        for along, side in ((-15.0, 1.0), (15.0, -1.0)):
            x, z, yaw = beside(path, d_x + along, side * 5.2)
            lx, lz, lyaw = rails.at(path, d_x + along)
            arm_yaw = math.atan2(lx - x, lz - z)
            fx, fz = math.sin(lyaw), math.cos(lyaw)
            facing = -1.0 if along < 0 else 1.0
            lamps = [b.at(x + fx * facing * 0.7 * k, 5.4, z + fz * facing * 0.7 * k) for k in (-1, 1)]
            out.append({"p": b.at(x, 4.6, z), "yaw": round(arm_yaw, 4), "len": 9.2, "lane": lane,
                        "lamps": lamps, "post": [round(x, 2), round(z, 2)], "face": round(lyaw, 4)})
    return out


def _gates(b: ArenaArea) -> None:
    """The stock gates' posts: a heavy timber post, a lantern on it each way,
    a sign with a longhorn on it, and a cattle guard across the track."""
    for gate in b.extra["sweep"]["gates"]:
        x, z = gate["post"]
        face = gate["face"]
        b.box([x, 3.2, z], [1.0, 6.4, 1.0], PLANK_DARK)
        b.box([x, 0.4, z], [1.8, 0.8, 1.8], "#7a6a58")
        for lamp in gate["lamps"]:
            lx, lz = lamp[0] - b.ox, lamp[2] - b.oz
            b.box([lx, 5.4, lz], [0.8, 0.9, 0.8], "#2a2018", collide=False, r=[0.0, face, 0.0])
        b.box([x, 7.4, z], [3.4, 1.8, 0.2], HORN, collide=False, r=[0.0, face + math.pi / 2.0, 0.0],
              decal=sign_decal("CATTLE", HORN, "#5a2a1a", 3.4))
        b.box([x, 8.6, z], [4.6, 0.3, 0.3], HORN, collide=False, r=[0.0, face + math.pi / 2.0, 0.08])
        _keep(rect(x - 2.0, x + 2.0, z - 2.0, z + 2.0))
    # the stop boards short of the trail
    for lane, path, side in (("a", LANE_A, 1.0), ("b", LANE_B, -1.0)):
        d = _lane_cross_d(path) - 17.0
        x, z, yaw = beside(path, d, side * 5.8)
        b.cyl([x, 2.6, z], [0.5, 5.2, 0.5], PLANK_DARK)
        b.box([x, 5.6, z], [2.6, 1.6, 0.2], WHITEWASH, collide=False, r=[0.0, yaw, 0.0],
              decal=sign_decal("STOP", WHITEWASH, BARN_RED, 2.0))
        _keep(rect(x - 1.5, x + 1.5, z - 1.5, z + 1.5))


def _calls(b: ArenaArea) -> None:
    """The corral gates that turn the herd loose: a gate post with a long
    lever and a bell, beside the gate onto the trail."""
    for x, z, name in CALLS:
        y = TRAIL_Y
        px = x + 2.7          # the post stands clear of where you stand to work it
        b.box([px, y + 2.6, z], [1.0, 5.2, 1.0], PLANK_DARK)
        b.box([px, y + 0.3, z], [2.0, 0.6, 2.0], "#7a6a58")
        b.box([px, y + 4.8, z - 1.2], [0.3, 3.6, 0.3], "#3a3a3e", material="metal", collide=False,
              r=[0.5, 0.0, 0.0])
        b.sphere([px, y + 5.5, z], [0.8, 0.7, 0.8], BARN_RED, collide=False)
        b.box([px, y + 5.6, z + 0.8], [0.4, 0.4, 1.2], "#3a3a3e", material="metal", collide=False)
        b.cone([px, y + 4.9, z + 1.3], [1.2, 1.2, 1.2], GOLD, material="metal", collide=False)
        b.mark("call", x, y + 0.4, z, name=name)
        _keep(rect(x - 1.0, px + 1.5, z - 3.0, z + 3.0))


def _diamond(b: ArenaArea) -> None:
    """Where the lines cross: a lamp at each corner."""
    y = 1.0
    for x, z in ((-16.0, -22.0), (16.0, 22.0), (-16.0, 22.0), (16.0, -22.0)):
        lamp_post(b, x, z, 11.0, light=WARM, y=y)
        _keep(rect(x - 1.0, x + 1.0, z - 1.0, z + 1.0))


# ================================================================ stockyards
def _fence(b: ArenaArea, axis: str, at: float, lo: float, hi: float, base: float,
           gaps=(), colour: str = FENCE, posts=None, h: float = 4.6, lift: float = 0.0) -> None:
    """A post-and-rail fence along ``axis`` at ``at`` from ``lo`` to ``hi``,
    three rails, posts every four units, an opening at each of ``gaps``.
    ``posts`` (a set) keeps two fences from planting a post in one hole;
    ``lift`` raises its rails a hair so two fences meeting at a corner never
    share a face."""
    cuts = sorted(gaps)
    spans, start = [], lo
    for g0, g1 in cuts:
        spans.append((start, g0))
        start = g1
    spans.append((start, hi))
    for s0, s1 in spans:
        if s1 - s0 < 0.6:
            continue
        n = max(1, int(round((s1 - s0) / 4.0)))
        for k in range(n + 1):
            u = s0 + (s1 - s0) * k / n
            x, z = (u, at) if axis == "x" else (at, u)
            if posts is not None:
                if any(abs(px - x) < 0.9 and abs(pz - z) < 0.9 for px, pz in posts):
                    continue
                posts.add((x, z))
            b.box([x, base + h / 2.0, z], [0.7, h, 0.7], colour)
        for y in (1.3, 2.5, 3.7):
            yy = base + y * h / 4.6 + lift
            if axis == "x":
                b.box([(s0 + s1) / 2.0, yy, at], [s1 - s0, 0.5, 0.3], colour)
            else:
                b.box([at, yy, (s0 + s1) / 2.0], [0.3, 0.5, s1 - s0], colour)


def _stock_car(b: ArenaArea, x: float, z: float, base: float) -> None:
    """A slatted stock car on the siding, its door slid back toward the
    chute, longhorns peering out between the slats."""
    length = 20.0
    rails._trucks(b, x, z, "x", length, base=base)
    floor = base + rails.CAR_FLOOR
    b.box([x, floor + 2.9, z], [length - 0.6, 5.8, 5.0], "#2a1c14")
    for side in (-1.0, 1.0):
        face = z + side * 2.62
        for k in range(5):
            b.box([x, floor + 0.7 + k * 1.15, face], [length - 0.4, 0.6, 0.24], "#a8603a", collide=False)
        for k in range(6):
            b.box([x - length / 2.0 + 0.5 + k * (length - 1.0) / 5.0, floor + 3.0, face + side * 0.16],
                  [0.4, 6.0, 0.2], "#6a3a22", collide=False)
    b.box([x, floor + 6.2, z], [length + 0.4, 0.4, 6.2], "#4a4642", material="metal")
    b.box([x + 1.0, floor + 2.9, z - 2.9], [5.0, 5.4, 0.3], "#1a1410", collide=False)
    rails._buffers(b, x, z, "x", length, base=base)


def _stockyards(b: ArenaArea, rng: random.Random) -> None:
    """The stockyards: two rows of pens either side of an alley, every pen
    with its gate onto the alley and a herd milling in it; a catwalk on
    posts down the alley for the buyers (a stair up each end); the
    Longhorn Arch over the alley's mouth by the trail; chutes up from the
    south pens into the stock cars on the siding; the Livestock Exchange
    with its clock at the far end."""
    x0, x1, z0, z1 = PENS
    a0, a1 = ALLEY
    y = TRAIL_Y
    posts: set = set()
    cols = [160.0 + 20.0 * k for k in range(8)]          # 160 .. 300
    chutes = (225.0, 255.0, 285.0)
    # the north row: z0 .. a0, the south row: a1 .. z1
    _fence(b, "x", z0, cols[0], cols[-1], y, posts=posts)
    _fence(b, "x", a0, cols[0], cols[-1], y, posts=posts,
           gaps=[(c + 7.5, c + 12.5) for c in cols[:-1]])
    _fence(b, "x", a1, cols[0], cols[-1], y, posts=posts,
           gaps=[(c + 7.5, c + 12.5) for c in cols[:-1]])
    _fence(b, "x", z1, cols[0], cols[-1], y, posts=posts, gaps=[(c - 2.4, c + 2.4) for c in chutes])
    for c in cols:
        _fence(b, "z", c, z0, a0, y, posts=posts, lift=0.1)
        _fence(b, "z", c, a1, z1, y, posts=posts, lift=0.1)
    # the gates swung open against the fence, troughs, hay racks, the herds
    for k, c in enumerate(cols[:-1]):
        for row, (r0, r1, face) in enumerate(((z0, a0, a0), (a1, z1, a1))):
            e = -1.0 if face == a0 else 1.0
            b.box([c + 12.9, y + 2.3, face - e * 2.6], [0.25, 3.6, 5.0], FENCE_DARK)
            if (k + row) % 3 == 0:
                b.box([c + 4.0, y + 0.6, (r0 + r1) / 2.0], [2.0, 1.2, 8.0], "#6a5a48")
                b.box([c + 4.0, y + 1.25, (r0 + r1) / 2.0], [1.6, 0.1, 7.6], "#4a8ab0", collide=False)
            elif (k + row) % 3 == 1:
                b.box([c + 16.0, y + 1.2, (r0 + r1) / 2.0], [2.6, 2.4, 6.0], "#c8a858", studs=True)
            if (k * 3 + row) % 5 != 4:
                RIGS["cattle"].append((c + 1.6, c + 18.4, r0 + 1.6, r1 - 1.6, y, 4 + (k + row) % 3, "cattle"))
    _keep(rect(x0 - 2.0, x1 + 2.0, z0 - 2.0, z1 + 2.0))
    # the catwalk over the alley, a stair up from each end
    cz = (a0 + a1) / 2.0
    top = y + CATWALK_Y
    slab(b, rect(170.0, 300.0, cz - 2.0, cz + 2.0), top, 0.5, PLANK, studs=True)
    for x in range(170, 301, 13):
        for e in (-1.0, 1.0):
            b.box([float(x), (y + top - 0.5) / 2.0, cz + e * 2.3], [0.6, top - 0.5 - y, 0.6], PLANK_DARK)
    for e in (-1.0, 1.0):
        b.box([235.0, top + 1.3, cz + e * 1.9], [130.0, 0.3, 0.3], PLANK_DARK)
        for x in range(172, 300, 8):
            b.box([float(x), top + 0.65, cz + e * 1.9], [0.3, 1.3, 0.3], PLANK_DARK)
    flight(b, "x", 150.0, 170.0, cz - 2.0, cz + 2.0, y, top, PLANK, fill=y)
    flight(b, "x", 318.0, 300.0, cz - 2.0, cz + 2.0, y, top, PLANK, fill=y)
    b.mark("perch", 236.0, top, cz)
    b.mark("perch", 288.0, top, cz)
    _keep(rect(148.0, 320.0, cz - 3.0, cz + 3.0))
    # the Longhorn Arch over the mouth of the alley
    ax = 148.0
    for pz in (a0 - 2.6, a1 + 2.6):
        b.box([ax, y + 9.0, pz], [2.4, 18.0, 2.4], PLANK_DARK)
        b.box([ax, y + 0.6, pz], [3.6, 1.2, 3.6], "#7a6a58")
    b.box([ax, y + 16.4, cz], [2.6, 2.8, a1 - a0 + 9.0], PLANK_DARK)
    wall_sign(b, ax - 1.66, y + 16.4, cz, a1 - a0 + 4.0, 2.2,
              sign_decal("LONGHORN STOCKYARDS", HORN, "#5a2a1a", 9.0), "x-", HORN)
    b.box([ax, y + 19.3, cz], [1.8, 3.0, 3.4], "#8a5a3a", collide=False)
    b.box([ax - 0.9, y + 18.6, cz], [0.3, 1.2, 1.6], "#2a201a", collide=False)
    for e in (-1.0, 1.0):
        b.box([ax, y + 19.8, cz + e * 4.6], [0.9, 0.9, 6.4], HORN, collide=False, r=[e * 0.08, 0.0, 0.0])
        b.box([ax, y + 20.6, cz + e * 9.4], [0.8, 0.8, 4.4], HORN, collide=False, r=[e * 0.32, 0.0, 0.0])
        b.box([ax, y + 22.1, cz + e * 11.6], [0.6, 2.6, 0.6], "#3a3028", collide=False, r=[-e * 0.5, 0.0, 0.0])
    for pz in (a0 + 1.0, a1 - 1.0):
        lantern(b, ax + 1.6, y + 13.4, pz, WARM)
    # the siding, its stock cars, the chutes up into them
    lay_graded(b, [(214.0, SIDING_Z), (298.0, SIDING_Z)], [y, y], ballast="#8a7a62")
    for x in (214.0, 298.0):
        rails.buffer_stop(b, x, SIDING_Z, math.pi / 2.0 if x > 250 else -math.pi / 2.0, BARN_RED, base=y)
    for c in chutes:
        _stock_car(b, c, SIDING_Z, y)
        floor = y + rails.CAR_FLOOR
        flight(b, "z", z1, SIDING_Z - 3.2, c - 2.0, c + 2.0, y, floor, PLANK, fill=y)
        for e in (-1.0, 1.0):
            b.box([c + e * 2.5, y + 2.6, (z1 + SIDING_Z - 3.2) / 2.0], [0.4, 5.2, z1 - SIDING_Z + 3.4],
                  FENCE_DARK)
    _keep(rect(210.0, 302.0, SIDING_Z - 5.0, SIDING_Z + 5.0))
    _keep(rect(cols[0], cols[-1], z1, SIDING_Z))
    # the Livestock Exchange
    ex = rect(306.0, 346.0, -246.0, -224.0)
    ey = TRAIL_Y
    storeyed(b, ex, [8.0, 7.0], "#9a4a32", roof="#3a3a40",
             doors={"z+": [(322.0, 330.0, ey + 7.0)]},
             windows=[{"z+": [(309.0, 316.0, ey + 2.6, ey + 6.0), (336.0, 343.0, ey + 2.6, ey + 6.0)]},
                      {"z+": [(309.0, 316.0, ey + 10.6, ey + 13.6), (320.0, 332.0, ey + 10.6, ey + 13.6),
                              (336.0, 343.0, ey + 10.6, ey + 13.6)]}], base=ey)
    threshold(b, ex, "z+", (322.0, 330.0), y0=ey)
    zf = ex[3] - 0.1
    b.box([326.0, ey + 18.4, zf - 0.8], [14.0, 6.0, 1.6], "#9a4a32")
    b.cyl([326.0, ey + 18.4, zf + 0.05], [4.6, 0.3, 4.6], "#2a2a2e", r=[math.pi / 2.0, 0, 0], collide=False)
    b.cyl([326.0, ey + 18.4, zf + 0.2], [3.9, 0.3, 3.9], HORN, r=[math.pi / 2.0, 0, 0], collide=False)
    RIGS.setdefault("clocks", []).append(((326.0, ey + 18.4, zf + 0.36), 0.0, 0.0, 1.8))
    wall_sign(b, 326.0, ey + 8.6, ex[3] + 0.36, 26.0, 1.6, sign_decal("LIVESTOCK EXCHANGE", HORN, "#5a2a1a", 13.0),
              "z+", HORN)
    _keep(rect(ex[0] - 2.0, ex[1] + 2.0, ex[2] - 2.0, ex[3] + 4.0))


def _crossing_corrals(b: ArenaArea) -> None:
    """A holding corral beside each crossing, full of steers waiting their
    turn, its gate onto the trail: open it and the herd breaks."""
    y = TRAIL_Y
    for x0, x1, z0, z1 in CORRALS:
        posts: set = set()
        zc = (z0 + z1) / 2.0
        _fence(b, "z", x0, z0, z1, y, posts=posts, colour=FENCE_DARK, gaps=[(zc - 3.0, zc + 3.0)])
        _fence(b, "z", x1, z0, z1, y, posts=posts, colour=FENCE_DARK)
        _fence(b, "x", z0, x0, x1, y, posts=posts, colour=FENCE_DARK, lift=0.1)
        _fence(b, "x", z1, x0, x1, y, posts=posts, colour=FENCE_DARK, lift=0.1)
        b.box([x0 + 0.1, y + 2.3, zc - 2.9], [0.25, 3.6, 5.6], FENCE)
        b.box([x1 - 4.0, y + 0.6, zc], [2.0, 1.2, 8.0], "#6a5a48")
        b.box([x1 - 4.0, y + 1.25, zc], [1.6, 0.1, 7.6], "#4a8ab0", collide=False)
        RIGS["cattle"].append((x0 + 2.0, x1 - 6.0, z0 + 2.0, z1 - 2.0, y, 5, "cattle"))
        _keep(rect(x0 - 4.0, x1 + 2.0, z0 - 2.0, z1 + 2.0))


# ==================================================================== barn
def _barn(b: ArenaArea, rng: random.Random) -> None:
    """The auction barn east of the trail: barn red with white trim, the big
    doors open at both ends, a cupola on the ridge; inside, the sale ring
    with bleachers either side and the auctioneer's stand; the scale house
    and its platform outside."""
    x0, x1, z0, z1 = BARN
    y = TRAIL_Y
    building(b, BARN, y, 14.0, BARN_RED, roof_colour="#4a3a30", floor_colour="#8a6a48",
             doors={"x-": [(-8.0, 8.0, 12.0)], "x+": [(-6.0, 6.0, 10.0)]},
             windows={"z-": [(156.0, 162.0, 5.0, 9.0), (182.0, 188.0, 5.0, 9.0)],
                      "z+": [(156.0, 162.0, 5.0, 9.0), (182.0, 188.0, 5.0, 9.0)]},
             glass=True, lights=WARM)
    threshold(b, BARN, "x-", (-8.0, 8.0))
    threshold(b, BARN, "x+", (-6.0, 6.0))
    gable(b, BARN, y + 15.2, "#4a3a30", "x", 5, 1.6, 0.8)
    # white trim: corner boards, the open doors' X braces, the hayloft door
    for xx in (x0 - 0.15, x1 + 0.15):
        for zz in (z0 - 0.15, z1 + 0.15):
            b.box([xx, y + 7.0, zz], [1.0, 14.0, 1.0], WHITEWASH)
    for e in (-1.0, 1.0):
        dz = e * 8.0
        b.box([x0 - 1.4, y + 6.0, dz + e * 4.2], [0.3, 12.0, 8.0], BARN_RED)
        b.box([x0 - 1.6, y + 6.0, dz + e * 4.2], [0.1, 12.6, 0.5], WHITEWASH, collide=False, r=[0.6, 0, 0])
        b.box([x0 - 1.6, y + 6.0, dz + e * 4.2], [0.1, 12.6, 0.5], WHITEWASH, collide=False, r=[-0.6, 0, 0])
    b.box([x0 - 0.4, y + 18.0, 0.0], [0.4, 4.0, 5.0], "#2a1a12", collide=False)
    b.box([x0 - 3.0, y + 20.6, 0.0], [6.0, 0.6, 0.6], WHITEWASH, collide=False)
    wall_sign(b, x0 - 0.36, y + 14.6, 0.0, 14.0, 1.6, sign_decal("AUCTION", WHITEWASH, BARN_RED, 7.0), "x-",
              WHITEWASH)
    # the cupola
    cx = (x0 + x1) / 2.0
    b.box([cx, y + 23.6, 0.0], [5.0, 4.6, 5.0], WHITEWASH)
    b.cone([cx, y + 27.2, 0.0], [6.4, 2.6, 6.4], "#4a3a30")
    RIGS["vanes"].append((cx, y + 28.7, 0.0))
    # the sale ring, the bleachers, the stand
    rx0, rx1, rz0, rz1 = 162.0, 182.0, -9.0, 9.0
    b.box([(rx0 + rx1) / 2.0, y + 0.08, 0.0], [rx1 - rx0 - 1.0, 0.16, rz1 - rz0 - 1.0], "#c8a06a", collide=False)
    rposts: set = set()
    _fence(b, "x", rz0, rx0, rx1, y, posts=rposts, colour=WHITEWASH, h=3.6, gaps=[(170.0, 174.0)])
    _fence(b, "x", rz1, rx0, rx1, y, posts=rposts, colour=WHITEWASH, h=3.6)
    _fence(b, "z", rx0, rz0, rz1, y, posts=rposts, colour=WHITEWASH, h=3.6, lift=0.1, gaps=[(-2.0, 2.0)])
    _fence(b, "z", rx1, rz0, rz1, y, posts=rposts, colour=WHITEWASH, h=3.6, lift=0.1)
    grandstand(b, rect(156.0, 188.0, -26.0, -14.0), "z+", base=y, tiers=3, colour=HORN, roof=BARN_RED)
    grandstand(b, rect(156.0, 188.0, 14.0, 26.0), "z-", base=y, tiers=3, colour=HORN, roof=BARN_RED)
    slab(b, rect(184.0, 191.0, -4.0, 4.0), y + 4.0, 4.0, PLANK_DARK)
    b.box([186.6, y + 5.2, 0.0], [0.6, 2.4, 6.0], PLANK)
    flight(b, "z", 12.0, 4.0, 186.0, 189.0, y, y + 4.0, PLANK, fill=y)
    b.mark("perch", 188.0, y + 4.0, 0.0)
    _keep(rect(x0 - 4.0, x1 + 4.0, z0 - 2.0, z1 + 2.0))
    RIGS["cattle"].append((rx0 + 2.0, rx1 - 2.0, rz0 + 2.0, rz1 - 2.0, y, 2, "cattle"))
    # the scale house and its platform outside the east doors
    sx0, sx1, sz0, sz1 = 210.0, 224.0, -7.0, 7.0
    building(b, rect(sx0, sx1, sz0, sz1), y, 7.0, WHITEWASH, roof_colour=BARN_RED, doors={"x-": [(-2.0, 2.0, y + 5.6)]},
             windows={"z+": [(213.0, 219.0, y + 2.6, y + 5.0)]}, glass=True, lights=WARM)
    threshold(b, rect(sx0, sx1, sz0, sz1), "x-", (-2.0, 2.0))
    gable(b, rect(sx0, sx1, sz0, sz1), y + 8.2, BARN_RED, "x", 2, 1.0, 0.5)
    wall_sign(b, (sx0 + sx1) / 2.0, y + 6.4, sz1 + 0.36, 8.0, 1.0, sign_decal("SCALES", WHITEWASH, BARN_RED, 5.0),
              "z+", WHITEWASH)
    slab(b, rect(197.0, 209.0, -8.0, 8.0), y + 0.4, 0.4, PLANK)
    _fence(b, "x", -8.6, 197.0, 209.0, y + 0.4, colour=WHITEWASH, h=3.0)
    _keep(rect(196.0, sx1 + 2.0, sz0 - 3.0, sz1 + 2.0))


# ============================================================= main street
def _front(b: ArenaArea, area, side: str, y: float, colour: str, name: str, sign_bg: str, sign_fg: str,
           heights=(8.0, 7.0), false_front: float = 4.0, roof: str = "#4a3a30", door_w: float = 4.0) -> None:
    """A Main Street building: storeys, a door and windows on the street,
    a false front standing up over the roof with the name painted on it,
    a plank boardwalk and its awning, a hitching rail."""
    x0, x1, z0, z1 = area
    zc = (z0 + z1) / 2.0
    total = sum(heights)
    wins = []
    for k, h in enumerate(heights):
        base = sum(heights[:k])
        wins.append({side: [(z0 + 2.0, zc - door_w / 2.0 - 2.0, y + base + 2.6, y + base + h - 1.6),
                            (zc + door_w / 2.0 + 2.0, z1 - 2.0, y + base + 2.6, y + base + h - 1.6)]})
    storeyed(b, area, list(heights), colour, roof=roof,
             doors={side: [(zc - door_w / 2.0, zc + door_w / 2.0, y + 6.4)]}, windows=wins, base=y)
    threshold(b, area, side, (zc - door_w / 2.0, zc + door_w / 2.0), y0=y)
    face = x1 if side == "x+" else x0
    e = 1.0 if side == "x+" else -1.0
    b.box([face, y + total + false_front / 2.0 + 0.6, zc], [0.8, false_front + 1.2, z1 - z0], colour)
    b.box([face, y + total + false_front + 1.4, zc], [1.4, 0.4, z1 - z0 + 0.6], roof)
    wall_sign(b, face + e * 0.76, y + total + false_front / 2.0 + 0.4, zc, z1 - z0 - 3.0, false_front - 0.6,
              sign_decal(name, sign_bg, sign_fg, (z1 - z0 - 3.0) / (false_front - 0.6)), side, sign_bg)
    # the boardwalk, its awning on posts, the hitching rail
    walk = rect(face, face + e * 3.4, z0, z1) if e > 0 else rect(face - 3.4, face, z0, z1)
    slab(b, rect(min(walk[0], walk[1]), max(walk[0], walk[1]), z0, z1), y + 0.6, 0.6, PLANK)
    awning_x = face + e * 1.7
    b.box([awning_x, y + 6.8, zc], [3.6, 0.3, z1 - z0], roof)
    for zz in (z0 + 0.4, z1 - 0.4):
        b.box([face + e * 3.2, y + 3.7, zz], [0.4, 6.2, 0.4], PLANK_DARK)
    rail_x = face + e * 4.6
    b.box([rail_x, y + 2.0, zc], [0.3, 0.3, min(8.0, z1 - z0 - 4.0)], PLANK_DARK)
    for zz in (zc - min(4.0, (z1 - z0 - 4.0) / 2.0), zc + min(4.0, (z1 - z0 - 4.0) / 2.0)):
        b.box([rail_x, y + 1.0, zz], [0.4, 2.0, 0.4], PLANK_DARK)
    _keep(rect(min(x0, rail_x) - 1.0, max(x1, rail_x) + 1.0, z0 - 1.0, z1 + 1.0))


def _main_street(b: ArenaArea, rng: random.Random) -> None:
    """Main Street, which is the cattle trail: when the herd comes it
    thunders down between the boardwalks.  The Golden Steer saloon and its
    balcony, the bank, the sheriff's office and jail, the general store, the
    barber's (his pole turning) and the telegraph office on the west side;
    the Drovers' Cottage, the livery stable, the drovers' corral and the
    smithy on the east; lanterns strung across the street."""
    y = TRAIL_Y
    west = ((rect(72.0, 101.0, 100.0, 128.0), "#c86a3a", "GOLDEN STEER", "#f2d27a", "#5a2a1a", (8.0, 7.0)),
            (rect(74.0, 104.0, 134.0, 154.0), "#8a4a3a", "BANK", HORN, "#2a2a2e", (9.0,)),
            (rect(74.0, 107.0, 160.0, 178.0), "#9a8a6a", "SHERIFF", HORN, "#2a2a2e", (8.0,)),
            (rect(74.0, 110.0, 184.0, 206.0), "#5a8a7a", "GENERAL STORE", HORN, "#2a3a2a", (8.0, 6.0)),
            (rect(78.0, 100.0, 212.0, 226.0), "#e8dcc8", "BARBER", BARN_RED, HORN, (7.0,)),
            (rect(78.0, 104.0, 230.0, 244.0), "#b8905a", "TELEGRAPH", HORN, "#2a2a2e", (7.0,)))
    for area, colour, name, bg, fg, heights in west:
        _front(b, area, "x+", y, colour, name, bg, fg, heights)
    east = ((rect(140.0, 174.0, 140.0, 170.0), "#d8c8a0", "DROVERS COTTAGE", "#2f4a6a", HORN, (8.0, 7.0, 7.0)),
            (rect(146.0, 184.0, 176.0, 204.0), BARN_RED, "LIVERY", WHITEWASH, BARN_RED, (12.0,)))
    for area, colour, name, bg, fg, heights in east:
        _front(b, area, "x-", y, colour, name, bg, fg, heights, door_w=8.0 if name == "LIVERY" else 4.0)
    # the saloon's balcony over its boardwalk, the swinging doors
    sx1 = 101.0
    slab(b, rect(sx1, sx1 + 3.4, 100.0, 128.0), y + 8.6, 0.4, PLANK)
    b.box([sx1 + 3.2, y + 9.5, 114.0], [0.3, 1.4, 28.0], PLANK_DARK)
    for zz in (101.0, 114.0, 127.0):
        b.box([sx1 + 3.2, y + 4.6, zz], [0.4, 7.6, 0.4], PLANK_DARK)
    # the jail's barred window, the store's goods, the barber's pole
    for k in range(4):
        b.box([107.1, y + 4.2, 173.6 + k * 0.7], [0.2, 4.6, 0.2], "#2a2a2e", material="metal", collide=False)
    for k in range(4):
        b.cyl([112.0, y + 1.4, 190.0 + k * 2.6], [1.8, 1.6, 1.8], "#8a5a3a")
    b.box([112.2, y + 1.6, 201.0], [1.8, 2.0, 2.6], "#c8a070")
    RIGS.setdefault("poles", []).append((102.0, y + 0.6, 214.0))
    b.cyl([102.0, y + 2.6, 214.0], [0.7, 4.0, 0.7], WHITEWASH)
    # the drovers' corral: the call gate on its trail side, horses in it
    cposts: set = set()
    _fence(b, "z", 156.0, 210.0, 229.0, y, posts=cposts, gaps=[(216.0, 222.0)])
    _fence(b, "x", 210.0, 156.0, 190.0, y, posts=cposts, lift=0.1)
    _fence(b, "x", 229.0, 156.0, 190.0, y, posts=cposts, lift=0.1)
    _fence(b, "z", 190.0, 210.0, 229.0, y, posts=cposts)
    RIGS["horses"].append((158.0, 188.0, 212.0, 227.0, y, 4, "horse"))
    _keep(rect(154.0, 192.0, 208.0, 231.0))
    # the smithy, its forge glowing, an anvil and a wagon wheel outside
    sm = rect(191.4, 215.4, 172.6, 196.6)
    building(b, sm, y, 8.0, "#6a5a4a", roof_colour="#3a3030", doors={"x-": [(178.6, 190.6, 6.6)]},
             windows={"z+": [(197.4, 209.4, y + 2.6, y + 5.4)]}, glass=False, lights=WARM)
    threshold(b, sm, "x-", (178.6, 190.6))
    b.box([199.4, y + 1.4, 190.6], [5.0, 2.8, 4.0], "#5a5a60")
    b.sphere([199.4, y + 3.0, 190.6], [3.0, 0.8, 2.4], "#ff7a2a", material="neon", collide=False)
    b.box([207.4, y + 9.6, 190.6], [2.0, 6.0, 2.0], "#4a3a30")
    RIGS["flame"].append((199.4, y + 3.2, 190.6, 0.7))
    RIGS["smoke"].append((207.4, y + 13.0, 190.6))
    b.box([185.0, y + 1.0, 180.0], [1.6, 1.0, 3.2], "#2a2a2e", material="metal")
    b.cyl([185.0, y + 0.5, 180.0], [1.4, 1.0, 1.4], "#5a4030")
    _keep(rect(sm[0] - 7.0, sm[1] + 2.0, sm[2] - 2.0, sm[3] + 2.0))
    # lanterns strung across the street from posts on the boardwalks
    for z in (110.0, 148.0, 190.0):
        tx = trail_x(z)
        for x in (tx - 14.6, tx + 14.6):
            b.box([x, y + 6.0, z], [0.5, 12.0, 0.5], PLANK_DARK)
        RIGS["lights"].append(((tx - 14.6, y + 11.6, z), (tx + 14.6, y + 11.6, z)))
        _keep(rect(tx - 16.0, tx - 13.0, z - 1.0, z + 1.0))
        _keep(rect(tx + 13.0, tx + 16.0, z - 1.0, z + 1.0))
    # water troughs at the hitching rails
    for x, z in ((106.6, 118.0), (110.6, 140.0), (140.6, 186.0), (136.6, 160.0)):
        b.box([x, y + 0.7, z], [1.6, 1.4, 5.0], "#6a4a30")
        b.box([x, y + 1.42, z], [1.2, 0.06, 4.6], "#4a8ab0", collide=False)


# =================================================================== rodeo
def _rodeo(b: ArenaArea, rng: random.Random, land: Land) -> None:
    """The rodeo grounds in the west: the arena's white fence, grandstands
    under striped roofs on both long sides, the bucking chutes at the west
    end with a catwalk over them, the announcer's booth on stilts at the
    east end, barrels set out for the barrel race -- and a bronc bucking
    round the arena with a cowboy hanging on."""
    x0, x1, z0, z1 = ARENA
    y = 2.0
    posts: set = set()
    _fence(b, "x", z0, x0, x1, y, posts=posts, colour=WHITEWASH)
    _fence(b, "x", z1, x0, x1, y, posts=posts, colour=WHITEWASH)
    _fence(b, "z", x0, z0, z1, y, posts=posts, colour=WHITEWASH, lift=0.1,
           gaps=[(-14.0, -10.0), (-4.0, 0.0), (6.0, 10.0)])
    _fence(b, "z", x1, z0, z1, y, posts=posts, colour=WHITEWASH, lift=0.1, gaps=[(-4.0, 4.0)])
    grandstand(b, rect(x0 + 8.0, x1 - 10.0, z0 - 18.0, z0 - 4.0), "z+", base=y, tiers=4, colour=HORN, roof=BARN_RED)
    grandstand(b, rect(x0 + 8.0, x1 - 10.0, z1 + 4.0, z1 + 18.0), "z-", base=y, tiers=4, colour=HORN, roof=NAVY)
    # the bucking chutes
    for zz in (-20.0, -12.0, -4.0, 4.0, 12.0):
        b.box([x0 - 6.0, y + 3.0, zz], [10.0, 6.0, 0.5], PLANK_DARK)
    for k in range(4):
        cz = -16.0 + k * 8.0
        b.box([x0 - 10.8, y + 3.0, cz], [0.5, 6.0, 7.2], PLANK_DARK)
        b.box([x0 - 6.0, y + 0.1, cz], [9.0, 0.2, 7.0], DIRT, collide=False)
        wall_sign(b, x0 - 6.0, y + 4.6, cz + 4.61, 2.4, 1.0, sign_decal(str(k + 1), HORN, "#2a2a2e", 2.4),
                  "z+", HORN)
    slab(b, rect(x0 - 11.2, x0 - 0.8, -20.7, -19.3), y + 6.5, 0.5, PLANK)
    slab(b, rect(x0 - 11.2, x0 - 0.8, 11.3, 12.7), y + 6.5, 0.5, PLANK)
    flight(b, "z", -32.0, -20.7, x0 - 10.0, x0 - 6.0, y, y + 6.5, PLANK, fill=y)
    _keep(rect(x0 - 12.0, x0 + 1.0, z0 - 2.0, z1 + 2.0))
    # the announcer's booth on stilts at the east end
    bx0, bx1, bz0, bz1 = x1 + 6.0, x1 + 16.0, -6.0, 6.0
    for xx in (bx0 + 0.5, bx1 - 0.5):
        for zz in (bz0 + 0.5, bz1 - 0.5):
            b.box([xx, y + 5.0, zz], [0.8, 10.0, 0.8], PLANK_DARK)
    slab(b, rect(bx0, bx1, bz0, bz1), y + 10.0, 0.5, PLANK)
    b.box([bx1 - 0.3, y + 12.0, 0.0], [0.6, 4.0, bz1 - bz0], WHITEWASH)
    for zz in (bz0 + 0.3, bz1 - 0.3):
        b.box([(bx0 + bx1 - 0.6) / 2.0, y + 11.0, zz], [bx1 - bx0 - 0.6, 2.0, 0.6], WHITEWASH)
    slab(b, rect(bx0 - 0.6, bx1 + 0.6, bz0 - 0.6, bz1 + 0.6), y + 15.4, 0.5, BARN_RED)
    for zz in (bz0 + 0.3, bz1 - 0.3):
        b.box([bx0 + 0.3, y + 12.7, zz], [0.4, 5.4, 0.4], PLANK_DARK)
    wall_sign(b, bx0 - 0.1, y + 16.6, 0.0, 10.0, 1.6, sign_decal("RODEO", GOLD, BARN_RED, 5.0), "x-", GOLD)
    flight(b, "z", bz1 + 14.0, bz1, bx1 - 4.0, bx1 - 0.8, y, y + 10.0, PLANK, fill=y)
    b.mark("perch", bx0 + 4.0, y + 10.0, 0.0)
    _keep(rect(bx0 - 2.0, bx1 + 2.0, bz0 - 2.0, bz1 + 16.0))
    # barrels for the barrel race, flags at the corners
    for bx, bz in ((-292.0, -14.0), (-292.0, 14.0), (-252.0, 0.0)):
        b.cyl([bx, y + 1.5, bz], [2.6, 3.0, 2.6], ("#2f6aa8", BARN_RED, GOLD)[int(bx + bz) % 3])
    for fx, fz in ((x0 - 2.0, z0 - 2.0), (x1 + 2.0, z0 - 2.0), (x0 - 2.0, z1 + 2.0), (x1 + 2.0, z1 + 2.0)):
        b.cyl([fx, y + 8.0, fz], [0.5, 16.0, 0.5], WHITEWASH, material="metal")
        RIGS["flags"].append(((fx, y + 15.4, fz), [BARN_RED, HORN, NAVY]))
    _keep(rect(x0 - 3.0, x1 + 3.0, z0 - 20.0, z1 + 20.0))
    RIGS["bronco"] = ((x0 + x1) / 2.0 + 6.0, y, 0.0, 26.0, 16.0)


# ==================================================================== camp
def _camp(b: ArenaArea, rng: random.Random, land: Land) -> None:
    """The trail crew's camp: the chuckwagon with its tailgate down, the
    fire with the coffee on, bedrolls and tents, saddles on a log, and the
    remuda in a rail corral."""
    fx, fz = CAMP
    y = 2.0
    camp_fire(b, fx, fz, base=y)
    RIGS["flame"].append((fx, y + 0.8, fz, 1.0))
    RIGS["smoke"].append((fx, y + 3.0, fz))
    cook_wagon(b, fx - 14.0, fz + 10.0, along="x", base=y)
    b.box([fx - 20.6, y + 1.0, fz + 10.0], [1.6, 0.3, 3.6], PLANK, collide=False)
    for k, (tx, tz, along) in enumerate(((fx + 14.0, fz + 14.0, "z"), (fx + 18.0, fz - 8.0, "x"),
                                          (fx - 6.0, fz - 14.0, "x"))):
        pup_tent(b, tx, tz, along=along, base=y, colour=("#d8ccae", "#c8b898", "#e0d4b8")[k])
    for k in range(3):
        a = 2.4 + k * 0.7
        lx, lz = fx + math.cos(a) * 6.0, fz + math.sin(a) * 6.0
        b.cyl([lx, y + 0.6, lz], [1.2, 4.0, 1.2], "#6a4a30", r=[0, -a, math.pi / 2.0])
    for k in range(2):
        b.box([fx + 4.0 + k * 2.6, y + 1.5, fz + 6.0], [2.0, 1.2, 2.6], "#7a4a2a")
        b.box([fx + 4.0 + k * 2.6, y + 2.2, fz + 6.0], [1.0, 0.4, 1.4], "#5a3a22")
    _keep(rect(fx - 22.0, fx + 22.0, fz - 18.0, fz + 18.0))
    # the remuda's corral
    r0x, r1x, r0z, r1z = REMUDA
    posts: set = set()
    _fence(b, "x", r0z, r0x, r1x, y, posts=posts)
    _fence(b, "x", r1z, r0x, r1x, y, posts=posts, gaps=[(-184.0, -178.0)])
    _fence(b, "z", r0x, r0z, r1z, y, posts=posts, lift=0.1)
    _fence(b, "z", r1x, r0z, r1z, y, posts=posts, lift=0.1)
    b.box([r1x - 4.0, y + 0.6, r0z + 4.0], [2.0, 1.2, 5.0], "#6a5a48")
    b.box([r1x - 4.0, y + 1.25, r0z + 4.0], [1.6, 0.1, 4.6], "#4a8ab0", collide=False)
    RIGS["horses"].append((r0x + 2.0, r1x - 2.0, r0z + 2.0, r1z - 2.0, y, 5, "horse"))
    _keep(rect(r0x - 2.0, r1x + 2.0, r0z - 2.0, r1z + 2.0))


# =============================================================== boot hill
BOOT_Y: dict = {}


def _boot_hill(b: ArenaArea, rng: random.Random, land: Land) -> None:
    """Boot Hill: crosses and headstones in rows on the knoll's top inside a
    picket fence, one grave fresh with a shovel in the mound, a dead tree
    with the vultures over it; and the white church at its foot."""
    hx, hz = BOOT_HILL[0], BOOT_HILL[1]
    y = BOOT_Y.get("top", land.height(hx, hz))
    gx0, gx1, gz0, gz1 = hx - 14.0, hx + 14.0, hz - 10.0, hz + 10.0
    posts: set = set()
    for zz, gaps in ((gz0, ()), (gz1, [(hx - 2.0, hx + 2.0)])):
        _fence(b, "x", zz, gx0, gx1, y, posts=posts, colour=WHITEWASH, h=2.4, gaps=gaps)
    for xx in (gx0, gx1):
        _fence(b, "z", xx, gz0, gz1, y, posts=posts, colour=WHITEWASH, h=2.4, lift=0.06)
    for row in range(3):
        for k in range(6):
            x, z = gx0 + 3.0 + k * 4.4, gz0 + 3.0 + row * 5.0
            if row == 1 and k == 2:
                continue
            b.box([x, y + 0.3, z + 1.2], [1.6, 0.6, 2.8], "#8a6a48")
            if (row + k) % 3 == 0:
                b.box([x, y + 1.2, z], [1.4, 2.4, 0.4], "#a8a090")
                b.cyl([x, y + 2.4, z], [1.4, 0.4, 1.4], "#a8a090", r=[math.pi / 2.0, 0, 0], collide=False)
            else:
                b.box([x, y + 1.5, z], [0.3, 3.0, 0.3], PLANK)
                b.box([x, y + 2.3, z], [1.6, 0.3, 0.3], PLANK, collide=False)
    # the fresh grave and its shovel
    fx, fz = gx0 + 3.0 + 2 * 4.4, gz0 + 8.0
    b.box([fx, y + 0.5, fz + 1.2], [1.8, 1.0, 3.0], "#6a4a30")
    b.box([fx + 0.5, y + 2.0, fz + 1.4], [0.2, 3.0, 0.2], "#6a4a30", collide=False, r=[0.0, 0.0, 0.3])
    b.box([fx + 0.2, y + 0.9, fz + 1.4], [0.8, 1.0, 0.1], "#8a8a92", material="metal", collide=False)
    # the dead tree
    tx, tz = gx1 - 4.0, gz1 - 3.0
    b.cyl([tx, y + 5.0, tz], [1.4, 10.0, 1.4], "#5a4a3a")
    for k, (len_, yaw, pitch, h) in enumerate(((6.0, 0.4, 0.7, 8.0), (5.0, 2.6, 0.6, 9.0), (4.0, 4.4, 0.9, 7.0),
                                               (3.6, 1.6, 0.5, 9.6))):
        b.box([tx + math.sin(yaw) * len_ * 0.35, y + h, tz + math.cos(yaw) * len_ * 0.35], [0.5, 0.5, len_],
              "#5a4a3a", r=[-pitch, yaw, 0.0], collide=False)
    RIGS["vultures"] = (tx, y + 30.0, tz)
    wall_sign(b, hx, y + 2.6, gz1 + 0.6, 7.0, 1.0, sign_decal("BOOT HILL", PLANK, HORN, 7.0), "z+", PLANK)
    b.mark("perch", hx - 6.0, y, gz1 - 1.0)
    _keep(rect(gx0 - 2.0, gx1 + 2.0, gz0 - 2.0, gz1 + 2.0))
    # the church
    cx0, cx1, cz0, cz1 = CHURCH
    cy = 4.0
    building(b, CHURCH, cy, 9.0, WHITEWASH, roof_colour="#5a3a2a",
             doors={"z+": [((cx0 + cx1) / 2.0 - 2.0, (cx0 + cx1) / 2.0 + 2.0, 7.0)]},
             windows={"x-": [(cz0 + 6.0, cz0 + 11.0, 3.0, 7.0), (cz0 + 18.0, cz0 + 23.0, 3.0, 7.0)],
                      "x+": [(cz0 + 6.0, cz0 + 11.0, 3.0, 7.0), (cz0 + 18.0, cz0 + 23.0, 3.0, 7.0)]},
             glass=True, lights=WARM)
    threshold(b, CHURCH, "z+", ((cx0 + cx1) / 2.0 - 2.0, (cx0 + cx1) / 2.0 + 2.0), y0=cy)
    gable(b, CHURCH, cy + 10.2, "#5a3a2a", "z", 4, 1.2, 0.6)
    sx = (cx0 + cx1) / 2.0
    b.box([sx, cy + 15.0, cz1 - 3.0], [5.0, 10.0, 5.0], WHITEWASH)
    b.box([sx, cy + 17.6, cz1 - 0.45], [2.4, 3.0, 0.1], "#2a2a2e", collide=False)
    b.cone([sx, cy + 23.0, cz1 - 3.0], [5.6, 6.0, 5.6], "#5a3a2a")
    b.cone([sx, cy + 17.4, cz1 - 3.0], [1.8, 1.8, 1.8], GOLD, material="metal", collide=False)
    RIGS["vanes"].append((sx, cy + 26.2, cz1 - 3.0))
    _keep(rect(cx0 - 3.0, cx1 + 3.0, cz0 - 3.0, cz1 + 4.0))


# ============================================================ west of town
def _yard_west(b: ArenaArea, rng: random.Random, land: Land) -> None:
    """The railroad's water tank by the Longhorn yard -- a wooden tub on
    legs, its spout swung back, a stair up to its walk (a perch) -- and the
    cowhands' bunkhouse: log walls, a porch with rockers, a woodpile, a
    horseshoe pitch."""
    tx, tz = TANK
    y = 2.0
    for dx in (-5.0, 5.0):
        for dz in (-5.0, 5.0):
            b.box([tx + dx, y + 5.0, tz + dz], [1.0, 10.0, 1.0], PLANK_DARK)
    slab(b, rect(tx - 7.4, tx + 7.4, tz - 7.4, tz + 7.4), y + 10.4, 0.4, PLANK)
    b.cyl([tx, y + 14.6, tz], [13.0, 8.0, 13.0], "#8a6040")
    for k in range(3):
        b.cyl([tx, y + 11.6 + k * 3.0, tz], [13.2, 0.3, 13.2], "#2a2a2e", collide=False, material="metal")
    b.cone([tx, y + 20.2, tz], [14.0, 3.2, 14.0], "#4a3a30")
    b.box([tx, y + 12.0, tz + 8.4], [0.8, 0.8, 4.4], "#3a3a40", collide=False, material="metal", r=[0.5, 0, 0])
    flight(b, "x", tx - 26.0, tx - 7.4, tz - 1.5, tz + 1.5, y, y + 10.4, PLANK, fill=y)
    b.mark("perch", tx + 3.0, y + 10.4, tz)
    _keep(rect(tx - 27.0, tx + 8.0, tz - 8.0, tz + 9.0))
    # the bunkhouse
    x0, x1, z0, z1 = BUNKHOUSE
    by = 3.0
    building(b, BUNKHOUSE, by, 8.0, "#8a6040", roof_colour="#4a3a30", doors={"z+": [(-242.0, -238.0, 6.4)]},
             windows={"z+": [(-258.0, -250.0, 2.6, 5.4), (-230.0, -222.0, 2.6, 5.4)]}, glass=True, lights=WARM)
    threshold(b, BUNKHOUSE, "z+", (-242.0, -238.0), y0=by)
    gable(b, BUNKHOUSE, by + 9.2, "#4a3a30", "x", 3, 1.0, 0.6)
    for k in range(5):
        b.box([(x0 + x1) / 2.0, by + 1.0 + k * 1.5, z1 + 0.15], [x1 - x0, 0.3, 0.3], "#6a4a30", collide=False)
    slab(b, rect(x0, x1, z1, z1 + 5.0), by + 0.6, 0.6, PLANK)
    b.box([(x0 + x1) / 2.0, by + 7.0, z1 + 2.5], [x1 - x0, 0.3, 5.4], "#4a3a30")
    for xx in (x0 + 0.5, x1 - 0.5, (x0 + x1) / 2.0 - 8.0, (x0 + x1) / 2.0 + 8.0):
        b.box([xx, by + 3.8, z1 + 4.8], [0.4, 6.4, 0.4], PLANK_DARK)
    for xx in (-250.0, -230.0):
        b.box([xx, by + 1.6, z1 + 2.6], [1.4, 0.3, 1.4], "#6a4a30")
        b.box([xx, by + 2.6, z1 + 2.0], [1.4, 2.0, 0.2], "#6a4a30")
    b.box([x1 - 3.0, by + 9.6, z0 + 4.0], [2.0, 5.0, 2.0], "#7a6a58")
    RIGS["smoke"].append((x1 - 3.0, by + 12.6, z0 + 4.0))
    for k in range(6):
        b.cyl([x0 - 3.0, by + 0.5 + (k // 3) * 1.0, z0 + 4.0 + (k % 3) * 1.1], [1.0, 3.0, 1.0], "#8a6a48",
              r=[math.pi / 2.0, 0, 0])
    _keep(rect(x0 - 5.0, x1 + 2.0, z0 - 2.0, z1 + 6.0))


# =================================================================== creek
def _creek(b: ArenaArea, rng: random.Random, land: Land) -> None:
    """Cottonwood Creek through the south-west: shallow water down a cut in
    the prairie, cottonwoods along its banks; the grist mill on its north
    bank with the wheel turning in the water; the hide yard, hides stretched
    on their frames, below the Chisholm yard."""
    for j in range(land.nz):
        for i in range(land.nx):
            if not land.hole[j][i]:
                continue
            x = land.x0 + (i + 0.5) * land.cell
            z = land.z0 + (j + 0.5) * land.cell
            b.box([x, 0.04, z], [land.cell, 0.08, land.cell], "#5a6a4a", collide=False)
            b.water(x, z, land.cell, land.cell, 0.4, "#5aa0b8")
    for k, (x, z) in enumerate(((-372.0, 214.0), (-300.0, 170.0), (-286.0, 222.0), (-190.0, 222.0),
                                (-168.0, 172.0), (-120.0, 214.0), (-74.0, 186.0), (-70.0, 236.0))):
        if any(kk[0] - 4 < x < kk[1] + 4 and kk[2] - 4 < z < kk[3] + 4 for kk in KEEP):
            continue
        base = land.height(x, z) - 0.3
        b.cyl([x, base + 4.0, z], [1.6, 8.0, 1.6], "#7a6a5a")
        b.sphere([x, base + 11.0, z], [11.0, 7.0, 10.0], ("#8ab84e", "#9ac85a", "#7aa848")[k % 3], collide=False)
        b.sphere([x + 2.4, base + 13.6, z - 1.4], [6.0, 4.6, 6.0], "#a8d066", collide=False)
        _keep(rect(x - 2.0, x + 2.0, z - 2.0, z + 2.0))
    # the mill, its wheel on the creek side
    mx, mz = MILL
    mill = rect(mx - 14.0, mx + 14.0, mz - 9.0, mz + 9.0)
    storeyed(b, mill, [8.0, 6.0], "#b89a6a", roof="#5a3a2a", doors={"z-": [(mx - 2.0, mx + 2.0, 6.4)]},
             windows=[{"z-": [(mx - 11.0, mx - 6.0, 4.4, 7.6)]}, {"z-": [(mx + 4.0, mx + 10.0, 12.4, 14.6)]}],
             base=2.0)
    threshold(b, mill, "z-", (mx - 2.0, mx + 2.0), y0=2.0)
    gable(b, mill, 2.0 + 14.0 + 1.2, "#5a3a2a", "x", 3, 1.2, 0.6)
    b.box([mx + 6.0, 2.0 + 8.0, mz + 9.6], [1.0, 1.0, 1.4], "#3a3a40", material="metal", collide=False)
    RIGS["wheel"] = (mx + 6.0, 6.2, mz + 11.0)
    wall_sign(b, mx, 2.0 + 15.6, mz - 9.36, 12.0, 1.4, sign_decal("COTTONWOOD MILL", HORN, "#5a2a1a", 8.5), "z-", HORN)
    _keep(rect(mill[0] - 2.0, mill[1] + 2.0, mill[2] - 2.0, mill[3] + 6.0))
    # the hide yard
    hx, hz = HIDES
    for k in range(6):
        x = hx - 15.0 + (k % 3) * 15.0
        z = hz - 6.0 + (k // 3) * 12.0
        for dx in (-5.0, 5.0):
            b.box([x + dx, 2.0 + 3.6, z], [0.5, 7.2, 0.5], PLANK_DARK)
        b.box([x, 2.0 + 7.0, z], [10.6, 0.4, 0.4], PLANK_DARK)
        b.box([x, 2.0 + 4.0, z], [8.2, 5.6, 0.2], ("#8a5a3a", "#5a3a28", "#c8a070", "#3a2a22")[k % 4])
        if k % 2 == 0:
            b.box([x - 1.0, 2.0 + 4.6, z + 0.12], [2.6, 2.0, 0.06], "#f2ece0", collide=False)
    b.box([hx + 14.0, 2.0 + 0.8, hz + 12.0], [5.0, 1.6, 3.0], "#8a6a48")
    _keep(rect(hx - 22.0, hx + 22.0, hz - 9.0, hz + 15.0))


def _windpump(b: ArenaArea, land: Land) -> None:
    """A windpump over a round stock tank west of the trail."""
    px, pz = 80.0, -24.0
    y = TRAIL_Y
    for dx in (-2.4, 2.4):
        for dz in (-2.4, 2.4):
            b.box([px + dx * 0.7, y + 9.0, pz + dz * 0.7], [0.5, 18.0, 0.5], "#6a6a64", material="metal",
                  r=[dz * 0.02, 0.0, -dx * 0.02])
    slab(b, rect(px - 2.0, px + 2.0, pz - 2.0, pz + 2.0), y + 18.0, 0.3, PLANK)
    RIGS["pumps"].append((px, y + 19.4, pz))
    b.cyl([px + 9.0, y + 1.0, pz], [10.0, 2.0, 10.0], "#7a7a7e", material="metal")
    b.cyl([px + 9.0, y + 1.9, pz], [9.2, 0.2, 9.2], "#4a8ab0", collide=False)
    b.box([px + 3.4, y + 2.2, pz], [4.0, 0.4, 0.4], "#5a5a60", collide=False, material="metal")
    _keep(rect(px - 4.0, px + 15.0, pz - 6.0, pz + 6.0))


# ============================================================ new places
def _schooner(b: ArenaArea, x: float, z: float, along: str, base: float, cover: str = "#f2ece0") -> None:
    """A prairie schooner: its blue bed, the white bonnet on its hoops, big
    red wheels, the tongue down."""
    lu, lw = 12.0, 4.6
    size = [lu, 1.6, lw] if along == "x" else [lw, 1.6, lu]
    b.box([x, base + 2.0, z], size, "#3a5a8a")
    b.cyl([x, base + 4.0, z], [lw + 0.4, lu - 1.0, lw + 0.4], cover, collide=False,
          r=[0, 0, math.pi / 2.0] if along == "x" else [math.pi / 2.0, 0, 0])
    for e in (-1.0, 1.0):
        for g in (-1.0, 1.0):
            wx, wz = (x + e * 3.8, z + g * 2.6) if along == "x" else (x + g * 2.6, z + e * 3.8)
            b.cyl([wx, base + 1.5, wz], [3.0, 0.3, 3.0], "#a8321e", collide=False,
                  r=[math.pi / 2.0, 0, 0] if along == "x" else [0, 0, math.pi / 2.0])
    tx, tz = (x + lu / 2.0 + 3.0, z) if along == "x" else (x, z + lu / 2.0 + 3.0)
    b.box([tx, base + 0.7, tz], [6.4, 0.3, 0.3] if along == "x" else [0.3, 0.3, 6.4], PLANK_DARK, collide=False,
          r=[0, 0, 0.22] if along == "x" else [-0.22, 0, 0])


def _wagons(b: ArenaArea, rng: random.Random) -> None:
    """Emigrants passing through: four schooners drawn up in a ring, a fire
    in the middle with the pot on, a fiddle on a barrel, washing on a line
    from one bonnet to the next, their oxen grazing in the lee."""
    wx, wz = WAGONS
    y = 3.0
    for k, (dx, dz, along) in enumerate(((0.0, -20.0, "x"), (20.0, 0.0, "z"), (0.0, 20.0, "x"), (-20.0, 0.0, "z"))):
        _schooner(b, wx + dx, wz + dz, along, y, cover=("#f2ece0", "#ece4d0", "#f6f0e4", "#e8dcc4")[k])
    camp_fire(b, wx, wz, base=y)
    RIGS["flame"].append((wx, y + 0.8, wz, 0.9))
    RIGS["smoke"].append((wx, y + 3.2, wz))
    for k in range(3):
        b.cyl([wx + 7.0 + k * 1.3, y + 1.0, wz + 7.0], [1.6, 2.0, 1.6], "#8a5a3a")
    b.box([wx + 8.3, y + 2.15, wz + 7.0], [0.4, 0.3, 1.8], "#6a3a1e", collide=False)
    for k in range(2):
        b.box([wx - 8.0, y + 0.6, wz - 6.0 + k * 3.0], [3.4, 1.2, 1.4], "#7a5a3a")
    RIGS["cattle"].append((wx - 30.0, wx - 14.0, wz + 26.0, wz + 34.0, y, 3, "cattle"))
    _keep(rect(wx - 30.0, wx + 30.0, wz - 28.0, wz + 34.0))


def _branding(b: ArenaArea, rng: random.Random, land: Land) -> None:
    """The branding pen: a stout rail corral, a snubbing post in the middle,
    the branding fire with its irons heating, calves waiting their turn, a
    rack of ropes and the tally board."""
    x0, x1, z0, z1 = BRANDING
    y = 3.0
    posts: set = set()
    _fence(b, "x", z0, x0, x1, y, posts=posts, colour=FENCE_DARK)
    _fence(b, "x", z1, x0, x1, y, posts=posts, colour=FENCE_DARK, gaps=[(30.0, 34.0)])
    _fence(b, "z", x0, z0, z1, y, posts=posts, colour=FENCE_DARK, lift=0.1)
    _fence(b, "z", x1, z0, z1, y, posts=posts, colour=FENCE_DARK, lift=0.1)
    b.cyl([32.0, y + 2.6, -176.0], [1.4, 5.2, 1.4], PLANK_DARK)
    fx, fz = 24.0, -168.0
    for k in range(6):
        a = k * math.pi / 3.0
        b.box([fx + math.cos(a) * 1.6, y + 0.3, fz + math.sin(a) * 1.6], [0.9, 0.6, 0.9], "#8a8478")
    b.sphere([fx, y + 0.4, fz], [2.0, 0.7, 2.0], "#ff6a2a", material="neon", collide=False)
    for k in range(3):
        b.box([fx + 0.8 - k * 0.8, y + 0.9, fz + 1.2], [0.15, 0.15, 3.4], "#3a3a40", material="metal",
              collide=False, r=[0.35, 0.0, 0.0])
    RIGS["flame"].append((fx, y + 0.5, fz, 0.6))
    RIGS["cattle"].append((x0 + 6.0, x1 - 2.0, z0 + 2.0, z1 - 10.0, y, 3, "cattle"))
    wall_sign(b, x1 + 0.4, y + 3.0, z1 - 4.0, 4.0, 2.4, sign_decal("TALLY 47", "#2a2a2e", HORN, 1.7), "x+", "#2a2a2e")
    b.box([x1 + 1.1, y + 1.4, z1 - 4.0], [0.6, 2.8, 0.6], PLANK_DARK)
    _keep(rect(x0 - 2.0, x1 + 3.0, z0 - 2.0, z1 + 2.0))


def _mansion(b: ArenaArea, rng: random.Random) -> None:
    """The cattle baron's house on its knoll: three storeys painted teal and
    cream with a pink trim, a round turret and its witch's hat, a porch all
    along the front, a picket fence and a gate, a rose bed."""
    x0, x1, z0, z1 = MANSION
    y = BOOT_Y.get("mansion", 4.0)
    storeyed(b, MANSION, [8.0, 7.0, 6.0], "#5ab0a0", roof="#5a3a4a",
             doors={"z+": [(258.0, 262.0, y + 6.4)]},
             windows=[{"z+": [(244.0, 250.0, y + 2.6, y + 6.0), (270.0, 276.0, y + 2.6, y + 6.0)],
                       "x-": [(-54.0, -48.0, y + 2.6, y + 6.0), (-40.0, -34.0, y + 2.6, y + 6.0)]},
                      {"z+": [(244.0, 250.0, y + 10.4, y + 13.6), (256.0, 264.0, y + 10.4, y + 13.6),
                              (270.0, 276.0, y + 10.4, y + 13.6)],
                       "x-": [(-54.0, -48.0, y + 10.4, y + 13.6), (-40.0, -34.0, y + 10.4, y + 13.6)]},
                      {"z+": [(250.0, 256.0, y + 17.4, y + 19.6), (264.0, 270.0, y + 17.4, y + 19.6)]}], base=y)
    threshold(b, MANSION, "z+", (258.0, 262.0), y0=y)
    gable(b, MANSION, y + 21.0 + 1.2, "#5a3a4a", "x", 4, 1.2, 0.6)
    for xx in (x0 - 0.15, x1 + 0.15):
        for zz in (z0 - 0.15, z1 + 0.15):
            b.box([xx, y + 10.5, zz], [1.0, 21.0, 1.0], "#f2e8d8")
    for k in range(3):
        b.box([(x0 + x1) / 2.0, y + 7.6 + k * 7.0, z1 + 0.25], [x1 - x0 - 1.6, 0.4, 0.5], "#f08aa8")
    # the turret on the corner
    tx, tz = x1, z1
    b.cyl([tx, y + 12.5, tz], [9.0, 25.0, 9.0], "#f2e8d8")
    for k in range(3):
        b.cyl([tx, y + 7.6 + k * 7.0, tz], [9.4, 0.5, 9.4], "#f08aa8")
    b.cone([tx, y + 29.0, tz], [10.4, 8.0, 10.4], "#5a3a4a")
    b.sphere([tx, y + 33.4, tz], [0.9, 0.9, 0.9], GOLD, material="metal", collide=False)
    RIGS["flags"].append(((tx, y + 37.6, tz), ["#5ab0a0", HORN, "#f08aa8"]))
    b.cyl([tx, y + 35.4, tz], [0.3, 4.6, 0.3], WHITEWASH, material="metal", collide=False)
    # the porch along the front
    slab(b, rect(x0, x1 - 4.0, z1, z1 + 6.0), y + 1.0, 1.0, PLANK)
    b.box([(x0 + x1 - 4.0) / 2.0, y + 7.4, z1 + 3.0], [x1 - x0 - 3.4, 0.4, 6.6], "#5a3a4a")
    for xx in range(int(x0) + 1, int(x1 - 4.0), 6):
        b.box([float(xx), y + 4.2, z1 + 5.6], [0.5, 6.4, 0.5], "#f2e8d8")
    b.box([(x0 + x1 - 4.0) / 2.0, y + 2.2, z1 + 5.7], [x1 - x0 - 4.6, 0.3, 0.3], "#f2e8d8")
    # the picket fence, its gate, the rose beds
    posts: set = set()
    fz = z1 + 14.0
    _fence(b, "x", fz, x0 - 6.0, x1 + 8.0, y, posts=posts, colour="#f2e8d8", h=2.2, gaps=[(256.0, 264.0)])
    for k in range(8):
        rx = x0 - 2.0 + k * 6.0
        if 254.0 < rx < 266.0:
            continue
        b.box([rx, y + 0.6, fz - 2.4], [3.6, 1.2, 2.0], "#6a4a30")
        b.sphere([rx, y + 1.6, fz - 2.4], [3.4, 1.4, 1.8], ("#e83a5a", "#f8a8c0", "#ffffff")[k % 3], collide=False)
    _keep(rect(x0 - 8.0, x1 + 10.0, z0 - 2.0, fz + 2.0))


def _haystacks(b: ArenaArea, rng: random.Random, land: Land) -> None:
    """Round haystacks about the prairie, a pitchfork left in one."""
    for k, (x, z) in enumerate(((-60.0, -110.0), (-44.0, -128.0), (60.0, -140.0), (78.0, -120.0),
                                (-170.0, 60.0), (-186.0, 76.0), (40.0, 100.0), (-80.0, 120.0),
                                (330.0, 40.0), (340.0, -40.0))):
        if _blocked(x, z) or not clear_of(rect(x - 5.0, x + 5.0, z - 5.0, z + 5.0), LANES, 12.0):
            continue
        base = min(land.height(x - 3.0, z - 3.0), land.height(x + 3.0, z + 3.0), land.height(x - 3.0, z + 3.0),
                   land.height(x + 3.0, z - 3.0)) - 0.4
        b.cyl([x, base + 2.6, z], [7.0, 5.2, 7.0], "#d8b860")
        b.sphere([x, base + 5.2, z], [7.2, 4.4, 7.2], "#e8c870", collide=False)
        if k % 3 == 0:
            b.box([x + 1.0, base + 7.4, z], [0.2, 4.0, 0.2], "#6a4a30", collide=False, r=[0.0, 0.0, 0.4])
        _keep(rect(x - 4.5, x + 4.5, z - 4.5, z + 4.5))


# ================================================================= scatter
def _scatter(b: ArenaArea, rng: random.Random, land: Land) -> None:
    """Prairie clutter: sagebrush, prickly pear, a bleached skull, hay bales,
    a wagon wheel against a rock, outcrops to take cover behind."""
    hx, hz = HALF
    tries = placed = 0
    while placed < 120 and tries < 2400:
        tries += 1
        x, z = rng.uniform(-hx + 12.0, hx - 12.0), rng.uniform(-hz + 14.0, hz - 14.0)
        if not clear_of(rect(x - 4.0, x + 4.0, z - 4.0, z + 4.0), LANES, 12.0) or _blocked(x, z):
            continue
        base = land.height(x, z)
        if abs(land.height(x + 3.0, z) - base) > 0.6 or abs(land.height(x, z + 3.0) - base) > 0.6:
            continue
        if base < 0.5:
            continue
        roll = rng.random()
        if roll < 0.42:
            sage(b, x, z, base=base, s=rng.uniform(0.8, 1.3))
        elif roll < 0.62:
            b.sphere([x, base + 1.0, z], [2.0, 2.0, 1.0], "#5a8a3a")
            b.sphere([x + 1.2, base + 2.2, z + 0.2], [1.6, 1.6, 0.8], "#5a8a3a", collide=False)
            b.sphere([x, base + 2.2, z], [0.5, 0.5, 0.5], "#e8508a", collide=False)
        elif roll < 0.72:
            skull(b, x, z, base=base, yaw=rng.uniform(0.0, math.pi))
        elif roll < 0.86:
            outcrop(b, x, z, rng.uniform(2.6, 4.4), rng.uniform(1.2, 2.2), rng.uniform(2.4, 3.6), base=base - 0.3,
                    colour=rng.choice([MESA, MESA_PALE, "#a87a5a"]))
        else:
            b.box([x, base + 1.0, z], [3.2, 2.0, 2.2], "#c8a858", studs=True)
        KEEP.append(rect(x - 4.0, x + 4.0, z - 4.0, z + 4.0))
        placed += 1


# ==================================================================== rigs
def _rigs(b: ArenaArea, land: Land) -> None:
    wind = [0.7, 0.3]
    yaw = math.atan2(-wind[0], -wind[1])
    b.rig("rr_weather", 0.0, 0.0, 0.0, weather="dust", wind=wind)
    for x0, x1, z0, z1, y, n, kind in RIGS["cattle"] + RIGS["horses"]:
        b.rig("rr_cattle", (x0 + x1) / 2.0, y, (z0 + z1) / 2.0, w=x1 - x0, d=z1 - z0, n=n, beast=kind,
              seed=round(x0 * 0.13 + z0 * 0.07, 2))
    for x, y, z, sz in RIGS["flame"]:
        b.rig("rr_flame", x, y, z, s=sz, wind=wind)
    for x, y, z in RIGS["smoke"]:
        b.rig("rr_smoke", x, y, z, wind=wind, rate=0.3, h=16.0, size=1.4, colour="#b8b0a4")
    for (x, y, z), colours in RIGS["flags"]:
        b.rig("rr_flag", x, y, z, w=3.6, h=2.2, yaw=yaw, colours=colours)
    for x, y, z in RIGS["vanes"]:
        b.rig("rr_vane", x, y, z, yaw=yaw)
    for a, q in RIGS["lights"]:
        b.rig("rr_lights", a[0], a[1], a[2], q=list(q), n=12, sag=2.2,
              colours=["#ffd27a", "#ff9a4a", "#ffe8b0"])
    for x, y, z in RIGS["pumps"]:
        b.rig("rr_windpump", x, y, z, yaw=yaw, r=4.4)
    for (x, y, z), yw, tilt, r in RIGS.get("clocks", []):
        b.rig("rr_clock", x, y, z, yaw=yw, tilt=tilt, r=r)
    for x, y, z in RIGS.get("poles", []):
        b.rig("rr_barber_pole", x, y + 4.6, z, h=3.0)
    if RIGS.get("bronco"):
        x, y, z, rx, rz = RIGS["bronco"]
        b.rig("rr_bronco", x, y, z, rx=rx, rz=rz)
    if RIGS.get("wheel"):
        x, y, z = RIGS["wheel"]
        b.rig("rr_waterwheel", x, y, z, r=5.2, yaw=0.0)
    if RIGS.get("vultures"):
        x, y, z = RIGS["vultures"]
        b.rig("rr_vultures", x, y, z, r=22.0, n=3)
    for k, (a, c) in enumerate((((-380.0, 2.0, -60.0), (-60.0, 2.0, -40.0)), ((380.0, 2.0, 40.0), (200.0, 2.0, 60.0)),
                                ((-60.0, 2.0, 140.0), (-360.0, 2.0, 120.0)))):
        b.rig("rr_tumbleweed", a[0], a[1], a[2], q=list(c), speed=10.0 + k, seed=k * 2.3)
