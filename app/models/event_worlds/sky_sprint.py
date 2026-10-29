"""Sky Sprint: an obstacle-course race in four places in the sky.

Two teams race the same course from a start deck to a finish high above
it: checkpoints, jump pads, conveyors, swinging hammers, sweeping arms,
lasers, blinking and crumbling tiles, and a fall puts you back at your
last checkpoint.  Every checkpoint and every place at the finish scores
for your team, and a bonk glove knocks rivals off the course.  The rules
are in app/game/worlds/sky_sprint.py and the four courses in
app/game/maps/events/sky_sprint/.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

WORLD: Dict[str, Any] = {
    "id": "sky_sprint",
    "prefix": "ss",
    "name": "Sky Sprint",
    "genre": "Obstacle Race",
    "tagline": "Run it, jump it, bonk past it. The lava is not a suggestion.",
    "description": (
        "Two teams, one obstacle course hung in the sky, and a gate that drops at GO. "
        "Run the girders, ride the conveyors, time the hammers, hop the sweeping arms, "
        "jump the gaps and launch off the pads to the finish -- and when you fall (you "
        "will fall) you are back at your last checkpoint, not the start. Every checkpoint "
        "you reach scores for your team, the first racer to each one scores more, and the "
        "finish pays out by place. Everybody carries a bonk glove: no damage, just a "
        "shove, and a rival shoved off the course is two more points. Power-ups turn up "
        "along the way -- spring shoes, a rocket, a feather, a bubble -- and every course "
        "has its twist: the Foundry's conveyors run backwards, Candy Clouds goes on a "
        "sugar rush, Neon Grid's beat drops, and a typhoon howls across the Jade Temple's "
        "bridges."),
    "max_players": 16,
    "team_count": 2,
    "mode": "obby_race",
    "round_label": "One race",
    "colors": ["#e8503a", "#3a8ae8", "#f2c230"],
    "thumb": "sky_sprint",
    "features": ["16 players", "Obstacle course", "Team race", "Bonk glove", "Power-ups",
                 "Checkpoints", "4 twists", "4 rotating courses"],
    "areas": [
        {"id": "foundry", "name": "The Foundry",
         "blurb": "An ironworks over a lake of molten iron: I-beams, conveyors, the hammer "
                  "hall, piston steps, the gear room and its sweeping arm, crane girders, "
                  "crumbling grates and two blast pads up the great chimney. The conveyors "
                  "run backwards."},
        {"id": "candy", "name": "Candy Clouds",
         "blurb": "A sweet shop in the sky over a chocolate river: gumdrop stepping stones, "
                  "jelly that bounces you, taffy that holds you, biscuit bridges that crumble, "
                  "lollipop sweepers and the cake at the top. Sugar rush!"},
        {"id": "neon", "name": "Neon Grid",
         "blurb": "A synthwave city at night: speed strips, beat tiles that blink to the "
                  "music, sweeping lasers, spinning neon bars and a tower of pads to the "
                  "rooftop. When the beat drops, everything doubles."},
        {"id": "jade", "name": "Jade Temple",
         "blurb": "Floating islands round a mountain temple: rope bridges in the wind, "
                  "spinning bamboo, cloud platforms that drift in and out, lotus pads and the "
                  "great bell. A typhoon blows across every bridge."},
    ],
    "areas_note": "Two races on each course, then everybody moves on to another one.",
    "howto": [
        {"title": "Race the course",
         "text": "The gate drops at GO. Run, jump and ride the machinery past every "
                 "checkpoint to the finish. Fall off and you are back at your last checkpoint."},
        {"title": "Score for your team",
         "text": "Every checkpoint you reach is a point for your team; the first racer to "
                 "each one gets three more; the finish pays 12, 9, 7, 5, 4, 3, 2 and 1 by place."},
        {"title": "Bonk your rivals",
         "text": "Your glove (click) shoves a rival -- no damage. Knock one off the course "
                 "and that is two points. A bubble power-up makes you unbonkable."},
        {"title": "Grab the power-ups",
         "text": "Spring shoes jump higher, a feather falls slowly, a bubble shrugs off "
                 "everything, and a rocket (press E) is a dash when you need one."},
    ],
    "howto_note": "Hammers, sweepers and lasers run on a clock: watch one go round once "
                  "before you go. Blinking tiles flash before they vanish.",
    "team_names": {"red": "Red Rockets", "blue": "Blue Comets"},
}

# struck on a cloud, the enamel in the middle of it
FAMILY = ("skycloud", {
    "mesh": "skycloud", "face": "#1a3a6a", "ribbon": "#e8503a", "wing": "#f2f6ff",
    "wing_mesh": "wing", "plate_size": [1.2, 1.2, 1.4], "face_r": 0.33, "face_y": 0.0,
    "stripes": [],
})

BADGES: List[Tuple[Any, ...]] = [
    ("ss_sky_high", "Sky High", "ss_wins", [1, 5, 15, 40, 100, 250],
     ["Hopper", "Climber", "Skywalker", "High Flyer", "Cloud Runner", "Sky Legend"],
     "Won races of Sky Sprint with your team.", "em_ss_trophy", "races won"),
    ("ss_over_the_line", "Over the Line", "ss_finishes", [1, 10, 40, 120, 300, 800],
     ["Finisher", "Regular", "Seasoned", "Marathoner", "Iron Legs", "Unstoppable"],
     "Crossed the finish line of a course.", "em_ss_flag", "finishes"),
    ("ss_first_across", "First Across", "ss_first_place", [1, 5, 20, 60, 150],
     ["Quick", "Swift", "Lightning", "Untouchable", "Speed Demon"],
     "Finished a race in first place.", "em_ss_first", "wins of the race"),
    ("ss_podium", "Podium", "ss_podium", [1, 5, 20, 60, 150],
     ["Third", "Contender", "Medallist", "Champion", "Podium Regular"],
     "Finished a race in the top three.", "em_ss_podium", "podiums"),
    ("ss_waypoints", "Waypoints", "ss_checkpoints", [5, 50, 200, 600, 1500, 4000],
     ["Tourist", "Wanderer", "Navigator", "Pathfinder", "Wayfarer", "Mapmaker"],
     "Reached checkpoints on the courses.", "em_ss_arch", "checkpoints"),
    ("ss_trailblazer", "Trailblazer", "ss_firsts", [1, 10, 40, 120, 300],
     ["Out Front", "Pacesetter", "Trailblazer", "Front Runner", "Pathbreaker"],
     "Were the first racer to reach a checkpoint.", "em_ss_boot", "first arrivals"),
    ("ss_flawless", "Flawless", "ss_clean_run", [1, 5, 20, 60],
     ["Steady", "Sure-Footed", "Flawless", "Perfectionist"],
     "Finished a race without falling off once.", "em_ss_feather", "clean runs"),
    ("ss_bonk", "Bonk!", "ss_bonks", [1, 25, 100, 300, 800],
     ["Poker", "Pusher", "Bonker", "Bruiser", "Bonk Master"],
     "Landed the bonk glove on a rival.", "em_ss_glove", "bonks"),
    ("ss_ring_out", "Ring Out", "ss_ring_outs", [1, 10, 40, 120, 300],
     ["Nudge", "Shover", "Bouncer", "Ring Master", "Gravity's Friend"],
     "Bonked a rival who then fell off the course.", "em_ss_ringout", "ring-outs"),
    ("ss_power_up", "Power Up", "ss_powers", [1, 20, 80, 250, 600],
     ["Collector", "Gatherer", "Hoarder", "Supercharged", "Overclocked"],
     "Picked up power-ups on the course.", "em_ss_power", "power-ups"),
    ("ss_rocketeer", "Rocketeer", "ss_rockets", [1, 10, 40, 120],
     ["Ignition", "Lift-Off", "Rocketeer", "Afterburner"],
     "Lit a rocket on the course.", "em_ss_rocket", "rockets"),
    ("ss_every_course", "Every Course", "ss_areas", [1, 2, 3, 4],
     ["Visitor", "Traveller", "Globetrotter", "Every Course"],
     "Won a race on each of Sky Sprint's four courses.", "em_ss_map", "courses"),
]

DERIVED = {"ss_areas": "ss_area_"}

# ------------------------------------------------------------------- speech
SPEECH: List[Tuple[str, str, int, str]] = [
    ("ss_first_cp", "First to a checkpoint", 35,
     "A racer reached a checkpoint before anybody else."),
    ("ss_finish", "Across the line", 55,
     "A racer crossed the finish line."),
    ("ss_ring_out", "Ring out", 45,
     "A racer bonked a rival off the course."),
    ("ss_twist", "The twist", 35,
     "The course's twist started: the belts reverse, a sugar rush, the beat drops, a typhoon."),
    ("ss_hurry", "Hurry up", 30,
     "Half the field is home: the rest have a few seconds left."),
]

_TWISTS = {"reverse": "The conveyors are running backwards!",
           "sugar_rush": "Sugar rush -- everybody is fast!",
           "drop": "The beat dropped -- the tiles are blinking double time!",
           "typhoon": "A typhoon is blowing across the bridges!"}


def describe(kind: str, event: Dict[str, Any], name: str, team: str
             ) -> Optional[Tuple[str, str]]:
    """How a Sky Sprint event reads from one bot's side."""
    by = str(event.get("by") or "somebody")
    me = bool(event.get("by")) and by == name
    ours = bool(team) and event.get("team") == team
    if kind == "ss_first_cp":
        n = int(event.get("n") or 1)
        if me:
            return ("You were first to checkpoint %d." % n, "actor")
        return ("%s was first to checkpoint %d%s." % (by, n, " -- one of ours" if ours else ""),
                "ally" if ours else "enemy")
    if kind == "ss_finish":
        place = int(event.get("place") or 1)
        nth = {1: "first", 2: "second", 3: "third"}.get(place, "%dth" % place)
        if me:
            return ("You finished %s." % nth, "actor")
        return ("%s finished %s%s." % (by, nth, " for us" if ours else ""),
                "ally" if ours else "enemy")
    if kind == "ss_ring_out":
        victim = str(event.get("victim") or "somebody")
        if me:
            return ("You bonked %s right off the course." % victim, "actor")
        if victim == name:
            return ("%s bonked you off the course." % by, "victim")
        return ("%s bonked %s off the course." % (by, victim), "ally" if ours else "enemy")
    if kind == "ss_twist":
        return (_TWISTS.get(str(event.get("twist") or ""), "The course changed!"), "neutral")
    if kind == "ss_hurry":
        return ("Half the field is home: hurry!", "neutral")
    return None


CANNED: Dict[Tuple[str, str], List[str]] = {
    ("ss_first_cp", "actor"): ["first!", "ez", "catch me", "lead", "gotta go fast"],
    ("ss_first_cp", "ally"): ["nice", "go go", "lead!", "keep going"],
    ("ss_first_cp", "enemy"): ["they're fast", "catch them", "how", "we're behind"],
    ("ss_finish", "actor"): ["done!", "gg", "first try", "ez", "made it"],
    ("ss_finish", "ally"): ["nice!", "gg", "go team", "keep going"],
    ("ss_finish", "enemy"): ["hurry", "they finished", "go go go", "aaah"],
    ("ss_ring_out", "actor"): ["bonk", "byeee", "see ya", "get bonked", "lol"],
    ("ss_ring_out", "victim"): ["HEY", "rude", "why", "noooo", "i'll get you"],
    ("ss_ring_out", "ally"): ["lol nice", "bonked", "ouch", "get them"],
    ("ss_ring_out", "enemy"): ["rip", "unlucky", "careful", "watch the edges"],
    ("ss_twist", "neutral"): ["uh oh", "here we go", "chaos", "noooo", "lets go"],
    ("ss_hurry", "neutral"): ["hurry!", "go go go", "almost", "come on"],
}

# ----------------------------------------------------------------- the bots
BOT_SECTION = ("sky_sprint", "Sky Sprint",
               "How bots run the obstacle course: how sure-footed they are, how patiently "
               "they wait out a hammer, how keen they are on the glove and the power-ups.",
               "\U0001F3C3")
BOT_INTRO = ("In Sky Sprint a bot runs the course's line: it jumps the gaps, rides the "
             "pads and belts, waits for a hammer to swing past or a tile to come back, hops "
             "a sweeping arm, grabs a power-up near its way, lights a rocket on a straight, "
             "and bonks a rival who gets too close to an edge.")
BOT_FIELDS: List[Tuple[Any, ...]] = [
    ("enabled", "Race the course", "bool", True,
     "Bots race the course's line to the finish. Off: they wander as in any world.",
     {"toggle": True}),
    ("skill", "Sure-footedness", "pct", 60,
     "How rarely a bot misjudges a jump and falls short; veteran and tryhard personas most.",
     {"min": 0, "max": 100, "step": 1, "unit": "%", "scope": "base"}),
    ("patience", "Patience", "pct", 60,
     "How long a bot will wait for a hammer, a sweeper, a laser or a blinking tile before it "
     "risks it anyway; patient personas most.",
     {"min": 0, "max": 100, "step": 1, "unit": "%", "scope": "base"}),
    ("bonk", "Bonk-happiness", "pct", 40,
     "How readily a bot swings the glove at a rival near it; fraggers and chaotic personas "
     "most.",
     {"min": 0, "max": 100, "step": 1, "unit": "%", "scope": "base"}),
    ("powerups", "Power-up hunting", "pct", 60,
     "How far off the line a bot goes for a power-up, and how soon it lights a rocket.",
     {"min": 0, "max": 100, "step": 1, "unit": "%", "scope": "base"}),
    ("callouts", "Callouts", "bool", True,
     "Bots shout in quick chat as they race: bonk, byeee, nooo, missed it, that jump. The "
     "language model's own reactions come from the speech events."),
]
PERSONA_TIES: List[Tuple[str, str]] = [
    ("Veteran, Tryhard, Speedrunner",
     "Sure-footed: rarely miss a jump, never waste a rocket."),
    ("Patient, Sniper main",
     "Wait for the hammer to swing past every time; slow and steady."),
    ("Fragger, Chaotic, Toxic",
     "Bonk everything that moves; win some, fall off chasing others."),
    ("Kid, Jumpy", "Run at everything, miss half the jumps and laugh about it."),
    ("Explorer, Collector", "Go out of their way for every power-up on the course."),
    ("Helpful, Wholesome", "Cheer the team on and wait up for the stragglers."),
]
PERSONA_TAG = {"id": "speedrunner", "label": "Speedrunner",
               "prompt": "Loves Sky Sprint; knows every jump on every course, times the "
                         "hammers in their sleep, and chases a personal best every race.",
               "weight": 0.9, "fx": {"w_sky_sprint": 2.4, "objective": 0.05}}
PROMPT = ("Sky Sprint is an obstacle-course race on BLOCKHAVEN for two teams, the Red "
          "Rockets and the Blue Comets: run, jump and ride a course in the sky from the start "
          "gate to the finish; checkpoints score for your team (the first racer to each scores "
          "more), the finish pays out by place, and falling sends you back to your last "
          "checkpoint. Everybody has a bonk glove to shove rivals off the course, and "
          "power-ups turn up: spring shoes, a rocket, a feather, a bubble. The courses are "
          "the Foundry (lava, hammers, conveyors that reverse), Candy Clouds (jelly, taffy, "
          "biscuits that crumble, a sugar rush), Neon Grid (blinking beat tiles, lasers, the "
          "beat drops) and the Jade Temple (wind on the bridges, a typhoon). Players talk in "
          "short bursts: 'go go go', 'that hammer', 'bonk', 'nooo', 'so close', 'gg'.")
HISTORY = {"kills": 0.0, "deaths": 0.0, "round_minutes": 3.0, "win": 0.5}


def history_badges(history: Dict[str, Any], traits: Dict[str, float], rng
                   ) -> List[Tuple[str, int, str]]:
    """The badge stats a new bot's made-up Sky Sprint history earned."""
    rounds = int(history.get("rounds", 0) or 0)
    wins = int(history.get("wins", 0) or 0)
    if rounds <= 0:
        return []
    skill = float(traits.get("skill", 0.5))
    aggro = float(traits.get("aggression", 0.5))
    finishes = int(rounds * rng.uniform(0.45, 0.9) * (0.5 + skill * 0.6))
    out = [("ss_wins", wins, "add"),
           ("ss_finishes", finishes, "add"),
           ("ss_first_place", int(finishes * rng.uniform(0.02, 0.14) * (0.4 + skill)), "add"),
           ("ss_podium", int(finishes * rng.uniform(0.1, 0.35) * (0.4 + skill)), "add"),
           ("ss_checkpoints", int(rounds * rng.uniform(2.0, 4.0)), "add"),
           ("ss_firsts", int(rounds * rng.uniform(0.05, 0.5) * (0.4 + skill)), "add"),
           ("ss_clean_run", int(finishes * rng.uniform(0.0, 0.2) * (0.3 + skill)), "add"),
           ("ss_bonks", int(rounds * rng.uniform(0.5, 4.0) * (0.4 + aggro)), "add"),
           ("ss_ring_outs", int(rounds * rng.uniform(0.0, 0.6) * (0.4 + aggro)), "add"),
           ("ss_powers", int(rounds * rng.uniform(0.3, 1.6)), "add"),
           ("ss_rockets", int(rounds * rng.uniform(0.0, 0.5)), "add")]
    areas = [a["id"] for a in WORLD["areas"]]
    rng.shuffle(areas)
    for area in areas[:min(len(areas), wins // 3)]:
        out.append(("ss_area_" + area, 1, "max"))
    return out


# a race runs up to three minutes and a course has two: the tests need this
# long to see the field move on
TEST_SECONDS = 480.0

DORMANT = {"round_seconds": 160.0, "rounds_per_area": 2, "intermission": 15.0,
           "teams": ["red", "blue"], "kills": 0.0, "deaths": 0.0, "swap": False}
