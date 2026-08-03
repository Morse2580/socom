# Evidence bucket

Work whose deliverable is **a fact about the world**, not a capability.

Governed by [`../decisions/0001-exposure-before-capability.md`](../decisions/0001-exposure-before-capability.md).
The root gate has been at proof tier **D0 — ASSUMED** since 2026-08-01, and
nothing in `build.md` can move it. Only rows here can.

**DONE rows in this bucket: 0.**

---

## Active

- `EV-NONAUTHOR-EXPOSURE-01` **READY P0** — **Put socom in front of five
  engineers who are not the author, one run each, and record where each one
  stops.** This is permitted action (1) of the §10 root gate, named there as
  *"the experiment that raises the tier is cheap and has never been run"* — and
  it is still unrun as of 2026-08-03, two days later. Every other row in this
  repo is downstream of it. **The instrument is `PILOT.md` as it stands** — do
  not improve it first; where it confuses someone IS the finding. Record per
  participant: (a) the point at which they stopped or had to read source, (b)
  whether they reached a bound gate that caught something real, (c) **whether
  they ran any socom verb a second time without being asked** — that last one is
  the actual metric, because first use is compliance and second use is value.
  ⚠️ **Do not demo it to them.** A walked-through session measures the author's
  explanation, not the artifact. ⚠️ **Do not recruit only people who owe you a
  favour** — politeness produces a first use and never a second, which is
  precisely the signal being read. **Falsifiable acceptance:** five recorded
  stall points in `bench/`, and a yes/no per participant on voluntary second
  use. A result of "five people, zero second uses" is a **valid and complete**
  outcome of this row — it is the kill signal the Phase 3a trial cannot
  produce. **Files:** `PILOT.md` (unchanged, as instrument), `bench/`.

- `EV-R1-ACCEPTANCE-CORPUS-01` **READY P1** — **Build R1's acceptance corpus
  before R1 is written, by MINING real drift out of git history rather than
  planting it.** Needs **no people**, so it is not blocked on
  [[EV-NONAUTHOR-EXPOSURE-01]] and can run in parallel. **Goal:** turn "R1
  works" from an opinion into a number that is fixed before the code exists —
  *finds N of M real drift defects, reports nothing on clean repos* — which is
  also the only sentence that makes [[EV-NONAUTHOR-EXPOSURE-01]] interpretable
  rather than a vibe.

  **Mine, do not plant** (revised 2026-08-03; the row previously said "seeded",
  which is now the rejected mechanism). A commit that renamed a build command
  without updating `CLAUDE.md` is a genuine drift defect, and **its parent
  commit is a free, perfect control** — same repo, same config, one difference.
  Planting biases the corpus toward defects the author already knows R1 will
  catch; mining does not. ⚠️ **Synthetic repos are worthless here** — the defect
  class is "config drifted away from a real codebase over months", which a
  freshly generated fixture cannot exhibit.

  **Precision matters more than recall.** A detector that flags everything
  scores 100% on defects alone. PILOT already names the killer: *"Did a gate
  fire a FALSE POSITIVE? Even one on a bad day kills adoption."* R1 parses, and
  parsing can be wrong. Five control classes, all required:

  | Control | Catches |
  |---|---|
  | **Paired parent** — the same repo one commit before the drift | everything; free from history |
  | **Honest config** — real repo, accurate declarations, R1 must report zero | flags-everything |
  | **Non-vacuity** — assert R1 extracted **>0 assertions** from that honest repo | ⚠️ the killer: a parser that understands nothing reports "clean" and is indistinguishable from healthy |
  | **Near-miss** — command exists only via Makefile/alias/wrapper · path gitignored but present · "never edit X" where X was edited *before* the rule landed · a command name appearing in prose, not as a declaration | anchoring + temporal traps |
  | **No config / pure prose** — nothing checkable exists | R1 must say "nothing to check" *distinguishably* from "checked, clean" |

  ⚠️ **Non-vacuity is the one that gets skipped.** An honest-config control
  alone cannot distinguish "parsed the config and found it truthful" from
  "parsed nothing at all" — both emit zero findings. Same class as the inert-check
  problem: a gate that looks present and checks nothing.

  **Falsifiable acceptance:** ≥10 mined defects, each with its paired parent
  commit, every defect independently confirmed present by a recorded command;
  plus at least one instance of each of the other four control classes; and the
  whole corpus committed **before any R1 code is written** — checkable by
  `git log` ordering. **Files:** `bench/`, `tests/`.

- `EV-TRIAL-PROTOCOL-CONFOUND-01` **READY P2** — **The blackboard trial protocol
  produces uninterpretable rows when the session prompt names the paths that
  carry findings.** MEASURED 2026-08-02, tally entry 2: the prompt specified
  both the task and the two paths, so the two findings returned at claim time
  could only corroborate, never redirect — the row scores `B` by construction,
  and would have scored `A` for the wrong reason had the work gone differently.
  The session's hardest problem (an ADR-145 RED-proof requirement that roughly
  doubled the work) was surfaced by CI, not by any finding. **Fix the protocol,
  not the tool:** a trial session must pick its own work *without* being told
  which paths carry findings. ⚠️ Note this makes the tally cheaper to run
  honestly, not more accurate — per [[decisions/0001]] the tally is an
  instrument and cannot clear D0 regardless. **Falsifiable acceptance:** the
  next trial row's `what_changed` field can state a counterfactual — what the
  session would have done absent the finding — without that counterfactual being
  fixed in advance by the prompt. **Files:** `PILOT.md` §the blackboard trial,
  `bench/blackboard-tally.csv`.

- `EV-SAVES-KILL-CRITERION-UNFIRABLE-01` **READY P2** — **Phase 3a's kill
  criterion cannot fire in the setting it is running in, so a clean negative
  result will be discarded rather than acted on.** `PILOT.md` requires *"three
  or more people running concurrent agents on a shared repo… untestable solo"*;
  the actual setting is one person, the author. Fourteen days of zero category-A
  therefore argues *"wrong setting, rerun properly"* — attempt #8 with a
  justification — rather than *stop*. Decision 0001 already rules that a solo
  zero-A is recorded as a **NULL, not a kill**, and transfers the kill criterion
  to [[EV-NONAUTHOR-EXPOSURE-01]]. This row is the paperwork: make `PILOT.md`
  and `ROADMAP.md` say so, so a future reader cannot mistake the null for a pass
  or for a failure. **Falsifiable acceptance:** `PILOT.md` §the blackboard trial
  states the setting precondition and what a solo result does and does not
  license; `ROADMAP.md` Phase 3a matches. **Files:** `PILOT.md`, `ROADMAP.md`.

## Done

*(none)*

---

## Note

This bucket having zero `DONE` rows is not a backlog problem. It is the finding.
Six artifacts, five months, zero external users — because work of this shape was
never on a list.
