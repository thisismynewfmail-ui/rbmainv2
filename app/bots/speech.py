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

CAPTURES = ("capture_the_flag", "blackout_relay")
RELAY = ("blackout_relay",)
PAYLOAD = ("fortress_team_2",)
TYCOON = ("burger_tycoon",)
ROUNDS = ("capture_the_flag", "blackout_relay", "fortress_team_2")
ALL = ("capture_the_flag", "blackout_relay", "fortress_team_2", "burger_tycoon")

# (group id, heading on the Speech Events subtab)
GROUPS = [
    ("all", "Every world"),
    ("rounds", "Rounds: Capture The Flag, Blackout Relay, Fortress Team 2"),
    ("captures", "Capture The Flag and Blackout Relay"),
    ("relay", "Blackout Relay only"),
    ("payload", "Fortress Team 2"),
    ("tycoon", "Burger Tycoon"),
]
GROUP_WORLDS = {"all": ALL, "rounds": ROUNDS, "captures": CAPTURES,
                "relay": RELAY, "payload": PAYLOAD, "tycoon": TYCOON}


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
]
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
}


def canned(event: Dict[str, Any], relation: str, rng) -> Optional[str]:
    lines = CANNED.get((event.get("kind", ""), relation))
    return rng.choice(lines) if lines else None
