# R1 acceptance corpus — the number that decides whether R1 works

> Row: `EV-R1-ACCEPTANCE-CORPUS-01` in [`../../buckets/evidence.md`](../../buckets/evidence.md).
> Governed by [`decisions/0001-exposure-before-capability.md`](../../decisions/0001-exposure-before-capability.md).

**This corpus was committed before a single line of R1 existed.** That ordering
is the whole point, and it is not a promise in prose — `tests/r1corpus.py`
asserts it mechanically, forever, by git-log ancestry. A corpus written after
the detector can be tuned to pass itself, and nothing you can inspect
afterwards tells the difference.

R1 is the intent-drift detector: parse a repo's declared agent intent
(`CLAUDE.md`, `AGENTS.md`, `.cursorrules`, `.github/copilot-instructions.md`)
into checkable assertions, then verify each against the repo.

## The sentence this exists to make true

> R1 finds **N of 18** real drift defects, reports **zero** on the honest
> config and on all **8** near-miss controls, extracts **≥20 assertions** while
> doing it, and says *"nothing to check"* distinguishably on a config with
> nothing in it.

Before this file, *"R1 works"* was an opinion. It is now a number. That number
is also the only thing that makes `EV-NONAUTHOR-EXPOSURE-01` interpretable
rather than a vibe: when five strangers run R1 and shrug, you need to already
know whether the tool was right.

## Mined, not planted

Every defect is a real commit by someone who has never heard of socom, found by
walking history — never seeded. The method (`mine.py`, reproducible):

1. read the agent config at `HEAD`, extract the **path referents** it declares
2. keep the ones that do not resolve at `HEAD`
3. walk back to the commit that removed each one (`--diff-filter=D`,
   `--no-renames`, so renames register as deletions)
4. **keep only pairs where the config blob is byte-identical at that commit and
   its parent**

Step 4 is what makes the parent a control rather than a comparison: same repo,
same config, same author, same everything — the single difference across the
pair is whether the referent is in the tree. Not chosen by the person writing
the detector.

Planting would have biased the corpus toward defects R1's author already knows
R1 will catch. That bias is invisible afterwards, and it is the entire reason
this row exists.

⚠️ **Synthetic repos would be worthless here.** The defect class is *"config
drifted away from a real codebase over months"*. A freshly generated fixture
cannot exhibit it — there is no drift without elapsed time. The pool was 475
real repos carrying an agent config, each created before 2025-06 and pushed
since 2025-09.

## Precision over recall — and the reason

A detector that flags everything scores 100% against defects alone. `PILOT.md`
names the killer directly:

> *"Did a gate fire a FALSE POSITIVE? Even one on a bad day kills adoption."*

R1 parses, and parsing can be wrong. A tool that reports three lies in a
stranger's config and gets one wrong is uninstalled that afternoon. So **eleven
of the thirty records are controls**, and a false positive on any of them is a
harder failure than a miss.

## What is in here

| Class | Records | R1 must |
|---|---|---|
| **Paired-parent defect** | 18 (`D01`–`D18`) | report at the defect commit, stay silent at its parent |
| **Declared-never-existed defect** | 1 (`D19`) | report — and flag exactly one of two adjacent referents |
| **Honest config** | 1 (`C01`) | report **zero** |
| **Non-vacuity** | 1 (`C02`) | extract **≥20 assertions** from `C01` |
| **No checkable content** | 1 (`C03`) | say *"nothing to check"*, distinguishably |
| **Near-miss** | 8 (`N01`–`N08`) | report **zero** — each is a different trap |

19 defects across **19 distinct repos** — no repo contributes more than one, so
no single author's idiom can dominate the score. Five config formats. Akili
contributes exactly one record, the calibration exemplar (`D19`); `tests/r1corpus.py`
caps it at one so the corpus can never quietly become all-Akili.

### Non-vacuity is the one that gets skipped

`C02` is the most important record in this file and the easiest to leave out.

An honest-config control **alone cannot distinguish** *"parsed the config and
found it truthful"* from *"parsed nothing at all"* — both emit zero findings. A
parser that understands none of the file passes every clean-repo test you can
write. So `C01` ships with its 20 ground-truth referents enumerated, and `C02`
turns them into a floor: **zero findings with fewer than 20 assertions
extracted is a FAILURE, not a pass.**

Record the assertion count, not just the finding count.

### The eight near-misses, and what each one traps

| id | trap | why a plausible R1 fires |
|---|---|---|
| `N01` | `make lint` | resolves to a Makefile target, not a file named `lint` |
| `N02` | `just check-isolation` | same, through a runner R1 may not know |
| `N03` | gitignored but present | absent from the tree, listed in `.gitignore:43` — it is on the developer's disk |
| `N04` | temporal | *"do not edit X"* landed 2026-05-22; all 29 edits to X predate it by 9+ months |
| `N05` | temporal | second instance, different generator toolchain |
| `N06` | prose mention | *"migrated from `webpack` in commit `bb4fd8b`"* — a replaced tool and a SHA, neither a declaration |
| `N07` | prose mention | *"Do not use `npm`"* — polarity inverted; absence is the intended state |
| `N08` | declared-as-deleted | the config says the file **was removed, do not restore it** |

`N03` and `N08` were not designed — they fell out of mining as candidate
defects and were reclassified on review. `N03`'s own defect commit says
*"gitignore and chezmoiignore it"*; `N08`'s config line says the file was
deleted on purpose. Both would have been scored as R1 successes by a careless
reading, which is exactly why they are controls.

### The calibration exemplar (`D19`)

Akili `main` `7c684528`, `docs/ERROR_INDEX.md:5-7`:

> *"This file is auto-generated from the akili-graph. Do NOT edit manually. Run
> `scripts/generate-error-index.sh` to regenerate."*

`scripts/generate-error-index.sh` has **never existed in any commit reachable
from main** — verified by `git log --all -- <path>` returning empty, not merely
absent at `HEAD`. It has no paired parent, so it does **not** count toward the
ten. It earns its place another way: two lines up, the same block names
`scripts/akili-graph/akili-graph`, which **does** exist. One declaration block,
one referent to flag and one to leave alone. Recall and precision in a single
record.

## How to score R1 against this

For each record, run R1 at the pinned commit and compare to `expected`:

```
recall     = defects reported / 19
precision  = 1 - (findings on C01,C03,N01..N08 / 11)
non-vacuity= assertions extracted on C01     (must be >= 20)
```

**Report all three or none of them.** Recall alone is the number a
flags-everything detector wins.

A run is a **PASS** only if precision is 1.0 — zero findings across all eleven
controls — *and* non-vacuity holds. Recall is then the score. There is no
recall threshold set here on purpose: fixing one before seeing R1's first
honest run would be picking the number that makes the tool look good, which is
the failure this whole row exists to prevent. Record the recall you get, then
argue about whether it is enough.

## Verifying the corpus itself

```sh
python3 tests/r1corpus.py            # offline, in CI: structure + ordering
bash bench/r1-corpus/verify.sh       # network: replay every recorded command
```

`tests/r1corpus.py` is wired into `socom.yaml` `checks.medium`/`full` and CI.
`verify.sh` is **not** — it clones ~29 repos and needs network, so it is
opt-in.

Every record carries its `confirm` block: the exact command, its exit code, and
its real stdout, captured at authoring time. Nothing here is asserted from
memory.

⚠️ One trap the confirmations encode deliberately: **`git ls-tree` exits 0 with
empty stdout for an absent path.** Exit code alone cannot witness absence.
`tests/r1corpus.py` asserts every paired defect records both a present and an
absent tree entry, so a future edit cannot quietly weaken the evidence to
exit-code checks.

## §decay — this corpus rots, and that is fine

It pins commits in repos owned by strangers. Repos get deleted, renamed, made
private, force-pushed. `verify.sh` reports that as DRIFT or SKIP rather than
failing silently.

**When a record decays, do not repair it by substitution** — mine a fresh one
with `mine.py` and give it a new id. Editing a decayed record to point at
something convenient is how a mined corpus quietly becomes a planted one.

## What this corpus does NOT do

It makes R1 **gradeable**. It does not make anyone **want** it.

The P0 is still `EV-NONAUTHOR-EXPOSURE-01` — five engineers who are not the
author, one run each, recorded stall points, voluntary-second-use yes/no. No
session can do it, because it needs people rather than agent time. It has been
available since 2026-08-01 and is still unrun.

A green run against this corpus is not progress on that.
