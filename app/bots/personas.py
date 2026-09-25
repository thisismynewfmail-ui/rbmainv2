"""Persona tags: who a bot is, and everything that follows from it.

Every bot is given a handful of tags when it is created.  The tags are the
single source of a bot's character, and every part of the system reads them:

* **friends** -- two bots become friends when they share at least the
  configured number of tags ("friend depth"); how many friends a bot wants,
  and how choosy it is about accepting, come from its social tags.
* **schedule** -- night owls are online late, early birds in the morning,
  weekend warriors at the weekend; how long a session lasts is a tag too.
* **worlds** -- a ``tycoon_fan`` queues for Burger Tycoon, a ``ctf_main``
  for the flag maps, and everybody drifts towards where their friends are.
* **in game** -- skill, aim, reaction time, how much they play the objective,
  how likely they are to wander off, go AFK or chase a revenge kill.
* **voice** -- the persona block every prompt carries is written from the
  tags, so a ``lowercase_typer`` types in lowercase in chat, in comments and
  in a DM alike.

Tags live in exclusive groups (a bot has one schedule, one skill level, one
typing style) and open ones (it can like two worlds and three hobbies).  The
catalogue is data; an administrator can add custom tags from the Bots Zone,
which then take part in friend matching and prompts like any other.
"""
from __future__ import annotations

import random
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

# --------------------------------------------------------------- traits
# Every number a bot runs on.  A tag nudges some of these; the rest stay at
# the base, then each bot gets a little noise of its own so no two
# ``sweaty sniper_main`` bots are the same player.
TRAIT_BASE: Dict[str, float] = {
    "activity": 0.5,    # how readily it comes online when the curve calls
    "night": 0.0,       # -1 morning person ... +1 night owl
    "weekend": 0.0,     # extra appetite at the weekend
    "session": 1.0,     # session length multiplier
    "gamer": 0.62,      # chance to queue for a world when it is free
    "skill": 0.5,
    "aggression": 0.5,
    "objective": 0.62,  # how much of a round it spends on the objective
    "support": 0.2,
    "explore": 0.2,
    "chaos": 0.08,
    "afk": 0.08,
    "jumpy": 0.2,
    "social": 0.5,      # friends wanted, how often it comments
    "chatty": 0.4,      # in-game chat
    "selective": 0.4,   # pickiness about friend requests
    "toxicity": 0.08,
    "kindness": 0.5,
    "collector": 0.3,
    "fashion": 0.4,
    "wealth": 0.5,
    "w_burger_tycoon": 1.0,
    "w_capture_the_flag": 1.0,
    "w_fortress_team_2": 1.0,
    "w_blackout_relay": 1.0,
    "wp_sniper": 0.2,
    "wp_shotgun": 0.35,
    "wp_smg": 0.3,
    "wp_rifle": 0.3,
    "wp_melee": 0.12,
    "wp_rocket": 0.15,
    "lower": 0.3,
    "emoji": 0.1,
    "grammar": 0.3,
    "abbrev": 0.3,
    "caps": 0.04,
}

# Traits that are weights or multipliers rather than 0..1 dials.
_UNBOUNDED = {"session", "night", "weekend"} | {
    k for k in TRAIT_BASE if k.startswith("w_") or k.startswith("wp_")}

# ------------------------------------------------------------ the catalogue
# (group, exclusive, core, max_from_group)
GROUPS: List[Tuple[str, bool, bool, int]] = [
    ("schedule", True, True, 1),
    ("skill", True, True, 1),
    ("focus", True, True, 1),
    ("social", True, True, 1),
    ("voice", True, True, 1),
    ("temper", True, False, 1),
    ("weapon", True, False, 1),
    ("age", True, False, 1),
    ("world", False, False, 2),
    ("interest", False, False, 3),
    ("custom", False, False, 2),
]
GROUP_INFO = {g[0]: g for g in GROUPS}


def _t(tag: str, group: str, label: str, prompt: str, weight: float = 1.0,
       **fx: float) -> Dict[str, Any]:
    return {"id": tag, "group": group, "label": label, "prompt": prompt,
            "weight": float(weight), "fx": fx}


# ``fx`` keys are traits; a value is added to the trait, except a key that
# starts with ``x_`` which multiplies it.
TAGS: List[Dict[str, Any]] = [
    # ---- schedule
    _t("night_owl", "schedule", "Night owl",
       "Mostly plays late at night and is often still on after midnight.",
       1.2, night=0.9, x_session=1.2),
    _t("early_bird", "schedule", "Early bird",
       "Plays in the morning before school or work; rarely on late.",
       0.7, night=-0.9),
    _t("after_school", "schedule", "After school",
       "Gets on in the afternoon and early evening.", 1.3, night=-0.2),
    _t("weekend_warrior", "schedule", "Weekend warrior",
       "Barely on during the week, then plays for hours at the weekend.",
       0.8, weekend=0.9, activity=-0.1, x_session=1.4),
    _t("no_life", "schedule", "Always online",
       "Seems to be online all the time and plays very long sessions.",
       0.5, activity=0.35, x_session=1.8, gamer=0.2),
    _t("casual_hours", "schedule", "Casual hours",
       "Drops in now and then for short sessions.", 1.2, activity=-0.1,
       x_session=0.7),
    # ---- skill
    _t("newbie", "skill", "Newbie",
       "Still new to the game: gets lost, misses a lot, asks questions.",
       0.8, skill=-0.3, objective=-0.15, explore=0.15, chatty=0.1),
    _t("average", "skill", "Average player",
       "An ordinary player -- wins some, loses some.", 1.6),
    _t("sweaty", "skill", "Tryhard",
       "Plays to win every round and takes it seriously.", 0.8, skill=0.3,
       aggression=0.2, objective=0.1, afk=-0.06, x_session=1.2),
    _t("veteran", "skill", "Veteran",
       "Has played since the early days and knows every map by heart.",
       0.7, skill=0.22, objective=0.12, explore=-0.05),
    # ---- focus
    _t("objective_player", "focus", "Objective player",
       "Always plays the objective -- flags, carts, plots -- over kills.",
       1.5, objective=0.25, aggression=-0.05),
    _t("fragger", "focus", "Fragger",
       "Hunts for kills and chases fights more than objectives.", 1.0,
       aggression=0.3, objective=-0.25),
    _t("support", "focus", "Team player",
       "Sticks with teammates, escorts carriers and heals people.", 0.8,
       support=0.45, objective=0.05, kindness=0.2),
    _t("chaotic", "focus", "Chaotic",
       "Does random things: jumps around, wanders off, messes about.", 0.6,
       chaos=0.3, jumpy=0.35, objective=-0.3, explore=0.2),
    _t("explorer", "focus", "Explorer",
       "Likes poking around the maps and finding hidden spots.", 0.7,
       explore=0.45, objective=-0.15),
    # ---- social
    _t("social_butterfly", "social", "Social butterfly",
       "Friends with everyone, comments on lots of profiles.", 0.8,
       social=0.4, chatty=0.25, selective=-0.25, kindness=0.15),
    _t("friendly", "social", "Friendly",
       "Easy-going and friendly to people.", 1.6, social=0.15,
       chatty=0.1, kindness=0.2, selective=-0.1),
    _t("shy", "social", "Shy",
       "Quiet; talks a little once it knows people.", 1.0, social=-0.2,
       chatty=-0.2, selective=0.15),
    _t("loner", "social", "Loner",
       "Mostly keeps to itself and has a small friends list.", 0.6,
       social=-0.35, chatty=-0.25, selective=0.35),
    _t("clique", "social", "Clique",
       "Sticks with a tight group of close friends.", 0.7, social=0.05,
       selective=0.3, chatty=0.1),
    # ---- voice
    _t("lowercase_typer", "voice", "lowercase typer",
       "Types almost entirely in lowercase with little punctuation.", 2.0,
       lower=0.7, grammar=-0.2),
    _t("emoji_lover", "voice", "Emoji lover",
       "Uses emoticons and text faces like :D xD <3 a lot.", 0.8,
       emoji=0.7),
    _t("proper_grammar", "voice", "Proper grammar",
       "Writes in full sentences with capitals and punctuation.", 0.9,
       grammar=0.7, lower=-0.3, abbrev=-0.2),
    _t("abbreviator", "voice", "Abbreviator",
       "Uses abbreviations like lol, ngl, idk, tbh, gg, wyd.", 1.3,
       abbrev=0.6, lower=0.2),
    _t("caps_yeller", "voice", "CAPS yeller",
       "Gets excited and types in CAPS when something happens.", 0.4,
       caps=0.5, chatty=0.1),
    _t("meme_speaker", "voice", "Meme speaker",
       "Talks in memes and in-jokes.", 0.7, abbrev=0.2, chaos=0.05),
    # ---- temper
    _t("chill", "temper", "Chill",
       "Relaxed; does not care much about winning.", 1.4, toxicity=-0.05,
       aggression=-0.1, kindness=0.1),
    _t("competitive", "temper", "Competitive",
       "Wants to win and hates losing.", 1.0, aggression=0.1, skill=0.05),
    _t("salty", "temper", "Salty",
       "Gets annoyed when it dies and complains about it.", 0.6,
       toxicity=0.15, chatty=0.1),
    _t("trash_talker", "temper", "Trash talker",
       "Teases opponents in chat (playfully, never hateful).", 0.4,
       toxicity=0.25, chatty=0.25, aggression=0.1),
    _t("wholesome", "temper", "Wholesome",
       "Compliments people and says gg every round.", 1.0, kindness=0.35,
       toxicity=-0.1),
    # ---- weapon
    _t("sniper_main", "weapon", "Sniper main",
       "Loves the Longshot sniper and long sightlines.", 0.8, wp_sniper=1.4,
       explore=0.05),
    _t("shotgun_rusher", "weapon", "Shotgun rusher",
       "Rushes in close with the shotgun.", 0.9, wp_shotgun=1.2,
       aggression=0.15),
    _t("smg_sprayer", "weapon", "SMG sprayer",
       "Sprays with the Rapid SMG.", 0.9, wp_smg=1.3),
    _t("melee_maniac", "weapon", "Melee maniac",
       "Runs at people with the Blockblade.", 0.4, wp_melee=1.5,
       aggression=0.2),
    _t("rocket_spammer", "weapon", "Rocket spammer",
       "Spams the Blast Launcher and rocket jumps.", 0.5, wp_rocket=1.5,
       jumpy=0.15),
    _t("all_rounder", "weapon", "All-rounder",
       "Uses whatever suits the situation.", 1.2, wp_rifle=0.6),
    # ---- age
    _t("kid", "age", "Kid",
       "Young player -- excitable, simple words, lots of energy.", 0.8,
       chatty=0.1, grammar=-0.2, jumpy=0.1),
    _t("teen", "age", "Teen", "A teenager.", 1.6),
    _t("young_adult", "age", "Young adult",
       "In their twenties; plays after work or classes.", 1.2),
    _t("adult", "age", "Adult",
       "An older player who plays to unwind.", 0.6, grammar=0.2,
       toxicity=-0.04, x_session=0.85),
    # ---- world
    _t("tycoon_fan", "world", "Tycoon fan",
       "Loves Burger Tycoon and building the biggest restaurant.", 1.2,
       w_burger_tycoon=2.4, objective=0.05),
    _t("ctf_main", "world", "CTF main",
       "Lives on Capture The Flag.", 1.1, w_capture_the_flag=2.4),
    _t("payload_enjoyer", "world", "Payload enjoyer",
       "Plays Fortress Team 2 and loves pushing the cart.", 0.9,
       w_fortress_team_2=2.4),
    _t("relay_regular", "world", "Relay regular",
       "Plays Blackout Relay's long flag runs at dusk.", 0.9,
       w_blackout_relay=2.4),
    # ---- interests
    _t("collector", "interest", "Hat collector",
       "Collects hats and dreams of Unusuals.", 0.9, collector=0.45,
       wealth=0.1),
    _t("fashionista", "interest", "Fashionista",
       "Cares a lot about outfits and colour schemes.", 0.8, fashion=0.4),
    _t("builder", "interest", "Builder",
       "Likes building and designing things.", 0.8, w_burger_tycoon=0.5),
    _t("anime", "interest", "Anime fan", "Watches a lot of anime.", 0.9),
    _t("music", "interest", "Music lover",
       "Always listening to music and talks about songs.", 1.0),
    _t("sports", "interest", "Sports fan", "Into football and sports.", 0.7),
    _t("memes", "interest", "Meme lord", "Knows every meme.", 1.0,
       chaos=0.04),
    _t("speedrunner", "interest", "Speedrunner",
       "Tries to do everything as fast as possible.", 0.4, skill=0.05,
       objective=0.1),
    _t("roleplayer", "interest", "Roleplayer",
       "Likes roleplaying characters in games.", 0.5, chatty=0.1,
       explore=0.1),
    _t("streamer_wannabe", "interest", "Streamer wannabe",
       "Wants to be a streamer and mentions it.", 0.4, chatty=0.15),
    _t("retro_gamer", "interest", "Retro gamer",
       "Nostalgic about old games.", 0.6),
    _t("trader", "interest", "Trader",
       "Always talking about item values and trades.", 0.5, wealth=0.2,
       collector=0.15),
    _t("artist", "interest", "Artist", "Draws and makes fan art.", 0.6,
       fashion=0.1),
    _t("pets", "interest", "Pet lover", "Talks about their pets.", 0.6,
       kindness=0.1),
]

TAGS_BY_ID: Dict[str, Dict[str, Any]] = {t["id"]: t for t in TAGS}
BUILTIN_TAG_IDS: List[str] = [t["id"] for t in TAGS]


# ------------------------------------------------------ custom tags + bits
_custom: Dict[str, Dict[str, Any]] = {}
_bits: Dict[str, int] = {}


def _rebuild_bits() -> None:
    """Every tag -- built in or custom -- gets a stable bit.

    Built-in tags always hold the low bits in catalogue order, so a mask
    computed before an administrator added a custom tag still means the
    same thing after.
    """
    _bits.clear()
    for index, tag in enumerate(BUILTIN_TAG_IDS):
        _bits[tag] = index
    offset = len(BUILTIN_TAG_IDS)
    for index, tag in enumerate(sorted(_custom)):
        _bits[tag] = offset + index


def set_custom_tags(lines: Iterable[str]) -> None:
    """Install the administrator's own tags ("tag: what it means")."""
    _custom.clear()
    for line in lines or []:
        line = str(line or "").strip()
        if not line or line.startswith("#"):
            continue
        tag, _, prompt = line.partition(":")
        tag = "".join(c for c in tag.strip().lower().replace(" ", "_")
                      if c.isalnum() or c == "_")[:32]
        if not tag or tag in TAGS_BY_ID:
            continue
        _custom[tag] = {"id": tag, "group": "custom",
                        "label": tag.replace("_", " ").title(),
                        "prompt": prompt.strip()[:200] or tag.replace("_", " "),
                        "weight": 1.0, "fx": {}}
    _rebuild_bits()


_rebuild_bits()


def tag_info(tag: str) -> Optional[Dict[str, Any]]:
    return TAGS_BY_ID.get(tag) or _custom.get(tag)


def all_tags() -> List[Dict[str, Any]]:
    return TAGS + [_custom[k] for k in sorted(_custom)]


def mask_of(tags: Iterable[str]) -> int:
    mask = 0
    for tag in tags:
        bit = _bits.get(tag)
        if bit is not None:
            mask |= 1 << bit
    return mask


def shared(mask_a: int, mask_b: int) -> int:
    """How many tags two bots have in common -- the friend-depth measure."""
    return bin(mask_a & mask_b).count("1")


def parse_tags(text: str) -> List[str]:
    return [t for t in (text or "").split(",") if t]


# ------------------------------------------------------------- drawing
def draw_tags(rng: random.Random, count: int,
              weights: Optional[Dict[str, float]] = None) -> List[str]:
    """Draw a coherent set of tags.

    One tag from every core group first -- every bot has a schedule, a skill
    level, a focus, a social style and a typing voice, so there is never a
    bot the system does not know how to drive -- then the optional groups
    fill the rest up to ``count``, never breaking a group's exclusivity.
    """
    weights = weights or {}
    catalogue = all_tags()
    by_group: Dict[str, List[Dict[str, Any]]] = {}
    for tag in catalogue:
        by_group.setdefault(tag["group"], []).append(tag)

    def pick(group: str, exclude: Sequence[str]) -> Optional[str]:
        pool = [t for t in by_group.get(group, []) if t["id"] not in exclude]
        scored = [(t, max(0.0, float(weights.get(t["id"], 1.0))) * t["weight"])
                  for t in pool]
        total = sum(w for _, w in scored)
        if total <= 0:
            return None
        roll = rng.random() * total
        for tag, w in scored:
            roll -= w
            if roll <= 0:
                return tag["id"]
        return scored[-1][0]["id"]

    chosen: List[str] = []
    taken: Dict[str, int] = {}
    for group, _excl, core, _cap in GROUPS:
        if core:
            tag = pick(group, chosen)
            if tag:
                chosen.append(tag)
                taken[group] = 1
    optional = [g for g in GROUPS if not g[2]]
    guard = 0
    while len(chosen) < count and guard < 60:
        guard += 1
        group, exclusive, _core, cap = rng.choice(optional)
        have = taken.get(group, 0)
        if (exclusive and have) or have >= cap:
            continue
        tag = pick(group, chosen)
        if tag and tag not in chosen:
            chosen.append(tag)
            taken[group] = have + 1
    return chosen


def derive_traits(tags: Sequence[str], rng: random.Random,
                  noise: float = 0.08) -> Dict[str, float]:
    """The numbers a bot runs on, from its tags plus a little of its own."""
    traits = dict(TRAIT_BASE)
    for tag in tags:
        info = tag_info(tag)
        if not info:
            continue
        for key, value in info["fx"].items():
            if key.startswith("x_"):
                name = key[2:]
                traits[name] = traits.get(name, 1.0) * float(value)
            else:
                traits[key] = traits.get(key, 0.0) + float(value)
    for key, value in list(traits.items()):
        if key in _UNBOUNDED:
            if key.startswith(("w_", "wp_")) or key == "session":
                traits[key] = round(max(0.05, value * rng.uniform(0.85, 1.15)), 3)
            else:
                traits[key] = round(max(-1.0, min(1.0, value + rng.gauss(0, noise))), 3)
        else:
            traits[key] = round(max(0.0, min(1.0, value + rng.gauss(0, noise))), 3)
    return traits


# ---------------------------------------------------------------- storage
# Traits are stored positionally ("t1|0.52,0.10,...") in the order below:
# about a fifth of the size of the same numbers as JSON, which matters when
# there are a couple of hundred thousand of them.  New traits go on the end
# of this list, never in the middle, so old rows keep reading correctly.
PACK_ORDER = [
    "activity", "night", "weekend", "session", "gamer", "skill", "aggression",
    "objective", "support", "explore", "chaos", "afk", "jumpy", "social",
    "chatty", "selective", "toxicity", "kindness", "collector", "fashion",
    "wealth", "w_burger_tycoon", "w_capture_the_flag", "w_fortress_team_2",
    "w_blackout_relay", "wp_sniper", "wp_shotgun", "wp_smg", "wp_rifle",
    "wp_melee", "wp_rocket", "lower", "emoji", "grammar", "abbrev", "caps",
]


def pack_traits(traits: Dict[str, float]) -> str:
    values = []
    for key in PACK_ORDER:
        value = float(traits.get(key, TRAIT_BASE.get(key, 0.0)))
        text = ("%.2f" % value).rstrip("0").rstrip(".")
        values.append(text if text not in ("-0", "") else "0")
    return "t1|" + ",".join(values)


def unpack_traits(text: str) -> Dict[str, float]:
    import json
    text = text or ""
    if text.startswith("t1|"):
        out = dict(TRAIT_BASE)
        for key, raw in zip(PACK_ORDER, text[3:].split(",")):
            try:
                out[key] = float(raw)
            except ValueError:
                pass
        return out
    try:
        data = json.loads(text or "{}")
    except ValueError:
        data = {}
    out = dict(TRAIT_BASE)
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (int, float)):
                out[key] = float(value)
    return out


# ------------------------------------------------------------- prompting
STYLE_LINES = [
    ("lower", 0.55, "Types in lowercase."),
    ("emoji", 0.45, "Sprinkles in text emoticons like :D, xD, :P or <3."),
    ("grammar", 0.6, "Writes with proper capitals and punctuation."),
    ("abbrev", 0.5, "Uses gamer abbreviations (lol, ngl, idk, tbh, gg)."),
    ("caps", 0.35, "Sometimes types in CAPS when excited."),
    ("toxicity", 0.3, "Can be a bit salty or teasing, but never hateful."),
    ("kindness", 0.7, "Is warm and complimentary."),
    ("chatty", 0.65, "Is talkative."),
]


def style_notes(traits: Dict[str, float]) -> List[str]:
    notes = [line for key, threshold, line in STYLE_LINES
             if float(traits.get(key, 0.0)) >= threshold]
    if float(traits.get("chatty", 0.4)) < 0.2:
        notes.append("Is quiet and keeps messages very short.")
    return notes


def favourite_worlds(traits: Dict[str, float], names: Dict[str, str],
                     top: int = 2) -> List[str]:
    scored = sorted(((float(traits.get("w_" + wid, 1.0)), wid) for wid in names),
                    reverse=True)
    return [names[wid] for _, wid in scored[:top]]


def describe(tags: Sequence[str]) -> List[str]:
    """One sentence per tag, for the persona block."""
    out = []
    for tag in tags:
        info = tag_info(tag)
        if info and info.get("prompt"):
            out.append(info["prompt"])
    return out


def labels(tags: Sequence[str]) -> List[str]:
    out = []
    for tag in tags:
        info = tag_info(tag)
        out.append(info["label"] if info else tag)
    return out
