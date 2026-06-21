"""socom handoff — handoff + next-session prompt. Assembled into bin/socom by build.py."""
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
from socom.core import SOCOM_DIR, SOCOM_VERSION, _now_iso, load_cfg, repo_root

# === BODY ===

# ── handoff + next-session prompt ───────────────────────────────────────

def cmd_handoff(args):
    """Generate a handoff skeleton from observable git state; the session
    fills judgment fields (undone/blockers/warnings) before closeout."""
    root = repo_root()
    summary = " ".join(args) or "session work"
    branch = subprocess.run(["git", "branch", "--show-current"], cwd=root,
                            capture_output=True, text=True).stdout.strip() or "detached"
    log = subprocess.run(["git", "log", "--oneline", "-10"], cwd=root,
                         capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--short"], cwd=root,
                           capture_output=True, text=True).stdout.strip()
    date = datetime.now(timezone.utc).date().isoformat()
    hid = f"H-{date}-{re.sub(r'[^a-z0-9-]', '-', branch.lower())[:40]}"
    out = root / SOCOM_DIR / "handoffs" / f"{hid}.xml"
    out.parent.mkdir(parents=True, exist_ok=True)
    commits = "\n".join(f"    <commit>{ln}</commit>" for ln in log.splitlines())
    dirty_el = (f"  <uncommitted>\n{dirty}\n  </uncommitted>\n" if dirty else "")
    out.write_text(f"""<?xml version="1.0" encoding="UTF-8"?>
<handoff socom="{SOCOM_VERSION}" id="{hid}" branch="{branch}"
         date="{_now_iso()}">
  <summary embed="true">{summary}</summary>
  <done embed="true">FILL: what was completed, with evidence refs</done>
  <undone embed="true">FILL: what remains, and why</undone>
  <recent-commits>
{commits}
  </recent-commits>
{dirty_el}  <blockers embed="true">FILL or remove</blockers>
  <warnings embed="true">FILL or remove</warnings>
  <next embed="true">FILL: ranked candidates for the next session</next>
</handoff>
""")
    print(f"socom handoff: skeleton -> {out}\n  Fill the FILL fields before "
          "closeout; the session-end gate checks freshness, the prompt builds on it."
          "\n  Context: the seat's `socom context emit` envelope (.socom/context) is "
          "what `socom context verify` gates — emit it if this session loaded "
          "context against a budget.")


# Claim-verification: every probe-able claim in the generated prompt is
# checked against the repo and annotated VERIFIED / HYPOTHESIS. Prompts
# state what was true at write time; the annotations say what still is.
def verify_claims(root: Path, text: str) -> list[str]:
    notes = []
    for path_m in set(re.findall(r"(?:^|[\s`(])((?:[\w.-]+/)+[\w.-]+\.\w{1,6})", text)):
        exists = (root / path_m).exists()
        notes.append(f"{'VERIFIED' if exists else 'HYPOTHESIS'}: path {path_m} "
                     f"{'exists' if exists else 'NOT FOUND in repo'}")
    for sha in set(re.findall(r"\b[0-9a-f]{7,12}\b", text)):
        rc = subprocess.run(["git", "cat-file", "-e", sha], cwd=root,
                            capture_output=True).returncode
        notes.append(f"{'VERIFIED' if rc == 0 else 'HYPOTHESIS'}: commit {sha}")
    return notes


def cmd_prompt(args):
    root = repo_root()
    cfg = load_cfg(root)
    handoffs = sorted((root / SOCOM_DIR / "handoffs").glob("*.xml"))
    if not handoffs:
        sys.exit("socom prompt: no handoffs — run `socom handoff <summary>` first")
    latest = handoffs[-1]
    body = latest.read_text()
    unfilled = body.count("FILL")
    claims = verify_claims(root, body)
    verified = sum(1 for c in claims if c.startswith("VERIFIED"))
    # Prompt identity: UNIQUE per session, content-addressed like a memory. The
    # source handoff (H-<date>-<branch>) gives ordering, but two sessions on the
    # same branch+day would collide on that alone — so the id also carries a short
    # CONTENT HASH (over the handoff body + the generation timestamp) plus the UTC
    # generation stamp. Same shape memories use: a hash + a unique time.
    gen_ts = _now_iso()
    phash = hashlib.sha256((body + gen_ts).encode()).hexdigest()[:12]
    pid = f"P{latest.stem[1:]}-{phash}"
    src_date_m = re.search(r'date="([^"]+)"', body)
    src_date = src_date_m.group(1) if src_date_m else "unknown"
    out = root / SOCOM_DIR / "prompts" / "next-session.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    notes = "\n".join(f"- {c}" for c in claims) or "- (no probe-able claims)"
    out.write_text(f"""<!-- socom:prompt id={pid} generated={gen_ts} source-handoff={latest.name} — regenerated each closeout, do not commit by hand -->
# Next session — {cfg.get('project', root.name)}

**Prompt-id:** `{pid}` · **Generated:** {gen_ts} · **From handoff:** `{latest.name}` (as-of {src_date})

You are resuming work on this repo's SOCOM substrate. Begin by:

1. `socom gate session-start` (drift check + orphan reaper + breach debt — NON-NEGOTIABLE)
2. Read `{latest.relative_to(root)}` end-to-end — the exit state you inherit.
3. `socom claim --scan`, then claim your domain before any work.
4. Load the session-start section of `.socom/memory/INDEX.md` and the lessons
   for your domain.
5. Non-trivial work: enter plan mode; ratify a contract before code.

## Inherited state (from {latest.name})
{"⚠ handoff has " + str(unfilled) + " unfilled FILL field(s) — treat its claims as provisional" if unfilled else "handoff was fully filled at closeout"}

## Claim verification ({verified}/{len(claims)} verified at generation time)
{notes}

Anything marked HYPOTHESIS must be re-checked before you rely on it.
""")
    print(f"socom prompt: -> {out} ({verified}/{len(claims)} claims verified"
          f"{', ' + str(unfilled) + ' FILL fields outstanding' if unfilled else ''})")
