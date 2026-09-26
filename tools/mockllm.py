#!/usr/bin/env python3
"""A stand-in language-model server for developing and testing the bots.

It answers the same endpoints the bot client probes and calls, the way
llama.cpp's server does -- ``/v1/models``, ``/props`` (sampling defaults, a
ChatML chat template, BOS/EOS, n_ctx), ``/tokenize``, ``/v1/chat/completions``
and ``/v1/completions`` -- and writes replies that fit what it was asked for:
a JSON array of usernames, a JSON array of profiles, or a short line of chat.

    python3 tools/mockllm.py --port 5000
    python3 tools/mockllm.py --port 5000 --latency 0.8 --dupes 0.3

``--dupes`` makes a share of the usernames it invents collide (with each
other and with the seeded accounts), which is how the "that name is taken,
give me another" loop gets exercised.  Point the Bots Zone's endpoint at
http://127.0.0.1:5000/v1 to use it.

``--think`` makes it behave like a reasoning model, which writes its notes
before the answer and spends ``max_tokens`` on them too:

    separate       hybrid (Qwen3, GLM): notes in ``reasoning_content`` the way
                   LM Studio and llama.cpp return them; skipped when asked not
                   to think (``chat_template_kwargs`` / ``template_vars`` /
                   ``enable_thinking``, or a template that closes the block)
    inline         hybrid, notes in the reply as ``<think>...</think>``
    forced         cannot be turned off (R1 distills, gpt-oss), notes in
                   ``reasoning_content``
    forced-inline  cannot be turned off and the template opens the block, so
                   the reply is ``notes</think>answer`` with no opening tag
    harmony        gpt-oss without a reasoning parser: ``<|channel|>analysis``
                   ... ``<|channel|>final<|message|>answer``

``--strict`` refuses requests carrying fields it does not know (HTTP 422),
the way a strict OpenAI-compatible server would; ``--knows FIELD`` teaches
it one more (``--strict --knows template_vars`` is TabbyAPI-like), and
``--efforts low,medium,high`` refuses any other ``reasoning_effort`` the way
vLLM does.  A thinking model's notes grow with the effort it is given.
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

CHATML = ("{% for message in messages %}{{'<|im_start|>' + message['role'] + "
          "'\\n' + message['content'] + '<|im_end|>' + '\\n'}}{% endfor %}"
          "{% if add_generation_prompt %}{{ '<|im_start|>assistant\\n' }}{% endif %}")
# Qwen3's switch: a template that closes the think block when told not to think
CHATML_THINK = CHATML.replace(
    "{{ '<|im_start|>assistant\\n' }}{% endif %}",
    "{{ '<|im_start|>assistant\\n' }}{% if enable_thinking is defined and "
    "enable_thinking is false %}{{ '<think>\\n\\n</think>\\n\\n' }}{% endif %}{% endif %}")
# DeepSeek-R1 style: the template itself opens the block
CHATML_FORCED = CHATML.replace("{{ '<|im_start|>assistant\\n' }}",
                               "{{ '<|im_start|>assistant\\n<think>\\n' }}")
KNOWN_FIELDS = {"model", "messages", "prompt", "max_tokens", "stream", "stop",
                "temperature", "top_p", "top_k", "min_p", "repeat_penalty",
                "repeat_last_n", "presence_penalty", "frequency_penalty", "n",
                "seed"}
NOTES = ["Okay, so the player said something and I should answer in character.",
         "Let me think about what a casual player would type here.",
         "The chat is fast so it should be short, lowercase maybe.",
         "I should not repeat what the others already said in the round.",
         "Maybe something about the flag or the score, or just a joke.",
         "Keep it natural, no punctuation at the end, one line only."]

TAKEN = ["builderman_x", "RetroKid2007", "BlockSmith", "NoobSlayer99",
         "PixelPatty", "CartPusher", "FlagRunner", "GrillMaster"]
SYLL = ["ka", "ri", "zo", "mi", "lu", "ne", "vo", "ta", "shi", "ro", "ba",
        "ki", "no", "sa", "de", "fi", "go", "ya", "mu", "te"]
WORDS = ["frog", "pixel", "toast", "ember", "moss", "comet", "noodle", "yeti",
         "banjo", "waffle", "otter", "glitch", "pickle", "rune", "moth"]
CHAT = ["gg", "lol", "nice one", "who has the flag", "push the cart pls",
        "rip", "brb", "anyone doing tycoon after this", "that was close",
        "ez", "go go go", "i need a medic lol", "how do u get that hat",
        "wait what", "lets gooo", "defend mid", "hi", "yo", "gg wp"]
COMMENTS = ["nice avatar!!", "gg earlier :D", "add me for tycoon runs",
            "your hat is so clean", "we should play ctf later", "hiii",
            "love the outfit", "you carried that round lol",
            "thanks for the friend request!", "that unusual tho"]
DMS = ["haha yeah", "sure, want to play burger tycoon?", "hey! whats up",
       "lol same", "i'm on later tonight if you want to play",
       "gg that match was crazy", "idk maybe, what are you playing?"]
ABOUT = ["just here for the hats", "ctf main. red team forever",
         "tycoon speedrunner", "add me!!", "dont ask about my kd lol",
         "i build things", "music + games", ""]


def invent(rng: random.Random, dupes: float) -> str:
    if rng.random() < dupes:
        return rng.choice(TAKEN)
    style = rng.random()
    if style < 0.4:
        name = "".join(rng.choice(SYLL) for _ in range(rng.randint(2, 3)))
        return name.title() if rng.random() < 0.5 else name
    if style < 0.7:
        return rng.choice(WORDS) + str(rng.randint(1, 99))
    return rng.choice(WORDS).title() + rng.choice(WORDS).title()


class State:
    latency = 0.0
    dupes = 0.0
    fail = 0.0
    think = ""
    strict = False
    knows: set = set()
    efforts: set = set()
    bodies: list = []          # the last requests, for tests
    requests = 0
    lock = threading.Lock()


def reply_for(messages, rng: random.Random) -> str:
    system = " ".join(m.get("content", "") for m in messages
                      if m.get("role") == "system").lower()
    last = messages[-1].get("content", "") if messages else ""
    if "invent usernames" in system or "usernames" in last.lower() and "give me" in last.lower():
        count = 12
        match = re.search(r"(\d+)", last)
        if match:
            count = max(1, min(60, int(match.group(1))))
        return json.dumps([invent(rng, State.dupes) for _ in range(count)])
    if "about-me" in system or "about me" in system and "players:" in last.lower():
        names = re.findall(r"name: ([A-Za-z0-9_]+)", last)
        return json.dumps([{"name": n, "about": rng.choice(ABOUT),
                            "location": rng.choice(["", "UK", "Ohio", "Canada"])}
                           for n in names])
    if "in-game chat" in system:
        return rng.choice(CHAT) if rng.random() > 0.1 else "(skip)"
    if "private message" in system:
        return rng.choice(DMS)
    if "status post" in system:
        return rng.choice(["finally got the golden arches", "ctf later anyone",
                           "new hat day", "so tired lol", "gg to everyone today"])
    if "comment" in system:
        return rng.choice(COMMENTS)
    return "ok"


def _asked_not_to_think(body, chat: bool) -> bool:
    if not chat:
        # completion mode: the template closed the block itself
        return (body.get("prompt") or "").rstrip().endswith("</think>")
    for key in ("chat_template_kwargs", "template_vars"):
        values = body.get(key)
        if isinstance(values, dict) and values.get("enable_thinking") is False:
            return True
    if body.get("enable_thinking") is False or body.get("reasoning_effort") == "none":
        return True
    return any("/no_think" in str(m.get("content", "")) for m in body.get("messages") or [])


def think(body, chat: bool, answer: str, limit: int, rng: random.Random):
    """(content, reasoning, finish) with ``limit`` tokens (4 characters each)."""
    mode = State.think
    if not mode or (mode in ("separate", "inline") and _asked_not_to_think(body, chat)):
        if len(answer) // 4 > limit:
            return answer[:limit * 4], "", "length"
        return answer, "", "stop"
    effort = body.get("reasoning_effort") or (body.get("chat_template_kwargs") or {}).get(
        "reasoning_effort") or "medium"
    scale = {"minimal": 0.25, "low": 0.5, "medium": 1, "high": 2, "xhigh": 4}.get(effort, 1)
    notes = " ".join(rng.choice(NOTES) for _ in range(max(1, int(rng.randint(4, 9) * scale))))
    budget = limit * 4
    if mode == "harmony":
        full = ("<|channel|>analysis<|message|>" + notes + "<|end|><|start|>assistant"
                "<|channel|>final<|message|>" + answer)
        return (full[:budget], "", "length") if len(full) > budget else (full, "", "stop")
    if mode in ("separate", "forced") and chat:
        if len(notes) >= budget:
            return "", notes[:budget], "length"
        left = budget - len(notes)
        return (answer[:left], notes, "length") if len(answer) > left else (answer, notes, "stop")
    opened = mode == "forced-inline" or (not chat and (body.get("prompt") or "")
                                          .rstrip().endswith("<think>"))
    full = ("" if opened else "<think>") + notes + "</think>\n\n" + answer
    return (full[:budget], "", "length") if len(full) > budget else (full, "", "stop")


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass

    def _send(self, status: int, payload) -> None:
        blob = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(blob)))
        self.end_headers()
        self.wfile.write(blob)

    def _body(self):
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            return json.loads(raw or b"{}")
        except ValueError:
            return {}

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/v1/models":
            return self._send(200, {"object": "list", "data": [
                {"id": "mock-model-7b", "object": "model", "owned_by": "mock",
                 "meta": {"n_ctx_train": 32768}}]})
        if path == "/props":
            template = {"separate": CHATML_THINK, "inline": CHATML_THINK,
                        "forced-inline": CHATML_FORCED}.get(State.think, CHATML)
            return self._send(200, {
                "default_generation_settings": {
                    "n_ctx": 16384,
                    "params": {"temperature": 0.8, "top_k": 40, "top_p": 0.95,
                               "min_p": 0.05, "repeat_penalty": 1.1,
                               "repeat_last_n": 64, "presence_penalty": 0.0,
                               "frequency_penalty": 0.0, "stop": []}},
                "total_slots": 1, "chat_template": template,
                "bos_token": "", "eos_token": "<|im_end|>",
                "model_path": "/models/mock-model-7b.gguf"})
        return self._send(404, {"error": "not found"})

    def do_POST(self):
        path = self.path.split("?")[0]
        body = self._body()
        with State.lock:
            State.requests += 1
        if path == "/tokenize":
            text = body.get("content") or ""
            return self._send(200, {"tokens": list(range(max(1, len(text) // 4)))})
        if path in ("/v1/chat/completions", "/v1/completions"):
            if State.latency:
                time.sleep(State.latency * random.uniform(0.5, 1.5))
            if random.random() < State.fail:
                return self._send(500, {"error": "mock failure"})
            with State.lock:
                State.bodies.append(body)
                del State.bodies[:-20]
            effort = body.get("reasoning_effort")
            if State.efforts and effort is not None and effort not in State.efforts:
                return self._send(400, {"detail": [{"loc": ["body", "reasoning_effort"],
                                                    "msg": "Input should be %s" % ", ".join(
                                                        sorted(State.efforts)),
                                                    "input": effort}]})
            if State.strict:
                unknown = sorted(set(body) - KNOWN_FIELDS - State.knows)
                if unknown:
                    return self._send(422, {"detail": [{"loc": ["body", k], "msg":
                                                        "extra fields not permitted"}
                                                       for k in unknown]})
            rng = random.Random()
            chat = path.endswith("chat/completions")
            if chat:
                messages = body.get("messages") or []
                prompt_chars = sum(len(m.get("content", "")) for m in messages)
            else:
                prompt = body.get("prompt") or ""
                prompt_chars = len(prompt)
                messages = []
                for match in re.finditer(r"<\|im_start\|>(\w+)\n(.*?)<\|im_end\|>",
                                         prompt, re.S):
                    messages.append({"role": match.group(1),
                                     "content": match.group(2)})
            answer = reply_for(messages, rng)
            limit = int(body.get("max_tokens") or 0) or 10 ** 6
            content, reasoning, finish = think(body, chat, answer, limit, rng)
            used = (len(content) + len(reasoning)) // 4
            usage = {"prompt_tokens": prompt_chars // 4,
                     "completion_tokens": max(1, used)}
            if chat:
                message = {"role": "assistant", "content": content}
                if reasoning:
                    message["reasoning_content"] = reasoning
                return self._send(200, {"choices": [{"index": 0, "message": message,
                                                     "finish_reason": finish}],
                                        "usage": usage})
            return self._send(200, {"choices": [{"index": 0, "text": content,
                                                 "finish_reason": finish}],
                                    "usage": usage})
        return self._send(404, {"error": "not found"})


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Mock LLM server for the bots")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--latency", type=float, default=0.15)
    parser.add_argument("--dupes", type=float, default=0.0)
    parser.add_argument("--fail", type=float, default=0.0)
    parser.add_argument("--think", default="", choices=["", "separate", "inline", "forced",
                                                         "forced-inline", "harmony"])
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--knows", action="append", default=[])
    parser.add_argument("--efforts", default="")
    args = parser.parse_args(argv)
    State.latency, State.dupes, State.fail = args.latency, args.dupes, args.fail
    State.think, State.strict, State.knows = args.think, args.strict, set(args.knows)
    State.efforts = {e for e in args.efforts.split(",") if e}
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print("mock LLM on http://%s:%d/v1" % (args.host, args.port), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
