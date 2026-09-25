"""Bots' social lives: friends, comment sections, posts, likes and DMs.

Everything here waits for the bot to be *there*: a request, a comment on its
wall or a private message that arrives while it is offline sits until it logs
in and its online delay has passed, and then it gets a reading-and-typing
delay of its own before the answer goes out.  A bot does not answer at three
in the morning unless it is the kind that is up at three in the morning.

**Friends** come from shared tags.  Every tag has an inverted index of the
bots carrying it, so finding someone a bot has at least *friend depth* tags in
common with is a couple of random picks, not a scan.  Requests are confirmed
(or ignored, or occasionally declined) by the recipient when it is next
online, with the odds set by how much the two have in common and by how
choosy the recipient's persona is.

**Chatter** is comments between closely associated bots -- friends, or bots
sharing enough tags -- one every so often per bot inside the configured
range, budgeted per minute so the language model stays free for people.
A comment on a bot's wall can draw a reply, so conversations actually form.

**Replies to people** -- a comment on a bot's wall, a DM -- go ahead of
bot-to-bot chatter in the model's queue, and use the log of that
conversation, from that bot's folder, as their context.
"""
from __future__ import annotations

import random
import threading
import time
import traceback
from array import array
from typing import Any, Dict, List, Optional, Tuple

from .. import db
from . import config as bot_config
from . import llm, modifiers, personas, prompts, social, storage

IDLE, PLAYING = 2, 3


def _now() -> int:
    return int(time.time())


class Bucket:
    """A token bucket: ``rate`` per ``per`` seconds, a little burst allowed."""

    def __init__(self):
        self.tokens = 0.0
        self.at = time.time()

    def take(self, rate: float, per: float = 60.0) -> bool:
        if rate <= 0:
            return False
        now = time.time()
        per_second = rate / per
        self.tokens = min(max(1.0, per_second * 30), self.tokens + (now - self.at) * per_second)
        self.at = now
        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True
        return False


class Engine:
    def __init__(self, director):
        self.d = director
        self.rng = random.Random()
        self.lock = threading.RLock()
        self.comment_at = array("I")
        self.post_at = array("I")
        self.friend_at = array("I")
        self.wheel: Dict[int, List[int]] = {}
        self.wheel_floor = _now()
        self.pending_dm: Dict[int, Dict[int, float]] = {}     # bot uid -> {other uid: due}
        self.pending_wall: Dict[int, List[Dict[str, Any]]] = {}
        self.busy: Dict[Tuple[int, int], float] = {}           # (bot, other) job in flight
        self.ignored: Dict[int, float] = {}                    # friendship id -> retry at
        self.friend_bucket = Bucket()
        self.comment_bucket = Bucket()
        self.pending_cursor = 0
        self.last = {"requests": 0.0, "replies": 0.0}
        self.stats = {"requests_sent": 0, "accepted": 0, "declined": 0,
                      "comments": 0, "replies": 0, "posts": 0, "likes": 0,
                      "dms": 0, "follows": 0, "deferred": 0}
        self.recent: List[Dict[str, Any]] = []
        self.primed = 0
        self.momentum = modifiers.Momentum()

    # --------------------------------------------------------------- timers
    def _ensure(self) -> None:
        n = self.d.n
        while len(self.comment_at) < n:
            self.comment_at.append(0)
            self.post_at.append(0)
            self.friend_at.append(0)

    def _interval(self, key: str, i: int, fallback) -> int:
        lo, hi = bot_config.get(key) or fallback
        sociable = self.d.traits["social"][i]
        hours = self.rng.uniform(float(lo), float(hi)) * (1.35 - sociable * 0.7)
        return int(max(60, hours * 3600))

    def _file(self, i: int, when: int) -> None:
        self.wheel.setdefault(int(when), []).append(i)

    def on_ready(self, i: int, now: int) -> None:
        """A bot has just finished settling in after logging on."""
        with self.lock:
            self._ensure()
            if not self.comment_at[i]:
                self.comment_at[i] = now + self.rng.randint(
                    60, max(120, self._interval("chatter.interval_hours", i, [1, 5]) // 2))
            if not self.post_at[i]:
                self.post_at[i] = now + self._interval("chatter.post_interval_hours", i, [8, 72]) // 2
            if not self.friend_at[i]:
                self.friend_at[i] = now + self.rng.randint(60, 1800)
            self._file(i, now + self.rng.randint(30, 600))

    # ----------------------------------------------------------------- tick
    def _prime(self, now: int) -> None:
        """File every bot that is already online (a warm start, a restored
        snapshot) into the social timers -- a few thousand a pass, so a big
        population is taken in over a few seconds rather than in one stall."""
        n = self.d.n
        end = min(n, self.primed + 5000)
        state = self.d.state
        for i in range(self.primed, end):
            if state[i] in (IDLE, PLAYING):
                self.on_ready(i, now + self.rng.randint(0, 1800))
        self.primed = end

    def tick(self, t: float) -> None:
        if not self.d.enabled():
            return
        now = int(t)
        if self.primed < self.d.n and self.d.loaded:
            self._prime(now)
        with self.lock:
            self._ensure()
            due: List[int] = []
            floor = self.wheel_floor
            while floor <= now and len(due) < 400:
                due.extend(self.wheel.pop(floor, ()))
                floor += 1
            self.wheel_floor = floor
        for i in due:
            try:
                self._social_event(i, now)
            except Exception:
                traceback.print_exc()
        if t - self.last["requests"] >= 3.0:
            self.last["requests"] = t
            try:
                self._deliver_requests(now)
            except Exception:
                traceback.print_exc()
        if t - self.last["replies"] >= 2.0:
            self.last["replies"] = t
            self._answer_pending(now)
        if t - self.last.get("prune", 0.0) >= 60.0:
            self.last["prune"] = t
            self.momentum.prune(t)

    def _ready(self, i: int) -> bool:
        return i < self.d.n and self.d.state[i] in (IDLE, PLAYING)

    def _social_event(self, i: int, now: int) -> None:
        if not self._ready(i):
            return          # it will be refiled when it next logs on
        uid = int(self.d.uids[i])
        if bot_config.get("friends.enabled") and now >= self.friend_at[i]:
            self.friend_at[i] = now + self.rng.randint(900, 7200)
            if self.d.friends[i] < self.d.friend_target[i]:
                self._send_request(i, uid, now)
        if bot_config.get("chatter.likes") and self.rng.random() < 0.35:
            self._like(i, uid)
        if bot_config.get("chatter.enabled") and now >= self.comment_at[i]:
            if self._comment(i, uid, now):
                self.comment_at[i] = now + self._interval("chatter.interval_hours", i, [1, 5])
            else:
                self.comment_at[i] = now + self.rng.randint(300, 1800)
                self.stats["deferred"] += 1
        if bot_config.get("chatter.posts") and now >= self.post_at[i]:
            self.post_at[i] = now + self._interval("chatter.post_interval_hours", i, [8, 72])
            self._post(i, uid)
        nxt = min(self.comment_at[i], self.post_at[i], self.friend_at[i])
        with self.lock:
            self._file(i, max(now + 60, nxt))

    # -------------------------------------------------------------- friends
    def candidate(self, i: int, depth: int, tries: int = 16) -> int:
        """Another bot sharing at least ``depth`` tags with bot ``i``, or -1."""
        d = self.d
        mask = d.masks[i]
        bits = [b for b in d.tag_index if mask >> b & 1]
        if not bits:
            return -1
        for _ in range(tries):
            members = d.tag_index.get(self.rng.choice(bits))
            if not members:
                continue
            j = members[self.rng.randrange(len(members))]
            if j == i or j >= d.n:
                continue
            if personas.shared(mask, d.masks[j]) >= depth:
                return j
        return -1

    def _send_request(self, i: int, uid: int, now: int) -> None:
        per_hour = float(bot_config.get("friends.requests_per_hour") or 0)
        if not self.friend_bucket.take(per_hour, 3600.0):
            return
        depth = int(bot_config.get("friends.depth") or 0)
        j = self.candidate(i, depth)
        if j < 0:
            return
        other = int(self.d.uids[j])
        if social.relationship(uid, other) is not None:
            return
        state = social.request_friend(uid, other)
        if state == "pending_out":
            self.stats["requests_sent"] += 1
        elif state == "friends":
            self._count_friend(uid, other)

    def _count_friend(self, a: int, b: int) -> None:
        with self.d.lock:
            for uid in (a, b):
                k = self.d.index_of(uid)
                if k >= 0 and self.d.friends[k] < 65000:
                    self.d.friends[k] += 1

    def _deliver_requests(self, now: int) -> None:
        """Bots answer the friend requests waiting for them."""
        if not bot_config.get("friends.enabled"):
            return
        rows = social.pending_batch(self.pending_cursor, 400)
        if len(rows) < 400:
            self.pending_cursor = 0
        else:
            self.pending_cursor = int(rows[-1]["id"])
        base = float(bot_config.get("friends.accept_chance") or 0) / 100.0
        human_ok = bool(bot_config.get("friends.accept_humans"))
        human_chance = float(bot_config.get("friends.accept_humans_chance") or 0) / 100.0
        follow = float(bot_config.get("friends.follow_chance") or 0) / 100.0
        for row in rows:
            fid = int(row["id"])
            if self.ignored.get(fid, 0) > now:
                continue
            requester = int(row["requester_id"])
            recipient = int(row["user_high"]) if int(row["user_low"]) == requester \
                else int(row["user_low"])
            i = self.d.index_of(recipient)
            if i < 0 or not self._ready(i):
                continue
            # people take a moment to notice a request
            if now - int(row["created_at"]) < self.rng.randint(45, 400):
                continue
            j = self.d.index_of(requester)
            if j >= 0:
                common = personas.shared(self.d.masks[i], self.d.masks[j])
                chance = base * (0.55 + 0.15 * common) * (1.25 - self.d.traits["selective"][i])
            else:
                if not human_ok:
                    continue
                chance = human_chance * (1.15 - self.d.traits["selective"][i] * 0.4)
            if self.d.friends[i] >= self.d.friend_target[i] * 1.4:
                chance *= 0.3
            roll = self.rng.random()
            if roll < chance:
                if social.accept(recipient, requester):
                    self.stats["accepted"] += 1
                    self._count_friend(recipient, requester)
                    if self.rng.random() < follow:
                        social.follow(recipient, requester)
                        self.stats["follows"] += 1
            elif roll > 0.94 and j >= 0:
                social.decline(recipient, requester)
                self.stats["declined"] += 1
            else:
                self.ignored[fid] = now + self.rng.randint(3600, 6 * 3600)
        if len(self.ignored) > 50000:
            self.ignored = {k: v for k, v in self.ignored.items() if v > now}

    def after_live_round(self, i: int, human_ids: List[int], now: int) -> None:
        """A bot leaving a live round may add a person it played with."""
        if not (bot_config.get("friends.enabled") and bot_config.get("friends.befriend_humans")):
            return
        if not human_ids or self.rng.random() > 0.12 * (0.5 + self.d.traits["social"][i]):
            return
        uid = int(self.d.uids[i])
        other = self.rng.choice(human_ids)

        def later():
            try:
                if social.relationship(uid, other) is None:
                    social.request_friend(uid, other)
                    self.stats["requests_sent"] += 1
            except Exception:
                pass
        threading.Timer(self.rng.uniform(20, 240), later).start()

    # ---------------------------------------------------------------- likes
    def _like(self, i: int, uid: int) -> None:
        try:
            friends = social.friend_ids(uid)
        except Exception:
            return
        if not friends:
            return
        self.rng.shuffle(friends)
        if social.like_something(uid, friends[:12]):
            self.stats["likes"] += 1

    # ------------------------------------------------------------- comments
    def _comment_budget(self) -> bool:
        if not llm.client().available():
            return False
        if llm.client().pressure() > 0.6:
            return False
        return self.comment_bucket.take(float(bot_config.get("chatter.max_per_minute") or 0))

    def _pick_wall(self, i: int, uid: int) -> Optional[Tuple[int, str]]:
        """Whose comment section to write in: a friend, or a close associate."""
        friends_only = bool(bot_config.get("chatter.friends_only"))
        depth = int(bot_config.get("chatter.min_shared_tags") or 0)
        try:
            friend_ids = social.friend_ids(uid)
        except Exception:
            friend_ids = []
        choice: Optional[int] = None
        if friend_ids and (friends_only or self.rng.random() < 0.65):
            choice = self.rng.choice(friend_ids)
        elif not friends_only:
            j = self.candidate(i, depth)
            if j >= 0:
                choice = int(self.d.uids[j])
        if choice is None or choice == uid:
            return None
        from ..models import users
        owner = users.get_by_id(choice)
        if owner is None or owner.get("is_banned") or not social.wall_open_to(owner, uid):
            return None
        return choice, owner["username"]

    def _relation(self, i: int, uid: int, other: int, other_name: str) -> str:
        from ..social import friends as friends_model
        if friends_model.are_friends(uid, other):
            return "You and %s are friends." % other_name
        j = self.d.index_of(other)
        if j >= 0:
            common = self.d.masks[i] & self.d.masks[j]
            tags = [t["label"] for t in personas.all_tags()
                    if common & personas.mask_of([t["id"]])]
            if tags:
                return ("You don't know %s well yet, but you have things in "
                        "common: %s." % (other_name, ", ".join(tags[:4]).lower()))
        return "%s is another player." % other_name

    def _comment(self, i: int, uid: int, now: int) -> bool:
        if not self._comment_budget():
            return False
        target = self._pick_wall(i, uid)
        if target is None:
            return True     # nobody suitable right now: try again next interval
        owner_id, owner_name = target
        return self._write_comment(i, uid, owner_id, owner_name, None, llm.P_COMMENT,
                                   "comment")

    def _write_comment(self, i: int, uid: int, owner_id: int, owner_name: str,
                       reply_to: Optional[Dict[str, Any]], priority: int,
                       kind: str) -> bool:
        card = self.d.card(uid)
        log_name = storage.comment_log(owner_name)
        context = int(bot_config.get("chatter.context_comments") or 14)
        state: Dict[str, Any] = {}

        def build():
            wall = social.wall(owner_id, context)
            remembered = storage.tail(uid, card["name"], log_name, context * 2)
            seen = {e.get("id") for e in wall}
            merged = [e for e in remembered if e.get("id") not in seen and e.get("id")]
            merged += wall
            merged.sort(key=lambda e: (e.get("at", 0), e.get("id", 0)))
            state["wall"] = wall
            relation = (self._relation(i, uid, reply_to["uid"], reply_to["who"])
                        if reply_to else self._relation(i, uid, owner_id, owner_name))
            return prompts.comment(card, owner_name, merged[-context * 2:], relation,
                                   reply_to)

        def done(text: Optional[str], error: Optional[str]) -> None:
            names = [e.get("who") for e in state.get("wall", [])]
            text = prompts.tidy(text, "reply" if reply_to else "comment",
                                card["name"], names)
            if not text:
                return
            owner = None
            from ..models import users
            owner = users.get_by_id(owner_id)
            if owner is None or not social.wall_open_to(owner, uid):
                return
            cid = social.comment(uid, owner_id, text)
            if not cid:
                return
            self.stats["replies" if reply_to else "comments"] += 1
            entries = [dict(e, tag="seen") for e in state.get("wall", [])[-6:]]
            entries.append({"id": cid, "at": _now(), "who": card["name"],
                            "text": text, "uid": uid})
            storage.append(uid, card["name"], log_name, _dedupe_log(uid, card["name"],
                                                                    log_name, entries))
            self._remember("comment", card["name"], owner_name, text)
            # if the wall belongs to a bot, it may answer
            self.on_wall_comment(owner_id, uid, card["name"], text, cid, from_bot=True)

        return llm.client().submit(kind, priority, build, done, ttl=1800, bot=uid)

    def on_wall_comment(self, owner_id: int, author_id: int, author_name: str,
                        body: str, comment_id: int, from_bot: bool = False) -> None:
        """Somebody wrote on a profile: if it is a bot's, it may answer."""
        i = self.d.index_of(owner_id)
        if i < 0 or owner_id == author_id:
            return
        if from_bot:
            if not bot_config.get("chatter.enabled"):
                return
            if self.rng.random() > 0.3 * (0.4 + self.d.traits["social"][i]):
                return
        elif not bot_config.get("chatter.reply_to_humans"):
            return
        lo, hi = bot_config.get("chatter.reply_delay_minutes") or [2, 25]
        with self.lock:
            queue = self.pending_wall.setdefault(owner_id, [])
            if len(queue) >= 6:
                queue.pop(0)
            queue.append({"id": comment_id, "uid": author_id, "who": author_name,
                          "text": body, "at": _now(), "bot": from_bot,
                          "due": _now() + int(self.rng.uniform(float(lo), float(hi)) * 60)})

    # ------------------------------------------------------------------ DMs
    def on_dm(self, bot_id: int, sender_id: int, sender_name: str, body: str) -> None:
        i = self.d.index_of(bot_id)
        if i < 0 or not bot_config.get("messages.dm_enabled"):
            return
        card = self.d.card(bot_id)
        now = _now()
        storage.append(bot_id, card["name"], storage.dm_log(sender_name),
                       [{"at": now, "who": sender_name, "text": body}])
        self.momentum.heard(bot_id, sender_id, now, (card["name"], sender_name))
        lo, hi = bot_config.get("messages.dm_delay_seconds") or [20, 180]
        # a conversation with momentum is answered sooner (Dynamic Modifiers)
        faster = self.momentum.speedup(bot_id, sender_id, now)
        due = now + self.rng.uniform(float(lo), float(hi)) * (1.0 - faster)
        if faster:
            self.stats["quickened"] = self.stats.get("quickened", 0) + 1
        with self.lock:
            waiting = self.pending_dm.setdefault(bot_id, {})
            waiting[sender_id] = min(waiting.get(sender_id, due), due)

    def _answer_pending(self, now: int) -> None:
        with self.lock:
            dms = [(bot, other, due) for bot, others in self.pending_dm.items()
                   for other, due in others.items()]
            walls = [(bot, entry) for bot, queue in self.pending_wall.items()
                     for entry in queue]
        for bot, other, due in dms:
            i = self.d.index_of(bot)
            if i < 0:
                self._clear_dm(bot, other)
                continue
            if not self._ready(i) or now < due:
                continue
            # the delay counts from when the bot could first have seen it
            ready_since = max(int(self.d.ready_at[i]), int(self.d.since[i]))
            if now - ready_since < 5:
                continue
            if (bot, other) in self.busy and self.busy[(bot, other)] > now:
                continue
            # one reply in flight per conversation; released the moment it
            # has gone out (or failed), so a quick back-and-forth stays quick
            self.busy[(bot, other)] = now + 120
            if self._reply_dm(i, bot, other):
                self._clear_dm(bot, other)
            else:
                self.busy.pop((bot, other), None)
        for bot, entry in walls:
            i = self.d.index_of(bot)
            if i < 0 or not self._ready(i) or now < entry["due"]:
                continue
            if not entry["bot"] or self._comment_budget():
                priority = llm.P_COMMENT if entry["bot"] else llm.P_REPLY
                self._reply_wall(i, bot, entry, priority)
            with self.lock:
                queue = self.pending_wall.get(bot) or []
                if entry in queue:
                    queue.remove(entry)
                if not queue:
                    self.pending_wall.pop(bot, None)
        if len(self.busy) > 5000:
            self.busy = {k: v for k, v in self.busy.items() if v > now}

    def _clear_dm(self, bot: int, other: int) -> None:
        with self.lock:
            waiting = self.pending_dm.get(bot)
            if waiting:
                waiting.pop(other, None)
                if not waiting:
                    self.pending_dm.pop(bot, None)

    def _reply_wall(self, i: int, bot: int, entry: Dict[str, Any], priority: int) -> None:
        card = self.d.card(bot)
        from ..models import users
        author = users.get_by_id(entry["uid"])
        # usually on its own wall under the comment, sometimes back on theirs
        if author is not None and self.rng.random() < 0.3 and \
                social.wall_open_to(author, bot):
            self._write_comment(i, bot, int(author["id"]), author["username"], entry,
                                priority, "reply" if not entry["bot"] else "comment")
        else:
            self._write_comment(i, bot, bot, card["name"], entry, priority,
                                "reply" if not entry["bot"] else "comment")

    def _reply_dm(self, i: int, bot: int, other: int) -> bool:
        from ..models import users
        other_user = users.get_by_id(other)
        if other_user is None:
            return True
        card = self.d.card(bot)
        other_name = other_user["username"]
        log_name = storage.dm_log(other_name)
        context = int(bot_config.get("messages.dm_context_messages") or 24)

        def build():
            history = storage.tail(bot, card["name"], log_name, context)
            if not history:
                history = [{"at": m["created_at"], "who": m["who"], "text": m["body"]}
                           for m in social.conversation(bot, other, context)]
            relation = self._relation(i, bot, other, other_name)
            return prompts.dm(card, other_name, history, relation)

        def done(text: Optional[str], error: Optional[str]) -> None:
            self.busy.pop((bot, other), None)
            text = prompts.tidy(text, "dm", card["name"], [other_name])
            if not text:
                return
            subject = "Re: hey"
            last = db.query_one("SELECT subject FROM messages WHERE sender_id=? AND"
                                " recipient_id=? ORDER BY id DESC LIMIT 1", (other, bot))
            if last and last["subject"]:
                subject = last["subject"] if last["subject"].lower().startswith("re:") \
                    else "Re: " + last["subject"]
            if social.dm(bot, other_name, text, subject):
                self.momentum.replied(bot, other, _now())
                social.mark_read(bot, other)
                storage.append(bot, card["name"], log_name,
                               [{"at": _now(), "who": card["name"], "text": text}])
                self.stats["dms"] += 1
                self._remember("dm", card["name"], other_name, text)

        # typing takes time too
        return llm.client().submit("dm", llm.P_DM, build, done, ttl=3600, bot=bot)

    # ---------------------------------------------------------------- posts
    def _post(self, i: int, uid: int) -> None:
        if not llm.client().available() or llm.client().pressure() > 0.5:
            return
        card = self.d.card(uid)
        world, _inst = self.d.bot_place(uid)
        doing = ""
        if world:
            doing = "playing %s right now" % bot_config.WORLD_LABELS.get(world, world)

        def build():
            earlier = [e.get("text", "") for e in storage.tail(uid, card["name"],
                                                               storage.POSTS_LOG, 8)]
            earlier = earlier or social.recent_posts(uid, 8)
            return prompts.post(card, earlier, doing)

        def done(text: Optional[str], error: Optional[str]) -> None:
            text = prompts.tidy(text, "post", card["name"])
            if not text:
                return
            if social.post(uid, text):
                storage.append(uid, card["name"], storage.POSTS_LOG,
                               [{"at": _now(), "who": card["name"], "text": text}])
                self.stats["posts"] += 1
                self._remember("post", card["name"], "", text)

        llm.client().submit("post", llm.P_POST, build, done, ttl=3600, bot=uid)

    # ---------------------------------------------------------------- misc
    def _remember(self, kind: str, who: str, where: str, text: str) -> None:
        with self.lock:
            self.recent.append({"at": _now(), "kind": kind, "who": who,
                                "where": where, "text": text[:200]})
            del self.recent[:-40]

    def snapshot(self) -> Dict[str, Any]:
        with self.lock:
            return {"stats": dict(self.stats),
                    "momentum": self.momentum.snapshot(_now()),
                    "pending_dms": sum(len(v) for v in self.pending_dm.values()),
                    "pending_walls": sum(len(v) for v in self.pending_wall.values()),
                    "recent": list(self.recent[-20:])}

    def pending_for(self, uid: int) -> Dict[str, Any]:
        with self.lock:
            return {"dms": len(self.pending_dm.get(uid, {})),
                    "walls": len(self.pending_wall.get(uid, []))}


def _dedupe_log(uid: int, name: str, log_name: str,
                entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Only the entries this bot's log does not have yet."""
    known = {e.get("id") for e in storage.tail(uid, name, log_name, 60) if e.get("id")}
    return [e for e in entries if not e.get("id") or e.get("id") not in known]
