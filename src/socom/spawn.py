"""socom spawn — record-first worker launch (orchestration). Assembled into bin/socom by build.py."""
from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import textwrap
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from socom.context import _estimate_tokens, _load_context_contract
from socom.core import SOCOM_DIR, _now_iso, load_cfg, repo_root, resource
from socom.ledger import _contract_checks, _contract_el
from socom.lesson import _lesson_attr, _lesson_files, _lesson_statement
from socom.lifecycle import render_agent
from socom.retrieval import l0_score

# === BODY ===

# ── spawn — launch a worker into a seat against a promise (R: orchestration) ─
# SOCOM was passive: it rendered briefs and scored runs but never LAUNCHED a
# worker, and nothing tracked the workers that were open. spawn makes a *run* a
# first-class, reapable artifact and splits launch (spawn writes the record) from
# supervision (monarch reconciles it — separate command). The run record is the
# source of truth; launching is a binding detail: default materializes the brief
# + record and PRINTS the launch command; --exec background-launches the runtime
# bound in socom.yaml. The load-bearing invariant: spawn NEVER writes a verdict —
# kept/broken belongs to the gate / contract verify --record / monarch-reap, never
# to the spawned worker (verify-never-claim, §separation-of-privilege). The record
# carries liveness + provenance, not judgment.
#   The run-id is content-addressed off the brief bytes (R-<YYYY-MMDD>-<seat>-
# <hash8>), mirroring the prompt-id scheme in handoff.py, so a re-spawn of
# identical intent is idempotent on id. Writes are atomic (sibling tmp + os.replace)
# and serialized under the SAME fcntl idiom as the run ledger.

RUNS_DIR = "runs"  # under .socom/ — the run registry monarch reconciles

# The heuristic envelope's earned-lessons subsection is bounded so the brief never
# grows without limit as the lesson corpus does — at most this many lessons, and
# the running token estimate (reusing context.py's single-sourced divisor) caps the
# subsection. Doctrine/residuality are fixed canon, not the unbounded-growth risk.
ENVELOPE_MAX_LESSONS = 5
ENVELOPE_BUDGET_TOKENS = 1200


# runtime: value in socom.yaml -> (binary, argv-builder). The binary is what must
# be on PATH for --exec; the builder turns a brief into the launch argv. Today
# only claude-code (headless `claude` reading the brief as its prompt); a new
# runtime is one entry here, never a fork of the launch logic.
def _claude_argv(binary, model, brief_text):
    argv = [binary]
    if model and model != "default":
        argv += ["--model", model]
    return argv + ["-p", brief_text]


def _claude_cmd(model, brief_path):
    """The copy-pasteable default-branch command (human pastes it). brief_path is
    repo-relative for readability; $(cat …) feeds the brief as the headless prompt."""
    flag = f" --model {model}" if model and model != "default" else ""
    return f"claude{flag} -p \"$(cat {brief_path})\""


RUNTIMES = {
    "claude-code": {"binary": "claude", "argv": _claude_argv, "cmd": _claude_cmd},
}


def _resolve_role(root: Path, seat: str):
    """The <role> element for a seat: adopted repos carry .socom/canon/roles.xml;
    the tool's own checkout (and the embedded distribution) resolve via resource()
    — the same on-disk-then-embedded fallback context.py uses for schemas. Returns
    the element or None (unknown seat)."""
    local = root / SOCOM_DIR / "canon" / "roles.xml"
    roles = (ET.parse(local).getroot() if local.exists()
             else ET.fromstring(resource("canon/roles.xml")))
    for r in roles.findall("role"):
        if r.get("id") == seat:
            return r
    return None


def _opt(args, name):
    """Pure: the value following --name in args, or None. --name with no following
    token (or a following --flag) reads as missing — loud at the caller."""
    if name in args:
        i = args.index(name)
        if i + 1 < len(args) and not args[i + 1].startswith("--"):
            return args[i + 1]
    return None


def _block_text(el) -> str:
    """Dedented, whitespace-trimmed text of an element (verbatim/decoded/goal). The
    verbatim is preserved as written (typos and all) modulo surrounding indentation
    — the embed contract of schemas/promise.xml."""
    if el is None or el.text is None:
        return ""
    return textwrap.dedent(el.text).strip()


def _forge_brief(verbatim, decoded, envelope, goal, checks, contract_ref,
                 op_env="") -> str:
    """Pure: assemble the dispatch brief in verbatim-protocol order (canon/session.xml,
    schemas/memory.xml): USER VERBATIM -> DECODED -> seat envelope -> contract goal +
    checks -> [Operating envelope] -> pointer to constitution and gates. The literal
    verbatim block is REQUIRED (the reviewer's blind-spot defense reads it). The CORE
    (everything but op_env) carries no timestamp or run-id, so identical intent yields
    identical core bytes -> an idempotent content hash; op_env is appended UNHASHED so
    the growing lesson corpus never perturbs the run-id."""
    out = ["# Dispatch brief", "",
           "## USER VERBATIM (the originating intent, human words — do not paraphrase)",
           "", "> " + (verbatim or "(no verbatim recorded)").replace("\n", "\n> "), ""]
    if decoded:
        out += ["## DECODED (labeled interpretation, separate from the verbatim)",
                "", decoded, ""]
    out += ["## Your seat", "", envelope.strip(), ""]
    out += [f"## Contract {contract_ref or '(none)'} — what done means", ""]
    out += [f"Goal: {goal}" if goal else "Goal: (no goal recorded)", ""]
    if checks:
        out.append("Checks (falsifiable):")
        for c in checks:
            how = f"run: {c['run']}" if c["auto"] else "MANUAL (assessor judges)"
            out.append(f"- [{c['id']}] {c['assessor']} — {how}; expect: {c['expect']}")
        out.append("")
    if op_env:
        out += [op_env.rstrip(), ""]
    out += ["## Authority",
            "Constitution and gates: see CLAUDE.md. Run `socom gate task-completion "
            "<promise>` to record your verdict — you never mark your own promise kept; "
            "assessors do. Verify, never claim: evidence is replayable commands + exit "
            "codes.", ""]
    return "\n".join(out)


def _canon_doc(root: Path, name: str):
    """A canon document element: adopted repos carry .socom/canon/<name>; the tool's
    own checkout (and the embedded distribution) resolve via resource() — the same
    on-disk-then-embedded fallback _resolve_role uses for roles."""
    local = root / SOCOM_DIR / "canon" / name
    return (ET.parse(local).getroot() if local.exists()
            else ET.fromstring(resource("canon/" + name)))


def _envelope_lessons(root: Path, domain, goal) -> list:
    """Active domain lessons ranked against the promise goal by REUSING l0_score (the
    query verb's keyword floor — the lesson set is small and domain-pre-filtered, so
    the BM25 index is not required and spawn stays index-free). Lifecycle-honest: only
    state=active surfaces; a retired/provisional lesson never does. Domain-filtered
    when the promise carries a domain. Returns ranked lesson dicts (id + statement)."""
    cands = []
    for f in _lesson_files(root):
        t = f.read_text()
        if _lesson_attr(t, "state") != "active":
            continue
        if domain and _lesson_attr(t, "domain") != domain:
            continue
        cands.append({"id": f.stem, "text": _lesson_statement(t), "metadata": {}})
    if not cands:
        return []
    by_id = {c["id"]: c for c in cands}
    return [by_id[i] for i in l0_score(goal, cands, len(cands))]


def _forge_operating_envelope(root: Path, domain, goal, signal) -> str:
    """The heuristic envelope: earned domain lessons (ranked, lifecycle-honest,
    budget-bounded) + doctrine thinking-devices + residuality stressors (only when a
    residuality contract applies). Advisory, cited by id — it informs HOW, the contract
    still decides DONE. Degrades LOUDLY to an explicit 'none on record yet' for lessons
    rather than a silent empty section (R6)."""
    divisor = _load_context_contract()[3]
    devices = ["Thinking devices (reach for one when its trigger fires):"]
    for c in _canon_doc(root, "doctrine.xml").findall("concept"):
        if c.get("state") == "active":
            devices.append(f"- **{c.get('id')}** ({c.findtext('title')}) — "
                           f"{' '.join((c.findtext('fires-when') or '').split())}")
    stressors = []
    if "residual" in (signal or "").lower():
        stressors = ["Residuality stressors (a 'yes' to any is a STOP — rework or leash):"]
        for r in _canon_doc(root, "residuality.xml").findall("gate/rule"):
            first = " ".join((r.text or "").split()).split(". ")[0]
            stressors.append(f"- **{r.get('id')}** — {first}.")
    header = ["## Operating envelope (heuristics — advisory; the contract still "
              "decides DONE)", ""]
    label = "Earned lessons" + (f" for `{domain}`" if domain else "") + ":"
    fixed_cost = _estimate_tokens(
        "\n".join(header + [label, ""] + devices + [""] + stressors), divisor)
    lessons = _envelope_lessons(root, domain, goal)
    lines = [label]
    if not lessons:
        lines.append("- none on record yet — lessons are earned from cycle hotspots"
                     + (f"; none active for `{domain}` yet." if domain else "."))
    else:
        shown = 0
        for c in lessons[:ENVELOPE_MAX_LESSONS]:
            line = f"- **{c['id']}** — {c['text']}"
            over = fixed_cost + _estimate_tokens("\n".join(lines + [line]),
                                                 divisor) > ENVELOPE_BUDGET_TOKENS
            if shown and over:  # always keep the top lesson; drop lowest-relevance first
                break
            lines.append(line)
            shown += 1
        if shown < len(lessons):
            lines.append(f"- (+{len(lessons) - shown} lower-relevance lesson(s) "
                         "trimmed to the envelope budget)")
    parts = header + lines + [""] + devices + ([""] + stressors if stressors else [])
    return "\n".join(parts).rstrip() + "\n"


def _atomic_write_locked(path: Path, data: str, lock: Path):
    """Write data to path atomically (sibling tmp + os.replace), serialized against
    other spawn writers by an exclusive flock on a shared lock file in the runs dir
    — the SAME POSIX advisory-lock idiom the run ledger uses (ledger.py). Degrades
    LOUDLY on a non-POSIX platform rather than crashing with a bare ImportError."""
    try:
        import fcntl
    except ImportError:
        sys.exit("socom spawn: the run registry requires POSIX fcntl.flock (unix "
                 "only — macOS/Linux/WSL). On native Windows, run socom under WSL.")
    lock.parent.mkdir(parents=True, exist_ok=True)
    with lock.open("a+") as lf:
        fcntl.flock(lf.fileno(), fcntl.LOCK_EX)
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_text(data)
        os.replace(tmp, path)


def cmd_spawn(args):
    seat = _opt(args, "--seat")
    promise_arg = _opt(args, "--promise")
    if not seat or not promise_arg:
        sys.exit("usage: socom spawn --seat S --promise P [--contract C] "
                 "[--exec] [--model M] [--out PATH] [--no-envelope]")
    exec_ = "--exec" in args
    no_envelope = "--no-envelope" in args
    contract_override = _opt(args, "--contract")
    model_override = _opt(args, "--model")
    out_arg = _opt(args, "--out")

    root = repo_root()
    cfg = load_cfg(root)

    # 1. resolve the seat: binding (runtime/model) from socom.yaml, role from canon.
    seats = cfg.get("seats", {}) or {}
    if seat not in seats:
        sys.exit(f"socom spawn: seat '{seat}' not bound in socom.yaml seats "
                 f"{sorted(seats)} (R6: degrade loudly).")
    binding = seats[seat] or {}
    runtime = binding.get("runtime")
    model = model_override or binding.get("model")
    role = _resolve_role(root, seat)
    if role is None:
        sys.exit(f"socom spawn: seat '{seat}' has no role in canon/roles.xml "
                 "(R6: degrade loudly).")
    if runtime not in RUNTIMES:
        sys.exit(f"socom spawn: runtime '{runtime}' for seat '{seat}' is unknown "
                 f"(bound runtimes: {sorted(RUNTIMES)}) (R6: degrade loudly).")

    # 2. read the promise: verbatim + decoded + contract goal/checks (reuse ledger).
    pf = Path(promise_arg)
    if not pf.is_absolute():
        pf = root / promise_arg
    if not pf.exists():
        sys.exit(f"socom spawn: no such promise '{promise_arg}' (R6: degrade loudly).")
    try:
        proot = ET.parse(pf).getroot()
    except (ET.ParseError, OSError) as e:
        sys.exit(f"socom spawn: {pf.name} is not readable well-formed XML — {e}")
    promise_id = proot.get("id") or pf.stem
    domain = proot.get("domain")
    verbatim = _block_text(proot.find("intent/verbatim"))
    decoded = _block_text(proot.find("intent/decoded"))
    cel = _contract_el(proot)
    goal = _block_text(cel.find("goal")) if cel is not None else ""
    checks = _contract_checks(cel) if cel is not None else []
    contract_ref = contract_override or (cel.get("ref") if cel is not None else None)

    # 3-5. render the seat envelope, forge the STABLE CORE brief, and content-address
    # the run-id off the CORE bytes ONLY (not the heuristic envelope) — so identity is
    # idempotent on intent even as the lesson corpus grows.
    seat_env = render_agent(role)
    core = _forge_brief(verbatim, decoded, seat_env, goal, checks, contract_ref)
    hash8 = hashlib.sha256(core.encode()).hexdigest()[:8]
    day = datetime.now(timezone.utc).strftime("%Y-%m%d")
    run_id = f"R-{day}-{seat}-{hash8}"
    # the heuristic envelope (default-on; --no-envelope suppresses) — earned lessons +
    # doctrine + residuality, APPENDED to the brief but NOT hashed, so it never
    # perturbs the run-id (the --no-envelope brief and the default brief share an id).
    # the residuality trigger reads the promise's MEANINGFUL intent (verbatim +
    # decoded + goal + contract ref), never the raw file — so a stray "residual"
    # in an XML comment cannot fire the stressors (reviewer MINOR, slice 3).
    signal = " ".join(x for x in (verbatim, decoded, goal, contract_ref) if x)
    op_env = "" if no_envelope else _forge_operating_envelope(
        root, domain, goal, signal)
    brief = core if not op_env else _forge_brief(
        verbatim, decoded, seat_env, goal, checks, contract_ref, op_env)

    # 6. containment: default out is .socom/runs; an --out outside the repo is refused.
    out_dir = (Path(out_arg) if out_arg else root / SOCOM_DIR / RUNS_DIR)
    if not out_dir.is_absolute():
        out_dir = root / out_dir
    out_dir = out_dir.resolve()
    if not (out_dir == root.resolve() or out_dir.is_relative_to(root.resolve())):
        sys.exit(f"socom spawn: refusing --out '{out_arg}' — resolves outside the "
                 "repo tree (containment; no partial writes).")
    brief_path = out_dir / f"{run_id}.brief.md"
    record_path = out_dir / f"{run_id}.json"
    log_path = out_dir / f"{run_id}.log"
    lock = out_dir / ".lock"
    rel_brief = brief_path.relative_to(root.resolve()) if brief_path.is_relative_to(root.resolve()) else brief_path

    record = {
        "run_id": run_id, "seat": seat, "promise": promise_id,
        "contract": contract_ref, "runtime": runtime, "model": model,
        "status": "materialized", "ts_started": _now_iso(), "pid": None,
        "brief_path": str(rel_brief), "ts_ended": None, "exit_code": None,
    }

    # 7. write the brief (atomic, locked). The record follows once status is known.
    _atomic_write_locked(brief_path, brief, lock)

    if not exec_:
        # default: materialized; print the EXACT launch command for the operator.
        _atomic_write_locked(record_path, json.dumps(record, indent=2) + "\n", lock)
        cmd = RUNTIMES[runtime]["cmd"](model, rel_brief)
        print(f"socom spawn: materialized {run_id} (seat {seat}, promise "
              f"{promise_id}) -> {rel_brief}")
        print(f"  record: {record_path.relative_to(root.resolve())}  [status=materialized]")
        print("  launch (paste to dispatch, or re-run with --exec):")
        print(f"    {cmd}")
        return

    # --exec: the bound runtime must be on PATH, else loud (no running record).
    binary = RUNTIMES[runtime]["binary"]
    if shutil.which(binary) is None:
        sys.exit(f"socom spawn --exec: runtime binary '{binary}' (for runtime "
                 f"'{runtime}') is not on PATH — cannot launch (R6: degrade loudly). "
                 f"The brief is materialized at {rel_brief}; bind/install the runtime "
                 "or run without --exec to dispatch by hand.")
    argv = RUNTIMES[runtime]["argv"](binary, model, brief)
    logf = log_path.open("w")
    proc = subprocess.Popen(argv, cwd=root, stdout=logf, stderr=subprocess.STDOUT,
                            start_new_session=True)
    record["status"] = "running"
    record["pid"] = proc.pid
    _atomic_write_locked(record_path, json.dumps(record, indent=2) + "\n", lock)
    print(f"socom spawn --exec: launched {run_id} (seat {seat}, promise "
          f"{promise_id}) as pid {proc.pid} [status=running]")
    print(f"  brief: {rel_brief}  log: {log_path.relative_to(root.resolve())}")
    print(f"  record: {record_path.relative_to(root.resolve())}")
    print("  monarch tallies + reaps this run; spawn never writes its verdict.")
