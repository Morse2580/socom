# SOCOM Roadmap — from v0.1 argument to the unsupervised floor

> Companion to `VISION.md` (the end goal) and `GAPS.md` (the deltas vs. the field).
> This is the *sequence*. Drafted on branch `claude/project-overview-quilm7`.

## The organizing thesis

The end goal (`VISION.md`) is to **widen, every cycle, the fraction of engineering
work that can run unsupervised without losing coherence.** So every item here is
justified by one question: *does this let a human look away from one more class of
work and still sleep?*

That orders the whole plan. You cannot scale unsupervised work you can't trust;
you can't trust what you can't measure; you can't measure safely if it can run
away. So:

**Safe → Measurable → Proven → Wider → Scaled.**

Cross-cutting discipline every phase: **ruthlessly shed scaffolding** the models
have outgrown (the A3 "bureaucracy" attractor is the real death, not better
models), and **every new mechanism must itself pass the eval/ROI bar** before it
becomes canon.

---

## Phase 0 — The measurement spine (prerequisite, days)

Nothing downstream is provable without this. Pick the ground truth before building.

- **Choose one pilot repo + a fixed task set** (10–30 real, representative
  promises across the active domains). This is the yardstick for every later claim.
- **Capture a baseline trace** of how SOCOM runs that set *today* — outcomes,
  tokens, where it fails. No scoring yet; just the "before" picture.
- **Definition of done:** a committed `bench/` task set + a baseline record in the
  run ledger you can diff against later.

## Phase 1 — Make unsupervised SAFE (the two 🔴, weeks) ✅ DONE

> **Status: complete.** 1a — trust-boundary principle (#12) + scout seat redesign
> (commit `cd6b1cd`). 1b — per-run wall-clock budget; monarch kills overruns, records
> broken (commit `c610dce`). Both verified: full test suite green (unit 227, e2e,
> xmlcheck, build), plus behavioral proofs (live process killed R→Z→gone; canon renders
> into CLAUDE.md + scout agent file).

These are the doors that must close before *anything* runs unwatched. Both gate the
exact regime the vision targets.

- **1a. Scout-seat lethal-trifecta fix** (GAPS #1).
  - New constitution principle: an explicit **untrusted-input / tool-authority
    boundary**.
  - Redesign `scout` in `roles.xml` to **cut one leg**: untrusted-content ingestion
    happens in a capability-stripped context whose output is treated as **data,
    never instructions**; no exfiltration path in the same context that read the repo.
  - Matching gate; red-team it with a poisoned source before declaring done.
- **1b. Runaway-loop + token/cost guard** (GAPS #8) in `spawn`/`monarch`.
  - Hard **per-promise token/cost ceiling** (pre-call check, not prose).
  - **Max-iteration cap** and a **rate-based circuit breaker** (sustained high
    token/min = loop → terminate).
  - **Definition of done:** a deliberately-looping test promise is killed by the
    guard, not by the bill.
- **Definition of phase done:** a promise can run with no human watching and the
  two catastrophic failure modes (data exfiltration, runaway spend) are
  structurally impossible, not "unlikely."

## Phase 2 — Make unsupervised MEASURABLE (the spine, weeks) ✅ DONE

> **Status: complete.** Five atomic commits. The unsupervised-green metric is now
> trustworthy: behaviour is traceable, the judge is calibrated, the regression set is
> sourced from earned lessons, and a green gate is checked for adequacy.

This is the highest-leverage phase. It's what turns the flywheel claim from
assertion into evidence and lets you *trust* removing the human.

- **2a. Trajectory observability + token meter** (GAPS #3, #10). ✅ **DONE**
  (`socom trace` `1b13e5c`, `socom meter` `12acad9`). `trace` exports the run registry +
  ledger as OTLP/JSON spans named by the OpenTelemetry GenAI conventions
  (`invoke_agent`, `gen_ai.agent.name`, `gen_ai.request.model`, `gen_ai.conversation.id`,
  `gen_ai.usage.*`) — replayable in any OTLP tool. `meter` parses token usage from run
  logs into the records, so the cost view is token-real; never fabricates counts.
- **2b. The eval + judge-alignment loop** (GAPS #4). ✅ **DONE**.
  - **Human-aligned judge** (`socom judge`, `e0cf0f1`): scores a model assessor against
    human labels; TPR/TNR separately; `--gate` blocks unless BOTH meet threshold (raw
    agreement misleads under imbalance). Proven to catch a sycophant a naive gate passes.
    The labelled-set format carries a `critique` field (critique-shadowing); curation is
    the operator's loop.
  - **Lessons → regression cases** (`socom lesson regression`, `34462c6`): active
    hotspot-born lessons become a "do not break" set; `--check` fires RED when a guarded
    promise's latest ledger verdict goes broken again.
- **2c. Contract-adequacy check** (`socom contract adequacy`, `ffb235b`). ✅ **DONE**.
  Flags a green-but-meaningless verify (no/trivial checks) plus coverage gaps (no
  regression-surface, single check); `--gate` blocks on a strong weakness.
- **Definition of phase done:** for any promise you can answer "did it do the
  *right* thing, and how do I know" with a trace and a calibrated score — not vibes.

## Phase 3 — PROVE the substrate pays off (the existential test, weeks)

Apply SOCOM's own residuality gate *to SOCOM*. This is cheap insurance against
building ceremony nobody needs.

- **3a. The A/B** (GAPS #7). Run the Phase-0 task set **SOCOM-on vs. SOCOM-off**
  (a well-prompted agent + plain CI), scored by the Phase-2 harness. Honest
  outcomes either way:
  - If SOCOM wins → you now have *evidence*, not anecdote, and you know which parts
    drove the win.
  - If it doesn't → you learned cheaply *which* ceremony is dead weight, and you cut it.
- **3b. Tighten doctrine + shed scaffolding.**
  - Promise Theory precision: state the **voluntary-promise vs. egress-assessment**
    distinction; make seat-trust **typed + statistical** (a distribution, not a
    scalar); cite prior art (Burgess 2604.10505, Dual-State 2512.20660).
  - Cut whatever Phase 3a shows the model has outgrown.
- **Definition of phase done:** a one-page, evidence-backed answer to "does the
  protocol beat a good agent with CI, and where."

## Phase 4 — WIDEN the unsupervised envelope (months)

Now that it's safe, measured, and proven, each item here removes one more reason a
human has to watch — i.e., literally executes the vision's flywheel.

- **Human-checkpoint tier** (GAPS #9) wired to the `residuality-gate`
  **one-way-door** trigger — tiered by reversibility, *not* uniform (uniform gating
  breeds rubber-stamping, the #1 exploited failure mode). Auto-approve low-risk;
  gate only the irreversible; summarize the *actual* action, not the agent's intent.
- **Conversational compaction** for long runs (GAPS #6) at the handoff seam —
  distinct from the existing envelope-level compress; this is what fights context rot.
- **Promote `librarian` / L2–L3 retrieval** — but gated behind a **retrieval-quality
  eval** (don't ship retrieval you can't measure).
- **Single-writer doctrine made explicit** + handoffs carry decision *rationale*,
  not just artifacts (defuses the Cognition multi-writer failure).
- **Definition of phase done:** the measured fraction of the task set that runs
  green with zero human touches goes *up*, release over release. That number is the
  vision, quantified.

## Phase 5 — SCALE to L4 (the vision, after 1–3 hold)

Only attempt org scale once the single room is safe, measured, and proven.

- **Containerized substrate-as-a-service** (`socom up`): sealed room — worktree,
  compiled adapters, hydrated memory, gates wired, **egress scoped to the contract**
  (Phase 1a becomes infrastructure, not policy).
- **Org constitution layered under each repo's bindings**; a fleet of rooms run the
  way an org runs CI.
- **Definition of phase done:** the "across all repos, all developers" deployment,
  with the unsupervised-fraction metric tracked per room.

---

## The one number that matters

If you track a single metric, track **the fraction of the pilot task set that
completes green with zero human intervention** — gated by a *calibrated* eval, not
self-report. Every phase above either makes that number trustworthy (1–3) or makes
it go up (4–5). When it climbs release-over-release on a held-out task set, the
vision is no longer a claim — it's a measurement.

## Sequencing rationale (why this order is non-negotiable)

- **Safety before everything:** an unsafe unsupervised system isn't a smaller
  version of the goal — it's a liability that ends the pilot.
- **Measurement before proof:** you cannot prove ROI or trust autonomy without a
  calibrated eval; "it feels better" is the failure mode the whole project exists
  to kill.
- **Proof before scale:** L4 multiplies whatever you have across an org. Multiply
  unproven ceremony and you get fleet-wide bureaucracy (A4 drift). Multiply a proven
  floor and you get the vision.
