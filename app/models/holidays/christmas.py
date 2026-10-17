"""Christmas: snow on everything, and a crate under every tree.

  2022  Frostfall             the first snow: a snow globe, cocoa, sledges and snowmen
  2023  Gingerbread Junction  the gingerbread railway: a cookie tin, candy canes, icing
  2024  North Pole Express    the overnight mail train: a coal tender, steam and parcels
  2025  Krampusnacht          Santa's dark companion comes calling with a basket
  2026  Aurora Winterlight    the northern lights over the pole -- waiting for December

Every December from the first to the thirtieth.  2026 is on the calendar but
has not started yet; its crate is built and boxed like the others, so the
shop can show it coming.
"""
from __future__ import annotations

import math

from .kit import (BLACK, BONE, BRASS, GOLD, GOLD_DARK, IRON, PI, SILVER, SNOW, TAU, WHITE,
                  Event, around, at_frame, band, buckle, cap, dome, gift_bow, mix, part,
                  place, pompom, ringband, rod, rotate, shade, sides, straps)

# the colours every year shares
BERRY = "#d0141c"
HOLLY = "#1e7a36"
COAL = "#1e1f24"
CARROT = "#ff8a1f"
SNOWBALL = "#f7fbff"
ICE = "#dff4ff"
CANDY_RED = "#d62828"


def _frame(facing):
    """A little local frame for a figure facing yaw ``facing``: offsets are
    (side, up, forward)."""
    fwd = (math.sin(facing), math.cos(facing))
    side = (math.cos(facing), -math.sin(facing))

    def off(at, dx, dy, dz):
        return [at[0] + side[0] * dx + fwd[0] * dz, at[1] + dy, at[2] + side[1] * dx + fwd[1] * dz]
    return off


def _snowman(at, k=1.0, facing=0.0, scarf=CANDY_RED, hat=True, arms=True, wave=False):
    """A snowman standing on ``at`` (the bottom of its lowest ball), facing
    yaw ``facing``: three balls of snow, coal eyes and buttons, a carrot nose,
    a scarf, stick arms and a little top hat."""
    off = _frame(facing)
    out = [
        part("sph", off(at, 0, 0.40 * k, 0), [0.80 * k, 0.76 * k, 0.80 * k], SNOWBALL,
             decal="xm_snow", wrap=True),
        part("sph", off(at, 0, 0.98 * k, 0), [0.60 * k, 0.56 * k, 0.60 * k], SNOWBALL,
             decal="xm_snow", wrap=True),
        part("sph", off(at, 0, 1.42 * k, 0), [0.46 * k, 0.44 * k, 0.46 * k], SNOWBALL,
             decal="xm_snow", wrap=True),
        # the scarf, round the neck, a tail down the front
        part("cyl", off(at, 0, 1.22 * k, 0), [0.50 * k, 0.10 * k, 0.50 * k], scarf,
             decal="knit", wrap=True),
        part("rbox", off(at, 0.12 * k, 1.08 * k, 0.24 * k), [0.10 * k, 0.26 * k, 0.04 * k], scarf,
             [0.25, facing, -0.15], decal="knit"),
        # carrot nose and coal
        place("carrot", off(at, 0, 1.42 * k, 0.20 * k), [0.08 * k, 0.24 * k, 0.08 * k], CARROT,
              anchor=[0, 1, 0], r=[-PI / 2 + 0.1, facing, 0]),
    ]
    for s in (1, -1):
        out.append(part("sph", off(at, 0.08 * k * s, 1.50 * k, 0.19 * k),
                        [0.06 * k, 0.06 * k, 0.04 * k], COAL))
    for n in range(3):
        out.append(part("sph", off(at, 0, (0.84 + n * 0.14) * k, 0.29 * k - abs(n - 1) * 0.01 * k),
                        [0.07 * k, 0.07 * k, 0.04 * k], COAL))
    if hat:
        out += [part("cyl", off(at, 0, 1.63 * k, 0), [0.40 * k, 0.03 * k, 0.40 * k], COAL),
                part("cyl", off(at, 0, 1.76 * k, 0), [0.26 * k, 0.24 * k, 0.26 * k], COAL),
                part("cyl", off(at, 0, 1.68 * k, 0), [0.27 * k, 0.05 * k, 0.27 * k], scarf)]
    if arms:
        for s in (1, -1):
            lift = 0.9 if (wave and s > 0) else 0.35
            out.append(part("cyl", off(at, 0.42 * k * s, (1.02 + (0.18 if lift > 0.5 else 0.04)) * k, 0),
                            [0.035 * k, 0.48 * k, 0.035 * k], "#5a3a22",
                            [0, facing, -s * (PI / 2 - lift)]))
    return out


def _mug(at, k=1.0, body="#f4f6f8", cocoa="#5a3020", handle_side=1, steam=True, lid=None):
    """A mug of hot cocoa: a printed mug, a handle, cocoa, marshmallows, a
    swirl of cream and the steam coming off it.  ``at`` is the bottom."""
    x, y, z = at
    out = [
        part("cyl", [x, y + 0.40 * k, z], [0.78 * k, 0.80 * k, 0.78 * k], body,
             decal="xm_mug", wrap=True),
        part("torus", [x, y + 0.80 * k, z], [0.80 * k, 0.40 * k, 0.80 * k], body),
        part("cyl", [x, y + 0.74 * k, z], [0.66 * k, 0.04 * k, 0.66 * k], cocoa),
        part("torus", [x + 0.40 * k * handle_side, y + 0.42 * k, z], [0.46 * k, 0.70 * k, 0.46 * k],
             body, [PI / 2, 0, 0]),
        part("sph", [x, y + 0.80 * k, z], [0.44 * k, 0.20 * k, 0.44 * k], WHITE),
        place("spiral", [x, y + 0.84 * k, z], [0.22 * k, 0.16 * k, 0.22 * k], WHITE),
        part("sph", [x, y + 0.96 * k, z], [0.10 * k, 0.10 * k, 0.10 * k], WHITE),
    ]
    for n, (dx, dz, turn) in enumerate(((0.22, 0.10, 0.3), (-0.20, 0.14, 1.1), (0.04, -0.22, 0.7))):
        out.append(part("rbox", [x + dx * k, y + 0.80 * k, z + dz * k], [0.13 * k, 0.11 * k, 0.13 * k],
                        "#fff6f0", [0.2, turn, 0.1]))
    if steam:
        for n, (dx, h) in enumerate(((-0.12, 0.30), (0.10, 0.40), (0.0, 0.26))):
            out.append(place("teardrop", [x + dx * k, y + (1.10 + n * 0.14) * k, z - 0.06 * k],
                             [0.12 * k, h * k, 0.12 * k], "#ffffff", a=0.35))
    if lid:
        for p in out:
            p["lid"] = 1
    return out


def _holly(at, k=1.0, yaw=0.0, berries=3):
    """A sprig of holly: two leaves and a cluster of berries, lying flat-ish."""
    x, y, z = at
    out = [place("holly", [x - 0.16 * k * math.cos(yaw), y, z + 0.16 * k * math.sin(yaw)],
                 [0.40 * k, 0.40 * k, 0.6 * k], HOLLY, r=[0, yaw, 0.5]),
           place("holly", [x + 0.16 * k * math.cos(yaw), y, z - 0.16 * k * math.sin(yaw)],
                 [0.40 * k, 0.40 * k, 0.6 * k], "#2a9446", r=[0, yaw, -0.5])]
    for n in range(berries):
        a = n * TAU / max(1, berries)
        out.append(part("sph", [x + math.sin(a) * 0.05 * k, y + 0.04 * k + math.cos(a) * 0.04 * k,
                                z + 0.05 * k], [0.09 * k, 0.09 * k, 0.09 * k], BERRY, m="glass"))
    return out


# ============================================================ 2022
FROST = "#8fd0ff"
NIGHT_BLUE = "#13264a"
LACQUER = "#9a1b22"
XM22 = Event(
    "christmas_2022", "christmas", 2022, "xm22",
    name="Frostfall", title="Frostfall",
    blurb="December 2022 brought Blockhaven its very first snow. It started on the "
          "first, did not stop until the thirtieth, and buried the Relay up to its "
          "antennas. Somebody built a snowman on the spawn pad. Nobody has had the "
          "heart to knock it down.",
    tagline="It's snowing. It's actually snowing!",
    starts="2022-12-01", ends="2022-12-30",
    colors={"accent": FROST, "deep": "#0c1830", "glow": "#e8f6ff"},
    family_effects=["frostbite", "starstruck", "candlelight_vigil"],
    hero_effect="snowglobe_swirl", stencil="stencil_xm22")


@XM22.crate_model("Snow Globe Crate",
                  "A snow globe the size of a crate: a lacquered music-box base, a "
                  "winding key, and under the glass a tiny Blockhaven in its very first "
                  "snow. The glass lifts. The snow keeps falling anyway. Holds the "
                  "Frostfall set. Needs a Snowflake Key.",
                  hinge=[0, -0.04, -0.70], keyhole=[0, -0.40, 0.86])
def _():
    wood = "#4a2814"
    parts = [
        # the music-box plinth: a dark wood foot, the red lacquer drum, gilt rims
        part("cyl", [0, -0.74, 0], [1.76, 0.16, 1.76], wood, decal="planks", wrap=True),
        part("cyl", [0, -0.40, 0], [1.60, 0.54, 1.60], LACQUER, decal="xm_giltscroll",
             wrap=True),
        part("cyl", [0, -0.665, 0], [1.66, 0.05, 1.66], GOLD, m="metal"),
        part("cyl", [0, -0.135, 0], [1.66, 0.05, 1.66], GOLD, m="metal"),
        part("cyl", [0, -0.08, 0], [1.46, 0.08, 1.46], wood),
        # the scene under the glass: a drift of snow, a pine with a star, a
        # snowman, and a cabin with its lamp lit
        place("hemi", [0, -0.05, 0], [1.30, 0.30, 1.30], SNOWBALL, anchor=[0, 0, 0],
              decal="xm_snow", wrap=True),
        place("tree", [-0.32, 0.02, -0.12], [0.44, 0.70, 0.44], "#2f6a3e", anchor=[0, 0, 0]),
        place("tree", [-0.32, 0.30, -0.12], [0.30, 0.36, 0.30], SNOWBALL, anchor=[0, 0, 0]),
        place("star", [-0.32, 0.76, -0.12], 0.14, GOLD, m="neon"),
        part("rbox", [0.14, 0.13, -0.34], [0.36, 0.24, 0.26], "#6a3a1e", decal="planks"),
        part("wedge", [0.14, 0.31, -0.40], [0.42, 0.14, 0.15], SNOWBALL, [0, PI, 0]),
        part("wedge", [0.14, 0.31, -0.28], [0.42, 0.14, 0.15], SNOWBALL),
        part("box", [0.14, 0.12, -0.205], [0.10, 0.10, 0.01], "#ffd36a", m="neon"),
        # the glass, and the snow caught in it (the glass is the lid)
        part("sph", [0, 0.58, 0], [1.36, 1.36, 1.36], "#e8f6ff", m="glass", a=0.2, lid=1),
        part("torus", [0, -0.02, 0], [1.42, 0.40, 1.42], GOLD, m="metal", lid=1),
        # the lock on the front of the drum, the winding key on its side
        part("rbox", [0, -0.40, 0.80], [0.36, 0.34, 0.08], BRASS, m="metal", decal="keyhole",
             lock=1),
        part("cyl", [0.86, -0.40, 0], [0.08, 0.16, 0.08], GOLD, [0, 0, PI / 2], m="metal"),
        part("torus", [0.98, -0.31, 0], [0.22, 0.30, 0.22], GOLD, [0, 0, PI / 2], m="metal"),
        part("torus", [0.98, -0.49, 0], [0.22, 0.30, 0.22], GOLD, [0, 0, PI / 2], m="metal"),
        part("sph", [0.97, -0.40, 0], [0.09, 0.09, 0.09], GOLD, m="metal"),
        # a brass plaque on the back with the year's stencil
        part("rbox", [0, -0.40, -0.80], [0.66, 0.42, 0.05], BRASS, m="metal"),
        part("box", [0, -0.40, -0.83], [0.58, 0.38, 0.02], "#000000", [0, PI, 0],
             decal="stencil_xm22", a=-1),
    ]
    parts += _snowman([0.30, 0.04, 0.16], 0.36, facing=0.25)
    parts += _holly([-0.48, -0.16, 0.70], 0.7, yaw=0.2)
    parts += _holly([0.48, -0.16, 0.70], 0.7, yaw=-0.2)
    # snow in the water: flakes and specks, which go up with the glass
    for n in range(18):
        a = n * 2.39996
        rr = 0.18 + (n * 37 % 10) / 10 * 0.36
        y = 0.30 + (n * 53 % 17) / 17 * 0.72
        p = [math.sin(a) * rr, y, math.cos(a) * rr]
        if n % 3 == 0:
            parts.append(place("snowflake", p, 0.12, "#ffffff", r=[0.3 * n, a, 0], lid=1))
        else:
            parts.append(part("sph", p, [0.05, 0.05, 0.05], "#ffffff", lid=1))
    return parts


@XM22.key_model("Snowflake Key",
                "A silver key whose bow is a snowflake that never melts, with two "
                "icicles for teeth. Opens one Snow Globe Crate, and is cold to the "
                "touch for a week afterwards.", shoulder=-0.30)
def _():
    silver = "#cfe3f2"
    return [
        place("snowflake", [-0.64, 0, 0], 0.66, silver, m="metal"),
        part("sph", [-0.64, 0, 0.02], [0.16, 0.16, 0.10], FROST, m="glass"),
        part("torus", [-0.30, 0, 0], [0.20, 0.40, 0.20], "#9fc4e0", [0, 0, PI / 2], m="metal"),
        part("cyl", [0.12, 0, 0], [0.09, 0.90, 0.09], silver, [0, 0, PI / 2], m="metal"),
        place("icicle", [0.40, -0.03, 0], [0.13, 0.26, 0.13], ICE, anchor=[0, 1, 0], m="glass"),
        place("icicle", [0.54, -0.03, 0], [0.13, 0.36, 0.13], ICE, anchor=[0, 1, 0], m="glass"),
        part("sph", [0.58, 0, 0], [0.11, 0.11, 0.11], silver, m="metal"),
    ]


@XM22.hat("globe_helmet", "Snowed In",
          "Your very own snow globe, worn: a glass bubble on a music-box collar, and a "
          "pine and a snowman stood on your head inside it while the snow comes down "
          "forever. Please do not shake the wearer.", "legendary")
def _():
    glass = "#e8f6ff"
    parts = [
        part("sph", [0, -0.45, 0], [2.24, 2.42, 2.20], glass, m="glass", a=0.16),
        # the collar it stands on, lacquered, gilt, with its winding key behind
        place("ring", [0, -1.36, 0], [1.98, 0.62, 1.94], LACQUER, anchor=[0, 0, 0],
              decal="xm_giltscroll", wrap=True),
        part("torus", [0, -1.23, 0], [2.00, 0.30, 1.96], GOLD, m="metal"),
        part("cyl", [0, -1.30, -1.02], [0.07, 0.14, 0.07], GOLD, [PI / 2, 0, 0], m="metal"),
        part("torus", [0.09, -1.30, -1.10], [0.18, 0.30, 0.18], GOLD, [PI / 2, 0, PI / 2],
             m="metal"),
        part("torus", [-0.09, -1.30, -1.10], [0.18, 0.30, 0.18], GOLD, [PI / 2, 0, PI / 2],
             m="metal"),
        # snow on the crown of the head, and the scene stood on it
        part("rbox", [0, 0.03, 0], [1.30, 0.10, 1.24], SNOWBALL, decal="xm_snow", wrap=True),
        place("hemi", [0.05, 0.04, -0.05], [1.0, 0.36, 0.9], SNOWBALL, anchor=[0, 0, 0],
              decal="xm_snow", wrap=True),
        place("tree", [-0.30, 0.10, -0.18], [0.44, 0.62, 0.44], "#2f6a3e", anchor=[0, 0, 0]),
        place("tree", [-0.30, 0.34, -0.18], [0.30, 0.32, 0.30], SNOWBALL, anchor=[0, 0, 0]),
        place("star", [-0.30, 0.78, -0.18], 0.12, GOLD, m="neon"),
    ]
    parts += _snowman([0.28, 0.10, 0.18], 0.34, facing=0.3, wave=True)
    # flakes caught in the glass all round
    for n in range(16):
        a = n * 2.39996
        y = -0.95 + (n * 41 % 16) / 16 * 1.55
        rr = 1.0 if y < 0.0 else 0.35 + (n % 4) * 0.12
        parts.append(place("snowflake", [math.sin(a) * rr, y, math.cos(a) * rr * 0.98],
                           0.10 + (n % 3) * 0.02, "#ffffff", r=[0.4 * n, a, 0]))
    return parts


@XM22.hat("snowman_head", "Snowman Head",
          "A whole snowman's head, coal, carrot and all, pulled down over your own. "
          "It is warmer in there than you would think. The carrot is load-bearing.",
          "rare", hair="hide", face_cover=True)
def _():
    shell = dome(-0.62, 1.10, SNOWBALL, decal="xm_snow", wrap=True)
    w = shell["s"][0]
    parts = [
        shell,
        part("cyl", [0, -0.95, 0], [w, 0.66, w * 0.97], SNOWBALL, decal="xm_snow", wrap=True),
        part("torus", [0, -1.26, 0], [w * 1.02, 1.0, w * 0.99], SNOWBALL, decal="xm_snow",
             wrap=True),
        # a knitted scarf, the tails hanging off to one side
        part("cyl", [0, -1.06, 0], [w + 0.10, 0.26, w * 0.97 + 0.10], "#c4281c", decal="knit",
             wrap=True),
        part("rbox", [0.46, -1.30, 0.92], [0.22, 0.56, 0.08], "#c4281c", [0.15, 0.4, 0.15],
             decal="knit"),
        part("rbox", [0.62, -1.24, 0.84], [0.22, 0.44, 0.08], "#2a8a4a", [0.10, 0.6, 0.35],
             decal="knit"),
        # coal eyes, a carrot, a coal smile
        part("sph", [0.24, -0.24, 0.90], [0.18, 0.18, 0.10], COAL),
        part("sph", [-0.24, -0.24, 0.90], [0.18, 0.18, 0.10], COAL),
        place("carrot", [0, -0.46, 0.94], [0.18, 0.56, 0.18], CARROT, anchor=[0, 1, 0],
              r=[-PI / 2 + 0.12, 0.10, 0]),
        # a battered top hat with a sprig of holly
        part("cyl", [0.10, 0.48, -0.05], [1.00, 0.05, 0.96], COAL, [0, 0, -0.12]),
        part("cyl", [0.13, 0.78, -0.05], [0.66, 0.56, 0.64], COAL, [0, 0, -0.12], decal="felt",
             wrap=True),
        part("cyl", [0.11, 0.58, -0.05], [0.68, 0.12, 0.66], "#c4281c", [0, 0, -0.12]),
    ]
    for n, x in enumerate((-0.30, -0.15, 0.0, 0.15, 0.30)):
        parts.append(part("sph", [x, -0.70 + abs(x) * -0.25 + 0.08, 0.96], [0.10, 0.10, 0.07], COAL))
    parts += _holly([-0.28, 0.62, 0.30], 0.55, yaw=0.3)
    return parts


@XM22.hat("earmuffs", "Fluffy Earmuffs",
          "Two clouds of white fluff on a red band, and a snowflake on each. You "
          "will not hear a single snowball coming.", "uncommon", hair="show")
def _():
    red = "#c4281c"
    parts = [
        part("rbox", [0, 0.05, 0], [1.22, 0.08, 0.18], red),
        part("rbox", [0.71, -0.03, 0], [0.32, 0.08, 0.18], red, [0, 0, -0.80]),
        part("rbox", [-0.71, -0.03, 0], [0.32, 0.08, 0.18], red, [0, 0, 0.80]),
        part("rbox", [0.81, -0.30, 0], [0.08, 0.46, 0.18], red),
        part("rbox", [-0.81, -0.30, 0], [0.08, 0.46, 0.18], red),
    ]
    for s in (1, -1):
        parts += [
            part("cyl", [0.83 * s, -0.62, 0], [0.48, 0.10, 0.48], red, [0, 0, PI / 2]),
            part("sph", [0.97 * s, -0.62, 0], [0.34, 0.58, 0.58], SNOWBALL, decal="fur", wrap=True),
            place("snowflake", [1.15 * s, -0.62, 0], 0.30, FROST, r=[0, PI / 2 * s, 0], m="metal"),
        ]
    return parts


@XM22.hat("snowdrift_robin", "Snowdrift & Robin",
          "You stood still for one minute in the first snow of the year and this "
          "happened. The robin has moved in. The robin is not moving out.", "uncommon")
def _():
    brown, breast = "#7a5a3a", "#e2552a"
    parts = [
        cap(-0.26, 0.10, SNOWBALL, decal="xm_snow", wrap=True),
        part("sph", [0, 0.12, 0], [1.40, 0.56, 1.30], SNOWBALL, decal="xm_snow", wrap=True),
        part("sph", [0.34, 0.26, -0.16], [0.80, 0.50, 0.70], SNOWBALL, decal="xm_snow", wrap=True),
        part("sph", [-0.36, 0.20, 0.18], [0.66, 0.40, 0.62], SNOWBALL, decal="xm_snow", wrap=True),
        part("sph", [-0.10, 0.40, -0.24], [0.56, 0.40, 0.50], SNOWBALL, decal="xm_snow", wrap=True),
    ]
    # lumps of snow spilling over the edge all round
    parts += around(11, 0.76, -0.04, lambda a, x, z: part(
        "sph", [x * 1.02, -0.06 + 0.04 * math.sin(a * 3), z], [0.46, 0.34, 0.46], SNOWBALL,
        decal="xm_snow", wrap=True), start=0.2)
    # icicles off the side and the back of the drift
    for x, z, h in ((0.83, -0.30, 0.30), (0.83, 0.12, 0.22), (-0.83, -0.20, 0.26),
                    (-0.83, 0.16, 0.20), (-0.40, -0.80, 0.30), (0.05, -0.80, 0.24),
                    (0.42, -0.80, 0.34)):
        parts.append(place("icicle", [x, -0.24, z], [0.11, h, 0.11], ICE, anchor=[0, 1, 0],
                           m="glass"))
    # the robin, on top of the drift
    rb = [0.18, 0.62, 0.08]
    parts += [
        part("sph", [rb[0], rb[1], rb[2]], [0.34, 0.30, 0.42], brown),
        part("sph", [rb[0], rb[1] - 0.02, rb[2] + 0.12], [0.26, 0.24, 0.16], breast),
        part("sph", [rb[0], rb[1] + 0.18, rb[2] + 0.12], [0.22, 0.22, 0.22], brown),
        part("sph", [rb[0], rb[1] + 0.16, rb[2] + 0.20], [0.14, 0.12, 0.08], breast),
        place("cone", [rb[0], rb[1] + 0.18, rb[2] + 0.28], [0.05, 0.10, 0.05], "#e8b23a",
              r=[PI / 2, 0, 0]),
        part("sph", [rb[0] + 0.07, rb[1] + 0.22, rb[2] + 0.21], [0.04, 0.04, 0.03], COAL),
        part("sph", [rb[0] - 0.07, rb[1] + 0.22, rb[2] + 0.21], [0.04, 0.04, 0.03], COAL),
        part("rbox", [rb[0], rb[1] + 0.02, rb[2] - 0.26], [0.14, 0.04, 0.24], "#5a3e26",
             [-0.5, 0, 0]),
        part("cyl", [rb[0] + 0.06, rb[1] - 0.17, rb[2]], [0.02, 0.10, 0.02], "#3a2a1a"),
        part("cyl", [rb[0] - 0.06, rb[1] - 0.17, rb[2]], [0.02, 0.10, 0.02], "#3a2a1a"),
    ]
    parts += _holly([-0.30, 0.42, 0.34], 0.7, yaw=-0.4)
    return parts


@XM22.hat("lost_mitten", "The Lost Mitten",
          "Somebody lost one mitten in the first snow, and it was enormous, so now "
          "it is a hat. The string it hung on is still attached, in case you lose "
          "it again.", "uncommon")
def _():
    red, cream = "#b8222a", "#f4ecdc"
    shell = dome(-0.28, 1.30, red, decal="knit", wrap=True)
    return [
        shell,
        ringband(-0.08, 0.36, cream, decal="knit", wrap=True),
        # the thumb, sticking out at a jaunty angle
        place("capsule", [0.50, 0.32, 0.10], [0.36, 0.30, 0.36], red, anchor=[0, 0, 0],
              r=[0.2, 0, -0.80], decal="knit", wrap=True),
        # a white knitted snowflake on the back of the hand
        place("snowflake", [0, 0.42, 0.80], 0.52, cream, r=[-0.42, 0, 0]),
        # the string, looping off the cuff
        place("arch", [-0.80, -0.36, 0.0], [0.30, 0.70, 1.0], "#e8e0d0", anchor=[0, 1, 0],
              r=[0, PI / 2, PI]),
        part("cyl", [-0.84, -0.62, -0.26], [0.04, 0.52, 0.04], "#e8e0d0", [0.4, 0, 0.1]),
    ]


@XM22.hat("snow_day_umbrella", "Snow Day Umbrella",
          "An umbrella hat, for keeping the snow off. It has kept a great deal of "
          "snow off. All of it is still on the umbrella.", "rare", hair="show")
def _():
    parts = [
        band(-0.22, 0.12, "#2a2a30", grow=0.02),
        part("cyl", [0, 0.30, 0], [0.08, 0.66, 0.08], "#c9ced6", m="metal"),
        part("rbox", [0, -0.02, 0], [0.30, 0.10, 0.30], "#2a2a30"),
        place("hemi", [0, 0.58, 0], [2.70, 1.30, 2.70], "#c4281c", anchor=[0, 0, 0],
              decal="xm_umbrella", wrap=True),
        # the snow on top of it, heaped
        place("hemi", [0, 0.66, 0], [2.24, 1.56, 2.24], SNOWBALL, anchor=[0, 0, 0],
              decal="xm_snow", wrap=True),
        part("sph", [0.24, 1.36, 0.10], [0.80, 0.46, 0.74], SNOWBALL, decal="xm_snow", wrap=True),
        part("sph", [-0.26, 1.30, -0.20], [0.66, 0.40, 0.62], SNOWBALL, decal="xm_snow", wrap=True),
        part("sph", [0, 1.56, 0], [0.34, 0.30, 0.34], SNOWBALL, decal="xm_snow", wrap=True),
        part("sph", [0, 1.72, 0], [0.12, 0.12, 0.12], GOLD, m="metal"),
    ]
    # ribs under the canopy, and icicles off every tip
    for k in range(8):
        a = k * TAU / 8 + TAU / 16
        tip = [math.sin(a) * 1.32, 0.58, math.cos(a) * 1.32]
        mid = [tip[0] / 2, 0.61, tip[2] / 2]
        parts.append(part("cyl", mid, [0.03, 1.33, 0.03], "#c9ced6", [PI / 2 + 0.05, a, 0], m="metal"))
        parts.append(part("sph", tip, [0.07, 0.07, 0.07], "#c9ced6", m="metal"))
        parts.append(place("icicle", [tip[0], 0.56, tip[2]], [0.14, 0.32 + (k % 3) * 0.10, 0.14],
                           ICE, anchor=[0, 1, 0], m="glass"))
    return parts


@XM22.hat("cocoa_mug", "Bottomless Cocoa",
          "A mug of hot cocoa the size of your head, cream, marshmallows and all, "
          "kept warm on a knitted cosy. It has never once gone cold. It has never "
          "once been drunk.", "rare")
def _():
    parts = [
        cap(-0.24, 0.10, "#2a8a4a", decal="knit", wrap=True),
        band(-0.20, 0.10, "#f4ecdc", grow=0.04, decal="knit", wrap=True),
    ]
    parts += _mug([0, 0.08, 0], 1.80, handle_side=1)
    parts.append(place("cane", [-0.36, 1.16, -0.06], [0.80, 1.10, 0.80], WHITE, anchor=[0, 0, 0],
                       r=[0, 0.4, 0.30], decal="candy", wrap=True))
    return parts


@XM22.back("toboggan", "Old Toboggan",
           "A wooden toboggan with a proper curl at the front and a red pull-rope, "
           "worn on your back between runs. It has a scratch for every hill in "
           "Blockhaven.", "rare")
def _():
    wood, dark = "#b07a44", "#7a4a26"
    parts = [
        part("rbox", [0, 0.06, -0.30], [1.00, 2.10, 0.08], wood, [-0.10, 0, 0], decal="planks",
             wrap=True),
        # the curl at the top, rolled back
        part("cyl", [0, 1.16, -0.52], [0.40, 1.00, 0.40], wood, [0, 0, PI / 2], decal="planks",
             wrap=True),
        part("rbox", [0, 1.03, -0.44], [1.00, 0.24, 0.10], wood, [-0.9, 0, 0], decal="planks"),
        # side rails and slats
        part("rbox", [0.46, 0.04, -0.37], [0.08, 2.00, 0.08], dark, [-0.10, 0, 0]),
        part("rbox", [-0.46, 0.04, -0.37], [0.08, 2.00, 0.08], dark, [-0.10, 0, 0]),
        # the pull-rope looped through the curl and down one side
        part("torus", [0, 1.16, -0.52], [0.52, 1.0, 0.52], "#c4281c", [0, 0, PI / 2]),
        part("cyl", [0.54, 0.62, -0.46], [0.05, 1.10, 0.05], "#c4281c", [-0.12, 0, 0.06]),
        part("cyl", [-0.54, 0.62, -0.46], [0.05, 1.10, 0.05], "#c4281c", [-0.12, 0, -0.06]),
        part("rbox", [0, -0.94, -0.18], [0.96, 0.06, 0.10], dark, [-0.10, 0, 0]),
        *straps("#3a2a1c", 0.34, 0.12),
    ]
    for y in (-0.55, -0.05, 0.45):
        parts.append(part("rbox", [0, y, -0.37 + (y * 0.1)], [0.96, 0.08, 0.06], dark, [-0.10, 0, 0]))
    return parts


@XM22.back("snowman_hitchhiker", "Snowman Hitchhiker",
           "A little snowman riding in a basket on your back, waving at everyone you "
           "pass. He is not heavy. He is a little bit cold. He says hello.", "legendary")
def _():
    wicker = "#9a6a3a"
    parts = [
        part("cyl", [0, 0.62, -0.55], [0.98, 0.80, 0.86], wicker, decal="xm_wicker", wrap=True),
        part("torus", [0, 1.02, -0.55], [1.02, 0.50, 0.90], shade(wicker, 0.8)),
        part("torus", [0, 0.24, -0.55], [1.02, 0.50, 0.90], shade(wicker, 0.8)),
        *straps("#5a3a22", 0.34, 0.12),
        part("rbox", [0, 0.62, -0.10], [0.70, 0.20, 0.10], "#5a3a22"),
        # a cushion of snow for him to sit in
        place("hemi", [0, 1.00, -0.55], [0.90, 0.30, 0.78], SNOWBALL, anchor=[0, 0, 0],
              decal="xm_snow", wrap=True),
    ]
    parts += _snowman([0.06, 0.92, -0.58], 1.0, facing=0.25, wave=True)
    return parts


@XM22.hairdo("frosted_spikes", "Frost-Tipped Spikes",
             "Spiked up before the first snow and frozen that way. The tips have not "
             "thawed since, and neither has the snowflake.", "uncommon")
def _():
    c = "#6b4a2a"
    parts = [place("hairshort", [0, 0, 0], [1.03, 1.03, 1.03], c, anchor=[0, 0, 0],
                   decal="strands", wrap=True)]
    spikes = [(0.0, 0.18, 0.0, 0.48), (0.22, 0.05, -0.2, 0.40), (-0.22, 0.05, 0.2, 0.40),
              (0.20, -0.20, -0.35, 0.36), (-0.20, -0.20, 0.35, 0.36), (0.0, -0.30, 0.0, 0.38),
              (0.32, 0.25, -0.5, 0.32), (-0.32, 0.25, 0.5, 0.32), (0.0, 0.34, 0.0, 0.34)]
    for x, z, lean, h in spikes:
        r = [-0.25 - z * 0.6, 0, lean * 0.8]
        base = [x, 0.47, z]
        tip = rotate([0, h, 0], r)
        parts.append(place("cone", base, [0.20, h, 0.20], c, anchor=[0, -0.5, 0], r=r))
        parts.append(place("cone", [base[0] + tip[0] * 0.78, base[1] + tip[1] * 0.78,
                                    base[2] + tip[2] * 0.78],
                           [0.09, h * 0.30, 0.09], "#f2faff", anchor=[0, -0.2, 0], r=r))
    parts.append(place("snowflake", [0.40, 0.42, 0.30], 0.20, "#f2faff", r=[-0.3, 0.6, 0]))
    return parts


@XM22.hairdo("flurry_bob", "Flurry Bob",
             "A neat bob with a dusting of fresh snow on top and two snowflake clips "
             "that sparkle when the light catches them.", "rare")
def _():
    c = "#3e2418"
    parts = [place("hairbob", [0, 0, 0], [1.04, 1.04, 1.04], c, anchor=[0, 0, 0],
                   decal="strands", wrap=True)]
    for s in (1, -1):
        parts.append(place("snowflake", [0.56 * s, 0.18, 0.22], 0.24, "#e8f6ff",
                           r=[0, PI / 2 * s, 0.3 * s], m="neon"))
    for n in range(9):
        a = n * 2.39996
        rr = 0.12 + (n % 3) * 0.12
        parts.append(part("sph", [math.sin(a) * rr, 0.54 - rr * 0.12, math.cos(a) * rr - 0.04],
                          [0.12, 0.05, 0.12], SNOWBALL))
    return parts


XM22.face("rosy_cheeks", "Rosy Cheeks",
          "Cheeks gone pink from the cold, a smile you cannot get off, and your "
          "breath coming out in little clouds.", [
              {"k": "arc", "x": -0.20, "y": -0.10, "r": 0.07, "a0": 0.55, "a1": 0.95, "w": 0.035,
               "c": "#1a1a1a"},
              {"k": "arc", "x": 0.20, "y": -0.10, "r": 0.07, "a0": 0.55, "a1": 0.95, "w": 0.035,
               "c": "#1a1a1a"},
              {"k": "ellipse", "x": -0.29, "y": 0.04, "w": 0.15, "h": 0.08, "c": "#ff8fa3"},
              {"k": "ellipse", "x": 0.29, "y": 0.04, "w": 0.15, "h": 0.08, "c": "#ff8fa3"},
              {"k": "arc", "x": 0, "y": 0.06, "r": 0.11, "a0": 0.08, "a1": 0.42, "w": 0.035,
               "c": "#1a1a1a"},
              {"k": "ellipse", "x": 0.30, "y": 0.24, "w": 0.09, "h": 0.07, "c": "#eef8ff"},
              {"k": "ellipse", "x": 0.37, "y": 0.20, "w": 0.08, "h": 0.07, "c": "#eef8ff"},
              {"k": "ellipse", "x": 0.42, "y": 0.26, "w": 0.07, "h": 0.06, "c": "#eef8ff"},
          ])
XM22.face("snowflake_catcher", "Catching Snowflakes",
          "Eyes up, tongue out, waiting for the one with your name on it. It has "
          "just landed.", [
              {"k": "ellipse", "x": -0.19, "y": -0.13, "w": 0.13, "h": 0.15, "c": "#ffffff"},
              {"k": "ellipse", "x": 0.19, "y": -0.13, "w": 0.13, "h": 0.15, "c": "#ffffff"},
              {"k": "ellipse", "x": -0.18, "y": -0.18, "w": 0.07, "h": 0.07, "c": "#1a1a1a"},
              {"k": "ellipse", "x": 0.20, "y": -0.18, "w": 0.07, "h": 0.07, "c": "#1a1a1a"},
              {"k": "ellipse", "x": 0, "y": 0.13, "w": 0.18, "h": 0.15, "c": "#3a1a1a"},
              {"k": "ellipse", "x": 0, "y": 0.21, "w": 0.13, "h": 0.12, "c": "#ff6f8a"},
              {"k": "star", "x": 0, "y": 0.21, "r": 0.045, "n": 6, "i": 0.35, "c": "#ffffff"},
              {"k": "star", "x": 0.30, "y": -0.36, "r": 0.04, "n": 6, "i": 0.35, "c": "#bfe6ff"},
              {"k": "star", "x": -0.34, "y": -0.30, "r": 0.03, "n": 6, "i": 0.35, "c": "#bfe6ff"},
          ], "rare")
XM22.shirt("fair_isle", "Fair Isle Snow Sweater",
           "Hand-knitted, navy and cream, with a snowflake on the chest and a yoke of "
           "little stars. Your nan says it will fit you next year.",
           {"torso": "#1b2f5a", "arms": "#1b2f5a", "decal": "xm_tee_yoke", "weave": "xm_fairisle",
            "stripe": "#f4ecdc"}, "rare")
XM22.pants("snow_pants", "Puffy Snow Pants",
           "Quilted, waterproof and so padded you can sit down in a snowdrift for an "
           "hour. Walking is harder.",
           {"legs": "#3a6fb0", "weave": "xm_quilt", "cuff": "#2a2a30"})
XM22.belt("snowball_belt", "Snowball Bandolier",
          "A knitted belt with two pouches, each holding one perfectly packed "
          "snowball. For emergencies.",
          {"band": "#e8f0fa", "buckle": FROST, "width": 0.22, "weave": "knit", "pouch": True})


@XM22.weapon("snowball_gatling", "Snowball Gatling",
             "A hand-cranked gatling gun with a hopper full of snow. Every snowball "
             "that lands chills; six in a row and the target freezes solid.",
             {"kind": "projectile", "projectile": "snowball", "damage": 7, "splash": 0,
              "splash_damage": 0, "rpm": 420, "mag": 48, "reload": 3.2, "speed": 115,
              "range": 220, "auto": True, "sound": "throw", "recoil": 0.3, "reserve": 192,
              "gravity_scale": 0.55, "self_damage": 0.0, "knockback": 1,
              "on_hit": {"freeze": [0.10, 6, 1.6]}, "held": {"speed": -0.15},
              "trail_colors": ["#ffffff", "#bfe6ff"]},
             [["+", "Every snowball chills; six in a row freeze the target solid for 1.6 "
                    "seconds"],
              ["+", "48 snowballs, seven a second"],
              ["-", "Only 7 damage a snowball, and they drop with distance"],
              ["-", "You move 15% slower while you lug it about"]], rarity="legendary",
             proj=lambda: [part("sph", [0, 0, 0], [0.46, 0.46, 0.46], SNOWBALL, decal="xm_snow",
                                wrap=True)],
             two_handed=True)
def _():
    steel = "#9fc4e0"
    parts = [
        part("rbox", [0, -0.32, -0.08], [0.18, 0.46, 0.22], "#5a3a22", [0.25, 0, 0]),
        part("rbox", [0, -0.06, -0.36], [0.22, 0.24, 0.50], "#5a3a22"),
        part("cyl", [0, 0.05, 0.30], [0.54, 0.56, 0.54], "#c4281c", [PI / 2, 0, 0]),
        part("torus", [0, 0.05, 0.02], [0.56, 0.6, 0.56], GOLD, [PI / 2, 0, 0], m="metal"),
        part("torus", [0, 0.05, 0.58], [0.56, 0.6, 0.56], GOLD, [PI / 2, 0, 0], m="metal"),
        part("cyl", [0, 0.05, 1.50], [0.48, 0.08, 0.48], steel, [PI / 2, 0, 0], m="metal"),
        part("cyl", [0, 0.05, 1.05], [0.40, 0.06, 0.40], steel, [PI / 2, 0, 0], m="metal"),
        part("cyl", [0, 0.05, 1.05], [0.08, 1.10, 0.08], steel, [PI / 2, 0, 0], m="metal"),
        # the hopper of snow, heaped with snowballs
        part("cyl", [0, 0.50, 0.30], [0.50, 0.36, 0.50], "#3a6fb0", decal="snowflakes",
             wrap=True),
        part("torus", [0, 0.68, 0.30], [0.54, 0.4, 0.54], GOLD, m="metal"),
        # the crank
        part("cyl", [0.34, 0.05, 0.30], [0.06, 0.20, 0.06], steel, [0, 0, PI / 2], m="metal"),
        part("rbox", [0.44, -0.08, 0.30], [0.05, 0.30, 0.05], steel, m="metal"),
        part("cyl", [0.50, -0.22, 0.30], [0.08, 0.16, 0.08], "#c4281c", [0, 0, PI / 2]),
    ]
    for k in range(6):
        a = k * TAU / 6
        parts.append(part("cyl", [math.sin(a) * 0.15, 0.05 + math.cos(a) * 0.15, 1.05],
                          [0.10, 1.10, 0.10], steel, [PI / 2, 0, 0], m="metal"))
    for k, (x, z) in enumerate(((0, 0.30), (0.12, 0.20), (-0.12, 0.38), (0.06, 0.42), (-0.08, 0.18))):
        parts.append(part("sph", [x, 0.74 + (k % 2) * 0.06, z], [0.16, 0.16, 0.16], SNOWBALL))
    return parts


@XM22.weapon("icicle_crossbow", "Icicle Crossbow",
             "A crossbow strung with frost that fires one long icicle at a time. It "
             "goes clean through the first few people in its way, and it hits hardest "
             "from a long way off.",
             {"kind": "projectile", "projectile": "icicle", "damage": 40, "headshot": 1.5,
              "splash": 0, "splash_damage": 0, "rpm": 60, "mag": 1, "reload": 1.5,
              "speed": 170, "range": 400, "auto": False, "sound": "throw", "recoil": 1.2,
              "reserve": 30, "gravity_scale": 0.25, "self_damage": 0.0, "knockback": 4,
              "pierce_players": 3, "far": {"dist": 40, "bonus": 0.35},
              "near": {"dist": 12, "bonus": -0.30}, "on_hit": {"slow": [0.25, 1.5]},
              "tracer": "#bfe6ff", "trail_colors": ["#ffffff", "#bfe6ff"]},
             [["+", "Each icicle passes through up to three people"],
              ["+", "35% more damage at 40 studs and beyond; chills whoever it hits"],
              ["-", "30% less damage within 12 studs"],
              ["-", "One icicle, then a reload"]], rarity="legendary",
             proj=lambda: [place("icicle", [0, 0, 0], [0.22, 1.40, 0.22], ICE, r=[-PI / 2, 0, 0],
                                 m="glass"),
                           part("cyl", [0, 0, -0.10], [0.06, 1.0, 0.06], "#ffffff", [PI / 2, 0, 0],
                                m="neon", a=0.7)])
def _():
    wood, frost = "#5a3a22", "#cfeaff"
    return [
        part("rbox", [0, -0.02, 0.32], [0.16, 0.16, 1.40], wood, decal="planks"),
        part("rbox", [0, -0.30, -0.08], [0.16, 0.42, 0.20], wood, [0.35, 0, 0]),
        part("rbox", [0, -0.06, -0.46], [0.18, 0.28, 0.30], wood),
        place("arch", [0, 0.02, 0.92], [1.40, 0.62, 1.4], frost, anchor=[0, 0, 0],
              r=[PI / 2, 0, 0], m="metal"),
        part("box", [0.35, 0.05, 0.735], [0.79, 0.02, 0.02], "#ffffff", [0, -0.487, 0]),
        part("box", [-0.35, 0.05, 0.735], [0.79, 0.02, 0.02], "#ffffff", [0, 0.487, 0]),
        place("icicle", [0, 0.10, 1.00], [0.14, 1.10, 0.14], ICE, r=[-PI / 2, 0, 0], m="glass"),
        place("gem", [0, 0.11, 0.30], [0.14, 0.14, 0.14], FROST, m="glass"),
        place("gem", [0, 0.11, 0.05], [0.10, 0.10, 0.10], FROST, m="glass"),
        part("rbox", [0, 0.12, 0.55], [0.06, 0.10, 0.10], "#9fc4e0", m="metal"),
    ]


@XM22.weapon("snow_globe", "Snow Globe Grenade",
             "Shake it, throw it, and the glass bursts into a blizzard the size of a "
             "room: everybody on the other side caught in it is slowed and cannot "
             "jump, while your team inside it slowly warms up.",
             {"kind": "deploy", "cooldown": 24, "sound": "throw",
              "deploy": {"type": "dome", "thrown": True, "throw": 26, "radius": 9.0,
                         "secs": 7.0, "limit": 1, "scale": 1.6, "color": "#dff4ff",
                         "particle": "flake", "name": "Blizzard",
                         "enemy": {"slow": [0.45, 1.0], "jumpless": 1.0},
                         "ally": {"regen": [4, 1.0]}}},
             [["+", "A 9 stud blizzard for 7 seconds: enemies inside are 45% slower and "
                    "cannot jump"],
              ["+", "Teammates inside heal 4 a second"],
              ["-", "Does no damage at all"],
              ["-", "24 second cooldown"]], rarity="legendary",
             deploy=lambda: [part("cyl", [0, 0.16, 0], [1.10, 0.32, 1.10], LACQUER),
                             part("cyl", [0, 0.33, 0], [1.14, 0.04, 1.14], GOLD, m="metal"),
                             place("hemi", [0, 0.34, 0], [0.96, 0.24, 0.96], SNOWBALL,
                                   anchor=[0, 0, 0]),
                             place("tree", [-0.18, 0.36, 0], [0.34, 0.54, 0.34], "#2f6a3e",
                                   anchor=[0, 0, 0]),
                             place("star", [-0.18, 0.94, 0], 0.12, GOLD, m="neon")]
             + _snowman([0.22, 0.38, 0.06], 0.30))
def _():
    return [
        part("cyl", [0, -0.02, 0.32], [0.52, 0.18, 0.52], LACQUER),
        part("cyl", [0, 0.08, 0.32], [0.54, 0.03, 0.54], GOLD, m="metal"),
        part("sph", [0, 0.34, 0.32], [0.50, 0.50, 0.50], "#e8f6ff", m="glass", a=0.25),
        place("hemi", [0, 0.09, 0.32], [0.42, 0.12, 0.42], SNOWBALL, anchor=[0, 0, 0]),
        place("tree", [-0.07, 0.10, 0.30], [0.16, 0.26, 0.16], "#2f6a3e", anchor=[0, 0, 0]),
        part("sph", [0.09, 0.16, 0.36], [0.10, 0.10, 0.10], SNOWBALL),
        part("sph", [0.09, 0.25, 0.36], [0.07, 0.07, 0.07], SNOWBALL),
        part("sph", [0.06, 0.46, 0.30], [0.03, 0.03, 0.03], "#ffffff"),
        part("sph", [-0.08, 0.42, 0.38], [0.03, 0.03, 0.03], "#ffffff"),
        part("sph", [0.12, 0.36, 0.22], [0.03, 0.03, 0.03], "#ffffff"),
    ]


@XM22.gear("hot_cocoa", "Hot Cocoa",
           "A mug of cocoa with cream and marshmallows on top. It warms you right "
           "through, slowly, and there is always enough to pass round.",
           {"kind": "consume", "cooldown": 28, "sound": "drink",
            "consume": {"heal": 40, "over": 8.0, "share": 12}},
           [["+", "Heals you 40 over 8 seconds"],
            ["+", "Teammates within 12 studs get a 20 health sip straight away"],
            ["-", "It takes its time: none of it is instant for you"],
            ["-", "28 second cooldown"]], rarity="rare")
def _():
    return _mug([0, -0.12, 0.30], 0.42, handle_side=-1)


XM22.effect("snowglobe_swirl", name="Snow Globe", rate=7.0, life=[2.4, 3.2],
            size=[0.14, 0.26], grow=0.0, gravity=-0.25, spread=0.1, rise=[0.1, 0.35],
            blend="normal", spin=1.2, colors=["#ffffff", "#e8f6ff", "#bfe6ff"],
            shapes=["flake", "flake", "flake", "flake", "snowman", "tree"], radius=1.0,
            orbit=1.5, wobble=0.3)
XM22.effect("fresh_powder", name="Fresh Powder", rate=10.0, life=[1.0, 1.6],
            size=[0.20, 0.42], grow=0.25, gravity=-1.8, spread=0.9, rise=[1.0, 1.6],
            blend="normal", spin=2.0, colors=["#ffffff", "#f2faff", "#cfe8ff"],
            shapes=["puff", "puff", "flake"], radius=0.5)
XM22.opening(
    sky={"top": "#0c1830", "horizon": "#3a5a8a", "sun": [0.3, 0.8, 0.5], "clouds": 0,
         "tint": "#dff0ff"},
    ambient="#8aa8d0", beam="#e8f6ff", seep="frostbite", after="snowglobe_swirl",
    burst=["#ffffff", "#bfe6ff", "#8fd0ff", "#ff5a5a"],
    pieces=[{"shape": "flake", "colors": ["#ffffff", "#dff4ff", "#bfe6ff"], "blend": "normal"},
            {"shape": "snowman", "colors": ["#ffffff", "#f2faff"], "blend": "normal"},
            {"shape": "mitten", "colors": ["#c4281c", "#2a8a4a"], "blend": "normal"},
            {"shape": "star", "colors": ["#fff3b0", "#ffd24a"], "blend": "add"}],
    backdrop="xm_snowfall", title_wait="Give it a good shake...",
    title_shake="Here comes the snow...")
XM22.award("Frostfall", ["Snowflake Spotter", "Snowball Thrower", "Snowman Builder",
                         "Sledge Captain", "Blizzard Chaser", "Spirit of the First Snow"],
           "Opened Snow Globe Crates during Frostfall, Christmas 2022.", "em_snowflake",
           "flake")
XM22.bundle("pair", "Globe and Key", 1, 1050, "One Snow Globe Crate, one Snowflake Key.")
XM22.bundle("snow_day", "Snow Day", 3, 3000, "Three globes, three keys. Saves 300.")


# ============================================================ 2023
GINGER = "#b5651d"
GINGER_DARK = "#8a4a14"
ICING = "#fdf6ec"
MINT = "#3fbf8f"
GUMDROPS = ["#e8344a", "#2fbf5f", "#f2c230", "#8a4fd6", "#ff8c1a", "#2f9fe8"]
XM23 = Event(
    "christmas_2023", "christmas", 2023, "xm23",
    name="Gingerbread Junction", title="Gingerbread Junction",
    blurb="For Christmas 2023 the bakers of Blockhaven built a railway out of "
          "gingerbread: a viaduct of cookies, signal boxes iced like wedding cakes, "
          "candy-cane points and a timetable written in piped sugar. The trains never "
          "ran on time. Most of them were eaten before they left the station.",
    tagline="Mind the gap. It's full of icing.",
    starts="2023-12-01", ends="2023-12-30",
    colors={"accent": CANDY_RED, "deep": "#2a0f0c", "glow": "#ffe3b8"},
    family_effects=["starstruck", "bubbly", "candlelight_vigil", "sunbeam"],
    hero_effect="gingerbread_parade", stencil="stencil_xm23")


def _gumdrop(at, k, c, **kw):
    """A sugared gumdrop: a tall dome with a coat of sugar."""
    return place("hemi", at, [0.30 * k, 0.62 * k, 0.30 * k], c, anchor=[0, 0, 0],
                 decal="xm_sugar", wrap=True, **kw)


def _gingerman(at, k=1.0, r=None, **kw):
    """An iced gingerbread man (the flat cookie, face to +Z), thicker than the
    bare mesh so he reads as a biscuit and not a sticker."""
    return place("gingerman", at, [k, k, k * 1.8], GINGER, r=r, decal="xm_gingerface", **kw)


@XM23.crate_model("Cookie Tin Crate",
                  "A peppermint-striped cookie tin with a mint-green lid, gumdrops round "
                  "the rim, icing dripping down its sides and an iced gingerbread man "
                  "lying on top -- and a signal on the side, set to go. Holds the "
                  "Gingerbread Junction set. Needs a Peppermint Key.",
                  hinge=[0, 0.30, -0.78], keyhole=[0, -0.20, 0.84])
def _():
    parts = [
        # the tin: candy stripes, gold rims, a paper label round the back
        part("cyl", [0, -0.16, 0], [1.50, 0.90, 1.50], CANDY_RED, decal="candy", wrap=True,
             m="metal"),
        part("cyl", [0, -0.60, 0], [1.56, 0.08, 1.56], GOLD, m="metal"),
        part("cyl", [0, 0.27, 0], [1.54, 0.06, 1.54], GOLD, m="metal"),
        part("rbox", [0, -0.16, -0.76], [0.74, 0.54, 0.05], ICING),
        part("box", [0, -0.16, -0.79], [0.66, 0.50, 0.02], "#000000", [0, PI, 0],
             decal="stencil_xm23", a=-1),
        # the lid: mint, a rim of icing, the gingerbread man asleep on top
        part("cyl", [0, 0.38, 0], [1.60, 0.18, 1.60], MINT, m="metal", lid=1),
        part("cyl", [0, 0.48, 0], [1.44, 0.04, 1.44], ICING, decal="xm_icingzag", wrap=True,
             lid=1),
        _gingerman([0, 0.52, 0.0], 1.05, r=[-PI / 2, 0.35, 0], lid=1),
        # the lock: a gold plate framed in piped icing
        part("rbox", [0, -0.20, 0.76], [0.38, 0.38, 0.10], GOLD, m="metal", decal="keyhole",
             lock=1),
        part("rbox", [0, -0.20, 0.745], [0.48, 0.48, 0.06], ICING, decal="xm_icingzag"),
    ]
    # gumdrops round the lid and icing dripping off its edge
    for n in range(12):
        a = n * TAU / 12 + 0.13
        parts.append(_gumdrop([math.sin(a) * 0.70, 0.46, math.cos(a) * 0.70], 0.8,
                              GUMDROPS[n % len(GUMDROPS)], lid=1))
        if n % 2 == 0:
            parts.append(place("teardrop", [math.sin(a + 0.26) * 0.79, 0.34, math.cos(a + 0.26) * 0.79],
                               [0.12, 0.22, 0.12], ICING, anchor=[0, 1, 0], r=[PI, 0, 0], lid=1))
    # a railway signal bolted to the side: post, arm raised, lamps lit
    sx = 0.92
    parts += [
        part("cyl", [sx, 0.05, -0.10], [0.10, 1.40, 0.10], WHITE, decal="candy", wrap=True),
        part("rbox", [sx, -0.66, -0.10], [0.28, 0.08, 0.28], GINGER_DARK, decal="xm_gingerbread"),
        part("rbox", [sx + 0.20, 0.82, -0.10], [0.50, 0.12, 0.04], CANDY_RED, [0, 0, 0.6]),
        part("rbox", [sx + 0.22, 0.84, -0.075], [0.08, 0.13, 0.01], ICING, [0, 0, 0.6]),
        part("rbox", [sx, 0.64, -0.02], [0.16, 0.30, 0.10], "#2a2a30"),
        part("sph", [sx, 0.70, 0.04], [0.09, 0.09, 0.04], "#6bff9a", m="neon"),
        part("sph", [sx, 0.58, 0.04], [0.09, 0.09, 0.04], "#5a1010"),
        part("sph", [sx, 0.80, -0.10], [0.12, 0.12, 0.12], GOLD, m="metal"),
    ]
    # two candy canes crossed against the front, and holly
    parts += [
        place("cane", [-0.62, -0.62, 0.58], [0.9, 0.95, 0.9], WHITE, anchor=[0, 0, 0],
              r=[0.1, -0.6, 0.25], decal="candy", wrap=True),
        place("cane", [-0.38, -0.62, 0.72], [0.9, 0.85, 0.9], WHITE, anchor=[0, 0, 0],
              r=[0.1, PI - 0.3, -0.35], decal="candy", wrap=True),
    ]
    parts += _holly([0.46, 0.06, 0.66], 0.7, yaw=-0.3)
    return parts


@XM23.key_model("Peppermint Key",
                "A key with a wrapped peppermint for a bow and a candy cane for a "
                "shaft. Opens one Cookie Tin Crate. Tastes of mint, faintly, if you "
                "are the kind of person who licks keys.", shoulder=-0.30)
def _():
    cello = "#e8f4ff"
    return [
        part("disc", [-0.66, 0, 0], [0.62, 0.62, 0.20], WHITE, decal="xm_swirl"),
        place("cone", [-1.02, 0, 0], [0.16, 0.16, 0.16], cello, r=[0, 0, -PI / 2], m="glass",
              a=0.55),
        place("fan", [-1.08, 0, 0], [0.42, 0.40, 1.0], cello, anchor=[0, 0, 0],
              r=[0, 0, PI / 2], m="glass", a=0.55),
        place("cone", [-0.30, 0, 0], [0.16, 0.16, 0.16], cello, r=[0, 0, PI / 2], m="glass",
              a=0.55),
        part("cyl", [0.14, 0, 0], [0.10, 0.92, 0.10], WHITE, [0, 0, PI / 2], decal="candy",
             wrap=True),
        _gumdrop([0.40, -0.17, 0], 0.55, GUMDROPS[1], r=[PI, 0, 0]),
        _gumdrop([0.55, -0.20, 0], 0.62, GUMDROPS[0], r=[PI, 0, 0]),
        part("sph", [0.62, 0, 0], [0.12, 0.12, 0.12], CANDY_RED),
    ]


@XM23.hat("cookie_jar", "Cookie Jar Breakout",
          "A glass jar of gingerbread on a gingham cloth, and one of the gingerbread "
          "men has pushed the lid up and is halfway out. Run, run, as fast as you "
          "can. He has nowhere to run. He is on your head.", "legendary")
def _():
    glass = "#eef8ff"
    parts = [
        cap(-0.24, 0.06, "#c4281c", decal="xm_gingham", wrap=True),
        place("cask", [0, 0.06, 0], [1.50, 1.20, 1.50], glass, anchor=[0, 0, 0], m="glass",
              a=0.22),
        part("cyl", [0, 1.24, 0], [1.20, 0.10, 1.20], glass, m="glass", a=0.3),
        # the cookies inside: rounds and gingerbread men, stacked anyhow
        part("cyl", [0.05, 0.20, 0.05], [0.90, 0.10, 0.90], GINGER, [0.10, 0, 0.05],
             decal="xm_gingerbread"),
        part("cyl", [-0.10, 0.32, -0.10], [0.80, 0.10, 0.80], GINGER_DARK, [-0.12, 0, 0.1],
             decal="xm_gingerbread"),
        _gingerman([0.10, 0.62, 0.0], 0.62, r=[0.2, 0.3, 0.15]),
        _gingerman([-0.24, 0.58, -0.12], 0.55, r=[-0.1, -0.5, -0.3]),
        part("cyl", [0.24, 0.48, -0.26], [0.50, 0.08, 0.50], GINGER, [1.2, 0.4, 0],
             decal="xm_gingerbread"),
        # the lid, shoved up at one side
        part("cyl", [-0.12, 1.40, 0], [1.28, 0.12, 1.28], CANDY_RED, [0, 0, 0.32], m="metal"),
        part("sph", [-0.18, 1.52, 0], [0.22, 0.16, 0.22], GOLD, m="metal"),
        # and the escapee, one leg over the rim
        _gingerman([0.46, 1.52, 0.10], 0.80, r=[0, -0.25, -0.30]),
        part("sph", [0.62, 1.26, 0.40], [0.06, 0.05, 0.06], GINGER_DARK),
        part("sph", [0.40, 1.27, 0.52], [0.05, 0.04, 0.05], GINGER_DARK),
    ]
    return parts


@XM23.hat("candy_antlers", "Candy Cane Antlers",
          "Antlers made of candy canes on a red velvet band, with a bow on top. "
          "Reindeer love them. Reindeer will follow you home.", "rare", hair="show")
def _():
    red = "#a8141c"
    parts = [
        part("rbox", [0, 0.05, 0], [1.22, 0.08, 0.18], red, decal="felt"),
        part("rbox", [0.71, -0.03, 0], [0.32, 0.08, 0.18], red, [0, 0, -0.80], decal="felt"),
        part("rbox", [-0.71, -0.03, 0], [0.32, 0.08, 0.18], red, [0, 0, 0.80], decal="felt"),
        part("rbox", [0.81, -0.22, 0], [0.08, 0.30, 0.18], red),
        part("rbox", [-0.81, -0.22, 0], [0.08, 0.30, 0.18], red),
    ]
    parts += gift_bow([0, 0.14, 0.04], 0.55, "#2a8a4a", tails=False)
    for s in (1, -1):
        turn = 0.0 if s > 0 else PI
        parts += [
            place("cane", [0.40 * s, 0.06, 0], [1.6, 1.25, 1.6], WHITE, anchor=[0, 0, 0],
                  r=[0, turn, -0.28 * s], decal="candy", wrap=True),
            place("cane", [0.52 * s, 0.50, 0], [1.4, 0.70, 1.4], WHITE, anchor=[0, 0, 0],
                  r=[0, turn, -0.95 * s], decal="candy", wrap=True),
            place("cane", [0.46 * s, 0.30, 0], [1.3, 0.55, 1.3], WHITE, anchor=[0, 0, 0],
                  r=[0, PI - turn, 0.45 * s], decal="candy", wrap=True),
            part("sph", [0.40 * s, 0.10, 0], [0.16, 0.16, 0.16], GOLD, m="metal"),
        ]
    return parts


@XM23.hat("baker_toque", "Head Baker's Toque",
          "A tall pleated chef's hat, dusted with flour, with a piping bag tucked in "
          "the band and a wooden spoon for emergencies. Every cookie on the Junction "
          "passed under this hat.", "rare")
def _():
    white = "#f8f6f0"
    parts = [
        band(0.06, 0.62, white, decal="linen", wrap=True),
        place("pumpkin", [0, 0.24, 0], [2.0, 1.45, 1.94], white, anchor=[0, 0, 0],
              decal="linen", wrap=True),
        # flour, on everything
        part("sph", [0.40, 0.20, 0.72], [0.30, 0.18, 0.06], "#ffffff", a=0.7),
        part("sph", [-0.30, 0.90, 0.70], [0.24, 0.14, 0.06], "#ffffff", a=0.7),
        # the piping bag, nozzle up, and the spoon
        place("cone", [0.86, 0.36, -0.10], [0.36, 0.86, 0.36], "#f2c8d8", r=[0.1, 0, -0.30],
              decal="xm_gingham", wrap=True),
        place("cone", [1.00, 0.86, -0.06], [0.14, 0.22, 0.14], SILVER, r=[0.1, 0, -0.30],
              m="metal"),
        place("spiral", [1.06, 0.98, -0.05], [0.12, 0.12, 0.12], ICING),
        part("cyl", [-0.86, 0.40, -0.20], [0.07, 0.96, 0.07], "#b07a44", [0.2, 0, 0.25]),
        part("sph", [-0.98, 0.88, -0.10], [0.24, 0.32, 0.10], "#b07a44", [0.2, 0, 0.25]),
    ]
    return parts


@XM23.hat("wrapped_peppermint", "Wrapped Peppermint",
          "A peppermint the size of a dinner plate, still in its crinkly wrapper, "
          "worn at an angle. It has been in somebody's coat pocket since 2019.",
          "uncommon")
def _():
    cello = "#e8f4ff"
    parts = [
        part("disc", [0, 0.20, 0.02], [1.36, 1.36, 0.32], WHITE, [-PI / 2 + 0.22, 0, 0.10],
             decal="xm_swirl"),
        part("cyl", [0, 0.20, 0.02], [1.42, 0.36, 1.42], cello, [0.22, 0, 0.10], m="glass",
             a=0.35),
    ]
    for s in (1, -1):
        tip = rotate([0.74 * s, 0, 0], [0.22, 0, 0.10])
        root = [tip[0], 0.20 + tip[1], 0.02 + tip[2]]
        parts += [
            place("cone", root, [0.24, 0.20, 0.24], cello, r=[0, 0, -PI / 2 * s + 0.10],
                  m="glass", a=0.6),
            place("fan", [root[0] + 0.08 * s, root[1] + 0.02 * s * 0.1, root[2]],
                  [0.70, 0.62, 1.0], cello, anchor=[0, 0, 0],
                  r=[0, 0, -PI / 2 * s + 0.10], m="glass", a=0.55),
        ]
    return parts


@XM23.hat("gumdrop_crown", "Gumdrop Crown",
          "A crown of sugared gumdrops on a band of piped icing. The red ones go "
          "first. Nobody ever eats the green ones.", "uncommon")
def _():
    parts = [
        ringband(-0.14, 0.22, ICING, decal="xm_icingzag", wrap=True),
        ringband(-0.26, 0.06, GOLD, m="metal"),
    ]
    parts += around(9, 0.86, -0.05, lambda a, x, z: _gumdrop(
        [x, -0.05, z * 0.97], 1.20, GUMDROPS[int(round(a / (TAU / 9))) % len(GUMDROPS)]))
    parts += around(9, 0.92, -0.20, lambda a, x, z: place(
        "teardrop", [x, -0.24, z * 0.97], [0.10, 0.20, 0.10], ICING, anchor=[0, 1, 0],
        r=[PI, 0, 0]), start=TAU / 18)
    parts.append(_gumdrop([0, 0.02, 0], 2.2, GUMDROPS[0]))
    return parts


@XM23.hat("ginger_hardhat", "Gingerbread Hard Hat",
          "Regulation headwear for the Junction works crew: gingerbread, two coats of "
          "icing, and a gumdrop on top that flashes when a train is coming. It has "
          "stopped a falling candy cane. Just the one.", "uncommon")
def _():
    shell = dome(-0.30, 0.80, GINGER, t="capcrown", decal="xm_gingerbread", wrap=True)
    w = shell["s"][0]
    return [
        shell,
        place("brim", [0, -0.30, 0], [w + 0.34, 0.9, w + 0.30], GINGER_DARK, anchor=[0, 0, 0],
              decal="xm_gingerbread", wrap=True),
        place("peak", [0, -0.24, 0], [w, 1.6, w * 1.1], GINGER_DARK, anchor=[0, 0, 0]),
        ringband(-0.12, 0.14, ICING, decal="xm_icingzag", wrap=True),
        part("rbox", [0, 0.44, 0], [0.18, 0.10, 1.30], ICING, [0, 0, 0]),
        part("cyl", [0, 0.50, 0], [0.34, 0.06, 0.34], "#2a2a30"),
        _gumdrop([0, 0.52, 0], 1.10, "#ff8c1a", m="neon"),
    ]


@XM23.hat("level_crossing", "Level Crossing",
          "A candy-cane crossbuck on a headband, two gumdrop lamps blinking either "
          "side. Anyone walking into you has been warned.", "rare", hair="show")
def _():
    red = "#2a2a30"
    parts = [
        part("rbox", [0, 0.05, 0], [1.22, 0.08, 0.18], red),
        part("rbox", [0.71, -0.03, 0], [0.32, 0.08, 0.18], red, [0, 0, -0.80]),
        part("rbox", [-0.71, -0.03, 0], [0.32, 0.08, 0.18], red, [0, 0, 0.80]),
        part("rbox", [0.81, -0.22, 0], [0.08, 0.30, 0.18], red),
        part("rbox", [-0.81, -0.22, 0], [0.08, 0.30, 0.18], red),
        part("cyl", [0, 0.50, 0], [0.10, 0.92, 0.10], WHITE, decal="candy", wrap=True),
        part("rbox", [0, 1.00, 0.04], [1.30, 0.20, 0.06], WHITE, [0, 0, 0.62], decal="candy"),
        part("rbox", [0, 1.00, 0.10], [1.30, 0.20, 0.06], WHITE, [0, 0, -0.62], decal="candy"),
        part("sph", [0, 1.00, 0.14], [0.12, 0.12, 0.06], GOLD, m="metal"),
        part("rbox", [0, 0.56, 0.02], [0.92, 0.08, 0.08], "#2a2a30"),
    ]
    for s in (1, -1):
        parts += [
            part("cyl", [0.42 * s, 0.56, 0.06], [0.26, 0.10, 0.26], "#2a2a30", [PI / 2, 0, 0]),
            part("sph", [0.42 * s, 0.56, 0.12], [0.20, 0.20, 0.10], "#ff2a3a", m="neon"),
            place("hemi", [0.42 * s, 0.64, 0.12], [0.30, 0.30, 0.20], "#2a2a30", anchor=[0, 0, 0],
                  r=[0.6, 0, 0]),
        ]
    return parts


@XM23.back("candy_cane_bundle", "Candy Cane Bundle",
           "Five candy canes as tall as you are, tied together with a green bow and "
           "carried home over your shoulder. Do not stand too close to anyone with a "
           "sweet tooth.", "uncommon")
def _():
    parts = []
    for n, (x, h, turn, lean) in enumerate(((-0.30, 2.0, 0.0, 0.10), (-0.10, 2.3, PI, 0.0),
                                            (0.12, 2.15, 0.0, -0.06), (0.30, 1.9, PI, -0.12),
                                            (0.02, 1.75, 0.0, 0.04))):
        parts.append(place("cane", [x, -0.90, -0.42 - (n % 2) * 0.10], [1.8, h / 1.02, 1.8],
                           WHITE, anchor=[0, 0, 0], r=[0.08, turn, lean], decal="candy",
                           wrap=True))
    parts += [
        part("cyl", [0, -0.30, -0.46], [0.86, 0.12, 0.40], "#2a8a4a"),
        part("cyl", [0, 0.50, -0.46], [0.86, 0.12, 0.40], "#2a8a4a"),
        *straps("#2a8a4a", 0.34, 0.12),
        part("rbox", [0, 0.50, -0.20], [0.70, 0.14, 0.10], "#2a8a4a"),
    ]
    parts += gift_bow([0, 0.50, -0.70], 0.80, "#2a8a4a", yaw=PI)
    return parts


@XM23.back("oven_tray", "Fresh From the Oven",
           "A baking tray of gingerbread men still warm from the oven, worn on your "
           "back to cool, with the oven glove and the rolling pin. Somebody always "
           "takes one when you are not looking.", "rare")
def _():
    tray = "#b9c0c8"
    parts = [
        part("rbox", [0, 0.10, -0.24], [1.40, 1.70, 0.06], tray, [-0.08, 0, 0], m="metal"),
        part("rbox", [0, 0.10, -0.28], [1.48, 1.78, 0.04], shade(tray, 0.85), [-0.08, 0, 0],
             m="metal"),
        *straps("#5a3a22", 0.34, 0.12),
        # the rolling pin through the top straps
        part("cyl", [0, 1.02, -0.40], [0.20, 1.40, 0.20], "#d8a868", [0, 0, PI / 2],
             decal="planks", wrap=True),
        part("cyl", [0.84, 1.02, -0.40], [0.10, 0.30, 0.10], "#a8784a", [0, 0, PI / 2]),
        part("cyl", [-0.84, 1.02, -0.40], [0.10, 0.30, 0.10], "#a8784a", [0, 0, PI / 2]),
        # the oven glove, hung on the corner
        place("mitten", [0.78, -0.20, -0.34], [0.80, 0.72, 1.4], "#c4281c", r=[0, PI, 0.3],
              decal="xm_quilt"),
    ]
    for n, (x, y, turn) in enumerate(((-0.38, 0.52, 0.1), (0.36, 0.56, -0.1), (-0.40, -0.18, -0.08),
                                      (0.34, -0.20, 0.12), (0.0, 0.16, 0.0))):
        z = -0.32 - (y + 0.10) * 0.08
        parts.append(_gingerman([x, y + 0.06, z], 0.62, r=[0.08, PI, turn]))
    for n, (x, h) in enumerate(((-0.30, 0.34), (0.20, 0.42), (0.0, 0.28))):
        parts.append(place("teardrop", [x, 1.14 + n * 0.12, -0.50], [0.14, h, 0.14], "#ffffff",
                           a=0.35))
    return parts


@XM23.hairdo("piped_icing", "Piped Icing",
             "Hair piped on like royal icing: a big rosette on top and a scatter of "
             "sprinkles. Do not stand near the oven.", "rare")
def _():
    c = "#fff2e0"
    parts = [place("hairmid", [0, 0, 0], [1.04, 1.04, 1.04], c, anchor=[0, 0, 0],
                   decal="strands", wrap=True),
             # the rosette, piped in rings from a base that sits on the hair
             place("hemi", [0, 0.50, -0.02], [0.86, 0.60, 0.86], c, anchor=[0, 0, 0]),
             place("spiral", [0, 0.62, -0.02], [0.70, 0.40, 0.70], c, anchor=[0, 0, 0]),
             place("spiral", [0, 0.92, -0.02], [0.48, 0.30, 0.48], c, anchor=[0, 0, 0]),
             place("teardrop", [0, 1.18, -0.02], [0.26, 0.30, 0.26], c, anchor=[0, 0, 0])]
    for n in range(14):
        a = n * 2.39996
        rr = 0.12 + (n % 4) * 0.09
        y = 0.50 + 0.30 * math.sqrt(max(0.0, 1.0 - (rr / 0.45) ** 2)) + 0.01
        parts.append(part("rbox", [math.sin(a) * rr, y, math.cos(a) * rr - 0.02],
                          [0.10, 0.03, 0.03], GUMDROPS[n % len(GUMDROPS)], [0.3, a * 1.7, 0.2]))
    return parts


@XM23.hairdo("licorice_twists", "Licorice Twists",
             "Two long red licorice twists for pigtails, tied off with gumdrops. "
             "Chewier than they look.", "uncommon")
def _():
    c = "#5a2a1a"
    parts = [place("hairmid", [0, 0, 0], [1.03, 1.03, 1.03], c, anchor=[0, 0, 0],
                   decal="strands", wrap=True)]
    for s in (1, -1):
        parts += [
            _gumdrop([0.50 * s, -0.10, -0.18], 0.55, GUMDROPS[1 if s > 0 else 2], r=[PI, 0, 0]),
            part("cyl", [0.54 * s, -0.56, -0.20], [0.17, 0.90, 0.17], "#c4182a", [0.08, 0, 0.06 * s],
                 decal="xm_licorice", wrap=True),
            part("sph", [0.57 * s, -1.02, -0.22], [0.17, 0.12, 0.17], "#c4182a"),
        ]
    return parts


XM23.face("iced_smile", "Iced Smile",
          "Two dots, a squiggle and a pair of pink cheeks, piped on in royal icing. "
          "Exactly what the cookies have.", [
              {"k": "ellipse", "x": -0.19, "y": -0.13, "w": 0.10, "h": 0.10, "c": "#fdf6ec"},
              {"k": "ellipse", "x": 0.19, "y": -0.13, "w": 0.10, "h": 0.10, "c": "#fdf6ec"},
              {"k": "ellipse", "x": -0.19, "y": -0.13, "w": 0.05, "h": 0.05, "c": "#3a1a0a"},
              {"k": "ellipse", "x": 0.19, "y": -0.13, "w": 0.05, "h": 0.05, "c": "#3a1a0a"},
              {"k": "arc", "x": -0.10, "y": 0.06, "r": 0.10, "a0": 0.05, "a1": 0.45, "w": 0.045,
               "c": "#fdf6ec"},
              {"k": "arc", "x": 0.10, "y": 0.06, "r": 0.10, "a0": 0.05, "a1": 0.45, "w": 0.045,
               "c": "#fdf6ec"},
              {"k": "ellipse", "x": -0.32, "y": 0.04, "w": 0.09, "h": 0.09, "c": "#ff8fa3"},
              {"k": "ellipse", "x": 0.32, "y": 0.04, "w": 0.09, "h": 0.09, "c": "#ff8fa3"},
          ])
XM23.face("sugar_rush", "Sugar Rush",
          "Stars in the eyes, a grin from ear to ear, and a tremor in the left eyebrow. "
          "That was the fourteenth candy cane.", [
              {"k": "ellipse", "x": -0.20, "y": -0.13, "w": 0.17, "h": 0.17, "c": "#ffffff"},
              {"k": "ellipse", "x": 0.20, "y": -0.13, "w": 0.17, "h": 0.17, "c": "#ffffff"},
              {"k": "star", "x": -0.20, "y": -0.13, "r": 0.065, "n": 5, "c": "#e8344a"},
              {"k": "star", "x": 0.20, "y": -0.13, "r": 0.065, "n": 5, "c": "#2fbf5f"},
              {"k": "line", "x1": -0.30, "y1": -0.29, "x2": -0.12, "y2": -0.25, "w": 0.03,
               "c": "#1a1a1a"},
              {"k": "line", "x1": 0.12, "y1": -0.27, "x2": 0.30, "y2": -0.31, "w": 0.03,
               "c": "#1a1a1a"},
              {"k": "poly", "pts": [[-0.30, 0.06], [0.30, 0.06], [0.22, 0.24], [-0.22, 0.24]],
               "c": "#3a1a1a"},
              {"k": "rect", "x": 0, "y": 0.09, "w": 0.52, "h": 0.05, "c": "#ffffff"},
              {"k": "ellipse", "x": 0.06, "y": 0.20, "w": 0.18, "h": 0.07, "c": "#ff6f8a"},
          ], "rare")
XM23.shirt("ugly_sweater", "Ugly Christmas Sweater",
           "Gingerbread men, zigzags, a candy cane on each cuff and a gingerbread man "
           "the size of your chest. It was a gift. You have to wear it at least once.",
           {"torso": "#b8202c", "arms": "#b8202c", "decal": "xm_tee_ugly", "weave": "xm_uglyknit",
            "stripe": "#1e7a36"}, "rare")
XM23.pants("candy_tights", "Candy Stripe Tights",
           "Red and white all the way down, like a pair of candy canes with knees.",
           {"legs": "#f4f0ea", "weave": "xm_candystripe", "cuff": "#1e7a36"})
XM23.belt("licorice_belt", "Licorice Belt",
          "A belt of twisted black licorice with a cherry-red gumdrop for a buckle. "
          "Holds up your trousers until about four in the afternoon.",
          {"band": "#1a1416", "buckle": "#e8344a", "width": 0.20, "weave": "xm_licorice"})


GINGER_MINION = {
    "name": "Gingerbread Man", "model": "parts", "count": 4, "hp": 25, "speed": 27,
    "damage": 0, "reach": 3.2, "rate": 0.6, "secs": 15, "scale": 1.0, "sight": 80,
    "explode": {"radius": 7.0, "damage": 45, "knock": 18},
    "parts": [place("gingerman", [0, 1.85, 0], [3.4, 3.6, 5.4], GINGER, decal="xm_gingerface"),
              part("sph", [0.62, 1.95, 0.30], [0.32, 0.32, 0.18], GUMDROPS[1]),
              part("sph", [0, 1.50, 0.34], [0.30, 0.30, 0.18], GUMDROPS[0]),
              part("sph", [0, 1.95, 0.34], [0.30, 0.30, 0.18], GUMDROPS[2])],
}


@XM23.weapon("candy_crook", "Candy Cane Crook",
             "A shepherd's crook of peppermint. The hook goes under the chin and up "
             "they go -- and anybody in the air takes the next swing a great deal "
             "harder.",
             {"kind": "melee", "damage": 26, "headshot": 1.0, "rpm": 96, "range": 13.0,
              "arc": 0.45, "sound": "swing", "knockback": 3,
              "on_hit": {"knockup": 30}, "vs_airborne": 1.5},
             [["+", "Hooks them and flips them into the air"],
              ["+", "50% more damage to anyone off the ground -- you, or them"],
              ["+", "A long reach: 13 studs"],
              ["-", "A narrow hook: easy to miss"],
              ["-", "13% less damage than a Blockblade"]], rarity="legendary")
def _():
    return [
        place("cane", [0, 0.0, -0.40], [2.0, 2.10, 2.0], WHITE, anchor=[0, 0, 0],
              r=[0, PI / 2, PI / 2], decal="candy", wrap=True),
        part("cyl", [0, 0.0, -0.10], [0.20, 0.50, 0.20], "#2a8a4a", [PI / 2, 0, 0],
             decal="felt", wrap=True),
        *gift_bow([0, 0.14, 0.20], 0.38, "#2a8a4a", tails=True),
    ]


@XM23.weapon("gingerbread_brigade", "Gingerbread Brigade",
             "A tray of four gingerbread men, baked in an instant and set loose. They "
             "run at the nearest enemy as fast as they can, and when they catch them, "
             "they go off like crackers.",
             {"kind": "summon", "cooldown": 45, "cost_hp": 20, "sound": "magic"},
             [["+", "Four gingerbread men who run at the nearest enemy and burst: 45 "
                    "damage each within 7 studs"],
              ["+", "Run, run, as fast as you can: they are faster than you"],
              ["-", "Costs you 20 health to bake them"],
              ["-", "45 second cooldown; they crumble after 15 seconds, or one good shot"]],
             rarity="legendary", minion=GINGER_MINION)
def _():
    tray = "#b9c0c8"
    parts = [
        part("rbox", [0, -0.02, 0.50], [0.86, 0.05, 1.00], tray, m="metal"),
        part("rbox", [0, 0.02, 0.50], [0.92, 0.04, 1.06], shade(tray, 0.85), m="metal"),
        part("rbox", [0, -0.06, -0.02], [0.14, 0.10, 0.22], "#5a3a22"),
    ]
    for x, z, turn in ((-0.20, 0.24, 0.1), (0.20, 0.30, -0.1), (-0.18, 0.72, -0.2), (0.20, 0.76, 0.15)):
        parts.append(_gingerman([x, 0.04, z], 0.40, r=[-PI / 2, turn, 0]))
    return parts


@XM23.weapon("gumdrop_launcher", "Gumdrop Launcher",
             "A gumball machine bolted to a stock. It fires sugared gumdrops that bounce "
             "off everything, and every bounce winds them up harder.",
             {"kind": "projectile", "projectile": "gumdrop", "damage": 18, "splash": 3.5,
              "splash_damage": 18, "rpm": 100, "mag": 6, "reload": 2.2, "speed": 72,
              "range": 260, "auto": False, "sound": "throw", "recoil": 1.0, "reserve": 36,
              "gravity_scale": 1.0, "self_damage": 0.3, "knockback": 8,
              "bounce": 3, "bounce_ramp": 0.4,
              "trail_colors": ["#ff6a8a", "#ffe08a"]},
             [["+", "Gumdrops bounce up to three times off walls and floors, 40% harder "
                    "each time"],
              ["+", "They burst on whoever they touch"],
              ["-", "Only 18 damage before the first bounce"],
              ["-", "Six to a load"]], rarity="legendary",
             proj=lambda: [_gumdrop([0, -0.25, 0], 1.6, GUMDROPS[0]),
                           part("sph", [0, -0.10, 0], [0.40, 0.40, 0.40], "#ff8fa8", m="neon",
                                a=0.3)])
def _():
    parts = [
        part("rbox", [0, -0.30, -0.06], [0.18, 0.44, 0.22], "#5a3a22", [0.3, 0, 0]),
        part("rbox", [0, -0.04, 0.30], [0.30, 0.26, 0.90], CANDY_RED, m="metal"),
        part("cyl", [0, 0.0, 0.95], [0.26, 0.40, 0.26], GOLD, [PI / 2, 0, 0], m="metal"),
        part("torus", [0, 0.0, 1.15], [0.30, 0.6, 0.30], GOLD, [PI / 2, 0, 0], m="metal"),
        part("cyl", [0, 0.14, 0.30], [0.36, 0.06, 0.36], GOLD, m="metal"),
        part("sph", [0, 0.44, 0.30], [0.58, 0.58, 0.58], "#eef8ff", m="glass", a=0.3),
        part("sph", [0, 0.76, 0.30], [0.14, 0.10, 0.14], CANDY_RED, m="metal"),
        part("cyl", [0.17, -0.04, 0.45], [0.06, 0.10, 0.06], SILVER, [0, 0, PI / 2], m="metal"),
    ]
    for n in range(9):
        a = n * 2.39996
        rr = 0.06 + (n % 3) * 0.06
        parts.append(_gumdrop([math.sin(a) * rr, 0.24 + (n // 3) * 0.11, 0.30 + math.cos(a) * rr],
                              0.36, GUMDROPS[n % len(GUMDROPS)]))
    return parts


@XM23.gear("fruitcake", "Fruitcake",
           "Grandma's fruitcake. Nobody knows what is in it, and every slice is "
           "different: usually something wonderful. Occasionally a walnut shell.",
           {"kind": "consume", "cooldown": 22, "sound": "eat",
            "consume": {"random": [
                {"name": "Plum and cherry: +50 health", "heal": 50},
                {"name": "Candied peel: you feel quick!", "heal": 10, "speed": [0.30, 6.0]},
                {"name": "Stem ginger: hit harder for 6 seconds", "might": [0.25, 6.0]},
                {"name": "Marzipan: a 40 point shield", "shield": [40, 8.0]},
                {"name": "A walnut shell. Crunch.", "heal": 5, "trick": {"slow": [0.3, 3.0]}},
            ]}},
           [["+", "One of five slices at random: 50 health, speed, extra damage or a shield"],
            ["+", "Most of them are wonderful"],
            ["-", "One of them is a walnut shell, and leaves you slowed"],
            ["-", "22 second cooldown"]], rarity="rare")
def _():
    return [
        part("rbox", [0, -0.04, 0.32], [0.46, 0.32, 0.62], "#6a3418", decal="xm_fruitcake",
             wrap=True),
        part("rbox", [0, 0.14, 0.32], [0.48, 0.06, 0.64], ICING),
        place("teardrop", [0.20, 0.08, 0.50], [0.06, 0.12, 0.06], ICING, r=[PI, 0, 0]),
        place("teardrop", [-0.21, 0.07, 0.20], [0.06, 0.14, 0.06], ICING, r=[PI, 0, 0]),
        part("sph", [0, 0.22, 0.32], [0.10, 0.10, 0.10], BERRY, m="glass"),
        *_holly([0.10, 0.20, 0.36], 0.35),
    ]


XM23.effect("gingerbread_parade", name="Gingerbread Parade", rate=2.4, life=[2.6, 3.4],
            size=[0.30, 0.42], grow=0.0, gravity=0.0, spread=0.05, rise=[0.02, 0.12],
            blend="normal", spin=0.0, colors=["#c97a32", "#b5651d", "#a85a1a"],
            shape="gingerbread", radius=0.9, orbit=1.3, upright=True, wobble=0.35)
XM23.effect("peppermint_twist", name="Peppermint Twist", rate=6.0, life=[1.4, 2.0],
            size=[0.18, 0.32], grow=0.0, gravity=-0.4, spread=0.5, rise=[0.6, 1.1],
            blend="normal", spin=5.0, colors=["#ff3344", "#e8344a", "#ffffff", "#2fbf5f"],
            shapes=["xm_peppermint", "xm_peppermint", "candycane"], radius=0.6)
XM23.opening(
    sky={"top": "#24100c", "horizon": "#7a3a24", "sun": [0.3, 0.8, 0.5], "clouds": 0,
         "tint": "#ffd8b0"},
    ambient="#a87a5a", beam="#ffe3b8", seep="peppermint_twist", after="gingerbread_parade",
    burst=["#e8344a", "#ffffff", "#2fbf5f", "#f2c230"],
    pieces=[{"shape": "gingerbread", "colors": ["#c97a32", "#b5651d"], "blend": "normal"},
            {"shape": "candycane", "colors": ["#ff3344", "#e8344a"], "blend": "normal"},
            {"shape": "xm_peppermint", "colors": ["#ff3344", "#2fbf5f"], "blend": "normal"},
            {"shape": "sweet", "colors": ["#f2c230", "#8a4fd6", "#2f9fe8"], "blend": "normal"}],
    backdrop="xm_gingerbread", title_wait="Lifting the lid...",
    title_shake="Something smells delicious...")
XM23.award("Gingerbread Junction", ["Cookie Cutter", "Icing Piper", "Gumdrop Gatherer",
                                    "Signal Baker", "Stationmaster", "Master of the Junction"],
           "Opened Cookie Tin Crates at Gingerbread Junction, Christmas 2023.", "em_gingerbread",
           "flake")
XM23.bundle("pair", "Tin and Key", 1, 1050, "One Cookie Tin Crate, one Peppermint Key.")
XM23.bundle("bakers_dozen", "Baker's Three", 3, 3000, "Three tins, three keys. Saves 300.")


# ============================================================ 2024
LIVERY = "#a8141e"
NAVY_COAT = "#1f2a4a"
PAPER = "#c9a26a"
STEAM = "#f4f8fc"
HICKORY = "#3a4a6a"


def _parcel(at, w, h, d, r=None, label=True, bow=None, **kw):
    """A brown-paper parcel tied with string, middle at ``at``: ``bow``
    a ribbon colour for a bow on top."""
    pieces = [
        part("rbox", [0, 0, 0], [w, h, d], PAPER, decal="xm_brownpaper", wrap=True),
        part("rbox", [0, 0, 0], [w + 0.01, h + 0.01, 0.025], "#f4ecd8"),
        part("rbox", [0, 0, 0], [0.025, h + 0.01, d + 0.01], "#f4ecd8"),
    ]
    if label:
        pieces.append(part("box", [w * 0.22, h * 0.18, d / 2 + 0.006], [w * 0.36, h * 0.26, 0.005],
                           "#ffffff", decal="xm_label"))
    if bow:
        pieces += gift_bow([0, h / 2, 0], min(w, d) * 0.55, bow)
    out = at_frame(pieces, at, r, 1.0)
    for p in out:
        p.update(kw)
    return out


def _puffs(at, k=1.0, n=4, **kw):
    """A column of steam puffs rising from ``at``, smaller and fainter as
    they go."""
    x, y, z = at
    out = []
    for i in range(n):
        s = (0.36 - i * 0.05) * k
        out.append(part("sph", [x + (0.05 if i % 2 else -0.04) * k, y + (0.10 + i * 0.26) * k, z],
                        [s, s * 0.86, s], STEAM, a=round(0.85 - i * 0.16, 2), **kw))
    return out


XM24 = Event(
    "christmas_2024", "christmas", 2024, "xm24",
    name="North Pole Express", title="The North Pole Express",
    blurb="Christmas 2024 a train came through Blockhaven every night at midnight: a "
          "red engine, a coal tender heaped with parcels and a mail car with every "
          "letter anybody had ever written to the North Pole. It never stopped. It only "
          "slowed down long enough for the parcels to be thrown off.",
    tagline="All aboard. Tickets, please.",
    starts="2024-12-01", ends="2024-12-30",
    colors={"accent": "#e8b84a", "deep": "#14162a", "glow": "#fff3b0"},
    family_effects=["frostbite", "starstruck", "candlelight_vigil"],
    hero_effect="steam_puffs", stencil="stencil_xm24")


@XM24.crate_model("Coal Tender",
                  "The coal tender off the North Pole Express, red with gold lining, the "
                  "railway's name down the side, buffers at the back and a heap of coal "
                  "with the parcels riding on top. Holds the North Pole Express set. Needs "
                  "a Whistle Key.",
                  hinge=[0, 0.32, -0.56], keyhole=[0, -0.30, 0.56])
def _():
    parts = [
        part("rbox", [0, -0.48, 0], [1.80, 0.16, 1.10], COAL, m="metal"),
        part("rbox", [0, -0.05, 0], [1.70, 0.70, 1.04], LIVERY, decal="xm_livery", wrap=True),
        part("rbox", [0, 0.32, 0], [1.76, 0.06, 1.10], GOLD, m="metal"),
        part("rbox", [0, -0.40, 0], [1.74, 0.04, 1.08], GOLD, m="metal"),
        part("box", [0, 0.28, 0], [1.60, 0.04, 0.96], "#ffd36a", m="neon"),
        # the lock: a brass plate on the side
        part("rbox", [0, -0.30, 0.535], [0.26, 0.18, 0.05], BRASS, m="metal", decal="keyhole",
             lock=1),
        part("box", [0, -0.05, -0.525], [0.80, 0.46, 0.02], "#000000", [0, PI, 0],
             decal="stencil_xm24", a=-1),
        # buffers and the coupling at the back, a lamp on the corner
        part("rbox", [-0.90, -0.40, 0], [0.10, 0.12, 0.70], COAL, m="metal"),
        part("rbox", [-0.98, -0.28, 0.22], [0.06, 0.30, 0.20], BRASS, m="metal"),
        part("cyl", [-1.02, -0.30, 0.30], [0.16, 0.10, 0.16], SILVER, [0, 0, PI / 2], m="metal"),
        part("cyl", [-1.02, -0.30, -0.30], [0.16, 0.10, 0.16], SILVER, [0, 0, PI / 2], m="metal"),
        part("torus", [-1.00, -0.44, 0], [0.12, 0.03, 0.12], COAL, [PI / 2, 0, 0], m="metal"),
        part("sph", [-0.80, 0.42, 0.44], [0.12, 0.12, 0.12], BERRY, m="neon"),
        # the coal (the lid), and the parcels riding on it
        part("hemi", [0, 0.48, 0], [1.56, 0.36, 0.96], COAL, decal="xm_coal", wrap=True, lid=1),
        part("rbox", [0, 0.32, 0], [1.66, 0.04, 1.02], shade(COAL, 1.3), lid=1),
        *_parcel([0.36, 0.62, 0.08], 0.36, 0.26, 0.30, r=[0, 0.4, 0.1], bow=BERRY, lid=1),
        *_parcel([-0.30, 0.60, -0.10], 0.30, 0.22, 0.30, r=[0.1, -0.3, -0.1], lid=1),
        *_parcel([-0.02, 0.76, 0.02], 0.24, 0.20, 0.22, r=[0, 0.9, 0.15], bow=HOLLY, lid=1),
    ]
    # the wheels: four spoked wheels each side, red hubs
    for x in (-0.55, 0.55):
        for z, yaw in ((0.57, 0.0), (-0.57, PI)):
            parts += [part("disc", [x, -0.58, z], [0.50, 0.50, 0.40], COAL, [0, yaw, 0],
                           decal="xm_wheel", m="metal"),
                      part("sph", [x, -0.58, z * 1.06], [0.10, 0.10, 0.06], BERRY)]
    parts += [rod([-0.55, -0.58, 0.62], [0.55, -0.58, 0.62], 0.05, SILVER, m="metal"),
              rod([-0.55, -0.58, -0.62], [0.55, -0.58, -0.62], 0.05, SILVER, m="metal")]
    return parts


@XM24.key_model("Whistle Key",
                "A brass key whose bow is the engine's own steam whistle, pull-chain and "
                "all. Opens one Coal Tender. Blow it and every reindeer for a mile "
                "looks up.", shoulder=-0.30)
def _():
    return [
        part("cyl", [-0.62, -0.02, 0], [0.22, 0.40, 0.22], BRASS, m="metal"),
        place("bell", [-0.62, 0.18, 0], [0.30, 0.26, 0.30], BRASS, anchor=[0, 0, 0], m="metal"),
        part("cyl", [-0.62, -0.26, 0], [0.12, 0.10, 0.12], shade(BRASS, 0.8), m="metal"),
        part("rbox", [-0.48, -0.02, 0], [0.24, 0.05, 0.05], shade(BRASS, 0.8), [0, 0, -0.3],
             m="metal"),
        rod([-0.38, -0.08, 0], [-0.40, -0.40, 0], 0.02, SILVER, m="metal"),
        part("sph", [-0.40, -0.44, 0], [0.06, 0.06, 0.06], BERRY),
        part("cyl", [0.13, 0, 0], [0.09, 0.84, 0.09], BRASS, [0, 0, PI / 2], m="metal"),
        part("torus", [-0.27, 0, 0], [0.20, 0.07, 0.20], GOLD_DARK, [0, 0, PI / 2], m="metal"),
        part("rbox", [0.40, -0.12, 0], [0.08, 0.22, 0.08], BRASS, m="metal"),
        part("rbox", [0.52, -0.16, 0], [0.08, 0.30, 0.08], BRASS, m="metal"),
        *_puffs([-0.62, 0.34, 0], 0.40, n=3),
    ]


@XM24.hat("conductor_cap", "Conductor's Cap",
          "Navy, peaked, a gold band and the railway's badge on the front. It has "
          "punched four hundred thousand tickets and never once been late.", "rare")
def _():
    return [
        cap(-0.30, 0.18, NAVY_COAT, grow=0.06, decal="felt", wrap=True),
        part("rbox", [0, 0.20, 0.04], [1.72, 0.08, 1.62], NAVY_COAT, decal="felt", wrap=True),
        place("peak", [0, -0.22, 0], [1.84, 1.0, 1.74], BLACK, anchor=[0, 0, 0], m="glass"),
        band(-0.20, 0.12, GOLD, grow=0.08, m="metal"),
        part("rbox", [0, -0.02, 0.86], [0.42, 0.28, 0.04], GOLD, [-0.06, 0, 0], m="metal",
             decal="xm_badge"),
        part("cyl", [0.80, -0.20, 0.40], [0.10, 0.04, 0.10], GOLD, [0, 0, PI / 2], m="metal"),
        part("cyl", [-0.80, -0.20, 0.40], [0.10, 0.04, 0.10], GOLD, [0, 0, PI / 2], m="metal"),
    ]


@XM24.hat("smokestack_topper", "Smokestack Topper",
          "The front of the engine worn as a top hat: a flared black smokestack puffing "
          "away, the headlamp lit, the brass bell and a cowcatcher for a brim. Clear "
          "the line.", "legendary")
def _():
    parts = [
        place("brim", [0, -0.05, 0], [2.16, 1.4, 2.06], LIVERY, anchor=[0, 0, 0], decal="felt",
              wrap=True),
        place("flare", [0, 0.0, 0], [1.30, 1.30, 1.26], COAL, anchor=[0, 0, 0], m="metal"),
        part("torus", [0, 1.30, 0], [1.32, 0.08, 1.28], BRASS, m="metal"),
        part("cyl", [0, 0.16, 0], [1.20, 0.22, 1.16], LIVERY, decal="xm_livery", wrap=True),
        part("cyl", [0, 0.28, 0], [1.22, 0.04, 1.18], GOLD, m="metal"),
        # the headlamp on the front, the bell on the side
        part("rbox", [0, 0.70, 0.62], [0.34, 0.30, 0.20], COAL, m="metal"),
        part("cyl", [0, 0.70, 0.73], [0.24, 0.04, 0.24], "#fff3b0", [PI / 2, 0, 0], m="neon"),
        part("torus", [0, 0.70, 0.73], [0.26, 0.04, 0.26], BRASS, [PI / 2, 0, 0], m="metal"),
        place("bell", [0.62, 0.50, -0.10], [0.24, 0.24, 0.24], BRASS, anchor=[0, 0, 0], m="metal"),
        part("rbox", [0.62, 0.78, -0.10], [0.04, 0.06, 0.04], BRASS, m="metal"),
    ]
    # the cowcatcher: slats raking down and forward over the brim
    for k in range(5):
        x = (k - 2) * 0.16
        parts.append(rod([x * 1.4, -0.04, 1.02], [x, -0.24, 1.30], 0.05, BERRY))
    parts.append(rod([-0.42, -0.04, 1.02], [0.42, -0.04, 1.02], 0.05, BERRY))
    parts += _puffs([0.06, 1.34, 0.02], 1.4, n=4)
    return parts


@XM24.hat("parcel_pile", "Parcel Pile",
          "Three parcels in brown paper and string, stacked on your head, addressed to "
          "somebody at the North Pole. You are not to look. You will look.", "uncommon",
          hair="show")
def _():
    return (_parcel([0, 0.22, 0], 0.98, 0.44, 0.90)
            + _parcel([0.06, 0.62, -0.04], 0.74, 0.36, 0.66, r=[0, 0.4, 0])
            + _parcel([-0.04, 0.96, 0.02], 0.46, 0.32, 0.44, r=[0, -0.3, 0.06], bow=BERRY))


@XM24.hat("drivers_cap", "Engine Driver's Cap",
          "A soft cap in hickory stripe, soot on the peak, and the driver's goggles "
          "pushed up off his eyes for the long straight stretch.", "uncommon")
def _():
    parts = [
        cap(-0.30, 0.20, HICKORY, grow=0.04, decal="xm_hickory", wrap=True),
        part("sph", [0, 0.20, -0.06], [1.62, 0.22, 1.54], HICKORY, decal="xm_hickory", wrap=True),
        place("peak", [0, -0.22, 0], [1.80, 1.0, 1.70], HICKORY, anchor=[0, 0, 0],
              decal="xm_hickory", wrap=True),
        ringband(-0.04, 0.08, "#2a2a30", margin=0.08),
    ]
    for s in (1, -1):
        parts += [part("cyl", [0.26 * s, 0.02, 0.84], [0.28, 0.10, 0.28], BRASS, [PI / 2 - 0.4, 0, 0],
                       m="metal"),
                  part("cyl", [0.26 * s, 0.02, 0.88], [0.22, 0.02, 0.22], "#9fd8ff",
                       [PI / 2 - 0.4, 0, 0], m="glass", a=0.6)]
    parts.append(part("sph", [0.30, -0.18, 0.92], [0.20, 0.06, 0.06], "#2a2a30", a=0.6))
    return parts


@XM24.hat("reindeer_plume", "Reindeer Plume",
          "The red-and-gold plume off the lead reindeer's harness, two sleigh bells on "
          "ribbons and a sprig of holly. You are now pulling the sleigh. Good luck.",
          "rare", hair="show")
def _():
    parts = [ringband(-0.24, 0.14, LIVERY, decal="felt", wrap=True),
             ringband(-0.30, 0.04, GOLD, margin=0.05, m="metal")]
    for k, (lean, c) in enumerate(((-0.3, BERRY), (0.0, GOLD), (0.3, BERRY), (0.15, "#ffffff"),
                                   (-0.15, GOLD))):
        parts.append(place("feather", [0.0, 0.0, -0.10 + k * 0.02], 1.10 - abs(lean) * 0.4, c,
                           anchor=[0, -0.5, 0], r=[-0.2, PI / 2, lean]))
    for s in (1, -1):
        parts += [rod([0.86 * s, -0.24, 0.30], [0.90 * s, -0.56, 0.36], 0.04, BERRY),
                  part("sph", [0.90 * s, -0.66, 0.36], [0.22, 0.22, 0.22], GOLD, m="metal"),
                  part("rbox", [0.90 * s, -0.68, 0.46], [0.10, 0.02, 0.02], COAL)]
    parts += _holly([0.0, -0.10, 0.92], 0.8)
    return parts


@XM24.hat("snowplough_helmet", "Snowplough Helmet",
          "A hi-vis orange hard hat with a reflective stripe, an amber lamp turning on top "
          "and a little plough blade bolted to the front, for clearing the line ahead of "
          "the Express.",
          "rare")
def _():
    hivis, amber = "#ff6a1a", "#ffc21f"
    parts = [
        dome(-0.36, 0.86, hivis, t="capcrown", m="glass"),
        place("brim", [0, -0.30, 0], [2.16, 0.8, 2.06], hivis, anchor=[0, 0, 0], m="glass"),
        ringband(-0.20, 0.08, COAL, margin=0.05),
        ringband(-0.08, 0.10, "#e8eef4", margin=0.16, m="metal"),
        part("cyl", [0, 0.56, 0], [0.30, 0.10, 0.30], COAL, m="metal"),
        part("cyl", [0, 0.70, 0], [0.24, 0.22, 0.24], amber, m="neon", a=0.8),
        part("rbox", [0, 0.70, 0], [0.28, 0.06, 0.06], "#ffffff", m="neon", spin=4.0),
        part("hemi", [0, 0.81, 0], [0.24, 0.10, 0.24], amber, m="glass", a=0.7),
    ]
    # the plough blade, raked forward off the brim
    parts += [part("rbox", [0, -0.20, 1.10], [0.62, 0.22, 0.05], BERRY, [0.45, 0, 0], m="metal",
                   decal="xm_candystripe"),
              part("rbox", [0.40, -0.20, 1.00], [0.28, 0.22, 0.05], BERRY, [0.45, 0.7, 0], m="metal"),
              part("rbox", [-0.40, -0.20, 1.00], [0.28, 0.22, 0.05], BERRY, [0.45, -0.7, 0], m="metal"),
              rod([0, -0.26, 0.92], [0, -0.22, 1.06], 0.06, COAL, m="metal")]
    return parts


@XM24.hat("sleigh_bell", "Silver Sleigh Bell",
          "One silver bell off the sleigh's harness, on a red ribbon, with a tag that "
          "says BELIEVE. Only some people can hear it ring.", "uncommon", hair="show")
def _():
    return [
        place("bowtie", [0, 0.10, 0.10], [0.90, 0.70, 1.0], BERRY),
        part("sph", [0, 0.10, 0.12], [0.16, 0.14, 0.12], BERRY),
        place("ribbon", [0.12, 0.08, 0.12], [0.20, 0.34, 0.10], BERRY, anchor=[0, 0.5, 0],
              r=[0.2, 0, 1.36]),
        place("ribbon", [-0.12, 0.08, 0.12], [0.20, 0.34, 0.10], BERRY, anchor=[0, 0.5, 0],
              r=[0.2, 0, -1.36]),
        part("sph", [0, 0.44, 0.06], [0.50, 0.46, 0.50], SILVER, m="metal"),
        part("rbox", [0, 0.38, 0.30], [0.20, 0.04, 0.04], COAL),
        part("torus", [0, 0.70, 0.06], [0.14, 0.04, 0.14], SILVER, [PI / 2, 0, 0], m="metal"),
        part("box", [0.30, 0.20, 0.26], [0.22, 0.12, 0.01], "#f4ecd8", [0, 0, -0.3],
             decal="xm_believe"),
    ]


@XM24.back("mail_sack", "North Pole Mail Sack",
           "A canvas mail sack over the shoulder, stencilled N.P. MAIL, tied at the neck "
           "with letters poking out of it -- every one addressed in crayon.", "rare")
def _():
    canvas = "#c8b48a"
    parts = straps("#5a3a22") + [
        part("sph", [0.06, 0.06, -0.52], [1.20, 1.40, 0.80], canvas, decal="xm_mailsack",
             wrap=True),
        place("teardrop", [0.10, 0.70, -0.52], [0.52, 0.52, 0.40], canvas, anchor=[0, 0, 0],
              decal="canvas", wrap=True),
        part("torus", [0.10, 0.80, -0.52], [0.34, 0.07, 0.30], "#5a3a22"),
    ]
    for k, (x, a) in enumerate(((0.0, 0.2), (0.16, -0.4), (-0.12, 0.6), (0.08, 0.0))):
        parts.append(part("box", [0.10 + x, 1.06 + k * 0.02, -0.52 + x * 0.3], [0.30, 0.20, 0.01],
                          "#ffffff", [0.2, a, x * 2], decal="xm_letter"))
    return parts


@XM24.back("little_engine", "The Little Engine",
           "A toy steam engine riding up your back on its own little track, puffing away, "
           "wheels going round. It thinks it can. It is fairly sure.", "legendary")
def _():
    z = -0.56
    parts = [
        # the track up your back
        part("rbox", [0.16, 0.30, -0.22], [0.06, 1.80, 0.06], SILVER, m="metal"),
        part("rbox", [-0.16, 0.30, -0.22], [0.06, 1.80, 0.06], SILVER, m="metal"),
        # the engine, climbing: boiler, smokestack, cab, cowcatcher
        part("cyl", [0, 0.40, z], [0.46, 1.00, 0.46], LIVERY, decal="xm_livery", wrap=True),
        part("cyl", [0, 0.92, z], [0.48, 0.06, 0.48], GOLD, m="metal"),
        part("rbox", [0, -0.24, z - 0.04], [0.56, 0.44, 0.56], COAL, m="metal"),
        part("rbox", [0, -0.24, z - 0.04], [0.40, 0.30, 0.58], "#ffd36a", m="neon"),
        part("rbox", [0, -0.48, z - 0.04], [0.60, 0.06, 0.60], LIVERY),
        place("flare", [0, 0.40, z - 0.30], [0.18, 0.30, 0.18], COAL, anchor=[0, 0, 0],
              r=[-PI / 2, 0, 0], m="metal"),
        part("cyl", [0, 0.94, z], [0.20, 0.08, 0.20], "#fff3b0", m="neon"),
        part("sph", [0, 0.62, z - 0.24], [0.14, 0.14, 0.10], BRASS, m="metal"),
    ]
    for y in (0.10, 0.56):
        for s in (1, -1):
            parts.append(part("disc", [0.26 * s, y, z + 0.08], [0.30, 0.30, 0.40], COAL,
                              [0, PI / 2 * s, 0], decal="xm_wheel", m="metal"))
    parts += _puffs([0, 0.40, z - 0.62], 0.9, n=3)
    return parts


@XM24.hairdo("steam_curls", "Steam Curls",
             "White hair in soft round puffs, like the steam off the Express on a frosty "
             "night, drifting up off the top.", "uncommon")
def _():
    c = "#f4f8fc"
    parts = [place("hairmid", [0, 0, 0], [1.04, 1.04, 1.04], c, anchor=[0, 0, 0],
                   decal="strands", wrap=True)]
    for k in range(7):
        a = k * TAU / 7
        parts.append(part("sph", [math.sin(a) * 0.30, 0.56 + (k % 2) * 0.06, math.cos(a) * 0.28 - 0.04],
                          [0.30, 0.26, 0.30], c if k % 2 else "#e8eef4"))
    parts += [part("sph", [0.04, 0.80, 0.0], [0.26, 0.22, 0.26], c, a=0.8),
              part("sph", [-0.04, 0.98, 0.02], [0.18, 0.16, 0.18], c, a=0.6)]
    return parts


@XM24.hairdo("soot_crop", "Stoker's Crop",
             "Short dark hair with the coal dust worked into it, a cowlick that has been "
             "standing up since Michaelmas, and ash on the ends.", "uncommon")
def _():
    c = "#2a2420"
    parts = [place("hairshort", [0, 0, 0], [1.03, 1.03, 1.03], c, anchor=[0, 0, 0],
                   decal="strands", wrap=True)]
    for k, (x, z) in enumerate(((0.20, 0.30), (-0.14, 0.24), (0.04, 0.40))):
        parts.append(place("teardrop", [x, 0.50, z], [0.20, 0.30, 0.18], "#4a4440" if k % 2 else c,
                           anchor=[0, 0.1, 0], r=[0.8, 0, -x], decal="strands", wrap=True))
    return parts


XM24.face("all_aboard", "All Aboard!",
          "Cheeks puffed, eyes screwed shut, and a whistle between the teeth, giving it "
          "everything.", [
              {"k": "arc", "x": -0.20, "y": -0.12, "r": 0.06, "a0": 0.55, "a1": 0.95, "w": 0.03,
               "c": "#16171b"},
              {"k": "arc", "x": 0.20, "y": -0.12, "r": 0.06, "a0": 0.55, "a1": 0.95, "w": 0.03,
               "c": "#16171b"},
              {"k": "ellipse", "x": -0.30, "y": 0.06, "w": 0.16, "h": 0.12, "c": "#ffb08a"},
              {"k": "ellipse", "x": 0.30, "y": 0.06, "w": 0.16, "h": 0.12, "c": "#ffb08a"},
              {"k": "ellipse", "x": 0.0, "y": 0.12, "w": 0.10, "h": 0.07, "c": "#16171b"},
              {"k": "poly", "pts": [[0.02, 0.10], [0.20, 0.08], [0.22, 0.16], [0.04, 0.15]],
               "c": "#c9a227"},
              {"k": "ellipse", "x": 0.21, "y": 0.12, "w": 0.04, "h": 0.06, "c": "#8a6a1a"},
          ], "uncommon")
XM24.face("sooty_grin", "Sooty Grin",
          "A face full of coal dust from a night on the footplate, and a grin as white "
          "as the snow.", [
              {"k": "ellipse", "x": -0.26, "y": 0.04, "w": 0.22, "h": 0.12, "c": "#5a5450"},
              {"k": "ellipse", "x": 0.30, "y": -0.24, "w": 0.18, "h": 0.08, "c": "#5a5450"},
              {"k": "ellipse", "x": 0.18, "y": 0.10, "w": 0.10, "h": 0.06, "c": "#5a5450"},
              {"k": "ellipse", "x": -0.20, "y": -0.13, "w": 0.08, "h": 0.10, "c": "#16171b"},
              {"k": "ellipse", "x": 0.20, "y": -0.13, "w": 0.08, "h": 0.10, "c": "#16171b"},
              {"k": "poly", "pts": [[-0.22, 0.08], [0.22, 0.08], [0.16, 0.22], [-0.16, 0.22]],
               "c": "#16171b"},
              {"k": "poly", "pts": [[-0.18, 0.09], [0.18, 0.09], [0.16, 0.14], [-0.16, 0.14]],
               "c": "#ffffff"},
          ], "rare")
XM24.shirt("conductor_coat", "Conductor's Coat",
           "Navy, double-breasted, gold buttons and braid, a ticket punch on a chain and "
           "a pocket watch that is never, ever wrong.",
           {"torso": NAVY_COAT, "arms": NAVY_COAT, "decal": "xm_tee_conductor", "weave": "felt",
            "stripe": GOLD}, "rare")
XM24.pants("hickory_overalls", "Footplate Overalls",
           "Hickory-stripe overalls, soot at the knees, for shovelling coal at forty miles "
           "an hour.",
           {"legs": HICKORY, "weave": "xm_hickory", "cuff": "#2a2a30"})
XM24.belt("watch_belt", "Guard's Belt",
          "A black belt with a brass buckle and the guard's watch on its chain, set to "
          "North Pole time.",
          {"band": "#2a2a30", "buckle": BRASS, "width": 0.20, "metal": True, "chain": GOLD})


@XM24.weapon("coal_shovel", "Fireman's Shovel",
             "The shovel off the footplate, still hot. A face full of coal dust leaves "
             "whoever it catches coughing, blinking and in no state to use anything "
             "clever -- and a long way back from where they were standing.",
             {"kind": "melee", "damage": 28, "headshot": 1.0, "rpm": 84, "range": 10.5,
              "arc": 0.62, "sound": "swing", "knockback": 0,
              "on_hit": {"silence": 2.5, "push": 24}},
             [["+", "Silences whoever it hits for 2.5 seconds: no abilities, no gear, nothing "
                    "to drink"],
              ["+", "...and shovels them well back"],
              ["-", "28 damage: it is a shovel"],
              ["-", "Slow to swing"]], rarity="legendary")
def _():
    wood, iron = "#8a5a2a", "#3a3d42"
    return [
        rod([0, 0, -0.40], [0, 0, 0.96], 0.10, wood),
        part("rbox", [0, 0, -0.48], [0.30, 0.08, 0.10], wood),
        part("cyl", [0, 0, 1.00], [0.14, 0.14, 0.14], iron, [PI / 2, 0, 0], m="metal"),
        part("rbox", [0, -0.02, 1.36], [0.56, 0.04, 0.62], iron, [0.12, 0, 0], m="metal"),
        part("rbox", [0.28, 0.04, 1.36], [0.04, 0.10, 0.62], iron, [0.12, 0, 0], m="metal"),
        part("rbox", [-0.28, 0.04, 1.36], [0.04, 0.10, 0.62], iron, [0.12, 0, 0], m="metal"),
        part("sph", [0.06, 0.06, 1.40], [0.16, 0.10, 0.14], COAL),
        part("sph", [-0.10, 0.06, 1.30], [0.12, 0.08, 0.12], COAL),
        part("sph", [0.0, 0.03, 1.52], [0.12, 0.05, 0.10], "#ff5a1a", m="neon"),
    ]


@XM24.weapon("return_to_sender", "Return to Sender",
             "A parcel, thrown off the back of the Express, that sits wherever it lands. "
             "The first enemy who goes near it finds out it was addressed to them: it "
             "pops open, bowls them up and ties them down.",
             {"kind": "deploy", "cooldown": 9, "sound": "throw",
              "deploy": {"type": "trap", "thrown": True, "throw": 24, "radius": 3.6,
                         "secs": 25.0, "limit": 2, "damage": 25, "scale": 1.3,
                         "enemy": {"root": 2.0, "knockup": 16}, "name": "Parcel",
                         "color": "#c9a26a"}},
             [["+", "Throws a parcel that waits up to 25 seconds; the first enemy within 3.6 "
                    "studs is bowled up and held fast for 2 seconds"],
              ["+", "Two can be waiting at once"],
              ["-", "25 damage"],
              ["-", "Anybody who sees it land knows to go round"]], rarity="legendary",
             deploy=lambda: _parcel([0, 0.30, 0], 0.80, 0.60, 0.70, bow=BERRY))
def _():
    return _parcel([0, 0.10, 0.16], 0.46, 0.36, 0.40, bow=BERRY)


@XM24.weapon("ticket_puncher", "Ticket Puncher",
             "A conductor's punch that clips holes at three hundred tickets a minute. "
             "Every hole it punches keeps on stinging, five deep, until they get "
             "somewhere warm.",
             {"kind": "hitscan", "damage": 8, "headshot": 1.5, "rpm": 300, "mag": 24,
              "reload": 2.0, "range": 140, "auto": True, "sound": "smg", "recoil": 0.3,
              "spread": 1.2, "reserve": 144, "tracer": "#ffe066",
              "on_hit": {"bleed": [2, 4.0, 5]}},
             [["+", "Every hit punches a hole that bleeds 2 a second for 4 seconds, stacking "
                    "five deep"],
              ["+", "300 a minute"],
              ["-", "8 damage a hit"],
              ["-", "24 to a clip"]], rarity="legendary")
def _():
    nickel = "#c9ced6"
    return [
        part("rbox", [0, -0.16, -0.02], [0.16, 0.42, 0.24], NAVY_COAT, [-0.25, 0, 0],
             decal="felt"),
        part("rbox", [0, 0.06, 0.32], [0.16, 0.10, 0.80], nickel, m="metal"),
        part("rbox", [0, -0.06, 0.32], [0.14, 0.06, 0.70], nickel, [0.08, 0, 0], m="metal"),
        part("cyl", [0, 0.00, 0.72], [0.18, 0.14, 0.18], nickel, [PI / 2, 0, 0], m="metal"),
        part("rbox", [0, 0.16, 0.10], [0.20, 0.14, 0.20], LIVERY, m="metal"),
        part("box", [0.06, 0.00, 0.80], [0.22, 0.12, 0.01], "#f4ecd8", [0, 0, 0.1],
             decal="xm_ticket"),
    ]


@XM24.gear("pocket_watch", "Full Steam Ahead",
           "The driver's pocket watch. Snap it open and you are running late: a burst of "
           "speed down the line and the steam up for whatever is at the end of it.",
           {"kind": "ability", "cooldown": 18, "sound": "whoosh",
            "ability": {"dash": {"speed": 62}, "might": {"secs": 4.0, "value": 0.20}}},
           [["+", "Dashes you forward down the line"],
            ["+", "20% more damage for 4 seconds after"],
            ["-", "18 second cooldown"],
            ["-", "Straight lines only"]], rarity="rare")
def _():
    return [
        part("cyl", [0, 0.28, 0.12], [0.44, 0.10, 0.44], GOLD, [PI / 2, 0, 0], m="metal"),
        part("disc", [0, 0.28, 0.175], [0.36, 0.36, 0.02], "#fffaf0", decal="clockface"),
        part("cyl", [0, 0.53, 0.12], [0.08, 0.10, 0.08], GOLD, m="metal"),
        part("torus", [0, 0.62, 0.12], [0.14, 0.03, 0.14], GOLD, [PI / 2, 0, 0], m="metal"),
        rod([0, 0.64, 0.12], [0.06, 0.04, 0.06], 0.02, GOLD, m="metal"),
    ]


XM24.effect("steam_puffs", name="Steam Puffs", rate=3.2, life=[1.6, 2.4],
            size=[0.36, 0.56], grow=0.6, gravity=-0.8, spread=0.3, rise=[0.5, 0.9],
            blend="normal", spin=0.3, colors=["#f4f8fc", "#e2eaf2", "#ffffff"],
            shape="puff", radius=0.5)
XM24.effect("parcel_post", name="Parcel Post", rate=1.8, life=[2.4, 3.0],
            size=[0.30, 0.42], grow=0.0, gravity=0.0, spread=0.2, rise=[0.05, 0.2],
            blend="normal", spin=1.2, colors=["#c9a26a", "#d0141c", "#1e7a36"],
            shape="gift", radius=0.9, orbit=1.6, wobble=0.3)
XM24.opening(
    sky={"top": "#06081a", "horizon": "#24305a", "sun": [0.2, 0.9, 0.6], "clouds": 0.2,
         "tint": "#e8f0ff"},
    ambient="#5a6488", beam="#fff3b0", seep="steam_puffs", after="parcel_post",
    burst=["#e8b84a", "#d0141c", "#ffffff", "#1e7a36"],
    pieces=[{"shape": "gift", "colors": ["#c9a26a", "#d0141c", "#1e7a36"], "blend": "normal"},
            {"shape": "flake", "colors": ["#ffffff", "#dff4ff"], "blend": "normal"},
            {"shape": "puff", "colors": ["#f4f8fc", "#e2eaf2"], "blend": "normal"},
            {"shape": "star", "colors": ["#fff3b0", "#e8b84a"], "blend": "add"}],
    backdrop="xm_express", title_wait="The Express is coming down the line...",
    title_shake="Tickets, please...")
XM24.award("North Pole Express", ["Passenger", "Ticket Holder", "Parcel Porter", "Stoker",
                                  "Engine Driver", "Conductor of the Express"],
           "Opened Coal Tenders aboard the North Pole Express, Christmas 2024.", "em_train",
           "flake")
XM24.bundle("pair", "Tender and Whistle", 1, 1050, "One Coal Tender, one Whistle Key.")
XM24.bundle("train", "The Whole Train", 3, 3000, "Three tenders, three keys. Saves 300.")

# ============================================================ 2025
KR_RED = "#8a1018"
FUR = "#2e221c"
FUR_HI = "#54402f"
HORN = "#cdb994"
BIRCH = "#ece6da"
EMBER = "#ff5a1a"
LODEN = "#3a5240"
RUST = "#8a4a22"
TONGUE = "#d4364a"
WICKER = "#7a5630"


def _twigs(base, tip, n, spread, w=0.045, c=BIRCH, **kw):
    """A birch switch: ``n`` bare twigs from ``base`` fanning out round
    ``tip`` by ``spread`` -- every one a rod, so no turn has to compose."""
    d = [tip[i] - base[i] for i in range(3)]
    length = math.sqrt(sum(v * v for v in d)) or 1.0
    u = [v / length for v in d]
    ref = [0.0, 1.0, 0.0] if abs(u[1]) < 0.9 else [1.0, 0.0, 0.0]
    p = [u[1] * ref[2] - u[2] * ref[1], u[2] * ref[0] - u[0] * ref[2], u[0] * ref[1] - u[1] * ref[0]]
    pl = math.sqrt(sum(v * v for v in p)) or 1.0
    p = [v / pl for v in p]
    q = [u[1] * p[2] - u[2] * p[1], u[2] * p[0] - u[0] * p[2], u[0] * p[1] - u[1] * p[0]]
    out = []
    for i in range(n):
        a = TAU * i / n + 0.4
        k = spread * (0.55 + 0.45 * ((i * 7) % 3) / 2)
        end = [tip[j] + (p[j] * math.cos(a) + q[j] * math.sin(a)) * k for j in range(3)]
        out.append(rod(base, end, w * (0.8 + 0.2 * (i % 2)), c if i % 3 else shade(c, 0.86),
                       **kw))
    return out


def _switch(base, tip, k=1.0, ribbon=KR_RED, n=6):
    """A switch with its handle bound in a ribbon a third of the way up."""
    tie = [base[j] + (tip[j] - base[j]) * 0.22 for j in range(3)]
    return _twigs(base, tip, n, 0.22 * k, 0.05 * k) + [
        rod([base[j] + (tip[j] - base[j]) * 0.16 for j in range(3)],
            [base[j] + (tip[j] - base[j]) * 0.28 for j in range(3)], 0.13 * k, ribbon),
        part("sph", tie, [0.12 * k, 0.12 * k, 0.12 * k], shade(ribbon, 1.15)),
    ]


def _cowbell(at, k=1.0, c=RUST, yaw=0.0, clapper=True):
    """A cowbell hanging from ``at`` (the top of its strap loop): flat
    front to back, wide at the mouth, rust on iron."""
    x, y, z = at
    out = [part("torus", [x, y - 0.03 * k, z], [0.14 * k, 0.04 * k, 0.14 * k], IRON, [PI / 2, yaw, 0],
                m="metal"),
           place("bell", [x, y - 0.06 * k, z], [0.34 * k, 0.44 * k, 0.24 * k], c, anchor=[0, 1.02, 0],
                 r=[0, yaw, 0], m="metal", decal="xm_rust", wrap=True)]
    if clapper:
        out.append(part("sph", [x, y - 0.50 * k, z], [0.09 * k, 0.09 * k, 0.09 * k], IRON, m="metal"))
    return out


def _goat_horn(side, at, k, lean=0.5, out=0.15, c=HORN):
    """One of the Krampus's horns: rising from ``at``, sweeping out to
    ``side`` and back by ``lean``, ridged to a dark tip."""
    r = [-lean, 0.0, -out] if side > 0 else [lean, PI, -out]
    tip = rotate([0.376 * k, 0.581 * k, 0], r)
    end = [at[0] + tip[0], at[1] + tip[1], at[2] + tip[2]]
    return [place("horn", list(at), [k, k, k], c, anchor=[0, 0, 0], r=r, decal="xm_hornridge",
                  wrap=True),
            part("sph", end, [0.05 * k, 0.05 * k, 0.05 * k], shade(c, 0.35))]


XM25 = Event(
    "christmas_2025", "christmas", 2025, "xm25",
    name="Krampusnacht", title="Krampusnacht",
    blurb="Christmas 2025 Saint Nicholas came to Blockhaven on the fifth of December, as "
          "he always does, and brought his companion with him, as he always does. The "
          "nice got oranges and gingerbread. The naughty heard chains in the street, "
          "and bells, and something with hooves coming up the stairs.",
    tagline="Have you been good this year?",
    starts="2025-12-01", ends="2025-12-30",
    colors={"accent": "#d8252e", "deep": "#140808", "glow": "#ff7a3a"},
    family_effects=["ember_storm", "raven_feathers", "candlelight_vigil"],
    hero_effect="krampuslauf", stencil="stencil_xm25")


@XM25.crate_model("Krampus Basket",
                  "The basket the Krampus carries on his back, woven from black willow, "
                  "bound in chains, a bell on the front and his switches tucked down "
                  "the side. Holds the Krampusnacht set. What else it has held, nobody "
                  "says. Needs a Horn Key.",
                  hinge=[0, 0.40, -0.62], keyhole=[0, 0.18, 0.66])
def _():
    parts = [
        # the basket: a woven tub wider at the mouth, a rim and a foot
        place("flare", [0, -0.70, 0], [1.56, 1.10, 1.22], WICKER, anchor=[0, 0, 0],
              decal="xm_kwicker", wrap=True),
        place("ring", [0, 0.30, 0], [1.66, 0.6, 1.32], shade(WICKER, 0.7), anchor=[0, 0, 0],
              decal="xm_kwicker", wrap=True),
        place("ring", [0, -0.72, 0], [1.42, 0.5, 1.12], shade(WICKER, 0.7), anchor=[0, 0, 0]),
        # an iron band round the middle, and the chain hung across the front
        place("ring", [0, -0.24, 0], [1.60, 0.30, 1.26], IRON, anchor=[0, 0, 0], m="metal"),
        # the lock: a rusted hasp on the rim
        part("rbox", [0, 0.18, 0.655], [0.30, 0.24, 0.06], RUST, m="metal", decal="keyhole",
             lock=1),
        part("box", [0, -0.22, -0.64], [0.86, 0.50, 0.02], "#000000", [0, PI, 0],
             decal="stencil_xm25", a=-1),
        # the lid: a woven dome, an iron band and the handle
        place("hemi", [0, 0.40, 0], [1.62, 0.56, 1.28], shade(WICKER, 0.85), anchor=[0, 0, 0],
              decal="xm_kwicker", wrap=True, lid=1),
        place("ring", [0, 0.38, 0], [1.68, 0.4, 1.34], IRON, anchor=[0, 0, 0], m="metal", lid=1),
        part("torus", [0, 0.72, 0], [0.36, 0.08, 0.36], IRON, [0, 0, PI / 2], m="metal", lid=1),
        # two little horns either side of the handle, and red eyes in the weave
        *[dict(p, lid=1) for p in _goat_horn(1, [0.30, 0.62, 0.0], 0.75, 0.1, 0.4)],
        *[dict(p, lid=1) for p in _goat_horn(-1, [-0.30, 0.62, 0.0], 0.75, 0.1, 0.4)],
        part("sph", [0.14, 0.58, 0.50], [0.10, 0.06, 0.04], EMBER, [0.6, 0, 0], m="neon", lid=1),
        part("sph", [-0.14, 0.58, 0.50], [0.10, 0.06, 0.04], EMBER, [0.6, 0, 0], m="neon", lid=1),
        # the glow from inside, through the gap
        part("cyl", [0, 0.36, 0], [1.40, 0.04, 1.10], "#ff7a3a", m="neon"),
    ]
    # the chain swagged across the front
    for k in range(15):
        t = k / 14
        th = -1.1 + t * 2.2
        y = -0.26 - math.sin(t * PI) * 0.20
        parts.append(part("torus", [math.sin(th) * 0.74, y, math.cos(th) * 0.60],
                          [0.13, 0.04, 0.09], IRON,
                          [0, th + (PI / 2 if k % 2 else 0.0), PI / 2 if k % 2 else 0.0],
                          m="metal"))
    parts += _cowbell([0, -0.52, 0.70], 0.80)
    # the switches tucked down the side, sprouting out over the rim
    parts += _switch([0.66, -0.50, -0.20], [0.98, 0.90, -0.40], 1.0)
    parts += _switch([0.70, -0.50, 0.10], [1.06, 0.80, 0.10], 0.9)
    parts += [part("rbox", [0.72, -0.20, -0.04], [0.06, 0.12, 0.50], "#3a2a1e")]
    return parts


@XM25.key_model("Horn Key",
                "An iron key with a little Krampus head for a bow: shaggy, horned, "
                "red-eyed, and the bit cut like a row of teeth. Opens one Krampus "
                "Basket. It is warm, and it should not be.", shoulder=-0.36)
def _():
    return [
        part("sph", [-0.62, 0, 0], [0.40, 0.42, 0.36], FUR, decal="xm_kfur", wrap=True),
        part("sph", [-0.62, -0.04, 0.12], [0.24, 0.20, 0.16], KR_RED),
        part("sph", [-0.56, 0.04, 0.17], [0.07, 0.05, 0.04], EMBER, m="neon"),
        part("sph", [-0.68, 0.04, 0.17], [0.07, 0.05, 0.04], EMBER, m="neon"),
        place("tri", [-0.62, -0.14, 0.19], [0.08, 0.09, 0.4], BONE, r=[0, 0, PI]),
        *_goat_horn(1, [-0.52, 0.14, 0], 0.62, 0.3, 0.3),
        *_goat_horn(-1, [-0.72, 0.14, 0], 0.62, 0.3, 0.3),
        part("cyl", [0.03, 0, 0], [0.09, 1.06, 0.09], IRON, [0, 0, PI / 2], m="metal"),
        part("torus", [-0.43, 0, 0], [0.18, 0.06, 0.18], RUST, [0, 0, PI / 2], m="metal"),
        place("tri", [0.36, -0.10, 0], [0.12, 0.16, 0.7], IRON, r=[0, 0, PI], m="metal"),
        place("tri", [0.46, -0.12, 0], [0.12, 0.22, 0.7], IRON, r=[0, 0, PI], m="metal"),
        place("tri", [0.56, -0.10, 0], [0.12, 0.16, 0.7], IRON, r=[0, 0, PI], m="metal"),
    ]


@XM25.hat("krampus_horns", "Horns of the Krampus",
          "A shaggy black cap and a pair of goat's horns as long as your arm, ridged, "
          "sweeping back. On the fifth of December you will find the crowd parts for "
          "you.", "legendary")
def _():
    parts = [
        cap(-0.32, 0.16, FUR, grow=0.08, decal="xm_kfur", wrap=True),
        ringband(-0.24, 0.12, FUR_HI, margin=0.07, decal="xm_kfur", wrap=True),
    ]
    parts += around(10, 0.80, -0.16, lambda a, x, z: part(
        "sph", [x, -0.16, z * 0.96], [0.32, 0.34, 0.30], FUR if int(round(a / (TAU / 10))) % 2
        else FUR_HI, decal="xm_kfur", wrap=True))
    parts += [part("sph", [0, 0.20, 0.30], [0.50, 0.24, 0.40], FUR_HI, decal="xm_kfur", wrap=True)]
    parts += _goat_horn(1, [0.40, 0.12, -0.04], 2.3, 0.55, 0.12)
    parts += _goat_horn(-1, [-0.40, 0.12, -0.04], 2.3, 0.55, 0.12)
    # pointed ears out to the sides, under the horns
    for s in (1, -1):
        parts.append(place("leaf", [0.92 * s, -0.36, -0.04], [0.9, 0.42, 1.0], FUR_HI,
                           r=[0, 0, -1.25 * s]))
        parts.append(place("leaf", [0.93 * s, -0.36, -0.01], [0.55, 0.30, 1.0], "#c46a6a",
                           r=[0, 0, -1.25 * s]))
    return parts


@XM25.hat("perchten_mask", "Perchten Mask",
          "A hand-carved Alpine Perchten mask: lacquered red, bulging eyes, fangs, a "
          "tongue down to your chest and a mane of black horsehair. Every village "
          "carves its own. This one is from the village nobody visits.", "legendary",
          hair="hide", face_cover=True)
def _():
    wood = "#a42a1c"
    parts = [
        # the horsehair mane behind and over the top
        place("hairlong", [0, -0.64, -0.04], [1.62, 1.36, 1.56], FUR, anchor=[0, 0, 0],
              decal="xm_kfur", wrap=True),
        part("capsule", [0.34, -1.10, -0.82], [0.30, 0.60, 0.26], FUR_HI, [0.3, 0, 0.1],
             decal="xm_kfur", wrap=True),
        part("capsule", [-0.30, -1.06, -0.84], [0.30, 0.60, 0.26], FUR, [0.3, 0, -0.1],
             decal="xm_kfur", wrap=True),
        part("capsule", [0.0, -1.14, -0.86], [0.30, 0.64, 0.26], FUR_HI, [0.3, 0, 0],
             decal="xm_kfur", wrap=True),
        # the carved face
        part("rbox", [0, -0.62, 0.79], [1.62, 1.36, 0.16], wood, decal="xm_perchten"),
        part("rbox", [0, -0.30, 0.89], [1.20, 0.12, 0.08], shade(wood, 0.7), [0.2, 0, 0]),
        part("sph", [0.30, -0.44, 0.88], [0.30, 0.26, 0.14], "#f4ecd0"),
        part("sph", [-0.30, -0.44, 0.88], [0.30, 0.26, 0.14], "#f4ecd0"),
        part("sph", [0.30, -0.44, 0.95], [0.12, 0.12, 0.04], BLACK),
        part("sph", [-0.30, -0.44, 0.95], [0.12, 0.12, 0.04], BLACK),
        part("sph", [0, -0.66, 0.92], [0.28, 0.32, 0.22], shade(wood, 1.12)),
        part("rbox", [0, -0.96, 0.88], [0.86, 0.22, 0.04], "#1a0808"),
        # fangs top and bottom
        place("tri", [0.24, -0.90, 0.91], [0.14, 0.16, 0.5], BONE, r=[0, 0, PI]),
        place("tri", [-0.24, -0.90, 0.91], [0.14, 0.16, 0.5], BONE, r=[0, 0, PI]),
        place("tri", [0.36, -1.02, 0.91], [0.10, 0.12, 0.5], BONE),
        place("tri", [-0.36, -1.02, 0.91], [0.10, 0.12, 0.5], BONE),
        # the tongue, lolling out and down
        place("ribbon", [0.04, -0.98, 0.94], [0.24, 0.64, 1.0], TONGUE, anchor=[0, 0.5, 0],
              r=[0.35, 0, 0.12]),
        part("sph", [0.04 + math.sin(0.12) * 0.62, -0.98 - math.cos(0.35) * 0.60, 0.94 + math.sin(0.35) * 0.62],
             [0.20, 0.10, 0.08], TONGUE),
    ]
    # four horns: two up off the brow, two short and twisted at the temples
    parts += _goat_horn(1, [0.40, 0.10, 0.30], 1.5, -0.10, 0.35)
    parts += _goat_horn(-1, [-0.40, 0.10, 0.30], 1.5, -0.10, 0.35)
    parts += _goat_horn(1, [0.86, -0.40, 0.40], 0.9, 0.3, 1.2)
    parts += _goat_horn(-1, [-0.86, -0.40, 0.40], 0.9, 0.3, 1.2)
    # horsehair round the edges of the mask
    for k in range(6):
        y = -0.10 - k * 0.22
        for s in (1, -1):
            parts.append(part("capsule", [0.90 * s, y - 0.10, 0.62], [0.16, 0.44, 0.14],
                              FUR if k % 2 else FUR_HI, [0.0, 0, 0.18 * s]))
    return parts


@XM25.hat("nikolaus_mitre", "Nikolaus's Mitre",
          "The tall white-and-gold mitre of the good bishop who walks in front of the "
          "Krampus, with the book of names. Wearing it does not make you nice. It does "
          "make the Krampus wait.", "rare")
def _():
    cream = "#f6f2e8"
    parts = [
        cap(-0.30, 0.06, cream, grow=0.04),
        ringband(-0.22, 0.20, GOLD, margin=0.06, m="metal", decal="xm_mitre_band", wrap=True),
        # the two tall panels: standing on the band at the brow and the nape
        # and leaning in until they all but meet at the top
        place("shield", [0, 0.80, 0.42], [1.64, 1.56, 0.7], cream, r=[-0.36, 0, PI],
              decal="xm_mitre"),
        place("shield", [0, 0.80, -0.42], [1.64, 1.56, 0.7], cream, r=[-0.36, PI, PI],
              decal="xm_mitre"),
        part("rbox", [0, 0.36, 0], [1.30, 0.60, 0.80], KR_RED),
        part("sph", [0, 1.54, 0.16], [0.12, 0.12, 0.12], GOLD, m="metal"),
        part("sph", [0, 1.54, -0.16], [0.12, 0.12, 0.12], GOLD, m="metal"),
    ]
    # the lappets down the back, fringed with gold
    for s in (1, -1):
        parts += [place("ribbon", [0.24 * s, -0.22, -0.84], [0.26, 0.86, 1.2], cream,
                        anchor=[0, 0.5, 0], r=[0.14, 0, 0], decal="xm_mitre_band"),
                  part("rbox", [0.24 * s, -1.06, -0.96], [0.28, 0.06, 0.06], GOLD, [0.14, 0, 0],
                       m="metal")]
    return parts


@XM25.hat("cowbell_crown", "Crown of Cowbells",
          "A spiked iron crown hung round with cowbells, the way the Krampus runners "
          "wear them. You will not sneak up on anyone ever again, and you will not "
          "care.", "rare")
def _():
    parts = [
        ringband(-0.22, 0.16, IRON, margin=0.07, m="metal"),
        place("spikecrown", [0, -0.24, 0], [1.98, 0.62, 1.92], IRON, anchor=[0, 0, 0],
              m="metal"),
        ringband(-0.30, 0.06, RUST, margin=0.10, m="metal"),
    ]
    parts += around(7, 1.06, 0.0, lambda a, x, z: _cowbell([x, -0.22, z], 0.62,
                                                            RUST if int(round(a * 7 / TAU)) % 2
                                                            else shade(RUST, 1.25), yaw=a))
    return parts


@XM25.hat("naughty_nightcap", "Naughty Nightcap",
          "A nightcap in black and red stripes for anybody who knows exactly which "
          "list they are on. The bobble is a lump of coal. It was a present.", "uncommon",
          hair="show")
def _():
    r = [0.0, 0.0, 0.10]
    tip = rotate([0.376 * 3.0, 0.581 * 1.9, 0], r)
    at = [-0.30, 0.10, 0.0]
    return [
        cap(-0.30, 0.16, BLACK, grow=0.06, decal="xm_naughtystripe", wrap=True),
        ringband(-0.24, 0.14, SNOW, margin=0.08, decal="fur", wrap=True),
        place("horn", at, [3.0, 1.9, 4.6], BLACK, anchor=[0, 0, 0], r=r,
              decal="xm_naughtystripe", wrap=True),
        part("sph", [at[0] + tip[0] + 0.04, at[1] + tip[1] - 0.10, at[2] + tip[2]],
             [0.28, 0.24, 0.26], COAL, decal="xm_coal", wrap=True),
        part("rbox", [at[0] + tip[0] + 0.08, at[1] + tip[1] - 0.36, 0.10], [0.20, 0.12, 0.01],
             "#f4ecd8", [0, 0, 0.2], decal="xm_naughtytag"),
        rod([at[0] + tip[0] + 0.04, at[1] + tip[1] - 0.16, 0.06],
            [at[0] + tip[0] + 0.08, at[1] + tip[1] - 0.30, 0.10], 0.015, KR_RED),
    ]


@XM25.hat("tyrolean_hat", "Tyrolean Hat",
          "Green loden felt, a twisted cord round the crown, an edelweiss and a "
          "chamois-hair brush stuck in the band. For walking up to the Krampuslauf "
          "and very much not taking part.", "uncommon", hair="show")
def _():
    parts = [
        place("brim", [0, -0.05, 0], [2.12, 1.0, 2.00], LODEN, anchor=[0, 0, 0], decal="felt",
              wrap=True),
        dome(-0.06, 0.78, LODEN, t="capcrown", decal="felt", wrap=True),
        part("rbox", [0, 0.70, 0], [0.12, 0.10, 0.80], shade(LODEN, 0.75)),
        ringband(0.08, 0.12, "#2a1e16", margin=0.04, decal="xm_cord", wrap=True),
    ]
    # the gamsbart: a brush of hair sprouting from a silver ferrule at the side
    base = [0.64, 0.10, -0.40]
    parts += [part("cyl", [base[0], base[1] + 0.06, base[2]], [0.16, 0.14, 0.16], SILVER,
                   [0, 0, -0.2], m="metal")]
    parts += _twigs([base[0], base[1] + 0.10, base[2]], [base[0] + 0.30, base[1] + 0.90, base[2] - 0.12],
                    9, 0.24, 0.07, "#3a3028")
    parts += _twigs([base[0], base[1] + 0.10, base[2]], [base[0] + 0.24, base[1] + 0.74, base[2] - 0.10],
                    6, 0.14, 0.06, "#d8ccb8")
    # the edelweiss on the front of the band
    parts += [place("flower", [0.30, 0.14, 0.82], [0.30, 0.30, 0.30], "#f4f2ea", r=[1.3, 0, 0]),
              part("sph", [0.30, 0.15, 0.86], [0.08, 0.06, 0.08], "#f2c230")]
    return parts


@XM25.hat("birch_crown", "Crown of Switches",
          "Nine bundles of birch switches bound in red ribbon, standing up round your "
          "head like a bonfire waiting for a match. Every one has been used. You do not "
          "want to know on whom.", "rare", hair="show")
def _():
    parts = [ringband(-0.20, 0.16, KR_RED, margin=0.08, decal="felt", wrap=True),
             ringband(-0.12, 0.04, GOLD, margin=0.10, m="metal")]
    for k in range(9):
        a = TAU * k / 9 + 0.17
        s, c = math.sin(a), math.cos(a)
        parts += _switch([s * 0.98, -0.26, c * 0.95], [s * 1.38, 0.95, c * 1.32], 0.8, n=5)
    return parts


@XM25.back("krampus_bells", "Krampuslauf Bells",
           "Three great rusted cowbells strapped across your back on a leather harness, "
           "the way the runners wear them through the streets on the fifth. They are "
           "loud. That is the point.", "legendary")
def _():
    leather = "#3a2a1e"
    parts = straps(leather) + [
        part("rbox", [0, 0.40, -0.10], [1.70, 0.16, 0.14], leather, decal="leather", wrap=True),
        part("rbox", [0, -0.30, -0.10], [1.50, 0.16, 0.14], leather, decal="leather", wrap=True),
        part("rbox", [0.70, 0.05, -0.10], [0.14, 0.86, 0.12], leather),
        part("rbox", [-0.70, 0.05, -0.10], [0.14, 0.86, 0.12], leather),
    ]
    parts += _cowbell([0, 0.62, -0.46], 2.30, RUST)
    parts += _cowbell([0.66, 0.40, -0.36], 1.60, shade(RUST, 1.2), yaw=-0.3)
    parts += _cowbell([-0.66, 0.40, -0.36], 1.60, shade(RUST, 0.85), yaw=0.3)
    parts += [part("torus", [0, 0.64, -0.24], [0.34, 0.07, 0.34], IRON, [PI / 2, 0, 0], m="metal")]
    return parts


@XM25.back("krampus_tail", "Krampus Tail",
           "A long black tail with a tuft on the end, hung from the belt and swishing. "
           "You did not have one this morning. You do now.", "rare")
def _():
    pts = [(0, -0.82, -0.10), (0.08, -1.02, -0.40), (0.16, -1.28, -0.66), (0.20, -1.58, -0.82),
           (0.16, -1.88, -0.86), (0.04, -2.10, -0.74), (-0.12, -2.20, -0.52)]
    parts = [part("rbox", [0, -0.82, -0.04], [0.40, 0.30, 0.10], "#3a2a1e")]
    for i, p in enumerate(pts):
        w = 0.40 - i * 0.03
        parts.append(part("sph", list(p), [w, w * 1.1, w], FUR if i % 2 else FUR_HI,
                          decal="xm_kfur", wrap=True))
        if i:
            parts.append(rod(pts[i - 1], p, w * 0.9, FUR, decal="xm_kfur", wrap=True))
    end = pts[-1]
    parts += [place("flame", [end[0] - 0.14, end[1] + 0.04, end[2] + 0.10], [0.70, 0.60, 2.4], FUR,
                    r=[0, 0, 1.2], decal="xm_kfur"),
              part("sph", [end[0] - 0.08, end[1], end[2] + 0.04], [0.30, 0.26, 0.30], FUR_HI,
                   decal="xm_kfur", wrap=True)]
    return parts


@XM25.hairdo("goat_shag", "Goat Shag",
             "Long, black and matted, with two little horn nubs poking through. Smells "
             "faintly of a stable, which is a mercy.", "uncommon")
def _():
    parts = [place("hairlong", [0, 0, 0], [1.05, 1.05, 1.05], FUR, anchor=[0, 0, 0],
                   decal="strands", wrap=True)]
    for k in range(9):
        a = k * TAU / 9
        parts.append(part("sph", [math.sin(a) * 0.36, 0.62 + (k % 3) * 0.02, math.cos(a) * 0.34 - 0.02],
                          [0.30, 0.20, 0.30], FUR if k % 2 else FUR_HI, decal="xm_kfur", wrap=True))
    for s in (1, -1):
        parts += [place("horn", [0.20 * s, 0.62, 0.18], [0.55, 0.55, 0.55], HORN, anchor=[0, 0, 0],
                        r=[0.1, 0.0 if s > 0 else PI, 0.25], decal="xm_hornridge", wrap=True)]
        parts += [part("capsule", [0.62 * s, -0.36, -0.10], [0.14, 0.40, 0.14], FUR, [0, 0, 0.10 * s]),
                  part("capsule", [0.40 * s, -0.40, -0.62], [0.14, 0.40, 0.14], FUR_HI, [0.1, 0, 0.08 * s])]
    return parts


@XM25.hairdo("alpine_braids", "Alpine Braids",
             "Golden plaits pinned round the crown and two more down the back, tied off "
             "in red ribbon, very neat. Very nice. Definitely on the nice list.",
             "uncommon")
def _():
    blond = "#e8c070"
    parts = [place("hairmid", [0, 0, 0], [1.03, 1.03, 1.03], blond, anchor=[0, 0, 0],
                   decal="strands", wrap=True)]
    # the plait round the crown: beads of hair alternating as they twist
    for k in range(18):
        a = TAU * k / 18
        parts.append(part("sph", [math.sin(a) * 0.34, 0.60 + 0.015 * (k % 2), math.cos(a) * 0.33],
                          [0.17, 0.12, 0.17], blond if k % 2 else shade(blond, 0.88),
                          [0, a, 0.5 if k % 2 else -0.5]))
    for s in (1, -1):
        for k in range(5):
            parts.append(part("sph", [0.24 * s, -0.46 - k * 0.11, -0.64 - k * 0.01],
                              [0.15 - k * 0.01, 0.13, 0.13], blond if k % 2 else shade(blond, 0.88),
                              [0, 0, 0.5 if k % 2 else -0.5]))
        parts += gift_bow([0.24 * s, -1.04, -0.68], 0.26, KR_RED, tails=False, yaw=PI / 2)
    return parts


XM25.face("krampus_grin", "Krampus Grin",
          "Burning eyes, a mouth full of fangs and a tongue that does not stop where "
          "tongues should stop.", [
              {"k": "poly", "pts": [[-0.32, -0.24], [-0.10, -0.14], [-0.14, -0.08], [-0.30, -0.14]],
               "c": "#ff7a1a"},
              {"k": "poly", "pts": [[0.32, -0.24], [0.10, -0.14], [0.14, -0.08], [0.30, -0.14]],
               "c": "#ff7a1a"},
              {"k": "ellipse", "x": -0.19, "y": -0.14, "w": 0.04, "h": 0.06, "c": "#16171b"},
              {"k": "ellipse", "x": 0.19, "y": -0.14, "w": 0.04, "h": 0.06, "c": "#16171b"},
              {"k": "line", "x1": -0.36, "y1": -0.30, "x2": -0.08, "y2": -0.20, "w": 0.05,
               "c": "#16171b"},
              {"k": "line", "x1": 0.36, "y1": -0.30, "x2": 0.08, "y2": -0.20, "w": 0.05,
               "c": "#16171b"},
              {"k": "poly", "pts": [[-0.30, 0.04], [0.30, 0.04], [0.18, 0.18], [-0.18, 0.18]],
               "c": "#16171b"},
              {"k": "poly", "pts": [[-0.24, 0.05], [-0.18, 0.13], [-0.12, 0.05]], "c": "#ffffff"},
              {"k": "poly", "pts": [[0.24, 0.05], [0.18, 0.13], [0.12, 0.05]], "c": "#ffffff"},
              {"k": "poly", "pts": [[-0.08, 0.10], [0.10, 0.10], [0.08, 0.40], [0.0, 0.46],
                                    [-0.06, 0.40]], "c": "#d4364a"},
          ], "rare")
XM25.face("nice_list", "Nice as Pie",
          "Big shining eyes, rosy cheeks and a smile that has absolutely never done "
          "anything wrong, and one small bead of sweat.", [
              {"k": "ellipse", "x": -0.19, "y": -0.12, "w": 0.15, "h": 0.19, "c": "#16171b"},
              {"k": "ellipse", "x": 0.19, "y": -0.12, "w": 0.15, "h": 0.19, "c": "#16171b"},
              {"k": "ellipse", "x": -0.16, "y": -0.16, "w": 0.06, "h": 0.07, "c": "#ffffff"},
              {"k": "ellipse", "x": 0.22, "y": -0.16, "w": 0.06, "h": 0.07, "c": "#ffffff"},
              {"k": "ellipse", "x": -0.32, "y": 0.06, "w": 0.14, "h": 0.09, "c": "#ff9aa8"},
              {"k": "ellipse", "x": 0.32, "y": 0.06, "w": 0.14, "h": 0.09, "c": "#ff9aa8"},
              {"k": "arc", "x": 0.0, "y": 0.06, "r": 0.10, "a0": 0.05, "a1": 0.45, "w": 0.035,
               "c": "#16171b"},
              {"k": "poly", "pts": [[0.36, -0.36], [0.40, -0.26], [0.36, -0.22], [0.32, -0.26]],
               "c": "#8fd0ff"},
          ], "uncommon")
XM25.shirt("krampus_pelt", "Krampus Pelt",
           "A shaggy black pelt, a red chest and a chain across it with a bell on, "
           "worn the way the runners wear them: all the way to the knuckles.",
           {"torso": FUR, "arms": FUR, "decal": "xm_tee_krampus", "weave": "xm_kfur"}, "rare")
XM25.pants("lederhosen", "Krampuslauf Lederhosen",
           "Deerskin shorts with an embroidered front flap and grey wool knee socks, "
           "for standing at the side of the road with a mug of something hot, "
           "cheering.",
           {"legs": "#6a4a2e", "weave": "xm_lederhosen", "length": 0.55, "skin": "#d8d2c4",
            "cuff": "#2a1e16"})
XM25.belt("chain_belt", "Chain Belt",
          "A length of old iron chain worn as a belt and padlocked at the front. The "
          "key went in the basket.",
          {"band": IRON, "buckle": RUST, "width": 0.22, "metal": True, "weave": "xm_chainlink"})


@XM25.weapon("birch_rute", "The Rute",
             "A bundle of birch switches bound in red ribbon. It does not hurt much. "
             "It does not have to: every fifth swat, everybody near you gets the lot "
             "at once.",
             {"kind": "melee", "damage": 18, "headshot": 1.0, "rpm": 170, "range": 9.5,
              "arc": 0.80, "sound": "swing", "knockback": 4,
              "aoe_every": {"every": 5, "radius": 9.0, "damage": 34, "knock": 26,
                            "label": "Thrashing", "fx": "pulse",
                            "on_hit": {"slow": [0.35, 2.0]}}},
             [["+", "Fast: nearly three swats a second"],
              ["+", "Every fifth hit thrashes everyone within 9 studs: 34 damage, a shove "
                    "and slowed by 35% for 2 seconds"],
              ["-", "18 damage a swat"],
              ["-", "Short reach"]], rarity="legendary")
def _():
    return [part("rbox", [0, -0.02, -0.08], [0.16, 0.16, 0.34], "#5a3a22")] + \
        _switch([0, 0, -0.20], [0, 0.10, 1.70], 1.1, n=7)


@XM25.weapon("krampus_chains", "Krampus's Chains",
             "A length of rattling chain with a hook on the end. Crack it at a crowd and "
             "it wraps the lot and drags them to you, where they find they cannot go "
             "anywhere for a moment.",
             {"kind": "cone", "damage": 18, "rpm": 50, "mag": 4, "reload": 2.4, "range": 18.0,
              "auto": False, "sound": "swing", "recoil": 1.4, "reserve": 24,
              "cone": {"angle": 0.42, "pull": 34, "color": "#8a8d92"},
              "on_hit": {"root": 1.2}},
             [["+", "Drags everyone in a narrow cone 18 studs deep right up to you"],
              ["+", "...and holds them there for 1.2 seconds"],
              ["-", "18 damage"],
              ["-", "Four cracks to a load"]], rarity="legendary")
def _():
    parts = [part("rbox", [0, -0.04, -0.02], [0.18, 0.40, 0.22], "#3a2a1e", [-0.2, 0, 0],
                  decal="leather", wrap=True)]
    for k in range(14):
        t = k / 13
        parts.append(part("torus", [0.0, 0.06 - math.sin(t * PI * 0.8) * 0.26, 0.18 + t * 1.16],
                          [0.13, 0.04, 0.16], IRON if k % 3 else RUST,
                          [0, 0, PI / 2 if k % 2 else 0.0], m="metal"))
    parts += [place("hook", [0, -0.02, 1.38], [0.42, 0.42, 0.30], IRON, anchor=[0, 0, 0],
                    r=[PI / 2, 0, -PI / 2], m="metal"),
              part("cyl", [0, -0.02, 1.36], [0.10, 0.06, 0.10], RUST, [PI / 2, 0, 0], m="metal")]
    return parts


@XM25.weapon("brimstone", "Brimstone Coal",
             "Not coal for your stocking. A lump of brimstone, lit, that sticks to "
             "whatever it hits and goes up a second later in a cloud of yellow smoke "
             "nobody wants to breathe.",
             {"kind": "projectile", "projectile": "brimstone", "damage": 10, "splash": 5.5,
              "splash_damage": 30, "rpm": 60, "mag": 4, "reload": 2.6, "speed": 58,
              "range": 220, "auto": False, "sound": "throw", "recoil": 1.0, "reserve": 24,
              "gravity_scale": 1.1, "self_damage": 0.4, "knockback": 6,
              "sticky": True, "fuse": 1.0,
              "on_hit": {"poison": [5, 6.0]},
              "trail_colors": ["#ffd84a", "#ff7a1a"]},
             [["+", "Sticks to walls, floors and people, and goes off a second later"],
              ["+", "Poisons everyone in the cloud: 5 a second for 6 seconds"],
              ["-", "30 splash damage"],
              ["-", "Lobbed: it drops"]], rarity="legendary",
             proj=lambda: [part("sph", [0, 0, 0], [0.70, 0.62, 0.66], COAL, decal="xm_coal",
                                wrap=True),
                           part("sph", [0, 0, 0], [0.86, 0.80, 0.82], "#ffd84a", m="neon",
                                a=0.25)])
def _():
    # a lump of it, lit, held out in a pair of smith's tongs
    return [
        rod([0.05, -0.02, -0.16], [0.07, 0.02, 0.52], 0.05, IRON, m="metal"),
        rod([-0.05, -0.06, -0.16], [-0.07, 0.10, 0.52], 0.05, IRON, m="metal"),
        part("cyl", [0, 0.01, 0.20], [0.10, 0.18, 0.10], RUST, [0, 0, PI / 2], m="metal"),
        part("rbox", [0, -0.04, -0.10], [0.16, 0.14, 0.24], "#3a2a1e", decal="leather", wrap=True),
        rod([0.07, 0.02, 0.52], [0.10, 0.00, 0.70], 0.05, IRON, m="metal"),
        rod([-0.07, 0.10, 0.52], [-0.10, 0.14, 0.70], 0.05, IRON, m="metal"),
        part("sph", [0, 0.07, 0.80], [0.30, 0.26, 0.28], COAL, decal="xm_coal", wrap=True),
        part("sph", [0.02, 0.08, 0.80], [0.34, 0.30, 0.32], "#ffd84a", m="neon", a=0.3),
        part("sph", [0.04, 0.18, 0.84], [0.10, 0.06, 0.10], "#ffd84a", m="neon"),
    ]


@XM25.gear("perchten_lantern", "Krampuslauf Lantern",
           "A pierced iron lantern on a pole, carried at the head of the run. Shake "
           "it and you are gone in a puff of brimstone and back twenty studs on, with "
           "whatever was on you left behind in the smoke.",
           {"kind": "ability", "cooldown": 14, "sound": "whoosh",
            "ability": {"blink": {"dist": 20}, "cleanse": {"heal": 15}}},
           [["+", "Steps you up to 20 studs the way you are looking, through nothing "
                  "solid"],
            ["+", "Shakes off every burn, poison, slow and snare, and heals 15"],
            ["-", "14 second cooldown"],
            ["-", "No damage at all"]], rarity="rare")
def _():
    return [
        rod([0, -0.10, -0.10], [0, 0.40, 0.30], 0.07, "#3a2a1e"),
        rod([0, 0.40, 0.30], [0, 0.44, 0.62], 0.05, IRON, m="metal"),
        part("cyl", [0, 0.20, 0.64], [0.30, 0.34, 0.30], IRON, m="metal", decal="xm_pierced",
             wrap=True),
        part("cyl", [0, 0.20, 0.64], [0.22, 0.28, 0.22], "#ff9a3a", m="neon"),
        place("cone", [0, 0.48, 0.64], [0.36, 0.22, 0.36], IRON, m="metal"),
        part("torus", [0, 0.60, 0.64], [0.10, 0.03, 0.10], IRON, [PI / 2, 0, 0], m="metal"),
        part("rbox", [0, 0.02, 0.64], [0.32, 0.04, 0.32], IRON, m="metal"),
    ]


XM25.effect("krampuslauf", name="Krampuslauf", rate=2.4, life=[1.6, 2.2],
            size=[0.30, 0.42], grow=0.0, gravity=0.0, spread=0.25, rise=[0.1, 0.3],
            blend="normal", spin=2.0, colors=["#8a4a22", "#5a5d62", "#ff7a3a"],
            shape="bell", radius=0.9, orbit=2.2, wobble=0.5)
XM25.effect("birch_flurry", name="Birch Flurry", rate=2.6, life=[1.8, 2.6],
            size=[0.36, 0.50], grow=0.0, gravity=0.6, spread=0.5, rise=[0.6, 1.0],
            blend="normal", spin=3.0, colors=["#ece6da", "#8a1018", "#c9a26a"],
            shape="xm_birch", radius=0.6)
XM25.opening(
    sky={"top": "#0a0406", "horizon": "#5a1a14", "sun": [0.1, 0.7, 0.6], "clouds": 0.5,
         "tint": "#ffd0b0"},
    ambient="#5a2a24", beam="#ff7a3a", seep="krampuslauf", after="birch_flurry",
    burst=["#ff7a3a", "#d8252e", "#ece6da", "#2e221c"],
    pieces=[{"shape": "bell", "colors": ["#8a4a22", "#5a5d62"], "blend": "normal"},
            {"shape": "xm_birch", "colors": ["#ece6da", "#8a1018"], "blend": "normal"},
            {"shape": "flame", "colors": ["#ff7a3a", "#ffd84a"], "blend": "add"},
            {"shape": "flake", "colors": ["#ffffff", "#ffd0b0"], "blend": "normal"}],
    backdrop="xm_krampus", title_wait="Something is rattling its chains...",
    title_shake="Have you been good?")
XM25.award("Krampusnacht", ["Nice", "On Thin Ice", "Naughty", "Very Naughty",
                            "Basket Case", "The Krampus's Own"],
           "Opened Krampus Baskets on Krampusnacht, Christmas 2025.", "em_krampus", "flake")
XM25.bundle("pair", "Basket and Horn", 1, 1050, "One Krampus Basket, one Horn Key.")
XM25.bundle("naughty_three", "Three in the Basket", 3, 3000,
            "Three baskets, three keys. Saves 300.")

# ============================================================ 2026
ICE = "#bfe8ff"
GLACIER = "#7ec8e8"
AURORA_G = "#3dffb0"
AURORA_P = "#a45aff"
POLAR_NIGHT = "#0c1430"
FROST = "#dfe9f2"
PARKA = "#e8641e"
POLAR_FUR = "#f6f4ee"


def _crystal(at, h, w, c=ICE, tilt=(0.0, 0.0), **kw):
    """An ice crystal standing on ``at``, ``h`` tall and ``w`` across,
    leaning ``tilt`` (towards +Z, towards +X)."""
    kw.setdefault("m", "glass")
    return place("icicle", list(at), [w, h, w], c, anchor=[0, 1.0, 0],
                 r=[PI + tilt[0], 0.0, tilt[1]], **kw)


def _north_star(at, k, c=FROST, glow="#e8fbff", yaw=0.0):
    """The north star: an eight-pointed spark, a long four-point over a
    short one turned by an eighth, a light in the middle."""
    x, y, z = at
    return [place("sparkle", [x, y, z], [k, k, 0.5 * k], c, r=[0, yaw, 0], m="metal"),
            place("sparkle", [x, y, z], [0.62 * k, 0.62 * k, 0.6 * k], shade(c, 0.9),
                  r=[0, yaw, PI / 4], m="metal"),
            part("sph", [x, y, z], [0.22 * k, 0.22 * k, 0.16 * k], glow, m="neon")]


XM26 = Event(
    "christmas_2026", "christmas", 2026, "xm26",
    name="Aurora Winterlight", title="Aurora Winterlight",
    blurb="Christmas 2026 the sky over the pole is going to light up green and violet "
          "every night of December, and Blockhaven is packing for the trip: glacier ice "
          "that holds the light, owls and bears and foxes in the snow, and a star to "
          "steer home by. It has not started yet. The crates are already boxed.",
    tagline="Look up.",
    starts="2026-12-01", ends="2026-12-30",
    colors={"accent": "#3dffb0", "deep": "#0c1430", "glow": "#a45aff"},
    family_effects=["frostbite", "starstruck", "void_mist"],
    hero_effect="aurora_veil", stencil="stencil_xm26")


@XM26.crate_model("Glacier Chest",
                  "A chest cut out of a block of glacier ice ten thousand years old, "
                  "bound in frost-silver, with crystals growing on the lid and the "
                  "northern lights caught inside it, still moving. Holds the Aurora "
                  "Winterlight set. Needs a Polaris Key.",
                  hinge=[0, 0.30, -0.54], keyhole=[0, -0.02, 0.56])
def _():
    parts = [
        # the light inside, behind the ice
        part("rbox", [0, -0.10, 0], [1.40, 0.60, 0.80], AURORA_G, m="neon", a=0.85,
             decal="xm_aurora", wrap=True),
        # the ice: a clear block, frosted round the edges
        part("rbox", [0, -0.08, 0], [1.70, 0.76, 1.06], "#9fdcff", m="glass", a=0.38,
             decal="xm_glacier", wrap=True),
        part("rbox", [0, -0.50, 0], [1.76, 0.10, 1.12], FROST, m="metal"),
        part("rbox", [0, 0.28, 0], [1.76, 0.05, 1.12], FROST, m="metal"),
        # the lock: a frost-silver plate with a star cut over the keyhole
        part("rbox", [0, -0.02, 0.555], [0.28, 0.30, 0.05], FROST, m="metal", decal="keyhole",
             lock=1),
        part("box", [0, -0.08, -0.545], [0.86, 0.50, 0.02], "#000000", [0, PI, 0],
             decal="stencil_xm26", a=-1),
        # the lid: an ice slab with crystals growing out of it and the star on top
        part("rbox", [0, 0.40, 0], [1.74, 0.22, 1.10], ICE, m="glass", a=0.7,
             decal="xm_glacier", wrap=True, lid=1),
        part("rbox", [0, 0.52, 0], [1.60, 0.04, 0.96], "#ffffff", lid=1),
    ]
    for x, z, h, w, t in ((-0.52, 0.18, 0.62, 0.30, (0.15, 0.2)), (-0.34, -0.20, 0.44, 0.24, (-0.2, 0.1)),
                          (0.40, 0.14, 0.52, 0.28, (0.1, -0.25)), (0.58, -0.22, 0.36, 0.22, (-0.2, -0.3)),
                          (-0.70, -0.30, 0.30, 0.18, (-0.1, 0.4))):
        parts.append(dict(_crystal([x, 0.50, z], h, w, ICE if x < 0 else GLACIER, t), lid=1))
    parts += [dict(p, lid=1) for p in _north_star([0, 0.98, 0.0], 0.62)]
    parts += [dict(part("cyl", [0, 0.72, 0], [0.06, 0.40, 0.06], FROST, m="metal"), lid=1)]
    # silver straps over the corners and icicles hanging off the base rim
    for x in (-0.86, 0.86):
        parts.append(part("rbox", [x, -0.10, 0], [0.06, 0.80, 1.12], FROST, m="metal"))
    for k in range(7):
        x = -0.72 + k * 0.24
        parts.append(place("icicle", [x, -0.56, 0.57], [0.10, 0.18 + 0.08 * (k % 3), 0.10], ICE,
                           anchor=[0, 1.0, 0], m="glass"))
    return parts


@XM26.key_model("Polaris Key",
                "A frost-silver key with the north star for a bow and an icicle for a "
                "bit. Opens one Glacier Chest. Hold it up at night and it points north.",
                shoulder=-0.30)
def _():
    return [
        *_north_star([-0.64, 0, 0], 0.72),
        part("torus", [-0.64, 0, 0], [0.46, 0.05, 0.46], FROST, [PI / 2, 0, 0], m="metal"),
        part("cyl", [0.10, 0, 0], [0.08, 0.80, 0.08], FROST, [0, 0, PI / 2], m="metal"),
        part("torus", [-0.30, 0, 0], [0.16, 0.05, 0.16], GLACIER, [0, 0, PI / 2], m="metal"),
        place("icicle", [0.40, 0.0, 0], [0.12, 0.30, 0.12], ICE, anchor=[0, 1.0, 0], m="glass"),
        place("icicle", [0.52, 0.0, 0], [0.10, 0.22, 0.10], ICE, anchor=[0, 1.0, 0], m="glass"),
        part("sph", [0.50, 0, 0], [0.06, 0.06, 0.06], AURORA_G, m="neon"),
    ]


@XM26.hat("aurora_crown", "Aurora Crown",
          "A tiara of ice crystals, frost-silver and the north star, and above it a "
          "ring of the northern lights itself, turning slowly. Do not ask how it was "
          "caught.", "legendary", hair="show")
def _():
    parts = [ringband(-0.20, 0.10, FROST, margin=0.05, m="metal"),
             ringband(-0.12, 0.04, GLACIER, margin=0.07, m="metal")]
    for k in range(16):
        a = TAU * k / 16
        h = 0.18 + 0.46 * max(0.0, math.cos(a)) ** 2
        parts.append(_crystal([math.sin(a) * 0.96, -0.16, math.cos(a) * 0.93], h, 0.20,
                              ICE if k % 2 else GLACIER, (0.25 * math.cos(a), 0.25 * math.sin(a))))
    parts += _north_star([0, 0.62, 0.98], 0.42)
    # a curtain of the lights round the crown, turning slowly
    parts += [place("ring", [0, -0.10, 0], [2.20, 3.2, 2.12], AURORA_G, anchor=[0, 0, 0],
                    m="neon", a=0.32, decal="xm_aurora", wrap=True, spin=0.5)]
    return parts


@XM26.hat("polar_bear", "Polar Bear Hat",
          "A white bear asleep on your head, nose on the front, paws hanging over "
          "your ears. It is very warm. It is also, you suspect, very heavy, and "
          "starting to wake up.", "rare")
def _():
    nose = "#1a1a20"
    parts = [
        dome(-0.42, 0.92, POLAR_FUR, t="capcrown", decal="xm_polarfur", wrap=True),
        ringband(-0.36, 0.10, shade(POLAR_FUR, 0.92), margin=0.07, decal="xm_polarfur", wrap=True),
        # the muzzle over the brow, the nose and the shut, sleepy eyes
        part("sph", [0, 0.02, 0.82], [0.56, 0.38, 0.42], shade(POLAR_FUR, 0.96), decal="xm_polarfur",
             wrap=True),
        part("sph", [0, 0.12, 1.02], [0.20, 0.13, 0.10], nose, m="glass"),
        part("rbox", [0, -0.06, 1.02], [0.03, 0.10, 0.02], nose),
        part("rbox", [0.26, 0.30, 0.82], [0.14, 0.03, 0.04], nose, [0, 0, -0.2]),
        part("rbox", [-0.26, 0.30, 0.82], [0.14, 0.03, 0.04], nose, [0, 0, 0.2]),
    ]
    for s in (1, -1):
        parts += [
            part("sph", [0.50 * s, 0.50, -0.02], [0.32, 0.30, 0.18], POLAR_FUR, decal="xm_polarfur",
                 wrap=True),
            part("sph", [0.50 * s, 0.50, 0.05], [0.18, 0.16, 0.06], "#c9c4ba"),
            # a paw hanging down each side, black pads showing
            part("capsule", [0.92 * s, -0.64, 0.12], [0.30, 0.66, 0.30], POLAR_FUR,
                 [0.0, 0, 0.12 * s], decal="xm_polarfur", wrap=True),
            part("sph", [0.94 * s, -1.00, 0.24], [0.24, 0.14, 0.12], "#2a2a30"),
        ]
    return parts


@XM26.hat("snowy_owl", "Snowy Owl",
          "A snowy owl, perched, white with black flecks and two enormous yellow eyes "
          "that see everything you do and judge most of it.", "rare", hair="show")
def _():
    owl = "#f8f6f0"
    parts = [
        part("sph", [0, 0.48, -0.04], [0.82, 0.90, 0.74], owl, decal="xm_owlspeckle", wrap=True),
        part("sph", [0, 1.04, 0.04], [0.66, 0.56, 0.60], owl, decal="xm_owlspeckle", wrap=True),
        part("sph", [0, 1.00, 0.24], [0.52, 0.40, 0.24], "#ffffff"),
        part("sph", [0.14, 1.04, 0.33], [0.18, 0.18, 0.06], "#f2c230"),
        part("sph", [-0.14, 1.04, 0.33], [0.18, 0.18, 0.06], "#f2c230"),
        part("sph", [0.14, 1.04, 0.36], [0.09, 0.09, 0.03], BLACK),
        part("sph", [-0.14, 1.04, 0.36], [0.09, 0.09, 0.03], BLACK),
        place("cone", [0, 0.92, 0.36], [0.08, 0.12, 0.08], "#3a3a40", r=[PI, 0, 0]),
        place("wedge", [0, 0.20, -0.44], [0.40, 0.30, 0.30], owl, r=[0.5, 0, 0]),
    ]
    for s in (1, -1):
        parts += [
            part("sph", [0.38 * s, 0.42, -0.08], [0.20, 0.72, 0.58], shade(owl, 0.97),
                 [0, 0, -0.12 * s], decal="xm_owlspeckle", wrap=True),
            part("rbox", [0.14 * s, 0.03, 0.12], [0.16, 0.06, 0.22], "#c9c4b0"),
            part("rbox", [0.14 * s, 0.03, 0.25], [0.14, 0.04, 0.06], "#2a2a30"),
        ]
    return parts


@XM26.hat("igloo", "Igloo Hat",
          "A little igloo of packed snow blocks, a tunnel out the front and a "
          "lamp lit inside. Somebody small lives in there. They have asked you to "
          "keep still.", "uncommon")
def _():
    parts = [
        dome(-0.30, 0.94, POLAR_FUR, decal="xm_iceblocks", wrap=True),
        ringband(-0.26, 0.08, shade(POLAR_FUR, 0.9), margin=0.06),
        part("cyl", [0, -0.06, 0.90], [0.52, 0.42, 0.50], POLAR_FUR, [PI / 2, 0, 0],
             decal="xm_iceblocks", wrap=True),
        part("disc", [0, -0.06, 1.11], [0.34, 0.34, 0.04], "#ffb04a", m="neon"),
        part("rbox", [0, -0.24, 1.0], [0.40, 0.06, 0.30], shade(POLAR_FUR, 0.9)),
    ]
    parts += around(5, 0.56, 0.0, lambda a, x, z: place(
        "sparkle", [x, 0.44 + 0.08 * math.cos(a * 3), z], [0.14, 0.14, 0.4], "#e8fbff",
        r=[0, a, 0], m="neon"), start=0.4)
    return parts


@XM26.hat("trapper", "Northern Trapper",
          "Deep blue felt and white fur, the flaps down over the ears and the front "
          "turned up, the north star pinned to it. For waiting outside in the cold all "
          "night for the lights.", "uncommon")
def _():
    navy = "#1f2a4a"
    parts = [
        cap(-0.34, 0.22, navy, grow=0.06, decal="felt", wrap=True),
        band(-0.26, 0.18, POLAR_FUR, grow=0.12, decal="xm_polarfur", wrap=True),
        # the front flap turned up against the crown
        part("rbox", [0, -0.02, 0.84], [1.40, 0.52, 0.16], POLAR_FUR, [-0.18, 0, 0], decal="xm_polarfur",
             wrap=True),
        part("rbox", [0, 0.20, -0.84], [1.30, 0.34, 0.12], POLAR_FUR, [0.20, 0, 0], decal="xm_polarfur",
             wrap=True),
    ]
    for s in (1, -1):
        # the ear flaps down: felt outside, the fur lining showing round the edge
        parts += [part("rbox", [0.86 * s, -0.60, -0.02], [0.12, 0.80, 0.86], POLAR_FUR,
                       [0, 0, 0.06 * s], decal="xm_polarfur", wrap=True),
                  part("rbox", [0.93 * s, -0.56, -0.02], [0.05, 0.66, 0.72], "#2a3a66",
                       [0, 0, 0.06 * s], decal="felt"),
                  rod([0.92 * s, -0.98, 0.10], [0.80 * s, -1.36, 0.24], 0.04, navy)]
    parts += _north_star([0, 0.10, 0.94], 0.30)
    return parts


@XM26.hat("star_halo", "Star of the North",
          "A slow ring of ice shards turning round your head, and the north star "
          "hanging over it. You will never be lost again. You may be followed.", "rare",
          hair="show")
def _():
    parts = around(8, 0.84, 0.0, lambda a, x, z: _crystal(
        [x, 0.40, z], 0.42 if int(round(a * 8 / TAU)) % 2 else 0.28, 0.20,
        ICE if int(round(a * 8 / TAU)) % 2 else GLACIER, (0.5 * math.cos(a), 0.5 * math.sin(a)),
        spin=0.8))
    parts += [place("ring", [0, 0.40, 0], [1.72, 0.3, 1.68], FROST, anchor=[0, 0, 0], m="metal")]
    parts += _north_star([0, 1.20, 0], 0.70)
    parts += [part("sph", [0, 1.20, 0], [0.62, 0.62, 0.62], "#e8fbff", m="neon", a=0.18)]
    return parts


@XM26.hat("glacier_helm", "Glacier Helm",
          "A helmet carved out of one piece of blue glacier ice, snow still on top, "
          "crystals growing out of the crown and icicles round the rim. It does not "
          "melt. Your head, however, is cold.", "legendary")
def _():
    parts = [
        dome(-0.56, 1.06, GLACIER, t="capcrown", m="glass", a=0.82, decal="xm_glacier",
             wrap=True),
        ringband(-0.50, 0.10, FROST, margin=0.10, m="metal"),
        place("hemi", [0, 0.34, 0], [1.20, 0.46, 1.14], "#ffffff", anchor=[0, 0, 0], decal="xm_polarfur",
              wrap=True),
    ]
    for x, z, h, w, t in ((0, 0.10, 0.80, 0.30, (0.15, 0.0)), (0.34, -0.10, 0.56, 0.24, (0.0, 0.3)),
                          (-0.34, -0.10, 0.56, 0.24, (0.0, -0.3)), (0.18, -0.36, 0.40, 0.20, (-0.2, 0.2)),
                          (-0.18, -0.36, 0.40, 0.20, (-0.2, -0.2))):
        parts.append(_crystal([x, 0.40, z], h, w, ICE, t))
    parts += around(12, 1.06, 0.0, lambda a, x, z: None if math.cos(a) > 0.6 else place(
        "icicle", [x, -0.55, z * 0.97], [0.14, 0.24 + 0.10 * ((int(a * 3)) % 2), 0.14], ICE,
        anchor=[0, 1.0, 0], m="glass"))
    return parts


@XM26.back("ice_wings", "Wings of Ice",
           "Two wings of clear blue ice, every feather a shard, the northern lights "
           "showing faintly through them. They do not work. They do not need to.",
           "legendary")
def _():
    parts = [part("rbox", [0, 0.56, -0.10], [0.40, 0.40, 0.14], FROST, m="metal"),
             *_north_star([0, 0.56, -0.20], 0.40)]
    for s in (1, -1):
        yaw = 0.45 if s > 0 else PI - 0.45
        at = [0.16 * s, 0.62, -0.26]
        parts += [place("wing", at, [2.50, 2.30, 1.4], ICE, anchor=[-0.5, 0.0, 0],
                        r=[0, yaw, 0.32], m="glass", a=0.72),
                  place("wing", [at[0], at[1], at[2] - 0.02], [2.10, 1.90, 0.8], AURORA_G,
                        anchor=[-0.5, 0.0, 0], r=[0, yaw, 0.32], m="neon", a=0.35)]
    return parts


@XM26.back("aurora_cape", "Aurora Cape",
           "A cape of polar night with the lights rippling across it, stars and all, "
           "and a roll of white fur at the shoulders. Wear it outside after dark and "
           "watch people look up.", "rare")
def _():
    return [
        place("cape", [0, 0.98, -0.14], [1.90, 2.00, 1.50], POLAR_NIGHT, anchor=[0, 0, 0],
              decal="xm_aurora_cape", wrap=True),
        part("capsule", [0, 0.98, -0.10], [0.22, 1.90, 0.22], POLAR_FUR, [0, 0, PI / 2],
             decal="xm_polarfur", wrap=True),
        *_north_star([0.0, 1.00, -0.22], 0.30),
    ]


@XM26.hairdo("aurora_ombre", "Aurora Ombre",
             "Long hair dyed the colours of the lights: midnight at the roots, then "
             "green, then violet at the ends. Hairdressers all over Blockhaven have "
             "been trying to copy it.", "rare")
def _():
    return [
        place("hairlong", [0, 0, 0], [1.04, 1.04, 1.04], "#1c2a5a", anchor=[0, 0, 0],
              decal="xm_aurora_hair", wrap=True),
        part("capsule", [0.42, -0.36, -0.40], [0.16, 0.46, 0.16], AURORA_P, [0.2, 0, 0.1], m="neon",
             a=0.5),
        part("capsule", [-0.42, -0.36, -0.40], [0.16, 0.46, 0.16], AURORA_G, [0.2, 0, -0.1], m="neon",
             a=0.5),
    ]


@XM26.hairdo("snowdrift_bun", "Snowdrift Bun",
             "Silver-white hair swept up into a bun like a snowdrift, a frost-silver "
             "snowflake pinned through it.", "uncommon")
def _():
    silver = "#e8eef6"
    return [
        place("hairmid", [0, 0, 0], [1.03, 1.03, 1.03], silver, anchor=[0, 0, 0], decal="strands",
              wrap=True),
        part("sph", [0, 0.66, -0.12], [0.50, 0.40, 0.48], silver, decal="strands", wrap=True),
        part("torus", [0, 0.56, -0.12], [0.40, 0.08, 0.38], shade(silver, 0.9)),
        place("snowflake", [0.24, 0.70, 0.02], [0.30, 0.30, 1.0], FROST, r=[0, 0.6, 0], m="metal"),
        part("sph", [0.24, 0.70, 0.02], [0.06, 0.06, 0.06], "#bfe8ff", m="neon"),
    ]


XM26.face("frostbitten", "Frostbitten",
          "Blue lips, chattering teeth, frost on the lashes and a nose that went numb "
          "an hour ago. Worth it, though. Did you see them?", [
              {"k": "arc", "x": -0.20, "y": -0.12, "r": 0.06, "a0": 0.55, "a1": 0.95, "w": 0.035,
               "c": "#16171b"},
              {"k": "arc", "x": 0.20, "y": -0.12, "r": 0.06, "a0": 0.55, "a1": 0.95, "w": 0.035,
               "c": "#16171b"},
              {"k": "star", "x": -0.27, "y": -0.20, "r": 0.03, "n": 6, "i": 0.35, "c": "#ffffff"},
              {"k": "star", "x": 0.27, "y": -0.20, "r": 0.03, "n": 6, "i": 0.35, "c": "#ffffff"},
              {"k": "ellipse", "x": -0.32, "y": 0.04, "w": 0.14, "h": 0.08, "c": "#9cc8ff"},
              {"k": "ellipse", "x": 0.32, "y": 0.04, "w": 0.14, "h": 0.08, "c": "#9cc8ff"},
              {"k": "poly", "pts": [[-0.18, 0.10], [0.18, 0.10], [0.16, 0.20], [-0.16, 0.20]],
               "c": "#2a4a8a"},
              {"k": "poly", "pts": [[-0.16, 0.11], [0.16, 0.11], [0.15, 0.15], [-0.15, 0.15]],
               "c": "#ffffff"},
              {"k": "line", "x1": -0.12, "y1": 0.11, "x2": -0.12, "y2": 0.15, "w": 0.015,
               "c": "#8aa0c0"},
              {"k": "line", "x1": 0.0, "y1": 0.11, "x2": 0.0, "y2": 0.15, "w": 0.015,
               "c": "#8aa0c0"},
              {"k": "line", "x1": 0.12, "y1": 0.11, "x2": 0.12, "y2": 0.15, "w": 0.015,
               "c": "#8aa0c0"},
          ], "uncommon")
XM26.face("starry_eyed", "Starry-Eyed",
          "Eyes full of the night sky -- a star in each, the lights reflected under "
          "them -- and a mouth that has forgotten to close.", [
              {"k": "ellipse", "x": -0.19, "y": -0.12, "w": 0.18, "h": 0.20, "c": "#0c1430"},
              {"k": "ellipse", "x": 0.19, "y": -0.12, "w": 0.18, "h": 0.20, "c": "#0c1430"},
              {"k": "star", "x": -0.19, "y": -0.13, "r": 0.06, "n": 4, "i": 0.35, "c": "#e8fbff"},
              {"k": "star", "x": 0.19, "y": -0.13, "r": 0.06, "n": 4, "i": 0.35, "c": "#e8fbff"},
              {"k": "arc", "x": -0.19, "y": -0.10, "r": 0.06, "a0": 0.10, "a1": 0.40, "w": 0.02,
               "c": "#3dffb0"},
              {"k": "arc", "x": 0.19, "y": -0.10, "r": 0.06, "a0": 0.10, "a1": 0.40, "w": 0.02,
               "c": "#a45aff"},
              {"k": "ellipse", "x": 0.0, "y": 0.14, "w": 0.10, "h": 0.12, "c": "#16171b"},
          ], "rare")
XM26.shirt("expedition_parka", "Expedition Parka",
           "A bright orange polar parka, fur round the hood, patches on the arm and "
           "POLAR EXPEDITION 2026 across the chest, for standing out against the snow.",
           {"torso": PARKA, "arms": PARKA, "decal": "xm_tee_parka", "weave": "xm_ripstop",
            "hood": POLAR_FUR}, "rare")
XM26.pants("mukluk_breeches", "Mukluk Breeches",
           "Quilted navy breeches tucked into sealskin mukluks with white fur round "
           "the top. Nothing below the knee has been cold since.",
           {"legs": "#1f2a4a", "weave": "xm_quilted", "length": 0.62, "skin": "#8a6a4a",
            "cuff": POLAR_FUR})
XM26.belt("aurora_sash", "Aurora Sash",
          "A sash woven in the colours of the lights, green into violet, fastened "
          "with a star.",
          {"band": "#1f8a7a", "buckle": FROST, "width": 0.22, "glow": True, "weave": "xm_aurora"})


@XM26.weapon("narwhal_lance", "Narwhal Lance",
             "A narwhal's tusk on a frost-silver haft. Lunge with it and it carries you "
             "forward into whoever is in front of you -- and it hits half as hard again "
             "if you come down on them from a jump.",
             {"kind": "melee", "damage": 42, "headshot": 1.0, "rpm": 60, "range": 13.0,
              "arc": 0.30, "sound": "swing", "knockback": 18,
              "lunge": {"speed": 34}, "self_airborne": 1.5,
              "on_hit": {"slow": [0.30, 2.0]}},
             [["+", "Long reach, and every thrust carries you forward with it"],
              ["+", "Half as hard again when you strike in mid-air"],
              ["+", "Chills: slowed by 30% for 2 seconds"],
              ["-", "One thrust a second, and a narrow point"]], rarity="legendary")
def _():
    ivory = "#ece4d0"
    return [
        rod([0, 0, -0.50], [0, 0, 0.30], 0.12, FROST, m="metal"),
        part("cyl", [0, 0, 0.32], [0.30, 0.10, 0.30], FROST, [PI / 2, 0, 0], m="metal"),
        part("sph", [0, 0, -0.52], [0.16, 0.16, 0.16], GLACIER, m="glass"),
        place("spiral", [0, 0, 0.36], [0.24, 2.10, 0.24], ivory, anchor=[0, 0, 0],
              r=[PI / 2, 0, 0]),
        place("cone", [0, 0, 1.30], [0.22, 1.90, 0.22], ivory, r=[PI / 2, 0, 0],
              decal="xm_narwhal", wrap=True),
    ]


@XM26.weapon("aurora_arc", "Aurora Arc",
             "A frost-silver wand with the lights in it. Every shot leaps from whoever "
             "it hits to the next nearest enemy, the way the aurora runs along the sky.",
             {"kind": "hitscan", "damage": 22, "headshot": 1.5, "rpm": 150, "mag": 10,
              "reload": 2.0, "range": 160, "auto": True, "sound": "laser", "recoil": 0.6,
              "spread": 0.5, "reserve": 80, "tracer": "#3dffb0",
              "ricochet": {"range": 18, "falloff": 0.75, "always": True},
              "on_hit": {"slow": [0.12, 1.0]}},
             [["+", "Every hit leaps on to the nearest other enemy within 18 studs for 75%"],
              ["+", "A light chill: slowed a little for a second"],
              ["-", "22 damage"],
              ["-", "Ten to a charge"]], rarity="legendary")
def _():
    return [
        part("rbox", [0, -0.10, -0.02], [0.14, 0.34, 0.20], POLAR_NIGHT, [-0.2, 0, 0],
             decal="felt"),
        rod([0, -0.02, -0.10], [0, 0.04, 0.80], 0.10, FROST, m="metal"),
        part("torus", [0, 0.04, 0.40], [0.18, 0.04, 0.18], GLACIER, [PI / 2, 0, 0], m="metal"),
        part("cyl", [0, 0.05, 0.84], [0.26, 0.20, 0.26], AURORA_G, [PI / 2, 0, 0], m="neon",
             a=0.6, decal="xm_aurora", wrap=True),
        _crystal([0, 0.05, 0.92], 0.44, 0.22, ICE, (PI / 2, 0.0)),
        part("sph", [0, 0.05, 1.04], [0.16, 0.16, 0.16], AURORA_P, m="neon", a=0.7),
    ]


@XM26.weapon("supply_drop", "Supply Drop",
             "A crate of expedition stores on a little parachute. Throw it for your team: "
             "whoever reaches it first gets ammunition, a padded layer and a spring in "
             "their step.",
             {"kind": "deploy", "cooldown": 20, "sound": "throw",
              "deploy": {"type": "pickup", "thrown": True, "throw": 22, "radius": 3.0,
                         "secs": 25.0, "limit": 2, "scale": 1.2, "ammo": 40,
                         "shield": [30, 8.0], "haste": [0.20, 5.0], "name": "Supply Drop",
                         "color": PARKA}},
             [["+", "A teammate who picks it up gets 40 rounds, a 30-point shield for 8 "
                    "seconds and 20% more speed for 5"],
              ["+", "Two can be waiting at once"],
              ["-", "No damage: it is for your friends"],
              ["-", "20 second cooldown, and anyone can see it fall"]], rarity="rare",
             deploy=lambda: [
                 part("rbox", [0, 0.30, 0], [0.80, 0.60, 0.70], "#6a4a2e", decal="planks",
                      wrap=True),
                 part("rbox", [0, 0.30, 0], [0.82, 0.10, 0.72], PARKA),
                 part("rbox", [0, 0.30, 0.36], [0.30, 0.30, 0.01], "#ffffff", decal="xm_supply"),
                 place("hemi", [0, 1.50, 0], [1.40, 0.80, 1.40], PARKA, anchor=[0, 0, 0],
                       decal="xm_parachute", wrap=True),
                 rod([0.38, 0.62, 0.32], [0.60, 1.50, 0.56], 0.02, "#f4f6f8"),
                 rod([-0.38, 0.62, 0.32], [-0.60, 1.50, 0.56], 0.02, "#f4f6f8"),
                 rod([0.38, 0.62, -0.32], [0.60, 1.50, -0.56], 0.02, "#f4f6f8"),
                 rod([-0.38, 0.62, -0.32], [-0.60, 1.50, -0.56], 0.02, "#f4f6f8"),
             ])
def _():
    return [
        part("rbox", [0, 0.06, 0.20], [0.46, 0.36, 0.40], "#6a4a2e", decal="planks", wrap=True),
        part("rbox", [0, 0.06, 0.20], [0.48, 0.06, 0.42], PARKA),
        part("rbox", [0, 0.06, 0.41], [0.18, 0.18, 0.01], "#ffffff", decal="xm_supply"),
        part("torus", [0, 0.28, 0.20], [0.20, 0.04, 0.12], "#2a2a30", [PI / 2, 0, 0]),
    ]


@XM26.gear("north_compass", "North Star Compass",
           "A frost-silver compass whose needle points at the north star -- and, if "
           "you tap the glass, at everyone hiding from you. Your team sets off "
           "after them at a run.",
           {"kind": "ability", "cooldown": 22, "sound": "chime",
            "ability": {"radar": {"radius": 120, "secs": 6.0, "color": "#3dffb0"},
                        "rally": {"radius": 24, "secs": 5.0, "speed": 0.20}}},
           [["+", "Shows every enemy within 120 studs to your whole team for 6 seconds"],
            ["+", "Teammates within 24 studs get 20% more speed for 5 seconds"],
            ["-", "22 second cooldown"],
            ["-", "No damage at all"]], rarity="rare")
def _():
    return [
        part("cyl", [0, 0.26, 0.12], [0.46, 0.10, 0.46], FROST, [PI / 2, 0, 0], m="metal"),
        part("disc", [0, 0.26, 0.175], [0.38, 0.38, 0.02], POLAR_NIGHT, decal="xm_compass"),
        part("cyl", [0, 0.26, 0.19], [0.38, 0.01, 0.38], "#e8fbff", [PI / 2, 0, 0], m="glass",
             a=0.3),
        part("cyl", [0, 0.52, 0.12], [0.08, 0.08, 0.08], FROST, m="metal"),
        part("torus", [0, 0.60, 0.12], [0.14, 0.03, 0.14], FROST, [PI / 2, 0, 0], m="metal"),
    ]


XM26.effect("aurora_veil", name="Aurora Veil", rate=1.6, life=[2.4, 3.2],
            size=[0.60, 0.90], grow=0.4, gravity=-0.2, spread=0.4, rise=[0.2, 0.4],
            blend="add", spin=0.2, colors=["#3dffb0", "#a45aff", "#5ab8ff"],
            shape="aurora", radius=0.7, wobble=0.6)
XM26.effect("diamond_dust", name="Diamond Dust", rate=4.0, life=[1.2, 1.8],
            size=[0.12, 0.22], grow=0.0, gravity=0.3, spread=0.8, rise=[0.1, 0.3],
            blend="add", spin=2.5, colors=["#ffffff", "#bfe8ff", "#e8fbff"],
            shape="crystal", radius=0.9)
XM26.opening(
    sky={"top": "#040818", "horizon": "#14305a", "sun": [0.0, 0.8, 0.6], "clouds": 0.1,
         "tint": "#d8f8ff"},
    ambient="#3a4a7a", beam="#3dffb0", seep="aurora_veil", after="diamond_dust",
    burst=["#3dffb0", "#a45aff", "#e8fbff", "#5ab8ff"],
    pieces=[{"shape": "aurora", "colors": ["#3dffb0", "#a45aff"], "blend": "add"},
            {"shape": "crystal", "colors": ["#e8fbff", "#bfe8ff"], "blend": "add"},
            {"shape": "flake", "colors": ["#ffffff", "#dff4ff"], "blend": "normal"},
            {"shape": "star", "colors": ["#ffffff", "#fff3b0"], "blend": "add"}],
    backdrop="xm_aurora", title_wait="The sky is starting to glow...",
    title_shake="Look up...")
XM26.award("Aurora Winterlight", ["Stargazer", "Night Watcher", "Ice Walker", "Light Catcher",
                                  "Polar Explorer", "Keeper of the Lights"],
           "Opened Glacier Chests under the Aurora Winterlight, Christmas 2026.", "em_aurora",
           "flake")
XM26.bundle("pair", "Chest and Star", 1, 1050, "One Glacier Chest, one Polaris Key.")
XM26.bundle("expedition", "The Expedition", 3, 3000, "Three chests, three keys. Saves 300.")

EVENTS = [XM22, XM23, XM24, XM25, XM26]
