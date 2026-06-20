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


TOOL_ROOT = Path(__file__).resolve().parent.parent  # the socom checkout


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


def write_generated(path: Path, body: str, hash_: str, comment=("<!--", "-->"),
                    force: bool = False):
    # HR2: never clobber a file we didn't generate. Adoption is explicit.
    if path.exists() and "socom:generated" not in path.read_text()[:200] and not force:
        print(f"  REFUSED {path}: exists and is not socom-generated "
              f"(hand-written?). Re-run with --force to adopt it.", file=sys.stderr)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    header = (f"{comment[0]} socom:generated v={SOCOM_VERSION} source={hash_} "
              f"— do not edit; edit .socom/ + socom.yaml, then `socom compile` {comment[1]}\n")
    path.write_text(header + body)
    print(f"  wrote {path}")

