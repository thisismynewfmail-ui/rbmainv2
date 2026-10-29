"""Jade Temple: floating islands round a mountain temple, over a sea of cloud.

The course crosses the first lacquered bridge in the wind to the shrine,
rides out the spinning bamboo on its stone disc, takes the lotus pad up to
the pagoda island, hops the clouds that drift in and out, walks the long
rope bridge across the gusts to the tea house, and goes up two more lotus
pads to the great bell on the temple top.

The twist: **TYPHOON** -- the gusts stop gusting and simply blow, twice as
hard, across every bridge.

    start (-120,-110) -> wind bridge (z -99..-55) -> CP1 the shrine (-120,-45)
    bamboo disc (-84,-41) -> lotus island (-56,-41) -> pad -> CP2 the pagoda (-24,50,-44)
    cloud hop (x 2..26) -> island (46,-44) -> rope bridge (z -32..20) -> CP3 the tea house (46,52,30)
    pad -> ledge (y 76) -> pad -> FINISH the bell (13,100,67)
"""
from __future__ import annotations

import math
import random

from ..kit import ArenaArea
from .common import JUMP, PAD, WALK, Course

HALF = (170.0, 140.0)
SKY = {"top": "#3a7ac8", "horizon": "#ffe8c8", "sun": [0.5, 0.45, 0.4], "clouds": 0.7,
       "tint": "#fff0d8"}
AMBIENT = "#a8b8c8"
GROUND = "#f2f4f8"
FOG = 780.0

THEME = {
    "deck": "#5a9a4a", "trim": "#c83a2a", "under": "#6a5a4a", "post": "#5a4a3a",
    "stone_a": "#8a8a7a", "stone_b": "#a89a7a", "rail": "#c83a2a", "arch": "#c83a2a",
    "finish": "#e8b830", "glow": "#ffe08a", "pad": "#f2a8c8", "boost": "#5ad0a8",
    "belt": "#6a4a2a", "roller": "#a8a8a8", "hub": "#8a7a5a", "start": "#7a5a3a",
    "gate": "#e8b830", "look": "bamboo",
}
RED = "#c83a2a"
GOLD = "#e8b830"
STONE = "#8a8a7a"
ROCK = "#6a5a4a"
PINE = "#2a5a3a"
BLOSSOM = "#f2b8d0"
ROOF = "#2a3a3a"


def _cloud_sea(b: ArenaArea, rng: random.Random) -> None:
    """A sea of cloud to the horizon, mountains standing out of it."""
    b.box([0.0, -0.5, 0.0], [1000.0, 1.0, 1000.0], "#f2f4f8")
    for k in range(90):
        x, z = rng.uniform(-450.0, 450.0), rng.uniform(-450.0, 450.0)
        d = rng.uniform(14.0, 40.0)
        b.sphere([x, 0.0, z], [d, d * 0.35, d * rng.uniform(0.7, 1.3)],
                 ["#ffffff", "#e8eef8", "#f8f0f0"][k % 3], collide=False)
    for k in range(12):
        a = k / 12.0 * math.tau + rng.uniform(-0.1, 0.1)
        d = rng.uniform(280.0, 380.0)
        x, z = math.cos(a) * d, math.sin(a) * d
        h = rng.uniform(90.0, 180.0)
        b.cone([x, h / 2.0, z], [h * 0.9, h, h * 0.8], "#5a6a7a")
        b.cone([x, h - h * 0.12, z], [h * 0.3, h * 0.25, h * 0.27], "#f2f4f8")


def _island(c: Course, x0: float, x1: float, z0: float, z1: float, y: float,
            skip=(), grass: str = "#5a9a4a") -> None:
    """A floating island: a grassy top, earth round its edge and a craggy
    root of rock hanging under it."""
    c.deck(x0, x1, z0, z1, y, colour=grass, skip=skip)
    cx, cz = (x0 + x1) / 2.0, (z0 + z1) / 2.0
    w, d = x1 - x0, z1 - z0
    c.b.cone([cx, y - 2.4 - min(w, d) * 0.45, cz], [w * 0.8, min(w, d) * 0.9, d * 0.8], ROCK,
             r=[math.pi, 0.0, 0.0])


def _tree(b: ArenaArea, x: float, y: float, z: float, blossom: bool = True) -> None:
    b.cyl([x, y + 3.0, z], [1.2, 6.0, 1.2], "#5a3a2a")
    c = BLOSSOM if blossom else PINE
    b.sphere([x, y + 7.0, z], [6.0, 4.2, 6.0], c)
    b.sphere([x + 2.0, y + 8.0, z + 1.0], [3.8, 3.0, 3.8], c)


def _lantern(b: ArenaArea, x: float, y: float, z: float) -> None:
    b.box([x, y + 0.4, z], [1.6, 0.8, 1.6], STONE)
    b.box([x, y + 1.8, z], [0.8, 2.0, 0.8], STONE)
    b.box([x, y + 3.2, z], [1.4, 0.8, 1.4], "#ffd88a", material="neon")
    b.box([x, y + 3.9, z], [2.0, 0.6, 2.0], STONE)


def _pagoda(b: ArenaArea, x: float, y: float, z: float, storeys: int, w: float) -> None:
    """A pagoda standing on an island: storeys stepping in, each with its
    wide roof."""
    for k in range(storeys):
        s = w - k * 2.2
        base = y + k * 5.6
        b.box([x, base + 2.0, z], [s * 0.7, 4.0, s * 0.7], "#f2e8d8")
        b.box([x, base + 4.4, z], [s + 2.6, 0.8, s + 2.6], ROOF)
        b.box([x, base + 4.95, z], [s * 0.8, 0.3, s * 0.8], RED)
    b.cyl([x, y + storeys * 5.6 + 2.2, z], [0.6, 4.0, 0.6], GOLD, material="metal")


def _start_and_wind_bridge(c: Course) -> None:
    b = c.b
    c.start(-120.0, 24.0, -110.0, 0.0)
    b.cone([-120.0, 24.0 - 2.4 - 12.0, -110.0], [28.0, 24.0, 18.0], ROCK, r=[math.pi, 0.0, 0.0])
    c.node(-120.0, 24.0, -104.0)
    # the first bridge: red lacquer, no rails, and the wind across it
    c.deck(-123.0, -117.0, -99.0, -55.0, 24.0, colour=RED, skip=("z0", "z1"))
    for z in (-90.0, -64.0):
        b.box([-120.0, 18.8, z], [6.0, 8.0, 1.2], RED, collide=False)
    c.zone("wind", -126.0, -114.0, -97.0, -57.0, 24.0, dir=[1.0, 0.0], strength=13.0,
           period=4.2, ph=0.0)
    # banners on the bridge's posts show which way it blows
    for z in (-97.0, -57.0):
        b.box([-123.3, 27.4, z], [0.4, 9.2, 0.4], GOLD, collide=False)
        b.box([-123.3, 32.4, z], [0.6, 0.8, 0.6], GOLD, collide=False)
    for z in (-97.0, -85.0, -73.0, -61.0):
        c.node(-120.0, 24.0, z)
    c.node(-120.0, 24.0, -57.0)
    # checkpoint 1: the shrine island
    _island(c, -134.0, -106.0, -55.0, -27.0, 24.0, skip=("z0",))
    b.box([-130.0, 26.0, -31.0], [6.0, 4.0, 4.0], "#f2e8d8")
    b.box([-130.0, 28.4, -31.0], [8.0, 0.8, 6.0], ROOF)
    _tree(b, -110.0, 24.0, -30.0)
    _lantern(b, -110.0, 24.0, -52.0)
    c.checkpoint(-120.0, 24.0, -48.0, "the shrine")
    c.power(-130.0, 24.0, -36.0)
    c.node(-120.0, 24.0, -41.0)
    c.node(-108.0, 24.0, -41.0, JUMP)


def _bamboo_and_lotus(c: Course) -> None:
    b = c.b
    # the bamboo disc: a stone disc round a hub, with bamboo poles turning
    y = 26.0
    c.deck(-98.0, -70.0, -49.0, -33.0, y, colour=STONE, skip=("z0", "z1"))
    c.deck(-92.0, -76.0, -57.0, -49.0, y, colour=STONE, under=False, skip=("z1",))
    c.deck(-92.0, -76.0, -33.0, -25.0, y, colour=STONE, under=False, skip=("z0",))
    b.cone([-84.0, y - 2.4 - 9.0, -41.0], [22.0, 18.0, 22.0], ROCK, r=[math.pi, 0.0, 0.0])
    spin = c.sweeper(-84.0, y, -41.0, 12.5, w=1.2, h=2.0, arms=3, speed=1.25)
    c.node(-96.0, y, -41.0, WALK, haz=spin)
    c.node(-88.0, y, -30.0, WALK, haz=spin)
    c.node(-80.0, y, -30.0, WALK, haz=spin)
    c.node(-72.0, y, -41.0, JUMP)
    # the lotus island, its pad throwing you up to the pagoda island
    _island(c, -64.0, -48.0, -49.0, -33.0, y)
    c.node(-62.0, y, -41.0)
    c.node(-56.0, y, -41.0, PAD)
    c.pad(-56.0, y, -41.0, up=64.0)
    # checkpoint 2: the pagoda island
    _island(c, -40.0, -8.0, -60.0, -28.0, 50.0)
    _pagoda(b, -32.0, 50.0, -56.0, 3, 9.0)
    _tree(b, -12.0, 50.0, -32.0)
    _lantern(b, -12.0, 50.0, -56.0)
    c.node(-38.0, 50.0, -41.0)
    c.checkpoint(-20.0, 50.0, -44.0, "the pagoda", yaw=math.pi / 2.0)
    c.power(-12.0, 50.0, -44.0)
    c.node(-16.0, 50.0, -44.0)
    c.node(-9.5, 50.0, -44.0, JUMP, blink="k1")


def _clouds_and_rope(c: Course) -> None:
    b = c.b
    # three clouds that come and go
    groups = ["k1", "k2", "k3"]
    for k, g in enumerate(groups):
        c.blinking(g, 4.0, 0.7, round((4.0 - k * 1.1) % 4.0, 2))
    clouds = [(2.0, 50.0, -44.0), (14.0, 51.0, -44.0), (26.0, 52.0, -44.0)]
    for k, (x, y, z) in enumerate(clouds):
        c.tile("cloud%d" % k, x - 4.0, x + 4.0, z - 4.0, z + 4.0, y, "#ffffff", group=groups[k],
               material="glass")
        c.node(x - 2.0, y, z)
        nxt = groups[k + 1] if k + 1 < len(groups) else None
        if nxt:
            c.node(x + 2.0, y, z, JUMP, blink=nxt)
        else:
            c.node(x + 2.0, y, z, JUMP)
    # the island before the rope bridge
    _island(c, 34.0, 58.0, -56.0, -32.0, 52.0, skip=("z1",))
    _tree(b, 54.0, 52.0, -52.0, blossom=False)
    c.node(38.0, 52.0, -44.0)
    c.node(46.0, 52.0, -36.0)
    # the rope bridge: planks four wide, posts and ropes, and the wind
    c.deck(43.0, 49.0, -32.0, 20.0, 52.0, colour="#8a6a4a", skip=("z0", "z1"), under=False)
    for z in range(-30, 20, 4):
        b.box([46.0, 52.03, z + 1.0], [5.6, 0.06, 0.4], "#6a4a2a", collide=False)
    for x in (43.4, 48.6):
        for z in (-31.0, -6.0, 19.0):
            b.cyl([x, 55.0, z], [0.7, 6.0, 0.7], "#5a3a2a")
        # the rope, strung post to post just over everybody's head
        b.box([x, 57.7, -6.0], [0.2, 0.2, 50.0], "#c8a878", collide=False)
    c.zone("wind", 40.0, 52.0, -30.0, 18.0, 52.0, dir=[-1.0, 0.0], strength=12.0,
           period=3.6, ph=1.2)
    for z in (-30.0, -18.0, -6.0, 6.0, 18.0):
        c.node(46.0, 52.0, z)
    # checkpoint 3: the tea house
    _island(c, 30.0, 62.0, 20.0, 48.0, 52.0, skip=("z0",))
    b.box([58.0, 55.0, 44.0], [6.0, 6.0, 6.0], "#f2e8d8")
    b.box([58.0, 58.4, 44.0], [9.0, 0.8, 9.0], ROOF)
    _lantern(b, 34.0, 52.0, 24.0)
    c.checkpoint(46.0, 52.0, 26.0, "the tea house")
    c.power(34.0, 52.0, 44.0)
    c.node(46.0, 52.0, 32.0)
    c.node(46.0, 52.0, 40.0, PAD)
    c.pad(46.0, 52.0, 40.0, up=62.0)


def _temple(c: Course) -> None:
    b = c.b
    # a ledge of the mountain, and the lotus pad on it
    _island(c, 34.0, 58.0, 54.0, 72.0, 76.0)
    c.node(46.0, 76.0, 58.0)
    c.node(40.0, 76.0, 63.0, PAD)
    c.pad(40.0, 76.0, 63.0, up=62.0)
    # the temple: a great stone platform up from the clouds, and its top
    b.box([13.0, 49.4, 67.0], [26.0, 98.8, 26.0], "#8a7a6a")
    for y in (20.0, 45.0, 70.0):
        b.box([13.0, y, 67.0], [27.0, 1.2, 27.0], RED)
    c.deck(0.0, 26.0, 54.0, 80.0, 100.0, colour="#c8b898", under=False)
    # the bell: a frame of red posts with the bronze bell hung in it
    for x in (4.0, 22.0):
        b.box([x, 106.0, 76.0], [1.6, 12.0, 1.6], RED)
    b.box([13.0, 112.6, 76.0], [20.0, 1.2, 2.0], RED, collide=False)
    b.box([13.0, 113.8, 76.0], [22.0, 1.2, 3.0], ROOF, collide=False)
    b.cone([13.0, 108.6, 76.0], [5.0, 6.0, 5.0], "#a8783a", collide=False, material="metal")
    b.cyl([13.0, 111.8, 76.0], [0.4, 0.4, 0.4], "#5a3a2a", collide=False)
    _lantern(b, 3.0, 100.0, 57.0)
    _lantern(b, 23.0, 100.0, 57.0)
    c.node(20.0, 100.0, 64.0)
    c.checkpoint(13.0, 100.0, 66.0, "the great bell", yaw=math.pi / 2.0, r=9.0, finish=True)
    c.node(13.0, 100.0, 66.0)


def build(b: ArenaArea) -> None:
    rng = random.Random(1368)
    b.void = True
    b.kill_y = -60.0
    _cloud_sea(b, rng)
    c = Course(b, THEME)
    _start_and_wind_bridge(c)
    _bamboo_and_lotus(c)
    _clouds_and_rope(c)
    _temple(c)
    b.camera(-160.0, 60.0, -150.0, -120.0, 24.0, -70.0)
    b.camera(-120.0, 80.0, 0.0, -60.0, 35.0, -41.0)
    b.camera(90.0, 80.0, -60.0, 30.0, 50.0, -20.0)
    b.camera(80.0, 120.0, 100.0, 20.0, 90.0, 60.0)
    b.landmark(-120.0, -77.0, "the first bridge")
    b.landmark(-120.0, -41.0, "the shrine")
    b.landmark(-84.0, -41.0, "the bamboo")
    b.landmark(-56.0, -41.0, "the lotus")
    b.landmark(-24.0, -44.0, "the pagoda")
    b.landmark(14.0, -44.0, "the clouds")
    b.landmark(46.0, -6.0, "the rope bridge")
    b.landmark(46.0, 34.0, "the tea house")
    b.landmark(13.0, 67.0, "the great bell")
    c.done(fall_y=10.0, twist="typhoon", twist_every=[36.0, 50.0], twist_for=12.0, warn=3.0,
           round_seconds=180.0, accent="#5ad0a8")
