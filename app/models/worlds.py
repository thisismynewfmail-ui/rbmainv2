"""World registry and world statistics.

The registry is the single source of truth shared by the website (world
browser, previews) and by the game host processes (round rules, capacity).
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from .. import db

# Blackout Relay's rotation, as the world page shows it.  The game side's
# list of the same maps is app/game/maps/relay/areas.py (and Ironvale).
RELAY_AREAS: List[Dict[str, Any]] = [
    {"id": "ironvale", "name": "Ironvale Relay", "thumb": "relay",
     "captures": 5, "minutes": 30,
     "blurb": "Dusk over a long green valley: both teams deploy out of the concrete "
              "relay station in the middle, the keeps are a long run apart, and a "
              "hatch behind each keep drops into tunnels that surface in all four "
              "bunkers."},
    {"id": "substation", "name": "Substation Nine", "thumb": "br_substation",
     "captures": 3, "minutes": 15,
     "blurb": "A city in a blackout, in the rain. Deploy from the substation's control "
              "house, climb the terraces to the office towers at each end, and take "
              "the dead subway line under it all."},
    {"id": "thimble", "name": "Thimble Acre", "thumb": "br_thimble",
     "captures": 3, "minutes": 15,
     "blurb": "A back garden at golden hour, and you are the size of a toy. Muster in an "
              "upturned flowerpot, raid the brick castles at either end of the lawn, and "
              "run the garden hose -- inside it or along the top."},
    {"id": "orrery", "name": "The Orrery", "thumb": "br_orrery",
     "captures": 3, "minutes": 15,
     "blurb": "A clockwork garden at twilight. Muster in the clockhouse under a brass sun, "
              "fight for the planet decks over the sunken plaza, and steal the flag from a "
              "glasshouse full of palms -- or come up the gear tunnel from its boiler room."},
    {"id": "saltglass", "name": "Saltglass Flats", "thumb": "br_saltglass",
     "captures": 3, "minutes": 15,
     "blurb": "A dry salt lake at night under a lightning storm. Deploy from Capacitor Hall "
              "under its Tesla coils, climb the mesas to the salt works, and run the dry "
              "washes under arches of salt crust."},
    {"id": "drawdown", "name": "Drawdown", "thumb": "br_drawdown",
     "captures": 3, "minutes": 15,
     "blurb": "A reservoir drained by drought, and the village it drowned is back. Muster "
              "at the valve tower, fight down the silted high street and the dry river, "
              "and take the flags from the chapels on their hills -- or come up the "
              "culvert into the crypt."},
    {"id": "lantern", "name": "Lantern Terraces", "thumb": "br_lantern",
     "captures": 3, "minutes": 15,
     "blurb": "A tea estate on the night of the lantern festival. Muster in the pagoda "
              "under a thousand lanterns, cross the koi streams and the bamboo, and climb "
              "the terraces of tea to the tea houses on the hilltops -- or take the old tea "
              "cellar through the hill."},
    {"id": "meteora", "name": "Meteora", "thumb": "br_meteora",
     "captures": 3, "minutes": 15,
     "blurb": "Monasteries on top of rock pillars in the morning mist. Muster in the "
              "chapel down in the valley, then climb to the flags -- up the switchback cut "
              "in the cliff, or the hermits' way: over the rope bridge and up the chimney "
              "inside the rock."},
    {"id": "circuit", "name": "Circuit City", "thumb": "br_circuit",
     "captures": 3, "minutes": 15,
     "blurb": "A motherboard at night, and you are the size of a transistor. Muster in the "
              "processor, fight through the heatsink's fins under its fan, run the copper "
              "traces past capacitor towers to the flags in the I/O blocks -- or the cable "
              "trenches under the board."},
    {"id": "snowglobe", "name": "Snowglobe Hollow", "thumb": "br_snowglobe",
     "captures": 3, "minutes": 15,
     "blurb": "An alpine village inside a snow globe on somebody's mantelpiece -- and they "
              "keep shaking it. Muster in the town hall under its clock, past the carousel "
              "and the toy train; the flags are in the chalets on the hills, each with an "
              "ice tunnel from beside the flag to the edge of the village."},
    {"id": "bigear", "name": "Big Ear Array", "thumb": "br_bigear",
     "captures": 3, "minutes": 15,
     "blurb": "A radio telescope field in the desert at night, and every dish on it turns to "
              "follow whoever carries a flag. Muster in the control building, run the rails "
              "to the receiver houses -- or take the arroyo, and the cable duct up into the "
              "flag room."},
    {"id": "polder", "name": "Polderhaven", "thumb": "br_polder",
     "captures": 3, "minutes": 15,
     "blurb": "Spring in the polder: dikes, canals, tulips, and nothing flat. Muster in the "
              "steam pumping station, cross the drawbridge and climb the dike to the great "
              "windmills where the flags are -- or come up the mill's drain from the sluice."},
    {"id": "leviathan", "name": "Leviathan Quarry", "thumb": "br_leviathan",
     "captures": 3, "minutes": 15,
     "blurb": "A sea monster's bones in a sandstone quarry at sunset. Muster in the dig "
              "station inside its skull, climb its ribs and run its spine, and take the flags "
              "from the winding houses up on the rim -- or come up the old adit beside them."},
    {"id": "stacks", "name": "The Grand Stacks", "thumb": "br_stacks",
     "captures": 3, "minutes": 15,
     "blurb": "A library the size of a cathedral, all of it indoors. Muster in the rotunda "
              "round the great globe, run the nave between the shelves or take the library "
              "steps up onto their tops, and lift the flags from the map tables. Books fly. "
              "The librarian is dead, and does not care for gunfire."},
    {"id": "steamworks", "name": "Steamworks Caldera", "thumb": "br_steamworks",
     "captures": 3, "minutes": 15,
     "blurb": "A geothermal power station in a volcano at dusk. Muster in the turbine hall on "
              "its island in the steaming lake; the flags are up on the rim in the wellhead "
              "stations. Run the pipe bridge high over everything, wade the hot lake past the "
              "geysers, or come up the steam tunnel beside the flag."},
    {"id": "saddleback", "name": "Saddleback Observatory", "thumb": "br_saddleback",
     "captures": 3, "minutes": 15,
     "blurb": "Twin summits under the aurora, a telescope dome on each. Muster in the cable "
              "car's mid-station in the saddle and climb for the flags -- the cliff bands only "
              "give at the trails -- while the cabins ride the cables overhead. Something on "
              "the saddle is watching you back."},
]

WORLDS: List[Dict[str, Any]] = [
    {
        "id": "burger_tycoon",
        # Retired from the browser: no page, no host, no bots (see HIDDEN_WORLDS).
        "hidden": True,
        "name": "Burger Tycoon",
        "genre": "Tycoon",
        "creator": "BLOCKHAVEN",
        "tagline": "Claim a plot. Flip the burgers. Build the empire.",
        "description": (
            "Eight plots, eight crews, one endless lunch rush. Claim an empty "
            "plate of land, buy your first grill and let the passive income "
            "roll in. Every building you unlock is welded onto your restaurant "
            "in real time. Nothing ever ends here -- players drift in and out "
            "and the world keeps cooking."),
        "max_players": 24,
        "team_count": 8,
        "mode": "endless",
        "shuffle": False,
        "round_label": "Endless world",
        "colors": ["#f2b01e", "#e2621b", "#8a5a2b"],
        "thumb": "burger",
        "features": ["8 claimable plots", "Idle + active income",
                     "Animated build-up", "No round timer"],
    },
    {
        "id": "capture_the_flag",
        # Retired from the browser: no page, no host, no bots (see HIDDEN_WORLDS).
        "hidden": True,
        "name": "Capture The Flag",
        "genre": "Classic Shooter",
        "creator": "BLOCKHAVEN",
        "tagline": "Crossroads never died. It just respawned.",
        "description": (
            "The classic. Two forts either side of a green valley, a bridge "
            "nobody survives, and a flag that will not carry itself. First "
            "team to three captures takes the round. Shuffle vote after every "
            "match."),
        "max_players": 16,
        "team_count": 2,
        "mode": "captures",
        "shuffle": True,
        "round_label": "First to 3 captures",
        "colors": ["#4b974b", "#0d69ac", "#c4281c"],
        "thumb": "ctf",
        "features": ["2 teams", "Flag carrying + returns", "Round shuffle vote",
                     "Classic block map"],
    },
    {
        "id": "fortress_team_2",
        # Retired from the browser: no page, no host, no bots (see HIDDEN_WORLDS).
        "hidden": True,
        "name": "Fortress Team 2",
        "genre": "Objective Shooter",
        "creator": "BLOCKHAVEN",
        "tagline": "Push the cart. Stop the cart. Repeat forever.",
        "description": (
            "Blue pushes the bomb cart along the rails towards Red's fortress. "
            "Stand near it and it rolls; leave it alone and it slides back. "
            "Three checkpoints, three round wins, and teams swap ends after "
            "every round."),
        "max_players": 24,
        "team_count": 2,
        "mode": "payload",
        "shuffle": True,
        "round_label": "First to 3 round wins",
        "colors": ["#b8383b", "#5885a2", "#c9b48b"],
        "thumb": "payload",
        "features": ["Payload cart", "3 checkpoints", "Team swap each round",
                     "Setup timer"],
    },
    {
        "id": "blackout_relay",
        "display_order": 2,
        # the day it opened (the home page's "Newest added")
        "added": "2026-09-20",
        "name": "Blackout Relay",
        "genre": "Team Objective",
        "creator": "BLOCKHAVEN",
        "tagline": "Two bases, one relay, and a tunnel nobody is watching.",
        "description": (
            "Dusk over Ironvale. Both teams deploy out of the same concrete "
            "relay station in the middle of the valley -- red out of the west "
            "doors, blue out of the east -- and everything after that is a "
            "race to the other end and back. Lose your own flag and your team "
            "falls back to the bunkers on your half, right across the "
            "carrier's way home. There is a hatch behind every keep, and the "
            "tunnels under the valley surface inside all four bunkers. "
            "Respawns come in waves, so your team arrives together. Half an "
            "hour on the clock, first to five captures, and the clock cannot "
            "end a round while a flag is still out there."),
        "max_players": 24,
        "team_count": 2,
        "mode": "captures",
        "shuffle": True,
        "round_label": "Capture the flag",
        "colors": ["#3f7a4a", "#c4281c", "#0d69ac"],
        "thumb": "relay",
        # This world hides enemy health on the nametags: you can read your
        # own team's condition at a glance, but an enemy is just a name.
        "ally_health_only": True,
        "features": ["24 players", "A rotation of maps", "Respawn waves",
                     "Outpost lockdown", "Secret routes",
                     "Overtime + sudden death"],
        # The rotation (app/game/maps/relay/): when a round ends the server
        # rolls the next map at random.  ``captures`` and ``minutes`` are
        # each map's round; the sleeping rounds read them too.
        "areas": RELAY_AREAS,
        "areas_note": "When a round ends the server rolls the next map at random and "
                      "everybody goes there. Ironvale's long valley is first to five "
                      "in half an hour; every other map is first to three in fifteen "
                      "minutes -- and overtime and sudden death everywhere.",
        "thumb_script": "/static/js/worlds/blackout_relay_thumbs.js",
        "game_scripts": ["/static/js/worlds/blackout_relay_rigs.js",
                         "/static/js/worlds/blackout_relay.js"],
        "prefix": "br",
    },
    # Appended last on purpose: the bot director snapshots each bot's world
    # as an index into this list, so a new world goes on the end.
    {
        "id": "last_light",
        # the day it opened (the home page's "Newest added")
        "added": "2026-10-01",
        # listed first wherever worlds are shown (home, Jump back in, the
        # world browser); the registry's own order stays put because the
        # bot director indexes worlds by position
        "display_order": 1,
        "name": "Last Light",
        "genre": "Zombie Survival",
        "creator": "BLOCKHAVEN",
        "tagline": "Hold the line. Wave after wave. Until the last light goes out.",
        "description": (
            "Harrow County fell in a single night. You and up to twenty-three "
            "others hold out against the infected, wave after wave, in one of "
            "four places the outbreak reached first -- Harrow's main street, "
            "St. Agnes Medical, the Blackwater docks or the Cedar Pines "
            "campground. Every wave is bigger than the last; every fifth "
            "brings a Tank. Eleven kinds of special infected hunt the slow, "
            "the careless and the alone: Bloaters, Bombers, Leapers, Brutes, "
            "Spitters, Screamers, Riot infected, the Plague Captain, Hives, "
            "Ronin and Burrowers. Go down and a teammate can pick you up; die "
            "and you watch the others until the next wave brings you back. "
            "When the last survivor falls, the round ends -- and the next one "
            "starts somewhere else."),
        "max_players": 24,
        "team_count": 1,
        "mode": "survival",
        "shuffle": False,
        "round_label": "Survive the waves",
        "colors": ["#5d8a4e", "#8a2a1c", "#e0a040"],
        "thumb": "lastlight",
        "features": ["24 players", "Endless waves", "Tank every 5th wave",
                     "11 special infected", "4 shuffled locations",
                     "Revive your team", "Spectate while dead"],
        # the newer places' moving scenery, weather and arrival scenes, and
        # their pictures on the world page (static/js/worlds/last_light*.js)
        "thumb_script": "/static/js/worlds/last_light_thumbs.js",
        "game_scripts": ["/static/js/worlds/last_light_rigs.js",
                         "/static/js/worlds/last_light.js"],
        # The places a round can be played in, in shuffle order, for the
        # world page's location gallery.  Each id is the map's own area id.
        "areas": [
            {"id": "town", "name": "Harrow Main Street",
             "blurb": "Dusk on a small-town main street: the sheriff's "
                      "office, a diner, a church whose bell carries for "
                      "miles, a gas station that should not be shot at, "
                      "back yards and a rail yard full of boxcars."},
            {"id": "hospital", "name": "St. Agnes Medical",
             "blurb": "A hospital the army tried to quarantine. Hold the "
                      "checkpoint, fight up the four-storey parking garage, "
                      "and listen for the ambulances."},
            {"id": "docks", "name": "Blackwater Docks",
             "blurb": "Night and harbour fog. Container mazes, a cargo ship "
                      "you can board, warehouses with catwalks and a "
                      "lighthouse at the end of the breakwater."},
            {"id": "camp", "name": "Cedar Pines Camp",
             "blurb": "A lakeside summer camp in the last of the sunset: "
                      "cabins round their fire pits, a mess hall with a "
                      "dinner bell, a fire lookout tower, a boathouse on "
                      "the lake and a terraced ridge with an old mine "
                      "running under it."},
            {"id": "drivein", "name": "Starlite Drive-In",
             "blurb": "A drive-in on the county line, the night the feature "
                      "was the end of the world. Hold the snack bar on its "
                      "mound, climb the scaffold behind the screen to the "
                      "walkway on top, and crank the movie's sound to send "
                      "the horde for the screen. They come out of the corn."},
            {"id": "zoo", "name": "Harrow County Zoo",
             "blurb": "Golden hour on the last day it was open. Hold the vet "
                      "hospital, run the monorail's loop on its stilts, watch "
                      "the penguins from the gallery under their pool -- and "
                      "play the showtime jingle to send the horde down into "
                      "the sea lion arena. The animals are watching you."},
            {"id": "aquarium", "name": "Harrow Point Aquarium",
             "blurb": "On the headland, the night the storm came in. Hold the "
                      "marine rescue centre, walk the shark tunnel, climb the "
                      "Great Hall's balcony under the whale -- and start the "
                      "dolphin show to send the horde into the pool on the "
                      "cliff edge. They are coming up out of the sea."},
            {"id": "backlot", "name": "Silver Screen Studios",
             "blurb": "A film studio's backlot on the night of a night shoot. "
                      "Hold the commissary, fight down a western street of false "
                      "fronts from the galleries behind their windows, take the "
                      "subway set, the moon and the castle hall in the sound "
                      "stages, the pirate ship in its tank -- and fire the war "
                      "set's special effects. The infected were the cast."},
            {"id": "fair", "name": "Harrow County Fair",
             "blurb": "The last night of the county fair, the lights just on. "
                      "Hold the exhibition hall among the quilts and the pies, "
                      "find the lookout in the middle of the corn maze, climb "
                      "the hay pyramid and the grain elevator -- and start the "
                      "demolition derby from the grandstand to send the horde "
                      "into the mud pit. The rides are still turning."},
            {"id": "bogs", "name": "Redwater Cranberry Bogs",
             "blurb": "Harvest night, the bogs flooded and the water solid with "
                      "floating berries, red from bank to bank. Hold the "
                      "screenhouse, wade the bogs between the narrow dikes, take "
                      "the windmill's stage and the duck blind -- and open the "
                      "reservoir's floodgate to pull the horde out into the "
                      "harvest bog. The water was red before any of this."},
            {"id": "mill", "name": "Kettle Falls Mill",
             "blurb": "A mill town in a river gorge, the autumn it ended. Hold "
                      "the counting house, cross the gorge by the dam, the "
                      "covered bridge or the swaying footbridge, take the mill "
                      "roof and its belfry -- and blow the mill whistle to call "
                      "the dead back to the yard for their shift. The wheel "
                      "never stopped turning."},
            {"id": "launchpad", "name": "Launch Complex 9",
             "blurb": "The night of the launch that never went. Hold the domed "
                      "blockhouse behind its blast door, climb the service "
                      "structure for the view, cross the pad under the moon "
                      "rocket -- and resume the countdown to light the engines "
                      "in the flame trench and bring the horde onto the pad. "
                      "Mind the canal."},
            {"id": "cistern", "name": "The Underneath",
             "blurb": "Harrow's floodworks, under the town, the night of the "
                      "storm. Hold the gatekeeper's office, cross the great "
                      "cistern on its catwalks among the pillars, walk the old "
                      "subway platform the floodworks swallowed -- and start the "
                      "pumps to pull the horde into the pit. The only sky is a "
                      "grate."},
            {"id": "rooftops", "name": "Rooftops of Harrow Heights",
             "blurb": "A snowy night in December, across the roofs of a city "
                      "block. Hold the penthouse, cross the alleys on planks, "
                      "take the construction site's top deck and the "
                      "billboard's catwalk -- and light the billboard to bring "
                      "the horde up for it. It's a long way down to the street."},
            {"id": "gardens", "name": "Glasshouse Gardens",
             "blurb": "The botanic gardens, the night the corpse flower "
                      "bloomed. Hold the Orangery among the lemon trees, take "
                      "the Palm House gallery under the dome and the treetop "
                      "walkway through the arboretum, cross the Lily House on "
                      "the giant lily pads -- and open the Titan House's vents "
                      "to let the stink of the corpse flower draw the dead. "
                      "Mind the flytraps."},
            {"id": "fireworks", "name": "Blackpowder Fireworks Co.",
             "blurb": "The fireworks works, the night before the Fourth. Hold "
                      "the office, fight among the magazines buried in their "
                      "mounds and the mixing sheds in their horseshoes of "
                      "earth, climb the giant rocket's gantry and the hall "
                      "roof -- and light the finale in the firing bunker to "
                      "send the whole show up and bring every one of the dead "
                      "to watch. There are fuel drums everywhere."},
        ],
        # Know your enemy: the world page's bestiary, in the order they
        # turn up.  ``kind`` is the infected kind (engine/zombies.js draws
        # the portrait); ``wave`` is the first wave it can appear in.
        "bestiary": [
            {"kind": "common", "name": "Infected", "wave": 1,
             "blurb": "Green, slow-witted and never alone. Two in the body "
                      "or one in the head.",
             "tip": "Back up while you shoot -- they hit harder in a crowd."},
            {"kind": "runner", "name": "Runner", "wave": 3,
             "blurb": "Fresh, fast and frantic: faster than you can walk.",
             "tip": "Turn and fight; you will not outrun one."},
            {"kind": "bloater", "name": "Bloater", "wave": 1,
             "blurb": "Swollen with bile. Pops when it dies and soaks "
                      "everyone close, and the horde comes for the smell.",
             "tip": "Kill it at range, never in the middle of your team."},
            {"kind": "spitter", "name": "Spitter", "wave": 1,
             "blurb": "Lobs acid that pools and burns hotter the longer you "
                      "stand in it.",
             "tip": "Move out of the green. It cannot spit and run at once."},
            {"kind": "leaper", "name": "Leaper", "wave": 2,
             "blurb": "Pounces from a long way off and pins you to the floor, "
                      "clawing.",
             "tip": "Shoot or shove it off a pinned friend; mash E if it is you."},
            {"kind": "bomber", "name": "Bomber", "wave": 2,
             "blurb": "Wears a vest of dynamite and runs for the biggest "
                      "group it can find.",
             "tip": "A clean headshot defuses it. Anything else, it goes off."},
            {"kind": "brute", "name": "Brute", "wave": 3,
             "blurb": "One arm grown into a club. Charges in a straight line "
                      "and knocks people flying.",
             "tip": "Sidestep the charge -- it stuns itself on walls."},
            {"kind": "screamer", "name": "Screamer", "wave": 3,
             "blurb": "Hangs back and shrieks, calling more of them and "
                      "driving the rest into a frenzy.",
             "tip": "Kill it first. Every scream is another pack."},
            {"kind": "riot", "name": "Riot", "wave": 4,
             "blurb": "Riot gear and a shield: bullets from the front barely "
                      "scratch it.",
             "tip": "Flank it, or shove it with a melee hit to open it up."},
            {"kind": "hive", "name": "Hive", "wave": 5,
             "blurb": "A walking nest. When it dies it bursts into a swarm "
                      "of fast, biting mites.",
             "tip": "Shotguns and explosions clear the swarm."},
            {"kind": "burrower", "name": "Burrower", "wave": 6,
             "blurb": "A miner who digs under the ground and comes up "
                      "beneath your feet.",
             "tip": "Watch for the moving earth and keep moving."},
            {"kind": "ronin", "name": "Ronin", "wave": 7,
             "blurb": "Guards with his blade and turns bullets aside, then "
                      "dashes in for a cut.",
             "tip": "Hit him from the side, or when he is open after a slash."},
            {"kind": "captain", "name": "Plague Captain", "wave": 8,
             "blurb": "A drowned captain with a lantern of plague fire. "
                      "Throws poison and raises the fallen.",
             "tip": "Hunt him down before the dead get back up."},
            {"kind": "tank", "name": "Tank", "wave": 5,
             "blurb": "Every fifth wave. Throws chunks of road, slams the "
                      "ground and punches people into next week.",
             "tip": "Everybody shoots. Nobody stands next to it."},
        ],
    },
]

# The event worlds (app/models/event_worlds/) come after the originals, in
# the order that package lists them -- the director's indexes again.
from . import event_worlds as _event_worlds  # noqa: E402

WORLDS.extend(_event_worlds.world_defs())

WORLDS = [db.AttrDict(w) for w in WORLDS]
WORLDS_BY_ID: Dict[str, Dict[str, Any]] = {w["id"]: w for w in WORLDS}


def is_arena(world_id: str) -> bool:
    """A world built from areas played one at a time (an event world)."""
    world = WORLDS_BY_ID.get(world_id)
    return bool(world and world.get("engine") == "arena")

# Worlds that are switched off.  They stay in WORLDS -- the bot director
# stores each bot's world as an index into that list, so removing one would
# shift every index after it -- but nothing outside this module ever sees
# them: no page, no Play button, no game host process, no join ticket, and no
# bot can be sent into one.  A sleeping round left over in a director
# snapshot from before a world was hidden is dropped when the snapshot loads,
# because ``get`` no longer answers for it.
HIDDEN_WORLDS = frozenset(w["id"] for w in WORLDS if w.get("hidden"))


def get(world_id: str) -> Optional[Dict[str, Any]]:
    """A world that is open to play, or None (unknown or hidden)."""
    if world_id in HIDDEN_WORLDS:
        return None
    return WORLDS_BY_ID.get(world_id)


def get_any(world_id: str) -> Optional[Dict[str, Any]]:
    """Any world in the registry, hidden or not -- for development tools that
    deliberately run a retired world's rules headless."""
    return WORLDS_BY_ID.get(world_id)


def is_open(world_id: str) -> bool:
    return world_id in WORLDS_BY_ID and world_id not in HIDDEN_WORLDS


def all_worlds() -> List[Dict[str, Any]]:
    """Every world that is open to play, in display order (``display_order``,
    then registry order): Last Light, then Blackout Relay."""
    open_worlds = [w for w in WORLDS if w["id"] not in HIDDEN_WORLDS]
    return sorted(open_worlds, key=lambda w: (int(w.get("display_order") or 99),
                                             WORLDS.index(w)))


def every_world() -> List[Dict[str, Any]]:
    """The whole registry, hidden worlds included."""
    return list(WORLDS)


# ------------------------------------------------------------------- stats

def ensure_rows() -> None:
    now = int(time.time())
    for world in WORLDS:
        db.execute("INSERT OR IGNORE INTO world_stats(world_id, updated_at)"
                   " VALUES(?,?)", (world["id"], now))


def stats(world_id: str) -> Dict[str, Any]:
    row = db.query_one("SELECT * FROM world_stats WHERE world_id=?", (world_id,))
    if row is None:
        ensure_rows()
        row = db.query_one("SELECT * FROM world_stats WHERE world_id=?",
                           (world_id,))
    data = db.AttrDict(row) if row else db.AttrDict({"world_id": world_id, "visits": 0,
                                  "favourites": 0, "likes": 0, "dislikes": 0,
                                  "peak_players": 0})
    total = data.get("likes", 0) + data.get("dislikes", 0)
    data["rating"] = int(round(100.0 * data.get("likes", 0) / total)) if total else 0
    data["rating_votes"] = total
    return data


def record_visit(world_id: str, user_id: int, seconds: int) -> None:
    now = int(time.time())
    with db.transaction() as conn:
        conn.execute("INSERT OR IGNORE INTO world_stats(world_id, updated_at)"
                     " VALUES(?,?)", (world_id, now))
        conn.execute("UPDATE world_stats SET visits=visits+1, updated_at=?"
                     " WHERE world_id=?", (now, world_id))
        conn.execute("INSERT INTO world_visits(world_id,user_id,created_at,seconds)"
                     " VALUES(?,?,?,?)", (world_id, user_id, now, int(seconds)))
        conn.execute("UPDATE users SET place_visits=place_visits+1 WHERE id=?",
                     (user_id,))


def note_peak(world_id: str, players: int) -> None:
    db.execute("UPDATE world_stats SET peak_players=MAX(peak_players,?),"
               " updated_at=? WHERE world_id=?",
               (int(players), int(time.time()), world_id))


def vote(world_id: str, user_id: int, like: bool) -> Dict[str, Any]:
    if world_id not in WORLDS_BY_ID:
        raise ValueError("Unknown world")
    value = 1 if like else -1
    with db.transaction() as conn:
        conn.execute("INSERT OR IGNORE INTO world_stats(world_id, updated_at)"
                     " VALUES(?,?)", (world_id, int(time.time())))
        prev = conn.execute(
            "SELECT vote FROM world_votes WHERE world_id=? AND user_id=?",
            (world_id, user_id)).fetchone()
        if prev is not None and int(prev["vote"]) == value:
            conn.execute("DELETE FROM world_votes WHERE world_id=? AND user_id=?",
                         (world_id, user_id))
        else:
            conn.execute(
                "INSERT INTO world_votes(world_id,user_id,vote) VALUES(?,?,?)"
                " ON CONFLICT(world_id,user_id) DO UPDATE SET vote=excluded.vote",
                (world_id, user_id, value))
        likes = int(conn.execute(
            "SELECT COUNT(*) FROM world_votes WHERE world_id=? AND vote=1",
            (world_id,)).fetchone()[0])
        dislikes = int(conn.execute(
            "SELECT COUNT(*) FROM world_votes WHERE world_id=? AND vote=-1",
            (world_id,)).fetchone()[0])
        conn.execute("UPDATE world_stats SET likes=?, dislikes=? WHERE world_id=?",
                     (likes, dislikes, world_id))
    return stats(world_id)


def user_vote(world_id: str, user_id: int) -> int:
    return int(db.scalar(
        "SELECT vote FROM world_votes WHERE world_id=? AND user_id=?",
        (world_id, user_id), 0))


def toggle_favourite(world_id: str, user_id: int) -> bool:
    existing = db.query_one(
        "SELECT 1 FROM world_favourites WHERE world_id=? AND user_id=?",
        (world_id, user_id))
    if existing:
        db.execute("DELETE FROM world_favourites WHERE world_id=? AND user_id=?",
                   (world_id, user_id))
        favourited = False
    else:
        db.execute("INSERT INTO world_favourites(world_id,user_id,created_at)"
                   " VALUES(?,?,?)", (world_id, user_id, int(time.time())))
        favourited = True
    count = int(db.scalar("SELECT COUNT(*) FROM world_favourites WHERE world_id=?",
                          (world_id,)))
    db.execute("UPDATE world_stats SET favourites=? WHERE world_id=?",
               (count, world_id))
    return favourited


def favourites_of(user_id: int) -> List[str]:
    return [r["world_id"] for r in db.query(
        "SELECT world_id FROM world_favourites WHERE user_id=? ORDER BY created_at DESC",
        (user_id,))]


def is_favourite(world_id: str, user_id: int) -> bool:
    return db.query_one(
        "SELECT 1 FROM world_favourites WHERE world_id=? AND user_id=?",
        (world_id, user_id)) is not None


# ------------------------------------------------------------- player stats

# Worlds whose enemies are the infected rather than other players: what dies
# there is booked as ``zkills``, never as a kill.
HORDE_WORLDS = ("last_light",)


def add_game_stats(user_id: int, world_id: str, kills: int = 0, deaths: int = 0,
                   wins: int = 0, rounds: int = 0, playtime: int = 0,
                   score: int = 0, zkills: int = 0) -> None:
    """Add to a player's record in one world.  ``kills`` are players (bots
    included) and only players; ``zkills`` are the infected."""
    db.execute(
        "INSERT INTO game_stats(user_id,world_id,kills,deaths,wins,rounds,"
        "playtime,score,zkills) VALUES(?,?,?,?,?,?,?,?,?)"
        " ON CONFLICT(user_id,world_id) DO UPDATE SET"
        " kills=kills+excluded.kills, deaths=deaths+excluded.deaths,"
        " wins=wins+excluded.wins, rounds=rounds+excluded.rounds,"
        " playtime=playtime+excluded.playtime, score=score+excluded.score,"
        " zkills=zkills+excluded.zkills",
        (user_id, world_id, kills, deaths, wins, rounds, playtime, score, zkills))


def player_stats(user_id: int) -> Dict[str, Any]:
    rows = db.rows_to_dicts(db.query(
        "SELECT * FROM game_stats WHERE user_id=?", (user_id,)))
    total = {"kills": 0, "deaths": 0, "wins": 0, "rounds": 0, "playtime": 0,
             "score": 0, "zkills": 0}
    per_world = {}
    for row in rows:
        for key in total:
            total[key] += int(row.get(key, 0) or 0)
        per_world[row["world_id"]] = row
    total["kdr"] = round(total["kills"] / max(1, total["deaths"]), 2)
    return {"total": total, "worlds": per_world}


def leaderboard(world_id: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
    if world_id:
        rows = db.query(
            "SELECT g.*, u.username FROM game_stats g JOIN users u ON u.id=g.user_id"
            " WHERE g.world_id=? ORDER BY g.score DESC, g.kills DESC LIMIT ?",
            (world_id, limit))
    else:
        rows = db.query(
            "SELECT u.username, u.id AS user_id, SUM(g.kills) AS kills,"
            " SUM(g.deaths) AS deaths, SUM(g.score) AS score,"
            " SUM(g.playtime) AS playtime"
            " FROM game_stats g JOIN users u ON u.id=g.user_id"
            " GROUP BY g.user_id ORDER BY score DESC, kills DESC LIMIT ?",
            (limit,))
    return db.rows_to_dicts(rows)


def total_visits() -> int:
    return int(db.scalar("SELECT COALESCE(SUM(visits),0) FROM world_stats"))
