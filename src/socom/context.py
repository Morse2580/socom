"""socom context — context envelopes (CTX). Assembled into bin/socom by build.py."""
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
from socom.core import SOCOM_DIR, SOCOM_VERSION, _now_iso, repo_root, resource
from socom.retrieval import l0_score

# === BODY ===

# ── context — the CTX-1/CTX-2 context envelope, made a first-class artifact ─
# Every work unit EMITS a schema-valid context envelope (.socom/context/<id>.xml,
# schemas/context.xml) declaring the input context it consumed against a declared
# budget. `socom context verify` IS the gate: exit 0 iff every targeted envelope
# is schema-valid AND input_tokens <= budget_tokens — fail-OPEN on an absent
# dir / no envelopes (lazy creation is not corruption), fail-CLOSED on any
# malformed or over-budget envelope. The field contract, the invariant AND the
# measurement divisor are SINGLE-SOURCED from schemas/context.xml (parsed, never
# hardcoded), exactly as ledgercheck derives the ledger contract from
# schemas/ledger.xml. The bands run this very verb (the tool verifies itself).
#   CTX-2 makes <inputs> load-bearing: `measure` writes per-ref token counts from
# the live artifacts, `verify` RE-MEASURES them and fails unless declared ==
# measured (un-forgeable input_tokens), and `compress` drops the lowest-relevance
# inputs (l0_score-ranked vs the promise goal) until the sum fits the budget.
# measure/compress MUTATE and are NOT gates (a gate that fixes its own failure is
# the separation-of-privilege trap); only verify is band-wired.
_INVARIANT_OPS = {"<=": lambda a, b: a <= b, "<": lambda a, b: a < b,
                  ">=": lambda a, b: a >= b, ">": lambda a, b: a > b,
                  "==": lambda a, b: a == b}


def _load_context_contract(schema=None):
    """Parse the context schema -> (required, int_fields, invariants, divisor,
    version). The <field> + <invariant> + <measurement> elements AND the schema's
    own socom= version ARE the contract; nothing is hardcoded (single source,
    §least-common-mechanism / open-design). An invariant rhs may name an int field
    OR be an int literal (so a lower bound like input_tokens >= 0 reuses the same
    mechanism rather than a bespoke check). schema=None reads the SHIPPED schema
    (embedded in the distributed file, or schemas/context.xml from a checkout); a
    path may be passed to validate against an alternative schema (tests)."""
    root = (ET.parse(schema).getroot() if schema is not None
            else ET.fromstring(resource("schemas/context.xml")))
    version = root.get("socom")  # the contract version an envelope must declare
    required = [f.get("name") for f in root.find("fields").findall("field")
                if f.get("required") == "true"]
    ints = [f.get("name") for f in root.find("fields").findall("field")
            if f.get("type") == "int"]
    inv_block = root.find("invariants")
    invariants = [(i.get("lhs"), i.get("op"), i.get("rhs"))
                  for i in inv_block.findall("invariant")] if inv_block is not None else []
    m = root.find("measurement")
    raw = m.get("divisor") if m is not None else None
    try:
        divisor = int(raw)
        if divisor <= 0:
            raise ValueError
    except (TypeError, ValueError):
        # The estimator divisor is single-sourced from the schema; a schema that
        # lacks a valid <measurement divisor> must FAIL, not silently default — a
        # rule that evaporates on a schema edit is a §degrade-loudly breach (R6),
        # the same class the CTX-1 reviewer caught on the invariant op.
        sys.exit("socom context: schemas/context.xml has no valid "
                 "<measurement divisor=\"N\"> (positive int) — cannot measure "
                 "honestly (R6: degrade loudly).")
    return required, ints, invariants, divisor, version


def _estimate_tokens(text, divisor):
    """Deterministic, offline token ESTIMATE: round(len(text) / divisor) — the
    OpenAI ~4-chars/token rule, divisor single-sourced from the schema's
    <measurement>. A lower bound: it UNDER-counts code/structured text, so budgets
    carry headroom. Not a model-exact tokenizer (BPE is CTX-3, behind this seam)."""
    return round(len(text) / divisor)


def _read_ref(repo, ref):
    """Read one input ref's live text -> str, or None if it does not resolve / is
    unreadable / ESCAPES the repo tree. ref is a repo-relative path in CTX-2.1
    (id-only refs are CTX-3). Containment is a hard boundary: a ref that resolves
    outside the repo — a ../ escape, an absolute path, or an in-repo symlink that
    points out (.resolve() follows it) — reads as None, so a crafted envelope can
    never make measure/verify read or size-leak an arbitrary file (path traversal)."""
    p = Path(ref)
    if not p.is_absolute():
        p = repo / ref
    try:
        rp = p.resolve()
        if not rp.is_relative_to(repo.resolve()):
            return None  # escapes the repo tree — refuse, don't read
        return rp.read_text()
    except (OSError, UnicodeDecodeError, ValueError):
        return None


def _measure_ref(repo, ref, divisor):
    """Re-measure one input ref from the LIVE artifact -> token estimate, or None
    if it does not resolve / is unreadable (a violation — degrade loudly, R6)."""
    text = _read_ref(repo, ref)
    return None if text is None else _estimate_tokens(text, divisor)


def _context_violations(path, required, ints, invariants, repo=None, divisor=4,
                        version=None):
    """Return a list of violation strings for one envelope file (empty = ok).
    When repo is given and the envelope carries <inputs>, the CTX-2 honesty check
    RE-MEASURES every ref from the live artifact: each declared <input tokens> and
    the top-level input_tokens must equal the re-measure, or the gate fails — so a
    hand-authored input_tokens cannot pass. repo=None skips the re-measure (used by
    schema-only unit checks); the verify gate always passes it. When version is
    given, the envelope's socom= must match it (the contract it was written for)."""
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError) as e:
        return [f"not well-formed XML — {e}"]
    if root.tag != "context":
        return [f"root element is <{root.tag}>, expected <context>"]
    bad, vals = [], {}
    # Contract version: an envelope written for a different socom= than the schema
    # declares cannot be trusted against this contract — reject rather than guess.
    if version is not None and root.get("socom") != version:
        bad.append(f"socom={root.get('socom')!r} does not match the schema "
                   f"contract version {version!r}")
    for key in required:
        if root.get(key) is None:
            bad.append(f"missing required attribute {key!r}")
    for key in ints:
        raw = root.get(key)
        if raw is None:
            continue  # a required int already reported missing above
        try:
            vals[key] = int(raw)
        except ValueError:
            bad.append(f"{key}={raw!r} is not an int")
    for lhs, op, rhs in invariants:
        if op not in _INVARIANT_OPS:
            # An invariant the verifier cannot evaluate must FAIL, never silently
            # skip — a schema-declared rule that evaporates is a §degrade-loudly
            # breach (R6) and a false PASS waiting on the next schema edit.
            bad.append(f"schema invariant op {op!r} is not recognized "
                       f"({lhs} {op} {rhs}) — cannot evaluate, failing closed")
            continue
        if lhs not in vals:
            continue  # lhs absent/non-int already reported; nothing to compare
        # rhs is a populated int field, a declared-but-missing int field (skip —
        # already reported), or an int literal (e.g. a >= 0 lower bound). Anything
        # else is an unevaluable schema rule -> fail closed (degrade loudly, R6).
        if rhs in vals:
            rval = vals[rhs]
        elif rhs in ints:
            continue
        else:
            try:
                rval = int(rhs)
            except (TypeError, ValueError):
                bad.append(f"schema invariant rhs {rhs!r} is neither an int field "
                           f"nor an int literal ({lhs} {op} {rhs}) — cannot "
                           f"evaluate, failing closed")
                continue
        if not _INVARIANT_OPS[op](vals[lhs], rval):
            bad.append(f"invariant violated: {lhs}({vals[lhs]}) {op} "
                       f"{rhs}({rval}) is false")
    # CTX-2 honesty check: re-measure the <inputs> refs from the live artifacts and
    # require declared == measured, per-input AND in total. Only when the envelope
    # carries <inputs> (a CTX-1 envelope omits it and keeps the declared<=budget
    # check above — backward compatible).
    inputs_el = root.find("inputs")
    if inputs_el is not None and repo is not None:
        total = 0
        for inp in inputs_el.findall("input"):
            ref = inp.get("ref")
            if not ref:
                bad.append("an <input> is missing its 'ref' attribute")
                continue
            measured = _measure_ref(repo, ref, divisor)
            if measured is None:
                bad.append(f"input ref {ref!r} does not resolve or is unreadable")
                continue
            total += measured
            raw = inp.get("tokens")
            try:
                declared = int(raw) if raw is not None else None
            except ValueError:
                declared = None
            if declared is None:
                bad.append(f"input ref {ref!r}: 'tokens' missing or non-int")
            elif declared != measured:
                bad.append(f"input ref {ref!r}: declared tokens={declared} "
                           f"!= re-measured {measured} (stale — run measure)")
        if "input_tokens" in vals and total != vals["input_tokens"]:
            bad.append(f"input_tokens={vals['input_tokens']} != sum of re-measured "
                       f"inputs {total} (run `socom context measure`)")
    return bad


def _context_targets(target):
    """A file -> [file]; a dir -> its *.xml; absent -> [] (fail-open on absence,
    the same posture ledgercheck gives an absent ledger)."""
    if target.is_file():
        return [target]
    if target.is_dir():
        return sorted(target.glob("*.xml"))
    return []


def _promise_goal_text(repo, pid):
    """Best-effort: the referenced promise's goal/intent text, for ranking inputs
    by relevance in `compress`. Globs .socom/promises and matches on the id attr;
    returns '' if unresolvable (compress then falls back to drop-largest)."""
    if not pid:
        return ""
    d = repo / SOCOM_DIR / "promises"
    if not d.is_dir():
        return ""
    for f in sorted(d.glob("*.xml")):
        try:
            el = ET.parse(f).getroot()
        except (ET.ParseError, OSError):
            continue
        if el.get("id") != pid:
            continue
        parts = [e.text for tag in ("goal", "intent", "decoded", "verbatim")
                 for e in el.iter(tag) if e.text]
        return " ".join(parts)
    return ""


def _write_envelope(tree, target):
    """Serialize a mutated envelope back to disk (UTF-8 + xml declaration). ET
    drops comments and normalizes whitespace — fine for a data envelope, which is
    measured/compressed/emitted output, not hand-tended canon."""
    tree.write(str(target), encoding="UTF-8", xml_declaration=True)


def _next_context_id(root, date):
    """Next free envelope id CTX-<date>-<NNN> (3-digit seq) in .socom/context —
    scans existing files for the date so two emits the same day don't collide."""
    d = root / SOCOM_DIR / "context"
    prefix = f"CTX-{date}-"
    seq = 0
    if d.is_dir():
        for f in d.glob(f"{prefix}*.xml"):
            m = re.match(rf"{re.escape(prefix)}(\d+)$", f.stem)
            if m:
                seq = max(seq, int(m.group(1)))
    return f"{prefix}{seq + 1:03d}"


def _emit_flags(args):
    """Parse the emit flag args -> dict. Repeatable --input accumulates; every
    flag needs a value (degrade loudly on a dangling flag, R6)."""
    out = {"input": []}
    flags = {"--promise": "promise", "--seat": "seat", "--budget": "budget",
             "--id": "id", "--out": "out", "--input": "input"}
    i = 0
    while i < len(args):
        tok = args[i]
        if tok not in flags:
            sys.exit(f"socom context emit: unexpected argument {tok!r} — usage: "
                     "context emit --promise P --seat S --budget N "
                     "[--input PATH ...] [--id ID] [--out PATH] (R6).")
        if i + 1 >= len(args):
            sys.exit(f"socom context emit: {tok} needs a value (R6).")
        val = args[i + 1]
        key = flags[tok]
        if key == "input":
            out["input"].append(val)
        else:
            if key in out:
                sys.exit(f"socom context emit: {tok} given more than once — "
                         "ambiguous intent (R6).")
            out[key] = val
        i += 2
    return out


def _cmd_context_emit(root, args):
    """PRODUCER (CTX-3 slice): write a measured, schema-valid envelope so the gate
    has real input. emit RECORDS the truth — it is NOT a gate: an over-budget work
    unit is written honestly (warn + point at compress, exit 0), because hiding an
    over-budget reality defeats the failure CTX exists to catch (separation of
    privilege; verify judges, compress remediates). A schema-invalid self-build
    (a tool bug, should never happen) exits nonzero — degrade loudly (R6)."""
    required, ints, invariants, divisor, version = _load_context_contract()
    f = _emit_flags(args)
    # Friction: a session exports $SOCOM_PROMISE + $SOCOM_SEAT once, then every
    # emit is just `--budget --input …`. Lowering the cost is how emit actually
    # gets RUN — a producer nobody invokes leaves the gate dormant.
    seat = f.get("seat") or os.environ.get("SOCOM_SEAT")
    promise = f.get("promise") or os.environ.get("SOCOM_PROMISE")
    missing = [n for n, v in (("--promise", promise),
                              ("--seat", seat),
                              ("--budget", f.get("budget"))) if not v]
    if missing:
        sys.exit(f"socom context emit: {', '.join(missing)} required "
                 "(promise/seat may come from $SOCOM_PROMISE / $SOCOM_SEAT) (R6).")
    try:
        budget = int(f["budget"])
        if budget < 0:
            raise ValueError
    except ValueError:
        sys.exit(f"socom context emit: --budget {f['budget']!r} is not a "
                 "non-negative int (R6).")

    date = datetime.now(timezone.utc).strftime("%Y-%m%d")
    cid = f.get("id") or _next_context_id(root, date)
    out = Path(f["out"]) if f.get("out") else root / SOCOM_DIR / "context" / f"{cid}.xml"
    if not out.is_absolute():
        out = root / out
    # OUTPUT containment — the same hard boundary _read_ref gives inputs, now on the
    # WRITE side: --id and --out both feed the filename, so a crafted --id
    # (../../../tmp/x) or absolute --out could write/clobber an arbitrary file
    # outside the repo. Resolve and refuse anything that escapes the tree (the CTX-2
    # reviewer caught this class on inputs; it is symmetric on outputs).
    if not out.resolve().is_relative_to(root.resolve()):
        sys.exit(f"socom context emit: output path {out} resolves outside the repo "
                 "tree (--id / --out may not escape) — refusing (R6 path containment).")

    # Measure every input ref from the LIVE artifact (CTX-2 path). A ref that does
    # not resolve / is unreadable / escapes the repo is refused — no partial write.
    measured = []
    total = 0
    for ref in f["input"]:
        m = _measure_ref(root, ref, divisor)
        if m is None:
            sys.exit(f"socom context emit: input ref {ref!r} does not resolve, is "
                     "unreadable, or escapes the repo tree — cannot measure "
                     "honestly (R6).")
        measured.append((ref, m))
        total += m

    el = ET.Element("context", {
        "socom": SOCOM_VERSION, "id": cid, "promise": promise,
        "seat": seat, "ts": _now_iso(),
        "budget_tokens": str(budget), "input_tokens": str(total)})
    if measured:
        ins = ET.SubElement(el, "inputs")
        for ref, m in measured:
            ET.SubElement(ins, "input", {"ref": ref, "tokens": str(m)})

    # Validate-before-publish: write a sibling temp, self-check it against the SAME
    # contract the gate uses (re-measure included), and only os.replace it into place
    # if it is publishable. An over-budget envelope IS publishable (emit records
    # truth; verify judges it) — only a schema-INVALID build (a tool bug, should
    # never happen) is discarded, so a bad write never lands in .socom/context even
    # momentarily (R6: no partial/torn artifact). os.replace is atomic on POSIX.
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(out.name + ".tmp")
    _write_envelope(ET.ElementTree(el), tmp)
    viols = _context_violations(tmp, required, ints, invariants, root, divisor, version)
    # "budget_only" means the SOLE failure is the <= budget invariant (publish
    # honestly + warn). Match that invariant specifically — a >= 0 lower-bound
    # violation is a correctness fault, not a budget overage, and must fail closed
    # (it is unreachable today since measures are >= 0, but don't let the label
    # silently widen to it).
    budget_only = bool(viols) and all(
        ("invariant violated" in v and "<=" in v and "budget_tokens" in v)
        for v in viols)
    if viols and not budget_only:
        tmp.unlink(missing_ok=True)
        for v in viols:
            print(f"  {v}", file=sys.stderr)
        sys.exit("socom context emit: built an envelope that fails its own schema "
                 "(above) — refusing to publish a bad write (R6).")
    os.replace(tmp, out)

    rel = out.relative_to(root)
    print(f"socom context emit: wrote {rel} — promise={promise} seat={seat} "
          f"input_tokens={total}/{budget} across {len(measured)} input(s) "
          f"(chars/{divisor} estimate).")
    if budget_only:
        print(f"socom context emit: WARNING — input_tokens {total} > budget "
              f"{budget}; `socom context verify` will FAIL this envelope until you "
              f"run `socom context compress {rel}`.", file=sys.stderr)


def _cmd_context_verify(root, args):
    """Read-only gate: validate every targeted envelope against the schema (and the
    CTX-2 re-measure of <inputs>). `--require <P-id[,P-id…]>` additionally asserts
    that each named promise has at least one VALID envelope referencing it — the
    opt-in CTX-4 precursor that makes per-work-unit emission CHECKABLE. It is
    fail-CLOSED on a named-but-unfulfilled promise, while the DEFAULT (no --require)
    keeps the fail-OPEN posture on an empty dir (lazy creation is not corruption)."""
    require, pos, i = [], [], 0
    while i < len(args):
        tok = args[i]
        if tok == "--require":
            if i + 1 >= len(args):
                sys.exit("socom context verify: --require needs a value "
                         "(P-id[,P-id…]) (R6).")
            # Strip each id so " P-A " matches promise="P-A"; reject a value that
            # yields NO ids (e.g. "," or "  ") rather than silently acting as if
            # --require was never given — a false green (R6).
            val = args[i + 1]
            ids = [p.strip() for p in val.split(",") if p.strip()]
            if not ids:
                sys.exit(f"socom context verify: --require {val!r} has no promise "
                         "ids after splitting on ',' — stray commas or whitespace? "
                         "(R6).")
            require += ids
            i += 2
        elif tok.startswith("--"):
            # An unknown flag must not silently fall through to a positional target
            # (a typo'd --requre would otherwise become a non-existent path and
            # pass fail-open, dropping the operator's assertion) — degrade loudly.
            sys.exit(f"socom context verify: unknown flag {tok!r} — usage: verify "
                     "[<envelope.xml|dir>] [--require P-id[,P-id…]] (R6).")
        else:
            pos.append(tok)
            i += 1
    raw = pos[0] if pos else f"{SOCOM_DIR}/context"
    target = Path(raw)
    if not target.is_absolute():
        target = root / raw

    required, ints, invariants, divisor, version = _load_context_contract()
    files = _context_targets(target)
    fulfilled, bad = set(), 0
    if not files:
        print(f"socom context verify: no envelopes at {raw} — nothing to "
              "validate (created lazily on first emit).")
    else:
        for f in files:
            viols = _context_violations(f, required, ints, invariants, root,
                                        divisor, version)
            if viols:
                bad += 1
                print(f"  {f.name} · FAIL")
                for v in viols:
                    print(f"    {v}", file=sys.stderr)
            else:
                print(f"  {f.name} · PASS")
                if require:  # only re-parse when --require needs the promise map
                    try:
                        pid = (ET.parse(f).getroot().get("promise") or "").strip()
                        if pid:
                            fulfilled.add(pid)
                    except (ET.ParseError, OSError):
                        pass  # a PASS file is parseable; defensive only
        print(f"socom context verify: {len(files) - bad} valid, {bad} invalid of "
              f"{len(files)} envelope(s) -> {'OK' if not bad else 'FAILED'}")

    missing = [p for p in require if p not in fulfilled]
    for p in missing:
        print(f"socom context verify: REQUIRED promise {p} has no valid context "
              "envelope — a work unit ran without recording the context it "
              "consumed (R6).", file=sys.stderr)
    if bad or missing:
        sys.exit(1)
    if require:
        print(f"socom context verify: all {len(require)} required promise(s) carry "
              "a valid context envelope.")


def cmd_context(args):
    subs = ("verify", "show", "measure", "compress", "emit")
    if not args or args[0] not in subs:
        sys.exit("usage: socom context <verify|show|measure|compress|emit> "
                 "[<envelope.xml|dir>]  (verify defaults to .socom/context and "
                 "takes --require P-id[,P-id…]; measure/compress need one envelope "
                 "file; emit takes flags — --promise --seat --budget --input ... "
                 "--id --out)")
    sub = args[0]
    root = repo_root()

    if sub == "emit":
        return _cmd_context_emit(root, args[1:])
    if sub == "verify":
        return _cmd_context_verify(root, args[1:])

    raw = args[1] if len(args) > 1 else f"{SOCOM_DIR}/context"
    target = Path(raw)
    if not target.is_absolute():
        target = root / raw

    if sub == "show":
        if not target.is_file():
            sys.exit(f"socom context show: no such envelope '{raw}' "
                     "(R6: degrade loudly).")
        try:
            el = ET.parse(target).getroot()
        except (ET.ParseError, OSError) as e:
            sys.exit(f"socom context: {target.name} is not readable "
                     f"well-formed XML — {e}")
        print(f"socom context {el.get('id', '?')} [{target.name}]")
        print(f"  promise: {el.get('promise', '?')}  seat: {el.get('seat', '?')}")
        print(f"  budget:  {el.get('input_tokens', '?')} / "
              f"{el.get('budget_tokens', '?')} tokens (consumed / declared)")
        ins = el.find("inputs")
        if ins is not None:
            for inp in ins.findall("input"):
                print(f"    input {inp.get('ref', '?')} · {inp.get('tokens', '?')} tokens")
        return

    if sub == "measure":
        # Writer: refresh per-input + total token counts FROM the live refs so the
        # author can declare them honestly. Mutates the envelope. No <inputs> ->
        # nothing to measure (a CTX-1 envelope declares input_tokens by hand).
        _, _, _, divisor, _ = _load_context_contract()
        if not target.is_file():
            sys.exit(f"socom context measure: need one envelope file, not '{raw}' (R6).")
        try:
            tree = ET.parse(target)
        except (ET.ParseError, OSError) as e:
            sys.exit(f"socom context measure: {target.name} is not readable "
                     f"well-formed XML — {e}")
        el = tree.getroot()
        ins = el.find("inputs")
        if ins is None or not ins.findall("input"):
            sys.exit("socom context measure: envelope has no <inputs> to measure "
                     "(R6: nothing to do).")
        total = 0
        for inp in ins.findall("input"):
            ref = inp.get("ref")
            m = _measure_ref(root, ref, divisor) if ref else None
            if m is None:
                sys.exit(f"socom context measure: input ref {ref!r} does not "
                         "resolve or is unreadable — cannot measure honestly (R6).")
            inp.set("tokens", str(m))
            total += m
        el.set("input_tokens", str(total))
        _write_envelope(tree, target)
        print(f"socom context measure: {target.name} -> input_tokens={total} "
              f"across {len(ins.findall('input'))} input(s) (chars/{divisor} "
              "estimate — a lower bound, not a model-exact count).")
        return

    if sub == "compress":
        # Remediation: drop the lowest-relevance inputs until the re-measured total
        # fits budget_tokens. Relevance = l0_score overlap vs the promise goal;
        # falls back to drop-largest when the promise is unresolvable. Mutates.
        _, _, _, divisor, _ = _load_context_contract()
        if not target.is_file():
            sys.exit(f"socom context compress: need one envelope file, not '{raw}' (R6).")
        try:
            tree = ET.parse(target)
        except (ET.ParseError, OSError) as e:
            sys.exit(f"socom context compress: {target.name} is not readable "
                     f"well-formed XML — {e}")
        el = tree.getroot()
        ins = el.find("inputs")
        if ins is None or not ins.findall("input"):
            sys.exit("socom context compress: envelope has no <inputs> to compress (R6).")
        try:
            budget = int(el.get("budget_tokens"))
        except (TypeError, ValueError):
            sys.exit("socom context compress: budget_tokens missing or non-int (R6).")
        inps = ins.findall("input")
        sized = {}
        for inp in inps:
            text = _read_ref(root, inp.get("ref"))
            if text is None:
                sys.exit(f"socom context compress: input ref {inp.get('ref')!r} "
                         "does not resolve or is unreadable (R6).")
            sized[inp] = (text, _estimate_tokens(text, divisor))
        total = sum(t for _, t in sized.values())
        if total <= budget:
            print(f"socom context compress: already within budget "
                  f"({total} <= {budget}) — nothing to drop.")
            return
        query = _promise_goal_text(root, el.get("promise"))
        if query:
            # chunk "id" is the index into inps BY CONVENTION (enumerate) — l0_score
            # returns ids ranked most-relevant-first, so inps[id] maps back and the
            # reverse is least-relevant-first (what we drop). Keep id == index.
            chunks = [{"id": i, "text": sized[inp][0]} for i, inp in enumerate(inps)]
            ranked = l0_score(query, chunks, k=len(chunks))  # most relevant first
            order = [inps[i] for i in reversed(ranked)]       # least relevant first
        else:
            order = sorted(inps, key=lambda inp: -sized[inp][1])  # largest first
        kept, dropped, running = list(inps), [], total
        for victim in order:
            if running <= budget or len(kept) <= 1:
                break
            kept.remove(victim)
            dropped.append(victim)
            running -= sized[victim][1]
        for victim in dropped:
            ins.remove(victim)
        el.set("input_tokens", str(running))
        _write_envelope(tree, target)
        how = "relevance vs promise goal" if query else "size (no promise goal found)"
        print(f"socom context compress: {target.name} {total} -> {running} tokens "
              f"(budget {budget}); dropped {len(dropped)} input(s) by {how}:")
        for victim in dropped:
            print(f"    - {victim.get('ref')} ({sized[victim][1]} tokens)")
        if running > budget:
            print(f"socom context compress: WARNING — still {running} > {budget}; the "
                  "single most-relevant input alone exceeds budget. Tail-truncation "
                  "is CTX-3; raise the budget or split the input.", file=sys.stderr)
            sys.exit(1)
        return
