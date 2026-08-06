"""socom install — self-install onto PATH + `quickstart` first-run on-ramp.
Assembled into bin/socom by build.py (install is late in ORDER, so quickstart may
reuse rung commands from lifecycle/retrieval/spawn/value with no import cycle)."""
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
import yaml
from socom.core import SOCOM_DIR, SOCOM_VERSION, load_cfg, repo_root
from socom.lifecycle import adoption_bar, adoption_rung, cmd_adopt, cmd_compile
from socom.retrieval import cmd_baseline, cmd_embed, cmd_eval, cmd_query
from socom.spawn import RUNTIMES
from socom.value import cmd_value
# === BODY ===

# ── install (self-bootstrap onto PATH) ─────────────────────────────────

DEFAULT_BIN_DIR = Path.home() / ".local" / "bin"


def _on_path(d: Path) -> bool:
    return str(d) in os.environ.get("PATH", "").split(os.pathsep)


def cmd_install(args):
    """Symlink the running socom file onto PATH. The link points at the file you
    ran (Path(__file__)), so nothing is copied — the symlink target is the source
    of truth (a checkout's bin/socom, or a distributed self-contained file)."""
    import tempfile
    force = "--force" in args
    rest = [a for a in args if a != "--force"]
    # `socom install --help` used to read --help as the TARGET DIR and create a
    # literal `--help/` directory holding a symlink, in whatever repo you asked
    # from. Asking a tool what it does must never leave debris behind. The guard
    # that fixed it here is now cli.py's dispatch intercept, which covers EVERY
    # command — this one was the instance that got patched, not the class.
    dst_dir = (Path(rest[0]).expanduser() if rest else DEFAULT_BIN_DIR)
    src = Path(__file__).resolve()  # the running socom file itself — works whether
    dst = dst_dir / "socom"         # this is repo/bin/socom or a distributed copy
    # The symlink will dangle if its target later disappears. Warn LOUDLY when the
    # target is a temp dir (the README's curl-then-install lands here) so a
    # permanent install never silently points at an ephemeral file (R6).
    if str(src).startswith(str(Path(tempfile.gettempdir()).resolve())):
        print(f"socom install: WARNING — installing from a temp location ({src}). "
              "Move socom somewhere permanent (e.g. ~/.local/bin) and install from "
              "there, or the symlink will break when the temp file is cleaned up.",
              file=sys.stderr)
    dst_dir.mkdir(parents=True, exist_ok=True)
    if dst.is_symlink() and dst.resolve() == src and not force:
        print(f"socom install: already installed → {dst}")
    elif dst.is_symlink() or dst.exists():
        if not force:
            tgt = dst.resolve() if dst.is_symlink() else "(regular file)"
            sys.exit(f"socom install: {dst} already exists ({tgt}), not this "
                     f"checkout. Re-run with --force to repoint.")
        dst.unlink()
        dst.symlink_to(src)
        print(f"socom install: repointed {dst} → {src}")
    else:
        dst.symlink_to(src)
        print(f"socom install: linked {dst} → {src}")
    if _on_path(dst_dir):
        print(f"socom install: {dst_dir} is on PATH — `socom` is ready.")
    else:
        print(f"socom install: NOTE {dst_dir} is not on PATH. Add it:")
        print(f'  export PATH="{dst_dir}:$PATH"')


def cmd_uninstall(args):
    dst_dir = (Path(args[0]).expanduser() if args else DEFAULT_BIN_DIR)
    dst = dst_dir / "socom"
    src = Path(__file__).resolve()
    if not dst.is_symlink() and not dst.exists():
        print(f"socom uninstall: nothing at {dst}")
        return
    if dst.is_symlink() and dst.resolve() == src:
        dst.unlink()
        print(f"socom uninstall: removed {dst}")
        # uninstall is MACHINE-level: it removes the binary from PATH and
        # nothing else. Every repo that ran `adopt` still has its core.hooksPath
        # pointing at socom's hooks — which now resolve to a tool that is gone.
        # Say so, and name the repo-level exit.
        print("socom uninstall: NOTE this removed the binary only. A repo you "
              "ran `socom adopt` in still has core.hooksPath set — run "
              "`socom unadopt` IN THAT REPO first to put its hooks back.")
    else:
        sys.exit(f"socom uninstall: {dst} is not a symlink to this checkout — "
                 f"refusing to remove. Remove it manually if intended.")


def cmd_version(args):
    """Identify the RUNNING artifact — version, build digest, interpreter, platform.

    The build digest, not SOCOM_VERSION, is the load-bearing field. SOCOM_VERSION
    is a static "0.1" that has never moved, so it cannot answer "which build did
    this person actually run" — and the distribution model is `curl` of raw main,
    which mints a new artifact on every merge under an unchanging version string.
    Hashing the executing file gives an identity that DOES move, and one anybody
    can reproduce against the public URL:

        curl -fsSL <raw-url> | shasum -a 256 | cut -c1-12

    Why it exists: an exposure run records its result on a sheet, and a result
    that cannot name the build it was produced against is not reproducible
    evidence (§verify-never-claim). EV-NONAUTHOR-EXPOSURE-01's sheet had no way
    to state this.

    `Path(__file__).resolve()` follows the ~/.local/bin symlink `install` plants,
    so this always hashes the real artifact rather than the link. In the
    distributed single-file form that IS bin/socom — the whole tool, one hash. Run
    from a src checkout it is this module only, so the path is printed alongside
    the digest and the output is never quietly misleading about what was hashed.
    """
    src = Path(__file__).resolve()
    try:
        digest = hashlib.sha256(src.read_bytes()).hexdigest()[:12]
    except OSError as e:
        # Degrade LOUDLY (R6): an unreadable artifact is reported as such, never
        # silently as a blank or a fabricated digest.
        digest = f"UNREADABLE ({e.__class__.__name__})"
    py = ".".join(str(n) for n in sys.version_info[:3])
    print(f"socom    {SOCOM_VERSION}")
    print(f"build    {digest}")
    print(f"source   {src}")
    print(f"python   {py}")
    print(f"platform {sys.platform}")


# ── quickstart (the first-run on-ramp: climb the adoption ladder) ──────────
# thread 1 of the orchestration vision — post-install DIRECT value. `adopt` lands a
# fresh repo at T2 in one command; quickstart climbs the rest of the ladder
# (adoption_rung: T2 bind-checks, T4 baseline, T5 embed, T6 eval) automatically,
# doing every MECHANICAL rung by reusing its existing command and degrading LOUDLY
# at the rungs that need human judgment (an undetectable test command), content
# (>=12 probes for L1 eval), or environment (the runtime binary). It reimplements no
# rung, writes no ledger row, and seeds no fake promise — the honesty `value` keeps.

# (test-command, detector-priority) — a Makefile `test:` target is the most explicit
# intent, so it wins; then the ecosystem manifests in rough ubiquity order.
def _detect_checks(root: Path):
    """Best-effort detect THIS repo's real test command, else None. Conservative:
    a miss returns None (quickstart degrades loudly) — it never invents a command."""
    mk = root / "Makefile"
    if mk.exists():
        try:
            if re.search(r'^test:', mk.read_text(errors="ignore"), re.M):
                return "make test"
        except OSError:
            pass
    pkg = root / "package.json"
    if pkg.exists():
        try:
            if ((json.loads(pkg.read_text()).get("scripts") or {}).get("test")):
                return "npm test"
        except (ValueError, OSError):
            pass
    if any((root / n).exists() for n in
           ("pyproject.toml", "setup.py", "pytest.ini", "tox.ini")) \
            or (root / "tests").is_dir():
        return "pytest -q"
    if (root / "Cargo.toml").exists():
        return "cargo test"
    if (root / "go.mod").exists():
        return "go test ./..."
    return None


# the placeholder values adoption_rung treats as "unbound" (None/""/"true"); the
# init template ships quoted "true" -> the string "true"; unquoted true -> bool True.
_CHECK_PLACEHOLDERS = (None, "", "true", True)


def _bind_checks(root: Path, command: str) -> bool:
    """Bind checks.fast/medium/full to `command` IFF all three are still the unbound
    placeholder (never clobber a real binding — the HR2 no-clobber posture). The guard
    reads the PARSED config (so it sees every placeholder form — "true"/true/""/null
    alike); the rewrite is SECTION-SCOPED to the `checks:` block only (a `fast:` under
    some other section is never touched) and replaces whatever scalar is there (the
    guard already proved it a placeholder), PRESERVING the trailing comment — not a yaml
    round-trip that would strip every comment. Returns True if it wrote, False if left."""
    checks = (load_cfg(root).get("checks") or {})
    if not all(checks.get(k) in _CHECK_PLACEHOLDERS for k in ("fast", "medium", "full")):
        return False
    cfgf = root / "socom.yaml"
    header = re.compile(r'^(?P<i>[ \t]*)checks:[ \t]*(?:#.*)?$')
    keyline = re.compile(r'^(?P<i>[ \t]*)(?P<k>fast|medium|full):[ \t]*'
                         r'[^#\n]*?[ \t]*(?P<c>#.*)?$')
    out, in_checks, checks_indent = [], False, -1
    for line in cfgf.read_text().split("\n"):
        hm = header.match(line)
        if hm:
            in_checks, checks_indent = True, len(hm.group("i"))
            out.append(line)
            continue
        if in_checks and line.strip():
            if len(line) - len(line.lstrip()) <= checks_indent:
                in_checks = False                       # dedented out of the block
            else:
                km = keyline.match(line)
                if km:
                    c = km.group("c")
                    line = (f'{km.group("i")}{km.group("k")}: "{command}"'
                            + (f'  {c}' if c else ""))
        out.append(line)
    cfgf.write_text("\n".join(out))
    return True


def _probe_count(root: Path) -> int:
    """How many L1 probes are on file — the L1-eval gate needs >=12 (the RAG
    contract). A fresh canon ships 2, so this is what tells quickstart whether T6 is
    even reachable yet (else it reports the honest ceiling, never forces a RED eval)."""
    f = root / SOCOM_DIR / "index" / "probes.yaml"
    if not f.exists():
        return 0
    try:
        return len((yaml.safe_load(f.read_text()) or {}).get("probes") or [])
    except (yaml.YAMLError, OSError):
        return 0


def _runtime_preflight(root: Path):
    """One line per distinct bound runtime binary: is it on PATH? (the same
    shutil.which check spawn --exec uses). Missing is NOT a failure — spawn is
    record-first, so it materializes the launch command either way; this just
    surfaces the verdict at onboarding instead of at the first --exec."""
    seats = (load_cfg(root).get("seats") or {})
    binaries: dict = {}
    for seat, b in seats.items():
        spec = RUNTIMES.get((b or {}).get("runtime"))
        if spec:
            binaries.setdefault(spec["binary"], []).append(seat)
    if not binaries:
        return ["  · no launchable runtime bound in socom.yaml seats"]
    lines = []
    for binary, seated in sorted(binaries.items()):
        if shutil.which(binary) is not None:
            lines.append(f"  ✓ runtime '{binary}' on PATH — spawn --exec / monarch "
                         f"recover ready ({', '.join(sorted(seated))})")
        else:
            lines.append(f"  ! runtime '{binary}' NOT on PATH — spawn / monarch recover "
                         f"will materialize-only (print the launch cmd) until it is "
                         f"installed; record-first still works")
    return lines


def cmd_quickstart(args):
    """One command from a fresh repo to a live, demonstrating substrate. Climbs the
    adoption ladder: adopt (plant+compile+wire) -> auto-bind checks -> baseline ->
    embed -> eval (when ready) -> runtime preflight -> a `value` readout + the rung.
    Honest-degrading + idempotent: every step reuses an existing idempotent command,
    binds nothing already bound, fabricates no metric. `--no-eval` skips the L1 attempt."""
    no_eval = "--no-eval" in args
    rest = [a for a in args if a != "--no-eval"]
    root = repo_root(Path(rest[0]) if rest else None)
    print("socom quickstart — from a fresh repo to a live, demonstrating substrate.\n")

    # rungs T1-T3: plant + compile + wire hooks (cmd_adopt is itself idempotent).
    cmd_adopt([str(root)])

    # rung T2: bind the gate checks to THIS repo's real test command (Wall 1).
    print("\n[checks] binding gates to your real test command…")
    detected = _detect_checks(root)
    if detected is None:
        print("  ! no test command detected (looked for a Makefile `test:` target, "
              "package.json scripts.test, pytest/cargo/go signals). Edit checks.fast "
              "in socom.yaml to your suite, then `socom compile` — gates stay vacuous "
              "until you do.")
    elif _bind_checks(root, detected):
        print(f"  ✓ bound checks.fast/medium/full → {detected!r} — gates now run YOUR tests")
        cmd_compile([str(root)])  # re-render adapters so the source hash tracks socom.yaml
    else:
        print(f"  · checks already bound — left as-is (detected {detected!r}, not clobbering)")

    # rungs T4-T5: the knowledge floor + index (Wall 2). query works after this (L0
    # fallback) even before L1 is certified.
    print("\n[knowledge] measuring the L0 floor + building the L1 index…")
    cmd_baseline([str(root)])
    cmd_embed([str(root)])

    # rung T6: L1 acceptance — only attemptable with >=12 probes; never force a RED.
    if no_eval:
        print("  · L1 eval skipped (--no-eval).")
    else:
        n = _probe_count(root)
        if n < 12:
            print(f"  · L1 acceptance needs ≥12 probes; you have {n}. Grow "
                  f".socom/index/probes.yaml, then `socom eval`. (query already works via L0.)")
        else:
            try:
                cmd_eval([str(root)])
            except SystemExit as e:  # eval exits RED on a miss — report, never crash
                print(f"  · L1 not yet certified: {e}")

    # a LIVE demonstration, not a number: the substrate answering a real question
    # from its own canon, so the new user SEES retrieval work (best-effort — the demo
    # never decides the climb; it reads cwd's index, the common in-repo case).
    print("\n[try it] the substrate answering a question from its own canon:")
    try:
        cmd_query(["how do I prove a task is done"])
    except (SystemExit, OSError) as e:
        print(f"  · query demo skipped ({e}); run `socom query \"...\"` yourself.")

    # Wall 3: the orchestration runtime verdict, surfaced now (not at first --exec).
    print("\n[runtime] orchestration readiness…")
    for ln in _runtime_preflight(root):
        print(ln)

    # the payoff: a `value` readout reflecting only what the rungs really produced.
    print("\n[value] what the substrate gives you right now:")
    cmd_value([str(root)])
    state, nxt = adoption_rung(root)
    print(f"\n  {adoption_bar(state)}\n  rung: {state}\n  next: {nxt}")
