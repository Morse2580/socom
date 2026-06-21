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

# ── _cycle_rollup (SM-3: the pure eval rollup, extracted from cmd_cycle) ──────
# Same fixture smoke.sh seeds; expectations hand-counted there. White-box now.
_rows = [
    {"ts": "t1", "seat": "builder", "promise": "P-A", "contract": "C-A", "exit_code": 0, "duration_s": 100, "attempt": 1, "verdict": "kept"},
    {"ts": "t2", "seat": "builder", "promise": "P-B", "contract": "C-B", "exit_code": 1, "duration_s": 50, "attempt": 1, "verdict": "broken"},
    {"ts": "t3", "seat": "builder", "promise": "P-B", "contract": "C-B", "exit_code": 0, "duration_s": 80, "attempt": 2, "verdict": "kept"},
    {"ts": "t4", "seat": "reviewer", "promise": "P-C", "exit_code": 1, "duration_s": 30, "attempt": 1, "verdict": "broken"},
]
_m = socom._cycle_rollup(_rows)
_s = _m["summary"]
eq("rollup total_runs", _s["total_runs"], 4)
eq("rollup unique_promises", _s["unique_promises"], 3)
eq("rollup pass@1 (first-attempt kept)", _s["pass_at_1"], 1)
eq("rollup pass@k (any attempt kept)", _s["pass_at_k"], 2)
eq("rollup pass_rate (kept rows / rows)", _s["pass_rate"], 50.0)
eq("rollup contract_coverage", _s["contract_coverage"], 66.7)
_bs = {s["seat"]: s for s in _m["seats"]}
check("rollup builder seat 1/2 pass@1, 2/2 pass@k, 100%",
      _bs["builder"]["pass_at_1"] == 1 and _bs["builder"]["pass_at_k"] == 2
      and _bs["builder"]["pass_rate"] == 100.0)
check("rollup reviewer seat 0/1, 0/1, 0%",
      _bs["reviewer"]["pass_at_1"] == 0 and _bs["reviewer"]["pass_at_k"] == 0)
eq("rollup seats sorted by name", [s["seat"] for s in _m["seats"]], ["builder", "reviewer"])
eq("rollup hotspots worst-first by (broken, name)",
   [(h["promise"], h["broken"], h["total"]) for h in _m["hotspots"]],
   [("P-B", 1, 2), ("P-C", 1, 1)])
eq("rollup exit_code distribution", _m["exit_codes"], {"0": 2, "1": 2})
eq("rollup avg attempts-to-success", _m["attempts"]["avg_to_success"], 1.5)
eq("rollup worst (most-attempted) promise", _m["attempts"]["worst_promise"], "P-B")
eq("rollup empty rows -> 0 promises",
   socom._cycle_rollup([])["summary"]["unique_promises"], 0)

# ── contract machinery (#6: _contract_el / _contract_checks / _verify_summary) ─
_promise_xml = """<promise id="P-x" state="open">
  <contract ref="C-x" state="ratified">
    <goal>g</goal>
    <check id="1" assessor="gate:task-completion"><run>true</run><expect>passes</expect></check>
    <check id="2" assessor="reviewer"><expect>human reads the diff</expect></check>
  </contract></promise>"""
_pe = ET.fromstring(_promise_xml)
_ce = socom._contract_el(_pe)
check("_contract_el finds <contract> inside a promise", _ce is not None and _ce.get("ref") == "C-x")
_bare = ET.fromstring('<contract ref="C-y" state="ratified"><goal>g</goal></contract>')
check("_contract_el returns a bare contract unchanged", socom._contract_el(_bare) is _bare)
check("_contract_el None when absent", socom._contract_el(ET.fromstring("<promise/>")) is None)

_cks = socom._contract_checks(_ce)
eq("_contract_checks count", len(_cks), 2)
check("_contract_checks marks <run> check auto",
      _cks[0]["auto"] is True and _cks[0]["run"] == "true" and _cks[0]["assessor"] == "gate:task-completion")
check("_contract_checks marks no-run check MANUAL",
      _cks[1]["auto"] is False and _cks[1]["run"] is None and _cks[1]["assessor"] == "reviewer")

eq("_verify_summary ok when no auto fails (pass + manual)",
   socom._verify_summary([{"auto": True, "passed": True}, {"auto": False, "passed": False}]),
   {"passed": 1, "failed": 0, "manual": 1, "ok": True})
eq("_verify_summary FAILS when an auto check fails",
   socom._verify_summary([{"auto": True, "passed": True}, {"auto": True, "passed": False}]),
   {"passed": 1, "failed": 1, "manual": 0, "ok": False})
check("_verify_summary: a manual check is never counted passed",
      socom._verify_summary([{"auto": False, "passed": False}])["passed"] == 0)

# ── ledger recording (#6f: _next_attempt / _ledger_row) ───────────────────────
_rows = [
    {"promise": "P-A", "contract": "C-A", "attempt": 1},
    {"promise": "P-A", "contract": "C-A", "attempt": 2},
    {"promise": "P-B", "contract": "C-B", "attempt": 1},
]
eq("_next_attempt: first run of an unseen pair is 1",
   socom._next_attempt(_rows, "P-NEW", "C-NEW"), 1)
eq("_next_attempt: one past the highest attempt for the pair",
   socom._next_attempt(_rows, "P-A", "C-A"), 3)
eq("_next_attempt: per-(promise,contract), not global",
   socom._next_attempt(_rows, "P-B", "C-B"), 2)
eq("_next_attempt: empty ledger is attempt 1",
   socom._next_attempt([], "P-A", "C-A"), 1)

_ok = {"passed": 1, "failed": 0, "manual": 0, "ok": True}
_bad = {"passed": 0, "failed": 1, "manual": 0, "ok": False}
_row = socom._ledger_row("P-A", "builder", "C-A", _ok, 1,
                         "2026-06-15T00:00:00+00:00", 7)
eq("_ledger_row: keys are exactly the ledger wire contract",
   sorted(_row.keys()),
   ["attempt", "contract", "duration_s", "exit_code", "gate_band",
    "promise", "seat", "ts", "verdict"])
check("_ledger_row: ok summary -> verdict kept, exit_code 0",
      _row["verdict"] == "kept" and _row["exit_code"] == 0)
check("_ledger_row: carries seat/promise/contract/attempt/duration verbatim",
      _row["seat"] == "builder" and _row["promise"] == "P-A"
      and _row["contract"] == "C-A" and _row["attempt"] == 1
      and _row["duration_s"] == 7)
check("_ledger_row: gate_band is red (the task-completion assessment band)",
      _row["gate_band"] == "red")
_brow = socom._ledger_row("P-A", "builder", "C-A", _bad, 2, "t", 0)
check("_ledger_row: failed summary -> verdict broken, exit_code 1",
      _brow["verdict"] == "broken" and _brow["exit_code"] == 1)

eq("_promise_ref: (id, seat, contract) from a promise",
   socom._promise_ref(ET.fromstring(
       '<promise id="P-z"><promiser seat="builder"/><contract ref="C-z"/></promise>')),
   ("P-z", "builder", "C-z"))
eq("_promise_ref: a standalone contract is not recordable (no seat)",
   socom._promise_ref(ET.fromstring('<contract ref="C-z"/>')),
   (None, None, None))
check("_promise_ref: a promise missing its promiser has no seat",
      socom._promise_ref(ET.fromstring(
          '<promise id="P-z"><contract ref="C-z"/></promise>'))[1] is None)

# _append_ledger_row — the one writer both verify --record and the gate use
with tempfile.TemporaryDirectory() as _d:
    _r = Path(_d)
    _a = socom._append_ledger_row(_r, "P-w", "builder", "C-w", {"ok": True}, 3)
    eq("_append_ledger_row: first row is attempt 1, kept",
       (_a["attempt"], _a["verdict"]), (1, "kept"))
    _b = socom._append_ledger_row(_r, "P-w", "builder", "C-w", {"ok": False}, 0)
    eq("_append_ledger_row: second row increments attempt, broken",
       (_b["attempt"], _b["verdict"]), (2, "broken"))
    _lines = (_r / ".socom" / "ledger" / "runs.jsonl").read_text().splitlines()
    eq("_append_ledger_row: one JSONL line appended per call", len(_lines), 2)

# ── context envelope (CTX-1: _load_context_contract / _context_violations) ────
# The field contract AND the budget invariant are parsed FROM schemas/context.xml
# (single source) — pin that, then pin the validator's verdicts.
_creq, _cints, _cinv, _cdiv, _cver = socom._load_context_contract()
check("_load_context_contract: required fields parsed from the schema",
      set(_creq) == {"id", "promise", "seat", "ts", "budget_tokens", "input_tokens"})
check("_load_context_contract: int fields parsed from the schema",
      set(_cints) == {"budget_tokens", "input_tokens"})
check("_load_context_contract: budget invariant parsed (input <= budget)",
      ("input_tokens", "<=", "budget_tokens") in _cinv)
check("_load_context_contract: >= 0 lower-bound invariants parsed (literal rhs)",
      ("input_tokens", ">=", "0") in _cinv and ("budget_tokens", ">=", "0") in _cinv)
check("_load_context_contract: measurement divisor parsed from the schema (chars/4)",
      _cdiv == 4)
check("_load_context_contract: contract version parsed from the schema socom=",
      _cver == "0.1")


def _viol(xml):
    with tempfile.TemporaryDirectory() as _d:
        p = Path(_d) / "e.xml"
        p.write_text(xml)
        return socom._context_violations(p, _creq, _cints, _cinv, version=_cver)


_cgood = ('<context socom="0.1" id="CTX-1" promise="P-1" seat="builder" '
          'ts="t" budget_tokens="8000" input_tokens="3200"/>')
check("_context_violations: a valid in-budget envelope has none", _viol(_cgood) == [])
check("_context_violations: over-budget is flagged",
      any("invariant" in v for v in
          _viol(_cgood.replace('budget_tokens="8000"', 'budget_tokens="1000"'))))
check("_context_violations: a missing required field is flagged",
      any("promise" in v for v in _viol(
          '<context socom="0.1" id="CTX-1" seat="builder" ts="t" '
          'budget_tokens="8000" input_tokens="3200"/>')))
check("_context_violations: a non-int token field is flagged",
      any("is not an int" in v for v in
          _viol(_cgood.replace('input_tokens="3200"', 'input_tokens="lots"'))))
check("_context_violations: wrong root element is flagged",
      any("expected <context>" in v for v in _viol('<envelope id="CTX-1"/>')))
# CTX carry-over (CTX-1 reviewer deferral): a NEGATIVE token count must be
# flagged — left unchecked, input_tokens="-50" trivially satisfies input <=
# budget (a false PASS). Closed via the >= 0 invariants, literal-rhs machinery.
check("_context_violations: a negative input_tokens is flagged (>= 0 lower bound)",
      any("input_tokens" in v and "is false" in v for v in
          _viol(_cgood.replace('input_tokens="3200"', 'input_tokens="-50"'))))
check("_context_violations: a negative budget_tokens is flagged (>= 0 lower bound)",
      any("budget_tokens" in v and "is false" in v for v in
          _viol(_cgood.replace('budget_tokens="8000"', 'budget_tokens="-1"'))))
# CTX carry-over: an envelope written for a different contract version is rejected.
check("_context_violations: a mismatched socom= version is flagged",
      any("does not match" in v for v in
          _viol(_cgood.replace('socom="0.1"', 'socom="9.9-bogus"'))))
check("_context_violations: a missing socom= version is flagged",
      any("does not match" in v for v in _viol(
          '<context id="CTX-1" promise="P-1" seat="builder" ts="t" '
          'budget_tokens="8000" input_tokens="3200"/>')))
# An invariant rhs that is neither an int field nor an int literal can't be
# evaluated -> fail closed (degrade loudly), same posture as an unknown op.
with tempfile.TemporaryDirectory() as _d:
    _p = Path(_d) / "e.xml"
    _p.write_text(_cgood)
    _bv = socom._context_violations(_p, _creq, _cints,
                                    [("input_tokens", ">=", "notanumber")])
    check("_context_violations: an unevaluable invariant rhs fails closed",
          any("neither an int field" in v for v in _bv))
# degrade-loudly (R6): an invariant op the verifier can't evaluate must FAIL
# closed, never silently skip — else a schema edit to an unknown op is a false
# PASS on an over-budget envelope.
with tempfile.TemporaryDirectory() as _d:
    _p = Path(_d) / "e.xml"
    _p.write_text('<context socom="0.1" id="CTX-1" promise="P-1" seat="builder" '
                  'ts="t" budget_tokens="1000" input_tokens="9999"/>')
    _uv = socom._context_violations(_p, _creq, _cints, [("input_tokens", "!!", "budget_tokens")])
    check("_context_violations: an unrecognized invariant op fails closed (not skipped)",
          any("not recognized" in v for v in _uv))

with tempfile.TemporaryDirectory() as _d:
    _dd = Path(_d)
    check("_context_targets: absent path -> [] (fail-open)",
          socom._context_targets(_dd / "nope") == [])
    (_dd / "a.xml").write_text(_cgood)
    (_dd / "b.xml").write_text(_cgood)
    eq("_context_targets: a dir globs its *.xml", len(socom._context_targets(_dd)), 2)
    check("_context_targets: a file -> [file]",
          socom._context_targets(_dd / "a.xml") == [_dd / "a.xml"])

# CTX-2: measurement (chars/divisor) + the honesty re-measure of <inputs>.
eq("_estimate_tokens: round(len/divisor)", socom._estimate_tokens("a" * 40, 4), 10)
with tempfile.TemporaryDirectory() as _d:
    _repo = Path(_d) / "repo"           # repo is a SUBDIR so an outside file exists
    _repo.mkdir()
    (Path(_d) / "outside.txt").write_text("secret outside the repo tree")
    (_repo / "art.txt").write_text("x" * 40)  # 40 chars -> 10 tokens at chars/4
    eq("_measure_ref: a live ref measured at the schema divisor",
       socom._measure_ref(_repo, "art.txt", 4), 10)
    check("_measure_ref: an absent ref -> None (degrade loudly)",
          socom._measure_ref(_repo, "nope.txt", 4) is None)

    def _hviol(total, decl):
        env = _repo / "e.xml"
        env.write_text(f'<context socom="0.1" id="C" promise="P" seat="s" ts="t" '
                       f'budget_tokens="1000" input_tokens="{total}">'
                       f'<inputs><input ref="art.txt" tokens="{decl}"/></inputs></context>')
        return socom._context_violations(env, _creq, _cints, _cinv, _repo, 4)

    check("honesty: declared == re-measured (per-input AND total) -> no violations",
          _hviol(10, 10) == [])
    check("honesty: a forged per-input tokens is flagged",
          any("re-measured" in v for v in _hviol(10, 99)))
    check("honesty: a forged input_tokens total is flagged",
          any("sum of re-measured" in v for v in _hviol(99, 10)))
    _m = _repo / "m.xml"
    _m.write_text('<context socom="0.1" id="C" promise="P" seat="s" ts="t" '
                  'budget_tokens="1000" input_tokens="5">'
                  '<inputs><input ref="gone.txt" tokens="5"/></inputs></context>')
    check("honesty: an unreadable input ref is flagged (degrade loudly)",
          any("does not resolve" in v for v in
              socom._context_violations(_m, _creq, _cints, _cinv, _repo, 4)))
    # repo=None skips the re-measure entirely (CTX-1 backward-compat path)
    (_repo / "e.xml").write_text(
        '<context socom="0.1" id="C" promise="P" seat="s" ts="t" '
        'budget_tokens="1000" input_tokens="99">'
        '<inputs><input ref="art.txt" tokens="10"/></inputs></context>')
    check("honesty: skipped when repo is None (CTX-1 schema-only, backward-compat)",
          socom._context_violations(_repo / "e.xml", _creq, _cints, _cinv) == [])

    # path containment (blocker fix): a ref escaping the repo tree reads as None —
    # no path-traversal side-channel from a crafted envelope.
    check("_read_ref: an in-repo ref still reads",
          socom._read_ref(_repo, "art.txt") == "x" * 40)
    check("_read_ref: a ../ escape is refused (None)",
          socom._read_ref(_repo, "../outside.txt") is None)
    check("_read_ref: an absolute path outside the repo is refused (None)",
          socom._read_ref(_repo, str(Path(_d) / "outside.txt")) is None)
    try:
        (_repo / "link.txt").symlink_to(Path(_d) / "outside.txt")
        check("_read_ref: an in-repo symlink pointing outside is refused (None)",
              socom._read_ref(_repo, "link.txt") is None)
    except OSError:
        pass  # symlinks unsupported on this filesystem — skip

# divisor is single-sourced from the schema: a schema lacking a valid
# <measurement divisor> must degrade loudly, never silently default (major fix).
with tempfile.TemporaryDirectory() as _d:
    _bad = Path(_d) / "noschema.xml"
    _bad.write_text('<context-schema><fields>'
                    '<field name="id" type="id" required="true"/></fields>'
                    '</context-schema>')
    try:
        socom._load_context_contract(_bad)
        check("_load_context_contract: missing <measurement> degrades loudly", False)
    except SystemExit:
        check("_load_context_contract: missing <measurement> degrades loudly", True)

# CTX-3 producer: emit's pure helpers — id sequencing and flag parsing.
with tempfile.TemporaryDirectory() as _d:
    _repo = Path(_d)
    (_repo / socom.SOCOM_DIR / "context").mkdir(parents=True)
    eq("_next_context_id: first id of the day is …-001",
       socom._next_context_id(_repo, "2026-0620"), "CTX-2026-0620-001")
    (_repo / socom.SOCOM_DIR / "context" / "CTX-2026-0620-001.xml").write_text("<context/>")
    (_repo / socom.SOCOM_DIR / "context" / "CTX-2026-0620-007.xml").write_text("<context/>")
    eq("_next_context_id: sequences past the highest existing seq (max+1, not count)",
       socom._next_context_id(_repo, "2026-0620"), "CTX-2026-0620-008")
    eq("_next_context_id: a different date restarts at …-001",
       socom._next_context_id(_repo, "2026-0621"), "CTX-2026-0621-001")

_ef = socom._emit_flags(["--promise", "P-1", "--seat", "builder", "--budget", "8000",
                         "--input", "a.txt", "--input", "b.txt", "--id", "CTX-X"])
check("_emit_flags: scalar flags parsed",
      _ef["promise"] == "P-1" and _ef["seat"] == "builder"
      and _ef["budget"] == "8000" and _ef["id"] == "CTX-X")
check("_emit_flags: --input is repeatable (accumulates)", _ef["input"] == ["a.txt", "b.txt"])
check("_emit_flags: no inputs -> empty list (CTX-1-style envelope is legal)",
      socom._emit_flags(["--promise", "P", "--seat", "s", "--budget", "1"])["input"] == [])
try:
    socom._emit_flags(["--promise"])  # dangling flag, no value
    check("_emit_flags: a dangling flag degrades loudly (SystemExit)", False)
except SystemExit:
    check("_emit_flags: a dangling flag degrades loudly (SystemExit)", True)
try:
    socom._emit_flags(["--bogus", "x"])  # unknown flag
    check("_emit_flags: an unknown flag degrades loudly (SystemExit)", False)
except SystemExit:
    check("_emit_flags: an unknown flag degrades loudly (SystemExit)", True)
try:
    socom._emit_flags(["--promise", "P-1", "--promise", "P-2"])  # duplicate scalar
    check("_emit_flags: a duplicated scalar flag degrades loudly (SystemExit)", False)
except SystemExit:
    check("_emit_flags: a duplicated scalar flag degrades loudly (SystemExit)", True)

# ── monarch — run liveness classification (pure: record + now -> state) ──────
import os as _os
_mnow = datetime(2026, 6, 21, 12, 0, 0, tzinfo=timezone.utc)


def _rec(**kw):
    base = {"status": "running", "pid": 2147483646,
            "ts_started": _mnow.isoformat()}
    base.update(kw)
    return base


eq("_classify: materialized passes through",
   socom._classify(_rec(status="materialized"), _mnow), "materialized")
eq("_classify: dead passes through",
   socom._classify(_rec(status="dead"), _mnow), "dead")
eq("_classify: running + dead pid -> dead",
   socom._classify(_rec(pid=2147483646), _mnow), "dead")
eq("_classify: running + no pid -> dead",
   socom._classify(_rec(pid=None), _mnow), "dead")
eq("_classify: running + stale start -> dead (cross-host horizon)",
   socom._classify(_rec(ts_started=(_mnow - timedelta(hours=socom.RUN_STALE_HOURS + 1)).isoformat()),
                   _mnow), "dead")
eq("_classify: running + unparseable start -> dead",
   socom._classify(_rec(ts_started="not-a-date"), _mnow), "dead")
check("_classify: running + live pid + fresh -> running",
      socom._classify(_rec(pid=_os.getpid()), _mnow) == "running")
check("_pid_alive: this process is alive", socom._pid_alive(_os.getpid()))
check("_pid_alive: pid 0 / None / negative is dead",
      not socom._pid_alive(0) and not socom._pid_alive(None) and not socom._pid_alive(-5))
eq("_uptime: seconds", socom._uptime(_rec(ts_started=(_mnow - timedelta(seconds=5)).isoformat()), _mnow), "5s")
eq("_uptime: minutes", socom._uptime(_rec(ts_started=(_mnow - timedelta(minutes=3)).isoformat()), _mnow), "3m")
eq("_uptime: hours", socom._uptime(_rec(ts_started=(_mnow - timedelta(hours=2)).isoformat()), _mnow), "2h")
eq("_uptime: days", socom._uptime(_rec(ts_started=(_mnow - timedelta(days=4)).isoformat()), _mnow), "4d")
eq("_uptime: unparseable -> ?", socom._uptime(_rec(ts_started="x"), _mnow), "?")

# ── monarch recover — kept-check + attempt-count + recoverable bucketing ──────
eq("_promise_kept: a kept verdict for the promise is seen",
   socom._promise_kept([{"promise": "P", "verdict": "kept"}], "P"), True)
eq("_promise_kept: only broken verdicts -> not kept",
   socom._promise_kept([{"promise": "P", "verdict": "broken"}], "P"), False)
eq("_promise_kept: a kept verdict for ANOTHER promise does not count",
   socom._promise_kept([{"promise": "Q", "verdict": "kept"}], "P"), False)
eq("_attempts_on_file: max of run-record count and ledger attempt (records win)",
   socom._attempts_on_file([("x", {"promise": "P"}), ("y", {"promise": "P"})],
                           [{"promise": "P", "attempt": 1}], "P"), 2)
eq("_attempts_on_file: max of run-record count and ledger attempt (ledger wins)",
   socom._attempts_on_file([("x", {"promise": "P"})],
                           [{"promise": "P", "attempt": 4}], "P"), 4)

import json as _json
import tempfile as _tf
_recroot = Path(_tf.mkdtemp())
_recdir = _recroot / ".socom" / "runs"
_recdir.mkdir(parents=True)
_ledf = _recroot / ".socom" / "ledger" / "runs.jsonl"
_ledf.parent.mkdir(parents=True)


def _wrun(rid, promise, **kw):
    base = {"run_id": rid, "seat": "builder", "promise": promise, "contract": "C",
            "runtime": "claude-code", "model": "default", "status": "dead",
            "ts_started": _mnow.isoformat(), "pid": None, "brief_path": "b",
            "promise_path": "p.xml", "ts_ended": None, "exit_code": 137}
    base.update(kw)
    (_recdir / f"{rid}.json").write_text(_json.dumps(base))


_freshnow = datetime.now(timezone.utc).isoformat()
# PA: one dead, unkept            -> ELIGIBLE
_wrun("R-PA-1", "PA")
# PB: dead but a kept ledger row  -> not eligible (already kept)
_wrun("R-PB-1", "PB")
# PC: three dead, unkept          -> ABANDONED (at the cap)
_wrun("R-PC-1", "PC"); _wrun("R-PC-2", "PC"); _wrun("R-PC-3", "PC")
# PD: dead + a LIVE running sibling -> not eligible (never double-dispatch)
_wrun("R-PD-1", "PD")
_wrun("R-PD-2", "PD", status="running", pid=_os.getpid(), ts_started=_freshnow)
# PE: dead + a materialized sibling -> not eligible (a launch is pending)
_wrun("R-PE-1", "PE"); _wrun("R-PE-2", "PE", status="materialized")
_ledf.write_text(_json.dumps({"promise": "PB", "verdict": "kept", "attempt": 1}) + "\n")

_elig, _aband = socom.recoverable(_recroot)
_eset = {e["promise"] for e in _elig}
_aset = {e["promise"] for e in _aband}
eq("recoverable: only the dead+unkept+under-cap promise is eligible", _eset, {"PA"})
eq("recoverable: the at-cap promise is abandoned, not eligible", _aset, {"PC"})
check("recoverable: a kept promise is never offered", "PB" not in _eset and "PB" not in _aset)
check("recoverable: a promise with a live run is never double-dispatched", "PD" not in _eset)
check("recoverable: a promise with a materialized launch is not re-dispatched", "PE" not in _eset)
eq("RECOVER_MAX_ATTEMPTS default is 3", socom.RECOVER_MAX_ATTEMPTS, 3)

# ── summary ──────────────────────────────────────────────────────────────────
print(f"unit: {_PASS} passed, {_FAIL} failed")
raise SystemExit(1 if _FAIL else 0)
