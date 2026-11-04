"""Tests for the stdlib Meta Model API client (``chimera.llm``).

No network and no key: every request goes through ``FakeTransport``.
Covers response parsing, robust JSON extraction, bounded retries with
backoff, optional-parameter fallback on HTTP 400, key handling
(environment, ``.env``, missing key), and key redaction everywhere a
key could leak (repr, errors, describe()).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from chimera import llm
from chimera.llm import (
    FakeTransport,
    HTTPResponse,
    LLMHTTPError,
    LLMResponseError,
    LLMTimeoutError,
    MetaModelClient,
    MissingAPIKeyError,
    TransportError,
    TransportTimeout,
    completion_body,
    extract_json_object,
    parse_dotenv,
    resolve_settings,
)

KEY = "sk-test-SECRET-0123456789"


def _client(responses, **kwargs):
    sleeps = []
    transport = FakeTransport(responses)
    client = MetaModelClient(api_key=KEY, transport=transport,
                             sleep=sleeps.append, jitter=lambda: 0.0,
                             **kwargs)
    return client, transport, sleeps


def _http(status, payload=None, headers=None):
    body = json.dumps(payload).encode() if payload is not None else b""
    return HTTPResponse(status, headers or {}, body)


# -- parsing ---------------------------------------------------------------


def test_chat_parses_openai_compatible_body() -> None:
    client, transport, _ = _client([completion_body(
        '{"action": "click", "index": 2}', prompt_tokens=120,
        completion_tokens=30, reasoning_tokens=12, response_id="cmpl-1")])
    result = client.chat([{"role": "user", "content": "hi"}], max_tokens=256)
    assert result.text == '{"action": "click", "index": 2}'
    assert result.parsed == {"action": "click", "index": 2}
    assert result.prompt_tokens == 120
    assert result.completion_tokens == 30
    assert result.total_tokens == 150
    assert result.reasoning_tokens == 12
    assert result.request_id == "cmpl-1"
    assert result.model == llm.DEFAULT_MODEL
    assert result.finish_reason == "stop"
    assert result.attempts == 1
    sent = transport.requests[0]
    assert sent["url"] == "https://api.meta.ai/v1/chat/completions"
    assert sent["json"]["model"] == "muse-spark-1.3"
    assert sent["json"]["temperature"] == 0.0
    assert sent["json"]["max_completion_tokens"] == 256
    assert sent["json"]["response_format"] == {"type": "json_object"}
    assert sent["headers"]["Authorization"] == f"Bearer {KEY}"


def test_request_id_header_preferred() -> None:
    body = json.dumps(completion_body("{}")).encode()
    client, _, _ = _client([HTTPResponse(200, {"X-Request-Id": "req-9"}, body)])
    assert client.chat([{"role": "user", "content": "x"}]).request_id == "req-9"


def test_missing_usage_is_none_not_zero() -> None:
    body = completion_body("ok")
    del body["usage"]
    client, _, _ = _client([body])
    result = client.chat([{"role": "user", "content": "x"}], json_mode=False)
    assert result.prompt_tokens is None
    assert result.completion_tokens is None
    assert result.parsed is None


def test_unrecognised_body_raises_response_error() -> None:
    client, _, _ = _client([{"unexpected": True}])
    with pytest.raises(LLMResponseError):
        client.chat([{"role": "user", "content": "x"}])


def test_non_json_body_raises_response_error() -> None:
    client, _, _ = _client([HTTPResponse(200, {}, b"<html>oops</html>")])
    with pytest.raises(LLMResponseError):
        client.chat([{"role": "user", "content": "x"}])


@pytest.mark.parametrize("text, expected", [
    ('{"a": 1}', {"a": 1}),
    ('```json\n{"a": 2}\n```', {"a": 2}),
    ('Sure! Here is the action: {"a": 3} hope that helps', {"a": 3}),
    ('noise {not json} then {"a": 4}', {"a": 4}),
    ('{"a": {"nested": [1, 2]}} {"b": 5}', {"a": {"nested": [1, 2]}}),
    ('[1, 2, 3]', None),
    ('"just a string"', None),
    ('', None),
    ('no braces at all', None),
    ('{"unterminated": ', None),
])
def test_extract_json_object(text, expected) -> None:
    assert extract_json_object(text) == expected


def test_extract_json_object_never_raises_on_odd_input() -> None:
    assert extract_json_object(None) is None
    assert extract_json_object(42) is None
    assert extract_json_object("{" * 5000) is None


# -- retries -----------------------------------------------------------------


def test_retries_429_then_succeeds_honouring_retry_after() -> None:
    client, transport, sleeps = _client([
        _http(429, {"error": {"message": "slow down"}}, {"Retry-After": "2"}),
        _http(503, {"error": {"message": "overloaded"}}),
        completion_body('{"ok": true}'),
    ])
    result = client.chat([{"role": "user", "content": "x"}])
    assert result.parsed == {"ok": True}
    assert result.attempts == 3
    assert len(transport.requests) == 3
    assert sleeps[0] == 2.0  # Retry-After honoured
    assert sleeps[1] == pytest.approx(client.backoff_base_seconds * 2)


def test_retries_are_bounded() -> None:
    client, transport, sleeps = _client(
        [_http(500, {"error": {"message": "boom"}})], max_retries=2)
    with pytest.raises(LLMHTTPError) as info:
        client.chat([{"role": "user", "content": "x"}])
    assert info.value.status == 500
    assert len(transport.requests) == 3  # 1 + 2 retries
    assert len(sleeps) == 2


def test_timeouts_retry_then_raise_timeout_error() -> None:
    client, transport, _ = _client([TransportTimeout("t")], max_retries=1)
    with pytest.raises(LLMTimeoutError):
        client.chat([{"role": "user", "content": "x"}])
    assert len(transport.requests) == 2


def test_connection_error_retries_then_recovers() -> None:
    client, transport, _ = _client([TransportError("reset"),
                                    completion_body("{}")])
    assert client.chat([{"role": "user", "content": "x"}]).parsed == {}
    assert len(transport.requests) == 2


@pytest.mark.parametrize("status", [401, 403, 404])
def test_client_errors_are_not_retried(status) -> None:
    client, transport, sleeps = _client(
        [_http(status, {"error": {"message": "nope"}})])
    with pytest.raises(LLMHTTPError) as info:
        client.chat([{"role": "user", "content": "x"}])
    assert info.value.status == status
    assert len(transport.requests) == 1
    assert sleeps == []


def test_json_mode_falls_back_when_rejected() -> None:
    client, transport, _ = _client([
        _http(400, {"error": {"type": "invalid_request_error",
                              "message": "response_format is not supported",
                              "param": "response_format"}}),
        completion_body('Here: {"action": "wait", "ms": 500}'),
        completion_body('{"again": 1}'),
    ])
    result = client.chat([{"role": "user", "content": "x"}])
    assert result.parsed == {"action": "wait", "ms": 500}
    assert result.dropped_params == ("response_format",)
    assert "response_format" in transport.requests[0]["json"]
    assert "response_format" not in transport.requests[1]["json"]
    # Remembered: the next call does not resend it.
    client.chat([{"role": "user", "content": "y"}])
    assert "response_format" not in transport.requests[2]["json"]


def test_unrelated_400_is_raised_not_swallowed() -> None:
    client, transport, _ = _client([
        _http(400, {"error": {"message": "messages must not be empty"}})])
    with pytest.raises(LLMHTTPError):
        client.chat([{"role": "user", "content": "x"}], json_mode=False,
                    temperature=None)
    assert len(transport.requests) == 1


def test_reasoning_effort_sent_and_dropped_if_rejected() -> None:
    client, transport, _ = _client([
        _http(400, {"error": {"message": "unsupported value",
                              "param": "reasoning_effort"}}),
        completion_body("{}")], reasoning_effort="low")
    client.chat([{"role": "user", "content": "x"}])
    assert transport.requests[0]["json"]["reasoning_effort"] == "low"
    assert "reasoning_effort" not in transport.requests[1]["json"]


# -- key handling -------------------------------------------------------------


def test_missing_key_is_a_clear_error(tmp_path: Path) -> None:
    with pytest.raises(MissingAPIKeyError) as info:
        MetaModelClient.from_env(env={}, dotenv_path=tmp_path / "absent.env")
    assert "MODEL_API_KEY" in str(info.value)
    with pytest.raises(MissingAPIKeyError):
        MetaModelClient(api_key="  ")


def test_env_key_wins_over_dotenv(tmp_path: Path) -> None:
    dotenv = tmp_path / ".env"
    dotenv.write_text("MODEL_API_KEY=from-dotenv\nCHIMERA_MODEL=muse-spark-1.2\n")
    settings = resolve_settings(env={"MODEL_API_KEY": "from-env"},
                                dotenv_path=dotenv)
    assert settings.api_key == "from-env"
    assert settings.key_source == "env"
    assert settings.model == "muse-spark-1.2"


def test_dotenv_key_loaded_and_overrides(tmp_path: Path) -> None:
    dotenv = tmp_path / ".env"
    dotenv.write_text(
        "# comment\n"
        "export MODEL_API_KEY='quoted-key'\n"
        "MODEL_API_BASE=https://example.invalid/v1/\n"
        "CHIMERA_REASONING_EFFORT=low  # inline comment\n"
        "garbage line without equals\n")
    settings = resolve_settings(env={}, dotenv_path=dotenv)
    assert settings.api_key == "quoted-key"
    assert settings.key_source == "dotenv"
    assert settings.api_base == "https://example.invalid/v1"
    assert settings.reasoning_effort == "low"
    assert "quoted-key" not in repr(settings)
    assert "quoted-key" not in json.dumps(settings.describe())
    client = MetaModelClient.from_env(env={}, dotenv_path=dotenv,
                                      transport=FakeTransport([{}]))
    assert client.model == llm.DEFAULT_MODEL
    assert client.api_base == "https://example.invalid/v1"


def test_parse_dotenv_edge_cases() -> None:
    parsed = parse_dotenv('A=1\nB="two words"\n=novalue\nC=x=y\n  D = spaced \n')
    assert parsed == {"A": "1", "B": "two words", "C": "x=y", "D": "spaced"}


def test_key_never_in_repr_describe_or_errors() -> None:
    client, _, _ = _client([_http(401, {"error": {
        "message": f"invalid key {KEY} supplied"}})])
    assert KEY not in repr(client)
    assert KEY not in json.dumps(client.describe())
    with pytest.raises(LLMHTTPError) as info:
        client.chat([{"role": "user", "content": "x"}])
    assert KEY not in str(info.value)
    assert llm.REDACTED in str(info.value)


def test_key_redacted_from_transport_errors() -> None:
    client, _, _ = _client([TransportError(f"proxy said {KEY}")],
                           max_retries=0)
    with pytest.raises(llm.LLMError) as info:
        client.chat([{"role": "user", "content": "x"}])
    assert KEY not in str(info.value)
    assert info.value.__cause__ is None  # no chained exception leaks it


def test_key_only_in_authorization_header() -> None:
    client, transport, _ = _client([completion_body("{}")])
    client.chat([{"role": "user", "content": "x"}])
    request = transport.requests[0]
    assert KEY not in json.dumps(request["json"])
    assert KEY not in request["url"]
    others = {k: v for k, v in request["headers"].items()
              if k != "Authorization"}
    assert KEY not in json.dumps(others)


def test_module_reads_no_key_at_import() -> None:
    # Importing the module must not require or read a key.
    import importlib

    importlib.reload(llm)
    assert llm.api_key_available(env={}, dotenv_path=Path("/nonexistent")) \
        is False
