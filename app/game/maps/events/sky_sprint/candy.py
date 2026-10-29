"""Candy Clouds: a sweet shop hung in a pink sky over a river of chocolate.

The course leaves the start deck down a row of gumdrops, bounces off a
block of jelly up to the first checkpoint, wades the taffy road between two
lollipop sweepers, runs the biscuit bridge (it crumbles), crosses a gap on a
jelly trampoline, climbs three marshmallow towers on their pads, walks the
candy-cane beams, rides out the spinning lollipop disc and bounces off the
last jelly onto the top of the cake.

The twist: **SUGAR RUSH** -- for a while everybody is faster and jumps
higher, which is wonderful until the taffy and the crumbling biscuits.

    start (-130,85) -> gumdrops (z 50..14) -> jelly -> CP1 (-130,-28)
    taffy road (x -116..-60) with two lollipop sweepers -> biscuit bridge -> CP2 (-16,-28)
    jelly gap (x 18..46) -> corner (58,-28) -> marshmallow pads -> CP3 (58,62,28)
    candy-cane beams (x 44..-6) -> lollipop disc (-20,34) -> jelly -> the cake: FINISH (y 80)
"""
from __future__ import annotations

import math
import random

from ..kit import ArenaArea
from .common import JUMP, PAD, WALK, Course

HALF = (170.0, 130.0)
SKY = {"top": "#f2a8d8", "horizon": "#ffe8f4", "sun": [0.3, 0.75, 0.4], "clouds": 0.6,
       "tint": "#fff0f8"}
AMBIENT = "#d8b8d0"
GROUND = "#5a3020"
FOG = 760.0

THEME = {
    "deck": "#f8e8c8", "trim": "#e85a9a", "under": "#c89868", "post": "#f2f2f2",
    "stone_a": "#5ad08a", "stone_b": "#ff8ac8", "rail": "#ffffff", "arch": "#e85a9a",
    "finish": "#ffb830", "glow": "#ffe08a", "pad": "#ffffff", "boost": "#5ad0ff",
    "belt": "#c8783a", "roller": "#f2f2f2", "hub": "#f2f2f2", "start": "#f8d8e8",
    "gate": "#ff8ac8", "look": "lolly",
}
CHOC = "#5a3020"
CHOC_LIGHT = "#8a5030"
WAFER = "#e8b878"
PINK = "#ff8ac8"
MINT = "#5ad0a8"
BERRY = "#c83a7a"
LEMON = "#ffe05a"


def _river(b: ArenaArea, rng: random.Random) -> None:
    """The chocolate below: a solid river, swirled, with wafer rafts and
    marshmallows floating in it, and the candy country round about."""
    b.box([0.0, -0.5, 0.0], [900.0, 1.0, 900.0], CHOC)
    for k in range(70):
        x, z = rng.uniform(-420.0, 420.0), rng.uniform(-420.0, 420.0)
        s = rng.uniform(10.0, 50.0)
        b.box([x, 0.04 + k * 0.0015, z], [s, 0.08, s * rng.uniform(0.15, 0.4)], CHOC_LIGHT,
              collide=False, r=[0.0, rng.uniform(0.0, 3.0), 0.0])
    for _ in range(26):
        x, z = rng.uniform(-300.0, 300.0), rng.uniform(-300.0, 300.0)
        if abs(x) < 190.0 and abs(z) < 150.0:
            continue
        b.box([x, 0.6, z], [10.0, 1.2, 6.0], WAFER, decal="planks", r=[0.0, rng.uniform(0, 3), 0.0])
    for _ in range(30):
        x, z = rng.uniform(-320.0, 320.0), rng.uniform(-320.0, 320.0)
        if abs(x) < 190.0 and abs(z) < 150.0:
            continue
        b.cyl([x, 1.5, z], [4.0, 3.0, 4.0], "#fff8f0")
    # the candy country: gumdrop hills, giant lollipops, candy canes, cupcakes
    for k in range(16):
        a = k / 16.0 * math.tau + rng.uniform(-0.12, 0.12)
        d = rng.uniform(250.0, 360.0)
        x, z = math.cos(a) * d, math.sin(a) * d
        kind = k % 4
        if kind == 0:
            h = rng.uniform(50.0, 90.0)
            b.cone([x, h / 2.0, z], [h * 1.1, h, h * 1.1], [MINT, PINK, LEMON, BERRY][k % 4])
            b.sphere([x, h + 1.0, z], [8.0, 6.0, 8.0], "#ffffff")
        elif kind == 1:
            h = rng.uniform(60.0, 110.0)
            b.cyl([x, h / 2.0, z], [3.0, h, 3.0], "#ffffff")
            _wrap(b.cyl([x, h + 10.0, z], [28.0, 4.0, 28.0], [PINK, MINT, LEMON][k % 3],
                  r=[math.pi / 2.0, 0.0, 0.0], decal="sp_rainbow_gores"))
        elif kind == 2:
            h = rng.uniform(50.0, 90.0)
            _wrap(b.cyl([x, h / 2.0, z], [6.0, h, 6.0], "#ffffff", decal="xm_candystripe"))
            _wrap(b.cyl([x + 6.0, h, z], [6.0, 12.0, 6.0], "#ffffff", r=[0.0, 0.0, 1.5708],
                  decal="xm_candystripe"))
        else:
            _wrap(b.cyl([x, 14.0, z], [40.0, 28.0, 40.0], [BERRY, "#8a5ad8", MINT][k % 3],
                  decal="sp_pleats"))
            b.sphere([x, 34.0, z], [44.0, 24.0, 44.0], "#fff0f8")
            b.sphere([x, 48.0, z], [6.0, 6.0, 6.0], "#e83a3a")
    # cotton-candy clouds high over the country, out of everybody's reach
    for k in range(18):
        a = k / 18.0 * math.tau
        d = rng.uniform(230.0, 330.0)
        x, z, y = math.cos(a) * d, math.sin(a) * d, rng.uniform(110.0, 160.0)
        c = ["#ffd0ec", "#d0e8ff", "#fff0f8"][k % 3]
        for m in range(4):
            b.sphere([x + m * 9.0 - 13.0, y + (m % 2) * 4.0, z], [18.0, 13.0, 15.0], c)


def _wrap(part):
    """A pattern printed all the way round a part, not on one face of it."""
    part["dw"] = 1
    return part


def _candy_post(c: Course, x: float, z: float, top: float) -> None:
    """A stick of rock holding something up, out of the chocolate."""
    _wrap(c.b.cyl([x, top / 2.0, z], [2.4, top, 2.4], "#ffffff", decal="xm_candystripe"))


def _start_and_gumdrops(c: Course) -> None:
    b = c.b
    c.start(-130.0, 18.0, 85.0, math.pi)
    for x, z in ((-142.0, 92.0), (-118.0, 92.0), (-142.0, 78.0), (-118.0, 78.0)):
        _candy_post(c, x, z, 18.0 - 2.4)
    c.node(-130.0, 18.0, 78.0)
    c.deck(-136.0, -124.0, 60.0, 74.0, 18.0, colour=WAFER, skip=("z1",))
    _candy_post(c, -130.0, 67.0, 18.0 - 2.4)
    c.node(-130.0, 18.0, 62.0, JUMP)
    # gumdrops: rounded, sugared, one hop apart
    drops = [(-130.0, 18.0, 50.0), (-127.0, 19.5, 38.0), (-131.0, 21.0, 26.0),
             (-128.0, 22.5, 14.0)]
    for k, (x, y, z) in enumerate(drops):
        colour = [PINK, MINT, LEMON, BERRY][k]
        b.add("rbox", [x, y - 1.6, z], [7.0, 3.2, 7.0], colour)
        b.sphere([x, y - 3.6, z], [6.0, 2.0, 6.0], colour, collide=False)
        _candy_post(c, x, z, y - 4.4)
        c.node(x, y, z + 2.5)
        c.node(x, y, z - 2.5, JUMP)
    # a block of jelly at the foot of the first cliff: it throws you up
    c.deck(-138.0, -122.0, -6.0, 8.0, 20.0, colour=WAFER)
    _candy_post(c, -130.0, 1.0, 20.0 - 2.4)
    c.jelly(-134.0, -126.0, -4.0, 4.0, 20.0, "#e83a5a", up=52.0)
    c.node(-130.0, 20.0, 6.0)
    c.node(-130.0, 22.0, 0.0, PAD)


def _cp1_and_taffy(c: Course) -> None:
    b = c.b
    y = 34.0
    # checkpoint 1: the sweet-shop counter, its near edge clear of the jelly
    c.deck(-140.0, -116.0, -40.0, -16.0, y, colour="#f8e8c8", skip=("x1",))
    for x, z in ((-136.0, -36.0), (-120.0, -36.0), (-136.0, -20.0), (-120.0, -20.0)):
        _candy_post(c, x, z, y - 2.4)
    c.node(-130.0, y, -20.0)
    c.checkpoint(-130.0, y, -24.0, "the sweet-shop counter")
    c.power(-138.0, y, -38.0)
    c.node(-128.0, y, -28.0)
    # the taffy road: pink and sticky, you wade through it
    c.deck(-116.0, -60.0, -34.0, -22.0, y, colour="#f8e8c8", skip=("x0", "x1", "z0", "z1"))
    b.box([-95.0, y + 0.04, -28.0], [30.0, 0.08, 11.6], "#ff6aa8", collide=False, material="glass",
          alpha=0.85)
    c.zone("taffy", -110.0, -80.0, -34.0, -22.0, y, scale=0.55)
    for x in (-108.0, -82.0):
        _candy_post(c, x, -28.0, y - 2.4)
    # two lollipop sweepers on islands either side of the road
    c.deck(-106.0, -94.0, -46.0, -34.0, y, colour=MINT, skip=("z1",))
    _candy_post(c, -100.0, -40.0, y - 2.4)
    s1 = c.sweeper(-100.0, y, -40.0, 16.0, w=1.4, h=2.2, arms=2, speed=1.1, phase=0.0)
    c.deck(-82.0, -70.0, -22.0, -10.0, y, colour=LEMON, skip=("z0",))
    _candy_post(c, -76.0, -16.0, y - 2.4)
    s2 = c.sweeper(-76.0, y, -16.0, 16.0, w=1.4, h=2.2, arms=2, speed=-1.2, phase=1.0)
    c.node(-114.0, y, -28.0, WALK, haz=s1)
    c.node(-90.0, y, -28.0, WALK, haz=s2)
    c.node(-62.0, y, -28.0, crumble=["biscuit%d" % k for k in range(4)])
    # the biscuit bridge: it crumbles a moment after you land on it
    for k in range(4):
        x0 = -60.0 + k * 10.0
        c.crumble("biscuit%d" % k, x0, x0 + 10.0, -32.0, -24.0, y, WAFER if k % 2 else "#d8a868")
        c.node(x0 + 5.0, y, -28.0)
    # checkpoint 2: the cookie jar lid
    c.deck(-20.0, 6.0, -40.0, -16.0, y, colour="#f8e8c8", skip=("x0",))
    for x, z in ((-16.0, -36.0), (2.0, -20.0)):
        _candy_post(c, x, z, y - 2.4)
    c.checkpoint(-14.0, y, -28.0, "the cookie jar", yaw=math.pi / 2.0)
    c.power(2.0, y, -36.0)
    c.node(-14.0, y, -28.0)
    c.node(4.0, y, -28.0, JUMP)


def _jelly_gap_and_towers(c: Course) -> None:
    b = c.b
    y = 34.0
    # a jelly trampoline in a gap, lower down: drop onto it and it throws
    # you on across
    c.deck(14.0, 26.0, -34.0, -22.0, 30.0, colour=WAFER)
    _candy_post(c, 20.0, -28.0, 30.0 - 2.4)
    c.jelly(14.6, 25.4, -33.4, -22.6, 30.0, "#3ab0e8", up=50.0)
    c.node(20.0, 32.0, -28.0, PAD)
    # the corner, and the marshmallow towers going up from it
    c.deck(40.0, 76.0, -40.0, -16.0, y + 2.0, colour="#f8e8c8")
    for x, z in ((44.0, -36.0), (72.0, -36.0), (44.0, -20.0), (72.0, -20.0)):
        _candy_post(c, x, z, y + 2.0 - 2.4)
    c.node(46.0, y + 2.0, -28.0)
    c.power(72.0, y + 2.0, -36.0)
    c.node(58.0, y + 2.0, -28.0)
    c.node(58.0, y + 2.0, -22.0, PAD)
    c.pad(58.0, y + 2.0, -22.0, up=62.0)
    for k, (z0, z1, top) in enumerate(((-8.0, 4.0, 50.0), (16.0, 40.0, 64.0))):
        # a marshmallow: a soft pale column with a toasted top
        h = top - 1.2
        b.cyl([58.0, h / 2.0, (z0 + z1) / 2.0], [11.0, h, 11.0], "#fff8f0")
        if k == 0:
            c.deck(52.0, 64.0, z0, z1, top, colour="#f2d8b0", under=False)
            c.node(58.0, top, -4.0)
            c.node(58.0, top, 0.0, PAD)
            c.pad(58.0, top, 0.0, up=62.0)
    # checkpoint 3: the top of the big marshmallow
    c.deck(46.0, 70.0, 16.0, 40.0, 64.0, colour="#f2d8b0")
    c.node(58.0, 64.0, 22.0)
    c.checkpoint(58.0, 64.0, 26.0, "the big marshmallow")
    c.power(66.0, 64.0, 36.0)
    c.node(55.0, 64.0, 34.0)
    c.node(47.5, 64.0, 34.0, JUMP)


def _beams_disc_cake(c: Course) -> None:
    b = c.b
    # candy canes laid as balance beams, three wide, each a hop up
    for k, (x0, x1, y) in enumerate(((30.0, 44.0, 64.0), (12.0, 26.0, 66.0), (-6.0, 8.0, 68.0))):
        _wrap(b.box([(x0 + x1) / 2.0, y - 0.6, 34.0], [x1 - x0, 1.2, 3.0], "#ffffff", decal="xm_candystripe"))
        _candy_post(c, (x0 + x1) / 2.0, 34.0, y - 1.2)
        c.node(x1 - 1.2, y, 34.0)
        c.node(x0 + 1.4, y, 34.0, JUMP)
    # the lollipop disc: an octagon of sugar round a stick, its arms going round
    y = 70.0
    c.deck(-34.0, -6.0, 26.0, 42.0, y, colour="#ffd0e8", skip=("x0", "z0", "z1"))
    c.deck(-28.0, -12.0, 18.0, 26.0, y, colour="#ffd0e8", under=False, skip=("z1",))
    c.deck(-28.0, -12.0, 42.0, 50.0, y, colour="#ffd0e8", under=False, skip=("z0",))
    _candy_post(c, -20.0, 34.0, y - 2.4)
    disc = c.sweeper(-20.0, y, 34.0, 13.0, w=1.4, h=2.2, arms=3, speed=1.0, phase=0.4)
    c.node(-8.0, y, 34.0, WALK, haz=disc)
    c.node(-14.0, y, 44.0, WALK, haz=disc)
    c.node(-26.0, y, 44.0, WALK, haz=disc)
    c.node(-33.0, y, 36.0)
    # the cake: a wide bottom tier with a jelly on it, the top tier above
    c.deck(-80.0, -34.0, 14.0, 54.0, y, colour="#fff0f8", skip=("x1",))
    _wrap(b.cyl([-57.0, (y - 1.2) / 2.0, 34.0], [44.0, y - 1.2, 40.0], "#f8d8e8", decal="sp_pleats"))
    for k in range(12):
        a = k / 12.0 * math.tau
        b.sphere([-57.0 + math.cos(a) * 22.0, y - 2.6, 34.0 + math.sin(a) * 20.0], [3.0, 2.4, 3.0],
                 [PINK, MINT, LEMON][k % 3], collide=False)
    c.jelly(-44.0, -36.0, 30.0, 38.0, y, "#8ad83a", up=56.0)
    c.node(-40.0, y + 2.0, 34.0, PAD)
    c.deck(-76.0, -56.0, 22.0, 46.0, 84.0, colour="#fff0f8", under=False)
    # the top tier's sponge, solid down to the bottom tier
    _wrap(b.cyl([-66.0, (y + 82.8) / 2.0, 34.0], [18.0, 82.8 - y, 22.0], "#ffd0e8", decal="sp_pleats"))
    # candles on the top tier, round its back
    for k, (x, z) in enumerate(((-74.0, 24.0), (-74.0, 44.0), (-74.0, 34.0))):
        b.cyl([x, 87.0, z], [1.2, 6.0, 1.2], [PINK, MINT, LEMON][k])
        b.sphere([x, 90.6, z], [0.8, 1.4, 0.8], "#ffb830", material="neon", collide=False)
    c.node(-60.0, 84.0, 34.0)
    c.checkpoint(-66.0, 84.0, 34.0, "the top of the cake", yaw=math.pi / 2.0, r=9.0, finish=True)
    c.node(-66.0, 84.0, 34.0)


def build(b: ArenaArea) -> None:
    rng = random.Random(1801)
    b.void = True
    b.kill_y = -60.0
    _river(b, rng)
    c = Course(b, THEME)
    _start_and_gumdrops(c)
    _cp1_and_taffy(c)
    _jelly_gap_and_towers(c)
    _beams_disc_cake(c)
    b.camera(-160.0, 60.0, 120.0, -130.0, 25.0, 20.0)
    b.camera(-150.0, 80.0, -80.0, -60.0, 30.0, -28.0)
    b.camera(100.0, 100.0, -60.0, 58.0, 50.0, 0.0)
    b.camera(20.0, 110.0, 90.0, -40.0, 75.0, 34.0)
    b.landmark(-130.0, 32.0, "the gumdrops")
    b.landmark(-130.0, -28.0, "the sweet-shop counter")
    b.landmark(-95.0, -28.0, "the taffy road")
    b.landmark(-40.0, -28.0, "the biscuit bridge")
    b.landmark(20.0, -28.0, "the jelly")
    b.landmark(58.0, 0.0, "the marshmallows")
    b.landmark(20.0, 34.0, "the candy canes")
    b.landmark(-20.0, 34.0, "the lollipop disc")
    b.landmark(-62.0, 34.0, "the cake")
    c.done(fall_y=10.0, twist="sugar_rush", twist_every=[36.0, 50.0], twist_for=12.0, warn=3.0,
           round_seconds=180.0, accent="#ff8ac8")
