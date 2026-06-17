#!/usr/bin/env python3
"""socom run-ledger schema gate.

The run ledger (.socom/ledger/runs.jsonl) is the #6f measurement spine: one
JSONL row per promise execution, rolled up by `socom cycle` into pass@1/pass@k.
Until this script NOTHING validated its schema — xmlcheck is XML-only, and
`socom cycle` only catches JSON-decode errors. A row that is valid JSON but
missing `verdict`, or carrying `gate_band:"purple"`, sailed through every gate
and silently mis-scored the cycle (one bad row REDs the eval gate). This asserts
each line parses, carries the required keys, and respects the enum/int contract.

Single source of truth: the field contract is PARSED from schemas/ledger.xml
(the <field name= type= required= values=> elements) — not hardcoded here — so
the schema lives in exactly one place (§least-common-mechanism / open-design).

Posture: absent ledger = PASS (nothing written yet is not corruption — the file
is created lazily on first record); a malformed/invalid row = FAIL. Fail-open on
absence, fail-closed on corruption. Wired into medium + full + CI.

Paths: the SCHEMA resolves relative to this script (always the canonical
schemas/ledger.xml), so it is found even from a throwaway CWD; the LEDGER is
CWD-relative (like xmlcheck globs the real repo from the check's CWD) so
medium/full run from repo root validate the real ledger. An explicit path arg
overrides the default (used by the smoke harness to point at fixture files).
"""
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SCHEMA = Path(__file__).resolve().parent.parent / "schemas" / "ledger.xml"
LEDGER = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".socom/ledger/runs.jsonl")


def load_field_contract(schema_path):
    """Parse schemas/ledger.xml -> (required_keys, enums, int_keys). The <field>
    elements ARE the contract; this keeps the schema single-sourced."""
    fields = ET.parse(schema_path).getroot().find("fields")
    required, enums, ints = [], {}, []
    for f in fields.findall("field"):
        name = f.get("name")
        if f.get("required") == "true":
            required.append(name)
        if f.get("type") == "enum" and f.get("values"):
            enums[name] = set(f.get("values").split("|"))
        if f.get("type") == "int":
            ints.append(name)
    return required, enums, ints


def check_row(row, required, enums, ints):
    """Return a list of violation strings for one parsed JSONL row (empty = ok)."""
    bad = []
    for key in required:
        if key not in row:
            bad.append(f"missing required key {key!r}")
    for key, allowed in enums.items():
        if key in row and row[key] not in allowed:
            bad.append(f"{key}={row[key]!r} not in {sorted(allowed)}")
    for key in ints:
        # bool is a subclass of int in Python — exclude it: a JSON true/false
        # in an int field is a schema violation, not a valid count/code.
        if key in row and (not isinstance(row[key], int) or isinstance(row[key], bool)):
            bad.append(f"{key}={row[key]!r} is not an int")
    return bad


def main():
    if not LEDGER.exists():
        print(f"ledgercheck: no ledger at {LEDGER} — "
              "nothing to validate (created lazily on first record).")
        return 0

    required, enums, ints = load_field_contract(SCHEMA)
    bad = []
    n = 0
    for i, ln in enumerate(LEDGER.read_text().splitlines(), 1):
        ln = ln.strip()
        if not ln:
            continue
        n += 1
        try:
            row = json.loads(ln)
        except json.JSONDecodeError as e:
            bad.append((i, f"malformed JSON: {e}"))
            continue
        if not isinstance(row, dict):
            bad.append((i, f"row is not a JSON object: {ln[:60]!r}"))
            continue
        for v in check_row(row, required, enums, ints):
            bad.append((i, v))

    if bad:
        for i, v in bad:
            print(f"  line {i}: {v}", file=sys.stderr)
        sys.exit(f"ledgercheck: {len(bad)} violation(s) across {n} ledger row(s)")
    print(f"ledgercheck: {n} ledger row(s) valid against schemas/ledger.xml")
    return 0


if __name__ == "__main__":
    sys.exit(main())
