"""The arena worlds' badges: six for each of the fifteen, on plates of their own.

``app/models/badges.py`` appends these to its list.  Every world strikes its
badges on its own plate -- Cataclysm on a hazard triangle, Rail Rumble on a
level-crossing sign, Plunder Cove on a ship's wheel -- so a badge says which
world it came from before anyone reads its name.  The emblems are painted
in ``static/js/engine/arena_art.js``.

The stats are booked by the worlds themselves (``ArenaWorld.badge`` -> the
host's heartbeat), each with its world's two-letter prefix.  A ``*_place_<id>``
stat is a mark for one place; the "tour" badges count those marks (see
``DERIVED``).
"""
from __future__ import annotations

import math
from typing import Any, Callable, Dict, List

from .modeling import part, place

HALF_PI = math.pi / 2

# ---------------------------------------------------------------- families
# face: the enamel; ribbon: the Platinum tails; wing: the Diamond wings
FAMILIES: Dict[str, Dict[str, str]] = {
    "hazard": {"face": "#2a1a06", "ribbon": "#e0a040", "wing": "#ffe6b0", "wing_mesh": "wing"},
    "frame": {"face": "#1c3446", "ribbon": "#3fa8d8", "wing": "#f2ead8", "wing_mesh": "wing"},
    "crossbuck": {"face": "#2a0e0e", "ribbon": "#b8383b", "wing": "#f4efe6", "wing_mesh": "wing"},
    "chevron": {"face": "#14263a", "ribbon": "#2f86cf", "wing": "#cfd8e2", "wing_mesh": "wing"},
    "keyhole": {"face": "#160c22", "ribbon": "#7a2a8a", "wing": "#2a1838", "wing_mesh": "bat"},
    "vault": {"face": "#14221a", "ribbon": "#2f8a4a", "wing": "#e8f0e0", "wing_mesh": "wing"},
    "splat": {"face": "#2a0c22", "ribbon": "#ff4fa8", "wing": "#bff7ef", "wing_mesh": "wing"},
    "burst": {"face": "#2c1206", "ribbon": "#ff7a1a", "wing": "#fff0c8", "wing_mesh": "wing"},
    "rampart": {"face": "#0e2230", "ribbon": "#1fb6c8", "wing": "#d8f4ff", "wing_mesh": "wing"},
    "ball": {"face": "#3a0c0c", "ribbon": "#d83a2a", "wing": "#fff4e8", "wing_mesh": "wing"},
    "bomb": {"face": "#14141c", "ribbon": "#ff5a2a", "wing": "#ffe0b0", "wing_mesh": "wing"},
    "helm": {"face": "#0c2a30", "ribbon": "#c8902a", "wing": "#f4e6c8", "wing_mesh": "wing"},
    "cloud": {"face": "#1a1240", "ribbon": "#8a5aff", "wing": "#e6dcff", "wing_mesh": "wing"},
    "pod": {"face": "#06222a", "ribbon": "#3ad8ff", "wing": "#1a1a22", "wing_mesh": "bat"},
    "coin": {"face": "#2a2206", "ribbon": "#2fa84f", "wing": "#fff2b0", "wing_mesh": "wing"},
}

GAMES: Dict[str, str] = {
    "cataclysm": "Cataclysm", "prop_panic": "Prop Panic", "rail_rumble": "Rail Rumble",
    "convoy": "Convoy", "midnight_mystery": "Midnight Mystery", "grand_heist": "Grand Heist",
    "splat_turf": "Splat Turf", "bonk_brawl": "Bonk Brawl", "bastion": "Bastion",
    "dodgeball": "Dodgeball Showdown", "bomb_bash": "Bomb Bash", "plunder_cove": "Plunder Cove",
    "storm_circle": "Storm Circle", "flee_beast": "Flee the Beast", "tycoon_wars": "Tycoon Wars",
}

# the "tour" stats, counted from per-place marks
DERIVED: Dict[str, str] = {
    "cx_kinds": "cx_kind_",
    "cv_places": "cv_place_",
    "st_places": "st_place_",
    "db_places": "db_place_",
    "bm_places": "bm_place_",
    "sc_places": "sc_place_",
    "tw_places": "tw_place_",
}

# a run of six thresholds for a stat that goes up a few at a time, another for
# one that goes up by the dozen, and a short one for rare feats
COMMON = [1, 10, 40, 120, 300, 700]
STEADY = [1, 15, 60, 180, 450, 1000]
MANY = [5, 40, 150, 400, 1000, 2500]
WINS = [1, 5, 15, 40, 100, 250]
RARE = [1, 3, 10, 25, 60]
TOUR = [1, 2, 3, 4]


def _rows() -> List[tuple]:
    """(id, name, game, stat, thresholds, ranks, description, emblem, unit, mode)"""
    return [
        # ------------------------------------------------------- Cataclysm
        ("cx_survivor", "Storm Survivor", "cataclysm", "cx_survived", COMMON,
         ["Lucky", "Weathered", "Storm Proof", "Unshaken", "Force of Nature", "Act of God"],
         "Counts every disaster you are still standing at the end of in Cataclysm.",
         "em_cx_umbrella", "disasters survived", "add"),
        ("cx_unbroken", "Unbroken", "cataclysm", "cx_best_streak", [2, 4, 6, 9, 12, 16],
         ["Steady", "Hardy", "Resilient", "Indomitable", "Immovable", "Eternal"],
         "Your longest run of disasters survived in a row without falling once.",
         "em_cx_chain", "in a row", "max"),
        ("cx_tourist", "Disaster Tourist", "cataclysm", "cx_kinds", [2, 4, 6, 8, 10],
         ["Sightseer", "Storm Chaser", "Thrill Seeker", "Doom Tourist", "Seen It All"],
         "Survived each of Cataclysm's ten kinds of disaster at least once.",
         "em_cx_globe", "kinds of disaster", "add"),
        ("cx_double", "Double Trouble", "cataclysm", "cx_double", [1, 5, 15, 40, 100],
         ["Twice Lucky", "Double Dodger", "Two-Faced Storm", "Twin Terror", "Perfect Storm"],
         "Survived a round when the sky threw two disasters at once.",
         "em_cx_twin", "double rounds survived", "add"),
        ("cx_thread", "By a Thread", "cataclysm", "cx_close", [1, 10, 30, 80, 200],
         ["Close Call", "Skin of the Teeth", "Hanging On", "Clinging", "Never Say Die"],
         "Came through a disaster on almost no health.", "em_cx_thread", "close calls", "add"),
        ("cx_lone", "Last One Standing", "cataclysm", "cx_last", [1, 3, 10, 25, 60],
         ["Sole Survivor", "Lone Wolf", "Last Light", "Ark Keeper", "The Remnant"],
         "Was the only survivor left when the disaster blew over.",
         "em_cx_lone", "lone survivals", "add"),
        # ------------------------------------------------------ Prop Panic
        ("pp_disguise", "Master of Disguise", "prop_panic", "pp_survived", COMMON,
         ["Wallflower", "Chameleon", "Stagehand", "Illusionist", "Phantom Prop", "Invisible"],
         "Survived a hunt as a prop in Prop Panic.", "em_pp_teapot", "hunts survived", "add"),
        ("pp_hunter", "Prop Hunter", "prop_panic", "pp_found", STEADY,
         ["Seeker", "Tracker", "Bloodhound", "Inspector", "Eagle Eye", "Nothing Escapes"],
         "Found hiding props as a Hunter.", "em_pp_lens", "props found", "add"),
        ("pp_showboat", "Showboat", "prop_panic", "pp_taunts", MANY,
         ["Heckler", "Show-off", "Entertainer", "Headliner", "Superstar", "Living Legend"],
         "Taunted while hiding -- and got away with it.", "em_pp_horn", "taunts", "add"),
        ("pp_double_take", "Double Take", "prop_panic", "pp_decoys", [1, 10, 40, 100, 250],
         ["Prankster", "Trickster", "Misdirector", "Mirror Maker", "Grand Deceiver"],
         "A Hunter wasted a shot on your decoy.", "em_pp_decoy", "decoys shot", "add"),
        ("pp_spotlight", "Last Prop Standing", "prop_panic", "pp_last", [1, 5, 15, 40, 100],
         ["Holdout", "Spotlight", "Encore", "Curtain Call", "Standing Ovation"],
         "Was the last prop hidden when the clock ran out.", "em_pp_spotlight",
         "last-prop wins", "add"),
        ("pp_sweep", "Clean Sweep", "prop_panic", "pp_sweeps", [1, 5, 15, 40, 100],
         ["Tidy", "Spotless", "Housekeeper", "Exterminator", "Marie Kondo"],
         "Hunted down every single prop before time ran out.", "em_pp_broom",
         "clean sweeps", "add"),
        # ----------------------------------------------------- Rail Rumble
        ("rr_driver", "Engine Driver", "rail_rumble", "rr_push_min", COMMON,
         ["Brakeman", "Fireman", "Driver", "Engineer", "Iron Horse", "Locomotive"],
         "Minutes spent pushing your team's cart along in Rail Rumble.",
         "em_rr_loco", "minutes pushing", "add"),
        ("rr_pointsman", "Pointsman", "rail_rumble", "rr_switches", COMMON,
         ["Lever Puller", "Signalman", "Pointsman", "Switchmaster", "Junction King",
          "Wrong Way Wizard"],
         "Threw a junction lever and sent a cart round its detour.",
         "em_rr_lever", "junctions thrown", "add"),
        ("rr_stoker", "Stoker", "rail_rumble", "rr_boosts", COMMON,
         ["Shoveller", "Stoker", "Firebox", "Full Steam", "Boiler Buster", "Steam Legend"],
         "Stoked your cart at a coal hopper for a burst of speed.",
         "em_rr_coal", "boosts", "add"),
        ("rr_spike", "Golden Spike", "rail_rumble", "rr_wins", WINS,
         ["Contender", "Front Runner", "Express", "Limited", "Flying Scotsman", "Golden Spike"],
         "Won races in Rail Rumble with your team.", "em_rr_spike", "races won", "add"),
        ("rr_photo", "Photo Finish", "rail_rumble", "rr_photo", RARE,
         ["Nose Ahead", "By a Whisker", "Photo Finish", "Dead Heat Breaker", "Hair's Breadth"],
         "Won a race by the narrowest of margins.", "em_rr_flag", "photo finishes", "add"),
        ("rr_wrecker", "Track Wrecker", "rail_rumble", "rr_pusher_kills", MANY,
         ["Derailer", "Saboteur", "Wrecker", "Train Robber", "Rail Bandit", "Last Stop"],
         "Knocked out enemies who were pushing their cart.", "em_rr_wrench",
         "pushers stopped", "add"),
        # ---------------------------------------------------------- Convoy
        ("cv_escort", "Convoy Escort", "convoy", "cv_legs", COMMON,
         ["Outrider", "Escort", "Shotgun Rider", "Road Captain", "Iron Column", "Unstoppable"],
         "Got the convoy through a leg of its journey as the Escort.",
         "em_cv_truck", "legs escorted", "add"),
        ("cv_breacher", "Breacher", "convoy", "cv_breaches", [1, 10, 40, 100, 250, 600],
         ["Door Kicker", "Sapper", "Breacher", "Battering Ram", "Wall Breaker", "Siege Engine"],
         "Helped tear down a roadblock in the convoy's way.", "em_cv_ram",
         "roadblocks breached", "add"),
        ("cv_ambusher", "Ambusher", "convoy", "cv_holds", [1, 10, 30, 80, 200, 500],
         ["Lookout", "Bushwhacker", "Ambusher", "Highwayman", "Road Warden", "The Blockade"],
         "Held a leg with the Ambush until the convoy's clock ran out.",
         "em_cv_barricade", "legs held", "add"),
        ("cv_long_haul", "Long Haul", "convoy", "cv_journeys", WINS,
         ["Day Trip", "Cross-Country", "Long Haul", "Trailblazer", "Odyssey", "Grand Voyage"],
         "Escorted the convoy the whole way: all three legs of a journey.",
         "em_cv_map", "journeys completed", "add"),
        ("cv_road_trip", "Road Tripper", "convoy", "cv_places", TOUR,
         ["Passenger", "Navigator", "Road Tripper", "Grand Tourer"],
         "Got the convoy through a leg in each of Convoy's four places.",
         "em_cv_compass", "places", "add"),
        ("cv_frontline", "Convoy Frontline", "convoy", "cv_kills",
         [25, 150, 500, 1500, 4000, 10000],
         ["Private", "Corporal", "Sergeant", "Lieutenant", "Colonel", "General"],
         "Counts every opponent you knock out in Convoy.", "em_cv_helmet", "knockouts", "add"),
        # ------------------------------------------------ Midnight Mystery
        ("mm_detective", "Detective", "midnight_mystery", "mm_solved", WINS,
         ["Gumshoe", "Sleuth", "Inspector", "Detective", "Chief Inspector", "Great Detective"],
         "Shot the murderer and saved the night in Midnight Mystery.",
         "em_mm_star", "cases solved", "add"),
        ("mm_phantom", "Phantom of the Night", "midnight_mystery", "mm_murder_wins", WINS,
         ["Shadow", "Lurker", "Stalker", "Nightshade", "Phantom", "The Unseen"],
         "Won a round as the murderer.", "em_mm_knife", "nights won", "add"),
        ("mm_wallflower", "Wallflower", "midnight_mystery", "mm_survived", COMMON,
         ["Guest", "Bystander", "Wallflower", "Survivor", "Unflappable", "Iron Nerve"],
         "Lived to see the morning as an innocent guest.", "em_mm_candle",
         "nights survived", "add"),
        ("mm_coins", "Coin Collector", "midnight_mystery", "mm_coins",
         [10, 100, 400, 1200, 3000, 8000],
         ["Penny", "Saver", "Collector", "Hoarder", "Treasurer", "Dragon's Hoard"],
         "Picked up the coins scattered round each place.", "em_mm_coin", "coins", "add"),
        ("mm_hero", "Unlikely Hero", "midnight_mystery", "mm_hero", RARE,
         ["Have-a-go", "Brave Soul", "Unlikely Hero", "Avenger", "Legend of the Night"],
         "Picked up the fallen sheriff's revolver and stopped the murderer with it.",
         "em_mm_revolver", "heroic finishes", "add"),
        ("mm_masquerade", "Masquerade", "midnight_mystery", "mm_spree", RARE,
         ["Unmasked", "Masquerade", "Grand Guignol", "Curtain Fall", "Lights Out"],
         "As the murderer, caught every guest before the night was out.",
         "em_mm_mask", "clean sweeps", "add"),
        # ----------------------------------------------------- Grand Heist
        ("gh_big_score", "Big Score", "grand_heist", "gh_loot",
         [5, 50, 200, 600, 1500, 4000],
         ["Pickpocket", "Burglar", "Robber", "Heister", "Mastermind", "Criminal Empire"],
         "Thousands of dollars of loot carried back to the getaway van in Grand Heist.",
         "em_gh_bag", "thousand banked", "add"),
        ("gh_safecracker", "Safecracker", "grand_heist", "gh_vaults",
         [1, 10, 40, 100, 250, 600],
         ["Tinkerer", "Lockpick", "Safecracker", "Vault Whisperer", "Ghost Fingers",
          "Open Sesame"], "Cracked a vault open.", "em_gh_dial", "vaults cracked", "add"),
        ("gh_long_arm", "Long Arm of the Law", "grand_heist", "gh_arrests", STEADY,
         ["Rookie", "Patrol", "Sergeant", "Detective", "Captain", "Commissioner"],
         "Cuffed a robber as a cop.", "em_gh_cuffs", "arrests", "add"),
        ("gh_jailbreak", "Jailbreak", "grand_heist", "gh_springs",
         [1, 10, 30, 80, 200, 500],
         ["Accomplice", "Locksmith", "Breakout", "Liberator", "Great Escape", "Alcatraz"],
         "Sprang your crew out of the cells.", "em_gh_bars", "jailbreaks", "add"),
        ("gh_getaway", "Clean Getaway", "grand_heist", "gh_clean", [1, 5, 15, 40, 100],
         ["Slippery", "Smooth", "Clean Getaway", "Untraceable", "Never Caught"],
         "Won a heist as a robber without being cuffed once.", "em_gh_car",
         "clean getaways", "add"),
        ("gh_precinct", "Precinct Hero", "grand_heist", "gh_cop_wins", WINS,
         ["Cadet", "Officer", "Lawman", "Marshal", "Chief", "Top Cop"],
         "Stopped a heist as a cop.", "em_gh_shield", "heists stopped", "add"),
        # ------------------------------------------------------ Splat Turf
        ("st_painter", "Turf Painter", "splat_turf", "st_cells",
         [5, 50, 200, 600, 1500, 4000],
         ["Doodler", "Tagger", "Muralist", "Street Artist", "Old Master", "Living Canvas"],
         "Hundreds of floor squares inked in your team's colour in Splat Turf.",
         "em_st_roller", "hundred squares", "add"),
        ("st_splatter", "Splatter", "splat_turf", "st_splats", MANY,
         ["Spritzer", "Splasher", "Splatter", "Drencher", "Ink Storm", "Tidal Wave"],
         "Splatted an opponent back to their spawn.", "em_st_splat", "splats", "add"),
        ("st_champion", "Turf Champion", "splat_turf", "st_wins", WINS,
         ["Squad", "Crew", "Gang", "Posse", "Crown", "Turf Royalty"],
         "Won turf matches with your team.", "em_st_bucket", "matches won", "add"),
        ("st_landslide", "Landslide", "splat_turf", "st_landslides", RARE,
         ["Blowout", "Landslide", "Wipeout", "Whitewash", "Total Coverage"],
         "Won a match with seven tenths of the floor in your colour.",
         "em_st_wave", "landslides", "add"),
        ("st_ink_rush", "Ink Rush", "splat_turf", "st_rushes", COMMON,
         ["Spark", "Rush", "Surge", "Flood", "Deluge", "Ink Typhoon"],
         "Filled your special meter and let rip.", "em_st_drop", "specials", "add"),
        ("st_gallery", "Gallery Tour", "splat_turf", "st_places", TOUR,
         ["Visitor", "Patron", "Curator", "Gallery Owner"],
         "Won a match in each of Splat Turf's four places.", "em_st_palette", "places", "add"),
        # ------------------------------------------------------ Bonk Brawl
        ("bb_bonker", "Bonker", "bonk_brawl", "bb_kos", MANY,
         ["Tapper", "Bopper", "Bonker", "Smasher", "Launcher", "Orbit Maker"],
         "Knocked rivals clean off the arena in Bonk Brawl.", "em_bb_hammer",
         "knock-offs", "add"),
        ("bb_home_run", "Home Run", "bonk_brawl", "bb_homeruns",
         [1, 10, 40, 100, 250, 600],
         ["Base Hit", "Double", "Triple", "Home Run", "Grand Slam", "Out of the Park"],
         "Sent somebody flying at a hundred and fifty per cent or more.",
         "em_bb_bat", "home runs", "add"),
        ("bb_belt", "Last Brawler", "bonk_brawl", "bb_wins", WINS,
         ["Scrapper", "Brawler", "Bruiser", "Contender", "Champion", "Undisputed"],
         "Was the last brawler standing.", "em_bb_belt", "brawls won", "add"),
        ("bb_untouched", "Untouched", "bonk_brawl", "bb_flawless", RARE,
         ["Clean", "Spotless", "Untouched", "Perfect", "Flawless Victory"],
         "Won a brawl without losing a single stock.", "em_bb_halo", "flawless wins", "add"),
        ("bb_power", "Power Hungry", "bonk_brawl", "bb_powerups", STEADY,
         ["Snacker", "Grabber", "Power Hungry", "Supercharged", "Overloaded", "Maxed Out"],
         "Grabbed power-ups off the arena floor.", "em_bb_power", "power-ups", "add"),
        ("bb_comeback", "Comeback Kid", "bonk_brawl", "bb_comeback", RARE,
         ["Scrappy", "Comeback Kid", "Never Out", "Phoenix", "Second Wind"],
         "Won a brawl on your very last stock.", "em_bb_heart", "comebacks", "add"),
        # --------------------------------------------------------- Bastion
        ("bs_holdout", "Bastion Holdout", "bastion", "bs_best_wave", [5, 10, 15, 20, 25, 30],
         ["Sentry", "Garrison", "Bulwark", "Citadel", "Bastion", "Last Bastion"],
         "The highest wave your team has held the core through in Bastion.",
         "em_bs_tower", "best wave", "max"),
        ("bs_builder", "Master Builder", "bastion", "bs_built", STEADY,
         ["Apprentice", "Builder", "Engineer", "Architect", "Fortifier", "Grand Architect"],
         "Built turrets on the lane.", "em_bs_hammer", "turrets built", "add"),
        ("bs_overclock", "Overclocked", "bastion", "bs_upgrades", STEADY,
         ["Tinker", "Mechanic", "Technician", "Overclocker", "Supercharger", "Singularity"],
         "Upgraded turrets to their next mark.", "em_bs_gear", "upgrades", "add"),
        ("bs_breaker", "Bot Breaker", "bastion", "bs_kills",
         [100, 500, 2000, 6000, 15000, 40000],
         ["Scrapper", "Recycler", "Bot Breaker", "Junkmaker", "Shredder", "System Crash"],
         "Scrapped invading drones with your own weapons.", "em_bs_drone",
         "drones scrapped", "add"),
        ("bs_giant", "Giant Killer", "bastion", "bs_mechs", [1, 5, 15, 40, 100, 200],
         ["Toppler", "Giant Killer", "Mech Breaker", "Colossus Slayer", "Titan Fall",
          "Goliath's End"], "Helped bring down a boss mech.", "em_bs_mech", "mechs", "add"),
        ("bs_scratch", "Not a Scratch", "bastion", "bs_perfect", [1, 5, 15, 40, 100],
         ["Tidy", "Clean", "Not a Scratch", "Pristine", "Untouchable Core"],
         "Held a wave from ten onwards without the core taking a hit.",
         "em_bs_core", "perfect waves", "add"),
        # ------------------------------------------------------- Dodgeball
        ("db_ace", "Dodgeball Ace", "dodgeball", "db_outs", MANY,
         ["Thrower", "Hurler", "Pitcher", "Cannon Arm", "Ace", "Hall of Famer"],
         "Hit opponents with a dodgeball and sent them out.", "em_db_ball", "outs", "add"),
        ("db_safe_hands", "Safe Hands", "dodgeball", "db_catches", STEADY,
         ["Butterfingers No More", "Catcher", "Safe Hands", "Glove", "Vacuum", "Black Hole"],
         "Caught a ball thrown at you -- the thrower is out.", "em_db_glove",
         "catches", "add"),
        ("db_varsity", "Varsity", "dodgeball", "db_wins", WINS,
         ["Junior Varsity", "Varsity", "All-County", "All-State", "All-Star", "Champion"],
         "Won dodgeball matches with your team.", "em_db_pennant", "matches won", "add"),
        ("db_last_in", "Last One In", "dodgeball", "db_clutch", RARE,
         ["Clutch", "Last One In", "One-Man Team", "Unbreakable", "The Anchor"],
         "Won the match as the last player standing on your side.",
         "em_db_whistle", "clutch wins", "add"),
        ("db_back_in", "Back in the Game", "dodgeball", "db_rescues", COMMON,
         ["Helper", "Teammate", "Lifeline", "Rescuer", "Saviour", "Captain"],
         "A catch of yours brought a teammate back onto the court.",
         "em_db_arrows", "teammates back", "add"),
        ("db_away", "Away Games", "dodgeball", "db_places", TOUR,
         ["Home Team", "Traveller", "Road Team", "World Tour"],
         "Won a match in each of the four courts.", "em_db_bus", "courts", "add"),
        # ------------------------------------------------------- Bomb Bash
        ("bm_last_spark", "Last Spark", "bomb_bash", "bm_wins", WINS,
         ["Survivor", "Firewalker", "Untouchable", "Bomb Proof", "Blast Master", "Last Spark"],
         "Was the last one standing when the final fuse went.", "em_bm_bomb",
         "rounds won", "add"),
        ("bm_hot_hands", "Hot Hands", "bomb_bash", "bm_passes",
         [10, 100, 400, 1200, 3000, 8000],
         ["Juggler", "Hot Potato", "Hot Hands", "Quick Draw", "Lightning Hands", "Teleporter"],
         "Passed the bomb on to somebody else.", "em_bm_hands", "passes", "add"),
        ("bm_close_shave", "Close Shave", "bomb_bash", "bm_close",
         [1, 10, 40, 100, 250, 600],
         ["Phew", "Close Shave", "Split Second", "Last Tick", "Zero Hour", "Time Lord"],
         "Got rid of the bomb with under a second on its fuse.", "em_bm_watch",
         "close shaves", "add"),
        ("bm_nine_lives", "Nine Lives", "bomb_bash", "bm_lives", MANY,
         ["Lucky", "Charmed", "Nine Lives", "Unkillable", "Immortal", "Cat of Legend"],
         "Every fuse that went off on somebody other than you.", "em_bm_cat",
         "fuses survived", "add"),
        ("bm_speed", "Speed Demon", "bomb_bash", "bm_powerups", STEADY,
         ["Jogger", "Sprinter", "Speed Demon", "Rocket", "Sonic", "Light Speed"],
         "Grabbed power-ups mid-round.", "em_bm_boot", "power-ups", "add"),
        ("bm_party", "Party Hopper", "bomb_bash", "bm_places", TOUR,
         ["Guest", "Partygoer", "Party Animal", "Life of the Party"],
         "Won a round in each of Bomb Bash's four places.", "em_bm_confetti",
         "places", "add"),
        # ---------------------------------------------------- Plunder Cove
        ("pc_plunderer", "Plunderer", "plunder_cove", "pc_banked",
         [10, 100, 400, 1200, 3000, 8000],
         ["Deckhand", "Buccaneer", "Plunderer", "Privateer", "Corsair", "Dread Pirate"],
         "Doubloons' worth of treasure carried home to your ship in Plunder Cove.",
         "em_pc_chest", "doubloons", "add"),
        ("pc_digger", "Treasure Digger", "plunder_cove", "pc_digs", STEADY,
         ["Sandcastle", "Digger", "Excavator", "Treasure Hunter", "Map Reader", "X Marks"],
         "Dug up buried chests.", "em_pc_shovel", "chests dug", "add"),
        ("pc_swashbuckler", "Swashbuckler", "plunder_cove", "pc_steals", COMMON,
         ["Pilferer", "Thief", "Swashbuckler", "Boarding Party", "Sea Wolf", "Kraken"],
         "Took a chest from the enemy's hold.", "em_pc_cutlass", "chests stolen", "add"),
        ("pc_gunner", "Master Gunner", "plunder_cove", "pc_cannon_hits", STEADY,
         ["Powder Monkey", "Loader", "Gunner", "Broadside", "Master Gunner", "Admiral"],
         "Hit opponents with a ship's cannon.", "em_pc_cannon", "cannon hits", "add"),
        ("pc_king", "Pirate King", "plunder_cove", "pc_wins", WINS,
         ["Crew", "Mate", "Quartermaster", "Captain", "Commodore", "Pirate King"],
         "Won the plunder with your crew.", "em_pc_jolly", "rounds won", "add"),
        ("pc_idol", "Golden Idol", "plunder_cove", "pc_golden", RARE,
         ["Glitter", "Gilded", "Golden Idol", "Cursed Gold", "El Dorado"],
         "Carried the golden chest home.", "em_pc_idol", "golden chests", "add"),
        # ---------------------------------------------------- Storm Circle
        ("sc_eye", "Eye of the Storm", "storm_circle", "sc_wins", WINS,
         ["Survivor", "Finalist", "Victor", "Storm King", "Legend", "Eye of the Storm"],
         "Last one standing in Storm Circle.", "em_sc_eye", "wins", "add"),
        ("sc_top_five", "Top Five", "storm_circle", "sc_top5", COMMON,
         ["Contender", "Finalist", "Top Five", "Elite", "Mainstay", "Fixture"],
         "Made it to the final five.", "em_sc_podium", "top fives", "add"),
        ("sc_hunter", "Storm Hunter", "storm_circle", "sc_kills", MANY,
         ["Scrapper", "Fighter", "Hunter", "Predator", "Apex", "Storm Reaper"],
         "Knocked out opponents in Storm Circle.", "em_sc_scope", "knockouts", "add"),
        ("sc_supply", "Supply Run", "storm_circle", "sc_crates",
         [5, 50, 200, 600, 1500, 4000],
         ["Scavenger", "Looter", "Quartermaster", "Supply Chief", "Logistics", "Armoury"],
         "Cracked open loot crates.", "em_sc_crate", "crates opened", "add"),
        ("sc_stormwalker", "Stormwalker", "storm_circle", "sc_storm_escapes",
         [1, 10, 40, 100, 250, 600],
         ["Wet Feet", "Drenched", "Stormwalker", "Thunder Runner", "Lightning Rod",
          "Storm Born"], "Ran out of the storm alive.", "em_sc_bolt", "storm escapes", "add"),
        ("sc_island", "Island Hopper", "storm_circle", "sc_places", TOUR,
         ["Castaway", "Islander", "Island Hopper", "Archipelago"],
         "Won a round in each of Storm Circle's four places.", "em_sc_island",
         "places", "add"),
        # --------------------------------------------------- Flee the Beast
        ("fb_escape", "Escape Artist", "flee_beast", "fb_escapes", COMMON,
         ["Runner", "Escapee", "Escape Artist", "Houdini", "Ghost", "Uncatchable"],
         "Made it out of an exit door before the Beast caught you.",
         "em_fb_door", "escapes", "add"),
        ("fb_hacker", "Hacker", "flee_beast", "fb_hacks", STEADY,
         ["Script Kiddie", "Coder", "Hacker", "Netrunner", "Root Access", "Zero Day"],
         "Finished hacking a computer.", "em_fb_terminal", "computers hacked", "add"),
        ("fb_rescuer", "Rescuer", "flee_beast", "fb_rescues", COMMON,
         ["Helper", "Rescuer", "Lifeguard", "Saviour", "Guardian", "Unbreakable Bond"],
         "Freed a captured survivor from a freezer pod.", "em_fb_pod", "rescues", "add"),
        ("fb_beast", "The Beast", "flee_beast", "fb_beast_wins", WINS,
         ["Prowler", "Stalker", "Hunter", "Monster", "Nightmare", "The Beast"],
         "Won a round as the Beast.", "em_fb_hammer", "rounds won", "add"),
        ("fb_apex", "Apex Predator", "flee_beast", "fb_captures", STEADY,
         ["Snatcher", "Catcher", "Trapper", "Freezer", "Apex Predator", "Ice Age"],
         "Froze survivors in pods as the Beast.", "em_fb_claw", "captures", "add"),
        ("fb_ghost", "Ghost Run", "flee_beast", "fb_unseen", RARE,
         ["Quiet", "Shadow", "Ghost Run", "Phantom", "Never Seen"],
         "Escaped without the Beast laying a hand on you.", "em_fb_eye",
         "ghost runs", "add"),
        # ---------------------------------------------------- Tycoon Wars
        ("tw_mogul", "Mogul", "tycoon_wars", "tw_earned", [5, 50, 200, 600, 1500, 4000],
         ["Trader", "Merchant", "Magnate", "Mogul", "Baron", "Monopoly"],
         "Thousands of coins earned by your factories in Tycoon Wars.",
         "em_tw_coins", "thousand earned", "add"),
        ("tw_empire", "Empire Builder", "tycoon_wars", "tw_built", MANY,
         ["Foreman", "Builder", "Developer", "Industrialist", "Empire Builder", "Megacorp"],
         "Bought droppers, conveyors, upgraders and walls for your team's base.",
         "em_tw_factory", "things built", "add"),
        ("tw_raider", "Raider", "tycoon_wars", "tw_raids", COMMON,
         ["Pilferer", "Raider", "Marauder", "Corporate Spy", "Hostile Takeover", "Asset Stripper"],
         "Stole from another team's vault.", "em_tw_crowbar", "raids", "add"),
        ("tw_tycoon", "Tycoon", "tycoon_wars", "tw_wins", WINS,
         ["Startup", "Small Business", "Corporation", "Conglomerate", "Tycoon", "Fortune 1"],
         "Finished a match with the richest team.", "em_tw_tophat", "matches won", "add"),
        ("tw_mega", "Mega Dropper", "tycoon_wars", "tw_mega", [1, 5, 15, 40, 100, 250],
         ["Ambitious", "Big Spender", "Mega Dropper", "Gold Rush", "Mint", "Infinite Money"],
         "Your team built its Mega Dropper.", "em_tw_dropper", "mega droppers", "add"),
        ("tw_franchise", "Franchise", "tycoon_wars", "tw_places", TOUR,
         ["Local", "Regional", "National", "Global Franchise"],
         "Won a match in each of Tycoon Wars' four places.", "em_tw_globe", "places", "add"),
    ]


FAMILY_OF: Dict[str, str] = {
    "cataclysm": "hazard", "prop_panic": "frame", "rail_rumble": "crossbuck",
    "convoy": "chevron", "midnight_mystery": "keyhole", "grand_heist": "vault",
    "splat_turf": "splat", "bonk_brawl": "burst", "bastion": "rampart", "dodgeball": "ball",
    "bomb_bash": "bomb", "plunder_cove": "helm", "storm_circle": "cloud",
    "flee_beast": "pod", "tycoon_wars": "coin",
}


def badges(make: Callable[..., Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Every arena badge, made by ``badges._badge``."""
    out = []
    for (badge_id, name, game, stat, thresholds, ranks, desc, emblem, unit,
         mode) in _rows():
        out.append(make(badge_id, name, game, stat, list(thresholds), list(ranks), desc,
                        emblem, FAMILY_OF[game], unit, mode=mode))
    return out


# ------------------------------------------------------------------ plates
def plate(parts: List[Dict[str, Any]], family: str, body: str, trim: str,
          face: str) -> float:
    """Strike one of the arena plates; returns the radius of its enamel face
    (the emblem is printed to fit it)."""
    m = "metal"
    if family == "hazard":
        # a warning triangle, its corners rounded off with studs
        parts.append(place("tri", [0, 0.02, 0], [1.24, 1.18, 0.9], body, m=m))
        parts.append(place("tri", [0, 0.0, 0.045], [0.96, 0.90, 0.5], face))
        for x, y in ((0, 0.58), (-0.6, -0.46), (0.6, -0.46)):
            parts.append(part("sph", [x * 0.9, y * 0.94, 0.04], [0.11, 0.11, 0.08], trim, m=m))
        return 0.27
    if family == "frame":
        # a gilded picture frame: the moulding, its corner blocks, the canvas
        parts.append(part("rbox", [0, 0, 0], [1.0, 1.08, 0.12], body, m=m))
        parts.append(part("box", [0, 0, 0.05], [0.78, 0.86, 0.04], face))
        for x in (-0.45, 0.45):
            for y in (-0.49, 0.49):
                parts.append(part("box", [x, y, 0.07], [0.16, 0.16, 0.06], trim, m=m))
        return 0.37
    if family == "crossbuck":
        # a level-crossing sign: two crossed boards behind a round plate
        for angle in (0.785, -0.785):
            parts.append(part("rbox", [0, 0, -0.03], [1.26, 0.22, 0.08], "#f4efe6",
                              r=[0, 0, angle]))
            parts.append(part("box", [0, 0, 0.012], [1.18, 0.05, 0.02], "#c4281c",
                              r=[0, 0, angle]))
        parts.append(place("disc", [0, 0, 0.0], [0.86, 0.86, 0.85], body, m=m))
        parts.append(place("disc", [0, 0, 0.045], [0.66, 0.66, 0.5], face))
        return 0.33
    if family == "chevron":
        # stacked rank chevrons under a round plate
        for k in range(3):
            parts.append(place("chevron", [0, -0.30 - k * 0.15, -0.03],
                               [0.96 - k * 0.1, 0.5, 0.6], trim, m=m))
        parts.append(place("disc", [0, 0.1, 0.0], [0.86, 0.86, 0.85], body, m=m))
        parts.append(place("disc", [0, 0.1, 0.045], [0.66, 0.66, 0.5], face))
        return 0.33
    if family == "keyhole":
        # a keyhole escutcheon: the round head and its tapering slot
        parts.append(place("disc", [0, 0.16, 0.0], [0.98, 0.98, 0.85], body, m=m))
        parts.append(place("tri", [0, -0.3, -0.01], [0.66, 0.62, 0.9], body, m=m))
        parts.append(place("disc", [0, 0.16, 0.045], [0.76, 0.76, 0.5], face))
        parts.append(part("box", [0, -0.4, 0.05], [0.12, 0.22, 0.02], "#06030a"))
        return 0.30
    if family == "vault":
        # a vault door: square plate, corner bolts, a combination ring
        parts.append(part("rbox", [0, 0, 0], [1.04, 1.04, 0.14], body, m=m))
        for x in (-0.4, 0.4):
            for y in (-0.4, 0.4):
                parts.append(part("cyl", [x, y, 0.07], [0.1, 0.06, 0.1], trim,
                                  r=[HALF_PI, 0, 0], m=m))
        parts.append(place("disc", [0, 0, 0.045], [0.74, 0.74, 0.5], face))
        for k in range(16):
            a = k * math.tau / 16
            parts.append(part("box", [math.sin(a) * 0.42, math.cos(a) * 0.42, 0.075],
                              [0.025, 0.06, 0.02], trim, r=[0, 0, -a], m=m))
        return 0.33
    if family == "splat":
        parts.append(place("flower", [0, 0, 0], [1.2, 1.2, 0.9], body, m=m))
        for x, y, s in ((0.52, 0.38, 0.12), (-0.56, -0.3, 0.09), (0.36, -0.58, 0.07)):
            parts.append(part("sph", [x, y, 0.0], [s, s, 0.06], body, m=m))
        parts.append(place("disc", [0, 0, 0.045], [0.66, 0.66, 0.5], face))
        return 0.31
    if family == "burst":
        # an impact burst: two four-point sparkles turned against each other
        parts.append(place("sparkle", [0, 0, -0.02], [1.32, 1.32, 0.9], trim, m=m))
        parts.append(place("sparkle", [0, 0, 0.0], [1.12, 1.12, 0.9], body, r=[0, 0, 0.785],
                           m=m))
        parts.append(place("disc", [0, 0, 0.045], [0.66, 0.66, 0.5], face))
        return 0.31
    if family == "rampart":
        # a tower face with battlements
        parts.append(part("rbox", [0, -0.06, 0], [0.92, 0.94, 0.14], body, m=m))
        for x in (-0.34, 0, 0.34):
            parts.append(part("box", [x, 0.5, 0], [0.2, 0.18, 0.14], body, m=m))
        parts.append(place("disc", [0, -0.06, 0.045], [0.7, 0.7, 0.5], face))
        return 0.33
    if family == "ball":
        # a dodgeball: the round plate and its two curved seams
        parts.append(place("disc", [0, 0, 0], [1.04, 1.04, 0.85], body, m=m))
        parts.append(place("disc", [0, 0, 0.045], [0.78, 0.78, 0.5], face))
        for side in (1, -1):
            parts.append(part("torus", [0.62 * side, 0, 0.04], [0.5, 0.5, 0.5], trim,
                              r=[HALF_PI, 0, 0], m=m))
        return 0.36
    if family == "bomb":
        # a round bomb, its cap and a lit fuse
        parts.append(place("disc", [0, -0.04, 0], [1.0, 1.0, 0.85], body, m=m))
        parts.append(part("cyl", [0.24, 0.44, 0.0], [0.22, 0.14, 0.14], trim,
                          r=[0, 0, -0.55], m=m))
        parts.append(part("cyl", [0.36, 0.58, 0.0], [0.05, 0.2, 0.05], "#8a6a3a",
                          r=[0, 0, -0.9]))
        parts.append(place("flame", [0.48, 0.68, 0.0], [0.22, 0.22, 0.5], "#ff9a2a",
                           m="neon"))
        parts.append(place("disc", [0, -0.04, 0.045], [0.76, 0.76, 0.5], face))
        return 0.35
    if family == "helm":
        # a ship's wheel: eight handles out of a rim round the face
        for k in range(8):
            a = k * math.tau / 8
            parts.append(part("cyl", [math.sin(a) * 0.5, math.cos(a) * 0.5, -0.02],
                              [0.07, 0.34, 0.07], trim, r=[0, 0, -a], m=m))
            parts.append(part("sph", [math.sin(a) * 0.66, math.cos(a) * 0.66, -0.02],
                              [0.1, 0.1, 0.1], trim, m=m))
        parts.append(place("disc", [0, 0, 0], [0.9, 0.9, 0.85], body, m=m))
        parts.append(place("disc", [0, 0, 0.045], [0.7, 0.7, 0.5], face))
        return 0.32
    if family == "cloud":
        parts.append(place("cloud", [0, 0.05, 0], [1.3, 1.3, 0.6], body, m=m))
        parts.append(place("disc", [0, -0.02, 0.06], [0.66, 0.66, 0.5], face))
        for k, x in enumerate((-0.24, 0.0, 0.24)):
            parts.append(place("bolt", [x, -0.5 - (k % 2) * 0.06, -0.02], [0.2, 0.24, 0.5],
                               "#ffd24a", m="neon"))
        return 0.31
    if family == "pod":
        # a freezer pod: a tall rounded plate, a frosted window, two vents
        parts.append(part("rbox", [0, 0, 0], [0.84, 1.14, 0.14], body, m=m))
        parts.append(part("rbox", [0, 0.06, 0.045], [0.66, 0.82, 0.04], face))
        for y in (-0.47, 0.5):
            parts.append(part("box", [0, y, 0.075], [0.5, 0.05, 0.02], trim, m=m))
        return 0.32
    if family == "coin":
        # a milled coin
        parts.append(place("disc", [0, 0, 0], [1.04, 1.04, 0.95], body, m=m))
        for k in range(28):
            a = k * math.tau / 28
            parts.append(part("box", [math.sin(a) * 0.5, math.cos(a) * 0.5, 0.0],
                              [0.035, 0.07, 0.15], trim, r=[0, 0, -a], m=m))
        parts.append(place("disc", [0, 0, 0.045], [0.76, 0.76, 0.5], face))
        return 0.35
    raise KeyError(family)


# ------------------------------------------------------------- bot histories
# What a bot made by the factory has booked, per round played (``lo``..``hi``,
# leaning on its skill or its objective-mindedness), so a bot with a few
# hundred rounds of Rail Rumble behind it wears the badges to show for it.
# ``kills`` scales with the bot's knockouts instead of its rounds and ``wins``
# with its wins.
BOT_RATES: Dict[str, List[tuple]] = {
    "cataclysm": [("cx_survived", 0.35, 0.75, "skill"), ("cx_double", 0.0, 0.08, "skill"),
                  ("cx_close", 0.0, 0.10, ""), ("cx_last", 0.0, 0.05, "skill")],
    "prop_panic": [("pp_survived", 0.15, 0.4, "skill"), ("pp_found", 0.3, 1.6, "skill"),
                   ("pp_taunts", 0.2, 2.5, ""), ("pp_decoys", 0.0, 0.3, ""),
                   ("pp_last", 0.0, 0.05, "skill"), ("pp_sweeps", 0.0, 0.06, "skill")],
    "rail_rumble": [("rr_push_min", 0.4, 1.6, "objective"), ("rr_switches", 0.1, 1.2, "objective"),
                    ("rr_boosts", 0.1, 1.2, "objective"), ("rr_wins", 1.0, 1.0, "wins"),
                    ("rr_photo", 0.0, 0.03, ""), ("rr_pusher_kills", 0.2, 0.5, "kills")],
    "convoy": [("cv_legs", 0.2, 0.8, "objective"), ("cv_breaches", 0.05, 0.5, "objective"),
               ("cv_holds", 0.05, 0.4, "skill"), ("cv_journeys", 0.02, 0.15, "objective"),
               ("cv_kills", 1.0, 1.0, "kills")],
    "midnight_mystery": [("mm_solved", 0.02, 0.1, "skill"), ("mm_murder_wins", 0.02, 0.08, "skill"),
                         ("mm_survived", 0.25, 0.6, ""), ("mm_coins", 2.0, 8.0, "objective"),
                         ("mm_hero", 0.0, 0.02, "skill"), ("mm_spree", 0.0, 0.01, "skill")],
    "grand_heist": [("gh_loot", 0.5, 3.0, "objective"), ("gh_vaults", 0.05, 0.5, "objective"),
                    ("gh_arrests", 0.2, 1.4, "skill"), ("gh_springs", 0.02, 0.4, "objective"),
                    ("gh_clean", 0.0, 0.12, "skill"), ("gh_cop_wins", 0.1, 0.35, "")],
    "splat_turf": [("st_cells", 0.6, 2.6, "objective"), ("st_splats", 0.7, 1.0, "kills"),
                   ("st_wins", 1.0, 1.0, "wins"), ("st_landslides", 0.0, 0.06, "skill"),
                   ("st_rushes", 0.2, 1.2, "")],
    "bonk_brawl": [("bb_kos", 0.9, 1.0, "kills"), ("bb_homeruns", 0.05, 0.2, "kills"),
                   ("bb_wins", 1.0, 1.0, "wins"), ("bb_flawless", 0.0, 0.03, "skill"),
                   ("bb_powerups", 0.4, 2.0, ""), ("bb_comeback", 0.0, 0.04, "")],
    "bastion": [("bs_built", 0.6, 3.0, "objective"), ("bs_upgrades", 0.4, 2.4, "objective"),
                ("bs_kills", 1.0, 1.0, "kills"), ("bs_mechs", 0.02, 0.3, "skill"),
                ("bs_perfect", 0.0, 0.2, "skill")],
    "dodgeball": [("db_outs", 0.9, 1.0, "kills"), ("db_catches", 0.1, 0.9, "skill"),
                  ("db_wins", 1.0, 1.0, "wins"), ("db_clutch", 0.0, 0.04, "skill"),
                  ("db_rescues", 0.05, 0.6, "")],
    "bomb_bash": [("bm_wins", 1.0, 1.0, "wins"), ("bm_passes", 1.0, 5.0, ""),
                  ("bm_close", 0.0, 0.4, "skill"), ("bm_lives", 2.0, 6.0, "skill"),
                  ("bm_powerups", 0.3, 2.0, "")],
    "plunder_cove": [("pc_banked", 1.0, 6.0, "objective"), ("pc_digs", 0.2, 1.4, "objective"),
                     ("pc_steals", 0.05, 0.6, "skill"), ("pc_cannon_hits", 0.1, 0.9, ""),
                     ("pc_wins", 1.0, 1.0, "wins"), ("pc_golden", 0.0, 0.04, "objective")],
    "storm_circle": [("sc_wins", 1.0, 1.0, "wins"), ("sc_top5", 0.05, 0.35, "skill"),
                     ("sc_kills", 1.0, 1.0, "kills"), ("sc_crates", 0.8, 3.0, ""),
                     ("sc_storm_escapes", 0.05, 0.5, "")],
    "flee_beast": [("fb_escapes", 0.15, 0.5, "skill"), ("fb_hacks", 0.2, 1.2, "objective"),
                   ("fb_rescues", 0.05, 0.6, "objective"), ("fb_beast_wins", 0.02, 0.08, "skill"),
                   ("fb_captures", 0.1, 0.6, "skill"), ("fb_unseen", 0.0, 0.04, "skill")],
    "tycoon_wars": [("tw_earned", 3.0, 14.0, "objective"), ("tw_built", 3.0, 9.0, "objective"),
                    ("tw_raids", 0.1, 1.2, "skill"), ("tw_wins", 1.0, 1.0, "wins"),
                    ("tw_mega", 0.05, 0.4, "objective")],
}

# the per-place marks behind the tour badges, and Cataclysm's disasters
TOUR_MARKS: Dict[str, tuple] = {
    "cataclysm": ("cx_kind_", ["flood", "tsunami", "meteor", "tornado", "acid", "lightning",
                               "quake", "blizzard", "sandstorm", "volcano"]),
    "convoy": ("cv_place_", ["canal", "highway", "pinecrest", "neon"]),
    "splat_turf": ("st_place_", ["skatepark", "aquarium", "rooftops", "gumdrop"]),
    "dodgeball": ("db_place_", ["gym", "beach", "orbital", "castle"]),
    "bomb_bash": ("bm_place_", ["playground", "rooftops", "arcade", "pirate"]),
    "storm_circle": ("sc_place_", ["pinewood", "mesa", "city", "glacier"]),
    "tycoon_wars": ("tw_place_", ["goldvein", "sugarloaf", "timberline", "oasis"]),
}


def bot_changes(world_id: str, history: Dict[str, int], traits: Dict[str, float],
                rng: Any) -> List[tuple]:
    """(stat, amount, mode) for a made-up bot's history in one arena world."""
    rates = BOT_RATES.get(world_id)
    rounds = int(history.get("rounds", 0) or 0)
    if not rates or rounds <= 0:
        return []
    skill = traits.get("skill", 0.5)
    objective = traits.get("objective", 0.6)
    lean_of = {"skill": 0.4 + skill * 1.2, "objective": 0.4 + objective, "": 1.0}
    out: List[tuple] = []
    for stat, lo, hi, lean in rates:
        if lean == "kills":
            amount = int(int(history.get("kills", 0) or 0) * rng.uniform(lo, hi))
        elif lean == "wins":
            amount = int(history.get("wins", 0) or 0)
        else:
            amount = int(rounds * rng.uniform(lo, hi) * lean_of[lean])
        out.append((stat, amount, "add"))
    if world_id == "cataclysm":
        out.append(("cx_best_streak", int(min(18, 1 + skill * rng.uniform(2, 9) +
                                          min(6, rounds / 40))), "max"))
    if world_id == "bastion":
        out.append(("bs_best_wave", int(min(32, 3 + skill * rng.uniform(6, 20) +
                                        min(8, rounds / 25))), "max"))
    marks = TOUR_MARKS.get(world_id)
    if marks:
        prefix, ids = marks
        ids = list(ids)
        rng.shuffle(ids)
        for mark in ids[:min(len(ids), 1 + int(rounds / rng.uniform(8, 40)))]:
            out.append((prefix + mark, 1, "max"))
    return out
