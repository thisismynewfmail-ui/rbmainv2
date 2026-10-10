"""Gear: everything an event weapon or held item does beyond point-and-shoot.

The base engine (instance.py) knows four kinds of hotbar item -- hitscan,
melee, projectile and support -- and a damage number.  The holiday weapons
(app/models/holidays) are written as those kinds plus *traits*: a staff that
raises zombies, a sword that dazzles, a bomb that sticks and ticks, a pot of
gold that rains coins, a bell that stuns every third swing.  This module is
where the traits live.  One ``Gear`` belongs to each round
(``instance.gear``) and is called from the engine at a handful of points:

* firing   -- ``fire`` runs the gear kinds (beam, cone, strike, deploy,
              summon, ability, consume); ``prepare``/``launch``/``after``
              wrap the ordinary kinds (pressure, streaks, volleys, meters).
* damage   -- every hit goes through ``adjust`` (what it is worth: buffs,
              crits, marks, shields, cheating death) and ``landed`` (what it
              leaves behind: burning, slowing, lifesteal, on-kill effects).
* things   -- projectiles are steered and stuck (``steer``/``impact``/
              ``exploded``), and the round's own objects -- minions,
              turrets, zones, traps, pickups, strikes -- tick in ``tick``.
* the wire -- per-player status bits ride in the snapshot, minions as
              ``mn`` rows, deployables in the 1 Hz state; the owner gets
              ``st`` (their statuses), ``cd`` (cooldowns) and ``meter``.

**Statuses** (``apply``) sit on anything with a ``pid`` -- players, bots,
the infected, minions -- and run out on their own.  Hurting ones tick
through the world's own ``apply_damage``, so a zombie set alight in Last
Light burns the way it would be shot.  On players the client enforces the
movement ones (static/js/game/gear.js) and the host checks them.

  burn, poison  damage over time (value = per second)
  bleed         damage over time that stacks
  slow          moves value slower (0.3 = 30%); the strongest applies
  freeze        stacking chill; enough stacks freeze solid (root)
  root          cannot move;  stun  cannot move or use anything
  jumpless      cannot jump;  silence  cannot use gear (abilities, items)
  blind         a screen full of confetti, ink or light
  mark          takes value more damage (0.3 = +30%) from everyone
  dazzle        stacks; enough of them mark
  reveal        shown to the other side through walls
  polymorph     a toad: slow, and cannot use anything
  haste, might, regen, shield, lowgrav, cloak, cheat, block, crit
                the good ones: faster, harder-hitting, mending,
                damage-soaking, floaty, near-invisible, a death refused,
                a parry, a chance of a critical hit

**Item stats** the module reads (a weapon's ``data.stats``) are listed with
the code that reads them; app/models/holidays/kit.py ``Event.weapon`` is
where they are written.
"""
from __future__ import annotations

import math
import random
from contextlib import contextmanager
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

GEAR_KINDS = frozenset(("beam", "cone", "strike", "deploy", "summon", "ability", "consume"))
# kinds that run on a cooldown rather than a magazine
CHARGED_KINDS = frozenset(("strike", "deploy", "summon", "ability", "consume"))

STATUS_BITS = {
    "burn": 1, "slow": 2, "root": 4, "stun": 8, "freeze": 16, "mark": 32,
    "blind": 64, "poison": 128, "bleed": 256, "polymorph": 512, "cloak": 1024,
    "shield": 2048, "haste": 4096, "reveal": 8192, "might": 16384, "regen": 32768,
    "jumpless": 65536, "silence": 131072, "lowgrav": 262144, "dazzle": 524288,
    "block": 1048576, "crit": 2097152,
}
HARMFUL = frozenset(("burn", "poison", "bleed", "slow", "freeze", "root", "stun",
                     "jumpless", "silence", "blind", "mark", "dazzle", "reveal",
                     "polymorph"))
DOTS = frozenset(("burn", "poison", "bleed"))
DOT_STEP = 0.5               # seconds between damage-over-time ticks
MINION_BASE = 200000         # minion ids: past players (small) and infected (100000+)
MAX_MINIONS = 24             # in a round, all owners together
MAX_DEPLOYABLES = 40
EYE = 5.05


def _now() -> float:
    from .instance import now
    return now()


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _norm(v: Sequence[float]) -> List[float]:
    length = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
    if length < 1e-9:
        return [0.0, 0.0, 1.0]
    return [v[0] / length, v[1] / length, v[2] / length]


def _look(yaw: float, pitch: float) -> List[float]:
    cp = math.cos(pitch)
    return [math.sin(yaw) * cp, math.sin(pitch), math.cos(yaw) * cp]


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _pair(value: Any, a: float = 0.0, b: float = 0.0) -> Tuple[float, float]:
    """[x, y] (or a bare x) as two floats."""
    if isinstance(value, (list, tuple)):
        return (_num(value[0], a) if len(value) > 0 else a,
                _num(value[1], b) if len(value) > 1 else b)
    return (_num(value, a), b)


# ================================================================= things
class Status:
    __slots__ = ("until", "value", "src", "stacks", "tick_at", "weapon")

    def __init__(self, until: float, value: float, src: Optional[int], weapon: str):
        self.until = until
        self.value = value
        self.src = src
        self.stacks = 1
        self.tick_at = 0.0
        self.weapon = weapon


class Minion:
    """Something a player summoned: zombies from the Restless Dead, chicks
    from the Hatchling Staff, a balloon dog, a decoy.  Duck-typed like a
    Player where the engine needs one (pos, team, alive, hitbox, send)."""

    __slots__ = ("pid", "owner", "team", "kind", "item", "name", "pos", "vel", "yaw",
                 "health", "max_health", "alive", "until", "spec", "next_attack",
                 "target", "anim", "grounded", "username", "brain", "npc", "pitch",
                 "scale", "spawn_protect_until", "extra", "airborne")

    def __init__(self, pid: int, owner, spec: Dict[str, Any], item: str, pos, until: float):
        self.pid = pid
        self.owner = owner.pid
        self.team = owner.team
        self.kind = str(spec.get("model") or "avatar")
        self.item = item
        self.name = str(spec.get("name") or "Minion")
        self.username = "%s's %s" % (owner.username, self.name)
        self.pos = [float(pos[0]), float(pos[1]), float(pos[2])]
        self.vel = [0.0, 0.0, 0.0]
        self.yaw = owner.yaw
        self.pitch = 0.0
        self.max_health = max(1.0, _num(spec.get("hp"), 40))
        self.health = self.max_health
        self.alive = True
        self.until = until
        self.spec = spec
        self.next_attack = 0.0
        self.target: Optional[int] = None
        self.anim = "idle"
        self.grounded = True
        self.airborne = False
        self.brain = None
        self.npc = True
        self.scale = _num(spec.get("scale"), 1.0) or 1.0
        self.spawn_protect_until = 0.0
        self.extra: Dict[str, Any] = {}

    def hitbox(self):
        w, h, d = 3.0 * self.scale, 5.2 * self.scale, 2.0 * self.scale
        x, y, z = self.pos
        return ([x - w / 2, y, z - d / 2], [x + w / 2, y + h, z + d / 2])

    def head_box(self):
        lo, hi = self.hitbox()
        return ([lo[0], hi[1] - 1.4 * self.scale, lo[2]], hi)

    def centre(self) -> List[float]:
        return [self.pos[0], self.pos[1] + 2.4 * self.scale, self.pos[2]]

    def send(self, payload: Dict[str, Any]) -> None:
        pass


class Deployable:
    """A thing placed in the world: a turret, a zone, a trap, a mine, a
    banner, a hazard circling its owner, coins to pick up."""

    __slots__ = ("ident", "owner", "team", "kind", "item", "pos", "yaw", "until",
                 "spec", "next_act", "armed_at", "hit_at", "born")

    def __init__(self, ident: int, owner_pid: int, team: str, kind: str, item: str,
                 pos, yaw: float, until: float, spec: Dict[str, Any]):
        self.ident = ident
        self.owner = owner_pid
        self.team = team
        self.kind = kind
        self.item = item
        self.pos = [float(pos[0]), float(pos[1]), float(pos[2])]
        self.yaw = yaw
        self.until = until
        self.spec = spec
        self.next_act = 0.0
        self.armed_at = _now() + _num(spec.get("arm"), 0.0)
        self.hit_at: Dict[int, float] = {}
        self.born = _now()

    def row(self, moment: float) -> List[Any]:
        return [self.ident, self.kind, round(self.pos[0], 2), round(self.pos[1], 2),
                round(self.pos[2], 2), round(self.yaw, 2), self.item, self.owner,
                round(_num(self.spec.get("radius"), 0.0), 2),
                round(max(0.0, self.until - moment), 1)]


class _Ctx:
    """Whose hit this is, and with what (set while a weapon is being used)."""

    __slots__ = ("owner", "stats", "weapon", "item", "hits", "kills", "victims")

    def __init__(self, owner, stats: Dict[str, Any], weapon: str, item: str):
        self.owner = owner
        self.stats = stats
        self.weapon = weapon
        self.item = item
        self.hits = 0
        self.kills = 0
        self.victims: List[int] = []


# ================================================================= gear
class Gear:
    def __init__(self, inst):
        self.inst = inst
        self.status: Dict[int, Dict[str, Status]] = {}
        self.minions: Dict[int, Minion] = {}
        self.deployables: Dict[int, Deployable] = {}
        self.pending: List[Tuple[float, Callable[[], None]]] = []
        self.ctx: List[_Ctx] = []
        self.rng = random.Random()
        self._next_minion = MINION_BASE
        self._next_dep = 1
        self._dirty_players: set = set()
        self._sent: Dict[int, Any] = {}

    # ============================================================ context
    @contextmanager
    def using(self, owner, stats: Dict[str, Any], weapon: str = "", item: str = ""):
        ctx = _Ctx(owner, stats or {}, weapon, item)
        self.ctx.append(ctx)
        try:
            yield ctx
        finally:
            self.ctx.pop()

    def current(self) -> Optional[_Ctx]:
        return self.ctx[-1] if self.ctx else None

    # ============================================================ statuses
    def apply(self, ent, name: str, secs: float, value: float = 0.0, src=None,
              weapon: str = "", stacks: Optional[int] = None) -> None:
        """Put ``name`` on ``ent`` for ``secs`` (refreshing it; the stronger
        value wins, and stacking ones count up)."""
        if ent is None or not getattr(ent, "alive", False) or secs <= 0:
            return
        moment = _now()
        table = self.status.setdefault(ent.pid, {})
        src_pid = getattr(src, "pid", src) if src is not None else None
        held = table.get(name)
        if held is None or held.until < moment:
            held = Status(moment + secs, value, src_pid, weapon)
            held.tick_at = moment + DOT_STEP
            table[name] = held
        else:
            held.until = max(held.until, moment + secs)
            if name in ("bleed", "freeze", "dazzle"):
                held.stacks += 1
                if stacks is not None:
                    held.stacks = min(held.stacks, int(stacks))
            held.value = max(held.value, value)
            if src_pid is not None:
                held.src = src_pid
                held.weapon = weapon or held.weapon
        self._on_status(ent, name, table[name])
        self._touched(ent)

    def _on_status(self, ent, name: str, held: Status) -> None:
        """What a status does the moment it lands on something that is not
        a player (the infected have their own states)."""
        z = ent
        if not hasattr(z, "state_until") or not hasattr(z, "data"):
            return
        moment = _now()
        if name in ("root", "stun", "polymorph") or \
                (name == "freeze" and held.stacks >= 3):
            if getattr(z, "state", "") not in ("rise", "burrow", "pin"):
                z.state = "stun"
                z.state_until = max(getattr(z, "state_until", 0.0),
                                    min(held.until, moment + 4.0))
        elif name in ("slow", "freeze"):
            z.data["slow"] = 1.0 - _clamp(held.value * (held.stacks if name == "freeze" else 1),
                                          0.0, 0.85)
            z.data["slow_until"] = held.until

    def remove(self, ent, name: str) -> None:
        table = self.status.get(getattr(ent, "pid", ent))
        if table and table.pop(name, None) is not None:
            self._touched(ent)

    def has(self, ent, name: str) -> bool:
        table = self.status.get(getattr(ent, "pid", ent))
        if not table:
            return False
        held = table.get(name)
        return held is not None and held.until > _now()

    def value(self, ent, name: str) -> float:
        table = self.status.get(getattr(ent, "pid", ent))
        if not table:
            return 0.0
        held = table.get(name)
        if held is None or held.until <= _now():
            return 0.0
        return held.value * (held.stacks if name in ("bleed",) else 1)

    def stacks(self, ent, name: str) -> int:
        table = self.status.get(getattr(ent, "pid", ent))
        held = table.get(name) if table else None
        return held.stacks if held is not None and held.until > _now() else 0

    def clear(self, ent, harmful_only: bool = False) -> None:
        pid = getattr(ent, "pid", ent)
        table = self.status.get(pid)
        if not table:
            return
        if harmful_only:
            for name in list(table):
                if name in HARMFUL:
                    table.pop(name, None)
        else:
            self.status.pop(pid, None)
        self._touched(ent)

    def bits(self, ent) -> int:
        table = self.status.get(getattr(ent, "pid", ent))
        if not table:
            return 0
        moment = _now()
        out = 0
        for name, held in table.items():
            if held.until > moment:
                out |= STATUS_BITS.get(name, 0)
        return out

    def _touched(self, ent) -> None:
        pid = getattr(ent, "pid", None)
        if pid is not None and pid in self.inst.players:
            self._dirty_players.add(pid)

    # ------------------------------------------------- what a player may do
    def held_stats(self, player) -> Dict[str, Any]:
        if getattr(player, "stowed", True) or not hasattr(player, "weapon_stats"):
            return {}
        try:
            return player.weapon_stats()
        except Exception:
            return {}

    def move_scale(self, player) -> float:
        if self.has(player, "root") or self.has(player, "stun") or \
                (self.stacks(player, "freeze") >= 3):
            return 0.0
        scale = 1.0
        slow = max(self.value(player, "slow"),
                   min(0.85, self.value(player, "freeze") * self.stacks(player, "freeze")))
        if self.has(player, "polymorph"):
            slow = max(slow, 0.4)
        scale *= 1.0 - _clamp(slow, 0.0, 0.9)
        scale *= 1.0 + _clamp(self.value(player, "haste"), 0.0, 1.5)
        held = (self.held_stats(player).get("held") or {})
        scale *= 1.0 + _clamp(_num(held.get("speed")), -0.6, 0.6)
        return scale

    def speed_cap(self, player) -> float:
        """How much faster than walking the host lets this player move."""
        return max(1.0, self.move_scale(player) if not self.has(player, "root") else 1.0)

    def can_move(self, player) -> bool:
        return self.move_scale(player) > 0.0

    def can_jump(self, player) -> bool:
        return self.can_move(player) and not self.has(player, "jumpless") \
            and not self.has(player, "polymorph")

    def can_fire(self, player) -> bool:
        return not (self.has(player, "stun") or self.has(player, "polymorph")
                    or self.stacks(player, "freeze") >= 3)

    def launched(self, player) -> bool:
        return getattr(player, "extra", {}).get("launch_until", 0.0) > _now() or \
            self.has(player, "lowgrav")

    def grace(self, player) -> bool:
        return getattr(player, "extra", {}).get("tp_grace", 0.0) > _now()

    # ================================================================ state
    def _gs(self, player) -> Dict[str, Any]:
        return player.extra.setdefault("gear", {"cd": {}, "w": {}})

    def _wstate(self, player, item: str) -> Dict[str, Any]:
        return self._gs(player)["w"].setdefault(item, {})

    def cooldown_left(self, player, item: str) -> float:
        return max(0.0, self._gs(player)["cd"].get(item, 0.0) - _now())

    def start_cooldown(self, player, item: str, secs: float) -> None:
        if secs <= 0:
            return
        self._gs(player)["cd"][item] = _now() + secs
        player.send({"t": "cd", "w": item, "s": round(secs, 2)})

    def meter(self, player, item: str, value: float, label: str, on: bool = False) -> None:
        player.send({"t": "meter", "w": item, "v": round(_clamp(value, 0.0, 1.0), 3),
                     "l": label, "on": bool(on)})

    # ============================================================== firing
    def fire(self, player, slot: int, stats: Dict[str, Any], direction, origin) -> None:
        """A gear kind (``GEAR_KINDS``): beam, cone, strike, deploy, summon,
        ability, consume."""
        kind = stats.get("kind")
        item = (player.weapon() or {}).get("item_id", "")
        weapon = (player.weapon() or {}).get("name", "")
        if kind in CHARGED_KINDS:
            if self.has(player, "silence"):
                player.send({"t": "notice", "m": "Silenced!"})
                return
            if self.cooldown_left(player, item) > 0:
                return
        if kind == "beam":
            self._beam(player, slot, stats, direction, origin, weapon, item)
        elif kind == "cone":
            if player.ammo[slot] <= 0 and int(stats.get("mag", 0) or 0) > 0:
                self.inst.handle_reload(player)
                return
            if int(stats.get("mag", 0) or 0) > 0:
                player.ammo[slot] -= 1
                player.send({"t": "you", "ammo": player.ammo[slot],
                             "reserve": player.reserve[slot], "slot": slot})
            with self.using(player, stats, weapon, item) as ctx:
                self._cone(player, stats, direction, origin, weapon)
            self.after(player, stats, ctx)
        elif kind == "strike":
            self._strike(player, stats, direction, origin, weapon, item)
        elif kind == "deploy":
            self._deploy(player, stats.get("deploy") or {}, direction, origin, item)
        elif kind == "summon":
            self._summon(player, stats, item)
        elif kind == "ability":
            self._ability(player, stats.get("ability") or {}, direction, item)
        elif kind == "consume":
            self._consume(player, stats.get("consume") or {}, item)
        if kind in CHARGED_KINDS:
            self.start_cooldown(player, item, _num(stats.get("cooldown"), 10.0))
            self.inst.broadcast({"t": "gfx", "k": "use", "id": player.pid, "w": item,
                                 "s": str(stats.get("sound") or "")}, exclude=player.pid)
        player.spawn_protect_until = 0.0
        if self.has(player, "cloak") and kind not in ("consume",):
            self.remove(player, "cloak")

    def prepare(self, player, stats: Dict[str, Any]) -> Dict[str, Any]:
        """An ordinary weapon's stats for this shot or swing, with its
        signature traits worked in."""
        item = (player.weapon() or {}).get("item_id", "")
        st = self._wstate(player, item)
        moment = _now()
        out = stats
        # pressure: the longer since the last shot, the harder the next
        pressure = stats.get("pressure")
        if pressure:
            out = dict(out)
            since = moment - st.get("last_shot", moment - 99.0)
            charge = min(_num(pressure.get("max"), 5), since * _num(pressure.get("per_sec"), 1))
            out["damage"] = _num(stats.get("damage")) + charge * _num(pressure.get("damage"), 0)
            out["knockback"] = _num(stats.get("knockback")) + charge * _num(pressure.get("knock"), 0)
            st["last_shot"] = moment
            self.meter(player, item, 0.0, str(pressure.get("label") or "Pressure"))
        # streak: every hit in a row is worth a little more
        streak = stats.get("streak")
        if streak:
            out = dict(out)
            bonus = min(_num(streak.get("max"), 0.5), st.get("streak", 0) * _num(streak.get("per_hit"), 0.1))
            out["damage"] = _num(out.get("damage")) * (1.0 + bonus)
        # combo: hits close together build up
        combo = stats.get("combo")
        if combo:
            out = dict(out)
            if moment - st.get("combo_at", 0.0) > _num(combo.get("window"), 1.2):
                st["combo"] = 0
            bonus = min(_num(combo.get("max"), 0.6), st.get("combo", 0) * _num(combo.get("step"), 0.15))
            out["damage"] = _num(out.get("damage")) * (1.0 + bonus)
        # the sparkler's fuse: lit, it hits harder and sets light
        fuse = stats.get("fuse_meter")
        if fuse:
            lit_until = st.get("lit_until", 0.0)
            if lit_until <= moment and self._fuse_charge(st, fuse, moment) >= 1.0:
                lit_until = st["lit_until"] = moment + _num(fuse.get("secs"), 10)
                st["fuse_spent"] = moment
                self.meter(player, item, 1.0, str(fuse.get("label") or "Fuse"), True)
                self.inst.broadcast({"t": "gfx", "k": "lit", "id": player.pid, "w": item})
            if lit_until > moment:
                out = dict(out)
                out["damage"] = _num(out.get("damage")) * (1.0 + _num(fuse.get("bonus"), 0.5))
                hit = dict(out.get("on_hit") or {})
                if fuse.get("burn"):
                    hit["burn"] = fuse["burn"]
                out["on_hit"] = hit
        # a lunge forward with the swing
        lunge = stats.get("lunge")
        if lunge and player.brain is None:
            d = _look(player.yaw, 0.0)
            force = _num(lunge.get("speed") if isinstance(lunge, dict) else lunge, 30)
            self.push(player, [d[0] * force, 6.0, d[2] * force])
        # a parry window opens with every swing
        parry = stats.get("parry")
        if parry:
            secs, reduce = _pair(parry, 0.35, 0.75)
            self.apply(player, "block", secs, reduce, player)
        # a held buff that only works while this is out
        return out

    def _fuse_charge(self, st: Dict[str, Any], fuse: Dict[str, Any], moment: float) -> float:
        spent = st.get("fuse_spent")
        if spent is None:
            return 1.0
        lit_end = spent + _num(fuse.get("secs"), 10)
        if moment < lit_end:
            return 0.0
        return _clamp((moment - lit_end) / max(0.5, _num(fuse.get("recharge"), 9)), 0.0, 1.0)

    def aim(self, player, stats: Dict[str, Any], origin, direction) -> List[float]:
        """Aim assist: snap to the nearest target inside a narrow cone."""
        assist = stats.get("aim_assist")
        if not assist:
            return direction
        angle = math.radians(_num(assist, 6.0) if not isinstance(assist, dict)
                             else _num(assist.get("angle"), 6.0))
        best, best_dot = None, math.cos(angle)
        for ent in self.targets_for(player, _num(stats.get("range"), 200)):
            c = self._centre(ent)
            delta = [c[0] - origin[0], c[1] - origin[1], c[2] - origin[2]]
            unit = _norm(delta)
            dot = unit[0] * direction[0] + unit[1] * direction[1] + unit[2] * direction[2]
            if dot > best_dot and self.inst.line_of_sight(origin, c):
                best, best_dot = unit, dot
        return best or direction

    def after(self, player, stats: Dict[str, Any], ctx: Optional[_Ctx]) -> None:
        """Book-keeping once a shot or swing is done: streaks, combos,
        counters."""
        item = (ctx.item if ctx else "") or (player.weapon() or {}).get("item_id", "")
        st = self._wstate(player, item)
        hits = ctx.hits if ctx else 0
        moment = _now()
        streak = stats.get("streak")
        if streak:
            st["streak"] = st.get("streak", 0) + 1 if hits else 0
            cap = max(1, int(round(_num(streak.get("max"), 0.5) / max(0.01, _num(streak.get("per_hit"), 0.1)))))
            self.meter(player, item, min(st["streak"], cap) / cap, str(streak.get("label") or "Streak"))
        combo = stats.get("combo")
        if combo:
            if hits:
                st["combo"] = st.get("combo", 0) + 1
                st["combo_at"] = moment
            cap = max(1, int(round(_num(combo.get("max"), 0.6) / max(0.01, _num(combo.get("step"), 0.15)))))
            self.meter(player, item, min(st.get("combo", 0), cap) / cap, str(combo.get("label") or "Combo"))
        counter = stats.get("counter") or stats.get("aoe_every")
        if counter and hits:
            every = max(1, int(_num(counter.get("every"), 10)))
            st["count"] = st.get("count", 0) + hits
            if st["count"] >= every:
                st["count"] = 0
                self.blast(player, [player.pos[0], player.pos[1] + 2.4, player.pos[2]],
                           _num(counter.get("radius"), 10.0), _num(counter.get("damage"), 60),
                           _num(counter.get("knock"), 30), ctx.weapon if ctx else "",
                           kind=str(counter.get("fx") or "pulse"),
                           extra={"on_hit": counter.get("on_hit") or {}})
            self.meter(player, item, st.get("count", 0) / every, str(counter.get("label") or "Charge"))
        fuse = stats.get("fuse_meter")
        if fuse:
            lit = st.get("lit_until", 0.0) > moment
            value = (st["lit_until"] - moment) / max(0.5, _num(fuse.get("secs"), 10)) if lit \
                else self._fuse_charge(st, fuse, moment)
            self.meter(player, item, value, str(fuse.get("label") or "Fuse"), lit)

    # ---------------------------------------------------------- projectiles
    def launch(self, player, stats: Dict[str, Any], origin, direction, weapon: str,
               item: str) -> bool:
        """Fire a projectile weapon's shot; True when the gear took care of
        it (a volley: the first round now, the rest over the next moments)."""
        volley = stats.get("volley")
        if not volley:
            self.spawn_projectile(player, stats, origin, direction, weapon, item)
            return True
        count, gap = _pair(volley, 3, 0.12)
        spread = _num(stats.get("volley_spread"), 1.5)
        self.spawn_projectile(player, stats, origin, direction, weapon, item)
        for k in range(1, int(count)):
            def again(k=k):
                if not player.alive or player.pid not in self.inst.players:
                    return
                d = _look(player.yaw, player.pitch)
                d = self.inst._offset_direction(d, self.rng.gauss(0, math.radians(spread) * 0.5),
                                                self.rng.gauss(0, math.radians(spread) * 0.5))
                o = [player.pos[0], player.pos[1] + EYE, player.pos[2]]
                self.spawn_projectile(player, stats, o, d, weapon, item)
            self.pending.append((_now() + gap * k, again))
        return True

    def spawn_projectile(self, owner, stats: Dict[str, Any], origin, direction, weapon: str,
                         item: str, kind: Optional[str] = None, speed: Optional[float] = None,
                         start_ahead: float = 2.0):
        from .instance import Projectile
        speed = _num(stats.get("speed"), 70) if speed is None else speed
        proj = Projectile(owner, [origin[0] + direction[0] * start_ahead,
                                  origin[1] + direction[1] * start_ahead,
                                  origin[2] + direction[2] * start_ahead],
                          [direction[0] * speed, direction[1] * speed, direction[2] * speed],
                          stats, str(kind or stats.get("projectile", "rocket")), weapon)
        proj.data["item"] = item
        proj.data["start"] = list(proj.pos)
        if stats.get("boomerang"):
            proj.data["boom"] = {"back": False, "hit": set()}
        self.inst.projectiles.append(proj)
        self.inst.broadcast({"t": "proj", "id": proj.ident, "p": proj.pos, "v": proj.vel,
                             "o": owner.pid, "k": proj.kind, "w": item})
        return proj

    def steer(self, proj, dt: float) -> Optional[str]:
        """Before a projectile moves: None to fly as usual, "stuck" to stay
        where it is this tick, "boom" to go off now, "gone" to vanish."""
        stats = proj.stats
        data = proj.data
        moment = _now()
        owner = self.inst.players.get(proj.pid_owner)
        if "stuck" in data:
            target = data["stuck"]
            if target != "wall":
                ent = self.inst.entity(target) if hasattr(self.inst, "entity") else None
                if ent is None:
                    ent = self.minions.get(target)
                if ent is not None and getattr(ent, "alive", False):
                    off = data.get("off", [0.0, 2.4, 0.0])
                    proj.pos = [ent.pos[0] + off[0], ent.pos[1] + off[1], ent.pos[2] + off[2]]
            return "boom" if moment >= data.get("fuse_at", moment) else "stuck"
        boom = data.get("boom")
        if boom is not None:
            out = _num((stats.get("boomerang") or {}).get("out"), 40)
            travelled = math.dist(proj.pos, data.get("start", proj.pos))
            if not boom["back"] and travelled >= out:
                boom["back"] = True
                boom["hit"] = set()
            if boom["back"]:
                if owner is None or not owner.alive:
                    return "gone"
                goal = [owner.pos[0], owner.pos[1] + 3.0, owner.pos[2]]
                if math.dist(goal, proj.pos) < 3.2:
                    self._refund(owner, data.get("item", ""))
                    return "gone"
                speed = math.sqrt(sum(v * v for v in proj.vel)) or _num(stats.get("speed"), 60)
                d = _norm([goal[0] - proj.pos[0], goal[1] - proj.pos[1], goal[2] - proj.pos[2]])
                proj.vel = [d[0] * speed, d[1] * speed, d[2] * speed]
            if moment - proj.born > 7.0:
                return "gone"
            return None
        homing = stats.get("homing")
        if homing:
            turn = _num(homing.get("turn") if isinstance(homing, dict) else homing, 3.0)
            reach = _num(homing.get("range") if isinstance(homing, dict) else 60, 60)
            if owner is not None:
                best, best_d = None, reach
                for ent in self.targets_for(owner, reach, proj.pos):
                    c = self._centre(ent)
                    d = math.dist(c, proj.pos)
                    if d < best_d:
                        best, best_d = c, d
                if best is not None:
                    self._turn(proj, best, turn * dt)
        guided = stats.get("guided")
        if guided and owner is not None and owner.alive:
            aim = _look(owner.yaw, owner.pitch)
            eye = [owner.pos[0], owner.pos[1] + EYE, owner.pos[2]]
            reach = self.inst.ray_world(eye, aim, 240.0)
            goal = [eye[0] + aim[0] * reach, eye[1] + aim[1] * reach, eye[2] + aim[2] * reach]
            self._turn(proj, goal, _num(guided.get("turn") if isinstance(guided, dict) else guided, 4.0) * dt)
        split = stats.get("split")
        if split and moment - proj.born >= _num(split.get("after"), 0.35):
            count = int(_num(split.get("count"), 3))
            spread = math.radians(_num(split.get("spread"), 14))
            speed = math.sqrt(sum(v * v for v in proj.vel))
            base = _norm(proj.vel)
            sub = dict(stats)
            sub.pop("split", None)
            sub["damage"] = _num(split.get("damage"), _num(stats.get("damage")) * 0.6)
            sub["splash_damage"] = _num(split.get("splash_damage"), _num(stats.get("splash_damage")) * 0.6)
            if owner is not None:
                for k in range(count):
                    yaw_off = spread * (k - (count - 1) / 2.0)
                    d = self.inst._offset_direction(base, yaw_off, 0.0)
                    self.spawn_projectile(owner, sub, proj.pos, d, proj.weapon,
                                          data.get("item", ""), kind=proj.kind, speed=speed,
                                          start_ahead=0.2)
            self.inst.broadcast({"t": "gfx", "k": "pop", "p": [round(v, 2) for v in proj.pos],
                                 "w": data.get("item", "")})
            return "gone"
        return None

    def _turn(self, proj, goal, amount: float) -> None:
        speed = math.sqrt(sum(v * v for v in proj.vel)) or 1.0
        cur = _norm(proj.vel)
        want = _norm([goal[0] - proj.pos[0], goal[1] - proj.pos[1], goal[2] - proj.pos[2]])
        k = _clamp(amount, 0.0, 1.0)
        mixed = _norm([cur[0] + (want[0] - cur[0]) * k, cur[1] + (want[1] - cur[1]) * k,
                       cur[2] + (want[2] - cur[2]) * k])
        proj.vel = [mixed[0] * speed, mixed[1] * speed, mixed[2] * speed]

    def _refund(self, owner, item: str) -> None:
        for slot in range(len(owner.ammo)):
            entry = owner.weapon(slot)
            if entry and entry.get("item_id") == item:
                mag = int(_num(owner.weapon_stats(slot).get("mag"), 1))
                if owner.ammo[slot] < mag:
                    owner.ammo[slot] += 1
                    owner.send({"t": "you", "ammo": owner.ammo[slot],
                                "reserve": owner.reserve[slot], "slot": slot})
                return

    def impact(self, proj, victim, point, wall: bool) -> bool:
        """A projectile has hit ``victim`` (or a wall).  True keeps it flying
        (it stuck, bounced, or passed through); False lets it explode."""
        stats = proj.stats
        data = proj.data
        owner = self.inst.players.get(proj.pid_owner)
        if stats.get("sticky") and "stuck" not in data:
            proj.pos = list(point)
            proj.vel = [0.0, 0.0, 0.0]
            data["stuck"] = victim.pid if victim is not None else "wall"
            if victim is not None:
                data["off"] = [point[0] - victim.pos[0], point[1] - victim.pos[1],
                               point[2] - victim.pos[2]]
            data["fuse_at"] = _now() + _num(stats.get("fuse"), 2.5)
            self.inst.broadcast({"t": "gfx", "k": "stick", "id": proj.ident,
                                 "p": [round(v, 2) for v in point],
                                 "on": victim.pid if victim is not None else 0,
                                 "f": _num(stats.get("fuse"), 2.5)})
            return True
        boom = data.get("boom")
        if boom is not None:
            if victim is not None:
                key = victim.pid
                if key not in boom["hit"]:
                    boom["hit"].add(key)
                    if owner is not None:
                        with self.using(owner, stats, proj.weapon, data.get("item", "")):
                            self.inst.apply_damage(victim, owner, _num(stats.get("damage"), 30),
                                                   proj.weapon, False)
                        owner.send({"t": "hit", "n": 1})
                pierce = (stats.get("boomerang") or {}).get("pierce", True)
                if pierce:
                    self._past(proj, point)
                    return True
                boom["back"] = True
                return True
            if boom["back"]:
                # on its way home it is not stopped by anything: through the
                # wall and on to its thrower's hand
                speed = math.sqrt(sum(v * v for v in proj.vel)) or 1.0
                d = _norm(proj.vel)
                proj.pos = [point[0] + d[0] * speed * 0.05 + d[0] * 0.5,
                            point[1] + d[1] * speed * 0.05 + d[1] * 0.5,
                            point[2] + d[2] * speed * 0.05 + d[2] * 0.5]
                return True
            # a wall turns it round
            boom["back"] = True
            boom["hit"] = set()
            proj.pos = list(point)
            return True
        bounces = int(_num(stats.get("bounce"), 0))
        if wall and victim is None and data.get("bounced", 0) < bounces:
            data["bounced"] = data.get("bounced", 0) + 1
            self._reflect(proj, point)
            ramp = _num(stats.get("bounce_ramp"), 0.0)
            if ramp:
                data["ramp"] = data.get("ramp", 1.0) + ramp
            self.inst.broadcast({"t": "gfx", "k": "bounce", "p": [round(v, 2) for v in point]})
            return True
        if stats.get("pierce_players") and victim is not None:
            hit = data.setdefault("pierced", set())
            if victim.pid not in hit and owner is not None:
                hit.add(victim.pid)
                with self.using(owner, stats, proj.weapon, data.get("item", "")):
                    self.inst.apply_damage(victim, owner, _num(stats.get("damage"), 20),
                                           proj.weapon, False)
            if len(hit) <= int(_num(stats.get("pierce_players"), 2)):
                self._past(proj, point)
                return True
        return False

    @staticmethod
    def _past(proj, point) -> None:
        """On through whoever it just went through (a body is about three
        studs deep), so it does not meet them again next tick."""
        d = _norm(proj.vel)
        proj.pos = [point[0] + d[0] * 3.6, point[1] + d[1] * 3.6, point[2] + d[2] * 3.6]

    def _reflect(self, proj, point) -> None:
        speed = math.sqrt(sum(v * v for v in proj.vel)) or 1.0
        d = _norm(proj.vel)
        best_axis, best_free = 1, -1.0
        for axis in range(3):
            probe = list(d)
            probe[axis] = 0.0
            if abs(d[axis]) < 0.05:
                continue
            probe = _norm(probe)
            free = self.inst.ray_world([point[0] - d[0] * 0.3, point[1] - d[1] * 0.3,
                                        point[2] - d[2] * 0.3], probe, 2.0)
            if free > best_free:
                best_free, best_axis = free, axis
        d[best_axis] = -d[best_axis]
        damping = 0.85
        proj.vel = [d[0] * speed * damping, d[1] * speed * damping, d[2] * speed * damping]
        proj.pos = [point[0] + d[0] * 0.4, point[1] + d[1] * 0.4, point[2] + d[2] * 0.4]

    def exploded(self, proj) -> None:
        """After a projectile went off: bomblets, fire on the ground, coins,
        whatever its weapon leaves behind."""
        stats = proj.stats
        owner = self.inst.players.get(proj.pid_owner)
        item = proj.data.get("item", "")
        if owner is None:
            return
        cluster = stats.get("cluster")
        if cluster:
            sub = {"damage": _num(cluster.get("damage"), 20), "splash": _num(cluster.get("radius"), 5),
                   "splash_damage": _num(cluster.get("damage"), 20), "speed": _num(cluster.get("speed"), 18),
                   "gravity_scale": 1.4, "self_damage": 0.2, "knockback": 8,
                   "projectile": cluster.get("projectile", "bomblet"),
                   "on_hit": cluster.get("on_hit") or {}}
            for k in range(int(_num(cluster.get("count"), 5))):
                a = k * math.tau / max(1, int(_num(cluster.get("count"), 5))) + self.rng.uniform(-0.3, 0.3)
                d = _norm([math.sin(a), 1.1 + self.rng.uniform(0, 0.5), math.cos(a)])
                self.spawn_projectile(owner, sub, [proj.pos[0], proj.pos[1] + 0.8, proj.pos[2]], d,
                                      proj.weapon, item, kind=sub["projectile"],
                                      speed=sub["speed"] * self.rng.uniform(0.8, 1.2), start_ahead=0.2)
        zone = stats.get("ground_zone") or stats.get("ground_fire")
        if zone:
            spec = dict(zone)
            spec.setdefault("type", "zone")
            if "ground_fire" in stats and "enemy" not in spec:
                spec["enemy"] = {"burn": [_num(spec.get("dps"), 8), 1.2]}
            spec.setdefault("secs", 5.0)
            self.place(owner, spec, self._floor(proj.pos), item, 0.0)
        pickups = stats.get("pickups")
        if pickups:
            for k in range(int(_num(pickups.get("count"), 3))):
                a = self.rng.uniform(0, math.tau)
                r = self.rng.uniform(1.0, _num(pickups.get("spread"), 5.0))
                spot = self._floor([proj.pos[0] + math.sin(a) * r, proj.pos[1] + 2.0,
                                    proj.pos[2] + math.cos(a) * r])
                spec = dict(pickups)
                spec["type"] = "pickup"
                spec.setdefault("secs", 12.0)
                spec.setdefault("radius", 3.0)
                self.place(owner, spec, spot, item, 0.0, limit=False)

    # ------------------------------------------------------------- the kinds
    def _beam(self, player, slot, stats, direction, origin, weapon, item) -> None:
        st = self._wstate(player, item)
        moment = _now()
        heat = stats.get("heat") or {}
        level = st.get("heat", 0.0)
        if st.get("locked_until", 0.0) > moment:
            return
        # cool down for the time since the last shot
        level = max(0.0, level - (moment - st.get("heat_at", moment)) * _num(heat.get("cool"), 0.35))
        level += _num(heat.get("per_shot"), 0.0)
        st["heat"], st["heat_at"] = level, moment
        if heat and level >= 1.0:
            st["locked_until"] = moment + _num(heat.get("lock"), 2.0)
            st["heat"] = 1.0
            player.send({"t": "notice", "m": "Overheated!"})
        # ramp: holding the beam on the same target warms it up
        ramp = stats.get("ramp") or {}
        if moment - st.get("beam_at", 0.0) > 0.35:
            st["ramp_from"] = moment
        st["beam_at"] = moment
        mult = 1.0 + min(_num(ramp.get("max"), 2.0) - 1.0,
                         (moment - st.get("ramp_from", moment)) * _num(ramp.get("per_sec"), 0.0))
        shot = dict(stats)
        shot["damage"] = _num(stats.get("damage"), 5) * mult
        reach = _num(stats.get("range"), 80)
        with self.using(player, shot, weapon, item) as ctx:
            self.inst.do_hitscan(player, origin, direction, shot)
        end_d = self.inst.ray_world(origin, direction, reach)
        end = [origin[0] + direction[0] * end_d, origin[1] + direction[1] * end_d,
               origin[2] + direction[2] * end_d]
        if moment - st.get("beam_fx", 0.0) > 0.09:
            st["beam_fx"] = moment
            self.inst.broadcast({"t": "gfx", "k": "beam", "id": player.pid,
                                 "o": [round(v, 2) for v in origin],
                                 "e": [round(v, 2) for v in end],
                                 "c": str(stats.get("beam") or "#ff2bd6"), "m": round(mult, 2)},
                                exclude=player.pid)
        if heat:
            self.meter(player, item, st["heat"], str(heat.get("label") or "Heat"),
                       st.get("locked_until", 0.0) > moment)
        self.after(player, stats, ctx)

    def _cone(self, player, stats, direction, origin, weapon) -> None:
        cone = stats.get("cone") or {}
        reach = _num(stats.get("range"), 14)
        half = _num(cone.get("angle"), 0.5)
        hits = 0
        for ent in self.targets_for(player, reach + 3.0):
            c = self._centre(ent)
            delta = [c[0] - origin[0], c[1] - origin[1], c[2] - origin[2]]
            dist = math.sqrt(sum(v * v for v in delta))
            if dist > reach + 1.5:
                continue
            unit = _norm(delta)
            if unit[0] * direction[0] + unit[1] * direction[1] + unit[2] * direction[2] \
                    < math.cos(half):
                continue
            if not self.inst.line_of_sight(origin, c):
                continue
            hits += 1
            falloff = 1.0 - 0.4 * _clamp(dist / max(1.0, reach), 0, 1)
            self.inst.apply_damage(ent, player, _num(stats.get("damage"), 10) * falloff, weapon, False)
            push, lift = _num(cone.get("push"), 0), _num(cone.get("lift"), 0)
            if push or lift:
                self.push(ent, [unit[0] * push * falloff, lift, unit[2] * push * falloff])
            if cone.get("stun"):
                self.apply(ent, "stun", _num(cone.get("stun")), 0, player, weapon)
            if cone.get("pull"):
                p = _num(cone.get("pull"))
                self.push(ent, [-unit[0] * p, 8.0, -unit[2] * p])
        if hits:
            player.send({"t": "hit", "n": hits})
        self.inst.broadcast({"t": "gfx", "k": "cone", "id": player.pid,
                             "o": [round(v, 2) for v in origin], "d": [round(v, 3) for v in direction],
                             "a": round(half, 3), "r": reach, "c": str(cone.get("color") or "#ffffff")})

    def _strike(self, player, stats, direction, origin, weapon, item) -> None:
        strike = stats.get("strike") or {}
        reach = _num(stats.get("range"), 120)
        d = self.inst.ray_world(origin, direction, reach)
        # pointed at someone: it comes down on them, not on the ground behind
        victim, at, _head = self.inst.nearest_player_hit(player, origin, direction, d)
        if victim is not None:
            d = at
        point = [origin[0] + direction[0] * d, origin[1] + direction[1] * d,
                 origin[2] + direction[2] * d]
        point = self._floor(point)
        delay = _num(strike.get("delay"), 1.5)
        radius = _num(strike.get("radius"), 8)
        self.inst.broadcast({"t": "gfx", "k": "strike", "p": [round(v, 2) for v in point],
                             "r": radius, "d": delay, "w": item, "o": player.pid,
                             "m": str(strike.get("model") or "")})

        def land():
            owner = self.inst.players.get(player.pid)
            if owner is None:
                return
            self.blast(owner, [point[0], point[1] + 1.0, point[2]], radius,
                       _num(strike.get("damage"), 100), _num(strike.get("knock"), 30), weapon,
                       kind=str(strike.get("fx") or "strike"), item=item,
                       extra={"on_hit": strike.get("on_hit") or {}, "self_damage": 0.0})
        self.pending.append((_now() + delay, land))

    def _deploy(self, player, spec: Dict[str, Any], direction, origin, item) -> None:
        if not spec:
            return
        if spec.get("thrown"):
            reach = _num(spec.get("throw"), 16.0)
            d = self.inst.ray_world(origin, direction, reach)
            spot = [origin[0] + direction[0] * max(0.0, d - 1.0),
                    origin[1] + direction[1] * max(0.0, d - 1.0),
                    origin[2] + direction[2] * max(0.0, d - 1.0)]
        else:
            ahead = _look(player.yaw, 0.0)
            spot = [player.pos[0] + ahead[0] * 3.0, player.pos[1] + 2.0, player.pos[2] + ahead[2] * 3.0]
        spot = self._floor(spot)
        if spec.get("float"):
            spot[1] += _num(spec.get("float"))
        kind = str(spec.get("type") or "zone")
        if kind == "decoy":
            self._decoy(player, spec, spot, item)
            return
        self.place(player, spec, spot, item, player.yaw)

    def place(self, owner, spec: Dict[str, Any], spot, item: str, yaw: float,
              limit: bool = True) -> Optional[Deployable]:
        kind = str(spec.get("type") or "zone")
        moment = _now()
        if limit:
            cap = int(_num(spec.get("limit"), 1))
            mine = sorted((d for d in self.deployables.values()
                           if d.owner == owner.pid and d.item == item and d.kind == kind),
                          key=lambda d: d.born)
            while cap > 0 and len(mine) >= cap:
                self.unplace(mine.pop(0).ident)
        if len(self.deployables) >= MAX_DEPLOYABLES:
            oldest = min(self.deployables.values(), key=lambda d: d.born)
            self.unplace(oldest.ident)
        dep = Deployable(self._next_dep, owner.pid, owner.team, kind, item, spot, yaw,
                         moment + _num(spec.get("secs"), 8.0), spec)
        self._next_dep += 1
        self.deployables[dep.ident] = dep
        self.inst.broadcast({"t": "dep", "d": dep.row(moment)})
        return dep

    def unplace(self, ident: int, fx: bool = True) -> None:
        dep = self.deployables.pop(ident, None)
        if dep is not None:
            self.inst.broadcast({"t": "undep", "id": ident, "fx": 1 if fx else 0})

    def _summon(self, player, stats, item) -> None:
        spec = stats.get("minion") or (player.weapon() or {}).get("data", {}).get("minion") or {}
        if not spec:
            return
        cost = _num(stats.get("cost_hp"), 0)
        if cost > 0:
            player.health = max(1, int(player.health - cost))
            player.send({"t": "dmg", "hp": int(player.health), "a": cost, "from": player.pos,
                         "by": "", "hs": False, "self": 1})
        count = int(_num(spec.get("count"), 1))
        moment = _now()
        mine = [m for m in self.minions.values() if m.owner == player.pid and m.item == item]
        for old in mine:
            self.kill_minion(old, None, quiet=True)
        for k in range(count):
            if len(self.minions) >= MAX_MINIONS:
                break
            a = player.yaw + (k - (count - 1) / 2.0) * 0.9
            spot = self._floor([player.pos[0] + math.sin(a) * 4.0, player.pos[1] + 2.0,
                                player.pos[2] + math.cos(a) * 4.0])
            m = Minion(self._next_minion, player, spec, item, spot,
                       moment + _num(spec.get("secs"), 25.0))
            self._next_minion += 1
            m.yaw = a
            m.next_attack = moment + 0.6 + 0.15 * k
            self.minions[m.pid] = m
            self.inst.broadcast({"t": "gfx", "k": "rise", "p": [round(v, 2) for v in spot],
                                 "w": item, "m": m.kind})

    def _decoy(self, player, spec, spot, item) -> None:
        decoy = {"name": "Decoy", "model": "decoy", "hp": _num(spec.get("hp"), 60),
                 "speed": 0, "damage": 0, "secs": _num(spec.get("secs"), 8.0)}
        for old in [m for m in self.minions.values() if m.owner == player.pid and m.kind == "decoy"]:
            self.kill_minion(old, None, quiet=True)
        m = Minion(self._next_minion, player, decoy, item, spot, _now() + decoy["secs"])
        self._next_minion += 1
        self.minions[m.pid] = m
        if spec.get("cloak"):
            self.apply(player, "cloak", _num(spec.get("cloak")), 0.0, player)
        self.inst.broadcast({"t": "gfx", "k": "poof", "p": [round(v, 2) for v in spot], "w": item})

    def _ability(self, player, ability: Dict[str, Any], direction, item) -> None:
        moment = _now()
        pos = [player.pos[0], player.pos[1] + 2.6, player.pos[2]]
        if "rally" in ability:
            r = ability["rally"]
            radius = _num(r.get("radius"), 20)
            for ally in self._allies(player, radius):
                self.apply(ally, "haste", _num(r.get("secs"), 5), _num(r.get("speed"), 0.2), player)
                if r.get("might"):
                    self.apply(ally, "might", _num(r.get("secs"), 5), _num(r.get("might")), player)
            self._pulse(pos, radius, str(r.get("color") or "#ffd96b"))
        if "launch" in ability:
            l = ability["launch"]
            d = _look(player.yaw, 0.0)
            fwd = _num(l.get("forward"), 15)
            self.push(player, [d[0] * fwd, _num(l.get("up"), 60), d[2] * fwd])
            player.extra["launch_until"] = moment + 2.5
            if l.get("glide"):
                self.apply(player, "lowgrav", _num(l.get("glide")), 0.5, player)
            self.inst.broadcast({"t": "gfx", "k": "launch", "id": player.pid,
                                 "p": [round(v, 2) for v in player.pos]})
        if "blink" in ability:
            b = ability["blink"]
            d = _look(player.yaw, max(-0.3, min(0.3, player.pitch)))
            eye = [player.pos[0], player.pos[1] + 2.4, player.pos[2]]
            reach = self.inst.ray_world(eye, d, _num(b.get("dist"), 18))
            reach = max(0.0, reach - 2.0)
            goal = self._floor([player.pos[0] + d[0] * reach, player.pos[1] + 2.0 + d[1] * reach,
                                player.pos[2] + d[2] * reach])
            if self.inst.body_fits(*goal):
                start = list(player.pos)
                player.pos = goal
                player.extra["tp_grace"] = moment + 0.8
                player.send({"t": "tp", "p": [round(v, 2) for v in goal]})
                self.inst.broadcast({"t": "gfx", "k": "blink", "a": [round(v, 2) for v in start],
                                     "b": [round(v, 2) for v in goal], "w": item})
        if "dash" in ability:
            d = _look(player.yaw, 0.0)
            force = _num(ability["dash"].get("speed"), 55)
            self.push(player, [d[0] * force, 8.0, d[2] * force])
            player.extra["launch_until"] = moment + 1.2
        if "cloak" in ability:
            self.apply(player, "cloak", _num(ability["cloak"].get("secs"), 6), 0.0, player)
            self.inst.broadcast({"t": "gfx", "k": "poof", "p": [round(v, 2) for v in pos], "w": item})
        if "glide" in ability:
            g = ability["glide"]
            self.apply(player, "lowgrav", _num(g.get("secs"), 6), _num(g.get("gravity"), 0.35), player)
        if "radar" in ability:
            r = ability["radar"]
            radius = _num(r.get("radius"), 120)
            for ent in self.targets_for(player, radius):
                self.apply(ent, "reveal", _num(r.get("secs"), 6), 1.0, player)
            self._pulse(pos, radius, str(r.get("color") or "#9fd8ff"))
        if "shield" in ability:
            s = ability["shield"]
            for ally in [player] + (self._allies(player, _num(s.get("radius"), 0)) if s.get("radius") else []):
                self.apply(ally, "shield", _num(s.get("secs"), 6), _num(s.get("amount"), 40), player)
        if "cleanse" in ability:
            self.clear(player, harmful_only=True)
            self.inst.heal(player, _num(ability["cleanse"].get("heal"), 0), player)
        if "jump" in ability:
            j = ability["jump"]
            self.apply(player, "lowgrav", _num(j.get("secs"), 6), _num(j.get("gravity"), 0.6), player)
        if "might" in ability:
            m = ability["might"]
            self.apply(player, "might", _num(m.get("secs"), 6), _num(m.get("value"), 0.25), player)

    def _consume(self, player, eat: Dict[str, Any], item) -> None:
        if eat.get("random"):
            # a lucky dip: one of the treats, at random (each may carry a
            # "name" for the notice)
            pick = self.rng.choice(list(eat["random"]))
            if pick.get("name"):
                player.send({"t": "notice", "m": str(pick["name"])})
            rest = {k: v for k, v in eat.items() if k != "random"}
            rest.update({k: v for k, v in pick.items() if k != "name"})
            eat = rest
            if pick.get("trick"):
                # the trick: something that happens to you
                for name, spec in pick["trick"].items():
                    v, s = _pair(spec, 0.3, 2.0)
                    self.apply(player, name, s, v, None)
        if "heal" in eat and not eat.get("over"):
            self.inst.heal(player, _num(eat["heal"]), player)
        if eat.get("over"):
            secs = _num(eat.get("over"), 3)
            self.apply(player, "regen", secs, _num(eat.get("heal"), 20) / max(0.5, secs), player)
        if "speed" in eat:
            v, s = _pair(eat["speed"], 0.2, 5)
            self.apply(player, "haste", s, v, player)
        if "crit" in eat:
            v, s = _pair(eat["crit"], 0.25, 10)
            self.apply(player, "crit", s, v, player)
        if "might" in eat:
            v, s = _pair(eat["might"], 0.2, 8)
            self.apply(player, "might", s, v, player)
        if "shield" in eat:
            v, s = _pair(eat["shield"], 30, 10)
            self.apply(player, "shield", s, v, player)
        if "jump" in eat:
            v, s = _pair(eat["jump"], 0.6, 8)
            self.apply(player, "lowgrav", s, v, player)
        if eat.get("cleanse"):
            self.clear(player, harmful_only=True)
        if "regen" in eat:
            v, s = _pair(eat["regen"], 3, 10)
            self.apply(player, "regen", s, v, player)
        if eat.get("share"):
            # a dish passed round: the same, at half strength, to allies near
            radius = _num(eat.get("share"), 10)
            for ally in self._allies(player, radius):
                if "heal" in eat:
                    self.inst.heal(ally, _num(eat["heal"]) * 0.5, player)
                if "speed" in eat:
                    v, s = _pair(eat["speed"], 0.2, 5)
                    self.apply(ally, "haste", s, v * 0.5, player)
            self._pulse([player.pos[0], player.pos[1] + 2, player.pos[2]], radius, "#ffd96b")
        self.inst.broadcast({"t": "gfx", "k": "eat", "id": player.pid, "w": item})

    # ============================================================== damage
    def adjust(self, victim, attacker, amount: float, headshot: bool = False) -> float:
        """What a hit is really worth, once buffs, crits, marks, parries and
        shields are counted -- and whether a cheated death leaves 1 hp."""
        if amount <= 0:
            return amount
        ctx = self.current()
        if attacker is not None and getattr(attacker, "pid", None) is not None:
            mult = 1.0 + _clamp(self.value(attacker, "might"), 0.0, 2.0)
            stats = ctx.stats if ctx is not None and ctx.owner is attacker else {}
            chance = _num(stats.get("crit_chance"), 0.0) + self.value(attacker, "crit")
            if chance > 0 and self.rng.random() < chance:
                mult *= 2.0
                attacker.send({"t": "gfx", "k": "crit"})
            near = stats.get("near")
            if near and math.dist(attacker.pos, victim.pos) <= _num(near.get("dist"), 10):
                mult *= 1.0 + _num(near.get("bonus"), 0.3)
            far = stats.get("far")
            if far and math.dist(attacker.pos, victim.pos) >= _num(far.get("dist"), 40):
                mult *= 1.0 + _num(far.get("bonus"), 0.3)
            if stats.get("vs_airborne") and self._airborne(victim):
                mult *= _num(stats.get("vs_airborne"), 1.5)
            if stats.get("self_airborne") and self._airborne(attacker):
                mult *= _num(stats.get("self_airborne"), 1.3)
            for name, factor in (stats.get("vs_status") or {}).items():
                if self.has(victim, name):
                    mult *= _num(factor, 1.0)
            if stats.get("backstab") and self._behind(attacker, victim):
                mult *= _num(stats.get("backstab"), 2.0)
            amount *= mult
        # incoming
        amount *= 1.0 + _clamp(self.value(victim, "mark"), 0.0, 1.5)
        held = (self.held_stats(victim).get("held") or {}) if hasattr(victim, "weapon_stats") else {}
        if held.get("dmg_taken"):
            amount *= 1.0 + _num(held.get("dmg_taken"))
        block = self.value(victim, "block")
        if block > 0 and attacker is not None and attacker is not victim:
            amount *= 1.0 - _clamp(block, 0.0, 0.95)
            parry = self.held_stats(victim).get("parry") if hasattr(victim, "weapon_stats") else None
            if isinstance(parry, dict) and parry.get("reflect") and hasattr(attacker, "pos"):
                away = _norm([attacker.pos[0] - victim.pos[0], 0.0, attacker.pos[2] - victim.pos[2]])
                force = _num(parry.get("reflect"), 26)
                self.push(attacker, [away[0] * force, 10.0, away[2] * force])
            self.inst.broadcast({"t": "gfx", "k": "parry",
                                 "p": [round(victim.pos[0], 2), round(victim.pos[1] + 3, 2),
                                       round(victim.pos[2], 2)]})
        shield = self.status.get(getattr(victim, "pid", None), {}).get("shield")
        if shield is not None and shield.until > _now() and shield.value > 0:
            soak = min(shield.value, amount)
            shield.value -= soak
            amount -= soak
            if shield.value <= 0.5:
                self.remove(victim, "shield")
            self._touched(victim)
        if amount >= getattr(victim, "health", 1e9) and self.has(victim, "cheat"):
            amount = max(0.0, victim.health - 1.0)
            self.remove(victim, "cheat")
            self.apply(victim, "haste", 2.0, 0.4, victim)
            self.inst.broadcast({"t": "gfx", "k": "cheat", "id": victim.pid})
            victim.send({"t": "notice", "m": "Lucky! Death cheated."})
        return amount

    def _airborne(self, ent) -> bool:
        if hasattr(ent, "grounded") and not getattr(ent, "npc", False):
            return not ent.grounded
        return bool(getattr(ent, "airborne", False))

    @staticmethod
    def _behind(attacker, victim) -> bool:
        to = math.atan2(attacker.pos[0] - victim.pos[0], attacker.pos[2] - victim.pos[2])
        facing = abs((to - victim.yaw + math.pi) % math.tau - math.pi)
        return facing > 2.1

    def landed(self, victim, attacker, amount: float, headshot: bool = False) -> None:
        """What a hit leaves behind, if it came from a weapon in use."""
        ctx = self.current()
        if ctx is None or attacker is None or ctx.owner is not attacker or amount <= 0:
            return
        stats = ctx.stats
        ctx.hits += 1
        killed = not getattr(victim, "alive", True) or getattr(victim, "health", 1) <= 0
        if killed:
            ctx.kills += 1
            self._on_kill(attacker, victim, stats, ctx)
        else:
            self.inflict(victim, attacker, stats.get("on_hit") or {}, ctx.weapon)
            if headshot and stats.get("on_headshot"):
                self.inflict(victim, attacker, stats["on_headshot"], ctx.weapon)
        steal = _num(stats.get("lifesteal"), 0.0)
        if steal > 0 and hasattr(self.inst, "heal") and hasattr(attacker, "weapon_stats"):
            self.inst.heal(attacker, amount * steal, attacker)
        if stats.get("speed_on_hit") and hasattr(attacker, "weapon_stats"):
            v, s = _pair(stats["speed_on_hit"], 0.15, 2.5)
            self.apply(attacker, "haste", s, v, attacker)
        if stats.get("ally_buff") and hasattr(attacker, "weapon_stats"):
            buff = stats["ally_buff"]
            for ally in self._allies(attacker, _num(buff.get("radius"), 14)):
                for name in ("might", "haste", "regen", "shield"):
                    if name in buff:
                        v, s = _pair(buff[name], 0.15, 4)
                        self.apply(ally, name, s, v, attacker)
        ricochet = stats.get("ricochet")
        if ricochet and not killed and hasattr(attacker, "extra") and not ctx.stats.get("_bounced"):
            item = ctx.item
            st = self._wstate(attacker, item) if item else {}
            if ricochet.get("always") or st.get("ricochets", 0) > 0:
                if not ricochet.get("always"):
                    st["ricochets"] = st.get("ricochets", 0) - 1
                self._ricochet(attacker, victim, amount, ricochet, ctx)

    def inflict(self, victim, attacker, effects: Dict[str, Any], weapon: str) -> None:
        """Statuses from an ``on_hit`` table onto ``victim``."""
        if not effects or not getattr(victim, "alive", False):
            return
        chance = _num(effects.get("chance"), 1.0)
        if chance < 1.0 and self.rng.random() > chance:
            return
        for name, spec in effects.items():
            if name == "chance":
                continue
            if name in ("burn", "poison"):
                dps, secs = _pair(spec, 5, 3)
                self.apply(victim, name, secs, dps, attacker, weapon)
            elif name == "bleed":
                dps, secs = _pair(spec, 3, 4)
                cap = int(spec[2]) if isinstance(spec, (list, tuple)) and len(spec) > 2 else 5
                self.apply(victim, "bleed", secs, dps, attacker, weapon, stacks=cap)
            elif name in ("slow", "mark", "haste", "might"):
                value, secs = _pair(spec, 0.3, 2.5)
                self.apply(victim, name, secs, value, attacker, weapon)
            elif name in ("root", "stun", "jumpless", "silence", "reveal", "polymorph"):
                self.apply(victim, name, _pair(spec, 1.0)[0], 1.0, attacker, weapon)
            elif name == "blind":
                secs = _pair(spec, 1.5)[0]
                style = spec[1] if isinstance(spec, (list, tuple)) and len(spec) > 1 else "flash"
                self.apply(victim, "blind", secs, 1.0, attacker, weapon)
                victim.send({"t": "gfx", "k": "blind", "s": secs, "v": str(style)})
            elif name == "freeze":
                per, need = _pair(spec, 0.15, 3)
                secs = spec[2] if isinstance(spec, (list, tuple)) and len(spec) > 2 else 2.0
                self.apply(victim, "freeze", 3.0, per, attacker, weapon, stacks=int(need))
                if self.stacks(victim, "freeze") >= int(need):
                    self.apply(victim, "root", _num(secs, 2.0), 1.0, attacker, weapon)
                    self.remove(victim, "freeze")
                    self.inst.broadcast({"t": "gfx", "k": "freeze", "id": victim.pid})
            elif name == "dazzle":
                need, secs = _pair(spec, 3, 4)
                value = spec[2] if isinstance(spec, (list, tuple)) and len(spec) > 2 else 0.3
                mark_secs = spec[3] if isinstance(spec, (list, tuple)) and len(spec) > 3 else 5.0
                self.apply(victim, "dazzle", secs, 1.0, attacker, weapon, stacks=int(need))
                if self.stacks(victim, "dazzle") >= int(need):
                    self.remove(victim, "dazzle")
                    self.apply(victim, "mark", _num(mark_secs, 5.0), _num(value, 0.3), attacker, weapon)
            elif name == "knockup":
                self.push(victim, [0.0, _num(spec, 30), 0.0])
            elif name == "pull" and attacker is not None:
                p = _num(spec, 25)
                d = _norm([attacker.pos[0] - victim.pos[0], 0.0, attacker.pos[2] - victim.pos[2]])
                self.push(victim, [d[0] * p, 10.0, d[2] * p])
            elif name == "push" and attacker is not None:
                p = _num(spec, 25)
                d = _norm([victim.pos[0] - attacker.pos[0], 0.0, victim.pos[2] - attacker.pos[2]])
                self.push(victim, [d[0] * p, 8.0, d[2] * p])

    def _on_kill(self, killer, victim, stats: Dict[str, Any], ctx: _Ctx) -> None:
        effects = stats.get("on_kill") or {}
        if not effects or not hasattr(killer, "weapon_stats"):
            return
        pos = [victim.pos[0], victim.pos[1] + 2.6, victim.pos[2]]
        if effects.get("refill"):
            for slot in range(len(killer.ammo)):
                entry = killer.weapon(slot)
                if entry and entry.get("item_id") == ctx.item:
                    killer.ammo[slot] = int(_num(killer.weapon_stats(slot).get("mag"), 0))
                    killer.send({"t": "you", "ammo": killer.ammo[slot],
                                 "reserve": killer.reserve[slot], "slot": slot})
        if effects.get("ricochet_shots") and ctx.item:
            st = self._wstate(killer, ctx.item)
            st["ricochets"] = int(_num(effects["ricochet_shots"]))
            self.meter(killer, ctx.item, 1.0, "Ricochet")
        if effects.get("heal"):
            self.inst.heal(killer, _num(effects["heal"]), killer)
        if effects.get("speed"):
            v, s = _pair(effects["speed"], 0.25, 4)
            self.apply(killer, "haste", s, v, killer)
        if effects.get("cheat"):
            self.apply(killer, "cheat", _num(effects["cheat"], 30), 1.0, killer)
        if effects.get("gild"):
            self.inst.broadcast({"t": "gfx", "k": "gild", "p": [round(v, 2) for v in pos]})
        summon = effects.get("summon")
        if summon:
            moment = _now()
            mine = [m for m in self.minions.values() if m.owner == killer.pid
                    and m.item == ctx.item]
            if len(mine) < int(_num(summon.get("max"), 3)) and len(self.minions) < MAX_MINIONS:
                m = Minion(self._next_minion, killer, summon, ctx.item, self._floor(pos),
                           moment + _num(summon.get("secs"), 20))
                self._next_minion += 1
                self.minions[m.pid] = m
                self.inst.broadcast({"t": "gfx", "k": "rise", "p": [round(v, 2) for v in m.pos],
                                     "w": ctx.item, "m": m.kind})

    def _ricochet(self, attacker, victim, amount: float, spec: Dict[str, Any], ctx: _Ctx) -> None:
        reach = _num(spec.get("range"), 20)
        start = self._centre(victim)
        best, best_d = None, reach
        for ent in self.targets_for(attacker, reach + 10, start):
            if ent is victim:
                continue
            c = self._centre(ent)
            d = math.dist(c, start)
            if d < best_d and self.inst.line_of_sight(start, c):
                best, best_d = ent, d
        if best is None:
            return
        bounced = dict(ctx.stats)
        bounced["_bounced"] = True
        bounced.pop("on_kill", None)
        with self.using(attacker, bounced, ctx.weapon, ctx.item):
            self.inst.apply_damage(best, attacker, amount * _num(spec.get("falloff"), 0.6),
                                   ctx.weapon, False)
        end = self._centre(best)
        self.inst.broadcast({"t": "gfx", "k": "ricochet", "a": [round(v, 2) for v in start],
                             "b": [round(v, 2) for v in end],
                             "c": str(ctx.stats.get("tracer") or "#ffd96b")})

    def blast(self, owner, centre, radius: float, damage: float, knock: float, weapon: str,
              kind: str = "pulse", item: str = "", extra: Optional[Dict[str, Any]] = None) -> None:
        """An explosion that is not a projectile's: a strike landing, a
        counter going off, a mine, a balloon dog popping.  Runs through the
        world's own ``explode`` (so Last Light's infected and barrels get it
        too)."""
        from .instance import Projectile
        stats = {"splash": radius, "splash_damage": damage, "damage": damage,
                 "knockback": knock, "self_damage": 0.0}
        stats.update(extra or {})
        proj = Projectile.__new__(Projectile)
        proj.pid_owner = owner.pid if owner is not None else -1
        proj.team = owner.team if owner is not None else ""
        proj.pos = [float(centre[0]), float(centre[1]), float(centre[2])]
        proj.vel = [0.0, 0.0, 0.0]
        proj.stats = stats
        proj.born = _now()
        proj.kind = kind
        proj.weapon = weapon
        proj.ident = 0
        proj.data = {"item": item, "fake": True}
        if owner is not None:
            with self.using(owner, stats, weapon, item):
                self.inst.explode(proj)
        else:
            self.inst.explode(proj)

    def push(self, ent, velocity) -> None:
        """Shove something: a player's client does it, a bot or a minion is
        moved here."""
        if ent is None:
            return
        if isinstance(ent, Minion):
            ent.vel = [ent.vel[0] + velocity[0], ent.vel[1] + velocity[1], ent.vel[2] + velocity[2]]
            ent.grounded = False
            return
        knock = getattr(self.inst, "knock", None)
        if knock is not None and hasattr(ent, "weapon_stats"):
            knock(ent, velocity)
            return
        if getattr(ent, "brain", None) is not None:
            brain = ent.brain
            brain.airborne = True
            brain.vy = max(getattr(brain, "vy", 0.0), float(velocity[1]))
            return
        if hasattr(ent, "weapon_stats"):
            ent.send({"t": "knock", "v": [round(v, 2) for v in velocity]})
            if velocity[1] > 20:
                ent.extra["launch_until"] = _now() + 2.0

    # ============================================================ targets
    def _centre(self, ent) -> List[float]:
        if hasattr(ent, "centre"):
            return list(ent.centre())
        return [ent.pos[0], ent.pos[1] + 2.6, ent.pos[2]]

    def hostile(self, a_team: str, b) -> bool:
        if getattr(b, "team", "") in ("world",):
            return False
        team = getattr(b, "team", "")
        if not a_team or not team:
            return True
        return a_team != team or bool(getattr(self.inst, "friendly_fire", False))

    def targets_for(self, owner, reach: float, origin=None) -> Iterable[Any]:
        """Everything ``owner`` may hurt within ``reach``: the other side's
        players and minions, and whatever the world adds (the infected)."""
        if owner is None:
            return []
        origin = origin or owner.pos
        team = getattr(owner, "team", "")
        owner_pid = getattr(owner, "owner", None) if isinstance(owner, Minion) else owner.pid
        out = []
        moment = _now()
        for p in self.inst.players.values():
            if not p.alive or p.pid == owner_pid or not self.hostile(team, p):
                continue
            if moment < p.spawn_protect_until:
                continue
            if self.has(p, "cloak") and math.dist(p.pos, origin) > 12.0:
                continue
            if math.dist(p.pos, origin) <= reach:
                out.append(p)
        for m in self.minions.values():
            if not m.alive or m.owner == owner_pid or not self.hostile(team, m):
                continue
            if math.dist(m.pos, origin) <= reach:
                out.append(m)
        extra = getattr(self.inst, "gear_hostiles", None)
        if extra is not None:
            for ent in extra(owner, origin, reach):
                out.append(ent)
        return out

    def _allies(self, player, radius: float) -> List[Any]:
        out = []
        for p in self.inst.players.values():
            if not p.alive:
                continue
            if p is player or (p.team and p.team == player.team):
                if radius <= 0 or math.dist(p.pos, player.pos) <= radius:
                    out.append(p)
        return out

    def _floor(self, spot) -> List[float]:
        """The ground under a point (or the point, if there is none near)."""
        drop = self.inst.ray_world([spot[0], spot[1] + 1.0, spot[2]], [0.0, -1.0, 0.0], 60.0)
        if drop >= 60.0:
            return [spot[0], spot[1], spot[2]]
        return [spot[0], spot[1] + 1.0 - drop, spot[2]]

    def _pulse(self, centre, radius: float, colour: str) -> None:
        self.inst.broadcast({"t": "gfx", "k": "pulse", "p": [round(v, 2) for v in centre],
                             "r": round(radius, 2), "c": colour})

    # ============================================================ minions
    def ray_minions(self, shooter, origin, direction, best: float):
        from .instance import ray_aabb
        hit, hit_d = None, best
        for m in self.minions.values():
            if not m.alive or m.owner == getattr(shooter, "pid", None):
                continue
            if not self.hostile(getattr(shooter, "team", ""), m):
                continue
            lo, hi = m.hitbox()
            d = ray_aabb(origin, direction, lo, hi)
            if d is not None and d < hit_d:
                hit, hit_d = m, d
        return hit, hit_d

    def melee_minions(self, player, origin, direction, reach: float, arc: float,
                      damage: float, weapon: str) -> int:
        hits = 0
        for m in list(self.minions.values()):
            if not m.alive or m.owner == player.pid or not self.hostile(player.team, m):
                continue
            c = m.centre()
            delta = [c[0] - origin[0], c[1] - origin[1], c[2] - origin[2]]
            if math.sqrt(sum(v * v for v in delta)) > reach:
                continue
            unit = _norm(delta)
            if unit[0] * direction[0] + unit[1] * direction[1] + unit[2] * direction[2] < 1.0 - arc:
                continue
            hits += 1
            self.hurt_minion(m, player, damage, weapon)
        return hits

    def blast_minions(self, centre, radius: float, damage: float, owner, weapon: str) -> None:
        team = owner.team if owner is not None else ""
        for m in list(self.minions.values()):
            if not m.alive or (owner is not None and m.owner == owner.pid):
                continue
            if owner is not None and not self.hostile(team, m):
                continue
            d = math.dist(m.centre(), centre)
            if d > radius:
                continue
            self.hurt_minion(m, owner, damage * (1.0 - (d / radius) ** 1.4), weapon)

    def hurt_minion(self, m: Minion, attacker, amount: float, weapon: str) -> None:
        if not m.alive or amount <= 0:
            return
        amount = self.adjust(m, attacker, amount)
        m.health -= amount
        if attacker is not None and hasattr(attacker, "send"):
            attacker.send({"t": "dealt", "a": round(amount, 1), "hs": False, "target": m.pid,
                           "hp": max(0, int(m.health))})
        if m.health <= 0:
            self.kill_minion(m, attacker)
        else:
            self.landed(m, attacker, amount)

    def kill_minion(self, m: Minion, by=None, quiet: bool = False) -> None:
        if m.pid not in self.minions:
            return
        m.alive = False
        self.minions.pop(m.pid, None)
        self.status.pop(m.pid, None)
        self.inst.broadcast({"t": "gfx", "k": "unrise" if not quiet else "poof",
                             "p": [round(v, 2) for v in m.pos], "w": m.item, "m": m.kind,
                             "id": m.pid})
        boom = m.spec.get("explode")
        if boom and not quiet:
            owner = self.inst.players.get(m.owner)
            if owner is not None:
                self.blast(owner, m.centre(), _num(boom.get("radius"), 7),
                           _num(boom.get("damage"), 40), _num(boom.get("knock"), 20), m.name,
                           kind=str(boom.get("fx") or "explode"), item=m.item)

    def _step_minion(self, m: Minion, dt: float, moment: float) -> None:
        spec = m.spec
        owner = self.inst.players.get(m.owner)
        if owner is None or moment >= m.until:
            self.kill_minion(m, None, quiet=owner is None)
            return
        # falling
        if not m.grounded or m.vel[1] != 0.0:
            m.vel[1] -= 62.0 * dt
            nxt = [m.pos[0] + m.vel[0] * dt, m.pos[1] + m.vel[1] * dt, m.pos[2] + m.vel[2] * dt]
            floor = self._floor([nxt[0], max(nxt[1], m.pos[1]) + 0.5, nxt[2]])
            if nxt[1] <= floor[1] and m.vel[1] <= 0:
                nxt[1] = floor[1]
                m.vel = [0.0, 0.0, 0.0]
                m.grounded = True
            m.pos = nxt
            if m.pos[1] < self.inst.map.get("kill_y", -60):
                self.kill_minion(m, None)
            return
        speed = _num(spec.get("speed"), 14) * self._minion_scale(m)
        if speed <= 0:
            m.anim = "idle"
            return
        reach = _num(spec.get("reach"), 4.5)
        ranged = spec.get("ranged") or {}
        sight = _num(spec.get("sight"), 70)
        # pick a target now and then
        if moment >= m.extra.get("look_at", 0.0) or m.target is None:
            m.extra["look_at"] = moment + 0.5
            best, best_d = None, sight
            for ent in self.targets_for(m, sight):
                d = math.dist(ent.pos, m.pos)
                if d < best_d:
                    best, best_d = ent, d
            m.target = best.pid if best is not None else None
        target = None
        if m.target is not None:
            target = self.inst.players.get(m.target) or self.minions.get(m.target)
            if target is None and hasattr(self.inst, "entity"):
                target = self.inst.entity(m.target)
            if target is None or not getattr(target, "alive", False):
                m.target = None
                target = None
        goal = target.pos if target is not None else owner.pos
        dist = math.dist(goal, m.pos)
        keep = reach * 0.8 if target is not None else 6.0
        if ranged and target is not None:
            keep = max(keep, _num(ranged.get("range"), 30) * 0.6)
        # attack
        if target is not None and moment >= m.next_attack:
            if ranged and dist <= _num(ranged.get("range"), 30):
                eye = m.centre()
                aim = self._centre(target)
                if self.inst.line_of_sight(eye, aim):
                    m.next_attack = moment + 60.0 / max(1.0, _num(ranged.get("rpm"), 60))
                    with self.using(owner, spec, m.name, m.item):
                        self.inst.apply_damage(target, owner, _num(ranged.get("damage"), 6),
                                               m.name, False)
                    self.inst.broadcast({"t": "gfx", "k": "mshot", "a": [round(v, 2) for v in eye],
                                         "b": [round(v, 2) for v in aim], "id": m.pid,
                                         "c": str(ranged.get("color") or "#ffd96b")})
            elif dist <= reach + 1.0:
                m.next_attack = moment + _num(spec.get("rate"), 1.0)
                m.anim = "attack"
                if spec.get("explode"):
                    self.kill_minion(m, None)
                    return
                with self.using(owner, spec, m.name, m.item):
                    self.inst.apply_damage(target, owner, _num(spec.get("damage"), 8), m.name, False)
                self.inst.broadcast({"t": "gfx", "k": "bite", "id": m.pid})
        # move
        if dist > keep:
            d = _norm([goal[0] - m.pos[0], 0.0, goal[2] - m.pos[2]])
            step = speed * dt
            moved = False
            for turn in (0.0, 0.7, -0.7, 1.4, -1.4):
                dd = d if turn == 0.0 else [d[0] * math.cos(turn) - d[2] * math.sin(turn), 0.0,
                                            d[0] * math.sin(turn) + d[2] * math.cos(turn)]
                eye = [m.pos[0], m.pos[1] + 1.4, m.pos[2]]
                if self.inst.ray_world(eye, dd, step + 1.5) >= step + 1.5:
                    m.pos = [m.pos[0] + dd[0] * step, m.pos[1], m.pos[2] + dd[2] * step]
                    m.yaw = math.atan2(dd[0], dd[2])
                    moved = True
                    break
            if moved:
                floor = self._floor([m.pos[0], m.pos[1] + 2.0, m.pos[2]])
                if floor[1] < m.pos[1] - 0.6:
                    m.grounded = False
                else:
                    m.pos[1] = floor[1]
                m.anim = "run" if speed > 18 else "walk"
            else:
                # stuck: hop
                m.vel = [d[0] * speed, 26.0, d[2] * speed]
                m.grounded = False
        else:
            if target is not None:
                m.yaw = math.atan2(goal[0] - m.pos[0], goal[2] - m.pos[2])
            if m.anim != "attack" or moment >= m.next_attack - 0.5:
                m.anim = "idle"

    def _minion_scale(self, m: Minion) -> float:
        if self.has(m, "root") or self.has(m, "stun"):
            return 0.0
        return 1.0 - _clamp(self.value(m, "slow"), 0.0, 0.9)

    # ============================================================ deployables
    def _step_deployable(self, dep: Deployable, dt: float, moment: float) -> None:
        if moment >= dep.until:
            self.unplace(dep.ident)
            return
        owner = self.inst.players.get(dep.owner)
        if owner is None:
            self.unplace(dep.ident, fx=False)
            return
        spec = dep.spec
        radius = _num(spec.get("radius"), 6.0)
        kind = dep.kind
        if kind == "orbit":
            a = (moment - dep.born) * _num(spec.get("speed"), 2.0)
            r = _num(spec.get("orbit"), 7.0)
            dep.pos = [owner.pos[0] + math.sin(a) * r, owner.pos[1] + 0.2, owner.pos[2] + math.cos(a) * r]
            dep.yaw = a + math.pi / 2
            if not owner.alive:
                self.unplace(dep.ident)
                return
            for ent in self.targets_for(owner, r + radius + 2.0):
                if math.dist(self._centre(ent), [dep.pos[0], dep.pos[1] + 1.5, dep.pos[2]]) > radius + 1.5:
                    continue
                if moment - dep.hit_at.get(ent.pid, 0.0) < _num(spec.get("rehit"), 0.8):
                    continue
                dep.hit_at[ent.pid] = moment
                with self.using(owner, spec, spec.get("name", "Hazard"), dep.item):
                    self.inst.apply_damage(ent, owner, _num(spec.get("damage"), 15),
                                           str(spec.get("name") or "Hazard"), False)
                d = _norm([ent.pos[0] - dep.pos[0], 0.0, ent.pos[2] - dep.pos[2]])
                k = _num(spec.get("knock"), 16)
                if k:
                    self.push(ent, [d[0] * k, k * 0.5, d[2] * k])
            return
        if moment < dep.armed_at or moment < dep.next_act:
            return
        if kind == "turret":
            rate = 60.0 / max(1.0, _num(spec.get("rpm"), 120))
            reach = _num(spec.get("range"), 22)
            eye = [dep.pos[0], dep.pos[1] + _num(spec.get("muzzle"), 2.0), dep.pos[2]]
            best, best_d = None, reach
            for ent in self.targets_for(owner, reach, eye):
                c = self._centre(ent)
                d = math.dist(c, eye)
                if d < best_d and self.inst.line_of_sight(eye, c):
                    best, best_d = ent, d
            if best is None:
                dep.next_act = moment + 0.25
                return
            dep.next_act = moment + rate
            aim = self._centre(best)
            dep.yaw = math.atan2(aim[0] - eye[0], aim[2] - eye[2])
            with self.using(owner, spec, str(spec.get("name") or "Turret"), dep.item):
                self.inst.apply_damage(best, owner, _num(spec.get("damage"), 6),
                                       str(spec.get("name") or "Turret"), False)
            self.inst.broadcast({"t": "gfx", "k": "tshot", "id": dep.ident,
                                 "a": [round(v, 2) for v in eye], "b": [round(v, 2) for v in aim],
                                 "c": str(spec.get("tracer") or "#ffffff")})
            return
        if kind in ("trap", "mine"):
            dep.next_act = moment + 0.1
            for ent in self.targets_for(owner, radius + 1.0, dep.pos):
                if math.dist(ent.pos, dep.pos) > radius:
                    continue
                if kind == "mine":
                    self.unplace(dep.ident, fx=False)
                    self.blast(owner, [dep.pos[0], dep.pos[1] + 1.0, dep.pos[2]],
                               _num(spec.get("splash"), 7), _num(spec.get("splash_damage"), 60),
                               _num(spec.get("knockback"), 24), str(spec.get("name") or "Mine"),
                               kind=str(spec.get("fx") or "explode"), item=dep.item,
                               extra={"on_hit": spec.get("on_hit") or {}})
                    return
                with self.using(owner, spec, str(spec.get("name") or "Trap"), dep.item):
                    if _num(spec.get("damage"), 0) > 0:
                        self.inst.apply_damage(ent, owner, _num(spec.get("damage")),
                                               str(spec.get("name") or "Trap"), False)
                self.inflict(ent, owner, spec.get("enemy") or {"root": 2.0},
                             str(spec.get("name") or "Trap"))
                self.inst.broadcast({"t": "gfx", "k": "snap", "id": dep.ident,
                                     "p": [round(v, 2) for v in dep.pos]})
                if spec.get("once", True):
                    self.unplace(dep.ident, fx=False)
                    return
                dep.next_act = moment + _num(spec.get("rearm"), 2.0)
                return
            return
        if kind == "pickup":
            dep.next_act = moment + 0.1
            for p in self.inst.players.values():
                if not p.alive or math.dist(p.pos, dep.pos) > radius:
                    continue
                if spec.get("ally_only", True) and p.team != dep.team and p.pid != dep.owner:
                    continue
                if _num(spec.get("heal"), 0) > 0:
                    self.inst.heal(p, _num(spec.get("heal")), owner)
                for name in ("haste", "might", "shield", "regen"):
                    if name in spec:
                        v, s = _pair(spec[name], 0.2, 4)
                        self.apply(p, name, s, v, owner)
                if spec.get("ammo"):
                    slot = p.slot
                    p.reserve[slot] += int(_num(spec.get("ammo")))
                    p.send({"t": "you", "ammo": p.ammo[slot], "reserve": p.reserve[slot],
                            "slot": slot})
                self.inst.broadcast({"t": "gfx", "k": "pickup", "id": dep.ident,
                                     "p": [round(v, 2) for v in dep.pos]})
                self.unplace(dep.ident, fx=False)
                return
            return
        # zones, banners, grills, domes: a pulse every half second
        dep.next_act = moment + 0.5
        centre = [dep.pos[0], dep.pos[1] + 1.0, dep.pos[2]]
        ally = spec.get("ally") or {}
        enemy = spec.get("enemy") or {}
        heal = _num(spec.get("heal"), 0.0)
        if heal or ally:
            for p in self.inst.players.values():
                if not p.alive or math.dist(p.pos, dep.pos) > radius:
                    continue
                if p.pid != dep.owner and (not p.team or p.team != dep.team):
                    continue
                if heal:
                    self.inst.heal(p, heal * 0.5, owner)
                for name, spec_v in ally.items():
                    if name == "cleanse":
                        self.clear(p, harmful_only=True)
                        continue
                    v, s = _pair(spec_v, 0.2, 1.0)
                    self.apply(p, name, max(s, 0.8), v, owner)
        if enemy:
            for ent in self.targets_for(owner, radius + 2.0, centre):
                if math.dist(ent.pos, dep.pos) > radius:
                    continue
                effects = dict(enemy)
                dps = effects.pop("damage", None)
                if dps:
                    with self.using(owner, {}, str(spec.get("name") or "Zone"), dep.item):
                        self.inst.apply_damage(ent, owner, _num(dps) * 0.5,
                                               str(spec.get("name") or "Zone"), False)
                self.inflict(ent, owner, effects, str(spec.get("name") or "Zone"))

    # ================================================================ tick
    def tick(self, dt: float) -> None:
        moment = _now()
        # scheduled things: volleys, strikes
        if self.pending:
            due = [p for p in self.pending if p[0] <= moment]
            if due:
                self.pending = [p for p in self.pending if p[0] > moment]
                for _when, fn in due:
                    try:
                        fn()
                    except Exception:
                        import traceback
                        traceback.print_exc()
        # statuses: damage over time, regeneration, running out
        for pid in list(self.status):
            table = self.status.get(pid)
            ent = self._entity(pid)
            if ent is None or not getattr(ent, "alive", False):
                self.status.pop(pid, None)
                if pid in self.inst.players:
                    self._dirty_players.add(pid)
                continue
            for name in list(table):
                held = table[name]
                if held.until <= moment:
                    table.pop(name, None)
                    self._touched(ent)
                    continue
                if (name in DOTS or name == "regen") and moment >= held.tick_at:
                    held.tick_at = moment + DOT_STEP
                    per = held.value * DOT_STEP * (held.stacks if name == "bleed" else 1)
                    if name == "regen":
                        if hasattr(ent, "weapon_stats"):
                            self.inst.heal(ent, per, None)
                        continue
                    src = self.inst.players.get(held.src) if held.src is not None else None
                    if isinstance(ent, Minion):
                        self.hurt_minion(ent, src, per, held.weapon or name)
                    else:
                        self.inst.apply_damage(ent, src, per, held.weapon or name.title(), False)
                    if not getattr(ent, "alive", False):
                        break
            if not table:
                self.status.pop(pid, None)
        for m in list(self.minions.values()):
            self._step_minion(m, dt, moment)
        for dep in list(self.deployables.values()):
            self._step_deployable(dep, dt, moment)
        # the owners' own status lists
        for pid in list(self._dirty_players):
            p = self.inst.players.get(pid)
            if p is None:
                continue
            table = self.status.get(pid) or {}
            out = {name: [round(h.until - moment, 1), round(h.value, 2), h.stacks]
                   for name, h in table.items() if h.until > moment}
            if out != self._sent.get(pid):
                self._sent[pid] = out
                p.send({"t": "st", "s": out})
        self._dirty_players.clear()

    def _entity(self, pid: int):
        found = self.inst.players.get(pid)
        if found is not None:
            return found
        found = self.minions.get(pid)
        if found is not None:
            return found
        entity = getattr(self.inst, "entity", None)
        return entity(pid) if entity is not None else None

    # ================================================================ wire
    def snapshot(self, payload: Dict[str, Any]) -> None:
        if self.minions:
            payload["mn"] = [[m.pid, round(m.pos[0], 2), round(m.pos[1], 2), round(m.pos[2], 2),
                              round(m.yaw, 2), m.anim, int(100 * m.health / m.max_health),
                              m.owner, m.item, self.bits(m)] for m in self.minions.values()]
        moved = [d for d in self.deployables.values() if d.kind == "orbit"]
        if moved:
            payload["dm"] = [[d.ident, round(d.pos[0], 2), round(d.pos[1], 2), round(d.pos[2], 2),
                              round(d.yaw, 2)] for d in moved]
        others = []
        for pid, table in self.status.items():
            if pid in self.inst.players or pid in self.minions or not table:
                continue
            bits = self.bits(pid)
            if bits:
                others.append([pid, bits])
        if others:
            payload["es"] = others

    def state(self) -> List[List[Any]]:
        moment = _now()
        return [d.row(moment) for d in self.deployables.values()]

    # ============================================================ upkeep
    def forget(self, pid: int) -> None:
        """A player left: their minions, things and statuses go with them."""
        for m in [m for m in self.minions.values() if m.owner == pid]:
            self.kill_minion(m, None, quiet=True)
        for d in [d for d in self.deployables.values() if d.owner == pid]:
            self.unplace(d.ident, fx=False)
        self.status.pop(pid, None)
        self._sent.pop(pid, None)

    def respawned(self, player) -> None:
        self.status.pop(player.pid, None)
        self._dirty_players.add(player.pid)
        gs = player.extra.get("gear")
        if gs:
            for st in gs.get("w", {}).values():
                for key in ("streak", "combo", "ricochets", "count", "lit_until", "fuse_spent"):
                    st.pop(key, None)

    def reset(self) -> None:
        for m in list(self.minions.values()):
            self.kill_minion(m, None, quiet=True)
        for d in list(self.deployables):
            self.unplace(d, fx=False)
        self.status.clear()
        self.pending.clear()
        for pid in list(self.inst.players):
            self._dirty_players.add(pid)
