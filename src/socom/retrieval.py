"""socom retrieval — index / embed / query / eval / cycle. Assembled into bin/socom by build.py."""
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
from socom.core import SOCOM_DIR, SOCOM_VERSION, _now_iso, repo_root

# === BODY ===

# HR6: redaction at the substrate boundary — index/hydrate refuse
# secret-shaped content. Focused patterns; full PII taxonomy is roadmap.
SECRET_RX = re.compile(
    r"(-----BEGIN [A-Z ]*PRIVATE KEY|AKIA[0-9A-Z]{16}|xox[baprs]-[A-Za-z0-9-]+"
    r"|ghp_[A-Za-z0-9]{36}|glpat-[A-Za-z0-9_-]{20}|eyJ[A-Za-z0-9_-]{30,}"
    r"|(?:password|passwd|secret|token|api[_-]?key)\s*[:=]\s*['\"]?[^\s'\"]{8,})",
    re.IGNORECASE)


# ── hydrate ──────────────────────────────────────────────────────────────

def cmd_hydrate(args):
    root = repo_root(Path(args[0]) if args else None)
    slug = str(root).replace("/", "-").replace(".", "-")
    dest = Path.home() / ".claude" / "projects" / slug / "memory"
    dest.mkdir(parents=True, exist_ok=True)
    src = root / SOCOM_DIR / "memory"
    n = 0
    for f in (src / "memories").glob("*.md"):
        text = f.read_text()
        if SECRET_RX.search(text):  # HR6
            print(f"  REFUSED {f.name}: secret-shaped content — redact before "
                  f"hydrating", file=sys.stderr)
            continue
        (dest / f.name).write_text(text)
        n += 1
    # HR2 applies here too (pilot finding, mwingz 2026-06-12): a developer's
    # existing MEMORY.md must survive hydration. socom owns only its marked
    # block; everything outside it is preserved verbatim.
    idx = src / "INDEX.md"
    if idx.exists():
        block = ("<!-- socom:hydrated section — managed by `socom hydrate`, "
                 "edits above survive -->\n"
                 + idx.read_text().replace("memories/", "")
                 + "\n<!-- /socom:hydrated -->\n")
        mem_md = dest / "MEMORY.md"
        if mem_md.exists():
            cur = mem_md.read_text()
            if "<!-- socom:hydrated" in cur:
                cur = re.sub(r"<!-- socom:hydrated.*?/socom:hydrated -->\n?",
                             block, cur, flags=re.DOTALL)
            else:
                cur = cur.rstrip() + "\n\n" + block
            mem_md.write_text(cur)
        else:
            mem_md.write_text(block)
    print(f"socom: hydrated {n} memories + index -> {dest}")


# ── index ────────────────────────────────────────────────────────────────

def cmd_index(args):
    import json
    root = repo_root(Path(args[0]) if args else None)
    out = root / SOCOM_DIR / "index" / "chunks.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    chunks = []
    for f in sorted((root / SOCOM_DIR).rglob("*.xml")):
        try:
            tree = ET.parse(f)
        except ET.ParseError as e:
            print(f"  skip {f}: {e}", file=sys.stderr)
            continue
        art = tree.getroot()

        # Identity per STORAGE.md: chunk_id is the FULL element path with id
        # attributes (ancestors included), so sibling concepts never collide
        # and rewording a chunk keeps its identity. Ancestor attrs (id, state,
        # lineage...) inherit into metadata so filters work on leaf chunks.
        def walk(el, path, inherited):
            seg = el.tag + (f".{el.get('id')}" if el.get("id") else "")
            path = f"{path}/{seg}" if path else seg
            meta = {**inherited, **{k: v for k, v in el.attrib.items()
                                    if k != "embed"}}
            if el.get("embed") == "true" and (el.text or "").strip():
                if SECRET_RX.search(el.text):  # HR6
                    print(f"  REDACTED {f.relative_to(root)}#{path}: "
                          f"secret-shaped content not indexed", file=sys.stderr)
                else:
                    text = textwrap.dedent(el.text).strip()
                    chunks.append({
                        "id": f"{f.relative_to(root)}#{path}",
                        "artifact_id": str(f.relative_to(root)),
                        "artifact": art.tag,
                        "element": el.tag,
                        "text": text,
                        "content_sha": hashlib.sha256(
                            " ".join(text.split()).encode()).hexdigest()[:16],
                        "metadata": meta,
                    })
            for child in el:
                walk(child, path, meta)

        walk(art, "", {})

    # The memory bank is markdown (frontmatter + body) — pilot finding #2
    # (mwingz): un-indexed memories made the bank invisible to query. Each
    # memory contributes its description and body as chunks; frontmatter
    # becomes filter metadata (state drives the lifecycle filter).
    for f in sorted((root / SOCOM_DIR / "memory" / "memories").glob("*.md")):
        text = f.read_text()
        fm, body = {}, text
        m = re.match(r"\A---\n(.*?)\n---\n(.*)\Z", text, re.DOTALL)
        if m:
            try:
                fm = yaml.safe_load(m.group(1)) or {}
            except yaml.YAMLError:
                fm = {}
            body = m.group(2).strip()
        meta = {k: str(v) for k, v in fm.items()
                if k in ("type", "lifecycle", "state", "originSession")}
        rel = f.relative_to(root)
        for element, payload in (("description", str(fm.get("description", ""))),
                                 ("body", body)):
            if not payload.strip():
                continue
            if SECRET_RX.search(payload):
                print(f"  REDACTED {rel}#{element}: secret-shaped content "
                      f"not indexed", file=sys.stderr)
                continue
            chunks.append({
                "id": f"{rel}#{element}",
                "artifact_id": str(rel),
                "artifact": "memory",
                "element": element,
                "text": payload.strip(),
                "content_sha": hashlib.sha256(
                    " ".join(payload.split()).encode()).hexdigest()[:16],
                "metadata": meta,
            })
    with out.open("w") as fh:
        for c in chunks:
            fh.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"socom: indexed {len(chunks)} chunks -> {out}")
    return chunks


# ── L1 retrieval — naive RAG, offline and deterministic ─────────────────
# Ranker: BM25 over the post-redaction chunk registry. Pure stdlib — no
# vendor, no keys, no network — so the seat is fillable anywhere; an external
# embedding model is a pluggable upgrade (L2 hybrid), never a dependency.
# The L0 keyword floor remains mandatory (R6): query degrades to it when the
# vector index is absent, loudly.

BM25_K1, BM25_B = 1.5, 0.75


EXCLUDED_STATES = {"retired", "superseded", "broken"}


def tokenize(text: str) -> list:
    return re.findall(r"\w+", text.lower())


def load_chunks(root: Path) -> list:
    import json
    f = root / SOCOM_DIR / "index" / "chunks.jsonl"
    if not f.exists():
        sys.exit("socom: no chunk index — run `socom index` first")
    return [json.loads(ln) for ln in f.read_text().splitlines() if ln.strip()]


def cmd_embed(args):
    """Build the L1 index (term stats) from the post-redaction registry."""
    import json, math, time
    root = repo_root(Path(args[0]) if args else None)
    t0 = time.monotonic()
    chunks = cmd_index([str(root)])  # always rebuilt from canonical, fresh
    docs = {c["id"]: tokenize(c["text"]) for c in chunks}
    df: dict = {}
    for toks in docs.values():
        for t in set(toks):
            df[t] = df.get(t, 0) + 1
    n = len(docs)
    avgdl = sum(len(t) for t in docs.values()) / max(n, 1)
    index = {
        "socom": SOCOM_VERSION, "ranker": f"bm25(k1={BM25_K1},b={BM25_B})",
        "built_at": _now_iso(),
        "n_docs": n, "avgdl": round(avgdl, 2),
        "idf": {t: round(math.log((n - d + 0.5) / (d + 0.5) + 1), 6)
                for t, d in df.items()},
        "docs": {cid: {"len": len(toks),
                       "tf": {t: toks.count(t) for t in set(toks)}}
                 for cid, toks in docs.items()},
    }
    out = root / SOCOM_DIR / "index" / "vectors.json"
    out.write_text(json.dumps(index) + "\n")
    print(f"socom embed: BM25 index over {n} chunks, {len(df)} terms, "
          f"{time.monotonic() - t0:.3f}s -> {out}")


def l1_score(query: str, index: dict, k: int = 5,
             allowed_ids=None) -> list:
    q = tokenize(query)
    idf, docs, avgdl = index["idf"], index["docs"], index["avgdl"]
    scored = []
    for cid, d in docs.items():
        if allowed_ids is not None and cid not in allowed_ids:
            continue
        s = 0.0
        for t in q:
            tf = d["tf"].get(t)
            if tf and t in idf:
                s += idf[t] * tf * (BM25_K1 + 1) / (
                    tf + BM25_K1 * (1 - BM25_B + BM25_B * d["len"] / avgdl))
        if s > 0:
            scored.append((s, cid))
    scored.sort(key=lambda x: -x[0])
    return [cid for _, cid in scored[:k]]


def live_chunk_ids(chunks: list) -> set:
    """Lifecycle filter: never surface retired/superseded/broken artifacts."""
    return {c["id"] for c in chunks
            if c["metadata"].get("state") not in EXCLUDED_STATES}


def cmd_query(args):
    import json
    k = 5
    if "-k" in args:
        i = args.index("-k")
        k = int(args[i + 1])
        args = args[:i] + args[i + 2:]
    if not args:
        sys.exit('usage: socom query "<question>" [-k N]')
    q = " ".join(args)
    root = repo_root()
    chunks = load_chunks(root)
    by_id = {c["id"]: c for c in chunks}
    allowed = live_chunk_ids(chunks)
    vf = root / SOCOM_DIR / "index" / "vectors.json"
    if vf.exists():
        level, top = "L1/bm25", l1_score(q, json.loads(vf.read_text()), k, allowed)
    else:  # R6: the floor is mandatory and the degrade is loud
        print("socom query: vector index absent — degraded to L0 keyword floor "
              "(run `socom embed`)", file=sys.stderr)
        level, top = "L0/keyword", [cid for cid in l0_score(q, chunks, k * 2)
                                    if cid in allowed][:k]
    print(f"socom query [{level}] — {q!r}")
    for rank, cid in enumerate(top, 1):
        c = by_id[cid]
        first = " ".join(c["text"].split())[:110]
        meta = c["metadata"]
        prov = ",".join(f"{a}={meta[a]}" for a in ("state", "lineage", "domain")
                        if meta.get(a))
        print(f"  {rank}. {cid}" + (f"  [{prov}]" if prov else ""))
        print(f"     {first}{'…' if len(c['text']) > 110 else ''}")


def cmd_eval(args):
    """The L1 acceptance gate: same probes, hit@5 >= L0 AND MRR@5 strictly
    greater, latency within budget, zero redaction violations. RED on fail —
    verify-never-claim applied to retrieval itself."""
    import json, time
    root = repo_root(Path(args[0]) if args else None)
    chunks = load_chunks(root)
    allowed = live_chunk_ids(chunks)
    vf = root / SOCOM_DIR / "index" / "vectors.json"
    if not vf.exists():
        sys.exit("socom eval: no L1 index — run `socom embed` first")
    index = json.loads(vf.read_text())
    probes = yaml.safe_load(
        (root / SOCOM_DIR / "index" / "probes.yaml").read_text()).get("probes", [])
    if len(probes) < 12:
        sys.exit(f"socom eval: RED — contract requires >=12 probes, found "
                 f"{len(probes)}; a saturated floor proves nothing")

    def run(scorer):
        hits, rr, t0 = 0, 0.0, time.monotonic()
        rows = []
        for p in probes:
            top = scorer(p["query"])
            rank = next((i for i, cid in enumerate(top, 1)
                         if p["expect"] in cid), None)
            hits += rank is not None
            rr += 1 / rank if rank else 0.0
            rows.append({"query": p["query"], "expect": p["expect"],
                         "rank": rank})
        return {"hit_at_5": hits, "mrr_at_5": round(rr / len(probes), 4),
                "latency_s": round(time.monotonic() - t0, 4), "rows": rows}

    l0 = run(lambda q: [c for c in l0_score(q, chunks, 10) if c in allowed][:5])
    l1 = run(lambda q: l1_score(q, index, 5, allowed))

    # redaction violations: any indexed text matching the secret scan = fail
    violations = sum(1 for c in chunks if SECRET_RX.search(c["text"]))
    budget = max(0.5, 2 * l0["latency_s"] + 0.5)
    verdict = {
        "hit_not_worse": l1["hit_at_5"] >= l0["hit_at_5"],
        "mrr_strictly_better": l1["mrr_at_5"] > l0["mrr_at_5"],
        "latency_in_budget": l1["latency_s"] <= budget,
        "zero_redaction_violations": violations == 0,
    }
    passed = all(verdict.values())
    out = root / SOCOM_DIR / "index" / "eval.json"
    out.write_text(json.dumps({
        "socom": SOCOM_VERSION,
        "evaluated_at": _now_iso(),
        "contract": "hit@5 >= L0 AND MRR@5 > L0, >=12 probes, latency <= "
                    f"{budget}s, zero redaction violations (amended per R10, "
                    "see probes.yaml)",
        "probes": len(probes), "l0": l0, "l1": l1,
        "verdict": verdict, "passed": passed,
    }, indent=2) + "\n")

    print(f"socom eval — {len(probes)} probes")
    print(f"  L0 keyword : hit@5 {l0['hit_at_5']}/{len(probes)}  "
          f"MRR@5 {l0['mrr_at_5']}  {l0['latency_s']}s")
    print(f"  L1 bm25    : hit@5 {l1['hit_at_5']}/{len(probes)}  "
          f"MRR@5 {l1['mrr_at_5']}  {l1['latency_s']}s")
    for k_, v in verdict.items():
        print(f"  {'✓' if v else '✗'} {k_}")
    misses = [r for r in l1["rows"] if r["rank"] is None]
    for m in misses:
        print(f"    L1 miss: {m['query']!r} -> wanted {m['expect']}")
    print(f"  -> {out}")
    if not passed:
        sys.exit("socom eval: RED — L1 does not satisfy the acceptance "
                 "contract; it may not replace the floor")
    print("socom eval: PASS — L1 accepted against the baseline contract")


# ── cycle — the eval rollup: run ledger -> scored cycle artifact ──────────
# Ported from Akili's evals/cycle-*.json (ledger -> cycle -> query). SOCOM
# vocabulary: seats not roles, promises not tasks, verdict kept/broken not
# DONE/FAILED. Read-only, cache-free: reads the append-only run ledger and
# rolls it into pass@1 / pass@k by seat + hotspots — giving verify-never-claim
# a scored, replayable spine. Distils the *essential* rollup; the full query
# suite (health/trends/reliability) is deliberately deferred.
def _cycle_rollup(rows: list) -> dict:
    """Pure: filtered ledger rows -> scored metrics (summary/seats/hotspots/
    exit_codes/attempts). Provenance (generated_at, ledger, filters) is added by
    the caller. pass@1 = first attempt kept; pass@k = any attempt kept; a promise
    is attributed to the seat of its first attempt."""
    from collections import defaultdict

    # Group attempts by promise, ordered by (attempt, ts). pass@1 reads the
    # first attempt's verdict; pass@k reads whether ANY attempt kept.
    by_promise = defaultdict(list)
    for r in rows:
        by_promise[r["promise"]].append(r)
    for p in by_promise.values():
        p.sort(key=lambda r: (r.get("attempt", 1), r.get("ts", "")))
    all_promises = list(by_promise.values())
    uniq = len(all_promises)

    # Per-seat tally — a promise is attributed to the seat of its first attempt.
    seat_promises = defaultdict(list)
    for attempts in all_promises:
        seat_promises[attempts[0].get("seat", "?")].append(attempts)
    seats = []
    for seat, plist in sorted(seat_promises.items()):
        total = len(plist)
        p1 = sum(1 for p in plist if p[0].get("verdict") == "kept")
        pk = sum(1 for p in plist
                 if any(r.get("verdict") == "kept" for r in p))
        durs = [r.get("duration_s", 0) for p in plist for r in p
                if r.get("verdict") == "kept"]
        seats.append({
            "seat": seat, "promises": total, "pass_at_1": p1, "pass_at_k": pk,
            "pass_rate": round(100 * pk / total, 1) if total else 0.0,
            "avg_duration_s": round(sum(durs) / len(durs)) if durs else 0,
        })

    p1_total = sum(1 for p in all_promises if p[0].get("verdict") == "kept")
    pk_total = sum(1 for p in all_promises
                   if any(r.get("verdict") == "kept" for r in p))
    kept_rows = sum(1 for r in rows if r.get("verdict") == "kept")
    pass_rate = round(100 * kept_rows / len(rows), 1) if rows else 0.0

    # Hotspots: promises with >=1 broken attempt, worst first.
    hotspots = []
    for pid, attempts in by_promise.items():
        broken = sum(1 for r in attempts if r.get("verdict") == "broken")
        if broken:
            hotspots.append({"promise": pid, "broken": broken,
                             "total": len(attempts)})
    hotspots.sort(key=lambda h: (-h["broken"], h["promise"]))

    exit_codes = {}
    for r in rows:
        k = str(r.get("exit_code", "?"))
        exit_codes[k] = exit_codes.get(k, 0) + 1

    # Attempts-to-success + worst (most-attempted) promise.
    succ_attempts, worst = [], (None, 0)
    for pid, attempts in by_promise.items():
        if len(attempts) > worst[1]:
            worst = (pid, len(attempts))
        kept_at = next((i for i, r in enumerate(attempts, 1)
                        if r.get("verdict") == "kept"), None)
        if kept_at:
            succ_attempts.append(kept_at)

    with_contract = sum(1 for p in all_promises if p[0].get("contract"))
    return {
        "summary": {
            "total_runs": len(rows), "unique_promises": uniq,
            "pass_rate": pass_rate,
            "pass_at_1": p1_total,
            "pass_at_1_rate": round(100 * p1_total / uniq, 1) if uniq else 0.0,
            "pass_at_k": pk_total,
            "pass_at_k_rate": round(100 * pk_total / uniq, 1) if uniq else 0.0,
            "contract_coverage": round(100 * with_contract / uniq, 1)
                                 if uniq else 0.0,
        },
        "seats": seats, "hotspots": hotspots, "exit_codes": exit_codes,
        "attempts": {
            "avg_to_success": round(sum(succ_attempts) / len(succ_attempts), 2)
                              if succ_attempts else None,
            "worst_promise": worst[0], "worst_promise_attempts": worst[1],
        },
    }


def cmd_cycle(args):
    import json

    def flag_val(name):
        return args[args.index(name) + 1] if name in args \
            and args.index(name) + 1 < len(args) else None

    root = repo_root()
    since = flag_val("--since")
    seat_filter = flag_val("--seat")
    threshold = flag_val("--threshold")
    gate = "--gate" in args
    print_only = "--cycle" in args or gate

    ledger = root / SOCOM_DIR / "ledger" / "runs.jsonl"
    if not ledger.exists():
        sys.exit("socom cycle: no ledger — .socom/ledger/runs.jsonl absent. "
                 "Nothing measured yet; append runs before rolling a cycle "
                 "(R6: degrade loudly, never a silent empty cycle).")
    rows = []
    for ln in ledger.read_text().splitlines():
        ln = ln.strip()
        if not ln:
            continue
        try:
            r = json.loads(ln)
        except json.JSONDecodeError:
            sys.exit(f"socom cycle: RED — malformed ledger row: {ln[:80]!r}")
        if since and r.get("ts", "") < since:
            continue
        if seat_filter and r.get("seat") != seat_filter:
            continue
        rows.append(r)
    if not rows:
        sys.exit("socom cycle: no rows after filters — nothing to roll up.")

    metrics = _cycle_rollup(rows)
    pass_rate = metrics["summary"]["pass_rate"]
    hotspots = metrics["hotspots"]
    cycle = {
        "socom": SOCOM_VERSION,
        "generated_at": _now_iso(),
        "ledger": str(ledger.relative_to(root)),
        "filters": {"since": since, "seat": seat_filter},
        **metrics,
    }

    # --gate: pass-rate threshold — the testable both-directions unit.
    if gate:
        thr = float(threshold) if threshold is not None else 70.0
        ok = pass_rate >= thr
        print(f"socom cycle: pass_rate {pass_rate}% vs threshold {thr}% "
              f"-> {'PASS' if ok else 'BELOW'}")
        if not ok:
            sys.exit(1)
        return

    written = None
    if not print_only:
        cdir = root / SOCOM_DIR / "cycles"
        cdir.mkdir(parents=True, exist_ok=True)
        stamp = cycle["generated_at"].replace(":", "").replace("-", "")
        out = cdir / f"cycle-{stamp}.json"
        out.write_text(json.dumps(cycle, indent=2) + "\n")
        written = out.relative_to(root)

    s = cycle["summary"]
    print(f"socom cycle — {s['total_runs']} runs, {s['unique_promises']} promises")
    print(f"  pass@1 {s['pass_at_1']}/{s['unique_promises']} ({s['pass_at_1_rate']}%)  "
          f"pass@k {s['pass_at_k']}/{s['unique_promises']} ({s['pass_at_k_rate']}%)  "
          f"pass_rate {s['pass_rate']}%  contract-coverage {s['contract_coverage']}%")
    for st in cycle["seats"]:
        print(f"  seat {st['seat']:<10} pass@1 {st['pass_at_1']}/{st['promises']}  "
              f"pass@k {st['pass_at_k']}/{st['promises']}  ({st['pass_rate']}%)")
    if hotspots:
        print("  hotspots (promises that keep failing assessment):")
        for h in hotspots[:10]:
            print(f"    {h['promise']}  broken {h['broken']}/{h['total']}")
    if written:
        print(f"  -> {written}")


# ── judge — calibrate the assessor, not just the work (Phase 2b) ──────────
# cycle scores the VERDICTS; judge scores the JUDGE. When a seat (reviewer) or any
# model assesses a promise, its verdict is only trustworthy if it agrees with a human.
# The field is emphatic (Hamel, Eugene Yan, Shankar "Who Validates the Validators?"):
# measure TPR and TNR SEPARATELY against human labels before relying on a judge — raw
# agreement misleads under class imbalance. judge reads a labelled set (each row a human
# label + the judge's verdict), computes the confusion matrix + TPR/TNR/precision, and
# --gate BLOCKS when EITHER falls below the bound (both must hold; a judge that only
# catches good work OR only catches bad work is not calibrated). The labelled set is
# JSONL under .socom/evals/ — the operational-data idiom the run ledger already uses.
# 'pass' is the positive class (the work is good / the promise is kept).

def _judge_metrics(rows: list) -> dict:
    """Pure: labelled rows [{human: pass|fail, judge: pass|fail}] -> confusion matrix +
    TPR/TNR/precision/agreement. A row whose human|judge is outside {pass,fail} is
    SKIPPED and counted (never silently dropped — a half-labelled set must not inflate
    the score). Rates are percentages, or None when the denominator is empty (an honest
    'no data for this rate', never a fabricated 100%)."""
    tp = fp = tn = fn = skipped = 0
    for r in rows:
        h, j = r.get("human"), r.get("judge")
        if h not in ("pass", "fail") or j not in ("pass", "fail"):
            skipped += 1
            continue
        if h == "pass":
            tp += (j == "pass")
            fn += (j == "fail")
        else:
            fp += (j == "pass")
            tn += (j == "fail")
    n = tp + fp + tn + fn

    def rate(num, den):
        return round(100 * num / den, 1) if den else None
    return {
        "n": n, "skipped": skipped, "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "tpr": rate(tp, tp + fn),         # judge accepts good work (recall on 'pass')
        "tnr": rate(tn, tn + fp),         # judge rejects bad work (recall on 'fail')
        "precision": rate(tp, tp + fp),   # of judge-passes, how many were truly good
        "agreement": rate(tp + tn, n),    # raw — printed, never gated (imbalance lies)
    }


def _load_labeled(path: Path) -> list:
    """Read a labelled-set JSONL into rows. Loud (R6) on a missing file or a malformed
    row — a calibration you can't trust the inputs of is worse than none (the same RED
    posture cycle takes on a torn ledger row)."""
    import json
    if not path.exists():
        sys.exit(f"socom judge: no labelled set at {path} — create it as JSONL rows "
                 '{"case": id, "human": "pass|fail", "judge": "pass|fail", '
                 '"critique": "..."} (R6: degrade loudly).')
    rows = []
    for ln in path.read_text().splitlines():
        ln = ln.strip()
        if not ln:
            continue
        try:
            rows.append(json.loads(ln))
        except json.JSONDecodeError:
            sys.exit(f"socom judge: RED — malformed labelled row: {ln[:80]!r}")
    return rows


def cmd_judge(args):
    """`socom judge <set> [--gate] [--threshold N]` — calibrate a model assessor against
    human labels. <set> is a name (-> .socom/evals/<set>.jsonl) or a path. Prints the
    confusion matrix + TPR/TNR/precision/agreement; --gate exits RED unless BOTH TPR and
    TNR meet the threshold (default 90%). Read-only."""
    pos = [a for a in args if not a.startswith("--")]
    if not pos:
        sys.exit("usage: socom judge <set> [--gate] [--threshold N]  "
                 "(<set> -> .socom/evals/<set>.jsonl, or a path)")
    gate = "--gate" in args
    thr = 90.0
    if "--threshold" in args:
        i = args.index("--threshold")
        if i + 1 >= len(args):
            sys.exit("socom judge: --threshold needs a number (R6: degrade loudly).")
        try:
            thr = float(args[i + 1])
        except ValueError:
            sys.exit(f"socom judge: --threshold must be a number, got {args[i + 1]!r}.")

    root = repo_root()
    name = pos[0]
    path = Path(name) if (name.endswith(".jsonl") or "/" in name) else \
        root / SOCOM_DIR / "evals" / f"{name}.jsonl"
    if not path.is_absolute():
        path = root / path
    m = _judge_metrics(_load_labeled(path))
    if m["n"] == 0:
        sys.exit(f"socom judge: no usable labelled rows in {name} "
                 f"({m['skipped']} skipped — need human+judge in {{pass,fail}}).")

    print(f"socom judge — {name}: {m['n']} labelled case(s)"
          + (f", {m['skipped']} skipped" if m["skipped"] else ""))
    print(f"  confusion: tp {m['tp']}  fn {m['fn']}  tn {m['tn']}  fp {m['fp']}  "
          "(positive = 'pass' / kept)")
    print(f"  TPR {m['tpr']}% (accepts good)   TNR {m['tnr']}% (rejects bad)   "
          f"precision {m['precision']}%")
    print(f"  agreement {m['agreement']}% — raw; not gated (class imbalance misleads, "
          "so the gate uses TPR & TNR)")

    if gate:
        worst = min(x for x in (m["tpr"], m["tnr"]) if x is not None) \
            if (m["tpr"] is not None and m["tnr"] is not None) else None
        ok = worst is not None and worst >= thr
        which = "TPR" if (m["tpr"] is not None and m["tpr"] == worst) else "TNR"
        if worst is None:
            print("socom judge: BELOW — a one-sided labelled set (TPR or TNR has no "
                  "cases); the judge is uncalibrated on one direction.")
            sys.exit(1)
        print(f"socom judge: min(TPR,TNR) {worst}% ({which}) vs threshold {thr}% "
              f"-> {'PASS' if ok else 'BELOW'}")
        if not ok:
            sys.exit(1)


# ── baseline (the gate before naive RAG) ─────────────────────────────────
# L1 may start only once an L0 floor is measured: corpus shape, L0 latency,
# and probe hit@k under keyword matching. The L1 acceptance contract is
# "same probes, strictly better hit@k, latency within budget" — contracts
# before code, applied to the substrate's own evolution (STORAGE.md).

def l0_score(query: str, chunks: list, k: int = 5) -> list:
    """Keyword-overlap retrieval — the floor any L1 must beat."""
    q = set(re.findall(r"\w+", query.lower()))
    scored = sorted(chunks, key=lambda c: -len(
        q & set(re.findall(r"\w+", c["text"].lower()))))
    return [c["id"] for c in scored[:k]]


def cmd_baseline(args):
    import json, time
    root = repo_root(Path(args[0]) if args else None)
    t0 = time.monotonic()
    chunks = cmd_index([str(root)])
    index_s = time.monotonic() - t0

    t0 = time.monotonic()
    subprocess.run(["grep", "-ri", "verify", "--include=*.xml", "--include=*.md",
                    str(root / SOCOM_DIR)], capture_output=True)
    grep_s = time.monotonic() - t0

    probes_f = root / SOCOM_DIR / "index" / "probes.yaml"
    if not probes_f.exists():
        probes_f.write_text(
            "# query -> expected chunk id substring; scored hit@5 under L0.\n"
            "# Grow this set as the substrate grows — it is the RAG contract.\n"
            "probes:\n"
            "  - query: \"how do I prove a task is done\"\n"
            "    expect: \"verify-never-claim\"\n"
            "  - query: \"when should I write the acceptance checks\"\n"
            "    expect: \"contracts-before-code\"\n")
        print(f"  planted {probes_f} — extend it; it is the L1 acceptance contract")
    probes = yaml.safe_load(probes_f.read_text()).get("probes", [])
    hits = 0
    results = []
    for p in probes:
        top = l0_score(p["query"], chunks)
        hit = any(p["expect"] in cid for cid in top)
        hits += hit
        results.append({"query": p["query"], "expect": p["expect"],
                        "hit@5": hit, "top": top[:3]})

    by_type: dict = {}
    for c in chunks:
        by_type[c["artifact"]] = by_type.get(c["artifact"], 0) + 1
    baseline = {
        "socom": SOCOM_VERSION,
        "measured_at": _now_iso(),
        "corpus": {"chunks": len(chunks), "artifacts_by_type": by_type,
                   "total_chars": sum(len(c["text"]) for c in chunks)},
        "latency_s": {"index_walk": round(index_s, 4), "grep_cold": round(grep_s, 4)},
        "probes": {"count": len(probes), "hit_at_5": hits,
                   "rate": round(hits / len(probes), 3) if probes else None,
                   "results": results},
        "l1_acceptance": "same probes (>=12), hit@5 >= L0 AND MRR@5 strictly "
                         "greater, latency within budget, zero redaction "
                         "violations (amended per R10, recorded in probes.yaml)",
    }
    out = root / SOCOM_DIR / "index" / "baseline.json"
    out.write_text(json.dumps(baseline, indent=2) + "\n")
    print(f"socom baseline: {len(chunks)} chunks, probes {hits}/{len(probes)} "
          f"hit@5 under L0 -> {out}\n  Naive RAG (L1) may start; it must beat "
          "this floor on the same probes.")
