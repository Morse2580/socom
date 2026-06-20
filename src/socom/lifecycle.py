"""socom lifecycle — compile / adopt / doctor / precond / greet / statusline. Assembled into bin/socom by build.py."""
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
from socom.claims import claim_expired, claim_holder
from socom.core import CANON_FILES, HOOKS_DIR, SOCOM_DIR, SOCOM_VERSION, canonical_hash, load_cfg, md_text, parse_canon, repo_root, resource, write_generated

# === BODY ===

# The substrate dirs every repo needs under .socom/ — single source of truth,
# shared by init (plants them) and precond (heals them).
SUBSTRATE_DIRS = ["memory/memories", "lessons", "handoffs", "prompts",
                  "promises", "gates"]


# ── init ─────────────────────────────────────────────────────────────────

def cmd_init(args):
    root = repo_root(Path(args[0]) if args else None)
    socom_dir = root / SOCOM_DIR
    (socom_dir / "canon").mkdir(parents=True, exist_ok=True)
    for sub in SUBSTRATE_DIRS:
        (socom_dir / sub).mkdir(parents=True, exist_ok=True)

    for name in CANON_FILES:
        dst = socom_dir / "canon" / name
        if not dst.exists():
            dst.write_text(resource("canon/" + name))
            print(f"  planted {dst}")

    idx = socom_dir / "memory" / "INDEX.md"
    if not idx.exists():
        idx.write_text(
            "# Memory Index — lifecycle-organized retrieval map\n\n"
            "Load the section matching your current phase. One line per memory:\n"
            "`- [title](memories/file.md) — when it fires`\n\n"
            "## Session start\n\n## Mid-session\n\n## Closeout\n\n## Always-on\n")
        print(f"  planted {idx}")

    lessons_idx = socom_dir / "lessons" / "index.md"
    if not lessons_idx.exists():
        lessons_idx.write_text(
            "# Lessons Index\n\nDomain-sharded; load the file(s) matching the task. "
            "Entries are provisional until re-confirmed, then active; falsified "
            "entries move to _retired.md (preserved, never deleted).\n\n"
            "| Domain | File | Active | Provisional |\n|---|---|---|---|\n")
        print(f"  planted {lessons_idx}")

    cfg = root / "socom.yaml"
    if not cfg.exists():
        cfg.write_text(textwrap.dedent(f"""\
            socom: "{SOCOM_VERSION}"
            project: {root.name}
            domains: [core]          # claim + lesson granularity
            checks:                  # bind to commands that really run here
              fast: "true"           # seconds-budget; runs at task-completion
              medium: "true"         # pre-commit (amber band)
              full: "true"           # pre-push + CI (red band)
            ci:
              status: "echo 'bind me: cache-free pipeline state query'"
            seats:
              builder:  {{ runtime: claude-code, model: default }}
              reviewer: {{ runtime: claude-code, model: different-family-preferred }}
            """))
        print(f"  planted {cfg} — EDIT THE BINDINGS, then run `socom compile`")
    cmd_greet([str(root)])


# ── compile ──────────────────────────────────────────────────────────────

def render_body(root: Path, cfg: dict) -> str:
    constitution = parse_canon(root, "constitution.xml")
    roles = parse_canon(root, "roles.xml")
    gates = parse_canon(root, "gates.xml")
    session = parse_canon(root, "session.xml")

    out = [f"# {cfg.get('project', root.name)} — SOCOM substrate\n"]
    out.append(
        "Protocol over participants: the rules below bind every participant — "
        "agent or human. Canonical source: `.socom/` + `socom.yaml`.\n")

    out.append("## Constitution (Non-Negotiable)\n")
    for p in sorted(constitution.findall("principle"), key=lambda e: int(e.get("rank", 99))):
        out.append(f"### {p.get('rank')}. {p.findtext('title')}\n")
        out.append(md_text(p) + "\n")

    out.append("## Session protocol\n")
    for ph in sorted(session.findall("phase"), key=lambda e: int(e.get("order", 9))):
        out.append(f"### {ph.get('id').capitalize()}\n")
        out.append(md_text(ph) + "\n")

    doctrine_f = root / SOCOM_DIR / "canon" / "doctrine.xml"
    if doctrine_f.exists():
        doctrine = ET.parse(doctrine_f).getroot()
        out.append("## Doctrine — named thinking devices (teaching layer)\n")
        out.append("Reach for the concept when its trigger fires; full text in "
                   "`.socom/canon/doctrine.xml` (and via retrieval).\n")
        out.append("| Concept | Fires when | Essence |\n|---|---|---|")
        for c in doctrine.findall("concept"):
            if c.get("state") != "active":
                continue
            fires = (c.findtext("fires-when") or "").strip()
            essence = md_text(c).split(". ")[0].replace("\n", " ") + "."
            out.append(f"| **{c.findtext('title')}** | {fires} | {essence} |")
        out.append("")

    out.append("## Seats (open registry — any model, runtime, or human)\n")
    out.append("| Seat | State | Promise |\n|---|---|---|")
    for r in roles.findall("role"):
        desc = (r.findtext("description") or "").strip()
        out.append(f"| **{r.get('id')}** | {r.get('state')} | {desc} |")
    out.append("\nFull seat envelopes: `.socom/canon/roles.xml` "
               "(compiled agents in `.claude/agents/`). Builder and reviewer "
               "never share context. Briefs open with the user's words verbatim.\n")

    out.append("## Gates\n")
    out.append("| Gate | Trigger | Tier | Band | Blocks |\n|---|---|---|---|---|")
    for g in gates.findall("gate"):
        out.append(f"| {g.get('id')} | {g.get('trigger')} | {g.get('tier')} "
                   f"| {g.get('band')} | {g.findtext('blocks')} |")
    out.append("\nLocal bypass is permitted for flow; CI re-asserts every gate. "
               "Run a gate: `socom gate <id>`.\n")

    forge_f = root / SOCOM_DIR / "canon" / "forge.xml"
    if forge_f.exists():
        forge = ET.parse(forge_f).getroot()
        fb = cfg.get("forge", {}) or {}
        out.append("## Forge — git-provider operations (universal verbs, "
                   "repo-bound commands)\n")
        out.append("Run `socom forge <verb>` — NEVER improvise provider "
                   "mechanics (auth, polling, MR calls) inline.\n")
        for r in forge.findall("rules/rule"):
            out.append(f"- **{r.get('id')}** — " +
                       " ".join((r.text or "").split()))
        out.append("\n| Verb | Intent | This repo |\n|---|---|---|")
        for v in forge.findall("verb"):
            vid = v.get("id")
            intent = (v.findtext("intent") or "").strip()
            b = fb.get(vid)
            out.append(f"| `{vid}` | {intent} | "
                       + (f"`{b}`" if b else "*unbound*") + " |")
        out.append("")

    resid_f = root / SOCOM_DIR / "canon" / "residuality.xml"
    if resid_f.exists():
        resid = ET.parse(resid_f).getroot()
        out.append("## Residuality — the falsifiable gate (constitution "
                   "§residuality-gate)\n")
        out.append("Run before any fix or hard-to-reverse decision. A \"yes\" to "
                   "any gate question is a STOP — rework or leash it.\n")
        for r in resid.findall("gate/rule"):
            out.append(f"- **{r.get('id')}** — " +
                       " ".join((r.text or "").split()))
        out.append("\nFalsifiable checklist — Saltzer & Schroeder (1975) principles, "
                   "each a test a design can be failed against:\n")
        for p in resid.findall("principles/principle"):
            out.append(f"- **{p.get('id')}** — " +
                       " ".join((p.text or "").split()))
        out.append("")

    cp_f = root / SOCOM_DIR / "canon" / "commit-protocol.xml"
    if cp_f.exists():
        cp = ET.parse(cp_f).getroot()
        out.append("## Commit protocol (constitution §structured-commits)\n")
        out.append("Every commit is institutional memory — the next session reads "
                   "the log alone and recovers the journey. The six blocks and what "
                   "each carries; full text in `.socom/canon/commit-protocol.xml`.\n")
        out.append("| Block | Carries |\n|---|---|")
        for b in cp.findall("blocks/block"):
            essence = " ".join((b.text or "").split()).split(". ")[0] + "."
            # strip the leading "[id] — " label the rule text repeats; the
            # Block column already carries it (reviewer nit, #7).
            essence = re.sub(r"^\[%s\]\s*—\s*" % b.get("id"), "", essence)
            out.append(f"| `[{b.get('id')}]` | {essence} |")
        out.append("\nThe discipline (Akili-ported teaching layer):\n")
        for r in cp.findall("discipline/rule"):
            out.append(f"- **{r.get('id')}** — " +
                       " ".join((r.text or "").split()))
        out.append("")

    out.append("## Repo bindings (socom.yaml)\n")
    checks = cfg.get("checks", {})
    out.append("| Check | Command |\n|---|---|")
    for k in ("fast", "medium", "full"):
        out.append(f"| {k} | `{checks.get(k, 'UNBOUND')}` |")
    out.append(f"| ci.status | `{cfg.get('ci', {}).get('status', 'UNBOUND')}` |")
    out.append(f"\nDomains: {', '.join(cfg.get('domains', []))}\n")

    out.append("## Retrieval map\n")
    out.append(
        "- Entering a phase? Load that section of `.socom/memory/INDEX.md` "
        "(session-start / mid-session / closeout / always-on).\n"
        "- Working a domain? Load its file via `.socom/lessons/index.md`.\n"
        "- Associative recall: `socom index` emits chunks for any vector store; "
        "the substrate never depends on it (L0 floor: this file + grep).\n")
    return "\n".join(out)


def render_agent(role) -> str:
    rid = role.get("id")
    desc = (role.findtext("description") or "").strip()
    lines = ["---", f"name: {rid}", f"description: {desc}", "---", "",
             f"You occupy the **{rid}** seat of this repo's SOCOM substrate. "
             "Your authority and limits come from the seat, not the model.", "",
             "## You promise"]
    lines += [f"- {p.text.strip()}" for p in role.findall("promises/promise")]
    ops = role.find("operations")
    if ops is not None:
        lines += ["", f"**Reads:** {ops.get('reads')}", f"**Writes:** {ops.get('writes')}"]
    lines += ["", "## You never"]
    lines += [f"- {r.text.strip()}" for r in role.findall("never/rule")]
    lines += ["", "Constitution and gates: see CLAUDE.md. Verify, never claim: "
              "evidence is replayable commands + exit codes, recorded in your result."]
    return "\n".join(lines) + "\n"


# HR1: hooks resolve the tool (PATH -> local git config -> $SOCOM_HOME) and
# degrade gracefully when absent — the substrate must never be why a fresh
# clone can't commit. CI re-asserts every gate (R1), so graceful local absence
# loses nothing. The committed hook carries NO machine-specific absolute path:
# the builder-machine fallback lives in local git config (socom.binpath, set by
# `adopt`/_wire_hooks, never committed), so a teammate's clone never inherits
# this machine's filesystem (constitution §open-design, §least-common-mechanism).
HOOK_RESOLVER = '''SOCOM="$(command -v socom 2>/dev/null)"
[ -x "$SOCOM" ] || SOCOM="$(git config socom.binpath 2>/dev/null)"
[ -x "$SOCOM" ] || { [ -n "$SOCOM_HOME" ] && SOCOM="$SOCOM_HOME/bin/socom"; }
if [ -z "$SOCOM" ] || [ ! -x "$SOCOM" ]; then
  echo "socom: tool not found — gate skipped locally, CI re-asserts. (run \\`socom adopt\\` here, or export SOCOM_HOME=<socom checkout>)" >&2
  exit 0
fi
'''


HOOK_TEMPLATES = {
    "pre-commit": 'exec "$SOCOM" gate pre-commit',
    "commit-msg": 'exec "$SOCOM" gate commit-msg "$1"',
    "pre-push": 'exec "$SOCOM" gate pre-push',
}


def cmd_compile(args):
    force = "--force" in args
    args = [a for a in args if a != "--force"]
    root = repo_root(Path(args[0]) if args else None)
    cfg = load_cfg(root)
    h = canonical_hash(root)
    body = render_body(root, cfg)

    write_generated(root / "CLAUDE.md", body, h, force=force)
    write_generated(root / "AGENTS.md", body, h, force=force)
    write_generated(root / ".cursor" / "rules" / "socom.mdc",
                    "---\nalwaysApply: true\n---\n" + body, h, force=force)

    roles = parse_canon(root, "roles.xml")
    for r in roles.findall("role"):
        if r.get("state") == "active":
            write_generated(root / ".claude" / "agents" / f"{r.get('id')}.md",
                            render_agent(r), h, force=force)

    hooks_dir = root / HOOKS_DIR
    for name, cmd in HOOK_TEMPLATES.items():
        script = (f"#!/bin/sh\n# socom:generated source={h}\n"
                  f"{HOOK_RESOLVER}{cmd}\n")
        p = hooks_dir / name
        if p.exists() and "socom:generated" not in p.read_text()[:200] and not force:
            print(f"  REFUSED {p}: existing non-socom hook (use --force)", file=sys.stderr)
            continue
        p.parent.mkdir(exist_ok=True)
        p.write_text(script)
        p.chmod(0o755)
        print(f"  wrote {p}")

    # CI adapters — the R1 floor as GitOps, generated for EVERY provider so
    # the repo delivers its enforcement to whichever remote it lands on.
    full = cfg.get("checks", {}).get("full", "true")
    extra = (cfg.get("ci") or {}).get("extra")
    gh_steps = [
        "      - uses: actions/checkout@v4",
        "      - uses: actions/setup-python@v5",
        "        with: { python-version: '3.12' }",
        "      - run: pip install pyyaml",
        "      - name: re-assert checks.full (socom gate, R1)",
        f"        run: {full}",
    ]
    if extra:
        gh_steps += ["      - name: extra CI checks (ci.extra)",
                     f"        run: {extra}"]
    write_generated(root / ".github" / "workflows" / "socom-gates.yml",
                    "name: socom-gates\n"
                    "on: [push, pull_request, workflow_dispatch]\n"
                    "jobs:\n  gates:\n    runs-on: ubuntu-latest\n    steps:\n"
                    + "\n".join(gh_steps) + "\n",
                    h, comment=("#", ""), force=force)
    gl = ["socom-gates:", "  image: python:3.12",
          "  rules:", "    - if: $CI_PIPELINE_SOURCE == 'push' || $CI_PIPELINE_SOURCE == 'merge_request_event'",
          "  script:", "    - pip install pyyaml", f"    - {full}"]
    if extra:
        gl.append(f"    - {extra}")
    write_generated(root / ".gitlab-ci.yml", "\n".join(gl) + "\n",
                    h, comment=("#", ""), force=force)
    ado = ["# include as a job in azure-pipelines.yml (or run standalone)",
           "jobs:", "  - job: socom_gates", "    pool: { vmImage: ubuntu-latest }",
           "    steps:",
           "      - task: UsePythonVersion@0",
           "        inputs: { versionSpec: '3.12' }",
           "      - script: pip install pyyaml && " + full,
           "        displayName: re-assert checks.full (socom gate, R1)"]
    if extra:
        ado += ["      - script: " + extra,
                "        displayName: extra CI checks (ci.extra)"]
    write_generated(root / SOCOM_DIR / "ci" / "azure-socom-gates.yml",
                    "\n".join(ado) + "\n", h, comment=("#", ""), force=force)

    # .claude/settings.json — NON-CLOBBERING MERGE: socom only ADDS keys that are
    # absent (the SessionStart gate hook and the statusLine), and never overwrites
    # a hand-set statusLine or existing hooks. So `adopt` offers its statusline +
    # gate without ever stomping a user's own config (e.g. another tool's
    # statusLine). Invalid JSON is left untouched (don't corrupt; §fail-safe).
    settings = root / ".claude" / "settings.json"
    import json
    # The SessionStart hook resolves socom through the SAME resolver the git hooks
    # use (HOOK_RESOLVER) — never a machine-specific absolute path (§open-design).
    sess_cmd = f'{HOOK_RESOLVER}exec "$SOCOM" gate session-start'
    existing = {}
    if settings.exists():
        try:
            existing = json.loads(settings.read_text())
        except Exception:
            print(f"  SKIP {settings} — not valid JSON, left untouched")
            existing = None
    if existing is not None:
        notes = []
        if "statusLine" not in existing:
            existing["statusLine"] = {"type": "command", "command": "socom statusline"}
            notes.append("statusLine -> `socom statusline`")
        else:
            notes.append("kept your statusLine")
        hooks = existing.setdefault("hooks", {})
        if "SessionStart" not in hooks:
            hooks["SessionStart"] = [{"matcher": "*", "hooks": [
                {"type": "command", "command": sess_cmd, "timeout": 30}]}]
            notes.append("SessionStart gate")
        settings.parent.mkdir(parents=True, exist_ok=True)
        settings.write_text(json.dumps(existing, indent=2) + "\n")
        print(f"  .claude/settings.json: {', '.join(notes)}")

    print(f"socom: compiled (source={h}). Activate git hooks: "
          f"git config core.hooksPath {HOOKS_DIR}  (or `socom adopt` does it for you)")


# ── git-hooks wiring (single source: doctor-heal and adopt route through here) ──

def _git_hooks_path(root: Path) -> str:
    """Current core.hooksPath for the repo ('' if unset or not a git repo)."""
    return subprocess.run(["git", "config", "core.hooksPath"], cwd=root,
                          capture_output=True, text=True).stdout.strip()


def _wire_hooks(root: Path) -> bool:
    """Set core.hooksPath to HOOKS_DIR (idempotent). Returns True if the repo is
    now wired, False if it could not be (not a git repo). The single WRITER for
    the hooks-wiring truth — both doctor-heal and `adopt` route through here, so
    'where the hooks live' lives in exactly one place (§least-common-mechanism).
    Fails soft: a non-git dir returns False rather than raising (CI re-asserts)."""
    if _git_hooks_path(root) == HOOKS_DIR:
        return True
    subprocess.run(["git", "config", "core.hooksPath", HOOKS_DIR],
                   cwd=root, capture_output=True)
    # Record THIS machine's socom location in LOCAL git config (never committed)
    # so the portable committed hook can resolve the tool without a PATH install
    # — replaces the old absolute path baked into the shared hook (HR1).
    subprocess.run(["git", "config", "socom.binpath",
                    str(Path(__file__).resolve())],
                   cwd=root, capture_output=True)
    return _git_hooks_path(root) == HOOKS_DIR


# ── doctor ───────────────────────────────────────────────────────────────

def cmd_doctor(args):
    root = repo_root(Path(args[0]) if args else None)
    cfg = load_cfg(root)
    h = canonical_hash(root)
    problems = []

    for rel in ["CLAUDE.md", "AGENTS.md", ".cursor/rules/socom.mdc"]:
        f = root / rel
        if not f.exists():
            problems.append(f"missing compiled view: {rel}")
            continue
        m = re.search(r"socom:generated v=\S+ source=(\w+)", f.read_text())
        if not m:
            problems.append(f"{rel}: no socom:generated header — hand-written or tampered")
        elif m.group(1) != h:
            problems.append(f"{rel}: stale (source={m.group(1)}, canonical={h}) — DRIFT, recompile")

    for k in ("fast", "medium", "full"):
        if cfg.get("checks", {}).get(k) in (None, "", "true"):
            problems.append(f"socom.yaml checks.{k} is unbound (placeholder)")

    try:
        if _git_hooks_path(root) != HOOKS_DIR:
            problems.append(f"git core.hooksPath not set to {HOOKS_DIR} — gates not wired")
    except FileNotFoundError:
        problems.append("git not available")

    # HR9: canon divergence from the tool's shipped canon is visible and
    # chosen, never accidental. Informational — divergence IS binding.
    deltas = []
    for name in CANON_FILES:
        local = root / SOCOM_DIR / "canon" / name
        if not local.exists():
            continue
        try:
            shipped = resource("canon/" + name)
        except SystemExit:
            continue  # neither embedded nor on disk — can't compare, skip
        # read_bytes().decode (not read_text, which normalizes CRLF) so a real
        # newline-only divergence is not masked — complete-mediation.
        if local.read_bytes().decode("utf-8") != shipped:
            deltas.append(name)

    if problems:
        print("socom doctor — FINDINGS:")
        for p in problems:
            print(f"  ✗ {p}")
        sys.exit(1)
    if deltas:
        print(f"socom doctor — INFO: local canon diverges from shipped canon "
              f"({', '.join(deltas)}) — fine if chosen; upstream what generalizes")
    print(f"socom doctor — clean (canonical source={h})")


# ── precond — the published gate: is THIS work ready to start? ────────────
# Ported from Akili's precondition-audit (backlog #3): a fast pre-flight that
# the repo is work-ready BEFORE a seat starts — the "before" bookend to gates.
# Velocity-first (operator constraint): auto-heals safe gaps, WARNS by default,
# blocks ONLY on the unrecoverable. It accelerates flow by fixing/surfacing the
# exact gap at the altitude where it's met, never by stopping for trivia.
# Sibling to doctor: doctor = substrate health (static); precond = work
# readiness (seat-aware, healing). Run before dispatch; --no-heal is the CI
# posture (assert, don't fix).
def cmd_precond(args):
    import time, shutil
    t0 = time.monotonic()
    root = repo_root()
    seat = next((a for a in args if not a.startswith("-")), None)
    heal = "--no-heal" not in args
    cfg = load_cfg(root)
    rows = []  # (mark, text) ; mark in ✓ ~ ! ✗
    blocks = warns = healed = 0

    # 1. Substrate dirs — heal-on: mkdir; heal-off: block (work writes will fail).
    missing = [d for d in SUBSTRATE_DIRS
               if not (root / SOCOM_DIR / d).is_dir()]
    if not missing:
        rows.append(("✓", "substrate dirs present"))
    elif heal:
        for d in missing:
            (root / SOCOM_DIR / d).mkdir(parents=True, exist_ok=True)
        healed += 1
        rows.append(("~", f"healed: mkdir .socom/{{{','.join(missing)}}}"))
    else:
        blocks += 1
        rows.append(("✗", f"BLOCKS: missing .socom/{{{','.join(missing)}}} "
                          "(run without --no-heal to auto-create)"))

    # 2. Tools — unrecoverable if absent.
    for tool in ("git", "python3"):
        if shutil.which(tool):
            rows.append(("✓", f"{tool} on PATH"))
        else:
            blocks += 1
            rows.append(("✗", f"BLOCKS: {tool} not on PATH"))

    # 3. Git hooks wired — heal-on: set config (safe, reversible); else warn.
    if _git_hooks_path(root) == HOOKS_DIR:
        rows.append(("✓", "git hooks wired (core.hooksPath)"))
    elif heal:
        _wire_hooks(root)
        healed += 1
        rows.append(("~", f"healed: git config core.hooksPath {HOOKS_DIR}"))
    else:
        warns += 1
        rows.append(("!", "WARN: hooks not wired — local gates skip (CI re-asserts)"))

    # 4. Checks bound — warn (work proceeds; gates assert vacuously if unbound).
    unbound = [k for k in ("fast", "medium", "full")
               if cfg.get("checks", {}).get(k) in (None, "", "true")]
    if unbound:
        warns += 1
        rows.append(("!", f"WARN: checks {unbound} unbound — gates can't assert"))
    else:
        rows.append(("✓", "checks.fast/medium/full bound"))

    # 5. Drift — warn with the exact fix (working stale is a risk, not a hard stop here).
    claude = root / "CLAUDE.md"
    if claude.exists():
        m = re.search(r"source=(\w+)", claude.read_text())
        if m and m.group(1) != canonical_hash(root):
            warns += 1
            rows.append(("!", "WARN: compiled views stale — run `socom compile`"))
        else:
            rows.append(("✓", "compiled views in sync"))

    # 6. Claim — only meaningful for production seats; warn if none held by you (R2).
    if seat in ("builder", "reviewer", "validator", "analyst"):
        cdir = root / SOCOM_DIR / "claims"
        mine = [p.stem for p in cdir.glob("*.claim")
                if not claim_expired(p) and claim_holder() in p.read_text()] \
            if cdir.exists() else []
        if mine:
            rows.append(("✓", f"domain claimed by you: {mine}"))
        else:
            warns += 1
            rows.append(("!", f"WARN: no domain claimed by you ({claim_holder()}) "
                              "— parallel seats need a claim (R2)"))

    ms = round((time.monotonic() - t0) * 1000)
    label = f"precond (seat={seat})" if seat else "precond"
    print(f"{label}:")
    for mark, text in rows:
        print(f"  {mark} {text}")
    verdict = "RED" if blocks else "PASS"
    extra = f", {healed} healed" if healed else ""
    print(f"-> {verdict} ({ms}ms): {blocks} blocker(s), {warns} warning(s){extra}")
    if blocks:
        sys.exit(1)


# ── forge (universal git-provider operations) ────────────────────────────
# Verbs + rules are protocol (canon/forge.xml); commands are per-repo
# bindings (socom.yaml `forge:`). Agents run `socom forge <verb>` and never
# re-derive provider mechanics. Unbound verbs fail honestly with guidance.

def cmd_forge(args):
    root = repo_root()
    cfg = load_cfg(root)
    forge = parse_canon(root, "forge.xml")
    verbs = {v.get("id"): (v.findtext("intent") or "").strip()
             for v in forge.findall("verb")}
    bindings = cfg.get("forge", {}) or {}
    if not args or args[0] in ("list", "--list"):
        print("socom forge — verbs (canon) and this repo's bindings:")
        for vid, intent in verbs.items():
            b = bindings.get(vid)
            print(f"  {vid:10} {'BOUND' if b else 'unbound':8} {intent}")
            if b:
                print(f"             $ {b}")
        return
    verb, extra = args[0], args[1:]
    if verb not in verbs:
        sys.exit(f"socom forge: unknown verb '{verb}' — canon verbs: "
                 f"{', '.join(verbs)} (extend canon/forge.xml to add one)")
    cmd = bindings.get(verb)
    if not cmd:
        sys.exit(f"socom forge: '{verb}' is not bound for this repo.\n"
                 f"  intent: {verbs[verb]}\n"
                 f"  bind it in socom.yaml under forge.{verb} (provider-"
                 f"specific command), then `socom compile`. Do not improvise "
                 f"provider mechanics inline.")
    full = cmd + (" " + " ".join(shlex.quote(a) for a in extra) if extra else "")
    print(f"socom forge {verb}: $ {full}", file=sys.stderr)
    sys.exit(subprocess.run(full, shell=True, cwd=root).returncode)


# ── greet ────────────────────────────────────────────────────────────────
# The greeting is itself a capability ladder (doctrine): it probes the
# substrate's adoption state and teaches exactly the next rung — O(1)
# orientation, never a wall of instructions.

BANNER = r"""
   ███████  ██████   ██████  ██████  ███    ███
   ██      ██    ██ ██      ██    ██ ████  ████
   ███████ ██    ██ ██      ██    ██ ██ ████ ██
        ██ ██    ██ ██      ██    ██ ██  ██  ██
   ███████  ██████   ██████  ██████  ██      ██
   substrate for orchestrated, contract-bound machines
   protocol over participants — the agents do the work,
   the protocol holds it together.
"""


def adoption_rung(root: Path) -> tuple[str, str]:
    """Lowest rung whose exit isn't provably green -> (state, next step)."""
    if not (root / "socom.yaml").exists():
        return ("T0 — no substrate", "run `socom init` to plant it")
    cfg = yaml.safe_load((root / "socom.yaml").read_text()) or {}
    if not (root / "CLAUDE.md").exists() or \
            "socom:generated" not in (root / "CLAUDE.md").read_text()[:200]:
        return ("T1 — planted, not compiled", "run `socom compile`")
    if any(cfg.get("checks", {}).get(k) in (None, "", "true")
           for k in ("fast", "medium", "full")):
        return ("T2 — compiled, checks unbound",
                "bind checks.fast/medium/full in socom.yaml to commands that "
                "really run here, then `socom compile`")
    if _git_hooks_path(root) != HOOKS_DIR:
        return ("T3 — bound, gates not wired",
                f"run `socom adopt` (or `git config core.hooksPath {HOOKS_DIR}`)")
    if not (root / SOCOM_DIR / "index" / "baseline.json").exists():
        return ("T4 — wired, no retrieval floor",
                "run `socom baseline` so L1 retrieval has a floor to beat")
    if not (root / SOCOM_DIR / "index" / "vectors.json").exists():
        return ("T5 — floored, retrieval at L0",
                "run `socom embed && socom eval` — L1 must beat the recorded "
                "floor before it serves")
    return ("T6 — operational (L1 retrieval live)",
            "work the loop: claim -> contract -> build -> verify -> handoff "
            "-> prompt. Ask the substrate things: `socom query \"...\"`")


def adoption_bar(state: str, width: int = 10) -> str:
    """Render the adoption ladder as a block progress bar: the 7 rungs (T0..T6)
    map linearly to 0..100%. One honest number a fresh install can watch climb
    from clone to operational — same shape for everyone (§psychological-accept.)."""
    m = re.match(r"T(\d+)", state)
    rung = int(m.group(1)) if m else 0
    pct = round(rung / 6 * 100)
    filled = round(pct / 100 * width)
    return f"socom {'█' * filled}{'░' * (width - filled)} {pct}%"


def _context_meter(data: dict, width: int = 10) -> str:
    """Context-window USED meter from the host's statusline JSON — same math as
    GSD's statusline: subtract the autocompact buffer (~16.5%, or computed from
    CLAUDE_CODE_AUTO_COMPACT_WINDOW), scale to the usable range, color by load.
    Returns '' when no context_window is present (run outside a statusline)."""
    cw = (data.get("context_window") or {}) if isinstance(data, dict) else {}
    remaining = cw.get("remaining_percentage")
    if remaining is None:
        return ""
    total = cw.get("total_tokens") or 1_000_000
    acw = int(os.environ.get("CLAUDE_CODE_AUTO_COMPACT_WINDOW", "0") or 0)
    buffer = min(100, acw / total * 100) if acw > 0 else 16.5
    usable_remaining = max(0, (remaining - buffer) / (100 - buffer) * 100)
    used = max(0, min(100, round(100 - usable_remaining)))
    filled = used * width // 100
    bar = "█" * filled + "░" * (width - filled)
    color = ("\x1b[32m" if used < 50 else "\x1b[33m" if used < 65
             else "\x1b[38;5;208m" if used < 80 else "\x1b[31m")
    return f"ctx {color}{bar} {used}%\x1b[0m"


def cmd_statusline(args):
    """Claude Code statusLine renderer: one line carrying the adoption bar AND
    the context-consumption meter (the way GSD surfaces context). Reads the
    host's statusline JSON on stdin; fails silent — a status line must never
    error. Wire it in settings.json: statusLine.command = "socom statusline"."""
    import json
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except Exception:
        data = {}
    cwd = (data.get("workspace") or {}).get("current_dir") or "."
    try:
        state, _ = adoption_rung(repo_root(Path(cwd)))
        left = adoption_bar(state)
    except Exception:
        left = "socom"
    ctx = _context_meter(data)
    print(f"{left}  ·  {ctx}" if ctx else left)


def cmd_greet(args):
    root = repo_root(Path(args[0]) if args else None)
    print(BANNER)
    state, nxt = adoption_rung(root)
    print(f"   repo: {root.name}")
    print(f"   {adoption_bar(state)}")
    print(f"   rung: {state}")
    print(f"   next: {nxt}")
    blog = root / SOCOM_DIR / "gates" / "breaches.log"
    if blog.exists():
        n = len([ln for ln in blog.read_text().splitlines() if ln.strip()])
        if n:
            print(f"   debt: {n} open amber breach(es) — `socom breach list`")
    mem = root / SOCOM_DIR / "memory" / "memories"
    if mem.exists():
        n = len(list(mem.glob("*.md")))
        if n:
            print(f"   bank: {n} memories on file — the substrate remembers")
    print()


# ── adopt (one command: fresh clone -> wired gates) ────────────────────────

def cmd_adopt(args):
    """One command from a fresh clone to live gates: plant the substrate (init)
    -> compile the runtime adapters -> wire git hooks -> report the rung. Closes
    the dormant-gates class: core.hooksPath was only ever PRINTED as a manual
    step (and auto-healed only inside `precond`), so a fresh clone's LOCAL gates
    slept until someone happened to heal them. Idempotent: init is exists-guarded,
    compile is no-clobber, the hook wiring is a config set. Composes the existing
    steps — no new substrate logic, so adopt can never drift from init/compile."""
    root = repo_root(Path(args[0]) if args else None)
    cmd_init([str(root)])       # plant + greet with the post-plant rung
    cmd_compile([str(root)])    # render adapters (no-clobber on hand-edited views)
    if _wire_hooks(root):
        print(f"  ✓ git hooks wired (core.hooksPath={HOOKS_DIR}) — local gates live")
    else:
        print(f"  ! hooks NOT wired: not a git repo. Run `git init`, then "
              f"`socom adopt` again. CI re-asserts every gate regardless.",
              file=sys.stderr)
    state, nxt = adoption_rung(root)
    print(f"  {adoption_bar(state)}")
    print(f"  rung: {state}\n  next: {nxt}")
