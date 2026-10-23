"""Rail Rivals: a payload race on four frontier railroads.

Two companies -- the Crimson Line and the Bluebird Express -- each push an
ore cart along their own track from one end of an area to the other, and
the first to the terminus wins.  The tracks cross in the middle, so the race
always comes to blows there.  Brake levers, coal, depots and each line's own
twist (a signal tower, snowdrifts, lift bridges, firedamp) are the rules in
app/game/worlds/rail_rivals.py.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

WORLD: Dict[str, Any] = {
    "id": "rail_rivals",
    "prefix": "rr",
    "name": "Rail Rivals",
    "genre": "Payload Race",
    "tagline": "Two railroads. One gold rush. First cart to the end of the line wins.",
    "description": (
        "The Crimson Line and the Bluebird Express both want the gold, and "
        "there is only one way to settle it: race your company's ore cart "
        "down its own line to the terminus before the other lot get theirs "
        "there. Stand by your cart to push it -- the more of you, the faster "
        "it rolls -- and stand by theirs to stop it dead. The two lines cross "
        "in the middle, so every race turns into a brawl at the junction. "
        "Pull the brake levers by the other team's track, shovel coal into "
        "your own firebox, and keep your cart moving past the depots so you "
        "come back further up the line. Four railroads, two races on each "
        "(you swap tracks for the second), and every line has a twist of "
        "its own: the signal tower over Dustbowl Gulch, snowdrifts on "
        "Silverpine Pass, the lift bridges over Redrock Mesa's gorge and the "
        "firedamp in Lantern Deep."),
    "max_players": 16,
    "team_count": 2,
    "mode": "payload_race",
    "round_label": "Race to the terminus",
    "colors": ["#c4281c", "#2f6aa8", "#e8b23a"],
    "thumb": "rail_rivals",
    "features": ["16 players", "Payload race", "Brake levers", "Coal boosts",
                 "Depot respawns", "4 rotating railroads", "A twist on every line"],
    "areas": [
        {"id": "dustbowl", "name": "Dustbowl Gulch",
         "blurb": "A gold town at the mouth of a red canyon. The lines cross "
                  "on Junction Square under the signal tower: take its cabin "
                  "and the signal holds the other cart at the diamond."},
        {"id": "silverpine", "name": "Silverpine Pass",
         "blurb": "A snowbound summit. Both lines cross a frozen lake on "
                  "trestles and run through snow sheds; drifts come down on "
                  "the track and somebody has to dig the cart out."},
        {"id": "redrock", "name": "Redrock Mesa",
         "blurb": "Sundown on banded sandstone. The lines cross in a cavern "
                  "under a mesa, past a dinosaur dig, and over a river gorge "
                  "on lift bridges the other team can winch up."},
        {"id": "lantern", "name": "Lantern Deep",
         "blurb": "The lowest level of the mine: crystals, glowing "
                  "mushrooms, a lava chasm under the Devil's Bridge, and "
                  "firedamp that gathers in the hollows and goes up."},
    ],
    "areas_note": "Two races on each line -- the teams swap tracks for the second -- "
                  "then the server moves on to another railroad.",
    "howto": [
        {"title": "Push your cart",
         "text": "Stand within a few steps of your own cart and it rolls. Two "
                 "pushers are faster than one, three faster still. Leave it "
                 "alone too long and it rolls back to the last depot."},
        {"title": "Stop theirs",
         "text": "Any enemy beside a cart stops it cold (contested). Hold E at "
                 "a brake lever by the other team's track to lock their cart "
                 "for a while -- they have to come and release it."},
        {"title": "Coal and depots",
         "text": "Hold E at a coal heap to pick up a sack, and E by your cart "
                 "to stoke it for a burst of speed. Every depot your cart "
                 "passes is where your team comes back from then on."},
        {"title": "Every line has a twist",
         "text": "Take Dustbowl's signal cabin to hold their cart at the "
                 "diamond; dig Silverpine's drifts off your track; winch "
                 "Redrock's lift bridges up in their faces; and get clear of "
                 "Lantern Deep's firedamp when the warning boards hiss."},
    ],
    "howto_note": "First cart to its terminus wins the race. If the clock runs out "
                  "first, the cart further along its line takes it.",
    "team_names": {"red": "Crimson Line", "blue": "Bluebird Express"},
}

FAMILY = ("horseshoe", {
    "mesh": "horseshoe", "face": "#3a2414", "ribbon": "#c4281c", "wing": "#e8d8b8",
    "wing_mesh": "wing", "plate_size": [1.12, 1.12, 0.9], "face_r": 0.3,
    "face_y": 0.04, "stripes": [],
})

BADGES: List[Tuple[Any, ...]] = [
    ("rr_gold_rush", "Gold Rush", "rr_wins", [1, 5, 15, 40, 100, 250],
     ["Prospector", "Claim Holder", "Gold Digger", "Rail Baron", "Tycoon",
      "Gilded Legend"],
     "Won races in Rail Rivals with your company.", "em_rr_nugget", "races won"),
    ("rr_conductor", "Conductor", "rr_pushed", [200, 2000, 8000, 25000, 60000, 150000],
     ["Water Boy", "Fireman", "Engineer", "Conductor", "Superintendent", "Iron Horse"],
     "Counts every unit your own cart rolled while you were pushing it.",
     "em_rr_cart", "units pushed"),
    ("rr_saboteur", "Saboteur", "rr_levers", [1, 10, 30, 80, 200, 400],
     ["Tinkerer", "Wrecker", "Saboteur", "Train Robber", "Outlaw", "Most Wanted"],
     "Pulled a brake lever on the other team's cart and stopped it dead.",
     "em_rr_lever", "brakes pulled"),
    ("rr_brakeman", "Brakeman", "rr_releases", [1, 10, 30, 80, 200, 400],
     ["Hand", "Brakeman", "Yardman", "Section Boss", "Roadmaster", "Unstoppable"],
     "Released the brakes the other team pulled on your cart.",
     "em_rr_brake", "brakes released"),
    ("rr_stoker", "Stoker", "rr_coal", [1, 10, 40, 100, 250, 500],
     ["Shoveller", "Stoker", "Fireman", "Boilermaker", "Furnace", "Full Steam"],
     "Carried coal from a heap to your company's cart and stoked it.",
     "em_rr_shovel", "sacks of coal"),
    ("rr_lawman", "Lawman", "rr_guard", [5, 40, 150, 400, 1000, 2500],
     ["Deputy", "Marshal", "Sheriff", "Ranger", "Judge", "Law of the Line"],
     "Knocked out raiders who came within reach of your own cart.",
     "em_rr_star", "raiders stopped"),
    ("rr_photo_finish", "Photo Finish", "rr_photo", [1, 3, 10, 25],
     ["Close Call", "By a Nose", "Hair's Breadth", "Flashbulb"],
     "Won a race with the other cart nine tenths of the way down its own line.",
     "em_rr_camera", "photo finishes"),
    ("rr_signalman", "Signalman", "rr_signal", [1, 10, 30, 80, 200],
     ["Lamp Boy", "Signalman", "Towerman", "Dispatcher", "Master of the Diamond"],
     "Took Dustbowl Gulch's signal cabin and held the other cart at the diamond.",
     "em_rr_signal", "signals set"),
    ("rr_snowplow", "Snowplow", "rr_dig", [1, 10, 30, 80, 200],
     ["Shovel Hand", "Digger", "Snowplow", "Rotary", "Avalanche Breaker"],
     "Dug your cart out of a snowdrift on Silverpine Pass.",
     "em_rr_drift", "drifts dug"),
    ("rr_bridgekeeper", "Bridgekeeper", "rr_winch", [1, 10, 30, 80, 200],
     ["Winch Hand", "Bridge Tender", "Keeper", "Lift Master", "Troll Under the Bridge"],
     "Raised a lift bridge in the other team's path, or lowered one for your own.",
     "em_rr_bridge", "bridges worked"),
    ("rr_canary", "Canary", "rr_canary", [1, 5, 15, 40, 100],
     ["Sniffer", "Canary", "Gas Man", "Firedamp Dodger", "Lungs of Iron"],
     "Got out of a venting firedamp pocket in Lantern Deep before it went up.",
     "em_rr_canary", "close escapes"),
    ("rr_four_lines", "Four Lines", "rr_areas", [1, 2, 3, 4],
     ["Day Tripper", "Two-Line Man", "Three-Line Hand", "Master of the Four Lines"],
     "Won a race on each of Rail Rivals' four railroads.", "em_rr_map", "railroads"),
]

DERIVED = {"rr_areas": "rr_area_"}

# ------------------------------------------------------------------- speech
SPEECH: List[Tuple[str, str, int, str]] = [
    ("rr_depot", "Depot passed", 35,
     "A cart rolls past a depot: its team comes back from there now."),
    ("rr_brake", "Brakes pulled", 45,
     "Somebody pulls a brake lever and a cart stops dead."),
    ("rr_release", "Brakes released", 30,
     "A cart's own team gets to the lever and frees it."),
    ("rr_stoke", "Cart stoked", 25,
     "Coal goes into a cart's firebox and it picks up speed."),
    ("rr_contest", "Cart contested", 20,
     "Enemies are standing on a cart and it has stopped."),
    ("rr_close", "Neck and neck", 45,
     "Both carts are past the last depot and nothing between them."),
    ("rr_signal", "Signal taken", 40,
     "Dustbowl Gulch: a team takes the signal cabin and holds the other cart."),
    ("rr_drift", "Snowed in", 35,
     "Silverpine Pass: a cart runs into a drift and has to be dug out."),
    ("rr_bridge", "Bridge raised", 45,
     "Redrock Mesa: a lift bridge goes up in front of a cart."),
    ("rr_gas", "Firedamp!", 40,
     "Lantern Deep: a firedamp pocket starts venting near the bot."),
]


def _side(event: Dict[str, Any], name: str, team: str) -> Tuple[bool, bool, bool]:
    """(the bot did it, its team did it, it is the bot's own cart)."""
    by = str(event.get("by") or "")
    me = bool(by) and by == name
    mine = bool(team) and str(event.get("by_team") or "") == team
    cart = bool(team) and str(event.get("team") or "") == team
    return me, mine, cart


def describe(kind: str, event: Dict[str, Any], name: str, team: str
             ) -> Optional[Tuple[str, str]]:
    """How a Rail Rivals event reads from one bot's side."""
    me, mine, cart = _side(event, name, team)
    by = str(event.get("by") or "somebody")
    what = str(event.get("what") or "")
    company = str(event.get("company") or "the other company")
    if kind == "rr_depot":
        if cart:
            return ("Your company's cart just rolled past %s; your team respawns there now."
                    % (what or "a depot"), "ally")
        return ("%s's cart just passed %s, further down their line." % (company, what or "a depot"),
                "victim")
    if kind == "rr_brake":
        if me:
            return ("You just pulled the brake lever on %s's cart: it is stuck until "
                    "they come and release it." % company, "actor")
        if cart:
            return ("%s pulled the brakes on YOUR cart near %s. Someone has to go and "
                    "release the lever." % (by, what or "the track"), "victim")
        if mine:
            return ("Your teammate %s pulled the brakes on the other cart." % by, "ally")
        return ("%s pulled a brake lever." % by, "neutral")
    if kind == "rr_release":
        if me:
            return ("You just released the brakes on your own cart.", "actor")
        if cart:
            return ("%s released the brakes on your cart; it can roll again." % by, "ally")
        return ("%s got the brakes off their cart." % by, "victim")
    if kind == "rr_stoke":
        if me:
            return ("You shovelled coal into your cart: it is running fast for a while.",
                    "actor")
        if cart:
            return ("%s stoked your cart with coal; push it while it is fast." % by, "ally")
        return ("%s stoked the other cart with coal and it sped up." % by, "victim")
    if kind == "rr_contest":
        if cart:
            return ("Enemies are standing on your cart and it has stopped; clear them off.",
                    "victim")
        return ("Your team is on the other cart and has it stopped.", "ally")
    if kind == "rr_close":
        return ("Both carts are past their last depot and the race is neck and neck.",
                "ally")
    if kind == "rr_signal":
        if me:
            return ("You took the signal cabin: the other cart is held at the diamond.",
                    "actor")
        if mine:
            return ("%s took the signal cabin for your team; their cart is held at the "
                    "diamond for a while." % by, "ally")
        return ("The other team took the signal cabin: your cart cannot cross the "
                "diamond until it clears or you take it back.", "victim")
    if kind == "rr_drift":
        if cart:
            return ("Your cart ran into a snowdrift near %s; dig it out (hold E by the "
                    "drift)." % (what or "the track"), "victim")
        return ("The other cart is snowed in.", "ally")
    if kind == "rr_bridge":
        if me:
            return ("You winched the lift bridge up in front of %s's cart." % company,
                    "actor")
        if cart:
            return ("%s raised the lift bridge on your line; your cart cannot cross until "
                    "it comes down." % by, "victim")
        return ("Your team raised the bridge on the other line.", "ally")
    if kind == "rr_gas":
        return ("Firedamp is venting near %s and about to go up -- get clear!"
                % (what or "you"), "victim")
    if kind == "round_end" and event.get("world") == WORLD["id"]:
        return None
    return None


CANNED: Dict[Tuple[str, str], List[str]] = {
    ("rr_depot", "ally"): ["depot!", "keep pushing", "nice push", "halfway", "go go"],
    ("rr_depot", "victim"): ["theyre ahead", "push ours", "they passed a depot", "hurry"],
    ("rr_brake", "actor"): ["brakes on lol", "got their brakes", "stuck now"],
    ("rr_brake", "victim"): ["BRAKES", "someone release it", "lever!!", "brakes on our cart"],
    ("rr_brake", "ally"): ["nice brake", "lol their cart", "gj"],
    ("rr_release", "actor"): ["brakes off", "go go go", "released"],
    ("rr_release", "ally"): ["ty", "nice", "push now"],
    ("rr_release", "victim"): ["they released it", "pull it again", "ugh"],
    ("rr_stoke", "actor"): ["coal in", "full steam", "go go"],
    ("rr_stoke", "ally"): ["fast cart", "nice coal", "push push"],
    ("rr_stoke", "victim"): ["their cart is fast", "stop it", "contest it"],
    ("rr_contest", "victim"): ["theyre on our cart", "clear the cart", "help at the cart"],
    ("rr_contest", "ally"): ["sit on it", "stay on their cart", "hold it"],
    ("rr_close", "ally"): ["so close", "its gonna be close", "push!!", "everyone on the cart"],
    ("rr_signal", "actor"): ["signal is ours", "hold the tower", "theyre stuck at the diamond"],
    ("rr_signal", "ally"): ["nice signal", "hold the tower", "push now"],
    ("rr_signal", "victim"): ["take the tower back", "signal!!", "tower"],
    ("rr_drift", "victim"): ["snowed in", "dig!!", "shovels out", "drift on our track"],
    ("rr_drift", "ally"): ["theyre stuck lol", "go go while theyre stuck"],
    ("rr_bridge", "actor"): ["bridge up lol", "no bridge for you", "raised it"],
    ("rr_bridge", "victim"): ["BRIDGE", "they raised the bridge", "lower it!!"],
    ("rr_bridge", "ally"): ["nice bridge", "lol", "theyre stuck"],
    ("rr_gas", "victim"): ["GAS", "get out", "run", "its gonna blow", "move"],
}

# ----------------------------------------------------------------- the bots
BOT_SECTION = ("rail_rivals", "Rail Rivals",
               "How bots race the carts: pushing, raiding, brakes, coal and each line's twist.",
               "⌂")
BOT_INTRO = ("In Rail Rivals every bot takes a job for the race -- pusher, raider, "
             "guard or sniper -- by its personas and how the race is going, and "
             "changes it when the race turns: everybody back to the cart when it "
             "stops, raiders onto the rival cart when it is ahead.")
BOT_FIELDS: List[Tuple[Any, ...]] = [
    ("enabled", "Race the carts", "bool", True,
     "Bots push their own cart, raid the other team's and work the levers, coal "
     "and twists. Off: they just fight round the tracks.", {"toggle": True}),
    ("pushers", "Pushers", "pct", 55,
     "The share of each team that stays with its own cart; objective players, "
     "team players and payload fans most, fraggers least.",
     {"min": 0, "max": 100, "step": 1, "unit": "%", "scope": "base"}),
    ("raiders", "Raiders", "pct", 25,
     "The share that goes after the other team's cart to stop it, sit on it and "
     "fight round it; fraggers and trash talkers most.",
     {"min": 0, "max": 100, "step": 1, "unit": "%", "scope": "base"}),
    ("min_pushers", "Never leave the cart", "int", 1,
     "However the personas fall, at least this many bots of a team stay on its "
     "cart (while the team has that many bots).",
     {"min": 0, "max": 4, "step": 1, "unit": "bots"}),
    ("sabotage", "Pull the brakes", "pct", 60,
     "How keen a raider is to run to a brake lever when the other cart is about "
     "to pass it; chaotic personas pull them for fun.",
     {"min": 0, "max": 100, "step": 1, "unit": "%", "scope": "base"}),
    ("release", "Release the brakes", "pct", 85,
     "How quickly a bot whose cart has been braked goes to free it; support "
     "personas first.", {"min": 0, "max": 100, "step": 1, "unit": "%", "scope": "base"}),
    ("coal", "Fetch coal", "pct", 40,
     "Chance a pusher with nothing to fight goes for a sack of coal and stokes "
     "the cart with it.", {"min": 0, "max": 100, "step": 1, "unit": "%", "scope": "base"}),
    ("twist", "Play the line's twist", "pct", 70,
     "How much bots work each line's twist: take the signal cabin, dig the drifts, "
     "winch the lift bridges, keep clear of firedamp.",
     {"min": 0, "max": 100, "step": 1, "unit": "%", "scope": "base"}),
    ("snipers", "Snipers on the perches", "pct", 30,
     "How much sniper mains and veterans hold the high places over the line: "
     "water towers, the tipple, the mesa top, the scaffold decks.",
     {"min": 0, "max": 100, "step": 1, "unit": "%", "scope": "base"}),
    ("callouts", "Callouts", "bool", True,
     "Bots shout the race's moments in quick chat: brakes on, snowed in, bridge "
     "up, gas. The language model's own reactions come from the speech events."),
]
PERSONA_TIES: List[Tuple[str, str]] = [
    ("Objective player, Team player, Payload enjoyer",
     "Stay on their own cart and push; stand on it when the other side contests it."),
    ("Fragger, Shotgun rusher, Trash talker",
     "Raid the rival cart, sit on it and fight round it; first to its brake levers."),
    ("Sniper main, Veteran", "Hold the perches over the line: water towers, the tipple, "
     "the mesa top, the scaffold decks."),
    ("Helpful, Wholesome, Support", "Fetch coal for the cart and run to release the brakes."),
    ("Explorer, Chaotic, Kid", "Wander off to the sights, ride the lift bridges, pull a "
     "lever just to see what happens."),
    ("Rail fan", "Knows every lever and depot; plays the line's twist first and calls it."),
]
PERSONA_TAG = {"id": "rail_fan", "label": "Rail fan",
               "prompt": "Loves Rail Rivals and anything with rails; knows every lever, "
                         "depot and twist on the four lines.",
               "weight": 0.9, "fx": {"w_rail_rivals": 2.4, "objective": 0.06}}
PROMPT = ("Rail Rivals is a payload race on BLOCKHAVEN: two railroad companies, the "
          "Crimson Line (red team) and the Bluebird Express (blue team), each push an "
          "ore cart along their own track to the far terminus, and the first cart "
          "there wins. Standing next to your cart pushes it; an enemy next to it stops "
          "it (contested). Brake levers beside the tracks lock a cart until its own "
          "team releases them; coal from the heaps makes a cart run fast; every depot "
          "a cart passes moves its team's respawn up the line. There are four "
          "railroads and each has a twist: Dustbowl Gulch's signal tower, Silverpine "
          "Pass's snowdrifts, Redrock Mesa's lift bridges over the gorge and Lantern "
          "Deep's firedamp. Players talk in short bursts: 'push', 'on the cart', "
          "'contest', 'brakes!', 'release it', 'coal', 'bridge up', 'gas'.")
HISTORY = {"kills": 0.85, "deaths": 0.85, "round_minutes": 5.5, "win": 0.48}


def history_badges(history: Dict[str, Any], traits: Dict[str, float], rng
                   ) -> List[Tuple[str, int, str]]:
    """The badge stats a new bot's made-up Rail Rivals history earned."""
    rounds = int(history.get("rounds", 0) or 0)
    wins = int(history.get("wins", 0) or 0)
    if rounds <= 0:
        return []
    objective = float(traits.get("objective", 0.6))
    chaos = float(traits.get("chaos", 0.2))
    support = float(traits.get("support", 0.2))
    skill = float(traits.get("skill", 0.5))
    out = [("rr_wins", wins, "add"),
           ("rr_pushed", int(rounds * rng.uniform(60, 240) * (0.3 + objective)), "add"),
           ("rr_levers", int(rounds * rng.uniform(0.0, 0.6) * (0.3 + chaos)), "add"),
           ("rr_releases", int(rounds * rng.uniform(0.0, 0.5) * (0.3 + support)), "add"),
           ("rr_coal", int(rounds * rng.uniform(0.0, 0.7) * (0.3 + support)), "add"),
           ("rr_guard", int(int(history.get("kills", 0) or 0) * rng.uniform(0.15, 0.4)), "add"),
           ("rr_photo", int(wins * rng.uniform(0.0, 0.08)), "add"),
           ("rr_signal", int(rounds / 4.0 * rng.uniform(0.0, 0.5) * (0.4 + objective)), "add"),
           ("rr_dig", int(rounds / 4.0 * rng.uniform(0.0, 1.2) * (0.4 + objective)), "add"),
           ("rr_winch", int(rounds / 4.0 * rng.uniform(0.0, 0.7) * (0.4 + chaos)), "add"),
           ("rr_canary", int(rounds / 4.0 * rng.uniform(0.0, 0.6) * (0.4 + skill)), "add")]
    areas = [a["id"] for a in WORLD["areas"]]
    rng.shuffle(areas)
    for area in areas[:min(len(areas), wins // 3)]:
        out.append(("rr_area_" + area, 1, "max"))
    return out


# a race runs three to five minutes: the tests need this long to see three
TEST_SECONDS = 1000.0

DORMANT = {"round_seconds": 300.0, "rounds_per_area": 2, "intermission": 15.0,
           "teams": ["red", "blue"], "kills": 0.85, "deaths": 0.85, "swap": False}
