#!/usr/bin/env python3
"""socom unit tests — direct assertions on the PURE core of bin/socom.

smoke.sh is black-box at the command level; this pins the return values of the
compute helpers (BM25/overlap scoring, hashing, TTL, lifecycle filter, parse
regexes, template well-formedness) so the next refactor (utility layer,
hotspot decomposition) rides on a real net. stdlib only — matches the binary.

The CLI is a single file named `socom` (no .py); load it by path. Its
`if __name__ == "__main__"` guard (bin/socom) means importing runs no command.
"""
import importlib.util
import re
import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from importlib.machinery import SourceFileLoader
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# bin/socom has no .py extension, so name an explicit source loader.
_loader = SourceFileLoader("socom_cli", str(REPO / "bin" / "socom"))
_spec = importlib.util.spec_from_loader("socom_cli", _loader)
socom = importlib.util.module_from_spec(_spec)
_loader.exec_module(socom)

# ── tiny harness (mirrors smoke.sh's ok/bad aesthetic) ──────────────────────
_PASS = 0
_FAIL = 0


def check(desc, cond):
    global _PASS, _FAIL
    if cond:
        _PASS += 1
        print(f"  ✓ {desc}")
    else:
        _FAIL += 1
        print(f"  ✗ {desc}")


def eq(desc, got, want):
    check(f"{desc} (got {got!r}, want {want!r})", got == want)


# ── tokenize ────────────────────────────────────────────────────────────────
eq("tokenize lowercases + splits on non-word",
   socom.tokenize("Hello, World! 123_x"), ["hello", "world", "123_x"])
eq("tokenize empty -> []", socom.tokenize(""), [])

# ── l0_score (keyword overlap; the floor) ────────────────────────────────────
_chunks = [
    {"id": "a", "text": "residuality gate saltzer", "metadata": {}},
    {"id": "b", "text": "lesson cycle hotspot", "metadata": {}},
    {"id": "c", "text": "residuality gate one way door", "metadata": {}},
]
_top = socom.l0_score("residuality gate", _chunks, k=2)
check("l0_score ranks overlapping chunks first", set(_top) == {"a", "c"})
eq("l0_score honours k", len(socom.l0_score("residuality", _chunks, k=1)), 1)

# ── l1_score (BM25) ──────────────────────────────────────────────────────────
_index = {
    "idf": {"residuality": 1.2, "gate": 0.8, "lesson": 1.5},
    "avgdl": 4.0,
    "docs": {
        "a": {"len": 3, "tf": {"residuality": 1, "gate": 1, "saltzer": 1}},
        "b": {"len": 3, "tf": {"lesson": 1, "cycle": 1, "hotspot": 1}},
    },
}
eq("l1_score returns the matching doc",
   socom.l1_score("residuality", _index, k=5), ["a"])
eq("l1_score non-match term -> []",
   socom.l1_score("nonexistentterm", _index, k=5), [])
eq("l1_score allowed_ids filters out the only match",
   socom.l1_score("residuality", _index, k=5, allowed_ids={"b"}), [])

# ── live_chunk_ids (lifecycle filter) ────────────────────────────────────────
_life = [
    {"id": "keep", "metadata": {"state": "active"}},
    {"id": "drop", "metadata": {"state": "retired"}},
    {"id": "nostate", "metadata": {}},
]
check("live_chunk_ids excludes retired, keeps active + stateless",
      socom.live_chunk_ids(_life) == {"keep", "nostate"})

# ── canonical_hash (stable 12-hex over canon + socom.yaml) ────────────────────
_h1 = socom.canonical_hash(REPO)
_h2 = socom.canonical_hash(REPO)
check("canonical_hash is 12 hex chars",
      len(_h1) == 12 and re.fullmatch(r"[0-9a-f]{12}", _h1) is not None)
eq("canonical_hash is deterministic", _h1, _h2)

# ── claim_expired (TTL boundary; unparseable = dead) ─────────────────────────
with tempfile.TemporaryDirectory() as _td:
    fresh = Path(_td) / "fresh.claim"
    fresh.write_text(datetime.now(timezone.utc).isoformat() + "\tholder")
    check("claim_expired False for a fresh claim", socom.claim_expired(fresh) is False)

    old = Path(_td) / "old.claim"
    old.write_text((datetime.now(timezone.utc) - timedelta(hours=99)).isoformat() + "\th")
    check("claim_expired True past the TTL", socom.claim_expired(old) is True)

    junk = Path(_td) / "junk.claim"
    junk.write_text("not-a-timestamp")
    check("claim_expired True for an unparseable claim", socom.claim_expired(junk) is True)

# ── md_text (dedent + strip an <md> child) ───────────────────────────────────
_el = ET.fromstring("<principle><md>\n    hello\n    world\n  </md></principle>")
eq("md_text dedents and strips", socom.md_text(_el), "hello\nworld")

# ── COMMIT_RX (the structured-commit subject contract) ───────────────────────
check("COMMIT_RX accepts type(scope): desc",
      socom.COMMIT_RX.match("feat(cli): add a thing") is not None)
check("COMMIT_RX accepts dotted/hyphen scope",
      socom.COMMIT_RX.match("fix(a.b-c): y") is not None)
check("COMMIT_RX rejects missing scope",
      socom.COMMIT_RX.match("feat: no scope") is None)
check("COMMIT_RX rejects unknown type",
      socom.COMMIT_RX.match("wibble(x): y") is None)

# ── SECRET_RX (HR6 redaction boundary) ───────────────────────────────────────
check("SECRET_RX flags an AWS-key shape",
      socom.SECRET_RX.search("AKIA" + "A" * 16) is not None)
check("SECRET_RX flags assignment-style secrets",
      socom.SECRET_RX.search("password: hunter2hunter2") is not None)
check("SECRET_RX leaves ordinary prose alone",
      socom.SECRET_RX.search("the quick brown fox jumps") is None)

# ── lesson parse helpers ─────────────────────────────────────────────────────
eq("_lesson_attr extracts an attribute",
   socom._lesson_attr('<lesson domain="cli" state="provisional">', "domain"), "cli")
eq("_lesson_attr missing attr -> ''",
   socom._lesson_attr("<lesson/>", "domain"), "")
eq("_lesson_statement collapses + extracts",
   socom._lesson_statement("<statement>  a\n  b  </statement>"), "a b")

# ── templates produce well-formed XML carrying the id ────────────────────────
_lt = socom._lesson_template("L-x", "cli", "p1", "C-1", 2, 3)
_lp = ET.fromstring(_lt)
check("_lesson_template is well-formed XML with the id",
      _lp.get("id") == "L-x" and _lp.get("domain") == "cli")
_at = socom._assertion_lesson_template("L-y", "cli", "A-1", "H-1", "cmd", "0")
check("_assertion_lesson_template is well-formed XML with the id",
      ET.fromstring(_at).get("id") == "L-y")

# ── _on_path (PATH membership) ───────────────────────────────────────────────
import os as _os
_saved = _os.environ.get("PATH", "")
try:
    with tempfile.TemporaryDirectory() as _pd:
        _os.environ["PATH"] = _pd + _os.pathsep + "/usr/bin"
        check("_on_path True when dir is on PATH", socom._on_path(Path(_pd)) is True)
        check("_on_path False when dir absent", socom._on_path(Path("/no/such/dir/x")) is False)
finally:
    _os.environ["PATH"] = _saved

# ── summary ──────────────────────────────────────────────────────────────────
print(f"unit: {_PASS} passed, {_FAIL} failed")
raise SystemExit(1 if _FAIL else 0)
