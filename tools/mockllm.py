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
            return self._send(200, {
                "default_generation_settings": {
                    "n_ctx": 16384,
                    "params": {"temperature": 0.8, "top_k": 40, "top_p": 0.95,
                               "min_p": 0.05, "repeat_penalty": 1.1,
                               "repeat_last_n": 64, "presence_penalty": 0.0,
                               "frequency_penalty": 0.0, "stop": []}},
                "total_slots": 1, "chat_template": CHATML,
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
            rng = random.Random()
            if path.endswith("chat/completions"):
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
            text = reply_for(messages, rng)
            usage = {"prompt_tokens": prompt_chars // 4,
                     "completion_tokens": max(1, len(text) // 4)}
            if path.endswith("chat/completions"):
                return self._send(200, {"choices": [{"index": 0, "message": {
                    "role": "assistant", "content": text},
                    "finish_reason": "stop"}], "usage": usage})
            return self._send(200, {"choices": [{"index": 0, "text": text,
                                                 "finish_reason": "stop"}],
                                    "usage": usage})
        return self._send(404, {"error": "not found"})


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Mock LLM server for the bots")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--latency", type=float, default=0.15)
    parser.add_argument("--dupes", type=float, default=0.0)
    parser.add_argument("--fail", type=float, default=0.0)
    args = parser.parse_args(argv)
    State.latency, State.dupes, State.fail = args.latency, args.dupes, args.fail
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print("mock LLM on http://%s:%d/v1" % (args.host, args.port), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
