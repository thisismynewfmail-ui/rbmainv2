"""Making bots: the creation pipeline and the jobs that run it.

A bot is created in a fixed order, because each step needs the one before it
and a failure part-way must never leave half an account behind:

1. **Names** are reserved first.  The language model is asked for a batch,
   shown the example usernames, and every candidate is normalised, checked
   against the site's rules, against the database and against the rest of the
   batch.  Names that are taken or broken are *told to the model* -- "these
   are taken: ..., give me N more" -- in the same conversation, a bounded
   number of times; whatever is still missing comes from the built-in
   generator (or is simply not created, if the model is the only source
   allowed).  Nothing waits forever: every request has a timeout.
2. **Persona**: tags drawn per group, then the traits they imply.
3. **Dates**: a join date inside the configured window, a last-seen after it.
4. **Profile**: about-me and location, from the model in batches or from the
   generator, written in the bot's own typing style.
5. **Things**: a balance, items chosen by persona (collectors own hats,
   tycoon fans own the burger shirt, snipers the Longshot), an Unusual roll
   per hat, an outfit worn from what it owns, a hotbar from its weapons.
6. **History**: play statistics in proportion to the account's age.
7. **One transaction** writes the account, ledger, inventory, avatar, bot
   profile and statistics together; a name somebody registered in the
   meantime just skips that one bot.
8. Then the **folder** (account.json), older bots' **friendships**, and the
   bot is handed to the director.
"""
from __future__ import annotations

import json
import random
import threading
import time
import traceback
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from .. import config as site_config
from .. import db
from ..models import catalog
from . import config as bot_config
from . import llm, names, personas, prompts, social, storage

BOT_PASSWORD_HASH = "!bot"      # never verifies: bots cannot be signed in to

SKIN = ["#f5cd30", "#f3cf9b", "#d7c59a", "#cc8e69", "#f0b47b", "#7c503a",
        "#40292a", "#f5cd30", "#f3cf9b", "#cc8e69"]
PALETTE = [e["hex"] for e in catalog.BODY_PALETTE]

_lock = threading.RLock()
_job: Optional[Dict[str, Any]] = None
_history: List[Dict[str, Any]] = []
_reserved: Set[str] = set()
_auto = {"carry": 0.0, "at": 0.0}


def _now() -> int:
    return int(time.time())


# ============================================================== job control
def job_status() -> Dict[str, Any]:
    with _lock:
        job = dict(_job) if _job else None
        if job:
            job["log"] = list(job.get("log", []))[-30:]
        return {"job": job, "history": list(_history[-10:])}


def _log(job: Dict[str, Any], text: str) -> None:
    job.setdefault("log", []).append({"at": _now(), "text": text})
    del job["log"][:-200]


def start_create(count: int, origin: str = "manual") -> Tuple[bool, str]:
    global _job
    count = max(1, min(100000, int(count)))
    with _lock:
        if _job and _job.get("running"):
            return False, "A job is already running."
        _job = {"id": _now(), "kind": "create", "origin": origin, "total": count,
                "done": 0, "failed": 0, "skipped": 0, "running": True,
                "cancel": False, "started": _now(), "log": [],
                "names_llm": 0, "names_generated": 0, "duplicates": 0,
                "profiles_llm": 0}
        job = _job
    threading.Thread(target=_run_create, args=(job,), daemon=True,
                     name="bots-create").start()
    return True, "Creating %d bot%s." % (count, "" if count == 1 else "s")


def start_delete(uids: Optional[Sequence[int]] = None) -> Tuple[bool, str]:
    global _job
    with _lock:
        if _job and _job.get("running"):
            return False, "A job is already running."
        if uids is None:
            uids = [int(r["id"]) for r in db.query("SELECT id FROM users WHERE is_bot=1")]
        else:
            wanted = [int(u) for u in uids]
            uids = []
            for start in range(0, len(wanted), 500):
                chunk = wanted[start:start + 500]
                marks = ",".join("?" * len(chunk))
                uids += [int(r["id"]) for r in db.query(
                    "SELECT id FROM users WHERE is_bot=1 AND id IN (%s)" % marks, chunk)]
        _job = {"id": _now(), "kind": "delete", "total": len(uids), "done": 0,
                "failed": 0, "running": True, "cancel": False, "started": _now(),
                "log": []}
        job = _job
    threading.Thread(target=_run_delete, args=(job, list(uids)), daemon=True,
                     name="bots-delete").start()
    return True, "Deleting %d bot%s." % (len(uids), "" if len(uids) == 1 else "s")


def cancel() -> bool:
    with _lock:
        if _job and _job.get("running"):
            _job["cancel"] = True
            return True
    return False


def _finish(job: Dict[str, Any]) -> None:
    with _lock:
        job["running"] = False
        job["finished"] = _now()
        _history.append({k: job.get(k) for k in (
            "id", "kind", "origin", "total", "done", "failed", "skipped",
            "started", "finished", "names_llm", "names_generated", "duplicates")})
        del _history[:-30]


def _run_create(job: Dict[str, Any]) -> None:
    rng = random.Random()
    try:
        remaining = job["total"]
        batch_size = 40
        while remaining > 0 and not job["cancel"]:
            size = min(batch_size, remaining)
            made = create_batch(size, rng, job)
            job["done"] += len(made)
            remaining -= size
            if not made:
                job["failed"] += size
        _log(job, "finished: %d created" % job["done"])
    except Exception as exc:
        traceback.print_exc()
        _log(job, "stopped: %s" % exc)
    finally:
        _finish(job)


def _run_delete(job: Dict[str, Any], uids: List[int]) -> None:
    from . import director as director_module
    director = director_module.get()
    try:
        names_rows: Dict[int, str] = {}
        for start in range(0, len(uids), 400):
            if job["cancel"]:
                break
            chunk = uids[start:start + 400]
            marks = ",".join("?" * len(chunk))
            for row in db.query("SELECT id, username FROM users WHERE id IN (%s)"
                                % marks, chunk):
                names_rows[int(row["id"])] = row["username"]
            director.remove_bots(chunk)
            with db.transaction() as conn:
                conn.execute("DELETE FROM users WHERE is_bot=1 AND id IN (%s)" % marks,
                             chunk)
            for uid in chunk:
                storage.remove(uid, names_rows.get(uid, ""))
            job["done"] += len(chunk)
        _log(job, "deleted %d bots" % job["done"])
        db.audit(None, "bots.delete", "", {"count": job["done"]})
    except Exception as exc:
        traceback.print_exc()
        _log(job, "stopped: %s" % exc)
    finally:
        try:
            director.reload()
        except Exception:
            traceback.print_exc()
        _finish(job)


def auto_tick(t: float) -> None:
    """Grow the population by itself when auto-creation is switched on."""
    if not bot_config.get("creation.enabled"):
        _auto["carry"] = 0.0
        _auto["at"] = t
        return
    if t - _auto["at"] < 10.0:
        return
    elapsed = t - _auto["at"] if _auto["at"] else 10.0
    _auto["at"] = t
    with _lock:
        if _job and _job.get("running"):
            return
    target = int(bot_config.get("creation.target_population") or 0)
    have = int(db.scalar("SELECT COUNT(*) FROM users WHERE is_bot=1"))
    if have >= target:
        return
    rate = float(bot_config.get("creation.rate_per_minute") or 0)
    _auto["carry"] += rate * min(60.0, elapsed) / 60.0
    count = int(_auto["carry"])
    if count <= 0:
        return
    _auto["carry"] -= count
    start_create(min(count, target - have), origin="auto")


# ================================================================== names
def _taken(candidates: Sequence[str]) -> Set[str]:
    lowers = [c.lower() for c in candidates]
    if not lowers:
        return set()
    marks = ",".join("?" * len(lowers))
    rows = db.query("SELECT username_lower FROM users WHERE username_lower IN (%s)"
                    % marks, lowers)
    return {r["username_lower"] for r in rows}


def _ask_model(messages: List[Dict[str, str]], max_tokens: int,
               timeout: float) -> Optional[str]:
    """One request through the shared queue, waited for (with a timeout)."""
    client = llm.client()
    if not client.available():
        return None
    done = threading.Event()
    result: Dict[str, Any] = {}

    def finished(text, error):
        result["text"], result["error"] = text, error
        done.set()

    if not client.submit("names", llm.P_NAMES,
                         lambda: {"messages": messages, "max_tokens": max_tokens},
                         finished, ttl=timeout):
        return None
    if not done.wait(timeout + 5):
        return None
    return result.get("text")


def reserve_names(count: int, rng: random.Random,
                  job: Optional[Dict[str, Any]] = None) -> List[str]:
    source = bot_config.get("creation.username_source") or "llm_then_procedural"
    got: List[str] = []
    batch_taken: Set[str] = set()
    with _lock:
        batch_taken |= _reserved
    if source in ("llm", "llm_then_procedural") and llm.client().available():
        per = max(1, int(bot_config.get("creation.names_per_request") or 24))
        retries = int(bot_config.get("creation.username_retries") or 0)
        max_tokens = int(bot_config.get("llm.max_tokens_names") or 400)
        timeout = float(bot_config.get("llm.timeout_seconds") or 90)
        examples = {e.lower() for e in bot_config.get("creation.username_examples") or []}
        messages = prompts.names(min(per, max(count, 4)))
        rounds = 0
        while len(got) < count and rounds <= retries:
            rounds += 1
            reply = _ask_model(messages, max_tokens, timeout)
            if reply is None:
                if job:
                    _log(job, "the model did not answer the name request")
                break
            raw = names.parse_model_list(reply)
            cleaned: List[Tuple[str, str]] = []
            broken: List[str] = []
            for item in raw:
                name = names.normalise(item, rng)
                if not names.acceptable(name) or name.lower() in examples:
                    broken.append(str(item)[:30])
                    continue
                cleaned.append((str(item), name))
            in_db = _taken([n for _r, n in cleaned])
            duplicates: List[str] = []
            for original, name in cleaned:
                key = name.lower()
                if key in in_db or key in batch_taken:
                    duplicates.append(name)
                    continue
                batch_taken.add(key)
                got.append(name)
                if len(got) >= count:
                    break
            if job is not None:
                job["duplicates"] = job.get("duplicates", 0) + len(duplicates)
            if len(got) >= count:
                break
            # tell the model what went wrong and ask again, same conversation
            need = count - len(got)
            complaint = []
            if duplicates:
                complaint.append("These names are already taken: %s."
                                 % ", ".join(duplicates[:30]))
            if broken:
                complaint.append("These do not follow the rules: %s."
                                 % ", ".join(broken[:15]))
            if not raw:
                complaint.append("I could not read a JSON array of names in your answer.")
            complaint.append("Give me %d more usernames, all different from every "
                             "name so far. Answer with a JSON array only." % min(per, need))
            messages = messages + [{"role": "assistant", "content": reply[:2000]},
                                   {"role": "user", "content": " ".join(complaint)}]
            if job and (duplicates or broken):
                _log(job, "model repeated %d taken name(s)%s; asked for %d more"
                     % (len(duplicates), " and %d broken" % len(broken) if broken else "",
                        min(per, need)))
        if job is not None:
            job["names_llm"] = job.get("names_llm", 0) + len(got)
    if len(got) < count and source in ("procedural", "llm_then_procedural"):
        want = count - len(got)
        generated: List[str] = []
        guard = 0
        while len(generated) < want and guard < 8:
            guard += 1
            fresh = names.generate_unique(rng, set(batch_taken), (want - len(generated)) * 2)
            in_db = _taken(fresh)
            for name in fresh:
                key = name.lower()
                if key in in_db or key in batch_taken:
                    continue
                batch_taken.add(key)
                generated.append(name)
                if len(generated) >= want:
                    break
        got += generated
        if job is not None:
            job["names_generated"] = job.get("names_generated", 0) + len(generated)
    with _lock:
        _reserved.update(n.lower() for n in got)
    return got


def release_names(taken: Sequence[str]) -> None:
    with _lock:
        for name in taken:
            _reserved.discard(name.lower())


# ============================================================ profile text
OPENERS = {
    "tycoon_fan": ["burger tycoon grinder", "8 plots 8 empires", "golden arches or bust",
                   "my restaurant > yours", "fry station enjoyer"],
    "ctf_main": ["ctf or nothing", "red team forever", "blue team supremacy",
                 "flag runner", "crossroads main"],
    "payload_enjoyer": ["push the cart", "fortress team 2 main", "cart pusher 4 life",
                        "i live on dustworks"],
    "relay_regular": ["blackout relay tunnels are mine", "ironvale regular",
                      "i know every tunnel", "relay main"],
    "collector": ["collecting every hat", "one day i will get an unusual",
                  "hat collector", "ask me about my hats"],
    "fashionista": ["outfit > kd", "fits on point", "drip check"],
    "sniper_main": ["longshot only", "sniper main", "headshots only"],
    "shotgun_rusher": ["shotgun in your face", "close range only"],
    "melee_maniac": ["blockblade gang", "i will bonk you"],
    "rocket_spammer": ["rocket jumping is a lifestyle", "blast launcher spam"],
    "music": ["music + games", "headphones always on", "lofi and ctf"],
    "anime": ["anime pfp energy", "watching one piece rn", "weeb and proud"],
    "sports": ["football on weekends", "go team"],
    "memes": ["professional memer", "no thoughts just vibes", "certified goofball"],
    "builder": ["i build things", "builder at heart"],
    "speedrunner": ["speedrunning everything", "any% burger tycoon"],
    "roleplayer": ["rp enjoyer", "lore first"],
    "streamer_wannabe": ["streaming soon", "future streamer"],
    "retro_gamer": ["old school gamer", "remember when this place was new"],
    "trader": ["trading hats, dm me", "always buying unusuals"],
    "artist": ["i draw stuff", "art + games"],
    "pets": ["my cat walks on my keyboard", "dog person"],
    "sweaty": ["tryhard and proud", "sweat mode on", "gg ez (jk)"],
    "newbie": ["new here!", "still learning lol", "just started"],
    "veteran": ["here since day one", "vet", "been here forever"],
    "chill": ["just vibing", "chill player", "here for fun"],
    "wholesome": ["be nice :)", "gg to everyone", "have a good day"],
    "trash_talker": ["you will lose", "get good", "ez"],
    "social_butterfly": ["add me!!", "friend me", "always down to play"],
    "night_owl": ["up at 3am", "night shift gamer"],
    "early_bird": ["morning gamer", "on before school"],
}
GENERIC = ["hi", "add me", "hello", "just playing", "gg", "i like this game",
           "dont message me for trades lol", "busy", "", "", "", ":)",
           "follow me", "hmm", "idk what to put here", "yes"]


def style_text(text: str, traits: Dict[str, float], rng: random.Random) -> str:
    """Rewrite a line in a persona's typing habits."""
    if not text:
        return text
    if traits.get("grammar", 0) > 0.55:
        text = text[:1].upper() + text[1:]
        if text[-1:] not in ".!?:)":
            text += "."
    elif traits.get("lower", 0) > 0.5:
        text = text.lower()
    if traits.get("caps", 0) > 0.4 and rng.random() < 0.5:
        text = text.upper()
    if traits.get("emoji", 0) > 0.4:
        text += " " + rng.choice([":D", "xD", ":P", "<3", ":)", "^_^", ";)"])
    return text[:180]


def procedural_profile(card: Dict[str, Any], rng: random.Random) -> Tuple[str, str]:
    tags = card["tags"]
    traits = card["traits"]
    quiet = traits.get("chatty", 0.4) < 0.25 or "loner" in tags or "shy" in tags
    if quiet and rng.random() < 0.5:
        blurb = ""
    else:
        pool: List[str] = []
        for tag in tags:
            pool += OPENERS.get(tag, [])
        parts = []
        if pool:
            parts.append(rng.choice(pool))
            if rng.random() < 0.4 and len(pool) > 1:
                second = rng.choice(pool)
                if second not in parts:
                    parts.append(second)
        if not parts or rng.random() < 0.25:
            generic = rng.choice(GENERIC)
            if generic:
                parts.append(generic)
        if "kid" in tags and rng.random() < 0.3:
            parts.append(str(rng.randint(10, 13)) + (" yrs" if rng.random() < 0.5 else ""))
        elif "teen" in tags and rng.random() < 0.25:
            parts.append(str(rng.randint(13, 18)))
        joiner = rng.choice([" | ", ". ", " - ", " / ", ", "])
        blurb = style_text(joiner.join(parts), traits, rng)
    locations = bot_config.get("creation.locations") or bot_config.DEFAULT_LOCATIONS
    location = rng.choice(locations) if locations else ""
    return blurb, location


def llm_profiles(cards: List[Dict[str, Any]], job: Optional[Dict[str, Any]]) -> Dict[str, Tuple[str, str]]:
    """About-me lines for a batch of bots from the model, keyed by name."""
    if not cards or not llm.client().available():
        return {}
    spec = prompts.profiles(cards)
    done = threading.Event()
    result: Dict[str, Any] = {}

    def finished(text, error):
        result["text"] = text
        done.set()

    timeout = float(bot_config.get("llm.timeout_seconds") or 90)
    if not llm.client().submit("profile", llm.P_PROFILE, lambda: spec, finished,
                               ttl=timeout):
        return {}
    if not done.wait(timeout + 5):
        return {}
    text = result.get("text") or ""
    start, end = text.find("["), text.rfind("]")
    out: Dict[str, Tuple[str, str]] = {}
    if start < 0 or end <= start:
        return out
    try:
        rows = json.loads(text[start:end + 1])
    except ValueError:
        return out
    if not isinstance(rows, list):
        return out
    by_order = [c["name"] for c in cards]
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        name = str(row.get("name") or (by_order[index] if index < len(by_order) else ""))
        about = prompts.tidy(str(row.get("about") or ""), "post", name) or ""
        location = str(row.get("location") or "")[:40]
        if name:
            out[name.lower()] = (about[:180], location)
    if job is not None:
        job["profiles_llm"] = job.get("profiles_llm", 0) + len(out)
    return out


# ============================================================== the things
def _choose_items(traits: Dict[str, float], tags: Sequence[str],
                  rng: random.Random) -> List[str]:
    lo, hi = bot_config.get("creation.items_owned") or [3, 16]
    appetite = 0.35 + traits.get("collector", 0.3) * 0.9 + traits.get("fashion", 0.4) * 0.4
    if "newbie" in tags:
        appetite *= 0.45
    if "veteran" in tags:
        appetite *= 1.3
    count = int(round(float(lo) + (float(hi) - float(lo)) * min(1.0, appetite * rng.uniform(0.45, 1.0))))
    wanted: List[str] = []

    def pick(slot: str, bias=None):
        pool = [it for it in catalog.by_slot(slot) if it["price"] > 0 and it["id"] not in wanted]
        if not pool:
            return
        weights = []
        for it in pool:
            w = 1.0 / (1.0 + it["price"] / 700.0)
            if it.get("rarity") in ("rare", "legendary"):
                w *= 0.5 + traits.get("collector", 0.3)
            if bias and it["id"] in bias:
                w *= 6.0
            weights.append(w)
        wanted.append(rng.choices(pool, weights)[0]["id"])

    # what this persona would go for first
    if "tycoon_fan" in tags or "builder" in tags:
        wanted += [i for i in ("shirt_burger", "use_buildhammer") if rng.random() < 0.6]
    weapon_pref = [("use_sniper", "wp_sniper"), ("use_smg", "wp_smg"),
                   ("use_rifle", "wp_rifle"), ("use_sword", "wp_melee"),
                   ("use_rocket", "wp_rocket")]
    for item_id, key in weapon_pref:
        if traits.get(key, 0) > 0.8 or rng.random() < traits.get(key, 0) * 0.35:
            wanted.append(item_id)
    if traits.get("support", 0) > 0.4 and rng.random() < 0.7:
        wanted.append("use_medkit")
    order = ["hair", "shirt", "pants", "hat", "face", "hat", "belt", "back", "hat",
             "shirt", "pants", "hat", "face", "hair", "hat", "back", "hat", "belt"]
    if traits.get("collector", 0) > 0.55:
        order = ["hat", "hat", "hair", "shirt", "hat", "pants", "hat", "face",
                 "hat", "back", "hat", "belt", "hat", "hat"] + order
    for slot in order:
        if len(wanted) >= count:
            break
        if slot == "hair" and rng.random() < 0.15:
            continue
        pick(slot)
    return list(dict.fromkeys(wanted))[:max(count, 0) + 2]


def _colors(traits: Dict[str, float], rng: random.Random) -> Dict[str, str]:
    skin = rng.choice(SKIN)
    torso = rng.choice(PALETTE)
    legs = rng.choice(PALETTE)
    if traits.get("fashion", 0.4) > 0.55:
        # a coordinated look: neighbouring palette colours
        index = PALETTE.index(torso)
        legs = PALETTE[(index + rng.choice((-2, -1, 1, 2))) % len(PALETTE)]
    elif rng.random() < 0.18:
        legs = torso
    return {"head": skin, "left_arm": skin, "right_arm": skin, "torso": torso,
            "hips": legs, "left_leg": legs, "right_leg": legs}


def _history(joined: int, traits: Dict[str, float], rng: random.Random,
             now: int) -> Dict[str, Dict[str, int]]:
    days = max(0.0, (now - joined) / 86400.0)
    minutes = days * rng.uniform(4, 34) * (0.3 + traits.get("gamer", 0.6))
    minutes = min(minutes, 60 * 24 * 365 * 0.25)
    worlds = bot_config.WORLD_IDS
    prefs = [max(0.05, traits.get("w_" + w, 1.0)) for w in worlds]
    total = sum(prefs)
    skill = traits.get("skill", 0.5)
    out = {}
    for world, pref in zip(worlds, prefs):
        share = minutes * pref / total * rng.uniform(0.6, 1.3)
        if share < 1:
            continue
        rate = 0.08 if world == "burger_tycoon" else 0.95
        kills = int(share * rate * (0.35 + skill * 1.3))
        deaths = int(share * rate * (1.45 - skill * 0.9))
        rounds = int(share / (9 if world != "blackout_relay" else 24))
        out[world] = {"kills": kills, "deaths": deaths, "rounds": rounds,
                      "wins": int(rounds * (0.3 + skill * 0.35)),
                      "playtime": int(share * 60),
                      "score": int(kills * 10 + share * (6 + traits.get("objective", 0.6) * 12)),
                      "visits": max(1, int(share / rng.uniform(12, 45)))}
    return out


# ================================================================ creation
def create_batch(count: int, rng: random.Random,
                 job: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    now = _now()
    reserved = reserve_names(count, rng, job)
    if not reserved:
        if job:
            _log(job, "no usable names -- nothing created in this batch")
        return []
    try:
        cards = _design(reserved, rng, now, job)
        created = _write(cards, now)
    finally:
        release_names(reserved)
    if not created:
        return []
    _after(created, rng, now)
    if job:
        _log(job, "created %d: %s%s" % (len(created),
                                        ", ".join(c["name"] for c in created[:6]),
                                        "..." if len(created) > 6 else ""))
    return created


def _design(reserved: List[str], rng: random.Random, now: int,
            job: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    weights = bot_config.get("personas.tag_weights") or {}
    t_lo, t_hi = bot_config.get("creation.tags_per_bot") or [6, 9]
    d_from, d_to = bot_config.get("creation.join_date") or ["2022-01-01", ""]
    start = bot_config.date_to_ts(d_from)
    end = min(now, bot_config.date_to_ts(d_to, end=True))
    if end <= start:
        start = end - 86400
    female = float(bot_config.get("creation.female_share") or 45) / 100.0
    public = float(bot_config.get("creation.public_server_share") or 40) / 100.0
    c_lo, c_hi = bot_config.get("creation.credits") or [150, 14000]
    unusual = float(bot_config.get("creation.unusual_chance") or 0)
    cards = []
    for name in reserved:
        tags = personas.draw_tags(rng, rng.randint(int(t_lo), int(t_hi)), weights)
        traits = personas.derive_traits(tags, rng)
        # new accounts are more common than old ones
        joined = int(start + (end - start) * (rng.random() ** 0.8))
        recency = rng.random() ** 2.2
        last_seen = int(max(joined, now - (now - joined) * recency * 0.3))
        wealth = traits.get("wealth", 0.5)
        credits = int(float(c_lo) + (float(c_hi) - float(c_lo)) * min(1.0, rng.random() ** 1.6 * (0.5 + wealth)))
        cards.append({
            "name": name, "tags": tags, "traits": traits, "joined": joined,
            "last_seen": last_seen, "credits": credits,
            "body": "female" if rng.random() < female else "male",
            "colors": _colors(traits, rng),
            "items": _choose_items(traits, tags, rng),
            "unusual": unusual,
            "privacy": {"server": "public"} if rng.random() < public else {},
            "theme": rng.choice(["auto", "auto", "dark", "light"]),
            "history": _history(joined, traits, rng, now)
            if bot_config.get("creation.seed_stats") else {},
        })
    source = bot_config.get("creation.profile_source") or "llm_then_procedural"
    texts: Dict[str, Tuple[str, str]] = {}
    if source in ("llm", "llm_then_procedural"):
        for start_at in range(0, len(cards), 12):
            texts.update(llm_profiles(cards[start_at:start_at + 12], job))
    for card in cards:
        text = texts.get(card["name"].lower())
        if text is None and source in ("procedural", "llm_then_procedural"):
            text = procedural_profile(card, rng)
        card["blurb"], card["location"] = text or ("", "")
        card["generator"] = "llm" if card["name"].lower() in texts else "procedural"
    return cards


def _write(cards: List[Dict[str, Any]], now: int) -> List[Dict[str, Any]]:
    rng = random.Random()
    starting = int(site_config.STARTING_CREDITS)
    created: List[Dict[str, Any]] = []
    with db.transaction() as conn:
        serial: Dict[str, int] = {}

        def next_serial(item_id: str) -> int:
            if item_id not in serial:
                serial[item_id] = int(conn.execute(
                    "SELECT COALESCE(MAX(serial),0) FROM inventory WHERE item_id=?",
                    (item_id,)).fetchone()[0])
            serial[item_id] += 1
            return serial[item_id]

        visits_per_world: Dict[str, int] = {}
        for card in cards:
            owned = [it for it in (catalog.get(i) for i in card["items"]) if it]
            spent = sum(int(it["price"]) for it in owned)
            opening = card["credits"] + spent
            place_visits = sum(h["visits"] for h in card["history"].values())
            cur = conn.execute(
                "INSERT OR IGNORE INTO users(username, username_lower, password_hash,"
                " created_at, last_seen, last_login, credits, is_admin, blurb,"
                " location, place_visits, theme, privacy, pinned, prefs, controls,"
                " is_bot) VALUES(?,?,?,?,?,?,?,0,?,?,?,?,?,'[]','{}','{}',1)",
                (card["name"], card["name"].lower(), BOT_PASSWORD_HASH,
                 card["joined"], card["last_seen"], card["last_seen"],
                 card["credits"], card["blurb"], card["location"], place_visits,
                 card["theme"], json.dumps(card["privacy"])))
            if not cur.rowcount:
                continue          # somebody registered that name meanwhile
            uid = int(cur.lastrowid)
            card["id"] = uid
            # ledger: the opening grant, then what it bought
            balance = opening
            ledger = [(uid, opening, balance, "Welcome bonus", card["joined"])]
            when = card["joined"]
            shown = owned[:4]
            for it in shown:
                when = min(now, when + rng.randint(600, 86400 * 20))
                balance -= int(it["price"])
                ledger.append((uid, -int(it["price"]), balance, "Bought %s" % it["name"], when))
            rest = owned[4:]
            if rest:
                when = min(now, when + rng.randint(600, 86400 * 40))
                total = sum(int(it["price"]) for it in rest)
                balance -= total
                ledger.append((uid, -total, balance, "Bought %d items" % len(rest), when))
            conn.executemany(
                "INSERT INTO credit_ledger(user_id,delta,balance_after,reason,"
                "actor_id,created_at) VALUES(?,?,?,?,NULL,?)", ledger)
            # inventory: the starter kit every account gets, then purchases
            rows: Dict[str, List[Tuple[int, str]]] = {}
            for item_id in catalog.STARTER_ITEMS:
                inv = conn.execute(
                    "INSERT INTO inventory(user_id,item_id,tier,effect,serial,"
                    "acquired_at,source) VALUES(?,?,'normal','',?,?,'starter')",
                    (uid, item_id, next_serial(item_id), card["joined"]))
                rows.setdefault(item_id, []).append((int(inv.lastrowid), "normal"))
            for it in owned:
                tier, effect = "normal", ""
                if it["slot"] == "hat" and rng.random() < card["unusual"]:
                    tier, effect = "unusual", rng.choice(catalog.EFFECT_IDS)
                inv = conn.execute(
                    "INSERT INTO inventory(user_id,item_id,tier,effect,serial,"
                    "acquired_at,source) VALUES(?,?,?,?,?,?,'market')",
                    (uid, it["id"], tier, effect, next_serial(it["id"]),
                     min(now, card["joined"] + rng.randint(600, 86400 * 60))))
                rows.setdefault(it["id"], []).append((int(inv.lastrowid), tier))
            equipped, hotbar, pinned = _outfit(card, rows, rng)
            conn.execute(
                "INSERT INTO avatars(user_id,colors,equipped,hotbar,body_type,updated_at)"
                " VALUES(?,?,?,?,?,?)",
                (uid, json.dumps(card["colors"]), json.dumps(equipped),
                 json.dumps(hotbar), card["body"], card["last_seen"]))
            if pinned:
                conn.execute("UPDATE users SET pinned=? WHERE id=?",
                             (json.dumps(pinned), uid))
            conn.execute(
                "INSERT INTO bot_profiles(user_id,tags,traits,voice,generator,created_at)"
                " VALUES(?,?,?,?,?,?)",
                (uid, ",".join(card["tags"]), personas.pack_traits(card["traits"]),
                 "", card["generator"], now))
            for world, h in card["history"].items():
                conn.execute(
                    "INSERT INTO game_stats(user_id,world_id,kills,deaths,wins,rounds,"
                    "playtime,score) VALUES(?,?,?,?,?,?,?,?)",
                    (uid, world, h["kills"], h["deaths"], h["wins"], h["rounds"],
                     h["playtime"], h["score"]))
                visits_per_world[world] = visits_per_world.get(world, 0) + h["visits"]
            created.append(card)
        for world, count in visits_per_world.items():
            conn.execute("UPDATE world_stats SET visits=visits+? WHERE world_id=?",
                         (count, world))
    return created


def _outfit(card: Dict[str, Any], rows: Dict[str, List[Tuple[int, str]]],
            rng: random.Random) -> Tuple[Dict[str, int], List[int], List[int]]:
    equipped: Dict[str, int] = {}
    by_slot: Dict[str, List[Tuple[int, str, str]]] = {}
    for item_id, copies in rows.items():
        item = catalog.get(item_id)
        if not item:
            continue
        for inv_id, tier in copies:
            by_slot.setdefault(item["slot"], []).append((inv_id, tier, item_id))
    for slot in catalog.SLOTS:
        options = by_slot.get(slot) or []
        if not options:
            continue
        unusual = [o for o in options if o[1] == "unusual"]
        paid = [o for o in options if catalog.get(o[2])["price"] > 0]
        if slot == "hat" and rng.random() < 0.18 and not unusual:
            continue        # some people just do not wear a hat
        choice = (unusual or paid or options)
        equipped[slot] = rng.choice(choice)[0]
    # the hotbar: the free three, then whatever weapons it bought
    hotbar = [0] * catalog.HOTBAR_SIZE
    for index, item_id in enumerate(catalog.DEFAULT_HOTBAR):
        if item_id and item_id in rows:
            hotbar[index] = rows[item_id][0][0]
    bought = [c for c in by_slot.get("usable", []) if c[2] not in catalog.DEFAULT_HOTBAR]
    rng.shuffle(bought)
    slots = [3, 4, 2, 1]
    for (inv_id, _tier, item_id), slot in zip(bought, slots):
        hotbar[slot] = inv_id
    pinned: List[int] = []
    showable = [o for o in by_slot.get("hat", []) if o[1] == "unusual"] + \
        [o for s in ("hat", "back", "usable", "shirt") for o in by_slot.get(s, [])
         if catalog.get(o[2])["price"] >= 600]
    if showable and rng.random() < 0.55:
        pinned = [o[0] for o in showable[:rng.randint(1, 3)]]
    return equipped, hotbar, list(dict.fromkeys(pinned))


def _after(created: List[Dict[str, Any]], rng: random.Random, now: int) -> None:
    from . import director as director_module
    director = director_module.get()
    for card in created:
        storage.write_account(card["id"], card["name"], {
            "id": card["id"], "username": card["name"], "is_bot": True,
            "tags": card["tags"], "tag_labels": personas.labels(card["tags"]),
            "persona": personas.describe(card["tags"]),
            "traits": card["traits"], "joined": card["joined"],
            "blurb": card["blurb"], "location": card["location"],
            "body_type": card["body"], "colors": card["colors"],
            "items": card["items"], "starting_credits": card["credits"],
            "profile_text_from": card["generator"], "created_at": now,
        })
    director.add_bots([{"id": c["id"], "tags": ",".join(c["tags"]),
                        "traits": personas.pack_traits(c["traits"]),
                        "last_seen": c["last_seen"]} for c in created])
    if bot_config.get("creation.seed_friendships"):
        _seed_friends(director, created, rng, now)
    db.audit(None, "bots.create", "", {"count": len(created),
                                       "names": [c["name"] for c in created[:20]]})
    from .. import console
    console.note("%d bot%s created" % (len(created), "" if len(created) == 1 else "s"))


def _seed_friends(director, created: List[Dict[str, Any]], rng: random.Random,
                  now: int) -> None:
    """Older accounts arrive with the friends they would already have."""
    depth = int(bot_config.get("friends.depth") or 0)
    pairs = []
    keys: Set[Tuple[int, int]] = set()
    for card in created:
        i = director.index_of(card["id"])
        if i < 0:
            continue
        age_days = (now - card["joined"]) / 86400.0
        target = director.friend_target[i] * min(1.0, age_days / 240.0) * rng.uniform(0.3, 0.9)
        wanted = int(target)
        seen: Set[int] = set()
        guard = 0
        engine = director.chatter
        while len(seen) < wanted and guard < wanted * 6 + 10:
            guard += 1
            if engine is not None:
                j = engine.candidate(i, depth, tries=10)
            else:
                j = rng.randrange(director.n) if director.n else -1
                if j >= 0 and personas.shared(director.masks[i], director.masks[j]) < depth:
                    j = -1
            if j < 0 or j == i or j in seen:
                continue
            if director.friends[j] >= director.friend_target[j]:
                continue
            seen.add(j)
            other = int(director.uids[j])
            key = (min(card["id"], other), max(card["id"], other))
            if key in keys:
                continue
            keys.add(key)
            when = int(card["joined"] + rng.random() * max(60, now - card["joined"]))
            pairs.append((card["id"], other, min(now, when)))
    if pairs:
        social.seed_friendships(pairs)
        with director.lock:
            for a, b, _w in pairs:
                for uid in (a, b):
                    k = director.index_of(uid)
                    if k >= 0:
                        director.friends[k] = min(65000, director.friends[k] + 1)


def population() -> int:
    return int(db.scalar("SELECT COUNT(*) FROM users WHERE is_bot=1"))
