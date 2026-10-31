"""Whodunit: a murder mystery in four grand old places.

Every guest arrives the same, and the roles are dealt in secret: a murderer
with a hidden knife, a detective with a revolver, and everybody else
innocent.  The murderer wins by leaving nobody standing; the detective wins
by shooting the murderer (and loses everything by shooting anybody else);
the innocents win by living out the clock and picking up the clues that
build the case file.  The rules are in app/game/worlds/whodunit.py and the
four places in app/game/maps/events/whodunit/.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

WORLD: Dict[str, Any] = {
    "id": "whodunit",
    "prefix": "wd",
    "name": "Whodunit",
    "genre": "Murder Mystery",
    "tagline": "Somebody here is the murderer. Nobody here will tell you.",
    "description": (
        "Everybody arrives a guest; nobody leaves the same. At the start of every round "
        "the roles are dealt in secret -- one murderer with a knife up their sleeve, one "
        "detective with a revolver and a single bullet in it at a time, and everybody else "
        "innocent. The murderer keeps the knife hidden until the moment they draw it, kills "
        "with one stab or throws it across a room, and wins by leaving nobody else standing. "
        "The detective wins by shooting the murderer -- and is disgraced on the spot for "
        "shooting anybody else, dropping the revolver for any innocent brave enough to pick "
        "it up. The innocents win by living out the clock, and by picking up the clues that "
        "turn up round the place: every clue goes in the shared case file, and the file "
        "gives up a hint -- where the murderer was seen, their footprints, three suspects, "
        "a glimpse -- each sharper than the last. The dead talk only to the dead. And each "
        "place has its twist: the storm puts the manor's lights out, the train goes "
        "through tunnels, the hotel's masked ball hides every face, and the liner sails "
        "into the fog."),
    "max_players": 16,
    "team_count": 0,
    "mode": "murder_mystery",
    "round_label": "One case",
    "colors": ["#c83a3a", "#3a7ac8", "#e8c860"],
    "thumb": "whodunit",
    "features": ["16 players", "Murder mystery", "Secret roles", "Hidden knife",
                 "Clues and hints", "4 twists", "4 rotating places"],
    "areas": [
        {"id": "manor", "name": "Blackwood Manor",
         "blurb": "A country house on a stormy night: a library with a secret door, a "
                  "grand hall, a hedge maze, a chapel and its crypt, and a tunnel from the "
                  "wine cellar to it. The storm puts the lights out."},
        {"id": "express", "name": "The Midnight Express",
         "blurb": "A sleeper train on the mountain line: the observation car, two sleeping "
                  "cars, the lounge, the dining car, the baggage car, the coal tender and the "
                  "engine -- and the roof, until the tunnel comes."},
        {"id": "hotel", "name": "The Grand Meridian",
         "blurb": "A city hotel holding a masked ball: the lobby and its grand stair, the "
                  "ballroom and its balcony, the bar, the kitchens, the guest rooms, the roof "
                  "garden under the great sign, and the fire escape down to the alley."},
        {"id": "liner", "name": "The SS Aurora",
         "blurb": "An ocean liner among the ice: the engine room, the swimming bath, the "
                  "staterooms, the dining saloon, the palm court, the boat deck and the "
                  "bridge -- and nothing but sea over the rail. Fog banks roll in."},
    ],
    "areas_note": "Two cases in each place, then the party moves on somewhere else.",
    "howto": [
        {"title": "Find out what you are",
         "text": "The roles are dealt in secret when the round starts: murderer, detective "
                 "or innocent. Only you know yours (a murderer in a big party knows their "
                 "partner)."},
        {"title": "The murderer",
         "text": "Your knife stays hidden until you draw it -- and a guest holding a knife "
                 "is a murderer, so pick your moment. One stab kills; R throws it across a "
                 "room, on a cooldown. Leave nobody else standing. Pick up a clue and you "
                 "burn it."},
        {"title": "The detective",
         "text": "One revolver, one shot, a slow reload. Shoot the murderer and the case is "
                 "closed. Shoot anybody else and you are disgraced -- out of the round, the "
                 "revolver on the floor for an innocent to pick up as the hero. The guests can "
                 "see you carry it; the murderer cannot, until you fire."},
        {"title": "The innocents",
         "text": "Live out the clock. Pick up clues: every one goes in the shared case file, "
                 "and enough of them give up a hint -- where the murderer was seen, their "
                 "glowing footprints, three suspects, a glimpse of them. Stick together; "
                 "a crowd is hard to murder."},
    ],
    "howto_note": "The kill feed never names the murderer, and the dead talk only to the "
                  "dead -- so watch who leaves the room, and who comes back alone.",
    "team_names": {},
}

# struck on a magnifying glass, the enamel in its lens and the handle
# running off to the bottom right
FAMILY = ("magnifier", {
    "mesh": "magnifier", "face": "#2a1a12", "ribbon": "#c83a3a", "wing": "#e8c860",
    "wing_mesh": "wing", "plate_size": [1.0, 1.0, 1.0], "plate_anchor": [0, 0, 0],
    "face_r": 0.36, "face_y": 0.0, "stripes": [],
})

BADGES: List[Tuple[Any, ...]] = [
    ("wd_case_closed", "Case Closed", "wd_wins", [1, 5, 15, 40, 100, 250],
     ["Guest", "Witness", "Sleuth", "Inspector", "Chief Inspector", "Great Detective"],
     "Were on the winning side of a case -- murderer or innocent.", "em_wd_glass",
     "cases won"),
    ("wd_cold_blooded", "Cold Blooded", "wd_kills", [1, 10, 40, 120, 300],
     ["Suspicious", "Sinister", "Cold Blooded", "Fiend", "Moriarty"],
     "Killed guests as the murderer.", "em_wd_knife", "murders"),
    ("wd_in_the_shadows", "In the Shadows", "wd_shadow", [1, 5, 20, 60, 150],
     ["Lurker", "Shade", "Phantom", "Unseen", "The Shadow"],
     "Struck while the lights were out, in a tunnel, behind a mask or in the fog.",
     "em_wd_shadow", "murders in the dark"),
    ("wd_knife_thrower", "Knife Thrower", "wd_throws", [1, 5, 20, 60, 150],
     ["Lucky Toss", "Dead Eye", "Knife Thrower", "Circus Act", "Never Misses"],
     "Killed a guest with a thrown knife.", "em_wd_throw", "throws"),
    ("wd_not_a_witness_left", "No Witnesses", "wd_spotless", [1, 3, 10, 25],
     ["Thorough", "Ruthless", "No Witnesses", "Perfect Crime"],
     "Won as the murderer after four kills or more.", "em_wd_spotless", "perfect crimes"),
    ("wd_elementary", "Elementary", "wd_solved", [1, 5, 20, 60, 150],
     ["Hunch", "Deduction", "Elementary", "Brilliant", "Master Detective"],
     "Shot the murderer.", "em_wd_revolver", "murderers caught"),
    ("wd_unlikely_hero", "Unlikely Hero", "wd_hero", [1, 3, 10, 25, 60],
     ["Bystander", "Brave Soul", "Unlikely Hero", "Avenger", "Legend"],
     "Picked up the dropped revolver and caught the murderer with it.", "em_wd_hero",
     "hero catches"),
    ("wd_last_minute", "Last Minute", "wd_close", [1, 3, 10, 25],
     ["Close Call", "Just in Time", "Last Minute", "Nerves of Steel"],
     "Caught the murderer with under ten seconds left on the clock.", "em_wd_clock",
     "last-minute catches"),
    ("wd_wrong_man", "The Wrong Man", "wd_wrong_man", [1, 3, 10, 25],
     ["Oops", "Trigger Happy", "The Wrong Man", "Disgraced"],
     "Shot an innocent as the detective. It happens.", "em_wd_oops", "wrong men"),
    ("wd_sharp_eyes", "Sharp Eyes", "wd_clues", [1, 10, 40, 120, 300, 800],
     ["Noticer", "Observer", "Sharp Eyes", "Bloodhound", "Eagle Eye", "All-Seeing"],
     "Picked up clues for the case file.", "em_wd_clue", "clues"),
    ("wd_still_breathing", "Still Breathing", "wd_survived", [1, 10, 40, 120, 300],
     ["Lucky", "Wary", "Still Breathing", "Unkillable", "Survivor"],
     "Lived out the clock as an innocent or the detective.", "em_wd_candle", "nights survived"),
    ("wd_every_scene", "Every Scene", "wd_areas", [1, 2, 3, 4],
     ["Visitor", "Traveller", "Globetrotter", "Every Scene"],
     "Won a case in each of Whodunit's four places.", "em_wd_map", "places"),
]

DERIVED = {"wd_areas": "wd_area_"}

# ------------------------------------------------------------------- speech
SPEECH: List[Tuple[str, str, int, str]] = [
    ("wd_body", "A body", 45,
     "Somebody was found murdered."),
    ("wd_caught", "Caught", 60,
     "The detective (or a hero) shot the murderer."),
    ("wd_misfire", "Wrong man", 60,
     "The detective shot an innocent and was disgraced."),
    ("wd_gun", "The revolver", 35,
     "The revolver was dropped, or picked up by an innocent."),
    ("wd_hint", "A hint", 35,
     "The case file gave up a hint about the murderer."),
    ("wd_escape", "Got away with it", 55,
     "The murderer won: nobody was left to stop them."),
]


def describe(kind: str, event: Dict[str, Any], name: str, team: str
             ) -> Optional[Tuple[str, str]]:
    """How a Whodunit event reads from one bot's side (nobody has a team)."""
    by = str(event.get("by") or "somebody")
    me = bool(event.get("by")) and by == name
    del team
    if kind == "wd_body":
        victim = str(event.get("victim") or "somebody")
        where = str(event.get("where") or "")
        if victim == name:
            return ("You were murdered%s. You can only talk to the dead now." % (
                " in " + where if where else ""), "victim")
        return ("%s was found dead%s. The murderer is still among you." % (
            victim, " in " + where if where else ""), "neutral")
    if kind == "wd_caught":
        who = str(event.get("who") or "the murderer")
        if me:
            return ("You shot %s -- and they were the murderer. Case closed." % who, "actor")
        if who == name:
            return ("%s shot you. They had you." % by, "victim")
        return ("%s shot %s, and %s was the murderer." % (by, who, who), "neutral")
    if kind == "wd_misfire":
        victim = str(event.get("victim") or "somebody")
        if me:
            return ("You shot %s, and they were innocent. You are disgraced." % victim, "victim")
        if victim == name:
            return ("The detective %s shot you by mistake." % by, "victim")
        return ("The detective %s shot %s, who was innocent. The revolver is on the floor."
                % (by, victim), "neutral")
    if kind == "wd_gun":
        if event.get("dropped"):
            where = str(event.get("where") or "")
            return ("The revolver is on the floor%s. Somebody brave should pick it up." % (
                " in " + where if where else ""), "neutral")
        if me:
            return ("You picked up the revolver. You are the hero now.", "actor")
        return ("%s picked up the revolver." % by, "neutral")
    if kind == "wd_hint":
        hint = str(event.get("hint") or "")
        text = {"seen": "The case file says where the murderer was just seen.",
                "trail": "The murderer's footprints are glowing.",
                "suspects": "The case file names three suspects.",
                "glimpse": "The murderer stands out for a moment."}.get(hint, "A new hint.")
        return (text, "neutral")
    if kind == "wd_escape":
        who = str(event.get("who") or "the murderer")
        if who == name or name in who.split(" and "):
            return ("You got away with it.", "actor")
        return ("%s got away with it." % who, "victim")
    return None


CANNED: Dict[Tuple[str, str], List[str]] = {
    ("wd_body", "neutral"): ["a body!", "who did that", "stick together", "nobody move",
                             "where was everyone", "it wasnt me"],
    ("wd_body", "victim"): ["rip", "didnt even see them", "how", "i trusted you", "noo"],
    ("wd_caught", "actor"): ["got them", "case closed", "elementary", "knew it", "gg"],
    ("wd_caught", "victim"): ["how did you know", "gg", "unlucky", "nice shot"],
    ("wd_caught", "neutral"): ["nice shot!", "called it", "finally", "gg", "knew it was them"],
    ("wd_misfire", "victim"): ["oops", "WHY", "it wasnt them??", "my bad", "rip"],
    ("wd_misfire", "neutral"): ["wrong guy lol", "unlucky", "the gun!", "who grabs it",
                                "detective down"],
    ("wd_gun", "actor"): ["got the gun", "im the hero", "nobody move"],
    ("wd_gun", "neutral"): ["gun's down", "grab it", "who has the gun"],
    ("wd_hint", "neutral"): ["new hint", "check the case file", "suspects!", "follow the trail",
                             "theres the footprints"],
    ("wd_escape", "actor"): ["ez", "nobody saw a thing", "gg", "too easy"],
    ("wd_escape", "victim"): ["gg", "how did nobody catch them", "it was them all along",
                              "next time"],
}

# ----------------------------------------------------------------- the bots
BOT_SECTION = ("whodunit", "Whodunit",
               "How bots play the murder mystery: how the murderer hunts, how the detective "
               "decides, what witnesses see and say.", "\U0001F50E")
BOT_INTRO = ("In Whodunit a bot plays the role it is dealt. A murderer picks off guests who "
             "are on their own, keeps the knife hidden until the moment, throws it when "
             "nobody is looking and burns the clues; a detective follows the case file and "
             "the witnesses and shoots when it is sure enough; an innocent collects clues, "
             "keeps to a crowd, runs from anybody it has seen with a knife and grabs a "
             "dropped revolver if it is brave enough.")
BOT_FIELDS: List[Tuple[Any, ...]] = [
    ("enabled", "Play the mystery", "bool", True,
     "Bots play their roles: murderers hunt, detectives hunt the murderer, innocents "
     "collect clues and keep together. Off: they wander as in any world.", {"toggle": True}),
    ("trigger", "Detective's trigger", "pct", 45,
     "How sure a bot detective must be before it shoots. Higher shoots sooner -- and gets "
     "the wrong man more often.",
     {"min": 0, "max": 100, "step": 1, "unit": "%", "scope": "base"}),
    ("eyes", "Witness eyes", "pct", 60,
     "How far away a bot can see a murder (or a drawn knife) and know who did it; "
     "observant and veteran personas most.",
     {"min": 0, "max": 100, "step": 1, "unit": "%", "scope": "base"}),
    ("stealth", "Murderer's patience", "pct", 55,
     "How long a bot murderer waits for a guest to be alone before it strikes; patient and "
     "sniper personas most.",
     {"min": 0, "max": 100, "step": 1, "unit": "%", "scope": "base"}),
    ("throw", "Knife throws", "pct", 50,
     "How often a bot murderer throws the knife from across a room instead of walking up.",
     {"min": 0, "max": 100, "step": 1, "unit": "%", "scope": "base"}),
    ("bravery", "Bravery", "pct", 40,
     "How readily an innocent bot goes for a dropped revolver, and stays with a friend "
     "instead of running.",
     {"min": 0, "max": 100, "step": 1, "unit": "%", "scope": "base"}),
    ("trust", "Trust", "pct", 50,
     "How much a bot believes another guest who names the murderer in chat.",
     {"min": 0, "max": 100, "step": 1, "unit": "%", "scope": "base"}),
    ("callouts", "Callouts", "bool", True,
     "Bots shout what they see in quick chat: its them, a mask did it, body -- run, stick "
     "together, getting the gun, a detective's don't move, and a cornered murderer's not me. "
     "The language model's own reactions come from the speech events."),
]
PERSONA_TIES: List[Tuple[str, str]] = [
    ("Veteran, Sniper main, Patient",
     "Patient murderers who wait for a guest to be alone; careful detectives who rarely "
     "shoot the wrong man."),
    ("Fragger, Shotgun rusher, Jumpy",
     "Quick to draw and quick to shoot: bold murderers, trigger-happy detectives."),
    ("Helpful, Wholesome, Support",
     "Stick to the crowd, collect clues for the case file, and call out what they see."),
    ("Kid, Chaotic", "Panic, run and accuse everybody; easy marks for a murderer."),
    ("Explorer", "Roam the whole place for clues -- and end up alone in the cellar."),
    ("Armchair detective", "Loves Whodunit: reads the hints, trusts nobody, and is right "
     "more often than not."),
]
PERSONA_TAG = {"id": "armchair_detective", "label": "Armchair detective",
               "prompt": "Loves Whodunit; reads every clue, trusts nobody, and is right about "
                         "the murderer more often than not.",
               "weight": 0.9, "fx": {"w_whodunit": 2.4, "objective": 0.05}}
PROMPT = ("Whodunit is a murder mystery on BLOCKHAVEN: every player is a guest, and the roles "
          "are dealt in secret -- one murderer with a hidden knife (they can throw it too), "
          "one detective with a revolver, everyone else innocent. The murderer wins by "
          "killing everybody; the detective wins by shooting the murderer but is disgraced "
          "for shooting an innocent (an innocent can pick the revolver up and be the hero); "
          "the innocents win by surviving the clock. Clues build a shared case file that "
          "gives hints. The places are Blackwood Manor (a storm puts the lights out), the "
          "Midnight Express (a sleeper train that goes through tunnels), the Grand Meridian "
          "(a hotel's masked ball) and the SS Aurora (an ocean liner in the fog). The dead "
          "talk only to the dead. Players talk in short bursts: 'sus', 'its them', 'who has "
          "the gun', 'stick together', 'not me', 'i saw nothing', 'case closed'.")
HISTORY = {"kills": 0.4, "deaths": 0.7, "round_minutes": 3.2, "win": 0.55}


def history_badges(history: Dict[str, Any], traits: Dict[str, float], rng
                   ) -> List[Tuple[str, int, str]]:
    """The badge stats a new bot's made-up Whodunit history earned."""
    rounds = int(history.get("rounds", 0) or 0)
    wins = int(history.get("wins", 0) or 0)
    if rounds <= 0:
        return []
    skill = float(traits.get("skill", 0.5))
    aggro = float(traits.get("aggression", 0.5))
    support = float(traits.get("support", 0.2))
    # one round in eight a murderer, one in eight a detective, the rest innocent
    murders = int(rounds / 8.0 * rng.uniform(0.8, 2.6) * (0.5 + skill))
    caught = int(rounds / 8.0 * rng.uniform(0.15, 0.55) * (0.5 + skill))
    out = [("wd_wins", wins, "add"),
           ("wd_kills", murders, "add"),
           ("wd_shadow", int(murders * rng.uniform(0.1, 0.35)), "add"),
           ("wd_throws", int(murders * rng.uniform(0.05, 0.25) * (0.5 + aggro)), "add"),
           ("wd_spotless", int(rounds / 8.0 * rng.uniform(0.0, 0.15) * (0.4 + skill)), "add"),
           ("wd_solved", caught, "add"),
           ("wd_hero", int(rounds * rng.uniform(0.0, 0.02) * (0.4 + skill)), "add"),
           ("wd_close", int(caught * rng.uniform(0.0, 0.15)), "add"),
           ("wd_wrong_man", int(rounds / 8.0 * rng.uniform(0.05, 0.3) * (0.5 + aggro)), "add"),
           ("wd_clues", int(rounds * rng.uniform(0.4, 2.2) * (0.5 + support)), "add"),
           ("wd_survived", int(rounds * 0.75 * rng.uniform(0.25, 0.55) * (0.6 + skill * 0.6)),
            "add")]
    areas = [a["id"] for a in WORLD["areas"]]
    rng.shuffle(areas)
    for area in areas[:min(len(areas), wins // 3)]:
        out.append(("wd_area_" + area, 1, "max"))
    return out


# a case runs about three minutes and a place has two: the tests need this
# long to see the party move on
TEST_SECONDS = 480.0

DORMANT = {"round_seconds": 190.0, "rounds_per_area": 2, "intermission": 16.0,
           "teams": ["ffa"], "kills": 0.4, "deaths": 0.7, "swap": False}
