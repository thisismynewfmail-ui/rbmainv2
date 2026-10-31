"""Plunder Bay: a treasure haul between two pirate crews, in four places.

Two crews -- the Scarlet Corsairs and the Azure Buccaneers -- moor their
ships at either end of an island and race to haul its treasure aboard:
loose doubloons, gold bars and jewels, chests dug up where X marks the
spot, and one cursed idol.  Treasure is carried one piece at a time (a
chest in both hands, no sword), tossed to a crewmate, dropped by whoever
is cut down carrying it, and stolen out of the other crew's hold by a bold
raider.  Each place has a twist: the tide goes out in Skull Cove, a kraken
rises on the Coral Reef, the redcoats march out of Port Royale's fort, and
Doubloon Isle's volcano erupts gold.  The rules are in
app/game/worlds/plunder_bay.py and the four places in
app/game/maps/events/plunder_bay/.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

WORLD: Dict[str, Any] = {
    "id": "plunder_bay",
    "prefix": "pb",
    "name": "Plunder Bay",
    "genre": "Treasure Haul",
    "tagline": "X marks the spot. Dig it up, haul it home, and cut down anybody who tries to take it.",
    "description": (
        "Two pirate crews, two ships, one island full of treasure. Loose doubloons, gold bars "
        "and jewels lie where they fell; chests are buried where X marks the spot (hold E to "
        "dig); and late in the haul a cursed idol rises on its altar. Carry it all back to "
        "your own ship's hold one piece at a time -- a chest takes both hands, so your crew "
        "had better watch your back -- toss it to a crewmate when you are chased, and cut "
        "down anybody carrying the other crew's plunder to drop it where they fall. A bold "
        "raider can even steal gold out of the enemy hold. Every place has its twist: the "
        "tide goes out in Skull Cove, a kraken rises on the Coral Reef, the redcoats march "
        "out of Port Royale's fort, and Doubloon Isle's volcano erupts in gold."),
    "max_players": 16,
    "team_count": 2,
    "mode": "treasure_haul",
    "round_label": "One haul",
    "colors": ["#c8302a", "#2a6ab8", "#e8b830"],
    "thumb": "plunder_bay",
    "features": ["16 players", "Treasure haul", "Pirate crews", "Dig for chests", "Your own weapons",
                 "Ship cannons", "Raids", "4 twists", "4 rotating islands"],
    # an enemy is just a name on the tag: you read your own crew's health at a
    # glance, never theirs
    "ally_health_only": True,
    "areas": [
        {"id": "skullcove", "name": "Skull Cove",
         "blurb": "A horseshoe island round a lagoon, under a rock shaped like a skull with a "
                  "cave in its mouth: jungle, a pirate camp, a rope bridge, a sandbar and a "
                  "wreck on the lagoon floor. The tide goes out."},
        {"id": "reef", "name": "Coral Reef",
         "blurb": "An atoll of sandy islets on boardwalks over the shallows, giant clams, a "
                  "lighthouse and a great wreck run aground in the lagoon. Something big "
                  "lives under the wreck."},
        {"id": "royale", "name": "Port Royale",
         "blurb": "A colonial harbour town: warehouses on the quays, the market square, the "
                  "governor's mansion, the church and the fort on the hill with the "
                  "treasury inside. The redcoats march out."},
        {"id": "doubloon", "name": "Doubloon Isle",
         "blurb": "A volcanic island of black sand and jungle: a lava river with stone "
                  "bridges, the old gold mine, a stepped temple with the idol on top, and "
                  "the volcano. It erupts gold."},
    ],
    "areas_note": "One haul on each island, then the crews sail on to another one.",
    "howto": [
        {"title": "Haul the treasure",
         "text": "Walk over doubloons, gold bars and jewels to pick them up, and carry them to "
                 "your own ship's hold. One piece at a time."},
        {"title": "X marks the spot",
         "text": "Hold E on an X to dig up a chest. It is worth the most -- and takes both "
                 "hands, so you cannot fight while you carry it."},
        {"title": "Your own arms, and the cannon",
         "text": "Fight with whatever is on your hotbar. Cut down a carrier and they drop their "
                 "treasure; your ship's cannons (E) shell the beach. Your crew's health shows "
                 "on their tags -- the other crew is just a name."},
        {"title": "Toss it, raid it",
         "text": "R tosses what you carry to a crewmate. Empty-handed in the enemy hold, hold "
                 "E to steal a bar of their gold."},
    ],
    "howto_note": "Late in every haul the cursed idol rises: it is worth more than anything "
                  "else, and everybody can see who is carrying it.",
    "team_names": {"red": "Scarlet Corsairs", "blue": "Azure Buccaneers"},
}

# struck on a doubloon, the enamel in the middle of it
FAMILY = ("doubloon", {
    "mesh": "doubloon", "face": "#1a2a3a", "ribbon": "#c8302a", "wing": "#e8d8a8",
    "wing_mesh": "wing", "plate_size": [1.3, 1.3, 1.0], "face_r": 0.34, "face_y": 0.0,
    "stripes": [],
})

BADGES: List[Tuple[Any, ...]] = [
    ("pb_jolly_roger", "Jolly Roger", "pb_wins", [1, 5, 15, 40, 100, 250],
     ["Cabin Boy", "Deckhand", "Buccaneer", "First Mate", "Captain", "Pirate King"],
     "Won hauls of Plunder Bay with your crew.", "em_pb_skull", "hauls won"),
    ("pb_plunderer", "Plunderer", "pb_plunder", [10, 100, 400, 1200, 3000, 8000],
     ["Pickpocket", "Looter", "Plunderer", "Hoarder", "Treasure Lord", "Dragon's Hoard"],
     "Banked doubloons' worth of treasure in your crew's hold.", "em_pb_coins", "doubloons banked"),
    ("pb_x_marks", "X Marks the Spot", "pb_digs", [1, 10, 40, 120, 300],
     ["Digger", "Shoveller", "Excavator", "Treasure Hunter", "Mapmaker"],
     "Dug up chests where X marks the spot.", "em_pb_x", "chests dug up"),
    ("pb_heavy_lifter", "Heavy Lifter", "pb_chests", [1, 10, 40, 120, 300],
     ["Porter", "Packhorse", "Strongarm", "Heavy Lifter", "Atlas"],
     "Carried a chest all the way into your crew's hold.", "em_pb_chest", "chests banked"),
    ("pb_cursed", "Cursed", "pb_idols", [1, 5, 15, 40],
     ["Unlucky", "Hexed", "Cursed", "Bearer of the Idol"],
     "Banked the cursed idol.", "em_pb_idol", "idols banked"),
    ("pb_raider", "Raider", "pb_raids", [1, 10, 40, 120, 300],
     ["Sneak", "Burglar", "Raider", "Sea Wolf", "Scourge of the Seas"],
     "Stole gold out of the enemy crew's hold.", "em_pb_hold", "raids"),
    ("pb_swashbuckler", "Swashbuckler", "pb_melee", [1, 25, 100, 300, 800],
     ["Scrapper", "Duellist", "Swashbuckler", "Blademaster", "Terror of the Tides"],
     "Cut down rival pirates up close, with a weapon off your own hotbar.", "em_pb_cutlass",
     "close-quarters takedowns"),
    ("pb_dead_shot", "Dead Shot", "pb_ranged", [1, 25, 100, 300, 800],
     ["Trigger", "Marksman", "Dead Shot", "Sharpshooter", "One Shot"],
     "Brought down rival pirates from range, with a weapon off your own hotbar.",
     "em_pb_pistol", "takedowns at range"),
    ("pb_broadside", "Broadside", "pb_cannon", [1, 20, 80, 250, 600],
     ["Gunner", "Powder Monkey", "Master Gunner", "Broadside", "Admiral"],
     "Hit rival pirates with your ship's cannon.", "em_pb_cannon", "cannon hits"),
    ("pb_good_catch", "Good Catch", "pb_catches", [1, 10, 40, 120],
     ["Butterfingers", "Safe Hands", "Good Catch", "Never Drops It"],
     "Caught treasure a crewmate tossed you.", "em_pb_catch", "catches"),
    ("pb_old_salt", "Old Salt", "pb_twists", [1, 10, 40, 120, 300],
     ["Landlubber", "Sea Legs", "Old Salt", "Storm Rider", "Legend of the Deep"],
     "Took on the sea itself: sunken treasure at low tide, blows on the kraken, redcoats "
     "downed, gold from the eruption.", "em_pb_anchor", "feats"),
    ("pb_every_port", "Every Port", "pb_areas", [1, 2, 3, 4],
     ["Visitor", "Traveller", "Navigator", "Every Port"],
     "Won a haul in each of Plunder Bay's four places.", "em_pb_map", "places"),
]

DERIVED = {"pb_areas": "pb_area_"}

# ------------------------------------------------------------------- speech
SPEECH: List[Tuple[str, str, int, str]] = [
    ("pb_bank_big", "A big haul banked", 45,
     "A pirate carried a chest (or the idol) into their crew's hold."),
    ("pb_idol", "The idol", 55,
     "The cursed idol rose on its altar -- or somebody picked it up."),
    ("pb_raid", "A raid", 45,
     "A pirate stole gold out of the other crew's hold."),
    ("pb_twist", "The twist", 40,
     "The place's twist started: low tide, the kraken, the redcoats, the eruption."),
    ("pb_lead", "The lead changes", 30,
     "One crew's hold overtook the other's."),
]

_TWISTS = {"tide": "The tide is going out -- there's treasure on the lagoon floor!",
           "kraken": "The kraken! It's coming up by the wreck!",
           "redcoats": "The redcoats are marching out of the fort!",
           "eruption": "The volcano's erupting -- and it's raining gold!"}


def describe(kind: str, event: Dict[str, Any], name: str, team: str
             ) -> Optional[Tuple[str, str]]:
    """How a Plunder Bay event reads from one bot's side."""
    by = str(event.get("by") or "somebody")
    me = bool(event.get("by")) and by == name
    ours = bool(team) and event.get("team") == team
    if kind == "pb_bank_big":
        what = str(event.get("what") or "a chest")
        if me:
            return ("You banked %s." % what, "actor")
        return ("%s banked %s%s." % (by, what, " for us" if ours else ""),
                "ally" if ours else "enemy")
    if kind == "pb_idol":
        if event.get("rose"):
            return ("The cursed idol has risen on its altar.", "neutral")
        if me:
            return ("You have the cursed idol.", "actor")
        return ("%s has the cursed idol%s." % (by, " -- cover them" if ours else ""),
                "ally" if ours else "enemy")
    if kind == "pb_raid":
        if me:
            return ("You stole gold out of their hold.", "actor")
        if ours:
            return ("%s raided their hold." % by, "ally")
        return ("%s is raiding our hold!" % by, "enemy")
    if kind == "pb_twist":
        return (_TWISTS.get(str(event.get("twist") or ""), "Something is happening!"), "neutral")
    if kind == "pb_lead":
        if ours:
            return ("We're in the lead now.", "ally")
        return ("They've taken the lead.", "enemy")
    return None


CANNED: Dict[Tuple[str, str], List[str]] = {
    ("pb_bank_big", "actor"): ["banked it", "ez gold", "chest in", "yarr", "loot secured"],
    ("pb_bank_big", "ally"): ["nice haul", "yarr", "gold!", "keep it coming"],
    ("pb_bank_big", "enemy"): ["they got a chest", "stop them", "ugh", "defend"],
    ("pb_idol", "neutral"): ["IDOL", "the idol!", "go go go", "idol's up"],
    ("pb_idol", "actor"): ["got the idol", "cover me", "help", "escort me"],
    ("pb_idol", "ally"): ["cover them", "escort", "protect the idol", "go go"],
    ("pb_idol", "enemy"): ["get the idol carrier", "stop them", "kill the idol guy"],
    ("pb_raid", "actor"): ["robbed em", "lol", "free gold", "yoink"],
    ("pb_raid", "ally"): ["nice raid", "yoink", "lol", "ez"],
    ("pb_raid", "enemy"): ["raiders!", "defend the ship", "hold!", "they're in the hold"],
    ("pb_twist", "neutral"): ["uh oh", "here we go", "yarr", "run", "lol"],
    ("pb_lead", "ally"): ["we're ahead", "keep going", "yarr", "nice"],
    ("pb_lead", "enemy"): ["we're behind", "come on", "need gold", "push"],
}

# ----------------------------------------------------------------- the bots
BOT_SECTION = ("plunder_bay", "Plunder Bay",
               "How bots play the treasure haul: how many dig and carry, how many raid the "
               "enemy hold or guard their own, how they fight and how they use the cannons.",
               "\U0001F3F4‍☠️")
BOT_INTRO = ("In Plunder Bay a bot is a hauler, a raider or a guard. Haulers go for the best "
             "treasure they can reach -- digging at an X, grabbing the idol -- and carry it "
             "home, tossing it to a crewmate when they are chased. Raiders hunt the other "
             "crew's carriers and slip into their hold to steal gold. Guards stay by their "
             "ship, cut down raiders and man the cannons. Everybody reacts to the twist.")
BOT_FIELDS: List[Tuple[Any, ...]] = [
    ("enabled", "Play the haul", "bool", True,
     "Bots dig, carry, raid and guard. Off: they wander and fight as in any world.",
     {"toggle": True}),
    ("haulers", "Haulers", "pct", 60,
     "The share of each crew's bots who go for treasure; the rest raid or guard. Explorer "
     "and collector personas haul most.",
     {"min": 0, "max": 100, "step": 1, "unit": "%", "scope": "base"}),
    ("raiding", "Raiding", "pct", 45,
     "Of the bots that do not haul, how many go raiding (the rest guard their ship); and how "
     "readily a raider slips into the enemy hold.",
     {"min": 0, "max": 100, "step": 1, "unit": "%", "scope": "base"}),
    ("aggression", "Aggression", "pct", 55,
     "How far a bot will chase a carrier of the other crew's treasure, and how readily it "
     "picks a fight while carrying something of its own.",
     {"min": 0, "max": 100, "step": 1, "unit": "%", "scope": "base"}),
    ("cannons", "Cannon fire", "pct", 50,
     "How readily a guard mans its ship's cannon when the other crew comes near.",
     {"min": 0, "max": 100, "step": 1, "unit": "%", "scope": "base"}),
    ("callouts", "Callouts", "bool", True,
     "Bots shout in quick chat as they play: yarr, got a chest, cover me, raiders!, idol's up. "
     "The language model's own reactions come from the speech events."),
]
PERSONA_TIES: List[Tuple[str, str]] = [
    ("Explorer, Collector", "Haul: dig every X and go for the idol."),
    ("Fragger, Tryhard, Toxic", "Raid: hunt carriers and rob the enemy hold."),
    ("Patient, Helpful, Wholesome", "Guard: stay by the ship, escort carriers, man the cannons."),
    ("Chaotic, Kid", "Do a bit of everything, toss treasure about, fire the cannon a lot."),
    ("Veteran, Sniper main", "Pick off carriers from range."),
    ("Social, Chatty", "Stick by a crewmate with a chest and catch whatever they toss."),
]
PERSONA_TAG = {"id": "pirate", "label": "Pirate",
               "prompt": "Loves Plunder Bay; talks like a pirate, never leaves a chest in the "
                         "sand, and would rather raid the other crew's hold than dig.",
               "weight": 0.9, "fx": {"w_plunder_bay": 2.4, "objective": 0.05}}
PROMPT = ("Plunder Bay is a pirate treasure haul on BLOCKHAVEN for two crews, the Scarlet "
          "Corsairs and the Azure Buccaneers: each crew's ship is moored at one end of an "
          "island, and they race to carry treasure into their own ship's hold -- doubloons, "
          "gold bars, jewels, chests dug up where X marks the spot, and the cursed idol late "
          "in the round. A chest takes both hands; a carrier who is cut down drops it; treasure "
          "can be tossed to a crewmate, and raiders steal from the other crew's hold. Everybody "
          "fights with their own weapons, and the ships have cannons. The places are "
          "Skull Cove (the tide goes out), the Coral Reef (a kraken), Port Royale (the redcoats "
          "march out) and Doubloon Isle (the volcano erupts gold). Players talk in short bursts, "
          "with a bit of pirate: 'yarr', 'got a chest', 'cover me', 'raiders!', 'idol's up', 'gg'.")
HISTORY = {"kills": 2.5, "deaths": 2.5, "round_minutes": 5.0, "win": 0.5}


def history_badges(history: Dict[str, Any], traits: Dict[str, float], rng
                   ) -> List[Tuple[str, int, str]]:
    """The badge stats a new bot's made-up Plunder Bay history earned."""
    rounds = int(history.get("rounds", 0) or 0)
    wins = int(history.get("wins", 0) or 0)
    if rounds <= 0:
        return []
    skill = float(traits.get("skill", 0.5))
    aggro = float(traits.get("aggression", 0.5))
    kills = int(history.get("kills", 0) or 0)
    out = [("pb_wins", wins, "add"),
           ("pb_plunder", int(rounds * rng.uniform(4.0, 18.0) * (0.5 + skill * 0.6)), "add"),
           ("pb_digs", int(rounds * rng.uniform(0.1, 1.2)), "add"),
           ("pb_chests", int(rounds * rng.uniform(0.05, 0.8) * (0.5 + skill * 0.5)), "add"),
           ("pb_idols", int(rounds * rng.uniform(0.0, 0.12)), "add"),
           ("pb_raids", int(rounds * rng.uniform(0.0, 0.6) * (0.4 + aggro)), "add"),
           ("pb_melee", int(kills * rng.uniform(0.3, 0.6)), "add"),
           ("pb_ranged", int(kills * rng.uniform(0.2, 0.5)), "add"),
           ("pb_cannon", int(rounds * rng.uniform(0.0, 1.0)), "add"),
           ("pb_catches", int(rounds * rng.uniform(0.0, 0.5)), "add"),
           ("pb_twists", int(rounds * rng.uniform(0.2, 1.5)), "add")]
    areas = [a["id"] for a in WORLD["areas"]]
    rng.shuffle(areas)
    for area in areas[:min(len(areas), wins // 3)]:
        out.append(("pb_area_" + area, 1, "max"))
    return out


# a haul runs five minutes, then the crews sail on: the tests need two hauls
TEST_SECONDS = 720.0

DORMANT = {"round_seconds": 300.0, "rounds_per_area": 1, "intermission": 15.0,
           "teams": ["red", "blue"], "kills": 2.5, "deaths": 2.5, "swap": False}
