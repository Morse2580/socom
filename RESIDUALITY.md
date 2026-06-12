# SOCOM Residuality Analysis

Method: Residuality Theory (Barry O'Reilly). Take the naive architecture,
hit it with stressors — including improbable ones — observe which attractor
the system falls into, and keep the **residues**: the design changes that
survive. The final architecture is the naive architecture plus its residues.
Criticality check at the end: residues must help against stressors they
weren't designed for, or they're patches, not residues.

## Naive architecture (components)

| # | Component |
|---|---|
| C1 | Canonical XML artifact store (`.socom/`) in git |
| C2 | Compiled runtime adapters (CLAUDE.md / AGENTS.md / .cursor/rules) |
| C3 | Gates (runtime hooks + git hooks + CI) |
| C4 | Memory bank + lifecycle index + hydration |
| C5 | Lessons (domain-sharded, counted index) |
| C6 | Promise registry (promises, contracts, assessments) |
| C7 | Roles/seats + trust scores |
| C8 | Session protocol (worktree, claims, handoffs, next-session prompts) |
| C9 | Retrieval index (L1+ RAG) |
| C10 | `socom` CLI (init/compile/hydrate/index/gate) |

## Attractors (failure states the system slides into)

- **A1 — Vibecoding attractor:** gates bypassed or decorative → the substrate
  exists but nobody is bound by it. (The death state; everything below is a
  road here.)
- **A2 — Stale-substrate attractor:** memories/lessons confidently wrong →
  worse than no substrate, because participants *trust* it.
- **A3 — Bureaucracy attractor:** protocol heavier than the work → routed
  around → A1 with extra steps.
- **A4 — Fleet-drift attractor:** many repos, diverging substrate versions →
  "socom" means something different everywhere → trust in the brand collapses.

## Stressor × impact

| S | Stressor | Hits | Slides toward |
|---|---|---|---|
| S1 | Participant ignores protocol (rogue agent, human with `--no-verify`, deadline panic) | C3, C6 | A1 |
| S2 | Two sessions parallel on same domain — write collision | C1, C8 | A1 |
| S3 | Someone edits a compiled view (CLAUDE.md) directly; canonical and compiled drift | C2 | A2 |
| S4 | Model upgrade changes prompt interpretation overnight | C2, C7 | A2 |
| S5 | A runtime vanishes or breaks its hook/rules API | C2, C3 | A1 |
| S6 | Memory bloat: 500 memories, index exceeds any context window | C4, C9 | A3 |
| S7 | Poisoned memory: confidently wrong rule distilled, followed for months | C4 | A2 |
| S8 | Vector store down / index stale | C9 | A2 |
| S9 | Schema v2 breaks v1 artifacts | C1, C9 | A4 |
| S10 | Monorepo / 40 domains / huge history | C5, C8 | A3 |
| S11 | Operator leaves; successor inherits substrate cold (bus factor) | all | A2 |
| S12 | Gates get slow (full check 20 min) | C3 | A3 → A1 |
| S13 | Trust gaming: seat farms trivial kept-promises to inflate score | C7 | A2 |
| S14 | Secrets/PII land in verbatims (verbatim protocol preserves typos AND tokens) | C1, C4, C9 | breach |
| S15 | Ratified contract turns out wrong mid-build; renegotiation feels heavy | C6 | A1 (bypass) |
| S16 | CI provider outage — the "universal floor" is gone | C3 | A1 |
| S17 | Force-push / history rewrite mangles promise registry state | C1, C6 | A2 |
| S18 | Org adopts across 50 repos; substrate versions diverge | C1, C2, C10 | A4 |
| S19 | Agent fabricates verification evidence (invented paste) | C3, C6 | A2 |
| S20 | Session dies mid-flight: no closeout, claims stuck, handoff missing | C8 | A1/A2 |
| S21 | New work type arrives (architect-only ADR work, analyst exploration) that the fixed role cast doesn't fit | C7 | A3 (protocol ignored as "not for me") |

## Residues

Each residue states what it survives, and (criticality) what else it
incidentally hardens.

**R1 — CI is the incorruptible floor.** Every local/runtime gate is
re-asserted in CI. Local bypass (`--no-verify`, hook-less runtimes, humans)
is *permitted for flow* but never escapes re-assessment; merge is the real
door. Survives S1, S5, S19. Criticality: also makes S12 tractable (slow
checks belong to the CI tier, see R9).

**R2 — Claims with auto-expiry.** Domain claims are cheap origin markers
(marker branches / claim files) with a TTL; expiry self-releases. Survives
S2, S20. Criticality: gives S10 its sharding unit (claims are per-domain).

**R3 — Compiled views are hashed.** Every compiled artifact carries the hash
of its canonical source; the session-start gate diffs them — mismatch is P0
drift, auto-recompiled or surfaced, never silently absorbed. Survives S3.
Criticality: also detects S18 (fleet drift) at every session start.

**R4 — Versioned, additive-only schemas.** Every artifact carries
`socom="<ver>"`; schema evolution is additive within a major; migration is a
compile step, never a hand edit. Survives S9, S18. Criticality: lets a fleet
run mixed versions during rollout (A4 resistance).

**R5 — Memory falsifiability + lifecycle hygiene.** A memory must cite its
origin (session, verbatim) **and state what would disprove it**; the
distillation gate rejects unfalsifiable rules. Provisional → active requires
a second confirming occurrence; decay review retires version-bound rules;
supersession is explicit and preserving. Hard cap ≤2/session stands.
Survives S7, S6 (cap + retirement bound growth). Criticality: S11 — a
successor can audit *why* every rule exists.

**R6 — The L0 floor is mandatory.** Every retrieval/feature level must
answer "what happens when you're gone": vector store down → lifecycle index
+ grep still fully operate. No protocol step may *require* a level above L0.
Survives S8, S16 (partially: git hooks still fire offline). Criticality:
makes L4 containers stateless — anything in the room is rebuildable from git.

**R7 — Evidence is replayable, not quotable.** Verification = recorded
command + exit code + artifact, re-runnable by any assessor; gates re-execute
rather than trust pasted output. Survives S19. Criticality: S11 (evidence
audit trail), S17 (assessments reconstructed by replay).

**R8 — Redaction gate on artifact writes.** A secrets/PII scan runs on every
substrate write; verbatims preserve typos, never tokens. Embedding only
happens post-redaction. Survives S14. Criticality: makes L1–L3 retrieval and
L4 egress safe by construction.

**R9 — Two-band gates with a latency budget.** Gates declare amber
(warn + record + deadline) and red (block) bands; the fast tier has a hard
seconds-budget — anything slower is demoted to the CI tier. Governance
follows "computer says no," but the *no* arrives in milliseconds or moves to
the floor. Survives S12, A3 generally. Criticality: amber-band data feeds
trust scoring (R11) without blocking flow.

**R10 — Renegotiation is cheaper than bypass.** Contract amendment is a
first-class lightweight flow: new contract version, originator re-ratifies,
diff recorded in the promise. Research-shaped work gets an **exploration
promise** variant (contract on the question + timebox, not the artifact).
Survives S15. Criticality: absorbs the article's "goals shift mid-execution"
open problem.

**R11 — Trust is risk-weighted and assessor-verified.** Only
assessor-confirmed promises score, weighted by contract scope/risk; trivial
promise farming moves nothing. Trust widens amber bands, never disables red.
Survives S13. Criticality: gives S4 a damper — a model swap that degrades a
seat shows up as falling kept-rate, automatically narrowing its autonomy.

**R12 — Orphan reaper at session start.** The session-start gate sweeps:
expired claims, worktrees with no live session, handoff-less terminated
sessions (reconstruct a minimal handoff from the reflog + uncommitted state).
Survives S20. Criticality: S2 cleanup, S17 partial recovery.

**R13 — The substrate explains itself.** `socom compile` emits a
human-facing view (CONTRIBUTING / onboarding) from the constitution, roles,
and gates — generated, never hand-written. Survives S11. Criticality: S21 —
new participant types meet a self-describing system.

**R14 — Roles are an open, versioned registry.** Seats are *data, not
protocol*: adding architect, librarian (L3), or analyst seats is an additive
registry entry with its own version — roles **flow in as the substrate
version increases**, and retire the same way (lifecycle like memories:
provisional seats prove themselves before becoming standard). The protocol
fixes only the seat *envelope* (promises / substrate-ops / never-rules /
dispatch / trust), never the cast. Survives S21, S4 (rebind seat to a
different model), S5 (rebind seat to a different runtime). Criticality: this
is what lets VISION §2's persona expansion happen without a protocol bump.

**R15 — Adapters are thin one-way compilers.** All intelligence lives in the
canonical store; an adapter only renders. Losing a runtime loses an
accelerator, never enforcement (R1) or knowledge (C1). Survives S5, S18.

**R16 — Registry state is append-only and fetch-protected.** Promise/
assessment mutations are append-only elements; protected branches forbid
force-push on substrate paths; `socom doctor` detects rewritten history by
hash chain. Survives S17.

## Criticality check

The matrix above is healthy: every residue survives ≥2 stressors, and the
three big attractors each have multiple independent defenses —
A1 (R1, R2, R9, R10, R12), A2 (R3, R5, R7, R11), A3 (R9, R10, R13, R14),
A4 (R3, R4, R15). No single residue is load-bearing for an attractor on its
own. The naive architecture needed: hashing of compiled views, falsifiable
memories, replayable evidence, two-band gates, cheap renegotiation, the open
role registry, and append-only registry state — none of which were in the
first sketch. That delta is the value of the exercise.

## Folded back into the protocol

These residues amend `PROTOCOL.md`: §4 (schema versioning, R4; redaction,
R8), §6 (amendment flow + exploration promise, R10), §7.5 (falsifiability,
R5), §8 (open versioned role registry, R14), §9 (two-band gates + latency
budget + CI re-assertion, R1/R9), §10 (orphan reaper, R12), §14 (thin
compilers + hashes, R3/R15).
