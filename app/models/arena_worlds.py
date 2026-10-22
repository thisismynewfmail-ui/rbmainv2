"""The fifteen arena worlds, as the registry knows them.

Each entry is an ordinary world (``app/models/worlds.py`` appends them after
the original five, because the bot director stores a bot's world as an index
into that list) with a few keys of its own:

``areas``     the places, in order, each with an id (the map's own), a name
              and a blurb for the world page's gallery
``howto``     the world page's "How it plays" steps
``teams``     the sides as the client draws them (name, colour)
``arena``     the sleeping-round numbers (``bots/dormant.py``): round and
              setup length, rounds per place, the sides, kills a minute
``ties``      what each persona does here, for the world's Bots Zone tab
``cols``      the scoreboard's extra columns
"""
from __future__ import annotations

from typing import Any, Dict, List

PREFIX = "ar_"


def _w(order: int, world_id: str, name: str, genre: str, tagline: str, description: str,
       max_players: int, colours: List[str], features: List[str], areas: List[Dict[str, str]],
       howto: List[List[str]], teams: Dict[str, Dict[str, str]], arena: Dict[str, Any],
       ties: List[List[str]], cols: List[List[str]], round_label: str,
       areas_note: str, **extra: Any) -> Dict[str, Any]:
    entry = {
        "id": world_id, "display_order": order, "name": name, "genre": genre,
        "creator": "BLOCKHAVEN", "tagline": tagline, "description": description,
        "max_players": max_players, "team_count": len(teams), "mode": "arena",
        "shuffle": False, "round_label": round_label, "colors": colours,
        "thumb": PREFIX + world_id, "area_prefix": PREFIX + world_id + "_",
        "features": features, "areas": areas, "areas_note": areas_note,
        "howto": [{"title": t, "text": x} for t, x in howto],
        "teams": teams, "arena": arena, "ties": ties, "cols": cols,
    }
    entry.update(extra)
    return entry


def _a(area_id: str, name: str, blurb: str) -> Dict[str, str]:
    return {"id": area_id, "name": name, "blurb": blurb}


ARENA_WORLDS: List[Dict[str, Any]] = [
    # ================================================================ 1
    _w(3, "cataclysm", "Cataclysm", "Survive the Disaster",
       "Find high ground. Find a roof. Find out what the sky does next.",
       "Twenty seconds of calm, then the sky picks a disaster: a flash flood, "
       "a tsunami, a meteor shower, a tornado, acid rain, a lightning storm, an "
       "earthquake, a blizzard, a sandstorm or the volcano itself. Everyone still "
       "standing when it blows over scores, and every disaster survived in a row "
       "is worth more than the last. No weapons do any damage here -- but any hit "
       "still shoves, and the lighthouse balcony is very narrow. Three disasters "
       "in each place, then the town is evacuated to another; from the third "
       "round a place can throw two at once.", 24,
       ["#3f78a8", "#e0a040", "#a83a2a"],
       ["24 players", "10 disasters", "Double Trouble rounds", "Survival streaks",
        "Shove your friends", "4 shuffled places"],
       [_a("harbour", "Breezy Point Harbour",
           "A fishing village on stilts round a little harbour: the lighthouse, the "
           "hill chapel, the water tower and boats that will not save you."),
        _a("ashfall", "Mount Ashfall",
           "A terraced village on a live volcano: rope bridges over the lava "
           "river, the observatory dome and the old mine under the cone."),
        _a("ranch", "Dustbowl Ranch",
           "Big sky country: the red barn, the silo, the windmill, a cornfield, the "
           "farmhouse and -- if you can find it -- the storm cellar."),
        _a("downtown", "Glasstown Downtown",
           "One city block: an office tower to climb, the mall, a parking garage, "
           "the plaza fountain and the subway steps going down.")],
       [["Calm", "Twenty seconds to find somewhere safe. The forecast at the top of "
                 "the screen hints at what is coming."],
        ["Disaster", "Sixty to eighty seconds of it, getting worse. Floods and "
                     "tsunamis want high ground; acid rain, lightning and meteors "
                     "want a roof; tornadoes want walls between you and them."],
        ["Survive", "Everyone standing at the end scores, and a streak pays more "
                    "each time. The fallen watch until the next round."],
        ["Shove", "Weapons do no damage here, but every hit shoves."]],
       {"ffa": {"name": "Survivors", "colour": "#e0a040"}},
       {"round": 85, "setup": 20, "per_area": 3, "teams": ["ffa"], "style": "coop",
        "kpm": 0.0, "dpm": 0.25},
       [["Explorer, Kid", "Climb the tallest thing in reach for the view, disaster or not."],
        ["Chaotic, Trash talker", "Shove people off ledges and into the water."],
        ["Tryhard, Veteran", "Read the disaster at once and go to the right kind of shelter."],
        ["Newbie, Chill", "Late to react; follow whoever looks like they know."],
        ["Social butterfly, Friendly", "Shelter together and cheer every survivor."]],
       [["streak", "Streak"], ["survived", "Survived"]],
       "Survive the disaster",
       "Every place has its own five disasters, its roofs, its high ground and its "
       "deathtraps."),
    # ================================================================ 2
    _w(4, "prop_panic", "Prop Panic", "Prop Hunt",
       "Be the teapot. Hold still. Do not sneeze.",
       "Props hide by turning into anything in the room -- a teapot, a teddy, a "
       "cannonball pile, a watermelon -- while the Hunters wait blindfolded in the "
       "cage. Then the Hunters get three minutes to find them, and every shot at "
       "real scenery costs the Hunter health. Taunt for points, throw a decoy, "
       "and in the last minute everybody hiding squeaks. Teams swap every round, "
       "so everyone hunts once in each place.", 20,
       ["#3fa8d8", "#d8573a", "#f2c84a"],
       ["Props vs Hunters", "Disguise as anything", "Taunts and decoys",
        "Teams swap every round", "4 shuffled places"],
       [_a("cottage", "Grandma Willow's Cottage",
           "Kitchen, parlour, two bedrooms, the attic, a greenhouse and a garden "
           "full of gnomes. Grandma owns a great many teapots."),
        _a("toystore", "Toybox Emporium",
           "Aisles of teddies, blocks, rocking horses and rubber ducks, a train set, "
           "the plush wall and a stockroom out back."),
        _a("museum", "Brine & Barnacle Museum",
           "A maritime museum: the ship hall, the cannon gallery, an aquarium "
           "corridor and a gift shop of anchors and life rings."),
        _a("market", "FreshCo Supermarket",
           "Aisles, the produce section, the freezers, checkouts, a loading dock "
           "of pallets and a car park full of trolleys.")],
       [["Hide", "Props get thirty seconds: look at a prop and press E (or fire the "
                 "Disguise tool) to become one. Settle next to its twins."],
        ["Hunt", "Hunters shoot what they think is a person. Hitting scenery costs "
                 "you health; finding a prop heals you."],
        ["Taunt", "Props can taunt for points and throw a decoy of themselves."],
        ["Swap", "Teams swap every round: everyone hunts once per place."]],
       {"props": {"name": "Props", "colour": "#3fa8d8"},
        "hunters": {"name": "Hunters", "colour": "#d8573a"}},
       {"round": 200, "setup": 30, "per_area": 2, "teams": ["props", "hunters"],
        "style": "teams", "kpm": 0.6, "dpm": 0.3},
       [["Shy, Loner", "Pick the quietest corner and never move."],
        ["Chaotic, Meme speaker", "Taunt all the time and become something silly."],
        ["Tryhard, Veteran", "Hide beside twins of the same prop at the same angle; "
                             "as hunters, check out-of-place props first."],
        ["Fragger, Shotgun rusher", "Hunt aggressively, shoot more hunches."],
        ["Explorer", "Hide in odd places: the attic, the stockroom, the car park."]],
       [["found", "Found"], ["survived", "Survived"]],
       "Hide or hunt",
       "Every place has a dozen kinds of prop, placed many times over, so a careful "
       "prop always has somewhere to blend in."),
    # ================================================================ 3
    _w(5, "rail_rumble", "Rail Rumble", "Payload Race",
       "Your cart. Their cart. One finish line. Mind the junctions.",
       "Both teams push their own cart along their own track; standing by it "
       "moves it, an enemy beside it stops it dead. Junction levers send a cart "
       "round its long detour -- the other team's, if you have any sense -- and "
       "coal hoppers stoke yours for a burst of speed. First cart over the line "
       "wins; when the clock runs out, the one further along does. Two races in "
       "each place.", 24,
       ["#b8383b", "#0d69ac", "#c8a050"],
       ["24 players", "Two carts", "Junction levers", "Coal boosts",
        "Mirrored tracks", "4 shuffled places"],
       [_a("gulch", "Gold Gulch Canyon",
           "Red rock mesas, a mine shaft, the saloon town in the middle and a "
           "trestle bridge both tracks cross."),
        _a("frostbite", "Frostbite Pass",
           "Rock tunnels and avalanche sheds over a frozen lake, with the mountain "
           "station at the top of the pass."),
        _a("temple", "Sunken Temple",
           "Jungle ruins: temple steps, vine arches, rope bridges and the waterfall "
           "the tracks run behind."),
        _a("foundry", "Ironworks Foundry",
           "Molten channels, overhead cranes and catwalks through the casting "
           "hall the tracks thread.")],
       [["Push", "Stand by your cart to move it (up to three of you push faster). "
                 "An enemy next to it stops it."],
        ["Switch", "Hold E on a junction lever to send that track's cart round its "
                   "detour."],
        ["Stoke", "Hold E at a coal hopper while your cart passes to boost it."],
        ["Win", "First cart home, or the further one at the horn."]],
       {"red": {"name": "Red", "colour": "#c4281c"}, "blue": {"name": "Blue", "colour": "#0d69ac"}},
       {"round": 330, "setup": 15, "per_area": 2, "teams": ["red", "blue"], "style": "teams",
        "kpm": 1.0, "dpm": 0.95},
       [["Objective player, Team player", "Ride the cart and stoke it."],
        ["Fragger, Shotgun rusher", "Hunt the enemy's pushers."],
        ["Tryhard, Veteran", "Throw the enemy's junction just before their cart reaches it."],
        ["Explorer, Chaotic", "Go the long way round and pull levers for fun."]],
       [["pushed", "Pushed"], ["switches", "Switches"]],
       "First cart home",
       "Every track has two junctions with a detour loop, and a coal hopper; the "
       "two tracks are point-mirrored so neither side has the shorter run."),
    # ================================================================ 4
    _w(6, "convoy", "Convoy", "Payload Travel",
       "Three places. One armoured truck. Get it through.",
       "The Escort drives the armoured convoy across a route of three legs -- "
       "three of the four places, in a new order every match. Each leg the "
       "convoy rolls in at the west gate and has to reach the east one, breaching "
       "a roadblock on the way. Reach the gate and the convoy rolls on, and "
       "everybody moves to the next place with it. The Ambush wins by holding any "
       "one leg until its clock runs out. Then the sides swap.", 24,
       ["#2f86cf", "#c4281c", "#6a6a6a"],
       ["24 players", "3-leg journeys", "Roadblocks to breach", "New route every match",
        "Checkpoints add time", "4 places"],
       [_a("canal", "Canal Market Quarter",
           "Narrow canals, hump bridges, market stalls and the clock tower over "
           "the square."),
        _a("highway", "Redrock Highway",
           "A desert highway: the gas station, a motel, billboards and the "
           "overpass the road ducks under."),
        _a("pinecrest", "Pinecrest Pass",
           "Mountain switchbacks past the lumber mill and across the top of the "
           "dam."),
        _a("neon", "Neon Boulevard",
           "A night street of holo billboards, monorail pillars and plazas, "
           "straight through downtown.")],
       [["Escort", "Stand by the convoy to drive it (more of you, faster). An "
                   "ambusher beside it stops it; left alone it rolls back."],
        ["Breach", "Each leg has a roadblock: hold E on its generator to open it."],
        ["Roll on", "Reach the east gate and the convoy rolls on to the next place."],
        ["Ambush", "Hold any leg until its clock runs out to win."]],
       {"escort": {"name": "Escort", "colour": "#2f86cf"},
        "ambush": {"name": "Ambush", "colour": "#c4281c"}},
       {"round": 420, "setup": 18, "per_area": 1, "teams": ["escort", "ambush"],
        "style": "teams", "kpm": 1.05, "dpm": 0.95},
       [["Objective player, Team player", "Ride the convoy, breach the roadblock."],
        ["Fragger", "Push ahead of the convoy and clear the next corner."],
        ["Sniper main, Veteran", "Hold the high ground over the road."],
        ["Chaotic, Explorer", "Flank through the side streets."]],
       [["escorted", "Escorted"], ["breaches", "Breaches"]],
       "Escort the convoy",
       "A match is a journey of three legs; the route is drawn fresh every match, "
       "so any place can be the first leg or the last."),
    # ================================================================ 5
    _w(7, "midnight_mystery", "Midnight Mystery", "Murder Mystery",
       "Someone here has a knife. Someone here has a badge. Everyone else, collect coins.",
       "Roles are dealt in secret. The Murderer has a knife and a throw; the "
       "Sheriff has one revolver -- shoot an innocent and you both go down, and "
       "the gun drops for anybody brave enough to pick it up. Innocents gather "
       "the coins scattered about and try never to be alone. The Murderer wins by "
       "getting everyone; everyone else wins if the Murderer falls or the clock "
       "runs out. Three rounds in each place.", 18,
       ["#5a3a7a", "#c42b2b", "#f2c84a"],
       ["Secret roles", "Murderer, Sheriff, Innocents", "Pick up the dropped gun",
        "Coins to collect", "4 shuffled places"],
       [_a("manor", "Ravenhurst Manor",
           "A gothic mansion: the grand hall, the library and its secret passage, "
           "the ballroom, the wine cellar and the upstairs bedrooms."),
        _a("hotel", "Hotel Marigold",
           "An art deco hotel: the lobby, the restaurant, the pool deck, corridors "
           "of rooms and the roof bar."),
        _a("station", "Snowpine Station",
           "A luxury train stopped in a snowstorm: carriage after carriage, the "
           "platforms and the station house."),
        _a("carnival", "Carnevale Nocturne",
           "A night carnival: striped tents, the carousel, the hall of mirrors and "
           "the haunted ride.")],
       [["Roles", "Everyone is told their own role, and only theirs."],
        ["Murderer", "Knife people (one hit) and throw the knife on a cooldown. "
                     "Do not get seen."],
        ["Sheriff", "One shot at a time. Shoot an innocent and you go down too, "
                    "and drop the gun."],
        ["Innocents", "Collect coins, stay in company, and pick up the gun if it "
                      "drops."]],
       {"guests": {"name": "Guests", "colour": "#e0a040"}},
       {"round": 180, "setup": 10, "per_area": 3, "teams": ["guests"], "style": "ffa",
        "kpm": 0.3, "dpm": 0.3},
       [["Shy, Loner", "Wander off alone (and get murdered more)."],
        ["Social butterfly, Friendly", "Stick with a crowd; say who they saw."],
        ["Tryhard, Veteran", "As Murderer, wait for nobody to be watching; as Sheriff, "
                             "only shoot what they saw."],
        ["Chatty, Trash talker", "Accuse people in chat, rightly or not."],
        ["Explorer", "Know the secret passages and coin spots."]],
       [["coins", "Coins"], ["role", "Role"]],
       "Find the Murderer",
       "Every place has rooms to be alone in, crowds to hide among and a coin trail "
       "through all of it."),
    # ================================================================ 6
    _w(8, "grand_heist", "Grand Heist", "Cops & Robbers",
       "Crack the vault. Grab the bags. Run for the getaway.",
       "Robbers crack vaults, grab the loot bags and run them to the getaway; "
       "Cops taser them, cuff them while they are stunned and send them to the "
       "cell -- which a free robber can spring. Robbers win at the take target, "
       "Cops by running out the clock or having the whole crew in the cell at "
       "once. Nobody dies: it is stuns, cuffs and jailbreaks. Sides swap every "
       "round; two rounds in each place.", 24,
       ["#e2621b", "#2f5fa8", "#f2d23a"],
       ["Robbers vs Cops", "Vaults and loot bags", "Tasers and cuffs", "Jailbreaks",
        "Sides swap", "4 shuffled places"],
       [_a("bank", "First Blockhaven Bank",
           "Marble lobby, offices, the vault level downstairs, and a getaway van in "
           "the alley."),
        _a("casino", "Royal Flush Casino",
           "The gaming floor, the cashier cage and its vaults, the penthouse and the "
           "garage."),
        _a("tower", "Crown Jewel Tower",
           "A castle keep: the jewel house, the armouries, the battlements and a "
           "boat waiting on the moat."),
        _a("railyard", "Gold Express Railyard",
           "The gold train in its sidings, signal towers, warehouses and a truck "
           "waiting at the gate.")],
       [["Crack", "Robbers: hold E on a vault until it opens. A taser hit stops you."],
        ["Carry", "Grab a loot bag (one at a time, and it slows you) and run it to "
                  "the getaway."],
        ["Cuff", "Cops: taser a robber to stun them, hit them again to cuff them."],
        ["Spring", "A free robber can hold E on the cell switch to free everyone."]],
       {"robbers": {"name": "Robbers", "colour": "#e2621b"},
        "cops": {"name": "Cops", "colour": "#2f5fa8"}},
       {"round": 300, "setup": 15, "per_area": 2, "teams": ["robbers", "cops"],
        "style": "teams", "kpm": 0.8, "dpm": 0.7},
       [["Objective player", "Crack vaults and run bags."],
        ["Team player, Wholesome", "Spring the cell; escort the bag carrier."],
        ["Fragger, Tryhard", "As a cop, chase down carriers first."],
        ["Chill, Shy", "As a cop, guard the getaway."],
        ["Chaotic", "Run the long way round the building."]],
       [["loot", "Loot"], ["arrests", "Arrests"]],
       "Rob it or stop it",
       "Every place has several vaults, a getaway, a cell and a switch to spring it."),
    # ================================================================ 7
    _w(9, "splat_turf", "Splat Turf", "Turf War",
       "Paint the ground your colour. That is the whole idea.",
       "Three minutes to paint as much of the floor as you can with the Splat "
       "Blaster, the Roller and the Lobber. Ink refills fast standing in your own "
       "colour; the other team's slows you down. Splat someone and they go back to "
       "spawn. The last thirty seconds are a Splat Rush. Coverage at the horn "
       "decides it. Two rounds in each place.", 16,
       ["#ff4fa8", "#1fc8b8", "#f2f3f3"],
       ["Paint the floor", "Blaster, Roller, Lobber", "Ink refills in your colour",
        "Splat Rush finale", "4 shuffled places"],
       [_a("skatepark", "Rad Ramps Skatepark",
           "Bowls, stepped ramps, rails and a graffiti wall that is already "
           "losing."),
        _a("aquarium", "Coral Commons Aquarium",
           "The glass tunnel, the tank halls, the shark pool and the plaza "
           "fountains."),
        _a("rooftops", "Rooftop Gardens",
           "City rooftops joined by footbridges, greenhouses and water towers."),
        _a("gumdrop", "Gumdrop Works",
           "A candy factory: conveyor lines, giant gumdrops, the mixing vats and "
           "catwalks overhead.")],
       [["Paint", "Everything you shoot paints the floor where it lands."],
        ["Ink", "Ink is your ammo. Stand in your own colour to refill fast."],
        ["Splat", "Hit enemies to splat them back to their spawn."],
        ["Cover", "Most coverage at the horn wins. The last 30 s are a Splat Rush."]],
       {"pink": {"name": "Pink", "colour": "#ff4fa8"}, "teal": {"name": "Teal", "colour": "#1fc8b8"}},
       {"round": 180, "setup": 10, "per_area": 2, "teams": ["pink", "teal"], "style": "teams",
        "kpm": 1.3, "dpm": 1.3},
       [["Objective player", "Paint the open ground and the far corners."],
        ["Fragger, Shotgun rusher", "Push into enemy paint and splat."],
        ["Tryhard", "Paint behind the enemy line, then defend it."],
        ["Chaotic, Kid", "Roll everything in sight."]],
       [["painted", "Painted"], ["splats", "Splats"]],
       "Paint the most ground",
       "Every place's floors, ramps and rooftops are paintable; walls are not."),
    # ================================================================ 8
    _w(10, "bonk_brawl", "Bonk Brawl", "Knockback Brawl",
       "The higher your bonk, the further you fly.",
       "Every hit raises your bonk percentage, and the higher it climbs the further "
       "the next hit throws you. Knock everybody else off the arena. Three stocks "
       "each: the last one with any left wins, or the most knock-outs when the clock "
       "runs out. Jump pads throw you across the gaps and power-ups turn up in the "
       "middle of everything. Three rounds in each place.", 16,
       ["#ffcf3a", "#e2621b", "#7a4ae0"],
       ["Bonk percentage", "3 stocks each", "Jump pads", "Power-ups",
        "Low gravity asteroid", "4 shuffled places"],
       [_a("temple", "Cloudtop Temple",
           "Marble islands in the clouds round a temple with a hundred columns."),
        _a("forge", "Magma Forge",
           "Iron platforms over a lava lake, and flame vents that throw you."),
        _a("circus", "Big Top Circus",
           "The rings, the trampolines and the cannon, under the big top."),
        _a("asteroid", "Junkyard Asteroid",
           "Space junk floating in low gravity: floatier jumps, longer flights.")],
       [["Bonk", "Every hit adds to the victim's bonk %. The higher it is, the further "
                 "they fly."],
        ["Knock out", "Fall off the arena and you lose a stock. The last one to hit you "
                      "gets the KO."],
        ["Stocks", "Three each. Last one with stocks wins."],
        ["Power-ups", "Mega Bonk, Feather and Bubble Shield turn up in the middle."]],
       {"ffa": {"name": "Brawlers", "colour": "#ffcf3a"}},
       {"round": 240, "setup": 10, "per_area": 3, "teams": ["ffa"], "style": "ffa",
        "kpm": 1.4, "dpm": 1.2},
       [["Fragger, Melee maniac", "Chase the highest bonk % near an edge."],
        ["Chill, Shy", "Keep to the middle of a platform."],
        ["Tryhard", "Hit people outward, never inward."],
        ["Chaotic, Kid", "Bounce on every jump pad."]],
       [["stocks", "Stocks"], ["kos", "KOs"]],
       "Last brawler standing",
       "Every arena floats over nothing; the edges are the weapon."),
    # ================================================================ 9
    _w(11, "bastion", "Bastion", "Tower Defence",
       "Build the turrets. Hold the road. Keep the core alive.",
       "Waves of robots march down the road to your core. Shoot them for scrap, "
       "spend the scrap on turret pads -- Gatling, Cannon, Frost and Tesla, each "
       "upgradable twice -- and keep the core in one piece. Every fifth wave brings "
       "a Siege Mech. Hold to wave fifteen and the sector is secured; lose the core "
       "and the next try starts again. Everyone is on the same side.", 16,
       ["#4ab8e8", "#e8a01a", "#3a3f46"],
       ["Co-op", "4 turret types", "Upgrades", "Siege Mechs", "Scrap economy",
        "4 shuffled sectors"],
       [_a("meadow", "Meadow Crossing",
           "One long country road, two bridges and the castle keep the core stands "
           "in."),
        _a("canyon", "Redstone Canyon",
           "Two paths down the canyon that meet at the mine where the core is."),
        _a("frostfall", "Frostfall Outpost",
           "A road across a frozen lake to the outpost on the far shore."),
        _a("grid", "Neon Grid",
           "Three glowing lanes across a digital plain to the server spire.")],
       [["Scrap", "Robots drop scrap when they die. Everyone shares it."],
        ["Build", "Hold E on a turret pad to buy a turret (or upgrade it)."],
        ["Defend", "Leaked robots damage the core. Shoot what the turrets miss."],
        ["Waves", "Every fifth wave brings a Siege Mech; wave 15 secures the sector."]],
       {"defenders": {"name": "Defenders", "colour": "#4ab8e8"}},
       {"round": 600, "setup": 20, "per_area": 2, "teams": ["defenders"], "style": "coop",
        "kpm": 4.0, "dpm": 0.2, "npc": True},
       [["Objective player, Team player", "Keep the pads built and upgraded."],
        ["Fragger, Sniper main", "Hold the chokepoints and shoot the leaks."],
        ["Wholesome, Support", "Run back to repair the core when it is hit."],
        ["Newbie", "Follow a builder about and shoot whatever it shoots."]],
       [["robots", "Robots"], ["built", "Built"]],
       "Hold the sector",
       "Every sector has its own road, its own turret pads and its own core."),
    # ================================================================ 10
    _w(12, "dodgeball", "Dodgeball Showdown", "Dodgeball",
       "If you can dodge a block, you can dodge a ball.",
       "The balls sit on the centre line at the whistle: run for them. Hit an "
       "opponent and they are out to the bench; catch a ball thrown at you and the "
       "thrower is out and one of your team comes back on. Step over the centre "
       "line and you are out. The last team with anybody on court wins. Big Balls, "
       "Fast Balls and Low Gravity rounds turn up now and then. Two rounds in each "
       "place.", 16,
       ["#c4281c", "#0d69ac", "#f2f3f3"],
       ["Throw and catch", "Comeback catches", "Line fouls", "Twist rounds",
        "4 shuffled courts"],
       [_a("gym", "Northfield High Gym",
           "Polished boards, bleachers, the scoreboard and the hoops."),
        _a("beach", "Sunny Shores Beach",
           "A sand court between the palms, the lifeguard tower and the tiki bar."),
        _a("orbital", "Orbital Station Zero",
           "A court in orbit: windows full of planet and gravity that cannot make "
           "up its mind."),
        _a("castle", "Castle Courtyard",
           "A tournament yard under the banners, stands on both sides and a moat "
           "outside.")],
       [["Grab", "Walk over a loose ball to pick it up (one at a time)."],
        ["Throw", "Fire to throw. A hit puts that player out."],
        ["Catch", "Press E (or right mouse) just as a ball reaches you: the thrower is "
                  "out and a teammate comes back."],
        ["Line", "Cross the centre line and you are out."]],
       {"red": {"name": "Red", "colour": "#c4281c"}, "blue": {"name": "Blue", "colour": "#0d69ac"}},
       {"round": 180, "setup": 8, "per_area": 2, "teams": ["red", "blue"], "style": "teams",
        "kpm": 1.0, "dpm": 0.9},
       [["Fragger, Tryhard", "Throw hard at the nearest open target."],
        ["Chill, Shy", "Hang back and dodge."],
        ["Veteran", "Catch when a ball comes straight at them."],
        ["Chaotic, Kid", "Sprint for every ball on the line."]],
       [["hits", "Hits"], ["catches", "Catches"]],
       "Last team on court",
       "Every court is mirrored down the middle line, cover and all."),
    # ================================================================ 11
    _w(13, "bomb_bash", "Bomb Bash", "Hot Potato",
       "Tag, you are it. You have nine seconds.",
       "A countdown, then a quarter of the players are handed a ticking bomb. Tag "
       "somebody to pass it on -- carriers run faster -- and whoever is holding it "
       "when the fuse runs out is out. New bombs go to the survivors until one is "
       "left. Sneakers, bubbles and short fuses turn up along the way. Three rounds "
       "in each place.", 20,
       ["#2a2d31", "#ff6a2a", "#ffd23a"],
       ["Hot potato", "Elimination", "Carriers run faster", "Power-ups",
        "4 shuffled places"],
       [_a("playground", "Jungle Gym Playground",
           "A giant playground: slides, climbing frames, the sandpit, tube tunnels "
           "and a treehouse."),
        _a("rooftops", "Rooftop Runway",
           "City rooftops with gaps to jump, bridges, billboards and a long way "
           "down."),
        _a("arcade", "Arcade Mania",
           "A giant arcade: cabinet aisles, the ball pit, the prize counter and a "
           "lot of neon."),
        _a("pirate", "Pirate Cove Deck",
           "Two pirate ships at a dock: masts, nets, cannons and cabins.")],
       [["Bombs", "A quarter of the players start each fuse holding a bomb."],
        ["Tag", "Hit somebody at arm's length to pass it. Not straight back!"],
        ["Boom", "Holding it when it goes off puts you out."],
        ["Last spark", "Last one left wins the round."]],
       {"ffa": {"name": "Players", "colour": "#ffd23a"}},
       {"round": 150, "setup": 8, "per_area": 3, "teams": ["ffa"], "style": "ffa",
        "kpm": 0.6, "dpm": 0.4},
       [["Fragger, Tryhard", "Chase the nearest runner the moment they have the bomb."],
        ["Shy, Chill", "Keep well away and climb."],
        ["Chaotic, Kid", "Hand it to whoever is closest, every time."],
        ["Explorer", "Use the high routes and the tunnels."]],
       [["passes", "Passes"], ["place", "Place"]],
       "Last one left",
       "Every place is built for running: loops, climbs and places to hide that are "
       "never quite safe."),
    # ================================================================ 12
    _w(14, "plunder_cove", "Plunder Cove", "Treasure Race",
       "X marks the spot. Dig it up. Carry it home. Steal theirs.",
       "Dig sites appear about the island: dig one up, carry the chest back to your "
       "ship's hold (slowly), and score it -- wooden chests are worth one, silver "
       "two, gold three. Raid the other ship to steal from its hold, man the deck "
       "cannons against the beach, and knock the carrier down to make them drop it. "
       "First crew to fifteen, or the richer one at the horn. Two rounds in each "
       "place.", 20,
       ["#c4281c", "#0d69ac", "#e8c060"],
       ["Dig, carry, score", "Steal from the hold", "Deck cannons",
        "Golden chests", "4 shuffled islands"],
       [_a("skull", "Skull Rock Cove",
           "A giant skull of rock over the beach, caves and a palm jungle."),
        _a("lagoon", "Palm Lagoon",
           "A shallow lagoon of sandbars and huts on stilts round a sunken ruin."),
        _a("reef", "Shipwreck Reef",
           "Wrecks on the reef, rocky islets and water to wade through."),
        _a("smoking", "Smoking Isle",
           "Black sand, lava rock and a temple at the top of a smoking cone.")],
       [["Dig", "Hold E on an X to dig up a chest."],
        ["Carry", "Carry it to your ship's hold. You are slower, and it drops if you "
                  "go down."],
        ["Steal", "Hold E in the other ship's hold to take a chest."],
        ["Cannons", "Hold E at a deck cannon to fire it at the beach."]],
       {"corsairs": {"name": "Corsairs", "colour": "#c4281c"},
        "tidebreakers": {"name": "Tidebreakers", "colour": "#0d69ac"}},
       {"round": 360, "setup": 15, "per_area": 2, "teams": ["corsairs", "tidebreakers"],
        "style": "teams", "kpm": 1.0, "dpm": 0.9},
       [["Objective player", "Dig and carry."],
        ["Team player", "Escort the carrier home."],
        ["Fragger, Tryhard", "Raid the other ship; knock carriers down."],
        ["Sniper main", "Man the cannons."]],
       [["chests", "Chests"], ["stolen", "Stolen"]],
       "First to 15 gold",
       "Every island has two ships at opposite ends, dig sites all over and cannons "
       "on both decks."),
    # ================================================================ 13
    _w(15, "storm_circle", "Storm Circle", "Battle Royale",
       "Drop in. Loot up. Stay in the circle.",
       "Everybody drops in from the sky and floats down. Loot supply crates for "
       "armour, medkits and a power weapon, while the storm closes in five phases "
       "on a random point -- outside it you burn, and harder every phase. The last "
       "one standing wins. Two rounds in each place.", 24,
       ["#7a4ae0", "#3a8a4a", "#e8e8e8"],
       ["24 players", "Sky drop", "Supply crates", "Power weapons",
        "Five storm phases", "4 shuffled islands"],
       [_a("pinewood", "Pinewood Isle",
           "A forest island: cabins, a lake, a ranger tower and a river."),
        _a("mesa", "Copper Mesa",
           "A desert canyon town: mesas, the mine, a water tower and the old "
           "railway."),
        _a("city", "Shattered City",
           "Ruined city blocks round a collapsed overpass and an overgrown park."),
        _a("glacier", "Glacier Bay",
           "An icy coast: the research station, ice caves and a crashed plane.")],
       [["Drop", "You float down from the sky at the start. Pick a spot."],
        ["Loot", "Hold E on a supply crate: armour, medkits or a power weapon."],
        ["Storm", "The circle shrinks five times. Outside it you burn."],
        ["Win", "Last one standing."]],
       {"ffa": {"name": "Everyone", "colour": "#e0a040"}},
       {"round": 330, "setup": 10, "per_area": 2, "teams": ["ffa"], "style": "ffa",
        "kpm": 0.7, "dpm": 0.25},
       [["Fragger, Tryhard", "Drop somewhere busy and fight."],
        ["Shy, Chill", "Drop somewhere quiet, loot, and move early."],
        ["Sniper main", "Hold high ground at the edge of the circle."],
        ["Explorer, Chaotic", "Loot everything; arrive late in the circle."]],
       [["elims", "Elims"], ["place", "Place"]],
       "Last one standing",
       "Every island has crates in every building and a storm that never closes on "
       "the same place twice."),
    # ================================================================ 14
    _w(16, "flee_beast", "Flee the Beast", "Asymmetric Escape",
       "Hack the computers. Open the exit. Do not let it catch you.",
       "One player is the Beast. Everyone else hacks computers -- a missed beat sets "
       "off an alarm the Beast can hear -- until the exits power up, then holds an "
       "exit open and gets out. The Beast knocks survivors down and drags them to a "
       "freezer pod, which holds you for a minute unless a friend frees you. Hide in "
       "a locker if you have to. Survivors win if anybody escapes. A new Beast every "
       "round; three rounds in each place.", 16,
       ["#c4281c", "#3a6a8a", "#1a1d24"],
       ["1 vs many", "Hack computers", "Freezer pods", "Lockers",
        "A new Beast every round", "4 shuffled places"],
       [_a("facility", "Hollowbrook Facility",
           "Labs, the server room, the cafeteria, corridors and a loading bay."),
        _a("academy", "Ashgrove Academy",
           "A school at night: classrooms, the gym, the library and the courtyard."),
        _a("abyssal", "Abyssal Station",
           "An undersea base of domes and tunnels round the moon pool and the "
           "reactor."),
        _a("sewers", "Undercroft Sewers",
           "Brick tunnels, pump rooms and walkways over the channels under the "
           "city.")],
       [["Hack", "Survivors: hold E on a computer. Miss a beat and the Beast hears it."],
        ["Escape", "When enough are hacked the exits power up: hold one open and run."],
        ["Pods", "The Beast hits you down and drags you to a pod. A friend can free "
                 "you; a minute in one and you are out."],
        ["Hide", "Press E at a locker to hide. The Beast can check it."]],
       {"survivors": {"name": "Survivors", "colour": "#5ab4e8"},
        "beast": {"name": "The Beast", "colour": "#c4281c"}},
       {"round": 360, "setup": 12, "per_area": 3, "teams": ["survivors", "beast"],
        "style": "teams", "kpm": 0.4, "dpm": 0.35},
       [["Objective player", "Hack computers."],
        ["Team player, Wholesome", "Free frozen friends from their pods."],
        ["Shy, Loner", "Hide in lockers a lot."],
        ["Tryhard, Veteran", "As the Beast, patrol computers and check lockers."],
        ["Chaotic", "Run circles round the Beast."]],
       [["hacks", "Hacks"], ["escaped", "Escaped"]],
       "Escape or catch them all",
       "Every place has computers spread out, two exits, freezer pods and lockers."),
    # ================================================================ 15
    _w(17, "tycoon_wars", "Tycoon Wars", "Competitive Tycoon",
       "Build the biggest business. Raid the others. Eight minutes.",
       "Four companies, one season each. Droppers make product, conveyors carry it "
       "to your bank, and the buttons on your plot buy the next machine -- more "
       "droppers, upgraders, laser gates that hurt intruders, auto turrets, the Mega "
       "Drill. Mine the ore field in the middle by hand for a bonus. Raid an enemy "
       "vault to take a tenth of their bank. Highest net worth when the season ends "
       "wins, and the economy moves on to another biome.", 24,
       ["#e0a020", "#c8283c", "#28a050"],
       ["4 companies", "Droppers and conveyors", "Laser gates and turrets",
        "Vault raids", "Ore field", "4 biomes"],
       [_a("goldvein", "Goldvein Mines",
           "Four mine heads round a gold-veined canyon floor."),
        _a("sugarloaf", "Sugarloaf Candy Co.",
           "Four candy works round a field of rock candy."),
        _a("timberline", "Timberline Lumber",
           "Four sawmills round a forest clearing and its river."),
        _a("oasis", "Oasis Oil Fields",
           "Four oil companies round a desert oasis.")],
       [["Earn", "Droppers make product; the conveyor banks it. Walk over your bank "
                 "pad to collect."],
        ["Build", "Stand on a button to buy the next machine."],
        ["Mine", "Hold E at an ore node in the middle and carry it home."],
        ["Raid", "Hold E at an enemy vault to take a tenth of their bank."]],
       {"ruby": {"name": "Ruby", "colour": "#c8283c"},
        "sapphire": {"name": "Sapphire", "colour": "#2858c8"},
        "emerald": {"name": "Emerald", "colour": "#28a050"},
        "topaz": {"name": "Topaz", "colour": "#e0a020"}},
       {"round": 480, "setup": 12, "per_area": 1, "teams": ["ruby", "sapphire", "emerald", "topaz"],
        "style": "teams", "kpm": 0.5, "dpm": 0.5},
       [["Objective player, Builder", "Buy in order and keep the bank collected."],
        ["Fragger, Tryhard", "Raid the richest vault."],
        ["Chill, Shy", "Stay home and guard."],
        ["Explorer", "Mine the ore field."]],
       [["worth", "Worth"], ["built", "Built"]],
       "Highest net worth",
       "Every biome has four plots round a shared ore field; the plots are mirrored "
       "four ways."),
]
