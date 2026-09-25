"""The language-model client every bot's words come from.

**Probing.**  "OpenAI compatible" covers half a dozen servers that each keep
their real settings somewhere different, so the probe asks all the places a
setting can live and keeps what answers:

    GET  /v1/models               ids; vLLM's max_model_len; llama.cpp's meta
    GET  /props                   llama.cpp / KoboldCpp: default sampling
                                  settings, the Jinja chat template, BOS/EOS,
                                  n_ctx
    GET  /api/v0/models           LM Studio: loaded model, context length
    GET  /v1/model                TabbyAPI: max_seq_len, prompt template name
    GET  /v1/sampling/override    TabbyAPI: the sampler overrides in force
    GET  /v1/internal/model/info  text-generation-webui
    GET  /api/extra/true_max_context_length   KoboldCpp
    POST /api/show                Ollama: parameters (sampling, stop, num_ctx)

and it finds a tokenizer (``/tokenize``, ``/v1/token/encode``,
``/v1/internal/token-count``, ``/api/extra/tokencount``) to calibrate how many
characters make a token, which is what the context culling counts with.

**Applying it.**  The sampling values pulled from the server are sent with
every request (under the names that server uses), overridden by anything set
in the Bots Zone.  In chat mode the server applies the model's template
itself; in completion mode the template pulled from the server is rendered
here by :mod:`app.bots.template` and its special tokens become stop strings.

**Spending it.**  One model serves every bot, so requests go through a
priority queue -- in-game chat with a person in the round first, private
messages next, a reply to a person's comment after that, bot-to-bot chatter
last -- behind a requests-per-minute budget and a concurrency limit.  Stale
work (a chat reply to a round that has moved on) is dropped rather than
answered late, and a server that keeps failing is backed off from instead of
hammered.
"""
from __future__ import annotations

import heapq
import json
import re
import threading
import time
import urllib.error
import urllib.request
from typing import Any, Callable, Dict, List, Optional, Tuple

from . import config as bot_config
from . import template as chat_template

# priorities: lower runs first
P_CHAT = 0
P_DM = 1
P_REPLY = 2
P_NAMES = 3
P_PROFILE = 4
P_COMMENT = 5
P_POST = 6

KIND_LABELS = {
    "chat": "In-game chat", "dm": "Direct messages", "reply": "Comment replies",
    "names": "Usernames", "profile": "Profiles", "comment": "Chatter",
    "post": "Status posts", "test": "Tests",
}

QUEUE_CAP = {"chat": 60, "dm": 400, "reply": 400, "names": 40,
             "profile": 40, "comment": 60, "post": 40, "test": 5}

SAMPLING_KEYS = ("temperature", "top_p", "top_k", "min_p", "typical_p",
                 "repeat_penalty", "repeat_last_n", "presence_penalty",
                 "frequency_penalty", "tfs_z", "mirostat", "mirostat_tau",
                 "mirostat_eta", "dry_multiplier", "dry_base",
                 "dry_allowed_length", "xtc_probability", "xtc_threshold",
                 "top_n_sigma")
# what each backend calls the same knob
ALIASES = {"repetition_penalty": "repeat_penalty", "rep_pen": "repeat_penalty",
           "penalty_repeat": "repeat_penalty", "typical": "typical_p",
           "tfs": "tfs_z", "num_ctx": "n_ctx", "rep_pen_range": "repeat_last_n"}

SPECIAL_TOKEN_RE = re.compile(
    r"<\|[A-Za-z0-9_\-]{1,40}\|>|</s>|<(?:start|end)_of_turn>|\[/INST\]|"
    r"<\|?eot_id\|?>|<\|endoftext\|>")

CALIBRATION_TEXT = (
    "yo anyone want to play burger tycoon later? i finally got the golden "
    "arches lol. gg on capture the flag btw, that last capture was insane. "
    "Hey! Thanks for the friend request :) your hat is so cool, where did "
    "you get it? I have been trying to get an Unusual for weeks now.")


class LLMError(Exception):
    pass


def _now() -> float:
    return time.time()


class Client:
    """Probe results, the request path and the work queue."""

    def __init__(self):
        self.lock = threading.RLock()
        self.info: Dict[str, Any] = {"reachable": False, "probed_at": 0,
                                     "notes": [], "errors": [],
                                     "sampling": {}, "models": [],
                                     "template": "", "context": 0,
                                     "backend": "", "chars_per_token": 3.6}
        self.queue: List[Tuple[int, int, "Job"]] = []
        self.seq = 0
        self.cond = threading.Condition(self.lock)
        self.workers: List[threading.Thread] = []
        self.running = True
        self.tokens = 0.0
        self.token_at = _now()
        self.failures = 0
        self.down_until = 0.0
        self.active = 0
        self.stats: Dict[str, Dict[str, float]] = {}
        self.recent: List[Dict[str, Any]] = []
        self.minute: List[float] = []
        self._probe_lock = threading.Lock()
        self._settings_seen = None

    # ================================================================ http
    def _endpoint(self) -> Tuple[str, str, str]:
        base = (bot_config.get("llm.base_url") or "").strip().rstrip("/")
        if base and not re.match(r"^https?://", base):
            base = "http://" + base
        root = re.sub(r"/v1$", "", base)
        return base, root, bot_config.get("llm.api_key") or ""

    def _http(self, method: str, url: str, body: Any = None,
              timeout: float = 10.0) -> Tuple[int, Any]:
        _base, _root, key = self._endpoint()
        data = None
        headers = {"Accept": "application/json", "User-Agent": "BLOCKHAVEN-bots"}
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if key:
            headers["Authorization"] = "Bearer %s" % key
        request = urllib.request.Request(url, data=data, method=method,
                                         headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw = response.read(8 * 1024 * 1024)
                status = response.status
        except urllib.error.HTTPError as exc:
            try:
                raw = exc.read(64 * 1024)
            except Exception:
                raw = b""
            status = exc.code
        text = raw.decode("utf-8", "replace")
        try:
            return status, json.loads(text)
        except ValueError:
            return status, text

    def _try(self, method: str, url: str, body: Any = None,
             timeout: float = 6.0) -> Optional[Any]:
        try:
            status, payload = self._http(method, url, body, timeout)
        except Exception:
            return None
        if status >= 400:
            return None
        return payload

    # =============================================================== probe
    def probe(self, force: bool = False) -> Dict[str, Any]:
        """Ask the server everything it will tell us.  Safe to call often:
        it runs at most once at a time and is skipped when recent."""
        if not force and _now() - float(self.info.get("probed_at") or 0) < 300 \
                and self.info.get("reachable"):
            return self.info
        if not self._probe_lock.acquire(blocking=False):
            return self.info
        try:
            info = self._probe()
            with self.lock:
                self.info = info
                if info["reachable"]:
                    self.failures = 0
                    self.down_until = 0.0
            return info
        finally:
            self._probe_lock.release()

    def _probe(self) -> Dict[str, Any]:
        base, root, _key = self._endpoint()
        wanted = (bot_config.get("llm.model") or "").strip()
        info: Dict[str, Any] = {"reachable": False, "probed_at": int(_now()),
                                "base": base, "notes": [], "errors": [],
                                "sampling": {}, "sampling_source": {},
                                "models": [], "model": wanted, "template": "",
                                "template_source": "", "bos": "", "eos": "",
                                "stop": [], "context": 0, "context_source": "",
                                "backend": "openai-compatible", "tokenizer": "",
                                "chars_per_token": 3.6, "rep_key": "repeat_penalty"}
        if not base:
            info["errors"].append("No endpoint configured.")
            return info

        def note(text: str) -> None:
            info["notes"].append(text)

        def take_sampling(values: Dict[str, Any], source: str) -> None:
            for key, value in (values or {}).items():
                name = ALIASES.get(key, key)
                if name == "n_ctx":
                    continue
                if name in SAMPLING_KEYS and isinstance(value, (int, float)) \
                        and not isinstance(value, bool):
                    info["sampling"][name] = value
                    info["sampling_source"][name] = source

        def take_context(value: Any, source: str) -> None:
            try:
                number = int(value)
            except (TypeError, ValueError):
                return
            if number > 0 and (not info["context"] or number < info["context"]
                               or source.startswith("loaded")):
                info["context"] = number
                info["context_source"] = source

        # ---- /v1/models
        models = self._try("GET", base + "/models")
        if isinstance(models, dict) and isinstance(models.get("data"), list):
            info["reachable"] = True
            for entry in models["data"]:
                if not isinstance(entry, dict) or not entry.get("id"):
                    continue
                info["models"].append(str(entry["id"]))
                if wanted and entry["id"] != wanted:
                    continue
                for key in ("max_model_len", "context_length",
                            "max_context_length", "context_window"):
                    if entry.get(key):
                        take_context(entry[key], "/v1/models %s" % key)
                meta = entry.get("meta") or {}
                if isinstance(meta, dict) and meta.get("n_ctx_train"):
                    take_context(meta["n_ctx_train"], "/v1/models meta")
            note("%d model(s) listed" % len(info["models"]))
        elif models is not None:
            info["reachable"] = True

        # ---- llama.cpp / KoboldCpp /props
        props = self._try("GET", root + "/props")
        if isinstance(props, dict) and props:
            info["reachable"] = True
            settings = props.get("default_generation_settings") or {}
            if isinstance(settings, dict):
                params = settings.get("params") if isinstance(
                    settings.get("params"), dict) else settings
                take_sampling(params, "/props")
                if settings.get("n_ctx"):
                    take_context(settings["n_ctx"], "loaded /props n_ctx")
                stops = params.get("stop") if isinstance(params, dict) else None
                if isinstance(stops, list):
                    info["stop"].extend(str(s) for s in stops if s)
            if props.get("n_ctx"):
                take_context(props["n_ctx"], "loaded /props n_ctx")
            if isinstance(props.get("chat_template"), str) and props["chat_template"]:
                info["template"] = props["chat_template"]
                info["template_source"] = "/props"
            for key in ("bos_token", "eos_token"):
                if isinstance(props.get(key), str):
                    info[key[:3]] = props[key]
            info["backend"] = "llama.cpp" if "total_slots" in props else "llama.cpp-like"
            if props.get("model_path"):
                note("model file %s" % str(props["model_path"]).split("/")[-1])

        # ---- LM Studio REST
        lms = self._try("GET", root + "/api/v0/models")
        if isinstance(lms, dict) and isinstance(lms.get("data"), list):
            info["reachable"] = True
            info["backend"] = "LM Studio"
            loaded = [m for m in lms["data"] if isinstance(m, dict)
                      and m.get("state") == "loaded" and m.get("type") in
                      (None, "llm", "vlm")]
            chosen = None
            for entry in loaded:
                if not wanted or entry.get("id") == wanted:
                    chosen = entry
                    break
            if chosen:
                if not wanted:
                    info["model"] = chosen.get("id", "")
                for key in ("loaded_context_length", "context_length"):
                    if chosen.get(key):
                        take_context(chosen[key], "loaded LM Studio %s" % key)
                if chosen.get("max_context_length") and not info["context"]:
                    take_context(chosen["max_context_length"],
                                 "LM Studio max_context_length")
                note("LM Studio has %s loaded" % chosen.get("id"))

        # ---- TabbyAPI
        tabby = self._try("GET", base + "/model")
        if isinstance(tabby, dict) and isinstance(tabby.get("parameters"), dict):
            info["reachable"] = True
            info["backend"] = "TabbyAPI"
            params = tabby["parameters"]
            if params.get("max_seq_len"):
                take_context(params["max_seq_len"], "loaded TabbyAPI max_seq_len")
            if not wanted and tabby.get("id"):
                info["model"] = tabby["id"]
            if params.get("prompt_template"):
                note("TabbyAPI template %s" % params["prompt_template"])
            overrides = self._try("GET", base + "/sampling/override")
            if isinstance(overrides, dict):
                values = {}
                for key, value in (overrides.get("overrides") or {}).items():
                    if isinstance(value, dict) and "override" in value:
                        values[key] = value["override"]
                take_sampling(values, "TabbyAPI overrides")

        # ---- text-generation-webui
        ooba = self._try("GET", base + "/internal/model/info")
        if isinstance(ooba, dict) and "model_name" in ooba:
            info["reachable"] = True
            info["backend"] = "text-generation-webui"
            if not wanted and ooba.get("model_name"):
                info["model"] = ooba["model_name"]
            info["rep_key"] = "repetition_penalty"

        # ---- KoboldCpp
        kobold = self._try("GET", root + "/api/extra/true_max_context_length")
        if isinstance(kobold, dict) and kobold.get("value"):
            info["reachable"] = True
            info["backend"] = "KoboldCpp"
            take_context(kobold["value"], "loaded KoboldCpp context")

        # ---- Ollama
        if info["model"] or info["models"]:
            name = info["model"] or info["models"][0]
            show = self._try("POST", root + "/api/show", {"model": name})
            if isinstance(show, dict) and ("parameters" in show or "model_info" in show):
                info["reachable"] = True
                info["backend"] = "Ollama"
                values: Dict[str, Any] = {}
                for line in str(show.get("parameters") or "").splitlines():
                    parts = line.split(None, 1)
                    if len(parts) != 2:
                        continue
                    key, raw = parts[0], parts[1].strip().strip('"')
                    if key == "stop":
                        info["stop"].append(raw)
                    elif key == "num_ctx":
                        take_context(raw, "loaded Ollama num_ctx")
                    else:
                        try:
                            values[key] = float(raw) if "." in raw else int(raw)
                        except ValueError:
                            pass
                take_sampling(values, "Ollama parameters")
                for key, value in (show.get("model_info") or {}).items():
                    if key.endswith(".context_length") and not info["context"]:
                        take_context(value, "Ollama context_length")

        if info["backend"] in ("text-generation-webui",):
            info["rep_key"] = "repetition_penalty"
        if not info["model"] and info["models"]:
            info["model"] = info["models"][0]

        # ---- tokenizer, for calibrating the culling
        if info["reachable"]:
            info.update(self._calibrate(base, root, info["model"]))

        if not info["reachable"]:
            info["errors"].append("The endpoint did not answer.")
        elif not info["template"]:
            note("no chat template reported: chat mode lets the server apply it")
        return info

    def _calibrate(self, base: str, root: str, model: str) -> Dict[str, Any]:
        text = CALIBRATION_TEXT
        attempts = [
            ("llama.cpp /tokenize", "POST", root + "/tokenize",
             {"content": text}, lambda r: len(r.get("tokens") or [])),
            ("vLLM /tokenize", "POST", root + "/tokenize",
             {"model": model, "prompt": text}, lambda r: r.get("count")),
            ("TabbyAPI /token/encode", "POST", base + "/token/encode",
             {"text": text}, lambda r: r.get("length") or len(r.get("tokens") or [])),
            ("text-generation-webui token-count", "POST",
             base + "/internal/token-count", {"text": text},
             lambda r: r.get("length")),
            ("KoboldCpp tokencount", "POST", root + "/api/extra/tokencount",
             {"prompt": text}, lambda r: r.get("value")),
        ]
        for label, method, url, body, read in attempts:
            result = self._try(method, url, body, timeout=5)
            if not isinstance(result, dict):
                continue
            try:
                count = int(read(result) or 0)
            except (TypeError, ValueError):
                count = 0
            if count > 10:
                return {"tokenizer": label,
                        "chars_per_token": round(len(text) / count, 3)}
        return {"tokenizer": "", "chars_per_token": 3.6}

    # ============================================================= helpers
    def context_limit(self) -> int:
        limit = int(bot_config.get("llm.context_limit") or 16000)
        server = int(self.info.get("context") or 0)
        if server and bot_config.get("llm.respect_server_context"):
            limit = min(limit, server)
        return max(256, limit)

    def estimate_tokens(self, text: str) -> int:
        ratio = float(self.info.get("chars_per_token") or 3.6)
        return int(len(text or "") / max(1.2, ratio)) + 4

    def sampling(self) -> Dict[str, Any]:
        """Server defaults, then the Bots Zone's overrides on top."""
        values: Dict[str, Any] = dict(self.info.get("sampling") or {})
        for key in ("temperature", "top_p", "top_k", "min_p", "repeat_penalty",
                    "presence_penalty", "frequency_penalty"):
            override = bot_config.get("llm." + key)
            if override is not None:
                values[key] = override
        return values

    def _body_sampling(self) -> Dict[str, Any]:
        values = self.sampling()
        rep_key = self.info.get("rep_key") or "repeat_penalty"
        out: Dict[str, Any] = {}
        for key, value in values.items():
            if key == "repeat_penalty":
                out[rep_key] = value
            else:
                out[key] = value
        return out

    def stops(self, mode: str) -> List[str]:
        out = [s for s in (self.info.get("stop") or []) if s]
        out += list(bot_config.get("llm.stop") or [])
        if mode == "completion":
            if self.info.get("eos"):
                out.append(self.info["eos"])
            for token in SPECIAL_TOKEN_RE.findall(self.info.get("template") or ""):
                out.append(token)
        seen, clean = set(), []
        for stop in out:
            if stop and stop not in seen:
                seen.add(stop)
                clean.append(stop)
        return clean[:16]

    # ============================================================ requests
    def complete(self, messages: List[Dict[str, str]], max_tokens: int,
                 timeout: Optional[float] = None) -> Dict[str, Any]:
        """One request, synchronously.  Returns {"text", "prompt_tokens", ...}."""
        base, _root, _key = self._endpoint()
        if not base:
            raise LLMError("no endpoint configured")
        mode = bot_config.get("llm.mode") or "auto"
        timeout = timeout or float(bot_config.get("llm.timeout_seconds") or 90)
        model = bot_config.get("llm.model") or self.info.get("model") or ""
        if mode == "completion" or (mode == "auto" and self.info.get("prefer_completion")):
            return self._completion(base, model, messages, max_tokens, timeout)
        try:
            return self._chat(base, model, messages, max_tokens, timeout)
        except LLMError as exc:
            if mode == "auto" and getattr(exc, "status", 0) in (404, 405, 501) \
                    and self.info.get("template"):
                self.info["prefer_completion"] = True
                return self._completion(base, model, messages, max_tokens, timeout)
            raise

    def _chat(self, base, model, messages, max_tokens, timeout):
        body: Dict[str, Any] = {"messages": messages, "max_tokens": int(max_tokens),
                                "stream": False}
        if model:
            body["model"] = model
        body.update(self._body_sampling())
        stops = self.stops("chat")
        if stops:
            body["stop"] = stops
        started = _now()
        status, payload = self._http("POST", base + "/chat/completions", body,
                                     timeout)
        if status >= 400 and _mentions_roles(payload):
            # a template that refuses a system turn (Gemma, early Mistral):
            # fold it into the first user message and ask again
            body["messages"] = fold_system(messages)
            status, payload = self._http("POST", base + "/chat/completions",
                                         body, timeout)
        if status >= 400 or not isinstance(payload, dict):
            error = LLMError("HTTP %s: %s" % (status, str(payload)[:200]))
            error.status = status  # type: ignore[attr-defined]
            raise error
        choice = (payload.get("choices") or [{}])[0]
        message = choice.get("message") or {}
        text = message.get("content")
        if text is None:
            text = choice.get("text") or ""
        usage = payload.get("usage") or {}
        return {"text": str(text), "prompt_tokens": usage.get("prompt_tokens"),
                "completion_tokens": usage.get("completion_tokens"),
                "ms": int((_now() - started) * 1000), "mode": "chat",
                "finish": choice.get("finish_reason")}

    def _completion(self, base, model, messages, max_tokens, timeout):
        source = self.info.get("template") or ""
        if not source:
            raise LLMError("completion mode needs a chat template from the server")
        try:
            prompt = chat_template.render_chat(
                source, messages, True, self.info.get("bos") or "",
                self.info.get("eos") or "")
        except chat_template.RaisedError:
            prompt = chat_template.render_chat(
                source, fold_system(messages), True,
                self.info.get("bos") or "", self.info.get("eos") or "")
        except chat_template.TemplateError as exc:
            raise LLMError("chat template failed: %s" % exc)
        body: Dict[str, Any] = {"prompt": prompt, "max_tokens": int(max_tokens),
                                "stream": False}
        if model:
            body["model"] = model
        body.update(self._body_sampling())
        stops = self.stops("completion")
        if stops:
            body["stop"] = stops
        started = _now()
        status, payload = self._http("POST", base + "/completions", body, timeout)
        if status >= 400 or not isinstance(payload, dict):
            error = LLMError("HTTP %s: %s" % (status, str(payload)[:200]))
            error.status = status  # type: ignore[attr-defined]
            raise error
        choice = (payload.get("choices") or [{}])[0]
        usage = payload.get("usage") or {}
        return {"text": str(choice.get("text") or ""),
                "prompt_tokens": usage.get("prompt_tokens"),
                "completion_tokens": usage.get("completion_tokens"),
                "ms": int((_now() - started) * 1000), "mode": "completion",
                "finish": choice.get("finish_reason"), "prompt_chars": len(prompt)}

    # =============================================================== queue
    def available(self) -> bool:
        return bool(bot_config.get("llm.enabled")) and \
            bool((bot_config.get("llm.base_url") or "").strip()) and \
            _now() >= self.down_until

    def pressure(self) -> float:
        """0 when idle, 1 when the queue is as long as it should get."""
        with self.lock:
            depth = len(self.queue)
        cap = max(4, int(bot_config.get("llm.concurrency") or 2) * 6)
        return min(1.0, depth / float(cap))

    def submit(self, kind: str, priority: int, build: Callable[[], Optional[Dict[str, Any]]],
               done: Callable[[Optional[str], Optional[str]], None],
               ttl: float = 600.0, bot: int = 0) -> bool:
        """Queue one request.  ``build`` makes the prompt when its turn comes
        (so the context is fresh), ``done(text, error)`` gets the answer."""
        if not self.available():
            return False
        with self.lock:
            waiting = sum(1 for _p, _s, job in self.queue if job.kind == kind)
            if waiting >= QUEUE_CAP.get(kind, 100):
                self._stat(kind, "dropped")
                return False
            self.seq += 1
            job = Job(kind, priority, build, done, _now() + ttl, bot)
            heapq.heappush(self.queue, (priority, self.seq, job))
            self._stat(kind, "queued")
            self._ensure_workers()
            self.cond.notify()
        return True

    def _ensure_workers(self) -> None:
        wanted = max(1, min(32, int(bot_config.get("llm.concurrency") or 2)))
        self.workers = [w for w in self.workers if w.is_alive()]
        while len(self.workers) < wanted:
            worker = threading.Thread(target=self._work, daemon=True,
                                      name="bots-llm-%d" % len(self.workers))
            worker.start()
            self.workers.append(worker)

    def _take_token(self) -> float:
        """Seconds to wait before the budget allows another request."""
        rate = max(1.0, float(bot_config.get("llm.requests_per_minute") or 60)) / 60.0
        now = _now()
        self.tokens = min(max(1.0, rate * 3), self.tokens + (now - self.token_at) * rate)
        self.token_at = now
        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return 0.0
        return (1.0 - self.tokens) / rate

    def _work(self) -> None:
        index = len(self.workers)
        while self.running:
            with self.lock:
                wanted = max(1, int(bot_config.get("llm.concurrency") or 2))
                if index > wanted:
                    return
                while not self.queue and self.running:
                    self.cond.wait(5.0)
                if not self.queue:
                    continue
                wait = self._take_token()
                if wait > 0:
                    self.cond.wait(min(wait, 2.0))
                    continue
                _prio, _seq, job = heapq.heappop(self.queue)
                self.active += 1
            try:
                self._run(job)
            finally:
                with self.lock:
                    self.active -= 1

    def _run(self, job: "Job") -> None:
        if _now() > job.deadline:
            self._stat(job.kind, "expired")
            _safe_call(job.done, None, "expired")
            return
        if _now() < self.down_until:
            self._stat(job.kind, "failed")
            _safe_call(job.done, None, "model unavailable")
            return
        try:
            spec = job.build()
        except Exception as exc:
            spec = None
            _safe_call(job.done, None, "prompt failed: %s" % exc)
            return
        if not spec:
            self._stat(job.kind, "skipped")
            _safe_call(job.done, None, "skipped")
            return
        started = _now()
        try:
            result = self.complete(spec["messages"], spec.get("max_tokens", 120))
        except Exception as exc:
            self.failures += 1
            if self.failures >= 3:
                backoff = min(300.0, 15.0 * (2 ** min(5, self.failures - 3)))
                self.down_until = _now() + backoff
            self._stat(job.kind, "failed")
            self._remember(job.kind, spec, None, str(exc), started)
            _safe_call(job.done, None, str(exc))
            return
        self.failures = 0
        self._learn_ratio(spec, result)
        text = clean_output(result.get("text") or "")
        self._stat(job.kind, "ok", (_now() - started) * 1000.0,
                   int(result.get("completion_tokens") or 0))
        self._remember(job.kind, spec, text, None, started)
        _safe_call(job.done, text, None)

    def _learn_ratio(self, spec: Dict[str, Any], result: Dict[str, Any]) -> None:
        """Keep the chars-per-token estimate honest from real usage figures."""
        tokens = result.get("prompt_tokens")
        if not tokens or self.info.get("tokenizer"):
            return
        chars = result.get("prompt_chars") or sum(
            len(m.get("content") or "") for m in spec["messages"])
        try:
            ratio = chars / float(tokens)
        except ZeroDivisionError:
            return
        if 1.5 < ratio < 8:
            old = float(self.info.get("chars_per_token") or 3.6)
            self.info["chars_per_token"] = round(old * 0.8 + ratio * 0.2, 3)

    def _stat(self, kind: str, what: str, ms: float = 0.0, tokens: int = 0) -> None:
        with self.lock:
            entry = self.stats.setdefault(kind, {
                "queued": 0, "ok": 0, "failed": 0, "dropped": 0, "expired": 0,
                "skipped": 0, "ms": 0.0, "tokens": 0})
            entry[what] = entry.get(what, 0) + 1
            if what == "ok":
                entry["ms"] = entry["ms"] * 0.9 + ms * 0.1 if entry["ok"] > 1 else ms
                entry["tokens"] += tokens
                self.minute.append(_now())
                cutoff = _now() - 60
                while self.minute and self.minute[0] < cutoff:
                    self.minute.pop(0)

    def _remember(self, kind, spec, text, error, started) -> None:
        with self.lock:
            prompt = spec["messages"][-1].get("content", "") if spec.get("messages") else ""
            self.recent.append({"kind": kind, "at": int(started),
                                "ms": int((_now() - started) * 1000),
                                "prompt": prompt[-240:], "reply": (text or "")[:240],
                                "error": (error or "")[:240]})
            del self.recent[:-30]

    def snapshot(self) -> Dict[str, Any]:
        with self.lock:
            depth: Dict[str, int] = {}
            for _p, _s, job in self.queue:
                depth[job.kind] = depth.get(job.kind, 0) + 1
            info = {k: v for k, v in self.info.items() if k != "template"}
            info["template_chars"] = len(self.info.get("template") or "")
            return {
                "info": info,
                "available": self.available(),
                "enabled": bool(bot_config.get("llm.enabled")),
                "down_for": max(0, int(self.down_until - _now())),
                "failures": self.failures,
                "queue": depth,
                "active": self.active,
                "per_minute": len(self.minute),
                "stats": {k: dict(v) for k, v in self.stats.items()},
                "recent": list(self.recent[-12:]),
                "context_limit": self.context_limit(),
                "sampling": self.sampling(),
                "labels": KIND_LABELS,
            }

    def template_text(self) -> str:
        return self.info.get("template") or ""


class Job:
    __slots__ = ("kind", "priority", "build", "done", "deadline", "bot")

    def __init__(self, kind, priority, build, done, deadline, bot):
        self.kind, self.priority, self.build = kind, priority, build
        self.done, self.deadline, self.bot = done, deadline, bot

    def __lt__(self, other):
        return False


def _safe_call(func, *args) -> None:
    try:
        func(*args)
    except Exception:
        import traceback
        traceback.print_exc()


def _mentions_roles(payload: Any) -> bool:
    text = json.dumps(payload) if not isinstance(payload, str) else payload
    text = text.lower()
    return ("system" in text and ("role" in text or "not supported" in text)) \
        or "alternate" in text


def fold_system(messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Merge the system turn into the first user turn, and make the rest
    strictly alternate, for templates that insist on it."""
    system = "\n\n".join(m["content"] for m in messages if m["role"] == "system")
    rest = [dict(m) for m in messages if m["role"] != "system"]
    merged: List[Dict[str, str]] = []
    for message in rest:
        if merged and merged[-1]["role"] == message["role"]:
            merged[-1]["content"] += "\n" + message["content"]
        else:
            merged.append(message)
    if not merged or merged[0]["role"] != "user":
        merged.insert(0, {"role": "user", "content": "(conversation start)"})
    if system:
        merged[0]["content"] = system + "\n\n" + merged[0]["content"]
    return merged


_THINK_RE = re.compile(r"<think>.*?</think>|<thinking>.*?</thinking>|"
                       r"<\|channel\|>analysis.*?<\|end\|>", re.S | re.I)


def clean_output(text: str) -> str:
    text = text or ""
    if bot_config.get("llm.strip_reasoning"):
        text = _THINK_RE.sub("", text)
        if "</think>" in text:
            text = text.split("</think>", 1)[1]
        if text.lstrip().lower().startswith("<think>"):
            text = ""
    text = SPECIAL_TOKEN_RE.sub("", text)
    return text.strip()


_client: Optional[Client] = None
_client_lock = threading.Lock()


def client() -> Client:
    global _client
    with _client_lock:
        if _client is None:
            _client = Client()
        return _client
