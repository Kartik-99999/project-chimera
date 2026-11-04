"""Baseline B: Muse Spark as the acting agent, judged by the harness.

The model *proposes* browser actions; Chimera's deterministic,
model-free verifier *judges* the outcome from a harness-captured
snapshot. Success criteria come from the test definition, never from
the model — a ``done`` claim of success that the verifier rejects is
counted as a false success, which is the metric this baseline exists
to measure.

Safety shape (mirrors the fixed drivers):

* the model addresses page elements by **index** into a
  harness-enumerated list — it never invents selectors or URLs;
* ``navigate`` is allowed only to the episode's own URL (a reload);
  anything else is blocked before it executes and recorded;
* every executed action is observed by the standard recording page
  and judged against the episode policy after the run;
* the loop writes a real trace (``TraceRecorder``), so the runner
  reads the terminal, the retry/action counts, and the verification
  evidence through the exact same path as Chimera episodes.

Model usage (calls, tokens, blocked attempts) is recorded per episode
in a ``<run>.model.json`` sidecar next to the trace. No USD cost is
recorded: the project has no pricing data and will not invent any.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Tuple

from chimera.llm import LLMError, MetaModelClient, extract_json_object

#: Baseline id used by the runner, manifests, and reports.
MODEL_BASELINE_ID = "baseline-b"

#: Upper bound on model steps per episode (each step is one call).
MAX_STEPS = 12

#: Longest single ``wait`` the model may request (ms).
MAX_WAIT_MS = 5000

#: Per-action Playwright timeout (ms): the same 5 s budget Chimera's
#: own actions get, so the comparison is time-matched.
MODEL_ACTION_TIMEOUT_MS = 5000

#: Consecutive failed steps (bad JSON, refused action, model error)
#: before the episode is failed instead of re-prompted.
MAX_CONSECUTIVE_FAILURES = 3

#: Longest fill value accepted (project names are short).
MAX_FILL_LEN = 500

#: Token budget per model call. Muse Spark is a reasoning model and
#: reasoning tokens count against this cap, so it must leave room for
#: thought (observed ~450-510) PLUS the JSON action (512 starves it).
MODEL_MAX_TOKENS = 2048

#: Elements the model may act on.
_ENUMERATE_SELECTOR = (
    "button, input, select, textarea, a[href], [role='button']"
)

SYSTEM_PROMPT = """You drive a web browser to complete ONE task. You see the page as a numbered element list. Reply with EXACTLY ONE JSON object per turn, no other text.

Actions:
{"action":"click","index":N,"reason":"..."} — click element N.
{"action":"fill","index":N,"value":"...","reason":"..."} — type into element N.
{"action":"wait","ms":M,"reason":"..."} — wait M milliseconds (0-5000) for the page to settle.
{"action":"navigate","url":"...","reason":"..."} — reload the task page. ONLY the exact task URL is allowed; anything else is blocked.
{"action":"done","claim":"success","reason":"..."} — the task is complete AND the page shows it.
{"action":"done","claim":"failure","reason":"..."} — the task cannot be completed.

Rules: address elements by index only. The page loads ready for the task — do NOT touch any test, fault, debug, settings, or configuration controls; they are harness equipment, not part of your task. Complete the task using only the task form itself. Never claim success unless the page visibly shows the completed task. If a control does nothing, say failure — do not repeat a dead action forever."""


@dataclass
class ModelOutcome:
    """Everything one model episode produced (in-memory carrier)."""

    run_id: str
    terminal_status: str
    trace_path: Optional[str]
    error: Optional[str]
    observation: Any = None
    observation_error: Optional[str] = None
    action_log: Any = None
    model_report_path: Optional[str] = None
    model_id: str = ""
    steps: int = 0
    model_calls: int = 0
    blocked_attempts: int = 0


def _truncate(text: Any, limit: int = 200) -> str:
    words = " ".join(str(text).split())
    return words if len(words) <= limit else words[:limit] + "…"


def snapshot_elements(page: Any, limit: int = 40
                      ) -> Tuple[List[Dict[str, Any]], list]:
    """Enumerate the page's actionable elements for one model step.

    Returns ``(elements, locators)``: JSON-serialisable summaries the
    model sees, and the matching live locators the executor acts on.
    The list is rebuilt every step, so an index can never go stale.
    """
    try:
        rows = page.locator(_ENUMERATE_SELECTOR).all()
    except Exception:  # noqa: BLE001 — unreadable page reads empty
        return [], []
    elements: List[Dict[str, Any]] = []
    locators: list = []
    for row in rows:
        if len(elements) >= limit:
            break
        try:
            visible = row.is_visible()
        except Exception:  # noqa: BLE001 — assume visible
            visible = True
        if not visible:
            continue
        name = ""
        for attr in ("aria-label", "placeholder", "value", "title",
                     "alt"):
            try:
                candidate = row.get_attribute(attr)
            except Exception:  # noqa: BLE001 — next attribute
                candidate = None
            if candidate:
                name = str(candidate)
                break
        if not name:
            try:
                name = row.text_content(timeout=1000) or ""
            except Exception:  # noqa: BLE001 — nameless control
                name = ""
        try:
            value = row.input_value(timeout=500)
        except Exception:  # noqa: BLE001 — not a readable field
            value = None
        elements.append({"index": len(elements),
                         "name": _truncate(name, 80),
                         "value": _truncate(value, 80)
                         if value is not None else None})
        locators.append(row)
    return elements, locators


def validate_action(action: Any, elements: List[Dict[str, Any]],
                    episode_url: str
                    ) -> Tuple[Optional[str], Dict[str, Any], Optional[str]]:
    """Check one model-proposed action. Returns ``(kind, params, error)``.

    ``error`` set means the action is refused: nothing executes, and
    the message is fed back to the model on the next step.
    """
    if not isinstance(action, dict):
        return None, {}, "action must be a JSON object"
    kind = action.get("action")
    if kind == "click":
        index = action.get("index")
        if isinstance(index, bool) or not isinstance(index, int):
            return None, {}, "click needs an integer element index"
        if not 0 <= index < len(elements):
            return None, {}, (
                f"click index {index} is out of range "
                f"(0-{len(elements) - 1})")
        return "click", {"index": index}, None
    if kind == "fill":
        index = action.get("index")
        value = action.get("value")
        if isinstance(index, bool) or not isinstance(index, int):
            return None, {}, "fill needs an integer element index"
        if not 0 <= index < len(elements):
            return None, {}, (
                f"fill index {index} is out of range "
                f"(0-{len(elements) - 1})")
        if not isinstance(value, str):
            return None, {}, "fill needs a string value"
        if len(value) > MAX_FILL_LEN:
            return None, {}, (
                f"fill value too long ({len(value)} > {MAX_FILL_LEN})")
        return "fill", {"index": index, "value": value}, None
    if kind == "wait":
        ms = action.get("ms")
        if isinstance(ms, bool) or not isinstance(ms, int):
            return None, {}, "wait needs an integer ms"
        if not 0 <= ms <= MAX_WAIT_MS:
            return None, {}, (
                f"wait ms out of range (0-{MAX_WAIT_MS})")
        return "wait", {"ms": ms}, None
    if kind == "navigate":
        url = action.get("url")
        if not isinstance(url, str) or url != episode_url:
            return None, {}, (
                "navigation blocked: only the task page may be opened, "
                f"got {url!r}")
        return "navigate", {"url": url}, None
    if kind == "done":
        claim = action.get("claim")
        if claim in ("success", "succeeded"):
            claim = "success"
        elif claim in ("failure", "failed"):
            claim = "failure"
        else:
            return None, {}, (
                "done needs a claim of 'success' or 'failure', "
                f"got {claim!r}")
        return "done", {"claim": claim}, None
    return None, {}, (
        f"unknown action {kind!r}: want one of "
        "navigate, fill, click, wait, done")


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _step_prompt(*, project_name: str, episode_url: str, step: int,
                 elements: List[Dict[str, Any]], page_text: str,
                 last_result: str) -> str:
    return (
        f"Task: create a project named {project_name!r}.\n"
        f"Task page: {episode_url}\n"
        f"Step {step} of {MAX_STEPS}.\n"
        f"Elements:\n{json.dumps(elements, indent=None)}\n"
        f"Visible page text:\n{page_text}\n"
        f"Last step result: {last_result}\n"
        "Reply with exactly one JSON action object."
    )


def _read_page_text(page: Any, limit: int = 600) -> str:
    """What a user would read on the page (confirmations, lists)."""
    try:
        text = page.locator("body").inner_text(timeout=1000) or ""
    except Exception:  # noqa: BLE001 — unreadable page reads empty
        return ""
    return _truncate(text, limit)


def _write_model_report(trace_dir: Path, run_id: str, payload: Mapping
                        ) -> Optional[str]:
    try:
        path = Path(trace_dir) / f"{run_id}.model.json"
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        tmp.replace(path)
        return str(path)
    except OSError:  # noqa: BLE001 — sidecar is best-effort
        return None


def run_model(
    *,
    project_name: str,
    url: str,
    trace_dir: Path,
    token: Any = None,
    observe: Optional[Callable[[Any], Any]] = None,
    browser_factory: Optional[Callable[[Any], Tuple[Any, Any, Any]]] = None,
    client: Optional[MetaModelClient] = None,
    max_steps: int = MAX_STEPS,
) -> ModelOutcome:
    """Run one Baseline B episode: Muse Spark acts, the harness watches.

    ``browser_factory`` / ``client`` are seams for tests (fake page,
    ``FakeTransport``); production passes neither and gets real
    Chromium plus a client built from ``MODEL_API_KEY``.
    """
    from chimera.safety import RunCancelledError
    from chimera.tracing import TraceRecorder, TraceWriteError

    from benchmarks.observer import ActionLog, recording_browser_factory

    if client is None:
        client = MetaModelClient.from_env()
    trace_dir = Path(trace_dir)
    trace_dir.mkdir(parents=True, exist_ok=True)
    recorder = TraceRecorder(trace_dir=trace_dir)
    run_id = recorder.run_id
    recorder.record(
        "run_started",
        evidence=[f"url={url}", f"project_name={project_name}",
                  f"baseline={MODEL_BASELINE_ID}",
                  f"model={client.model}"],
    )
    log = ActionLog(run_id=run_id)
    calls: List[Dict[str, Any]] = []
    blocked = 0
    steps = 0
    outcome = ModelOutcome(
        run_id=run_id, terminal_status="failed", trace_path=None,
        error=None, model_id=client.model)

    def _check_cancel() -> None:
        if token is not None:
            token.check()

    def _finish(terminal: str, error: Optional[str] = None) -> None:
        outcome.terminal_status = terminal
        outcome.error = error
        outcome.steps = steps
        outcome.model_calls = len(calls)
        outcome.blocked_attempts = blocked
        try:
            outcome.trace_path = str(recorder.finish(
                terminal,
                error_details=({"type": "ModelEpisodeError",
                                "message": error}
                               if error else None)))
        except TraceWriteError as exc:
            outcome.terminal_status = "failed"
            outcome.error = f"TraceWriteError: {exc}"
            outcome.trace_path = None
        outcome.model_report_path = _write_model_report(
            trace_dir, run_id,
            {"run_id": run_id, "baseline": MODEL_BASELINE_ID,
             "model": client.model, "terminal_status": terminal,
             "steps": steps, "blocked_attempts": blocked,
             "max_tokens": MODEL_MAX_TOKENS,
             "reasoning_effort": client.reasoning_effort,
             "calls": calls})

    def _fail_step(action_type: str, message: str) -> None:
        recorder.action_attempted(action_type)
        recorder.action_failed(
            action_type,
            RuntimeError(message))

    if browser_factory is None:
        from playwright.sync_api import sync_playwright

        playwright_context = sync_playwright()
        playwright = playwright_context.__enter__()
        factory = recording_browser_factory(log)
        browser, context, page = factory(playwright)
        owned_playwright: Any = playwright_context
    else:
        browser, context, page = browser_factory(object())
        owned_playwright = None
    try:
        # Deterministic start: the harness opens the episode page, so
        # the model always acts from the same state.
        _check_cancel()
        recorder.action_attempted("navigate")
        try:
            page.goto(url, timeout=MODEL_ACTION_TIMEOUT_MS)
            recorder.action_succeeded("navigate")
        except Exception as exc:  # noqa: BLE001 — failed start
            recorder.action_failed("navigate", exc)
            _finish("failed", f"episode page did not load: {exc}")
            return outcome

        last_result = "episode page loaded; no model action yet."
        consecutive_failures = 0
        for step in range(1, max_steps + 1):
            _check_cancel()
            steps = step
            elements, locators = snapshot_elements(page)
            prompt = _step_prompt(
                project_name=project_name, episode_url=url, step=step,
                elements=elements,
                page_text=_read_page_text(page),
                last_result=last_result)
            try:
                result = client.chat(
                    [{"role": "system", "content": SYSTEM_PROMPT},
                     {"role": "user", "content": prompt}],
                    max_tokens=MODEL_MAX_TOKENS, temperature=0.0,
                    json_mode=True)
            except LLMError as exc:
                _fail_step("model", f"model call failed: {exc}")
                consecutive_failures += 1
                last_result = f"model call failed ({exc}); try again."
                if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                    _finish("failed",
                            f"model unreachable: {exc}")
                    return outcome
                continue
            action = result.parsed
            if action is None:
                action = extract_json_object(result.text)
            calls.append({
                "step": step, "latency_ms": result.latency_ms,
                "prompt_tokens": result.prompt_tokens,
                "completion_tokens": result.completion_tokens,
                "total_tokens": result.total_tokens,
                "reasoning_tokens": result.reasoning_tokens,
                "finish_reason": result.finish_reason,
                "raw": _truncate(result.text, 500),
                "parsed": action,
            })
            if action is None:
                _fail_step("model", "model reply was not JSON")
                consecutive_failures += 1
                last_result = ("your last reply was not a JSON object; "
                               "reply with exactly one JSON action.")
                if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                    _finish("failed", "model never replied with JSON")
                    return outcome
                continue
            kind, params, refusal = validate_action(
                action, elements, url)
            reason = _truncate(action.get("reason", ""), 200)
            if refusal is not None:
                _fail_step(kind or "model",
                           f"action refused: {refusal}")
                if action.get("action") == "navigate":
                    blocked += 1
                calls[-1]["refused"] = refusal
                consecutive_failures += 1
                last_result = f"refused ({refusal}); propose better."
                if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                    _finish("failed",
                            f"action refused repeatedly: {refusal}")
                    return outcome
                continue
            if kind == "done":
                recorder.record(
                    "model_done",
                    evidence=[f"claim={params['claim']}",
                              f"reason={reason}"])
                if params["claim"] == "success":
                    _finish("succeeded")
                else:
                    _finish("failed",
                            f"model gave up: {reason or 'no reason'}")
                return outcome
            recorder.action_attempted(kind)
            try:
                if kind == "click":
                    locators[params["index"]].click(
                        timeout=MODEL_ACTION_TIMEOUT_MS)
                    observed = "clicked"
                elif kind == "fill":
                    locators[params["index"]].fill(
                        params["value"],
                        timeout=MODEL_ACTION_TIMEOUT_MS)
                    observed = "filled"
                elif kind == "wait":
                    page.wait_for_timeout(params["ms"])
                    observed = f"waited {params['ms']} ms"
                else:  # navigate: validated to the episode URL only
                    page.goto(params["url"],
                              timeout=MODEL_ACTION_TIMEOUT_MS)
                    observed = "reloaded"
                recorder.action_succeeded(kind)
            except Exception as exc:  # noqa: BLE001 — failed step
                recorder.action_failed(kind, exc)
                consecutive_failures += 1
                last_result = (f"{kind} failed ({exc}); "
                               "inspect the page and try differently.")
                if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                    _finish("failed",
                            f"{kind} kept failing: {exc}")
                    return outcome
                continue
            consecutive_failures = 0
            calls[-1]["executed"] = kind
            calls[-1]["observed"] = observed
            calls[-1]["reason"] = reason
            elements_after, _ = snapshot_elements(page)
            names = ", ".join(
                e["name"] for e in elements_after[:6] if e["name"])
            last_result = (f"{kind} ok ({observed}). reason: {reason}. "
                           f"page now shows: {names or 'nothing'}.")
        _finish("failed", f"step budget exhausted ({max_steps} steps)")
        return outcome
    except RunCancelledError as exc:
        _finish("cancelled", f"RunCancelledError: {exc}")
        return outcome
    finally:
        if observe is not None:
            try:
                outcome.observation = observe(page)
                outcome.observation_error = None
            except Exception as exc:  # noqa: BLE001 — reported
                outcome.observation = None
                outcome.observation_error = (
                    f"{type(exc).__name__}: {exc}")
        outcome.action_log = log
        # Direct close on the owning thread: Playwright's sync API is
        # thread-bound (a helper thread breaks every close).
        try:
            context.close()
        finally:
            browser.close()
            if owned_playwright is not None:
                owned_playwright.__exit__(None, None, None)


def model_executor(
    *,
    scenario: Any,
    task_input: Any,
    fault: Any,
    trace_dir: Path,
    token: Any,
    timeout_seconds: float,
    client: Optional[MetaModelClient] = None,
    browser_factory: Optional[Callable] = None,
) -> Any:
    """Execute one Baseline B episode (the runner's executor seam)."""
    from benchmarks.runner import EpisodeExecution

    import chimera.agent as agent_module

    from benchmarks.observer import (
        actions_path_for,
        episode_policy,
        judge_log,
    )
    from benchmarks.verifier import (
        DOMSnapshot,
        SnapshotValidationError,
        capture_page_state,
        snapshot_path_for,
    )

    del scenario, timeout_seconds  # fixed loop; runner owns the budget
    url = agent_module.get_demo_url_with_faults(
        slow_ms=fault.slow_ms, disabled=fault.disabled)
    outcome = run_model(
        project_name=task_input.project_name, url=url,
        trace_dir=Path(trace_dir), token=token,
        observe=capture_page_state, browser_factory=browser_factory,
        client=client,
    )
    judged = judge_log(outcome.action_log, episode_policy(url))
    actions_path = actions_path_for(Path(trace_dir), outcome.run_id)
    actions_tmp = actions_path.with_suffix(actions_path.suffix + ".tmp")
    actions_tmp.write_text(judged.to_json(), encoding="utf-8")
    actions_tmp.replace(actions_path)
    snapshot_dict: Optional[Dict[str, Any]] = None
    snapshot_ref: Optional[str] = None
    observation_error: Optional[str] = outcome.observation_error
    if observation_error is None:
        observation = outcome.observation
        if not isinstance(observation, dict):
            observation_error = (
                "state snapshot missing: the observer returned "
                f"{type(observation).__name__}, not a state object"
            )
        else:
            try:
                candidate = dict(observation)
                candidate["run_id"] = outcome.run_id
                candidate.setdefault("captured_at", _now_utc_iso())
                snapshot = DOMSnapshot.from_dict(candidate)
            except SnapshotValidationError as exc:
                observation_error = f"state snapshot malformed: {exc}"
            else:
                path = snapshot_path_for(Path(trace_dir), outcome.run_id)
                tmp = path.with_suffix(path.suffix + ".tmp")
                tmp.write_text(snapshot.to_json(), encoding="utf-8")
                tmp.replace(path)
                snapshot_dict = snapshot.to_dict()
                snapshot_ref = str(path)
    return EpisodeExecution(
        run_id=outcome.run_id,
        trace_path=outcome.trace_path,
        reported_status=outcome.terminal_status,
        error=outcome.error,
        state_snapshot=snapshot_dict,
        snapshot_ref=snapshot_ref,
        observation_error=observation_error,
        episode_url=url,
        action_log=judged.to_dict(),
    )
