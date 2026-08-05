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
from socom.blackboard import bb_author, bb_cfg, bb_live_for_session
from socom.core import CANON_FILES, HOOKS_DIR, SOCOM_DIR, SOCOM_VERSION, _now_iso, canonical_hash, load_cfg, md_text, parse_canon, repo_root, resource, write_generated

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
            domains:                 # a NAME for a set of paths — claims are
              core: "src/**"         # per-PATH; EDIT so `socom claim core` covers
                                     # what you mean. Also lesson granularity.
            blackboard:              # findings + path leases, local by default
              ref: refs/socom/blackboard   # a directly-pushed ref, NOT an MR —
              remote: origin               # a finding must arrive at claim time
              sync: false            # ⚠️ OPT-IN. true = socom PUSHES the ref
                                     # above to the remote above — YOUR repo's
                                     # origin, which your colleagues share.
                                     # Turn it on when you want the surface
                                     # shared across clones; leave it off and
                                     # the blackboard is a local notebook.
              policy: lease          # the conflict-policy seam
              ttl_s: 28800           # 8h; a dead session never wedges a path
            checks:                  # bind to commands that really run here
              fast: "true"           # seconds-budget; runs at task-completion
              medium: "true"         # pre-commit (amber band)
              full: "true"           # pre-push + CI (red band)
            ci:
              status: "echo 'bind me: cache-free pipeline state query'"
            seats:                   # context_budget (tokens, optional) caps a seat's spawn brief + defaults `context emit --budget`
              builder:  {{ runtime: claude-code, model: default }}
              reviewer: {{ runtime: claude-code, model: different-family-preferred, context_budget: 600 }}
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
    doms = cfg.get("domains") or {}
    out.append("\nDomains (a name for a set of paths — claims are per-path): "
               + (", ".join(f"{k} -> {v}" for k, v in doms.items())
                  if isinstance(doms, dict) else ", ".join(doms)) + "\n")

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


# core.hooksPath is the ONE piece of the adopting repo's own configuration that
# socom writes, so it is the one place socom can be destructive. Recording the
# prior value is what makes that write reversible; refusing a FOREIGN value is
# what keeps the "additive and non-destructive" claim true for a repo that
# already routes hooks somewhere (husky, lefthook, its own convention). Both
# live beside the single writer so "what adopt did to your config" has one home.
HOOKS_PRIOR_KEY = "socom.priorhookspath"

# The durable record that the operator LEFT — the other half of `unadopt`.
# unadopt restored core.hooksPath and then erased every trace of itself, so the
# next `precond` read an unwired repo, could not tell "never adopted" from
# "adopted and left", called it drift, healed it, and scored the reversal as
# `1 healed` under a PASS verdict without ever printing the word "adopt"
# (DEF-PRECOND-SILENTLY-REVERSES-UNADOPT-01). An exit that a later command
# silently undoes is not an exit — and it is worse than shipping no exit at all,
# because the user believes they left. Set by unadopt, honoured by the single
# hook-wiring writer, and cleared by exactly one thing: an explicit `socom adopt`.
HOOKS_OPTOUT_KEY = "socom.unadopted"


def _git_config_get(root: Path, key: str, local: bool = False):
    """The configured value for `key`, or None if the key is UNSET. Distinct
    from "": a key deliberately recorded as empty means "core.hooksPath was
    unset before adopt", and `unadopt` has to tell that apart from "socom never
    recorded anything here" to restore the right state.

    `local=True` reads ONLY this repo's config. That distinction is load-bearing:
    a value inherited from --global or --system is not this repo's to save and
    restore, and writing it back locally would PIN the repo to a stale copy of a
    setting the operator can still change globally."""
    cmd = ["git", "config"] + (["--local"] if local else []) + ["--get", key]
    p = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
    return p.stdout.rstrip("\n") if p.returncode == 0 else None


def _default_hooks_present(root: Path) -> list:
    """Executable, non-`.sample` hooks in the repo's DEFAULT hook directory.

    An unset `core.hooksPath` does NOT mean "this repo has no hooks" — it means
    "hooks live in the default place", which is exactly where `git init` seeds
    the `.sample` files and where **lefthook installs real ones**. Treating unset
    as nobody-home is what let adopt silently disable a repo's whole hook set
    while printing a green checkmark (verified: a `.git/hooks/pre-commit` that
    blocked before adopt stopped running after it, and the commit landed).
    `.sample` files are inert by definition and are not evidence of hooks."""
    p = subprocess.run(["git", "rev-parse", "--git-path", "hooks"], cwd=root,
                       capture_output=True, text=True)
    if p.returncode:
        return []
    d = Path(p.stdout.strip())
    if not d.is_absolute():
        d = root / d
    if not d.is_dir():
        return []
    try:
        return sorted(f.name for f in d.iterdir()
                      if f.is_file() and not f.name.endswith(".sample")
                      and os.access(f, os.X_OK))
    except OSError:
        return []


def _record_binpath(root: Path):
    """Record THIS machine's socom location in LOCAL git config (never committed)
    so the portable committed hook can resolve the tool without a PATH install
    — replaces the old absolute path baked into the shared hook (HR1)."""
    subprocess.run(["git", "config", "socom.binpath",
                    str(Path(__file__).resolve())],
                   cwd=root, capture_output=True)


def _wire_hooks(root: Path) -> str:
    """Point core.hooksPath at HOOKS_DIR, recording what it was so `unadopt` can
    put it back. The single WRITER for the hooks-wiring truth — both doctor-heal
    and `adopt` route through here, so 'where the hooks live' lives in exactly
    one place (§least-common-mechanism). Fails soft: never raises.

    Returns the outcome, which the caller MUST report — the three cases are not
    interchangeable and collapsing them to a bool is what let the destructive
    one go unnoticed:
      'wired'     — the repo's hooks are socom's (idempotent no-op if already)
      'foreign'   — the repo already routes hooks elsewhere; NOTHING was changed
      'unadopted' — the operator ran `unadopt`; NOTHING was changed, and only an
                    explicit `adopt` clears that record
      'nogit'     — not a git repo, nothing to wire (CI re-asserts regardless)

    Why 'foreign' refuses rather than overwrites: a repo on husky has its
    lint-staged, its commit-msg validator and its secret scanner behind
    core.hooksPath. Repointing it does not make those gates fail — it makes them
    silently PASS, which is the one failure mode a gate must never have. socom
    declines and says so; the adopter can switch deliberately with one command.

    Why 'unadopted' refuses: an unset core.hooksPath is ambiguous — it is both
    "socom was never here" and "socom was here and I asked it to leave". Healing
    on that ambiguity is how the documented exit got silently reversed. The
    record disambiguates it, and it is checked HERE, at the single writer, so no
    caller can heal around it (§least-common-mechanism)."""
    if _git_config_get(root, HOOKS_OPTOUT_KEY) is not None:
        return "unadopted"
    cur = _git_hooks_path(root)
    if cur == HOOKS_DIR:
        _record_binpath(root)
        return "wired"
    # Record the pre-adopt value BEFORE touching anything, and only once — a
    # second `adopt` must not overwrite the record with socom's own value, or
    # `unadopt` would faithfully "restore" the repo to socom.
    # Record the LOCAL value, not the effective one: a global/system setting is
    # not this repo's to save, and writing it back locally would pin the repo to
    # a stale copy of a setting the operator can still change globally.
    if _git_config_get(root, HOOKS_PRIOR_KEY) is None:
        subprocess.run(["git", "config", "--local", HOOKS_PRIOR_KEY,
                        _git_config_get(root, "core.hooksPath", local=True) or ""],
                       cwd=root, capture_output=True)
    if cur:
        return "foreign"
    # An unset core.hooksPath is NOT "no hooks" — see _default_hooks_present.
    if _default_hooks_present(root):
        return "foreign"
    subprocess.run(["git", "config", "--local", "core.hooksPath", HOOKS_DIR],
                   cwd=root, capture_output=True)
    _record_binpath(root)
    return "wired" if _git_hooks_path(root) == HOOKS_DIR else "nogit"


# ── ignore wiring: socom declares its own artifacts to the host repo's tools ──
# socom writes files INTO someone else's repo, and two of that repo's tools then
# form an opinion about them:
#   git       — machine-local runtime state (per-PID lease shards, this machine's
#               breach log, the derived index) is one `git add -A` from a commit,
#               and then conflicts on every branch.
#   the formatter — a generated adapter is not written to the host's prettier
#               config, so a format check that was green before adopt goes red
#               on files the adopter did not write and cannot sensibly fix.
# Both are the same defect: socom never told the host's tools which files are
# socom's. Emitting prettier-shaped YAML would fix neither (the next formatter,
# and git, would still be wrong). Naming its own artifacts in the ignore file
# each tool already reads fixes the class.

IGNORE_BEGIN = "# >>> socom (generated block — edit outside the markers)"
IGNORE_END = "# <<< socom"

# Machine-local runtime state ONLY: regenerable (`socom embed`), per-machine, and
# conflict-generating if shared. NOT canon, probes, lessons or memory — those are
# the substrate's SOURCE and must travel with the repo, so `.socom/` as a whole
# must never appear here (it does appear in the prettier block, where excluding
# all of it is right: none of it is the host's to format).
GITIGNORE_PATTERNS = [
    f"{SOCOM_DIR}/blackboard/",
    f"{SOCOM_DIR}/claims/",
    f"{SOCOM_DIR}/gates/breaches.log",
    f"{SOCOM_DIR}/gates/breaches.resolved.log",
    f"{SOCOM_DIR}/index/vectors.json",
    f"{SOCOM_DIR}/index/chunks.jsonl",
]

_PRETTIER_CONFIGS = (
    ".prettierrc", ".prettierrc.json", ".prettierrc.json5", ".prettierrc.yml",
    ".prettierrc.yaml", ".prettierrc.js", ".prettierrc.cjs", ".prettierrc.mjs",
    ".prettierrc.toml", "prettier.config.js", "prettier.config.cjs",
    "prettier.config.mjs", ".prettierignore",
)


def _has_prettier(root: Path) -> bool:
    """Does this repo actually run prettier? Only then is a .prettierignore
    socom's business — planting one in a Go repo is litter. Prettier is the only
    common formatter that claims markdown/yaml/json, which is the whole of
    socom's emitted surface: black/ruff-format own .py, rustfmt .rs, gofmt .go,
    and none of them will ever look at a generated CLAUDE.md."""
    import json
    if any((root / n).exists() for n in _PRETTIER_CONFIGS):
        return True
    pkg = root / "package.json"
    if not pkg.exists():
        return False
    try:
        d = json.loads(pkg.read_text())
    except (ValueError, OSError):
        return False
    # A package.json whose top level is a list/null/number is still valid JSON,
    # and `"prettier" in d` raises TypeError on it — a crash the try/except above
    # was written to prevent but does not cover.
    if not isinstance(d, dict):
        return False
    return ("prettier" in d
            or "prettier" in (d.get("devDependencies") or {})
            or "prettier" in (d.get("dependencies") or {}))


def _socom_artifacts(root: Path) -> list:
    """The files socom itself wrote — the ONLY ones it may name in the host's
    ignore files. Membership is PROVED by the `socom:generated` header, never
    assumed from the path: a repo that owns its own .gitlab-ci.yml must not find
    it silently excluded from its own formatter because socom recognised the
    name."""
    out = []
    if (root / SOCOM_DIR).is_dir():
        out.append(f"{SOCOM_DIR}/")
    if (root / "socom.yaml").exists():
        out.append("socom.yaml")
    candidates = ["CLAUDE.md", "AGENTS.md", ".cursor/rules/socom.mdc",
                  ".gitlab-ci.yml", ".github/workflows/socom-gates.yml"]
    agents = root / ".claude" / "agents"
    if agents.is_dir():
        candidates += [f".claude/agents/{p.name}" for p in sorted(agents.glob("*.md"))]
    for rel in candidates:
        f = root / rel
        try:
            if f.is_file() and "socom:generated" in f.read_text(errors="ignore"):
                out.append(rel)
        except OSError:
            pass
    return out


def _ensure_ignore_block(f: Path, patterns: list, why: str) -> str:
    """Idempotently maintain socom's marked block in one ignore file. Everything
    outside the markers is left byte-for-byte as the repo wrote it; the block
    itself is rewritten when the pattern set changes, so a later socom version
    adding an artifact does not append a second block. Returns 'wrote',
    'updated' or 'unchanged'."""
    body = "\n".join([f"# {why}", *patterns])
    block = "\n".join([IGNORE_BEGIN, body, IGNORE_END])
    if not f.exists():
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(block + "\n")
        return "wrote"
    try:
        text = f.read_text()
    except OSError:
        return "malformed"

    # Marker arithmetic BEFORE any surgery. The previous version checked only
    # that both markers were PRESENT, then split on the first of each — which
    # crashed outright when they were out of order (a plain `sort` on .gitignore
    # reorders them, since '<' sorts before '>'), and SILENTLY DELETED whatever
    # sat between a duplicated BEGIN and the first END. Both verified.
    # An ignore file is the adopter's, and the only safe failure here is to
    # touch nothing and say so.
    n_begin, n_end = text.count(IGNORE_BEGIN), text.count(IGNORE_END)
    if n_begin == 0 and n_end == 0:
        sep = "" if text.endswith("\n") else "\n"
        f.write_text(text + sep + "\n" + block + "\n")
        return "updated"
    if n_begin != 1 or n_end != 1 or text.index(IGNORE_BEGIN) > text.index(IGNORE_END):
        return "malformed"
    pre, rest = text.split(IGNORE_BEGIN, 1)
    _old, post = rest.split(IGNORE_END, 1)
    if _old.strip("\n") == body:
        return "unchanged"
    f.write_text(pre + block + post)
    return "updated"


def _wire_ignores(root: Path):
    """Declare socom's artifacts to git and (when present) prettier. Reports what
    it did — a file socom writes into the adopter's repo is never silent."""
    git_res = _ensure_ignore_block(
        root / ".gitignore", GITIGNORE_PATTERNS,
        "machine-local socom runtime state: regenerable, per-machine, and a "
        "merge conflict on every branch if shared. The rest of .socom/ (canon, "
        "probes, lessons, memory) is SOURCE — keep it committed.")
    if git_res == "malformed":
        print(f"  ! .gitignore: socom's marked block is malformed (duplicated, "
              f"out of order, or half-deleted) — LEFT UNTOUCHED. Machine-local "
              f"runtime state is NOT ignored, so `git add -A` can commit it. "
              f"Fix by deleting every '{IGNORE_BEGIN}'…'{IGNORE_END}' block by "
              f"hand, then re-run `socom adopt`.", file=sys.stderr)
    elif git_res != "unchanged":
        print(f"  ✓ .gitignore: socom runtime state ignored "
              f"({len(GITIGNORE_PATTERNS)} patterns) — `git add -A` is safe")

    if not _has_prettier(root):
        return
    arts = _socom_artifacts(root)
    if not arts:
        return
    p_res = _ensure_ignore_block(
        root / ".prettierignore", arts,
        "socom-generated files. They are not written to your prettier config, "
        "and they are not yours to format — excluded so adopting socom cannot "
        "turn a green format check red.")
    if p_res == "malformed":
        print(f"  ! .prettierignore: socom's marked block is malformed — LEFT "
              f"UNTOUCHED. Your format check may go red on socom's generated "
              f"files. Delete the marked block by hand and re-run `socom adopt`.",
              file=sys.stderr)
    elif p_res != "unchanged":
        print(f"  ✓ .prettierignore: {len(arts)} socom-generated path(s) "
              f"excluded — your format check stays green")


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
        left = _git_config_get(root, HOOKS_OPTOUT_KEY)
        if _git_hooks_path(root) == HOOKS_DIR:
            pass
        elif left is not None:
            # Not a finding. The operator unadopted this repo on purpose, and
            # reporting their own decision back as a defect is how a tool talks
            # someone into re-adopting it. State it; do not fail on it.
            print(f"socom doctor — INFO: unadopted on {left or 'an unrecorded date'}"
                  f" — hooks intentionally unwired; `socom adopt` re-arms them")
        else:
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
    # Heals that write the HOST REPO'S OWN config are counted apart from heals
    # that only touch socom's own dirs. They are not the same act, and collapsing
    # them is what let a git-config write land inside `PASS … 0 warning(s)`.
    cfg_heals = 0

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
    # Healing NEVER includes taking over a foreign core.hooksPath: precond is
    # allowed to fix what socom owns, never to disable what the repo owns.
    if _git_hooks_path(root) == HOOKS_DIR:
        rows.append(("✓", "git hooks wired (core.hooksPath)"))
    elif heal:
        state = _wire_hooks(root)
        if state == "wired":
            healed += 1
            cfg_heals += 1
            warns += 1   # a write to the host's git config is never a quiet PASS
            rows.append(("~", f"healed: WROTE YOUR GIT CONFIG — core.hooksPath="
                              f"{HOOKS_DIR} (reverse it with `socom unadopt`, "
                              f"which precond now honours durably)"))
        elif state == "unadopted":
            warns += 1
            rows.append(("!", f"WARN: this repo was UNADOPTED on "
                              f"{_git_config_get(root, HOOKS_OPTOUT_KEY) or 'an unrecorded date'}"
                              f" — hooks left unwired and precond will not re-arm "
                              f"them. `socom adopt` is the way back in, and the only "
                              f"thing that clears the record. CI re-asserts every "
                              f"gate meanwhile."))
        elif state == "foreign":
            warns += 1
            rows.append(("!", f"WARN: core.hooksPath is {_git_hooks_path(root)!r}, "
                              "not socom's — left alone (socom never disables "
                              "hooks you already have). Local socom gates skip; "
                              "CI re-asserts. `socom adopt` prints the way forward."))
        else:
            warns += 1
            rows.append(("!", "WARN: hooks not wired — not a git repo (CI re-asserts)"))
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
    # Local read (sync=False): precond is a fast pre-flight and must not block
    # on the network to answer a question about this session's own shard.
    if seat in ("builder", "reviewer", "validator", "analyst"):
        mine = [p for l in bb_live_for_session(root, bb_cfg(cfg), sync=False)
                for p in l.get("paths", [])]
        if mine:
            rows.append(("✓", f"paths claimed by you: {mine}"))
        else:
            warns += 1
            rows.append(("!", f"WARN: no paths claimed by you ({bb_author(root)}) — "
                              "parallel seats need a claim, and claiming is how "
                              "you receive the findings on what you are about to "
                              "touch (R2)"))

    ms = round((time.monotonic() - t0) * 1000)
    label = f"precond (seat={seat})" if seat else "precond"
    print(f"{label}:")
    for mark, text in rows:
        print(f"  {mark} {text}")
    verdict = "RED" if blocks else "PASS"
    extra = (f", {healed} healed" if healed else "") + \
            (f" ({cfg_heals} WROTE GIT CONFIG)" if cfg_heals else "")
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
    # value pointer: shown once any signal exists, so the "why" is one command away.
    sig = [root / SOCOM_DIR / "gates" / "breaches.log",
           root / SOCOM_DIR / "ledger" / "runs.jsonl",
           root / SOCOM_DIR / "index" / "chunks.jsonl"]
    if any(p.exists() and p.read_text().strip() for p in sig) \
            or list((root / SOCOM_DIR / "context").glob("*.xml")) \
            or list((root / SOCOM_DIR / "claims").glob("*.claim")):
        print("   value: what the substrate has bought you — `socom value`")
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
    # After compile, because the artifact set adopt must declare to the host's
    # tools is only complete once the adapters are rendered.
    _wire_ignores(root)
    # `adopt` is the explicit re-entry, and the ONLY thing that clears the exit
    # record. That asymmetry — one command sets it, one command clears it, every
    # other command honours it — is the whole of what makes `unadopt` durable.
    left = _git_config_get(root, HOOKS_OPTOUT_KEY)
    if left is not None:
        subprocess.run(["git", "config", "--unset", HOOKS_OPTOUT_KEY],
                       cwd=root, capture_output=True)
        print(f"  · re-adopting: you unadopted this repo on "
              f"{left or 'an unrecorded date'} — that record is now cleared and "
              f"socom may wire hooks again")
    state = _wire_hooks(root)
    if state == "wired":
        print(f"  ✓ git hooks wired (core.hooksPath={HOOKS_DIR}) — local gates live")
    elif state == "foreign":
        prior = _git_hooks_path(root)
        if not prior:
            # The default-location case: core.hooksPath is unset, but the repo
            # HAS hooks where git looks by default (lefthook, or hand-installed).
            found = _default_hooks_present(root)
            print(f"  ! hooks NOT wired — this repo already has git hooks in "
                  f"the default location: {', '.join(found)}.\n"
                  f"    Nothing was changed. core.hooksPath is unset, which "
                  f"means 'use .git/hooks' — not 'no hooks'. Setting it would "
                  f"silently STOP every one of those.\n"
                  f"    Two ways forward:\n"
                  f"      keep yours — do nothing. socom's gates still run in "
                  f"CI, and `socom gate <name>` runs any of them by hand.\n"
                  f"      switch     — git config core.hooksPath {HOOKS_DIR}\n"
                  f"                   (`socom unadopt` unsets it again; your "
                  f"hook files are never touched)",
                  file=sys.stderr)
            state, nxt = adoption_rung(root)
            print(f"  {adoption_bar(state)}")
            print(f"  rung: {state}\n  next: {nxt}")
            return
        print(f"  ! hooks NOT wired — this repo already routes git hooks to "
              f"{prior!r}.\n"
              f"    Nothing was changed. Repointing it would not fail your "
              f"existing hooks, it would silently STOP them (lint-staged, "
              f"commit-msg validators, secret scanners), and socom does not do "
              f"that to a repo it was just invited into.\n"
              f"    Two ways forward:\n"
              f"      keep yours — do nothing. socom's gates still run in CI, "
              f"and `socom gate <name>` runs any of them by hand.\n"
              f"      switch     — git config core.hooksPath {HOOKS_DIR}\n"
              f"                   (`socom unadopt` puts {prior!r} back; socom "
              f"recorded it as {HOOKS_PRIOR_KEY})",
              file=sys.stderr)
    else:
        print(f"  ! hooks NOT wired: not a git repo. Run `git init`, then "
              f"`socom adopt` again. CI re-asserts every gate regardless.",
              file=sys.stderr)
    state, nxt = adoption_rung(root)
    print(f"  {adoption_bar(state)}")
    print(f"  rung: {state}\n  next: {nxt}")


def cmd_unadopt(args):
    """The repo-level exit `uninstall` never was. `uninstall` removes a symlink
    from ~/.local/bin; nothing has ever put the ADOPTING REPO back the way it
    was. This restores the one piece of the repo's own configuration socom
    writes — core.hooksPath — to whatever it held before adopt, or unsets it if
    it held nothing, and drops the machine-local socom.binpath.

    It deliberately does NOT delete the planted files. Deleting tracked files
    out from under someone is exactly the destructiveness this command exists to
    disclaim; it lists them instead so removing them stays the operator's
    deliberate act."""
    root = repo_root(Path(args[0]) if args else None)
    cur = _git_hooks_path(root)
    prior = _git_config_get(root, HOOKS_PRIOR_KEY)

    if prior is None:
        print(f"socom unadopt: no pre-adopt core.hooksPath on record — socom "
              f"never wired this repo (or a previous unadopt already ran). "
              f"core.hooksPath is {cur or '<unset>'}; left as-is.")
    elif cur != HOOKS_DIR:
        # The record says what the repo had BEFORE adopt; it does not say what
        # the repo has NOW. If hooks no longer point at socom, someone moved
        # them after adopting, and restoring blind would silently disable THAT
        # — the exact clobber this command exists to undo, performed by the undo.
        # Verified: adopt, then `git config core.hooksPath .husky`, then unadopt
        # unset husky and reported "it was unset before adopt" as if current.
        print(f"socom unadopt: core.hooksPath is {cur or '<unset>'}, which is "
              f"not socom's ({HOOKS_DIR}) — it was changed after adopt. "
              f"Refusing to overwrite it; that would be the same silent clobber "
              f"unadopt exists to undo.\n"
              f"  socom recorded {prior or '<unset>'} as the pre-adopt value. "
              f"If you really want it back:\n"
              f"    " + (f"git config --local core.hooksPath {prior}" if prior
                         else "git config --local --unset core.hooksPath") + "\n"
              f"  To drop socom's record: git config --unset {HOOKS_PRIOR_KEY}")
        return
    elif prior == "":
        subprocess.run(["git", "config", "--unset", "core.hooksPath"],
                       cwd=root, capture_output=True)
        print(f"  ✓ core.hooksPath unset — it was unset before adopt "
              f"(was {cur or '<unset>'})")
    else:
        subprocess.run(["git", "config", "core.hooksPath", prior],
                       cwd=root, capture_output=True)
        print(f"  ✓ core.hooksPath restored to {prior!r} (was {cur or '<unset>'})")
    if prior is not None:
        subprocess.run(["git", "config", "--unset", HOOKS_PRIOR_KEY],
                       cwd=root, capture_output=True)
        subprocess.run(["git", "config", "--unset", "socom.binpath"],
                       cwd=root, capture_output=True)

    # Record the exit DURABLY, and do it on every path that got this far — the
    # "socom never wired this" branch included, because the operator asked to
    # leave either way and the next `precond` must not read the result as drift.
    # Erasing every trace of itself is what made unadopt reversible-by-accident.
    subprocess.run(["git", "config", "--local", HOOKS_OPTOUT_KEY, _now_iso()],
                   cwd=root, capture_output=True)
    print(f"  ✓ exit recorded ({HOOKS_OPTOUT_KEY}) — no socom command re-wires "
          f"hooks from here; `socom adopt` is the only way back in")

    # Read back rather than assert — the restore is the whole product of this
    # command, so it states what git now reports, not what it just tried to set.
    now = _git_hooks_path(root)
    print(f"  core.hooksPath now: {now or '<unset>'}")

    left = [p for p in (SOCOM_DIR, HOOKS_DIR, "socom.yaml", "CLAUDE.md",
                        "AGENTS.md", ".cursor/rules/socom.mdc",
                        ".github/workflows/socom-gates.yml")
            if (root / p).exists()]
    if left:
        print(f"  · left in place (yours to delete, socom will not): "
              f"{', '.join(left)}")
        print(f"  · socom's blocks in .gitignore/.prettierignore are marked "
              f"'{IGNORE_BEGIN}' — delete the marked block to remove them.")
