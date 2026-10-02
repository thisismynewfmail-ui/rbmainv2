"""St. Agnes Medical -- the hospital the army tried to quarantine.

Layout (north is +z)::

      z +280  ----------------------------- boundary ----------------------------
              FUEL YARD      |G| service yard, the helicopter    |R| APARTMENTS
              + salt dome    |a|    wreck, the generator house   |o|
      z +176  ...............|r|..... fire stair ................|a| ............
              PARKING GARAGE |a|  ST. AGNES MEDICAL CENTER  ER   |d| CLINIC
              (3 decks +     |g|  wards | lobby | ER        BAY  |  |
               the roof) ====|e|== skybridge onto the roof       |B|
      z  +36  ...............|S|... the front lot, the drop-off .|  |..........
              HEDGE MAZE     |t|   QUARANTINE CHECKPOINT        |  | STRIP MALL
                             | |   command tent, med tents       |  | laundromat
      z -190  ============== Mercy Avenue ===================================
              TRANSIT DEPOT    BASKETBALL COURT     CONSTRUCTION SITE
      z -280  ----------------------------- boundary ----------------------------

The army's quarantine checkpoint in front of the hospital is the safe room:
everyone deploys inside the command tent.

What this place is about is height.  The parking garage is three decks and a
roof joined by switchback ramps, and its third deck runs straight across a
glass skybridge onto the hospital roof and its helipad -- which the outside
fire stair also reaches.  Holding the roof is strong and the horde knows
every way up.  At ground level the hospital is a building you can fight
through room by room: wards, lobby, emergency, surgery, records.

The lure is the ambulance in the emergency bay: run its siren and every
infected nearby turns towards the bay.
"""
from __future__ import annotations

import math
import random

from .kit import (
    ASPHALT, COLD, CONCRETE, CONCRETE_DARK, CONCRETE_LIGHT, FLOOR, GLASS,
    HAZARD, LAMP, LINE_WHITE, LINE_YELLOW, PAVEMENT, PAVEMENT_DARK, RUST,
    SANDBAG, STEEL, STEEL_DARK, WARM, WOOD, WOOD_DARK, WOOD_LIGHT, Area,
    Surfaces, army_truck, barrel_prop, barrel_spot, barrier, bench, boundary,
    building, bus, car, chain_fence, crate, deploy_pad, dumpster, flight,
    flood, gable, ground, hesco, holed_wall, house, lamp_post, pallet_stack,
    rect, room_walls, sandbags, sign_decal, slab, solid_fence, strip_light,
    supply_ammo, supply_med, tent, threshold, treeline, van, wall_sign,
    watchtower)

HALF = 280.0
GRASS = "#3d5a3e"
SKY = {"top": "#0f1a2c", "horizon": "#4a6478", "sun": [-0.35, 0.55, 0.6],
       "clouds": 0.68, "tint": "#a8c4e0"}
AMBIENT = "#5c6c84"

ROAD_A = (-206.0, -190.0)        # Mercy Avenue, along x
ROAD_C = (-140.0, -124.0)        # Garage Street, along z
ROAD_B = (176.0, 192.0)          # Harbor Road, along z
HOSP = (-110.0, 90.0, 40.0, 170.0)
GARAGE = (-262.0, -150.0, -40.0, 124.0)
DECK = 10.0                      # deck spacing in the garage
CAMP = (-100.0, 90.0, -182.0, -62.0)
WHITE = "#dfe4e6"
SCRUB = "#5f8a8a"


def build(b: Area) -> None:
    rng = random.Random(0xA6E5)
    ground(b, GRASS)
    boundary(b, 30.0, "#1e2630", "#161c24", rng, horizon="city")
    s = Surfaces(b)
    _roads(b, s)
    _hospital(b, s)
    _garage(b, s, rng)
    _skybridge(b)
    _er_bay(b, s)
    _camp(b, s, rng)
    _maze(b, s, rng)
    _east_side(b, s, rng)
    _south(b, s, rng)
    _north(b, s, rng)
    _zombie_spawns(b)
    for x, z, name in ((0, 70, "the hospital lobby"), (-206, 40, "the parking garage"),
                       (-130, 103, "the skybridge"), (0, 136, "the helipad"),
                       (126, 80, "the ambulance bay"), (0, -120, "the checkpoint"),
                       (-206, -117, "the hedge maze"), (232, -120, "the strip mall"),
                       (150, -246, "the construction site"), (-30, 224, "the helicopter"),
                       (-50, -244, "the basketball court"), (-200, -244, "the bus depot")):
        b.landmark(float(x), float(z), name)


# ================================================================= roads
def _roads(b: Area, s: Surfaces) -> None:
    H = HALF
    s.lay(rect(-H, H, ROAD_A[0], ROAD_A[1]), 0.3, ASPHALT)
    s.lay(rect(-H, H, ROAD_A[1], ROAD_A[1] + 6.0), 0.6, PAVEMENT)
    s.lay(rect(-H, H, ROAD_A[0] - 6.0, ROAD_A[0]), 0.6, PAVEMENT)
    s.lay(rect(ROAD_C[0], ROAD_C[1], ROAD_A[1] + 6.0, H), 0.3, ASPHALT)
    s.lay(rect(ROAD_B[0], ROAD_B[1], ROAD_A[1] + 6.0, H), 0.3, ASPHALT)
    for x0, x1 in ((ROAD_C[0] - 6.0, ROAD_C[0]), (ROAD_C[1], ROAD_C[1] + 6.0),
                   (ROAD_B[0] - 6.0, ROAD_B[0]), (ROAD_B[1], ROAD_B[1] + 6.0)):
        s.lay(rect(x0, x1, ROAD_A[1] + 6.0, H), 0.6, PAVEMENT_DARK)
    # the front lot between the checkpoint and the hospital doors
    s.lay(rect(ROAD_C[1] + 6.0, ROAD_B[0] - 6.0, -56.0, 36.0), 0.3, ASPHALT)
    for i in range(14):
        x = -100.0 + i * 13.0
        if -26.0 < x < 26.0:
            continue
        for z0 in (-46.0, 20.0):
            b.box([x, 0.34, z0 + 6.0], [0.5, 0.08, 12.0], LINE_WHITE, collide=False)
    for a, c in ((-H + 4.0, ROAD_C[0] - 8.0), (ROAD_C[1] + 8.0, ROAD_B[0] - 8.0),
                 (ROAD_B[1] + 8.0, H - 4.0)):
        for dz in (-0.7, 0.7):
            b.box([(a + c) / 2.0, 0.34, (ROAD_A[0] + ROAD_A[1]) / 2.0 + dz],
                  [c - a, 0.08, 0.5], LINE_YELLOW, collide=False)
    for i in range(9):
        x = -240.0 + i * 60.0
        if abs(x - (ROAD_C[0] + ROAD_C[1]) / 2.0) < 14 or \
                abs(x - (ROAD_B[0] + ROAD_B[1]) / 2.0) < 14:
            x += 20.0
        lamp_post(b, x, ROAD_A[1] + 3.0, 16.0, arm="z-", y=0.6)
    for i in range(7):
        z = -150.0 + i * 64.0
        lamp_post(b, ROAD_C[1] + 3.0, z, 16.0, arm="x-", y=0.6)
        lamp_post(b, ROAD_B[0] - 3.0, z + 32.0, 16.0, arm="x+", y=0.6)


# ============================================================== hospital
def _hospital(b: Area, s: Surfaces) -> None:
    x0, x1, z0, z1 = HOSP
    s.reserve(rect(x0, x1, z0, z1))
    stair = rect(10.0, 38.0, 90.0, 98.0)
    roof = 18.0 + 1.2
    building(b, HOSP, 0.0, 18.0, WHITE, roof_colour="#7a8088",
             floor_colour="#c8d2d2",
             doors={"z-": [(-20.0, 20.0, 12.0)], "x+": [(70.0, 90.0, 12.0)],
                    "x-": [(116.0, 128.0, 11.0)],
                    "z+": [(-96.0, -84.0, 12.0), (40.0, 52.0, 11.0)]},
             windows={"z-": [(-100.0, -80.0, 4.0, 12.0), (-70.0, -50.0, 4.0, 12.0),
                             (-38.0, -26.0, 4.0, 12.0), (26.0, 38.0, 4.0, 12.0),
                             (50.0, 70.0, 4.0, 12.0), (76.0, 86.0, 4.0, 12.0)],
                      "x+": [(110.0, 130.0, 4.0, 12.0), (146.0, 162.0, 4.0, 12.0)],
                      "x-": [(52.0, 70.0, 4.0, 12.0), (140.0, 160.0, 4.0, 12.0)],
                      "z+": [(-70.0, -64.0, 4.0, 12.0), (0.0, 20.0, 4.0, 12.0),
                             (60.0, 80.0, 4.0, 12.0)]},
             glass=True, roof_holes=[stair], parapet=3.0,
             parapet_gaps={"x-": [(96.0, 110.0)], "z+": [(-62.0, -54.0)]},
             lights=COLD,
             no_lights=[rect(x0, x1, 97.0, 103.0), rect(-43.0, -37.0, z0, 100.0),
                        rect(37.0, 43.0, z0, 100.0), rect(-13.0, -7.0, 100.0, z1)])
    for side, span in (("z-", (-20.0, 20.0)), ("x+", (70.0, 90.0)),
                       ("x-", (116.0, 128.0)), ("z+", (-96.0, -84.0)),
                       ("z+", (40.0, 52.0))):
        threshold(b, HOSP, side, span)
    # partitions: front rooms from back rooms, wards from the lobby from ER
    holed_wall(b, "x", 100.0, 1.6, x0 + 2.0, x1 - 2.0, FLOOR, 18.0, "#c8ced2",
               [(-92.0, -80.0, 0.0, 11.0), (-16.0, 16.0, 0.0, 12.0),
                (56.0, 70.0, 0.0, 11.0)])
    holed_wall(b, "z", -40.0, 1.6, z0 + 2.0, 99.2, FLOOR, 18.0, "#c8ced2",
               [(58.0, 74.0, 0.0, 11.0)])
    holed_wall(b, "z", 40.0, 1.6, z0 + 2.0, 99.2, FLOOR, 18.0, "#c8ced2",
               [(56.0, 72.0, 0.0, 11.0)])
    holed_wall(b, "z", -10.0, 1.6, 100.8, z1 - 2.0, FLOOR, 18.0, "#c8ced2",
               [(120.0, 132.0, 0.0, 11.0), (150.0, 160.0, 0.0, 11.0)])
    # the west ward: beds along both walls, curtains between them
    for i in range(4):
        z = 50.0 + i * 12.0
        for x in (-102.0, -48.0):
            b.box([x, FLOOR + 1.3, z], [9.0, 2.6, 4.6], "#e8ecee", studs=True)
            b.box([x + (4.8 if x < -60 else -4.8), FLOOR + 2.6, z], [0.6, 5.2, 4.6],
                  "#8a9aa8")
        b.box([-75.0, FLOOR + 4.0, z + 6.0], [12.0, 8.0, 0.4], "#a8d0c8",
              alpha=0.6)
    supply_med(b, -74.0, FLOOR, 96.3, "z-")
    # the lobby: the desk, the waiting chairs, the stair to the roof
    b.box([0.0, FLOOR + 2.0, 72.0], [26.0, 4.0, 4.0], "#8a6a4a", studs=True)
    b.box([0.0, FLOOR + 4.3, 72.0], [27.0, 0.6, 5.0], "#d8d0c0")
    for row in range(3):
        for k in (-1, 1):
            b.box([k * 22.0, FLOOR + 1.2, 50.0 + row * 7.0], [14.0, 2.4, 2.6],
                  SCRUB)
    for x in (-34.0, 34.0):
        b.cyl([x, FLOOR + 2.0, 47.0], [5.0, 4.0, 5.0], "#8a6a4a")
        b.sphere([x, FLOOR + 6.0, 47.0], [5.6, 5.0, 5.6], "#3f7a4a", collide=False)
    flight(b, "x", stair[0], stair[1], stair[2], stair[3], FLOOR, roof,
           CONCRETE_DARK, fill=FLOOR, rise=1.95)
    for z in (stair[2] - 0.5, stair[3] + 0.5):
        b.box([(stair[0] + stair[1]) / 2.0, roof + 1.5, z],
              [stair[1] - stair[0], 3.0, 1.0], STEEL, material="metal")
    b.box([stair[0] - 0.5, roof + 1.5, (stair[2] + stair[3]) / 2.0],
          [1.0, 3.0, stair[3] - stair[2] + 2.0], STEEL, material="metal")
    # emergency: trauma bays, a crash cart, the ammunition the guards left
    for i in range(3):
        z = 50.0 + i * 15.0
        b.box([80.0, FLOOR + 1.3, z], [9.0, 2.6, 4.6], "#e8ecee", studs=True)
        b.box([80.0, FLOOR + 4.0, z + 5.2], [12.0, 8.0, 0.4], "#c8a8a8", alpha=0.6)
    b.box([56.0, FLOOR + 2.0, 90.0], [4.0, 4.0, 6.0], "#c42b20", material="metal")
    supply_ammo(b, 50.0, FLOOR, 46.0, "z+")
    # surgery, back left: two tables under their lamps
    for x in (-80.0, -40.0):
        b.box([x, FLOOR + 2.0, 134.0], [6.0, 4.0, 12.0], "#c8d0d8", studs=True)
        b.cyl([x, 17.4, 134.0], [6.0, 1.2, 6.0], "#8a9098", material="metal")
        b.cyl([x, 16.65, 134.0], [4.4, 0.3, 4.4], "#f2fbff", material="neon",
              collide=False)
    supply_med(b, -106.0, FLOOR, 150.0, "x+")
    for z in (110.0, 160.0):
        b.box([-60.0, FLOOR + 3.0, z], [30.0, 6.0, 3.0], "#9aa8b0")
    # records and the morgue, back right: shelving to fight through
    for i in range(4):
        b.box([10.0 + i * 16.0, FLOOR + 4.0, 128.0], [3.0, 8.0, 26.0], WOOD_DARK)
    b.box([40.0, FLOOR + 5.0, 165.8], [44.0, 10.0, 2.4], STEEL, material="metal")
    supply_ammo(b, 80.0, FLOOR, 160.0, "x-")
    barrel_spot(b, 70.0, FLOOR, 108.0)
    # outside: the drop-off canopy, the sign, the emergency sign
    for x in (-28.0, 28.0):
        b.box([x, 0.3 + 6.5, 22.0], [2.0, 13.0, 2.0], "#c8ced2")
    slab(b, rect(-30.0, 30.0, 20.0, 40.0), 14.0, 1.2, "#8a9098")
    for z in (19.85,):
        b.box([0.0, 13.4, z], [60.0, 1.0, 0.3], "#7fd8ff", material="neon",
              collide=False)
    wall_sign(b, 0.0, 16.0, z0 - 0.35, 50.0, 2.6,
              sign_decal("ST. AGNES MEDICAL CENTER", WHITE, "#1f4a7a", 50 / 2.6),
              "z-", WHITE)
    wall_sign(b, x1 + 0.35, 14.6, 80.0, 22.0, 2.8,
              sign_decal("EMERGENCY", "#c42b20", "#ffffff", 22 / 2.8), "x+",
              "#c42b20")
    # the roof: the helipad, the plant, the water tank, the fire stair
    pad = rect(-30.0, 30.0, 112.0, 160.0)
    slab(b, pad, roof + 0.12, 0.12, "#3a3f46", collide=False)
    b.cyl([0.0, roof + 0.2, 136.0], [40.0, 0.12, 40.0], "#d8b23a", collide=False)
    b.cyl([0.0, roof + 0.24, 136.0], [36.0, 0.12, 36.0], "#3a3f46", collide=False)
    for x in (-8.0, 8.0):
        b.box([x, roof + 0.32, 136.0], [3.0, 0.12, 22.0], "#f2f2f2", collide=False)
    b.box([0.0, roof + 0.34, 136.0], [13.0, 0.12, 3.0], "#f2f2f2", collide=False)
    for x, z in ((-80.0, 60.0), (-80.0, 80.0), (60.0, 60.0), (60.0, 150.0)):
        b.box([x, roof + 3.0, z], [12.0, 6.0, 10.0], "#8a9098", material="metal")
        b.cyl([x, roof + 6.4, z], [5.0, 0.8, 5.0], STEEL_DARK, material="metal")
    b.cyl([-80.0, roof + 9.0, 150.0], [14.0, 18.0, 14.0], "#6a7480",
          material="metal")
    supply_ammo(b, -60.0, roof, 120.0, "x+")
    flood(b, 80.0, 48.0, roof, 10.0, COLD)
    flood(b, -100.0, 160.0, roof, 10.0, COLD)
    flight(b, "x", -20.0, -60.0, z1, z1 + 10.0, 0.0, roof, CONCRETE_DARK,
           fill=0.0, rise=1.95)
    s.reserve(rect(-60.0, -20.0, z1, z1 + 10.0))


# ================================================================ garage
def _garage(b: Area, s: Surfaces, rng: random.Random) -> None:
    gx0, gx1, gz0, gz1 = GARAGE
    s.lay(rect(gx0, gx1, gz0, gz1), 0.3, "#4a4f55")
    east_ramp = rect(-168.0, -152.0, 20.0, 60.0)
    west_ramp = rect(-260.0, -244.0, 20.0, 60.0)
    holes = {1: [east_ramp], 2: [west_ramp], 3: [east_ramp]}
    gaps = {2: {"x+": [(96.0, 110.0)]}}
    for level in (1, 2, 3):
        top = level * DECK
        from .kit import carve, plate
        plate(b, carve(rect(gx0, gx1, gz0, gz1), holes[level]), top, 1.2,
              CONCRETE if level < 3 else CONCRETE_LIGHT, studs=True)
        room_walls(b, rect(gx0, gx1, gz0, gz1), 1.2, top, top + 3.2, CONCRETE_DARK,
                   doors={side: [(a, c, top + 3.2) for a, c in spans]
                          for side, spans in gaps.get(level, {}).items()})
        for hole in holes[level]:
            hx0, hx1, hz0, hz1 = hole
            # a rail along the open side of the ramp well
            b.box([(hx0 + hx1) / 2.0, top + 1.5, hz0 - 0.5], [hx1 - hx0, 3.0, 1.0],
                  STEEL, material="metal")
            if hx0 > gx0 + 4.0:
                b.box([hx0 - 0.5, top + 1.5, (hz0 + hz1) / 2.0],
                      [1.0, 3.0, hz1 - hz0 + 2.0], STEEL, material="metal")
            else:
                b.box([hx1 + 0.5, top + 1.5, (hz0 + hz1) / 2.0],
                      [1.0, 3.0, hz1 - hz0 + 2.0], STEEL, material="metal")
        # ceiling lights under every deck
        for z in (-28.0, 4.0, 76.0, 108.0):
            strip_light(b, -206.0, z, top - 1.2, 80.0, "x", LAMP)
    # the ramps, switching back up the building
    flight(b, "z", 20.0, 60.0, east_ramp[0], east_ramp[1], 0.3, DECK, CONCRETE_DARK,
           fill=0.3, rise=1.95)
    flight(b, "z", 60.0, 20.0, west_ramp[0], west_ramp[1], DECK, 2 * DECK,
           CONCRETE_DARK, fill=DECK, rise=1.95)
    flight(b, "z", 20.0, 60.0, east_ramp[0], east_ramp[1], 2 * DECK, 3 * DECK,
           CONCRETE_DARK, fill=2 * DECK, rise=1.95)
    # columns between the decks
    for level in range(3):
        base = 0.3 if level == 0 else level * DECK
        top = (level + 1) * DECK - 1.2
        for x in (-250.0, -220.0, -190.0, -176.0):
            for z in (-28.0, 4.0, 36.0, 72.0, 104.0):
                if x == -250.0 and 16.0 < z < 64.0:
                    continue
                b.box([x, (base + top) / 2.0, z], [2.4, top - base, 2.4],
                      CONCRETE_LIGHT)
    # cars left where they were parked, on every level
    colours = ["#6a7a8a", "#8a3a2a", "#2a2a2a", "#d8d0b8", "#3a5a3a", "#5a4a7a"]
    for level in range(4):
        y = 0.3 if level == 0 else level * DECK
        for k, (x, z) in enumerate(((-236.0, -16.0), (-205.0, 88.0),
                                    (-180.0, -12.0), (-236.0, 96.0))):
            if (level + k) % 3 == 0:
                continue
            car(b, x, z, "z", colours[(level * 3 + k) % len(colours)], y=y,
                wrecked=(level + k) % 5 == 0)
    for level, (x, z) in ((1, (-200.0, 112.0)), (2, (-240.0, -30.0)),
                          (3, (-176.0, 116.0))):
        barrel_spot(b, x, level * DECK, z)
    supply_ammo(b, -230.0, 3 * DECK, 110.0, "z-")
    flood(b, -258.0, -36.0, 3 * DECK + 3.2, 6.0)
    wall_sign(b, gx1 + 0.35, 6.0, -20.0, 18.0, 3.6,
              sign_decal("PARKING", "#1f4a7a", "#ffffff", 5.0), "x+", "#1f4a7a")
    wall_sign(b, gx1 + 0.35, 2 * DECK + 6.0, 0.0, 14.0, 3.0,
              sign_decal("LEVEL 2", "#d8b23a", "#1b1b1b", 14 / 3.0), "x+",
              "#d8b23a")


def _skybridge(b: Area) -> None:
    """Garage deck two to the hospital roof, high over Garage Street."""
    x0, x1, z0, z1 = GARAGE[1], HOSP[0], 96.0, 110.0
    slab(b, rect(x0, x1, z0, z1), 2 * DECK, 1.2, CONCRETE_LIGHT, studs=True)
    for z in (z0 + 0.5, z1 - 0.5):
        b.box([(x0 + x1) / 2.0, 2 * DECK + 3.4, z], [x1 - x0, 6.8, 1.0], GLASS,
              material="glass", alpha=0.45)
    slab(b, rect(x0, x1, z0, z1), 2 * DECK + 7.4, 0.6, CONCRETE)
    strip_light(b, (x0 + x1) / 2.0, (z0 + z1) / 2.0, 2 * DECK + 6.8, 30.0, "x",
                COLD)
    for x in (-145.0, -115.0):
        b.box([x, (2 * DECK - 1.2) / 2.0, (z0 + z1) / 2.0], [3.0, 2 * DECK - 1.2, 4.0],
              CONCRETE_DARK)


# ================================================================ ER bay
def _er_bay(b: Area, s: Surfaces) -> None:
    s.lay(rect(HOSP[1], ROAD_B[0] - 6.0, 40.0, 140.0), 0.3, "#4a4f55")
    slab(b, rect(HOSP[1], 140.0, 56.0, 104.0), 15.2, 1.2, "#8a9098")
    for z in (58.0, 102.0):
        b.box([138.5, 0.3 + 7.15, z], [2.0, 14.3, 2.0], "#c8ced2")
    b.box([140.15, 14.6, 80.0], [0.3, 1.0, 48.0], "#ff4a3a", material="neon",
          collide=False)
    for z, front in ((66.0, 1), (94.0, 1)):
        van(b, 114.0, z, "x", "#f2f2f2", "#c42b20", 18.0, "#ff3a2a",
            "AMBULANCE", y=0.3, front=front)
    b.set_lure(126.0, 0.3, 80.0, "the ambulance siren", "Sound the siren",
               "siren", (122.0, 0.3, 80.0))
    for x in (150.0, 160.0):
        b.box([x, 0.3 + 3.0, 128.0], [4.0, 6.0, 6.0], "#c8d0d8")
    barrel_spot(b, 160.0, 0.3, 48.0)


# ================================================================== camp
def _camp(b: Area, s: Surfaces, rng: random.Random) -> None:
    cx0, cx1, cz0, cz1 = CAMP
    s.lay(rect(cx0, cx1, cz0, cz1), 0.2, "#7a7058")
    # the fence, gates on three sides
    chain_fence(b, cx0, cz1, -14.0, cz1, 10.0)
    chain_fence(b, 14.0, cz1, cx1, cz1, 10.0)
    chain_fence(b, cx0, cz0, cx1, cz0, 10.0)
    for x in (cx0, cx1):
        chain_fence(b, x, cz0, x, -130.0, 10.0)
        chain_fence(b, x, -114.0, x, cz1, 10.0)
    wall_sign(b, -22.0, 7.0, cz1 + 0.6, 14.0, 4.0,
              sign_decal("QUARANTINE ZONE", "#f2d23a", "#1b1b1b", 3.5), "z+",
              "#f2d23a")
    b.box([-22.0, 2.5, cz1 + 0.6], [0.8, 5.0, 0.4], STEEL_DARK)
    # chicanes of sandbags just inside the gates
    sandbags(b, -20.0, cz1 - 10.0, 14.0, "x", 4.0)
    sandbags(b, 20.0, cz1 - 10.0, 14.0, "x", 4.0)
    for x, d in ((cx0 + 10.0, 1), (cx1 - 10.0, -1)):
        sandbags(b, x, -112.0, 12.0, "z", 4.0)
    hesco(b, -60.0, -72.0, 5, "x")
    hesco(b, 56.0, -72.0, 5, "x")
    # the command tent: the deploy pads are inside it
    area = rect(-30.0, 30.0, -142.0, -100.0)
    tent(b, area, 11.0, "#5a6a48", doors={"z+": [(-8.0, 8.0, 9.0)],
                                           "z-": [(-6.0, 6.0, 9.0)]})
    b.box([0.0, FLOOR + 1.8, -121.0], [8.0, 3.6, 14.0], WOOD, studs=True)
    for x in (-22.0, -11.0, 11.0, 22.0):
        for z in (-134.0, -126.0, -116.0, -108.0):
            deploy_pad(b, x, z, FLOOR, "#7aa84a", 5.0)
            b.safe_spawn(x, FLOOR + 0.6, z, 0.0)
    supply_ammo(b, -25.0, FLOOR, -138.6, "z+")
    supply_med(b, 25.0, FLOOR, -139.8, "z+")
    wall_sign(b, 0.0, 9.6, -100.0 + 0.35, 14.0, 2.4,
              sign_decal("COMMAND", "#3a4a2a", "#e8e2c8", 14 / 2.4), "z+",
              "#3a4a2a")
    # medical tents either side
    tent(b, rect(-92.0, -50.0, -174.0, -146.0), 9.0, "#d8d8d0",
         doors={"z+": [(-76.0, -66.0, 7.6)]}, lights=COLD)
    tent(b, rect(46.0, 86.0, -174.0, -146.0), 9.0, "#d8d8d0",
         doors={"z+": [(60.0, 70.0, 7.6)]}, lights=COLD)
    for x in (-84.0, -58.0):
        b.box([x, FLOOR + 1.3, -164.0], [5.0, 2.6, 10.0], "#e8ecee", studs=True)
    for x in (54.0, 78.0):
        b.box([x, FLOOR + 1.3, -164.0], [5.0, 2.6, 10.0], "#e8ecee", studs=True)
    supply_med(b, -71.0, FLOOR, -171.4, "z+")
    # watchtowers on the two front corners
    watchtower(b, -86.0, -78.0, 16.0, "#6a5a3a", "x+")
    watchtower(b, 76.0, -78.0, 16.0, "#6a5a3a", "x-")
    # trucks, the generator, crates
    army_truck(b, -62.0, -98.0, "x")
    army_truck(b, 62.0, -112.0, "z", front=1)
    b.box([40.0, 3.0, -160.0 + 40.0], [8.0, 6.0, 6.0], "#4a5a3a", material="metal")
    for i in range(3):
        crate(b, -44.0 + i * 5.5, 0.2, -126.0, 5.0, "#5a6a3a")
    crate(b, -41.0, 5.2, -126.0, 4.0, "#5a6a3a")
    supply_ammo(b, 40.0, 0.2, -92.0, "z-")
    for x, z in ((cx0 + 4.0, cz0 + 4.0), (cx1 - 4.0, cz0 + 4.0)):
        flood(b, x, z, 0.2, 20.0)
    barrel_spot(b, -40.0, 0.3, -30.0)
    barrel_spot(b, 50.0, 0.3, 10.0)
    # the lot: abandoned cars and a bus on its side of the road
    for x, z, c in ((-80.0, -30.0, "#6a7a8a"), (60.0, -40.0, "#2a2a2a"),
                    (-40.0, 26.0, "#8a3a2a"), (80.0, 26.0, "#d8d0b8")):
        car(b, x, z, "z", c, y=0.3, wrecked=c == "#2a2a2a")
    bus(b, 120.0, -16.0, "x", "#2f5f8a", 32.0, "ST AGNES SHUTTLE")
    barrier(b, -50.0, -2.0, 16.0, "x")
    barrier(b, 40.0, -8.0, 16.0, "x")
    # more of what was parked here when it all went wrong
    colours = ["#5a6a7a", "#7a3a2a", "#c8c0a8", "#3a4a5a", "#6a5a3a", "#2a3a2a"]
    for i, x in enumerate((-100.0, -87.0, -61.0, 34.0, 74.0, 100.0)):
        car(b, x, -40.0, "z", colours[i], y=0.3, wrecked=i == 4)
    for i, x in enumerate((-113.0, -100.0, -74.0, 61.0, 74.0, 113.0, 139.0)):
        car(b, x, 26.0, "z", colours[(i + 2) % len(colours)], y=0.3)
    # the police got here first: two cruisers nose to nose across the doors
    for x, f in ((-12.0, 1), (12.0, -1)):
        car(b, x, 12.0, "x", "#1d1f22", 12.0, y=0.3)
        b.box([x - 0.6, 5.35, 12.0], [3.0, 0.4, 2.6], "#3a6aff" if f > 0 else "#ff3a2a",
              material="neon")
    for x in (-30.0, -22.0, 22.0, 30.0):
        b.box([x, 2.0, 2.0], [6.0, 0.8, 0.6], "#e8e8e8")
        for dx in (-2.4, 2.4):
            b.box([x + dx, 0.3 + 0.85, 2.0], [0.6, 1.7, 1.6], "#e8e8e8")
    # the triage canopy the army put up in the lot
    for x in (-84.0, -56.0):
        for z in (-16.0, 8.0):
            b.box([x, 0.3 + 5.0, z], [1.0, 10.0, 1.0], STEEL)
    slab(b, rect(-86.0, -54.0, -18.0, 10.0), 10.9, 0.6, "#d8d8d0")
    for z in (-10.0, 0.0):
        b.box([-70.0, 0.3 + 1.3, z], [10.0, 2.6, 4.0], "#e8ecee", studs=True)
    for x, z in ((-120.0, -60.0), (-120.0, 0.0), (160.0, -60.0), (160.0, 0.0)):
        lamp_post(b, x, z, 16.0, y=0.3)


# ================================================================== maze
def _maze(b: Area, s: Surfaces, rng: random.Random) -> None:
    """The memorial garden: a hedge maze three rings deep."""
    cx, cz = -206.0, -117.0
    s.lay(rect(-262.0, -150.0, -182.0, -52.0), 0.15, "#4a6a3a", studs=True,
          material="grass")
    hedge = "#2a4a2a"
    rings = ((52.0, {"x+": [(cz - 6.0, cz + 6.0, 8.0)], "z-": [(cx - 6.0, cx + 6.0, 8.0)]}),
             (36.0, {"z+": [(cx - 6.0, cx + 6.0, 8.0)], "x-": [(cz - 6.0, cz + 6.0, 8.0)]}),
             (20.0, {"x+": [(cz - 5.0, cz + 5.0, 8.0)], "z-": [(cx - 5.0, cx + 5.0, 8.0)]}))
    for r, gaps in rings:
        room_walls(b, rect(cx - r, cx + r, cz - r, cz + r), 3.0, 0.15, 7.15, hedge,
                   doors=gaps, material="grass")
    # dead ends between the rings
    for dx, dz, along, length in ((-44.0, -20.0, "z", 14.0), (44.0, 20.0, "z", 14.0),
                                  (20.0, -44.0, "x", 14.0), (-20.0, 44.0, "x", 14.0)):
        w, d = (3.0, length) if along == "z" else (length, 3.0)
        b.box([cx + dx, 3.65, cz + dz], [w, 7.0, d], hedge, material="grass")
    # the centre: the saint, benches, lamps
    b.box([cx, 2.15, cz], [8.0, 4.0, 8.0], "#a8a49a", studs=True)
    b.box([cx, 6.6, cz], [2.4, 5.0, 1.6], "#c8c4b8")
    b.box([cx, 9.9, cz], [1.6, 1.6, 1.6], "#c8c4b8")
    for dz in (-11.0, 11.0):
        bench(b, cx, cz + dz, "x", y=0.15)
    lamp_post(b, cx - 11.0, cz, 10.0, y=0.15)
    supply_med(b, cx + 11.0, 0.15, cz, "x-")
    for x, z in ((-256.0, -60.0), (-156.0, -176.0)):
        b.tree(x, z, 0.15, 1.2, WOOD, "#2f5a2f")


# ============================================================= east side
def _east_side(b: Area, s: Surfaces, rng: random.Random) -> None:
    ex0 = ROAD_B[1] + 6.0
    # the clinic
    area = (204.0, 262.0, 50.0, 120.0)
    s.reserve(rect(*area))
    building(b, area, 0.0, 13.0, "#c8d8d0", roof_colour="#5a6a6a",
             floor_colour="#d8e0dc", doors={"x-": [(76.0, 90.0, 10.0)],
                                             "z+": [(226.0, 236.0, 10.0)]},
             windows={"x-": [(56.0, 70.0, 3.6, 8.6), (98.0, 112.0, 3.6, 8.6)]},
             glass=True, lights=COLD)
    threshold(b, area, "x-", (76.0, 90.0))
    threshold(b, area, "z+", (226.0, 236.0))
    wall_sign(b, 203.65, 10.6, 83.0, 22.0, 2.6,
              sign_decal("HARROW FAMILY CLINIC", "#ffffff", "#2f7a5a", 22 / 2.6),
              "x-", "#ffffff")
    for z in (60.0, 104.0):
        b.box([232.0, FLOOR + 3.0, z], [30.0, 6.0, 3.0], "#d8e0dc")
    supply_med(b, 258.0, FLOOR, 84.0, "x-")
    # the apartments: a lobby you can get into under a block you cannot
    area = (204.0, 266.0, 150.0, 250.0)
    s.reserve(rect(*area))
    building(b, area, 0.0, 12.0, "#8a7a6a", roof_colour="#5a4f46",
             floor_colour="#9a8a7a", doors={"x-": [(190.0, 210.0, 10.0)]},
             windows={"x-": [(160.0, 180.0, 3.6, 8.6), (220.0, 240.0, 3.6, 8.6)]},
             boards=True, lights=WARM)
    threshold(b, area, "x-", (190.0, 210.0))
    b.box([235.0, 13.2 + 14.0, 200.0], [58.0, 28.0, 96.0], "#7a6a5a")
    for k in range(3):
        for i in range(6):
            if rng.random() < 0.55:
                b.box([205.94, 18.0 + k * 9.0, 158.0 + i * 16.0], [0.12, 3.0, 4.0],
                      rng.choice(["#ffd27a", "#ffb35a", "#cfe8ff"]), material="neon",
                      collide=False)
            else:
                b.box([205.94, 18.0 + k * 9.0, 158.0 + i * 16.0], [0.12, 3.0, 4.0],
                      "#20262f", collide=False)
    for z in (160.0, 238.0):
        b.box([220.0, FLOOR + 2.0, z], [10.0, 4.0, 4.0], "#6b3a3a", studs=True)
    # the strip mall, facing the road across its own little car park
    s.lay(rect(ex0, 214.0, -178.0, -60.0), 0.3, "#4a4f55")
    shops = (("LAUNDROMAT", "#3a7aa8", -178.0, -142.0),
             ("TONY'S PIZZA", "#c43a2a", -138.0, -102.0),
             ("PAWN & GUN", "#3a3a3a", -98.0, -62.0))
    for name, colour, z0, z1 in shops:
        area = (214.0, 262.0, z0, z1)
        s.reserve(rect(*area))
        mid = (z0 + z1) / 2.0
        building(b, area, 0.0, 12.0, "#c8b89a", roof_colour="#5a4f46",
                 floor_colour="#b8b0a0", doors={"x-": [(mid - 5.0, mid + 5.0, 10.0)]},
                 windows={"x-": [(z0 + 3.0, mid - 7.0, 3.4, 8.4),
                                 (mid + 7.0, z1 - 3.0, 3.4, 8.4)]},
                 glass=True, lights=WARM)
        threshold(b, area, "x-", (mid - 5.0, mid + 5.0))
        wall_sign(b, 213.65, 10.4, mid, 26.0, 2.6,
                  sign_decal(name, colour, "#ffffff", 10.0), "x-", colour)
    for z in (-170.0, -150.0):
        b.box([250.0, FLOOR + 2.6, z], [8.0, 5.2, 5.0], "#e8ecee", studs=True)
    b.box([248.0, FLOOR + 2.0, -120.0], [3.0, 4.0, 24.0], "#8a6a4a", studs=True)
    b.box([240.0, FLOOR + 2.0, -80.0], [3.0, 4.0, 20.0], WOOD_DARK, studs=True)
    supply_ammo(b, 256.0, FLOOR, -72.0, "x-")
    for z in (-120.0, -84.0):
        car(b, ex0 + 8.0, z, "x", rng.choice(["#6a7a8a", "#8a6a3a"]), y=0.3)
    barrel_spot(b, 208.0, 0.3, -100.0)
    barrel_spot(b, 208.0, 0.3, -62.0)
    # the bus stop on Harbor Road
    slab(b, rect(198.5, 204.0, 0.0, 14.0), 9.6, 0.4, "#5a6a7a")
    b.box([203.6, 0.6 + 4.3, 7.0], [0.8, 8.6, 14.0], GLASS, material="glass",
          alpha=0.4)
    bench(b, 201.2, 7.0, "z", y=0.6)
    van(b, 184.0, 40.0, "z", "#c8a83a", "", 16.0, label="", y=0.3, front=-1)
    car(b, 184.0, -40.0, "z", "#2a2a2a", wrecked=True, y=0.3)
    barrier(b, 184.0, 150.0, 14.0, "x")


# ================================================================= south
def _south(b: Area, s: Surfaces, rng: random.Random) -> None:
    south = ROAD_A[0] - 6.0          # the far pavement's outer edge
    # the transit depot
    s.lay(rect(-262.0, -130.0, -270.0, south), 0.3, "#4a4f55")
    bus(b, -230.0, -236.0, "x", "#c8c4b8", 34.0, "METRO 12")
    bus(b, -180.0, -252.0, "x", "#2f6b8a", 34.0, "METRO 4")
    area = (-160.0, -134.0, -268.0, -236.0)
    building(b, area, 0.3, 10.0, "#8a8478", roof_colour="#4a4a52",
             floor_colour="#8a8478", doors={"x-": [(-256.0, -248.0, 8.0)]},
             windows={"z+": [(-156.0, -138.0, 3.6, 7.6)]}, boards=True, lights=WARM)
    threshold(b, area, "x-", (-256.0, -248.0), y0=0.3)
    supply_ammo(b, -147.0, 0.7, -262.0, "z+")
    barrel_spot(b, -250.0, 0.3, -262.0)
    # the basketball court
    court = rect(-104.0, 0.0, -262.0, -224.0)
    s.lay(court, 0.25, "#a85a3a")
    b.box([-52.0, 0.29, -243.0], [0.4, 0.08, 38.0], "#f2f2f2", collide=False)
    for x, face in ((-100.0, 1), (-4.0, -1)):
        b.box([x, 5.0, -243.0], [1.0, 10.0, 1.0], STEEL_DARK)
        b.box([x + face * 1.0, 10.8, -243.0], [1.0, 3.6, 6.0], "#f2f2f2")
        b.cyl([x + face * 2.6, 9.4, -243.0], [2.2, 0.3, 2.2], "#e84a1a",
              collide=False)
    chain_fence(b, -108.0, -220.0, -64.0, -220.0, 10.0)
    chain_fence(b, -40.0, -220.0, 4.0, -220.0, 10.0)
    for i in range(3):
        slab(b, rect(-90.0, -14.0, -270.0 + i * 2.0, -264.0), 0.25 + 1.6 * (i + 1),
             1.6 if i else 1.6 + 0.25, "#8a8a8a")
    # the construction site
    site = rect(40.0, 268.0, -270.0, -218.0)
    s.lay(site, 0.2, "#7a6a52")
    chain_fence(b, 40.0, -216.0, 120.0, -216.0, 10.0)
    chain_fence(b, 144.0, -216.0, 266.0, -216.0, 10.0)
    # the scaffold: three decks stepping up towards the crane, each reached
    # by a stair standing on the deck below
    for i, top in enumerate((7.0, 14.0, 21.0)):
        x0 = 150.0 + i * 30.0
        slab(b, rect(x0, x0 + 30.0, -262.0, -242.0), top, 0.8, WOOD_LIGHT,
             studs=True)
        for x in (x0 + 0.6, x0 + 29.4):
            for z in (-261.4, -242.6):
                b.box([x, (0.2 + top - 0.8) / 2.0, z], [1.2, top - 1.0, 1.2],
                      "#d8a83a")
        b.box([x0 + 15.0, top + 1.6, -242.5], [30.0, 3.2, 1.0], "#d8a83a")
    flight(b, "x", 126.0, 150.0, -250.0, -244.0, 0.2, 7.0, "#d8a83a", fill=0.2)
    flight(b, "x", 164.0, 180.0, -262.0, -256.0, 7.0, 14.0, "#d8a83a", fill=7.0)
    flight(b, "x", 194.0, 210.0, -262.0, -256.0, 14.0, 21.0, "#d8a83a", fill=14.0)
    for i, (x, z) in enumerate(((80.0, -240.0), (110.0, -255.0))):
        for k in range(3):
            b.box([x, 1.2 + k * 2.0, z], [16.0 - k * 4.0, 2.0, 12.0 - k * 3.0],
                  "#6b5a42", studs=True)
    for k in range(4):
        b.cyl([220.0 + k * 3.2, 1.8, -230.0], [3.2, 12.0, 3.2], "#8a8478",
              r=[math.pi / 2.0, 0, 0], collide=False)
    b.box([226.0, 1.8, -230.0], [16.0, 3.6, 12.0], "#8a8478", alpha=0.0, collide=True)
    # the excavator and the crane
    b.box([60.0, 3.0, -232.0], [14.0, 5.0, 9.0], "#d8a83a", material="metal")
    b.box([58.0, 7.5, -232.0], [7.0, 4.0, 7.0], "#d8a83a", material="metal")
    b.box([67.0, 9.0, -232.0], [12.0, 1.4, 1.4], "#c89a2a", material="metal")
    b.box([248.0, 40.0, -258.0], [4.0, 80.0, 4.0], "#d8a83a", material="metal")
    b.box([228.0, 80.6, -258.0], [60.0, 1.6, 2.4], "#d8a83a", material="metal",
          collide=False)
    supply_ammo(b, 140.0, 0.2, -228.0, "z+")
    for x, z in ((200.0, -226.0), (90.0, -262.0), (150.0, -232.0)):
        barrel_spot(b, x, 0.2, z)


# ================================================================= north
def _north(b: Area, s: Surfaces, rng: random.Random) -> None:
    # the service yard behind the hospital
    s.lay(rect(HOSP[0], ROAD_B[0] - 6.0, 182.0, 262.0), 0.25, "#55595e")
    # the helicopter: down on its side, rotor torn off and lying beside it
    hx, hz = -30.0, 224.0
    b.box([hx, 4.75, hz], [30.0, 9.0, 10.0], "#3a4a3a", material="metal")
    b.box([hx + 10.0, 5.0, hz], [8.0, 6.0, 10.4], "#24323c", material="metal")
    b.box([hx - 26.0, 4.0, hz], [22.0, 3.0, 3.0], "#3a4a3a", material="metal")
    b.box([hx - 36.0, 9.5, hz], [3.0, 8.0, 1.0], "#3a4a3a", material="metal")
    b.box([hx, 0.85, hz + 6.4], [24.0, 1.2, 1.0], STEEL_DARK)
    b.box([hx + 4.0, 0.55, hz - 14.0], [40.0, 0.6, 2.0], "#2a2f2a")
    b.cyl([hx, 9.75, hz], [3.0, 1.0, 3.0], STEEL_DARK)
    # the generator house
    area = (40.0, 100.0, 198.0, 246.0)
    s.reserve(rect(*area))
    building(b, area, 0.25, 12.0, "#8a8478", roof_colour="#4a4a52",
             floor_colour="#6a6a64", doors={"x-": [(212.0, 226.0, 10.0)]},
             windows={"z-": [(52.0, 70.0, 4.0, 8.6)]}, boards=True, lights=WARM)
    threshold(b, area, "x-", (212.0, 226.0), y0=0.25)
    for x in (58.0, 82.0):
        b.box([x, 0.65 + 3.5, 232.0], [12.0, 7.0, 10.0], "#5a6a5a", material="metal")
    supply_ammo(b, 92.0, 0.65, 204.0, "x-")
    for i in range(6):
        b.cyl([-96.0 + i * 5.0, 0.25 + 4.0, 194.0], [3.6, 8.0, 3.6],
              "#3a8a4a" if i % 2 else "#d8d8d0", material="metal")
    for x in (-60.0, 130.0):
        dumpster(b, x, 196.0, "x")
    barrel_spot(b, 20.0, 0.25, 190.0)
    barrel_spot(b, 140.0, 0.25, 250.0)
    for x in (-100.0, 160.0):
        lamp_post(b, x, 258.0, 16.0, y=0.25)
    # the fuel yard north-west of the garage
    s.lay(rect(-262.0, ROAD_C[0] - 6.0, 134.0, 262.0), 0.25, "#55595e")
    for x, z in ((-236.0, 170.0), (-200.0, 170.0)):
        b.cyl([x, 0.25 + 9.0, z], [26.0, 18.0, 26.0], "#c8c4b8", material="metal")
        b.cyl([x, 0.25 + 18.6, z], [24.0, 1.2, 24.0], "#a8a498", material="metal",
              collide=False)
    b.sphere([-210.0, 0.25, 236.0], [44.0, 30.0, 44.0], "#a8a090")
    hesco(b, -170.0, 214.0, 4, "z")
    barrel_spot(b, -170.0, 0.25, 150.0)
    treeline(b, -262.0, 270.0, 262.0, 270.0, 22, rng, 1.4, leaf="#24402c")


def _zombie_spawns(b: Area) -> None:
    pts = [
        # the north edge, behind the service yard and the fuel yard
        (-250, 262), (-190, 266), (-120, 270), (-60, 268), (20, 268), (80, 268),
        (140, 268), (220, 268), (270, 220),
        # the east edge, behind the clinic, the apartments and the mall
        (272, 140), (272, 30), (272, -40), (272, -110), (272, -170),
        # the south edge, the depot, the court and the construction site
        (-250, -274), (-170, -274), (-90, -274), (-20, -274), (60, -274),
        (130, -274), (200, -274), (262, -232),
        # the west edge, beside the garage and the maze
        (-272, -200), (-272, -140), (-272, -60), (-272, 30), (-272, 110),
        (-272, 190),
        # the ends of the roads, and the alley between the clinic and the flats
        (184, 274), (-132, 274), (232, 136),
        # deep in the maze's outer corners
        (-255, -168), (-156, -66),
    ]
    for x, z in pts:
        b.zombie_spawn(float(x), float(z), "maze" if z < -50 and x < -150 and z > -182 else "")
