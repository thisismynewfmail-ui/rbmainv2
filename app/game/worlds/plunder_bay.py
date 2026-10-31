"""Plunder Bay: a treasure haul between two pirate crews
(app/models/event_worlds/plunder_bay.py).

Two crews -- the **Scarlet Corsairs** and the **Azure Buccaneers** -- moor
their galleons at either end of an island and race to carry its treasure
into their own ship's hold (the ``hold`` mark on each main deck).  The
first crew to 300 doubloons' worth, or the richer one when the clock runs
out, wins the haul.

**Treasure** is carried one piece at a time: walk over it to pick it up.

=========  =====  ========================================================
pouch        2    a pouch of doubloons; full speed, weapons in hand
gold bar     4    a little slower
jewel        6    a little slower
chest       12    dug up where X marks the spot (hold E); both hands, slow
idol        25    rises on its altar two minutes from the end; both hands,
                  and everybody can see who has it
=========  =====  ========================================================

Whoever is cut down drops what they carry where they fall.  R tosses it
(a crewmate can catch it in the air -- or anybody else can), and treasure
that lands on a hold's hatch is banked for that crew.  Empty-handed in the
other crew's hold, hold E for four seconds to steal a gold bar's worth out
of it.

**Arms**: everybody fights with their own hotbar -- whatever they set on it
-- against the other crew and the island's own (redcoats, the kraken); a
chest or the idol takes both hands, and gives the hotbar back when it goes.
Both ships carry two deck cannons: E at one of your own fires a shell
where you are looking, within its arc -- it lands a moment later where the
ring shows, knocks everybody about and the treasure out of their hands.

**The sea**: wading slows you, deep water more.  Each place has a twist
(``extra["twist"]``), warned a few seconds ahead:

* Skull Cove -- **low tide**: the sea falls in two steps, the lagoon floor
  is uncovered and treasure lies on it -- until the tide comes back and
  washes what is left away.
* Coral Reef -- **the kraken**: six tentacles rise round the wreck and slam
  down on whoever comes near (a ring shows where); cut one down and it
  leaves a jewel.
* Port Royale -- **the redcoats**: the fort's garrison marches out on
  patrol and shoots any pirate it sees, carriers first; a downed redcoat
  drops his purse.
* Doubloon Isle -- **the eruption**: lava bombs rain on the island (rings
  again) and the volcano spews gold all over it.  The lava in the trenches
  is death at any time.

The tentacles and the redcoats are the world's own creatures (:class:`Npc`):
``hostiles_for`` lists them and ``entity`` resolves them, so the bots see,
chase and shoot them like anybody else.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence, Tuple

from ...models import catalog
from .. import instance as engine
from ..instance import EYE_HEIGHT, GRAVITY, Player, normalise, ray_aabb
from ..maps.events import plunder_bay as pb_map
from .arena import NEVER, ArenaWorld

TARGET = 300
KINDS = ("pouch", "bar", "gem", "chest", "idol")
KIND_CODE = {k: i for i, k in enumerate(KINDS)}
VALUE = {"pouch": 2, "bar": 4, "gem": 6, "chest": 12, "idol": 25}
NAMES = {"pouch": "a pouch of doubloons", "bar": "a gold bar", "gem": "a jewel",
         "chest": "a chest", "idol": "the cursed idol"}
CARRY_SPEED = {"pouch": 1.0, "bar": 0.95, "gem": 0.95, "chest": 0.74, "idol": 0.8}
TWO_HANDS = ("chest", "idol")
ANY_LOOT = (("pouch", 0.5), ("bar", 0.32), ("gem", 0.18))
SOURCES = ("loot", "drop", "sunken", "spew", "kraken", "coat", "raid", "dig", "idol")
SRC_CODE = {s: i for i, s in enumerate(SOURCES)}
FEATS = ("sunken", "spew")             # treasure the twist brought: a feat to pick up

PICK_REACH = 3.2
PICK_RISE = 3.6
BANK_PAD = 1.4
DIG_REACH = 3.6
DIG_SECONDS = 2.6
LIVE_X = 4
X_AGAIN = (16.0, 26.0)
RAID_SECONDS = 2.5
RAID_TAKE = 4
RAID_COOL = 12.0
LOOT_BACK = (28.0, 44.0)
LOOSE_CAP = 46
IDOL_LEFT = 120.0                     # seconds left on the clock when the idol rises
TOSS_SPEED = 26.0
TOSS_UP = 12.0
TOSS_LOCK = 0.9
DROP_LOCK = 1.0
CATCH_REACH = 3.2
FLY_MAX = 4.0
STOP_POINTS = 3                       # for cutting down a carrier

CANNON_REACH = 5.4
CANNON_COOL = 9.0
CANNON_MIN = 24.0
CANNON_MAX = 120.0
CANNON_ARC = 0.85
SHELL_SPLASH = 7.5
SHELL_DAMAGE = 60.0
SHELL_KNOCK = 28.0
SHELL_UP = 16.0

WADE = 0.4                            # deeper than this, wading
DEEP = 2.8                            # deeper than this, up to the chest
WADE_SCALE = 0.78
DEEP_SCALE = 0.6

TIDE_STEP = 2.5
TENT_HP = 150.0
TENT_REACH = 26.0
SLAM_EVERY = (3.2, 5.0)
SLAM_WARN = 1.4
SLAM_RADIUS = 6.0
SLAM_DAMAGE = 28.0
SLAM_KNOCK = 26.0
COAT_HP = 70.0
COAT_SPEED = 7.0
COAT_SIGHT = 48.0
COAT_AIM = 1.2
COAT_COOL = (2.4, 3.6)
COAT_DAMAGE = 24.0
BOMB_EVERY = (0.9, 1.5)
BOMB_WARN = 1.6
BOMB_RADIUS = 6.5
BOMB_DAMAGE = 38.0
BOMB_KNOCK = 24.0
GOLD_EVERY = (1.2, 2.0)
NPC_BASE = 900000
SHIP_NAMES = {"red": "Scarlet Queen", "blue": "Blue Marlin"}
TWIST_NAMES = {"tide": "low tide", "kraken": "the kraken", "redcoats": "the redcoats",
               "eruption": "the eruption"}
DEFAULTS: Dict[str, Any] = {}


def _defaults() -> Dict[str, Any]:
    if not DEFAULTS:
        from ...models.event_worlds import plunder_bay as meta
        for spec in meta.BOT_FIELDS:
            DEFAULTS[spec[0]] = spec[3]
    return DEFAULTS


def _item(item_id: str, name: str, kind: str, parts: List[Dict[str, Any]],
          **stats: Any) -> Dict[str, Any]:
    body = {"kind": kind, "rpm": stats.pop("rpm", 60), "mag": 999, "reserve": 999,
            "range": stats.pop("range", 10), "custom": True}
    body.update(stats)
    return ArenaWorld.item(item_id, name, body, parts)


GOLD = "#e8b830"
HELD = {
    "chest": _item("pb_chest", "Treasure Chest", "pb_carry", [
        {"t": "box", "p": [-0.75, -0.25, 0.75], "s": [1.9, 1.1, 1.3], "c": "#7a4a26"},
        {"t": "box", "p": [-0.75, 0.48, 0.75], "s": [1.96, 0.42, 1.36], "c": "#8a5a2e"},
        {"t": "box", "p": [-1.35, 0.1, 0.75], "s": [0.16, 1.5, 1.4], "c": GOLD, "m": "metal"},
        {"t": "box", "p": [-0.15, 0.1, 0.75], "s": [0.16, 1.5, 1.4], "c": GOLD, "m": "metal"},
        {"t": "box", "p": [-0.75, 0.2, 1.46], "s": [0.32, 0.38, 0.08], "c": GOLD, "m": "metal"}],
        rpm=60, range=1, hide_ammo=True),
    "idol": _item("pb_idol", "Cursed Idol", "pb_carry", [
        {"t": "box", "p": [-0.5, -0.4, 0.7], "s": [1.0, 0.3, 0.8], "c": "#b88a20", "m": "metal"},
        {"t": "box", "p": [-0.5, 0.3, 0.7], "s": [0.8, 1.2, 0.6], "c": GOLD, "m": "metal"},
        {"t": "box", "p": [-0.5, 1.2, 0.7], "s": [0.96, 0.76, 0.76], "c": GOLD, "m": "metal"},
        {"t": "box", "p": [-0.7, 1.26, 1.09], "s": [0.18, 0.14, 0.04], "c": "#ff3030", "m": "neon"},
        {"t": "box", "p": [-0.3, 1.26, 1.09], "s": [0.18, 0.14, 0.04], "c": "#ff3030", "m": "neon"}],
        rpm=60, range=1, hide_ammo=True),
}


def _in_rect(rect: Sequence[float], pos: Sequence[float], pad: float = 0.0) -> bool:
    return rect[0] - pad <= pos[0] <= rect[1] + pad and rect[2] - pad <= pos[2] <= rect[3] + pad


def _flat(a: Sequence[float], b: Sequence[float]) -> float:
    return math.hypot(a[0] - b[0], a[2] - b[2])


def _wrap(angle: float) -> float:
    return (angle + math.pi) % (2.0 * math.pi) - math.pi


def _r(values: Sequence[float], places: int = 2) -> List[float]:
    return [round(v, places) for v in values]


def _ballistic(a: Sequence[float], b: Sequence[float], seconds: float) -> List[float]:
    """The velocity that carries a thing from a to b in ``seconds`` under
    gravity."""
    t = max(0.2, seconds)
    return [(b[0] - a[0]) / t, (b[1] - a[1] + 0.5 * GRAVITY * t * t) / t, (b[2] - a[2]) / t]


def _arc(fly: Dict[str, Any], t: float) -> List[float]:
    a, v = fly["from"], fly["v"]
    t = max(0.0, min(fly["T"], t))
    return [a[0] + v[0] * t, a[1] + v[1] * t - 0.5 * GRAVITY * t * t, a[2] + v[2] * t]


class Npc:
    """One of the world's own fighters: a kraken's tentacle or a redcoat.
    Bots see, chase and shoot these like anybody else."""
    npc = True
    brain = None
    hidden = False

    def __init__(self, pid: int, kind: str, pos: Sequence[float], hp: float):
        self.pid = pid
        self.kind = kind
        self.pos = list(pos)
        self.vel = [0.0, 0.0, 0.0]
        self.alive = True
        self.health = hp
        self.max_health = hp
        self.state = "rise"
        self.yaw = 0.0
        self.team = ""
        self.username = "a redcoat" if kind == "redcoat" else "the kraken"
        self.aim_heights = (3.0, 4.6) if kind == "redcoat" else (7.0, 10.0)
        self.data: Dict[str, Any] = {}

    def hitbox(self) -> Tuple[List[float], List[float]]:
        x, y, z = self.pos
        if self.kind == "redcoat":
            return [x - 1.6, y, z - 1.0], [x + 1.6, y + 5.4, z + 1.0]
        return [x - 1.8, y, z - 1.8], [x + 1.8, y + 13.0, z + 1.8]

    def head_box(self) -> Tuple[List[float], List[float]]:
        x, y, z = self.pos
        if self.kind == "redcoat":
            return [x - 0.9, y + 4.2, z - 0.8], [x + 0.9, y + 5.6, z + 0.8]
        return [x - 1.4, y + 10.0, z - 1.4], [x + 1.4, y + 13.0, z + 1.4]

    def chest(self) -> List[float]:
        lo, hi = self.hitbox()
        return [self.pos[0], (lo[1] + hi[1]) / 2.0, self.pos[2]]


class PlunderBayWorld(ArenaWorld):
    MAP = pb_map
    TEAMS = ("red", "blue")
    TEAM_NAMES = {"red": "Scarlet Corsairs", "blue": "Azure Buccaneers"}
    ROUNDS_PER_AREA = 1
    SETUP_SECONDS = 10.0
    ROUND_SECONDS = 300.0
    RESULTS_SECONDS = 15.0
    LOGO = "Plunder Bay"
    FREEZE_COUNTDOWN = True
    CUSTOM_KINDS = ("pb_carry",)
    respawn_seconds = 5.0
    BOT_CHATTER = ["yarr", "gg", "gold!", "where's the X", "cover me", "lol", "nice haul",
                   "raiders!", "ahoy", "shiver me timbers", "who has the chest", "go go"]

    # ------------------------------------------------------------ settings
    def setting(self, key: str) -> Any:
        cfg = getattr(self.bots, "cfg", None) if self.bots is not None else None
        value = (cfg or {}).get("plunder_bay_" + key)
        return _defaults().get(key) if value is None else value

    def pct(self, key: str) -> float:
        try:
            return max(0.0, min(1.0, float(self.setting(key)) / 100.0))
        except (TypeError, ValueError):
            return 0.5

    # ================================================================ setup
    def world_setup(self) -> None:
        self.extra: Dict[str, Any] = {}
        self.items: Dict[int, Dict[str, Any]] = {}
        self.next_id = 1
        self.points: Dict[str, int] = {"red": 0, "blue": 0}
        self.holds: Dict[str, Dict[str, Any]] = {}
        self.cannons: List[Dict[str, Any]] = []
        self.digs: List[Dict[str, Any]] = []
        self.spots: List[Dict[str, Any]] = []
        self.idol_mark: Optional[Dict[str, Any]] = None
        self.idol_state = "waiting"
        self.idol_id = 0
        self.npcs: Dict[int, Npc] = {}
        self.next_npc = NPC_BASE
        self.hazards: List[Dict[str, Any]] = []
        self.water_y = -1.0
        self.levels: List[float] = []
        self.lava: List[List[float]] = []
        self.lava_y = -1e9
        self.bridges: List[List[float]] = []
        self.twist: Dict[str, Any] = {"kind": "", "on": False, "until": 0.0, "next": NEVER,
                                      "warned": False}
        self.raid_cool: Dict[str, float] = {}
        self.next_x = NEVER
        self.leader_now = ""
        self.claims: Dict[Tuple[str, int], float] = {}
        self.round_stats: Dict[int, Dict[str, float]] = {}
        self.counts: Dict[str, int] = {k: 0 for k in (
            "picks", "banks", "banked", "digs", "chests", "tosses", "catches", "raids",
            "melee_kills", "ranged_kills", "cannons", "cannon_hits", "drops", "twists",
            "npc_hits", "npc_kills", "slams", "volleys", "bombs", "spews", "sunken", "washed",
            "idols", "lava", "stops")}
        self.events_said: Dict[str, float] = {}
        self.landmarks: List[Tuple[List[float], str]] = []
        self.items_dirty = True
        self.items_sent = 0.0
        self.nav_scrubbed = False

    def round_setup(self) -> None:
        area = self.area
        extra = area.get("extra") or {}
        self.extra = extra
        pts = area.get("points") or {}
        cx, cz = area["centre"][0], area["centre"][2]
        self.holds = {m["team"]: dict(m) for m in pts.get("hold") or []}
        self.cannons = [dict(m, i=k, ready=0.0) for k, m in enumerate(pts.get("cannon") or [])]
        self.digs = [dict(m, live=False, dug=0.0)
                     for m in sorted(pts.get("dig") or [], key=lambda m: m["i"])]
        self.spots = [dict(m, item=0, back=0.0)
                      for m in sorted(pts.get("loot") or [], key=lambda m: m["i"])]
        self.idol_mark = (pts.get("idol") or [None])[0]
        self.sunken_marks = [list(m["p"]) for m in pts.get("sunken") or []]
        self.tentacle_marks = [list(m["p"]) for m in pts.get("tentacle") or []]
        self.barracks = [list(m["p"]) for m in pts.get("barracks") or []]
        routes: Dict[int, List[Dict[str, Any]]] = {}
        for m in pts.get("patrol") or []:
            routes.setdefault(int(m.get("route", 0)), []).append(m)
        self.routes = {r: [list(m["p"]) for m in sorted(ms, key=lambda m: m["i"])]
                       for r, ms in routes.items()}
        self.rain = [list(m["p"]) for m in pts.get("rain") or []]
        vent = extra.get("vent") or [0.0, 40.0, 0.0]
        self.vent = [vent[0] + cx, vent[1], vent[2] + cz]
        self.landmarks = [(list(m["p"]), m["name"]) for m in area.get("landmarks") or []]
        self.levels = [float(v) for v in extra.get("levels") or [extra.get("water", -1.0)]]
        self.water_y = float(extra.get("water", -1.0))
        self.lava = [[r[0] + cx, r[1] + cx, r[2] + cz, r[3] + cz] for r in extra.get("lava") or []]
        self.lava_y = float(extra.get("lava_y", -1e9)) if self.lava else -1e9
        self.bridges = [[r[0] + cx, r[1] + cx, r[2] + cz, r[3] + cz, r[4]]
                        for r in extra.get("bridges") or []]
        self.kill_floor = float(area.get("kill_y", -80.0))
        self.items = {}
        self.npcs = {}
        self.hazards = []
        self.points = {"red": 0, "blue": 0}
        self.raid_cool = {}
        self.claims = {}
        self.round_stats = {}
        self.events_said = {}
        self.leader_now = ""
        self.idol_state = "waiting"
        self.idol_id = 0
        self.next_x = NEVER
        kind = extra.get("twist", "")
        self.twist = {"kind": kind, "on": False, "until": 0.0, "warned": False, "next": NEVER,
                      "stage": 0, "at": 0.0}
        for key, d in (area.get("dynamic") or {}).items():
            self.set_dynamic(key, bool(d.get("on", True)))
        # the treasure lies about the island, and the first X's are drawn
        for k in range(len(self.spots)):
            self._spawn_at_spot(k)
        dormant = list(range(len(self.digs)))
        self.rng.shuffle(dormant)
        for i in dormant[:LIVE_X]:
            self.digs[i]["live"] = True
        self.items_dirty = True
        for player in self.players.values():
            self.reset_player(player)

    def reset_player(self, player: Player) -> None:
        for key in ("pb_carry", "pb_act", "pb_mind", "pb_push", "pb_toss_at", "pb_lock"):
            player.extra.pop(key, None)

    # ============================================================ spawning
    def on_spawned(self, player: Player) -> None:
        for key in ("pb_act", "pb_push"):
            player.extra.pop(key, None)
        # everybody fights with their own hotbar (a chest or the idol is the
        # only thing the world ever puts in their hands)
        if player.extra.get("loadout") is not None:
            self.set_loadout(player, None, quiet=True)

    def on_player_ready(self, player: Player) -> None:
        super().on_player_ready(player)
        player.send(self._items_message())
        if self.twist["on"]:
            player.send({"t": "pbx", "k": "twist", "twist": self.twist["kind"], "on": True,
                         "left": round(max(0.0, self.twist["until"] - engine.now()), 1)})

    def on_player_leave(self, player: Player) -> None:
        self._drop(player, engine.now(), "left")

    def welcome_lines(self, player: Player) -> List[str]:
        lines = super().welcome_lines(player)
        lines.append("Haul treasure into your own ship's hold: walk over it to pick it up. Hold E "
                     "on an X to dig up a chest. First crew to %d doubloons wins." % TARGET)
        lines.append("R tosses what you carry to a crewmate. E at your ship's cannon fires it. "
                     "Empty-handed in their hold, hold E to steal their gold.")
        return lines

    # ============================================================ movement
    def move_scale(self, player: Player) -> float:
        # a person's own browser slows them down (static/js/worlds/plunder_bay.js):
        # the server only holds its bots to the same
        if player.brain is None:
            return 1.0
        scale = 1.0
        item = self._carried(player)
        if item is not None:
            scale *= CARRY_SPEED[item["kind"]]
        depth = self.water_y - player.pos[1]
        if depth > DEEP:
            scale *= DEEP_SCALE
        elif depth > WADE:
            scale *= WADE_SCALE
        return scale

    def can_fire(self, player: Player) -> bool:
        if not super().can_fire(player):
            return False
        item = self._carried(player)
        return item is None or item["kind"] not in TWO_HANDS

    def hostiles_for(self, player: Player):
        if not self.in_play(player):
            return
        for other in self.players.values():
            if other is not player and self.in_play(other) and self.can_hurt(player, other):
                yield other
        for npc in self.npcs.values():
            if npc.alive and npc.state in ("idle", "wind", "walk", "aim"):
                yield npc

    def entity(self, eid: Optional[int]):
        if eid is None:
            return None
        return self.players.get(eid) or self.npcs.get(eid)

    # ============================================================== rounds
    def on_live(self) -> None:
        moment = engine.now()
        tw = self.twist
        if tw["kind"]:
            lo, hi = self.extra.get(tw["kind"] + "_every") or (55.0, 75.0)
            tw["next"] = moment + self.rng.uniform(lo, hi)
        self.next_x = moment + self.rng.uniform(*X_AGAIN)
        self.broadcast({"t": "pbx", "k": "go"})
        self._broadcast_state()

    def round_tick(self, dt: float, moment: float) -> None:
        self._twist_tick(moment)
        self._spots_tick(moment)
        self._fly_tick(moment)
        self._npc_tick(dt, moment)
        self._hazard_tick(moment)
        for player in self.playing():
            self._player_tick(player, dt, moment)
            if self.phase != "active":
                return
        self._flush_items(moment)

    def setup_tick(self, dt: float, moment: float) -> None:
        self._flush_items(moment)

    def time_up(self) -> None:
        self.finish_round(self.leader(), "time")

    def leader(self) -> str:
        red, blue = self.points.get("red", 0), self.points.get("blue", 0)
        return "" if red == blue else ("red" if red > blue else "blue")

    def headline(self, winner: str, reason: str) -> str:
        if not winner:
            return "A draw -- %d doubloons each" % self.points.get("red", 0)
        loser = "blue" if winner == "red" else "red"
        return "%s win, %d doubloons to %d" % (self.team_name(winner), self.points.get(winner, 0),
                                               self.points.get(loser, 0))

    # ============================================================ treasure
    def _new_item(self, kind: str, pos: Sequence[float], src: str) -> Dict[str, Any]:
        iid = self.next_id
        self.next_id += 1
        item = {"id": iid, "kind": kind, "p": list(pos), "state": "ground", "by": 0, "src": src,
                "spot": -1, "lock": (0, 0.0), "thrown": (0, ""), "fly": None, "feat": src in FEATS}
        self.items[iid] = item
        self.items_dirty = True
        return item

    def _any_kind(self) -> str:
        roll = self.rng.random()
        for kind, share in ANY_LOOT:
            roll -= share
            if roll <= 0:
                return kind
        return "pouch"

    def _spawn_at_spot(self, k: int) -> None:
        spot = self.spots[k]
        what = spot.get("what", "any")
        kind = self._any_kind() if what not in VALUE else what
        item = self._new_item(kind, spot["p"], "loot")
        item["spot"] = k
        spot["item"] = item["id"]

    def _loose(self) -> int:
        return sum(1 for item in self.items.values() if item["state"] != "carried")

    def _spots_tick(self, moment: float) -> None:
        loose = None
        for k, spot in enumerate(self.spots):
            if spot["item"] or moment < spot["back"]:
                continue
            if loose is None:
                loose = self._loose()
            if loose >= LOOSE_CAP:
                spot["back"] = moment + 5.0
                continue
            if any(_flat(p.pos, spot["p"]) < 4.0 for p in self.playing()):
                spot["back"] = moment + 3.0
                continue
            self._spawn_at_spot(k)
            loose += 1
        # a new X once one has been dug
        if moment >= self.next_x:
            self.next_x = moment + self.rng.uniform(*X_AGAIN)
            live = [d for d in self.digs if d["live"]]
            if len(live) < LIVE_X:
                options = [i for i, d in enumerate(self.digs)
                           if not d["live"] and moment - d["dug"] > 20.0]
                if options:
                    i = self.rng.choice(options)
                    self.digs[i]["live"] = True
                    self.items_dirty = True
                    self.broadcast({"t": "pbx", "k": "x", "i": i})
        # the idol rises with two minutes to go
        if self.idol_state == "waiting" and self.idol_mark is not None and self.round_ends \
                and moment >= self.round_ends - IDOL_LEFT:
            self._raise_idol(moment)

    def _raise_idol(self, moment: float) -> None:
        if self.idol_mark is None:
            return
        item = self._new_item("idol", self.idol_mark["p"], "idol")
        self.idol_id = item["id"]
        self.idol_state = "altar"
        self.counts["idols"] += 1
        self.broadcast({"t": "pbx", "k": "idol", "s": "rise", "p": _r(item["p"])})
        self._event("pb_idol", None, "", rose=True)
        self._broadcast_state()

    def _carried(self, player: Player) -> Optional[Dict[str, Any]]:
        iid = player.extra.get("pb_carry")
        if not iid:
            return None
        item = self.items.get(iid)
        if item is None or item["state"] != "carried" or item["by"] != player.pid:
            player.extra.pop("pb_carry", None)
            return None
        return item

    def _pick(self, player: Player, item: Dict[str, Any], moment: float) -> None:
        item["state"] = "carried"
        item["by"] = player.pid
        item["fly"] = None
        item["p"] = list(player.pos)
        player.extra["pb_carry"] = item["id"]
        player.extra.pop("pb_act", None)
        if item["spot"] >= 0:
            spot = self.spots[item["spot"]]
            if spot["item"] == item["id"]:
                spot["item"] = 0
                spot["back"] = moment + self.rng.uniform(*LOOT_BACK)
            item["spot"] = -1
        if item["kind"] in TWO_HANDS:
            self.set_loadout(player, [HELD[item["kind"]]], quiet=True)
        if player.brain is not None:
            # a scrapper keeps fighting with a pouch in hand; the rest run it home
            self._mind(player)["scrapper"] = player.brain.rng.random() < self.pct("aggression") * 0.5
        if item.get("feat"):
            item["feat"] = False
            self._feat(player)
            if item["src"] == "sunken":
                self.counts["sunken"] += 1
        self.counts["picks"] += 1
        self.items_dirty = True
        self.broadcast({"t": "pbx", "k": "pick", "id": item["id"], "by": player.pid,
                        "kind": item["kind"]})
        if item["kind"] == "idol":
            self.idol_state = "carried"
            self._event("pb_idol", player, player.team)
            self.system_message("%s has the cursed idol!" % player.username)
            self._broadcast_state()
        self._send_me(player, force=True)

    def _release(self, player: Player, item: Dict[str, Any]) -> None:
        """Out of ``player``'s hands, whichever way it went."""
        player.extra.pop("pb_carry", None)
        item["by"] = 0
        if item["kind"] in TWO_HANDS:
            self.set_loadout(player, None, quiet=True)      # their own hotbar back
        if item["kind"] == "idol":
            self.idol_state = "ground"
            self._broadcast_state()
        self._send_me(player, force=True)

    def _drop(self, player: Player, moment: float, why: str = "",
              fling: Optional[Sequence[float]] = None) -> None:
        item = self._carried(player)
        if item is None:
            return
        self._release(player, item)
        item["lock"] = (player.pid, moment + DROP_LOCK)
        self.counts["drops"] += 1
        if fling is not None:
            origin = [player.pos[0], player.pos[1] + 3.0, player.pos[2]]
            self._launch(item, origin, fling, moment)
        else:
            floor = self._floor_under(player.pos[0], player.pos[1] + 1.0, player.pos[2])
            self._settle(item, [player.pos[0], floor, player.pos[2]] if floor is not None
                         else None, moment)
        self.broadcast({"t": "pbx", "k": "drop", "id": item["id"], "by": player.pid,
                        "why": why})

    def _settle(self, item: Dict[str, Any], at: Optional[Sequence[float]], moment: float) -> None:
        """Treasure comes to rest at ``at`` -- or is lost, if that is the lava
        or nowhere -- and is banked if it is on a hold's hatch."""
        item["fly"] = None
        if at is None or self._in_lava(at) or at[1] < self.kill_floor + 4.0:
            self._lose(item, moment)
            return
        item["state"] = "ground"
        item["p"] = list(at)
        self.items_dirty = True
        for team, hold in self.holds.items():
            if self._on_hold(hold, at):
                pid, thrower_team = item.get("thrown") or (0, "")
                by = self.players.get(pid) if thrower_team == team else None
                self._bank(team, item, by, moment)
                return

    def _lose(self, item: Dict[str, Any], moment: float) -> None:
        """Into the lava, or off the world: a chest makes an X live again; the
        idol goes back on its altar; anything else is gone."""
        self.items.pop(item["id"], None)
        self.items_dirty = True
        self.broadcast({"t": "pbx", "k": "lost", "id": item["id"], "p": _r(item["p"])})
        if item["kind"] == "idol" and self.idol_mark is not None:
            fresh = self._new_item("idol", self.idol_mark["p"], "idol")
            self.idol_id = fresh["id"]
            self.idol_state = "altar"
            self.broadcast({"t": "pbx", "k": "idol", "s": "back", "p": _r(fresh["p"])})
            self._broadcast_state()
        elif item["kind"] == "chest":
            self.next_x = min(self.next_x, moment + 2.0)

    def _on_hold(self, hold: Dict[str, Any], pos: Sequence[float], pad: float = BANK_PAD) -> bool:
        return _flat(hold["p"], pos) < float(hold.get("r", 4.2)) + pad and \
            abs(pos[1] - hold["p"][1]) < 3.0

    def _bank(self, team: str, item: Dict[str, Any], player: Optional[Player],
              moment: float) -> None:
        kind = item["kind"]
        value = VALUE[kind]
        if player is not None and self._carried(player) is item:
            self._release(player, item)
        self.items.pop(item["id"], None)
        self.items_dirty = True
        self.points[team] = self.points.get(team, 0) + value
        self.counts["banks"] += 1
        self.counts["banked"] += value
        if player is not None:
            player.score += value
            self._stat(player, "plunder", value)
            self.badge(player, "pb_plunder", value)
            if kind == "chest":
                self._stat(player, "chests")
                self.badge(player, "pb_chests")
            elif kind == "idol":
                self._stat(player, "idols")
                self.badge(player, "pb_idols")
        if kind == "chest":
            self.counts["chests"] += 1
        if kind == "idol":
            self.idol_state = "banked"
        self.broadcast({"t": "pbx", "k": "bank", "id": item["id"], "kind": kind, "team": team,
                        "by": player.pid if player is not None else 0, "v": value,
                        "pts": dict(self.points)})
        if kind in TWO_HANDS:
            self._event("pb_bank_big", player, team, what=NAMES[kind])
            if player is not None:
                self.system_message("%s banked %s for the %s!" % (player.username, NAMES[kind],
                                                                 self.team_name(team)))
        lead = self.leader()
        if lead and lead != self.leader_now:
            if self.leader_now:
                self._event("pb_lead", None, lead)
            self.leader_now = lead
        self._broadcast_state()
        if self.points[team] >= TARGET and self.phase == "active":
            self.finish_round(team, "target")

    # ------------------------------------------------------------ in flight
    def _launch(self, item: Dict[str, Any], origin: Sequence[float], v: Sequence[float],
                moment: float) -> None:
        """Send treasure flying: where it will come down is worked out now
        (the path up to the first thing it strikes), so the clients draw the
        same arc and the catch is tested along it."""
        pos = list(origin)
        vel = list(v)
        t, step = 0.0, 0.05
        land: Optional[List[float]] = None
        while t < FLY_MAX:
            nxt = [pos[0] + vel[0] * step, pos[1] + vel[1] * step - 0.5 * GRAVITY * step * step,
                   pos[2] + vel[2] * step]
            seg = [nxt[i] - pos[i] for i in range(3)]
            length = math.sqrt(seg[0] ** 2 + seg[1] ** 2 + seg[2] ** 2)
            if length > 1e-6:
                direction = [c / length for c in seg]
                hit = self.ray_world(pos, direction, length)
                if hit < length:
                    land = [pos[i] + direction[i] * hit for i in range(3)]
                    t += step * hit / length
                    break
            vel[1] -= GRAVITY * step
            pos = nxt
            t += step
            if pos[1] < self.kill_floor:
                break
        to: Optional[List[float]] = None
        if land is not None:
            fx, fz = v[0], v[2]
            fl = math.hypot(fx, fz) or 1.0
            x, z = land[0] - fx / fl * 0.4, land[2] - fz / fl * 0.4
            floor = self._floor_under(x, land[1] + 0.3, z)
            if floor is not None:
                to = [x, floor, z]
        item["state"] = "fly"
        item["by"] = 0
        item["fly"] = {"from": list(origin), "v": list(v), "t0": moment, "T": max(0.05, t),
                       "to": to}
        item["p"] = list(origin)
        self.items_dirty = True
        self.broadcast({"t": "pbx", "k": "fly", "id": item["id"], "kind": item["kind"],
                        "a": _r(origin), "v": _r(v), "T": round(max(0.05, t), 3),
                        "to": _r(to) if to else None})

    def _fly_tick(self, moment: float) -> None:
        for item in list(self.items.values()):
            fly = item.get("fly")
            if item["state"] != "fly" or not fly:
                continue
            t = moment - fly["t0"]
            if t >= fly["T"]:
                self._settle(item, fly["to"], moment)
                continue
            item["p"] = _arc(fly, t)
            if t < 0.12:
                continue
            for p in self.playing():
                if self._carried(p) is not None:
                    continue
                lock = item.get("lock") or (0, 0.0)
                if lock[0] == p.pid and moment < lock[1]:
                    continue
                chest = [p.pos[0], p.pos[1] + 2.6, p.pos[2]]
                if math.dist(chest, item["p"]) < CATCH_REACH:
                    pid, team = item.get("thrown") or (0, "")
                    self._pick(p, item, moment)
                    if pid and pid != p.pid and team == p.team:
                        self.counts["catches"] += 1
                        self._stat(p, "catches")
                        self.badge(p, "pb_catches")
                        self.broadcast({"t": "pbx", "k": "catch", "id": item["id"], "by": p.pid})
                    break

    def _floor_under(self, x: float, y: float, z: float) -> Optional[float]:
        drop = self.ray_world([x, y + 0.6, z], [0.0, -1.0, 0.0], 90.0)
        if drop >= 90.0:
            return None
        return y + 0.6 - drop

    def _ground_at(self, x: float, z: float, top: float = 80.0) -> float:
        drop = self.ray_world([x, top, z], [0.0, -1.0, 0.0], top + 40.0)
        return top - drop if drop < top + 40.0 else self.water_y

    def _in_lava(self, pos: Sequence[float]) -> bool:
        return bool(self.lava) and pos[1] < self.lava_y and \
            any(_in_rect(r, pos) for r in self.lava)

    def _flush_items(self, moment: float) -> None:
        if self.items_dirty and moment - self.items_sent >= 0.2:
            self.items_dirty = False
            self.items_sent = moment
            self.broadcast(self._items_message())

    def _items_message(self) -> Dict[str, Any]:
        """Everything lying about, and the live X's (what is carried or in
        the air rides on the snapshots)."""
        return {"t": "pbi",
                "it": [[i["id"], KIND_CODE[i["kind"]], round(i["p"][0], 2), round(i["p"][1], 2),
                        round(i["p"][2], 2), SRC_CODE.get(i["src"], 0)]
                       for i in self.items.values() if i["state"] == "ground"],
                "x": [k for k, d in enumerate(self.digs) if d["live"]]}

    # ============================================================== players
    def _player_tick(self, player: Player, dt: float, moment: float) -> None:
        pos = player.pos
        if self._in_lava(pos):
            self.counts["lava"] += 1
            self.broadcast({"t": "pbx", "k": "burn", "id": player.pid, "p": _r(pos)})
            self.kill(player, None, "the lava")
            return
        item = self._carried(player)
        if item is not None:
            item["p"] = list(pos)
            hold = self.holds.get(player.team)
            if hold is not None and self._on_hold(hold, pos):
                self._bank(player.team, item, player, moment)
        else:
            best, best_d = None, PICK_REACH
            for other in self.items.values():
                if other["state"] != "ground":
                    continue
                d = _flat(other["p"], pos)
                if d >= best_d or abs(other["p"][1] - pos[1]) > PICK_RISE:
                    continue
                lock = other.get("lock") or (0, 0.0)
                if lock[0] == player.pid and moment < lock[1]:
                    continue
                best, best_d = other, d
            if best is not None:
                self._pick(player, best, moment)
        act = player.extra.get("pb_act")
        if act:
            self._act_tick(player, act, dt, moment)

    # ================================================================== E
    def use(self, player: Player, message: Dict[str, Any]) -> None:
        if self.phase != "active" or not self.in_play(player):
            return
        moment = engine.now()
        cannon = self._cannon_near(player)
        if cannon is not None and self._carried(player) is None:
            player.extra.pop("using", None)
            self._fire_cannon(player, cannon, self._aim_point(player, cannon), moment)
            return
        if self._carried(player) is not None:
            return
        dig = self._dig_near(player)
        if dig is not None:
            player.extra["pb_act"] = {"k": "dig", "i": dig, "t": 0.0}
            self.broadcast({"t": "pbx", "k": "digging", "id": player.pid, "i": dig})
            self._send_me(player, force=True)
            return
        for team, hold in self.holds.items():
            if team != player.team and self._on_hold(hold, player.pos, 0.6):
                if self.points.get(team, 0) < RAID_TAKE:
                    player.send({"t": "notice", "m": "Their hold is empty -- nothing to steal.",
                                 "bad": True})
                    return
                if moment < self.raid_cool.get(team, 0.0):
                    player.send({"t": "notice", "m": "They are still counting what was taken. "
                                 "Try again in a moment.", "bad": True})
                    return
                player.extra["pb_act"] = {"k": "raid", "team": team, "t": 0.0}
                self.broadcast({"t": "pbx", "k": "raiding", "id": player.pid, "team": team})
                self._send_me(player, force=True)
                return

    def unuse(self, player: Player) -> None:
        if player.extra.pop("pb_act", None) is not None:
            self._send_me(player, force=True)

    def _dig_near(self, player: Player) -> Optional[int]:
        best, best_d = None, DIG_REACH
        for i, d in enumerate(self.digs):
            if not d["live"]:
                continue
            dist = _flat(d["p"], player.pos)
            if dist < best_d and abs(d["p"][1] - player.pos[1]) < 3.0:
                best, best_d = i, dist
        return best

    def _act_tick(self, player: Player, act: Dict[str, Any], dt: float, moment: float) -> None:
        if not player.extra.get("using") or self._carried(player) is not None:
            player.extra.pop("pb_act", None)
            return
        if act["k"] == "dig":
            d = self.digs[act["i"]]
            if not d["live"] or _flat(d["p"], player.pos) > DIG_REACH + 1.2:
                player.extra.pop("pb_act", None)
                return
            act["t"] += dt
            if act["t"] >= DIG_SECONDS:
                self._dug(player, act["i"], moment)
        elif act["k"] == "raid":
            team = act["team"]
            hold = self.holds.get(team)
            if hold is None or not self._on_hold(hold, player.pos, 1.6) or \
                    self.points.get(team, 0) < RAID_TAKE or moment < self.raid_cool.get(team, 0.0):
                player.extra.pop("pb_act", None)
                return
            act["t"] += dt
            if act["t"] >= RAID_SECONDS:
                self._raid(player, team, moment)

    def _dug(self, player: Player, i: int, moment: float) -> None:
        d = self.digs[i]
        d["live"] = False
        d["dug"] = moment
        player.extra.pop("pb_act", None)
        player.extra.pop("using", None)
        self.next_x = min(self.next_x, moment + self.rng.uniform(*X_AGAIN))
        item = self._new_item("chest", d["p"], "dig")
        self.counts["digs"] += 1
        self._stat(player, "digs")
        self.badge(player, "pb_digs")
        self.broadcast({"t": "pbx", "k": "dug", "i": i, "by": player.pid, "id": item["id"],
                        "p": _r(d["p"])})
        self._pick(player, item, moment)

    def _raid(self, player: Player, team: str, moment: float) -> None:
        player.extra.pop("pb_act", None)
        player.extra.pop("using", None)
        take = min(RAID_TAKE, self.points.get(team, 0))
        if take <= 0:
            return
        self.points[team] -= take
        self.raid_cool[team] = moment + RAID_COOL
        item = self._new_item("bar", player.pos, "raid")
        self.counts["raids"] += 1
        self._stat(player, "raids")
        self.badge(player, "pb_raids")
        player.score += 3
        self.broadcast({"t": "pbx", "k": "raid", "by": player.pid, "team": team, "v": take,
                        "pts": dict(self.points)})
        self._event("pb_raid", player, player.team)
        self._pick(player, item, moment)
        self._broadcast_state()

    # ============================================================== tossing
    def world_action(self, player: Player, kind: Any, message: Dict[str, Any]) -> None:
        if kind != "toss":
            return
        direction = message.get("d")
        if not (isinstance(direction, list) and len(direction) == 3):
            return
        try:
            direction = normalise([float(v) for v in direction])
        except (TypeError, ValueError):
            return
        self._toss(player, direction, engine.now())

    def _toss(self, player: Player, direction: Sequence[float], moment: float,
              velocity: Optional[Sequence[float]] = None) -> bool:
        if self.phase != "active" or not self.in_play(player):
            return False
        item = self._carried(player)
        if item is None or moment < player.extra.get("pb_toss_at", 0.0):
            return False
        player.extra["pb_toss_at"] = moment + 0.6
        flat = normalise([direction[0], 0.0, direction[2]])
        if velocity is None:
            heavy = 0.65 if item["kind"] in TWO_HANDS else 1.0
            up = max(-0.2, min(0.8, direction[1]))
            speed = TOSS_SPEED * heavy * (1.0 - up * 0.4)
            velocity = [flat[0] * speed, (TOSS_UP + up * TOSS_SPEED * 0.6) * heavy, flat[2] * speed]
        origin = [player.pos[0] + flat[0] * 1.4, player.pos[1] + 3.6, player.pos[2] + flat[2] * 1.4]
        self._release(player, item)
        item["lock"] = (player.pid, moment + TOSS_LOCK)
        item["thrown"] = (player.pid, player.team)
        self.counts["tosses"] += 1
        self._launch(item, origin, velocity, moment)
        return True

    # ============================================================= weapons
    # Everybody fights with their own hotbar, through the engine's own
    # hitscan, projectiles, melee and blasts; these let all of it hit the
    # island's own as well -- the redcoats and the kraken's tentacles.
    def _npc_targets(self) -> List["Npc"]:
        return [n for n in self.npcs.values() if n.alive and n.state not in ("rise", "sink", "gone",
                                                                             "down")]

    def nearest_player_hit(self, shooter, origin, direction, max_dist: float):
        best, best_d, head = super().nearest_player_hit(shooter, origin, direction, max_dist)
        if not isinstance(shooter, Player) or shooter.pid <= 0:
            return best, best_d, head
        for npc in self._npc_targets():
            lo, hi = npc.hitbox()
            t = ray_aabb(origin, direction, lo, hi)
            if t is None or not 0.0 <= t < best_d:
                continue
            hlo, hhi = npc.head_box()
            best, best_d = npc, t
            head = ray_aabb(origin, direction, hlo, hhi) is not None
        return best, best_d, head

    def do_melee(self, player: Player, direction, stats: Dict[str, Any]) -> None:
        super().do_melee(player, direction, stats)
        reach = float(stats.get("range", 9.0))
        arc = float(stats.get("arc", 0.55))
        origin = [player.pos[0], player.pos[1] + 3.4, player.pos[2]]
        weapon = (player.weapon() or {}).get("name", "Fists")
        for npc in self._npc_targets():
            lo, hi = npc.hitbox()
            # the nearest point of it to the swing, at about chest height
            target = [npc.pos[0], max(lo[1], min(hi[1], origin[1])), npc.pos[2]]
            delta = [target[i] - origin[i] for i in range(3)]
            distance = math.sqrt(sum(v * v for v in delta)) or 1e-6
            if distance - (hi[0] - lo[0]) * 0.5 > reach:
                continue
            if sum(delta[i] / distance * direction[i] for i in range(3)) < 1.0 - arc:
                continue
            if not self.line_of_sight(origin, target):
                continue
            self._hurt_npc(npc, player, float(stats.get("damage", 30)), weapon)

    def explode(self, proj) -> None:
        super().explode(proj)
        owner = self.players.get(proj.pid_owner)
        if owner is None:
            return
        radius = float(proj.stats.get("splash", 8.0))
        splash = float(proj.stats.get("splash_damage", proj.stats.get("damage", 50)))
        for npc in self._npc_targets():
            distance = math.dist(npc.chest(), proj.pos)
            if distance <= radius:
                self._hurt_npc(npc, owner, splash * (1.0 - (distance / radius) ** 1.4),
                               proj.weapon or "Blast")

    def _melee_weapon(self, player: Player, weapon: str) -> Optional[bool]:
        """Was ``weapon`` (by name) one of ``player``'s close-quarters ones --
        True -- or one that reaches -- False?  None for the ship's cannons and
        the like, which are neither."""
        for slot in range(catalog.HOTBAR_SIZE):
            item = player.weapon(slot)
            if item and item.get("name") == weapon:
                stats = (item.get("data") or {}).get("stats") or {}
                return stats.get("kind") == "melee" or bool(stats.get("melee"))
        return None

    def _knock(self, player: Player, vx: float, vy: float, vz: float) -> None:
        if not player.alive:
            return
        moment = engine.now()
        player.extra["launch_until"] = moment + 1.2
        if player.brain is not None:
            player.extra["pb_push"] = (vx, vz, moment + 0.35)
            if vy > 4.0:
                player.brain.airborne = True
                player.brain.vy = max(player.brain.vy, vy)
            return
        player.send({"t": "knock", "v": [round(vx, 2), round(vy, 2), round(vz, 2)]})

    def bot_push(self, player: Player) -> Optional[Tuple[float, float]]:
        push = player.extra.get("pb_push")
        if not push or push[2] < engine.now():
            return None
        return push[0], push[1]

    def after_kill(self, killer: Optional[Player], victim: Player, weapon: str) -> None:
        moment = engine.now()
        carried = self._carried(victim)
        victim.extra.pop("pb_act", None)
        self._drop(victim, moment, "cut down")
        if killer is None or killer is victim:
            return
        close = self._melee_weapon(killer, weapon)
        if close is True:
            self.counts["melee_kills"] += 1
            self._stat(killer, "melee")
            self.badge(killer, "pb_melee")
        elif close is False:
            self.counts["ranged_kills"] += 1
            self._stat(killer, "ranged")
            self.badge(killer, "pb_ranged")
        if carried is not None:
            killer.score += STOP_POINTS
            self.counts["stops"] += 1
            self._stat(killer, "stops")

    # ============================================================= cannons
    def _cannon_near(self, player: Player) -> Optional[Dict[str, Any]]:
        for c in self.cannons:
            if c["team"] == player.team and _flat(c["p"], player.pos) < CANNON_REACH and \
                    abs(player.pos[1] - c["p"][1]) < 2.5:
                return c
        return None

    def _aim_point(self, player: Player, cannon: Dict[str, Any]) -> List[float]:
        cp = math.cos(player.pitch)
        direction = [math.sin(player.yaw) * cp, math.sin(player.pitch), math.cos(player.yaw) * cp]
        eye = [player.pos[0], player.pos[1] + EYE_HEIGHT, player.pos[2]]
        reach = 180.0
        hit = self.ray_world(eye, direction, reach)
        if hit < reach:
            return [eye[i] + direction[i] * hit for i in range(3)]
        flat = normalise([direction[0], 0.0, direction[2]])
        return [cannon["p"][0] + flat[0] * CANNON_MAX, 0.0, cannon["p"][2] + flat[2] * CANNON_MAX]

    def _fire_cannon(self, player: Player, cannon: Dict[str, Any], aim: Sequence[float],
                     moment: float) -> bool:
        if moment < cannon["ready"]:
            player.send({"t": "notice", "m": "The cannon is still being loaded (%d s)."
                         % (int(cannon["ready"] - moment) + 1), "bad": True})
            return False
        cannon["ready"] = moment + CANNON_COOL
        yaw = float(cannon.get("yaw", 0.0))
        cx, cy, cz = cannon["p"]
        dx, dz = aim[0] - cx, aim[2] - cz
        d = max(CANNON_MIN, min(CANNON_MAX, math.hypot(dx, dz)))
        off = max(-CANNON_ARC, min(CANNON_ARC, _wrap(math.atan2(dx, dz) - yaw)))
        tx, tz = cx + math.sin(yaw + off) * d, cz + math.cos(yaw + off) * d
        target = [tx, self._ground_at(tx, tz), tz]
        muzzle = [cx + math.sin(yaw + off) * 4.4, cy + 2.4, cz + math.cos(yaw + off) * 4.4]
        seconds = 1.1 + d / 95.0
        v = _ballistic(muzzle, target, seconds)
        self.hazards.append({"k": "shell", "at": target, "when": moment + seconds,
                             "r": SHELL_SPLASH, "dmg": SHELL_DAMAGE, "knock": SHELL_KNOCK,
                             "team": player.team, "by": player.pid})
        self.counts["cannons"] += 1
        self._stat(player, "cannons")
        self.broadcast({"t": "pbx", "k": "cannon", "i": cannon["i"], "by": player.pid,
                        "a": _r(muzzle), "v": _r(v), "T": round(seconds, 3), "at": _r(target),
                        "r": SHELL_SPLASH, "team": player.team})
        player.send({"t": "pbx", "k": "cannon_cool", "i": cannon["i"], "s": CANNON_COOL})
        return True

    # ============================================================= hazards
    def _hazard_tick(self, moment: float) -> None:
        if not self.hazards:
            return
        due = [h for h in self.hazards if moment >= h["when"]]
        if not due:
            return
        self.hazards = [h for h in self.hazards if moment < h["when"]]
        for h in due:
            self._blast(h, moment)

    def _blast(self, h: Dict[str, Any], moment: float) -> None:
        """A shell, a tentacle's slam or a lava bomb comes down: damage
        falling off from the middle, everybody knocked away from it, and
        treasure knocked out of their hands."""
        at, radius = h["at"], h["r"]
        team = h.get("team", "")
        by = self.players.get(h.get("by", 0)) if h.get("by") else None
        if by is not None and not self.in_play(by):
            by = None
        weapon = {"shell": "Cannon", "slam": "the kraken", "bomb": "a lava bomb"}.get(h["k"], "")
        self.broadcast({"t": "pbx", "k": "blast", "w": h["k"], "p": _r(at), "r": radius})
        hits = 0
        for p in list(self.playing()):
            d = _flat(p.pos, at)
            if d > radius + 1.0 or not (at[1] - 3.0 < p.pos[1] < at[1] + 6.0):
                continue
            if team and p.team == team:
                continue
            f = max(0.0, min(1.0, d / (radius + 1.0)))
            dx, dz = p.pos[0] - at[0], p.pos[2] - at[2]
            dl = math.hypot(dx, dz) or 1.0
            push = h["knock"] * (1.0 - 0.5 * f)
            if self._carried(p) is not None:
                self._drop(p, moment, "knocked loose",
                           fling=[dx / dl * 9.0, 10.0, dz / dl * 9.0])
            self.apply_damage(p, by, h["dmg"] * (1.0 - 0.55 * f), weapon)
            if p.alive:
                self._knock(p, dx / dl * push, SHELL_UP * (1.0 - 0.4 * f), dz / dl * push)
            hits += 1
            if h["k"] == "shell":
                self.counts["cannon_hits"] += 1
            if by is not None and h["k"] == "shell":
                self._stat(by, "cannon_hits")
                self.badge(by, "pb_cannon")
        if h["k"] == "shell":
            for npc in list(self.npcs.values()):
                if npc.alive and _flat(npc.pos, at) < radius + 1.6:
                    self._hurt_npc(npc, by, h["dmg"] * 0.8, weapon)

    # =============================================================== twists
    def _twist_tick(self, moment: float) -> None:
        tw = self.twist
        kind = tw["kind"]
        if not kind:
            return
        warn = float(self.extra.get("warn", 5.0))
        if not tw["on"]:
            if not tw["warned"] and moment >= tw["next"] - warn:
                tw["warned"] = True
                self.broadcast({"t": "pbx", "k": "warn", "twist": kind,
                                "in": round(max(0.0, tw["next"] - moment), 1)})
            if moment >= tw["next"]:
                self._twist_on(moment)
            return
        self._twist_run(moment)
        if moment >= tw["until"]:
            self._twist_off(moment)

    def _twist_on(self, moment: float) -> None:
        tw = self.twist
        kind = tw["kind"]
        tw["on"] = True
        tw["warned"] = False
        tw["until"] = moment + float(self.extra.get(kind + "_for", 28.0))
        tw["stage"] = 0
        tw["at"] = moment
        tw["next_bomb"] = moment + 1.0
        tw["next_gold"] = moment + 0.6
        self.counts["twists"] += 1
        if kind == "kraken":
            for k, base in enumerate(self.tentacle_marks):
                npc = self._new_npc("tentacle", [base[0], self.water_y - 1.0, base[2]], TENT_HP)
                npc.data.update({"base": list(base), "next": moment + 1.6 + self.rng.uniform(*SLAM_EVERY),
                                 "hit_by": set()})
                npc.state = "rise"
                npc.data["ready"] = moment + 1.5
        elif kind == "redcoats":
            routes = sorted(self.routes)
            for k, spot in enumerate(self.barracks):
                if not routes:
                    break
                npc = self._new_npc("redcoat", spot, COAT_HP)
                route = self.routes[routes[k % len(routes)]]
                npc.data.update({"route": route, "leg": 0, "next_shot": moment + 3.0,
                                 "wait": moment + 0.6 + (k // len(routes)) * 3.0})
                npc.state = "walk"
        self.broadcast({"t": "pbx", "k": "twist", "twist": kind, "on": True,
                        "left": round(tw["until"] - moment, 1)})
        self._event("pb_twist", None, "", twist=kind)
        self._broadcast_state()

    def _twist_run(self, moment: float) -> None:
        tw = self.twist
        kind = tw["kind"]
        if kind == "tide":
            # out in two steps, back in two steps
            levels = self.levels
            if len(levels) < 3:
                return
            back_at = tw["until"] - 2.0 * TIDE_STEP
            if tw["stage"] == 0:
                self._tide(1)
                tw["stage"] = 1
            elif tw["stage"] == 1 and moment >= tw["at"] + TIDE_STEP:
                self._tide(2)
                tw["stage"] = 2
                self._uncover()
            elif tw["stage"] == 2 and moment >= back_at:
                self._tide(1)
                tw["stage"] = 3
                self._wash(moment)
        elif kind == "eruption":
            if moment >= tw.get("next_bomb", 0.0):
                tw["next_bomb"] = moment + self.rng.uniform(*BOMB_EVERY)
                self._lava_bomb(moment)
            if moment >= tw.get("next_gold", 0.0):
                tw["next_gold"] = moment + self.rng.uniform(*GOLD_EVERY)
                self._spew(moment)

    def _twist_off(self, moment: float) -> None:
        tw = self.twist
        kind = tw["kind"]
        tw["on"] = False
        lo, hi = self.extra.get(kind + "_every") or (55.0, 75.0)
        tw["next"] = moment + self.rng.uniform(lo, hi)
        if kind == "tide":
            self._tide(0)
        for npc in self.npcs.values():
            if npc.alive:
                npc.state = "sink" if npc.kind == "tentacle" else "gone"
                npc.alive = False
                npc.data["gone_at"] = moment + 1.6
        self.broadcast({"t": "pbx", "k": "twist", "twist": kind, "on": False})
        self._broadcast_state()

    # ---- the tide
    def _tide(self, stage: int) -> None:
        keys = ("tide_hi", "tide_mid", "tide_lo")
        stage = max(0, min(len(self.levels) - 1, stage))
        self.water_y = self.levels[stage]
        on = keys[stage] if stage < len(keys) else ""
        self.set_dynamic_keys([k for k in keys if k != on], False)
        if on:
            self.set_dynamic_keys([on], True)
        self.broadcast({"t": "pbx", "k": "tide", "s": stage, "y": self.water_y})
        self._broadcast_state()

    def _uncover(self) -> None:
        kinds = ("gem", "bar", "chest", "bar", "gem", "pouch", "bar")
        for k, spot in enumerate(self.sunken_marks):
            item = self._new_item(kinds[k % len(kinds)], spot, "sunken")
            item["feat"] = True
        self.broadcast({"t": "pbx", "k": "uncover", "n": len(self.sunken_marks)})

    def _wash(self, moment: float) -> None:
        mid = self.levels[1] if len(self.levels) > 1 else self.water_y
        gone = [i for i in self.items.values()
                if i["src"] == "sunken" and i["state"] == "ground" and i["p"][1] < mid - 0.5]
        for item in gone:
            self.items.pop(item["id"], None)
            self.counts["washed"] += 1
        if gone:
            self.items_dirty = True
            self.broadcast({"t": "pbx", "k": "wash", "ids": [i["id"] for i in gone]})

    # ---- the eruption
    def _lava_bomb(self, moment: float) -> None:
        targets = [p for p in self.playing() if not self._in_lava(p.pos)]
        if targets and self.rng.random() < 0.55:
            who = self.rng.choice(targets)
            x = who.pos[0] + self.rng.uniform(-6.0, 6.0)
            z = who.pos[2] + self.rng.uniform(-6.0, 6.0)
        elif self.rain:
            spot = self.rng.choice(self.rain)
            x, z = spot[0] + self.rng.uniform(-4.0, 4.0), spot[2] + self.rng.uniform(-4.0, 4.0)
        else:
            return
        at = [x, self._ground_at(x, z), z]
        self.hazards.append({"k": "bomb", "at": at, "when": moment + BOMB_WARN, "r": BOMB_RADIUS,
                             "dmg": BOMB_DAMAGE, "knock": BOMB_KNOCK, "team": "", "by": 0})
        self.counts["bombs"] += 1
        self.broadcast({"t": "pbx", "k": "bomb", "a": _r(self.vent), "at": _r(at),
                        "in": BOMB_WARN, "r": BOMB_RADIUS})

    def _spew(self, moment: float) -> None:
        if not self.rain or self._loose() >= LOOSE_CAP + 8:
            return
        spot = self.rng.choice(self.rain)
        x, z = spot[0] + self.rng.uniform(-3.0, 3.0), spot[2] + self.rng.uniform(-3.0, 3.0)
        to = [x, self._ground_at(x, z), z]
        roll = self.rng.random()
        kind = "pouch" if roll < 0.68 else ("bar" if roll < 0.94 else "gem")
        item = self._new_item(kind, self.vent, "spew")
        item["feat"] = True
        seconds = self.rng.uniform(2.6, 3.4)
        self.counts["spews"] += 1
        self._launch(item, self.vent, _ballistic(self.vent, to, seconds), moment)

    # ================================================================= npcs
    def _new_npc(self, kind: str, pos: Sequence[float], hp: float) -> Npc:
        self.next_npc += 1
        npc = Npc(self.next_npc, kind, pos, hp)
        self.npcs[npc.pid] = npc
        return npc

    def _npc_tick(self, dt: float, moment: float) -> None:
        if not self.npcs:
            return
        for npc in list(self.npcs.values()):
            if not npc.alive:
                if moment >= npc.data.get("gone_at", 0.0):
                    self.npcs.pop(npc.pid, None)
                continue
            if npc.kind == "tentacle":
                self._tentacle(npc, moment)
            else:
                self._redcoat(npc, dt, moment)

    def _tentacle(self, npc: Npc, moment: float) -> None:
        npc.pos[1] = self.water_y - 1.0
        if npc.state == "rise":
            if moment >= npc.data.get("ready", 0.0):
                npc.state = "idle"
            return
        if npc.state == "wind":
            if moment >= npc.data["slam_at"]:
                npc.state = "idle"
                npc.data["next"] = moment + self.rng.uniform(*SLAM_EVERY)
                self.counts["slams"] += 1
            return
        if moment < npc.data.get("next", 0.0):
            return
        base = npc.data["base"]
        best, best_s = None, 1e9
        for p in self.playing():
            d = _flat(p.pos, base)
            if d > TENT_REACH or p.pos[1] > base[1] + 14.0:
                continue
            score = d - (12.0 if self._carried(p) is not None else 0.0)
            if score < best_s:
                best, best_s = p, score
        if best is None:
            npc.data["next"] = moment + 1.0
            return
        at = [best.pos[0] + best.vel[0] * 0.3, best.pos[1], best.pos[2] + best.vel[2] * 0.3]
        npc.state = "wind"
        npc.data["slam_at"] = moment + SLAM_WARN
        npc.data["at"] = at
        npc.yaw = math.atan2(at[0] - base[0], at[2] - base[2])
        self.hazards.append({"k": "slam", "at": at, "when": moment + SLAM_WARN, "r": SLAM_RADIUS,
                             "dmg": SLAM_DAMAGE, "knock": SLAM_KNOCK, "team": "", "by": 0,
                             "src": npc.pid})
        self.broadcast({"t": "pbx", "k": "slam", "id": npc.pid, "at": _r(at), "in": SLAM_WARN,
                        "r": SLAM_RADIUS})

    def _redcoat(self, npc: Npc, dt: float, moment: float) -> None:
        data = npc.data
        if npc.state == "aim":
            target = self.players.get(data.get("target", 0))
            if target is not None and target.alive:
                npc.yaw = math.atan2(target.pos[0] - npc.pos[0], target.pos[2] - npc.pos[2])
            if moment >= data["fire_at"]:
                self._volley(npc, target, moment)
                npc.state = "walk"
                data["next_shot"] = moment + self.rng.uniform(*COAT_COOL)
            return
        if moment < data.get("wait", 0.0):
            return
        # a pirate in sight: stop, raise the musket
        if moment >= data.get("next_shot", 0.0):
            target = self._coat_target(npc)
            data["next_shot"] = moment + 0.5
            if target is not None:
                npc.state = "aim"
                npc.vel = [0.0, 0.0, 0.0]
                data["target"] = target.pid
                data["fire_at"] = moment + COAT_AIM
                self.broadcast({"t": "pbx", "k": "aim", "id": npc.pid, "at": target.pid})
                return
        # march on along the route: out of the fort, then round the loop
        route = data["route"]
        leg = int(data.get("leg", 0))
        goal = route[leg % len(route)]
        dx, dy, dz = goal[0] - npc.pos[0], goal[1] - npc.pos[1], goal[2] - npc.pos[2]
        d = math.hypot(dx, dz)
        step = COAT_SPEED * dt
        if d <= step + 1e-6:
            npc.pos = list(goal)
            leg += 1
            if leg >= len(route):
                leg = min(3, len(route) - 1)
            data["leg"] = leg
            npc.vel = [0.0, 0.0, 0.0]
            return
        k = step / d
        npc.pos = [npc.pos[0] + dx * k, npc.pos[1] + dy * k, npc.pos[2] + dz * k]
        npc.vel = [dx / d * COAT_SPEED, 0.0, dz / d * COAT_SPEED]
        npc.yaw = math.atan2(dx, dz)

    def _coat_target(self, npc: Npc) -> Optional[Player]:
        eye = [npc.pos[0], npc.pos[1] + 4.2, npc.pos[2]]
        best, best_s = None, 1e9
        for p in self.playing():
            d = math.dist(p.pos, npc.pos)
            if d > COAT_SIGHT:
                continue
            if not self.line_of_sight(eye, [p.pos[0], p.pos[1] + 3.0, p.pos[2]]):
                continue
            score = d - (20.0 if self._carried(p) is not None else 0.0)
            if score < best_s:
                best, best_s = p, score
        return best

    def _volley(self, npc: Npc, target: Optional[Player], moment: float) -> None:
        eye = [npc.pos[0] + math.sin(npc.yaw) * 1.2, npc.pos[1] + 4.0,
               npc.pos[2] + math.cos(npc.yaw) * 1.2]
        self.counts["volleys"] += 1
        if target is None or not self.in_play(target):
            self.broadcast({"t": "pbx", "k": "volley", "id": npc.pid, "a": _r(eye),
                            "b": _r([eye[0] + math.sin(npc.yaw) * 30.0, eye[1],
                                     eye[2] + math.cos(npc.yaw) * 30.0]), "hit": 0})
            return
        chest = [target.pos[0], target.pos[1] + 3.0, target.pos[2]]
        seen = self.line_of_sight(eye, chest)
        speed = math.hypot(target.vel[0], target.vel[2])
        chance = 0.78 - min(0.4, speed / 40.0)
        hit = seen and math.dist(eye, chest) < COAT_SIGHT + 6.0 and self.rng.random() < chance
        end = chest if hit else [chest[0] + self.rng.uniform(-3.0, 3.0), chest[1] + 1.5,
                                 chest[2] + self.rng.uniform(-3.0, 3.0)]
        self.broadcast({"t": "pbx", "k": "volley", "id": npc.pid, "a": _r(eye), "b": _r(end),
                        "hit": target.pid if hit else 0})
        if not hit:
            return
        dx, dz = target.pos[0] - npc.pos[0], target.pos[2] - npc.pos[2]
        dl = math.hypot(dx, dz) or 1.0
        if self._carried(target) is not None:
            self._drop(target, moment, "shot", fling=[dx / dl * 7.0, 9.0, dz / dl * 7.0])
        self.apply_damage(target, None, COAT_DAMAGE, "a redcoat's musket")
        if target.brain is not None and target.alive:
            target.brain.hurt_by(npc)

    def hit_thing(self, thing, attacker, amount: float, weapon: str, headshot: bool) -> None:
        if isinstance(thing, Npc):
            self._hurt_npc(thing, attacker if isinstance(attacker, Player) else None, amount,
                           weapon)

    def _hurt_npc(self, npc: Npc, attacker: Optional[Player], amount: float, weapon: str) -> None:
        if not npc.alive or npc.state in ("rise", "sink", "gone"):
            return
        npc.health -= amount
        self.counts["npc_hits"] += 1
        if attacker is not None:
            attacker.send({"t": "dealt", "a": round(amount, 1), "hs": False, "target": npc.pid,
                           "hp": max(0, int(npc.health))})
            if npc.kind == "tentacle" and attacker.pid not in npc.data.setdefault("hit_by", set()):
                npc.data["hit_by"].add(attacker.pid)
                self._feat(attacker)
        self.broadcast({"t": "pbx", "k": "nhit", "id": npc.pid,
                        "hp": round(max(0.0, npc.health) / npc.max_health, 2)})
        if npc.health > 0:
            return
        moment = engine.now()
        npc.alive = False
        npc.state = "sink" if npc.kind == "tentacle" else "down"
        npc.data["gone_at"] = moment + 2.0
        self.counts["npc_kills"] += 1
        if npc.kind == "tentacle":
            base = npc.data.get("base") or npc.pos
            floor = self._floor_under(base[0], base[1] + 2.0, base[2])
            self._new_item("gem", [base[0], floor if floor is not None else base[1], base[2]],
                           "kraken")
        else:
            floor = self._floor_under(npc.pos[0], npc.pos[1] + 1.0, npc.pos[2])
            self._new_item("pouch", [npc.pos[0], floor if floor is not None else npc.pos[1],
                                     npc.pos[2]], "coat")
            if attacker is not None:
                self._feat(attacker)
        if attacker is not None:
            attacker.score += 4
            self._stat(attacker, "npcs")
        self.broadcast({"t": "pbx", "k": "ndown", "id": npc.pid,
                        "by": attacker.pid if attacker is not None else 0,
                        "who": attacker.username if attacker is not None else "",
                        "kind": npc.kind, "w": weapon})

    def _feat(self, player: Player) -> None:
        self._stat(player, "feats")
        self.badge(player, "pb_twists")

    # ============================================================ the bots
    def _mind(self, p: Player) -> Dict[str, Any]:
        return p.extra.setdefault("pb_mind", {"toss_at": 0.0, "gun_at": 0.0, "dodge_until": 0.0,
                                              "post": None, "aim": None})

    def bot_role(self, brain) -> str:
        if not self.setting("enabled"):
            return "pirate"
        team = brain.p.team
        counts = self.bots.role_counts(team, brain) if self.bots is not None else {}
        size = sum(counts.values()) + 1
        t = brain.t
        haul, raid = self.pct("haulers"), self.pct("raiding")
        weights = {
            "hauler": 0.08 + haul * (0.8 + t("explore", 0.2) * 0.8 + brain.objective * 0.4),
            "raider": 0.04 + (1.0 - haul) * raid * (0.8 + t("aggression", 0.5) * 0.9
                                                    + t("chaos", 0.1) * 0.4),
            "guard": 0.04 + (1.0 - haul) * (1.0 - raid) * (0.8 + t("support", 0.2) * 0.9
                                                           + t("social", 0.5) * 0.2),
        }
        if counts.get("hauler", 0) < max(1, round(size * haul * 0.6)):
            weights["hauler"] *= 2.0
        if counts.get("guard", 0) >= max(1, round(size * 0.34)):
            weights["guard"] *= 0.2
        if counts.get("raider", 0) >= max(1, round(size * 0.4)):
            weights["raider"] *= 0.25
        roll = brain.rng.random() * sum(weights.values())
        for role, weight in weights.items():
            roll -= weight
            if roll <= 0:
                return role
        return "hauler"

    def bot_goal_weights(self, brain, weights: Dict[str, float]) -> Dict[str, float]:
        if not self.setting("enabled"):
            return weights
        weights["objective"] = weights.get("objective", 0.5) * 2.4 + 0.5
        weights["fight"] = weights.get("fight", 0.3) * (0.5 + self.pct("aggression"))
        weights["afk"] = weights.get("afk", 0.0) * 0.3
        weights["explore"] = weights.get("explore", 0.0) * 0.4
        return weights

    def bot_urgent(self, brain) -> bool:
        if self.phase != "active" or not self.setting("enabled"):
            return False
        p = brain.p
        if p.extra.get("pb_act") or engine.now() < self._mind(p).get("dodge_until", 0.0):
            return True
        item = self._carried(p)
        if item is None:
            return False
        # a pouch in hand does not stop a scrapper picking a fight
        return item["kind"] in TWO_HANDS or not self._mind(p).get("scrapper")

    def bot_tick(self, moment: float) -> None:
        if not self.nav_scrubbed and self.lava:
            self._scrub_lava()
        if self.phase != "active" or self.bots is None:
            return
        if self.lava:
            self._bot_rims(moment)
        # a ring about to come down: the quick step out of it
        if self.hazards:
            for brain in self.bots.brains.values():
                p = brain.p
                if not self.in_play(p):
                    continue
                for h in self.hazards:
                    if h.get("team") and h["team"] == p.team:
                        continue
                    left = h["when"] - moment
                    if left > 1.3 or left < 0.0 or _flat(p.pos, h["at"]) > h["r"] + 1.2:
                        continue
                    mind = self._mind(p)
                    if moment < mind.get("dodge_until", 0.0) or \
                            brain.rng.random() > 0.35 + brain.skill * 0.55:
                        mind["dodge_until"] = max(mind.get("dodge_until", 0.0), h["when"])
                        continue
                    dx, dz = p.pos[0] - h["at"][0], p.pos[2] - h["at"][2]
                    dl = math.hypot(dx, dz)
                    if dl < 0.5:
                        a = brain.rng.uniform(0.0, 2.0 * math.pi)
                        dx, dz, dl = math.sin(a), math.cos(a), 1.0
                    out = h["r"] + 3.0
                    brain.waypoints = [[h["at"][0] + dx / dl * out, p.pos[1],
                                        h["at"][2] + dz / dl * out]]
                    brain.dest_key = "pb_dodge"
                    mind["dodge_until"] = h["when"] + 0.2
                    break

    def _bot_rims(self, moment: float) -> None:
        """Bots keep out of the lava the way a careful person does.  One on
        the very rim of a trench (a body half over the edge still stands)
        steps back onto the bank; one about to sail over an edge in mid-hop
        stops dead and comes down where it took off; one up on a bridge's
        parapet steps down onto the deck.  A bot that was knocked there is
        left to the lava."""
        for brain in self.bots.brains.values():
            p = brain.p
            if not self.in_play(p) or p.pos[1] < self.lava_y:
                continue
            if moment < p.extra.get("launch_until", 0.0):
                continue
            x, y, z = p.pos
            bridge = next((r for r in self.bridges if _in_rect(r, p.pos)), None)
            if bridge is not None and y > bridge[4] - 0.3:
                if not brain.airborne and y > bridge[4] + 1.0:
                    brain.waypoints = [[x, bridge[4], (bridge[2] + bridge[3]) / 2.0]]
                    brain.dest_key = "pb_rim"
                    brain.repath_at = moment + 1.0
                continue
            inside = [r for r in self.lava if _in_rect(r, p.pos)]
            if not inside:
                if brain.airborne:
                    ahead = [x + p.vel[0] * 0.15, y, z + p.vel[2] * 0.15]
                    if any(_in_rect(r, ahead) for r in self.lava) and \
                            not any(_in_rect(r, ahead) for r in self.bridges):
                        brain.waypoints = []
                        brain.dest_key = ""
                        brain.repath_at = moment + 0.5
                continue
            best = None
            for r in inside:
                for gap, ex, ez in ((x - r[0], r[0] - 2.5, z), (r[1] - x, r[1] + 2.5, z),
                                    (z - r[2], x, r[2] - 2.5), (r[3] - z, x, r[3] + 2.5)):
                    spot = [ex, y, ez]
                    if any(_in_rect(o, spot) for o in self.lava):
                        continue
                    if best is None or gap < best[0]:
                        best = (gap, spot)
            if best is None:
                continue
            brain.waypoints = [best[1]]
            brain.dest_key = "pb_rim"
            brain.repath_at = moment + 1.0

    def _scrub_lava(self) -> None:
        """The lava is a floor as far as the bots' map of the place goes (a
        hot one), and so is the top of a bridge's parapet and the very rim
        of a trench, where a body half over the edge still counts as
        standing.  Every way onto any of those is made too dear to take, so
        a bot keeps to the banks and crosses on the bridge decks.  The graph
        is this map's alone."""
        grid = getattr(self.bots, "nav", None) if self.bots is not None else None
        if grid is None or not grid.ready:
            return
        self.nav_scrubbed = True
        hot = set()
        for node in range(grid.size):
            pos = (grid.px[node], grid.py[node], grid.pz[node])
            if not any(_in_rect(r, pos, 1.2) for r in self.lava):
                continue
            deck = any(_in_rect(r, pos) and abs(pos[1] - r[4]) < 0.3 for r in self.bridges)
            if not deck:
                hot.add(node)
        if not hot:
            return
        for k in range(len(grid.out_to)):
            if grid.out_to[k] in hot:
                grid.out_cost[k] = 1e6
        for node in hot:
            for k in range(grid.in_off[node], grid.in_off[node + 1]):
                grid.in_cost[k] = 1e6

    def _claimed(self, key: str, p: Player, moment: float, share: int = 1) -> bool:
        holders = [pid for (k, pid), until in self.claims.items()
                   if k == key and pid != p.pid and until > moment and pid in self.players
                   and self.players[pid].alive]
        return len(holders) >= share

    def _claim(self, key: str, p: Player, moment: float) -> None:
        self.claims = {kp: until for kp, until in self.claims.items() if until > moment}
        self.claims[(key, p.pid)] = moment + 6.0

    def bot_objective(self, brain) -> None:
        p = brain.p
        if not self.setting("enabled"):
            super().bot_objective(brain)
            return
        if self.phase != "active":
            self.doing(brain, "waiting on deck")
            return
        moment = engine.now()
        mind = self._mind(p)
        if moment < mind.get("dodge_until", 0.0):
            self.doing(brain, "getting out of the way")
            return
        item = self._carried(p)
        if item is not None:
            self._bot_carry(brain, item, mind, moment)
            return
        act = p.extra.get("pb_act")
        if act:
            brain.waypoints = []
            if act["k"] == "dig":
                self.doing(brain, "digging at %s" % self.digs[act["i"]].get("name", "an X"))
            else:
                self.doing(brain, "robbing the %s's hold" % self.team_name(act["team"]))
            return
        if self._bot_cannon(brain, mind, moment):
            return
        role = getattr(brain, "role", "hauler")
        if role == "raider" and self._bot_raid(brain, mind, moment):
            return
        if role == "guard" and self._bot_guard(brain, mind, moment):
            return
        self._bot_haul(brain, mind, moment)

    def _bot_carry(self, brain, item: Dict[str, Any], mind: Dict[str, Any], moment: float) -> None:
        p = brain.p
        hold = self.holds.get(p.team)
        if hold is None:
            return
        brain.go(list(hold["p"]), "pb_home", precise=True)
        home = _flat(p.pos, hold["p"])
        self.doing(brain, "carrying %s home" % NAMES[item["kind"]])
        if item["kind"] in TWO_HANDS:
            self.callout(brain, ["got a chest", "cover me", "escort me", "chest coming home",
                                 "yarr got one"] if item["kind"] == "chest" else
                         ["got the idol", "cover me", "idol coming home", "help"],
                         "pb_carry", chance=0.5, every=30.0, team=True)
        if moment < mind.get("toss_at", 0.0) or home < 20.0:
            return
        mind["toss_at"] = moment + 1.5
        threat = None
        for other in self.players.values():
            if other.team != p.team and self.in_play(other) and math.dist(other.pos, p.pos) < 16.0:
                threat = other
                break
        if threat is None:
            return
        if brain.rng.random() > 0.25 + 0.4 * brain.t("support", 0.2) + 0.3 * brain.t("chaos", 0.1):
            return
        best, best_s = None, 1e9
        for mate in self.players.values():
            if mate is p or mate.team != p.team or not self.in_play(mate) or \
                    self._carried(mate) is not None:
                continue
            d = math.dist(mate.pos, p.pos)
            if not 8.0 < d < 24.0 or _flat(mate.pos, hold["p"]) > home - 6.0:
                continue
            if not self.line_of_sight([p.pos[0], p.pos[1] + 3.6, p.pos[2]],
                                      [mate.pos[0], mate.pos[1] + 2.6, mate.pos[2]]):
                continue
            if d < best_s:
                best, best_s = mate, d
        if best is None:
            return
        origin = [p.pos[0], p.pos[1] + 3.6, p.pos[2]]
        aim = [best.pos[0], best.pos[1] + 2.6, best.pos[2]]
        flat = _flat(origin, aim)
        seconds = 0.35 + flat / 26.0
        if self._toss(p, normalise([aim[0] - origin[0], 0.0, aim[2] - origin[2]]), moment,
                      velocity=_ballistic(origin, aim, seconds)):
            mind["toss_at"] = moment + 8.0
            self.callout(brain, ["catch", "heads up", "take it", "go go", "yours"], "pb_toss",
                         chance=0.7, every=15.0, team=True)

    def _bot_haul(self, brain, mind: Dict[str, Any], moment: float) -> None:
        p = brain.p
        greed = 0.5 + self.pct("aggression") * 0.5
        best, best_s, best_key = None, 0.0, ""
        tentacles = [n.data.get("base") or n.pos for n in self.npcs.values()
                     if n.alive and n.kind == "tentacle"]
        for item in self.items.values():
            if item["state"] != "ground" or self._in_lava(item["p"]):
                continue
            lock = item.get("lock") or (0, 0.0)
            if lock[0] == p.pid and moment < lock[1]:
                continue
            key = "i%d" % item["id"]
            if self._claimed(key, p, moment, 2 if item["kind"] == "idol" else 1):
                continue
            d = math.dist(item["p"], p.pos)
            if d > 240.0:
                continue
            score = (VALUE[item["kind"]] + 2.0) / (d + 18.0)
            if item["kind"] == "idol":
                score *= 1.6
            if item.get("feat"):
                score *= 1.3
            if any(_flat(item["p"], b) < TENT_REACH for b in tentacles):
                score *= 0.5 * greed
            if score > best_s:
                best, best_s, best_key = item, score, key
        for i, dig in enumerate(self.digs):
            if not dig["live"]:
                continue
            key = "x%d" % i
            if self._claimed(key, p, moment):
                continue
            d = math.dist(dig["p"], p.pos)
            score = 10.0 / (d + 18.0 + DIG_SECONDS * 6.0)
            if score > best_s:
                best, best_s, best_key = dig, score, key
        if best is None:
            spot = self.random_spot(brain.rng)
            if spot is not None and not brain.waypoints and not self._in_lava(spot):
                brain.go(spot, "pb_roam")
            self.doing(brain, "looking for treasure")
            return
        self._claim(best_key, p, moment)
        if best_key.startswith("x"):
            i = int(best_key[1:])
            if _flat(best["p"], p.pos) < DIG_REACH - 0.8 and abs(best["p"][1] - p.pos[1]) < 2.5:
                brain.waypoints = []
                p.yaw = math.atan2(best["p"][0] - p.pos[0], best["p"][2] - p.pos[2])
                p.extra["using"] = True
                self.use(p, {})
                self.doing(brain, "digging at %s" % best.get("name", "an X"))
                self.callout(brain, ["digging", "found an X", "cover me", "x marks the spot"],
                             "pb_dig", chance=0.3, every=40.0, team=True)
                return
            brain.go(list(best["p"]), "pb_" + best_key, precise=True)
            self.doing(brain, "heading for the X at %s" % best.get("name", "the beach"))
            return
        brain.go(list(best["p"]), "pb_" + best_key, precise=True)
        where = self._place(best["p"])
        self.doing(brain, "going for %s%s" % (NAMES[best["kind"]], (" at " + where) if where else ""))
        if best["kind"] == "idol":
            self.callout(brain, ["IDOL", "going for the idol", "idol's up", "get the idol"],
                         "pb_idol", chance=0.6, every=40.0)

    def _bot_raid(self, brain, mind: Dict[str, Any], moment: float) -> bool:
        p = brain.p
        other = "blue" if p.team == "red" else "red"
        hold = self.holds.get(other)
        raiding = moment < mind.get("raid_until", 0.0)
        # a carrier of theirs: anybody close, and a chest or the idol from
        # further off -- but a raid under way only turns for one right there
        reach = (10.0 + 8.0 * self.pct("aggression")) if raiding else \
            (40.0 + 50.0 * self.pct("aggression"))
        best, best_s = None, 1e9
        for o in self.players.values():
            if o.team == p.team or not self.in_play(o):
                continue
            item = self._carried(o)
            if item is None:
                continue
            d = math.dist(o.pos, p.pos)
            big = item["kind"] in TWO_HANDS
            if d > (reach * 2.0 if big else reach):
                continue
            score = d - (40.0 if big else 0.0)
            if score < best_s:
                best, best_s = o, score
        if best is not None:
            if brain.target != best.pid and brain._sees(best):
                brain.target = best.pid
                brain.target_since = moment
            brain.go([best.pos[0], best.pos[1], best.pos[2]], "pb_hunt%d" % best.pid)
            item = self._carried(best)
            self.doing(brain, "hunting %s, who has %s" % (best.username,
                                                          NAMES[item["kind"]] if item else "loot"))
            self.callout(brain, ["get the carrier", "they have a chest", "stop them", "on it"],
                         "pb_hunt", chance=0.35, every=30.0, team=True)
            return True
        if hold is None or self.points.get(other, 0) < RAID_TAKE or \
                moment < self.raid_cool.get(other, 0.0):
            mind["raid_until"] = 0.0
            return False
        if not raiding:
            if moment < mind.get("raid_think", 0.0):
                return False
            mind["raid_think"] = moment + 6.0
            # a bold raider goes when the ship looks empty: the crew comes
            # back to life right by its hold
            guards = sum(1 for o in self.players.values()
                         if o.team == other and self.in_play(o) and _flat(o.pos, hold["p"]) < 22.0)
            if guards >= 3 or brain.rng.random() > 0.3 + 0.7 * self.pct("raiding"):
                return False
            mind["raid_until"] = moment + 45.0
        elif _flat(p.pos, hold["p"]) < 40.0 and not self._on_hold(hold, p.pos, 0.2):
            # nearly there, and their deck has filled up: not now
            guards = sum(1 for o in self.players.values()
                         if o.team == other and self.in_play(o) and _flat(o.pos, hold["p"]) < 18.0)
            if guards >= 3:
                mind["raid_until"] = 0.0
                mind["raid_think"] = moment + 10.0
                return False
        if self._on_hold(hold, p.pos, 0.2):
            brain.waypoints = []
            p.extra["using"] = True
            self.use(p, {})
            self.doing(brain, "robbing the %s's hold" % self.team_name(other))
            self.callout(brain, ["yoink", "robbing them", "free gold", "lol their hold"],
                         "pb_rob", chance=0.4, every=40.0)
            return True
        brain.go(list(hold["p"]), "pb_raid", precise=True)
        self.doing(brain, "sneaking aboard the %s" % SHIP_NAMES.get(other, "enemy ship"))
        return True

    def _bot_guard(self, brain, mind: Dict[str, Any], moment: float) -> bool:
        p = brain.p
        hold = self.holds.get(p.team)
        if hold is None:
            return False
        intruder, near = None, 34.0
        for other in self.players.values():
            if other.team == p.team or not self.in_play(other):
                continue
            d = _flat(other.pos, hold["p"])
            if d < near:
                intruder, near = other, d
        if intruder is not None:
            if brain.target != intruder.pid and brain._sees(intruder):
                brain.target = intruder.pid
                brain.target_since = moment
            brain.go(list(intruder.pos), "pb_repel%d" % intruder.pid)
            self.doing(brain, "repelling boarders")
            self.callout(brain, ["raiders!", "they're on the ship", "defend the hold", "boarders"],
                         "pb_board", chance=0.5, every=30.0, team=True)
            return True
        # a crewmate's treasure coming home with somebody on its tail: meet it
        for mate in self.players.values():
            if mate.team != p.team or mate is p or self._carried(mate) is None:
                continue
            if _flat(mate.pos, hold["p"]) < 70.0 and any(
                    o.team != p.team and self.in_play(o) and math.dist(o.pos, mate.pos) < 18.0
                    for o in self.players.values()):
                brain.go(list(mate.pos), "pb_escort%d" % mate.pid)
                self.doing(brain, "covering %s" % mate.username)
                return True
        if brain.rng.random() < 0.25:
            return False           # a guard picks up what is close to the ship, too
        post = mind.get("post")
        if post is None:
            a = brain.rng.uniform(0.0, 2.0 * math.pi)
            post = [hold["p"][0] + math.sin(a) * 4.0, hold["p"][1], hold["p"][2] + math.cos(a) * 9.0]
            mind["post"] = post
        if _flat(post, p.pos) > 5.0:
            brain.go(list(post), "pb_post")
        else:
            brain.waypoints = []
        self.doing(brain, "guarding the %s" % SHIP_NAMES.get(p.team, "ship"))
        return True

    def _bot_cannon(self, brain, mind: Dict[str, Any], moment: float) -> bool:
        p = brain.p
        keen = self.pct("cannons")
        if keen <= 0.0 or moment < mind.get("gun_at", 0.0):
            return False
        role = getattr(brain, "role", "hauler")
        mine = [c for c in self.cannons if c["team"] == p.team and moment >= c["ready"]]
        if not mine:
            return False
        for c in mine:
            target = self._cannon_target(c, p)
            if target is None:
                continue
            here = _flat(c["p"], p.pos) < CANNON_REACH - 0.6 and abs(p.pos[1] - c["p"][1]) < 2.0
            if here:
                lead = 1.1 + _flat(c["p"], target.pos) / 95.0
                spread = 7.0 * (1.2 - brain.skill)
                aim = [target.pos[0] + target.vel[0] * lead * 0.6 + brain.rng.gauss(0, spread),
                       target.pos[1],
                       target.pos[2] + target.vel[2] * lead * 0.6 + brain.rng.gauss(0, spread)]
                p.yaw = math.atan2(aim[0] - p.pos[0], aim[2] - p.pos[2])
                brain.waypoints = []
                if self._fire_cannon(p, c, aim, moment):
                    mind["gun_at"] = moment + brain.rng.uniform(1.0, 3.0)
                    self.doing(brain, "firing the cannon")
                    self.callout(brain, ["FIRE", "broadside", "boom", "eat cannonball",
                                         "fire in the hole"], "pb_fire", chance=0.4, every=25.0)
                return True
            wants = (role == "guard" and brain.rng.random() < 0.3 + 0.7 * keen) or \
                (_flat(c["p"], p.pos) < 26.0 and brain.rng.random() < 0.25 * keen
                 + 0.3 * brain.t("chaos", 0.1))
            if wants and _flat(c["p"], p.pos) < 60.0:
                yaw = float(c.get("yaw", 0.0))
                spot = [c["p"][0] - math.sin(yaw) * 3.0, c["p"][1], c["p"][2] - math.cos(yaw) * 3.0]
                brain.go(spot, "pb_gun%d" % c["i"], precise=True)
                self.doing(brain, "running to the cannon")
                return True
        mind["gun_at"] = moment + 1.5
        return False

    def _cannon_target(self, c: Dict[str, Any], p: Player):
        yaw = float(c.get("yaw", 0.0))
        best, best_s = None, 1e9
        targets = [o for o in self.players.values()
                   if o.team != p.team and self.in_play(o)] + \
            [n for n in self.npcs.values() if n.alive and n.state in ("idle", "wind", "walk", "aim")]
        for o in targets:
            d = _flat(o.pos, c["p"])
            if not CANNON_MIN + 4.0 < d < CANNON_MAX - 4.0:
                continue
            off = abs(_wrap(math.atan2(o.pos[0] - c["p"][0], o.pos[2] - c["p"][2]) - yaw))
            if off > CANNON_ARC - 0.05:
                continue
            score = d
            if not isinstance(o, Npc) and self._carried(o) is not None:
                score -= 40.0
            if score < best_s:
                best, best_s = o, score
        return best

    def bot_context(self) -> List[str]:
        lines = ["You are playing Plunder Bay, a pirate treasure haul: carry treasure into your "
                 "own ship's hold; first crew to %d doubloons wins." % TARGET]
        lines.append("Holds: %s %d, %s %d." % (self.team_name("red"), self.points.get("red", 0),
                                               self.team_name("blue"), self.points.get("blue", 0)))
        if self.idol_state in ("altar", "ground"):
            lines.append("The cursed idol is up for grabs.")
        elif self.idol_state == "carried":
            who = next((p for p in self.players.values() if (self._carried(p) or {}).get("kind")
                        == "idol"), None)
            if who is not None:
                lines.append("%s is carrying the cursed idol." % who.username)
        if self.twist["on"]:
            lines.append("Right now: %s." % TWIST_NAMES.get(self.twist["kind"], "the twist"))
        return lines

    def bot_me(self, brain) -> Dict[str, Any]:
        p = brain.p
        item = self._carried(p)
        out = super().bot_me(brain)
        out["context"] = list(out.get("context") or [])
        out["context"].append("you are a %s" % getattr(brain, "role", "pirate"))
        if item is not None:
            out["context"].append("you are carrying %s" % NAMES[item["kind"]])
        return out

    def bot_spread(self, players: List[Player]) -> None:
        for player in players:
            if player.brain is not None:
                player.brain.on_spawn()

    # ============================================================== state
    def _stat(self, player: Player, key: str, amount: float = 1.0) -> None:
        stats = self.round_stats.setdefault(player.pid, {})
        stats[key] = stats.get(key, 0.0) + amount

    def _place(self, pos: Sequence[float]) -> str:
        best, best_d = "", 1e9
        for p, name in self.landmarks:
            d = math.hypot(p[0] - pos[0], p[2] - pos[2])
            if d < best_d:
                best, best_d = name, d
        return best if best_d < 60 else ""

    def _event(self, kind: str, player: Optional[Player], team: str, **extra: Any) -> None:
        moment = engine.now()
        key = kind + (team or "")
        if moment - self.events_said.get(key, -99.0) < 6.0:
            return
        self.events_said[key] = moment
        data = {"world": "plunder_bay", "by": player.username if player else "",
                "by_team": player.team if player else "", "team": team}
        data.update(extra)
        if self.bots is not None:
            self.bots.on_game_event(kind, data)

    def _broadcast_state(self) -> None:
        self.broadcast({"t": "pbs", "s": self.hud_state()})

    def hud_state(self) -> Dict[str, Any]:
        moment = engine.now()
        tw = self.twist
        idol_by = 0
        if self.idol_state == "carried":
            item = self.items.get(self.idol_id)
            idol_by = item["by"] if item else 0
        return {"pb": {"pts": dict(self.points), "target": TARGET, "twist": tw["kind"],
                       "on": tw["on"], "left": round(max(0.0, tw["until"] - moment), 1)
                       if tw["on"] else 0, "idol": self.idol_state, "idol_by": idol_by,
                       "water": self.water_y}}

    def snapshot_extra(self) -> Any:
        if self.phase not in ("active", "setup"):
            return None
        out: Dict[str, Any] = {"w": self.water_y}
        carried = {}
        flying = []
        for item in self.items.values():
            if item["state"] == "carried":
                carried[str(item["by"])] = KIND_CODE[item["kind"]]
            elif item["state"] == "fly":
                flying.append([item["id"], KIND_CODE[item["kind"]]] + _r(item["p"]))
        if carried:
            out["cr"] = carried
        if flying:
            out["fl"] = flying
        acts = [[p.pid, 0 if p.extra["pb_act"]["k"] == "dig" else 1]
                for p in self.players.values() if p.extra.get("pb_act")]
        if acts:
            out["ac"] = acts
        if self.npcs:
            out["np"] = [[n.pid, 0 if n.kind == "tentacle" else 1, round(n.pos[0], 2),
                          round(n.pos[1], 2), round(n.pos[2], 2), round(n.yaw, 2), n.state,
                          round(max(0.0, n.health) / n.max_health, 2)]
                         for n in self.npcs.values()]
        return out

    def me_state(self, player: Player) -> Dict[str, Any]:
        item = self._carried(player)
        act = player.extra.get("pb_act")
        frac = 0.0
        if act:
            frac = act["t"] / (DIG_SECONDS if act["k"] == "dig" else RAID_SECONDS)
        return {"carry": item["kind"] if item is not None else "",
                "act": act["k"] if act else "", "frac": round(min(1.0, frac), 2)}

    def score_row(self, player: Player, row: Dict[str, Any]) -> None:
        stats = self.round_stats.get(player.pid, {})
        row["plunder"] = int(stats.get("plunder", 0))
        item = self._carried(player)
        row["carry"] = item["kind"] if item is not None else ""

    def result_columns(self) -> List[List[str]]:
        return [["plunder", "Plunder"], ["chests", "Chests"], ["raids", "Raids"],
                ["kills", "Kills"], ["deaths", "Deaths"], ["score", "Score"]]

    def results_rows(self) -> List[Dict[str, Any]]:
        rows = []
        for p in self.players.values():
            if p.team not in self.TEAMS:
                continue
            stats = self.round_stats.get(p.pid, {})
            rows.append({"id": p.pid, "name": p.username, "team": p.team, "score": p.score,
                         "plunder": int(stats.get("plunder", 0)),
                         "chests": int(stats.get("chests", 0)),
                         "raids": int(stats.get("raids", 0)), "kills": p.kills,
                         "deaths": p.deaths})
        rows.sort(key=lambda r: (-r["plunder"], -r["score"], r["name"].lower()))
        return rows

    def awards(self, winner: str) -> List[str]:
        out = []

        def top(key: str) -> Tuple[float, Optional[Player]]:
            best = max(((s.get(key, 0.0), pid) for pid, s in self.round_stats.items()),
                       default=(0.0, 0))
            return best[0], self.players.get(best[1])

        for key, line, least in (("plunder", "Richest pirate: %s (%d doubloons)", 1),
                                 ("chests", "Heavy lifter: %s (%d chests)", 1),
                                 ("idols", "Bearer of the idol: %s", 1),
                                 ("raids", "Scourge of the seas: %s (%d raids)", 1),
                                 ("cannon_hits", "Master gunner: %s (%d hits)", 2),
                                 ("stops", "Pirate hunter: %s (%d carriers cut down)", 2)):
            amount, who = top(key)
            if who is not None and amount >= least:
                out.append(line % ((who.username,) if line.count("%") == 1
                                   else (who.username, int(amount))))
            if len(out) >= 4:
                break
        return out

    def result_extra(self, winner: str) -> Dict[str, Any]:
        return {"points": dict(self.points), "target": TARGET}

    def on_round_over(self, winner: str, reason: str, winners: List[Player]) -> None:
        for player in winners:
            self.badge(player, "pb_wins")
            self.badge(player, "pb_area_" + self.area_id, 1, "max")
        self.npcs = {}
        self.hazards = []

    def describe(self) -> Dict[str, Any]:
        out = super().describe()
        out["points"] = dict(self.points)
        return out

    def sleep_extra(self) -> Dict[str, Any]:
        lead = max(self.points.values()) if self.points else 0
        return {"points": dict(self.points), "progress": round(min(0.95, lead / float(TARGET)), 3)}

    def resume_progress(self, progress: float, state: Dict[str, Any]) -> None:
        points = state.get("points") or {}
        for team in self.TEAMS:
            try:
                self.points[team] = max(0, min(TARGET - 20, int(points.get(team, 0) or 0)))
            except (TypeError, ValueError):
                self.points[team] = 0
        self._broadcast_state()

    def observe(self) -> Dict[str, Any]:
        return {"pts": dict(self.points), "items": len(self.items),
                "carried": sum(1 for i in self.items.values() if i["state"] == "carried"),
                "npcs": len(self.npcs), "twist": self.twist["on"]}

    def selftest(self, result: Dict[str, Any]) -> List[Tuple[str, bool, Any]]:
        c = self.counts
        return [
            ("treasure is picked up", c["picks"] >= 10, c["picks"]),
            ("treasure is banked in the holds", c["banks"] >= 5,
             "%d banks, %d doubloons" % (c["banks"], c["banked"])),
            ("chests are dug up", c["digs"] >= 1, c["digs"]),
            ("pirates fight with their own weapons", c["melee_kills"] + c["ranged_kills"] >= 2,
             "%d up close, %d at range" % (c["melee_kills"], c["ranged_kills"])),
            ("the cannons fire", c["cannons"] >= 1, c["cannons"]),
            ("the twist comes round", c["twists"] >= 1, c["twists"]),
            ("carriers drop what they carry", c["drops"] >= 1, c["drops"]),
        ]


WORLD_CLASS = PlunderBayWorld
