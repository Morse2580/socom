"""socom gate — gates + breach. Assembled into bin/socom by build.py."""
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
from socom.blackboard import bb_cfg, bb_live_for_session, reap_orphans
from socom.core import SOCOM_DIR, _now_iso, canonical_hash, load_cfg, log_breach, repo_root
from socom.ledger import _append_ledger_row, _promise_model, _promise_ref
from socom.monarch import reap_dead_runs, recoverable

# === BODY ===

# ── breach lifecycle (HR3: amber must close a loop) ─────────────────────

def cmd_breach(args):
    root = repo_root()
    log = root / SOCOM_DIR / "gates" / "breaches.log"
    resolved = root / SOCOM_DIR / "gates" / "breaches.resolved.log"
    lines = [ln for ln in log.read_text().splitlines() if ln.strip()] \
        if log.exists() else []
    if not args or args[0] == "list":
        for i, ln in enumerate(lines, 1):
            print(f"  {i}. {ln}")
        print(f"socom breach: {len(lines)} open")
        return
    if args[0] == "resolve":
        which = args[1] if len(args) > 1 else "all"
        note = " ".join(args[2:]) or "resolved"
        keep, done = [], []
        for i, ln in enumerate(lines, 1):
            if which == "all" or str(i) == which:
                done.append(ln)
            else:
                keep.append(ln)
        if not done:
            sys.exit(f"socom breach: nothing matched '{which}'")
        ts = _now_iso()
        with resolved.open("a") as f:
            for ln in done:
                f.write(f"{ln}\tresolved={ts}\tnote={note}\n")
        log.write_text("\n".join(keep) + ("\n" if keep else ""))
        print(f"socom breach: resolved {len(done)}, {len(keep)} remain open")
        return
    sys.exit("usage: socom breach [list|resolve <n|all> [note]]")


# ── gate ─────────────────────────────────────────────────────────────────

def run_check(cmd: str, root: Path) -> int:
    print(f"  $ {cmd}")
    return subprocess.run(cmd, shell=True, cwd=root).returncode


# Conventional Commits v1.0.0: `type[(scope)][!]: description`.
#
# The set is the spec's two mandated types plus its recommended set, plus
# `revert` (the spec's own example) and `wip`. Two things were wrong before and
# both rejected commits that ARE conventional:
#   · the scope was MANDATORY. The spec says optional, and requiring it rejected
#     zustand's own upstream HEAD (`fix: update broken README links…`).
#   · the scope charset was [a-z0-9._-], so `test(middleware/immer):` — fully
#     conventional — was rejected for containing a slash.
# Together those two took out 60 of zustand's last 100 upstream subjects.
#
# This set is deliberately NOT configurable: a knob is a capability, filed as
# SUBSTRATE-COMMIT-TYPES-CONFIGURABLE-01. The repair is to stop rejecting what
# the published standard permits.
COMMIT_TYPES = ("build", "chore", "ci", "docs", "feat", "fix", "perf",
                "refactor", "revert", "style", "test", "wip")
COMMIT_RX = re.compile(r"^(?:" + "|".join(COMMIT_TYPES) + r")(?:\([^()]+\))?!?: .+")

# Autosquash subjects: `git commit --fixup=<sha>` writes `fixup! <subject>`.
# The prefix is STRIPPED and the remainder still validated, so a real autosquash
# of a conventional commit passes while `fixup! sloppy change` is still RED.
AUTOSQUASH_RX = re.compile(r"^(?:(?:fixup|squash|amend)! )+")


def _git_authored_commit(root: Path) -> str:
    """The in-progress operation whose message GIT wrote — "merge", "revert",
    "cherry-pick" — or "" for an ordinary commit. The commit-msg hook fires on
    all of them, and blocking a merge on a subject the developer never typed is
    the same defect as the mandatory scope: the gate rejecting what the adopting
    repo legitimately produces. (Verified: `git merge --no-ff` aborted with "Not
    committing merge"; 21 of socom's own last 100 subjects are merges.)

    Read from repo STATE, never from the subject text. The first cut of this
    matched a leading 'Merge '/'Revert "' on the message, which made the ENTIRE
    commit gate bypassable by typing it — verified: the subject "Merge in my
    sloppy change with no blocks at all" committed cleanly, no type, no blocks.
    A message is what the author controls; MERGE_HEAD is what git controls, and
    only the latter can discriminate here (§complete-mediation)."""
    p = subprocess.run(["git", "rev-parse", "--git-dir"], cwd=root,
                       capture_output=True, text=True)
    if p.returncode:
        return ""
    d = Path(p.stdout.strip())
    if not d.is_absolute():
        d = root / d
    for name, label in (("MERGE_HEAD", "merge"), ("REVERT_HEAD", "revert"),
                        ("CHERRY_PICK_HEAD", "cherry-pick")):
        if (d / name).exists():
            return label
    return ""


def _gate_record(root, promise_arg, rc, duration_s):
    """Record a task-completion assessment to the run ledger: the gate just
    assessed the named promise — verdict kept iff the bound check passed. Best-
    effort — a missing / malformed / standalone arg WARNS but never blocks the
    gate (the gate's job is its check; the ledger row is the bonus that lets
    `socom cycle` measure real done-attempts). Mirrors the fail-closed posture
    of `contract verify --record` and writes through the one shared writer."""
    f = Path(promise_arg)
    if not f.is_absolute():
        f = root / promise_arg
    if not f.exists():
        print(f"socom gate task-completion: no ledger row — '{promise_arg}' "
              "not found (the gate still ran).", file=sys.stderr)
        return
    try:
        root_el = ET.parse(f).getroot()
    except (ET.ParseError, OSError) as e:
        # OSError too (e.g. a directory arg) — a bad arg must WARN, never crash
        # the gate into a false RED (the gate's check already ran).
        print(f"socom gate task-completion: no ledger row — {f.name} is not "
              f"readable well-formed XML ({e}).", file=sys.stderr)
        return
    promise_id, seat, cref = _promise_ref(root_el)
    if not promise_id or not seat:
        print(f"socom gate task-completion: no ledger row — {f.name} is not a "
              "promise with a promiser seat (a standalone contract has no "
              "executing seat to attribute).", file=sys.stderr)
        return
    row = _append_ledger_row(root, promise_id, seat, cref, {"ok": rc == 0},
                             duration_s, _promise_model(root, promise_id))
    print(f"socom gate task-completion: recorded ledger row — {seat} "
          f"{promise_id} attempt {row['attempt']} verdict {row['verdict']} "
          "(.socom/ledger/runs.jsonl).")


def cmd_gate(args):
    if not args:
        sys.exit("usage: socom gate <session-start|task-completion|pre-commit|"
                 "commit-msg|pre-push|session-end> [args]")
    name, rest = args[0], args[1:]
    root = repo_root()
    cfg = load_cfg(root)
    checks = cfg.get("checks", {})

    if name == "commit-msg":
        msg = Path(rest[0]).read_text() if rest else ""
        first = msg.splitlines()[0] if msg.splitlines() else ""
        op = _git_authored_commit(root)
        if op:
            # git wrote this message, not a person — and the [what]/[test]
            # blocks below are equally not the developer's to supply here.
            print(f"socom gate commit-msg: skipped — git authored this message "
                  f"({op} in progress).")
            return
        # Validate what an autosquash TARGETS, not the generated prefix.
        subject = AUTOSQUASH_RX.sub("", first)
        if not COMMIT_RX.match(subject):
            # Print the RULE THAT FIRED, not a paraphrase of it. The old message
            # named the format 'type(scope): description' and then echoed back a
            # subject that WAS exactly that — rejected for a reason it never
            # stated (mandatory scope, restricted charset), so three of five
            # cold-run agents had to grep the binary to learn the real rule.
            sys.exit("socom gate commit-msg: RED — the subject line is not a "
                     "Conventional Commits subject.\n"
                     f"  got:   {first!r}\n"
                     "  rule:  <type>[(scope)][!]: <description>\n"
                     f"  types: {' '.join(COMMIT_TYPES)}\n"
                     "  scope is OPTIONAL; `!` marks a breaking change; the "
                     "description must be non-empty.\n"
                     "  e.g.   fix: restore the L0 fallback\n"
                     "         test(middleware/immer): add runtime tests")
        if subject != first:
            # A real autosquash: it is squashed away before it lands, and the
            # blocks belong on the commit it targets, not on the fixup.
            return
        missing = [b for b in ("[what]", "[test]") if b not in msg]
        if missing:
            log_breach(root, "commit-msg", f"amber: missing {missing} blocks")
            print(f"socom gate commit-msg: AMBER — missing {missing}; logged. "
                  "Full blocks belong on the first branch commit.")
            return
        # HR4: substance heuristic — evidence should look like evidence
        # (a command, an exit code, an output line), not a vibe. Anchor the
        # block token to line-start so a prose mention of "[test]" inside an
        # earlier block can't capture a digit-less fragment (false negative).
        m = re.search(r"^\[test\](.*?)(?:\n\[|\Z)", msg, re.DOTALL | re.M)
        body = (m.group(1) if m else "").strip()
        looks_like_evidence = (len(body) >= 20 and
                               re.search(r"(\$ |rc=|exit|PASS|FAIL|\d)", body))
        if not looks_like_evidence:
            log_breach(root, "commit-msg", "amber: [test] block has no "
                                           "evidence-shaped content")
            print("socom gate commit-msg: AMBER — [test] reads like a claim, "
                  "not evidence (no command/exit-code/output). Logged; CI replays.")
        return

    if name == "session-start":
        h = canonical_hash(root)
        claude = root / "CLAUDE.md"
        if claude.exists():
            m = re.search(r"source=(\w+)", claude.read_text())
            if m and m.group(1) != h:
                print(f"socom: P0 DRIFT — compiled views stale ({m.group(1)} != {h}); "
                      "run `socom compile`", file=sys.stderr)
                sys.exit(2)
        for ln in reap_orphans(root):  # R12: reap, don't just report
            print(f"  {ln}")
        # close the orchestration loop beside the claim reaper: a worker spawned
        # with --exec that died (or completed) without a verdict is reaped here
        # every session, so dead runs never linger.
        for ln in reap_dead_runs(root):
            print(f"  {ln}")
        # surface the recovery debt WITHOUT acting on it: recover is a deliberate
        # act, never auto-run every session (auto-relaunching is too aggressive).
        # A read-only pointer so the debt is visible; `monarch recover` re-dispatches.
        elig, _aband = recoverable(root)
        if elig:
            print(f"  {len(elig)} promise(s) eligible for `socom monarch recover` "
                  "(dead + unkept, under the attempt cap) — recovery is deliberate, "
                  "not run here.")
        wt = subprocess.run(["git", "worktree", "list"], cwd=root,
                            capture_output=True, text=True).stdout
        # HR3: amber closes a loop — every session opens by seeing its debt.
        # Entries carry gate + detail, never author identity (telemetry about
        # the system, not surveillance of people).
        blog = root / SOCOM_DIR / "gates" / "breaches.log"
        if blog.exists():
            lines = [ln for ln in blog.read_text().splitlines() if ln.strip()]
            if lines:
                print(f"socom session-start: {len(lines)} amber breach(es) on "
                      f"record — oldest {lines[0].split(chr(9))[0]}; last 3:")
                for ln in lines[-3:]:
                    print(f"    {ln}")
                print("  review or resolve before new work piles on top.")
        print(f"socom session-start: source={h} ok; worktrees:\n{wt.strip()}")
        return

    if name == "session-end":
        handoffs = sorted((root / SOCOM_DIR / "handoffs").glob("*.xml"))
        today = datetime.now(timezone.utc).date().isoformat()
        fresh = [f for f in handoffs if today in f.name]
        if not fresh:
            sys.exit("socom gate session-end: RED — no handoff written today "
                     "(.socom/handoffs/H-<date>*.xml). A session may not vanish.")
        if "FILL" in fresh[-1].read_text():
            sys.exit(f"socom gate session-end: RED — {fresh[-1].name} still has "
                     "unfilled FILL fields. A handoff of placeholders is a "
                     "vanishing session with paperwork.")
        prompt = root / SOCOM_DIR / "prompts" / "next-session.md"
        if not prompt.exists() or \
                prompt.stat().st_mtime < fresh[-1].stat().st_mtime:
            sys.exit("socom gate session-end: RED — next-session prompt missing "
                     "or older than the handoff. Run `socom prompt`.")
        # Local read only (sync=False): session-end must not block on a network
        # fetch, and the question — "did THIS session leave a lease open?" — is
        # answerable from our own shard alone.
        held = bb_live_for_session(root, bb_cfg(load_cfg(root)), sync=False)
        if held:
            open_paths = [p for l in held for p in l.get("paths", [])]
            print(f"socom session-end: AMBER — paths still claimed: "
                  f"{open_paths} (the TTL will expire them, but release is the intent)")
            log_breach(root, "session-end", f"amber: unreleased leases {open_paths}")
        print(f"socom session-end: PASS — handoff {fresh[-1].name} filled, "
              "prompt generated + claim-verified. Distill memories (cap 2, "
              "five gates) before you go.")
        return

    # Built-ins are handled above; every other gate id resolves to its own
    # bound check (checks.<id>) — so canon can add gates like `eval` that bind
    # to a repo check without new dispatch code.
    builtins = ("task-completion", "pre-commit", "pre-push")
    tier = {"task-completion": "fast", "pre-commit": "medium",
            "pre-push": "full"}.get(name, name)
    cmd = checks.get(tier)
    if cmd is None and name not in builtins:
        sys.exit(f"socom: unknown gate '{name}' (no built-in handler and no "
                 f"checks.{name} binding in socom.yaml)")
    if not cmd or cmd == "true":
        print(f"socom gate {name}: checks.{tier} unbound — passing (bind it in socom.yaml)")
        return
    import time
    _t0 = time.monotonic()
    rc = run_check(cmd, root)
    duration_s = int(time.monotonic() - _t0)
    # task-completion, given a promise, records its assessment to the run ledger
    # — the canonical "a gate assessed the promise -> kept/broken" event
    # (schemas/ledger.xml), so `socom cycle` measures real done-attempts WITHOUT
    # a manual flag. Recorded BEFORE the RED exit: a broken attempt is the
    # pass@1-vs-pass@k signal, not noise. No promise arg -> behaviour unchanged.
    if name == "task-completion" and rest:
        _gate_record(root, rest[0], rc, duration_s)
    if rc != 0:
        if name == "pre-commit":  # amber band
            log_breach(root, name, f"checks.medium failed rc={rc}")
            print(f"socom gate {name}: AMBER — failed (rc={rc}); breach logged, "
                  "commit proceeds, CI re-asserts at red.")
            return
        sys.exit(f"socom gate {name}: RED — checks.{tier} failed (rc={rc})")
    print(f"socom gate {name}: PASS")
