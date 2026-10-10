"""New Year: Blockhaven's own birthday, and every midnight since.

The platform opened on the first of January 2022 with a countdown crate, and
every New Year's Eve has brought the next one:

  2022  First Light          the launch: clocks, streamers, the first midnight
  2023  Glitterfall Gala     black tie, champagne, sequins and a masquerade
  2024  Rocket Rally         fireworks, fuses and a great deal of smoke
  2025  Neon Midnight        synthwave: neon grids, disco and cassettes
  2026  Crystal Countdown    the ball drop: crystal, silver and starlight
"""
from __future__ import annotations

import math

from .kit import (BLACK, BRASS, GOLD, GOLD_DARK, IRON, PI, SILVER, SNOW, TAU, WHITE,
                  Event, around, at_frame, band, buckle, cap, dome, gift_bow, mix, part,
                  place, pompom, ringband, rotate, shade, sides, straps)

NAVY = "#0b1433"
MIDNIGHT = "#141d45"


# ============================================================ 2022
NY22 = Event(
    "newyear_2022", "newyear", 2022, "ny22",
    name="First Light", title="First Light",
    blurb="Blockhaven's very first midnight. The servers came up at 23:59 on New "
          "Year's Eve 2021, the clock ran down, and the first crate ever opened "
          "at 00:00:01. Everything in it is from that night.",
    tagline="The very first crate. It has been counting down ever since.",
    starts="2022-01-01", ends="2022-01-15",
    colors={"accent": "#f2c230", "deep": "#0b1433", "glow": "#fff3b0"},
    family_effects=["starstruck", "sunbeam", "static_charge"],
    hero_effect="midnight_chimes", stencil="stencil_ny22")


def _clock_face(at, r, k=1.0, hands=(11.9, 0.0), rim=GOLD, face=SNOW, tilt=0.0):
    """A clock face standing up facing +Z: a dial, a rim, two hands."""
    x, y, z = at
    out = [
        part("disc", [x, y, z], [r * 2, r * 2, 0.10 * k], face, [tilt, 0, 0],
             decal="clockface"),
        part("torus", [x, y, z + 0.02 * k], [r * 2.08, 0.07 * k, r * 2.08], rim,
             [PI / 2 + tilt, 0, 0], m="metal"),
    ]
    for hour, length, width in ((hands[0], 0.62, 0.07), (hands[1], 0.86, 0.05)):
        a = hour / 12.0 * TAU
        hx, hy = math.sin(a) * r * length * 0.5, math.cos(a) * r * length * 0.5
        out.append(place("arrow", [x + hx, y + hy, z + 0.07 * k],
                         [width * 6 * k * r, r * length, 0.4 * k], BLACK,
                         r=[tilt, 0, -a]))
    out.append(part("sph", [x, y, z + 0.08 * k], [0.08 * k * r * 2, 0.08 * k * r * 2,
                                                   0.05 * k], rim, m="metal"))
    return out


@NY22.crate_model("Countdown Crate",
                  "Midnight-blue boards, gold corners and a clock that stopped at one "
                  "second to twelve on the night Blockhaven opened. Holds the First "
                  "Light set. Needs a Midnight Key.",
                  hinge=[0, 0.50, -0.56], keyhole=[0, -0.19, 0.61])
def _():
    wood, deep, gold = "#1d2a6b", "#121a4a", GOLD
    parts = [
        part("rbox", [0, 0.0, 0], [1.66, 1.00, 1.12], wood, decal="planks", wrap=True),
        part("rbox", [0, 0.64, 0], [1.72, 0.28, 1.18], deep, decal="planks", wrap=True, lid=1),
        # gold bands round the body and the lid
        part("rbox", [0, -0.40, 0], [1.70, 0.08, 1.16], gold, m="metal"),
        part("rbox", [0, 0.40, 0], [1.70, 0.08, 1.16], gold, m="metal"),
        part("rbox", [0, 0.64, 0], [1.76, 0.06, 1.22], gold, m="metal", lid=1),
        # the stencil on the back and the sides
        part("box", [0, 0.0, -0.572], [1.0, 0.70, 0.02], "#000000", [0, PI, 0],
             decal="stencil_ny22", a=-1),
        part("box", [0.842, 0.0, 0], [0.02, 0.62, 0.80], "#000000", [0, PI / 2, 0],
             decal="stencil_ny22", a=-1),
        part("box", [-0.842, 0.0, 0], [0.02, 0.62, 0.80], "#000000", [0, -PI / 2, 0],
             decal="stencil_ny22", a=-1),
        # the lock: a brass plate under the clock
        part("rbox", [0, -0.19, 0.575], [0.34, 0.36, 0.06], BRASS, decal="keyhole",
             m="metal", lock=1),
        part("rbox", [0, 0.48, 0.60], [0.18, 0.26, 0.06], gold, m="metal", lid=1),
        # the light waiting in the seam
        part("box", [0, 0.48, 0], [1.52, 0.04, 0.98], "#fff3b0", m="neon"),
    ]
    parts += _clock_face([0, 0.18, 0.585], 0.25, 0.6, hands=(11.95, 11.98))
    # streamers coiled on the lid, and confetti stuck to it
    parts += [place("spiral", [-0.42, 0.79, 0.12], [0.30, 0.22, 0.30], "#ff4fa0",
                    r=[PI / 2, 0.3, 0], lid=1),
              place("spiral", [0.38, 0.79, -0.18], [0.28, 0.20, 0.28], "#3cc8ff",
                    r=[PI / 2, -0.6, 0], lid=1)]
    for k, (x, z, c) in enumerate(((0.1, 0.3, "#ff4fa0"), (-0.2, -0.3, "#3cc8ff"),
                                   (0.55, 0.25, "#f2c230"), (-0.6, -0.1, "#7dff9a"),
                                   (0.25, -0.35, "#f2c230"))):
        parts.append(part("box", [x, 0.785, z], [0.07, 0.01, 0.045], c, [0, k * 0.9, 0], lid=1))
    # gold corner caps
    for x in (-0.80, 0.80):
        for zz in (-0.54, 0.54):
            for yy, lid in ((-0.46, 0), (0.74, 1)):
                parts.append(part("rbox", [x, yy, zz], [0.15, 0.15, 0.15], gold,
                                  m="metal", lid=lid or None))
    return parts


@NY22.key_model("Midnight Key",
                "A gold key whose bow is a pocket watch that stopped at midnight. Opens "
                "one Countdown Crate, then winds down for good.", shoulder=-0.28)
def _():
    return [
        part("disc", [-0.62, 0, 0], [0.62, 0.62, 0.14], SNOW, [0, 0, 0], decal="clockface"),
        part("torus", [-0.62, 0, 0], [0.66, 0.10, 0.66], GOLD, [PI / 2, 0, 0], m="metal"),
        part("cyl", [-0.62, 0.35, 0], [0.09, 0.10, 0.09], GOLD, m="metal"),
        part("torus", [-0.62, 0.44, 0], [0.16, 0.05, 0.16], GOLD_DARK, [0, 0, PI / 2], m="metal"),
        place("arrow", [-0.62, 0.08, 0.08], [0.10, 0.20, 0.3], BLACK),
        place("arrow", [-0.66, 0.02, 0.08], [0.08, 0.15, 0.3], BLACK, r=[0, 0, 0.8]),
        part("cyl", [0.12, 0, 0], [0.10, 1.10, 0.10], GOLD, [0, 0, PI / 2], m="metal"),
        part("torus", [-0.26, 0, 0], [0.20, 0.08, 0.20], GOLD_DARK, [0, 0, PI / 2], m="metal"),
        # the bit: two clock hands
        place("arrow", [0.52, -0.13, 0], [0.12, 0.24, 0.5], GOLD, r=[0, 0, PI], m="metal"),
        place("arrow", [0.36, -0.10, 0], [0.10, 0.17, 0.5], GOLD, r=[0, 0, PI], m="metal"),
        part("sph", [0.66, 0, 0], [0.12, 0.12, 0.12], GOLD, m="metal"),
    ]


@NY22.hat("midnight_topper", "Midnight Top Hat",
          "Black silk, a gold band, and a clock set into the crown that has read 11:59 "
          "since the first night. Nobody has ever seen it tick over.", "legendary")
def _():
    parts = [
        place("brim", [0, -0.05, 0], [2.20, 1.6, 2.10], BLACK, anchor=[0, 0, 0]),
        place("flare", [0, 0.0, 0], [1.40, 1.55, 1.34], "#1a1c25", anchor=[0, 0, 0],
              decal="felt", wrap=True),
        part("cyl", [0, 0.18, 0], [1.29, 0.28, 1.23], GOLD, m="metal"),
        part("cyl", [0, 0.18, 0], [1.31, 0.06, 1.25], GOLD_DARK, m="metal"),
        # a streamer tucked into the band, curling off down the side
        place("spiral", [0.66, 0.02, 0.10], [0.20, 0.70, 0.20], "#ff4fa0", anchor=[0, 0.5, 0],
              r=[0.15, 0, 0.12]),
        place("spiral", [0.62, 0.06, -0.18], [0.16, 0.52, 0.16], "#3cc8ff", anchor=[0, 0.5, 0],
              r=[-0.15, 0, 0.20]),
        # a tiny gold star where the twelve should be
        place("star", [0, 1.42, 0.0], 0.24, "#fff3b0", m="neon"),
        part("cyl", [0, 1.32, 0.0], [0.03, 0.18, 0.03], GOLD, m="metal"),
    ]
    parts += _clock_face([0, 0.75, 0.70], 0.30, 0.7, hands=(11.95, 11.98), tilt=-0.03)
    return parts


@NY22.hat("countdown_cone", "Countdown Party Hat",
          "Midnight-blue foil, gold stars, a tinsel pompom and a streamer still "
          "uncurling from the tip. Elastic not included, or needed.", "rare")
def _():
    return [
        part("cone", [0, 0.86, 0], [1.50, 1.80, 1.50], "#1d2a6b", decal="party", wrap=True),
        ringband(-0.02, 0.18, GOLD, m="metal"),
        pompom([0, 1.82, 0], 0.46, GOLD),
        part("sph", [0, 1.82, 0], [0.30, 0.28, 0.30], "#fff3b0", m="neon", a=0.5),
        place("spiral", [0.10, 1.95, 0.0], [0.42, 0.70, 0.42], "#ff4fa0", r=[0.5, 0, -0.6]),
        place("spiral", [-0.10, 1.95, 0.05], [0.34, 0.60, 0.34], "#3cc8ff", r=[-0.4, 0, 0.7]),
        place("star", [0.30, 0.70, 0.66], 0.26, GOLD, r=[-0.45, 0.42, 0], m="metal"),
        place("star", [-0.34, 1.05, 0.48], 0.20, "#fff3b0", r=[-0.45, -0.55, 0], m="metal"),
    ]


@NY22.hat("first_crown", "Noisemaker Crown",
          "A gold-foil party crown with a star on every point, handed out at the door "
          "on opening night. It crinkles when you nod.", "uncommon")
def _():
    parts = [
        place("spikecrown", [0, -0.30, 0], [1.86, 0.62, 1.80], GOLD, anchor=[0, 0, 0],
              m="metal"),
        ringband(-0.22, 0.12, "#1d2a6b"),
    ]
    parts += around(7, 0.92, 0.0, lambda a, x, z: place(
        "star", [x * 0.985, 0.33, z * 0.965], 0.17, "#fff3b0", r=[0, a, 0], m="neon"),
        start=TAU / 14)
    parts += around(14, 0.93, 0.0, lambda a, x, z: part(
        "sph", [x, -0.22, z * 0.97], [0.07, 0.07, 0.07],
        ["#ff4fa0", "#3cc8ff", "#7dff9a"][int(round(a / (TAU / 14))) % 3], m="glass"))
    return parts


@NY22.hat("popper_topper", "Popper Topper",
          "A party popper the size of a traffic cone, perched on a cap and frozen at "
          "the exact moment it went off. The streamers never came down.", "rare")
def _():
    colours = ["#ff4fa0", "#3cc8ff", "#f2c230", "#7dff9a", "#b26bff"]
    tilt = [0.0, 0.0, -0.35]
    parts = [
        cap(-0.28, 0.14, "#1d2a6b", decal="felt", wrap=True),
        band(-0.22, 0.12, "#f2c230", grow=0.05, m="metal"),
        # the popper: a cone stood on its point, its mouth open to the sky
        place("cone", [0.0, 0.12, 0.0], [0.70, 1.10, 0.70], "#e8e4f0", anchor=[0, 0.5, 0],
              r=[PI, 0, -0.35], decal="party", wrap=True),
    ]
    up = rotate([0, 1.08, 0], tilt)
    mouth = [up[0], 0.12 + up[1], up[2]]
    parts += [part("torus", mouth, [0.72, 0.06, 0.72], "#f2c230", tilt, m="metal"),
              part("cyl", [0, 0.10, 0], [0.16, 0.10, 0.16], "#c4281c", tilt)]
    for k in range(7):
        a = k * TAU / 7
        lean = [math.cos(a) * 0.55, 0, -0.35 - math.sin(a) * 0.55]
        parts.append(place("spiral", [mouth[0] + math.sin(a) * 0.14, mouth[1],
                                      mouth[2] + math.cos(a) * 0.14],
                           [0.20, 0.75 + (k % 3) * 0.18, 0.20], colours[k % 5],
                           anchor=[0, -0.5, 0], r=lean))
    for k in range(9):
        a = k * 2.3
        parts.append(part("box", [mouth[0] + math.sin(a) * 0.55, mouth[1] + 0.5 + (k % 4) * 0.16,
                                  mouth[2] + math.cos(a) * 0.55],
                          [0.12, 0.02, 0.08], colours[k % 5], [k * 0.7, k, k * 0.4]))
    return parts


@NY22.hat("alarm_clock", "Time's Up",
          "A twin-bell alarm clock that rings at midnight -- every midnight, wherever "
          "you are, whoever is trying to sleep.", "legendary")
def _():
    body = "#c4281c"
    parts = [
        part("cyl", [0, 0.62, 0], [1.20, 0.44, 1.20], body, [PI / 2, 0, 0], m="metal"),
        part("torus", [0, 0.62, 0.22], [1.24, 0.10, 1.24], SILVER, [PI / 2, 0, 0], m="metal"),
        part("torus", [0, 0.62, -0.22], [1.24, 0.10, 1.24], SILVER, [PI / 2, 0, 0], m="metal"),
        part("disc", [0, 0.62, 0.225], [1.0, 1.0, 0.04], "#fffdf2", decal="clockface"),
        part("cyl", [0, 0.62, 0.235], [1.02, 0.03, 1.02], "#e8f6ff", [PI / 2, 0, 0],
             m="glass", a=0.25),
    ]
    for hour, length in ((11.95, 0.30), (0.0, 0.42)):
        a = hour / 12 * TAU
        parts.append(place("arrow", [math.sin(a) * length * 0.5, 0.62 + math.cos(a) * length * 0.5,
                                     0.27], [0.08, length, 0.4], BLACK, r=[0, 0, -a]))
    for side in (1, -1):
        parts += [
            place("bell", [0.44 * side, 1.08, 0], [0.42, 0.34, 0.42], SILVER, anchor=[0, 0, 0],
                  r=[0, 0, -0.5 * side], m="metal"),
            part("sph", [0.40 * side, 1.12, 0], [0.08, 0.08, 0.08], GOLD, m="metal"),
            # legs
            part("cyl", [0.42 * side, 0.20, 0.0], [0.08, 0.30, 0.08], SILVER,
                 [0, 0, 0.35 * side], m="metal"),
            part("sph", [0.48 * side, 0.06, 0.0], [0.14, 0.10, 0.14], SILVER, m="metal"),
        ]
    parts += [
        place("arch", [0, 1.06, 0], [0.56, 0.32, 0.6], SILVER, anchor=[0, 0, 0], m="metal"),
        part("cyl", [0, 1.12, 0], [0.04, 0.16, 0.04], SILVER, m="metal"),
        part("sph", [0, 1.22, 0], [0.12, 0.08, 0.12], SILVER, m="metal"),
        # it sits on a little cushion so it does not slide off
        cap(-0.26, 0.14, "#1d2a6b", decal="felt", wrap=True),
        band(-0.22, 0.12, GOLD, grow=0.05, m="metal"),
    ]
    return parts


@NY22.hat("dawn_visor", "New Dawn Visor",
          "A sun visor with the first sunrise of 2022 printed on it. It is always "
          "slightly brighter than everything around it.", "uncommon")
def _():
    return [
        band(-0.20, 0.20, "#f6f1e6", grow=0.04),
        place("visor", [0, -0.14, 0], [1.94, 2.0, 1.94], "#ffb347", anchor=[0, 0, 0]),
        place("visor", [0, -0.17, 0], [1.92, 1.9, 1.92], "#2b2f4a", anchor=[0, 0, 0]),
        part("rbox", [0, -0.06, 0.82], [1.20, 0.30, 0.05], "#000000", [-0.08, 0, 0],
             decal="sunrise", a=-1),
        part("rbox", [0, -0.20, -0.80], [0.30, 0.10, 0.06], GOLD, m="metal"),
    ]


@NY22.hat("streamer_tangle", "Streamer Tangle",
          "Somebody pulled every streamer off the ceiling at 00:01 and it all ended "
          "up here. There is a noisemaker in there somewhere.", "uncommon")
def _():
    colours = ["#ff4fa0", "#3cc8ff", "#f2c230", "#7dff9a", "#b26bff", "#ff8c1a"]
    parts = [cap(-0.28, 0.08, "#2b2f4a", decal="felt", wrap=True)]
    for k in range(11):
        a = k * TAU / 11
        x, z = math.sin(a) * 0.55, math.cos(a) * 0.55
        parts.append(place("spiral", [x, 0.0, z], [0.36, 0.50 + (k % 3) * 0.12, 0.36],
                           colours[k % 6], anchor=[0, -0.5, 0],
                           r=[math.cos(a) * 0.9, 0, -math.sin(a) * 0.9]))
    parts += [
        place("spiral", [0, 0.12, 0], [0.70, 0.60, 0.70], "#f2c230"),
        place("trumpet", [0.30, 0.24, 0.10], [0.34, 1.0, 0.34], "#3cc8ff", anchor=[0, 0, 0],
              r=[0, 0, -1.05], decal="party", wrap=True),
    ]
    return parts


@NY22.back("grandfather_pack", "Grandfather Clock Pack",
           "A grandfather clock on shoulder straps, pendulum swinging, chiming the "
           "hour whether or not anybody asked.", "legendary")
def _():
    wood, dark = "#5a3016", "#3a1d0c"
    return [
        part("rbox", [0, 0.10, -0.40], [0.86, 1.90, 0.56], wood, decal="planks", wrap=True),
        part("rbox", [0, 1.10, -0.40], [0.98, 0.20, 0.64], dark),
        place("arch", [0, 1.18, -0.40], [0.80, 0.50, 3.6], dark, anchor=[0, 0, 0]),
        part("disc", [0, 0.70, -0.70], [0.62, 0.62, 0.08], SNOW, [0, PI, 0], decal="clockface"),
        part("torus", [0, 0.70, -0.71], [0.66, 0.06, 0.66], GOLD, [PI / 2, 0, 0], m="metal"),
        # the glass door and the pendulum behind it
        part("rbox", [0, -0.20, -0.69], [0.56, 0.96, 0.04], "#cfe8ff", m="glass", a=0.35),
        part("cyl", [0, 0.05, -0.62], [0.03, 0.70, 0.03], GOLD, m="metal"),
        part("disc", [0, -0.36, -0.62], [0.26, 0.26, 0.05], GOLD, [0, PI, 0], m="metal"),
        part("rbox", [0, -0.88, -0.40], [0.98, 0.16, 0.64], dark),
        # straps over the shoulders
        *straps("#2b2b30", 0.36, 0.14),
    ]


@NY22.back("tinsel_wings", "Tinsel Wings",
           "Two wings made out of every strand of gold tinsel left over on the first "
           "night. They shed. Constantly.", "rare")
def _():
    parts = []
    for layer, (c, k, dz) in enumerate(((GOLD, 1.0, 0.0), ("#ffe58a", 0.80, -0.05),
                                        ("#fff3b0", 0.60, -0.10))):
        for side in (1, -1):
            parts.append(place("wing", [0.16 * side, 0.55 - layer * 0.10, -0.40 + dz],
                               2.1 * k, c, anchor=[-0.5, 0.0, 0],
                               r=[0, 0.34 if side > 0 else PI - 0.34, 0.36 - layer * 0.12],
                               decal="fur", wrap=True, m="metal"))
    parts.append(part("rbox", [0, 0.50, -0.30], [0.36, 0.40, 0.18], GOLD_DARK, m="metal"))
    parts.append(place("star", [0, 0.52, -0.40], 0.36, "#fff3b0", r=[0, PI, 0], m="neon"))
    return parts


@NY22.hairdo("countdown_curls", "Countdown Curls",
             "Twelve ringlets, one for every chime, held back with a gold star clip.",
             "uncommon")
def _():
    c, hi = "#6b3a1e", shade("#6b3a1e", 1.3)
    parts = [place("hairmid", [0, 0, 0], [1.0, 1.0, 1.0], c, anchor=[0, 0, 0],
                   decal="strands", wrap=True)]
    parts.append(part("rbox", [0, 0.545, 0.05], [0.03, 0.02, 0.66], shade(c, 0.6)))
    for k in range(12):
        a = PI * 0.30 + k * PI * 1.40 / 11
        sa, ca = math.sin(a), math.cos(a)
        if ca * 0.5 > 0.30:
            continue
        # just outside the hair, which follows the square of the skull
        d = min(0.5 / max(abs(sa), abs(ca)), 0.60) + 0.09
        x, z = sa * d, ca * d
        parts.append(place("spiral", [x, -0.05, z], [0.16, 0.42, 0.16],
                           hi if k % 2 else c, anchor=[0, 0.5, 0]))
    parts.append(place("star", [0.585, 0.22, 0.16], 0.18, GOLD, r=[0, PI / 2, 0], m="metal"))
    return parts


@NY22.hairdo("midnight_slick", "Midnight Slick",
             "Swept straight back and set hard enough to survive the countdown, the "
             "confetti and the hugging.", "rare")
def _():
    c, hi = "#14161c", "#2c3240"
    parts = [place("hairshort", [0, 0, 0], [1.02, 1.02, 1.02], c, anchor=[0, 0, 0],
                   decal="strands", wrap=True)]
    for k, x in enumerate((-0.30, -0.15, 0.0, 0.15, 0.30)):
        parts.append(place("teardrop", [x, 0.50, 0.08], [0.20, 0.80, 0.16], hi if k % 2 else c,
                           anchor=[0, 0.1, 0], r=[PI / 2 + 0.25, 0, 0]))
    parts.append(part("rbox", [0, 0.53, -0.36], [0.70, 0.10, 0.20], c))
    return parts


NY22.face("midnight_grin", "Midnight Grin",
          "Stars in both eyes and a grin from one ear to the other.", [
              {"k": "star", "x": -0.22, "y": -0.16, "r": 0.10, "c": "#1a1a1a"},
              {"k": "star", "x": 0.22, "y": -0.16, "r": 0.10, "c": "#1a1a1a"},
              {"k": "star", "x": -0.22, "y": -0.17, "r": 0.04, "c": "#f2c230"},
              {"k": "star", "x": 0.22, "y": -0.17, "r": 0.04, "c": "#f2c230"},
              {"k": "arc", "x": 0, "y": 0.0, "r": 0.30, "a0": 0.06, "a1": 0.44,
               "w": 0.06, "c": "#1a1a1a"},
              {"k": "poly", "pts": [[-0.20, 0.20], [0.20, 0.20], [0.12, 0.27], [-0.12, 0.27]],
               "c": "#ffffff"},
          ], "rare")
NY22.face("blower", "Party Blower",
          "Cheeks puffed, eyes squeezed shut, the blower rolled out to its full and "
          "glorious length.", [
              {"k": "arc", "x": -0.22, "y": -0.13, "r": 0.10, "a0": 0.55, "a1": 0.95,
               "w": 0.05, "c": "#1a1a1a"},
              {"k": "arc", "x": 0.22, "y": -0.13, "r": 0.10, "a0": 0.55, "a1": 0.95,
               "w": 0.05, "c": "#1a1a1a"},
              {"k": "ellipse", "x": -0.27, "y": 0.10, "w": 0.12, "h": 0.07, "c": "#ff8fa8"},
              {"k": "ellipse", "x": 0.27, "y": 0.10, "w": 0.12, "h": 0.07, "c": "#ff8fa8"},
              {"k": "ellipse", "x": 0, "y": 0.16, "w": 0.09, "h": 0.07, "c": "#1a1a1a"},
              {"k": "line", "x1": 0.02, "y1": 0.17, "x2": 0.24, "y2": 0.21, "w": 0.06,
               "c": "#3cc8ff"},
              {"k": "line", "x1": 0.08, "y1": 0.18, "x2": 0.12, "y2": 0.19, "w": 0.06,
               "c": "#ff4fa0"},
              {"k": "line", "x1": 0.16, "y1": 0.195, "x2": 0.20, "y2": 0.20, "w": 0.06,
               "c": "#ff4fa0"},
              {"k": "ring", "x": 0.27, "y": 0.25, "r": 0.04, "w": 0.035, "c": "#3cc8ff"},
              {"k": "poly", "pts": [[0.0, 0.13], [-0.05, 0.10], [-0.05, 0.24], [0.0, 0.21]],
               "c": "#f2c230"},
          ])
NY22.shirt("countdown_sweater", "Countdown Sweater",
           "Midnight-blue knit with a gold clock on the chest. Itchy in exactly the way "
           "a party sweater should be.",
           {"torso": "#1d2a6b", "arms": "#1d2a6b", "decal": "tee_clock", "weave": "knit",
            "stripe": "#f2c230"}, "rare")
NY22.pants("starlit_slacks", "Starlit Slacks",
           "Navy trousers with a gold stripe that glows faintly after midnight.",
           {"legs": "#141d45", "stripe": "#f2c230", "glow": True, "weave": "felt"})


@NY22.weapon("midnight_mallet", "Midnight Mallet",
             "A brass clock-bell on a stick. Every hit is a chime; the twelfth strikes "
             "midnight -- a shockwave that throws everything near you off its feet.",
             {"kind": "melee", "damage": 30, "headshot": 1.2, "rpm": 84, "range": 10.0,
              "arc": 0.6, "sound": "swing", "knockback": 11,
              "counter": {"every": 12, "radius": 11.0, "damage": 80, "knock": 34,
                          "label": "Chimes", "fx": "midnight"}},
             [["+", "Every hit is a chime; the 12th strikes Midnight: 80 damage to every "
                    "enemy within 11 studs, and a shockwave that knocks them flying"],
              ["+", "Chimes are kept when you put it away"],
              ["-", "20% less damage than a Blockblade"],
              ["-", "Chimes are lost when you die"]], rarity="legendary")
def _():
    return [
        part("cyl", [0, 0, 0.70], [0.14, 1.90, 0.14], "#3a1d0c", [PI / 2, 0, 0],
             decal="leather", wrap=True),
        part("cyl", [0, 0, -0.10], [0.17, 0.36, 0.17], "#1d2a6b", [PI / 2, 0, 0]),
        part("sph", [0, 0, -0.30], [0.20, 0.20, 0.20], GOLD, m="metal"),
        place("bell", [0, 0.0, 1.55], [0.70, 0.62, 0.70], BRASS, anchor=[0, 0.51, 0],
              r=[0, 0, PI / 2], m="metal"),
        part("disc", [0.32, 0, 1.55], [0.40, 0.40, 0.06], SNOW, [0, PI / 2, 0], decal="clockface"),
        part("torus", [0, 0, 1.55], [0.74, 0.08, 0.74], GOLD_DARK, [0, 0, PI / 2], m="metal"),
        part("sph", [-0.36, 0, 1.55], [0.18, 0.18, 0.18], GOLD, m="metal"),
    ]


@NY22.weapon("confetti_cannon", "Confetti Cannon",
             "A party cannon loaded with a whole room's worth of confetti. It barely "
             "hurts. Nobody can see a thing afterwards.",
             {"kind": "hitscan", "damage": 6, "headshot": 1.2, "rpm": 66, "mag": 4,
              "reload": 2.2, "spread": 7.5, "pellets": 10, "range": 46, "auto": False,
              "sound": "shotgun", "recoil": 2.6, "reserve": 32, "falloff": 0.4,
              "knockback": 9, "tracer": "#ff4fa0",
              "on_hit": {"blind": [1.6, "confetti"]}},
             [["+", "Every pellet that lands buries the target's screen in confetti for "
                    "1.6 seconds"],
              ["+", "Knocks the target back a step"],
              ["-", "Only 6 damage a pellet"],
              ["-", "Four shots a load"]], rarity="legendary")
def _():
    return [
        part("cyl", [0, 0.04, 0.70], [0.46, 1.50, 0.46], "#1d2a6b", [PI / 2, 0, 0],
             decal="party", wrap=True),
        place("trumpet", [0, 0.04, 1.28], [0.95, 0.55, 0.95], "#e8e4f0", anchor=[0, 0, 0],
              r=[PI / 2, 0, 0], decal="party", wrap=True),
        part("torus", [0, 0.04, 0.10], [0.50, 0.08, 0.50], GOLD, [PI / 2, 0, 0], m="metal"),
        part("rbox", [0, -0.34, 0.02], [0.18, 0.46, 0.22], "#3a1d0c", [0.3, 0, 0]),
        part("rbox", [0, -0.20, -0.36], [0.20, 0.26, 0.62], "#2b2f4a"),
        part("box", [0.0, 0.33, 0.6], [0.06, 0.12, 0.30], GOLD, m="metal"),
        place("spiral", [0.0, 0.10, 1.60], [0.24, 0.40, 0.24], "#ff4fa0", r=[PI / 2, 0, 0]),
    ]


@NY22.weapon("countdown_crackler", "Countdown Crackler",
             "Fires a party clock that sticks to whatever it hits -- a wall, the floor, "
             "somebody's back -- and counts down three, two, one.",
             {"kind": "projectile", "projectile": "clockbomb", "damage": 20, "splash": 9.0,
              "splash_damage": 74, "rpm": 60, "mag": 3, "reload": 2.6, "speed": 70,
              "range": 400, "auto": False, "sound": "rocket", "recoil": 2.2, "reserve": 18,
              "gravity_scale": 0.9, "self_damage": 0.3, "knockback": 24,
              "sticky": True, "fuse": 3.0},
             [["+", "Sticks to walls, floors and people, then goes off after 3 seconds"],
              ["+", "Stuck to a person, it deals 50% more"],
              ["-", "Nothing goes off on impact: plan ahead"],
              ["-", "Three shots a load"]], rarity="legendary",
             proj=lambda: _clock_face([0, 0, 0], 0.45, 1.0) + [
                 part("cyl", [0, 0, -0.10], [0.9, 0.20, 0.9], "#c4281c", [PI / 2, 0, 0]),
                 part("sph", [0, 0.50, 0], [0.12, 0.12, 0.12], "#ffcf3a", m="neon")])
def _():
    return [
        part("cyl", [0, 0.05, 0.75], [0.36, 1.60, 0.36], "#2b2f4a", [PI / 2, 0, 0],
             m="metal", decal="rivets", wrap=True),
        part("torus", [0, 0.05, 1.55], [0.42, 0.08, 0.42], GOLD, [PI / 2, 0, 0], m="metal"),
        part("cyl", [0, 0.05, 0.2], [0.52, 0.42, 0.52], "#1d2a6b", [PI / 2, 0, 0]),
        part("disc", [0, 0.05, -0.02], [0.44, 0.44, 0.05], SNOW, [0, PI, 0], decal="clockface"),
        part("rbox", [0, -0.34, 0.18], [0.18, 0.44, 0.22], "#3a1d0c", [0.3, 0, 0]),
        part("rbox", [0, -0.12, -0.36], [0.22, 0.28, 0.56], "#3a1d0c"),
        part("cyl", [0.0, 0.36, 0.80], [0.10, 0.10, 0.10], "#ffcf3a", m="neon"),
    ]


@NY22.gear("noisemaker", "Noisemaker Horn",
           "Blow it and every teammate within earshot remembers there is a party on: a "
           "burst of speed for everybody near you.",
           {"kind": "ability", "cooldown": 30, "sound": "horn",
            "ability": {"rally": {"radius": 22, "speed": 0.22, "secs": 6}}},
           [["+", "You and every teammate within 22 studs run 22% faster for 6 seconds"],
            ["-", "30 second cooldown"],
            ["=", "Does no damage"]])
def _():
    return [
        place("trumpet", [0, 0.02, 0.2], [0.42, 1.30, 0.42], "#f2c230", anchor=[0, 0, 0],
              r=[PI / 2, 0, 0], decal="party", wrap=True),
        part("cyl", [0, 0.02, 0.05], [0.10, 0.20, 0.10], "#ff4fa0", [PI / 2, 0, 0]),
        place("spiral", [0, 0.02, 1.62], [0.22, 0.40, 0.22], "#3cc8ff", r=[PI / 2, 0, 0]),
    ]


NY22.effect("midnight_chimes", name="Midnight Chimes", rate=3.0, life=[2.0, 2.8],
            size=[0.40, 0.54], grow=0.0, gravity=0.0, spread=0.12, rise=[0.04, 0.18],
            blend="normal", spin=0.3, colors=["#fff6d8", "#ffd96b", "#e0a22a", "#7d5212"],
            shape="clock", radius=0.84, orbit=1.1, upright=True, wobble=0.25)
NY22.effect("confetti_storm", name="Confetti Storm", rate=9.0, life=[1.4, 2.2],
            size=[0.16, 0.26], grow=0.0, gravity=-1.6, spread=0.9, rise=[1.2, 2.0],
            blend="normal", spin=6.0, colors=["#ff4fa0", "#3cc8ff", "#f2c230", "#7dff9a"],
            shapes=["confetti", "confetti", "streamer"], radius=0.4)
NY22.opening(
    sky={"top": "#050a24", "horizon": "#1c2b6b", "sun": [0.3, 0.9, 0.5], "clouds": 0,
         "tint": "#c8d4ff"},
    ambient="#5c6aa8", beam="#fff3b0", seep="midnight_chimes", after="confetti_storm",
    burst=["#f2c230", "#ff4fa0", "#3cc8ff", "#ffffff"],
    pieces=[{"shape": "confetti", "colors": ["#ff4fa0", "#3cc8ff", "#f2c230", "#7dff9a"],
             "blend": "normal"},
            {"shape": "streamer", "colors": ["#ff4fa0", "#f2c230"], "blend": "normal"},
            {"shape": "star", "colors": ["#fff3b0", "#ffd24a"], "blend": "add"}],
    backdrop="newyear", title_wait="Ten... nine... eight...",
    title_shake="Three... two... one...")
NY22.award("First Light", ["Party Guest", "Countdowner", "Toastmaster", "Night Owl",
                           "Midnight Mayor", "First Light Founder"],
           "Opened First Light crates during Blockhaven's launch event, New Year 2022.",
           "em_clock", "clock")
NY22.bundle("pair", "Midnight Pair", 1, 1050, "One Countdown Crate, one Midnight Key.")
NY22.bundle("dozen", "Twelve Chimes", 3, 3000, "Three crates, three keys. Saves 300.")


# ============================================================ 2023
NY23 = Event(
    "newyear_2023", "newyear", 2023, "ny23",
    name="Glitterfall Gala", title="The Glitterfall Gala",
    blurb="Black tie, a masquerade and a champagne tower taller than the Relay. The "
          "ballroom was decorated with forty thousand sequins and nobody has found "
          "the last of them yet.",
    tagline="Dress code: dazzling.",
    starts="2022-12-31", ends="2023-01-15",
    colors={"accent": "#e8c46a", "deep": "#120f18", "glow": "#fff6d0"},
    family_effects=["starstruck", "bubbly", "sunbeam"],
    hero_effect="champagne_fizz", stencil="stencil_ny23")


@NY23.crate_model("Gala Crate",
                  "Black lacquer, bands of gold sequins, a satin bow and a champagne cork "
                  "for a lock. Holds the Glitterfall set. Needs a Corkscrew Key.",
                  hinge=[0, 0.50, -0.56], keyhole=[0, -0.05, 0.69])
def _():
    lacquer, gold = "#16121e", "#e8c46a"
    parts = [
        part("rbox", [0, 0.0, 0], [1.62, 1.00, 1.10], lacquer, m="metal"),
        part("rbox", [0, 0.64, 0], [1.70, 0.30, 1.18], "#1e1828", m="metal", lid=1),
        # sequin bands round the body and the lid
        part("rbox", [0, -0.36, 0], [1.66, 0.14, 1.14], gold, decal="sequins", wrap=True,
             m="metal"),
        part("rbox", [0, 0.30, 0], [1.66, 0.10, 1.14], gold, decal="sequins", wrap=True,
             m="metal"),
        part("rbox", [0, 0.64, 0], [1.74, 0.10, 1.22], gold, decal="sequins", wrap=True,
             m="metal", lid=1),
        part("box", [0, 0.0, -0.562], [0.90, 0.56, 0.02], "#000000", [0, PI, 0],
             decal="stencil_ny23", a=-1),
        part("box", [0.822, 0.0, 0], [0.02, 0.56, 0.80], "#000000", [0, PI / 2, 0],
             decal="stencil_ny23", a=-1),
        part("box", [-0.822, 0.0, 0], [0.02, 0.56, 0.80], "#000000", [0, -PI / 2, 0],
             decal="stencil_ny23", a=-1),
        # the lock is a champagne cork in its wire cage, set into a gold rosette
        part("cyl", [0, -0.05, 0.58], [0.40, 0.06, 0.40], gold, [PI / 2, 0, 0], m="metal",
             lock=1),
        place("cask", [0, -0.05, 0.62], [0.26, 0.20, 0.26], "#c9a26a", anchor=[0, 0, 0],
              r=[PI / 2, 0, 0], decal="leather", wrap=True),
        part("torus", [0, -0.05, 0.66], [0.28, 0.03, 0.28], SILVER, [PI / 2, 0, 0], m="metal"),
        part("disc", [0, -0.05, 0.69], [0.16, 0.16, 0.03], gold, m="metal", decal="keyhole"),
        part("box", [0, 0.48, 0], [1.50, 0.04, 0.96], "#fff6d0", m="neon"),
    ]
    # a satin bow on the lid, and its ribbons over the top
    bow = gift_bow([0, 0.82, 0.05], 1.0, "#f4e7c4", knot=gold)
    bow += [part("rbox", [0, 0.79, 0], [0.16, 0.03, 1.20], "#f4e7c4"),
            part("rbox", [0, 0.79, 0], [1.76, 0.03, 0.16], "#f4e7c4")]
    for p in bow:
        p["lid"] = 1
    parts += bow
    for x in (-0.79, 0.79):
        for zz in (-0.53, 0.53):
            parts.append(place("gem", [x, -0.50, zz], [0.14, 0.14, 0.14], gold,
                               anchor=[0, 0, 0], m="metal"))
    return parts


@NY23.key_model("Corkscrew Key",
                "Its bow is a champagne cork in a wire cage; its blade is a gold "
                "corkscrew. Uncorks one Gala Crate, then pops.", shoulder=-0.22)
def _():
    return [
        place("cask", [-0.66, 0, 0], [0.42, 0.38, 0.42], "#c9a26a", anchor=[0, 0.5, 0],
              r=[0, 0, PI / 2], decal="leather", wrap=True),
        part("torus", [-0.62, 0, 0], [0.44, 0.04, 0.44], SILVER, [0, 0, PI / 2], m="metal"),
        part("torus", [-0.78, 0, 0], [0.42, 0.04, 0.42], SILVER, [0, 0, PI / 2], m="metal"),
        part("disc", [-0.88, 0, 0], [0.34, 0.34, 0.06], "#e8c46a", [0, PI / 2, 0], m="metal"),
        part("cyl", [-0.30, 0, 0], [0.16, 0.20, 0.16], "#e8c46a", [0, 0, PI / 2], m="metal"),
        place("spiral", [0.22, 0, 0], [0.18, 0.86, 0.18], "#e8c46a", anchor=[0, 0, 0],
              r=[0, 0, -PI / 2], m="metal"),
        part("cyl", [0.0, 0, 0], [0.05, 0.50, 0.05], "#e8c46a", [0, 0, PI / 2], m="metal"),
    ]


@NY23.hat("sequin_fedora", "Sequin Fedora",
          "Forty thousand sequins went into the ballroom. About nine hundred of them "
          "went into this.", "rare")
def _():
    return [
        place("brim", [0, -0.06, 0], [2.30, 1.2, 2.22], "#141019", anchor=[0, 0, 0],
              decal="sequins", wrap=True, m="metal"),
        dome(-0.10, 0.92, "#1a1424", decal="sequins", wrap=True, m="metal"),
        part("rbox", [0, 0.62, 0.0], [0.20, 0.12, 0.86], "#141019", [0.10, 0, 0]),
        ringband(0.08, 0.20, "#e8c46a", m="metal"),
        place("feather", [0.62, 0.32, -0.20], 0.95, "#fff6d0", anchor=[0, -0.5, 0],
              r=[0.2, PI / 2, -0.6]),
        place("feather", [0.64, 0.30, -0.12], 0.70, "#e8c46a", anchor=[0, -0.5, 0],
              r=[0.2, PI / 2, -0.4]),
    ]


@NY23.hat("champagne_tower", "Champagne Tower",
          "Six flutes in a pyramid on a silver tray, every one full and fizzing. The "
          "trick is to never, ever nod.", "legendary")
def _():
    parts = [
        cap(-0.26, 0.04, "#1a1424", decal="felt", wrap=True),
        band(-0.20, 0.12, SILVER, grow=0.05, m="metal"),
        part("cyl", [0, 0.07, 0], [1.70, 0.06, 1.70], SILVER, m="metal"),
        part("torus", [0, 0.09, 0], [1.72, 0.05, 1.72], "#e8c46a", m="metal"),
    ]

    def flute(x, y, z):
        return [place("flute", [x, y, z], [0.44, 0.78, 0.44], "#eef7ff", anchor=[0, 0, 0],
                      m="glass", a=0.45),
                part("cyl", [x, y + 0.60, z], [0.16, 0.25, 0.16], "#f6d77a", a=0.85),
                part("sph", [x + 0.03, y + 0.74, z], [0.06, 0.06, 0.06], "#fffbe8", a=0.8)]
    for x, z in ((-0.42, 0.24), (0.42, 0.24), (0, -0.46)):
        parts += flute(x, 0.10, z)
    for x, z in ((-0.21, -0.07), (0.21, -0.07)):
        parts += flute(x, 0.88, z)
    parts += flute(0, 1.66, -0.02)
    return parts


@NY23.hat("masquerade", "Gala Masquerade",
          "A gold filigree mask with three plumes. Wear it and the gala does not know "
          "who you are -- which, at the gala, is the point.", "rare", hair="flat",
          face_cover=True)
def _():
    gold = "#e8c46a"
    return [
        band(-0.36, 0.10, "#141019"),
        place("mask", [0, -0.42, 0.74], [1.36, 0.70, 1.2], gold, m="metal",
              decal="filigree", wrap=True),
        part("sph", [-0.25, -0.44, 0.78], [0.28, 0.17, 0.04], "#141019"),
        part("sph", [0.25, -0.44, 0.78], [0.28, 0.17, 0.04], "#141019"),
        place("gem", [0, -0.34, 0.80], [0.10, 0.10, 0.10], "#c4281c", anchor=[0, 0.36, 0],
              r=[PI / 2, 0, 0], m="glass"),
        place("feather", [0.50, -0.06, 0.62], 0.95, "#141019", anchor=[0, -0.5, 0],
              r=[0.1, 0.3, -0.4]),
        place("feather", [0.58, -0.10, 0.58], 0.80, "#c4281c", anchor=[0, -0.5, 0],
              r=[0.0, 0.3, -0.75]),
        place("feather", [0.44, -0.08, 0.66], 0.70, gold, anchor=[0, -0.5, 0],
              r=[0.2, 0.3, -0.1], m="metal"),
    ]


@NY23.hat("glitter_tiara", "Glitter Tiara",
          "Five points, three diamonds and a ruby the colour of the ballroom carpet.",
          "uncommon", hair="show")
def _():
    gold = "#e8c46a"
    # a thin circlet round the crown, the points rising from its front
    parts = [band(-0.16, 0.06, gold, grow=-0.10, m="metal"),
             band(-0.16, 0.025, "#fff6d0", grow=-0.085, m="metal")]
    for k, (x, h, c) in enumerate(((-0.42, 0.20, "#bfe9ff"), (-0.22, 0.30, "#e8c46a"),
                                   (0.0, 0.44, "#c4281c"), (0.22, 0.30, "#e8c46a"),
                                   (0.42, 0.20, "#bfe9ff"))):
        z = 0.735 - abs(x) * 0.04
        parts.append(place("leaf", [x, -0.15, z], [0.9, h * 1.6, 1.0], gold,
                           anchor=[0, -0.5, 0], r=[-0.30, x * 0.25, 0], m="metal"))
        tip = rotate([0, h * 0.55, 0], [-0.30, x * 0.25, 0])
        parts.append(place("gem", [x + tip[0], -0.15 + tip[1], z + tip[2] + 0.035],
                           [0.12, 0.12, 0.12], c, anchor=[0, 0.36, 0],
                           r=[PI / 2 - 0.30, x * 0.25, 0], m="glass"))
    return parts


@NY23.hat("fascinator", "Feathered Fascinator",
          "A tiny black pillbox at a daring angle, a veil of net and a spray of "
          "feathers. Fascinating, as advertised.", "uncommon", hair="show")
def _():
    tilt = [0.12, 0, -0.30]
    return [
        part("cyl", [0.36, 0.08, 0.38], [0.62, 0.20, 0.62], "#141019", tilt, decal="felt",
             wrap=True),
        part("torus", [0.36, 0.08, 0.38], [0.64, 0.05, 0.64], "#e8c46a", tilt, m="metal"),
        # the veil: down over the right eye
        part("box", [0.30, -0.22, 0.722], [0.54, 0.48, 0.008], "#1c1822", [0, 0, -0.18],
             a=0.38, decal="netting"),
        place("feather", [0.58, 0.20, 0.12], 0.85, "#141019", anchor=[0, -0.5, 0],
              r=[-0.2, PI / 2, -0.5]),
        place("feather", [0.56, 0.18, 0.24], 0.70, "#e8c46a", anchor=[0, -0.5, 0],
              r=[-0.3, PI / 2, -0.8]),
        place("gem", [0.40, 0.20, 0.56], [0.14, 0.14, 0.14], "#bfe9ff", anchor=[0, 0.36, 0],
              r=[PI / 2, 0.4, 0], m="glass"),
    ]


@NY23.hat("gramophone", "Golden Gramophone",
          "A gramophone horn on a turntable, playing the same three bars of swing "
          "it has played since 1923.", "legendary")
def _():
    gold = "#e8c46a"
    return [
        cap(-0.26, 0.02, "#3a1d0c", decal="felt", wrap=True),
        part("rbox", [0, 0.15, 0], [1.10, 0.28, 1.10], "#4a2810", decal="planks", wrap=True),
        part("cyl", [0, 0.31, 0], [0.96, 0.04, 0.96], "#141019", decal="vinyl"),
        part("cyl", [0, 0.34, 0], [0.24, 0.03, 0.24], "#c4281c"),
        part("cyl", [0.36, 0.55, -0.30], [0.06, 0.48, 0.06], gold, m="metal"),
        place("trumpet", [0.36, 0.78, -0.30], [1.5, 1.4, 1.5], gold, anchor=[0, 0, 0],
              r=[-1.0, 0.4, 0], m="metal"),
        part("rbox", [0.56, 0.30, 0.0], [0.08, 0.06, 0.60], gold, [0, 0.3, 0], m="metal"),
        part("cyl", [-0.62, 0.15, 0.0], [0.06, 0.24, 0.06], gold, [0, 0, PI / 2], m="metal"),
        part("sph", [-0.76, 0.15, 0.0], [0.10, 0.10, 0.10], "#141019"),
    ]


@NY23.hat("sparkler_crown", "Sparkler Crown",
          "A velvet crown with seven sparklers for points, all lit, all fizzing, none "
          "of them ever burning down.", "rare")
def _():
    gold = "#e8c46a"
    parts = [
        cap(-0.22, 0.24, "#5a1028", decal="felt", wrap=True),
        band(-0.20, 0.22, gold, grow=0.05, m="metal", decal="sequins", wrap=True),
    ]

    def stick(a, x, z):
        tilt = 0.32
        r = [-math.cos(a) * tilt, 0, math.sin(a) * tilt]
        tip = rotate([0, 0.62, 0], r)
        return [part("cyl", [x + tip[0] * 0.5, -0.04 + tip[1] * 0.5, z + tip[2] * 0.5],
                     [0.03, 0.62, 0.03], "#7a7d84", r, m="metal"),
                place("sparkle", [x + tip[0], -0.04 + tip[1], z + tip[2]], 0.30, "#fff6d0",
                      r=[0, a, 0], m="neon"),
                part("sph", [x + tip[0], -0.04 + tip[1], z + tip[2]], [0.10, 0.10, 0.10],
                     "#ffd96b", m="neon")]
    parts += around(7, 0.90, 0, stick)
    return parts


@NY23.back("sequin_cape", "Sequin Cape",
           "Floor-length black satin lined with gold sequins, so it flashes every time "
           "you turn round. You will turn round a lot.", "rare")
def _():
    return [
        place("cape", [0, 0.98, -0.08], [1.70, 1.92, 1.5], "#141019", anchor=[0, 0, 0],
              decal="sequins", wrap=True, m="metal"),
        place("cape", [0, 0.96, -0.05], [1.58, 1.86, 1.2], "#e8c46a", anchor=[0, 0, 0],
              decal="sequins", wrap=True, m="metal"),
        part("rbox", [0, 0.96, -0.14], [1.40, 0.14, 0.16], "#141019"),
        part("disc", [0.46, 0.96, -0.24], [0.20, 0.20, 0.06], "#e8c46a", [0, PI, 0], m="metal"),
        part("disc", [-0.46, 0.96, -0.24], [0.20, 0.20, 0.06], "#e8c46a", [0, PI, 0], m="metal"),
    ]


@NY23.back("magnum", "Magnum Pack",
           "A champagne magnum on a leather sling, cork mid-flight and foam frozen in "
           "the air. It never empties.", "rare")
def _():
    return [
        place("cask", [0, -0.30, -0.46], [0.66, 1.30, 0.66], "#1d4a2a", anchor=[0, 0, 0],
              m="glass", a=0.92),
        part("cyl", [0, 1.12, -0.46], [0.30, 0.30, 0.30], "#1d4a2a", m="glass", a=0.92),
        part("cyl", [0, 1.30, -0.46], [0.32, 0.20, 0.32], "#e8c46a", m="metal"),
        part("rbox", [0, 0.30, -0.80], [0.40, 0.46, 0.04], "#f4e7c4", decal="stencil_ny23"),
        place("cask", [0, 1.62, -0.46], [0.26, 0.24, 0.26], "#c9a26a", anchor=[0, 0, 0],
              decal="leather", wrap=True),
        part("sph", [0.05, 1.50, -0.46], [0.36, 0.30, 0.36], "#fffbe8", a=0.85),
        part("sph", [-0.08, 1.58, -0.40], [0.24, 0.22, 0.24], "#fffbe8", a=0.85),
        part("rbox", [0.36, 0.40, -0.10], [0.12, 1.60, 0.06], "#5a3016", [0, 0, -0.4],
             decal="leather", wrap=True),
    ]


@NY23.hairdo("finger_waves", "Finger Waves",
             "A glossy 1920s bob set in deep waves, with a single gold pin. The gala "
             "hairdresser charged by the wave.", "rare")
def _():
    c, hi = "#1a1214", "#3a2a2e"
    parts = [place("hairbob", [0, 0, 0], [1.04, 1.04, 1.04], c, anchor=[0, 0, 0],
                   decal="strands", wrap=True)]
    for k in range(4):
        y = 0.42 - k * 0.20
        parts.append(part("rbox", [0, y, -0.02], [1.13 - k * 0.01, 0.06, 1.15 - k * 0.01], hi))
    parts += [place("leaf", [0.16, 0.30, 0.535], [0.7, 0.70, 2.4], hi, r=[0, 0, PI / 2 - 0.3]),
              part("rbox", [-0.40, 0.30, 0.40], [0.16, 0.04, 0.04], "#e8c46a", [0, 0.6, 0.4],
                   m="metal")]
    return parts


@NY23.hairdo("gala_updo", "Gala Updo",
             "Swept up into a twisted bun and pinned with pearls, with two loose curls "
             "left down on purpose.", "uncommon")
def _():
    c = "#7a4a22"
    hi = shade(c, 1.3)
    parts = [place("hairmid", [0, 0, 0], [1.0, 1.0, 1.0], c, anchor=[0, 0, 0],
                   decal="strands", wrap=True),
             part("sph", [0, 0.50, -0.30], [0.52, 0.44, 0.46], c, decal="strands", wrap=True),
             part("torus", [0, 0.50, -0.30], [0.50, 0.12, 0.50], hi, [0.6, 0, 0])]
    parts += [part("sph", [math.sin(a) * 0.24, 0.62, -0.30 + math.cos(a) * 0.20],
                   [0.07, 0.07, 0.07], "#fffaf0", m="glass") for a in (0.6, 1.8, 3.0, 4.2, 5.4)]
    parts += [place("spiral", [0.50 * s, -0.15, 0.26], [0.10, 0.36, 0.10], hi,
                    anchor=[0, 0.5, 0]) for s in (1, -1)]
    return parts


NY23.face("starlet", "Starlet",
          "Long lashes, a beauty mark and a red smile for the cameras.", [
              {"k": "ellipse", "x": -0.22, "y": -0.15, "w": 0.11, "h": 0.15, "c": "#1a1a1a"},
              {"k": "ellipse", "x": 0.22, "y": -0.15, "w": 0.11, "h": 0.15, "c": "#1a1a1a"},
              {"k": "line", "x1": -0.30, "y1": -0.24, "x2": -0.34, "y2": -0.29, "w": 0.02,
               "c": "#1a1a1a"},
              {"k": "line", "x1": -0.26, "y1": -0.25, "x2": -0.28, "y2": -0.31, "w": 0.02,
               "c": "#1a1a1a"},
              {"k": "line", "x1": 0.30, "y1": -0.24, "x2": 0.34, "y2": -0.29, "w": 0.02,
               "c": "#1a1a1a"},
              {"k": "line", "x1": 0.26, "y1": -0.25, "x2": 0.28, "y2": -0.31, "w": 0.02,
               "c": "#1a1a1a"},
              {"k": "ellipse", "x": 0.16, "y": 0.10, "w": 0.03, "h": 0.03, "c": "#1a1a1a"},
              {"k": "arc", "x": 0, "y": 0.06, "r": 0.20, "a0": 0.10, "a1": 0.40,
               "w": 0.07, "c": "#c4281c"},
          ], "rare")
NY23.face("fizzy", "Fizzy",
          "Sparkles in both eyes and a grin like a shaken bottle.", [
              {"k": "star", "x": -0.22, "y": -0.16, "r": 0.09, "c": "#e0a22a", "n": 4},
              {"k": "star", "x": 0.22, "y": -0.16, "r": 0.09, "c": "#e0a22a", "n": 4},
              {"k": "ellipse", "x": -0.22, "y": -0.16, "w": 0.06, "h": 0.06, "c": "#1a1a1a"},
              {"k": "ellipse", "x": 0.22, "y": -0.16, "w": 0.06, "h": 0.06, "c": "#1a1a1a"},
              {"k": "arc", "x": 0, "y": 0.02, "r": 0.26, "a0": 0.07, "a1": 0.43,
               "w": 0.055, "c": "#1a1a1a"},
              {"k": "ring", "x": 0.28, "y": 0.12, "r": 0.03, "w": 0.012, "c": "#e0a22a"},
              {"k": "ring", "x": 0.31, "y": 0.04, "r": 0.02, "w": 0.01, "c": "#e0a22a"},
          ])
NY23.shirt("gala_tailcoat", "Gala Tailcoat",
           "Black tails, gold sequin lapels and a white bow tie. Black tie, white tie, "
           "gold tie, all at once.",
           {"torso": "#141019", "arms": "#141019", "decal": "tee_tailcoat",
            "stripe": "#e8c46a"}, "rare")
NY23.belt("gilded_sash", "Gilded Sash",
          "A wide gold sash with a jewelled clasp, for whoever is hosting.",
          {"band": "#e8c46a", "buckle": "#bfe9ff", "width": 0.30, "metal": True,
           "weave": "sequins"})


@NY23.weapon("bubbly_blaster", "Bubbly Blaster",
             "A champagne bottle that only gets more dangerous the longer you hold it "
             "without firing. Shake, aim, and let the cork fly.",
             {"kind": "projectile", "projectile": "cork", "damage": 16, "splash": 3.0,
              "splash_damage": 10, "rpm": 80, "mag": 6, "reload": 1.8, "speed": 110,
              "range": 300, "auto": False, "sound": "pop", "recoil": 1.6, "reserve": 36,
              "gravity_scale": 0.25, "self_damage": 0.0, "knockback": 10,
              "pressure": {"max": 5, "per_sec": 1.0, "damage": 13, "knock": 7,
                           "label": "Pressure"}},
             [["+", "Builds 1 Pressure a second while you hold it without firing (up to 5)"],
              ["+", "Each Pressure adds 13 damage and a harder shove to the next cork"],
              ["-", "An unshaken cork does only 16 damage"],
              ["-", "Any shot spends all the Pressure"]], rarity="legendary",
             proj=lambda: [place("cask", [0, 0, 0], [0.30, 0.26, 0.30], "#c9a26a",
                                 anchor=[0, 0.5, 0], r=[PI / 2, 0, 0], decal="leather",
                                 wrap=True)])
def _():
    return [
        place("cask", [0, 0.04, 0.10], [0.50, 1.00, 0.50], "#1d4a2a", anchor=[0, 0, 0],
              r=[PI / 2, 0, 0], m="glass", a=0.92),
        part("cyl", [0, 0.04, 1.20], [0.24, 0.30, 0.24], "#1d4a2a", [PI / 2, 0, 0],
             m="glass", a=0.92),
        part("cyl", [0, 0.04, 1.40], [0.26, 0.18, 0.26], "#e8c46a", [PI / 2, 0, 0], m="metal"),
        place("cask", [0, 0.04, 1.50], [0.22, 0.18, 0.22], "#c9a26a", anchor=[0, 0, 0],
              r=[PI / 2, 0, 0], decal="leather", wrap=True),
        part("rbox", [0, 0.30, 0.60], [0.36, 0.04, 0.46], "#f4e7c4", [0, 0, 0],
             decal="stencil_ny23"),
        part("rbox", [0, -0.32, 0.18], [0.18, 0.40, 0.22], "#3a1d0c", [0.3, 0, 0]),
    ]


@NY23.weapon("sequin_saber", "Sequin Saber",
             "A fencing sabre crusted in gold sequins. Each hit dazzles; three in a row "
             "leave the target so dazzled they take more from everyone.",
             {"kind": "melee", "damage": 26, "headshot": 1.3, "rpm": 130, "range": 10.5,
              "arc": 0.42, "sound": "sword", "knockback": 6,
              "on_hit": {"dazzle": [3, 4.0, 0.30, 5.0]}},
             [["+", "Fast: 130 swings a minute"],
              ["+", "Three hits within 4 seconds Dazzle the target: they take 30% more "
                    "damage from everyone for 5 seconds"],
              ["-", "26 damage a hit"],
              ["-", "Narrow swing"]], rarity="legendary")
def _():
    gold = "#e8c46a"
    return [
        place("blade", [0.0, 0.0, 1.40], [2.20, 0.34, 1.0], "#e9eef5", anchor=[0, 0, 0],
              r=[PI / 2, PI / 2, 0], m="metal", decal="sequins"),
        part("rbox", [0, 0, 0.30], [0.06, 0.07, 0.30], gold, m="metal"),
        place("arch", [0.12, 0, 0.18], [0.40, 0.40, 1.0], gold, anchor=[0, 0, 0],
              r=[0, PI / 2, PI / 2], m="metal"),
        part("cyl", [0, 0, -0.06], [0.14, 0.44, 0.14], "#141019", [PI / 2, 0, 0],
             decal="leather", wrap=True),
        part("sph", [0, 0, -0.30], [0.16, 0.16, 0.16], gold, m="metal"),
    ]


@NY23.weapon("gold_rush", "Gold Rush Revolver",
             "A gold-plated six-shooter. Every kill refills the cylinder, and the next "
             "three shots ring off whoever they hit into whoever is next to them.",
             {"kind": "hitscan", "damage": 30, "headshot": 2.0, "rpm": 170, "mag": 6,
              "reload": 2.0, "spread": 0.7, "pellets": 1, "range": 240, "auto": False,
              "sound": "pistol", "recoil": 1.6, "reserve": 42, "tracer": "#ffd96b",
              "on_kill": {"refill": True, "ricochet_shots": 3, "gild": True},
              "ricochet": {"range": 22, "falloff": 0.6}},
             [["+", "A kill refills the cylinder"],
              ["+", "After a kill, the next 3 shots ricochet into the nearest other enemy "
                    "for 60% damage"],
              ["-", "Six shots and a slow reload"],
              ["=", "Victims are briefly gilded, gold head to toe"]], rarity="legendary")
def _():
    gold = "#e8c46a"
    return [
        part("cyl", [0, 0.06, 0.62], [0.16, 0.96, 0.16], gold, [PI / 2, 0, 0], m="metal"),
        part("rbox", [0, 0.12, 0.62], [0.12, 0.08, 0.90], gold, m="metal"),
        part("cyl", [0, 0.02, 0.18], [0.36, 0.30, 0.36], "#b8952e", [PI / 2, 0, 0], m="metal",
             decal="rivets", wrap=True),
        part("rbox", [0, -0.30, -0.04], [0.18, 0.52, 0.26], "#f4e7c4", [0.36, 0, 0],
             decal="filigree"),
        place("arch", [0, -0.12, 0.16], [0.22, 0.22, 0.8], gold, anchor=[0, 0, 0],
              r=[0, PI / 2, PI], m="metal"),
        part("rbox", [0, 0.20, 0.0], [0.06, 0.10, 0.12], gold, m="metal"),
    ]


@NY23.gear("cider", "Sparkling Cider",
           "A whole bottle of sparkling cider, drunk in one go. Patches you up and puts "
           "a spring in your step.",
           {"kind": "consume", "cooldown": 25, "sound": "drink",
            "consume": {"heal": 30, "over": 3.0, "speed": [0.18, 5.0]}},
           [["+", "Heals 30 over 3 seconds"],
            ["+", "18% faster for 5 seconds"],
            ["-", "25 second cooldown"]])
def _():
    return [
        place("cask", [0, 0.0, 0.10], [0.40, 0.80, 0.40], "#c98a2a", anchor=[0, 0, 0],
              r=[PI / 2, 0, 0], m="glass", a=0.85),
        part("cyl", [0, 0.0, 0.98], [0.18, 0.22, 0.18], "#c98a2a", [PI / 2, 0, 0], m="glass",
             a=0.85),
        part("cyl", [0, 0.0, 1.12], [0.20, 0.10, 0.20], "#e8c46a", [PI / 2, 0, 0], m="metal"),
        part("rbox", [0, 0.20, 0.50], [0.30, 0.04, 0.36], "#f4e7c4"),
    ]


NY23.effect("champagne_fizz", name="Champagne Fizz", rate=12.0, life=[1.3, 2.1],
            size=[0.10, 0.22], grow=0.04, gravity=0.9, spread=0.30, rise=[0.8, 1.5],
            blend="add", spin=0.6, colors=["#fffbe8", "#ffe9a0", "#e8c46a", "#a87a22"],
            shape="bubble", radius=0.45)
NY23.effect("sequin_shower", name="Sequin Shower", rate=10.0, life=[1.5, 2.3],
            size=[0.14, 0.24], grow=0.0, gravity=-1.2, spread=0.7, rise=[0.9, 1.6],
            blend="add", spin=7.0, colors=["#ffffff", "#fff0b8", "#e8c46a", "#b8862e"],
            shape="sequin", radius=0.5)
NY23.opening(
    sky={"top": "#08060c", "horizon": "#2a2030", "sun": [0.3, 0.9, 0.5], "clouds": 0,
         "tint": "#ffe9c0"},
    ambient="#8a7a6a", beam="#fff6d0", seep="champagne_fizz", after="sequin_shower",
    burst=["#e8c46a", "#fff6d0", "#ffffff", "#c9a26a"],
    pieces=[{"shape": "sequin", "colors": ["#ffffff", "#e8c46a", "#fff0b8"], "blend": "add"},
            {"shape": "bubble", "colors": ["#fffbe8", "#ffe9a0"], "blend": "add"},
            {"shape": "confetti", "colors": ["#e8c46a", "#141019", "#fff6d0"],
             "blend": "normal"}],
    backdrop="gala", title_wait="The band strikes up...", title_shake="Pop the cork...")
NY23.award("Glitterfall Gala", ["Plus-One", "Socialite", "Belle of the Ball", "Toast "
                                "of the Town", "High Society", "Gala Royalty"],
           "Opened Gala Crates during the Glitterfall Gala, New Year 2023.",
           "em_champagne", "clock")
NY23.bundle("pair", "Gala Pair", 1, 1050, "One Gala Crate, one Corkscrew Key.")
NY23.bundle("table", "Table for Three", 3, 3000, "Three crates, three keys. Saves 300.")


# ============================================================ 2024
NY24 = Event(
    "newyear_2024", "newyear", 2024, "ny24",
    name="Rocket Rally", title="The Rocket Rally",
    blurb="Somebody ordered the fireworks for 2024 by the pallet instead of by the "
          "box. The whole server lit up at midnight -- and at 00:04, and at 00:11, "
          "and for most of the following week.",
    tagline="Light the fuse. Stand well back. Further than that.",
    starts="2023-12-31", ends="2024-01-15",
    colors={"accent": "#ff3b4e", "deep": "#0a0d1f", "glow": "#ffcf3a"},
    family_effects=["ember_storm", "scorching", "static_charge"],
    hero_effect="sky_bloom", stencil="stencil_ny24")


@NY24.crate_model("Launch Crate",
                  "A riveted steel firework crate with a rack of rockets on the lid and "
                  "a fuse running to the lock. Holds the Rocket Rally set. Needs a Fuse "
                  "Key.", hinge=[0, 0.50, -0.56], keyhole=[0, -0.08, 0.62])
def _():
    steel, red = "#4a4f58", "#c4281c"
    parts = [
        part("rbox", [0, 0.0, 0], [1.64, 1.00, 1.10], steel, m="metal", decal="rivets",
             wrap=True),
        part("rbox", [0, 0.64, 0], [1.70, 0.28, 1.16], "#3a3e46", m="metal", decal="rivets",
             wrap=True, lid=1),
        # hazard bands
        part("rbox", [0, -0.38, 0], [1.68, 0.16, 1.14], "#f5c518", decal="hazard", wrap=True),
        part("rbox", [0, 0.36, 0], [1.68, 0.10, 1.14], red),
        part("box", [0, 0.02, -0.562], [0.96, 0.60, 0.02], "#000000", [0, PI, 0],
             decal="stencil_ny24", a=-1),
        part("box", [0.832, 0.02, 0], [0.02, 0.56, 0.80], "#000000", [0, PI / 2, 0],
             decal="stencil_ny24", a=-1),
        part("box", [-0.832, 0.02, 0], [0.02, 0.56, 0.80], "#000000", [0, -PI / 2, 0],
             decal="stencil_ny24", a=-1),
        # the lock: an ignition plate with a fuse wire running to it
        part("rbox", [0, -0.08, 0.575], [0.42, 0.40, 0.07], "#c9a227", m="metal",
             decal="keyhole", lock=1),
        part("cyl", [0, 0.18, 0.60], [0.04, 0.16, 0.04], "#2b2b30"),
        place("spiral", [0.28, 0.28, 0.60], [0.22, 0.16, 0.22], "#2b2b30", r=[PI / 2, 0, 0]),
        part("sph", [0.40, 0.30, 0.62], [0.10, 0.10, 0.10], "#ffcf3a", m="neon"),
        part("box", [0, 0.48, 0], [1.50, 0.04, 0.96], "#ffcf3a", m="neon"),
    ]
    # the rocket rack on the lid
    colours = [red, "#2f6fd6", "#2fa84f", "#f5c518", "#b26bff"]
    for k, x in enumerate((-0.56, -0.28, 0.0, 0.28, 0.56)):
        parts += [
            place("rocket", [x, 0.78, -0.10], [0.40, 0.95, 0.40], colours[k], anchor=[0, 0, 0],
                  decal="party", wrap=True, lid=1),
            part("cyl", [x, 0.78 + 0.95 + 0.12, -0.10], [0.02, 0.22, 0.02], "#2b2b30", lid=1),
            place("tri", [x + 0.08, 0.84, -0.10], [0.14, 0.18, 0.2], colours[(k + 2) % 5],
                  r=[0, PI / 2, 0], lid=1),
            place("tri", [x - 0.08, 0.84, -0.10], [0.14, 0.18, 0.2], colours[(k + 2) % 5],
                  r=[0, PI / 2, 0], lid=1),
        ]
    for x in (-0.80, 0.80):
        for zz in (-0.53, 0.53):
            for yy, lid in ((-0.46, 0), (0.74, 1)):
                parts.append(part("rbox", [x, yy, zz], [0.14, 0.14, 0.14], "#2b2b30",
                                  m="metal", lid=lid or None))
    return parts


@NY24.key_model("Fuse Key",
                "Its bow is a coil of fuse with the spark already lit; its blade is a "
                "rocket stick. Opens one Launch Crate and fizzles out.", shoulder=-0.30)
def _():
    return [
        place("spiral", [-0.64, 0, 0], [0.70, 0.22, 0.70], "#3a2e22", anchor=[0, 0, 0],
              r=[PI / 2, 0, 0]),
        part("disc", [-0.64, 0, 0], [0.40, 0.40, 0.10], "#c4281c", decal="party"),
        part("sph", [-0.94, 0.20, 0], [0.16, 0.16, 0.16], "#ffcf3a", m="neon"),
        place("sparkle", [-0.94, 0.20, 0.04], 0.34, "#fff6c9", m="neon"),
        part("cyl", [0.10, 0, 0], [0.10, 1.04, 0.10], "#c8a070", [0, 0, PI / 2]),
        part("torus", [-0.30, 0, 0], [0.20, 0.08, 0.20], "#c4281c", [0, 0, PI / 2], m="metal"),
        place("flame", [0.52, -0.10, 0], [0.18, 0.22, 0.5], "#ff8c1a", r=[0, 0, PI], m="neon"),
        place("rocket", [0.64, 0, 0], [0.18, 0.30, 0.18], "#c4281c", anchor=[0, 0.5, 0],
              r=[0, 0, -PI / 2]),
    ]


@NY24.hat("rocket_beanie", "Rocket Beanie",
          "A red knitted beanie with a firework rocket where the bobble should be. "
          "The fuse is lit. It has been lit since 2024.", "rare")
def _():
    return [
        dome(-0.32, 1.02, "#c4281c", decal="knit", wrap=True),
        band(-0.28, 0.34, "#f2f3f3", grow=0.12, decal="knit", wrap=True),
        place("rocket", [0, 0.62, 0], [0.48, 1.10, 0.48], "#2f6fd6", anchor=[0, 0, 0],
              decal="party", wrap=True),
        place("tri", [0.13, 0.72, 0], [0.24, 0.30, 0.2], "#f5c518", r=[0, PI / 2, 0]),
        place("tri", [-0.13, 0.72, 0], [0.24, 0.30, 0.2], "#f5c518", r=[0, PI / 2, 0]),
        place("tri", [0, 0.72, 0.13], [0.24, 0.30, 0.2], "#f5c518"),
        place("tri", [0, 0.72, -0.13], [0.24, 0.30, 0.2], "#f5c518"),
        part("cyl", [0, 1.84, 0], [0.03, 0.20, 0.03], "#2b2b30"),
        place("sparkle", [0, 1.98, 0], 0.30, "#fff6c9", m="neon"),
    ]


@NY24.hat("mortar_helmet", "Mortar Helmet",
          "A firework mortar tube, cut down and padded, worn as a helmet. The paper "
          "wrap still says DO NOT HOLD.", "uncommon")
def _():
    return [
        place("cask", [0, -0.34, 0], [1.88, 1.20, 1.88], "#e8d9b8", anchor=[0, 0, 0],
              decal="firecracker", wrap=True),
        part("box", [0, 0.20, 0.905], [0.62, 0.46, 0.01], "#000000", [-0.05, 0, 0],
             decal="stencil_ny24", a=-1),
        ringband(-0.30, 0.14, "#c4281c"),
        ringband(0.70, 0.12, "#2f6fd6"),
        part("cyl", [0, 0.86, 0], [1.40, 0.04, 1.40], "#2b2b30"),
        part("cyl", [0, 0.62, 0], [1.20, 0.40, 1.20], "#1d1e22"),
        part("cyl", [0.62, 0.44, 0.40], [0.03, 0.34, 0.03], "#2b2b30", [0.4, 0, -0.5]),
        part("sph", [0.70, 0.60, 0.48], [0.10, 0.10, 0.10], "#ffcf3a", m="neon"),
    ]


@NY24.hat("sky_bloom_crown", "Sky Bloom Crown",
          "A firework caught at the top of its burst: a ring of sparkling petals on "
          "stalks of smoke, blooming above you for ever.", "legendary", hair="show")
def _():
    colours = ["#ff3b4e", "#ffcf3a", "#3cc8ff", "#ff4fd8", "#7dff9a"]
    parts = [
        band(-0.16, 0.12, "#2b2b30", grow=-0.08, m="metal"),
        band(-0.16, 0.04, "#ffcf3a", grow=-0.06, m="metal"),
        part("sph", [0, 0.80, 0], [0.30, 0.30, 0.30], "#fff6c9", m="neon"),
        # the trail it rose on: puffs of smoke twisting up from the crown
        part("sph", [0.0, 0.08, 0.0], [0.62, 0.20, 0.58], "#cfd3da", a=0.75),
        part("sph", [0.04, 0.26, 0.02], [0.40, 0.20, 0.38], "#d9dce2", a=0.65),
        part("sph", [-0.03, 0.44, 0.0], [0.26, 0.18, 0.26], "#e3e6ea", a=0.55),
        part("cyl", [0, 0.50, 0], [0.06, 0.50, 0.06], "#ffcf3a", m="neon", a=0.6),
    ]
    # little rockets standing round the band, waiting their turn
    parts += around(4, 0.81, 0, lambda a, x, z: [
        part("cyl", [x, -0.06, z], [0.10, 0.30, 0.10], colours[int(round(a * 4 / TAU)) % 5]),
        part("cone", [x, 0.15, z], [0.11, 0.14, 0.11], SNOW)])
    for k in range(12):
        a = k * TAU / 12
        d = [math.sin(a), 0.45, math.cos(a)]
        tip = [d[0] * 0.80, 0.80 + d[1] * 0.80, d[2] * 0.80]
        parts.append(part("cyl", [d[0] * 0.40, 0.80 + d[1] * 0.40, d[2] * 0.40],
                          [0.03, 0.82, 0.03], colours[k % 5],
                          [math.cos(a) * 1.1, 0, -math.sin(a) * 1.1], m="neon", a=0.7))
        parts.append(place("star" if k % 2 else "sparkle", tip, 0.26, colours[k % 5],
                           r=[0, a, 0], m="neon"))
    return parts


@NY24.hat("blast_goggles", "Blast Goggles",
          "Leather pyro goggles over a scorched flying cap. The soot is genuine and "
          "will not wash out.", "uncommon")
def _():
    return [
        dome(-0.30, 0.86, "#5a3a22", t="capcrown", decal="leather", wrap=True),
        part("rbox", [0, -0.22, 0], [1.60, 0.12, 1.54], "#2b2b30", decal="leather", wrap=True),
        part("cyl", [-0.26, -0.20, 0.80], [0.40, 0.22, 0.40], "#2b2b30", [PI / 2, 0, 0], m="metal"),
        part("cyl", [0.26, -0.20, 0.80], [0.40, 0.22, 0.40], "#2b2b30", [PI / 2, 0, 0], m="metal"),
        part("cyl", [-0.26, -0.20, 0.91], [0.30, 0.03, 0.30], "#ff8c1a", [PI / 2, 0, 0],
             m="glass", a=0.75),
        part("cyl", [0.26, -0.20, 0.91], [0.30, 0.03, 0.30], "#ff8c1a", [PI / 2, 0, 0],
             m="glass", a=0.75),
        part("rbox", [0, -0.20, 0.84], [0.16, 0.08, 0.10], "#2b2b30"),
        part("sph", [0.40, 0.30, 0.50], [0.30, 0.10, 0.26], "#1a1a1a", a=0.55),
        part("sph", [-0.30, 0.42, -0.10], [0.36, 0.10, 0.30], "#1a1a1a", a=0.45),
    ]


@NY24.hat("catherine_wheel", "Catherine Wheel",
          "A pinwheel firework nailed to the top of a cap, spinning and spitting "
          "sparks in every direction. Mostly in yours.", "rare")
def _():
    return [
        dome(-0.30, 0.74, "#2f6fd6", t="capcrown", decal="panels", wrap=True),
        part("cyl", [0, 0.58, 0], [0.08, 0.42, 0.08], "#c8a070"),
        place("pinwheel", [0, 0.86, 0.06], [1.40, 1.40, 1.0], "#ff3b4e", r=[0, 0, 0],
              spin=5.0, decal="party", wrap=True),
        part("sph", [0, 0.86, 0.10], [0.16, 0.16, 0.16], "#ffcf3a", m="metal"),
        place("sparkle", [0.62, 1.10, 0.06], 0.26, "#fff6c9", m="neon", spin=5.0),
        place("sparkle", [-0.58, 0.60, 0.06], 0.22, "#ffcf3a", m="neon", spin=5.0),
    ]


@NY24.hat("firecracker_fez", "Firecracker Fez",
          "A fez rolled from red firecracker paper, with a fuse for a tassel. Do not "
          "stand near a candle.", "uncommon")
def _():
    return [
        place("cask", [0, -0.34, 0], [1.86, 0.98, 1.86], "#c4281c", anchor=[0, 0, 0],
              decal="firecracker", wrap=True),
        part("cyl", [0, 0.64, 0], [1.40, 0.04, 1.40], "#a8201a"),
        ringband(-0.30, 0.12, "#f2c230", m="metal"),
        part("cyl", [0, 0.72, 0], [0.12, 0.12, 0.12], "#f2c230", m="metal"),
        place("hook", [0.0, 0.76, 0.0], 0.50, "#3a2e22", anchor=[0, 0, 0], r=[0, PI / 2, 0]),
        part("sph", [0.0, 0.50, -0.42], [0.12, 0.12, 0.12], "#ffcf3a", m="neon"),
    ]


@NY24.hat("spark_fountain", "Spark Fountain",
          "A cone fountain firework on a gold band, pouring a column of white and gold "
          "sparks straight up. Indoors, apparently, is fine.", "legendary")
def _():
    parts = [
        band(-0.18, 0.20, "#f2c230", grow=0.05, m="metal"),
        cap(-0.22, 0.08, "#2b2b30"),
        part("cone", [0, 0.62, 0], [0.86, 0.90, 0.86], "#2f6fd6", decal="party", wrap=True),
        part("cyl", [0, 0.16, 0], [0.88, 0.06, 0.88], "#f2c230", m="metal"),
        part("cyl", [0, 1.10, 0], [0.12, 0.10, 0.12], "#2b2b30"),
    ]
    for k in range(9):
        a = k * TAU / 9
        h = 0.5 + (k % 3) * 0.25
        parts.append(part("cyl", [math.sin(a) * 0.12, 1.16 + h / 2, math.cos(a) * 0.12],
                          [0.03, h, 0.03], "#fff6c9" if k % 2 else "#ffcf3a",
                          [-math.cos(a) * 0.25, 0, math.sin(a) * 0.25], m="neon", a=0.8))
        parts.append(place("sparkle", [math.sin(a) * (0.12 + h * 0.25), 1.16 + h,
                                       math.cos(a) * (0.12 + h * 0.25)],
                           0.20, "#fff6c9", m="neon"))
    return parts


@NY24.back("rocket_rack", "Rocket Rack",
           "Five rockets on a back rack, fuses lit in a row. The straps are "
           "flame-retardant. You are not.", "legendary")
def _():
    colours = ["#c4281c", "#2f6fd6", "#2fa84f", "#f5c518", "#b26bff"]
    parts = [part("rbox", [0, 0.0, -0.32], [1.20, 1.10, 0.26], "#4a4f58", m="metal",
                  decal="rivets", wrap=True),
             part("rbox", [0, -0.50, -0.46], [1.24, 0.14, 0.40], "#2b2b30", m="metal")]
    for k, x in enumerate((-0.44, -0.22, 0.0, 0.22, 0.44)):
        parts += [
            place("rocket", [x, -0.46, -0.58], [0.40, 1.50, 0.40], colours[k], anchor=[0, 0, 0],
                  decal="party", wrap=True),
            place("tri", [x, -0.36, -0.70], [0.16, 0.22, 0.2], colours[(k + 1) % 5]),
            part("cyl", [x, 1.20, -0.58], [0.02, 0.20, 0.02], "#2b2b30"),
            part("sph", [x, 1.32, -0.58], [0.08, 0.08, 0.08], "#ffcf3a", m="neon"),
        ]
    parts += straps("#2b2b30", 0.38, 0.14)
    return parts


@NY24.back("smoke_wings", "Smoke Trail Wings",
           "Two wings of firework smoke, still glowing with the sparks that made "
           "them. They drift a little when you stand still.", "rare")
def _():
    parts = []
    for side in (1, -1):
        for k in range(7):
            t = k / 6.0
            x = (0.30 + t * 1.30) * side
            y = 0.50 + math.sin(t * PI) * 0.50 - t * 0.2
            r = 0.36 - t * 0.12
            parts.append(part("sph", [x, y, -0.56 - t * 0.2], [r * 2, r * 1.7, r * 1.4],
                              mix("#cfd3d8", "#6b7078", t), a=0.85, decal="fur", wrap=True))
            if k % 2:
                parts.append(part("sph", [x, y + r * 0.6, -0.56 - t * 0.2 - r * 0.5],
                                  [0.08, 0.08, 0.08], "#ffcf3a", m="neon"))
    parts.append(part("rbox", [0, 0.50, -0.26], [0.36, 0.40, 0.18], "#2b2b30", m="metal"))
    return parts


@NY24.hairdo("burnt_frizz", "Burnt Frizz",
             "What is left after standing too close to the 00:04 volley. Still smoking "
             "a little.", "uncommon")
def _():
    c = "#3a2a1e"
    parts = [place("hairshort", [0, 0, 0], [1.03, 1.03, 1.03], c, anchor=[0, 0, 0],
                   decal="strands", wrap=True)]
    for k in range(16):
        a = k * TAU / 16
        z = math.cos(a) * 0.40
        if z > 0.32:
            continue
        parts.append(part("sph", [math.sin(a) * 0.44, 0.40 + (k % 3) * 0.04, z],
                          [0.30, 0.26, 0.30], shade(c, 0.8 + (k % 3) * 0.15),
                          decal="fur", wrap=True))
    parts += [part("sph", [0.10, 0.68, -0.10], [0.42, 0.30, 0.40], c, decal="fur", wrap=True),
              part("sph", [0.20, 0.92, -0.10], [0.26, 0.22, 0.22], "#9aa0aa", a=0.5),
              part("sph", [0.30, 1.10, -0.14], [0.18, 0.16, 0.16], "#9aa0aa", a=0.35)]
    return parts


@NY24.hairdo("spark_spikes", "Spark Spikes",
             "Spiked up stiff and tipped with sparks that never quite go out.", "rare")
def _():
    c = "#1a1a1a"
    parts = [place("hairshort", [0, 0, 0], [1.0, 1.0, 1.0], c, anchor=[0, 0, 0],
                   decal="strands", wrap=True)]
    for ring, (radius, count, h, tilt, y) in enumerate(((0.0, 1, 0.50, 0.0, 0.52),
                                                        (0.22, 6, 0.42, 0.45, 0.50),
                                                        (0.40, 8, 0.30, 0.80, 0.44))):
        for k in range(count):
            a = TAU * k / max(1, count) + ring * 0.3
            x, z = math.sin(a) * radius, math.cos(a) * radius - 0.04
            r = [-math.cos(a) * tilt - 0.1, 0, math.sin(a) * tilt]
            parts.append(place("cone", [x, y, z], [0.22, h, 0.22], c, anchor=[0, -0.5, 0], r=r))
            tip = rotate([0, h, 0], r)
            parts.append(part("sph", [x + tip[0], y + tip[1], z + tip[2]], [0.07, 0.07, 0.07],
                              "#ffcf3a", m="neon"))
    return parts


NY24.face("soot", "Soot Face",
          "Blinking through a layer of firework soot, eyebrows mostly gone.", [
              {"k": "ellipse", "x": -0.24, "y": -0.02, "w": 0.30, "h": 0.22, "c": "#3a3a3a"},
              {"k": "ellipse", "x": 0.20, "y": 0.10, "w": 0.26, "h": 0.18, "c": "#3a3a3a"},
              {"k": "ellipse", "x": -0.22, "y": -0.16, "w": 0.14, "h": 0.14, "c": "#ffffff"},
              {"k": "ellipse", "x": 0.22, "y": -0.16, "w": 0.14, "h": 0.14, "c": "#ffffff"},
              {"k": "ellipse", "x": -0.22, "y": -0.16, "w": 0.06, "h": 0.07, "c": "#1a1a1a"},
              {"k": "ellipse", "x": 0.22, "y": -0.16, "w": 0.06, "h": 0.07, "c": "#1a1a1a"},
              {"k": "rect", "x": 0.02, "y": 0.20, "w": 0.22, "h": 0.05, "c": "#1a1a1a",
               "rot": 0.15},
          ])
NY24.face("kaboom", "Kaboom",
          "Eyes wide, mouth wider, the moment the big one went off overhead.", [
              {"k": "ellipse", "x": -0.23, "y": -0.18, "w": 0.16, "h": 0.20, "c": "#1a1a1a"},
              {"k": "ellipse", "x": 0.23, "y": -0.18, "w": 0.16, "h": 0.20, "c": "#1a1a1a"},
              {"k": "star", "x": -0.23, "y": -0.18, "r": 0.05, "c": "#ffcf3a"},
              {"k": "star", "x": 0.23, "y": -0.18, "r": 0.05, "c": "#ff3b4e"},
              {"k": "ellipse", "x": 0, "y": 0.18, "w": 0.22, "h": 0.26, "c": "#1a1a1a"},
              {"k": "ellipse", "x": 0, "y": 0.24, "w": 0.12, "h": 0.10, "c": "#c4281c"},
          ], "rare")
NY24.shirt("pyro_vest", "Pyro Vest",
           "A hi-vis firework crew vest with a rocket on the back and singe marks on "
           "the front.",
           {"torso": "#ff8c1a", "arms": "#2b2b30", "sleeves": 1.0, "stripe": "#c8cbcd",
            "weave": "hivis", "decal": "tee_rocket"})
NY24.pants("blast_trousers", "Blast-Proof Trousers",
           "Heavy canvas with orange flash stripes. Rated for most explosions.",
           {"legs": "#3a3e46", "stripe": "#ff8c1a", "weave": "canvas", "cuff": "#2b2b30"})


@NY24.weapon("roman_candle", "Roman Candle",
             "Pull the trigger once and it empties itself: eight balls of coloured fire "
             "in a rising volley. Anything they touch keeps burning.",
             {"kind": "projectile", "projectile": "fireball", "damage": 11, "splash": 2.5,
              "splash_damage": 6, "rpm": 34, "mag": 1, "reload": 2.6, "speed": 84,
              "range": 260, "auto": False, "sound": "pop", "recoil": 1.0, "reserve": 12,
              "gravity_scale": 0.45, "self_damage": 0.0, "knockback": 3,
              "volley": [8, 0.11], "volley_spread": 2.2,
              "on_hit": {"burn": [6, 3.0]}},
             [["+", "Each pull fires a volley of 8 fireballs"],
              ["+", "Every fireball sets the target burning: 6 a second for 3 seconds"],
              ["-", "One volley, then a 2.6 second reload"],
              ["-", "Only 11 damage a fireball"]], rarity="legendary",
             proj=lambda: [part("sph", [0, 0, 0], [0.55, 0.55, 0.55], "#ff8c1a", m="neon")])
def _():
    return [
        part("cyl", [0, 0.04, 0.90], [0.30, 2.20, 0.30], "#c4281c", [PI / 2, 0, 0],
             decal="party", wrap=True),
        part("cyl", [0, 0.04, 2.02], [0.32, 0.06, 0.32], "#f2c230", [PI / 2, 0, 0], m="metal"),
        part("cyl", [0, 0.04, 2.06], [0.20, 0.04, 0.20], "#1d1e22", [PI / 2, 0, 0]),
        part("cyl", [0, 0.04, -0.20], [0.26, 0.40, 0.26], "#3a2e22", [PI / 2, 0, 0],
             decal="leather", wrap=True),
        part("torus", [0, 0.04, 0.0], [0.34, 0.06, 0.34], "#f2c230", [PI / 2, 0, 0], m="metal"),
        part("cyl", [0, 0.04, -0.46], [0.06, 0.20, 0.06], "#3a2e22", [PI / 2, 0, 0]),
    ]


@NY24.weapon("sky_bloom", "Sky Bloom Launcher",
             "A mortar that lobs a shell high, then bursts it into six burning "
             "bomblets that rain down over everything beneath.",
             {"kind": "projectile", "projectile": "shell", "damage": 30, "splash": 6.0,
              "splash_damage": 28, "rpm": 40, "mag": 2, "reload": 2.8, "speed": 58,
              "range": 400, "auto": False, "sound": "rocket", "recoil": 3.2, "reserve": 16,
              "gravity_scale": 1.3, "self_damage": 0.3, "knockback": 14,
              "cluster": {"count": 6, "damage": 26, "radius": 5.5, "speed": 18,
                          "projectile": "bomblet"}},
             [["+", "The shell bursts into 6 bomblets that each blow for 26 in a 5.5 stud "
                    "radius"],
              ["+", "Perfect for clearing a roof or a doorway"],
              ["-", "The shell itself only blows for 28"],
              ["-", "A high, slow lob: hard to hit anything that is moving"]],
             rarity="legendary",
             proj=lambda: [place("rocket", [0, 0, 0], [0.5, 0.9, 0.5], "#2f6fd6",
                                 decal="party", wrap=True)])
def _():
    return [
        part("cyl", [0, 0.10, 0.60], [0.56, 1.40, 0.56], "#2f6fd6", [PI / 2, 0, 0],
             decal="party", wrap=True),
        part("torus", [0, 0.10, 1.30], [0.60, 0.10, 0.60], "#f2c230", [PI / 2, 0, 0], m="metal"),
        part("cyl", [0, 0.10, 1.31], [0.44, 0.03, 0.44], "#1d1e22", [PI / 2, 0, 0]),
        part("rbox", [0, -0.28, 0.10], [0.20, 0.40, 0.26], "#3a3e46", [0.3, 0, 0], m="metal"),
        part("rbox", [0, -0.10, -0.40], [0.30, 0.30, 0.60], "#3a3e46", m="metal",
             decal="rivets", wrap=True),
        place("tri", [0.30, 0.10, 0.20], [0.22, 0.26, 0.2], "#f5c518", r=[0, PI / 2, 0]),
        place("tri", [-0.30, 0.10, 0.20], [0.22, 0.26, 0.2], "#f5c518", r=[0, PI / 2, 0]),
    ]


@NY24.weapon("sparkler_sword", "Sparkler Sword",
             "A sparkler the length of a sword. While it is lit it cuts and burns; it "
             "burns down while you hold it and relights while it is away.",
             {"kind": "melee", "damage": 30, "headshot": 1.2, "rpm": 96, "range": 10.5,
              "arc": 0.6, "sound": "sword", "knockback": 9,
              "fuse_meter": {"secs": 18.0, "recharge": 9.0, "bonus": 0.6,
                             "burn": [8, 3.0], "label": "Fuse"},
              },
             [["+", "While the fuse burns: +60% damage and sets the target burning (8 a "
                    "second for 3 seconds)"],
              ["-", "The fuse burns down in 18 seconds while you hold it"],
              ["-", "Burnt out, it is a 30-damage stick until it relights"],
              ["=", "Relights while it is put away, fully in 9 seconds"]],
             rarity="legendary")
def _():
    return [
        part("cyl", [0, 0, 1.30], [0.06, 2.40, 0.06], "#8a8f99", [PI / 2, 0, 0], m="metal"),
        part("cyl", [0, 0, 1.70], [0.14, 1.60, 0.14], "#5a5e66", [PI / 2, 0, 0],
             decal="rivets", wrap=True),
        place("sparkle", [0, 0, 2.55], 0.6, "#fff6c9", m="neon"),
        part("sph", [0, 0, 2.55], [0.22, 0.22, 0.22], "#ffcf3a", m="neon"),
        part("rbox", [0, 0, 0.12], [0.50, 0.10, 0.12], "#f2c230", m="metal"),
        part("cyl", [0, 0, -0.20], [0.16, 0.50, 0.16], "#c4281c", [PI / 2, 0, 0],
             decal="leather", wrap=True),
    ]


@NY24.gear("bottle_rocket", "Bottle Rocket",
           "Hold on tight and light it. Straight up, about forty feet, and then you "
           "are on your own.",
           {"kind": "ability", "cooldown": 18, "sound": "rocket",
            "ability": {"launch": {"up": 72, "forward": 18}}},
           [["+", "Launches you straight up and a little forward"],
            ["+", "No damage to you, landing included"],
            ["-", "18 second cooldown"]])
def _():
    return [
        place("rocket", [0, 0.0, 0.10], [0.36, 1.20, 0.36], "#c4281c", anchor=[0, 0, 0],
              r=[PI / 2, 0, 0], decal="party", wrap=True),
        part("cyl", [0, 0.0, -0.40], [0.04, 1.00, 0.04], "#c8a070", [PI / 2, 0, 0]),
        place("tri", [0.10, 0, 0.20], [0.16, 0.22, 0.2], "#f5c518", r=[PI / 2, PI / 2, 0]),
    ]


NY24.effect("sky_bloom", name="Sky Bloom", rate=2.4, life=[1.0, 1.4], size=[0.70, 1.05],
            grow=0.6, gravity=0.0, spread=0.2, rise=[0.3, 0.8], blend="add", spin=0.8,
            colors=["#ffffff", "#ffcf3a", "#ff3b4e", "#5a1a8a"], shape="firework",
            radius=0.5)
NY24.effect("rocket_trail", name="Rocket Trail", rate=16.0, life=[0.7, 1.1],
            size=[0.14, 0.28], grow=-0.2, gravity=0.6, spread=0.2, rise=[1.6, 2.6],
            blend="add", spin=3.0, colors=["#fff6c9", "#ffcf3a", "#ff8c1a", "#5a1a04"],
            shape="spark", radius=0.65, orbit=3.2)
NY24.opening(
    sky={"top": "#03050f", "horizon": "#1a1430", "sun": [0.3, 0.9, 0.5], "clouds": 0,
         "tint": "#ffd0b0"},
    ambient="#6a5a7a", beam="#ffcf3a", seep="rocket_trail", after="sky_bloom",
    burst=["#ff3b4e", "#ffcf3a", "#3cc8ff", "#ffffff"],
    pieces=[{"shape": "firework", "colors": ["#ff3b4e", "#ffcf3a", "#3cc8ff"], "blend": "add"},
            {"shape": "spark", "colors": ["#fff6c9", "#ffcf3a"], "blend": "add"},
            {"shape": "star", "colors": ["#ff4fd8", "#7dff9a"], "blend": "add"}],
    backdrop="fireworks", title_wait="Lighting the fuse...", title_shake="Stand back...")
NY24.award("Rocket Rally", ["Spark", "Fuse Lighter", "Pyro", "Rocketeer",
                            "Grand Finale", "Sky Bloomer"],
           "Opened Launch Crates during the Rocket Rally, New Year 2024.",
           "em_firework", "clock")
NY24.bundle("pair", "Launch Pair", 1, 1050, "One Launch Crate, one Fuse Key.")
NY24.bundle("finale", "Grand Finale", 3, 3000, "Three crates, three keys. Saves 300.")


# ============================================================ 2025
NY25 = Event(
    "newyear_2025", "newyear", 2025, "ny25",
    name="Neon Midnight", title="Neon Midnight",
    blurb="For 2025 the server went retro: a synthwave sky, a grid to the horizon, a "
          "disco ball the size of a car and a cassette deck playing the same "
          "countdown mix on repeat until February.",
    tagline="Rewind the tape. Press play. Hit midnight.",
    starts="2024-12-31", ends="2025-01-15",
    colors={"accent": "#ff2bd6", "deep": "#0d0221", "glow": "#19f0ff"},
    family_effects=["circuitry", "static_charge", "void_mist"],
    hero_effect="laser_show", stencil="stencil_ny25")


@NY25.crate_model("Retro Arcade Crate",
                  "A black crate wrapped in a neon grid, chrome at the corners, a disco "
                  "ball on the lid and a cassette for a lock. Holds the Neon Midnight "
                  "set. Needs a Cassette Key.", hinge=[0, 0.50, -0.56],
                  keyhole=[0, -0.05, 0.62])
def _():
    black, pink, cyan = "#0d0221", "#ff2bd6", "#19f0ff"
    parts = [
        part("rbox", [0, 0.0, 0], [1.64, 1.00, 1.10], black, decal="neongrid", wrap=True),
        part("rbox", [0, 0.64, 0], [1.70, 0.28, 1.16], "#160632", decal="neongrid", wrap=True,
             lid=1),
        # neon tubes along the edges
        part("rbox", [0, 0.49, 0.56], [1.66, 0.04, 0.04], pink, m="neon"),
        part("rbox", [0, -0.49, 0.56], [1.66, 0.04, 0.04], cyan, m="neon"),
        part("rbox", [0.82, 0, 0.56], [0.04, 1.0, 0.04], pink, m="neon"),
        part("rbox", [-0.82, 0, 0.56], [0.04, 1.0, 0.04], pink, m="neon"),
        part("rbox", [0, 0.78, 0.58], [1.72, 0.04, 0.04], cyan, m="neon", lid=1),
        part("box", [0, 0.0, -0.562], [0.96, 0.58, 0.02], "#000000", [0, PI, 0],
             decal="stencil_ny25", a=-1),
        part("box", [0.832, 0.0, 0], [0.02, 0.56, 0.80], "#000000", [0, PI / 2, 0],
             decal="stencil_ny25", a=-1),
        part("box", [-0.832, 0.0, 0], [0.02, 0.56, 0.80], "#000000", [0, -PI / 2, 0],
             decal="stencil_ny25", a=-1),
        # the lock: a cassette tape with its spools
        part("rbox", [0, -0.05, 0.575], [0.56, 0.36, 0.07], "#2a2a33", lock=1),
        part("rbox", [0, -0.02, 0.61], [0.44, 0.16, 0.02], "#e8e4f0", decal="cassette"),
        part("cyl", [-0.12, -0.02, 0.62], [0.10, 0.03, 0.10], "#1a1a1a", [PI / 2, 0, 0]),
        part("cyl", [0.12, -0.02, 0.62], [0.10, 0.03, 0.10], "#1a1a1a", [PI / 2, 0, 0]),
        part("box", [0, 0.48, 0], [1.50, 0.04, 0.96], pink, m="neon"),
        # the disco ball on the lid
        part("cyl", [0, 0.86, 0], [0.04, 0.16, 0.04], SILVER, m="metal", lid=1),
        part("sph", [0, 1.14, 0], [0.52, 0.52, 0.52], "#d8dde6", m="metal", decal="mirror",
             wrap=True, lid=1, spin=1.0),
    ]
    for x in (-0.80, 0.80):
        for zz in (-0.53, 0.53):
            for yy, lid in ((-0.46, 0), (0.74, 1)):
                parts.append(part("rbox", [x, yy, zz], [0.14, 0.14, 0.14], SILVER,
                                  m="metal", lid=lid or None))
    return parts


@NY25.key_model("Cassette Key",
                "A chrome key with a tiny cassette for a bow and a ribbon of tape for a "
                "bit. Plays one Retro Arcade Crate open, then the tape snaps.",
                shoulder=-0.26)
def _():
    return [
        part("rbox", [-0.64, 0, 0], [0.62, 0.40, 0.10], "#2a2a33"),
        part("rbox", [-0.64, 0.03, 0.055], [0.48, 0.18, 0.02], "#e8e4f0", decal="cassette"),
        part("cyl", [-0.76, 0.03, 0.06], [0.10, 0.03, 0.10], "#1a1a1a", [PI / 2, 0, 0]),
        part("cyl", [-0.52, 0.03, 0.06], [0.10, 0.03, 0.10], "#1a1a1a", [PI / 2, 0, 0]),
        part("rbox", [-0.64, 0, 0], [0.66, 0.44, 0.04], "#ff2bd6", m="neon", a=0.6),
        part("cyl", [0.10, 0, 0], [0.10, 1.04, 0.10], SILVER, [0, 0, PI / 2], m="metal"),
        part("torus", [-0.30, 0, 0], [0.20, 0.08, 0.20], "#19f0ff", [0, 0, PI / 2], m="neon"),
        part("rbox", [0.50, -0.12, 0], [0.30, 0.16, 0.03], "#2a1a12"),
        part("rbox", [0.38, -0.08, 0], [0.08, 0.14, 0.06], SILVER, m="metal"),
        part("rbox", [0.60, -0.10, 0], [0.08, 0.18, 0.06], SILVER, m="metal"),
    ]


@NY25.hat("synth_visor", "Synthwave Visor",
          "A wraparound visor with a sunset sliding down the glass. The horizon is "
          "always a grid.", "rare")
def _():
    return [
        band(-0.40, 0.30, "#160632", grow=0.04),
        part("rbox", [0, -0.44, 0.74], [1.52, 0.30, 0.10], "#ff2bd6", m="glass", a=0.78,
             decal="sunset_grid"),
        part("rbox", [0, -0.28, 0.78], [1.56, 0.05, 0.06], "#19f0ff", m="neon"),
        part("rbox", [0, -0.60, 0.78], [1.56, 0.05, 0.06], "#ff2bd6", m="neon"),
        part("rbox", [0.80, -0.44, 0.30], [0.08, 0.30, 0.60], "#160632"),
        part("rbox", [-0.80, -0.44, 0.30], [0.08, 0.30, 0.60], "#160632"),
    ]


@NY25.hat("disco_ball", "Disco Ball Head",
          "A mirrorball where your head should be, turning slowly and throwing light "
          "at everyone. Very hard to have a serious conversation in.", "legendary",
          hair="hide")
def _():
    return [
        part("sph", [0, -0.62, 0], [2.10, 2.10, 2.10], "#d8dde6", m="metal",
             decal="mirror", wrap=True, spin=0.8),
        part("cyl", [0, 0.50, 0], [0.10, 0.20, 0.10], SILVER, m="metal"),
        part("torus", [0, 0.64, 0], [0.24, 0.06, 0.24], SILVER, [PI / 2, 0, 0], m="metal"),
        place("sparkle", [0.62, 0.20, 0.62], 0.30, "#ffffff", m="neon"),
        place("sparkle", [-0.80, -0.30, 0.50], 0.24, "#19f0ff", m="neon"),
    ]


@NY25.hat("cassette_phones", "Cassette Headphones",
          "Foam headphones with a cassette deck in each ear cup. Auto-reverse, "
          "naturally.", "uncommon", hair="flat")
def _():
    parts = [place("arch", [0, -0.48, 0], [1.70, 1.16, 1.6], "#2a2a33", anchor=[0, 0, 0]),
             part("rbox", [0, 0.11, 0], [0.62, 0.08, 0.20], "#ff2bd6", m="neon")]
    for side in (1, -1):
        parts += [
            part("rbox", [0.86 * side, -0.38, 0], [0.08, 0.30, 0.10], SILVER, m="metal"),
            part("rbox", [0.90 * side, -0.66, 0.02], [0.24, 0.60, 0.80], "#2a2a33"),
            part("rbox", [0.76 * side, -0.66, 0.02], [0.10, 0.54, 0.72], "#ff8c1a",
                 decal="fur", wrap=True),
            part("rbox", [1.03 * side, -0.66, 0.02], [0.02, 0.36, 0.58], "#e8e4f0",
                 [0, PI / 2 * side, 0], decal="cassette"),
        ]
    return parts


@NY25.hat("laser_mohawk", "Laser Mohawk",
          "Seven blades of light standing up along a black band. It hums. It is "
          "definitely not regulation.", "rare")
def _():
    parts = [part("rbox", [0, 0.01, -0.02], [0.36, 0.08, 1.36], "#160632"),
             band(-0.28, 0.14, "#160632")]
    colours = ["#ff2bd6", "#b26bff", "#19f0ff", "#19f0ff", "#b26bff", "#ff2bd6", "#ff2bd6"]
    for k, c in enumerate(colours):
        z = 0.60 - k * 0.20
        h = 0.55 + 0.45 * math.sin(PI * (k + 0.5) / len(colours))
        parts.append(place("blade", [0, 0.03, z], [h * 1.2, h, 1.0], c, anchor=[-0.5, -0.1, 0],
                           r=[0, PI / 2, PI / 2 - 0.20 + k * 0.05], m="neon", a=0.85))
    return parts


@NY25.hat("neon_halo", "Neon Triangle",
          "A triangle of neon tube hovering over your head, flickering on the beat.",
          "uncommon", hair="show")
def _():
    parts = []
    pts = [(0.0, 0.62), (0.54, -0.31), (-0.54, -0.31)]
    for i in range(3):
        a, b = pts[i], pts[(i + 1) % 3]
        mx, mz = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        length = math.hypot(b[0] - a[0], b[1] - a[1])
        yaw = math.atan2(b[0] - a[0], b[1] - a[1])
        parts.append(part("cyl", [mx, 0.58, mz], [0.07, length, 0.07],
                          ["#ff2bd6", "#19f0ff", "#b26bff"][i], [PI / 2, yaw, 0], m="neon",
                          spin=0.6))
    return parts


@NY25.hat("vinyl_fedora", "Vinyl Fedora",
          "A fedora whose brim is a 12-inch record. It plays when it spins, and it "
          "only spins when you do.", "rare")
def _():
    return [
        part("cyl", [0, -0.02, 0], [2.30, 0.04, 2.30], "#141018", decal="vinyl"),
        part("cyl", [0, 0.01, 0], [0.70, 0.02, 0.70], "#ff2bd6"),
        dome(-0.06, 0.86, "#2a2a33", decal="felt", wrap=True),
        part("rbox", [0, 0.58, 0.0], [0.18, 0.10, 0.80], "#1d1d24", [0.10, 0, 0]),
        ringband(0.10, 0.18, "#19f0ff", m="neon"),
    ]


@NY25.hat("pixel_crown", "8-Bit Crown",
          "A crown built out of glowing pixels, one cube at a time. It renders at "
          "exactly thirty frames a second, out of respect.", "legendary")
def _():
    parts = []
    colours = ["#ff2bd6", "#19f0ff", "#ffcf3a", "#b26bff"]
    for k in range(16):
        a = k * TAU / 16
        x, z = math.sin(a) * 0.86, math.cos(a) * 0.84
        parts.append(part("box", [x, -0.12, z], [0.30, 0.24, 0.30], "#ffcf3a", [0, a, 0],
                          m="neon" if k % 4 == 0 else ""))
        if k % 2 == 0:
            parts.append(part("box", [x, 0.12, z], [0.24, 0.24, 0.24], colours[(k // 2) % 4],
                              [0, a, 0], m="neon"))
            parts.append(part("box", [x, 0.34, z], [0.16, 0.18, 0.16], "#ffcf3a", [0, a, 0]))
    parts.append(cap(-0.20, 0.2, "#160632", decal="felt", wrap=True))
    return parts


@NY25.back("keytar", "Keytar",
           "A white keytar slung across the back on a neon strap. Plays one riff. It "
           "is a good riff.", "rare")
def _():
    return [
        part("rbox", [0, 0.05, -0.30], [1.60, 0.50, 0.12], "#f2f3f3", [0, 0, -0.35]),
        part("rbox", [0.10, 0.10, -0.38], [1.10, 0.26, 0.04], "#ffffff", [0, 0, -0.35],
             decal="keys"),
        part("rbox", [-0.72, 0.38, -0.30], [0.60, 0.18, 0.12], "#2a2a33", [0, 0, -0.35]),
        part("rbox", [-0.92, 0.48, -0.36], [0.10, 0.10, 0.04], "#ff2bd6", m="neon"),
        part("rbox", [0.40, 0.30, -0.10], [0.10, 1.40, 0.06], "#19f0ff", [0, 0, 0.6], m="neon"),
    ]


@NY25.back("neon_wings", "Neon Wings",
           "Two wings drawn in light: just the outlines, glowing pink and cyan. They "
           "cast a colour on everything behind you.", "legendary")
def _():
    parts = []
    for side in (1, -1):
        for k, (c, scale, lift) in enumerate((("#ff2bd6", 2.2, 0.40), ("#19f0ff", 1.7, 0.26))):
            parts.append(place("wing", [0.18 * side, 0.55 - k * 0.08, -0.42 - k * 0.04], scale, c,
                               anchor=[-0.5, 0, 0], r=[0, 0.30 if side > 0 else PI - 0.30, lift],
                               m="neon", a=0.55))
    parts.append(part("rbox", [0, 0.50, -0.30], [0.30, 0.36, 0.16], "#2a2a33", m="metal"))
    return parts


@NY25.hairdo("neon_sideshave", "Neon Side Shave",
             "Shaved on one side, a long hot-pink sweep on the other, glowing at the "
             "tips.", "rare")
def _():
    c, tip = "#ff2bd6", "#19f0ff"
    parts = [place("hairshort", [0, 0, 0], [1.0, 1.0, 1.0], "#2a1030", anchor=[0, 0, 0],
                   decal="strands", wrap=True)]
    parts.append(place("teardrop", [0.12, 0.50, 0.06], [0.70, 1.20, 0.60], c,
                       anchor=[0, 0.2, 0], r=[0.15, 0, -PI / 2 + 0.35], decal="strands", wrap=True))
    for k, (y, length, tilt) in enumerate(((0.36, 0.95, -0.25), (0.28, 0.85, -0.40),
                                           (0.44, 0.70, -0.10))):
        parts.append(place("leaf", [0.14, y, 0.53], [0.65, length, 3.0], c if k else tip,
                           r=[0, 0, PI / 2 + tilt]))
    parts.append(place("teardrop", [-0.40, 0.40, 0.06], [0.18, 0.26, 0.18], tip,
                       anchor=[0, 0, 0], r=[0, 0, 1.4], m="neon"))
    return parts


@NY25.hairdo("retro_perm", "Retro Perm",
             "Permed, teased and sprayed to twice its natural size. Peak 1985.", "uncommon")
def _():
    c = "#c88a3a"
    parts = [place("hairmid", [0, 0, 0], [1.02, 1.02, 1.02], c, anchor=[0, 0, 0],
                   decal="strands", wrap=True)]
    for ring, (y, radius, count) in enumerate(((0.62, 0.28, 6), (0.46, 0.50, 10),
                                               (0.20, 0.60, 12), (-0.10, 0.60, 10))):
        for n in range(count):
            a = TAU * n / count + ring * 0.3
            z = math.cos(a) * radius * 0.94 - 0.06
            if ring >= 2 and z > 0.28:
                continue
            parts.append(part("sph", [math.sin(a) * radius, y, z], [0.30, 0.28, 0.30],
                              shade(c, 0.9 + (n % 3) * 0.1), decal="fur", wrap=True))
    parts.append(part("rbox", [0, 0.36, 0.40], [0.95, 0.10, 0.12], "#ff2bd6"))
    return parts


NY25.face("pixel_smile", "Pixel Smile",
          "A smiley face rendered at eight bits per colour channel, most of them pink.", [
              {"k": "rect", "x": -0.22, "y": -0.16, "w": 0.10, "h": 0.10, "c": "#ff2bd6"},
              {"k": "rect", "x": 0.22, "y": -0.16, "w": 0.10, "h": 0.10, "c": "#ff2bd6"},
              {"k": "rect", "x": -0.24, "y": 0.10, "w": 0.08, "h": 0.08, "c": "#19f0ff"},
              {"k": "rect", "x": 0.24, "y": 0.10, "w": 0.08, "h": 0.08, "c": "#19f0ff"},
              {"k": "rect", "x": -0.16, "y": 0.18, "w": 0.08, "h": 0.08, "c": "#19f0ff"},
              {"k": "rect", "x": 0.16, "y": 0.18, "w": 0.08, "h": 0.08, "c": "#19f0ff"},
              {"k": "rect", "x": 0.0, "y": 0.22, "w": 0.24, "h": 0.08, "c": "#19f0ff"},
          ], "rare")
NY25.face("laser_eyes", "Laser Eyes",
          "Two red laser bars where the eyes go, and a smile that is entirely too "
          "calm about it.", [
              {"k": "rect", "x": -0.22, "y": -0.16, "w": 0.22, "h": 0.06, "c": "#ff1b3a"},
              {"k": "rect", "x": 0.22, "y": -0.16, "w": 0.22, "h": 0.06, "c": "#ff1b3a"},
              {"k": "rect", "x": -0.22, "y": -0.16, "w": 0.16, "h": 0.02, "c": "#ffd0d6"},
              {"k": "rect", "x": 0.22, "y": -0.16, "w": 0.16, "h": 0.02, "c": "#ffd0d6"},
              {"k": "arc", "x": 0, "y": 0.06, "r": 0.24, "a0": 0.12, "a1": 0.38,
               "w": 0.05, "c": "#1a1a1a"},
          ])
NY25.shirt("synth_jacket", "Synth Jacket",
           "A black bomber jacket with a neon grid across it and the sleeves pushed up.",
           {"torso": "#160632", "arms": "#160632", "sleeves": 0.7, "weave": "neongrid",
            "stripe": "#ff2bd6"}, "rare")
NY25.pants("glow_leggings", "Glow Leggings",
           "Deep purple leggings with a cyan stripe that glows in the dark.",
           {"legs": "#2a0a4a", "stripe": "#19f0ff", "glow": True})


@NY25.weapon("disco_grenade", "Disco Ball Grenade",
              "Throw it and it hangs in the air, turning, firing lasers at every enemy "
              "who comes within reach, until the song ends.",
              {"kind": "deploy", "cooldown": 22, "sound": "throw",
               "deploy": {"type": "turret", "thrown": True, "secs": 7.0, "hp": 60,
                          "range": 22.0, "rpm": 300, "damage": 7, "float": 3.0,
                          "tracer": "#ff2bd6", "limit": 1}},
              [["+", "Hangs in the air for 7 seconds firing lasers at enemies within 22 "
                     "studs"],
               ["+", "Five lasers a second"],
               ["-", "22 second cooldown"],
               ["-", "Can be shot down (60 health)"]], rarity="legendary",
              deploy=lambda: [part("sph", [0, 0, 0], [1.2, 1.2, 1.2], "#d8dde6", m="metal",
                                   decal="mirror", wrap=True, spin=2.0),
                              part("cyl", [0, 0.68, 0], [0.06, 0.24, 0.06], SILVER, m="metal")])
def _():
    return [
        part("sph", [0, 0.0, 0.30], [0.62, 0.62, 0.62], "#d8dde6", m="metal", decal="mirror",
             wrap=True),
        part("cyl", [0, 0.36, 0.30], [0.06, 0.14, 0.06], SILVER, m="metal"),
        part("torus", [0, 0.44, 0.30], [0.14, 0.04, 0.14], SILVER, [PI / 2, 0, 0], m="metal"),
    ]


@NY25.weapon("synth_laser", "Synth Laser",
             "A keytar that fires a continuous beam. Hold it on one target and it climbs "
             "the scale -- until it overheats.",
             {"kind": "beam", "damage": 6, "headshot": 1.0, "rpm": 600, "mag": 0,
              "range": 90, "auto": True, "sound": "laser", "recoil": 0.1, "spread": 0.2,
              "beam": "#ff2bd6",
              "ramp": {"per_sec": 0.9, "max": 2.5},
              "heat": {"per_shot": 0.012, "cool": 0.35, "lock": 2.5, "label": "Heat"}},
             [["+", "A continuous beam, no ammunition"],
              ["+", "Damage climbs while it stays on the same target: up to 2.5x after a "
                    "second and a half"],
              ["-", "Overheats: locks up for 2.5 seconds when the gauge fills"],
              ["-", "90 stud reach"]], rarity="legendary")
def _():
    return [
        part("rbox", [0, 0.0, 0.50], [0.30, 0.30, 1.60], "#f2f3f3", [0, 0, 0]),
        part("rbox", [0.16, 0.0, 0.60], [0.02, 0.22, 1.20], "#ffffff", [0, 0, 0], decal="keys"),
        part("rbox", [0, 0.0, 1.40], [0.34, 0.14, 0.40], "#2a2a33"),
        part("cyl", [0, 0, 1.66], [0.10, 0.20, 0.10], "#ff2bd6", [PI / 2, 0, 0], m="neon"),
        part("rbox", [0, -0.30, 0.10], [0.16, 0.40, 0.20], "#2a2a33", [0.3, 0, 0]),
        part("rbox", [-0.16, 0.0, 0.50], [0.02, 0.06, 1.50], "#19f0ff", m="neon"),
    ]


@NY25.weapon("vinyl_disc", "Vinyl Disc Thrower",
             "Flings a 12-inch record like a frisbee. It cuts through everyone in its "
             "path, and then it comes back and does it again.",
             {"kind": "projectile", "projectile": "vinyl", "damage": 34, "splash": 0,
              "splash_damage": 0, "rpm": 75, "mag": 1, "reload": 0.1, "speed": 64,
              "range": 46, "auto": False, "sound": "throw", "recoil": 0.8, "reserve": 99,
              "gravity_scale": 0.0, "self_damage": 0.0, "knockback": 6,
              "boomerang": {"out": 46, "pierce": True}},
             [["+", "Passes through everyone it meets, out and back"],
              ["+", "Every pass hits: 34 damage going, 34 coming back"],
              ["-", "You cannot throw another until it is back in your hand"],
              ["-", "Flies 46 studs at most"]], rarity="legendary",
             proj=lambda: [part("cyl", [0, 0, 0], [1.20, 0.05, 1.20], "#141018",
                                decal="vinyl", spin=14.0),
                           part("cyl", [0, 0, 0], [0.36, 0.07, 0.36], "#ff2bd6", spin=14.0)])
def _():
    return [
        part("cyl", [0, 0.0, 0.70], [1.10, 0.05, 1.10], "#141018", [PI / 2, 0, 0], decal="vinyl"),
        part("cyl", [0, 0.0, 0.70], [0.34, 0.07, 0.34], "#ff2bd6", [PI / 2, 0, 0]),
        part("rbox", [0, 0.0, 0.0], [0.24, 0.20, 0.30], "#2a2a33"),
    ]


@NY25.gear("glowstick", "Glow Stick Bundle",
           "Crack the bundle and drop it: a pool of green light that patches up every "
           "teammate standing in it.",
           {"kind": "deploy", "cooldown": 28, "sound": "crack",
            "deploy": {"type": "zone", "zone": "heal", "radius": 9.0, "secs": 8.0,
                       "heal": 5.0, "color": "#7dff9a", "limit": 1}},
           [["+", "Drops a 9 stud pool that heals teammates 5 a second for 8 seconds"],
            ["-", "28 second cooldown"],
            ["=", "Heals you as well"]],
           deploy=lambda: [part("cyl", [0, 0.1, 0], [0.12, 0.9, 0.12], "#7dff9a", [0, 0, 1.4],
                                m="neon"),
                           part("cyl", [0.1, 0.1, 0.1], [0.12, 0.9, 0.12], "#ff2bd6", [0.8, 0, 1.4],
                                m="neon"),
                           part("cyl", [-0.1, 0.1, -0.1], [0.12, 0.9, 0.12], "#19f0ff",
                                [-0.8, 0, 1.4], m="neon")])
def _():
    return [
        part("cyl", [0.06, 0.0, 0.40], [0.10, 0.90, 0.10], "#7dff9a", [PI / 2, 0, 0.1], m="neon"),
        part("cyl", [-0.06, 0.04, 0.40], [0.10, 0.90, 0.10], "#ff2bd6", [PI / 2, 0, -0.1],
             m="neon"),
        part("cyl", [0.0, -0.06, 0.40], [0.10, 0.90, 0.10], "#19f0ff", [PI / 2, 0, 0], m="neon"),
        part("torus", [0, 0, 0.20], [0.30, 0.04, 0.30], "#2a2a33", [PI / 2, 0, 0]),
    ]


NY25.effect("laser_show", name="Laser Show", rate=10.0, life=[0.6, 1.0], size=[0.40, 0.70],
            grow=0.2, gravity=0.0, spread=0.1, rise=[0.1, 0.4], blend="add", spin=0.0,
            colors=["#ffffff", "#ff2bd6", "#19f0ff", "#4a0a6a"], shape="ray", radius=0.7,
            orbit=2.6)
NY25.effect("disco_fever", name="Disco Fever", rate=8.0, life=[1.2, 1.8], size=[0.16, 0.28],
            grow=0.0, gravity=0.0, spread=0.3, rise=[0.1, 0.4], blend="add", spin=4.0,
            colors=["#ffffff", "#19f0ff", "#ff2bd6", "#ffcf3a"], shape="sequin", radius=0.9,
            orbit=1.8)
NY25.opening(
    sky={"top": "#07011a", "horizon": "#5a0a6a", "sun": [0.0, 0.2, 1.0], "clouds": 0,
         "tint": "#ff9ae8"},
    ambient="#7a4a9a", beam="#ff2bd6", seep="laser_show", after="disco_fever",
    burst=["#ff2bd6", "#19f0ff", "#ffcf3a", "#ffffff"],
    pieces=[{"shape": "sequin", "colors": ["#ffffff", "#19f0ff", "#ff2bd6"], "blend": "add"},
            {"shape": "note", "colors": ["#ff2bd6", "#19f0ff"], "blend": "add"},
            {"shape": "star", "colors": ["#ffcf3a", "#ffffff"], "blend": "add"}],
    backdrop="synthwave", title_wait="Rewinding the tape...", title_shake="Press play...")
NY25.award("Neon Midnight", ["Arcade Kid", "High Scorer", "Synth Pilot", "Mix Master",
                             "Neon Legend", "Midnight Rider"],
           "Opened Retro Arcade Crates during Neon Midnight, New Year 2025.",
           "em_cassette", "clock")
NY25.bundle("pair", "Side A", 1, 1050, "One Retro Arcade Crate, one Cassette Key.")
NY25.bundle("mixtape", "Mixtape", 3, 3000, "Three crates, three keys. Saves 300.")


# ============================================================ 2026
NY26 = Event(
    "newyear_2026", "newyear", 2026, "ny26",
    name="Crystal Countdown", title="The Crystal Countdown",
    blurb="A ball of ten thousand crystals came down a pole on the roof of the "
          "Relay at midnight, and the whole server watched it fall. The fifth New "
          "Year, and the shiniest by a distance.",
    tagline="Ten thousand crystals. One second to midnight.",
    starts="2025-12-31", ends="2026-01-15",
    colors={"accent": "#9fd8ff", "deep": "#0b1830", "glow": "#e8f8ff"},
    family_effects=["frostbite", "starstruck", "sunbeam"],
    hero_effect="crystal_shower", stencil="stencil_ny26")


@NY26.crate_model("Ball Drop Crate",
                  "Frosted glass panels in a silver frame, lit from the edges, with a "
                  "crystal ball on a pole above the lid. Holds the Crystal Countdown set. "
                  "Needs a Crystal Key.", hinge=[0, 0.50, -0.56], keyhole=[0, -0.05, 0.66])
def _():
    frame, glass = "#c9d6e6", "#dff2ff"
    parts = [
        part("rbox", [0, 0.0, 0], [1.56, 0.94, 1.04], "#9fc4e6", m="glass", a=0.82,
             decal="frost", wrap=True),
        part("rbox", [0, 0.0, 0], [1.44, 0.82, 0.92], "#e8f8ff", m="neon", a=0.5),
        part("rbox", [0, 0.64, 0], [1.70, 0.26, 1.16], frame, m="metal", lid=1),
        part("box", [0, 0.0, -0.53], [0.90, 0.52, 0.02], "#000000", [0, PI, 0],
             decal="stencil_ny26", a=-1),
        # the silver frame
    ]
    for x in (-0.80, 0.80):
        for zz in (-0.54, 0.54):
            parts.append(part("rbox", [x, 0.0, zz], [0.10, 1.04, 0.10], frame, m="metal"))
    for y in (-0.49, 0.47):
        parts += [part("rbox", [0, y, 0.54], [1.66, 0.08, 0.10], frame, m="metal"),
                  part("rbox", [0, y, -0.54], [1.66, 0.08, 0.10], frame, m="metal"),
                  part("rbox", [0.80, y, 0], [0.10, 0.08, 1.14], frame, m="metal"),
                  part("rbox", [-0.80, y, 0], [0.10, 0.08, 1.14], frame, m="metal")]
    parts += [
        # the lock: a faceted crystal set in a silver bezel
        part("cyl", [0, -0.05, 0.56], [0.36, 0.06, 0.36], frame, [PI / 2, 0, 0], m="metal",
             lock=1),
        place("gem", [0, -0.05, 0.60], [0.26, 0.26, 0.26], "#bfe9ff", anchor=[0, 0.36, 0],
              r=[PI / 2, 0, 0], m="glass"),
        part("box", [0, 0.48, 0], [1.50, 0.04, 0.96], "#e8f8ff", m="neon"),
        # the pole and the ball
        part("cyl", [0, 1.00, 0], [0.06, 0.56, 0.06], frame, m="metal", lid=1),
        place("gem", [0, 1.30, 0], [0.62, 0.62, 0.62], "#dff2ff", m="glass", lid=1, spin=0.6),
        place("gem", [0, 1.30, 0], [0.62, 0.62, 0.62], "#9fd8ff", r=[PI, 0, 0], m="glass",
              lid=1, spin=0.6),
        part("sph", [0, 1.30, 0], [0.34, 0.34, 0.34], "#ffffff", m="neon", a=0.5, lid=1),
    ]
    return parts


@NY26.key_model("Crystal Key",
                "Silver, with a faceted crystal for a bow and teeth of clear crystal. "
                "Opens one Ball Drop Crate and shatters into glitter.", shoulder=-0.30)
def _():
    return [
        place("gem", [-0.64, 0, 0], [0.52, 0.52, 0.52], "#dff2ff", anchor=[0, 0.36, 0],
              r=[0, 0, PI / 2], m="glass"),
        place("gem", [-0.64, 0, 0], [0.52, 0.52, 0.52], "#9fd8ff", anchor=[0, 0.36, 0],
              r=[0, 0, -PI / 2], m="glass"),
        part("torus", [-0.64, 0, 0], [0.56, 0.06, 0.56], SILVER, [0, 0, PI / 2], m="metal"),
        part("cyl", [0.10, 0, 0], [0.09, 1.04, 0.09], SILVER, [0, 0, PI / 2], m="metal"),
        part("torus", [-0.30, 0, 0], [0.18, 0.07, 0.18], "#9fd8ff", [0, 0, PI / 2], m="metal"),
        place("icicle", [0.40, -0.14, 0], [0.10, 0.22, 0.10], "#dff2ff", r=[0, 0, 0], m="glass"),
        place("icicle", [0.56, -0.17, 0], [0.12, 0.28, 0.12], "#dff2ff", m="glass"),
        part("sph", [0.62, 0, 0], [0.12, 0.12, 0.12], SILVER, m="metal"),
    ]


@NY26.hat("ball_drop", "Ball Drop Crown",
          "A silver band, a pole and the crystal ball at the top of it, lit from "
          "inside and turning. Ten thousand facets, give or take.", "legendary")
def _():
    return [
        band(-0.20, 0.20, SILVER, grow=0.05, m="metal"),
        cap(-0.24, 0.16, "#1b2c4a", decal="felt", wrap=True),
        part("cyl", [0, 0.42, 0], [0.08, 0.52, 0.08], SILVER, m="metal"),
        part("cyl", [0, 0.20, 0], [0.36, 0.08, 0.36], SILVER, m="metal"),
        place("gem", [0, 1.06, 0], [1.5, 1.5, 1.5], "#dff2ff", m="glass", spin=0.5),
        place("gem", [0, 1.06, 0], [1.5, 1.5, 1.5], "#9fd8ff", r=[PI, 0, 0], m="glass",
              spin=0.5),
        part("sph", [0, 1.06, 0], [0.62, 0.62, 0.62], "#ffffff", m="neon", a=0.55),
        part("torus", [0, 1.06, 0], [1.12, 0.04, 1.12], "#e8f8ff", m="neon", spin=1.2),
    ]


@NY26.hat("silver_bowler", "Silver Bowler",
          "A bowler hat in silver satin with a band of crystal beads. Tips "
          "beautifully.", "uncommon")
def _():
    parts = [
        place("brim", [0, -0.05, 0], [2.10, 1.3, 2.04], "#b8c4d4", anchor=[0, 0, 0], m="metal"),
        dome(-0.05, 0.86, "#c9d6e6", m="metal", decal="felt", wrap=True),
        ringband(0.06, 0.16, "#1b2c4a"),
    ]
    parts += around(14, 0.94, 0.06, lambda a, x, z: part(
        "sph", [x, 0.08, z * 0.97], [0.08, 0.08, 0.08], "#dff2ff", m="glass"))
    return parts


@NY26.hat("countdown_ticker", "Countdown Ticker",
          "A headband with a scrolling LED ticker across the front, still counting "
          "down to a midnight that has already been.", "rare")
def _():
    return [
        band(-0.20, 0.26, "#1b2c4a", grow=0.05),
        part("rbox", [0, 0.02, 0.62], [1.30, 0.38, 0.16], "#0b1220"),
        part("rbox", [0, 0.02, 0.705], [1.16, 0.26, 0.02], "#000000", decal="ticker", m="neon"),
        part("rbox", [0, 0.22, 0.62], [1.34, 0.04, 0.18], SILVER, m="metal"),
        part("rbox", [0, -0.18, 0.62], [1.34, 0.04, 0.18], SILVER, m="metal"),
    ]


@NY26.hat("starlight_wreath", "Starlight Wreath",
          "A wreath of silver stars and crystal beads, worn like a crown. It catches "
          "the light from every direction at once.", "rare")
def _():
    parts = [ringband(-0.16, 0.14, SILVER, m="metal")]

    def piece(a, x, z):
        tilt = [-0.25, a, 0]
        return [place("star", [x, -0.06 + (0.1 if int(round(a / (TAU / 12))) % 2 else 0), z],
                      0.30, "#e8f8ff", r=tilt, m="metal"),
                part("sph", [x * 1.02, 0.12, z * 1.02], [0.09, 0.09, 0.09], "#9fd8ff", m="glass")]
    parts += around(12, 0.94, 0, piece, zscale=0.97)
    return parts


@NY26.hat("hourglass", "Last Hourglass",
          "A silver hourglass balanced on your head with the sand still running. "
          "It runs out at midnight. It always runs out at midnight.", "legendary")
def _():
    frame = SILVER
    return [
        cap(-0.24, 0.1, "#1b2c4a", decal="felt", wrap=True),
        part("cyl", [0, 0.16, 0], [1.00, 0.10, 1.00], frame, m="metal"),
        part("cyl", [0, 1.46, 0], [1.00, 0.10, 1.00], frame, m="metal"),
        place("cask", [0, 0.20, 0], [0.76, 0.62, 0.76], "#e8f8ff", anchor=[0, 0, 0], m="glass",
              a=0.35),
        place("cask", [0, 0.80, 0], [0.76, 0.62, 0.76], "#e8f8ff", anchor=[0, 0, 0], m="glass",
              a=0.35),
        part("cone", [0, 0.40, 0], [0.56, 0.36, 0.56], "#e0c27a"),
        part("cone", [0, 1.02, 0], [0.42, 0.30, 0.42], "#e0c27a", [PI, 0, 0]),
        part("cyl", [0, 0.72, 0], [0.04, 0.36, 0.04], "#e0c27a"),
        part("cyl", [0.44, 0.81, 0], [0.06, 1.30, 0.06], frame, m="metal"),
        part("cyl", [-0.44, 0.81, 0], [0.06, 1.30, 0.06], frame, m="metal"),
        part("cyl", [0, 0.81, 0.44], [0.06, 1.30, 0.06], frame, m="metal"),
    ]


@NY26.hat("prism_visor", "Prism Visor",
          "A visor of cut crystal that splits every light into a rainbow across your "
          "face. Makes reading the scoreboard an adventure.", "uncommon")
def _():
    return [
        band(-0.30, 0.18, SILVER, m="metal", grow=0.03),
        place("visor", [0, -0.26, 0], [1.84, 1.3, 1.84], "#dff2ff", anchor=[0, 0, 0],
              m="glass", a=0.55),
        part("rbox", [0, -0.24, 0.80], [1.0, 0.05, 0.10], "#ff6ad5", m="glass", a=0.6),
        part("rbox", [0, -0.24, 0.87], [0.8, 0.05, 0.08], "#ffd36a", m="glass", a=0.6),
        part("rbox", [0, -0.24, 0.93], [0.6, 0.05, 0.06], "#6ae8ff", m="glass", a=0.6),
    ]


@NY26.hat("crown_2026", "Party Crown 2026",
          "A silver card crown with the year cut out of it and confetti still stuck "
          "to the glue.", "uncommon")
def _():
    parts = [place("spikecrown", [0, -0.30, 0], [1.86, 0.70, 1.80], "#c9d6e6",
                   anchor=[0, 0, 0], m="metal", decal="year2026", wrap=True)]
    colours = ["#9fd8ff", "#ff6ad5", "#ffd36a"]
    for k in range(9):
        a = k * 1.7
        parts.append(part("box", [math.sin(a) * 0.95, -0.10 + (k % 3) * 0.12,
                                  math.cos(a) * 0.93], [0.08, 0.05, 0.02], colours[k % 3],
                          [0, a, k]))
    return parts


@NY26.back("clock_tower", "Crystal Clock Tower",
           "A silver clock tower on your back with a crystal ball up its spire, "
           "striking every hour on the hour.", "legendary")
def _():
    frame = SILVER
    return [
        part("rbox", [0, -0.20, -0.42], [0.80, 1.30, 0.56], "#c9d6e6", m="metal",
             decal="rivets", wrap=True),
        part("rbox", [0, 0.62, -0.42], [0.68, 0.40, 0.48], "#9fb4c8", m="metal"),
        part("disc", [0, 0.62, -0.68], [0.40, 0.40, 0.06], SNOW, [0, PI, 0], decal="clockface"),
        part("cone", [0, 1.12, -0.42], [0.70, 0.62, 0.70], "#1b2c4a"),
        part("cyl", [0, 1.56, -0.42], [0.04, 0.30, 0.04], frame, m="metal"),
        place("gem", [0, 1.78, -0.42], [0.30, 0.30, 0.30], "#dff2ff", m="glass", spin=0.8),
        part("rbox", [0, -0.30, -0.71], [0.30, 0.50, 0.04], "#e8f8ff", m="neon", a=0.6),
        *straps("#2b2b30", 0.34, 0.12),
    ]


@NY26.back("streamer_cape", "Silver Streamer Cape",
           "A cape of silver streamers that fan out when you run and rustle when you "
           "do not.", "rare")
def _():
    parts = [part("rbox", [0, 0.96, -0.12], [1.40, 0.14, 0.18], "#c9d6e6", m="metal")]
    for k in range(9):
        x = -0.60 + k * 0.15
        c = ["#c9d6e6", "#9fd8ff", "#e8f8ff"][k % 3]
        parts.append(place("ribbon", [x, 0.92, -0.26 - abs(x) * 0.08], [0.13, 1.80, 0.05], c,
                           anchor=[0, 0.5, 0], r=[0.12 + abs(x) * 0.05, 0, x * 0.10], m="metal"))
    return parts


@NY26.hairdo("crystal_braids", "Crystal Braids",
             "Two long braids threaded with crystal beads that click when you turn.",
             "rare")
def _():
    c = "#3a2416"
    parts = [place("hairmid", [0, 0, 0], [1.0, 1.0, 1.0], c, anchor=[0, 0, 0],
                   decal="strands", wrap=True),
             part("rbox", [0, 0.545, 0.05], [0.03, 0.02, 0.66], shade(c, 0.6))]
    for side in (1, -1):
        y = -0.05
        for k in range(6):
            parts.append(part("sph", [0.50 * side, y, -0.10], [0.20, 0.22, 0.20],
                              c if k % 2 else shade(c, 1.25), decal="strands", wrap=True))
            if k % 2:
                parts.append(part("sph", [0.50 * side, y - 0.12, -0.10], [0.10, 0.10, 0.10],
                                  "#9fd8ff", m="glass"))
            y -= 0.20
    return parts


@NY26.hairdo("silver_pixie", "Silver Pixie",
             "A short silver pixie cut with a long side fringe. Ice cold, very neat.",
             "uncommon")
def _():
    c, hi = "#c9ced8", "#f2f5fa"
    return [place("hairshort", [0, 0, 0], [1.02, 1.02, 1.02], c, anchor=[0, 0, 0],
                  decal="strands", wrap=True),
            place("leaf", [0.08, 0.32, 0.535], [0.75, 0.86, 2.4], hi, r=[0, 0, PI / 2 - 0.4]),
            place("leaf", [-0.18, 0.36, 0.53], [0.60, 0.60, 2.4], c, r=[0, 0, PI / 2 + 0.3]),
            place("teardrop", [0.0, 0.52, -0.12], [0.50, 0.40, 0.50], hi, anchor=[0, 0, 0],
                  r=[-0.4, 0, 0])]


NY26.face("crystal_gaze", "Crystal Gaze",
          "Diamond eyes that catch the light, and a small, knowing smile.", [
              {"k": "poly", "pts": [[-0.22, -0.26], [-0.14, -0.16], [-0.22, -0.06], [-0.30, -0.16]],
               "c": "#5aa9e6"},
              {"k": "poly", "pts": [[0.22, -0.26], [0.30, -0.16], [0.22, -0.06], [0.14, -0.16]],
               "c": "#5aa9e6"},
              {"k": "poly", "pts": [[-0.22, -0.22], [-0.18, -0.17], [-0.22, -0.12], [-0.26, -0.17]],
               "c": "#e8f8ff"},
              {"k": "poly", "pts": [[0.22, -0.22], [0.26, -0.17], [0.22, -0.12], [0.18, -0.17]],
               "c": "#e8f8ff"},
              {"k": "arc", "x": 0.02, "y": 0.06, "r": 0.18, "a0": 0.10, "a1": 0.36,
               "w": 0.045, "c": "#1a1a1a"},
          ], "rare")
NY26.face("countdown_cheer", "Countdown Cheer",
          "Eyes screwed shut, mouth wide open, yelling 'ONE!' a fraction early.", [
              {"k": "arc", "x": -0.22, "y": -0.12, "r": 0.10, "a0": 0.55, "a1": 0.95,
               "w": 0.05, "c": "#1a1a1a"},
              {"k": "arc", "x": 0.22, "y": -0.12, "r": 0.10, "a0": 0.55, "a1": 0.95,
               "w": 0.05, "c": "#1a1a1a"},
              {"k": "ellipse", "x": 0, "y": 0.16, "w": 0.30, "h": 0.24, "c": "#1a1a1a"},
              {"k": "ellipse", "x": 0, "y": 0.22, "w": 0.18, "h": 0.10, "c": "#e05a6a"},
              {"k": "star", "x": 0.33, "y": -0.26, "r": 0.05, "c": "#5aa9e6", "n": 4},
              {"k": "star", "x": -0.34, "y": -0.24, "r": 0.04, "c": "#5aa9e6", "n": 4},
          ])
NY26.shirt("silver_sequin", "Silver Sequin Jacket",
           "A cropped jacket of silver sequins over a midnight-blue shirt.",
           {"torso": "#c9d6e6", "arms": "#c9d6e6", "weave": "sequins", "stripe": "#1b2c4a"},
           "rare")
NY26.belt("crystal_belt", "Crystal Buckle Belt",
          "A silver belt with a buckle cut from one crystal.",
          {"band": "#c9d6e6", "buckle": "#dff2ff", "metal": True, "glow": True,
           "weave": "leather"})


@NY26.weapon("ball_drop", "Ball Drop",
             "Point at the ground and call it: two seconds later a crystal ball the "
             "size of a car comes down out of the sky on that exact spot.",
             {"kind": "strike", "cooldown": 9, "range": 160, "sound": "chime",
              "strike": {"delay": 2.0, "radius": 9.0, "damage": 130, "knock": 30,
                         "model": "crystalball"}},
             [["+", "Marks a spot up to 160 studs away; 2 seconds later everything within "
                    "9 studs takes 130"],
              ["+", "Everyone can see the shadow coming"],
              ["-", "So can they"],
              ["-", "9 second cooldown"]], rarity="legendary",
             proj=lambda: [place("gem", [0, 0, 0], [4.0, 4.0, 4.0], "#dff2ff", m="glass"),
                           place("gem", [0, 0, 0], [4.0, 4.0, 4.0], "#9fd8ff", r=[PI, 0, 0],
                                 m="glass"),
                           part("sph", [0, 0, 0], [2.2, 2.2, 2.2], "#ffffff", m="neon", a=0.6)])
def _():
    return [
        part("cyl", [0, 0, 0.70], [0.10, 1.80, 0.10], SILVER, [PI / 2, 0, 0], m="metal"),
        place("gem", [0, 0, 1.70], [0.50, 0.50, 0.50], "#dff2ff", r=[PI / 2, 0, 0], m="glass"),
        place("gem", [0, 0, 1.70], [0.50, 0.50, 0.50], "#9fd8ff", r=[-PI / 2, 0, 0], m="glass"),
        part("sph", [0, 0, 1.70], [0.26, 0.26, 0.26], "#ffffff", m="neon", a=0.6),
        part("torus", [0, 0, 1.40], [0.30, 0.05, 0.30], SILVER, [PI / 2, 0, 0], m="metal"),
        part("cyl", [0, 0, -0.10], [0.18, 0.36, 0.18], "#1b2c4a", [PI / 2, 0, 0],
             decal="leather", wrap=True),
    ]


@NY26.weapon("resolution_rifle", "Resolution Rifle",
             "A silver marksman's rifle that rewards keeping your resolution: every hit "
             "in a row adds to the next. One miss and it starts again.",
             {"kind": "hitscan", "damage": 36, "headshot": 2.2, "rpm": 110, "mag": 6,
              "reload": 2.4, "spread": 0.25, "pellets": 1, "range": 500, "auto": False,
              "sound": "rifle", "recoil": 2.2, "reserve": 48, "scope": 2.5,
              "tracer": "#9fd8ff",
              "streak": {"per_hit": 0.10, "max": 0.5, "label": "Resolve"}},
             [["+", "Every hit in a row adds 10% to the next shot, up to +50%"],
              ["+", "Scoped"],
              ["-", "A single miss resets the streak"],
              ["-", "Slower to fire than the Ranger Rifle"]], rarity="legendary")
def _():
    return [
        part("rbox", [0, 0.0, 0.70], [0.20, 0.26, 2.10], "#c9d6e6", m="metal"),
        part("cyl", [0, 0.06, 1.80], [0.09, 1.10, 0.09], "#9fb4c8", [PI / 2, 0, 0], m="metal"),
        part("cyl", [0, 0.30, 0.70], [0.16, 0.80, 0.16], "#1b2c4a", [PI / 2, 0, 0]),
        part("cyl", [0, 0.30, 1.12], [0.16, 0.02, 0.16], "#9fd8ff", [PI / 2, 0, 0], m="glass"),
        place("gem", [0, 0.16, 0.30], [0.14, 0.14, 0.14], "#9fd8ff", m="glass"),
        part("rbox", [0, -0.30, -0.10], [0.20, 0.50, 0.40], "#1b2c4a"),
        part("rbox", [0, -0.24, 0.30], [0.08, 0.20, 0.10], SILVER, m="metal"),
    ]


@NY26.weapon("party_horn", "Party Horn Blunderbuss",
             "A brass blunderbuss with a party horn for a bell. It hardly hurts; it "
             "does blow everyone in front of you clean off their feet.",
             {"kind": "cone", "damage": 14, "rpm": 50, "mag": 4, "reload": 2.4,
              "range": 15.0, "auto": False, "sound": "horn", "recoil": 3.0, "reserve": 24,
              "cone": {"angle": 0.55, "push": 42, "lift": 14, "stun": 0.6}},
             [["+", "A blast of air that shoves everyone in front of you 42 studs back"],
              ["+", "Stuns them for 0.6 seconds"],
              ["-", "Only 14 damage"],
              ["-", "15 stud reach"]], rarity="legendary")
def _():
    return [
        part("cyl", [0, 0.04, 0.60], [0.24, 1.20, 0.24], BRASS, [PI / 2, 0, 0], m="metal"),
        place("trumpet", [0, 0.04, 1.10], [1.40, 0.70, 1.40], "#c4281c", anchor=[0, 0, 0],
              r=[PI / 2, 0, 0], decal="party", wrap=True),
        part("torus", [0, 0.04, 1.80], [0.72, 0.06, 0.72], BRASS, [PI / 2, 0, 0], m="metal"),
        part("rbox", [0, -0.24, -0.10], [0.20, 0.36, 0.70], "#5a3016", [0.25, 0, 0],
             decal="planks", wrap=True),
        place("spiral", [0, 0.30, 0.60], [0.20, 0.50, 0.20], "#9fd8ff", r=[PI / 2, 0, 0]),
    ]


@NY26.gear("grapes", "Twelve Grapes",
           "Eat a grape for every chime of midnight, for luck. For twelve seconds, "
           "luck is on your side.",
           {"kind": "consume", "cooldown": 30, "sound": "eat",
            "consume": {"crit": [0.25, 12.0], "heal": 12}},
           [["+", "For 12 seconds, every shot has a 25% chance to deal double damage"],
            ["+", "Heals 12"],
            ["-", "30 second cooldown"]])
def _():
    parts = [part("cyl", [0, 0.20, 0.30], [0.03, 0.40, 0.03], "#4a6a2a", [0.3, 0, 0])]
    for k in range(12):
        a = k * 2.4
        y = 0.10 - (k % 4) * 0.10
        r = 0.08 + (k % 4) * 0.03
        parts.append(part("sph", [math.sin(a) * r, y, 0.30 + math.cos(a) * r],
                          [0.13, 0.13, 0.13], "#5a2a6a" if k % 3 else "#7a3a8a", m="glass"))
    return parts


NY26.effect("crystal_shower", name="Crystal Shower", rate=7.0, life=[1.6, 2.4],
            size=[0.18, 0.30], grow=0.0, gravity=-0.9, spread=0.5, rise=[0.6, 1.2],
            blend="add", spin=3.0, colors=["#ffffff", "#e8f8ff", "#9fd8ff", "#3a6aa8"],
            shape="crystal", radius=0.6)
NY26.effect("ball_drop", name="Ball Drop", rate=1.4, life=[2.6, 3.2], size=[0.50, 0.62],
            grow=0.0, gravity=-0.3, spread=0.05, rise=[0.6, 0.8], blend="add", spin=0.4,
            colors=["#ffffff", "#dff2ff", "#9fd8ff", "#1b2c4a"], shape="crystal",
            radius=0.2, upright=True, wobble=0.1)
NY26.opening(
    sky={"top": "#030914", "horizon": "#1b3a5c", "sun": [0.3, 0.9, 0.4], "clouds": 0,
         "tint": "#cfe8ff"},
    ambient="#7a9cc0", beam="#e8f8ff", seep="crystal_shower", after="ball_drop",
    burst=["#ffffff", "#dff2ff", "#9fd8ff", "#c9d6e6"],
    pieces=[{"shape": "crystal", "colors": ["#ffffff", "#9fd8ff"], "blend": "add"},
            {"shape": "sparkle", "colors": ["#e8f8ff", "#ffffff"], "blend": "add"},
            {"shape": "confetti", "colors": ["#c9d6e6", "#9fd8ff", "#ff6ad5"], "blend": "normal"}],
    backdrop="skyline", title_wait="The ball is on its way down...",
    title_shake="Five... four... three...")
NY26.award("Crystal Countdown", ["Spectator", "Ball Watcher", "Crystal Clear",
                                 "Prismatic", "Starlit", "Crystal Sovereign"],
           "Opened Ball Drop Crates during the Crystal Countdown, New Year 2026.",
           "em_crystal", "clock")
NY26.bundle("pair", "Crystal Pair", 1, 1050, "One Ball Drop Crate, one Crystal Key.")
NY26.bundle("trio", "Final Countdown", 3, 3000, "Three crates, three keys. Saves 300.")


EVENTS = [NY22, NY23, NY24, NY25, NY26]
