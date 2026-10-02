"""Last Light: bots that play the survival map on their own.

A bot in Last Light is a survivor with a mind of its own, not a bodyguard for
whoever is real.  What it does comes from four places:

**Its persona.**  Every tag and trait a bot has feeds a small profile when it
deploys: a ``loner`` or an ``explorer`` goes off on its own, a ``support`` or
``social_butterfly`` sticks with people and picks them up, a ``sniper_main``
or a ``veteran`` heads for the high ground and keeps watch, a ``fragger`` or a
``shotgun_rusher`` hunts the horde down and kites it round the block, a
``newbie`` trails along behind the others and now and then gets lost, a
``chaotic`` kid hops about on the boxcars and presses buttons to see what
they do, a ``chill`` one takes a breather on a bench, and a ``survivor`` main
stocks up before every wave and rings the bell at the right moment.  The
Bots Zone's own dials (tangents, AFK moments, the "anything can happen"
floor, objective focus) apply here too.

**Squads.**  Bots team up the way people do in a co-op lobby: two or three
who drift together -- never a stack of six -- a couple who latch on to a
real player, the odd one who wanders off alone and comes back when it gets
hairy.  Squads form, split when somebody wanders off between waves, and
change leader when the one in front goes down.  Members do not walk in their
leader's footprints: each keeps a loose slot beside or behind it (re-picked
every so often), reacts to it moving after a beat, jogs to catch up and
shift-walks to settle, stands in a ring facing the others when the squad
stops for a chat, looks out over the street while it holds, and a leader who
has left its squad behind stops and lets them catch up.

**The whole map.**  An area is known as a grid of places -- one on the
ground in every cell of it, and one up on whatever roof, deck or boxcar is
there -- each known for how high it is, how open, how near the infected come
out and what it is near; the named landmarks (:data:`AREA_SPOTS`) sit on top
of that for what people do with them.  Every plan is a place, scored against
where the rest of the team is right now (people do not pile into one
corner), where somebody already said they are going, where nobody has been
for a while, and which way this squad set off from the safe room -- so the
squads fan out across the map instead of milling about the spawn, and a
breather is spent in the back alleys and on the rooftops as much as at the
diner.

**What there is to do.**  Between waves: hang about in a ring and chat,
explore the landmarks, wander the streets, walk a patrol round one side of
the map, search a building room by room, climb on things, keep watch from a
roof, stock up before the wave, take a breather, mess about, go and see
what that bang was, poke at the bell.  In a wave: hold a spot (each facing
out), take the high ground, roam with the fight, kite the horde round the
block, flank it, stand guard over somebody, fall back when a spot is
overrun, and hunt the last few.  Between all of that: a glance at the gun
and a swap back, backing off a step while shooting, a hop when the wave is
cleared.

**Talking.**  Bots call out specials as they see them ("bomber by the
diner"), say what they are off to do in their own typing, and the moments
worth talking about -- a special showing up, the last one standing, a squad
taking the high ground, somebody going off alone, a barrel taking out a pack
-- go to the chat relay as speech events, where the language model writes
the line in the bot's own voice.

**Cost.**  Squads, the census of who is where and the noises worth a look
are kept by one pass a second over at most a couple of dozen survivors; a
plan scores a sample of the places, a few times a minute per squad; a bot
thinks at the usual near/far rates, and the far ones still settle fights by
the odds -- except that "near" here means near anybody real *or* near
whoever a dead or waiting player is watching, so a spectator never sees the
bots they follow fight by dice.
"""
from __future__ import annotations

import math
import random
from typing import Any, Dict, List, Optional, Sequence, Tuple

from ..instance import WALK_SPEED, now
from .brain import feet, styled

RUN = WALK_SPEED                 # what a player's movement keys give
WALK = WALK_SPEED * 0.45         # holding the "walk slowly" key
HIGH = 8.0                       # floors this far up count as high ground
CELL = 30.0                      # the area is known as cells this wide
SQUAD_MAX = 3                    # nobody plays in a stack of six
SAFE_ZONE = 45.0                 # this close to the safe room is "at spawn"
COMPASS = ["north", "north-east", "east", "south-east", "south", "south-west",
           "west", "north-west"]

# What people do with each area's places.  Flags: s = a strong point to hold,
# h = somewhere to hang about between waves, e = worth a look, c = something
# to climb about on, r = trouble while a wave is on (spawns, water, a maze),
# p = there is high ground right next to it.
AREA_SPOTS: Dict[str, Dict[str, str]] = {
    "town": {
        "the Sheriff's Office": "shp", "Rosie's Diner": "he", "the Bijou": "e",
        "the town square": "sh", "the church": "er", "the bell tower": "e",
        "the gas station": "er", "the rail yard": "ec", "the grain silos": "ec",
        "the school": "es", "the back alley": "e", "Maple Street": "he",
    },
    "hospital": {
        "the hospital lobby": "sh", "the parking garage": "spe", "the skybridge": "pe",
        "the helipad": "spe", "the ambulance bay": "he", "the checkpoint": "sh",
        "the hedge maze": "er", "the strip mall": "eh", "the construction site": "ec",
        "the helicopter": "ec", "the basketball court": "he", "the bus depot": "e",
    },
    "docks": {
        "the harbourmaster's office": "shp", "the ship": "spe", "the bridge": "pe",
        "the pier": "er", "the lighthouse": "erp", "the container yard": "sc",
        "warehouse one": "sp", "warehouse two": "sp", "the fish market": "he",
        "the Rusty Anchor": "he", "the tank farm": "er", "the boatyard": "e",
        "the gantry crane": "ec",
    },
    "camp": {
        "the ranger station": "sh", "the mess hall": "she", "the overlook": "pe",
        "the old mine": "er", "the boathouse": "e", "the amphitheatre": "sh",
        "the raft": "er", "the island": "er", "the west cabins": "e",
        "the east cabins": "e", "the fire lookout": "pe", "the car park": "h",
        "the archery range": "he", "the creek": "e",
    },
}

# How a special gets called out, before the "by the diner" goes on the end.
CALLOUTS: Dict[str, List[str]] = {
    "bloater": ["bloater", "fat one", "dont pop the bloater close"],
    "bomber": ["BOMBER", "bomber", "bomber incoming", "headshot the bomber"],
    "leaper": ["leaper", "leaper!!", "watch the leaper"],
    "brute": ["brute", "BRUTE", "brute charging"],
    "spitter": ["spitter", "spitter, move", "acid guy"],
    "screamer": ["screamer", "kill the screamer", "screamer!!"],
    "riot": ["riot", "riot, shoot his back", "armored one"],
    "captain": ["plague captain", "captain", "the captain is here"],
    "hive": ["hive", "hive, back up", "bug guy"],
    "burrower": ["burrower", "burrower under us", "something digging"],
    "ronin": ["ronin", "sword guy", "ronin!!"],
    "tank": ["TANK", "tank!!", "TANK INCOMING", "big one"],
}

LINES: Dict[str, List[str]] = {
    "omw": ["omw", "coming", "got you", "hold on", "im coming"],
    "cover": ["covering", "i got you", "go go", "watching your back"],
    "regroup": ["regroup", "stack up", "on me", "group up", "everyone together"],
    "solo": ["brb checking something", "going for a look", "scouting", "be right back"],
    "ammo": ["need ammo", "ammo", "reloading", "out of ammo", "getting ammo"],
    "low": ["im low", "need meds", "low hp", "healing"],
    "lure": ["ringing it", "pulling them", "lure!!", "bell time"],
    "perch": ["get up here", "high ground", "up top", "on the roof"],
    "lost": ["where is everyone", "wait where are you guys", "lost lol", "guys?"],
    "hunt": ["few left", "hunting the last ones", "where are they", "find the last one"],
    "backoff": ["back up", "too many", "fall back", "falling back"],
    "practice": ["warming up", "practice", "lol the dummy"],
    "wander": ["gonna look around", "walking the block", "checking around",
               "taking a walk lol", "ill be around"],
    "search": ["looting", "checking inside", "anything in here?", "searching this place",
               "nothing in here"],
    "lookout": ["ill watch from up here", "eyes up", "watching this side",
                "i got overwatch", "i can see everything from here"],
    "climb": ["parkour", "look where i am", "up here lol", "can you get up here",
              "how did i get up here"],
    "patrol": ["patrolling", "ill take this side", "walking the perimeter",
               "checking the edge"],
    "prep": ["stocking up", "grab ammo before the wave", "full ammo", "topping up",
             "get ammo guys"],
    "mess": ["lol", "wheee", "look at me", "bunny hop gang", "im so bored"],
    "curious": ["what was that", "did something blow up", "whats over there",
                "you hear that?", "going to check that out"],
    "kite": ["kiting them", "im kiting", "follow me im kiting", "training them",
             "come get me"],
    "flank": ["flanking", "going round the side", "hitting them from the side"],
    "fallback": ["falling back", "too many here", "moving back", "cant hold this"],
    "guard": ["i got you", "sticking with you", "ill cover you"],
    "poke": ["what does this do", "ding dong", "lol it doesnt work", "*presses button*",
             "why wont it ring"],
    "celebrate": ["ez", "gg wave", "lets gooo", "too easy", "clean", "w"],
    "rest": ["afk 1 sec", "brb", "1 sec", "sec"],
}


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def _flat(a: Sequence[float], b: Sequence[float]) -> float:
    return math.hypot(a[0] - b[0], a[2] - b[2])


def _bearing(frm: Sequence[float], to: Sequence[float]) -> float:
    return math.atan2(to[0] - frm[0], to[2] - frm[2])


def _angle_gap(a: float, b: float) -> float:
    return abs((a - b + math.pi) % (2 * math.pi) - math.pi)


# ================================================================== intel
class AreaIntel:
    """One area as the bots know it: places, high ground, supplies, danger."""

    def __init__(self, area: Dict[str, Any], grid) -> None:
        self.id = area["id"]
        self.name = area.get("name", self.id)
        self.area = area
        self.grid = grid
        safe = area.get("safe") or []
        if safe:
            self.safe = [sum(s["p"][i] for s in safe) / len(safe) for i in range(3)]
        else:
            self.safe = list(area.get("centre") or [0.0, 0.0, 0.0])
        self.centre = list(area.get("centre") or self.safe)
        rect = area.get("rect")
        if not rect:
            rect = [self.centre[0] - 280, self.centre[0] + 280,
                    self.centre[2] - 280, self.centre[2] + 280]
        self.rect = [float(v) for v in rect]
        self.half = max(60.0, min(self.rect[1] - self.rect[0], self.rect[3] - self.rect[2]) / 2.0)
        self.zspawn = [z["p"] for z in area.get("zspawn") or []]
        self.risky_spawns = [z["p"] for z in area.get("zspawn") or [] if z.get("tag")]
        self.lure = area.get("lure")
        self.landmarks = list(area.get("landmarks") or [])
        flags = AREA_SPOTS.get(self.id, {})
        self.spots: List[Dict[str, Any]] = []
        for mark in self.landmarks:
            point = self._ground(mark["p"])
            if point is None:
                continue
            self.spots.append({"name": mark["name"], "p": point,
                               "flags": flags.get(mark["name"], "e"),
                               "danger": self._danger(point)})
        self.perches: List[Dict[str, Any]] = []
        self.places: List[Dict[str, Any]] = []
        self.high_places: List[Dict[str, Any]] = []
        self.field_name = "ll_safe_%s" % self.id
        self._perches_built = False
        self._places_built = False
        self.grounded = bool(grid is not None and grid.ready)

    # ------------------------------------------------------------ helpers
    def _ground(self, point: Sequence[float]) -> Optional[List[float]]:
        grid = self.grid
        if grid is None or not grid.ready:
            return [point[0], point[1], point[2]]
        node = grid.nearest([point[0], max(point[1], 0.5), point[2]], 4)
        return grid.point(node) if node >= 0 else None

    def _danger(self, point: Sequence[float]) -> float:
        """How far the nearest place the infected come out of is."""
        return min((_flat(point, z) for z in self.zspawn), default=999.0)

    def name_of(self, pos: Sequence[float], reach: float = 75.0) -> str:
        best, best_d = "", reach
        for mark in self.landmarks:
            d = _flat(mark["p"], pos)
            if d < best_d:
                best, best_d = mark["name"], d
        return best

    def compass(self, pos: Sequence[float]) -> str:
        """Which side of the area a point is on, for somewhere with no name."""
        dx, dz = pos[0] - self.centre[0], pos[2] - self.centre[2]
        if math.hypot(dx, dz) < self.half * 0.22:
            return "the middle"
        k = int(round(math.atan2(dx, dz) / (math.pi / 4))) % 8
        return "the %s side" % COMPASS[k]

    def describe(self, pos: Sequence[float]) -> str:
        return self.name_of(pos, 60.0) or self.compass(pos)

    def cell_of(self, pos: Sequence[float]) -> Tuple[int, int]:
        return (int((pos[0] - self.rect[0]) // CELL), int((pos[2] - self.rect[2]) // CELL))

    def ring(self, pos: Sequence[float]) -> float:
        """0 at the middle of the area, 1 at its edge."""
        return min(1.0, math.hypot(pos[0] - self.centre[0], pos[2] - self.centre[2]) / self.half)

    def reachable(self, point: Sequence[float]) -> bool:
        """Can a body get from here back to the safe room?  Read off one flow
        field built in the background; unknown until it is ready."""
        grid = self.grid
        if grid is None or not grid.ready:
            return True
        dist = grid.field(self.field_name, self.safe)
        if dist is None:
            return True
        node = grid.nearest(point, 3)
        return node >= 0 and dist[node] < 1e29

    def build_perches(self) -> None:
        """The high ground: supply points up on roofs and decks, and the
        highest floor a body can stand on next to each landmark that has
        one -- kept only once the safe-room field says you can get back."""
        grid = self.grid
        if self._perches_built or grid is None or not grid.ready:
            return
        if grid.field(self.field_name, self.safe) is None:
            return                       # still building in the background
        out: List[Dict[str, Any]] = []
        for kind in ("ammo", "med"):
            for point in (self.area.get("points") or {}).get(kind, []):
                p = point["p"]
                if p[1] >= HIGH and self.reachable(p):
                    out.append({"name": self._perch_name(p), "p": list(p), "supply": kind})
        for spot in self.spots:
            if "p" not in spot["flags"]:
                continue
            high = self._highest_near(spot["p"], 26.0)
            if high is not None and all(_flat(high, o["p"]) > 14 for o in out):
                out.append({"name": self._perch_name(high, spot["name"]), "p": high})
        for perch in out:
            perch["danger"] = self._danger(perch["p"])
        self.perches = out
        self._perches_built = True

    def build_places(self) -> None:
        """Somewhere to be in every part of the area: a place on the ground in
        each cell a body can reach, and one up top where a roof, a deck or a
        boxcar is -- each known for its height, how open it is, how near the
        infected come out and what it is near.  A sample of each cell's
        columns, once per area per process."""
        grid = self.grid
        if self._places_built or grid is None or not grid.ready:
            return
        dist = grid.field(self.field_name, self.safe)
        if dist is None:
            return
        x0, x1, z0, z1 = self.rect
        nx, nz = int((x1 - x0) // CELL) + 1, int((z1 - z0) // CELL) + 1
        offsets = [(fx, fz) for fx in (0.15, 0.4, 0.65, 0.9) for fz in (0.15, 0.4, 0.65, 0.9)]
        out: List[Dict[str, Any]] = []
        for i in range(nx):
            for j in range(nz):
                ground = high = None
                ground_y, high_y = 1e9, HIGH
                for fx, fz in offsets:
                    x, z = x0 + (i + fx) * CELL, z0 + (j + fz) * CELL
                    ix, iz = grid.column(x, z)
                    ids = grid.cols.get(ix * grid.nz + iz)
                    if not ids:
                        continue
                    for node in ids:
                        degree = grid.out_off[node + 1] - grid.out_off[node]
                        if degree < 4 or dist[node] >= 1e29:
                            continue
                        y = grid.py[node]
                        if y < ground_y:
                            ground, ground_y = (node, degree), y
                        if y >= high_y:
                            high, high_y = (node, degree), y
                for found, up in ((ground, False), (high, True)):
                    if found is None or (up and ground is not None and found[0] == ground[0]):
                        continue
                    point = grid.point(found[0])
                    out.append({"p": point, "cell": (i, j), "high": up or point[1] >= HIGH,
                                "open": found[1], "danger": self._danger(point),
                                "near": self.name_of(point, 45.0),
                                "ring": self.ring(point),
                                "angle": math.atan2(point[0] - self.safe[0],
                                                    point[2] - self.safe[2]),
                                "home": _flat(point, self.safe)})
        self.places = out
        self.high_places = [p for p in out if p["high"]]
        self._places_built = True

    def _perch_name(self, point: Sequence[float], landmark: str = "") -> str:
        landmark = landmark or self.name_of(point, 60.0)
        return ("up top at %s" % landmark) if landmark else "the high ground"

    def _highest_near(self, centre: Sequence[float], radius: float) -> Optional[List[float]]:
        grid = self.grid
        best, best_y = None, HIGH
        cx, cz = grid.column(centre[0], centre[2])
        reach = int(radius / grid.spacing) + 1
        for dx in range(-reach, reach + 1):
            for dz in range(-reach, reach + 1):
                ids = grid.cols.get((cx + dx) * grid.nz + (cz + dz))
                if not ids:
                    continue
                for node in ids:
                    y = grid.py[node]
                    if y <= best_y:
                        continue
                    if grid.out_off[node + 1] - grid.out_off[node] < 4:
                        continue          # a ledge, not somewhere to stand
                    point = grid.point(node)
                    if self.reachable(point):
                        best, best_y = point, y
        return best

    # ------------------------------------------------------------ choices
    def spots_with(self, flag: str) -> List[Dict[str, Any]]:
        return [s for s in self.spots if flag in s["flags"]]

    def exposed(self, point: Sequence[float], margin: float = 55.0) -> bool:
        """Somewhere the infected come out right next to."""
        return any(_flat(point, z) < margin for z in self.zspawn)


_INTEL: Dict[Tuple[int, str], AreaIntel] = {}


def intel_for(area: Dict[str, Any], grid) -> AreaIntel:
    key = (id(grid), area["id"])
    found = _INTEL.get(key)
    if found is None or (grid is not None and grid.ready and not found.grounded):
        found = AreaIntel(area, grid)
        _INTEL[key] = found
    return found


# ================================================================ persona
class Profile:
    """What a bot's tags make of it in a survival round, worked out once."""

    __slots__ = ("lone", "size", "cohesion", "people", "roam", "perch", "hunt",
                 "lure", "reach", "nerve", "lead", "lag", "afk", "jumpy",
                 "chatty", "front", "medic", "pace_walk", "climb", "wander",
                 "curious", "prep", "play", "watch", "kite", "flank", "rest",
                 "social")

    def __init__(self, brain, cfg: Dict[str, Any]) -> None:
        tags = set(brain.tags)
        t = brain.t
        rng = brain.rng
        social, support = t("social", 0.5), t("support", 0.2)
        explore, chaos = t("explore", 0.2), t("chaos", 0.08)
        aggression, kindness = t("aggression", 0.5), t("kindness", 0.5)
        skill, objective = brain.skill, brain.objective

        def has(*names: str) -> bool:
            return any(n in tags for n in names)

        def pct(key: str, default: float) -> float:
            value = cfg.get("survival_" + key)
            return float(default if value is None else value) / 100.0

        self.lone = _clamp(pct("solo", 14) * (
            0.35 + (2.6 if has("loner") else 0) + (0.8 if has("shy") else 0)
            + explore * 1.6 + chaos * 1.2 + (1.0 if has("speedrunner") else 0)
            + (0.7 if has("fragger") else 0) - social * 0.5 - support * 1.2
            - (0.5 if has("newbie") else 0) - (0.4 if has("clique") else 0)), 0.01, 0.85)
        lo, hi = cfg.get("survival_squad_size") or [2, SQUAD_MAX]
        hi = max(2, min(SQUAD_MAX, int(hi)))
        lo = max(2, min(hi, int(lo)))
        lean = _clamp(social * 0.7 + support * 0.5 + rng.random() * 0.45
                      - (0.35 if has("clique") else 0) - (0.3 if has("shy") else 0))
        self.size = int(round(lo + (hi - lo) * lean))
        self.cohesion = _clamp(pct("cohesion", 70) * (
            0.65 + support * 0.8 + objective * 0.3 - chaos * 0.9 - explore * 0.4
            + (0.2 if has("clique") else 0) + (0.15 if has("newbie") else 0)), 0.15, 1.0)
        self.people = _clamp(pct("people", 35) * (
            0.3 + social * 0.6 + kindness * 0.2
            + (0.35 if has("social_butterfly") else 0) + (0.15 if has("friendly") else 0)
            + (0.3 if has("newbie") else 0) - (0.5 if has("loner", "shy") else 0)), 0.0, 0.9)
        self.roam = _clamp(pct("roam", 30) * (
            0.4 + explore * 2.4 + chaos * 1.2 + (0.6 if has("kid") else 0)
            + (0.5 if has("roleplayer", "explorer") else 0)), 0.0, 0.95)
        self.perch = _clamp(pct("perch", 30) * (
            0.4 + (1.6 if has("sniper_main") else 0) + (0.8 if has("veteran", "survivor") else 0)
            + skill * 0.6 + t("wp_sniper", 0.2) * 0.8
            - (0.6 if has("shotgun_rusher", "melee_maniac") else 0)), 0.0, 0.95)
        self.hunt = _clamp(pct("hunt", 45) * (
            0.4 + aggression * 1.2 + (0.8 if has("fragger") else 0)
            + (0.6 if has("shotgun_rusher", "melee_maniac") else 0)
            + (0.4 if has("streamer_wannabe", "sweaty") else 0)), 0.0, 0.95)
        self.lure = _clamp(pct("lure", 55) * (
            0.3 + objective * 0.6 + skill * 0.5 + (0.8 if has("survivor") else 0)
            + (0.5 if has("veteran") else 0) + (0.3 if has("chaotic") else 0)), 0.0, 0.98)
        reach = float(cfg.get("survival_revive_reach", 140) or 140)
        self.reach = reach * (0.5 + kindness * 0.7 + support * 0.8
                              + (0.3 if has("wholesome") else 0))
        self.nerve = _clamp(0.35 + skill * 0.4 + aggression * 0.3
                            - (0.2 if has("newbie") else 0) + (0.15 if has("survivor") else 0))
        self.lead = (skill * 0.6 + objective * 0.4 + t("chatty", 0.4) * 0.3
                     + (0.5 if has("survivor", "veteran") else 0)
                     + (0.3 if has("sweaty", "streamer_wannabe") else 0)
                     - (0.5 if has("newbie", "shy") else 0) + rng.random() * 0.2)
        self.lag = 0.3 + (1.0 - skill) * 0.9 + (0.5 if has("newbie") else 0) \
            + t("afk", 0.08) * 2.0
        self.afk = t("afk", 0.08)
        self.jumpy = t("jumpy", 0.2) + chaos * 0.5 + (0.2 if has("kid") else 0)
        self.chatty = t("chatty", 0.4)
        self.front = _clamp(aggression * 0.6 + (0.4 if has("shotgun_rusher", "melee_maniac",
                                                             "fragger") else 0))
        self.medic = _clamp(kindness * 0.5 + support * 0.9 + (0.3 if has("support") else 0))
        self.pace_walk = _clamp(0.25 + (1.0 - aggression) * 0.3 + (0.2 if has("chill") else 0)
                                - (0.3 if has("speedrunner", "kid") else 0))
        self.climb = _clamp(self.jumpy * 0.8 + explore * 0.4)
        # the things people do with a breather, and the ways they fight a wave
        self.wander = _clamp(0.25 + explore * 0.9 + (0.25 if has("chill") else 0)
                             + (0.2 if has("roleplayer", "explorer") else 0) - objective * 0.2)
        self.curious = _clamp(0.2 + explore * 0.8 + chaos * 0.5
                              + (0.35 if has("kid", "newbie") else 0))
        self.prep = _clamp(0.15 + objective * 0.5 + skill * 0.3 - chaos * 0.4
                           + (0.4 if has("survivor", "veteran", "objective_player") else 0))
        self.play = _clamp(chaos * 1.4 + self.jumpy * 0.6
                           + (0.4 if has("kid", "chaotic") else 0) + (0.15 if has("teen") else 0)
                           - (0.2 if has("adult", "veteran") else 0))
        self.watch = _clamp(self.perch * 0.7 + (0.35 if has("sniper_main") else 0)
                            + (0.15 if has("shy", "chill") else 0))
        self.kite = _clamp(skill * 0.6 + aggression * 0.5 - 0.35
                           + (0.35 if has("sweaty", "fragger", "streamer_wannabe",
                                          "competitive") else 0)
                           - (0.3 if has("newbie") else 0))
        self.flank = _clamp(skill * 0.5 + aggression * 0.3 - 0.15
                            + (0.25 if has("veteran", "competitive") else 0))
        self.rest = _clamp(self.afk * 2.0 + (0.35 if has("chill") else 0)
                           + (0.15 if has("adult") else 0))
        self.social = _clamp(social * 0.8 + self.chatty * 0.4
                             + (0.3 if has("social_butterfly", "friendly", "clique") else 0)
                             - (0.3 if has("loner", "shy") else 0))


# The plans that are a string of stops rather than one place to be.
ROUTED = ("explore", "roam", "regroup", "wander", "patrol", "search", "climb", "kite",
          "curious", "prep", "poke")


class Activity:
    """What a squad (or a bot on its own) is up to for the next while."""

    __slots__ = ("kind", "point", "name", "until", "arrived", "route", "data", "linger",
                 "pace", "look")

    def __init__(self, kind: str, point: Optional[List[float]], name: str,
                 until: float, route: Optional[List[Dict[str, Any]]] = None,
                 linger: float = 8.0, pace: str = "mix", look: str = "around") -> None:
        self.kind = kind
        self.point = point
        self.name = name
        self.until = until
        self.arrived = 0.0
        self.route = route or []
        self.data: Dict[str, Any] = {}
        self.linger = linger           # how long a stop lasts before the next
        self.pace = pace               # walk, mix, jog or run
        self.look = look               # around, out, in or edge

    def label(self) -> str:
        where = (" " + self.name) if self.name else ""
        at = (" at " + self.name) if self.name else ""
        return {"hold": "holding%s" % (" " + self.name if self.name else " the line"),
                "perch": "holding%s" % where,
                "hangout": "hanging out%s" % at,
                "explore": "exploring%s" % where,
                "roam": "roaming%s" % ((" towards " + self.name) if self.name else ""),
                "hunt": "hunting the last infected",
                "restock": "restocking",
                "heal": "patching up",
                "regroup": "regrouping",
                "with": "sticking with %s" % (self.name or "a teammate"),
                "wander": "wandering round%s" % where,
                "patrol": "patrolling%s" % where,
                "search": "searching%s" % where,
                "climb": "climbing about%s" % at,
                "lookout": "keeping watch%s" % ((" from " + self.name) if self.name else ""),
                "prep": "stocking up for the wave",
                "rest": "taking a breather%s" % at,
                "mess": "messing about%s" % at,
                "curious": "checking out %s" % (self.name or "a noise"),
                "poke": "poking at %s" % (self.name or "something"),
                "kite": "kiting the horde",
                "flank": "flanking%s" % ((" by " + self.name) if self.name else ""),
                "fallback": "falling back%s" % ((" to " + self.name) if self.name else ""),
                "guard": "guarding %s" % (self.name or "a teammate"),
                }.get(self.kind, self.kind)


class Squad:
    __slots__ = ("sid", "members", "leader", "person", "act", "formed", "spread",
                 "called_at", "waiting_until", "said_perch", "recent", "person_at",
                 "person_still", "home")

    def __init__(self, sid: int, moment: float) -> None:
        self.sid = sid
        self.members: List[Any] = []        # brains
        self.leader = None                  # a brain
        self.person = None                  # a real player the squad sticks with
        self.act: Optional[Activity] = None
        self.formed = moment
        self.spread = 9.0
        self.called_at = 0.0
        self.waiting_until = 0.0
        self.said_perch = False
        self.recent: List[Tuple[str, str]] = []   # (kind, place) of the last plans
        self.person_at: Optional[List[float]] = None
        self.person_still = 0.0
        self.home = 0.0                     # the way it set off from the safe room


class Mind:
    """One bot's survival state, alongside its Brain."""

    __slots__ = ("profile", "squad", "solo", "act", "slot", "slot_until",
                 "next_follow", "follow_at", "decide_at", "stray_since",
                 "noticed", "nerve", "doing", "where", "last_lost", "lone_until",
                 "afk_checked", "last_fidget", "reviving", "wave_seen", "recent",
                 "lines", "ammo_at", "ammo", "cfg_v", "home", "gear_at", "swap_back",
                 "back_until", "back_ready", "rest_at", "jog_at", "jog_run", "glance_at",
                 "falls")

    def __init__(self, profile: Profile) -> None:
        self.profile = profile
        self.squad: Optional[Squad] = None
        self.solo = False
        self.act: Optional[Activity] = None
        self.slot = (math.pi, 6.0)          # angle off the anchor's heading, distance
        self.slot_until = 0.0
        self.next_follow = 0.0
        self.follow_at: Optional[List[float]] = None
        self.decide_at = 0.0
        self.stray_since = 0.0
        self.noticed: Dict[int, float] = {}  # downed pid -> when this bot noticed
        self.nerve = profile.nerve
        self.doing = ""
        self.where = ""
        self.last_lost = 0.0
        self.lone_until = 0.0
        self.afk_checked = 0.0
        self.last_fidget = 0.0
        self.reviving = 0
        self.wave_seen = -1
        self.recent: List[Tuple[str, str]] = []
        self.lines: Dict[str, float] = {}      # line kind -> when this bot last said one
        self.ammo_at = -1e9
        self.ammo = 1.0
        self.cfg_v = None
        self.home = random.uniform(-math.pi, math.pi)  # a lone bot's way out
        self.gear_at = 0.0                      # next look at the guns
        self.swap_back: Optional[Tuple[float, int]] = None
        self.back_until = 0.0                   # backing off a step in a fight
        self.back_ready = 0.0
        self.falls = 0                          # times it fell somewhere no path goes
        self.rest_at = 0.0
        self.jog_at = 0.0                       # walk a bit, jog a bit
        self.jog_run = False
        self.glance_at = 0.0


# ================================================================== plan
class SurvivalPlan:
    """The bots of one Last Light round, as survivors."""

    def __init__(self, runner) -> None:
        self.runner = runner
        self.rng = random.Random()
        self.squads: Dict[int, Squad] = {}
        self.next_sid = 1
        self.tick_at = 0.0
        self.area_id = ""
        self.phase = ""
        self.wave = -1
        self.best_seen = 0
        self.called: Dict[int, float] = {}       # infected id -> when called out
        self.said: Dict[str, float] = {}         # speech event kind -> last time
        self.once: Dict[str, int] = {}           # per-wave events: kind -> wave
        self.swarm_said: Dict[int, float] = {}
        self.omw: Dict[int, float] = {}          # downed pid -> when somebody said "omw"
        self.specials: List[Any] = []
        self.attention: List[List[float]] = []
        self.crowd: Dict[Tuple[int, int], int] = {}     # cell -> people standing in it
        self.heat: Dict[Tuple[int, int], float] = {}    # cell -> when somebody was last there
        self.claims: Dict[Any, List[float]] = {}        # squad sid / -pid -> where it is going
        self.noises: List[Tuple[List[float], float, str]] = []
        self.barrels_seen: Dict[int, List[float]] = {}
        self.lure_seen = 0.0
        self.poked = False
        self.round_seen: Optional[int] = None
        self.still: Dict[int, Tuple[List[float], float]] = {}   # person -> (where, since)
        self.bad: List[List[float]] = []    # spots somebody fell off: never again

    # ------------------------------------------------------------ helpers
    @property
    def inst(self):
        return self.runner.instance

    @property
    def cfg(self) -> Dict[str, Any]:
        return self.runner.cfg

    @property
    def grid(self):
        return self.runner.nav

    def intel(self) -> AreaIntel:
        return intel_for(self.inst.area, self.grid)

    def on(self, key: str, default: bool = True) -> bool:
        value = self.cfg.get("survival_" + key)
        return default if value is None else bool(value)

    def dial(self, key: str, default: float) -> float:
        value = self.cfg.get("survival_" + key)
        return float(default if value is None else value) / 100.0

    def mind(self, brain) -> Mind:
        cfg = self.cfg
        if brain.mind is None:
            brain.mind = Mind(Profile(brain, cfg))
            brain.mind.cfg_v = cfg.get("v")
            brain.mind.home = brain.rng.uniform(-math.pi, math.pi)
        elif brain.mind.cfg_v != cfg.get("v"):
            # the Bots Zone changed a setting: the same persona, new dials
            brain.mind.profile = Profile(brain, cfg)
            brain.mind.cfg_v = cfg.get("v")
        return brain.mind

    def forget(self, brain) -> None:
        mind = brain.mind
        if mind is not None and mind.squad is not None:
            self._leave(brain, mind.squad)
        self.claims.pop(-brain.p.pid, None)

    def reset(self) -> None:
        """A new round: everybody starts again together at the safe room."""
        for brain in self.runner.brains.values():
            if brain.mind is not None:
                brain.mind.squad = None
                brain.mind.solo = False
                brain.mind.act = None
                brain.mind.decide_at = now() + self.rng.uniform(2.0, 9.0)
        self.squads.clear()
        self.called.clear()
        self.once.clear()
        self.claims.clear()
        self.heat.clear()
        self.noises = []
        self.barrels_seen = {}
        self.poked = False
        self.bad = []

    def _field(self, brain) -> bool:
        p = brain.p
        return p.alive and p.extra.get("ll_where") == "field"

    def _standing(self, player) -> bool:
        return player.alive and not player.extra.get("downed") and \
            player.extra.get("ll_where") == "field"

    def _speech(self, kind: str, cooldown: float, **data: Any) -> bool:
        """A moment worth talking about, for the chat relay -- not too often."""
        moment = now()
        if moment - self.said.get(kind, -1e9) < cooldown:
            return False
        self.said[kind] = moment
        self.runner.on_game_event(kind, data)
        return True

    def _once_per_wave(self, kind: str) -> bool:
        wave = int(getattr(self.inst, "wave", 0) or 0)
        if self.once.get(kind) == wave:
            return False
        self.once[kind] = wave
        return True

    def _line(self, brain, key: str, chance: float, delay: float = 0.0,
              text: str = "") -> None:
        """A quick line of the bot's own, in its own typing -- the Quick
        reactions switch (and the in-game chat switch) apply."""
        cfg = self.cfg
        if not cfg.get("messages_quick_reactions", True) or \
                not cfg.get("messages_ingame_chat", True) or not self.runner.humans:
            return
        mind = self.mind(brain)
        profile = mind.profile
        moment = now()
        if moment - mind.lines.get(key, -1e9) < 40.0 or \
                moment - mind.lines.get("", -1e9) < 6.0:
            return                     # said that lately, or said anything just now
        if brain.rng.random() > chance * (0.3 + profile.chatty):
            return
        mind.lines[key] = mind.lines[""] = moment
        line = text or brain.rng.choice(LINES.get(key) or [key])
        line = styled(line, brain.traits, brain.rng)
        if line in brain.said:
            return
        brain.said.append(line)
        self.runner.queue_chat(brain, line, delay + brain.rng.uniform(0.4, 1.8), quick=True)

    def _walk(self, brain, point: Sequence[float], key: str) -> None:
        """Head for ``point``: straight there when it is close, on the same
        level and nothing stands between (no search needed), otherwise by
        the navigation graph."""
        moment = now()
        if key == brain.dest_key and brain.waypoints and moment < brain.repath_at:
            return
        p = brain.p
        grid = self.grid
        if grid is not None and grid.ready and not brain.airborne and \
                _flat(point, p.pos) < 40.0 and abs(point[1] - p.pos[1]) <= 2.0 and \
                grid.clear_line(p.pos, point) and self.inst.line_of_sight(
                    [p.pos[0], p.pos[1] + 1.2, p.pos[2]],
                    [point[0], point[1] + 1.2, point[2]]):
            brain.waypoints = [list(point)]
            brain.dest = list(point)
            brain.dest_key = key
            brain.repath_at = moment + 2.5
            return
        brain.go(list(point), key)

    def _zombies(self):
        return [z for z in self.inst.horde.zombies.values()
                if z.alive and not z.hidden]

    def _near_count(self, pos: Sequence[float], radius: float) -> int:
        return sum(1 for z in self.inst.horde.zombies.values()
                   if z.alive and math.dist(z.pos, pos) < radius)

    def _snap(self, point: Sequence[float], radius: float, rng) -> List[float]:
        """A spot near ``point`` a body can stand on and get back from: nobody
        stops on the exact same patch of ground as the last person."""
        grid = self.grid
        if grid is None or not grid.ready:
            return list(point)
        intel = self.intel()
        for _ in range(4):
            node = grid.random_node(rng, point, radius, tries=8)
            if node < 0:
                break
            spot = grid.point(node)
            if abs(spot[1] - point[1]) <= 3.0 and intel.reachable(spot):
                return spot
        return list(point)

    # ======================================================== coordination
    def tick(self, moment: float) -> None:
        """Once a second: squads, attention, the census, and the moments
        worth a word."""
        if moment - self.tick_at < 1.0:
            return
        self.tick_at = moment
        inst = self.inst
        intel = self.intel()
        intel.build_perches()
        intel.build_places()
        if inst.area_id != self.area_id or getattr(inst, "round_number", 0) != \
                self.round_seen:
            fresh = inst.area_id != self.area_id
            self.area_id = inst.area_id
            self.round_seen = getattr(inst, "round_number", 0)
            if fresh or self.squads:
                self.reset()
        if inst.phase != self.phase or inst.wave != self.wave:
            self._phase_change(self.phase, inst.phase, moment)
            self.phase = inst.phase
            self.wave = inst.wave
        self.specials = [z for z in inst.horde.zombies.values()
                         if z.alive and z.info.get("special") and not z.hidden]
        self._attention()
        self._census(moment)
        self._listen(moment)
        if not self.on("squads") and self.squads:
            # switched off in the Bots Zone: everybody carries on alone
            for squad in list(self.squads.values()):
                for brain in list(squad.members):
                    self._leave(brain, squad)
        self._tidy_squads(moment)
        if self.on("squads"):
            self._join_loose(moment)
            self._merge(moment)
        self._callouts(moment)
        self._moments(moment)

    def _attention(self) -> None:
        """Where somebody real is looking: their own spot in the field, or
        the survivor a dead or waiting player is watching."""
        inst = self.inst
        out = []
        field = [p for p in inst.survivors()]
        for human in self.runner.humans:
            where = human.extra.get("ll_where", "lobby")
            if where == "field" and human.alive:
                out.append(list(human.pos))
                continue
            watching = int(human.extra.get("watching", 0) or 0)
            target = inst.players.get(watching) if watching else None
            if target is None or not target.alive or \
                    target.extra.get("ll_where") != "field":
                if where == "lobby" and not watching:
                    continue             # in the bunker, not watching anyone
                # the spectator camera starts on the lowest id still standing
                alive = sorted((p for p in field if p.alive), key=lambda p: p.pid)
                target = alive[0] if alive else None
            if target is not None:
                out.append(list(target.pos))
        self.attention = out

    def _census(self, moment: float) -> None:
        """Who is standing where, by cell; and when each cell last had
        anybody in it -- so plans go where the others are not, and where
        nobody has been for a while."""
        intel = self.intel()
        crowd: Dict[Tuple[int, int], int] = {}
        for p in self.inst.survivors():
            if p.extra.get("downed"):
                continue
            cell = intel.cell_of(p.pos)
            crowd[cell] = crowd.get(cell, 0) + 1
            self.heat[cell] = moment
        self.crowd = crowd
        for human in self.runner.humans:
            seen = self.still.get(human.pid)
            if seen is None or _flat(seen[0], human.pos) > 8.0:
                self.still[human.pid] = (list(human.pos), moment)
        live = {s.sid for s in self.squads.values()}
        live.update(-b.p.pid for b in self.runner.brains.values())
        for key in [k for k in self.claims if k not in live]:
            self.claims.pop(key, None)

    def _listen(self, moment: float) -> None:
        """The noises worth going to see about: a barrel going up, the bell,
        somebody going down out of sight."""
        inst = self.inst
        alive = {b.ident: list(b.pos) for b in getattr(inst, "barrels", []) if b.alive}
        for ident, pos in self.barrels_seen.items():
            if ident not in alive:
                self.noises.append((pos, moment, "the explosion"))
        self.barrels_seen = alive
        lure = inst.area.get("lure")
        if lure and inst.lure_until > self.lure_seen and moment < inst.lure_until:
            self.lure_seen = inst.lure_until
            self.noises.append((list(lure["p"]), moment, lure.get("name", "the noise")))
        self.noises = [n for n in self.noises if moment - n[1] < 45.0][-6:]

    def _phase_change(self, old: str, new: str, moment: float) -> None:
        inst = self.inst
        if new == "active" and old != "active":
            # a wave is coming: plans for the wave, and most lone wolves come
            # back to somebody for this one
            for squad in self.squads.values():
                squad.act = None
            for brain in self.runner.brains.values():
                mind = brain.mind
                if mind is None:
                    continue
                if mind.solo and self.on("regroup") and \
                        brain.rng.random() > mind.profile.lone * 0.8:
                    mind.solo = False                 # back to the others for this one
                mind.act = None
                mind.decide_at = moment + brain.rng.uniform(0.0, 4.0)
        elif new == "setup" and old == "active":
            # cleared: the breather -- a hop or two, restock, heal, wander, chat
            best_before = self.best_seen
            self.best_seen = max(self.best_seen, int(getattr(inst, "best", 0) or 0))
            if inst.wave > best_before and best_before >= 3:
                self._speech("record", 60.0, n=inst.wave)
            for squad in self.squads.values():
                squad.act = None
            for brain in self.runner.brains.values():
                if brain.mind is None:
                    continue
                brain.mind.act = None
                brain.mind.decide_at = moment + brain.rng.uniform(1.0, 8.0)
                if self._standing(brain.p) and \
                        brain.rng.random() < 0.15 + brain.mind.profile.play * 0.6:
                    brain.jumpy_until = moment + brain.rng.uniform(1.5, 4.0)
                    self._line(brain, "celebrate", 0.3, delay=brain.rng.uniform(0.0, 2.0))
        self.best_seen = max(self.best_seen, int(getattr(inst, "best", 0) or 0))

    # ------------------------------------------------------------- squads
    def _new_squad(self, moment: float) -> Squad:
        squad = Squad(self.next_sid, moment)
        self.next_sid += 1
        squad.home = self._free_heading()
        self.squads[squad.sid] = squad
        return squad

    def _free_heading(self) -> float:
        """A way out of the safe room nobody else has taken: squads fan out."""
        taken = [s.home for s in self.squads.values()]
        best, best_gap = self.rng.uniform(-math.pi, math.pi), -1.0
        for _ in range(10):
            angle = self.rng.uniform(-math.pi, math.pi)
            gap = min((_angle_gap(angle, other) for other in taken), default=math.pi)
            if gap > best_gap:
                best, best_gap = angle, gap
        return best

    def _join(self, brain, squad: Squad) -> None:
        mind = self.mind(brain)
        if mind.squad is squad:
            return
        if mind.squad is not None:
            self._leave(brain, mind.squad)
        squad.members.append(brain)
        mind.squad = squad
        mind.solo = False
        mind.act = None
        mind.slot_until = 0.0
        mind.stray_since = 0.0
        self.claims.pop(-brain.p.pid, None)
        self._elect(squad)

    def _leave(self, brain, squad: Squad) -> None:
        if brain in squad.members:
            squad.members.remove(brain)
        if brain.mind is not None and brain.mind.squad is squad:
            brain.mind.squad = None
        if squad.leader is brain:
            squad.leader = None
            self._elect(squad)
        if not squad.members:
            self.squads.pop(squad.sid, None)
            self.claims.pop(squad.sid, None)

    def _elect(self, squad: Squad) -> None:
        standing = [b for b in squad.members if self._standing(b.p)]
        pool = standing or squad.members
        if not pool:
            squad.leader = None
            return
        if squad.leader in standing:
            return
        squad.leader = max(pool, key=lambda b: self.mind(b).profile.lead)
        squad.act = None

    def _idle(self, person, moment: float) -> float:
        """How boring a real player is as company right now: 0 while they
        get about, more the longer they stand still -- and a lot more
        when they are standing still in the safe room."""
        seen = self.still.get(person.pid)
        if seen is None:
            return 0.0
        still = moment - seen[1]
        if still < 15.0:
            return 0.0
        at_spawn = _flat(person.pos, self.intel().safe) < SAFE_ZONE
        return (3.0 if at_spawn else 1.0) * min(2.0, still / 30.0)

    def _room(self, squad: Squad) -> int:
        """How many more bots a squad takes: three people at most, a real
        player counting as one of them."""
        return self._cap() - len(squad.members) - (1 if squad.person is not None else 0)

    def _tidy_squads(self, moment: float) -> None:
        humans = [h for h in self.runner.humans if self._standing(h)]
        for squad in list(self.squads.values()):
            for brain in list(squad.members):
                if brain.p.pid not in self.runner.brains or \
                        brain.p.extra.get("ll_where") != "field" or not brain.p.alive:
                    self._leave(brain, squad)
            if squad.sid not in self.squads:
                continue
            if squad.person is not None and squad.person not in humans:
                squad.person = None
                squad.act = None
            elif squad.person is not None:
                # tagging along with somebody is a choice, not a leash: the
                # less a bot cares for company the sooner it drifts off, and
                # somebody who has not moved in a while is boring company
                here = feet(squad.person)
                if squad.person_at is None or _flat(here, squad.person_at) > 8.0:
                    squad.person_at = here
                    squad.person_still = moment
                bored = 1.0 + self._idle(squad.person, moment) * 2.5
                for brain in list(squad.members):
                    profile = self.mind(brain).profile
                    if self.rng.random() < (1.0 - profile.people) * 0.012 * bored:
                        self._leave(brain, squad)
                        self.mind(brain).decide_at = moment + brain.rng.uniform(5, 20)
            self._elect(squad)
            active = self.inst.phase == "active"
            # never more than three: the extras split off into a squad of
            # their own (or go their own way) at once
            while squad.sid in self.squads and self._room(squad) < 0:
                spare = sorted((b for b in squad.members if b is not squad.leader),
                               key=lambda b: self._shared(b, squad.leader)
                               if squad.leader is not None else 0)
                over = -self._room(squad)
                split = spare[:over]
                if not split:
                    break
                if len(split) >= 2:
                    other = self._new_squad(moment)
                    for brain in split:
                        self._join(brain, other)
                else:
                    for brain in split:
                        self._leave(brain, squad)
                        self.mind(brain).decide_at = moment
            # now and then somebody wanders off on their own: mostly between
            # waves, mostly the loners and explorers, as the tangent rate says
            tangent = float(self.cfg.get("tangent_per_minute", 9) or 0) / 100.0
            for brain in list(squad.members):
                if len(squad.members) <= 1 or not self._standing(brain.p):
                    continue
                profile = self.mind(brain).profile
                rate = tangent / 60.0 * (0.4 + profile.lone * 5.0) * (0.35 if active else 1.6)
                if self.rng.random() < rate:
                    self._leave(brain, squad)
                    mind = self.mind(brain)
                    mind.solo = True
                    mind.lone_until = moment + brain.rng.uniform(30.0, 90.0)
                    mind.decide_at = mind.lone_until
                    mind.act = None
                    self._went_solo(brain, moment)
            if squad.sid not in self.squads:
                continue
            if len(squad.members) == 1 and squad.person is None and \
                    moment - squad.formed > 20.0:
                # a squad of one is just somebody on their own
                brain = squad.members[0]
                self._leave(brain, squad)
                self.mind(brain).decide_at = moment
                continue
            squad.spread = self._spread(squad)

    def _spread(self, squad: Squad) -> float:
        cohesion = sum(self.mind(b).profile.cohesion for b in squad.members) / \
            max(1, len(squad.members))
        calm = self.inst.phase != "active"
        base = (14.0 if calm else 9.0) - cohesion * 4.0
        if any(z.kind == "tank" for z in self.specials):
            base *= 0.8
        return max(4.5, base + len(squad.members) * 0.8)

    def _join_loose(self, moment: float) -> None:
        """Bots without a squad (and not off on their own) find company --
        two or three at a time -- or go their own way for a while.  Nobody
        stands about the safe room waiting."""
        inst = self.inst
        humans = [h for h in self.runner.humans if self._standing(h)]
        loose = []
        for brain in self.runner.brains.values():
            if not self._field(brain) or brain.p.extra.get("downed"):
                continue
            mind = self.mind(brain)
            if mind.squad is not None or moment < mind.decide_at:
                continue
            if mind.solo and moment < mind.lone_until:
                continue
            loose.append(brain)
        self.rng.shuffle(loose)
        for brain in loose:
            mind = self.mind(brain)
            if mind.squad is not None:
                continue
            profile = mind.profile
            mind.decide_at = moment + brain.rng.uniform(15.0, 45.0)
            # off alone for a while?  Loners and explorers, mostly between waves
            lone = profile.lone * (1.4 if inst.phase != "active" else 0.6)
            if brain.rng.random() < lone:
                was_solo = mind.solo
                mind.solo = True
                mind.lone_until = moment + brain.rng.uniform(40.0, 120.0)
                mind.act = None
                if not was_solo:
                    self._went_solo(brain, moment)
                continue
            mind.solo = False
            best, best_score = None, -1e9
            for squad in self.squads.values():
                if self._room(squad) <= 0:
                    continue                    # full: people do not pile into one group
                anchor = self._anchor(squad)
                if anchor is None:
                    continue
                d = _flat(anchor, brain.p.pos)
                if d > 220:
                    continue
                size = len(squad.members) + (1 if squad.person is not None else 0)
                fit = 1.0 - abs(size + 1 - profile.size) * 0.35
                shared = sum(self._shared(brain, other) for other in squad.members) / \
                    max(1, len(squad.members))
                score = fit + shared * 0.25 - d / 120.0 + brain.rng.uniform(-0.3, 0.3)
                if squad.person is not None:
                    score += profile.people * 1.2 - self._idle(squad.person, moment)
                if score > best_score:
                    best, best_score = squad, score
            # a real player without a squad: tag along with them
            lively = [h for h in humans if self._idle(h, moment) <= 0.0]
            if lively and brain.rng.random() < profile.people:
                person = min(lively, key=lambda h: _flat(h.pos, brain.p.pos))
                if _flat(person.pos, brain.p.pos) < 260 and not any(
                        s.person is person for s in self.squads.values()):
                    squad = self._new_squad(moment)
                    squad.person = person
                    self._join(brain, squad)
                    self._line(brain, "omw", 0.25, text=brain.rng.choice(
                        ["im with you %s" % person.username.lower(), "following you",
                         "ill stick with you", "wait for me"]))
                    continue
            if best is not None and best_score > -0.8:
                self._join(brain, best)
                continue
            # start one with whoever else is about and free (a pair, or a
            # three if the next one along wants company too)
            partners = [o for o in loose if o is not brain and self.mind(o).squad is None
                        and not self.mind(o).solo and _flat(o.p.pos, brain.p.pos) < 90]
            if partners:
                squad = self._new_squad(moment)
                self._join(brain, squad)
                want = max(2, min(self._cap(), profile.size))
                for other in partners[:want - 1]:
                    self._join(other, squad)
                    self.mind(other).decide_at = moment + other.rng.uniform(15.0, 45.0)
            elif best is not None:
                self._join(brain, best)
            else:
                # nobody about: off on its own for a bit, and back for
                # company later
                mind.solo = True
                mind.lone_until = moment + brain.rng.uniform(20.0, 50.0)
                mind.act = None

    def _cap(self) -> int:
        _lo, hi = self.cfg.get("survival_squad_size") or [2, SQUAD_MAX]
        return max(2, min(SQUAD_MAX, int(hi)))

    def _shared(self, a, b) -> int:
        return len(set(a.tags) & set(b.tags))

    def _merge(self, moment: float) -> None:
        """Two small squads that end up together at a big moment become one
        -- but never past three."""
        squads = list(self.squads.values())
        if len(squads) < 2:
            return
        busy = self.inst.phase == "active"
        for i, a in enumerate(squads):
            for b in squads[i + 1:]:
                if a.sid not in self.squads or b.sid not in self.squads:
                    continue
                if a.person is not None and b.person is not None:
                    continue
                pa, pb = self._anchor(a), self._anchor(b)
                if pa is None or pb is None or _flat(pa, pb) > 22:
                    continue
                keep, drop = (a, b) if a.person is not None or \
                    len(a.members) >= len(b.members) else (b, a)
                if len(drop.members) > self._room(keep) or \
                        self.rng.random() > (0.35 if busy else 0.1):
                    continue
                for brain in list(drop.members):
                    self._join(brain, keep)

    def _anchor(self, squad: Squad) -> Optional[List[float]]:
        if squad.person is not None:
            return feet(squad.person)
        if squad.act is not None and squad.act.kind in ("hold", "perch", "hangout", "lookout",
                                                         "rest", "flank", "fallback") \
                and squad.act.arrived and squad.act.point is not None:
            return list(squad.act.point)
        if squad.leader is not None:
            return feet(squad.leader.p)
        return None

    def _went_solo(self, brain, moment: float) -> None:
        mind = self.mind(brain)
        intel = self.intel()
        act = self._plan(brain, mind, brain.rng.choice(["explore", "wander", "wander", "search"])
                         if self.inst.phase != "active" else "roam",
                         moment, None, self.inst.phase == "active", mind.recent)
        mind.act = act
        self._line(brain, "solo", 0.35)
        self._speech("split", 75.0, by=brain.p.username,
                     what=act.name or intel.describe(brain.p.pos))

    def _rally(self, moment: float, why: str) -> None:
        """Things are going wrong (a Tank, half the team down): somebody
        shouts "stack up" and the squads spread wide close in -- near each
        other, each still its own squad, not one heap."""
        squads = [s for s in self.squads.values() if s.leader is not None]
        anchors = [(s, self._anchor(s)) for s in squads]
        anchors = [(s, a) for s, a in anchors if a is not None]
        if len(anchors) < 2:
            return
        cx = sum(a[0] for _s, a in anchors) / len(anchors)
        cz = sum(a[2] for _s, a in anchors) / len(anchors)
        far = [(s, a) for s, a in anchors if math.hypot(a[0] - cx, a[2] - cz) > 90]
        if not far:
            return
        caller = max((s.leader for s, _a in anchors), key=lambda b: self.mind(b).profile.lead)
        self._line(caller, "regroup", 0.5)
        intel = self.intel()
        place = intel.describe(caller.p.pos) or "the safe room"
        self._speech("regroup", 60.0, by=caller.p.username, what=place)
        here = feet(caller.p)
        for squad, anchor in far:
            if squad is caller.mind.squad or squad.person is not None:
                continue
            if self.rng.random() < 0.6:
                # come in to somewhere near, on its own side
                angle = _bearing(here, anchor)
                spot = [here[0] + math.sin(angle) * 26.0, here[1], here[2] + math.cos(angle) * 26.0]
                spot = self._snap(spot, 10.0, self.rng)
                squad.act = Activity("regroup", spot, place, moment + 25.0, pace="run")

    # ------------------------------------------------------------ callouts
    def _callouts(self, moment: float) -> None:
        """Specials get called out by whoever sees them first."""
        for key in [k for k, at in self.called.items() if moment - at > 120]:
            self.called.pop(key, None)
        if not self.specials and not any(z.kind == "tank" for z in
                                         self.inst.horde.zombies.values()):
            return
        intel = self.intel()
        targets = self.specials + [z for z in self.inst.horde.zombies.values()
                                   if z.kind == "tank" and z.alive]
        for z in targets:
            if z.pid in self.called:
                continue
            spotter = None
            for brain in self.runner.brains.values():
                if not self._standing(brain.p):
                    continue
                d = math.dist(brain.p.pos, z.pos)
                if d > 95:
                    continue
                if d > 25 and not brain._sees(z):
                    continue
                spotter = brain
                break
            if spotter is None:
                continue
            self.called[z.pid] = moment
            where = intel.name_of(z.pos, 60.0)
            if self.on("callouts") and z.kind in CALLOUTS:
                text = spotter.rng.choice(CALLOUTS[z.kind])
                if where and spotter.rng.random() < 0.55:
                    text += " " + spotter.rng.choice(["by", "at", "near"]) + " " + \
                        where.replace("the ", "", 1)
                self._line(spotter, "callout", 0.85 if z.kind == "tank" else 0.6, text=text)
            if z.kind != "tank":
                self._speech("special", 25.0, by=spotter.p.username,
                             what=z.info.get("name", z.kind), where=where)
            elif self.on("regroup"):
                self._rally(moment, "tank")

    # ------------------------------------------------------------- moments
    def _moments(self, moment: float) -> None:
        inst = self.inst
        if inst.phase != "active":
            return
        survivors = inst.survivors()
        standing = [p for p in survivors if not p.extra.get("downed")]
        intel = self.intel()
        # swarmed: eight or more on one person
        for p in standing:
            if moment - self.swarm_said.get(p.pid, 0.0) < 45:
                continue
            if self._near_count(p.pos, 12.0) >= 8:
                self.swarm_said[p.pid] = moment
                self._speech("swarmed", 30.0, by=p.username, what=intel.name_of(p.pos))
                break
        # half the team down: pull in
        if survivors and len(standing) * 2 <= len(survivors) and len(survivors) >= 4 and \
                self.on("regroup") and self._once_per_wave("rally"):
            self._rally(moment, "downed")
        # the last one standing
        if len(standing) == 1 and len(survivors) >= 2 and self._once_per_wave("last_stand"):
            self._speech("last_stand", 20.0, by=standing[0].username,
                         what=intel.name_of(standing[0].pos))
            if self.on("regroup"):
                for brain in self.runner.brains.values():
                    if brain.p is standing[0] and brain.mind is not None:
                        brain.mind.nerve = max(0.0, brain.mind.nerve - 0.2)
        # the last few of a wave
        left = inst.wave_left()
        if 0 < left <= 3 and self._once_per_wave("few_left"):
            self._speech("few_left", 30.0, n=left)

    # ================================================================ act
    def act(self, brain) -> None:
        """One think's worth of survival for one bot."""
        inst = self.inst
        p = brain.p
        moment = now()
        mind = self.mind(brain)
        where = p.extra.get("ll_where", "lobby")
        if where != "field" or not p.alive:
            p.extra.pop("using", None)
            if where == "lobby" and p.alive:
                self._lobby(brain, moment)
            return
        if mind.wave_seen != inst.wave:
            mind.wave_seen = inst.wave
            mind.nerve = mind.profile.nerve
        if brain.rescues != mind.falls:
            # it fell off whatever it was heading for: a ledge too narrow to
            # stand on.  Nobody goes up there again this round.
            mind.falls = brain.rescues
            act = mind.squad.act if mind.squad is not None else mind.act
            if act is not None and act.point is not None:
                self.bad.append(list(act.point))
                del self.bad[:-24]
                if mind.squad is not None:
                    mind.squad.act = None
                mind.act = None
        self._gear(brain, mind, moment)
        if self._emergency(brain, mind, moment):
            brain.afk_until = 0.0
            return
        if self._needs(brain, mind, moment):
            brain.afk_until = 0.0
            return
        if self._mood(brain, mind, moment):
            return
        squad = mind.squad
        if squad is not None and self.on("squads"):
            if squad.leader is brain and squad.person is None:
                self._lead(brain, mind, squad, moment)
            else:
                self._follow(brain, mind, squad, moment)
        else:
            self._alone(brain, mind, moment)

    def _gear(self, brain, mind: Mind, moment: float) -> None:
        """A look at the guns between waves: out comes another one, and a
        moment later back to the usual -- the way people fidget."""
        p = brain.p
        if mind.swap_back is not None:
            if moment >= mind.swap_back[0] or brain.target is not None:
                slot = mind.swap_back[1]
                mind.swap_back = None
                if p.weapon(slot) and p.slot != slot:
                    self.inst.handle_slot(p, {"i": slot})
            return
        if self.inst.phase == "active" or brain.target is not None or moment < mind.gear_at:
            return
        mind.gear_at = moment + brain.rng.uniform(25.0, 80.0)
        if brain.rng.random() > 0.35 + mind.profile.play * 0.4:
            return
        slots = [s for s in range(5) if s != p.slot and p.weapon(s)]
        if not slots:
            return
        mind.swap_back = (moment + brain.rng.uniform(1.0, 3.5), p.slot)
        self.inst.handle_slot(p, {"i": brain.rng.choice(slots)})

    # -------------------------------------------------------- emergencies
    def _emergency(self, brain, mind: Mind, moment: float) -> bool:
        inst = self.inst
        p = brain.p
        rng = brain.rng
        profile = mind.profile
        if p.extra.get("pinned_by"):
            # mash the key: quicker for the steadier hands
            if rng.random() < 0.45 + brain.skill * 0.4:
                inst.use(p)
            if rng.random() < 0.08:
                brain.say("pinned", chance=0.6)
            return True
        if p.extra.get("downed"):
            p.extra.pop("using", None)
            if not p.extra.get("said_down"):
                p.extra["said_down"] = True
                brain.say("downed", chance=0.7)
            # crawl towards help, unless somebody is already on the way
            if not p.extra.get("revive"):
                helpers = [m for m in inst.survivors() if m is not p and
                           not m.extra.get("downed")]
                if helpers:
                    helper = min(helpers, key=lambda m: math.dist(m.pos, p.pos))
                    if 6.0 < math.dist(helper.pos, p.pos) < 60.0:
                        brain.speed = RUN
                        brain.go(feet(helper), "crawl%d" % helper.pid)
                        return True
            brain.waypoints = []
            return True
        p.extra.pop("said_down", None)
        team = [s for s in inst.survivors() if s is not p]
        horde = inst.horde.zombies
        # standing in acid: out of it before anything else
        for pool in inst.horde.pools:
            px, py, pz = pool["p"]
            dx, dz = p.pos[0] - px, p.pos[2] - pz
            flat = math.hypot(dx, dz)
            if flat < pool["r"] + 1.5 and abs(p.pos[1] - py) < 3.0:
                flat = flat or 1.0
                out = pool["r"] + 5.0
                spot = [px + dx / flat * out, p.pos[1], pz + dz / flat * out]
                if self.grid is not None and self.grid.ready:
                    node = self.grid.nearest(spot, 2)
                    if node >= 0:
                        spot = self.grid.point(node)
                brain.speed = RUN
                brain.go(spot, "acid%.0f" % px, precise=True)
                p.extra.pop("using", None)
                return True
        # somebody pinned: get over there, the pinner is the target
        for mate in team:
            pinner = horde.get(mate.extra.get("pinned_by", 0))
            if pinner is None:
                continue
            reach = profile.reach * (0.9 if mate.brain is not None else 1.2)
            if math.dist(mate.pos, p.pos) > reach:
                continue
            brain.target = pinner.pid
            brain.speed = RUN
            if math.dist(mate.pos, p.pos) > 7:
                brain.go(feet(mate), "save%d" % mate.pid)
            else:
                brain.waypoints = []
            p.extra.pop("using", None)
            return True
        # a Tank close by: back off towards the squad and keep shooting
        tank = min((z for z in horde.values() if z.kind == "tank" and z.alive),
                   key=lambda z: math.dist(z.pos, p.pos), default=None)
        if tank is not None and math.dist(tank.pos, p.pos) < 20 and self.grid and \
                self.grid.ready:
            brain.target = tank.pid
            dx, dz = p.pos[0] - tank.pos[0], p.pos[2] - tank.pos[2]
            flat = math.hypot(dx, dz) or 1.0
            away = [p.pos[0] + dx / flat * 22.0, p.pos[1], p.pos[2] + dz / flat * 22.0]
            squad = mind.squad
            anchor = self._anchor(squad) if squad is not None else None
            if anchor is not None and math.dist(anchor, tank.pos) > 25:
                away = [(away[0] + anchor[0]) / 2.0, p.pos[1], (away[2] + anchor[2]) / 2.0]
            node = self.grid.nearest(away, 3)
            if node >= 0:
                brain.speed = RUN
                brain.go(self.grid.point(node), "kite%d" % node)
                return True
        # somebody down: pick them up -- or cover whoever is
        if self._revive(brain, mind, team, moment):
            return True
        p.extra.pop("using", None)
        # covered in bile: get to the others, they are about to be needed
        if moment < p.extra.get("biled_until", 0) and mind.squad is not None:
            anchor = self._anchor(mind.squad)
            if anchor is not None and _flat(anchor, p.pos) > 8:
                brain.speed = RUN
                brain.go(anchor, "bile")
                return True
        # one right on top of it: a step or two back while shooting, the
        # way a player backs off without taking their eyes off it
        if moment < mind.back_until:
            return True
        if self._back_off(brain, mind, moment):
            return True
        # swamped and losing its nerve: back off to the others or the high ground
        close = self._near_count(p.pos, 9.0)
        if close >= 4:
            mind.nerve = max(0.0, mind.nerve - 0.04 * close)
        else:
            mind.nerve = min(profile.nerve, mind.nerve + 0.02)
        if close >= 5 and mind.nerve < 0.35 and self.grid is not None and self.grid.ready:
            retreat = None
            if mind.squad is not None:
                anchor = self._anchor(mind.squad)
                if anchor is not None and _flat(anchor, p.pos) > 10:
                    retreat = anchor
            if retreat is None:
                retreat = self._away_from_horde(p.pos, 18.0)
            if retreat is not None:
                if brain.rng.random() < 0.15:
                    self._line(brain, "backoff", 0.4)
                brain.speed = RUN
                brain.go(retreat, "retreat%.0f%.0f" % (retreat[0], retreat[2]))
                # a squad whose spot is overrun moves on from it
                squad = mind.squad
                if squad is not None and squad.act is not None and squad.leader is brain and \
                        squad.act.kind in ("hold", "perch", "lookout", "flank") and \
                        self._near_count(squad.act.point or p.pos, 14.0) >= 6:
                    squad.act = self._plan(brain, mind, "fallback", moment, squad, True,
                                           squad.recent)
                return True
        return False

    def _back_off(self, brain, mind: Mind, moment: float) -> bool:
        p = brain.p
        if brain.target is None or self.grid is None or not self.grid.ready or \
                brain.airborne or moment < mind.back_ready:
            return False
        tgt = self.inst.entity(brain.target)
        if tgt is None or not getattr(tgt, "alive", False):
            return False
        d = _flat(tgt.pos, p.pos)
        stats = p.weapon_stats()
        if d > 6.5 or stats.get("kind") == "melee" or mind.profile.front > 0.8:
            return False
        if brain.rng.random() > 0.35 + brain.skill * 0.4:
            return False
        dx, dz = p.pos[0] - tgt.pos[0], p.pos[2] - tgt.pos[2]
        flat = math.hypot(dx, dz) or 1.0
        back = [p.pos[0] + dx / flat * 6.0, p.pos[1], p.pos[2] + dz / flat * 6.0]
        if not brain._walkable(back[0], back[1], back[2]):
            return False
        brain.speed = RUN * 0.8
        brain.waypoints = [back]
        brain.dest_key = ""
        mind.back_until = moment + brain.rng.uniform(0.5, 1.0)
        mind.back_ready = mind.back_until + brain.rng.uniform(1.5, 4.0)
        return True

    def _away_from_horde(self, pos: Sequence[float], dist: float) -> Optional[List[float]]:
        near = [z for z in self.inst.horde.zombies.values()
                if z.alive and math.dist(z.pos, pos) < 25]
        if not near:
            return None
        cx = sum(z.pos[0] for z in near) / len(near)
        cz = sum(z.pos[2] for z in near) / len(near)
        dx, dz = pos[0] - cx, pos[2] - cz
        flat = math.hypot(dx, dz) or 1.0
        spot = [pos[0] + dx / flat * dist, pos[1], pos[2] + dz / flat * dist]
        node = self.grid.nearest(spot, 3)
        return self.grid.point(node) if node >= 0 else None

    def _revive(self, brain, mind: Mind, team, moment: float) -> bool:
        inst = self.inst
        p = brain.p
        profile = mind.profile
        mind.reviving = 0
        downed = [m for m in team if m.extra.get("downed")]
        if not downed:
            mind.noticed.clear()
            return False
        horde = inst.horde.zombies

        def weight(mate) -> float:
            d = math.dist(mate.pos, p.pos)
            if mate.brain is None:
                d *= 0.6                      # a real player first
            elif mind.squad is not None and mate.brain.mind is not None and \
                    mate.brain.mind.squad is mind.squad:
                d *= 0.8                      # then the squad
            return d
        mate = min(downed, key=weight)
        d = math.dist(mate.pos, p.pos)
        if d > profile.reach:
            return False
        # a beat to notice and decide, as a person needs
        seen = mind.noticed.setdefault(mate.pid, moment)
        if moment - seen < brain.reaction * (1.0 + (1.0 - profile.medic)):
            return False
        crowded = sum(1 for z in horde.values() if math.dist(z.pos, p.pos) < 7) >= \
            (2 + int(profile.medic * 3)) or any(
            z.kind == "tank" and math.dist(z.pos, mate.pos) < 22 for z in horde.values())
        reviver = None
        for other in team:
            current = other.extra.get("revive")
            if not other.extra.get("downed") and current and current[0] == mate.pid:
                reviver = other
                break
        if reviver is None and crowded and brain.rng.random() > profile.medic * 0.5:
            return False
        if reviver is not None and reviver is not p:
            # somebody is on it: stand over them facing out, shooting
            covers = sum(1 for o in team if o.brain is not None and o.brain.mind is not None
                         and o.brain.mind.reviving == mate.pid and o is not reviver)
            if covers >= 2 or d > 60:
                return False
            mind.reviving = mate.pid
            p.extra.pop("using", None)
            if d > 9:
                brain.speed = RUN
                self._walk(brain, feet(mate), "cover%d" % mate.pid)
            else:
                brain.waypoints = []
                away = math.atan2(p.pos[0] - mate.pos[0], p.pos[2] - mate.pos[2])
                brain.look_yaw = away + brain.rng.uniform(-0.6, 0.6)
                if brain.rng.random() < 0.02:
                    self._line(brain, "cover", 0.3)
            return True
        mind.reviving = mate.pid
        if d > 4.5:
            p.extra.pop("using", None)
            brain.speed = RUN
            if d > 25 and not p.extra.get("said_omw") and \
                    moment - self.omw.get(mate.pid, -1e9) > 12.0:
                # one "omw" per person down, not a chorus of them
                p.extra["said_omw"] = True
                self.omw[mate.pid] = moment
                self._line(brain, "omw", 0.4)
            self._walk(brain, feet(mate), "revive%d" % mate.pid)
        else:
            brain.waypoints = []
            p.extra["using"] = True
            p.extra.pop("said_omw", None)
        return True

    # -------------------------------------------------------------- needs
    def _needs(self, brain, mind: Mind, moment: float) -> bool:
        """Ammunition and patching up, when it is time."""
        inst = self.inst
        p = brain.p
        area = inst.area
        if moment - mind.ammo_at > 1.0:
            mind.ammo_at = moment
            mind.ammo = self._ammo(p)
        if mind.ammo < 0.62:
            calm = inst.phase != "active" or self._near_count(p.pos, 25.0) == 0
            crate = min((math.dist(pt["p"], p.pos) for pt in area["points"].get("ammo", [])),
                        default=1e9)
            low = 0.6 if calm and inst.phase != "active" else 0.25
            if crate < 45:
                low = max(low, 0.5)            # one is right here: top up
            if mind.ammo < low:
                if inst.phase == "active" and mind.ammo < 0.15:
                    if self._speech("ammo_low", 60.0, by=p.username,
                                    what=self.intel().name_of(p.pos)):
                        self._line(brain, "ammo", 0.5)
                if self._fetch(brain, area["points"].get("ammo", []), 240, "ammo"):
                    mind.doing = "getting ammo"
                    return True
        hurt = p.health < (55 if inst.phase != "active" else 40)
        if hurt or (p.extra.get("downs", 0) >= 1 and inst.phase != "active"):
            cabinets = [pt for i, pt in enumerate(area["points"].get("med", []))
                        if i < len(inst.med_charges) and inst.med_charges[i] > 0]
            if self._fetch(brain, cabinets, 180, "med"):
                if p.health < 35 and brain.rng.random() < 0.3:
                    self._line(brain, "low", 0.3)
                mind.doing = "patching up"
                return True
        # the lure: when the team is being swamped and it is to hand
        lure = area.get("lure")
        if lure and inst.phase == "active" and moment >= inst.lure_ready:
            d = math.dist(lure["p"], p.pos)
            swamped = self._near_count(p.pos, 50.0) >= 14 or any(
                self._near_count(m.pos, 14.0) >= 8 for m in inst.survivors()
                if m.extra.get("downed"))
            impulse = mind.profile.lure * 0.04 if brain.t("chaos", 0.08) > 0.3 else 0.0
            if d < 120 and ((swamped and brain.rng.random() < mind.profile.lure * 0.5)
                            or brain.rng.random() < impulse):
                if d < 6:
                    inst.use(p)
                    self._line(brain, "lure", 0.4)
                else:
                    brain.speed = RUN
                    brain.go(lure["p"], "lure", precise=True)
                mind.doing = "going for the %s" % lure.get("name", "lure")
                return True
        return False

    @staticmethod
    def _ammo(p) -> float:
        """How full this bot's guns are, 0..1 (1 for no guns at all)."""
        have = full = 0
        for slot in range(5):
            if not p.weapon(slot):
                continue
            stats = p.weapon_stats(slot)
            if stats.get("kind") not in ("hitscan", "projectile"):
                continue
            have += p.ammo[slot] + p.reserve[slot]
            full += int(stats.get("mag", 0) or 0) + int(stats.get("reserve", 0) or 0)
        return have / float(full) if full else 1.0

    def _fetch(self, brain, points, reach: float, key: str) -> bool:
        p = brain.p
        best, best_d = None, reach
        for point in points:
            d = math.dist(point["p"], p.pos)
            if d < best_d:
                best, best_d = point, d
        if best is None:
            return False
        if best_d < 5.5:
            brain.waypoints = []
            self.inst.use(p)
            if brain.mind is not None:
                brain.mind.ammo_at = -1e9
            return False
        brain.speed = RUN
        brain.go(best["p"], "%s%.0f" % (key, best["p"][0]), precise=True)
        return True

    # --------------------------------------------------------------- mood
    def _mood(self, brain, mind: Mind, moment: float) -> bool:
        """Between waves people stand about, hop on things and go AFK for a
        bit; the persona and the Bots Zone's own rates decide how much."""
        inst = self.inst
        if inst.phase == "active":
            return False
        if moment < brain.afk_until:
            if self._near_count(brain.p.pos, 45.0):
                brain.afk_until = 0.0        # something is coming: back to it
                return False
            return True
        if moment - mind.afk_checked < 5.0:
            return False
        mind.afk_checked = moment
        cfg = self.cfg
        floor = float(cfg.get("anything_floor", 3) or 0) / 100.0
        afk_rate = float(cfg.get("afk_per_minute", 3) or 0) / 100.0
        tangent = float(cfg.get("tangent_per_minute", 9) or 0) / 100.0
        # five-second rolls, so a per-minute rate is spread over twelve
        afk = max(floor * 0.3, afk_rate * (0.5 + mind.profile.afk * 6)) / 12.0
        left = inst.phase_until - moment
        if left > 8 and brain.rng.random() < afk:
            brain.afk_until = moment + min(left - 4, brain.rng.uniform(5, 18))
            brain.waypoints = []
            if brain.rng.random() < 0.3:
                self._line(brain, "rest", 0.3)
            return True
        jumpy = max(floor * 0.3, tangent * mind.profile.jumpy * 1.5) / 12.0
        if brain.rng.random() < jumpy:
            brain.jumpy_until = moment + brain.rng.uniform(2, 7)
        return False

    # ------------------------------------------------------------ squads
    def _lead(self, brain, mind: Mind, squad: Squad, moment: float) -> None:
        act = squad.act
        if act is None or moment >= act.until or self._act_done(act, brain):
            act = squad.act = self._choose(brain, mind, squad.members, moment, squad)
            self.claims[squad.sid] = list(act.point) if act.point is not None else \
                list(brain.p.pos)
        mind.doing = act.label()
        mind.where = act.name
        if act.kind == "regroup":
            if act.point is not None and _flat(act.point, brain.p.pos) < 12:
                squad.act = None
                return
        # the ones behind: wait for them now and then, as a leader does
        if squad.members and act.kind in ROUTED and act.kind != "kite" and not act.arrived:
            lag = max((_flat(m.p.pos, brain.p.pos) for m in squad.members if m is not brain
                       and self._standing(m.p)), default=0.0)
            if lag > squad.spread * 3.5 and moment > squad.waiting_until:
                squad.waiting_until = moment + brain.rng.uniform(2.0, 4.5)
            if moment < squad.waiting_until:
                brain.waypoints = []
                self._look_round(brain, moment)
                return
        self._pursue(brain, mind, act, moment, squad)

    def _follow(self, brain, mind: Mind, squad: Squad, moment: float) -> None:
        """Keep a loose place beside or behind the squad, a beat behind it."""
        anchor_player = squad.person or (squad.leader.p if squad.leader is not None else None)
        if anchor_player is None or anchor_player is brain.p:
            self._alone(brain, mind, moment)
            return
        act = squad.act
        settled = act is not None and act.arrived and act.point is not None and \
            act.kind in ("hold", "perch", "hangout", "lookout", "rest", "flank", "fallback")
        circle = settled and act.kind == "hangout"
        centre = list(act.point) if settled else feet(anchor_player)
        profile = mind.profile
        spread = squad.spread
        if moment >= mind.slot_until:
            index = squad.members.index(brain) if brain in squad.members else 0
            if circle:
                # a ring, everybody facing in: the squad stopped for a chat
                base = 2 * math.pi * (index + 1) / (len(squad.members) + 1)
                mind.slot = (base + brain.rng.uniform(-0.35, 0.35), brain.rng.uniform(2.6, 4.2))
            elif settled:
                # each takes a side of the spot, facing out
                base = 2 * math.pi * index / max(1, len(squad.members))
                close = 0.25 if act.kind == "rest" else 0.35
                mind.slot = (base + brain.rng.uniform(-0.5, 0.5),
                             spread * brain.rng.uniform(close, 0.8))
            else:
                side = 1.0 if brain.rng.random() < 0.5 else -1.0
                angle = math.pi + side * brain.rng.uniform(0.35, 1.5)
                if profile.front > 0.6 and brain.rng.random() < 0.4:
                    angle = side * brain.rng.uniform(0.2, 0.9)   # out in front
                mind.slot = (angle, spread * brain.rng.uniform(0.4, 1.0))
            mind.slot_until = moment + brain.rng.uniform(8.0, 22.0)
        angle, dist = mind.slot
        heading = 0.0 if settled else self._heading(anchor_player)
        a = heading + angle
        target = [centre[0] + math.sin(a) * dist, centre[1], centre[2] + math.cos(a) * dist]
        mind.doing = (act.label() if act is not None else "with the squad") \
            if squad.person is None else "sticking with %s" % anchor_player.username
        mind.where = act.name if act is not None else ""
        if squad.person is not None and act is None:
            mind.doing = "sticking with %s" % anchor_player.username
        d_me = _flat(brain.p.pos, target)
        d_anchor = _flat(brain.p.pos, centre)
        # strayed far from the squad: catch up, or give up and go another way
        if d_anchor > spread * 6:
            if not mind.stray_since:
                mind.stray_since = moment
            elif moment - mind.stray_since > 20 and brain.rng.random() < 0.3:
                self._leave(brain, squad)
                mind.decide_at = moment
                if moment - mind.last_lost > 90:
                    mind.last_lost = moment
                    self._line(brain, "lost", 0.4)
                return
        else:
            mind.stray_since = 0.0
        # react to the squad moving after a beat, not the same instant
        moved = mind.follow_at is None or _flat(mind.follow_at, target) > 3.5
        if d_me > 2.5 and (moved or not brain.waypoints) and moment >= mind.next_follow:
            mind.next_follow = moment + profile.lag * brain.rng.uniform(0.6, 1.6)
            mind.follow_at = target
            calm = self.inst.phase != "active"
            if d_me > spread * 1.6 or not calm or (act is not None and act.pace == "run"):
                brain.speed = RUN
            else:
                brain.speed = WALK if brain.rng.random() < 0.6 + profile.pace_walk * 0.4 \
                    else RUN
            node = self.grid.nearest(target, 2) if self.grid is not None and \
                self.grid.ready else -1
            point = self.grid.point(node) if node >= 0 else target
            self._walk(brain, point, "sq%d:%d:%d" % (squad.sid, int(point[0] // 4),
                                                     int(point[2] // 4)))
            return
        if d_me <= 2.5:
            brain.waypoints = []
            if circle:
                self._face(brain, moment, centre, 0.5, toward=True)
            elif settled:
                if act.kind == "rest":
                    self._rest(brain, mind, moment)
                else:
                    brain.look_yaw = angle + brain.rng.uniform(-0.5, 0.5)
            else:
                self._look_round(brain, moment, toward=feet(anchor_player))
            if act is not None and act.kind == "mess" and act.arrived:
                brain.jumpy_until = moment + 1.0

    def _heading(self, player) -> float:
        vel = getattr(player, "vel", None) or [0.0, 0.0, 0.0]
        if math.hypot(vel[0], vel[2]) > 2.0:
            return math.atan2(vel[0], vel[2])
        return float(getattr(player, "yaw", 0.0) or 0.0)

    def _alone(self, brain, mind: Mind, moment: float) -> None:
        act = mind.act
        if act is None or moment >= act.until or self._act_done(act, brain):
            act = mind.act = self._choose(brain, mind, [brain], moment, None)
            self.claims[-brain.p.pid] = list(act.point) if act.point is not None else \
                list(brain.p.pos)
        mind.doing = act.label()
        mind.where = act.name
        self._pursue(brain, mind, act, moment, None)

    def _act_done(self, act: Activity, brain) -> bool:
        if act.kind in ROUTED and act.arrived and now() - act.arrived > act.linger:
            if act.route:
                nxt = act.route.pop(0)
                act.point, act.name = list(nxt["p"]), nxt.get("name", act.name)
                act.linger = nxt.get("linger", act.linger)
                act.arrived = 0.0
                act.data.pop("via", None)
                act.data.pop("meandered", None)
                return False
            return True
        if act.kind == "hunt" and not self._zombies():
            return True
        if act.kind == "guard":
            pid = act.data.get("pid", 0)
            person = self.inst.players.get(pid)
            return person is None or not self._standing(person)
        return False

    # --------------------------------------------------- choosing a plan
    def _choose(self, brain, mind: Mind, members, moment: float,
                squad: Optional[Squad]) -> Activity:
        """What this squad (or this lone bot) does next, by everybody's
        persona and how the round stands."""
        inst = self.inst
        intel = self.intel()
        rng = brain.rng
        profs = [self.mind(m).profile for m in members]
        avg = lambda key: sum(getattr(pr, key) for pr in profs) / max(1, len(profs))  # noqa: E731
        solo = squad is None
        active = inst.phase == "active"
        cfg = self.cfg
        floor = float(cfg.get("anything_floor", 3) or 0) / 100.0
        tangent = float(cfg.get("tangent_per_minute", 9) or 0) / 100.0
        variety = self.dial("variety", 60) * 1.6
        objective = sum(m.objective for m in members) / max(1, len(members))
        left = inst.wave_left() if active else 0
        high = bool(intel.perches or intel.high_places)
        weights: Dict[str, float] = {}
        if active:
            weights["hold"] = 0.4 + objective * 0.6 + avg("medic") * 0.3
            weights["perch"] = avg("perch") * (1.4 if high else 0.0)
            weights["roam"] = 0.12 + avg("front") * 0.5 + (0.3 if solo else 0.0)
            weights["kite"] = avg("kite") * 0.9 * (1.0 if intel.places else 0.0)
            weights["flank"] = avg("flank") * 0.8 * (1.0 if intel.places else 0.0)
            if any(self._guardable(m, brain) for m in self.inst.survivors()):
                weights["guard"] = avg("medic") * (0.6 if len(members) <= 2 else 0.2)
            hunting = left and left <= max(4, int(inst.plan.get("total", 30) * 0.12)
                                           if inst.plan else 4)
            weights["hunt"] = avg("hunt") * (2.2 if hunting else 0.25)
        else:
            left_s = inst.phase_until - moment
            weights["hangout"] = 0.2 + avg("social") * 0.5 + (0.0 if solo else 0.25)
            weights["explore"] = (avg("roam") + tangent * 2.0) * (1.4 if solo else 0.8)
            weights["wander"] = avg("wander") * variety * (1.0 if solo else 0.7)
            weights["patrol"] = (avg("watch") * 0.4 + objective * 0.25) * variety
            weights["search"] = (avg("curious") * 0.5 + avg("roam") * 0.3) * variety
            weights["climb"] = (avg("play") * 0.5 + avg("climb") * 0.5) * variety * \
                (1.0 if high else 0.0)
            weights["lookout"] = avg("watch") * variety * (1.0 if len(members) <= 2 else 0.5) * \
                (1.0 if high else 0.4)
            weights["prep"] = avg("prep") * (1.6 if left_s < 25 else 0.35)
            weights["rest"] = avg("rest") * 0.7 * (1.3 if solo else 0.8)
            weights["mess"] = avg("play") * variety * 0.6
            if self.noises:
                noise = max(self.noises, key=lambda n: n[1])
                if _flat(noise[0], brain.p.pos) < 260:
                    weights["curious"] = avg("curious") * 2.5
            if intel.lure and not self.poked:
                weights["poke"] = avg("play") * 0.2
            weights["perch"] = avg("perch") * (0.8 if left_s < 12 else 0.2) * \
                (1.0 if high else 0.0)
            weights["roam"] = 0.05 + avg("front") * 0.1
        recent = squad.recent if squad is not None else mind.recent
        for key in weights:
            repeats = sum(1 for k, _n in recent[-3:] if k == key)
            weights[key] = max(floor, weights[key] * (0.5 ** repeats))
        kind = rng.choices(list(weights), list(weights.values()))[0]
        act = self._plan(brain, mind, kind, moment, squad, active, recent)
        recent.append((act.kind, act.name))
        del recent[:-6]
        return act

    def _owner(self, brain, squad: Optional[Squad]) -> Any:
        return squad.sid if squad is not None else -brain.p.pid

    def _heading_for(self, brain, squad: Optional[Squad]) -> float:
        return squad.home if squad is not None else self.mind(brain).home

    def _plan(self, brain, mind: Mind, kind: str, moment: float, squad: Optional[Squad],
              active: bool, recent: List[Tuple[str, str]]) -> Activity:
        intel = self.intel()
        rng = brain.rng
        solo = squad is None
        avoid = {name for _k, name in recent[-2:]}
        here = list(brain.p.pos)
        owner = self._owner(brain, squad)
        heading = self._heading_for(brain, squad)
        members = len(squad.members) if squad is not None else 1

        def pick(want: str, near: float = 0.0, far: float = 260.0,
                 around: Optional[Sequence[float]] = None,
                 pool: Optional[List[Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
            return self._pick_place(brain, owner, heading, want, around or here, near, far,
                                    active, avoid, members, pool)

        def named(place: Dict[str, Any]) -> str:
            return place.get("near") or intel.compass(place["p"])

        if kind == "perch":
            perch = self._pick_perch(brain, active, avoid)
            if perch is not None and (not intel.high_places or rng.random() < 0.55):
                act = Activity("perch", list(perch["p"]), perch["name"],
                               moment + rng.uniform(35, 80), look="out")
                act.data["perch"] = True
                return act
            place = pick("high", far=170)
            if place is not None:
                act = Activity("perch", list(place["p"]), "up top by %s" % named(place)
                               if place.get("near") else "up on %s" % intel.compass(place["p"]),
                               moment + rng.uniform(35, 80), look="out")
                act.data["perch"] = True
                return act
            kind = "hold"
        if kind == "hold":
            spot = self._pick_spot(brain, "s", active=active, avoid=avoid, owner=owner)
            place = pick("hold", far=170)
            use_place = place is not None and (spot is None or rng.random() < 0.6 or
                                               _flat(spot["p"], here) > 170)
            if use_place:
                point, name = list(place["p"]), named(place)
            elif spot is not None:
                point, name = self._snap(spot["p"], 9.0, rng), spot["name"]
            else:
                point, name = here, intel.describe(here)
            return Activity("hold", point, name, moment + rng.uniform(25, 60), look="out")
        if kind == "hunt":
            target = self._straggler(here)
            if target is not None:
                act = Activity("hunt", target, "", moment + rng.uniform(15, 30), pace="run")
                if solo or rng.random() < 0.3:
                    self._line(brain, "hunt", 0.25)
                return act
            return Activity("hold", here, intel.describe(here), moment + 15, look="out")
        if kind == "hangout":
            spot = self._pick_spot(brain, "h", active=False, near=True, avoid=avoid,
                                   owner=owner)
            place = pick("open", near=25, far=150)
            if spot is not None and (place is None or rng.random() < 0.45) and \
                    self._crowd_near(spot["p"], owner) < 2:
                point, name = self._snap(spot["p"], 10.0, rng), spot["name"]
            elif place is not None:
                point, name = list(place["p"]), named(place)
            else:
                point, name = self._snap(intel.safe, 20.0, rng), "the safe room"
            return Activity("hangout", point, name, moment + rng.uniform(20, 50), look="in")
        if kind == "explore":
            route = []
            first = self._pick_spot(brain, "e", active=active, far=True, avoid=avoid,
                                    owner=owner)
            if first is not None:
                for _ in range(rng.randint(0, 2)):
                    nxt = self._pick_spot(brain, "e", active=active, around=first["p"],
                                          owner=owner)
                    if nxt is not None and nxt is not first:
                        route.append({"p": self._snap(nxt["p"], 10.0, rng), "name": nxt["name"],
                                      "linger": rng.uniform(5, 16)})
                act = Activity("explore", self._snap(first["p"], 10.0, rng), first["name"],
                               moment + rng.uniform(40, 90), route=route,
                               linger=rng.uniform(5, 18), pace="mix")
                if solo and rng.random() < 0.3:
                    self._line(brain, "solo", 0.25)
                return act
            kind = "wander"
        if kind == "wander":
            stops = self._chain(brain, owner, heading, rng.randint(3, 5), 45, 140, active, avoid,
                                members)
            if stops:
                first = stops.pop(0)
                act = Activity("wander", list(first["p"]), named(first),
                               moment + rng.uniform(45, 100),
                               route=[{"p": s["p"], "name": named(s),
                                       "linger": rng.uniform(1.0, 6.0)} for s in stops],
                               linger=rng.uniform(1.0, 6.0), pace="walk")
                if rng.random() < 0.25:
                    self._line(brain, "wander", 0.3)
                return act
        if kind == "patrol":
            stops = self._patrol(brain, owner, heading, active, avoid, members)
            if stops:
                first = stops.pop(0)
                side = intel.compass(first["p"])
                act = Activity("patrol", list(first["p"]), side, moment + rng.uniform(50, 100),
                               route=[{"p": s["p"], "name": side,
                                       "linger": rng.uniform(1.5, 5.0)} for s in stops],
                               linger=rng.uniform(1.5, 5.0), pace="walk", look="edge")
                if rng.random() < 0.3:
                    self._line(brain, "patrol", 0.3, text="ill take %s" % side.replace(
                        "the ", "", 1) if rng.random() < 0.5 else "")
                return act
        if kind == "search":
            anchor = self._pick_spot(brain, "e", active=active, avoid=avoid, owner=owner) \
                if rng.random() < 0.5 else None
            centre = pick("any", near=30, far=200)
            base = anchor["p"] if anchor is not None else (centre["p"] if centre else None)
            if base is not None:
                name = anchor["name"] if anchor is not None else named(centre)
                stops = [s for s in (self._snap(base, 22.0, rng) for _ in range(rng.randint(3, 5)))]
                first = stops.pop(0)
                act = Activity("search", first, name, moment + rng.uniform(40, 80),
                               route=[{"p": s, "name": name, "linger": rng.uniform(1.5, 4.5)}
                                      for s in stops],
                               linger=rng.uniform(1.5, 4.5), pace="jog")
                if rng.random() < 0.3:
                    self._line(brain, "search", 0.3)
                return act
        if kind == "climb":
            place = pick("high", far=140)
            if place is not None:
                route = []
                for _ in range(rng.randint(0, 2)):
                    nxt = pick("high", far=35, around=place["p"])
                    if nxt is not None and nxt is not place:
                        route.append({"p": nxt["p"], "name": named(nxt),
                                      "linger": rng.uniform(4, 12)})
                act = Activity("climb", list(place["p"]), named(place),
                               moment + rng.uniform(30, 70), route=route,
                               linger=rng.uniform(5, 14), pace="jog")
                return act
        if kind == "lookout":
            place = pick("watch", near=40, far=230)
            if place is not None:
                act = Activity("lookout", list(place["p"]), named(place),
                               moment + rng.uniform(30, 65), look="edge")
                return act
        if kind == "prep":
            route = []
            ammo = sorted(self.inst.area["points"].get("ammo", []),
                          key=lambda pt: _flat(pt["p"], here))[:1]
            meds = [pt for i, pt in enumerate(self.inst.area["points"].get("med", []))
                    if i < len(self.inst.med_charges) and self.inst.med_charges[i] > 0]
            meds = sorted(meds, key=lambda pt: _flat(pt["p"], here))[:1]
            stops = ammo + (meds if brain.p.health < 90 or rng.random() < 0.3 else [])
            if stops:
                for stop in stops[1:]:
                    route.append({"p": list(stop["p"]), "name": "", "linger": 1.5, "use": True})
                act = Activity("prep", list(stops[0]["p"]), "", moment + rng.uniform(25, 45),
                               route=route, linger=1.5, pace="run")
                act.data["use"] = True
                if rng.random() < 0.35:
                    self._line(brain, "prep", 0.35)
                return act
        if kind == "rest":
            place = pick("quiet", near=10, far=90)
            if place is not None:
                return Activity("rest", list(place["p"]), named(place),
                                moment + rng.uniform(15, 40), pace="walk", look="around")
        if kind == "mess":
            place = pick("open", near=0, far=60)
            point = list(place["p"]) if place is not None else here
            act = Activity("mess", point, named(place) if place else intel.describe(here),
                           moment + rng.uniform(10, 22), pace="run")
            if rng.random() < 0.4:
                self._line(brain, "mess", 0.35)
            return act
        if kind == "curious" and self.noises:
            noise = max(self.noises, key=lambda n: n[1])
            act = Activity("curious", self._snap(noise[0], 12.0, rng), noise[2],
                           moment + rng.uniform(25, 45), linger=rng.uniform(4, 10), pace="jog")
            self._line(brain, "curious", 0.4)
            return act
        if kind == "poke" and intel.lure:
            self.poked = True
            act = Activity("poke", list(intel.lure["p"]), intel.lure.get("name", ""),
                           moment + rng.uniform(25, 45), linger=2.0, pace="run")
            act.data["use"] = True
            return act
        if kind == "kite":
            stops = self._loop(brain, here, rng.uniform(26, 40), 4)
            if stops:
                first = stops.pop(0)
                act = Activity("kite", first, "", moment + rng.uniform(15, 26),
                               route=[{"p": s, "name": "", "linger": 0.0} for s in stops],
                               linger=0.0, pace="run")
                if rng.random() < 0.4:
                    self._line(brain, "kite", 0.35)
                return act
        if kind == "flank":
            spot = self._flank_spot(brain, here)
            if spot is not None:
                act = Activity("flank", spot, intel.describe(spot), moment + rng.uniform(20, 40),
                               pace="run", look="out")
                if rng.random() < 0.4:
                    self._line(brain, "flank", 0.35)
                return act
        if kind == "guard":
            person = min((m for m in self.inst.survivors() if self._guardable(m, brain)),
                         key=lambda m: _flat(m.pos, here), default=None)
            if person is not None:
                act = Activity("guard", feet(person), person.username,
                               moment + rng.uniform(25, 50), pace="run", look="out")
                act.data["pid"] = person.pid
                if rng.random() < 0.3:
                    self._line(brain, "guard", 0.3)
                return act
        if kind == "fallback":
            away = self._away_from_horde(here, 34.0) if self.grid is not None and \
                self.grid.ready else None
            place = pick("hold", near=15, far=70, around=away) if away is not None else None
            point = list(place["p"]) if place is not None else (away or here)
            act = Activity("fallback", point, intel.describe(point),
                           moment + rng.uniform(15, 30), pace="run", look="out")
            self._line(brain, "fallback", 0.35)
            return act
        if kind == "roam":
            stops = self._chain(brain, owner, heading, rng.randint(2, 3), 40, 110, active,
                                avoid, members)
            if stops:
                first = stops.pop(0)
                return Activity("roam", list(first["p"]), named(first),
                                moment + rng.uniform(30, 70),
                                route=[{"p": s["p"], "name": named(s), "linger": 2.0}
                                       for s in stops], linger=2.0,
                                pace="run" if active else "mix")
            first = self._pick_spot(brain, "s", active=active, far=True, avoid=avoid,
                                    owner=owner)
            if first is not None:
                return Activity("roam", self._snap(first["p"], 10.0, rng), first["name"],
                                moment + rng.uniform(40, 90), linger=2.0,
                                pace="run" if active else "mix")
        # nothing else came of it: somewhere to be, away from the spawn
        place = pick("any", near=20, far=120)
        if place is not None:
            return Activity("hangout" if not active else "hold", list(place["p"]),
                            named(place), moment + rng.uniform(15, 30),
                            look="around" if not active else "out")
        return Activity("hold", here, intel.describe(here), moment + 20, look="out")

    # ---------------------------------------------------- where to go
    def _crowd_near(self, point: Sequence[float], owner: Any) -> float:
        """How many people are standing round ``point`` right now, not
        counting the asker's own squad."""
        intel = self.intel()
        ci, cj = intel.cell_of(point)
        total = 0.0
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                n = self.crowd.get((ci + di, cj + dj), 0)
                if n:
                    total += n * (1.0 if di == 0 and dj == 0 else 0.5)
        if isinstance(owner, int) and owner > 0 and owner in self.squads:
            squad = self.squads[owner]
            for member in squad.members:
                if _flat(member.p.pos, point) < CELL * 1.5:
                    total -= 1.0
            if squad.person is not None and _flat(squad.person.pos, point) < CELL * 1.5:
                total -= 1.0
        return max(0.0, total)

    def _claimed(self, point: Sequence[float], owner: Any) -> float:
        """Somebody else already said they are going there (or near it)."""
        total = 0.0
        for key, where in self.claims.items():
            if key == owner:
                continue
            d = _flat(where, point)
            if d < 70.0:
                total += 1.0 - d / 70.0
        return total

    def _pick_place(self, brain, owner: Any, heading: float, want: str,
                    around: Sequence[float], near: float, far: float, active: bool,
                    avoid=(), members: int = 1,
                    pool: Optional[List[Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
        """The best of a sample of the area's places for ``want`` -- any,
        open, quiet, high, watch or hold -- between ``near`` and ``far`` of
        ``around``: away from the others and from the spawn, somewhere
        nobody has been for a while, out the way this squad set off."""
        intel = self.intel()
        places = pool if pool is not None else intel.places
        if not places:
            return None
        rng = brain.rng
        moment = now()
        spread = self.dial("spread", 70)
        keep_clear = self.on("avoid_spawns")
        sample = places if len(places) <= 140 else rng.sample(places, 140)
        best, best_score = None, -1e9
        for place in sample:
            p = place["p"]
            d = _flat(p, around)
            if d < near or d > far or self._fell(p):
                continue
            score = rng.uniform(0.0, 0.6)
            last = self.heat.get(place["cell"], -1e9)
            score += min(1.0, (moment - last) / 150.0) * 0.8
            score -= self._crowd_near(p, owner) * 0.6 * (0.4 + spread)
            score -= self._claimed(p, owner) * 1.1 * (0.4 + spread)
            if place["home"] < SAFE_ZONE:
                score -= 1.6 * (0.3 + spread)
            score += math.cos(place["angle"] - heading) * 0.45 * spread
            score -= d / 400.0
            if place.get("near") in avoid:
                score -= 0.6
            if want == "high":
                score += 1.4 if place["high"] else -3.0
            elif want == "open":
                score += (place["open"] - 6) * 0.12 - (0.8 if place["high"] else 0.0)
            elif want == "quiet":
                score += (0.5 if not place.get("near") else -0.2) + place["ring"] * 0.4 - \
                    (0.5 if place["high"] else 0.0)
            elif want == "watch":
                score += (1.0 if place["high"] else 0.0) + place["ring"] * 0.8
            elif want == "hold":
                score += (0.7 if place["high"] else 0.0) + (0.25 if place["open"] < 7 else 0.0)
            if active:
                if place["danger"] < 25:
                    score -= 3.0
                elif keep_clear and place["danger"] < 50:
                    score -= 1.2
                if members == 1 and place["home"] > 200:
                    score -= 0.6            # alone at the far end in a wave: no
            if score > best_score:
                best, best_score = place, score
        return best

    def _chain(self, brain, owner: Any, heading: float, count: int, step_near: float,
               step_far: float, active: bool, avoid, members: int) -> List[Dict[str, Any]]:
        """A string of places, each a walk on from the last: a wander."""
        stops: List[Dict[str, Any]] = []
        at = list(brain.p.pos)
        for _ in range(count):
            place = self._pick_place(brain, owner, heading, "any", at, step_near, step_far,
                                     active, avoid, members)
            if place is None:
                break
            stops.append(place)
            at = place["p"]
            heading += brain.rng.uniform(-0.9, 0.9)      # wanders, does not march
        return stops

    def _patrol(self, brain, owner: Any, heading: float, active: bool, avoid,
                members: int) -> List[Dict[str, Any]]:
        """A walk round one side of the area, out near its edge."""
        intel = self.intel()
        rng = brain.rng
        edge = [pl for pl in intel.places if pl["ring"] > 0.55 and not pl["high"]]
        if len(edge) < 4:
            return []
        start = self._pick_place(brain, owner, heading, "watch", brain.p.pos, 30, 260, active,
                                 avoid, members, pool=edge)
        if start is None:
            return []
        stops = [start]
        centre = intel.centre
        angle = math.atan2(start["p"][0] - centre[0], start["p"][2] - centre[2])
        turn = rng.choice((-1.0, 1.0)) * rng.uniform(0.35, 0.6)
        for _ in range(rng.randint(2, 4)):
            angle += turn
            want = [centre[0] + math.sin(angle) * intel.half * 0.75, 0.0,
                    centre[2] + math.cos(angle) * intel.half * 0.75]
            nxt = min(edge, key=lambda pl: _flat(pl["p"], want))
            if nxt is stops[-1] or _flat(nxt["p"], want) > 80:
                break
            stops.append(nxt)
        return stops if len(stops) >= 2 else []

    def _loop(self, brain, centre: Sequence[float], radius: float, count: int) -> List[List[float]]:
        """A ring of stops round ``centre``: the way round the block that a
        horde can be led round and round."""
        grid = self.grid
        if grid is None or not grid.ready:
            return []
        intel = self.intel()
        start = brain.rng.uniform(-math.pi, math.pi)
        turn = brain.rng.choice((-1.0, 1.0))
        out = []
        for k in range(count):
            angle = start + turn * k * 2 * math.pi / count
            want = [centre[0] + math.sin(angle) * radius, centre[1],
                    centre[2] + math.cos(angle) * radius]
            node = grid.nearest(want, 3)
            if node < 0:
                continue
            point = grid.point(node)
            if abs(point[1] - centre[1]) > 4.0 or not intel.reachable(point):
                continue
            out.append(point)
        return out if len(out) >= 3 else []

    def _flank_spot(self, brain, here: Sequence[float]) -> Optional[List[float]]:
        """Off to the side of where the horde is coming from."""
        near = [z for z in self.inst.horde.zombies.values()
                if z.alive and _flat(z.pos, here) < 220]
        if len(near) < 3:
            return None
        cx = sum(z.pos[0] for z in near) / len(near)
        cz = sum(z.pos[2] for z in near) / len(near)
        angle = math.atan2(cx - here[0], cz - here[2]) + brain.rng.choice((-1.0, 1.0)) * \
            brain.rng.uniform(1.0, 1.4)
        dist = brain.rng.uniform(30.0, 50.0)
        want = [here[0] + math.sin(angle) * dist, here[1], here[2] + math.cos(angle) * dist]
        spot = self._snap(want, 12.0, brain.rng)
        intel = self.intel()
        if intel._danger(spot) < 30:
            return None
        return spot

    def _guardable(self, player, brain) -> bool:
        """Somebody worth standing next to: a real player, or a newbie, on
        their feet and not already guarded by two."""
        if player is brain.p or not self._standing(player):
            return False
        if player.brain is not None and "newbie" not in player.brain.tags:
            return False
        if _flat(player.pos, self.intel().safe) < SAFE_ZONE and \
                self._near_count(player.pos, 50.0) < 3:
            return False                 # safe and sound: no guard needed
        guards = 0
        for other in self.runner.brains.values():
            mind = other.mind
            if mind is None or other is brain:
                continue
            act = mind.squad.act if mind.squad is not None else mind.act
            if act is not None and act.kind == "guard" and act.data.get("pid") == player.pid:
                guards += 1
        return guards < 2

    def _pick_spot(self, brain, flag: str, active: Optional[bool] = None,
                   far: bool = False, near: bool = False,
                   around: Optional[Sequence[float]] = None,
                   avoid=(), owner: Any = None) -> Optional[Dict[str, Any]]:
        intel = self.intel()
        if active is None:
            active = self.inst.phase == "active"
        mind = self.mind(brain)
        pool = intel.spots_with(flag) or intel.spots
        here = around or brain.p.pos
        keep_clear = self.on("avoid_spawns")
        spread = self.dial("spread", 70)
        best, best_score = None, -1e9
        for spot in pool:
            d = _flat(spot["p"], here)
            score = brain.rng.uniform(0.0, 1.0)
            if near:
                score -= d / 90.0
            elif far:
                score += min(d, 220.0) / 220.0 * 0.6 - (1.0 if d > 300 else 0.0)
            else:
                score -= d / 140.0
            if "r" in spot["flags"]:
                if active and keep_clear:
                    score -= 2.5
                else:
                    score += mind.profile.roam * 0.6 - 0.3
            if "c" in spot["flags"]:
                score += mind.profile.climb * 0.5
            if spot["name"] in avoid:
                score -= 0.9
            if active and keep_clear and spot.get("danger", 999) < 45:
                score -= 1.0
            if owner is not None:
                score -= self._crowd_near(spot["p"], owner) * 0.45 * (0.4 + spread)
                score -= self._claimed(spot["p"], owner) * 0.9 * (0.4 + spread)
            if _flat(spot["p"], intel.safe) < SAFE_ZONE:
                score -= 2.0 * (0.3 + spread)
            if score > best_score:
                best, best_score = spot, score
        return best

    def _pick_perch(self, brain, active: bool, avoid=()) -> Optional[Dict[str, Any]]:
        intel = self.intel()
        best, best_score = None, -1e9
        owner = self._owner(brain, self.mind(brain).squad)
        for perch in intel.perches:
            if self._fell(perch["p"]):
                continue
            d = _flat(perch["p"], brain.p.pos)
            score = brain.rng.uniform(0, 0.6) - d / 150.0
            score -= self._claimed(perch["p"], owner) * 1.2
            if perch["name"] in avoid:
                score -= 0.9
            if active and perch.get("danger", 999) < 40:
                score -= 0.6
            if score > best_score:
                best, best_score = perch, score
        return best

    def _fell(self, point: Sequence[float]) -> bool:
        return any(_flat(point, b) < 8.0 and abs(point[1] - b[1]) < 4.0 for b in self.bad)

    def _straggler(self, pos: Sequence[float]) -> Optional[List[float]]:
        zombies = self._zombies()
        if not zombies:
            return None
        z = min(zombies, key=lambda z: math.dist(z.pos, pos))
        return list(z.pos)

    def _meander(self, brain, start: Sequence[float], end: Sequence[float]) -> Optional[List[float]]:
        """A point a little off the straight line, so a long walk curves the
        way a person's does instead of running on rails."""
        mx, mz = (start[0] + end[0]) / 2.0, (start[2] + end[2]) / 2.0
        dx, dz = end[0] - start[0], end[2] - start[2]
        length = math.hypot(dx, dz) or 1.0
        side = brain.rng.uniform(0.15, 0.35) * length * brain.rng.choice((-1.0, 1.0))
        want = [mx - dz / length * side, (start[1] + end[1]) / 2.0, mz + dx / length * side]
        spot = self._snap(want, 10.0, brain.rng)
        if spot is want or abs(spot[1] - start[1]) > 3.0:
            return None
        return spot

    # ------------------------------------------------------ carrying it out
    def _pace(self, brain, mind: Mind, act: Activity, d: float, calm: bool,
              moment: float) -> float:
        """How fast: a run in a wave, a stroll on a wander, and on a jog a
        run and a walk by turns."""
        profile = mind.profile
        if not calm or act.pace == "run":
            return RUN
        if act.pace == "jog":
            if moment >= mind.jog_at:
                mind.jog_run = not mind.jog_run
                mind.jog_at = moment + brain.rng.uniform(2.5, 7.0)
            return RUN if mind.jog_run else WALK
        # decided for a few seconds at a time, never think by think
        if moment < act.data.get("speed_until", 0.0):
            return act.data["speed"]
        if act.pace == "walk":
            speed = RUN if d > 160 else WALK
        else:
            relaxed = d < 30 and act.kind in ("hangout", "explore", "rest", "mess", "lookout")
            speed = WALK if relaxed and brain.rng.random() < 0.6 + profile.pace_walk * 0.3 \
                else RUN
        act.data["speed"] = speed
        act.data["speed_until"] = moment + brain.rng.uniform(3.0, 8.0)
        return speed

    def _pursue(self, brain, mind: Mind, act: Activity, moment: float,
                squad: Optional[Squad]) -> None:
        p = brain.p
        point = act.point
        if point is None:
            self._look_round(brain, moment)
            return
        if act.kind == "hunt" and moment - act.data.get("re", 0.0) > 3.0:
            act.data["re"] = moment
            fresh = self._straggler(p.pos)
            if fresh is not None:
                act.point = point = fresh
        if act.kind == "guard":
            person = self.inst.players.get(act.data.get("pid", 0))
            if person is not None and self._standing(person):
                act.point = point = feet(person)
                if _flat(point, p.pos) < 7.0:
                    brain.waypoints = []
                    self._face(brain, moment, point, 0.8)
                    return
        d = _flat(point, p.pos)
        arrive = 4.0 if act.kind in ("perch", "climb", "lookout", "poke", "prep") else \
            (5.0 if act.kind in ("search", "kite", "curious") else 7.0)
        vertical = act.kind in ("perch", "climb", "lookout") and abs(point[1] - p.pos[1]) > 3.0
        if d > arrive or vertical:
            calm = self.inst.phase != "active"
            target = point
            via = act.data.get("via")
            if via is None and calm and act.pace != "run" and d > 55 and \
                    not act.data.get("meandered"):
                act.data["meandered"] = True
                via = act.data["via"] = self._meander(brain, p.pos, point)
            if via is not None:
                if _flat(via, p.pos) < 6.0:
                    act.data["via"] = None
                else:
                    target = via
            brain.speed = self._pace(brain, mind, act, d, calm, moment)
            key = "%s%.0f:%.0f" % (act.kind, target[0], target[2])
            if target is point and (act.kind in ("perch", "climb", "lookout") or
                                    act.data.get("use")):
                brain.go(point, key, precise=True)
            else:
                self._walk(brain, target, key)
            if calm and act.pace == "walk" and moment >= mind.glance_at:
                # a glance at something on the way, as people do
                mind.glance_at = moment + brain.rng.uniform(4.0, 10.0)
                if brain.rng.random() < 0.5:
                    brain.look_until = moment + brain.rng.uniform(0.8, 1.6)
                    brain.look_yaw = p.yaw + brain.rng.uniform(-1.2, 1.2)
            return
        if not act.arrived:
            act.arrived = moment
            self._arrived(brain, mind, act, moment, squad)
        self._at(brain, mind, act, moment, squad)

    def _arrived(self, brain, mind: Mind, act: Activity, moment: float,
                 squad: Optional[Squad]) -> None:
        p = brain.p
        if act.kind == "perch":
            if squad is not None and not squad.said_perch:
                squad.said_perch = True
                self._line(brain, "perch", 0.35)
            self._speech("high_ground", 120.0, by=p.username, what=act.name)
        elif act.kind == "climb":
            if brain.rng.random() < mind.profile.play + 0.2:
                brain.jumpy_until = moment + brain.rng.uniform(1.5, 4.0)
            if brain.rng.random() < 0.3:
                self._line(brain, "climb", 0.35)
        elif act.kind == "lookout" and brain.rng.random() < 0.35:
            self._line(brain, "lookout", 0.35)
        elif act.kind == "poke":
            self._line(brain, "poke", 0.6)        # pressing it is the "use" below
        elif act.kind == "curious" and brain.rng.random() < 0.3:
            self._line(brain, "curious", 0.25, text=brain.rng.choice(
                ["nothing here", "huh", "all clear", "nvm"]))
        if act.data.get("use"):
            self.inst.use(p)
            mind.ammo_at = -1e9
        # the next stop on a string of them is "use" too if it says so
        if act.route and act.route[0].get("use"):
            act.data["use"] = True

    def _at(self, brain, mind: Mind, act: Activity, moment: float,
            squad: Optional[Squad]) -> None:
        """There: what each plan looks like once you have got to it."""
        p = brain.p
        point = act.point
        kind = act.kind
        grid_ok = self.grid is not None and self.grid.ready
        if kind == "hangout":
            if squad is not None and len(squad.members) > 1:
                # the leader takes its own place in the ring
                spot = [point[0], point[1], point[2] + 3.2]
                if _flat(spot, p.pos) > 2.0:
                    brain.speed = WALK
                    self._walk(brain, spot, "ring%d" % squad.sid)
                    return
                brain.waypoints = []
                self._face(brain, moment, point, 0.5, toward=True)
                return
            if moment - mind.last_fidget > brain.rng.uniform(6, 14) and grid_ok:
                mind.last_fidget = moment
                node = self.grid.random_node(brain.rng, point, 7.0)
                if node >= 0:
                    brain.speed = WALK
                    self._walk(brain, self.grid.point(node), "fidget%d" % node)
                    return
        elif kind == "rest":
            brain.waypoints = []
            self._rest(brain, mind, moment)
            return
        elif kind == "mess":
            brain.jumpy_until = moment + 1.0
            if not brain.waypoints and grid_ok and brain.rng.random() < 0.25:
                node = self.grid.random_node(brain.rng, point, 9.0)
                if node >= 0:
                    brain.speed = RUN
                    self._walk(brain, self.grid.point(node), "mess%d" % node)
            elif not brain.waypoints:
                brain.look_yaw = p.yaw + brain.rng.uniform(1.5, 3.0)
            return
        elif kind == "climb":
            if not brain.waypoints and grid_ok and moment - mind.last_fidget > \
                    brain.rng.uniform(4, 9):
                mind.last_fidget = moment
                node = self.grid.random_node(brain.rng, point, 6.0)
                if node >= 0 and abs(self.grid.py[node] - point[1]) < 1.5:
                    brain.speed = WALK
                    self._walk(brain, self.grid.point(node), "roof%d" % node)
                    return
            if brain.rng.random() < 0.02 + mind.profile.play * 0.05:
                brain.jumpy_until = moment + brain.rng.uniform(0.8, 2.0)
        elif kind in ("lookout", "patrol"):
            if not brain.waypoints:
                self._face(brain, moment, self.intel().centre, 0.7, toward=False)
            return
        elif kind in ("hold", "perch", "flank", "fallback"):
            if not brain.waypoints:
                near = [z for z in self.inst.horde.zombies.values()
                        if z.alive and math.dist(z.pos, p.pos) < 120]
                if near and brain.rng.random() < 0.7:
                    z = min(near, key=lambda z: math.dist(z.pos, p.pos))
                    self._face(brain, moment, z.pos, 0.3, toward=True)
                else:
                    self._face(brain, moment, self.intel().safe, 0.9, toward=False)
                # a small shuffle now and then: nobody stands like a statue
                if grid_ok and moment - mind.last_fidget > brain.rng.uniform(8, 16):
                    mind.last_fidget = moment
                    node = self.grid.random_node(brain.rng, point, 3.5)
                    if node >= 0 and abs(self.grid.py[node] - point[1]) < 1.5:
                        brain.speed = WALK
                        self._walk(brain, self.grid.point(node), "shuffle%d" % node)
            return
        elif kind == "search":
            if not brain.waypoints and moment >= brain.look_until:
                # peering into the corners: quick looks, side to side
                brain.look_until = moment + brain.rng.uniform(0.5, 1.2)
                brain.look_yaw = p.yaw + brain.rng.choice((-1.0, 1.0)) * brain.rng.uniform(0.8, 1.8)
            return
        if not brain.waypoints:
            self._look_round(brain, moment)

    def _rest(self, brain, mind: Mind, moment: float) -> None:
        """A breather: standing about, a few seconds AFK at a time."""
        if moment >= mind.rest_at:
            mind.rest_at = moment + brain.rng.uniform(6.0, 14.0)
            if brain.rng.random() < 0.5 and not self._near_count(brain.p.pos, 50.0):
                brain.afk_until = moment + brain.rng.uniform(2.5, 7.0)
                return
        self._look_round(brain, moment)

    def _face(self, brain, moment: float, point: Sequence[float], jitter: float,
              toward: bool = True) -> None:
        """Turn to (or away from) ``point`` every so often, never quite the
        same way twice."""
        if moment < brain.look_until:
            return
        brain.look_until = moment + brain.rng.uniform(1.5, 4.5)
        p = brain.p
        angle = math.atan2(point[0] - p.pos[0], point[2] - p.pos[2])
        if not toward:
            angle += math.pi
        brain.look_yaw = angle + brain.rng.uniform(-jitter, jitter)

    def _look_round(self, brain, moment: float, toward: Optional[Sequence[float]] = None) -> None:
        """Eyes up and about: out over the street, at the noise, at a mate."""
        if moment < brain.look_until:
            return
        brain.look_until = moment + brain.rng.uniform(1.2, 4.0)
        p = brain.p
        if toward is not None and brain.rng.random() < 0.3:
            brain.look_yaw = math.atan2(toward[0] - p.pos[0], toward[2] - p.pos[2])
            return
        near = [z for z in self.inst.horde.zombies.values()
                if z.alive and math.dist(z.pos, p.pos) < 160]
        if near and brain.rng.random() < 0.6:
            z = min(near, key=lambda z: math.dist(z.pos, p.pos))
            brain.look_yaw = math.atan2(z.pos[0] - p.pos[0], z.pos[2] - p.pos[2]) + \
                brain.rng.uniform(-0.3, 0.3)
            return
        brain.look_yaw = (brain.look_yaw if brain.look_yaw is not None else p.yaw) + \
            brain.rng.uniform(-1.6, 1.6)

    # ------------------------------------------------------------- lobby
    def _lobby(self, brain, moment: float) -> None:
        """Waiting in the bunker for the next wave: mill about, and the ones
        with an itchy trigger finger put a few rounds into the dummies."""
        inst = self.inst
        p = brain.p
        dummies = [d for d in getattr(inst, "dummies", []) if d.alive]
        mind = self.mind(brain)
        if dummies and self.on("practice") and mind.profile.front + brain.skill > 0.6:
            dummy = min(dummies, key=lambda d: math.dist(d.pos, p.pos))
            d = math.dist(dummy.pos, p.pos)
            if d > 45:
                brain.speed = RUN
                brain.go(dummy.pos, "range%d" % dummy.ident)
                return
            brain.waypoints = []
            eye_y = p.pos[1] + 5.05
            dx, dy, dz = dummy.pos[0] - p.pos[0], dummy.pos[1] + 3.6 - eye_y, dummy.pos[2] - p.pos[2]
            yaw = math.atan2(dx, dz)
            pitch = math.atan2(dy, math.hypot(dx, dz))
            brain.aim_yaw, brain.aim_pitch = yaw, pitch
            p.yaw, p.pitch = yaw, pitch
            if moment >= brain.next_shot and brain.rng.random() < 0.5:
                err = brain.aim_error
                yaw += brain.rng.gauss(0, err)
                pitch += brain.rng.gauss(0, err * 0.7)
                cp = math.cos(pitch)
                if p.ammo[p.slot] <= 0:
                    inst.use(p)                  # the bunker's crate is free
                inst.handle_fire(p, {"d": [math.sin(yaw) * cp, math.sin(pitch),
                                           math.cos(yaw) * cp]})
                brain.next_shot = moment + brain.rng.uniform(0.35, 1.4)
                if brain.rng.random() < 0.01:
                    self._line(brain, "practice", 0.2)
            return
        if not brain.waypoints and brain.rng.random() < 0.15 and self.grid is not None \
                and self.grid.ready:
            centre = (inst.lobby.get("centre") or [0, 0, 0])
            node = self.grid.random_node(brain.rng, centre, 40)
            if node >= 0:
                brain.speed = WALK if brain.rng.random() < 0.5 else RUN
                brain.go(self.grid.point(node), "lobby%d" % node)

    # ============================================================ reports
    def bot_state(self, brain) -> Dict[str, Any]:
        mind = brain.mind
        p = brain.p
        out: Dict[str, Any] = {}
        if mind is None or p.extra.get("ll_where") != "field":
            return out
        intel = self.intel()
        out["doing"] = mind.doing
        out["near"] = intel.describe(p.pos)
        squad = mind.squad
        if squad is not None:
            names = [m.p.username for m in squad.members if m is not brain]
            if squad.person is not None:
                names.insert(0, squad.person.username)
            out["squad"] = names
        elif mind.solo:
            out["solo"] = True
        out["hp"] = int(max(0, p.health))
        out["ammo_low"] = self._ammo(p) < 0.2
        return out

    def summary(self) -> Dict[str, Any]:
        """The squads as the dashboard shows them."""
        intel = self.intel()
        squads = []
        for squad in self.squads.values():
            members = [m.p.username for m in squad.members]
            if not members:
                continue
            act = squad.act
            squads.append({"members": members,
                           "leader": squad.leader.p.username if squad.leader else "",
                           "person": squad.person.username if squad.person else "",
                           "doing": act.label() if act is not None else
                           ("sticking with %s" % squad.person.username if squad.person
                            else "getting going"),
                           "where": intel.describe(self._anchor(squad) or intel.safe)})
        solo = []
        for brain in self.runner.brains.values():
            mind = brain.mind
            if mind is None or mind.squad is not None or not self._field(brain):
                continue
            solo.append({"name": brain.p.username, "doing": mind.doing or "on their own",
                         "where": intel.describe(brain.p.pos)})
        return {"squads": squads, "solo": solo, "area": intel.name}

    # =============================================================== wake
    def spread(self, players) -> None:
        """A round woken between waves looks like one: squads of two or
        three spread over the area, a lone wolf or two further out, nobody
        heaped up at the safe room."""
        grid = self.grid
        if grid is None or not grid.ready:
            return
        intel = self.intel()
        intel.build_places()
        rng = self.rng
        moment = now()
        self.area_id = self.inst.area_id      # this is the area, not a change of it
        self.round_seen = getattr(self.inst, "round_number", 0)
        brains = [p.brain for p in players if p.brain is not None]
        rng.shuffle(brains)
        i = 0
        while i < len(brains):
            brain = brains[i]
            mind = self.mind(brain)
            if rng.random() < mind.profile.lone or not self.on("squads"):
                group = [brain]
                mind.solo = True
                mind.lone_until = moment + rng.uniform(30, 90)
                owner, heading = -brain.p.pid, mind.home
                i += 1
            else:
                size = max(2, min(mind.profile.size, self._cap(), len(brains) - i))
                group = brains[i:i + size]
                i += size
                if len(group) > 1:
                    squad = self._new_squad(moment)
                    for member in group:
                        self._join(member, squad)
                    owner, heading = squad.sid, squad.home
                else:
                    owner, heading = -brain.p.pid, mind.home
            place = self._pick_place(brain, owner, heading, "any", intel.safe, 40, 400,
                                     False, (), len(group)) if intel.places else None
            if place is not None:
                centre = place["p"]
            else:
                spot = rng.choice(intel.spots) if intel.spots else None
                centre = spot["p"] if spot else intel.safe
            self.claims[owner] = list(centre)
            cell = intel.cell_of(centre)
            self.crowd[cell] = self.crowd.get(cell, 0) + len(group)
            for member in group:
                # on the ground by the place -- never up on some roof nobody
                # can walk down from, which is where a careless pick lands
                spot = self._snap(centre, 8.0, rng)
                if not intel.reachable(spot):
                    continue
                member.p.pos = list(spot)
                member.p.last_ground_pos = list(member.p.pos)
                member.ground = list(member.p.pos)
                member.airborne = True
                member.last_progress = (list(member.p.pos), moment)
                member.p.yaw = rng.uniform(-math.pi, math.pi)
