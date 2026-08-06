"""socom core — shared constants + primitives. Assembled into bin/socom by build.py."""
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

# === BODY ===

try:
    import yaml
except ImportError:
    sys.exit("socom: needs PyYAML — `pip install -r requirements.txt` "
             "(or `pip install pyyaml`). See README 'Requirements'.")


SOCOM_VERSION = "0.1"


SOCOM_DIR = ".socom"  # the substrate root under any repo — single source of truth


HOOKS_DIR = ".githooks"  # core.hooksPath target — single source for every wire/read site


CANON_FILES = ["constitution.xml", "roles.xml", "gates.xml", "session.xml",
               "doctrine.xml", "forge.xml", "residuality.xml",
               "commit-protocol.xml"]


def _find_tool_root():
    """The socom checkout — the dir that ships canon/ + schemas/. Walk UP from this
    file's location until both are found, so TOOL_ROOT is correct whether this code
    runs as the assembled bin/socom (…/bin/socom → …/) OR as a src/socom/ module
    (…/src/socom/core.py → …/) — the latter is what lets the modules be imported
    and unit-tested in isolation. Falls back to parent.parent (the old assumption)
    if neither marker is found, so a relocated single file still resolves."""
    here = Path(__file__).resolve()
    for d in here.parents:
        if (d / "canon").is_dir() and (d / "schemas").is_dir():
            return d
    return here.parent.parent


TOOL_ROOT = _find_tool_root()  # the socom checkout (ships canon/ + schemas/)


# Shipped resources (canon/*, schemas/*) so the DISTRIBUTED bin/socom is a single
# self-contained file that works with NO clone. build.py replaces this empty
# literal with the embedded contents; from source it stays empty and resource()
# falls back to reading the checkout (TOOL_ROOT). Keep the marker — build.py keys
# on it.
RESOURCES = {}  # @EMBED@


def resource(relpath: str) -> str:
    """Text of a shipped resource (e.g. 'schemas/context.xml', 'canon/roles.xml').
    Prefers the embedded copy (distributed single file); falls back to the checkout
    on disk (running from source). Degrades LOUDLY (R6) if neither has it — a clean
    message, never a raw FileNotFoundError traceback."""
    if relpath in RESOURCES:
        return RESOURCES[relpath]
    p = TOOL_ROOT / relpath
    if p.is_file():
        return p.read_text()
    raise SystemExit(
        f"socom: resource {relpath!r} not found — this build is neither embedded "
        "nor running from a socom checkout (canon/ + schemas/). Reinstall from a "
        "release artifact, or run from a clone.")


# ── helpers ──────────────────────────────────────────────────────────────

def repo_root(start: Path | None = None) -> Path:
    p = (start or Path.cwd()).resolve()
    for cand in [p, *p.parents]:
        if (cand / ".git").exists() or (cand / "socom.yaml").exists():
            return cand
    return p


def _now_iso() -> str:
    """UTC now as a second-precision ISO stamp — the substrate's one time shape."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def log_breach(root: Path, gate: str, detail: str):
    """Append one amber breach to .socom/gates/breaches.log (ts, source, detail).
    A shared substrate primitive: gates log here (HR3), and so does the monarch
    run-reaper — kept in core so both can write without a gate<->monarch import
    cycle (§least-common-mechanism). Telemetry about the system, never an author."""
    log = root / SOCOM_DIR / "gates" / "breaches.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a") as f:
        f.write(f"{_now_iso()}\t{gate}\t{detail}\n")


def md_text(el) -> str:
    """Dedented text content of an <md> child (or the element itself)."""
    node = el.find("md") if el.find("md") is not None else el
    return textwrap.dedent(node.text or "").strip()


def canonical_hash(root: Path) -> str:
    h = hashlib.sha256()
    for name in CANON_FILES:
        f = root / SOCOM_DIR / "canon" / name
        if f.exists():
            h.update(f.read_bytes())
    cfg = root / "socom.yaml"
    if cfg.exists():
        h.update(cfg.read_bytes())
    return h.hexdigest()[:12]


def load_cfg(root: Path) -> dict:
    cfg = root / "socom.yaml"
    if not cfg.exists():
        sys.exit(f"socom: no socom.yaml in {root} — run `socom init` first")
    return yaml.safe_load(cfg.read_text()) or {}


def parse_canon(root: Path, name: str):
    f = root / SOCOM_DIR / "canon" / name
    if not f.exists():
        sys.exit(f"socom: missing canonical file {f} — run `socom init`")
    return ET.parse(f).getroot()


def is_generated(path: Path) -> bool:
    """True iff socom wrote this file — PROVED by the header, never by the path."""
    try:
        return path.is_file() and "socom:generated" in path.read_text(errors="ignore")[:200]
    except OSError:
        return False


def sidecar_for(path: Path) -> Path:
    """The socom-owned neighbour of a view socom is not allowed to write:
    CLAUDE.md -> CLAUDE.socom.md. One naming rule, one place."""
    return path.with_name(f"{path.stem}.socom{path.suffix}")


CLAUDE_SIDECAR = "CLAUDE.socom.md"  # socom's half when CLAUDE.md is the user's


def compiled_view(root: Path) -> tuple[Path | None, str]:
    """Where socom's compiled instructions actually live, and how they are reached:

      (CLAUDE.md,      "owned")     socom generated CLAUDE.md itself
      (sidecar,        "imported")  CLAUDE.md is the user's and imports the sidecar
      (sidecar,        "orphan")    the sidecar exists but nothing loads it
      (None,           "none")      nothing compiled yet

    Every other surface (rung, doctor, drift gates) reads THIS, so there is one
    answer to "which file is socom's" and it is proved by the header, not a path.
    NOTE the honest limit of "imported": socom checks that the import LINE is
    present. It cannot execute the agent runtime, so it never claims the file was
    loaded — only that the user joined them.
    """
    claude = root / "CLAUDE.md"
    if is_generated(claude):
        return (claude, "owned")
    side = root / CLAUDE_SIDECAR
    if is_generated(side):
        try:
            txt = claude.read_text(errors="ignore") if claude.exists() else ""
        except OSError:
            txt = ""
        hit = re.search(rf"@\.?/?{re.escape(CLAUDE_SIDECAR)}", txt)
        return (side, "imported" if hit else "orphan")
    return (None, "none")


def write_generated(path: Path, body: str, hash_: str, comment=("<!--", "-->"),
                    force: bool = False, sidecar: bool = False,
                    import_line: str | None = None):
    """Write a compiled view. Returns the path actually written, or None.

    HR2: never clobber a file we didn't generate. Adoption is explicit. But a
    refusal that offers only `--force` makes destroying the user's file the ONLY
    way forward, and the caller then goes on printing an instruction it just
    refused (DEF-HANDWRITTEN-CLAUDE-MD-WEDGES-THE-LADDER-01). With sidecar=True
    the refusal keeps HR2 AND leaves an exit: socom's half lands beside the file
    it will not touch, and the user joins them with one line socom does not write.
    """
    if path.exists() and not is_generated(path) and not force:
        if not sidecar:
            print(f"  REFUSED {path}: exists and is not socom-generated "
                  f"(hand-written?). Re-run with --force to adopt it.", file=sys.stderr)
            return None
        side = sidecar_for(path)
        write_generated(side, body, hash_, comment, force=True)
        print(f"  KEPT {path.name} — it is yours and socom did not touch it. "
              f"socom's half is {side.name}.")
        if import_line:
            print(f"         to load it, add this ONE line to {path.name}: "
                  f"{import_line}")
        print(f"         (`socom compile --force` would instead OVERWRITE "
              f"{path.name} — it still works and still destroys it.)")
        return side
    path.parent.mkdir(parents=True, exist_ok=True)
    header = (f"{comment[0]} socom:generated v={SOCOM_VERSION} source={hash_} "
              f"— do not edit; edit .socom/ + socom.yaml, then `socom compile` {comment[1]}\n")
    path.write_text(header + body)
    print(f"  wrote {path}")
    return path

