"""Blackwater Docks -- the harbour at night, and the fog off the water.

Layout (north is +z; everything south of the quay is harbour)::

      z +280  -------------------------- boundary ---------------------------
              FISH MARKET          | Wharf  |  THE RUSTY ANCHOR   TANK FARM
      z +130  ======================= Wharf Road ===========================
              BOATYARD         HARBOURMASTER'S OFFICE           (lot)
      z  +40  .......... the container yard: stacks, aisles, the gantry ......
              WAREHOUSE ONE      containers        containers     WAREHOUSE TWO
      z -140  ====== the quay: bollards, the gangway ==========================
              pier + shack     THE BLACKWATER STAR (moored)       breakwater
              boats                                               + LIGHTHOUSE
      z -280  ~~~~~~~~~~~~~~~~~~~~~~~~~~ harbour water ~~~~~~~~~~~~~~~~~~~~~~~~

The harbourmaster's office is the safe room: everybody deploys on its ground
floor, and its upstairs room opens onto a balcony over the container yard.

The water is real water: four units of it over the harbour bed, deep enough
to slow you and shallow enough to wade.  Fall in and the stairs and the boat
ramp in the quay wall bring you out.  The infected come out of it too.

The ship is the high ground.  One gangway from the quay, a cargo ladder on
the far side the infected come up out of the water by, containers on deck
to fight across, and the bridge on top -- where the horn is.  Sounding it
pulls every infected at the docks to the quay below.
"""
from __future__ import annotations

import math
import random

from .kit import (
    ASPHALT, CONCRETE, CONCRETE_DARK, CONCRETE_LIGHT, CONTAINER_COLOURS,
    CONTAINER_H, COLD, FLOOR, GLASS, HAZARD, LAMP, LINE_WHITE, PAVEMENT,
    PAVEMENT_DARK, RUST, SANDBAG, STEEL, STEEL_DARK, WARM, WOOD, WOOD_DARK,
    WOOD_LIGHT, Area, Surfaces, barrel_spot, barrier, boat, bollard, boundary,
    building, car, chain_fence, container, crate, deploy_pad, dumpster,
    flight, flood, gable, hesco, holed_wall, lamp_post, pallet_stack, rect,
    room_walls, sandbags, sign_decal, slab, strip_light, supply_ammo,
    supply_med, threshold, treeline, van, wall_sign)

HALF = 280.0
QUAY = -140.0              # the quay edge: land north of it, water south
BED = -4.0                 # the harbour bed
SURFACE = -1.0             # the water's surface
YARD = "#585d63"
SKY = {"top": "#0a111d", "horizon": "#2c3c4a", "sun": [0.45, 0.45, -0.62],
       "clouds": 0.42, "tint": "#a0b4cc"}
AMBIENT = "#4a586a"

SHIP = (-20.0, 180.0, -190.0, -146.0)
DECK_Y = 12.0
OFFICE = (-40.0, 40.0, 64.0, 110.0)
WHARF = (130.0, 146.0)


def build(b: Area) -> None:
    rng = random.Random(0xD0C5)
    _ground(b)
    boundary(b, 26.0, "#222c36", "#1a2229", rng, horizon="fog")
    s = Surfaces(b)
    s.reserve(rect(-HALF - 20, HALF + 20, -HALF - 20, QUAY))
    _quay(b, s, rng)
    _ship(b, s, rng)
    _pier(b, rng)
    _breakwater(b, rng)
    _container_yard(b, s, rng)
    _warehouses(b, s, rng)
    _office(b, s)
    _north(b, s, rng)
    _boatyard(b, s, rng)
    _loading(b, s, rng)
    _cannery(b, s, rng)
    _zombie_spawns(b)
    for x, z, name in ((0, 87, "the harbourmaster's office"), (80, -168, "the ship"),
                       (158, -170, "the bridge"), (-188, -200, "the pier"),
                       (238, -240, "the lighthouse"), (0, -40, "the container yard"),
                       (-206, -60, "warehouse one"), (206, -60, "warehouse two"),
                       (-150, 186, "the fish market"), (85, 185, "the Rusty Anchor"),
                       (210, 210, "the tank farm"), (-206, 60, "the boatyard"),
                       (52, -30, "the gantry crane")):
        b.landmark(float(x), float(z), name)


# ================================================================ ground
def _ground(b: Area) -> None:
    h = b.half + b.margin
    slab(b, rect(-h, h, QUAY, h), 0.0, 6.0, YARD, studs=True)
    slab(b, rect(-h, h, -h, QUAY), BED, 2.0, "#24302f", studs=True)
    b.water(0.0, (QUAY - b.half) / 2.0, 2 * b.half, b.half + QUAY, SURFACE,
            "#1f4a5a")


def _quay(b: Area, s: Surfaces, rng: random.Random) -> None:
    # stairs and a boat ramp up out of the water, set into the quay wall
    for x0, x1 in ((-112.0, -102.0), (198.0, 208.0), (-252.0, -242.0)):
        flight(b, "z", QUAY - 12.0, QUAY, x0, x1, BED, 0.0, CONCRETE_DARK,
               fill=BED, rise=2.0)
    flight(b, "z", QUAY - 34.0, QUAY, -150.0, -130.0, BED, 0.0, CONCRETE,
           fill=BED, rise=0.8)
    # bollards and a hazard edge along the quay, broken where you get on
    # and off the water and the ship
    gaps = [(-112.0, -102.0), (-150.0, -130.0), (198.0, 208.0), (-252.0, -242.0),
            (38.0, 52.0), (-204.0, -172.0), (222.0, 254.0)]
    x = -270.0
    while x < 270.0:
        if not any(a - 3.0 < x < c + 3.0 for a, c in gaps):
            bollard(b, x, QUAY + 2.0)
        x += 22.0
    lay = rect(-HALF, HALF, QUAY, QUAY + 4.0)
    b.box([0.0, 0.03, QUAY + 0.6], [2 * HALF, 0.06, 1.2], HAZARD, collide=False)
    s.reserve(lay)
    # quay cranes: two tall rail-mounted cranes over the ship's berth
    for cx in (20.0, 120.0):
        for dz in (-128.0, -108.0):
            b.box([cx - 8.0, 16.0, dz], [2.4, 32.0, 2.4], "#c8862a", material="metal")
            b.box([cx + 8.0, 16.0, dz], [2.4, 32.0, 2.4], "#c8862a", material="metal")
        slab(b, rect(cx - 10.0, cx + 10.0, -130.0, -106.0), 34.0, 2.0, "#c8862a")
        b.box([cx, 34.6, -160.0], [4.0, 1.2, 60.0], "#b8762a", material="metal",
              collide=False)
        b.box([cx, 32.0, -150.0], [5.0, 4.0, 5.0], "#24323c", collide=False)
        flood(b, cx + 9.0, -129.0, 34.0, 3.0, COLD)
    for x, z in ((-60.0, -124.0), (90.0, -122.0), (150.0, -124.0)):
        pallet_stack(b, x, z, 3)
    for x, z in ((-80.0, -126.0), (170.0, -122.0)):
        crate(b, x, 0.0, z, 6.0, WOOD)
    barrel_spot(b, -30.0, 0.0, -124.0)
    barrel_spot(b, 110.0, 0.0, -126.0)
    barrel_spot(b, 190.0, 0.0, -130.0)
    for i in range(7):
        lamp_post(b, -240.0 + i * 80.0, QUAY + 8.0, 16.0)


# ================================================================== ship
def _ship(b: Area, s: Surfaces, rng: random.Random) -> None:
    x0, x1, z0, z1 = SHIP
    # the hull: rust red below the waterline, black above, a stepped bow
    slab(b, rect(x0, x1, z0, z1), 3.0, 3.0 - BED, "#7a2a24")
    slab(b, rect(x0, x1, z0, z1), DECK_Y, DECK_Y - 3.0, "#1f2226", studs=True)
    for (a, c, za, zc) in ((x0 - 16.0, x0, z0 + 8.0, z1 - 8.0),
                           (x0 - 28.0, x0 - 16.0, z0 + 14.0, z1 - 14.0)):
        slab(b, rect(a, c, za, zc), 3.0, 3.0 - BED, "#7a2a24")
        slab(b, rect(a, c, za, zc), DECK_Y, DECK_Y - 3.0, "#1f2226", studs=True)
    b.box([x0 + 60.0, 8.0, z1 + 0.06], [60.0, 3.0, 0.12], "#d8d0c0",
          collide=False,
          decal=sign_decal("BLACKWATER STAR", "#1f2226", "#d8d0c0", 20.0))
    # rails round the deck, open at the gangway, the ladder and the bow
    room_walls(b, rect(x0, x1, z0, z1), 1.0, DECK_Y, DECK_Y + 2.6, "#c8c4b8",
               doors={"z+": [(40.0, 50.0, DECK_Y + 2.6)],
                      "z-": [(100.0, 108.0, DECK_Y + 2.6)],
                      "x-": [(z0 + 8.0, z1 - 8.0, DECK_Y + 2.6)]})
    # the gangway down to the quay, and the cargo ladder up out of the water
    flight(b, "z", -116.0, z1, 40.0, 50.0, 0.0, DECK_Y, "#8a8478", fill=BED,
           rise=2.0)
    flight(b, "z", z0 - 16.0, z0, 100.0, 108.0, BED, DECK_Y, "#4a5057",
           fill=BED, rise=2.0)
    # containers on deck: three rows, some stacked, with aisles between
    for i, cx in enumerate((4.0, 34.0, 64.0, 94.0)):
        for k, cz in enumerate((z0 + 6.3, z0 + 22.0, z1 - 6.3)):
            if (i + k) % 3 == 1:
                continue
            colour = CONTAINER_COLOURS[(i * 3 + k) % len(CONTAINER_COLOURS)]
            container(b, cx, DECK_Y, cz, "x", colour)
            if (i * 7 + k) % 4 == 0:
                container(b, cx, DECK_Y + CONTAINER_H, cz, "x",
                          CONTAINER_COLOURS[(i + k + 3) % len(CONTAINER_COLOURS)])
    # the superstructure: crew deck, and the bridge on top of it
    sx0, sx1, sz0, sz1 = 140.0, 174.0, z0 + 6.0, z1 - 12.0
    crew = rect(sx0, sx1, sz0, sz1)
    building(b, crew, DECK_Y, 10.0, "#e8e4d8", roof_colour="#c8c4b8",
             floor_colour="#8a8478", doors={"z+": [(150.0, 160.0, DECK_Y + 8.4)]},
             windows={"x+": [(sz0 + 6.0, sz1 - 6.0, DECK_Y + 4.0, DECK_Y + 8.0)]},
             glass=True, parapet=2.4, parapet_gaps={"x-": [(sz0 + 2.0, sz0 + 10.0)]},
             lights=WARM)
    threshold(b, crew, "z+", (150.0, 160.0), y0=DECK_Y)
    crew_roof = DECK_Y + 10.0 + 1.2
    flight(b, "z", sz1 + 4.0, sz0 + 6.0, sx0 - 8.0, sx0, DECK_Y, crew_roof,
           "#8a8478", fill=DECK_Y, rise=1.9)
    b.box([158.0, DECK_Y + FLOOR + 1.5, sz0 + 12.0], [16.0, 3.0, 6.0], WOOD,
          studs=True)
    supply_ammo(b, 168.0, DECK_Y + FLOOR, sz1 - 4.0, "x-")
    supply_med(b, 145.0, DECK_Y + FLOOR, sz0 + 3.0, "z+")
    bridge = rect(146.0, 172.0, sz0 + 2.0, sz0 + 20.0)
    building(b, bridge, crew_roof, 8.0, "#e8e4d8", roof_colour="#c8c4b8",
             floor_colour="#6a6458", doors={"x-": [(sz0 + 4.0, sz0 + 10.0, crew_roof + 7.0)]},
             windows={"x+": [(sz0 + 4.0, sz0 + 18.0, crew_roof + 3.0, crew_roof + 6.6)],
                      "z+": [(148.0, 170.0, crew_roof + 3.0, crew_roof + 6.6)],
                      "z-": [(148.0, 170.0, crew_roof + 3.0, crew_roof + 6.6)]},
             glass=True, lights=COLD)
    threshold(b, bridge, "x-", (sz0 + 4.0, sz0 + 10.0), y0=crew_roof)
    b.box([166.0, crew_roof + FLOOR + 2.0, sz0 + 11.0], [4.0, 4.0, 10.0], "#3a3f46",
          studs=True)
    b.set_lure(160.0, crew_roof + FLOOR, sz0 + 11.0, "the ship's horn",
               "Sound the horn", "horn", (45.0, 0.0, -124.0))
    top = crew_roof + 8.0 + 1.2
    b.cyl([150.0, top + 3.0, sz0 + 6.0], [2.0, 6.0, 2.0], "#c8c4b8",
          material="metal")
    b.cyl([150.0, top + 6.6, sz0 + 6.0], [3.2, 1.2, 3.2], "#c42b20",
          material="metal")
    b.box([166.0, top + 0.5, sz0 + 12.0], [1.0, 1.0, 1.0], "#ff3a2a",
          material="neon")
    # the funnel and the masts
    b.box([162.0, crew_roof + 6.0, sz1 - 3.6], [8.0, 12.0, 4.0], "#1f2226")
    b.box([162.0, crew_roof + 9.0, sz1 - 3.6], [8.2, 2.0, 4.2], "#c42b20",
          collide=False)
    for mx in (0.0, 120.0):
        b.box([mx, DECK_Y + 13.0, (z0 + z1) / 2.0], [1.6, 26.0, 1.6], "#c8c4b8")
        b.box([mx, DECK_Y + 24.0, (z0 + z1) / 2.0], [1.0, 1.0, 20.0], "#c8c4b8",
              collide=False)
    barrel_spot(b, 20.0, DECK_Y, (z0 + z1) / 2.0)
    barrel_spot(b, 120.0, DECK_Y, z0 + 4.0)
    for x in (-30.0, 80.0):
        lamp_post(b, x, z1 - 3.0, 8.0, y=DECK_Y)


# ================================================================== pier
def _pier(b: Area, rng: random.Random) -> None:
    x0, x1, z0, z1 = -204.0, -172.0, -262.0, QUAY
    slab(b, rect(x0, x1, z0, z1), 2.0, 1.0, WOOD_LIGHT, studs=True)
    for z in range(int(z0) + 6, int(z1), 14):
        for x in (x0 + 1.0, x1 - 1.0):
            b.cyl([x, (BED + 1.0) / 2.0, float(z)], [2.0, 1.0 - BED, 2.0], WOOD_DARK)
    for x in (x0 + 0.4, x1 - 0.4):
        b.box([x, 3.4, (z0 + QUAY - 20.0) / 2.0], [0.8, 2.8, QUAY - 20.0 - z0],
              WOOD)
    shack = rect(-198.0, -178.0, -258.0, -240.0)
    building(b, shack, 2.0, 9.0, "#6a7a72", roof_colour="#3a3a3a",
             floor_colour="#7a6a52", doors={"z+": [(-192.0, -184.0, 9.0)]},
             windows={"x-": [(-254.0, -246.0, 5.6, 8.6)]}, boards=True, lights=WARM)
    threshold(b, shack, "z+", (-192.0, -184.0), y0=2.0)
    supply_med(b, -194.0, 2.0 + FLOOR, -255.0, "z+")
    wall_sign(b, -188.0, 9.6, -239.65, 14.0, 2.0,
              sign_decal("BAIT & TACKLE", "#e8e2d0", "#2a4a6a", 7.0), "z+",
              "#e8e2d0")
    boat(b, -218.0, -206.0, "z", 32.0, "#d8d8d0")
    boat(b, -158.0, -226.0, "z", 26.0, "#2f6b8a")
    boat(b, -130.0, -186.0, "x", 24.0, "#c8a83a", cabin=False)
    for z in (-190.0, -230.0):
        lamp_post(b, x0 + 2.0, z, 10.0, y=2.0)


def _breakwater(b: Area, rng: random.Random) -> None:
    """A rock jetty out to the lighthouse, and the keeper's hut on it."""
    x0, x1, z0, z1 = 224.0, 252.0, -268.0, QUAY
    slab(b, rect(x0, x1, z0, z1), 2.0, 2.0 - BED, "#6a6e72", studs=True)
    for i, z in enumerate(range(int(z0) + 8, int(z1), 16)):
        for side in (-1, 1):
            r = rng.uniform(5.0, 8.0)
            b.sphere([(x0 + x1) / 2.0 + side * 15.0, 0.0, float(z)],
                     [r * 1.4, r, r * 1.4], "#5a5e62")
    hut = rect(228.0, 248.0, -232.0, -216.0)
    building(b, hut, 2.0, 9.0, "#e8e2d8", roof_colour="#8a2a24",
             floor_colour="#8a7a64", doors={"z+": [(234.0, 242.0, 9.0)]},
             windows={"x-": [(-228.0, -220.0, 5.4, 8.4)]}, glass=True, lights=WARM)
    threshold(b, hut, "z+", (234.0, 242.0), y0=2.0)
    gable(b, hut, 2.0 + 9.0 + 1.2, "#8a2a24", "z", 2, 1.4, 0.0)
    supply_med(b, 244.0, 2.0 + FLOOR, -228.0, "x-")
    lx, lz = 238.0, -252.0
    b.cyl([lx, 2.0 + 26.0, lz], [16.0, 52.0, 16.0], "#e8e4d8")
    for k in range(3):
        b.cyl([lx, 2.0 + 8.0 + k * 16.0, lz], [16.4, 4.0, 16.4], "#c42b20",
              collide=False)
    b.cyl([lx, 55.0, lz], [20.0, 2.0, 20.0], "#2a2d31", collide=False)
    b.cyl([lx, 60.0, lz], [10.0, 8.0, 10.0], "#fff2b0", material="neon",
          collide=False)
    b.cone([lx, 67.0, lz], [13.0, 6.0, 13.0], "#2a2d31", collide=False)


# ======================================================== container yard
def _container_yard(b: Area, s: Surfaces, rng: random.Random) -> None:
    s.lay(rect(-124.0, 124.0, -112.0, 48.0), 0.12, "#4f545a")
    xs = (-100.0, -62.0, -24.0, 14.0, 52.0, 90.0)
    zs = (-92.0, -60.0, -28.0, 4.0, 36.0)
    for i, cx in enumerate(xs):
        for k, cz in enumerate(zs):
            if (i, k) in ((2, 2), (3, 2), (2, 3)):
                continue                 # the square in the middle of the yard
            height = rng.choice((1, 1, 2, 2, 2, 3))
            for half in (-1, 1):
                if (i + k + half) % 5 == 0:
                    continue
                for level in range(height if half > 0 else max(1, height - 1)):
                    container(b, cx, 0.12 + level * CONTAINER_H, cz + half * 4.35,
                              "x", rng.choice(CONTAINER_COLOURS))
    # the gantry crane straddling the east columns
    for gx in (33.0, 71.0):
        for gz in (-110.0, 48.0):
            b.box([gx, 18.0, gz], [2.4, 36.0, 2.4], "#2f6b8a", material="metal")
        b.box([gx, 37.0, -31.0], [2.0, 2.0, 160.0], "#2f6b8a", material="metal",
              collide=False)
    for gz in (-110.0, 48.0):
        b.box([52.0, 39.0, gz], [40.0, 2.0, 2.0], "#2f6b8a", material="metal",
              collide=False)
    b.box([52.0, 33.6, -20.0], [10.0, 4.8, 8.0], "#24323c", collide=False)
    b.box([52.0, 34.9, -20.0], [36.0, 1.2, 2.0], "#2f6b8a", material="metal",
          collide=False)
    # cover in the middle square, and the yard's barrels
    for x, z in ((-12.0, -34.0), (6.0, -22.0), (-4.0, 6.0)):
        pallet_stack(b, x, z, 2)
    crate(b, -24.0, 0.12, 0.0, 6.0, WOOD)
    for x, z in ((-43.0, -44.0), (33.0, 20.0), (-81.0, -12.0), (71.0, -76.0)):
        barrel_spot(b, x, 0.12, z)
    for x in (-110.0, 110.0):
        for z in (-60.0, 20.0):
            flood(b, x, z, 0.12, 22.0)


# ============================================================ warehouses
def _warehouse(b: Area, s: Surfaces, area, doors, name: str, mezz_side: int,
               rng: random.Random) -> None:
    x0, x1, z0, z1 = area
    s.reserve(rect(x0, x1, z0, z1))
    building(b, area, 0.0, 22.0, "#7a6a58", roof_colour="#4a4a4a",
             floor_colour="#6a6a64", doors=doors,
             windows={"z+": [(x0 + 10.0, x0 + 30.0, 14.0, 19.0),
                             (x1 - 30.0, x1 - 10.0, 14.0, 19.0)]},
             glass=True, lights=LAMP)
    for side, spans in doors.items():
        for a, c, _head in spans:
            threshold(b, area, side, (a, c))
    wall_sign(b, (x0 + x1) / 2.0, 19.0, z0 - 0.35, 30.0, 3.0,
              sign_decal(name, "#7a6a58", "#f2e2a8", 10.0), "z-", "#7a6a58")
    # the mezzanine down one long wall, and its stair
    mx0, mx1 = (x0 + 2.0, x0 + 20.0) if mezz_side < 0 else (x1 - 20.0, x1 - 2.0)
    slab(b, rect(mx0, mx1, z0 + 2.0, z1 - 2.0), 12.0, 1.2, STEEL_DARK, studs=True)
    edge = mx1 if mezz_side < 0 else mx0
    sx0, sx1 = (edge, edge + 8.0) if mezz_side < 0 else (edge - 8.0, edge)
    flight(b, "z", z1 - 16.0, z1 - 46.0, sx0, sx1, FLOOR, 12.0, STEEL, fill=FLOOR)
    rail_x = edge + (0.5 if mezz_side < 0 else -0.5)
    b.box([rail_x, 13.6, (z0 + z1 - 48.0) / 2.0 + 1.0], [1.0, 3.2, z1 - z0 - 48.0 - 2.0],
          STEEL, material="metal")
    for z in (z0 + 8.0, z0 + 40.0, z1 - 20.0):
        b.box([(mx0 + mx1) / 2.0, (FLOOR + 10.8) / 2.0, z], [2.0, 10.8 - FLOOR, 2.0],
              STEEL_DARK)
    # racks of pallets on the floor
    for i in range(3):
        rx = (x0 + x1) / 2.0 + (i - 1) * 22.0 + (8.0 if mezz_side < 0 else -8.0)
        b.box([rx, FLOOR + 5.0, (z0 + z1) / 2.0 - 6.0], [6.0, 10.0, 36.0], "#a8642a")
        for level in range(2):
            b.box([rx, FLOOR + 2.0 + level * 5.0, (z0 + z1) / 2.0 - 6.0],
                  [6.4, 3.2, 34.0], rng.choice(["#c8b89a", "#8a7a5a", "#5a7a8a"]))
    # a forklift
    fx = (x0 + x1) / 2.0
    b.box([fx, FLOOR + 2.0, z1 - 14.0], [6.0, 4.0, 9.0], "#d8a83a", material="metal")
    b.box([fx, FLOOR + 6.0, z1 - 12.0], [5.0, 4.0, 4.0], "#24323c")
    b.box([fx, FLOOR + 3.5, z1 - 20.4], [4.0, 7.0, 0.6], STEEL_DARK)


def _warehouses(b: Area, s: Surfaces, rng: random.Random) -> None:
    _warehouse(b, s, (-262.0, -150.0, -110.0, -12.0),
               {"z-": [(-230.0, -206.0, 16.0)], "x+": [(-70.0, -56.0, 12.0)],
                "z+": [(-200.0, -188.0, 12.0)]}, "BLACKWATER COLD STORE", -1, rng)
    supply_ammo(b, -246.0, 12.0, -100.0, "z+")
    _warehouse(b, s, (150.0, 262.0, -110.0, -12.0),
               {"z-": [(176.0, 200.0, 16.0)], "x-": [(-70.0, -56.0, 12.0)],
                "z+": [(210.0, 222.0, 12.0)]}, "HARROW FREIGHT CO", 1, rng)
    supply_med(b, 252.0, 12.0, -100.0, "z+")


# ================================================================ office
def _office(b: Area, s: Surfaces) -> None:
    x0, x1, z0, z1 = OFFICE
    s.reserve(rect(x0, x1, z0, z1))
    stair = rect(8.0, 36.0, 98.0, 106.0)
    ground_roof = 12.0 + 1.2
    building(b, OFFICE, 0.0, 12.0, "#5a6a7a", roof_colour="#3a4652",
             floor_colour="#8a8478",
             doors={"z-": [(-8.0, 8.0, 10.0)], "x-": [(76.0, 86.0, 10.0)],
                    "x+": [(76.0, 86.0, 10.0)], "z+": [(-30.0, -20.0, 10.0)]},
             windows={"z-": [(-36.0, -16.0, 3.6, 8.6), (16.0, 36.0, 3.6, 8.6)]},
             boards=True, roof_holes=[stair], lights=LAMP)
    for side, span in (("z-", (-8.0, 8.0)), ("x-", (76.0, 86.0)),
                       ("x+", (76.0, 86.0)), ("z+", (-30.0, -20.0))):
        threshold(b, OFFICE, side, span)
    flight(b, "x", stair[0], stair[1], stair[2], stair[3], FLOOR, ground_roof,
           CONCRETE_DARK, fill=FLOOR, rise=1.9)
    # the deploy pads
    for row, z in enumerate((70.0, 79.0)):
        for x in (-34.0, -25.0, -16.0, -8.0, 8.0, 16.0, 25.0, 34.0):
            deploy_pad(b, x, z, FLOOR, "#4fa3a6", 5.0)
            b.safe_spawn(x, FLOOR + 0.6, z, math.pi)
    b.box([-20.0, FLOOR + 2.0, 94.0], [20.0, 4.0, 4.0], WOOD_DARK, studs=True)
    supply_ammo(b, -35.0, FLOOR, 104.0, "x+")
    supply_med(b, 36.4, FLOOR, 90.0, "x-")
    wall_sign(b, 0.0, 11.0, z0 - 0.35, 30.0, 1.6,
              sign_decal("HARBOURMASTER", "#5a6a7a", "#f2f2f2", 30 / 1.6), "z-",
              "#5a6a7a")
    # upstairs: a room set back from the front, so the ground floor's roof
    # in front of it is a balcony over the yard
    up = rect(x0, x1, 76.0, z1)
    building(b, up, ground_roof, 10.0, "#6a7a8a", roof_colour="#3a4652",
             floor_colour="", doors={"z-": [(-10.0, 10.0, ground_roof + 8.0)]},
             windows={"z-": [(-36.0, -14.0, ground_roof + 3.0, ground_roof + 8.0),
                             (14.0, 36.0, ground_roof + 3.0, ground_roof + 8.0)],
                      "x-": [(80.0, 104.0, ground_roof + 3.0, ground_roof + 8.0)],
                      "x+": [(80.0, 104.0, ground_roof + 3.0, ground_roof + 8.0)]},
             glass=True, lights=WARM, no_lights=[stair])
    room_walls(b, rect(x0, x1, z0, 76.0), 1.0, ground_roof, ground_roof + 3.0,
               "#5a6a7a", sides=("x-", "x+", "z-"))
    b.box([-30.0, ground_roof + 2.0, 100.0], [10.0, 4.0, 6.0], WOOD, studs=True)
    supply_ammo(b, 30.0, ground_roof, 86.0, "x-")
    for x in (-24.0, 24.0):
        sandbags(b, x, z0 + 4.0, 12.0, "x", 2.6, y=ground_roof)
    s.lay(rect(x0 - 10.0, x1 + 10.0, z1, WHARF[0]), 0.3, ASPHALT)
    for x in (-28.0, 28.0):
        car(b, x, 120.0, "x", "#3a4a5a" if x < 0 else "#6a5a3a", y=0.3)


# ================================================================= north
def _north(b: Area, s: Surfaces, rng: random.Random) -> None:
    H = HALF
    s.lay(rect(-H, H, WHARF[0], WHARF[1]), 0.3, ASPHALT)
    s.lay(rect(-H, H, WHARF[1], WHARF[1] + 6.0), 0.6, PAVEMENT_DARK)
    for i in range(18):
        x = -H + 16.0 + i * (2 * H - 32.0) / 17.0
        b.box([x, 0.34, (WHARF[0] + WHARF[1]) / 2.0], [8.0, 0.08, 0.6], LINE_WHITE,
              collide=False)
    for i in range(7):
        lamp_post(b, -240.0 + i * 80.0, WHARF[1] + 3.0, 16.0, arm="z-", y=0.6)
    # the fish market: two open sheds of stalls
    for sx0 in (-214.0, -148.0):
        area = rect(sx0, sx0 + 56.0, 158.0, 214.0)
        s.reserve(area)
        for x in (sx0 + 1.0, sx0 + 55.0):
            for z in (159.0, 186.0, 213.0):
                b.box([x, 6.0, z], [2.0, 12.0, 2.0], "#5a6a72")
        slab(b, area, 13.2, 1.2, "#3a6a8a")
        gable(b, area, 13.2, "#3a6a8a", "x", 2, 1.4, 0.0)
        for k in range(3):
            for z in (170.0, 202.0):
                b.box([sx0 + 12.0 + k * 16.0, 2.0, z], [10.0, 4.0, 5.0],
                      rng.choice(["#c8c4b8", "#8a9aa8", "#d8d0c0"]), studs=True)
        strip_light(b, sx0 + 28.0, 186.0, 12.0, 40.0, "x", COLD)
    supply_ammo(b, -152.0, 0.0, 210.0, "z-")
    wall_sign(b, -152.0, 18.0, 157.65, 30.0, 3.2,
              sign_decal("BLACKWATER FISH MARKET", "#3a6a8a", "#ffffff", 9.4),
              "z-", "#3a6a8a")
    b.box([-152.0, 15.0, 157.65], [1.0, 3.0, 0.7], "#3a6a8a")
    # the bar
    area = (50.0, 122.0, 160.0, 212.0)
    s.reserve(rect(*area))
    building(b, area, 0.0, 13.0, "#5a3a2a", roof_colour="#2a2420",
             floor_colour="#6a4a32", doors={"z-": [(78.0, 90.0, 10.0)],
                                             "x+": [(194.0, 204.0, 10.0)]},
             windows={"z-": [(56.0, 72.0, 3.6, 8.6), (96.0, 116.0, 3.6, 8.6)]},
             glass=True, lights=WARM)
    threshold(b, area, "z-", (78.0, 90.0))
    threshold(b, area, "x+", (194.0, 204.0))
    wall_sign(b, 86.0, 15.6, 159.65, 28.0, 4.0,
              sign_decal("THE RUSTY ANCHOR", "#1b1b1b", "#ff9a3a", 7.0), "z-",
              "#1b1b1b")
    b.box([86.0, FLOOR + 2.2, 204.0], [40.0, 4.4, 3.0], WOOD_DARK, studs=True)
    for x in (66.0, 106.0):
        b.box([x, FLOOR + 2.0, 180.0], [9.0, 4.0, 5.0], "#2f6b3a", studs=True)
    supply_ammo(b, 118.0, FLOOR, 168.0, "x-")
    for x in (40.0, 136.0):
        dumpster(b, x, 220.0, "z")
    # the tank farm, behind its own fence
    chain_fence(b, 160.0, 156.0, 262.0, 156.0, 10.0)
    chain_fence(b, 160.0, 156.0, 160.0, 230.0, 10.0)
    for x, z in ((186.0, 190.0), (232.0, 190.0), (210.0, 244.0)):
        b.cyl([x, 11.0, z], [30.0, 22.0, 30.0], "#c8c4b8", material="metal")
        b.cyl([x, 22.6, z], [28.0, 1.2, 28.0], "#a8a498", material="metal",
              collide=False)
    for x in (174.0, 250.0):
        b.box([x, 9.0, 172.0], [2.0, 18.0, 2.0], STEEL_DARK)
    b.box([212.0, 18.6, 172.0], [80.0, 1.2, 3.0], STEEL, material="metal",
          collide=False)
    barrel_spot(b, 170.0, 0.0, 168.0)
    barrel_spot(b, 252.0, 0.0, 168.0)
    # rigs parked on the road
    for x, z, c in ((-40.0, 138.0, "#8a3a2a"), (150.0, 138.0, "#2f5f8a")):
        van(b, x, z, "x", c, "", 22.0, y=0.3)
    car(b, 20.0, 134.0, "x", "#2a2a2a", wrecked=True, y=0.3)
    barrier(b, -110.0, 138.0, 14.0, "x")
    treeline(b, -H + 10.0, 266.0, H - 10.0, 266.0, 20, rng, 1.3, leaf="#1f3a2a",
             avoid=[rect(160.0, 262.0, 156.0, 262.0)])


def _boatyard(b: Area, s: Surfaces, rng: random.Random) -> None:
    s.lay(rect(-262.0, -140.0, 4.0, 118.0), 0.15, "#6a6658")
    # boats up on cradles
    for x, z, c in ((-236.0, 40.0, "#d8d8d0"), (-186.0, 30.0, "#2f6b8a"),
                    (-210.0, 90.0, "#c8a83a")):
        for dx in (-8.0, 8.0):
            b.box([x + dx, 1.8, z], [2.0, 3.3, 8.0], WOOD_DARK)
        boat(b, x, z, "x", 28.0, c, deck=9.0, base=3.45)
    # the travel lift: two arches you can walk under
    for z in (60.0, 80.0):
        for x in (-160.0, -144.0):
            b.box([x, 11.0, z], [2.0, 22.0, 2.0], "#2f6b8a", material="metal")
    slab(b, rect(-162.0, -142.0, 58.0, 82.0), 23.2, 1.2, "#2f6b8a")
    chain_fence(b, -262.0, 118.0, -170.0, 118.0, 9.0)
    for x, z in ((-250.0, 110.0), (-170.0, 10.0)):
        barrel_spot(b, x, 0.15, z)
    supply_ammo(b, -246.0, 0.15, 12.0, "z+")
    crate(b, -180.0, 0.15, 104.0, 6.0, WOOD)


def _trailer(b: Area, x: float, z: float, colour: str) -> None:
    """A container on a road trailer, its tractor unit still coupled."""
    b.box([x, 1.6, z], [28.0, 1.2, 6.0], "#2a2d31")
    for k in (-10.0, 8.0, 11.0):
        for side in (-1, 1):
            b.cyl([x + k, 1.3, z + side * 3.4], [2.6, 0.9, 2.6], "#1b1d20",
                  r=[math.pi / 2.0, 0, 0], collide=False)
    container(b, x - 1.0, 2.2, z, "x", colour)
    b.box([x + 16.5, 4.5, z], [7.0, 6.8, 7.0], "#c8c4b8", material="metal")
    b.box([x + 18.0, 6.6, z], [3.6, 2.2, 6.0], "#24323c")
    b.box([x + 14.2, 9.2, z + 2.0], [0.8, 3.0, 0.8], STEEL_DARK)


def _loading(b: Area, s: Surfaces, rng: random.Random) -> None:
    """Either side of the office: the truck bays to the west, customs to the
    east.  Both are cover across what would otherwise be open concrete."""
    s.lay(rect(-140.0, -46.0, 54.0, 124.0), 0.1, "#4f545a")
    for i, z in enumerate((64.0, 84.0, 104.0)):
        _trailer(b, -96.0, z, CONTAINER_COLOURS[(i * 3) % len(CONTAINER_COLOURS)])
        b.box([-96.0, 0.13, z - 9.0], [40.0, 0.06, 0.6], HAZARD, collide=False)
    hut = rect(-138.0, -122.0, 100.0, 118.0)
    building(b, hut, 0.1, 9.0, "#c8a83a", roof_colour="#3a3a3a",
             floor_colour="#6a6a64", doors={"x+": [(104.0, 112.0, 8.0)]},
             windows={"z-": [(-134.0, -126.0, 3.6, 7.4)]}, glass=True,
             lights=WARM)
    threshold(b, hut, "x+", (104.0, 112.0), y0=0.1)
    wall_sign(b, -130.0, 7.6, 99.65, 12.0, 1.8,
              sign_decal("WEIGH STATION", "#c8a83a", "#1b1b1b", 12 / 1.8), "z-",
              "#c8a83a")
    barrel_spot(b, -120.0, 0.1, 60.0)
    # customs: booths, barrier arms and the queue of what was waiting
    s.lay(rect(46.0, 140.0, 54.0, 124.0), 0.1, "#4f545a")
    for x in (70.0, 104.0):
        booth = rect(x - 5.0, x + 5.0, 84.0, 94.0)
        building(b, booth, 0.1, 8.0, "#e8e4d8", roof_colour="#c42b20",
                 floor_colour="#8a8478", doors={"z-": [(x - 2.5, x + 2.5, 7.0)]},
                 windows={"x-": [(86.0, 92.0, 3.4, 6.4)],
                          "x+": [(86.0, 92.0, 3.4, 6.4)]},
                 glass=True, lights=COLD, eave=1.5)
        threshold(b, booth, "z-", (x - 2.5, x + 2.5), y0=0.1)
        b.box([x + 9.0, 3.4, 89.0], [12.0, 0.6, 0.6], "#e8e8e8")
        b.box([x + 4.4, 1.75, 89.0], [0.8, 3.5, 0.8], "#c42b20")
    for i, x in enumerate((60.0, 88.0, 118.0)):
        van(b, x, 108.0, "z", ["#5a6a72", "#8a6a3a", "#d8d8d0"][i], "", 16.0,
            y=0.1, front=-1)
    sandbags(b, 87.0, 66.0, 18.0, "x", 3.6, y=0.1)
    supply_ammo(b, 132.0, 0.1, 66.0, "x-")
    wall_sign(b, 87.0, 12.0, 83.65, 20.0, 2.0,
              sign_decal("CUSTOMS", "#1f3a5a", "#f2f2f2", 10.0), "z-", "#1f3a5a")
    b.box([87.0, 10.4, 83.65], [1.0, 1.2, 0.7], "#1f3a5a")
    # crane rails under the gantry, and walkway paint through the yard
    for gx in (33.0, 71.0):
        b.box([gx, 0.18, -31.0], [1.2, 0.12, 156.0], "#6a6e72", collide=False)
    for z in (-110.5, 46.0):
        b.box([0.0, 0.17, z], [246.0, 0.1, 1.0], HAZARD, collide=False)


def _cannery(b: Area, s: Surfaces, rng: random.Random) -> None:
    """The cannery north of the road: a long hall you can run straight
    through, with the line of machines down the middle as cover."""
    area = (-78.0, 34.0, 168.0, 238.0)
    s.reserve(rect(*area))
    building(b, area, 0.0, 16.0, "#8a9a9a", roof_colour="#3a4a4a",
             floor_colour="#7a8a8a",
             doors={"z-": [(-30.0, -14.0, 12.0)], "z+": [(-30.0, -14.0, 12.0)],
                    "x-": [(196.0, 210.0, 12.0)], "x+": [(196.0, 210.0, 12.0)]},
             windows={"z-": [(-70.0, -44.0, 9.0, 13.0), (0.0, 26.0, 9.0, 13.0)]},
             glass=True, lights=COLD)
    for side, span in (("z-", (-30.0, -14.0)), ("z+", (-30.0, -14.0)),
                       ("x-", (196.0, 210.0)), ("x+", (196.0, 210.0))):
        threshold(b, area, side, span)
    wall_sign(b, -22.0, 14.2, 167.65, 34.0, 2.6,
              sign_decal("HARROW BAY CANNERY", "#8a9a9a", "#1f3a5a", 34 / 2.6),
              "z-", "#8a9a9a")
    # the canning line: a conveyor on legs with the machines along it
    b.box([-22.0, FLOOR + 3.0, 186.0], [80.0, 1.2, 4.0], STEEL, material="metal")
    for x in (-58.0, -40.0, -4.0, 14.0):
        b.box([x, FLOOR + 1.2, 186.0], [1.2, 2.4, 3.0], STEEL_DARK)
        b.box([x, FLOOR + 5.5, 186.0], [8.0, 3.8, 7.0], "#5a7a8a", material="metal")
    for x in (-58.0, 14.0):
        b.cyl([x, FLOOR + 5.0, 222.0], [10.0, 10.0, 10.0], "#a8b0b0",
              material="metal")
    for i in range(4):
        crate(b, -66.0 + i * 6.0, FLOOR, 230.0, 5.0, "#c8b89a")
    supply_ammo(b, 28.0, FLOOR, 222.0, "x-")
    barrel_spot(b, -72.0, FLOOR, 176.0)


def _zombie_spawns(b: Area) -> None:
    pts = [
        # out of the harbour
        (-80, -232), (-110, -262), (-40, -258), (40, -246), (130, -250),
        (200, -232), (-250, -270), (-150, -268), (204, -270),
        # the north edge and the tank farm
        (-250, 258), (-180, 262), (-100, 262), (-20, 262), (40, 262), (130, 262),
        (262, 248), (210, 268),
        # the west and east edges
        (-272, 150), (-272, 80), (-272, -60), (-272, -126), (272, 140), (272, 60),
        (272, -60), (272, -126),
        # behind the warehouses, the bar and the boatyard
        (-206, -2), (206, -2), (40, 236), (138, 236), (-250, 124),
    ]
    for x, z in pts:
        tag = "water" if z < QUAY else ""
        b.zombie_spawn(float(x), float(z), tag, y=BED if z < QUAY else None)
