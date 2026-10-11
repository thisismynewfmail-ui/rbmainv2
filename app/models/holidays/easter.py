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

from .kit import (BLACK, BRASS, GOLD, GOLD_DARK, IRON, PI, SILVER, SNOW, TAU, WHITE,
                  Event, around, at_frame, band, buckle, cap, dome, gift_bow, mix, part,
                  place, pompom, ringband, rod, rotate, shade, sides, straps)

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
        part("cyl", [0.13, 0, 0], [0.09, 0.84, 0.09], BRASS, [0, 0, PI / 2], m="metal"),
        part("torus", [-0.27, 0, 0], [0.20, 0.07, 0.20], GOLD_DARK, [0, 0, PI / 2], m="metal"),
        part("rbox", [-0.48, 0.0, 0], [0.30, 0.06, 0.06], BRASS, m="metal"),
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

EVENTS = [EA22, EA23]
