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


# ============================================================ 2024
STONE = "#8a8f88"
MOSS = "#5a8a2a"
BRONZE = "#b07a3a"
CELT_GOLD = "#e8b23a"
WOAD = "#2a4ab0"
DRUID = "#2f5a34"
RAVEN = "#16161c"


def _moss(at, k=1.0, n=4):
    """A cushion of moss: a few flattened green lumps."""
    x, y, z = at
    out = []
    for i in range(n):
        a = i * 2.4
        out.append(part("sph", [x + math.cos(a) * 0.10 * k, y + 0.01 * (i % 2), z + math.sin(a) * 0.08 * k],
                        [0.26 * k, 0.10 * k, 0.22 * k], MOSS if i % 2 else shade(MOSS, 0.8),
                        decal="sp_moss", wrap=True))
    return out


def _torc(at, k=1.0, r=None, c=CELT_GOLD):
    """A gold torc: a twisted neck ring open at the front, a knob on each
    end.  Stands in the XY plane facing +Z (turn it with ``r``)."""
    x, y, z = at
    out = [place("horseshoe", [x, y, z], [k, k, k], c, r=r, m="metal", decal="sp_twist",
                 wrap=True)]
    for s in (1, -1):
        off = [0.235 * k * s, -0.31 * k, 0]
        if r:
            off = rotate(off, r)
        out.append(part("sph", [x + off[0], y + off[1], z + off[2]], [0.16 * k, 0.16 * k, 0.16 * k],
                        c, m="metal"))
    return out


def _toadstool(at, k=1.0, lean=0.0):
    """A red toadstool with white spots."""
    x, y, z = at
    return [part("cyl", [x, y + 0.12 * k, z], [0.10 * k, 0.24 * k, 0.10 * k], "#f4ecd8",
                 [0, 0, lean]),
            place("hemi", [x - math.sin(lean) * 0.22 * k, y + 0.22 * k, z], [0.34 * k, 0.24 * k, 0.34 * k],
                  "#d0281c", anchor=[0, 0, 0], r=[0, 0, lean], decal="sp_toadstool", wrap=True)]


SP24 = Event(
    "stpatricks_2024", "stpatricks", 2024, "sp24",
    name="Blarney Hoard", title="The Blarney Hoard",
    blurb="St. Patrick's 2024 somebody kissed a mossy old stone at the top of the "
          "hill for luck, and the stone said thank you. Then it said a great deal "
          "more. By the time it stopped talking it had told them where the old kings "
          "buried their gold: right underneath it.",
    tagline="Kiss the stone. Find the gold. Never stop talking.",
    starts="2024-03-10", ends="2024-03-24",
    colors={"accent": "#e8b23a", "deep": "#0f2414", "glow": "#9aff6a"},
    family_effects=["sunbeam", "cursed_runes", "haunted_wisps"],
    hero_effect="ogham_glow", stencil="stencil_sp24")


@SP24.crate_model("Standing Stone Cist",
                  "A stone box under a standing stone on the hill, four slabs and a "
                  "capstone, carved with spirals older than the hill, mossed over, and "
                  "the old kings' gold glinting through the cracks. Holds the Blarney "
                  "Hoard set. Needs a Torc Key.",
                  hinge=[0, 0.34, -0.58], keyhole=[0, -0.04, 0.58])
def _():
    parts = [
        part("rbox", [0, -0.16, 0], [1.66, 0.84, 1.04], STONE, decal="sp_stone", wrap=True),
        part("box", [0, 0.24, 0], [1.50, 0.06, 0.90], "#ffd34a", m="neon"),
        # the lock: a bronze plate let into the front slab
        part("rbox", [0, -0.04, 0.545], [0.30, 0.32, 0.06], BRONZE, m="metal", decal="keyhole",
             lock=1),
        part("box", [0, -0.12, -0.53], [0.86, 0.50, 0.02], "#000000", [0, PI, 0],
             decal="stencil_sp24", a=-1),
        # spirals carved into the end slabs, ogham down the front corners
        part("box", [0.835, -0.14, 0], [0.70, 0.62, 0.02], "#000000", [0, PI / 2, 0],
             decal="sp_triskele", a=-1),
        part("box", [-0.835, -0.14, 0], [0.70, 0.62, 0.02], "#000000", [0, -PI / 2, 0],
             decal="sp_triskele", a=-1),
        part("box", [0.62, -0.16, 0.525], [0.22, 0.76, 0.02], "#000000", decal="sp_ogham", a=-1),
        part("box", [-0.62, -0.16, 0.525], [0.22, 0.76, 0.02], "#000000", decal="sp_ogham", a=-1),
        # the corner slabs standing proud of the box
        *[part("rbox", [0.80 * sx, -0.20, 0.48 * sz], [0.18, 0.96, 0.18], shade(STONE, 0.9),
               decal="sp_stone", wrap=True) for sx in (1, -1) for sz in (1, -1)],
        # a torc spilling out of the gap at the front
        *_torc([0.36, 0.20, 0.56], 0.40, r=[-0.4, 0.2, 0.3]),
        part("disc", [-0.30, 0.26, 0.54], [0.18, 0.18, 0.04], GOLD, [0.3, 0, 0], m="metal",
             decal="sp_coin"),
        # the capstone: one great slab, mossed, the spiral cut into its top
        part("rbox", [0, 0.46, 0], [1.92, 0.32, 1.24], STONE, [0.02, 0.04, -0.02], decal="sp_stone",
             wrap=True, lid=1),
        part("box", [0, 0.625, 0], [0.90, 0.90, 0.02], "#000000", [-PI / 2, 0, 0],
             decal="sp_triskele", a=-1, lid=1),
        *[dict(p, lid=1) for p in _moss([-0.66, 0.62, -0.36], 1.2, 5)],
        *[dict(p, lid=1) for p in _moss([0.70, 0.62, 0.30], 0.9, 4)],
        dict(part("sph", [0.62, 0.70, -0.40], [0.30, 0.20, 0.26], shade(STONE, 1.1), decal="sp_stone",
                  wrap=True), lid=1),
        dict(_shamrock([-0.50, 0.78, 0.36], [0.36, 0.36, 0.6], SHAMROCK, r=[-0.3, 0.4, 0]), lid=1),
    ]
    parts += _moss([0.86, -0.56, 0.40], 1.0, 3) + _moss([-0.84, -0.50, -0.42], 1.0, 3)
    return parts


@SP24.key_model("Torc Key",
                "A bronze key whose bow is a little gold torc with the spiral set in it. "
                "Opens one Standing Stone Cist. It hums when you hold it near a hill.",
                shoulder=-0.30)
def _():
    return [
        *_torc([-0.66, 0.0, 0], 0.62),
        part("disc", [-0.66, 0.02, 0], [0.30, 0.30, 0.06], BRONZE, m="metal", decal="sp_triskele"),
        part("cyl", [0.10, 0, 0], [0.09, 0.80, 0.09], BRONZE, [0, 0, PI / 2], m="metal"),
        part("torus", [-0.30, 0, 0], [0.18, 0.05, 0.18], CELT_GOLD, [0, 0, PI / 2], m="metal"),
        part("rbox", [0.36, -0.12, 0], [0.06, 0.20, 0.08], BRONZE, m="metal"),
        part("rbox", [0.44, -0.10, 0], [0.06, 0.16, 0.08], BRONZE, m="metal"),
        part("rbox", [0.52, -0.14, 0], [0.06, 0.24, 0.08], BRONZE, m="metal"),
    ]


@SP24.hat("hoard_crown", "Crown of the High King",
          "A gold crown out of the hoard, knotwork all round, red enamel on every "
          "point and the spiral on the front. The last man who wore it was buried in "
          "it, which is how it got into the hoard.", "legendary")
def _():
    parts = [
        cap(-0.30, 0.22, EMERALD, grow=-0.10, decal="felt", wrap=True),
        ringband(-0.02, 0.32, CELT_GOLD, margin=0.05, m="metal", decal="sp_knotband", wrap=True),
    ]
    parts += around(8, 0.93, 0.0, lambda a, x, z: [
        place("tri", [x, 0.32, z * 0.97], [0.34, 0.40, 0.5], CELT_GOLD, r=[0, a, 0], m="metal"),
        part("sph", [x * 1.02, 0.42, z * 0.99], [0.10, 0.10, 0.08], "#c42a2a", m="glass")])
    parts += [part("disc", [0, -0.02, 0.99], [0.34, 0.34, 0.06], CELT_GOLD, m="metal",
                   decal="sp_triskele")]
    return parts


@SP24.hat("druid_hood", "Druid's Hood",
          "A deep green hood with a point, oak leaves round the brow and a sprig of "
          "mistletoe tucked in. The druids knew where the hoard was all along. They "
          "just never told anyone.", "rare", hair="hide")
def _():
    parts = [
        place("hairlong", [0, -0.64, -0.06], [1.60, 1.40, 1.58], DRUID, anchor=[0, 0, 0],
              decal="felt", wrap=True),
        place("cone", [0, 0.06, -0.62], [0.50, 0.80, 0.50], DRUID, r=[-1.1, 0, 0], decal="felt",
              wrap=True),
        part("rbox", [0, -1.24, -0.30], [1.70, 0.20, 1.10], shade(DRUID, 0.85), decal="felt", wrap=True),
    ]
    for k in range(9):
        a = -1.1 + k * 0.275
        parts.append(place("leaf", [math.sin(a) * 0.90, -0.16, math.cos(a) * 0.86], [0.7, 0.30, 1.0],
                           "#5a7a2a" if k % 2 else "#3a6a1e", r=[0.4, a, PI / 2 + 0.3 * (k % 2)]))
    parts += [place("leaf", [0.56, 0.0, 0.66], [0.6, 0.24, 1.0], "#8ab84a", r=[0.6, 0.6, 0.6]),
              part("sph", [0.52, 0.02, 0.76], [0.07, 0.07, 0.07], "#f4f2ea", m="glass"),
              part("sph", [0.60, -0.04, 0.74], [0.07, 0.07, 0.07], "#f4f2ea", m="glass"),
              part("sph", [0.56, 0.06, 0.70], [0.06, 0.06, 0.06], "#f4f2ea", m="glass")]
    return parts


@SP24.hat("blarney_stone", "Piece of the Blarney Stone",
          "A chunk off the Blarney Stone, moss and all, with a big red kiss on the "
          "front where somebody got there first. Wear it and you will never be lost "
          "for words. Anyone near you will be lost for theirs.", "uncommon",
          hair="show")
def _():
    parts = [
        part("rbox", [0, 0.36, 0], [1.34, 0.74, 1.10], STONE, [0.04, 0.10, -0.03], decal="sp_stone",
             wrap=True),
        part("box", [0.02, 0.36, 0.555], [0.56, 0.42, 0.02], "#000000", [0.04, 0.10, -0.03],
             decal="sp_kiss", a=-1),
    ]
    parts += _moss([-0.30, 0.74, -0.20], 1.2, 5) + _moss([0.44, 0.70, 0.30], 0.8, 3)
    parts += [_shamrock([0.40, 0.92, -0.20], [0.30, 0.30, 0.5], SHAMROCK, r=[0, 0.5, 0.2])]
    return parts


@SP24.hat("flat_cap", "Donegal Flat Cap",
          "A Donegal tweed flat cap with a shamrock tucked in the band, for "
          "standing at the bar telling a story that is mostly true.", "uncommon")
def _():
    tweed = "#6a6452"
    return [
        cap(-0.30, 0.06, tweed, grow=0.04, decal="sp_tweed", wrap=True),
        part("sph", [0, 0.16, 0.10], [1.80, 0.34, 1.76], tweed, [0.16, 0, 0], decal="sp_tweed",
             wrap=True),
        part("cyl", [0, 0.17, 0.06], [0.14, 0.04, 0.14], shade(tweed, 0.8)),
        place("peak", [0, -0.18, 0.06], [1.86, 1.0, 1.80], shade(tweed, 0.85), anchor=[0, 0, 0],
              decal="sp_tweed", wrap=True),
        _shamrock([0.82, -0.06, 0.30], [0.30, 0.30, 0.5], SHAMROCK, r=[0, PI / 2, 0.2]),
    ]


@SP24.hat("fairy_ring", "Fairy Ring",
          "A ring of toadstools in a ring of moss, and the little lights dancing "
          "round it. Step inside a fairy ring and you lose a hundred years. Wear one "
          "and you only lose track of time.", "rare", hair="show")
def _():
    parts = [place("ring", [0, -0.02, 0], [1.60, 0.5, 1.56], MOSS, anchor=[0, 0, 0],
                   decal="sp_moss", wrap=True)]
    parts += around(9, 0.68, 0.0, lambda a, x, z: _toadstool(
        [x, 0.06, z], 0.9 + 0.35 * ((int(round(a * 9 / TAU))) % 3) / 2, 0.15 * math.sin(a * 3)))
    parts += around(5, 0.40, 0.0, lambda a, x, z: part(
        "sph", [x, 0.60 + 0.12 * math.sin(a * 2), z], [0.10, 0.10, 0.10],
        "#d8ff8a" if int(round(a * 5 / TAU)) % 2 else "#ffe88a", m="neon", spin=1.5), start=0.3)
    return parts


@SP24.hat("bronze_helm", "Bronze Horned Helm",
          "A bronze war-helm with two short horns, spirals hammered all over it and "
          "studs of red enamel. Found in a river. Nobody has ever found the "
          "warrior.", "rare")
def _():
    parts = [
        dome(-0.52, 1.00, BRONZE, t="capcrown", m="metal", decal="sp_bronze", wrap=True),
        ringband(-0.46, 0.12, shade(BRONZE, 0.8), margin=0.08, m="metal"),
        part("rbox", [0, 0.48, 0], [0.12, 0.10, 1.10], shade(BRONZE, 1.15), m="metal"),
    ]
    for s in (1, -1):
        # each horn's root sits on the dome's shoulder, its middle half its
        # length further out along the slant
        d = [math.sin(0.62) * s, math.cos(0.62)]
        parts += [place("cone", [0.72 * s + d[0] * 0.45, 0.12 + d[1] * 0.45, 0], [0.42, 0.90, 0.42],
                        BRONZE, r=[0, 0, -0.62 * s], m="metal", decal="sp_bronze", wrap=True),
                  part("sph", [0.72 * s + d[0] * 0.90, 0.12 + d[1] * 0.90, 0], [0.14, 0.14, 0.14],
                       CELT_GOLD, m="metal")]
    parts += around(6, 0.98, -0.48, lambda a, x, z: part(
        "sph", [x, -0.48, z * 0.97], [0.10, 0.10, 0.08], "#c42a2a", m="glass"), start=PI / 6)
    return parts


@SP24.hat("raven", "The Morrigan's Raven",
          "A great black raven on your head, wings half open, watching the battle "
          "from on high. In the old stories she picked the winners. She has picked "
          "you. Probably.", "rare", hair="show")
def _():
    parts = [
        part("sph", [0, 0.36, -0.06], [0.56, 0.58, 0.82], RAVEN, [0.35, 0, 0], m="glass"),
        part("sph", [0, 0.78, 0.30], [0.40, 0.38, 0.42], RAVEN, m="glass"),
        place("cone", [0, 0.76, 0.62], [0.12, 0.32, 0.12], "#2a2a30", r=[PI / 2 + 0.2, 0, 0]),
        part("sph", [0.12, 0.84, 0.44], [0.07, 0.07, 0.05], "#d8b23a", m="neon"),
        part("sph", [-0.12, 0.84, 0.44], [0.07, 0.07, 0.05], "#d8b23a", m="neon"),
        place("wedge", [0, 0.16, -0.60], [0.40, 0.08, 0.50], RAVEN, r=[0.6, 0, 0], m="glass"),
        part("rbox", [0.12, 0.03, 0.10], [0.10, 0.06, 0.24], "#2a2a30"),
        part("rbox", [-0.12, 0.03, 0.10], [0.10, 0.06, 0.24], "#2a2a30"),
    ]
    for s in (1, -1):
        parts += [place("wing", [0.22 * s, 0.50, -0.06], [1.10, 0.90, 1.0], RAVEN,
                        anchor=[-0.5, 0.0, 0], r=[0, 0.0 if s > 0 else PI, 0.40], m="glass")]
    return parts


@SP24.back("celtic_harp", "Harp of the Bards",
           "The old Irish harp, willow and brass, carved with knotwork and strung "
           "with gold, slung across your back. It plays itself when you are not "
           "looking. It knows a lot of very long songs.", "legendary")
def _():
    wood = "#6a3a1e"
    z = -0.36
    parts = straps("#5a3a22") + [
        part("rbox", [0, 0.40, -0.12], [0.40, 0.30, 0.16], "#5a3a22"),
        # the soundbox: a long tapered box up the left side
        rod([-0.56, -0.70, z], [-0.30, 1.20, z], 0.36, wood, t="rbox", decal="sp_knotband",
            wrap=True),
        # the neck curving over the top, and the forepillar down the right
        rod([-0.30, 1.20, z], [0.20, 1.34, z], 0.16, wood, t="rbox"),
        rod([0.20, 1.34, z], [0.58, 1.00, z], 0.16, wood, t="rbox"),
        rod([0.58, 1.00, z], [0.66, 0.30, z], 0.18, wood, t="rbox"),
        rod([0.66, 0.30, z], [0.36, -0.60, z], 0.20, wood, t="rbox"),
        rod([0.36, -0.60, z], [-0.52, -0.70, z], 0.14, wood, t="rbox"),
        part("sph", [0.20, 1.36, z], [0.16, 0.16, 0.16], CELT_GOLD, m="metal"),
        part("disc", [0.64, 0.50, z - 0.11], [0.26, 0.26, 0.04], CELT_GOLD, [0, PI, 0], m="metal",
             decal="sp_triskele"),
    ]
    for i in range(8):
        t = (i + 0.5) / 8
        bx = -0.54 + 0.24 * t * 1.9
        by = -0.62 + 1.80 * t
        tx = bx + 0.02
        ty = min(1.28, 1.20 + 0.12 * math.sin(t * PI)) if t < 0.5 else 1.30 - (t - 0.5) * 0.40
        parts.append(rod([bx + 0.14, by, z - 0.02], [min(0.58, bx + 0.14 + (1 - t) * 0.0 + t * 0.62), ty - 0.06 if t > 0.5 else 1.22, z - 0.02],
                         0.018, GOLD, m="metal"))
    return parts


@SP24.back("celtic_shield", "Shield of the Fianna",
           "A round bronze shield with the triple spiral on its face and a great "
           "boss in the middle, hung on your back. Fionn's warriors carried them. "
           "Fionn's warriors also had to leap a branch as high as their brow, so "
           "count yourself lucky.", "rare")
def _():
    return straps("#5a3a22") + [
        part("disc", [0, 0.16, -0.20], [1.80, 1.80, 0.16], BRONZE, [0, PI, 0], m="metal",
             decal="sp_shield"),
        part("torus", [0, 0.16, -0.24], [1.82, 0.06, 1.82], shade(BRONZE, 0.8), [PI / 2, 0, 0],
             m="metal"),
        place("hemi", [0, 0.16, -0.28], [0.44, 0.40, 0.44], CELT_GOLD, anchor=[0, 0, 0],
              r=[-PI / 2, 0, 0], m="metal"),
        rod([-0.70, -0.60, -0.10], [0.80, 1.40, -0.10], 0.06, "#6a4a2e"),
        place("cone", [0.86, 1.48, -0.10], [0.12, 0.30, 0.06], BRONZE, r=[0, 0, -0.64], m="metal"),
    ]


@SP24.hairdo("druid_braids", "Druid's Braids",
             "Long silver hair, a braid down each side bound with gold rings, the "
             "way the old bards wore it.", "uncommon")
def _():
    silver = "#c9ccd2"
    parts = [place("hairlong", [0, 0, 0], [1.04, 1.04, 1.04], silver, anchor=[0, 0, 0],
                   decal="strands", wrap=True)]
    for s in (1, -1):
        for k in range(6):
            parts.append(part("sph", [0.58 * s, -0.36 - k * 0.11, 0.10], [0.15 - k * 0.008, 0.13, 0.14],
                              silver if k % 2 else shade(silver, 0.88), [0, 0, 0.5 if k % 2 else -0.5]))
        parts += [part("cyl", [0.58 * s, -0.58, 0.10], [0.17, 0.05, 0.17], CELT_GOLD, m="metal"),
                  part("cyl", [0.58 * s, -0.86, 0.10], [0.15, 0.05, 0.15], CELT_GOLD, m="metal")]
    return parts


@SP24.hairdo("mossy_mop", "Mossy Mop",
             "Hair gone green with moss from sleeping out on the hill, with a "
             "toadstool or two coming up and a snail who has moved in.", "uncommon")
def _():
    parts = [place("hairmid", [0, 0, 0], [1.04, 1.04, 1.04], MOSS, anchor=[0, 0, 0],
                   decal="sp_moss", wrap=True)]
    parts += around(7, 0.30, 0.0, lambda a, x, z: part(
        "sph", [x, 0.60, z - 0.02], [0.26, 0.14, 0.26], shade(MOSS, 0.85 + 0.1 * math.sin(a * 3)),
        decal="sp_moss", wrap=True))
    parts += _toadstool([0.22, 0.62, 0.10], 0.55, 0.2) + _toadstool([-0.20, 0.62, -0.18], 0.45, -0.3)
    parts += [part("sph", [-0.36, 0.56, 0.24], [0.14, 0.14, 0.08], "#a0703a", [0, PI / 2, 0],
                   decal="sp_snail"),
              part("capsule", [-0.30, 0.52, 0.30], [0.06, 0.20, 0.06], "#c8b89a", [PI / 2, 0, 0])]
    return parts


SP24.face("gift_of_the_gab", "Gift of the Gab",
          "Eyebrows up, one eye winking and a mouth going nineteen to the dozen. You "
          "kissed the stone. Everyone knows. You told them.", [
              {"k": "arc", "x": -0.20, "y": -0.12, "r": 0.06, "a0": 0.55, "a1": 0.95, "w": 0.035,
               "c": "#16171b"},
              {"k": "ellipse", "x": 0.20, "y": -0.13, "w": 0.09, "h": 0.12, "c": "#16171b"},
              {"k": "line", "x1": -0.30, "y1": -0.30, "x2": -0.10, "y2": -0.26, "w": 0.03,
               "c": "#16171b"},
              {"k": "line", "x1": 0.10, "y1": -0.30, "x2": 0.30, "y2": -0.34, "w": 0.03,
               "c": "#16171b"},
              {"k": "ellipse", "x": -0.02, "y": 0.14, "w": 0.26, "h": 0.18, "c": "#16171b"},
              {"k": "ellipse", "x": -0.02, "y": 0.19, "w": 0.16, "h": 0.07, "c": "#e05a6a"},
              {"k": "line", "x1": 0.20, "y1": 0.08, "x2": 0.30, "y2": 0.03, "w": 0.02,
               "c": "#16171b"},
              {"k": "line", "x1": 0.21, "y1": 0.14, "x2": 0.33, "y2": 0.14, "w": 0.02,
               "c": "#16171b"},
              {"k": "line", "x1": 0.20, "y1": 0.20, "x2": 0.30, "y2": 0.25, "w": 0.02,
               "c": "#16171b"},
          ], "uncommon")
SP24.face("woad_warrior", "Woad Warrior",
          "Blue woad spirals round the eyes and a stripe across the face, and the "
          "look of somebody about to run down a hill shouting.", [
              {"k": "arc", "x": -0.20, "y": -0.13, "r": 0.13, "a0": 0.0, "a1": 0.85, "w": 0.04,
               "c": "#2a4ab0"},
              {"k": "arc", "x": 0.20, "y": -0.13, "r": 0.13, "a0": 0.15, "a1": 1.0, "w": 0.04,
               "c": "#2a4ab0"},
              {"k": "arc", "x": -0.20, "y": -0.13, "r": 0.20, "a0": 0.5, "a1": 1.0, "w": 0.03,
               "c": "#2a4ab0"},
              {"k": "arc", "x": 0.20, "y": -0.13, "r": 0.20, "a0": 0.0, "a1": 0.5, "w": 0.03,
               "c": "#2a4ab0"},
              {"k": "line", "x1": -0.45, "y1": 0.02, "x2": 0.45, "y2": 0.02, "w": 0.05,
               "c": "#2a4ab0"},
              {"k": "ellipse", "x": -0.20, "y": -0.13, "w": 0.07, "h": 0.10, "c": "#16171b"},
              {"k": "ellipse", "x": 0.20, "y": -0.13, "w": 0.07, "h": 0.10, "c": "#16171b"},
              {"k": "line", "x1": -0.30, "y1": -0.30, "x2": -0.08, "y2": -0.22, "w": 0.04,
               "c": "#16171b"},
              {"k": "line", "x1": 0.30, "y1": -0.30, "x2": 0.08, "y2": -0.22, "w": 0.04,
               "c": "#16171b"},
              {"k": "poly", "pts": [[-0.20, 0.14], [0.20, 0.14], [0.16, 0.24], [-0.16, 0.24]],
               "c": "#16171b"},
              {"k": "poly", "pts": [[-0.18, 0.15], [0.18, 0.15], [0.17, 0.18], [-0.17, 0.18]],
               "c": "#ffffff"},
          ], "rare")
SP24.shirt("knotwork_tunic", "Knotwork Tunic",
           "A green wool tunic with a gold knotwork collar and hem and a torc at the "
           "throat, the kind of thing a king wears to be buried in, or to the pub.",
           {"torso": "#2f6a3a", "arms": "#2f6a3a", "decal": "sp_tee_knot", "weave": "sp_linen",
            "stripe": CELT_GOLD}, "rare")
SP24.pants("saffron_kilt", "Saffron Kilt",
           "A saffron kilt, heavy pleats, knee socks and brogues. Traditional. Draughty.",
           {"legs": "#d89a2a", "weave": "sp_pleats", "length": 0.55, "skin": "#ece6d4",
            "cuff": "#3a2a1e"})
SP24.belt("ring_belt", "Belt of Bronze Rings",
          "A leather belt hung with bronze rings, a pouch either side of the buckle "
          "for whatever falls out of the hoard.",
          {"band": "#5a3a22", "buckle": BRONZE, "width": 0.22, "metal": True, "pouch": True,
           "weave": "sp_bronze"})


@SP24.weapon("carnyx", "Carnyx of the Gab",
             "The old Celtic war-horn, bronze, as tall as a man, with a boar's head "
             "for a bell. Blow it and everyone in front of you is so busy listening "
             "they forget how to do anything clever.",
             {"kind": "cone", "damage": 10, "rpm": 40, "mag": 3, "reload": 2.6, "range": 16.0,
              "auto": False, "sound": "horn", "recoil": 2.0, "reserve": 18,
              "cone": {"angle": 0.50, "push": 12, "lift": 4, "color": "#e8b23a"},
              "on_hit": {"silence": 3.0}},
             [["+", "Silences everyone in front of you for 3 seconds: no abilities, no gear"],
              ["+", "...and gives them a little shove"],
              ["-", "10 damage"],
              ["-", "16 stud reach, three blasts to a breath"]], rarity="legendary")
def _():
    parts = [
        part("rbox", [0, -0.12, -0.04], [0.16, 0.36, 0.22], "#5a3a22", [-0.2, 0, 0]),
        rod([0, -0.30, -0.50], [0, 0.30, 0.30], 0.12, BRONZE, m="metal"),
        rod([0, 0.30, 0.30], [0, 1.10, 0.62], 0.12, BRONZE, m="metal"),
        part("torus", [0, 0.70, 0.46], [0.18, 0.04, 0.18], CELT_GOLD, [0.4, 0, 0], m="metal"),
        # the boar's head bell
        part("sph", [0, 1.22, 0.74], [0.40, 0.34, 0.56], BRONZE, [0.5, 0, 0], m="metal",
             decal="sp_bronze", wrap=True),
        place("cone", [0, 1.40, 1.06], [0.24, 0.36, 0.22], BRONZE, r=[1.0, 0, 0], m="metal"),
        part("sph", [0.14, 1.36, 0.86], [0.07, 0.07, 0.05], "#c42a2a", m="glass"),
        part("sph", [-0.14, 1.36, 0.86], [0.07, 0.07, 0.05], "#c42a2a", m="glass"),
        place("cone", [0.20, 1.44, 0.58], [0.10, 0.24, 0.06], BRONZE, r=[-0.4, 0, -0.4], m="metal"),
        place("cone", [-0.20, 1.44, 0.58], [0.10, 0.24, 0.06], BRONZE, r=[-0.4, 0, 0.4], m="metal"),
        part("rbox", [0, 1.04, 0.92], [0.24, 0.04, 0.24], "#2a1810", [0.5, 0, 0]),
    ]
    return parts


@SP24.weapon("lughs_sling", "Sling of Lugh",
             "The sling Lugh of the Long Arm used to put out the eye of Balor. One "
             "stone at a time, and if it finds a head the head stays still for a good "
             "long while.",
             {"kind": "hitscan", "damage": 42, "headshot": 2.5, "rpm": 45, "mag": 1,
              "reload": 1.3, "range": 260, "auto": False, "sound": "crack", "recoil": 1.4,
              "spread": 0.2, "reserve": 30, "tracer": "#c9ccd2",
              "on_headshot": {"stun": 1.5}},
             [["+", "Headshots do two and a half times the damage"],
              ["+", "...and stun for a second and a half"],
              ["-", "One stone at a time"],
              ["-", "Body shots only do 42"]], rarity="legendary")
def _():
    leather = "#7a5030"
    return [
        part("sph", [0, -0.04, 0.02], [0.14, 0.14, 0.14], leather),
        rod([0, -0.02, 0.0], [0.06, -0.30, 0.40], 0.035, leather),
        rod([0, -0.02, 0.0], [-0.06, -0.30, 0.40], 0.035, leather),
        part("sph", [0, -0.36, 0.46], [0.30, 0.18, 0.26], leather, decal="leather", wrap=True),
        part("sph", [0, -0.30, 0.46], [0.20, 0.18, 0.20], "#9a9a98", decal="sp_stone", wrap=True),
    ]


@SP24.weapon("ogham_stone", "Ogham Stone",
             "Raise a little standing stone cut with ogham. Your side, near it, heals "
             "a little every second; the other side, near it, cannot hide -- the "
             "stone tells everyone exactly where they are.",
             {"kind": "deploy", "cooldown": 28, "sound": "magic",
              "deploy": {"type": "banner", "radius": 12.0, "secs": 14.0, "limit": 1,
                         "color": "#9aff6a", "particle": "rune",
                         "ally": {"regen": [5, 1.0]}, "enemy": {"reveal": 1.2}}},
             [["+", "You and teammates within 12 studs heal 5 a second"],
              ["+", "Enemies within 12 studs are shown to your whole team"],
              ["-", "Stands for 14 seconds, where you put it"],
              ["-", "28 second cooldown"]], rarity="rare",
             deploy=lambda: [
                 part("rbox", [0, 1.10, 0], [0.70, 2.20, 0.46], STONE, [0, 0, 0.04], decal="sp_stone",
                      wrap=True),
                 part("box", [0.355, 1.10, 0], [0.42, 1.90, 0.02], "#000000", [0, PI / 2, 0],
                      decal="sp_ogham", a=-1),
                 part("box", [0, 1.30, 0.235], [0.56, 0.56, 0.02], "#000000", decal="sp_triskele",
                      a=-1),
                 *_moss([0.10, 2.20, 0.0], 1.1, 4)])
def _():
    return [
        part("rbox", [0, 0.20, 0.16], [0.34, 0.70, 0.24], STONE, decal="sp_stone", wrap=True),
        part("box", [0, 0.20, 0.285], [0.24, 0.56, 0.02], "#000000", decal="sp_ogham", a=-1),
        *_moss([0.04, 0.56, 0.16], 0.6, 3),
    ]


@SP24.gear("salmon_of_knowledge", "Salmon of Knowledge",
           "The salmon that ate the nine hazelnuts of wisdom. Fionn only burnt his "
           "thumb on it and knew everything ever after. Eat the whole thing and you "
           "will know exactly where to hit people.",
           {"kind": "consume", "cooldown": 30, "sound": "eat",
            "consume": {"heal": 20, "crit": [0.5, 6.0]}},
           [["+", "Half of your hits are critical for 6 seconds"],
            ["+", "Heals 20"],
            ["-", "30 second cooldown"]], rarity="rare")
def _():
    salmon = "#c9ced6"
    return [
        part("cyl", [0, -0.06, 0.20], [0.70, 0.04, 0.70], "#f4f2ea", m="glass"),
        part("sph", [0, 0.06, 0.20], [0.24, 0.20, 0.66], salmon, m="metal", decal="sp_scales",
             wrap=True),
        part("sph", [0, 0.02, 0.20], [0.18, 0.10, 0.56], "#f0a080"),
        place("tri", [0, 0.06, -0.20], [0.30, 0.24, 0.4], salmon, r=[PI / 2, 0, PI], m="metal"),
        part("sph", [0.08, 0.10, 0.44], [0.05, 0.05, 0.03], BLACK),
        part("sph", [-0.08, 0.10, 0.44], [0.05, 0.05, 0.03], BLACK),
        place("leaf", [0.24, 0.0, 0.10], [0.5, 0.24, 1.0], "#5a8a2a", r=[PI / 2, 0.6, 0]),
        part("sph", [-0.24, 0.0, 0.34], [0.10, 0.08, 0.10], "#a0703a"),
    ]


SP24.effect("ogham_glow", name="Ogham Glow", rate=2.2, life=[1.8, 2.4],
            size=[0.34, 0.48], grow=0.0, gravity=0.0, spread=0.3, rise=[0.1, 0.3],
            blend="add", spin=0.8, colors=["#e8b23a", "#9aff6a"], shape="sp_triskele",
            radius=0.8, orbit=1.6, wobble=0.3)
SP24.effect("bog_lights", name="Bog Lights", rate=3.0, life=[1.6, 2.4],
            size=[0.20, 0.32], grow=0.2, gravity=-0.2, spread=0.6, rise=[0.2, 0.4],
            blend="add", spin=0.0, colors=["#9aff6a", "#ffe88a", "#d8ff8a"], shape="wisp",
            radius=0.9, wobble=0.8)
SP24.opening(
    sky={"top": "#0a1a10", "horizon": "#4a6a3a", "sun": [0.2, 0.6, 0.6], "clouds": 0.6,
         "tint": "#e8ffd8"},
    ambient="#5a7a5a", beam="#ffd34a", seep="bog_lights", after="ogham_glow",
    burst=["#e8b23a", "#9aff6a", "#ffffff", "#5a8a2a"],
    pieces=[{"shape": "sp_coin", "colors": ["#ffd34a", "#e8b23a"], "blend": "normal"},
            {"shape": "sp_triskele", "colors": ["#e8b23a", "#9aff6a"], "blend": "add"},
            {"shape": "shamrock", "colors": ["#4fc46e", "#2f8a3a"], "blend": "normal"},
            {"shape": "wisp", "colors": ["#d8ff8a"], "blend": "add"}],
    backdrop="sp_stones", title_wait="The stone is clearing its throat...",
    title_shake="It knows where the gold is...")
SP24.award("Blarney Hoard", ["Wanderer", "Stone Kisser", "Silver Tongue", "Hoard Finder",
                             "Keeper of the Stones", "High King of the Hoard"],
           "Opened Standing Stone Cists under the hill, St. Patrick's 2024.", "em_horseshoe",
           "clover")
SP24.bundle("pair", "Cist and Torc", 1, 1050, "One Standing Stone Cist, one Torc Key.")
SP24.bundle("hoard", "The Whole Hoard", 3, 3000, "Three cists, three keys. Saves 300.")

# ============================================================ 2025
FIDDLE = "#8a3a14"
EBONY = "#1a1414"
ARAN = "#ece4cc"
CASE = "#1a3a24"
DRUMSKIN = "#e8dcc0"
ASH = "#d8b888"


def _fiddle(k=1.0, c=FIDDLE):
    """A fiddle lying in the XY plane, its belly to +Z and its scroll up
    +Y, middle of the body at the origin.  Every part is square to the
    axes, so ``at_frame`` can turn the whole thing."""
    return [
        part("sph", [0, 0.26 * k, 0], [0.52 * k, 0.48 * k, 0.16 * k], c, decal="sp_fiddlewood", wrap=True),
        part("sph", [0, -0.22 * k, 0], [0.64 * k, 0.60 * k, 0.16 * k], c, decal="sp_fiddlewood", wrap=True),
        part("rbox", [0, 0.02 * k, 0], [0.40 * k, 0.30 * k, 0.15 * k], c),
        part("box", [0, -0.02 * k, 0.081 * k], [0.46 * k, 0.70 * k, 0.01 * k], "#000000", decal="sp_fholes",
             a=-1),
        part("rbox", [0, 0.56 * k, 0.07 * k], [0.10 * k, 0.86 * k, 0.04 * k], EBONY),
        part("rbox", [0, 0.86 * k, 0.0], [0.10 * k, 0.40 * k, 0.08 * k], c),
        part("rbox", [0, 1.10 * k, 0.0], [0.12 * k, 0.20 * k, 0.10 * k], c),
        part("sph", [0, 1.24 * k, 0.02 * k], [0.14 * k, 0.14 * k, 0.12 * k], c),
        part("rbox", [0.09 * k, 1.08 * k, 0], [0.08 * k, 0.03 * k, 0.03 * k], EBONY),
        part("rbox", [-0.09 * k, 1.14 * k, 0], [0.08 * k, 0.03 * k, 0.03 * k], EBONY),
        part("rbox", [0, -0.12 * k, 0.10 * k], [0.18 * k, 0.04 * k, 0.04 * k], "#e8d0a0"),
        part("rbox", [0, -0.38 * k, 0.09 * k], [0.12 * k, 0.22 * k, 0.03 * k], EBONY),
        part("rbox", [0.025 * k, 0.30 * k, 0.10 * k], [0.006 * k, 1.20 * k, 0.006 * k], "#e8e8e8"),
        part("rbox", [-0.025 * k, 0.30 * k, 0.10 * k], [0.006 * k, 1.20 * k, 0.006 * k], "#e8e8e8"),
    ]


def _bow(p0, p1, k=1.0):
    """A fiddle bow from its frog at ``p0`` to its tip at ``p1``."""
    return [rod(p0, p1, 0.03 * k, "#5a2a10"),
            rod([p0[0], p0[1] - 0.05 * k, p0[2]], [p1[0], p1[1] - 0.05 * k, p1[2]], 0.02 * k, "#f4f0e0"),
            part("rbox", list(p0), [0.06 * k, 0.08 * k, 0.06 * k], EBONY)]


SP25 = Event(
    "stpatricks_2025", "stpatricks", 2025, "sp25",
    name="Emerald Jamboree", title="The Emerald Jamboree",
    blurb="St. Patrick's 2025 somebody strung lamps across the village green, "
          "somebody else brought a fiddle, and by nine o'clock there was a céilí going "
          "that nobody could stop. It ran for a week. The fiddler never once put the "
          "fiddle down, and nobody ever saw who he was.",
    tagline="One more reel. Just one more.",
    starts="2025-03-10", ends="2025-03-24",
    colors={"accent": "#9aff6a", "deep": "#0c2014", "glow": "#ffd34a"},
    family_effects=["sunbeam", "starstruck", "bubbly"],
    hero_effect="ceili_notes", stencil="stencil_sp25")


@SP25.crate_model("Fiddle Case",
                  "A battered old fiddle case, green leather gone black at the corners, "
                  "plastered with stickers from every céilí in the country and two "
                  "brass latches that never quite shut. Holds the Emerald Jamboree set. "
                  "Needs a Tuning Key.",
                  hinge=[0, 0.10, -0.46], keyhole=[0, -0.12, 0.47])
def _():
    parts = [
        # the shell: the wide end for the fiddle's body, the narrow for its neck
        part("rbox", [-0.34, -0.24, 0], [1.10, 0.62, 0.92], CASE, decal="sp_casestickers", wrap=True),
        part("rbox", [0.52, -0.24, 0], [0.76, 0.56, 0.62], CASE, decal="sp_casestickers", wrap=True),
        part("cyl", [-0.88, -0.24, 0], [0.62, 0.60, 0.92], CASE, [0, 0, PI / 2]),
        part("rbox", [-0.20, 0.06, 0], [1.40, 0.04, 0.86], "#ffd34a", m="neon"),
        part("rbox", [0, -0.06, 0.455], [1.40, 0.04, 0.02], BRASS, m="metal"),
        # the lock and the two latches either side
        part("rbox", [0, -0.12, 0.475], [0.26, 0.24, 0.05], BRASS, m="metal", decal="keyhole", lock=1),
        part("rbox", [-0.62, -0.08, 0.475], [0.18, 0.20, 0.05], BRASS, m="metal"),
        part("rbox", [0.58, -0.08, 0.32], [0.18, 0.20, 0.05], BRASS, m="metal"),
        part("box", [-0.30, -0.30, -0.465], [0.80, 0.44, 0.02], "#000000", [0, PI, 0],
             decal="stencil_sp25", a=-1),
        # the lid, its stickers and the carrying handle
        part("rbox", [-0.34, 0.24, 0], [1.12, 0.30, 0.94], CASE, decal="sp_casestickers", wrap=True,
             lid=1),
        part("rbox", [0.52, 0.22, 0], [0.78, 0.26, 0.64], CASE, decal="sp_casestickers", wrap=True,
             lid=1),
        part("cyl", [-0.88, 0.24, 0], [0.30, 0.60, 0.94], CASE, [0, 0, PI / 2], lid=1),
        part("box", [-0.30, 0.395, 0.0], [0.90, 0.70, 0.02], "#000000", [-PI / 2, 0, 0],
             decal="sp_stickers", a=-1, lid=1),
        rod([-0.30, 0.26, 0.48], [-0.30, 0.34, 0.60], 0.06, "#3a2a1e", lid=1),
        rod([0.10, 0.26, 0.48], [0.10, 0.34, 0.60], 0.06, "#3a2a1e", lid=1),
        rod([-0.30, 0.34, 0.60], [0.10, 0.34, 0.60], 0.08, "#3a2a1e", lid=1),
    ]
    # corner guards
    for x in (-0.88, 0.88):
        parts.append(part("rbox", [x, -0.50, 0], [0.12, 0.10, 0.70 if x > 0 else 0.94], BRASS, m="metal"))
    return parts


@SP25.key_model("Tuning Key",
                "A brass key whose bow is a fiddle's scroll and pegbox, two pegs and "
                "all. Opens one Fiddle Case. Turn it the wrong way and every fiddle in "
                "earshot goes flat.", shoulder=-0.34)
def _():
    return [
        part("torus", [-0.80, 0.02, 0], [0.26, 0.09, 0.26], FIDDLE, [PI / 2, 0, 0]),
        part("torus", [-0.82, 0.04, 0], [0.13, 0.07, 0.13], shade(FIDDLE, 0.85), [PI / 2, 0, 0]),
        part("sph", [-0.83, 0.05, 0], [0.08, 0.08, 0.12], FIDDLE),
        part("rbox", [-0.56, 0, 0], [0.30, 0.14, 0.12], FIDDLE),
        part("rbox", [-0.58, 0, 0.10], [0.04, 0.04, 0.16], EBONY),
        part("rbox", [-0.50, 0, -0.10], [0.04, 0.04, 0.16], EBONY),
        part("sph", [-0.58, 0, 0.19], [0.08, 0.08, 0.04], EBONY),
        part("sph", [-0.50, 0, -0.19], [0.08, 0.08, 0.04], EBONY),
        part("cyl", [0.08, 0, 0], [0.09, 0.84, 0.09], BRASS, [0, 0, PI / 2], m="metal"),
        part("torus", [-0.34, 0, 0], [0.18, 0.05, 0.18], GOLD, [0, 0, PI / 2], m="metal"),
        part("rbox", [0.38, -0.12, 0], [0.08, 0.20, 0.08], BRASS, m="metal"),
        part("rbox", [0.50, -0.10, 0], [0.08, 0.16, 0.08], BRASS, m="metal"),
    ]


@SP25.hat("maypole_crown", "Maypole Crown",
          "A little maypole standing up out of your head, gold ball on top, eight "
          "ribbons wound down to a ring of spring flowers round your brow. Stand still "
          "and people start dancing round you.", "legendary", hair="show")
def _():
    colours = [EMERALD, "#f4f6f8", "#ff8a2a", LEP_GOLD, "#d0281c", "#3a6ad6", SHAMROCK, "#f2a6c8"]
    parts = [
        ringband(-0.14, 0.14, "#3a6a1e", margin=0.07, decal="sp_moss", wrap=True),
        rod([0, 0.0, 0], [0, 1.40, 0], 0.10, "#f4f0e0"),
        part("sph", [0, 1.46, 0], [0.18, 0.18, 0.18], GOLD, m="metal"),
        part("torus", [0, 1.28, 0], [0.30, 0.08, 0.30], "#3a6a1e"),
    ]
    for k, c in enumerate(colours):
        a = TAU * k / 8
        parts.append(rod([math.sin(a) * 0.10, 1.28, math.cos(a) * 0.10],
                         [math.sin(a + 0.5) * 0.98, -0.06, math.cos(a + 0.5) * 0.95], 0.05, c))
    parts += around(8, 0.98, -0.10, lambda a, x, z: place(
        "flower", [x, -0.06, z * 0.97], [0.26, 0.26, 0.5],
        ["#ffffff", "#ffd34a", "#f2a6c8", "#c8a0ff"][int(round(a * 8 / TAU)) % 4], r=[0, a, 0]),
        start=0.25)
    return parts


@SP25.hat("feis_tiara", "Feis Tiara",
          "A dancer's tiara, every stone glittering, a knot of silver in the middle. "
          "It has won four medals at the feis and lost one, and it is still not over "
          "the one.", "rare", hair="show")
def _():
    # two silver arches standing from the brow and leaning back over the
    # crown, a stone at every turn, the knot at the top
    lean = -0.75
    base = [0, 0.04, 0.60]
    parts = [place("arch", base, [1.24, 0.90, 1.0], SILVER, r=[lean, 0, 0], m="metal"),
             place("arch", base, [0.84, 0.64, 1.0], SILVER, r=[lean, 0, 0], m="metal")]
    for k in range(9):
        a = (k + 0.5) / 9 * PI
        x, y = -math.cos(a) * 0.62, math.sin(a) * 0.45
        parts.append(part("sph", [x, base[1] + y * math.cos(lean), base[2] + y * math.sin(lean)],
                          [0.10, 0.10, 0.10], "#e8fbff" if k % 2 else "#9aff6a", m="glass"))
    top = [0, base[1] + 0.52 * math.cos(lean), base[2] + 0.52 * math.sin(lean) + 0.04]
    parts += [part("disc", top, [0.30, 0.30, 0.06], SILVER, [lean, 0, 0], m="metal",
                   decal="sp_triskele"),
              part("sph", [top[0], top[1], top[2] + 0.03], [0.10, 0.10, 0.08], EMERALD, m="glass")]
    return parts


@SP25.hat("bodhran_hat", "Bodhrán Hat",
          "A bodhrán, goatskin up, a knot painted on the head and the tipper stuck in "
          "the frame. Tap it and the whole room starts keeping time.", "uncommon",
          hair="show")
def _():
    return [
        part("cyl", [0, 0.16, 0], [1.76, 0.30, 1.76], ASH, decal="sp_drumframe", wrap=True),
        part("cyl", [0, 0.32, 0], [1.70, 0.02, 1.70], DRUMSKIN),
        part("box", [0, 0.335, 0], [1.40, 1.40, 0.01], "#000000", [-PI / 2, 0, 0], decal="sp_bodhran",
             a=-1),
        part("torus", [0, 0.31, 0], [1.76, 0.06, 1.76], shade(ASH, 0.8)),
        rod([0.40, 0.40, 0.50], [0.80, 1.00, 0.30], 0.07, "#5a3a22"),
        part("sph", [0.40, 0.40, 0.50], [0.12, 0.12, 0.12], "#5a3a22"),
        part("sph", [0.80, 1.00, 0.30], [0.12, 0.12, 0.12], "#5a3a22"),
    ]


@SP25.hat("festoon_crown", "Festoon Crown",
          "A string of lamps looped round your head on a black wire, every bulb lit, "
          "the same ones that were strung over the green. Dance till they go out.",
          "rare", hair="show")
def _():
    # eight little posts round the brim and the wire swagged between them,
    # a lamp hanging at the bottom of every swag
    n = 8
    pts = [[math.sin(TAU * k / n) * 0.96, 0.40, math.cos(TAU * k / n) * 0.93] for k in range(n)]
    parts = [ringband(-0.10, 0.08, BLACK, margin=0.06)]
    for k in range(n):
        p, q = pts[k], pts[(k + 1) % n]
        mid = [(p[0] + q[0]) / 2 * 1.03, 0.24, (p[2] + q[2]) / 2 * 1.03]
        parts += [rod(p, mid, 0.025, BLACK), rod(mid, q, 0.025, BLACK),
                  rod([p[0], -0.06, p[2]], [p[0], p[1] + 0.04, p[2]], 0.04, BLACK),
                  part("sph", [p[0], p[1] + 0.05, p[2]], [0.06, 0.06, 0.06], BRASS, m="metal")]
        bulb = [mid[0], mid[1] - 0.12, mid[2]]
        parts += [part("cyl", [mid[0], mid[1] - 0.03, mid[2]], [0.08, 0.06, 0.08], BLACK),
                  part("sph", bulb, [0.16, 0.20, 0.16],
                       ["#ffe08a", "#9aff6a", "#ff9a4a", "#fff3b0", "#ff6a8a"][k % 5], m="neon")]
    return parts


@SP25.hat("squeezebox", "Squeezebox",
          "A button accordion balanced on your head, bellows open, playing a jig by "
          "itself. Nobody has ever played one of these quietly. Nobody ever will.",
          "uncommon", hair="show")
def _():
    red = "#b0202a"
    parts = [part("rbox", [0.70, 0.36, 0], [0.24, 0.70, 0.62], red, decal="sp_accordion"),
             part("rbox", [-0.70, 0.36, 0], [0.24, 0.70, 0.62], red, decal="sp_accordion")]
    for k in range(9):
        x = -0.54 + k * 0.135
        parts.append(part("rbox", [x, 0.36, 0], [0.11, 0.66 - 0.04 * (k % 2), 0.58 - 0.04 * (k % 2)],
                          "#f4ecd8" if k % 2 else "#1a1a20"))
    for k in range(10):
        parts.append(part("cyl", [0.83, 0.20 + (k % 5) * 0.08, 0.10 if k < 5 else -0.10],
                          [0.05, 0.03, 0.05], "#f4ecd8", [0, 0, PI / 2]))
    parts += [part("rbox", [0, 0.02, 0], [1.20, 0.04, 0.20], "#3a2a1e")]
    return parts


@SP25.hat("caubeen", "Piper's Caubeen",
          "The big floppy green beret the pipers wear, pulled down over one ear, a "
          "silver badge and a hackle of feathers on the other side.", "rare")
def _():
    green = "#1f5a30"
    return [
        cap(-0.30, 0.10, green, grow=0.04, decal="felt", wrap=True),
        part("sph", [-0.24, 0.12, 0.02], [2.0, 0.36, 1.86], green, [0, 0, 0.18], decal="felt", wrap=True),
        ringband(-0.24, 0.10, "#1a1a20", margin=0.06),
        part("cyl", [-0.20, 0.30, 0.0], [0.12, 0.08, 0.12], shade(green, 0.8)),
        part("disc", [0.70, -0.06, 0.40], [0.26, 0.26, 0.06], SILVER, [0, 0.9, 0], m="metal",
             decal="sp_triskele"),
        place("feather", [0.80, 0.10, 0.20], [1.0, 0.60, 1.0], "#2f8a3a", r=[0, PI / 2, -0.4]),
        place("feather", [0.82, 0.12, 0.10], [1.0, 0.55, 1.0], "#f4f6f8", r=[0, PI / 2, -0.2]),
        place("feather", [0.80, 0.10, 0.00], [1.0, 0.50, 1.0], "#ff8a2a", r=[0, PI / 2, 0.0]),
    ]


@SP25.hat("derby_bow", "Fiddler's Derby",
          "A green derby with a fiddle bow stuck through the band, worn by the "
          "fiddler at the jamboree that nobody could put a name to.", "uncommon")
def _():
    green = "#1f4a2a"
    parts = [
        place("brim", [0, -0.05, 0], [2.10, 1.0, 2.0], green, anchor=[0, 0, 0], decal="felt", wrap=True),
        dome(-0.06, 0.70, green, t="capcrown", decal="felt", wrap=True),
        ringband(0.06, 0.14, EBONY, margin=0.04),
    ]
    parts += _bow([-0.86, 0.14, 0.40], [0.80, 0.40, -0.50], 1.0)
    return parts


@SP25.back("uilleann_pipes", "Uilleann Pipes",
           "The Irish pipes, bag and bellows and drones and regulators and a chanter "
           "on a ribbon, all strapped across your back. Takes seven years to learn, "
           "seven to practise and seven to play.", "legendary")
def _():
    velvet = "#1f5a30"
    parts = straps("#5a3a22") + [
        part("sph", [0.40, 0.26, -0.40], [0.80, 0.62, 0.50], velvet, decal="felt", wrap=True),
        part("rbox", [-0.50, -0.30, -0.30], [0.50, 0.60, 0.20], "#6a3a1e", decal="leather", wrap=True),
        rod([-0.50, 0.00, -0.30], [0.20, 0.20, -0.36], 0.08, "#5a3a22"),
    ]
    # the drones and regulators lying across, ivory mounts and brass rings
    for k, (y, w) in enumerate(((0.80, 0.12), (0.64, 0.10), (0.50, 0.09), (0.36, 0.08))):
        p0, p1 = [0.80, y - 0.40, -0.50 - 0.04 * k], [-0.90, y + 0.30, -0.50 - 0.04 * k]
        parts.append(rod(p0, p1, w, EBONY))
        parts += [part("sph", list(p1), [w * 1.4, w * 1.4, w * 1.4], "#ece4d0"),
                  part("sph", [p0[0] * 0.4 + p1[0] * 0.6, p0[1] * 0.4 + p1[1] * 0.6, p0[2]],
                       [w * 1.3, w * 1.3, w * 1.3], BRASS, m="metal")]
    parts += [rod([0.40, -0.04, -0.46], [0.36, -1.00, -0.40], 0.09, EBONY),
              part("sph", [0.36, -1.02, -0.40], [0.14, 0.14, 0.14], "#ece4d0"),
              place("ribbon", [0.44, -0.08, -0.48], [0.14, 0.60, 0.5], EMERALD, anchor=[0, 0.5, 0],
                    r=[0.1, 0, 0.3])]
    return parts


@SP25.back("fiddle_back", "Fiddle and Bow",
           "The fiddle slung across your back on a green strap, the bow tucked under "
           "it, ready for the next tune somebody calls.", "rare")
def _():
    parts = [rod([0.70, 1.00, 0.20], [-0.60, -0.70, -0.20], 0.10, EMERALD),
             part("rbox", [0.36, 1.025, 0.20], [0.14, 0.06, 0.72], EMERALD)]
    parts += at_frame(_fiddle(1.25), [0.0, 0.20, -0.22], [0, PI, 0.55])
    parts += _bow([-0.50, -0.50, -0.34], [0.60, 1.10, -0.34], 1.2)
    return parts


@SP25.hairdo("feis_ringlets", "Feis Ringlets",
             "Ginger ringlets, a hundred of them, every one bouncing in time, and a "
             "band across the top to hold the whole lot down.", "rare")
def _():
    parts = [place("hairmid", [0, 0, 0], [1.04, 1.04, 1.04], GINGER, anchor=[0, 0, 0],
                   decal="strands", wrap=True),
             part("rbox", [0, 0.50, 0.04], [1.06, 0.08, 1.08], EMERALD)]
    for k in range(14):
        a = PI * 0.30 + k * (PI * 1.40 / 13)
        x, z = math.sin(a) * 0.58, math.cos(a) * 0.58
        parts.append(place("spiral", [x, 0.10 - (k % 2) * 0.06, z], [0.20, 0.42, 0.20],
                           GINGER if k % 2 else shade(GINGER, 0.88), anchor=[0, 1.1, 0]))
    return parts


@SP25.hairdo("sean_nos_curls", "Sean-nós Curls",
             "A thick mop of black curls that bounces when you dance, which is "
             "always.", "uncommon")
def _():
    black = "#1e1a18"
    parts = [place("hairshort", [0, 0, 0], [1.04, 1.04, 1.04], black, anchor=[0, 0, 0],
                   decal="strands", wrap=True)]
    for k in range(16):
        a = k * 2.399
        r = 0.12 + 0.26 * ((k * 7) % 16) / 16
        parts.append(part("sph", [math.sin(a) * r, 0.56 + 0.04 * (k % 3), math.cos(a) * r],
                          [0.20, 0.16, 0.20], black if k % 2 else "#2e2824"))
    return parts


SP25.face("lost_in_the_reel", "Lost in the Reel",
          "Eyes shut, head back, a grin from ear to ear and a tune going round in "
          "there that will not stop.", [
              {"k": "arc", "x": -0.20, "y": -0.14, "r": 0.07, "a0": 0.55, "a1": 0.95, "w": 0.035,
               "c": "#16171b"},
              {"k": "arc", "x": 0.20, "y": -0.14, "r": 0.07, "a0": 0.55, "a1": 0.95, "w": 0.035,
               "c": "#16171b"},
              {"k": "arc", "x": 0.0, "y": 0.02, "r": 0.22, "a0": 0.05, "a1": 0.45, "w": 0.045,
               "c": "#16171b"},
              {"k": "ellipse", "x": -0.32, "y": 0.04, "w": 0.12, "h": 0.07, "c": "#ff9aa8"},
              {"k": "ellipse", "x": 0.32, "y": 0.04, "w": 0.12, "h": 0.07, "c": "#ff9aa8"},
              {"k": "ellipse", "x": 0.34, "y": -0.30, "w": 0.07, "h": 0.05, "c": "#2f8a3a"},
              {"k": "line", "x1": 0.37, "y1": -0.30, "x2": 0.37, "y2": -0.44, "w": 0.015,
               "c": "#2f8a3a"},
              {"k": "line", "x1": 0.37, "y1": -0.44, "x2": 0.42, "y2": -0.40, "w": 0.015,
               "c": "#2f8a3a"},
          ], "uncommon")
SP25.face("out_of_breath", "Out of Breath",
          "Red to the ears, gasping, a bead of sweat on the brow -- and asking the "
          "band for one more.", [
              {"k": "line", "x1": -0.28, "y1": -0.16, "x2": -0.12, "y2": -0.12, "w": 0.04,
               "c": "#16171b"},
              {"k": "line", "x1": 0.28, "y1": -0.16, "x2": 0.12, "y2": -0.12, "w": 0.04,
               "c": "#16171b"},
              {"k": "ellipse", "x": -0.30, "y": 0.04, "w": 0.18, "h": 0.12, "c": "#ff6a6a"},
              {"k": "ellipse", "x": 0.30, "y": 0.04, "w": 0.18, "h": 0.12, "c": "#ff6a6a"},
              {"k": "ellipse", "x": 0.0, "y": 0.14, "w": 0.16, "h": 0.18, "c": "#16171b"},
              {"k": "ellipse", "x": 0.0, "y": 0.19, "w": 0.10, "h": 0.06, "c": "#e05a6a"},
              {"k": "poly", "pts": [[-0.36, -0.36], [-0.32, -0.26], [-0.36, -0.22], [-0.40, -0.26]],
               "c": "#8fd0ff"},
              {"k": "poly", "pts": [[0.40, -0.30], [0.43, -0.22], [0.40, -0.19], [0.37, -0.22]],
               "c": "#8fd0ff"},
          ], "uncommon")
SP25.shirt("aran_jumper", "Aran Jumper",
           "A cream Aran jumper, cables and diamonds and honeycomb, knitted on the "
           "islands and heavy enough to stop a bullet. Probably.",
           {"torso": ARAN, "arms": ARAN, "decal": "sp_tee_aran", "weave": "sp_aran"}, "rare")
SP25.pants("cord_trousers", "Céilí Cords",
           "Olive corduroy trousers with the knees gone shiny, tucked into "
           "dancing boots.",
           {"legs": "#5a6a2e", "weave": "sp_corduroy", "cuff": "#2a1e16"})
SP25.belt("crios", "Crios",
          "The woven belt of the Aran Islands: red and green and blue in zigzags, "
          "tied round twice, the fringes hanging.",
          {"band": "#c43a2a", "width": 0.18, "weave": "sp_crios"})


@SP25.weapon("devils_reel", "The Devil's Reel",
             "The fiddler's fiddle. Play it fast enough for long enough and it starts "
             "to play itself, faster, harder, every note landing heavier than the last "
             "-- until you miss one.",
             {"kind": "hitscan", "damage": 7, "headshot": 1.5, "rpm": 420, "mag": 40,
              "reload": 2.4, "range": 120, "auto": True, "sound": "fiddle", "recoil": 0.2,
              "spread": 1.4, "reserve": 200, "tracer": "#9aff6a",
              "streak": {"per_hit": 0.05, "max": 1.0, "label": "Reel"}},
             [["+", "Every hit in a row plays 5% harder, up to double after twenty"],
              ["+", "Seven notes a second"],
              ["-", "7 damage to start with"],
              ["-", "One missed note and you start the reel again"]], rarity="legendary")
def _():
    return at_frame(_fiddle(0.80), [0, 0.12, 0.30], [PI / 2, 0, 0]) + \
        _bow([0.30, 0.30, 0.10], [-0.20, 0.30, 1.00], 0.9)


@SP25.weapon("bodhran", "Bodhrán",
             "Throw the drum down and it keeps the beat on its own. Your side dances to "
             "it, quicker; the other side trips over their feet trying to keep up.",
             {"kind": "deploy", "cooldown": 24, "sound": "drum",
              "deploy": {"type": "zone", "thrown": True, "throw": 18, "radius": 10.0,
                         "secs": 10.0, "limit": 1, "color": "#9aff6a", "particle": "note",
                         "ally": {"haste": [0.25, 1.0]},
                         "enemy": {"slow": [0.30, 1.0], "jumpless": 1.0}, "name": "Bodhrán"}},
             [["+", "Teammates within 10 studs of the drum run 25% faster"],
              ["+", "Enemies within 10 studs are slowed by 30% and cannot jump"],
              ["-", "Keeps time for 10 seconds, then stops"],
              ["-", "24 second cooldown"]], rarity="rare",
             deploy=lambda: [
                 part("cyl", [0, 0.20, 0], [1.80, 0.30, 1.80], ASH, decal="sp_drumframe", wrap=True),
                 part("cyl", [0, 0.36, 0], [1.74, 0.02, 1.74], DRUMSKIN),
                 part("box", [0, 0.375, 0], [1.40, 1.40, 0.01], "#000000", [-PI / 2, 0, 0],
                      decal="sp_bodhran", a=-1),
                 rod([0.40, 0.46, 0.30], [-0.20, 0.80, -0.30], 0.08, "#5a3a22", spin=3.0)])
def _():
    return [
        part("cyl", [0, 0.10, 0.36], [0.90, 0.16, 0.90], ASH, [PI / 2, 0, 0], decal="sp_drumframe",
             wrap=True),
        part("cyl", [0, 0.10, 0.45], [0.86, 0.01, 0.86], DRUMSKIN, [PI / 2, 0, 0]),
        part("box", [0, 0.10, 0.455], [0.70, 0.70, 0.01], "#000000", decal="sp_bodhran", a=-1),
        rod([0, -0.06, -0.06], [0, 0.10, 0.30], 0.06, "#5a3a22"),
    ]


@SP25.weapon("hurley", "Hurley",
             "An ash hurley with a sliotar's worth of welts on the bas. One swing puts "
             "them up in the air; the next, while they are still up there, puts them in "
             "the back of the net.",
             {"kind": "melee", "damage": 30, "headshot": 1.0, "rpm": 84, "range": 11.0,
              "arc": 0.70, "sound": "swing", "knockback": 6,
              "on_hit": {"knockup": 20}, "vs_airborne": 1.6},
             [["+", "Pucks whoever it hits up into the air"],
              ["+", "60% more damage to anyone already off the ground"],
              ["-", "30 damage on the ground"],
              ["-", "Close in only"]], rarity="legendary")
def _():
    return [
        rod([0, 0, -0.30], [0, 0.06, 1.10], 0.12, ASH, decal="leather"),
        part("rbox", [0, -0.02, -0.18], [0.14, 0.14, 0.30], "#2a2a30"),
        part("sph", [0, -0.04, 1.32], [0.10, 0.36, 0.60], ASH, [0.5, 0, 0], decal="sp_fiddlewood",
             wrap=True),
        part("rbox", [0, -0.16, 1.40], [0.11, 0.06, 0.36], "#c9ced6", [0.5, 0, 0], m="metal"),
        part("sph", [0.20, 0.14, 1.20], [0.18, 0.18, 0.18], "#f4f0e0", decal="leather", wrap=True),
    ]


@SP25.gear("hornpipe_shoes", "Hornpipe Shoes",
           "A pair of hard dancing shoes. Click your heels and you leap straight up "
           "and come floating down as if the music were holding you.",
           {"kind": "ability", "cooldown": 16, "sound": "drum",
            "ability": {"launch": {"up": 46, "forward": 10}, "jump": {"secs": 6.0, "gravity": 0.5}}},
           [["+", "A standing leap straight up"],
            ["+", "Half gravity for 6 seconds after"],
            ["-", "16 second cooldown"],
            ["-", "No damage at all"]], rarity="rare")
def _():
    out = []
    for s in (1, -1):
        x = 0.14 * s
        out += [part("sph", [x, -0.02, 0.46], [0.22, 0.18, 0.34], BLACK, m="glass"),
                part("rbox", [x, 0.02, 0.22], [0.22, 0.24, 0.30], BLACK, m="glass"),
                part("rbox", [x, -0.14, 0.10], [0.20, 0.10, 0.12], "#3a3a40"),
                part("rbox", [x, -0.12, 0.50], [0.20, 0.04, 0.22], "#3a3a40"),
                part("rbox", [x, 0.12, 0.34], [0.18, 0.04, 0.12], SILVER, [-0.4, 0, 0], m="metal"),
                part("rbox", [x, 0.12, 0.34], [0.10, 0.05, 0.06], BLACK, [-0.4, 0, 0])]
    return out


SP25.effect("ceili_notes", name="Céilí Notes", rate=2.6, life=[1.8, 2.4],
            size=[0.30, 0.42], grow=0.0, gravity=-0.4, spread=0.4, rise=[0.3, 0.6],
            blend="normal", spin=1.0, colors=["#9aff6a", "#ffffff", "#ffd34a"], shape="note",
            radius=0.8, orbit=1.4, wobble=0.6)
SP25.effect("lamps_lit", name="Lamps Lit", rate=3.0, life=[1.4, 2.0],
            size=[0.18, 0.26], grow=0.0, gravity=0.0, spread=0.3, rise=[0.0, 0.1],
            blend="add", spin=0.0, colors=["#ffe08a", "#9aff6a", "#ff9a4a", "#ff6a8a"],
            shape="bubble", radius=1.0, orbit=2.0, wobble=0.2)
SP25.opening(
    sky={"top": "#06140c", "horizon": "#2a4a2a", "sun": [0.1, 0.5, 0.6], "clouds": 0.3,
         "tint": "#fff0c8"},
    ambient="#5a6a4a", beam="#ffd34a", seep="lamps_lit", after="ceili_notes",
    burst=["#9aff6a", "#ffd34a", "#ffffff", "#ff9a4a"],
    pieces=[{"shape": "note", "colors": ["#9aff6a", "#ffffff"], "blend": "normal"},
            {"shape": "shamrock", "colors": ["#4fc46e", "#2f8a3a"], "blend": "normal"},
            {"shape": "sp_coin", "colors": ["#ffd34a"], "blend": "normal"},
            {"shape": "spark", "colors": ["#ffe08a", "#ff9a4a"], "blend": "add"}],
    backdrop="sp_ceili", title_wait="The fiddler is tuning up...",
    title_shake="Take your partners...")
SP25.award("Emerald Jamboree", ["Wallflower", "Toe Tapper", "Set Dancer", "Reel Runner",
                                "Céilí Caller", "The Fiddler Himself"],
           "Opened Fiddle Cases at the Emerald Jamboree, St. Patrick's 2025.", "em_fiddle",
           "clover")
SP25.bundle("pair", "Case and Key", 1, 1050, "One Fiddle Case, one Tuning Key.")
SP25.bundle("set", "A Set of Three", 3, 3000, "Three cases, three keys. Saves 300.")

EVENTS = [SP22, SP23, SP24, SP25]
