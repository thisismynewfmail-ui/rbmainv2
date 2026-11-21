"""Leviathan Quarry -- a sea monster's bones in a sandstone quarry, at sunset.

The quarrymen went down through the strata a stride at a time and found
it: a leviathan, ninety million years dead, lying on its belly across the
pit.  They built the dig station inside its skull.  Both teams muster
there, under the cranium, between the jaws; the flags are up on the rim at
either end, in the old winding houses under their headframes.

Layout (red to the west; mirrored about x = 0)::

      z +176  ~~ the tail, going into the quarry wall ~~      rim road
      z +118  CORE SHED (outpost)     |  rib  rib  rib  |       (and theirs)
      z   +60  rim: WINDING HOUSE      == THE SPINE (walk it) ==
      z    0  (flag) |benches| pit .... THE SKULL: dig station (relay) .. pit
      z  -19  ==== the adit: from the bench face, under the benches, up to the flag ====
      z  -47  .................. the jaws, open to the south ..................
      z -118  PALAEO TENT (outpost)  dig trenches, the crane, spoil heaps
      z -196  ================== rim road ========================================

The benches rise outward in eight strides of coloured stone from the pit
floor to the rim; the ribs are stairs from the pit up to the spine, which
runs north to the quarry wall.  The adit is a cutting into each bench face
that becomes a tunnel under the benches and comes up by a stair beside the
flag.
"""
from __future__ import annotations

import math
import random

from . import kit
from .kit import (Half, carve, halves, holed_wall, rect, room_walls, slab, strip_light)

HALF = (310.0, 196.0)
SKY = {"top": "#3a2a5a", "horizon": "#ff9a5a", "sun": [0.55, 0.16, -0.35],
       "clouds": 0.55, "tint": "#ffc8a0"}
AMBIENT = "#b0907a"
GROUND = "#c8a070"
FOG = 880.0

STRATA = ["#e8d0a0", "#b8603a", "#f0e0b8", "#9a5a3a", "#e0c090", "#a86a48", "#f2dcb0",
          "#8a4a30"]
BONE = "#e8dcc0"
BONE_DARK = "#c8b898"
PIT = "#b89870"
TIMBER = "#6a4a2e"
CANVAS = "#d8ccb0"
RUST = "#a85a32"

RIM_Y = 16.0
RINGS = [(150.0 + 8.0 * k, 140.0 + 6.0 * k) for k in range(8)]
STATION = (36.0, 24.0)
STATION_H = 12.0
ADIT_Z = (-24.0, -14.0)
ADIT_X = (150.0, 256.0)
SHAFT_STAIR = (256.0, 272.0)
HOUSE = (250.0, 300.0, -30.0, 30.0)
FLAG_X = 284.0
SPINE_Y = 12.0
RIBS = (44.0, 64.0, 84.0, 104.0, 124.0)


def build(b: kit.RelayArea) -> None:
    rng = random.Random(0x1E71)
    b.relay("the Dig Station", 46.0)
    b.intro = ["Leviathan Quarry -- a sea monster's bones in a sandstone quarry, at sunset.",
               "Muster in the dig station inside its skull; the flags are up on the rim in the "
               "winding houses. Its ribs are stairs to its spine -- walk it.",
               "An adit runs from each bench face under the benches to a stair beside the flag."]
    b.extra.update({"accent": "#ff9a5a", "weather": "dust"})
    kit.ground(b, PIT, soil="#8a6a4a", material="")
    _benches(b)
    for h in halves(b):
        _winding_house(b, h)
        _outposts(b, h)
        _pit(b, h, random.Random(0xD16))
        _rim(b, h)
    _station(b)
    _skull(b)
    _spine(b)
    _edge(b, rng)
    _life(b)
    _landmarks(b)


# =============================================================== the benches
def _benches(b: kit.RelayArea) -> None:
    """Eight strides of strata from the pit floor up to the rim, each its
    own colour, the adits cut through the lowest three and the shaft stairs
    through all of them."""
    hx, hz = HALF
    m = b.margin
    whole = rect(-hx, hx, -hz, hz)
    adits, shafts = [], []
    for h in halves(b):
        adits.append(h.r(ADIT_X[0], ADIT_X[1], ADIT_Z[0], ADIT_Z[1]))
        shafts.append(h.r(SHAFT_STAIR[0], SHAFT_STAIR[1], ADIT_Z[0], ADIT_Z[1]))
    tiers = []
    for k, (rx, rz) in enumerate(RINGS):
        cut = [rect(-rx, rx, -rz, rz)] + shafts + (adits if k < 3 else [])
        tiers.append(carve(whole, cut))
    kit.tier_stack(b, tiers, 0.0, [2.0], STRATA, studs=True)
    # an ammonite in the strata, a fish in the face: the quarry's other fossils
    for h in halves(b):
        h.cyl(RINGS[4][0] - 0.3, 9.0, 60.0, 1.8, 0.6, 1.8, "#8a6a4a", collide=False,
              r=[0.0, 0.0, math.pi / 2.0])
        h.box(RINGS[2][0] - 0.05, 5.0, -90.0, 0.1, 1.0, 5.0, BONE_DARK, collide=False)
    del m


# ============================================================ winding houses
def _winding_house(b: kit.RelayArea, h: Half) -> None:
    """The winding house on the rim: brick, the winding drum and its engine
    inside, the flag before them, the shaft stair beside it -- and the
    headframe outside with its sheave wheel turning."""
    x0, x1, z0, z1 = HOUSE
    y = RIM_Y
    top = y + 14.0
    area = h.r(x0, x1, z0, z1)
    room_walls(b, area, 2.0, y, top, "#9a4a32",
               doors={h.inward: [(-7.0, 7.0, y + 9.0)],
                      "z-": [(*h.xs(276.0, 286.0), y + 8.0)],
                      "z+": [(*h.xs(258.0, 268.0), y + 8.0)],
                      h.outward: [(8.0, 16.0, y + 8.0)]})
    slab(b, h.r(x0 - 1.0, x1 + 1.0, z0 - 1.0, z1 + 1.0), top + 1.2, 1.2, "#5a4a44", studs=True)
    kit.gable(b, h.r(x0 - 1.0, x1 + 1.0, z0 - 1.0, z1 + 1.0), top + 1.2, "#5a4a44", along="z",
              tiers=3, rise=2.0)
    # the shaft stair: up from the adit beside the flag, railed
    sx0, sx1 = SHAFT_STAIR
    z0a, z1a = ADIT_Z
    h.flight_x(sx0, sx1, z0a, z1a, 0.0, y, "#8a6a4a", fill=0.0)
    h.box(sx0 - 0.6, y + 1.5, (z0a + z1a) / 2.0, 1.2, 3.0, z1a - z0a, TIMBER)
    h.box((sx0 + sx1) / 2.0 - 0.6, y + 1.5, z1a + 0.6, sx1 - sx0 - 1.2, 3.0, 1.2, TIMBER)
    h.box((sx0 + sx1) / 2.0 - 0.6, y + 1.5, z0a - 0.6, sx1 - sx0 - 1.2, 3.0, 1.2, TIMBER)
    # the flag before the winding drum
    top_y = kit.pedestal(b, h.x(FLAG_X), 0.0, y, h.colour, h.neon, base="#6a5a4a")
    b.flag(h.team, h.x(FLAG_X), top_y, 0.0)
    h.box(292.0, y + 4.0, 18.0, 6.0, 8.0, 10.0, "#3a3a40", studs=True)
    b.rig("winding_drum", h.x(292.0), y + 4.0, 18.0, r=4.0, w=8.0, yaw=h.yaw_in, seed=h.sx)
    strip_light(b, h.x((x0 + x1) / 2.0), 0.0, top, 40.0, "x", "#ffd890")
    # the headframe over the old shaft: four legs, a deck, the sheave
    hx_, hz_ = 232.0, 44.0
    for dx in (-3.0, 3.0):
        for dz in (-3.0, 3.0):
            h.box(hx_ + dx, y + 15.0, hz_ + dz, 1.0, 30.0, 1.0, RUST, material="metal")
    for k in range(3):
        h.box(hx_, y + 8.0 + k * 9.0, hz_, 7.0, 0.6, 7.0, RUST, material="metal", collide=False)
    h.box(hx_, y + 30.4, hz_, 8.0, 0.8, 8.0, "#7a4a2e", material="metal")
    b.rig("sheave", h.x(hx_), y + 34.0, hz_, r=4.0, yaw=h.yaw_in, rope_p=[h.x(270.0), top + 4.0, 18.0])
    h.box(hx_, y + 0.06, hz_, 5.0, 0.12, 5.0, "#1a1410", collide=False)
    kit.banner_mast(b, h.x(x0 - 10.0), -44.0, y, 24.0, h.team, h.inward)


# ================================================================= outposts
def _outposts(b: kit.RelayArea, h: Half) -> None:
    """The core shed (north) and the palaeontologists' tent (south) on the
    pit floor: where a team falls back to while its flag is out."""
    kit.outpost_room(h, 100.0, 140.0, 96.0, 132.0, 0.0, "#c8c0b0", "#6a6a60", height=10.0,
                     door_w=12.0, pads=2, lights="#ffe8b0")
    for k in range(4):
        h.box(144.0 + 0.0, 0.6 + k * 1.2, 100.0 + 0.0, 4.0, 1.2, 4.0 + 0.0,
              ["#c8a070", "#a86a4a", "#e0c8a0", "#9a7a5a"][k], studs=True)
    kit.outpost_room(h, 100.0, 140.0, -132.0, -96.0, 0.0, CANVAS, "#b8a888", height=9.0,
                     door_w=12.0, pads=2, lights="#ffe8b0")
    kit.gable(b, h.r(100.0, 140.0, -132.0, -96.0), 10.2, CANVAS, along="x", tiers=3, rise=1.6)
    h.box(120.0, 7.0, -96.0 + 0.36, 12.0, 2.4, 0.7, "#f2f2e8", collide=False,
          decal=kit.sign_decal("DIG HQ", "#f2f2e8", "#6a3a1a", 5.0))


# ======================================================================= pit
def _pit(b: kit.RelayArea, h: Half, rng: random.Random) -> None:
    """The pit floor: dig trenches with bones showing, spoil heaps, a crane,
    the drill, a dump truck, tents, the sign."""
    # a dig trench: a cutting two deep, a fin bone in it, steps down
    tx0, tx1, tz0, tz1 = 56.0, 92.0, -76.0, -60.0
    h.box((tx0 + tx1) / 2.0, 1.0, tz0 - 1.0, tx1 - tx0 + 4.0, 2.0, 2.0, "#a88a62", studs=True)
    h.box((tx0 + tx1) / 2.0, 1.0, tz1 + 1.0, tx1 - tx0 + 4.0, 2.0, 2.0, "#a88a62", studs=True)
    for k in range(5):
        h.box(tx0 + 4.0 + k * 7.0, 0.4, (tz0 + tz1) / 2.0, 2.0, 0.8, 9.0 - abs(k - 2) * 2.0, BONE)
    # spoil heaps: stepped mounds of rubble
    for x, z, rx, rz in ((70.0, 40.0, 16.0, 12.0), (124.0, -40.0, 14.0, 12.0),
                         (60.0, -120.0, 18.0, 10.0), (100.0, 64.0, 12.0, 10.0)):
        kit.mound(b, h.x(x), z, rx, rz, 3, 2.0, ["#9a7a5a", "#a88a62", "#b89870"], band=4.0)
    # the crane by the skull's flank: a base, the mast and jib turning (rig)
    h.box(64.0, 2.0, 0.0, 8.0, 4.0, 8.0, "#e8a020", studs=True)
    h.box(64.0, 14.0, 0.0, 2.4, 20.0, 2.4, "#e8a020", material="metal")
    b.rig("crane", h.x(64.0), 24.0, 0.0, jib=26.0, seed=h.sx)
    # a dump truck, parked; a drill rig hammering at the bench foot
    h.box(130.0, 2.2, 30.0, 8.0, 4.4, 14.0, "#e8b820", studs=True)
    h.box(130.0, 5.6, 36.0, 7.0, 2.6, 4.0, "#3a3a40")
    h.box(66.0, 2.0, -96.0, 6.0, 4.0, 6.0, "#c84a2a", studs=True)
    b.rig("drill_rig", h.x(66.0), 4.0, -96.0, h=16.0, seed=h.sx)
    # palaeontologists at the trench with their brushes
    for k, (x, z) in enumerate(((60.0, -68.0), (82.0, -66.0))):
        b.rig("digger", h.x(x), 0.0, z, yaw=(0.4 + k) * h.sx, seed=k + h.sx * 3)
    del rng


def _rim(b: kit.RelayArea, h: Half) -> None:
    """The rim by the winding house: spoil heaps, a conveyor coming up out of
    the pit to the crusher, a hut."""
    for x, z, rx, rz in ((232.0, -110.0, 22.0, 18.0), (284.0, 110.0, 18.0, 22.0),
                         (226.0, 120.0, 12.0, 10.0)):
        kit.mound(b, h.x(x), z, rx, rz, 3, 2.0, ["#9a7a5a", "#a88a62", "#b89870"], band=4.0,
                  y0=RIM_Y)
    h.box(244.0, RIM_Y + 4.0, -70.0, 10.0, 8.0, 10.0, "#6a6a70", studs=True)
    b.rig("conveyor", h.x(150.0), 0.6, -70.0, q=[h.x(240.0), RIM_Y + 8.4, -70.0], w=3.0, seed=h.sx)


# ================================================================ the skull
def _station(b: kit.RelayArea) -> None:
    """The dig station: two muster halls and the lab between them, built
    inside the leviathan's skull (the walls are its bone)."""
    hx, hz = STATION
    area = rect(-hx, hx, -hz, hz)
    room_walls(b, area, 3.0, 0.0, STATION_H, BONE_DARK,
               doors={"x-": [(-7.0, 7.0, 10.0)], "x+": [(-7.0, 7.0, 10.0)],
                      "z-": [(-6.0, 6.0, 10.0)], "z+": [(-5.0, 5.0, 9.0)]})
    for sx in (-1, 1):
        holed_wall(b, "z", sx * 13.0, 2.0, -hz + 3.0, hz - 3.0, 0.0, STATION_H, BONE,
                   holes=[(-6.0, 6.0, -1.0, 9.0)])
    slab(b, area, STATION_H + 1.2, 1.2, BONE, studs=True)
    # the lab: a table of bones being pieced together, lamps, a skeleton
    b.box([0.0, 1.6, 6.0], [14.0, 3.2, 6.0], "#6a5a4a", studs=True)
    for k in range(5):
        b.box([-5.0 + k * 2.5, 3.5, 6.0], [1.6, 0.6, 3.0 - (k % 2), ], BONE, collide=False)
    b.box([0.0, 1.0, -14.0], [8.0, 2.0, 4.0], "#3a3a40", studs=True)
    strip_light(b, 0.0, 0.0, STATION_H, 40.0, "z", "#ffe8b0")
    for h in halves(b):
        for i in range(3):
            for j in (-1, 1):
                b.muster(h.team, h.x(17.0 + 5.0 * i), 0.0, j * 13.0, h.yaw_out, size=4.4)
        h.sign(hx - 3.36, 10.0, 0.0, 10.0, 3.0, "sign_%s" % h.team, "x+")
        strip_light(b, h.x(24.0), 0.0, STATION_H, 40.0, "z", "#ffe8b0")
        h.box(hx + 7.0, 2.0, -14.0, 6.0, 4.0, 6.0, "#9a7a5a", studs=True)
        h.box(hx + 7.0, 1.6, 14.0, 5.0, 3.2, 5.0, BONE_DARK, studs=True)


def _skull(b: kit.RelayArea) -> None:
    """The skull over the station: a cranium of stepped bone you can climb
    (from the spine at its back), the eye sockets over the south door, the
    upper jaw out over the approach on its teeth, the lower jaw on the
    ground either side."""
    hx, hz = STATION
    y = STATION_H + 1.2
    # the cranium: eleven strides of bone, narrowing
    tiers = []
    for k in range(11):
        ix, iz = 2.6 * k, 2.4 * k
        tiers.append([rect(-hx - 2.0 + ix, hx + 2.0 - ix, -hz - 2.0 + iz, hz - iz)])
    kit.tier_stack(b, tiers, y, [2.0], [BONE, BONE_DARK], studs=True)
    # its face: a wall of bone over the south door with the eye sockets in
    # it -- dark hollows, glowing when it sings
    face0, face1 = y + 2.0, y + 20.0
    holed_wall(b, "x", -hz - 1.0, 2.0, -hx - 2.0, hx + 2.0, face0, face1, BONE,
               holes=[(-21.0, -9.0, y + 5.0, y + 13.0), (9.0, 21.0, y + 5.0, y + 13.0)])
    for sx in (-1, 1):
        b.box([sx * 15.0, y + 9.0, -hz + 0.05], [12.0, 8.0, 0.1], "#2a1a12", collide=False)
        b.rig("leviathan_eye", sx * 15.0, y + 9.0, -hz - 0.6, s=1.0)
        # a heavy brow over each socket
        b.box([sx * 15.0, y + 13.9, -hz - 2.7], [15.0, 1.6, 1.6], BONE_DARK, collide=False)
    # a crest of spines down the cranium's ridge
    for k in range(5):
        b.cone([0.0, y + 22.0 + 1.6, -1.0 + (k - 2) * 0.4], [2.4 - k * 0.2, 3.2, 1.6], BONE_DARK,
               collide=False)
    # the upper jaw: a long snout out over the approach, teeth along it
    jz0, jz1 = -74.0, -hz - 2.0
    b.box([0.0, y + 3.0, (jz0 + jz1) / 2.0], [26.0, 6.0, jz1 - jz0], BONE, studs=True)
    b.box([0.0, y + 6.6, (jz0 + jz1) / 2.0 - 2.0], [20.0, 1.2, jz1 - jz0 - 6.0], BONE_DARK, studs=True)
    for sx in (-1, 1):
        b.box([sx * 4.0, y + 3.0, jz0 - 0.05], [3.0, 2.0, 0.1], "#2a1a12", collide=False)
    for k in range(9):
        z = jz0 + 3.0 + k * (jz1 - jz0 - 6.0) / 8.0
        for sx in (-1, 1):
            b.cone([sx * 11.5, y - 2.2, z], [2.4, 4.4, 2.4], "#f2ead8", collide=False,
                   r=[math.pi, 0.0, 0.0])
    # the lower jaw: low walls of bone either side of the way in, teeth up
    for sx in (-1, 1):
        b.box([sx * 14.0, 2.0, (jz0 + jz1) / 2.0], [4.0, 4.0, jz1 - jz0], BONE_DARK, studs=True)
        for k in range(8):
            z = jz0 + 4.0 + k * (jz1 - jz0 - 8.0) / 7.0
            b.cone([sx * 14.0, 5.6, z], [2.0, 3.2, 2.0], "#f2ead8", collide=False)
    b.box([0.0, 2.0, jz0 - 8.0], [14.0, 4.0, 0.8], "#f2f2e8",
          decal=kit.sign_decal("DO NOT FEED", "#f2f2e8", "#a82a1a", 3.5))
    for sx in (-1, 1):
        b.box([sx * 6.0, 1.0, jz0 - 8.0], [0.8, 2.0, 0.8], TIMBER)


def _spine(b: kit.RelayArea) -> None:
    """The spine: vertebrae from the back of the skull north to the quarry
    wall, a walk along the top a stride wide each side, the ribs coming
    down from it -- stairs from the pit floor -- and pillars of bone
    holding it up between them."""
    hz = STATION[1]
    z0, z1 = hz, RINGS[5][1]
    # the walkway: vertebrae (a step up each) and the discs between them
    z = z0
    k = 0
    while z < z1:
        length = 6.0 if k % 2 == 0 else 2.0
        top = SPINE_Y if k % 2 == 0 else SPINE_Y - 1.0
        zz = min(z + length, z1)
        b.box([0.0, (top + SPINE_Y - 3.0) / 2.0, (z + zz) / 2.0], [8.0 if k % 2 == 0 else 5.0,
              top - SPINE_Y + 3.0, zz - z], BONE if k % 2 == 0 else BONE_DARK, studs=True)
        if k % 2 == 0:
            b.cone([0.0, SPINE_Y + 1.6, (z + zz) / 2.0], [2.0, 3.2, 3.0], BONE_DARK, collide=False)
        z = zz
        k += 1
    # the neck: steps up from the spine onto the cranium's first stride
    b.box([0.0, SPINE_Y + 1.0, hz + 2.0], [8.0, 2.0, 4.0], BONE, studs=True)
    # pillars under it between the ribs
    for zp in (54.0, 74.0, 94.0, 114.0, 134.0, 150.0):
        b.box([0.0, (SPINE_Y - 3.0) / 2.0, zp], [3.0, SPINE_Y - 3.0, 3.0], BONE_DARK)
    # the ribs: stairs of bone from the floor up to the walk, both sides
    for zr in RIBS:
        for h in halves(b):
            h.flight_x(34.0, 4.0, zr - 1.6, zr + 1.6, 0.0, SPINE_Y, BONE, fill=0.0)
    del z1


def _edge(b: kit.RelayArea, rng: random.Random) -> None:
    """The quarry's lip all round, and the sea beyond to the south."""
    hx, hz, m = HALF[0], HALF[1], b.margin
    room_walls(b, rect(-hx - m, hx + m, -hz - m, hz + m), m, 0.0, RIM_Y + 14.0, "#a87a52",
               studs=True)
    b.box([0.0, RIM_Y - 1.0, -hz - m - 150.0], [1400.0, 2.0, 300.0], "#4a7aa8", collide=False,
          material="glass", alpha=0.9)
    kit.backdrop(b, "hills", RIM_Y + 14.0, rng, colours=["#7a5a4a", "#8a6a50", "#6a4a3a"],
                 sides=("x-", "x+", "z+"), depth=50.0)


def _life(b: kit.RelayArea) -> None:
    """Gulls over the quarry, dust devils on the floor, the haul truck on the
    rim road, clouds lit by the sunset."""
    b.rig("gulls", 0.0, 70.0, 0.0, n=7, r=150.0)
    for k, (x, z) in enumerate(((-90.0, -110.0), (96.0, 40.0))):
        b.rig("dust_devil", x, 0.0, z, r=30.0, seed=k * 3.1)
    b.rig("haul_truck", -200.0, RIM_Y, 189.0, q=[200.0, RIM_Y, 189.0], speed=10.0)
    b.rig("clouds", 0.0, 240.0, 0.0, n=7, r=560.0, tint="#ffd0b0")


def _landmarks(b: kit.RelayArea) -> None:
    for x, z, name in ((0, 0, "the skull"), (0, 90, "the spine"), (0, -50, "the jaws"),
                       (0, 160, "the tail")):
        b.landmark(float(x), float(z), name)
    for sx, team in ((-1, "red"), (1, "blue")):
        b.landmark(sx * 275.0, 0.0, "the %s winding house" % team)
        for x, z, name in ((120, 114, "the core shed"), (120, -114, "the dig tent"),
                           (150, -19, "the adit"), (64, 0, "the crane"), (232, 44, "the headframe")):
            b.landmark(sx * float(x), float(z), "%s (%s side)" % (name, team))
    b.camera(-150.0, 70.0, 150.0, 0.0, 10.0, 0.0)
    b.camera(150.0, 70.0, -150.0, 0.0, 10.0, 0.0)
    b.camera(0.0, 90.0, -185.0, 0.0, 14.0, 0.0)
