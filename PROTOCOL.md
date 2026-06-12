# The SOCOM Protocol — v0.1 (draft)

Status: capture draft, extracted 2026-06-12 from the Akili substrate +
"Protocol over Participants". Agent-agnostic, repo-agnostic.

---

## 0. Thesis

Durable agentic engineering systems hold together because of the **protocol**
— contracts, handoff schemas, write-coordination, verification topology — not
because of the capability of any participant. Substituting participants is
safe; changing protocol is what requires care. Therefore:

> Invest less in making any single agent more capable. Invest more in the
> substrate the agents work against.

Everything that must survive a participant swap, a model release, a context
reset, or a machine change lives in **plain files in git**. Nothing
load-bearing lives in a session, a vendor API, or anyone's memory — human or
model.

## 1. The Room Model

A working session is an agent locked in a room:

| Room element | Substrate artifact |
|---|---|
| The room | An isolated git worktree (never the shared main checkout) |
| The briefing | Next-session prompt — generated, claim-verified, prescriptive |
| The law | Constitution (non-negotiable principles) |
| The job | A promise: accepted intent + validation contract written *before* work |
| The library | Memory bank + lessons, with a **retrieval map** saying what to load when |
| The phone | Role dispatch — which seat to call, with the human's words passed verbatim |
| The door | Gates — mechanical assessment; the door does not open on unkept promises |
| The exit log | Structured handoff — done / undone / commands / exit codes / next |

"Knowing when it needs to retrieve what, when, and with what agents" is not
agent intelligence — it is the lifecycle index (§7), the role contracts (§8),
and the trigger phrases on procedures (§11). The room is self-describing.

## 2. Substrate invariants

1. **Git is shared memory.** Reads parallelize freely; all writes serialize
   through commits. Merge conflicts are paid in tokens — so the protocol
   prevents them structurally (one writer per domain per session, worktree
   isolation, claims).
2. **Plain files, schema'd.** Every artifact is an XML document (markdown
   islands for prose) conforming to a schema in `schemas/`. Human views are
   compiled markdown; the XML is canonical.
3. **Operational state lives in the repo.** Task buckets, handoffs, memories,
   lessons, trust scores. Any clone on any machine has the full state.
4. **Drift is a P0.** Between git and the live system, between buckets and
   reality, between a prompt's claims and origin — drift is itself an incident.

## 3. The Promise Model

Adopted from Promise Theory (Burgess): autonomous agents cannot be commanded,
only *make promises about their own behavior* and *assess* the promises of
others. This is the contract model for human↔agent and agent↔agent alike.

- **Intent** — a participant (usually human or orchestrator) publishes what is
  wanted, including the operator's words **verbatim** (typos preserved — they
  carry signal). An intent is an invitation, not an imposition.
- **Promise (+)** — a participant accepts intent by recording a promise: *I
  will produce artifact X satisfying validation contract Y, with evidence.*
  A promise binds only its maker. Claiming a bucket row IS making a promise.
- **Use-promise (−)** — a downstream participant promises to *rely on* X only
  in its contracted form (e.g., serving layer relies on the output port
  schema, never on internals).
- **Assessment** — every promise names its assessors: a gate (mechanical), a
  reviewer seat (adversarial), or the human. Assessors promise independent
  judgment and **never share working context with the promiser**.
- **Trust** — the rolling, assessed history of kept promises, tracked per
  *seat* (role binding), not per model. Trust modulates autonomy: a seat with
  high kept-promise history earns longer leashes (more autonomous scope);
  broken promises shrink scope and add gates.

Consequences:

- "Done" is defined by the contract, not by the worker — an external
  correctness referent the agent cannot redefine.
- Verification is never self-assessment. VERIFY-NEVER-CLAIM (§5.1) is the
  assessment half of every promise.
- The human's instruction is converted into a contract the agent promises
  against; disagreement is surfaced at contract time, not delivery time.

## 4. Artifacts and the XML canonical form

Every artifact type has: an XML schema, a markdown view template, and a
**retrieval declaration**. Element boundaries are chunk boundaries; attributes
are filter metadata; `embed="true"` marks vectorizable text. The contract
schema is therefore *also* the RAG schema — `socom index` walks the registry
and emits `(id, text, metadata)` tuples for any vector store, with zero
artifact-specific code.

Two invariants from the residuality analysis (R4, R8): every artifact
carries a `socom="<version>"` attribute and schema evolution is additive
within a major version — migration is a compile step, never a hand edit; and
every substrate write passes a **redaction gate** (secrets/PII scan) before
it is stored or embedded — verbatims preserve typos, never tokens.

Artifact types (schemas in `schemas/`):

| Type | Purpose | Lifecycle |
|---|---|---|
| `promise` | Accepted intent + validation contract + assessors | open → kept / broken / withdrawn |
| `contract` | Falsifiable done-ness, written before work | draft → ratified → satisfied |
| `memory` | Distilled cross-session knowledge | active → superseded / retired |
| `lesson` | Domain-sharded operational learning | provisional → active → retired |
| `handoff` | Session exit state | immutable once written |
| `role` | A seat: substrate operations + tool surface + dispatch triggers | versioned |
| `gate` | An assessment: check command, blocking behavior, enforcement point | versioned |
| `decision` (ADR) | Irreversible/structural choice | proposed → accepted (settled law) |
| `runbook` | Known failure → recovery procedure | living |

## 5. The Constitution

Non-negotiable principles. Portable verbatim across stacks; each repo binds
the *mechanics* (commands, CI) in `socom.yaml` (§13).

### 5.1 Verify, never claim
No task is done until concrete proof is shown. "It should work" is a
violation. Run the check, paste the output. Verification output from a
different session or from before the final change does not count. If
verification is impossible from the room, state explicitly what remains
unverified and who must check it.

### 5.2 Contracts before code
The validation contract — falsifiable acceptance checks — is written and
ratified *before* implementation begins. Tests confirm contracts; they are not
retrofitted to bless whatever was built.

### 5.3 Research-first
Plan mode before non-trivial work (multi-file, architectural, unfamiliar
systems, unclear root cause). Prefer official docs, upstream repos, RFCs over
guessing or content farms. Store what you learn (memory or runbook) so the
research is never repeated.

### 5.4 Initiative framing — fix the class, not the instance
Every initiative's objective is to make an entire *class* of problem
structurally impossible at the root — never to patch the visible symptom.
State objectives in that form first: "eliminate class X by changing Y at the
root." Pairs with §5.7: mitigate the live instance fast, but the objective is
always the class.

### 5.5 Residuality gate
Before proposing any fix or hard-to-reverse decision, run the 60-second
adversarial check: does this relocate stress rather than remove it? hide a
quantitative assumption? patch a symptom? open a one-way door? Trigger words
that demand the gate: *pin, bump, raise the limit, add a retry, add a buffer,
bigger node, works for now, temporarily, good enough.*

### 5.6 Git is the single source of truth
No manual changes to live systems that aren't first (or same-session)
declarative in git. Temporary live patches revert or reconcile in the same
session. Break-glass without same-session reconciliation is itself a new P0.

### 5.7 Mitigate before perfect
Outage time is a first-class cost. Rapid read-only diagnosis → narrowest
mitigation → permanent class-level fix, in that order, in the same session.

### 5.8 Context economy
The primary's context is the scarcest resource. Offload bulk, mechanical, and
fan-out work to subordinate seats whose success is verifiable from output.
Retain judgment and final verification in the primary — assessment cannot be
delegated to the promiser.

### 5.9 Verbatim protocol
Every brief to another participant opens with the originating human's words
verbatim (typos preserved), followed by the decoded interpretation, clearly
labeled. Participants compare the two and flag drift. Paraphrase loses signal.

### 5.10 No quick fixes without a leash
Every change must be one you'd accept in the codebase a year from now. An
unavoidable shortcut gets: a documented *why*, a follow-up task with an ID,
and a TODO carrying that ID.

### 5.11 Structured commits
One format, enforced by hook:
`type(scope): description` + `[what] [why] [how] [test] [broke] [next]`
blocks. Full blocks on the *first* branch commit (squash inherits it).

## 6. Contracts

A validation contract states, before work begins:

- **Goal** — one falsifiable sentence.
- **Acceptance checks** — commands/queries with expected outcomes; each
  machine-runnable where possible.
- **Out of scope** — explicit non-goals (drift detector).
- **Regression surface** — what could this break; how is that checked.
- **Assessors** — which gate, seat, or human assesses each check.

Contracts are ratified by the intent's originator (human or orchestrator),
then become the external referent for done-ness. A worker cannot amend its own
contract; renegotiation goes back to the originator — and it is deliberately
**cheaper than bypass** (R10): amendment is a lightweight first-class flow
(new contract version, originator re-ratifies, diff recorded in the promise).
Research-shaped work uses an **exploration promise**: the contract binds the
question and a timebox, not a deliverable artifact.

## 7. Memory

Three tiers, all in-repo, all schema'd, all indexed.

### 7.1 Tiers
- **Memories** — distilled cross-session knowledge, mostly `feedback` (operator
  corrections decoded into standing rules), plus `project` (state/vision) and
  `reference` (external knowledge). Master copy in repo; *hydrated* into each
  runtime's native memory location by the adapter.
- **Lessons** — domain-sharded files (one per subsystem domain) with a counted
  index; entries are `provisional` until re-confirmed, then `active`, and move
  to `_retired` when falsified or obsolete.
- **Runbooks & ADRs** — operational recovery and settled decisions. A failure
  occurring twice, or having non-obvious recovery, demands a runbook. An
  irreversible or standard-setting choice demands an ADR. Accepted ADRs are
  settled — do not re-litigate.

### 7.2 The retrieval map (deterministic retrieval)
The memory index is organized by **lifecycle moment, not topic**:

- *Session start* — bootstrap reflexes, drift protocols, claim discipline
- *Mid-session* — planning gates, verification rules, dispatch patterns
- *Closeout* — wrap pipeline, cleanup, prompt generation
- *Always-on* — standing reflexes (procedure capture, tool gotchas)

A participant entering phase P loads the P section. This is how the locked
agent "knows what to retrieve when" — deterministically, before any RAG.

### 7.3 Associative retrieval (the RAG dividend)
Because every artifact is schema'd XML with embed declarations, associative
retrieval ("what does the substrate know related to this task?") is a trivial
index over the registry: filter by artifact type / lifecycle / domain
attributes, rank by vector similarity on embeddable elements. Deterministic
retrieval (7.2) is the backbone; associative retrieval is the complement. The
substrate never *depends* on RAG — degrade to the index gracefully.

### 7.4 Memory look and feel (the voice)
A memory is decoded operator feedback, not a note. Its body carries, in order:

1. `USER VERBATIM (<date>, <session>):` — the human's literal words, typos
   preserved.
2. **Decoded rule** — the standing rule, stated imperatively.
3. **Why** — the cost of not knowing this, citing the incident.
4. **How to apply** — concrete triggers, commands, and behavior.
5. **Counter-cases** — when NOT to apply it (every rule names its limits).
6. Cross-links `[[other-memory]]`; supersession is explicit
   (`SUPERSEDED by [[x]]` — original preserved, never silently deleted).

### 7.5 Distillation gate
Memory write-access is rationed: **hard cap ≤2 new memories per session**,
each passing five gates — *Dedup* (not already covered), *Counterfactual*
(would a past session have gone better with it?), *Generality* (beyond this
instance?), *Decay* (durable, or version-bound rot?), and *Falsifiability*
(R5: the memory states what would disprove it; unfalsifiable rules are
rejected). Memory is a curated asset, not a log.

## 8. Roles — seats, not models

A role is defined by its **substrate operations** (what it reads, what it may
write, what it promises), its tool surface, and its dispatch triggers. Any
model, runtime, or human can occupy a seat. Right-model-per-seat is an
optimization the protocol enables, never a dependency.

**The role registry is open and versioned (R14).** The protocol fixes only
the seat *envelope* — promises, substrate operations, never-rules, dispatch
triggers, trust — never the cast. New seats (architect, librarian, analyst…)
flow in as the substrate version increases: added as registry entries,
provisional until they prove themselves, retired the same way. The table
below is the founding cast, not a closed set.

| Seat | Promises | Substrate ops | Never |
|---|---|---|---|
| **Orchestrator** | Decomposition, contracts, dispatch | Writes intents/contracts/buckets | Writes production code |
| **Builder** ("mason") | One contracted unit, implemented + self-checked, in an isolated worktree | Mutates code via commits | Assesses its own promise as final |
| **Reviewer** ("ferris/aegis") | Independent adversarial assessment against conventions + contract | Reads diff + contract; writes verdict | Shares context with the builder |
| **Validator** ("pixel") | Live-effect verification against the deployed system | Drives the running system; writes evidence | Trusting the diff over the live effect |
| **Scout** | Bounded research → one-page decision-ready brief | Writes reference memories | Unbounded wandering |
| **Analyst** ("euler") | Objective structural telemetry | Reads code; writes measurements | Giving advice |
| **Adversary** ("hydra") | Competing-hypothesis investigation; each head tries to disprove the others | Writes evidence per hypothesis | Converging early |

Dispatch rules:
- Builder/Reviewer context separation is **absolute** — assessment is only
  meaningful from clean context (and ideally a different model family, to
  avoid shared blind spots).
- Briefs follow the verbatim protocol (§5.9).
- Parallel builders require worktree isolation + domain claims; output returns
  as verifiable assertions (counts, diffs, test summaries), re-verified by the
  dispatching seat.

## 9. Gates — assessment made mechanical

A gate is a promise assessor that runs as code. Each gate declares: trigger
point, check command, **bands**, latency tier, and enforcement mapping.

Gates are two-band (R9): **amber** warns, records, and attaches a deadline;
**red** blocks. Trust per seat widens or narrows the amber band; red is never
disabled. Each tier has a hard latency budget — a fast gate that grows slow
is demoted to the CI tier rather than tolerated (a slow gate breeds bypass).
Local bypass (`--no-verify`, hook-less runtimes, humans) is permitted for
flow but every gate is **re-asserted in CI** (R1): merge is the real door.

| Gate | Trigger | Assessment | Blocks |
|---|---|---|---|
| `session-start` | Session open | Sync with origin; drift scan (prompt claims vs reality); inject context; surface pending failures | Work on stale/drifted state |
| `task-completion` | Marking work done | Run the repo's fast checks on changed surface | The "done" transition |
| `pre-commit` / `pre-push` | Git | Repo's medium/full checks; commit-format contract | The commit/push |
| `ci` | Push/PR | Full contract checks; the universal floor every participant hits | The merge |
| `session-end` | Session close | Generate handoff + next-session prompt; **claim-verify** the prompt (every factual claim probed against the repo: VERIFIED / REWRITTEN / HYPOTHESIS); memory distillation gate; worktree/claims cleanup | A vanishing session |

Enforcement mapping (the agent-agnostic move): every gate exists at the **git
hook + CI layer** (works for every participant including humans); runtime-
specific hooks (Claude Code `TaskCompleted`/`Stop`/`SessionStart`, etc.) are
*accelerators* that catch violations earlier. Losing a runtime never loses
enforcement.

## 10. The session protocol

**Bootstrap** (deterministic, no permission-seeking):
1. Fetch + fast-forward main; create isolated worktree; never work in the
   shared checkout. Run the orphan reaper (R12): expired claims, dead
   worktrees, handoff-less terminated sessions get triaged before new work.
2. Discover the latest next-session prompt; read it *plus* the drift scan —
   prompts state what was true at write time, the repo states what is true now.
3. Claim the work (promise registered against a bucket row + contract).
4. Load the retrieval map's *session-start* section; load lessons for the
   task's domain.
5. Non-trivial work → plan mode; plan ratified against the contract before
   any code.

**Build:**
- Contract first if none exists. Implement. Verify continuously (fast gate
  after every change). Dispatch seats per §8 with verbatim briefs. Run the
  residuality gate before any fix lands. Capture candidate memories/lessons as
  they occur (distilled later, not trusted to recall).

**Closeout** (one uninterrupted pipeline — autonomous end-to-end):
1. Bucket rows flipped to reflect reality; push; CI verified green.
2. Handoff artifact written: done / undone / commands run / exit codes /
   blockers / warnings for the next session.
3. Next-session prompt generated, then **claim-verified** (§9) before it is
   trusted.
4. Memory distillation (≤2, four gates).
5. Claims released; worktrees removed; clean process table.

## 11. The escalation ladder — feedback becomes infrastructure

Nothing relies on a participant remembering to behave. Every recurrence climbs
one rung:

1. Operator correction → **memory** (decoded rule, same session).
2. Second occurrence of a failure → **lesson** or **runbook**.
3. Procedure hand-run twice → **procedure/skill** (trigger-phrased, encoded
   steps with the incident that birthed it).
4. Recurring *and* fan-out-shaped procedure → **workflow** (deterministic
   orchestration script).
5. Principle violated despite documentation → **gate** (made mechanical).
6. Structural choice with trade-offs → **ADR** (settled law).

This ladder is the compounding engine: the substrate gets stricter and faster
with use, and the codebase agents leave behind is *more* automatable than they
found it.

## 12. Retrieval summary — "what, when, with what agents"

- **When** → lifecycle index (§7.2) + gate trigger points (§9).
- **What** → domain-sharded lessons, typed/filtered artifact registry,
  associative search over embed-declared elements (§7.3).
- **With what agents** → role dispatch triggers (§8) + procedure trigger
  phrases (§11.3): the artifacts themselves name the seat that handles them.

## 13. Repo binding — `socom.yaml`

The protocol is invariant; each repo binds the mechanics:

```yaml
socom: 0.1
domains: [data-pipeline, infra, integration]    # bucket + claim granularity
checks:
  fast:   "<command — seconds, every change>"
  medium: "<command — pre-commit>"
  full:   "<command — pre-push / CI>"
ci:
  status: "<command to query pipeline state, cache-free>"
seats:                                           # role → participant binding
  builder:   { runtime: claude-code, model: default }
  reviewer:  { runtime: claude-code, model: different-family-preferred }
retrieval:
  index: ".socom/index"                          # socom index output
```

## 14. Runtime adapters

`socom compile` renders the canonical store into each participant's dialect:

| Target | Output |
|---|---|
| Claude Code | `CLAUDE.md` (constitution + bindings), `.claude/agents/` (seats), `.claude/skills/` (procedures), hooks wired to gates, memory hydration |
| Codex / generic agent | `AGENTS.md` |
| Cursor | `.cursor/rules` |
| Humans & everything else | Git hooks + CI + `CONTRIBUTING.md` view |

The canonical store is the only thing edited by hand. Adapters are thin
one-way compilers (R15) — all intelligence stays canonical; losing a runtime
loses an accelerator, never enforcement or knowledge. Compiled views carry a
"generated — do not edit" header **with the hash of their canonical source**
(R3); the `session-start` gate diffs hashes and treats mismatch as P0 drift.

## 15. Open questions

- Promise/trust scoring: how formal? (EMA per seat exists in the Akili
  lineage; the protocol needs a minimal portable version.)
- Cross-repo memory: per-repo substrate is clean; an org-level shared
  constitution + memory federation needs a precedence rule.
- XML ergonomics: canonical-XML/markdown-view is the bet; validate that
  round-tripping doesn't make artifacts hostile to humans.
- Goal-shift mid-session (research-flavored work destabilizes contracts) —
  likely needs a lighter "exploration promise" variant.
