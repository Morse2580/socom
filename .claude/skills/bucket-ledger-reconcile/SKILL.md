---
name: bucket-ledger-reconcile
description: Reconcile socom's buckets and proof tier against reality, grounded in re-run evidence and never asserted from a commit. Computes the CHANGED to PINNED to EFFECT tri-state for every DONE row, re-measures the row counts with grep, and re-derives the proof tier from what is on disk. Surfaces the "repaired is not proven" gap. Use at closeout, before writing any state table, after any row flips DONE, and whenever a prompt or handoff states a bucket count. Triggers on "reconcile the buckets", "is this row really done", "check the bucket counts", "what is the proof tier", "/bucket-ledger-reconcile".
---

# Bucket Ledger Reconcile — socom

**Adapted from Akili's `program-ledger-reconcile`**
(`/root/Akili/.claude/skills/program-ledger-reconcile/SKILL.md`). The rule that
makes a ledger trustworthy is Akili's and is unchanged: **the load-bearing state
is asserted from evidence, never inferred from a merge.** Akili's tri-state is
`R → L → T` over a cluster. socom has no cluster, so the tri-state below is
socom's, and it is drawn from this repo's own record of getting it wrong.

⚠️ `buckets/defects.md` says so in its own header: four rows *"were marked DONE
once prematurely, and adversarial verification reopened one of them"* — plus
three further defects **introduced by the repairs themselves**. This skill is
that lesson made repeatable.

## The tri-state — what `DONE` must mean

| Glyph | State | Proven by (required evidence) |
|---|---|---|
| `C` | **CHANGED** — the repair is on `main` | `git merge-base --is-ancestor <sha> HEAD` → rc=0, and CI `success` on that SHA (`gh run list --json conclusion,headSha`). Not "I edited the file". |
| `P` | **PINNED** — a test fails without the repair | The new assertions run against a pre-fix tree: `git archive <pre-fix-sha> \| tar -x -C <dir>`, copy the NEW test files in, run. **Name how many fail.** A test that passes both before and after proves nothing. |
| `E` | **EFFECT** — the row's own acceptance re-run, post-fix | The row's `Falsifiable acceptance:` executed against the built `bin/socom`, with the **output pasted into the row**. Not a description of what it would print. |

**`DONE` requires all three.** `C` alone is socom's own `decisions/0004` Class A
defect — *"reports what it WROTE, not what took EFFECT"* — committed by the
author, in the ledger, about the tool that has the defect.

## Procedure — per row

1. **C** — find the fixing commit. `git log --oneline -S'<symbol>' -- src/socom/`
   or the SHA named in the row. Prove it is on `main` and CI was green on it.
2. **P** — build the pre-fix tree and run the new tests against it. Record the
   count in the row: *"5 of the 9 new smoke assertions FAIL against a
   `git archive HEAD` of the pre-fix tree."* If nothing fails, the tests do not
   pin the defect and the row is not `DONE`.
3. **E** — re-run the row's stated acceptance against `./bin/socom` and paste the
   output. If the row has no falsifiable acceptance line, **that is the finding**
   — write one before closing it.
4. **Write back.** Move the row under a `## Done` heading, flip `READY P0` →
   `DONE P0`, and append the evidence inline. Never widen the row's scope while
   closing it.

## Procedure — whole bucket

```sh
grep -cE '^- `DEF-.*DONE P0'  buckets/defects.md
grep -cE '^- `DEF-.*READY P0' buckets/defects.md
grep -cE '^- `DEF-.*READY P1' buckets/defects.md
grep -cE '^- `.*READY'        buckets/build.md
grep -cE '^- `.*BLOCKED'      buckets/build.md
grep -nE '^- `EV-NONAUTHOR-EXPOSURE-01`' buckets/evidence.md
ls decisions/ bench/exposure/
```

⚠️ `grep -c` **exits 1 when the count is 0**, which silently truncates a
`&&`-chained probe list. Separate these with `;`, or a "0 READY P0" result looks
like a broken command.

Every count that appears in a prompt, handoff or state table is one of these
numbers, measured this session. Not carried.

## The proof tier is re-derived, never advanced by repair

```sh
ls bench/exposure/     # README.md + TEMPLATE.md only  ⇒  still D0
```

`D0 — ASSUMED` holds until a **dated participant sheet** exists. Eight P0 repairs,
eleven field findings, five decision documents and two agent cohorts have moved it
by **nothing**, and that is the designed behaviour, not a disappointment: only a
non-author's recorded session moves it (`decisions/0001`, `0005`).

## Anti-patterns — the whole reason this skill exists

- ❌ **`DONE` because the code changed.** That is `C` alone. See Class A, above.
- ❌ **`DONE` from a test that never saw the defect.** Run it against the pre-fix
  tree or you are pinning your own repair, not the bug.
- ❌ **Moving the proof tier because defects were repaired.** Different currency.
- ❌ **Counting rows by eye.** Use `grep -cE`; a hand count is how a state table
  starts drifting from the file it describes.
- ❌ **Closing a row whose acceptance was never written.** Then `DONE` means
  "someone felt finished."
- ❌ **Growing the P0 cap while reconciling.** `decisions/0001` §Amendment 1
  rule 2 bounds `P0` to defects that fire *before a non-author's stall point*;
  everything else is `P1` and waits. Rule 3: a defect the exposure is **supposed
  to discover** is not repaired first — repairing it deletes the finding.

## Output contract

Per row: `<ROW-ID> — C:<✓/✗> P:<✓/✗> E:<✓/✗>` with one evidence clause each, and
for any `✗` the blocking reason in one clause. Then the headline: **the measured
counts, the proof tier, and what the tier is waiting on** — which, until a dated
sheet exists in `bench/exposure/`, is the same sentence every time.
