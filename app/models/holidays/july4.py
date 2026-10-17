"""The Fourth of July: fireworks, flags and the cookout that gets out of hand.

Blockhaven has kept the Fourth every summer since its first, the week either
side of it (June 27th to July 11th):

  2022  Star-Spangled Blast   the first Fourth: a powder keg, bunting, the flag
  2023  Backyard Cookout      a kettle grill, the picnic, the lawn and the ants
  2024  Liberty Lights        the torch, tin lanterns and a summer night
  2025  Rocket's Red Glare    a star fort, its garrison flag and the night barrage
  2026  America 250           the semiquincentennial: the Liberty Bell, the quill
                              and two hundred and fifty candles
"""
from __future__ import annotations

import math

from .kit import (BLACK, BONE, BRASS, GOLD, GOLD_DARK, IRON, PI, SILVER, SNOW, TAU, WHITE,
                  Event, around, at_frame, band, buckle, cap, dome, gift_bow, mix, part,
                  place, pompom, reach, ringband, rod, rotate, shade, sides, straps)

RED = "#c8202f"
NAVY = "#22306e"
BLUE = "#2f5fc4"
CREAM = "#f6f1e3"
STRAW = "#e3c47a"


# ============================================================ shared bits
def _flag(at, k=1.0, yaw=0.0, pole=1.0, decal="jl_flag", finial=GOLD, c=WHITE):
    """A flag on its pole: ``at`` is the foot of the pole, the flag flies
    from the top of it towards +X turned by ``yaw``."""
    x, y, z = at
    h = pole * k
    out = [
        part("cyl", [x, y + h / 2, z], [0.06 * k, h, 0.06 * k], "#d9d2c0", m="metal"),
        part("sph", [x, y + h + 0.05 * k, z], [0.13 * k, 0.13 * k, 0.13 * k], finial, m="metal"),
        place("flag", [x, y + h - 0.02 * k, z], [0.80 * k, 0.80 * k, 0.80 * k], c,
              anchor=[-0.5, 0.30, 0], r=[0, yaw, 0], decal=decal, wrap=True),
    ]
    return out


def _bunting(at, k=1.0, yaw=0.0, colours=(RED, WHITE, NAVY), **kw):
    """A fan of pleated bunting hanging from ``at``: red outside, white, and
    the blue at its heart, facing +Z turned by ``yaw``."""
    out = []
    for n, (c, s) in enumerate(zip(colours, (1.0, 0.70, 0.40))):
        off = rotate([0, 0, 0.012 * n * k], [0, yaw, 0])
        out.append(place("fan", [at[0] + off[0], at[1], at[2] + off[2]], [s * k, s * k, k], c,
                         anchor=[0, 0, 0], r=[0, yaw, PI], **kw))
    off = rotate([0, 0, 0.05 * k], [0, yaw, 0])
    out.append(part("sph", [at[0] + off[0], at[1] - 0.02 * k, at[2] + off[2]],
                    [0.09 * k, 0.09 * k, 0.09 * k], GOLD, m="metal", **kw))
    return out


def _rosette(at, k=1.0, yaw=0.0, colours=(RED, WHITE, NAVY), tails=True):
    """A ribbon cockade: three rings of colour and two tails, facing +Z
    turned by ``yaw``."""
    x, y, z = at
    out = []
    for n, (c, s) in enumerate(zip(colours, (0.34, 0.24, 0.14))):
        off = rotate([0, 0, 0.012 * n * k], [0, yaw, 0])
        out.append(part("cyl", [x + off[0], y, z + off[2]], [s * k, 0.03 * k, s * k], c,
                        [PI / 2, yaw, 0]))
    if tails:
        for side in (1, -1):
            out.append(place("ribbon", [x + rotate([0.04 * side * k, 0, 0], [0, yaw, 0])[0],
                                        y - 0.06 * k,
                                        z + rotate([0.04 * side * k, 0, 0], [0, yaw, 0])[2]],
                             [0.10 * k, 0.26 * k, 0.05 * k], colours[0], anchor=[0, 0.5, 0],
                             r=[0, yaw, 0.30 * side]))
    return out


def _rod(p0, p1, w, c, t="cyl", **kw):
    """A rod from point ``p0`` to point ``p1``, ``w`` thick: a straw, a strut,
    a tube."""
    d = [p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]]
    length = math.sqrt(sum(v * v for v in d)) or 1e-6
    rx = math.acos(max(-1.0, min(1.0, d[1] / length)))
    ry = math.atan2(d[0], d[2])
    mid = [(p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2, (p0[2] + p1[2]) / 2]
    return part(t, mid, [w, length, w], c, [rx, ry, 0], **kw)


def _cracker(at, k=1.0, c=RED, r=None, lit=False):
    """A firecracker: a paper tube with frilled ends and a fuse."""
    x, y, z = at
    r = r or [0, 0, 0]
    tip = rotate([0, 0.52 * k, 0], r)
    out = [place("cracker", [x, y, z], [0.36 * k, 0.70 * k, 0.36 * k], c, r=r,
                 decal="firecracker", wrap=True),
           part("cyl", [x + tip[0], y + tip[1], z + tip[2]], [0.03 * k, 0.24 * k, 0.03 * k],
                "#3a2e22", r)]
    if lit:
        end = rotate([0, 0.66 * k, 0], r)
        out.append(place("sparkle", [x + end[0], y + end[1], z + end[2]], 0.22 * k, "#fff6c9",
                         m="neon", spin=6.0))
    return out


# ============================================================ 2022
JL22 = Event(
    "july4_2022", "july4", 2022, "jl22",
    name="Star-Spangled Blast", title="The Star-Spangled Blast",
    blurb="Blockhaven's very first Fourth of July. Somebody rolled a powder keg into "
          "the town square, hung bunting off everything that would hold still, and "
          "lit the fuse at dusk. The square has not been quite the same shape since.",
    tagline="Light the fuse. Wave the flag. Mind the eyebrows.",
    starts="2022-06-27", ends="2022-07-11",
    colors={"accent": RED, "deep": "#0b1233", "glow": "#fff3e0"},
    family_effects=["starstruck", "ember_storm", "sunbeam", "static_charge"],
    hero_effect="spangled_salute", stencil="stencil_jl22")


@JL22.crate_model("Powder Keg Crate",
                  "An oak powder keg bound in iron and draped in bunting, its fuse already "
                  "fizzing in the bung. Holds the Star-Spangled Blast set. Needs a Liberty "
                  "Star Key.",
                  hinge=[0, 0.62, -0.70], keyhole=[0, -0.06, 0.86])
def _():
    oak, iron = "#9a6236", "#3a3d42"
    parts = [
        # the keg: staves bellied out, iron hoops round it
        place("cask", [0, -0.72, 0], [1.62, 1.32, 1.62], oak, anchor=[0, 0, 0],
              decal="jl_staves", wrap=True),
        part("torus", [0, -0.56, 0], [1.50, 0.07, 1.50], iron, m="metal"),
        part("torus", [0, -0.34, 0], [1.60, 0.07, 1.60], iron, m="metal"),
        part("torus", [0, 0.22, 0], [1.60, 0.07, 1.60], iron, m="metal"),
        part("torus", [0, 0.48, 0], [1.50, 0.07, 1.50], iron, m="metal"),
        # the head of the keg is the lid, with its hoop, the bung and the fuse
        part("cyl", [0, 0.60, 0], [1.38, 0.06, 1.38], shade(oak, 0.86), lid=1,
             decal="jl_staves", wrap=True),
        part("torus", [0, 0.62, 0], [1.40, 0.08, 1.40], iron, m="metal", lid=1),
        part("cyl", [0.28, 0.68, 0.18], [0.20, 0.10, 0.20], "#5a3a22", lid=1),
        place("spiral", [0.28, 0.70, 0.18], [0.20, 0.30, 0.20], "#3a2e22", anchor=[0, -0.5, 0],
              lid=1),
        place("sparkle", [0.28, 1.06, 0.18], 0.34, "#fff6c9", m="neon", spin=5.0, lid=1),
        part("sph", [0.28, 1.04, 0.18], [0.12, 0.12, 0.12], "#ffcf3a", m="neon", lid=1),
        place("star", [-0.20, 0.64, 0.16], [0.46, 0.46, 0.3], GOLD, r=[-PI / 2, 0, 0],
              m="metal", lid=1),
        # the light waiting under the lid
        part("cyl", [0, 0.605, 0], [1.28, 0.01, 1.28], "#fff3e0", m="neon"),
        # the lock: a brass plate on the belly, the stencil on a tag at the back
        part("rbox", [0, -0.06, 0.80], [0.36, 0.40, 0.10], BRASS, m="metal", decal="keyhole",
             lock=1),
        part("rbox", [0, -0.06, -0.80], [0.84, 0.62, 0.05], "#d8c08a", decal="planks"),
        part("box", [0, -0.06, -0.83], [0.80, 0.58, 0.02], "#000000", [0, PI, 0],
             decal="stencil_jl22", a=-1),
    ]
    for x in (-0.36, 0.36):
        parts.append(part("cyl", [x, 0.20, -0.82], [0.05, 0.03, 0.05], iron, [PI / 2, 0, 0],
                          m="metal"))
    # bunting hung from the top hoop all the way round, and a gold star over the lock
    for yaw in (PI / 4, -PI / 4, 3 * PI / 4, -3 * PI / 4, PI / 2, -PI / 2):
        r = 0.80 if abs(abs(yaw) - PI / 2) < 0.1 else 0.79
        at = [math.sin(yaw) * r, 0.46, math.cos(yaw) * r]
        parts += _bunting(at, 0.86, yaw)
    parts.append(place("star", [0, 0.30, 0.83], 0.30, GOLD, r=[-0.08, 0, 0], m="metal"))
    # and two little flags stuck in the lid
    parts += [dict(p, lid=1) for p in _flag([-0.42, 0.62, -0.30], 0.70, yaw=0.5, pole=1.0)]
    parts += [dict(p, lid=1) for p in _flag([0.46, 0.62, -0.26], 0.62, yaw=-0.3, pole=0.9)]
    return parts


@JL22.key_model("Liberty Star Key",
                "A gold key with a star for a bow, a ribbon of red, white and blue tied "
                "at the throat, and teeth cut like a flag in the wind. Opens one Powder "
                "Keg Crate.", shoulder=-0.30)
def _():
    return [
        place("star", [-0.66, 0.0, 0], 0.66, GOLD, m="metal"),
        part("cyl", [-0.66, 0.0, 0.05], [0.30, 0.04, 0.30], NAVY, [PI / 2, 0, 0]),
        place("star", [-0.66, 0.0, 0.08], 0.22, WHITE),
        part("cyl", [0.10, 0, 0], [0.10, 1.04, 0.10], GOLD, [0, 0, PI / 2], m="metal"),
        part("torus", [-0.28, 0, 0], [0.22, 0.08, 0.22], GOLD_DARK, [0, 0, PI / 2], m="metal"),
        place("ribbon", [-0.30, -0.08, 0.06], [0.12, 0.34, 0.05], RED, anchor=[0, 0.5, 0],
              r=[0, 0, 0.35]),
        place("ribbon", [-0.26, -0.08, 0.04], [0.12, 0.30, 0.05], NAVY, anchor=[0, 0.5, 0],
              r=[0, 0, -0.25]),
        # the bit: three stripes stepping down
        part("rbox", [0.40, -0.11, 0], [0.08, 0.20, 0.08], RED),
        part("rbox", [0.50, -0.14, 0], [0.08, 0.26, 0.08], WHITE),
        part("rbox", [0.60, -0.11, 0], [0.08, 0.20, 0.08], RED),
        place("star", [0.68, 0.0, 0], 0.16, GOLD, m="metal"),
    ]


@JL22.hat("uncle_sam", "Uncle Sam's Topper",
          "Tall, white, striped like a barber's pole and banded with stars. Put it on "
          "and you start pointing at people. You cannot help it. He wants them.",
          "legendary")
def _():
    parts = [
        place("brim", [0, -0.05, 0], [2.20, 1.6, 2.10], NAVY, anchor=[0, 0, 0],
              decal="jl_starsprinkle", wrap=True),
        place("flare", [0, 0.0, 0], [1.40, 1.62, 1.34], WHITE, anchor=[0, 0, 0],
              decal="jl_vstripes", wrap=True),
        part("cyl", [0, 0.24, 0], [1.29, 0.36, 1.23], NAVY, decal="jl_starband", wrap=True),
        part("cyl", [0, 0.07, 0], [1.31, 0.05, 1.25], GOLD, m="metal"),
        part("cyl", [0, 0.42, 0], [1.31, 0.05, 1.25], GOLD, m="metal"),
        place("star", [0, 0.25, 0.64], 0.30, GOLD, r=[-0.05, 0, 0], m="metal"),
    ]
    parts += _rosette([0.60, 0.26, 0.30], 0.9, yaw=1.1)
    return parts


@JL22.hat("flag_helmet", "First Flag",
          "The first flag ever planted on Blockhaven went up on the first Fourth. It "
          "went up on a helmet, on a head, and it has not been taken down since.",
          "legendary")
def _():
    parts = [
        dome(-0.30, 0.84, NAVY, t="capcrown", decal="jl_starsprinkle", wrap=True),
        ringband(-0.20, 0.16, RED),
        ringband(-0.25, 0.05, WHITE, margin=0.05),
        part("rbox", [0, 0.50, 0], [0.12, 0.10, 1.40], GOLD, [0.0, 0, 0], m="metal"),
        part("cyl", [0, 0.52, 0], [0.30, 0.12, 0.30], GOLD, m="metal"),
        part("sph", [0, 0.58, 0], [0.18, 0.12, 0.18], GOLD, m="metal"),
    ]
    parts += _flag([0, 0.58, 0], 1.80, yaw=0.55, pole=1.05)
    parts += _rosette([0, -0.18, 0.92], 0.7)
    return parts


@JL22.hat("bunting_boater", "Bunting Boater",
          "A straw boater for the parade, with a hatband of red, white and blue and "
          "a fan of bunting pinned on the side. Pairs well with a brass band.", "rare")
def _():
    parts = [
        place("brim", [0, -0.05, 0], [2.24, 0.9, 2.14], STRAW, anchor=[0, 0, 0],
              decal="jl_straw", wrap=True),
        part("cyl", [0, 0.22, 0], [1.38, 0.50, 1.32], STRAW, decal="jl_straw", wrap=True),
        part("cyl", [0, 0.475, 0], [1.38, 0.02, 1.32], shade(STRAW, 0.92)),
        part("cyl", [0, 0.12, 0], [1.40, 0.22, 1.34], WHITE, decal="jl_bandstripe", wrap=True),
    ]
    parts += _bunting([0.60, 0.22, 0.32], 0.42, yaw=1.08)
    parts += _flag([-0.58, 0.12, -0.20], 0.50, yaw=-2.3, pole=1.1)
    return parts


@JL22.hat("fan_wig", "Spangled Fan Wig",
          "A huge curly wig in red, white and blue, from the stands of the first "
          "fireworks show. It sheds stars. Nobody sitting behind you can see a thing.",
          "rare", hair="hide")
def _():
    parts = [dome(-0.36, 0.80, NAVY, decal="fur", wrap=True)]
    rows = ((0.50, 0.0, 1, 0.46), (0.40, 0.36, 7, 0.42), (0.22, 0.66, 11, 0.42),
            (-0.02, 0.88, 16, 0.42), (-0.30, 1.00, 18, 0.40), (-0.62, 1.02, 18, 0.38))
    for ring, (y, radius, count, s) in enumerate(rows):
        for n in range(count):
            a = n * TAU / count + ring * 0.4
            x = math.sin(a) * radius
            z = math.cos(a) * radius * 0.96
            if z > 0.40 and y < -0.10:
                continue
            # the flag in curls: a blue canton front-left, stripes elsewhere
            canton = x < -0.05 and z > -0.10 and y > 0.10
            c = NAVY if canton else (RED if (ring + n) % 2 else WHITE)
            parts.append(part("sph", [x, y, z], [s, s * 0.92, s], c, decal="fur", wrap=True))
            if canton and n % 2 == 0:
                parts.append(place("star", [x * 1.2, y + 0.08, z * 1.2], 0.14, WHITE,
                                   r=[0, a, 0]))
    return parts


@JL22.hat("assortment_box", "Family Assortment",
          "Thirty-six shots of fireworks in a cardboard box, worn on the head so both "
          "hands are free for the lighter. Read the label. Then read it again.", "rare")
def _():
    colours = [RED, BLUE, "#f5c518", "#2fa84f", "#b26bff", WHITE]
    parts = [
        part("rbox", [0, 0.24, 0], [1.66, 0.62, 1.58], RED, decal="jl_fwbox", wrap=True),
        part("box", [0, 0.24, 0.80], [0.80, 0.56, 0.02], "#000000", decal="jl_assortment", a=-1),
        part("rbox", [0, 0.56, 0], [1.60, 0.04, 1.52], "#c9a24a"),
    ]
    k = 0
    for gx in (-0.48, 0.0, 0.48):
        for gz in (-0.42, 0.0, 0.42):
            h = 0.30 + ((k * 7) % 5) * 0.08
            c = colours[k % 6]
            parts.append(part("cyl", [gx, 0.58 + h / 2, gz], [0.34, h, 0.34], c,
                              decal="party", wrap=True))
            parts.append(part("cyl", [gx, 0.58 + h, gz], [0.24, 0.02, 0.24], "#2b2b30"))
            parts.append(part("cyl", [gx + 0.08, 0.66 + h, gz], [0.025, 0.16, 0.025],
                              "#3a2e22", [0, 0, -0.4]))
            k += 1
    parts += [place("sparkle", [0.58, 1.12, 0.42], 0.30, "#fff6c9", m="neon", spin=5.0),
              part("sph", [0.56, 1.10, 0.42], [0.10, 0.10, 0.10], "#ffcf3a", m="neon"),
              part("sph", [0.40, 1.30, 0.30], [0.30, 0.22, 0.28], "#d9dce2", a=0.6),
              part("sph", [0.30, 1.50, 0.20], [0.20, 0.16, 0.20], "#e3e6ea", a=0.45)]
    return parts


@JL22.hat("star_boppers", "Star Boppers",
          "A headband with two glitter stars on springs. They bob when you walk, "
          "bounce when you jump, and wobble for a full minute after every firework.",
          "uncommon", hair="show")
def _():
    parts = [band(-0.12, 0.16, RED, grow=-0.04, decal="sequins", wrap=True),
             band(-0.12, 0.05, WHITE, grow=-0.02)]
    for side, c in ((1, RED), (-1, BLUE)):
        lean = [0.10, 0, -0.38 * side]
        root = [0.56 * side, -0.02, 0.06]
        parts.append(place("cyl", root, [0.10, 0.08, 0.10], WHITE))
        parts.append(place("spiral", root, [0.26, 0.74, 0.26], SILVER, anchor=[0, -0.5, 0],
                           r=lean, m="metal"))
        tip = rotate([0, 0.82, 0], lean)
        at = [root[0] + tip[0], root[1] + tip[1] + 0.20, root[2] + tip[2]]
        parts.append(place("star", at, [0.80, 0.80, 2.2], c, r=[0, 0, -0.25 * side],
                           decal="sequins", m="metal"))
        parts.append(place("star", [at[0], at[1] + 0.02, at[2] + 0.17], 0.36, WHITE, m="neon",
                           r=[0, 0, -0.25 * side]))
    return parts


@JL22.hat("star_shades", "Star-Spangled Shades",
          "Sunglasses shaped like stars: one red, one blue, both entirely unsuitable "
          "for looking at fireworks, which is what everybody uses them for.", "uncommon",
          hair="show")
def _():
    parts = []
    for side, c in ((1, BLUE), (-1, RED)):
        x = 0.30 * side
        parts += [place("star", [x, -0.46, 0.76], 0.50, c, r=[0, 0, 0.12 * side], m="metal"),
                  place("star", [x, -0.46, 0.79], 0.38, "#1a1d2a", r=[0, 0, 0.12 * side],
                        m="glass", a=0.85),
                  place("star", [x - 0.06 * side, -0.40, 0.81], 0.10, WHITE, m="neon", a=0.8)]
        # the arm back to the ear
        parts.append(part("rbox", [0.76 * side, -0.42, 0.36], [0.05, 0.06, 0.78], c, m="metal"))
    parts.append(part("rbox", [0, -0.44, 0.78], [0.18, 0.05, 0.05], WHITE, m="metal"))
    return parts


@JL22.back("flag_cape", "Star-Spangled Cape",
           "The flag, worn as a cape, the way it was on the first night when the big "
           "ones went up and everyone had something to wave.", "rare")
def _():
    return [
        place("cape", [0, 0.98, -0.08], [1.70, 1.92, 1.5], WHITE, anchor=[0, 0, 0],
              decal="jl_flagcape", wrap=True),
        part("rbox", [0, 0.96, -0.14], [1.40, 0.14, 0.16], NAVY),
        place("star", [0.48, 0.96, -0.24], 0.24, GOLD, r=[0, PI, 0], m="metal"),
        place("star", [-0.48, 0.96, -0.24], 0.24, GOLD, r=[0, PI, 0], m="metal"),
    ]


@JL22.back("keg_pack", "Keg on My Back",
           "A little powder keg on a pair of straps, fuse lit, bunting tied round its "
           "middle. Everybody gives you a lot of room in the queue.", "legendary")
def _():
    oak, iron = "#9a6236", "#3a3d42"
    zc = -0.72
    parts = [
        place("cask", [0, -0.50, zc], [1.30, 1.40, 1.30], oak, anchor=[0, 0, 0],
              decal="jl_staves", wrap=True),
        part("torus", [0, -0.36, zc], [1.20, 0.07, 1.20], iron, m="metal"),
        part("torus", [0, 0.76, zc], [1.20, 0.07, 1.20], iron, m="metal"),
        part("cyl", [0, 0.89, zc], [1.08, 0.04, 1.08], shade(oak, 0.85)),
        part("rbox", [0, 0.30, -0.08], [0.86, 0.18, 0.14], "#3a2a1c"),
        part("cyl", [0.22, 0.94, zc - 0.04], [0.16, 0.10, 0.16], "#5a3a22"),
        place("spiral", [0.22, 0.96, zc - 0.04], [0.18, 0.40, 0.18], "#3a2e22",
              anchor=[0, -0.5, 0]),
        place("sparkle", [0.22, 1.42, zc - 0.04], 0.36, "#fff6c9", m="neon", spin=5.0),
        part("sph", [0.22, 1.40, zc - 0.04], [0.12, 0.12, 0.12], "#ffcf3a", m="neon"),
        part("rbox", [0, -0.06, zc - 0.66], [0.56, 0.38, 0.02], CREAM, [0, PI, 0],
             decal="jl_xxx"),
        *straps("#3a2a1c", 0.34, 0.13),
    ]
    for yaw in (PI, PI * 0.72, -PI * 0.72, PI / 2, -PI / 2):
        parts += _bunting([math.sin(yaw) * 0.64, 0.74, zc + math.cos(yaw) * 0.64], 0.62, yaw=yaw)
    return parts


@JL22.hairdo("spangled_mohawk", "Spangled Mohawk",
             "Shaved at the sides and spiked down the middle in stripes of red, white "
             "and blue. Took three cans of hair gel and most of the afternoon.", "rare")
def _():
    c = "#2a1e16"
    parts = [place("hairshort", [0, 0, 0], [1.0, 1.0, 1.0], c, anchor=[0, 0, 0],
                   decal="strands", wrap=True)]
    colours = [RED, WHITE, BLUE]
    for n, z in enumerate((0.30, 0.16, 0.02, -0.12, -0.26, -0.40)):
        h = 0.34 + 0.10 * math.sin((n + 1) / 7 * PI)
        y = 0.52 if z > -0.30 else 0.46
        parts.append(place("tri", [0, y - 0.02, z], [0.30, h / 0.9, 0.9], colours[n % 3],
                           anchor=[0, -0.40, 0], r=[-0.25 + n * 0.10, PI / 2, 0]))
    return parts


@JL22.hairdo("liberty_pigtails", "Liberty Pigtails",
             "Two bouncing pigtails tied off with red and blue bows and a gold star clip "
             "each. Made for running to the front for the best view.", "uncommon")
def _():
    c = "#a8642a"
    parts = [place("hairmid", [0, 0, 0], [1.02, 1.02, 1.02], c, anchor=[0, 0, 0],
                   decal="strands", wrap=True)]
    for side, bow in ((1, RED), (-1, BLUE)):
        parts += [
            part("sph", [0.62 * side, 0.08, -0.08], [0.30, 0.30, 0.30], c, decal="strands",
                 wrap=True),
            place("teardrop", [0.74 * side, -0.02, -0.10], [0.34, 0.66, 0.32], c,
                  anchor=[0, 0.85, 0], r=[0, 0, -0.35 * side], decal="strands", wrap=True),
            place("bowtie", [0.66 * side, 0.20, -0.08], [0.34, 0.34, 1.0], bow,
                  r=[0, PI / 2 * side, 0]),
            place("star", [0.585 * side, 0.30, 0.16], 0.17, GOLD, r=[0, PI / 2 * side, 0],
                  m="metal"),
        ]
    return parts


JL22.face("ooh_aah", "Ooh! Aah!",
          "Eyes wide, mouth open, a firework going off in each pupil. The face of "
          "everybody in the square at nine o'clock on the first Fourth.", [
              {"k": "ellipse", "x": -0.21, "y": -0.14, "w": 0.17, "h": 0.20, "c": "#ffffff"},
              {"k": "ellipse", "x": 0.21, "y": -0.14, "w": 0.17, "h": 0.20, "c": "#ffffff"},
              {"k": "ring", "x": -0.21, "y": -0.14, "r": 0.09, "w": 0.025, "c": "#16171b"},
              {"k": "ring", "x": 0.21, "y": -0.14, "r": 0.09, "w": 0.025, "c": "#16171b"},
              {"k": "star", "x": -0.21, "y": -0.14, "r": 0.06, "n": 8, "i": 0.35, "c": "#c8202f"},
              {"k": "star", "x": 0.21, "y": -0.14, "r": 0.06, "n": 8, "i": 0.35, "c": "#2f5fc4"},
              {"k": "ellipse", "x": 0, "y": 0.17, "w": 0.13, "h": 0.17, "c": "#16171b"},
              {"k": "ellipse", "x": 0, "y": 0.21, "w": 0.07, "h": 0.06, "c": "#c4281c"},
              {"k": "arc", "x": -0.21, "y": -0.33, "r": 0.08, "a0": 0.60, "a1": 0.90, "w": 0.03,
               "c": "#16171b"},
              {"k": "arc", "x": 0.21, "y": -0.33, "r": 0.08, "a0": 0.60, "a1": 0.90, "w": 0.03,
               "c": "#16171b"},
          ])
JL22.face("face_paint", "Face Paint",
          "A little flag painted on one cheek, a gold star on the other, and the grin "
          "of somebody who did it themselves in the mirror.", [
              {"k": "ellipse", "x": -0.20, "y": -0.13, "w": 0.07, "h": 0.10, "c": "#16171b"},
              {"k": "ellipse", "x": 0.20, "y": -0.13, "w": 0.07, "h": 0.10, "c": "#16171b"},
              {"k": "arc", "x": 0, "y": 0.0, "r": 0.24, "a0": 0.08, "a1": 0.42, "w": 0.05,
               "c": "#16171b"},
              {"k": "rect", "x": -0.30, "y": 0.10, "w": 0.24, "h": 0.16, "c": "#f4f6f8",
               "rot": -0.12},
              {"k": "rect", "x": -0.30, "y": 0.054, "w": 0.24, "h": 0.035, "c": "#c8202f",
               "rot": -0.12},
              {"k": "rect", "x": -0.30, "y": 0.122, "w": 0.24, "h": 0.035, "c": "#c8202f",
               "rot": -0.12},
              {"k": "rect", "x": -0.36, "y": 0.065, "w": 0.10, "h": 0.08, "c": "#22306e",
               "rot": -0.12},
              {"k": "star", "x": 0.30, "y": 0.10, "r": 0.085, "c": "#22306e"},
              {"k": "star", "x": 0.30, "y": 0.10, "r": 0.045, "c": "#f4f6f8"},
          ], "rare")
JL22.shirt("spangled_tank", "Spangled Tank",
           "A white tank top with a great big star-spangled star on the front, for "
           "the hottest night of the summer.",
           {"torso": "#f4f6f8", "arms": "#f4f6f8", "sleeves": 0.0, "decal": "jl_tee_spangled",
            "stripe": NAVY})
JL22.pants("star_shorts", "Star-Spangled Shorts",
           "Navy shorts scattered with little white stars. Built for running away from "
           "something you just lit.",
           {"legs": NAVY, "weave": "jl_starsprinkle", "length": 0.48})
JL22.belt("bunting_belt", "Bunting Belt",
          "A belt of striped ribbon with a gold star for a buckle.",
          {"band": RED, "buckle": GOLD, "width": 0.22, "metal": True, "weave": "jl_hstripes"})


@JL22.weapon("firecracker_string", "Firecracker String",
             "A whole string of firecrackers, lit at one end and thrown. It comes apart "
             "in the air into five crackers that fan out and go off wherever they land.",
             {"kind": "projectile", "projectile": "firecracker", "damage": 14, "splash": 4.0,
              "splash_damage": 16, "rpm": 66, "mag": 4, "reload": 2.3, "speed": 66,
              "range": 220, "auto": False, "sound": "fuse", "recoil": 1.0, "reserve": 24,
              "gravity_scale": 0.85, "self_damage": 0.25, "knockback": 6, "tracer": "#ffcf3a",
              "split": {"after": 0.28, "count": 5, "spread": 9, "damage": 12,
                        "splash_damage": 18}},
             [["+", "Breaks into five crackers a moment after it leaves your hand, fanned "
                    "out across 36 degrees"],
              ["+", "Close up, all five go off on the same unlucky somebody"],
              ["-", "Further away they spread out and land wide"],
              ["-", "The crackers can catch you too"]], rarity="legendary",
             proj=lambda: _cracker([0, 0, 0], 0.9, RED, r=[PI / 2, 0, 0], lit=True))
def _():
    # a plait of crackers on a fuse, held by the tail, the far end lit
    parts = [part("cyl", [0, 0.0, 0.66], [0.05, 1.32, 0.05], "#3a2e22", [PI / 2, 0, 0])]
    for n in range(7):
        z = 0.16 + n * 0.17
        side = 1 if n % 2 else -1
        parts += _cracker([0.13 * side, 0.0, z], 0.78, RED if n % 3 else "#f5c518",
                          r=[0, 0, -1.2 * side])
    parts.append(place("sparkle", [0, 0.0, 1.40], 0.36, "#fff6c9", m="neon", spin=6.0))
    parts.append(part("sph", [0, 0.0, 1.36], [0.11, 0.11, 0.11], "#ffcf3a", m="neon"))
    return parts


def _keg_model(k=1.0, lit=True):
    oak, iron = "#9a6236", "#3a3d42"
    out = [
        place("cask", [0, 0, 0], [0.80 * k, 0.96 * k, 0.80 * k], oak, anchor=[0, 0, 0],
              decal="jl_staves", wrap=True),
        part("torus", [0, 0.14 * k, 0], [0.74 * k, 0.05 * k, 0.74 * k], iron, m="metal"),
        part("torus", [0, 0.82 * k, 0], [0.74 * k, 0.05 * k, 0.74 * k], iron, m="metal"),
        part("rbox", [0, 0.48 * k, 0.40 * k], [0.36 * k, 0.24 * k, 0.03 * k], CREAM,
             decal="jl_xxx"),
        part("cyl", [0.12 * k, 0.98 * k, 0], [0.12 * k, 0.06 * k, 0.12 * k], "#5a3a22"),
        part("cyl", [0.12 * k, 1.12 * k, 0], [0.03 * k, 0.24 * k, 0.03 * k], "#3a2e22"),
    ]
    if lit:
        out.append(place("sparkle", [0.12 * k, 1.28 * k, 0], 0.24 * k, "#fff6c9", m="neon",
                         spin=6.0))
    return out


@JL22.weapon("powder_keg", "Powder Keg",
             "Roll out a keg of black powder and walk away whistling. It sits there, "
             "quiet as you like, until somebody on the other side walks too close.",
             {"kind": "deploy", "cooldown": 14, "sound": "throw",
              "deploy": {"type": "mine", "thrown": True, "throw": 18, "radius": 4.5,
                         "arm": 1.0, "splash": 9.0, "splash_damage": 85, "knockback": 30,
                         "secs": 40, "limit": 2, "name": "Powder Keg", "fx": "explode",
                         "color": RED, "scale": 1.6}},
             [["+", "Throws a keg that goes off when an enemy comes within 4.5 studs: 85 "
                    "damage in a 9 stud blast"],
              ["+", "Two kegs down at once; each waits up to 40 seconds"],
              ["-", "Takes a second to arm, and it is not hard to spot"],
              ["-", "14 second cooldown"]], rarity="legendary",
             deploy=lambda: _keg_model(1.0))
def _():
    return at_frame(_keg_model(0.62), [0, -0.30, 0.42])


@JL22.weapon("jumping_jack", "Jumping Jack",
             "Light it, drop it, and it goes off round your feet: a fizzing ground "
             "spinner that whirls round and round you, bowling over anyone it meets.",
             {"kind": "deploy", "cooldown": 24, "sound": "fuse",
              "deploy": {"type": "orbit", "orbit": 6.5, "speed": 2.6, "radius": 3.0,
                         "damage": 18, "knock": 18, "rehit": 0.7, "secs": 8, "limit": 1,
                         "name": "Jumping Jack", "color": "#ffcf3a", "scale": 1.5}},
             [["+", "A spinner circles you 6.5 studs out for 8 seconds"],
              ["+", "18 damage and a shove to anyone it runs into, again every 0.7 seconds"],
              ["-", "Reaches nobody further away than that"],
              ["-", "24 second cooldown"]], rarity="legendary",
             deploy=lambda: [
                 place("disc", [0, 0.9, 0], [1.3, 1.3, 1.6], RED, r=[-PI / 2, 0, 0], spin=14.0,
                       decal="jl_coil"),
                 part("torus", [0, 0.9, 0], [1.34, 0.22, 1.34], "#f5c518", spin=14.0),
                 place("sparkle", [0.70, 0.9, 0], 0.70, "#fff6c9", m="neon", spin=14.0),
                 place("sparkle", [-0.70, 0.9, 0], 0.56, "#ffcf3a", m="neon", spin=14.0),
                 place("sparkle", [0, 0.9, 0.70], 0.50, "#ff8c1a", m="neon", spin=14.0),
                 part("sph", [0, 0.9, 0], [2.2, 0.30, 2.2], "#ffcf3a", m="neon", a=0.22)])
def _():
    # a puck of coiled red paper, the fuse already going
    return [
        place("disc", [0, 0.10, 0.46], [0.70, 0.70, 1.6], RED, decal="jl_coil"),
        part("torus", [0, 0.10, 0.46], [0.72, 0.14, 0.72], "#f5c518", [PI / 2, 0, 0]),
        part("rbox", [0, -0.16, 0.24], [0.10, 0.40, 0.10], "#c8a070", [0.5, 0, 0]),
        part("cyl", [0.40, 0.30, 0.46], [0.03, 0.24, 0.03], "#3a2e22", [0, 0, -0.7]),
        place("sparkle", [0.50, 0.40, 0.46], 0.26, "#fff6c9", m="neon", spin=6.0),
        part("sph", [0.49, 0.39, 0.46], [0.08, 0.08, 0.08], "#ffcf3a", m="neon"),
    ]


@JL22.gear("old_glory", "Old Glory",
           "Plant the flag and stand by it. Everybody on your side who can see it "
           "fights a little harder and runs a little faster, and knows it.",
           {"kind": "deploy", "cooldown": 30, "sound": "horn",
            "deploy": {"type": "banner", "radius": 13.0, "secs": 10.0, "limit": 1,
                       "color": "#f4f6f8", "particle": "star",
                       "ally": {"might": [0.20, 1.0], "haste": [0.10, 1.0]}}},
           [["+", "Plants a flag: you and every teammate within 13 studs do 20% more "
                  "damage and run 10% faster"],
            ["+", "Flies for 10 seconds"],
            ["-", "It stays where you planted it"],
            ["-", "30 second cooldown"]], rarity="rare",
           deploy=lambda: [part("cyl", [0, 0.20, 0], [0.70, 0.40, 0.70], "#5a3a22"),
                           part("cyl", [0, 0.44, 0], [0.80, 0.08, 0.80], GOLD, m="metal")]
           + _flag([0, 0.40, 0], 3.2, yaw=0.0, pole=1.5))
def _():
    return [
        part("cyl", [0, 0.0, 0.50], [0.08, 2.0, 0.08], "#d9d2c0", [PI / 2, 0, 0], m="metal"),
        part("sph", [0, 0.0, 1.54], [0.16, 0.16, 0.16], GOLD, m="metal"),
        # the flag furled round the pole and tied
        place("cask", [0, 0.0, 1.10], [0.30, 0.70, 0.30], WHITE, anchor=[0, 0.5, 0],
              r=[PI / 2, 0, 0], decal="jl_flag", wrap=True),
        part("cyl", [0, 0.0, 0.92], [0.24, 0.04, 0.24], GOLD, [PI / 2, 0, 0]),
        part("cyl", [0, 0.0, 1.30], [0.24, 0.04, 0.24], GOLD, [PI / 2, 0, 0]),
        part("rbox", [0, -0.24, 0.00], [0.14, 0.40, 0.14], "#3a2a1c", [0.3, 0, 0]),
    ]


JL22.effect("spangled_salute", name="Star-Spangled Salute", rate=4.0, life=[1.8, 2.6],
            size=[0.20, 0.34], grow=0.0, gravity=0.0, spread=0.25, rise=[0.10, 0.35],
            blend="add", spin=1.4, colors=["#ffffff", "#ff3b4e", "#4f86ff", "#ffe08a"],
            shape="star", radius=0.85, orbit=1.5, upright=True, wobble=0.3)
JL22.effect("bunting_breeze", name="Bunting Breeze", rate=3.4, life=[2.0, 2.8],
            size=[0.26, 0.36], grow=0.0, gravity=-0.2, spread=0.5, rise=[0.2, 0.5],
            blend="normal", spin=0.8, colors=["#c8202f", "#f4f6f8", "#22306e"],
            shape="jl_pennant", radius=0.8, orbit=0.9, upright=True, wobble=0.6)
JL22.opening(
    sky={"top": "#060b24", "horizon": "#2a1840", "sun": [0.3, 0.9, 0.5], "clouds": 0,
         "tint": "#ffd8dc"},
    ambient="#6a6a9a", beam="#fff3e0", seep="bunting_breeze", after="spangled_salute",
    burst=["#ff3b4e", "#ffffff", "#4f86ff", "#ffe08a"],
    pieces=[{"shape": "star", "colors": ["#ff3b4e", "#ffffff", "#4f86ff"], "blend": "add"},
            {"shape": "jl_pennant", "colors": ["#c8202f", "#f4f6f8", "#22306e"],
             "blend": "normal"},
            {"shape": "firework", "colors": ["#ff3b4e", "#4f86ff", "#ffe08a"], "blend": "add"},
            {"shape": "spark", "colors": ["#fff6c9", "#ffcf3a"], "blend": "add"}],
    backdrop="jl_bunting", title_wait="The fuse is fizzing...",
    title_shake="Cover your ears...")
JL22.award("Star-Spangled Blast", ["Sparkler Holder", "Flag Waver", "Fuse Lighter",
                                   "Parade Marshal", "Star-Spangled", "First Fourth Founder"],
           "Opened Powder Keg Crates during Blockhaven's first Fourth of July, 2022.",
           "em_spangle", "spangle")
JL22.bundle("pair", "Keg and Key", 1, 1050, "One Powder Keg Crate, one Liberty Star Key.")
JL22.bundle("cheers", "Three Cheers", 3, 3000, "Three kegs, three keys. Saves 300.")


# ============================================================ 2023
CHAR = "#26272b"
BUN = "#d9944a"
MUSTARD = "#f2b705"
KETCHUP = "#c4281c"
GRASS = "#4f9e3a"
JL23 = Event(
    "july4_2023", "july4", 2023, "jl23",
    name="Backyard Cookout", title="The Backyard Cookout",
    blurb="For the second Fourth the whole server came round to the same back yard. "
          "Somebody wheeled out a kettle grill, somebody else brought far too many "
          "hot dogs, and the ants arrived before anybody. Nobody has seen the "
          "spatula since.",
    tagline="Who wants a burger? Everybody wants a burger.",
    starts="2023-06-27", ends="2023-07-11",
    colors={"accent": "#ff8c1a", "deep": "#1e1410", "glow": "#ffcf6a"},
    family_effects=["scorching", "ember_storm", "sunbeam", "bubbly"],
    hero_effect="burger_flip", stencil="stencil_jl23")


def _hot_dog(at, k=1.0, yaw=0.0, mustard=True):
    """A hot dog in its bun, lying along X turned by ``yaw``."""
    x, y, z = at
    out = []
    for side in (1, -1):
        off = rotate([0, 0, 0.13 * side * k], [0, yaw, 0])
        out.append(place("capsule", [x + off[0], y, z + off[2]], [0.40 * k, 0.56 * k, 0.40 * k],
                         BUN, r=[0, yaw, PI / 2]))
    out.append(place("capsule", [x, y + 0.14 * k, z], [0.28 * k, 0.70 * k, 0.28 * k], "#b0452a",
                     r=[0, yaw, PI / 2]))
    if mustard:
        for n in range(9):
            t = (n - 4) / 4.0
            off = rotate([t * 0.80 * k, 0.29 * k, 0.0], [0, yaw, 0])
            out.append(part("rbox", [x + off[0], y + off[1], z + off[2]],
                            [0.06 * k, 0.05 * k, 0.24 * k], MUSTARD,
                            [0, yaw + (0.55 if n % 2 else -0.55), 0]))
    return out


def _burger(at, k=1.0, patties=1):
    """A burger with everything, sitting at ``at`` (its base)."""
    x, y, z = at
    out = [part("cyl", [x, y + 0.10 * k, z], [1.30 * k, 0.20 * k, 1.30 * k], BUN)]
    h = y + 0.20 * k
    for n in range(patties):
        out.append(part("cyl", [x, h + 0.08 * k, z], [1.40 * k, 0.16 * k, 1.40 * k], "#5a2e1a",
                        decal="jl_patty", wrap=True))
        out.append(part("rbox", [x, h + 0.18 * k, z], [1.24 * k, 0.04 * k, 1.24 * k], MUSTARD,
                        [0, 0.78 + n * 0.3, 0]))
        for c in range(4):
            a = 0.78 + n * 0.3 + c * PI / 2 + PI / 4
            out.append(place("teardrop", [x + math.sin(a) * 0.80 * k, h + 0.10 * k,
                                          z + math.cos(a) * 0.80 * k],
                             [0.10 * k, 0.20 * k, 0.10 * k], MUSTARD, r=[PI, 0, 0]))
        h += 0.20 * k
    out += [place("ruffle", [x, h + 0.02 * k, z], [1.56 * k, 2.0 * k, 1.56 * k], "#6abf4b"),
            part("cyl", [x, h + 0.07 * k, z], [1.20 * k, 0.08 * k, 1.20 * k], "#e2483a"),
            place("hemi", [x, h + 0.11 * k, z], [1.40 * k, 1.0 * k, 1.40 * k], BUN,
                  anchor=[0, 0, 0])]
    top = h + 0.11 * k
    for n in range(14):
        a = n * 2.4
        rr = 0.18 + (n % 4) * 0.12
        yy = top + 0.5 * k * math.sqrt(max(0.0, 1 - (rr / 0.70) ** 2)) + 0.01 * k
        out.append(part("sph", [x + math.sin(a) * rr * k, yy, z + math.cos(a) * rr * k],
                        [0.07 * k, 0.03 * k, 0.04 * k], "#fff3d6", [0, a, 0]))
    return out


@JL23.crate_model("Kettle Grill Crate",
                  "A black kettle grill on three legs, the coals still glowing, smoke "
                  "curling out of the vent and something sizzling under the lid. Holds the "
                  "Backyard Cookout set. Needs a Corn-Cob Key.",
                  hinge=[0, 0.24, -0.86], keyhole=[0, -0.10, 0.90])
def _():
    steel = "#9aa0a8"
    parts = [
        place("bowl", [0, -0.56, 0], [1.66, 1.30, 1.66], CHAR, anchor=[0, 0, 0], m="metal"),
        part("torus", [0, 0.20, 0], [1.70, 0.08, 1.70], "#3a3b40", m="metal"),
        # the coals and the grate, and dinner on it
        part("cyl", [0, 0.00, 0], [1.40, 0.04, 1.40], "#ff6a1a", m="neon"),
        part("cyl", [0, 0.13, 0], [1.56, 0.02, 1.56], "#3a3b40", m="metal", a=0.0),
    ]
    for n in range(9):
        x = -0.64 + n * 0.16
        parts.append(part("rbox", [x, 0.13, 0], [0.03, 0.03, 2 * math.sqrt(0.78 ** 2 - x * x)],
                          steel, m="metal"))
    for n in range(7):
        a = n * 2.1
        parts.append(part("sph", [math.sin(a) * 0.40, 0.04, math.cos(a) * 0.40],
                          [0.20, 0.12, 0.20], "#ffb347" if n % 2 else "#e8481a", m="neon"))
    parts += _hot_dog([-0.24, 0.20, 0.30], 0.30, yaw=0.2, mustard=False)
    parts += _hot_dog([-0.28, 0.20, -0.10], 0.30, yaw=-0.1, mustard=False)
    parts += at_frame(_burger([0, 0, 0], 1.0)[1:2], [0.32, 0.12, 0.14], k=0.36)
    parts += at_frame(_burger([0, 0, 0], 1.0)[1:2], [0.28, 0.12, -0.32], k=0.32)
    parts += [
        # the lid, its handle, the vent and the smoke
        place("hemi", [0, 0.22, 0], [1.72, 1.16, 1.72], CHAR, anchor=[0, 0, 0], m="metal",
              lid=1),
        part("torus", [0, 0.24, 0], [1.74, 0.07, 1.74], "#3a3b40", m="metal", lid=1),
        part("cyl", [0, 0.80, 0], [0.42, 0.05, 0.42], steel, m="metal", lid=1),
        part("rbox", [0.06, 0.83, 0], [0.18, 0.03, 0.06], steel, m="metal", lid=1),
        part("rbox", [0, 0.60, 0.66], [0.64, 0.04, 0.18], steel, [-0.55, 0, 0], m="metal", lid=1),
        part("rbox", [0, 0.68, 0.72], [0.62, 0.10, 0.12], "#3a2414", decal="leather", lid=1),
        part("rbox", [0.25, 0.63, 0.68], [0.05, 0.12, 0.10], steel, m="metal", lid=1),
        part("rbox", [-0.25, 0.63, 0.68], [0.05, 0.12, 0.10], steel, m="metal", lid=1),
        part("sph", [0.04, 1.02, 0.02], [0.30, 0.24, 0.28], "#c9ccd2", a=0.6, lid=1),
        part("sph", [0.12, 1.24, -0.04], [0.24, 0.20, 0.22], "#d9dce2", a=0.48, lid=1),
        part("sph", [0.04, 1.44, 0.02], [0.18, 0.15, 0.17], "#e3e6ea", a=0.35, lid=1),
        # the lock on the bowl's front, the badge at the back
        part("rbox", [0, -0.10, 0.84], [0.34, 0.36, 0.10], BRASS, m="metal", decal="keyhole",
             lock=1),
        part("rbox", [0, -0.10, -0.82], [0.64, 0.42, 0.04], steel, m="metal"),
        part("box", [0, -0.10, -0.85], [0.60, 0.40, 0.02], "#000000", [0, PI, 0],
             decal="stencil_jl23", a=-1),
        # side handles
        part("rbox", [0.90, 0.08, 0], [0.12, 0.06, 0.40], "#3a2414"),
        part("rbox", [-0.90, 0.08, 0], [0.12, 0.06, 0.40], "#3a2414"),
        # the ash pan slung between the legs
        place("bowl", [0, -0.84, 0], [0.70, 0.30, 0.70], steel, anchor=[0, 0, 0], m="metal"),
    ]
    feet = []
    for n, a in enumerate((0.0, 2 * PI / 3, -2 * PI / 3)):
        top = [math.sin(a) * 0.50, -0.42, math.cos(a) * 0.50]
        foot = [math.sin(a) * 0.80, -0.98, math.cos(a) * 0.80]
        feet.append(foot)
        parts.append(_rod(top, foot, 0.08, steel, m="metal"))
        if n:
            parts += [part("cyl", foot, [0.30, 0.08, 0.30], "#2b2b30", [0, a, PI / 2]),
                      part("cyl", foot, [0.12, 0.10, 0.12], steel, [0, a, PI / 2], m="metal")]
        else:
            parts.append(part("sph", foot, [0.12, 0.08, 0.12], "#2b2b30"))
    for n in range(3):
        a, b = feet[n], feet[(n + 1) % 3]
        mid = lambda p: [p[0] * 0.75, -0.82, p[2] * 0.75]
        parts.append(_rod(mid(a), mid(b), 0.04, steel, m="metal"))
    # the spatula, hung off the right handle
    parts += [part("rbox", [0.96, -0.12, 0.10], [0.05, 0.40, 0.06], steel, m="metal"),
              part("rbox", [0.96, -0.42, 0.10], [0.03, 0.24, 0.20], steel, m="metal"),
              part("rbox", [0.96, 0.12, 0.10], [0.07, 0.16, 0.08], "#3a2414")]
    return parts


@JL23.key_model("Corn-Cob Key",
                "A buttered corn cob for a bow, a corn-holder for a blade, and kernels "
                "for teeth. Opens one Kettle Grill Crate. Mind it does not melt.",
                shoulder=-0.32)
def _():
    parts = [
        place("capsule", [-0.66, 0.0, 0], [0.32, 0.21, 0.32], "#f5c518", r=[0, 0, PI / 2],
              decal="jl_kernels", wrap=True),
        part("rbox", [-0.72, 0.17, 0.0], [0.18, 0.06, 0.14], "#fff3a0", [0, 0.3, 0.08]),
        place("teardrop", [-0.62, 0.11, 0.08], [0.08, 0.12, 0.08], "#fff3a0", r=[PI, 0, 0]),
        part("rbox", [-0.30, 0.0, 0], [0.10, 0.22, 0.22], "#2f9a4a"),
        part("cyl", [0.12, 0, 0], [0.07, 0.84, 0.07], SILVER, [0, 0, PI / 2], m="metal"),
        part("rbox", [0.40, -0.10, 0], [0.09, 0.14, 0.09], "#f5c518"),
        part("rbox", [0.52, -0.13, 0], [0.09, 0.20, 0.09], "#f5c518"),
        part("rbox", [0.62, -0.09, 0], [0.09, 0.12, 0.09], "#f5c518"),
    ]
    for n, (tilt, z) in enumerate(((2.3, 0.10), (2.6, -0.08), (2.0, 0.0))):
        parts.append(place("leaf", [-0.36, 0.02 * n, z], [0.9, 0.62, 1.0], "#6aa84f",
                           anchor=[0, -0.5, 0], r=[0.25 * (n - 1), 0, tilt]))
    return parts


@JL23.hat("chef_toque", "Grill Master's Toque",
          "A chef's hat two feet tall, pleated, starched and labelled, with the tongs "
          "tucked in the band where they belong. The person in this hat is in charge "
          "of the grill. That is not up for discussion.", "legendary")
def _():
    white = "#ffffff"
    parts = [
        band(-0.10, 0.32, white, grow=0.04, decal="linen", wrap=True),
        part("cyl", [0, 0.52, 0], [1.46, 0.94, 1.40], white, decal="jl_pleats", wrap=True),
        part("sph", [0, 1.12, 0], [2.00, 0.86, 1.92], white, decal="linen", wrap=True),
        part("box", [0, -0.10, 0.795], [1.00, 0.30, 0.02], "#000000", decal="jl_grillband", a=-1),
    ]
    for n in range(7):
        a = n * TAU / 7 + 0.3
        parts.append(part("sph", [math.sin(a) * 0.66, 1.20, math.cos(a) * 0.64],
                          [0.70, 0.56, 0.70], white, decal="linen", wrap=True))
    parts.append(part("sph", [0, 1.46, 0], [0.90, 0.40, 0.86], white, decal="linen", wrap=True))
    # tongs one side, a spatula the other, both tucked in the band
    parts += [part("rbox", [0.84, 0.16, -0.06], [0.05, 0.96, 0.06], SILVER, [0.10, 0, -0.16],
                   m="metal"),
              part("rbox", [0.86, 0.16, 0.04], [0.05, 0.96, 0.06], SILVER, [-0.12, 0, -0.16],
                   m="metal"),
              part("rbox", [0.92, 0.62, -0.01], [0.10, 0.12, 0.18], KETCHUP, [0, 0, -0.16]),
              part("rbox", [-0.84, 0.14, -0.10], [0.06, 0.66, 0.06], "#3a2414", [0, 0, 0.16]),
              part("rbox", [-0.92, 0.62, -0.10], [0.04, 0.36, 0.32], SILVER, [0, 0, 0.16],
                   m="metal", decal="jl_slots"),
              part("sph", [0.30, 1.78, -0.10], [0.36, 0.26, 0.32], "#c9ccd2", a=0.5),
              part("sph", [0.42, 2.02, -0.18], [0.24, 0.20, 0.22], "#d9dce2", a=0.38)]
    return parts


@JL23.hat("sprinkler", "Backyard Sprinkler",
          "A square of the back lawn, worn as a hat, with the sprinkler going round "
          "and round on top of it. Coolest person at the cookout. Also the wettest.",
          "legendary")
def _():
    water = "#8fd8ff"
    parts = [
        cap(-0.26, 0.10, GRASS, decal="jl_grass", wrap=True),
        band(-0.22, 0.10, "#6a4a2a", grow=0.04),
        part("cyl", [0, 0.16, 0], [0.34, 0.12, 0.34], "#2f6a2a"),
        part("cyl", [0, 0.30, 0], [0.10, 0.30, 0.10], BRASS, m="metal"),
        part("cyl", [0, 0.46, 0], [0.22, 0.10, 0.22], BRASS, m="metal", spin=4.0),
        part("rbox", [0, 0.48, 0], [1.10, 0.06, 0.08], BRASS, m="metal", spin=4.0),
        part("rbox", [0, 0.48, 0], [0.08, 0.06, 1.10], BRASS, m="metal", spin=4.0),
        place("arch", [0, 0.50, 0], [2.2, 1.6, 2.0], water, anchor=[0, 0, 0], m="glass",
              a=0.45, spin=4.0),
        place("arch", [0, 0.50, 0], [2.2, 1.4, 2.0], water, anchor=[0, 0, 0], m="glass",
              a=0.45, r=[0, PI / 2, 0], spin=4.0),
    ]
    for n in range(10):
        a = n * TAU / 10
        parts.append(place("cone", [math.sin(a) * 0.80, 0.10, math.cos(a) * 0.78],
                           [0.12, 0.20, 0.12], "#5cbf4a", r=[math.cos(a) * 0.3, 0, -math.sin(a) * 0.3]))
    for n, (x, y, z) in enumerate(((1.05, 0.30, 0.20), (-0.96, 0.40, -0.30), (0.30, 0.20, 1.00),
                                   (-0.40, 0.10, -1.0), (0.80, 0.0, -0.70))):
        parts.append(place("teardrop", [x, y, z], [0.10, 0.16, 0.10], water, r=[PI, 0, 0],
                           m="glass", a=0.7))
    return parts


@JL23.hat("hot_dog", "Hot Dog Hat",
          "A foot-long in a bun, with mustard, worn sideways. There is a little flag on "
          "a toothpick in it because it is the Fourth and that is the law.", "rare")
def _():
    parts = _hot_dog([0, 0.20, 0], 1.0)
    parts += [part("cyl", [0.52, 0.52, 0.0], [0.03, 0.40, 0.03], "#e8d4a0")]
    parts += _flag([0.52, 0.52, 0.0], 0.42, yaw=0.2, pole=0.55, finial="#e8d4a0")[1:]
    return parts


@JL23.hat("burger_stack", "Double Stack",
          "Two patties, two slices of cheese, lettuce, tomato and a sesame bun the "
          "size of a hubcap. Worn with pride, eaten in instalments.", "rare")
def _():
    return _burger([0, 0.0, 0], 1.0, patties=2)


@JL23.hat("lemonade_helmet", "Lemonade Hard Hat",
          "A hard hat with a cup of lemonade either side and a straw from each of them "
          "to your mouth. Fresh-squeezed, hands-free, no refills.", "rare")
def _():
    yellow, straw = "#f5c518", "#e8505b"
    parts = [
        dome(-0.30, 0.86, yellow, t="capcrown"),
        ringband(-0.27, 0.07, shade(yellow, 0.9), margin=0.12),
        part("box", [0, 0.06, 0.88], [0.44, 0.44, 0.02], "#000000", [-0.45, 0, 0],
             decal="jl_lemon", a=-1),
    ]
    for side in (1, -1):
        x = 1.02 * side
        parts += [
            part("rbox", [0.90 * side, 0.02, 0.0], [0.24, 0.08, 0.10], KETCHUP),
            part("torus", [x, -0.10, 0.0], [0.42, 0.08, 0.42], KETCHUP),
            part("torus", [x, 0.12, 0.0], [0.42, 0.08, 0.42], KETCHUP),
            part("cyl", [x, 0.16, 0.0], [0.34, 0.52, 0.34], "#ffe680", m="glass", a=0.8),
            part("cyl", [x, 0.42, 0.0], [0.30, 0.02, 0.30], "#fff6c0"),
            part("cyl", [x + 0.10 * side, 0.44, 0.10], [0.20, 0.03, 0.20], "#f5e04a",
                 [PI / 2, 0, 0.4 * side], decal="jl_lemon"),
        ]
        path = [(x, 0.30, 0.04), (x, 0.64, 0.04), (1.16 * side, 0.42, 0.14),
                (1.06 * side, -0.60, 0.36), (0.78 * side, -0.86, 0.80), (0.10 * side, -0.86, 0.80)]
        for a, b in zip(path, path[1:]):
            parts.append(_rod(a, b, 0.07, straw))
            parts.append(part("sph", list(b), [0.07, 0.07, 0.07], straw))
    return parts


@JL23.hat("melon_helmet", "Watermelon Helmet",
          "Half a watermelon, scooped out and worn as a helmet. The seeds round the "
          "rim are a design choice.", "uncommon")
def _():
    parts = [
        dome(-0.26, 0.86, "#3c8a3c", decal="jl_melon", wrap=True),
        ringband(-0.25, 0.05, "#eef4cf", margin=0.04),
        ringband(-0.31, 0.08, "#ea4a5c", margin=0.03),
    ]
    for n in range(12):
        a = n * TAU / 12 + 0.2
        parts.append(place("teardrop", [math.sin(a) * 0.93, -0.33, math.cos(a) * 0.91],
                           [0.06, 0.10, 0.04], "#1a1a1a", r=[PI, a, 0]))
    return parts


@JL23.hat("straw_hat", "Pitmaster's Straw Hat",
          "A battered straw cowboy hat with a gingham band and a smell of hickory "
          "smoke that will never, ever come out.", "uncommon")
def _():
    return [
        place("cowbrim", [0, -0.04, 0], [2.52, 2.1, 2.52], STRAW, anchor=[0, 0, 0],
              decal="jl_straw", wrap=True),
        place("cask", [0, 0.0, 0], [1.38, 0.84, 1.30], STRAW, anchor=[0, 0, 0],
              decal="jl_straw", wrap=True),
        place("hemi", [0, 0.80, 0], [1.16, 0.42, 1.10], STRAW, anchor=[0, 0, 0],
              decal="jl_straw", wrap=True),
        part("rbox", [0, 0.98, -0.08], [0.14, 0.07, 0.80], shade(STRAW, 0.8), [0.12, 0, 0]),
        part("sph", [0.30, 0.86, 0.38], [0.22, 0.20, 0.30], shade(STRAW, 0.85), [0.3, 0.6, -0.3]),
        part("sph", [-0.30, 0.86, 0.38], [0.22, 0.20, 0.30], shade(STRAW, 0.85), [0.3, -0.6, 0.3]),
        part("cyl", [0, 0.07, 0], [1.36, 0.15, 1.28], KETCHUP, decal="jl_gingham", wrap=True),
        place("feather", [0.62, 0.10, 0.14], 0.50, "#6a4a2a", anchor=[0, -0.5, 0],
              r=[0, 1.2, -0.5]),
    ]


@JL23.back("lawn_chair", "Folding Lawn Chair",
           "A folding lawn chair in green and white webbing, carried on the back so "
           "you always have somewhere to sit when the fireworks start.", "rare")
def _():
    alu = "#c9ced6"
    parts = [
        part("rbox", [0, 0.50, -0.30], [1.54, 1.66, 0.04], "#2f8a4a", decal="jl_webbing"),
        part("rbox", [0, 0.30, -0.44], [1.54, 1.30, 0.04], "#2f8a4a"),
        part("box", [0, 0.30, -0.465], [1.48, 1.24, 0.01], "#000000", [0, PI, 0],
             decal="jl_webbing", a=-1),
        *straps("#2b2b30", 0.34, 0.12),
    ]
    for x in (-0.80, 0.80):
        parts += [part("cyl", [x, 0.50, -0.30], [0.08, 1.80, 0.08], alu, m="metal"),
                  part("cyl", [x * 0.97, 0.20, -0.46], [0.08, 1.50, 0.08], alu, m="metal"),
                  part("rbox", [x * 1.04, 0.70, -0.38], [0.12, 0.08, 0.50], "#e8e2d0"),
                  part("cyl", [x * 0.97, -0.62, -0.50], [0.08, 0.40, 0.08], alu, [0.4, 0, 0],
                       m="metal")]
    for y, z in ((1.38, -0.30), (-0.36, -0.30), (0.94, -0.46), (-0.52, -0.46)):
        parts.append(part("cyl", [0, y, z], [0.08, 1.60, 0.08], alu, [0, 0, PI / 2], m="metal"))
    return parts


@JL23.back("picnic_blanket", "Picnic Blanket",
           "The red gingham picnic blanket, worn as a cape. Two ants are still on it, "
           "walking very purposefully towards your sandwich.", "uncommon")
def _():
    parts = [
        place("cape", [0, 0.98, -0.08], [1.70, 1.92, 1.5], KETCHUP, anchor=[0, 0, 0],
              decal="jl_gingham", wrap=True),
        part("rbox", [0, 0.96, -0.14], [1.40, 0.14, 0.16], "#8a1c14"),
    ]
    for n, (x, y) in enumerate(((0.30, 0.30), (0.42, 0.18))):
        z = -0.29 - 0.12 * (0.98 - y)
        for k in range(3):
            parts.append(part("sph", [x - 0.05 * k, y + 0.03 * k, z - 0.03],
                              [0.06, 0.05, 0.05], "#1a1a1a"))
    return parts


@JL23.hairdo("pompadour", "Cookout Pompadour",
             "Combed up and rolled over in a wave you could surf on, held there by a "
             "great deal of something from a jar.", "rare")
def _():
    c, hi = "#1c1612", "#3a2e24"
    parts = [place("hairshort", [0, 0, 0], [1.02, 1.02, 1.02], c, anchor=[0, 0, 0],
                   decal="strands", wrap=True)]
    parts += [part("sph", [0, 0.62, 0.10], [0.86, 0.34, 0.70], c, decal="strands", wrap=True),
              place("capsule", [0, 0.68, 0.40], [0.40, 0.27, 0.42], hi, r=[0, 0, PI / 2],
                    decal="strands", wrap=True),
              place("teardrop", [0.12, 0.52, 0.60], [0.12, 0.26, 0.10], c, r=[2.4, 0, -0.3])]
    return parts


@JL23.hairdo("gingham_ponytail", "Gingham Ponytail",
             "A high ponytail with a red gingham scrunchie that matches the tablecloth "
             "exactly. Coincidence. Probably.", "uncommon")
def _():
    c = "#c8913a"
    return [
        place("hairmid", [0, 0, 0], [1.02, 1.02, 1.02], c, anchor=[0, 0, 0], decal="strands",
              wrap=True),
        part("torus", [0, 0.50, -0.42], [0.30, 0.14, 0.30], KETCHUP, [1.0, 0, 0],
             decal="jl_gingham", wrap=True),
        place("teardrop", [0, 0.56, -0.48], [0.40, 0.90, 0.34], c, anchor=[0, 0.95, 0],
              r=[2.6, 0, 0], decal="strands", wrap=True),
    ]


JL23.face("sunglasses_tan", "Sunglasses Tan",
          "Six hours at the grill in sunglasses. The sunglasses are off now. The tan "
          "is not.", [
              {"k": "ellipse", "x": -0.26, "y": 0.02, "w": 0.30, "h": 0.22, "c": "rgba(255,96,72,0.40)"},
              {"k": "ellipse", "x": 0.26, "y": 0.02, "w": 0.30, "h": 0.22, "c": "rgba(255,96,72,0.40)"},
              {"k": "ellipse", "x": 0, "y": -0.26, "w": 0.60, "h": 0.16, "c": "rgba(255,96,72,0.32)"},
              {"k": "ellipse", "x": -0.20, "y": -0.13, "w": 0.24, "h": 0.17, "c": "#fff1dc"},
              {"k": "ellipse", "x": 0.20, "y": -0.13, "w": 0.24, "h": 0.17, "c": "#fff1dc"},
              {"k": "rect", "x": 0, "y": -0.15, "w": 0.18, "h": 0.04, "c": "#fff1dc"},
              {"k": "arc", "x": -0.20, "y": -0.11, "r": 0.06, "a0": 0.55, "a1": 0.95, "w": 0.03,
               "c": "#16171b"},
              {"k": "arc", "x": 0.20, "y": -0.11, "r": 0.06, "a0": 0.55, "a1": 0.95, "w": 0.03,
               "c": "#16171b"},
              {"k": "arc", "x": 0, "y": 0.04, "r": 0.18, "a0": 0.10, "a1": 0.40, "w": 0.045,
               "c": "#16171b"},
              {"k": "ellipse", "x": 0, "y": -0.01, "w": 0.08, "h": 0.06, "c": "#ff5a48"},
          ])
JL23.face("mustard_mustache", "Mustard Mustache",
          "A big happy grin and a moustache of mustard from the last bite. Nobody has "
          "told them. Nobody is going to.", [
              {"k": "arc", "x": -0.20, "y": -0.10, "r": 0.07, "a0": 0.55, "a1": 0.95, "w": 0.04,
               "c": "#16171b"},
              {"k": "arc", "x": 0.20, "y": -0.10, "r": 0.07, "a0": 0.55, "a1": 0.95, "w": 0.04,
               "c": "#16171b"},
              {"k": "poly", "pts": [[-0.22, 0.10], [0.22, 0.10], [0.14, 0.24], [-0.14, 0.24]],
               "c": "#16171b"},
              {"k": "rect", "x": 0, "y": 0.12, "w": 0.36, "h": 0.03, "c": "#ffffff"},
              {"k": "poly", "pts": [[-0.26, 0.06], [-0.12, 0.03], [0.0, 0.07], [0.12, 0.03],
                                    [0.27, 0.07], [0.20, 0.10], [0.05, 0.08], [-0.05, 0.09],
                                    [-0.20, 0.10]], "c": "#f2b705"},
              {"k": "ellipse", "x": 0.10, "y": 0.33, "w": 0.06, "h": 0.05, "c": "#c4281c"},
          ], "rare")
JL23.shirt("bbq_apron", "Licensed to Grill",
           "A white tee under a red apron that says exactly what it means. Comes with "
           "a sauce stain already on it, to save time.",
           {"torso": "#f4f6f8", "arms": "#f4f6f8", "sleeves": 0.45, "decal": "jl_tee_apron",
            "stripe": KETCHUP})
JL23.pants("jorts", "Grass-Stained Jorts",
           "Denim shorts, cut off at the knee, green at both knees from the tug-of-war.",
           {"legs": "#4a6fa8", "weave": "jl_jorts", "length": 0.55})
JL23.belt("condiment_belt", "Condiment Holster",
          "A leather belt with two holsters: ketchup on the left, mustard on the right. "
          "Quickest draw at the cookout.",
          {"band": "#6a3a1a", "buckle": MUSTARD, "width": 0.22, "weave": "leather",
           "pouch": KETCHUP, "metal": True})


@JL23.weapon("grill_spatula", "Grill Master's Spatula",
             "A spatula the length of your arm, built for flipping burgers and very good "
             "at flipping people. Flip them up, then serve them on the way down.",
             {"kind": "melee", "damage": 22, "headshot": 1.0, "rpm": 100, "range": 10.0,
              "arc": 0.6, "sound": "swing", "knockback": 4,
              "on_hit": {"knockup": 30}, "vs_airborne": 1.6},
             [["+", "Flips whoever it hits up into the air"],
              ["+", "60% more damage to anyone off the ground: flip, then serve"],
              ["-", "Only 22 damage to anybody with both feet down"],
              ["-", "Flip somebody too high and they sail out of reach"]], rarity="legendary")
def _():
    steel = "#c9ced6"
    return [
        part("cyl", [0, 0.0, -0.10], [0.16, 0.56, 0.16], "#3a2414", [PI / 2, 0, 0],
             decal="leather", wrap=True),
        part("torus", [0, 0.0, -0.44], [0.16, 0.04, 0.16], steel, [0, 0, PI / 2], m="metal"),
        part("rbox", [0, 0.0, 0.60], [0.08, 0.05, 1.20], steel, [-0.12, 0, 0], m="metal"),
        part("rbox", [0, 0.12, 1.44], [0.82, 0.05, 0.86], steel, [-0.18, 0, 0], m="metal",
             decal="jl_slots"),
        part("cyl", [0.12, 0.17, 1.40], [0.40, 0.08, 0.40], "#5a2e1a", [-0.18, 0, 0],
             decal="jl_patty", wrap=True),
    ]


def _hot_dog_proj():
    return [p for p in _hot_dog([0, 0, 0], 0.55, yaw=PI / 2)]


@JL23.weapon("hot_dog_launcher", "Hot Dog Launcher",
             "A stadium T-shirt cannon converted, at some expense, to hot dogs. Each one "
             "lands with a splat and leaves two spares on the grass for your team.",
             {"kind": "projectile", "projectile": "hotdog", "damage": 30, "splash": 3.5,
              "splash_damage": 14, "rpm": 60, "mag": 4, "reload": 2.4, "speed": 76,
              "range": 300, "auto": False, "sound": "pop", "recoil": 1.8, "reserve": 24,
              "gravity_scale": 0.8, "self_damage": 0.0, "knockback": 8,
              "pickups": {"count": 2, "spread": 4.0, "heal": 15, "color": "#d9763a",
                          "secs": 12, "radius": 3.0}},
             [["+", "Every hot dog leaves two more on the ground: a teammate who picks one "
                    "up heals 15"],
              ["+", "You can eat them too"],
              ["-", "A lobbed shot with a small splash"],
              ["-", "Four to a load"]], rarity="legendary",
             proj=_hot_dog_proj)
def _():
    return [
        part("cyl", [0, 0.06, 0.70], [0.56, 1.40, 0.56], KETCHUP, [PI / 2, 0, 0],
             decal="jl_hstripes", wrap=True),
        part("torus", [0, 0.06, 1.40], [0.62, 0.10, 0.62], MUSTARD, [PI / 2, 0, 0]),
        part("cyl", [0, 0.06, 1.41], [0.44, 0.03, 0.44], "#2b2b30", [PI / 2, 0, 0]),
        part("cyl", [0, -0.32, 0.36], [0.30, 0.70, 0.30], "#c9ced6", [PI / 2, 0, 0], m="metal"),
        part("cyl", [0, -0.32, 0.74], [0.16, 0.06, 0.16], "#2b2b30", [PI / 2, 0, 0]),
        part("rbox", [0, -0.34, -0.04], [0.18, 0.46, 0.24], "#2b2b30", [0.3, 0, 0]),
        part("rbox", [0, 0.10, -0.24], [0.30, 0.28, 0.50], "#2b2b30"),
    ] + at_frame(_hot_dog([0, 0, 0], 0.40, yaw=PI / 2, mustard=True), [0, 0.06, 1.44])


@JL23.weapon("seed_spitter", "Watermelon Seed Spitter",
             "A whole watermelon with a brass nozzle in one end and a pump in the other. "
             "It spits seeds faster than anybody at the picnic, and they go straight "
             "through the first person in the way.",
             {"kind": "projectile", "projectile": "seed", "damage": 8, "splash": 0,
              "splash_damage": 0, "rpm": 480, "mag": 30, "reload": 2.2, "speed": 140,
              "range": 160, "auto": True, "sound": "pop", "recoil": 0.25, "reserve": 150,
              "gravity_scale": 0.55, "self_damage": 0.0, "knockback": 1,
              "pierce_players": 2, "tracer": "#1a1a1a"},
             [["+", "Eight seeds a second"],
              ["+", "Every seed goes on through up to two people"],
              ["-", "8 damage a seed"],
              ["-", "They drop off over distance"]], rarity="legendary",
             proj=lambda: [place("teardrop", [0, 0, 0], [0.22, 0.34, 0.16], "#1a1a1a",
                                 r=[PI / 2, 0, 0])])
def _():
    return [
        part("sph", [0, 0.10, 0.50], [0.80, 0.76, 1.30], "#3c8a3c", decal="jl_melon", wrap=True),
        part("cyl", [0, 0.48, 0.50], [0.50, 0.03, 0.80], "#ea4a5c"),
        part("cyl", [0, 0.46, 0.50], [0.56, 0.02, 0.86], "#eef4cf"),
        part("sph", [0.10, 0.50, 0.40], [0.04, 0.02, 0.06], "#1a1a1a"),
        part("sph", [-0.12, 0.50, 0.62], [0.04, 0.02, 0.06], "#1a1a1a"),
        part("cyl", [0, 0.10, 1.24], [0.12, 0.30, 0.12], BRASS, [PI / 2, 0, 0], m="metal"),
        part("cyl", [0, 0.10, 1.40], [0.18, 0.06, 0.18], BRASS, [PI / 2, 0, 0], m="metal"),
        part("cyl", [0, 0.10, -0.24], [0.14, 0.40, 0.14], BRASS, [PI / 2, 0, 0], m="metal"),
        part("rbox", [0, -0.30, -0.04], [0.16, 0.44, 0.22], "#3a2414", [0.3, 0, 0]),
    ]


def _grill_model(k=1.0):
    steel = "#9aa0a8"
    out = [
        place("bowl", [0, 1.0 * k, 0], [1.20 * k, 0.90 * k, 1.20 * k], CHAR, anchor=[0, 0, 0],
              m="metal"),
        part("torus", [0, 1.54 * k, 0], [1.24 * k, 0.06 * k, 1.24 * k], "#3a3b40", m="metal"),
        part("cyl", [0, 1.40 * k, 0], [1.00 * k, 0.03 * k, 1.00 * k], "#ff6a1a", m="neon"),
        place("hemi", [0, 1.56 * k, -0.62 * k], [1.24 * k, 0.84 * k, 1.24 * k], CHAR,
              anchor=[0, 0, -0.5], r=[-1.3, 0, 0], m="metal"),
        part("sph", [0, 2.10 * k, 0], [0.50 * k, 0.40 * k, 0.48 * k], "#c9ccd2", a=0.5),
        part("sph", [0.10 * k, 2.50 * k, 0], [0.36 * k, 0.30 * k, 0.34 * k], "#d9dce2", a=0.38),
    ]
    out += at_frame(_burger([0, 0, 0], 1.0)[1:2], [0.18 * k, 1.50 * k, 0.10 * k], k=0.28 * k)
    out += _hot_dog([-0.24 * k, 1.56 * k, -0.06 * k], 0.24 * k, yaw=0.3, mustard=False)
    for a in (0.0, 2 * PI / 3, -2 * PI / 3):
        out.append(_rod([math.sin(a) * 0.36 * k, 1.10 * k, math.cos(a) * 0.36 * k],
                        [math.sin(a) * 0.60 * k, 0.0, math.cos(a) * 0.60 * k], 0.06 * k, steel,
                        m="metal"))
    return out


@JL23.gear("backyard_grill", "Backyard Grill",
           "Set the grill down, light it, and everybody on your side gathers round: "
           "patched up, well fed and spoiling for it. Anybody else who wanders over "
           "gets a hot coal.",
           {"kind": "deploy", "cooldown": 35, "sound": "crack",
            "deploy": {"type": "grill", "radius": 8.0, "secs": 12.0, "heal": 6.0, "limit": 1,
                       "color": "#ff8c1a", "particle": "puff", "name": "Backyard Grill",
                       "ally": {"might": [0.15, 1.0]}, "enemy": {"burn": [5, 1.2]}}},
           [["+", "Sets up a grill: teammates within 8 studs heal 6 a second and hit 15% "
                  "harder"],
            ["+", "Enemies who come too close get burnt"],
            ["-", "Runs out of charcoal in 12 seconds"],
            ["-", "35 second cooldown"]], rarity="rare",
           deploy=lambda: _grill_model(1.0))
def _():
    return at_frame(_grill_model(0.42), [0, -0.66, 0.36])


JL23.effect("burger_flip", name="Burger Flip", rate=2.2, life=[1.4, 1.9], size=[0.30, 0.42],
            grow=0.0, gravity=1.4, spread=0.35, rise=[1.6, 2.2], blend="normal", spin=7.0,
            colors=["#ffffff", "#fff0d8", "#ffe0b8"], shape="jl_burger", radius=0.5)
JL23.effect("picnic_ants", name="Picnic Ants", rate=5.0, life=[2.4, 3.2], size=[0.14, 0.18],
            grow=0.0, gravity=0.0, spread=0.05, rise=[0.0, 0.05], blend="normal", spin=0.0,
            colors=["#1a1a1a", "#2a1a12", "#3a2418"], shape="jl_ant", radius=0.9, orbit=1.2,
            upright=True, wobble=0.15)
JL23.opening(
    sky={"top": "#2a3f7a", "horizon": "#ff9a5a", "sun": [0.4, 0.3, 0.8], "clouds": 2,
         "tint": "#ffe0b0"},
    ambient="#a07a5a", beam="#ffb347", seep="picnic_ants", after="burger_flip",
    burst=["#ff8c1a", "#f2b705", "#c4281c", "#ffffff"],
    pieces=[{"shape": "jl_burger", "colors": ["#ffffff", "#fff0d8"], "blend": "normal"},
            {"shape": "jl_hotdog", "colors": ["#ffffff", "#fff0d8"], "blend": "normal"},
            {"shape": "puff", "colors": ["#c9ccd2", "#e3e6ea"], "blend": "normal"},
            {"shape": "spark", "colors": ["#ffb347", "#ff6a1a"], "blend": "add"}],
    backdrop="jl_cookout", title_wait="Firing up the grill...",
    title_shake="Something smells amazing...")
JL23.award("Backyard Cookout", ["Paper Plate", "Lawn Chair", "Condiment Wrangler",
                                "Patty Flipper", "Pitmaster", "Grill Master General"],
           "Opened Kettle Grill Crates at the Backyard Cookout, Fourth of July 2023.",
           "em_grill", "spangle")
JL23.bundle("pair", "Seconds", 1, 1050, "One Kettle Grill Crate, one Corn-Cob Key.")
JL23.bundle("potluck", "Potluck", 3, 3000, "Three grills, three keys. Saves 300.")



# ============================================================ 2024
VERDIGRIS = "#5fa89a"
PATINA = "#7fc4b4"
TIN = "#8a9098"
FLAME = "#ffc94a"
NIGHT = "#141a3a"


def _torch(at, k=1.0, r=None, lit=True, metal=GOLD):
    """Liberty's torch, its handle at ``at`` and the flame on top: a ribbed
    handle, a fluted cup, a gilded flame (``k`` is about its height)."""
    pieces = [
        part("cyl", [0, 0.20, 0], [0.14, 0.40, 0.14], metal, m="metal"),
        part("torus", [0, 0.40, 0], [0.18, 0.04, 0.18], metal, m="metal"),
        place("cone", [0, 0.52, 0], [0.38, 0.24, 0.38], metal, r=[PI, 0, 0], m="metal"),
        part("cyl", [0, 0.64, 0], [0.42, 0.04, 0.42], metal, m="metal"),
        place("flame", [0, 0.66, 0], [0.34, 0.46, 0.34], FLAME if lit else metal,
              anchor=[0, 0, 0], m="neon" if lit else "metal", spin=2.0 if lit else 0.0),
    ]
    return at_frame(pieces, at, r, k)


def _tin_lantern(at, k=1.0, lit=True):
    """A punched-tin lantern, middle at ``at``: a drum of pierced tin, a
    cone roof, a ring to hang it by and a glow inside."""
    pieces = [
        part("cyl", [0, 0, 0], [0.50, 0.56, 0.50], TIN, m="metal", decal="jl_punchtin", wrap=True),
        part("cyl", [0, -0.30, 0], [0.56, 0.05, 0.56], shade(TIN, 0.8), m="metal"),
        place("cone", [0, 0.40, 0], [0.58, 0.28, 0.58], TIN, m="metal", decal="jl_punchtin",
              wrap=True),
        part("torus", [0, 0.60, 0], [0.14, 0.03, 0.14], shade(TIN, 0.8), [PI / 2, 0, 0], m="metal"),
    ]
    if lit:
        pieces.append(part("sph", [0, 0, 0], [0.30, 0.34, 0.30], FLAME, m="neon", a=0.55))
    return at_frame(pieces, at, None, k)


JL24 = Event(
    "july4_2024", "july4", 2024, "jl24",
    name="Liberty Lights", title="Liberty Lights",
    blurb="The Fourth of July 2024 was a night for lanterns. Somebody built Lady Liberty "
          "on the hill above the harbour map, ten storeys of green copper, and lit the "
          "torch at dusk; the whole server walked up with tin lanterns and watched the "
          "fireflies come out. Nobody knows who built her. She is still there.",
    tagline="Lift your lamp. Bring a lantern.",
    starts="2024-06-27", ends="2024-07-11",
    colors={"accent": FLAME, "deep": NIGHT, "glow": "#fff3b0"},
    family_effects=["starstruck", "candlelight_vigil", "sunbeam"],
    hero_effect="firefly_waltz", stencil="stencil_jl24")


@JL24.crate_model("Tin Lantern Crate",
                  "A great colonial lantern of punched tin, stars and stripes pierced in it "
                  "so the light comes out in patterns, a cone roof and a ring to carry it "
                  "by. Holds the Liberty Lights set. Needs a Torch Key.",
                  hinge=[0, 0.50, -0.68], keyhole=[0.22, -0.02, 0.71])
def _():
    parts = [
        part("cyl", [0, -0.05, 0], [1.32, 1.10, 1.32], TIN, m="metal", decal="jl_punchtin",
             wrap=True),
        part("cyl", [0, -0.05, 0], [1.20, 1.00, 1.20], FLAME, m="neon", a=0.35),
        part("cyl", [0, -0.62, 0], [1.44, 0.10, 1.44], shade(TIN, 0.75), m="metal"),
        part("cyl", [0, 0.50, 0], [1.40, 0.08, 1.40], shade(TIN, 0.75), m="metal"),
        # the door, its hinges, and the latch (the lock)
        part("rbox", [0, -0.04, 0.665], [0.56, 0.74, 0.03], shade(TIN, 1.1), m="metal",
             decal="jl_punchtin"),
        part("rbox", [-0.29, 0.20, 0.68], [0.06, 0.10, 0.04], BLACK),
        part("rbox", [-0.29, -0.28, 0.68], [0.06, 0.10, 0.04], BLACK),
        part("rbox", [0.22, -0.02, 0.69], [0.16, 0.22, 0.05], BRASS, m="metal", decal="keyhole",
             lock=1),
        # the stencil on the back
        part("box", [0, -0.05, -0.665], [0.62, 0.42, 0.02], "#000000", [0, PI, 0],
             decal="stencil_jl24", a=-1),
        # the roof and the ring (the lid)
        place("cone", [0, 0.54, 0], [1.52, 0.70, 1.52], TIN, anchor=[0, -0.5, 0], m="metal",
              decal="jl_punchtin", wrap=True, lid=1),
        part("cyl", [0, 1.26, 0], [0.18, 0.08, 0.18], shade(TIN, 0.75), m="metal", lid=1),
        part("torus", [0, 1.44, 0], [0.36, 0.06, 0.36], shade(TIN, 0.75), [PI / 2, 0, 0],
             m="metal", lid=1),
    ]
    for a in (PI / 4, 3 * PI / 4, 5 * PI / 4, 7 * PI / 4):
        parts.append(part("sph", [math.cos(a) * 0.62, -0.70, math.sin(a) * 0.62],
                          [0.16, 0.10, 0.16], shade(TIN, 0.7), m="metal"))
    # fireflies come out with the light
    for x, y, z in ((0.80, 0.30, 0.40), (-0.86, 0.10, 0.30), (0.50, 0.86, -0.40)):
        parts.append(part("sph", [x, y, z], [0.07, 0.07, 0.07], "#e8ff7a", m="neon"))
    return parts


@JL24.key_model("Torch Key",
                "A key of green copper with Lady Liberty's torch for a bow, the flame "
                "gilded and lit. Opens one Tin Lantern Crate.", shoulder=-0.30)
def _():
    parts = _torch([-0.62, -0.30, 0], 0.80, metal=VERDIGRIS)
    parts += [
        part("cyl", [0.13, 0, 0], [0.09, 0.84, 0.09], VERDIGRIS, [0, 0, PI / 2], m="metal"),
        part("torus", [-0.27, 0, 0], [0.20, 0.07, 0.20], PATINA, [0, 0, PI / 2], m="metal"),
        part("rbox", [-0.46, 0, 0], [0.30, 0.08, 0.08], VERDIGRIS, m="metal"),
        part("rbox", [0.40, -0.12, 0], [0.08, 0.22, 0.08], VERDIGRIS, m="metal"),
        place("star", [0.54, -0.16, 0], 0.24, GOLD, m="metal"),
    ]
    return parts


@JL24.hat("liberty_crown", "Lady Liberty's Crown",
          "Green copper, a band of little windows and seven rays, one for each sea and "
          "each continent. Very heavy. Visitors keep trying to climb up inside it.",
          "legendary", hair="show")
def _():
    parts = [
        ringband(-0.24, 0.30, VERDIGRIS, m="metal", decal="jl_verdigris", wrap=True),
        ringband(-0.08, 0.06, PATINA, margin=0.06, m="metal"),
        ringband(-0.40, 0.06, PATINA, margin=0.06, m="metal"),
    ]
    # the windows round the band
    parts += around(9, 0.96, -0.24, lambda a, x, z: part(
        "rbox", [x, -0.24, z * 0.97], [0.12, 0.14, 0.02], "#dff6ff", [0, a, 0], m="glass",
        a=0.8), start=-TAU / 18)
    # seven rays fanning out from the top of the band, front and sides only
    for n in range(7):
        a = (n - 3) * 0.42
        x, z = math.sin(a) * 0.86, math.cos(a) * 0.84
        lean = 0.62 + abs(n - 3) * 0.06
        base = [x, -0.02, z]
        # each ray tips outwards, away from the middle of the head
        parts.append(place("cone", base, [0.20, 0.86, 0.20], VERDIGRIS, anchor=[0, -0.5, 0],
                           r=[lean * math.cos(a), 0, -lean * math.sin(a)], m="metal",
                           decal="jl_verdigris", wrap=True))
    return parts


@JL24.hat("firefly_jar", "Firefly Jar",
          "A mason jar, a punched-tin lid, and a summer night's catch of fireflies "
          "blinking inside. Let them go before bed. You will not.", "rare", hair="show")
def _():
    parts = [
        part("cyl", [0, 0.40, 0], [0.86, 0.76, 0.86], "#dff6ff", m="glass", a=0.35),
        part("cyl", [0, 0.82, 0], [0.70, 0.10, 0.70], "#dff6ff", m="glass", a=0.5),
        part("cyl", [0, 0.90, 0], [0.76, 0.10, 0.76], TIN, m="metal", decal="jl_punchtin",
             wrap=True),
        part("cyl", [0, 0.04, 0], [0.88, 0.06, 0.88], "#cfe4ea", m="glass", a=0.55),
        part("rbox", [0, 0.40, 0.44], [0.36, 0.22, 0.02], CREAM, [0, 0, 0], decal="jl_label"),
    ]
    for k in range(9):
        a = k * 2.4
        parts.append(part("sph", [math.sin(a) * 0.26, 0.16 + (k * 0.618 % 1) * 0.56,
                                  math.cos(a) * 0.26], [0.07, 0.07, 0.07],
                          "#e8ff7a" if k % 3 else "#fff3b0", m="neon"))
    return parts


@JL24.hat("paper_lanterns", "Paper Lantern Ring",
          "A string of red, white and blue paper lanterns round a band, each with a "
          "little light in it. Do not stand near the sparklers.", "uncommon", hair="show")
def _():
    parts = [ringband(-0.10, 0.08, "#3a2e22")]
    colours = (RED, CREAM, BLUE)
    for n in range(8):
        a = n * TAU / 8 + TAU / 16
        x, z = math.sin(a) * 1.00, math.cos(a) * 0.97
        c = colours[n % 3]
        parts += [part("cyl", [x, -0.06, z], [0.02, 0.10, 0.02], "#3a2e22"),
                  place("cask", [x, -0.36, z], [0.34, 0.38, 0.34], c, anchor=[0, 0, 0],
                        decal="jl_paperlantern", wrap=True),
                  part("sph", [x, -0.18, z], [0.16, 0.16, 0.16], FLAME, m="neon", a=0.6),
                  part("cyl", [x, -0.37, z], [0.24, 0.02, 0.24], "#3a2e22"),
                  part("cyl", [x, -0.03, z], [0.20, 0.02, 0.20], "#3a2e22")]
    return parts


@JL24.hat("lamplighter_cap", "Lamplighter's Cap",
          "A leather cap with a little tin lantern hung off the front of it, the way the "
          "old lamplighters went round at dusk. Lights the way. Also your face.", "rare")
def _():
    leather = "#5a3a22"
    parts = [
        cap(-0.30, 0.16, leather, grow=0.04, decal="leather", wrap=True),
        place("peak", [0, -0.24, 0], [1.80, 1.0, 1.70], shade(leather, 0.8), anchor=[0, 0, 0],
              decal="leather", wrap=True),
        band(-0.24, 0.08, BRASS, grow=0.06, m="metal"),
        part("rbox", [0, -0.02, 0.82], [0.10, 0.36, 0.08], BRASS, [-0.3, 0, 0], m="metal"),
        part("rbox", [0, 0.16, 0.92], [0.06, 0.06, 0.24], BRASS, m="metal"),
    ]
    parts += _tin_lantern([0, 0.0, 1.06], 0.56)
    return parts


@JL24.hat("starry_nightcap", "Summer Nightcap",
          "A long navy nightcap scattered with stars, a crescent moon on the bobble, and "
          "the tip flopped over. For watching the fireworks from bed.", "uncommon")
def _():
    parts = [
        dome(-0.30, 0.70, NIGHT, decal="jl_starsprinkle", wrap=True),
        ringband(-0.22, 0.20, CREAM, decal="knit", wrap=True),
    ]
    # the long tail of the cap, flopping over to one side and down
    path = [(0.0, 0.36, -0.04), (0.18, 0.70, -0.10), (0.46, 0.86, -0.16), (0.74, 0.74, -0.20),
            (0.88, 0.46, -0.22)]
    for n in range(len(path) - 1):
        parts.append(_rod(path[n], path[n + 1], 0.46 - n * 0.09, NIGHT, t="capsule",
                          decal="jl_starsprinkle", wrap=True))
    parts += [place("crescent", [0.90, 0.30, -0.22], 0.30, "#fff3b0", m="neon"),
              pompom([0.88, 0.40, -0.22], 0.20, CREAM)]
    return parts


@JL24.hat("firefly_antennae", "Lightning Bug",
          "A headband with two springy antennae, a glowing bead on each, for anybody "
          "who would rather be a firefly than watch them.", "uncommon", hair="show")
def _():
    black = "#1a1a20"
    parts = [
        part("rbox", [0, 0.035, 0], [1.00, 0.07, 0.16], black),
        *sides(lambda s: [
            part("rbox", [0.62 * s, -0.035, 0], [0.34, 0.07, 0.16], black, [0, 0, 0.55 * s]),
            part("rbox", [0.775 * s, -0.42, 0], [0.07, 0.62, 0.16], black),
            part("sph", [0.79 * s, -0.74, 0], [0.10, 0.10, 0.18], black),
        ]),
    ]
    for s in (1, -1):
        path = [(0.22 * s, 0.06, 0.04), (0.30 * s, 0.40, 0.14), (0.44 * s, 0.70, 0.20),
                (0.56 * s, 0.86, 0.12)]
        for n in range(len(path) - 1):
            parts.append(_rod(path[n], path[n + 1], 0.04, black))
        parts += [part("sph", [0.58 * s, 0.90, 0.10], [0.16, 0.16, 0.16], "#e8ff7a", m="neon"),
                  part("sph", [0.58 * s, 0.90, 0.10], [0.30, 0.30, 0.30], "#e8ff7a", m="neon",
                       a=0.25)]
    return parts


@JL24.hat("sky_bowler", "Night-Sky Bowler",
          "A navy bowler with the night printed on it -- every constellation over the "
          "harbour on the Fourth -- and a shooting star pinned to the band.", "rare")
def _():
    return [
        place("brim", [0, -0.05, 0], [2.06, 1.2, 1.98], NIGHT, anchor=[0, 0, 0],
              decal="jl_starsprinkle", wrap=True),
        dome(-0.05, 0.82, NIGHT, decal="jl_starsprinkle", wrap=True),
        ringband(0.06, 0.16, "#c9a227", m="metal"),
        place("star", [0.40, 0.14, 0.86], 0.26, "#fff3b0", r=[-0.1, 0.42, 0], m="neon"),
        _rod([0.40, 0.14, 0.86], [0.70, 0.02, 0.66], 0.03, "#fff3b0", m="neon", a=0.7),
        _rod([0.70, 0.02, 0.66], [0.92, -0.06, 0.42], 0.02, "#fff3b0", m="neon", a=0.4),
    ]


@JL24.back("liberty_tablet", "Liberty's Tablet",
           "The stone tablet off the statue, JULY IV MDCCLXXVI cut into it, strapped on "
           "like a shield and carried with exactly as much dignity as you can manage.",
           "legendary")
def _():
    return straps("#3a2e22") + [
        part("rbox", [0, 0.24, -0.26], [1.20, 1.60, 0.24], VERDIGRIS, [0, 0, 0.08],
             m="metal", decal="jl_verdigris", wrap=True),
        part("rbox", [0, 0.24, -0.39], [1.04, 1.40, 0.02], "#000000", [0, PI, -0.08],
             decal="jl_tablet", a=-1),
        part("rbox", [0, 1.06, -0.26], [1.26, 0.10, 0.28], PATINA, [0, 0, 0.08], m="metal"),
        part("rbox", [0, -0.58, -0.26], [1.26, 0.10, 0.28], PATINA, [0, 0, 0.08], m="metal"),
    ]


@JL24.back("lantern_yoke", "Lamplighter's Yoke",
           "A shoulder yoke with a tin lantern swinging from either end. You light up "
           "the path for everybody walking behind you, and blind everybody in front.",
           "rare")
def _():
    wood = "#8a5a2a"
    parts = straps("#3a2e22") + [
        part("rbox", [0, 1.04, -0.30], [3.20, 0.12, 0.16], wood, decal="planks", wrap=True),
        part("rbox", [0, 1.04, -0.14], [0.70, 0.10, 0.22], wood),
    ]
    for s in (1, -1):
        parts += [_rod([1.48 * s, 1.00, -0.30], [1.48 * s, 0.66, -0.30], 0.03, "#3a2e22")]
        parts += _tin_lantern([1.48 * s, 0.38, -0.30], 0.80)
    return parts


@JL24.hairdo("verdigris_waves", "Copper Waves",
             "Heavy waves of hair gone green as an old penny, swept back under the crown "
             "like hers. One hundred and forty years of sea air will do that.", "rare")
def _():
    c = "#5fa89a"
    parts = [place("hairlong", [0, 0, 0], [1.05, 1.05, 1.05], c, anchor=[0, 0, 0],
                   decal="jl_verdigris", wrap=True, m="metal")]
    for k, (x, z) in enumerate(((0.40, -0.40), (0.0, -0.56), (-0.40, -0.40))):
        parts.append(place("spiral", [x, -0.50, z], [0.30, 0.50, 0.30], shade(c, 1.1 if k % 2 else 0.9),
                           anchor=[0, 0.5, 0], m="metal"))
    return parts


@JL24.hairdo("firefly_braids", "Firefly Braids",
             "Two long dark braids with little glowing beads woven into them, as if the "
             "fireflies got caught on the way past.", "uncommon")
def _():
    c = "#2a1e1a"
    parts = [place("hairmid", [0, 0, 0], [1.03, 1.03, 1.03], c, anchor=[0, 0, 0],
                   decal="strands", wrap=True)]
    for s in (1, -1):
        for n in range(5):
            parts.append(part("sph", [0.52 * s, -0.30 - n * 0.20, -0.10 - n * 0.02],
                              [0.22 - n * 0.01, 0.24, 0.20], shade(c, 1.1 if n % 2 else 0.95)))
            if n % 2:
                parts.append(part("sph", [0.60 * s, -0.30 - n * 0.20, -0.04],
                                  [0.07, 0.07, 0.07], "#e8ff7a", m="neon"))
        parts.append(part("cyl", [0.52 * s, -1.30, -0.20], [0.14, 0.06, 0.14], RED))
    return parts


JL24.face("torchlit", "Torchlit",
          "Wide eyes with a lantern flame in each, cheeks warm from standing too close, "
          "and a hushed little 'oh'.", [
              {"k": "ellipse", "x": -0.20, "y": -0.13, "w": 0.12, "h": 0.14, "c": "#16171b"},
              {"k": "ellipse", "x": 0.20, "y": -0.13, "w": 0.12, "h": 0.14, "c": "#16171b"},
              {"k": "poly", "pts": [[-0.20, -0.20], [-0.17, -0.12], [-0.20, -0.08], [-0.23, -0.12]],
               "c": "#ffc94a"},
              {"k": "poly", "pts": [[0.20, -0.20], [0.23, -0.12], [0.20, -0.08], [0.17, -0.12]],
               "c": "#ffc94a"},
              {"k": "ellipse", "x": -0.32, "y": 0.06, "w": 0.12, "h": 0.06, "c": "#ffb08a"},
              {"k": "ellipse", "x": 0.32, "y": 0.06, "w": 0.12, "h": 0.06, "c": "#ffb08a"},
              {"k": "ellipse", "x": 0.0, "y": 0.14, "w": 0.07, "h": 0.08, "c": "#16171b"},
          ], "uncommon")
JL24.face("starry_eyed", "Starry-Eyed",
          "Stars where the pupils should be and a grin that has not stopped since the "
          "first rocket went up.", [
              {"k": "ellipse", "x": -0.20, "y": -0.13, "w": 0.16, "h": 0.16, "c": "#22306e"},
              {"k": "ellipse", "x": 0.20, "y": -0.13, "w": 0.16, "h": 0.16, "c": "#22306e"},
              {"k": "star", "x": -0.20, "y": -0.13, "r": 0.06, "c": "#ffffff"},
              {"k": "star", "x": 0.20, "y": -0.13, "r": 0.06, "c": "#ffffff"},
              {"k": "arc", "x": 0.0, "y": 0.0, "r": 0.24, "a0": 0.06, "a1": 0.44, "w": 0.04,
               "c": "#16171b"},
              {"k": "star", "x": 0.34, "y": -0.30, "r": 0.03, "c": "#c8202f"},
          ], "rare")
JL24.shirt("liberty_robe", "Liberty's Robe",
           "Green copper drapery from the shoulder, folded the way it has been since "
           "1886, and a tablet's worth of gravitas.",
           {"torso": VERDIGRIS, "arms": VERDIGRIS, "decal": "jl_tee_toga", "weave": "jl_verdigris"},
           "rare")
JL24.pants("star_field", "Star-Field Trousers",
           "Navy trousers with the whole summer sky printed on them, and a gold stripe "
           "down the side.",
           {"legs": NIGHT, "weave": "jl_starsprinkle", "stripe": "#c9a227"})
JL24.belt("punched_tin_belt", "Punched-Tin Belt",
          "A belt of pierced tin plates, a star for a buckle, and a light inside every "
          "plate.",
          {"band": TIN, "buckle": FLAME, "width": 0.22, "weave": "jl_punchtin", "metal": True,
           "glow": True})


@JL24.weapon("liberty_torch", "Liberty's Torch",
             "The torch itself, lifted off the statue. Every swing sets whoever it hits "
             "alight -- and while it is swinging, its flare turns blows aside and throws "
             "whoever struck them back.",
             {"kind": "melee", "damage": 24, "headshot": 1.0, "rpm": 96, "range": 10.0,
              "arc": 0.66, "sound": "swing", "knockback": 8,
              "on_hit": {"burn": [5, 3.0]},
              "parry": {"secs": 0.45, "reduce": 0.70, "reflect": 28}},
             [["+", "Sets its target alight: 5 a second for 3 seconds"],
              ["+", "Every swing opens a guard: 70% less damage for 0.45 seconds, and "
                    "whoever hits you is thrown back"],
              ["-", "Only 24 damage a swing"],
              ["-", "Time the guard wrong and it is gone"]], rarity="legendary")
def _():
    return _torch([0, -0.10, 0.10], 1.60, r=[PI / 2 - 0.2, 0, 0])


@JL24.weapon("signal_flare", "Signal Flare Pistol",
             "A brass flare pistol that fires a ball of red fire. Whoever it hits is "
             "dazzled, and where it lands it keeps burning for a good while -- two if by "
             "sea.",
             {"kind": "projectile", "projectile": "flare", "damage": 20, "splash": 3.5,
              "splash_damage": 18, "rpm": 50, "mag": 2, "reload": 2.4, "speed": 72,
              "range": 260, "auto": False, "sound": "pop", "recoil": 1.0, "reserve": 18,
              "gravity_scale": 0.35, "self_damage": 0.0, "knockback": 4,
              "on_hit": {"blind": [1.2, "flash"]},
              "ground_fire": {"radius": 4.5, "secs": 5.0, "dps": 7, "color": "#ff5a3a",
                              "particle": "flame", "name": "Signal Fire"},
              "trail_colors": ["#ff5a3a", "#ffc94a"]},
             [["+", "Dazzles whoever it hits for 1.2 seconds"],
              ["+", "Leaves a patch of burning flare for 5 seconds: 7 a second to anyone "
                    "standing in it"],
              ["-", "A little 18 damage blast"],
              ["-", "Two shots, then a reload"]], rarity="legendary",
             proj=lambda: [part("sph", [0, 0, 0], [0.46, 0.46, 0.46], "#ff5a3a", m="neon"),
                           part("sph", [0, 0, 0], [0.80, 0.80, 0.80], "#ffc94a", m="neon",
                                a=0.35)])
def _():
    brass = "#c9a227"
    return [
        part("rbox", [0, -0.20, -0.04], [0.16, 0.42, 0.24], "#5a3a22", [-0.3, 0, 0],
             decal="leather"),
        part("cyl", [0, 0.04, 0.36], [0.30, 0.70, 0.30], brass, [PI / 2, 0, 0], m="metal"),
        part("torus", [0, 0.04, 0.72], [0.32, 0.05, 0.32], shade(brass, 0.8), [PI / 2, 0, 0],
             m="metal"),
        part("cyl", [0, 0.04, 0.73], [0.18, 0.02, 0.18], "#ff5a3a", [PI / 2, 0, 0], m="neon"),
        part("rbox", [0, -0.06, 0.04], [0.10, 0.08, 0.14], shade(brass, 0.7), m="metal"),
        part("torus", [0, -0.14, 0.12], [0.16, 0.03, 0.16], brass, [0, PI / 2, 0], m="metal"),
    ]


@JL24.weapon("midnight_lantern", "Midnight Ride Lantern",
             "One if by land. Hang the lantern up and everybody sees you there, standing "
             "in its light; by the time they get close, you have been gone a while.",
             {"kind": "deploy", "cooldown": 20, "sound": "magic",
              "deploy": {"type": "decoy", "hp": 80, "secs": 8.0, "cloak": 5.0, "limit": 1}},
             [["+", "Leaves a double of you standing in the lantern-light for 8 seconds"],
              ["+", "You slip away near-invisible for 5 seconds"],
              ["-", "The double has 80 health, and does nothing but stand there"],
              ["-", "20 second cooldown"]], rarity="legendary")
def _():
    parts = [part("cyl", [0, 0.30, 0.10], [0.05, 0.70, 0.05], "#3a2e22"),
             part("rbox", [0, 0.66, 0.24], [0.04, 0.04, 0.30], "#3a2e22")]
    parts += _tin_lantern([0, 0.42, 0.36], 0.60)
    return parts


@JL24.gear("sweet_tea", "Porch Sweet Tea",
           "A mason jar of sweet tea off the porch, ice and lemon and all. Cures what "
           "ails you, and there is plenty to go round.",
           {"kind": "consume", "cooldown": 28, "sound": "drink",
            "consume": {"cleanse": True, "regen": [4.0, 6.0], "share": 10}},
           [["+", "Shakes off every burn, poison, slow and mark on you"],
            ["+", "Heals 4 a second for 6 seconds"],
            ["+", "Teammates within 10 studs get a share"],
            ["-", "28 second cooldown"]], rarity="rare")
def _():
    return [
        part("cyl", [0, 0.30, 0.14], [0.44, 0.56, 0.44], "#dff6ff", m="glass", a=0.4),
        part("cyl", [0, 0.24, 0.14], [0.40, 0.42, 0.40], "#b8742a", a=0.85),
        part("cyl", [0, 0.60, 0.14], [0.46, 0.06, 0.46], TIN, m="metal"),
        part("rbox", [0.06, 0.40, 0.14], [0.12, 0.12, 0.12], "#eef8ff", [0.4, 0.4, 0], m="glass",
             a=0.7),
        part("cyl", [0.12, 0.50, 0.24], [0.16, 0.03, 0.16], "#ffe066", [0.4, 0, 0.6]),
        _rod([-0.08, 0.30, 0.14], [-0.16, 0.86, 0.10], 0.04, RED),
    ]


JL24.effect("firefly_waltz", name="Firefly Waltz", rate=6.0, life=[1.6, 2.4],
            size=[0.10, 0.16], grow=0.0, gravity=0.0, spread=0.5, rise=[0.0, 0.2],
            blend="add", spin=0.0, colors=["#e8ff7a", "#fff3b0", "#c8ff5a"],
            shape="spark", radius=1.0, orbit=1.0, wobble=0.6)
JL24.effect("torchlight", name="Torchlight", rate=5.0, life=[1.0, 1.6],
            size=[0.24, 0.36], grow=-0.2, gravity=-1.6, spread=0.3, rise=[0.6, 1.0],
            blend="add", spin=0.5, colors=["#ffc94a", "#ff8a2a", "#fff3b0"],
            shapes=["flame", "flame", "spark"], radius=0.4)
JL24.opening(
    sky={"top": "#070a1e", "horizon": NIGHT, "sun": [0.2, 0.9, 0.6], "clouds": 0,
         "tint": "#ffe0a8"},
    ambient="#5a5a7a", beam=FLAME, seep="firefly_waltz", after="torchlight",
    burst=[FLAME, "#e8ff7a", RED, "#ffffff"],
    pieces=[{"shape": "spark", "colors": ["#e8ff7a", "#fff3b0"], "blend": "add"},
            {"shape": "star", "colors": ["#ffffff", "#ffc94a"], "blend": "normal"},
            {"shape": "flame", "colors": ["#ffc94a", "#ff8a2a"], "blend": "add"},
            {"shape": "jl_pennant", "colors": [RED, CREAM, BLUE], "blend": "normal"}],
    backdrop="jl_liberty", title_wait="Somebody is lighting the lanterns...",
    title_shake="The torch is catching...")
JL24.award("Liberty Lights", ["Lantern Bearer", "Firefly Catcher", "Lamplighter",
                              "Torchbearer", "Keeper of the Flame", "Lady Liberty"],
           "Opened Tin Lantern Crates during Liberty Lights, the Fourth of July 2024.",
           "em_torch", "spangle")
JL24.bundle("pair", "Lantern and Torch", 1, 1050, "One Tin Lantern Crate, one Torch Key.")
JL24.bundle("parade", "Lantern Parade", 3, 3000, "Three lanterns, three keys. Saves 300.")

# ============================================================ 2025
JL25_BRICK = "#c0644a"
JL25_STONE = "#cfc6b0"
JL25_GRASS = "#4f8a3a"
JL25_SAND = "#d8c890"
JL25_SEA = "#2a5a8a"
JL25_IRON = "#2e3034"
JL25_HIVIS = "#f2d23a"
JL25_HAT = "#d8282a"
JL25_FUSE = "#3a3226"
JL25_EMBER = "#ff6a2a"
JL25_SPARK = "#fff3b0"
JL25_NIGHT = "#0e1430"
JL25_WOOD = "#7a5230"
JL25_SLATE = "#4a5060"
# the star fort: five bastions, their points R_OUT out, the re-entrant
# angles between them R_IN in
JL25_OUT, JL25_IN = 0.80, 0.50


def _jl25_star(n):
    """The ten corners of the fort's outline, point and re-entrant angle in
    turn, its first point at the back (-Z)."""
    a = PI + n * PI / 5
    r = JL25_OUT if n % 2 == 0 else JL25_IN
    return [math.sin(a) * r, math.cos(a) * r]


def _jl25_fort(h=0.60, brick=JL25_BRICK, **kw):
    """A five-bastioned star fort, its foot on the origin and its walls
    ``h`` high: a round keep of brick, a triangular bastion on every side,
    and a stone parapet along the top of the whole outline."""
    base = JL25_IN * math.cos(PI / 5)
    width = 2 * JL25_IN * math.sin(PI / 5)
    parts = [part("cyl", [0, h / 2, 0], [2 * JL25_IN, h, 2 * JL25_IN], brick, decal="bricks", wrap=True,
                  **kw)]
    for n in range(5):
        a = PI + n * TAU / 5
        mid = (base + JL25_OUT) / 2
        parts.append(part("tri", [math.sin(a) * mid, h / 2, math.cos(a) * mid], [width, JL25_OUT - base, h],
                          brick, [PI / 2, a, 0], decal="bricks", wrap=True, **kw))
    for n in range(10):
        p, q = _jl25_star(n), _jl25_star(n + 1)
        mx, mz = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
        ml = math.hypot(mx, mz)
        mx, mz = mx * (1 - 0.035 / ml), mz * (1 - 0.035 / ml)
        length = math.hypot(q[0] - p[0], q[1] - p[1])
        parts.append(part("rbox", [mx, h + 0.035, mz], [0.07, 0.07, length + 0.04], JL25_STONE,
                          [0, math.atan2(q[0] - p[0], q[1] - p[1]), 0], **kw))
    return parts


def _jl25_cannon(at, a, k=1.0, **kw):
    """A cannon on its carriage at ``at``, its muzzle out along the angle
    ``a`` (0 is +Z), cocked up a little."""
    x, y, z = at
    s, c = math.sin(a), math.cos(a)
    out = [
        part("rbox", [x, y + 0.04 * k, z], [0.16 * k, 0.08 * k, 0.24 * k], JL25_WOOD, [0, a, 0], **kw),
        part("cyl", [x + s * 0.07 * k, y + 0.12 * k, z + c * 0.07 * k], [0.09 * k, 0.36 * k, 0.09 * k],
             JL25_IRON, [PI / 2 - 0.18, a, 0], m="metal", **kw),
        part("sph", [x - s * 0.10 * k, y + 0.09 * k, z - c * 0.10 * k], [0.10 * k, 0.10 * k, 0.10 * k],
             JL25_IRON, m="metal", **kw),
    ]
    for side in (1, -1):
        out.append(part("cyl", [x + c * 0.09 * k * side, y + 0.04 * k, z - s * 0.09 * k * side],
                        [0.12 * k, 0.03 * k, 0.12 * k], JL25_WOOD, [0, a, PI / 2], **kw))
    return out


def _jl25_mortars(at, a, k=1.0, launch=False, **kw):
    """A rack of four firework mortars on a board at ``at``, splayed out
    along the angle ``a``, their fuses joined -- and, ``launch``, a shell
    just leaving one of them in a streak of sparks."""
    x, y, z = at
    s, c = math.sin(a), math.cos(a)
    out = [part("rbox", [x, y + 0.025 * k, z], [0.26 * k, 0.05 * k, 0.26 * k], JL25_WOOD, [0, a, 0],
                decal="planks", **kw)]
    tubes = []
    for i, (u, v) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
        px = x + (u * c + v * s) * 0.065 * k
        pz = z + (-u * s + v * c) * 0.065 * k
        tubes.append([px, y + 0.05 * k, pz])
        out += [part("cyl", [px, y + 0.15 * k, pz], [0.10 * k, 0.20 * k, 0.10 * k],
                     [NAVY, RED, RED, NAVY][i], [0.12 * v, a, 0.12 * u], decal="jl25_tube", wrap=True, **kw),
                part("cyl", [px, y + 0.255 * k, pz], [0.075 * k, 0.012 * k, 0.075 * k], "#1a1a1a", **kw)]
    for p, q in zip(tubes, tubes[1:]):
        out.append(rod(p, q, 0.018 * k, JL25_FUSE, **kw))
    if launch:
        t = tubes[3]
        out += [rod([t[0], t[1] + 0.30 * k, t[2]], [t[0], t[1] + 0.95 * k, t[2]], 0.035 * k, JL25_EMBER,
                    m="neon", a=0.7, **kw),
                part("sph", [t[0], t[1] + 1.02 * k, t[2]], [0.11 * k, 0.11 * k, 0.11 * k], JL25_SPARK, m="neon",
                     **kw),
                place("sparkle", [t[0], t[1] + 1.02 * k, t[2]], 0.26 * k, JL25_SPARK, m="neon", spin=6.0, **kw)]
    return out


JL25 = Event(
    "july4_2025", "july4", 2025, "jl25",
    name="Rocket's Red Glare", title="Rocket's Red Glare",
    blurb="Blockhaven fires its Fourth of July show from the old star fort out in the "
          "harbour, and in 2025 the pyro crew had a plan: load the whole season's stock "
          "into the fort's powder magazine and light everything at once. The barrage "
          "went on all night. Nobody on the shore slept. At dawn the smoke cleared, the "
          "crew climbed out of the moat one by one, and the great flag was still there.",
    tagline="Light the fuse. Walk -- do not run -- away.",
    starts="2025-06-27", ends="2025-07-11",
    colors={"accent": "#ff3a2a", "deep": JL25_NIGHT, "glow": "#ffb04a"},
    family_effects=["ember_storm", "scorching", "starstruck"],
    hero_effect="rockets_red_glare", stencil="stencil_jl25")

JL25_K = 0.88          # the crate's island, scaled to the stage


@JL25.crate_model("Star Fort",
                  "The old star fort in the harbour on its little island: five brick "
                  "bastions, cannons on the seaward ones and firework mortars on the "
                  "others, a gatehouse with the lock in it, and the parade ground lifting "
                  "off with the powder magazine and the great garrison flag still flying. "
                  "Holds the Rocket's Red Glare set. Needs a Rampart Key.",
                  hinge=[0, -0.15 * JL25_K, -0.44 * JL25_K],
                  keyhole=[0.13 * JL25_K, -0.62 * JL25_K, 0.69 * JL25_K])
def _():
    y0, h = -0.80, 0.62
    top = y0 + h
    parts = [
        # the harbour, the beach and the island's turf
        part("cyl", [0, -0.885, 0], [2.10, 0.05, 2.10], JL25_SEA, m="glass", decal="jl25_water"),
        part("cyl", [0, -0.855, 0], [1.98, 0.05, 1.98], JL25_SAND),
        part("cyl", [0, -0.82, 0], [1.90, 0.04, 1.90], JL25_GRASS, decal="jl_grass", wrap=True),
    ]
    parts += at_frame(_jl25_fort(h), [0, y0, 0])
    parts += [
        # the gatehouse in the front angle, its arch, its sign and the lock
        part("rbox", [0, y0 + 0.24, 0.53], [0.42, 0.48, 0.24], JL25_BRICK, decal="bricks", wrap=True),
        part("rbox", [0, y0 + 0.50, 0.53], [0.46, 0.05, 0.28], JL25_STONE),
        part("rbox", [0, y0 + 0.12, 0.652], [0.17, 0.24, 0.02], "#2a1e16"),
        part("cyl", [0, y0 + 0.24, 0.652], [0.17, 0.02, 0.17], "#2a1e16", [PI / 2, 0, 0]),
        part("box", [0, y0 + 0.38, 0.651], [0.32, 0.10, 0.01], "#000000", decal="jl25_plaque", a=-1),
        part("rbox", [0.13, y0 + 0.18, 0.66], [0.09, 0.12, 0.03], BRASS, m="metal", decal="keyhole",
             lock=1),
        # the light inside, at the seam
        part("cyl", [0, top + 0.005, 0], [0.90, 0.03, 0.90], "#ffd38a", m="neon"),
        # the lid: the parade ground, its magazine, the shot, the flag
        part("cyl", [0, top + 0.04, 0], [0.94, 0.06, 0.94], "#9a8a6a", lid=1),
        part("rbox", [0.14, top + 0.17, 0.08], [0.34, 0.20, 0.26], JL25_BRICK, decal="bricks", wrap=True,
             lid=1),
        part("cyl", [0.14, top + 0.255, 0.08], [0.26, 0.36, 0.26], JL25_SLATE, [0, 0, PI / 2], lid=1),
        part("box", [0.14, top + 0.15, 0.212], [0.14, 0.14, 0.01], "#000000", decal="jl25_powder", a=-1,
             lid=1),
        *[part("sph", p, [0.07, 0.07, 0.07], JL25_IRON, m="metal", lid=1)
          for p in ([-0.22, top + 0.105, 0.20], [-0.15, top + 0.105, 0.20], [-0.185, top + 0.105, 0.14],
                    [-0.185, top + 0.165, 0.18])],
    ]
    flag = _flag([-0.20, top + 0.07, -0.18], 1.0, 0.0, pole=1.10, decal="jl25_garrison")
    parts += [dict(p, lid=1) for p in flag]
    # cannons on the three seaward bastions, mortars on the two by the gate
    for n in range(5):
        a = PI + n * TAU / 5
        r = 0.56
        spot = [math.sin(a) * r, top + 0.07, math.cos(a) * r]
        if n in (0, 1, 4):
            parts += _jl25_cannon(spot, a, 1.0)
        else:
            parts += _jl25_mortars(spot, a, 1.0, launch=(n == 2))
    # the stencil, on a notice board on the beach behind
    parts += [rod([-0.22, -0.84, -0.92], [-0.22, -0.40, -0.92], 0.04, JL25_WOOD),
              rod([0.22, -0.84, -0.92], [0.22, -0.40, -0.92], 0.04, JL25_WOOD),
              part("rbox", [0, -0.50, -0.92], [0.60, 0.34, 0.03], "#e8dcc0"),
              part("box", [0, -0.50, -0.94], [0.54, 0.30, 0.01], "#000000", [0, PI, 0], decal="stencil_jl25",
                   a=-1)]
    return at_frame(parts, [0, 0, 0], k=JL25_K)


@JL25.key_model("Rampart Key",
                "A brass key with a five-pointed star for a bow -- the fort seen from the "
                "sky -- a red star in the middle with a fuse curling out of it, and a bit "
                "cut like battlements. Opens one Star Fort. Keep it dry.", shoulder=-0.36)
def _():
    x0 = -0.62
    return [
        place("star", [x0, 0, 0], [0.62, 0.62, 0.60], BRASS, m="metal", decal="rivets"),
        place("star", [x0, 0.0, 0.05], [0.34, 0.34, 0.30], RED, m="glass"),
        part("sph", [x0, 0.0, 0.08], [0.08, 0.08, 0.05], WHITE),
        rod([x0 + 0.02, 0.18, 0.04], [x0 + 0.10, 0.36, 0.06], 0.025, JL25_FUSE),
        place("sparkle", [x0 + 0.11, 0.38, 0.06], 0.16, JL25_SPARK, m="neon", spin=6.0),
        part("torus", [-0.34, 0, 0], [0.18, 0.18, 0.18], BRASS, [0, 0, PI / 2], m="metal"),
        part("cyl", [0.06, 0, 0], [0.09, 0.80, 0.09], BRASS, [0, 0, PI / 2], m="metal"),
        part("sph", [0.47, 0, 0], [0.11, 0.11, 0.11], BRASS, m="metal"),
        # the bit: a wall and three merlons
        part("rbox", [0.34, -0.10, 0], [0.26, 0.08, 0.07], BRASS, m="metal"),
        *[part("rbox", [0.24 + 0.10 * n, -0.18, 0], [0.06, 0.08, 0.07], BRASS, m="metal") for n in range(3)],
    ]


# ================================================================== hats
@JL25.hat("pyro_hard_hat", "Pyro Crew Hard Hat",
          "Bright red, stickered all over, ear defenders clamped on the sides and a "
          "face shield flipped up because you cannot see the fuse through it. The "
          "crew wore these all night. The crew cannot hear you.", "uncommon")
def _():
    crown = dome(-0.34, 0.82, JL25_HAT, t="capcrown", decal="jl25_hardhat", wrap=True)
    top = crown["p"][1] + crown["s"][1] / 2
    parts = [
        crown,
        ringband(-0.30, 0.05, shade(JL25_HAT, 0.85), margin=0.16),
        place("peak", [0, -0.30, 0.0], [1.30, 1.0, 1.80], shade(JL25_HAT, 0.92), anchor=[0, 0, 0]),
        part("rbox", [0, top - 0.02, -0.05], [0.16, 0.07, 1.10], shade(JL25_HAT, 1.08)),
        # the face shield, flipped up against the crown
        part("rbox", [0, 0.22, 0.64], [1.26, 0.40, 0.03], "#bfe0ff", [-1.18, 0, 0], m="glass", a=0.45),
    ]
    for s in (1, -1):
        parts += [
            part("cyl", [0.86 * s, -0.64, 0.0], [0.36, 0.13, 0.36], "#2e3238", [0, 0, PI / 2]),
            part("cyl", [0.80 * s, -0.64, 0.0], [0.30, 0.03, 0.30], "#1a1c20", [0, 0, PI / 2]),
            part("cyl", [0.93 * s, -0.64, 0.0], [0.18, 0.02, 0.18], JL25_HIVIS, [0, 0, PI / 2]),
            rod([0.86 * s, -0.47, 0.0], [0.86 * s, -0.31, 0.0], 0.05, JL25_HIVIS),
            part("cyl", [0.80 * s, 0.10, 0.50], [0.08, 0.06, 0.08], "#1a1c20", [0, 0, PI / 2]),
        ]
    return parts


@JL25.hat("garrison_shako", "Garrison Shako",
          "The fort's own: tall blue felt, a leather peak, the brass plate with the "
          "eagle on it, a cockade and a red-over-white plume that adds a foot to you. "
          "Regulation. The regulations were written in 1812 and nobody has dared "
          "change them.", "rare")
def _():
    parts = [
        place("flare", [0, -0.40, 0], [2.06, 1.00, 2.00], NAVY, anchor=[0, 0, 0], decal="felt", wrap=True),
        part("cyl", [0, 0.585, 0], [2.06, 0.05, 2.00], BLACK, decal="leather"),
        part("torus", [0, 0.56, 0], [2.08, 0.25, 2.02], GOLD, m="metal"),
        ringband(-0.36, 0.08, BLACK, margin=0.05, decal="leather"),
        place("peak", [0, -0.36, 0.0], [1.30, 1.0, 1.80], BLACK, anchor=[0, 0, 0], decal="leather"),
        place("shield", [0, 0.06, 0.885], [0.46, 0.52, 0.5], BRASS, r=[-0.05, 0, 0], m="metal",
              decal="jl25_shakoplate"),
        # the plume, red over white
        part("capsule", [0, 1.00, 0.78], [0.26, 0.84, 0.26], WHITE, decal="felt", wrap=True),
        part("capsule", [0, 1.52, 0.78], [0.23, 0.52, 0.23], RED, decal="felt", wrap=True),
        part("cyl", [0, 0.62, 0.80], [0.14, 0.10, 0.14], GOLD, m="metal"),
        # the cords swagged across the front
        rod([-0.70, 0.20, 0.66], [0.0, 0.02, 0.92], 0.04, WHITE),
        rod([0.0, 0.02, 0.92], [0.70, 0.20, 0.66], 0.04, WHITE),
    ]
    parts += _rosette([0, 0.42, 0.93], 0.70)
    return parts


@JL25.hat("finale_rack", "The Finale Rack",
          "Nine mortars on a board on your head, fused together, and the middle one has "
          "just gone: a streak of sparks straight up and a shell bursting red, white and "
          "blue overhead, every single time. The crew built it as a joke. Then they ran "
          "out of mortars and used it for real.", "legendary")
def _():
    parts = [
        cap(-0.22, 0.06, JL25_WOOD, decal="planks", wrap=True),
        band(-0.18, 0.08, shade(JL25_WOOD, 0.8)),
        part("rbox", [0, 0.11, 0], [1.40, 0.10, 1.34], JL25_WOOD, decal="planks", wrap=True),
    ]
    tubes = []
    for i, z in enumerate((-0.40, 0.0, 0.40)):
        for j, x in enumerate((-0.42, 0.0, 0.42)):
            c = [NAVY, RED, WHITE][(i + j) % 3]
            tubes.append([x, 0.16, z])
            parts += [part("cyl", [x, 0.38, z], [0.30, 0.44, 0.30], c, [0.12 * (z / 0.40), 0, -0.12 * (x / 0.42)],
                           decal="jl25_tube", wrap=True),
                      part("cyl", [x * 1.04, 0.605, z * 1.04], [0.22, 0.02, 0.22], "#1a1a1a")]
    for p, q in zip(tubes, tubes[1:]):
        parts.append(rod([p[0], 0.17, p[2]], [q[0], 0.17, q[2]], 0.03, JL25_FUSE))
    # the middle one has just gone: the trail, the smoke, the burst
    parts += [rod([0, 0.66, 0], [0, 1.50, 0], 0.05, JL25_EMBER, m="neon", a=0.75),
              part("sph", [0, 0.70, 0], [0.30, 0.18, 0.30], "#c8c8cc", a=0.55),
              part("sph", [0, 1.62, 0], [0.16, 0.16, 0.16], JL25_SPARK, m="neon")]
    for n in range(14):
        a = n * TAU / 14
        tilt = 0.55 if n % 2 else -0.35
        d = [math.sin(a) * math.cos(tilt), math.sin(tilt), math.cos(a) * math.cos(tilt)]
        c = [RED, WHITE, "#4a7ae8"][n % 3]
        tip = [d[0] * 0.70, 1.62 + d[1] * 0.70, d[2] * 0.70]
        parts += [rod([d[0] * 0.14, 1.62 + d[1] * 0.14, d[2] * 0.14], tip, 0.035, c, m="neon"),
                  part("sph", tip, [0.09, 0.09, 0.09], c, m="neon")]
    return parts


@JL25.hat("star_fort_cap", "Star Fort Cap",
          "The fort itself, all five bastions of it, on a turf cap: the guns run out, the "
          "magazine in the middle and the flag on its pole. Defended, at all times, by "
          "whoever is wearing it. Has never fallen.", "legendary")
def _():
    parts = [
        cap(-0.22, 0.06, JL25_GRASS, decal="jl_grass", wrap=True),
        band(-0.18, 0.08, JL25_SAND),
    ]
    k, h = 0.84, 0.36
    parts += at_frame(_jl25_fort(h), [0, 0.06, 0], k=k)
    top = 0.06 + (h + 0.07) * k
    parts += [part("cyl", [0, top - 0.02, 0], [0.80, 0.03, 0.80], "#9a8a6a"),
              part("rbox", [0.12, top + 0.07, 0.06], [0.28, 0.16, 0.22], JL25_BRICK, decal="bricks", wrap=True),
              part("cyl", [0.12, top + 0.15, 0.06], [0.24, 0.28, 0.22], JL25_SLATE, [0, 0, PI / 2])]
    parts += _flag([-0.16, top, -0.14], 0.70, 0.0, pole=1.00, decal="jl25_garrison")
    for n in (0, 1, 4):
        a = PI + n * TAU / 5
        parts += _jl25_cannon([math.sin(a) * 0.47, top, math.cos(a) * 0.47], a, 0.85)
    return parts


@JL25.hat("rampart_crown", "Rampart Crown",
          "A mural crown: a ring of brick wall round your head with battlements on top, "
          "four turrets with slate roofs, a gate at the front and pennants flying. In "
          "the old pictures, cities wear these. Now you are a city.", "rare")
def _():
    parts = [
        place("flare", [0, -0.32, 0], [2.06, 0.46, 2.00], JL25_BRICK, anchor=[0, 0, 0], decal="bricks",
              wrap=True),
        part("cyl", [0, 0.12, 0], [1.96, 0.04, 1.90], JL25_STONE),
        ringband(-0.30, 0.06, JL25_STONE, margin=0.05),
        # the gate
        part("rbox", [0, -0.14, 0.93], [0.22, 0.28, 0.04], "#2a1e16"),
        part("cyl", [0, 0.0, 0.93], [0.22, 0.04, 0.22], "#2a1e16", [PI / 2, 0, 0]),
    ]
    parts += around(16, 0.0, 0.0, lambda a, x, z: None if abs(math.sin(a * 2)) > 0.92 else part(
        "rbox", [math.sin(a) * 0.98, 0.20, math.cos(a) * 0.95], [0.16, 0.14, 0.10], JL25_BRICK, [0, a, 0],
        decal="bricks"), start=TAU / 32)
    for n in range(4):
        a = PI / 4 + n * PI / 2
        x, z = math.sin(a) * 0.99, math.cos(a) * 0.96
        parts += [part("cyl", [x, 0.05, z], [0.30, 0.50, 0.30], JL25_BRICK, decal="bricks", wrap=True),
                  place("cone", [x, 0.38, z], [0.36, 0.26, 0.36], JL25_SLATE),
                  rod([x, 0.50, z], [x, 0.74, z], 0.02, "#d9d2c0"),
                  place("flag", [x, 0.72, z], [0.26, 0.26, 0.3], [RED, WHITE, NAVY, RED][n], anchor=[-0.5, 0.30, 0],
                        r=[0, -a, 0])]
    return parts


@JL25.hat("blast_goggles", "Blast Goggles",
          "Big brass-rimmed goggles with smoked lenses, pushed up on your forehead now "
          "the show is over, and a perfect clean ring round each eye where they were. "
          "Everything else about you is soot.", "uncommon", hair="show")
def _():
    brass = BRASS
    parts = [band(-0.13, 0.11, "#3a3a3a", grow=0.02, decal="canvas")]
    for s in (1, -1):
        c = [0.24 * s, -0.04, 0.84]
        parts += [
            part("cyl", c, [0.34, 0.14, 0.34], "#2e2a26", [PI / 2 - 0.55, 0, 0]),
            part("torus", [c[0], c[1] + 0.035, c[2] + 0.06], [0.34, 0.30, 0.34], brass, [PI / 2 - 0.55, 0, 0],
                 m="metal"),
            part("cyl", [c[0], c[1] + 0.04, c[2] + 0.065], [0.26, 0.02, 0.26], "#3a3a2a", [PI / 2 - 0.55, 0, 0],
                 m="glass", a=0.8),
        ]
    parts.append(rod([-0.08, -0.04, 0.88], [0.08, -0.04, 0.88], 0.05, brass, m="metal"))
    return parts


@JL25.hat("sparkler_crown", "Sparkler Crown",
          "A brass band with eleven sparklers stuck in it, every one of them lit. It is "
          "the best crown in the world for exactly ninety seconds. Bring a bucket.",
          "rare", hair="show")
def _():
    parts = [band(-0.10, 0.10, BRASS, grow=0.02, m="metal")]
    for n in range(11):
        a = (n - 5) * 0.27
        s, c = math.sin(a), math.cos(a)
        base = [s * 0.82, -0.06, c * 0.80]
        tip = [s * 1.00, 0.78 + 0.06 * math.cos(n * 1.7), c * 0.96]
        burnt = [base[0] + (tip[0] - base[0]) * 0.80, base[1] + (tip[1] - base[1]) * 0.80,
                 base[2] + (tip[2] - base[2]) * 0.80]
        parts += [rod(base, burnt, 0.03, "#8a8c90", m="metal"),
                  rod(burnt, tip, 0.04, "#3a3836"),
                  part("sph", tip, [0.08, 0.08, 0.08], JL25_SPARK, m="neon"),
                  place("sparkle", tip, 0.30, "#ffd27a", m="neon", spin=6.0)]
    return parts


# ================================================================= backs
@JL25.back("garrison_flag", "The Garrison Flag",
           "The great flag from the fort, on a pole in a harness on your back: fifteen "
           "stars, fifteen stripes, scorched at the fly and holed in three places by the "
           "night's work, and still flying. Doorways are a problem.", "legendary")
def _():
    parts = straps("#5a3a1a") + [
        part("rbox", [0.30, 0.50, -0.20], [0.30, 0.56, 0.26], "#6a4a2a", decal="leather", wrap=True),
        part("rbox", [0.30, 0.78, -0.20], [0.34, 0.06, 0.30], BRASS, m="metal"),
        part("cyl", [0.30, 2.20, -0.36], [0.09, 3.60, 0.09], "#d9d2c0", m="metal"),
        part("sph", [0.30, 4.06, -0.36], [0.20, 0.20, 0.20], GOLD, m="metal"),
        place("flag", [0.30, 3.92, -0.36], [3.10, 3.10, 1.4], WHITE, anchor=[-0.5, 0.30, 0],
              decal="jl25_garrison", wrap=True),
        rod([0.36, 0.80, -0.30], [0.36, 3.90, -0.30], 0.02, "#e8dcc0"),
    ]
    return parts


@JL25.back("rocket_rack", "Rocket Rack",
           "A launch frame on your back with five skyrockets loaded in their tubes, sticks "
           "hanging down, fuses run together to one that is already fizzing. The crew "
           "calls it the Backpack Finale. The crew is not allowed near it any more.",
           "rare")
def _():
    parts = straps("#3a3a3a") + [
        part("rbox", [0, 0.48, -0.30], [0.90, 0.84, 0.36], "#5a5a4a", decal="canvas", wrap=True),
        part("rbox", [0, 0.94, -0.38], [1.10, 0.08, 0.50], JL25_IRON, m="metal"),
    ]
    tips = []
    for n, x in enumerate((-0.44, -0.22, 0.0, 0.22, 0.44)):
        tilt = x * 0.75
        base = [x, 0.98, -0.42]
        d = [math.sin(tilt), math.cos(tilt) * 0.97, -0.25]
        c = [RED, WHITE, "#3a5ad8", WHITE, RED][n]
        parts += [rod(base, [base[0] + d[0] * 0.62, base[1] + d[1] * 0.62, base[2] + d[2] * 0.62], 0.24,
                      "#3a3e46", m="metal"),
                  rod([base[0], base[1] - 0.80, base[2] + 0.04], base, 0.035, JL25_WOOD),
                  place("rocket", [base[0] + d[0] * 0.95, base[1] + d[1] * 0.95, base[2] + d[2] * 0.95],
                        [0.70, 0.95, 0.70], c, r=[-0.25, 0, -tilt], decal="firecracker", wrap=True)]
        tips.append(base)
    for p, q in zip(tips, tips[1:]):
        parts.append(rod([p[0], 0.92, -0.66], [q[0], 0.92, -0.66], 0.025, JL25_FUSE))
    parts += [rod([0.44, 0.92, -0.66], [0.56, 0.80, -0.70], 0.025, JL25_FUSE),
              place("sparkle", [0.57, 0.78, -0.71], 0.22, JL25_SPARK, m="neon", spin=6.0)]
    return parts


# ================================================================== hair
@JL25.hairdo("lit_fuse_mohawk", "Lit Fuse Mohawk",
             "Shaved short at the sides and up the middle a crest of twisted black-powder "
             "fuse, burning at the front. You have about four minutes. Nobody knows what "
             "happens after that.", "rare")
def _():
    c = "#2a2420"
    parts = [place("hairshort", [0, 0, 0], [1.03, 0.98, 1.03], c, anchor=[0, 0, 0], decal="strands",
                   wrap=True)]
    # the crest: one long twist of fuse laid front to back, standing up in
    # the middle and coiling over at the front where it is lit
    pts = [[0, 0.80, 0.48], [0, 0.86, 0.30], [0, 0.88, 0.10], [0, 0.86, -0.10], [0, 0.80, -0.28],
           [0, 0.70, -0.42], [0, 0.56, -0.52]]
    for n, (p, q) in enumerate(zip(pts, pts[1:])):
        w = 0.20 - 0.015 * n
        parts.append(rod(p, q, w, JL25_FUSE, t="capsule", decal="jl25_fuse", wrap=True))
        parts.append(rod([p[0], p[1] - 0.16, p[2]], [q[0], q[1] - 0.16, q[2]], w * 0.8, shade(JL25_FUSE, 0.8)))
    parts += [part("sph", [0, 0.84, 0.52], [0.13, 0.12, 0.13], JL25_EMBER, m="neon"),
              place("sparkle", [0, 0.88, 0.56], 0.30, JL25_SPARK, m="neon", spin=6.0),
              part("sph", [0.03, 0.78, 0.46], [0.12, 0.08, 0.10], "#4a4440")]
    return parts


@JL25.hairdo("singed_frizz", "Singed Frizz",
             "What is left after you leant over the mortar to see why it had not gone off: "
             "a great sooty frizz standing straight up, still smoking gently, with an ember "
             "somewhere in it you have not found yet.", "uncommon")
def _():
    c, d = "#3a3430", "#24201e"
    parts = [place("hairmid", [0, 0, 0], [1.05, 1.05, 1.05], c, anchor=[0, 0, 0], decal="felt", wrap=True)]
    for n, (x, y, z, w) in enumerate(((0.0, 0.74, 0.0, 0.70), (0.32, 0.62, 0.20, 0.44),
                                      (-0.32, 0.64, 0.18, 0.44), (0.30, 0.66, -0.26, 0.46),
                                      (-0.28, 0.68, -0.26, 0.46), (0.0, 0.66, 0.34, 0.42),
                                      (0.0, 0.70, -0.38, 0.44), (0.18, 0.90, 0.0, 0.40),
                                      (-0.18, 0.88, -0.04, 0.40))):
        parts.append(part("sph", [x, y, z], [w, w * 0.9, w], c if n % 2 else d, decal="felt", wrap=True))
    for n, (x, y, s) in enumerate(((0.10, 1.18, 0.30), (-0.06, 1.42, 0.24), (0.12, 1.62, 0.18))):
        parts.append(part("sph", [x, y, 0.0], [s, s * 0.85, s], "#c8c8cc", a=0.5 - 0.1 * n))
    parts.append(part("sph", [0.30, 0.76, 0.30], [0.05, 0.05, 0.05], JL25_EMBER, m="neon"))
    return parts


# ================================================================= faces
JL25.face("ka_boom", "Ka-BOOM!",
          "Eyes screwed shut, mouth wide open in a scream nobody can hear over the "
          "barrage, soot on both cheeks and a bead of sweat. The shell went off. You were "
          "standing quite near it.", [
              {"k": "line", "x1": -0.28, "y1": -0.18, "x2": -0.13, "y2": -0.11, "w": 0.035, "c": "#16171b"},
              {"k": "line", "x1": -0.13, "y1": -0.11, "x2": -0.28, "y2": -0.04, "w": 0.035, "c": "#16171b"},
              {"k": "line", "x1": 0.28, "y1": -0.18, "x2": 0.13, "y2": -0.11, "w": 0.035, "c": "#16171b"},
              {"k": "line", "x1": 0.13, "y1": -0.11, "x2": 0.28, "y2": -0.04, "w": 0.035, "c": "#16171b"},
              {"k": "ellipse", "x": 0.0, "y": 0.17, "w": 0.24, "h": 0.22, "c": "#3a1414"},
              {"k": "ellipse", "x": 0.0, "y": 0.235, "w": 0.13, "h": 0.07, "c": "#e05a6a"},
              {"k": "ellipse", "x": -0.32, "y": 0.06, "w": 0.13, "h": 0.07, "c": "#5a5450"},
              {"k": "ellipse", "x": 0.30, "y": 0.09, "w": 0.10, "h": 0.06, "c": "#5a5450"},
              {"k": "ellipse", "x": 0.24, "y": -0.30, "w": 0.06, "h": 0.03, "c": "#5a5450"},
              {"k": "poly", "pts": [[0.37, -0.30], [0.40, -0.21], [0.37, -0.17], [0.34, -0.21]], "c": "#7ac8ff"},
          ])
JL25.face("dawns_early_light", "Dawn's Early Light",
          "Up all night: eyes half shut and heavy-lidded, bags under them, soot on the "
          "forehead and a single tear, because at dawn the smoke cleared and the flag was "
          "still there.", [
              {"k": "ellipse", "x": -0.19, "y": -0.09, "w": 0.13, "h": 0.07, "c": "#16171b"},
              {"k": "ellipse", "x": 0.19, "y": -0.09, "w": 0.13, "h": 0.07, "c": "#16171b"},
              {"k": "line", "x1": -0.28, "y1": -0.125, "x2": -0.10, "y2": -0.12, "w": 0.04, "c": "#16171b"},
              {"k": "line", "x1": 0.10, "y1": -0.12, "x2": 0.28, "y2": -0.125, "w": 0.04, "c": "#16171b"},
              {"k": "arc", "x": -0.19, "y": -0.07, "r": 0.09, "a0": 0.12, "a1": 0.38, "w": 0.018, "c": "#8a6a9a"},
              {"k": "arc", "x": 0.19, "y": -0.07, "r": 0.09, "a0": 0.12, "a1": 0.38, "w": 0.018, "c": "#8a6a9a"},
              {"k": "arc", "x": 0.0, "y": 0.10, "r": 0.09, "a0": 0.10, "a1": 0.40, "w": 0.03, "c": "#16171b"},
              {"k": "poly", "pts": [[0.25, -0.01], [0.27, 0.07], [0.25, 0.10], [0.23, 0.07]], "c": "#7ac8ff"},
              {"k": "ellipse", "x": -0.10, "y": -0.36, "w": 0.18, "h": 0.06, "c": "#5a5450"},
              {"k": "ellipse", "x": 0.04, "y": -0.39, "w": 0.08, "h": 0.04, "c": "#5a5450"},
          ], "rare")

# =============================================================== clothes
JL25.shirt("garrison_coatee", "Garrison Coatee",
           "The fort's dress coat: navy wool, red collar and facings, white cross-belts "
           "with a polished brass plate where they meet, and two rows of buttons nobody "
           "has managed to keep done up through a whole barrage.",
           {"torso": NAVY, "arms": NAVY, "decal": "jl25_coatee"}, "rare")
JL25.pants("pyro_cargo", "Pyro Cargo Trousers",
           "Flame-resistant olive cargo trousers with a hi-vis stripe down each leg, pockets "
           "full of spare fuse, and steel-capped boots for when the rack falls over.",
           {"legs": "#4a4a36", "stripe": JL25_HIVIS, "cuff": "#2a2420", "weave": "canvas"})
JL25.belt("fuse_bandolier", "Fuse Bandolier Belt",
          "A canvas belt with a row of little firework shells in loops all the way round, "
          "a brass buckle and two pouches of spare fuse. Do not sit near the barbecue.",
          {"band": "#6a5a3a", "buckle": BRASS, "width": 0.22, "metal": True, "weave": "jl25_shells",
           "pouch": True})


# ================================================================ weapons
def _jl25_ball(k=1.0):
    """A round shot, still hot from the gun."""
    return [part("sph", [0, 0, 0], [0.60 * k, 0.60 * k, 0.60 * k], JL25_IRON, m="metal"),
            part("sph", [0, 0, -0.10 * k], [0.50 * k, 0.50 * k, 0.40 * k], JL25_EMBER, m="neon", a=0.35)]


@JL25.weapon("round_shot", "Round Shot",
             "A swivel gun off the fort's walls, bronze, on its yoke, with a tiller to aim "
             "it by. It throws a solid iron ball that bowls straight through everybody in "
             "a line and skips off the walls and floor like a stone on a pond.",
             {"kind": "projectile", "projectile": "roundshot", "damage": 45, "splash": 0,
              "splash_damage": 0, "rpm": 40, "mag": 1, "reload": 2.6, "speed": 72, "range": 240,
              "auto": False, "sound": "shotgun", "recoil": 3.2, "reserve": 14, "gravity_scale": 0.55,
              "self_damage": 0.0, "knockback": 20, "bounce": 2, "pierce_players": 3,
              "trail_colors": ["#3a3a3a", "#ff8a2a"]},
             [["+", "Bowls straight through up to three people: 45 each"],
              ["+", "Skips off walls and floors twice before it stops"],
              ["+", "Knocks whoever it hits flat: a 20 stud shove"],
              ["-", "One ball, then a 2.6 second reload"],
              ["-", "No splash at all: a miss is a miss"]], rarity="legendary",
             proj=lambda: _jl25_ball(1.0))
def _():
    bronze = "#b8863a"
    return [
        # the tiller the hand holds, and the yoke it swivels on
        rod([0, -0.02, -0.34], [0, 0.10, 0.02], 0.07, JL25_WOOD),
        part("sph", [0, -0.03, -0.36], [0.09, 0.09, 0.09], JL25_WOOD),
        rod([0, -0.04, 0.24], [0, 0.14, 0.24], 0.06, JL25_IRON, m="metal"),
        rod([0.13, 0.14, 0.24], [0.0, -0.04, 0.24], 0.04, JL25_IRON, m="metal"),
        rod([-0.13, 0.14, 0.24], [0.0, -0.04, 0.24], 0.04, JL25_IRON, m="metal"),
        # the barrel, its rings, the muzzle swell and the cascabel
        part("cyl", [0, 0.16, 0.50], [0.22, 0.96, 0.22], bronze, [PI / 2, 0, 0], m="metal"),
        part("torus", [0, 0.16, 0.24], [0.26, 0.24, 0.26], bronze, [PI / 2, 0, 0], m="metal"),
        part("torus", [0, 0.16, 0.66], [0.25, 0.22, 0.25], bronze, [PI / 2, 0, 0], m="metal"),
        part("cyl", [0, 0.16, 0.96], [0.28, 0.08, 0.28], bronze, [PI / 2, 0, 0], m="metal"),
        part("cyl", [0, 0.16, 0.995], [0.14, 0.02, 0.14], "#1a1a1a", [PI / 2, 0, 0]),
        part("sph", [0, 0.16, 0.0], [0.14, 0.14, 0.14], bronze, m="metal"),
        part("cyl", [0, 0.27, 0.06], [0.03, 0.04, 0.03], "#1a1a1a"),
    ]


@JL25.weapon("star_shell", "Star Shell",
             "An illumination shell, fired high, that pops a parachute and hangs there "
             "burning red. Under its light nobody on the other side can hide, and "
             "everybody on yours can see exactly where to aim.",
             {"kind": "deploy", "cooldown": 24, "sound": "rocket",
              "deploy": {"type": "zone", "thrown": True, "throw": 40, "float": 9.0, "radius": 16.0,
                         "secs": 9.0, "limit": 1, "scale": 1.6, "color": "#ff5a3a", "particle": "spark",
                         "name": "Star Shell", "enemy": {"reveal": 1.5}, "ally": {"crit": [0.15, 1.0]}}},
             [["+", "Fires a flare 40 studs out that hangs 9 studs up on its parachute for 9 "
                    "seconds"],
              ["+", "Every enemy under its light is shown to your whole side through walls"],
              ["+", "Your side under it shoots straighter: a 15% chance of a critical hit"],
              ["-", "Does no damage at all"],
              ["-", "24 second cooldown"]], rarity="legendary",
             deploy=lambda: [
                 place("hemi", [0, 1.30, 0], [1.60, 0.70, 1.60], WHITE, anchor=[0, 0, 0], decal="jl25_chute",
                       wrap=True),
                 *[rod([math.sin(a) * 0.78, 1.30, math.cos(a) * 0.78], [0, 0.18, 0], 0.02, "#d9d2c0")
                   for a in (0.4, 2.0, 3.6, 5.2)],
                 part("cyl", [0, 0.10, 0], [0.16, 0.20, 0.16], "#3a3226"),
                 part("sph", [0, -0.04, 0], [0.30, 0.30, 0.30], "#ff4a2a", m="neon"),
                 part("sph", [0, -0.04, 0], [0.60, 0.60, 0.60], "#ff8a5a", m="neon", a=0.3)])
def _():
    return [
        part("cyl", [0, 0.10, 0.20], [0.34, 0.56, 0.34], RED, decal="jl25_shell", wrap=True),
        part("cyl", [0, 0.39, 0.20], [0.36, 0.04, 0.36], WHITE),
        part("cyl", [0, -0.19, 0.20], [0.36, 0.04, 0.36], WHITE),
        place("hemi", [0, 0.41, 0.20], [0.30, 0.10, 0.30], "#e8e0d0", anchor=[0, 0, 0]),
        rod([0, 0.46, 0.20], [0.06, 0.62, 0.24], 0.025, JL25_FUSE),
        part("sph", [0.065, 0.63, 0.245], [0.04, 0.04, 0.04], JL25_EMBER, m="neon"),
    ]


@JL25.weapon("linstock", "The Linstock",
             "The gunner's staff: a spear point, and a brass serpent's head holding a "
             "smouldering slow match. Every touch leaves them smoking, and every fourth "
             "swing touches off whatever powder is lying about -- which, tonight, is all of it.",
             {"kind": "melee", "damage": 30, "headshot": 1.0, "rpm": 80, "range": 11.0, "arc": 0.55,
              "sound": "swing", "knockback": 6, "on_hit": {"burn": [4, 2.0]},
              "aoe_every": {"every": 4, "radius": 8.0, "damage": 34, "knock": 22, "label": "Touched Off",
                            "fx": "pulse", "on_hit": {"burn": [6, 3.0]}}},
             [["+", "The slow match leaves whoever it hits smouldering: 4 a second for 2 seconds"],
              ["+", "Every fourth hit touches off the powder: 34 to everyone within 8 studs, a "
                    "shove, and they burn 6 a second for 3 seconds"],
              ["-", "Slow: 80 swings a minute"],
              ["-", "30 damage a hit"]], rarity="legendary")
def _():
    return [
        part("cyl", [0, 0, 0.42], [0.09, 1.70, 0.09], JL25_WOOD, [PI / 2, 0, 0], decal="planks", wrap=True),
        part("cyl", [0, 0, -0.42], [0.11, 0.06, 0.11], BRASS, [PI / 2, 0, 0], m="metal"),
        # the serpent's head fork, the match in its jaws, the spear point
        part("sph", [0, 0.02, 1.30], [0.14, 0.12, 0.20], BRASS, m="metal"),
        rod([0, 0.0, 1.28], [0.14, 0.04, 1.44], 0.04, BRASS, m="metal"),
        rod([0, 0.0, 1.28], [-0.14, 0.04, 1.44], 0.04, BRASS, m="metal"),
        part("torus", [0.14, 0.05, 1.46], [0.12, 0.12, 0.12], JL25_FUSE),
        part("sph", [0.15, 0.11, 1.48], [0.06, 0.06, 0.06], JL25_EMBER, m="neon"),
        place("sparkle", [0.15, 0.13, 1.50], 0.18, JL25_SPARK, m="neon", spin=6.0),
        part("sph", [-0.14, 0.12, 1.46], [0.10, 0.08, 0.10], "#c8c8cc", a=0.5),
        place("cone", [0, 0, 1.58], [0.12, 0.30, 0.06], SILVER, r=[PI / 2, 0, 0], m="metal"),
    ]


@JL25.gear("garrison_bugle", "Garrison Bugle",
           "A brass bugle with a red, white and blue cord. Sound To Arms and everybody on "
           "your side who hears it squares up behind the ramparts and steps out smartly.",
           {"kind": "ability", "cooldown": 30, "sound": "horn",
            "ability": {"shield": {"secs": 6.0, "amount": 30, "radius": 18},
                        "rally": {"radius": 18, "secs": 6.0, "speed": 0.20}}},
           [["+", "You and everyone on your side within 18 studs get a 30 point shield for 6 "
                  "seconds"],
            ["+", "...and march 20% faster while it lasts"],
            ["-", "No damage"],
            ["-", "30 second cooldown"]], rarity="rare")
def _():
    return [
        part("torus", [0, 0.16, 0.20], [0.42, 0.36, 0.42], BRASS, [0, 0, PI / 2], m="metal"),
        place("trumpet", [0, 0.30, 0.20], [0.40, 0.44, 0.40], BRASS, anchor=[0, 0, 0], r=[PI / 2, 0, 0],
              m="metal"),
        rod([0, 0.0, 0.20], [0, -0.02, -0.06], 0.05, BRASS, m="metal"),
        part("cyl", [0, -0.02, -0.08], [0.08, 0.04, 0.08], SILVER, [PI / 2, 0, 0], m="metal"),
        rod([0.04, 0.0, 0.06], [0.04, -0.20, 0.24], 0.03, RED),
        rod([0.04, -0.20, 0.24], [0.04, -0.06, 0.50], 0.03, WHITE),
        place("teardrop", [0.04, -0.20, 0.24], [0.08, 0.16, 0.08], NAVY, anchor=[0, 1.0, 0]),
    ]


# =============================================================== effects
JL25.effect("rockets_red_glare", name="Rocket's Red Glare", rate=3.0, life=[1.0, 1.4],
            size=[0.30, 0.44], grow=-0.1, gravity=4.0, spread=0.25, rise=[1.5, 2.5],
            blend="add", spin=0.0, colors=["#ff3a2a", "#ff8a2a", "#fff3b0"],
            shapes=["jl25_rocket", "jl25_rocket", "spark"], radius=0.6, upright=True, wobble=0.1)
JL25.effect("bombs_bursting", name="Bombs Bursting in Air", rate=2.2, life=[1.2, 1.8],
            size=[0.30, 0.46], grow=0.25, gravity=0.0, spread=0.6, rise=[0.3, 0.7],
            blend="normal", spin=1.2, colors=["#2a2a2e", "#ff3a2a", "#ffffff", "#4a7ae8"],
            shapes=["jl25_bomb", "jl25_bomb", "firework"], radius=0.8, wobble=0.4)
JL25.opening(
    sky={"top": "#070a1e", "horizon": "#3a1a2a", "sun": [0.2, 0.9, 0.6], "clouds": 0,
         "tint": "#ffd0b0"},
    ambient="#5a4a6a", beam="#ff5a3a", seep="bombs_bursting", after="rockets_red_glare",
    burst=["#ff3a2a", "#ffffff", "#3a5ad8", "#ffc94a"],
    pieces=[{"shape": "jl25_rocket", "colors": ["#ff3a2a", "#ffc94a"], "blend": "add"},
            {"shape": "star", "colors": ["#ffffff", "#4a7ae8"], "blend": "normal"},
            {"shape": "jl25_bomb", "colors": ["#2a2a2e", "#ff5a2a"], "blend": "normal"},
            {"shape": "jl_pennant", "colors": [RED, CREAM, BLUE], "blend": "normal"}],
    backdrop="jl25_ramparts", title_wait="The fuses are lit...", title_shake="Ka-BOOM!")
JL25.award("Rocket's Red Glare", ["Powder Monkey", "Fuse Lighter", "Gunner", "Rampart Watch",
                                  "Master Pyrotechnician", "The Banner Yet Waves"],
           "Opened Star Forts during Rocket's Red Glare, the Fourth of July 2025.", "em_firework",
           "spangle")
JL25.bundle("pair", "Fort and Key", 1, 1050, "One Star Fort, one Rampart Key.")
JL25.bundle("barrage", "The Barrage", 3, 3000, "Three forts, three keys. Saves 300.")


# @@ JL25 Rocket's Red Glare goes above this line @@

# @@ JL26 America 250 goes above this line @@


EVENTS = [JL22, JL23, JL24]

# (JL25 adds itself to the list here)
EVENTS += [JL25]  # @@ JL25 @@

# (JL26 adds itself to the list here)
EVENTS += []  # @@ JL26 @@
