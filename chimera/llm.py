"""Meta Model API client (stdlib only) for Muse Spark.

A small, dependency-free client for the OpenAI-compatible Chat
Completions endpoint of the Meta Model API
(``POST https://api.meta.ai/v1/chat/completions``, bearer auth).

Used by the model-driven benchmark baseline (``benchmarks.baseline_b``)
and the Workflow Studio planner (``workbench.planner``). The model is
only ever a *proposer*: nothing in this module, or in its callers,
lets a model's output decide whether a task succeeded. That verdict
always comes from Chimera's deterministic, model-free verifier.

Configuration
-------------
* ``MODEL_API_KEY`` — the API key. Read from the process environment,
  else from a project-root ``.env`` file (``KEY=VALUE`` lines; the file
  is git-ignored). Never printed, logged, persisted, or included in any
  exception text: every error message is passed through
  :func:`redact` before it is raised.
* ``MODEL_API_BASE`` — base URL override (default
  ``https://api.meta.ai/v1``).
* ``CHIMERA_MODEL`` — model override (default ``muse-spark-1.3``).
* ``CHIMERA_REASONING_EFFORT`` — optional ``reasoning_effort`` sent with
  each request (``low`` etc.; ``default``/empty omits it). Muse Spark is
  a reasoning model: reasoning tokens count against
  ``max_completion_tokens``.

Robustness
----------
* Bounded retries with exponential backoff (+ jitter, honouring
  ``Retry-After``) on 429, 500, 502, 503 and transport timeouts /
  connection errors. Never on other 4xx.
* Optional request parameters (``response_format``, ``reasoning_effort``,
  ``temperature``) are dropped — once, and remembered for the client's
  lifetime — when the API rejects them with HTTP 400, so an endpoint
  that lacks JSON mode still works. Callers always parse robustly:
  :func:`extract_json_object` takes the first JSON object out of free
  text (code fences, leading prose, trailing commentary).
* The HTTP transport is injectable (:class:`FakeTransport` for tests);
  no test needs a key or the network.
"""

from __future__ import annotations

import json
import os
import random
import socket
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

#: Defaults (overridable via environment / ``.env``).
DEFAULT_API_BASE = "https://api.meta.ai/v1"
DEFAULT_MODEL = "muse-spark-1.3"

ENV_API_KEY = "MODEL_API_KEY"
ENV_API_BASE = "MODEL_API_BASE"
ENV_MODEL = "CHIMERA_MODEL"
ENV_REASONING_EFFORT = "CHIMERA_REASONING_EFFORT"

#: Project-root ``.env`` (git-ignored).
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DOTENV = PROJECT_ROOT / ".env"

#: HTTP statuses retried with backoff (Meta error-handling guide: 429,
#: 500, 503 are retryable; 502 is a transient gateway error).
RETRYABLE_STATUSES: Tuple[int, ...] = (429, 500, 502, 503)

DEFAULT_MAX_RETRIES = 3
DEFAULT_TIMEOUT_SECONDS = 60.0
DEFAULT_BACKOFF_BASE_SECONDS = 0.75
MAX_BACKOFF_SECONDS = 20.0
MAX_RETRY_AFTER_SECONDS = 30.0

#: Optional request parameters that are dropped if the API rejects them.
OPTIONAL_PARAMS: Tuple[str, ...] = ("response_format", "reasoning_effort",
                                    "temperature")

REDACTED = "[REDACTED]"


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class LLMError(RuntimeError):
    """Base class for model-client failures (messages are key-redacted)."""


class MissingAPIKeyError(LLMError):
    """No API key in the environment or the project ``.env`` file."""


class LLMHTTPError(LLMError):
    """The API returned a non-success HTTP status."""

    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status


class LLMTimeoutError(LLMError):
    """The request timed out (after all retries)."""


class LLMResponseError(LLMError):
    """The API returned a body the client cannot interpret."""


class TransportError(Exception):
    """A transport-level failure (connection refused, DNS, reset ...)."""


class TransportTimeout(TransportError):
    """A transport-level timeout."""


# ---------------------------------------------------------------------------
# Key handling
# ---------------------------------------------------------------------------


def redact(text: Any, secret: Optional[str]) -> str:
    """Remove ``secret`` (and an ``Authorization`` value) from ``text``."""
    out = str(text)
    if secret:
        out = out.replace(secret, REDACTED)
    return out


def parse_dotenv(text: str) -> Dict[str, str]:
    """Parse simple ``KEY=VALUE`` lines (``export`` prefix and quotes ok).

    Blank lines and ``#`` comments are ignored; malformed lines are
    skipped silently (their content is never echoed — it may be a key).
    """
    values: Dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].lstrip()
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if not key or not key.replace("_", "").isalnum():
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        else:
            # Strip an inline comment only when unquoted and space-led.
            hash_at = value.find(" #")
            if hash_at >= 0:
                value = value[:hash_at].rstrip()
        values[key] = value
    return values


def load_dotenv_values(path: Optional[Path] = None) -> Dict[str, str]:
    """Read the project ``.env`` (missing/unreadable file → ``{}``)."""
    target = Path(path) if path is not None else DEFAULT_DOTENV
    try:
        return parse_dotenv(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError):
        return {}


def _setting(name: str, env: Mapping[str, str],
             dotenv: Mapping[str, str]) -> Optional[str]:
    value = env.get(name)
    if value is not None and value.strip():
        return value.strip()
    value = dotenv.get(name)
    if value is not None and value.strip():
        return value.strip()
    return None


@dataclass(frozen=True)
class ModelSettings:
    """Resolved configuration. ``api_key`` is excluded from ``repr``."""

    api_key: Optional[str] = field(repr=False)
    api_base: str
    model: str
    reasoning_effort: Optional[str]
    key_source: str  # "env" | "dotenv" | "explicit" | "none"

    def describe(self) -> Dict[str, Any]:
        """A key-free description safe to persist in results."""
        return {"api_base": self.api_base, "model": self.model,
                "reasoning_effort": self.reasoning_effort,
                "key_present": bool(self.api_key),
                "key_source": self.key_source}


def resolve_settings(*, env: Optional[Mapping[str, str]] = None,
                     dotenv_path: Optional[Path] = None) -> ModelSettings:
    """Resolve key/base/model from the environment, then ``.env``."""
    env = os.environ if env is None else env
    dotenv = load_dotenv_values(dotenv_path)
    key = None
    source = "none"
    env_key = env.get(ENV_API_KEY)
    if env_key and env_key.strip():
        key, source = env_key.strip(), "env"
    elif dotenv.get(ENV_API_KEY, "").strip():
        key, source = dotenv[ENV_API_KEY].strip(), "dotenv"
    base = _setting(ENV_API_BASE, env, dotenv) or DEFAULT_API_BASE
    model = _setting(ENV_MODEL, env, dotenv) or DEFAULT_MODEL
    effort = _setting(ENV_REASONING_EFFORT, env, dotenv)
    if effort is not None and effort.lower() in ("default", "none-sent", ""):
        effort = None
    return ModelSettings(api_key=key, api_base=base.rstrip("/"), model=model,
                         reasoning_effort=effort, key_source=source)


def api_key_available(*, env: Optional[Mapping[str, str]] = None,
                      dotenv_path: Optional[Path] = None) -> bool:
    """Whether a key is configured (never returns or prints the key)."""
    return bool(resolve_settings(env=env, dotenv_path=dotenv_path).api_key)


# ---------------------------------------------------------------------------
# JSON extraction
# ---------------------------------------------------------------------------


def extract_json_object(text: Any) -> Optional[Dict[str, Any]]:
    """Return the first JSON *object* found in ``text``, else ``None``.

    Accepts a bare object, an object inside a Markdown code fence, or
    an object surrounded by prose. Arrays and scalars are not objects
    and yield ``None``. Never raises.
    """
    if isinstance(text, dict):
        return text
    if not isinstance(text, str):
        return None
    candidate = text.strip()
    if not candidate:
        return None
    try:
        value = json.loads(candidate)
    except (ValueError, RecursionError):
        value = None
    if isinstance(value, dict):
        return value
    decoder = json.JSONDecoder()
    # Prefer fenced blocks, then any '{' position, in order.
    starts: List[int] = []
    fence = candidate.find("```")
    while fence >= 0:
        brace = candidate.find("{", fence)
        if brace >= 0:
            starts.append(brace)
        fence = candidate.find("```", fence + 3)
    index = candidate.find("{")
    while index >= 0:
        starts.append(index)
        index = candidate.find("{", index + 1)
    seen = set()
    for start in starts:
        if start in seen:
            continue
        seen.add(start)
        try:
            value, _end = decoder.raw_decode(candidate, start)
        except (ValueError, RecursionError):
            continue
        if isinstance(value, dict):
            return value
    return None


# ---------------------------------------------------------------------------
# Transport
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class HTTPResponse:
    status: int
    headers: Mapping[str, str]
    body: bytes


#: ``transport(url, headers, body, timeout) -> HTTPResponse``. Raises
#: :class:`TransportTimeout` / :class:`TransportError` on network failure.
Transport = Callable[[str, Mapping[str, str], bytes, float], HTTPResponse]


def urllib_transport(url: str, headers: Mapping[str, str], body: bytes,
                     timeout: float) -> HTTPResponse:
    """The default transport: one POST via :mod:`urllib.request`."""
    request = urllib.request.Request(url, data=body, method="POST",
                                     headers=dict(headers))
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return HTTPResponse(status=response.status,
                                headers={k.lower(): v for k, v
                                         in response.headers.items()},
                                body=response.read())
    except urllib.error.HTTPError as exc:
        try:
            payload = exc.read()
        except Exception:  # noqa: BLE001 — body is best effort
            payload = b""
        hdrs = {k.lower(): v for k, v in (exc.headers or {}).items()}
        return HTTPResponse(status=exc.code, headers=hdrs, body=payload)
    except (socket.timeout, TimeoutError) as exc:
        raise TransportTimeout(f"request timed out after {timeout}s") from exc
    except urllib.error.URLError as exc:
        reason = exc.reason
        if isinstance(reason, (socket.timeout, TimeoutError)):
            raise TransportTimeout(
                f"request timed out after {timeout}s") from exc
        raise TransportError(f"connection failed: {reason}") from exc
    except (ConnectionError, OSError) as exc:
        raise TransportError(f"connection failed: {exc}") from exc


class FakeTransport:
    """A scripted transport for tests and dry runs (no network).

    ``responses`` is a sequence whose items are an :class:`HTTPResponse`,
    an exception instance (raised), a ``dict`` (returned as a 200 JSON
    body), or a callable ``(request_json) -> any of the above``. The
    last item repeats once the script is exhausted. Every request is
    recorded in :attr:`requests` (headers included, so tests can prove
    the key is only ever in the ``Authorization`` header).
    """

    def __init__(self, responses: Sequence[Any]) -> None:
        if not responses:
            raise ValueError("FakeTransport needs at least one response")
        self._responses = list(responses)
        self.requests: List[Dict[str, Any]] = []

    def __call__(self, url: str, headers: Mapping[str, str], body: bytes,
                 timeout: float) -> HTTPResponse:
        payload = json.loads(body.decode("utf-8"))
        self.requests.append({"url": url, "headers": dict(headers),
                              "json": payload, "timeout": timeout})
        index = min(len(self.requests) - 1, len(self._responses) - 1)
        item = self._responses[index]
        if callable(item) and not isinstance(item, HTTPResponse):
            item = item(payload)
        if isinstance(item, BaseException):
            raise item
        if isinstance(item, HTTPResponse):
            return item
        if isinstance(item, dict):
            return HTTPResponse(200, {"content-type": "application/json"},
                                json.dumps(item).encode("utf-8"))
        raise TypeError(f"unsupported fake response {type(item).__name__}")


def completion_body(content: str, *, model: str = DEFAULT_MODEL,
                    prompt_tokens: int = 10, completion_tokens: int = 5,
                    reasoning_tokens: Optional[int] = None,
                    response_id: str = "chatcmpl-fake",
                    finish_reason: str = "stop") -> Dict[str, Any]:
    """An OpenAI-compatible chat.completion body (for fakes and tests)."""
    usage: Dict[str, Any] = {"prompt_tokens": prompt_tokens,
                             "completion_tokens": completion_tokens,
                             "total_tokens": prompt_tokens + completion_tokens}
    if reasoning_tokens is not None:
        usage["completion_tokens_details"] = {
            "reasoning_tokens": reasoning_tokens}
    return {
        "id": response_id, "object": "chat.completion", "created": 0,
        "model": model,
        "choices": [{"index": 0, "finish_reason": finish_reason,
                     "logprobs": None,
                     "message": {"role": "assistant", "content": content,
                                 "refusal": None}}],
        "usage": usage,
    }


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ChatResult:
    """One completed chat call.

    ``parsed`` is the first JSON object in ``text`` (or ``None``);
    token counts are ``None`` when the API did not report usage.
    ``attempts`` counts HTTP requests made (retries + param fallbacks).
    """

    text: str
    parsed: Optional[Dict[str, Any]]
    model: str
    request_id: Optional[str]
    latency_ms: int
    prompt_tokens: Optional[int]
    completion_tokens: Optional[int]
    total_tokens: Optional[int]
    reasoning_tokens: Optional[int]
    finish_reason: Optional[str]
    attempts: int
    dropped_params: Tuple[str, ...] = ()

    def usage(self) -> Dict[str, Any]:
        return {"prompt_tokens": self.prompt_tokens,
                "completion_tokens": self.completion_tokens,
                "total_tokens": self.total_tokens,
                "reasoning_tokens": self.reasoning_tokens}


def _int_or_none(value: Any) -> Optional[int]:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return None


def _content_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):  # content parts
        parts = []
        for part in content:
            if isinstance(part, dict) and isinstance(part.get("text"), str):
                parts.append(part["text"])
            elif isinstance(part, str):
                parts.append(part)
        return "".join(parts)
    if isinstance(content, dict) and isinstance(content.get("text"), str):
        return content["text"]
    return ""


def _parse_completion(data: Mapping[str, Any]
                      ) -> Tuple[str, Optional[str], Dict[str, Optional[int]]]:
    """``(text, finish_reason, usage)`` from a completion body.

    Accepts the OpenAI-compatible ``choices[0].message.content`` shape
    and, defensively, a ``completion_message.content`` shape.
    """
    text = ""
    finish: Optional[str] = None
    choices = data.get("choices")
    if isinstance(choices, list) and choices and isinstance(choices[0], dict):
        message = choices[0].get("message") or {}
        if isinstance(message, dict):
            text = _content_text(message.get("content"))
        finish = choices[0].get("finish_reason")
    elif isinstance(data.get("completion_message"), dict):
        message = data["completion_message"]
        text = _content_text(message.get("content"))
        finish = message.get("stop_reason")
    elif isinstance(data.get("output_text"), str):
        text = data["output_text"]
    else:
        raise LLMResponseError(
            "unrecognised completion body: no choices[0].message")
    usage_raw = data.get("usage") if isinstance(data.get("usage"), dict) else {}
    details = usage_raw.get("completion_tokens_details")
    reasoning = (_int_or_none(details.get("reasoning_tokens"))
                 if isinstance(details, dict) else None)
    usage = {
        "prompt_tokens": _int_or_none(usage_raw.get("prompt_tokens")),
        "completion_tokens": _int_or_none(usage_raw.get("completion_tokens")),
        "total_tokens": _int_or_none(usage_raw.get("total_tokens")),
        "reasoning_tokens": reasoning,
    }
    return text, (finish if isinstance(finish, str) else None), usage


def _error_message(body: bytes) -> str:
    try:
        data = json.loads(body.decode("utf-8", errors="replace"))
    except ValueError:
        snippet = body[:300].decode("utf-8", errors="replace")
        return snippet or "(empty body)"
    if isinstance(data, dict):
        err = data.get("error")
        if isinstance(err, dict):
            parts = [str(err.get(k)) for k in ("type", "message", "param")
                     if err.get(k)]
            if parts:
                return "; ".join(parts)
        if isinstance(err, str):
            return err
        if isinstance(data.get("message"), str):
            return data["message"]
    return json.dumps(data)[:300]


class MetaModelClient:
    """Chat Completions client for the Meta Model API.

    The key is held privately and never appears in ``repr``, results,
    or errors. Construct with :meth:`from_env` in production; tests pass
    ``api_key`` and a :class:`FakeTransport`.
    """

    def __init__(
        self,
        *,
        api_key: Optional[str],
        api_base: str = DEFAULT_API_BASE,
        model: str = DEFAULT_MODEL,
        reasoning_effort: Optional[str] = None,
        transport: Optional[Transport] = None,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_base_seconds: float = DEFAULT_BACKOFF_BASE_SECONDS,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
        jitter: Callable[[], float] = random.random,
    ) -> None:
        if not api_key or not str(api_key).strip():
            raise MissingAPIKeyError(
                f"no Meta Model API key: set {ENV_API_KEY} in the "
                f"environment or in {DEFAULT_DOTENV} (git-ignored)")
        self.__key = str(api_key).strip()
        self.api_base = api_base.rstrip("/")
        self.model = model
        self.reasoning_effort = reasoning_effort
        self._transport: Transport = transport or urllib_transport
        self.max_retries = max(0, int(max_retries))
        self.backoff_base_seconds = backoff_base_seconds
        self._sleep = sleep
        self._clock = clock
        self._jitter = jitter
        #: Optional params the endpoint rejected (dropped from now on).
        self.unsupported_params: set = set()

    @classmethod
    def from_env(cls, *, env: Optional[Mapping[str, str]] = None,
                 dotenv_path: Optional[Path] = None,
                 model: Optional[str] = None,
                 **kwargs: Any) -> "MetaModelClient":
        """Build a client from ``MODEL_API_KEY`` / ``.env`` settings."""
        settings = resolve_settings(env=env, dotenv_path=dotenv_path)
        if not settings.api_key:
            raise MissingAPIKeyError(
                f"no Meta Model API key: set {ENV_API_KEY} in the "
                f"environment or in {DEFAULT_DOTENV} (git-ignored)")
        kwargs.setdefault("reasoning_effort", settings.reasoning_effort)
        return cls(api_key=settings.api_key, api_base=settings.api_base,
                   model=model or settings.model, **kwargs)

    def __repr__(self) -> str:
        return (f"MetaModelClient(api_base={self.api_base!r}, "
                f"model={self.model!r}, key=<redacted>)")

    def describe(self) -> Dict[str, Any]:
        """Key-free configuration record for results files."""
        return {"api_base": self.api_base, "model": self.model,
                "reasoning_effort": self.reasoning_effort,
                "max_retries": self.max_retries,
                "unsupported_params": sorted(self.unsupported_params)}

    # -- internals ------------------------------------------------------

    def _redact(self, text: Any) -> str:
        return redact(text, self.__key)

    def _backoff(self, attempt: int, retry_after: Optional[str]) -> float:
        if retry_after:
            try:
                return min(MAX_RETRY_AFTER_SECONDS, max(0.0, float(retry_after)))
            except ValueError:
                pass
        delay = self.backoff_base_seconds * (2 ** attempt) + self._jitter()
        return min(MAX_BACKOFF_SECONDS, delay)

    def _body(self, messages: Sequence[Mapping[str, Any]], *,
              max_tokens: int, temperature: Optional[float],
              json_mode: bool, extra: Optional[Mapping[str, Any]]
              ) -> Dict[str, Any]:
        body: Dict[str, Any] = {
            "model": self.model,
            "messages": [dict(m) for m in messages],
            "max_completion_tokens": int(max_tokens),
        }
        if temperature is not None and "temperature" not in self.unsupported_params:
            body["temperature"] = temperature
        if json_mode and "response_format" not in self.unsupported_params:
            body["response_format"] = {"type": "json_object"}
        if self.reasoning_effort and \
                "reasoning_effort" not in self.unsupported_params:
            body["reasoning_effort"] = self.reasoning_effort
        if extra:
            body.update(dict(extra))
        return body

    def _rejected_param(self, body: Mapping[str, Any], message: str
                        ) -> Optional[str]:
        """Which optional param a 400 most plausibly rejected, if any."""
        lowered = message.lower()
        present = [p for p in OPTIONAL_PARAMS if p in body]
        for param in present:
            if param in lowered:
                return param
        if "response_format" in present and ("json" in lowered
                                             or "format" in lowered):
            return "response_format"
        if "reasoning_effort" in present and ("reasoning" in lowered
                                              or "effort" in lowered):
            return "reasoning_effort"
        return None

    # -- public ---------------------------------------------------------

    def chat(
        self,
        messages: Sequence[Mapping[str, Any]],
        *,
        max_tokens: int = 1024,
        temperature: Optional[float] = 0.0,
        json_mode: bool = True,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        extra: Optional[Mapping[str, Any]] = None,
    ) -> ChatResult:
        """Send one chat completion request and return the parsed result.

        ``max_tokens`` is sent as ``max_completion_tokens`` (it caps
        reasoning + visible tokens). Raises :class:`LLMHTTPError`,
        :class:`LLMTimeoutError`, or :class:`LLMResponseError`, all with
        key-redacted messages.
        """
        if not messages:
            raise ValueError("messages must be a non-empty sequence")
        url = f"{self.api_base}/chat/completions"
        headers = {"Authorization": f"Bearer {self.__key}",
                   "Content-Type": "application/json",
                   "Accept": "application/json",
                   "User-Agent": "project-chimera/llm"}
        started = self._clock()
        attempts = 0
        retries_used = 0
        dropped: List[str] = []
        while True:
            body = self._body(messages, max_tokens=max_tokens,
                              temperature=temperature, json_mode=json_mode,
                              extra=extra)
            payload = json.dumps(body).encode("utf-8")
            attempts += 1
            try:
                response = self._transport(url, headers, payload, timeout)
            except TransportTimeout as exc:
                if retries_used < self.max_retries:
                    self._sleep(self._backoff(retries_used, None))
                    retries_used += 1
                    continue
                raise LLMTimeoutError(self._redact(
                    f"model request timed out after {attempts} attempt(s): "
                    f"{exc}")) from None
            except TransportError as exc:
                if retries_used < self.max_retries:
                    self._sleep(self._backoff(retries_used, None))
                    retries_used += 1
                    continue
                raise LLMError(self._redact(
                    f"model request failed after {attempts} attempt(s): "
                    f"{exc}")) from None
            status = response.status
            if 200 <= status < 300:
                break
            message = self._redact(_error_message(response.body))
            if status in RETRYABLE_STATUSES and retries_used < self.max_retries:
                retry_after = {k.lower(): v for k, v
                               in response.headers.items()}.get("retry-after")
                self._sleep(self._backoff(retries_used, retry_after))
                retries_used += 1
                continue
            if status == 400:
                param = self._rejected_param(body, message)
                if param is not None and param not in self.unsupported_params:
                    self.unsupported_params.add(param)
                    dropped.append(param)
                    continue
            raise LLMHTTPError(status, self._redact(
                f"model API returned HTTP {status}: {message}"))
        latency_ms = int((self._clock() - started) * 1000)
        try:
            data = json.loads(response.body.decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as exc:
            raise LLMResponseError(self._redact(
                f"model API returned a non-JSON body: {exc}")) from None
        if not isinstance(data, dict):
            raise LLMResponseError("model API returned a non-object body")
        text, finish, usage = _parse_completion(data)
        request_id = None
        for key in ("x-request-id", "request-id", "x-fb-request-id"):
            value = {k.lower(): v for k, v in response.headers.items()}.get(key)
            if value:
                request_id = str(value)
                break
        if request_id is None and isinstance(data.get("id"), str):
            request_id = data["id"]
        return ChatResult(
            text=text,
            parsed=extract_json_object(text),
            model=str(data.get("model") or self.model),
            request_id=request_id,
            latency_ms=max(0, latency_ms),
            prompt_tokens=usage["prompt_tokens"],
            completion_tokens=usage["completion_tokens"],
            total_tokens=usage["total_tokens"],
            reasoning_tokens=usage["reasoning_tokens"],
            finish_reason=finish,
            attempts=attempts,
            dropped_params=tuple(dropped),
        )


__all__ = [
    "ChatResult",
    "DEFAULT_API_BASE",
    "DEFAULT_MODEL",
    "ENV_API_BASE",
    "ENV_API_KEY",
    "ENV_MODEL",
    "ENV_REASONING_EFFORT",
    "FakeTransport",
    "HTTPResponse",
    "LLMError",
    "LLMHTTPError",
    "LLMResponseError",
    "LLMTimeoutError",
    "MetaModelClient",
    "MissingAPIKeyError",
    "ModelSettings",
    "TransportError",
    "TransportTimeout",
    "api_key_available",
    "completion_body",
    "extract_json_object",
    "load_dotenv_values",
    "parse_dotenv",
    "redact",
    "resolve_settings",
    "urllib_transport",
]
