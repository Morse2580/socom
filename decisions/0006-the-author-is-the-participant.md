# 0006 — The author is the participant

**Status:** **Accepted 2026-08-07** — operator ruling. `EV-NONAUTHOR-EXPOSURE-01`
is **amended**: the *non-author* requirement is **struck**. The author's own
runs, across the machines they hold, satisfy the row.
**Supersedes:** `0005` on the disposition only — `0005`'s *analysis* stands and
is not re-derived; its *refusal* is overturned by the operator.
**Resolves:** who may be the participant. **The population question is closed in
the other direction and is not re-litigated.**
**Upstream:** `0001` §Decision, `0005`, and the §10 ROOT GATE of 2026-08-01.

---

## The ruling, in the operator's terms

> *"I have access to several machines that could access repos; every feature I
> test and make sure end to end runs. I tell you what path to go to, and I test
> your work — for me that's an end-to-end chain for making sure everything
> works. I am that person."*

Accepted as given. The operator directs, the agent builds, the operator tests
across several machines and real repos. That chain is the verification
instrument this project actually has, and the ruling is that it is the one the
row will be measured with.

## What this changes

1. **`EV-NONAUTHOR-EXPOSURE-01`'s non-author clause is struck.** The row ID is
   kept — it is cross-referenced from `buckets/defects.md`, `PILOT.md` and the
   session prompts, and renaming it would break those. The name is historical
   from 2026-08-07 forward.
2. **The four prohibitions collapse to two.** *No demo* and *no doc-fix-first*
   survive unchanged — they protect the finding regardless of who is at the
   keyboard. *No favour* and *no agent substitute* are moot: the first has no
   referent when the participant is the operator, and the second is superseded
   by the ruling rather than by an argument.
3. **The instrument is the same sheet.** `bench/exposure/TEMPLATE.md` and its
   README are unchanged. A run is recorded there or it did not happen
   (README step 5). §5 — voluntary second use, one week later — is still the
   headline metric and is still filled in a separate sitting.
4. **First recorded run:** `bench/exposure/2026-08-07-akili.md`, from the `buzz`
   run on `/home/akili`.

## What this ruling does not claim

Recorded so the next session does not have to reconstruct it, and so no later
artifact overstates what is on file. This is bookkeeping, not a re-argument; the
question is closed.

- It does not claim the operator's runs are independent of the operator. They
  are not, and the sheet's §5 is scored knowing that.
- It does not retroactively convert the two agent cohorts (2026-08-03,
  2026-08-05) or the `/home/akili` smoke test of 2026-08-05 into exposure runs.
  Those remain what their rows say they are.
- It does not set the proof tier. The `D0`/`D1` vocabulary is defined by the
  root gate in `/root/Akili/.claude/skills/root-gate` and **nothing in this
  repo defines it** (see the standing note in the session prompt). The tier
  after a run is the operator's to set, against that definition, on the sheet's
  §6 line.

## Reopening trigger

Fork > 0, or a second person running socom unprompted. Neither is expected, and
neither is required for anything currently in `buckets/build.md`.
