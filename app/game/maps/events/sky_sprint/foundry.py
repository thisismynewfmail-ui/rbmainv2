"""The Foundry: an ironworks hung over a lake of molten iron.

The course runs out of the loading bay along a row of I-beams, up two
conveyors (the first against you, the second with you), through the hammer
hall, up the piston steps, across the gear room with its sweeping arm,
up the crane girders and along the ladle line -- a fast belt, a gap over
the pour and a run of rusted grates that drop under you -- to the foot of
the great chimney, and up it on two blast pads to the bell at the top.

The twist: **REVERSE** -- every conveyor runs the other way for a while,
and the hammers swing harder.

    start (-140,-100) ->  girders  -> CP1 (-5,-100) -> belts -> corner (110,-97)
                                                                    |  hammer hall
    CP3 (-31,-18) <- gear room (0,-18) <- piston steps <- CP2 (110,-18)
         |  crane girders
    corner (-30,50) -> ladle belt -> pour -> grates -> chimney (108,52) -> pads -> FINISH (y 110)
"""
from __future__ import annotations

import math
import random

from ..kit import ArenaArea
from .common import JUMP, PAD, WALK, Course

HALF = (180.0, 140.0)
SKY = {"top": "#2a1a1a", "horizon": "#a8502a", "sun": [0.4, 0.5, -0.3], "clouds": 0.5,
       "tint": "#ffc890"}
AMBIENT = "#8a6a5a"
GROUND = "#3a2018"
FOG = 700.0

THEME = {
    "deck": "#5a5e66", "trim": "#e8b830", "under": "#3a3e44", "post": "#4a4a50",
    "stone_a": "#6a6e76", "stone_b": "#7a6e5e", "rail": "#e8b830", "arch": "#3a3e44",
    "finish": "#c8302a", "glow": "#ff8a2a", "pad": "#ff6a1a", "boost": "#ffc83a",
    "belt": "#2a2a2e", "roller": "#8a8e96", "hub": "#6a5a4a", "start": "#4a4e56",
    "gate": "#ffb84a",
}
LAVA = "#ff6a1a"
STEEL = "#5a5e66"
RUST = "#8a4a2a"


def _lava(b: ArenaArea, rng: random.Random) -> None:
    """The pour below: a glowing lake, crusted, with the works round it."""
    b.box([0.0, -0.5, 0.0], [900.0, 1.0, 900.0], LAVA, material="neon")
    # crust floating on it, darker in the middle of each floe, and bubbles
    for k in range(150):
        x, z = rng.uniform(-420.0, 420.0), rng.uniform(-420.0, 420.0)
        s = rng.uniform(8.0, 46.0)
        yaw = rng.uniform(0.0, 3.0)
        y = 0.1 + k * 0.0015                      # each floe at its own height
        b.box([x, y, z], [s, 0.2, s * rng.uniform(0.4, 1.1)], "#5a2a14" if k % 3 else "#3a1a10",
              collide=False, r=[0.0, yaw, 0.0])
        if k % 4 == 0:
            b.box([x, y + 0.14, z], [s * 0.5, 0.08, s * 0.3], "#2a120a", collide=False,
                  r=[0.0, yaw, 0.0])
    for _ in range(40):
        x, z = rng.uniform(-300.0, 300.0), rng.uniform(-300.0, 300.0)
        d = rng.uniform(2.0, 6.0)
        b.sphere([x, 0.0, z], [d, d * 0.7, d], "#ffc860", collide=False)
    # the works at the edge of the lake: sheds, stacks and gantries
    for k in range(14):
        a = k / 14.0 * math.tau + rng.uniform(-0.1, 0.1)
        d = rng.uniform(260.0, 340.0)
        x, z = math.cos(a) * d, math.sin(a) * d
        w, h = rng.uniform(40.0, 80.0), rng.uniform(40.0, 90.0)
        dep = w * 0.7
        b.box([x, h / 2.0, z], [w, h, dep], "#2a2a30")
        b.box([x, h + 2.0, z], [w + 4.0, 4.0, dep + 4.0], "#3a2a24")
        if k % 2:
            b.cyl([x + w / 4.0, h + 34.0, z], [8.0, 60.0, 8.0], "#4a3a34", collide=False)
            b.cyl([x + w / 4.0, h + 65.0, z], [9.0, 2.0, 9.0], "#2a2a2a", collide=False)
        # a row of furnace mouths glowing on the face towards the lake
        face = z - dep / 2.0 - 0.2 if z > 0 else z + dep / 2.0 + 0.2
        for m in range(3):
            b.box([x - w / 3.0 + m * w / 3.0, h * 0.4, face], [4.0, 6.0, 0.4], "#ffb04a",
                  collide=False, material="neon")


def _beam(c: Course, x0: float, x1: float, z: float, y: float, w: float = 5.0) -> None:
    """An I-beam laid along x: the top flange you run on, the web, the foot."""
    c.deck(x0, x1, z - w / 2.0, z + w / 2.0, y, colour=STEEL, trim="#c8a030", under=False)
    c.b.box([(x0 + x1) / 2.0, y - 2.4, z], [x1 - x0, 2.4, 1.0], "#4a4e56", collide=False)
    c.b.box([(x0 + x1) / 2.0, y - 4.0, z], [x1 - x0, 1.2, w * 0.8], "#4a4e56", collide=False)
    for x in (x0 + 2.0, x1 - 2.0):
        c.b.box([x, y - 2.4, z + 0.55], [0.8, 0.8, 0.1], RUST, collide=False)


def _supports(c: Course, x: float, z: float, top: float) -> None:
    """A lattice tower from the pour up to whatever it holds."""
    c.pillar(x, z, top, 0.0, r=2.2, colour="#3a3e44")
    for y in range(8, int(top) - 4, 10):
        c.b.box([x, y, z], [4.4, 0.6, 4.4], "#5a5e66", collide=False)


def _start_and_girders(c: Course) -> None:
    b = c.b
    c.start(-140.0, 20.0, -100.0, math.pi / 2.0)
    c.node(-133.0, 20.0, -100.0)
    # the loading bay apron
    c.deck(-129.0, -112.0, -106.0, -94.0, 20.0, skip=("x0",))
    c.rail(-128.0, -105.6, -112.6, -105.6, 20.0)
    c.rail(-128.0, -94.4, -112.6, -94.4, 20.0)
    b.box([-120.5, 20.03, -100.0], [16.0, 0.06, 1.0], "#e8b830", collide=False)
    c.node(-114.0, 20.0, -100.0, JUMP)
    _supports(c, -120.0, -100.0, 20.0 - 2.4)
    # four I-beams, gaps of eight
    for k, (x0, x1, y) in enumerate(((-104.0, -90.0, 20.0), (-82.0, -68.0, 20.0),
                                     (-60.0, -46.0, 22.0), (-38.0, -26.0, 20.0))):
        _beam(c, x0, x1, -100.0, y)
        _supports(c, (x0 + x1) / 2.0, -100.0, y - 4.6)
        c.node(x0 + 2.5, y, -100.0)
        c.node(x1 - 1.8, y, -100.0, JUMP)
    # checkpoint 1: the weigh-house deck
    c.deck(-18.0, 8.0, -112.0, -88.0, 20.0, skip=("x1",))
    for x, z in ((-14.0, -108.0), (4.0, -108.0), (-14.0, -92.0), (4.0, -92.0)):
        _supports(c, x, z, 20.0 - 2.4)
    c.node(-15.0, 20.0, -100.0)
    c.checkpoint(-5.0, 20.0, -100.0, "the weigh-house", yaw=math.pi / 2.0)
    c.power(-5.0, 20.0, -106.0)
    b.box([-15.0, 21.5, -110.0], [4.0, 3.0, 3.0], "#6a5a3a", collide=True)      # a crate of ingots
    b.box([-15.0, 23.2, -110.0], [3.0, 0.4, 2.0], "#e8b830", collide=False, material="metal")
    c.node(5.0, 20.0, -100.0)


def _belts(c: Course) -> None:
    b = c.b
    # the first belt runs against you; the second carries you
    c.belt(8.0, 40.0, -106.0, -94.0, 20.0, -8.0, 0.0, skip=("x0",))
    _supports(c, 24.0, -100.0, 20.0 - 2.4)
    c.node(37.5, 20.0, -100.0, JUMP)
    c.deck(40.0, 56.0, -106.0, -94.0, 26.0, skip=("x1",))
    _supports(c, 48.0, -100.0, 26.0 - 2.4)
    c.node(43.0, 26.0, -100.0)
    c.belt(56.0, 92.0, -106.0, -94.0, 26.0, 10.0, 0.0, skip=("x0",))
    _supports(c, 74.0, -100.0, 26.0 - 2.4)
    c.node(90.0, 26.0, -100.0, JUMP)
    # the corner landing, where the hammer hall starts
    c.deck(96.0, 124.0, -112.0, -82.0, 32.0, skip=("z1",))
    for x, z in ((100.0, -108.0), (120.0, -108.0), (100.0, -86.0), (120.0, -86.0)):
        _supports(c, x, z, 32.0 - 2.4)
    c.node(100.0, 32.0, -100.0)
    c.node(110.0, 32.0, -90.0)
    c.power(118.0, 32.0, -106.0)
    b.box([104.0, 33.6, -109.0], [5.0, 3.2, 3.0], "#8a4a2a")                    # a skip of slag
    b.box([104.0, 35.3, -109.0], [4.4, 0.2, 2.4], "#ff8a3a", collide=False, material="neon")


def _hammer_hall(c: Course) -> None:
    b = c.b
    c.deck(104.0, 116.0, -82.0, -30.0, 32.0, skip=("z0", "z1"))
    c.rail(104.4, -81.4, 104.4, -30.6, 32.0, h=1.6)
    c.rail(115.6, -81.4, 115.6, -30.6, 32.0, h=1.6)
    _supports(c, 110.0, -66.0, 32.0 - 2.4)
    _supports(c, 110.0, -44.0, 32.0 - 2.4)
    hammers = []
    for k, z in enumerate((-70.0, -56.0, -42.0)):
        # the gantry: two legs off the deck's sides and a beam across
        for x in (100.0, 120.0):
            b.box([x, 24.0, z], [1.6, 48.0, 1.6], "#3a3e44")
        b.box([110.0, 48.8, z], [21.6, 1.6, 2.0], "#c8a030", collide=False)
        b.box([110.0, 48.8, z + 1.05], [21.6, 1.2, 0.1], "#1a1a1a", collide=False,
              decal="hazard")
        hammers.append(c.hammer(110.0, 48.0, z, 13.6, "x", amp=1.0, period=2.8,
                                phase=k * 1.1, head=(4.4, 4.4, 4.4)))
    c.node(110.0, 32.0, -80.0, WALK, haz=hammers[0])
    c.node(110.0, 32.0, -63.0, WALK, haz=hammers[1])
    c.node(110.0, 32.0, -49.0, WALK, haz=hammers[2])
    c.node(110.0, 32.0, -34.0)
    # checkpoint 2: the casting floor
    c.deck(96.0, 124.0, -30.0, -6.0, 32.0, skip=("z0",))
    for x, z in ((100.0, -26.0), (120.0, -26.0), (100.0, -10.0), (120.0, -10.0)):
        _supports(c, x, z, 32.0 - 2.4)
    c.checkpoint(110.0, 32.0, -25.0, "the casting floor")
    c.power(118.0, 32.0, -10.0)
    c.node(110.0, 32.0, -18.0)
    c.node(99.0, 32.0, -18.0, JUMP, blink="pa")


def _pistons(c: Course) -> None:
    b = c.b
    # five pistons stepping up and down the line, A and B out of step
    c.blinking("pa", 3.2, 0.6, 0.0)
    c.blinking("pb", 3.2, 0.6, 1.6)
    steps = ((86.0, 35.0), (74.0, 38.0), (62.0, 41.0), (50.0, 44.0), (38.0, 46.0))
    for k, (x, y) in enumerate(steps):
        group = "pa" if k % 2 == 0 else "pb"
        ahead = ("pb" if group == "pa" else "pa") if k + 1 < len(steps) else None
        c.tile("piston%d" % k, x - 4.0, x + 4.0, -22.0, -14.0, y,
               "#c8a030" if group == "pa" else "#8a8e96", group=group, material="metal")
        # the cylinder it rides on, down into the dark
        # (solid, and well short of the tile: nobody wedges in under one)
        b.cyl([x, (y - 4.0) / 2.0, -18.0], [3.0, y - 4.0, 3.0], "#3a3e44")
        c.node(x + 2.5, y, -18.0)
        if ahead:
            c.node(x - 2.5, y, -18.0, JUMP, blink=ahead)
        else:
            c.node(x - 2.5, y, -18.0, JUMP)
    c.deck(16.0, 32.0, -26.0, -10.0, 48.0, skip=("x0",))
    _supports(c, 25.0, -18.0, 48.0 - 2.4)
    c.node(30.0, 48.0, -18.0)
    c.node(19.0, 48.0, -18.0)


def _gear_room(c: Course) -> None:
    b = c.b
    # an octagon of deck round the great gear's hub, one step up
    y = 50.0
    c.deck(-16.0, 16.0, -26.0, -10.0, y, skip=("x0", "z0", "z1"))
    c.deck(-10.0, 10.0, -34.0, -26.0, y, under=False, skip=("z1",))
    c.deck(-10.0, 10.0, -10.0, -2.0, y, under=False, skip=("z0",))
    # the teeth of the gear round the rim, below the deck
    b.cyl([0.0, y - 3.6, -18.0], [34.0, 1.6, 34.0], "#5a4a3a", collide=False, material="metal")
    for k in range(16):
        a = k / 16.0 * math.tau
        b.box([math.cos(a) * 17.6, y - 3.6, -18.0 + math.sin(a) * 17.6], [3.0, 1.2, 3.0],
              "#6a5a4a", collide=False, r=[0.0, -a, 0.0])
    _supports(c, 0.0, -18.0, y - 2.4)
    sweep = c.sweeper(0.0, y, -18.0, 15.0, w=1.4, h=2.2, arms=2, speed=1.3)
    c.node(15.0, y, -18.0, WALK, haz=sweep)
    c.node(6.0, y, -9.0, WALK, haz=sweep)
    c.node(-6.0, y, -9.0, WALK, haz=sweep)
    c.node(-15.0, y, -18.0)
    # checkpoint 3: the pattern shop, abutting the gear room
    c.deck(-46.0, -16.0, -30.0, -6.0, y, skip=("x1",))
    for x, z in ((-42.0, -26.0), (-20.0, -26.0), (-42.0, -10.0), (-20.0, -10.0)):
        _supports(c, x, z, y - 2.4)
    c.checkpoint(-24.0, y, -18.0, "the pattern shop", yaw=math.pi / 2.0)
    c.power(-42.0, y, -26.0)
    c.node(-31.0, y, -18.0)
    c.node(-30.0, y, -8.0, JUMP)


def _crane(c: Course) -> None:
    b = c.b
    stones = [(-30.0, 53.0, 2.0), (-30.0, 56.0, 16.0), (-30.0, 59.0, 30.0)]
    c.stones(stones, size=7.0, colour="#c8a030")
    for k, (x, y, z) in enumerate(stones):
        # each a girder end slung from the crane's trolley beam by two
        # cables, clear of the line either side
        for side in (-1.0, 1.0):
            b.cyl([x + side * 3.2, (y + 100.0) / 2.0, z], [0.3, 100.0 - y, 0.3], "#2a2a2a",
                  collide=False)
        c.node(x, y, z - 2.5)
        c.node(x, y, z + 2.5, JUMP)
    # the crane: a mast off to the side, its jib out over the girders and a
    # trolley beam along them that the cables hang from
    b.box([-62.0, 50.0, 16.0], [4.0, 100.0, 4.0], "#c8a030")
    b.box([-45.0, 101.0, 16.0], [38.0, 2.0, 3.0], "#c8a030", collide=False)
    b.box([-30.0, 99.6, 16.0], [9.0, 0.8, 36.0], "#3a3e44", collide=False)
    b.box([-62.0, 104.0, 16.0], [8.0, 6.0, 6.0], "#3a3e44", collide=False)
    c.deck(-40.0, -20.0, 38.0, 62.0, 62.0, skip=("x1",))
    for x, z in ((-36.0, 42.0), (-24.0, 58.0)):
        _supports(c, x, z, 62.0 - 2.4)
    c.node(-30.0, 62.0, 42.0)
    c.node(-24.0, 62.0, 50.0)


def _ladle_line(c: Course) -> None:
    b = c.b
    y = 62.0
    c.belt(-20.0, 30.0, 44.0, 56.0, y, 12.0, 0.0, skip=("x0",))
    _supports(c, 5.0, 50.0, y - 2.4)
    c.node(28.0, y, 50.0, JUMP)
    # the pour: a ladle tipping molten iron down past the gap
    b.cyl([35.0, y + 18.0, 64.0], [14.0, 12.0, 14.0], "#3a3a40", collide=False, r=[0.6, 0.0, 0.0])
    b.cyl([35.0, (y + 12.0) / 2.0, 58.0], [3.0, y + 12.0, 3.0], LAVA, material="neon")
    c.deck(40.0, 56.0, 42.0, 58.0, y, skip=("x1",))
    _supports(c, 48.0, 50.0, y - 2.4)
    c.node(43.0, y, 50.0)
    c.boost(48.0, y, 50.0, math.pi / 2.0, length=8.0, width=5.0, speed=46.0)
    c.node(54.0, y, 50.0, crumble=["grate%d" % k for k in range(4)])
    # the grates: rusted through, they drop a moment after you land on them
    for k in range(4):
        x0 = 56.0 + k * 10.0
        c.crumble("grate%d" % k, x0, x0 + 10.0, 44.0, 56.0, y, RUST if k % 2 else "#7a4a2a")
        c.node(x0 + 5.0, y, 50.0)
    # the chimney's foot
    c.deck(96.0, 120.0, 38.0, 64.0, y, skip=("x0",))
    _supports(c, 100.0, 42.0, y - 2.4)
    _supports(c, 116.0, 60.0, y - 2.4)
    c.power(100.0, y, 60.0)
    c.node(104.0, y, 50.0)
    c.node(108.0, y, 50.0, PAD)


def _chimney(c: Course) -> None:
    b = c.b
    # the stack itself, behind the ledges, bricks up into the smoke
    b.cyl([108.0, 80.0, 92.0], [26.0, 160.0, 26.0], "#7a3a2a", decal="bricks")["dw"] = 1
    b.cyl([108.0, 161.0, 92.0], [28.0, 2.0, 28.0], "#3a2a24", collide=False)
    for y in (90.0, 120.0, 150.0):
        b.cyl([108.0, y, 92.0], [26.6, 1.2, 26.6], "#c8a030", collide=False)
    # a pad throws you straight up beside the ledge over it; you come up
    # past its edge and step on
    c.pad(108.0, 62.0, 50.0, up=62.0)
    c.deck(100.0, 116.0, 60.0, 80.0, 86.0)
    b.box([108.0, 83.2, 78.0], [14.0, 3.2, 4.0], "#7a3a2a", collide=False, decal="bricks")
    c.node(108.0, 86.0, 64.0)
    c.node(108.0, 86.0, 76.0, PAD)
    c.pad(108.0, 86.0, 76.0, up=62.0)
    # the top: the finish, under the works bell
    c.deck(96.0, 120.0, 40.0, 62.0, 110.0)
    for x, z in ((99.0, 43.0), (117.0, 43.0)):
        b.box([x, 116.0, z], [1.6, 12.0, 1.6], "#3a3e44")
    b.box([108.0, 122.6, 43.0], [21.6, 1.2, 1.6], "#3a3e44", collide=False)
    b.cone([108.0, 119.6, 43.0], [4.6, 4.8, 4.6], "#e8b830", collide=False, material="metal")
    b.sphere([108.0, 117.2, 43.0], [1.2, 1.2, 1.2], "#c8a030", collide=False, material="metal")
    c.node(108.0, 110.0, 58.0)
    c.checkpoint(108.0, 110.0, 51.0, "the top of the chimney", r=9.0, finish=True)
    c.node(108.0, 110.0, 50.0)


def build(b: ArenaArea) -> None:
    rng = random.Random(1709)
    b.void = True
    b.kill_y = -60.0
    _lava(b, rng)
    c = Course(b, THEME)
    _start_and_girders(c)
    _belts(c)
    _hammer_hall(c)
    _pistons(c)
    _gear_room(c)
    _crane(c)
    _ladle_line(c)
    _chimney(c)
    b.camera(-170.0, 60.0, -150.0, -60.0, 20.0, -100.0)
    b.camera(150.0, 80.0, -150.0, 110.0, 32.0, -60.0)
    b.camera(60.0, 90.0, 30.0, 0.0, 50.0, -18.0)
    b.camera(40.0, 120.0, 120.0, 108.0, 100.0, 52.0)
    b.landmark(-80.0, -100.0, "the girders")
    b.landmark(60.0, -100.0, "the belts")
    b.landmark(110.0, -56.0, "the hammer hall")
    b.landmark(62.0, -18.0, "the piston steps")
    b.landmark(0.0, -18.0, "the gear room")
    b.landmark(-30.0, 16.0, "the crane girders")
    b.landmark(20.0, 50.0, "the ladle line")
    b.landmark(108.0, 60.0, "the chimney")
    c.done(fall_y=10.0, twist="reverse", twist_every=[38.0, 52.0], twist_for=12.0, warn=3.0,
           round_seconds=180.0, accent="#ff8a2a")
