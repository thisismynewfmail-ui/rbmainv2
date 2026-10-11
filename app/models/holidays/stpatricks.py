"""St. Patrick's Day: a leprechaun, a pot of gold and whatever he left behind.

  2022  Lucky Lep's Lockbox      the first one: Lucky Lep, the cobbler
                                 leprechaun, and the brogue he left his
                                 stash in
  2023  Rainbow's End            the pot of gold where the rainbow comes down
  2024  Blarney Hoard            an ancient hoard under a mossy standing
                                 stone, and the gift of the gab
  2025  Emerald Jamboree         a ceili on the green: fiddles, drums and
                                 dancing till the lamps go out
  2026  Leprechaun's Last Laugh  Lep comes back for his gold, and every crate
                                 is a jack-in-the-box

Every year runs the week either side of March 17th.
"""
from __future__ import annotations

import math

from .kit import (BLACK, BRASS, GOLD, GOLD_DARK, IRON, PI, SILVER, SNOW, TAU, WHITE,
                  Event, around, at_frame, band, buckle, cap, dome, mix, part, place,
                  pompom, ringband, rod, rotate, shade, sides, straps)

SHAMROCK = "#4fc46e"
CLOVER = "#2f8a3a"
EMERALD = "#1f9e4a"
BOTTLE = "#1f6b34"
GINGER = "#c8611e"
SKIN = "#f2c9a0"
LEP_GOLD = "#ffd34a"


def _shamrock(at, k, c=SHAMROCK, r=None, **kw):
    """A shamrock standing up facing +Z (turn it with ``r``); ``at`` is the
    middle of its leaves."""
    return place("shamrock", at, k, c, r=r, **kw)


def _coin(at, k=1.0, r=None, face=True):
    """A gold coin standing up facing +Z, struck with a shamrock."""
    return part("disc", at, [0.30 * k, 0.30 * k, 0.05 * k], GOLD, r, m="metal",
                decal="sp_coin" if face else None)


def _lep(at, k=1.0, yaw=0.0, wave=False, glass=False):
    """Lucky Lep himself, about a stud tall at k=1, feet at ``at``: buckled
    shoes and white stockings, green breeches and coat, a ginger fringe of
    beard and his tall buckled hat.  ``glass`` has him peering through a
    spyglass; ``wave`` has an arm up."""
    coat, hat = "#2a8a3e", "#1f6b34"
    pieces = [
        # shoes, stockings and breeches
        *[p for s in (1, -1) for p in (
            part("rbox", [0.08 * s, 0.04, 0.03], [0.13, 0.08, 0.22], BLACK),
            part("rbox", [0.08 * s, 0.06, 0.135], [0.07, 0.05, 0.02], LEP_GOLD, m="metal"),
            part("cyl", [0.08 * s, 0.17, 0.0], [0.09, 0.20, 0.09], WHITE),
        )],
        part("rbox", [0, 0.31, 0], [0.30, 0.14, 0.19], "#2a7a36"),
        # the coat, its belt and buckle
        part("rbox", [0, 0.49, 0], [0.32, 0.30, 0.22], coat, decal="felt", wrap=True),
        part("rbox", [0, 0.40, 0], [0.33, 0.05, 0.23], BLACK),
        part("rbox", [0, 0.40, 0.115], [0.08, 0.06, 0.02], LEP_GOLD, m="metal"),
        part("sph", [0, 0.55, 0.112], [0.03, 0.03, 0.02], LEP_GOLD, m="metal"),
        # head, nose, eyes, the ginger fringe of beard
        part("sph", [0, 0.75, 0], [0.26, 0.26, 0.25], SKIN),
        part("sph", [0, 0.74, 0.13], [0.06, 0.05, 0.05], "#e8957a"),
        part("sph", [0.05, 0.78, 0.115], [0.035, 0.04, 0.02], BLACK),
        part("sph", [-0.05, 0.78, 0.115], [0.035, 0.04, 0.02], BLACK),
        part("sph", [0, 0.66, 0.06], [0.28, 0.16, 0.18], GINGER),
        part("sph", [0.11, 0.72, 0.03], [0.08, 0.16, 0.14], GINGER),
        part("sph", [-0.11, 0.72, 0.03], [0.08, 0.16, 0.14], GINGER),
        # the hat
        part("cyl", [0, 0.86, 0], [0.36, 0.025, 0.36], hat),
        place("sp_taper", [0, 0.87, 0], [0.22, 0.24, 0.22], hat, anchor=[0, 0, 0]),
        part("cyl", [0, 0.905, 0], [0.225, 0.05, 0.225], BLACK),
        part("rbox", [0, 0.905, 0.112], [0.06, 0.05, 0.015], LEP_GOLD, m="metal"),
    ]
    if glass:
        # one arm up holding a brass spyglass to his eye, the other on his hip
        pieces += [part("cyl", [0.15, 0.62, 0.07], [0.07, 0.22, 0.07], coat, [-0.9, 0, 0.5]),
                   part("cyl", [0.05, 0.78, 0.24], [0.06, 0.24, 0.06], BRASS, [PI / 2, 0, 0],
                        m="metal"),
                   part("cyl", [0.05, 0.78, 0.36], [0.075, 0.04, 0.075], BRASS, [PI / 2, 0, 0],
                        m="metal"),
                   part("cyl", [-0.17, 0.46, 0.02], [0.07, 0.22, 0.07], coat, [0, 0, -0.6])]
    elif wave:
        pieces += [part("cyl", [0.20, 0.66, 0], [0.07, 0.24, 0.07], coat, [0, 0, -0.5]),
                   part("sph", [0.26, 0.79, 0], [0.07, 0.07, 0.07], SKIN),
                   part("cyl", [-0.18, 0.46, 0.02], [0.07, 0.22, 0.07], coat, [0, 0, -0.4])]
    else:
        pieces += [part("cyl", [0.19, 0.48, 0.02], [0.07, 0.22, 0.07], coat, [0, 0, 0.35]),
                   part("cyl", [-0.19, 0.48, 0.02], [0.07, 0.22, 0.07], coat, [0, 0, -0.35])]
    return at_frame(pieces, at, [0, yaw, 0] if yaw else None, k)


def _brogue(at, k=1.0, c="#1f6b34", r=None):
    """A little buckled brogue, toe to +X, sole at ``at``."""
    pieces = [
        part("rbox", [0.02, 0.025, 0], [0.62, 0.05, 0.26], "#3a2414"),
        part("rbox", [-0.13, 0.13, 0], [0.32, 0.18, 0.24], c),
        part("sph", [0.12, 0.10, 0], [0.42, 0.16, 0.25], c),
        part("rbox", [-0.06, 0.15, 0.125], [0.08, 0.07, 0.02], LEP_GOLD, m="metal"),
        part("rbox", [-0.23, -0.02, 0], [0.12, 0.06, 0.22], "#2a1a10"),
    ]
    return at_frame(pieces, at, r, k)


# ============================================================ 2022
SP22 = Event(
    "stpatricks_2022", "stpatricks", 2022, "sp22",
    name="Lucky Lep's Lockbox", title="Lucky Lep's Lockbox",
    blurb="Blockhaven's first St. Patrick's Day. A cobbler leprechaun called Lucky Lep "
          "set up shop under the spawn bridge, mended everybody's shoes for nothing, and "
          "paid himself in whatever fell out of their pockets. When he left, he forgot "
          "one shoe. It was full.",
    tagline="Finders keepers. Lep says otherwise.",
    starts="2022-03-10", ends="2022-03-24",
    colors={"accent": "#2fb35a", "deep": "#0a2614", "glow": LEP_GOLD},
    family_effects=["sunbeam", "starstruck", "bubbly"],
    hero_effect="leps_luck", stencil="stencil_sp22")


@SP22.crate_model("Lucky Brogue",
                  "Lucky Lep's own left brogue, ten sizes too big, its flap strapped down "
                  "and buckled, its toe curled up like it is about to start a jig. Holds "
                  "the Lucky Lep's Lockbox set. Needs a Buckle Key.",
                  hinge=[0, 0.30, -0.47], keyhole=[-0.36, -0.08, 0.53])
def _():
    upper, toe, sole, welt = "#1f6b34", "#17552a", "#3a2414", "#8a5a2a"
    parts = [
        # the sole, the welt stitched round it, a stacked heel and the tread
        # under the ball of the foot, so the arch shows between them
        part("rbox", [0.06, -0.47, 0], [1.90, 0.10, 0.98], sole, decal="leather", wrap=True),
        part("rbox", [0.06, -0.40, 0], [1.94, 0.05, 1.02], welt, decal="stitches", wrap=True),
        part("rbox", [-0.66, -0.62, 0], [0.48, 0.20, 0.88], "#2a1a10", decal="planks", wrap=True),
        part("rbox", [0.52, -0.56, 0], [0.82, 0.10, 0.92], sole),
        # the heel counter and quarters, the instep sloping down to the toe
        part("rbox", [-0.44, -0.07, 0], [0.92, 0.66, 0.94], upper, decal="sp_brogue", wrap=True),
        part("wedge", [0.30, -0.06, 0], [0.92, 0.66, 0.60], upper, [0, PI / 2, 0],
             decal="sp_brogue"),
        part("sph", [0.50, -0.20, 0], [1.04, 0.50, 0.94], upper, decal="sp_brogue", wrap=True),
        part("sph", [0.10, -0.06, 0], [0.86, 0.58, 0.93], upper, decal="sp_brogue", wrap=True),
        # the wingtip toe cap, and the toe that curls up and over
        part("sph", [0.76, -0.22, 0], [0.56, 0.44, 0.96], toe, decal="sp_brogue", wrap=True),
        place("horn", [0.98, -0.26, 0], [1.00, 0.90, 2.2], toe, anchor=[0, 0, 0],
              r=[PI, 0, -PI / 2]),
        part("sph", [1.22, 0.03, 0], [0.15, 0.15, 0.15], LEP_GOLD, m="metal"),
        # the padded collar round the opening, and the gold heaped inside it
        part("torus", [-0.44, 0.27, 0], [0.90, 0.12, 0.90], toe),
        part("cyl", [-0.44, 0.27, 0], [0.80, 0.03, 0.80], LEP_GOLD, m="neon"),
        part("cyl", [-0.52, 0.30, 0.12], [0.18, 0.04, 0.18], GOLD, [0.2, 0, 0.1], m="metal"),
        part("cyl", [-0.30, 0.31, -0.10], [0.18, 0.04, 0.18], GOLD, [-0.2, 0, 0.2], m="metal"),
        # the flap (the lid): a leather tongue over the opening, the strap
        # across it and down to the buckle, a shamrock tooled into it
        place("hemi", [-0.44, 0.29, 0], [1.02, 0.22, 1.00], upper, anchor=[0, 0, 0],
              decal="sp_brogue", wrap=True, lid=1),
        part("cyl", [-0.44, 0.30, 0], [1.04, 0.05, 1.02], toe, lid=1),
        part("rbox", [-0.36, 0.40, 0.04], [0.24, 0.07, 1.00], "#16171b", decal="leather", lid=1),
        part("rbox", [-0.36, 0.24, 0.515], [0.24, 0.30, 0.05], "#16171b", decal="leather", lid=1),
        _shamrock([-0.66, 0.43, -0.04], 0.30, SHAMROCK, r=[-PI / 2 + 0.25, 0.6, 0], lid=1),
        # the buckle on the strap (the lock)
        part("rbox", [-0.36, -0.08, 0.50], [0.26, 0.26, 0.06], LEP_GOLD, m="metal",
             decal="keyhole", lock=1),
        part("box", [-0.44, -0.08, -0.475], [0.84, 0.54, 0.02], "#000000", [0, PI, 0],
             decal="stencil_sp22", a=-1),
    ]
    # the buckle's frame round the lock
    for dx, dy, w, h in ((0, 0.17, 0.44, 0.08), (0, -0.33, 0.44, 0.08),
                         (0.18, -0.08, 0.08, 0.50), (-0.18, -0.08, 0.08, 0.50)):
        parts.append(part("rbox", [-0.36 + dx, -0.08 + dy, 0.495], [w, h, 0.07], GOLD_DARK,
                          m="metal"))
    # a few coins that fell out on the way, and hobnails in the heel
    parts += [_coin([1.04, -0.60, 0.40], 0.9, r=[-PI / 2, 0, 0.0]),
              _coin([0.84, -0.615, 0.54], 0.8, r=[-PI / 2, 0, 0.0]),
              _coin([-0.98, -0.58, 0.46], 0.9, r=[-0.4, 0.5, 0.2])]
    parts += [part("sph", [-0.66, -0.62, 0.44 * s], [0.05, 0.05, 0.03], SILVER, m="metal")
              for s in (1, -1)]
    return parts


@SP22.key_model("Buckle Key",
                "A gold key whose bow is a cobbler's shoe-buckle, a shamrock set in green "
                "enamel in the middle and a bit cut like a little boot. Opens one Lucky "
                "Brogue. Lep would like it back.", shoulder=-0.30)
def _():
    parts = [
        part("rbox", [-0.62, 0.25, 0], [0.62, 0.11, 0.10], GOLD, m="metal"),
        part("rbox", [-0.62, -0.25, 0], [0.62, 0.11, 0.10], GOLD, m="metal"),
        part("rbox", [-0.88, 0, 0], [0.11, 0.60, 0.10], GOLD, m="metal"),
        part("rbox", [-0.36, 0, 0], [0.11, 0.60, 0.10], GOLD, m="metal"),
        part("box", [-0.62, 0, -0.01], [0.42, 0.40, 0.03], "#16171b"),
        _shamrock([-0.62, 0.02, 0.03], 0.36, SHAMROCK, m="glass"),
        part("cyl", [0.14, 0, 0], [0.09, 0.96, 0.09], GOLD, [0, 0, PI / 2], m="metal"),
        part("torus", [-0.26, 0, 0], [0.20, 0.07, 0.20], GOLD_DARK, [0, 0, PI / 2], m="metal"),
        # the bit: a boot, heel and toe
        part("rbox", [0.44, -0.13, 0], [0.09, 0.22, 0.08], GOLD, m="metal"),
        part("rbox", [0.56, -0.21, 0], [0.30, 0.08, 0.08], GOLD, m="metal"),
        part("sph", [0.66, 0, 0], [0.11, 0.11, 0.11], GOLD, m="metal"),
    ]
    return parts


@SP22.hat("lep_topper", "Lep's Buckle Topper",
          "The real thing: tall, green, narrowing to the top, a black band and a buckle "
          "you could see your face in. Lep swears this is his spare. Lep swears a lot of "
          "things.", "legendary")
def _():
    hat, brim = "#2a8a3e", "#1f6b34"
    return [
        place("brim", [0, -0.05, 0], [2.30, 1.5, 2.20], brim, anchor=[0, 0, 0],
              decal="felt", wrap=True),
        place("sp_taper", [0, 0.0, 0], [1.36, 1.42, 1.31], hat, anchor=[0, 0, 0],
              decal="felt", wrap=True),
        part("cyl", [0, 0.17, 0], [1.37, 0.28, 1.32], BLACK),
        *buckle([0, 0.17, 0.685], 0.44, 0.34, LEP_GOLD, plate=BLACK),
        part("torus", [0, 1.42, 0], [1.16, 0.05, 1.12], brim),
        # a sprig of shamrock tucked in the band
        _shamrock([0.60, 0.44, 0.30], 0.36, SHAMROCK, r=[0, 1.1, 0.25]),
        _shamrock([0.66, 0.36, 0.12], 0.26, "#3aa85a", r=[0, 1.4, -0.2]),
        part("cyl", [0.66, 0.24, 0.24], [0.03, 0.22, 0.03], CLOVER, [0, 0, 0.2]),
    ]


@SP22.hat("shamrock_boppers", "Shamrock Boppers",
          "A green headband with two shamrocks on springs. They bob when you walk, bob "
          "when you nod, and bob at everybody who says they look silly.", "uncommon",
          hair="show")
def _():
    green = "#2f8a3a"
    parts = [
        part("rbox", [0, 0.035, 0], [1.00, 0.07, 0.16], green),
        *sides(lambda s: [
            part("rbox", [0.62 * s, -0.035, 0], [0.34, 0.07, 0.16], green, [0, 0, 0.55 * s]),
            part("rbox", [0.775 * s, -0.42, 0], [0.07, 0.62, 0.16], green),
            part("sph", [0.79 * s, -0.74, 0], [0.10, 0.10, 0.18], green),
        ]),
    ]
    for s in (1, -1):
        tip = [0.40 * s, 0.86, 0.04]
        parts += [
            part("cyl", [0.34 * s, 0.09, 0], [0.12, 0.06, 0.12], SILVER, m="metal"),
            place("spiral", [0.34 * s, 0.10, 0], [0.16, 0.66, 0.16], SILVER,
                  anchor=[0, 0, 0], r=[0, 0, -0.10 * s], m="metal"),
            _shamrock(tip, 0.56, SHAMROCK, r=[0, 0, -0.18 * s]),
            part("sph", [tip[0], tip[1] - 0.02, 0.07], [0.08, 0.08, 0.06], LEP_GOLD, m="metal"),
        ]
    return parts


@SP22.hat("lep_whiskers", "Lep's Whiskers",
          "A green bowler, and a ginger fringe of beard that goes ear to ear under the "
          "chin and leaves the mouth free for whistling. Clean-shaven upper lip, as is "
          "traditional.", "rare")
def _():
    green = "#22783a"
    parts = [
        place("brim", [0, -0.05, 0], [2.06, 1.2, 1.98], "#1a5a2c", anchor=[0, 0, 0],
              decal="felt", wrap=True),
        dome(-0.05, 0.82, green, decal="felt", wrap=True),
        ringband(0.06, 0.16, BLACK),
        _shamrock([0.42, 0.12, 0.84], 0.26, SHAMROCK, r=[-0.1, 0.45, 0]),
        # the beard: the fringe under the chin, clear of the mouth
        place("beard", [0, -1.10, 0.74], [1.40, 0.58, 0.62], GINGER, anchor=[0, 0.5, 0],
              decal="fur", wrap=True),
    ]
    # ...and up the jaw on either side to the sideburns
    for s in (1, -1):
        parts += [part("rbox", [0.765 * s, -0.66, 0.30], [0.07, 0.62, 0.34], GINGER,
                       decal="fur", wrap=True),
                  part("rbox", [0.70 * s, -1.08, 0.52], [0.16, 0.34, 0.30], GINGER,
                       [0.0, 0.0, -0.25 * s], decal="fur", wrap=True)]
    return parts


@SP22.hat("lep_lookout", "Lep's Little Lookout",
          "Lucky Lep himself, about a foot tall, standing on your head with his spyglass "
          "out, keeping an eye open for anybody who looks like they might have a "
          "pocketful of gold.", "legendary", hair="show")
def _():
    return [
        part("cyl", [0, 0.03, 0], [0.80, 0.06, 0.80], "#5a3a22", decal="planks"),
        *_lep([0.06, 0.06, 0.04], 1.32, yaw=0.0, glass=True),
        # his pot, never far away
        place("bowl", [-0.36, 0.06, -0.16], [0.40, 0.44, 0.40], BLACK, anchor=[0, 0, 0],
              m="metal"),
        part("cyl", [-0.36, 0.28, -0.16], [0.35, 0.04, 0.35], LEP_GOLD, m="metal"),
        part("cyl", [-0.32, 0.32, -0.12], [0.12, 0.03, 0.12], GOLD, [0.3, 0, 0.2], m="metal"),
    ]


@SP22.hat("shamrock_garland", "Shamrock Garland",
          "A crown of fresh shamrocks woven on a green vine, picked from the hill behind "
          "the spawn on the first St. Patrick's morning. Somebody found a four-leaf in "
          "it once. Nobody has since.", "uncommon", hair="show")
def _():
    vine = "#2f6a2a"
    parts = [ringband(-0.08, 0.10, vine)]
    parts += around(10, 0.95, 0, lambda a, x, z: _shamrock(
        [x, 0.06, z * 0.97], 0.40, SHAMROCK if int(round(a / (TAU / 10))) % 2 else "#3aa85a",
        r=[-0.25, a, 0]))
    parts += around(5, 0.96, 0, lambda a, x, z: part(
        "sph", [x, -0.05, z * 0.97], [0.11, 0.11, 0.11], "#fbfdff"), start=TAU / 20)
    return parts


@SP22.hat("cobblers_loupe", "Cobbler's Loupe",
          "Lep's magnifying loupe on a leather headband, for counting stitches, and a "
          "stub of chalk behind the ear for marking soles. The lens makes one eye look "
          "enormous, which is half the point.", "uncommon", hair="show")
def _():
    leather = "#5a3a22"
    return [
        band(-0.28, 0.12, leather, grow=0.02, decal="leather", wrap=True),
        part("rbox", [0.80, -0.28, 0.20], [0.06, 0.20, 0.20], BRASS, m="metal"),
        # the hinge arm forward from the band, and the loupe over the right eye
        part("cyl", [0.62, -0.32, 0.62], [0.05, 0.52, 0.05], BRASS, [PI / 2, -0.55, 0], m="metal"),
        part("cyl", [0.29, -0.47, 0.86], [0.30, 0.26, 0.30], "#16171b", [PI / 2, 0, 0]),
        part("torus", [0.29, -0.47, 0.99], [0.30, 0.05, 0.30], BRASS, [PI / 2, 0, 0], m="metal"),
        part("cyl", [0.29, -0.47, 0.995], [0.24, 0.02, 0.24], "#cfe8ff", [PI / 2, 0, 0],
             m="glass", a=0.55),
        part("sph", [0.29, -0.47, 0.75], [0.10, 0.10, 0.04], "#ffffff", m="glass", a=0.4),
        # the chalk behind the left ear, and a shamrock on the band
        part("cyl", [-0.78, -0.40, -0.05], [0.06, 0.46, 0.06], "#f4f1e6", [0.2, 0, 0.35]),
        _shamrock([-0.32, -0.26, 0.78], 0.22, SHAMROCK),
    ]


@SP22.hat("shamrock_bobble", "Shamrock Bobble",
          "A hand-knitted beanie in county green with a turned-up cuff, and a bobble on "
          "top made of three bobbles, because Lep's aunt could not count to one.", "rare")
def _():
    green = "#2f8a3a"
    parts = [
        dome(-0.30, 0.98, green, decal="knit", wrap=True),
        ringband(-0.04, 0.32, "#f4f6f8", decal="knit", wrap=True),
        ringband(-0.05, 0.08, "#ff9a3a", margin=0.05),
        ringband(-0.27, 0.08, "#ff9a3a", margin=0.05),
        part("cyl", [0, 0.70, 0], [0.09, 0.26, 0.09], "#1f6b34"),
    ]
    for a in (0.0, 2.1, -2.1):
        parts.append(pompom([math.sin(a) * 0.22, 0.90 + math.cos(a) * 0.20, 0.0], 0.42,
                            "#4fc46e"))
    return parts


@SP22.back("shoe_rack", "Lep's Shoe Rack",
           "A little ladder of a rack on shoulder straps, three mended brogues hanging "
           "from it by their laces and Lep's tack hammer hooked on the side. Every pair "
           "is somebody's. None of them are paid for.", "rare")
def _():
    wood = "#b07a40"
    parts = [
        *sides(lambda s: [part("rbox", [0.56 * s, 0.50, -0.30], [0.14, 2.40, 0.14], wood,
                               decal="planks", wrap=True),
                          part("sph", [0.56 * s, 1.74, -0.30], [0.22, 0.22, 0.22], wood)]),
        part("cyl", [0, 1.50, -0.30], [0.09, 1.10, 0.09], wood, [0, 0, PI / 2]),
        part("cyl", [0, 0.70, -0.30], [0.09, 1.10, 0.09], wood, [0, 0, PI / 2]),
        part("cyl", [0, -0.10, -0.30], [0.09, 1.10, 0.09], wood, [0, 0, PI / 2]),
        *straps("#3a2414", 0.36, 0.12),
        part("rbox", [0, 0.72, -0.14], [0.30, 0.12, 0.24], "#3a2414"),
    ]
    # three shoes on their laces, hanging toe down
    for x, y, c in ((-0.22, 1.40, "#2f9e4a"), (0.20, 0.60, "#a0522d"), (-0.16, -0.20, "#e8c890")):
        parts.append(part("cyl", [x, y + 0.02, -0.40], [0.025, 0.16, 0.025], "#f4f1e6"))
        parts += _brogue([x, y - 0.08, -0.44], 1.12, c, r=[0, 0, -PI / 2])
    # the tack hammer on the right rail
    parts += [part("cyl", [0.72, 0.30, -0.30], [0.07, 0.72, 0.07], "#e0b070", [0, 0, 0.25]),
              part("rbox", [0.81, 0.64, -0.30], [0.34, 0.12, 0.12], SILVER, [0, 0, 0.25],
                   m="metal")]
    return parts


@SP22.back("frock_tails", "Lep's Frock-Tails",
           "The swallowtails of a green frock coat, with the half-belt and two gold "
           "buttons at the back. Wear it over anything and you are dressed for a "
           "wedding, a wake or a getaway.", "uncommon")
def _():
    green = "#22783a"
    return [
        # the back of the coat down to the waist, and the half-belt across it
        part("rbox", [0, -0.20, -0.10], [1.70, 1.10, 0.08], green, decal="felt", wrap=True),
        part("rbox", [0, -0.66, -0.15], [1.30, 0.18, 0.06], "#1a5a2c", decal="felt"),
        *sides(lambda s: [
            place("ribbon", [0.36 * s, -1.62, -0.14], [0.74, 1.90, 1.6], green,
                  r=[0.08, 0, 0.10 * s], decal="felt", wrap=True),
            part("rbox", [0.04 * s, -1.60, -0.15], [0.04, 1.80, 0.09], LEP_GOLD, [0.08, 0, 0.0],
                 m="metal"),
            part("sph", [0.32 * s, -0.66, -0.19], [0.16, 0.16, 0.06], LEP_GOLD, m="metal"),
        ]),
    ]


@SP22.hairdo("ginger_tufts", "Ginger Tufts",
             "Short, ginger and determined to stick out over the ears whatever hat you "
             "put on top of it.", "uncommon")
def _():
    c, hi = "#c8611e", "#e07a2e"
    parts = [place("hairmid", [0, 0, 0], [1.04, 1.04, 1.04], c, anchor=[0, 0, 0],
                   decal="strands", wrap=True)]
    # the tufts spring out of the hair over each ear, curling up at the tips
    for s in (1, -1):
        for k, (y, z, lean) in enumerate(((-0.22, 0.08, 1.05), (-0.28, -0.18, 1.30),
                                          (-0.16, -0.42, 0.95))):
            parts.append(place("teardrop", [0.66 * s, y, z], [0.22, 0.36, 0.22],
                               hi if k % 2 else c, anchor=[0, 0.1, 0], r=[0, 0, -lean * s],
                               decal="strands", wrap=True))
    # and a cowlick at the front that will not lie down
    parts.append(place("teardrop", [0.10, 0.50, 0.36], [0.20, 0.44, 0.20], hi,
                       anchor=[0, 0.1, 0], r=[0.7, 0, -0.35]))
    return parts


@SP22.hairdo("clover_curls", "Clover Curls",
             "Long red ringlets, a dozen of them, with two shamrock clips holding the "
             "front back. Every curl has been counted. Lep is still counting.", "rare")
def _():
    c, hi = "#b8401a", "#d8582a"
    parts = [place("hairlong", [0, 0, 0], [1.05, 1.05, 1.05], c, anchor=[0, 0, 0],
                   decal="strands", wrap=True)]
    for k, (x, z) in enumerate(((0.62, 0.10), (0.56, -0.30), (0.30, -0.56), (-0.02, -0.62),
                                (-0.32, -0.56), (-0.58, -0.30), (-0.64, 0.10))):
        parts.append(place("spiral", [x, -0.95, z], [0.24, 0.62, 0.24], hi if k % 2 else c,
                           anchor=[0, 0.5, 0]))
    for s in (1, -1):
        parts += [_shamrock([0.50 * s, -0.10, 0.52], 0.24, SHAMROCK, r=[-0.2, 0.7 * s, 0]),
                  part("rbox", [0.50 * s, -0.20, 0.52], [0.18, 0.04, 0.06], LEP_GOLD,
                       [0, 0.7 * s, 0], m="metal")]
    return parts


SP22.face("lucky_wink", "Lucky Wink",
          "One eye shut, cheeks like apples, freckles everywhere and a grin that knows "
          "exactly where the gold is.", [
              {"k": "ellipse", "x": -0.20, "y": -0.14, "w": 0.07, "h": 0.10, "c": "#16171b"},
              {"k": "ellipse", "x": -0.185, "y": -0.16, "w": 0.025, "h": 0.03, "c": "#ffffff"},
              {"k": "arc", "x": 0.20, "y": -0.11, "r": 0.06, "a0": 0.55, "a1": 0.95, "w": 0.03,
               "c": "#16171b"},
              {"k": "ellipse", "x": -0.30, "y": 0.04, "w": 0.13, "h": 0.07, "c": "#f29a8a"},
              {"k": "ellipse", "x": 0.30, "y": 0.04, "w": 0.13, "h": 0.07, "c": "#f29a8a"},
              {"k": "arc", "x": 0.0, "y": 0.02, "r": 0.20, "a0": 0.08, "a1": 0.42, "w": 0.04,
               "c": "#16171b"},
              {"k": "ellipse", "x": -0.36, "y": -0.02, "w": 0.02, "h": 0.02, "c": "#b8602a"},
              {"k": "ellipse", "x": -0.30, "y": -0.04, "w": 0.02, "h": 0.02, "c": "#b8602a"},
              {"k": "ellipse", "x": -0.26, "y": 0.00, "w": 0.02, "h": 0.02, "c": "#b8602a"},
              {"k": "ellipse", "x": 0.36, "y": -0.02, "w": 0.02, "h": 0.02, "c": "#b8602a"},
              {"k": "ellipse", "x": 0.30, "y": -0.04, "w": 0.02, "h": 0.02, "c": "#b8602a"},
              {"k": "ellipse", "x": 0.26, "y": 0.00, "w": 0.02, "h": 0.02, "c": "#b8602a"},
          ], "uncommon")
SP22.face("gold_fever", "Gold Fever",
          "Eyes like two new sovereigns, and one gold tooth to match. Somebody has "
          "been thinking about the shoe again.", [
              {"k": "ellipse", "x": -0.20, "y": -0.13, "w": 0.15, "h": 0.15, "c": "#b8860b"},
              {"k": "ellipse", "x": 0.20, "y": -0.13, "w": 0.15, "h": 0.15, "c": "#b8860b"},
              {"k": "ellipse", "x": -0.20, "y": -0.13, "w": 0.115, "h": 0.115, "c": "#ffd34a"},
              {"k": "ellipse", "x": 0.20, "y": -0.13, "w": 0.115, "h": 0.115, "c": "#ffd34a"},
              {"k": "ring", "x": -0.20, "y": -0.13, "r": 0.04, "w": 0.012, "c": "#b8860b"},
              {"k": "ring", "x": 0.20, "y": -0.13, "r": 0.04, "w": 0.012, "c": "#b8860b"},
              {"k": "ellipse", "x": -0.225, "y": -0.16, "w": 0.03, "h": 0.03, "c": "#ffffff"},
              {"k": "ellipse", "x": 0.175, "y": -0.16, "w": 0.03, "h": 0.03, "c": "#ffffff"},
              {"k": "poly", "pts": [[-0.20, 0.06], [0.20, 0.06], [0.14, 0.18], [-0.14, 0.18]],
               "c": "#16171b"},
              {"k": "poly", "pts": [[-0.16, 0.065], [0.16, 0.065], [0.15, 0.10], [-0.15, 0.10]],
               "c": "#fffaf0"},
              {"k": "poly", "pts": [[0.04, 0.065], [0.09, 0.065], [0.09, 0.105], [0.04, 0.105]],
               "c": "#ffd34a"},
          ], "rare")
SP22.shirt("lep_waistcoat", "Lep's Sunday Best",
           "A bottle-green coat over a mustard waistcoat, four gold buttons, a green "
           "bow at the throat and a shamrock in the buttonhole. Lep only wears it to "
           "count things.",
           {"torso": "#22783a", "arms": "#22783a", "decal": "sp_tee_waistcoat",
            "weave": "felt", "stripe": "#1a5a2c"}, "rare")
SP22.pants("lep_breeches", "Lep's Knee Breeches",
           "Green breeches to the knee, white stockings and black buckled shoes, polished "
           "until they squeak.",
           {"legs": "#2a7a36", "length": 0.62, "skin": "#f4f6f8", "cuff": "#16171b",
            "weave": "felt"})
SP22.belt("cobblers_belt", "Cobbler's Belt",
          "Black leather, a gold buckle the size of a biscuit, and two pouches: one for "
          "tacks, one for whatever falls out of other people's pockets.",
          {"band": "#1a1410", "buckle": LEP_GOLD, "width": 0.26, "metal": True,
           "weave": "leather", "pouch": "#5a3a22"})


@SP22.weapon("shillelagh", "Shillelagh",
             "A knotted blackthorn stick with a head like a fist, cut from the hedge on "
             "the hill. Swing it in a hurry and the luck runs with you; hit hard enough "
             "and the luck goes all the way.",
             {"kind": "melee", "damage": 30, "headshot": 1.0, "rpm": 92, "range": 10.0,
              "arc": 0.62, "sound": "swing", "knockback": 10, "crit_chance": 0.12,
              "combo": {"window": 1.4, "step": 0.12, "max": 0.6, "label": "Luck"}},
             [["+", "A 12% chance on every swing to land a critical hit for double damage"],
              ["+", "Hits less than 1.4 seconds apart build Luck: +12% damage each, up to "
                    "+60%"],
              ["-", "Pause for longer and the Luck is gone"],
              ["-", "No bonus on a headshot"]], rarity="legendary")
def _():
    wood = "#4a2a18"
    parts = [
        part("cyl", [0, 0, 0.55], [0.17, 1.50, 0.17], wood, [PI / 2, 0, 0], decal="planks",
             wrap=True),
        part("cyl", [0, 0, -0.30], [0.16, 0.40, 0.16], "#3a2416", [PI / 2, 0, 0],
             decal="leather", wrap=True),
        part("torus", [0, -0.10, -0.52], [0.24, 0.04, 0.24], "#5a3a22", [0, 0, PI / 2]),
        part("sph", [0, 0.02, 1.50], [0.56, 0.52, 0.60], "#5a3420", decal="planks", wrap=True),
        part("sph", [0.16, 0.16, 1.66], [0.24, 0.24, 0.24], "#5a3420"),
        part("sph", [-0.17, -0.10, 1.60], [0.22, 0.22, 0.22], "#4a2a18"),
        part("torus", [0, 0, 1.22], [0.22, 0.06, 0.22], SILVER, [PI / 2, 0, 0], m="metal"),
        _shamrock([0.285, 0.04, 1.46], 0.24, SHAMROCK, r=[0, PI / 2, 0]),
    ]
    # the blackthorn knots down the shaft
    for k, (z, a) in enumerate(((0.10, 0.4), (0.42, 2.2), (0.74, 4.1), (1.02, 1.0))):
        parts.append(part("sph", [math.cos(a) * 0.08, math.sin(a) * 0.08, z],
                          [0.11, 0.11, 0.13], "#5a3420"))
    return parts


@SP22.weapon("bubble_pipe", "Lep's Bubble Pipe",
             "Lep's long clay pipe, which has never had a pinch of tobacco in it -- "
             "only soapy water. It blows one great bubble that drifts after the nearest "
             "enemy and swallows them whole.",
             {"kind": "projectile", "projectile": "bubble", "damage": 14, "splash": 4.0,
              "splash_damage": 14, "rpm": 40, "mag": 2, "reload": 2.4, "speed": 24,
              "range": 200, "auto": False, "sound": "pop", "recoil": 0.3, "reserve": 16,
              "gravity_scale": 0.0, "self_damage": 0.0, "knockback": 0,
              "homing": {"turn": 1.6, "range": 26}, "tracer": "#bfefff",
              "trail_shape": "bubble", "trail_colors": ["#dff6ff", "#9fffb0"],
              "on_hit": {"knockup": 20, "root": 1.6}},
             [["+", "A slow bubble that drifts after the nearest enemy within 26 studs"],
              ["+", "Whoever it pops on is lifted off their feet and held fast for 1.6 "
                    "seconds"],
              ["-", "About 10 damage: it is a bubble"],
              ["-", "So slow that anybody watching can step out of its way"]],
             rarity="legendary",
             proj=lambda: [part("sph", [0, 0, 0], [1.30, 1.30, 1.30], "#dff6ff", m="glass",
                                a=0.30),
                           part("torus", [0, 0, 0], [1.10, 0.03, 1.10], "#ffb3e6", [0.5, 0, 0.3],
                                m="neon", a=0.45),
                           part("torus", [0, 0, 0], [1.00, 0.03, 1.00], "#9fffb0", [-0.4, 0, 1.2],
                                m="neon", a=0.45),
                           part("sph", [-0.24, 0.28, 0.30], [0.22, 0.14, 0.10], "#ffffff",
                                m="neon", a=0.6),
                           _shamrock([0, 0, 0], 0.30, SHAMROCK, spin=3.0)])
def _():
    clay = "#efe8da"
    return [
        part("cyl", [0, 0.02, 0.36], [0.08, 1.14, 0.08], clay, [PI / 2 - 0.08, 0, 0]),
        part("cyl", [0, -0.02, -0.22], [0.09, 0.10, 0.09], "#2f8a3a", [PI / 2, 0, 0]),
        place("bowl", [0, 0.06, 0.98], [0.30, 0.42, 0.30], clay, anchor=[0, 0, 0]),
        part("torus", [0, 0.31, 0.98], [0.30, 0.04, 0.30], "#2f8a3a"),
        _shamrock([0, 0.19, 1.135], 0.14, CLOVER),
        part("sph", [0, 0.56, 1.00], [0.42, 0.42, 0.42], "#dff6ff", m="glass", a=0.32),
        part("sph", [-0.07, 0.65, 0.92], [0.10, 0.07, 0.05], "#ffffff", m="neon", a=0.6),
        part("sph", [0.16, 0.86, 0.90], [0.14, 0.14, 0.14], "#dff6ff", m="glass", a=0.3),
    ]


def _chakram():
    """The four-leaf chakram, lying flat: a gold ring round a clover of
    four bright blades."""
    return [
        part("torus", [0, 0, 0], [1.02, 0.07, 1.02], GOLD, m="metal"),
        place("clover4", [0, 0, 0.04], [1.10, 1.10, 0.8], "#3fd06a", r=[PI / 2, 0, 0],
              m="metal"),
        part("cyl", [0, 0, 0], [0.22, 0.10, 0.22], GOLD, m="metal"),
        part("sph", [0, 0.05, 0], [0.10, 0.06, 0.10], "#ffffff", m="glass"),
    ]


@SP22.weapon("clover_chakram", "Four-Leaf Chakram",
             "A gold ring round four clover leaves, each one sharpened to an edge. It "
             "flies true for a breath, then breaks into its four leaves -- and every "
             "leaf can glance off a wall once and keep going.",
             {"kind": "projectile", "projectile": "chakram", "damage": 50, "splash": 4.5,
              "splash_damage": 50, "rpm": 70, "mag": 3, "reload": 2.0, "speed": 84,
              "range": 220, "auto": False, "sound": "throw", "recoil": 0.8, "reserve": 30,
              "gravity_scale": 0.0, "self_damage": 0.0, "knockback": 6, "bounce": 1,
              "tracer": "#7dff9a",
              "split": {"after": 0.24, "count": 4, "spread": 7, "damage": 14,
                        "splash_damage": 14}},
             [["+", "Thrown close, it lands whole: up to 50 damage"],
              ["+", "Past about 20 studs it splits into four leaves fanned across the "
                    "way, up to 14 a leaf"],
              ["+", "Each leaf glances off one wall and carries on"],
              ["-", "The leaves spread as they fly: the further off the target, the "
                    "fewer find them"]],
             rarity="legendary",
             proj=lambda: [dict(p, spin=14.0) for p in _chakram()])
def _():
    return [
        part("cyl", [0, -0.04, -0.06], [0.16, 0.40, 0.16], "#3a2414", [PI / 2, 0, 0],
             decal="leather", wrap=True),
        *at_frame(_chakram(), [0, 0.0, 0.62], k=0.82),
    ]


@SP22.gear("lucky_coin", "Lep's Lucky Coin",
           "Lep's own gold coin, worn smooth by forty years of flipping. Toss it: three "
           "times in five, the luck is yours. The other two, it is Lep's.",
           {"kind": "consume", "cooldown": 20, "sound": "coin",
            "consume": {"random": [
                {"name": "Heads! Luck's with you", "crit": [0.30, 10.0], "speed": [0.12, 10.0]},
                {"name": "A four-leaf clover in the change", "heal": 35, "shield": [30, 8.0]},
                {"name": "Lep's own lucky penny: one death cheated",
                 "trick": {"cheat": [1.0, 20.0]}},
                {"name": "Tails! Lep's tied your laces", "trick": {"slow": [0.35, 4.0]}},
                {"name": "Tails! Lep's pinned a target on you", "trick": {"mark": [0.2, 4.0]}},
            ]}},
           [["+", "Flip it for one of three lucky outcomes: 30% crits and a little speed "
                  "for 10 seconds; a 35 heal and a 30-point shield; or a death cheated "
                  "within 20 seconds"],
            ["-", "Or one of Lep's two tricks: 35% slower for 4 seconds, or taking 20% "
                  "more damage for 4"],
            ["-", "20 second cooldown"]], rarity="rare")
def _():
    return [
        _coin([0.012, 0.30, 0.18], 1.9, r=[0, PI / 2, 0]),
        _coin([-0.012, 0.30, 0.18], 1.9, r=[0, -PI / 2, 0]),
        part("torus", [0, 0.30, 0.18], [0.58, 0.05, 0.58], GOLD_DARK, [0, 0, PI / 2], m="metal"),
        part("sph", [0.06, 0.40, 0.12], [0.06, 0.06, 0.03], "#ffffff", m="neon", a=0.7),
    ]


SP22.effect("leps_luck", name="Lep's Luck", rate=4.0, life=[1.8, 2.6],
            size=[0.24, 0.36], grow=0.0, gravity=0.0, spread=0.25, rise=[0.1, 0.3],
            blend="normal", spin=1.4, colors=["#9fffb0", "#4fc46e", "#2f8a3a", "#ffd34a"],
            shapes=["shamrock", "shamrock", "sp_coin"], radius=0.8, orbit=1.5, wobble=0.3)
SP22.effect("cobblers_jig", name="Cobbler's Jig", rate=2.4, life=[2.0, 2.8],
            size=[0.30, 0.40], grow=0.0, gravity=-0.4, spread=0.3, rise=[0.3, 0.6],
            blend="normal", spin=0.0, colors=["#2f8a3a", "#1f6b34", "#16171b"],
            shape="sp_brogue", radius=0.9, orbit=2.2, upright=True, wobble=0.6)
SP22.opening(
    sky={"top": "#06180c", "horizon": "#1f5a2e", "sun": [0.2, 0.9, 0.6], "clouds": 0,
         "tint": "#c8ffd0"},
    ambient="#5a8a5a", beam=LEP_GOLD, seep="leps_luck", after="cobblers_jig",
    burst=[LEP_GOLD, "#4fc46e", "#ffffff", "#2f8a3a"],
    pieces=[{"shape": "shamrock", "colors": ["#4fc46e", "#2f8a3a"], "blend": "normal"},
            {"shape": "sp_coin", "colors": ["#ffd34a", "#f2c230"], "blend": "normal"},
            {"shape": "sp_brogue", "colors": ["#1f6b34", "#16171b"], "blend": "normal"},
            {"shape": "spark", "colors": ["#fff3b0", "#ffd34a"], "blend": "add"}],
    backdrop="sp_cobbler", title_wait="Something is tapping inside the shoe...",
    title_shake="Lep wants his shoe back...")
SP22.award("Lucky Lep's Lockbox", ["Finder", "Keeper", "Shoe Shiner", "Cobbler's Apprentice",
                                    "Buckle Bearer", "Lep's Own Luck"],
           "Opened Lucky Brogues at Blockhaven's first St. Patrick's Day, 2022.",
           "em_shamrock", "clover")
SP22.bundle("pair", "Brogue and Buckle", 1, 1050, "One Lucky Brogue, one Buckle Key.")
SP22.bundle("stash", "Lep's Stash", 3, 3000, "Three brogues, three keys. Saves 300.")



# ============================================================ 2023
RAIN_BLUE = "#3a6ad6"
CLOUD = "#f6f8fc"
OILSKIN = "#ffd34a"


def _rainbow(at, k, r=None, **kw):
    """A rainbow arching over ``at`` (the middle of its foot), red on the
    outside, ``k`` across, standing up facing +Z."""
    return place("rainbowarc", at, [k, k, 1.6], "#ffffff", anchor=[0, 0, 0], r=r,
                 decal="sp_rainbow", wrap=True, **kw)


def _cloud(at, k, c=CLOUD, r=None, **kw):
    """A fluffy cloud, about ``k`` wide, middle at ``at`` (the flat cut-out,
    for things seen from the front)."""
    return place("cloud", at, [k, k, k * 1.6], c, r=r, **kw)


def _puff(at, k, c=CLOUD, **kw):
    """A cloud in the round, about ``k`` wide: a few soft lumps on a flat
    underside, for things seen from every side."""
    x, y, z = at
    lumps = [(0.0, 0.10, 0.0, 0.62), (0.26, 0.04, 0.06, 0.46), (-0.26, 0.04, -0.04, 0.48),
             (0.08, 0.04, 0.24, 0.40), (-0.06, 0.06, -0.24, 0.42), (0.10, 0.24, -0.04, 0.40)]
    out = [part("sph", [x + dx * k, y + dy * k, z + dz * k], [w * k, w * k * 0.82, w * k],
                c if n % 2 else shade(c, 0.95), **kw) for n, (dx, dy, dz, w) in enumerate(lumps)]
    out.append(part("cyl", [x, y - 0.06 * k, z], [0.80 * k, 0.10 * k, 0.62 * k], shade(c, 0.88), **kw))
    return out


SP23 = Event(
    "stpatricks_2023", "stpatricks", 2023, "sp23",
    name="Rainbow's End", title="Rainbow's End",
    blurb="St. Patrick's 2023 came in on a week of showers, and on the last afternoon "
          "the sun broke through and a rainbow came down right in the middle of the "
          "spawn. Everybody ran for the end of it. There was a pot. There was gold. "
          "There was also a very cross leprechaun.",
    tagline="Somewhere over the spawn point.",
    starts="2023-03-10", ends="2023-03-24",
    colors={"accent": "#ffd34a", "deep": "#0e1e3a", "glow": "#9fd8ff"},
    family_effects=["sunbeam", "bubbly", "starstruck"],
    hero_effect="rainbow_road", stencil="stencil_sp23")


@SP23.crate_model("Pot o' Gold",
                  "The pot at the very end of the rainbow: black iron, a gold rim, heaped "
                  "over the top with coins, and the rainbow still coming down into it. "
                  "Holds the Rainbow's End set. Needs a Rainbow Key.",
                  hinge=[0, 0.30, -0.72], keyhole=[0, -0.12, 0.83])
def _():
    iron = "#1c1d22"
    parts = [
        # the pot: a fat iron belly on three stubby feet, a gold rim, two ears
        place("bowl", [0, -0.56, 0], [1.66, 1.42, 1.66], iron, anchor=[0, 0, 0], m="metal"),
        part("torus", [0, 0.27, 0], [1.50, 0.13, 1.50], GOLD, m="metal"),
        part("torus", [0, -0.30, 0], [1.66, 0.05, 1.66], shade(iron, 1.4), m="metal"),
        part("cyl", [0, 0.22, 0], [1.38, 0.04, 1.38], LEP_GOLD, m="neon"),
        # the lock: a gold plate with a shamrock over the keyhole
        part("rbox", [0, -0.12, 0.79], [0.32, 0.32, 0.07], GOLD, m="metal", decal="keyhole",
             lock=1),
        _shamrock([0, 0.12, 0.79], 0.20, SHAMROCK),
        # the stencil on the back
        part("box", [0, -0.12, -0.80], [0.64, 0.46, 0.02], "#000000", [0, PI, 0],
             decal="stencil_sp23", a=-1),
        # the lid: the heap of gold, the rainbow coming down into it and the
        # cloud at each foot of it
        part("hemi", [0, 0.44, 0], [1.42, 0.40, 1.42], GOLD, m="metal", decal="sp_coins",
             wrap=True, lid=1),
        _rainbow([0, 0.40, -0.06], 1.30, lid=1),
        _cloud([0.64, 0.50, -0.06], 0.62, lid=1),
        _cloud([-0.64, 0.50, -0.06], 0.62, lid=1),
    ]
    for a in (PI / 2, PI * 7 / 6, PI * 11 / 6):
        parts.append(part("sph", [math.cos(a) * 0.52, -0.62, math.sin(a) * 0.52],
                          [0.22, 0.16, 0.22], iron, m="metal"))
    for side in (1, -1):
        parts.append(part("torus", [0.84 * side, 0.08, 0], [0.30, 0.07, 0.30], iron,
                          [0, 0, PI / 2], m="metal"))
    # coins on top of the heap and a few that rolled down the side
    for x, z, a in ((0.30, 0.24, 0.5), (-0.26, 0.30, -0.4), (0.06, -0.26, 1.1), (0.40, -0.12, -0.8)):
        parts.append(_coin([x, 0.58 - (x * x + z * z) * 0.6, z], 0.9, r=[-PI / 2 + a * 0.3, a, 0]))
    for x, y, z in ((0.70, -0.62, 0.42), (-0.62, -0.63, 0.50)):
        parts.append(_coin([x, y, z], 0.9, r=[-PI / 2, 0, 0]))
    return parts


@SP23.key_model("Rainbow Key",
                "A gold key whose bow is a little rainbow, a cloud at either foot. Opens "
                "one Pot o' Gold, if you can get to the end of it first.", shoulder=-0.30)
def _():
    return [
        _rainbow([-0.62, -0.12, 0], 0.66),
        _cloud([-0.93, -0.08, 0], 0.30),
        _cloud([-0.31, -0.08, 0], 0.30),
        part("cyl", [0.13, 0, 0], [0.09, 0.84, 0.09], GOLD, [0, 0, PI / 2], m="metal"),
        part("torus", [-0.27, 0, 0], [0.20, 0.07, 0.20], GOLD_DARK, [0, 0, PI / 2], m="metal"),
        part("rbox", [0.40, -0.12, 0], [0.08, 0.22, 0.08], GOLD, m="metal"),
        part("rbox", [0.50, -0.16, 0], [0.08, 0.30, 0.08], GOLD, m="metal"),
        _coin([0.60, -0.02, 0], 0.7),
    ]


@SP23.hat("rainbow_crown", "Rainbow's End",
          "A whole rainbow, ear to ear, a cloud at either foot and the pot of gold "
          "sitting on the right-hand one. You are standing at the end of it. You are "
          "the end of it.", "legendary", hair="show")
def _():
    parts = [
        ringband(-0.30, 0.10, "#ffffff"),
        # the arch, wide enough to clear the head, its feet down by the ears
        _rainbow([0, -0.42, 0], 2.80),
        _cloud([1.08, -0.40, 0], 0.80),
        _cloud([-1.08, -0.40, 0], 0.80),
        part("rbox", [0.78, -0.33, 0], [0.12, 0.08, 0.16], "#ffffff"),
        part("rbox", [-0.78, -0.33, 0], [0.12, 0.08, 0.16], "#ffffff"),
        # the pot of gold on the right cloud
        place("bowl", [1.10, -0.30, 0.04], [0.40, 0.42, 0.40], "#1c1d22", anchor=[0, 0, 0],
              m="metal"),
        part("hemi", [1.10, -0.06, 0.04], [0.36, 0.12, 0.36], GOLD, m="metal", decal="sp_coins",
             wrap=True),
    ]
    # the light coming off it
    parts += [part("sph", [0, 0.92, 0], [0.10, 0.10, 0.10], "#fff3b0", m="neon", a=0.8)]
    return parts


@SP23.hat("souwester", "Puddle-Hopper Sou'wester",
          "A yellow oilskin rain hat, wide behind to keep the drips off your collar, a "
          "shamrock badge on the front and a drip on the brim that never quite falls.",
          "rare")
def _():
    parts = [
        dome(-0.32, 0.86, OILSKIN, t="capcrown", m="glass"),
        # the brim, short at the front and long down the back
        place("brim", [0, -0.30, -0.18], [2.30, 1.0, 2.50], OILSKIN, anchor=[0, 0, 0],
              r=[-0.18, 0, 0], m="glass"),
        ringband(-0.24, 0.10, shade(OILSKIN, 0.82), margin=0.05),
        _shamrock([0, -0.06, 0.88], 0.26, SHAMROCK, r=[-0.3, 0, 0]),
        # the drip
        place("teardrop", [0.46, -0.52, 0.86], [0.10, 0.16, 0.10], "#9fd8ff", r=[PI, 0, 0],
              m="glass", a=0.8),
    ]
    # the stitching round the crown
    parts += around(10, 0.93, -0.12, lambda a, x, z: part(
        "rbox", [x, -0.12, z * 0.97], [0.10, 0.02, 0.02], shade(OILSKIN, 0.7), [0, a, 0]))
    return parts


@SP23.hat("cloud_nine", "Cloud Nine",
          "Your own little cloud, a foot above your head, raining very gently on you and "
          "nobody else. There is a rainbow in it, if you stand at the right angle.",
          "rare", hair="show")
def _():
    parts = [
        *_puff([0, 1.02, 0], 1.60),
        *_puff([0.46, 1.10, -0.16], 0.80),
        _rainbow([0.10, 0.66, 0.40], 0.80, r=[0, 0.3, 0]),
    ]
    # the rain, a column of drips falling past the head (but clear of it)
    for k, (x, z) in enumerate(((0.52, 0.30), (-0.50, 0.24), (0.30, -0.42), (-0.24, -0.46),
                                (0.62, -0.10), (-0.62, -0.06))):
        for n in range(2):
            parts.append(place("teardrop", [x, 0.62 - n * 0.42 - (k % 2) * 0.18, z],
                               [0.07, 0.12, 0.07], "#9fd8ff", r=[PI, 0, 0], m="glass", a=0.75))
    return parts


@SP23.hat("coin_crown", "Crown of Sovereigns",
          "A crown made of nothing but stacked gold coins -- no glue, no wire, just "
          "balance and greed. Nod too hard and you will be paying for it.", "uncommon",
          hair="show")
def _():
    parts = [ringband(-0.22, 0.16, GOLD_DARK, m="metal")]
    heights = [5, 3, 6, 4, 7, 4, 6, 3, 5, 4, 6, 3]
    for k, n in enumerate(heights):
        a = k * TAU / len(heights)
        x, z = math.sin(a) * 0.92, math.cos(a) * 0.89
        for c in range(n):
            parts.append(part("cyl", [x + ((c * 7) % 3 - 1) * 0.008, -0.10 + c * 0.055, z],
                              [0.22, 0.05, 0.22], GOLD if c % 2 else LEP_GOLD, m="metal"))
    parts.append(_shamrock([0, 0.14, 0.94], 0.24, SHAMROCK, m="glass"))
    return parts


@SP23.hat("rainbow_bucket", "Rainbow Bucket Hat",
          "A floppy bucket hat sewn from seven panels, one for every band of the "
          "rainbow, with a shamrock pin. Good in the rain. Better after it.", "uncommon")
def _():
    return [
        place("bell", [0, -0.30, 0], [2.30, 0.66, 2.30], "#ffffff", anchor=[0, 0, 0],
              decal="sp_rainbow_gores", wrap=True),
        part("cyl", [0, 0.13, 0], [1.82, 0.54, 1.78], "#ffffff", decal="sp_rainbow_gores",
             wrap=True),
        part("sph", [0, 0.40, 0], [1.82, 0.18, 1.78], "#ffffff", decal="sp_rainbow_gores",
             wrap=True),
        part("cyl", [0, -0.05, 0], [1.86, 0.13, 1.82], "#16171b"),
        _shamrock([0.58, 0.02, 0.70], 0.24, SHAMROCK, r=[0, 0.7, 0]),
    ]


@SP23.hat("prism_specs", "Prism Specs",
          "Wire spectacles with a glass prism for each lens. Look at the world through "
          "them and everything has a rainbow round it, including the people you are "
          "aiming at.", "rare", hair="show")
def _():
    wire = "#c9a227"
    parts = [
        part("rbox", [0, -0.47, 0.74], [0.20, 0.03, 0.03], wire, m="metal"),
        *sides(lambda s: [
            place("gem", [0.27 * s, -0.47, 0.76], [0.34, 0.24, 0.30], "#dff6ff",
                  anchor=[0, 0.36, 0], r=[PI / 2, 0, 0], m="glass", a=0.55),
            part("torus", [0.27 * s, -0.47, 0.75], [0.34, 0.04, 0.34], wire, [PI / 2, 0, 0],
                 m="metal"),
            part("rbox", [0.75 * s, -0.47, 0.28], [0.03, 0.03, 0.90], wire, m="metal"),
            # the little rainbow each lens throws
            _rainbow([0.27 * s, -0.33, 0.90], 0.42, r=[-0.4, 0, 0], a=0.9),
        ]),
    ]
    return parts


@SP23.hat("weathercock", "Shamrock Weathercock",
          "A tin weathervane on a green cap: a cockerel on top, a shamrock for the "
          "arrow, and the four letters underneath. It always points to the nearest "
          "gold.", "uncommon")
def _():
    tin = "#9aa3ad"
    parts = [
        cap(-0.28, 0.12, "#2f8a3a", decal="felt", wrap=True),
        band(-0.22, 0.10, GOLD, grow=0.05, m="metal"),
        part("cyl", [0, 0.50, 0], [0.05, 0.80, 0.05], tin, m="metal"),
        part("sph", [0, 0.14, 0], [0.16, 0.06, 0.16], tin, m="metal"),
    ]
    # N E S W on their arms
    for k, a in enumerate((0.0, PI / 2, PI, -PI / 2)):
        x, z = math.sin(a) * 0.30, math.cos(a) * 0.30
        parts += [part("cyl", [x / 2, 0.42, z / 2], [0.025, 0.30, 0.025], tin,
                       [PI / 2, a, 0], m="metal"),
                  part("box", [x * 1.15, 0.42, z * 1.15], [0.10, 0.12, 0.02], tin, [0, a, 0],
                       m="metal")]
    # the vane turns: a shamrock arrow and the cockerel riding it
    parts += [
        part("rbox", [0, 0.74, 0], [0.04, 0.04, 0.70], GOLD, m="metal", spin=0.6),
        _shamrock([0, 0.74, 0.40], 0.24, SHAMROCK, r=[PI / 2, 0, 0], spin=0.6),
        place("tri", [0, 0.74, -0.38], [0.24, 0.20, 0.3], GOLD, r=[0, PI / 2, 0], m="metal",
              spin=0.6),
        part("sph", [0, 0.92, 0.02], [0.20, 0.18, 0.28], GOLD, m="metal", spin=0.6),
        part("sph", [0, 1.04, 0.12], [0.11, 0.12, 0.11], GOLD, m="metal", spin=0.6),
        place("tri", [0, 1.02, -0.14], [0.16, 0.22, 0.3], GOLD, r=[0, PI / 2, 0.4], m="metal",
              spin=0.6),
    ]
    return parts


@SP23.back("rainbow_cape", "Rainbow Cape",
           "A cape cut from the rainbow itself, seven bands from collar to hem, fastened "
           "at the throat with a cloud. It is lighter than it looks. It is lighter than "
           "anything.", "legendary")
def _():
    return [
        place("cape", [0, 0.96, -0.08], [1.66, 1.90, 1.4], "#ffffff", anchor=[0, 0, 0],
              decal="sp_rainbow_gores", wrap=True),
        # a cloud on each shoulder, and one more at the throat for a clasp
        *_puff([0.80, 1.08, 0.34], 0.50),
        *_puff([-0.80, 1.08, 0.34], 0.50),
        *_puff([0, 1.02, 1.17], 0.26),
    ]


@SP23.back("sack_of_gold", "Sack of Gold",
           "A bulging sack slung over the shoulder, tied at the neck, with a gold coin "
           "slipping out of a hole near the bottom every few steps. The trail leads "
           "straight back to you.", "rare")
def _():
    burlap = "#b08a52"
    parts = straps("#5a3a22") + [
        part("sph", [0.06, 0.10, -0.52], [1.20, 1.30, 0.80], burlap, decal="canvas", wrap=True),
        place("teardrop", [0.10, 0.70, -0.52], [0.52, 0.56, 0.40], burlap, anchor=[0, 0, 0],
              decal="canvas", wrap=True),
        part("torus", [0.10, 0.80, -0.52], [0.34, 0.07, 0.30], "#5a3a22"),
        place("teardrop", [0.10, 1.04, -0.52], [0.30, 0.30, 0.26], burlap, anchor=[0, 0, 0],
              r=[0, 0, 0.5], decal="canvas", wrap=True),
        # a coin peeking out of the hole, and the stencilled pound sign
        _coin([0.38, -0.36, -0.86], 0.9, r=[0.4, 0.3, 0.6]),
        part("box", [0.06, 0.18, -0.925], [0.42, 0.42, 0.02], "#000000", [0, PI, 0],
             decal="sp_coin", a=-1),
    ]
    return parts


@SP23.hairdo("rainbow_streaks", "Rainbow Streaks",
             "Long white hair with every colour of the rainbow combed through it, from "
             "red at the parting to violet at the tips.", "rare")
def _():
    return [place("hairlong", [0, 0, 0], [1.05, 1.05, 1.05], "#f4f6f8", anchor=[0, 0, 0],
                  decal="sp_rainbow_gores", wrap=True),
            # a white streak at the parting, where the colours start
            part("rbox", [0, 0.51, 0.10], [0.06, 0.03, 0.60], "#ffffff")]


@SP23.hairdo("sunbreak_spikes", "Sunbreak Spikes",
             "Short spikes bleached gold at the tips, like the sun coming out from behind "
             "a cloud. Takes an hour and a whole tub of gel. Lasts until the first "
             "shower.", "uncommon")
def _():
    c, tip = "#6a4a2a", "#ffd34a"
    parts = [place("hairshort", [0, 0, 0], [1.03, 1.03, 1.03], c, anchor=[0, 0, 0],
                   decal="strands", wrap=True)]
    for k in range(11):
        a = k * TAU / 11
        r = 0.30 if k % 2 else 0.18
        lean = 0.5 if k % 2 else 0.25
        at = [math.sin(a) * r, 0.50, math.cos(a) * r - 0.04]
        parts.append(place("cone", at, [0.20, 0.34, 0.20], tip if k % 3 else c,
                           anchor=[0, -0.5, 0], r=[math.cos(a) * lean, 0, -math.sin(a) * lean]))
    return parts


SP23.face("sun_shower", "Sun Shower",
          "One eye squinting at the sun, the other one crying at the rain, and a grin "
          "in between because there is a rainbow coming.", [
              {"k": "arc", "x": -0.20, "y": -0.12, "r": 0.06, "a0": 0.55, "a1": 0.95, "w": 0.03,
               "c": "#16171b"},
              {"k": "star", "x": -0.20, "y": -0.24, "r": 0.05, "c": "#ffd34a"},
              {"k": "ellipse", "x": 0.20, "y": -0.13, "w": 0.07, "h": 0.10, "c": "#16171b"},
              {"k": "ellipse", "x": 0.185, "y": -0.15, "w": 0.025, "h": 0.03, "c": "#ffffff"},
              {"k": "poly", "pts": [[0.23, -0.05], [0.21, 0.04], [0.25, 0.04]], "c": "#5aa8ff"},
              {"k": "arc", "x": 0.0, "y": 0.02, "r": 0.20, "a0": 0.08, "a1": 0.42, "w": 0.04,
               "c": "#16171b"},
          ], "uncommon")
SP23.face("rainbow_blush", "Rainbow Blush",
          "Sparkling eyes and a rainbow across each cheek, painted on at the parade and "
          "never washed off.", [
              {"k": "ellipse", "x": -0.20, "y": -0.13, "w": 0.08, "h": 0.11, "c": "#16171b"},
              {"k": "ellipse", "x": 0.20, "y": -0.13, "w": 0.08, "h": 0.11, "c": "#16171b"},
              {"k": "ellipse", "x": -0.185, "y": -0.16, "w": 0.03, "h": 0.035, "c": "#ffffff"},
              {"k": "ellipse", "x": 0.215, "y": -0.16, "w": 0.03, "h": 0.035, "c": "#ffffff"},
          ] + [{"k": "arc", "x": sx, "y": 0.10, "r": 0.10 - n * 0.018, "a0": 0.52, "a1": 0.98,
                "w": 0.016, "c": c}
               for sx in (-0.30, 0.30)
               for n, c in enumerate(("#ff5a5a", "#ffb347", "#ffe066", "#6be08a", "#5aa8ff"))] + [
              {"k": "arc", "x": 0.0, "y": 0.06, "r": 0.12, "a0": 0.10, "a1": 0.40, "w": 0.035,
               "c": "#16171b"},
          ], "rare")
SP23.shirt("rainbow_jumper", "Rainbow Jumper",
           "A chunky knit in seven stripes with a pot of gold on the chest. Knitted by "
           "the same aunt as the bobble hat. She has since learned to count.",
           {"torso": "#f4f6f8", "arms": "#f4f6f8", "decal": "sp_tee_rainbow", "weave": "knit"},
           "uncommon")
SP23.pants("puddle_jumpers", "Puddle Jumpers",
           "Navy oilskin trousers tucked into yellow wellies, for going straight through "
           "the middle of every puddle between you and the gold.",
           {"legs": "#24365e", "cuff": OILSKIN, "weave": "canvas"})
SP23.belt("sovereign_belt", "Sovereign Belt",
          "A green belt with a gold sovereign for a buckle and two pouches for the change.",
          {"band": "#1f6b34", "buckle": GOLD, "width": 0.22, "metal": True, "weave": "leather",
           "pouch": True})


@SP23.weapon("rainbow_ray", "Prism Ray",
             "A brass prism on a stock that splits the sun into a beam of every colour. "
             "Hold it on somebody and it burns brighter; and while it shines, every "
             "teammate near you stands a little taller in the light.",
             {"kind": "beam", "damage": 3, "headshot": 1.0, "rpm": 600, "mag": 0, "range": 60,
              "auto": True, "sound": "laser", "recoil": 0.05, "spread": 0.3, "beam": "#ffe066",
              "ramp": {"per_sec": 0.7, "max": 2.4},
              "heat": {"per_shot": 0.022, "cool": 0.20, "lock": 2.2, "label": "Glare"},
              "ally_buff": {"radius": 16, "might": [0.12, 1.5], "haste": [0.10, 1.5]}},
             [["+", "A continuous rainbow beam: up to 2.4x damage held on one target"],
              ["+", "While it is hitting, teammates within 16 studs do 12% more damage and "
                    "move 10% faster"],
              ["-", "Only 3 damage a tick to begin with"],
              ["-", "Overheats: 2 seconds of Glare if you hold it too long"]],
             rarity="legendary")
def _():
    brass = "#c9a227"
    return [
        part("rbox", [0, -0.10, -0.12], [0.16, 0.36, 0.24], "#5a3a22", [-0.25, 0, 0],
             decal="leather"),
        part("cyl", [0, 0.04, 0.32], [0.20, 0.80, 0.20], brass, [PI / 2, 0, 0], m="metal"),
        place("gem", [0, 0.04, 0.86], [0.42, 0.42, 0.42], "#dff6ff", anchor=[0, 0.36, 0],
              r=[PI / 2, 0, 0], m="glass", a=0.6),
        part("torus", [0, 0.04, 0.74], [0.30, 0.05, 0.30], brass, [PI / 2, 0, 0], m="metal"),
        _rainbow([0, 0.04, 1.02], 0.36, r=[PI / 2, 0, 0], a=0.9),
        _shamrock([0, 0.16, 0.30], 0.16, SHAMROCK, r=[-PI / 2, 0, 0]),
    ]


@SP23.weapon("pot_mortar", "Pot o' Gold Mortar",
             "Lobs Lep's own pot in a long arc. It bursts where it lands in a shower of "
             "gold, and every coin a teammate picks up makes them hit harder and fills "
             "their pockets with ammunition.",
             {"kind": "projectile", "projectile": "potogold", "damage": 30, "splash": 7.0,
              "splash_damage": 30, "rpm": 40, "mag": 2, "reload": 2.6, "speed": 58, "range": 260,
              "auto": False, "sound": "throw", "recoil": 1.4, "reserve": 14, "gravity_scale": 1.2,
              "self_damage": 0.0, "knockback": 12,
              "pickups": {"count": 4, "spread": 5.0, "might": [0.15, 6.0], "ammo": 6,
                          "secs": 14.0, "radius": 3.0, "color": "#ffd34a"}},
             [["+", "Leaves four gold coins where it lands: a teammate who picks one up does "
                    "15% more damage for 6 seconds and gets 6 rounds"],
              ["+", "A 7 stud blast"],
              ["-", "A high, slow lob"],
              ["-", "Two to a load"]], rarity="legendary",
             proj=lambda: [place("bowl", [0, -0.20, 0], [0.80, 0.80, 0.80], "#1c1d22",
                                 anchor=[0, 0, 0], m="metal"),
                           part("hemi", [0, 0.28, 0], [0.70, 0.22, 0.70], GOLD, m="metal",
                                decal="sp_coins", wrap=True)])
def _():
    return [
        part("rbox", [0, -0.16, -0.10], [0.18, 0.40, 0.26], "#5a3a22", [-0.25, 0, 0],
             decal="leather"),
        part("cyl", [0, 0.06, 0.40], [0.42, 1.10, 0.42], "#2f8a3a", [PI / 2 - 0.12, 0, 0],
             m="metal"),
        part("torus", [0, 0.12, 0.96], [0.46, 0.08, 0.46], GOLD, [PI / 2 - 0.12, 0, 0],
             m="metal"),
        part("hemi", [0, 0.13, 1.00], [0.34, 0.12, 0.34], GOLD, [PI / 2 - 0.12, 0, 0],
             m="metal", decal="sp_coins", wrap=True),
        _shamrock([0, 0.30, 0.40], 0.24, SHAMROCK, r=[-PI / 2 - 0.12, 0, 0]),
    ]


@SP23.weapon("cloudburst", "Cloudburst",
             "A little grey cloud in a jar. Point it and pop the lid: the cloud goes and "
             "sits over whoever you were pointing at, rumbles once, and lets go of a "
             "bolt that leaves them seeing stars.",
             {"kind": "strike", "cooldown": 7, "range": 120, "sound": "chime",
              "strike": {"delay": 1.0, "radius": 5.0, "damage": 45, "knock": 14,
                         "on_hit": {"stun": 1.0}}},
             [["+", "A bolt one second after you call it, anywhere you can see up to 120 "
                    "studs away"],
              ["+", "Everyone it strikes is stunned for a second"],
              ["-", "A small strike: 5 studs across"],
              ["-", "7 seconds between bolts"]], rarity="legendary",
             proj=lambda: [_cloud([0, 1.4, 0], 2.4, "#8a93a6"),
                           place("bolt", [0, 0.2, 0], [0.9, 1.6, 0.9], "#ffe066", m="neon")])
def _():
    return [
        part("cyl", [0, 0.20, 0.20], [0.46, 0.60, 0.46], "#dff6ff", m="glass", a=0.45),
        part("cyl", [0, 0.52, 0.20], [0.50, 0.08, 0.50], "#c9a227", m="metal"),
        _cloud([0, 0.22, 0.20], 0.36, "#8a93a6"),
        place("bolt", [0.02, 0.12, 0.20], [0.12, 0.20, 0.12], "#ffe066", m="neon"),
        part("cyl", [0, -0.12, 0.20], [0.48, 0.06, 0.48], "#c9a227", m="metal"),
    ]


@SP23.gear("leps_brolly", "Lep's Brolly",
           "A green umbrella with a shamrock on every panel. Open it and the wind takes "
           "you: you float down from anywhere, and the rain bounces off it -- along with "
           "a fair bit of everything else.",
           {"kind": "ability", "cooldown": 22, "sound": "whoosh",
            "ability": {"glide": {"secs": 5.0, "gravity": 0.3},
                        "shield": {"secs": 5.0, "amount": 30}}},
           [["+", "Float for 5 seconds: about a third of the usual gravity"],
            ["+", "A 30 point shield while it is open"],
            ["-", "22 second cooldown"]], rarity="rare")
def _():
    green = "#2f8a3a"
    parts = [
        part("cyl", [0, 0.30, 0.10], [0.05, 0.90, 0.05], "#5a3a22"),
        place("hook", [0, -0.16, 0.06], [0.30, 0.30, 0.30], "#5a3a22", anchor=[0, 0, 0],
              r=[PI, 0, 0]),
        place("hemi", [0, 0.72, 0.10], [1.20, 0.60, 1.20], green, anchor=[0, 0, 0],
              decal="felt", wrap=True),
        part("cyl", [0, 1.06, 0.10], [0.05, 0.10, 0.05], GOLD, m="metal"),
    ]
    parts += around(8, 0.60, 0.72, lambda a, x, z: part(
        "sph", [x, 0.72, z + 0.10], [0.06, 0.06, 0.06], GOLD, m="metal"))
    parts += around(4, 0.42, 0.82, lambda a, x, z: _shamrock(
        [x * 0.9, 0.86, z * 0.9 + 0.10], 0.18, SHAMROCK, r=[-0.9, a, 0]))
    return parts


SP23.effect("rainbow_road", name="Rainbow Road", rate=3.0, life=[2.0, 2.8],
            size=[0.40, 0.56], grow=0.1, gravity=0.0, spread=0.2, rise=[0.1, 0.3],
            blend="normal", spin=0.0, colors=["#ffffff"], shape="sp_rainbow", radius=0.7,
            orbit=1.2, upright=True, wobble=0.2)
SP23.effect("sun_shower", name="Sun Shower", rate=7.0, life=[1.2, 1.8],
            size=[0.14, 0.22], grow=0.0, gravity=-2.4, spread=0.7, rise=[-0.2, 0.0],
            blend="normal", spin=0.0, colors=["#9fd8ff", "#dff6ff", "#ffe066"],
            shapes=["sp_raindrop", "sp_raindrop", "spark"], radius=0.8)
SP23.opening(
    sky={"top": "#0e1e3a", "horizon": "#3a6a9a", "sun": [0.3, 0.8, 0.5], "clouds": 0.4,
         "tint": "#dff6ff"},
    ambient="#7a8aa8", beam="#ffe066", seep="sun_shower", after="rainbow_road",
    burst=["#ff5a5a", "#ffb347", "#ffe066", "#6be08a", "#5aa8ff"],
    pieces=[{"shape": "sp_coin", "colors": ["#ffd34a", "#f2c230"], "blend": "normal"},
            {"shape": "sp_rainbow", "colors": ["#ffffff"], "blend": "normal"},
            {"shape": "sp_cloud", "colors": ["#ffffff", "#dff6ff"], "blend": "normal"},
            {"shape": "shamrock", "colors": ["#4fc46e", "#2f8a3a"], "blend": "normal"}],
    backdrop="sp_rainbow", title_wait="The rain is easing off...",
    title_shake="Somebody is at the end of the rainbow...")
SP23.award("Rainbow's End", ["Puddle Hopper", "Rain Dancer", "Rainbow Chaser", "Gold Digger",
                             "Keeper of the Pot", "The End of the Rainbow"],
           "Opened Pots o' Gold at Rainbow's End, St. Patrick's Day 2023.", "em_rainbow",
           "clover")
SP23.bundle("pair", "Pot and Key", 1, 1050, "One Pot o' Gold, one Rainbow Key.")
SP23.bundle("hoard", "Double Rainbow", 3, 3000, "Three pots, three keys. Saves 300.")

EVENTS = [SP22, SP23]
