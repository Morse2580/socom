"""socom monarch — reconcile-and-reap supervisor over run records. Assembled into bin/socom by build.py."""
from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import textwrap
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from socom.core import SOCOM_DIR, _now_iso, load_cfg, log_breach, repo_root
from socom.ledger import _append_ledger_row
from socom.spawn import (RUNS_DIR, RUNTIMES, _atomic_write_locked, _resolve_promise,
                         _resolve_seat, _spawn_run)

# === BODY ===

# ── monarch — the supervisor half of orchestration (spawn launches, monarch
# reconciles). NOT a daemon: a reconcile-and-reap pass over the on-disk run
# records spawn writes, modeled on a track/supervise daemon lifecycle. `monarch`
# (tally) is read-only — it probes each open run's liveness with os.kill(pid, 0)
# and prints who is running / done / dead. `monarch reap` generalizes the claim
# reaper (claims.py reap_orphans): a record marked running whose pid is gone is
# flipped to dead (atomic) and logged as exactly ONE amber breach — idempotent,
# because after the flip the record is no longer running. The reap is wired into
# `gate session-start` beside the claim reaper, so dead runs never linger.
#   VERDICT BOUNDARY preserved: the verdict comes from the run DYING (observed by
# the supervisor), never from the worker self-asserting. A reaped death MAY append
# a `broken` ledger row so `cycle` scoring sees the failure.

# A run started on another host/boot carries a pid meaningless here; os.kill can
# coincidentally hit an unrelated live pid. So a record older than this horizon is
# treated dead regardless of a probe — the claim-TTL precedent (claims.py), scaled
# up because a run legitimately outlives an 8h claim.
RUN_STALE_HOURS = 72


def _pid_alive(pid) -> bool:
    """True iff signal 0 is deliverable to pid on THIS host. ESRCH (no such
    process) = dead; EPERM (exists, owned by another user) = alive; a falsy/non-int
    pid = dead. Pure probe — sends no real signal."""
    if not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False


def _stale(rec, now) -> bool:
    """True iff the record's ts_started is older than RUN_STALE_HOURS (or
    unparseable — an unparseable start is a dead record, mirroring claim_expired)."""
    try:
        ts = datetime.fromisoformat(rec.get("ts_started"))
    except (ValueError, TypeError):
        return True
    return (now - ts).total_seconds() / 3600 > RUN_STALE_HOURS


def _classify(rec, now) -> str:
    """Pure: a run record + now -> running | done | dead | its own status. A
    non-running status passes through (materialized/done/dead are facts on record).
    A running record is dead unless its pid probes alive AND it is within the
    staleness horizon — so a killed pid (ESRCH) or a long-stale record reads dead,
    while a live, fresh pid reads running."""
    st = rec.get("status")
    if st != "running":
        return st or "unknown"
    if _stale(rec, now):
        return "dead"
    return "running" if _pid_alive(rec.get("pid")) else "dead"


def _uptime(rec, now) -> str:
    """Pure: a human uptime (now - ts_started) as Ns/Nm/Nh/Nd, or '?' if unparseable."""
    try:
        ts = datetime.fromisoformat(rec.get("ts_started"))
    except (ValueError, TypeError):
        return "?"
    secs = max(0, int((now - ts).total_seconds()))
    if secs < 60:
        return f"{secs}s"
    if secs < 3600:
        return f"{secs // 60}m"
    if secs < 86400:
        return f"{secs // 3600}h"
    return f"{secs // 86400}d"


def _load_runs(root: Path) -> list:
    """Every parseable run record under .socom/runs (R-*.json). A torn/unreadable
    record is skipped, never fatal — the same posture cycle takes on a bad row."""
    rundir = root / SOCOM_DIR / RUNS_DIR
    out = []
    if not rundir.exists():
        return out
    for p in sorted(rundir.glob("R-*.json")):
        try:
            out.append((p, json.loads(p.read_text())))
        except (json.JSONDecodeError, OSError):
            continue
    return out


def reap_dead_runs(root: Path) -> list:
    """Generalizes reap_orphans (claims.py) to runs: each record marked running
    whose liveness classifies dead is rewritten status=dead (atomic, locked), and
    exactly ONE amber breach is logged. Idempotent — after the flip the record is
    no longer running, so a re-reap (or a second session-start) logs nothing. MAY
    append a `broken` ledger row so cycle sees the failure (the verdict is the run
    dying, observed here — not the worker self-asserting; the boundary holds).
    Returns report lines, like reap_orphans, for the caller to print."""
    report = []
    rundir = root / SOCOM_DIR / RUNS_DIR
    if not rundir.exists():
        return report
    now = datetime.now(timezone.utc)
    lock = rundir / ".lock"
    for p, rec in _load_runs(root):
        if rec.get("status") != "running" or _classify(rec, now) != "dead":
            continue
        rec["status"] = "dead"
        rec["ts_ended"] = _now_iso()
        if rec.get("exit_code") is None:
            rec["exit_code"] = 137  # presumed killed (128 + SIGKILL) — process gone
        _atomic_write_locked(p, json.dumps(rec, indent=2) + "\n", lock)
        log_breach(root, "monarch",
                   f"amber: run {rec.get('run_id')} died without verdict "
                   f"(seat {rec.get('seat')}, promise {rec.get('promise')})")
        report.append(f"reaped dead run: {rec.get('run_id')} "
                      f"(seat {rec.get('seat')}, promise {rec.get('promise')})")
        # broken ledger row — guarded on an attributable (promise, seat), the same
        # requirement contract verify --record enforces (a row needs an owner).
        promise, seat = rec.get("promise"), rec.get("seat")
        if promise and seat:
            _append_ledger_row(root, promise, seat, rec.get("contract"),
                               {"ok": False}, 0)
    return report


# ── monarch recover — the loop-closer (slice 4) ──────────────────────────────
# reap turns a dead-but-running run into dead + a broken row, then STOPS — recovery
# was manual. `recover` closes spawn<->monarch into a real loop: for a reaped run
# whose promise was never kept, it re-dispatches a fresh attempt THROUGH spawn's own
# brief-forge + record write (recover IS spawn, chosen by monarch instead of a human).
# Bounded by an attempt cap and opt-in --exec, so a flapping worker can never spin
# forever (the runaway backstop is the whole point — an unbounded auto-relauncher is
# the fix-the-class trap, not the fix). The dead record is NEVER mutated or deleted;
# each attempt is its own record, and a recovery-lineage line in the hashed core keeps
# the new id distinct + the lineage traceable. recover NEVER writes a verdict — the
# verdict boundary holds (the new run is unjudged until a gate/reviewer/reap speaks).
RECOVER_MAX_ATTEMPTS = 3


def _read_ledger(root: Path) -> list:
    """Every parseable row of the run ledger (.socom/ledger/runs.jsonl), or [] if
    absent — the tolerant read posture _load_runs takes, so a torn ledger never
    aborts a recovery scan."""
    ledger = root / SOCOM_DIR / "ledger" / "runs.jsonl"
    if not ledger.exists():
        return []
    rows = []
    for ln in ledger.read_text().splitlines():
        if ln.strip():
            try:
                rows.append(json.loads(ln))
            except json.JSONDecodeError:
                continue
    return rows


def _promise_kept(ledger_rows: list, promise: str) -> bool:
    """True iff the ledger carries a `kept` verdict for this promise — a kept promise
    needs no recovery (reuse the ledger as the verdict-of-record, never the run record,
    which by the boundary never holds a verdict)."""
    return any(r.get("promise") == promise and r.get("verdict") == "kept"
               for r in ledger_rows)


def _attempts_on_file(runs: list, ledger_rows: list, promise: str) -> int:
    """How many attempts a promise has already cost — the max of the run records
    written for it (each spawn/recover is one) and the highest ledger attempt recorded
    for it. The max (not the sum) so the two signals reinforce rather than double-count
    — the conservative read that never OVER-spawns past the cap."""
    rec_n = sum(1 for _, r in runs if r.get("promise") == promise)
    led_n = max([int(r.get("attempt", 0)) for r in ledger_rows
                 if r.get("promise") == promise], default=0)
    return max(rec_n, led_n)


def recoverable(root: Path):
    """Read-only: bucket every promise with run records into (eligible, abandoned).
    A promise is ELIGIBLE iff its LATEST run classifies dead, it has no `kept` ledger
    verdict, NO run of it is currently running or materialized (so recover never stacks
    a second live worker on one promise — idempotent within a session), and it is under
    the attempt cap. It is ABANDONED iff it would be eligible but is at/over the cap
    (needs a human, not another auto-attempt). Pure-ish: reads runs + ledger, mutates
    nothing — both the recover command and the session-start pointer call it."""
    now = datetime.now(timezone.utc)
    runs = _load_runs(root)
    ledger = _read_ledger(root)
    by_promise = {}
    for p, rec in runs:
        promise = rec.get("promise")
        if promise:
            by_promise.setdefault(promise, []).append(rec)
    eligible, abandoned = [], []
    for promise, recs in by_promise.items():
        if any(_classify(r, now) == "running" for r in recs):
            continue  # a live worker exists — never double-dispatch
        if any(r.get("status") == "materialized" for r in recs):
            continue  # a printed-but-unlaunched dispatch is already pending
        if _promise_kept(ledger, promise):
            continue  # already kept — nothing to recover
        latest = max(recs, key=lambda r: r.get("ts_started", ""))
        if _classify(latest, now) != "dead":
            continue
        attempts = _attempts_on_file(runs, ledger, promise)
        entry = {"promise": promise, "dead": latest, "attempts": attempts}
        (abandoned if attempts >= RECOVER_MAX_ATTEMPTS else eligible).append(entry)
    return eligible, abandoned


def _abandoned_already(root: Path, promise: str) -> bool:
    """True iff an abandon breach for this promise is already on record — so the
    abandon breach fires exactly ONCE (the breach-once posture reap proved, here keyed
    on the breach log rather than a status flip, since the dead record is never mutated)."""
    log = root / SOCOM_DIR / "gates" / "breaches.log"
    if not log.exists():
        return False
    needle = f"promise {promise} abandoned"
    return any(needle in ln for ln in log.read_text().splitlines())


def _abandon(root: Path, entry: dict):
    """Log exactly one amber breach for a promise at/over the attempt cap — idempotent
    (a second recover of an already-abandoned promise logs nothing)."""
    promise = entry["promise"]
    if _abandoned_already(root, promise):
        return False
    log_breach(root, "monarch",
               f"amber: promise {promise} abandoned after {entry['attempts']} "
               "attempts — needs a human (monarch recover cap reached)")
    return True


def _recover_one(root: Path, cfg: dict, entry: dict, exec_: bool):
    """Re-dispatch ONE eligible promise through spawn's shared launch core. Re-resolves
    the seat (preserving the dead run's model) and re-reads the original promise file,
    then calls _spawn_run with a recovery-lineage line — producing a NEW record (the dead
    one is left intact). Returns the _spawn_run result, or None if the promise source is
    gone (degrade loudly, skip — never abort the whole recovery pass)."""
    dead = entry["dead"]
    seat = dead.get("seat")
    promise_path = dead.get("promise_path")
    if not seat or not promise_path:
        print(f"  skip {dead.get('run_id')}: record predates promise_path — "
              "cannot re-resolve its source (re-spawn it by hand).", file=sys.stderr)
        return None
    if not (root / promise_path).exists():
        print(f"  skip {entry['promise']}: promise source '{promise_path}' is gone — "
              "cannot re-dispatch (degrade loudly).", file=sys.stderr)
        return None
    runtime, model, role = _resolve_seat(root, cfg, seat, model_override=dead.get("model"))
    pr = _resolve_promise(root, promise_path)
    attempt_n = entry["attempts"] + 1
    lineage = (f"recovery attempt {attempt_n} of {dead.get('run_id')} — the prior "
               "attempt died unkept; this is a fresh, independently-judged run.")
    return _spawn_run(root, seat, runtime, model, role, pr,
                      contract_override=dead.get("contract"), exec_=exec_,
                      lineage=lineage)


def _cmd_recover(root: Path, args: list):
    """`socom monarch recover [--exec]` — re-dispatch dead-but-unkept promises under the
    attempt cap. Default prints the re-spawn command(s) and exits 0 (record-first, no
    process launched); --exec background-launches each through spawn's own --exec path.
    Promises at/over the cap log one abandon breach (idempotent) and are NOT re-spawned."""
    exec_ = "--exec" in args
    cfg = load_cfg(root)
    eligible, abandoned = recoverable(root)

    abandoned_now = sum(1 for e in abandoned if _abandon(root, e))
    if abandoned:
        print(f"socom monarch recover: {len(abandoned)} promise(s) at the attempt cap "
              f"(>= {RECOVER_MAX_ATTEMPTS}) — abandoned, needs a human"
              + (f"; {abandoned_now} newly logged." if abandoned_now else " (already logged)."))
        for e in abandoned:
            print(f"  abandoned: {e['promise']} ({e['attempts']} attempts)")

    if not eligible:
        print("socom monarch recover: no promises eligible for recovery "
              "(dead + unkept + under the cap).")
        return

    print(f"socom monarch recover: {len(eligible)} promise(s) eligible "
          f"({'launching' if exec_ else 'printing re-spawn command(s)'}):")
    for e in eligible:
        r = _recover_one(root, cfg, e, exec_)
        if r is None:
            continue
        if r["launched"]:
            print(f"  re-dispatched {e['promise']} -> {r['run_id']} "
                  f"(attempt {e['attempts'] + 1}) as pid {r['pid']} [status=running]")
        else:
            print(f"  {e['promise']} -> {r['run_id']} (attempt {e['attempts'] + 1}) "
                  f"[status=materialized]; launch (or re-run with --exec):")
            print(f"    {r['cmd']}")
    if not exec_:
        print("  recover is record-first: re-run with --exec to launch, or paste a "
              "command above. The dead record stays on disk; the verdict is unwritten "
              "until a gate/reviewer/reap speaks.")


def cmd_monarch(args):
    root = repo_root()

    if args and args[0] == "recover":
        return _cmd_recover(root, args[1:])

    if args and args[0] == "reap":
        lines = reap_dead_runs(root)
        for ln in lines:
            print(f"  {ln}")
        if lines:
            print(f"socom monarch reap: {len(lines)} dead run(s) reaped "
                  "(status flipped to dead, one amber breach each).")
        else:
            print("socom monarch reap: no dead-but-running runs to reap.")
        return

    if args and args[0] not in ("tally",):
        sys.exit("usage: socom monarch [tally] | socom monarch reap | "
                 "socom monarch recover [--exec]")

    # tally (default) — read-only liveness reconcile over every open run.
    now = datetime.now(timezone.utc)
    rows = [(rec, _classify(rec, now)) for _, rec in _load_runs(root)]
    running = [r for r, c in rows if c == "running"]
    dead = [r for r, c in rows if c == "dead"]
    done = [r for r, c in rows if c == "done"]
    # everything that is neither running/dead/done — chiefly materialized
    # (printed-but-not-launched) runs — so the summary counts equal the on-disk
    # record count (running + dead + done + pending == len(rows)).
    pending = [r for r, c in rows if c not in ("running", "dead", "done")]
    oldest = min(running, key=lambda r: r.get("ts_started", ""), default=None)
    tail = f", oldest {oldest.get('seat')} {_uptime(oldest, now)}" if oldest else ""
    pend = f", {len(pending)} pending" if pending else ""
    print(f"socom monarch: {len(running)} running, {len(dead)} dead, "
          f"{len(done)} done{pend}{tail}")
    if not rows:
        print("  (no runs on record — launch a worker with `socom spawn`.)")
        return
    print(f"  {'run-id':<31} {'seat':<10} {'promise':<16} {'uptime':<8} status")
    for rec, c in rows:
        print(f"  {rec.get('run_id', ''):<31} {rec.get('seat', ''):<10} "
              f"{rec.get('promise', ''):<16} {_uptime(rec, now):<8} {c}")
