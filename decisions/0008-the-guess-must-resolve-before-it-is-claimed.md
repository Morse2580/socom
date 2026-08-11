# 0008 — The guess must resolve before it is claimed

**Status:** **PROPOSED — awaiting operator acceptance.** Drafted 2026-08-11
against `3d1bd40` at operator request. **To accept:** change this line to
`**Accepted <date>** — operator ruling` and commit. Until then the hold below
stands and nothing may be repaired.
**Row:** [[DEF-STATUS-CLAIMS-UNLABELLED-01]] (`buckets/defects.md`, **READY P1**)
— this decision lifts its P1 hold **for one surface only**.
**Governed by:** [`0001`](0001-exposure-before-capability.md) §Amendment 1
rule 3, which is the rule this decision asks to be released from — not
overturned.
**Evidence:** [`bench/exposure/2026-08-11-buzz-engineer-report.md`](../bench/exposure/2026-08-11-buzz-engineer-report.md)
and [`bench/exposure/2026-08-07-akili.md`](../bench/exposure/2026-08-07-akili.md).

---

## What is being asked

**Release `DEF-STATUS-CLAIMS-UNLABELLED-01`'s *detect-then-claim* surface — and
only that surface — from the rule-3 hold, so it can be repaired before
[[EV-NONAUTHOR-EXPOSURE-01]] closes.**

Not: repair the row. Not: repair the class. One surface, named below.

## Step 0 — Data breakdown

| # | Claim | Tag | Probe |
|---|---|---|---|
| 1 | Detection selects a test command from **file existence alone** | `MEASURED` | `src/socom/install.py:255` — `if (root / "Cargo.toml").exists(): return "cargo test"`; same shape for `pyproject.toml`, `go.mod`, `package.json` |
| 2 | The success line is printed without resolving the command | `MEASURED` | `install.py:364` — `✓ bound checks.fast/medium/full → {detected!r} — gates now run YOUR tests`, reached from `_bind_checks` returning True; no execution or resolution between |
| 3 | socom **has** the guard and applies it correctly elsewhere | `MEASURED` | `shutil.which` at `spawn.py:413` (`sys.exit` when absent) and `install.py:331`. The guard is **inconsistently applied**, not missing |
| 4 | The tool's promise that this violates is **rank 1** | `MEASURED` | `canon/constitution.xml:6` — `<principle id="verify-never-claim" rank="1">` |
| 5 | Sighting 1 — the agent cohort, 2026-08-05 | `MEASURED` | the row's own text: *"the quickstart bind checkmark … written without executing the command — **5/5 hit this**"* |
| 6 | Sighting 2 — the operator, `buzz`, 2026-08-07 | `MEASURED` | `bench/exposure/2026-08-07-akili.md` §2 — `gate fast` → `RED (rc=127)`, `cargo: not found`; participant escalated out |
| 7 | Sighting 3 — a **non-author engineer**, `buzz`, 2026-08-11 | `MEASURED` | the field report, §2 — same command, same failure, diagnosed unprompted and in writing |
| 8 | Whether the class recurs on repos with a *runnable* detected command | **`UNMEASURED`** | all three sightings are absent-toolchain; a wrong-but-runnable command is a different failure and has never been seen |
| 9 | Whether repairing this surface reduces what `PILOT.md` collects | **argued below, not measured** | six of the row's seven surfaces are untouched by this repair |

## The argument

**Rule 3 kept this row P1 for a reason, and the reason has been satisfied.**
`0001` §Amendment 1 rule 3: *a defect the exposure measurement is supposed to
discover is not repaired first, because `PILOT.md` asks "did a metric mislead
you?" and repairing it deletes the finding.*

That finding has now been collected **three times, independently**: 5/5 of the
agent cohort (claim 5), the operator in the field (claim 6), and a non-author
engineer who made it their **lead** finding, unprompted, in writing (claim 7).
Rule 3 protects a finding that has not yet been collected. This one has been
collected to saturation. **Continuing to hold it no longer protects a
measurement; it protects a defect.**

**The precedent is exact.** `DEF-INSTALLED-BINARY-LANDS-INSIDE-THE-ADOPTED-REPO-01`
was repaired out of P1 order on 2026-08-07 by explicit operator instruction,
because a second sighting refuted the row's own diagnosis. Here a third sighting
does the same work: the row's `⚠️ P1` note reasons about a finding *"the five
participants are supposed to generate."* They generated it; so did a sixth person
nobody recruited.

**And the third sighting supplies an argument the row does not have.** The
engineer's charge — *"the guide makes a specific promise: when it can't figure
something out honestly, it tells you and stops. It guessed and reported
success"* — lands on `verify-never-claim`, **rank 1** (claim 4). The row
currently files this as a labelling defect. It is a **rank-1 constitutional
violation by socom's own binary**, and that is a different severity argument
from the one on file.

**Severity, stated plainly (from the field report, §2):** the failure is not a
one-time stall. A person who walks away after setup has a gate that is red on
every commit, permanently, for a reason unrelated to their code, reported as
`checks failed` — which reads as *your tests are broken*, not *the tool never
worked*. Sighting 2 escalated out of the tool. Sighting 3 recovered only by
diagnosing socom's internals.

## Scope — what may be repaired

**One surface: `_detect_checks` → `_bind_checks` → the `quickstart` success
line.** Concretely:

1. Resolve the detected command's executable before claiming anything —
   `shutil.which` on the first token, the same guard `spawn.py:413` already
   uses. This is claim 3: apply the existing guard consistently.
2. **Separate *detected* from *verified* in what is printed.** A signal found
   and a command proven runnable are different states and must not render
   identically. Bind either way — binding a plausible command is useful — but
   only the resolved case may print `✓ … gates now run YOUR tests`. The
   unresolved case names the command, names what is missing, and says the gate
   will fail until it is bound or the toolchain is present.

**Falsifiable acceptance:** on a repo with a `Cargo.toml` and no `cargo` on
PATH, `quickstart` does not print a success claim about running the user's
tests, and the text it prints instead names both the detected command and the
reason it was not verified. Proved by assertions that **FAIL against a
`git archive HEAD` of the pre-fix tree** — asserted-done is not done
(`verify-never-claim`).

**Files:** `src/socom/install.py` (`_detect_checks`, `_bind_checks`,
`cmd_quickstart`).

## What this decision does NOT do

- **It does not repair the row.** Six of the row's seven surfaces —
  `socom value`, `doctor`, `precond`, the CI step name, `knowledge N chunks`,
  the adoption bar — **remain READY P1 under rule 3**, and `PILOT.md`'s *"did a
  metric mislead you?"* still has six surfaces to collect on. That is the
  argument for a narrow lift rather than a general one, and it is why claim 9 is
  argued rather than measured.
- **It does not touch [[SUBSTRATE-STATUS-TIER-SWEEP-01]]**, which is BLOCKED and
  concerns what the surfaces derive *from*, not what they *claim*.
- **It does not re-open the build lane.** This is a defect repair — behaviour the
  tool already ships and already claims (`0001`:155). It adds no surface, knob,
  mechanism or authorization.
- **It does not rule on the population question.** `0006`'s reopening trigger is
  *"a second person running socom **unprompted**"*. Sighting 3 is a non-author,
  but **whether it was unprompted is `NOT OBSERVED`** (field report §1) and is
  the operator's to establish. This decision stands either way — the repair
  argument does not depend on the participant's provenance.
- **It does not touch §5.** `2026-08-07-akili.md` §5 asks whether *the operator*
  returned and is due **2026-08-14**. Nothing here changes that date or that
  question.
- **It sets no proof tier.**

## The counter-argument, kept

Rule 3 exists because *"building is more enjoyable than finding out why the last
one got no users"* (`0001`), and a repair backlog reproduces that pattern as
easily as a feature backlog. A session that reads this decision as permission to
work the defects bucket has made exactly that mistake. **One surface. Named
files. A pre-fix-failing test. Then stop.**

## Reopening trigger

If a fourth sighting occurs on a repo where the detected command **exists but is
wrong** (claim 8), that is a different failure and needs its own row — this
repair does not cover it.
