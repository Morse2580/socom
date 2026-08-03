# Work buckets

Task state lives here, in git. There is no external tracker, so any clone has
the full operational state. Drift between a bucket and reality is treated the
same as drift between git and a deployed system: a defect, not a nuisance.

## The split, and why it is this one

Two buckets, split by **what the work produces** — not by module, language, or
merge domain:

| Bucket | Produces |
|---|---|
| [`build.md`](build.md) | a capability. Code that did not exist before. |
| [`evidence.md`](evidence.md) | a fact about the world. Something we did not know before. |

This split is deliberate and it is an instrument, not bookkeeping.

The diagnosis in [`../decisions/0001-exposure-before-capability.md`](../decisions/0001-exposure-before-capability.md)
is that **every increment in the R1–R5 ladder is a build, and none is an
exposure** — six artifacts over five months, zero users, because the plan never
contained a task whose deliverable was *"someone who is not the author touched
it."* Capability work is enjoyable and always available; evidence work is
uncomfortable and easy to defer. A single backlog lets the first crowd out the
second silently.

Two buckets make the ratio impossible to miss. If `build.md` has rows moving and
`evidence.md` has none, that is the failure mode reproducing itself, visible in
one glance.

**The one number to read here:** rows DONE in `evidence.md`. As of 2026-08-03 it
is **zero**, and the root gate has been at proof tier **D0 — ASSUMED** since
2026-08-01.

## Row format

```
- `ROW-ID` STATUS PRIORITY — description.
  **Falsifiable acceptance:** what must be observably true. **Files:** paths.
```

- **Status:** `READY` · `CLAIMED` · `BLOCKED` · `DONE`
- **Priority:** `P0` (blocking everything) … `P3` (nice to have)
- A `BLOCKED` row must name its blocker by row id. A blocker that is not a row
  id is a wish, not a dependency.
- Every row needs a **falsifiable acceptance test**. A row that cannot be shown
  false is not a task, it is an intention.

## Rules

1. A row moves to `DONE` only when its acceptance test has actually been run and
   the output recorded — not when the code merged. Merged is not done.
2. Adding a `build.md` row while `evidence.md` has zero `DONE` rows requires
   naming which decision permits it. Today only `R1-INTENT-DRIFT-DETECTOR-01`
   qualifies, per decision 0001.
3. Cross-referencing is by row id in double brackets: `[[EV-NONAUTHOR-EXPOSURE-01]]`.
