# Evidence bucket

Work whose deliverable is **a fact about the world**, not a capability.

Governed by [`../decisions/0001-exposure-before-capability.md`](../decisions/0001-exposure-before-capability.md).
The root gate has been at proof tier **D0 — ASSUMED** since 2026-08-01, and
nothing in `build.md` can move it. Only rows here can.

**DONE rows in this bucket: 1.**

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
  produce.

  ⚠️ **Agent cold runs cannot substitute for this row, and it was tried on
  2026-08-03.** Five agents with distinct engineering backgrounds were given only
  the public link and one session each on a real repo of their choosing. It was
  productive — ~30 defects, 4 filed `P0` in [`defects.md`](defects.md), one
  (`DEF-HOOKS-HIJACK-NO-UNADOPT-01`) more severe than anything the author had
  found. **It produced none of this row's output.** (a) *Zero stall points*: not
  one agent stopped. One downloaded and installed a Go toolchain mid-session to
  keep going where a person closes the tab; all five read the source rather than
  giving up. Agents do not quit, and the stall point is the measurement. (b)
  *Zero organic value*: 3/5 planted their own defect and then caught it, 1 built
  a probe repo — so every "it caught something real" is staged. The cohort
  produced evidence of defects and **no evidence of value**. (c) *Nobody reached
  run #2*, which is the metric. **The asymmetry is the rule: an agent cohort can
  FALSIFY (a tool that fails a compliant, infinitely patient reader certainly
  fails a person) but cannot CONFIRM** — a simulated "yes" is compliance, and the
  profile is written by the author, so the author writes the verdict. This
  forecloses the substitution: cheap, fast, needs no humans, **and cannot move
  the D-tier**. Reaching for it again instead of this row is proxy selection.

  **Files:** `PILOT.md` (unchanged, as instrument), `bench/`.

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

- `EV-R1-ACCEPTANCE-CORPUS-01` **DONE** (2026-08-03) — **R1's acceptance corpus
  exists, and it was committed before any R1 code.** 30 records in
  [`../bench/r1-corpus/corpus.jsonl`](../bench/r1-corpus/corpus.jsonl); method,
  scoring contract and decay policy in
  [`../bench/r1-corpus/README.md`](../bench/r1-corpus/README.md).

  **Against the falsifiable acceptance, in order:**
  - ≥10 mined defects each with a paired parent → **18**, plus 1 never-existed
    defect that does not count toward the ten. Mined from a pool of **475** real
    repos carrying an agent config; **19 distinct repos**, no repo contributing
    more than one, 5 config formats.
  - every defect confirmed by a recorded command and its output → every record
    carries a `confirm` block with argv, exit code and real stdout, captured at
    authoring time by `assemble.py`.
  - ≥1 instance of each of the other four control classes → honest config
    (`C01`), non-vacuity (`C02`, ≥20 assertions), no-checkable-content (`C03`),
    near-miss (`N01`–`N08`, covering **all four** named sub-classes plus a fifth
    found by mining).
  - committed before any R1 code, checkable by `git log` ordering → asserted
    **mechanically and permanently** by `tests/r1corpus.py` via git ancestry, not
    promised in prose. Wired into `socom.yaml` `checks.medium`/`full` and CI.

  **Two candidate defects were reclassified as controls on review**, which is the
  method working: `N03`'s own defect commit says *"gitignore and chezmoiignore
  it"* (the file is on the developer's disk, untracked), and `N08`'s config line
  declares the referent was deleted **on purpose**. Both would have scored as R1
  successes under a careless reading. Neither was designed — mining found them.

  **What it does not do:** it makes R1 gradeable, not wanted. The P0 remains
  [[EV-NONAUTHOR-EXPOSURE-01]], still unrun. A green run against this corpus is
  not progress on that. **Files:** `bench/r1-corpus/`, `tests/r1corpus.py`,
  `socom.yaml`, `.github/workflows/ci.yml`.

---

## Note

This bucket's first `DONE` row is an evidence row, not a capability — which is
the shape the whole split exists to make visible. The finding that produced it
stands: six artifacts, five months, zero external users, because work of this
shape was never on a list. One row of it now is not a trend.
