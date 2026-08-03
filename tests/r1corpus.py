#!/usr/bin/env python3
"""R1 acceptance-corpus structural gate — offline, wired into CI.

This does NOT check that the corpus matches the upstream repos (that is
`bench/r1-corpus/verify.sh`, which needs network).  It checks the properties
that make the corpus *worth anything*, and which are silently easy to lose:

  1. enough MINED paired-parent defects, each with a real parent commit
  2. every defect independently confirmed by a RECORDED command and its output
  3. all five control classes present -- especially non-vacuity, the one that
     gets skipped
  4. no single repo dominates -- one repo's idiom is one repo's idiom
  5. THE ORDERING: the corpus was committed before any R1 code existed

(5) is the load-bearing one.  A corpus written after the detector can be tuned
to pass it, and no amount of inspection afterwards can tell the difference.  Git
log ordering is the only durable proof, so it is asserted mechanically here
rather than promised in prose.
"""
import json
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CORPUS = ROOT / "bench" / "r1-corpus" / "corpus.jsonl"

MIN_PAIRED_DEFECTS = 10
REQUIRED_CONTROLS = {
    "honest-config",
    "non-vacuity",
    "no-checkable-content",
}
REQUIRED_NEARMISS = {
    "near-miss/wrapper-command",
    "near-miss/gitignored-but-present",
    "near-miss/temporal",
    "near-miss/prose-mention",
}
# where an R1 implementation would live (build.md: "Files: src/socom/ (new module)")
R1_GLOBS = ["src/socom/drift*.py", "src/socom/intent*.py", "src/socom/r1*.py"]

fail = []
ok = []


def check(cond, msg):
    (ok if cond else fail).append(msg)


def git(*a):
    return subprocess.run(["git", "-C", str(ROOT), *a],
                          capture_output=True, text=True, timeout=120)


# ---------------------------------------------------------------- load
if not CORPUS.exists():
    print(f"r1corpus: MISSING {CORPUS}")
    sys.exit(1)

recs = [json.loads(l) for l in CORPUS.read_text(encoding="utf-8").splitlines() if l.strip()]
ids = [r["id"] for r in recs]
check(len(ids) == len(set(ids)), f"record ids are unique ({len(ids)} records)")

defects = [r for r in recs if r["class"] == "defect"]
controls = [r for r in recs if r["class"] == "control"]
paired = [r for r in defects if r["subclass"] == "paired-parent"]

# ------------------------------------------------- 1. mined paired defects
check(len(paired) >= MIN_PAIRED_DEFECTS,
      f"{len(paired)} paired-parent defects (need >= {MIN_PAIRED_DEFECTS})")
for r in paired:
    check(bool(r.get("parent_commit")) and len(r["parent_commit"]) == 40,
          f"{r['id']}: has a full-length paired parent commit")
    check(r.get("config_identical_across_pair") is True,
          f"{r['id']}: config is byte-identical across the pair "
          f"(that is what makes the parent a control)")
    check(r["defect_commit"] != r["parent_commit"],
          f"{r['id']}: defect and parent are distinct commits")
    check(r["expected"]["at_defect_commit"] == "FINDING"
          and r["expected"]["at_parent_commit"] == "CLEAN",
          f"{r['id']}: expectation is stated in both directions")

# ------------------------------------- 2. recorded, independent confirmation
for r in defects:
    conf = r.get("confirm") or []
    check(len(conf) >= 2, f"{r['id']}: >= 2 recorded confirmations")
    check(all("cmd" in c and "exit" in c and "stdout" in c for c in conf),
          f"{r['id']}: every confirmation records cmd + exit + stdout")
    # the pair must be witnessed by output, not by exit code alone: `git
    # ls-tree` exits 0 for an absent path and prints nothing.
    if r["subclass"] == "paired-parent":
        trees = [c for c in conf if c["cmd"].startswith("git ls-tree")]
        check(any(c["stdout"] for c in trees) and any(not c["stdout"] for c in trees),
              f"{r['id']}: confirmations witness BOTH a present and an absent "
              f"tree entry (exit code alone cannot distinguish them)")

# ------------------------------------------------------ 3. control classes
subs = {r["subclass"] for r in controls}
for want in REQUIRED_CONTROLS | REQUIRED_NEARMISS:
    check(want in subs, f"control class present: {want}")

nv = [r for r in controls if r["subclass"] == "non-vacuity"]
check(len(nv) == 1, "exactly one non-vacuity control")
if nv:
    n = nv[0]
    target = n.get("applies_to")
    check(target in ids, f"non-vacuity control names its honest config ({target})")
    thr = str(n["expected"]["assertions_extracted"])
    check(thr.startswith(">=") and int(thr.split(">=")[1].strip()) > 0,
          f"non-vacuity threshold is a positive lower bound ({thr})")
    honest = next((r for r in controls if r["id"] == target), None)
    if honest:
        check(len(honest.get("ground_truth_referents", [])) >=
              int(thr.split(">=")[1].strip()),
              "the honest config actually contains at least as many referents "
              "as the non-vacuity threshold demands")

# --------------------------------------------------------- 4. independence
repos = [r["repo"] for r in defects]
per = {x: repos.count(x) for x in set(repos)}
worst = max(per.values())
check(worst <= 2, f"no repo contributes more than 2 defects (max={worst})")
check(len(set(repos)) >= 10,
      f"defects span {len(set(repos))} distinct repos")
akili = sum(1 for r in defects if "akili" in r["repo"].lower())
check(akili <= 1, f"corpus is not all-Akili (Akili defects: {akili})")
check(len({r["config"] for r in recs}) >= 3,
      f"corpus spans {len({r['config'] for r in recs})} distinct config formats")

# ------------------------------------------------------------ 5. ORDERING
corpus_rel = "bench/r1-corpus/corpus.jsonl"
corpus_add = git("log", "--diff-filter=A", "--format=%H", "--", corpus_rel).stdout.split()
r1_files = []
for pat in R1_GLOBS:
    r1_files += [p for p in git("ls-files", pat).stdout.split() if p]

if not corpus_add:
    # not yet committed -- the ordering claim is unfalsifiable but also unbroken
    ok.append("ordering: corpus not yet committed (nothing to violate)")
elif not r1_files:
    ok.append("ordering: no R1 implementation exists yet -- corpus is first "
              f"(committed {corpus_add[-1][:12]})")
else:
    corpus_sha = corpus_add[-1]
    first_r1 = None
    for f in r1_files:
        adds = git("log", "--diff-filter=A", "--format=%H", "--", f).stdout.split()
        if adds:
            first_r1 = adds[-1] if first_r1 is None else first_r1
    if first_r1:
        anc = git("merge-base", "--is-ancestor", corpus_sha, first_r1).returncode
        check(anc == 0,
              f"ordering: corpus commit {corpus_sha[:12]} is an ancestor of the "
              f"first R1 commit {first_r1[:12]} -- the corpus was fixed BEFORE "
              f"the detector it grades")

# ---------------------------------------------------------------- report
for m in ok:
    print(f"  ✓ {m}")
for m in fail:
    print(f"  ✗ {m}")
print(f"r1corpus: {len(ok)} passed, {len(fail)} failed "
      f"({len(paired)} paired defects, {len(controls)} controls, "
      f"{len(set(repos))} repos)")
sys.exit(1 if fail else 0)
