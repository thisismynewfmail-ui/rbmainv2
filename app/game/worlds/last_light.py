"""Last Light -- team zombie survival across four places, one at a time.

**A round** is fought in one area, wave after wave, until every survivor in
it is dead; then the server moves everybody to a different area and starts
again at wave one.  Each wave sends a set number of infected (more, faster
and stranger as the waves climb), spread over its first few minutes so a
wave lasts about four, and ends when the last of them is dead.  Between
waves there is a short breather to regroup, restock and patch up.  Every
fifth wave brings a Tank.

**Dying** is not the end of a life at once: a survivor brought to nothing is
*downed* -- on the ground, still shooting, bleeding out -- and a teammate
holding *use* beside them for a few seconds gets them back up.  The third
time in one life (or bleeding out, or nobody coming) they are dead, and the
dead watch the living until the next wave begins, when everybody who is
dead comes back at the area's safe room.

**The holdout** is the bunker people join into while a wave is on: the next
wave deploys them with everybody else.  Joining between waves deploys at
once.

**The tools**: ammunition crates (as often as you like), first-aid cabinets
(a few charges a wave, and they reset your downs), explosive barrels that
come back every wave, and in every area one noise-maker -- a bell, a siren,
a horn -- that drags the whole horde to it for a quarter of a minute.

The infected themselves -- their kinds, their pathing and their tricks --
live in :mod:`app.game.worlds.infected`.
"""
from __future__ import annotations

import math
import random
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple

from ..instance import (EYE_HEIGHT, MAX_HEALTH, GameInstance, Player, now,
                        ray_aabb, vec_len)
from ..maps import lastlight
from ...models import catalog
from .infected import (KIND_INDEX, KINDS, SPECIALS, UNLOCK, WEIGHT, Horde,
                       NpcShot, Zombie)

TEAM = "survivors"
NEVER = 1e18                     # "respawn at": not until a wave says so

FIRST_SETUP = 30.0               # a new area: look round, restock
BREATHER = 20.0                  # between waves
WIPE_SECONDS = 12.0              # the end card before the move
WAVE_TARGET = 240.0              # what a wave is tuned to last
OVERDUE = 330.0                  # after this the stragglers hurry up
UNSEEN_LIMIT = 240.0             # out of everybody's sight this long: gone

DOWNS_PER_LIFE = 2               # the third time is death
BLEED_PER_SECOND = 1.6           # a downed survivor's 100 runs out in ~a minute
REVIVE_SECONDS = 3.2
REVIVE_RANGE = 7.0
REVIVED_HEALTH = 35
USE_RANGE = 7.5
STRUGGLE_PRESSES = 9
MED_CHARGES = 3
MED_HEAL = 50
LURE_SECONDS = 16.0
LURE_COOLDOWN = 100.0
BILE_SECONDS = 12.0
BARREL_HP = 30.0
BARREL_RADIUS = 15.0
SPAWN_MIN = 70.0                 # infected appear at least this far away
SPAWN_MAX = 260.0

MODIFIERS = {
    "rush": {"name": "Rush Hour", "blurb": "Half of them are running."},
    "horde": {"name": "Horde Night", "blurb": "Twice as many, all at once."},
    "elite": {"name": "Elite Wave", "blurb": "More specials, and tougher."},
    "fog": {"name": "Fog Bank", "blurb": "You will not see them coming."},
}


class Barrel:
    """A red drum of fuel, on its own spot; shoot it and stand back."""

    __slots__ = ("ident", "pos", "health", "alive", "team", "username", "brain",
                 "npc", "vel", "pid")

    def __init__(self, ident: int, pos: Sequence[float]):
        self.ident = ident
        self.pid = -ident
        self.pos = [float(pos[0]), float(pos[1]), float(pos[2])]
        self.health = BARREL_HP
        self.alive = True
        self.team = "world"
        self.username = "Fuel Barrel"
        self.brain = None
        self.npc = True
        self.vel = [0.0, 0.0, 0.0]

    def hitbox(self):
        x, y, z = self.pos
        return ([x - 1.3, y, z - 1.3], [x + 1.3, y + 3.6, z + 1.3])

    def head_box(self):
        return self.hitbox()

    def send(self, payload: Dict[str, Any]) -> None:
        pass


class Dummy(Barrel):
    """A practice target in the holdout's range.  It never goes down."""

    __slots__ = ()

    def hitbox(self):
        x, y, z = self.pos
        return ([x - 1.5, y, z - 1.0], [x + 1.5, y + 5.4, z + 1.0])

    def head_box(self):
        x, y, z = self.pos
        return ([x - 0.9, y + 4.0, z - 0.8], [x + 0.9, y + 5.45, z + 0.8])


class LastLight(GameInstance):
    mode = "survival"
    friendly_fire = False
    shuffle_enabled = False
    respawn_seconds = 0.0

    @staticmethod
    def build_map() -> Dict[str, Any]:
        return lastlight.build()

    # ============================================================== setup
    def setup(self) -> None:
        markers = self.map.get("markers", {})
        self.areas: Dict[str, Dict[str, Any]] = {
            a["id"]: a for a in markers.get("areas", [])}
        self.area_order = [a["id"] for a in markers.get("areas", [])]
        self.lobby = markers.get("lobby") or {}
        self.rng = random.Random()
        self.horde = Horde(self)
        self._payloads: Dict[str, Dict[str, Any]] = {}
        self.area_id = self.rng.choice(self.area_order)
        self.wave = 0
        self.best = 0                       # best wave reached on this server
        self.phase = "setup"
        self.phase_until = now() + FIRST_SETUP
        self.wave_started = 0.0
        self.plan: Dict[str, Any] = {}
        self.modifier = ""
        self.last_modifier = ""
        self.wave_kills = 0
        self.round_kills = 0
        self.round_started = now()
        self.barrels: List[Barrel] = []
        self.dummies: List[Dummy] = [
            Dummy(900 + i, p["p"]) for i, p in
            enumerate((self.lobby.get("points") or {}).get("dummy", []))]
        self.med_charges: List[int] = []
        self.lure_until = 0.0
        self.lure_ready = 0.0
        self.wipe_card: Dict[str, Any] = {}
        self.spawn_cache: Tuple[float, List[Dict[str, Any]]] = (0.0, [])
        self.next_pack = 0.0
        self.paused = False
        self._me_tick = 0
        nav = getattr(self.host, "nav", None)
        if nav is not None and not nav.ready:
            nav.build_async()
        self._arm_area()

    # ------------------------------------------------------------- teams
    def team_names(self) -> List[str]:
        return [TEAM]

    def pick_team(self, player: Player) -> str:
        return TEAM

    # ------------------------------------------------------------- areas
    @property
    def area(self) -> Dict[str, Any]:
        return self.areas[self.area_id]

    def map_payload(self, player: Optional[Player] = None) -> Dict[str, Any]:
        cached = self._payloads.get(self.area_id)
        if cached is None:
            cached = lastlight.area_payload(self.map, self.area_id)
            area = self.area
            cached["markers"].update({
                "ammo": [p["p"] for p in area["points"].get("ammo", [])],
                "med": [p["p"] for p in area["points"].get("med", [])],
                "landmarks": area.get("landmarks", []),
                "dummies": [d.pos for d in self.dummies],
                "safe": [s["p"] for s in area["safe"]],
            })
            self._payloads[self.area_id] = cached
        return cached

    def _arm_area(self) -> None:
        """Barrels on their spots and full cabinets: the area as found."""
        area = self.area
        self.barrels = [Barrel(i + 1, p["p"]) for i, p in
                        enumerate(area["points"].get("barrel", []))]
        self.med_charges = [MED_CHARGES] * len(area["points"].get("med", []))
        self.lure_until = 0.0
        self.lure_ready = 0.0

    # ------------------------------------------------------------ players
    def where(self, player: Player) -> str:
        return player.extra.get("ll_where", "lobby")

    def field_players(self) -> List[Player]:
        return [p for p in self.players.values() if self.where(p) == "field"]

    def survivors(self) -> List[Player]:
        """The living in the area: standing, downed or pinned."""
        return [p for p in self.players.values()
                if p.alive and self.where(p) == "field"]

    def standing(self) -> List[Player]:
        return [p for p in self.survivors() if not p.extra.get("downed")]

    def humans_here(self) -> bool:
        return any(p.brain is None for p in self.players.values())

    def spawn_points(self, team: str) -> List[Dict[str, Any]]:
        where = getattr(self, "_deploying", "lobby")
        if where == "field":
            return list(self.area["safe"]) or list(self.lobby.get("safe", []))
        return list(self.lobby.get("safe", [])) or super().spawn_points(team)

    def spawn_player(self, player: Player) -> None:
        if "ll_where" not in player.extra:
            player.extra["ll_where"] = "field" if self.phase == "setup" else "lobby"
            player.extra["ll"] = {"kills": 0, "specials": 0, "revives": 0,
                                  "downs": 0, "damage": 0, "best": 0}
        self._deploying = player.extra["ll_where"]
        try:
            super().spawn_player(player)
        finally:
            self._deploying = "lobby"
        player.respawn_at = NEVER
        for key in ("downed", "pinned_by", "biled_until", "poison_until",
                    "revive", "struggle", "using"):
            player.extra.pop(key, None)
        player.extra["downs"] = 0
        self._send_me(player, force=True)

    def deploy(self, player: Player) -> None:
        """Into the area, at its safe room."""
        player.extra["ll_where"] = "field"
        self.spawn_player(player)
        if player.brain is not None:
            player.brain.on_spawn()

    def to_lobby(self, player: Player) -> None:
        player.extra["ll_where"] = "lobby"
        self.spawn_player(player)

    def on_player_ready(self, player: Player) -> None:
        area = self.area
        lines = ["Last Light -- %s. Stay together, revive each other, and make "
                 "every bullet count." % area["name"]]
        if self.where(player) == "lobby" and self.phase == "wiped":
            lines.append("The last stand just fell -- everybody moves to %s in a "
                         "moment, you included." % self.areas[
                             getattr(self, "_next_area_id", None) or self.area_id]["name"])
        elif self.where(player) == "lobby":
            lines.append("A wave is under way: you deploy with everyone when "
                         "wave %d begins. Press F to watch the survivors."
                         % (self.wave + 1))
        else:
            lines.append("Hold E to revive a downed teammate, restock at ammo "
                         "crates and patch up at first-aid cabinets.")
        if area.get("lure"):
            name = area["lure"]["name"]
            lines.append("%s draws the horde -- use it to buy breathing room."
                         % (name[:1].upper() + name[1:]))
        for line in lines:
            player.send({"t": "chat", "kind": "system", "from": "", "id": 0,
                         "m": line, "at": time.time()})
        self._send_me(player, force=True)

    def on_player_leave(self, player: Player) -> None:
        pinner = self.horde.zombies.get(player.extra.get("pinned_by", 0))
        if pinner is not None:
            self.horde._release(pinner, now(), stun=0.6)

    # ------------------------------------------------------------- input
    def max_speed(self, player: Player) -> float:
        if player.extra.get("downed"):
            return 6.0
        return super().max_speed(player)

    def handle_input(self, player: Player, message: Dict[str, Any]) -> None:
        if player.extra.get("pinned_by"):
            with self.lock:
                try:
                    player.yaw = float(message.get("y", player.yaw))
                except (TypeError, ValueError):
                    pass
                moment = now()
                if moment - player.extra.get("pin_corrected", 0) > 0.5:
                    player.extra["pin_corrected"] = moment
                    self.correct(player)
            return
        super().handle_input(player, message)

    def handle_fire(self, player: Player, message: Dict[str, Any]) -> None:
        if player.extra.get("pinned_by"):
            return
        super().handle_fire(player, message)

    def on_action(self, player: Player, message: Dict[str, Any]) -> None:
        kind = message.get("k")
        if kind == "use":
            self.use(player)
        elif kind == "unuse":
            player.extra.pop("using", None)

    def use(self, player: Player) -> None:
        """E: struggle, ring the lure, restock, patch up, or start reviving."""
        if not player.alive or self.where(player) != "field":
            if self.where(player) == "lobby":
                self._restock(player, quiet=True)
            return
        moment = now()
        if player.extra.get("pinned_by"):
            player.extra["struggle"] = player.extra.get("struggle", 0) + 1
            if player.extra["struggle"] >= STRUGGLE_PRESSES:
                pinner = self.horde.zombies.get(player.extra["pinned_by"])
                if pinner is not None:
                    self.horde._release(pinner, moment, stun=2.0)
                else:
                    self.unpin(player)
                player.send({"t": "notice", "m": "You fought it off!"})
            return
        if player.extra.get("downed"):
            return
        lure = self.area.get("lure")
        if lure and math.dist(player.pos, lure["p"]) < USE_RANGE + 2.0:
            self.ring_lure(player)
            return
        for point in self.area["points"].get("ammo", []):
            if math.dist(player.pos, point["p"]) < USE_RANGE:
                self._restock(player)
                return
        for index, point in enumerate(self.area["points"].get("med", [])):
            if math.dist(player.pos, point["p"]) < USE_RANGE:
                self._medicate(player, index)
                return
        player.extra["using"] = True

    def _restock(self, player: Player, quiet: bool = False) -> None:
        moment = now()
        if moment < player.extra.get("restock_at", 0):
            return
        player.extra["restock_at"] = moment + 1.0
        for slot in range(catalog.HOTBAR_SIZE):
            stats = player.weapon_stats(slot)
            if player.weapon(slot) is None:
                continue
            player.ammo[slot] = int(stats.get("mag", 0) or 0)
            player.reserve[slot] = int(stats.get("reserve", 0) or 0)
        player.reload_until = 0.0
        player.send({"t": "you", "ammo": player.ammo[player.slot],
                     "reserve": player.reserve[player.slot], "slot": player.slot})
        if not quiet:
            player.send({"t": "notice", "m": "Ammunition restocked."})
            player.send({"t": "zfx", "k": "restock", "p": player.pos, "id": 0})

    def _medicate(self, player: Player, index: int) -> None:
        if index >= len(self.med_charges) or self.med_charges[index] <= 0:
            player.send({"t": "notice", "m": "This cabinet is empty until the "
                         "next wave.", "bad": True})
            return
        if player.health >= MAX_HEALTH and not player.extra.get("downs"):
            player.send({"t": "notice", "m": "You are already patched up."})
            return
        self.med_charges[index] -= 1
        self.heal(player, MED_HEAL, player)
        player.extra["downs"] = 0
        player.extra.pop("poison_until", None)
        player.send({"t": "notice", "m": "Patched up (%d left in this cabinet)."
                     % self.med_charges[index]})
        self._send_me(player, force=True)

    def ring_lure(self, player: Player) -> None:
        moment = now()
        lure = self.area["lure"]
        if moment < self.lure_ready:
            player.send({"t": "notice", "m": "%s needs %d more seconds."
                         % (lure["name"][:1].upper() + lure["name"][1:],
                            int(self.lure_ready - moment) + 1), "bad": True})
            return
        if self.phase != "active":
            player.send({"t": "notice", "m": "Nothing out there to call yet.",
                         "bad": True})
            return
        self.lure_until = moment + LURE_SECONDS
        self.lure_ready = moment + LURE_COOLDOWN
        for z in self.horde.zombies.values():
            z.lured = True
        self.horde.field_at = 0.0
        self.broadcast({"t": "zfx", "k": "lure", "s": lure["sound"],
                        "p": lure["p"], "id": 0, "by": player.username})
        self.system_message("%s rang %s -- the horde is drawn to it!"
                            % (player.username, lure["name"]))
        self.push_event("lure", by=player.username, what=lure["name"])
        player.score += 2

    def lure_focus(self) -> Optional[List[float]]:
        if now() < self.lure_until and self.area.get("lure"):
            return self.area["lure"]["focus"]
        return None

    # ============================================================ hitting
    def hostiles_for(self, player: Player):
        """What a bot in this world fights: the infected, never people."""
        if self.where(player) != "field":
            return
        for z in self.horde.zombies.values():
            if z.alive and not z.hidden and z.state != "rise":
                yield z

    def entity(self, eid: Optional[int]):
        if eid is None:
            return None
        found = self.players.get(eid)
        if found is not None:
            return found
        return self.horde.zombies.get(eid)

    def nearest_player_hit(self, shooter, origin, direction, max_dist: float):
        best, best_d, head = None, max_dist, False
        if isinstance(shooter, Zombie):
            return None, max_dist, False
        if self.where(shooter) == "lobby":
            targets = self.dummies
        else:
            targets = list(self.horde.zombies.values()) + \
                [b for b in self.barrels if b.alive]
        ox, oy, oz = origin
        dx, dy, dz = direction
        for target in targets:
            if isinstance(target, Zombie):
                if target.hidden:
                    continue
                cx, cy, cz = target.centre()
                radius = max(KINDS[target.kind]["box"][:2]) * 0.75 + 0.5
            else:
                cx, cy, cz = target.pos[0], target.pos[1] + 2.0, target.pos[2]
                radius = 3.4
            t = (cx - ox) * dx + (cy - oy) * dy + (cz - oz) * dz
            if t < -radius or t > best_d + radius:
                continue
            px, py, pz = ox + dx * t - cx, oy + dy * t - cy, oz + dz * t - cz
            if px * px + py * py + pz * pz > radius * radius:
                continue
            lo, hi = target.hitbox()
            hit = ray_aabb(origin, direction, lo, hi)
            if hit is None or hit >= best_d:
                continue
            hlo, hhi = target.head_box()
            best, best_d = target, hit
            head = not isinstance(target, Barrel) or isinstance(target, Dummy)
            head = head and ray_aabb(origin, direction, hlo, hhi) is not None
        return best, best_d, head

    def apply_damage(self, victim, attacker, amount: float, weapon_name: str,
                     headshot: bool = False) -> None:
        if isinstance(victim, Zombie):
            self.damage_infected(victim, attacker, amount, weapon_name, headshot)
        elif isinstance(victim, Dummy):
            if attacker is not None:
                attacker.send({"t": "dealt", "a": round(amount, 1), "hs": headshot,
                               "target": victim.pid, "hp": 100})
        elif isinstance(victim, Barrel):
            if victim.alive:
                victim.health -= amount
                if victim.health <= 0:
                    self.detonate(victim, attacker)
        else:
            self.hurt_survivor(victim, attacker, amount, weapon_name, headshot)

    def do_melee(self, player: Player, direction, stats: Dict[str, Any]) -> None:
        """Swing at the infected; a swing at a Leaper knocks it off whoever
        it is on, and one at a Riot from the front staggers it open."""
        if self.where(player) != "field":
            return
        reach = float(stats.get("range", 9.0)) + 1.0
        arc = float(stats.get("arc", 0.55))
        origin = [player.pos[0], player.pos[1] + 3.4, player.pos[2]]
        weapon_name = (player.weapon() or {}).get("name", "Fists")
        hits = 0
        moment = now()
        for z in list(self.horde.zombies.values()):
            if z.hidden:
                continue
            target = z.centre()
            delta = [target[i] - origin[i] for i in range(3)]
            distance = vec_len(delta)
            if distance > reach + KINDS[z.kind]["box"][0] * 0.5:
                continue
            unit = [v / (distance or 1.0) for v in delta]
            if unit[0] * direction[0] + unit[1] * direction[1] + \
                    unit[2] * direction[2] < 1.0 - arc:
                continue
            if not self.line_of_sight(origin, target):
                continue
            hits += 1
            if z.state == "pin":
                self.horde._release(z, moment, stun=1.6)
                self.push_event("save", by=player.username)
                player.score += 3
            elif z.kind in ("common", "runner", "mite", "riot", "spitter",
                            "screamer", "bomber", "leaper") and z.state == "walk":
                z.state = "stun"
                z.state_until = moment + (1.4 if z.kind == "riot" else 0.6)
                z.data["shoved"] = moment
            self.damage_infected(z, player, float(stats.get("damage", 30)),
                                 weapon_name, False, melee=True)
        if hits:
            player.send({"t": "hit", "n": hits})

    def explode(self, proj) -> None:
        super().explode(proj)
        owner = self.players.get(proj.pid_owner)
        radius = float(proj.stats.get("splash", 8.0))
        splash = float(proj.stats.get("splash_damage", proj.stats.get("damage", 50)))
        self._blast(proj.pos, radius, splash * 1.6, owner, "Blast Launcher",
                    hurt_people=False)

    def _blast(self, centre: Sequence[float], radius: float, damage: float,
               owner: Optional[Player], weapon: str, hurt_people: bool = True,
               people_damage: float = 0.0, zombie_scale: float = 1.0) -> None:
        for z in list(self.horde.zombies.values()):
            d = math.dist(z.centre(), centre)
            if d > radius + 1.0 or z.hidden:
                continue
            falloff = max(0.35, 1.0 - (d / (radius + 1.0)) ** 1.5)
            self.damage_infected(z, owner, damage * falloff * zombie_scale, weapon,
                                 False, blast=True)
        for barrel in self.barrels:
            if barrel.alive and math.dist(barrel.pos, centre) < radius * 0.8:
                barrel.health = 0
                self.detonate(barrel, owner)
        if not hurt_people:
            return
        for s in self.survivors():
            mid = [s.pos[0], s.pos[1] + 2.6, s.pos[2]]
            d = math.dist(mid, centre)
            if d > radius:
                continue
            falloff = 1.0 - (d / radius) ** 1.4
            push = [mid[0] - centre[0], max(0.5, mid[1] - centre[1]), mid[2] - centre[2]]
            length = vec_len(push) or 1.0
            knock = 46.0 * falloff
            self.knock(s, [push[0] / length * knock, abs(push[1] / length) * knock * 1.1
                           + 12.0, push[2] / length * knock])
            if people_damage * falloff > 0.5:
                self.hurt_survivor(s, owner, people_damage * falloff, weapon)

    def detonate(self, barrel: Barrel, by: Optional[Player]) -> None:
        if not barrel.alive:
            return
        barrel.alive = False
        centre = [barrel.pos[0], barrel.pos[1] + 1.8, barrel.pos[2]]
        self.broadcast({"t": "fx", "k": "explode", "p": centre, "r": BARREL_RADIUS,
                        "id": -barrel.ident, "big": 1})
        self.broadcast({"t": "zbar", "id": barrel.ident, "alive": False})
        self._blast(centre, BARREL_RADIUS, 210.0, by if isinstance(by, Player) else None,
                    "Fuel Barrel", hurt_people=True, people_damage=22.0)

    def knock(self, player: Player, velocity: Sequence[float]) -> None:
        if player.extra.get("downed") or player.extra.get("pinned_by"):
            return
        if player.brain is not None:
            brain = player.brain
            brain.airborne = True
            brain.vy = max(brain.vy, float(velocity[1]))
            return
        player.send({"t": "knock", "v": [round(v, 2) for v in velocity]})

    # ===================================================== the infected
    def damage_infected(self, z: Zombie, attacker, amount: float, weapon: str,
                        headshot: bool = False, melee: bool = False,
                        blast: bool = False) -> None:
        if not z.alive or z.hidden or amount <= 0:
            return
        moment = now()
        if z.kind == "tank" and headshot:
            amount /= 1.6                    # its head is not a weak spot
        blocked = False
        if isinstance(attacker, Player) and not blast:
            to_attacker = math.atan2(attacker.pos[0] - z.pos[0],
                                     attacker.pos[2] - z.pos[2])
            facing = abs((to_attacker - z.yaw + math.pi) % (2 * math.pi) - math.pi)
            front = facing < 1.2
            if z.kind == "riot" and front and z.state != "stun" and not melee:
                amount *= 0.12
                blocked = True
            elif z.kind == "ronin" and front and z.state in ("walk",) and \
                    not melee:
                amount *= 0.2
                blocked = True
        z.health -= amount
        if isinstance(attacker, Player):
            z.damage_by[attacker.pid] = z.damage_by.get(attacker.pid, 0.0) + amount
            stats = attacker.extra.get("ll")
            if stats is not None:
                stats["damage"] = stats.get("damage", 0) + int(amount)
            attacker.send({"t": "dealt", "a": round(amount, 1), "hs": headshot,
                           "target": z.pid, "blk": blocked,
                           "hp": max(0, int(z.health))})
            if attacker.brain is not None and z.state == "pin":
                attacker.brain.target = z.pid
        if z.state == "pin":
            z.data["pin_dmg"] = z.data.get("pin_dmg", 0.0) + amount
            if z.data["pin_dmg"] >= 60.0 and z.health > 0:
                self.horde._release(z, moment, stun=1.2)
        if blocked and moment - z.data.get("clang", 0) > 0.4:
            z.data["clang"] = moment
            self.zfx("block", z)
        if z.health <= 0:
            self.kill_infected(z, attacker if isinstance(attacker, Player) else None,
                               headshot=headshot)
        elif z.kind == "brute" and z.state == "walk" and isinstance(attacker, Player):
            z.data["charge_at"] = min(z.data.get("charge_at", 0), moment + 0.8)

    def kill_infected(self, z: Zombie, killer: Optional[Player],
                      headshot: bool = False, cause: str = "",
                      quietly: bool = False) -> None:
        if not z.alive:
            return
        z.alive = False
        self.horde.zombies.pop(z.pid, None)
        moment = now()
        if not quietly:
            self.wave_kills += 1
            self.round_kills += 1
        centre = z.centre()
        # --- what it does as it goes
        if z.state == "pin" or z.data.get("victim"):
            victim = self.players.get(z.data.get("victim", 0))
            if victim is not None and victim.extra.get("pinned_by") == z.pid:
                self.unpin(victim)
        if not quietly:
            if z.kind == "bloater":
                self.broadcast({"t": "zfx", "k": "bile", "p": centre, "id": z.pid})
                for s in self.survivors():
                    if math.dist([s.pos[0], s.pos[1] + 2.6, s.pos[2]], centre) < 11.0:
                        self.bile(s)
                self._blast(centre, 11.0, 0.0, None, "Bloater", hurt_people=True,
                            people_damage=4.0)
            elif z.kind == "bomber":
                if headshot and cause != "fuse":
                    self.broadcast({"t": "zfx", "k": "defuse", "p": centre,
                                    "id": z.pid})
                    if killer is not None:
                        killer.score += 3
                        killer.send({"t": "notice", "m": "Defused! Clean headshot."})
                else:
                    self.broadcast({"t": "fx", "k": "explode", "p": centre, "r": 13.0,
                                    "id": -z.pid, "big": 1})
                    self._blast(centre, 13.0, 220.0, killer, "Bomber",
                                hurt_people=True, people_damage=46.0)
            elif z.kind == "hive":
                self.broadcast({"t": "zfx", "k": "burst", "p": centre, "id": z.pid})
                scale = z.max_health / KINDS["hive"]["hp"]
                for k in range(6):
                    angle = k * math.pi / 3.0
                    pos = [z.pos[0] + math.cos(angle) * 2.5, z.pos[1] + 0.5,
                           z.pos[2] + math.sin(angle) * 2.5]
                    if not self.body_fits(pos[0], pos[1], pos[2]):
                        pos = list(z.pos)
                    self.horde.spawn("mite", pos, KINDS["mite"]["hp"] * scale,
                                     KINDS["mite"]["dmg"] * self._dmg_scale(),
                                     self.wave)
            elif z.kind == "spitter":
                self.horde.add_pool(z.pos, 5.0, 4.0)
                self.broadcast({"t": "zpool", "p": z.pos, "r": 5.0, "s": 4.0})
            elif z.kind == "tank":
                self.push_event("tank_down", by=killer.username if killer else "")
        if z.kind in ("common", "runner"):
            self.horde.corpses.append((moment, list(z.pos)))
            del self.horde.corpses[:-30]
        self.broadcast({"t": "zd", "id": z.pid, "by": killer.pid if killer else 0,
                        "hs": bool(headshot), "k": KIND_INDEX[z.kind],
                        "gone": bool(quietly)})
        if quietly:
            return
        # --- credit
        if z.kind == "tank" and z.damage_by:
            total = sum(z.damage_by.values()) or 1.0
            for pid, dealt in z.damage_by.items():
                player = self.players.get(pid)
                if player is not None:
                    player.score += int(round(z.score_value * dealt / total))
        if killer is not None:
            killer.kills += 1
            stats = killer.extra.get("ll") or {}
            stats["kills"] = stats.get("kills", 0) + 1
            if z.kind != "tank":
                killer.score += z.score_value
            if KINDS[z.kind].get("special"):
                stats["specials"] = stats.get("specials", 0) + 1
                self.broadcast({"t": "kill", "k": killer.username, "kid": killer.pid,
                                "kteam": TEAM, "v": KINDS[z.kind]["name"],
                                "vid": z.pid, "vteam": "infected",
                                "w": (killer.weapon() or {}).get("name", ""),
                                "hs": headshot, "streak": 0})
                if killer.brain is not None:
                    killer.brain.on_kill(z)

    def infected_hits(self, z: Zombie, target: Player, damage: float,
                      name: str, knock: Optional[Sequence[float]] = None,
                      quiet: bool = False) -> None:
        if not target.alive or self.where(target) != "field":
            return
        self.hurt_survivor(target, z, damage, name)
        if knock is not None and target.alive:
            self.knock(target, knock)

    def shot_landed(self, shot: NpcShot, hit: Optional[Player]) -> None:
        owner = self.horde.zombies.get(shot.owner)
        if shot.kind == "acid":
            ground = list(shot.pos)
            if hit is not None:
                ground = list(hit.pos)
            self.horde.add_pool(ground, 7.0, 7.0)
            self.broadcast({"t": "zpool", "p": ground, "r": 7.0, "s": 7.0})
        elif shot.kind == "bolt":
            if hit is not None:
                self.hurt_survivor(hit, owner, shot.damage, "Plague Captain")
                hit.extra["poison_until"] = now() + 4.0
            self.broadcast({"t": "zfx", "k": "boltend", "p": shot.pos, "id": shot.ident})
        elif shot.kind == "rock":
            self.broadcast({"t": "fx", "k": "explode", "p": shot.pos, "r": shot.splash,
                            "id": -shot.ident, "rock": 1})
            for s in self.survivors():
                mid = [s.pos[0], s.pos[1] + 2.6, s.pos[2]]
                d = math.dist(mid, shot.pos)
                if d > shot.splash:
                    continue
                falloff = 1.0 - (d / shot.splash) ** 1.3
                self.hurt_survivor(s, owner, shot.damage * max(0.3, falloff), "Tank")
                push = [mid[i] - shot.pos[i] for i in range(3)]
                length = vec_len(push) or 1.0
                self.knock(s, [push[0] / length * 50 * falloff, 30.0,
                               push[2] / length * 50 * falloff])

    def acid_burn(self, player: Player, amount: float) -> None:
        self.hurt_survivor(player, None, amount, "Acid", quiet=True)

    def bile(self, player: Player) -> None:
        player.extra["biled_until"] = now() + BILE_SECONDS
        self.horde.field_at = 0.0
        self._send_me(player, force=True)

    def pin(self, player: Player, z: Zombie) -> bool:
        if player.extra.get("pinned_by") or player.extra.get("downed"):
            return False
        player.extra["pinned_by"] = z.pid
        player.extra["struggle"] = 0
        player.extra.pop("using", None)
        self.broadcast({"t": "zfx", "k": "pin", "id": z.pid, "p": player.pos,
                        "v": player.pid})
        self.push_event("pinned", by=player.username, what=KINDS[z.kind]["name"])
        self._send_me(player, force=True)
        return True

    def unpin(self, player: Player) -> None:
        if player.extra.pop("pinned_by", None) is not None:
            player.extra.pop("struggle", None)
            self._send_me(player, force=True)

    def scream(self, z: Zombie) -> None:
        moment = now()
        self.zfx("scream", z)
        for other in self.horde.zombies.values():
            if math.dist(other.pos, z.pos) < 85.0:
                other.enraged_until = moment + 10.0
        room = self._cap() - self.horde.count(("common", "runner"))
        count = min(max(0, room), 4 + len(self.survivors()))
        if count <= 0:
            return
        spots = self._spawn_spots(near=z.pos, within=170.0)
        for _ in range(count):
            spot = self.rng.choice(spots) if spots else {"p": list(z.pos)}
            self._spawn_common(self._jitter(spot["p"]))

    def raise_dead(self, z: Zombie) -> bool:
        moment = now()
        raised = 0
        keep = []
        for at, pos in self.horde.corpses:
            if raised < 3 and moment - at < 75.0 and math.dist(pos, z.pos) < 50.0:
                self.horde.spawn("common", pos, KINDS["common"]["hp"] * self._hp_scale(),
                                 KINDS["common"]["dmg"] * self._dmg_scale(), self.wave,
                                 rise=True)
                raised += 1
            else:
                keep.append((at, pos))
        self.horde.corpses = keep
        if raised:
            self.zfx("raise", z)
        return raised > 0

    def zfx(self, kind: str, z: Zombie) -> None:
        self.broadcast({"t": "zfx", "k": kind, "id": z.pid,
                        "p": [round(v, 2) for v in z.pos]})

    def wave_overdue(self) -> bool:
        return self.phase == "active" and now() - self.wave_started > OVERDUE

    # ===================================================== survivors
    def hurt_survivor(self, victim: Player, attacker, amount: float,
                      weapon: str, headshot: bool = False,
                      quiet: bool = False) -> None:
        if not victim.alive or amount <= 0 or self.where(victim) != "field":
            return
        if self.phase == "wiped":
            return
        moment = now()
        if moment < victim.spawn_protect_until:
            return
        if isinstance(attacker, Player) and attacker is not victim:
            return                              # no friendly fire, ever
        amount = float(amount)
        if victim.extra.get("downed"):
            victim.health -= amount * 0.5
        else:
            victim.health -= amount
        victim.last_damage_at = moment
        victim.last_damage_from = attacker.pid if attacker is not None else None
        source = attacker.pos if attacker is not None else victim.pos
        victim.send({"t": "dmg", "hp": max(0, int(victim.health)),
                     "a": round(amount, 1), "from": source,
                     "by": getattr(attacker, "username", "") or weapon, "hs": headshot,
                     "q": quiet})
        if victim.brain is not None and isinstance(attacker, Zombie):
            victim.brain.hurt_by(attacker)
        if victim.health > 0:
            return
        if victim.extra.get("downed") or victim.extra.get("downs", 0) >= DOWNS_PER_LIFE:
            self.kill(victim, attacker, weapon, headshot)
        else:
            self.go_down(victim, attacker)

    def go_down(self, player: Player, by) -> None:
        player.extra["downed"] = True
        player.extra["downs"] = player.extra.get("downs", 0) + 1
        player.extra.pop("using", None)
        stats = player.extra.get("ll") or {}
        stats["downs"] = stats.get("downs", 0) + 1
        player.health = MAX_HEALTH
        pinner = self.horde.zombies.get(player.extra.get("pinned_by", 0))
        if pinner is not None:
            self.horde._release(pinner, now(), stun=1.0)
        self.broadcast({"t": "zdown", "id": player.pid, "on": True,
                        "by": getattr(by, "username", "")})
        self.system_message("%s is down!" % player.username)
        self.push_event("downed", by=player.username,
                        what=getattr(by, "username", "") or "")
        self._send_me(player, force=True)

    def revive(self, player: Player, by: Optional[Player]) -> None:
        player.extra.pop("downed", None)
        player.extra.pop("revive", None)
        player.health = REVIVED_HEALTH
        player.spawn_protect_until = now() + 1.5
        self.broadcast({"t": "zdown", "id": player.pid, "on": False,
                        "by": by.username if by else ""})
        if by is not None:
            by.score += 5
            stats = by.extra.get("ll") or {}
            stats["revives"] = stats.get("revives", 0) + 1
            self.system_message("%s picked %s up." % (by.username, player.username))
            self.push_event("revived", by=by.username, what=player.username)
        player.send({"t": "heal", "hp": player.health, "amt": REVIVED_HEALTH,
                     "by": by.username if by else ""})
        self._send_me(player, force=True)
        if player.brain is not None:
            player.brain.on_spawn()

    def kill(self, victim, killer, weapon_name: str, headshot: bool = False) -> None:
        if isinstance(victim, Zombie):
            self.kill_infected(victim, killer if isinstance(killer, Player) else None,
                               headshot)
            return
        if not victim.alive:
            return
        if self.where(victim) == "lobby":
            # fell out of the bunker somehow: straight back in
            self.to_lobby(victim)
            return
        victim.alive = False
        victim.health = 0
        victim.deaths += 1
        victim.streak = 0
        victim.respawn_at = NEVER
        pinner = self.horde.zombies.get(victim.extra.get("pinned_by", 0))
        if pinner is not None:
            self.horde._release(pinner, now(), stun=0.5)
        for key in ("downed", "pinned_by", "using", "revive", "biled_until",
                    "poison_until"):
            victim.extra.pop(key, None)
        name = getattr(killer, "username", "") or weapon_name
        self.broadcast({"t": "kill", "k": name, "kid": getattr(killer, "pid", 0) or 0,
                        "kteam": "infected", "v": victim.username, "vid": victim.pid,
                        "vteam": TEAM, "w": weapon_name, "hs": headshot, "streak": 0})
        victim.send({"t": "died", "in": -1, "by": name, "wave": self.wave + 1,
                     "spectate": True})
        self.on_kill(killer, victim, weapon_name)
        if self.bots is not None:
            self.bots.on_kill(killer, victim, weapon_name)
        self._send_me(victim, force=True)

    def _send_me(self, player: Player, force: bool = False) -> None:
        """This player's own survival state, sent when it changes."""
        if player.ws is None and player.brain is not None:
            return
        moment = now()
        revive = player.extra.get("revive")
        me = {
            "where": self.where(player),
            "downed": bool(player.extra.get("downed")),
            "downs": int(player.extra.get("downs", 0)),
            "pinned": int(player.extra.get("pinned_by", 0) or 0),
            "struggle": int(player.extra.get("struggle", 0) or 0),
            "biled": round(max(0.0, player.extra.get("biled_until", 0) - moment), 0),
            "poison": moment < player.extra.get("poison_until", 0),
            "revive": [revive[0], round(revive[1] / REVIVE_SECONDS, 2), revive[2]]
            if revive else None,
        }
        if not force and me == player.extra.get("_me"):
            return
        player.extra["_me"] = me
        payload = {"t": "llme"}
        payload.update(me)
        player.send(payload)

    # ============================================================== waves
    def _hp_scale(self) -> float:
        return 1.0 + 0.035 * max(0, self.wave - 1)

    def _dmg_scale(self) -> float:
        return min(2.2, 1.0 + 0.045 * max(0, self.wave - 1))

    def _crowd(self) -> int:
        return max(1, len(self.field_players()))

    def _cap(self) -> int:
        cap = min(56, 16 + 2 * self.wave + 2 * self._crowd())
        if self.modifier == "horde":
            cap += 12
        return cap

    def _compose(self) -> Dict[str, Any]:
        w, n = self.wave, self._crowd()
        commons = (8 + 5 * w + 3.5 * n)
        runners = 0.0 if w < 3 else min(0.3, 0.04 * (w - 2))
        specials = int(round(w * 0.6 + n * 0.35 - 0.4))
        specials = max(0, min(specials, 4 + w // 2, 12))
        if self.modifier == "rush":
            runners = 0.5
            commons *= 1.1
        elif self.modifier == "horde":
            commons *= 1.5
            specials = max(0, specials - 1)
        elif self.modifier == "elite":
            specials += 2
        commons = int(min(160, commons))
        tanks = 0
        if w % 5 == 0:
            tanks = 1 + (1 if w >= 15 else 0) + (1 if w >= 25 and n >= 6 else 0)
        # spread over most of the wave, so the last pack arrives with a
        # minute or so left of the four the wave is tuned to
        window = min(230.0, 200.0 + 3.0 * w)
        if self.modifier == "horde":
            window *= 0.75
        unlocked = [k for k in SPECIALS if UNLOCK.get(k, 99) <= w]
        picks: List[str] = []
        counts: Dict[str, int] = {}
        for _ in range(specials):
            options = [k for k in unlocked if counts.get(k, 0) < 3] or unlocked
            if not options:
                break
            kind = self.rng.choices(options, [WEIGHT.get(k, 1.0) for k in options])[0]
            counts[kind] = counts.get(kind, 0) + 1
            picks.append(kind)
        schedule = sorted((self.rng.uniform(12.0, window), kind) for kind in picks)
        tank_times = sorted(self.rng.uniform(35.0, 70.0) + i * 40.0
                            for i in range(tanks))
        return {"commons": commons, "runners": runners, "spawned": 0,
                "specials": schedule, "tanks": tank_times, "window": window,
                "total": commons + len(picks) + tanks}

    def begin_wave(self) -> None:
        moment = now()
        self.wave += 1
        self.modifier = ""
        if self.wave >= 3 and self.rng.random() < 0.35:
            choice = self.rng.choice([m for m in MODIFIERS if m != self.last_modifier])
            self.modifier = choice
            self.last_modifier = choice
        # the dead and the waiting come in with the wave
        for player in list(self.players.values()):
            if not player.alive or self.where(player) == "lobby":
                self.deploy(player)
        self.plan = self._compose()
        self.phase = "active"
        self.wave_started = moment
        self.phase_until = moment + WAVE_TARGET
        self.wave_kills = 0
        self.next_pack = moment + 4.0
        self.med_charges = [MED_CHARGES] * len(self.med_charges)
        for barrel in self.barrels:
            if not barrel.alive:
                barrel.alive = True
                barrel.health = BARREL_HP
        self.broadcast({"t": "zbar", "all": [[b.ident] + b.pos for b in self.barrels]})
        tank = self.wave % 5 == 0
        payload = {"t": "zwave", "wave": self.wave, "on": True, "tank": tank,
                   "total": self.plan["total"], "mod": self.modifier,
                   "mod_name": MODIFIERS.get(self.modifier, {}).get("name", ""),
                   "mod_blurb": MODIFIERS.get(self.modifier, {}).get("blurb", "")}
        self.broadcast(payload)
        text = "Wave %d -- here they come!" % self.wave
        if tank:
            text = "Wave %d -- something big is coming. Tank wave!" % self.wave
        if self.modifier:
            text += " (%s: %s)" % (MODIFIERS[self.modifier]["name"],
                                   MODIFIERS[self.modifier]["blurb"])
        self.system_message(text)
        self.push_event("wave_start", n=self.wave, tank=tank,
                        what=MODIFIERS.get(self.modifier, {}).get("name", ""))

    def clear_wave(self) -> None:
        moment = now()
        self.phase = "setup"
        self.phase_until = moment + BREATHER
        self.best = max(self.best, self.wave)
        alive = self.survivors()
        for player in alive:
            player.score += 10
            if player.extra.get("downed"):
                self.revive(player, None)
            stats = player.extra.get("ll") or {}
            stats["best"] = max(stats.get("best", 0), self.wave)
        self.broadcast({"t": "zwave", "wave": self.wave, "on": False,
                        "next": self.wave + 1, "in": BREATHER,
                        "kills": self.wave_kills,
                        "time": round(moment - self.wave_started, 1)})
        self.system_message("Wave %d cleared! %d seconds until wave %d."
                            % (self.wave, int(BREATHER), self.wave + 1))
        self.push_event("wave_clear", n=self.wave)

    def wipe(self) -> None:
        moment = now()
        self.phase = "wiped"
        self.phase_until = moment + WIPE_SECONDS
        self.best = max(self.best, self.wave - 1 if self.wave else 0)
        rows = []
        for player in self.players.values():
            stats = player.extra.get("ll") or {}
            rows.append({"id": player.pid, "name": player.username,
                         "kills": stats.get("kills", 0),
                         "specials": stats.get("specials", 0),
                         "revives": stats.get("revives", 0),
                         "damage": stats.get("damage", 0),
                         "downs": stats.get("downs", 0), "score": player.score})
        rows.sort(key=lambda r: (-r["kills"] - r["specials"] * 4 - r["revives"] * 6,
                                 r["name"].lower()))
        survived = max(0, self.wave - 1)
        nxt = self._next_area()
        self.wipe_card = {"t": "zwipe", "wave": self.wave, "survived": survived,
                          "area": self.area["name"], "next": self.areas[nxt]["name"],
                          "next_id": nxt, "in": WIPE_SECONDS, "rows": rows[:24],
                          "kills": self.round_kills,
                          "time": round(moment - self.round_started)}
        self._next_area_id = nxt
        self.broadcast(self.wipe_card)
        self.system_message("Everybody is down. You held %s for %d wave%s."
                            % (self.area["name"], survived, "" if survived == 1 else "s"))
        for player in self.players.values():
            self.host.report_round(self, player, won=survived >= 5)
        self.push_event("wipe", n=survived, what=self.area["name"])
        if self.bots is not None:
            self.bots.on_round_end("", "wipe")

    def _next_area(self) -> str:
        options = [a for a in self.area_order if a != self.area_id] or self.area_order
        return self.rng.choice(options)

    def start_round(self, area_id: Optional[str] = None, wave: int = 0,
                    setup: float = FIRST_SETUP) -> None:
        """Everybody to a fresh area, wave one (or ``wave`` + 1) next."""
        moment = now()
        self.horde.clear()
        self.area_id = area_id or getattr(self, "_next_area_id", None) or \
            self._next_area()
        self._arm_area()
        self.round_number += 1
        self.wave = wave
        self.modifier = ""
        self.plan = {}
        self.round_kills = 0
        self.round_started = moment
        self.phase = "setup"
        self.phase_until = moment + setup
        self.projectiles.clear()
        payload = {"t": "zarea", "map": self.map_payload(), "area": self.area_id,
                   "name": self.area["name"], "round": self.round_number}
        for player in list(self.players.values()):
            stats = player.extra.get("ll")
            if stats is not None:
                for key in ("kills", "specials", "revives", "downs", "damage"):
                    stats[key] = 0
            player.kills = 0
            player.deaths = 0
            player.send(payload)
            self.deploy(player)
        self.broadcast({"t": "round_start", "round": self.round_number,
                        "state": self.full_state()})
        self.system_message("Round %d: %s. %d seconds to get ready."
                            % (self.round_number, self.area["name"], int(setup)))
        self.push_event("area", what=self.area["name"])
        if self.bots is not None:
            self.bots.on_round_start()

    # -------------------------------------------------------------- spawning
    def _spawn_spots(self, near: Optional[Sequence[float]] = None,
                     within: float = 1e9) -> List[Dict[str, Any]]:
        """Spawn markers far from every survivor and out of their sight."""
        moment = now()
        survivors = self.survivors()
        cached_at, cached = self.spawn_cache
        if near is None and moment - cached_at < 2.0 and cached:
            return cached
        min_d = SPAWN_MIN * (0.6 if self.modifier == "fog" else 1.0)
        hidden, visible = [], []
        for spot in self.area["zspawn"]:
            p = spot["p"]
            if near is not None and math.dist(p, near) > within:
                continue
            nearest = min((math.dist(s.pos, p) for s in survivors), default=150.0)
            if nearest < min_d or nearest > SPAWN_MAX * (1.6 if near else 1.0):
                continue
            seen = False
            for s in survivors:
                if math.dist(s.pos, p) > 230.0:
                    continue
                eye = [s.pos[0], s.pos[1] + EYE_HEIGHT, s.pos[2]]
                if self.line_of_sight(eye, [p[0], p[1] + 3.0, p[2]]):
                    seen = True
                    break
            (visible if seen else hidden).append(spot)
        result = hidden or [s for s in visible
                            if min((math.dist(x.pos, s["p"]) for x in survivors),
                                   default=200) > 110.0] or \
            [s for s in self.area["zspawn"]
             if min((math.dist(x.pos, s["p"]) for x in survivors), default=200) > 45.0] \
            or list(self.area["zspawn"])
        if near is None:
            self.spawn_cache = (moment, result)
        return result

    def _jitter(self, point: Sequence[float]) -> List[float]:
        for _ in range(6):
            x = point[0] + self.rng.uniform(-6.0, 6.0)
            z = point[2] + self.rng.uniform(-6.0, 6.0)
            y = point[1]
            if self.body_fits(x, y, z) and self._floored(x, y, z):
                return [x, y, z]
        return list(point)

    def _spawn_common(self, pos: Sequence[float]) -> Zombie:
        runner = self.rng.random() < self.plan.get("runners", 0.0)
        kind = "runner" if runner else "common"
        return self.horde.spawn(kind, pos, KINDS[kind]["hp"] * self._hp_scale(),
                                KINDS[kind]["dmg"] * self._dmg_scale(), self.wave)

    def _spawn_special(self, kind: str) -> None:
        spots = self._spawn_spots()
        if kind in ("tank", "bomber", "brute", "ronin"):
            dry = [s for s in spots if s.get("tag") != "water"]
            spots = dry or spots
        spot = self.rng.choice(spots)
        n = self._crowd()
        scale = self._hp_scale() * min(2.5, 1.0 + 0.1 * (n - 1))
        if self.modifier == "elite":
            scale *= 1.25
        hp = KINDS[kind]["hp"] * scale
        if kind == "tank":
            hp = KINDS["tank"]["hp"] * (0.5 + 0.22 * n) * \
                (1.0 + 0.1 * max(0, self.wave // 5 - 1))
        z = self.horde.spawn(kind, self._jitter(spot["p"]), hp,
                             KINDS[kind]["dmg"] * self._dmg_scale(), self.wave)
        if kind == "tank":
            self.zfx("roar", z)
            self.system_message("A Tank is here! Everybody on it!")
            self.push_event("tank", n=self.wave)

    def _run_plan(self, moment: float) -> None:
        plan = self.plan
        if not plan:
            return
        elapsed = moment - self.wave_started
        while plan["specials"] and plan["specials"][0][0] <= elapsed:
            specials_alive = sum(1 for z in self.horde.zombies.values()
                                 if KINDS[z.kind].get("special") and z.kind != "tank")
            if specials_alive >= 3 + self.wave // 3:
                break
            _at, kind = plan["specials"].pop(0)
            self._spawn_special(kind)
        while plan["tanks"] and plan["tanks"][0] <= elapsed:
            plan["tanks"].pop(0)
            self._spawn_special("tank")
        left = plan["commons"] - plan["spawned"]
        if left <= 0 or moment < self.next_pack:
            return
        self.next_pack = moment + 1.0
        # packs keep to a schedule spread over the window, so a wave lasts
        # its four minutes however fast the team kills
        due = plan["commons"] * min(1.0, (elapsed + 8.0) / plan["window"])
        if plan["spawned"] >= due:
            return
        alive = self.horde.count(("common", "runner"))
        room = self._cap() - alive
        if room <= 0:
            return
        size = min(left, room, self.rng.randint(4, 8) + self.wave // 3)
        spots = self._spawn_spots()
        spot = self.rng.choice(spots)
        for _ in range(size):
            self._spawn_common(self._jitter(spot["p"]))
        plan["spawned"] += size
        self.next_pack = moment + self.rng.uniform(3.0, 6.0)

    def wave_left(self) -> int:
        plan = self.plan
        if not plan:
            return self.horde.count()
        return self.horde.count() + max(0, plan["commons"] - plan["spawned"]) + \
            len(plan["specials"]) + len(plan["tanks"])

    def _sweep(self, moment: float) -> None:
        """The anti-softlock: whatever nobody has been able to see for four
        minutes goes, and anything stuck out of sight is moved."""
        zombies = list(self.horde.zombies.values())
        if not zombies:
            return
        watchers = [p for p in self.survivors()]
        share = max(1, len(zombies) // 20 + 1)
        start = (self.tick_count * share) % max(1, len(zombies))
        for z in zombies[start:start + share]:
            seen = False
            mid = z.centre()
            for w in watchers:
                d = math.dist(w.pos, z.pos)
                if d < 30.0:
                    seen = True
                    break
                if d > 420.0:
                    continue
                eye = [w.pos[0], w.pos[1] + EYE_HEIGHT, w.pos[2]]
                if self.line_of_sight(eye, mid):
                    seen = True
                    break
            if seen:
                z.last_seen = moment
                continue
            if moment - z.last_seen > UNSEEN_LIMIT:
                self.kill_infected(z, None, quietly=True)
                self.wave_kills += 1
                continue
            if z.data.get("stuck", 0) >= 4 and moment - z.last_seen > 10.0:
                spots = self._spawn_spots()
                if spots:
                    z.pos = self._jitter(self.rng.choice(spots)["p"])
                    z.waypoints = []
                    z.data["stuck"] = 0
                    z.boxes_at = [1e9, 1e9, 1e9]

    # ================================================================ tick
    def on_tick(self, dt: float) -> None:
        moment = now()
        humans = self.humans_here()
        if not humans:
            # nobody real here: the round holds its breath until somebody is
            self.phase_until += dt
            self.wave_started += dt
            self.lure_until += dt
            self.lure_ready += dt
            self.horde.frozen = True
            return
        self.horde.frozen = False
        survivors = self.survivors()
        if self.phase in ("active", "setup"):
            self.horde.step(dt, survivors)
        if self.lure_until and moment >= self.lure_until:
            self.lure_until = 0.0
            for z in self.horde.zombies.values():
                z.lured = False
        self._tick_survivors(dt, moment)
        if self.phase == "setup":
            if moment >= self.phase_until:
                self.begin_wave()
        elif self.phase == "active":
            self._run_plan(moment)
            if self.tick_count % 2 == 0:
                self._sweep(moment)
            if self.wave_left() == 0:
                self.clear_wave()
        elif self.phase == "wiped":
            if moment >= self.phase_until:
                self.start_round()
            return
        if self.phase in ("active", "setup"):
            field = self.field_players()
            if field and not any(p.alive and not p.extra.get("downed") for p in field):
                if self.phase == "active" or any(not p.alive for p in field):
                    self.wipe()
            elif not field and self.phase == "active":
                # everyone in the area left: the waiting start a new round
                if any(self.where(p) == "lobby" for p in self.players.values()):
                    self.start_round(self._next_area())

    def _tick_survivors(self, dt: float, moment: float) -> None:
        self._me_tick += 1
        for player in self.survivors():
            extra = player.extra
            if extra.get("downed"):
                player.health -= BLEED_PER_SECOND * dt
                if player.health <= 0:
                    self.kill(player, None, "bleeding out")
                    continue
                if self._me_tick % 10 == 0:
                    player.send({"t": "dmg", "hp": max(0, int(player.health)),
                                 "a": 0, "from": player.pos, "by": "", "hs": False,
                                 "q": True})
            if moment < extra.get("poison_until", 0) and self._me_tick % 10 == 0:
                self.hurt_survivor(player, None, 1.5, "Plague", quiet=True)
            if extra.get("using") and not extra.get("downed") and \
                    not extra.get("pinned_by"):
                self._try_revive(player, dt)
            elif extra.get("revive") and not extra.get("downed"):
                self._cancel_revive(player)
            if extra.get("biled_until") and moment > extra["biled_until"]:
                extra.pop("biled_until", None)
            if self._me_tick % 5 == 0 or extra.get("revive"):
                self._send_me(player)
        if self._me_tick % 20 == 0:
            for player in self.players.values():
                if not player.alive or self.where(player) == "lobby":
                    self._send_me(player)

    def _try_revive(self, player: Player, dt: float) -> None:
        best, best_d = None, REVIVE_RANGE
        for other in self.survivors():
            if other is player or not other.extra.get("downed"):
                continue
            d = math.hypot(other.pos[0] - player.pos[0], other.pos[2] - player.pos[2])
            if d < best_d and abs(other.pos[1] - player.pos[1]) < 4.0:
                best, best_d = other, d
        current = player.extra.get("revive")
        if best is None:
            if current:
                self._cancel_revive(player)
            return
        if not current or current[0] != best.pid:
            current = [best.pid, 0.0, best.username]
        current[1] += dt
        player.extra["revive"] = current
        best.extra["revive"] = [player.pid, current[1], player.username]
        if current[1] >= REVIVE_SECONDS:
            player.extra.pop("revive", None)
            player.extra.pop("using", None)
            self.revive(best, player)

    def _cancel_revive(self, player: Player) -> None:
        current = player.extra.pop("revive", None)
        if current:
            other = self.players.get(current[0])
            if other is not None:
                other.extra.pop("revive", None)

    # ============================================================== wire
    def snapshot(self) -> Dict[str, Any]:
        payload = super().snapshot()
        zombies = self.horde.zombies
        if zombies and (len(zombies) <= 30 or self.tick_count % 2 == 0):
            payload["zs"] = [z.row() for z in zombies.values()]
        elif not zombies and self.tick_count % 20 == 0:
            payload["zs"] = []
        if self.horde.shots:
            payload["zp"] = [[s.ident, s.kind, round(s.pos[0], 2), round(s.pos[1], 2),
                              round(s.pos[2], 2)] for s in self.horde.shots]
        return payload

    def round_state(self) -> Dict[str, Any]:
        moment = now()
        tanks = [round(z.health / z.max_health, 3) for z in self.horde.zombies.values()
                 if z.kind == "tank"]
        specials: Dict[str, int] = {}
        for z in self.horde.zombies.values():
            if KINDS[z.kind].get("special") and z.kind != "tank":
                specials[z.kind] = specials.get(z.kind, 0) + 1
        lure = self.area.get("lure") or {}
        players = list(self.players.values())
        return {
            "area": self.area_id, "area_name": self.area["name"],
            "wave": self.wave, "best": self.best, "wphase": self.phase,
            "phase_left": round(max(0.0, self.phase_until - moment), 1),
            "wave_time": round(moment - self.wave_started, 1)
            if self.phase == "active" else 0.0,
            "zleft": self.wave_left(), "zalive": self.horde.count(),
            "total": self.plan.get("total", 0) if self.plan else 0,
            "tank": tanks, "specials": specials, "modifier": self.modifier,
            "modifier_name": MODIFIERS.get(self.modifier, {}).get("name", ""),
            "lure": {"name": lure.get("name", ""), "verb": lure.get("verb", ""),
                     "p": lure.get("p"),
                     "ready": round(max(0.0, self.lure_ready - moment), 1),
                     "on": moment < self.lure_until},
            "barrels": [[b.ident] + b.pos for b in self.barrels if b.alive],
            "pools": [p["p"] + [p["r"], round(p["until"] - moment, 1)]
                      for p in self.horde.pools],
            "med": list(self.med_charges),
            "field": sum(1 for p in players if self.where(p) == "field"),
            "alive": sum(1 for p in players if self.where(p) == "field" and p.alive),
            "lobby": sum(1 for p in players if self.where(p) == "lobby"),
            "downed": [p.pid for p in players if p.extra.get("downed")],
            "pinned": [p.pid for p in players if p.extra.get("pinned_by")],
            "where": {p.pid: self.where(p) for p in players},
            "kills": self.round_kills,
        }

    def scoreboard(self) -> List[Dict[str, Any]]:
        rows = super().scoreboard()
        for row in rows:
            player = self.players.get(row["id"])
            if player is None:
                continue
            stats = player.extra.get("ll") or {}
            row.update({"specials": stats.get("specials", 0),
                        "revives": stats.get("revives", 0),
                        "damage": stats.get("damage", 0),
                        "where": self.where(player),
                        "downed": bool(player.extra.get("downed")),
                        "alive": bool(player.alive)})
        return rows

    def describe(self) -> Dict[str, Any]:
        info = super().describe()
        info["summary"] = "Wave %d · %s" % (max(1, self.wave), self.area["name"])
        return info

    # ======================================================== sleep / wake
    def sleep_state(self) -> Dict[str, Any]:
        return {"area": self.area_id, "wave": self.wave, "best": self.best,
                "phase": self.phase}

    def resume(self, state: Dict[str, Any]) -> None:
        """Pick a sleeping round back up: the same area, between waves."""
        area = state.get("area")
        if area not in self.areas:
            area = self.rng.choice(self.area_order)
        wave = max(0, int(state.get("wave", 0) or 0))
        self.best = max(self.best, int(state.get("best", 0) or 0))
        self.round_number = max(0, self.round_number - 1)
        self.start_round(area, wave=wave, setup=BREATHER if wave else FIRST_SETUP)
