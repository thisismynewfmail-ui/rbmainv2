"""Prop Panic: prop hunt (app/models/event_worlds/prop_panic.py).

Each round one team **hides** and the other **seeks**, and the next round
they swap, so in an area's two rounds everybody does both.

**Hiders** are props.  Every one starts as the area's humblest thing (a
flower pot, a toy block, a can of paint) and turns into anything placed in
the area by looking at it and pressing E -- the disguise is the area's own
drawing of that thing (app/game/maps/events/prop_panic/catalogue.py), and
its size is the hider's hull: what a shot has to hit, and what the hider's
own movement collides with on the client.  R gives it a quarter turn.  A
small thing is hard to spot and easy to break; a big one soaks hits.  They
carry a **taunt** (points, at the price of being heard), a **decoy** (a
copy of their disguise left behind for a hunter to waste a shot on) and a
**scurry** (a short burst of speed).

**Seekers** wait in the area's pen, blindfolded, through the countdown,
then the door opens.  Their **popper** finds a hider in a few hits and
heals them a little; a shot into a prop that was only a prop costs them
health (a wrong guess); a decoy costs more.  The **sniffer** makes the
nearest hider squeak; the **glitter bomb** dusts everything near where it
lands and shows who is not what they seem.  A hider who is found is out
and watches the rest.  The seekers win by finding every hider before the
clock runs out; one hider left standing at the end wins it for the hiders.

In the last minute the house *creaks*: every hider still standing squeaks
on its own every so often.  The last hider standing is told so, and is
worth more.

**The twists**, one per area (``extra["twist"]``):

``cat``       Grandma's Cottage: Mittens wanders the house and garden and
              stops to stare at anything that is not what it seems.  A
              taunt next to her sends her off with a hiss.
``blackout``  the Toy Emporium: the power goes every so often; the lights
              flicker first, then darkness and the seekers' torches.
``sale``      MegaMart: the tannoy announces a flash sale on one kind of
              thing, and a few seconds later everything of that kind in the
              store has a price tag over it -- change, or be priced.
``alarm``     the Museum after dark: a security searchlight sweeps the halls
              and anything that moves in its beam sets off the alarm.
"""
from __future__ import annotations

import math
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from .. import instance as engine
from ..instance import EYE_HEIGHT, MAX_HEALTH, Player, ray_aabb
from ..maps.events import prop_panic as pp_map
from .arena import NEVER, ArenaWorld

HIDE_TOOLS = ("pp_taunt", "pp_decoy", "pp_scurry")
SEEK_TOOLS = ("pp_popper", "pp_sniff", "pp_glitter")

POP_DAMAGE = 20.0
POP_RANGE = 140.0
POP_HEAL = 4.0
WRONG_GUESS = 4.0
DECOY_FOOLED = 6.0
DISGUISE_REACH = 14.0
DISGUISE_COOL = 1.2
TAUNT_COOL = 5.0
DECOYS = 2
SCURRY_SECONDS = 3.0
SCURRY_COOL = 16.0
SCURRY_SPEED = 1.6
SNIFF_COOL = 24.0
SNIFF_RANGE = 75.0
GLITTER_CHARGES = 2
GLITTER_R = 8.0
GLITTER_DAMAGE = 15.0
GLITTER_SECONDS = 6.0
GLITTER_RANGE = 70.0
CREAK_LEFT = 60.0
CREAK_EVERY = 20.0
MOVING = 1.8              # units a second before a hider counts as moving
CAT_SPEED = 9.0
CAT_SNIFF = 9.0
CAT_STARE = 5.0
CAT_SHOO = 10.0
DARK_EVERY = (50.0, 70.0)
DARK_WARN = 3.0
DARK_SECONDS = 12.0
SALE_EVERY = (52.0, 70.0)
SALE_WARN = 6.0
SALE_SECONDS = 10.0
SPOT_SPEED = 10.0
SPOT_R = 9.0
ALARM_SECONDS = 6.0
BOT_WALK = 14.0             # about how fast a bot covers ground, paths and all
REVEAL_FIND = 9.0          # a find within this long of a reveal counts for its badge
# what a seeking bot says when it goes after a lead, by what the lead was
LEAD_LINES = {"cat": ["follow the cat", "the cat found one", "cats staring at something"],
              "sale": ["check the price tags", "sale tag over here", "tagged one"],
              "alarm": ["alarm!", "searchlight got one", "the alarm, go"],
              "taunt": ["heard one", "its close", "taunt over here"],
              "sniff": ["squeak over here", "sniffer says close"],
              "creak": ["heard a squeak", "something squeaked"],
              "glitter": ["glitter on one", "its sparkly lol"]}
DEFAULTS: Dict[str, Any] = {}


def _defaults() -> Dict[str, Any]:
    if not DEFAULTS:
        from ...models.event_worlds import prop_panic as meta
        for spec in meta.BOT_FIELDS:
            DEFAULTS[spec[0]] = spec[3]
    return DEFAULTS


def hull_size(kinds: Dict[str, Any], key: str, quarter: int) -> Tuple[float, float, float]:
    w, h, d = (kinds.get(key) or {}).get("size") or (2.0, 2.0, 2.0)
    return (d, h, w) if quarter % 2 else (w, h, d)


def hull_box(pos: Sequence[float], size: Sequence[float]) -> Tuple[List[float], List[float]]:
    w, h, d = size
    return ([pos[0] - w / 2.0, pos[1], pos[2] - d / 2.0],
            [pos[0] + w / 2.0, pos[1] + h, pos[2] + d / 2.0])


def _item(item_id: str, name: str, kind: str, parts: List[Dict[str, Any]],
          **stats: Any) -> Dict[str, Any]:
    body = {"kind": kind, "rpm": stats.pop("rpm", 120), "mag": stats.pop("mag", 99),
            "reserve": 0, "range": stats.pop("range", 60), "custom": True}
    body.update(stats)
    return ArenaWorld.item(item_id, name, body, parts)


def _kit(role: str) -> List[Dict[str, Any]]:
    """The hotbar for a role, in the avatar's own item format."""
    if role == "hunter":
        return [
            _item("pp_popper", "Prop Popper", "pp_popper", [
                {"t": "box", "p": [0, 0, 0.3], "s": [0.5, 0.6, 1.6], "c": "#3a8ad8"},
                {"t": "cyl", "p": [0, 0.05, 1.3], "s": [0.36, 0.5, 0.36], "c": "#f2c230",
                 "r": [1.5708, 0, 0]},
                {"t": "box", "p": [0, -0.45, 0.0], "s": [0.3, 0.6, 0.4], "c": "#2a2a30"},
                {"t": "sph", "p": [0, 0.42, 0.2], "s": [0.42, 0.42, 0.42], "c": "#f07aa8"}],
                rpm=300, range=POP_RANGE, auto=True, sound="pp_pop", tracer="#ffd23a"),
            _item("pp_sniff", "Sniffer", "pp_sniff", [
                {"t": "box", "p": [0, 0, 0.2], "s": [0.6, 0.5, 1.0], "c": "#7a5a3a"},
                {"t": "cone", "p": [0, 0, 0.9], "s": [0.6, 0.6, 0.6], "c": "#2a2a2a",
                 "r": [1.5708, 0, 0]},
                {"t": "sph", "p": [0, 0.35, 0.1], "s": [0.3, 0.3, 0.3], "c": "#7affd8",
                 "m": "neon"}], held_item=True, range=SNIFF_RANGE),
            _item("pp_glitter", "Glitter Bomb", "pp_glitter", [
                {"t": "sph", "p": [0, 0, 0.3], "s": [0.8, 0.8, 0.8], "c": "#c86af0",
                 "m": "metal"},
                {"t": "cyl", "p": [0, 0.45, 0.3], "s": [0.2, 0.3, 0.2], "c": "#f2c230"}],
                held_item=True, range=GLITTER_RANGE),
        ]
    return [
        _item("pp_taunt", "Taunt", "pp_taunt", [
            {"t": "cone", "p": [0, 0, 0.4], "s": [0.6, 1.0, 0.6], "c": "#f2c230",
             "r": [1.5708, 0, 0]},
            {"t": "sph", "p": [0, 0, -0.2], "s": [0.5, 0.5, 0.5], "c": "#d83a2a"}],
            held_item=True),
        _item("pp_decoy", "Decoy", "pp_decoy", [
            {"t": "box", "p": [0, 0, 0.2], "s": [0.7, 0.7, 0.7], "c": "#a07a52"},
            {"t": "box", "p": [0, 0.36, 0.2], "s": [0.72, 0.06, 0.72], "c": "#f2f0ea"}],
            held_item=True),
        _item("pp_scurry", "Scurry", "pp_scurry", [
            {"t": "box", "p": [0, 0, 0.2], "s": [0.5, 0.3, 0.9], "c": "#3aa04a"},
            {"t": "box", "p": [0, -0.2, 0.2], "s": [0.56, 0.12, 0.96], "c": "#f2f0ea"}],
            held_item=True),
    ]


class PropPanicWorld(ArenaWorld):
    MAP = pp_map
    TEAMS = ("red", "blue")
    TEAM_NAMES = {"red": "Dust Bunnies", "blue": "Feather Dusters"}
    ROUNDS_PER_AREA = 2
    SETUP_SECONDS = 40.0          # the hiders' head start, the seekers in the pen
    ROUND_SECONDS = 210.0
    RESULTS_SECONDS = 14.0
    CUSTOM_KINDS = HIDE_TOOLS + SEEK_TOOLS
    LOGO = "Prop Panic"
    respawn_seconds = 6.0
    BOT_REVENGE = 0.0
    HELD_TIMERS = ("creak_at",)
    BOT_CHATTER = ["where are they", "found one", "that lamp moved", "sus teapot", "gg",
                   "lol", "nice hide", "checking upstairs", "taunt again i dare u", "ez"]

    # ------------------------------------------------------------ settings
    def setting(self, key: str) -> Any:
        cfg = getattr(self.bots, "cfg", None) if self.bots is not None else None
        value = (cfg or {}).get("prop_panic_" + key)
        return _defaults().get(key) if value is None else value

    def pct(self, key: str) -> float:
        try:
            return max(0.0, min(1.0, float(self.setting(key)) / 100.0))
        except (TypeError, ValueError):
            return 0.5

    # ================================================================ setup
    def world_setup(self) -> None:
        self.hiders = "red"
        self.seekers = "blue"
        self.kinds: Dict[str, Dict[str, Any]] = {}
        self.decor: List[Dict[str, Any]] = []
        self.decor_grid: Dict[Tuple[int, int], List[int]] = {}
        self.decoys: List[Dict[str, Any]] = []
        self.decoy_seq = 0
        self.reveals: Dict[int, Dict[str, Any]] = {}
        self.round_stats: Dict[int, Dict[str, float]] = {}
        self.claims: Dict[int, int] = {}
        self.searched: Dict[int, float] = {}
        self.leads: List[Dict[str, Any]] = []
        self.creak_at = 0.0
        self.last_called = False
        self.started_hiders = 0
        self.twist = ""
        self.cat: Dict[str, Any] = {}
        self.dark: Dict[str, Any] = {}
        self.sale: Dict[str, Any] = {}
        self.spot: Dict[str, Any] = {}
        self.events_said: Dict[str, float] = {}
        self.counts: Dict[str, int] = {"found": 0, "disguised": 0, "taunts": 0, "decoys": 0,
                                       "cat": 0, "dark": 0, "sale": 0, "alarm": 0,
                                       "wrong": 0, "sniffs": 0, "glitter": 0}

    def round_setup(self) -> None:
        area = self.area
        extra = area.get("extra") or {}
        points = area.get("points") or {}
        # a place may set its own clock, tuned to how long it takes to search
        self.ROUND_SECONDS = float(extra.get("round_seconds") or PropPanicWorld.ROUND_SECONDS)
        # who hides this round: the teams take turns, so each does both in an area
        self.hiders = self.TEAMS[self.round_number % 2]
        self.seekers = self.rival(self.hiders)
        self.kinds = dict(extra.get("props") or {})
        self.starter = str(extra.get("starter") or (next(iter(self.kinds)) if self.kinds else ""))
        self.decor = []
        for i, d in enumerate(extra.get("decor") or []):
            size = hull_size(self.kinds, d["k"], int(d.get("q", 0)))
            lo, hi = hull_box(d["p"], size)
            self.decor.append({"i": i, "k": d["k"], "p": list(d["p"]), "q": int(d.get("q", 0)),
                               "lo": lo, "hi": hi})
        self.decor_grid = {}
        for entry in self.decor:
            key = (int(entry["p"][0] // 24), int(entry["p"][2] // 24))
            self.decor_grid.setdefault(key, []).append(entry["i"])
        self.hides = [list(m["p"]) for m in points.get("hide", [])]
        self.searches = [(list(m["p"]), str(m.get("name") or "")) for m in points.get("search", [])]
        self.cat_spots = [list(m["p"]) for m in points.get("cat", [])]
        self.sweep = [list(m["p"]) for m in points.get("sweep", [])]
        self.pen = (points.get("pen") or [{}])[0]
        self.landmarks = [(list(m["p"]), m["name"]) for m in area.get("landmarks") or []]
        self.twist = str(extra.get("twist") or "")
        self.pen_key = str(extra.get("pen_key") or "pen")
        self.decoys = []
        self.reveals = {}
        self.round_stats = {}
        self.claims = {}
        self.searched = {}
        self.leads = []
        self.creak_at = 0.0
        self.last_called = False
        self.started_hiders = 0
        self.events_said = {}
        self.set_dynamic_group(self.pen_key, True)
        moment = engine.now()
        self.cat = {}
        if self.twist == "cat" and self.cat_spots:
            start = self.cat_spots[0]
            self.cat = {"p": list(start), "yaw": 0.0, "path": [], "goal": 0, "mode": "walk",
                        "stare": 0, "until": 0.0, "rest": {}, "next_pick": moment}
        self.dark = {"on": False, "warn": 0.0, "until": 0.0, "next": NEVER}
        self.sale = {"kind": "", "warn": 0.0, "until": 0.0, "next": NEVER}
        self.spot = {}
        if self.twist == "alarm" and len(self.sweep) >= 2:
            self.spot = {"i": 0, "f": 0.0, "p": list(self.sweep[0])}
        for player in self.players.values():
            self._clear(player)

    def _clear(self, player: Player) -> None:
        for key in ("dis", "q", "dis_at", "taunt_at", "decoys", "scurry_until", "scurry_at",
                    "sniff_at", "glitter", "pp_mind", "pp_hp", "last_pos", "last_at",
                    "moved_at", "role"):
            player.extra.pop(key, None)

    # ------------------------------------------------------------- teams
    def rival(self, team: str) -> str:
        return "blue" if team == "red" else "red"

    def role_of(self, player: Player) -> str:
        return "prop" if player.team == self.hiders else "hunter"

    def is_prop(self, player: Player) -> bool:
        return player.team == self.hiders

    def props_alive(self) -> List[Player]:
        return [p for p in self.players.values() if p.team == self.hiders and self.in_play(p)]

    # ============================================================ spawning
    def spawn_points(self, team: str) -> List[Dict[str, Any]]:
        spawns = self.area.get("spawns") or {}
        key = "props" if team == self.hiders else "hunters"
        return list(spawns.get(key) or []) or super().spawn_points(team)

    def spawn_player(self, player: Player) -> None:
        # a hider who arrives once the seekers are out has nowhere left to hide
        if player.team == self.hiders and self.phase == "active" and \
                not player.extra.get("in_round"):
            self.park(player)
            return
        super().spawn_player(player)

    def on_spawned(self, player: Player) -> None:
        moment = engine.now()
        role = self.role_of(player)
        player.extra["role"] = role
        player.extra["last_pos"] = list(player.pos)
        player.extra["last_at"] = moment
        if role == "prop":
            player.extra["decoys"] = DECOYS
            player.extra["q"] = 0
            self._become(player, self.starter, 0, quiet=True, first=True)
            self.set_loadout(player, _kit("prop"), public=[], quiet=True)
        else:
            player.extra["glitter"] = GLITTER_CHARGES
            player.extra.pop("dis", None)
            self.set_loadout(player, _kit("hunter"), quiet=True)
            self.broadcast({"t": "ppd", "id": player.pid, "k": "", "q": 0})

    def reset_player(self, player: Player) -> None:
        self._clear(player)

    def welcome_lines(self, player: Player) -> List[str]:
        lines = super().welcome_lines(player)
        lines.append("%s hide this round, %s seek. Hiders: look at anything and press E to "
                     "become it, R to turn it. Seekers: pop the props that are people -- a "
                     "wrong guess hurts." % (self.team_name(self.hiders),
                                             self.team_name(self.seekers)))
        twist = {"cat": "Mind Mittens the cat: she stares at anything that is not what it seems.",
                 "blackout": "The power keeps going in the Toy Emporium -- the seekers have torches.",
                 "sale": "Listen for the tannoy: a flash sale puts a price tag on everything of "
                         "one kind.",
                 "alarm": "Do not move in the searchlight's beam: it sets off the alarm."}.get(self.twist)
        if twist:
            lines.append(twist)
        return lines

    def on_player_ready(self, player: Player) -> None:
        super().on_player_ready(player)
        player.send({"t": "ppall", "d": self._disguises(), "decoys": self._decoy_list()})

    # ========================================================== disguises
    def _become(self, player: Player, key: str, quarter: int, quiet: bool = False,
                first: bool = False) -> bool:
        if key not in self.kinds:
            return False
        old = player.extra.get("dis")
        old_hp = float((self.kinds.get(old) or {}).get("hp", MAX_HEALTH)) if old else MAX_HEALTH
        frac = 1.0 if first else max(0.05, min(1.0, player.health / max(1.0, old_hp)))
        player.extra["dis"] = key
        player.extra["q"] = int(quarter) % 4
        hp = float(self.kinds[key].get("hp", 50))
        player.health = max(1.0, round(hp * frac, 1))
        player.extra["pp_hp"] = hp
        self.broadcast({"t": "ppd", "id": player.pid, "k": key, "q": player.extra["q"]})
        if not first:
            self._stat(player, "disguises")
            self.badge(player, "pp_disguises")
            self.counts["disguised"] += 1
            if not quiet:
                player.send({"t": "ppx", "k": "became", "what": self.kinds[key]["name"]})
        self._send_me(player, force=True)
        return True

    def _hull(self, player: Player) -> Tuple[List[float], List[float]]:
        key = player.extra.get("dis") or self.starter
        return hull_box(player.pos, hull_size(self.kinds, key, int(player.extra.get("q", 0))))

    def hull_fits(self, x: float, y: float, z: float, size: Sequence[float]) -> bool:
        """Is there room for a hull of ``size`` standing at (x, y, z)?"""
        w, h, d = size
        lo = [x - w / 2.0 + 0.05, y + 0.1, z - d / 2.0 + 0.05]
        hi = [x + w / 2.0 - 0.05, y + h, z + d / 2.0 - 0.05]
        return not any(b_hi[0] > lo[0] and b_lo[0] < hi[0] and b_hi[1] > lo[1]
                       and b_lo[1] < hi[1] and b_hi[2] > lo[2] and b_lo[2] < hi[2]
                       for b_lo, b_hi in self._colliders_near(lo, hi))

    def _decor_near(self, x: float, z: float, radius: float) -> Iterable[Dict[str, Any]]:
        cx, cz = int(x // 24), int(z // 24)
        reach = int(radius // 24) + 1
        for gx in range(cx - reach, cx + reach + 1):
            for gz in range(cz - reach, cz + reach + 1):
                for index in self.decor_grid.get((gx, gz), ()):
                    entry = self.decor[index]
                    if math.hypot(entry["p"][0] - x, entry["p"][2] - z) <= radius:
                        yield entry

    def _look_decor(self, player: Player, index: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """The placed prop ``player`` is looking at (or the one it named, if
        it is in reach and in sight)."""
        eye = [player.pos[0], player.pos[1] + EYE_HEIGHT, player.pos[2]]
        if index is not None:
            if not (0 <= index < len(self.decor)):
                return None
            entry = self.decor[index]
            centre = [(entry["lo"][i] + entry["hi"][i]) / 2.0 for i in range(3)]
            if math.dist(eye, centre) > DISGUISE_REACH + 4.0:
                return None
            if not self._sees_box(eye, entry["lo"], entry["hi"]):
                return None
            return entry
        cp = math.cos(player.pitch)
        direction = [math.sin(player.yaw) * cp, math.sin(player.pitch), math.cos(player.yaw) * cp]
        world = self.ray_world(eye, direction, DISGUISE_REACH)
        best, best_t = None, world + 0.8
        for entry in self._decor_near(player.pos[0], player.pos[2], DISGUISE_REACH + 4.0):
            t = ray_aabb(eye, direction, entry["lo"], entry["hi"])
            if t is not None and 0.0 <= t < best_t:
                best, best_t = entry, t
        return best

    def _sees_box(self, eye: Sequence[float], lo: Sequence[float], hi: Sequence[float]) -> bool:
        centre = [(lo[0] + hi[0]) / 2.0, (lo[1] + hi[1]) / 2.0, (lo[2] + hi[2]) / 2.0]
        delta = [centre[i] - eye[i] for i in range(3)]
        dist = math.sqrt(sum(v * v for v in delta)) or 1.0
        direction = [v / dist for v in delta]
        world = self.ray_world(eye, direction, dist)
        hit = ray_aabb(eye, direction, lo, hi)
        return hit is not None and hit <= world + 0.6

    def disguise_as(self, player: Player, entry: Dict[str, Any]) -> bool:
        """``player`` becomes what ``entry`` is, facing the way it faces."""
        moment = engine.now()
        if not self.is_prop(player) or not self.in_play(player):
            return False
        if moment < float(player.extra.get("dis_at", 0.0)):
            return False
        same = player.extra.get("dis") == entry["k"] and \
            int(player.extra.get("q", 0)) == entry["q"]
        if same:
            return False
        player.extra["dis_at"] = moment + DISGUISE_COOL
        return self._become(player, entry["k"], entry["q"])

    # ============================================================== input
    def use(self, player: Player, message: Dict[str, Any]) -> None:
        if not self.is_prop(player):
            return
        index = message.get("i")
        try:
            index = int(index) if index is not None else None
        except (TypeError, ValueError):
            index = None
        entry = self._look_decor(player, index)
        if entry is not None:
            self.disguise_as(player, entry)

    def world_action(self, player: Player, kind: Any, message: Dict[str, Any]) -> None:
        if kind == "disguise":
            self.use(player, message)
        elif kind == "spin":
            self.spin(player)

    def spin(self, player: Player) -> None:
        if not self.is_prop(player) or not self.in_play(player):
            return
        key = player.extra.get("dis") or self.starter
        q = (int(player.extra.get("q", 0)) + 1) % 4
        player.extra["q"] = q
        self.broadcast({"t": "ppd", "id": player.pid, "k": key, "q": q})
        self._send_me(player, force=True)

    def move_scale(self, player: Player) -> float:
        if not self.is_prop(player):
            return 1.0
        moment = engine.now()
        speed = float((self.kinds.get(player.extra.get("dis") or "") or {}).get("speed", 1.0))
        if moment < float(player.extra.get("scurry_until", 0.0)):
            speed *= SCURRY_SPEED
        return speed

    def can_fire(self, player: Player) -> bool:
        return self.phase == "active" and self.in_play(player)

    # ============================================================ the kit
    def custom_fire(self, player: Player, stats: Dict[str, Any], direction: List[float],
                    origin: List[float]) -> None:
        kind = stats.get("kind")
        hunter = not self.is_prop(player)
        if kind == "pp_popper" and hunter:
            self._pop(player, direction, origin)
        elif kind == "pp_sniff" and hunter:
            self._sniff(player)
        elif kind == "pp_glitter" and hunter:
            self._glitter(player, direction, origin)
        elif kind == "pp_taunt" and not hunter:
            self._taunt(player)
        elif kind == "pp_decoy" and not hunter:
            self._decoy(player)
        elif kind == "pp_scurry" and not hunter:
            self._scurry(player)

    def _pop(self, hunter: Player, direction: List[float], origin: List[float]) -> None:
        moment = engine.now()
        world = self.ray_world(origin, direction, POP_RANGE)
        best_t, best = world, None
        for prop in self.props_alive():
            lo, hi = self._hull(prop)
            t = ray_aabb(origin, direction, lo, hi)
            if t is not None and 0.0 <= t < best_t + 0.3:
                best_t, best = min(best_t, t), ("prop", prop)
        if best is None:
            for decoy in self.decoys:
                t = ray_aabb(origin, direction, decoy["lo"], decoy["hi"])
                if t is not None and 0.0 <= t < best_t + 0.3:
                    best_t, best = min(best_t, t), ("decoy", decoy)
        if best is None:
            for entry in self._decor_near(origin[0], origin[2], min(POP_RANGE, world + 6.0)):
                t = ray_aabb(origin, direction, entry["lo"], entry["hi"])
                if t is not None and 0.0 <= t < world + 0.8 and t < best_t + 0.8:
                    best_t, best = min(best_t, t), ("decor", entry)
        end = [origin[i] + direction[i] * best_t for i in range(3)]
        what = best[0] if best else ""
        self.broadcast({"t": "ppx", "k": "shot", "id": hunter.pid,
                        "a": [round(v, 2) for v in origin], "b": [round(v, 2) for v in end],
                        "h": what}, exclude=hunter.pid)
        if what == "prop":
            prop = best[1]
            self._stat(hunter, "hits")
            hunter.health = min(MAX_HEALTH, hunter.health + POP_HEAL)
            self._mind(prop)["shot_at"] = moment
            self.apply_damage(prop, hunter, POP_DAMAGE, "Prop Popper")
            hunter.send({"t": "ppx", "k": "hit", "hp": round(hunter.health)})
        elif what == "decoy":
            decoy = best[1]
            self._pop_decoy(decoy, hunter)
            self.apply_damage(hunter, None, DECOY_FOOLED, "a decoy")
        elif what == "decor":
            self.counts["wrong"] += 1
            self._stat(hunter, "wrong")
            hunter.send({"t": "ppx", "k": "wrong", "what": self.kinds.get(best[1]["k"], {}).get(
                "name", "a prop")})
            self.apply_damage(hunter, None, WRONG_GUESS, "a wrong guess")

    def _pop_decoy(self, decoy: Dict[str, Any], hunter: Optional[Player]) -> None:
        if decoy not in self.decoys:
            return
        self.decoys.remove(decoy)
        owner = self.players.get(decoy["owner"])
        self.counts["decoys"] += 1
        if owner is not None and hunter is not None:
            owner.score += 8
            self._stat(owner, "decoy_hits")
            self.badge(owner, "pp_decoys")
            owner.send({"t": "ppx", "k": "fooled", "by": hunter.username})
        self.broadcast({"t": "ppx", "k": "decoy_pop", "id": decoy["id"], "p": decoy["p"],
                        "by": hunter.username if hunter else ""})
        if hunter is not None:
            self._event("pp_decoy", hunter, hunter.team, what=self._place(decoy["p"]),
                        owner=owner.username if owner else "")

    def _sniff(self, hunter: Player) -> None:
        moment = engine.now()
        if moment < float(hunter.extra.get("sniff_at", 0.0)):
            return
        hunter.extra["sniff_at"] = moment + SNIFF_COOL
        self.counts["sniffs"] += 1
        best, best_d = None, SNIFF_RANGE
        for prop in self.props_alive():
            d = math.dist(prop.pos, hunter.pos)
            if d < best_d:
                best, best_d = prop, d
        if best is None:
            hunter.send({"t": "ppx", "k": "sniff", "d": -1})
            self._send_me(hunter, force=True)
            return
        band = "right here" if best_d < 15 else ("close" if best_d < 35 else "somewhere near")
        hunter.send({"t": "ppx", "k": "sniff", "d": round(best_d), "band": band})
        self._squeak(best, "sniff")
        self._lead(best.pos, 6.0, hunter.team, "sniff")
        self._send_me(hunter, force=True)

    def _glitter(self, hunter: Player, direction: List[float], origin: List[float]) -> None:
        left = int(hunter.extra.get("glitter", 0))
        if left <= 0:
            return
        hunter.extra["glitter"] = left - 1
        self.counts["glitter"] += 1
        t = self.ray_world(origin, direction, GLITTER_RANGE)
        point = [origin[i] + direction[i] * max(0.0, t - 0.5) for i in range(3)]
        self.broadcast({"t": "ppx", "k": "glitter", "p": [round(v, 2) for v in point],
                        "r": GLITTER_R, "id": hunter.pid})
        for prop in self.props_alive():
            lo, hi = self._hull(prop)
            centre = [(lo[i] + hi[i]) / 2.0 for i in range(3)]
            if math.dist(centre, point) <= GLITTER_R + 1.0:
                self._reveal(prop, "glitter", GLITTER_SECONDS)
                self.apply_damage(prop, hunter, GLITTER_DAMAGE, "Glitter Bomb")
        for decoy in list(self.decoys):
            if math.dist(decoy["p"], point) <= GLITTER_R:
                self._pop_decoy(decoy, hunter)
        self._send_me(hunter, force=True)

    def _taunt(self, prop: Player) -> None:
        moment = engine.now()
        if moment < float(prop.extra.get("taunt_at", 0.0)):
            return
        prop.extra["taunt_at"] = moment + TAUNT_COOL
        near = [h for h in self.players.values() if h.team == self.seekers and self.in_play(h)
                and math.dist(h.pos, prop.pos) < 30.0]
        close = any(math.dist(h.pos, prop.pos) < 12.0 for h in near)
        last = len(self.props_alive()) == 1 and self.started_hiders >= 3
        worth = (2 + min(4, len(near))) * (3 if last else 1)
        prop.score += worth
        self.counts["taunts"] += 1
        self._stat(prop, "taunts")
        self.badge(prop, "pp_taunts")
        if close:
            self._stat(prop, "close")
            self.badge(prop, "pp_daredevil")
            self._event("pp_taunt", prop, prop.team, what=self._place(prop.pos))
        self._squeak(prop, "taunt")
        self._lead(prop.pos, 8.0, self.seekers, "taunt")
        # a taunt beside the cat sends her packing
        if self.cat and math.dist(self.cat["p"], prop.pos) < CAT_SHOO:
            self._cat_shoo(prop)
        self._send_me(prop, force=True)

    def _squeak(self, prop: Player, why: str) -> None:
        self.broadcast({"t": "ppx", "k": "taunt", "id": prop.pid, "why": why,
                        "p": [round(v, 2) for v in prop.pos],
                        "n": self.rng.randrange(8)})

    def _decoy(self, prop: Player) -> None:
        left = int(prop.extra.get("decoys", 0))
        if left <= 0 or not prop.grounded:
            return
        key = prop.extra.get("dis") or self.starter
        q = int(prop.extra.get("q", 0))
        size = hull_size(self.kinds, key, q)
        lo, hi = hull_box(prop.pos, size)
        prop.extra["decoys"] = left - 1
        self.decoy_seq += 1
        decoy = {"id": self.decoy_seq, "k": key, "q": q, "p": [round(v, 2) for v in prop.pos],
                 "lo": lo, "hi": hi, "owner": prop.pid}
        self.decoys.append(decoy)
        self.broadcast({"t": "ppx", "k": "decoy", "d": self._decoy_entry(decoy)})
        self._send_me(prop, force=True)

    def _decoy_entry(self, decoy: Dict[str, Any]) -> List[Any]:
        return [decoy["id"], decoy["k"], decoy["p"][0], decoy["p"][1], decoy["p"][2], decoy["q"]]

    def _decoy_list(self) -> List[List[Any]]:
        return [self._decoy_entry(d) for d in self.decoys]

    def _scurry(self, prop: Player) -> None:
        moment = engine.now()
        if moment < float(prop.extra.get("scurry_at", 0.0)):
            return
        prop.extra["scurry_at"] = moment + SCURRY_COOL
        prop.extra["scurry_until"] = moment + SCURRY_SECONDS
        self.broadcast({"t": "ppx", "k": "scurry", "id": prop.pid})
        self._send_me(prop, force=True)

    # ============================================================ hitting
    def can_hurt(self, attacker: Player, victim: Player) -> bool:
        if not super().can_hurt(attacker, victim):
            return False
        return attacker.team == self.seekers and victim.team == self.hiders

    def hostiles_for(self, player: Player):
        """A seeking bot shoots at what it suspects, nothing else; hiders
        shoot nobody."""
        if self.phase != "active" or not self.in_play(player) or self.is_prop(player):
            return
        mind = self._mind(player)
        moment = engine.now()
        for pid, until in list((mind.get("sus") or {}).items()):
            if until < moment:
                mind["sus"].pop(pid, None)
                continue
            prop = self.players.get(pid)
            if prop is not None and self.in_play(prop) and prop.team == self.hiders:
                yield prop

    def aim_heights(self, target) -> Optional[Tuple[float, float]]:
        if isinstance(target, Player) and target.team == self.hiders and target.extra.get("dis"):
            lo, hi = self._hull(target)
            h = hi[1] - lo[1]
            return (h * 0.45, h * 0.7)
        return None

    def after_kill(self, killer: Optional[Player], victim: Player, weapon: str) -> None:
        moment = engine.now()
        if victim.team != self.hiders:
            return
        # a found hider is out of this round, watching the rest
        victim.respawn_at = NEVER
        victim.extra["out"] = True
        self.counts["found"] += 1
        key = victim.extra.get("dis") or self.starter
        self.broadcast({"t": "ppx", "k": "found", "id": victim.pid,
                        "p": [round(v, 2) for v in victim.pos], "what": key,
                        "by": killer.username if killer else ""})
        self.broadcast({"t": "ppd", "id": victim.pid, "k": "", "q": 0})
        reveal = self.reveals.pop(victim.pid, None)
        if killer is not None and killer.team == self.seekers:
            killer.score += 10
            self._stat(killer, "found")
            self.badge(killer, "pp_found")
            if reveal and moment - reveal["at"] <= REVEAL_FIND + reveal["for"]:
                stat = {"cat": "pp_cat", "dark": "pp_dark", "sale": "pp_sale",
                        "alarm": "pp_alarm"}.get(reveal["why"])
                if stat:
                    self.badge(killer, stat)
                    self._stat(killer, reveal["why"])
            if self.dark.get("on") and self.twist == "blackout":
                self.badge(killer, "pp_dark")
            self._event("pp_found", killer, killer.team, victim=victim.username,
                        what=self.kinds.get(key, {}).get("name", "a prop"),
                        where=self._place(victim.pos))
        left = self.props_alive()
        if len(left) == 1 and self.started_hiders >= 3 and not self.last_called:
            self.last_called = True
            last = left[0]
            self.system_message("One hider left: %s, somewhere in %s!" % (
                last.username, self.area["name"]))
            last.send({"t": "ppx", "k": "last"})
            self._event("pp_last", last, last.team)
        self._broadcast_state()

    # ============================================================== rounds
    def on_live(self) -> None:
        moment = engine.now()
        self.set_dynamic_group(self.pen_key, False)
        self.started_hiders = len(self.props_alive())
        self.creak_at = moment + max(0.0, self.ROUND_SECONDS - CREAK_LEFT)
        if self.twist == "blackout":
            self.dark["next"] = moment + self.rng.uniform(*DARK_EVERY) * 0.6
        elif self.twist == "sale":
            self.sale["next"] = moment + self.rng.uniform(*SALE_EVERY) * 0.6
        self.broadcast({"t": "ppx", "k": "release"})
        self.system_message("Ready or not, here they come! %s are out of the pen." %
                            self.team_name(self.seekers))
        self._event("pp_release", None, self.seekers)
        if not self.started_hiders:
            self.finish_round(self.seekers, "nobody hid")

    def round_tick(self, dt: float, moment: float) -> None:
        props = self.props_alive()
        for prop in props:
            self._track_motion(prop, moment)
        if self.started_hiders and not props:
            self.finish_round(self.seekers, "found")
            return
        # every hider still standing earns a little for every few seconds
        if int(moment * 4) % 16 == 0 and int((moment - dt) * 4) % 16 != 0:
            for prop in props:
                prop.score += 1
                self._stat(prop, "alive", 4.0)
        self._decoy_bumps()
        self._creak(props, moment)
        self._twist(props, dt, moment)
        for pid, rev in list(self.reveals.items()):
            if moment > rev["until"] + REVEAL_FIND:
                self.reveals.pop(pid, None)

    def setup_tick(self, dt: float, moment: float) -> None:
        for prop in self.props_alive():
            self._track_motion(prop, moment)

    def _track_motion(self, prop: Player, moment: float) -> None:
        """Half a second at a time: how far has this hider gone?"""
        if moment - float(prop.extra.get("last_at", 0.0)) < 0.5:
            return
        last = prop.extra.get("last_pos") or list(prop.pos)
        moved = math.hypot(prop.pos[0] - last[0], prop.pos[2] - last[2])
        if moved > MOVING * 0.5 or abs(prop.pos[1] - last[1]) > 0.8:
            prop.extra["moved_at"] = moment
        prop.extra["last_pos"] = list(prop.pos)
        prop.extra["last_at"] = moment

    def moving(self, prop: Player) -> bool:
        return engine.now() - float(prop.extra.get("moved_at", -9.0)) < 0.8

    def _decoy_bumps(self) -> None:
        """A seeker who walks into a decoy finds out the hard way."""
        if not self.decoys:
            return
        for hunter in self.players.values():
            if hunter.team != self.seekers or not self.in_play(hunter):
                continue
            for decoy in list(self.decoys):
                lo, hi = decoy["lo"], decoy["hi"]
                if lo[0] - 1.2 < hunter.pos[0] < hi[0] + 1.2 and \
                        lo[2] - 0.9 < hunter.pos[2] < hi[2] + 0.9 and \
                        lo[1] - 2.0 < hunter.pos[1] < hi[1]:
                    self._pop_decoy(decoy, hunter)

    def _creak(self, props: List[Player], moment: float) -> None:
        if not self.creak_at or moment < self.creak_at or not props:
            return
        self.creak_at = moment + CREAK_EVERY
        self.broadcast({"t": "ppx", "k": "creak"})
        for prop in props:
            self._squeak(prop, "creak")
            self._lead(prop.pos, 10.0, self.seekers, "creak")

    def time_up(self) -> None:
        if self.props_alive():
            self.finish_round(self.hiders, "time")
        else:
            self.finish_round(self.seekers, "found")

    def leader(self) -> str:
        return self.hiders if self.props_alive() else self.seekers

    def headline(self, winner: str, reason: str) -> str:
        if reason == "found":
            return "%s found everybody" % self.team_name(winner)
        if reason == "time":
            n = len(self.props_alive())
            return "%s hid it out (%d left)" % (self.team_name(winner), n)
        if reason == "nobody hid":
            return "nobody hid"
        return super().headline(winner, reason)

    # ============================================================= twists
    def _twist(self, props: List[Player], dt: float, moment: float) -> None:
        if self.twist == "cat":
            self._cat_tick(props, dt, moment)
        elif self.twist == "blackout":
            self._dark_tick(moment)
        elif self.twist == "sale":
            self._sale_tick(props, moment)
        elif self.twist == "alarm":
            self._spot_tick(props, dt, moment)

    def _reveal(self, prop: Player, why: str, seconds: float) -> None:
        moment = engine.now()
        self.reveals[prop.pid] = {"why": why, "at": moment, "until": moment + seconds,
                                  "for": seconds}
        self.broadcast({"t": "ppx", "k": "reveal", "id": prop.pid, "why": why,
                        "for": seconds})
        self._lead(prop.pos, 2.0, self.seekers, why, seen=prop.pid)
        mind = self._mind(prop)
        mind["exposed"] = moment

    # ---- the cat
    def _cat_tick(self, props: List[Player], dt: float, moment: float) -> None:
        cat = self.cat
        if not cat:
            return
        if cat["mode"] == "stare":
            target = self.players.get(cat["stare"])
            if target is None or not self.in_play(target) or moment > cat["until"]:
                cat["mode"] = "walk"
                cat["path"] = []
                cat["rest"][cat["stare"]] = moment + 22.0
                cat["stare"] = 0
            else:
                cat["yaw"] = math.atan2(target.pos[0] - cat["p"][0], target.pos[2] - cat["p"][2])
            return
        speed = CAT_SPEED * (1.8 if cat["mode"] == "flee" else 1.0)
        if cat["mode"] == "sit":
            if moment >= cat["until"]:
                cat["mode"] = "walk"
                self._cat_route(moment)
        elif not cat["path"]:
            if cat["mode"] == "walk" and cat.get("walked"):
                cat["mode"] = "sit"
                cat["until"] = moment + self.rng.uniform(3.0, 8.0)
                cat["walked"] = False
            else:
                self._cat_route(moment)
        step = speed * dt
        while step > 0 and cat["path"]:
            nxt = cat["path"][0]
            dx, dy, dz = nxt[0] - cat["p"][0], nxt[1] - cat["p"][1], nxt[2] - cat["p"][2]
            dist = math.hypot(dx, dz)
            if dist <= step:
                cat["p"] = list(nxt)
                cat["path"].pop(0)
                step -= dist
                continue
            cat["p"][0] += dx / dist * step
            cat["p"][2] += dz / dist * step
            cat["p"][1] += dy * min(1.0, step / max(dist, 0.01))
            cat["yaw"] = math.atan2(dx, dz)
            step = 0.0
        if cat["path"]:
            cat["walked"] = True
        if not cat["path"] and cat["mode"] == "flee":
            cat["mode"] = "walk"
        # anything nearby that is not what it seems?
        if cat["mode"] not in ("walk", "sit"):
            return
        for prop in props:
            if cat["rest"].get(prop.pid, 0.0) > moment:
                continue
            if abs(prop.pos[1] - cat["p"][1]) > 4.0:
                continue
            if math.hypot(prop.pos[0] - cat["p"][0], prop.pos[2] - cat["p"][2]) < CAT_SNIFF:
                cat["mode"] = "stare"
                cat["stare"] = prop.pid
                cat["until"] = moment + CAT_STARE
                self.counts["cat"] += 1
                self._reveal(prop, "cat", CAT_STARE)
                self.broadcast({"t": "ppx", "k": "cat", "id": prop.pid,
                                "p": [round(v, 2) for v in prop.pos]})
                self._event("pp_cat", prop, prop.team, what=self._place(prop.pos))
                break

    def _cat_route(self, moment: float, away_from: Optional[Sequence[float]] = None) -> None:
        cat = self.cat
        nav = getattr(self.host, "nav", None)
        spots = self.cat_spots
        if not spots:
            return
        if away_from is not None:
            far = sorted(spots, key=lambda s: -math.dist(s, away_from))
            goal = far[0]
        else:
            choices = [i for i in range(len(spots)) if i != cat.get("goal")]
            cat["goal"] = self.rng.choice(choices) if choices else 0
            goal = spots[cat["goal"]]
            # a cat knows where the people are: half the time she wanders off
            # towards one of the hiders rather than round her usual spots
            near = [p for p in self.props_alive() if cat["rest"].get(p.pid, 0.0) <= moment]
            if near and self.rng.random() < 0.5:
                goal = list(self.rng.choice(near).pos)
        if nav is None or not nav.ready:
            cat["path"] = [list(goal)]
            return
        start = nav.nearest(cat["p"], 3)
        end = nav.nearest(goal, 3)
        if start < 0 or end < 0:
            cat["path"] = [list(goal)]
            return
        nodes = nav.astar(start, end, 2500) or []
        if not nodes:
            # nowhere to walk to from here: she slips off to the goal unseen
            cat["p"] = list(goal)
            cat["path"] = []
            return
        cat["path"] = [nav.point(n) for n in nodes] + [list(goal)]

    def _cat_shoo(self, prop: Player) -> None:
        cat = self.cat
        cat["mode"] = "flee"
        cat["rest"][prop.pid] = engine.now() + 30.0
        cat["stare"] = 0
        self._cat_route(engine.now(), away_from=prop.pos)
        self.broadcast({"t": "ppx", "k": "hiss", "p": [round(v, 2) for v in cat["p"]]})

    # ---- the power cut
    def _dark_tick(self, moment: float) -> None:
        dark = self.dark
        if dark["on"]:
            if moment >= dark["until"]:
                dark["on"] = False
                dark["next"] = moment + self.rng.uniform(*DARK_EVERY)
                self.broadcast({"t": "ppx", "k": "lights", "on": True})
                self._broadcast_state()
            return
        if dark["warn"]:
            if moment >= dark["warn"]:
                dark["warn"] = 0.0
                dark["on"] = True
                dark["until"] = moment + DARK_SECONDS
                self.counts["dark"] += 1
                self.broadcast({"t": "ppx", "k": "lights", "on": False, "for": DARK_SECONDS})
                self._event("pp_dark", None, self.seekers)
                self._broadcast_state()
            return
        if moment >= dark["next"]:
            dark["warn"] = moment + DARK_WARN
            self.broadcast({"t": "ppx", "k": "flicker", "in": DARK_WARN})

    # ---- the flash sale
    def _sale_tick(self, props: List[Player], moment: float) -> None:
        sale = self.sale
        if sale["until"]:
            if moment >= sale["until"]:
                sale.update({"kind": "", "until": 0.0, "next": moment + self.rng.uniform(*SALE_EVERY)})
                self._broadcast_state()
                return
            for prop in props:
                if prop.extra.get("dis") == sale["kind"] and prop.pid not in self.reveals:
                    self._reveal(prop, "sale", max(1.0, sale["until"] - moment))
            return
        if sale["warn"]:
            if moment >= sale["warn"]:
                sale["warn"] = 0.0
                sale["until"] = moment + SALE_SECONDS
                tagged = [p for p in props if p.extra.get("dis") == sale["kind"]]
                self.counts["sale"] += 1
                for prop in tagged:
                    self._reveal(prop, "sale", SALE_SECONDS)
                self.broadcast({"t": "ppx", "k": "sale_on", "kind": sale["kind"],
                                "name": self.kinds.get(sale["kind"], {}).get("name", ""),
                                "n": len(tagged)})
                self._event("pp_sale", None, self.seekers,
                            what=self.kinds.get(sale["kind"], {}).get("name", ""))
                self._broadcast_state()
            return
        if moment >= sale["next"]:
            worn = [p.extra.get("dis") for p in props if p.extra.get("dis")]
            pool = worn if worn and self.rng.random() < 0.5 else list(self.kinds)
            if not pool:
                sale["next"] = moment + 20.0
                return
            sale["kind"] = self.rng.choice(pool)
            sale["warn"] = moment + SALE_WARN
            self.broadcast({"t": "ppx", "k": "sale_warn", "kind": sale["kind"],
                            "name": self.kinds.get(sale["kind"], {}).get("name", ""),
                            "in": SALE_WARN})
            self._broadcast_state()

    # ---- the searchlight
    def _spot_tick(self, props: List[Player], dt: float, moment: float) -> None:
        spot = self.spot
        if not spot:
            return
        path = self.sweep
        a, b = path[spot["i"]], path[(spot["i"] + 1) % len(path)]
        seg = math.hypot(b[0] - a[0], b[2] - a[2]) or 1.0
        spot["f"] += SPOT_SPEED * dt / seg
        while spot["f"] >= 1.0:
            spot["f"] -= 1.0
            spot["i"] = (spot["i"] + 1) % len(path)
            a, b = path[spot["i"]], path[(spot["i"] + 1) % len(path)]
            seg = math.hypot(b[0] - a[0], b[2] - a[2]) or 1.0
        f = spot["f"]
        spot["p"] = [a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f]
        for prop in props:
            if prop.pid in self.reveals or not self.moving(prop):
                continue
            if abs(prop.pos[1] - spot["p"][1]) > 6.0:
                continue
            if math.hypot(prop.pos[0] - spot["p"][0], prop.pos[2] - spot["p"][2]) < SPOT_R:
                self.counts["alarm"] += 1
                self._reveal(prop, "alarm", ALARM_SECONDS)
                self.broadcast({"t": "ppx", "k": "alarm", "id": prop.pid,
                                "p": [round(v, 2) for v in prop.pos]})
                self._event("pp_alarm", prop, prop.team, what=self._place(prop.pos))

    # ============================================================ helpers
    def _stat(self, player: Player, key: str, amount: float = 1.0) -> None:
        stats = self.round_stats.setdefault(player.pid, {})
        stats[key] = stats.get(key, 0.0) + amount

    def _mind(self, player: Player) -> Dict[str, Any]:
        mind = player.extra.get("pp_mind")
        if mind is None:
            mind = player.extra["pp_mind"] = {}
        return mind

    def _place(self, pos: Sequence[float]) -> str:
        best, best_d = "", 1e9
        for p, name in self.landmarks:
            d = math.hypot(p[0] - pos[0], p[2] - pos[2]) + abs(p[1] - pos[1]) * 2.0
            if d < best_d:
                best, best_d = name, d
        return best

    def _lead(self, pos: Sequence[float], noise: float, team: str, why: str,
              seen: int = 0) -> None:
        """Something the seekers' bots could have heard or seen."""
        moment = engine.now()
        self.leads.append({"p": [pos[0] + self.rng.uniform(-noise, noise), pos[1],
                                 pos[2] + self.rng.uniform(-noise, noise)],
                           "at": moment, "why": why, "seen": seen})
        self.leads = [l for l in self.leads if moment - l["at"] < 25.0][-24:]

    def _event(self, kind: str, player: Optional[Player], team: str, **extra: Any) -> None:
        moment = engine.now()
        if moment - self.events_said.get(kind, -99.0) < 8.0 and kind not in ("pp_found",):
            return
        self.events_said[kind] = moment
        data = {"by": player.username if player else "", "by_team": player.team if player else "",
                "team": team, "hiders": self.team_name(self.hiders),
                "seekers": self.team_name(self.seekers), "world": self.world_id}
        data.update(extra)
        self.push_event(kind, **data)

    def _disguises(self) -> Dict[str, List[Any]]:
        out = {}
        for p in self.players.values():
            if p.team == self.hiders and self.in_play(p):
                out[str(p.pid)] = [p.extra.get("dis") or self.starter, int(p.extra.get("q", 0))]
        return out

    # ========================================================== the end
    def on_round_over(self, winner: str, reason: str, winners: List[Player]) -> None:
        survivors = self.props_alive() if winner == self.hiders else []
        left = max(0.0, self.round_ends - engine.now()) if self.round_ends else 0.0
        for player in winners:
            self.badge(player, "pp_wins")
            if winner == self.seekers and reason == "found" and left >= 60.0 and \
                    self.started_hiders >= 2:
                self.badge(player, "pp_sweep")
        for prop in survivors:
            prop.score += 50
            self.badge(prop, "pp_survived")
            self.badge(prop, "pp_area_" + self.area_id, 1, "max")
            if len(survivors) == 1 and self.started_hiders >= 3:
                self.badge(prop, "pp_last_stand")
        if winner == self.seekers:
            for player in winners:
                self.badge(player, "pp_area_" + self.area_id, 1, "max")
        self.decoys = []
        self.reveals = {}

    def results_rows(self) -> List[Dict[str, Any]]:
        rows = []
        for p in self.players.values():
            st = self.round_stats.get(p.pid, {})
            hid = p.team == self.hiders
            rows.append({"id": p.pid, "name": p.username, "team": p.team, "score": p.score,
                         "role": "Hider" if hid else "Seeker",
                         "found": int(st.get("found", 0)),
                         "taunts": int(st.get("taunts", 0)),
                         "fate": ("hid it out" if hid and self.in_play(p) else
                                  ("found" if hid else "%d wrong" % int(st.get("wrong", 0))))})
        rows.sort(key=lambda r: (-r["score"], r["name"].lower()))
        return rows

    def result_columns(self) -> List[List[str]]:
        return [["role", "Role"], ["fate", "Fate"], ["found", "Found"],
                ["taunts", "Taunts"], ["score", "Score"]]

    def awards(self, winner: str) -> List[str]:
        out = []
        best: Dict[str, Tuple[int, float]] = {}
        for pid, st in self.round_stats.items():
            for key in ("found", "taunts", "close", "decoy_hits", "disguises", "wrong"):
                if st.get(key, 0) > best.get(key, (0, 0.0))[1]:
                    best[key] = (pid, st[key])
        labels = {"found": ("Eagle Eye", "found %d hiders"),
                  "close": ("Daredevil", "taunted %d times under a seeker's nose"),
                  "taunts": ("Show-Off", "taunted %d times"),
                  "decoy_hits": ("Decoy Duck", "fooled %d seekers with decoys"),
                  "disguises": ("Quick Change", "changed disguise %d times"),
                  "wrong": ("Trigger Happy", "made %d wrong guesses")}
        for key in ("found", "close", "taunts", "decoy_hits", "disguises", "wrong"):
            if key not in best:
                continue
            pid, value = best[key]
            player = self.players.get(pid)
            if player is None or value < 1:
                continue
            title, text = labels[key]
            out.append("%s: %s %s" % (title, player.username, text % int(value)))
        survivors = [p.username for p in self.props_alive()]
        if survivors and winner == self.hiders:
            out.insert(0, "Still hidden: %s" % ", ".join(survivors[:4]))
        return out[:5]

    def result_extra(self, winner: str) -> Dict[str, Any]:
        return {"hiders": self.hiders, "left": len(self.props_alive()),
                "started": self.started_hiders}

    # ============================================================== state
    def _broadcast_state(self) -> None:
        self.broadcast({"t": "pps", "s": self.hud_state().get("pp")})

    def hud_state(self) -> Dict[str, Any]:
        moment = engine.now()
        twist: Dict[str, Any] = {"kind": self.twist}
        if self.twist == "blackout":
            twist.update({"dark": round(max(0.0, self.dark.get("until", 0) - moment), 1)
                          if self.dark.get("on") else 0,
                          "warn": round(max(0.0, self.dark.get("warn", 0) - moment), 1)
                          if self.dark.get("warn") else 0})
        elif self.twist == "sale":
            twist.update({"sale": self.sale.get("kind", ""),
                          "name": self.kinds.get(self.sale.get("kind", ""), {}).get("name", ""),
                          "warn": round(max(0.0, self.sale.get("warn", 0) - moment), 1)
                          if self.sale.get("warn") else 0,
                          "left": round(max(0.0, self.sale.get("until", 0) - moment), 1)
                          if self.sale.get("until") else 0})
        reveals = {str(pid): [r["why"], round(max(0.0, r["until"] - moment), 1)]
                   for pid, r in self.reveals.items() if r["until"] > moment}
        return {"pp": {"hiders": self.hiders, "seekers": self.seekers,
                       "alive": len(self.props_alive()), "started": self.started_hiders,
                       "dis": self._disguises(), "decoys": self._decoy_list(),
                       "reveals": reveals, "twist": twist,
                       "creak": round(max(0.0, self.creak_at - moment), 1)
                       if self.creak_at and self.phase == "active" else 0}}

    def snapshot_extra(self) -> Any:
        out: Dict[str, Any] = {}
        if self.cat:
            c = self.cat
            out["cat"] = [round(c["p"][0], 2), round(c["p"][1], 2), round(c["p"][2], 2),
                          round(c["yaw"], 2), {"walk": 0, "stare": 1, "flee": 2, "sit": 3}[c["mode"]]]
        if self.spot:
            out["spot"] = [round(self.spot["p"][0], 2), round(self.spot["p"][1], 2),
                           round(self.spot["p"][2], 2), SPOT_R]
        return out or None

    def me_state(self, player: Player) -> Dict[str, Any]:
        moment = engine.now()
        out: Dict[str, Any] = {"hiders": self.hiders}
        if self.is_prop(player):
            out.update({"dis": player.extra.get("dis") or "", "q": int(player.extra.get("q", 0)),
                        "decoys": int(player.extra.get("decoys", 0)),
                        "taunt": round(max(0.0, float(player.extra.get("taunt_at", 0)) - moment), 1),
                        "scurry": round(max(0.0, float(player.extra.get("scurry_at", 0)) - moment), 1),
                        "fast": round(max(0.0, float(player.extra.get("scurry_until", 0)) - moment), 1),
                        "rev": (self.reveals.get(player.pid) or {}).get("why", "")})
        else:
            out.update({"sniff": round(max(0.0, float(player.extra.get("sniff_at", 0)) - moment), 1),
                        "glitter": int(player.extra.get("glitter", 0))})
        return out

    def score_row(self, player: Player, row: Dict[str, Any]) -> None:
        st = self.round_stats.get(player.pid, {})
        row["found"] = int(st.get("found", 0))
        row["taunts"] = int(st.get("taunts", 0))
        row["hider"] = player.team == self.hiders

    def describe(self) -> Dict[str, Any]:
        info = super().describe()
        if self.phase == "active":
            info["summary"] = "Round %d · %s · %d of %d hiders left" % (
                max(1, self.round_number), self.area["name"], len(self.props_alive()),
                self.started_hiders)
        return info

    # ======================================================= sleep / wake
    def sleep_extra(self) -> Dict[str, Any]:
        elapsed = 0.0
        if self.phase == "active" and self.round_ends:
            elapsed = 1.0 - max(0.0, self.round_ends - engine.now()) / self.ROUND_SECONDS
        return {"progress": round(max(0.0, min(1.0, elapsed)), 3), "hiders": self.hiders}

    def resume_progress(self, progress: float, state: Dict[str, Any]) -> None:
        """A woken round: some of the hiders have been found already."""
        props = self.props_alive()
        self.rng.shuffle(props)
        gone = int(len(props) * progress * self.rng.uniform(0.3, 0.7))
        for prop in props[:gone]:
            prop.alive = False
            prop.health = 0
            prop.respawn_at = NEVER
            prop.extra["out"] = True
        self.started_hiders = max(self.started_hiders, len(props))

    # =============================================================== bots
    def bot_role(self, brain) -> str:
        if not self.setting("enabled"):
            return "player"
        t = brain.t
        if brain.p.team == self.hiders:
            weights = {"still": 0.3 + (1.0 - t("jumpy", 0.2)) * 0.6 + t("skill", 0.5) * 0.4,
                       "taunter": 0.1 + t("chaos", 0.1) * 1.2 + t("toxicity", 0.1) * 0.8
                       + t("chatty", 0.4) * 0.3,
                       "runner": 0.1 + t("explore", 0.2) * 0.8 + t("jumpy", 0.2) * 0.6}
        else:
            weights = {"seeker": 0.5 + brain.objective * 0.5,
                       "sweeper": 0.1 + t("aggression", 0.5) * 0.7 + t("chaos", 0.1) * 0.6,
                       "sniffer": 0.1 + t("support", 0.2) * 0.9 + self.pct("sniffer") * 0.4}
        roll = brain.rng.random() * sum(weights.values())
        for role, weight in weights.items():
            roll -= weight
            if roll <= 0:
                return role
        return next(iter(weights))

    def bot_goal_weights(self, brain, weights: Dict[str, float]) -> Dict[str, float]:
        if not self.setting("enabled"):
            return weights
        if brain.p.team == self.hiders:
            return {"objective": 1.0}
        weights["objective"] = weights.get("objective", 0.5) * 2.6 + 0.6
        weights["afk"] = 0.0
        weights["revenge"] = 0.0
        weights["follow"] = weights.get("follow", 0.0) * 0.3
        weights["jumpy"] = weights.get("jumpy", 0.0) * 0.4
        return weights

    def bot_urgent(self, brain) -> bool:
        if not self.setting("enabled"):
            return False
        p = brain.p
        if p.team == self.hiders:
            return self.phase in ("setup", "active") and self.in_play(p)
        mind = self._mind(p)
        if self.phase == "setup":
            return True               # counting in the pen, not wandering into its door
        return self.phase == "active" and bool(mind.get("lead"))

    def bot_tick(self, moment: float) -> None:
        """Hiders never fight back, whatever they are hit by."""
        if self.bots is None:
            return
        for brain in self.bots.brains.values():
            if brain.p.team == self.hiders:
                brain.target = None
                brain.revenge = None

    def bot_objective(self, brain) -> None:
        if not self.setting("enabled"):
            return super().bot_objective(brain)
        p = brain.p
        if not self.in_play(p):
            return
        if p.team == self.hiders:
            self._bot_hide(brain)
        else:
            self._bot_seek(brain)

    # ---- hiding
    def _bot_hide(self, brain) -> None:
        p = brain.p
        moment = engine.now()
        mind = self._mind(p)
        if self.phase not in ("setup", "active"):
            return
        spot = mind.get("spot")
        if spot is None:
            spot = self._claim_spot(brain, avoid=mind.get("avoid"))
            if spot is None:
                return
            mind["spot"] = spot
            mind["hidden"] = False
            self.doing(brain, "looking for somewhere to hide")
        target = self.hides[spot]
        dist = math.hypot(p.pos[0] - target[0], p.pos[2] - target[2])
        if not mind.get("hidden"):
            if dist > 2.6 or abs(p.pos[1] - target[1]) > 2.5:
                if not mind.get("fleeing") and self._bot_beam_near(brain, mind):
                    brain.waypoints = []
                    self.doing(brain, "standing still while the searchlight passes")
                    return
                brain.go(target, "hide%d" % spot)
                if mind.get("fleeing") and moment >= float(p.extra.get("scurry_at", 0.0)) \
                        and self.phase == "active":
                    self._scurry(p)
                return
            brain.waypoints = []
            self._bot_pick_disguise(brain, mind)
            mind["hidden"] = True
            mind["fleeing"] = False
            mind["since"] = moment
            mind["next_taunt"] = moment + brain.rng.uniform(12.0, 40.0)
            self.doing(brain, "hiding as %s near %s" % (
                self.kinds.get(p.extra.get("dis") or "", {}).get("name", "something").lower(),
                self._place(p.pos) or "here"))
            return
        # hidden: keep still, now and then taunt, run if found out
        brain.waypoints = []
        if self.phase != "active":
            return
        if self._bot_should_flee(brain, mind, moment):
            self._bot_flee(brain, mind)
            return
        self._bot_dodge_sale(brain, mind, moment)
        if moment >= mind.get("next_taunt", NEVER):
            rate = self.pct("taunt") * (1.6 if brain.role == "taunter" else 0.6)
            hunters = [h for h in self.players.values() if h.team == self.seekers and
                       self.in_play(h)]
            nearest = min((math.dist(h.pos, p.pos) for h in hunters), default=99.0)
            brave = brain.role == "taunter" or brain.t("chaos", 0.1) > 0.5
            if brain.rng.random() < rate and (nearest > 18.0 or brave):
                self._taunt(p)
                self.callout(brain, ["catch me", "lol", "over here", "too slow", "cant find me"],
                             "taunt", chance=0.3, every=40.0)
            mind["next_taunt"] = moment + brain.rng.uniform(14.0, 45.0) / max(0.3, rate + 0.2)
        if int(p.extra.get("decoys", 0)) > 0 and brain.rng.random() < 0.004 * self.pct("decoys") \
                and brain.role != "still":
            self._decoy(p)
            mind["spot"] = None
            mind["hidden"] = False
            mind["avoid"] = list(p.pos)

    def _claim_spot(self, brain, avoid: Optional[Sequence[float]] = None) -> Optional[int]:
        p = brain.p
        if not self.hides:
            return None
        taken = {i for i, pid in self.claims.items() if pid != p.pid and
                 pid in self.players and self.in_play(self.players[pid])}
        far = 0.3 + brain.t("explore", 0.2) * 1.4 + (0.6 if brain.role == "runner" else 0.0)
        # a hider still on its way when the seekers come out is a hider seen:
        # in the countdown it picks somewhere it can reach in time
        moment = engine.now()
        left = max(0.0, self.phase_until - moment) if self.phase == "setup" else 0.0
        best, best_s = None, -1e9
        for i, h in enumerate(self.hides):
            if i in taken:
                continue
            d = math.dist(h, p.pos)
            score = brain.rng.uniform(0.0, 60.0) + min(d, 160.0) * (far - 0.5) * 0.4
            walk = d * 1.4 / BOT_WALK
            if self.phase == "setup" and walk > left - 4.0:
                score -= 12.0 * (walk - left + 4.0)
            if avoid is not None and math.dist(h, avoid) < 30.0:
                score -= 80.0
            for hunter in self.players.values():
                if hunter.team == self.seekers and self.in_play(hunter) and \
                        math.dist(hunter.pos, h) < 30.0 and self.phase == "active":
                    score -= 50.0
            if score > best_s:
                best, best_s = i, score
        if best is not None:
            for i, pid in list(self.claims.items()):
                if pid == p.pid:
                    self.claims.pop(i)
            self.claims[best] = p.pid
        return best

    def _bot_pick_disguise(self, brain, mind: Dict[str, Any]) -> None:
        """Become something that belongs here and fits here."""
        p = brain.p
        smart = self.pct("hide_smart") * (0.5 + brain.skill * 0.8)
        near = [e for e in self._decor_near(p.pos[0], p.pos[2], 22.0)
                if abs(e["p"][1] - p.pos[1]) < 1.6]
        if not near:
            near = list(self._decor_near(p.pos[0], p.pos[2], 40.0))
        if not near and self.decor:
            near = [brain.rng.choice(self.decor)]
        options = []
        for entry in near:
            size = hull_size(self.kinds, entry["k"], entry["q"])
            if not self.hull_fits(p.pos[0], p.pos[1], p.pos[2], size):
                continue
            w, h, d = size
            if brain.role == "runner" and (w > 2.6 or d > 2.6):
                continue
            same = sum(1 for e in near if e["k"] == entry["k"])
            score = brain.rng.random() * (1.2 - smart) + smart * (same * 0.25 +
                                                                   1.0 / (1.0 + math.dist(entry["p"], p.pos) / 8.0))
            if brain.role == "taunter" or brain.t("chaos", 0.1) > 0.6:
                score += brain.rng.random() * 0.8
            options.append((score, entry))
        if not options:
            return
        options.sort(key=lambda o: -o[0])
        entry = options[0][1]
        self._become(p, entry["k"], entry["q"], quiet=True)

    def _bot_should_flee(self, brain, mind: Dict[str, Any], moment: float) -> bool:
        p = brain.p
        still = self.pct("stillness") * (1.4 if brain.role == "still" else 0.9)
        shot = moment - float(mind.get("shot_at", -99.0)) < 1.5
        exposed = moment - float(mind.get("exposed", -99.0)) < 1.5
        cat = self.cat and self.cat.get("stare") == p.pid
        if not (shot or exposed or cat):
            if brain.role == "runner" and moment - mind.get("since", moment) > \
                    brain.rng.uniform(40.0, 90.0) * (0.6 + still):
                return brain.rng.random() < 0.008
            return False
        size = hull_size(self.kinds, p.extra.get("dis") or self.starter, int(p.extra.get("q", 0)))
        if size[0] > 2.7 or size[2] > 2.7:
            return False              # too big to run: stay and pray
        chance = (0.75 - still * 0.55) * (1.3 if shot else 0.8)
        return brain.rng.random() < chance

    def _bot_flee(self, brain, mind: Dict[str, Any]) -> None:
        p = brain.p
        mind["avoid"] = list(p.pos)
        mind["spot"] = self._claim_spot(brain, avoid=p.pos)
        mind["hidden"] = False
        mind["fleeing"] = True
        mind["shot_at"] = -99.0
        mind["exposed"] = -99.0
        self.doing(brain, "running for a new hiding place")
        self.callout(brain, ["rumbled", "run", "moving!", "they found me"], "flee", chance=0.4,
                     team=True)
        if int(p.extra.get("decoys", 0)) > 0 and brain.rng.random() < self.pct("decoys"):
            self._decoy(p)

    def _bot_beam_near(self, brain, mind: Dict[str, Any]) -> bool:
        """A hider with its wits about it stands still while the museum's
        searchlight passes over or close by, rather than walk through it."""
        spot = self.spot
        if not spot or self.phase != "active":
            return False
        p, sp = brain.p, spot.get("p") or []
        if len(sp) < 3 or abs(p.pos[1] - sp[1]) > 6.0:
            return False
        if math.hypot(p.pos[0] - sp[0], p.pos[2] - sp[2]) > SPOT_R + 5.0:
            return False
        if "beam_wits" not in mind:
            mind["beam_wits"] = brain.rng.random() < 0.2 + 0.75 * self.pct("twist")
        return bool(mind["beam_wits"])

    def _bot_dodge_sale(self, brain, mind: Dict[str, Any], moment: float) -> None:
        if self.twist != "sale" or not self.sale.get("warn"):
            return
        p = brain.p
        if p.extra.get("dis") != self.sale.get("kind") or mind.get("dodged") == self.sale["warn"]:
            return
        mind["dodged"] = self.sale["warn"]
        if brain.rng.random() > self.pct("twist") * (0.5 + brain.skill * 0.6):
            return
        others = [e for e in self._decor_near(p.pos[0], p.pos[2], 14.0)
                  if e["k"] != self.sale["kind"] and abs(e["p"][1] - p.pos[1]) < 1.6]
        for entry in sorted(others, key=lambda e: math.dist(e["p"], p.pos)):
            if self.hull_fits(p.pos[0], p.pos[1], p.pos[2],
                              hull_size(self.kinds, entry["k"], entry["q"])):
                self._become(p, entry["k"], entry["q"], quiet=True)
                return

    # ---- seeking
    def _bot_seek(self, brain) -> None:
        p = brain.p
        moment = engine.now()
        mind = self._mind(p)
        if self.phase == "setup":
            self.doing(brain, "counting to forty in the pen")
            return
        if self.phase != "active":
            return
        if moment - self.live_since < 6.0:
            self.callout(brain, ["ready or not", "here we come", "lets find them", "spread out"],
                         "release", chance=0.35, every=120.0)
        self._bot_perceive(brain, mind, moment)
        lead = mind.get("lead")
        if lead is not None and moment - lead["at"] > 18.0:
            mind["lead"] = lead = None
        if lead is None:
            lead = self._bot_take_lead(brain, mind, moment)
        # the sniffer, when there is nothing better to go on
        sniff_rate = self.pct("sniffer") * (1.8 if brain.role == "sniffer" else 0.5)
        if lead is None and moment >= float(p.extra.get("sniff_at", 0.0)) and \
                brain.rng.random() < sniff_rate * 0.25:
            self._sniff(p)
            lead = self._bot_take_lead(brain, mind, moment)
        if lead is not None:
            d = math.hypot(p.pos[0] - lead["p"][0], p.pos[2] - lead["p"][2])
            if d > 7.0:
                brain.go(lead["p"], "lead%d" % int(lead["at"] * 10))
                self.callout(brain, LEAD_LINES.get(lead["why"], LEAD_LINES["taunt"]),
                             "lead" + lead["why"], chance=0.45, every=30.0, team=True)
                self.doing(brain, "following a %s near %s" % (
                    {"taunt": "taunt", "sniff": "sniff", "creak": "creak", "cat": "staring cat",
                     "sale": "price tag", "alarm": "alarm", "glitter": "glint"}.get(
                         lead["why"], "noise"), self._place(lead["p"]) or "here"))
                return
            # at the spot: guess at what is around, glitter it, or move on
            self._bot_guess(brain, mind, moment, lead["p"])
            if int(p.extra.get("glitter", 0)) > 0 and brain.rng.random() < 0.08 * (
                    1.0 + brain.t("aggression", 0.5)):
                self._bot_glitter(brain, lead["p"])
            if moment - lead.get("arrived", moment) > 6.0:
                mind["lead"] = None
            lead.setdefault("arrived", moment)
            return
        # nothing to go on: sweep the place, room by room
        search = mind.get("search")
        if search is None or search >= len(self.searches):
            search = self._bot_pick_search(brain)
            mind["search"] = search
            mind["search_at"] = moment
        if search is None:
            return super().bot_objective(brain)
        point, name = self.searches[search]
        if math.dist(point, p.pos) > 8.0 and moment - mind.get("search_at", moment) < 40.0:
            brain.go(point, "search%d" % search)
            self.doing(brain, "searching %s" % (name or "the place"))
            return
        self._bot_guess(brain, mind, moment, p.pos)
        if moment - mind.get("search_at", moment) > 10.0 + brain.rng.uniform(0.0, 8.0):
            self.searched[search] = moment
            mind["search"] = None

    def _bot_pick_search(self, brain) -> Optional[int]:
        if not self.searches:
            return None
        moment = engine.now()
        best, best_s = None, -1e9
        for i, (point, _) in enumerate(self.searches):
            age = moment - self.searched.get(i, -300.0)
            d = math.dist(point, brain.p.pos)
            score = min(age, 240.0) - d * 0.35 + brain.rng.uniform(0.0, 40.0)
            if score > best_s:
                best, best_s = i, score
        if best is not None:
            self.searched[best] = moment
        return best

    def _bot_take_lead(self, brain, mind: Dict[str, Any], moment: float) -> Optional[Dict[str, Any]]:
        p = brain.p
        heard = 45.0 + self.pct("twist") * 30.0
        best, best_d = None, heard
        for lead in self.leads:
            if moment - lead["at"] > 12.0:
                continue
            d = math.dist(lead["p"], p.pos)
            if lead["why"] in ("cat", "sale", "alarm", "glitter") and \
                    brain.rng.random() > self.pct("twist"):
                continue
            if d < best_d:
                best, best_d = lead, d
        if best is None:
            return None
        lead = dict(best)
        mind["lead"] = lead
        if best.get("seen"):
            mind.setdefault("sus", {})[best["seen"]] = moment + 8.0
        return lead

    def _bot_perceive(self, brain, mind: Dict[str, Any], moment: float) -> None:
        """Does anything here look like a person?"""
        p = brain.p
        if moment < mind.get("look_at", 0.0):
            return
        mind["look_at"] = moment + 0.5
        eyes = self.pct("eyes") * (0.5 + brain.skill)
        dark = self.twist == "blackout" and self.dark.get("on")
        eye = [p.pos[0], p.pos[1] + EYE_HEIGHT, p.pos[2]]
        sus = mind.setdefault("sus", {})
        for prop in self.props_alive():
            d = math.dist(prop.pos, p.pos)
            if d > 55.0:
                continue
            dx, dz = prop.pos[0] - p.pos[0], prop.pos[2] - p.pos[2]
            off = abs((math.atan2(dx, dz) - p.yaw + math.pi) % (2 * math.pi) - math.pi)
            if off > 1.3 and d > 8.0:
                continue
            lo, hi = self._hull(prop)
            if not self._sees_box(eye, lo, hi):
                continue
            chance = 0.015
            if self.moving(prop):
                chance += 0.35
            if prop.pid in self.reveals:
                chance += 0.7
            if not self._fits_in(prop):
                chance += 0.12
            if prop.extra.get("dis") == self.starter:
                chance += 0.06
            chance *= eyes * max(0.15, 1.0 - d / 60.0)
            if dark:
                chance *= 0.25
            if brain.rng.random() < chance:
                sus[prop.pid] = moment + 10.0
                if brain.rng.random() < 0.2:
                    what = str(self.kinds.get(prop.extra.get("dis") or "", {}).get("name", "prop")).lower()
                    self.callout(brain, ["that %s moved" % what, "sus %s" % what,
                                         "%s looks off" % what], "spotted", chance=0.5, team=True)

    def _fits_in(self, prop: Player) -> bool:
        """Is there another of what this hider is pretending to be nearby?"""
        key = prop.extra.get("dis") or ""
        return any(e["k"] == key for e in self._decor_near(prop.pos[0], prop.pos[2], 20.0))

    def _bot_guess(self, brain, mind: Dict[str, Any], moment: float,
                   around: Sequence[float]) -> None:
        """Shoot something suspicious-looking -- it costs, so not too often."""
        p = brain.p
        if moment < mind.get("guess_at", 0.0) or p.health < 45.0 or brain.target is not None:
            return
        rate = self.pct("guess") * (1.7 if brain.role == "sweeper" else 0.7) * \
            (0.5 + brain.t("aggression", 0.5))
        mind["guess_at"] = moment + brain.rng.uniform(1.2, 3.0)
        if brain.rng.random() > rate * 0.5:
            return
        eye = [p.pos[0], p.pos[1] + EYE_HEIGHT, p.pos[2]]
        candidates = []
        for entry in self._decor_near(around[0], around[2], 14.0):
            if math.dist(entry["p"], p.pos) > 30.0:
                continue
            if self._sees_box(eye, entry["lo"], entry["hi"]):
                candidates.append(entry)
        # a hider pretending to be one of these is as good a guess as any
        for prop in self.props_alive():
            if math.dist(prop.pos, around) < 14.0 and math.dist(prop.pos, p.pos) < 30.0:
                lo, hi = self._hull(prop)
                if self._sees_box(eye, lo, hi) and brain.rng.random() < 0.5 + brain.skill * 0.3:
                    candidates.append({"lo": lo, "hi": hi, "prop": prop.pid})
        if not candidates:
            return
        pick = brain.rng.choice(candidates)
        centre = [(pick["lo"][i] + pick["hi"][i]) / 2.0 for i in range(3)]
        delta = [centre[i] - eye[i] for i in range(3)]
        dist = math.sqrt(sum(v * v for v in delta)) or 1.0
        err = brain.aim_error * 0.6
        yaw = math.atan2(delta[0], delta[2]) + brain.rng.gauss(0, err)
        pitch = math.asin(max(-1.0, min(1.0, delta[1] / dist))) + brain.rng.gauss(0, err * 0.7)
        cp = math.cos(pitch)
        p.yaw, p.pitch = yaw, pitch
        if p.slot != 0 or p.stowed:
            self.handle_slot(p, {"i": 0})
        self.handle_fire(p, {"d": [math.sin(yaw) * cp, math.sin(pitch), math.cos(yaw) * cp]})
        if pick.get("prop"):
            mind.setdefault("sus", {})[pick["prop"]] = moment + 6.0

    def _bot_glitter(self, brain, point: Sequence[float]) -> None:
        p = brain.p
        eye = [p.pos[0], p.pos[1] + EYE_HEIGHT, p.pos[2]]
        delta = [point[0] - eye[0], point[1] + 1.0 - eye[1], point[2] - eye[2]]
        dist = math.sqrt(sum(v * v for v in delta)) or 1.0
        self._glitter(p, [v / dist for v in delta], eye)

    def bot_context(self) -> List[str]:
        lines = ["%s are hiding (as props) and %s are seeking this round." % (
            self.team_name(self.hiders), self.team_name(self.seekers))]
        if self.phase == "active":
            lines.append("%d of %d hiders are still hidden." % (len(self.props_alive()),
                                                                self.started_hiders))
        twist = {"cat": "Mittens the cat stares at disguised hiders.",
                 "blackout": "The lights keep going out in the toy shop.",
                 "sale": "Flash sales put price tags on every hider of one kind.",
                 "alarm": "A searchlight sets off the alarm on hiders who move in it."}.get(self.twist)
        if twist:
            lines.append(twist)
        return lines

    def bot_me(self, brain) -> Dict[str, Any]:
        info = super().bot_me(brain)
        p = brain.p
        if p.team == self.hiders:
            what = self.kinds.get(p.extra.get("dis") or "", {}).get("name", "")
            info["context"].append("you are hiding this round%s" % (
                (", disguised as a %s" % what.lower()) if what else ""))
        else:
            info["context"].append("you are seeking this round: find the hiders")
            info["found"] = int(self.round_stats.get(p.pid, {}).get("found", 0))
        return info

    def bot_spread(self, players: List[Player]) -> None:
        """A woken round: hiders already in their hiding places, seekers out
        looking."""
        free = list(range(len(self.hides)))
        self.rng.shuffle(free)
        for player in players:
            if player.brain is None:
                continue
            brain = player.brain
            if player.team == self.hiders and self.in_play(player) and free:
                spot = free.pop()
                player.pos = list(self.hides[spot])
                brain.on_spawn()
                mind = self._mind(player)
                mind.update({"spot": spot, "hidden": True, "since": engine.now(),
                             "next_taunt": engine.now() + 20.0})
                self.claims[spot] = player.pid
                self._bot_pick_disguise(brain, mind)
            elif player.team == self.seekers and self.searches and player.alive:
                point, _ = self.rng.choice(self.searches)
                player.pos = list(point)
                brain.on_spawn()
            else:
                brain.on_spawn()

    # ============================================================== tests
    def observe(self) -> Dict[str, Any]:
        props = self.props_alive()
        return {"phase": self.phase, "area": self.area_id, "hiders": self.hiders,
                "alive": len(props),
                "disguised": sum(1 for p in props if (p.extra.get("dis") or self.starter)
                                 != self.starter),
                "counts": dict(self.counts)}

    def selftest(self, result: Dict[str, Any]) -> List[Tuple[str, bool, Any]]:
        obs = result.get("observations") or []
        live = [o for o in obs if o["phase"] == "active" and o["alive"]]
        disguised = max((o["disguised"] / max(1, o["alive"]) for o in live), default=0.0)
        counts = self.counts
        twists = {k: counts.get(k, 0) for k in ("cat", "dark", "sale", "alarm")}
        seen = {o["area"] for o in obs}
        return [
            ("hiders take disguises from the room they hide in", disguised >= 0.6,
             "%.0f%% at best" % (disguised * 100)),
            ("seekers find hiders", counts.get("found", 0) > 0, counts),
            ("hiders taunt", counts.get("taunts", 0) > 0, counts.get("taunts")),
            ("seekers guess, sniff and glitter",
             counts.get("wrong", 0) + counts.get("sniffs", 0) + counts.get("glitter", 0) > 0,
             counts),
            ("the areas' twists happen", sum(twists.values()) > 0 or not seen & {
                "grandma", "toyshop", "megamart", "museum"}, twists),
        ]


WORLD_CLASS = PropPanicWorld
