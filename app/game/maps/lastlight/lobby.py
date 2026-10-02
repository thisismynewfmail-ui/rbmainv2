"""The Holdout -- the bunker where everybody waits for the next wave.

Nobody fights here.  It is where a player who joins mid-wave, or who died
in the last one, stands until the next wave deploys them: a long concrete
hall with the deploy pads, a wall of monitors (the spectator camera is the
real view; the wall just says where it is), a board of what is out there,
and a shooting range of practice dummies to keep the trigger finger warm.

Layout (local, north is +z)::

      z +36  [ monitor wall ...................... ]
             bunks   map table     armoury   |      |
             (24 deploy pads, six by four)   | door | PRACTICE RANGE
             bestiary board (west wall)      |      | (dummies at the far end)
      z -36  [ blast door ......................... ]
             x -50                      x 48          x 112
"""
from __future__ import annotations

import math

from .kit import (
    CONCRETE, CONCRETE_DARK, FLOOR, HAZARD, LAMP, STEEL, STEEL_DARK, WOOD,
    WOOD_DARK, Area, crate, deploy_pad, rect, room_walls, sandbags, sign_decal,
    slab, strip_light, wall_sign)

HALF = 64.0
SKY = {"top": "#141820", "horizon": "#2a3038", "sun": [0.3, 0.7, 0.4],
       "clouds": 0.0, "tint": "#c8d0d8"}
AMBIENT = "#8a929c"

HALL = rect(-50.0, 48.0, -36.0, 36.0)
RANGE = rect(48.0, 112.0, -24.0, 24.0)
CEILING = 16.0
WALL = "#7c828a"
TRIM = "#59606a"

# what the board on the west wall warns about, top to bottom
BESTIARY = [
    ("BLOATER", "Pops in a cloud of bile. Shoot it far away."),
    ("BOMBER", "Dynamite vest. A headshot defuses it."),
    ("LEAPER", "Pounces and pins. Shoot it off your friends."),
    ("BRUTE", "Charges in a straight line. Sidestep."),
    ("SPITTER", "Acid pools. Do not stand in the green."),
    ("SCREAMER", "Calls the horde. Kill it first."),
    ("RIOT", "Armoured front. Shoot it in the back."),
    ("PLAGUE CAPTAIN", "Raises the dead. Hunt him down."),
    ("HIVE", "Bursts into mites when it dies."),
    ("RONIN", "Blocks bullets with his blade. Flank him."),
    ("BURROWER", "Digs under you. Listen for the ground."),
    ("TANK", "Every fifth wave. Everybody shoots it."),
]


def build(b: Area) -> None:
    x0, x1, z0, z1 = HALL
    rx0, rx1, rz0, rz1 = RANGE
    # floor, walls and the ceiling of both rooms
    slab(b, rect(x0, rx1, z0, z1), 0.0, 2.0, CONCRETE_DARK)
    slab(b, rect(x0 + 2.0, x1 - 2.0, z0 + 2.0, z1 - 2.0), FLOOR, FLOOR, "#6f757c",
         studs=True)
    slab(b, rect(rx0, rx1 - 2.0, rz0 + 2.0, rz1 - 2.0), FLOOR, FLOOR, "#686e74",
         studs=True)
    room_walls(b, HALL, 2.0, 0.0, CEILING, WALL,
               doors={"x+": [(-8.0, 8.0, 11.0)]})
    room_walls(b, RANGE, 2.0, 0.0, CEILING, WALL, sides=("x+", "z-", "z+"))
    slab(b, HALL, CEILING + 2.0, 2.0, CONCRETE_DARK)
    slab(b, RANGE, CEILING + 2.0, 2.0, CONCRETE_DARK)
    # the threshold through the range door
    slab(b, rect(x1 - 2.0, x1, -8.0, 8.0), FLOOR, FLOOR, "#6f757c")
    # skirting stripes so the room has a floor line
    for z in (z0 + 2.0, z1 - 2.0):
        inward = 0.15 if z < 0 else -0.15
        b.box([(x0 + x1) / 2.0, 1.1, z + inward], [x1 - x0 - 4.0, 1.4, 0.3], TRIM)
    # lights: tubes down the hall and the range
    for x in (-36.0, -12.0, 12.0, 34.0):
        for z in (-20.0, 4.0, 24.0):
            strip_light(b, x, z, CEILING, 14.0, "x", LAMP)
    for z in (-12.0, 12.0):
        strip_light(b, 80.0, z, CEILING, 40.0, "x", "#d8f0ff")

    _pads(b)
    _monitors(b)
    _blast_door(b)
    _bestiary(b)
    _furniture(b)
    _range(b)
    b.landmark(0.0, -16.0, "the deploy pads")
    b.landmark(80.0, 0.0, "the practice range")


def _pads(b: Area) -> None:
    """Twenty-four pads, one for everybody the server holds, facing the
    monitors and the blast door both (the door is behind them)."""
    for row, z in enumerate((-28.0, -20.0, -12.0, -4.0)):
        for col in range(6):
            x = -38.0 + col * 12.0
            deploy_pad(b, x, z, FLOOR, "#e0a040", 5.0)
            b.safe_spawn(x, FLOOR + 0.6, z, 0.0)


def _monitors(b: Area) -> None:
    """The monitor wall: eight feeds and the banner over them."""
    z = HALL[3] - 2.0                       # the wall's inner face
    b.box([0.0, 6.4, z - 0.6], [74.0, 9.6, 1.2], "#22272e")
    feeds = ["MAIN ST", "CHURCH", "ER BAY", "ROOF",
             "QUAY", "SHIP", "MESS HALL", "LAKE"]
    for i, label in enumerate(feeds):
        col, row = i % 4, i // 4
        x = -27.0 + col * 18.0
        y = 8.6 - row * 4.6
        b.box([x, y, z - 1.35], [16.0, 4.0, 0.3], "#1d3a2a", material="neon",
              decal=sign_decal("CAM %d %s" % (i + 1, label), "#10241a", "#7af0a0",
                               4.0))
    wall_sign(b, 0.0, 13.2, z - 0.35, 56.0, 3.6,
              sign_decal("THE HOLDOUT - NEXT WAVE DEPLOYS FROM HERE", "#2a2f36",
                         "#e0a040", 56.0 / 3.6), "z-", "#2a2f36")
    # a console in front of the wall, with a chair
    b.box([0.0, FLOOR + 1.6, z - 6.0], [30.0, 3.2, 3.0], STEEL_DARK, studs=True,
          material="metal")
    for x in (-10.0, 0.0, 10.0):
        b.box([x, FLOOR + 3.5, z - 5.4], [6.0, 0.6, 1.6], "#3a6a8a",
              material="neon")
    b.box([0.0, FLOOR + 1.2, z - 10.0], [2.4, 2.4, 2.4], "#3a3f46")


def _blast_door(b: Area) -> None:
    """The way out, which only the wave opens."""
    z = HALL[2] + 2.0                       # the south wall's inner face
    b.box([0.0, 6.0, z + 0.6], [24.0, 12.0, 1.2], "#5a6068", material="metal")
    for k in range(5):
        b.box([-10.0 + k * 5.0, 6.0, z + 1.35], [2.4, 11.6, 0.3], HAZARD
              if k % 2 == 0 else "#2a2d31")
    wall_sign(b, 0.0, 13.6, z + 0.35, 24.0, 2.4,
              sign_decal("BLAST DOOR - OPENS ON THE WAVE", "#2a2d31", "#ffd23a",
                         10.0), "z+", "#2a2d31")
    for x in (-15.0, 15.0):
        b.box([x, 13.6, z + 0.5], [1.4, 1.4, 1.0], "#ff4a2a", material="neon")


def _bestiary(b: Area) -> None:
    """The board of what is out there, on the west wall."""
    x = HALL[0] + 2.0
    b.box([x + 0.4, 8.0, 2.0], [0.8, 13.0, 62.0], "#3a3f46")
    wall_sign(b, x + 1.15, 13.2, 2.0, 30.0, 2.2,
              sign_decal("KNOW YOUR ENEMY", "#3a3f46", "#ff6a4a", 13.6), "x+",
              "#3a3f46")
    for i, (name, line) in enumerate(BESTIARY):
        col, row = i // 6, i % 6
        z = -10.0 + col * 30.0
        y = 11.0 - row * 1.8
        wall_sign(b, x + 1.15, y, z, 26.0, 1.5,
                  sign_decal("%s: %s" % (name, line), "#e8e2d0", "#2a2a2a",
                             26.0 / 1.5), "x+", "#e8e2d0")


def _furniture(b: Area) -> None:
    x0, x1, z0, z1 = HALL
    # bunks along the north-west
    for z in (12.0, 22.0):
        for x in (-42.0,):
            b.box([x, FLOOR + 1.2, z], [8.0, 2.4, 4.0], "#4a5a3a", studs=True)
            b.box([x, FLOOR + 5.4, z], [8.0, 0.8, 4.0], "#4a5a3a")
            for dx in (-3.6, 3.6):
                b.box([x + dx, 3.9, z], [0.6, 2.2, 3.6], STEEL_DARK,
                      material="metal")
    # the map table in the middle
    b.box([-16.0, FLOOR + 1.8, 14.0], [14.0, 3.6, 9.0], WOOD_DARK, studs=True)
    b.box([-16.0, FLOOR + 3.7, 14.0], [12.0, 0.2, 7.0], "#c8b88a",
          decal=sign_decal("HARROW / ST AGNES / BLACKWATER / CEDAR PINES",
                           "#c8b88a", "#4a3a22", 12.0 / 7.0), collide=False)
    # the armoury racks by the range door
    for z in (14.0, 24.0):
        b.box([40.0, FLOOR + 4.0, z], [4.0, 8.0, 8.0], STEEL_DARK, material="metal")
        for k in range(3):
            b.box([37.8, FLOOR + 2.4 + k * 2.4, z], [0.4, 0.4, 7.0], "#2a2d31",
                  material="metal")
    # crates and sandbags in the corners
    crate(b, 40.0, FLOOR, -30.0, 4.0, WOOD)
    crate(b, 40.0, FLOOR + 4.0, -30.0, 3.0, WOOD)
    crate(b, -42.0, FLOOR, 30.0, 4.0, "#5a6a3a")
    sandbags(b, 22.0, 30.0, 10.0, "x", y=FLOOR)
    wall_sign(b, -16.0, 9.0, z1 - 2.35, 18.0, 1.8,
              sign_decal("STAY TOGETHER", "#2a2f36", "#d8d8d0", 10.0), "z-",
              "#2a2f36")


def _range(b: Area) -> None:
    rx0, rx1, rz0, rz1 = RANGE
    # the shooting counter across the room, with a gap at each end
    b.box([62.0, FLOOR + 1.8, 0.0], [3.0, 3.6, 30.0], WOOD, studs=True)
    for z in (-12.0, 0.0, 12.0):
        b.box([62.0, FLOOR + 3.8, z], [2.0, 0.4, 2.0], "#c8a02a", collide=False)
    # distance stripes painted down the lanes
    for x in (74.0, 86.0, 98.0):
        b.box([x, FLOOR + 0.03, 0.0], [0.8, 0.06, 40.0], HAZARD, collide=False)
    # the berm at the far end, and the dummies standing in front of it
    b.box([rx1 - 4.0, 5.0, 0.0], [4.0, 10.0, rz1 - rz0 - 4.0], "#6a5a42")
    for z in (-14.0, -7.0, 0.0, 7.0, 14.0):
        b.mark("dummy", 102.0, FLOOR + 0.6, z)
        b.box([102.0, FLOOR + 0.3, z], [3.0, 0.6, 3.0], STEEL_DARK)
    wall_sign(b, 80.0, 13.0, rz1 - 2.35, 22.0, 2.0,
              sign_decal("PRACTICE RANGE", "#2a2f36", "#ffd23a", 11.0), "z-",
              "#2a2f36")
