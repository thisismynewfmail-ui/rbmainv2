"""Pet care: how a pet is doing, for the Pet Zone (/pet-zone).

Four needs -- fullness, happiness, energy and cleanliness, each 0 to 100 --
and a bond that only ever grows.  Nothing runs in the background.  A pet's
needs are stored as they stood at ``settled_at`` and every read works out
where they have got to since (settle()), so a pet nobody has visited for a
week costs nothing until somebody does:

  * awake, every need runs down at its own hourly rate (DECAY);
  * asleep, her energy comes back fast (NAP_GAIN) and everything else runs
    down at half speed -- and she wakes up by herself once she is rested,
    which settle() places at the exact second it happened.

Looking after her is a handful of actions (ACTIONS), each with its own
cooldown, plus a once-a-day greeting.  What an action does leans on who she
is: every persona tag makes some needs run down faster or slower and some
actions loved or disliked (PERSONA), every species has a favourite treat,
and the toys suit some personas more than others.  The bond grows with
every kindness, a little more for the ones she loves, up to DAILY_BOND a day
(the greeting is on top), and passes named milestones on the way.

The table is app/db.py's (``pet_care``), keyed like ``pets`` on the
inventory row that is the pet.  How she looks and who she is stays in
app/models/pets.py; the Pet Zone page and its API are app/views/pets_view.py
and the room itself is static/js/ui/pet_zone.js.
"""
from __future__ import annotations

import json
import math
import time
from typing import Any, Dict, List, Optional

from .. import db
from . import pets

# ------------------------------------------------------------------- needs
NEEDS = ["fullness", "happiness", "energy", "cleanliness"]
NEED_LABELS = {"fullness": "Fullness", "happiness": "Happiness", "energy": "Energy",
               "cleanliness": "Cleanliness"}
# A new pet arrives fed, happy and freshly brushed.
START = {"fullness": 75.0, "happiness": 80.0, "energy": 85.0, "cleanliness": 90.0}
# How far each need falls in an hour while she is awake.  Paced for a visit
# a day: left full and happy, she is hungry and bored by the same time
# tomorrow, and starving and sad the day after.
DECAY = {"fullness": 3.0, "happiness": 2.5, "energy": 2.0, "cleanliness": 1.6}
NAP_SLOW = 0.5            # asleep, the other needs fall at half speed
NAP_GAIN = 12.0           # energy back per minute asleep: empty to full in ~8
HOUR = 3600.0
DAY = 86400

# ----------------------------------------------------------------- persona
# What each persona tag changes about looking after her: how fast a need
# runs down (a multiplier on DECAY), which actions she loves (half as much
# happiness again, and a bond point) and which she would rather you did not
# (half the happiness).  Tags are app/models/pets.py's TAGS.
PERSONA: Dict[str, Dict[str, Any]] = {
    "cheerful": {"decay": {"happiness": 0.75}, "loves": ["cheer"]},
    "shy": {"loves": ["pat"], "dislikes": ["cheer"]},
    "curious": {"loves": ["play"]},
    "loyal": {"loves": ["pat"], "bond": 1.5},
    "sleepy": {"decay": {"energy": 1.4}, "loves": ["nap"]},
    "energetic": {"decay": {"energy": 1.25, "fullness": 1.2}, "loves": ["play"]},
    "feisty": {"loves": ["play"], "dislikes": ["brush"]},
    "dreamy": {"loves": ["brush", "nap"]},
    "playful": {"loves": ["tickle", "play"]},
    "brave": {"loves": ["cheer"]},
    "clingy": {"decay": {"happiness": 1.4}, "loves": ["pat"]},
    "showoff": {"loves": ["brush", "cheer"]},
    "chatty": {"loves": ["cheer", "tickle"]},
    "clumsy": {"decay": {"cleanliness": 1.35}, "dislikes": ["tickle"]},
}

# ------------------------------------------------------------------ treats
# What each treat does to her.  The order is the tray's.
TREATS: Dict[str, Dict[str, Any]] = {
    "cookie": {"name": "Star Cookie", "blurb": "Sweet, crumbly, star-shaped.",
               "fullness": 10, "happiness": 7},
    "berries": {"name": "Berry Bowl", "blurb": "A bowl of fresh berries. Good for her.",
                "fullness": 10, "happiness": 4, "energy": 3},
    "riceball": {"name": "Rice Ball", "blurb": "Big, plain and very filling.",
                 "fullness": 24, "happiness": 3, "energy": 4},
    "carrot": {"name": "Crunchy Carrot", "blurb": "Crunch crunch crunch.",
               "fullness": 12, "happiness": 3, "energy": 4},
    "pudding": {"name": "Pudding Cup", "blurb": "Wobbly, delicious and a bit messy.",
                "fullness": 14, "happiness": 10, "cleanliness": -5},
    "pepper": {"name": "Fire Pepper", "blurb": "Hot! A burst of energy, and steam.",
               "fullness": 8, "happiness": 4, "energy": 12},
    "mooncake": {"name": "Moon Cake", "blurb": "Golden pastry, a moon on top.",
                 "fullness": 16, "happiness": 7, "energy": 2},
    "bytebar": {"name": "Byte Bar", "blurb": "Crunchy, charged, slightly fizzy.",
                "fullness": 12, "happiness": 4, "energy": 10},
}
TREAT_ORDER = ["cookie", "berries", "riceball", "carrot", "pudding", "pepper", "mooncake",
               "bytebar"]
# every species has one she loves more than the rest
FAVOURITE = {"fern": "berries", "ember": "pepper", "luna": "mooncake", "mochi": "carrot",
             "pixel": "bytebar"}

# -------------------------------------------------------------------- toys
TOYS: Dict[str, Dict[str, Any]] = {
    "ball": {"name": "Bouncy Ball", "blurb": "Throw it and she chases it down.",
             "happiness": 14, "energy": -10, "fullness": -3, "cleanliness": -5},
    "plush": {"name": "Star Plushie", "blurb": "Soft. She catches it and cuddles it.",
              "happiness": 12, "energy": -5, "fullness": -2, "cleanliness": -2},
    "wand": {"name": "Feather Wand", "blurb": "Wiggle it and she pounces.",
             "happiness": 13, "energy": -8, "fullness": -3, "cleanliness": -3},
}
TOY_ORDER = ["ball", "plush", "wand"]
# which toy suits which persona: a quarter as much happiness again
TOY_FANS = {"ball": ["playful", "energetic", "brave"], "plush": ["dreamy", "clingy", "shy"],
            "wand": ["curious", "feisty", "showoff"]}

# ----------------------------------------------------------------- actions
# What each action does on its own (before persona and treat), its cooldown
# in seconds and the bond it is worth.  ``item`` names the list the action
# takes an item from.
ACTIONS: Dict[str, Dict[str, Any]] = {
    "pat": {"name": "Pat", "cooldown": 3, "bond": 1, "happiness": 5},
    "feed": {"name": "Feed", "cooldown": 6, "bond": 2, "item": "treat"},
    "play": {"name": "Play", "cooldown": 10, "bond": 3, "item": "toy"},
    "brush": {"name": "Brush", "cooldown": 8, "bond": 2, "cleanliness": 30, "happiness": 3},
    "tickle": {"name": "Tickle", "cooldown": 6, "bond": 1, "happiness": 8, "energy": -2},
    "cheer": {"name": "Cheer", "cooldown": 8, "bond": 1, "happiness": 6, "energy": 5},
    "nap": {"name": "Nap", "cooldown": 15, "bond": 1},
    "wake": {"name": "Wake", "cooldown": 2, "bond": 0},
}
ACTION_ORDER = ["pat", "feed", "play", "brush", "tickle", "cheer", "nap"]
# The thresholds an action is refused at.
FULL_AT = 95          # feed: she is stuffed
TIRED_AT = 10         # play: too tired
NOT_SLEEPY_AT = 85    # nap: not sleepy yet
SPOTLESS_AT = 98      # brush: nothing to brush
GROGGY_BELOW = 60     # woken before this much energy, she is a little cross

# -------------------------------------------------------------------- bond
DAILY_BOND = 60       # from care, a day; the greeting is on top
MILESTONES: List[Dict[str, Any]] = [
    {"at": 0, "name": "Just Met", "blurb": "She is still working out who you are."},
    {"at": 20, "name": "Getting Acquainted", "blurb": "She knows your face now, and perks up when you come in."},
    {"at": 60, "name": "Pals", "blurb": "She saves you the comfy end of the cushion."},
    {"at": 140, "name": "Good Friends", "blurb": "She runs to the door when she hears you."},
    {"at": 280, "name": "Close Friends", "blurb": "She tells you everything. Even the boring bits."},
    {"at": 480, "name": "Best Friends", "blurb": "You are her favourite person, and she says so."},
    {"at": 760, "name": "Kindred Spirits", "blurb": "She knows what you are going to do before you do."},
    {"at": 1120, "name": "Inseparable", "blurb": "Wherever you go, she is already there."},
    {"at": 1600, "name": "Soulmates", "blurb": "Two of a kind. There is nothing more to say."},
]

# -------------------------------------------------------------------- mood
# In order of urgency: the first that fits is her mood.  ``need`` is the
# action that would help, which the Pet Zone lights up.
MOODS: Dict[str, Dict[str, str]] = {
    "asleep": {"label": "Fast asleep", "line": "Dreaming. Let her sleep.", "need": "wake"},
    "starving": {"label": "Starving", "line": "Her tummy is growling. Feed her!", "need": "feed"},
    "exhausted": {"label": "Exhausted", "line": "She can barely keep her eyes open.", "need": "nap"},
    "sad": {"label": "Sad", "line": "She could really use some attention.", "need": "pat"},
    "hungry": {"label": "Peckish", "line": "She keeps glancing at her bowl.", "need": "feed"},
    "sleepy": {"label": "Sleepy", "line": "Yawning. A nap would do her good.", "need": "nap"},
    "grubby": {"label": "Grubby", "line": "She could do with a good brush.", "need": "brush"},
    "lonely": {"label": "Lonely", "line": "She wants a fuss made of her.", "need": "pat"},
    "bored": {"label": "Bored", "line": "She wants to play.", "need": "play"},
    "ecstatic": {"label": "Over the moon", "line": "She could not be happier.", "need": ""},
    "happy": {"label": "Happy", "line": "Having a lovely day.", "need": ""},
    "content": {"label": "Content", "line": "Pottering about, quite happily.", "need": ""},
}
# the moods that mean she needs something (a little badge on the switcher)
NEEDY = {"starving", "exhausted", "sad", "hungry", "sleepy", "grubby", "lonely", "bored"}

COUNT_KEYS = ["pat", "feed", "play", "brush", "tickle", "cheer", "nap", "greet"]
RATE_LIMIT = (60, 60)     # actions per user per minute, whatever their cooldowns


class CareError(Exception):
    """An action that cannot happen.  ``code`` says why -- "invalid" and
    "not_owned" are mistakes; "cooldown" and the refusals (full, tired,
    asleep, ...) are her saying no, and come with her state so the page can
    show it.  ``status`` is the HTTP status the API answers with."""

    def __init__(self, message: str, code: str = "invalid", status: int = 400,
                 retry_in: float = 0.0, care: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.code = code
        self.status = status
        self.retry_in = retry_in
        self.care = care


def _now() -> int:
    return int(time.time())


def day_of(when: float) -> int:
    """The day number a timestamp falls on (UTC): greetings and the daily
    bond allowance turn over at midnight UTC."""
    return int(when // DAY)


def _load(raw: Any) -> Dict[str, Any]:
    try:
        value = json.loads(raw or "{}")
    except (TypeError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def _clamp(v: float) -> float:
    return 0.0 if v < 0 else (100.0 if v > 100 else v)


# ----------------------------------------------------------------- persona
def rates(tags: List[str]) -> Dict[str, float]:
    """How fast each need runs down for a pet with these tags, per hour."""
    out = dict(DECAY)
    for tag in tags or []:
        for need, k in (PERSONA.get(tag, {}).get("decay") or {}).items():
            out[need] *= k
    return out


def leanings(tags: List[str]) -> Dict[str, List[str]]:
    """The actions she loves and dislikes, from her persona tags (a tag that
    loves an action outweighs one that dislikes it)."""
    loves: List[str] = []
    dislikes: List[str] = []
    for tag in tags or []:
        info = PERSONA.get(tag, {})
        loves += [a for a in info.get("loves", []) if a not in loves]
        dislikes += [a for a in info.get("dislikes", []) if a not in dislikes]
    return {"loves": loves, "dislikes": [a for a in dislikes if a not in loves]}


def favourite_toy(tags: List[str]) -> str:
    for toy in TOY_ORDER:
        if any(t in TOY_FANS[toy] for t in tags or []):
            return toy
    return "ball"


# ------------------------------------------------------------------ decay
def settle(row: Dict[str, Any], tags: List[str], now: Optional[float] = None) -> Dict[str, Any]:
    """Where her needs have got to by ``now``: a new row (the input is left
    alone) with the needs, ``settled_at`` and the nap brought up to date.
    ``woke_at`` is set when she woke up by herself on the way."""
    now = _now() if now is None else now
    out = dict(row)
    t0 = float(row.get("settled_at") or now)
    span = max(0.0, now - t0)
    per_hour = rates(tags)
    needs = {k: float(row.get(k, START[k])) for k in NEEDS}
    out["woke_at"] = 0
    if row.get("napping_since"):
        gain = NAP_GAIN / 60.0
        rested = max(0.0, (100.0 - needs["energy"]) / gain)
        asleep = min(span, rested)
        needs["energy"] = needs["energy"] + gain * asleep
        for k in NEEDS:
            if k != "energy":
                needs[k] -= per_hour[k] / HOUR * NAP_SLOW * asleep
        if asleep < span:
            # she woke up rested, and has been up and about since
            out["napping_since"] = 0
            out["woke_at"] = int(t0 + asleep)
            span -= asleep
        else:
            span = 0.0
    for k in NEEDS:
        needs[k] = _clamp(needs[k] - per_hour[k] / HOUR * span)
    out.update(needs)
    out["settled_at"] = int(now)
    return out


def nap_left(row: Dict[str, Any]) -> int:
    """Seconds until a napping pet wakes up by herself (0 when awake)."""
    if not row.get("napping_since"):
        return 0
    return int(math.ceil(max(0.0, 100.0 - float(row["energy"])) / (NAP_GAIN / 60.0)))


def mood_of(needs: Dict[str, float], napping: bool, tags: List[str]) -> str:
    if napping:
        return "asleep"
    f, h, e, c = (needs[k] for k in NEEDS)
    if f < 15:
        return "starving"
    if e < 15:
        return "exhausted"
    if h < 20:
        return "sad"
    if f < 35:
        return "hungry"
    if e < 30:
        return "sleepy"
    if c < 25:
        return "grubby"
    if h < 40:
        return "lonely" if "clingy" in (tags or []) else "bored"
    if h >= 85 and min(f, e, c) >= 60:
        return "ecstatic"
    if h >= 65 and min(f, e, c) >= 40:
        return "happy"
    return "content"


def milestone(points: int) -> Dict[str, Any]:
    """The bond level ``points`` is at: its index, name and blurb, where it
    starts, the next one and how far along to it."""
    level = 0
    for i, m in enumerate(MILESTONES):
        if points >= m["at"]:
            level = i
    here = MILESTONES[level]
    nxt = MILESTONES[level + 1] if level + 1 < len(MILESTONES) else None
    progress = 1.0
    if nxt:
        progress = (points - here["at"]) / float(nxt["at"] - here["at"])
    return {"level": level, "name": here["name"], "blurb": here["blurb"], "floor": here["at"],
            "next": dict(nxt) if nxt else None, "progress": round(progress, 4)}


# ----------------------------------------------------------------- storage
def _pet(user_id: int, inv_id: int) -> Dict[str, Any]:
    pet = next((p for p in pets.owned(user_id) if p["inv_id"] == int(inv_id or 0)), None)
    if pet is None:
        raise CareError("You do not own that pet.", "not_owned", 404)
    return pet


def _row(user_id: int, inv_id: int, now: int) -> Dict[str, Any]:
    row = db.query_one("SELECT * FROM pet_care WHERE inv_id=?", (inv_id,))
    if row is None or int(row["user_id"]) != int(user_id):
        # first visit (or she changed hands): she arrives fed and brushed
        db.execute("INSERT OR REPLACE INTO pet_care(inv_id,user_id,fullness,happiness,energy,"
                   "cleanliness,settled_at,created_at) VALUES(?,?,?,?,?,?,?,?)",
                   (inv_id, user_id, START["fullness"], START["happiness"], START["energy"],
                    START["cleanliness"], now, now))
        row = db.query_one("SELECT * FROM pet_care WHERE inv_id=?", (inv_id,))
    return dict(row)


def _save(row: Dict[str, Any], cooldowns: Dict[str, Any], counts: Dict[str, Any]) -> None:
    db.execute("UPDATE pet_care SET fullness=?, happiness=?, energy=?, cleanliness=?, "
               "settled_at=?, napping_since=?, bond=?, bond_day=?, bond_today=?, greeted_day=?, "
               "streak=?, cooldowns=?, counts=? WHERE inv_id=? AND user_id=?",
               (round(row["fullness"], 3), round(row["happiness"], 3), round(row["energy"], 3),
                round(row["cleanliness"], 3), int(row["settled_at"]), int(row["napping_since"]),
                int(row["bond"]), int(row["bond_day"]), int(row["bond_today"]),
                int(row["greeted_day"]), int(row["streak"]),
                json.dumps(cooldowns, separators=(",", ":")),
                json.dumps(counts, separators=(",", ":")), row["inv_id"], row["user_id"]))


# ------------------------------------------------------------------- state
def describe(row: Dict[str, Any], pet: Dict[str, Any], now: Optional[int] = None) -> Dict[str, Any]:
    """Everything the Pet Zone shows about how she is, from a settled row."""
    now = _now() if now is None else now
    tags = pet.get("tags") or []
    napping = bool(row.get("napping_since"))
    needs = {k: float(row[k]) for k in NEEDS}
    mood = mood_of(needs, napping, tags)
    cooldowns = _load(row.get("cooldowns"))
    left = {}
    for action, info in ACTIONS.items():
        since = now - float(cooldowns.get(action, 0) or 0)
        left[action] = round(max(0.0, info["cooldown"] - since), 1)
    today = day_of(now)
    counts = _load(row.get("counts"))
    bond = int(row.get("bond") or 0)
    lean = leanings(tags)
    per_hour = rates(tags)
    return {
        "inv_id": int(row["inv_id"]),
        "needs": {k: round(v, 2) for k, v in needs.items()},
        "rates": {k: round(v / HOUR, 6) for k, v in per_hour.items()},
        "nap_gain": round(NAP_GAIN / 60.0, 6), "nap_slow": NAP_SLOW,
        "napping": napping, "nap_left": nap_left(row),
        "mood": dict(MOODS[mood], id=mood, needy=mood in NEEDY),
        "bond": dict(milestone(bond), points=bond,
                     today=int(row.get("bond_today") or 0) if int(row.get("bond_day") or 0) == today else 0,
                     cap=DAILY_BOND),
        "streak": int(row.get("streak") or 0),
        "greet_ready": int(row.get("greeted_day") or 0) != today,
        "cooldowns": left,
        "counts": {k: int(counts.get(k, 0) or 0) for k in COUNT_KEYS},
        "loves": lean["loves"], "dislikes": lean["dislikes"],
        "favourite_treat": FAVOURITE.get(pet["species"], ""),
        "favourite_toy": favourite_toy(tags),
        "since": int(row.get("created_at") or now), "now": now,
    }


def state(user_id: int, inv_id: int, now: Optional[int] = None) -> Dict[str, Any]:
    """How one of your pets is doing right now (read-only, but for a pet's
    very first visit, which gives her a row)."""
    now = _now() if now is None else now
    pet = _pet(user_id, inv_id)
    row = _row(user_id, pet["inv_id"], now)
    return describe(settle(row, pet["tags"], now), pet, now)


def summary(user_id: int, now: Optional[int] = None) -> Dict[int, Dict[str, Any]]:
    """Each of your pets' mood and bond level, for the switcher."""
    now = _now() if now is None else now
    out = {}
    for pet in pets.owned(user_id):
        row = settle(_row(user_id, pet["inv_id"], now), pet["tags"], now)
        needs = {k: float(row[k]) for k in NEEDS}
        mood = mood_of(needs, bool(row.get("napping_since")), pet["tags"])
        out[pet["inv_id"]] = {"mood": mood, "label": MOODS[mood]["label"],
                              "needy": mood in NEEDY,
                              "bond": milestone(int(row.get("bond") or 0))["name"]}
    return out


# ------------------------------------------------------------------ acting
def _gain(base: float, loved: bool, disliked: bool, extra: float = 1.0) -> float:
    if base <= 0:
        return base
    k = extra * (1.5 if loved else 1.0) * (0.5 if disliked else 1.0)
    return base * k


def act(user_id: int, inv_id: Any, action: Any, item: Any = None,
        now: Optional[int] = None) -> Dict[str, Any]:
    """Do one thing for one of your pets.  Returns {"care": her state after,
    "result": what happened}; raises CareError when it cannot happen."""
    now = _now() if now is None else now
    action = str(action or "").strip().lower()
    if action not in ACTIONS and action != "greet":
        raise CareError("Unknown action.")
    try:
        inv_id = int(inv_id or 0)
    except (TypeError, ValueError):
        raise CareError("Unknown pet.")
    info = ACTIONS.get(action, {"cooldown": 0, "bond": 0})
    item = str(item or "").strip().lower() if item is not None else ""
    if info.get("item") == "treat" and item not in TREATS:
        raise CareError("Unknown treat.")
    if info.get("item") == "toy" and item not in TOYS:
        raise CareError("Unknown toy.")
    if not info.get("item"):
        item = ""
    with db.transaction():
        pet = _pet(user_id, inv_id)
        tags = pet["tags"]
        row = settle(_row(user_id, inv_id, now), tags, now)
        cooldowns = _load(row.get("cooldowns"))
        counts = _load(row.get("counts"))
        napping = bool(row["napping_since"])
        today = day_of(now)

        def refuse(message: str, code: str, status: int = 409, retry: float = 0.0):
            raise CareError(message, code, status, retry, describe(row, pet, now))

        if napping and action != "wake":
            refuse("Shh -- she is asleep.", "asleep")
        if action == "wake" and not napping:
            refuse("She is already up.", "awake")
        if action == "greet" and int(row["greeted_day"] or 0) == today:
            refuse("You have said hello today already.", "greeted")
        if action != "greet":
            wait = info["cooldown"] - (now - float(cooldowns.get(action, 0) or 0))
            if wait > 0:
                refuse("Give her a moment.", "cooldown", 429, round(wait, 1))
        if action == "feed" and row["fullness"] >= FULL_AT:
            refuse("She is stuffed!", "full")
        if action == "play" and row["energy"] < TIRED_AT:
            refuse("She is too tired to play.", "tired")
        if action == "nap" and row["energy"] >= NOT_SLEEPY_AT:
            refuse("She is not sleepy yet.", "not_sleepy")
        if action == "brush" and row["cleanliness"] >= SPOTLESS_AT:
            refuse("She is spotless already.", "spotless")

        lean = leanings(tags)
        loved = action in lean["loves"]
        disliked = action in lean["dislikes"]
        favourite = False
        effects: Dict[str, float] = {k: float(info.get(k, 0)) for k in NEEDS}
        extra = 1.0
        if action == "feed":
            effects = {k: float(TREATS[item].get(k, 0)) for k in NEEDS}
            favourite = FAVOURITE.get(pet["species"]) == item
            loved = loved or favourite
        elif action == "play":
            effects = {k: float(TOYS[item].get(k, 0)) for k in NEEDS}
            favourite = favourite_toy(tags) == item
            extra = 1.25 if favourite else 1.0
        elif action == "wake":
            # woken before she was rested, she is a little cross about it
            if row["energy"] < GROGGY_BELOW:
                effects["happiness"] = -3.0
        effects["happiness"] = _gain(effects["happiness"], loved, disliked, extra)

        before = {k: row[k] for k in NEEDS}
        for k in NEEDS:
            row[k] = _clamp(row[k] + effects[k])
        if action == "nap":
            row["napping_since"] = now
        elif action == "wake":
            row["napping_since"] = 0

        # the bond
        if int(row["bond_day"] or 0) != today:
            row["bond_day"], row["bond_today"] = today, 0
        old_level = milestone(int(row["bond"]))["level"]
        streak = int(row["streak"] or 0)
        if action == "greet":
            streak = streak + 1 if int(row["greeted_day"] or 0) == today - 1 else 1
            row["greeted_day"], row["streak"] = today, streak
            row["happiness"] = _clamp(row["happiness"] + 10)
            gained = 4 + min(streak, 6)
        else:
            raw = info["bond"] + (1 if loved and info["bond"] else 0)
            for tag in tags:
                raw = int(math.ceil(raw * PERSONA.get(tag, {}).get("bond", 1)))
            gained = max(0, min(raw, DAILY_BOND - int(row["bond_today"])))
            row["bond_today"] = int(row["bond_today"]) + gained
        row["bond"] = int(row["bond"]) + gained
        new = milestone(int(row["bond"]))

        if action != "greet":
            cooldowns[action] = now
        counts[action] = int(counts.get(action, 0) or 0) + 1
        _save(row, cooldowns, counts)
        # the answer describes her as saved: this cooldown started, this
        # count gone up
        row["cooldowns"] = json.dumps(cooldowns)
        row["counts"] = json.dumps(counts)

    care = describe(row, pet, now)
    return {"care": care, "result": {
        "action": action, "item": item, "loved": loved, "disliked": disliked,
        "favourite": favourite, "bond": gained, "streak": int(row["streak"] or 0),
        "capped": action != "greet" and info["bond"] > 0 and gained == 0,
        "deltas": {k: round(row[k] - before[k], 1) for k in NEEDS},
        "milestone": ({"level": new["level"], "name": new["name"], "blurb": new["blurb"]}
                      if new["level"] > old_level else None),
    }}


# ----------------------------------------------------------- for the page
def catalogue() -> Dict[str, Any]:
    """The fixed parts of the Pet Zone: actions (and what each does on its
    own, which the page shows at once and the server's answer then
    corrects), treats, toys, milestones, moods and need labels, as the
    page's script wants them."""
    return {
        "actions": [{"id": a, "name": ACTIONS[a]["name"], "cooldown": ACTIONS[a]["cooldown"]}
                    for a in ACTION_ORDER],
        "effects": {a: {k: ACTIONS[a][k] for k in NEEDS if k in ACTIONS[a]} for a in ACTIONS},
        "treats": [dict(TREATS[t], id=t) for t in TREAT_ORDER],
        "toys": [dict(TOYS[t], id=t) for t in TOY_ORDER],
        "milestones": MILESTONES, "moodInfo": MOODS, "needs": NEEDS, "needLabels": NEED_LABELS,
        "dailyBond": DAILY_BOND, "favourites": FAVOURITE, "toyFans": TOY_FANS,
        "thresholds": {"full": FULL_AT, "tired": TIRED_AT, "notSleepy": NOT_SLEEPY_AT,
                       "spotless": SPOTLESS_AT, "groggy": GROGGY_BELOW},
    }
