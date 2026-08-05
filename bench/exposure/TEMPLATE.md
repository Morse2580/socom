# Exposure run — <participant handle> — <YYYY-MM-DD>

> Observer's sheet. Do not show it to the participant. Protocol and prohibitions:
> [`README.md`](README.md). Row: [[EV-NONAUTHOR-EXPOSURE-01]].

## 1. Before the session

| | |
|---|---|
| Participant (handle/pseudonym) | |
| How they were recruited | |
| **Do they owe me a favour?** | **must be NO — if YES, stop and pick someone else** |
| Drives AI agents on a real repo? | |
| Platform (macOS / Linux / WSL) | |
| Repo they will use — theirs, real? | |
| **Build under test** — paste `socom version` output | |
| socom commit at run time (observer fills; the digest above is authoritative) | |
| Preflight `curl` + `--help` clean? | |
| Mode | live screen-share, observer muted / async |

**Opening line, said once, then silence:**

> Do what you'd normally do — google it, read the source, or give up. All three
> are useful. I'm not going to answer anything.

**If they ask a direct question**, the only permitted reply is:
*"I can't answer that — what would you do if I weren't here?"*

## 2. (a) STALL POINT — the richest datum

Where they stopped, or had to read source to continue. Timestamp each. Quote them
**verbatim** — paraphrase destroys the signal.

| t+ | What they were trying to do | What stopped them | Verbatim | Read source? | Recovered? |
|---|---|---|---|---|---|
| | | | | | |

**Did they abandon the session?** If so, at what and after how long:

**What they had to read source to understand:**

## 3. (b) DID A BOUND GATE CATCH SOMETHING REAL

Unstaged only. A defect the participant planted in order to test the gate does
**not** count — 3/5 of the agent cohort did exactly that and it produced zero
evidence of value.

| | |
|---|---|
| Did a gate fire on real work? | |
| What it caught | |
| Was the defect pre-existing / organic? | |
| Did they fix it, or bypass it? | |
| Did they agree it was worth catching? | |

## 4. Free findings — `PILOT.md`'s own report list

Only what actually happened. Leave blank rather than fill.

| Question | Observed |
|---|---|
| Reached for `git commit --no-verify`? When and why | |
| A gate fired a FALSE POSITIVE | |
| A metric misled them (`value` / `cycle` / trust) | |
| Where discovery stalled *(cross-ref §2)* | |
| They "gamed" a gate — satisfied the check without doing the work | |

**Anything they said about what they thought socom was FOR:**
*(a mismatch with the actual pitch is a finding about the entry shape)*

**Did they hit the adoption surface — 32 planted files, `core.hooksPath`
rewrite — and did they react to it?**
*(the scout's 2026-08-04 assessment says this spends first-contact trust before
earning any; this is the observation that confirms or refutes it)*

## 5. (c) VOLUNTARY SECOND USE — **the metric**

**Filled ONE WEEK later, in a separate sitting. Do not remind them socom exists
before then.**

| | |
|---|---|
| Date asked | |
| Exact wording used | *"No obligation either way — did you end up running it again?"* |
| **Ran a socom verb again, unprompted?** | **YES / NO** |
| If yes — which verb, on what, why | |
| If no — did they say why | |

## 6. Verdict

| | |
|---|---|
| Stall point recorded? | |
| Unstaged gate catch? | |
| **Voluntary second use?** | |
| Any prohibition broken? *(demo · favour · doc-fix-first · agent)* — if yes, the run is void | |

**Proof tier after this run:** D0 / D1 — and why:

**What this run says the next action is:**

> A result of *"stopped at step 2, never ran it again"* is **complete and valid**.
> Record it plainly. It is the kill signal Phase 3a cannot produce, and it closes
> the row exactly as a positive result would.

## 7. Rows this run generated

Defects, doc gaps, and entry-shape findings go to `buckets/defects.md` — filed,
not fixed during the run.

| Finding | Bucket row filed |
|---|---|
| | |
