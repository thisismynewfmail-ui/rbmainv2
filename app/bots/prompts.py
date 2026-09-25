"""Prompts: what a bot is told before it writes anything.

Every request has the same three layers, in this order:

1. the **system message** for the kind of interaction -- a comment section,
   in-game chat, a private message, a status post -- written in the Bots
   Zone, saying where the bot is and what normal looks like there;
2. the **persona block** under it, built from the bot's own tags, traits,
   typing style, favourite worlds, join date and about-me;
3. the **content**: the actual comment section, chat log or conversation,
   read from that bot's log for that conversation.

The content is culled to fit the context: the oldest entries go first, a
note says so, and the most recent exchange -- the thing being answered -- is
always kept.  The budget is the smaller of the configured limit and what the
server reports, less the reply's own allowance and a safety margin, measured
with the characters-per-token ratio calibrated against the server's own
tokenizer.
"""
from __future__ import annotations

import re
import time
from typing import Any, Dict, List, Optional, Sequence

from . import config as bot_config
from . import llm, personas

SAFETY_TOKENS = 64
META_TALK = re.compile(r"\b(as an ai|language model|i am an ai|i'm an ai|"
                       r"as a bot|i am a bot|i'm a bot|openai|chatgpt|"
                       r"cannot assist|can't assist|i cannot help)\b", re.I)


def _fmt(template: str, **values: Any) -> str:
    """str.format that leaves unknown {placeholders} alone."""
    def repl(match):
        key = match.group(1)
        return str(values[key]) if key in values else match.group(0)
    return re.sub(r"\{([a-z_]+)\}", repl, template or "")


def persona_block(card: Dict[str, Any]) -> str:
    tags = card.get("tags") or []
    traits = card.get("traits") or {}
    lines = personas.describe(tags)
    style = personas.style_notes(traits) or ["Casual."]
    worlds = personas.favourite_worlds(traits, bot_config.WORLD_LABELS)
    joined = card.get("joined") or 0
    return _fmt(bot_config.get("prompts.persona") or bot_config.PERSONA_TEMPLATE,
                name=card.get("name", ""),
                tags=", ".join(personas.labels(tags)),
                traits="\n".join("- " + line for line in lines),
                style=" ".join(style),
                worlds=", ".join(worlds),
                joined=time.strftime("%B %Y", time.localtime(joined)) if joined else "a while ago",
                blurb=card.get("blurb") or "(empty)")


def _budget(system: str, max_tokens: int) -> int:
    client = llm.client()
    return client.context_limit() - max_tokens - SAFETY_TOKENS - \
        client.estimate_tokens(system)


def cull(lines: Sequence[str], budget: int, keep_last: int = 1) -> List[str]:
    """The newest lines that fit in ``budget`` tokens, oldest first."""
    client = llm.client()
    kept: List[str] = []
    used = 0
    for index, line in enumerate(reversed(list(lines))):
        cost = client.estimate_tokens(line)
        if used + cost > budget and index >= keep_last:
            break
        kept.append(line)
        used += cost
    kept.reverse()
    if len(kept) < len(lines):
        kept.insert(0, "(%d older lines left out)" % (len(lines) - len(kept)))
    return kept


def _line(entry: Dict[str, Any]) -> str:
    who = entry.get("who") or "?"
    text = " ".join(str(entry.get("text") or "").split())
    tag = entry.get("tag")
    return "%s%s: %s" % (who, " (%s)" % tag if tag else "", text)


# ------------------------------------------------------------------ builders
def comment(card: Dict[str, Any], owner: str, wall: List[Dict[str, Any]],
            relation: str, reply_to: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    max_tokens = int(bot_config.get("llm.max_tokens_comment") or 96)
    system = _fmt(bot_config.get("prompts.comment"), target=owner) + \
        "\n\n" + persona_block(card)
    header = ("Comment section on %s's profile, oldest first:" % owner
              if owner != card.get("name") else
              "Comment section on your own profile, oldest first:")
    ending = []
    if relation:
        ending.append(relation)
    if reply_to:
        ending.append("%s just wrote: %s" % (reply_to.get("who"), reply_to.get("text")))
        ending.append("Write your reply to them as your next comment.")
    else:
        ending.append("Write your comment for %s's profile now." % owner)
    tail = "\n\n" + "\n".join(ending)
    budget = _budget(system + header + tail, max_tokens)
    lines = cull([_line(e) for e in wall], budget) or ["(no comments yet)"]
    user = header + "\n" + "\n".join(lines) + tail
    return {"messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
            "max_tokens": max_tokens}


def _clock(seconds: Any) -> str:
    try:
        seconds = int(seconds)
    except (TypeError, ValueError):
        return ""
    if seconds <= 0:
        return ""
    return "%d:%02d" % (seconds // 60, seconds % 60)


def game_context(state: Dict[str, Any], me: Dict[str, Any], team: str) -> List[str]:
    """What the bot could see on its own screen right now, as plain lines.

    It is background: the model is told it may use it, not that it must --
    a player knows the score without announcing it in every message.
    """
    if not state:
        return []
    lines: List[str] = []
    mode = state.get("mode")
    other = "blue" if team == "red" else ("red" if team == "blue" else "")
    if mode == "captures":
        score = state.get("score") or {}
        target = state.get("target")
        if team in score and other:
            lines.append("Score: your team (%s) %d, %s %d%s." % (
                team, int(score.get(team, 0)), other, int(score.get(other, 0)),
                "; first to %s captures wins" % target if target else ""))
        flags = state.get("flags") or {}

        def flag_line(side: str, label: str) -> None:
            flag = flags.get(side) or {}
            where = flag.get("state")
            if where == "home":
                lines.append("%s: safe at its base." % label)
            elif where == "carried":
                carrier = flag.get("by", "someone")
                whose = "your teammate" if flag.get("by_team") == team else "an enemy"
                if me.get("carrying") and side != team:
                    lines.append("%s: YOU are carrying it." % label)
                else:
                    lines.append("%s: carried by %s (%s)." % (label, carrier, whose))
            elif where == "dropped":
                lines.append("%s: lying on the ground." % label)
        if team in flags:
            flag_line(team, "Your team's flag")
        if other in flags:
            flag_line(other, "The enemy flag")
        if state.get("sudden_death"):
            lines.append("Sudden death: the next capture wins.")
        elif state.get("overtime"):
            lines.append("Overtime: the round goes on while a flag is out.")
    elif mode == "payload":
        attackers = state.get("attackers")
        if team and attackers:
            lines.append("Your team is %s this round." % (
                "attacking (pushing the cart)" if attackers == team
                else "defending (stopping the cart)"))
        reached, of = (state.get("checkpoints") or [0, 0])[:2]
        cart = "The cart is %s%% of the way along the track (%s of %s checkpoints)" % (
            state.get("progress", 0), reached, of)
        if state.get("blocked"):
            cart += ", stopped because a defender is on it"
        elif state.get("pushing"):
            cart += ", %s pushing it" % state.get("pushing")
        lines.append(cart + ".")
        wins = state.get("round_wins") or {}
        if team in wins and other:
            lines.append("Rounds won: your team %d, %s %d%s." % (
                int(wins.get(team, 0)), other, int(wins.get(other, 0)),
                "; first to %s takes the match" % state.get("target_wins")
                if state.get("target_wins") else ""))
        if state.get("setup_left"):
            lines.append("Setup: the gates open in %s." % _clock(state["setup_left"]))
    elif mode == "endless":
        if me.get("plot"):
            lines.append("Your restaurant: %s, %s upgrades built, %s coins in hand." % (
                me.get("plot"), me.get("built", 0), me.get("coins", 0)))
        best = state.get("restaurants") or []
        if best:
            lines.append("Restaurants doing best: " + "; ".join(
                "%s (%s, %s of %s upgrades)" % (r.get("name"), r.get("owner"),
                                                r.get("built"), r.get("total"))
                for r in best[:3]) + ".")
    left = _clock(state.get("time_left"))
    if left and mode != "endless" and state.get("phase") == "active":
        lines.append("Time left in the round: %s." % left)
    if state.get("players"):
        lines.append("%s players in this server." % state["players"])
    mine = []
    if me:
        if me.get("alive") is False:
            mine.append("you are dead and waiting to respawn")
        if mode != "endless" and ("kills" in me or "deaths" in me):
            mine.append("%s kills and %s deaths this round" % (me.get("kills", 0),
                                                              me.get("deaths", 0)))
        role = {"attack": "you have been attacking", "defend": "you have been defending",
                "roam": "you have been roaming the middle", "cart": "you have been on the cart",
                "tycoon": "you have been building your restaurant"}.get(me.get("role", ""))
        if role:
            mine.append(role)
    if mine:
        lines.append("You: " + "; ".join(mine) + ".")
    return lines


def chat(card: Dict[str, Any], world: str, team: str,
         log: List[Dict[str, Any]], happening: List[str],
         addressed_by: str = "", state: Optional[Dict[str, Any]] = None,
         me: Optional[Dict[str, Any]] = None, event: str = "") -> Dict[str, Any]:
    max_tokens = int(bot_config.get("llm.max_tokens_chat") or 48)
    system = _fmt(bot_config.get("prompts.chat"), world=world) + "\n\n" + \
        persona_block(card)
    if team and (state or {}).get("mode") != "endless":
        system += "\nYou are on the %s team this round." % team
    context = game_context(state or {}, me or {}, team)
    header = "Recent chat in the round, oldest first:"
    ending = []
    if context:
        ending.append("What you can see on your screen right now (background only; "
                      "bring it up only if it fits what you are saying):\n" +
                      "\n".join("- " + line for line in context))
    if happening:
        ending.append("Recently in the round: " + "; ".join(happening[-6:]))
    if event:
        ending.append("Just now: " + event)
        ending.append("React in chat the way a player would at this moment, or (skip) "
                      "if you would not bother:")
    else:
        if addressed_by:
            ending.append("%s is talking to you." % addressed_by)
        ending.append("Your next chat message, or (skip):")
    tail = "\n\n" + "\n\n".join(ending)
    budget = _budget(system + header + tail, max_tokens)
    context_lines = int(bot_config.get("messages.chat_context_lines") or 30)
    lines = cull([_line(e) for e in log[-context_lines:]], budget) or ["(quiet so far)"]
    user = header + "\n" + "\n".join(lines) + tail
    return {"messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
            "max_tokens": max_tokens}


def dm(card: Dict[str, Any], other: str, history: List[Dict[str, Any]],
       relation: str, opener: bool = False) -> Dict[str, Any]:
    max_tokens = int(bot_config.get("llm.max_tokens_dm") or 200)
    system = _fmt(bot_config.get("prompts.dm"), target=other) + "\n\n" + \
        persona_block(card)
    if relation:
        system += "\n" + relation
    me = card.get("name")
    turns: List[Dict[str, str]] = []
    for entry in history:
        role = "assistant" if entry.get("who") == me else "user"
        text = str(entry.get("text") or "").strip()
        if not text:
            continue
        if turns and turns[-1]["role"] == role:
            turns[-1]["content"] += "\n" + text
        else:
            turns.append({"role": role, "content": text})
    if opener or not turns or turns[-1]["role"] != "user":
        turns.append({"role": "user", "content":
                      "(Send %s a new message to start a conversation.)" % other
                      if not turns else "(Write your next message to %s.)" % other})
    # cull the oldest turns until it fits; the last turn always stays
    client = llm.client()
    budget = _budget(system, max_tokens)
    kept: List[Dict[str, str]] = []
    used = 0
    for index, turn in enumerate(reversed(turns)):
        cost = client.estimate_tokens(turn["content"]) + 6
        if used + cost > budget and index >= 1:
            break
        kept.append(turn)
        used += cost
    kept.reverse()
    if kept and kept[0]["role"] == "assistant":
        kept.insert(0, {"role": "user", "content": "(earlier messages left out)"})
    return {"messages": [{"role": "system", "content": system}] + kept,
            "max_tokens": max_tokens}


def post(card: Dict[str, Any], earlier: List[str], doing: str) -> Dict[str, Any]:
    max_tokens = int(bot_config.get("llm.max_tokens_post") or 96)
    system = bot_config.get("prompts.post") + "\n\n" + persona_block(card)
    lines = ["- " + p for p in earlier[-8:]] or ["(none yet)"]
    user = ("Your earlier posts:\n" + "\n".join(lines) +
            ("\n\nLately: " + doing if doing else "") + "\n\nWrite a new post.")
    return {"messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
            "max_tokens": max_tokens}


def names(count: int) -> List[Dict[str, str]]:
    examples = bot_config.get("creation.username_examples") or \
        bot_config.DEFAULT_USERNAME_EXAMPLES
    system = _fmt(bot_config.get("prompts.names"),
                  examples=", ".join(examples))
    return [{"role": "system", "content": system},
            {"role": "user", "content": "Give me %d new usernames." % count}]


def profiles(cards: List[Dict[str, Any]]) -> Dict[str, Any]:
    rows = []
    for index, card in enumerate(cards):
        tags = ", ".join(personas.labels(card.get("tags") or []))
        style = " ".join(personas.style_notes(card.get("traits") or {})) or "casual"
        rows.append("%d. name: %s | persona: %s | style: %s"
                    % (index + 1, card["name"], tags, style))
    return {"messages": [{"role": "system", "content": bot_config.get("prompts.profile")},
                         {"role": "user", "content": "Players:\n" + "\n".join(rows)}],
            "max_tokens": int(bot_config.get("llm.max_tokens_profile") or 900)}


# ----------------------------------------------------------------- clean-up
LIMITS = {"chat": 150, "comment": 290, "dm": 1800, "post": 390, "reply": 290}


def tidy(text: Optional[str], kind: str, name: str = "",
         others: Sequence[str] = ()) -> Optional[str]:
    """Turn a raw model reply into something a player would have typed."""
    if not text:
        return None
    text = text.strip()
    if kind in ("chat", "comment", "post", "reply"):
        # the model sometimes answers a transcript in transcript form
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        if not lines:
            return None
        text = lines[0] if kind == "chat" else " ".join(lines)
    for who in [name] + list(others):
        if who and re.match(r"^\[?%s\]?\s*(\([^)]*\))?\s*:" % re.escape(who), text, re.I):
            text = text.split(":", 1)[1].strip()
    text = text.strip().strip('"').strip("“”").strip()
    if text.lower().strip("(). ") in ("skip", "", "silence", "no reply", "none"):
        return None
    if META_TALK.search(text):
        return None
    limit = LIMITS.get(kind, 300)
    if len(text) > limit:
        cut = text[:limit]
        stop = max(cut.rfind(". "), cut.rfind("! "), cut.rfind("? "))
        text = cut[:stop + 1] if stop > limit * 0.5 else cut.rstrip()
    return text or None
