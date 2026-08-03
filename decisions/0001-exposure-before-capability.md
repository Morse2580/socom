# 0001 — Exposure before capability

**Status:** Accepted 2026-08-03
**Supersedes:** nothing. **Resolves:** the §14.4 ⇄ §20 contradiction described below.
**Upstream gate:** §10 ROOT GATE, 2026-08-01, in
`Akili:thoughts/shared/research/2026-08-01-agent-development-substrate-standalone-product.md`.

---

## Context

The root gate of 2026-08-01 returned **NO-GO on a rebuild**, proof tier **D0 —
ASSUMED**, and named the load-bearing mechanism explicitly:

> The load-bearing mechanism is not an engine, a schema, or a protocol. It is
> **adoption by someone who is not the author**. That mechanism has never been
> executed. Six public artifacts, five months, zero users.

It permitted exactly three things: (1) run the adoption experiment on socom **as
it stands**, one non-author engineer, observed; (2) subtract, don't restart;
(3) clean up the residue on Akili main.

**The same research document then gave two incompatible answers to "build what
first."**

| § | Says |
|---|---|
| **§14.4** | *"R1 is the cheapest instrument ever available for raising it… Ship R1 alone, put it in front of five people… **No increment beyond R1 should be built before that measurement exists.**"* |
| **§20** | *"Not the drift detector… The blackboard is smaller than the drift detector, and it is the part that measures."* |

The blackboard is **R3** in the §14.2 ladder. It was built on 2026-08-02
(`2b8f244`: `blackboard.py` +824, `mcp.py` +375, `claims.py` −102, `bin/socom`
+1281) — the day after the gate. **R1 was not built. §14.4 was never withdrawn.**

### Why the ordering is the whole problem

- **R1 pays off to a stranger on run #1.** It parses a repo's own declared agent
  intent and reports the lies in it — a named verify command that does not
  exist, a "never edit X" rule with X edited last week. No protocol to adopt,
  nothing to configure, no second person required.
- **R3 pays only when 2+ agents and a stock of findings both exist.** Its value
  is *structurally invisible* in a single-author setting.

So the increment whose payoff cannot be seen in our actual setting was built,
and the increment designed to be useful to someone who owes us nothing was not.
The Phase 3a trial is not stalled because the instrument is bad. It is stalled
because of the ordering.

### The trial cannot fire its own kill criterion

`PILOT.md` §the blackboard trial: *"**Setting:** three or more people running
concurrent agents on a shared repo. The thesis is a claim about teams and is
**untestable solo**."*

The actual setting is one person — the author — running concurrent agent
sessions. Fourteen days of zero category-A therefore does **not** license
"stop"; it licenses *"the setting was wrong, run it properly,"* which is attempt
#8 with a justification attached. The kill criterion was described as *"the one
procedural difference between this and everything that came before it."* As
configured it is disarmed.

---

## Decision

1. **§14.4 governs. §20's ordering is retired.** Exposure precedes capability.
2. **R1 is the next and only build.** No increment beyond R1 — including every
   candidate in ROADMAP §Candidate increments — lands before
   `EV-NONAUTHOR-EXPOSURE-01` has a recorded result.
3. **The blackboard stays and keeps running.** It is already paid for and costs
   nothing to leave in place. It is **demoted from "the experiment" to "an
   instrument."** It cannot clear D0 no matter what it reads, because it is not
   measuring the blocking claim.
4. **The gate on candidate increments moves** from "Phase 3a produced saves" to
   "the exposure measurement exists." Saves is no longer a release gate.
5. **A solo zero-A result is recorded as a NULL, not a kill.** The kill
   criterion transfers to the exposure measurement, where the setting
   precondition can actually be met.

## What measuring should be

The metric that clears D0 is not `saves`. It is:

> **Voluntary second use by a non-author** — did they run it again when nobody
> was watching.

Binary, cheap, unfakeable. **First use is compliance; second use is value.**

Supporting instruments, in order of cost:

| Instrument | Needs people? | What it establishes |
|---|---|---|
| R1 seeded-defect corpus (≥10 real repos) | no | R1 works at all — its own §14.2 acceptance test |
| Stall point — where a non-author stops and has to read source | 5, one run each | `PILOT.md`'s own phrasing; the first D1 evidence this idea has ever had |
| Voluntary second use | same 5, no prompting | the D0→D1 mechanism itself |
| `saves` A/B/C tally | 3+ concurrent | demoted to instrument; interpretable only once the above exists |

## Consequences

- ROADMAP Phase 3a keeps running but is re-labelled: instrument, not existential
  test.
- Two work buckets are created (`buckets/build.md`, `buckets/evidence.md`). The
  split is itself the instrument: **every increment in the ladder is a build and
  none is an exposure**, and a bucket pair makes that legible at a glance.
- The candidate increments (notifications, projection to a queryable store, HTTP
  transport, outcome-graded findings, spawn triggers) remain recorded and
  unscheduled. Each is larger than the artifact that already failed with zero
  users.

## Falsifiable acceptance

No commit lands a capability beyond R1 until `EV-NONAUTHOR-EXPOSURE-01` carries
a recorded result. Checkable by reading `buckets/build.md`: every row below R1
reads `BLOCKED` and names that row as its blocker.

## Alternatives rejected

- **Retract §14.4, formalise §20.** Rejected: §20's premise — *"the blackboard
  is the part that measures"* — is true only in a multi-person setting, which is
  exactly the thing not yet obtained. It assumes its own precondition.
- **Keep building blackboard candidates while waiting for people.** Rejected:
  this is the 6/6 pattern the root gate scored as **Lens 1 FAIL (convenience)**
  — building is more enjoyable than finding out why the last one got no users.
- **Restart in a new repo.** Already NO-GO at §10 and unchanged here.
- **Drop the blackboard.** Rejected: it is built, it is not in the way, and
  deleting it would be motion rather than progress. Demote, don't destroy.

## The bound

This decision changes what gets built next. It does **not** claim R1 will
succeed — R1's own acceptance test is unrun, and whether a stranger finds its
output useful is exactly the thing at D0. That is the point: it is the cheapest
available way to find out.
