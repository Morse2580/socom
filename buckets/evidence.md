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

- `EV-R1-SEEDED-CORPUS-01` **READY P1** — **Build the seeded-defect corpus that
  is R1's acceptance test, before R1 is written.** ≥10 real repos, each with a
  planted intent-drift defect: a `CLAUDE.md` naming a build command that was
  renamed, a "never edit X" rule with X modified after the rule landed, a
  documented path that no longer exists. Needs **no people**, so it is not
  blocked on [[EV-NONAUTHOR-EXPOSURE-01]] and can run in parallel. Writing the
  corpus first means R1 cannot be tuned to pass its own test. ⚠️ **A corpus of
  synthetic repos is worthless here** — the defect class is "config drifted
  away from a real codebase over months," which a freshly generated fixture
  cannot exhibit. Use real repos with real history. **Falsifiable acceptance:**
  the corpus exists and every seeded defect is independently confirmed present
  by a command whose output is recorded — before any R1 code is written.
  **Files:** `bench/`, `tests/`.

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
