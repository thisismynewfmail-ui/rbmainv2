"""Usernames: the rules every bot name must pass, and a generator for when
the language model is not available.

The generator does not glue random syllables together.  It reproduces the
handful of habits real players' names actually come from -- the same ones the
example list shows:

    Scarvia, Subaru, keigo       an invented or borrowed single word
    crtea20, banjo53             a short word and a two digit number
    teto gaming                  two words (spaces become _ or vanish here)
    DavidJoggins                 a first name and a silly surname
    EgonisCoolCat, NyxieSticks   a name welded to a phrase
    SHOUBI                       an all-caps word
    zFcBoxhead                   a clan-style prefix on a word
    pushmataha                   a long, strange real-sounding word

Every candidate -- the model's or the generator's -- goes through
:func:`normalise` and :func:`acceptable`, which apply the site's own username
rules (3 to 20 letters, digits and underscores) plus a short list of things a
bot's name must never be.
"""
from __future__ import annotations

import random
import re
from typing import Iterable, List, Optional, Set

from .. import config as site_config

FIRST_NAMES = """
aaron abby ada adam aiden alex alfie ali alice amara amir amy andre anna
anton archie aria arlo asher ava bea ben bianca blake bo bram brooke caleb
cam cara carlos casey cece chloe chris clara cody cole dani dante david dean
diego dom eden eli ella emil emma enzo eric eva evan ezra felix finn frank
freya gabe gio grace gus hana hank harper harvey hugo ian iris isaac ivan
izzy jack jade jake jamal james jana jay jen jonah jose josh jude julia
kai kara kate keira kian kira kobe kofi lana lars leah leo levi liam lila
lily lina logan lola luca lucy luis luke mae maisie malik mara marco maria
mason matt max maya mia mika milo mira mo nadia nate nico nina noah noor
nora olly omar oscar owen paige pablo pip priya quinn rafa reece remy rhys
rio rory rosa ruby ryan sam sami sara seb sean siena silas sofia sol stan
tara teo theo toby tom troy uma vera vic wes will xan yara yuki zac zara
zoe
""".split()

SURNAMES = """
joggins wobble puddles noodle bramble crumbs biscuit fumble pickles
wiggins tumble barnaby snoozle waffles gubbins dingle marrow muffin
thistle butters fizzwick grumble humphries jingles mcfly nutley
pepperpot quibble rumbles sprockets tater bumble cobble doodle
""".split()

NOUNS = """
cat fox wolf bear frog duck toad owl bee crow moth crab shark squid
panda koala otter tiger lion lynx hawk raven goose moose yak llama
cookie waffle noodle taco burger nugget pickle donut mochi bean toast
pixel byte block brick cube shard gem star moon comet nova storm rain
cloud frost ember blaze ash dust rock stone leaf root moss fern thorn
box boxhead sticks sock hat cap boot knight wizard ninja pirate ghost
goblin gremlin slime blob muffin potato turnip radish cheese bagel
spark bolt volt flux beam laser rocket jet drift glitch
""".split()

ADJECTIVES = """
cool silly sleepy happy grumpy tiny big mega super hyper lazy crazy
sneaky swift quiet loud fuzzy spicy salty sweet frozen golden silver
shadow neon cosmic lucky rusty dusty mighty funky chill wild angry
""".split()

GAMERISH = """
gaming games plays tv yt ttv irl real official fr lol xd hd pro
""".split()

# Invented words come in the two families the examples show.  Kana-style
# ("keigo", "Subaru", "SHOUBI") is built from morae; the other ("Scarvia",
# "bolin", "pushmataha") from a soft onset, an open middle and a real-sounding
# ending.  Both are kept short and pronounceable on purpose: a name is
# something a person could say out loud.
MORAE = ("ka ki ku ke ko sa shi su se so ta chi tsu te to na ni nu ne no ha hi "
         "fu he ho ma mi mu me mo ya yu yo ra ri ru re ro wa ga gi gu ge go "
         "za ji zu ze zo ba bi bu be bo pa pi po kyo ryu sho shou kei rei "
         "tou dai kou nyo").split()
SOFT_ONSETS = ["b", "br", "c", "d", "f", "fl", "g", "gr", "h", "j", "k", "l",
               "m", "n", "p", "pr", "r", "s", "sc", "sh", "st", "t", "tr",
               "v", "w", "z", "", ""]
MIDDLES = ["r", "l", "n", "v", "m", "s", "t", "d", "k", "rv", "lv", "nd",
           "sh", "b", "g", "th", "rt"]
VOWELS = ["a", "e", "i", "o", "u", "a", "i", "o"]
ENDINGS = ["a", "ia", "o", "us", "ix", "en", "y", "ie", "er", "in", "on",
           "el", "a", "i", "an", "is", "ara", "ata", "ika", "ette", "ino"]

BANNED_PARTS = ("bot", "npc", "admin", "moderator", "official_",
                "blockhaven", "system", "_ai_", "chatgpt",
                "fuck", "shit", "nazi", "hitler", "cunt", "nigg", "fag",
                "rape", "porn", "sex", "slut", "whore", "retard", "kys",
                "fuk", "fuc", "phuk", "dick", "cock", "penis", "vagin",
                "tits", "cum", "jizz", "anus", "nigg", "kkk", "isis")

_VALID = re.compile(r"^[A-Za-z0-9_]{%d,%d}$" % (site_config.USERNAME_MIN,
                                                site_config.USERNAME_MAX))


def normalise(raw: str, rng: Optional[random.Random] = None) -> str:
    """Bend a candidate into the site's username rules, or return ''.

    Spaces are the common case -- "teto gaming" -- and become an underscore
    or disappear (both are what people do when a site refuses the space).
    Anything else outside letters, digits and underscores is dropped.
    """
    rng = rng or random
    text = str(raw or "").strip().strip("\"'`.,;:-*#[](){}<>")
    if not text:
        return ""
    text = re.sub(r"^\d+[.)]\s*", "", text)          # "3. Name" from a list
    joiner = "_" if rng.random() < 0.5 else ""
    text = re.sub(r"\s+", joiner, text)
    text = re.sub(r"[^A-Za-z0-9_]", "", text)
    text = re.sub(r"_{2,}", "_", text).strip("_")
    if len(text) > site_config.USERNAME_MAX:
        text = text[:site_config.USERNAME_MAX].rstrip("_")
    return text


def acceptable(name: str) -> bool:
    if not name or not _VALID.match(name):
        return False
    lower = name.lower()
    if any(part in lower for part in BANNED_PARTS):
        return False
    if lower.isdigit() or lower.strip("_") == "":
        return False
    # "aaaaaaa", "_____x": nobody picks those
    if len(set(lower)) < 2:
        return False
    return True


# ------------------------------------------------------------- generator
def _word(rng: random.Random, syllables: Optional[int] = None) -> str:
    """An invented but pronounceable word, 3 to 11 letters."""
    if rng.random() < 0.45:
        count = syllables or rng.choice((2, 2, 3, 3))
        word = "".join(rng.choice(MORAE) for _ in range(count))
        if rng.random() < 0.18:
            word += "n"
        return word[:11]
    word = rng.choice(SOFT_ONSETS) + rng.choice(VOWELS)
    extra = (syllables or rng.choice((2, 2, 3))) - 2
    for _ in range(max(0, extra)):
        word += rng.choice(MIDDLES) + rng.choice(VOWELS)
    word += rng.choice(MIDDLES) + rng.choice(ENDINGS)
    return word[:11]


def _case(rng: random.Random, word: str) -> str:
    roll = rng.random()
    if roll < 0.5:
        return word.lower()
    if roll < 0.92:
        return word[:1].upper() + word[1:]
    return word.upper()


def _digits(rng: random.Random) -> str:
    roll = rng.random()
    if roll < 0.55:
        return str(rng.randint(1, 99))
    if roll < 0.8:
        return str(rng.choice(range(2005, 2016)))
    if roll < 0.92:
        return str(rng.randint(100, 999))
    return rng.choice(("7", "13", "21", "42", "69", "77", "88", "99", "123",
                       "1337", "404", "000"))


def generate(rng: random.Random) -> str:
    """One username in a randomly chosen real-world style."""
    style = rng.random()
    if style < 0.15:                                       # Scarvia, keigo
        return _case(rng, _word(rng))
    if style < 0.30:                                       # banjo53
        base = rng.choice((rng.choice(NOUNS), rng.choice(FIRST_NAMES),
                           _word(rng, 2)))
        return base.lower() + _digits(rng)
    if style < 0.40:                                       # teto gaming
        left = rng.choice((_word(rng, 2), rng.choice(FIRST_NAMES),
                           rng.choice(NOUNS)))
        right = rng.choice(GAMERISH + NOUNS[:20])
        return left.lower() + rng.choice(("_", "", "_")) + right.lower()
    if style < 0.50:                                       # DavidJoggins
        return (rng.choice(FIRST_NAMES).title()
                + rng.choice(SURNAMES).title())
    if style < 0.63:                                       # EgonisCoolCat
        name = rng.choice((rng.choice(FIRST_NAMES), _word(rng, 2))).title()
        joiner = rng.choice(("is", "the", "", "", "Is"))
        tail = rng.choice(ADJECTIVES).title() + rng.choice(NOUNS).title()
        if rng.random() < 0.5:
            tail = rng.choice(NOUNS).title() + rng.choice(("s", "", "z", ""))
        return name + joiner + tail
    if style < 0.68:                                       # SHOUBI
        return _word(rng, rng.choice((2, 3))).upper()
    if style < 0.74:                                       # zFcBoxhead
        prefix = (rng.choice("xzqvkj") + "".join(
            rng.choice("ABCDEFGHJKLMNPRSTVWXZ") for _ in range(2)))
        return prefix + rng.choice(NOUNS).title()
    if style < 0.80:                                       # pushmataha
        return _word(rng, rng.choice((3, 4))).lower()
    if style < 0.88:                                       # adjective noun
        return (rng.choice(ADJECTIVES).title() + rng.choice(NOUNS).title()
                + (_digits(rng) if rng.random() < 0.35 else ""))
    if style < 0.93:                                       # itz / xX_ Xx
        core = rng.choice((rng.choice(FIRST_NAMES), _word(rng, 2),
                           rng.choice(NOUNS))).title()
        return rng.choice(("itz", "its", "iam", "the", "xX_", "Real")) + core \
            + ("_Xx" if rng.random() < 0.2 else "")
    if style < 0.97:                                       # name_name
        return (rng.choice(FIRST_NAMES) + "_" + rng.choice(NOUNS)).lower()
    # stretched letters: kaiiii, nooodle
    word = rng.choice(FIRST_NAMES + NOUNS)
    return word + word[-1] * rng.randint(2, 4)


def generate_unique(rng: random.Random, taken: Set[str],
                    count: int) -> List[str]:
    """``count`` valid names whose lowercase form is not in ``taken``."""
    out: List[str] = []
    guard = 0
    while len(out) < count and guard < count * 40:
        guard += 1
        raw = generate(rng)
        if len(raw) > site_config.USERNAME_MAX:
            continue              # cut short it would read as a typo
        name = normalise(raw, rng)
        if not acceptable(name):
            continue
        key = name.lower()
        if key in taken:
            # a clash gets a number, the way a person whose name is gone
            # reaches for their birth year
            name = normalise(name[:16] + _digits(rng), rng)
            key = name.lower()
            if not acceptable(name) or key in taken:
                continue
        taken.add(key)
        out.append(name)
    return out


def parse_model_list(text: str) -> List[str]:
    """Names out of a model reply: a JSON array if it wrote one, else lines."""
    import json
    text = (text or "").strip()
    start, end = text.find("["), text.rfind("]")
    if start >= 0 and end > start:
        try:
            data = json.loads(text[start:end + 1])
            if isinstance(data, list):
                return [str(v) for v in data if isinstance(v, (str, int))]
        except ValueError:
            pass
    out = []
    for line in re.split(r"[\n,]", text):
        line = line.strip()
        if line and len(line) <= 40:
            out.append(line)
    return out


def dedupe(names: Iterable[str]) -> List[str]:
    seen: Set[str] = set()
    out = []
    for name in names:
        key = name.lower()
        if key not in seen:
            seen.add(key)
            out.append(name)
    return out
