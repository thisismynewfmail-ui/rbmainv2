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


EVENTS = [JL22]
