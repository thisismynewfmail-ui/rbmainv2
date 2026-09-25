"""A sandboxed renderer for model chat templates.

Model servers report their chat template as Jinja source (llama.cpp's
``/props``, Ollama's ``/api/show``, TabbyAPI's model card).  In completion
mode the bots format their own prompts with it, exactly as the server would
for a chat request, so the model sees the turn markers it was trained on.

The template is text that arrived over the network, so it is interpreted,
never compiled: there is no ``eval``, no attribute that starts with an
underscore, no method that is not on a short list of harmless string, list and
dict methods, and a cap on loop iterations and output size.  The dialect is
the one Hugging Face renders chat templates with -- ``trim_blocks`` and
``lstrip_blocks`` on, loop controls enabled, ``raise_exception`` and
``strftime_now`` available -- which is the dialect the templates are written
for.
"""
from __future__ import annotations

import json
import re
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

MAX_OUTPUT = 400_000
MAX_STEPS = 200_000


class TemplateError(Exception):
    pass


class RaisedError(TemplateError):
    """The template called raise_exception() -- a deliberate refusal."""


class Undefined:
    __slots__ = ("name",)

    def __init__(self, name: str = ""):
        self.name = name

    def __bool__(self):
        return False

    def __str__(self):
        return ""

    def __iter__(self):
        return iter(())

    def __len__(self):
        return 0

    def __eq__(self, other):
        return isinstance(other, Undefined) or other is None and False

    def __hash__(self):
        return 0


UNDEF = Undefined()


class Namespace(dict):
    pass


class Macro:
    def __init__(self, name, params, body, renderer):
        self.name, self.params, self.body, self.renderer = name, params, body, renderer


class _Break(Exception):
    pass


class _Continue(Exception):
    pass


# ================================================================== lexing
_TAG_RE = re.compile(r"(\{\{-?|\{%-?|\{#-?)", re.S)


def _tokenize_template(source: str) -> List[Tuple[str, str]]:
    """Split into ("text"|"var"|"block", content) with whitespace control."""
    out: List[Tuple[str, str]] = []
    pos = 0
    length = len(source)
    pending_lstrip = False       # a "-" on the closing side of the last tag
    trim_newline = False         # trim_blocks after a block tag
    while pos < length:
        match = _TAG_RE.search(source, pos)
        if not match:
            text = source[pos:]
            out.append(("text", _apply_trims(text, pending_lstrip, trim_newline)))
            break
        start = match.start()
        opener = match.group(1)
        text = source[pos:start]
        kind = {"{{": "var", "{%": "block", "{#": "comment"}[opener[:2]]
        strip_left = opener.endswith("-")
        text = _apply_trims(text, pending_lstrip, trim_newline)
        if strip_left:
            text = text.rstrip()
        elif kind in ("block", "comment"):
            # lstrip_blocks: whitespace from the start of the line up to a
            # block tag is dropped
            line_start = text.rfind("\n")
            tail = text[line_start + 1:]
            if tail.strip(" \t") == "":
                text = text[:line_start + 1]
        out.append(("text", text))
        closer = {"var": "}}", "block": "%}", "comment": "#}"}[kind]
        end = source.find(closer, match.end())
        if end < 0:
            raise TemplateError("unclosed tag")
        inner = source[match.end():end]
        pending_lstrip = inner.endswith("-")
        if pending_lstrip:
            inner = inner[:-1]
        pos = end + 2
        trim_newline = kind in ("block", "comment")
        if kind != "comment":
            out.append((kind, inner.strip()))
    return [t for t in out if not (t[0] == "text" and t[1] == "")]


def _apply_trims(text: str, lstrip: bool, trim_newline: bool) -> str:
    if lstrip:
        return text.lstrip()
    if trim_newline and text.startswith("\n"):
        return text[1:]
    if trim_newline and text.startswith("\r\n"):
        return text[2:]
    return text


# ============================================================ expressions
_EXPR_TOKEN = re.compile(r"""
    \s*(?:
      (?P<num>\d+\.\d*|\d+)
    | (?P<str>'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*")
    | (?P<name>[A-Za-z_][A-Za-z0-9_]*)
    | (?P<op>\*\*|//|==|!=|<=|>=|[-+*/%~<>()\[\]{}.,:|=])
    )""", re.X | re.S)


def _lex_expr(text: str) -> List[Tuple[str, Any]]:
    tokens = []
    pos = 0
    text = text.rstrip()
    while pos < len(text):
        match = _EXPR_TOKEN.match(text, pos)
        if not match or match.end() == pos:
            if text[pos:].strip() == "":
                break
            raise TemplateError("bad expression near %r" % text[pos:pos + 12])
        pos = match.end()
        if match.group("num") is not None:
            raw = match.group("num")
            tokens.append(("num", float(raw) if "." in raw else int(raw)))
        elif match.group("str") is not None:
            raw = match.group("str")
            tokens.append(("str", _unescape(raw[1:-1])))
        elif match.group("name") is not None:
            tokens.append(("name", match.group("name")))
        else:
            tokens.append(("op", match.group("op")))
    tokens.append(("end", None))
    return tokens


def _unescape(text: str) -> str:
    return re.sub(r"\\(.)", lambda m: {"n": "\n", "t": "\t", "r": "\r"}.get(
        m.group(1), m.group(1)), text)


class _Parser:
    """Pratt-ish recursive descent over expression tokens -> AST tuples."""

    def __init__(self, text: str):
        self.tokens = _lex_expr(text)
        self.i = 0

    def peek(self, offset: int = 0):
        return self.tokens[min(self.i + offset, len(self.tokens) - 1)]

    def next(self):
        tok = self.tokens[self.i]
        self.i += 1
        return tok

    def at(self, kind: str, value: Any = None) -> bool:
        tok = self.peek()
        return tok[0] == kind and (value is None or tok[1] == value)

    def eat(self, kind: str, value: Any = None):
        if not self.at(kind, value):
            raise TemplateError("expected %s %r, got %r" % (kind, value, self.peek()))
        return self.next()

    def done(self) -> bool:
        return self.at("end")

    # -- grammar
    def expression(self):
        node = self.or_expr()
        if self.at("name", "if"):
            self.next()
            cond = self.or_expr()
            other = ("lit", UNDEF)
            if self.at("name", "else"):
                self.next()
                other = self.expression()
            node = ("cond", cond, node, other)
        return node

    def or_expr(self):
        node = self.and_expr()
        while self.at("name", "or"):
            self.next()
            node = ("or", node, self.and_expr())
        return node

    def and_expr(self):
        node = self.not_expr()
        while self.at("name", "and"):
            self.next()
            node = ("and", node, self.not_expr())
        return node

    def not_expr(self):
        if self.at("name", "not"):
            self.next()
            return ("not", self.not_expr())
        return self.compare()

    def compare(self):
        node = self.concat()
        while True:
            tok = self.peek()
            if tok[0] == "op" and tok[1] in ("==", "!=", "<", ">", "<=", ">="):
                self.next()
                node = ("cmp", tok[1], node, self.concat())
            elif tok == ("name", "in"):
                self.next()
                node = ("in", node, self.concat())
            elif tok == ("name", "not") and self.peek(1) == ("name", "in"):
                self.next(); self.next()
                node = ("not", ("in", node, self.concat()))
            elif tok == ("name", "is"):
                self.next()
                negate = False
                if self.at("name", "not"):
                    self.next()
                    negate = True
                name = self.eat("name")[1]
                args = []
                if self.at("op", "("):
                    args = self.call_args()[0]
                elif not self.done() and self.peek()[0] in ("num", "str"):
                    args = [self.primary()]
                test = ("test", name, node, args)
                node = ("not", test) if negate else test
            else:
                return node

    def concat(self):
        node = self.additive()
        while self.at("op", "~"):
            self.next()
            node = ("concat", node, self.additive())
        return node

    def additive(self):
        node = self.term()
        while self.peek()[0] == "op" and self.peek()[1] in ("+", "-"):
            op = self.next()[1]
            node = ("bin", op, node, self.term())
        return node

    def term(self):
        node = self.unary()
        while self.peek()[0] == "op" and self.peek()[1] in ("*", "/", "//", "%"):
            op = self.next()[1]
            node = ("bin", op, node, self.unary())
        return node

    def unary(self):
        if self.at("op", "-"):
            self.next()
            return ("neg", self.unary())
        if self.at("op", "+"):
            self.next()
            return self.unary()
        return self.power()

    def power(self):
        node = self.filtered()
        if self.at("op", "**"):
            self.next()
            node = ("bin", "**", node, self.unary())
        return node

    def filtered(self):
        node = self.postfix(self.primary())
        while self.at("op", "|"):
            self.next()
            name = self.eat("name")[1]
            args, kwargs = [], {}
            if self.at("op", "("):
                args, kwargs = self.call_args()
            node = ("filter", name, node, args, kwargs)
        return node

    def postfix(self, node):
        while True:
            if self.at("op", "."):
                self.next()
                name = self.eat("name")[1]
                node = ("attr", node, name)
            elif self.at("op", "["):
                self.next()
                if self.at("op", ":") or self._slice_ahead():
                    start = stop = step = None
                    if not self.at("op", ":"):
                        start = self.expression()
                    self.eat("op", ":")
                    if not self.at("op", "]") and not self.at("op", ":"):
                        stop = self.expression()
                    if self.at("op", ":"):
                        self.next()
                        if not self.at("op", "]"):
                            step = self.expression()
                    self.eat("op", "]")
                    node = ("slice", node, start, stop, step)
                else:
                    key = self.expression()
                    self.eat("op", "]")
                    node = ("item", node, key)
            elif self.at("op", "("):
                args, kwargs = self.call_args()
                node = ("call", node, args, kwargs)
            else:
                return node

    def _slice_ahead(self) -> bool:
        depth = 0
        j = self.i
        while j < len(self.tokens):
            kind, value = self.tokens[j]
            if kind == "op" and value in "([{":
                depth += 1
            elif kind == "op" and value in ")]}":
                if depth == 0:
                    return False
                depth -= 1
            elif kind == "op" and value == ":" and depth == 0:
                return True
            elif kind == "end":
                return False
            j += 1
        return False

    def call_args(self):
        self.eat("op", "(")
        args, kwargs = [], {}
        while not self.at("op", ")"):
            if self.peek()[0] == "name" and self.peek(1) == ("op", "="):
                name = self.next()[1]
                self.next()
                kwargs[name] = self.expression()
            else:
                args.append(self.expression())
            if not self.at("op", ")"):
                self.eat("op", ",")
        self.eat("op", ")")
        return args, kwargs

    def primary(self):
        kind, value = self.next()
        if kind == "num" or kind == "str":
            node = ("lit", value)
            # adjacent string literals concatenate
            while kind == "str" and self.peek()[0] == "str":
                node = ("lit", node[1] + self.next()[1])
            return node
        if kind == "name":
            if value in ("true", "True"):
                return ("lit", True)
            if value in ("false", "False"):
                return ("lit", False)
            if value in ("none", "None"):
                return ("lit", None)
            return ("name", value)
        if kind == "op" and value == "(":
            if self.at("op", ")"):
                self.next()
                return ("tuple", [])
            first = self.expression()
            if self.at("op", ","):
                items = [first]
                while self.at("op", ","):
                    self.next()
                    if self.at("op", ")"):
                        break
                    items.append(self.expression())
                self.eat("op", ")")
                return ("tuple", items)
            self.eat("op", ")")
            return first
        if kind == "op" and value == "[":
            items = []
            while not self.at("op", "]"):
                items.append(self.expression())
                if not self.at("op", "]"):
                    self.eat("op", ",")
            self.eat("op", "]")
            return ("list", items)
        if kind == "op" and value == "{":
            pairs = []
            while not self.at("op", "}"):
                key = self.expression()
                self.eat("op", ":")
                pairs.append((key, self.expression()))
                if not self.at("op", "}"):
                    self.eat("op", ",")
            self.eat("op", "}")
            return ("dict", pairs)
        raise TemplateError("unexpected %r" % (value,))


def parse_expr(text: str):
    parser = _Parser(text)
    node = parser.expression()
    if not parser.done():
        raise TemplateError("trailing tokens in %r" % text)
    return node


# ============================================================ statements
def _parse_nodes(tokens: List[Tuple[str, str]], pos: int,
                 stop: Tuple[str, ...]) -> Tuple[List[Any], int, str]:
    nodes: List[Any] = []
    while pos < len(tokens):
        kind, content = tokens[pos]
        if kind == "text":
            nodes.append(("text", content))
            pos += 1
            continue
        if kind == "var":
            nodes.append(("out", parse_expr(content)))
            pos += 1
            continue
        word = content.split(None, 1)[0] if content else ""
        rest = content[len(word):].strip()
        if word in stop:
            return nodes, pos, content
        pos += 1
        if word == "if":
            branches = []
            cond = parse_expr(rest)
            body, pos, end = _parse_nodes(tokens, pos, ("elif", "else", "endif"))
            branches.append((cond, body))
            while True:
                word2 = end.split(None, 1)[0]
                pos += 1
                if word2 == "elif":
                    cond = parse_expr(end[4:].strip())
                    body, pos, end = _parse_nodes(tokens, pos,
                                                  ("elif", "else", "endif"))
                    branches.append((cond, body))
                elif word2 == "else":
                    body, pos, end = _parse_nodes(tokens, pos, ("endif",))
                    branches.append((None, body))
                    pos += 1
                    break
                else:
                    break
            nodes.append(("if", branches))
        elif word == "for":
            match = re.match(r"(.+?)\s+in\s+(.+)$", rest, re.S)
            if not match:
                raise TemplateError("bad for: %r" % rest)
            targets = [t.strip() for t in match.group(1).split(",")]
            source_text = match.group(2)
            cond = None
            recursive = False
            # "for x in xs if cond" -- split on a top level ' if '
            parser = _Parser(source_text)
            iterable = parser.or_expr()
            if parser.at("name", "if"):
                parser.next()
                cond = parser.expression()
            if parser.at("name", "recursive"):
                parser.next()
                recursive = True
            body, pos, end = _parse_nodes(tokens, pos, ("else", "endfor"))
            other: List[Any] = []
            if end.split(None, 1)[0] == "else":
                pos += 1
                other, pos, end = _parse_nodes(tokens, pos, ("endfor",))
            pos += 1
            nodes.append(("for", targets, iterable, cond, body, other, recursive))
        elif word == "set":
            if "=" in rest and not rest.strip().startswith("="):
                name, _, expr = rest.partition("=")
                nodes.append(("set", name.strip(), parse_expr(expr)))
            else:
                body, pos, _end = _parse_nodes(tokens, pos, ("endset",))
                pos += 1
                nodes.append(("setblock", rest.strip(), body))
        elif word == "macro":
            match = re.match(r"([A-Za-z_]\w*)\s*\((.*)\)\s*$", rest, re.S)
            if not match:
                raise TemplateError("bad macro")
            params = []
            for part in _split_top(match.group(2)):
                part = part.strip()
                if not part:
                    continue
                if "=" in part:
                    pname, _, default = part.partition("=")
                    params.append((pname.strip(), parse_expr(default)))
                else:
                    params.append((part, None))
            body, pos, _end = _parse_nodes(tokens, pos, ("endmacro",))
            pos += 1
            nodes.append(("macro", match.group(1), params, body))
        elif word in ("break", "continue"):
            nodes.append((word,))
        elif word in ("generation", "endgeneration"):
            continue
        elif word == "filter":
            body, pos, _end = _parse_nodes(tokens, pos, ("endfilter",))
            pos += 1
            nodes.append(("filterblock", rest, body))
        elif word == "call":
            body, pos, _end = _parse_nodes(tokens, pos, ("endcall",))
            pos += 1
            nodes.append(("out", parse_expr(rest)))
        else:
            raise TemplateError("unsupported tag %r" % word)
    return nodes, pos, ""


def _split_top(text: str) -> List[str]:
    parts, depth, cur = [], 0, []
    quote = ""
    for ch in text:
        if quote:
            cur.append(ch)
            if ch == quote:
                quote = ""
            continue
        if ch in "'\"":
            quote = ch
        elif ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        elif ch == "," and depth == 0:
            parts.append("".join(cur))
            cur = []
            continue
        cur.append(ch)
    parts.append("".join(cur))
    return parts


# ================================================================ runtime
_SAFE_METHODS = {
    str: {"strip", "lstrip", "rstrip", "split", "rsplit", "startswith",
          "endswith", "upper", "lower", "title", "capitalize", "replace",
          "find", "rfind", "count", "splitlines", "join", "isdigit",
          "isalpha", "isspace", "format", "index"},
    list: {"index", "count"},
    tuple: {"index", "count"},
    dict: {"items", "keys", "values", "get"},
    Namespace: {"items", "keys", "values", "get"},
}


class _Loop:
    def __init__(self, items: List[Any], index: int, depth: int = 1):
        self.items = items
        self.index0 = index
        self.depth = depth

    def get(self, name: str) -> Any:
        n = len(self.items)
        i = self.index0
        return {
            "index0": i, "index": i + 1, "first": i == 0, "last": i == n - 1,
            "length": n, "revindex": n - i, "revindex0": n - i - 1,
            "previtem": self.items[i - 1] if i > 0 else UNDEF,
            "nextitem": self.items[i + 1] if i + 1 < n else UNDEF,
            "depth": self.depth, "depth0": self.depth - 1,
        }.get(name, UNDEF)


class Template:
    def __init__(self, source: str):
        self.source = source or ""
        self.nodes, _pos, _end = _parse_nodes(_tokenize_template(self.source),
                                              0, ())

    def render(self, **context: Any) -> str:
        state = {"steps": 0, "out": 0}
        scope = dict(_GLOBALS)
        scope.update(context)
        out: List[str] = []
        self._run(self.nodes, [scope], out, state)
        return "".join(out)

    # ------------------------------------------------------------ nodes
    def _run(self, nodes, scopes, out, state) -> None:
        for node in nodes:
            state["steps"] += 1
            if state["steps"] > MAX_STEPS:
                raise TemplateError("template ran too long")
            kind = node[0]
            if kind == "text":
                self._emit(out, node[1], state)
            elif kind == "out":
                self._emit(out, _to_str(self._eval(node[1], scopes)), state)
            elif kind == "if":
                for cond, body in node[1]:
                    if cond is None or _truthy(self._eval(cond, scopes)):
                        self._run(body, scopes, out, state)
                        break
            elif kind == "for":
                self._for(node, scopes, out, state)
            elif kind == "set":
                self._set(node[1], self._eval(node[2], scopes), scopes)
            elif kind == "setblock":
                buf: List[str] = []
                self._run(node[2], scopes, buf, state)
                self._set(node[1], "".join(buf), scopes)
            elif kind == "macro":
                scopes[-1][node[1]] = Macro(node[1], node[2], node[3], self)
            elif kind == "break":
                raise _Break()
            elif kind == "continue":
                raise _Continue()
            elif kind == "filterblock":
                buf = []
                self._run(node[2], scopes, buf, state)
                parser = _Parser(node[1])
                name = parser.eat("name")[1]
                args, kwargs = ([], {})
                if parser.at("op", "("):
                    args, kwargs = parser.call_args()
                value = _apply_filter(name, "".join(buf),
                                      [self._eval(a, scopes) for a in args],
                                      {k: self._eval(v, scopes)
                                       for k, v in kwargs.items()})
                self._emit(out, _to_str(value), state)

    def _emit(self, out, text: str, state) -> None:
        state["out"] += len(text)
        if state["out"] > MAX_OUTPUT:
            raise TemplateError("template output too large")
        out.append(text)

    def _set(self, target: str, value: Any, scopes) -> None:
        if "." in target:
            name, attr = target.split(".", 1)
            obj = self._lookup(name, scopes)
            if isinstance(obj, Namespace) and not attr.startswith("_"):
                obj[attr] = value
                return
            raise TemplateError("cannot set %s" % target)
        if "," in target:
            names = [t.strip() for t in target.split(",")]
            values = list(value)
            for name, item in zip(names, values):
                scopes[-1][name] = item
            return
        scopes[-1][target] = value

    def _for(self, node, scopes, out, state) -> None:
        _, targets, iterable, cond, body, other, _recursive = node
        source = self._eval(iterable, scopes)
        if isinstance(source, dict):
            items = list(source.keys())
        elif isinstance(source, (str, Undefined)) or source is None:
            items = list(source) if isinstance(source, str) else []
        else:
            try:
                items = list(source)
            except TypeError:
                items = []
        if cond is not None:
            filtered = []
            for item in items:
                frame = dict()
                self._bind(targets, item, frame)
                if _truthy(self._eval(cond, scopes + [frame])):
                    filtered.append(item)
            items = filtered
        if not items:
            self._run(other, scopes, out, state)
            return
        frame: Dict[str, Any] = {}
        scopes = scopes + [frame]
        for index, item in enumerate(items):
            state["steps"] += 1
            if state["steps"] > MAX_STEPS:
                raise TemplateError("template ran too long")
            self._bind(targets, item, frame)
            frame["loop"] = _Loop(items, index)
            try:
                self._run(body, scopes, out, state)
            except _Continue:
                continue
            except _Break:
                break

    @staticmethod
    def _bind(targets, item, frame) -> None:
        if len(targets) == 1:
            frame[targets[0]] = item
        else:
            values = list(item) if not isinstance(item, (str, Undefined)) else []
            for i, name in enumerate(targets):
                frame[name] = values[i] if i < len(values) else UNDEF

    # --------------------------------------------------------- expressions
    def _lookup(self, name: str, scopes) -> Any:
        for scope in reversed(scopes):
            if name in scope:
                return scope[name]
        return Undefined(name)

    def _eval(self, node, scopes) -> Any:
        kind = node[0]
        if kind == "lit":
            return node[1]
        if kind == "name":
            return self._lookup(node[1], scopes)
        if kind == "attr":
            return _getattr(self._eval(node[1], scopes), node[2])
        if kind == "item":
            return _getitem(self._eval(node[1], scopes), self._eval(node[2], scopes))
        if kind == "slice":
            obj = self._eval(node[1], scopes)
            parts = [None if p is None else self._eval(p, scopes)
                     for p in node[2:5]]
            try:
                return obj[slice(*parts)]
            except Exception:
                return UNDEF
        if kind == "call":
            return self._call(node, scopes)
        if kind == "filter":
            _, name, target, args, kwargs = node
            value = self._eval(target, scopes)
            return _apply_filter(name, value, [self._eval(a, scopes) for a in args],
                                 {k: self._eval(v, scopes) for k, v in kwargs.items()})
        if kind == "test":
            _, name, target, args = node
            return _apply_test(name, self._eval(target, scopes),
                               [self._eval(a, scopes) for a in args])
        if kind == "not":
            return not _truthy(self._eval(node[1], scopes))
        if kind == "and":
            left = self._eval(node[1], scopes)
            return self._eval(node[2], scopes) if _truthy(left) else left
        if kind == "or":
            left = self._eval(node[1], scopes)
            return left if _truthy(left) else self._eval(node[2], scopes)
        if kind == "cond":
            return self._eval(node[2] if _truthy(self._eval(node[1], scopes))
                              else node[3], scopes)
        if kind == "cmp":
            return _compare(node[1], self._eval(node[2], scopes),
                            self._eval(node[3], scopes))
        if kind == "in":
            needle, hay = self._eval(node[1], scopes), self._eval(node[2], scopes)
            try:
                return needle in hay
            except TypeError:
                return False
        if kind == "concat":
            return _to_str(self._eval(node[1], scopes)) + \
                _to_str(self._eval(node[2], scopes))
        if kind == "bin":
            return _binary(node[1], self._eval(node[2], scopes),
                           self._eval(node[3], scopes))
        if kind == "neg":
            value = self._eval(node[1], scopes)
            return -value if isinstance(value, (int, float)) else UNDEF
        if kind == "list":
            return [self._eval(n, scopes) for n in node[1]]
        if kind == "tuple":
            return tuple(self._eval(n, scopes) for n in node[1])
        if kind == "dict":
            return {self._eval(k, scopes): self._eval(v, scopes)
                    for k, v in node[1]}
        raise TemplateError("bad node %r" % (kind,))

    def _call(self, node, scopes) -> Any:
        _, target, arg_nodes, kwarg_nodes = node
        args = [self._eval(a, scopes) for a in arg_nodes]
        kwargs = {k: self._eval(v, scopes) for k, v in kwarg_nodes.items()}
        if target[0] == "attr":
            obj = self._eval(target[1], scopes)
            name = target[2]
            if isinstance(obj, _Loop) and name == "cycle":
                return args[obj.index0 % len(args)] if args else UNDEF
            allowed = None
            for typ, methods in _SAFE_METHODS.items():
                if isinstance(obj, typ):
                    allowed = methods
                    break
            if allowed is None or name not in allowed:
                return UNDEF
            try:
                if name == "format" and isinstance(obj, str):
                    return obj.format(*[_to_str(a) for a in args])
                result = getattr(obj, name)(*args, **kwargs)
            except Exception:
                return UNDEF
            if isinstance(result, (type({}.items()), type({}.keys()),
                                   type({}.values()))):
                return list(result)
            return result
        func = self._eval(target, scopes)
        if isinstance(func, Macro):
            return self._call_macro(func, args, kwargs)
        if callable(func) and getattr(func, "_template_safe", False):
            return func(*args, **kwargs)
        return UNDEF

    def _call_macro(self, macro: Macro, args, kwargs) -> str:
        frame: Dict[str, Any] = {}
        for index, (name, default) in enumerate(macro.params):
            if index < len(args):
                frame[name] = args[index]
            elif name in kwargs:
                frame[name] = kwargs[name]
            elif default is not None:
                frame[name] = self._eval(default, [dict(_GLOBALS)])
            else:
                frame[name] = UNDEF
        out: List[str] = []
        self._run(macro.body, [dict(_GLOBALS), frame], out,
                  {"steps": 0, "out": 0})
        return "".join(out)


# -------------------------------------------------------------- helpers
def _truthy(value: Any) -> bool:
    if isinstance(value, Undefined):
        return False
    return bool(value)


def _to_str(value: Any) -> str:
    if value is None or isinstance(value, Undefined):
        return "" if isinstance(value, Undefined) else "None"
    if value is True:
        return "True"
    if value is False:
        return "False"
    if isinstance(value, float) and value.is_integer():
        return repr(value)
    if isinstance(value, (list, tuple, dict)):
        return repr(value)
    return str(value)


def _getattr(obj: Any, name: str) -> Any:
    if name.startswith("_"):
        return UNDEF
    if isinstance(obj, _Loop):
        return obj.get(name)
    if isinstance(obj, dict):
        if name in obj:
            return obj[name]
        return UNDEF
    return UNDEF


def _getitem(obj: Any, key: Any) -> Any:
    if isinstance(key, str) and key.startswith("_"):
        return UNDEF
    if isinstance(obj, dict):
        return obj.get(key, UNDEF)
    if isinstance(obj, (list, tuple, str)):
        try:
            return obj[int(key)]
        except (ValueError, TypeError, IndexError):
            return UNDEF
    if isinstance(obj, _Loop) and isinstance(key, str):
        return obj.get(key)
    return UNDEF


def _compare(op: str, a: Any, b: Any) -> bool:
    if isinstance(a, Undefined):
        a = None
    if isinstance(b, Undefined):
        b = None
    try:
        if op == "==":
            return a == b
        if op == "!=":
            return a != b
        if op == "<":
            return a < b
        if op == ">":
            return a > b
        if op == "<=":
            return a <= b
        if op == ">=":
            return a >= b
    except TypeError:
        return False
    return False


def _binary(op: str, a: Any, b: Any) -> Any:
    try:
        if op == "+":
            if isinstance(a, Undefined) or isinstance(b, Undefined):
                if isinstance(a, str) or isinstance(b, str):
                    return _to_str(a) + _to_str(b)
                return UNDEF
            return a + b
        if op == "-":
            return a - b
        if op == "*":
            if isinstance(a, str) and isinstance(b, int) and b > 10000:
                return UNDEF
            return a * b
        if op == "/":
            return a / b
        if op == "//":
            return a // b
        if op == "%":
            if isinstance(a, str):
                return a % (b if isinstance(b, tuple) else (b,))
            return a % b
        if op == "**":
            if abs(b) > 64:
                return UNDEF
            return a ** b
    except Exception:
        return UNDEF
    return UNDEF


def _tojson(value: Any, indent: Any = None, **kwargs: Any) -> str:
    def clean(v):
        if isinstance(v, Undefined):
            return None
        if isinstance(v, dict):
            return {str(k): clean(x) for k, x in v.items()}
        if isinstance(v, (list, tuple)):
            return [clean(x) for x in v]
        return v
    ind = indent if isinstance(indent, int) else None
    return json.dumps(clean(value), ensure_ascii=False, indent=ind,
                      sort_keys=bool(kwargs.get("sort_keys", False)))


def _apply_filter(name: str, value: Any, args: List[Any],
                  kwargs: Dict[str, Any]) -> Any:
    if name == "trim" or name == "strip":
        return _to_str(value).strip()
    if name == "tojson":
        return _tojson(value, *args, **kwargs)
    if name in ("length", "count"):
        try:
            return len(value)
        except TypeError:
            return 0
    if name == "upper":
        return _to_str(value).upper()
    if name == "lower":
        return _to_str(value).lower()
    if name == "title":
        return _to_str(value).title()
    if name == "capitalize":
        return _to_str(value).capitalize()
    if name in ("default", "d"):
        fallback = args[0] if args else ""
        boolean = bool(args[1]) if len(args) > 1 else bool(kwargs.get("boolean"))
        if isinstance(value, Undefined) or (boolean and not _truthy(value)):
            return fallback
        return value
    if name == "join":
        sep = args[0] if args else kwargs.get("d", "")
        attr = kwargs.get("attribute")
        items = [(_getattr(v, attr) if attr else v) for v in (value or [])]
        return _to_str(sep).join(_to_str(v) for v in items)
    if name == "first":
        try:
            return next(iter(value))
        except (StopIteration, TypeError):
            return UNDEF
    if name == "last":
        try:
            return list(value)[-1]
        except (IndexError, TypeError):
            return UNDEF
    if name == "list":
        try:
            return list(value)
        except TypeError:
            return []
    if name == "string":
        return _to_str(value)
    if name == "int":
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return args[0] if args else 0
    if name == "float":
        try:
            return float(value)
        except (TypeError, ValueError):
            return args[0] if args else 0.0
    if name in ("safe", "e", "escape", "forceescape"):
        if name == "safe":
            return value
        return (_to_str(value).replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;").replace('"', "&#34;").replace("'", "&#39;"))
    if name == "replace":
        if len(args) >= 2:
            return _to_str(value).replace(_to_str(args[0]), _to_str(args[1]))
        return value
    if name == "reverse":
        try:
            return list(value)[::-1] if not isinstance(value, str) else value[::-1]
        except TypeError:
            return value
    if name == "sort":
        attr = kwargs.get("attribute")
        try:
            return sorted(value, key=(lambda v: _getattr(v, attr)) if attr else None,
                          reverse=bool(kwargs.get("reverse")))
        except TypeError:
            return list(value)
    if name == "unique":
        out, seen = [], set()
        for item in value or []:
            key = json.dumps(item, sort_keys=True, default=str)
            if key not in seen:
                seen.add(key)
                out.append(item)
        return out
    if name == "map":
        attr = kwargs.get("attribute")
        if attr:
            return [_getattr(v, attr) for v in (value or [])]
        if args:
            return [_apply_filter(args[0], v, list(args[1:]), {})
                    for v in (value or [])]
        return list(value or [])
    if name in ("select", "reject"):
        test = args[0] if args else "truthy"
        keep = name == "select"
        return [v for v in (value or [])
                if _apply_test(test, v, list(args[1:])) == keep]
    if name in ("selectattr", "rejectattr"):
        attr = args[0] if args else ""
        test = args[1] if len(args) > 1 else "truthy"
        keep = name == "selectattr"
        return [v for v in (value or [])
                if _apply_test(test, _getattr(v, attr), list(args[2:])) == keep]
    if name == "items":
        return list(value.items()) if isinstance(value, dict) else []
    if name == "dictsort":
        return sorted(value.items()) if isinstance(value, dict) else []
    if name == "abs":
        return abs(value) if isinstance(value, (int, float)) else value
    if name == "round":
        try:
            return round(float(value), int(args[0]) if args else 0)
        except (TypeError, ValueError):
            return value
    if name == "indent":
        width = args[0] if args else kwargs.get("width", 4)
        pad = " " * width if isinstance(width, int) else _to_str(width)
        lines = _to_str(value).split("\n")
        first = bool(kwargs.get("first", args[1] if len(args) > 1 else False))
        return "\n".join((pad + l if (i or first) and l else l)
                         for i, l in enumerate(lines))
    if name == "wordcount":
        return len(_to_str(value).split())
    if name == "batch":
        size = int(args[0]) if args else 1
        items = list(value or [])
        return [items[i:i + size] for i in range(0, len(items), max(1, size))]
    raise TemplateError("unknown filter %r" % name)


def _apply_test(name: str, value: Any, args: List[Any]) -> bool:
    if name == "defined":
        return not isinstance(value, Undefined)
    if name == "undefined":
        return isinstance(value, Undefined)
    if name == "none":
        return value is None
    if name in ("string",):
        return isinstance(value, str)
    if name in ("mapping",):
        return isinstance(value, dict)
    if name in ("iterable", "sequence"):
        return isinstance(value, (list, tuple, str, dict))
    if name == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if name == "float":
        return isinstance(value, float)
    if name == "boolean":
        return isinstance(value, bool)
    if name in ("true",):
        return value is True
    if name in ("false",):
        return value is False
    if name in ("truthy",):
        return _truthy(value)
    if name in ("falsy",):
        return not _truthy(value)
    if name == "odd":
        return isinstance(value, int) and value % 2 == 1
    if name == "even":
        return isinstance(value, int) and value % 2 == 0
    if name in ("equalto", "eq", "=="):
        return bool(args) and value == args[0]
    if name in ("ne", "!="):
        return bool(args) and value != args[0]
    if name == "in":
        return bool(args) and value in args[0]
    if name == "divisibleby":
        return bool(args) and isinstance(value, int) and value % args[0] == 0
    raise TemplateError("unknown test %r" % name)


def _safe(func: Callable) -> Callable:
    func._template_safe = True  # type: ignore[attr-defined]
    return func


@_safe
def _raise_exception(message: Any = "") -> None:
    raise RaisedError(_to_str(message))


@_safe
def _namespace(**kwargs: Any) -> Namespace:
    return Namespace(kwargs)


@_safe
def _range(*args: Any) -> List[int]:
    values = list(range(*[int(a) for a in args]))
    return values[:10000]


@_safe
def _strftime_now(fmt: str) -> str:
    return time.strftime(_to_str(fmt))


@_safe
def _dict(**kwargs: Any) -> Dict[str, Any]:
    return dict(kwargs)


_GLOBALS: Dict[str, Any] = {
    "raise_exception": _raise_exception,
    "namespace": _namespace,
    "range": _range,
    "strftime_now": _strftime_now,
    "dict": _dict,
    "true": True, "false": False, "none": None,
}


# ---------------------------------------------------------------- public
_compiled: Dict[str, Template] = {}


def render_chat(source: str, messages: List[Dict[str, Any]],
                add_generation_prompt: bool = True, bos_token: str = "",
                eos_token: str = "", **extra: Any) -> str:
    """Format ``messages`` with a model's chat template."""
    template = _compiled.get(source)
    if template is None:
        template = Template(source)
        if len(_compiled) > 8:
            _compiled.clear()
        _compiled[source] = template
    context = {"messages": [dict(m) for m in messages],
               "add_generation_prompt": add_generation_prompt,
               "bos_token": bos_token or "", "eos_token": eos_token or "",
               "tools": UNDEF, "documents": UNDEF, "custom_tools": UNDEF}
    context.update(extra)
    return template.render(**context)
