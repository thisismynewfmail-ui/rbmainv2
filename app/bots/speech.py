"""Speech events: things that happen in a round that bots talk about.

A flag stolen from under a team's nose, a capture, the cart reaching a
checkpoint, somebody finishing their restaurant: these are what people in a
round actually talk about, so each one raises the chance that the bots in
that round say something -- and gives the ones that do the context to say it
from where they stand. Losing your flag and grabbing theirs are the same event
seen from opposite teams, and the model is told which side of it the bot is
on.

The game host reports every event from a round a real player is in (the
same channel its chat goes over). This module is the catalogue: which events
exist in which worlds, how each reads from a given bot's point of view, whose
reaction it is most likely to be, and a few canned lines per event for when
the language model is unavailable.

Nothing here decides *whether* anyone speaks -- the chance for each event is
a setting on the Speech Events subtab, and the chat relay rolls it.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from ..models import arena_worlds as _arena_registry

ARENA = tuple(w["id"] for w in _arena_registry.ARENA_WORLDS)
CAPTURES = ("capture_the_flag", "blackout_relay")
RELAY = ("blackout_relay",)
PAYLOAD = ("fortress_team_2",)
TYCOON = ("burger_tycoon",)
SURVIVAL = ("last_light",)
ROUNDS = ("capture_the_flag", "blackout_relay", "fortress_team_2") + ARENA
ALL = ("capture_the_flag", "blackout_relay", "fortress_team_2", "burger_tycoon",
       "last_light") + ARENA

# (group id, heading on the Speech Events subtab)
GROUPS = [
    ("all", "Every world"),
    ("rounds", "Rounds: Capture The Flag, Blackout Relay, Fortress Team 2"),
    ("captures", "Capture The Flag and Blackout Relay"),
    ("relay", "Blackout Relay only"),
    ("payload", "Fortress Team 2"),
    ("tycoon", "Burger Tycoon"),
    ("survival", "Last Light"),
    ("arena", "Every arena world"),
] + [(w["id"], w["name"]) for w in _arena_registry.ARENA_WORLDS]
GROUP_WORLDS = {"all": ALL, "rounds": ROUNDS, "captures": CAPTURES,
                "relay": RELAY, "payload": PAYLOAD, "tycoon": TYCOON,
                "survival": SURVIVAL, "arena": ARENA}
GROUP_WORLDS.update({w: (w,) for w in ARENA})


class Kind:
    __slots__ = ("id", "label", "group", "chance", "help")

    def __init__(self, kind_id: str, label: str, group: str, chance: int, help: str):
        self.id, self.label, self.group = kind_id, label, group
        self.chance, self.help = chance, help

    @property
    def worlds(self) -> Tuple[str, ...]:
        return GROUP_WORLDS[self.group]


KINDS: List[Kind] = [
    Kind("player_joined", "Someone joins", "all", 30,
         "A real player arrives in the round."),
    Kind("killstreak", "Killing spree", "all", 25,
         "Somebody reaches 3, 5, 8 or 12 kills without dying."),
    Kind("streak_ended", "Spree ended", "all", 30,
         "Somebody on a spree of 3 or more is finally taken down."),
    Kind("round_start", "New round", "rounds", 15,
         "A round begins (and who is attacking, in Fortress Team 2)."),
    Kind("time_low", "Clock running out", "rounds", 30,
         "A minute left in the round."),
    Kind("round_end", "Round over", "rounds", 45,
         "A round is won, lost or drawn."),
    Kind("flag_take", "Flag stolen", "captures", 60,
         "A flag is grabbed from its base."),
    Kind("flag_drop", "Carrier down", "captures", 35,
         "A flag carrier is killed and the flag hits the ground."),
    Kind("flag_return", "Flag returned", "captures", 30,
         "A dropped flag goes back to its base."),
    Kind("flag_capture", "Capture", "captures", 65,
         "A flag is carried home and scored."),
    Kind("lockdown", "Lockdown", "relay", 20,
         "A team whose flag is out falls back to its bunkers."),
    Kind("overtime", "Overtime", "relay", 45,
         "Time is up but a flag is still out."),
    Kind("sudden_death", "Sudden death", "relay", 60,
         "Level at the end: the next capture wins."),
    Kind("setup_end", "Gates open", "payload", 25,
         "Setup is over and the attackers can push."),
    Kind("checkpoint", "Checkpoint reached", "payload", 45,
         "The cart reaches a checkpoint."),
    Kind("cart_final", "Final stretch", "payload", 40,
         "The cart enters the last part of the track."),
    Kind("tycoon_claim", "Restaurant claimed", "tycoon", 25,
         "Somebody claims an empty plot."),
    Kind("tycoon_build", "Big purchase", "tycoon", 15,
         "An upgrade is bought; dearer ones get talked about more."),
    Kind("tycoon_complete", "Restaurant finished", "tycoon", 55,
         "A restaurant gets its last upgrade."),
    Kind("area", "New area", "survival", 20,
         "A round starts: another go at the same place, or (after three wipes "
         "there) the server shuffles everybody somewhere new."),
    Kind("wave_start", "Wave incoming", "survival", 12,
         "A wave of infected begins (and any twist it comes with)."),
    Kind("wave_clear", "Wave cleared", "survival", 20,
         "The last infected of a wave goes down."),
    Kind("tank", "Tank!", "survival", 55,
         "A Tank arrives, every fifth wave."),
    Kind("tank_down", "Tank down", "survival", 50,
         "The Tank is finally killed."),
    Kind("downed", "Survivor down", "survival", 30,
         "Somebody is downed and needs picking up."),
    Kind("revived", "Revive", "survival", 25,
         "Somebody picks a downed teammate back up."),
    Kind("pinned", "Pinned", "survival", 35,
         "A Leaper pins somebody to the ground."),
    Kind("save", "Shoved off", "survival", 25,
         "Somebody knocks a Leaper off a pinned teammate."),
    Kind("lure", "Lure rung", "survival", 25,
         "Somebody sets off the area's bell, siren or horn."),
    Kind("wipe", "Wiped", "survival", 50,
         "Everybody is dead: the round is over (the third at one place shuffles "
         "the map)."),
    Kind("special", "Special spotted", "survival", 30,
         "Somebody sees a special infected (a Bomber, a Spitter...) and where."),
    Kind("swarmed", "Swarmed", "survival", 30,
         "Eight or more infected are on one survivor."),
    Kind("last_stand", "Last one standing", "survival", 60,
         "Everybody else is down or dead: one survivor left on their feet."),
    Kind("few_left", "Last few infected", "survival", 20,
         "The wave is down to its last three; time to hunt them."),
    Kind("record", "New best wave", "survival", 45,
         "The team clears a wave further than this server has got before."),
    Kind("split", "Going solo", "survival", 15,
         "Somebody wanders off on their own to look round."),
    Kind("regroup", "Regroup", "survival", 20,
         "The team is scattered and somebody calls everyone together."),
    Kind("high_ground", "High ground", "survival", 15,
         "A squad takes a roof, a deck or a tower to hold."),
    Kind("ammo_low", "Out of ammo", "survival", 15,
         "Somebody runs dry mid-wave and goes for a crate."),
    Kind("clutch", "Clutch revive", "survival", 45,
         "A revive under heavy fire, or by one of the last ones standing."),
    Kind("barrel", "Barrel blast", "survival", 30,
         "A fuel barrel takes out a pack of infected at once."),
    Kind("biled", "Covered in bile", "survival", 25,
         "A Bloater bursts on somebody and the horde comes for them."),
]

# The arena worlds.  Each event is written up by the world itself, once for
# every side and for whoever did it (``ArenaWorld.say``), so the catalogue
# here is only the names, the chances and the canned fall-backs.
ARENA_KINDS_TABLE = [
    ("arena", "ar_area", "New place", 20,
     "A round starts: another round in the same place, or the server shuffles to "
     "a new one."),
    ("arena", "ar_go", "Round starts", 15, "Setup is over and the round is on."),
    ("arena", "ar_end", "Round over", 45, "A round is won, lost or drawn."),
    ("cataclysm", "cx_disaster", "Disaster strikes", 50, "The disaster begins, and what it is."),
    ("cataclysm", "cx_survived", "Survived", 35, "The disaster blows over and the survivors count up."),
    ("cataclysm", "cx_close", "Close call", 30, "Somebody comes through it on almost no health."),
    ("cataclysm", "cx_last", "Last one standing", 55, "Only one survivor left mid-disaster."),
    ("cataclysm", "cx_shove", "Shoved", 20, "Somebody shoves somebody to their doom."),
    ("prop_panic", "pp_release", "Hunters released", 25, "The blindfolds come off."),
    ("prop_panic", "pp_found", "Prop found", 40, "A hunter finds a hidden prop."),
    ("prop_panic", "pp_taunt", "Taunt", 12, "A prop taunts the hunters."),
    ("prop_panic", "pp_decoy", "Decoy shot", 25, "A hunter falls for a decoy."),
    ("prop_panic", "pp_last", "Last prop", 50, "Only one prop left hiding."),
    ("rail_rumble", "rr_switch", "Junction thrown", 45, "A cart is sent round its detour."),
    ("rail_rumble", "rr_boost", "Cart stoked", 15, "A cart gets a burst of coal."),
    ("rail_rumble", "rr_lead", "Lead change", 30, "The other cart is now in front."),
    ("rail_rumble", "rr_final", "Final stretch", 45, "A cart enters the last part of its track."),
    ("rail_rumble", "rr_blocked", "Cart blocked", 20, "An enemy is standing on a cart."),
    ("convoy", "cv_breach", "Roadblock breached", 40, "The escort opens the leg's roadblock."),
    ("convoy", "cv_checkpoint", "Checkpoint", 30, "The convoy reaches a checkpoint."),
    ("convoy", "cv_leg", "Leg complete", 55, "The convoy rolls on to the next place."),
    ("convoy", "cv_stall", "Convoy stalled", 25, "The ambush has stopped the convoy."),
    ("midnight_mystery", "mm_kill", "Murder", 45, "Somebody is murdered."),
    ("midnight_mystery", "mm_witness", "Witness", 40, "Somebody sees who did it."),
    ("midnight_mystery", "mm_sheriff_down", "Sheriff down", 50, "The Sheriff falls and drops the gun."),
    ("midnight_mystery", "mm_gun", "Gun picked up", 45, "Somebody picks up the dropped gun."),
    ("midnight_mystery", "mm_wrong", "Wrong person", 45, "The Sheriff shoots an innocent."),
    ("grand_heist", "gh_vault", "Vault cracked", 40, "Robbers crack a vault open."),
    ("grand_heist", "gh_bag", "Bag delivered", 35, "A loot bag reaches the getaway."),
    ("grand_heist", "gh_cuff", "Arrest", 30, "A cop cuffs a robber."),
    ("grand_heist", "gh_spring", "Jailbreak", 45, "A robber springs the cell."),
    ("grand_heist", "gh_close", "Nearly there", 40, "The robbers are one bag from the target."),
    ("splat_turf", "st_rush", "Splat Rush", 45, "The last thirty seconds begin."),
    ("splat_turf", "st_lead", "Coverage lead", 25, "The other colour takes the lead."),
    ("splat_turf", "st_streak", "Splat streak", 25, "Somebody splats three in a row."),
    ("bonk_brawl", "bb_ko", "Knock-out", 25, "Somebody is knocked off the arena."),
    ("bonk_brawl", "bb_homerun", "Home run", 45, "A knock-out from a huge bonk."),
    ("bonk_brawl", "bb_last_stock", "Last stock", 35, "Somebody is down to their last stock."),
    ("bonk_brawl", "bb_powerup", "Power-up", 15, "Somebody grabs a power-up."),
    ("bastion", "bs_wave", "Wave incoming", 12, "A wave of robots sets off."),
    ("bastion", "bs_clear", "Wave cleared", 20, "The last robot of a wave goes down."),
    ("bastion", "bs_mech", "Siege Mech", 50, "A Siege Mech joins the wave."),
    ("bastion", "bs_core", "Core under attack", 45, "Robots are hitting the core."),
    ("bastion", "bs_build", "Turret built", 15, "Somebody builds or upgrades a turret."),
    ("bastion", "bs_secured", "Sector secured", 55, "The team holds the sector to the end."),
    ("bastion", "bs_lost", "Sector lost", 55, "The core falls."),
    ("dodgeball", "db_catch", "Catch", 45, "Somebody catches a throw."),
    ("dodgeball", "db_out", "Out", 12, "Somebody is hit and goes to the bench."),
    ("dodgeball", "db_last", "Last one on court", 50, "One player left for a team."),
    ("dodgeball", "db_line", "Line foul", 30, "Somebody steps over the centre line."),
    ("bomb_bash", "bm_pass", "Pass", 8, "The bomb changes hands."),
    ("bomb_bash", "bm_boom", "Boom", 40, "A bomb goes off on somebody."),
    ("bomb_bash", "bm_close", "Close call", 35, "A pass with the fuse almost gone."),
    ("bomb_bash", "bm_final", "Final two", 45, "Two players left."),
    ("plunder_cove", "pc_dig", "Chest dug", 12, "Somebody digs up a chest."),
    ("plunder_cove", "pc_score", "Chest scored", 30, "A chest reaches a ship's hold."),
    ("plunder_cove", "pc_steal", "Chest stolen", 45, "A chest is stolen from a hold."),
    ("plunder_cove", "pc_gold", "Golden chest", 40, "A golden chest is dug up."),
    ("plunder_cove", "pc_drop", "Carrier down", 25, "A chest carrier is knocked down."),
    ("storm_circle", "sc_storm", "Storm moves", 25, "The circle starts to close."),
    ("storm_circle", "sc_elim", "Elimination", 12, "Somebody is eliminated."),
    ("storm_circle", "sc_final", "Final few", 45, "Three or fewer left."),
    ("storm_circle", "sc_power", "Power weapon", 20, "Somebody loots a power weapon."),
    ("flee_beast", "fb_hack", "Computer hacked", 25, "A computer is hacked."),
    ("flee_beast", "fb_alarm", "Alarm", 30, "A missed beat sets off a computer's alarm."),
    ("flee_beast", "fb_pod", "Frozen", 35, "The Beast puts somebody in a pod."),
    ("flee_beast", "fb_free", "Freed", 40, "Somebody frees a friend from a pod."),
    ("flee_beast", "fb_exits", "Exits powered", 50, "Enough computers: the exits are live."),
    ("flee_beast", "fb_escape", "Escape", 45, "Somebody gets out."),
    ("tycoon_wars", "tw_build", "Big purchase", 15, "A company buys a big machine."),
    ("tycoon_wars", "tw_raid", "Vault raided", 50, "Somebody raids a vault."),
    ("tycoon_wars", "tw_lead", "Lead change", 30, "A new company is worth the most."),
    ("tycoon_wars", "tw_mega", "Mega Drill", 45, "A company buys the Mega Drill."),
]
KINDS.extend(Kind(kind, label, group, chance, help)
             for group, kind, label, chance, help in ARENA_KINDS_TABLE)
ARENA_KIND_IDS = frozenset(row[1] for row in ARENA_KINDS_TABLE)
KINDS_BY_ID: Dict[str, Kind] = {k.id: k for k in KINDS}
DEFAULT_CHANCES: Dict[str, int] = {k.id: k.chance for k in KINDS}


def options() -> List[List[str]]:
    """[id, label, group heading, help] rows for the settings form."""
    headings = dict(GROUPS)
    return [[k.id, k.label, headings[k.group], k.help] for k in KINDS]


def applies(kind: str, world: str) -> bool:
    info = KINDS_BY_ID.get(kind)
    return info is not None and world in info.worlds


# ----------------------------------------------------------- perspectives
# What a bot sees in an event, and how strongly it is likely to want to say
# something about it. Relations: "actor" did it, "ally" is on the team it
# helps, "victim" is on the team it hurts, "neutral" watched it happen.
VOICE = {"actor": 0.7, "ally": 1.0, "victim": 1.15, "neutral": 0.55}


def _score(event: Dict[str, Any], team: str) -> str:
    score = event.get("score") or {}
    if not isinstance(score, dict) or not score:
        return ""
    if team in score:
        other = "blue" if team == "red" else "red"
        return "Score: your team %s %d, %s %d." % (team, int(score.get(team, 0)),
                                                   other, int(score.get(other, 0)))
    return "Score: " + ", ".join("%s %d" % (t, int(v)) for t, v in sorted(score.items())) + "."


def describe(event: Dict[str, Any], name: str, team: str) -> Tuple[str, str]:
    """(what happened, from this bot's side; its relation to it)."""
    kind = event.get("kind", "")
    by = str(event.get("by") or "")
    by_team = str(event.get("by_team") or "")
    flag = str(event.get("team") or "")
    me = by and by == name
    mine = bool(team) and by_team == team

    if kind == "flag_take":
        if flag and flag == team:
            return ("An enemy, %s, just grabbed YOUR team's flag from your base." % by, "victim")
        if me:
            return ("You just grabbed the %s team's flag. Now run it home." % flag, "actor")
        if mine:
            return ("Your teammate %s just grabbed the enemy flag." % by, "ally")
        return ("%s just took the %s flag." % (by, flag), "neutral")
    if kind == "flag_drop":
        carrier = by or "the carrier"
        if flag and flag == team:
            return ("%s, the enemy carrying your flag, went down. Your flag is on "
                    "the ground; touching it sends it home." % carrier, "ally")
        if me:
            return ("You got killed carrying the %s flag and dropped it." % flag, "actor")
        if team and by_team == team:
            return ("Your teammate %s was killed carrying the enemy flag and dropped it."
                    % carrier, "victim")
        return ("%s dropped the %s flag." % (carrier, flag), "neutral")
    if kind == "flag_return":
        if flag and flag == team:
            if me:
                return ("You just returned your team's flag to base.", "actor")
            if by:
                return ("%s returned your team's flag to base." % by, "ally")
            return ("Your team's flag went back to base on its own.", "ally")
        if flag:
            return ("The %s team got their flag back to base." % flag, "victim")
        return ("A flag went back to base.", "neutral")
    if kind == "flag_capture":
        score = _score(event, team)
        if me:
            return ("You just captured the flag! %s" % score, "actor")
        if mine:
            return ("Your teammate %s just captured the flag! %s" % (by, score), "ally")
        if team:
            return ("The other team scored: %s captured your flag. %s" % (by, score), "victim")
        return ("%s captured a flag. %s" % (by, score), "neutral")
    if kind == "time_low":
        left = int(event.get("left", 60) or 60)
        return ("About %d seconds left in the round. %s" % (left, _score(event, team)), "neutral")
    if kind == "round_end":
        winner = str(event.get("winner") or "")
        reason = str(event.get("reason") or "")
        tail = (" (%s)" % reason) if reason else ""
        if not winner:
            return ("The round just ended in a draw%s." % tail, "neutral")
        if team and winner == team:
            return ("Your team just won the round%s." % tail, "ally")
        if team:
            return ("Your team just lost the round%s." % tail, "victim")
        return ("%s won the round%s." % (winner, tail), "neutral")
    if kind == "round_start":
        attackers = str(event.get("attackers") or "")
        if attackers and team:
            side = "attacking" if attackers == team else "defending"
            return ("A new round is starting; your team is %s." % side, "neutral")
        return ("A new round is starting.", "neutral")
    if kind == "lockdown":
        if not event.get("on"):
            if flag == team:
                return ("Your flag is home, so your team is out of lockdown.", "ally")
            return ("The %s team's lockdown lifted." % flag, "neutral")
        if flag == team:
            return ("Your flag is out, so your team is locked back into its bunkers "
                    "until it comes home.", "victim")
        return ("The %s team lost their flag and is locked into their bunkers." % flag, "ally")
    if kind == "overtime":
        return ("Overtime: the round will not end while a flag is out. %s"
                % _score(event, team), "neutral")
    if kind == "sudden_death":
        return ("Sudden death: the next capture wins the round.", "neutral")
    if kind == "setup_end":
        attackers = str(event.get("attackers") or "")
        if team and attackers == team:
            return ("The gates just opened: your team is attacking, push the cart.", "ally")
        return ("The gates just opened: the attackers are coming, defend.", "victim")
    if kind in ("checkpoint", "cart_final"):
        attackers = str(event.get("attackers") or "")
        where = ("checkpoint %s of %s" % (event.get("n", "?"), event.get("of", "?"))
                 if kind == "checkpoint" else "the final stretch of the track")
        if team and attackers == team:
            return ("Your team just pushed the cart to %s." % where, "ally")
        return ("The attackers just got the cart to %s." % where, "victim")
    if kind in ("tycoon_claim", "tycoon_build", "tycoon_complete"):
        plot = str(event.get("plot") or "a plot")
        mine_plot = bool(team) and str(event.get("plot_id") or "") == team
        if kind == "tycoon_claim":
            if me:
                return ("You just claimed %s." % plot, "actor")
            return ("%s just claimed %s." % (by, plot), "neutral")
        if kind == "tycoon_complete":
            if me or mine_plot:
                return ("Your restaurant, %s, just got its very last upgrade." % plot, "actor")
            return ("%s just finished every upgrade at %s." % (by, plot), "neutral")
        upgrade = str(event.get("upgrade") or "an upgrade")
        progress = "%s of %s upgrades done" % (event.get("built", "?"), event.get("total", "?"))
        if me:
            return ("You just bought %s for %s (%s)." % (upgrade, plot, progress), "actor")
        if mine_plot:
            return ("Your crewmate %s just bought %s for your restaurant (%s)."
                    % (by, upgrade, progress), "ally")
        return ("%s just bought %s for %s (%s)." % (by, upgrade, plot, progress), "neutral")
    if kind in SURVIVAL_KINDS:
        return _survival(kind, event, name, me)
    if kind in ARENA_KIND_IDS:
        return _arena(event, name, team, bool(me))
    if kind == "killstreak":
        count = int(event.get("n", 3) or 3)
        if me:
            return ("You are on a %d-kill streak." % count, "actor")
        if mine:
            return ("Your teammate %s is on a %d-kill streak." % (by, count), "ally")
        if team:
            return ("%s on the other team is on a %d-kill streak." % (by, count), "victim")
        return ("%s is on a %d-kill streak." % (by, count), "neutral")
    if kind == "streak_ended":
        victim = str(event.get("victim") or "")
        count = int(event.get("n", 3) or 3)
        if me:
            return ("You just ended %s's %d-kill streak." % (victim, count), "actor")
        if victim and victim == name:
            return ("%s just ended your %d-kill streak." % (by, count), "victim")
        if mine:
            return ("Your teammate %s just ended %s's %d-kill streak." % (by, victim, count), "ally")
        return ("%s just ended %s's %d-kill streak." % (by, victim, count), "neutral")
    if kind == "player_joined":
        if team and by_team:
            side = "your team" if by_team == team else "the other team"
            return ("%s just joined the round, on %s." % (by, side), "neutral")
        return ("%s just joined." % by, "neutral")
    return ("", "neutral")


SURVIVAL_KINDS = ("area", "wave_start", "wave_clear", "tank", "tank_down",
                  "downed", "revived", "pinned", "save", "lure", "wipe",
                  "special", "swarmed", "last_stand", "few_left", "record", "split",
                  "regroup", "high_ground", "ammo_low", "clutch", "barrel", "biled")

# what each special does, so a bot can say something that makes sense
SPECIAL_HINTS = {
    "Bloater": "it bursts into bile that draws the horde, so shoot it from range",
    "Bomber": "it wears a dynamite vest; a clean headshot defuses it",
    "Leaper": "it pounces on people and pins them",
    "Brute": "it charges and knocks people over",
    "Spitter": "it spits acid pools you must not stand in",
    "Screamer": "it calls in more infected and enrages the rest",
    "Riot": "it is armoured from the front, shoot it from behind",
    "Plague Captain": "it fires poison bolts and raises the dead",
    "Hive": "it bursts into a swarm of mites",
    "Burrower": "it digs under you and comes up beneath",
    "Ronin": "it deflects bullets with a blade, then dashes in",
}


def _survival(kind: str, event: Dict[str, Any], name: str, me: bool) -> Tuple[str, str]:
    """Last Light: one team against the horde, so everything is "us"."""
    by = str(event.get("by") or "")
    what = str(event.get("what") or "")
    n = int(event.get("n", 0) or 0)
    if kind == "area":
        if event.get("retry"):
            return ("Your team is running %s back: attempt %d of 3 there, from wave "
                    "one." % (what or "the area", max(2, n)), "ally")
        return ("The server just shuffled everybody to %s; the waves start again "
                "from one." % (what or "a new area"), "neutral")
    if kind == "wave_start":
        twist = (" It is a %s." % what) if what else ""
        if event.get("tank"):
            return ("Wave %d is starting, and it is a Tank wave.%s" % (n, twist), "ally")
        return ("Wave %d of infected is starting.%s" % (n, twist), "ally")
    if kind == "wave_clear":
        return ("Your team just cleared wave %d. Time to restock and heal." % n, "ally")
    if kind == "tank":
        return ("A Tank -- a huge boss infected -- just showed up on wave %d." % n, "victim")
    if kind == "tank_down":
        if me:
            return ("You landed the killing shot on the Tank.", "actor")
        return ("The Tank is dead%s." % ((", %s finished it" % by) if by else ""), "ally")
    if kind == "downed":
        if me:
            return ("You just got downed%s and need a teammate to pick you up."
                    % ((" by a " + what) if what else ""), "victim")
        return ("Your teammate %s is down and needs reviving." % by, "victim")
    if kind == "revived":
        if me:
            return ("You just picked %s back up." % what, "actor")
        if what == name:
            return ("%s just revived you." % by, "ally")
        return ("%s picked %s back up." % (by, what), "ally")
    if kind == "pinned":
        if me:
            return ("A %s just pinned you to the ground; you need help." % (what or "Leaper"),
                    "victim")
        return ("%s is pinned by a %s." % (by, what or "Leaper"), "victim")
    if kind == "save":
        if me:
            return ("You shoved a Leaper off a teammate.", "actor")
        return ("%s shoved a Leaper off a teammate." % by, "ally")
    if kind == "lure":
        if me:
            return ("You rang %s to draw the horde away." % what, "actor")
        return ("%s rang %s and the horde is heading for it." % (by, what), "ally")
    if kind == "wipe":
        held = "Everybody died: your team held %s for %d waves." % (what or "the area", n)
        left = int(event.get("left", 0) or 0)
        if left > 0:
            return ("%s You get %d more %s there before the server shuffles the map."
                    % (held, left, "try" if left == 1 else "tries"), "victim")
        nxt = str(event.get("next") or "")
        return ("%s That was the third wipe there, so the server shuffles to %s."
                % (held, nxt or "a new area"), "victim")
    where = str(event.get("where") or "")
    near = (" near %s" % where) if where else ""
    place = (" near %s" % what) if what else ""
    if kind == "special":
        hint = SPECIAL_HINTS.get(what, "")
        hint = (" (%s)" % hint) if hint else ""
        if me:
            return ("You just spotted a %s%s%s." % (what or "special infected", near, hint),
                    "actor")
        return ("%s just called out a %s%s%s." % (by, what or "special infected", near, hint),
                "victim")
    if kind == "swarmed":
        if me:
            return ("You are getting swarmed by the horde%s." % place, "victim")
        return ("Your teammate %s is getting swarmed by the horde%s." % (by, place), "victim")
    if kind == "last_stand":
        if me:
            return ("Everybody else is down or dead: you are the LAST one standing%s." % place,
                    "victim")
        return ("%s is the last survivor still standing%s; everyone else is down or dead."
                % (by, place), "victim")
    if kind == "few_left":
        return ("Only %d infected left in this wave; time to hunt the stragglers." % max(1, n),
                "ally")
    if kind == "record":
        return ("Your team just cleared wave %d, the furthest anyone has got on this server."
                % n, "ally")
    if kind == "split":
        towards = (" towards %s" % what) if what else ""
        if me:
            return ("You just went off on your own to look round%s." % towards, "actor")
        return ("%s just wandered off on their own%s." % (by, towards), "neutral")
    if kind == "regroup":
        if me:
            return ("You told everyone to regroup with you%s." % place, "actor")
        return ("%s is calling everyone to regroup%s." % (by, place), "ally")
    if kind == "high_ground":
        if me:
            return ("Your squad just took the high ground: %s." % (what or "a roof"), "actor")
        return ("%s's squad is holding the high ground: %s." % (by, what or "a roof"), "ally")
    if kind == "ammo_low":
        if me:
            return ("You are nearly out of ammo mid-wave and heading for a crate%s." % place,
                    "victim")
        return ("%s is out of ammo mid-wave%s." % (by, place), "neutral")
    if kind == "clutch":
        if me:
            return ("You just clutch-revived %s with the horde all over you." % what, "actor")
        if what == name:
            return ("%s just clutch-revived you under heavy fire." % by, "ally")
        return ("%s just pulled off a clutch revive on %s under heavy fire." % (by, what), "ally")
    if kind == "barrel":
        if me:
            return ("You blew up a fuel barrel and took out %d infected at once." % n, "actor")
        return ("A fuel barrel%s just blew up %d infected at once."
                % ((" shot by %s" % by) if by else "", n), "ally")
    if kind == "biled":
        if me:
            return ("You just got covered in Bloater bile: every infected is coming for you.",
                    "victim")
        return ("%s just got covered in bile and the horde is going for them." % by, "victim")
    return ("", "neutral")


def _arena(event: Dict[str, Any], name: str, team: str, me: bool) -> Tuple[str, str]:
    """An arena world's event, as the world wrote it for this bot: what only
    it knows (a witness), what it did, what its side saw, or the plain
    version."""
    private = (event.get("private") or {}).get(name)
    if private:
        return str(private[0]), str(private[1] if len(private) > 1 else "neutral")
    if me and event.get("actor"):
        return str(event["actor"]), "actor"
    sides = event.get("sides") or {}
    if team and team in sides:
        text, relation = (list(sides[team]) + ["neutral"])[:2]
        return str(text), str(relation)
    default = list(event.get("default") or ["", "neutral"]) + ["neutral"]
    return str(default[0]), str(default[1])


def voice_weight(event: Dict[str, Any], relation: str) -> float:
    if event.get("kind") == "player_joined":
        return 1.0
    return VOICE.get(relation, 0.5)


def importance(event: Dict[str, Any]) -> float:
    """How much bigger (or smaller) news this one is than the usual of its kind."""
    kind = event.get("kind", "")
    if kind == "tycoon_build":
        # a milkshake machine is small talk; a drive-through is news
        cost = float(event.get("cost", 0) or 0)
        return max(0.3, min(2.0, 0.4 + cost / 2500.0))
    if kind in ("killstreak", "streak_ended"):
        count = int(event.get("n", 3) or 3)
        return 1.0 if count < 5 else (1.4 if count < 8 else 1.8)
    if kind in ("wave_start", "wave_clear"):
        # the tenth wave is news; the second is not
        return max(0.5, min(2.0, 0.4 + int(event.get("n", 1) or 1) * 0.12))
    if kind == "wipe":
        return max(0.8, min(2.0, 0.6 + int(event.get("n", 1) or 1) * 0.1))
    if kind == "barrel":
        return max(0.8, min(2.0, 0.5 + int(event.get("n", 3) or 3) * 0.12))
    if kind == "record":
        return max(1.0, min(2.0, 0.6 + int(event.get("n", 1) or 1) * 0.08))
    return 1.0


# ------------------------------------------------------ canned fall-backs
# Typed when the language model is unavailable, so a round never goes quiet
# about a stolen flag just because the model is busy or down.
CANNED: Dict[Tuple[str, str], List[str]] = {
    ("flag_take", "victim"): ["they have our flag", "flag!!", "stop the carrier",
                              "someone get the flag back", "carrier coming through mid",
                              "defend!!"],
    ("flag_take", "actor"): ["got it", "i have the flag", "cover me", "going home w flag"],
    ("flag_take", "ally"): ["go go go", "escort him", "nice grab", "cover the carrier"],
    ("flag_drop", "ally"): ["flag down, return it", "get our flag", "nice, touch the flag"],
    ("flag_drop", "victim"): ["noo", "pick it up", "so close", "grab it again"],
    ("flag_return", "ally"): ["flag is back", "nice return", "ty"],
    ("flag_return", "victim"): ["ugh", "so close", "again"],
    ("flag_capture", "actor"): ["lets go", "ez cap", "got it home"],
    ("flag_capture", "ally"): ["lets go", "nice cap", "GG", "yesss", "lets gooo", "w"],
    ("flag_capture", "victim"): ["how did he get through", "defense??", "wow", "ugh",
                                 "who was on d"],
    ("round_end", "ally"): ["gg", "gg wp", "ggs", "ez", "gg all"],
    ("round_end", "victim"): ["gg", "ggs", "close one", "rematch", "gg wp"],
    ("round_end", "neutral"): ["gg", "ggs", "good game"],
    ("time_low", "neutral"): ["1 min left", "hurry", "clock", "last minute"],
    ("sudden_death", "neutral"): ["sudden death lets go", "next cap wins", "this is it"],
    ("overtime", "neutral"): ["overtime!!", "ot", "dont let them cap"],
    ("setup_end", "ally"): ["push push", "go go go", "on the cart"],
    ("setup_end", "victim"): ["here they come", "hold the line", "defend"],
    ("checkpoint", "ally"): ["checkpoint!", "keep pushing", "nice push"],
    ("checkpoint", "victim"): ["stop the cart", "get on the cart", "hold them"],
    ("cart_final", "ally"): ["almost there", "push!!", "last stretch"],
    ("cart_final", "victim"): ["stop the cart!!", "last chance", "everyone on the cart"],
    ("tycoon_complete", "neutral"): ["nice restaurant", "how", "rich"],
    ("tycoon_complete", "actor"): ["done!!", "finally finished", "lets gooo"],
    ("killstreak", "victim"): ["who is this", "stop him", "someone get him"],
    ("killstreak", "ally"): ["carry", "nice", "go off"],
    ("streak_ended", "actor"): ["got him", "streak over", "ez"],
    ("streak_ended", "victim"): ["bruh", "lag", "was on a roll"],
    ("player_joined", "neutral"): ["hi", "hey", "yo", "welcome", "o/", "sup"],
    ("area", "neutral"): ["new map lets go", "ooh this one", "stick together", "find the ammo",
                          "finally a new map", "ok fresh start"],
    ("area", "ally"): ["run it back", "again", "we got this one", "this time fr",
                       "dont split up this time", "ok focus"],
    ("wave_start", "ally"): ["here they come", "stack up", "reload", "stay together"],
    ("wave_clear", "ally"): ["nice", "wave clear", "get ammo", "heal up", "ez"],
    ("tank", "victim"): ["TANK", "tank!!", "everyone on the tank", "run", "oh no"],
    ("tank_down", "ally"): ["tank down!!", "lets go", "gg tank", "ez tank"],
    ("tank_down", "actor"): ["got the tank", "lets gooo", "ez"],
    ("downed", "victim"): ["help", "pick me up", "im down", "someone get him up", "revive!!"],
    ("revived", "ally"): ["ty", "thanks", "saved", "nice"],
    ("revived", "actor"): ["np", "got you", "up you go"],
    ("pinned", "victim"): ["HELP", "get it off", "shoot it", "leaper!!"],
    ("save", "ally"): ["nice save", "ty", "clutch"],
    ("lure", "ally"): ["nice bell", "go go while theyre distracted", "smart"],
    ("wipe", "victim"): ["gg", "so close", "next time", "gg all", "rip", "one more",
                         "again again"],
    ("special", "actor"): ["special here", "watch out", "got a special"],
    ("special", "victim"): ["where", "on it", "i see it", "focus it"],
    ("swarmed", "victim"): ["theyre all over me", "help", "too many", "need help here"],
    ("last_stand", "victim"): ["its all on me", "clutch time", "dont die", "its up to you"],
    ("few_left", "ally"): ["few left", "hunt them", "where are the last ones"],
    ("record", "ally"): ["new record", "lets gooo", "furthest weve been", "ez"],
    ("split", "actor"): ["brb scouting", "going for a look"],
    ("split", "neutral"): ["where u going", "dont die lol", "lone wolf"],
    ("regroup", "ally"): ["omw", "coming", "on my way"],
    ("high_ground", "ally"): ["nice spot", "omw up", "coming up"],
    ("high_ground", "actor"): ["get up here", "up top"],
    ("ammo_low", "victim"): ["need ammo", "reloading", "cover me"],
    ("clutch", "ally"): ["clutch", "huge", "what a save", "ty"],
    ("clutch", "actor"): ["np", "got you", "that was close"],
    ("barrel", "ally"): ["boom", "nice barrel", "lmao", "big boom"],
    ("barrel", "actor"): ["boom", "lol", "kaboom"],
    ("biled", "victim"): ["run", "get away from him", "cover him", "ew"],
    # ---- the arena worlds
    ("ar_area", "neutral"): ["new map", "ooh this one", "lets go", "i love this one", "ok"],
    ("ar_go", "neutral"): ["go go go", "here we go", "gl", "lets go", "gl hf"],
    ("ar_end", "ally"): ["gg", "ez", "gg wp", "lets go", "ggs"],
    ("ar_end", "victim"): ["gg", "close one", "rematch", "ggs", "next one"],
    ("ar_end", "actor"): ["gg", "lets gooo", "ez", "gg all"],
    ("ar_end", "neutral"): ["gg", "ggs", "good game"],
    ("cx_disaster", "neutral"): ["RUN", "oh no", "get high", "find a roof", "here it comes"],
    ("cx_survived", "neutral"): ["survived", "made it", "ez", "that was close"],
    ("cx_survived", "actor"): ["made it!!", "survived lol", "ez"],
    ("cx_last", "neutral"): ["youre the last one", "dont die", "clutch time"],
    ("cx_shove", "victim"): ["why", "bro", "who pushed me", "rude"],
    ("cx_shove", "actor"): ["oops", "lol", "byeee"],
    ("pp_release", "neutral"): ["here they come", "shh", "dont move"],
    ("pp_found", "actor"): ["got one", "found you", "lol nice try"],
    ("pp_found", "victim"): ["noo", "how", "they got me"],
    ("pp_taunt", "neutral"): ["lol", "i heard that", "where was that"],
    ("pp_last", "neutral"): ["one left", "find the last one", "dont move"],
    ("rr_switch", "victim"): ["they switched our track", "junction!!", "get the lever"],
    ("rr_switch", "ally"): ["nice switch", "sent them round", "lol"],
    ("rr_final", "ally"): ["almost there", "push push", "last stretch"],
    ("rr_final", "victim"): ["stop their cart", "everyone on their cart", "block it"],
    ("cv_breach", "ally"): ["roadblock open", "nice", "push through"],
    ("cv_breach", "victim"): ["they opened it", "fall back", "hold the next corner"],
    ("cv_leg", "ally"): ["next leg", "rolling on", "lets go"],
    ("cv_leg", "victim"): ["hold the next one", "they got through", "regroup"],
    ("mm_kill", "neutral"): ["someone died", "who was that", "omg", "run"],
    ("mm_sheriff_down", "neutral"): ["gun dropped", "sheriff is down", "get the gun"],
    ("mm_gun", "neutral"): ["someone has the gun", "hero time", "go get him"],
    ("mm_wrong", "neutral"): ["sheriff shot the wrong guy", "lol rip", "bruh"],
    ("gh_vault", "ally"): ["vault open", "grab the bags", "go go go"],
    ("gh_vault", "victim"): ["they cracked it", "stop the bags", "cover the getaway"],
    ("gh_bag", "ally"): ["bag secured", "ka-ching", "more more"],
    ("gh_cuff", "victim"): ["got cuffed", "spring me", "help"],
    ("gh_spring", "ally"): ["free!!", "jailbreak", "ty"],
    ("st_rush", "neutral"): ["splat rush", "paint everything", "go go go"],
    ("st_lead", "victim"): ["they are ahead", "paint more", "push"],
    ("bb_ko", "actor"): ["bonk", "byeee", "home run"],
    ("bb_ko", "victim"): ["nooo", "how", "rip"],
    ("bb_homerun", "neutral"): ["HOME RUN", "he flew", "lmao"],
    ("bs_mech", "neutral"): ["MECH", "big one", "everyone on the mech"],
    ("bs_core", "neutral"): ["core!!", "they are at the core", "defend the core"],
    ("bs_clear", "neutral"): ["wave clear", "nice", "build more"],
    ("bs_secured", "neutral"): ["SECURED", "gg", "we held it"],
    ("bs_lost", "neutral"): ["core down", "gg", "next time"],
    ("db_catch", "actor"): ["caught it", "nice try", "got it"],
    ("db_catch", "ally"): ["nice catch", "clutch", "lets go"],
    ("db_catch", "victim"): ["no way", "how did he catch that", "bruh"],
    ("db_last", "neutral"): ["one left", "clutch time", "you got this"],
    ("db_line", "neutral"): ["line!!", "lol stepped over", "out"],
    ("bm_boom", "neutral"): ["BOOM", "lol", "rip", "kaboom"],
    ("bm_close", "neutral"): ["so close", "lmao", "just in time"],
    ("bm_final", "neutral"): ["final two", "who wins", "dont get tagged"],
    ("pc_steal", "victim"): ["they stole our chest", "stop him", "thief!!"],
    ("pc_steal", "ally"): ["nice steal", "run run", "got one"],
    ("pc_gold", "neutral"): ["GOLD", "gold chest!!", "escort the gold"],
    ("pc_score", "ally"): ["scored", "nice", "more gold"],
    ("sc_storm", "neutral"): ["storm coming", "move in", "rotate"],
    ("sc_final", "neutral"): ["final three", "gl", "this is it"],
    ("fb_alarm", "neutral"): ["oops", "alarm!!", "it heard that"],
    ("fb_pod", "victim"): ["help", "free me", "im in a pod"],
    ("fb_free", "ally"): ["ty", "freed", "run"],
    ("fb_exits", "neutral"): ["EXITS OPEN", "go go go", "get out"],
    ("fb_escape", "neutral"): ["one got out", "escaped", "lets go"],
    ("tw_raid", "victim"): ["raided!!", "guard the vault", "who was that"],
    ("tw_raid", "actor"): ["ka-ching", "ez money", "lol"],
    ("tw_mega", "neutral"): ["mega drill wow", "rich", "theyre winning"],
}


def canned(event: Dict[str, Any], relation: str, rng) -> Optional[str]:
    lines = CANNED.get((event.get("kind", ""), relation))
    return rng.choice(lines) if lines else None
