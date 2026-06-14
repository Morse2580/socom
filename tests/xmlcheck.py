#!/usr/bin/env python3
"""socom substrate XML well-formedness gate.

Every hand-authored XML artifact in the substrate must parse. Handoffs and
promises are hand-filled prose-heavy XML — a raw `<` in a [done] block silently
breaks them, and (until this script) no gate caught it: `socom index` skips
malformed files, and only `medium` parsed canon/schemas. This globs the REAL
repo (run from the check's CWD, not smoke's throwaway), so a broken handoff or
promise fails pre-commit AND CI (it is wired into both medium and full).
"""
import glob
import sys
import xml.etree.ElementTree as ET

PATTERNS = [
    "canon/*.xml", "schemas/*.xml",
    ".socom/canon/*.xml", ".socom/handoffs/*.xml", ".socom/promises/*.xml",
]

bad = []
n = 0
for pat in PATTERNS:
    for f in sorted(glob.glob(pat)):
        n += 1
        try:
            ET.parse(f)
        except ET.ParseError as e:
            bad.append((f, e))

if bad:
    for f, e in bad:
        print(f"  MALFORMED {f}: {e}", file=sys.stderr)
    sys.exit(f"xmlcheck: {len(bad)} malformed of {n} substrate XML file(s)")
print(f"xmlcheck: {n} substrate XML files well-formed")
