"""Neon Grid: a synthwave city at night, its rooftops strung together.

The course goes down a boost highway and jumps its end, hops the beat
bridge (tiles that light in sequence, in time with the music), jumps the
lasers sliding along the laser corridor, crosses two spinning neon discs,
rides a pad up to the rooftops, climbs a staircase of beat tiles and takes
a boost off the edge to the finish under the big sign.

The twist: **THE DROP** -- the beat doubles: the tiles blink twice as fast
and the lasers slide faster.

    start (0,110) -> boost highway -> jump -> CP1 (0,30)
    beat bridge (z 0..-30) -> deck -> laser corridor (z -64..-110) -> CP2 (0,-120)
    two neon discs (x 34, 64) -> pad -> rooftop: CP3 (92,48,-86)
    rising beat stairs (x 72..42) -> boost -> jump -> FINISH (-22,58,-86)
"""
from __future__ import annotations

import math
import random

from ..kit import ArenaArea
from .common import JUMP, PAD, WALK, Course

HALF = (170.0, 140.0)
SKY = {"top": "#0a0618", "horizon": "#5a1a6a", "sun": [0.0, 0.25, -0.9], "clouds": 0.15,
       "tint": "#ff9ae8"}
AMBIENT = "#6a5aa0"
GROUND = "#0a0818"
FOG = 820.0

THEME = {
    "deck": "#1a1430", "trim": "#ff3ac8", "trim_m": "neon", "under": "#0e0a1e", "post": "#241c3a",
    "stone_a": "#2a1a4a", "stone_b": "#1a2a4a", "rail": "#3ad8ff", "arch": "#1a1430",
    "finish": "#ff3ac8", "glow": "#3ad8ff", "pad": "#3ad8ff", "boost": "#ffe03a",
    "belt": "#1a1a1a", "roller": "#8a8e96", "hub": "#2a2040", "start": "#1a1430",
    "gate": "#3ad8ff", "look": "neon",
}
CYAN = "#3ad8ff"
MAGENTA = "#ff3ac8"
YELLOW = "#ffe03a"
VIOLET = "#9a5aff"


def _grid(b: ArenaArea, rng: random.Random) -> None:
    """The ground: a glowing grid to the horizon, the city round it and the
    sun going down behind."""
    size = 60.0
    for i in range(-4, 4):
        for j in range(-4, 4):
            tile = b.box([(i + 0.5) * size, -0.5, (j + 0.5) * size], [size, 1.0, size], "#0a0818",
                         decal="neongrid")
            tile["dw"] = 1                       # the grid on the top, not the edge
    b.box([0.0, -0.9, 0.0], [1200.0, 1.0, 1200.0], "#0a0818")
    # the city: towers with lit windows and a neon edge at the top
    for k in range(28):
        a = k / 28.0 * math.tau + rng.uniform(-0.05, 0.05)
        d = rng.uniform(270.0, 380.0)
        x, z = math.cos(a) * d, math.sin(a) * d
        w, h = rng.uniform(26.0, 48.0), rng.uniform(60.0, 180.0)
        colour = [MAGENTA, CYAN, VIOLET, YELLOW][k % 4]
        b.box([x, h / 2.0, z], [w, h, w], "#120e24")
        b.box([x, h + 0.6, z], [w + 1.0, 1.2, w + 1.0], colour, material="neon")
        face = z - w / 2.0 - 0.2 if z > 0 else z + w / 2.0 + 0.2
        for row in range(3):
            b.box([x, h * (0.3 + row * 0.22), face], [w * 0.7, 2.0, 0.4],
                  [CYAN, MAGENTA, "#ffd08a"][(k + row) % 3], material="neon", collide=False)
    # the sun: a striped disc on the horizon, and a mountain line under it
    sun = b.cyl([0.0, 120.0, -620.0], [300.0, 4.0, 300.0], "#ff6a3a", r=[math.pi / 2.0, 0.0, 0.0],
                material="neon", decal="sunset_grid")
    sun["dw"] = 1
    for k in range(9):
        x = -420.0 + k * 105.0
        h = rng.uniform(50.0, 110.0)
        b.cone([x, h / 2.0, -560.0], [130.0, h, 60.0], "#1a0a2a")
        b.cone([x, h / 2.0 + 0.3, -559.0], [126.0, h - 2.0, 2.0], MAGENTA, collide=False,
               material="neon", alpha=0.6)


def _post(c: Course, x: float, z: float, top: float) -> None:
    """A dark mast up from the grid, ringed with light."""
    c.pillar(x, z, top, 0.0, r=2.0, colour="#1a1430")
    for y in range(12, int(top) - 2, 14):
        c.b.cyl([x, y, z], [2.6, 0.5, 2.6], CYAN, material="neon", collide=False)


def _beat_tiles(c: Course, groups, points, period: float, on: float, size: float = 6.0,
                axis: str = "z", lead: str = "") -> None:
    """Tiles that light in sequence; each a hop from the one before.  The
    mark before each tile waits for it, the way a person waits for the beat."""
    colours = [CYAN, MAGENTA, YELLOW, VIOLET]
    for k, g in enumerate(groups):
        c.blinking(g, period, on, round((period - k * period / len(groups)) % period, 3))
    for k, (g, (x, y, z)) in enumerate(zip(groups, points)):
        h = size / 2.0
        c.tile("%s_tile" % g, x - h, x + h, z - h, z + h, y, colours[k % 4], group=g,
               material="neon")
        _post(c, x, z, y - 1.9 - 2.1)


def _start_and_highway(c: Course) -> None:
    b = c.b
    c.start(0.0, 20.0, 110.0, math.pi)
    for x, z in ((-12.0, 116.0), (12.0, 116.0), (-12.0, 104.0), (12.0, 104.0)):
        _post(c, x, z, 20.0 - 2.4)
    c.node(0.0, 20.0, 103.0)
    c.deck(-6.0, 6.0, 60.0, 99.0, 20.0, skip=("z1",))
    # the highway's lane lines
    for z in range(64, 98, 8):
        b.box([0.0, 20.03, z + 2.0], [0.4, 0.06, 4.0], "#ffffff", collide=False, material="neon")
    c.boost(0.0, 20.0, 92.0, math.pi, length=8.0, width=5.0, speed=46.0)
    c.boost(0.0, 20.0, 74.0, math.pi, length=8.0, width=5.0, speed=46.0)
    for z in (90.0, 66.0):
        _post(c, 0.0, z, 20.0 - 2.4)
    c.node(0.0, 20.0, 62.0, JUMP)
    # checkpoint 1: the overpass
    c.deck(-12.0, 12.0, 8.0, 46.0, 20.0)
    for x, z in ((-8.0, 40.0), (8.0, 40.0), (-8.0, 14.0), (8.0, 14.0)):
        _post(c, x, z, 20.0 - 2.4)
    c.node(0.0, 20.0, 42.0)
    c.checkpoint(0.0, 20.0, 32.0, "the overpass")
    c.power(-8.0, 20.0, 18.0)
    c.node(0.0, 20.0, 18.0)
    c.node(0.0, 20.0, 10.0, JUMP, blink="b1")


def _beat_bridge_and_lasers(c: Course) -> None:
    b = c.b
    groups = ["b1", "b2", "b3", "b4"]
    points = [(0.0, 20.0, 0.0), (0.0, 20.0, -10.0), (0.0, 20.0, -20.0), (0.0, 20.0, -30.0)]
    _beat_tiles(c, groups, points, 2.0, 0.55)
    for k, (x, y, z) in enumerate(points):
        c.node(x, y, z + 1.5)
        nxt = groups[k + 1] if k + 1 < len(groups) else None
        if nxt:
            c.node(x, y, z - 1.5, JUMP, blink=nxt)
        else:
            c.node(x, y, z - 1.5, JUMP)
    # the deck before the corridor
    c.deck(-12.0, 12.0, -64.0, -37.0, 20.0, skip=("z0",))
    for x, z in ((-8.0, -42.0), (8.0, -58.0)):
        _post(c, x, z, 20.0 - 2.4)
    c.node(0.0, 20.0, -42.0)
    # the laser corridor: low walls, and beams at knee height sliding along it
    c.deck(-6.0, 6.0, -110.0, -64.0, 20.0, skip=("x0", "x1", "z0", "z1"))
    for x in (-6.6, 6.6):
        b.box([x, 20.2, -87.0], [1.2, 2.8, 46.0], "#241c3a")
        b.box([x, 21.66, -87.0], [1.2, 0.12, 46.0], MAGENTA, material="neon", collide=False)
    for z in (-74.0, -100.0):
        _post(c, 0.0, z, 20.0 - 2.4)
    l1 = c.laser(-6.0, 21.1, -78.0, 6.0, -78.0, (0.0, 0.0, 9.0), period=3.0, phase=0.0)
    l2 = c.laser(-6.0, 21.1, -96.0, 6.0, -96.0, (0.0, 0.0, 9.0), period=3.0, phase=1.6)
    # (nothing to wait for: a beam sliding along the corridor is jumped)
    del l1, l2
    c.node(0.0, 20.0, -66.0)
    c.node(0.0, 20.0, -87.0)
    c.node(0.0, 20.0, -108.0)
    # checkpoint 2: the plaza
    c.deck(-16.0, 16.0, -136.0, -110.0, 20.0, skip=("z1",))
    for x, z in ((-12.0, -132.0), (12.0, -132.0), (-12.0, -114.0), (12.0, -114.0)):
        _post(c, x, z, 20.0 - 2.4)
    c.checkpoint(0.0, 20.0, -116.0, "the plaza")
    c.power(-12.0, 20.0, -130.0)
    c.node(0.0, 20.0, -123.0)
    c.node(14.0, 20.0, -123.0, JUMP)


def _discs_and_pad(c: Course) -> None:
    b = c.b
    hazards = []
    for k, (cx, y) in enumerate(((34.0, 22.0), (64.0, 24.0))):
        c.deck(cx - 13.0, cx + 13.0, -131.0, -115.0, y, skip=("z0", "z1"))
        c.deck(cx - 7.0, cx + 7.0, -139.0, -131.0, y, under=False, skip=("z1",))
        c.deck(cx - 7.0, cx + 7.0, -115.0, -107.0, y, under=False, skip=("z0",))
        _post(c, cx, -123.0, y - 2.4)
        hazards.append(c.sweeper(cx, y, -123.0, 12.0, w=1.2, h=1.8, arms=4 if k else 2,
                                 speed=1.5 if k == 0 else -1.2, phase=k * 0.7))
        # round the hub by the near strip
        c.node(cx - 11.0, y, -123.0, WALK, haz=hazards[-1])
        c.node(cx - 4.0, y, -111.0, WALK, haz=hazards[-1])
        c.node(cx + 4.0, y, -111.0, WALK, haz=hazards[-1])
        c.node(cx + 11.5, y, -123.0, JUMP)
    # the pad deck, and the rooftop up above beside it
    c.deck(80.0, 98.0, -132.0, -114.0, 24.0)
    _post(c, 89.0, -123.0, 24.0 - 2.4)
    c.node(84.0, 24.0, -123.0)
    c.node(89.0, 24.0, -120.0, PAD)
    c.pad(89.0, 24.0, -120.0, up=64.0)
    c.deck(80.0, 104.0, -98.0, -74.0, 48.0)
    for x, z in ((84.0, -94.0), (100.0, -78.0)):
        _post(c, x, z, 48.0 - 2.4)
    # a billboard on the rooftop's back edge
    b.box([92.0, 54.0, -74.6], [22.0, 12.0, 1.2], "#120e24")
    b.box([92.0, 55.0, -75.3], [20.0, 9.0, 0.2], MAGENTA, material="neon",
          decal="t~NEON GRID~#ff3ac8~#120e24~2.22")
    c.node(90.0, 48.0, -92.0)
    c.checkpoint(92.0, 48.0, -86.0, "the rooftop", yaw=math.pi / 2.0)
    c.power(100.0, 48.0, -94.0)
    c.node(92.0, 48.0, -86.0)
    c.node(81.5, 48.0, -86.0, JUMP, blink="c1")


def _stairs_and_finish(c: Course) -> None:
    b = c.b
    groups = ["c1", "c2", "c3", "c4"]
    points = [(73.0, 50.0, -86.0), (63.0, 52.0, -86.0), (53.0, 54.0, -86.0), (43.0, 56.0, -86.0)]
    _beat_tiles(c, groups, points, 2.4, 0.5)
    for k, (x, y, z) in enumerate(points):
        c.node(x + 1.5, y, z)
        nxt = groups[k + 1] if k + 1 < len(groups) else None
        if nxt:
            c.node(x - 1.5, y, z, JUMP, blink=nxt)
        else:
            c.node(x - 1.5, y, z, JUMP)
    # the launch deck, its boost, and the gap to the last roof
    c.deck(14.0, 36.0, -94.0, -78.0, 58.0)
    _post(c, 25.0, -86.0, 58.0 - 2.4)
    c.node(33.0, 58.0, -86.0)
    c.boost(25.0, 58.0, -86.0, -math.pi / 2.0, length=8.0, width=5.0, speed=46.0)
    c.node(16.0, 58.0, -86.0, JUMP)
    c.deck(-40.0, -2.0, -104.0, -68.0, 60.0)
    for x, z in ((-36.0, -100.0), (-6.0, -100.0), (-36.0, -72.0), (-6.0, -72.0)):
        _post(c, x, z, 60.0 - 2.4)
    # the big sign over the finish
    b.box([-38.4, 70.0, -86.0], [1.2, 20.0, 30.0], "#120e24")
    b.box([-37.7, 72.0, -86.0], [0.2, 10.0, 26.0], CYAN, material="neon",
          decal="t~SKY SPRINT~#3ad8ff~#120e24~2.60")
    c.node(-6.0, 60.0, -86.0)
    c.checkpoint(-22.0, 60.0, -86.0, "the top of the city", yaw=math.pi / 2.0, r=9.0,
                 finish=True)
    c.node(-22.0, 60.0, -86.0)


def build(b: ArenaArea) -> None:
    rng = random.Random(1984)
    b.void = True
    b.kill_y = -60.0
    _grid(b, rng)
    c = Course(b, THEME)
    _start_and_highway(c)
    _beat_bridge_and_lasers(c)
    _discs_and_pad(c)
    _stairs_and_finish(c)
    b.camera(40.0, 60.0, 140.0, 0.0, 20.0, 40.0)
    b.camera(50.0, 60.0, -40.0, 0.0, 20.0, -90.0)
    b.camera(60.0, 70.0, -170.0, 60.0, 30.0, -110.0)
    b.camera(60.0, 100.0, -20.0, 20.0, 55.0, -86.0)
    b.landmark(0.0, 80.0, "the highway")
    b.landmark(0.0, 30.0, "the overpass")
    b.landmark(0.0, -15.0, "the beat bridge")
    b.landmark(0.0, -87.0, "the laser corridor")
    b.landmark(0.0, -123.0, "the plaza")
    b.landmark(50.0, -123.0, "the neon discs")
    b.landmark(92.0, -86.0, "the rooftop")
    b.landmark(58.0, -86.0, "the beat stairs")
    b.landmark(-22.0, -86.0, "the top of the city")
    c.done(fall_y=10.0, twist="drop", twist_every=[36.0, 50.0], twist_for=12.0, warn=3.0,
           round_seconds=180.0, accent="#3ad8ff")
