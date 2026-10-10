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

from .kit import (BLACK, BRASS, GOLD, GOLD_DARK, IRON, PI, SILVER, SNOW, TAU, WHITE,
                  Event, around, at_frame, band, buckle, cap, dome, mix, part, place,
                  pompom, ringband, rotate, shade, sides, straps)

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


def _rod(a, b, w, c, t="cyl", **kw):
    """A rod from point ``a`` to point ``b``, ``w`` thick: a straw, a strut,
    a tube."""
    d = [b[0] - a[0], b[1] - a[1], b[2] - a[2]]
    length = math.sqrt(sum(v * v for v in d)) or 1e-6
    rx = math.acos(max(-1.0, min(1.0, d[1] / length)))
    ry = math.atan2(d[0], d[2])
    mid = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2]
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
    parts = [
        band(-0.10, 0.32, WHITE, grow=0.04, decal="linen", wrap=True),
        part("cyl", [0, 0.38, 0], [1.50, 0.66, 1.44], WHITE, decal="jl_pleats", wrap=True),
        part("sph", [0, 0.86, 0], [1.94, 0.78, 1.86], "#fbfbf8", decal="linen", wrap=True),
        part("box", [0, -0.10, 0.795], [0.96, 0.24, 0.02], "#000000", decal="jl_grillband", a=-1),
    ]
    for n in range(6):
        a = n * TAU / 6 + 0.3
        parts.append(part("sph", [math.sin(a) * 0.62, 0.96, math.cos(a) * 0.60],
                          [0.66, 0.50, 0.66], "#fbfbf8", decal="linen", wrap=True))
    # tongs one side, a spatula the other
    parts += [part("rbox", [0.74, 0.20, 0.30], [0.05, 0.86, 0.06], SILVER, [0.10, 0, -0.22],
                   m="metal"),
              part("rbox", [0.78, 0.20, 0.36], [0.05, 0.86, 0.06], SILVER, [0.30, 0, -0.22],
                   m="metal"),
              part("rbox", [0.84, 0.66, 0.40], [0.10, 0.10, 0.20], KETCHUP, [0.2, 0, -0.22]),
              part("rbox", [-0.74, 0.14, 0.20], [0.06, 0.66, 0.06], "#3a2414", [0, 0, 0.18]),
              part("rbox", [-0.86, 0.62, 0.20], [0.04, 0.34, 0.30], SILVER, [0, 0, 0.18],
                   m="metal"),
              part("sph", [0.30, 1.42, -0.10], [0.36, 0.26, 0.32], "#c9ccd2", a=0.5),
              part("sph", [0.42, 1.66, -0.18], [0.24, 0.20, 0.22], "#d9dce2", a=0.38)]
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
            part("cyl", [x, 0.02, 0.0], [0.42, 0.36, 0.42], KETCHUP),
            part("cyl", [x, 0.16, 0.0], [0.34, 0.52, 0.34], "#ffe680", m="glass", a=0.8),
            part("cyl", [x, 0.42, 0.0], [0.30, 0.02, 0.30], "#fff6c0"),
            part("cyl", [x + 0.10 * side, 0.44, 0.10], [0.20, 0.03, 0.20], "#f5e04a",
                 [PI / 2, 0, 0.4 * side], decal="jl_lemon"),
        ]
        path = [(x, 0.30, 0.04), (x, 0.64, 0.04), (1.16 * side, 0.42, 0.14),
                (1.06 * side, -0.60, 0.36), (0.78 * side, -0.86, 0.80), (0.10 * side, -0.86, 0.80)]
        for a, b in zip(path, path[1:]):
            parts.append(_rod(a, b, 0.05, straw))
            parts.append(part("sph", list(b), [0.05, 0.05, 0.05], straw))
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
        part("rbox", [0, 0.30, -0.30], [1.30, 1.26, 0.04], "#2f8a4a", decal="jl_webbing"),
        part("rbox", [0, 0.20, -0.40], [1.30, 1.10, 0.04], "#2f8a4a", decal="jl_webbing"),
        part("box", [0, 0.20, -0.425], [1.24, 1.04, 0.01], "#000000", [0, PI, 0],
             decal="jl_webbing", a=-1),
        *straps("#2b2b30", 0.34, 0.12),
    ]
    for x in (-0.66, 0.66):
        parts += [part("cyl", [x, 0.28, -0.34], [0.07, 1.42, 0.07], alu, m="metal"),
                  part("rbox", [x * 1.06, 0.62, -0.40], [0.10, 0.06, 0.40], "#e8e2d0"),
                  part("cyl", [x, -0.44, -0.46], [0.07, 0.30, 0.07], alu, [0.5, 0, 0], m="metal")]
    for y in (0.95, -0.37):
        parts.append(part("cyl", [0, y, -0.34], [0.07, 1.36, 0.07], alu, [0, 0, PI / 2], m="metal"))
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
    parts += [part("sph", [0, 0.64, 0.16], [0.82, 0.36, 0.62], c, decal="strands", wrap=True),
              part("sph", [0, 0.68, 0.38], [0.70, 0.34, 0.44], hi, [0.3, 0, 0], decal="strands",
                   wrap=True),
              place("spiral", [0.06, 0.46, 0.58], [0.10, 0.20, 0.10], c, r=[0.4, 0, 0.2])]
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
              {"k": "ellipse", "x": 0, "y": 0.02, "w": 0.86, "h": 0.66, "c": "rgba(255,96,72,0.45)"},
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
        part("rbox", [0, 0.10, 1.34], [0.66, 0.05, 0.70], steel, [-0.18, 0, 0], m="metal",
             decal="jl_slots"),
        part("rbox", [0, 0.13, 1.26], [0.40, 0.06, 0.08], "#5a2e1a", [-0.18, 0, 0]),
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


EVENTS = [JL22, JL23]
