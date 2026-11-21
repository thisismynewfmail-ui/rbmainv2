"""Substation Nine -- a downtown in the middle of a citywide blackout.

Night, rain, and no power anywhere but the substation itself, still arcing
inside its fences.  Both teams deploy out of its control house in the low
plaza in the middle of the city; from there the city climbs in terraces --
Market Street, the Heights, the tower plazas -- to an office tower at each
end, where the flags are kept in the lobby atriums.

Layout (red to the west; the map is its own mirror image about x = 0)::

      z +200  .............. the city's back walls, a water tower ..............
      z +126  NORTH STREET: bus shelters -- a stair at every terrace edge
      z  +80  N. TRANSFORMER YARD          LAUNDROMAT (outpost)
      z    0  CONTROL HOUSE --- THE AVENUE --- stairs --- TOWER PLAZA / LOBBY
      z  -80  S. TRANSFORMER YARD          DINER (outpost)
      z -125  SOUTH STREET: a city bus stalled broadside
      z -165  ===== LINE 9: open cut in the plaza, a tunnel under the terraces =====
              Civic Centre (the cut) ................... Terminal (behind each tower)

Elevations: the plaza is the ground (0), Market Street 4 up, the Heights 8,
the tower plazas 12; every terrace edge has stairs in three places and can
be jumped.  Line 9 is the flag runner's road: open to the sky in the plaza,
it runs on under the terraces to the Terminal under each tower, whose stair
comes up in a kiosk on the tower plaza.  A dead train stands in each tunnel.
"""
from __future__ import annotations

import math
import random

from . import kit
from .kit import (BRICK, BRICK_DARK, CONCRETE, CONCRETE_DARK, CONCRETE_LIGHT, GLASS, LAMP,
                  STEEL, STEEL_DARK, WOOD, Half, carve, flight, halves, holed_wall,
                  letters, rect, room_walls, sign_decal, slab, strip_light)

HALF = (330.0, 200.0)
SKY = {"top": "#070a14", "horizon": "#2a3446", "sun": [0.3, 0.55, -0.6],
       "clouds": 0.8, "tint": "#8aa0c8"}
AMBIENT = "#4a5468"
GROUND = "#3a3f46"
FOG = 520.0

PAVE = "#6e7178"
PAVE_DARK = "#5c5f66"
ROAD = "#33363c"
KERB = "#8c8f96"
TOWER_RED = "#5a2a28"
TOWER_BLUE = "#23324a"
EMERGENCY = "#ff4a3a"
SODIUM = "#ffb050"

MARKET, HEIGHTS, TOWER = 4.0, 8.0, 12.0
MARKET_X, HEIGHTS_X, TOWER_X = 96.0, 170.0, 236.0
Z0, Z1 = -200.0, 200.0
SUB = (-176.0, -154.0)            # Line 9's cut, south of everything
SUB_X = 320.0                     # where its tunnels end, at the Terminals
SUB_DEPTH = 9.0
PLATFORM = -SUB_DEPTH + 2.0
WELL = (300.0, 310.0, -154.0, -128.0)   # a Terminal's stairwell (magnitudes)
HOUSE_X, HOUSE_Z = 46.0, 28.0      # the control house's outer faces
LOBBY = (262.0, 316.0, -40.0, 40.0)


def _y(x: float) -> float:
    """The ground's height at magnitude ``x`` (which terrace it is on)."""
    return 0.0 if x < MARKET_X else (MARKET if x < HEIGHTS_X else
                                     (HEIGHTS if x < TOWER_X else TOWER))


def build(b: kit.RelayArea) -> None:
    rng = random.Random(0x5B9)
    b.relay("Substation Nine", 60.0)
    b.intro = ["Substation Nine -- the whole city is dark but this.",
               "Deploy from the control house; the flags are in the tower lobbies at "
               "each end, up the terraces.",
               "Line 9 is dead. Its tunnels run under the terraces to the Terminal "
               "behind both towers."]
    b.extra.update({"accent": "#ffb050", "weather": "rain"})
    trench = rect(-SUB_X, SUB_X, SUB[0], SUB[1])
    wells = [h.r(*WELL) for h in halves(b)]
    kit.ground(b, PAVE, soil="#3c3a36", holes=[trench] + wells, material="")
    _subway(b, trench)
    _terraces(b, wells)
    _house(b)
    for h in halves(b):
        _yards(b, h)
        _streets(b, h)
        _outposts(b, h)
        _tower(b, h)
        _stairs(b, h)
        _terminal(b, h)
        _apartments(b, h)
        _garage(b, h)
        _skybridge(b, h)
        _shops(b, h)
        _plaza(b, h)
    _edge(b)
    _landmarks(b)


# ================================================================ terraces
def _terraces(b: kit.RelayArea, wells) -> None:
    """Market Street, the Heights and the tower plazas, stacked, with the
    Terminal stairwells cut down through all three."""
    for h in halves(b):
        tiers = [carve(h.r(x, HALF[0], Z0, Z1), wells) for x in (MARKET_X, HEIGHTS_X, TOWER_X)]
        kit.tier_stack(b, tiers, 0.0, [4.0], [PAVE, PAVE_DARK, PAVE], studs=True)
        # a lip of brighter stone along every terrace edge, broken at the stairs
        for x, y in ((MARKET_X, MARKET), (HEIGHTS_X, HEIGHTS), (TOWER_X, TOWER)):
            for za, zc in ((Z0, -150.0), (-136.0, -26.0), (26.0, 112.0), (140.0, Z1)):
                h.box(x + 1.0, y + 0.2, (za + zc) / 2.0, 2.0, 0.4, zc - za, KERB)


def _stairs(b: kit.RelayArea, h: Half) -> None:
    """Three ways up every terrace edge: the avenue, North and South Street."""
    for x, y in ((MARKET_X, 0.0), (HEIGHTS_X, MARKET), (TOWER_X, HEIGHTS)):
        for za, zc in ((-26.0, 26.0), (112.0, 140.0), (-150.0, -136.0)):
            h.flight_x(x - 10.0, x, za, zc, y, y + 4.0, CONCRETE_LIGHT, fill=y)
        for zz in (-26.5, 26.5):
            h.box(x - 5.0, y + 3.0, zz, 10.0, 2.0, 1.0, STEEL_DARK, material="metal")


# ================================================================ the subway
def _subway(b: kit.RelayArea, trench) -> None:
    """Line 9: open in the plaza, a tunnel under the terraces, Civic Centre
    in the middle of the cut and a Terminal under each tower."""
    kit.channel(b, trench, SUB_DEPTH, "#4a4d52", wall_c="#3c3a36", studs=True)
    zc = (SUB[0] + SUB[1]) / 2.0
    y = -SUB_DEPTH
    b.box([0.0, y + 0.25, zc], [2 * SUB_X, 0.5, 7.0], "#3a2e26")
    for dz in (-2.4, 2.4):
        b.box([0.0, y + 0.7, zc + dz], [2 * SUB_X, 0.4, 0.5], STEEL, material="metal")
    # Civic Centre: a platform either side in the open cut
    for side in (-1, 1):
        pz = zc + side * 8.0
        slab(b, rect(-40.0, 40.0, pz - 3.0, pz + 3.0), PLATFORM, 2.0, CONCRETE_LIGHT,
             studs=True)
        b.box([0.0, PLATFORM + 0.06, pz - side * 2.6], [80.0, 0.12, 0.8], "#f2d24a",
              collide=False)
    for h in halves(b):
        # the stairs down to Civic Centre, along the cut's north wall
        h.flight_x(64.0, 40.0, SUB[1] - 6.0, SUB[1], 0.0, PLATFORM, CONCRETE, fill=y)
        b.cyl([h.x(66.0), 4.0, SUB[1] + 4.0], [1.0, 8.0, 1.0], STEEL_DARK, material="metal")
        b.box([h.x(66.0), 8.6, SUB[1] + 4.0], [0.7, 2.4, 7.0], "#1d4fa0",
              decal=sign_decal("CIVIC CTR", "#1d4fa0", "#ffffff", 7.0 / 2.4))
        # lights in the tunnel roof, every 24 units, the odd one red
        for x in range(108, int(SUB_X), 24):
            strip_light(b, h.x(float(x)), zc, 0.0, 14.0, "z",
                        "#9fe8ff" if x % 48 else EMERGENCY)
        _train(b, h, 196.0, zc)
        # the Terminal's platform, and the buffers at the end of the line
        h.slab(262.0, SUB_X, SUB[1] - 7.0, SUB[1], PLATFORM, 2.0, CONCRETE_LIGHT, studs=True)
        h.box(SUB_X - 2.0, y + 2.0, zc - 4.0, 4.0, 4.0, 3.0, "#d8b23a", studs=True)
        flight(b, "z", WELL[2], WELL[3], *h.xs(WELL[0], WELL[1]), PLATFORM, TOWER, CONCRETE,
               fill=-6.0)


def _train(b: kit.RelayArea, h: Half, x: float, zc: float) -> None:
    """A two-car train stopped dead in the tunnel, its doors open."""
    y = -SUB_DEPTH + 0.9
    for x0, x1 in ((x - 30.0, x - 1.0), (x + 1.0, x + 30.0)):
        car = h.r(x0, x1, zc - 4.0, zc + 4.0)
        mid = (x0 + x1) / 2.0
        door = tuple(sorted((h.x(mid - 3.0), h.x(mid + 3.0))))
        for zz in (zc - 3.7, zc + 3.7):
            holed_wall(b, "x", zz, 0.6, car[0], car[1], y, y + 7.0, "#c9ccd2",
                       holes=[(door[0], door[1], y - 1.0, y + 6.0)])
        slab(b, car, y + 7.6, 0.6, "#a8acb2")
        slab(b, (car[0], car[1], zc - 3.4, zc + 3.4), y + 0.4, 0.4, "#6a6e74")
        for zz, off in ((zc - 4.0, -0.05), (zc + 4.0, 0.05)):
            h.box(mid, y + 3.6, zz + off, x1 - x0 - 4.0, 0.5, 0.1, "#1d4fa0", collide=False)


def _terminal(b: kit.RelayArea, h: Half) -> None:
    """The kiosk over a Terminal's stair, on the tower plaza: walls round
    three sides of the stairwell, a roof, the line's sign over the way in."""
    x0, x1, z0, z1 = WELL
    y = TOWER
    h.box(x0 - 0.5, y + 4.0, (z0 + z1) / 2.0 - 0.5, 1.0, 8.0, z1 - z0 + 1.0, STEEL_DARK)
    h.box(x1 + 0.5, y + 4.0, (z0 + z1) / 2.0 - 0.5, 1.0, 8.0, z1 - z0 + 1.0, STEEL_DARK)
    h.box((x0 + x1) / 2.0, y + 4.0, z0 - 0.5, x1 - x0, 8.0, 1.0, STEEL_DARK)
    h.box((x0 + x1) / 2.0, y + 8.5, (z0 + z1) / 2.0 - 0.5, x1 - x0 + 2.0, 1.0,
          z1 - z0 + 1.0, STEEL_DARK)
    h.sign((x0 + x1) / 2.0, y + 7.2, z1 + 0.36, 8.0, 2.4,
           sign_decal("LINE 9", "#1d4fa0", "#ffffff", 3.3), "z+")


# =========================================================== control house
def _house(b: kit.RelayArea) -> None:
    """Substation Nine's control house: two muster halls and the control
    room between them, on the plaza in the middle of everything."""
    top = 16.0
    area = rect(-HOUSE_X, HOUSE_X, -HOUSE_Z, HOUSE_Z)
    room_walls(b, area, 3.0, 0.0, top, BRICK,
               doors={"x-": [(-7.0, 7.0, 10.0)], "x+": [(-7.0, 7.0, 10.0)],
                      "z-": [(-8.0, 8.0, 10.0)], "z+": [(-8.0, 8.0, 10.0)]})
    for sx in (-1, 1):
        holed_wall(b, "z", sx * 18.0, 2.0, -HOUSE_Z + 3.0, HOUSE_Z - 3.0, 0.0, top,
                   BRICK_DARK, holes=[(-6.0, 6.0, -1.0, 9.0)])
    slab(b, area, top + 1.4, 1.4, CONCRETE_DARK, studs=True)
    room_walls(b, area, 1.2, top + 1.4, top + 4.4, BRICK_DARK,
               doors={"z+": [(-40.0, -31.0, top + 4.4), (31.0, 40.0, top + 4.4)]})
    for sx in (-1, 1):
        flight(b, "z", 52.0, HOUSE_Z, *sorted((sx * 31.0, sx * 40.0)), 0.0, top + 1.4,
               CONCRETE, fill=0.0)
    # inside: the switchboard, still lit -- the only power in town
    b.box([0.0, 4.0, HOUSE_Z - 4.5], [30.0, 8.0, 3.0], "#2a3038", material="metal")
    for i in range(10):
        b.box([-13.5 + i * 3.0, 5.0 + (i % 3) * 1.2, HOUSE_Z - 6.05], [1.6, 0.6, 0.1],
              ["#ff4a3a", "#7cff8a", "#ffd25a"][i % 3], material="neon", collide=False)
    b.box([0.0, 2.0, -8.0], [12.0, 4.0, 6.0], STEEL_DARK, material="metal", studs=True)
    strip_light(b, 0.0, 0.0, top, 30.0, "z", "#bfe4ff")
    kit.board_letters(b, 0.0, top - 3.0, HOUSE_Z, "SUBSTATION 9", 3.0, "#1b1f26", SODIUM,
                      solid=False)
    kit.board_letters(b, 0.0, top - 3.0, -HOUSE_Z, "SUBSTATION 9", 3.0, "#1b1f26", SODIUM,
                      facing="z-", solid=False)
    for h in halves(b):
        for i in range(3):
            for j in (-1, 1):
                b.muster(h.team, h.x(24.0 + 6.0 * i), 0.0, j * 14.0, h.yaw_out, size=5.6)
        h.sign(HOUSE_X - 3.36, 13.4, 0.0, 12.0, 3.4, "sign_%s" % h.team, "x+")
        strip_light(b, h.x(32.0), 0.0, top, 40.0, "z", LAMP)
        h.box(HOUSE_X + 7.0, 2.4, -16.0, 8.0, 4.8, 8.0, h.dark, studs=True)
        h.box(HOUSE_X + 7.0, 2.0, 16.0, 8.0, 4.0, 8.0, CONCRETE_DARK, studs=True)


def _yards(b: kit.RelayArea, h: Half) -> None:
    """The transformer yards north and south of the house, fenced, the
    transformers still humming: big, finned, good cover."""
    for sz in (-1, 1):
        far = sz * 96.0
        _mesh(b, h.x(4.0), far, h.x(40.0), far)
        _mesh(b, h.x(40.0), min(sz * 64.0, far), h.x(40.0), max(sz * 64.0, far))
        for k, x in enumerate((14.0, 30.0)):
            _transformer(b, h, x, sz * (50.0 + k * 26.0))
        for x in (8.0, 36.0):
            h.box(x, 9.0, sz * 64.0, 1.4, 18.0, 1.4, STEEL, material="metal")
        h.box(22.0, 18.6, sz * 64.0, 29.4, 1.2, 1.4, STEEL, material="metal")
        for x in (14.0, 22.0, 30.0):
            h.cyl(x, 16.7, sz * 64.0, 0.9, 2.6, 0.9, "#c8d4dc", collide=False)


def _transformer(b: kit.RelayArea, h: Half, x: float, z: float) -> None:
    h.box(x, 0.6, z, 12.0, 1.2, 10.0, CONCRETE, studs=True)
    h.box(x, 5.2, z, 9.0, 8.0, 7.0, "#5d6b62", material="metal")
    for dz in (-4.0, 4.0):
        h.box(x, 5.2, z + dz, 7.0, 6.0, 1.0, "#4d5a52", material="metal")
    for dx in (-2.5, 0.0, 2.5):
        h.cyl(x + dx, 10.6, z, 1.0, 2.8, 1.0, "#d8e2e8")
        h.sphere(x + dx, 12.3, z, 1.2, 1.2, 1.2, "#9fe8ff", material="neon", collide=False)


def _mesh(b, x0: float, z0: float, x1: float, z1: float, y: float = 0.0,
          h: float = 9.0) -> None:
    """Chain-link: see-through panels between posts, all of it solid."""
    along_x = abs(z1 - z0) < 1e-6
    lo, hi = (min(x0, x1), max(x0, x1)) if along_x else (min(z0, z1), max(z0, z1))
    if hi - lo < 1.0:
        return
    count = max(1, int(round((hi - lo) / 12.0)))
    step = (hi - lo) / count
    fixed = z0 if along_x else x0
    for i in range(count + 1):
        u = lo + i * step
        p = [u, y + h / 2.0 + 0.3, fixed] if along_x else [fixed, y + h / 2.0 + 0.3, u]
        b.cyl(p, [0.9, h + 0.6, 0.9], STEEL, material="metal")
    for i in range(count):
        a, c = lo + i * step + 0.45, lo + (i + 1) * step - 0.45
        if along_x:
            b.box([(a + c) / 2.0, y + h / 2.0, fixed], [c - a, h, 0.3], "#9aa3a8",
                  material="metal", alpha=0.38)
        else:
            b.box([fixed, y + h / 2.0, (a + c) / 2.0], [0.3, h, c - a], "#9aa3a8",
                  material="metal", alpha=0.38)


# ================================================================= streets
def _streets(b: kit.RelayArea, h: Half) -> None:
    """The avenue and the side streets, with what the blackout left in them:
    stalled cars, a bus, flares, a police car, rain-black asphalt."""
    for x0, x1 in ((HOUSE_X + 16.0, MARKET_X - 12.0), (MARKET_X + 4.0, HEIGHTS_X - 12.0),
                   (HEIGHTS_X + 4.0, TOWER_X - 12.0)):
        y = _y(x0)
        h.box((x0 + x1) / 2.0, y + 0.04, 0.0, x1 - x0, 0.08, 34.0, ROAD, collide=False)
        for k in range(int((x1 - x0) // 14)):
            h.box(x0 + 7.0 + k * 14.0, y + 0.1, 0.0, 6.0, 0.06, 0.8, "#d8b23a", collide=False)
    for x, z, along, colour in ((70.0, 9.0, "x", "#7a2a24"), (128.0, -10.0, "x", "#2b4a6a"),
                                (150.0, 30.0, "z", "#d8b23a"), (200.0, 8.0, "x", "#3d5a3a"),
                                (120.0, 126.0, "x", "#c8c8c8"), (206.0, -124.0, "x", "#555b66")):
        h.car(x, z, along, colour, y=_y(x))
    # the police car on the avenue's corner, lights going
    h.car(76.0, -16.0, "z", "#e8e8ec", y=0.0)
    h.box(76.0, 5.05, -16.6, 2.2, 0.5, 0.9, "#ff3a2a", material="neon", collide=False)
    h.box(76.0, 5.05, -15.4, 2.2, 0.5, 0.9, "#3a7aff", material="neon", collide=False)
    _bus(b, h, 150.0, -118.0)
    for x in (112.0, 186.0):
        y = _y(x)
        h.box(x, y + 6.2, 160.0, 12.0, 0.6, 5.0, "#2a3038", collide=False)
        for dx in (-5.6, 5.6):
            h.box(x + dx, y + 2.95, 160.0, 0.6, 5.9, 5.0, "#2a3038", material="glass",
                  alpha=0.5)
        h.box(x, y + 2.95, 161.9, 10.6, 5.9, 0.6, "#2a3038", material="glass", alpha=0.5)
        h.box(x + 9.0, y + 1.5, 156.0, 2.0, 3.0, 2.0, "#1d4fa0", studs=True)
    for x in (64.0, 112.0, 150.0, 190.0, 222.0):
        y = _y(x)
        for z in (-30.0, 30.0):
            h.cyl(x, y + 7.0, z, 1.0, 14.0, 1.0, STEEL_DARK, material="metal")
            h.box(x, y + 14.6, z, 2.6, 1.2, 2.6, STEEL_DARK, collide=False, material="metal")
    for x, z in ((70.0, 24.0), (138.0, -28.0), (212.0, 24.0)):
        h.cyl(x, _y(x) + 0.3, z, 0.5, 0.6, 0.5, EMERGENCY, material="neon", collide=False)
    for x in (104.0, 154.0, 178.0, 220.0):
        y = _y(x)
        for z in (-21.0, 21.0):
            h.box(x, y + 1.0, z, 6.0, 2.0, 6.0, CONCRETE, studs=True)
            h.sphere(x, y + 3.2, z, 5.0, 3.6, 5.0, "#2f5a36", collide=False)


def _bus(b: kit.RelayArea, h: Half, x: float, z: float) -> None:
    y = MARKET
    h.box(x, y + 4.6, z, 32.0, 7.6, 7.6, "#d89a2a")
    h.box(x, y + 5.6, z - 3.85, 28.0, 2.2, 0.1, "#1f2a33", collide=False)
    h.box(x, y + 5.6, z + 3.85, 28.0, 2.2, 0.1, "#1f2a33", collide=False)
    h.box(x, y + 0.4, z, 30.0, 0.8, 7.0, "#1b1d20")


# ================================================================ outposts
def _outposts(b: kit.RelayArea, h: Half) -> None:
    """The laundromat (north) and the diner (south) on Market Street: where
    a team falls back to while its flag is out."""
    for sz, name, colour, sign_bg in ((1, "LAUNDRY", "#c8d0d8", "#2a6aa0"),
                                      (-1, "DINER", "#e0c8a0", "#b02a28")):
        zlo, zhi = sorted((sz * 60.0, sz * 102.0))
        kit.outpost_room(h, 112.0, 158.0, zlo, zhi, MARKET, colour, CONCRETE_DARK,
                         height=12.0, door_w=12.0, pads=2)
        face = zlo if sz > 0 else zhi
        letters(b, h.x(135.0), MARKET + 8.0, face, name, 2.6, sign_bg, "#fff4d0",
                facing="z-" if sz > 0 else "z+")
        h.box(119.0, MARKET + 2.0, sz * 95.0, 4.0, 4.0, 6.0, "#9aa0a6", studs=True)


# =================================================================== towers
def _tower(b: kit.RelayArea, h: Half) -> None:
    """The office tower at the team's end: a two-storey lobby atrium with
    the flag on a plinth in the middle, three ways in, and the dark tower
    over it, an emergency light here and there."""
    x0, x1, z0, z1 = LOBBY
    y = TOWER
    top = y + 26.0
    area = h.r(x0, x1, z0, z1)
    wall_c = TOWER_RED if h.team == "red" else TOWER_BLUE
    t = 3.0
    room_walls(b, area, t, y, top, wall_c,
               doors={h.inward: [(-10.0, 10.0, y + 12.0)],
                      "z-": [(*h.xs(282.0, 296.0), y + 10.0)],
                      "z+": [(*h.xs(282.0, 296.0), y + 10.0)],
                      h.outward: [(-6.0, 6.0, y + 9.0)]})
    # the mezzanine round three sides, a stair up to each side
    for sz in (-1, 1):
        h.slab(x0 + t, x1 - t, sz * 26.0, sz * (40.0 - t), y + 12.0, 1.2, CONCRETE_LIGHT,
               studs=True)
        h.box(285.5, y + 13.0, sz * 26.5, 29.0, 2.0, 1.0, STEEL, material="metal")
        h.flight_z(sz * 12.0, sz * 26.0, x0 + t, x0 + t + 6.0, y, y + 12.0, CONCRETE, fill=y)
    h.slab(x1 - 16.0, x1 - t, -26.0, 26.0, y + 12.0, 1.2, CONCRETE_LIGHT, studs=True)
    h.box(x1 - 15.5, y + 13.0, 0.0, 1.0, 2.0, 36.0, STEEL, material="metal")
    roof = top + 1.6
    slab(b, area, roof, 1.6, CONCRETE_DARK, studs=True)
    tower = h.r(x0 + 6.0, x1 - 6.0, z0 + 8.0, z1 - 8.0)
    b.box([(tower[0] + tower[1]) / 2.0, roof + 40.0, 0.0],
          [tower[1] - tower[0], 80.0, tower[3] - tower[2]], wall_c, collide=False)
    face = tower[1] + 0.06 if h.sx < 0 else tower[0] - 0.06
    for k in range(9):
        for zz in (-12.0, 0.0, 12.0):
            lit = (k * 3 + int(zz)) % 7 == 0
            b.box([face, roof + 6.0 + k * 8.5, zz], [0.12, 3.0, 6.0],
                  EMERGENCY if lit else "#1b2230", material="neon" if lit else "",
                  collide=False)
    name = "CRIMSON MUTUAL" if h.team == "red" else "COBALT TELECOM"
    kit.board_letters(b, h.x(x0), top - 4.0, 0.0, name, 3.2, h.dark, h.light,
                      facing=h.inward, solid=False)
    fx = 289.0
    top_y = kit.pedestal(b, h.x(fx), 0.0, y, h.colour, h.neon)
    b.flag(h.team, h.x(fx), top_y, 0.0)
    kit.banner_mast(b, h.x(fx), 0.0, roof, 30.0, h.team, h.inward)
    for zz in (-20.0, 20.0):
        h.box(279.0, y + 2.0, zz, 4.0, 4.0, 8.0, "#3a3028", studs=True)
    strip_light(b, h.x(fx), 0.0, top, 60.0, "z", "#ffe2a8")
    # the loading dock in the alley out the back
    h.box(x1 + 5.0, y + 2.0, -14.0, 8.0, 4.0, 10.0, WOOD, studs=True)
    h.box(x1 + 5.0, y + 2.5, 16.0, 5.0, 5.0, 5.0, "#6a5a3a", studs=True)


# =============================================================== the Heights
APT = (178.0, 228.0, 40.0, 104.0)      # Larkspur Apartments (north), magnitudes
GARAGE = (178.0, 228.0, -104.0, -40.0)  # the parking garage (south)
DECK = HEIGHTS + 11.2                    # garage deck, skybridge and apartment roof
BRIDGE = (196.0, 210.0)                  # the skybridge's x span


def _apartments(b: kit.RelayArea, h: Half) -> None:
    """Larkspur Apartments: a block on the Heights you can go into, a fire
    escape up its face to a roof of water tanks and air-conditioning --
    and the skybridge's north end."""
    x0, x1, z0, z1 = APT
    y = HEIGHTS
    area = h.r(x0, x1, z0, z1)
    kit.building(b, area, y, 10.0, "#7a5a4a", roof=False,
                 doors={h.inward: [(64.0, 76.0, y + 8.0)], h.outward: [(64.0, 76.0, y + 8.0)],
                        "z-": [(*h.xs(186.0, 194.0), y + 8.0)]},
                 windows={h.inward: [(46.0, 56.0, y + 3.0, y + 7.5), (84.0, 94.0, y + 3.0, y + 7.5)],
                          "z+": [(*h.xs(186.0, 198.0), y + 3.0, y + 7.5),
                                 (*h.xs(208.0, 220.0), y + 3.0, y + 7.5)]},
                 glass=True, lights="#ffcf7a")
    slab(b, area, DECK, 1.2, CONCRETE_DARK, studs=True)
    # parapet round the roof, open where the fire escape and the bridge land
    room_walls(b, area, 1.0, DECK, DECK + 3.0, "#6a4a3c",
               doors={"z-": [(*h.xs(BRIDGE[0], BRIDGE[1]), DECK + 3.0)],
                      h.inward: [(88.0, 100.0, DECK + 3.0)]})
    # the fire escape: a steel stair up the inward face, landing in the gap
    h.flight_z(56.0, 100.0, x0 - 6.0, x0, y, DECK, "#3a4048", fill=y)
    # the roof: water tanks on legs, air-conditioning units, a dish
    for k, z in enumerate((54.0, 90.0)):
        for dx in (-3.0, 3.0):
            for dz in (-3.0, 3.0):
                h.box(214.0 + dx, DECK + 2.0, z + dz, 0.8, 4.0, 0.8, WOOD)
        h.cyl(214.0, DECK + 7.5, z, 9.0, 7.0, 9.0, "#6a4a30")
        h.cone(214.0, DECK + 12.0, z, 9.6, 2.0, 9.6, "#3a2a1e", collide=False)
    for x, z in ((188.0, 60.0), (198.0, 84.0)):
        h.box(x, DECK + 1.6, z, 6.0, 3.2, 5.0, "#9aa0a6", material="metal", studs=True)
        h.box(x, DECK + 3.25, z, 4.0, 0.1, 3.0, "#5a6068", collide=False)
    h.cyl(222.0, DECK + 2.0, 70.0, 0.6, 4.0, 0.6, STEEL_DARK)
    h.sphere(222.0, DECK + 4.5, 70.0, 4.0, 1.2, 4.0, "#c8ccd2", collide=False)
    kit.board_letters(b, h.x(203.0), y + 9.0, z0, "LARKSPUR", 1.8, "#3a2a24", "#ffcf7a",
                      facing="z-", solid=True)


def _garage(b: kit.RelayArea, h: Half) -> None:
    """The parking garage across the avenue: an open ground floor of
    pillars and parked cars, a deck above behind a low wall, a stair up at
    the far end, and the skybridge's south end."""
    x0, x1, z0, z1 = GARAGE
    y = HEIGHTS
    area = h.r(x0, x1, z0, z1)
    slab(b, area, DECK, 1.2, "#8a8f96", studs=True)
    for x in (x0 + 1.0, (x0 + x1) / 2.0, x1 - 1.0):
        for z in (z0 + 1.0, (z0 + z1) / 2.0, z1 - 1.0):
            h.box(x, y + (DECK - 1.2 - y) / 2.0, z, 2.0, DECK - 1.2 - y, 2.0, CONCRETE)
    # the deck's wall: chest-high, cover, gaps for the stair and the bridge
    room_walls(b, area, 1.0, DECK, DECK + 3.0, CONCRETE_LIGHT,
               doors={"z+": [(*h.xs(BRIDGE[0], BRIDGE[1]), DECK + 3.0)],
                      h.outward: [(-84.0, -72.0, DECK + 3.0)]})
    h.flight_x(x1 + 22.0, x1, -84.0, -72.0, y, DECK, CONCRETE, fill=y)
    for i, (x, z, colour) in enumerate(((186.0, -52.0, "#7a2a24"), (218.0, -52.0, "#c8c8c8"),
                                        (186.0, -92.0, "#2b4a6a"), (218.0, -92.0, "#555b66"))):
        h.car(x, z, "z", colour, y=y)
        h.car(x, z + (6.0 if i < 2 else -6.0) * 0.0 + (14.0 if i < 2 else 14.0), "z",
              ["#3d5a3a", "#d8b23a", "#e8e8ec", "#5a2a6a"][i], y=DECK)
    h.sign(x0 - 0.36, y + 8.0, -72.0, 8.0, 3.0, sign_decal("P", "#1d4fa0", "#ffffff", 8.0 / 3.0),
           "x-")


def _skybridge(b: kit.RelayArea, h: Half) -> None:
    """A glass bridge over the avenue between the garage deck and the
    apartment roof: the high road across the Heights."""
    xa, xb = BRIDGE
    span = (-40.0, 40.0)
    h.slab(xa, xb, span[0], span[1], DECK, 1.2, "#9aa0a6", studs=True)
    for x in (xa, xb):
        h.box(x + (0.4 if x == xa else -0.4), DECK + 3.0, 0.0, 0.8, 6.0, 80.0, GLASS,
              material="glass", alpha=0.42)
    h.slab(xa, xb, span[0], span[1], DECK + 6.6, 0.6, "#5a6068")
    strip_light(b, h.x((xa + xb) / 2.0), 0.0, DECK + 6.0, 70.0, "z", "#bfe4ff")
    # the steel trusses under it, clear of the road
    for z in (-24.0, 0.0, 24.0):
        h.box((xa + xb) / 2.0, DECK - 1.8, z, xb - xa, 1.2, 1.2, STEEL_DARK, material="metal")


def _shops(b: kit.RelayArea, h: Half) -> None:
    """Shopfronts on Market Street either side of the avenue: dark
    windows, awnings, a door you can duck into."""
    for sz in (-1, 1):
        for k, (xa, xb, name, awning) in enumerate(((100.0, 124.0, "PAWN", "#2a6a3a"),
                                                   (128.0, 156.0, "NOODLE", "#a02a28"))):
            z_near, z_far = sz * 30.0, sz * 52.0
            area = h.r(xa, xb, z_near, z_far)
            front = "z+" if sz < 0 else "z-"
            kit.building(b, area, MARKET, 9.0, ["#8a7a6a", "#6a7a8a"][k], roof=True,
                         roof_colour=CONCRETE_DARK,
                         doors={front: [(*h.xs(xa + 4.0, xa + 10.0), MARKET + 7.0)]},
                         windows={front: [(*h.xs(xa + 13.0, xb - 3.0), MARKET + 2.0,
                                           MARKET + 6.5)]}, glass=True, lights="#5a6a7a")
            face = z_near if sz > 0 else z_near
            h.box((xa + xb) / 2.0, MARKET + 7.4, face - sz * 1.6, xb - xa, 0.4, 3.2, awning,
                  collide=False)
            kit.board_letters(b, h.x((xa + xb) / 2.0), MARKET + 8.6, face - sz * 0.0, name, 1.2,
                              "#1b1f26", "#c8c8c8", facing=front, solid=False, depth=0.2)


def _plaza(b: kit.RelayArea, h: Half) -> None:
    """The tower plaza: a dry fountain and benches in front of the lobby,
    and puddles on every terrace."""
    cx = 249.0
    for sz in (-1, 1):
        z = sz * 62.0
        h.cyl(cx, TOWER + 1.0, z, 16.0, 2.0, 16.0, CONCRETE_LIGHT)
        h.cyl(cx, TOWER + 2.06, z, 13.0, 0.12, 13.0, "#2f6f8f", collide=False,
              material="glass", alpha=0.7)
        h.cyl(cx, TOWER + 4.0, z, 3.0, 4.0, 3.0, CONCRETE)
        h.sphere(cx, TOWER + 6.6, z, 4.0, 1.4, 4.0, CONCRETE_LIGHT, collide=False)
        kit.bench(b, h.x(cx), sz * 84.0, along="x", y=TOWER)
    for x, z, w, d in ((70.0, -40.0, 14.0, 8.0), (130.0, 40.0, 10.0, 12.0),
                       (200.0, -16.0, 16.0, 6.0), (250.0, 30.0, 8.0, 14.0)):
        h.box(x, _y(x) + 0.03, z, w, 0.06, d, "#3a5a7a", collide=False, material="glass",
              alpha=0.55)


# ===================================================================== edge
def _edge(b: kit.RelayArea) -> None:
    """The city round the edge: the blank backs of buildings, dark, a
    candle in the odd window -- and a water tower on a north roof."""
    hx, hz, m = HALF[0], HALF[1], b.margin
    room_walls(b, rect(-hx - m, hx + m, -hz - m, hz + m), m, 0.0, 40.0, "#2a2e36")
    for i in range(18):
        x = -hx + 18.0 + i * (2 * hx - 36.0) / 17.0
        hgt = 20.0 + (i * 37 % 11) * 4.0
        depth = m + 0.4 + (i % 3) * 0.1
        for sz in (-1, 1):
            cz = sz * (hz + m / 2.0)
            b.box([x, 40.0 + hgt / 2.0, cz], [34.0, hgt, depth], "#232831", collide=False)
            if i % 4 == 1:
                inner = cz - sz * depth / 2.0
                b.box([x, 50.0, inner - sz * 0.1], [3.0, 2.4, 0.2], "#ffcf7a",
                      material="neon", collide=False)
    for i in range(6):
        z = -hz + 30.0 + i * (2 * hz - 60.0) / 5.0
        hgt = 26.0 + (i * 13 % 5) * 6.0
        for sx in (-1, 1):
            b.box([sx * (hx + m / 2.0), 40.0 + hgt / 2.0, z],
                  [m + 0.5 + (i % 2) * 0.1, hgt, 40.0], "#20252d", collide=False)
    # billboards on the north and south walls, their lights out, one still
    # buzzing
    for k, (x, text) in enumerate(((-150.0, "STAY TUNED"), (90.0, "POWER TO THE PEOPLE"),
                                   (-40.0, "CALL 555-0199"), (180.0, "OPEN 24 HRS"))):
        sz = 1 if k % 2 == 0 else -1
        face = sz * hz
        b.box([x, 30.0, face - sz * 0.36], [40.0, 12.0, 0.7], "#2a2e36",
              r=[0, 0 if sz < 0 else math.pi, 0], collide=False,
              decal=sign_decal(text, "#2a2e36", "#ffb050" if k == 1 else "#5a6068",
                               40.0 / 12.0))
    for sx in (-1, 1):
        b.cyl([sx * 120.0, 46.0, hz + m / 2.0], [14.0, 12.0, 14.0], WOOD, collide=False)
        b.cone([sx * 120.0, 54.0, hz + m / 2.0], [15.0, 4.0, 15.0], "#3a2a1e", collide=False)


def _landmarks(b: kit.RelayArea) -> None:
    for x, z, name in ((0, 0, "the control house"), (0, 64, "the north yard"),
                       (0, -64, "the south yard"), (0, -165, "Civic Centre")):
        b.landmark(float(x), float(z), name)
    for sx, team in ((-1, "red"), (1, "blue")):
        tower = "Crimson Mutual" if team == "red" else "Cobalt Telecom"
        b.landmark(sx * 289.0, 0.0, "the %s lobby" % tower)
        b.landmark(sx * 305.0, -140.0, "the %s Terminal" % team)
        for x, z, name in ((135, 81, "the laundromat"), (135, -81, "the diner"),
                           (150, -118, "the bus"), (196, -165, "the dead train")):
            b.landmark(sx * float(x), float(z), "%s (%s side)" % (name, team))
    b.camera(-200.0, 70.0, 120.0, 0.0, 6.0, 0.0)
    b.camera(200.0, 60.0, -110.0, 0.0, 6.0, 0.0)
    b.camera(0.0, 90.0, 190.0, 0.0, 0.0, 0.0)
