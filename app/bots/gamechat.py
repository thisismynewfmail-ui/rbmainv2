"""In-game chat between bots and the people in a round.

The game host only reports chat from rounds a real player is in -- nobody
reads the chat of a sleeping instance.  Each report carries the new lines, the
events that just happened (a flag stolen, a checkpoint, a spree), a snapshot
of the round everybody can see (score, flags or cart, clock) and, per bot, its
own view (team, job, kills, whether it has the flag).  From that the relay
decides who, if anyone, speaks:

* a bot addressed by name nearly always answers;
* otherwise a chatty bot might -- more likely while the player keeps talking
  (**chat heat**, a Dynamic Modifier that fades once they go quiet), and most
  likely the bot they were just talking with;
* a bot's own line can draw a reply from another bot (**bots answer each
  other**), less likely with every bot-only line in a row, never past a
  limit, so the chat is a conversation without becoming a bot loop;
* a **speech event** gives the bots on either side of it something to say,
  told from their own side: "they have our flag" and "nice grab" are the same
  event; a round stays buzzing for a while after one;
* never more than the per-instance budget a minute.

Every line is written by the language model from the round's chat, with the
round's state underneath it as background the bot may or may not bring up,
and appears after the time it would take to type.  When the model is down,
speech events fall back to short stock lines.  Every bot that takes part gets
the lines it saw and the line it said appended to its own "In-Game Chat In
World ..." log.

Quick reactions -- "rip", "nice", "gottem" -- never come here: the host types
those itself, so a round stays lively however busy the model is.
"""
from __future__ import annotations

import random
import re
import threading
import time
from collections import deque
from typing import Any, Dict, List, Optional, Tuple

from . import config as bot_config
from . import llm, modifiers, prompts, speech, storage


def _now() -> float:
    return time.time()


def _norm(text: str) -> str:
    return "".join(c for c in (text or "").lower() if c.isalnum())


class Room:
    __slots__ = ("world", "inst", "lines", "events", "bots", "humans",
                 "sent", "logged", "last_speaker", "touched", "state", "heat",
                 "chain", "buzz_at", "event_at", "speech_log", "burst_at")

    def __init__(self, world: str, inst: int):
        self.world = world
        self.inst = inst
        self.lines: deque = deque(maxlen=120)
        self.events: deque = deque(maxlen=24)
        self.bots: Dict[int, Dict[str, Any]] = {}
        self.humans: Dict[int, str] = {}
        self.sent: deque = deque(maxlen=60)          # times bots spoke
        self.logged: Dict[int, int] = {}             # bot uid -> lines logged
        self.last_speaker: Dict[int, float] = {}
        self.touched = _now()
        self.state: Dict[str, Any] = {}              # what everyone can see
        self.heat = modifiers.Heat()                 # the players' chat heat
        self.chain = 0                               # bot lines since a person spoke
        self.buzz_at = 0.0                           # last speech event
        self.event_at: Dict[str, float] = {}         # event kind -> last reaction
        self.speech_log: deque = deque(maxlen=20)
        self.burst_at = 0.0                          # last time bots reacted to one


class Relay:
    def __init__(self, director):
        self.d = director
        self.rng = random.Random()
        self.lock = threading.RLock()
        self.rooms: Dict[Tuple[str, int], Room] = {}
        self.stats = {"heard": 0, "answered": 0, "skipped": 0, "budget": 0,
                      "events": 0, "reactions": 0, "bot_replies": 0,
                      "second_voices": 0, "canned": 0, "repeats": 0}
        self.recent: deque = deque(maxlen=30)
        self.event_log: deque = deque(maxlen=40)
        self.counter = 0

    # ------------------------------------------------------------ reports
    def on_report(self, world: str, report: Dict[str, Any]) -> None:
        inst = int(report.get("inst", 0))
        now = _now()
        with self.lock:
            room = self.rooms.get((world, inst))
            if room is None:
                room = self.rooms[(world, inst)] = Room(world, inst)
            room.touched = now
            room.bots = {int(b["uid"]): b for b in report.get("bots", []) or []}
            room.humans = {int(h["uid"]): h.get("name", "") for h in report.get("humans", []) or []}
            if isinstance(report.get("state"), dict):
                room.state = report["state"]
            for event in report.get("events", []) or []:
                room.events.append(str(event)[:120])
            fresh = []
            for line in report.get("lines", []) or []:
                self.counter += 1
                entry = {"n": self.counter, "at": line.get("at", now),
                         "who": str(line.get("who", ""))[:24],
                         "uid": int(line.get("uid", 0) or 0),
                         "text": str(line.get("text", ""))[:160],
                         "team": line.get("team", ""), "bot": bool(line.get("bot"))}
                room.lines.append(entry)
                fresh.append(entry)
                if entry["bot"]:
                    room.chain += 1
                elif entry["uid"]:
                    room.chain = 0
                    room.heat.heard(entry["uid"], now)
            happened = [e for e in report.get("speech", []) or [] if isinstance(e, dict)]
        if not bot_config.get("messages.ingame_chat") or not self.d.enabled():
            return
        for event in happened:
            self._on_event(room, event)
        for entry in fresh:
            if not entry["uid"]:
                continue
            if entry["bot"]:
                self._consider_bot_line(room, entry)
            else:
                self.stats["heard"] += 1
                self._consider(room, entry)

    def _addressed(self, room: Room, text: str, besides: int = 0) -> Optional[int]:
        lower = text.lower()
        words = set(re.findall(r"[a-z0-9_]+", lower))
        for uid, bot in room.bots.items():
            if uid == besides:
                continue
            name = str(bot.get("name", "")).lower()
            if not name:
                continue
            if name in lower or (len(name) >= 5 and name[:5] in words) or \
                    any(len(w) >= 4 and name.startswith(w) for w in words):
                return uid
        return None

    def _budget_ok(self, room: Room) -> bool:
        limit = int(bot_config.get("messages.chat_per_minute") or 0)
        cutoff = _now() - 60
        while room.sent and room.sent[0] < cutoff:
            room.sent.popleft()
        return len(room.sent) < limit

    def _buzz(self, room: Room, now: float) -> float:
        """1.0 normally; more for a while after a speech event, fading out."""
        if not bot_config.get("speech.enabled") or not room.buzz_at:
            return 1.0
        seconds = float(bot_config.get("speech.buzz_seconds") or 0)
        boost = float(bot_config.get("speech.buzz_boost") or 0) / 100.0
        return 1.0 + boost * modifiers.fade(now - room.buzz_at, seconds)

    def _weights(self, room: Room, now: float, besides: int = 0) -> List[Tuple[int, float]]:
        out = []
        for uid, bot in room.bots.items():
            if uid == besides:
                continue
            chatty = float((bot.get("traits") or {}).get("chatty", 0.4))
            recent = 1.8 if now - room.last_speaker.get(uid, 0) < 45 else 1.0
            out.append((uid, chatty * recent))
        return out

    # ------------------------------------------------- a real player spoke
    def _consider(self, room: Room, entry: Dict[str, Any]) -> None:
        if not room.bots:
            return
        now = _now()
        human = entry["uid"]
        target = self._addressed(room, entry["text"])
        chance = float(bot_config.get("messages.chat_reply_chance") or 0) / 100.0
        heat = room.heat.multiplier(now, human)
        buzz = self._buzz(room, now)
        if target is not None:
            if self.rng.random() > 0.92:
                return
            uid = target
        else:
            chattiest = self._weights(room, now)
            if not chattiest:
                return
            average = sum(w for _u, w in chattiest) / len(chattiest)
            # a question or a greeting pulls an answer more than a statement
            pull = 1.4 if ("?" in entry["text"] or re.search(
                r"\b(hi|hey|hello|yo|sup|gg|anyone|who)\b", entry["text"].lower())) else 0.8
            odds = min(0.95, chance * min(1.2, average * 1.6) * pull * heat * buzz)
            if self.rng.random() > odds:
                self.stats["skipped"] += 1
                return
            uid = self._continuing(room, human, now)
            if uid is None:
                uid = self.rng.choices([u for u, _w in chattiest],
                                       [max(0.02, w) for _u, w in chattiest])[0]
        if not self._budget_ok(room):
            self.stats["budget"] += 1
            return
        room.sent.append(now)
        room.heat.answered(human, uid, now)
        self._speak(room, uid, trigger=entry)
        # a hot chat pulls in a second voice now and then
        if bot_config.get("modifiers.chat_enabled") and room.heat.level(now) >= 2.0:
            second = float(bot_config.get("modifiers.chat_second_voice") or 0) / 100.0
            if self.rng.random() < second * min(1.5, buzz):
                others = self._weights(room, now, besides=uid)
                if others and self._budget_ok(room):
                    other = self.rng.choices([u for u, _w in others],
                                             [max(0.02, w) for _u, w in others])[0]
                    room.sent.append(now)
                    self.stats["second_voices"] += 1
                    self._speak(room, other, trigger=entry, extra_delay=self.rng.uniform(2.0, 6.0))

    def _continuing(self, room: Room, human: int, now: float) -> Optional[int]:
        """The bot this player was just talking with, if it keeps the thread."""
        if not bot_config.get("modifiers.chat_enabled"):
            return None
        partner, warmth = room.heat.partner_of(human, now)
        if partner is None or partner not in room.bots:
            return None
        keep = float(bot_config.get("modifiers.chat_partner") or 0) / 100.0
        return partner if self.rng.random() < keep * warmth else None

    # --------------------------------------------------------- a bot spoke
    def _consider_bot_line(self, room: Room, entry: Dict[str, Any]) -> None:
        """Another bot might answer -- a conversation, within limits."""
        if not bot_config.get("modifiers.bots_talk") or not room.humans:
            return
        longest = int(bot_config.get("modifiers.bot_chain_max") or 0)
        if room.chain > longest:
            return
        now = _now()
        speaker = entry["uid"]
        base = float(bot_config.get("modifiers.bot_reply_chance") or 0) / 100.0
        fade = 1.0 - float(bot_config.get("modifiers.bot_chain_fade") or 0) / 100.0
        odds = base * (fade ** max(0, room.chain - 1)) * self._buzz(room, now)
        target = self._addressed(room, entry["text"], besides=speaker)
        if target is not None:
            odds = max(odds, 0.7 * (fade ** max(0, room.chain - 1)))
        if self.rng.random() > min(0.9, odds):
            return
        if target is None:
            others = self._weights(room, now, besides=speaker)
            if not others:
                return
            target = self.rng.choices([u for u, _w in others],
                                      [max(0.02, w) for _u, w in others])[0]
        if not self._budget_ok(room):
            self.stats["budget"] += 1
            return
        room.sent.append(now)
        self.stats["bot_replies"] += 1
        self._speak(room, target, trigger=entry, extra_delay=self.rng.uniform(0.5, 2.5))

    # ------------------------------------------------------ speech events
    def _on_event(self, room: Room, event: Dict[str, Any]) -> None:
        if not bot_config.get("speech.enabled") or not room.bots:
            return
        kind = str(event.get("kind") or "")
        if not speech.applies(kind, room.world):
            return
        now = _now()
        self.stats["events"] += 1
        room.buzz_at = now
        chances = bot_config.get("speech.chances") or speech.DEFAULT_CHANCES
        chance = float(chances.get(kind, 0) or 0) / 100.0
        if chance > 0:
            chance = min(1.0, chance * speech.importance(event))
            if now - room.burst_at < 4.0:
                # one moment, several notifications (the flag is taken and the
                # team is locked down): people react to the moment once
                chance *= 0.3
        cooldown = float(bot_config.get("speech.cooldown_seconds") or 0)
        record = {"at": int(now), "world": room.world, "inst": room.inst, "kind": kind,
                  "label": speech.KINDS_BY_ID[kind].label, "voices": []}
        room.speech_log.append(record)
        self.event_log.append(record)
        if chance <= 0 or now - room.event_at.get(kind, 0.0) < cooldown:
            record["outcome"] = "cooling down" if chance > 0 else "off"
            return
        # everybody sees it from their own side; that decides who is likeliest
        # to say something and what they are told
        sides: Dict[int, Tuple[str, str]] = {}
        weights: List[Tuple[int, float]] = []
        for uid, bot in room.bots.items():
            text, relation = speech.describe(event, str(bot.get("name", "")),
                                             str(bot.get("team", "")))
            if not text:
                continue
            chatty = float((bot.get("traits") or {}).get("chatty", 0.4))
            me = bot.get("me") or {}
            if me.get("alive") is False and kind not in ("round_end", "flag_capture"):
                chatty *= 0.8           # on the respawn screen, typing
            sides[uid] = (text, relation)
            weights.append((uid, max(0.02, speech.voice_weight(event, relation) * (0.3 + chatty))))
        if not weights or self.rng.random() >= chance:
            record["outcome"] = "nobody reacted"
            return
        room.event_at[kind] = now
        room.burst_at = now
        most = max(1, int(bot_config.get("speech.max_voices") or 1))
        follow = float(bot_config.get("speech.follow_chance") or 0) / 100.0
        picked: List[int] = []
        pool = list(weights)
        while pool and len(picked) < most:
            if picked and self.rng.random() >= follow:
                break
            uid = self.rng.choices([u for u, _w in pool], [w for _u, w in pool])[0]
            picked.append(uid)
            pool = [(u, w) for u, w in pool if u != uid]
        delay = self.rng.uniform(0.3, 1.5)
        for uid in picked:
            if not self._budget_ok(room):
                self.stats["budget"] += 1
                break
            room.sent.append(now)
            text, relation = sides[uid]
            self.stats["reactions"] += 1
            record["voices"].append(str(room.bots[uid].get("name", "")))
            self._speak(room, uid, event=event, event_text=text, relation=relation,
                        extra_delay=delay)
            delay += self.rng.uniform(1.5, 4.5)
        record["outcome"] = "%d reacted" % len(record["voices"]) if record["voices"] else "over budget"

    # -------------------------------------------------------------- lines
    def _speak(self, room: Room, uid: int, trigger: Optional[Dict[str, Any]] = None,
               event: Optional[Dict[str, Any]] = None, event_text: str = "",
               relation: str = "", extra_delay: float = 0.0) -> None:
        card = self.d.card(uid)
        world_name = bot_config.WORLD_LABELS.get(room.world, room.world)
        bot = room.bots.get(uid) or {}
        team = bot.get("team", "")
        addressed = ""
        if trigger is not None and self._addressed(room, trigger["text"],
                                                   besides=trigger.get("uid", 0)) == uid:
            addressed = trigger["who"]
        snapshot: Dict[str, Any] = {}

        def build():
            with self.lock:
                lines = list(room.lines)
                events = list(room.events)
                state = dict(room.state)
                me = dict((room.bots.get(uid) or {}).get("me") or {})
            snapshot["lines"] = lines
            return prompts.chat(card, world_name, team, lines, events, addressed,
                                state=state, me=me, event=event_text)

        def done(text: Optional[str], error: Optional[str]) -> None:
            text = prompts.tidy(text, "chat", card["name"],
                                [l["who"] for l in snapshot.get("lines", [])])
            if not text:
                return
            # a person does not say the same line twice in a row: models do
            said_before = {_norm(l["text"]) for l in snapshot.get("lines", [])[-24:]
                           if l["who"] == card["name"]}
            if _norm(text) in said_before:
                self.stats["repeats"] += 1
                return
            self._deliver(room, uid, card, text, extra_delay, snapshot.get("lines", []),
                          trigger["who"] if trigger else (event or {}).get("kind", ""))

        if llm.client().submit("chat", llm.P_CHAT, build, done, ttl=25.0, bot=uid):
            return
        # the model is down or swamped: an event still gets a stock reaction
        if event is not None and bot_config.get("speech.canned_fallback"):
            line = speech.canned(event, relation, self.rng)
            if line:
                self.stats["canned"] += 1
                self._deliver(room, uid, card, _styled(line, card, self.rng), extra_delay,
                              list(room.lines), event.get("kind", ""))

    def _deliver(self, room: Room, uid: int, card: Dict[str, Any], text: str,
                 extra_delay: float, lines: List[Dict[str, Any]], to: str) -> None:
        typing = len(text) / max(1.0, float(bot_config.get("messages.typing_cps") or 7))
        delay = round(min(14.0, extra_delay + 0.6 + typing * self.rng.uniform(0.7, 1.2)), 2)
        self._send(room, uid, text, delay)
        self._log(room, uid, card["name"], lines, text)
        room.last_speaker[uid] = _now()
        self.stats["answered"] += 1
        self.recent.append({"at": int(_now()), "who": card["name"],
                            "world": bot_config.WORLD_LABELS.get(room.world, room.world),
                            "text": text, "to": to})

    def _send(self, room: Room, uid: int, text: str, delay: float) -> None:
        from ..game import registry
        body = {"action": "bot_chat", "inst": room.inst, "uid": uid,
                "text": text, "delay": delay}

        def push():
            answer = registry.control(room.world, body, timeout=3.0)
            if not answer or not answer.get("ok"):
                # fall back to the heartbeat channel
                with self.d.lock:
                    self.d.ops[room.world].append({"op": "chat", "uid": uid,
                                                   "inst": room.inst, "text": text,
                                                   "delay": 0.2})
        threading.Thread(target=push, daemon=True, name="bots-chat").start()

    def _log(self, room: Room, uid: int, name: str, lines: List[Dict[str, Any]],
             said: str) -> None:
        world_name = bot_config.WORLD_LABELS.get(room.world, room.world)
        already = room.logged.get(uid, 0)
        seen = [{"at": int(l["at"]), "who": l["who"], "text": l["text"],
                 "inst": room.inst} for l in lines if l["n"] > already]
        seen.append({"at": int(_now()), "who": name, "text": said, "inst": room.inst})
        if lines:
            room.logged[uid] = lines[-1]["n"]
        storage.append(uid, name, storage.chat_log(world_name), seen[-40:])

    # --------------------------------------------------------------- tick
    def tick(self, t: float) -> None:
        with self.lock:
            stale = [key for key, room in self.rooms.items() if t - room.touched > 600]
            for key in stale:
                self.rooms.pop(key, None)

    def snapshot(self) -> Dict[str, Any]:
        now = _now()
        with self.lock:
            heat = modifiers.summarise_heat(
                [(r.world, r.inst, r.heat, r.humans) for r in self.rooms.values()], now)
            for row in heat:
                room = self.rooms.get((row["world"], row["inst"]))
                row["buzz"] = round(self._buzz(room, now), 2) if room else 1.0
                row["chain"] = room.chain if room else 0
                row["world_name"] = bot_config.WORLD_LABELS.get(row["world"], row["world"])
            return {"rooms": len(self.rooms), "stats": dict(self.stats),
                    "recent": list(self.recent), "heat": heat,
                    "events": list(self.event_log)[-25:]}


def _styled(line: str, card: Dict[str, Any], rng: random.Random) -> str:
    try:
        from ..game.bots.brain import styled
        return styled(line, card.get("traits") or {}, rng)
    except Exception:
        return line
