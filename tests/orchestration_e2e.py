#!/usr/bin/env python3
"""socom orchestration end-to-end — spawn launches, monarch reaps.

Drives the REAL bin/socom through the full lifecycle a user would exercise:
launch (spawn --exec) -> record -> kill the worker -> reconcile (monarch tally)
-> reap (monarch reap) -> amber breach + broken ledger row -> idempotent re-reap
-> the same reap firing inside `gate session-start`. Black-box, via subprocess,
in throwaway git repos with an isolated HOME — so it proves the assembled tool
RUNS, not just that the pure core is correct. Complements tests/smoke.sh's
black-box checks and tests/unit.py's white-box checks with a Python harness the
operator can run standalone:

    python3 tests/orchestration_e2e.py

Chained into checks.fast via tests/smoke.sh, so fast/medium/full + CI run it too.
"""
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOCOM = ROOT / "bin" / "socom"

PROMISE = """<promise id="P-E2E" state="open" domain="cli">
  <promiser seat="builder" participant="claude-code:default"/>
  <intent><verbatim from="human:moses" date="2026-06-21">spin up teh worker and watch it</verbatim>
  <decoded>Launch a builder and supervise it to completion.</decoded></intent>
  <contract ref="C-E2E" state="ratified"><goal>the run is supervised end to end</goal>
  <check id="1" assessor="gate:task-completion"><run>true</run><expect>record exists</expect></check>
</contract></promise>
"""

_fail = 0


def ok(msg):
    print(f"  ✓ {msg}")


def bad(msg):
    global _fail
    _fail += 1
    print(f"  ✗ {msg}")


def check(desc, cond):
    ok(desc) if cond else bad(desc)


def run(args, env, cwd):
    """Run bin/socom <args> in cwd with env; return (rc, stdout+stderr)."""
    cp = subprocess.run([str(SOCOM), *args], cwd=cwd, env=env,
                        capture_output=True, text=True)
    return cp.returncode, cp.stdout + cp.stderr


def the_record(repo):
    js = sorted((repo / ".socom" / "runs").glob("R-*.json"))
    return json.loads(js[0].read_text()) if js else None


def breach_lines(repo):
    log = repo / ".socom" / "gates" / "breaches.log"
    return [ln for ln in log.read_text().splitlines() if ln.strip()] if log.exists() else []


def main():
    tmp = Path(tempfile.mkdtemp())
    home = tmp / "home"
    home.mkdir()
    env = {**os.environ, "HOME": str(home), "SOCOM_SESSION": "e2e"}

    # a stub `claude` that stays alive until killed (exec sleep -> pid IS sleep).
    bindir = tmp / "bin"
    bindir.mkdir()
    stub = bindir / "claude"
    stub.write_text("#!/bin/sh\nexec sleep 600\n")
    stub.chmod(0o755)
    env_with_stub = {**env, "PATH": f"{bindir}{os.pathsep}{env['PATH']}"}

    repo = tmp / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main", "."], cwd=repo, check=True)
    rc, _ = run(["init", "."], env, repo)
    check("init a fresh repo (seats + canon planted)", rc == 0)
    (repo / ".socom" / "promises").mkdir(parents=True, exist_ok=True)
    (repo / ".socom" / "promises" / "p.xml").write_text(PROMISE)
    ppath = ".socom/promises/p.xml"

    killed_pid = None
    try:
        # ── spawn (default): materialize + print launch command, no verdict ──
        rc, out = run(["spawn", "--seat", "builder", "--promise", ppath], env, repo)
        check("spawn default exits 0", rc == 0)
        check("spawn default prints a launch command", 'claude -p' in out)
        rec = the_record(repo)
        check("spawn writes a materialized record (null pid)",
              rec and rec["status"] == "materialized" and rec["pid"] is None)
        check("record carries exactly the schema fields", rec and set(rec) == {
            "run_id", "seat", "promise", "contract", "runtime", "model",
            "status", "ts_started", "pid", "brief_path", "promise_path",
            "ts_ended", "exit_code"})
        brief = (repo / rec["brief_path"]).read_text()
        check("brief carries the literal user verbatim",
              "spin up teh worker and watch it" in brief)
        check("brief embeds the reused seat envelope",
              "builder" in brief and "You promise" in brief)
        rid1 = rec["run_id"]

        # idempotent id (same intent -> same content hash -> same run)
        run(["spawn", "--seat", "builder", "--promise", ppath], env, repo)
        runs = list((repo / ".socom" / "runs").glob("R-*.json"))
        check("spawn id is content-addressed + idempotent (one record)",
              len(runs) == 1 and runs[0].stem == rid1)

        # spawn never writes a verdict
        check("spawn writes NO ledger row (verdict boundary)",
              not (repo / ".socom" / "ledger" / "runs.jsonl").exists())

        # ── spawn --exec: launch the stub, capture a live pid ──
        for f in (repo / ".socom" / "runs").glob("R-*"):
            f.unlink()
        rc, out = run(["spawn", "--seat", "builder", "--promise", ppath, "--exec"],
                      env_with_stub, repo)
        check("spawn --exec exits 0", rc == 0)
        rec = the_record(repo)
        check("spawn --exec record is running with an int pid",
              rec and rec["status"] == "running" and isinstance(rec["pid"], int))
        killed_pid = rec["pid"]

        # ── monarch tally: the live run reads running ──
        rc, out = run(["monarch"], env, repo)
        check("monarch tally exits 0 (read-only)", rc == 0)
        check("monarch tally reports the live run as running",
              "1 running, 0 dead" in out and "running" in out.splitlines()[-1])

        # ── kill the worker: tally now classifies it dead (status still running) ──
        os.kill(killed_pid, signal.SIGKILL)
        for _ in range(50):
            try:
                os.kill(killed_pid, 0)
                time.sleep(0.05)
            except OSError:
                break
        rc, out = run(["monarch"], env, repo)
        check("monarch tally reconciles a killed worker to dead",
              "0 running, 1 dead" in out)
        check("tally is non-mutating (record still says running)",
              the_record(repo)["status"] == "running")

        # ── monarch reap: flip status, one amber breach, one broken ledger row ──
        rc, out = run(["monarch", "reap"], env, repo)
        check("monarch reap exits 0", rc == 0)
        check("monarch reap reports one reaped run", "1 dead run(s) reaped" in out)
        rec = the_record(repo)
        check("reap flips status to dead with an end stamp + exit code",
              rec["status"] == "dead" and rec["ts_ended"] and rec["exit_code"] == 137)
        breaches = breach_lines(repo)
        check("reap logs exactly ONE amber breach",
              len(breaches) == 1 and "died without verdict" in breaches[0]
              and rid1 in breaches[0])
        ledger = repo / ".socom" / "ledger" / "runs.jsonl"
        rows = [json.loads(x) for x in ledger.read_text().splitlines() if x.strip()] \
            if ledger.exists() else []
        check("reap appends one broken ledger row (cycle sees the failure)",
              len(rows) == 1 and rows[0]["verdict"] == "broken"
              and rows[0]["seat"] == "builder")

        # ── idempotent: a re-reap of the same dead run does nothing ──
        rc, out = run(["monarch", "reap"], env, repo)
        check("re-reap is idempotent (nothing to reap)",
              "no dead-but-running runs to reap" in out)
        check("re-reap logs no second breach", len(breach_lines(repo)) == 1)

        # ── wiring: gate session-start reaps dead runs beside the claim reaper ──
        for f in (repo / ".socom" / "runs").glob("R-*"):
            f.unlink()
        rc, out = run(["spawn", "--seat", "builder", "--promise", ppath, "--exec"],
                      env_with_stub, repo)
        pid2 = the_record(repo)["pid"]
        os.kill(pid2, signal.SIGKILL)
        for _ in range(50):
            try:
                os.kill(pid2, 0)
                time.sleep(0.05)
            except OSError:
                break
        before = len(breach_lines(repo))
        rc, out = run(["gate", "session-start"], env, repo)
        check("gate session-start reaps the dead run (wiring)",
              "reaped dead run" in out and the_record(repo)["status"] == "dead")
        check("gate session-start reap logged one more amber breach",
              len(breach_lines(repo)) == before + 1)

        # ── monarch recover (slice 4): re-dispatch a dead, unkept promise ──
        # the session-start above left exactly one dead, unkept run for the promise.
        # session-start should also POINT at the recovery debt (read-only, not acting).
        check("session-start points at the recoverable run (read-only debt)",
              "eligible for `socom monarch recover`" in out)
        dead = the_record(repo)

        # recover --exec: a NEW running record, a DISTINCT id, recovery lineage in the
        # brief, the dead record left intact (death history stays on disk).
        rc, out = run(["monarch", "recover", "--exec"], env_with_stub, repo)
        check("monarch recover --exec exits 0", rc == 0)
        check("recover reports one eligible promise", "1 eligible promise(s)" in out)
        recs = [json.loads(p.read_text())
                for p in sorted((repo / ".socom" / "runs").glob("R-*.json"))]
        live = [r for r in recs if r["status"] == "running"]
        deads = [r for r in recs if r["status"] == "dead"]
        recovered_pid = live[0]["pid"] if live else None
        check("recover --exec yields a NEW running record, dead one intact",
              len(recs) == 2 and len(live) == 1 and len(deads) == 1)
        check("the recovery run has a distinct id from the dead run",
              live and live[0]["run_id"] != dead["run_id"])
        if live:
            rbrief = (repo / live[0]["brief_path"]).read_text()
            check("the recovery brief carries the recovery-lineage line (traceable)",
                  "Recovery lineage" in rbrief and dead["run_id"] in rbrief)

        # idempotent within a session: a promise with a live run is never re-dispatched
        # (the second recover sees the running worker and offers nothing).
        rc, out = run(["monarch", "recover"], env, repo)
        check("recover never double-dispatches a promise with a live run",
              "no promises eligible" in out)
        if recovered_pid:
            os.kill(recovered_pid, signal.SIGKILL)

        # ── recover attempt cap: a promise at the cap is abandoned, not re-spawned ──
        # clean slate, then fabricate three dead, unkept runs for one synthetic promise
        # (3 == RECOVER_MAX_ATTEMPTS default). recover must refuse to spawn and log ONE
        # abandon breach — idempotently (the backstop against a flapping worker).
        for f in (repo / ".socom" / "runs").glob("R-*"):
            f.unlink()
        capdir = repo / ".socom" / "runs"
        for i in range(3):
            (capdir / f"R-CAP-{i}.json").write_text(json.dumps({
                "run_id": f"R-CAP-{i}", "seat": "builder", "promise": "P-CAP",
                "contract": "C-CAP", "runtime": "claude-code", "model": "default",
                "status": "dead", "ts_started": "2026-06-21T12:00:00+00:00",
                "pid": None, "brief_path": "b", "promise_path": ppath,
                "ts_ended": "2026-06-21T12:01:00+00:00", "exit_code": 137}))
        before = len(breach_lines(repo))
        rc, out = run(["monarch", "recover"], env, repo)
        check("recover abandons a promise at the attempt cap (no re-spawn)",
              "abandoned" in out and "P-CAP" in out)
        check("abandon logs exactly one amber breach",
              len(breach_lines(repo)) == before + 1)
        check("recover spawns nothing for an abandoned promise (records unchanged)",
              len(list(capdir.glob("R-CAP-*.json"))) == 3
              and not list(capdir.glob("R-2*.json")))
        before2 = len(breach_lines(repo))
        run(["monarch", "recover"], env, repo)
        check("re-recover is idempotent (no second abandon breach)",
              len(breach_lines(repo)) == before2)

        # ── monarch triage (slice 5): rank eligible dead runs by recovery-worth ──
        # clean slate; two eligible dead promises, one whose intent matches a FOCUS.
        for f in (repo / ".socom" / "runs").glob("R-*"):
            f.unlink()
        proms = repo / ".socom" / "promises"
        for pid, intent in (("P-TPX", "make the ledger flock serialize writers"),
                            ("P-TPY", "restyle the frontend widget colour palette")):
            (proms / f"{pid}.xml").write_text(
                f'<promise id="{pid}" domain="cli">'
                f'<promiser seat="builder" participant="x"/>'
                f'<intent><verbatim>{intent}</verbatim></intent>'
                f'<contract ref="C-{pid}" state="ratified"><goal>{intent}</goal>'
                f'<check id="1" assessor="gate"><run>true</run><expect>x</expect></check>'
                f'</contract></promise>')
            (repo / ".socom" / "runs" / f"R-{pid}.json").write_text(json.dumps({
                "run_id": f"R-{pid}", "seat": "builder", "promise": pid,
                "contract": f"C-{pid}", "runtime": "claude-code", "model": "default",
                "status": "dead", "ts_started": "2026-06-21T12:00:00+00:00",
                "pid": None, "brief_path": "b",
                "promise_path": f".socom/promises/{pid}.xml",
                "ts_ended": "2026-06-21T12:01:00+00:00", "exit_code": 137}))
        rc, out = run(["monarch", "triage", "flock"], env, repo)
        check("monarch triage exits 0 (read-only)", rc == 0)
        check("triage ranks the FOCUS-matching run first",
              "P-TPX" in out and "P-TPY" in out
              and out.index("P-TPX") < out.index("P-TPY"))
        check("triage mutates nothing (no new run record)",
              len(list((repo / ".socom" / "runs").glob("R-*.json"))) == 2)

        # recover FOCUS --top 1: re-dispatch only the top-worth promise, defer the rest
        rc, out = run(["monarch", "recover", "flock", "--top", "1"], env, repo)
        check("recover --top 1 exits 0", rc == 0)
        check("recover --top 1 defers the lower-worth promise (no silent drop)",
              "1 lower-worth deferred" in out)
        after = [json.loads(p.read_text())
                 for p in (repo / ".socom" / "runs").glob("R-*.json")]
        tpx = [r for r in after if r["promise"] == "P-TPX"]
        tpy = [r for r in after if r["promise"] == "P-TPY"]
        check("recover --top 1 re-dispatched ONLY the top-worth promise (P-TPX)",
              any(r["status"] == "materialized" for r in tpx)
              and all(r["status"] == "dead" for r in tpy))
        # --top with a bad value is loud
        rc, out = run(["monarch", "recover", "--top", "0"], env, repo)
        check("recover --top 0 exits nonzero (loud)", rc != 0)

        # ── per-seat envelope budget (slice 6): the seat's context_budget caps the brief ──
        for f in (repo / ".socom" / "runs").glob("R-*"):
            f.unlink()
        lessons = repo / ".socom" / "lessons"
        lessons.mkdir(exist_ok=True)
        for i in range(4):
            (lessons / f"L-B{i}.xml").write_text(
                f'<lesson id="L-B{i}" domain="cli" state="active"><statement embed="true">'
                f'supervise the spawned worker to completion lesson {i} '
                + ("x" * 60) + "</statement></lesson>")
        # default-budget spawn (the builder declares no context_budget -> 1200)
        run(["spawn", "--seat", "builder", "--promise", ppath], env, repo)
        rec0 = the_record(repo)
        brief0 = (repo / rec0["brief_path"]).read_text()
        n_default = brief0.count("**L-B")
        rid_default = rec0["run_id"]
        # tighten the builder's budget; the brief must carry FEWER lessons
        cfg = (repo / "socom.yaml").read_text().replace(
            "{ runtime: claude-code, model: default }",
            "{ runtime: claude-code, model: default, context_budget: 30 }")
        (repo / "socom.yaml").write_text(cfg)
        for f in (repo / ".socom" / "runs").glob("R-*"):
            f.unlink()
        run(["spawn", "--seat", "builder", "--promise", ppath], env, repo)
        rec1 = the_record(repo)
        brief1 = (repo / rec1["brief_path"]).read_text()
        n_tight = brief1.count("**L-B")
        check("a tight context_budget trims the envelope to fewer lessons",
              1 <= n_tight < n_default)
        check("a tight budget does NOT perturb the run-id (envelope is unhashed)",
              rec1["run_id"] == rid_default)
        check("a trimmed brief still says what it dropped (no silent truncation)",
              "trimmed to the envelope budget" in brief1)
        # an invalid context_budget exits loud, no record written
        (repo / "socom.yaml").write_text((repo / "socom.yaml").read_text().replace(
            "context_budget: 30", "context_budget: abc"))
        for f in (repo / ".socom" / "runs").glob("R-*"):
            f.unlink()
        rc, out = run(["spawn", "--seat", "builder", "--promise", ppath], env, repo)
        check("a non-integer context_budget exits loud",
              rc != 0 and "context_budget" in out)
        check("a loud budget error writes no run record",
              not list((repo / ".socom" / "runs").glob("R-*.json")))

        # ── per-seat trust weighting (slice 7): equal relevance -> trusted seat first ──
        # two eligible dead runs of EQUAL relevance under different seats; a ledger makes
        # builder mostly-kept and reviewer mostly-broken. The LOW-trust seat gets the
        # alphabetically-FIRST promise id, so ranking the builder run first proves TRUST
        # reordered it (not the run-id tie-break).
        for f in (repo / ".socom" / "runs").glob("R-*"):
            f.unlink()
        for pid, seat in (("P-TRA", "reviewer"), ("P-TRZ", "builder")):
            (proms / f"{pid}.xml").write_text(
                f'<promise id="{pid}" domain="cli">'
                f'<promiser seat="{seat}" participant="x"/>'
                f'<intent><verbatim>flock the ledger writers serialize</verbatim></intent>'
                f'<contract ref="C-{pid}" state="ratified"><goal>flock ledger writers</goal>'
                f'</contract></promise>')
            (repo / ".socom" / "runs" / f"R-{pid}.json").write_text(json.dumps({
                "run_id": f"R-{pid}", "seat": seat, "promise": pid,
                "contract": f"C-{pid}", "runtime": "claude-code", "model": "default",
                "status": "dead", "ts_started": "2026-06-21T12:00:00+00:00",
                "pid": None, "brief_path": "b",
                "promise_path": f".socom/promises/{pid}.xml",
                "ts_ended": "2026-06-21T12:01:00+00:00", "exit_code": 137}))
        ledger = repo / ".socom" / "ledger"
        ledger.mkdir(exist_ok=True)
        rows = ([{"promise": "hist-b", "seat": "builder", "verdict": "kept", "attempt": 1}] * 3
                + [{"promise": "hist-r", "seat": "reviewer", "verdict": "broken", "attempt": 1}] * 3)
        (ledger / "runs.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
        rc, out = run(["monarch", "triage", "flock"], env, repo)
        check("triage exits 0 with a ledger present", rc == 0)
        check("triage shows a trust column and names trust in the basis",
              "trust" in out and "trust" in out.splitlines()[0])
        check("equal relevance -> the higher-trust seat's run ranks first (trust beats run-id)",
              "P-TRZ" in out and "P-TRA" in out and out.index("P-TRZ") < out.index("P-TRA"))

    finally:
        if killed_pid:
            try:
                os.kill(killed_pid, signal.SIGKILL)
            except OSError:
                pass
        subprocess.run(["rm", "-rf", str(tmp)])

    if _fail:
        print(f"orchestration-e2e: {_fail} FAILURE(S)")
        return 1
    print("orchestration-e2e: all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
