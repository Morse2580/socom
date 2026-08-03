# Build bucket

Work whose deliverable is **a capability**.

Governed by [`../decisions/0001-exposure-before-capability.md`](../decisions/0001-exposure-before-capability.md):
**no capability beyond R1 lands until `EV-NONAUTHOR-EXPOSURE-01` carries a
recorded result.** Every row below R1 therefore reads `BLOCKED` and names that
row as its blocker. That is not a scheduling opinion; it is §14.4 of the source
research, which the 2026-08-02 build bypassed without withdrawing.

Ladder reference: §14.2 of
`Akili:thoughts/shared/research/2026-08-01-agent-development-substrate-standalone-product.md`.

---

## Active

- `R1-INTENT-DRIFT-DETECTOR-01` **READY P0** — **Parse the repo's declared agent
  intent (`CLAUDE.md`, `AGENTS.md`, `.cursor/rules`) into checkable assertions,
  then verify each against the repo.** The only capability row permitted to
  proceed today. **Why it is the one:** it pays off to a stranger on run #1 — it
  finds lies in their *own* config, needs nobody's permission, no protocol to
  adopt, nothing to configure. That is what makes it the cheapest instrument
  ever available for moving the D-tier, per §14.4. Contrast R3, already built,
  whose payoff is structurally invisible without 2+ agents and a stock of
  findings. ⚠️ **Write [[EV-R1-ACCEPTANCE-CORPUS-01]] first** — building the
  acceptance corpus after the detector lets the detector be tuned to pass its
  own test. ⚠️ **R1 must parse, and parsing can be wrong** — this is exactly why
  §20 preferred the blackboard, whose findings are authored and need no
  inference. Accept the inference cost here; it is the price of paying off to
  one person. **Falsifiable acceptance:** on a repo whose `CLAUDE.md` names a
  build command that was renamed, R1 reports it and exits non-zero; and it
  scores against [[EV-R1-ACCEPTANCE-CORPUS-01]]'s mined corpus on **both recall
  and precision**, with the per-defect result recorded — including a non-zero
  assertion count on the honest-config control, so "reported nothing" cannot be
  confused with "parsed nothing". **Size:** 1–2 wks. **Files:** `src/socom/`
  (new module), `tests/`, `bin/socom` (rebuilt via `build.py`).

## Blocked

All blocked on [[EV-NONAUTHOR-EXPOSURE-01]] per decision 0001.

- `R2-CLAIM-VERIFIER-HOOK-01` **BLOCKED P2** — commit/PR hook refusing claims
  that lack evidence: "tests pass" with no captured run, "verified" with no
  output. Turns verify-never-claim from a principle into a gate on your own
  commits, solo. **Falsifiable acceptance:** a commit asserting a green suite
  with no recorded run is rejected; one with a captured run passes. **Size:**
  1 wk.
- `R4-HANDOFF-COMPILER-01` **BLOCKED P2** — session end emits a structured
  handoff derived from what actually happened (diff, gates run, commands,
  outcomes), not authored by hand. **Falsifiable acceptance:** the handoff
  regenerates deterministically from git + run records with no human input, and
  a resumed session reaches the same working state. **Size:** 2 wks.
- `R5-THE-RECORD-01` **BLOCKED P3** — the typed store: provenance, contradiction,
  temporal validity, decay — written as a side effect of R1–R4, queryable on
  demand. **Deferred by design, therefore last** — its value is the most
  deferred and most plural, and starting here is what killed every prior
  attempt. R1–R4 populate the store before it is built, which removes the
  cold-start problem. **Falsifiable acceptance:** a question answerable only
  from accumulated history ("why was X rejected?") returns the right prior
  decision with its provenance chain. **Size:** 3–4 wks.

### Candidate increments — recorded, unscheduled

Full text in [`../ROADMAP.md`](../ROADMAP.md) §Candidate increments. All
`BLOCKED` on [[EV-NONAUTHOR-EXPOSURE-01]]. Each is larger than the artifact that
already failed with zero users: lease-holder invalidation via `notifications/*`
· projection to a queryable store · streamable HTTP transport · findings graded
by repo outcome · autonomous spawn on a blackboard trigger.

## Done

- `R3-BLACKBOARD-01` **DONE** (`2b8f244`, 2026-08-02) — `claim` / `attest` /
  `findings` / `resolve` / `release` over a local stdio MCP server; append-only
  JSONL, one shard per author, synced over `refs/socom/blackboard`. Works, is
  tested, and is in live use from Akili sessions. **Recorded honestly:** this
  was built out of ladder order. §14.4 said ship R1 alone and build nothing
  beyond it until the non-author measurement exists; §20 said build this first;
  the build followed §20 and §14.4 was never withdrawn. Decision 0001 resolves
  that in favour of §14.4 and **demotes this from "the experiment" to "an
  instrument."** It is not being reverted — it is built, it is not in the way,
  and deleting it would be motion rather than progress. **What it does not
  establish:** anything about adoption by a non-author, which is the claim
  actually at D0.
