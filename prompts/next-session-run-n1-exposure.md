# Next session — stop building. Run the n=1 exposure.

**Row:** `EV-NONAUTHOR-EXPOSURE-01` (`buckets/evidence.md`), **READY P0**, amended
2026-08-04 to `n=1`. **Governed by** `decisions/0001-exposure-before-capability.md`.

## Where the repo is

**Everything here is relative to `/root/socom`** — a SIBLING of `/root/Akili`,
not inside it. `cd /root/socom && git pull` first; check `pwd` before any edit.
Akili's `CLAUDE.md` does not govern here: no worktrees, no row claims, no `glab`,
no MRs. Commit **directly to `main`**, push, watch with `gh run watch`.
`bin/socom` is BUILT from `src/socom/*.py` — edit the source, run
`python3 build.py`, commit both (`python3 build.py --check` is a CI gate).
socom's own hooks are not wired in its checkout, so run `./bin/socom gate full`
yourself before every push.

## The one thing this session is for

**Put socom in front of one engineer who is not the author, watch in silence,
write down where they stop.** That is the whole session. It is not a coding task
and there is no code deliverable.

The root gate authorised exactly this — *"one non-author engineer, observed"* —
and it has never been done. Five months, six artifacts, zero non-author users,
proof tier **D0**. Every capability row in `buckets/build.md` is BLOCKED on it.

Record per the row: (a) where they stopped or had to read source, (b) whether a
bound gate caught something real, (c) whether they ran any socom verb again
**without being asked**. Write it to `bench/`.

⚠️ Do not demo it. ⚠️ Do not fix `PILOT.md` first — where it confuses a stranger
IS the finding. ⚠️ Do not substitute an agent: agents can falsify but cannot
confirm, and one cohort already ran (2026-08-03).

## What changed on 2026-08-04, and why it should change your instinct

The four pre-exposure P0 defects are **DONE** — and the session that closed them
found **six more**, three of which it had introduced itself:

- `adopt` silently disabled the hooks of any repo using the default
  `.git/hooks/` — **where lefthook installs**. The row had been marked DONE
  while its own defect class was still live. `PILOT.md` shipped a safety claim
  naming lefthook that was false when written.
- The commit gate could be bypassed by typing `Merge ` in front of any subject.
- `adopt` crashed on a `sort`ed `.gitignore`; `_ensure_ignore_block` silently
  deleted a user's own rule; `unadopt` performed the clobber it exists to undo.

**All six survived `gate full`, `build.py --check` and a 323-test suite** — the
tested half was the regex; the half that reaches into someone else's repo had
none. Treat green gates here as evidence about the tested surface only.

Three assessments, all recorded, all pointing the same way:

1. **Build order/shape (scout, 2026-08-04).** Execution is rigorous; the *order*
   and *entry shape* are wrong for the population socom needs. Planting ~32 files
   and rewriting `core.hooksPath` spends first-contact trust before earning any.
   Corroborated by socom's own `GAPS.md:121`: *"SOCOM is a lot of complexity
   justified by anecdote (192 Akili sessions), not measurement."*
2. **The adoption model contaminates its own experiment.** A stranger cannot
   evaluate "is drift-detection useful" without also absorbing "will this rewrite
   my git hooks." Two hypotheses, one test, inseparable result.
3. **R1 measured, not guessed.** Against Akili's own 815-line `CLAUDE.md`: only
   **13%** of 576 statements name a checkable referent (80% is prose no checker
   can verify), and actual drift is **~0**. Its grading corpus requires
   **precision 1.0 across 11 near-miss controls** — a naive resolver fell into
   three within minutes. R1's hard problem is precision, not detection.

**So the instinct to build R1 next is weaker than it looks**, and building it
unblocks nothing (`0001` §2 freezes every increment until this row has a result).

## Do NOT do these

- **Do not work the P1 defects.** Four are filed, cheaper and more interesting,
  and they measure nothing. `DEF-STATUS-CLAIMS-UNLABELLED-01` is P1 **on
  purpose** — `PILOT.md` asks *"did a metric mislead you?"*, so repairing it
  first deletes a finding the participant is meant to generate (`0001`
  §Amendment 1 rule 3).
- **Do not build any capability.** Everything except R1 reads BLOCKED.
- **Do not build R1 either**, unless the exposure run has happened or you are
  overriding this prompt deliberately. If you do build it, ship it **standalone**
  — own binary, zero adoption, zero git-config writes, no `.socom/` — so the two
  hypotheses stay separable.
- **Do not run another agent cohort.** It cannot move the D-tier.

## Cheaper alternative if no engineer is reachable this week

Test the *premise* instead of the tool: ask three engineers to describe their
last painful session driving AI agents on a real repo. Twenty minutes each, no
install, no `PILOT.md`. If the pain they describe is not the pain socom
addresses, tool quality is irrelevant and that is worth knowing before R1.

## State — verified 2026-08-04, re-probe anything you lean on

| Thing | State |
|---|---|
| socom `main` | `d781516`, clean, pushed, CI green |
| Buckets | `defects.md` 4 DONE P0 + 4 READY P1 · `build.md` 1 READY (R1) + 7 BLOCKED · `evidence.md` `EV-NONAUTHOR-EXPOSURE-01` READY P0, **unrun** |
| Proof tier | **D0 — ASSUMED**, unchanged since 2026-08-01 |
| Suite | `unit: 339 passed, 0 failed` · `gate full: PASS` · `build.py --check` clean |

Probes: `./bin/socom gate full` · `python3 build.py --check` ·
`python3 tests/unit.py` · `python3 tests/r1corpus.py` · `grep -c '^- \`' buckets/*.md`

## The bound

Today the tool got meaningfully less broken — it no longer disables your hooks,
crashes on your `.gitignore`, or lets anyone bypass its own commit gate. The
proof tier did not move, because none of that is the blocking claim.

**One engineer. This week. Watch in silence.**
