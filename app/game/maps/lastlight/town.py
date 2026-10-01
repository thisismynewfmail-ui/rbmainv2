"""Harrow Main Street -- a small town at dusk, the night it fell.

Layout (north is +z, the street runs east-west through the middle)::

      z +280  ------------------- woods / boundary --------------------
              houses   houses  |Ch|  houses  |St|  SCHOOL      GYM
      z +155  ======= Maple Street ==========================================
              houses   houses  |ur|  houses  |at|  houses   houses
      z +106  ------- back alley (dumpsters, the long way round) -----------
              HARDWARE  BANK   |ch| DINER  SHERIFF  PHARMACY |io| BIJOU  GARAGE
      z    0  ======= MAIN STREET =========================================
              GRAVE  CHURCH+   |  | POST  TOWN SQUARE         |n | GAS STATION
              YARD   BELL TOWER|St|       fountain, gazebo     |Rd|  + mini-mart
      z -138  ------- Depot Road ------------------------------------------
              SILOS            boxcars on two tracks   DEPOT   WATER TOWER
      z -280  ------------------- boundary --------------------------------

The Sheriff's Office in the middle of the north row is the safe room:
everyone deploys in its lobby.  It has an armory, a first aid cabinet and a
stair to a sandbagged roof that looks down Main Street both ways.

The fights this place is built for:

* **Main Street** is the long open lane -- good for shooting, bad for being
  caught in.  Cars, barricades and the bus at the east end break it up.
* **The back alley** is the flank nobody watches; the dumpsters and the
  gaps between the shops let the horde in behind you.
* **The church** has the bell.  Climb the outside stair to the nave roof and
  walk into the belfry: ringing it draws every infected in town to the
  church steps for a few seconds -- time to get away, or to line them up.
* **The gas station** is a trap for whoever is standing in it: its pumps are
  explosive and the infected walk right past them.
* **The rail yard** is a maze of boxcars; two of them are open right through,
  so the train is a wall with doors in it.
"""
from __future__ import annotations

import math
import random
from typing import Dict, List

from .kit import (
    ASPHALT, BRICK, BRICK_DARK, CONCRETE, CONCRETE_DARK, CONCRETE_LIGHT,
    COLD, FLOOR, GLASS, HAZARD, LAMP, LINE_WHITE, LINE_YELLOW, PAVEMENT,
    PAVEMENT_DARK, RUST, SANDBAG, STEEL, STEEL_DARK, WARM, WOOD, WOOD_DARK,
    WOOD_LIGHT, Area, Surfaces, barrel_prop, barrel_spot, barrier, bench,
    boundary, building, bus, car, chain_fence, crate, deploy_pad, dumpster,
    face_sign, flight, flood, floodlight, gable, ground, holed_wall, house,
    lamp_post, pallet_stack, rect, room_walls, sandbags, sign_decal, slab,
    solid_fence, strip_light, supply_ammo, supply_med, threshold, treeline,
    wall, wall_sign)

HALF = 280.0
GRASS = "#4b6b3a"
GRASS_DARK = "#3f5d31"
DIRT = "#6b5a45"
GRAVEL = "#7c766c"

SKY = {"top": "#2c2748", "horizon": "#d9805a", "sun": [0.62, 0.22, -0.55],
       "clouds": 0.5, "tint": "#ffb27a"}
AMBIENT = "#7d6b78"

# street lines
MAIN_Z = 14.0          # half-width of Main Street's carriageway
WALK = 10.0            # pavement width
FRONT = MAIN_Z + WALK  # the building line on either side: z = +-24
CHURCH_ST = (-128.0, -112.0)
STATION_RD = (92.0, 108.0)
ALLEY = (100.0, 112.0)
MAPLE = (148.0, 162.0)
DEPOT_RD = (-146.0, -134.0)
TRACK1 = (-204.0, -192.0)
TRACK2 = (-232.0, -220.0)


def build(b: Area) -> None:
    rng = random.Random(0x7A11)
    ground(b, GRASS)
    boundary(b, 30.0, "#24331f", "#283224", rng, horizon="forest")
    s = Surfaces(b)
    _streets(b, s)
    _north_row(b, s, rng)
    _alley(b, s, rng)
    _maple(b, s, rng)
    _school(b, s, rng)
    _square(b, s, rng)
    _church(b, s, rng)
    _graveyard(b, s, rng)
    _gas_station(b, s, rng)
    _rail_yard(b, s, rng)
    _ends(b, s, rng)
    _woods(b, rng)
    _zombie_spawns(b)
    b.landmark(0, 40, "the Sheriff's Office")
    b.landmark(-84, 46, "Rosie's Diner")
    b.landmark(142, 50, "the Bijou")
    b.landmark(0, -80, "the town square")
    b.landmark(-180, -90, "the church")
    b.landmark(170, -70, "the gas station")
    b.landmark(-40, -215, "the rail yard")
    b.landmark(-220, -175, "the grain silos")
    b.landmark(190, 205, "the school")
    b.landmark(0, 106, "the back alley")
    b.landmark(-60, 155, "Maple Street")


# =============================================================== streets
def _streets(b: Area, s: Surfaces) -> None:
    H = HALF
    # Main Street and its pavements first: everything else fits round them
    s.lay(rect(-H, H, -MAIN_Z, MAIN_Z), 0.3, ASPHALT)
    s.lay(rect(-H, H, MAIN_Z, FRONT), 0.6, PAVEMENT)
    s.lay(rect(-H, H, -FRONT, -MAIN_Z), 0.6, PAVEMENT)
    # the side roads, from Main Street's pavements out to Maple and the depot
    for x0, x1 in (CHURCH_ST, STATION_RD):
        s.lay(rect(x0, x1, FRONT, MAPLE[1] + 6.0), 0.3, ASPHALT)
        s.lay(rect(x0, x1, DEPOT_RD[0], -FRONT), 0.3, ASPHALT)
    s.lay(rect(-H, H, MAPLE[0], MAPLE[1]), 0.3, ASPHALT)
    s.lay(rect(-H, H, MAPLE[0] - 6.0, MAPLE[0]), 0.6, PAVEMENT_DARK)
    s.lay(rect(-H, H, MAPLE[1], MAPLE[1] + 6.0), 0.6, PAVEMENT_DARK)
    s.lay(rect(-H, H, ALLEY[0], ALLEY[1]), 0.25, ASPHALT)
    s.lay(rect(-H, H, DEPOT_RD[0], DEPOT_RD[1]), 0.35, GRAVEL)
    # the centre line: a double yellow down Main Street, broken at the
    # junctions, and dashes down Maple
    for a, c in ((-H + 4, CHURCH_ST[0] - 2), (CHURCH_ST[1] + 2, -16.0),
                 (16.0, STATION_RD[0] - 2), (STATION_RD[1] + 2, H - 4)):
        for dz in (-0.7, 0.7):
            b.box([(a + c) / 2.0, 0.34, dz], [c - a, 0.08, 0.5], LINE_YELLOW,
                  collide=False)
    for i in range(26):
        x = -H + 12.0 + i * (2 * H - 24.0) / 25.0
        if CHURCH_ST[0] - 4 < x < CHURCH_ST[1] + 4 or \
                STATION_RD[0] - 4 < x < STATION_RD[1] + 4:
            continue
        b.box([x, 0.34, (MAPLE[0] + MAPLE[1]) / 2.0], [8.0, 0.08, 0.6],
              LINE_WHITE, collide=False)
    # zebra crossings at the square
    for i in range(7):
        b.box([-12.0 + i * 4.0, 0.34, 0.0], [2.2, 0.08, 2 * MAIN_Z - 3.0],
              LINE_WHITE, collide=False)
    # street lamps on both pavements
    for i in range(10):
        x = -252.0 + i * 56.0
        if abs(x - (CHURCH_ST[0] + CHURCH_ST[1]) / 2) < 14 or \
                abs(x - (STATION_RD[0] + STATION_RD[1]) / 2) < 14:
            x += 18.0
        if x < 240.0:
            lamp_post(b, x, MAIN_Z + 2.0, 15.0, arm="z-", y=0.6)
    for i in range(9):
        x = -224.0 + i * 56.0
        if abs(x - (CHURCH_ST[0] + CHURCH_ST[1]) / 2) < 14 or \
                abs(x - (STATION_RD[0] + STATION_RD[1]) / 2) < 14:
            x += 18.0
        lamp_post(b, x, -MAIN_Z - 2.0, 15.0, arm="z+", y=0.6)
    for i in range(6):
        x = -230.0 + i * 92.0
        lamp_post(b, x, MAPLE[1] + 3.0, 14.0, arm="z-", y=0.6)


# ============================================================ north row
def _storefront_sign(b: Area, x0: float, x1: float, text: str, bg: str,
                     fg: str, y: float = 12.6, h: float = 3.0) -> None:
    w = min(x1 - x0 - 6.0, max(12.0, len(text) * 2.2))
    wall_sign(b, (x0 + x1) / 2.0, y, FRONT - 0.35, w, h,
              sign_decal(text, bg, fg, w / h), "z-", bg)


def _awning(b: Area, x0: float, x1: float, colour: str, y: float = 10.9) -> None:
    """A canvas awning over the shop front: overhead, so it never gets in
    anybody's way, and fixed to the wall it hangs off."""
    slab(b, rect(x0 + 2.0, x1 - 2.0, FRONT - 5.0, FRONT), y, 0.5, colour)
    b.box([(x0 + x1) / 2.0, y - 1.15, FRONT - 4.85], [x1 - x0 - 4.0, 1.3, 0.3],
          colour, collide=False)


def _north_row(b: Area, s: Surfaces, rng: random.Random) -> None:
    for area in ((-268, -208, FRONT, 84), (-204, -140, FRONT, 74),
                 (-112, -56, FRONT, 70), (-46, 46, FRONT, 92),
                 (56, 92, FRONT, 72), (108, 176, FRONT, 96),
                 (180, 268, FRONT, 84)):
        s.reserve(rect(*area))
    _hardware(b, rng)
    _bank(b, s)
    _diner(b)
    _sheriff(b)
    _pharmacy(b)
    _theater(b)
    _garage(b, rng)
    # the gaps between the shops are passages through to the alley
    for x0, x1 in ((-56, -46), (46, 56)):
        s.lay(rect(x0, x1, FRONT, ALLEY[0]), 0.3, PAVEMENT_DARK)
        lamp_post(b, (x0 + x1) / 2.0, ALLEY[0] - 4.0, 12.0, y=0.3)


def _hardware(b: Area, rng: random.Random) -> None:
    x0, x1, z0, z1 = -268.0, -208.0, FRONT, 84.0
    building(b, (x0, x1, z0, z1), 0.0, 16.0, "#6e7b5a", roof_colour="#4a5240",
             floor_colour="#7d7466",
             doors={"z-": [(-244.0, -232.0, 11.0)], "z+": [(-226.0, -216.0, 11.0)]},
             windows={"z-": [(-264.0, -250.0, 3.0, 9.0), (-226.0, -212.0, 3.0, 9.0)],
                      "x+": [(40.0, 54.0, 4.0, 9.0)]},
             glass=True, parapet=2.4)
    threshold(b, (x0, x1, z0, z1), "z-", (-244.0, -232.0))
    threshold(b, (x0, x1, z0, z1), "z+", (-226.0, -216.0))
    _storefront_sign(b, x0, x1, "HARROW HARDWARE", "#2f3a24", "#f2e2a8")
    _awning(b, x0, x1, "#3f6b3a")
    # aisles of shelving, end-on to the door so you can see down them
    for x in (-260.0, -250.0, -226.0):
        b.box([x, FLOOR + 4.0, 56.0], [3.0, 8.0, 30.0], WOOD_DARK)
        for k in range(3):
            b.box([x, FLOOR + 1.4 + k * 2.4, 56.0], [3.4, 0.3, 30.4], STEEL)
    b.box([-218.0, FLOOR + 2.0, 40.0], [8.0, 4.0, 3.0], WOOD, studs=True)
    supply_ammo(b, -220.0, FLOOR, 66.0, "x-")
    crate(b, -262.0, FLOOR, 78.0, 4.5, WOOD)
    crate(b, -262.0, FLOOR + 4.5, 78.0, 3.6, WOOD_LIGHT)


def _bank(b: Area, s: Surfaces) -> None:
    x0, x1, z0, z1 = -204.0, -140.0, FRONT, 74.0
    stone = "#b9b29e"
    building(b, (x0, x1, z0, z1), 0.0, 20.0, stone, roof_colour="#8f887a",
             floor_colour="#c9c2ae", doors={"z-": [(-180.0, -164.0, 13.0)]},
             windows={"z-": [(-200.0, -188.0, 4.0, 14.0), (-156.0, -144.0, 4.0, 14.0)]},
             glass=True, parapet=3.0,
             parapet_gaps={"x+": [(28.0, 38.0)]})
    threshold(b, (x0, x1, z0, z1), "z-", (-180.0, -164.0))
    # the portico: four columns and a pediment over the door
    for x in (-184.0, -177.0, -167.0, -160.0):
        b.cyl([x, 10.0, FRONT - 2.4], [2.6, 20.0, 2.6], "#d6d0bd")
    slab(b, rect(-188.0, -156.0, FRONT - 5.0, FRONT), 21.2, 1.2, "#d6d0bd")
    face_sign(b, -172.0, 16.4, FRONT - 0.35, 24.0, 2.6,
              sign_decal("FIRST HARROW BANK", "#d6d0bd", "#3a3428", 24 / 2.6),
              "z-", "#d6d0bd")
    # teller counter and the vault door at the back
    b.box([-172.0, FLOOR + 2.2, 52.0], [50.0, 4.4, 3.0], WOOD_DARK, studs=True)
    b.cyl([-172.0, FLOOR + 7.0, z1 - 2.4], [11.0, 11.0, 0.8], STEEL,
          r=[math.pi / 2.0, 0, 0], collide=False, material="metal")
    # outside stair up the east wall to the roof
    flight(b, "z", 72.0, 30.0, x1, x1 + 10.0, 0.0, 21.2, CONCRETE_DARK,
           fill=0.0, rise=1.95)
    s.reserve(rect(x1, x1 + 10.0, 30.0, 72.0))
    crate(b, -150.0, 21.2, 34.0, 5.0, SANDBAG)


def _diner(b: Area) -> None:
    x0, x1, z0, z1 = -112.0, -56.0, FRONT, 70.0
    building(b, (x0, x1, z0, z1), 0.0, 13.0, "#c9cfd2", roof_colour="#8e2b2b",
             floor_colour="#e8e2d0",
             doors={"z-": [(-90.0, -80.0, 10.0)], "x+": [(52.0, 62.0, 10.0)]},
             windows={"z-": [(-110.0, -94.0, 3.2, 9.0), (-76.0, -58.0, 3.2, 9.0)],
                      "x-": [(32.0, 46.0, 3.2, 9.0)]},
             glass=True, lights=WARM)
    threshold(b, (x0, x1, z0, z1), "z-", (-90.0, -80.0))
    threshold(b, (x0, x1, z0, z1), "x+", (52.0, 62.0))
    # a chrome band and the neon script over the door
    b.box([-84.0, 12.4, FRONT - 0.3], [56.0, 0.8, 0.6], "#e8ecee",
          material="metal", collide=False)
    face_sign(b, -84.0, 15.4, FRONT + 1.0, 30.0, 4.2,
              sign_decal("ROSIE'S DINER", "#1b1b1b", "#ff5a7a", 30 / 4.2),
              "z-", "#1b1b1b")
    # counter with stools, booths under the windows
    b.box([-84.0, FLOOR + 2.0, 58.0], [40.0, 4.0, 3.0], "#b8323a", studs=True)
    for i in range(6):
        b.cyl([-100.0 + i * 6.4, FLOOR + 1.3, 54.0], [1.8, 2.6, 1.8], "#d8dde2",
              material="metal")
    for x in (-104.0, -66.0):
        for dz in (0.0, 9.0):
            b.box([x, FLOOR + 1.6, 30.0 + dz], [10.0, 3.2, 2.0], "#b8323a")
        b.box([x, FLOOR + 1.6, 34.5], [6.0, 3.2, 4.0], "#e8e2d0", studs=True)
    supply_med(b, -107.4, FLOOR, 50.0, "x+")


def _sheriff(b: Area) -> None:
    """The safe room: lobby with the deploy pads, armory, cells, roof."""
    x0, x1, z0, z1 = -46.0, 46.0, FRONT, 92.0
    stair = rect(-42.0, -10.0, 80.0, 90.0)
    building(b, (x0, x1, z0, z1), 0.0, 16.0, BRICK, roof_colour="#5a3a2c",
             floor_colour="#8c8478",
             doors={"z-": [(-8.0, 8.0, 12.0)], "z+": [(-8.0, 4.0, 11.0)],
                    "x-": [(56.0, 66.0, 11.0)], "x+": [(56.0, 66.0, 11.0)]},
             windows={"z-": [(-40.0, -22.0, 3.6, 10.0), (22.0, 40.0, 3.6, 10.0)],
                      "x-": [(30.0, 44.0, 3.6, 10.0)], "x+": [(30.0, 44.0, 3.6, 10.0)]},
             boards=True, roof_holes=[stair], parapet=3.4, lights=LAMP)
    for side, span in (("z-", (-8.0, 8.0)), ("z+", (-8.0, 4.0)),
                       ("x-", (56.0, 66.0)), ("x+", (56.0, 66.0))):
        threshold(b, (x0, x1, z0, z1), side, span)
    face_sign(b, 0.0, 13.6, FRONT - 0.35, 30.0, 3.4,
              sign_decal("HARROW COUNTY SHERIFF", "#2a2014", "#f2d27a", 30 / 3.4),
              "z-", "#2a2014")
    # the light bar over the door, red and blue
    b.box([-4.0, 12.6, FRONT - 0.45], [7.0, 0.9, 0.9], "#ff3a2a",
          material="neon", collide=False)
    b.box([4.0, 12.6, FRONT - 0.45], [7.0, 0.9, 0.9], "#3a7aff",
          material="neon", collide=False)
    for x in (-12.0, 12.0):
        b.cyl([x, 6.6, FRONT - 1.6], [2.2, 13.2, 2.2], "#d8cdb8")
    # inside: the front desk across the middle, cells along the back wall
    b.box([-2.0, FLOOR + 2.2, 52.0], [36.0, 4.4, 3.0], WOOD_DARK, studs=True)
    for x in (-32.0, 30.0):
        b.box([x, FLOOR + 1.6, 64.0], [8.0, 3.2, 5.0], WOOD, studs=True)
    b.box([9.5, FLOOR + 6.0, 82.0], [1.0, 12.0, 16.0], CONCRETE_LIGHT)
    for i in range(3):
        cx0 = 10.0 + i * 11.0
        b.box([cx0 + 10.5, FLOOR + 6.0, 82.0], [1.0, 12.0, 16.0], CONCRETE_LIGHT)
        for k in range(4):
            b.box([cx0 + 1.4 + k * 2.2, FLOOR + 6.0, 74.5], [0.5, 12.0, 0.5],
                  STEEL_DARK, material="metal")
        b.box([cx0 + 7.0, FLOOR + 1.0, 86.0], [5.0, 2.0, 7.0], "#6b7a8a")
    # stair to the roof in the back left corner, and a rail round its well
    flight(b, "x", stair[0], stair[1], stair[2], stair[3], FLOOR, 17.2,
           CONCRETE_DARK, fill=FLOOR, rise=1.92)
    b.box([(stair[0] + stair[1]) / 2.0 - 2.0, 18.7, stair[2] - 0.5],
          [stair[1] - stair[0] - 4.0, 3.0, 1.0], STEEL, material="metal")
    # armory and aid on the west wall
    supply_ammo(b, -36.0, FLOOR, 68.0, "x+")
    supply_med(b, 41.0, FLOOR, 71.0, "x-")
    # the deploy pads: sixteen, in the lobby, facing the front door
    for row, z in enumerate((34.0, 44.0)):
        for i, x in enumerate((-38.0, -28.0, -18.0, -10.0, 10.0, 18.0, 28.0, 38.0)):
            deploy_pad(b, x, z, FLOOR, "#4fa36a", 5.5)
            b.safe_spawn(x, FLOOR + 0.6, z, math.pi)
    # the roof: sandbag nests at the corners overlooking both ways down the
    # street, a floodlight, and the rack you reload from
    roof = 17.2
    for x in (-36.0, 36.0):
        b.box([x, roof + 1.8, FRONT + 6.0], [10.0, 3.6, 3.0], SANDBAG, studs=True)
    flood(b, 38.0, 84.0, roof, 10.0)
    supply_ammo(b, 20.0, roof, 70.0, "z-")
    # parked outside: the sheriff's cruiser
    car(b, 26.0, 8.0, "x", "#1d1f22", 12.0, y=0.3)
    b.box([26.0 - 0.6, 5.35, 8.0], [3.0, 0.4, 2.6], "#ff3a2a", material="neon",
          collide=False)
    for x in (-30.0, 30.0):
        sandbags(b, x, FRONT - 7.0, 12.0, "x", 4.0)


def _pharmacy(b: Area) -> None:
    x0, x1, z0, z1 = 56.0, 92.0, FRONT, 72.0
    building(b, (x0, x1, z0, z1), 0.0, 13.0, "#e6e4de", roof_colour="#6b7a7a",
             floor_colour="#d8dcd8",
             doors={"z-": [(68.0, 80.0, 10.0)], "x-": [(54.0, 64.0, 10.0)]},
             windows={"z-": [(58.0, 66.0, 3.2, 9.0), (82.0, 90.0, 3.2, 9.0)]},
             glass=True, lights=COLD)
    threshold(b, (x0, x1, z0, z1), "z-", (68.0, 80.0))
    threshold(b, (x0, x1, z0, z1), "x-", (54.0, 64.0))
    _storefront_sign(b, x0, x1, "PHARMACY", "#ffffff", "#2f8f4a")
    # the green cross, lit
    b.box([59.6, 11.5, FRONT - 0.5], [1.4, 4.2, 1.0], "#3aff7a",
          material="neon", collide=False)
    b.box([59.6, 11.5, FRONT - 0.45], [4.2, 1.4, 0.9], "#3aff7a",
          material="neon", collide=False)
    for x in (62.0, 86.0):
        b.box([x, FLOOR + 3.5, 52.0], [3.0, 7.0, 24.0], "#d8dcd8")
    b.box([74.0, FLOOR + 2.0, 64.0], [16.0, 4.0, 3.0], "#2f8f4a", studs=True)
    supply_med(b, 74.0, FLOOR, 68.4, "z-")


def _theater(b: Area) -> None:
    """The Bijou: lobby, an auditorium with raked seating, the marquee."""
    x0, x1, z0, z1 = 108.0, 176.0, FRONT, 96.0
    building(b, (x0, x1, z0, z1), 0.0, 22.0, "#7a2f3a", roof_colour="#3a2028",
             floor_colour="#5a2a2a",
             doors={"z-": [(128.0, 156.0, 12.0)], "x+": [(78.0, 90.0, 11.0)],
                    "x-": [(78.0, 90.0, 11.0)]},
             lights="#ffd27a")
    for side, span in (("z-", (128.0, 156.0)), ("x+", (78.0, 90.0)),
                       ("x-", (78.0, 90.0))):
        threshold(b, (x0, x1, z0, z1), side, span)
    # the lobby wall, with three ways into the auditorium
    holed_wall(b, "x", 50.0, 2.0, x0 + 2.0, x1 - 2.0, 0.0, 22.0, "#5a2028",
               [(114.0, 124.0, -1.0, 12.0), (137.0, 147.0, -1.0, 12.0),
                (160.0, 170.0, -1.0, 12.0)])
    # raked seating: rows rising towards the back, every row a step
    for i in range(5):
        z = 56.0 + i * 5.0
        slab(b, rect(x0 + 2.0, x1 - 2.0, z, z + 5.0), FLOOR + 1.0 + i * 1.0,
             1.0 + i * 1.0, "#4a1f24")
        for k in range(8):
            b.box([114.0 + k * 7.4, FLOOR + 2.0 + i * 1.0, z + 3.6],
                  [5.6, 2.0, 1.2], "#8a2a30")
    # the screen on the far wall, glowing
    b.box([142.0, 13.0, 93.85], [52.0, 12.0, 0.3], "#e6eef8", material="neon",
          collide=False)
    # the marquee over the pavement: overhead, so it hangs clear of heads
    slab(b, rect(116.0, 168.0, FRONT - 8.0, FRONT), 14.6, 2.4, "#2a1418")
    face_sign(b, 142.0, 13.4, FRONT - 8.35, 48.0, 4.4,
              sign_decal("BIJOU  -  NIGHT OF THE LIVING NOOB", "#fff3c4",
                         "#1b1b1b", 48 / 4.4), "z-", "#fff3c4")
    for i in range(12):
        b.box([118.0 + i * 4.4, 14.8, FRONT - 7.4], [1.4, 0.4, 0.6], "#ffe27a",
              material="neon", collide=False)
    # the vertical blade sign
    b.box([170.0, 24.0, FRONT - 2.0], [1.6, 18.0, 4.0], "#2a1418",
          collide=False)
    face_sign(b, 171.15, 24.0, FRONT - 2.0, 3.6, 16.0,
              sign_decal("BIJOU", "#2a1418", "#ffb03a", 3.6 / 16.0), "x+",
              "#2a1418")
    supply_ammo(b, 166.0, FLOOR, 40.0, "x-")


def _garage(b: Area, rng: random.Random) -> None:
    x0, x1, z0, z1 = 180.0, 268.0, FRONT, 84.0
    building(b, (x0, x1, z0, z1), 0.0, 15.0, "#c9c3b0", roof_colour="#6b6656",
             floor_colour="#7a7a74",
             doors={"z-": [(188.0, 206.0, 12.0), (238.0, 256.0, 12.0)],
                    "z+": [(218.0, 228.0, 10.0)]},
             windows={"z-": [(212.0, 232.0, 4.0, 10.0)]}, glass=True)
    for span in ((188.0, 206.0), (238.0, 256.0)):
        threshold(b, (x0, x1, z0, z1), "z-", span)
    threshold(b, (x0, x1, z0, z1), "z+", (218.0, 228.0))
    _storefront_sign(b, x0, x1, "MILLER AUTO REPAIR", "#1f3a5a", "#f2f2f2")
    # a car up on the lift and one waiting
    for x in (197.0, 247.0):
        b.box([x, FLOOR + 0.2, 52.0], [10.0, 0.4, 20.0], HAZARD, collide=False)
    b.box([197.0, FLOOR + 3.8, 52.0], [1.2, 7.6, 1.2], STEEL)
    car(b, 197.0, 52.0, "z", "#2f5f8a", 12.0, y=FLOOR + 7.0)
    car(b, 247.0, 52.0, "z", "#8a7a2f", 12.0, y=FLOOR)
    b.box([262.0, FLOOR + 3.0, 60.0], [3.0, 6.0, 20.0], "#a8323a", material="metal")
    pallet_stack(b, 224.0, 74.0, 3)
    barrel_spot(b, 214.0, FLOOR, 72.0)


# ================================================================ alley
def _alley(b: Area, s: Surfaces, rng: random.Random) -> None:
    for x, along in ((-238.0, "x"), (-170.0, "x"), (-84.0, "x"), (74.0, "x"),
                     (210.0, "x")):
        dumpster(b, x, ALLEY[0] - 3.0, along)
    for x in (-130.0, 20.0, 130.0):
        crate(b, x, 0.25, ALLEY[1] - 3.0, 5.0, WOOD)
    pallet_stack(b, -60.0, ALLEY[1] - 4.0, 4)
    barrel_spot(b, -150.0, 0.25, 106.0)
    barrel_spot(b, 100.0, 0.25, 106.0)
    barrel_spot(b, -20.0, 0.25, 106.0)
    for x in (-200.0, -40.0, 160.0):
        barrel_prop(b, x, ALLEY[1] - 2.6, RUST, 0.25)


# =========================================================== Maple St
def _maple(b: Area, s: Surfaces, rng: random.Random) -> None:
    colours = ["#c9b48b", "#8fa8b8", "#b88a7a", "#a8b88f", "#d8d0c0",
               "#b8a07a", "#9a8fb8", "#c8c0a8"]
    roofs = ["#4a3a30", "#3a4048", "#5a2a24", "#3a4a34"]
    # south of Maple: houses facing north onto the street
    south = [(-262.0, -236.0), (-226.0, -200.0), (-186.0, -160.0),
             (-98.0, -72.0), (-34.0, -8.0), (30.0, 56.0), (122.0, 148.0),
             (176.0, 202.0), (230.0, 256.0)]
    for i, (x0, x1) in enumerate(south):
        area = rect(x0, x1, 116.0, 136.0)
        s.reserve(rect(x0 - 1.0, x1 + 1.0, 116.0, 143.0))
        house(b, area, "z+", colours[i % len(colours)], roofs[i % len(roofs)],
              enterable=i % 3 != 1, rng=rng)
        solid_fence(b, x0 - 3.0, 113.0, x0 - 3.0, 136.0, 5.0)
    solid_fence(b, 259.0, 113.0, 259.0, 136.0, 5.0)
    # north of Maple, west of Station Road: houses facing south
    north = [(-262.0, -236.0), (-222.0, -196.0), (-176.0, -150.0),
             (-100.0, -74.0), (-56.0, -30.0), (-8.0, 18.0), (40.0, 66.0)]
    for i, (x0, x1) in enumerate(north):
        area = rect(x0, x1, 176.0, 198.0)
        s.reserve(rect(x0 - 1.0, x1 + 1.0, 169.0, 198.0))
        house(b, area, "z-", colours[(i + 3) % len(colours)],
              roofs[(i + 1) % len(roofs)], enterable=i % 2 == 0, rng=rng,
              back_door=i % 4 == 0)
        # back yards, fenced, with the gate side open
        solid_fence(b, x0 - 4.0, 198.0, x0 - 4.0, 232.0, 5.0)
        solid_fence(b, x0 - 4.0, 232.0, x1 - 6.0, 232.0, 5.0, first_post=False)
        if rng.random() < 0.6:
            b.tree((x0 + x1) / 2.0, 216.0, 0.0, 1.1, WOOD, "#3f6b2f")
        else:
            crate(b, (x0 + x1) / 2.0 + 6.0, 0.0, 214.0, 4.0, "#4a6a8a")
    # parked cars and a crash on Maple
    car(b, -140.0, MAPLE[0] + 4.0, "x", "#6a7a8a", y=0.3)
    car(b, -20.0, MAPLE[1] - 4.0, "x", "#8a3a2a", y=0.3)
    car(b, 60.0, MAPLE[0] + 4.0, "x", "#2a2a2a", wrecked=True, y=0.3)
    car(b, 200.0, MAPLE[1] - 4.0, "x", "#d8d0b8", y=0.3)
    barrier(b, -190.0, (MAPLE[0] + MAPLE[1]) / 2.0, 14.0, "x")
    for x in (-118.0, 102.0):
        b.box([x, 9.0, MAPLE[0] - 4.0], [0.8, 18.0, 0.8], STEEL_DARK)
        face_sign(b, x, 16.0, MAPLE[0] - 4.75, 10.0, 2.0,
                  sign_decal("MAPLE ST", "#2f6b3a", "#ffffff", 5.0), "z-",
                  "#2f6b3a")


def _school(b: Area, s: Surfaces, rng: random.Random) -> None:
    """Harrow Elementary: a hall of classrooms and the gym beside it."""
    x0, x1, z0, z1 = 116.0, 200.0, 176.0, 232.0
    s.reserve(rect(x0, 266.0, 170.0, 232.0))
    s.lay(rect(116.0, 266.0, MAPLE[1] + 6.0, 176.0), 0.45, PAVEMENT)
    building(b, (x0, x1, z0, z1), 0.0, 16.0, "#c87a4a", roof_colour="#5a4a3a",
             floor_colour="#b8b0a0",
             doors={"z-": [(150.0, 166.0, 12.0)], "x+": [(196.0, 210.0, 11.0)],
                    "z+": [(128.0, 138.0, 10.0)]},
             windows={"z-": [(120.0, 140.0, 4.0, 10.0), (176.0, 196.0, 4.0, 10.0)],
                      "z+": [(150.0, 196.0, 4.0, 10.0)]},
             glass=True, parapet=2.0, no_lights=[rect(116.0, 200.0, 201.0, 207.0)])
    for side, span in (("z-", (150.0, 166.0)), ("x+", (196.0, 210.0)),
                       ("z+", (128.0, 138.0))):
        threshold(b, (x0, x1, z0, z1), side, span)
    # a corridor wall with classroom doors
    holed_wall(b, "x", 204.0, 1.6, x0 + 2.0, x1 - 2.0, FLOOR, 16.0, "#d8cdb8",
               [(124.0, 132.0, 0.0, 10.5), (146.0, 170.0, 0.0, 12.0),
                (184.0, 192.0, 0.0, 10.5)])
    for i in range(4):
        for k in range(3):
            b.box([128.0 + i * 16.0, FLOOR + 1.4, 212.0 + k * 6.0],
                  [5.0, 2.8, 3.0], "#c8a878", studs=True)
    b.box([158.0, FLOOR + 6.0, 229.85], [28.0, 7.0, 0.3], "#2f4a3a")
    supply_med(b, 195.3, FLOOR, 188.0, "x-")
    face_sign(b, 158.0, 13.6, z0 - 0.35, 34.0, 3.2,
              sign_decal("HARROW ELEMENTARY", "#f2f2f2", "#7a2f2a", 34 / 3.2),
              "z-", "#f2f2f2")
    # the gym
    g0, g1 = 206.0, 264.0
    building(b, (g0, g1, z0, z1), 0.0, 22.0, "#b86a3a", roof_colour="#4a3a30",
             floor_colour="#c89a5a",
             doors={"x-": [(196.0, 210.0, 11.0)], "z-": [(226.0, 244.0, 12.0)]},
             windows={"x+": [(186.0, 222.0, 14.0, 20.0)]}, glass=True)
    threshold(b, (g0, g1, z0, z1), "x-", (196.0, 210.0))
    threshold(b, (g0, g1, z0, z1), "z-", (226.0, 244.0))
    slab(b, rect(200.0, 206.0, 196.0, 210.0), FLOOR, FLOOR, "#b8b0a0")
    # bleachers up the back wall, and the hoops
    for i in range(4):
        slab(b, rect(g0 + 2.0, g1 - 2.0, 222.0 + i * 2.0, 230.0),
             FLOOR + 1.6 + i * 1.6, 1.6, "#a87a4a" if i % 2 else "#8a6a3a")
    for x in (g0 + 2.6, g1 - 2.6):
        b.box([x, 11.0, 196.0], [1.2, 6.0, 8.0], "#f2f2f2", collide=False)
    supply_ammo(b, 252.0, FLOOR, 186.0, "z+")
    # the playground behind, and the school buses
    chain_fence(b, 116.0, 244.0, 264.0, 244.0, 7.0)
    for x in (140.0, 170.0):
        b.box([x, 4.0, 254.0], [1.0, 8.0, 1.0], "#c42b20")
        b.box([x + 10.0, 4.0, 254.0], [1.0, 8.0, 1.0], "#c42b20")
        b.box([x + 5.0, 8.4, 254.0], [11.0, 0.8, 1.0], "#c42b20")
    slab(b, rect(204.0, 222.0, 248.0, 258.0), 6.0, 6.0, "#2f6b9a")
    flight(b, "z", 258.0, 248.0, 222.0, 228.0, 0.0, 6.0, "#d8a83a", fill=0.0)
    bus(b, 236.0, 156.0, "x", label="HARROW SCHOOLS")


# ============================================================== square
def _square(b: Area, s: Surfaces, rng: random.Random) -> None:
    x0, x1, z0, z1 = -70.0, 70.0, -130.0, -FRONT
    # the plaza and paths first, the lawn fitted round them
    s.lay(rect(-26.0, 26.0, -106.0, -54.0), 0.35, "#b8b0a0")
    s.lay(rect(-5.0, 5.0, z0, z1), 0.32, "#a8a090")
    s.lay(rect(x0, x1, -84.0, -76.0), 0.32, "#a8a090")
    s.lay(rect(x0, x1, z0, z1), 0.16, GRASS_DARK, studs=True, material="grass")
    # the fountain: a basin you can stand in, water, the column and the bowl
    room_walls(b, rect(-11.0, 11.0, -91.0, -69.0), 1.6, 0.35, 2.8, "#c8c0b0")
    b.water(0.0, -80.0, 18.8, 18.8, 1.6, "#3f7f9f")
    b.cyl([0.0, 3.6, -80.0], [3.6, 6.5, 3.6], "#c8c0b0")
    b.cyl([0.0, 7.2, -80.0], [10.0, 1.2, 10.0], "#c8c0b0")
    b.cyl([0.0, 7.95, -80.0], [8.4, 0.3, 8.4], "#5fa8c8", material="glass",
          collide=False, alpha=0.8)
    # the gazebo
    slab(b, rect(-9.0, 9.0, -125.0, -107.0), 1.4, 1.4, "#e8e2d4")
    for x in (-8.0, 8.0):
        for z in (-124.0, -108.0):
            b.box([x, 1.4 + 4.6, z], [1.2, 9.2, 1.2], "#f2ede0")
    slab(b, rect(-10.0, 10.0, -126.0, -106.0), 11.2, 0.6, "#5a3a30")
    gable(b, rect(-10.0, 10.0, -126.0, -106.0), 11.2, "#5a3a30", "x", 3, 1.2, 0.0)
    # the memorial: the town founder, in bronze
    b.box([0.0, 2.0, -42.0], [8.0, 4.0, 8.0], "#8f887a", studs=True)
    b.box([0.0, 6.2, -42.0], [3.0, 4.4, 2.0], "#6b5a3a", material="metal")
    b.box([0.0, 9.3, -42.0], [1.8, 1.8, 1.8], "#6b5a3a", material="metal")
    b.box([0.0, 10.6, -42.0], [2.6, 0.8, 2.6], "#5a4a2a", material="metal")
    for x, z in ((-40.0, -50.0), (40.0, -50.0), (-40.0, -112.0), (40.0, -112.0),
                 (-58.0, -80.0), (58.0, -80.0)):
        b.tree(x, z, 0.16, 1.25, WOOD, "#3f6b2f")
    for x, z, along in ((-18.0, -64.0, "x"), (18.0, -64.0, "x"),
                        (-18.0, -96.0, "x"), (18.0, -96.0, "x")):
        bench(b, x, z, along)
    for x, z in ((-30.0, -58.0), (30.0, -58.0), (-30.0, -102.0), (30.0, -102.0)):
        lamp_post(b, x, z, 12.0, y=0.16)
    barrel_spot(b, -60.0, 0.16, -126.0)
    barrel_spot(b, 62.0, 0.16, -40.0)
    # the post office between the square and Church Street
    px0, px1, pz0, pz1 = -106.0, -76.0, -76.0, -32.0
    s.reserve(rect(px0, px1, pz0, pz1))
    building(b, (px0, px1, pz0, pz1), 0.0, 12.0, "#b8a88a", roof_colour="#4a4a52",
             floor_colour="#a8a090", doors={"z+": [(-96.0, -86.0, 10.0)],
                                             "x+": [(-62.0, -52.0, 10.0)]},
             windows={"x-": [(-66.0, -44.0, 3.6, 8.6)]}, glass=True)
    threshold(b, (px0, px1, pz0, pz1), "z+", (-96.0, -86.0))
    threshold(b, (px0, px1, pz0, pz1), "x+", (-62.0, -52.0))
    face_sign(b, -91.0, 10.0, pz1 + 0.35, 20.0, 2.6,
              sign_decal("U.S. POST OFFICE", "#f2f2f2", "#1f3a6b", 20 / 2.6),
              "z+", "#f2f2f2")
    b.box([-91.0, FLOOR + 2.0, -54.0], [20.0, 4.0, 3.0], WOOD, studs=True)
    b.box([-70.0, 2.4, -36.0], [2.4, 4.8, 2.4], "#2a4a8a")
    # a little car park between the square and Station Road
    s.lay(rect(74.0, STATION_RD[0], -126.0, -30.0), 0.3, ASPHALT)
    car(b, 83.0, -50.0, "z", "#4a6a3a", y=0.3)
    car(b, 83.0, -96.0, "z", "#7a7a7a", wrecked=True, y=0.3)


# ============================================================== church
def _church(b: Area, s: Surfaces, rng: random.Random) -> None:
    """The nave, the bell tower, and the stair to the roof the tower opens
    onto.  The bell is the lure."""
    nx0, nx1, nz0, nz1 = -214.0, -146.0, -130.0, -56.0
    tx0, tx1, tz0, tz1 = -190.0, -170.0, -56.0, -36.0
    stone = "#a8a49a"
    s.reserve(rect(nx0, nx1 + 10.0, nz0, nz1))
    s.reserve(rect(tx0, tx1, tz0, tz1 + 4.0))
    roof_top = 21.2
    building(b, (nx0, nx1, nz0, nz1), 0.0, 20.0, stone, roof_colour="#4a4f58",
             floor_colour="#8a7a64",
             doors={"z+": [(-186.0, -174.0, 13.0)], "x-": [(-104.0, -94.0, 11.0)]},
             windows={"x-": [(-122.0, -112.0, 8.0, 17.0), (-82.0, -72.0, 8.0, 17.0)],
                      "x+": [(-122.0, -112.0, 8.0, 17.0), (-100.0, -90.0, 8.0, 17.0)]},
             glass=True, parapet=3.0,
             parapet_gaps={"z+": [(tx0, tx1)], "x+": [(-76.0, -68.0)]},
             lights="#ffd8a0")
    threshold(b, (nx0, nx1, nz0, nz1), "z+", (-186.0, -174.0))
    threshold(b, (nx0, nx1, nz0, nz1), "x-", (-104.0, -94.0))
    # stained glass: colour washed over the clear panes
    for x in (nx0 - 0.08, nx1 + 0.08):
        for z0, z1 in ((-122.0, -112.0), (-82.0, -72.0) if x < -180 else (-100.0, -90.0)):
            b.box([x, 12.5, (z0 + z1) / 2.0], [0.12, 9.0, z1 - z0],
                  rng.choice(["#c43a3a", "#3a5ac4", "#c4a83a", "#3ac47a"]),
                  material="glass", alpha=0.55, collide=False)
    # pews either side of the aisle, the altar under the east window
    for i in range(7):
        z = -66.0 - i * 7.5
        for x in (-200.0, -160.0):
            b.box([x, FLOOR + 1.3, z], [22.0, 2.6, 2.4], WOOD_DARK)
    b.box([-180.0, FLOOR + 2.2, -122.0], [16.0, 4.4, 5.0], "#e8e2d4", studs=True)
    for x in (-186.0, -174.0):
        b.cyl([x, FLOOR + 5.2, -122.0], [0.8, 1.6, 0.8], "#f2ede0")
        b.sphere([x, FLOOR + 6.4, -122.0], [0.6, 0.9, 0.6], "#ffb03a",
                 material="neon", collide=False)
    supply_med(b, -210.0, FLOOR, -76.0, "x+")
    # the bell tower: a vestibule below, the belfry above at roof height
    holed_wall(b, "z", tx0 + 1.0, 2.0, tz0, tz1, 0.0, 20.0, stone)
    holed_wall(b, "z", tx1 - 1.0, 2.0, tz0, tz1, 0.0, 20.0, stone)
    holed_wall(b, "x", tz1 - 1.0, 2.0, tx0 + 2.0, tx1 - 2.0, 0.0, 20.0, stone,
               [(-184.0, -176.0, -1.0, 12.0)])
    slab(b, rect(tx0 + 2.0, tx1 - 2.0, tz0, tz1 - 2.0), FLOOR, FLOOR, "#8a7a64")
    slab(b, rect(-184.0, -176.0, tz1 - 2.0, tz1), FLOOR, FLOOR, "#8a7a64")
    slab(b, rect(tx0, tx1, tz0, tz1), roof_top, 1.2, "#6a6458")
    for x in (tx0 + 2.0, tx1 - 2.0):
        for z in (tz0 + 2.0, tz1 - 2.0):
            b.box([x, roof_top + 6.0, z], [4.0, 12.0, 4.0], stone)
    # waist-high rails between the pillars on the three open faces
    b.box([(tx0 + tx1) / 2.0, roof_top + 1.4, tz1 - 1.0], [12.0, 2.8, 2.0], stone)
    for x in (tx0 + 1.0, tx1 - 1.0):
        b.box([x, roof_top + 1.4, (tz0 + tz1) / 2.0], [2.0, 2.8, 12.0], stone)
    slab(b, rect(tx0 - 1.0, tx1 + 1.0, tz0 - 1.0, tz1 + 1.0), roof_top + 13.2,
         1.2, "#4a4f58")
    b.cone([(tx0 + tx1) / 2.0, roof_top + 20.6, (tz0 + tz1) / 2.0],
           [20.0, 14.8, 20.0], "#3a3f48", collide=False)
    b.box([(tx0 + tx1) / 2.0, roof_top + 29.9, (tz0 + tz1) / 2.0],
          [0.6, 4.0, 0.6], "#d8c87a", material="metal", collide=False)
    b.box([(tx0 + tx1) / 2.0, roof_top + 30.8, (tz0 + tz1) / 2.0],
          [2.4, 0.6, 0.6], "#d8c87a", material="metal", collide=False)
    # the bell, hung from the belfry ceiling
    bx, bz = (tx0 + tx1) / 2.0, (tz0 + tz1) / 2.0
    b.box([bx, roof_top + 11.4, bz], [0.6, 1.2, 0.6], STEEL_DARK, collide=False)
    b.cone([bx, roof_top + 9.0, bz], [5.6, 4.6, 5.6], "#b8862a",
           material="metal", collide=False)
    b.set_lure(bx, roof_top, bz - 3.0, "the church bell", "Ring the bell",
               "bell", (bx, 0.6, tz1 + 14.0))
    face_sign(b, (tx0 + tx1) / 2.0, 16.0, tz1 + 0.35, 14.0, 3.0,
              sign_decal("ST. JUDE'S", "#e8e2d4", "#3a2a1a", 14 / 3.0),
              "z+", "#e8e2d4")
    # the outside stair up the east wall to the nave roof
    flight(b, "z", nz0 + 2.0, -70.0, nx1, nx1 + 10.0, 0.0, roof_top,
           CONCRETE_DARK, fill=0.0, rise=1.95)
    b.landmark(bx, bz, "the bell tower")


def _graveyard(b: Area, s: Surfaces, rng: random.Random) -> None:
    x0, x1, z0, z1 = -268.0, -220.0, -134.0, -32.0
    s.reserve(rect(x0, x1, z0, z1))
    for i in range(4):
        for k in range(4):
            x = -260.0 + k * 11.0 + rng.uniform(-1.0, 1.0)
            z = -46.0 - i * 18.0 + rng.uniform(-1.5, 1.5)
            h = rng.uniform(2.6, 4.2)
            b.box([x, h / 2.0, z], [3.2, h, 0.9], "#8f9296")
    # the mausoleum
    building(b, (-266.0, -246.0, -128.0, -110.0), 0.0, 11.0, "#9a968c",
             roof_colour="#6f6c64", floor_colour="#7a766c",
             doors={"z+": [(-260.0, -252.0, 8.6)]})
    threshold(b, (-266.0, -246.0, -128.0, -110.0), "z+", (-260.0, -252.0))
    gable(b, rect(-266.0, -246.0, -128.0, -110.0), 12.2, "#6f6c64", "z", 2, 1.4, 0.0)
    for z in (-30.0, -134.0):
        chain_fence(b, x0, z, x1, z, 6.0, 12.0)
    chain_fence(b, x1, -134.0, x1, -60.0, 6.0, 12.0)
    for x, z in ((-232.0, -60.0), (-226.0, -122.0)):
        b.tree(x, z, 0.0, 1.0, "#3a2e24", "#3a4a2a")


# ========================================================= gas station
def _gas_station(b: Area, s: Surfaces, rng: random.Random) -> None:
    x0, x1, z0, z1 = STATION_RD[1], 240.0, -128.0, -FRONT
    s.reserve(rect(206.0, 250.0, -92.0, -40.0))
    s.lay(rect(x0, x1, z0, z1), 0.3, "#4a4f55")
    # the canopy over the pumps
    cx0, cx1, cz0, cz1 = 126.0, 198.0, -88.0, -42.0
    for x in (130.0, 194.0):
        for z in (-84.0, -46.0):
            b.box([x, 7.15, z], [2.6, 13.7, 2.6], "#e8e8e8")
    slab(b, rect(cx0, cx1, cz0, cz1), 15.6, 1.6, "#f2f2f2")
    for z in (cz0 - 0.15, cz1 + 0.15):
        b.box([(cx0 + cx1) / 2.0, 14.8, z], [cx1 - cx0, 1.2, 0.3], "#e83a2a",
              material="neon", collide=False)
    for x in (cx0 - 0.15, cx1 + 0.15):
        b.box([x, 14.8, (cz0 + cz1) / 2.0], [0.3, 1.2, cz1 - cz0], "#e83a2a",
              material="neon", collide=False)
    strip_light(b, 162.0, -65.0, 14.0, 60.0, "x", "#fff6e0")
    # two islands, two pumps each; the pumps are the explosive kind
    for z in (-74.0, -56.0):
        slab(b, rect(140.0, 184.0, z - 2.5, z + 2.5), 0.9, 0.6, CONCRETE_LIGHT)
        for x in (150.0, 174.0):
            b.box([x, 0.9 + 2.6, z], [3.0, 5.2, 2.2], "#c42b20", studs=True)
            b.box([x, 0.9 + 4.2, z + 1.14], [2.2, 1.2, 0.08], "#1b1b1b",
                  material="neon", collide=False)
            barrel_spot(b, x + (4.0 if x < 160 else -4.0), 0.9, z)
    # the price pylon by the road
    b.box([224.0, 9.0, -30.0], [1.4, 18.0, 1.4], STEEL_DARK)
    face_sign(b, 224.0, 19.0, -29.3 + 0.0, 10.0, 8.0,
              sign_decal("GAS 3.99", "#e83a2a", "#ffffff", 10.0 / 8.0), "z+",
              "#e83a2a")
    # the mini-mart
    mx0, mx1, mz0, mz1 = 206.0, 250.0, -92.0, -40.0
    building(b, (mx0, mx1, mz0, mz1), 0.0, 12.0, "#e8e2d4", roof_colour="#c42b20",
             floor_colour="#d8d4c8", doors={"x-": [(-72.0, -60.0, 10.0)],
                                             "z-": [(220.0, 230.0, 10.0)]},
             windows={"x-": [(-88.0, -76.0, 3.2, 9.0), (-56.0, -44.0, 3.2, 9.0)]},
             glass=True, lights=COLD)
    threshold(b, (mx0, mx1, mz0, mz1), "x-", (-72.0, -60.0))
    threshold(b, (mx0, mx1, mz0, mz1), "z-", (220.0, 230.0))
    face_sign(b, mx0 - 0.35, 10.2, -66.0, 26.0, 2.8,
              sign_decal("HARROW STOP & GO", "#c42b20", "#ffffff", 26 / 2.8),
              "x-", "#c42b20")
    for z in (-80.0, -66.0, -52.0):
        b.box([232.0, FLOOR + 2.5, z], [14.0, 5.0, 3.0], "#d8dcd8")
    b.box([212.0, FLOOR + 2.0, -82.0], [3.0, 4.0, 10.0], WOOD, studs=True)
    supply_ammo(b, 244.0, FLOOR, -84.0, "x-")
    car(b, 162.0, -100.0, "x", "#3a5a8a", y=0.3)
    car(b, 130.0, -112.0, "x", "#2a2a2a", wrecked=True, y=0.3)


# ============================================================ rail yard
def _rail_yard(b: Area, s: Surfaces, rng: random.Random) -> None:
    H = HALF
    for z0, z1 in (TRACK1, TRACK2):
        s.lay(rect(-H, H, z0, z1), 0.5, GRAVEL)
        for dz in (2.4, -2.4):
            zc = (z0 + z1) / 2.0 + dz
            b.box([0.0, 0.85, zc], [2 * H, 0.7, 0.7], "#5a5f66", material="metal")
        for i in range(36):
            x = -H + 8.0 + i * (2 * H - 16.0) / 35.0
            b.box([x, 0.6, (z0 + z1) / 2.0], [1.6, 0.2, z1 - z0 - 1.0], WOOD_DARK,
                  collide=False)
    # boxcars: solid ones are walls, open ones are doors through the train
    palette = ["#8a3a2a", "#3a5a6a", "#6a5a3a", "#5a3a4a", "#4a5a3a"]
    cars = [(TRACK1, -170.0, False), (TRACK1, -116.0, True), (TRACK1, 30.0, False),
            (TRACK1, 84.0, False), (TRACK1, 196.0, True),
            (TRACK2, -60.0, True), (TRACK2, 130.0, False), (TRACK2, -224.0, False),
            (TRACK2, 230.0, False)]
    for (z0, z1), x, open_through in cars:
        zc = (z0 + z1) / 2.0
        colour = rng.choice(palette)
        x0, x1 = x - 20.0, x + 20.0
        bz0, bz1 = zc - 4.6, zc + 4.6
        b.box([x, 1.25, zc], [36.0, 1.5, 7.0], "#22262b")
        if not open_through:
            b.box([x, 6.5, zc], [40.0, 9.0, 9.2], colour, studs=True)
            for dz in (-4.66, 4.66):
                b.box([x, 6.0, zc + dz], [10.0, 7.0, 0.12], STEEL_DARK)
        else:
            slab(b, rect(x0 + 1.0, x1 - 1.0, bz0 + 1.0, bz1 - 1.0), 2.6, 0.6,
                 "#5a4a3a")
            holed_wall(b, "z", x0 + 0.5, 1.0, bz0, bz1, 2.0, 11.0, colour)
            holed_wall(b, "z", x1 - 0.5, 1.0, bz0, bz1, 2.0, 11.0, colour)
            for zw in (bz0 + 0.5, bz1 - 0.5):
                holed_wall(b, "x", zw, 1.0, x0 + 1.0, x1 - 1.0, 2.0, 11.0, colour,
                           [(x - 5.0, x + 5.0, 1.0, 9.8)])
                slab(b, rect(x - 5.0, x + 5.0, zw - 0.5, zw + 0.5), 2.6, 0.6,
                     "#5a4a3a")
            slab(b, rect(x0, x1, bz0, bz1), 11.8, 0.8, colour, studs=True)
            for dz in (-1, 1):
                slab(b, rect(x - 5.0, x + 5.0, zc + dz * 4.6 - (2.0 if dz < 0 else 0.0),
                             zc + dz * 4.6 + (0.0 if dz < 0 else 2.0)), 1.6, 1.6,
                     "#4a4f55")
        for end in (-1, 1):
            for dz in (-2.6, 2.6):
                b.cyl([x + end * 14.0, 1.3, zc + dz], [2.2, 0.8, 2.2], "#1b1d20",
                      r=[math.pi / 2.0, 0, 0], collide=False)
    # the depot and its platform
    dx0, dx1, dz0, dz1 = 50.0, 130.0, -170.0, -148.0
    s.reserve(rect(dx0, dx1, dz0, dz1))
    building(b, (dx0, dx1, dz0, dz1), 0.0, 12.0, "#8a6a4a", roof_colour="#3a3a3a",
             floor_colour="#8a7a64",
             doors={"z+": [(84.0, 96.0, 10.0)], "x-": [(-164.0, -154.0, 10.0)]},
             windows={"z+": [(56.0, 74.0, 3.4, 8.4), (106.0, 124.0, 3.4, 8.4)]},
             boards=True, eave=1.5)
    threshold(b, (dx0, dx1, dz0, dz1), "z+", (84.0, 96.0))
    threshold(b, (dx0, dx1, dz0, dz1), "x-", (-164.0, -154.0))
    face_sign(b, 90.0, 9.4, dz1 + 0.35, 22.0, 2.6,
              sign_decal("HARROW STATION", "#2a2a2a", "#f2e2a8", 22 / 2.6),
              "z+", "#2a2a2a")
    supply_ammo(b, 120.0, FLOOR, -160.0, "x-")
    slab(b, rect(30.0, 160.0, -190.0, -174.0), 3.0, 3.0, CONCRETE)
    for x0, near, far in ((30.0, 18.0, 30.0), (160.0, 172.0, 160.0)):
        flight(b, "x", near, far, -190.0, -180.0, 0.0, 3.0, CONCRETE_DARK, fill=0.0)
    b.box([95.0, 3.1, -189.4], [130.0, 0.2, 1.2], HAZARD, collide=False)
    for x in (60.0, 130.0):
        b.box([x, 3.0 + 4.6, -178.0], [1.0, 9.2, 1.0], STEEL_DARK)
        slab(b, rect(x - 10.0, x + 10.0, -186.0, -176.0), 13.0, 0.8, "#3a3a3a")
    for x in (44.0, 146.0):
        bench(b, x, -184.0, "x", y=3.0)
    barrel_spot(b, 0.0, 0.0, -170.0)
    barrel_spot(b, -90.0, 0.0, -212.0)
    barrel_spot(b, 160.0, 0.0, -240.0)
    # the grain silos and their loading shed
    for i, x in enumerate((-252.0, -228.0, -204.0)):
        b.cyl([x, 24.0, -170.0], [20.0, 48.0, 20.0], "#c8c4b8", material="metal")
        b.cone([x, 51.0, -170.0], [20.0, 6.0, 20.0], "#a8a498", material="metal",
               collide=False)
    b.box([-228.0, 55.2, -170.0], [56.0, 3.0, 4.0], STEEL_DARK, collide=False)
    building(b, (-262.0, -194.0, -158.0, -146.0), 0.0, 9.0, "#6a5a4a",
             roof_colour="#3a3a3a", roof_t=0.8, floor_colour="#6a6258",
             doors={"z+": [(-232.0, -224.0, 7.4)]}, lights=WARM)
    threshold(b, (-262.0, -194.0, -158.0, -146.0), "z+", (-232.0, -224.0))
    # the water tower
    for dx in (-8.0, 8.0):
        for dz in (-8.0, 8.0):
            b.cyl([220.0 + dx, 19.0, -255.0 + dz], [1.6, 38.0, 1.6], STEEL_DARK,
                  material="metal")
    b.cyl([220.0, 46.0, -255.0], [24.0, 16.0, 24.0], "#8a9aa8",
          material="metal", collide=False)
    b.cone([220.0, 57.0, -255.0], [26.0, 6.0, 26.0], "#6a7a88",
           material="metal", collide=False)
    face_sign(b, 220.0, 46.0, -242.6, 10.0, 4.0,
              sign_decal("HARROW", "#8a9aa8", "#1f2a3a", 4.0), "z+", "#8a9aa8")
    for x in (-150.0, -10.0, 60.0, 250.0):
        lamp_post(b, x, -214.0, 18.0, y=0.0)


# ================================================================ ends
def _ends(b: Area, s: Surfaces, rng: random.Random) -> None:
    """Both ends of Main Street are blocked: the bus at the east end, an
    army barricade at the west."""
    bus(b, 252.0, 0.0, "z", "#e0a62a", 30.0, "HARROW SCHOOLS")
    car(b, 236.0, -8.0, "x", "#6a2a2a", wrecked=True, y=0.3)
    car(b, 238.0, 9.0, "x", "#2a4a6a", y=0.3)
    for z in (-10.0, 10.0):
        sandbags(b, -246.0, z, 12.0, "z", 4.4)
    barrier(b, -232.0, 0.0, 16.0, "z")
    b.box([-240.0, 6.0, 0.0], [1.0, 12.0, 1.0], STEEL_DARK)
    face_sign(b, -239.15, 9.0, 0.0, 12.0, 4.0,
              sign_decal("ROAD CLOSED", "#f2f2f2", "#c42b20", 3.0), "x+", "#f2f2f2")
    for x, z in ((-150.0, 6.0), (60.0, -8.0)):
        car(b, x, z, "x", rng.choice(["#4a5a6a", "#8a6a3a", "#5a2a2a"]), y=0.3)
    car(b, -40.0, -6.0, "x", "#2a2a2a", wrecked=True, y=0.3)
    barrier(b, 150.0, 7.0, 14.0, "x")
    barrier(b, -84.0, -8.0, 14.0, "x")


def _woods(b: Area, rng: random.Random) -> None:
    """The tree line round the edge of town: the dark the infected come out
    of, and cover for whoever is waiting for them."""
    H = HALF
    treeline(b, -H + 12, 266.0, H - 12, 266.0, 26, rng, 1.6)
    treeline(b, -H + 12, 246.0, 100.0, 246.0, 14, rng, 1.2, kinds="mixed")
    treeline(b, -H + 10, -264.0, H - 30, -264.0, 22, rng, 1.5,
             avoid=[rect(196.0, 244.0, -280.0, -230.0)])
    treeline(b, H - 10, -150.0, H - 10, -40.0, 5, rng, 1.4)


def _zombie_spawns(b: Area) -> None:
    H = HALF
    pts = [
        # the woods north of the houses
        (-240, 254), (-170, 254), (-100, 254), (-30, 254), (40, 254), (90, 254),
        (180, 274), (250, 274),
        # the ends of the back alley and the gaps between the houses
        (-270, 106), (270, 106), (-140, 132), (100, 132),
        # behind the school and the gym
        (140, 238), (260, 238),
        # the graveyard: they come up out of the ground
        (-258, -60), (-244, -80), (-258, -98), (-236, -116),
        # the rail yard's far side, and along the tracks
        (-230, -270), (-150, -270), (-60, -270), (30, -270), (120, -270),
        (200, -270), (-270, -212), (270, -212),
        # behind the silos and the water tower
        (-266, -186), (262, -246),
        # both ends of Main Street, beyond the barricades
        (270, -14), (270, 14), (-266, -14), (-266, 14),
        # behind the gas station and the mini-mart
        (256, -110), (230, -126),
        # the west end of Maple, east end of Maple
        (-272, 155), (272, 155),
    ]
    for x, z in pts:
        tag = "grave" if x < -230 and -120 < z < -50 else ""
        b.zombie_spawn(float(x), float(z), tag)
