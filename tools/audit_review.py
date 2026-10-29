"""Guided human-audit review tool (benchmark harness, manual step).

Walks a human auditor through every sampled episode in one or more
audit-plan files, showing the evidence for P1–P3 and recording the
human's own judgments in the plans' ``cells.<key>.verdicts`` fields.
Implements the adjudication step of ``docs/user_guide.md`` §15.1:

* The original verifier P1–P3 verdicts are **hidden** until the
  human records their own decision for that episode, so nothing is
  ever inferred from the verifier's results.
* Only ``verdicts`` entries are written, atomically (temp file +
  rename); every other byte of the plan file is preserved, and no
  snapshot, trace, replay report, or run file is ever modified.
* Progress is the file itself: recorded verdicts are skipped on
  re-launch, so the auditor can stop (``q``) and resume freely.
* Every input is validated; verdicts use strict JSON booleans, and
  each save is re-loaded through :func:`benchmarks.audit.load_plan`
  so :func:`benchmarks.audit.apply_audit` is guaranteed to accept
  the file's shape.

Usage::

    .venv/bin/python tools/audit_review.py \\
        artifacts/dev-20261028/run-chimera.audit-plan.json \\
        artifacts/dev-20261028/run-baseline-a.audit-plan.json

With no arguments the two development-run plans above are used.
``--redo`` re-prompts even episodes that already have verdicts
(overwriting them); otherwise completed episodes are skipped.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from benchmarks.audit import AuditError, load_plan  # noqa: E402

#: Default plans when the tool is launched without arguments.
DEFAULT_PLANS = (
    "artifacts/dev-20261028/run-chimera.audit-plan.json",
    "artifacts/dev-20261028/run-baseline-a.audit-plan.json",
)

#: Human explanations for the postcondition checks (§15.1 step 2).
CHECK_HELP = {
    "P1": "Is confirmation_visible true in the snapshot?",
    "P2": ("Does items contain exactly one entry whose text equals "
           "the expected stored name?"),
    "P3": "Does items contain exactly one entry?",
}

TRUE_WORDS = {"y", "yes", "t", "true"}
FALSE_WORDS = {"n", "no", "f", "false"}


def _sha256_file(path: Path) -> Optional[str]:
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except OSError:
        return None


def _load_json(path: Path) -> Optional[Any]:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _check_ids(bundle: Dict[str, Any]) -> List[str]:
    checks = bundle.get("verifier_checks")
    if not isinstance(checks, dict) or not checks:
        return []
    return sorted(str(k) for k in checks)


class ReviewSession:
    """One guided pass over the sampled episodes of the given plans."""

    def __init__(self, plan_paths: List[Path],
                 input_fn: Callable[[str], str] = input,
                 print_fn: Callable[..., None] = print) -> None:
        self.plan_paths = plan_paths
        self.ask = input_fn
        self.show = print_fn
        self.recorded_this_run = 0
        self.skipped_done = 0

    # -- loading ----------------------------------------------------

    def _load_raw(self, path: Path) -> Dict[str, Any]:
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise AuditError(f"cannot read audit plan {path}: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise AuditError(
                f"audit plan {path} is not valid JSON: {exc}") from exc
        if not isinstance(raw, dict):
            raise AuditError(f"audit plan {path} must contain an object")
        # Validates the whole file, including any verdicts already
        # recorded: a malformed file stops the session loudly rather
        # than being written back worse.
        load_plan(path)
        return raw

    def _save_verdict(self, path: Path, raw: Dict[str, Any], cell_key: str,
                      trial_id: str, verdict: Dict[str, Any]) -> None:
        raw["cells"][cell_key]["verdicts"][trial_id] = verdict
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(
            json.dumps(raw, sort_keys=True, ensure_ascii=False, indent=2)
            + "\n", encoding="utf-8")
        tmp.replace(path)
        # The save must remain applicable: reload through the same
        # parser apply_audit uses.
        load_plan(path)

    # -- evidence ---------------------------------------------------

    def _evidence_status(self, bundle: Dict[str, Any]
                         ) -> List[Tuple[str, str]]:
        """Freshness of the hashed evidence (trace/snapshot) vs the plan."""
        rows: List[Tuple[str, str]] = []
        digests = bundle.get("digests", {})
        for kind, field in (("trace", "trace_path"),
                            ("snapshot", "snapshot_path")):
            expected = digests.get(kind)
            current = _sha256_file(Path(str(bundle.get(field, ""))))
            if current is None:
                rows.append((kind, "MISSING — file unreadable"))
            elif expected is not None and current != expected:
                rows.append((kind, "CHANGED since planning — "
                                  "apply_audit will refuse this episode"))
            else:
                rows.append((kind, "unchanged since planning"))
        return rows

    def _show_episode(self, plan_label: str, cell_key: str,
                      bundle: Dict[str, Any], position: str) -> None:
        self.show("")
        self.show(f"=== Episode {position} · {plan_label} · {cell_key} · "
                  f"{bundle.get('trial_id')} ===")
        self.show(f"Expected stored name: {bundle.get('expected_stored_name')!r}")
        self.show(f"Agent terminal: {bundle.get('agent_terminal_status')} · "
                  f"Outcome: {bundle.get('outcome')}")
        self.show(f"Trace/report: {bundle.get('trace_path')}")
        self.show(f"Snapshot:     {bundle.get('snapshot_path')}")
        for kind, status in self._evidence_status(bundle):
            self.show(f"  [{kind}] {status}")
        trace = _load_json(Path(str(bundle.get("trace_path", ""))))
        if isinstance(trace, dict) and "terminal_status" in trace:
            if "event_count" in trace:
                detail = f"{trace['event_count']} events"
            elif isinstance(trace.get("steps"), list):
                detail = f"{len(trace['steps'])} steps"
            else:
                detail = "driver report"
            self.show(f"Trace terminal: {trace['terminal_status']} "
                      f"({detail})")
        else:
            self.show("Trace terminal: (file unreadable — open it directly)")
        snapshot = _load_json(Path(str(bundle.get("snapshot_path", ""))))
        if isinstance(snapshot, dict):
            items = snapshot.get("items", [])
            self.show(f"Snapshot confirmation_visible: "
                      f"{snapshot.get('confirmation_visible')}")
            self.show(f"Snapshot items ({len(items) if isinstance(items, list) else '?'}):")
            if isinstance(items, list):
                for index, item in enumerate(items):
                    self.show(f"  [{index}] {item!r}")
        else:
            self.show("Snapshot: (file unreadable — open it directly, or "
                      "mark unauditable)")
        self.show("")
        self.show("Judge each check yourself from the evidence above:")
        for check_id in _check_ids(bundle):
            self.show(f"  {check_id}: "
                      f"{CHECK_HELP.get(check_id, 'judge this check yourself')}")

    # -- prompting --------------------------------------------------

    def _prompt_check(self, check_id: str) -> Any:
        """One check's judgment: bool, "unauditable"/"skip", or None."""
        while True:
            try:
                answer = self.ask(
                    f"{check_id} true or false? [y/n, u=unauditable, "
                    f"s=skip, q=quit] ").strip().lower()
            except EOFError:
                return None
            if answer in TRUE_WORDS:
                return True
            if answer in FALSE_WORDS:
                return False
            if answer in ("u", "unauditable"):
                return "unauditable"
            if answer in ("s", "skip"):
                return "skip"
            if answer in ("q", "quit"):
                return None
            self.show("Please answer y or n (or u/s/q).")

    def _prompt_reason(self) -> Optional[str]:
        while True:
            try:
                reason = self.ask(
                    "Unauditable reason (required): ").strip()
            except EOFError:
                return None
            if reason:
                return reason
            self.show("A reason is required — an empty reason would be "
                      "refused at apply time.")

    def _judge(self, bundle: Dict[str, Any]
               ) -> Tuple[str, Dict[str, Any]]:
        """Collect one episode's verdict.

        Returns ("verdict"|"skip"|"quit", verdict-dict). The verdict
        dict is empty for skip/quit.
        """
        check_ids = _check_ids(bundle)
        if not check_ids:
            self.show("This bundle names no verifier checks; it cannot "
                      "be adjudicated as checks. Mark it unauditable or "
                      "skip it.")
            while True:
                try:
                    answer = self.ask("[u=unauditable, s=skip, q=quit] "
                                      ).strip().lower()
                except EOFError:
                    return "quit", {}
                if answer in ("u", "unauditable"):
                    reason = self._prompt_reason()
                    if reason is None:
                        return "quit", {}
                    return "verdict", {"verdict": "unauditable",
                                       "reason": reason}
                if answer in ("s", "skip"):
                    return "skip", {}
                if answer in ("q", "quit"):
                    return "quit", {}
                self.show("Please answer u, s, or q.")
        checks: Dict[str, bool] = {}
        for check_id in check_ids:
            result = self._prompt_check(check_id)
            if result is None:
                return "quit", {}
            if result == "skip":
                return "skip", {}
            if result == "unauditable":
                reason = self._prompt_reason()
                if reason is None:
                    return "quit", {}
                return "verdict", {"verdict": "unauditable",
                                   "reason": reason}
            checks[check_id] = bool(result)
        try:
            note = self.ask("Note (optional, Enter to skip): ").strip()
        except EOFError:
            return "quit", {}
        verdict: Dict[str, Any] = {"checks": checks}
        if note:
            verdict["note"] = note
        return "verdict", verdict

    # -- main loop --------------------------------------------------

    def run(self, redo: bool = False) -> Dict[str, int]:
        plans: List[Tuple[Path, Dict[str, Any]]] = []
        for path in self.plan_paths:
            if not path.is_file():
                raise AuditError(f"audit plan not found: {path}")
            plans.append((path, self._load_raw(path)))
        queue: List[Tuple[int, str, Dict[str, Any]]] = []
        for index, (_, raw) in enumerate(plans):
            for cell_key in sorted(raw.get("cells", {})):
                cell = raw["cells"][cell_key]
                done = set(cell.get("verdicts", {}))
                for bundle in cell.get("sampled", []):
                    trial_id = str(bundle.get("trial_id"))
                    if trial_id in done and not redo:
                        self.skipped_done += 1
                        continue
                    queue.append((index, cell_key, bundle))
        total = len(queue) + self.skipped_done
        self.show(f"Audit review: {total} sampled episode(s) across "
                  f"{len(plans)} plan(s).")
        if self.skipped_done:
            self.show(f"{self.skipped_done} already have verdicts and "
                      f"will be skipped (use --redo to revisit).")
        self.show("The verifier's own P1–P3 are hidden until you record "
                  "each episode.")
        position = self.skipped_done
        index = 0
        quit_early = False
        while index < len(queue):
            plan_index, cell_key, bundle = queue[index]
            position += 1
            path, raw = plans[plan_index]
            self._show_episode(path.name, cell_key, bundle,
                               f"{position}/{total}")
            action, verdict = self._judge(bundle)
            if action == "quit":
                quit_early = True
                position -= 1
                break
            if action == "skip":
                queue.append(queue.pop(index))
                position -= 1
                continue
            trial_id = str(bundle.get("trial_id"))
            self._save_verdict(path, raw, cell_key, trial_id, verdict)
            self.recorded_this_run += 1
            index += 1
            # Revealed only now that the human's judgment is saved.
            self.show(f"Recorded for {trial_id}. The verifier's checks "
                      f"were: {bundle.get('verifier_checks')}")
        recorded = self.skipped_done + self.recorded_this_run
        self.show("")
        if recorded >= total and not quit_early:
            self.show(f"Done: {total}/{total} episodes have verdicts. "
                      f"Next: apply_audit each plan (user guide §15.1 "
                      f"step 3).")
        else:
            self.show(f"Progress saved: {recorded}/{total} episodes have "
                      f"verdicts. Re-launch to resume.")
        return {"total": total, "recorded": recorded,
                "this_run": self.recorded_this_run,
                "quit_early": int(quit_early)}


def main(argv: List[str]) -> int:
    args = [a for a in argv if a != "--redo"]
    redo = len(args) != len(argv)
    if "--help" in args or "-h" in args:
        print(__doc__)
        return 0
    plan_paths = [Path(a) for a in args] or [Path(p) for p in DEFAULT_PLANS]
    try:
        ReviewSession(plan_paths).run(redo=redo)
    except AuditError as exc:
        print(f"audit review: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted — progress so far is saved in the plan files.")
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
