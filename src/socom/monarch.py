"""socom monarch — reconcile-and-reap supervisor over run records. Assembled into bin/socom by build.py."""
from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import signal
import subprocess
import sys
import textwrap
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from socom.core import SOCOM_DIR, SOCOM_VERSION, _now_iso, load_cfg, log_breach, repo_root
from socom.ledger import _append_ledger_row
from socom.lesson import _lesson_attr, _lesson_files, _lesson_statement
from socom.spawn import (RUNS_DIR, RUNTIMES, _atomic_write_locked, _resolve_promise,
                         _resolve_runtime_budget, _resolve_seat, _spawn_run)

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


def _overrun(rec, now) -> bool:
    """True iff a run has a POSITIVE wall-clock budget (max_runtime_s) and has been
    running past it — the Phase-1 runaway-spend backstop. DISTINCT from _stale: stale is
    the 72h record horizon for a pid that may already be gone; overrun targets a run that
    is (likely) still ALIVE and still burning, so reap must actively KILL it. A 0/absent/
    invalid budget => no deadline (legacy records and explicit opt-out fall through to
    staleness only). An unparseable ts_started is left to _stale, not double-judged here."""
    budget = rec.get("max_runtime_s")
    if isinstance(budget, bool) or not isinstance(budget, int) or budget <= 0:
        return False
    try:
        ts = datetime.fromisoformat(rec.get("ts_started"))
    except (ValueError, TypeError):
        return False
    return (now - ts).total_seconds() > budget


def _kill(pid) -> bool:
    """SIGKILL a live run's pid — the ACTIVE half of the runtime budget. reap observes
    the death it just caused, so the verdict boundary holds (the worker never self-asserts;
    the supervisor ends it and records the broken verdict). Tolerant by construction: a gone
    pid (already dead), a non-int, or a pid owned by another user is a no-op returning False —
    never raises, so one unkillable record never aborts a reap pass."""
    if not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(pid, signal.SIGKILL)
        return True
    except (ProcessLookupError, PermissionError, OSError):
        return False


def _classify(rec, now) -> str:
    """Pure: a run record + now -> running | done | dead | its own status. A
    non-running status passes through (materialized/done/dead are facts on record).
    A running record is dead unless its pid probes alive AND it is within the
    staleness horizon — so a killed pid (ESRCH) or a long-stale record reads dead,
    while a live, fresh pid reads running."""
    st = rec.get("status")
    if st != "running":
        return st or "unknown"
    if _stale(rec, now) or _overrun(rec, now):
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
        # active enforcement (Phase-1 runaway guard): a still-alive pid being reaped is a
        # runaway overrun (or a stale survivor); either way it must stop burning the moment
        # we record it dead. Killing it here keeps reap the SOLE place a verdict is written
        # — the supervisor ends the run and observes the death (the boundary holds).
        overrun = _overrun(rec, now)
        killed = _kill(rec.get("pid")) if _pid_alive(rec.get("pid")) else False
        rec["status"] = "dead"
        rec["ts_ended"] = _now_iso()
        if rec.get("exit_code") is None:
            rec["exit_code"] = 137  # 128 + SIGKILL — killed or presumed killed
        _atomic_write_locked(p, json.dumps(rec, indent=2) + "\n", lock)
        reason = "exceeded its runtime budget" if overrun else "died without verdict"
        killnote = " — killed by monarch" if killed else ""
        log_breach(root, "monarch",
                   f"amber: run {rec.get('run_id')} {reason}{killnote} "
                   f"(seat {rec.get('seat')}, promise {rec.get('promise')})")
        report.append(f"reaped {'overrun' if overrun else 'dead'} run: "
                      f"{rec.get('run_id')} (seat {rec.get('seat')}, "
                      f"promise {rec.get('promise')}){killnote}")
        # broken ledger row — guarded on an attributable (promise, seat), the same
        # requirement contract verify --record enforces (a row needs an owner).
        promise, seat = rec.get("promise"), rec.get("seat")
        if promise and seat:
            # the dying run carries its own model — record it so per-(seat,model)
            # trust (slice 9) attributes this death to the model that produced it.
            _append_ledger_row(root, promise, seat, rec.get("contract"),
                               {"ok": False}, 0, rec.get("model"))
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
    runtime, model, role, budget = _resolve_seat(root, cfg, seat,
                                                 model_override=dead.get("model"))
    pr = _resolve_promise(root, promise_path)
    attempt_n = entry["attempts"] + 1
    lineage = (f"recovery attempt {attempt_n} of {dead.get('run_id')} — the prior "
               "attempt died unkept; this is a fresh, independently-judged run.")
    return _spawn_run(root, seat, runtime, model, role, pr,
                      contract_override=dead.get("contract"), exec_=exec_,
                      lineage=lineage, budget=budget,
                      max_runtime_s=_resolve_runtime_budget(cfg))


# ── monarch triage — heuristic relevance over which dead runs to recover (slice 5)
# recover is MECHANICAL: it offers every eligible dead-but-unkept run in dict order.
# triage makes it SMART — it RANKS the already-eligible promises by recovery-worth,
# retrieved the SAME way `socom query` ranks (l0 keyword overlap, the stdlib floor), so
# the most-relevant dead runs surface first and a pass can be bounded to the top. triage
# NEVER widens eligibility (recoverable() still decides WHO is eligible); it only ORDERS
# and BOUNDS. The triage/recover split mirrors tally/reap: triage is the read-only ranked
# view, recover is the act — now ordered by triage instead of by filesystem iteration.


def _run_intent(root: Path, dead: dict) -> str:
    """The MEANINGFUL intent of a dead run's promise (verbatim + decoded + goal — the
    same signal spawn's residuality trigger reads), for ranking. TOLERANT by design: a
    missing promise_path, a gone source, or a torn promise yields "" (it ranks low),
    never an abort — ranking is best-effort, unlike the strict _resolve_promise recover
    uses to actually dispatch (which SHOULD be loud)."""
    pp = dead.get("promise_path")
    if not pp:
        return ""
    f = root / pp
    if not f.exists():
        return ""
    try:
        proot = ET.parse(f).getroot()
    except (ET.ParseError, OSError):
        return ""
    parts = []
    for path in ("intent/verbatim", "intent/decoded", "contract/goal"):
        el = proot.find(path)
        if el is not None and el.text:
            parts.append(" ".join(el.text.split()))
    return " ".join(parts)


def _active_lessons_text(root: Path) -> str:
    """The concatenated statements of the ACTIVE domain lessons — the repo's earned
    wisdom, used as the relevance focus when triage gets no explicit FOCUS. Lifecycle-
    honest: only state=active counts (the SAME filter spawn's envelope applies); a
    retired/provisional lesson never colours the ranking."""
    out = []
    for f in _lesson_files(root):
        t = f.read_text()
        if _lesson_attr(t, "state") == "active":
            out.append(_lesson_statement(t))
    return " ".join(out)


def _seat_trust(ledger_rows: list) -> dict:
    """Per-(seat, model) trust = the LAPLACE-SMOOTHED kept-rate over the ledger's verdicts:
    (kept + 1) / (kept + broken + 2) (the rule of succession). Small samples are damped
    (one kept of one -> 2/3, not 1.0); an unseen (seat, model) pair resolves to the 1/2 prior
    via `_trust_of`. The KEY is the (seat, model) pair (slice 9): trust is scoped to the model
    that produced the verdicts, so a model UPGRADE starts the seat at the neutral prior under
    the new model rather than inheriting the old model's reputation. A row's model is
    `r.get("model")` (None for legacy/manual rows -> an inert (seat, None) bucket no live dead
    run consumes, since run records always carry a model). The denominator counts ONLY
    kept/broken verdicts (the verdicts of record); any other verdict on a torn/hand-edited row
    is ignored, never counted as a failure. Reuses the ledger — no new store (slice 7)."""
    kept, seen = {}, {}  # keyed by (seat, model); seen = kept + broken (the denominator)
    for r in ledger_rows:
        s, v = r.get("seat"), r.get("verdict")
        if not s or v not in ("kept", "broken"):
            continue
        key = (s, r.get("model"))
        seen[key] = seen.get(key, 0) + 1
        if v == "kept":
            kept[key] = kept.get(key, 0) + 1
    return {k: (kept.get(k, 0) + 1) / (seen[k] + 2) for k in seen}


def _trust_of(trust_map: dict, seat, model) -> float:
    """The (seat, model) pair's trust, or the neutral 1/2 no-history prior (unproven is not
    failed — the Laplace limit of zero verdicts). An upgraded model is unseen for the seat, so
    it resolves to 1/2: reset, not inherited (slice 9)."""
    return trust_map.get((seat, model), 0.5)


def _triage_rank(root: Path, eligible: list, focus=None):
    """Rank the eligible bucket by recovery-worth, highest first — a COMPOSITE of
    relevance (PRIMARY) and per-seat trust (SECONDARY), then the tie-break. Relevance =
    overlap of each promise's meaningful intent with a FOCUS (explicit query, else the
    active-lesson corpus) — the SAME l0 keyword-overlap count the query floor uses (slice
    5). Trust = the Laplace-smoothed kept-rate of the run's (SEAT, MODEL) (slice 7/9): scoped
    to the model recover will re-run it with (`_recover_one` preserves the dead run's model),
    so an upgraded model starts at the neutral prior rather than inheriting the old model's
    reputation. A likely-to-succeed (seat, model) ranks higher, but only among EQUALLY-relevant
    runs (relevance stays dominant). The sort key is (−worth, −trust, then the tie-break
    pre-sort: fewer attempts,
    more-recent death, run-id) — a single stable sort over a tie-break-ordered list, so
    equal (worth, trust) keep the tie-break order, and trust becomes the effective primary
    only when no relevance signal exists. Returns (ranked_entries_with_worth_and_trust,
    basis_string)."""
    # tie-break pre-sort: least-significant key first (stable sort composes them).
    pre = sorted(eligible, key=lambda e: e["dead"].get("run_id", ""))
    pre = sorted(pre, key=lambda e: e["dead"].get("ts_started", ""), reverse=True)
    pre = sorted(pre, key=lambda e: e["attempts"])
    if focus:
        focus_text, relbasis = focus, f"focus: {focus}"
    else:
        focus_text, relbasis = _active_lessons_text(root), "earned lessons"
    qwords = set(re.findall(r"\w+", (focus_text or "").lower()))
    trust = _seat_trust(_read_ledger(root))
    enriched = []
    for e in pre:
        itext = _run_intent(root, e["dead"])
        worth = len(qwords & set(re.findall(r"\w+", itext.lower()))) if qwords else 0
        enriched.append({**e, "worth": worth, "_intent": itext,
                         "trust": _trust_of(trust, e["dead"].get("seat"),
                                            e["dead"].get("model"))})
    # composite, relevance PRIMARY then trust; the pre-sort tie-break survives equal keys.
    ranked = sorted(enriched, key=lambda x: (-x["worth"], -x["trust"]))
    relevance_active = any(x["worth"] for x in ranked)
    trust_active = len({round(x["trust"], 6) for x in ranked}) > 1
    if relevance_active:
        basis = relbasis + (" + seat trust" if trust_active else "")
    elif trust_active:
        basis = "seat trust (no relevance signal)"
    else:
        basis = "recency (no relevance or trust signal)"
    return ranked, basis


def _focus_arg(args: list):
    """The first positional (non-flag) token in args, skipping --top's value — the
    optional FOCUS query for triage/recover. None when only flags are present."""
    out, i = [], 0
    while i < len(args):
        a = args[i]
        if a == "--top":
            i += 2
            continue
        if a.startswith("--"):
            i += 1
            continue
        out.append(a)
        i += 1
    return out[0] if out else None


def _parse_top(args: list):
    """The --top N bound (a positive int) or None. A missing/non-positive/non-integer
    value exits nonzero, loud (R6) — a silent reinterpretation would mask operator error."""
    if "--top" not in args:
        return None
    i = args.index("--top")
    val = args[i + 1] if i + 1 < len(args) else None
    if val is None or not val.isdigit() or int(val) <= 0:
        sys.exit("socom monarch recover: --top needs a positive integer "
                 "(R6: degrade loudly).")
    return int(val)


def _cmd_triage(root: Path, args: list):
    """`socom monarch triage [FOCUS]` — read-only: rank the eligible dead-but-unkept runs
    by recovery-worth and print the plan, highest-worth first. Ranks ONLY what recover
    would already accept; mutates nothing; exits 0 (the tally posture)."""
    focus = _focus_arg(args)
    eligible, abandoned = recoverable(root)
    if not eligible:
        print("socom monarch triage: no eligible runs to rank "
              f"({len(abandoned)} at/over the cap, needs a human).")
        return
    ranked, basis = _triage_rank(root, eligible, focus)
    print(f"socom monarch triage: {len(ranked)} eligible run(s) ranked by "
          f"recovery-worth [{basis}].")
    now = datetime.now(timezone.utc)
    print(f"  {'#':<3} {'promise':<16} {'worth':<6} {'trust':<6} {'seat':<10} "
          f"{'attempts':<9} {'age':<7} run-id")
    for n, x in enumerate(ranked, 1):
        d = x["dead"]
        trust = f"{x['trust']:.2f}"
        print(f"  {n:<3} {x['promise']:<16} {x['worth']:<6} {trust:<6} "
              f"{d.get('seat', ''):<10} "
              f"{str(x['attempts']) + '/' + str(RECOVER_MAX_ATTEMPTS):<9} "
              f"{_uptime(d, now):<7} {d.get('run_id', '')}")
    print("  recover in this order with `socom monarch recover"
          + (f" {focus!r}" if focus else "") + " [--top N] [--exec]`.")


def _cmd_recover(root: Path, args: list):
    """`socom monarch recover [FOCUS] [--top N] [--exec]` — re-dispatch dead-but-unkept
    promises under the attempt cap, in TRIAGE order (most recovery-worth first). Default
    prints the re-spawn command(s) and exits 0 (record-first); --exec background-launches
    each through spawn's own --exec path. --top N bounds the pass to the N highest-worth;
    the remainder stay eligible for a later pass (reported, never silently dropped).
    Promises at/over the cap log one abandon breach (idempotent) and are NOT re-spawned."""
    exec_ = "--exec" in args
    top = _parse_top(args)
    focus = _focus_arg(args)
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

    ranked, basis = _triage_rank(root, eligible, focus)
    deferred = 0
    if top is not None and top < len(ranked):
        deferred = len(ranked) - top
        ranked = ranked[:top]

    print(f"socom monarch recover: {len(eligible)} eligible promise(s); recovering "
          f"{len(ranked)} in triage order [{basis}]"
          + (f"; {deferred} lower-worth deferred to a later pass." if deferred
             else "") + (":" if not deferred else ""))
    for e in ranked:
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


# ── trace — export the run registry + ledger as OpenTelemetry GenAI spans ────
# ROADMAP Phase 2a (observability). SOCOM already records every run (.socom/runs)
# and every verdict (the ledger), but in a SOCOM-private shape no trace tool reads.
# `trace` joins them into OTLP/JSON spans named by the OpenTelemetry GenAI semantic
# conventions (gen_ai.*) — a promise's attempts become sibling spans under one trace
# (trace_id = hash(promise)), so the whole registry replays in Phoenix / LangSmith /
# any OTLP consumer. Read-only, stdlib-only: the conventions are just attribute names,
# so no OTel SDK (SOCOM's one-dep rule holds). Token usage is emitted ONLY when a
# record carries it (gen_ai.usage.*) — SOCOM does not yet meter the runtime, so the
# cost rollup is duration-based and SAYS so (verify-never-claim: no fabricated tokens).

def _iso_nanos(s):
    """ISO stamp -> unix nanoseconds as a string (OTLP's wire type), or None if
    unparseable — a torn stamp drops the timestamp, never aborts the export."""
    try:
        return str(int(datetime.fromisoformat(s).timestamp() * 1_000_000_000))
    except (ValueError, TypeError):
        return None


def _attr(key, val):
    """One OTLP KeyValue. bool -> boolValue, int -> intValue (OTLP wants it stringified),
    everything else -> stringValue. Order matters: bool is an int subclass, so test it first."""
    if isinstance(val, bool):
        return {"key": key, "value": {"boolValue": val}}
    if isinstance(val, int):
        return {"key": key, "value": {"intValue": str(val)}}
    return {"key": key, "value": {"stringValue": str(val)}}


def _run_seconds(rec) -> int:
    """Wall-clock seconds a run record spans (ts_ended - ts_started), or 0 when either
    stamp is missing/torn — the duration-based cost proxy until the runtime is metered."""
    s, e = _iso_nanos(rec.get("ts_started")), _iso_nanos(rec.get("ts_ended"))
    return max(0, (int(e) - int(s)) // 1_000_000_000) if s and e else 0


def _run_overran(rec, now) -> bool:
    """True iff a run breached its wall-clock budget — the cost-rollup's overrun test,
    correct for BOTH finished and live runs (unlike _overrun, which compares ts_started to
    NOW and so only fits a still-running record). A killed run (exit 137) overran by
    definition; a FINISHED run overran iff its actual wall (_run_seconds) exceeded the
    budget; a still-in-flight run defers to the live deadline (_overrun)."""
    if rec.get("exit_code") == 137:
        return True
    b = rec.get("max_runtime_s")
    if not isinstance(b, int) or isinstance(b, bool) or b <= 0:
        return False
    secs = _run_seconds(rec)  # >0 only when ts_ended is present (a finished run)
    return secs > b if secs else _overrun(rec, now)


def _run_span(rec, now, verdict):
    """One OTLP span for a run record, attributes per the GenAI semantic conventions.
    Deterministic ids (trace = hash(promise) so attempts share a trace; span = hash(run_id))
    so re-export is stable. Span status from the run's lifecycle: done/exit0 -> OK,
    dead/killed -> ERROR, still-in-flight -> UNSET (the run is the span; the ledger verdict
    rides as a cross-reference attribute, never overriding what the run itself did)."""
    cls = _classify(rec, now)
    exit_code = rec.get("exit_code")
    if cls == "done" and exit_code in (0, None):
        status = {"code": 1}  # OK
    elif cls == "dead":
        status = {"code": 2, "message": "run died/killed without a kept verdict"}  # ERROR
    else:
        status = {"code": 0}  # UNSET — running/materialized
    attrs = [
        _attr("gen_ai.operation.name", "invoke_agent"),
        _attr("gen_ai.agent.name", rec.get("seat") or "?"),
        _attr("gen_ai.agent.id", rec.get("run_id") or "?"),
        _attr("gen_ai.conversation.id", rec.get("promise") or "?"),
    ]
    if rec.get("model"):
        attrs.append(_attr("gen_ai.request.model", rec["model"]))
    if rec.get("runtime"):
        attrs.append(_attr("gen_ai.provider.name", rec["runtime"]))
    # usage only when the record actually carries it — no fabricated token counts
    for k, conv in (("input_tokens", "gen_ai.usage.input_tokens"),
                    ("output_tokens", "gen_ai.usage.output_tokens")):
        if isinstance(rec.get(k), int) and not isinstance(rec.get(k), bool):
            attrs.append(_attr(conv, rec[k]))
    # socom-native cross-reference (namespaced so it never collides with gen_ai.*)
    attrs.append(_attr("socom.run.status", cls))
    if exit_code is not None:
        attrs.append(_attr("socom.run.exit_code", exit_code))
    if rec.get("max_runtime_s") is not None:
        attrs.append(_attr("socom.run.max_runtime_s", rec["max_runtime_s"]))
    if rec.get("contract"):
        attrs.append(_attr("socom.contract", rec["contract"]))
    if verdict:
        attrs.append(_attr("socom.promise.verdict", verdict))
    if status["code"] == 2:
        attrs.append(_attr("error.type", "run_died"))
    start = _iso_nanos(rec.get("ts_started"))
    end = (_iso_nanos(rec.get("ts_ended"))
           or (_iso_nanos(now.isoformat()) if cls == "running" else start))
    span = {
        "traceId": hashlib.sha256((rec.get("promise") or "?").encode()).hexdigest()[:32],
        "spanId": hashlib.sha256((rec.get("run_id") or "?").encode()).hexdigest()[:16],
        "name": f"invoke_agent {rec.get('model') or rec.get('seat') or '?'}",
        "kind": 1,  # SPAN_KIND_INTERNAL
        "attributes": attrs,
        "status": status,
    }
    if start:
        span["startTimeUnixNano"] = start
    if end:
        span["endTimeUnixNano"] = end
    return span


def _otlp_payload(runs, verdicts, now) -> dict:
    """Pure: run records + per-promise verdicts -> an OTLP/JSON ExportTraceServiceRequest
    (resourceSpans -> scopeSpans -> spans). The interop shape any OTLP collector ingests."""
    spans = [_run_span(rec, now, verdicts.get(rec.get("promise"))) for _, rec in runs]
    return {"resourceSpans": [{
        "resource": {"attributes": [_attr("service.name", "socom"),
                                    _attr("service.version", SOCOM_VERSION)]},
        "scopeSpans": [{"scope": {"name": "socom", "version": SOCOM_VERSION},
                        "spans": spans}],
    }]}


def cmd_trace(args):
    """`socom trace [--out PATH] [--stdout]` — export the run registry + ledger as OTLP/
    JSON GenAI spans (Phase 2a observability). Default writes .socom/traces/trace-<stamp>.json;
    --stdout streams the OTLP to stdout (the human rollup then goes to stderr, so the pipe
    stays clean). Read-only."""
    import json
    from collections import defaultdict
    root = repo_root()
    to_stdout = "--stdout" in args
    out_path = None
    if "--out" in args:
        i = args.index("--out")
        if i + 1 >= len(args) or args[i + 1].startswith("--"):
            sys.exit("socom trace: --out needs a path (R6: degrade loudly).")
        out_path = args[i + 1]
    now = datetime.now(timezone.utc)
    runs = _load_runs(root)
    if not runs:
        sys.exit("socom trace: no run records under .socom/runs — launch a worker with "
                 "`socom spawn` first (R6: degrade loudly, never an empty trace).")
    verdicts = {}
    for r in _read_ledger(root):
        if r.get("verdict") in ("kept", "broken"):
            verdicts[r.get("promise")] = r["verdict"]  # append-order: last verdict wins
    payload = json.dumps(_otlp_payload(runs, verdicts, now), indent=2) + "\n"

    if to_stdout:
        sys.stdout.write(payload)
    else:
        tdir = root / SOCOM_DIR / "traces"
        tdir.mkdir(parents=True, exist_ok=True)
        out = Path(out_path) if out_path else tdir / f"trace-{_now_iso().replace(':', '').replace('-', '')}.json"
        if not out.is_absolute():
            out = root / out
        out.write_text(payload)
        rel = out.relative_to(root.resolve()) if out.resolve().is_relative_to(root.resolve()) else out
        print(f"socom trace: wrote {len(runs)} OTLP/GenAI span(s) -> {rel}")

    # cost/latency rollup — duration-based (the runtime is not yet metered for tokens;
    # SAY so rather than print a fake $/token). Goes to stderr so --stdout stays a clean pipe.
    agg = defaultdict(lambda: {"runs": 0, "secs": 0, "overruns": 0})
    for _, rec in runs:
        a = agg[(rec.get("seat") or "?", rec.get("model") or "?")]
        a["runs"] += 1
        a["secs"] += _run_seconds(rec)
        if _run_overran(rec, now):
            a["overruns"] += 1
    w = sys.stderr
    print(f"socom trace: {len(runs)} run(s) across {len(agg)} (seat,model) pair(s) "
          "— cost view is duration-based (runtime not yet token-metered).", file=w)
    print(f"  {'seat':<10} {'model':<22} {'runs':<5} {'wall_s':<7} overruns", file=w)
    for (seat, model), a in sorted(agg.items()):
        print(f"  {seat:<10} {model:<22} {a['runs']:<5} {a['secs']:<7} {a['overruns']}", file=w)


def cmd_monarch(args):
    root = repo_root()

    if args and args[0] == "recover":
        return _cmd_recover(root, args[1:])

    if args and args[0] == "triage":
        return _cmd_triage(root, args[1:])

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
                 "socom monarch triage [FOCUS] | "
                 "socom monarch recover [FOCUS] [--top N] [--exec]")

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
