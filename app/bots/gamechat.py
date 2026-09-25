"""In-game chat between bots and the people in a round.

The game host only reports chat from rounds a real player is in -- nobody
reads the chat of a sleeping instance.  Each report carries the new lines, a
few words on what just happened (kills, captures, the cart) and who is in the
round.  From that the relay decides who, if anyone, answers:

* a bot addressed by name nearly always answers;
* otherwise a chatty bot might, more likely one who was just talking;
* never more than the per-instance budget a minute, so a round never turns
  into bots talking over each other.

The answer is written by the language model from the round's own chat, sits
behind a delay that is the time it would take to type, and is sent straight to
the host.  Every bot that takes part gets the lines it saw and the line it
said appended to its own "In-Game Chat In World ..." log.

Quick reactions -- "gg", "nice", "rip" -- never come here: the host types those
itself, so a round stays lively however busy the model is.
"""
from __future__ import annotations

import random
import re
import threading
import time
from collections import deque
from typing import Any, Dict, List, Optional, Tuple

from . import config as bot_config
from . import llm, prompts, storage


def _now() -> float:
    return time.time()


class Room:
    __slots__ = ("world", "inst", "lines", "events", "bots", "humans",
                 "sent", "logged", "last_speaker", "touched")

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


class Relay:
    def __init__(self, director):
        self.d = director
        self.rng = random.Random()
        self.lock = threading.RLock()
        self.rooms: Dict[Tuple[str, int], Room] = {}
        self.stats = {"heard": 0, "answered": 0, "skipped": 0, "budget": 0}
        self.recent: deque = deque(maxlen=30)
        self.counter = 0

    # ------------------------------------------------------------ reports
    def on_report(self, world: str, report: Dict[str, Any]) -> None:
        inst = int(report.get("inst", 0))
        with self.lock:
            room = self.rooms.get((world, inst))
            if room is None:
                room = self.rooms[(world, inst)] = Room(world, inst)
            room.touched = _now()
            room.bots = {int(b["uid"]): b for b in report.get("bots", []) or []}
            room.humans = {int(h["uid"]): h.get("name", "") for h in report.get("humans", []) or []}
            for event in report.get("events", []) or []:
                room.events.append(str(event)[:120])
            fresh = []
            for line in report.get("lines", []) or []:
                self.counter += 1
                entry = {"n": self.counter, "at": line.get("at", _now()),
                         "who": str(line.get("who", ""))[:24],
                         "uid": int(line.get("uid", 0) or 0),
                         "text": str(line.get("text", ""))[:160],
                         "team": line.get("team", ""), "bot": bool(line.get("bot"))}
                room.lines.append(entry)
                fresh.append(entry)
        if not bot_config.get("messages.ingame_chat") or not self.d.enabled():
            return
        for entry in fresh:
            if entry["bot"] or not entry["uid"]:
                continue
            self.stats["heard"] += 1
            self._consider(room, entry)

    def _addressed(self, room: Room, text: str) -> Optional[int]:
        lower = text.lower()
        words = set(re.findall(r"[a-z0-9_]+", lower))
        for uid, bot in room.bots.items():
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

    def _consider(self, room: Room, entry: Dict[str, Any]) -> None:
        if not room.bots:
            return
        target = self._addressed(room, entry["text"])
        chance = float(bot_config.get("messages.chat_reply_chance") or 0) / 100.0
        if target is not None:
            if self.rng.random() > 0.92:
                return
            uid = target
        else:
            chattiest = []
            now = _now()
            for uid, bot in room.bots.items():
                chatty = float((bot.get("traits") or {}).get("chatty", 0.4))
                recent = 1.8 if now - room.last_speaker.get(uid, 0) < 45 else 1.0
                chattiest.append((uid, chatty * recent))
            if not chattiest:
                return
            average = sum(w for _u, w in chattiest) / len(chattiest)
            # a question or a greeting pulls an answer more than a statement
            pull = 1.4 if ("?" in entry["text"] or re.search(
                r"\b(hi|hey|hello|yo|sup|gg|anyone|who)\b", entry["text"].lower())) else 0.8
            if self.rng.random() > chance * min(1.2, average * 1.6) * pull:
                self.stats["skipped"] += 1
                return
            uid = self.rng.choices([u for u, _w in chattiest],
                                   [max(0.02, w) for _u, w in chattiest])[0]
        if not self._budget_ok(room):
            self.stats["budget"] += 1
            return
        room.sent.append(_now())
        self._answer(room, uid, entry)

    # ------------------------------------------------------------ answers
    def _answer(self, room: Room, uid: int, trigger: Dict[str, Any]) -> None:
        card = self.d.card(uid)
        world_name = bot_config.WORLD_LABELS.get(room.world, room.world)
        bot = room.bots.get(uid) or {}
        team = bot.get("team", "")
        addressed = trigger["who"] if self._addressed(room, trigger["text"]) == uid else ""
        snapshot: Dict[str, Any] = {}

        def build():
            with self.lock:
                lines = list(room.lines)
                events = list(room.events)
            snapshot["lines"] = lines
            log = [{"who": l["who"], "text": l["text"]} for l in lines]
            return prompts.chat(card, world_name, team, log, events, addressed)

        def done(text: Optional[str], error: Optional[str]) -> None:
            text = prompts.tidy(text, "chat", card["name"],
                                [l["who"] for l in snapshot.get("lines", [])])
            if not text:
                return
            typing = len(text) / max(1.0, float(bot_config.get("messages.typing_cps") or 7))
            delay = round(min(12.0, 0.6 + typing * self.rng.uniform(0.7, 1.2)), 2)
            self._send(room, uid, text, delay)
            self._log(room, uid, card["name"], snapshot.get("lines", []), text)
            room.last_speaker[uid] = _now()
            self.stats["answered"] += 1
            self.recent.append({"at": int(_now()), "who": card["name"],
                                "world": world_name, "text": text,
                                "to": trigger["who"]})

        llm.client().submit("chat", llm.P_CHAT, build, done, ttl=25.0, bot=uid)

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
        with self.lock:
            return {"rooms": len(self.rooms), "stats": dict(self.stats),
                    "recent": list(self.recent)}
