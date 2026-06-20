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
from socom.claims import cmd_claim, cmd_release
from socom.context import cmd_context
from socom.gate import cmd_breach, cmd_gate
from socom.handoff import cmd_handoff, cmd_prompt
from socom.install import cmd_install, cmd_uninstall
from socom.ledger import cmd_contract
from socom.lesson import cmd_introspect, cmd_lesson
from socom.lifecycle import cmd_adopt, cmd_compile, cmd_doctor, cmd_forge, cmd_greet, cmd_init, cmd_precond, cmd_statusline
from socom.retrieval import cmd_baseline, cmd_cycle, cmd_embed, cmd_eval, cmd_hydrate, cmd_index, cmd_query

# === BODY ===

# ── main ─────────────────────────────────────────────────────────────────

COMMANDS = {"init": cmd_init, "compile": cmd_compile, "doctor": cmd_doctor,
            "gate": cmd_gate, "hydrate": cmd_hydrate, "index": cmd_index,
            "claim": cmd_claim, "release": cmd_release, "handoff": cmd_handoff,
            "prompt": cmd_prompt, "breach": cmd_breach,
            "baseline": cmd_baseline, "greet": cmd_greet,
            "statusline": cmd_statusline,
            "embed": cmd_embed, "query": cmd_query, "eval": cmd_eval,
            "cycle": cmd_cycle, "lesson": cmd_lesson, "precond": cmd_precond,
            "introspect": cmd_introspect, "contract": cmd_contract,
            "context": cmd_context,
            "forge": cmd_forge, "adopt": cmd_adopt, "install": cmd_install,
            "uninstall": cmd_uninstall}


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        sys.exit(__doc__)
    fn = COMMANDS.get(sys.argv[1])
    if fn is None:
        sys.exit(f"socom: unknown command '{sys.argv[1]}'\n{__doc__}")
    fn(sys.argv[2:])
