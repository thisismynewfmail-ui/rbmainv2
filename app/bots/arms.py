"""What a bot carries into a game.

Every account owns the free three (the pistol, the shotgun and the stick).
A bot, persona permitting, buys more: shelf weapons its preferences favour
(the Longshot for a sniper fan, a sword for someone who likes it close),
and -- for a veteran or a collector -- a weapon or two from the Event Armory.
This module says which weapons a bot would buy, and lays its hotbar out from
whatever it owns, so the brain in a game has them to hand and uses them.

It imports nothing but the catalogue: the game host's brain reads
``preference`` and ``free`` too.
"""
from __future__ import annotations

import random
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from ..models import catalog

# the shelf weapons and the preference trait (personas: wp_*) each answers to
SHELF = {"use_sniper": "wp_sniper", "use_smg": "wp_smg", "use_rifle": "wp_rifle",
         "use_sword": "wp_melee", "use_rocket": "wp_rocket"}
# the weapons every account starts with, by hotbar slot
FREE = tuple(item_id for item_id in catalog.DEFAULT_HOTBAR if item_id)
GEAR = frozenset(("support", "consume", "deploy", "ability", "summon", "strike"))


def stats_of(item: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    return ((item or {}).get("data") or {}).get("stats") or {}


def free(item_id: str) -> bool:
    """One of the weapons everybody has without buying it."""
    return item_id in FREE


def preference(item: Any) -> str:
    """The trait a weapon answers to -- the shelf ones by name, the rest by
    what kind of weapon they are -- or '' for gear (abilities, a medkit)."""
    if isinstance(item, str):
        item = catalog.get(item)
    if not item:
        return ""
    if item["id"] in SHELF:
        return SHELF[item["id"]]
    if item["id"] == "use_buildhammer":
        return "wp_melee"
    stats = stats_of(item)
    kind = stats.get("kind")
    if kind == "melee":
        return "wp_melee"
    if kind == "projectile":
        return "wp_rocket"
    if kind in ("beam", "cone"):
        return "wp_smg"
    if kind == "hitscan":
        if int(stats.get("pellets", 1) or 1) > 1:
            return "wp_shotgun"
        if float(stats.get("range", 200) or 200) >= 600:
            return "wp_sniper"
        return "wp_smg" if stats.get("auto") else "wp_rifle"
    return ""


def role(item: Any) -> str:
    """'melee', 'close' (a spread, a beam or a cone), 'gear' or 'gun'."""
    if isinstance(item, str):
        item = catalog.get(item)
    stats = stats_of(item)
    kind = stats.get("kind")
    if kind == "melee":
        return "melee"
    if kind in GEAR:
        return "gear"
    if kind in ("beam", "cone") or int(stats.get("pellets", 1) or 1) > 1:
        return "close"
    return "gun"


def wanted(traits: Dict[str, float], tags: Sequence[str], rng: random.Random,
           armory: Iterable[Dict[str, Any]] = ()) -> List[str]:
    """The weapons a bot buys.  Each shelf weapon on its preference (a strong
    one always); a hammer for builders and tycoon fans; a medkit for team
    players; and from the Event Armory, more likely the longer it has been
    about and the more it collects, one weapon or two."""
    out: List[str] = []
    for item_id, key in SHELF.items():
        pull = float(traits.get(key, 0.3))
        if pull > 0.75 or rng.random() < 0.15 + pull * 0.6:
            out.append(item_id)
    if ("tycoon_fan" in tags or "builder" in tags) and rng.random() < 0.6:
        out.append("use_buildhammer")
    if float(traits.get("support", 0.2)) > 0.4 and rng.random() < 0.7:
        out.append("use_medkit")
    pool = [it for it in armory if it.get("slot") == "usable" and int(it.get("price", 0)) > 0]
    chance = 0.2 + float(traits.get("collector", 0.3)) * 0.4
    if "veteran" in tags:
        chance += 0.25
    if "newbie" in tags:
        chance -= 0.15
    if pool and rng.random() < chance:
        for _ in range(1 if rng.random() < 0.65 else 2):
            weights = []
            for it in pool:
                key = preference(it)
                w = 0.4 + (float(traits.get(key, 0.3)) if key else 0.25)
                if it.get("rarity") == "legendary":
                    w *= 0.6 + float(traits.get("collector", 0.3))
                weights.append(w)
            choice = rng.choices(pool, weights)[0]
            pool = [it for it in pool if it["id"] != choice["id"]]
            out.append(choice["id"])
            if not pool:
                break
    return list(dict.fromkeys(out))


def lay_out(owned: Iterable[Tuple[int, str]], traits: Dict[str, float],
            rng: random.Random, keep: Sequence[str] = ()) -> List[int]:
    """A hotbar (inventory ids, 0 for empty) from what a bot owns, given as
    (inventory id, item id) pairs.

    The free three keep their places, and the weapons it bought go in the
    empty slots, the ones it likes best first.  Any more take over from the
    free weapon that does the same job -- a melee weapon from the stick, a
    close-range one from the shotgun, anything else from the stick and then
    the shotgun.  The pistol stays, so there is always something to shoot.
    A free weapon named in ``keep`` keeps its place this time (``change_up``
    leaves the stick or the shotgun in now and then).  Only what is owned
    ever goes on it."""
    size = catalog.HOTBAR_SIZE
    hotbar = [0] * size
    first: Dict[str, int] = {}
    for inv_id, item_id in owned:
        item = catalog.get(item_id)
        if item is None or item.get("slot") != "usable" or item_id in first:
            continue
        first[item_id] = int(inv_id)
    for index, item_id in enumerate(catalog.DEFAULT_HOTBAR[:size]):
        if item_id and item_id in first:
            hotbar[index] = first[item_id]

    def liking(item_id: str) -> float:
        key = preference(item_id)
        base = float(traits.get(key, 0.35)) if key else float(traits.get("support", 0.2)) * 0.8
        price = int((catalog.get(item_id) or {}).get("price", 0))
        return base + price / 4000.0 + rng.random() * 0.25

    bought = sorted((i for i in first if not free(i)), key=liking, reverse=True)[:size - 1]
    free_slot = {item_id: index for index, item_id in enumerate(catalog.DEFAULT_HOTBAR[:size]) if item_id}
    stick, shotgun = free_slot.get("use_stick"), free_slot.get("use_shotgun")

    def holds_free(index: Optional[int]) -> bool:
        if index is None or catalog.DEFAULT_HOTBAR[index] in keep:
            return False
        return hotbar[index] in (0, first.get(catalog.DEFAULT_HOTBAR[index]))

    for item_id in bought:
        empty = [i for i in range(size) if not hotbar[i] and not catalog.DEFAULT_HOTBAR[i]]
        if empty:
            hotbar[empty[0]] = first[item_id]
            continue
        job = role(item_id)
        order = [stick] if job == "melee" else [shotgun] if job == "close" else [stick, shotgun]
        for index in order:
            if holds_free(index):
                hotbar[index] = first[item_id]
                break
    return hotbar


# ------------------------------------------------------------ changing up
# How much a persona scales the platform's chance per minute that a bot
# changes up its hotbar (the Bots Zone's "Hotbar changes"): collectors and
# chaotic players change theirs often, explorers a little more, the most
# skilled stick with what works.  CHANGE_MAX is the most it can scale it --
# the director rolls against that first and the bot's own factor after, so
# it only reads the persona of a bot that might change.
CHANGE_MAX = 3.0
WEAPON_KEYS = ("wp_sniper", "wp_shotgun", "wp_smg", "wp_rifle", "wp_melee", "wp_rocket")


def change_factor(traits: Dict[str, float]) -> float:
    f = (0.6 + float(traits.get("collector", 0.3)) * 1.0 + float(traits.get("chaos", 0.08)) * 2.0
         + float(traits.get("explore", 0.2)) * 0.5 - float(traits.get("skill", 0.5)) * 0.3)
    return max(0.25, min(CHANGE_MAX, f))


def change_up(owned: Sequence[Tuple[int, str]], traits: Dict[str, float],
              rng: random.Random, current: Sequence[int]) -> List[int]:
    """A different hotbar from what a bot already owns -- nothing bought,
    nothing given.  Today it fancies something else (its weapon preferences
    nudged up and down), so it carries a different pick -- when it owns
    more than fits -- in a different order, and now and then keeps the
    stick or the shotgun in.  The pistol stays in slot 1.  A bot with
    nothing but the free three has nothing to change: its hotbar comes back
    as it was, and so does one whose things only go one way."""
    current = list(current)
    items = set()
    for _inv, item_id in owned:
        item = catalog.get(item_id)
        if item is not None and item.get("slot") == "usable":
            items.add(item_id)
    if not any(not free(i) for i in items):
        return current
    for _ in range(8):
        mood = dict(traits)
        for key in WEAPON_KEYS:
            mood[key] = float(traits.get(key, 0.3)) + rng.uniform(-0.45, 0.45)
        keep = [i for i in ("use_stick", "use_shotgun") if rng.random() < 0.3]
        bar = lay_out(owned, mood, rng, keep=keep)
        if rng.random() < 0.6:
            # and moves things round: everything but the pistol in slot 1
            rest = bar[1:]
            rng.shuffle(rest)
            bar = bar[:1] + rest
        if bar != current:
            return bar
    return current


def shuffle_all(owned: Sequence[Tuple[int, str]], rng: random.Random,
                current: Sequence[int]) -> List[int]:
    """Every slot of the hotbar chosen afresh (the Bots Zone's "Shuffle
    loadouts"): up to five of the bot's own weapons and held items, picked
    at random and dealt into the five slots in a random order -- slot 1
    included, so the pistol can go too -- with at least one weapon among
    them, so there is always something to fight with.  Nothing is bought or
    given.  A bot that owns no more than fits gets the same things in a new
    order; one with nothing to move gets its hotbar back as it was."""
    size = catalog.HOTBAR_SIZE
    current = list(current)
    first: Dict[str, int] = {}
    for inv_id, item_id in owned:
        item = catalog.get(item_id)
        if item is None or item.get("slot") != "usable" or item_id in first:
            continue
        first[item_id] = int(inv_id)
    if not first:
        return current
    items = sorted(first)
    weapons = [i for i in items if role(i) != "gear"]
    for _ in range(12):
        picked = rng.sample(items, min(size, len(items)))
        if weapons and all(role(i) == "gear" for i in picked):
            picked[rng.randrange(len(picked))] = rng.choice(weapons)
        bar = [first[i] for i in picked] + [0] * (size - len(picked))
        rng.shuffle(bar)
        if bar != current:
            return bar
    return current


def open_loadout(pool: Sequence[str], rng: random.Random, size: Optional[int] = None) -> List[str]:
    """A hotbar's worth of weapons picked at random from ``pool`` (the
    marketplace's weapons, for the Bots Zone's "Open shuffle"): as many
    different ones as there are slots, dealt in a random order.  Not all of
    them melee when the pool has anything else, so the bot can always hit
    something it can't reach."""
    size = catalog.HOTBAR_SIZE if size is None else int(size)
    pool = list(dict.fromkeys(i for i in pool if catalog.get(i) is not None))
    if not pool or size <= 0:
        return []
    picked = rng.sample(pool, min(size, len(pool)))
    if all(role(i) == "melee" for i in picked):
        reach = [i for i in pool if role(i) != "melee" and i not in picked]
        if reach:
            picked[rng.randrange(len(picked))] = rng.choice(reach)
    rng.shuffle(picked)
    return picked


# ----------------------------------------------------------- between games
def plan(owned: Sequence[Tuple[int, str]], traits: Dict[str, float],
         rng: random.Random, current: Sequence[int], unsettled: bool = False) -> List[int]:
    """Between games (Dynamic Modifiers' "Loadout planning"): which weapons a
    bot takes into its next game, chosen from what it already owns.  Mostly
    it settles on what it likes best -- its own preferences, give or take a
    little -- the way a player goes back to their favourite set; now and then
    (more often for an explorer, much more after a rough game) it tries
    something different instead (``change_up``).  Nothing is bought or
    given, and the pistol stays in slot 1.  The hotbar comes back as it was
    when it already holds what the bot would choose."""
    current = list(current)
    explore = 0.2 + float(traits.get("explore", 0.2)) * 0.4 + (0.35 if unsettled else 0.0)
    if rng.random() < explore:
        return change_up(owned, traits, rng, current)
    mood = dict(traits)
    for key in WEAPON_KEYS:
        mood[key] = float(traits.get(key, 0.3)) + rng.uniform(-0.12, 0.12)
    return lay_out(owned, mood, rng)
