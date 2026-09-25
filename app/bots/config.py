"""The Bots Zone settings.

One schema drives everything: the defaults, the validation every save goes
through, and the forms the dashboard draws -- each field below becomes a
control in the subtab named by its ``section``, so a new setting is one entry
here and nothing else.

Every field says what *kind* of setting it is, because the dashboard shows it:

``universal``  one value for the whole platform (a toggle, a URL, a limit)
``per-bot``    a range; every bot draws its own value from inside it once,
               nudged by its persona, and keeps it (session length, skill)
``base``       one platform-wide value that each bot then scales by its own
               persona (how chatty in-game chat is, the in-game share)

Only the values an administrator actually changed are stored (as JSON in the
``meta`` table), so a later change to a default still reaches every install
that never touched that row.
"""
from __future__ import annotations

import json
import re
import threading
import time
from typing import Any, Callable, Dict, List, Optional

from .. import db
from . import speech as speech_catalogue

META_KEY = "bots.config"

DEFAULT_USERNAME_EXAMPLES = [
    "Scarvia", "crtea20", "teto gaming", "bolin", "DavidJoggins",
    "NyxieSticks", "keigo", "pushmataha", "EgonisCoolCat", "SHOUBI",
    "Subaru", "zFcBoxhead", "banjo53",
]

DEFAULT_LOCATIONS = [
    "", "", "", "Canada", "UK", "Texas", "Ohio", "somewhere cold",
    "Australia", "Germany", "the lobby", "Brazil", "Poland", "my room",
    "California", "Florida", "New York", "Sweden", "France", "Philippines",
    "Netherlands", "Mexico", "under your bed", "Burger Tycoon plot 3",
    "Scotland", "Ireland", "Norway", "Japan", "Chile", "Arizona",
]

WORLD_IDS = ["burger_tycoon", "capture_the_flag", "fortress_team_2",
             "blackout_relay"]
WORLD_LABELS = {"burger_tycoon": "Burger Tycoon",
                "capture_the_flag": "Capture The Flag",
                "fortress_team_2": "Fortress Team 2",
                "blackout_relay": "Blackout Relay"}

# ------------------------------------------------------------------ prompts
PROMPT_COMMENT = """You are a player on BLOCKHAVEN, an online block-game platform with worlds like Burger Tycoon, Capture The Flag, Fortress Team 2 and Blackout Relay. You are leaving a comment on the comment section of {target}'s profile page. Profile comments are short, casual and public, like a guestbook: greetings, compliments on an avatar or hat, "gg earlier", inviting someone to play, inside jokes between friends, replying to what was said before.

Rules:
- Write exactly ONE comment, as the character described below, in their typing style.
- Keep it short: usually 3 to 20 words. No hashtags, no quotation marks, no signature.
- React to the recent comments if there are any; never repeat a comment that is already there.
- Never mention being an AI, a bot, a language model or a prompt. You are simply a player.
- Output only the comment text."""

PROMPT_CHAT = """You are a player typing in the in-game chat of the BLOCKHAVEN world "{world}". Other players can see what you type. In-game chat is fast and very short: usually 1 to 10 words, often lowercase, reacting to what is happening in the round, greeting people, joking, asking for help, trash talking a little or saying gg.

Rules:
- Write exactly ONE chat message as the character described below, in their typing style.
- If nothing needs a reply, output exactly: (skip)
- Never mention being an AI, a bot, a language model or a prompt. You are a player in the round.
- Output only the chat message."""

PROMPT_DM = """You are a player on BLOCKHAVEN, an online block-game platform, answering a private message from {target}. Private messages are casual and personal: one to three short sentences, the way people text.

Rules:
- Reply as the character described below, in their typing style, and stay consistent with what you said earlier in this conversation.
- Be natural: answer questions, ask one back sometimes, suggest playing a world together if it fits.
- Never mention being an AI, a bot, a language model or a prompt. You are simply a player.
- Output only the message text."""

PROMPT_POST = """You are a player on BLOCKHAVEN, an online block-game platform, writing a short status post ("shout") on your own profile for your friends to see: what you have been playing, an item you want, a funny moment, how your day is going.

Rules:
- Write exactly ONE post as the character described below, in their typing style, 4 to 25 words.
- Do not repeat your earlier posts.
- Never mention being an AI, a bot, a language model or a prompt.
- Output only the post text."""

PROMPT_NAMES = """You invent usernames for new player accounts on BLOCKHAVEN, an online block game popular with teens and young adults. The names must look like names real people pick for themselves: nicknames, gamer tags, a word plus a number, a first-and-last name mashup, a favourite character, an in-joke, a stretched or oddly capitalised word. Mix the styles; do not make them all look alike.

Here are real usernames from the platform to show the range of styles:
{examples}

Rules for every name:
- 3 to 20 characters, letters, digits and underscores only (a space becomes an underscore or is dropped).
- No real celebrities, no brands, nothing offensive, nothing that says "bot", "npc", "ai" or "player".
- Every name must be different from the others and from the examples.

Answer with a JSON array of strings and nothing else."""

PROMPT_PROFILE = """You write the "About me" line and location for BLOCKHAVEN player profiles. BLOCKHAVEN is an online block-game platform (Burger Tycoon, Capture The Flag, Fortress Team 2, Blackout Relay, hats, Unusual effects, trading). Real profiles are short and personal: a joke, what they play, a favourite hat, a friend's name, a song lyric, an age, "add me", or nothing profound at all.

For each player described, write an about-me of 0 to 22 words in that player's own typing style, and a location (a country, a state, a city, something silly, or an empty string).

Answer with a JSON array of objects like {{"name": "...", "about": "...", "location": "..."}} in the same order, and nothing else."""

PERSONA_TEMPLATE = """## Your character
Username: {name}
Persona: {tags}
{traits}
Typing style: {style}
Favourite worlds: {worlds}
Joined BLOCKHAVEN: {joined}
About me: {blurb}"""


# ------------------------------------------------------------------ schema
class Field:
    __slots__ = ("key", "label", "kind", "default", "section", "help",
                 "min", "max", "step", "unit", "scope", "options", "toggle",
                 "rows", "nullable")

    def __init__(self, key: str, label: str, kind: str, default: Any,
                 section: str, help: str = "", min: Optional[float] = None,
                 max: Optional[float] = None, step: Optional[float] = None,
                 unit: str = "", scope: str = "universal",
                 options: Optional[List[Any]] = None, toggle: bool = False,
                 rows: int = 4, nullable: bool = False):
        self.key, self.label, self.kind = key, label, kind
        self.default, self.section, self.help = default, section, help
        self.min, self.max, self.step, self.unit = min, max, step, unit
        self.scope, self.options, self.toggle = scope, options, toggle
        self.rows, self.nullable = rows, nullable

    def describe(self) -> Dict[str, Any]:
        return {k: getattr(self, k) for k in self.__slots__}


SECTIONS = [
    ("stats", "Bot Stats", "Every bot, where it is and what it is doing."),
    ("creation", "Bot Creation", "Generate bots now, or let the population grow by itself."),
    ("personas", "Personas", "The tags that decide how every bot behaves."),
    ("presence", "Presence & Schedule", "When bots are online, and for how long."),
    ("worlds", "Joining Worlds", "How bots pick a world and an instance, and how empty instances sleep."),
    ("ingame", "In-Game Behaviour", "How bots play when a real player is in the round."),
    ("friends", "Friends", "Bots adding and confirming friends."),
    ("chatter", "Chatter", "Profile comments, posts and likes between associated bots."),
    ("messages", "DMs & Chat", "Private messages and in-game chat."),
    ("modifiers", "Dynamic Modifiers", "Short-lived boosts that follow a live conversation, then fade."),
    ("speech", "Speech Events", "What happens in a round, and how likely bots are to talk about it."),
    ("llm", "Language Model", "The endpoint every word a bot writes comes from."),
    ("prompts", "Prompts", "The system message used for each kind of interaction."),
]

TAG_OPTIONS: List[str] = []   # filled in by _tag_options() below


def _tag_options() -> List[str]:
    from . import personas
    return list(personas.BUILTIN_TAG_IDS)


F = Field
FIELDS: List[Field] = [
    # ------------------------------------------------------------- master
    F("system.enabled", "Bot system", "bool", True, "stats",
      "Master switch. Off freezes every bot where it is: no one comes online, "
      "joins a world, comments or replies until it is back on.", toggle=True),

    # ------------------------------------------------------------ creation
    F("creation.enabled", "Bots keep creating themselves", "bool", False,
      "creation", "Grow the population towards the target below in the "
      "background, a few at a time.", toggle=True),
    F("creation.target_population", "Target population", "int", 1000,
      "creation", "How many bots auto-creation grows to.", 0, 500000, 1,
      "bots"),
    F("creation.rate_per_minute", "Creation rate", "int", 30, "creation",
      "How fast auto-creation adds bots.", 1, 20000, 1, "bots/min"),
    F("creation.username_source", "Usernames come from", "select",
      "llm_then_procedural", "creation",
      "The language model is given the examples below. If it is unreachable "
      "the built-in generator takes over.",
      options=[["llm_then_procedural", "Language model, generator as fallback"],
               ["llm", "Language model only"],
               ["procedural", "Built-in generator only"]]),
    F("creation.username_examples", "Example usernames", "list",
      DEFAULT_USERNAME_EXAMPLES, "creation",
      "Real usernames the model is shown so its names look like people's.",
      rows=5),
    F("creation.names_per_request", "Names per model request", "int", 24,
      "creation", "Usernames asked for in one request.", 1, 100, 1),
    F("creation.username_retries", "Duplicate-name retries", "int", 4,
      "creation", "When the model repeats a name that is taken, it is told so "
      "and asked for replacements this many times before the generator fills "
      "the gap.", 0, 12, 1),
    F("creation.profile_source", "About-me text comes from", "select",
      "llm_then_procedural", "creation", "",
      options=[["llm_then_procedural", "Language model, generator as fallback"],
               ["llm", "Language model only"],
               ["procedural", "Built-in generator only"]]),
    F("creation.join_date", "Join date range", "daterange",
      ["2022-01-01", ""], "creation",
      "Each new bot's 'joined' date is drawn from inside this window (blank "
      "end = today).", scope="per-bot"),
    F("creation.tags_per_bot", "Persona tags per bot", "range", [6, 9],
      "creation", "Five core tags (schedule, skill, focus, social, voice) "
      "plus extras.", 5, 14, 1, "tags", scope="per-bot"),
    F("creation.credits", "Nooget balance", "range", [150, 14000], "creation",
      "", 0, 1000000, 50, "Noogets", scope="per-bot"),
    F("creation.items_owned", "Items owned", "range", [3, 16], "creation",
      "Collectors own more, newbies fewer.", 0, 60, 1, "items",
      scope="per-bot"),
    F("creation.unusual_chance", "Unusual chance per hat", "float", 0.005,
      "creation", "The site rate is 0.005 (0.5%).", 0, 1, 0.001),
    F("creation.female_share", "Female build share", "pct", 45, "creation",
      "", 0, 100, 1, "%"),
    F("creation.public_server_share", "Show their server publicly", "pct", 40,
      "creation", "Share of bots whose privacy lets anyone see the world "
      "they are in (the rest show it to friends, like the site default).",
      0, 100, 1, "%"),
    F("creation.seed_friendships", "Arrive with friends", "bool", True,
      "creation", "Older accounts are created with friendships they would "
      "already have made, back-dated, with associated bots."),
    F("creation.seed_stats", "Arrive with play history", "bool", True,
      "creation", "Kills, rounds and playtime in proportion to account age."),
    F("creation.locations", "Location pool", "list", DEFAULT_LOCATIONS,
      "creation", "Used by the built-in generator (blank lines = no "
      "location).", rows=6),

    # ------------------------------------------------------------ personas
    F("personas.tag_weights", "Tag weights", "weights", {}, "personas",
      "How common each tag is among new bots (1 = normal, 0 = never).",
      0, 5, 0.1, options="tags"),
    F("personas.custom_tags", "Custom tags", "list", [], "personas",
      "One per line as  tag: what it means  -- they join friend matching and "
      "every prompt.", rows=5),

    # ------------------------------------------------------------ presence
    F("presence.enabled", "Bots come online", "bool", True, "presence",
      "Bots log in and out on the schedule below.", toggle=True),
    F("presence.utc_offset", "Clock (UTC offset)", "float", None, "presence",
      "Blank uses this server's local time.", -12, 14, 0.5, "h",
      nullable=True),
    F("presence.peak_hours", "Peak play time", "hours", [18, 23], "presence",
      "Start and end of the evening peak (hours, 24h clock).", 0, 24, 0.5,
      "h"),
    F("presence.peak_online", "Online at peak", "pct", 90, "presence",
      "Share of all bots online during the peak.", 0, 100, 1, "%",
      scope="base"),
    F("presence.offpeak_online", "Online off-peak", "pct", 22, "presence",
      "Share online at the quietest point of the day.", 0, 100, 1, "%",
      scope="base"),
    F("presence.ramp_hours", "Ramp / fall-off", "float", 3.0, "presence",
      "How many hours the rise into and fall out of the peak takes.",
      0, 12, 0.25, "h"),
    F("presence.weekend_boost", "Weekend boost", "pct", 12, "presence",
      "Extra online share on Saturdays and Sundays.", -50, 100, 1, "%"),
    F("presence.offline_hours", "Offline for", "range", [1, 48], "presence",
      "How long a bot stays offline. Each bot's stint is drawn from this "
      "window; the peak curve decides where inside it they come back.",
      0.1, 240, 0.1, "h", scope="per-bot"),
    F("presence.session_hours", "Online session", "range", [0.5, 5],
      "presence", "How long a bot stays online once it logs in.", 0.05, 48,
      0.05, "h", scope="per-bot"),
    F("presence.online_delay_minutes", "Online delay", "range", [1, 4],
      "presence", "After coming online a bot waits this long before it joins "
      "a world or answers anybody.", 0, 60, 0.5, "min", scope="per-bot"),
    F("presence.max_changes_per_minute", "Log-in/out smoothing", "int", 3000,
      "presence", "Most bots allowed to change online state in one minute.",
      10, 200000, 10, "/min"),

    # ------------------------------------------------------------- worlds
    F("worlds.enabled", "Bots join worlds", "bool", True, "worlds",
      "Online bots queue for worlds and appear in their player counts.",
      toggle=True),
    F("worlds.ingame_share", "In a world", "pct", 64, "worlds",
      "Share of online bots in a world at any moment; each bot's appetite "
      "for games scales its own odds.", 0, 100, 1, "%", scope="base"),
    F("worlds.session_minutes", "Game session", "range", [10, 70], "worlds",
      "How long a bot stays in one world before leaving.", 1, 600, 1, "min",
      scope="per-bot"),
    F("worlds.break_minutes", "Break between games", "range", [2, 18],
      "worlds", "", 0, 240, 1, "min", scope="per-bot"),
    F("worlds.world_weights", "World popularity", "weights",
      {w: 1.0 for w in WORLD_IDS}, "worlds",
      "Multiplies every bot's own preference for each world.", 0, 5, 0.1,
      options=[[w, WORLD_LABELS[w]] for w in WORLD_IDS]),
    F("worlds.fill", "Instance fill", "range", [45, 92], "worlds",
      "How full bots let an instance get before they start another one.",
      10, 100, 1, "%"),
    F("worlds.follow_friends", "Join a friend's game", "pct", 55, "worlds",
      "Chance a bot joins the instance a friend is in instead of choosing "
      "by itself.", 0, 100, 1, "%", scope="base"),
    F("worlds.human_pull", "Pull towards real players", "float", 1.5,
      "worlds", "How strongly bots prefer instances that have a real player "
      "in them (1 = no preference).", 0, 6, 0.1, "x"),
    F("worlds.max_live_bots", "Bots per live instance", "int", 20, "worlds",
      "Most bots allowed in an instance a real player is in -- the ones that "
      "actually run on the game host.", 0, 24, 1, "bots"),
    F("worlds.sleep_grace_seconds", "Sleep after", "int", 45, "worlds",
      "Once the last real player leaves, the instance keeps running this long "
      "and then goes to sleep: its bots stay in the player counts, it stops "
      "costing anything.", 5, 900, 5, "s"),
    F("worlds.progress_on_wake", "Wake mid-round", "bool", True, "worlds",
      "A sleeping instance a player walks into is mid-round: scores, "
      "captures, cart progress and restaurants already built, bots spread "
      "over the map."),
    F("worlds.sim_pace", "Sleeping round pace", "float", 1.0, "worlds",
      "Speed of the objective in sleeping instances (captures, cart pushes, "
      "builds) relative to a live round.", 0.1, 5, 0.1, "x"),
    F("worlds.warm_start", "Warm start", "bool", True, "worlds",
      "After a restart, bots are already online and mid-game instead of "
      "logging in from zero."),

    # ------------------------------------------------------------- ingame
    F("ingame.enabled", "Bots play alongside real players", "bool", True,
      "ingame", "Off keeps real players and bots in separate instances.",
      toggle=True),
    F("ingame.skill", "Skill", "range", [0.2, 0.85], "ingame",
      "Aim, awareness and decision quality; tryhards and veterans sit at the "
      "top of the range.", 0, 1, 0.01, scope="per-bot"),
    F("ingame.reaction_ms", "Reaction time", "range", [220, 700], "ingame",
      "", 60, 3000, 10, "ms", scope="per-bot"),
    F("ingame.aim_error", "Aim error", "range", [1.2, 7.5], "ingame",
      "Degrees of aim wobble; tightens the longer a bot tracks a target.",
      0, 25, 0.1, "°", scope="per-bot"),
    F("ingame.objective_focus", "Objective focus", "pct", 72, "ingame",
      "Most bots play the objective; their tags raise or lower this.",
      0, 100, 1, "%", scope="base"),
    F("ingame.tangent_per_minute", "Tangents", "pct", 9, "ingame",
      "Chance per minute a bot drifts off on a tangent (exploring, messing "
      "about, following someone).", 0, 100, 1, "%/min", scope="base"),
    F("ingame.tilt_deaths", "Tilt after", "int", 4, "ingame",
      "Deaths inside two minutes before a bot tilts: revenge-hunts its "
      "killer, rage-rushes or wanders off.", 1, 30, 1, "deaths",
      scope="base"),
    F("ingame.revenge", "Revenge chance", "pct", 40, "ingame",
      "Chance a bot goes after whoever just killed it.", 0, 100, 1, "%",
      scope="base"),
    F("ingame.afk_per_minute", "AFK moments", "pct", 3, "ingame",
      "Chance per minute a bot stands still for a bit.", 0, 100, 0.5,
      "%/min", scope="base"),
    F("ingame.anything_floor", "Anything can happen", "pct", 3, "ingame",
      "Every bot, however focused, keeps at least this chance of doing any "
      "behaviour it has.", 0, 50, 0.5, "%"),
    F("ingame.greet", "Say hello", "pct", 35, "ingame",
      "Chance a bot greets a real player who joins.", 0, 100, 1, "%",
      scope="base"),
    F("ingame.near_radius", "Full-detail radius", "int", 170, "ingame",
      "Bots within this distance of a real player (or in view) run at full "
      "detail; the rest think less often and settle far-off fights by "
      "odds.", 30, 900, 10, "units"),
    F("ingame.think_hz", "Think rate (near)", "float", 6.0, "ingame", "",
      1, 20, 0.5, "Hz"),
    F("ingame.far_think_hz", "Think rate (far)", "float", 1.2, "ingame", "",
      0.1, 10, 0.1, "Hz"),

    # ------------------------------------------------------------ friends
    F("friends.enabled", "Bots add friends", "bool", True, "friends",
      "Bots send friend requests to associated bots and confirm the ones "
      "they receive.", toggle=True),
    F("friends.depth", "Friend depth", "int", 2, "friends",
      "Tags two bots must share before either will send a friend request.",
      0, 10, 1, "tags"),
    F("friends.max_friends", "Friends per bot", "range", [3, 45], "friends",
      "Each bot aims for a friend count inside this range; social butterflies "
      "at the top, loners at the bottom.", 0, 200, 1, "friends",
      scope="per-bot"),
    F("friends.requests_per_hour", "Request budget", "int", 900, "friends",
      "Most friend requests all bots together send in an hour.", 0, 200000,
      10, "/h"),
    F("friends.accept_chance", "Accept rate (bots)", "pct", 85, "friends",
      "Chance a bot confirms another bot's request; more shared tags raise "
      "it, pickier personas lower it.", 0, 100, 1, "%", scope="base"),
    F("friends.accept_humans", "Confirm real players", "bool", True,
      "friends", "Bots confirm friend requests from real players."),
    F("friends.accept_humans_chance", "Accept rate (players)", "pct", 80,
      "friends", "", 0, 100, 1, "%", scope="base"),
    F("friends.befriend_humans", "Befriend real players", "bool", False,
      "friends", "Bots may send a request to a real player they just played "
      "a round with."),
    F("friends.follow_chance", "Follow too", "pct", 35, "friends",
      "Chance a bot also follows a new friend.", 0, 100, 1, "%"),

    # ------------------------------------------------------------ chatter
    F("chatter.enabled", "Chatter", "bool", False, "chatter",
      "Bots comment in the comment sections of bots they are closely "
      "associated with.", toggle=True),
    F("chatter.interval_hours", "Time between comments", "range", [1, 5],
      "chatter", "Each bot leaves a comment once every so often inside this "
      "range while online.", 0.05, 168, 0.05, "h", scope="per-bot"),
    F("chatter.min_shared_tags", "Close association", "int", 2, "chatter",
      "Tags a bot must share with a profile's owner to comment there "
      "(friends always count).", 0, 10, 1, "tags"),
    F("chatter.friends_only", "Friends' walls only", "bool", False, "chatter",
      ""),
    F("chatter.reply_to_humans", "Reply to real players", "bool", True,
      "chatter", "When a real player comments on a bot's wall, the bot "
      "answers there once it is online."),
    F("chatter.reply_delay_minutes", "Reply delay", "range", [2, 25],
      "chatter", "", 0, 1440, 1, "min", scope="per-bot"),
    F("chatter.context_comments", "Comments of context", "int", 14,
      "chatter", "How many of a wall's latest comments the model reads before "
      "writing.", 1, 60, 1),
    F("chatter.max_per_minute", "Comment budget", "int", 12, "chatter",
      "Most comments all bots together write in a minute (keeps the model "
      "free for chat and DMs).", 0, 600, 1, "/min"),
    F("chatter.posts", "Status posts", "bool", True, "chatter",
      "Bots post a status update now and then."),
    F("chatter.post_interval_hours", "Time between posts", "range", [8, 72],
      "chatter", "", 0.5, 720, 0.5, "h", scope="per-bot"),
    F("chatter.likes", "Likes", "bool", True, "chatter",
      "Bots like posts from friends and associated bots."),

    # ------------------------------------------------------------ messages
    F("messages.dm_enabled", "Bots answer DMs", "bool", True, "messages",
      "A bot answers a private message once it is online and past its online "
      "delay.", toggle=True),
    F("messages.dm_delay_seconds", "Reading and typing time", "range",
      [20, 180], "messages", "Added before a reply goes out, on top of any "
      "time spent offline.", 0, 3600, 5, "s", scope="per-bot"),
    F("messages.dm_context_messages", "Messages of context", "int", 24,
      "messages", "", 2, 200, 1),
    F("messages.dm_initiate", "Bots start conversations", "bool", False,
      "messages", "Bots occasionally message a real player they are friends "
      "with."),
    F("messages.ingame_chat", "In-game chat", "bool", True, "messages",
      "Bots talk in a round's chat when a real player is there to read it.",
      toggle=True),
    F("messages.chat_reply_chance", "Answer players", "pct", 60, "messages",
      "Chance a bot answers when a real player talks (much higher when they "
      "use its name).", 0, 100, 1, "%", scope="base"),
    F("messages.quick_reactions", "Quick reactions", "bool", True, "messages",
      "Short reactions (gg, nice, rip, lol) are typed without asking the "
      "model, so a round stays lively however busy it is."),
    F("messages.chat_per_minute", "Chat budget per instance", "int", 8,
      "messages", "Most bot chat lines in one instance per minute.", 0, 120,
      1, "/min"),
    F("messages.chat_context_lines", "Chat lines of context", "int", 30,
      "messages", "", 2, 200, 1),
    F("messages.typing_cps", "Typing speed", "float", 7.0, "messages",
      "Characters a second; a reply appears after it would have been typed.",
      1, 40, 0.5, "chars/s"),

    # ------------------------------------------------------------ modifiers
    F("modifiers.dm_enabled", "Conversation momentum (DMs)", "bool", True,
      "modifiers", "When somebody keeps trading messages with a bot, it answers "
      "sooner; once the conversation goes quiet the effect fades away.",
      toggle=True),
    F("modifiers.dm_min_turns", "Back-and-forths before it starts", "int", 2,
      "modifiers", "One back-and-forth is the bot answering and the person "
      "answering back.", 1, 20, 1, "turns"),
    F("modifiers.dm_speedup", "Replies this much sooner", "pct", 30,
      "modifiers", "Cut from the bot's usual reading and typing time once the "
      "momentum kicks in.", 0, 95, 1, "%"),
    F("modifiers.dm_step", "More for each further turn", "pct", 10,
      "modifiers", "Added on top for every back-and-forth after that.", 0, 50,
      1, "%"),
    F("modifiers.dm_max", "Never more than", "pct", 70, "modifiers",
      "The ceiling on how much sooner a bot can answer.", 0, 95, 1, "%"),
    F("modifiers.dm_decay_seconds", "Decay time (DMs)", "int", 60,
      "modifiers", "How long a pause kills the momentum. It fades gradually: "
      "an answer straight back keeps all of it, one half this long later "
      "keeps half, and after this long it is gone and the count starts again.",
      5, 3600, 5, "s"),
    F("modifiers.dm_stay_online", "Stay online mid-conversation", "bool", True,
      "modifiers", "A bot about to log off stays on a little longer while a "
      "conversation still has momentum."),
    F("modifiers.chat_enabled", "Chat heat (in-game)", "bool", True,
      "modifiers", "When a real player keeps talking in a round, bots are more "
      "likely to answer; once they go quiet it fades back to normal.",
      toggle=True),
    F("modifiers.chat_boost", "Boost per recent message", "pct", 35,
      "modifiers", "Extra reply chance for each of the player's recent lines "
      "before the one being answered (each fades out over the decay time).",
      0, 300, 5, "%"),
    F("modifiers.chat_max", "Most extra chance", "pct", 150, "modifiers",
      "The ceiling on the boost: 150% means up to two and a half times the "
      "usual chance.", 0, 500, 5, "%"),
    F("modifiers.chat_decay_seconds", "Decay time (in-game)", "int", 60,
      "modifiers", "A line stops adding heat this long after it was said, "
      "fading gradually until then.", 5, 600, 5, "s"),
    F("modifiers.chat_partner", "Keep talking to the same bot", "pct", 60,
      "modifiers", "Chance the bot a player was just talking with is the one "
      "that answers their next line (fades with the heat).", 0, 100, 1, "%"),
    F("modifiers.chat_second_voice", "Second voice", "pct", 20, "modifiers",
      "Chance another bot chimes in as well when the chat is hot.", 0, 100, 1,
      "%"),
    F("modifiers.bots_talk", "Bots answer each other", "bool", True,
      "modifiers", "A bot's line in a round can draw a reply from another bot "
      "there, so a round's chat is a conversation, not a list of answers to "
      "the player.", toggle=True),
    F("modifiers.bot_reply_chance", "Reply to another bot", "pct", 22,
      "modifiers", "Chance a bot's line gets an answer from another bot; much "
      "higher when it named that bot.", 0, 100, 1, "%", scope="base"),
    F("modifiers.bot_chain_max", "Longest bot-only exchange", "int", 3,
      "modifiers", "After this many bot lines in a row with no real player "
      "speaking, the bots let it drop.", 0, 12, 1, "lines"),
    F("modifiers.bot_chain_fade", "Each further bot reply", "pct", 50,
      "modifiers", "How much less likely each further reply in a bot-only "
      "exchange is.", 0, 100, 5, "% less"),

    # --------------------------------------------------------------- speech
    F("speech.enabled", "Speech events", "bool", True, "speech",
      "Things that happen in a round -- a stolen flag, a capture, a "
      "checkpoint, a finished restaurant -- make the bots there more likely "
      "to say something about it, told what happened from their own side.",
      toggle=True),
    F("speech.chances", "Chance per event", "chances",
      dict(speech_catalogue.DEFAULT_CHANCES), "speech",
      "The chance that someone in the round reacts in chat when it happens. "
      "0 turns an event off.", 0, 100, 1, "%", options="events"),
    F("speech.max_voices", "Most bots reacting to one event", "int", 2,
      "speech", "", 1, 6, 1, "bots"),
    F("speech.follow_chance", "Another bot joins in", "pct", 35, "speech",
      "Chance each further bot also reacts, up to the limit above.", 0, 100,
      1, "%"),
    F("speech.cooldown_seconds", "Quiet time per kind of event", "int", 20,
      "speech", "After bots react to an event, the same kind of event in that "
      "round cannot set them off again for this long.", 0, 600, 5, "s"),
    F("speech.buzz_seconds", "Buzz afterwards", "int", 45, "speech",
      "For this long after an event the round is buzzing: bots are more likely "
      "to answer each other and the players, fading as it goes.", 0, 600, 5,
      "s"),
    F("speech.buzz_boost", "How much more likely during the buzz", "pct", 60,
      "speech", "", 0, 300, 5, "%"),
    F("speech.canned_fallback", "Canned lines when the model is down", "bool",
      True, "speech", "Short stock reactions (\"they have our flag\", \"nice "
      "cap\") stand in when the language model is unavailable."),

    # ----------------------------------------------------------------- llm
    F("llm.enabled", "Use the language model", "bool", True, "llm",
      "Every word a bot writes comes from the endpoint below.", toggle=True),
    F("llm.base_url", "Endpoint", "text", "http://10.0.0.139:5000/v1", "llm",
      "Any OpenAI / LM Studio compatible base URL (ending in /v1)."),
    F("llm.api_key", "API key", "secret", "", "llm",
      "Only if the server asks for one."),
    F("llm.model", "Model", "text", "", "llm",
      "Blank uses whichever model the server has loaded."),
    F("llm.mode", "Prompt format", "select", "auto", "llm",
      "Chat lets the server apply the model's chat template. Completion "
      "applies the template pulled from the server here and sends raw text.",
      options=[["auto", "Auto (chat, completion as fallback)"],
               ["chat", "Chat completions"],
               ["completion", "Completion with the pulled chat template"]]),
    F("llm.context_limit", "Context limit", "int", 16000, "llm",
      "Tokens of prompt plus reply. Logs are culled oldest-first to fit.",
      256, 2000000, 256, "tokens"),
    F("llm.respect_server_context", "Never exceed the server's context",
      "bool", True, "llm", "Use the smaller of this limit and the context "
      "the server reports."),
    F("llm.concurrency", "Parallel requests", "int", 2, "llm", "", 1, 32, 1),
    F("llm.requests_per_minute", "Request budget", "int", 90, "llm",
      "All bots together.", 1, 20000, 1, "/min"),
    F("llm.timeout_seconds", "Timeout", "int", 90, "llm", "", 5, 900, 5,
      "s"),
    F("llm.max_tokens_chat", "Reply length: in-game chat", "int", 48, "llm",
      "", 8, 4096, 8, "tokens"),
    F("llm.max_tokens_comment", "Reply length: comments", "int", 96, "llm",
      "", 8, 4096, 8, "tokens"),
    F("llm.max_tokens_dm", "Reply length: DMs", "int", 200, "llm", "", 8,
      4096, 8, "tokens"),
    F("llm.max_tokens_post", "Reply length: posts", "int", 96, "llm", "", 8,
      4096, 8, "tokens"),
    F("llm.max_tokens_names", "Reply length: usernames", "int", 400, "llm",
      "", 32, 8192, 16, "tokens"),
    F("llm.max_tokens_profile", "Reply length: profiles", "int", 900, "llm",
      "", 32, 8192, 16, "tokens"),
    F("llm.temperature", "Temperature", "float", None, "llm",
      "Blank uses the value pulled from the server.", 0, 3, 0.05,
      nullable=True),
    F("llm.top_p", "Top-p", "float", None, "llm", "", 0, 1, 0.01,
      nullable=True),
    F("llm.top_k", "Top-k", "int", None, "llm", "", 0, 1000, 1,
      nullable=True),
    F("llm.min_p", "Min-p", "float", None, "llm", "", 0, 1, 0.01,
      nullable=True),
    F("llm.repeat_penalty", "Repeat penalty", "float", None, "llm", "", 0.5,
      2.5, 0.01, nullable=True),
    F("llm.presence_penalty", "Presence penalty", "float", None, "llm", "",
      -2, 2, 0.05, nullable=True),
    F("llm.frequency_penalty", "Frequency penalty", "float", None, "llm", "",
      -2, 2, 0.05, nullable=True),
    F("llm.stop", "Extra stop strings", "list", [], "llm",
      "Added to the stop strings the server reports.", rows=3),
    F("llm.strip_reasoning", "Strip reasoning", "bool", True, "llm",
      "Remove <think> blocks that reasoning models put before an answer."),

    # ------------------------------------------------------------- prompts
    F("prompts.comment", "Comment sections", "textarea", PROMPT_COMMENT,
      "prompts", "{target} is the profile's owner.", rows=10),
    F("prompts.chat", "In-game chat", "textarea", PROMPT_CHAT, "prompts",
      "{world} is the world's name.", rows=9),
    F("prompts.dm", "Direct messages", "textarea", PROMPT_DM, "prompts",
      "{target} is who the bot is talking to.", rows=8),
    F("prompts.post", "Status posts", "textarea", PROMPT_POST, "prompts",
      "", rows=7),
    F("prompts.names", "Username generation", "textarea", PROMPT_NAMES,
      "prompts", "{examples} is replaced by the example usernames.", rows=12),
    F("prompts.profile", "Profile generation", "textarea", PROMPT_PROFILE,
      "prompts", "", rows=9),
    F("prompts.persona", "Persona block", "textarea", PERSONA_TEMPLATE,
      "prompts", "Goes under every system message. {name} {tags} {traits} "
      "{style} {worlds} {joined} {blurb}", rows=8),
]

FIELDS_BY_KEY: Dict[str, Field] = {f.key: f for f in FIELDS}

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

_lock = threading.RLock()
_cache: Optional[Dict[str, Any]] = None
_version = 0
_listeners: List[Callable[[Dict[str, Any]], None]] = []


# ---------------------------------------------------------------- validation
def _num(field: Field, value: Any) -> Optional[float]:
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    if field.min is not None:
        number = max(float(field.min), number)
    if field.max is not None:
        number = min(float(field.max), number)
    return number


def clean(field: Field, value: Any) -> Any:
    """Coerce one posted value into what the field holds, or its default."""
    kind = field.kind
    if kind == "bool":
        if isinstance(value, str):
            return value.strip().lower() in ("1", "true", "on", "yes")
        return bool(value)
    if kind in ("int", "float", "pct"):
        number = _num(field, value)
        if number is None:
            return None if field.nullable else field.default
        return int(round(number)) if kind == "int" else round(number, 4)
    if kind in ("range", "hours"):
        if not isinstance(value, (list, tuple)) or len(value) != 2:
            return list(field.default)
        lo, hi = _num(field, value[0]), _num(field, value[1])
        if lo is None or hi is None:
            return list(field.default)
        if kind == "range" and lo > hi:
            lo, hi = hi, lo
        step = field.step or 0
        if step and step >= 1:
            lo, hi = int(round(lo)), int(round(hi))
        return [round(lo, 4), round(hi, 4)]
    if kind == "daterange":
        if not isinstance(value, (list, tuple)) or len(value) != 2:
            return list(field.default)
        out = []
        for part in value:
            part = str(part or "").strip()
            out.append(part if _DATE_RE.match(part) else "")
        if not out[0]:
            out[0] = field.default[0]
        if out[1] and out[1] < out[0]:
            out = [out[1], out[0]]
        return out
    if kind in ("text", "secret"):
        return str(value if value is not None else "").strip()[:500]
    if kind == "textarea":
        text = str(value if value is not None else "")
        return text.replace("\r\n", "\n")[:12000] or field.default
    if kind == "list":
        if isinstance(value, str):
            value = value.splitlines()
        if not isinstance(value, (list, tuple)):
            return list(field.default)
        items = [str(v).strip()[:120] for v in value][:2000]
        if field.key == "creation.locations":
            return items          # blank lines mean "no location" here
        return [v for v in items if v]
    if kind == "select":
        allowed = [o[0] for o in (field.options or [])]
        return value if value in allowed else field.default
    if kind == "chances":
        if not isinstance(value, dict):
            return dict(field.default)
        out_c = dict(field.default)
        for key, pct in value.items():
            if key not in out_c:
                continue
            number = _num(field, pct)
            if number is not None:
                out_c[key] = int(round(number))
        return out_c
    if kind == "weights":
        if not isinstance(value, dict):
            return dict(field.default)
        keys = (_tag_options() if field.options == "tags"
                else [o[0] for o in (field.options or [])])
        out: Dict[str, float] = {}
        for key, weight in value.items():
            if key not in keys:
                continue
            number = _num(field, weight)
            if number is not None:
                out[key] = round(number, 3)
        return out
    return field.default


# ------------------------------------------------------------------ storage
def _stored() -> Dict[str, Any]:
    raw = db.get_meta(META_KEY, "{}") or "{}"
    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        data = {}
    return data if isinstance(data, dict) else {}


def load() -> Dict[str, Any]:
    """Every setting, merged over its default.  Cached until a save."""
    global _cache
    with _lock:
        if _cache is not None:
            return _cache
        stored = _stored()
        merged: Dict[str, Any] = {}
        for field in FIELDS:
            if field.key in stored:
                merged[field.key] = clean(field, stored[field.key])
            else:
                merged[field.key] = (json.loads(json.dumps(field.default))
                                     if isinstance(field.default, (list, dict))
                                     else field.default)
        _cache = merged
        _apply_side_effects(merged)
        return merged


def get(key: str, fallback: Any = None) -> Any:
    value = load().get(key, fallback)
    return fallback if value is None and fallback is not None else value


def version() -> int:
    return _version


def save(changes: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and store a set of changes; returns the cleaned values."""
    global _cache, _version
    applied: Dict[str, Any] = {}
    with _lock:
        stored = _stored()
        for key, value in (changes or {}).items():
            field = FIELDS_BY_KEY.get(key)
            if field is None:
                continue
            if field.kind == "secret" and str(value or "").strip("•") == "" \
                    and str(value or ""):
                continue          # the masked placeholder came back unchanged
            cleaned = clean(field, value)
            applied[key] = cleaned
            if cleaned == field.default:
                stored.pop(key, None)
            else:
                stored[key] = cleaned
        db.set_meta(META_KEY, json.dumps(stored, separators=(",", ":")))
        _cache = None
        _version += 1
        merged = load()
    for listener in list(_listeners):
        try:
            listener(merged)
        except Exception:
            pass
    return applied


def reset(section: str) -> None:
    with _lock:
        stored = _stored()
    keys = [f.key for f in FIELDS if f.section == section]
    save({key: FIELDS_BY_KEY[key].default for key in keys if key in stored})


def on_change(callback: Callable[[Dict[str, Any]], None]) -> None:
    _listeners.append(callback)


def _apply_side_effects(merged: Dict[str, Any]) -> None:
    try:
        from . import personas
        personas.set_custom_tags(merged.get("personas.custom_tags") or [])
    except Exception:
        pass


def schema() -> Dict[str, Any]:
    """What the dashboard draws its forms from."""
    from . import personas
    fields = []
    for field in FIELDS:
        entry = field.describe()
        if field.options == "tags":
            entry["options"] = [[t["id"], t["label"], t["group"]]
                                for t in personas.all_tags()]
        elif field.options == "events":
            entry["options"] = speech_catalogue.options()
        fields.append(entry)
    return {"sections": [{"id": s, "label": l, "blurb": b}
                         for s, l, b in SECTIONS],
            "fields": fields}


def public_values() -> Dict[str, Any]:
    """The settings as the dashboard may see them (the key stays hidden)."""
    values = dict(load())
    if values.get("llm.api_key"):
        values["llm.api_key"] = "•" * 8
    return values


def ingame_section() -> Dict[str, Any]:
    """The part of the settings the game hosts need, as a compact dict."""
    values = load()
    out = {k.split(".", 1)[1]: v for k, v in values.items()
           if k.startswith("ingame.")}
    for key in ("messages.ingame_chat", "messages.quick_reactions",
                "messages.chat_per_minute", "messages.typing_cps",
                "messages.chat_reply_chance", "worlds.sleep_grace_seconds",
                "worlds.max_live_bots", "system.enabled", "speech.enabled"):
        out[key.replace(".", "_")] = values.get(key)
    out["v"] = _version
    out["at"] = int(time.time())
    return out


def date_to_ts(text: str, end: bool = False) -> int:
    """``YYYY-MM-DD`` as a local timestamp (blank = now)."""
    if not text:
        return int(time.time())
    try:
        parsed = time.strptime(text, "%Y-%m-%d")
    except ValueError:
        return int(time.time())
    stamp = int(time.mktime(parsed))
    return stamp + (86399 if end else 0)
