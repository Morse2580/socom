"""socom install — self-install onto PATH. Assembled into bin/socom by build.py."""
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
    else:
        sys.exit(f"socom uninstall: {dst} is not a symlink to this checkout — "
                 f"refusing to remove. Remove it manually if intended.")
