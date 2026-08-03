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
| [`defects.md`](defects.md) | behaviour already shipped and already claimed, made true. |

This split is deliberate and it is an instrument, not bookkeeping.

`defects.md` was added 2026-08-03 by decision 0001 §Amendment 1, because a
defect repair is **neither** of the first two — it produces no capability (the
code already ships and already claims it) and no fact about the world — and so
had no legitimate row shape. Its bound: anything adding a surface, knob,
mechanism or authorization absent from `bin/socom` today is a capability and
belongs in `build.md` as `BLOCKED`. **When in doubt it is a capability**, so the
lane cannot become a build lane under another name.

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
is **one** (`EV-R1-ACCEPTANCE-CORPUS-01`), and the root gate has been at proof
tier **D0 — ASSUMED** since 2026-08-01. One DONE row is not a trend, and the row
that can move the tier — `EV-NONAUTHOR-EXPOSURE-01` — is still unrun.

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
