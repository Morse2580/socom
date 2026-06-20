"""socom claims — work claims + reaping. Assembled into bin/socom by build.py."""
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
from socom.core import SOCOM_DIR, _now_iso, load_cfg, repo_root

# === BODY ===

# ── claims (R2) ──────────────────────────────────────────────────────────
# Cheap domain locks: a claim file with holder + expiry. TTL auto-expiry is
# the safety net (a dead session never wedges a domain); release is the
# intent. Cross-machine propagation comes via git push of .socom/claims/.

CLAIM_TTL_HOURS = 8


def claim_path(root: Path, domain: str) -> Path:
    return root / SOCOM_DIR / "claims" / f"{domain}.claim"


def claim_holder() -> str:
    return os.environ.get("SOCOM_SESSION", f"pid-{os.getppid()}")


def claim_expired(p: Path) -> bool:
    try:
        ts = datetime.fromisoformat(p.read_text().splitlines()[0].split("\t")[0])
    except (ValueError, IndexError):
        return True  # unparseable claim is a dead claim
    age_h = (datetime.now(timezone.utc) - ts).total_seconds() / 3600
    return age_h > CLAIM_TTL_HOURS


def cmd_claim(args):
    if not args:
        sys.exit("usage: socom claim <domain> | socom claim --scan")
    root = repo_root()
    cfg = load_cfg(root)
    cdir = root / SOCOM_DIR / "claims"
    cdir.mkdir(parents=True, exist_ok=True)
    if args[0] == "--scan":
        live = expired = 0
        for p in sorted(cdir.glob("*.claim")):
            state = "EXPIRED" if claim_expired(p) else "live"
            if state == "live":
                live += 1
            else:
                expired += 1
            print(f"  {p.stem}: {state} — {p.read_text().strip()}")
        print(f"socom claim: {live} live, {expired} expired")
        return
    domain = args[0]
    if domain not in cfg.get("domains", []):
        sys.exit(f"socom claim: '{domain}' not in socom.yaml domains "
                 f"{cfg.get('domains', [])}")
    p = claim_path(root, domain)
    if p.exists() and not claim_expired(p):
        holder = p.read_text().strip()
        if claim_holder() not in holder:
            sys.exit(f"socom claim: '{domain}' held by another session "
                     f"({holder}) — yield or wait for TTL expiry")
    ts = _now_iso()
    p.write_text(f"{ts}\t{claim_holder()}\tttl={CLAIM_TTL_HOURS}h\n")
    print(f"socom claim: acquired '{domain}' as {claim_holder()} "
          f"(expires in {CLAIM_TTL_HOURS}h)")


def cmd_release(args):
    root = repo_root()
    if not args:
        sys.exit("usage: socom release <domain>|--all")
    cdir = root / SOCOM_DIR / "claims"
    targets = sorted(cdir.glob("*.claim")) if args[0] == "--all" \
        else [claim_path(root, args[0])]
    for p in targets:
        if p.exists():
            p.unlink()
            print(f"socom release: '{p.stem}' released")


def reap_orphans(root: Path) -> list[str]:
    """R12: expired claims removed; dead worktrees pruned. Returns report lines."""
    report = []
    cdir = root / SOCOM_DIR / "claims"
    if cdir.exists():
        for p in sorted(cdir.glob("*.claim")):
            if claim_expired(p):
                p.unlink()
                report.append(f"reaped expired claim: {p.stem}")
    pr = subprocess.run(["git", "worktree", "prune", "-v"], cwd=root,
                        capture_output=True, text=True)
    report += [f"worktree: {ln}" for ln in pr.stderr.splitlines() if ln.strip()]
    return report
