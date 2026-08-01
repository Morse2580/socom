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
from socom.install import cmd_install, cmd_quickstart, cmd_uninstall
from socom.ledger import cmd_contract
from socom.lesson import cmd_introspect, cmd_lesson
from socom.lifecycle import cmd_adopt, cmd_compile, cmd_doctor, cmd_forge, cmd_greet, cmd_init, cmd_precond, cmd_statusline
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
            "install": cmd_install, "uninstall": cmd_uninstall}


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        sys.exit(__doc__)
    fn = COMMANDS.get(sys.argv[1])
    if fn is None:
        sys.exit(f"socom: unknown command '{sys.argv[1]}'\n{__doc__}")
    fn(sys.argv[2:])
