"""socom value — first-run value readout. Assembled into bin/socom by build.py."""
from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import textwrap
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from socom.blackboard import BB_LEASES, bb_cfg, bb_live_leases, bb_read_local
from socom.core import SOCOM_DIR, repo_root
from socom.lifecycle import adoption_bar, adoption_rung
from socom.retrieval import _cycle_rollup

# === BODY ===

# ── value — what the substrate has already bought you ─────────────────────
# A readout, not a gate: it surfaces signals ALREADY on disk (gate catches,
# scored runs, context adherence, claims, knowledge, adoption rung) so the
# value paid for at install is legible on the first run. No new instrumentation
# and no writes — verify-never-claim: we report measured facts, we never
# fabricate a number. Exit 0 always; absent signals read "not yet measured"
# (R6: degrade loudly, never a silent zero that reads as "nothing happened").


def _fmt_tokens(n: int) -> str:
    """Compact token count: 3120 -> '3.1k', 840 -> '840'."""
    return f"{n / 1000:.1f}k" if n >= 1000 else str(n)


def _val_gate_catches(root: Path):
    """Open + resolved breaches = slips the gates stopped. (open_n, total_n)."""
    gates = root / SOCOM_DIR / "gates"
    def _count(name):
        f = gates / name
        return len([ln for ln in f.read_text().splitlines() if ln.strip()]) \
            if f.exists() else 0
    open_n = _count("breaches.log")
    total_n = open_n + _count("breaches.resolved.log")
    return open_n, total_n


def _val_runs(root: Path):
    """Scored-run rollup from the run ledger, or None if nothing measured yet.
    Skips non-scorable rows — bad JSON, or a row missing the `promise` key that
    `_cycle_rollup` groups on — the SAME way: a readout never crashes on one row
    (C1, unconditional). `socom cycle` + `ledgercheck` are the gates that fail
    loudly on a malformed ledger; `value` only reports, so it degrades."""
    ledger = root / SOCOM_DIR / "ledger" / "runs.jsonl"
    if not ledger.exists():
        return None
    rows = []
    for ln in ledger.read_text().splitlines():
        ln = ln.strip()
        if not ln:
            continue
        try:
            r = json.loads(ln)
        except json.JSONDecodeError:
            continue
        if isinstance(r, dict) and "promise" in r:
            rows.append(r)
    if not rows:
        return None
    try:
        return _cycle_rollup(rows)
    except (KeyError, TypeError):
        return None  # backstop: any future bare-key access stays a readout, not a crash


def _val_context(root: Path):
    """Context envelopes: (count, within_budget, headroom_tokens), or None."""
    cdir = root / SOCOM_DIR / "context"
    envs = sorted(cdir.glob("*.xml")) if cdir.exists() else []
    if not envs:
        return None
    count = within = headroom = 0
    for p in envs:
        try:
            r = ET.parse(p).getroot()
            budget = int(r.get("budget_tokens") or 0)
            used = int(r.get("input_tokens") or 0)
        except (ET.ParseError, ValueError):
            continue
        count += 1
        if budget and used <= budget:
            within += 1
            headroom += budget - used
    return (count, within, headroom) if count else None


def _val_claims(root: Path) -> int:
    """Live (unexpired) path leases — concurrent work the substrate serialized.
    Local shards only: `value` is a readout of signals already on disk, and must
    not reach the network to produce one."""
    return len(bb_live_leases(bb_read_local(root, BB_LEASES)))


def _val_knowledge(root: Path):
    """(retrievable chunks, memories on file)."""
    chunks = root / SOCOM_DIR / "index" / "chunks.jsonl"
    n_chunks = len([ln for ln in chunks.read_text().splitlines() if ln.strip()]) \
        if chunks.exists() else 0
    mem = root / SOCOM_DIR / "memory" / "memories"
    n_mem = len(list(mem.glob("*.md"))) if mem.exists() else 0
    return n_chunks, n_mem


def cmd_value(args):
    """Usage: socom value [path] — readout of value the substrate has delivered."""
    root = repo_root(Path(args[0]) if args else None)
    open_n, catches = _val_gate_catches(root)
    runs = _val_runs(root)
    ctx = _val_context(root)
    live_claims = _val_claims(root)
    n_chunks, n_mem = _val_knowledge(root)
    state, _ = adoption_rung(root)

    print("socom value — what the substrate has bought you")

    if catches:
        tail = f" ({open_n} still open)" if open_n else ""
        print(f"  gate catches   {catches}{tail}   slips stopped before they landed")
    else:
        print("  gate catches   none yet — no breach has been caught")

    if runs:
        s = runs["summary"]
        print(f"  runs scored    pass@1 {s['pass_at_1_rate']}%  ·  "
              f"{s['unique_promises']} promises, {s['total_runs']} runs")
    else:
        print("  runs scored    not yet measured — append runs (`socom contract "
              "verify --record`)")

    if ctx:
        count, within, headroom = ctx
        print(f"  context        {count} envelope(s), {within} within budget "
              f"({_fmt_tokens(headroom)} tokens headroom)")
    else:
        print("  context        not yet measured — emit envelopes (`socom context emit`)")

    if live_claims:
        plural = "s" if live_claims != 1 else ""
        print(f"  claims         {live_claims} live domain lock{plural} — "
              f"concurrent work serialized")
    else:
        print("  claims         none live")

    print(f"  knowledge      {n_chunks} chunks retrievable  ·  "
          f"{n_mem} memories on file")
    print(f"  adoption       {adoption_bar(state)}  ({state})")
