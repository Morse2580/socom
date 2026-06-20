"""socom lesson — lesson lifecycle + introspect. Assembled into bin/socom by build.py."""
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
from socom.core import SOCOM_DIR, repo_root

# === BODY ===

# ── lesson — experience earned into durable, retrievable rules ────────────
# Ported from Akili's lesson system. A lesson is BORN provisional from a cycle
# hotspot (the eval->lesson bridge), EARNS active by re-confirmation, and is
# RETIRED (never deleted) when falsified. Lives at .socom/lessons/<id>.xml so
# `socom index` retrieves it for free; the lifecycle filter hides retired.
def _lesson_files(root):
    d = root / SOCOM_DIR / "lessons"
    return sorted(d.glob("L-*.xml")) if d.exists() else []


def _lesson_attr(text, name):
    m = re.search(rf'\b{name}="([^"]*)"', text)
    return m.group(1) if m else ""


def _lesson_statement(text):
    m = re.search(r"<statement[^>]*>(.*?)</statement>", text, re.DOTALL)
    return " ".join(m.group(1).split())[:80] if m else ""


def _lesson_template(lid, domain, promise, cycle, broken, total):
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- socom lesson — provisional candidate born from a cycle hotspot. Refine the
     statement and why into the specific guard, then promote it once
     re-confirmed (socom lesson promote {lid}), or retire it with a reason if
     falsified. The body is never deleted; retirement flips state, adds a tag. -->
<lesson id="{lid}" domain="{domain}" state="provisional" source="cycle"
        lifecycle="mid-session">
  <statement embed="true">
    Promise {promise} keeps failing assessment ({broken}/{total} broken) —
    encode the guard that prevents this recurring failure before reworking it.
  </statement>
  <why embed="true">
    Born from cycle {cycle}: repeated `broken` verdicts on {promise} signal a
    failure class, not a one-off. Refine this into the specific guard, then
    promote so it surfaces as domain guidance.
  </why>
  <derived-from promise="{promise}" cycle="{cycle}" broken="{broken}" total="{total}"/>
  <evidence embed="true">
    cycle hotspot: {promise} broken {broken}/{total}.
  </evidence>
  <validated count="0"/>
</lesson>
"""


def _regen_lessons_index(root):
    by_domain = {}
    for f in _lesson_files(root):
        t = f.read_text()
        by_domain.setdefault(_lesson_attr(t, "domain") or "general", []).append(
            (f.stem, _lesson_attr(t, "state")))
    lines = ["# Lessons Index", "",
             "Domain-sharded; load the file(s) matching the task. Entries are "
             "provisional until re-confirmed, then active; falsified entries are "
             "state=retired (preserved, never deleted).", "",
             "| Domain | Lessons | Active | Provisional |", "|---|---|---|---|"]
    for dom in sorted(by_domain):
        ls = by_domain[dom]
        act = sum(1 for _, s in ls if s == "active")
        prov = sum(1 for _, s in ls if s == "provisional")
        lines.append(f"| {dom} | {', '.join(i for i, _ in ls)} | {act} | {prov} |")
    (root / SOCOM_DIR / "lessons" / "index.md").write_text("\n".join(lines) + "\n")


def cmd_lesson(args):
    import json
    root = repo_root()
    if not args:
        sys.exit("usage: socom lesson <candidates|list|promote|retire> [args]")
    sub, rest = args[0], args[1:]

    def flag_val(name, default=None):
        return rest[rest.index(name) + 1] if name in rest \
            and rest.index(name) + 1 < len(rest) else default

    ldir = root / SOCOM_DIR / "lessons"
    ldir.mkdir(parents=True, exist_ok=True)

    if sub == "candidates":
        domain = flag_val("--domain", "general")
        min_broken = int(flag_val("--min-broken", "2"))
        cdir = root / SOCOM_DIR / "cycles"
        cycles = sorted(cdir.glob("cycle-*.json")) if cdir.exists() else []
        if not cycles:
            sys.exit("socom lesson candidates: no cycle artifact — run "
                     "`socom cycle` first (the bridge consumes its hotspots).")
        cyc = cycles[-1]
        hotspots = json.loads(cyc.read_text()).get("hotspots", [])
        existing = {_lesson_attr(f.read_text(), "promise")
                    for f in _lesson_files(root)}
        born = 0
        for h in hotspots:
            promise = h.get("promise")
            if h.get("broken", 0) < min_broken or promise in existing:
                continue  # below threshold, or idempotent: one per source promise
            lid = f"L-{promise}"
            (ldir / f"{lid}.xml").write_text(_lesson_template(
                lid, domain, promise, cyc.name, h.get("broken", 0),
                h.get("total", 0)))
            existing.add(promise)
            born += 1
            print(f"  + {lid} (provisional) <- hotspot {promise} "
                  f"broken {h.get('broken')}/{h.get('total')}")
        _regen_lessons_index(root)
        print(f"socom lesson: {born} candidate(s) born from {cyc.name}; "
              f"{len(hotspots)} hotspot(s) seen. Refine, then "
              f"`socom lesson promote <id>`.")
        return

    if sub == "list":
        dom_f, state_f = flag_val("--domain"), flag_val("--state")
        rows = []
        for f in _lesson_files(root):
            t = f.read_text()
            d, s = _lesson_attr(t, "domain"), _lesson_attr(t, "state")
            if (dom_f and d != dom_f) or (state_f and s != state_f):
                continue
            rows.append((f.stem, d, s, _lesson_statement(t)))
        for lid, d, s, stmt in rows:
            print(f"  {s:<11} [{d}] {lid}: {stmt}")
        suffix = (f" domain={dom_f}" if dom_f else "") + \
                 (f" state={state_f}" if state_f else "")
        print(f"socom lesson: {len(rows)} lesson(s){suffix}")
        return

    if sub in ("promote", "retire"):
        if not rest:
            sys.exit(f"usage: socom lesson {sub} <id>"
                     + (' --reason "..."' if sub == "retire" else ""))
        lid = rest[0]
        f = ldir / f"{lid}.xml"
        if not f.exists():
            sys.exit(f"socom lesson {sub}: no such lesson {lid}")
        t = f.read_text()
        cur = _lesson_attr(t, "state")
        if sub == "promote":
            if cur != "provisional":
                sys.exit(f"socom lesson promote: {lid} is '{cur}'; only "
                         "provisional lessons promote")
            f.write_text(re.sub(r'state="provisional"', 'state="active"',
                                t, count=1))
            _regen_lessons_index(root)
            print(f"socom lesson: {lid} provisional -> active")
            return
        if cur == "retired":
            sys.exit(f"socom lesson retire: {lid} already retired")
        reason = flag_val("--reason", "falsified")
        date = datetime.now(timezone.utc).date().isoformat()
        t = re.sub(rf'state="{cur}"', 'state="retired"', t, count=1)
        t = t.replace("</lesson>",
                      f'  <retire reason="{reason}" date="{date}"/>\n</lesson>')
        f.write_text(t)
        _regen_lessons_index(root)
        print(f"socom lesson: {lid} {cur} -> retired (preserved; reason: {reason})")
        return

    sys.exit(f"socom lesson: unknown subcommand '{sub}'")


# ── introspect (backlog #4: agent introspection, increment 1) ────────────
# Post-session self-capture: parse machine-verifiable assertions from a
# closing handoff's <evidence> commands into a replayable append-only log
# (schemas/assertion.xml), and birth provisional lesson candidates from
# CAPTURED failures. Deterministic — the only one of Akili's five extractors
# with no model in the loop (the rest deferred to preserve the L0 floor).
# Outcome-conditional and non-blocking: capture never fails a closeout.

def _assertion_lesson_template(lid, domain, aid, handoff, verify, expect_exit):
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- socom lesson — provisional candidate born from a captured failure assertion
     ({aid}). A command in {handoff}'s evidence exited unexpectedly (expected
     {expect_exit}) with no explanatory note. Refine this into the specific guard,
     then promote once re-confirmed (socom lesson promote {lid}), or retire with a
     reason if it was a one-off. Provisional by design: a single occurrence earns
     active only by re-confirmation. The body is never deleted. -->
<lesson id="{lid}" domain="{domain}" state="provisional" source="introspect"
        lifecycle="mid-session">
  <statement embed="true">
    `{verify}` failed unexpectedly (expected exit {expect_exit}) at closeout —
    encode the guard that makes this command's failure mode impossible, or
    explain it as a deliberate check (then annotate it in the handoff).
  </statement>
  <why embed="true">
    Born from assertion {aid} ({handoff}): an un-noted non-expected exit captured
    in the session evidence signals a failure worth a guard, not a passing check.
    Refine into the specific guard, then promote so it surfaces as guidance.
  </why>
  <derived-from assertion="{aid}" handoff="{handoff}"/>
  <evidence embed="true">
    assertion {aid}: `{verify}` expected exit {expect_exit}.
  </evidence>
  <validated count="0"/>
</lesson>
"""


def cmd_introspect(args):
    import json
    import xml.etree.ElementTree as ET
    root = repo_root()
    pos = [a for a in args if not a.startswith("-")]
    domain = args[args.index("--domain") + 1] if "--domain" in args \
        and args.index("--domain") + 1 < len(args) else "general"

    # Resolve the handoff: explicit path/name, else the latest H-*.xml.
    hdir = root / SOCOM_DIR / "handoffs"
    if pos:
        cand = Path(pos[0])
        handoff = cand if cand.exists() else hdir / pos[0]
        if not handoff.exists():
            sys.exit(f"socom introspect: no such handoff '{pos[0]}' "
                     f"(looked at it directly and under .socom/handoffs/).")
    else:
        hs = sorted(hdir.glob("H-*.xml")) if hdir.exists() else []
        if not hs:
            sys.exit("socom introspect: no handoff — .socom/handoffs/H-*.xml "
                     "absent. Nothing closed to introspect (R6: degrade loudly). "
                     "Pass a handoff path, or write one with `socom handoff`.")
        handoff = hs[-1]

    # Parse — a malformed handoff WARNS and exits 0 (capture never blocks closeout).
    try:
        tree = ET.parse(handoff)
    except ET.ParseError as e:
        print(f"socom introspect: WARN — {handoff.name} is not well-formed XML "
              f"({e}); nothing captured. (capture never blocks closeout)")
        return
    hroot = tree.getroot()
    hid = hroot.get("id") or handoff.stem
    hts = hroot.get("date") or ""

    ev = hroot.find("evidence")
    commands = list(ev.findall("command")) if ev is not None else []
    if not commands:
        print(f"socom introspect: {handoff.name} has no <evidence> commands — "
              "no assertions to capture.")
        return

    # Idempotency: load existing assertion ids; one row per (handoff, index).
    adir = root / SOCOM_DIR / "assertions"
    adir.mkdir(parents=True, exist_ok=True)
    log = adir / "log.jsonl"
    seen = set()
    if log.exists():
        for ln in log.read_text().splitlines():
            ln = ln.strip()
            if ln:
                try:
                    seen.add(json.loads(ln)["id"])
                except (ValueError, KeyError):
                    continue

    ldir = root / SOCOM_DIR / "lessons"
    existing_lessons = {_lesson_attr(f.read_text(), "id") for f in _lesson_files(root)}

    rows, born = [], 0
    for i, c in enumerate(commands):
        aid = f"A-{hid}-{i}"
        if aid in seen:
            continue
        verify = " ".join((c.text or "").split())
        try:
            expect_exit = int(c.get("exit", "0"))
        except ValueError:
            expect_exit = 0
        note = c.get("note", "")
        category = c.get("category", "general")
        row = {"id": aid, "ts": hts, "source_handoff": hid, "verify": verify,
               "expect_exit": expect_exit, "category": category}
        if note:
            row["note"] = note
        rows.append(row)

        # Bridge: an un-noted unexpected failure births a provisional lesson.
        if expect_exit != 0 and not note:
            lid = f"L-{aid}"
            if lid not in existing_lessons:
                ldir.mkdir(parents=True, exist_ok=True)
                (ldir / f"{lid}.xml").write_text(_assertion_lesson_template(
                    lid, domain, aid, hid, verify, expect_exit))
                existing_lessons.add(lid)
                born += 1
                print(f"  + {lid} (provisional) <- captured failure {aid}: "
                      f"`{verify[:48]}`")

    if rows:
        with log.open("a") as fh:
            for r in rows:
                fh.write(json.dumps(r) + "\n")
        if born:
            _regen_lessons_index(root)

    print(f"socom introspect: {handoff.name} -> {len(rows)} new assertion(s) "
          f"({len(commands)} command(s) seen, {len(commands) - len(rows)} already "
          f"logged); {born} lesson candidate(s) born. Replay log: "
          f".socom/assertions/log.jsonl")
