"""socom ledger — run ledger + contract verification. Assembled into bin/socom by build.py."""
from __future__ import annotations

import hashlib
import os
import re
import shlex
import subprocess
import sys
import textwrap
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from socom.core import SOCOM_DIR, _now_iso, repo_root

# === BODY ===

# ── contract — make the validation contract testable, not inert ──────────
# §contracts-before-code: a contract's <check> elements carry a <run> command
# and an <expect> outcome. `verify` RUNS each runnable check (PASS/FAIL on exit
# code) and flags the rest MANUAL — the SOCOM-native conformance-test runner.

def _contract_el(root_el):
    """The <contract> element of a promise root, or root itself if it IS one.
    Pure: returns the element or None."""
    if root_el.tag == "contract":
        return root_el
    return root_el.find("contract")


def _contract_checks(contract_el) -> list:
    """Pure: a contract element -> [{id, assessor, run, expect, auto}]. A check
    with a <run> command is auto-verifiable; one without is MANUAL."""
    checks = []
    for c in contract_el.findall("check"):
        run = c.findtext("run")
        run = run.strip() if run and run.strip() else None
        checks.append({
            "id": c.get("id", "?"),
            "assessor": c.get("assessor", "?"),
            "run": run,
            "expect": " ".join((c.findtext("expect") or "").split()),
            "auto": run is not None,
        })
    return checks


def _verify_summary(results: list) -> dict:
    """Pure: [{auto, passed}] -> tallies. ok iff no auto check FAILED. Manual
    checks never count as passed (fail-closed) and never as failed."""
    passed = sum(1 for r in results if r["auto"] and r["passed"])
    failed = sum(1 for r in results if r["auto"] and not r["passed"])
    manual = sum(1 for r in results if not r["auto"])
    return {"passed": passed, "failed": failed, "manual": manual,
            "ok": failed == 0}


def _next_attempt(rows: list, promise: str, contract: str) -> int:
    """Pure: the 1-based attempt number for the next (promise, contract)
    execution — one past the highest attempt already recorded for that pair.
    cycle groups pass@1/pass@k by promise, so the attempt sequence is
    per-promise; attempt 1's verdict decides pass@1 (schemas/ledger.xml)."""
    prior = [int(r.get("attempt", 0)) for r in rows
             if r.get("promise") == promise and r.get("contract") == contract]
    return (max(prior) + 1) if prior else 1


def _append_ledger_row(root, promise, seat, contract, summary, duration_s) -> dict:
    """The single writer for .socom/ledger/runs.jsonl: read the ledger, compute
    the next attempt for (promise, contract), append one row for this
    assessment, and return it. Both `contract verify --record` and the
    task-completion gate record through here, so the wire format and the attempt
    sequence have ONE source of truth (§least-common-mechanism). Callers own the
    fail-closed guards (standalone / manual-pending / no-evidence) — this writes
    unconditionally once a row is warranted."""
    import json
    try:
        import fcntl
    except ImportError:
        # The ledger writer needs POSIX advisory locking (flock) to serialize
        # concurrent seats. socom is POSIX-scoped (macOS/Linux/WSL) — say so
        # plainly rather than crash with a bare ImportError (R6: degrade loudly).
        sys.exit("socom: the run ledger requires POSIX fcntl.flock (unix only — "
                 "macOS/Linux/WSL). On native Windows, run socom under WSL.")
    ledger = root / SOCOM_DIR / "ledger" / "runs.jsonl"
    ledger.parent.mkdir(parents=True, exist_ok=True)
    # Serialize the whole read -> compute-attempt -> append under one exclusive
    # lock: without it, two seats recording concurrently (multi-agent is the
    # goal) read the same tail, both compute attempt=K+1, and both write it —
    # duplicate attempts break cycle's pass@1/pass@k, and interleaved writes can
    # tear a row. 'a+' creates the file if absent and keeps one fd for both the
    # read (seek 0) and the append (O_APPEND ignores seek, always tail). flock is
    # POSIX advisory and same-host — honored because this is the SINGLE writer
    # for runs.jsonl (all writers cooperate); the ledger is a same-host artifact,
    # so cross-host/NFS locking is out of scope (unix only: darwin/linux).
    with ledger.open("a+") as fh:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        fh.seek(0)
        rows = [json.loads(ln) for ln in fh.read().splitlines() if ln.strip()]
        attempt = _next_attempt(rows, promise, contract)
        row = _ledger_row(promise, seat, contract, summary, attempt, _now_iso(),
                          duration_s)
        fh.write(json.dumps(row) + "\n")
    return row


def _ledger_row(promise, seat, contract, summary, attempt, ts, duration_s) -> dict:
    """Pure: a verify outcome -> one ledger JSONL row (the schemas/ledger.xml
    field contract — these keys ARE the wire keys). verdict 'kept' iff no auto
    check failed; gate_band 'red' because a contract verify is the
    task-completion-band assessment that decides done. Only ever called for a
    fully-mechanical verify (manual==0) — the manual-pending guard lives in the
    caller so the mechanical assessor never records a verdict it cannot make
    (constitution §context-economy / §separation-of-privilege)."""
    return {
        "ts": ts,
        "seat": seat,
        "promise": promise,
        "contract": contract,
        "gate_band": "red",
        "exit_code": 0 if summary["ok"] else 1,
        "duration_s": duration_s,
        "attempt": attempt,
        "verdict": "kept" if summary["ok"] else "broken",
    }


def _promise_ref(root_el):
    """Pure: (promise_id, seat, contract_ref) from a <promise> root element, or
    (None, None, None) when it is not a recordable promise — a standalone
    contract has no executing seat to attribute a ledger row to. The shared
    promise->ledger identity used by both `contract verify --record` and the
    task-completion gate."""
    if root_el.tag != "promise":
        return None, None, None
    promiser = root_el.find("promiser")
    contract = root_el.find("contract")
    return (root_el.get("id"),
            promiser.get("seat") if promiser is not None else None,
            contract.get("ref") if contract is not None else None)


def cmd_contract(args):
    record = "--record" in args
    args = [a for a in args if a != "--record"]
    if not args or args[0] not in ("verify", "show"):
        sys.exit("usage: socom contract <verify|show> <promise-or-contract.xml> "
                 "[--record]")
    sub = args[0]
    if len(args) < 2:
        sys.exit(f"usage: socom contract {sub} <promise-or-contract.xml>")
    root = repo_root()
    f = Path(args[1])
    if not f.is_absolute():
        f = root / args[1]
    if not f.exists():
        sys.exit(f"socom contract: no such file '{args[1]}' (R6: degrade loudly).")
    try:
        root_el = ET.parse(f).getroot()
    except (ET.ParseError, OSError) as e:
        sys.exit(f"socom contract: {f.name} is not readable well-formed XML — {e}")
    contract = _contract_el(root_el)
    if contract is None:
        sys.exit(f"socom contract: no <contract> in {f.name} "
                 "(a promise embeds one, or pass a standalone contract).")
    checks = _contract_checks(contract)
    state = contract.get("state", "?")
    goal = " ".join((contract.findtext("goal") or "").split())

    if sub == "show":
        print(f"socom contract {contract.get('ref', '?')} [{state}]")
        print(f"  goal: {goal}")
        for c in checks:
            kind = f"run: {c['run']}" if c["auto"] else "MANUAL (no <run>)"
            print(f"  check {c['id']} · {c['assessor']} · {kind}")
            print(f"    expect: {c['expect']}")
        return

    # verify: run each auto check, report; manual checks flagged, never passed.
    if state != "ratified":
        print(f"socom contract: WARN — {contract.get('ref', '?')} state is "
              f"'{state}', not 'ratified' (work runs against ratified contracts).")
    import json, time
    _t0 = time.monotonic()
    results = []
    for c in checks:
        if c["auto"]:
            cp = subprocess.run(c["run"], shell=True, cwd=root,
                                capture_output=True, text=True)
            passed = cp.returncode == 0
            tail = (cp.stdout + cp.stderr).strip().splitlines()[-1:] or [""]
            print(f"  check {c['id']} · {c['assessor']} · "
                  f"{'PASS' if passed else 'FAIL'} (exit {cp.returncode})")
            print(f"    $ {c['run']}")
            print(f"    expect: {c['expect']}")
            if tail[0]:
                print(f"    output: {tail[0][:100]}")
            results.append({**c, "passed": passed})
        else:
            print(f"  check {c['id']} · {c['assessor']} · MANUAL — "
                  f"needs {c['assessor']}, not auto-verifiable")
            print(f"    expect: {c['expect']}")
            results.append({**c, "passed": False})

    duration_s = int(time.monotonic() - _t0)
    s = _verify_summary(results)
    print(f"socom contract verify: {s['passed']} passed, {s['failed']} failed, "
          f"{s['manual']} manual -> {'OK' if s['ok'] else 'FAILED'}")
    if s["manual"]:
        print(f"  {s['manual']} manual check(s) still need an assessor — "
              "verify confirms the auto checks only (fail-closed on the rest).")

    # --record: append this verify outcome to the run ledger so `socom cycle`
    # rolls REAL data (the first automatic producer; cycle/lesson otherwise
    # measure synthetic rows). Guarded: a row is the assessment of record, not
    # every exploratory run, so it is opt-in. A promise (id + promiser seat) is
    # required — a standalone contract has no executing seat to attribute. And
    # a row is WITHHELD while any check is MANUAL: the verdict then belongs to
    # the human assessor, and the mechanical assessor must not claim it
    # (constitution §separation-of-privilege — assessment is never delegated to
    # the promiser). The row is the same fail-closed posture #6 gave verify.
    if record:
        promise_id, seat, cref = _promise_ref(root_el)
        if not promise_id or not seat:
            print("socom contract verify: --record needs a promise with a "
                  "promiser seat (a standalone contract has no executing seat "
                  "to attribute) — no ledger row written.", file=sys.stderr)
        elif s["manual"]:
            print("socom contract verify: --record withheld — "
                  f"{s['manual']} manual check(s) pending; the verdict is the "
                  "human assessor's to record, not the mechanical runner's "
                  "(§separation-of-privilege).", file=sys.stderr)
        elif s["passed"] + s["failed"] == 0:
            print("socom contract verify: --record withheld — no auto check "
                  "ran, so there is no evidence to record. A vacuous 'kept' in "
                  "the ledger is exactly what verify-never-claim forbids.",
                  file=sys.stderr)
        else:
            row = _append_ledger_row(root, promise_id, seat, cref, s,
                                     duration_s)
            print(f"socom contract verify: recorded ledger row — {seat} "
                  f"{promise_id} attempt {row['attempt']} verdict "
                  f"{row['verdict']} (.socom/ledger/runs.jsonl).")

    if not s["ok"]:
        sys.exit(1)
