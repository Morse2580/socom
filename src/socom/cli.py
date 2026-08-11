"""socom cli — command dispatch. Assembled into bin/socom by build.py."""
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
from socom.blackboard import cmd_attest, cmd_claim, cmd_findings, cmd_release, cmd_resolve
from socom.mcp import cmd_mcp
from socom.context import cmd_context
from socom.gate import cmd_breach, cmd_gate
from socom.handoff import cmd_handoff, cmd_prompt
from socom.install import DEFAULT_BIN_DIR, cmd_install, cmd_quickstart, cmd_uninstall, cmd_version
from socom.ledger import cmd_contract
from socom.lesson import cmd_introspect, cmd_lesson
from socom.lifecycle import cmd_adopt, cmd_compile, cmd_doctor, cmd_forge, cmd_greet, cmd_init, cmd_precond, cmd_statusline, cmd_unadopt
from socom.monarch import cmd_meter, cmd_monarch, cmd_trace
from socom.retrieval import cmd_baseline, cmd_cycle, cmd_embed, cmd_eval, cmd_hydrate, cmd_index, cmd_judge, cmd_query
from socom.spawn import cmd_spawn
from socom.value import cmd_value

# === BODY ===

# ── main ─────────────────────────────────────────────────────────────────

COMMANDS = {"init": cmd_init, "compile": cmd_compile, "doctor": cmd_doctor,
            "gate": cmd_gate, "hydrate": cmd_hydrate, "index": cmd_index,
            "claim": cmd_claim, "release": cmd_release, "handoff": cmd_handoff,
            "attest": cmd_attest, "findings": cmd_findings,
            "resolve": cmd_resolve, "mcp": cmd_mcp,
            "prompt": cmd_prompt, "breach": cmd_breach,
            "baseline": cmd_baseline, "greet": cmd_greet,
            "statusline": cmd_statusline,
            "embed": cmd_embed, "query": cmd_query, "eval": cmd_eval,
            "cycle": cmd_cycle, "judge": cmd_judge,
            "lesson": cmd_lesson, "precond": cmd_precond,
            "introspect": cmd_introspect, "contract": cmd_contract,
            "context": cmd_context, "value": cmd_value, "spawn": cmd_spawn,
            "monarch": cmd_monarch, "trace": cmd_trace, "meter": cmd_meter,
            "forge": cmd_forge, "adopt": cmd_adopt, "quickstart": cmd_quickstart,
            "unadopt": cmd_unadopt,
            "install": cmd_install, "uninstall": cmd_uninstall,
            "version": cmd_version}


# ── help: explain, never act ─────────────────────────────────────────────
# `<cmd> --help` is the first thing a stranger types at an unfamiliar
# subcommand. No cmd_* handled it, so the flag fell through as a positional:
# `claim --help` took a real lease NAMED "--help", `compile --help` planted 33
# files, `release --help` released the bogus lease. Two commands had already
# patched their own instance locally (install, mcp) — which is exactly why the
# class survived: a per-command guard is one every future cmd_* must remember.
# The guard lives at the dispatch instead, so no cmd_* can reintroduce it.
HELP_FLAGS = ("-h", "--help")

# The two commands whose detail a one-line table entry cannot carry. Extra
# lines only — the description itself is still derived, never spelled twice.
USAGE_EXTRA = {
    "install": f"usage: socom install [<bin-dir>] [--force]  (default: {DEFAULT_BIN_DIR})\n"
               "--force overwrites an existing NON-socom file at the target.\n"
               "COPIES the file you ran, so the download is disposable and nothing on\n"
               "PATH depends on where you left it. A socom SOURCE CHECKOUT\n"
               "(<root>/bin/socom) is symlinked instead, where following the\n"
               "checkout is the point.",
    "mcp": 'Register in .mcp.json:\n  {"mcpServers": {"socom": '
           '{"command": "<path>/bin/socom", "args": ["mcp"]}}}',
}


def root_doc():
    """The top-level command list. bin/socom is one flat namespace, so there it
    is this module's __doc__; under src/ the docstring lives on the package."""
    pkg = sys.modules.get("socom")
    return (pkg.__doc__ if pkg is not None else None) or __doc__ or ""


def subcommand_usage(name, doc=None):
    """One command's entry, lifted out of the single `Commands:` table in the
    root docstring. Derived so help cannot drift from the command list — the
    table is indented two spaces per command, deeper for continuation lines.
    Returns None when `name` has no entry (tests/unit.py asserts none do)."""
    body = None
    for line in (root_doc() if doc is None else doc).splitlines():
        entry = line.strip() and line.startswith("  ") and not line.startswith("   ")
        if body is not None:
            if entry or not line.startswith("   "):
                break
            body.append(line.strip())
        elif entry:
            head = line[2:].split(" ", 1)
            if head[0] == name:
                body = [head[1].strip()] if len(head) > 1 else []
    return "\n".join(body) if body else None


def print_usage(name):
    """Explain `name` on stdout and write NOTHING else — no lease, no file, no
    git config, no ref. The whole point of the row this closes."""
    print(f"socom {name}\n")
    print(textwrap.indent(subcommand_usage(name) or "(no entry in the command "
                          "table — run `socom --help`)", "  "))
    if name in USAGE_EXTRA:
        print(f"\n{USAGE_EXTRA[name]}")
    print("\n`--help` explains; it never acts — nothing was written.\n"
          "Run `socom --help` for the full command list.")


if __name__ == "__main__":
    if sys.argv[1:2] and sys.argv[1] in HELP_FLAGS:
        print(root_doc().strip())          # asked for: stdout, exit 0
        raise SystemExit(0)
    if len(sys.argv) < 2:
        sys.exit(root_doc())               # no command given: a usage ERROR
    fn = COMMANDS.get(sys.argv[1])
    if fn is None:
        sys.exit(f"socom: unknown command '{sys.argv[1]}'\n{root_doc()}")
    if any(a in HELP_FLAGS for a in sys.argv[2:]):
        print_usage(sys.argv[1])
        raise SystemExit(0)
    fn(sys.argv[2:])
