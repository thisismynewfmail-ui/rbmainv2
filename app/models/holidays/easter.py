"""Easter: eggs, bunnies, and chocolate in quantities nobody should eat.

Nine days either side of Easter Sunday, every spring since the first:

  2022  Eggstravaganza    the first hunt: ten thousand painted eggs, three still lost
  2023  Bunny Burrow      the warren under the hill, its round door and its carrots
  2024  The Great Hatch   the incubator in the barn, and everything that hatched
  2025  Choc-o-Lock       the chocolatier's vault, foil, fondue and a hollow bunny
  2026  Faberge Gala      the jewelled egg at the imperial ball, and its surprise

Every egg in here is the one egg mesh (``egg``) or the two halves of a broken
one (``crackedshell`` and ``ea_eggtop``, which share an anchor and a scale and
close into a whole egg along the same zig-zag); ``_egg`` paints one up with
bands and spots, and ``_egg_r`` says how wide the egg is at any height, so a
band or a spot can sit on its surface instead of in it or off it.
"""
from __future__ import annotations

import math

from .kit import (BLACK, BONE, BRASS, GOLD, GOLD_DARK, IRON, PI, SILVER, SNOW, TAU, WHITE,
                  Event, around, at_frame, band, buckle, cap, dome, gift_bow, mix, part,
                  place, pompom, reach, ringband, rod, rotate, shade, sides, straps)

# the egg mesh: native 0.92 wide and 1.30 tall, its bottom at its origin
EGG_W, EGG_H = 0.92, 1.30


def _egg_r(f, k=1.0):
    """The egg's radius a fraction ``f`` of the way up it (0 the bottom, 1
    the top), for an egg mesh scaled by ``k`` across."""
    f = min(1.0, max(0.0, f))
    return k * math.sqrt(f * (1.0 - f)) * (1.0 - 0.16 * f)


def _egg_band(f0, f1, k, ky, y0, c, grow=0.012, mesh="ring", **kw):
    """A painted band round an upright egg (scaled ``k`` across and ``ky``
    up, its bottom at ``y0``) from ``f0`` to ``f1`` of its height: a washer
    just proud of the widest point it has to cover.  ``mesh`` "spikecrown"
    makes it a zig-zag."""
    rad = max(_egg_r(f0 + (f1 - f0) * i / 8.0, k) for i in range(9)) + grow
    h = EGG_H * ky * (f1 - f0)
    native_h = 0.2 if mesh == "ring" else 1.0
    return place(mesh, [0, y0 + EGG_H * ky * f0, 0], [rad * 2, h / native_h, rad * 2], c,
                 anchor=[0, 0, 0], **kw)


def _egg_spot(f, ang, k, ky, y0, d, c, depth=0.05, **kw):
    """A painted spot on an upright egg's surface, ``f`` of the way up and
    ``ang`` round from the front, turned to face out of the shell."""
    r = _egg_r(f, k)
    e = 0.01
    dr = _egg_r(f + e, k) - _egg_r(f - e, k)
    dy = EGG_H * ky * 2 * e
    tilt = math.atan2(dr, dy)          # the surface leans in as it climbs
    p = [math.sin(ang) * (r + depth * 0.25), y0 + EGG_H * ky * f, math.cos(ang) * (r + depth * 0.25)]
    return part("sph", p, [d, d, depth], c, [tilt, ang, 0], **kw)


def _egg(w, c, bands=(), zig=None, dots=None, m=None):
    """A painted egg ``w`` wide, upright with its bottom at the origin:
    ``bands`` are (f0, f1, colour), ``zig`` one (f0, f1, colour) zig-zag,
    ``dots`` (f, count, colour, size) a ring of spots.  Move it into place
    with ``at_frame`` (which turns it as a whole)."""
    k = w / EGG_W
    parts = [place("egg", [0, 0, 0], [k, k, k], c, anchor=[0, 0, 0], m=m)]
    for f0, f1, bc in bands:
        parts.append(_egg_band(f0, f1, k, k, 0.0, bc, grow=0.006 * w))
    if zig:
        parts.append(_egg_band(zig[0], zig[1], k, k, 0.0, zig[2], grow=0.008 * w,
                               mesh="spikecrown"))
    if dots:
        f, count, dc, size = dots
        r = _egg_r(f, k)
        for n in range(count):
            a = n * TAU / count
            parts.append(part("sph", [math.sin(a) * r, EGG_H * k * f, math.cos(a) * r],
                              [size * w, size * w, size * w], dc))
    return parts


def _lid(parts):
    """Mark every part as part of a crate's lid."""
    for p in parts:
        p["lid"] = 1
    return parts


def _euler(*steps):
    """The renderer's euler angles (R = Ry * Rx * Rz) for a sequence of
    turns about the world axes, applied in order: ``_euler(("y", a), ("x",
    PI / 2))`` spins a part about its own up axis and then lays it forward."""
    m = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    for axis, a in steps:
        c, s = math.cos(a), math.sin(a)
        r = {"x": [[1, 0, 0], [0, c, -s], [0, s, c]],
             "y": [[c, 0, s], [0, 1, 0], [-s, 0, c]],
             "z": [[c, -s, 0], [s, c, 0], [0, 0, 1]]}[axis]
        m = [[sum(r[i][k] * m[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
    rx = math.asin(max(-1.0, min(1.0, -m[1][2])))
    ry = math.atan2(m[0][2], m[2][2])
    rz = math.atan2(m[1][0], m[1][1])
    return [rx, ry, rz]


def _flower(at, k, petals, centre="#ffd84a", r=None, leaf=None):
    """A five-petalled blossom facing +Z (turned by ``r``), a bead of a
    centre, and a leaf behind it if asked."""
    x, y, z = at
    rr = list(r or [0, 0, 0])
    fwd = rotate([0, 0, 1], rr)
    out = [place("flower", [x, y, z], [k, k, k], petals, r=rr),
           part("sph", [x + fwd[0] * 0.04 * k, y + fwd[1] * 0.04 * k, z + fwd[2] * 0.04 * k],
                [0.30 * k, 0.30 * k, 0.16 * k], centre, rr)]
    if leaf:
        back = [x - fwd[0] * 0.03 * k, y - fwd[1] * 0.03 * k, z - fwd[2] * 0.03 * k]
        out.append(place("leaf", back, [k * 1.1, k * 0.9, k], leaf,
                         r=[rr[0], rr[1], rr[2] + 2.2]))
    return out


# ============================================================ 2022
LILAC = "#c7a8f0"
PINK = "#ff9cc9"
MINT = "#8fe3c0"
BUTTER = "#ffe58a"
SKYBLUE = "#9fd4ff"
CREAM = "#fff6e0"
STRAW = "#f1d98f"
GRASS = "#8fd36a"

EA22 = Event(
    "easter_2022", "easter", 2022, "ea22",
    name="Eggstravaganza", title="The Eggstravaganza",
    blurb="Blockhaven's first Easter. The mayor hid ten thousand painted eggs across "
          "every map in one night and declared a hunt. Nine thousand nine hundred and "
          "ninety-seven were found by Monday. The other three are still out there, and "
          "the big egg in the square has been rattling ever since.",
    tagline="Ten thousand eggs hidden. Three still missing.",
    starts="2022-04-08", ends="2022-04-26",
    colors={"accent": "#ff8fc8", "deep": "#2a1f3d", "glow": "#fff0a8"},
    family_effects=["sunbeam", "bubbly", "starstruck"],
    hero_effect="painted_parade", stencil="stencil_ea22")


@EA22.crate_model("Eggstravaganza Egg",
                  "The big egg from the town square: lilac, hand-painted, sat in a nest of "
                  "paper grass and cracked right round the top, which lifts off. Holds the "
                  "Eggstravaganza set. Needs a Painted Egg Key.",
                  hinge=[0, 0.12, -0.72], keyhole=[0, 0.01, 0.79])
def _():
    y0, k, ky = -0.80, 1.565, 1.33

    def Y(f):
        return y0 + EGG_H * ky * f
    parts = [
        place("crackedshell", [0, y0, 0], [k, ky, k], LILAC, anchor=[0, 0, 0],
              decal="ea_eggdots", wrap=True),
        place("ea_eggtop", [0, y0, 0], [k, ky, k], LILAC, anchor=[0, 0, 0],
              decal="ea_eggdots", wrap=True, lid=1),
        # the light inside, showing at the crack
        part("cyl", [0, Y(0.50), 0], [1.30, 0.05, 1.30], "#fff0a8", m="neon"),
        # painted bands on the bottom half: mint, then a zig-zag of butter
        _egg_band(0.12, 0.17, k, ky, y0, MINT),
        _egg_band(0.39, 0.49, k, ky, y0, BUTTER, mesh="spikecrown"),
        _egg_band(0.36, 0.39, k, ky, y0, PINK),
        # the nest: a shallow straw bowl, and paper grass spilling over it
        place("bowl", [0, -0.88, 0], [1.56, 0.56, 1.56], STRAW, anchor=[0, 0, 0],
              decal="ea_straw", wrap=True),
        part("torus", [0, -0.56, 0], [1.54, 0.5, 1.54], shade(STRAW, 0.9), decal="ea_straw",
             wrap=True),
        # the lock: a gold plate on the front, and a hasp down off the lid
        part("rbox", [0, 0.01, 0.745], [0.30, 0.32, 0.07], GOLD, decal="keyhole", m="metal",
             lock=1),
        part("rbox", [0, 0.24, 0.735], [0.12, 0.30, 0.05], GOLD, [0.08, 0, 0], m="metal", lid=1),
        part("torus", [0, 0.14, 0.775], [0.16, 0.25, 0.16], GOLD_DARK, [PI / 2, 0, 0], m="metal"),
        # the stencil, painted on the back
        part("box", [0, Y(0.30), -0.70], [0.62, 0.62, 0.02], "#000000", [0, PI, 0],
             decal="stencil_ea22", a=-1),
    ]
    # a row of spots round the front of the bottom half, two rows on the lid
    for n in range(7):
        a = -1.6 + n * 3.2 / 6
        parts.append(_egg_spot(0.25, a, k, ky, y0, 0.16, CREAM if n % 2 else PINK))
    for n in range(10):
        a = n * TAU / 10
        parts.append(_egg_spot(0.84, a, k, ky, y0, 0.14, PINK if n % 2 else SKYBLUE, lid=1))
    for n in range(6):
        a = n * TAU / 6 + 0.5
        parts.append(_egg_spot(0.93, a, k, ky, y0, 0.10, BUTTER, lid=1))
    # a pink bow tied on top
    parts += _lid(gift_bow([0, Y(1.0) - 0.02, 0], 0.55, PINK, knot="#ff7ab8"))
    # crinkled paper grass round the egg, in three greens and a pink
    for n in range(26):
        a = n * TAU / 26 + (0.12 if n % 2 else 0.0)
        rad = 0.66 if n % 2 else 0.74
        col = [GRASS, "#b5e88a", "#6fc25a", "#ffc4e1"][n % 4]
        parts.append(place("leaf", [math.sin(a) * rad, -0.50, math.cos(a) * rad],
                           [0.55, 0.42, 0.6], col, anchor=[0, -0.5, 0],
                           r=[0.45, a, 0]))
    return parts


@EA22.key_model("Painted Egg Key",
                "A key whose bow is a little painted egg, tied on with a pink ribbon, its "
                "teeth cut in a zig-zag like a crack. Opens one Eggstravaganza Egg.",
                shoulder=-0.30)
def _():
    parts = at_frame(_egg(0.46, LILAC, bands=[(0.16, 0.24, MINT), (0.62, 0.70, PINK)],
                          zig=(0.36, 0.50, BUTTER), dots=(0.84, 5, CREAM, 0.08)),
                     [-0.30, 0, 0], r=[0, 0, PI / 2])
    parts += [
        part("cyl", [0.18, 0, 0], [0.10, 0.98, 0.10], GOLD, [0, 0, PI / 2], m="metal"),
        part("cyl", [-0.30, 0, 0], [0.22, 0.08, 0.22], GOLD_DARK, [0, 0, PI / 2], m="metal"),
        # the bit: teeth in a zig-zag, each a different pastel
        part("rbox", [0.40, -0.13, 0], [0.09, 0.20, 0.08], PINK),
        part("rbox", [0.50, -0.10, 0], [0.09, 0.14, 0.08], MINT),
        part("rbox", [0.60, -0.15, 0], [0.09, 0.24, 0.08], BUTTER),
        part("sph", [0.68, 0, 0], [0.12, 0.12, 0.12], GOLD, m="metal"),
    ]
    parts += gift_bow([-0.24, 0.10, 0], 0.30, PINK, knot="#ff7ab8", yaw=PI / 2)
    return parts


@EA22.hat("parade_bonnet", "Easter Parade Bonnet",
          "A wide straw picture hat with a satin band, a bow down the back, and more "
          "silk flowers than a garden centre. Something has been nesting in them.",
          "rare")
def _():
    parts = [
        dome(-0.24, 0.78, STRAW, decal="ea_straw", wrap=True),
        place("brim", [0, -0.02, 0], [2.70, 1.2, 2.60], STRAW, anchor=[0, 0, 0],
              decal="ea_straw", wrap=True),
        part("cyl", [0, 0.10, 0], [1.74, 0.18, 1.70], PINK),
        # the bow at the back and its tails
        *gift_bow([0, 0.12, -0.84], 0.62, PINK, knot="#ff7ab8", yaw=0.0, tails=False),
        place("ribbon", [0.12, 0.02, -1.00], [0.16, 0.86, 0.05], PINK, anchor=[0, 0.5, 0],
              r=[0.25, 0, 0.16]),
        place("ribbon", [-0.12, 0.02, -1.00], [0.16, 0.80, 0.05], PINK, anchor=[0, 0.5, 0],
              r=[0.25, 0, -0.16]),
        # a painted egg tucked into the flowers
        *at_frame(_egg(0.30, SKYBLUE, bands=[(0.30, 0.40, CREAM)], dots=(0.64, 5, PINK, 0.12)),
                  [0.30, 0.12, 0.86], r=[0.3, 0, -0.4]),
    ]
    # silk flowers bunched up the front left of the brim
    for (x, y, z, c, s, tilt) in ((-0.42, 0.30, 0.88, "#ffb3d8", 0.62, -0.45),
                                  (-0.80, 0.30, 0.56, "#fff3b0", 0.56, -0.40),
                                  (-0.04, 0.24, 1.00, "#c7a8f0", 0.46, -0.6),
                                  (-0.98, 0.28, 0.12, "#ffffff", 0.48, -0.35),
                                  (-0.64, 0.58, 0.62, "#9fd4ff", 0.42, -0.2),
                                  (-0.24, 0.56, 0.84, "#ffd0a0", 0.40, -0.2)):
        parts += _flower([x, y, z], s, c, r=[tilt, math.atan2(x, z), 0], leaf="#6fc25a")
    # a butterfly that has decided this is the best flower in town
    for side in (1, -1):
        parts.append(place("heart", [0.10 * side, 0.58, 0.06], [0.24, 0.26, 0.5], "#ffb35a",
                           r=[0, 0, -0.9 * side]))
    parts.append(part("capsule", [0, 0.56, 0.06], [0.05, 0.18, 0.05], BLACK))
    return parts


@EA22.hat("egg_cosy", "Egg Cosy",
          "Knitted by a grandmother for an egg of unusual size. You are the egg of "
          "unusual size. It is very warm and it has a pompom.", "uncommon")
def _():
    return [
        dome(-0.28, 1.02, WHITE, decal="ea_cosy", wrap=True),
        ringband(-0.20, 0.22, "#ff9cc9", decal="knit", wrap=True),
        pompom([0, 0.80, 0], 0.44, "#ffb3d8"),
        # a felt chick sewn on the front
        part("sph", [0, 0.16, 0.80], [0.34, 0.32, 0.08], "#ffe14d", [-0.35, 0, 0]),
        part("sph", [0, 0.36, 0.73], [0.20, 0.18, 0.06], "#ffe14d", [-0.45, 0, 0]),
        part("sph", [0.05, 0.38, 0.77], [0.04, 0.04, 0.02], BLACK, [-0.45, 0, 0]),
        place("tri", [0.0, 0.31, 0.75], [0.08, 0.08, 0.3], "#ff8c1a", r=[-0.45, 0, PI]),
    ]


@EA22.hat("humpty_wall", "Humpty's Wall",
          "A good stretch of brick wall and the egg who sits on it, swinging his legs, "
          "with a bow tie on and a hairline crack he would rather you did not mention.",
          "legendary")
def _():
    shell, suit = "#f6eedc", "#4a6ab0"
    parts = [
        # the wall, coping stones along its top
        part("rbox", [0, 0.06, 0], [1.98, 0.56, 1.62], "#b8613e", decal="bricks", wrap=True),
        part("rbox", [0, 0.38, 0], [2.06, 0.10, 1.70], "#c9b8a4"),
        # Humpty, sat square on the top
        place("egg", [0, 0.43, 0.28], [0.82, 0.78, 0.82], shell, anchor=[0, 0, 0]),
        # his face: two eyes, a smile, and a little crack
        part("sph", [0.13, 0.98, 0.65], [0.13, 0.16, 0.06], WHITE, [-0.2, 0.35, 0]),
        part("sph", [-0.13, 0.98, 0.65], [0.13, 0.16, 0.06], WHITE, [-0.2, -0.35, 0]),
        part("sph", [0.137, 0.97, 0.675], [0.07, 0.09, 0.03], BLACK, [-0.2, 0.35, 0]),
        part("sph", [-0.137, 0.97, 0.675], [0.07, 0.09, 0.03], BLACK, [-0.2, -0.35, 0]),
        place("grin", [0, 0.84, 0.67], [0.26, 0.26, 0.4], "#7a2a2a", r=[-0.15, 0, 0]),
        part("box", [0.24, 1.10, 0.55], [0.012, 0.12, 0.02], "#6a5a4a", [0, 0.8, 0.5]),
        part("box", [0.28, 1.02, 0.54], [0.012, 0.09, 0.02], "#6a5a4a", [0, 0.8, -0.4]),
        # his bow tie and the front of his waistcoat
        place("bowtie", [0, 0.70, 0.70], [0.30, 0.30, 0.6], "#e0405a", r=[-0.3, 0, 0]),
        # arms resting on the coping, legs dangling over the front
        part("capsule", [0.38, 0.60, 0.40], [0.08, 0.32, 0.08], shell, [0.4, 0, 1.0]),
        part("capsule", [-0.38, 0.60, 0.40], [0.08, 0.32, 0.08], shell, [0.4, 0, -1.0]),
    ]
    for side in (1, -1):
        parts += [
            part("cyl", [0.15 * side, 0.50, 0.74], [0.11, 0.30, 0.11], suit, [PI / 2, 0, 0]),
            part("sph", [0.15 * side, 0.50, 0.89], [0.12, 0.12, 0.12], suit),
            part("cyl", [0.15 * side, 0.30, 0.91], [0.11, 0.40, 0.11], suit, [0.12, 0, 0]),
            part("rbox", [0.15 * side, 0.10, 0.98], [0.16, 0.10, 0.24], BLACK),
        ]
    return parts


@EA22.hat("flower_crown", "Spring Flower Crown",
          "A ring of every pastel flower in the meadow, woven together on a vine. "
          "Bees will follow you. Accept this.", "uncommon", hair="show")
def _():
    parts = [ringband(-0.16, 0.08, "#5a9a3a")]
    cols = ["#ffb3d8", "#fff3b0", "#c7a8f0", "#ffffff", "#9fd4ff"]
    r = 0.96
    for n in range(10):
        a = n * TAU / 10
        parts += _flower([math.sin(a) * r, -0.12, math.cos(a) * r * 0.96],
                         0.30 if n % 2 else 0.36, cols[n % len(cols)],
                         r=[-0.35, a, 0], leaf="#6fc25a" if n % 2 else None)
    # ribbons trailing down the back
    for side in (1, -1):
        parts.append(place("ribbon", [0.10 * side, -0.16, -1.00], [0.14, 0.70, 0.05],
                           PINK if side > 0 else SKYBLUE, anchor=[0, 0.5, 0],
                           r=[0.18, 0, 0.12 * side]))
    return parts


@EA22.hat("dye_pot", "Dye Pot Topper",
          "The enamel cup from the egg-dyeing table, worn upside down after an "
          "incident, still running pink, blue and yellow down the sides. The egg on "
          "the dipper came out half done.", "rare")
def _():
    enamel = "#f4f6f8"
    parts = [
        part("cyl", [0, 0.30, 0], [1.24, 0.58, 1.24], enamel),
        part("torus", [0, 0.01, 0], [1.36, 0.55, 1.36], "#4a6ab0"),
        part("cyl", [0, 0.57, 0], [1.10, 0.04, 1.10], "#4a6ab0"),
        # the handle, round the side
        place("arch", [0.62, 0.30, 0], [0.42, 0.50, 0.9], enamel, anchor=[0, 0, 0],
              r=[0, 0, -PI / 2]),
    ]
    # three colours run down the sides from the bottom (the cup's upturned
    # mouth), drips hanging off the rim
    for n, (a, c) in enumerate(((0.3, "#ff7ab8"), (1.5, "#6ab8ff"), (2.6, "#ffd84a"),
                                (3.7, "#ff7ab8"), (4.8, "#6ab8ff"), (5.7, "#ffd84a"))):
        x, z = math.sin(a), math.cos(a)
        h = 0.50 + 0.06 * (n % 3)
        parts += [
            part("capsule", [x * 0.625, 0.60 - h / 2, z * 0.625], [0.22, h, 0.05], c, [0, a, 0],
                 m="glass"),
            part("sph", [x * 0.52, 0.595, z * 0.52], [0.30, 0.03, 0.30], c, m="glass"),
        ]
        if n % 2 == 0:
            parts.append(place("teardrop", [x * 0.66, 0.66 - h, z * 0.66], [0.13, 0.22, 0.13], c,
                               r=[PI, 0, 0], m="glass"))
    # the wire dipper, still holding the egg that came out half dyed
    parts += [
        part("cyl", [-0.30, 0.86, 0.10], [0.035, 0.80, 0.035], SILVER, [0.2, 0, 0.5], m="metal"),
        part("torus", [-0.52, 1.24, 0.18], [0.30, 0.15, 0.30], SILVER, [0.3, 0, 0.5], m="metal"),
    ]
    parts += at_frame(_egg(0.30, "#ff9cc9", bands=[(0.5, 1.0, CREAM)]),
                      [-0.54, 1.12, 0.18], r=[0.3, 0, 0.5])
    return parts


@EA22.hat("hunt_deerstalker", "Egg Hunter's Deerstalker",
          "A deerstalker in pastel tweed, flaps tied up, a magnifying glass in the band. "
          "Eleven eggs found under it on the first morning. Elementary.", "rare")
def _():
    tweed = "#b8a6d8"
    parts = [
        dome(-0.30, 0.86, tweed, decal="ea_gingham", wrap=True),
        part("sph", [0, 0.56, 0], [0.16, 0.10, 0.16], "#7a5aa8"),
        # front and back peaks, turned down a little
        place("peak", [0, -0.22, 0], [1.05, 2.2, 1.70], shade(tweed, 0.88), anchor=[0, 0, 0],
              decal="ea_gingham", wrap=True),
        place("peak", [0, -0.22, 0], [1.05, 2.2, 1.70], shade(tweed, 0.88), anchor=[0, 0, 0],
              r=[0, PI, 0], decal="ea_gingham", wrap=True),
        ringband(-0.20, 0.10, "#7a5aa8"),
        # the ear flaps, tied up over the crown with a bow
        part("rbox", [0.73, 0.29, 0], [0.08, 0.60, 0.50], shade(tweed, 1.08), [0, 0, 0.735],
             decal="ea_gingham", wrap=True),
        part("rbox", [-0.73, 0.29, 0], [0.08, 0.60, 0.50], shade(tweed, 1.08), [0, 0, -0.735],
             decal="ea_gingham", wrap=True),
        part("cyl", [0, 0.53, 0], [0.025, 0.95, 0.025], PINK, [0, 0, PI / 2]),
        place("bowtie", [0, 0.53, 0], [0.30, 0.30, 0.6], PINK, r=[0, PI / 2, 0]),
        # the magnifying glass, tucked in at the side
        part("torus", [0.86, 0.18, 0.30], [0.40, 0.50, 0.40], BRASS, [PI / 2, PI / 2, 0.4],
             m="metal"),
        part("cyl", [0.86, 0.18, 0.30], [0.34, 0.02, 0.34], "#dff2ff", [PI / 2, PI / 2, 0.4],
             m="glass", a=0.5),
        part("cyl", [0.88, -0.10, 0.18], [0.08, 0.36, 0.08], "#5a3a22", [0.4, 0, 0.0]),
    ]
    return parts


@EA22.hat("egg_crown", "Crown of a Dozen Eggs",
          "A gold circlet set with twelve eggs, one from every map, each painted by "
          "hand and sat in its own cup. The thirteenth setting is empty. It knows.",
          "legendary", hair="show")
def _():
    parts = [
        ringband(-0.10, 0.20, GOLD, m="metal"),
        part("torus", [0, 0.0, 0], [1.92, 0.45, 1.88], GOLD_DARK, m="metal"),
    ]
    paints = [(LILAC, MINT), (PINK, CREAM), (BUTTER, SKYBLUE), (MINT, PINK),
              (SKYBLUE, BUTTER), (CREAM, LILAC)]
    for n in range(13):
        a = n * TAU / 13
        x, z = math.sin(a) * 0.93, math.cos(a) * 0.91
        parts.append(part("cyl", [x, 0.03, z], [0.18, 0.08, 0.18], GOLD, m="metal"))
        if n == 0:
            # the empty setting, front and centre
            parts.append(part("torus", [x, 0.08, z], [0.18, 0.2, 0.18], GOLD_DARK, m="metal"))
            continue
        body, stripe = paints[n % len(paints)]
        parts += at_frame(_egg(0.20, body, bands=[(0.40, 0.52, stripe)],
                               dots=(0.74, 4, WHITE, 0.10)),
                          [x, 0.07, z], r=[0.18 * math.cos(a), 0, -0.18 * math.sin(a)])
    return parts


@EA22.back("hunt_basket", "Egg Hunt Basket",
           "A wicker basket on your back, heaped with paper grass and the morning's "
           "haul. Some of the eggs in it are not yours. Keep walking.", "rare")
def _():
    parts = [
        place("bowl", [0, -0.42, -0.68], [1.60, 1.30, 1.18], "#d8b06a", anchor=[0, 0, 0],
              decal="ea_wicker", wrap=True),
        part("torus", [0, 0.33, -0.68], [1.58, 0.7, 1.16], "#b88a4a", decal="ea_wicker", wrap=True),
        place("arch", [0, 0.34, -0.68], [1.30, 1.15, 1.0], "#b88a4a", anchor=[0, 0, 0],
              decal="ea_wicker", wrap=True),
        *straps("#b88a4a", 0.36, 0.13),
        part("rbox", [0, 0.40, -0.08], [0.20, 0.12, 0.10], "#8a6a3a"),
    ]
    # paper grass heaped up, and the eggs on top of it
    for n in range(14):
        a = n * TAU / 14
        parts.append(place("leaf", [math.sin(a) * 0.52, 0.30, -0.68 + math.cos(a) * 0.36],
                           [0.45, 0.40, 0.5], [GRASS, "#b5e88a", "#ffc4e1"][n % 3],
                           anchor=[0, -0.5, 0], r=[0.45, a, 0]))
    for (x, z, c, s, tilt) in ((-0.30, -0.58, PINK, 0.36, 0.3), (0.24, -0.78, SKYBLUE, 0.38, -0.3),
                               (0.02, -0.46, BUTTER, 0.34, 0.1), (-0.14, -0.90, MINT, 0.36, 0.5),
                               (0.42, -0.52, LILAC, 0.32, -0.6)):
        parts += at_frame(_egg(s, c, bands=[(0.42, 0.52, CREAM)], dots=(0.72, 4, WHITE, 0.10)),
                          [x, 0.22, z], r=[0.2, 0, tilt])
    return parts


@EA22.back("butterfly_wings", "Pastel Butterfly Wings",
           "Four wings in sugared-almond colours, spotted like a painted egg, and they "
           "flutter when you run. Caterpillars are very jealous.", "uncommon")
def _():
    parts = [part("capsule", [0, 0.42, -0.20], [0.14, 0.80, 0.14], "#4a3a5a")]
    for side in (1, -1):
        parts += [
            place("heart", [0.74 * side, 0.86, -0.34], [1.36, 1.36, 0.5], "#d2b6ff",
                  r=[0.15, 0.35 * side, -0.785 * side]),
            place("heart", [0.54 * side, 0.02, -0.28], [0.92, 0.92, 0.5], "#ffbfdf",
                  r=[0.15, 0.35 * side, -2.36 * side]),
            part("sph", [0.86 * side, 1.00, -0.42], [0.32, 0.32, 0.05], BUTTER,
                 [0.15, 0.35 * side, 0]),
            part("sph", [0.60 * side, -0.06, -0.35], [0.22, 0.22, 0.05], WHITE,
                 [0.15, 0.35 * side, 0]),
            part("cyl", [0.10 * side, 1.00, -0.20], [0.03, 0.44, 0.03], "#4a3a5a",
                 [0, 0, -0.5 * side]),
            part("sph", [0.21 * side, 1.20, -0.20], [0.08, 0.08, 0.08], "#4a3a5a"),
        ]
    return parts


@EA22.hairdo("pastel_pigtails", "Pastel Pigtails",
             "Candyfloss pink, in two bunches tied off with little painted-egg bobbles.",
             "uncommon")
def _():
    c = "#f2a7c8"
    parts = [place("hairmid", [0, 0, 0], [1.04, 1.04, 1.04], c, anchor=[0, 0, 0],
                   decal="strands", wrap=True)]
    for side in (1, -1):
        parts += [
            place("teardrop", [0.60 * side, 0.14, -0.14], [0.38, 0.70, 0.38], c,
                  anchor=[0, 1.0, 0], r=[0, 0, 0.85 * side], decal="strands", wrap=True),
            *at_frame(_egg(0.12, BUTTER if side > 0 else MINT, bands=[(0.40, 0.55, WHITE)]),
                      [0.56 * side, 0.13, -0.14], r=[0, 0, -PI / 2 * side]),
        ]
    return parts


@EA22.hairdo("bobbed_bow", "Sunday Best Bob",
             "A neat lilac bob with a fringe, a big pink bow and a hair clip shaped like "
             "a fried egg. It was a long morning.", "rare")
def _():
    c = "#b89ae0"
    return [
        place("hairbob", [0, 0, 0], [1.05, 1.05, 1.05], c, anchor=[0, 0, 0],
              decal="strands", wrap=True),
        place("bowtie", [0.30, 0.50, 0.12], [0.44, 0.44, 0.9], PINK, r=[-0.6, 0.6, 0.3]),
        part("sph", [0.31, 0.51, 0.14], [0.11, 0.11, 0.10], "#ff7ab8", [-0.6, 0.6, 0.3]),
        # the fried egg clip, over the other ear
        part("cyl", [-0.585, 0.12, 0.16], [0.24, 0.03, 0.21], WHITE, [0, 0, PI / 2 - 0.15]),
        part("sph", [-0.605, 0.12, 0.16], [0.06, 0.10, 0.10], "#ffc21a", [0, 0, -0.15]),
    ]


EA22.face("egg_cited", "Egg-cited",
          "Eyes like saucers and a grin that will not quit. Somebody found the golden "
          "egg. It was not you, but you are happy for them. Mostly.", [
              {"k": "ellipse", "x": -0.20, "y": -0.13, "w": 0.17, "h": 0.20, "c": "#16171b"},
              {"k": "ellipse", "x": 0.20, "y": -0.13, "w": 0.17, "h": 0.20, "c": "#16171b"},
              {"k": "ellipse", "x": -0.23, "y": -0.17, "w": 0.06, "h": 0.07, "c": "#ffffff"},
              {"k": "ellipse", "x": 0.17, "y": -0.17, "w": 0.06, "h": 0.07, "c": "#ffffff"},
              {"k": "ellipse", "x": -0.17, "y": -0.08, "w": 0.03, "h": 0.03, "c": "#ffffff"},
              {"k": "ellipse", "x": 0.23, "y": -0.08, "w": 0.03, "h": 0.03, "c": "#ffffff"},
              {"k": "poly", "pts": [[-0.20, 0.06], [0.20, 0.06], [0.14, 0.20], [0.0, 0.25],
                                    [-0.14, 0.20]], "c": "#16171b"},
              {"k": "ellipse", "x": 0.0, "y": 0.18, "w": 0.14, "h": 0.06, "c": "#ff7a9a"},
              {"k": "ellipse", "x": -0.33, "y": 0.04, "w": 0.09, "h": 0.05, "c": "#ffa8c8"},
              {"k": "ellipse", "x": 0.33, "y": 0.04, "w": 0.09, "h": 0.05, "c": "#ffa8c8"},
          ], "uncommon")
EA22.face("sunny_side_up", "Sunny Side Up",
          "Two eggs, fried, where the eyes go, and a satisfied smile. Breakfast is the "
          "most important face of the day.", [
              {"k": "poly", "pts": [[-0.34, -0.14], [-0.30, -0.24], [-0.20, -0.27], [-0.10, -0.22],
                                    [-0.06, -0.12], [-0.11, -0.03], [-0.22, -0.01], [-0.31, -0.05]],
               "c": "#fffaf0"},
              {"k": "poly", "pts": [[0.06, -0.15], [0.11, -0.24], [0.22, -0.28], [0.32, -0.21],
                                    [0.35, -0.12], [0.30, -0.03], [0.18, -0.01], [0.09, -0.06]],
               "c": "#fffaf0"},
              {"k": "ellipse", "x": -0.20, "y": -0.14, "w": 0.10, "h": 0.10, "c": "#ffb81a"},
              {"k": "ellipse", "x": 0.21, "y": -0.14, "w": 0.10, "h": 0.10, "c": "#ffb81a"},
              {"k": "ellipse", "x": -0.22, "y": -0.16, "w": 0.03, "h": 0.03, "c": "#fff3c0"},
              {"k": "ellipse", "x": 0.19, "y": -0.16, "w": 0.03, "h": 0.03, "c": "#fff3c0"},
              {"k": "arc", "x": 0, "y": 0.04, "r": 0.15, "a0": 0.08, "a1": 0.42, "w": 0.035,
               "c": "#16171b"},
          ], "rare")
EA22.shirt("hunt_marshal", "Hunt Marshal's Polo",
           "Mint green, a pink trim, and the badge that lets you say 'that one is mine, I "
           "saw it first' with real authority.",
           {"torso": "#9fe3c8", "arms": "#9fe3c8", "decal": "ea_tee_marshal",
            "stripe": "#ff9cc9", "sleeves": 0.45}, "rare")
EA22.pants("zigzag_dungarees", "Zig-Zag Dungarees",
           "Lilac, with a crack of every pastel running round and round. Hard to lose "
           "in a hedge.", {"legs": "#c7a8f0", "weave": "ea_zigzag"})
EA22.belt("egg_pouches", "Egg Hunter's Belt",
          "Gingham, with two padded pouches on the front for carrying eggs. They are "
          "padded for a reason. Ask about the first one.",
          {"band": "#ff9cc9", "buckle": "#fff3b0", "width": 0.22, "weave": "ea_gingham",
           "pouch": True})


@EA22.weapon("clutch_launcher", "Clutch Launcher",
             "A painted tube that lobs a whole clutch of eggs in one shell. A moment out "
             "of the barrel the shell cracks, and four eggs fan out across the field.",
             {"kind": "projectile", "projectile": "egg", "damage": 22, "splash": 3.6,
              "splash_damage": 18, "rpm": 54, "mag": 4, "reload": 2.4, "speed": 64,
              "range": 280, "auto": False, "sound": "pop", "recoil": 1.8, "reserve": 24,
              "gravity_scale": 0.9, "self_damage": 0.0, "knockback": 7,
              "split": {"after": 0.30, "count": 4, "spread": 9, "damage": 15,
                        "splash_damage": 14}},
             [["+", "The shell cracks a moment out of the barrel into four eggs that fan "
                    "out side by side"],
              ["+", "Your own eggs cannot hurt you"],
              ["-", "Each egg is small: 15 on a hit, a 3.6 stud splash"],
              ["-", "Up close, the shell has not cracked yet"]], rarity="legendary",
             proj=lambda: at_frame(_egg(0.42, LILAC, bands=[(0.30, 0.40, MINT)],
                                        zig=(0.52, 0.64, BUTTER)),
                                   [0, 0, -0.28], r=[PI / 2, 0, 0]))
def _():
    tube = "#c7a8f0"
    parts = [
        part("cyl", [0, 0.08, 0.50], [0.40, 1.30, 0.40], tube, [PI / 2, 0, 0],
             decal="ea_eggdots", wrap=True),
        part("torus", [0, 0.08, 1.14], [0.48, 0.5, 0.48], PINK, [PI / 2, 0, 0]),
        part("torus", [0, 0.08, -0.12], [0.46, 0.5, 0.46], MINT, [PI / 2, 0, 0]),
        part("rbox", [0, -0.22, 0.02], [0.16, 0.46, 0.22], "#7a5aa8", [-0.25, 0, 0]),
        part("rbox", [0, -0.10, 0.50], [0.14, 0.30, 0.20], "#7a5aa8", [0.3, 0, 0]),
        # the ammunition: a half-dozen box clipped on top
        part("rbox", [0, 0.40, 0.30], [0.30, 0.14, 0.50], CREAM),
    ]
    for n in range(3):
        parts.append(part("sph", [0, 0.50, 0.14 + n * 0.16], [0.13, 0.15, 0.13],
                          [PINK, BUTTER, SKYBLUE][n]))
    # an egg peeking out of the muzzle
    parts += at_frame(_egg(0.30, BUTTER, bands=[(0.40, 0.50, PINK)]), [0, 0.08, 1.06],
                      r=[PI / 2, 0, 0])
    return parts


@EA22.weapon("dye_hard", "Dye Hard",
             "A wire dipper and a bucket of eggs blown hollow and filled with dye. Whoever "
             "is splashed cannot see for the paint, and everyone else can see them a mile "
             "off.",
             {"kind": "projectile", "projectile": "paintegg", "damage": 8, "splash": 5.5,
              "splash_damage": 10, "rpm": 46, "mag": 2, "reload": 2.2, "speed": 58,
              "range": 220, "auto": False, "sound": "throw", "recoil": 0.8, "reserve": 20,
              "gravity_scale": 1.3, "self_damage": 0.0, "knockback": 3,
              "on_hit": {"blind": [1.8, "confetti"], "mark": [0.20, 4.0]}},
             [["+", "Everyone in the splash is blinded by dye for 1.8 seconds"],
              ["+", "...and marked: they take 20% more damage from everybody for 4 seconds"],
              ["-", "Barely hurts: 10 at the most"],
              ["-", "Two eggs, then a reload"]], rarity="legendary",
             proj=lambda: at_frame(_egg(0.40, WHITE, bands=[(0.0, 0.34, "#ff7ab8"),
                                                            (0.34, 0.62, "#6ab8ff")]),
                                   [0, 0, -0.26], r=[PI / 2, 0, 0]))
def _():
    wire = SILVER
    parts = [
        part("cyl", [0, 0.0, 0.55], [0.07, 1.70, 0.07], wire, [PI / 2, 0, 0], m="metal"),
        part("cyl", [0, 0.0, -0.20], [0.18, 0.56, 0.18], "#ff9cc9", [PI / 2, 0, 0]),
        part("torus", [0, 0.0, -0.50], [0.20, 0.4, 0.20], "#ff7ab8", [PI / 2, 0, 0]),
        part("torus", [0, 0.0, 1.62], [0.62, 0.3, 0.62], wire, [PI / 2, 0, 0], m="metal"),
        part("torus", [0, 0.0, 1.62], [0.62, 0.3, 0.62], wire, [PI / 2, PI / 2, 0], m="metal"),
    ]
    # the dyed egg in the dipper's cradle, dripping
    parts += at_frame(_egg(0.44, WHITE, bands=[(0.0, 0.36, "#ff7ab8"), (0.36, 0.64, "#6ab8ff")]),
                      [0, -0.24, 1.62])
    parts += [place("teardrop", [0.08, -0.38, 1.62], [0.10, 0.18, 0.10], "#ff7ab8",
                    r=[PI, 0, 0], m="glass"),
              place("teardrop", [-0.10, -0.32, 1.58], [0.08, 0.14, 0.08], "#6ab8ff",
                    r=[PI, 0, 0], m="glass")]
    return parts


@EA22.weapon("balloon_whisk", "Balloon Whisk",
             "The big whisk from the bake-off tent. It does not hit hard, but keep "
             "whisking and it whips up a froth that hits harder with every stroke.",
             {"kind": "melee", "damage": 17, "headshot": 1.0, "rpm": 160, "range": 9.5,
              "arc": 0.62, "sound": "swing", "knockback": 4,
              "combo": {"window": 1.2, "step": 0.15, "max": 0.75, "label": "Froth"}},
             [["+", "Every hit within 1.2 seconds of the last whips up 15% more damage, "
                    "up to +75%"],
              ["+", "Very quick: 160 strokes a minute"],
              ["-", "Starts out feeble: 17 damage"],
              ["-", "Miss, or stop for breath, and the froth goes flat"]], rarity="legendary")
def _():
    wire = "#dfe4ea"
    parts = [
        part("cyl", [0, 0.0, 0.0], [0.20, 0.80, 0.20], PINK, [PI / 2, 0, 0]),
        part("cyl", [0, 0.0, 0.44], [0.13, 0.14, 0.13], wire, [PI / 2, 0, 0], m="metal"),
        part("torus", [0, 0.0, -0.46], [0.18, 0.4, 0.18], wire, [0, 0, PI / 2], m="metal"),
    ]
    # the balloon of wires: half-loops standing round the axis
    for n in range(5):
        a = n * PI / 5
        parts.append(place("arch", [0, 0.0, 0.48], [0.80, 2.40, 1.4], wire, anchor=[0, 0, 0],
                           r=_euler(("y", a), ("x", PI / 2)), m="metal"))
    parts.append(part("sph", [0, 0.0, 1.70], [0.22, 0.22, 0.22], CREAM, a=0.7))
    return parts


@EA22.weapon("hunt_basket_toss", "Egg Hunt Basket",
           "A little basket of painted eggs, thrown underarm. It tips out where it lands "
           "and the eggs roll about for your team to find -- each one a bite of chocolate "
           "in a painted shell.",
           {"kind": "projectile", "projectile": "basket", "damage": 0, "splash": 0,
            "splash_damage": 0, "rpm": 30, "mag": 1, "reload": 20.0, "speed": 40,
            "range": 120, "auto": False, "sound": "throw", "recoil": 0.4, "reserve": 30,
            "gravity_scale": 1.4, "self_damage": 0.0, "knockback": 0, "held_item": True,
            "pickups": {"count": 5, "spread": 6.0, "heal": 15, "haste": [0.15, 3.0],
                        "secs": 15.0, "radius": 3.0, "color": "#ff9cc9"}},
           [["+", "Spills five eggs where it lands; each heals whoever of your team finds "
                  "it 15, with a quick burst of speed"],
            ["+", "Lobs well over cover"],
            ["-", "Takes 20 seconds to fill a new basket"],
            ["-", "The eggs only keep for 15 seconds"]], rarity="rare", grade="",
             proj=lambda: [place("bowl", [0, -0.2, 0], [0.9, 0.7, 0.9], "#d8b06a", anchor=[0, 0, 0],
                                 decal="ea_wicker", wrap=True),
                           place("arch", [0, 0.2, 0], [0.8, 1.1, 1.0], "#b88a4a", anchor=[0, 0, 0],
                                 r=[0, PI / 2, 0]),
                           part("sph", [0.1, 0.18, 0.05], [0.24, 0.30, 0.24], PINK),
                           part("sph", [-0.12, 0.16, -0.06], [0.24, 0.30, 0.24], SKYBLUE)])
def _():
    parts = [
        place("bowl", [0, -0.30, 0.42], [0.90, 0.72, 0.84], "#d8b06a", anchor=[0, 0, 0],
              decal="ea_wicker", wrap=True),
        part("torus", [0, 0.12, 0.42], [0.90, 0.5, 0.84], "#b88a4a"),
        place("arch", [0, 0.14, 0.42], [0.72, 1.10, 0.8], "#b88a4a", anchor=[0, 0, 0],
              r=[0, PI / 2, 0]),
    ]
    for (x, z, c) in ((-0.14, 0.34, PINK), (0.14, 0.52, SKYBLUE), (0.0, 0.42, BUTTER),
                      (0.16, 0.28, MINT)):
        parts += at_frame(_egg(0.22, c, bands=[(0.42, 0.55, WHITE)]), [x, -0.02, z],
                          r=[0.25, 0, x * 2])
    # carried by the handle: the hand closes round the top of the arch
    return at_frame(parts, [0, -0.72, -0.42])


EA22.effect("painted_parade", name="Painted Parade", rate=2.8, life=[2.2, 3.0],
            size=[0.26, 0.38], grow=0.0, gravity=0.0, spread=0.15, rise=[0.05, 0.2],
            blend="normal", spin=0.4, colors=["#ff9cc9", "#c7a8f0", "#8fe3c0", "#ffe58a"],
            shape="egg", radius=0.86, orbit=1.2, upright=True, wobble=0.35)
EA22.effect("spring_shower", name="Spring Shower", rate=6.0, life=[1.8, 2.6],
            size=[0.18, 0.30], grow=0.0, gravity=0.5, spread=0.8, rise=[0.6, 1.0],
            blend="normal", spin=2.0, colors=["#ffb3d8", "#fff3b0", "#c7a8f0", "#ffffff"],
            shapes=["flower", "flower", "butterfly"], radius=0.7, wobble=0.5)
EA22.opening(
    sky={"top": "#6fbaf0", "horizon": "#ffe3f1", "sun": [0.3, 0.8, 0.5], "clouds": 0,
         "tint": "#fff4fb"},
    ambient="#e8dcff", beam="#fff0a8", seep="painted_parade", after="spring_shower",
    burst=["#ff9cc9", "#c7a8f0", "#8fe3c0", "#ffe58a", "#ffffff"],
    pieces=[{"shape": "egg", "colors": ["#ff9cc9", "#c7a8f0", "#8fe3c0", "#ffe58a", "#9fd4ff"],
             "blend": "normal"},
            {"shape": "flower", "colors": ["#ffb3d8", "#fff3b0", "#ffffff"], "blend": "normal"},
            {"shape": "confetti", "colors": ["#ff9cc9", "#8fe3c0", "#ffe58a"], "blend": "normal"},
            {"shape": "star", "colors": ["#fff0a8", "#ffffff"], "blend": "add"}],
    backdrop="ea_eggfair", title_wait="Somebody is checking under the bandstand...",
    title_shake="Found one!")
EA22.award("Eggstravaganza", ["Egg Spotter", "Basket Carrier", "Dye Dipper", "Hunt Marshal",
                              "Golden Yolk", "Grand Eggsplorer"],
           "Opened Eggstravaganza Eggs during Blockhaven's first Easter, 2022.", "em_egg", "egg")
EA22.bundle("pair", "Egg and Key", 1, 1050, "One Eggstravaganza Egg, one Painted Egg Key.")
EA22.bundle("clutch", "A Clutch of Three", 3, 3000, "Three eggs, three keys. Saves 300.")



# ============================================================ 2023
EARTH = "#6a4a2e"
TURF = "#5fb84a"
CARROT = "#ff8a2a"
CARROT_TOP = "#4f9e3a"
BUNNY = "#f6f2ee"
NOSE = "#ff8fb0"
CORD = "#8a6a44"


def _carrot(at, k=1.0, r=None, leaves=True, **kw):
    """A carrot ``k`` long, its shoulders at ``at`` and its tip pointing
    down (turned as a whole by ``r``), with a tuft of leaves on top."""
    pieces = [place("carrot", [0, 0, 0], [1.0, 1.0, 1.0], CARROT, anchor=[0, 1.0, 0])]
    if leaves:
        for a in (-0.5, 0.0, 0.5):
            pieces.append(place("leaf", [math.sin(a) * 0.06, 0.20, math.cos(a) * 0.03],
                                [0.70, 0.42, 1.0], CARROT_TOP, r=[0, 0, a * 0.9]))
    out = at_frame(pieces, at, r, k)
    for p in out:
        p.update(kw)
    return out


def _bunny_head(at, k=1.0, yaw=0.0, lop=False, **kw):
    """A white rabbit's head looking along ``yaw`` from ``at`` (its middle):
    round cheeks, a pink nose, two long ears (one flopped over if ``lop``)."""
    pieces = [
        part("sph", [0, 0, 0], [0.50, 0.44, 0.46], BUNNY, decal="fur", wrap=True),
        part("sph", [0.10, -0.08, 0.16], [0.20, 0.18, 0.18], BUNNY),
        part("sph", [-0.10, -0.08, 0.16], [0.20, 0.18, 0.18], BUNNY),
        part("sph", [0, -0.02, 0.24], [0.08, 0.06, 0.05], NOSE),
        part("sph", [0.11, 0.06, 0.19], [0.07, 0.09, 0.04], BLACK),
        part("sph", [-0.11, 0.06, 0.19], [0.07, 0.09, 0.04], BLACK),
        part("rbox", [0, -0.17, 0.21], [0.08, 0.07, 0.02], WHITE),
        place("bunnyear", [0.10, 0.40, -0.02], [0.32, 0.46, 1.0], BUNNY, anchor=[0, -0.5, 0],
              r=[-0.15, 0, -0.12]),
        place("bunnyear", [0.10, 0.40, 0.012], [0.20, 0.36, 0.6], NOSE, anchor=[0, -0.5, 0],
              r=[-0.15, 0, -0.12]),
        place("bunnyear", [-0.10, 0.40, -0.02], [0.32, 0.46, 1.0], BUNNY, anchor=[0, -0.5, 0],
              r=[-0.15, 0, 1.4 if lop else 0.12]),
    ]
    out = at_frame(pieces, at, [0, yaw, 0], k)
    for p in out:
        p.update(kw)
    return out


EA23 = Event(
    "easter_2023", "easter", 2023, "ea23",
    name="Bunny Burrow", title="The Bunny Burrow",
    blurb="Easter 2023 the egg hunt went underground. Somebody had dug a warren under "
          "the hill behind the spawn -- a round green door, a little tin chimney, "
          "carrots growing out of the roof -- and every morning there were more holes "
          "in the lawn and fewer carrots in the allotments.",
    tagline="Mind the holes. Mind the carrots. Mind your ankles.",
    starts="2023-03-31", ends="2023-04-18",
    colors={"accent": "#ff8a2a", "deep": "#2a3a1a", "glow": "#fff0a8"},
    family_effects=["sunbeam", "bubbly", "starstruck"],
    hero_effect="carrot_patch", stencil="stencil_ea23")


@EA23.crate_model("Burrow Mound",
                  "A hump of earth with turf for a roof, a round green door with a brass "
                  "knob, a lit window and a tin chimney, and carrots coming up through the "
                  "grass. Holds the Bunny Burrow set. Needs a Carrot Key.",
                  hinge=[0, 0.12, -0.66], keyhole=[0.18, -0.30, 0.73])
def _():
    wood = "#3f8a4a"
    parts = [
        # the mound of dug earth, and the turf over the top of it (the lid)
        place("hemi", [0, -0.62, 0], [1.84, 2.2, 1.44], EARTH, anchor=[0, 0, 0],
              decal="ea_earth", wrap=True),
        part("cyl", [0, 0.08, 0], [1.40, 0.04, 1.10], "#ffd36a", m="neon"),
        place("hemi", [0, 0.08, 0], [1.44, 1.06, 1.14], TURF, anchor=[0, 0, 0],
              decal="ea_turf", wrap=True, lid=1),
        # the round front door in its frame, and the knob (the lock)
        part("cyl", [0, -0.30, 0.655], [0.62, 0.06, 0.62], wood, [PI / 2, 0, 0], decal="planks"),
        part("torus", [0, -0.30, 0.68], [0.70, 0.08, 0.70], "#5a3a22", [PI / 2, 0, 0]),
        part("cyl", [0.18, -0.30, 0.70], [0.16, 0.05, 0.16], BRASS, [PI / 2, 0, 0], m="metal",
             decal="keyhole", lock=1),
        part("sph", [0.18, -0.30, 0.74], [0.08, 0.08, 0.06], GOLD, m="metal"),
        # a lit window round the side
        part("cyl", [0.56, -0.12, 0.47], [0.24, 0.04, 0.24], "#ffd36a", [PI / 2, 0.75, 0],
             m="neon"),
        part("torus", [0.57, -0.12, 0.48], [0.28, 0.05, 0.28], "#5a3a22", [PI / 2, 0.75, 0]),
        # the stencil on the back
        part("box", [0, -0.28, -0.70], [0.66, 0.42, 0.02], "#000000", [0, PI, 0],
             decal="stencil_ea23", a=-1),
        # the tin chimney through the turf, with a curl of smoke
        part("cyl", [-0.36, 0.56, -0.18], [0.14, 0.34, 0.14], SILVER, m="metal", lid=1),
        part("cyl", [-0.36, 0.74, -0.18], [0.18, 0.04, 0.18], SILVER, m="metal", lid=1),
        part("sph", [-0.32, 0.92, -0.18], [0.16, 0.14, 0.16], "#e8eef4", a=0.6, lid=1),
        part("sph", [-0.26, 1.06, -0.20], [0.12, 0.10, 0.12], "#e8eef4", a=0.45, lid=1),
    ]
    # carrots coming up through the roof
    for x, z, k in ((0.24, 0.10, 0.50), (0.44, -0.14, 0.42), (0.06, -0.28, 0.46)):
        parts += _carrot([x, 0.62 - (x * x + z * z) * 0.5, z], k, lid=1)
    # the mailbox by the door
    parts += [part("rbox", [-0.72, -0.42, 0.66], [0.06, 0.40, 0.06], "#5a3a22"),
              part("rbox", [-0.72, -0.18, 0.66], [0.22, 0.14, 0.14], "#c4281c", m="metal"),
              part("rbox", [-0.60, -0.14, 0.66], [0.02, 0.10, 0.04], "#ffd36a", m="metal")]
    # flowers round the foot of the mound
    for x, z, c in ((0.60, 0.40, PINK), (-0.40, 0.60, BUTTER), (0.80, 0.0, LILAC)):
        parts += _flower([x, -0.52, z], 0.18, c, r=[-0.4, math.atan2(x, z), 0])
    return parts


@EA23.key_model("Carrot Key",
                "A brass key with a carrot for a bow, leaves and all. Opens one Burrow "
                "Mound. Do not let a rabbit see you holding it.", shoulder=-0.28)
def _():
    parts = _carrot([-0.62, 0.26, 0], 0.62, r=[0, 0, 0.0])
    parts += [
        part("cyl", [-0.03, 0, 0], [0.09, 1.16, 0.09], BRASS, [0, 0, PI / 2], m="metal"),
        part("torus", [-0.44, 0, 0], [0.20, 0.07, 0.20], GOLD_DARK, [0, 0, PI / 2], m="metal"),
        part("rbox", [0.40, -0.12, 0], [0.08, 0.22, 0.08], BRASS, m="metal"),
        part("rbox", [0.52, -0.10, 0], [0.08, 0.18, 0.08], BRASS, m="metal"),
    ]
    return parts


@EA23.hat("burrow_hat", "Burrow Hat",
          "A hump of lawn on your head with a hole in the top, and somebody living in "
          "it. He comes up to see what is going on. He does not like what is going on.",
          "legendary")
def _():
    parts = [
        dome(-0.26, 0.74, TURF, decal="ea_turf", wrap=True),
        ringband(-0.24, 0.10, EARTH, decal="ea_earth", wrap=True),
        # the hole, and its tenant
        part("cyl", [0.10, 0.46, 0.12], [0.50, 0.04, 0.46], "#2a1a10"),
        part("torus", [0.10, 0.46, 0.12], [0.54, 0.08, 0.50], EARTH),
        *_bunny_head([0.10, 0.80, 0.16], 1.30, yaw=0.15, lop=True),
        part("sph", [0.30, 0.52, 0.40], [0.18, 0.12, 0.18], BUNNY),
        part("sph", [-0.08, 0.52, 0.42], [0.18, 0.12, 0.18], BUNNY),
    ]
    parts += _carrot([-0.38, 0.40, -0.20], 0.40, r=[0.2, 0, 0.3])
    parts += _flower([-0.40, 0.30, 0.46], 0.20, PINK, r=[-0.6, -0.5, 0])
    return parts


@EA23.hat("lop_ears", "Lop Ears",
          "A pair of rabbit ears on a band: one standing up straight, one flopped over "
          "sideways like it has heard something it did not like.", "uncommon", hair="show")
def _():
    band_c = "#f2f3f3"
    parts = [
        part("rbox", [0, 0.035, 0], [1.00, 0.07, 0.16], band_c),
        *sides(lambda s: [
            part("rbox", [0.62 * s, -0.035, 0], [0.34, 0.07, 0.16], band_c, [0, 0, 0.55 * s]),
            part("rbox", [0.775 * s, -0.42, 0], [0.07, 0.62, 0.16], band_c),
            part("sph", [0.79 * s, -0.74, 0], [0.10, 0.10, 0.18], band_c),
        ]),
        # the upright ear
        place("bunnyear", [0.28, 0.08, 0.0], [0.80, 0.86, 1.6], BUNNY, anchor=[0, -0.5, 0],
              r=[-0.1, 0, -0.12], decal="fur", wrap=True),
        place("bunnyear", [0.28, 0.08, 0.04], [0.52, 0.70, 1.0], NOSE, anchor=[0, -0.5, 0],
              r=[-0.1, 0, -0.12]),
        # the lop: out sideways from the band, folded, and hanging down by the ear
        place("bunnyear", [-0.26, 0.12, 0.0], [0.80, 0.64, 1.6], BUNNY, anchor=[0, -0.5, 0],
              r=[0.0, 0, 1.70], decal="fur", wrap=True),
        place("bunnyear", [-0.26, 0.12, 0.04], [0.52, 0.52, 1.0], NOSE, anchor=[0, -0.5, 0],
              r=[0.0, 0, 1.70]),
        part("sph", [-0.92, 0.08, 0.0], [0.22, 0.18, 0.14], BUNNY, decal="fur", wrap=True),
        place("bunnyear", [-0.98, 0.10, 0.0], [0.80, 0.66, 1.6], BUNNY, anchor=[0, -0.5, 0],
              r=[0.0, 0, 2.98], decal="fur", wrap=True),
        place("bunnyear", [-0.98, 0.10, 0.04], [0.52, 0.54, 1.0], NOSE, anchor=[0, -0.5, 0],
              r=[0.0, 0, 2.98]),
    ]
    return parts


@EA23.hat("allotment_sunhat", "Allotment Sunhat",
          "A wide straw sunhat with a gingham band, and two seed packets tucked into it "
          "so you never forget what you planted. You will still forget where.",
          "uncommon")
def _():
    return [
        place("brim", [0, -0.12, 0], [2.60, 1.2, 2.50], STRAW, anchor=[0, 0, 0],
              decal="ea_straw", wrap=True),
        dome(-0.30, 0.82, STRAW, t="capcrown", decal="ea_straw", wrap=True),
        ringband(-0.20, 0.18, "#ff8fb0", margin=0.05, decal="ea_gingham", wrap=True),
        part("rbox", [0.40, 0.02, 0.86], [0.24, 0.32, 0.02], "#ffffff", [-0.1, 0.42, 0],
             decal="ea_seeds"),
        part("rbox", [0.62, 0.0, 0.70], [0.24, 0.32, 0.02], "#ffffff", [-0.1, 0.80, 0.1],
             decal="ea_seeds"),
    ]


@EA23.hat("watering_can", "Watering Can",
          "The galvanised can from the allotment shed, worn upside down. The rose on "
          "the spout has sprouted, because somebody forgot to empty it.", "rare")
def _():
    zinc = "#a8b4bc"
    parts = [
        part("cyl", [0, 0.36, 0], [1.12, 0.70, 1.06], zinc, m="metal", decal="rivets", wrap=True),
        part("torus", [0, 0.04, 0], [1.14, 0.06, 1.08], shade(zinc, 0.8), m="metal"),
        part("torus", [0, 0.70, 0], [1.14, 0.06, 1.08], shade(zinc, 0.8), m="metal"),
        part("cyl", [0, 0.72, 0], [1.04, 0.02, 1.00], shade(zinc, 0.7), m="metal"),
        # the handle over the top, and the spout reaching out and up
        place("arch", [0, 0.71, -0.12], [0.80, 0.70, 0.6], zinc, anchor=[0, 0, 0],
              r=[0, PI / 2, 0], m="metal"),
        rod([0.40, 0.20, 0.30], [0.95, 0.62, 0.55], 0.12, zinc, m="metal"),
        part("cyl", [1.00, 0.66, 0.58], [0.26, 0.08, 0.26], zinc, [0.6, 0, -0.9], m="metal"),
    ]
    parts += _flower([1.08, 0.80, 0.66], 0.24, PINK, r=[-0.4, 0.6, 0], leaf=CARROT_TOP)
    parts += _flower([0.94, 0.88, 0.52], 0.20, BUTTER, r=[-0.6, 0.3, 0.3])
    return parts


@EA23.hat("dandelion_crown", "Dandelion Clocks",
          "A band of dandelions in every stage: gold flowers, closed buds and clocks "
          "all ready to blow. Every breath of wind tells the time.", "uncommon",
          hair="show")
def _():
    stem = "#6aa84a"
    parts = [ringband(-0.08, 0.10, stem)]
    for k in range(9):
        a = k * TAU / 9 + 0.2
        x, z = math.sin(a) * 0.95, math.cos(a) * 0.92
        h = 0.34 + 0.12 * (k % 3)
        top = [x * 1.04, -0.04 + h, z * 1.04]
        parts.append(rod([x, -0.06, z], top, 0.03, stem))
        if k % 3 == 0:
            parts.append(part("sph", top, [0.26, 0.26, 0.26], "#f6f8fc", a=0.7, m="glass"))
            parts.append(part("sph", top, [0.06, 0.06, 0.06], "#c9b06a"))
        elif k % 3 == 1:
            parts += _flower(top, 0.22, "#ffd23a", centre="#ffb000", r=[-0.5, a, 0])
        else:
            parts.append(place("teardrop", top, [0.10, 0.16, 0.10], "#7ab84a", anchor=[0, 0, 0]))
    return parts


@EA23.hat("bunny_hood", "Mascot Head",
          "The big furry rabbit head from the Easter parade, enormous eyes, buck teeth "
          "and a fixed, cheerful, unblinking smile. It is very hot in there. You can "
          "barely see out. Nobody can see in.", "legendary", hair="hide", face_cover=True)
def _():
    parts = [
        dome(-0.30, 0.74, BUNNY, decal="fur", wrap=True),
        part("cyl", [0, -0.78, 0], [1.88, 0.96, 1.82], BUNNY, decal="fur", wrap=True),
        part("sph", [0, -1.20, 0.14], [1.80, 0.30, 1.70], BUNNY, decal="fur", wrap=True),
        # the face: huge eyes, a pink nose, cheeks and teeth
        part("sph", [0.30, -0.42, 0.84], [0.40, 0.46, 0.20], WHITE),
        part("sph", [-0.30, -0.42, 0.84], [0.40, 0.46, 0.20], WHITE),
        part("sph", [0.30, -0.42, 0.93], [0.22, 0.28, 0.06], BLACK),
        part("sph", [-0.30, -0.42, 0.93], [0.22, 0.28, 0.06], BLACK),
        part("sph", [0.26, -0.36, 0.955], [0.06, 0.07, 0.02], WHITE),
        part("sph", [-0.34, -0.36, 0.955], [0.06, 0.07, 0.02], WHITE),
        part("sph", [0, -0.70, 0.95], [0.20, 0.14, 0.10], NOSE),
        part("sph", [0.22, -0.84, 0.90], [0.36, 0.28, 0.16], BUNNY),
        part("sph", [-0.22, -0.84, 0.90], [0.36, 0.28, 0.16], BUNNY),
        part("rbox", [0.06, -1.00, 0.92], [0.10, 0.14, 0.04], WHITE),
        part("rbox", [-0.06, -1.00, 0.92], [0.10, 0.14, 0.04], WHITE),
        part("sph", [0.48, -0.66, 0.80], [0.16, 0.10, 0.06], "#ffb0c8"),
        part("sph", [-0.48, -0.66, 0.80], [0.16, 0.10, 0.06], "#ffb0c8"),
        # ears, one a little bent
        place("bunnyear", [0.30, 0.40, 0.0], [1.10, 1.30, 2.4], BUNNY, anchor=[0, -0.5, 0],
              r=[0, 0, -0.10], decal="fur", wrap=True),
        place("bunnyear", [0.30, 0.40, 0.08], [0.70, 1.00, 1.2], NOSE, anchor=[0, -0.5, 0],
              r=[0, 0, -0.10]),
        place("bunnyear", [-0.30, 0.40, 0.0], [1.10, 1.30, 2.4], BUNNY, anchor=[0, -0.5, 0],
              r=[0.3, 0, 0.35], decal="fur", wrap=True),
        place("bunnyear", [-0.30, 0.40, 0.08], [0.70, 1.00, 1.2], NOSE, anchor=[0, -0.5, 0],
              r=[0.3, 0, 0.35]),
    ]
    return parts


@EA23.hat("carrot_cap", "Gardener's Flat Cap",
          "A brown corduroy flat cap with a carrot tucked in the band behind one ear, "
          "for later. There is always a later.", "rare")
def _():
    parts = [
        cap(-0.30, 0.14, CORD, grow=0.04, decal="ea_cord", wrap=True),
        part("rbox", [0, 0.17, 0.06], [1.56, 0.08, 1.40], CORD, [0.08, 0, 0], decal="ea_cord",
             wrap=True),
        place("peak", [0, -0.20, 0], [1.80, 1.0, 1.70], shade(CORD, 0.85), anchor=[0, 0, 0],
              decal="ea_cord", wrap=True),
        band(-0.24, 0.08, "#3a2a1a", grow=0.06),
    ]
    parts += _carrot([0.84, -0.06, -0.20], 0.56, r=[0.2, 0.0, -0.9])
    return parts


@EA23.back("carrot_quiver", "Carrot Quiver",
           "A twine-bound quiver of carrots, slung over the shoulder, fat end down, "
           "leaves up, and a packet of seed tied on for the long game.", "rare")
def _():
    parts = straps("#7a5426", 0.36, 0.12) + [
        part("cyl", [0, 0.20, -0.34], [0.62, 1.50, 0.56], "#b88a52", [0, 0, -0.45],
             decal="ea_wicker", wrap=True),
        part("torus", [0.21, 0.66, -0.34], [0.64, 0.08, 0.58], "#7a5426", [0, 0, -0.45]),
        part("torus", [-0.24, -0.30, -0.34], [0.64, 0.08, 0.58], "#7a5426", [0, 0, -0.45]),
        part("rbox", [-0.06, 0.12, -0.64], [0.32, 0.40, 0.02], "#ffffff", [0, 0, -0.45],
             decal="ea_seeds"),
    ]
    for dx, dz, k in ((0.0, 0.0, 0.70), (0.14, 0.10, 0.62), (-0.10, -0.08, 0.64), (0.10, -0.12, 0.56)):
        parts += _carrot([0.34 + dx, 0.98 + dx * 0.4, -0.34 + dz], k, r=[0, 0, PI - 0.45])
    return parts


@EA23.back("garden_tools", "Allotment Tools",
           "A spade and a rake, crossed on your back and lashed together with garden "
           "twine. You look like you mean business. The business is weeding.",
           "uncommon")
def _():
    wood, iron = "#b07a40", "#7a828c"
    parts = [
        rod([-0.70, -0.70, -0.24], [0.66, 1.30, -0.24], 0.10, wood),
        part("rbox", [0.78, 1.52, -0.24], [0.42, 0.10, 0.10], wood, [0, 0, 0.6]),
        place("shield", [-0.82, -0.94, -0.24], [0.44, 0.60, 0.6], iron, r=[0, 0, PI + 0.6],
              m="metal"),
        rod([0.70, -0.70, -0.30], [-0.66, 1.30, -0.30], 0.08, wood),
        part("rbox", [-0.72, 1.40, -0.30], [0.66, 0.08, 0.08], iron, [0, 0, -0.6], m="metal"),
        part("torus", [0, 0.30, -0.27], [0.24, 0.08, 0.24], "#c9a26a", [PI / 2, 0, 0],
             decal="ea_twine", wrap=True),
    ]
    for n in range(6):
        t = -0.24 + n * 0.10
        parts.append(rod([-0.72 + t * 0.83, 1.40 + t * 0.56, -0.30],
                         [-0.72 + t * 0.83 - 0.08, 1.40 + t * 0.56 - 0.16, -0.30], 0.03, iron,
                         m="metal"))
    return parts + straps("#7a5426")


@EA23.hairdo("cottontail_bun", "Cottontail Bun",
             "Soft brown hair swept back into a big white bun that looks exactly like a "
             "rabbit's tail, and wobbles like one.", "uncommon")
def _():
    c = "#a87a52"
    return [
        place("hairmid", [0, 0, 0], [1.03, 1.03, 1.03], c, anchor=[0, 0, 0], decal="strands",
              wrap=True),
        part("sph", [0, 0.20, -0.66], [0.52, 0.50, 0.42], BUNNY, decal="fur", wrap=True),
        part("sph", [0.12, 0.30, -0.70], [0.24, 0.22, 0.20], WHITE, decal="fur", wrap=True),
        part("sph", [-0.14, 0.12, -0.70], [0.22, 0.20, 0.18], WHITE, decal="fur", wrap=True),
    ]


@EA23.hairdo("hay_tousle", "Haystack",
             "Straw-blond hair, slept on in a hay loft, with a few stalks of the hay still "
             "in it. Somebody has been sleeping in the barn again.", "uncommon")
def _():
    c = "#e8c46a"
    parts = [place("hairmid", [0, 0, 0], [1.05, 1.05, 1.05], c, anchor=[0, 0, 0],
                   decal="strands", wrap=True)]
    for k, (x, z, a, b) in enumerate(((0.30, 0.20, 0.6, 0.2), (-0.20, -0.10, -0.8, 0.4),
                                      (0.06, -0.36, 0.2, -0.9), (-0.38, 0.22, -0.4, -0.3))):
        base = [x, 0.50, z]
        tip = [x + math.sin(a) * 0.50, 0.50 + 0.18 + 0.06 * k, z + math.sin(b) * 0.40]
        parts.append(rod(base, tip, 0.035, "#f2d27a"))
    for k in range(5):
        a = k * TAU / 5
        parts.append(place("teardrop", [math.sin(a) * 0.36, 0.48, math.cos(a) * 0.32 - 0.04],
                           [0.22, 0.28, 0.20], c if k % 2 else shade(c, 1.1), anchor=[0, 0.1, 0],
                           r=[math.cos(a) * 0.7, 0, -math.sin(a) * 0.7], decal="strands",
                           wrap=True))
    return parts


EA23.face("twitchy_nose", "Twitchy Nose",
          "A pink button nose, whiskers, two buck teeth, and eyes screwed up happy at the "
          "thought of somebody else's carrots.", [
              {"k": "arc", "x": -0.20, "y": -0.11, "r": 0.06, "a0": 0.55, "a1": 0.95, "w": 0.03,
               "c": "#16171b"},
              {"k": "arc", "x": 0.20, "y": -0.11, "r": 0.06, "a0": 0.55, "a1": 0.95, "w": 0.03,
               "c": "#16171b"},
              {"k": "poly", "pts": [[-0.06, -0.02], [0.06, -0.02], [0.0, 0.05]], "c": "#ff8fb0"},
              {"k": "line", "x1": -0.08, "y1": 0.02, "x2": -0.34, "y2": -0.02, "w": 0.012, "c": "#16171b"},
              {"k": "line", "x1": -0.08, "y1": 0.04, "x2": -0.34, "y2": 0.07, "w": 0.012, "c": "#16171b"},
              {"k": "line", "x1": 0.08, "y1": 0.02, "x2": 0.34, "y2": -0.02, "w": 0.012, "c": "#16171b"},
              {"k": "line", "x1": 0.08, "y1": 0.04, "x2": 0.34, "y2": 0.07, "w": 0.012, "c": "#16171b"},
              {"k": "arc", "x": -0.05, "y": 0.04, "r": 0.05, "a0": 0.05, "a1": 0.45, "w": 0.02,
               "c": "#16171b"},
              {"k": "arc", "x": 0.05, "y": 0.04, "r": 0.05, "a0": 0.05, "a1": 0.45, "w": 0.02,
               "c": "#16171b"},
              {"k": "poly", "pts": [[-0.045, 0.09], [0.0, 0.09], [0.0, 0.15], [-0.045, 0.15]],
               "c": "#fffaf0"},
              {"k": "poly", "pts": [[0.005, 0.09], [0.05, 0.09], [0.05, 0.15], [0.005, 0.15]],
               "c": "#fffaf0"},
          ], "uncommon")
EA23.face("carrot_crunch", "Carrot Crunch",
          "Both cheeks stuffed as full as they go, eyes wide, and a crumb of carrot on "
          "the chin. Do not ask how many. Many.", [
              {"k": "ellipse", "x": -0.20, "y": -0.15, "w": 0.09, "h": 0.12, "c": "#16171b"},
              {"k": "ellipse", "x": 0.20, "y": -0.15, "w": 0.09, "h": 0.12, "c": "#16171b"},
              {"k": "ellipse", "x": -0.185, "y": -0.18, "w": 0.03, "h": 0.035, "c": "#ffffff"},
              {"k": "ellipse", "x": 0.215, "y": -0.18, "w": 0.03, "h": 0.035, "c": "#ffffff"},
              {"k": "ellipse", "x": -0.30, "y": 0.10, "w": 0.22, "h": 0.18, "c": "#ffc9a0"},
              {"k": "ellipse", "x": 0.30, "y": 0.10, "w": 0.22, "h": 0.18, "c": "#ffc9a0"},
              {"k": "ellipse", "x": 0.0, "y": 0.12, "w": 0.10, "h": 0.06, "c": "#16171b"},
              {"k": "ellipse", "x": 0.06, "y": 0.26, "w": 0.04, "h": 0.03, "c": "#ff8a2a"},
              {"k": "ellipse", "x": -0.04, "y": 0.30, "w": 0.03, "h": 0.025, "c": "#ff8a2a"},
          ], "rare")
EA23.shirt("carrot_jumper", "Carrot Jumper",
           "A chunky cream knit with a carrot on the front, leaves and all, in case "
           "anybody was wondering where your loyalties lie.",
           {"torso": "#f6efe0", "arms": "#f6efe0", "decal": "ea_tee_carrot", "weave": "knit"},
           "uncommon")
EA23.pants("cord_dungarees", "Allotment Cords",
           "Brown corduroys with the knees gone, tucked into green wellies.",
           {"legs": "#7a5a3a", "weave": "ea_cord", "cuff": "#3f8a4a"})
EA23.belt("twine_belt", "Twine Belt",
          "Garden twine wound round and round for a belt, and two seed pouches hanging "
          "off it.",
          {"band": "#c9a26a", "buckle": "#7a5426", "width": 0.20, "weave": "ea_twine",
           "pouch": True})


@EA23.weapon("burrow_spade", "Burrower's Spade",
             "The spade the warren was dug with. Nobody hears a rabbit coming up behind "
             "them -- and the spade hits a great deal harder from behind. Every catch "
             "sends you scurrying off again.",
             {"kind": "melee", "damage": 28, "headshot": 1.0, "rpm": 84, "range": 10.0,
              "arc": 0.58, "sound": "swing", "knockback": 8, "backstab": 2.5,
              "on_kill": {"speed": [0.35, 3.0]}},
             [["+", "Two and a half times the damage from behind: 70 a swing"],
              ["+", "A kill sends you scurrying: 35% faster for 3 seconds"],
              ["-", "Only 28 damage from the front"],
              ["-", "Slower than a sword"]], rarity="legendary")
def _():
    wood, iron = "#b07a40", "#8a929c"
    return [
        rod([0, 0, -0.40], [0, 0, 1.00], 0.11, wood),
        part("rbox", [0, 0, -0.50], [0.36, 0.08, 0.10], wood),
        part("torus", [0, 0, -0.50], [0.30, 0.06, 0.20], wood, [PI / 2, 0, 0]),
        part("cyl", [0, 0, 1.04], [0.14, 0.16, 0.14], iron, [PI / 2, 0, 0], m="metal"),
        place("shield", [0, 0, 1.40], [0.50, 0.66, 0.6], iron, r=[0, -PI / 2, PI / 2],
              m="metal"),
        part("sph", [0.06, 0.03, 1.36], [0.10, 0.05, 0.10], EARTH),
    ]


@EA23.weapon("carrot_rocket", "Guided Carrot",
             "A carrot with a firework up its back end. It goes wherever you are looking, "
             "turning as you turn, so you can steer it round corners and over walls.",
             {"kind": "projectile", "projectile": "carrot", "damage": 55, "splash": 6.0,
              "splash_damage": 55, "rpm": 30, "mag": 1, "reload": 2.8, "speed": 44,
              "range": 300, "auto": False, "sound": "rocket", "recoil": 1.2, "reserve": 12,
              "gravity_scale": 0.0, "self_damage": 0.3, "knockback": 22,
              "guided": {"turn": 3.0}, "trail_colors": ["#ff8a2a", "#ffd36a"]},
             [["+", "Steers towards wherever you aim while it flies"],
              ["+", "A full rocket's blast: 55"],
              ["-", "Slow: you have to fly it all the way there"],
              ["-", "One at a time, and a long reload"]], rarity="legendary",
             proj=lambda: _carrot([0, 0, 0.40], 0.80, r=[-PI / 2, 0, 0]))
def _():
    parts = [part("cyl", [0, 0.02, 0.30], [0.30, 1.00, 0.30], "#3f8a4a", [PI / 2, 0, 0],
                  m="metal"),
             part("rbox", [0, -0.20, -0.04], [0.16, 0.40, 0.22], "#5a3a22", [-0.25, 0, 0]),
             part("torus", [0, 0.02, 0.80], [0.34, 0.06, 0.34], BRASS, [PI / 2, 0, 0], m="metal")]
    parts += _carrot([0, 0.02, 0.98], 0.50, r=[-PI / 2, 0, 0])
    return parts


@EA23.weapon("peashooter", "Peashooter",
             "Garden peas, a great many of them, very fast. Every one that lands puts a "
             "spring in your step and a little colour back in your cheeks -- eat your "
             "greens.",
             {"kind": "hitscan", "damage": 7, "headshot": 1.5, "rpm": 520, "mag": 40,
              "reload": 2.2, "range": 120, "auto": True, "sound": "smg", "recoil": 0.25,
              "spread": 2.2, "reserve": 200, "tracer": "#7ad84a",
              "lifesteal": 0.25, "speed_on_hit": [0.12, 2.0]},
             [["+", "Every hit heals you a quarter of the damage it does"],
              ["+", "...and quickens your step: 12% faster for 2 seconds"],
              ["-", "Peas: 7 damage a hit"],
              ["-", "Sprays wide"]], rarity="legendary")
def _():
    green = "#4f9e3a"
    parts = [
        part("cyl", [0, 0.04, 0.50], [0.18, 1.20, 0.18], green, [PI / 2, 0, 0]),
        part("sph", [0, 0.04, 1.12], [0.22, 0.22, 0.12], shade(green, 0.85)),
        part("rbox", [0, -0.18, -0.02], [0.16, 0.40, 0.22], "#5a3a22", [-0.25, 0, 0]),
        # the pod hopper on top, peas showing
        part("capsule", [0, 0.26, 0.30], [0.22, 0.60, 0.22], "#7ad84a", [PI / 2, 0, 0]),
    ]
    for n in range(4):
        parts.append(part("sph", [0.07, 0.30, 0.10 + n * 0.12], [0.09, 0.09, 0.09], "#a8f06a"))
    parts.append(place("leaf", [0, 0.30, -0.14], [0.6, 0.5, 1.0], green, r=[-1.2, 0, 0.4]))
    return parts


@EA23.gear("rabbits_foot", "Lucky Rabbit's Foot",
           "A white rabbit's foot on a chain, which belonged to a very lucky rabbit until "
           "fairly recently. Give it a squeeze: your ears prick up and your legs remember "
           "how to hop.",
           {"kind": "ability", "cooldown": 24, "sound": "magic",
            "ability": {"radar": {"radius": 70, "secs": 5.0, "color": "#ffb0c8"},
                        "jump": {"secs": 6.0, "gravity": 0.55}}},
           [["+", "Hear everything: every enemy within 70 studs is shown to your team for "
                  "5 seconds"],
            ["+", "Hop: lighter on your feet for 6 seconds"],
            ["-", "24 second cooldown"]], rarity="rare")
def _():
    return [
        part("capsule", [0, 0.20, 0.14], [0.24, 0.50, 0.22], BUNNY, [0.3, 0, 0], decal="fur",
             wrap=True),
        part("sph", [0, 0.40, 0.20], [0.28, 0.20, 0.30], BUNNY, decal="fur", wrap=True),
        part("cyl", [0, 0.04, 0.10], [0.20, 0.08, 0.20], GOLD, m="metal"),
        part("torus", [0, -0.06, 0.10], [0.14, 0.03, 0.14], GOLD, [PI / 2, 0, 0], m="metal"),
        part("sph", [0, 0.46, 0.34], [0.06, 0.04, 0.05], NOSE),
    ]


EA23.effect("carrot_patch", name="Carrot Patch", rate=2.4, life=[2.0, 2.8],
            size=[0.30, 0.42], grow=0.05, gravity=-0.3, spread=0.4, rise=[0.2, 0.5],
            blend="normal", spin=0.6, colors=["#ff8a2a", "#ff9f40", "#4f9e3a"],
            shapes=["carrot", "carrot", "flower"], radius=0.7, upright=True, wobble=0.3)
EA23.effect("hoppity", name="Hoppity", rate=1.8, life=[2.2, 3.0],
            size=[0.34, 0.44], grow=0.0, gravity=0.0, spread=0.15, rise=[0.05, 0.2],
            blend="normal", spin=0.0, colors=["#f6f2ee", "#e8dccc", "#ffb0c8"],
            shape="bunny", radius=0.9, orbit=1.8, upright=True, wobble=0.7)
EA23.opening(
    sky={"top": "#3a7ac8", "horizon": "#bfe4ff", "sun": [0.3, 0.8, 0.5], "clouds": 0.5,
         "tint": "#fff6d8"},
    ambient="#9ab87a", beam="#fff0a8", seep="carrot_patch", after="hoppity",
    burst=["#ff8a2a", "#5fb84a", "#ffffff", "#ff8fb0"],
    pieces=[{"shape": "carrot", "colors": ["#ff8a2a", "#ff9f40"], "blend": "normal"},
            {"shape": "bunny", "colors": ["#f6f2ee", "#e8dccc"], "blend": "normal"},
            {"shape": "flower", "colors": ["#ff8fb0", "#ffe58a", "#c7a8f0"], "blend": "normal"},
            {"shape": "spark", "colors": ["#fff3b0", "#ffffff"], "blend": "add"}],
    backdrop="ea_burrow", title_wait="Something is digging...",
    title_shake="Something wants out of the burrow...")
EA23.award("Bunny Burrow", ["Lawn Lounger", "Hole Spotter", "Carrot Grower", "Warren Warden",
                            "Head Gardener", "King of the Burrow"],
           "Opened Burrow Mounds during the Bunny Burrow, Easter 2023.", "em_bunny", "egg")
EA23.bundle("pair", "Mound and Key", 1, 1050, "One Burrow Mound, one Carrot Key.")
EA23.bundle("warren", "The Whole Warren", 3, 3000, "Three mounds, three keys. Saves 300.")

# ============================================================ 2024
EA24_CHICK = "#ffd23a"
EA24_BEAK = "#ff9a1a"
EA24_HEN = "#b5562a"
EA24_HEN_DARK = "#7a3216"
EA24_COMB = "#e0302a"
EA24_GOOSE = "#f6f4ee"
EA24_GOSLING = "#c9c07c"
EA24_STRAW = "#e8c468"
EA24_BARN = "#b8322a"
EA24_TRIM = "#f6f2e8"
EA24_ROOF = "#4a4f58"
EA24_WOOD = "#b0703a"
EA24_WOOD_DARK = "#6a3e1e"
EA24_ALU = "#c9ced6"
EA24_LAMP = "#ff5a24"
EA24_GLASS = "#e8f6ff"
EA24_SHELL = "#f6ecda"
EA24_BROWN_EGG = "#dcae7c"
EA24_DUCK_EGG = "#c8e6da"
EA24_BURLAP = "#c8a56a"


def _ea24_turn(parts, at, yaw=0.0, k=1.0, **kw):
    """A little model authored round its own origin and looking along +Z,
    scaled by ``k``, turned by ``yaw`` about the upright and moved to ``at``.
    A turn about the upright composes with any part's own turn just by
    adding to its yaw, so -- unlike ``at_frame`` -- tilted parts come too."""
    c, s = math.cos(yaw), math.sin(yaw)
    out = []
    for p in parts:
        x, y, z = (v * k for v in p["p"])
        q = dict(p)
        q["p"] = [round(at[0] + x * c + z * s, 4), round(at[1] + y, 4),
                  round(at[2] - x * s + z * c, 4)]
        q["s"] = [round(v * k, 4) for v in p["s"]]
        if yaw:
            r = list(p.get("r") or [0.0, 0.0, 0.0])
            q["r"] = [round(r[0], 4), round(r[1] + yaw, 4), round(r[2], 4)]
        q.update(kw)
        out.append(q)
    return out


def _ea24_on_dome(d, y, ang, out=0.0):
    """The point at height ``y`` on the outside of a crown made by ``dome``
    (a hemi or a capcrown part), ``ang`` round from the front, stood ``out``
    off its surface."""
    base = d["p"][1] - d["s"][1] / 2
    f = min(1.0, max(0.0, (y - base) / d["s"][1]))
    if d["t"] == "capcrown":
        band = 0.10 / 0.52
        r = 1.0 if f <= band else math.sqrt(max(0.0, 1 - ((f - band) / (1 - band)) ** 2))
    else:
        r = math.sqrt(max(0.0, 1 - f * f))
    return [math.sin(ang) * (d["s"][0] / 2 * r + out), y,
            d["p"][2] + math.cos(ang) * (d["s"][2] / 2 * r + out)]


def _ea24_chick(at=(0, 0, 0), k=1.0, yaw=0.0, c=EA24_CHICK, eyes="open", **kw):
    """A chick sat down, about ``k`` tall: feet at ``at``, looking along
    ``yaw``, all down and no sense."""
    lo = shade(c, 0.86)
    parts = [
        part("sph", [0, 0.36, -0.02], [0.74, 0.70, 0.80], c, decal="ea24_down", wrap=True),
        part("sph", [0, 0.80, 0.10], [0.54, 0.52, 0.52], c, decal="ea24_down", wrap=True),
        place("cone", [0, 0.78, 0.42], [0.15, 0.17, 0.15], EA24_BEAK, r=[PI / 2, 0, 0]),
        part("sph", [0.36, 0.38, -0.04], [0.14, 0.36, 0.46], lo, [0, 0, -0.25]),
        part("sph", [-0.36, 0.38, -0.04], [0.14, 0.36, 0.46], lo, [0, 0, 0.25]),
        # a tuft of fluff on top, and a stub of a tail
        place("teardrop", [0.0, 1.02, 0.10], [0.09, 0.16, 0.09], c, anchor=[0, 0, 0], r=[0.2, 0, 0]),
        place("teardrop", [0.05, 1.01, 0.06], [0.07, 0.13, 0.07], c, anchor=[0, 0, 0],
              r=[-0.1, 0, -0.5]),
        place("teardrop", [-0.05, 1.01, 0.07], [0.07, 0.12, 0.07], c, anchor=[0, 0, 0],
              r=[-0.1, 0, 0.5]),
        place("teardrop", [0, 0.40, -0.38], [0.16, 0.22, 0.12], lo, anchor=[0, 0, 0], r=[-1.2, 0, 0]),
        part("rbox", [0.13, 0.025, 0.20], [0.12, 0.05, 0.22], EA24_BEAK),
        part("rbox", [-0.13, 0.025, 0.20], [0.12, 0.05, 0.22], EA24_BEAK),
    ]
    for s in (1, -1):
        if eyes == "open":
            parts += [part("sph", [0.12 * s, 0.86, 0.33], [0.08, 0.10, 0.05], BLACK),
                      part("sph", [0.105 * s, 0.885, 0.355], [0.03, 0.03, 0.015], WHITE)]
        else:
            parts.append(part("rbox", [0.12 * s, 0.85, 0.345], [0.10, 0.025, 0.02], BLACK))
    return _ea24_turn(parts, at, yaw, k, **kw)


def _ea24_hen(at=(0, 0, 0), k=1.0, yaw=0.0, c=EA24_HEN, wing=EA24_HEN_DARK, **kw):
    """A broody hen sat down on her eggs (no legs to be seen), about 1.4
    ``k`` tall: russet scallops, a red comb and a look in her eye."""
    parts = [
        part("sph", [0, 0.46, -0.06], [1.00, 0.86, 1.20], c, decal="ea24_plumage", wrap=True),
        part("sph", [0, 0.60, 0.30], [0.78, 0.74, 0.62], c, decal="ea24_plumage", wrap=True),
        part("sph", [0, 1.02, 0.40], [0.44, 0.50, 0.44], c, decal="ea24_plumage", wrap=True),
        # comb, wattle, beak
        part("sph", [0, 1.29, 0.52], [0.08, 0.16, 0.12], EA24_COMB),
        part("sph", [0, 1.32, 0.42], [0.08, 0.18, 0.12], EA24_COMB),
        part("sph", [0, 1.29, 0.32], [0.08, 0.15, 0.11], EA24_COMB),
        place("teardrop", [0, 0.90, 0.62], [0.10, 0.16, 0.08], EA24_COMB, r=[PI, 0, 0]),
        place("cone", [0, 0.99, 0.69], [0.13, 0.18, 0.12], "#f2b23a", r=[PI / 2 + 0.25, 0, 0]),
        # the wings folded at her sides, and the tail fanned up behind
        part("sph", [0.47, 0.50, -0.10], [0.22, 0.58, 0.88], wing, [0.1, 0, -0.12],
             decal="ea24_plumage", wrap=True),
        part("sph", [-0.47, 0.50, -0.10], [0.22, 0.58, 0.88], wing, [0.1, 0, 0.12],
             decal="ea24_plumage", wrap=True),
    ]
    for s in (1, -1):
        parts += [part("sph", [0.15 * s, 1.08, 0.56], [0.09, 0.10, 0.05], "#f2a62a"),
                  part("sph", [0.16 * s, 1.08, 0.58], [0.05, 0.06, 0.03], BLACK)]
    for x, roll, tone in ((0.13, -0.40, 1.0), (0.0, 0.0, 0.8), (-0.13, 0.40, 1.0)):
        parts.append(place("feather", [x, 0.66, -0.58], [2.0, 0.82, 2.0], shade(wing, tone),
                           anchor=[0, -0.5, 0], r=[-0.75, 0, roll]))
    return _ea24_turn(parts, at, yaw, k, **kw)


def _ea24_egg(at, w, c, speckle=False, r=None, **kw):
    """An egg ``w`` wide stood on ``at`` (turned as a whole by ``r``):
    a hen's, a duck's or a goose's, plain or speckled."""
    k = w / EGG_W
    egg = place("egg", [0, 0, 0], [k, k, k], c, anchor=[0, 0, 0],
                decal="ea24_speckle" if speckle else None, wrap=True if speckle else None)
    out = at_frame([egg], at, r)
    for p in out:
        p.update(kw)
    return out


EA24 = Event(
    "easter_2024", "easter", 2024, "ea24",
    name="The Great Hatch", title="The Great Hatch",
    blurb="Easter 2024 somebody found the barn's old incubator, plugged it back in, "
          "filled it with every egg left over from the hunt and forgot all about it. "
          "Twenty-one days later the whole barn started peeping. Chicks, ducklings, "
          "three goslings and one thing nobody can identify now run the farm, and they "
          "have very firm views on the pecking order.",
    tagline="Keep them warm. Keep them fed. Keep your ankles moving.",
    starts="2024-03-22", ends="2024-04-09",
    colors={"accent": "#ffc93a", "deep": "#3a2412", "glow": "#ff9a3a"},
    family_effects=["sunbeam", "candlelight_vigil", "starstruck"],
    hero_effect="hatching_hour", stencil="stencil_ea24")


@EA24.crate_model("Incubator",
                  "The barn's old incubator: a varnished cabinet on turned legs, a glass "
                  "dome of eggs on top with the heat lamp glowing in it, a paraffin heater "
                  "ticking at its side and the dial stuck on ninety-nine and a half. Some "
                  "of the eggs have started without you. Holds The Great Hatch set. Needs "
                  "an Egg Tooth Key.",
                  hinge=[0, 0.21, -0.48], keyhole=[0, -0.15, 0.50])
def _():
    tray_y = 0.22
    parts = [
        # the cabinet on its legs
        part("rbox", [0, -0.17, 0], [1.36, 0.62, 0.90], EA24_WOOD, decal="ea24_cabinet", wrap=True),
        part("rbox", [0, -0.50, 0], [1.30, 0.08, 0.84], EA24_WOOD_DARK),
        part("rbox", [0, 0.17, 0], [1.44, 0.08, 0.98], EA24_WOOD_DARK),
        # the front: a maker's plate, the lock, the dial, a vent and the water drawer
        part("box", [0, 0.05, 0.452], [0.74, 0.12, 0.02], "#000000", decal="ea24_incplate", a=-1),
        part("rbox", [0, -0.15, 0.47], [0.28, 0.28, 0.06], BRASS, m="metal", decal="keyhole", lock=1),
        part("disc", [-0.43, -0.12, 0.465], [0.30, 0.30, 0.05], "#f6f0dc", decal="ea24_dial"),
        part("torus", [-0.43, -0.12, 0.47], [0.34, 0.34, 0.34], BRASS, [PI / 2, 0, 0], m="metal"),
        part("rbox", [0, -0.38, 0.455], [0.86, 0.13, 0.03], shade(EA24_WOOD, 0.85)),
        part("sph", [0, -0.38, 0.48], [0.07, 0.07, 0.05], BRASS, m="metal"),
        # the stencil, painted on the back
        part("box", [0, -0.17, -0.455], [0.62, 0.50, 0.02], "#000000", [0, PI, 0],
             decal="stencil_ea24", a=-1),
        # the tray of eggs under the dome, warm straw under them, and the
        # light of the lamp on it
        part("rbox", [0, tray_y - 0.01, 0], [1.20, 0.03, 0.78], SILVER, m="metal"),
        part("cyl", [0, tray_y + 0.005, 0], [1.16, 0.02, 0.74], "#ffb04a", m="neon", a=0.6),
        # the glass dome (the lid): a brass ring at its foot, two straps over
        # it, a knob, and the heat lamp hung inside
        place("hemi", [0, tray_y - 0.01, 0], [1.40, 1.20, 1.00], EA24_GLASS, anchor=[0, 0, 0],
              m="glass", a=0.30, lid=1),
        place("ring", [0, tray_y - 0.02, 0], [1.44, 0.4, 1.04], BRASS, anchor=[0, 0, 0], m="metal",
              lid=1),
        place("arch", [0, tray_y + 0.02, 0], [1.26, 1.06, 0.30], BRASS, anchor=[0, 0, 0], m="metal",
              lid=1),
        place("arch", [0, tray_y + 0.02, 0], [0.90, 1.06, 0.30], BRASS, anchor=[0, 0, 0],
              r=[0, PI / 2, 0], m="metal", lid=1),
        part("sph", [0, tray_y + 0.62, 0], [0.12, 0.10, 0.12], BRASS, m="metal", lid=1),
        place("bell", [0, tray_y + 0.40, 0], [0.32, 0.17, 0.32], EA24_ALU, anchor=[0, 0, 0],
              m="metal", lid=1),
        part("sph", [0, tray_y + 0.40, 0], [0.17, 0.15, 0.17], EA24_LAMP, m="neon", lid=1),
        # the paraffin heater on its bracket at the side, and its chimney
        part("rbox", [0.80, -0.22, 0], [0.24, 0.40, 0.38], "#8a929a", m="metal",
             decal="rivets", wrap=True),
        part("rbox", [0.925, -0.26, 0], [0.02, 0.14, 0.18], "#ff9a3a", m="neon"),
        part("rbox", [0.70, -0.40, 0], [0.12, 0.06, 0.30], "#5a5f66", m="metal"),
        part("cyl", [0.80, 0.24, 0], [0.11, 0.56, 0.11], "#6a7078", m="metal"),
        place("cone", [0.80, 0.58, 0], [0.22, 0.12, 0.22], "#5a5f66", m="metal"),
        part("sph", [0.84, 0.74, 0.02], [0.18, 0.14, 0.18], "#eef2f6", a=0.55),
        part("sph", [0.90, 0.88, 0.0], [0.13, 0.10, 0.13], "#eef2f6", a=0.4),
        # the egg-turner's crank on the other side
        part("cyl", [-0.72, -0.10, 0], [0.08, 0.10, 0.08], BRASS, [0, 0, PI / 2], m="metal"),
        part("rbox", [-0.78, -0.18, 0], [0.04, 0.24, 0.06], BRASS, m="metal"),
        part("cyl", [-0.83, -0.27, 0], [0.07, 0.12, 0.07], EA24_WOOD_DARK, [0, 0, PI / 2]),
    ]
    # turned legs and their feet
    for sx in (1, -1):
        for sz in (1, -1):
            parts += [part("cyl", [0.56 * sx, -0.70, 0.32 * sz], [0.12, 0.36, 0.12], EA24_WOOD_DARK),
                      part("sph", [0.56 * sx, -0.62, 0.32 * sz], [0.16, 0.10, 0.16], EA24_WOOD),
                      part("sph", [0.56 * sx, -0.86, 0.32 * sz], [0.15, 0.08, 0.15], EA24_WOOD_DARK)]
    # the eggs: hens', a duck's, a goose's -- two of them hatching, one pipping
    for x, z, c, w, speck in ((-0.40, 0.17, EA24_SHELL, 0.24, False),
                              (0.14, 0.17, EA24_DUCK_EGG, 0.24, False),
                              (0.40, 0.17, EA24_BROWN_EGG, 0.24, True),
                              (-0.40, -0.15, WHITE, 0.30, False),
                              (-0.13, -0.15, EA24_BROWN_EGG, 0.24, True),
                              (0.40, -0.15, EA24_SHELL, 0.23, True)):
        parts += _ea24_egg([x, tray_y, z], w, c, speck)
    # pipping: a beak through a hole in the brown egg at the front
    parts += [part("sph", [0.40, tray_y + 0.20, 0.285], [0.08, 0.07, 0.03], "#3a2a1a"),
              place("cone", [0.40, tray_y + 0.20, 0.31], [0.05, 0.06, 0.05], EA24_BEAK,
                    r=[PI / 2, 0, 0])]
    # hatching: a chick and a gosling out through the tops of theirs
    for x, z, c, shell, yaw in ((-0.14, 0.17, EA24_CHICK, EA24_SHELL, 0.3),
                                (0.13, -0.15, EA24_GOSLING, EA24_DUCK_EGG, -0.4)):
        k = 0.26 / EGG_W
        parts.append(place("crackedshell", [x, tray_y, z], [k, k, k], shell, anchor=[0, 0, 0]))
        parts += [p for p in _ea24_chick([x, tray_y + 0.02, z], 0.36, yaw, c)
                  if p["p"][1] > tray_y + 0.18]
        parts.append(place("ea_eggtop", [x + 0.17, tray_y, z + 0.02], [k, k, k], shell,
                           anchor=[0, 0.69, 0], r=[0.3, 0.5, 1.6]))
    # and one already out, sat on top of the dome where it is warm
    parts += _ea24_chick([0.22, tray_y + 0.52, 0.10], 0.30, 0.5, lid=1)
    return parts


@EA24.key_model("Egg Tooth Key",
                "A brass key with a chick for a bow, still sat in the bottom of its "
                "shell, and the bit cut with an egg tooth -- the little point a chick "
                "chips its way out with. Opens one Incubator, tap by tap.",
                shoulder=-0.30)
def _():
    k = 0.40 / EGG_W
    parts = [
        place("crackedshell", [-0.62, -0.24, 0], [k, k, k], EA24_SHELL, anchor=[0, 0, 0]),
        part("cyl", [0.06, 0, 0], [0.09, 0.92, 0.09], BRASS, [0, 0, PI / 2], m="metal"),
        part("torus", [-0.30, 0, 0], [0.20, 0.20, 0.20], GOLD_DARK, [0, 0, PI / 2], m="metal"),
        part("rbox", [-0.40, 0.0, 0], [0.12, 0.10, 0.08], BRASS, m="metal"),
        # the bit: two wards and the egg tooth on the tip
        part("rbox", [0.34, -0.11, 0], [0.07, 0.16, 0.07], BRASS, m="metal"),
        part("rbox", [0.44, -0.14, 0], [0.07, 0.22, 0.07], BRASS, m="metal"),
        place("tri", [0.56, 0.0, 0], [0.12, 0.14, 0.6], "#fff8e8", r=[0, 0, -PI / 2]),
    ]
    parts += [p for p in _ea24_chick([-0.62, -0.20, 0], 0.50, 0.0) if p["p"][1] > -0.04]
    return parts


@EA24.hat("broody_hen", "Broody Hen",
          "She has sat down on your head, and she is not getting up until everything "
          "under her has hatched. You are what is under her. Her chicks peep out from "
          "under her wings to see how you are getting on.", "legendary")
def _():
    parts = [
        cap(-0.26, 0.12, EA24_STRAW, grow=0.06, decal="ea_straw", wrap=True),
        ringband(-0.20, 0.20, shade(EA24_STRAW, 0.85), margin=0.07, decal="ea_straw", wrap=True),
    ]
    parts += _ea24_hen([0, 0.06, -0.02], 0.92)
    # straws poking out of the nest all round
    parts += around(14, 0.86, 0.06, lambda a, x, z: rod(
        [x * 0.98, 0.04, z * 0.95], [x * 1.18, 0.14 + 0.05 * math.sin(a * 3), z * 1.12], 0.03,
        shade(EA24_STRAW, 1.05 if int(round(a * 14 / TAU)) % 2 else 0.85)), start=0.1)
    # her chicks, peeping out from under her wings
    parts += _ea24_chick([0.50, 0.10, 0.34], 0.36, 0.4)
    parts += _ea24_chick([-0.50, 0.10, 0.36], 0.33, -0.5)
    return parts


@EA24.hat("eggshell", "Just Hatched",
          "The top of the shell you came out of, still on your head where it landed. "
          "Everybody else took theirs off. Everybody else did not think it was a good "
          "look.", "uncommon")
def _():
    k = 1.62
    tilt = [0.10, 0.0, -0.22]
    parts = [place("ea_eggtop", [0.02, 0.06, 0], [k, k, k], EA24_SHELL, anchor=[0, 0.69, 0],
                   r=tilt, decal="ea24_speckle", wrap=True)]
    # a wisp of down and a stalk of straw stuck to it
    tip = rotate([0, (1.30 - 0.69) * k, 0], tilt)
    parts += [place("feather", [0.02 + tip[0] - 0.10, 0.06 + tip[1] - 0.20, 0.32],
                    [0.9, 0.36, 1.0], "#fff8de", r=[-0.5, 0.2, 0.9], decal="ea24_down"),
              rod([-0.46, 0.34, 0.50], [0.10, 0.56, 0.56], 0.03, EA24_STRAW)]
    return parts


@EA24.hat("brooder_lamp", "Brooder Lamp",
          "The heat lamp off the incubator, worn like a lampshade at a party, the "
          "bulb still on and a chick asleep on top because it is the warmest place in "
          "the barn. The plug is somewhere down your back.", "rare")
def _():
    shade_ = dome(-0.32, 0.76, EA24_ALU, m="metal", decal="ea24_reflector", wrap=True)
    top = shade_["p"][1] + shade_["s"][1] / 2
    rim = shade_["s"][0] / 2
    parts = [
        shade_,
        place("ring", [0, -0.35, 0], [rim * 2 + 0.10, 0.45, rim * 2 * 0.97 + 0.10],
              shade(EA24_ALU, 0.8), anchor=[0, 0, 0], m="metal"),
        part("torus", [0, -0.34, 0], [rim * 2 - 0.04, 0.30, (rim * 2 - 0.04) * 0.97], EA24_LAMP,
             m="neon"),
        # the socket, its switch, and the chain it hangs by
        part("cyl", [0, top + 0.08, 0], [0.32, 0.20, 0.32], "#2a2420"),
        part("cyl", [0, top + 0.20, 0], [0.22, 0.08, 0.22], "#2a2420"),
        part("sph", [0.17, top + 0.10, 0.04], [0.06, 0.06, 0.06], "#ff3a2a", m="neon"),
    ]
    for n in range(3):
        parts.append(part("torus", [0, top + 0.32 + n * 0.12, 0], [0.12, 0.10, 0.16], SILVER,
                          [PI / 2, (n % 2) * PI / 2, 0], m="metal"))
    parts.append(place("hook", [0, top + 0.66, 0], [0.30, 0.30, 0.30], SILVER, r=[0, PI / 2, 0],
                       m="metal"))
    # the cord, down over the back of the shade to the plug
    cord = [[0.04, top + 0.06, -0.16]]
    for y in (top - 0.08, top - 0.30, 0.0, -0.22):
        cord.append(_ea24_on_dome(shade_, y, PI - 0.15, 0.04))
    cord += [[cord[-1][0], -0.62, cord[-1][2] - 0.02], [cord[-1][0] + 0.02, -0.86, cord[-1][2] - 0.04]]
    for a, b in zip(cord, cord[1:]):
        parts.append(rod(a, b, 0.05, "#2a2420"))
    end = cord[-1]
    parts += [part("rbox", [end[0], end[1] - 0.10, end[2]], [0.14, 0.16, 0.10], "#2a2420"),
              part("rbox", [end[0] - 0.035, end[1] - 0.22, end[2]], [0.02, 0.10, 0.03], BRASS, m="metal"),
              part("rbox", [end[0] + 0.035, end[1] - 0.22, end[2]], [0.02, 0.10, 0.03], BRASS, m="metal")]
    # a thermometer clipped to the rim, and the sleeper on top
    side = _ea24_on_dome(shade_, -0.30, 1.30, 0.03)
    parts += [part("rbox", [side[0], -0.46, side[2]], [0.03, 0.34, 0.09], WHITE, [0, 1.30, 0]),
              part("rbox", [side[0] + 0.01, -0.44, side[2]], [0.02, 0.26, 0.02], "#e0302a", [0, 1.30, 0]),
              part("sph", [side[0] + 0.01, -0.61, side[2]], [0.06, 0.06, 0.06], "#e0302a")]
    parts += _ea24_chick(_ea24_on_dome(shade_, top - 0.06, -0.9, -0.05), 0.34, 0.6, eyes="shut")
    return parts


@EA24.hat("puddle_duck", "Puddle Duck Cap",
          "A white cap with an orange bill for a peak, two button eyes and the drake's "
          "curl on top. Anyone who meets you will say 'quack'. Everyone who meets you "
          "will say 'quack'.", "uncommon")
def _():
    crown = dome(-0.30, 0.84, EA24_GOOSE, t="capcrown", decal="felt", wrap=True)
    top = crown["p"][1] + crown["s"][1] / 2
    parts = [
        crown,
        ringband(-0.22, 0.10, shade(EA24_GOOSE, 0.88), margin=0.05),
        # the bill: a broad flat peak and its rounded tip, nostrils on top
        place("peak", [0, -0.20, 0.0], [1.20, 1.8, 1.90], EA24_BEAK, anchor=[0, 0, 0]),
        part("sph", [0, -0.25, 1.30], [0.92, 0.12, 0.30], EA24_BEAK),
        part("rbox", [0.10, -0.15, 0.98], [0.06, 0.02, 0.10], "#b85a10"),
        part("rbox", [-0.10, -0.15, 0.98], [0.06, 0.02, 0.10], "#b85a10"),
        part("cyl", [0, top + 0.01, 0], [0.12, 0.03, 0.12], shade(EA24_GOOSE, 0.85)),
    ]
    for s in (1, -1):
        eye = _ea24_on_dome(crown, 0.08, 0.36 * s, 0.0)
        parts += [part("sph", eye, [0.26, 0.28, 0.12], WHITE, [0, 0.36 * s, 0]),
                  part("sph", [eye[0] + math.sin(0.36 * s) * 0.05, eye[1] - 0.02,
                               eye[2] + math.cos(0.36 * s) * 0.05],
                       [0.12, 0.14, 0.06], BLACK, [0, 0.36 * s, 0])]
    # the drake's curl
    parts.append(place("spiral", [0, top - 0.02, -0.10], [0.22, 0.30, 0.22], "#3a8a5a",
                       anchor=[0, 0, 0], r=[-0.3, 0, 0]))
    return parts


@EA24.hat("barn_roof", "Weathervane Barn",
          "The big red barn, gambrel roof, X-braced door and all, with the hay still "
          "in the loft and the rooster on the weathervane pointing whichever way the "
          "wind is blowing. It is blowing out of the barn, mostly.", "legendary")
def _():
    wall, eave, knee, ridge = 0.30, [0.90, 0.30], [0.64, 0.66], [0.0, 0.86]
    depth = 1.80
    parts = [part("rbox", [0, 0.0, 0], [1.74, 0.62, 1.62], EA24_BARN, decal="ea24_barnboards",
                  wrap=True)]
    # white corner boards
    parts += [part("rbox", [0.87 * sx, 0.0, 0.81 * sz], [0.08, 0.64, 0.08], EA24_TRIM)
              for sx in (1, -1) for sz in (1, -1)]

    def slab(a, b, side):
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = math.hypot(dx, dy)
        rz = math.atan2(-dx, dy)
        n = [math.cos(rz), math.sin(rz)]
        mid = [(a[0] + b[0]) / 2 + n[0] * 0.035, (a[1] + b[1]) / 2 + n[1] * 0.035]
        return part("rbox", [mid[0] * side, mid[1], 0], [0.07, length + 0.06, depth], EA24_ROOF,
                    [0, 0, rz * side], decal="ea24_shingles", wrap=True)
    for side in (1, -1):
        parts += [slab(eave, knee, side), slab(knee, ridge, side)]
    # the gable ends: the barn red up to the roof, a hayloft door in each
    for sz in (1, -1):
        z = 0.80 * sz
        parts += [
            part("rbox", [0, 0.39, z], [1.54, 0.18, 0.04], EA24_BARN, decal="ea24_barnboards"),
            part("rbox", [0, 0.57, z], [1.28, 0.18, 0.04], EA24_BARN, decal="ea24_barnboards"),
            place("tri", [0, 0.66, z], [1.28, 0.20 / 0.9, 0.34], EA24_BARN, anchor=[0, -0.40, 0]),
        ]
    # the big door, X-braced in white
    f = 0.82
    parts += [
        part("rbox", [0, -0.05, f], [0.60, 0.50, 0.02], "#8a2018", decal="ea24_barnboards"),
        part("rbox", [0, 0.21, f + 0.01], [0.66, 0.05, 0.03], EA24_TRIM),
        part("rbox", [0, -0.30, f + 0.01], [0.66, 0.05, 0.03], EA24_TRIM),
        part("rbox", [0.31, -0.05, f + 0.01], [0.05, 0.54, 0.03], EA24_TRIM),
        part("rbox", [-0.31, -0.05, f + 0.01], [0.05, 0.54, 0.03], EA24_TRIM),
        rod([-0.28, -0.28, f + 0.02], [0.28, 0.19, f + 0.02], 0.045, EA24_TRIM, t="rbox"),
        rod([0.28, -0.28, f + 0.02], [-0.28, 0.19, f + 0.02], 0.045, EA24_TRIM, t="rbox"),
        # the hayloft, and the hay coming out of it
        part("rbox", [0, 0.56, f], [0.30, 0.24, 0.02], "#3a1a10"),
        part("rbox", [0, 0.56, f + 0.005], [0.36, 0.30, 0.01], EA24_TRIM),
    ]
    for n, (x, lean) in enumerate(((-0.08, 0.4), (0.0, 0.0), (0.08, -0.4), (0.04, 0.2))):
        parts.append(place("teardrop", [x, 0.50, f + 0.03], [0.06, 0.18, 0.05],
                           shade(EA24_STRAW, 1.0 if n % 2 else 0.85), anchor=[0, 1.0, 0],
                           r=[PI - 0.5, 0, lean]))
    # the cupola on the ridge, and the weathervane on top of it
    parts += [
        part("rbox", [0, 0.98, 0], [0.30, 0.24, 0.30], EA24_TRIM),
        part("rbox", [0, 0.98, 0.152], [0.18, 0.14, 0.01], "#3a1a10"),
        place("cone", [0, 1.16, 0], [0.44, 0.18, 0.44], EA24_ROOF),
        part("cyl", [0, 1.42, 0], [0.03, 0.40, 0.03], IRON, m="metal"),
        part("cyl", [0, 1.40, 0], [0.025, 0.40, 0.025], IRON, [0, 0, PI / 2], m="metal"),
        part("cyl", [0, 1.40, 0], [0.025, 0.40, 0.025], IRON, [PI / 2, 0, 0], m="metal"),
    ]
    parts += [part("sph", p, [0.05, 0.05, 0.05], GOLD, m="metal")
              for p in ([0.20, 1.40, 0], [-0.20, 1.40, 0], [0, 1.40, 0.20], [0, 1.40, -0.20])]
    # the rooster, cut from sheet iron, crowing into the wind
    vane = [
        part("sph", [0.0, 1.70, 0], [0.30, 0.18, 0.04], BLACK, [0, 0, 0.25]),
        part("sph", [0.15, 1.82, 0], [0.11, 0.12, 0.04], BLACK),
        place("tri", [0.24, 1.83, 0], [0.08, 0.06, 0.3], BLACK, r=[0, 0, -PI / 2]),
        place("tri", [0.15, 1.91, 0], [0.10, 0.07, 0.3], "#c42a22"),
        place("fan", [-0.14, 1.78, 0], [0.30, 0.50, 0.6], BLACK, anchor=[0, 0, 0], r=[0, 0, 0.6]),
        part("rbox", [0.0, 1.61, 0], [0.025, 0.12, 0.03], BLACK),
        place("arrow", [0.0, 1.55, 0], [0.30, 0.56, 0.4], BLACK, r=[0, 0, -PI / 2]),
    ]
    return parts + vane


@EA24.hat("rooster_comb", "Cock-a-Doodle Crest",
          "A great red comb on an elastic band and a wattle clipped on either side. "
          "Whoever wears it is up first. Every morning. Loudly. Sorry.", "uncommon",
          hair="show")
def _():
    band_c = "#c42a22"
    parts = [
        part("rbox", [0, 0.035, 0], [1.00, 0.07, 0.16], band_c),
        *sides(lambda s: [
            part("rbox", [0.62 * s, -0.035, 0], [0.34, 0.07, 0.16], band_c, [0, 0, 0.55 * s]),
            part("rbox", [0.775 * s, -0.40, 0], [0.07, 0.58, 0.16], band_c),
            place("teardrop", [0.80 * s, -0.66, 0.02], [0.16, 0.30, 0.10], EA24_COMB,
                  anchor=[0, 1.0, 0], r=[PI, 0, 0.12 * s]),
        ]),
        part("capsule", [0, 0.11, 0], [0.18, 0.88, 0.18], EA24_COMB, [PI / 2, 0, 0]),
    ]
    # the comb: five lobes, the tallest in the middle, leaning back a touch
    for z, h, w in ((0.36, 0.28, 0.24), (0.18, 0.40, 0.28), (0.0, 0.48, 0.30),
                    (-0.18, 0.42, 0.28), (-0.36, 0.32, 0.24)):
        parts.append(part("sph", [0, 0.10 + h / 2, z - 0.04 * h], [0.14, h, w],
                          EA24_COMB if int(round(z * 10)) % 2 == 0 else shade(EA24_COMB, 1.1),
                          [-0.15, 0, 0], m="glass"))
    return parts


@EA24.hat("feed_sack", "Chick Crumb Sack",
          "An empty sack of chick crumb, turned up at the edge and tied at the top. "
          "It still smells of breakfast. Every chick in the barn knows it, and follows "
          "it, everywhere.", "uncommon")
def _():
    parts = [
        cap(-0.30, 0.22, EA24_BURLAP, grow=0.06, decal="ea24_burlap", wrap=True),
        ringband(-0.22, 0.16, shade(EA24_BURLAP, 0.9), margin=0.08, decal="ea24_burlap", wrap=True),
        part("box", [0.0, 0.0, 0.825], [0.70, 0.36, 0.02], "#000000", decal="ea24_feedlabel", a=-1),
    ]
    # the top, gathered up, twisted and tied, flopping over to one side
    lean = [0.10, 0.0, -0.55]
    base = [0.06, 0.18, -0.04]
    parts.append(place("teardrop", base, [0.86, 0.66, 0.78], EA24_BURLAP, anchor=[0, 0, 0], r=lean,
                       decal="ea24_burlap", wrap=True))
    neck = rotate([0, 0.52, 0], lean)
    tie = [base[0] + neck[0], base[1] + neck[1], base[2] + neck[2]]
    parts.append(part("torus", tie, [0.20, 0.16, 0.20], "#c9a26a", lean, decal="ea_twine", wrap=True))
    for n in range(5):
        a = n * TAU / 5
        flop = rotate([math.sin(a) * 0.08, 0.14, math.cos(a) * 0.08], lean)
        parts.append(place("leaf", [tie[0] + flop[0], tie[1] + flop[1], tie[2] + flop[2]],
                           [0.70, 0.26, 1.0], shade(EA24_BURLAP, 1.0 if n % 2 else 0.9),
                           anchor=[0, -0.5, 0], r=[lean[0] + math.cos(a) * 0.7, a, lean[2] - math.sin(a) * 0.7],
                           decal="ea24_burlap"))
    # a few crumbs caught in the turn-up
    for x, z in ((0.50, 0.70), (-0.30, 0.82), (0.84, 0.20), (-0.70, -0.50)):
        parts.append(part("sph", [x, -0.12, z], [0.05, 0.04, 0.05], "#f2dca0"))
    return parts


@EA24.back("goose_pack", "Hitchhiking Goose",
           "A rucksack with a goose in it. You did not put the goose in it. The goose "
           "does not want to get out of it. The goose would like a word with whoever is "
           "behind you, and the word is HONK.", "legendary")
def _():
    canvas, strap = "#6a7a4a", "#4a5a32"
    parts = straps(strap) + [
        part("rbox", [0, 0.28, -0.42], [1.10, 0.96, 0.70], canvas, decal="canvas", wrap=True),
        part("rbox", [0, 0.78, -0.42], [1.16, 0.08, 0.76], shade(canvas, 0.85)),
        part("rbox", [0, 0.06, -0.80], [0.72, 0.40, 0.10], shade(canvas, 1.08), decal="canvas"),
        part("rbox", [0, 0.24, -0.86], [0.74, 0.08, 0.04], strap),
        part("rbox", [0.20, 0.16, -0.86], [0.06, 0.20, 0.03], strap),
        part("rbox", [-0.20, 0.16, -0.86], [0.06, 0.20, 0.03], strap),
        part("rbox", [0.20, 0.06, -0.865], [0.10, 0.08, 0.02], BRASS, m="metal"),
        part("rbox", [-0.20, 0.06, -0.865], [0.10, 0.08, 0.02], BRASS, m="metal"),
        # the goose, sat in the top of it
        part("sph", [0, 0.92, -0.45], [0.82, 0.56, 0.66], EA24_GOOSE, decal="ea24_plumage", wrap=True),
        part("sph", [0.34, 0.94, -0.48], [0.18, 0.36, 0.56], "#e4e2dc", [0.2, 0, -0.2]),
        part("sph", [-0.34, 0.94, -0.48], [0.18, 0.36, 0.56], "#e4e2dc", [0.2, 0, 0.2]),
        place("teardrop", [0, 1.00, -0.76], [0.22, 0.26, 0.14], "#e4e2dc", anchor=[0, 0, 0],
              r=[-1.1, 0, 0]),
    ]
    # its neck, up out of the bag and round past your right ear
    neck = [[0.16, 1.02, -0.36], [0.50, 1.40, -0.44], [0.88, 1.80, -0.34], [0.98, 2.08, -0.10]]
    for a, b in zip(neck, neck[1:]):
        parts.append(rod(a, b, 0.20, EA24_GOOSE, t="capsule"))
    parts += [part("sph", p, [0.20, 0.20, 0.20], EA24_GOOSE) for p in neck[1:]]
    head = [1.00, 2.16, 0.02]
    parts += [
        part("sph", head, [0.28, 0.26, 0.36], EA24_GOOSE),
        # the bill, wide open, and the knob on top of it
        place("cone", [head[0], head[1] + 0.02, head[2] + 0.26], [0.14, 0.22, 0.10], EA24_BEAK,
              r=[PI / 2 - 0.15, 0, 0]),
        place("cone", [head[0], head[1] - 0.07, head[2] + 0.22], [0.11, 0.18, 0.07], "#e8801a",
              r=[PI / 2 + 0.35, 0, 0]),
        part("sph", [head[0], head[1] + 0.07, head[2] + 0.16], [0.08, 0.07, 0.07], "#e8801a"),
        part("sph", [head[0] + 0.12, head[1] + 0.05, head[2] + 0.07], [0.05, 0.06, 0.05], BLACK),
        part("sph", [head[0] - 0.12, head[1] + 0.05, head[2] + 0.07], [0.05, 0.06, 0.05], BLACK),
    ]
    # and a gosling, looking out of the front pocket
    parts += [p for p in _ea24_chick([-0.22, -0.02, -0.86], 0.34, PI, EA24_GOSLING)
              if p["p"][1] > 0.18]
    return parts


@EA24.back("hay_bale", "Hay Bale",
           "A bale of good dry straw on your back, with the pitchfork still in it and "
           "a chick asleep on top. You are, for all practical purposes, a bed now.",
           "rare")
def _():
    twine = "#a8743a"
    parts = straps("#7a5426") + [
        part("rbox", [0, 0.28, -0.42], [1.36, 0.80, 0.66], EA24_STRAW, decal="ea24_hay", wrap=True),
        part("rbox", [0.36, 0.28, -0.42], [0.05, 0.82, 0.68], twine),
        part("rbox", [-0.36, 0.28, -0.42], [0.05, 0.82, 0.68], twine),
        part("rbox", [0, 0.40, -0.05], [0.30, 0.14, 0.10], "#7a5426"),
    ]
    # loose stalks sticking out of the ends
    for n in range(10):
        s = 1 if n % 2 else -1
        y = 0.0 + (n // 2) * 0.13
        z = -0.20 - ((n * 7) % 5) * 0.10
        parts.append(rod([0.66 * s, y, z], [0.84 * s, y + 0.05 * ((n % 3) - 1), z - 0.04], 0.025,
                         shade(EA24_STRAW, 0.9 + 0.1 * (n % 3))))
    # the pitchfork, stuck in the top and leaning off over your shoulder
    base, top = [0.26, 0.60, -0.50], [0.92, 1.92, -0.66]
    parts += [rod(base, top, 0.07, "#a8743a"),
              rod([top[0] - 0.02, top[1] - 0.04, top[2]], [top[0] + 0.06, top[1] + 0.12, top[2] - 0.01],
                  0.09, "#8a5a2a")]
    d = [top[i] - base[i] for i in range(3)]
    length = math.sqrt(sum(v * v for v in d))
    u = [v / length for v in d]
    cross = [base[i] + u[i] * 0.04 for i in range(3)]
    parts.append(rod([cross[0] - 0.16, cross[1] + 0.08, cross[2]], [cross[0] + 0.16, cross[1] - 0.08, cross[2]],
                     0.05, IRON, m="metal"))
    for dx in (-0.14, 0.0, 0.14):
        p0 = [cross[0] + dx, cross[1] - dx * 0.5, cross[2]]
        parts.append(rod(p0, [p0[0] - u[0] * 0.26, p0[1] - u[1] * 0.26, p0[2] - u[2] * 0.26], 0.035,
                         IRON, m="metal"))
    # a red bandana tied round the handle
    mid = [base[i] + d[i] * 0.62 for i in range(3)]
    parts += [part("cyl", mid, [0.12, 0.10, 0.12], "#c42a22",
                   [math.acos(u[1]), math.atan2(u[0], u[2]), 0], decal="ea24_flannel", wrap=True),
              place("tri", [mid[0] + 0.07, mid[1] - 0.12, mid[2]], [0.16, 0.20, 0.4], "#c42a22",
                    r=[0, 0, PI + 0.3])]
    # and the sleeper on top of it all
    parts += _ea24_chick([-0.34, 0.68, -0.40], 0.34, 0.3, eyes="shut")
    return parts


@EA24.hairdo("silkie_puff", "Silkie Pompom",
             "The great white powder-puff crest of a silkie hen, the fluffiest chicken "
             "there is, and a pair of turquoise ear clips because silkies have "
             "turquoise ears. Look it up.", "uncommon")
def _():
    c = "#fbf6ec"
    parts = [place("hairshort", [0, 0, 0], [1.04, 1.04, 1.04], c, anchor=[0, 0, 0],
                   decal="ea24_down", wrap=True),
             part("sph", [0, 0.70, 0.02], [0.82, 0.58, 0.78], c, decal="ea24_down", wrap=True)]
    parts += around(8, 0.34, 0.0, lambda a, x, z: part(
        "sph", [x, 0.62 + 0.04 * math.cos(a), z * 0.95 + 0.02], [0.34, 0.30, 0.32],
        c if int(round(a * 8 / TAU)) % 2 else shade(c, 0.95), decal="ea24_down", wrap=True), start=0.2)
    parts += [part("sph", [0.12, 0.98, 0.04], [0.30, 0.22, 0.28], c, decal="ea24_down", wrap=True),
              part("sph", [-0.10, 0.96, -0.06], [0.26, 0.20, 0.26], c, decal="ea24_down", wrap=True),
              part("sph", [0.0, 0.52, 0.46], [0.40, 0.22, 0.20], c, decal="ea24_down", wrap=True)]
    parts += sides(lambda s: [part("sph", [0.565 * s, -0.10, 0.06], [0.06, 0.16, 0.12], "#2fc8c0",
                                   m="glass")])
    return parts


@EA24.hairdo("ducks_tail", "Duck's Tail",
             "A greased black pompadour: the quiff up front, a kiss curl on the brow and "
             "the back combed in from both sides to meet like the tail of a duck. Takes "
             "two hours and a whole tin of brilliantine.", "rare")
def _():
    c = "#1c1816"
    parts = [
        place("hairmid", [0, 0, 0], [1.04, 1.02, 1.05], c, anchor=[0, 0, 0], decal="strands",
              wrap=True),
        # the quiff, swept up off the brow and rolled forward
        part("sph", [0, 0.67, 0.14], [0.86, 0.38, 0.70], c, [-0.30, 0, 0], decal="strands", wrap=True),
        part("sph", [0, 0.66, 0.42], [0.70, 0.34, 0.36], c, [-0.70, 0, 0], decal="strands", wrap=True),
        part("capsule", [0, 0.70, 0.54], [0.18, 0.62, 0.18], shade(c, 1.5), [0, 0, PI / 2], m="glass"),
        # the kiss curl
        place("spiral", [0.10, 0.38, 0.57], [0.10, 0.12, 0.06], c, r=[PI / 2, 0, 0]),
    ]
    # the duck's tail: both sides combed in to meet in a seam down the back,
    # flicking up where they meet
    for s in (1, -1):
        parts.append(part("sph", [0.17 * s, 0.02, -0.57], [0.38, 0.92, 0.16], c, [0.0, -0.30 * s, 0.20 * s],
                          decal="strands", wrap=True))
    parts.append(place("teardrop", [0, -0.38, -0.60], [0.22, 0.26, 0.12], c, anchor=[0, 0, 0],
                       r=[-2.3, 0, 0], decal="strands", wrap=True))
    return parts


EA24.face("peep", "Peep!",
          "Two great round eyes, a little beak open for the first word anyone ever says, "
          "and the word is 'peep'. Everything is new. Everything is a mother.", [
              {"k": "ellipse", "x": -0.19, "y": -0.12, "w": 0.16, "h": 0.19, "c": "#16171b"},
              {"k": "ellipse", "x": 0.19, "y": -0.12, "w": 0.16, "h": 0.19, "c": "#16171b"},
              {"k": "ellipse", "x": -0.16, "y": -0.16, "w": 0.06, "h": 0.07, "c": "#ffffff"},
              {"k": "ellipse", "x": 0.22, "y": -0.16, "w": 0.06, "h": 0.07, "c": "#ffffff"},
              {"k": "ellipse", "x": -0.21, "y": -0.07, "w": 0.025, "h": 0.025, "c": "#ffffff"},
              {"k": "ellipse", "x": 0.17, "y": -0.07, "w": 0.025, "h": 0.025, "c": "#ffffff"},
              {"k": "ellipse", "x": 0.0, "y": 0.13, "w": 0.13, "h": 0.06, "c": "#7a2a1a"},
              {"k": "poly", "pts": [[-0.10, 0.03], [0.10, 0.03], [0.0, 0.12]], "c": "#ff9a1a"},
              {"k": "poly", "pts": [[-0.08, 0.15], [0.08, 0.15], [0.0, 0.22]], "c": "#e0781a"},
              {"k": "ellipse", "x": -0.33, "y": 0.05, "w": 0.11, "h": 0.06, "c": "#ff9aa8"},
              {"k": "ellipse", "x": 0.33, "y": 0.05, "w": 0.11, "h": 0.06, "c": "#ff9aa8"},
          ], "uncommon")
EA24.face("up_with_the_rooster", "Up With the Rooster",
          "Half past four in the morning. One eye open, one still asleep, a yawn you "
          "could post a letter in. The rooster is very pleased with himself.", [
              {"k": "arc", "x": -0.19, "y": -0.13, "r": 0.07, "a0": 0.05, "a1": 0.45, "w": 0.035,
               "c": "#16171b"},
              {"k": "ellipse", "x": 0.19, "y": -0.10, "w": 0.12, "h": 0.07, "c": "#16171b"},
              {"k": "line", "x1": 0.10, "y1": -0.135, "x2": 0.28, "y2": -0.13, "w": 0.04,
               "c": "#16171b"},
              {"k": "arc", "x": -0.19, "y": -0.10, "r": 0.10, "a0": 0.12, "a1": 0.38, "w": 0.02,
               "c": "#8a6a9a"},
              {"k": "arc", "x": 0.19, "y": -0.08, "r": 0.10, "a0": 0.12, "a1": 0.38, "w": 0.02,
               "c": "#8a6a9a"},
              {"k": "ellipse", "x": 0.0, "y": 0.17, "w": 0.15, "h": 0.21, "c": "#3a1414"},
              {"k": "ellipse", "x": 0.0, "y": 0.235, "w": 0.10, "h": 0.06, "c": "#e05a6a"},
              {"k": "line", "x1": 0.30, "y1": -0.42, "x2": 0.40, "y2": -0.42, "w": 0.02, "c": "#4a5ab0"},
              {"k": "line", "x1": 0.40, "y1": -0.42, "x2": 0.30, "y2": -0.34, "w": 0.02, "c": "#4a5ab0"},
              {"k": "line", "x1": 0.30, "y1": -0.34, "x2": 0.40, "y2": -0.34, "w": 0.02, "c": "#4a5ab0"},
          ], "rare")
EA24.shirt("hatchery_flannel", "Hatchery Hand's Flannel",
           "A red check work shirt with the hatchery's patch on it and a chick living in "
           "the pocket. It came with the shirt. It is not leaving with the shirt.",
           {"torso": "#a8302a", "arms": "#a8302a", "decal": "ea24_tee_pocket",
            "weave": "ea24_flannel"}, "rare")
EA24.pants("chicken_legs", "Chicken Legs",
           "Feathered drumsticks above, yellow and scaly below, three toes apiece. "
           "Very comfortable. Nobody will take you seriously ever again.",
           {"legs": "#f4efe4", "weave": "ea24_drumsticks", "cuff": "#e8901a"})
EA24.belt("follow_my_leader", "Follow-My-Leader Belt",
          "Green webbing with a line of chicks marching round and round it, each one "
          "sure the one in front knows where they are going, and a pocket thermometer "
          "on a chain.",
          {"band": "#4f8a3a", "buckle": BRASS, "width": 0.22, "metal": True,
           "weave": "ea24_chickrow", "chain": GOLD})


EA24_CHICK_MINION = {
    "name": "Chick", "model": "parts", "count": 5, "hp": 15, "speed": 22, "damage": 4,
    "reach": 3.0, "rate": 0.55, "secs": 14, "sight": 60, "scale": 0.5,
    "on_hit": {"mark": [0.15, 3.0]},
    "parts": _ea24_chick([0, 0, 0], 3.0),
}


@EA24.weapon("pecking_order", "The Pecking Order",
             "Mother Hen, tucked under your arm. Point her at somebody and she clucks, "
             "and five chicks come tumbling out of her feathers to peck them about the "
             "ankles until they understand exactly where they stand.",
             {"kind": "summon", "cooldown": 24, "sound": "crow"},
             [["+", "Five chicks run at the nearest enemy and peck: 4 a peck, nearly two "
                    "pecks a second each"],
              ["+", "Pecked is marked: anyone they peck takes 15% more damage from "
                    "everybody for 3 seconds"],
              ["-", "15 health apiece: one stray shot and a chick is gone"],
              ["-", "They lose interest after 14 seconds; 24 second cooldown"]],
             rarity="legendary", minion=EA24_CHICK_MINION)
def _():
    parts = _ea24_hen([0, -0.26, 0.24], 0.56)
    parts += [p for p in _ea24_chick([0.26, -0.22, 0.36], 0.24, 0.5) if p["p"][1] > -0.14]
    parts += [p for p in _ea24_chick([-0.25, -0.22, 0.34], 0.22, -0.6) if p["p"][1] > -0.14]
    return parts


def _ea24_goose_egg(k=1.0, flying=False):
    """The nest egg: a speckled goose egg with a coin slot in the top and a
    coin half in it -- upright, or (``flying``) lying along +Z."""
    w = 0.40 * k
    s = w / EGG_W
    parts = [place("egg", [0, 0, 0], [s, s, s], "#f8f2e4", anchor=[0, 0, 0], decal="ea24_speckle",
                   wrap=True),
             part("rbox", [0, EGG_H * s - 0.01 * k, 0], [0.10 * k, 0.03 * k, 0.025 * k], "#3a2a1a"),
             part("disc", [0, EGG_H * s + 0.03 * k, 0], [0.09 * k, 0.09 * k, 0.02 * k], GOLD, m="metal")]
    if flying:
        return at_frame(parts, [0, 0, -EGG_H * s / 2], [PI / 2, 0, 0])
    return parts


@EA24.weapon("nest_egg", "Nest Egg",
             "A goose egg the size of your head with a coin slot in the top: everything "
             "you were saving for a rainy day. Throw it and it pays out -- yolk in the "
             "face of whoever it hits, and five little eggs bursting out all over "
             "everybody near them.",
             {"kind": "projectile", "projectile": "nestegg", "damage": 20, "splash": 4.5,
              "splash_damage": 22, "rpm": 40, "mag": 1, "reload": 1.6, "speed": 46,
              "range": 220, "auto": False, "sound": "throw", "recoil": 1.0, "reserve": 16,
              "gravity_scale": 1.25, "self_damage": 0.3, "knockback": 8,
              "on_hit": {"blind": [1.0, "light"]},
              "cluster": {"count": 5, "damage": 18, "radius": 4.0, "speed": 16,
                          "projectile": "eggling", "color": "#fff1d0",
                          "on_hit": {"slow": [0.30, 2.0]}},
              "trail_colors": ["#fff1d0", "#ffd23a"]},
             [["+", "A direct hit gets yolk in their eyes: blinded for a second"],
              ["+", "Cracks open into five little eggs that burst for 18 each and leave "
                    "everyone they hit slowed by 30% for 2 seconds"],
              ["-", "The goose egg itself only bursts for 22"],
              ["-", "One at a time, lobbed: it drops"],
              ["-", "Your own savings can hurt you"]], rarity="legendary",
             proj=lambda: _ea24_goose_egg(1.4, flying=True))
def _():
    parts = [
        place("bowl", [0, -0.14, 0.34], [0.64, 0.42, 0.64], EA24_STRAW, anchor=[0, 0, 0],
              decal="ea_straw", wrap=True),
        part("torus", [0, 0.10, 0.34], [0.70, 0.70, 0.70], shade(EA24_STRAW, 0.9), decal="ea_straw",
             wrap=True),
    ]
    parts += at_frame(_ea24_goose_egg(1.0), [0, -0.04, 0.34])
    for a in (0.4, 1.9, 3.3, 4.6):
        parts.append(rod([math.sin(a) * 0.30, 0.10, 0.34 + math.cos(a) * 0.30],
                         [math.sin(a) * 0.42, 0.20, 0.34 + math.cos(a) * 0.42], 0.025, EA24_STRAW))
    return parts


def _ea24_bulb(k=1.0):
    """A red heat-lamp bulb lying along +Z: the brass screw at the back, the
    big domed face glowing at the front."""
    parts = [part("cyl", [0, 0, 0.06 * k], [0.16 * k, 0.16 * k, 0.16 * k], BRASS, [PI / 2, 0, 0],
                  m="metal")]
    for n in range(3):
        parts.append(part("torus", [0, 0, (0.01 + n * 0.05) * k], [0.19 * k, 0.12 * k, 0.19 * k],
                          GOLD_DARK, [PI / 2, 0, 0], m="metal"))
    parts += [part("cyl", [0, 0, -0.05 * k], [0.10 * k, 0.06 * k, 0.10 * k], BLACK, [PI / 2, 0, 0]),
              place("bell", [0, 0, 0.72 * k], [0.56 * k, 0.56 * k, 0.56 * k], "#c42a1a",
                    anchor=[0, 0, 0], r=[-PI / 2, 0, 0], m="glass"),
              part("sph", [0, 0, 0.72 * k], [0.55 * k, 0.55 * k, 0.16 * k], EA24_LAMP, m="neon"),
              part("sph", [0.10 * k, 0.10 * k, 0.78 * k], [0.10 * k, 0.08 * k, 0.04 * k], "#ffd0a0",
                   m="neon")]
    return parts


@EA24.weapon("brooder_bulb", "Brooder Bulb",
             "The incubator's spare heat lamp, lobbed underarm. It goes off with a pop "
             "and leaves the ground glowing like the floor of the brooder: your side "
             "warm and mending in it, the other side warm and very, very sleepy.",
             {"kind": "projectile", "projectile": "heatbulb", "damage": 14, "splash": 3.5,
              "splash_damage": 16, "rpm": 50, "mag": 2, "reload": 2.2, "speed": 52,
              "range": 200, "auto": False, "sound": "throw", "recoil": 0.6, "reserve": 16,
              "gravity_scale": 1.2, "self_damage": 0.0, "knockback": 4,
              "on_hit": {"burn": [4, 2.0]},
              "ground_zone": {"radius": 7.0, "secs": 6.0, "color": "#ff8a3a",
                              "particle": "ea24_down", "name": "Heat Lamp",
                              "ally": {"regen": [6, 1.0]}, "enemy": {"slow": [0.30, 1.0]}},
              "trail_colors": ["#ff8a3a", "#ffd0a0"]},
             [["+", "Leaves a warm patch for 6 seconds: you and your team heal 6 a second "
                    "in it"],
              ["+", "Enemies in it are drowsy: 30% slower"],
              ["+", "The hot glass singes: 4 burn a second for 2 seconds"],
              ["-", "The pop itself is small: 16"],
              ["-", "Two bulbs, then a careful reload"]], rarity="legendary",
             proj=lambda: _ea24_bulb(1.3),
             deploy=lambda: [
                 *at_frame(_ea24_bulb(1.4)[:5], [0.3, 0.14, -0.2], [0, 0.8, 0]),
                 *[place("tri", [math.sin(a) * 0.8, 0.06, math.cos(a) * 0.8], [0.30, 0.34, 0.6],
                         "#c42a1a", r=[-PI / 2 + 0.2, a, 0.4 * (n % 2)], m="glass")
                   for n, a in enumerate((0.3, 1.6, 2.7, 4.0, 5.2))],
                 *[place("leaf", [math.sin(a) * r_, 0.03, math.cos(a) * r_], [1.2, 1.4, 1.0],
                         shade(EA24_STRAW, 0.85 + 0.1 * (n % 3)), r=[-PI / 2, a, 0])
                   for n, (a, r_) in enumerate(((0.9, 1.6), (2.0, 2.2), (3.1, 1.4), (4.3, 2.6),
                                                 (5.5, 1.9), (0.2, 2.8)))]])
def _():
    return _ea24_bulb(1.0) + [part("rbox", [0, -0.06, -0.06], [0.12, 0.16, 0.10], "#2a2420")]


@EA24.gear("coddler", "The Coddler",
           "A porcelain egg coddler with a chick painted on it and a coddled egg inside, "
           "still warm. Eat it and you are coddled: wrapped up, kept warm and very hard "
           "to hurt for a little while. Your gran would approve.",
           {"kind": "consume", "cooldown": 26, "sound": "eat",
            "consume": {"shield": [45, 8.0], "regen": [4, 8.0]}},
           [["+", "Coddled: the next 45 damage you take within 8 seconds is soaked up"],
            ["+", "...and you mend 4 health a second while it lasts"],
            ["-", "No instant healing at all"],
            ["-", "26 second cooldown"]], rarity="rare")
def _():
    china = "#f8f6f0"
    return [
        part("cyl", [0, 0.10, 0.16], [0.36, 0.34, 0.36], china, decal="ea24_coddler", wrap=True),
        part("sph", [0, -0.07, 0.16], [0.36, 0.14, 0.36], china),
        part("torus", [0, 0.27, 0.16], [0.40, 0.40, 0.40], "#4a7ac8"),
        # the screw lid and its wire ring
        part("cyl", [0, 0.31, 0.16], [0.38, 0.08, 0.38], SILVER, m="metal"),
        place("hemi", [0, 0.35, 0.16], [0.30, 0.16, 0.30], SILVER, anchor=[0, 0, 0], m="metal"),
        part("torus", [0, 0.50, 0.16], [0.18, 0.18, 0.18], SILVER, [PI / 2, 0, 0], m="metal"),
        # a spoon, at the ready
        rod([0.22, -0.02, 0.00], [0.26, 0.40, 0.30], 0.03, SILVER, m="metal"),
        part("sph", [0.27, 0.44, 0.33], [0.08, 0.04, 0.12], SILVER, [0.6, 0, 0], m="metal"),
    ]


EA24.effect("hatching_hour", name="Hatching Hour", rate=2.2, life=[1.4, 2.0],
            size=[0.34, 0.46], grow=0.0, gravity=1.2, spread=0.35, rise=[1.0, 1.5],
            blend="normal", spin=0.5, colors=["#ffd93a", "#fff4d0", "#ffc64a"],
            shapes=["ea24_hatchling", "ea24_hatchling", "ea24_shell"], radius=0.8,
            upright=True, wobble=0.4)
EA24.effect("downy_drift", name="Downy Drift", rate=3.0, life=[2.2, 3.2],
            size=[0.20, 0.32], grow=0.1, gravity=0.12, spread=0.7, rise=[0.2, 0.4],
            blend="normal", spin=1.4, colors=["#fff6dc", "#ffe08a", "#ffc890"],
            shapes=["ea24_down", "ea24_down", "puff"], radius=0.8, wobble=0.9)
EA24.opening(
    sky={"top": "#4a5ac8", "horizon": "#ffb878", "sun": [0.2, 0.25, 0.7], "clouds": 0.4,
         "tint": "#ffe8cc"},
    ambient="#ffd8a8", beam="#ffb04a", seep="downy_drift", after="hatching_hour",
    burst=["#ffd93a", "#ffb04a", "#ffffff", "#e8c468"],
    pieces=[{"shape": "chick", "colors": ["#ffd93a", "#ffe680", "#c9c07c"], "blend": "normal"},
            {"shape": "ea24_shell", "colors": ["#fff4e0", "#f2dcc0", "#c8e6da"], "blend": "normal"},
            {"shape": "ea24_down", "colors": ["#fff6dc", "#ffe08a"], "blend": "normal"},
            {"shape": "feather", "colors": ["#b5562a", "#f4efe4"], "blend": "normal"}],
    backdrop="ea24_barnyard", title_wait="Something is tapping on the inside...",
    title_shake="Peep!")
EA24.award("The Great Hatch", ["Egg Sitter", "Peeper", "Fledgling", "Brooder",
                               "Top of the Pecking Order", "Mother Hen"],
           "Opened Incubators during The Great Hatch, Easter 2024.", "em_chick", "egg")
EA24.bundle("pair", "Incubator and Key", 1, 1050, "One Incubator, one Egg Tooth Key.")
EA24.bundle("brood", "A Whole Brood", 3, 3000, "Three incubators, three keys. Saves 300.")

# @@ EA24 The Great Hatch goes above this line @@

# @@ EA25 Choc-o-Lock goes above this line @@

# @@ EA26 Faberge Gala goes above this line @@


EVENTS = [EA22, EA23]

# (EA24 adds itself to the list here)
EVENTS += [EA24]  # @@ EA24 @@

# (EA25 adds itself to the list here)
EVENTS += []  # @@ EA25 @@

# (EA26 adds itself to the list here)
EVENTS += []  # @@ EA26 @@
