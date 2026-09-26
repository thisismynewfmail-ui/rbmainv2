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

**One conversation per round.**  Each live round has a single chat session:
it starts when the first real player arrives and ends -- and is thrown away --
when the last one leaves.  Everything in it sits in one transcript in the
order it happened: public chat, the team chat a bot's own team can see, the
bots' quick reactions, kills a real player was part of, flags, joins and the
rest of what the round announces.  Every bot reads that same transcript, and
a line a bot has decided to say goes into it at once (before it has finished
"typing"), so the next bot to speak knows it is coming and nobody answers the
same thing twice.  Bots also speak up on their own now and then while they
play, so the chat is a conversation rather than answers to the player.

Every line is written by the language model from that transcript, with the
round's state underneath it as background the bot may or may not bring up,
and appears after the time it would take to type.  When the model is down,
speech events fall back to short stock lines.  Every bot that takes part gets
the lines it saw and the line it said appended to its own "In-Game Chat In
World ..." log on disk, as a record; the session itself does not outlive the
round's players.

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
    """One live round's chat session."""

    __slots__ = ("world", "inst", "lines", "events", "bots", "humans",
                 "sent", "logged", "last_speaker", "touched", "state", "heat",
                 "chain", "buzz_at", "event_at", "speech_log", "burst_at",
                 "session", "started", "pending", "next_own", "last_line_at",
                 "unhosted_since")

    def __init__(self, world: str, inst: int, session: str = ""):
        self.world = world
        self.inst = inst
        self.session = session
        self.started = _now()
        self.lines: deque = deque(maxlen=200)       # the session's transcript
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
        self.pending: Dict[Tuple[int, str], Dict[str, Any]] = {}  # said, not yet seen back
        self.next_own = 0.0                          # when a bot next speaks up unasked
        self.last_line_at = 0.0
        self.unhosted_since = 0.0


class Relay:
    def __init__(self, director):
        self.d = director
        self.rng = random.Random()
        self.lock = threading.RLock()
        self.rooms: Dict[Tuple[str, int], Room] = {}
        self.stats = {"heard": 0, "answered": 0, "skipped": 0, "budget": 0,
                      "events": 0, "reactions": 0, "bot_replies": 0,
                      "second_voices": 0, "canned": 0, "repeats": 0,
                      "own_lines": 0, "sessions": 0, "team_replies": 0}
        self.recent: deque = deque(maxlen=30)
        self.event_log: deque = deque(maxlen=40)
        self.counter = 0

    # ------------------------------------------------------------ reports
    def on_report(self, world: str, report: Dict[str, Any]) -> None:
        inst = int(report.get("inst", 0))
        now = _now()
        session = str(report.get("session") or "")
        with self.lock:
            if report.get("ended"):
                # the last real player left: the conversation goes with them
                room = self.rooms.get((world, inst))
                if room is not None and (not session or room.session in ("", session)):
                    self.rooms.pop((world, inst), None)
                return
            room = self.rooms.get((world, inst))
            if room is not None and session and room.session and room.session != session:
                room = None                 # a new group of players: a fresh start
            if room is None:
                room = self.rooms[(world, inst)] = Room(world, inst, session)
                self.stats["sessions"] += 1
            room.session = room.session or session
            room.touched = now
            room.unhosted_since = 0.0
            room.bots = {int(b["uid"]): b for b in report.get("bots", []) or []}
            room.humans = {int(h["uid"]): h.get("name", "") for h in report.get("humans", []) or []}
            if isinstance(report.get("state"), dict):
                room.state = report["state"]
            incoming: List[Dict[str, Any]] = []
            for event in report.get("events", []) or []:
                if isinstance(event, dict):
                    text, at = str(event.get("text", "")), float(event.get("at", now) or now)
                else:
                    text, at = str(event), now
                if text:
                    incoming.append({"at": at, "who": "", "uid": 0, "text": text[:120],
                                     "team": "", "bot": False, "kind": "event"})
            for line in report.get("lines", []) or []:
                incoming.append({"at": float(line.get("at", now) or now),
                                 "who": str(line.get("who", ""))[:24],
                                 "uid": int(line.get("uid", 0) or 0),
                                 "text": str(line.get("text", ""))[:160],
                                 "team": line.get("team", ""), "bot": bool(line.get("bot")),
                                 "kind": "team" if line.get("team_only") else "chat"})
            incoming.sort(key=lambda e: e["at"])
            fresh = []
            for entry in incoming:
                if entry["kind"] == "event":
                    self._append(room, entry)
                    continue
                if entry["bot"]:
                    said = room.pending.pop((entry["uid"], _norm(entry["text"])), None)
                    if said is not None:
                        # already in the transcript since the bot decided on it
                        said["pending"] = False
                        said["at"] = entry["at"]
                        entry = said
                    else:
                        self._append(room, entry)
                    room.chain += 1
                else:
                    self._append(room, entry)
                    if entry["uid"]:
                        room.chain = 0
                        room.heat.heard(entry["uid"], now)
                room.last_line_at = now
                fresh.append(entry)
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

    def _append(self, room: Room, entry: Dict[str, Any]) -> Dict[str, Any]:
        self.counter += 1
        entry["n"] = self.counter
        room.lines.append(entry)
        return entry

    def _visible(self, room: Room, uid: int) -> List[Dict[str, Any]]:
        """The transcript as one bot sees it: the other team's team chat is not
        on its screen."""
        team = str((room.bots.get(uid) or {}).get("team", ""))
        return [l for l in room.lines if l.get("kind") != "team" or l.get("team") == team]

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
        if entry.get("kind") == "team":
            self._consider_team(room, entry)
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

    def _consider_team(self, room: Room, entry: Dict[str, Any]) -> None:
        """Team chat: only the player's own team sees it, so only they answer,
        and they answer in team chat."""
        if not bot_config.get("messages.team_chat"):
            return
        now = _now()
        mates = [(u, w) for u, w in self._weights(room, now, besides=entry["uid"])
                 if (room.bots.get(u) or {}).get("team") == entry.get("team")]
        if not mates:
            return
        target = self._addressed(room, entry["text"])
        if target is None or all(u != target for u, _w in mates):
            chance = float(bot_config.get("messages.chat_reply_chance") or 0) / 100.0
            # a teammate asking something on team chat is harder to ignore
            odds = min(0.95, chance * 1.3 * room.heat.multiplier(now, entry["uid"]))
            if self.rng.random() > odds:
                self.stats["skipped"] += 1
                return
            target = self.rng.choices([u for u, _w in mates], [max(0.02, w) for _u, w in mates])[0]
        if not self._budget_ok(room):
            self.stats["budget"] += 1
            return
        room.sent.append(now)
        room.heat.answered(entry["uid"], target, now)
        self.stats["team_replies"] += 1
        self._speak(room, target, trigger=entry, team_chat=True)

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
        team_line = entry.get("kind") == "team"
        if target is None:
            others = self._weights(room, now, besides=speaker)
            if team_line:
                others = [(u, w) for u, w in others
                          if (room.bots.get(u) or {}).get("team") == entry.get("team")]
            if not others:
                return
            target = self.rng.choices([u for u, _w in others],
                                      [max(0.02, w) for _u, w in others])[0]
        elif team_line and (room.bots.get(target) or {}).get("team") != entry.get("team"):
            return
        if not self._budget_ok(room):
            self.stats["budget"] += 1
            return
        room.sent.append(now)
        self.stats["bot_replies"] += 1
        self._speak(room, target, trigger=entry, extra_delay=self.rng.uniform(0.5, 2.5),
                    team_chat=team_line)

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
               relation: str = "", extra_delay: float = 0.0, team_chat: bool = False,
               own: bool = False) -> None:
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
                lines = self._visible(room, uid)
                state = dict(room.state)
                me = dict((room.bots.get(uid) or {}).get("me") or {})
                roster = [(str(b.get("name", "")), str(b.get("team", "")))
                          for b in room.bots.values() if int(b.get("uid", 0)) != uid]
                roster += [(name, "") for name in room.humans.values()]
            snapshot["lines"] = lines
            return prompts.chat(card, world_name, team, lines, [], addressed,
                                state=state, me=me, event=event_text,
                                team_chat=team_chat, own=own, roster=roster)

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
            to = trigger["who"] if trigger else ((event or {}).get("kind", "") or
                                                 ("unprompted" if own else ""))
            self._deliver(room, uid, card, text, extra_delay, snapshot.get("lines", []),
                          to, team_chat)

        if llm.client().submit("chat", llm.P_CHAT, build, done, ttl=25.0, bot=uid):
            return
        # the model is down or swamped: an event still gets a stock reaction
        if event is not None and bot_config.get("speech.canned_fallback"):
            line = speech.canned(event, relation, self.rng)
            if line:
                self.stats["canned"] += 1
                self._deliver(room, uid, card, _styled(line, card, self.rng), extra_delay,
                              self._visible(room, uid), event.get("kind", ""))

    def _deliver(self, room: Room, uid: int, card: Dict[str, Any], text: str,
                 extra_delay: float, lines: List[Dict[str, Any]], to: str,
                 team_chat: bool = False) -> None:
        typing = len(text) / max(1.0, float(bot_config.get("messages.typing_cps") or 7))
        delay = round(min(14.0, extra_delay + 0.6 + typing * self.rng.uniform(0.7, 1.2)), 2)
        with self.lock:
            if self.rooms.get((room.world, room.inst)) is not room:
                return              # the session ended while the model was writing
            bot = room.bots.get(uid) or {}
            # into the transcript straight away: the next bot to speak knows
            # this is coming and does not say the same thing
            said = self._append(room, {"at": _now() + delay, "who": card["name"], "uid": uid,
                                       "text": text, "team": bot.get("team", ""), "bot": True,
                                       "kind": "team" if team_chat else "chat",
                                       "pending": True})
            room.pending[(uid, _norm(text))] = said
            room.last_line_at = _now()
        self._send(room, uid, text, delay, team_chat)
        self._log(room, uid, card["name"], lines, text)
        room.last_speaker[uid] = _now()
        self.stats["answered"] += 1
        self.recent.append({"at": int(_now()), "who": card["name"],
                            "world": bot_config.WORLD_LABELS.get(room.world, room.world),
                            "text": text, "to": to})

    def _send(self, room: Room, uid: int, text: str, delay: float, team: bool = False) -> None:
        from ..game import registry
        body = {"action": "bot_chat", "inst": room.inst, "uid": uid,
                "text": text, "delay": delay, "team": bool(team)}

        def push():
            answer = registry.control(room.world, body, timeout=3.0)
            if not answer or not answer.get("ok"):
                # fall back to the heartbeat channel
                with self.d.lock:
                    self.d.ops[room.world].append({"op": "chat", "uid": uid,
                                                   "inst": room.inst, "text": text,
                                                   "delay": 0.2, "team": bool(team)})
        threading.Thread(target=push, daemon=True, name="bots-chat").start()

    def _log(self, room: Room, uid: int, name: str, lines: List[Dict[str, Any]],
             said: str) -> None:
        world_name = bot_config.WORLD_LABELS.get(room.world, room.world)
        already = room.logged.get(uid, 0)
        seen = [{"at": int(l["at"]), "who": l["who"], "text": l["text"],
                 "inst": room.inst, "session": room.session, "kind": l.get("kind", "chat")}
                for l in lines if l.get("n", 0) > already]
        seen.append({"at": int(_now()), "who": name, "text": said, "inst": room.inst,
                     "session": room.session})
        if lines:
            room.logged[uid] = lines[-1]["n"]
        storage.append(uid, name, storage.chat_log(world_name), seen[-40:])

    # --------------------------------------------------------------- tick
    def tick(self, t: float) -> None:
        with self.lock:
            rooms = list(self.rooms.items())
        for key, room in rooms:
            # a host that went away (or a round that went to sleep) never
            # sends its "ended": the director's view of the host decides
            hosted = self._hosted(room)
            if hosted is None or not hosted.get("humans"):
                room.unhosted_since = room.unhosted_since or t
                if t - room.unhosted_since > 15 or t - room.touched > 1800:
                    with self.lock:
                        if self.rooms.get(key) is room:
                            self.rooms.pop(key, None)
                continue
            room.unhosted_since = 0.0
            self._expire_pending(room, t)
            try:
                self._speak_up(room, t)
            except Exception:
                import traceback
                traceback.print_exc()

    def _expire_pending(self, room: Room, now: float) -> None:
        """A line the host never showed (the bot left, the round ended under
        it) was never said: out of the transcript it goes."""
        with self.lock:
            gone = [k for k, e in room.pending.items() if now > float(e["at"]) + 20.0]
            for key in gone:
                entry = room.pending.pop(key)
                try:
                    room.lines.remove(entry)
                except ValueError:
                    pass

    def _hosted(self, room: Room) -> Optional[Dict[str, Any]]:
        hosted = getattr(self.d, "hosted", None)
        if hosted is None:
            return {"humans": len(room.humans)}      # no host view: trust the reports
        return (hosted.get(room.world) or {}).get(room.inst)

    def _speak_up(self, room: Room, now: float) -> None:
        """Now and then a bot says something nobody asked for, the way people
        do while they play: to someone in the server, about the round, a joke."""
        if not bot_config.get("messages.own_lines") or not bot_config.get("messages.ingame_chat") \
                or not room.bots or not room.humans or not self.d.enabled():
            return
        lo, hi = bot_config.get("messages.own_lines_seconds") or [30, 90]
        if not room.next_own:
            room.next_own = now + self.rng.uniform(float(lo), float(hi)) * 0.5
            return
        if now < room.next_own:
            return
        room.next_own = now + self.rng.uniform(float(lo), float(hi)) / self._buzz(room, now)
        if now - room.last_line_at < 6.0:
            room.next_own = min(room.next_own, now + 8.0)    # someone just spoke
            return
        weights = [(u, w) for u, w in self._weights(room, now)
                   if (room.bots[u].get("me") or {}).get("alive", True)]
        if not weights or not self._budget_ok(room):
            return
        uid = self.rng.choices([u for u, _w in weights], [max(0.02, w) for _u, w in weights])[0]
        room.sent.append(now)
        self.stats["own_lines"] += 1
        self._speak(room, uid, own=True)

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
            sessions = []
            for room in sorted(self.rooms.values(), key=lambda r: -r.last_line_at)[:6]:
                sessions.append({
                    "world": room.world, "inst": room.inst, "session": room.session,
                    "world_name": bot_config.WORLD_LABELS.get(room.world, room.world),
                    "since": int(room.started), "people": sorted(room.humans.values()),
                    "bots": len(room.bots), "lines": len(room.lines),
                    "tail": [{"who": l.get("who", ""), "text": l.get("text", ""),
                              "kind": l.get("kind", "chat"), "bot": bool(l.get("bot")),
                              "pending": bool(l.get("pending"))}
                             for l in list(room.lines)[-14:]]})
            return {"rooms": len(self.rooms), "stats": dict(self.stats),
                    "recent": list(self.recent), "heat": heat,
                    "events": list(self.event_log)[-25:], "sessions": sessions}


def _styled(line: str, card: Dict[str, Any], rng: random.Random) -> str:
    try:
        from ..game.bots.brain import styled
        return styled(line, card.get("traits") or {}, rng)
    except Exception:
        return line
