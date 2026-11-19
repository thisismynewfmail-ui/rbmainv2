"""Safe Chat: the personal-information and outside-contact shield.

Pure functions with no database and no site imports, because two kinds of
process run it: the web server, over private messages, profile comments and
the about-me box, and every game host, over in-game chat (a host imports
this module in its own process).

``scan(text)`` returns a :class:`Verdict` saying what to do with a line that
involves a child account:

    allow   nothing found
    mask    deliver it with the strong language blanked out
    flag    deliver it, and tell the parent (words that can be a sign of
            distress; a question about age)
    block   do not deliver it, and tell the parent: a phone number, an email
            address, a home address, a link, an invitation to talk on another
            app, a request to meet up / keep secrets / send photos, bullying

What it is honest about: this is a pattern filter, not a person.  It knows the
common ways children are asked for -- and give away -- the details that
matter (digits written as words, "name at gmail dot com", "s n a p",
leetspeak), and it errs on the side of blocking in a children's chat.  It
will not catch everything, which is why the dashboard also shows parents the
messages themselves.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Iterable, List, NamedTuple, Optional, Tuple

MASK = "•••"

# --------------------------------------------------------------- the verdict

ACTION_RANK = {"allow": 0, "mask": 1, "flag": 2, "block": 3}
SEVERITY_RANK = {"none": 0, "info": 1, "warn": 2, "high": 3}

# category -> (action, severity, what a parent reads)
CATEGORIES = {
    "phone": ("block", "warn", "a phone number"),
    "email": ("block", "warn", "an email address"),
    "address": ("block", "warn", "a home address"),
    "contact": ("block", "warn", "an invitation to talk on another app"),
    "link": ("block", "warn", "a web link"),
    "meetup": ("block", "high", "a request to meet up or for private details"),
    "secret": ("block", "high", "a request to keep secrets from parents"),
    "photos": ("block", "high", "a request for photos"),
    "bullying": ("block", "high", "bullying language"),
    "wellbeing": ("flag", "warn", "words that can be a sign of distress"),
    "age": ("flag", "info", "a question about age"),
    "language": ("mask", "none", "strong language"),
}


class Verdict(NamedTuple):
    action: str                 # allow | mask | flag | block
    severity: str               # none | info | warn | high
    categories: Tuple[str, ...]
    masked: str                 # the text with every hit blanked

    @property
    def blocked(self) -> bool:
        return self.action == "block"

    @property
    def flagged(self) -> bool:
        return self.action in ("flag", "block")

    @property
    def changed(self) -> bool:
        return self.action != "allow"

    def describe(self) -> str:
        """``a phone number and a web link`` -- for the parent's alert."""
        labels = [CATEGORIES[c][2] for c in self.categories if c in CATEGORIES
                  and CATEGORIES[c][0] != "mask"]
        if not labels:
            return "nothing"
        if len(labels) == 1:
            return labels[0]
        return ", ".join(labels[:-1]) + " and " + labels[-1]


CLEAN = Verdict("allow", "none", (), "")


def kid_notice(verdict: Verdict) -> str:
    """What the child is told when their own line is stopped."""
    cats = set(verdict.categories)
    if cats & {"meetup", "secret", "photos"}:
        return ("That wasn't sent. Chats about meeting up, secrets or photos "
                "stay off NoogBlock -- that's how everybody stays safe.")
    if "bullying" in cats:
        return "That wasn't sent. Be kind -- everybody here is somebody's friend."
    if "link" in cats:
        return "That wasn't sent. Links can't be shared in chat."
    return ("That wasn't sent. It looked like personal info (a phone number, "
            "address or email) or an invite to another app. Keep that private!")


# ------------------------------------------------------------- normalising

_ZERO_WIDTH = dict.fromkeys(map(ord, "​‌‍‎‏⁠﻿­"))
_LEET = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s",
                       "7": "t", "@": "a", "$": "s", "!": "i", "|": "l"})
_SPACED = re.compile(r"\b(?:[a-z0-9][\s._\-*]){2,}[a-z0-9]\b")


def _base(text: str) -> str:
    text = unicodedata.normalize("NFKC", str(text or ""))
    return text.translate(_ZERO_WIDTH)


def _squash_spaced(text: str) -> str:
    """``s n a p c h a t`` and ``d.i.s.c.o.r.d`` back into words."""
    return _SPACED.sub(lambda m: re.sub(r"[\s._\-*]", "", m.group(0)), text)


def _words(text: str) -> str:
    """A lower-cased copy for phrase matching: spaced-out letters joined, runs
    of the same letter shortened (``snaaaap``), leetspeak undone."""
    low = _squash_spaced(_base(text).lower())
    low = re.sub(r"([a-z])\1{2,}", r"\1", low)
    return low


def _leet(text: str) -> str:
    return _words(text).translate(_LEET)


# ------------------------------------------------------------------ phones

_DIGIT_RUN = re.compile(r"(?<![\w])\+?[\(\[]?\d[\d\s\-\.\(\)\[\]/]{4,}\d(?![\w])")
_NUMBER_WORDS = {
    "zero": "0", "oh": "0", "o": "0", "one": "1", "won": "1", "two": "2",
    "to": None, "too": None, "three": "3", "four": "4", "for": None,
    "five": "5", "six": "6", "seven": "7", "eight": "8", "ate": None,
    "nine": "9", "niner": "9",
}


def _phone_like(digits: str) -> bool:
    if not 7 <= len(digits) <= 15:
        return False
    # a big round number ("1000000 noogets") is a boast, not a phone, and
    # neither is one digit held down
    return not (re.search(r"0{5,}$", digits) or len(set(digits)) == 1)


def _phone_spans(text: str) -> List[Tuple[int, int]]:
    spans = []
    for m in _DIGIT_RUN.finditer(text):
        if _phone_like(re.sub(r"\D", "", m.group(0))):
            spans.append(m.span())
    # digits written out as words: "five five five one two three four"
    tokens = list(re.finditer(r"[a-z]+|\d", text.lower()))
    run: List[re.Match] = []
    count = 0

    def close() -> None:
        if count >= 7 and run:
            digits = "".join(t.group(0) if t.group(0).isdigit()
                             else _NUMBER_WORDS[t.group(0)] for t in run)
            if _phone_like(digits):
                spans.append((run[0].start(), run[-1].end()))

    for tok in tokens:
        word = tok.group(0)
        value = word if word.isdigit() else _NUMBER_WORDS.get(word, "")
        if value:
            if run and tok.start() - run[-1].end() > 3:
                close()
                run, count = [], 0
            run.append(tok)
            count += 1
            continue
        close()
        run, count = [], 0
    close()
    return spans


# ------------------------------------------------------------------ emails

_EMAIL = re.compile(
    r"[a-z0-9._%+\-]+\s*@\s*[a-z0-9\-]+(?:\s*\.\s*[a-z]{2,})+", re.I)
_EMAIL_SPOKEN = re.compile(
    r"\b[a-z0-9._%+\-]{2,}\s*(?:\(at\)|\[at\]|\{at\}|\bat\b)\s*[a-z0-9\-]{2,}"
    r"\s*(?:\.|\(dot\)|\[dot\]|\bdot\b)\s*(?:com|net|org|edu|co|uk|us|ca|au|io|me|info)\b",
    re.I)
_MAIL_PROVIDERS = re.compile(
    r"\b(?:g\s?mail|hotmail|ymail|icloud|yahoo\s?mail|outlook\.com|aol\s?mail|"
    r"proton\s?mail|live\.com)\b", re.I)

# --------------------------------------------------------------- addresses

_STREET_PLAIN = (r"street|avenue|ave|road|rd|lane|ln|drive|boulevard|blvd|terrace|"
                 r"highway|hwy|parkway|pkwy|crescent|cres")
_STREET_AMBIGUOUS = r"st|dr|court|ct|way|place|pl|circle|cir|close|square|sq|trail|trl|grove|row"
_NOT_A_STREET_NAME = (r"(?!(?:in|a|an|the|of|to|my|your|ur|on|at|for|and|or|more|"
                      r"kills?|wins?|times?|points?|games?|rounds?|people|players?|"
                      r"waves?|levels?|coins?|noogets?|hits?|shots?|goals?)\b)")
_STREET = re.compile(
    r"\b\d{1,6}[a-z]?\s+(?:[a-z']+\s+){0,3}(?:%s)\b\.?|"
    r"\b\d{2,6}[a-z]?\s+(?:%s[a-z']+\s+){1,3}(?:%s)\b\.?"
    % (_STREET_PLAIN, _NOT_A_STREET_NAME, _STREET_AMBIGUOUS), re.I)
_ADDRESS_TALK = re.compile(
    r"\b(?:(?:my|our)\s+(?:home\s+|house\s+)?address|address\s+is|i\s+live\s+(?:at|on)\s+\w+|"
    r"zip\s*code|post\s*code|apartment\s*#?\d+|apt\.?\s*#?\d+)\b", re.I)

# ------------------------------------------------------- outside contact

_APPS = (r"snap\s?chat|snap|sc|insta\s?gram|insta|ig|tik\s?tok|tt|discord|dc|"
         r"whats\s?app|wa|kik|telegram|tele|face\s?book|fb|messenger|skype|zoom|"
         r"face\s?time|we\s?chat|line\s?app|twitter|threads|you\s?tube|yt|twitch|"
         r"xbox|psn|play\s?station|switch\s?code|friend\s?code|steam|e-?mail|"
         r"text|phone|cell|mobile|imessage|google\s?chat|hangouts|reddit|pinterest|"
         r"bereal|omegle|roblox|minecraft|fortnite")
_INVITE = re.compile(
    r"\b(?:add|follow|dm|pm|message|msg|text|txt|call|ring|find|friend|hmu|hit\s+me\s+up|"
    r"join|chat|talk|sub|subscribe|search|look\s+me\s+up|vc|voice\s?chat|facetime)"
    r"\s+(?:me\s+|us\s+)?(?:on|at|in|over|thru|through|@|via|to)?\s*(?:my\s+|the\s+)?(?:%s)\b" % _APPS,
    re.I)
# "my snap is ...", "my discord: ...": the social apps.  The phone, the
# consoles and the games are left out of this one, because "my phone is
# dead" and "my xbox is broken" are not anybody's contact details.
_SOCIAL = (r"snap\s?chat|snap|sc|insta\s?gram|insta|ig|tik\s?tok|tt|discord|dc|"
           r"whats\s?app|wa|kik|telegram|tele|face\s?book|fb|messenger|skype|"
           r"we\s?chat|line\s?app|twitter|threads|you\s?tube|yt|twitch|reddit|"
           r"pinterest|bereal|omegle|e-?mail")
_MY_HANDLE = re.compile(
    r"\b(?:my|ma|mah|our)\s+(?:%s)\s*(?:is|=|:|@|name|user(?:name)?|handle|tag|account|acc|id|code)\b"
    % _SOCIAL, re.I)
_MY_GAMERTAG = re.compile(
    r"\b(?:my|ma|mah|our)\s+(?:xbox|psn|play\s?station|steam|switch|nintendo|epic|roblox|minecraft|fortnite)"
    r"\s*(?:gamer\s?tag|tag|id|code|name|user(?:name)?|account|acc|friend\s?code|=|:)", re.I)
_DO_YOU_HAVE = re.compile(
    r"\b(?:do|can|have|got|r|are)\s+(?:you|u|ya)\s+(?:got\s+|have\s+|use\s+|on\s+|play\s+on\s+)?"
    r"(?:snap\s?chat|snap|insta\s?gram|insta|ig|tik\s?tok|discord|whats\s?app|kik|telegram|"
    r"face\s?book|messenger|skype|zoom|face\s?time|we\s?chat|a\s+phone|ur\s+own\s+phone|your\s+own\s+phone|"
    r"an?\s+e-?mail)\b", re.I)
_APP_HANDLE = re.compile(
    r"\b(?:snap\s?chat|snap|sc|insta\s?gram|insta|ig|tik\s?tok|discord|whats\s?app|kik|telegram|"
    r"twitter|twitch|you\s?tube|psn|xbox|steam)\s*(?::|@)\s*@?[a-z0-9._#\-]{3,}", re.I)
_NUMBER_ASK = re.compile(
    r"\b(?:your|ur|yo|my|ma|her|his)\s+(?:phone\s+|cell\s+|mobile\s+|home\s+)?"
    r"(?:number|digits|num|#|cell|mobile)(?!\s+(?:of|one|1|two|2|three|3))\b|\bphone\s*(?:number|#|num)\b|"
    r"\b(?:text|txt|facetime)\s+me\b|\bcall\s+me\s+(?:at|on)\b", re.I)
_LINK = re.compile(
    r"(?:https?://|www\.|\b[a-z0-9\-]{2,}\.(?:com|net|org|gg|io|tv|ly|me|co|app|link|xyz|site)\b"
    r"(?:/\S*)?|\b[a-z0-9\-]{2,}\s*(?:\(dot\)|\[dot\]|\sdot\s)\s*(?:com|net|org|gg|io|tv)\b|"
    r"discord\s?\.?\s?gg\s?/)", re.I)

# ------------------------------------------------ grooming and risk phrases

_MEETUP = re.compile(
    r"\b(?:meet(?:\s+up)?\s+(?:me\s+)?(?:irl|in\s+real\s+life|in\s+person|for\s+real|offline|somewhere)|"
    r"(?:come|coming)\s+(?:over\s+)?to\s+my\s+(?:house|home|place|apartment|flat|room)|"
    r"(?:can|could)\s+i\s+come\s+(?:over|to\s+your\s+house)|"
    r"where\s+(?:do|d)\s+(?:you|u|ya)\s+live|what\s+(?:city|town|street|state)\s+(?:do\s+)?(?:you|u)\s+live|"
    r"what(?:'?s|\s+is)\s+(?:your|ur)\s+(?:home\s+|house\s+)?address|"
    r"(?:what|which)\s+school\s+(?:do|d)\s+(?:you|u)|what(?:'?s|\s+is)\s+(?:your|ur)\s+school|"
    r"(?:are|r)\s+(?:you|u)\s+home\s+alone|"
    r"(?:are|r|is)\s+(?:your|ur)\s+(?:parents|mom|dad|mum|mommy|daddy)\s+(?:home|around|there|watching|awake|asleep)|"
    r"what(?:'?s|\s+is)\s+(?:your|ur)\s+(?:real|full|last)\s+name|\basl\b)", re.I)
_MEETUP_PRIVATE = re.compile(
    r"\b(?:(?:are|r)\s+(?:you|u)\s+alone|(?:is|are)\s+any(?:one|body)\s+(?:else\s+)?(?:home|there|with\s+(?:you|u)))\b",
    re.I)
_SECRET = re.compile(
    r"\b(?:(?:don'?t|dont|do\s+not|never)\s+tell\s+(?:your|ur|anyone|anybody|nobody|ur\s+mom|your\s+mom|"
    r"your\s+parents|ur\s+parents)|keep\s+(?:this|it|that)\s+(?:a\s+|our\s+)?secret|"
    r"our\s+(?:little\s+)?secret|just\s+between\s+(?:us|you\s+and\s+me|u\s+and\s+me)|"
    r"delete\s+(?:this|these|the)\s+(?:message|messages|chat|msgs?)|"
    r"(?:your|ur)\s+parents\s+(?:won'?t|wont|wouldn'?t)\s+(?:understand|know|find\s+out))\b", re.I)
_PHOTOS = re.compile(
    r"\b(?:send|show|snap|post)\s+(?:me\s+)?(?:a\s+|some\s+|your\s+|ur\s+|more\s+)?"
    r"(?:pic|pics|picture|pictures|photo|photos|selfie|selfies|nudes?|vid|video|face\s+pic)"
    r"|\bwhat\s+do\s+(?:you|u)\s+(?:really\s+)?look\s+like\s+(?:irl|in\s+real\s+life|for\s+real|in\s+person)\b"
    r"|\bturn\s+(?:on\s+)?(?:your|ur)\s+(?:cam|camera|webcam)\b", re.I)
_BULLYING = re.compile(
    r"\b(?:kys|kill\s+(?:your\s*self|ur\s*self|yo\s*self)|go\s+die|you\s+should\s+die|"
    r"u\s+should\s+die|nobody\s+(?:likes|loves|cares\s+about)\s+(?:you|u)|"
    r"everyone\s+hates\s+(?:you|u)|drink\s+bleach)\b", re.I)
_WELLBEING = re.compile(
    r"\b(?:kill\s+my\s*self|want\s+to\s+die|wanna\s+die|end\s+(?:my|it)\s+(?:life|all)|"
    r"hurt\s+my\s*self|cut\s+my\s*self|suicid\w*|self[\s-]?harm|no\s+reason\s+to\s+live|"
    r"hate\s+my\s+life|i\s+(?:hate|can'?t\s+stand)\s+myself)\b", re.I)
_AGE = re.compile(r"\b(?:how\s+old\s+(?:are|r)\s+(?:you|u|ya)|what\s+age\s+(?:are|r)\s+(?:you|u))\b", re.I)

# Strong language: blanked in a child's chat rather than stopped.  Kept short
# on purpose -- the common words, with the usual stretched spellings.
_LANGUAGE = re.compile(
    r"\b(?:f+u+c+k+\w*|f+\*+c?k\w*|fk|fuk\w*|phuck\w*|sh+i+t+\w*|bullsh+it|b+i+t+c+h+\w*|"
    r"c+u+n+t+\w*|d+i+c+k+head\w*|cock(?:s|sucker\w*)?|puss(?:y|ies)|a+s+s+h+o+l+e+\w*|"
    r"bastard\w*|slut\w*|whore\w*|wh0re|motherf\w*|mf+|stfu|wtf|"
    r"retard\w*|fag\w*|n+i+g+g+\w*)\b", re.I)


# ------------------------------------------------------------------- scan

def _spans(pattern: "re.Pattern", text: str) -> List[Tuple[int, int]]:
    return [m.span() for m in pattern.finditer(text)]


def _token_spans(pattern: "re.Pattern", text: str) -> List[Tuple[int, int]]:
    """Whole words of ``text`` that match once their leetspeak is undone
    (``sh1t``), as spans of the original text."""
    out = []
    for m in re.finditer(r"\S+", text):
        if pattern.search(_leet(m.group(0))):
            out.append(m.span())
    return out


def scan(text: str, author_is_child: bool = True,
         channel: str = "private") -> Verdict:
    """Look at one line.

    ``channel`` is ``private`` (a message, a profile comment, the about-me
    box) or ``game`` (in-game chat, where a few questions that are red
    flags in a private message -- "are you alone?" -- are everyday talk in
    a zombie game).  ``author_is_child`` only changes the wellbeing check: a
    child saying it about themselves is what a parent needs to hear.
    """
    raw = _base(text)
    if not raw.strip():
        return CLEAN
    words = _words(raw)
    leet = _leet(raw)
    hits: List[str] = []
    mask_spans: List[Tuple[int, int]] = []

    def hit(category: str, spans: Iterable[Tuple[int, int]] = ()) -> None:
        if category not in hits:
            hits.append(category)
        mask_spans.extend(spans)

    def seen(pattern: "re.Pattern") -> bool:
        return bool(pattern.search(words) or pattern.search(leet))

    phone = _phone_spans(raw)
    if phone:
        hit("phone", phone)
    for pattern in (_EMAIL, _EMAIL_SPOKEN):
        if pattern.search(raw) or pattern.search(words):
            hit("email", _spans(pattern, raw))
    if _MAIL_PROVIDERS.search(words):
        hit("email", _spans(_MAIL_PROVIDERS, raw))
    if _STREET.search(raw) or _STREET.search(words):
        hit("address", _spans(_STREET, raw))
    if _ADDRESS_TALK.search(words):
        hit("address", _spans(_ADDRESS_TALK, raw))
    if _LINK.search(raw) or _LINK.search(words):
        hit("link", _spans(_LINK, raw))
    for pattern in (_INVITE, _MY_HANDLE, _MY_GAMERTAG, _DO_YOU_HAVE, _APP_HANDLE,
                    _NUMBER_ASK):
        if seen(pattern):
            hit("contact", _spans(pattern, raw))
    risky = [("meetup", _MEETUP), ("secret", _SECRET), ("photos", _PHOTOS),
             ("bullying", _BULLYING)]
    if channel != "game":
        risky.append(("meetup", _MEETUP_PRIVATE))
    for category, pattern in risky:
        if seen(pattern):
            hit(category, _spans(pattern, raw))
    if author_is_child and _WELLBEING.search(words):
        hit("wellbeing")
    if _AGE.search(words):
        hit("age")
    language = _spans(_LANGUAGE, raw) + _token_spans(_LANGUAGE, raw)
    if language:
        hit("language", language)

    if not hits:
        return Verdict("allow", "none", (), raw)
    action = max((CATEGORIES[c][0] for c in hits), key=ACTION_RANK.__getitem__)
    severity = max((CATEGORIES[c][1] for c in hits), key=SEVERITY_RANK.__getitem__)
    return Verdict(action, severity, tuple(hits), _apply_mask(raw, mask_spans))


def _apply_mask(text: str, spans: List[Tuple[int, int]]) -> str:
    if not spans:
        return text
    merged: List[List[int]] = []
    for start, end in sorted(spans):
        if start >= end:
            continue
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    out, last = [], 0
    for start, end in merged:
        out.append(text[last:start])
        out.append(MASK)
        last = end
    out.append(text[last:])
    return re.sub(r"(?:%s\s*){2,}" % re.escape(MASK), MASK + " ", "".join(out)).strip()


def mask(text: str, channel: str = "game") -> str:
    """Just the blanked copy (for showing an incoming line to a child)."""
    return scan(text, author_is_child=False, channel=channel).masked


def excerpt(text: str, limit: int = 160) -> str:
    """A parent-safe excerpt: the masked text, trimmed to one line."""
    flat = " ".join((scan(text).masked or "").split())
    return flat if len(flat) <= limit else flat[:limit - 1].rstrip() + "…"


def username_warnings(username: str, first_name: str = "",
                      birth_year: Optional[int] = None) -> List[str]:
    """Gentle coaching for a child's username (shown during setup).

    Nothing here blocks: a parent and child choosing together get to decide.
    It only points out the things that make a username a give-away.
    """
    warnings: List[str] = []
    name = (username or "").lower()
    first = re.sub(r"[^a-z]", "", (first_name or "").lower())
    if len(first) >= 3 and first in name:
        warnings.append("It includes %s's real first name." % (first_name.strip() or "their"))
    years = re.findall(r"(?:19|20)\d\d", name)
    if years or (birth_year and str(birth_year) in name):
        warnings.append("It includes what looks like a birth year.")
    if re.search(r"\d{5,}", name):
        warnings.append("It has a long run of numbers -- avoid phone or house numbers.")
    if re.search(r"(?:^|_)(?:school|elem|grade|class)", name):
        warnings.append("It mentions school -- leave that out.")
    return warnings
