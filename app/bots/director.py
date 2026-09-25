"""The bot director: who is online, where they are, and what happens next.

It runs in the web server process, on one thread, and it is built to carry a
couple of hundred thousand bots on a Raspberry Pi 3 without anybody noticing
it is there.  Three ideas make that possible.

**Struct-of-arrays.**  A bot at runtime is not an object; it is one slot in a
dozen flat arrays (``bytearray`` for states, ``array('I')`` for times,
``array('f')`` for traits).  Two hundred thousand bots are a few megabytes, and
looking one up by account id is a binary search over a sorted id array rather
than a dictionary of two hundred thousand boxed integers.

**Nothing is polled.**  Every bot has exactly one "next thing that happens to
me" time, filed in a timing wheel keyed by the second.  Each pass of the loop
takes the buckets that have come due and nothing else, so the cost is the
number of *events* per second -- a few dozen even at full scale -- and not
the number of bots.  A bot asleep for thirty hours costs nothing for thirty
hours.

**Totals are steered, individuals are free.**  Each bot keeps its own
timeline -- sessions, breaks, offline stints drawn from its own ranges and
its persona's hours -- and a controller every few seconds compares the
population online (and in worlds) with the configured daily curve and nudges
the gap: waking the bots whose personal hours suit the moment, or sending
home the ones whose do not.  The curve is met exactly without anyone
behaving like a clock.

Bots in worlds are counted into the world browser, profiles and the terminal
exactly as players are.  An instance holding only bots is a
:class:`~app.bots.dormant.Dormant` -- numbers advanced in closed form -- and
only becomes a real simulation on a game host when a person joins it
("hydration"), going back to sleep when the last person leaves.
"""
from __future__ import annotations

import base64
import bisect
import json
import math
import os
import random
import threading
import time
import traceback
from array import array
from collections import deque
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from .. import db
from ..models import worlds as world_registry
from . import config as bot_config
from . import dormant as dormant_model
from . import personas, social, storage

OFFLINE, WAKING, IDLE, PLAYING = 0, 1, 2, 3
STATE_NAMES = {OFFLINE: "offline", WAKING: "online (settling in)",
               IDLE: "online", PLAYING: "in a world"}
NO_WORLD = 255
SNAPSHOT = storage.ROOT / "state.json"
SNAPSHOT_MAX_AGE = 20 * 60

WORLD_IDS: List[str] = [w["id"] for w in world_registry.WORLDS]
WORLD_INDEX = {wid: i for i, wid in enumerate(WORLD_IDS)}

# per-bot traits the director itself reads, as float arrays
TRAIT_ARRAYS = ("activity", "night", "weekend", "session", "gamer", "social",
                "selective", "skill", "objective", "chatty", "kindness")


def _now() -> int:
    return int(time.time())


def _between(rng: random.Random, pair, scale: float = 1.0) -> float:
    lo, hi = float(pair[0]), float(pair[1])
    if hi < lo:
        lo, hi = hi, lo
    return rng.uniform(lo, hi) * scale


class Director:
    def __init__(self):
        self.lock = threading.RLock()
        self.rng = random.Random()
        self.loaded = False
        self.started = 0.0
        self._reset_arrays()
        self.dormant: Dict[str, Dict[int, dormant_model.Dormant]] = {w: {} for w in WORLD_IDS}
        self.hosted: Dict[str, Dict[int, Dict[str, Any]]] = {w: {} for w in WORLD_IDS}
        self.hosted_at: Dict[str, float] = {w: 0.0 for w in WORLD_IDS}
        self.next_inst: Dict[str, int] = {w: 2 for w in WORLD_IDS}
        # sleeping instances with room, so a bot joining a world samples a few
        # instead of scanning thousands (entries go stale and are dropped
        # lazily; the whole index is rebuilt every minute)
        self.open: Dict[str, List[int]] = {w: [] for w in WORLD_IDS}
        self.open_set: Dict[str, Set[int]] = {w: set() for w in WORLD_IDS}
        self._open_at = 0.0
        self._free_hint: Dict[str, int] = {w: 1 for w in WORLD_IDS}
        self.ops: Dict[str, List[Dict[str, Any]]] = {w: [] for w in WORLD_IDS}
        self.expect: Dict[int, Tuple[str, int, float]] = {}   # uid -> (world, inst, deadline)
        # bots the director has placed in live (hosted) rounds: world -> uid -> inst
        self.live: Dict[str, Dict[int, int]] = {w: {} for w in WORLD_IDS}
        self.summaries: Dict[str, Dict[str, Any]] = {}
        self.recent_online: deque = deque(maxlen=600)
        self.session_rows: List[Dict[str, Any]] = []
        self.seen_rows: List[Tuple[int, int]] = []
        self.events: deque = deque(maxlen=200)
        self.history: deque = deque(maxlen=24 * 60)           # one sample a minute
        self.counters = {"woke": 0, "slept": 0, "joined": 0, "left": 0,
                         "hydrated": 0, "slept_instances": 0}
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._last = {"ctrl": 0.0, "dorm": 0.0, "flush": 0.0, "snap": 0.0,
                      "hist": 0.0, "prune": 0.0, "social": 0.0}
        self._dorm_cursor = 0
        self._curve_cache: Dict[Tuple[int, int, int], float] = {}
        self._hosts_up: Set[str] = set()
        self._hosts_checked = 0.0
        self._flat: List[Tuple[str, dormant_model.Dormant]] = []
        self._flat_at = 0.0
        self._listing_at = 0.0
        self._count_at = 0.0
        self.chatter = None          # set by start(): chatter.Engine
        self.gamechat = None         # set by start(): gamechat.Relay
        self.version = 0

    def _reset_arrays(self) -> None:
        self.n = 0
        self.uids = array("I")
        self.state = bytearray()
        self.world = bytearray()
        self.inst = array("I")
        self.next_at = array("I")
        self.since = array("I")
        self.ready_at = array("I")
        self.session_end = array("I")
        self.friends = array("H")
        self.friend_target = array("H")
        self.masks: List[int] = []
        self.traits: Dict[str, array] = {k: array("f") for k in TRAIT_ARRAYS}
        self.wpref: List[array] = [array("f") for _ in WORLD_IDS]
        self.tag_index: Dict[int, array] = {}
        self.wheel: Dict[int, array] = {}
        self.wheel_floor = _now()
        self.online = 0
        self.playing = 0

    # ================================================================ lookup
    def index_of(self, uid: int) -> int:
        """Bot slot for an account id, or -1 when it is not a bot."""
        uids = self.uids
        i = bisect.bisect_left(uids, uid)
        if i < len(uids) and uids[i] == uid:
            return i
        return -1

    def is_bot(self, uid: int) -> bool:
        return self.index_of(int(uid or 0)) >= 0

    def bot_online(self, uid: int) -> bool:
        i = self.index_of(int(uid or 0))
        return i >= 0 and self.state[i] != OFFLINE

    def bot_ready(self, uid: int) -> bool:
        i = self.index_of(int(uid or 0))
        return i >= 0 and self.state[i] in (IDLE, PLAYING)

    def bot_world(self, uid: int) -> Optional[str]:
        i = self.index_of(int(uid or 0))
        if i < 0 or self.state[i] != PLAYING or self.world[i] == NO_WORLD:
            return None
        return WORLD_IDS[self.world[i]]

    def bot_place(self, uid: int) -> Tuple[Optional[str], int]:
        i = self.index_of(int(uid or 0))
        if i < 0 or self.state[i] != PLAYING or self.world[i] == NO_WORLD:
            return None, 0
        return WORLD_IDS[self.world[i]], int(self.inst[i])

    def enabled(self) -> bool:
        return bool(bot_config.get("system.enabled"))

    # ================================================================ wheel
    def _schedule(self, i: int, when: int) -> None:
        # never behind the wheel's hand: a slot it has passed is never read
        when = max(int(when), self.wheel_floor)
        self.next_at[i] = when
        bucket = self.wheel.get(when)
        if bucket is None:
            # 4 bytes a bot rather than a list of int objects
            bucket = self.wheel[when] = array("I")
        bucket.append(i)

    def _due(self, now: int, budget: int) -> List[int]:
        out: List[int] = []
        floor = self.wheel_floor
        while floor <= now and len(out) < budget:
            bucket = self.wheel.pop(floor, None)
            if bucket:
                for i in bucket:
                    if i < self.n and self.next_at[i] == floor:
                        out.append(i)
                if len(out) >= budget:
                    floor += 1
                    break
            floor += 1
        self.wheel_floor = floor
        return out

    # ================================================================ load
    def load(self) -> None:
        """Read every bot out of the database into the arrays.

        The rows are parsed column by column outside the lock -- a hundred
        thousand bots take a couple of seconds to parse, and heartbeats and
        page requests that ask the director something must not wait on it.
        """
        started = time.time()
        counts = social.friend_counts()
        now = _now()
        # streamed straight off the cursor: the rows are never all in memory
        rows = db.connect().execute(
            "SELECT u.id, u.last_seen, b.tags, b.traits"
            " FROM users u JOIN bot_profiles b ON b.user_id=u.id"
            " WHERE u.is_bot=1 ORDER BY u.id")
        columns = self._columns(rows, counts, now)
        with self.lock:
            self._reset_arrays()
            self._install(columns)
            self.loaded = True
            restored = self._restore_snapshot(now)
            if not restored:
                self._warm_start(now)
            self._rebuild_open()
        self._note("loaded %d bots in %.1fs%s" % (self.n, time.time() - started,
                                                  " (restored)" if self.n and restored else ""))

    def _columns(self, rows: Iterable[Any], counts: Dict[int, int], now: int) -> Dict[str, Any]:
        """Parse database rows into ready-made arrays (no lock held)."""
        order = {key: k for k, key in enumerate(personas.PACK_ORDER)}
        base = personas.TRAIT_BASE
        trait_keys = list(TRAIT_ARRAYS)
        world_keys = ["w_" + wid for wid in WORLD_IDS]
        picks = [(key, order.get(key), float(base.get(key, 0.5))) for key in trait_keys]
        wpicks = [(order.get(key), 1.0) for key in world_keys]
        # typed arrays from the start: no per-bot float or int objects
        traits: Dict[str, array] = {k: array("f") for k in trait_keys}
        wpref: List[array] = [array("f") for _ in WORLD_IDS]
        uids = array("I")
        since = array("I")
        friends = array("H")
        targets = array("H")
        masks: List[int] = []
        index: Dict[int, array] = {}
        bits = personas.tag_bits()
        lo, hi = bot_config.get("friends.max_friends") or [3, 45]
        lo, hi = float(lo), float(hi)
        last = -1
        for row in rows:
            uid = int(row[0])
            if uid <= last:
                continue
            last = uid
            i = len(uids)
            uids.append(uid)
            seen = int(row[1] or 0)
            since.append(max(0, min(now, seen or now)))
            friends.append(min(65000, counts.get(uid, 0)))
            mask = 0
            for tag in (row[2] or "").split(","):
                bit = bits.get(tag)
                if bit is not None and not mask >> bit & 1:
                    mask |= 1 << bit
                    ids = index.get(bit)
                    if ids is None:
                        ids = index[bit] = array("I")
                    ids.append(i)
            masks.append(mask)
            text = row[3] or ""
            if text.startswith("t1|"):
                raw = text[3:].split(",")
                size = len(raw)
                for key, k, default in picks:
                    value = default
                    if k is not None and k < size:
                        try:
                            value = float(raw[k])
                        except ValueError:
                            pass
                    traits[key].append(value)
                for w, (k, default) in enumerate(wpicks):
                    value = default
                    if k is not None and k < size:
                        try:
                            value = float(raw[k])
                        except ValueError:
                            pass
                    wpref[w].append(value)
            else:
                full = personas.unpack_traits(text)
                for key, _, default in picks:
                    traits[key].append(float(full.get(key, default)))
                for w, key in enumerate(world_keys):
                    wpref[w].append(float(full.get(key, 1.0)))
            social_trait = max(0.0, min(1.0, traits["social"][-1]))
            target = lo + (hi - lo) * social_trait ** 1.3
            # a fixed wobble per bot, so the target is the same after every restart
            wobble = 0.8 + 0.4 * ((uid * 2654435761) % 1000) / 999.0
            targets.append(int(max(0, min(200, round(target * wobble)))))
        n = len(uids)
        return {
            "n": n, "uids": uids, "since": since,
            "friends": friends, "friend_target": targets,
            "masks": masks, "traits": traits, "wpref": wpref, "tag_index": index,
        }

    def _install(self, c: Dict[str, Any]) -> None:
        n = c["n"]
        self.n = n
        self.uids = c["uids"]
        self.state = bytearray(n)                      # OFFLINE == 0
        self.world = bytearray([NO_WORLD]) * n
        self.inst = array("I", bytes(4 * n))
        self.next_at = array("I", bytes(4 * n))
        self.since = c["since"]
        self.ready_at = array("I", bytes(4 * n))
        self.session_end = array("I", bytes(4 * n))
        self.friends = c["friends"]
        self.friend_target = c["friend_target"]
        self.masks = c["masks"]
        self.traits = c["traits"]
        self.wpref = c["wpref"]
        self.tag_index = c["tag_index"]

    def _append(self, uid: int, tags_text: str, traits_text: str,
                last_seen: int, friend_count: int, now: int,
                schedule: bool = True) -> int:
        tags = personas.parse_tags(tags_text)
        traits = personas.unpack_traits(traits_text)
        i = self.n
        if self.uids and uid <= self.uids[-1]:
            # ids arrive in order from the database; one that does not means
            # a rebuild is cheaper than an insert into every array
            raise ValueError("bot ids must be appended in order")
        self.n += 1
        self.uids.append(uid)
        self.state.append(OFFLINE)
        self.world.append(NO_WORLD)
        self.inst.append(0)
        self.next_at.append(0)
        self.since.append(max(0, min(now, last_seen or now)))
        self.ready_at.append(0)
        self.session_end.append(0)
        self.friends.append(min(65000, friend_count))
        mask = personas.mask_of(tags)
        self.masks.append(mask)
        for key in TRAIT_ARRAYS:
            self.traits[key].append(float(traits.get(key, personas.TRAIT_BASE.get(key, 0.5))))
        for w, wid in enumerate(WORLD_IDS):
            self.wpref[w].append(float(traits.get("w_" + wid, 1.0)))
        lo, hi = bot_config.get("friends.max_friends") or [3, 45]
        social_trait = float(traits.get("social", 0.5))
        target = lo + (hi - lo) * max(0.0, min(1.0, social_trait ** 1.3))
        # a fixed wobble per bot, so the target is the same after every restart
        wobble = 0.8 + 0.4 * ((uid * 2654435761) % 1000) / 999.0
        self.friend_target.append(int(max(0, min(200, round(target * wobble)))))
        bit = 0
        while mask:
            if mask & 1:
                self.tag_index.setdefault(bit, array("I")).append(i)
            mask >>= 1
            bit += 1
        if schedule:
            self._plan_offline(i, now, fresh=True)
        return i

    def add_bots(self, rows: List[Dict[str, Any]]) -> None:
        """Register freshly created bots (called by the factory)."""
        now = _now()
        with self.lock:
            for row in rows:
                try:
                    i = self._append(int(row["id"]), row["tags"], row["traits"],
                                     int(row.get("last_seen") or now), 0, now)
                except ValueError:
                    self._rebuild_later = True
                    continue
                # a brand new bot can come straight online if the curve wants it
                if self.rng.random() < self.curve(now) * 0.5:
                    self._schedule(i, now + self.rng.randint(5, 600))
            self.version += 1

    def remove_bots(self, uids: Iterable[int]) -> None:
        """Pull bots out of play before their accounts are deleted."""
        with self.lock:
            for uid in uids:
                i = self.index_of(int(uid))
                if i < 0:
                    continue
                if self.state[i] == PLAYING:
                    self._leave_world(i, _now(), "left the server")
                if self.state[i] != OFFLINE:
                    self.online -= 1
                self.state[i] = OFFLINE
                self.next_at[i] = 0
            self.version += 1

    def reload(self) -> None:
        """Rebuild from the database (after a mass deletion, say)."""
        self.save_snapshot()
        self.load()

    # ============================================================== curve
    def _clock(self, t: float) -> Tuple[float, int]:
        offset = bot_config.get("presence.utc_offset")
        if offset is None:
            local = time.localtime(t)
            seconds = local.tm_hour * 3600 + local.tm_min * 60 + local.tm_sec
            return seconds / 3600.0, local.tm_wday
        shifted = t + float(offset) * 3600.0
        gm = time.gmtime(shifted)
        return (gm.tm_hour * 3600 + gm.tm_min * 60 + gm.tm_sec) / 3600.0, gm.tm_wday

    def curve(self, t: float, shift_hours: float = 0.0) -> float:
        """Share of bots that should be online at ``t`` (0..1).

        Cached in fifteen-second steps and quarter-hour shifts: the controller
        asks for thousands of personal curves a pass, and there are only a few
        dozen distinct answers.
        """
        key = (int(t) // 15, int(round(shift_hours * 4)), bot_config.version())
        cached = self._curve_cache.get(key)
        if cached is not None:
            return cached
        if len(self._curve_cache) > 4000:
            self._curve_cache.clear()
        value = self._curve(t, round(shift_hours * 4) / 4.0)
        self._curve_cache[key] = value
        return value

    def _curve(self, t: float, shift_hours: float) -> float:
        hour, weekday = self._clock(t - shift_hours * 3600.0)
        start, end = bot_config.get("presence.peak_hours") or [18, 23]
        peak = float(bot_config.get("presence.peak_online") or 0) / 100.0
        low = float(bot_config.get("presence.offpeak_online") or 0) / 100.0
        ramp = max(0.01, float(bot_config.get("presence.ramp_hours") or 3.0))
        start, end = float(start) % 24, float(end) % 24
        span = (end - start) % 24 or 24.0
        into = (hour - start) % 24
        if into <= span:
            distance = 0.0
        else:
            distance = min(into - span, 24.0 - into)
        shoulder = low + (peak - low) * 0.25
        if distance <= ramp:
            level = shoulder + (peak - shoulder) * 0.5 * (1 + math.cos(math.pi * distance / ramp))
        else:
            far = max(0.01, (24.0 - span) / 2.0 - ramp)
            level = shoulder - (shoulder - low) * min(1.0, (distance - ramp) / far)
        if weekday >= 5:
            level *= 1.0 + float(bot_config.get("presence.weekend_boost") or 0) / 100.0
        return max(0.0, min(1.0, level))

    def _weekday(self, t: float) -> int:
        key = int(t) // 60
        if getattr(self, "_wd_key", None) != key:
            self._wd_key = key
            self._wd = self._clock(t)[1]
        return self._wd

    def personal(self, i: int, t: float) -> float:
        """How much bot ``i`` wants to be online at ``t``, relative to the
        crowd: night owls peak hours later, early birds hours earlier."""
        night = self.traits["night"][i]
        level = self.curve(t, shift_hours=night * 4.5)
        weekend = self.traits["weekend"][i]
        if weekend:
            weekday = self._weekday(t)
            level *= (1.0 + weekend) if weekday >= 5 else max(0.2, 1.0 - weekend * 0.6)
        return level * (0.4 + self.traits["activity"][i] * 1.2)

    def targets(self, now: float) -> Tuple[int, int]:
        """(bots that should be online, bots that should be in worlds)."""
        if not (self.enabled() and bot_config.get("presence.enabled")):
            return 0, 0
        online = int(round(self.n * self.curve(now)))
        share = float(bot_config.get("worlds.ingame_share") or 0) / 100.0
        if not bot_config.get("worlds.enabled"):
            share = 0.0
        return online, int(round(online * share))

    # ========================================================== presence
    def _plan_offline(self, i: int, now: int, fresh: bool = False) -> None:
        lo, hi = bot_config.get("presence.offline_hours") or [1, 48]
        activity = self.traits["activity"][i]
        # active personas skew towards the short end of the window
        span = float(hi) - float(lo)
        draw = float(lo) + span * (self.rng.random() ** (1.0 + activity * 1.6))
        seconds = draw * 3600.0
        base = self.since[i] if fresh else now
        when = int(base + seconds)
        if when < now + 30:
            # overdue (the server was down through its return): spread the
            # returns over a quarter of an hour instead of all at once
            when = now + 30 + int(self.rng.random() * 900)
        self._schedule(i, when)

    def _wake(self, i: int, now: int) -> None:
        if self.state[i] != OFFLINE:
            return
        self.state[i] = WAKING
        self.online += 1
        self.since[i] = now
        lo, hi = bot_config.get("presence.online_delay_minutes") or [1, 4]
        self.ready_at[i] = now + int(_between(self.rng, (lo, hi)) * 60)
        s_lo, s_hi = bot_config.get("presence.session_hours") or [0.5, 5]
        length = _between(self.rng, (s_lo, s_hi), self.traits["session"][i]) * 3600
        self.session_end[i] = now + int(max(120, length))
        self.seen_rows.append((now, int(self.uids[i])))
        self.recent_online.append(i)
        self.counters["woke"] += 1
        self._schedule(i, self.ready_at[i])

    def _sleep(self, i: int, now: int) -> None:
        if self.state[i] == OFFLINE:
            return
        if self.state[i] == PLAYING:
            self._leave_world(i, now, "left the server")
        self.state[i] = OFFLINE
        self.online -= 1
        self.since[i] = now
        self.seen_rows.append((now, int(self.uids[i])))
        self.counters["slept"] += 1
        self._plan_offline(i, now)

    def _event(self, i: int, now: int, want_online: int, want_playing: int) -> None:
        state = self.state[i]
        if not (self.enabled() and bot_config.get("presence.enabled")):
            if state != OFFLINE:
                self._sleep(i, now)
            else:
                self._schedule(i, now + 600)
            return
        if state == OFFLINE:
            lo, hi = bot_config.get("presence.offline_hours") or [1, 48]
            overdue = now - self.since[i] >= float(hi) * 3600
            if overdue or self.online < want_online * 1.02 or \
                    self.rng.random() < 0.15 * self.personal(i, now):
                self._wake(i, now)
            else:
                self._schedule(i, now + self.rng.randint(600, 3600))
            return
        if state == WAKING:
            self.state[i] = IDLE
            self._schedule(i, now + self.rng.randint(5, 90))
            if self.chatter is not None:
                self.chatter.on_ready(i, now)
            return
        if now >= self.session_end[i]:
            s_lo, s_hi = bot_config.get("presence.session_hours") or [0.5, 5]
            too_long = now - self.since[i] > float(s_hi) * 3600 * 1.5
            if self.online < want_online * 0.97 and not too_long:
                self.session_end[i] = now + self.rng.randint(600, 2400)
            elif self._mid_conversation(i, now):
                # nobody logs off halfway through a conversation
                decay = int(bot_config.get("modifiers.dm_decay_seconds") or 60)
                self.session_end[i] = now + decay + self.rng.randint(30, 180)
                self._schedule(i, self.session_end[i])
                return
            else:
                self._sleep(i, now)
                return
        if state == IDLE:
            if self._wants_game(i, want_playing):
                if self._join_world(i, now):
                    return
            self._schedule(i, now + self.rng.randint(120, 900))
            return
        if state == PLAYING:
            # the game session is over; take a break (or go home)
            self._leave_world(i, now, "left the server")
            b_lo, b_hi = bot_config.get("worlds.break_minutes") or [2, 18]
            self._schedule(i, now + int(_between(self.rng, (b_lo, b_hi)) * 60) + 5)

    def _wants_game(self, i: int, want_playing: int) -> bool:
        if not bot_config.get("worlds.enabled") or not self._any_host():
            return False
        pressure = want_playing / float(max(1, self.playing))
        chance = self.traits["gamer"][i] * min(3.0, max(0.15, pressure))
        return self.rng.random() < chance

    def _any_host(self) -> bool:
        self._check_hosts()
        return bool(self._hosts_up)

    def _check_hosts(self) -> None:
        now = time.time()
        if now - self._hosts_checked < 1.0:
            return
        self._hosts_checked = now
        from ..game import registry
        self._hosts_up = {w for w in WORLD_IDS if registry.raw(w)}

    # =========================================================== controller
    def _control(self, now: int) -> None:
        want_online, want_playing = self.targets(now)
        cap = max(4, int(bot_config.get("presence.max_changes_per_minute") or 3000) // 12)
        tolerance = max(1, int(self.n * 0.004))
        gap = want_online - self.online
        if gap > tolerance:
            self._wake_some(min(gap, cap), now)
        elif -gap > tolerance:
            self._sleep_some(min(-gap, cap), now)
        gap = want_playing - self.playing
        if gap > tolerance:
            self._start_games(min(gap, cap), now)
        elif -gap > tolerance * 2:
            self._end_games(min(-gap, cap // 2), now)

    def _sample(self, count: int, test, weight, tries: int) -> List[int]:
        picked: List[int] = []
        seen: Set[int] = set()
        n = self.n
        if not n:
            return picked
        for _ in range(tries):
            if len(picked) >= count:
                break
            i = self.rng.randrange(n)
            if i in seen or not test(i):
                continue
            seen.add(i)
            if self.rng.random() < weight(i):
                picked.append(i)
        return picked

    def _wake_some(self, count: int, now: int) -> None:
        lo = float((bot_config.get("presence.offline_hours") or [1, 48])[0]) * 3600
        base = max(0.02, self.curve(now))
        state, since = self.state, self.since

        def eligible(i: int) -> bool:
            return state[i] == OFFLINE and now - since[i] >= lo

        picked = self._sample(count, eligible,
                              lambda i: min(1.0, self.personal(i, now) / base * 0.6),
                              count * 40)
        for i in picked:
            self._wake(i, now)

    def _mid_conversation(self, i: int, now: int) -> bool:
        if not (bot_config.get("modifiers.dm_stay_online")
                and bot_config.get("modifiers.dm_enabled")) or self.chatter is None:
            return False
        return self.chatter.momentum.talking(int(self.uids[i]), now)

    def _sleep_some(self, count: int, now: int) -> None:
        base = max(0.02, self.curve(now))
        state = self.state

        def eligible(i: int) -> bool:
            if state[i] == OFFLINE:
                return False
            if state[i] == PLAYING and self._is_hosted(i):
                return False            # never pull a bot out of a live round
            if self._mid_conversation(i, now):
                return False            # or out of a conversation
            return True

        picked = self._sample(count, eligible,
                              lambda i: min(1.0, max(0.05, 1.2 - self.personal(i, now) / base)),
                              count * 30)
        for i in picked:
            self._sleep(i, now)

    def _start_games(self, count: int, now: int) -> None:
        if not bot_config.get("worlds.enabled") or not self._any_host():
            return
        state = self.state
        picked = self._sample(count, lambda i: state[i] == IDLE,
                              lambda i: self.traits["gamer"][i], count * 30)
        for i in picked:
            self._join_world(i, now)

    def _end_games(self, count: int, now: int) -> None:
        state = self.state
        picked = self._sample(count, lambda i: state[i] == PLAYING and not self._is_hosted(i),
                              lambda i: 1.0 - self.traits["gamer"][i] * 0.6, count * 30)
        for i in picked:
            self._leave_world(i, now, "left the server")
            self._schedule(i, now + self.rng.randint(120, 900))

    # ============================================================== worlds
    def _is_hosted(self, i: int) -> bool:
        w = self.world[i]
        if w == NO_WORLD:
            return False
        return int(self.uids[i]) in self.live[WORLD_IDS[w]]

    def _world_weights(self, i: int) -> List[float]:
        self._check_hosts()
        weights = bot_config.get("worlds.world_weights") or {}
        out = []
        for w, wid in enumerate(WORLD_IDS):
            if wid not in self._hosts_up:
                out.append(0.0)
                continue
            base = self.wpref[w][i] * float(weights.get(wid, 1.0))
            summary = self.summaries.get(wid) or {}
            crowd = summary.get("players", 0)
            out.append(max(0.0, base * (1.0 + math.log1p(crowd) * 0.08)))
        return out

    def _join_world(self, i: int, now: int, world: Optional[str] = None,
                    inst: Optional[int] = None) -> bool:
        uid = int(self.uids[i])
        if world is None and self.rng.random() < float(bot_config.get("worlds.follow_friends") or 0) / 100.0:
            spot = self._friend_spot(uid)
            if spot:
                world, inst = spot
        if world is None:
            weights = self._world_weights(i)
            if sum(weights) <= 0:
                return False
            world = self.rng.choices(WORLD_IDS, weights)[0]
        info = world_registry.get(world)
        if info is None:
            return False
        target = self._pick_instance(world, i, inst)
        if target is None:
            return False
        kind, inst_id = target
        w = WORLD_INDEX[world]
        self.state[i] = PLAYING
        self.world[i] = w
        self.inst[i] = inst_id
        self.playing += 1
        self.counters["joined"] += 1
        g_lo, g_hi = bot_config.get("worlds.session_minutes") or [10, 70]
        self._schedule(i, now + int(_between(self.rng, (g_lo, g_hi),
                                             0.6 + self.traits["gamer"][i] * 0.8) * 60))
        if kind == "dormant":
            self.dormant[world][inst_id].add(uid, now, self.traits["skill"][i],
                                             self.traits["objective"][i])
        else:
            self.expect[uid] = (world, inst_id, now + 15)
            self.live[world][uid] = inst_id
            hosted = self.hosted[world].get(inst_id)
            if hosted is not None:
                hosted["bots"] += 1
                hosted["count"] += 1
            self.ops[world].append({"op": "join", "inst": inst_id,
                                    "bot": self._bot_payload(i, None)})
        return True

    def _friend_spot(self, uid: int) -> Optional[Tuple[str, int]]:
        from ..game import registry
        try:
            friend_ids = social.friend_ids(uid)
        except Exception:
            return None
        self.rng.shuffle(friend_ids)
        for fid in friend_ids[:40]:
            j = self.index_of(fid)
            if j >= 0:
                if self.state[j] == PLAYING and self.world[j] != NO_WORLD:
                    return WORLD_IDS[self.world[j]], int(self.inst[j])
                continue
            where = registry.human_place(fid)
            if where:
                return where
        return None

    def _pick_instance(self, world: str, i: int,
                       prefer: Optional[int]) -> Optional[Tuple[str, int]]:
        info = world_registry.get(world)
        cap = int(info["max_players"])
        dorm = self.dormant[world]
        hosted = self.hosted[world]
        live_cap = int(bot_config.get("worlds.max_live_bots") or 0)
        live_ok = bool(bot_config.get("ingame.enabled")) and live_cap > 0
        if prefer is not None:
            if prefer in dorm and dorm[prefer].room() > 1:
                return "dormant", prefer
            h = hosted.get(prefer)
            if h and live_ok and h["count"] < cap and h["bots"] < live_cap:
                return "hosted", prefer
        # a live round with people in it pulls bots towards it
        pull = float(bot_config.get("worlds.human_pull") or 1.0)
        if live_ok:
            options = [(iid, h) for iid, h in hosted.items()
                       if h.get("humans") and h["count"] < cap - 1 and h["bots"] < live_cap
                       and not h.get("closing")]
            if options and self.rng.random() < min(0.95, 0.25 * pull):
                iid, _h = max(options, key=lambda o: (self.rng.random() * pull, -o[1]["count"]))
                return "hosted", iid
        pick = self._sample_open(world)
        if pick is not None:
            return "dormant", pick.id
        return "dormant", self._new_dormant(world).id

    # -------------------------------------------------- open-instance index
    def _mark_open(self, world: str, iid: int) -> None:
        if iid not in self.open_set[world]:
            self.open_set[world].add(iid)
            self.open[world].append(iid)

    def _rebuild_open(self) -> None:
        for world in WORLD_IDS:
            ids = [d.id for d in self.dormant[world].values()
                   if len(d.members) < d.cap and d.room() > 1]
            self.open[world] = ids
            self.open_set[world] = set(ids)
            self._free_hint[world] = 1

    def _sample_open(self, world: str):
        """A handful of sleeping instances with room, fuller ones favoured.

        Sampling six and weighting those keeps the preference for busy
        rounds that a weighted draw over every instance has, at a constant
        cost however many instances a world has.
        """
        ids = self.open[world]
        dorm = self.dormant[world]
        picks = []
        tries = 0
        while ids and len(picks) < 6 and tries < 24:
            tries += 1
            k = self.rng.randrange(len(ids))
            d = dorm.get(ids[k])
            if d is None or len(d.members) >= d.cap or d.room() <= 1:
                gone = ids[k]
                ids[k] = ids[-1]
                ids.pop()
                self.open_set[world].discard(gone)
                continue
            picks.append(d)
        if not picks:
            return None
        return self.rng.choices(picks, [1.0 + len(d.members) * 1.5 for d in picks])[0]

    def _new_dormant(self, world: str, inst_id: Optional[int] = None) -> dormant_model.Dormant:
        info = world_registry.get(world)
        if inst_id is None:
            inst_id = self._allocate_id(world)
        lo, hi = bot_config.get("worlds.fill") or [45, 92]
        cap = self.rng.uniform(float(lo), float(hi)) / 100.0
        inst = dormant_model.Dormant(info, inst_id, time.time(), random.Random(), cap)
        self.dormant[world][inst_id] = inst
        self._mark_open(world, inst_id)
        return inst

    def _allocate_id(self, world: str) -> int:
        dorm, hosted = self.dormant[world], self.hosted[world]
        # the lowest free number, so the list reads #1, #2, #3 rather than
        # counting up forever over a long-running server; the hint skips the
        # numbers known to be taken and falls back to 1 once a minute
        candidate = self._free_hint[world]
        while candidate in dorm or candidate in hosted:
            candidate += 1
        self._free_hint[world] = candidate + 1
        self.next_inst[world] = max(self.next_inst[world], candidate + 1)
        return candidate

    def _leave_world(self, i: int, now: int, reason: str = "") -> None:
        if self.state[i] != PLAYING:
            return
        w = self.world[i]
        world = WORLD_IDS[w] if w != NO_WORLD else ""
        inst_id = int(self.inst[i])
        uid = int(self.uids[i])
        self.state[i] = IDLE
        self.world[i] = NO_WORLD
        self.inst[i] = 0
        self.playing -= 1
        self.counters["left"] += 1
        self.expect.pop(uid, None)
        if not world:
            return
        dorm = self.dormant[world].get(inst_id)
        if dorm is not None:
            member = dorm.remove(uid, now)
            if member is not None:
                stats = dorm.sample_segment(member, now)
                seconds = now - member.joined
                stats.update({"uid": uid, "world": world, "at": now,
                              "visit": seconds >= 30})
                self.session_rows.append(stats)
            if not dorm.members:
                self.dormant[world].pop(inst_id, None)
                self._free_hint[world] = min(self._free_hint[world], inst_id)
            else:
                self._mark_open(world, inst_id)
        elif self.live[world].pop(uid, None) is not None:
            self.ops[world].append({"op": "leave", "uid": uid, "inst": inst_id,
                                    "reason": reason})
            hosted = self.hosted[world].get(inst_id)
            if hosted is not None:
                hosted["bots"] = max(0, hosted["bots"] - 1)
                hosted["count"] = max(0, hosted["count"] - 1)
                if self.chatter is not None and hosted.get("human_ids"):
                    self.chatter.after_live_round(i, list(hosted["human_ids"]), now)

    # ======================================================= host traffic
    def _bot_payload(self, i: int, member: Optional[dormant_model.Member]) -> Dict[str, Any]:
        """Everything a game host needs to put one bot in a live round."""
        from ..models import avatars
        uid = int(self.uids[i])
        card = self.card(uid)
        traits = card.get("traits") or {}
        return {
            "uid": uid, "name": card.get("name") or "Player",
            "avatar": avatars.descriptor(uid, card.get("name")),
            "team": member.team if member else "",
            "stats": [member.k, member.d, member.s] if member else [0, 0, 0],
            "tags": card.get("tags") or [],
            "traits": {k: traits.get(k) for k in (
                "skill", "aggression", "objective", "support", "explore",
                "chaos", "afk", "jumpy", "chatty", "toxicity", "kindness",
                "wp_sniper", "wp_shotgun", "wp_smg", "wp_rifle", "wp_melee",
                "wp_rocket", "lower", "emoji", "abbrev", "caps", "grammar")
                if k in traits},
            "bias": self._behaviour_bias(i),
        }

    def _behaviour_bias(self, i: int) -> Dict[str, float]:
        """The per-bot numbers the universal in-game settings turn into."""
        rng = random.Random(int(self.uids[i]))
        skill_lo, skill_hi = bot_config.get("ingame.skill") or [0.2, 0.85]
        r_lo, r_hi = bot_config.get("ingame.reaction_ms") or [220, 700]
        a_lo, a_hi = bot_config.get("ingame.aim_error") or [1.2, 7.5]
        skill = self.traits["skill"][i]
        return {
            "skill": round(skill_lo + (skill_hi - skill_lo) * skill, 3),
            "reaction": round(r_hi - (r_hi - r_lo) * skill * rng.uniform(0.8, 1.1), 1),
            "aim": round(a_hi - (a_hi - a_lo) * skill * rng.uniform(0.8, 1.1), 2),
            "objective": round(min(1.0, float(bot_config.get("ingame.objective_focus") or 72)
                                   / 100.0 * (0.5 + self.traits["objective"][i])), 3),
        }

    def take_ops(self, world: str) -> List[Dict[str, Any]]:
        with self.lock:
            ops = self.ops.get(world) or []
            self.ops[world] = []
            return ops

    def on_heartbeat(self, world: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """A game host reported in.  Returns what goes back to it."""
        if world not in self.hosted:
            return {}
        now = _now()
        with self.lock:
            hosted: Dict[int, Dict[str, Any]] = {}
            present: Dict[int, int] = {}
            for entry in payload.get("instances", []) or []:
                iid = int(entry.get("id", 0))
                humans = [int(p.get("user_id", 0)) for p in entry.get("players", [])
                          if not p.get("bot")]
                bots = [int(p.get("user_id", 0)) for p in entry.get("players", [])
                        if p.get("bot")]
                hosted[iid] = {"count": int(entry.get("count", len(humans) + len(bots))),
                               "max": int(entry.get("max", 16)),
                               "humans": len(humans), "bots": len(bots),
                               "human_ids": humans, "phase": entry.get("phase", ""),
                               "round": entry.get("round", 1),
                               "closing": bool(entry.get("closing"))}
                for uid in bots:
                    present[uid] = iid
            self.hosted[world] = hosted
            self.hosted_at[world] = time.time()
            for iid in hosted:
                # a live instance and a sleeping one can never share a number
                if iid in self.dormant[world]:
                    self._merge_into_live(world, iid, now)
                self.next_inst[world] = max(self.next_inst[world], iid + 1)
            w = WORLD_INDEX[world]
            live = self.live[world]
            # bots the host has: the host is the authority on where they are
            for uid, iid in present.items():
                i = self.index_of(uid)
                if i < 0:
                    continue
                self.expect.pop(uid, None)
                if self.state[i] == PLAYING and self.world[i] == w:
                    self.inst[i] = iid
                    live[uid] = iid
                else:
                    live.pop(uid, None)
                    self.ops[world].append({"op": "leave", "uid": uid, "inst": iid,
                                            "reason": "left the server"})
            # bots we placed in a live round that the host no longer has
            asleep = {int(snap.get("id", 0)) for snap in payload.get("dormant", []) or []}
            for uid, iid in list(live.items()):
                if uid in present or iid in asleep:
                    continue
                pending = self.expect.get(uid)
                if pending and pending[0] == world and now <= pending[2]:
                    continue
                live.pop(uid, None)
                self.expect.pop(uid, None)
                i = self.index_of(uid)
                if i >= 0 and self.state[i] == PLAYING and self.world[i] == w:
                    self.state[i] = IDLE
                    self.world[i] = NO_WORLD
                    self.inst[i] = 0
                    self.playing -= 1
                    self._schedule(i, now + self.rng.randint(60, 600))
            for snap in payload.get("dormant", []) or []:
                self._adopt_sleeper(world, snap, now)
            for left in payload.get("left", []) or []:
                live.pop(int(left.get("uid", 0)), None)
                i = self.index_of(int(left.get("uid", 0)))
                if i >= 0 and self.state[i] == PLAYING and self.world[i] == w:
                    self.state[i] = IDLE
                    self.world[i] = NO_WORLD
                    self.inst[i] = 0
                    self.playing -= 1
                    self._schedule(i, now + self.rng.randint(120, 900))
            reply: Dict[str, Any] = {"ops": self.ops[world],
                                     "reserve": self.next_inst[world]}
            self.ops[world] = []
        if self.gamechat is not None:
            for report in payload.get("chat", []) or []:
                try:
                    self.gamechat.on_report(world, report)
                except Exception:
                    traceback.print_exc()
        return reply

    def _merge_into_live(self, world: str, iid: int, now: int) -> None:
        """A number the host is running is also a sleeping instance here:
        the bots in the sleeping one move to another."""
        dorm = self.dormant[world].pop(iid, None)
        if dorm is None:
            return
        for uid in list(dorm.members):
            i = self.index_of(uid)
            dorm.remove(uid, now)
            if i >= 0 and self.state[i] == PLAYING:
                self.state[i] = IDLE
                self.world[i] = NO_WORLD
                self.inst[i] = 0
                self.playing -= 1
                self._join_world(i, now, world)

    def _adopt_sleeper(self, world: str, snap: Dict[str, Any], now: int) -> None:
        """A live instance with no people left has gone to sleep."""
        iid = int(snap.get("id", 0))
        if not iid:
            return
        self.hosted[world].pop(iid, None)
        dorm = self.dormant[world].get(iid) or self._new_dormant(world, iid)
        w = WORLD_INDEX[world]
        for row in snap.get("bots", []) or []:
            uid = int(row.get("uid", 0))
            i = self.index_of(uid)
            if i < 0:
                continue
            self.live[world].pop(uid, None)
            if self.state[i] != PLAYING or self.world[i] != w:
                continue
            member = dormant_model.Member(row.get("team") or "red", now,
                                          self.traits["skill"][i],
                                          self.traits["objective"][i])
            member.joined = now - int(row.get("played", 0) or 0)
            member.k, member.d, member.s = (int(v) for v in (row.get("stats") or [0, 0, 0])[:3])
            member.rounds = dorm.rounds_ended
            dorm.members[uid] = member
            self.inst[i] = iid
        # anybody we had in that round who did not come back with it has gone
        for uid, where in list(self.live[world].items()):
            if where == iid and uid not in dorm.members:
                self.live[world].pop(uid, None)
                i = self.index_of(uid)
                if i >= 0 and self.state[i] == PLAYING and self.world[i] == w:
                    self.state[i] = IDLE
                    self.world[i] = NO_WORLD
                    self.inst[i] = 0
                    self.playing -= 1
                    self._schedule(i, now + self.rng.randint(60, 600))
        dorm.from_live(snap.get("live") or {}, now)
        if dorm.mode == "endless":
            for plot in dorm.plots:
                plot["members"] = [u for u in plot["members"] if u in dorm.members]
        if not dorm.members:
            self.dormant[world].pop(iid, None)
        self.counters["slept_instances"] += 1
        self._note("%s #%d went to sleep with %d bots" % (world, iid, len(dorm.members)))

    # ======================================================== real players
    def place_human(self, world: str, prefer: Optional[int], uid: int) -> Optional[int]:
        """Pick (and wake, if needed) the instance a person should join.

        People go where other people are first, so two players on a quiet
        server end up in the same round.  Otherwise a sleeping instance with
        room is woken -- mid-round, busy, alive -- and failing that the host
        opens a fresh one.
        """
        if world not in self.dormant:
            return prefer
        now = _now()
        info = world_registry.get(world)
        cap = int(info["max_players"])
        ingame = bool(bot_config.get("ingame.enabled")) and self.enabled()
        with self.lock:
            hosted = self.hosted[world]
            if prefer:
                if prefer in hosted:
                    if hosted[prefer]["count"] >= cap and hosted[prefer]["bots"]:
                        self._yield_seat(world, prefer, now)
                    return prefer
                if prefer in self.dormant[world]:
                    if not ingame:
                        return self._fresh_id(world)
                    return self._hydrate(world, prefer, now)
            human_rounds = [(iid, h) for iid, h in hosted.items()
                            if h.get("humans") and h["count"] < cap]
            if human_rounds:
                return max(human_rounds, key=lambda o: o[1]["humans"])[0]
            if ingame and self.dormant[world]:
                options = [d for d in self.dormant[world].values() if d.room() >= 1]
                if options:
                    def score(d):
                        fill = d.count / float(d.max)
                        return -abs(fill - 0.7) + self.rng.random() * 0.15
                    best = max(options, key=score)
                    return self._hydrate(world, best.id, now)
            for iid, h in hosted.items():
                if h["count"] < cap and (ingame or not h["bots"]):
                    return iid
            return self._fresh_id(world)

    def _fresh_id(self, world: str) -> int:
        return self._allocate_id(world)

    def _yield_seat(self, world: str, iid: int, now: int) -> None:
        """A full live instance a person wants into: one bot heads off."""
        for uid, where in list(self.live[world].items()):
            i = self.index_of(uid)
            if where == iid and i >= 0:
                self._leave_world(i, now, "left the server")
                self._schedule(i, now + self.rng.randint(60, 600))
                return

    def _hydrate(self, world: str, iid: int, now: int) -> Optional[int]:
        """Wake a sleeping instance on its game host, mid-round."""
        from ..game import registry
        dorm = self.dormant[world].get(iid)
        if dorm is None:
            return None
        dorm.advance(now, float(bot_config.get("worlds.sim_pace") or 1.0))
        live_cap = int(bot_config.get("worlds.max_live_bots") or 0)
        keep_room = 1
        limit = max(0, min(live_cap, dorm.max - keep_room))
        # anybody over the live limit moves to another sleeping instance, so
        # the world's player count does not jump when a person arrives
        overflow = list(dorm.members)[limit:]
        for uid in overflow:
            i = self.index_of(uid)
            member = dorm.remove(uid, now)
            if i >= 0 and member is not None and self.state[i] == PLAYING:
                others = [d for d in self.dormant[world].values()
                          if d.id != iid and d.room() > 1]
                target = others[0] if others else self._new_dormant(world)
                target.add(uid, now, member.skill, member.objective)
                self.inst[i] = target.id
        bots = []
        for uid, member in list(dorm.members.items()):
            i = self.index_of(uid)
            if i < 0:
                dorm.remove(uid, now)
                continue
            stats = dorm.sample_segment(member, now)
            stats.update({"uid": uid, "world": world, "at": now,
                          "visit": now - member.joined >= 30})
            self.session_rows.append(stats)
            if bot_config.get("worlds.progress_on_wake"):
                dorm.scoreboard_fill(member, now)
            payload = self._bot_payload(i, member)
            payload["played"] = int(now - member.joined)
            bots.append(payload)
        state = dorm.wake_state(now) if bot_config.get("worlds.progress_on_wake") \
            else {"mode": dorm.mode, "round": 1, "phase": "active"}
        body = {"action": "hydrate", "inst": iid, "state": state, "bots": bots,
                "config": bot_config.ingame_section()}
        ok = registry.control(world, body, timeout=6.0)
        if not ok or not ok.get("ok"):
            self._note("could not wake %s #%d: %s" % (world, iid, (ok or {}).get("error", "host did not answer")))
            return self._fresh_id(world)
        self.dormant[world].pop(iid, None)
        self.hosted[world][iid] = {"count": len(bots), "max": dorm.max, "humans": 0,
                                   "bots": len(bots), "human_ids": [],
                                   "phase": dorm.phase, "round": dorm.round}
        for payload in bots:
            self.expect[int(payload["uid"])] = (world, iid, now + 20)
            self.live[world][int(payload["uid"])] = iid
        self.counters["hydrated"] += 1
        self._note("woke %s #%d for a player (%d bots, %s)"
                   % (world, iid, len(bots), dorm.summary()))
        return iid

    # ============================================================ summaries
    def _summarise(self, now: float) -> None:
        """Refresh the per-world numbers the site reads, and advance a slice
        of the sleeping instances.

        The counts are recomputed every two seconds (a sum over instances),
        the sorted listing every five and only its top rows, and each pass
        advances a sixtieth of the sleeping instances, so every one is fresh
        within a minute without ever advancing them all at once.
        """
        import heapq
        pace = float(bot_config.get("worlds.sim_pace") or 1.0)
        relist = now - self._listing_at >= 5.0
        if relist:
            self._listing_at = now
        if now - self._open_at >= 60.0:
            self._open_at = now
            self._rebuild_open()
        recount = now - self._count_at >= 2.0
        if recount:
            self._count_at = now
        for world in WORLD_IDS:
            insts = self.dormant[world]
            summary = self.summaries.get(world)
            if summary is None or recount or relist:
                summary = summary or {}
                players = 0
                for inst in insts.values():
                    players += len(inst.members)
                summary.update({"players": players, "instances": len(insts), "at": now})
            if relist or "list" not in summary:
                top = heapq.nlargest(80, insts.values(), key=lambda d: (len(d.members), -d.id))
                summary["list"] = [d.describe() for d in top]
            self.summaries[world] = summary
        if now - self._flat_at >= 10.0 or not self._flat:
            self._flat_at = now
            self._flat = [(w, d) for w in WORLD_IDS for d in self.dormant[w].values()]
        everything = self._flat
        if not everything:
            return
        # nobody can see a sleeping round's phase change within a minute, and
        # one that is woken, joined or left is advanced to the second anyway
        step = max(1, len(everything) // 60)
        start = self._dorm_cursor % len(everything)
        for world, inst in everything[start:start + step]:
            if inst.members:
                inst.advance(now, pace)
        self._dorm_cursor = start + step

    def world_view(self, world: str) -> Dict[str, Any]:
        return self.summaries.get(world) or {"players": 0, "instances": 0, "list": []}

    def rounds(self, per_world: int = 24) -> Dict[str, Any]:
        """Every round in every world, live first, for the dashboard."""
        now = _now()
        out: Dict[str, Any] = {}
        with self.lock:
            for world in WORLD_IDS:
                rows: List[Dict[str, Any]] = []
                for iid, h in sorted(self.hosted[world].items()):
                    if not (h["bots"] or h["humans"]):
                        continue
                    rows.append({"id": iid, "state": "live", "bots": h["bots"],
                                 "humans": h["humans"], "max": h["max"],
                                 "round": h.get("round", 1), "phase": h.get("phase", ""),
                                 "summary": ""})
                sleeping = sorted(self.dormant[world].values(), key=lambda d: -d.count)
                for inst in sleeping[:max(0, per_world - len(rows))]:
                    rows.append({"id": inst.id, "state": "asleep", "bots": inst.count,
                                 "humans": 0, "max": inst.max, "round": inst.round,
                                 "phase": inst.phase, "summary": inst.summary(),
                                 "age": max(0, now - int(inst.created))})
                out[world] = {"rows": rows,
                              "hidden": max(0, len(sleeping) + len(rows) - per_world)}
        return out

    def dormant_players(self, world: str, limit: int = 60) -> List[Dict[str, Any]]:
        with self.lock:
            out = []
            for inst in sorted(self.dormant.get(world, {}).values(),
                               key=lambda d: -d.count):
                for uid, member in inst.members.items():
                    out.append({"user_id": uid, "instance": inst.id,
                                "team": member.team, "score": member.s,
                                "kills": member.k})
                    if len(out) >= limit:
                        return out
            return out

    # ================================================================ cards
    _cards: Dict[int, Dict[str, Any]] = {}

    def card(self, uid: int) -> Dict[str, Any]:
        card = self._cards.get(uid)
        if card is not None:
            return card
        row = db.query_one(
            "SELECT u.id, u.username, u.blurb, u.created_at, b.tags, b.traits,"
            " b.voice FROM users u JOIN bot_profiles b ON b.user_id=u.id"
            " WHERE u.id=?", (uid,))
        if row is None:
            return {"id": uid, "name": "", "tags": [], "traits": {}}
        traits = personas.unpack_traits(row["traits"])
        card = {"id": uid, "name": row["username"], "blurb": row["blurb"],
                "joined": int(row["created_at"] or 0),
                "tags": personas.parse_tags(row["tags"]), "traits": traits,
                "voice": row["voice"]}
        if len(self._cards) > 4000:
            self._cards.clear()
        self._cards[uid] = card
        return card

    # ================================================================ loop
    def start(self) -> None:
        if self._thread is not None:
            return
        from . import chatter, gamechat
        self.chatter = chatter.Engine(self)
        self.gamechat = gamechat.Relay(self)
        storage.ensure_root()
        self._thread = threading.Thread(target=self._run, daemon=True,
                                        name="bots-director")
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        try:
            self._flush()
            self.save_snapshot()
        except Exception:
            pass

    def _run(self) -> None:
        try:
            self.load()
        except Exception:
            traceback.print_exc()
            self.loaded = True
        self.started = time.time()
        try:
            from . import llm
            threading.Thread(target=lambda: llm.client().probe(True),
                             daemon=True, name="bots-probe").start()
        except Exception:
            pass
        while not self._stop.is_set():
            began = time.time()
            try:
                self.tick(began)
            except Exception:
                traceback.print_exc()
            self.last_tick_ms = (time.time() - began) * 1000.0
            self._stop.wait(max(0.1, 1.0 - (time.time() - began)))

    last_tick_ms = 0.0

    def tick(self, t: float) -> None:
        now = int(t)
        with self.lock:
            want_online, want_playing = self.targets(now)
            for i in self._due(now, 800):
                self._event(i, now, want_online, want_playing)
            if t - self._last["ctrl"] >= 5.0:
                self._last["ctrl"] = t
                self._control(now)
            if t - self._last["dorm"] >= 1.0:
                self._last["dorm"] = t
                self._summarise(t)
            if t - self._last["hist"] >= 60.0:
                self._last["hist"] = t
                self.history.append({"at": now, "online": self.online,
                                     "playing": self.playing,
                                     "target": want_online, "n": self.n})
        if self.chatter is not None:
            try:
                self.chatter.tick(t)
            except Exception:
                traceback.print_exc()
        if self.gamechat is not None:
            try:
                self.gamechat.tick(t)
            except Exception:
                traceback.print_exc()
        if t - self._last["flush"] >= 8.0:
            self._last["flush"] = t
            self._flush()
        if t - self._last["snap"] >= 180.0:
            self._last["snap"] = t
            self.save_snapshot()
        if t - self._last["prune"] >= 3600.0:
            self._last["prune"] = t
            try:
                social.prune_bot_visits()
            except Exception:
                pass
        try:
            from . import factory
            factory.auto_tick(t)
        except Exception:
            traceback.print_exc()

    def _flush(self) -> None:
        with self.lock:
            rows, self.session_rows = self.session_rows, []
            seen, self.seen_rows = self.seen_rows, []
        if seen:
            social.set_last_seen(seen)
        if rows:
            social.write_sessions(rows)

    def _note(self, text: str) -> None:
        self.events.append({"at": _now(), "text": text})

    # ============================================================ warm start
    def _warm_start(self, now: int) -> None:
        """Start as if the bots had been running all along."""
        if not self.n:
            return
        want_online, want_playing = self.targets(now)
        if not bot_config.get("worlds.warm_start"):
            want_online = min(want_online, max(1, self.n // 50))
        # weighted sample without replacement: key = u ** (1 / w)
        keyed = []
        for i in range(self.n):
            weight = max(1e-4, self.personal(i, now))
            keyed.append((self.rng.random() ** (1.0 / weight), i))
        keyed.sort(reverse=True)
        chosen = [i for _k, i in keyed[:want_online]]
        chosen_set = set(chosen)
        s_lo, s_hi = bot_config.get("presence.session_hours") or [0.5, 5]
        for i in range(self.n):
            if i in chosen_set:
                continue
            self.state[i] = OFFLINE
            lo, hi = bot_config.get("presence.offline_hours") or [1, 48]
            since = self.since[i]
            if since <= 0 or now - since > float(hi) * 3600:
                since = now - int(self.rng.uniform(0, float(hi) * 3600))
                self.since[i] = since
            self._plan_offline(i, now, fresh=True)
        for i in chosen:
            self.state[i] = IDLE
            self.online += 1
            length = _between(self.rng, (s_lo, s_hi), self.traits["session"][i]) * 3600
            elapsed = self.rng.uniform(0, length)
            self.since[i] = int(now - elapsed)
            self.ready_at[i] = self.since[i]
            self.session_end[i] = int(now + max(300, length - elapsed))
            self.recent_online.append(i)
            self._schedule(i, now + self.rng.randint(30, 900))
        # the ones who are gaming, straight into worlds
        gamers = sorted(chosen, key=lambda i: -self.traits["gamer"][i] * self.rng.random())
        if bot_config.get("worlds.enabled") and bot_config.get("worlds.warm_start"):
            for i in gamers[:want_playing]:
                self._warm_join(i, now)
        for world in WORLD_IDS:
            for inst in self.dormant[world].values():
                inst.warm(now)
        self._summarise(time.time())

    def _warm_join(self, i: int, now: int) -> None:
        weights = [self.wpref[w][i] * float((bot_config.get("worlds.world_weights") or {})
                                            .get(wid, 1.0)) for w, wid in enumerate(WORLD_IDS)]
        if sum(weights) <= 0:
            return
        world = self.rng.choices(WORLD_IDS, weights)[0]
        target = self._pick_instance(world, i, None)
        if target is None or target[0] != "dormant":
            return
        inst_id = target[1]
        self.state[i] = PLAYING
        self.world[i] = WORLD_INDEX[world]
        self.inst[i] = inst_id
        self.playing += 1
        self.dormant[world][inst_id].add(int(self.uids[i]), now,
                                         self.traits["skill"][i],
                                         self.traits["objective"][i])
        g_lo, g_hi = bot_config.get("worlds.session_minutes") or [10, 70]
        self._schedule(i, now + int(self.rng.uniform(0.1, 1.0)
                                    * _between(self.rng, (g_lo, g_hi)) * 60) + 30)

    # ============================================================ snapshots
    def save_snapshot(self) -> None:
        if not self.loaded or not self.n:
            return
        with self.lock:
            data = {
                "at": _now(), "n": self.n,
                "uids": base64.b64encode(self.uids.tobytes()).decode(),
                "state": base64.b64encode(bytes(self.state)).decode(),
                "world": base64.b64encode(bytes(self.world)).decode(),
                "inst": base64.b64encode(self.inst.tobytes()).decode(),
                "next_at": base64.b64encode(self.next_at.tobytes()).decode(),
                "since": base64.b64encode(self.since.tobytes()).decode(),
                "ready_at": base64.b64encode(self.ready_at.tobytes()).decode(),
                "session_end": base64.b64encode(self.session_end.tobytes()).decode(),
                "dormant": [d.dump() for w in WORLD_IDS for d in self.dormant[w].values()],
                "history": [[p["at"], p["online"], p["playing"], p["target"]]
                            for p in self.history],
            }
        try:
            storage.ensure_root()
            temp = str(SNAPSHOT) + ".tmp"
            with open(temp, "w") as handle:
                json.dump(data, handle, separators=(",", ":"))
            os.replace(temp, str(SNAPSHOT))
        except OSError:
            pass

    def _restore_history(self, rows: List[Any], now: int) -> None:
        if self.history:
            return
        for row in rows:
            try:
                at, online, playing, target = (int(v) for v in row[:4])
            except (TypeError, ValueError):
                continue
            if now - 24 * 3600 < at <= now:
                self.history.append({"at": at, "online": online, "playing": playing,
                                     "target": target, "n": self.n})

    def _restore_snapshot(self, now: int) -> bool:
        try:
            with open(str(SNAPSHOT)) as handle:
                data = json.load(handle)
        except (OSError, ValueError):
            return False
        # the activity chart survives a restart even when the rest is stale
        self._restore_history(data.get("history") or [], now)
        if now - int(data.get("at", 0)) > SNAPSHOT_MAX_AGE:
            return False

        def unpack(key: str, code: str):
            raw = base64.b64decode(data[key])
            if code == "B":
                return bytearray(raw)
            out = array(code)
            out.frombytes(raw)
            return out
        try:
            uids = unpack("uids", "I")
            fields = {k: unpack(k, c) for k, c in (
                ("state", "B"), ("world", "B"), ("inst", "I"), ("next_at", "I"),
                ("since", "I"), ("ready_at", "I"), ("session_end", "I"))}
        except (KeyError, ValueError):
            return False
        places = {int(u): j for j, u in enumerate(uids)}
        for world_dump in data.get("dormant", []):
            world = world_registry.get(world_dump.get("world", ""))
            if world is None:
                continue
            inst = dormant_model.Dormant.load(world, world_dump)
            inst.members = {u: m for u, m in inst.members.items() if self.index_of(u) >= 0}
            if inst.members:
                self.dormant[world["id"]][inst.id] = inst
        for i in range(self.n):
            j = places.get(int(self.uids[i]))
            if j is None:
                self._plan_offline(i, now, fresh=True)
                continue
            state = fields["state"][j]
            self.since[i] = fields["since"][j]
            self.ready_at[i] = fields["ready_at"][j]
            self.session_end[i] = fields["session_end"][j]
            if state == PLAYING:
                w = fields["world"][j]
                iid = int(fields["inst"][j])
                if w == NO_WORLD or iid not in self.dormant.get(WORLD_IDS[w], {}) \
                        or int(self.uids[i]) not in self.dormant[WORLD_IDS[w]][iid].members:
                    state = IDLE
                else:
                    self.world[i] = w
                    self.inst[i] = iid
                    self.playing += 1
            self.state[i] = state
            if state != OFFLINE:
                self.online += 1
                if state == IDLE:
                    self.recent_online.append(i)
            self._schedule(i, max(now + 1, fields["next_at"][j]))
        # sleeping instances whose bots came back as something else
        for world in WORLD_IDS:
            for iid, inst in list(self.dormant[world].items()):
                for uid in list(inst.members):
                    i = self.index_of(uid)
                    if i < 0 or self.state[i] != PLAYING or self.world[i] != WORLD_INDEX[world] \
                            or int(self.inst[i]) != iid:
                        inst.members.pop(uid, None)
                if not inst.members:
                    self.dormant[world].pop(iid, None)
        return True

    # =============================================================== stats
    def stats(self) -> Dict[str, Any]:
        with self.lock:
            now = _now()
            want_online, want_playing = self.targets(now)
            per_world = {}
            for world in WORLD_IDS:
                summary = self.summaries.get(world) or {}
                live_bots = sum(h["bots"] for h in self.hosted[world].values())
                live_humans = sum(h["humans"] for h in self.hosted[world].values())
                per_world[world] = {
                    "sleeping_bots": summary.get("players", 0),
                    "sleeping_instances": summary.get("instances", 0),
                    "live_bots": live_bots, "live_humans": live_humans,
                    "live_instances": len(self.hosted[world]),
                    # a host keeps an empty round warm; only count rounds with players
                    "active_instances": sum(1 for h in self.hosted[world].values()
                                            if h["bots"] or h["humans"]),
                }
            return {
                "total": self.n, "online": self.online, "playing": self.playing,
                "offline": self.n - self.online,
                "target_online": want_online, "target_playing": want_playing,
                "curve_now": round(self.curve(now), 4),
                "worlds": per_world, "counters": dict(self.counters),
                "tick_ms": round(self.last_tick_ms, 2),
                "events": list(self.events)[-30:],
                "history": list(self.history)[-360:],
                "plan": self.plan(now),
                "loaded": self.loaded,
                "enabled": self.enabled(),
            }

    # ============================================================ dashboard
    STATE_KEYS = {"offline": OFFLINE, "waking": WAKING, "online": IDLE,
                  "playing": PLAYING}

    def presence(self, uid: int) -> Dict[str, Any]:
        i = self.index_of(uid)
        if i < 0:
            return {}
        state = self.state[i]
        world = WORLD_IDS[self.world[i]] if self.world[i] != NO_WORLD else ""
        live = bool(world) and int(self.uids[i]) in self.live.get(world, {})
        return {"state": {OFFLINE: "offline", WAKING: "waking", IDLE: "online",
                          PLAYING: "playing"}[state],
                "label": STATE_NAMES[state], "world": world,
                "instance": int(self.inst[i]) if world else 0, "live": live,
                "since": int(self.since[i]), "ready_at": int(self.ready_at[i]),
                "session_end": int(self.session_end[i]) if state != OFFLINE else 0,
                "next_at": int(self.next_at[i]), "friends": int(self.friends[i]),
                "friend_target": int(self.friend_target[i])}

    def select(self, state: str = "", world: str = "", offset: int = 0,
               limit: int = 50) -> Tuple[int, List[int]]:
        """Bots in a presence state and/or world, most recently changed
        first -- for the Bot Stats table."""
        want_state = self.STATE_KEYS.get(state)
        want_world = WORLD_INDEX.get(world) if world else None
        with self.lock:
            picked = []
            st, wd = self.state, self.world
            for i in range(self.n):
                if want_state is not None and st[i] != want_state:
                    continue
                if want_world is not None and wd[i] != want_world:
                    continue
                picked.append(i)
            picked.sort(key=lambda i: -self.since[i])
            total = len(picked)
            return total, [int(self.uids[i]) for i in picked[offset:offset + limit]]

    def tag_counts(self) -> Dict[str, int]:
        counts: Dict[int, int] = {}
        with self.lock:
            for bit, members in self.tag_index.items():
                counts[bit] = len(members)
        out = {}
        for tag in personas.all_tags():
            bit = personas._bits.get(tag["id"])
            if bit is not None:
                out[tag["id"]] = counts.get(bit, 0)
        return out

    def force(self, uid: int, action: str, world: str = "") -> str:
        """Admin overrides: log a bot in or out, send it somewhere."""
        now = _now()
        with self.lock:
            i = self.index_of(uid)
            if i < 0:
                return "not a bot"
            if action == "online":
                if self.state[i] == OFFLINE:
                    self._wake(i, now)
                    # skip the settling-in wait: the administrator asked
                    self.ready_at[i] = now
                    self._schedule(i, now + 1)
                return "online"
            if action == "offline":
                self._sleep(i, now)
                return "offline"
            if action == "leave":
                if self.state[i] == PLAYING:
                    self._leave_world(i, now, "left the server")
                    self._schedule(i, now + self.rng.randint(120, 900))
                return "left"
            if action == "join":
                if world not in WORLD_INDEX:
                    return "no such world"
                if self.state[i] == OFFLINE:
                    self._wake(i, now)
                if self.state[i] == PLAYING:
                    self._leave_world(i, now)
                self.state[i] = IDLE
                return "joined" if self._join_world(i, now, world) else "no room"
        return "unknown action"

    def online_sample(self, limit: int) -> List[int]:
        """Account ids of bots that came online most recently and still are."""
        with self.lock:
            out: List[int] = []
            seen: Set[int] = set()
            for i in reversed(self.recent_online):
                if i < self.n and self.state[i] != OFFLINE and i not in seen:
                    seen.add(i)
                    out.append(int(self.uids[i]))
                    if len(out) >= limit:
                        break
            return out

    def plan(self, now: int, back_hours: int = 6, ahead_hours: int = 2) -> List[Dict[str, int]]:
        """The target line for the activity chart, every ten minutes."""
        if not (self.enabled() and bot_config.get("presence.enabled")):
            return []
        start = now - now % 600 - back_hours * 3600
        steps = (back_hours + ahead_hours) * 6 + 1
        return [{"at": start + k * 600,
                 "target": int(round(self.n * self.curve(start + k * 600)))}
                for k in range(steps + 1)]

    def curve_preview(self) -> List[Dict[str, Any]]:
        """Tomorrow's target curve, hour by hour, for the settings page."""
        now = _now()
        start = now - now % 3600
        return [{"at": start + h * 1800,
                 "share": round(self.curve(start + h * 1800), 4)}
                for h in range(48)]


_director: Optional[Director] = None
_lock = threading.Lock()


def get() -> Director:
    global _director
    with _lock:
        if _director is None:
            _director = Director()
        return _director


def running() -> Optional[Director]:
    """The director if it has been started, for hooks that must be cheap."""
    director = _director
    if director is None or director._thread is None:
        return None
    return director
