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


# The docstring of the generated binary. Narrow enough that no unrelated file at
# ~/.local/bin/socom matches, so `uninstall` can recognise a COPIED install
# without needing it to be a symlink back to this particular file.
_SOCOM_MARK = "socom — substrate for orchestrated"


def _is_socom_binary(p: Path) -> bool:
    try:
        return _SOCOM_MARK in p.read_text(errors="ignore")[:200]
    except OSError:
        return False


def _is_dev_checkout(src: Path) -> bool:
    """True when the running file is `<root>/bin/socom` of a socom SOURCE tree.

    This is the one place a symlink is right: the maintainer edits `src/socom/`,
    runs `build.py`, and wants `socom` on PATH to follow the checkout with no
    reinstall. Everywhere else — a `curl`'d single file, in /tmp or in the
    user's own repo — the install must not depend on where that file was sitting
    when it ran, so it is copied.
    """
    return src.parent.name == "bin" and (src.parent.parent / "src" / "socom").is_dir()


def _enclosing_git_root(p: Path) -> Path | None:
    """The git work tree containing `p`, or None. Used only to tell the user their
    downloaded file is sitting in a repo and can now be deleted."""
    try:
        r = subprocess.run(["git", "-C", str(p.parent), "rev-parse", "--show-toplevel"],
                           capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return None
    out = r.stdout.strip()
    return Path(out) if r.returncode == 0 and out else None


def _report_path(dst_dir: Path) -> None:
    if _on_path(dst_dir):
        print(f"socom install: {dst_dir} is on PATH — `socom` is ready.")
    else:
        print(f"socom install: NOTE {dst_dir} is not on PATH. Add it:")
        print(f'  export PATH="{dst_dir}:$PATH"')


def cmd_install(args):
    """Put socom on PATH. A socom development checkout is SYMLINKED; every other
    location is COPIED, so the install depends on nothing outside the target dir.

    Why it copies (DEF-INSTALLED-BINARY-LANDS-INSIDE-THE-ADOPTED-REPO-01): the
    documented path is `curl` the single file → `chmod +x` → `./socom install`,
    and users run it from inside the repo they mean to adopt. Symlinking there
    made `~/.local/bin/socom` resolve INTO that repo — so `git add -A` staged a
    ~430 KB executable into the adopter's history, and deleting or moving that
    repo broke socom for the whole machine. Observed twice on real repos
    (2026-08-05 following PILOT.md, 2026-08-07 NOT following it — which is why
    rewording the doc was never the fix). A copy severs the dependency: the
    downloaded file becomes disposable and socom says so.

    The symlink survives for `<root>/bin/socom` of a source tree only, where
    following the checkout is the point.
    """
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
    link = _is_dev_checkout(src)
    # Only a SYMLINK can dangle, so this warning is now scoped to the link path.
    # Installing a copy out of /tmp is fine and is the on-ramp working: the temp
    # file can be cleaned up the moment the copy lands (R6).
    if link and str(src).startswith(str(Path(tempfile.gettempdir()).resolve())):
        print(f"socom install: WARNING — installing from a temp location ({src}). "
              "Move socom somewhere permanent (e.g. ~/.local/bin) and install from "
              "there, or the symlink will break when the temp file is cleaned up.",
              file=sys.stderr)
    dst_dir.mkdir(parents=True, exist_ok=True)
    if dst == src:
        # `curl`'d straight into the target dir and ran it from there. Copying a
        # file onto itself truncates it; there is also nothing to do.
        print(f"socom install: already at {dst} — nothing to copy.")
        _report_path(dst_dir)
        return
    exists = dst.is_symlink() or dst.exists()
    if link:
        already = dst.is_symlink() and dst.resolve() == src
    else:
        already = (dst.is_file() and not dst.is_symlink()
                   and dst.read_bytes() == src.read_bytes())
    if already and not force:
        print(f"socom install: already installed → {dst}")
    elif exists and not force:
        tgt = dst.resolve() if dst.is_symlink() else "(regular file)"
        sys.exit(f"socom install: {dst} already exists ({tgt}), not this "
                 f"{'checkout' if link else 'build'}. Re-run with --force to replace.")
    else:
        if exists:
            dst.unlink()
        if link:
            dst.symlink_to(src)
            print(f"socom install: linked {dst} → {src}  (source checkout — it "
                  f"follows your build)")
        else:
            shutil.copyfile(src, dst)
            dst.chmod(0o755)
            print(f"socom install: copied {src} → {dst}")
    if not link:
        root = _enclosing_git_root(src)
        if root is not None:
            print(f"socom install: NOTE the file you ran is inside a git repo "
                  f"({root}). socom COPIED itself to {dst} and nothing on PATH "
                  f"points back — so that download is now disposable:")
            print(f"  rm {src}")
    _report_path(dst_dir)


def cmd_uninstall(args):
    dst_dir = (Path(args[0]).expanduser() if args else DEFAULT_BIN_DIR)
    dst = dst_dir / "socom"
    src = Path(__file__).resolve()
    if not dst.is_symlink() and not dst.exists():
        print(f"socom uninstall: nothing at {dst}")
        return
    # Two shapes are ours now: the dev-checkout symlink, and a copied binary.
    # Recognise the copy by its own content, not by whether it matches THIS
    # build — an older installed copy must still be removable.
    ours = ((dst.is_symlink() and dst.resolve() == src)
            or (not dst.is_symlink() and dst.is_file() and _is_socom_binary(dst)))
    if ours:
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
        sys.exit(f"socom uninstall: {dst} is neither a symlink to this checkout "
                 f"nor a socom binary — refusing to remove. Remove it manually "
                 f"if intended.")


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


def _resolve_check(command: str, root: Path):
    """Resolve the executable a detected check command would actually run.

    Returns `(binary, resolved_path_or_None)`.

    Detection and resolution are SEPARATE AXES and `_detect_checks` only reads the
    first: a `Cargo.toml` is evidence about the PROJECT, never about whether `cargo`
    exists on THIS machine. A binding can be exactly right about the repo and
    unrunnable where it runs — measured three times, most recently by a non-author on
    a Rust repo whose toolchain lived in an unactivated local `bin/`
    (`bench/exposure/2026-08-11-buzz-engineer-report.md`). Reporting the first as
    though the second had been checked is a §verify-never-claim violation, which is
    constitution rank 1; see `decisions/0008`.

    This is the guard `spawn --exec` already applies (`spawn.py`, `shutil.which` then
    refuse) — applied here for consistency, not invented. It answers "does this
    resolve", NOT "does this pass": executing an adopter's test suite during setup is
    not socom's to do, and a resolvable command that fails is the gate working."""
    parts = shlex.split(command) if command else []
    if not parts:
        return command, None
    binary = parts[0]
    hit = shutil.which(binary)
    if hit is None and os.sep in binary and not os.path.isabs(binary):
        # a repo-relative script (`tests/smoke.sh`): which() resolves paths against
        # CWD, and the gate will run it from the repo root instead.
        cand = root / binary
        if cand.is_file() and os.access(cand, os.X_OK):
            hit = str(cand)
    return binary, hit


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
        # BIND either way — a command that is right about the repo is worth binding
        # even where it cannot run — but CLAIM only what was resolved (0008).
        binary, resolved = _resolve_check(detected, root)
        if resolved:
            print(f"  ✓ bound checks.fast/medium/full → {detected!r} — gates now run YOUR tests")
        else:
            print(f"  ! bound checks.fast/medium/full → {detected!r} — but {binary!r} is NOT "
                  f"on PATH here, so socom has NOT verified this runs.")
            print(f"    Detection read your REPO (it found the project layout); it cannot read "
                  f"your MACHINE. Both can be true: right command, missing toolchain.")
            print(f"    Until {binary!r} resolves, every gate fails with rc=127 — that is this "
                  f"binding, not your code.")
            print(f"    Fix either side: install or activate {binary!r}, or edit checks.fast in "
                  f"socom.yaml and re-run `socom compile`.")
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
