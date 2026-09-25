"""The bots of one live instance: their loop, their objectives, their chat,
and the two conversions between a live round and a sleeping one.

**The loop** runs inside the instance's own tick.  Movement is integrated for
every bot every tick (a few multiplications each); *thinking* is staggered and
depends on attention -- the near-radius and think rates come from the Bots
Zone -- and path planning is rationed per tick so a crowd of bots all deciding
at once cannot stall a frame.

**Objectives** are per mode and read the world's own state: the flags' real
positions and carriers, the cart's real position on its track, a plot's real
bank, buttons and stations.  Bots take flags, push carts and buy upgrades
through exactly the calls a player's client triggers.

**Waking** ("hydrate") builds a live round from the director's sleeping one:
the score, the clock, the captures, the cart, the restaurants -- and the bots
spread over the map by role (attackers up the field, defenders at home, the
odd one dead and waiting on a respawn, sometimes a flag already on the move),
so a person joining walks into the middle of a game rather than the start of
one.  **Sleeping** is the reverse, once nobody real has been in the round for
the grace period.
"""
from __future__ import annotations

import math
import random
import time
from typing import Any, Dict, List, Optional

from ..instance import Player, now
from .brain import Brain, feet, styled

TEAMS = ("red", "blue")


class BotRunner:
    def __init__(self, instance):
        self.instance = instance
        self.host = instance.host
        self.mode = instance.world.get("mode", "captures")
        self.rng = random.Random()
        self.brains: Dict[int, Brain] = {}
        self.humans: List[Player] = []
        self.nav = getattr(self.host, "nav", None)
        self.kill_y = float(instance.map.get("kill_y", -60.0))
        self.chat_due: List[Any] = []
        self.quick_times: List[float] = []
        self.reported_chat = len(instance.chat_log)
        self.events: List[str] = []
        self.speech: List[Dict[str, Any]] = []      # speech events not yet reported
        self.carriers: Dict[str, Any] = {}          # flag team -> (name, team) carrying it
        self.streaks: Dict[int, int] = {}           # pid -> kills since last death
        self.said_time_low = False
        self.said_final = False
        self._clock_check = 0.0
        self.path_tokens = 0
        self.sleep_at = 0.0
        self.wants_report = False
        self._human_check = 0.0

    @property
    def cfg(self) -> Dict[str, Any]:
        return getattr(self.host, "bot_cfg", None) or {}

    # ================================================================ bots
    def add(self, spec: Dict[str, Any], quiet: bool = False,
            team: Optional[str] = None) -> Optional[Player]:
        inst = self.instance
        uid = int(spec.get("uid", 0))
        for other in inst.players.values():
            if other.user_id == uid:
                return other           # already here
        player = inst.add_bot(uid, spec.get("name") or "Player",
                              spec.get("avatar") or {}, team or spec.get("team") or "",
                              quiet=quiet)
        stats = spec.get("stats") or [0, 0, 0]
        player.kills, player.deaths, player.score = (int(v) for v in stats[:3])
        brain = Brain(self, player, spec)
        player.brain = brain
        self.brains[player.pid] = brain
        if not quiet and self.humans:
            # somebody just arriving says hello now and then
            if self.rng.random() < 0.25:
                brain.say("hello", chance=0.6, delay=self.rng.uniform(2, 5))
        return player

    def remove(self, uid: int, reason: str = "", say_bye: bool = True) -> bool:
        inst = self.instance
        for pid, brain in list(self.brains.items()):
            if brain.uid != uid:
                continue
            if say_bye and self.humans and self.rng.random() < 0.3:
                player = inst.players.get(pid)
                if player is not None:
                    inst.handle_chat(player, {"m": styled(self.rng.choice(
                        ["gtg", "bye", "cya", "gn", "bye guys", "brb"]), brain.traits, self.rng)})
            self.brains.pop(pid, None)
            inst.remove_player(pid)
            return True
        return False

    def forget(self, pid: int) -> None:
        self.brains.pop(pid, None)

    # ================================================================ tick
    def tick(self, dt: float) -> None:
        moment = now()
        inst = self.instance
        if moment - self._human_check > 0.5:
            self._human_check = moment
            self.humans = [p for p in inst.players.values() if p.brain is None]
        if self.nav is not None and not self.nav.ready:
            self.nav.build_async()
        self.path_tokens = min(3, self.path_tokens + 1)
        active = bool(self.cfg.get("system_enabled", True))
        radius = float(self.cfg.get("near_radius", 170) or 170)
        humans = [h for h in self.humans if h.alive] or self.humans
        for brain in list(self.brains.values()):
            if active:
                brain.step(dt)
            else:
                brain.p.last_message = moment
                brain.p.last_input = moment
                continue
            if moment >= brain.next_think:
                near = False
                for human in humans:
                    if math.dist(human.pos, brain.p.pos) < radius:
                        near = True
                        break
                try:
                    brain.think(moment, near)
                except Exception:
                    import traceback
                    traceback.print_exc()
        if self.chat_due:
            self._flush_chat(moment)
        if self.humans and moment - self._clock_check >= 1.0:
            self._clock_check = moment
            self._check_clock()

    def path_budget(self) -> int:
        """Rationed A*: a few full searches a tick, cheap ones after that."""
        if self.path_tokens > 0:
            self.path_tokens -= 1
            return 1600
        return 250

    # ================================================================ chat
    def queue_chat(self, brain: Brain, text: str, delay: float, quick: bool = False) -> None:
        moment = now()
        if quick:
            limit = min(4, int(self.cfg.get("messages_chat_per_minute", 8) or 8))
            self.quick_times = [t for t in self.quick_times if moment - t < 60]
            if len(self.quick_times) >= limit:
                return
            self.quick_times.append(moment)
        self.chat_due.append((moment + max(0.0, delay), brain.p.pid, text))
        # people stop moving to type anything longer than a word or two
        if len(text) > 10:
            brain.typing_until = max(brain.typing_until, moment + min(6.0, delay))

    def say_for(self, uid: int, text: str, delay: float) -> bool:
        for brain in self.brains.values():
            if brain.uid == uid:
                self.queue_chat(brain, text, delay)
                return True
        return False

    def _flush_chat(self, moment: float) -> None:
        keep = []
        for due, pid, text in self.chat_due:
            if due > moment:
                keep.append((due, pid, text))
                continue
            player = self.instance.players.get(pid)
            if player is not None and self.humans:
                self.instance.handle_chat(player, {"m": text})
        self.chat_due = keep

    def note(self, text: str) -> None:
        self.events.append(text[:120])
        del self.events[:-20]

    def chat_report(self) -> Optional[Dict[str, Any]]:
        """New chat lines and happenings, for the web server's chat relay."""
        inst = self.instance
        if not self.humans:
            self.reported_chat = len(inst.chat_log)
            return None
        log = inst.chat_log
        start = min(self.reported_chat, len(log))
        # the log is trimmed from the front; if it shrank, start from the end
        fresh = log[start:] if start <= len(log) else []
        self.reported_chat = len(log)
        lines = []
        for entry in fresh:
            if entry.get("kind") == "system":
                self.note(entry.get("m", ""))
                continue
            uid = int(entry.get("uid", 0) or 0)
            is_bot = any(b.uid == uid for b in self.brains.values())
            lines.append({"who": entry.get("from", ""), "uid": uid,
                          "text": entry.get("m", ""), "team": entry.get("team", ""),
                          "at": entry.get("at", time.time()), "bot": is_bot})
        if not lines and not self.wants_report:
            return None
        self.wants_report = False
        events, self.events = self.events[-8:], []
        speech, self.speech = self.speech[-12:], []
        return {
            "inst": inst.instance_id, "lines": lines, "events": events,
            "speech": speech,
            "state": self.game_state(),
            "bots": [{"uid": b.uid, "name": b.p.username, "team": b.p.team,
                      "traits": {"chatty": b.t("chatty", 0.4)},
                      "me": self.bot_state(b)}
                     for b in self.brains.values()],
            "humans": [{"uid": h.user_id, "name": h.username, "team": h.team}
                       for h in self.humans],
        }

    # ========================================================== game state
    def game_state(self) -> Dict[str, Any]:
        """What anybody in the round can see on their screen right now: the
        score, the flags or the cart, the clock. Bots get it as background
        for anything they say."""
        inst = self.instance
        try:
            round_state = inst.round_state() or {}
        except Exception:
            round_state = {}
        state: Dict[str, Any] = {"mode": self.mode, "phase": inst.phase,
                                 "round": inst.round_number}
        if self.mode == "captures" and hasattr(inst, "flags"):
            state["score"] = dict(round_state.get("captures") or {})
            state["target"] = round_state.get("target")
            state["time_left"] = round_state.get("time_left")
            flags = {}
            for team, flag in inst.flags.items():
                entry: Dict[str, Any] = {"state": flag.state}
                if flag.state == "carried":
                    carrier = inst.players.get(flag.carrier or 0)
                    if carrier is not None:
                        entry["by"] = carrier.username
                        entry["by_team"] = carrier.team
                flags[team] = entry
            state["flags"] = flags
            for key in ("overtime", "sudden_death"):
                if round_state.get(key):
                    state[key] = True
        elif self.mode == "payload" and hasattr(inst, "cart_distance"):
            cart = round_state.get("cart") or {}
            state.update({
                "attackers": getattr(inst, "attackers", ""),
                "progress": round(float(cart.get("progress", 0.0)) * 100),
                "checkpoints": [int(round_state.get("checkpoints_reached", 0) or 0),
                                len(round_state.get("checkpoints") or [])],
                "round_wins": dict(round_state.get("round_wins") or {}),
                "target_wins": round_state.get("target_wins"),
                "time_left": round_state.get("time_left"),
                "setup_left": round_state.get("setup_left"),
                "pushing": int(cart.get("pushers", 0) or 0),
                "blocked": bool(cart.get("blocked")),
            })
        elif self.mode == "endless":
            plots = sorted(round_state.get("plots") or [], key=lambda p: -p.get("earned", 0))
            state["restaurants"] = [
                {"name": p.get("name"), "owner": p.get("owner") or "", "built": p.get("built"),
                 "total": p.get("total"), "income": p.get("income")}
                for p in plots if p.get("owner")][:5]
        state["people"] = [h.username for h in self.humans]
        state["players"] = len(inst.players)
        return state

    def bot_state(self, brain: Brain) -> Dict[str, Any]:
        """This bot's own view: its team, job and how its round is going."""
        p = brain.p
        me: Dict[str, Any] = {"alive": bool(p.alive), "kills": int(p.kills),
                              "deaths": int(p.deaths), "score": int(p.score),
                              "role": getattr(brain, "role", "")}
        if self.mode == "captures":
            me["carrying"] = self.urgent(brain)
        if self.mode == "endless":
            plot = getattr(self.instance, "plot_of", lambda _p: None)(p)
            if plot is not None:
                me["plot"] = plot.name
                me["built"] = len(plot.built)
                me["coins"] = int(getattr(p, "coins", 0) or 0)
        return me

    # ======================================================== speech events
    def on_game_event(self, kind: str, data: Dict[str, Any]) -> None:
        """Something happened that the people in the round could talk about.

        Nothing is decided here: the event is written up with who and which
        team, queued for the web server's chat relay, and the heartbeat is
        nudged so the reaction comes while it is still news."""
        if not self.humans or not self.brains:
            return
        if not self.cfg.get("speech_enabled", True):
            return
        inst = self.instance
        event: Dict[str, Any] = {"kind": kind, "at": time.time()}
        by_name = str(data.get("by") or "")
        if kind == "flag_take":
            carrier = inst.players.get(int(data.get("pid", 0) or 0))
            event.update(team=data.get("team", ""), by=by_name,
                         by_team=carrier.team if carrier else "")
            self.carriers[str(data.get("team", ""))] = (by_name, event["by_team"])
        elif kind == "flag_drop":
            name, team = self.carriers.pop(str(data.get("team", "")), ("", ""))
            event.update(team=data.get("team", ""), by=name, by_team=team)
        elif kind == "flag_return":
            returner = self._by_name(by_name)
            event.update(team=data.get("team", ""), by=by_name,
                         by_team=returner.team if returner else "")
            self.carriers.pop(str(data.get("team", "")), None)
        elif kind == "flag_capture":
            event.update(team=data.get("team", ""), by=by_name,
                         by_team=data.get("team", ""), score=data.get("score") or {})
            for team in list(self.carriers):
                if self.carriers[team][0] == by_name:
                    self.carriers.pop(team, None)
        elif kind == "lockdown":
            event.update(team=data.get("team", ""), on=bool(data.get("on")))
        elif kind in ("overtime", "sudden_death"):
            event["score"] = dict(getattr(inst, "captures", {}) or {})
        elif kind in ("setup_end", "checkpoint"):
            event["attackers"] = getattr(inst, "attackers", "")
            if kind == "checkpoint":
                event["n"] = data.get("n", 0)
                event["of"] = len(getattr(inst, "checkpoint_fractions", []) or [])
        else:
            event.update(data)
        self.speech.append(event)
        del self.speech[:-12]
        self.wants_report = True
        wake = getattr(self.host, "wake_heartbeat", None)
        if wake is not None:
            wake()

    def _by_name(self, name: str) -> Optional[Player]:
        if not name:
            return None
        for player in self.instance.players.values():
            if player.username == name:
                return player
        return None

    def _check_clock(self) -> None:
        """The events nobody pushes: a minute left, the cart's last stretch."""
        inst = self.instance
        if inst.phase != "active" or self.mode == "endless":
            return
        ends = getattr(inst, "round_ends", 0) or 0
        left = ends - now()
        if not self.said_time_low and 0 < left <= 60:
            self.said_time_low = True
            event: Dict[str, Any] = {"left": int(left)}
            if self.mode == "captures":
                event["score"] = dict(getattr(inst, "captures", {}) or {})
            self.on_game_event("time_low", event)
        if self.mode == "payload" and not self.said_final:
            length = max(1.0, float(getattr(inst, "track_length", 1.0) or 1.0))
            if float(getattr(inst, "cart_distance", 0.0) or 0.0) / length >= 0.85:
                self.said_final = True
                self.on_game_event("cart_final", {"attackers": getattr(inst, "attackers", "")})

    # =============================================================== events
    def on_kill(self, killer, victim, weapon: str) -> None:
        if victim is not None and victim.brain is not None:
            victim.brain.on_death(killer)
        if killer is not None and killer is not victim and killer.brain is not None:
            killer.brain.on_kill(victim)
        if killer is not None and victim is not None and self.humans:
            self.note("%s killed %s with %s" % (killer.username, victim.username, weapon))
        ended = self.streaks.pop(victim.pid, 0) if victim is not None else 0
        if killer is not None and killer is not victim:
            count = self.streaks.get(killer.pid, 0) + 1
            self.streaks[killer.pid] = count
            if count in (3, 5, 8, 12):
                self.on_game_event("killstreak", {"by": killer.username,
                                                  "by_team": killer.team, "n": count})
        if ended >= 3 and killer is not None and killer is not victim:
            self.on_game_event("streak_ended", {"by": killer.username, "by_team": killer.team,
                                                "victim": victim.username, "n": ended})

    def on_human_join(self, player) -> None:
        self.humans = [p for p in self.instance.players.values() if p.brain is None]
        self.sleep_at = 0.0
        greet = float(self.cfg.get("greet", 35) or 0) / 100.0
        if self._speech_on():
            # the chat relay greets them, knowing the score and who they are
            self.on_game_event("player_joined", {"by": player.username,
                                                 "by_team": player.team})
        elif self.brains and self.rng.random() < greet:
            brain = self.rng.choice(list(self.brains.values()))
            brain.say("hello", player.username, 1.0, delay=self.rng.uniform(1.5, 4.5))
        self.wants_report = True
        self.note("%s joined" % player.username)

    def _speech_on(self) -> bool:
        return bool(self.cfg.get("speech_enabled", True)) and \
            bool(self.cfg.get("messages_ingame_chat", True))

    def on_round_end(self, winner: str, reason: str = "") -> None:
        if self._speech_on():
            self.on_game_event("round_end", {
                "winner": winner, "reason": reason,
                "score": dict(getattr(self.instance, "captures", None)
                              or getattr(self.instance, "round_wins", None) or {})})
            return
        for brain in self.brains.values():
            if self.rng.random() < 0.3:
                brain.say("round", chance=0.4 + brain.t("kindness", 0.5) * 0.5,
                          delay=self.rng.uniform(0.5, 4.0))

    def on_round_start(self) -> None:
        self.said_time_low = False
        self.said_final = False
        self.carriers.clear()
        for brain in self.brains.values():
            # the round wiped kills and deaths; the score carries on
            brain.base = (0, 0, brain.base[2])
            brain.goal_until = 0.0
            brain.role = brain._pick_role()
        self.on_game_event("round_start", {
            "round": self.instance.round_number,
            "attackers": getattr(self.instance, "attackers", "")})

    def on_capture(self, team: str) -> None:
        if self._speech_on():
            return          # the capture reaches the chat relay as an event
        for brain in self.brains.values():
            if brain.p.team == team:
                brain.say("capture", chance=0.2)

    def on_flag_taken(self, team: str) -> None:
        if self._speech_on():
            return
        for brain in self.brains.values():
            if brain.p.team == team and self.rng.random() < 0.25:
                brain.say("lost", chance=0.35)
                break

    # =========================================================== objectives
    def role_counts(self, team: str, besides: Optional[Brain] = None) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for brain in self.brains.values():
            if brain is besides or brain.p.team != team:
                continue
            role = getattr(brain, "role", "")
            if role:
                counts[role] = counts.get(role, 0) + 1
        return counts

    def carries_our_flag(self, brain: Brain, other: Player) -> bool:
        flags = getattr(self.instance, "flags", None) or {}
        own = flags.get(brain.p.team)
        return own is not None and own.carrier == other.pid

    def urgent(self, brain: Brain) -> bool:
        """True while nothing should distract this bot from the objective:
        a flag carrier runs home, whatever mood it was in a moment ago."""
        if self.mode != "captures":
            return False
        flags = getattr(self.instance, "flags", None) or {}
        pid = brain.p.pid
        return any(f.carrier == pid for team, f in flags.items() if team != brain.p.team)

    def objective(self, brain: Brain) -> None:
        try:
            if self.mode == "captures":
                self._ctf(brain)
            elif self.mode == "payload":
                self._payload(brain)
            else:
                self._tycoon(brain)
        except Exception:
            import traceback
            traceback.print_exc()

    def _ctf(self, brain: Brain) -> None:
        inst = self.instance
        p = brain.p
        mine = p.team
        theirs = "blue" if mine == "red" else "red"
        own = inst.flags.get(mine)
        enemy = inst.flags.get(theirs)
        if own is None or enemy is None:
            return
        if enemy.carrier == p.pid:
            # run it home; a bot with sense runs the tunnels and flanks less
            brain.speed = 22.0
            brain.go(own.home, "home_" + mine, field="flag_" + mine)
            return
        if own.state == "dropped" and (brain.role == "defend" or
                                       math.dist(p.pos, own.pos) < 120):
            brain.go(own.pos, "return", precise=True)
            return
        if own.state == "carried":
            carrier = inst.players.get(own.carrier or 0)
            if carrier is not None and (brain.role != "attack" or
                                        math.dist(p.pos, carrier.pos) < 90):
                brain.go(feet(carrier), "chase%d" % carrier.pid)
                if brain.target is None and brain.near:
                    brain.target = carrier.pid
                return
        if enemy.state == "carried" and brain.role in ("attack", "roam"):
            carrier = inst.players.get(enemy.carrier or 0)
            if carrier is not None and carrier.team == mine:
                if math.dist(p.pos, carrier.pos) > 18:
                    brain.go(feet(carrier), "escort%d" % carrier.pid)
                return
        if brain.role == "attack" or (brain.role == "roam" and self.rng.random() < 0.4):
            if enemy.state == "home":
                if self._clear_first(brain, enemy.home):
                    return
                brain.go(enemy.home, "flag_" + theirs, field="flag_" + theirs, precise=True)
            else:
                brain.go(enemy.pos, "dropped_" + theirs, precise=True)
            return
        if brain.role == "defend":
            if brain.near_point(own.home, 45) and self.nav is not None and self.nav.ready:
                if not brain.waypoints:
                    node = self.nav.random_node(self.rng, own.home, 38)
                    if node >= 0:
                        brain.go(self.nav.point(node), "patrol%d" % node)
            else:
                brain.go(own.home, "home_" + mine, field="flag_" + mine)
            return
        # roamers hold the middle of the map
        mid = [(own.home[0] + enemy.home[0]) / 2.0, own.home[1],
               (own.home[2] + enemy.home[2]) / 2.0]
        if self.nav is not None and self.nav.ready and not brain.waypoints:
            node = self.nav.random_node(self.rng, mid, 70)
            if node >= 0:
                brain.go(self.nav.point(node), "mid%d" % node)

    def _clear_first(self, brain: Brain, flag_home: List[float]) -> bool:
        """Near a guarded flag, deal with the guards before grabbing it.

        Walking onto a flag with two defenders on it is how a carrier dies a
        second after the pickup, so an attacker who is outnumbered at the
        flag -- or already hurt -- stops at the edge of the base and fights
        from there, and goes for the flag once the room is clear.
        """
        p = brain.p
        d = math.dist(p.pos, flag_home)
        if d > 80 or d < 10:
            return False
        guards = [e for e in brain._enemies() if math.dist(e.pos, flag_home) < 42]
        if not guards:
            return False
        allies = sum(1 for other in self.instance.players.values()
                     if other is not p and other.alive and other.team == p.team
                     and math.dist(other.pos, p.pos) < 45)
        bold = brain.t("aggression", 0.5) * 0.4 + brain.skill * 0.3
        if len(guards) <= allies and p.health >= 50 and self.rng.random() < 0.5 + bold:
            return False
        nearest = min(guards, key=lambda e: math.dist(e.pos, p.pos))
        if brain.target is None:
            brain.target = nearest.pid
            brain.target_since = now()
        if d < 55:
            brain.waypoints = []          # hold the edge and trade from cover
        else:
            brain.go(flag_home, "flag_edge", field="flag_" + ("blue" if p.team == "red" else "red"))
        return True

    def _payload(self, brain: Brain) -> None:
        inst = self.instance
        p = brain.p
        cart = list(inst.cart_pos)
        attacking = p.team == inst.attackers
        if inst.phase == "setup":
            if not attacking and self.nav is not None and self.nav.ready and not brain.waypoints:
                ahead = self._track_point(inst, 0.08 + self.rng.random() * 0.25)
                node = self.nav.random_node(self.rng, ahead, 25)
                if node >= 0:
                    brain.go(self.nav.point(node), "setup%d" % node)
            return
        if attacking:
            if brain.role == "cart" or math.dist(p.pos, cart) < 40:
                if math.dist(p.pos, cart) > 6:
                    spot = [cart[0] + self.rng.uniform(-4, 4), cart[1],
                            cart[2] + self.rng.uniform(-4, 4)]
                    brain.go(spot, "cart%d" % int(inst.cart_distance // 6))
                else:
                    brain.waypoints = []
            else:
                ahead = self._track_point(inst, min(1.0, inst.cart_distance /
                                                    max(1.0, inst.track_length) + 0.1))
                brain.go(ahead, "flank%d" % int(inst.cart_distance // 10))
        else:
            if brain.role == "cart":
                spot = self._track_point(inst, min(1.0, inst.cart_distance /
                                                   max(1.0, inst.track_length) + 0.03))
                if math.dist(p.pos, spot) > 8:
                    brain.go(spot, "block%d" % int(inst.cart_distance // 6))
            else:
                ahead = self._track_point(inst, min(1.0, inst.cart_distance /
                                                    max(1.0, inst.track_length) + 0.15))
                if math.dist(p.pos, ahead) > 25:
                    brain.go(ahead, "hold%d" % int(inst.cart_distance // 10))

    @staticmethod
    def _track_point(inst, fraction: float) -> List[float]:
        from ..maps import payload as payload_map
        fraction = max(0.0, min(1.0, fraction))
        point, _yaw = payload_map.point_at(inst.track, fraction * inst.track_length)
        return list(point)

    def _tycoon(self, brain: Brain) -> None:
        from ..worlds import burger_tycoon as tycoon
        inst = self.instance
        p = brain.p
        plot = inst.plot_of(p)
        if plot is None:
            return
        if brain.role == "wander" and self.rng.random() < 0.6:
            if self.nav is not None and self.nav.ready and not brain.waypoints:
                node = self.nav.random_node(self.rng, plot.origin if self.rng.random() < 0.5
                                            else None, 120)
                if node >= 0:
                    brain.go(self.nav.point(node), "wander%d" % node)
            return
        # a station off cooldown pays best when you are standing at it
        for active in plot.actives():
            if active["ready_in"] <= 0 and self.rng.random() < 0.4 + brain.objective * 0.5:
                if math.dist(p.pos, active["p"]) <= tycoon.BUTTON_RADIUS * 1.6:
                    inst.handle(p, {"t": "act", "k": "use", "id": active["id"]})
                else:
                    brain.go(active["p"], "station_" + active["id"], precise=True)
                return
        buttons = sorted(plot.available(), key=lambda b: b["cost"])
        if buttons and p.coins >= buttons[0]["cost"]:
            button = buttons[0]
            if math.dist(p.pos, button["p"]) <= tycoon.BUTTON_RADIUS * 1.8:
                before = len(plot.built)
                inst.handle(p, {"t": "act", "k": "buy", "id": button["id"]})
                if len(plot.built) > before and self.rng.random() < 0.3:
                    brain.say("build", chance=0.5)
            else:
                brain.go(button["p"], "button_" + button["id"], precise=True)
            return
        collector = plot.to_world(tycoon.COLLECTOR_LOCAL)
        if plot.bank >= 40 or not buttons:
            brain.go(collector, "collect%d" % plot.index, precise=True)
            return
        # waiting on money: mill about the plot
        if self.nav is not None and self.nav.ready and not brain.waypoints:
            node = self.nav.random_node(self.rng, plot.origin, 36)
            if node >= 0:
                brain.go(self.nav.point(node), "mill%d" % node)

    # ================================================================ wake
    def wake(self, state: Dict[str, Any], bots: List[Dict[str, Any]]) -> None:
        """Build a live round, mid-flight, from a sleeping one."""
        inst = self.instance
        mode = state.get("mode") or self.mode
        by_uid: Dict[int, Player] = {}
        for spec in bots:
            player = self.add(spec, quiet=True, team=spec.get("team") or None)
            if player is not None:
                by_uid[int(spec["uid"])] = player
        inst.round_number = int(state.get("round", 1) or 1)
        moment = now()
        if mode == "captures" and hasattr(inst, "flags"):
            caps = state.get("captures") or {}
            inst.captures = {t: int(caps.get(t, 0) or 0) for t in TEAMS}
            left = float(state.get("time_left", inst.round_seconds) or inst.round_seconds)
            inst.round_ends = moment + max(30.0, left)
            inst.phase = "active"
        elif mode == "payload" and hasattr(inst, "cart_distance"):
            inst.attackers = state.get("attackers") or "blue"
            inst.defenders = "red" if inst.attackers == "blue" else "blue"
            inst.cart_distance = float(state.get("progress", 0) or 0) * inst.track_length
            inst.checkpoints_reached = int(state.get("checkpoints", 0) or 0)
            wins = state.get("round_wins") or {}
            inst.round_wins = {t: int(wins.get(t, 0) or 0) for t in TEAMS}
            from ..maps import payload as payload_map
            inst.cart_pos, inst.cart_yaw = payload_map.point_at(inst.track, inst.cart_distance)
            if state.get("phase") == "setup" and float(state.get("setup_left", 0) or 0) > 1:
                inst.phase = "setup"
                inst.phase_until = moment + float(state["setup_left"])
                inst.round_ends = inst.phase_until + float(state.get("time_left", 420) or 420)
            else:
                inst.phase = "active"
                inst.round_ends = moment + max(20.0, float(state.get("time_left", 300) or 300))
            inst.last_push = moment
        elif mode == "endless" and hasattr(inst, "plots"):
            self._wake_tycoon(state, by_uid)
        self._spread(by_uid, state)
        self._seed_chat(state, list(by_uid.values()))

    def _wake_tycoon(self, state: Dict[str, Any], by_uid: Dict[int, Player]) -> None:
        from ..worlds import burger_tycoon as tycoon
        inst = self.instance
        for index, info in enumerate(state.get("plots") or []):
            if index >= len(inst.plots):
                break
            plot = inst.plots[index]
            members = [by_uid[u] for u in info.get("members", []) if u in by_uid]
            if not members:
                continue
            for member in members:
                if member.plot != plot.index:
                    # move it onto the plot the sleeping round had it on
                    current = inst.plot_of(member)
                    if current is not None and member.pid in current.members:
                        current.members.remove(member.pid)
                        if current.owner == member.pid:
                            current.owner = current.members[0] if current.members else None
                        if not current.members:
                            current.reset()
                    member.team = plot.id
                    member.plot = plot.index
                    if member.pid not in plot.members:
                        plot.members.append(member.pid)
            if plot.owner is None or plot.owner not in [m.pid for m in members]:
                plot.owner = members[0].pid
                plot.owner_name = members[0].username
            plot.built = [u for u in info.get("built", []) if u in tycoon.UPGRADES_BY_ID]
            plot.recompute_income()
            plot.bank = float(info.get("bank", 0) or 0)
            plot.total_earned = float(info.get("earned", 0) or 0)
            coins = int(info.get("coins", 0) or 0)
            for member in members:
                member.coins = coins // max(1, len(members))
            for uid in plot.built:
                plot.active_ready.setdefault(uid, 0.0)

    def _spread(self, by_uid: Dict[int, Player], state: Dict[str, Any]) -> None:
        """Put the bots about the map the way a round in progress looks."""
        inst = self.instance
        grid = self.nav
        if grid is None or not grid.ready:
            return
        rng = self.rng
        moment = now()
        flag_out = state.get("flag_out")
        carrier_done = False
        for uid, player in by_uid.items():
            brain = player.brain
            point = None
            if self.mode == "captures" and hasattr(inst, "flags"):
                mine = inst.flags.get(player.team)
                theirs = inst.flags.get("blue" if player.team == "red" else "red")
                if mine is None or theirs is None:
                    continue
                if brain.role == "attack":
                    f = rng.uniform(0.35, 1.0)
                elif brain.role == "defend":
                    f = rng.uniform(0.0, 0.3)
                else:
                    f = rng.uniform(0.2, 0.8)
                point = [mine.home[i] + (theirs.home[i] - mine.home[i]) * f for i in range(3)]
                if flag_out and not carrier_done and theirs.team == flag_out and \
                        brain.role != "defend":
                    # this one is already running the enemy flag home
                    carrier_done = True
                    f = rng.uniform(0.35, 0.8)
                    point = [theirs.home[i] + (mine.home[i] - theirs.home[i]) * f for i in range(3)]
                    node = grid.random_node(rng, point, 30)
                    if node >= 0:
                        player.pos = grid.point(node)
                        brain.ground = list(player.pos)
                        brain.airborne = True
                        theirs.state = "carried"
                        theirs.carrier = player.pid
                        theirs.pos = [player.pos[0], player.pos[1] + 5.6, player.pos[2]]
                    continue
            elif self.mode == "payload" and hasattr(inst, "cart_pos"):
                attacking = player.team == inst.attackers
                progress = inst.cart_distance / max(1.0, inst.track_length)
                offset = rng.uniform(-0.12, 0.02) if attacking else rng.uniform(0.02, 0.25)
                point = self._track_point(inst, progress + offset)
            elif self.mode == "endless" and hasattr(inst, "plots"):
                plot = inst.plot_of(player)
                point = list(plot.origin) if plot is not None else None
            if point is None:
                continue
            node = grid.random_node(rng, point, 40)
            if node < 0:
                continue
            player.pos = grid.point(node)
            player.last_ground_pos = list(player.pos)
            if brain is not None:
                brain.ground = list(player.pos)
                brain.airborne = True
                brain.last_progress = (list(player.pos), moment)
            player.yaw = rng.uniform(-math.pi, math.pi)
            player.spawn_protect_until = 0.0
            # a few are waiting on a respawn when you arrive
            if self.mode != "endless" and rng.random() < 0.12:
                player.alive = False
                player.health = 0
                player.respawn_at = moment + rng.uniform(0.5, 4.0)
        if hasattr(inst, "broadcast_flags"):
            try:
                inst.broadcast_flags()
            except Exception:
                pass

    def _seed_chat(self, state: Dict[str, Any], players: List[Player]) -> None:
        """A round in progress has a chat history; give it a few lines."""
        if not players:
            return
        inst = self.instance
        rng = self.rng
        at = time.time() - rng.uniform(40, 200)
        lines = []
        if self.mode == "captures":
            caps = state.get("captures") or {}
            for team in TEAMS:
                for _ in range(int(caps.get(team, 0) or 0)):
                    scorers = [p for p in players if p.team == team]
                    if scorers:
                        lines.append({"t": "chat", "kind": "system", "from": "", "id": 0,
                                      "m": "%s captured the flag!" % rng.choice(scorers).username,
                                      "at": at})
                        at += rng.uniform(20, 90)
        elif self.mode == "endless":
            for p in rng.sample(players, min(2, len(players))):
                plot = inst.plot_of(p) if hasattr(inst, "plot_of") else None
                if plot is not None:
                    lines.append({"t": "chat", "kind": "system", "from": "", "id": 0,
                                  "m": "%s claimed %s!" % (p.username, plot.name), "at": at})
                    at += rng.uniform(10, 60)
        chatty = sorted(players, key=lambda p: -(p.brain.t("chatty", 0.4) if p.brain else 0))
        for p in chatty[:rng.randint(1, 3)]:
            text = styled(rng.choice(["gg", "lol", "nice", "push", "who has the flag",
                                      "anyone", "wait", "go go", "rip"]
                                     if self.mode != "endless" else
                                     ["nice restaurant", "lol", "how do i get money",
                                      "we need the fryer", "almost arches"]), p.brain.traits, rng)
            lines.append({"t": "chat", "from": p.username, "id": p.pid, "uid": p.user_id,
                          "team": p.team, "m": text, "kind": "all", "at": at,
                          "admin": False})
            at += rng.uniform(5, 40)
        lines.sort(key=lambda e: e["at"])
        inst.chat_log.extend(lines)
        del inst.chat_log[:-120]
        self.reported_chat = len(inst.chat_log)

    # =============================================================== sleep
    def sleep_snapshot(self) -> Dict[str, Any]:
        """Everything the director needs to keep this round going asleep."""
        inst = self.instance
        moment = now()
        live: Dict[str, Any] = {"mode": self.mode, "round": inst.round_number,
                                "phase": inst.phase,
                                "phase_left": max(0.0, inst.phase_until - moment)}
        if self.mode == "captures" and hasattr(inst, "captures"):
            live["captures"] = dict(inst.captures)
            live["time_left"] = max(0.0, inst.round_ends - moment)
        elif self.mode == "payload" and hasattr(inst, "cart_distance"):
            live.update({"attackers": inst.attackers,
                         "progress": inst.cart_distance / max(1.0, inst.track_length),
                         "checkpoints": inst.checkpoints_reached,
                         "round_wins": dict(inst.round_wins),
                         "time_left": max(0.0, inst.round_ends - moment)})
        elif self.mode == "endless" and hasattr(inst, "plots"):
            plots = []
            for plot in inst.plots:
                members = []
                for pid in plot.members:
                    player = inst.players.get(pid)
                    if player is not None and player.brain is not None:
                        members.append(player.user_id)
                coins = sum(inst.players[pid].coins for pid in plot.members
                            if pid in inst.players)
                plots.append({"members": members, "built": list(plot.built),
                              "coins": coins, "bank": int(plot.bank),
                              "earned": int(plot.total_earned)})
            live["plots"] = plots
        bots = []
        for brain in self.brains.values():
            p = brain.p
            bots.append({"uid": brain.uid, "team": p.team,
                         "stats": [p.kills, p.deaths, p.score],
                         "played": int(moment - p.joined_at)})
        return {"id": inst.instance_id, "bots": bots, "live": live}
