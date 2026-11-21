"""Circuit City -- a motherboard at night, and everybody is the size of a
transistor.

The board is a city: copper traces are its streets, capacitors its towers,
RAM sticks a district of long blocks, two graphics cards stand up like
walls, and in the middle sits the processor under a heatsink the size of a
cathedral, its fan humming over the fins.  Both teams muster in the CPU's
package; the flags are on chips inside the I/O blocks at either end of the
board.  Under the board, in the cable trenches, nobody is watching.

Layout (red to the west; mirrored about x = 0)::

      z +196  ======== the case wall, its window, the room outside ===========
      z +134  ======== the north cable trench (under the board) ===============
      z +120  RAM BANKS  ....  CAPACITORS  ....  CMOS BATTERY (centre)
      z  +56  VRM (outpost)                     HEATSINK FINS (on the CPU)
      z    0  I/O BLOCK (flag) -- traces -- CAPS -- THE CPU (relay)
      z  -56  VRM (outpost)
      z -100  GPU (a wall, fans on its face) .... SOUTHBRIDGE (centre)
      z -134  ======== the south cable trench =================================

Everything stands on the board at y = 0; the heatsink's fins are a maze on
the CPU's roof, sixteen high; the trenches run eight down.
"""
from __future__ import annotations

import math
import random

from . import kit
from .kit import (Half, carve, flight, halves, holed_wall, rect, room_walls, slab,
                  strip_light)

HALF = (320.0, 196.0)
SKY = {"top": "#05060c", "horizon": "#1a2a4a", "sun": [0.3, 0.7, 0.4],
       "clouds": 0.1, "tint": "#9ab8e8"}
AMBIENT = "#4a5a7a"
GROUND = "#1f5a3a"
FOG = 640.0

PCB = "#1f5a3a"
PCB_DARK = "#174a30"
SILK = "#e8f0e8"
COPPER = "#ffb05a"
SOLDER = "#c8ccd2"
CHIP = "#1b1d22"
CHIP_LIGHT = "#2a2e36"
ALU = "#b8c0c8"
ALU_DARK = "#8a929a"
CAP_BLUE = "#2a4aa8"
CAP_BLACK = "#22242a"
GOLD = "#e8c050"
LED_GREEN = "#4aff7a"
LED_RED = "#ff4a3a"

CPU = 34.0
CPU_TOP = 12.0
FIN_TOP = 28.0
IO = (262.0, 316.0, -40.0, 40.0)
FLAG_X = 290.0
TRENCH_Z = (128.0, 140.0)
TRENCH_X = 270.0
TRENCH_DEPTH = 8.0
CENTRE_WELLS = (6.0, 22.0)
BASE_WELLS = (244.0, 260.0)


def build(b: kit.RelayArea) -> None:
    rng = random.Random(0xC1C)
    b.relay("the CPU", 48.0)
    b.intro = ["Circuit City -- a motherboard at night, and you are the size of a transistor.",
               "Muster in the processor's package under the heatsink; the flags are on "
               "chips in the I/O blocks at either end of the board.",
               "The cable trenches under the board run end to end. Mind the dust."]
    b.extra.update({"accent": "#ffb05a", "weather": "sparks"})
    trenches = [rect(-TRENCH_X, TRENCH_X, TRENCH_Z[0], TRENCH_Z[1]),
                rect(-TRENCH_X, TRENCH_X, -TRENCH_Z[1], -TRENCH_Z[0])]
    kit.ground(b, PCB, soil="#0e2a1c", holes=trenches, material="")
    for trench in trenches:
        _trench(b, trench)
    _cpu(b)
    _heatsink(b)
    _centre_parts(b)
    for h in halves(b):
        _io(b, h)
        _caps(b, h)
        _ram(b, h)
        _gpu(b, h)
        _vrms(b, h)
        _chips(b, h)
        _traces(b, h)
    _case(b, rng)
    _landmarks(b)


# ================================================================ trenches
def _trench(b: kit.RelayArea, trench) -> None:
    """A cable trench under the board: the board over it, stairs down
    through holes at the middle and near each end, the cables, the dust."""
    x0, x1, z0, z1 = trench
    wells = []
    for sx in (-1, 1):
        wells.append(rect(*sorted((sx * CENTRE_WELLS[0], sx * CENTRE_WELLS[1])), z0, z1))
        wells.append(rect(*sorted((sx * BASE_WELLS[0], sx * BASE_WELLS[1])), z0, z1))
    kit.channel(b, trench, TRENCH_DEPTH, "#2a2e36", wall_c="#22262c", studs=True,
                material="metal")
    kit.plate(b, carve(trench, wells), 0.0, 0.6, PCB, studs=True)
    y = -TRENCH_DEPTH
    zc = (z0 + z1) / 2.0
    for sx in (-1, 1):
        # down at the middle: outward from the centre line
        flight(b, "x", sx * CENTRE_WELLS[0], sx * CENTRE_WELLS[1], z0, z1, 0.0, y, ALU_DARK,
               fill=y)
        # down near the end: inward from the I/O block
        flight(b, "x", sx * BASE_WELLS[1], sx * BASE_WELLS[0], z0, z1, 0.0, y, ALU_DARK, fill=y)
        # hazard kerbs along the open sides of each hole
        for xa, xb in (CENTRE_WELLS, BASE_WELLS):
            for z in (z0 - 0.6, z1 + 0.6):
                b.box([sx * (xa + xb) / 2.0, 0.4, z], [xb - xa, 0.8, 1.2], "#f2b01e")
    # the cables along the floor: flat ribbons, red, blue, rainbow
    for k, (dz, colour) in enumerate(((-3.0, "#c42b20"), (0.0, "#2a6aa8"), (3.0, "#e8e8e8"))):
        b.box([0.0, y + 0.3, zc + dz], [480.0, 0.6, 2.0], colour)
    # lights in the board's underside, and the dust bunny and the screw
    for x in range(-250, 260, 25):
        if any(abs(abs(x) - (a + c) / 2.0) < 10.0 for a, c in (CENTRE_WELLS, BASE_WELLS)):
            continue
        strip_light(b, float(x), zc, -0.6, 4.0, "z", "#9fe8ff")
    north = zc > 0
    bx = 120.0 if north else -120.0
    for dx, dz, s in ((0.0, 0.0, 5.0), (2.4, 1.0, 3.6), (-2.0, -1.4, 3.0)):
        b.sphere([bx + dx, y + 2.0 + s * 0.2, zc + dz], [s, s * 0.8, s], "#9a9a92",
                 collide=False)
    b.cone([-bx, y + 1.0, zc + 2.0], [2.4, 2.0, 2.4], SOLDER, material="metal", collide=False)
    b.sphere([-bx, y + 2.2, zc + 2.0], [5.0, 1.0, 5.0], SOLDER, material="metal", collide=False)


# ===================================================================== CPU
def _cpu(b: kit.RelayArea) -> None:
    """The processor's package: two muster halls and the die room between
    them, gold pins round its skirt."""
    c = CPU
    area = rect(-c, c, -c, c)
    room_walls(b, area, 3.0, 0.0, CPU_TOP, "#3a3e46",
               doors={"x-": [(-7.0, 7.0, 9.0)], "x+": [(-7.0, 7.0, 9.0)],
                      "z-": [(-5.0, 5.0, 9.0)], "z+": [(-5.0, 5.0, 9.0)]})
    for sx in (-1, 1):
        holed_wall(b, "z", sx * 12.0, 2.0, -c + 3.0, c - 3.0, 0.0, CPU_TOP, CHIP_LIGHT,
                   holes=[(-6.0, 6.0, -1.0, 9.0)])
    slab(b, area, CPU_TOP + 1.4, 1.4, ALU, studs=True, material="metal")
    # the socket's frame round the base, a step out
    frame_gaps = [(-16.0, -8.0, 1.6), (-5.0, 5.0, 1.6), (8.0, 16.0, 1.6)]
    room_walls(b, rect(-c - 4.0, c + 4.0, -c - 4.0, c + 4.0), 4.0, 0.0, 1.6, "#2a2e36",
               doors={"x-": [(-7.0, 7.0, 1.6)], "x+": [(-7.0, 7.0, 1.6)],
                      "z-": frame_gaps, "z+": frame_gaps})
    # the die room: the die itself glowing under a glass lid
    b.box([0.0, 1.0, 0.0], [12.0, 2.0, 12.0], "#4a3a8a", studs=True)
    b.box([0.0, 2.06, 0.0], [10.0, 0.1, 10.0], "#a88aff", material="neon", collide=False)
    strip_light(b, 0.0, 0.0, CPU_TOP, 40.0, "z", "#bfe4ff")
    kit.board_letters(b, 0.0, 8.0, c, "CORE X", 2.4, "#3a3e46", SILK, solid=False)
    kit.board_letters(b, 0.0, 8.0, -c, "CORE X", 2.4, "#3a3e46", SILK, facing="z-", solid=False)
    for h in halves(b):
        for i in range(3):
            for j in (-1, 1):
                b.muster(h.team, h.x(16.5 + 4.6 * i), 0.0, j * 14.0, h.yaw_out, size=4.0)
        h.sign(c - 3.36, 10.0, 0.0, 10.0, 3.0, "sign_%s" % h.team, "x+")
        strip_light(b, h.x(22.0), 0.0, CPU_TOP, 50.0, "z", "#ffe2a8")
        h.box(c + 9.0, 2.0, -15.0, 6.0, 4.0, 6.0, CHIP, studs=True)
        h.box(c + 9.0, 1.6, 15.0, 5.0, 3.2, 5.0, CAP_BLUE, studs=True)


def _heatsink(b: kit.RelayArea) -> None:
    """The heatsink on the CPU's roof: rows of fins, a maze to fight in,
    stairs up at its ends, the fan over it all with its lit ring."""
    c = CPU
    y = CPU_TOP + 1.4
    xs = [-28.0 + k * 7.0 for k in range(9)]
    for x in xs:
        b.box([x, y + (FIN_TOP - y) / 2.0, 0.0], [1.2, FIN_TOP - y, 2 * c - 12.0], ALU,
              material="metal")
    # crossbars through the fins near the ends, overhead
    for z in (-16.0, 16.0):
        b.box([0.0, FIN_TOP - 1.0, z], [58.0, 1.2, 1.2], ALU_DARK, material="metal")
    # the fan: a frame on the fins, a hub, blades, a lit ring
    b.box([0.0, FIN_TOP + 0.6, 0.0], [62.0, 1.2, 62.0], "#2a2e36", collide=False)
    b.cyl([0.0, FIN_TOP + 2.2, 0.0], [10.0, 2.0, 10.0], CHIP, collide=False)
    for k in range(7):
        a = k * 2.0 * math.pi / 7.0
        b.box([math.cos(a) * 13.0, FIN_TOP + 1.8, math.sin(a) * 13.0], [18.0, 0.4, 7.0],
              "#3a3e46", collide=False, r=[0.25, -a, 0.0])
    b.add("torus", [0.0, FIN_TOP + 1.6, 0.0], [50.0, 50.0, 2.0], "#ff4aaa", material="neon",
          collide=False, r=[math.pi / 2.0, 0.0, 0.0])
    # the stairs up to the fins, north and south, mirrored
    for sx in (-1, 1):
        for sz in (-1, 1):
            flight(b, "z", sz * (c + 24.0), sz * c, *sorted((sx * 8.0, sx * 16.0)),
                   0.0, y, ALU_DARK, fill=0.0)


def _centre_parts(b: kit.RelayArea) -> None:
    """On the centre line: the CMOS battery north of the CPU, the
    southbridge and its little heatsink south of it, the screwdriver
    somebody left on the board, a coffee spill."""
    b.cyl([0.0, 2.0, 100.0], [34.0, 4.0, 34.0], SOLDER, material="metal", studs=True)
    b.cyl([0.0, 4.06, 100.0], [30.0, 0.1, 30.0], ALU_DARK, collide=False)
    b.box([0.0, 4.2, 100.0], [10.0, 0.12, 3.0], ALU, collide=False,
          decal=kit.sign_decal("CR2032", ALU, CHIP, 10.0 / 3.0))
    # the southbridge
    b.box([0.0, 1.5, -100.0], [26.0, 3.0, 26.0], CHIP, studs=True)
    for x in range(-10, 12, 4):
        b.box([float(x), 3.0 + 4.0, -100.0], [1.0, 8.0, 22.0], ALU, material="metal")
    # the screwdriver lying across the north of the board
    b.cyl([0.0, 2.4, 160.0], [4.8, 30.0, 4.8], "#c42b20", collide=False,
          r=[math.pi / 2.0, 0.0, 0.0])
    b.box([0.0, 2.4, 160.0], [4.0, 4.8, 30.0], "#c42b20")
    b.box([0.0, 1.0, 184.0], [1.6, 2.0, 20.0], SOLDER, material="metal")
    # the coffee spill, a ring where the mug stood
    b.cyl([0.0, 0.04, -64.0], [22.0, 0.08, 16.0], "#5a3a22", collide=False, material="glass",
          alpha=0.8)


# ================================================================ I/O block
def _io(b: kit.RelayArea, h: Half) -> None:
    """The I/O block at the team's end: the port shield, ports for doors,
    the flag on a chip inside it, the LEDs."""
    x0, x1, z0, z1 = IO
    top = 20.0
    area = h.r(x0, x1, z0, z1)
    room_walls(b, area, 2.0, 0.0, top, ALU,
               doors={h.inward: [(-8.0, 8.0, 10.0)],
                      "z-": [(*h.xs(282.0, 296.0), 9.0)], "z+": [(*h.xs(282.0, 296.0), 9.0)],
                      h.outward: [(-5.0, 5.0, 8.0)]}, material="metal")
    slab(b, area, top + 1.2, 1.2, ALU_DARK, studs=True, material="metal")
    # the port mouths: a coloured tongue over each door, as a port has
    h.box(x0 - 0.3, 11.0, 0.0, 0.6, 1.0, 16.0, "#2a6aa8", collide=False)
    # rows of smaller ports along the inward face, lit
    for k, (zc, colour) in enumerate(((-26.0, "#2a6aa8"), (-18.0, "#2a6aa8"), (18.0, CHIP),
                                       (26.0, "#e8b84a"))):
        h.box(x0 - 0.35, 14.0, zc, 0.7, 3.0, 6.0, CHIP, collide=False)
        h.box(x0 - 0.75, 14.0, zc, 0.1, 1.0, 4.0, colour, collide=False)
    for zc in (-12.0, 12.0):
        h.box(x0 - 0.06, 17.0, zc, 0.1, 0.8, 0.8, LED_GREEN, material="neon", collide=False)
    # the flag on its chip: black, pins round it
    top_y = kit.pedestal(b, h.x(FLAG_X), 0.0, 0.0, h.colour, h.neon, base=CHIP)
    b.flag(h.team, h.x(FLAG_X), top_y, 0.0)
    for k in range(6):
        for side in (-1, 1):
            h.box(FLAG_X - 10.0 + k * 4.0, 0.5, side * 12.6, 1.0, 1.0, 1.2, GOLD, material="metal")
    kit.banner_mast(b, h.x(x1 - 6.0), 48.0, 0.0, 30.0, h.team, h.inward)
    strip_light(b, h.x(FLAG_X), 0.0, top, 60.0, "z", "#e8f0ff")
    # inside: stacked jacks and a heat pipe for cover
    for zz in (-26.0, 26.0):
        h.box(274.0, 3.0, zz, 6.0, 6.0, 8.0, CHIP_LIGHT, studs=True)
    kit.board_letters(b, h.x(x0), top - 3.0, 0.0, "I O", 3.0, ALU, CHIP, facing=h.inward,
                      solid=False)


# ================================================================== caps
def _caps(b: kit.RelayArea, h: Half) -> None:
    """Electrolytic capacitors in clusters: towers, sleeved blue or black,
    their silver tops scored with a cross."""
    rng = random.Random(0xCA9)
    for cx, cz in ((88.0, 72.0), (150.0, -36.0), (214.0, 96.0), (96.0, -66.0), (226.0, -84.0)):
        for k in range(4):
            a = k * math.pi / 2.0 + 0.6
            x, z = cx + math.cos(a) * 7.0, cz + math.sin(a) * 7.0
            r = rng.uniform(4.0, 6.0)
            hgt = rng.uniform(12.0, 22.0)
            colour = CAP_BLUE if k % 2 else CAP_BLACK
            h.cyl(x, hgt / 2.0, z, 2 * r, hgt, 2 * r, colour)
            h.cyl(x, hgt + 0.2, z, 2 * r - 0.4, 0.4, 2 * r - 0.4, SOLDER, material="metal",
                  collide=False)
            h.box(x, hgt + 0.44, z, 2 * r - 1.6, 0.08, 0.4, ALU_DARK, collide=False)
            h.box(x, hgt + 0.44, z, 0.4, 0.08, 2 * r - 1.6, ALU_DARK, collide=False)
            h.box(x - r * 0.62, hgt * 0.5, z, 0.2, hgt * 0.8, r * 0.5, "#e8e8e8", collide=False)


# =================================================================== RAM
def _ram(b: kit.RelayArea, h: Half) -> None:
    """Four RAM sticks in their slots, north: long blocks with lanes
    between them, chips on their faces, clips at their ends."""
    for k in range(4):
        x = 104.0 + k * 12.0
        h.box(x, 1.0, 120.0, 3.0, 2.0, 64.0, CHIP_LIGHT, studs=True)
        h.box(x, 2.0 + 7.0, 120.0, 1.2, 14.0, 60.0, "#1a3a2a")
        for j in range(4):
            z = 96.0 + j * 16.0
            for side in (-1, 1):
                h.box(x + side * 0.9, 9.0, z, 0.6, 6.0, 10.0, CHIP, collide=False)
        h.box(x, 16.4, 120.0, 1.4, 0.8, 60.0, "#e8c050" if k % 2 else "#8a929a",
              material="metal", collide=False)
        for z in (88.0, 152.0):
            h.box(x, 3.0, z, 3.0, 2.0, 2.0, "#e8e8e8")


# =================================================================== GPU
def _gpu(b: kit.RelayArea, h: Half) -> None:
    """A graphics card standing in its slot, south: a wall with two fans on
    its face, a backplate, a power connector -- and a gap at the slot's end
    to run through."""
    x0, x1 = 80.0, 196.0
    z = -118.0
    h.box((x0 + x1) / 2.0, 1.0, z, x1 - x0 + 6.0, 2.0, 4.0, CHIP_LIGHT, studs=True)
    h.box((x0 + x1) / 2.0, 2.0 + 13.0, z, x1 - x0, 26.0, 3.0, "#2a2e36")
    for fx in (110.0, 166.0):
        h.cyl(fx, 15.0, z + 1.6, 20.0, 0.4, 20.0, "#1b1d22", collide=False,
              r=[math.pi / 2.0, 0.0, 0.0])
        h.cyl(fx, 15.0, z + 1.85, 6.0, 0.2, 6.0, "#ff4a2a", collide=False, material="neon",
              r=[math.pi / 2.0, 0.0, 0.0])
    h.box((x0 + x1) / 2.0, 28.4, z, x1 - x0, 0.8, 3.4, "#c42b20", collide=False)
    h.box(x1 - 10.0, 29.6, z, 6.0, 1.6, 2.0, CHIP)
    kit.board_letters(b, h.x((x0 + x1) / 2.0), 24.0, z + 1.5, "RTX", 2.4, "#2a2e36", "#4aff7a",
                      facing="z+", solid=False, depth=0.1)


# =================================================================== VRMs
def _vrms(b: kit.RelayArea, h: Half) -> None:
    """The voltage regulators north and south of the way to the CPU: where a
    team falls back to while its flag is out.  A heatsink on each."""
    for sz in (-1, 1):
        zlo, zhi = sorted((sz * 40.0, sz * 74.0))
        kit.outpost_room(h, 166.0, 204.0, zlo, zhi, 0.0, "#3a3e46", ALU, height=10.0,
                         door_w=10.0, pads=2, lights="#bfe4ff")
        for k in range(5):
            h.box(170.0 + k * 7.0, 11.2 + 3.0, (zlo + zhi) / 2.0, 1.0, 6.0, zhi - zlo - 4.0, ALU,
                  material="metal")


# ================================================================== chips
def _chips(b: kit.RelayArea, h: Half) -> None:
    """Chips, chokes, resistors and pin headers about the board: low cover
    everywhere, a step up onto most of it."""
    for x, z, w, d in ((60.0, 40.0, 14.0, 10.0), (130.0, 10.0, 10.0, 10.0), (240.0, 60.0, 12.0, 8.0),
                       (60.0, -36.0, 12.0, 12.0), (236.0, -56.0, 10.0, 14.0)):
        h.box(x, 1.0, z, w, 2.0, d, CHIP, studs=True)
        for k in range(int(w // 2)):
            for side in (-1, 1):
                h.box(x - w / 2.0 + 1.0 + k * 2.0, 0.3, z + side * (d / 2.0 + 0.5), 0.8, 0.6, 1.0,
                      SOLDER, material="metal")
        h.cyl(x - w / 2.0 + 2.0, 2.04, z + d / 2.0 - 2.0, 1.2, 0.08, 1.2, SILK, collide=False)
    for x, z in ((180.0, 140.0 - 20.0), (190.0, 10.0)):
        h.box(x, 3.0, z, 8.0, 6.0, 8.0, "#3a3a3a", studs=True)
        h.cyl(x, 3.0, z, 7.4, 4.0, 7.4, "#c87a3a", material="metal", collide=False)
    for x, z in ((120.0, 40.0), (240.0, 20.0)):
        h.box(x, 1.4, z, 10.0, 2.8, 2.8, "#d8c8a0")
        for k, colour in enumerate(("#8a4a2a", "#1b1b1b", "#c42b20", GOLD)):
            h.box(x - 3.0 + k * 2.0, 1.4, z, 0.8, 2.9, 2.9, colour, collide=False)
    for x0, z0 in ((150.0, 80.0), (60.0, 100.0)):
        for i in range(5):
            for j in range(2):
                h.box(x0 + i * 2.4, 2.0, z0 + j * 2.4, 0.8, 4.0, 0.8, GOLD, material="metal")
        h.box(x0 + 4.8, 0.5, z0 + 1.2, 12.0, 1.0, 4.4, CHIP)
    # LEDs blinking on the board
    for x, z, colour in ((70.0, 0.0, LED_GREEN), (140.0, -20.0, LED_RED), (250.0, 0.0, LED_GREEN)):
        h.box(x, 0.4, z, 1.0, 0.8, 1.0, colour, material="neon")


# ================================================================= traces
def _traces(b: kit.RelayArea, h: Half) -> None:
    """Copper traces: the board's streets, lit, in runs that turn at right
    angles from the CPU out to everything else."""
    runs = [((CPU + 6.0, 4.0), (262.0, 4.0)), ((CPU + 6.0, -4.0), (262.0, -4.0)),
            ((CPU + 6.0, 20.0), (120.0, 20.0)), ((120.0, 20.0), (120.0, 86.0)),
            ((CPU + 6.0, -22.0), (96.0, -22.0)), ((96.0, -22.0), (96.0, -112.0)),
            ((150.0, 4.0), (150.0, -28.0)), ((200.0, -4.0), (200.0, -34.0)),
            ((214.0, 4.0), (214.0, 84.0)), ((60.0, 40.0), (60.0, 90.0)),
            ((24.0, CPU + 6.0), (24.0, 78.0)), ((24.0, -CPU - 6.0), (24.0, -84.0))]
    for i, ((xa, za), (xb, zb)) in enumerate(runs):
        t = 0.08 + 0.012 * i          # every run its own height: crossings never fight
        if abs(za - zb) < 1e-6:
            lo, hi = sorted((xa, xb))
            h.box((lo + hi) / 2.0, t / 2.0, za, hi - lo, t, 1.2, COPPER, material="neon",
                  collide=False)
        else:
            lo, hi = sorted((za, zb))
            h.box(xa, t / 2.0, (lo + hi) / 2.0, 1.2, t, hi - lo, COPPER, material="neon",
                  collide=False)
    # vias: little rings of solder where traces dive through the board
    for x, z in ((80.0, 4.0), (180.0, -4.0), (120.0, 60.0), (96.0, -80.0)):
        h.cyl(x, 0.06, z, 2.2, 0.12, 2.2, SOLDER, collide=False)
    h.box(140.0, 0.05, 30.0, 14.0, 0.1, 4.0, "#e8e8e8", collide=False,
          decal=kit.sign_decal("VOID IF REMOVED", "#e8e8e8", "#c42b20", 14.0 / 4.0))


# =================================================================== case
def _case(b: kit.RelayArea, rng: random.Random) -> None:
    """The computer case all round: steel walls, the side window, and the
    room outside it -- a desk lamp, a mug, a sleeping cat's tail."""
    hx, hz, m = HALF[0], HALF[1], b.margin
    room_walls(b, rect(-hx - m, hx + m, -hz - m, hz + m), m, 0.0, 60.0, "#3a3e46",
               material="metal")
    # the window panel in the north wall's top: the room beyond
    b.box([0.0, 70.0, hz + m / 2.0], [400.0, 20.0, m + 0.4], "#9fd8e8", collide=False,
          material="glass", alpha=0.3)
    b.box([0.0, 81.0, hz + m / 2.0], [404.0, 2.0, m + 0.8], "#2a2e36", collide=False)
    # the desk the case stands on, the lamp leaning over, its light on
    b.box([0.0, 30.0, hz + m + 100.0], [900.0, 60.0, 200.0], "#6a4a32", collide=False)
    b.box([-160.0, 100.0, hz + m + 60.0], [8.0, 80.0, 8.0], "#2a2e36", collide=False)
    b.box([-128.0, 144.0, hz + m + 60.0], [72.0, 8.0, 8.0], "#2a2e36", collide=False)
    b.cone([-96.0, 128.0, hz + m + 60.0], [30.0, 24.0, 30.0], "#2a2e36", collide=False)
    b.sphere([-96.0, 118.0, hz + m + 60.0], [14.0, 8.0, 14.0], "#fff0c8", material="neon",
             collide=False)
    # the mug
    b.cyl([140.0, 100.0, hz + m + 50.0], [60.0, 80.0, 60.0], "#e8e8e8", collide=False)
    b.cyl([140.0, 140.2, hz + m + 50.0], [54.0, 0.4, 54.0], "#4a2a1a", collide=False)
    # rows of RGB along the case floor's edge
    for k in range(24):
        x = -hx + 14.0 + k * (2 * hx - 28.0) / 23.0
        for sz in (-1, 1):
            b.box([x, 60.6, sz * (hz + m / 2.0)], [8.0, 1.2, 1.6],
                  ["#ff4aaa", "#4aaaff", "#4aff7a"][k % 3], material="neon", collide=False)
    del rng


def _landmarks(b: kit.RelayArea) -> None:
    for x, z, name in ((0, 0, "the CPU"), (0, 0, "the fins"), (0, 100, "the battery"),
                       (0, -100, "the southbridge"), (0, 160, "the screwdriver")):
        b.landmark(float(x), float(z), name)
    for sx, team in ((-1, "red"), (1, "blue")):
        b.landmark(sx * 289.0, 0.0, "the %s I/O block" % team)
        for x, z, name in ((122, 120, "the RAM"), (138, -118, "the graphics card"),
                           (185, 57, "the north VRM"), (185, -57, "the south VRM"),
                           (150, -36, "the capacitors")):
            b.landmark(sx * float(x), float(z), "%s (%s side)" % (name, team))
    b.camera(-150.0, 70.0, 150.0, 0.0, 10.0, 0.0)
    b.camera(150.0, 70.0, -150.0, 0.0, 10.0, 0.0)
    b.camera(0.0, 80.0, -180.0, 0.0, 14.0, 0.0)
