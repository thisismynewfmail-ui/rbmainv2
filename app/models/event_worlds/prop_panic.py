"""Prop Panic: prop hunt in four places full of things.

Each round one team hides as the furniture -- a teapot, a teddy bear, a
cereal box, a suit of armour -- and the other team seeks with poppers that
punish a wrong guess.  The teams swap every round, so everybody hides and
seeks in every place.  Each place has a twist of its own: Grandma's cat,
the toy shop's power cuts, the supermarket's flash sales and the museum's
searchlight.  The rules are in app/game/worlds/prop_panic.py.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

WORLD: Dict[str, Any] = {
    "id": "prop_panic",
    "prefix": "pp",
    "name": "Prop Panic",
    "genre": "Prop Hunt",
    "tagline": "Be the teapot. Fool the hunters. Don't move when the cat is looking.",
    "description": (
        "Half the server are furniture and the other half are trying to work out "
        "which furniture. Hiders look at anything in the room -- a teapot, a teddy "
        "bear, a cereal box, a suit of armour -- and press E to become it, then find "
        "somewhere it belongs and keep very, very still. Seekers wait in the pen "
        "with their eyes shut, then come out with prop poppers: pop a hider and you "
        "heal, pop a real lamp and it hurts. Hiders can taunt for points, leave "
        "decoys and scurry when they are rumbled; seekers sniff, glitter-bomb and "
        "listen. The teams swap every round, and there are four places to play: "
        "Grandma's Cottage (mind the cat), Tinker's Toy Emporium (mind the power "
        "cuts), the MegaMart (mind the flash sales) and the Museum after dark (mind "
        "the searchlight)."),
    "max_players": 16,
    "team_count": 2,
    "mode": "prop_hunt",
    "round_label": "Hide and seek",
    "colors": ["#e85a7a", "#3a8ad8", "#f2c230"],
    "thumb": "prop_panic",
    "features": ["16 players", "Prop hunt", "Swap sides every round", "78 disguises",
                 "Taunts, decoys and glitter", "4 rotating places", "A twist in every place"],
    "areas": [
        {"id": "grandma", "name": "Grandma's Cottage",
         "blurb": "Two floors of armchairs, teapots and grandfather clocks, a garden "
                  "full of gnomes and a treehouse. Grandma's cat Mittens wanders about "
                  "and stops to stare at anything that is not what it seems."},
        {"id": "toyshop", "name": "Tinker's Toy Emporium",
         "blurb": "A two-floor toy shop of teddy bears, building blocks and rocking "
                  "horses, with a train set, a ball pit and a stockroom. Every so often "
                  "the power goes and the seekers have only their torches."},
        {"id": "megamart", "name": "MegaMart",
         "blurb": "Aisles of cereal boxes and giant sodas, a produce hall, a garden "
                  "centre and a car park of trolleys. The tannoy calls flash sales, and "
                  "everything of that kind gets a price tag over it."},
        {"id": "museum", "name": "The Museum After Dark",
         "blurb": "A T. rex under a glass lantern, mummies and a pyramid, armour, "
                  "rockets, vases and clocks on two floors round the great hall, and a "
                  "hedge maze outside. The night watchman's searchlight sweeps the "
                  "great hall: move in its beam and the alarm goes off."},
    ],
    "areas_note": "Two rounds in each place -- one hiding, one seeking -- then the server "
                  "moves on somewhere else.",
    "howto": [
        {"title": "Hiders: become the furniture",
         "text": "Look at anything in the room and press E to turn into it. R turns you a "
                 "quarter. Small things are hard to spot but break easily; big things "
                 "take more hits. Find somewhere you belong and stay still."},
        {"title": "Taunt, decoy, scurry",
         "text": "Your taunt is worth points -- more the closer the seekers are -- but "
                 "they hear it. A decoy leaves a copy of you behind. Scurry is a burst of "
                 "speed for when you are rumbled."},
        {"title": "Seekers: pop the right prop",
         "text": "You start in the pen with your eyes shut. Your popper heals you when it "
                 "hits a hider and hurts you when it hits a real prop. The sniffer makes "
                 "the nearest hider squeak; a glitter bomb shows who is not what they seem."},
        {"title": "Every place has a twist",
         "text": "Mittens the cat stares at hiders in Grandma's Cottage; the toy shop's "
                 "power cuts out; MegaMart's flash sales put price tags on one kind of "
                 "thing; the museum's searchlight sets off the alarm on anything moving."},
    ],
    "howto_note": "Seekers win by finding every hider before the clock runs out. One hider "
                  "left standing wins it for the hiders. In the last minute the house "
                  "creaks and every hider squeaks.",
    "team_names": {"red": "Dust Bunnies", "blue": "Feather Dusters"},
}

FAMILY = ("mask", {
    "mesh": "mask", "face": "#2a163a", "ribbon": "#e85a7a", "wing": "#f2c230",
    "wing_mesh": "wing", "plate_size": [1.34, 1.0, 0.9], "plate_y": -0.06, "face_r": 0.27,
    "face_y": 0.04, "stripes": [],
})

BADGES: List[Tuple[Any, ...]] = [
    ("pp_house_rules", "House Rules", "pp_wins", [1, 5, 15, 40, 100, 250],
     ["Houseguest", "Lodger", "Tenant", "Landlord", "Lord of the Manor", "Master of the House"],
     "Won rounds of Prop Panic with your team, hiding or seeking.", "em_pp_house", "rounds won"),
    ("pp_still_life", "Still Life", "pp_survived", [1, 5, 20, 50, 120, 300],
     ["Ornament", "Fixture", "Furniture", "Heirloom", "Antique", "Part of the House"],
     "Hid it out to the end of a round without being found.", "em_pp_still", "rounds survived"),
    ("pp_eagle_eye", "Eagle Eye", "pp_found", [1, 10, 40, 120, 300, 800],
     ["Looker", "Spotter", "Sharp Eye", "Hawk", "Eagle Eye", "All-Seeing"],
     "Found hiders as a seeker.", "em_pp_eye", "hiders found"),
    ("pp_show_off", "Show-Off", "pp_taunts", [5, 40, 150, 400, 1000, 2500],
     ["Squeaker", "Whistler", "Show-Off", "Loudmouth", "Diva", "Headliner"],
     "Taunted the seekers while you were hiding.", "em_pp_horn", "taunts"),
    ("pp_daredevil", "Daredevil", "pp_daredevil", [1, 10, 40, 100, 250],
     ["Bold", "Cheeky", "Daredevil", "Fearless", "Untouchable"],
     "Taunted with a seeker close enough to touch you.", "em_pp_dare", "close taunts"),
    ("pp_decoy_duck", "Decoy Duck", "pp_decoys", [1, 10, 40, 100, 250],
     ["Trickster", "Double", "Decoy Duck", "Illusionist", "Hall of Mirrors"],
     "A seeker wasted a shot (or a walk) on one of your decoys.", "em_pp_duck",
     "seekers fooled"),
    ("pp_last_standing", "Last Prop Standing", "pp_last_stand", [1, 3, 10, 25],
     ["Survivor", "Holdout", "Last One Out", "The Last Teapot"],
     "Were the last hider left -- and lasted to the end.", "em_pp_last", "last stands"),
    ("pp_clean_sweep", "Clean Sweep", "pp_sweep", [1, 5, 20, 60],
     ["Tidy", "Spring Clean", "Clean Sweep", "Spotless"],
     "Seekers found every hider with a minute or more to spare.", "em_pp_broom",
     "clean sweeps"),
    ("pp_master_disguise", "Master of Disguise", "pp_disguises", [10, 100, 400, 1200, 3000],
     ["Dresser-Up", "Quick Change", "Chameleon", "Shapeshifter", "Thousand Faces"],
     "Changed what you were disguised as.", "em_pp_mask", "disguises"),
    ("pp_cat_whisperer", "Cat Whisperer", "pp_cat", [1, 5, 15, 40, 100],
     ["Cat Person", "Cat Whisperer", "Mittens' Friend", "Crazy Cat Seeker", "Cat Lord"],
     "In Grandma's Cottage, found a hider Mittens was staring at.", "em_pp_cat",
     "cat finds"),
    ("pp_night_owl", "Night Owl", "pp_dark", [1, 5, 15, 40, 100],
     ["Torchbearer", "Night Owl", "Bat Eyes", "Lights Out", "Owl of the Emporium"],
     "Found a hider in the Toy Emporium while the power was out.", "em_pp_owl",
     "finds in the dark"),
    ("pp_bargain_hunter", "Bargain Hunter", "pp_sale", [1, 5, 15, 40, 100],
     ["Shopper", "Bargain Hunter", "Deal Finder", "Clearance King", "Black Friday"],
     "In MegaMart, found a hider with a flash-sale price tag on it.", "em_pp_tag",
     "bargains"),
    ("pp_alarm_bells", "Alarm Bells", "pp_alarm", [1, 5, 15, 40, 100],
     ["Night Guard", "Alarm Bells", "Security", "Head of Security", "The Curator"],
     "In the museum, found a hider who set off the searchlight alarm.", "em_pp_alarm",
     "alarms answered"),
    ("pp_every_room", "Every Room", "pp_areas", [1, 2, 3, 4],
     ["Visitor", "Regular", "Know Every Room", "Owns the Place"],
     "Won a round in each of Prop Panic's four places.", "em_pp_map", "places"),
]

DERIVED = {"pp_areas": "pp_area_"}

# ------------------------------------------------------------------- speech
SPEECH: List[Tuple[str, str, int, str]] = [
    ("pp_release", "Seekers released", 25,
     "The countdown ends and the seekers come out of the pen."),
    ("pp_found", "Hider found", 45,
     "A seeker pops a hider: it is out."),
    ("pp_taunt", "Cheeky taunt", 35,
     "A hider taunts with a seeker right next to it."),
    ("pp_decoy", "Fooled by a decoy", 40,
     "A seeker shoots (or walks into) a hider's decoy."),
    ("pp_last", "Last hider", 50,
     "Only one hider is left."),
    ("pp_cat", "The cat stares", 35,
     "Grandma's Cottage: Mittens stops and stares at a hider."),
    ("pp_dark", "Lights out", 35,
     "The Toy Emporium: the power cuts out."),
    ("pp_sale", "Flash sale", 35,
     "MegaMart: a flash sale tags every hider disguised as one kind of thing."),
    ("pp_alarm", "Alarm", 40,
     "The museum: a hider moved in the searchlight and set off the alarm."),
]


def _side(event: Dict[str, Any], name: str, team: str) -> Tuple[bool, bool, bool]:
    """(the bot did it, its team did it, the bot's team is hiding)."""
    by = str(event.get("by") or "")
    me = bool(by) and by == name
    mine = bool(team) and str(event.get("by_team") or "") == team
    hiding = bool(team) and str(event.get("hiders") or "") != "" and \
        str(event.get("team") or "") == team
    return me, mine, hiding


def describe(kind: str, event: Dict[str, Any], name: str, team: str
             ) -> Optional[Tuple[str, str]]:
    """How a Prop Panic event reads from one bot's side."""
    me, mine, _ = _side(event, name, team)
    by = str(event.get("by") or "somebody")
    where = str(event.get("where") or event.get("what") or "")
    if kind == "pp_release":
        if str(event.get("team") or "") == team:
            return ("The countdown is over and your team is out of the pen: go and find "
                    "the hiders.", "actor")
        return ("The seekers are out of the pen. Stay very still.", "victim")
    if kind == "pp_found":
        victim = str(event.get("victim") or "a hider")
        what = str(event.get("what") or "a prop")
        if me:
            return ("You just found %s, disguised as %s%s." % (
                victim, what.lower(), (" in " + where) if event.get("where") else ""), "actor")
        if victim == name:
            return ("%s found you -- you were a %s. You are out until the next round." % (
                by, what.lower()), "victim")
        if mine:
            return ("Your teammate %s found %s (a %s)." % (by, victim, what.lower()), "ally")
        return ("%s found %s, who was hiding as a %s." % (by, victim, what.lower()), "victim")
    if kind == "pp_taunt":
        if me:
            return ("You taunted right under a seeker's nose near %s." % (where or "here"),
                    "actor")
        if mine:
            return ("%s just taunted right next to a seeker. Bold." % by, "ally")
        return ("A hider just taunted right next to you near %s -- it is close!" % (
            where or "here"), "victim")
    if kind == "pp_decoy":
        owner = str(event.get("owner") or "a hider")
        if me:
            return ("You popped a decoy near %s. It was a fake." % (where or "here"), "victim")
        if owner == name:
            return ("%s fell for your decoy." % by, "actor")
        if mine:
            return ("%s got fooled by a decoy." % by, "victim")
        return ("%s fell for %s's decoy." % (by, owner), "ally")
    if kind == "pp_last":
        if me:
            return ("You are the last hider left. Everyone is looking for you now.", "actor")
        if str(event.get("by_team") or "") == team:
            return ("%s is your team's last hider." % by, "ally")
        return ("Only one hider is left: %s. Find them!" % by, "ally")
    if kind == "pp_cat":
        if me:
            return ("Grandma's cat is staring right at you near %s." % (where or "here"),
                    "victim")
        if mine:
            return ("The cat is staring at your teammate %s." % by, "victim")
        return ("Mittens the cat is staring at something near %s -- that is a hider." % (
            where or "here"), "ally")
    if kind == "pp_dark":
        return ("The lights just went out in the toy shop.", "neutral")
    if kind == "pp_sale":
        what = str(event.get("what") or "something")
        return ("Flash sale: every %s in the store has a price tag on it now." % what.lower(),
                "neutral")
    if kind == "pp_alarm":
        if me:
            return ("You moved in the searchlight and set off the alarm.", "victim")
        if mine:
            return ("%s set off the museum alarm near %s." % (by, where or "here"), "victim")
        return ("The alarm went off near %s: a hider moved in the searchlight." % (
            where or "here"), "ally")
    return None


CANNED: Dict[Tuple[str, str], List[str]] = {
    ("pp_release", "actor"): ["ready or not", "here we come", "lets find them", "spread out"],
    ("pp_release", "victim"): ["shh", "dont move", "they're out", "stay still"],
    ("pp_found", "actor"): ["found one", "gotcha", "got the teapot lol", "ez", "one down"],
    ("pp_found", "victim"): ["noo", "how", "i was a lamp", "gg", "rip"],
    ("pp_found", "ally"): ["nice find", "gj", "keep going", "how many left"],
    ("pp_taunt", "actor"): ["lol", "catch me", "right here", "too slow"],
    ("pp_taunt", "ally"): ["bold", "lol", "dont get caught"],
    ("pp_taunt", "victim"): ["its close", "i heard that", "where", "its right here"],
    ("pp_decoy", "actor"): ["lol fake", "got em", "decoy"],
    ("pp_decoy", "victim"): ["fake", "decoy lol", "ugh", "rigged"],
    ("pp_decoy", "ally"): ["lol", "nice decoy"],
    ("pp_last", "actor"): ["just me", "1v8", "dont find me", "pray for me"],
    ("pp_last", "ally"): ["one left", "find the last one", "check upstairs", "last one"],
    ("pp_cat", "victim"): ["shoo", "go away cat", "bad kitty", "stop staring"],
    ("pp_cat", "ally"): ["follow the cat", "cat found one", "good kitty", "the cat knows"],
    ("pp_dark", "neutral"): ["lights", "cant see", "torches on", "spooky"],
    ("pp_sale", "neutral"): ["sale lol", "check the tags", "change change", "bargain"],
    ("pp_alarm", "victim"): ["oops", "ALARM", "run"],
    ("pp_alarm", "ally"): ["alarm!", "over there", "follow the alarm"],
}

# ----------------------------------------------------------------- the bots
BOT_SECTION = ("prop_panic", "Prop Panic",
               "How bots hide and seek: disguises, stillness, taunts, guesses and each "
               "place's twist.", "\U0001FAD6")
BOT_INTRO = ("In Prop Panic a hiding bot picks a spot, turns into something that belongs "
             "there and keeps still -- or taunts, runs and drops decoys, by its personas. "
             "A seeking bot searches room by room, follows taunts, sniffs, guesses at "
             "suspicious props and plays each place's twist.")
BOT_FIELDS: List[Tuple[Any, ...]] = [
    ("enabled", "Play hide and seek", "bool", True,
     "Bots hide as props and seek with poppers. Off: they wander and shoot as in any "
     "world (hiders are still props).", {"toggle": True}),
    ("stillness", "Keep still", "pct", 75,
     "How still a hiding bot stays once it has picked a spot, and how readily it stays "
     "put when shot at; patient and veteran personas most.",
     {"min": 0, "max": 100, "step": 1, "unit": "%", "scope": "base"}),
    ("hide_smart", "Hide where it fits", "pct", 70,
     "How much a hiding bot picks a disguise that belongs in its room (and fits the "
     "spot); chaotic personas pick silly ones anyway.",
     {"min": 0, "max": 100, "step": 1, "unit": "%", "scope": "base"}),
    ("taunt", "Taunt", "pct", 35,
     "How often a hiding bot taunts; trash talkers and kids most, and the brave ones "
     "with a seeker right beside them.",
     {"min": 0, "max": 100, "step": 1, "unit": "%", "scope": "base"}),
    ("decoys", "Drop decoys", "pct", 50,
     "Chance a hiding bot leaves a decoy behind when it moves on or runs.",
     {"min": 0, "max": 100, "step": 1, "unit": "%", "scope": "base"}),
    ("eyes", "Seekers' eyes", "pct", 50,
     "How sharp a seeking bot's eyes are: the chance it notices a prop that moved, a "
     "prop that does not belong, or one being revealed.",
     {"min": 0, "max": 100, "step": 1, "unit": "%", "scope": "base"}),
    ("guess", "Guess at props", "pct", 40,
     "How readily a seeking bot shoots suspicious-looking props (a wrong guess costs it "
     "health); fraggers and chaotic personas most.",
     {"min": 0, "max": 100, "step": 1, "unit": "%", "scope": "base"}),
    ("sniffer", "Use the sniffer", "pct", 60,
     "How often a seeking bot uses its sniffer when it has nothing else to go on; "
     "support personas most.", {"min": 0, "max": 100, "step": 1, "unit": "%", "scope": "base"}),
    ("twist", "Play the place's twist", "pct", 70,
     "How much bots work each place's twist: follow the cat, the price tags and the "
     "alarm; dodge flash sales; listen harder in the dark.",
     {"min": 0, "max": 100, "step": 1, "unit": "%", "scope": "base"}),
    ("callouts", "Callouts", "bool", True,
     "Bots shout the round's moments in quick chat: found one, it's close, follow the "
     "cat, sale! The language model's own reactions come from the speech events."),
]
PERSONA_TIES: List[Tuple[str, str]] = [
    ("Veteran, Patient, Sniper main",
     "Hide still and in character; as seekers, watch for anything that moved."),
    ("Chaotic, Kid, Trash talker",
     "Taunt from the silliest disguises, right under the seekers' noses."),
    ("Fragger, Shotgun rusher", "Sweep a room by popping everything that looks off."),
    ("Helpful, Wholesome, Support", "Use the sniffer and call out where the squeaks came from."),
    ("Explorer, Jumpy", "Hide in the far corners -- the treehouse, the stockroom, the "
     "loading dock -- and move on when the coast is clear."),
    ("Prop master", "Knows every room's props; picks a disguise that belongs, and plays "
     "the place's twist."),
]
PERSONA_TAG = {"id": "prop_master", "label": "Prop master",
               "prompt": "Loves Prop Panic; has hidden as every teapot in Grandma's Cottage "
                         "and knows which props in each place are really people.",
               "weight": 0.9, "fx": {"w_prop_panic": 2.4, "objective": 0.05}}
PROMPT = ("Prop Panic is prop hunt on BLOCKHAVEN: each round one team hides by turning into "
          "props (a teapot, a teddy bear, a cereal box, a suit of armour) and the other "
          "team seeks with prop poppers -- popping a real prop by mistake hurts the seeker. "
          "The teams are the Dust Bunnies (red) and the Feather Dusters (blue) and they "
          "swap every round. Hiders taunt, leave decoys and scurry; seekers sniff and "
          "throw glitter bombs. There are four places: Grandma's Cottage (her cat Mittens "
          "stares at hiders), Tinker's Toy Emporium (the power cuts out), MegaMart "
          "(flash sales tag hiders) and the Museum After Dark (a searchlight sets off "
          "the alarm). Players talk in short bursts: 'found one', 'that lamp moved', "
          "'sus teapot', 'its close', 'follow the cat', 'one left'.")
HISTORY = {"kills": 0.5, "deaths": 0.45, "round_minutes": 4.5, "win": 0.5}


def history_badges(history: Dict[str, Any], traits: Dict[str, float], rng
                   ) -> List[Tuple[str, int, str]]:
    """The badge stats a new bot's made-up Prop Panic history earned."""
    rounds = int(history.get("rounds", 0) or 0)
    wins = int(history.get("wins", 0) or 0)
    if rounds <= 0:
        return []
    chaos = float(traits.get("chaos", 0.2))
    skill = float(traits.get("skill", 0.5))
    patience = 1.0 - float(traits.get("jumpy", 0.2))
    hid = rounds // 2
    out = [("pp_wins", wins, "add"),
           ("pp_survived", int(hid * rng.uniform(0.15, 0.5) * (0.5 + patience)), "add"),
           ("pp_found", int(int(history.get("kills", 0) or 0) * rng.uniform(0.6, 1.0)), "add"),
           ("pp_taunts", int(hid * rng.uniform(0.5, 3.0) * (0.3 + chaos)), "add"),
           ("pp_daredevil", int(hid * rng.uniform(0.0, 0.4) * (0.2 + chaos)), "add"),
           ("pp_decoys", int(hid * rng.uniform(0.0, 0.5) * (0.3 + skill)), "add"),
           ("pp_last_stand", int(hid * rng.uniform(0.0, 0.05) * (0.3 + skill)), "add"),
           ("pp_sweep", int((rounds - hid) * rng.uniform(0.0, 0.08) * (0.3 + skill)), "add"),
           ("pp_disguises", int(hid * rng.uniform(2.0, 6.0)), "add"),
           ("pp_cat", int(rounds / 8.0 * rng.uniform(0.0, 0.8)), "add"),
           ("pp_dark", int(rounds / 8.0 * rng.uniform(0.0, 0.6)), "add"),
           ("pp_sale", int(rounds / 8.0 * rng.uniform(0.0, 0.7)), "add"),
           ("pp_alarm", int(rounds / 8.0 * rng.uniform(0.0, 0.7)), "add")]
    areas = [a["id"] for a in WORLD["areas"]]
    rng.shuffle(areas)
    for area in areas[:min(len(areas), wins // 3)]:
        out.append(("pp_area_" + area, 1, "max"))
    return out


# a round is four and a half minutes and an area has two: the tests need
# this long to see the server move on
TEST_SECONDS = 1250.0

DORMANT = {"round_seconds": 250.0, "rounds_per_area": 2, "intermission": 14.0,
           "teams": ["red", "blue"], "kills": 0.5, "deaths": 0.45, "swap": False}
