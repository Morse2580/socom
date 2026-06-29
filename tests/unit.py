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

# ── judge — assessor calibration (Phase 2b: TPR/TNR vs human labels) ─────────
# a perfect judge: every human label matched
_perf = socom._judge_metrics([{"human": "pass", "judge": "pass"},
                              {"human": "fail", "judge": "fail"}])
eq("_judge_metrics: perfect judge TPR=100", _perf["tpr"], 100.0)
eq("_judge_metrics: perfect judge TNR=100", _perf["tnr"], 100.0)
eq("_judge_metrics: perfect judge agreement=100", _perf["agreement"], 100.0)
# a sycophantic judge that always says 'pass' — high TPR, ZERO TNR (the failure the
# gate must catch: it never rejects bad work, but raw agreement looks fine under imbalance)
_syc = socom._judge_metrics([{"human": "pass", "judge": "pass"}] * 9
                            + [{"human": "fail", "judge": "pass"}])
eq("_judge_metrics: sycophant TPR=100 (accepts all good)", _syc["tpr"], 100.0)
eq("_judge_metrics: sycophant TNR=0 (never rejects bad)", _syc["tnr"], 0.0)
eq("_judge_metrics: sycophant agreement is misleadingly high (90)", _syc["agreement"], 90.0)
check("_judge_metrics: confusion counts add up to n",
      _syc["tp"] + _syc["fp"] + _syc["tn"] + _syc["fn"] == _syc["n"] == 10)
# half-labelled rows are skipped & counted, never inflate the score
_skip = socom._judge_metrics([{"human": "pass", "judge": "pass"},
                             {"human": "?", "judge": "pass"}, {"human": "pass"}])
eq("_judge_metrics: unusable rows are skipped", _skip["skipped"], 2)
eq("_judge_metrics: only fully-labelled rows count toward n", _skip["n"], 1)
eq("_judge_metrics: empty denominator -> None rate (no fabricated 100)",
   socom._judge_metrics([{"human": "pass", "judge": "pass"}])["tnr"], None)

# ── contract adequacy — is a GREEN verify real confidence? (Phase 2c) ────────
check("_trivial_run: true/:/exit 0/echo are vacuous",
      all(socom._trivial_run(c) for c in ("true", ":", "exit 0", "echo hi", "  echo  ")))
check("_trivial_run: a real command is not trivial",
      not socom._trivial_run("pytest -q") and not socom._trivial_run("./run.sh"))
_full = ET.fromstring(
    '<contract ref="C-1"><goal>g</goal>'
    '<check id="1" assessor="gate:tc"><run>pytest -q</run><expect>green</expect></check>'
    '<check id="2" assessor="gate:tc"><run>./lint.sh</run><expect>clean</expect></check>'
    '<regression-surface>existing API stays green</regression-surface>'
    '<out-of-scope>perf</out-of-scope></contract>')
_a_full = socom._contract_adequacy(_full, socom._contract_checks(_full))
check("_contract_adequacy: a real contract is ADEQUATE, no findings",
      _a_full["adequate"] and _a_full["findings"] == [])
_manual = ET.fromstring(
    '<contract ref="C-2"><goal>g</goal>'
    '<check id="1" assessor="reviewer"><expect>looks right</expect></check></contract>')
_a_manual = socom._contract_adequacy(_manual, socom._contract_checks(_manual))
check("_contract_adequacy: all-manual contract is WEAK (strong: no-auto-check)",
      not _a_manual["adequate"]
      and any(f[1] == "no-auto-check" and f[0] == "strong" for f in _a_manual["findings"]))
_vac = ET.fromstring(
    '<contract ref="C-3"><goal>g</goal>'
    '<check id="1" assessor="gate:tc"><run>true</run><expect>x</expect></check></contract>')
_a_vac = socom._contract_adequacy(_vac, socom._contract_checks(_vac))
check("_contract_adequacy: only-trivial checks are WEAK (strong: vacuous-checks)",
      not _a_vac["adequate"]
      and any(f[1] == "vacuous-checks" for f in _a_vac["findings"]))
check("_contract_adequacy: a real-but-thin contract flags weak coverage, stays adequate",
      socom._contract_adequacy(
          ET.fromstring('<contract ref="C-4"><goal>g</goal>'
                        '<check id="1" assessor="gate:tc"><run>pytest</run>'
                        '<expect>x</expect></check></contract>'),
          socom._contract_checks(ET.fromstring(
              '<contract ref="C-4"><goal>g</goal><check id="1" assessor="gate:tc">'
              '<run>pytest</run><expect>x</expect></check></contract>')))["adequate"]
      and any(f[1] == "no-regression-surface" for f in socom._contract_adequacy(
          _vac, socom._contract_checks(_vac))["findings"]))

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

# ── monarch — Phase-1 runtime budget (runaway guard) ────────────────────────
check("_overrun: no budget on record -> False (legacy/opt-out falls through)",
      not socom._overrun(_rec(), _mnow))
check("_overrun: within budget -> False",
      not socom._overrun(_rec(max_runtime_s=3600,
                              ts_started=(_mnow - timedelta(seconds=100)).isoformat()), _mnow))
check("_overrun: past budget -> True",
      socom._overrun(_rec(max_runtime_s=60,
                          ts_started=(_mnow - timedelta(seconds=120)).isoformat()), _mnow))
check("_overrun: zero budget disables the deadline -> False",
      not socom._overrun(_rec(max_runtime_s=0,
                              ts_started=(_mnow - timedelta(hours=99)).isoformat()), _mnow))
check("_overrun: unparseable start -> False (left to _stale)",
      not socom._overrun(_rec(max_runtime_s=60, ts_started="x"), _mnow))
eq("_classify: running + live pid but overrun -> dead (budget overrides liveness)",
   socom._classify(_rec(pid=_os.getpid(), max_runtime_s=1,
                        ts_started=(_mnow - timedelta(seconds=10)).isoformat()), _mnow), "dead")
check("_kill: bogus pid (0 / None / negative) is a no-op False",
      not socom._kill(0) and not socom._kill(None) and not socom._kill(-5))
eq("_resolve_runtime_budget: absent limits -> default",
   socom._resolve_runtime_budget({}), socom.DEFAULT_MAX_RUNTIME_S)
eq("_resolve_runtime_budget: explicit value honored",
   socom._resolve_runtime_budget({"limits": {"max_runtime_s": 120}}), 120)
eq("_resolve_runtime_budget: explicit 0 disables (allowed)",
   socom._resolve_runtime_budget({"limits": {"max_runtime_s": 0}}), 0)
for _bad in (-1, "60", True, 1.5):
    try:
        socom._resolve_runtime_budget({"limits": {"max_runtime_s": _bad}})
        check(f"_resolve_runtime_budget: invalid {_bad!r} degrades loudly (SystemExit)", False)
    except SystemExit:
        check(f"_resolve_runtime_budget: invalid {_bad!r} degrades loudly (SystemExit)", True)
eq("_uptime: seconds", socom._uptime(_rec(ts_started=(_mnow - timedelta(seconds=5)).isoformat()), _mnow), "5s")
eq("_uptime: minutes", socom._uptime(_rec(ts_started=(_mnow - timedelta(minutes=3)).isoformat()), _mnow), "3m")
eq("_uptime: hours", socom._uptime(_rec(ts_started=(_mnow - timedelta(hours=2)).isoformat()), _mnow), "2h")
eq("_uptime: days", socom._uptime(_rec(ts_started=(_mnow - timedelta(days=4)).isoformat()), _mnow), "4d")
eq("_uptime: unparseable -> ?", socom._uptime(_rec(ts_started="x"), _mnow), "?")

# ── lessons -> regression cases (Phase 2b: the do-not-break set) ─────────────
with tempfile.TemporaryDirectory() as _rd:
    _rr = Path(_rd)
    _ld = _rr / ".socom" / "lessons"
    _ld.mkdir(parents=True)
    (_ld / "L-PX.xml").write_text(
        '<lesson id="L-PX" domain="cli" state="active">'
        '<derived-from promise="P-X" cycle="c" broken="3" total="4"/></lesson>')
    (_ld / "L-PY.xml").write_text(  # provisional -> NOT a regression contract yet
        '<lesson id="L-PY" domain="cli" state="provisional">'
        '<derived-from promise="P-Y" cycle="c" broken="2" total="2"/></lesson>')
    _re = socom._regression_entries(_rr)
    check("_regression_entries: only ACTIVE promise-guarding lessons count",
          len(_re) == 1 and _re[0]["promise"] == "P-X" and _re[0]["lesson"] == "L-PX")
    _led = _rr / ".socom" / "ledger"
    _led.mkdir(parents=True)
    (_led / "runs.jsonl").write_text(
        '{"promise":"P-X","verdict":"broken","attempt":1,"ts":"2026-06-01T00:00:00+00:00"}\n'
        '{"promise":"P-X","verdict":"kept","attempt":2,"ts":"2026-06-02T00:00:00+00:00"}\n')
    eq("_latest_verdict: takes the MOST-RECENT attempt (kept beats the earlier broken)",
       socom._latest_verdict(_rr).get("P-X"), "kept")
    (_led / "runs.jsonl").write_text(
        '{"promise":"P-X","verdict":"kept","attempt":1,"ts":"2026-06-01T00:00:00+00:00"}\n'
        '{"promise":"P-X","verdict":"broken","attempt":2,"ts":"2026-06-02T00:00:00+00:00"}\n')
    eq("_latest_verdict: a later broken IS the regression signal",
       socom._latest_verdict(_rr).get("P-X"), "broken")
    eq("_latest_verdict: absent ledger -> {} (no crash)",
       socom._latest_verdict(Path(_rd) / "nope"), {})

# ── trace — OTLP/GenAI span export (Phase 2a observability) ──────────────────
eq("_iso_nanos: parses ISO to unix nanos (string)",
   socom._iso_nanos("2026-06-21T12:00:00+00:00"), str(int(_mnow.timestamp() * 1_000_000_000)))
eq("_iso_nanos: unparseable -> None", socom._iso_nanos("nope"), None)
eq("_attr: int -> stringified intValue",
   socom._attr("k", 5), {"key": "k", "value": {"intValue": "5"}})
eq("_attr: bool -> boolValue (not int — bool tested first)",
   socom._attr("k", True), {"key": "k", "value": {"boolValue": True}})
eq("_attr: str -> stringValue",
   socom._attr("k", "v"), {"key": "k", "value": {"stringValue": "v"}})
# a done run -> OK status with GenAI attrs; a dead run -> ERROR + error.type
_done = _rec(status="done", exit_code=0, run_id="R-d", seat="builder",
             promise="P1", model="default", runtime="claude-code",
             ts_ended=(_mnow + timedelta(seconds=5)).isoformat())
_dspan = socom._run_span(_done, _mnow, "kept")
eq("_run_span: done+exit0 -> status OK", _dspan["status"]["code"], 1)
_akeys = {a["key"]: a["value"] for a in _dspan["attributes"]}
check("_run_span: carries gen_ai.operation.name=invoke_agent",
      _akeys.get("gen_ai.operation.name") == {"stringValue": "invoke_agent"})
check("_run_span: agent.name is the seat, request.model is the model",
      _akeys.get("gen_ai.agent.name") == {"stringValue": "builder"}
      and _akeys.get("gen_ai.request.model") == {"stringValue": "default"})
check("_run_span: conversation.id is the promise; verdict rides as cross-ref",
      _akeys.get("gen_ai.conversation.id") == {"stringValue": "P1"}
      and _akeys.get("socom.promise.verdict") == {"stringValue": "kept"})
check("_run_span: NO fabricated token usage when the record lacks it",
      "gen_ai.usage.input_tokens" not in _akeys)
check("_run_span: deterministic ids (trace=hash(promise) 32hex, span=hash(run) 16hex)",
      len(_dspan["traceId"]) == 32 and len(_dspan["spanId"]) == 16)
_dead = _rec(status="running", pid=2147483646, run_id="R-x", promise="P2",
             ts_started=(_mnow - timedelta(hours=socom.RUN_STALE_HOURS + 1)).isoformat())
_xspan = socom._run_span(_dead, _mnow, "broken")
eq("_run_span: dead run -> status ERROR", _xspan["status"]["code"], 2)
check("_run_span: ERROR span carries error.type",
      any(a["key"] == "error.type" for a in _xspan["attributes"]))
# usage IS emitted when the record actually carries it
_tok = socom._run_span(_rec(status="done", exit_code=0, input_tokens=120,
                            output_tokens=40), _mnow, None)
_tkeys = {a["key"] for a in _tok["attributes"]}
check("_run_span: emits gen_ai.usage.* when the record carries token counts",
      {"gen_ai.usage.input_tokens", "gen_ai.usage.output_tokens"} <= _tkeys)
# the OTLP envelope is well-formed (resourceSpans -> scopeSpans -> spans)
_otlp = socom._otlp_payload([("p", _done)], {"P1": "kept"}, _mnow)
check("_otlp_payload: valid ExportTraceServiceRequest shape",
      _otlp["resourceSpans"][0]["scopeSpans"][0]["spans"][0]["name"].startswith("invoke_agent"))
eq("_run_seconds: ts_ended - ts_started in whole seconds",
   socom._run_seconds(_done), 5)
eq("_run_seconds: missing end stamp -> 0", socom._run_seconds(_rec(ts_ended=None)), 0)

# ── meter — parse real token usage from runtime output (Phase 2a token half) ─
eq("_parse_usage: whole-object JSON (claude --output-format json)",
   socom._parse_usage('{"type":"result","usage":{"input_tokens":1200,"output_tokens":340}}'),
   {"input_tokens": 1200, "output_tokens": 340})
eq("_parse_usage: scans for the LAST pair in a mixed/stream log",
   socom._parse_usage('noise "input_tokens": 1 ... later "input_tokens": 50, '
                      '"output_tokens": 9 trailing'),
   {"input_tokens": 50, "output_tokens": 9})
eq("_parse_usage: no usage -> None (never fabricated)",
   socom._parse_usage("just some plain log output, no tokens here"), None)
eq("_parse_usage: half a pair (input only) -> None",
   socom._parse_usage('{"usage":{"input_tokens":10}}'), None)
eq("_parse_usage: empty/none -> None", socom._parse_usage(""), None)
# _run_overran: a finished run under budget is NOT an overrun even if it started long ago
check("_run_overran: finished run under budget -> False (not judged against now)",
      not socom._run_overran(_done, _mnow))
check("_run_overran: killed run (exit 137) -> True",
      socom._run_overran(_rec(status="dead", exit_code=137, max_runtime_s=3600,
                              ts_ended=(_mnow + timedelta(seconds=10)).isoformat()), _mnow))
check("_run_overran: finished run OVER budget -> True",
      socom._run_overran(_rec(status="done", exit_code=0, max_runtime_s=5,
                              ts_started=_mnow.isoformat(),
                              ts_ended=(_mnow + timedelta(seconds=60)).isoformat()), _mnow))
check("_run_overran: still-running past the live deadline -> True",
      socom._run_overran(_rec(status="running", pid=_os.getpid(), max_runtime_s=1,
                              ts_started=(_mnow - timedelta(seconds=10)).isoformat()), _mnow))

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

# ── monarch triage — rank eligible dead runs by recovery-worth (reuse l0_score) ─
_troot = Path(_tf.mkdtemp())
(_troot / ".socom" / "runs").mkdir(parents=True)
(_troot / ".socom" / "promises").mkdir(parents=True)


def _wpromise(pid, intent):
    (_troot / ".socom" / "promises" / f"{pid}.xml").write_text(
        f'<promise id="{pid}" domain="cli"><intent><verbatim>{intent}</verbatim>'
        f'</intent><contract ref="C-{pid}"><goal>{intent}</goal></contract></promise>')


def _wdead(rid, pid):
    (_troot / ".socom" / "runs" / f"{rid}.json").write_text(_json.dumps({
        "run_id": rid, "seat": "builder", "promise": pid, "contract": f"C-{pid}",
        "runtime": "claude-code", "model": "default", "status": "dead",
        "ts_started": _mnow.isoformat(), "pid": None, "brief_path": "b",
        "promise_path": f".socom/promises/{pid}.xml", "ts_ended": None,
        "exit_code": 137}))


_wpromise("PX", "make the ledger flock serialize concurrent writers")
_wpromise("PY", "restyle the frontend widget colour palette")
_wdead("R-PX-1", "PX")
_wdead("R-PY-1", "PY")
_telig, _ = socom.recoverable(_troot)
eq("triage fixture: both promises are eligible", {e["promise"] for e in _telig}, {"PX", "PY"})

_tranked, _tbasis = socom._triage_rank(_troot, _telig, "flock")
eq("_triage_rank: a focus-matching promise ranks first", _tranked[0]["promise"], "PX")
check("_triage_rank: the basis names the focus", "focus" in _tbasis)
eq("_triage_rank: the matching promise carries a positive worth", _tranked[0]["worth"] >= 1, True)
eq("_triage_rank: the non-matching promise carries zero worth",
   [x for x in _tranked if x["promise"] == "PY"][0]["worth"], 0)

_nranked, _nbasis = socom._triage_rank(_troot, _telig, "zzz qqq nomatch")
check("_triage_rank: no overlap -> loud recency fallback", "recency" in _nbasis)

# no focus -> rank by the active-lesson corpus (lifecycle-honest)
(_troot / ".socom" / "lessons").mkdir(parents=True)
(_troot / ".socom" / "lessons" / "L-1.xml").write_text(
    '<lesson id="L-1" domain="cli" state="active"><statement embed="true">'
    'flock around the ledger read-compute-append or attempts duplicate</statement></lesson>')
_lranked, _lbasis = socom._triage_rank(_troot, _telig, None)
eq("_triage_rank: no focus ranks by active-lesson overlap", _lranked[0]["promise"], "PX")
check("_triage_rank: lesson basis", "lesson" in _lbasis.lower())
check("_active_lessons_text: gathers the active statement",
      "flock" in socom._active_lessons_text(_troot))
eq("_run_intent: reads verbatim + goal from the promise",
   "flock" in socom._run_intent(_troot, {"promise_path": ".socom/promises/PX.xml"}), True)
eq("_run_intent: a missing promise_path is tolerant ('')",
   socom._run_intent(_troot, {}), "")
eq("_focus_arg: skips flags and --top's value, returns the positional",
   socom._focus_arg(["flock", "--top", "2", "--exec"]), "flock")
eq("_focus_arg: only flags -> None", socom._focus_arg(["--exec", "--top", "1"]), None)
eq("_parse_top: a positive int parses", socom._parse_top(["--top", "2"]), 2)
eq("_parse_top: absent -> None", socom._parse_top(["--exec"]), None)
try:
    socom._parse_top(["--top", "0"])
    check("_parse_top: non-positive exits loud", False)
except SystemExit:
    check("_parse_top: non-positive exits loud", True)

# ── per-seat trust weighting of recovery-worth (slice 7), keyed by (seat, model) (slice 9) ──
_trows = ([{"promise": "h1", "seat": "builder", "verdict": "kept", "model": "default"}] * 3
          + [{"promise": "h2", "seat": "reviewer", "verdict": "broken", "model": "default"}] * 3)
_tmap = socom._seat_trust(_trows)
eq("_seat_trust: a mostly-kept seat -> Laplace rate (3+1)/(3+2)",
   round(_tmap[("builder", "default")], 3), 0.8)
eq("_seat_trust: a mostly-broken seat -> (0+1)/(3+2)",
   round(_tmap[("reviewer", "default")], 3), 0.2)
eq("_seat_trust: one kept of one is damped to 2/3 (small sample)",
   round(socom._seat_trust([{"seat": "x", "verdict": "kept"}])[("x", None)], 3), 0.667)
eq("_trust_of: an unseen (seat, model) -> the neutral 1/2 prior",
   socom._trust_of(_tmap, "neverseen", "default"), 0.5)
eq("_seat_trust: a non-kept/broken verdict is ignored, not counted as failure",
   socom._seat_trust([{"seat": "z", "verdict": "kept"},
                      {"seat": "z", "verdict": "amber"}]).get(("z", None)),
   socom._seat_trust([{"seat": "z", "verdict": "kept"}])[("z", None)])
check("_seat_trust: a seat with ONLY non-kept/broken verdicts is absent (-> 1/2 prior)",
      ("q", None) not in socom._seat_trust([{"seat": "q", "verdict": "skipped"}]))

# slice 9 — trust is scoped to (seat, model): a model UPGRADE resets to the neutral prior.
_mvrows = [{"seat": "builder", "verdict": "kept", "model": "modelA"}] * 3
_mvmap = socom._seat_trust(_mvrows)
eq("_seat_trust: trust is keyed by (seat, model)", round(_mvmap[("builder", "modelA")], 3), 0.8)
eq("_trust_of: the SAME seat under an UPGRADED model -> neutral 1/2 (reset, not inherited)",
   socom._trust_of(_mvmap, "builder", "modelB"), 0.5)
eq("_trust_of: the seat under its EARNED model keeps its earned trust",
   round(socom._trust_of(_mvmap, "builder", "modelA"), 3), 0.8)
eq("_seat_trust: the same seat under two models forms two independent buckets",
   sorted(socom._seat_trust(
       [{"seat": "b", "verdict": "kept", "model": "m1"},
        {"seat": "b", "verdict": "broken", "model": "m2"}]).keys()),
   [("b", "m1"), ("b", "m2")])
eq("_seat_trust: a legacy row (no model) buckets under (seat, None), inert for live runs",
   list(socom._seat_trust([{"seat": "b", "verdict": "kept"}]).keys()), [("b", None)])

# _promise_model: the verdict inherits the model of the promise's LATEST run record (slice 9)
_pmroot = Path(_tf.mkdtemp())
eq("_promise_model: no runs dir -> None (a manual verify has no model)",
   socom._promise_model(_pmroot, "P-1"), None)
(_pmroot / ".socom" / "runs").mkdir(parents=True)
(_pmroot / ".socom" / "runs" / "R-old.json").write_text(_json.dumps(
    {"promise": "P-1", "model": "m-old", "ts_started": "2026-06-20T10:00:00+00:00"}))
(_pmroot / ".socom" / "runs" / "R-new.json").write_text(_json.dumps(
    {"promise": "P-1", "model": "m-new", "ts_started": "2026-06-21T10:00:00+00:00"}))
(_pmroot / ".socom" / "runs" / "R-other.json").write_text(_json.dumps(
    {"promise": "P-2", "model": "m-x", "ts_started": "2026-06-22T10:00:00+00:00"}))
eq("_promise_model: returns the LATEST run's model for the promise (not another promise's)",
   socom._promise_model(_pmroot, "P-1"), "m-new")
eq("_promise_model: a promise with no run record -> None",
   socom._promise_model(_pmroot, "P-never"), None)
# tied ts_started -> deterministic by run-id (never let glob order decide the model)
_pmtie = Path(_tf.mkdtemp())
(_pmtie / ".socom" / "runs").mkdir(parents=True)
for _rid, _m in (("R-aaa", "m-lo"), ("R-zzz", "m-hi")):
    (_pmtie / ".socom" / "runs" / f"{_rid}.json").write_text(_json.dumps(
        {"run_id": _rid, "promise": "P-T", "model": _m,
         "ts_started": "2026-06-21T10:00:00+00:00"}))
eq("_promise_model: a ts tie is broken deterministically by run-id (higher wins)",
   socom._promise_model(_pmtie, "P-T"), "m-hi")

# composite ranking: relevance PRIMARY, trust SECONDARY (slice 7)
_xroot = Path(_tf.mkdtemp())
(_xroot / ".socom" / "runs").mkdir(parents=True)
(_xroot / ".socom" / "promises").mkdir(parents=True)
(_xroot / ".socom" / "ledger").mkdir(parents=True)
# NOTE: the LOW-trust seat (reviewer) gets the alphabetically-FIRST promise id, so a
# pass that ranks the builder run first proves TRUST reordered it — not the run-id tie-break.
for _pid, _seat, _intent in (("PT-A", "reviewer", "alpha alpha"),
                             ("PT-B", "builder", "beta beta")):
    (_xroot / ".socom" / "promises" / f"{_pid}.xml").write_text(
        f'<promise id="{_pid}" domain="cli"><intent><verbatim>{_intent}</verbatim></intent>'
        f'<contract ref="C"><goal>{_intent}</goal></contract></promise>')
    (_xroot / ".socom" / "runs" / f"R-{_pid}.json").write_text(_json.dumps({
        "run_id": f"R-{_pid}", "seat": _seat, "promise": _pid, "contract": "C",
        "runtime": "claude-code", "model": "default", "status": "dead",
        "ts_started": _mnow.isoformat(), "pid": None, "brief_path": "b",
        "promise_path": f".socom/promises/{_pid}.xml", "ts_ended": None, "exit_code": 137}))
# builder mostly-kept, reviewer mostly-broken (for OTHER promises -> PT-* stay unkept)
(_xroot / ".socom" / "ledger" / "runs.jsonl").write_text("\n".join(_json.dumps(r) for r in _trows) + "\n")
_xelig, _ = socom.recoverable(_xroot)
eq("trust fixture: both runs are eligible", {e["promise"] for e in _xelig}, {"PT-A", "PT-B"})
# equal relevance (focus hits both once) -> the higher-trust seat (builder/PT-B) ranks first,
# overriding the run-id tie-break that would otherwise put PT-A first
_eqrank, _eqbasis = socom._triage_rank(_xroot, _xelig, "alpha beta")
eq("_triage_rank: equal relevance -> higher-trust seat ranks first", _eqrank[0]["promise"], "PT-B")
check("_triage_rank: basis names trust when it is an active signal", "trust" in _eqbasis)
# relevance stays PRIMARY: PT-A is strictly more relevant to 'alpha' and outranks despite LOW trust
_relrank, _ = socom._triage_rank(_xroot, _xelig, "alpha")
eq("_triage_rank: a strictly-more-relevant run outranks a higher-trust one",
   _relrank[0]["promise"], "PT-A")
# no relevance signal -> trust becomes the effective primary (builder/PT-B first)
_trrank, _trbasis = socom._triage_rank(_xroot, _xelig, "gamma")
eq("_triage_rank: no relevance -> trust decides (builder/PT-B first)",
   _trrank[0]["promise"], "PT-B")
check("_triage_rank: no relevance but trust varies -> trust basis", "trust" in _trbasis)
# slice-5 invariant: an empty ledger (uniform 1/2 trust) reproduces the relevance-only order
(_xroot / ".socom" / "ledger" / "runs.jsonl").write_text("")
_flat, _flatbasis = socom._triage_rank(_xroot, _xelig, "gamma")
check("_triage_rank: empty ledger + no relevance -> recency basis (slice-5 preserved)",
      "recency" in _flatbasis)

# slice 9 — triage ranks by (seat, model): a dead run under the EARNED model outranks the
# same seat's dead run under an UPGRADED (unseen) model, equal relevance. The earned-model
# run gets the alphabetically-LATER run-id, so ranking it first proves TRUST (not tie-break).
_mvroot = Path(_tf.mkdtemp())
(_mvroot / ".socom" / "runs").mkdir(parents=True)
(_mvroot / ".socom" / "promises").mkdir(parents=True)
(_mvroot / ".socom" / "ledger").mkdir(parents=True)
for _pid, _model in (("PM-NEW", "modelB"), ("PM-OLD", "modelA")):  # OLD = later run-id
    (_mvroot / ".socom" / "promises" / f"{_pid}.xml").write_text(
        f'<promise id="{_pid}" domain="cli"><intent><verbatim>delta delta</verbatim></intent>'
        f'<contract ref="C"><goal>delta delta</goal></contract></promise>')
    (_mvroot / ".socom" / "runs" / f"R-{_pid}.json").write_text(_json.dumps({
        "run_id": f"R-{_pid}", "seat": "builder", "promise": _pid, "contract": "C",
        "runtime": "claude-code", "model": _model, "status": "dead",
        "ts_started": _mnow.isoformat(), "pid": None, "brief_path": "b",
        "promise_path": f".socom/promises/{_pid}.xml", "ts_ended": None, "exit_code": 137}))
# builder is 3-kept ONLY under modelA -> high trust for the modelA run, neutral for modelB
(_mvroot / ".socom" / "ledger" / "runs.jsonl").write_text("\n".join(_json.dumps(
    {"promise": "hx", "seat": "builder", "verdict": "kept", "model": "modelA"})
    for _ in range(3)) + "\n")
_mvelig, _ = socom.recoverable(_mvroot)
_mvrank, _ = socom._triage_rank(_mvroot, _mvelig, "delta")
eq("_triage_rank: the earned-model dead run outranks the upgraded-model one (trust is per-model)",
   _mvrank[0]["promise"], "PM-OLD")
eq("_triage_rank: the upgraded-model run resolves to the neutral prior (reset, not inherited)",
   next(r["trust"] for r in _mvrank if r["promise"] == "PM-NEW"), 0.5)

# ── per-seat envelope budget (slice 6) ───────────────────────────────────────
eq("_seat_budget: a positive int is used",
   socom._seat_budget({"context_budget": 600}, "reviewer"), 600)
eq("_seat_budget: absent -> the default",
   socom._seat_budget({}, "builder"), socom.ENVELOPE_DEFAULT_BUDGET_TOKENS)
eq("_seat_budget: explicit YAML null -> the default (unset, like absent)",
   socom._seat_budget({"context_budget": None}, "s"), socom.ENVELOPE_DEFAULT_BUDGET_TOKENS)
for _bad in (0, -5, "abc", 1.5, True):
    try:
        socom._seat_budget({"context_budget": _bad}, "s")
        check(f"_seat_budget: invalid {_bad!r} exits loud", False)
    except SystemExit:
        check(f"_seat_budget: invalid {_bad!r} exits loud", True)

# ── context emit per-seat budget default (slice 8) ───────────────────────────
# _seat_context_budget is the SINGLE validator both spawn and emit share. Unlike
# _seat_budget it returns None (not the default) when the field is absent, so emit
# can refuse to invent a recorded budget while spawn falls back to its advisory default.
eq("_seat_context_budget: a positive int is returned validated",
   socom._seat_context_budget({"context_budget": 600}, "reviewer"), 600)
eq("_seat_context_budget: absent -> None (NOT the default — emit distinguishes them)",
   socom._seat_context_budget({}, "builder"), None)
eq("_seat_context_budget: explicit YAML null -> None (unset, like absent)",
   socom._seat_context_budget({"context_budget": None}, "s"), None)
for _bad in (0, -5, "abc", 1.5, True):
    try:
        socom._seat_context_budget({"context_budget": _bad}, "s")
        check(f"_seat_context_budget: invalid {_bad!r} exits loud", False)
    except SystemExit:
        check(f"_seat_context_budget: invalid {_bad!r} exits loud", True)
# _seat_budget delegates to it: same validation, but None -> the advisory default.
eq("_seat_budget delegates to _seat_context_budget (declared value passes through)",
   socom._seat_budget({"context_budget": 42}, "s"), 42)
eq("_seat_budget: None from the validator -> the advisory default (spawn behavior)",
   socom._seat_budget({}, "s"), socom.ENVELOPE_DEFAULT_BUDGET_TOKENS)

# the budget actually bounds the envelope's lessons subsection (canon resolves from
# the embedded resources; lessons from the temp root).
_broot = Path(_tf.mkdtemp())
(_broot / ".socom" / "lessons").mkdir(parents=True)
for _i in range(4):
    (_broot / ".socom" / "lessons" / f"L-Q{_i}.xml").write_text(
        f'<lesson id="L-Q{_i}" domain="cli" state="active"><statement embed="true">'
        f'flock ledger writers serialize lesson {_i} ' + ("y" * 60) + "</statement></lesson>")
_big = socom._forge_operating_envelope(_broot, "cli", "flock ledger", "", 5000)
_small = socom._forge_operating_envelope(_broot, "cli", "flock ledger", "", 20)
check("_forge_operating_envelope: a larger budget carries more lessons",
      _big.count("**L-Q") > _small.count("**L-Q"))
check("_forge_operating_envelope: the tightest budget still keeps the top lesson",
      _small.count("**L-Q") >= 1)
check("_forge_operating_envelope: a trimmed envelope says what it dropped",
      "trimmed to the envelope budget" in _small)

# ── quickstart first-run on-ramp ─────────────────────────────────────────────
# _detect_checks: the repo test-command heuristic (priority Makefile>npm>pytest>cargo>go).
_qr = Path(_tf.mkdtemp())
eq("_detect_checks: empty repo -> None (degrade loudly, never invent)",
   socom._detect_checks(_qr), None)
(_qr / "go.mod").write_text("module x\n")
eq("_detect_checks: go.mod -> go test", socom._detect_checks(_qr), "go test ./...")
(_qr / "Cargo.toml").write_text("[package]\n")
eq("_detect_checks: Cargo.toml outranks go.mod", socom._detect_checks(_qr), "cargo test")
(_qr / "pyproject.toml").write_text("[project]\n")
eq("_detect_checks: a pytest signal outranks cargo", socom._detect_checks(_qr), "pytest -q")
(_qr / "package.json").write_text('{"scripts":{"test":"jest"}}')
eq("_detect_checks: package.json scripts.test outranks pytest",
   socom._detect_checks(_qr), "npm test")
(_qr / "Makefile").write_text("build:\n\tcc\ntest:\n\tpytest\n")
eq("_detect_checks: a Makefile `test:` target wins (most explicit)",
   socom._detect_checks(_qr), "make test")
# a package.json without a test script is not a hit on the npm rung
_qr2 = Path(_tf.mkdtemp())
(_qr2 / "package.json").write_text('{"name":"x"}')
eq("_detect_checks: package.json with no scripts.test is not an npm hit",
   socom._detect_checks(_qr2), None)
# a Makefile without a `test:` target is not a hit on the make rung
_qr3 = Path(_tf.mkdtemp())
(_qr3 / "Makefile").write_text("build:\n\tcc\n")
eq("_detect_checks: a Makefile with no test target is not a make hit",
   socom._detect_checks(_qr3), None)

# _bind_checks: writes the detected command into the placeholders, preserving comments,
# and never clobbers a real binding.
_qb = Path(_tf.mkdtemp())
(_qb / "socom.yaml").write_text(
    'checks:\n  fast: "true"    # runs at task-completion\n'
    '  medium: "true"\n  full: "true"\n')
check("_bind_checks: binds when all three are placeholders",
      socom._bind_checks(_qb, "pytest -q") is True)
_bound = (_qb / "socom.yaml").read_text()
check("_bind_checks: wrote the command into fast/medium/full",
      _bound.count('"pytest -q"') == 3)
check("_bind_checks: preserved the trailing comment (no yaml round-trip)",
      "# runs at task-completion" in _bound)
check("_bind_checks: a second bind is a no-op (already bound, no clobber)",
      socom._bind_checks(_qb, "make test") is False
      and '"make test"' not in (_qb / "socom.yaml").read_text())
# a partially-bound config is also left alone (never clobber a real value)
_qb2 = Path(_tf.mkdtemp())
(_qb2 / "socom.yaml").write_text('checks:\n  fast: "make real"\n  medium: "true"\n  full: "true"\n')
check("_bind_checks: any real binding present -> leave all as-is",
      socom._bind_checks(_qb2, "pytest -q") is False)
# section-scoped: a `fast:` key under a DIFFERENT section is never touched (reviewer C1)
_qb3 = Path(_tf.mkdtemp())
(_qb3 / "socom.yaml").write_text(
    'checks:\n  fast: "true"\n  medium: "true"\n  full: "true"\n'
    'tiers:\n  fast: "true"   # NOT a check — must survive untouched\n')
check("_bind_checks: binds only within the checks block",
      socom._bind_checks(_qb3, "pytest -q") is True)
_b3 = (_qb3 / "socom.yaml").read_text()
check("_bind_checks: the sibling section's fast: is left untouched (section-scoped)",
      _b3.count('"pytest -q"') == 3 and "NOT a check — must survive untouched" in _b3)
# unquoted YAML `true` (bool) is a placeholder AND gets really rewritten (reviewer C2 —
# no false 'bound' report: returns True only when it actually writes the command)
_qb4 = Path(_tf.mkdtemp())
(_qb4 / "socom.yaml").write_text('checks:\n  fast: true\n  medium: true\n  full: true\n')
check("_bind_checks: unquoted bool `true` is recognized and actually rewritten",
      socom._bind_checks(_qb4, "go test ./...") is True
      and (_qb4 / "socom.yaml").read_text().count('"go test ./..."') == 3
      and "fast: true\n" not in (_qb4 / "socom.yaml").read_text())

# _probe_count: 0 when absent, parses the planted probes.yaml
_qp = Path(_tf.mkdtemp())
eq("_probe_count: no probes file -> 0", socom._probe_count(_qp), 0)
(_qp / ".socom" / "index").mkdir(parents=True)
(_qp / ".socom" / "index" / "probes.yaml").write_text(
    "probes:\n  - query: a\n    expect: x\n  - query: b\n    expect: y\n")
eq("_probe_count: counts the probes on file", socom._probe_count(_qp), 2)

# ── help completeness (the guard that would have caught spawn/monarch/forge drift) ──
# every registered command MUST appear in the help text, else `socom` lies about its
# own surface — exactly how spawn/monarch/forge silently fell out of the listing.
_help = socom.__doc__ or ""
_listed = set(re.findall(r'^  (\w+)\s', _help, re.M))
_unlisted = sorted(c for c in socom.COMMANDS if c not in _listed)
check(f"help lists every registered command (unlisted: {_unlisted})", not _unlisted)

# ── summary ──────────────────────────────────────────────────────────────────
print(f"unit: {_PASS} passed, {_FAIL} failed")
raise SystemExit(1 if _FAIL else 0)
