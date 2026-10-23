"""Calamity Coast: survive the disaster, in four towns having a very bad day.

Two teams of rescuers ride out three disasters a round -- a tsunami, a
blizzard, an eruption, a great fire -- scoring for everybody still standing
when each one passes and for every stranded townsperson carried to the
evacuation point.  Nobody can hurt anybody: the town does all the hurting.
The rules are in app/game/worlds/calamity_coast.py and the four towns in
app/game/maps/events/calamity_coast/.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

WORLD: Dict[str, Any] = {
    "id": "calamity_coast",
    "prefix": "cc",
    "name": "Calamity Coast",
    "genre": "Disaster Survival",
    "tagline": "The siren means run. The tsunami means up. The rest you work out.",
    "description": (
        "Four towns, and every one of them is about to have a very bad day. Each round "
        "is three disasters, one after another: the next one is named in a short calm, "
        "the siren sounds, and then it hits -- a tsunami over the harbour wall, a "
        "tornado down the high street, an avalanche off the peak, lava out of the "
        "volcano, a great fire leaping from roof to roof. Everybody still standing when "
        "it passes scores for their team. In the calm, supply crates drop (a life ring, "
        "a hard hat, a raincoat, running shoes) and townsfolk get stranded in the worst "
        "places: pick one up and carry them to the helipad for a big score of your own. "
        "Nobody can hurt anybody -- the town does all the hurting -- so it is all about "
        "reading the disaster and getting to the right place: up high for water, under "
        "a roof for things falling from the sky, out in the open when the ground shakes."),
    "max_players": 16,
    "team_count": 2,
    "mode": "disaster_survival",
    "round_label": "Three disasters",
    "colors": ["#e8502a", "#2a8ad8", "#f2c230"],
    "thumb": "calamity_coast",
    "features": ["16 players", "Disaster survival", "16 disasters", "No PvP",
                 "Rescue the townsfolk", "Power-up crates", "4 rotating towns"],
    "areas": [
        {"id": "portsunny", "name": "Port Sunny",
         "blurb": "A seaside town climbing four terraces up from the harbour, with a "
                  "lighthouse, a church belfry and a water tower. Tsunami, lightning "
                  "storm, meteor shower and a tornado down the high street."},
        {"id": "summit", "name": "Summit Village",
         "blurb": "A ski village on a mountainside: a lodge with a roaring fire, a rope "
                  "bridge over the gorge, a mine, a frozen lake and a cable car to the "
                  "peak. Avalanche, blizzard, earthquake and rockslide."},
        {"id": "palmkey", "name": "Palm Key",
         "blurb": "A tropical resort under a smoking volcano: a temple in the jungle, a "
                  "hotel, bungalows on stilts and a long pier. Eruption, hurricane, "
                  "tsunami and sinkholes opening in the lawns."},
        {"id": "oldtown", "name": "Old Town",
         "blurb": "A river town of timbered houses round a market square, with a "
                  "cathedral under scaffolding and a castle on the hill. Earthquake, the "
                  "great fire, the river in flood and a hailstorm."},
    ],
    "areas_note": "Two rounds in each town -- six disasters, never the same three twice "
                  "running -- then the server moves on somewhere else.",
    "howto": [
        {"title": "Read the disaster",
         "text": "The next disaster is named in the calm before it, with a hint. Water "
                 "rising? Get up high. Things falling from the sky? Get under a roof. The "
                 "ground shaking? Out into the open, away from walls. Snow and wind? "
                 "Indoors or by a fire."},
        {"title": "Survive for your team",
         "text": "When the siren stops and the disaster passes, everybody on their feet "
                 "scores for their team. The fallen watch until the next calm, then come "
                 "back. Three disasters make a round; the team with more points wins it."},
        {"title": "Rescue the townsfolk",
         "text": "In the calm, townsfolk get stranded in bad places. Hold E by one to pick "
                 "them up and carry them to the helipad (you walk slower). A rescue is "
                 "worth more than surviving -- if you make it."},
        {"title": "Grab the crates",
         "text": "Supply crates drop in the calm: a life ring floats you in water, a hard "
                 "hat stops one hit from above, a raincoat keeps out the cold and the "
                 "hail, running shoes make you quick. The crates lean towards what is "
                 "coming next."},
    ],
    "howto_note": "Nobody can hurt anybody here: the guns are for show. The town does all "
                  "the hurting, and a roof is anything solid over your head.",
    "team_names": {"red": "Lifeguards", "blue": "Rangers"},
}

# struck on a life ring, the enamel in the middle
FAMILY = ("lifebuoy", {
    "mesh": "ring", "face": "#0d2a4a", "ribbon": "#e8502a", "wing": "#f2f3f3",
    "wing_mesh": "wing", "plate_size": [1.24, 0.9, 1.24], "plate_r": [1.5708, 0, 0],
    "face_r": 0.46, "face_y": 0.0, "stripes": [],
})

BADGES: List[Tuple[Any, ...]] = [
    ("cc_storm_chasers", "Storm Chasers", "cc_wins", [1, 5, 15, 40, 100, 250],
     ["Volunteer", "Rescuer", "Responder", "Captain", "Commander", "Legend of the Coast"],
     "Won rounds of Calamity Coast with your team.", "em_cc_siren", "rounds won"),
    ("cc_still_standing", "Still Standing", "cc_survived", [1, 10, 40, 120, 300, 800],
     ["Lucky", "Hardy", "Tough", "Unshakeable", "Unbreakable", "Force of Nature"],
     "Were on your feet when a disaster passed.", "em_cc_stand", "disasters survived"),
    ("cc_high_water", "High Water", "cc_floods", [1, 5, 20, 60, 150],
     ["Paddler", "Swimmer", "High and Dry", "Wave Rider", "Tide Master"],
     "Survived a tsunami, a flood or a flood of lava.", "em_cc_wave", "floods survived"),
    ("cc_eye_of_storm", "Eye of the Storm", "cc_storms", [1, 5, 20, 60, 150],
     ["Windswept", "Weathered", "Storm Chaser", "Twister Tamer", "Eye of the Storm"],
     "Survived a tornado or a hurricane.", "em_cc_twister", "storms survived"),
    ("cc_cold_feet", "Cold Feet", "cc_cold", [1, 5, 20, 60, 150],
     ["Chilly", "Frosty", "Snowbound", "Iceborn", "Yeti"],
     "Survived a blizzard or an avalanche.", "em_cc_snow", "freezes survived"),
    ("cc_on_shaky_ground", "On Shaky Ground", "cc_quakes", [1, 5, 20, 60, 150],
     ["Wobbly", "Steady", "Rock Solid", "Seismologist", "Richter Ten"],
     "Survived an earthquake or the sinkholes.", "em_cc_quake", "quakes survived"),
    ("cc_firewalker", "Firewalker", "cc_fires", [1, 5, 20, 60, 150],
     ["Singed", "Smoky", "Firewalker", "Fireproof", "Phoenix"],
     "Survived the great fire.", "em_cc_flame", "fires survived"),
    ("cc_not_a_scratch", "Not a Scratch", "cc_unscathed", [1, 5, 20, 60, 150],
     ["Careful", "Untouched", "Not a Scratch", "Pristine", "Invincible"],
     "Came through a disaster without losing any health at all.", "em_cc_shield",
     "clean escapes"),
    ("cc_last_one_standing", "Last One Standing", "cc_last_one", [1, 3, 10, 25],
     ["Survivor", "Holdout", "Sole Survivor", "Last One Standing"],
     "Were the only one left standing when a disaster passed.", "em_cc_last",
     "last stands"),
    ("cc_lightning_rod", "Lightning Rod", "cc_lightning", [1, 3, 10, 25, 60],
     ["Zapped", "Grounded", "Lightning Rod", "Thunderhead", "Storm King"],
     "Took a lightning strike on your hard hat and walked away.", "em_cc_bolt",
     "strikes shrugged off"),
    ("cc_lifesaver", "Lifesaver", "cc_rescues", [1, 10, 40, 120, 300, 800],
     ["Helper", "Lifesaver", "Rescuer", "Guardian", "Saviour", "Patron Saint"],
     "Carried stranded townsfolk to the evacuation point.", "em_cc_buoy", "rescues"),
    ("cc_hero_of_the_hour", "Hero of the Hour", "cc_hero", [1, 5, 15, 40, 100],
     ["Brave", "Hero", "Hero of the Hour", "Hero of the Town", "Hero of the Coast"],
     "Made three rescues or more in one round.", "em_cc_medal", "hero rounds"),
    ("cc_supply_run", "Supply Run", "cc_crates", [1, 10, 40, 120, 300],
     ["Picker", "Scrounger", "Quartermaster", "Supply Chief", "Logistics"],
     "Opened supply crates.", "em_cc_crate", "crates"),
    ("cc_every_town", "Every Town", "cc_areas", [1, 2, 3, 4],
     ["Visitor", "Traveller", "Knows the Coast", "Saved Them All"],
     "Won a round in each of Calamity Coast's four towns.", "em_cc_map", "towns"),
]

DERIVED = {"cc_areas": "cc_area_"}

# ------------------------------------------------------------------- speech
SPEECH: List[Tuple[str, str, int, str]] = [
    ("cc_siren", "The siren", 35,
     "The calm is ending: the siren sounds and the next disaster is named."),
    ("cc_hit", "Disaster strikes", 30,
     "The disaster hits the town."),
    ("cc_passed", "It passed", 40,
     "The disaster is over; everyone standing scores."),
    ("cc_down", "Taken out", 40,
     "Somebody was taken out by the disaster."),
    ("cc_rescue", "Rescue", 40,
     "Somebody carried a stranded townsperson to safety."),
]


def describe(kind: str, event: Dict[str, Any], name: str, team: str
             ) -> Optional[Tuple[str, str]]:
    """How a Calamity Coast event reads from one bot's side."""
    by = str(event.get("by") or "somebody")
    me = bool(event.get("by")) and by == name
    mine = bool(team) and str(event.get("by_team") or "") == team
    what = str(event.get("what") or "the disaster")
    if kind == "cc_siren":
        return ("The siren is going: %s is coming. Get somewhere safe." % what, "neutral")
    if kind == "cc_hit":
        return ("%s just hit the town." % what, "neutral")
    if kind == "cc_passed":
        red, blue = int(event.get("red", 0) or 0), int(event.get("blue", 0) or 0)
        ours = red if team == "red" else blue
        theirs = blue if team == "red" else red
        if ours > theirs:
            return ("%s passed. More of your team are still standing (%d to %d)." % (
                what, ours, theirs), "actor")
        if ours < theirs:
            return ("%s passed, but more of the other team made it (%d to %d)." % (
                what, theirs, ours), "victim")
        return ("%s passed. Phew." % what, "neutral")
    if kind == "cc_down":
        if me:
            return ("You were taken out by %s. You are watching until the next calm." % what,
                    "victim")
        if mine:
            return ("Your teammate %s was taken out by %s." % (by, what), "victim")
        return ("%s from the other team was taken out by %s." % (by, what), "ally")
    if kind == "cc_rescue":
        if me:
            return ("You carried a stranded townsperson to the evacuation point.", "actor")
        if mine:
            return ("Your teammate %s rescued somebody." % by, "ally")
        return ("%s from the other team rescued somebody." % by, "victim")
    return None


CANNED: Dict[Tuple[str, str], List[str]] = {
    ("cc_siren", "neutral"): ["here it comes", "siren!", "get safe", "high ground", "go go go",
                              "where do we go"],
    ("cc_hit", "neutral"): ["AAA", "hold on", "its here", "dont move", "omg"],
    ("cc_passed", "actor"): ["we made it", "ez", "still standing", "survived lol", "next"],
    ("cc_passed", "victim"): ["close one", "we lost some", "regroup", "next one"],
    ("cc_passed", "neutral"): ["phew", "made it", "that was close", "next"],
    ("cc_down", "victim"): ["rip", "noo", "i got wrecked", "how", "the town hates me"],
    ("cc_down", "ally"): ["rip them", "lol", "one less"],
    ("cc_rescue", "actor"): ["saved one", "got them out", "rescue!", "evac done"],
    ("cc_rescue", "ally"): ["nice save", "hero", "gj", "keep saving"],
    ("cc_rescue", "victim"): ["they got one", "our turn", "get the next one"],
}

# ----------------------------------------------------------------- the bots
BOT_SECTION = ("calamity_coast", "Calamity Coast",
               "How bots ride out the disasters: where they shelter, how they dodge, "
               "rescues and crates.", "\U0001F30A")
BOT_INTRO = ("In Calamity Coast a bot reads the coming disaster and heads for the right "
             "kind of place -- up high for water, under a roof for strikes and hail, out "
             "in the open for a quake, by a fire in a blizzard -- dodges warning circles "
             "and funnels, and by its role carries stranded townsfolk to the evacuation "
             "point or goes for the supply crates.")
BOT_FIELDS: List[Tuple[Any, ...]] = [
    ("enabled", "Play the disasters", "bool", True,
     "Bots shelter, dodge, rescue and loot crates. Off: they wander as in any world (the "
     "disasters still hit them).", {"toggle": True}),
    ("rescuers", "Rescuers", "pct", 55,
     "How many bots take the rescuer's job -- fetching stranded townsfolk to the "
     "evacuation point in the calm; support and objective personas most.",
     {"min": 0, "max": 100, "step": 1, "unit": "%", "scope": "base"}),
    ("scavengers", "Scavengers", "pct", 45,
     "How many bots go for the supply crates in the calm; explorers and chaotic personas "
     "most.", {"min": 0, "max": 100, "step": 1, "unit": "%", "scope": "base"}),
    ("bravery", "Brave rescues", "pct", 30,
     "How readily a rescuer goes out for somebody while the disaster is still raging.",
     {"min": 0, "max": 100, "step": 1, "unit": "%", "scope": "base"}),
    ("dodge", "Dodge", "pct", 70,
     "How sharp a bot is at getting out from under a warning circle or away from a "
     "funnel; skilled personas most.",
     {"min": 0, "max": 100, "step": 1, "unit": "%", "scope": "base"}),
    ("callouts", "Callouts", "bool", True,
     "Bots shout the round's moments in quick chat: high ground, get inside, incoming, "
     "got one, crate! The language model's own reactions come from the speech events."),
]
PERSONA_TIES: List[Tuple[str, str]] = [
    ("Helpful, Wholesome, Support",
     "Rescuers: fetch the stranded townsfolk and call out where the evac is."),
    ("Explorer, Chaotic", "Scavengers: race for the supply crates in every calm."),
    ("Veteran, Sniper main, Patient",
     "Read the disaster early and get to the best spot first; dodge cleanly."),
    ("Kid, Jumpy", "Panic a little: late to cover, quick on their feet."),
    ("Fragger, Shotgun rusher",
     "Nothing to shoot here -- they turn their speed to brave rescues."),
    ("Storm chaser", "Loves the disasters: knows every town's safe spots and goes out "
     "for rescues while it is still raging."),
]
PERSONA_TAG = {"id": "storm_chaser", "label": "Storm chaser",
               "prompt": "Loves Calamity Coast; knows where to stand for every tsunami, "
                         "tornado and avalanche, and goes out for the stranded mid-storm.",
               "weight": 0.9, "fx": {"w_calamity_coast": 2.4, "objective": 0.05}}
PROMPT = ("Calamity Coast is disaster survival on BLOCKHAVEN: two teams, the Lifeguards "
          "(red) and the Rangers (blue), ride out three disasters a round in one of four "
          "towns -- Port Sunny (tsunami, lightning, meteors, a tornado), Summit Village "
          "(avalanche, blizzard, earthquake, rockslide), Palm Key (eruption, hurricane, "
          "tsunami, sinkholes) and Old Town (earthquake, the great fire, a flood, hail). "
          "Everybody still standing when a disaster passes scores for their team, and "
          "carrying stranded townsfolk to the helipad scores more. Supply crates give a "
          "life ring, a hard hat, a raincoat or running shoes. Nobody can hurt anybody: "
          "the town does all the hurting. Players talk in short bursts: 'high ground', "
          "'get inside', 'incoming', 'got one', 'crate', 'close one', 'evac'.")
HISTORY = {"kills": 0.0, "deaths": 0.5, "round_minutes": 3.6, "win": 0.5}


def history_badges(history: Dict[str, Any], traits: Dict[str, float], rng
                   ) -> List[Tuple[str, int, str]]:
    """The badge stats a new bot's made-up Calamity Coast history earned."""
    rounds = int(history.get("rounds", 0) or 0)
    wins = int(history.get("wins", 0) or 0)
    if rounds <= 0:
        return []
    skill = float(traits.get("skill", 0.5))
    support = float(traits.get("support", 0.2))
    explore = float(traits.get("explore", 0.2))
    survived = int(rounds * 3 * rng.uniform(0.35, 0.75) * (0.6 + skill * 0.6))
    # each town has its own kinds of disaster: a quarter of the rounds each
    town = rounds / 4.0
    out = [("cc_wins", wins, "add"),
           ("cc_survived", survived, "add"),
           ("cc_floods", int(town * 2.0 * rng.uniform(0.3, 0.7)), "add"),
           ("cc_storms", int(town * 1.5 * rng.uniform(0.3, 0.7)), "add"),
           ("cc_cold", int(town * 1.5 * rng.uniform(0.3, 0.7)), "add"),
           ("cc_quakes", int(town * 2.0 * rng.uniform(0.3, 0.7)), "add"),
           ("cc_fires", int(town * 0.7 * rng.uniform(0.3, 0.7)), "add"),
           ("cc_unscathed", int(survived * rng.uniform(0.1, 0.3) * (0.5 + skill)), "add"),
           ("cc_last_one", int(rounds * rng.uniform(0.0, 0.04) * (0.4 + skill)), "add"),
           ("cc_lightning", int(town * rng.uniform(0.0, 0.25)), "add"),
           ("cc_rescues", int(rounds * rng.uniform(0.1, 1.0) * (0.3 + support * 1.5)), "add"),
           ("cc_hero", int(rounds * rng.uniform(0.0, 0.08) * (0.2 + support)), "add"),
           ("cc_crates", int(rounds * rng.uniform(0.3, 1.6) * (0.4 + explore)), "add")]
    areas = [a["id"] for a in WORLD["areas"]]
    rng.shuffle(areas)
    for area in areas[:min(len(areas), wins // 3)]:
        out.append(("cc_area_" + area, 1, "max"))
    return out


# a round is three disasters (a little over three minutes) and a town has
# two: the tests need this long to see the server move on
TEST_SECONDS = 520.0

DORMANT = {"round_seconds": 200.0, "rounds_per_area": 2, "intermission": 15.0,
           "teams": ["red", "blue"], "kills": 0.0, "deaths": 0.5, "swap": False}
