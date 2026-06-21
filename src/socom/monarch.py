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
from socom.core import SOCOM_DIR, _now_iso, log_breach, repo_root
from socom.ledger import _append_ledger_row
from socom.spawn import RUNS_DIR, _atomic_write_locked

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


def cmd_monarch(args):
    root = repo_root()

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
        sys.exit("usage: socom monarch [tally] | socom monarch reap")

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
