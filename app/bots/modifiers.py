"""Dynamic modifiers: short-lived boosts that follow a live conversation.

Two kinds, both on the Dynamic Modifiers subtab:

**Conversation momentum (DMs).** Somebody trading messages with a bot is in
a conversation, and people in a conversation answer faster than people
checking their inbox. Every time the person answers the bot counts as one
back-and-forth; from the configured number of turns on, the bot's reply
delay is cut by a percentage that grows a little with each further turn.
The boost is scaled by how quickly the person answered: straight back keeps
all of it, and a pause fades it linearly until, at the decay time, it is gone
and the count starts again.

**Chat heat (in-game).** A player who keeps talking in a round is more likely
to get answers. Each of their lines adds heat that fades linearly over the
decay time; the reply chance is multiplied by one plus the boost per unit of
heat, up to a ceiling. The bot they were last talking with is favoured to
answer their next line (people keep talking to whoever answered them), and a
hot chat can pull in a second voice.

Both only ever change *how soon* or *how likely*; whether a bot is online,
the budgets and the language model's own limits still apply as usual.
"""
from __future__ import annotations

import threading
from collections import deque
from typing import Any, Dict, Iterable, List, Optional, Tuple

from . import config as bot_config


def fade(elapsed: float, decay: float) -> float:
    """1.0 just now, falling in a straight line to 0.0 at ``decay`` seconds."""
    if decay <= 0:
        return 0.0
    return max(0.0, 1.0 - max(0.0, elapsed) / decay)


# ------------------------------------------------------------------ DMs
class Momentum:
    """Back-and-forth between bots and the people messaging them."""

    def __init__(self):
        self.lock = threading.Lock()
        # (bot uid, other uid) -> {"turns", "last", "side", "gap", "names"}
        self.pairs: Dict[Tuple[int, int], Dict[str, Any]] = {}

    @staticmethod
    def _decay() -> float:
        return float(bot_config.get("modifiers.dm_decay_seconds") or 60)

    def heard(self, bot: int, other: int, now: float, names: Tuple[str, str] = ("", "")) -> None:
        """The person sent the bot a message."""
        decay = self._decay()
        with self.lock:
            pair = self.pairs.get((bot, other))
            if pair is None or now - pair["last"] > decay:
                self.pairs[(bot, other)] = {"turns": 0, "last": now, "side": "human",
                                            "gap": 0.0, "names": names, "started": now}
                return
            if pair["side"] == "bot":
                # the bot had answered and now they answered back: one turn
                pair["turns"] += 1
                pair["gap"] = now - pair["last"]
            pair["last"] = now
            pair["side"] = "human"
            if names[0]:
                pair["names"] = names

    def replied(self, bot: int, other: int, now: float) -> None:
        """The bot's answer went out."""
        with self.lock:
            pair = self.pairs.get((bot, other))
            if pair is None:
                self.pairs[(bot, other)] = {"turns": 0, "last": now, "side": "bot",
                                            "gap": 0.0, "names": ("", ""), "started": now}
                return
            pair["last"] = now
            pair["side"] = "bot"

    def speedup(self, bot: int, other: int, now: float) -> float:
        """How much sooner the bot answers, 0.0 (no change) to 0.95."""
        if not bot_config.get("modifiers.dm_enabled"):
            return 0.0
        with self.lock:
            pair = self.pairs.get((bot, other))
            if pair is None:
                return 0.0
            return self._speedup(pair, now)

    def _speedup(self, pair: Dict[str, Any], now: float) -> float:
        need = int(bot_config.get("modifiers.dm_min_turns") or 0)
        turns = int(pair["turns"])
        if turns < max(1, need):
            return 0.0
        base = float(bot_config.get("modifiers.dm_speedup") or 0)
        step = float(bot_config.get("modifiers.dm_step") or 0)
        most = float(bot_config.get("modifiers.dm_max") or 0)
        percent = min(most, base + step * (turns - max(1, need)))
        # how quickly they came back decides how much of it is left
        strength = fade(pair["gap"], self._decay())
        return max(0.0, min(0.95, percent / 100.0 * strength))

    def talking(self, bot: int, now: float) -> bool:
        """Is the bot in a conversation that still has momentum?"""
        decay = self._decay()
        with self.lock:
            for (b, _o), pair in self.pairs.items():
                if b == bot and pair["turns"] >= 1 and now - pair["last"] < decay:
                    return True
        return False

    def prune(self, now: float) -> None:
        keep_for = self._decay() * 3 + 60
        with self.lock:
            for key in [k for k, p in self.pairs.items() if now - p["last"] > keep_for]:
                self.pairs.pop(key, None)

    def snapshot(self, now: float, limit: int = 30) -> List[Dict[str, Any]]:
        decay = self._decay()
        with self.lock:
            rows = []
            for (bot, other), pair in self.pairs.items():
                idle = now - pair["last"]
                if idle > decay:
                    continue
                rows.append({"bot": bot, "other": other,
                             "bot_name": pair["names"][0], "other_name": pair["names"][1],
                             "turns": pair["turns"], "waiting_on": pair["side"],
                             "speedup": round(self._speedup(pair, now) * 100, 1),
                             "fades_in": round(max(0.0, decay - idle), 1)})
        rows.sort(key=lambda r: (-r["turns"], r["fades_in"]))
        return rows[:limit]


# ------------------------------------------------------------ in-game chat
class Heat:
    """How much a round's real players are talking, fading as they stop."""

    __slots__ = ("lines", "partner")

    def __init__(self):
        self.lines: deque = deque(maxlen=40)                  # (uid, at)
        self.partner: Dict[int, Tuple[int, float]] = {}       # human -> (bot, at)

    def heard(self, uid: int, at: float) -> None:
        self.lines.append((uid, at))

    def level(self, now: float, uid: Optional[int] = None) -> float:
        decay = float(bot_config.get("modifiers.chat_decay_seconds") or 60)
        total = 0.0
        for who, at in self.lines:
            if uid is None or who == uid:
                total += fade(now - at, decay)
        return total

    def multiplier(self, now: float, uid: Optional[int] = None) -> float:
        if not bot_config.get("modifiers.chat_enabled"):
            return 1.0
        boost = float(bot_config.get("modifiers.chat_boost") or 0) / 100.0
        most = float(bot_config.get("modifiers.chat_max") or 0) / 100.0
        # the line being answered is already in the heat; it is the ones
        # before it that make this a conversation
        heat = max(0.0, self.level(now, uid) - 1.0)
        return 1.0 + min(most, boost * heat)

    def answered(self, human: int, bot: int, at: float) -> None:
        self.partner[human] = (bot, at)

    def partner_of(self, human: int, now: float) -> Tuple[Optional[int], float]:
        """The bot this person was last talking with, and how warm that is."""
        found = self.partner.get(human)
        if not found:
            return None, 0.0
        decay = float(bot_config.get("modifiers.chat_decay_seconds") or 60)
        warmth = fade(now - found[1], decay)
        return (found[0], warmth) if warmth > 0 else (None, 0.0)


def summarise_heat(rooms: Iterable[Tuple[str, int, "Heat", Dict[int, str]]],
                   now: float) -> List[Dict[str, Any]]:
    out = []
    for world, inst, heat, humans in rooms:
        level = heat.level(now)
        if level <= 0:
            continue
        talking = sorted({u for u, _at in heat.lines if u in humans and heat.level(now, u) > 0})
        out.append({"world": world, "inst": inst, "heat": round(level, 2),
                    "multiplier": round(heat.multiplier(now), 2),
                    "talking": [humans[uid] for uid in talking]})
    out.sort(key=lambda r: -r["heat"])
    return out
